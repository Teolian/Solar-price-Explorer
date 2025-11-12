#!/usr/bin/env python3
"""
Debug JEPX CSV Import - Identify Column Matching Issues

This script helps diagnose why import_jepx_csv.py fails with
"No valid records after normalization!"

Usage:
  docker compose exec api python /etl/debug_jepx_import.py
"""
import pandas as pd
from pathlib import Path

# Area mapping from import script
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

def debug_csv_structure(file_path: str = '/app/data/jepx/spot_2025.csv'):
    """Debug CSV structure and column matching"""

    print('='*80)
    print('JEPX CSV Import Debug')
    print('='*80)
    print(f'File: {file_path}')
    print()

    # Load CSV
    try:
        df = pd.read_csv(file_path, encoding='cp932')
        print(f'✓ Loaded successfully: {len(df)} rows, {len(df.columns)} columns')
    except FileNotFoundError:
        print(f'✗ File not found: {file_path}')
        return
    except Exception as e:
        print(f'✗ Error loading: {e}')
        return

    print()
    print('='*80)
    print('ALL COLUMN NAMES')
    print('='*80)
    for i, col in enumerate(df.columns, 1):
        print(f'{i:3d}. {col}')

    print()
    print('='*80)
    print('AREA PRICE COLUMNS (matching logic test)')
    print('='*80)

    # Test matching logic for each area
    areas_filter = ['TOKYO', 'TOHOKU', 'HOKKAIDO']

    for jp_name, en_name in AREA_MAPPING.items():
        # Skip if filtering and not in filter
        if areas_filter and en_name not in areas_filter:
            continue

        print(f'\nTesting: {jp_name} → {en_name}')
        print(f'  Looking for columns containing: "{jp_name}" AND "エリアプライス"')

        # Method 1: OLD (broken) - exact column name
        found_exact = jp_name in df.columns
        print(f'  Method 1 (exact match "{jp_name}"): {found_exact}')

        # Method 2: NEW (should work) - substring search
        area_col = None
        for col in df.columns:
            if jp_name in col and 'エリアプライス' in col:
                area_col = col
                break

        if area_col:
            print(f'  Method 2 (substring search): ✓ FOUND')
            print(f'    Column: "{area_col}"')
            print(f'    Sample values:')
            sample_values = df[area_col].head(5).tolist()
            for i, val in enumerate(sample_values, 1):
                print(f'      Row {i}: {val}')
        else:
            print(f'  Method 2 (substring search): ✗ NOT FOUND')
            print(f'    Searched all {len(df.columns)} columns')

            # Show columns that contain the area name
            matching_cols = [col for col in df.columns if jp_name in col]
            if matching_cols:
                print(f'    Columns containing "{jp_name}":')
                for col in matching_cols:
                    print(f'      - {col}')

            # Show columns containing エリアプライス
            price_cols = [col for col in df.columns if 'エリアプライス' in col]
            if price_cols and len(price_cols) <= 3:
                print(f'    Columns containing "エリアプライス":')
                for col in price_cols:
                    print(f'      - {col}')

    print()
    print('='*80)
    print('DATE AND TIME COLUMNS')
    print('='*80)

    # Check for date column
    date_col = '年月日' if '年月日' in df.columns else 'Date'
    if date_col in df.columns:
        print(f'✓ Date column found: "{date_col}"')
        print(f'  Sample values: {df[date_col].head(3).tolist()}')
    else:
        print(f'✗ Date column not found (expected "年月日" or "Date")')

    # Check for time code column
    slot_col = '時刻コード' if '時刻コード' in df.columns else 'Slot'
    if slot_col in df.columns:
        print(f'✓ Time code column found: "{slot_col}"')
        print(f'  Sample values: {df[slot_col].head(3).tolist()}')
    else:
        print(f'✗ Time code column not found (expected "時刻コード" or "Slot")')

    # Check for system price
    sys_price_col = 'システムプライス' if 'システムプライス' in df.columns else 'System Price'
    if sys_price_col in df.columns:
        print(f'✓ System price column found: "{sys_price_col}"')
        print(f'  Sample values: {df[sys_price_col].head(3).tolist()}')
    else:
        print(f'✗ System price column not found')

    print()
    print('='*80)
    print('FIRST ROW COMPLETE')
    print('='*80)
    print(df.iloc[0].to_string())

    print()
    print('='*80)
    print('SUMMARY')
    print('='*80)

    # Count how many area columns we can find
    found_areas = []
    for jp_name, en_name in AREA_MAPPING.items():
        if areas_filter and en_name not in areas_filter:
            continue

        for col in df.columns:
            if jp_name in col and 'エリアプライス' in col:
                found_areas.append(en_name)
                break

    if found_areas:
        print(f'✓ Found {len(found_areas)} area price columns for filtered areas')
        print(f'  Areas: {", ".join(found_areas)}')

        # Estimate records that should be imported
        total_rows = len(df)
        expected_records = total_rows * len(found_areas)
        print(f'\n✓ Expected import: {expected_records:,} records')
        print(f'  ({total_rows:,} rows × {len(found_areas)} areas)')
    else:
        print(f'✗ NO area price columns found!')
        print(f'  This will cause "No valid records after normalization!"')
        print(f'\nPossible reasons:')
        print(f'  1. CSV structure different than expected')
        print(f'  2. Encoding issue (should be cp932)')
        print(f'  3. Wrong file downloaded')

    print('='*80)

if __name__ == '__main__':
    debug_csv_structure()
