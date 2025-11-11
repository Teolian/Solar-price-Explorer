#!/usr/bin/env python3
"""
JapanesePower.org JEPX Data Ingestion

Downloads JEPX spot price history from japanesepower.org
Source: https://japanesepower.org

Data available:
- JEPX Spot History (30-minute intervals)
- Demand History
- CSV format with SHIFT_JIS encoding

Regions: Tokyo, Tohoku, Hokkaido, Kansai, Chubu, etc.

Usage:
  python japanesepower_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --start-date 2025-09-01 --end-date 2025-11-11
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
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JST = pytz.timezone('Asia/Tokyo')

# JapanesePower.org area pages
JAPANESEPOWER_BASE_URL = "https://japanesepower.org"
AREA_PAGES = {
    'TOKYO': 'Tokyo_main.html',
    'TOHOKU': 'Tohoku_main.html',
    'HOKKAIDO': 'Hokkaido_main.html',
    'KANSAI': 'Kansai_main.html',
    'CHUBU': 'Chuubu_main.html',
    'KYUSHU': 'Kyushu_main.html',
    'CHUGOKU': 'Chuugoku_main.html',
    'SHIKOKU': 'Shikoku_main.html',
    'HOKURIKU': 'Hokuriku_main.html'
}


class JapanesePowerIngester:
    """Ingests JEPX spot price data from JapanesePower.org"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)

    def fetch_area_data(self, area: str) -> Optional[pd.DataFrame]:
        """
        Fetch JEPX spot price data for an area

        Note: This is a simplified version. JapanesePower.org might require:
        - Parsing the HTML page to find CSV download links
        - Using specific CSV endpoints
        - Handling JavaScript-generated download links

        Args:
            area: Area name (TOKYO, TOHOKU, etc.)

        Returns:
            DataFrame with JEPX spot price data
        """
        if area not in AREA_PAGES:
            logger.error(f"Unknown area: {area}")
            return None

        page_url = f"{JAPANESEPOWER_BASE_URL}/{AREA_PAGES[area]}"
        logger.info(f"Fetching data for {area} from {page_url}")

        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': JAPANESEPOWER_BASE_URL
                }

                # First, get the page to find CSV download links
                response = client.get(page_url, headers=headers)
                response.raise_for_status()

                # Parse HTML to find CSV links
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for CSV download links
                # Common patterns: "download", "csv", "spot_history"
                csv_links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if any(pattern in href.lower() for pattern in ['csv', '.csv', 'download', 'spot']):
                        if not href.startswith('http'):
                            href = f"{JAPANESEPOWER_BASE_URL}/{href}"
                        csv_links.append(href)
                        logger.info(f"Found CSV link: {href}")

                if not csv_links:
                    logger.warning(f"No CSV links found on {page_url}")
                    logger.info("You may need to manually download CSV from the website")
                    return None

                # Try to download the first CSV link
                csv_url = csv_links[0]
                logger.info(f"Downloading CSV from: {csv_url}")

                csv_response = client.get(csv_url, headers=headers)
                csv_response.raise_for_status()

                # Decode with SHIFT_JIS
                try:
                    content = csv_response.content.decode('shift_jis')
                except UnicodeDecodeError:
                    content = csv_response.content.decode('utf-8')

                # Parse CSV
                from io import StringIO
                df = pd.read_csv(StringIO(content))

                logger.info(f"✓ Loaded {len(df)} records")
                logger.info(f"Columns: {list(df.columns)[:10]}")

                return df

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error("Access forbidden (403). JapanesePower.org might block automated access.")
                logger.info("Consider using Playwright or manual download.")
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data for {area}: {e}")
            return None

    def normalize_data(self, raw_df: pd.DataFrame, area: str) -> pd.DataFrame:
        """
        Normalize JapanesePower CSV to standard format

        Expected columns (similar to JEPX format):
        - Date or 年月日: Date
        - Time or 時刻コード: Time code (1-48)
        - Price columns for area

        Returns:
            DataFrame with columns: timestamp, area, area_price_jpy_kwh
        """
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()

        normalized_records = []

        # Detect column names
        date_col = None
        time_col = None

        for col in raw_df.columns:
            if 'date' in str(col).lower() or '年月日' in col:
                date_col = col
            elif 'time' in str(col).lower() or '時刻' in col or 'slot' in str(col).lower():
                time_col = col

        if not date_col:
            logger.warning(f"Could not find date column in: {list(raw_df.columns)}")
            return pd.DataFrame()

        logger.info(f"Detected columns: date={date_col}, time={time_col}")

        for _, row in raw_df.iterrows():
            try:
                # Parse date
                date_str = str(row[date_col])
                if '/' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                elif '-' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')

                # Parse time code if available
                if time_col and pd.notna(row[time_col]):
                    slot = int(row[time_col])
                    hour = (slot - 1) // 2
                    minute = 30 if (slot % 2 == 0) else 0
                else:
                    # Assume hourly data
                    hour = 0
                    minute = 0

                timestamp = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
                timestamp = JST.localize(timestamp)

                # Look for price column
                price = None
                for col in raw_df.columns:
                    if 'price' in str(col).lower() or '価格' in col or area.lower() in str(col).lower():
                        if pd.notna(row[col]):
                            price = float(row[col])
                            break

                if price is not None:
                    normalized_records.append({
                        'timestamp': timestamp,
                        'area': area,
                        'area_price_jpy_kwh': price
                    })

            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue

        result = pd.DataFrame(normalized_records)
        logger.info(f"✓ Normalized {len(result)} price records for {area}")

        return result

    def store_prices(self, df: pd.DataFrame):
        """Store price data in database"""
        if df.empty:
            logger.warning("No price data to store")
            return

        logger.info(f"Storing {len(df)} price records...")

        with self.engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO jepx_prices
                    (timestamp, area, area_price_jpy_kwh, system_price_jpy_kwh,
                     volume_total_kwh, volume_sell_kwh, volume_buy_kwh)
                    VALUES (:timestamp, :area, :price, NULL, NULL, NULL, NULL)
                    ON CONFLICT (timestamp, area)
                    DO UPDATE SET
                        area_price_jpy_kwh = EXCLUDED.area_price_jpy_kwh
                """), {
                    'timestamp': row['timestamp'],
                    'area': row['area'],
                    'price': row['area_price_jpy_kwh']
                })

        logger.info(f"✓ Stored {len(df)} records")

    def run(self, areas: List[str], start_date: str, end_date: str):
        """
        Fetch JEPX data for specified areas and date range

        Args:
            areas: List of area names
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        logger.info("="*60)
        logger.info("JapanesePower.org Data Ingestion")
        logger.info("="*60)
        logger.info(f"Areas: {', '.join(areas)}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info("="*60 + "\n")

        total_records = 0
        successful_areas = 0
        failed_areas = 0

        for area in areas:
            logger.info(f"\nProcessing area: {area}")
            logger.info("-" * 40)

            # Fetch area data
            raw_df = self.fetch_area_data(area)

            if raw_df is not None:
                # Normalize data
                normalized_df = self.normalize_data(raw_df, area)

                if not normalized_df.empty:
                    # Filter by date range
                    start_dt = JST.localize(datetime.strptime(start_date, '%Y-%m-%d'))
                    end_dt = JST.localize(datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59))

                    normalized_df = normalized_df[
                        (normalized_df['timestamp'] >= start_dt) &
                        (normalized_df['timestamp'] <= end_dt)
                    ]

                    logger.info(f"After date filtering: {len(normalized_df)} records")

                    if not normalized_df.empty:
                        # Store in database
                        self.store_prices(normalized_df)
                        total_records += len(normalized_df)
                        successful_areas += 1
                    else:
                        logger.warning(f"No data in date range for {area}")
                        failed_areas += 1
                else:
                    logger.warning(f"No valid data after normalization for {area}")
                    failed_areas += 1
            else:
                logger.warning(f"Failed to fetch data for {area}")
                failed_areas += 1

        logger.info("\n" + "="*60)
        logger.info("JAPANESEPOWER INGESTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Successful areas: {successful_areas}")
        logger.info(f"Failed areas: {failed_areas}")
        logger.info(f"Total records: {total_records}")
        logger.info("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Ingest JEPX data from JapanesePower.org'
    )
    parser.add_argument(
        '--areas',
        type=str,
        required=True,
        help='Comma-separated areas (e.g., TOKYO,TOHOKU,HOKKAIDO)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        required=True,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/solar_prices'),
        help='Database URL'
    )

    args = parser.parse_args()

    # Parse areas
    areas = [a.strip().upper() for a in args.areas.split(',')]

    # Create ingester
    ingester = JapanesePowerIngester(args.database_url)

    # Run ingestion
    try:
        ingester.run(areas, args.start_date, args.end_date)
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
