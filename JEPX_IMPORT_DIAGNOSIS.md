# JEPX Import Diagnosis & Fix Guide

## Problem Summary

**Issue**: JEPX CSV import failing with "No valid records after normalization!"

```
Loaded 10848 rows
ERROR - No valid records after normalization!
ERROR - No data to import!
```

**Expected**: Should import ~3,504 records for Sept-Nov 2025 (73 days × 48 slots × 3 areas)

## Current Status

✅ **Data Downloaded**: `/app/data/jepx/spot_2025.csv` (2.7MB, 10,848 rows)
✅ **Data Available**: Contains April-November 2025 data
✅ **Target Period**: Sept-Nov 2025 data is present (3,504 rows)
❌ **Import Failing**: Column matching logic issue

## Root Cause Analysis

The `normalize_data()` function in `import_jepx_csv.py` is likely failing to match column names.

### Expected Column Names

JEPX CSV should have columns like:
- `年月日` (Date)
- `時刻コード` (Time code: 1-48)
- `システムプライス(円/kWh)` (System price)
- `エリアプライス北海道(円/kWh)` (Hokkaido area price)
- `エリアプライス東北(円/kWh)` (Tohoku area price)
- `エリアプライス東京(円/kWh)` (Tokyo area price)
- ... etc for all 9 areas

### Current Matching Logic

The code searches for columns containing BOTH:
1. Area name (e.g., `北海道`, `東北`, `東京`)
2. Prefix `エリアプライス`

```python
for col in raw_df.columns:
    if jp_name in col and 'エリアプライス' in col:
        area_col = col
        break
```

## Diagnostic Commands

Run these to identify the exact issue:

### 1. Analyze CSV Structure
```bash
make analyze-jepx-csv
```

Shows:
- Date range and row counts
- What months are available
- How many days × 48 slots

### 2. Debug Column Matching
```bash
make debug-jepx-structure
```

Shows:
- All column names in the CSV
- Which columns match the search pattern
- Sample values for each found column

### 3. Test Normalization Logic
```bash
make test-jepx-normalization
```

Shows:
- Step-by-step normalization of first 5 rows
- Exactly where the process fails
- What records are created (if any)

## Diagnosis Steps

### Step 1: Check CSV Structure

```bash
docker compose exec api python /etl/debug_jepx_import.py
```

**Look for**:
- Are there columns with `エリアプライス`?
- Are the area names spelled correctly?
- Is the encoding correct (should be CP932)?

### Step 2: Test Normalization

```bash
docker compose exec api python /etl/test_jepx_normalization.py
```

**Look for**:
- Does it find area columns for Tokyo, Tohoku, Hokkaido?
- Are prices valid numbers (not NaN)?
- Does it create any records from first 5 rows?

### Step 3: Check Actual Column Names

```bash
docker compose exec api python3 -c "
import pandas as pd
df = pd.read_csv('/app/data/jepx/spot_2025.csv', encoding='cp932')
print('All columns:')
for col in df.columns:
    print(f'  {col}')
"
```

## Possible Issues & Fixes

### Issue 1: Column Names Different Than Expected

**Symptom**: debug shows no columns with `エリアプライス`

**Possible actual format**:
- `北海道(円/kWh)` (no prefix)
- `HOKKAIDO` (English names)
- `Area Price - Hokkaido` (different format)

**Fix**: Update matching logic in `import_jepx_csv.py` line 132-136:

```python
# Try multiple patterns
area_col = None

# Pattern 1: エリアプライス prefix
for col in raw_df.columns:
    if jp_name in col and 'エリアプライス' in col:
        area_col = col
        break

# Pattern 2: Just area name with price indicator
if not area_col:
    for col in raw_df.columns:
        if jp_name in col and ('円' in col or 'kWh' in col):
            area_col = col
            break

# Pattern 3: English names
if not area_col:
    for col in raw_df.columns:
        if en_name in col.upper():
            area_col = col
            break
```

### Issue 2: Encoding Issue

**Symptom**: Column names are garbled or unreadable

**Fix**: Try different encodings:

```python
# Try these in order:
df = pd.read_csv(file_path, encoding='cp932')  # Current
df = pd.read_csv(file_path, encoding='shift_jis')  # Alternative
df = pd.read_csv(file_path, encoding='utf-8')  # If converted
```

### Issue 3: All Prices are NaN

**Symptom**: Columns found but all prices are null/empty

**Possible reasons**:
- Wrong file downloaded (metadata only)
- Prices in different columns
- Need to skip header rows

**Fix**: Check first few rows:

```python
print(df.head(10))
print(df.dtypes)
```

### Issue 4: Date/Time Parsing Fails

**Symptom**: Error before column matching even runs

**Fix**: Check date format:

```python
print(df['年月日'].head())  # Or df['Date'].head()
print(df['時刻コード'].head())  # Or df['Slot'].head()
```

## Expected Fix Process

1. **Run diagnostics** (see commands above)
2. **Identify exact issue** (column names? encoding? format?)
3. **Update `import_jepx_csv.py`** with correct matching logic
4. **Test fix**:
   ```bash
   docker compose exec api python /etl/test_jepx_normalization.py
   ```
5. **If successful**, run full import:
   ```bash
   docker compose exec api python /etl/import_jepx_csv.py \
     --file /app/data/jepx/spot_2025.csv \
     --areas TOKYO,TOHOKU,HOKKAIDO
   ```
6. **Verify** expected ~3,504 records imported

## Success Criteria

After fix, you should see:

```
INFO - Loaded 10848 rows
INFO - Columns: ['年月日', '時刻コード', ...]
INFO - Normalizing JEPX data...
INFO - Normalized to 3504 records across 3 areas

Data preview:
                timestamp    area  area_price_jpy_kwh  system_price_jpy_kwh
0 2025-09-01 00:00:00+09:00  TOKYO            15.23              14.98
1 2025-09-01 00:00:00+09:00  TOHOKU           14.87              14.98
2 2025-09-01 00:00:00+09:00  HOKKAIDO         13.45              14.98
...

Date range: 2025-09-01 00:00:00+09:00 to 2025-11-11 23:30:00+09:00
Areas: ['HOKKAIDO', 'TOHOKU', 'TOKYO']

INFO - Storing 3504 price records to database...
INFO - ✓ Successfully stored 3504 records

✓ Import complete!
```

## Next Steps After Fix

1. **Import JEPX data** (3,504 records)
2. **Fetch solar radiation** from Open-Meteo
   ```bash
   make fetch-radiation
   ```
3. **Build ML features**
   ```bash
   docker compose exec api python /etl/build_features.py \
     --areas TOKYO,TOHOKU,HOKKAIDO \
     --start-date 2025-09-01 \
     --end-date 2025-11-11
   ```
4. **Verify frontend** shows real data

## Database Cleanup (If Needed)

If you have experimental/test data and want to start fresh:

```bash
# Clean all data
make db-clean

# Or manually
docker compose exec db psql -U postgres -d solar_explorer -c "
  TRUNCATE TABLE jepx_prices CASCADE;
  TRUNCATE TABLE radiation CASCADE;
  TRUNCATE TABLE features CASCADE;
"
```

## Contact & Support

If diagnostics don't reveal the issue:
1. Run all 3 diagnostic commands
2. Save the output
3. Share output to identify the specific column format used

The diagnostic scripts will show exactly what's in the CSV file!
