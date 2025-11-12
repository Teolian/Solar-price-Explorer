# Troubleshooting Playwright Downloads

## Recent Issues & Fixes

### Issue 1: TEPCO Downloaded Wrong Year (2022 instead of 2025)

**Problem**: TEPCO downloader had fallback logic that would download ANY CSV file if it couldn't find the specific year/month requested.

**Fix Applied**:
- Removed fallback to "any CSV/ZIP" link
- Now only downloads files matching specific year/month patterns
- Added date validation (won't try to download future dates)

**Result**: Will return error if data not found, instead of downloading wrong year

---

### Issue 2: JapanesePower.org Timeout (30s exceeded)

**Problem**: JapanesePower.org is very slow or has connectivity issues. 30-second timeout was too short.

**Fix Applied**:
- Increased timeout from 30s → 90s
- Added fallback: try `wait_until='load'` if `networkidle` times out
- Better error handling for screenshot timeouts

**Result**: More time for slow sites, better error messages

---

## Checking What Data Was Downloaded

### 1. Check Files Inside Docker Container

Since Playwright runs inside Docker, files are saved in the container's filesystem:

```bash
# If using docker-compose
docker-compose exec api ls -lh /app/data/jepx/
docker-compose exec api ls -lh /app/data/tepco/
docker-compose exec api ls -lh /app/data/japanesepower/

# If using docker compose (no dash)
docker compose exec api ls -lh /app/data/jepx/
docker compose exec api ls -lh /app/data/tepco/
docker compose exec api ls -lh /app/data/japanesepower/
```

### 2. Copy Files from Container to Host

To examine files on your local machine:

```bash
# Copy TEPCO files
docker-compose exec api ls /app/data/tepco/ | grep .csv | while read file; do
  docker cp solar-price-explorer-api-1:/app/data/tepco/$file ./data/tepco/
done

# Copy JEPX files
docker cp solar-price-explorer-api-1:/app/data/jepx/spot_2025.csv ./data/jepx/

# Copy JapanesePower.org files
docker-compose exec api ls /app/data/japanesepower/ | grep .csv | while read file; do
  docker cp solar-price-explorer-api-1:/app/data/japanesepower/$file ./data/japanesepower/
done
```

### 3. Check File Contents

Verify downloaded files are valid:

```bash
# Check TEPCO file
docker-compose exec api head -20 /app/data/tepco/juyo-2022.csv
# Expected: Should see Japanese headers with 時刻 (time) columns

# Check encoding
docker-compose exec api file /app/data/tepco/juyo-2022.csv
# Expected: Shift-JIS or UTF-8

# Check JEPX file (if downloaded)
docker-compose exec api head -20 /app/data/jepx/spot_2025.csv
# Expected: Should see 年月日, 時刻コード columns
```

---

## Understanding Data Availability

### Current Date Context
**Today is November 11, 2025**

### JEPX Data
- **2025 data**: May NOT be available yet
  - JEPX typically publishes yearly files after year ends
  - `spot_2025.csv` might not exist until December 31, 2025 or January 2026
- **2024 data**: Should be available
  - Try: `--year 2024` instead

### TEPCO Data
- **Publishing lag**: 1-2 days
- **Available dates**: Today is Nov 11, so data up to Nov 9 or Nov 10 should exist
- **September-November 2025**: Should be available (in the past)
- **Pattern**: `juyo-YYYYMMDD.csv` (daily files)

### JapanesePower.org
- **Status**: Community site, may be offline or slow
- **Fallback**: If site is down, use JEPX direct or wait for site recovery

---

## Testing Data Availability

We created a test script to check what's actually accessible:

```bash
# Run availability checker
docker-compose exec api python /etl/check_data_availability.py
```

This will test:
- ✅ JEPX: Which years are available (2025, 2024, 2023, 2022)
- ✅ TEPCO: Which recent dates are available
- ✅ JapanesePower.org: Site status and page accessibility

**Expected results**:
- Most sources will return **403 Forbidden** (WAF blocking)
- This confirms Playwright is required
- Some TEPCO dates might return **404 Not Found** (not published yet)

---

## Recommended Next Steps

### Option 1: Try 2024 Data Instead

Since 2025 data might not be available yet:

```bash
# Download JEPX 2024 data
make download-jepx-playwright YEAR=2024

# Or directly
docker-compose exec api python /etl/download_jepx_playwright.py \
  --year 2024 \
  --output /app/data/jepx/spot_2024.csv \
  --headless true
```

### Option 2: Test TEPCO with Recent Dates

Try downloading last week's data (definitely available):

```bash
# Download TEPCO data for October 2025 (past month)
docker-compose exec api python /etl/download_tepco_playwright.py \
  --year 2025 \
  --month 10 \
  --output /app/data/tepco \
  --headless false \
  --slow-mo 500
```

**Note**: `--headless false` lets you watch the browser and see what's happening

### Option 3: Skip JapanesePower.org for Now

If JapanesePower.org keeps timing out:

```bash
# Just download JEPX and TEPCO
make download-jepx-playwright
make download-tepco-playwright
# Skip: make download-japanesepower-playwright
```

---

## Common Errors & Solutions

### Error: "403 Forbidden"
**Cause**: Direct HTTP blocked by WAF
**Solution**: Use Playwright (already implemented)

### Error: "404 Not Found"
**Cause**: Data not published yet or wrong date
**Solution**:
- Check if date is in the future
- Try older dates (e.g., 2024 instead of 2025)
- TEPCO: Try yesterday's date, not today

### Error: "Timeout exceeded"
**Cause**: Site is slow or down
**Solution**:
- Increase `--slow-mo` (e.g., 500-1000)
- Try again later
- Check site manually in browser

### Error: "Could not find download button"
**Cause**: Website structure changed
**Solution**:
- Run with `--headless false` to see page
- Check debug screenshots in `data/` directories
- Update selectors in downloader script

### TEPCO Downloaded Wrong Year
**Cause**: Old version of script had fallback logic
**Solution**: ✅ **FIXED** - Pull latest changes and try again

---

## Verifying Fixes Work

### 1. Pull Latest Changes

```bash
git pull origin claude/work-in-progress-011CUzWiYCAmLUpNh7koyBsH
```

### 2. Rebuild Docker Image (if needed)

```bash
docker-compose build api
# or
docker compose build api
```

### 3. Try Downloads Again

```bash
# Clean start
docker-compose down
docker-compose up -d

# Try TEPCO October 2025 (past month, should work)
docker-compose exec api python /etl/download_tepco_playwright.py \
  --year 2025 \
  --month 10 \
  --output /app/data/tepco \
  --headless false

# Watch browser to see what happens
```

---

## Data Import After Download

Once you have valid CSV files:

### Import TEPCO Data

```bash
# Single file
docker-compose exec api python /etl/tepco_demand_ingest.py \
  --file /app/data/tepco/juyo-20251001.csv

# All files in directory
docker-compose exec api python /etl/tepco_demand_ingest.py \
  --directory /app/data/tepco
```

### Import JEPX Data

```bash
docker-compose exec api python /etl/import_jepx_csv.py \
  --file /app/data/jepx/spot_2024.csv \
  --areas TOKYO,TOHOKU,HOKKAIDO
```

### Import JapanesePower.org Data

```bash
docker-compose exec api python /etl/japanesepower_ingest.py \
  --directory /app/data/japanesepower
```

---

## Getting Help

### Enable Debug Mode

```bash
# Run with visible browser
--headless false

# Slow down actions
--slow-mo 1000

# Check debug screenshots
ls -la data/jepx/*.png
ls -la data/tepco/*.png
ls -la data/japanesepower/*.png
```

### Check Logs

```bash
# View full output
docker-compose logs api | grep -A 20 "Playwright"

# Follow logs in real-time
docker-compose logs -f api
```

### Test Data Availability

```bash
# Run availability checker
docker-compose exec api python /etl/check_data_availability.py
```

This shows which sources return:
- 200 OK → Direct HTTP works
- 403 Forbidden → Playwright required
- 404 Not Found → Data not published
- Timeout → Site down/slow

---

## Summary

✅ **Fixed**: TEPCO won't download wrong year anymore
✅ **Fixed**: JapanesePower.org has longer timeout (90s)
✅ **New**: check_data_availability.py to test what's accessible
⚠️ **Note**: 2025 data might not be available yet - try 2024

**Recommended command**:
```bash
# Test with 2024 data (definitely available)
docker-compose exec api python /etl/download_jepx_playwright.py \
  --year 2024 \
  --output /app/data/jepx/spot_2024.csv \
  --headless false
```

Watch the browser to see exactly what happens!
