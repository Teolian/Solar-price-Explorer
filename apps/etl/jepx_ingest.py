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

        JEPX uses a POST-based download mechanism via /_download.php
        The download button on the website sends a POST request with form data:
        - dir=spot_summary (or spot for raw data)
        - file=spot_summary_YYYY.csv

        Encoding: Shift_JIS (cp932)
        """
        logger.info(f"Attempting to fetch JEPX data for {year}")

        # JEPX download endpoint - timestamp in query string is CRITICAL!
        import time
        timestamp_ms = int(time.time() * 1000)
        download_url = f"https://www.jepx.jp/_download.php?timestamp={timestamp_ms}"

        # Try different file patterns (spot has full 48-slot data)
        file_patterns = [
            ("spot", f"spot_{year}.csv"),  # Full data with 48 time codes - try this first
            ("spot_summary", f"spot_summary_{year}.csv"),  # Summary
        ]

        # Browser-like headers required by JEPX (complete set for WAF bypass)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.jepx.jp',
            'Referer': 'https://www.jepx.jp/electricpower/market-data/spot/',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            # Try each file pattern
            for dir_name, file_name in file_patterns:
                try:
                    # Form data for POST request
                    form_data = {
                        'dir': dir_name,
                        'file': file_name
                    }

                    logger.info(f"POST {download_url}")
                    logger.info(f"  dir={dir_name}, file={file_name}")
                    response = client.post(download_url, data=form_data, headers=headers)

                    logger.info(f"  Response: {response.status_code}, {len(response.content)} bytes")

                    if response.status_code == 200 and len(response.content) > 100:  # At least 100 bytes for valid CSV
                        logger.info(f"✓ Successfully fetched {file_name}")

                        # JEPX uses SHIFT_JIS (cp932) encoding
                        try:
                            content = response.content.decode('cp932')
                        except UnicodeDecodeError:
                            try:
                                content = response.content.decode('shift_jis')
                            except UnicodeDecodeError:
                                logger.warning("Failed to decode as cp932/shift_jis, trying utf-8")
                                content = response.content.decode('utf-8')

                        # Parse CSV
                        from io import StringIO
                        df = pd.read_csv(StringIO(content))

                        logger.info(f"Fetched {len(df)} records for {year}")
                        logger.info(f"Columns: {list(df.columns)[:10]}")
                        return df

                    else:
                        # Log what we got for debugging
                        preview = response.content[:200].decode('utf-8', errors='ignore')
                        logger.warning(f"✗ Failed: {response.status_code}, preview: {preview}")

                except Exception as e:
                    logger.warning(f"✗ Exception for {file_name}: {e}")
                    continue

                # Throttle between attempts (2-3 seconds as recommended)
                logger.info("  Waiting 2 seconds before next attempt...")
                import time
                time.sleep(2)

            # If all patterns failed, try to load from local file
            local_file = self._try_load_local_file(year)
            if local_file is not None:
                return local_file

            # If all patterns failed for 2025, try previous year as fallback
            if year >= 2025:
                logger.warning(f"All file patterns failed for {year}, trying {year-1}")
                return self.fetch_yearly_prices(year - 1)

            logger.error(f"Could not fetch JEPX data for {year} from any source")
            logger.info("\n" + "="*60)
            logger.info("MANUAL DOWNLOAD INSTRUCTIONS:")
            logger.info("="*60)
            logger.info("1. Go to https://www.jepx.jp/electricpower/market-data/spot/")
            logger.info("2. Click 'Data Download' button")
            logger.info(f"3. Select year {year} and download spot_{year}.csv")
            logger.info(f"4. Save file to: data/jepx/spot_{year}.csv")
            logger.info("5. Run: python apps/etl/import_jepx_csv.py --file data/jepx/spot_{}.csv".format(year))
            logger.info("="*60 + "\n")
            return None

    def _try_load_local_file(self, year: int) -> Optional[pd.DataFrame]:
        """Try to load JEPX data from local file"""
        # Check common locations
        possible_paths = [
            f"data/jepx/spot_{year}.csv",
            f"data/jepx/spot_summary_{year}.csv",
            f"../data/jepx/spot_{year}.csv",
            f"/data/jepx/spot_{year}.csv"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found local file: {path}")
                try:
                    # Try CP932 (Shift_JIS) encoding
                    try:
                        df = pd.read_csv(path, encoding='cp932')
                    except UnicodeDecodeError:
                        df = pd.read_csv(path, encoding='shift_jis')

                    logger.info(f"✓ Loaded {len(df)} records from local file")
                    logger.info(f"Columns: {list(df.columns)[:10]}")
                    return df
                except Exception as e:
                    logger.warning(f"Failed to load local file {path}: {e}")
                    continue

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

            # Parse slot/hour (時刻コード or Slot)
            # JEPX uses 48 time codes (1-48) for 30-minute intervals:
            # Code 1  = 00:00-00:30 (timestamp 00:00)
            # Code 2  = 00:30-01:00 (timestamp 00:30)
            # Code 3  = 01:00-01:30 (timestamp 01:00)
            # ...
            # Code 48 = 23:30-24:00 (timestamp 23:30)
            slot_col = '時刻コード' if '時刻コード' in raw_df.columns else ('コマ' if 'コマ' in raw_df.columns else 'Slot')
            if slot_col in row:
                slot = int(row[slot_col])
                hour = (slot - 1) // 2
                minute = 30 if (slot % 2 == 0) else 0
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
