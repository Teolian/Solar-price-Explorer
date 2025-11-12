#!/usr/bin/env python3
"""
Test JEPX Normalization Logic

Runs the actual normalize_data function with detailed debugging
to identify why it produces 0 records.

Usage:
  docker compose exec api python /etl/test_jepx_normalization.py
"""
import os
import sys
import pandas as pd
from datetime import datetime
import pytz

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Constants (from import_jepx_csv.py)
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

def test_normalization(file_path: str = '/app/data/jepx/spot_2025.csv'):
    """Test normalization with detailed debugging"""

    print('='*80)
    print('JEPX Normalization Test')
    print('='*80)

    # Load CSV
    print(f'Loading: {file_path}')
    try:
        raw_df = pd.read_csv(file_path, encoding='cp932')
        print(f'✓ Loaded {len(raw_df)} rows, {len(raw_df.columns)} columns')
    except Exception as e:
        print(f'✗ Error: {e}')
        return

    print('\nColumns in CSV:')
    for col in raw_df.columns[:10]:
        print(f'  - {col}')
    if len(raw_df.columns) > 10:
        print(f'  ... and {len(raw_df.columns) - 10} more')

    # Test with TOKYO, TOHOKU, HOKKAIDO filter
    areas_filter = ['TOKYO', 'TOHOKU', 'HOKKAIDO']
    print(f'\nFiltering for areas: {areas_filter}')

    print('\n' + '='*80)
    print('TESTING FIRST 5 ROWS')
    print('='*80)

    normalized_records = []
    rows_processed = 0
    max_test_rows = 5

    for _, row in raw_df.iterrows():
        if rows_processed >= max_test_rows:
            break

        rows_processed += 1
        print(f'\n--- ROW {rows_processed} ---')

        # Parse date
        date_col = '年月日' if '年月日' in raw_df.columns else 'Date'
        if date_col not in raw_df.columns:
            print(f'✗ No date column found!')
            continue

        date_str = str(row[date_col])
        print(f'Date: {date_str}')

        try:
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, '%Y/%m/%d')
            elif '-' in date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
            print(f'  Parsed: {date_obj}')
        except Exception as e:
            print(f'✗ Date parse error: {e}')
            continue

        # Parse time code
        slot_col = '時刻コード' if '時刻コード' in raw_df.columns else 'Slot'
        if slot_col not in row:
            print(f'✗ No time code column!')
            continue

        slot = int(row[slot_col])
        hour = (slot - 1) // 2
        minute = 30 if (slot % 2 == 0) else 0
        print(f'Time: Slot {slot} → {hour:02d}:{minute:02d}')

        # Create timestamp
        timestamp = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
        timestamp = JST.localize(timestamp)
        print(f'  Timestamp: {timestamp}')

        # Get system price
        sys_price_col = 'システムプライス' if 'システムプライス' in raw_df.columns else 'System Price'
        system_price = row.get(sys_price_col, None)
        print(f'System Price: {system_price}')

        # Test each area
        records_this_row = 0
        for jp_name, en_name in AREA_MAPPING.items():
            if areas_filter and en_name not in areas_filter:
                continue

            print(f'\n  Testing area: {jp_name} ({en_name})')

            # Find column
            area_col = None
            for col in raw_df.columns:
                if jp_name in col and 'エリアプライス' in col:
                    area_col = col
                    break

            if area_col:
                print(f'    ✓ Found column: "{area_col}"')
                area_price = row[area_col]
                print(f'    Price value: {area_price} (type: {type(area_price).__name__})')

                # Check if valid
                if pd.isna(area_price):
                    print(f'    ✗ Price is NaN - skipping')
                    continue

                if area_price == '':
                    print(f'    ✗ Price is empty string - skipping')
                    continue

                try:
                    price_float = float(area_price)
                    print(f'    ✓ Converted to float: {price_float}')

                    record = {
                        'timestamp': timestamp,
                        'area': en_name,
                        'area_price_jpy_kwh': price_float,
                        'system_price_jpy_kwh': float(system_price) if pd.notna(system_price) else None
                    }
                    normalized_records.append(record)
                    records_this_row += 1
                    print(f'    ✓ RECORD CREATED')

                except (ValueError, TypeError) as e:
                    print(f'    ✗ Conversion error: {e}')
            else:
                print(f'    ✗ NO COLUMN FOUND')
                # Debug: show what columns we searched
                matching_area = [col for col in raw_df.columns if jp_name in col]
                matching_price = [col for col in raw_df.columns if 'エリアプライス' in col]
                print(f'    Columns with "{jp_name}": {len(matching_area)}')
                if matching_area and len(matching_area) <= 3:
                    for col in matching_area:
                        print(f'      - {col}')
                print(f'    Columns with "エリアプライス": {len(matching_price)}')

        print(f'\n  → Created {records_this_row} records from this row')

    print('\n' + '='*80)
    print('NORMALIZATION TEST RESULTS')
    print('='*80)
    print(f'Rows processed: {rows_processed}')
    print(f'Records created: {len(normalized_records)}')

    if normalized_records:
        print('\n✓ Normalization WORKS!')
        print(f'\nFirst record:')
        for key, value in normalized_records[0].items():
            print(f'  {key}: {value}')

        # Now test full file
        print('\n' + '='*80)
        print('RUNNING FULL NORMALIZATION')
        print('='*80)
        all_records = normalize_full(raw_df, areas_filter)
        print(f'\n✓ Full normalization: {len(all_records)} records')

        if all_records:
            result_df = pd.DataFrame(all_records)
            print(f'\nAreas: {sorted(result_df["area"].unique())}')
            print(f'Date range: {result_df["timestamp"].min()} to {result_df["timestamp"].max()}')
            print(f'Records per area:')
            for area, count in result_df['area'].value_counts().items():
                print(f'  {area}: {count:,}')
        else:
            print('✗ Full normalization produced 0 records!')
    else:
        print('\n✗ Normalization FAILED - 0 records created')
        print('\nPossible issues:')
        print('  1. Column names don\'t match expected pattern')
        print('  2. All prices are NaN or empty')
        print('  3. Date/time parsing fails')
        print('\nRun debug_jepx_import.py for detailed column analysis')

    print('='*80)

