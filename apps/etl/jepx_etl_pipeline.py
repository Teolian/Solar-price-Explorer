#!/usr/bin/env python3
"""
Complete JEPX ETL Pipeline

Automated pipeline that:
1. Downloads JEPX CSV using Playwright (bypasses WAF)
2. Decodes from CP932/Shift_JIS
3. Normalizes time codes (時刻コード 1-48 → timestamps)
4. Partitions data by date
5. Loads into PostgreSQL with upsert

USAGE:
  # Download and process 2024 data
  python jepx_etl_pipeline.py --year 2024 --areas TOKYO,TOHOKU,HOKKAIDO

  # Process existing file
  python jepx_etl_pipeline.py --file data/jepx/spot_2024.csv --skip-download

  # Full pipeline with all steps
  python jepx_etl_pipeline.py --year 2025 --start-date 2025-09-01 --end-date 2025-11-10
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import pytz

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JST = pytz.timezone('Asia/Tokyo')
AREA_MAPPING = {
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


class JEPXETLPipeline:
    """Complete ETL pipeline for JEPX data"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)

    def run(
        self,
        year: Optional[int] = None,
        file_path: Optional[str] = None,
        skip_download: bool = False,
        areas_filter: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_playwright: bool = True
    ) -> Dict:
        """
        Run complete ETL pipeline

        Args:
            year: Year to download (if not using existing file)
            file_path: Path to existing CSV file (if skip_download=True)
            skip_download: Skip download step, use existing file
            areas_filter: List of areas to process (e.g., ['TOKYO', 'TOHOKU'])
            start_date: Filter data from this date (YYYY-MM-DD)
            end_date: Filter data to this date (YYYY-MM-DD)
            use_playwright: Use Playwright for download (default: True)

        Returns:
            Dictionary with pipeline statistics
        """
        stats = {
            'downloaded': False,
            'downloaded_path': None,
            'raw_rows': 0,
            'normalized_rows': 0,
            'inserted_rows': 0,
            'date_range': None,
            'areas': [],
            'errors': []
        }

        try:
            # Step 1: Download or locate file
            if skip_download:
                if not file_path or not os.path.exists(file_path):
                    raise ValueError(f"File not found: {file_path}")
                csv_path = file_path
                logger.info(f"Using existing file: {csv_path}")
            else:
                csv_path = self._download_data(year, use_playwright)
                stats['downloaded'] = True
                stats['downloaded_path'] = csv_path

            # Step 2: Load and decode CSV (CP932)
            logger.info("\n" + "="*60)
            logger.info("STEP 2: Loading and decoding CSV")
            logger.info("="*60)
            raw_df = self._load_csv(csv_path)
            stats['raw_rows'] = len(raw_df)
            logger.info(f"Loaded {len(raw_df)} raw rows")

            # Step 3: Normalize data (time codes, area names, etc.)
            logger.info("\n" + "="*60)
            logger.info("STEP 3: Normalizing data")
            logger.info("="*60)
            normalized_df = self._normalize_data(raw_df, areas_filter)
            stats['normalized_rows'] = len(normalized_df)
            logger.info(f"Normalized to {len(normalized_df)} rows")

            if normalized_df.empty:
                logger.warning("No data after normalization!")
                return stats

            # Step 4: Filter by date range if specified
            if start_date or end_date:
                logger.info("\n" + "="*60)
                logger.info("STEP 4: Filtering by date range")
                logger.info("="*60)
                normalized_df = self._filter_by_date(
                    normalized_df,
                    start_date,
                    end_date
                )
                logger.info(f"Filtered to {len(normalized_df)} rows")

            # Step 5: Partition data by date (for efficient storage)
            logger.info("\n" + "="*60)
            logger.info("STEP 5: Analyzing data partitions")
            logger.info("="*60)
            partitions = self._analyze_partitions(normalized_df)
            logger.info(f"Data spans {len(partitions)} days")
            for date, count in list(partitions.items())[:5]:
                logger.info(f"  {date}: {count} records")
            if len(partitions) > 5:
                logger.info(f"  ... and {len(partitions)-5} more days")

            # Collect stats
            stats['date_range'] = (
                normalized_df['timestamp'].min().strftime('%Y-%m-%d'),
                normalized_df['timestamp'].max().strftime('%Y-%m-%d')
            )
            stats['areas'] = sorted(normalized_df['area'].unique().tolist())

            # Step 6: Load into PostgreSQL with upsert
            logger.info("\n" + "="*60)
            logger.info("STEP 6: Loading into PostgreSQL")
            logger.info("="*60)
            inserted = self._load_to_postgres(normalized_df)
            stats['inserted_rows'] = inserted
            logger.info(f"✓ Inserted/updated {inserted} records")

            # Step 7: Summary
            logger.info("\n" + "="*60)
            logger.info("PIPELINE COMPLETE!")
            logger.info("="*60)
            logger.info(f"Raw rows loaded:      {stats['raw_rows']:,}")
            logger.info(f"Normalized rows:      {stats['normalized_rows']:,}")
            logger.info(f"Inserted to DB:       {stats['inserted_rows']:,}")
            logger.info(f"Date range:           {stats['date_range'][0]} to {stats['date_range'][1]}")
            logger.info(f"Areas processed:      {', '.join(stats['areas'])}")
            logger.info("="*60 + "\n")

            return stats

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            stats['errors'].append(str(e))
            raise

    def _download_data(self, year: int, use_playwright: bool) -> str:
        """Download JEPX data"""
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Downloading JEPX data")
        logger.info("="*60)

        output_path = f"data/jepx/spot_{year}.csv"

        if use_playwright:
            logger.info(f"Using Playwright to download year {year}")
            try:
                from download_jepx_playwright import JEPXDownloader

                downloader = JEPXDownloader(headless=True, slow_mo=100)
                success = downloader.download_spot_data(
                    year=year,
                    output_path=output_path,
                    data_type="spot"
                )

                if not success:
                    raise Exception("Playwright download failed")

                logger.info(f"✓ Downloaded to {output_path}")
                return output_path

            except ImportError:
                logger.warning("Playwright not available, falling back to manual instructions")
                self._print_manual_instructions(year, output_path)
                raise Exception("Playwright not installed. Install with: pip install playwright && playwright install chromium")

        else:
            # Manual download instructions
            self._print_manual_instructions(year, output_path)
            raise Exception("Automated download disabled. Please download manually.")

    def _print_manual_instructions(self, year: int, output_path: str):
        """Print manual download instructions"""
        logger.info("\n" + "="*60)
        logger.info("MANUAL DOWNLOAD REQUIRED")
        logger.info("="*60)
        logger.info("1. Go to: https://www.jepx.jp/electricpower/market-data/spot/")
        logger.info("2. Click 'Data Download' button")
        logger.info(f"3. Select year {year}")
        logger.info(f"4. Save file as: {output_path}")
        logger.info(f"5. Re-run with: --file {output_path} --skip-download")
        logger.info("="*60 + "\n")

    def _load_csv(self, file_path: str) -> pd.DataFrame:
        """Load CSV with proper CP932 encoding"""
        try:
            df = pd.read_csv(file_path, encoding='cp932')
            logger.info(f"✓ Decoded with CP932 encoding")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='shift_jis')
                logger.info(f"✓ Decoded with Shift_JIS encoding")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='utf-8')
                logger.info(f"✓ Decoded with UTF-8 encoding")

        logger.info(f"Columns: {list(df.columns)[:10]}")
        return df

    def _normalize_data(
        self,
        raw_df: pd.DataFrame,
        areas_filter: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Normalize JEPX data:
        - Parse dates (年月日)
        - Map time codes (時刻コード 1-48 → timestamps)
        - Map area names (Japanese → English)
        - Extract prices per area
        """
        normalized_records = []

        for idx, row in raw_df.iterrows():
            if idx % 1000 == 0:
                logger.info(f"  Processing row {idx:,}/{len(raw_df):,}")

            # Parse date
            date_col = '年月日' if '年月日' in raw_df.columns else 'Date'
            date_str = str(row[date_col])

            # Normalize date format
            try:
                if '/' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                elif '-' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
            except ValueError as e:
                logger.warning(f"Invalid date format: {date_str}, skipping")
                continue

            # Parse time code (時刻コード 1-48)
            slot_col = '時刻コード' if '時刻コード' in raw_df.columns else 'Slot'
            if slot_col not in row or pd.isna(row[slot_col]):
                continue

            slot = int(row[slot_col])
            hour = (slot - 1) // 2
            minute = 30 if (slot % 2 == 0) else 0

            # Create timestamp
            timestamp = date_obj.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            timestamp = JST.localize(timestamp)

            # Get system price
            sys_price_col = 'システムプライス' if 'システムプライス' in raw_df.columns else 'System Price'
            system_price = row.get(sys_price_col, None)

            # Extract prices for each area
            for jp_name, en_name in AREA_MAPPING.items():
                if areas_filter and en_name not in areas_filter:
                    continue

                if jp_name in raw_df.columns:
                    area_price = row[jp_name]

                    if pd.isna(area_price):
                        continue

                    normalized_records.append({
                        'timestamp': timestamp,
                        'area': en_name,
                        'area_price_jpy_kwh': float(area_price),
                        'system_price_jpy_kwh': float(system_price) if pd.notna(system_price) else None
                    })

        result = pd.DataFrame(normalized_records)
        logger.info(f"✓ Normalized {len(result):,} records")

        if not result.empty:
            logger.info(f"  Date range: {result['timestamp'].min()} to {result['timestamp'].max()}")
            logger.info(f"  Areas: {sorted(result['area'].unique())}")

        return result

    def _filter_by_date(
        self,
        df: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """Filter data by date range"""
        if start_date:
            start_dt = JST.localize(datetime.strptime(start_date, '%Y-%m-%d'))
            df = df[df['timestamp'] >= start_dt]
            logger.info(f"  Filtered from {start_date}: {len(df)} rows")

        if end_date:
            end_dt = JST.localize(datetime.strptime(end_date, '%Y-%m-%d'))
            # Include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            df = df[df['timestamp'] <= end_dt]
            logger.info(f"  Filtered to {end_date}: {len(df)} rows")

        return df

    def _analyze_partitions(self, df: pd.DataFrame) -> Dict[str, int]:
        """Analyze data by date partitions"""
        df['date'] = df['timestamp'].dt.date
        partitions = df.groupby('date').size().to_dict()
        return {str(k): v for k, v in partitions.items()}

    def _load_to_postgres(self, df: pd.DataFrame) -> int:
        """Load data to PostgreSQL with upsert"""
        inserted = 0

        with self.engine.begin() as conn:
            for idx, row in df.iterrows():
                if idx % 500 == 0 and idx > 0:
                    logger.info(f"  Inserted {idx:,}/{len(df):,} rows")

                conn.execute(text("""
                    INSERT INTO jepx_prices
                    (timestamp, area, area_price_jpy_kwh, system_price_jpy_kwh,
                     volume_total_kwh, volume_sell_kwh, volume_buy_kwh)
                    VALUES (:timestamp, :area, :area_price, :system_price, NULL, NULL, NULL)
                    ON CONFLICT (timestamp, area)
                    DO UPDATE SET
                        area_price_jpy_kwh = EXCLUDED.area_price_jpy_kwh,
                        system_price_jpy_kwh = EXCLUDED.system_price_jpy_kwh
                """), {
                    'timestamp': row['timestamp'],
                    'area': row['area'],
                    'area_price': row['area_price_jpy_kwh'],
                    'system_price': row['system_price_jpy_kwh']
                })
                inserted += 1

        return inserted


def main():
    parser = argparse.ArgumentParser(
        description='Complete JEPX ETL Pipeline'
    )
    parser.add_argument(
        '--year',
        type=int,
        help='Year to download (e.g., 2024, 2025)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to existing CSV file (use with --skip-download)'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip download step, use existing file'
    )
    parser.add_argument(
        '--areas',
        type=str,
        help='Comma-separated areas (e.g., TOKYO,TOHOKU,HOKKAIDO)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Filter from date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Filter to date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--no-playwright',
        action='store_true',
        help='Disable Playwright automation'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/solar_prices'),
        help='Database URL'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.skip_download and not args.year:
        parser.error("--year is required unless --skip-download is used")

    if args.skip_download and not args.file:
        parser.error("--file is required when --skip-download is used")

    # Parse areas filter
    areas_filter = None
    if args.areas:
        areas_filter = [a.strip().upper() for a in args.areas.split(',')]

    # Create pipeline
    pipeline = JEPXETLPipeline(args.database_url)

    # Run pipeline
    try:
        stats = pipeline.run(
            year=args.year,
            file_path=args.file,
            skip_download=args.skip_download,
            areas_filter=areas_filter,
            start_date=args.start_date,
            end_date=args.end_date,
            use_playwright=not args.no_playwright
        )

        logger.info("\n✅ Pipeline completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
