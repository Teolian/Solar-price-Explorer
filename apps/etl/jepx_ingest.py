#!/usr/bin/env python3
"""
JEPX Data Ingestion Script
Downloads and processes JEPX spot market price data
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pytz
import pandas as pd
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JST = pytz.timezone('Asia/Tokyo')
JEPX_BASE_URL = "https://www.jepx.jp/en/electricpower/market-data/spot"
AREAS = ["HOKKAIDO", "TOHOKU", "TOKYO", "CHUBU", "HOKURIKU",
         "KANSAI", "CHUGOKU", "SHIKOKU", "KYUSHU"]

class JEPXIngester:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def fetch_yearly_prices(self, year: int) -> Optional[pd.DataFrame]:
        """
        Fetch yearly spot prices from JEPX CSV
        JEPX publishes annual CSV files: https://www.jepx.jp/market/excel/spot_YEAR.csv
        """
        url = f"https://www.jepx.jp/market/excel/spot_{year}.csv"
        logger.info(f"Fetching JEPX data from {url}")

        try:
            # Use browser-like headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/csv,application/csv,text/plain,*/*',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                'Referer': 'https://www.jepx.jp/'
            }

            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                # JEPX uses SHIFT_JIS encoding, try UTF-8 as fallback
                try:
                    content = response.content.decode('shift_jis')
                except UnicodeDecodeError:
                    logger.warning("Failed to decode as shift_jis, trying utf-8")
                    content = response.content.decode('utf-8')

                # Parse CSV
                from io import StringIO
                df = pd.read_csv(StringIO(content))

                logger.info(f"Fetched {len(df)} records for {year}")
                logger.info(f"Columns: {list(df.columns)[:5]}...")  # Log first few columns
                return df

        except Exception as e:
            logger.error(f"Error fetching JEPX data for {year}: {e}")
            return None

    def fetch_daily_prices(self, date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch daily spot prices from JEPX
        Downloads yearly CSV and filters for the requested date
        """
        year = date.year
        logger.info(f"Fetching JEPX data for {date.strftime('%Y-%m-%d')}")

        # Check if we already have this year's data cached
        cache_key = f"jepx_{year}"
        if not hasattr(self, '_cache'):
            self._cache = {}

        if cache_key not in self._cache:
            yearly_data = self.fetch_yearly_prices(year)
            if yearly_data is None:
                return None
            self._cache[cache_key] = yearly_data

        # Filter for specific date
        df = self._cache[cache_key].copy()
        date_str = date.strftime('%Y/%m/%d')

        # Filter by date (column name might be 年月日 or Date)
        if '年月日' in df.columns:
            df = df[df['年月日'] == date_str]
        elif 'Date' in df.columns:
            df = df[df['Date'] == date_str]

        return df if not df.empty else None

    def normalize_data(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize JEPX data to standard format
        JEPX CSV columns (Japanese):
        - 年月日 (Date): YYYY/MM/DD format
        - コマ (Slot): Hour slot (1-24 or 1-48 for 30-min intervals)
        - システムプライス (System Price): JPY/kWh
        - 北海道, 東北, 東京, 中部, 北陸, 関西, 中国, 四国, 九州: Area prices
        - 量(kWh), 売量(kWh), 買量(kWh): Volume data
        """
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()

        # Map Japanese area names to English
        area_mapping = {
            '北海道': 'HOKKAIDO',
            '東北': 'TOHOKU',
            '東京': 'TOKYO',
            '中部': 'CHUBU',
            '北陸': 'HOKURIKU',
            '関西': 'KANSAI',
            '中国': 'CHUGOKU',
            '四国': 'SHIKOKU',
            '九州': 'KYUSHU'
        }

        normalized_records = []

        # Process each row
        for _, row in raw_df.iterrows():
            # Parse date
            date_col = '年月日' if '年月日' in raw_df.columns else 'Date'
            date_str = row[date_col]

            # Parse slot/hour (コマ or Slot)
            slot_col = 'コマ' if 'コマ' in raw_df.columns else 'Slot'
            if slot_col in row:
                # Slot is usually 1-48 for 30-minute intervals
                # Convert to hour (slot 1 = 00:30, slot 2 = 01:00, etc.)
                slot = int(row[slot_col])
                hour = (slot - 1) // 2
                minute = 0 if slot % 2 == 0 else 30
            else:
                hour = 0
                minute = 0

            # Create timestamp
            timestamp = pd.to_datetime(f"{date_str} {hour:02d}:{minute:02d}:00")
            timestamp = timestamp.tz_localize(JST)

            # Get system price
            sys_price_col = 'システムプライス' if 'システムプライス' in raw_df.columns else 'System Price'
            system_price = row.get(sys_price_col, None)

            # Get volume if available
            volume_col = '量(kWh)' if '量(kWh)' in raw_df.columns else 'Volume'
            volume = row.get(volume_col, None)

            # Create record for each area
            for jp_name, en_name in area_mapping.items():
                if jp_name in raw_df.columns:
                    area_price = row[jp_name]

                    # Skip if price is null or invalid
                    if pd.isna(area_price):
                        continue

                    normalized_records.append({
                        'timestamp': timestamp,
                        'area': en_name,
                        'area_price_jpy_kwh': float(area_price),
                        'system_price_jpy_kwh': float(system_price) if pd.notna(system_price) else None,
                        'volume_total_kwh': float(volume) if pd.notna(volume) else None,
                        'volume_sell_kwh': None,
                        'volume_buy_kwh': None
                    })

        if not normalized_records:
            logger.warning("No valid records after normalization")
            return pd.DataFrame()

        result = pd.DataFrame(normalized_records)
        logger.info(f"Normalized {len(result)} records")
        return result

    def store_data(self, df: pd.DataFrame):
        """
        Store normalized data in database using upsert to handle duplicates
        """
        if df.empty:
            logger.warning("No data to store")
            return

        try:
            from sqlalchemy import text

            # Use INSERT ... ON CONFLICT DO UPDATE to handle duplicates
            with self.engine.connect() as conn:
                for _, row in df.iterrows():
                    query = text("""
                        INSERT INTO prices (
                            timestamp, area, area_price_jpy_kwh, system_price_jpy_kwh,
                            volume_total_kwh, volume_sell_kwh, volume_buy_kwh
                        ) VALUES (
                            :timestamp, :area, :area_price, :system_price,
                            :volume_total, :volume_sell, :volume_buy
                        )
                        ON CONFLICT (timestamp, area)
                        DO UPDATE SET
                            area_price_jpy_kwh = EXCLUDED.area_price_jpy_kwh,
                            system_price_jpy_kwh = EXCLUDED.system_price_jpy_kwh,
                            volume_total_kwh = EXCLUDED.volume_total_kwh,
                            volume_sell_kwh = EXCLUDED.volume_sell_kwh,
                            volume_buy_kwh = EXCLUDED.volume_buy_kwh
                    """)

                    conn.execute(query, {
                        'timestamp': row['timestamp'],
                        'area': row['area'],
                        'area_price': row['area_price_jpy_kwh'],
                        'system_price': row['system_price_jpy_kwh'],
                        'volume_total': row['volume_total_kwh'],
                        'volume_sell': row['volume_sell_kwh'],
                        'volume_buy': row['volume_buy_kwh']
                    })

                conn.commit()
                logger.info(f"Stored/updated {len(df)} price records")

        except Exception as e:
            logger.error(f"Error storing data: {e}")
            raise

    def run(self, areas: List[str], start_date: datetime, end_date: datetime):
        """
        Run ingestion for specified areas and date range
        """
        logger.info(f"Starting JEPX ingestion for areas: {areas}")
        logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        current_date = start_date
        while current_date <= end_date:
            try:
                raw_data = self.fetch_daily_prices(current_date)
                if raw_data is not None:
                    normalized_data = self.normalize_data(raw_data)
                    self.store_data(normalized_data)
            except Exception as e:
                logger.error(f"Error processing {current_date}: {e}")

            current_date += timedelta(days=1)

        logger.info("JEPX ingestion completed")

def main():
    parser = argparse.ArgumentParser(description='Ingest JEPX spot market data')
    parser.add_argument('--areas', type=str, default='TOKYO,TOHOKU',
                        help='Comma-separated list of areas')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to fetch (backward from today)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Parse areas
    areas = [a.strip().upper() for a in args.areas.split(',')]

    # Parse date range
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=JST)
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').replace(tzinfo=JST)
    else:
        end_date = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=args.days)

    # Run ingestion
    ingester = JEPXIngester(database_url)
    ingester.run(areas, start_date, end_date)

if __name__ == '__main__':
    main()
