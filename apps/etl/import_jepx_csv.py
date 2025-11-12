#!/usr/bin/env python3
"""
Import manually downloaded JEPX CSV files into database

USAGE:
  1. Download CSV from JEPX website manually:
     - Go to https://www.jepx.jp/electricpower/market-data/spot/
     - Click "Data Download" button
     - Select year and download spot_YYYY.csv or spot_summary_YYYY.csv

  2. Place downloaded file in data/jepx/ directory

  3. Run this script:
     python import_jepx_csv.py --file data/jepx/spot_2024.csv --areas TOKYO,TOHOKU,HOKKAIDO

JEPX CSV FORMAT:
  - Encoding: Shift_JIS (cp932)
  - Columns: 年月日, 時刻コード (1-48), システムプライス, area prices (北海道, 東北, etc.)
  - Time codes: 1-48 for 30-minute intervals (1=00:00-00:30, 2=00:30-01:00, etc.)
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Optional
import pytz
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def load_csv(file_path: str) -> pd.DataFrame:
    """Load JEPX CSV with proper encoding"""
    logger.info(f"Loading CSV from {file_path}")

    try:
        # Try CP932 (Shift_JIS) first
        df = pd.read_csv(file_path, encoding='cp932')
        logger.info(f"Loaded with cp932 encoding")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='shift_jis')
            logger.info(f"Loaded with shift_jis encoding")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='utf-8')
            logger.info(f"Loaded with utf-8 encoding")

    logger.info(f"Loaded {len(df)} rows")
    logger.info(f"Columns: {list(df.columns)[:10]}")

    return df

def normalize_data(raw_df: pd.DataFrame, areas_filter: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Normalize JEPX CSV to standard format

    Handles:
    - Date parsing (年月日: YYYY/MM/DD, YYYY-MM-DD, or YYYYMMDD)
    - Time code mapping (時刻コード 1-48 → hourly timestamps)
    - Area name mapping (Japanese → English)
    - Price extraction per area
    """
    logger.info("Normalizing JEPX data...")

    normalized_records = []

    for _, row in raw_df.iterrows():
        # Parse date (年月日 or Date)
        date_col = '年月日' if '年月日' in raw_df.columns else 'Date'
        date_str = str(row[date_col])

        # Normalize date format
        if '/' in date_str:
            date_obj = datetime.strptime(date_str, '%Y/%m/%d')
        elif '-' in date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = datetime.strptime(date_str, '%Y%m%d')

        # Parse time code (時刻コード or Slot)
        # JEPX uses 48 codes: 1=00:00, 2=00:30, ..., 48=23:30
        slot_col = '時刻コード' if '時刻コード' in raw_df.columns else 'Slot'
        if slot_col not in row:
            logger.warning(f"No time code column found, skipping row")
            continue

        slot = int(row[slot_col])
        hour = (slot - 1) // 2
        minute = 30 if (slot % 2 == 0) else 0

        # Create timestamp
        timestamp = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
        timestamp = JST.localize(timestamp)

        # Get system price
        sys_price_col = 'システムプライス' if 'システムプライス' in raw_df.columns else 'System Price'
        system_price = row.get(sys_price_col, None)

        # Extract prices for each area
        for jp_name, en_name in AREA_MAPPING.items():
            # Skip if filtering areas and this area not in filter
            if areas_filter and en_name not in areas_filter:
                continue

            # Find column that contains the area name
            # Columns are like: エリアプライス北海道(円/kWh)
            # We search for columns containing the area name (北海道, 東京, etc.)
            area_col = None
            for col in raw_df.columns:
                if jp_name in col and 'エリアプライス' in col:
                    area_col = col
                    break

            if area_col and area_col in row:
                area_price = row[area_col]

                # Skip if price is null or empty
                if pd.isna(area_price) or area_price == '':
                    continue

                try:
                    normalized_records.append({
                        'timestamp': timestamp,
                        'area': en_name,
                        'area_price_jpy_kwh': float(area_price),
                        'system_price_jpy_kwh': float(system_price) if pd.notna(system_price) else None
                    })
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not convert price for {en_name} at {timestamp}: {area_price}")

    if not normalized_records:
        logger.error("No valid records after normalization!")
        return pd.DataFrame()

    result = pd.DataFrame(normalized_records)
    logger.info(f"Normalized to {len(result)} records across {result['area'].nunique()} areas")

    return result

def store_prices(df: pd.DataFrame, database_url: str):
    """Store normalized prices in database"""
    logger.info(f"Storing {len(df)} price records to database...")

    engine = create_engine(database_url)

    # Use upsert to handle duplicates
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO prices
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

    logger.info(f"✓ Successfully stored {len(df)} records")

def main():
    parser = argparse.ArgumentParser(description='Import manually downloaded JEPX CSV files')
    parser.add_argument('--file', required=True, help='Path to JEPX CSV file')
    parser.add_argument('--areas', type=str, help='Comma-separated list of areas (e.g., TOKYO,TOHOKU,HOKKAIDO)')
    parser.add_argument('--database-url', type=str,
                       default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/solar_prices'),
                       help='Database URL')

    args = parser.parse_args()

    # Parse areas filter
    areas_filter = None
    if args.areas:
        areas_filter = [a.strip().upper() for a in args.areas.split(',')]
        logger.info(f"Filtering for areas: {areas_filter}")

    # Check file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        logger.info("\nHOW TO GET JEPX DATA:")
        logger.info("1. Go to https://www.jepx.jp/electricpower/market-data/spot/")
        logger.info("2. Click 'Data Download' button")
        logger.info("3. Select year and download spot_YYYY.csv")
        logger.info(f"4. Save to {args.file}")
        return 1

    # Load CSV
    raw_df = load_csv(args.file)

    # Normalize data
    normalized_df = normalize_data(raw_df, areas_filter)

    if normalized_df.empty:
        logger.error("No data to import!")
        return 1

    # Show preview
    logger.info("\nData preview:")
    logger.info(f"\n{normalized_df.head(10).to_string()}")
    logger.info(f"\nDate range: {normalized_df['timestamp'].min()} to {normalized_df['timestamp'].max()}")
    logger.info(f"Areas: {sorted(normalized_df['area'].unique())}")

    # Store in database
    store_prices(normalized_df, args.database_url)

    logger.info("\n✓ Import complete!")

    return 0

if __name__ == '__main__':
    sys.exit(main())