def normalize_full(raw_df: pd.DataFrame, areas_filter=None):
    """Full normalization without debug output"""
    normalized_records = []

    date_col = '年月日' if '年月日' in raw_df.columns else 'Date'
    slot_col = '時刻コード' if '時刻コード' in raw_df.columns else 'Slot'
    sys_price_col = 'システムプライス' if 'システムプライス' in raw_df.columns else 'System Price'

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

            # Parse time
            slot = int(row[slot_col])
            hour = (slot - 1) // 2
            minute = 30 if (slot % 2 == 0) else 0

            timestamp = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
            timestamp = JST.localize(timestamp)

            system_price = row.get(sys_price_col, None)

            # Extract prices for each area
            for jp_name, en_name in AREA_MAPPING.items():
                if areas_filter and en_name not in areas_filter:
                    continue

                # Find column
                area_col = None
                for col in raw_df.columns:
                    if jp_name in col and 'エリアプライス' in col:
                        area_col = col
                        break

                if area_col and area_col in row:
                    area_price = row[area_col]

                    if pd.isna(area_price) or area_price == '':
                        continue

                    try:
                        normalized_records.append({
                            'timestamp': timestamp,
                            'area': en_name,
                            'area_price_jpy_kwh': float(area_price),
                            'system_price_jpy_kwh': float(system_price) if pd.notna(system_price) else None
                        })
                    except (ValueError, TypeError):
                        pass

        except Exception:
            pass

    return normalized_records

if __name__ == '__main__':
    test_normalization()
