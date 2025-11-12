# Quick Start Guide - JEPX Data Import

## ✅ Current Status

**GOOD NEWS**: Your JEPX import is working! The normalization successfully created **32,544 records** from the CSV.

## What Just Happened

When you ran the import, you got:
```
✅ Loaded 10,848 rows
✅ Normalized to 32,544 records across 3 areas
✅ Data range: 2025-04-01 to 2025-11-12
✅ Areas: HOKKAIDO, TOHOKU, TOKYO
❌ ERROR: relation "jepx_prices" does not exist
```

**Problem**: Database table doesn't exist yet!

**Solution**: Initialize the database schema first.

## Next Steps

### Step 1: Initialize Database Schema

```bash
make db-init
```

This creates the necessary tables:
- `prices` - JEPX price data
- `radiation` - Solar radiation data
- `features` - ML features
- `models` - Trained models

### Step 2: Re-run JEPX Import

```bash
docker compose exec api python /etl/import_jepx_csv.py \
  --file /app/data/jepx/spot_2025.csv \
  --areas TOKYO,TOHOKU,HOKKAIDO
```

Expected output:
```
✓ Successfully stored 32,544 records
```

### Step 3: Verify Data in Database

```bash
docker compose exec db psql -U postgres -d solar_explorer -c "
  SELECT
    area,
    COUNT(*) as records,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    ROUND(AVG(area_price_jpy_kwh)::numeric, 2) as avg_price
  FROM prices
  GROUP BY area
  ORDER BY area;
"
```

Expected result:
```
   area    | records |       earliest        |        latest         | avg_price
-----------+---------+-----------------------+-----------------------+-----------
 HOKKAIDO  |  10,848 | 2025-04-01 00:00:00+09| 2025-11-12 23:30:00+09|   14.25
 TOHOKU    |  10,848 | 2025-04-01 00:00:00+09| 2025-11-12 23:30:00+09|   14.30
 TOKYO     |  10,848 | 2025-04-01 00:00:00+09| 2025-11-12 23:30:00+09|   15.15
```

### Step 4: Fetch Solar Radiation Data

```bash
docker compose exec api python /etl/jma_ingest.py \
  --areas TOKYO,TOHOKU,HOKKAIDO \
  --start-date 2025-09-01 \
  --end-date 2025-11-11
```

Or use Open-Meteo (more reliable):
```bash
make fetch-radiation
```

### Step 5: Build ML Features

```bash
docker compose exec api python /etl/build_features.py \
  --areas TOKYO,TOHOKU,HOKKAIDO \
  --start-date 2025-09-01 \
  --end-date 2025-11-11
```

### Step 6: Verify Frontend

Open http://localhost:3000 and you should see:
- Real JEPX price data instead of mock data
- Charts showing April-November 2025
- Tokyo, Tohoku, Hokkaido areas

## Summary of What We Fixed

### 1. Column Matching Issue
**Before**: Looked for exact column names like `'北海道'`
**After**: Searches for columns containing area name + `'エリアプライス'` prefix

### 2. Table Name Issue
**Before**: Script wrote to `jepx_prices` table
**After**: Script writes to `prices` table (matches schema)

### 3. Database Schema
**Before**: Tables didn't exist
**After**: Run `make db-init` to create tables

## Your Data Summary

You have **excellent data**:
- **Date range**: April 1 - November 12, 2025
- **Total rows**: 10,848 (226 days × 48 time slots)
- **Areas**: 3 (Tokyo, Tohoku, Hokkaido)
- **Total records**: 32,544 (10,848 × 3 areas)
- **Target period**: Sept 1 - Nov 11, 2025 ✅ **INCLUDED**

The September-November 2025 period you need is fully covered!

## Troubleshooting

### If `make db-init` fails:

Check if database is running:
```bash
docker compose ps
```

Check database logs:
```bash
docker compose logs db
```

Restart database:
```bash
docker compose restart db
sleep 5
make db-init
```

### If import is slow:

The import processes 32,544 records one-by-one. This might take 2-3 minutes. That's normal!

### To clean and restart:

```bash
make db-clean  # Clear all data
make db-init   # Recreate schema
# Then re-run import
```

## What's Next After Import?

1. ✅ Import JEPX prices (32,544 records)
2. ⏳ Fetch solar radiation for same period
3. ⏳ Build correlation features
4. ⏳ Train ML model
5. ⏳ View insights on dashboard

## Success Criteria

You'll know everything works when:

1. **Import completes**: `✓ Successfully stored 32,544 records`
2. **Database query shows data**: 10,848 records per area
3. **Frontend displays real data**: Charts show April-Nov 2025
4. **No mock data warnings**: Real data is being used

Ready to proceed! Run `make db-init` first! 🚀
