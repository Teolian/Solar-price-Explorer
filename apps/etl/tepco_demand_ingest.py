#!/usr/bin/env python3
"""
TEPCO Demand Data Ingestion

Downloads electricity demand data from TEPCO (Tokyo Electric Power Company)
Official CSV downloads: https://www.tepco.co.jp/en/forecast/html/download-e.html

Data:
- Hourly electricity demand for Tokyo area
- Historical and forecast data
- Updated daily at ~6:00 AM JST

Usage:
  python tepco_demand_ingest.py --start-date 2025-09-01 --end-date 2025-11-11
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional
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

# TEPCO CSV download URLs
# Format: https://www.tepco.co.jp/forecast/html/images/juyo-YYYYMMDD.csv
TEPCO_CSV_URL_PATTERN = "https://www.tepco.co.jp/forecast/html/images/juyo-{date}.csv"


class TEPCODemandIngester:
    """Ingests TEPCO electricity demand data"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)

    def fetch_daily_demand(self, date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch TEPCO demand data for a specific date

        Args:
            date: Date to fetch data for

        Returns:
            DataFrame with columns: timestamp, demand_mw, forecast_mw
        """
        date_str = date.strftime('%Y%m%d')
        url = TEPCO_CSV_URL_PATTERN.format(date=date_str)

        logger.info(f"Fetching TEPCO data for {date.strftime('%Y-%m-%d')}")
        logger.info(f"URL: {url}")

        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                # TEPCO might use browser-like headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'text/csv,text/plain,*/*',
                    'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
                    'Referer': 'https://www.tepco.co.jp/en/forecast/html/download-e.html'
                }

                response = client.get(url, headers=headers)

                if response.status_code == 404:
                    logger.warning(f"Data not available for {date_str} (404)")
                    return None

                response.raise_for_status()

                # Try different encodings (might be Shift_JIS or UTF-8)
                try:
                    content = response.content.decode('shift_jis')
                except UnicodeDecodeError:
                    content = response.content.decode('utf-8')

                # Parse CSV
                from io import StringIO
                df = pd.read_csv(StringIO(content))

                logger.info(f"✓ Fetched {len(df)} records")
                logger.info(f"Columns: {list(df.columns)[:5]}")

                return df

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching TEPCO data: {e}")
            return None

    def normalize_data(self, raw_df: pd.DataFrame, date: datetime) -> pd.DataFrame:
        """
        Normalize TEPCO CSV to standard format

        TEPCO CSV columns (might vary):
        - TIME or 時刻: Hour (0-23 or 1-24)
        - 実績 or Actual: Actual demand (MW x100)
        - 予測 or Forecast: Forecast demand (MW x100)

        Returns:
            DataFrame with columns: timestamp, demand_mw, forecast_mw, area
        """
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()

        normalized_records = []

        # Detect column names (Japanese or English)
        time_col = None
        actual_col = None
        forecast_col = None

        for col in raw_df.columns:
            col_lower = str(col).lower()
            if 'time' in col_lower or '時刻' in col:
                time_col = col
            elif 'actual' in col_lower or '実績' in col:
                actual_col = col
            elif 'forecast' in col_lower or '予測' in col:
                forecast_col = col

        if not time_col:
            logger.warning(f"Could not find time column in: {list(raw_df.columns)}")
            return pd.DataFrame()

        logger.info(f"Detected columns: time={time_col}, actual={actual_col}, forecast={forecast_col}")

        for _, row in raw_df.iterrows():
            try:
                # Parse hour
                hour_str = str(row[time_col])
                # Remove any non-numeric characters
                hour_str = ''.join(filter(str.isdigit, hour_str))
                if not hour_str:
                    continue

                hour = int(hour_str)
                # TEPCO might use 1-24 or 0-23
                if hour == 24:
                    hour = 0
                elif hour > 24:
                    continue

                # Create timestamp
                timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                timestamp = JST.localize(timestamp)

                # Get demand values (might be in MW*100 format)
                actual_demand = None
                forecast_demand = None

                if actual_col and pd.notna(row[actual_col]):
                    actual_demand = float(row[actual_col])

                if forecast_col and pd.notna(row[forecast_col]):
                    forecast_demand = float(row[forecast_col])

                normalized_records.append({
                    'timestamp': timestamp,
                    'area': 'TOKYO',
                    'demand_mw': actual_demand,
                    'forecast_mw': forecast_demand
                })

            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue

        result = pd.DataFrame(normalized_records)
        logger.info(f"✓ Normalized {len(result)} demand records")

        return result

    def store_demand(self, df: pd.DataFrame):
        """Store demand data in database"""
        if df.empty:
            logger.warning("No demand data to store")
            return

        logger.info(f"Storing {len(df)} demand records...")

        with self.engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO electricity_demand
                    (timestamp, area, demand_mw, forecast_mw)
                    VALUES (:timestamp, :area, :demand, :forecast)
                    ON CONFLICT (timestamp, area)
                    DO UPDATE SET
                        demand_mw = EXCLUDED.demand_mw,
                        forecast_mw = EXCLUDED.forecast_mw
                """), {
                    'timestamp': row['timestamp'],
                    'area': row['area'],
                    'demand': row['demand_mw'],
                    'forecast': row['forecast_mw']
                })

        logger.info(f"✓ Stored {len(df)} records")

    def run(self, start_date: str, end_date: str):
        """
        Fetch TEPCO demand data for date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        logger.info("="*60)
        logger.info("TEPCO Demand Data Ingestion")
        logger.info("="*60)
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Total days: {(end_dt - start_dt).days + 1}")
        logger.info("="*60 + "\n")

        current_date = start_dt
        total_records = 0
        successful_days = 0
        failed_days = 0

        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')

            # Fetch daily data
            raw_df = self.fetch_daily_demand(current_date)

            if raw_df is not None:
                # Normalize data
                normalized_df = self.normalize_data(raw_df, current_date)

                if not normalized_df.empty:
                    # Store in database
                    self.store_demand(normalized_df)
                    total_records += len(normalized_df)
                    successful_days += 1
                else:
                    logger.warning(f"No valid data after normalization for {date_str}")
                    failed_days += 1
            else:
                logger.warning(f"Failed to fetch data for {date_str}")
                failed_days += 1

            # Move to next day
            current_date += timedelta(days=1)

        logger.info("\n" + "="*60)
        logger.info("TEPCO INGESTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Successful days: {successful_days}")
        logger.info(f"Failed days: {failed_days}")
        logger.info(f"Total records: {total_records}")
        logger.info("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Ingest TEPCO electricity demand data'
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

    # Create ingester
    ingester = TEPCODemandIngester(args.database_url)

    # Run ingestion
    try:
        ingester.run(args.start_date, args.end_date)
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
