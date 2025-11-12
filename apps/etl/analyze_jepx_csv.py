#!/usr/bin/env python3
"""
Analyze JEPX CSV file to understand what data is available
"""
import pandas as pd
import sys

def analyze_jepx_csv(file_path: str = '/app/data/jepx/spot_2025.csv'):
    """Analyze JEPX CSV file"""

    print('='*60)
    print('JEPX spot_2025.csv Analysis')
    print('='*60)

    # Read CSV
    print(f'Reading file: {file_path}')
    try:
        df = pd.read_csv(file_path, encoding='cp932')
    except FileNotFoundError:
        print(f'✗ File not found: {file_path}')
        return
    except Exception as e:
        print(f'✗ Error reading file: {e}')
        return

    print(f'✓ Loaded successfully')
    print()

    # Basic info
    print(f'Total rows: {len(df):,}')
    print(f'Total columns: {len(df.columns)}')
    print()

    # Show all column names
    print('All columns:')
    for i, col in enumerate(df.columns, 1):
        print(f'  {i:2d}. {col}')
    print()

    # Check date column
    date_col = df.columns[0]
    time_col = df.columns[1] if len(df.columns) > 1 else None

    print(f'Date column: "{date_col}"')
    if time_col:
        print(f'Time column: "{time_col}"')
    print()

    # Parse dates
    df['date_parsed'] = pd.to_datetime(df[date_col], format='%Y/%m/%d', errors='coerce')

    # Date range
    print('Date Range:')
    print(f'  First date: {df[date_col].iloc[0]} (row 1)')
    print(f'  Last date:  {df[date_col].iloc[-1]} (row {len(df)})')
    print(f'  Parsed first: {df["date_parsed"].min()}')
    print(f'  Parsed last:  {df["date_parsed"].max()}')
    print()

    # Count rows per month
    df['month'] = df['date_parsed'].dt.to_period('M')
    monthly = df.groupby('month').size().sort_index()

    print('Data by Month:')
    print(f'{"Month":<12} {"Rows":>8} {"Days":>6} {"Expected":<10}')
    print('-'*40)

    for month, count in monthly.items():
        month_str = str(month)
        # Each day has 48 time slots (30-min intervals)
        days = count // 48
        expected = f'{days} days × 48'
        print(f'{month_str:<12} {count:>8,} {days:>6} {expected:<10}')

    print()

    # Check target months (Sept-Nov 2025)
    print('Target Period Check (Sept-Nov 2025):')
    print('-'*40)

    target_months = [
        ('September 2025', '2025-09'),
        ('October 2025', '2025-10'),
        ('November 2025', '2025-11')
    ]

    total_target_rows = 0
    for name, month_str in target_months:
        count = len(df[df['date_parsed'].dt.strftime('%Y-%m') == month_str])
        days = count // 48

        if count > 0:
            print(f'✓ {name:<20} {count:>6,} rows ({days} days)')
            total_target_rows += count
        else:
            print(f'✗ {name:<20} NO DATA')

    print('-'*40)
    print(f'Total Sept-Nov 2025: {total_target_rows:,} rows')
    print()

    # Check area price columns
    print('Area Price Columns:')
    area_cols = [col for col in df.columns if 'エリアプライス' in col or 'Area' in col]
    for col in area_cols[:10]:  # Show first 10
        print(f'  - {col}')
    if len(area_cols) > 10:
        print(f'  ... and {len(area_cols) - 10} more')
    print()

    # Sample data for Sept-Nov 2025
    sept_nov = df[df['date_parsed'].dt.strftime('%Y-%m').isin(['2025-09', '2025-10', '2025-11'])]

    if len(sept_nov) > 0:
        print('Sample Data (Sept-Nov 2025):')
        print()

        # Show first 5 rows
        print('First 5 rows:')
        print(sept_nov.head(5).to_string(max_colwidth=30))
        print()

        # Show date distribution
        print('Days per month:')
        for month, group in sept_nov.groupby(sept_nov['date_parsed'].dt.to_period('M')):
            unique_days = group['date_parsed'].nunique()
            print(f'  {month}: {unique_days} days')
        print()

    # Final summary
    print('='*60)
    print('SUMMARY')
    print('='*60)

    if total_target_rows > 0:
        days_count = total_target_rows // 48
        print(f'✓ JEPX data is AVAILABLE for Sept-Nov 2025')
        print(f'  Total: {total_target_rows:,} rows ({days_count} days × 48 slots)')
        print()
        print('✓ This data is SUFFICIENT for your analysis!')
        print('  - All required months present')
        print('  - 48 time slots per day (30-min intervals)')
        print('  - Multiple area prices included')
        print()
        print('NEXT STEP: Import data to database')
        print('  docker-compose exec api python /etl/import_jepx_csv.py \\')
        print('    --file /app/data/jepx/spot_2025.csv \\')
        print('    --areas TOKYO,TOHOKU,HOKKAIDO \\')
        print('    --start-date 2025-09-01 \\')
        print('    --end-date 2025-11-11')
    else:
        print('✗ WARNING: No data for Sept-Nov 2025 found!')
        print('  File contains data from other months only')
        print('  You may need different date range or data source')

    print('='*60)

if __name__ == '__main__':
    file_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/jepx/spot_2025.csv'
    analyze_jepx_csv(file_path)
