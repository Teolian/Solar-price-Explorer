# Playwright Automation Setup

## Overview

Playwright provides automated browser control to download JEPX data, bypassing WAF/bot detection by simulating real user behavior.

## Installation

### Option 1: Inside Docker Container (Recommended)

```bash
# Enter the container
docker-compose exec api bash

# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium

# Install browser dependencies (Linux)
playwright install-deps
```

### Option 2: Local Installation

```bash
# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium

# On Linux, install dependencies
playwright install-deps
```

## Usage

### 1. Automated Download with Playwright

```bash
# Using Makefile (easiest)
make download-jepx-playwright

# Or directly
python apps/etl/download_jepx_playwright.py \
  --year 2024 \
  --output data/jepx/spot_2024.csv \
  --headless true
```

### 2. Full ETL Pipeline (Download → Process → Load to DB)

```bash
# Complete pipeline
make jepx-etl-pipeline

# Or with custom parameters
python apps/etl/jepx_etl_pipeline.py \
  --year 2024 \
  --areas TOKYO,TOHOKU,HOKKAIDO \
  --start-date 2024-09-01 \
  --end-date 2024-11-10
```

## Parameters

### download_jepx_playwright.py

- `--year` - Year to download (e.g., 2024, 2025)
- `--output` - Output path for CSV file
- `--type` - Data type: "spot" (48 slots) or "summary" (aggregated)
- `--headless` - Run browser in headless mode (default: true)
- `--slow-mo` - Slow down by N milliseconds (default: 100)

### jepx_etl_pipeline.py

- `--year` - Year to download
- `--file` - Use existing file (with --skip-download)
- `--skip-download` - Skip download, use existing file
- `--areas` - Filter areas (e.g., TOKYO,TOHOKU,HOKKAIDO)
- `--start-date` - Filter from date (YYYY-MM-DD)
- `--end-date` - Filter to date (YYYY-MM-DD)
- `--no-playwright` - Disable Playwright, print manual instructions

## Examples

### Download 2024 data with visible browser

```bash
python apps/etl/download_jepx_playwright.py \
  --year 2024 \
  --output data/jepx/spot_2024.csv \
  --headless false
```

### Process existing file without download

```bash
python apps/etl/jepx_etl_pipeline.py \
  --file data/jepx/spot_2024.csv \
  --skip-download \
  --areas TOKYO,TOHOKU,HOKKAIDO
```

### Full pipeline for specific date range

```bash
python apps/etl/jepx_etl_pipeline.py \
  --year 2024 \
  --start-date 2024-09-01 \
  --end-date 2024-11-10 \
  --areas TOKYO,TOHOKU,HOKKAIDO
```

## How It Works

### Playwright Download Process

1. **Launch Browser** - Chromium in headless mode
2. **Navigate to JEPX** - https://www.jepx.jp/electricpower/market-data/spot/
3. **Click "Data Download"** - Find and click download button
4. **Select Year** - Choose year from dropdown/selector
5. **Submit Form** - Click final download button
6. **Save File** - Wait for download and save to output path

### Anti-Detection Features

- Realistic browser fingerprint (resolution, user-agent, locale)
- Hide automation flags (`navigator.webdriver`)
- Human-like delays (slow_mo parameter)
- Proper timezone (Asia/Tokyo) and locale (ja-JP)
- No sandbox mode for Docker compatibility

### ETL Pipeline Steps

1. **Download** - Playwright automation (or use existing file)
2. **Decode** - CP932/Shift_JIS → UTF-8
3. **Normalize** - Parse dates, time codes, area names
4. **Filter** - Date range and area filtering
5. **Partition** - Analyze data by date
6. **Load** - Upsert to PostgreSQL

## Troubleshooting

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "Browser failed to launch"

In Docker, you may need system dependencies:

```bash
# Add to Dockerfile
RUN playwright install-deps chromium

# Or manually in container
apt-get update && apt-get install -y \
  libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
  libatk1.0-0 libatk-bridge2.0-0 libcups2 \
  libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxfixes3 libxrandr2 \
  libgbm1 libpango-1.0-0 libcairo2 libasound2
```

### Selectors not found

JEPX may change their website structure. Debug with:

```bash
# Run with visible browser
python apps/etl/download_jepx_playwright.py \
  --year 2024 \
  --output data/jepx/spot_2024.csv \
  --headless false

# Check debug screenshots
ls data/jepx/*.png
```

### Still getting 403 errors

Even Playwright may be blocked. In this case:

1. Try from Japanese IP (VPN or JP server)
2. Increase `--slow-mo` delay (e.g., 500ms)
3. Run during off-peak hours
4. Fall back to manual download

## Docker Integration

### Update Dockerfile

Add Playwright to your Docker image:

```dockerfile
# Install Playwright
RUN pip install playwright==1.40.0

# Install Chromium and dependencies
RUN playwright install chromium && \
    playwright install-deps chromium
```

### Volume Mounting

Ensure data directory is mounted:

```yaml
# docker-compose.yml
services:
  api:
    volumes:
      - ./data:/app/data
      - ./apps/etl:/etl
```

## Performance

- **Headless mode**: ~30 seconds per download
- **Visible mode**: ~40 seconds per download
- **File size**: ~50-100MB per year (spot data)
- **Processing**: ~5-10 minutes for full year (17,520 rows × 9 areas)

## Security & Legal

⚠️ **Important Notes**:

1. **Bot Detection**: Playwright bypasses technical blocks but doesn't change legal status
2. **Terms of Service**: JEPX may prohibit automated access in ToS
3. **Commercial Use**: Still requires JEPX contract for commercial purposes
4. **Rate Limiting**: Add delays, don't hammer the server
5. **Personal Use**: Generally acceptable for research/development

**Recommendation**: Use for development/testing. For production, consider:
- Official JEPX API (for participants)
- Manual periodic downloads
- Contact JEPX for proper access

---

**Updated**: 2025-11-10
**Status**: Tested with JEPX spot market page structure as of 2025
