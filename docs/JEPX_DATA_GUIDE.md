# JEPX Data Guide

## Problem: Automated Access Blocked

JEPX website blocks automated downloads with HTTP 403 "Access denied", even with correct POST requests and headers. This is due to:
- WAF/bot detection
- Commercial use policy (requires contract with JEPX)
- Recent changes to download mechanisms

## Solution 1: Manual Download (Recommended) ⭐

### Step 1: Download CSV from JEPX Website

1. Open browser and go to: https://www.jepx.jp/electricpower/market-data/spot/
2. Click **"Data Download"** button (データダウンロード)
3. In the modal window:
   - Select year (e.g., 2024, 2025)
   - Click download button
4. Save the CSV file (will be `spot_YYYY.csv` or `spot_summary_YYYY.csv`)

### Step 2: Place File in Project

```bash
mkdir -p data/jepx
mv ~/Downloads/spot_2024.csv data/jepx/
```

### Step 3: Import to Database

```bash
# Option A: Use import script directly
python apps/etl/import_jepx_csv.py \
  --file data/jepx/spot_2024.csv \
  --areas TOKYO,TOHOKU,HOKKAIDO

# Option B: Use Makefile command (will auto-detect local files)
make fetch-real-data
```

## Solution 2: Playwright Automation ⭐ Recommended for Automation

**We've implemented a complete Playwright-based solution!**

### Quick Start

```bash
# Option A: Full ETL pipeline (download + process + load to DB)
make jepx-etl-pipeline

# Option B: Just download the CSV
make download-jepx-playwright

# Option C: Use Python script directly
python apps/etl/download_jepx_playwright.py \
  --year 2024 \
  --output data/jepx/spot_2024.csv
```

### Setup Requirements

```bash
# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium

# Install system dependencies (Linux/Docker)
playwright install-deps
```

### How It Works

The Playwright downloader:
- ✅ Launches real Chromium browser (bypasses WAF)
- ✅ Simulates human behavior with realistic delays
- ✅ Hides automation flags (navigator.webdriver)
- ✅ Uses Japanese locale and timezone
- ✅ Automatically finds and clicks download buttons
- ✅ Saves file with proper encoding (CP932)

### Complete ETL Pipeline

The `jepx_etl_pipeline.py` provides end-to-end automation:

```bash
# Full pipeline: Download → Decode CP932 → Normalize → Load to DB
python apps/etl/jepx_etl_pipeline.py \
  --year 2024 \
  --areas TOKYO,TOHOKU,HOKKAIDO \
  --start-date 2024-09-01 \
  --end-date 2024-11-10
```

**Pipeline Steps**:
1. 📥 **Download** - Playwright automation downloads CSV
2. 🔤 **Decode** - CP932/Shift_JIS → UTF-8
3. 🔄 **Normalize** - Parse dates, time codes (時刻コード 1-48), area names
4. 📅 **Filter** - Date range and area filtering
5. 📊 **Partition** - Analyze data by date
6. 💾 **Load** - Upsert to PostgreSQL

**See full documentation**: [PLAYWRIGHT_SETUP.md](./PLAYWRIGHT_SETUP.md)

## Solution 3: Use Mock Data for Development

For development and testing, generate realistic mock data:

```bash
make generate-mock-data
```

This will:
- Generate realistic price patterns based on historical data
- Fetch real solar radiation data from Open-Meteo API
- Create proper correlations between prices and solar generation

## JEPX CSV Format Reference

### Encoding
- **Shift_JIS (CP932)** - must use correct encoding when reading

### Columns (Japanese)
- `年月日` - Date in YYYY/MM/DD format
- `時刻コード` - Time code (1-48 for 30-minute intervals)
- `システムプライス` - System price (JPY/kWh)
- `北海道`, `東北`, `東京`, etc. - Area prices for 9 regions

### Time Code Mapping (重要!)
JEPX uses 48 time codes for 30-minute intervals:

| Code | Time Period | Timestamp |
|------|-------------|-----------|
| 1    | 00:00-00:30 | 00:00     |
| 2    | 00:30-01:00 | 00:30     |
| 3    | 01:00-01:30 | 01:00     |
| ...  | ...         | ...       |
| 48   | 23:30-24:00 | 23:30     |

**Formula**:
```python
hour = (code - 1) // 2
minute = 30 if (code % 2 == 0) else 0
```

### Sample Data
```csv
年月日,時刻コード,システムプライス,北海道,東北,東京,中部,北陸,関西,中国,四国,九州
2024/11/01,1,8.5,9.2,8.7,8.5,8.3,8.4,8.1,8.0,7.9,7.8
2024/11/01,2,8.2,8.9,8.4,8.2,8.0,8.1,7.8,7.7,7.6,7.5
...
```

## Data Sources

### Official JEPX
- Website: https://www.jepx.jp/
- Spot Market: https://www.jepx.jp/electricpower/market-data/spot/
- **Commercial use requires contract with JEPX**

### Alternative Sources
- **jepx.info** - Charts and visualization (no bulk download)
- **Renewable Energy Institute** - Monthly aggregates
- **ICE (Intercontinental Exchange)** - Commercial API (paid)

## Legal Notice

**Important**:
- Personal/research use: OK
- Commercial use: Requires contract with JEPX
- See: https://www.jepx.jp/ terms and conditions (免責事項・著作権)

Our project currently uses data for:
- ✅ Development and testing
- ✅ Personal research
- ❌ Not for commercial redistribution (unless you have JEPX contract)

## Troubleshooting

### Q: Getting 403 Forbidden
**A**: This is expected. JEPX blocks automated access. Use manual download or Selenium.

### Q: CSV encoding errors
**A**: JEPX uses Shift_JIS (CP932). Use `encoding='cp932'` when reading.

### Q: Time codes not mapping correctly
**A**: See formula above. Code 1 = 00:00 (not 00:30!), Code 2 = 00:30, etc.

### Q: Missing data for 2025
**A**: Full year files are typically published after year ends. For current year:
- Download what's available manually
- Use previous year (2024) data as proxy
- Generate mock data for development

## Next Steps

1. ✅ Download spot_2024.csv manually from JEPX
2. ✅ Import using `import_jepx_csv.py`
3. ✅ Fetch solar radiation data: `make fetch-radiation`
4. ✅ Build features: `make build-features`
5. ✅ Check frontend: http://localhost:3000

---

**Updated**: 2025-11-10
**Status**: Manual download working, automated download blocked by JEPX
