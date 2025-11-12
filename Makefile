.PHONY: help setup start stop restart clean test lint logs test-data db-clean fetch-real-data fetch-jepx fetch-radiation

help:
	@echo "Solar×Price Explorer - Development Commands"
	@echo ""
	@echo "=== Setup & Services ==="
	@echo "make setup          - Setup development environment"
	@echo "make start          - Start all services with Docker Compose"
	@echo "make stop           - Stop all services"
	@echo "make restart        - Restart services with latest code (USE THIS AFTER GIT PULL!)"
	@echo "make clean          - Clean all containers and volumes"
	@echo "make logs           - View logs from all services"
	@echo ""
	@echo "=== Database ==="
	@echo "make db-init        - Initialize database schema"
	@echo "make db-clean       - Clear all data from tables"
	@echo ""
	@echo "=== Data Collection (RECOMMENDED) ==="
	@echo "make download-all-playwright     - Download ALL data with Playwright (bypasses 403)"
	@echo "make download-jepx-playwright    - Download JEPX data only"
	@echo "make download-tepco-playwright   - Download TEPCO demand data"
	@echo "make download-japanesepower-playwright - Download JapanesePower.org JEPX data"
	@echo "make download-and-process-all    - Complete pipeline: download + process + features"
	@echo ""
	@echo "=== Data Processing ==="
	@echo "make test-data      - Generate mock test data"
	@echo "make import-jepx-csv - Import manually downloaded JEPX CSV"
	@echo "make fetch-radiation - Fetch solar radiation from Open-Meteo"
	@echo ""
	@echo "=== Testing & Debugging ==="
	@echo "make test           - Run all tests"
	@echo "make lint           - Run linters"
	@echo "make test-download-single-day    - Quick test: download single day data"
	@echo "make analyze-jepx-csv            - Analyze JEPX CSV structure and availability"
	@echo "make debug-jepx-structure        - Debug JEPX column matching issues"
	@echo "make test-jepx-normalization     - Test normalization logic with debug output"
	@echo ""
	@echo "NOTE: Direct HTTP fetching (fetch-real-data) returns 403 errors."
	@echo "      Use Playwright automation instead!"

setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Created .env file - please update with your credentials"
	cd apps/api && pip install -r requirements.txt
	cd apps/frontend && npm install
	@echo "Setup complete!"

start:
	docker-compose up -d
	@echo "Services starting..."
	@echo "Waiting for database..."
	@sleep 5
	@echo ""
	@echo "Services ready!"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@echo "Initialize database with: make db-init"
	@echo "Generate test data with: make test-data"

logs:
	docker-compose logs -f

test-data:
	@echo "Generating test data..."
	docker-compose exec -T api python /etl/generate_mock_data.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
	docker-compose exec -T api python /etl/build_features.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
	@echo "Test data generated!"

stop:
	docker-compose down

restart:
	@echo "Restarting services with latest code..."
	docker-compose down
	docker-compose up -d --build
	@echo ""
	@echo "✓ Services restarted!"
	@echo "  API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Frontend: http://localhost:3000"
	@echo ""
	@echo "Check new endpoints at /docs"

clean:
	docker-compose down -v
	rm -rf apps/frontend/node_modules
	rm -rf apps/frontend/.next
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	cd apps/api && pytest
	cd apps/frontend && npm test

lint:
	cd apps/api && flake8 .
	cd apps/frontend && npm run lint

db-init:
	@echo "Initializing database..."
	docker-compose exec -T db psql -U postgres -d solar_explorer < db/migrations/001_initial_schema.sql
	@echo "Database initialized!"

db-clean:
	@echo "Clearing all data from tables..."
	@docker-compose exec -T db psql -U postgres -d solar_explorer -c "TRUNCATE TABLE prices, radiation, features, models CASCADE;"
	@echo "All data cleared!"

etl:
	@echo "Running ETL pipeline..."
	./scripts/run_etl.sh TOKYO,TOHOKU 7

fetch-jepx:
	@echo "Fetching real JEPX price data..."
	docker-compose exec -T api python /etl/jepx_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --days 7
	@echo "JEPX data fetched!"

fetch-radiation:
	@echo "Fetching real solar radiation data..."
	docker-compose exec -T api python /etl/jma_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --days 7
	@echo "Radiation data fetched!"

download-jepx-playwright:
	@echo "Downloading JEPX data using Playwright automation..."
	@echo "This will open a browser and download the CSV file"
	@echo "Target: Sept-Nov 2025 (until 11.11.2025)"
	docker-compose exec -T api python /etl/download_jepx_playwright.py \
		--year 2025 \
		--output /app/data/jepx/spot_2025.csv \
		--headless true
	@echo "✓ Download complete!"

download-tepco-playwright:
	@echo "Downloading TEPCO demand data using Playwright automation..."
	@echo "This will download CSV files for September-November 2025"
	@echo "Source: TEPCO official demand forecast data"
	docker-compose exec -T api python /etl/download_tepco_playwright.py \
		--year 2025 \
		--month 9 \
		--output /app/data/tepco \
		--headless true
	docker-compose exec -T api python /etl/download_tepco_playwright.py \
		--year 2025 \
		--month 10 \
		--output /app/data/tepco \
		--headless true
	docker-compose exec -T api python /etl/download_tepco_playwright.py \
		--year 2025 \
		--month 11 \
		--output /app/data/tepco \
		--headless true
	@echo "✓ TEPCO downloads complete!"

download-japanesepower-playwright:
	@echo "Downloading JEPX prices from JapanesePower.org using Playwright..."
	@echo "This will download CSV files for all areas"
	@echo "Source: JapanesePower.org community JEPX data"
	docker-compose exec -T api python /etl/download_japanesepower_playwright.py \
		--area TOKYO \
		--output /app/data/japanesepower \
		--headless true
	docker-compose exec -T api python /etl/download_japanesepower_playwright.py \
		--area TOHOKU \
		--output /app/data/japanesepower \
		--headless true
	docker-compose exec -T api python /etl/download_japanesepower_playwright.py \
		--area HOKKAIDO \
		--output /app/data/japanesepower \
		--headless true
	@echo "✓ JapanesePower.org downloads complete!"

download-all-playwright:
	@echo "========================================"
	@echo "Playwright Download Suite"
	@echo "========================================"
	@echo "Downloading data from all sources using browser automation"
	@echo "This bypasses 403 errors by simulating real browser behavior"
	@echo ""
	@echo "Sources:"
	@echo "  1. JEPX (jepx.jp) - Spot market prices"
	@echo "  2. TEPCO (tepco.co.jp) - Tokyo demand data"
	@echo "  3. JapanesePower.org - JEPX historical archives"
	@echo ""
	@echo "Period: September-November 2025"
	@echo "========================================"
	@echo ""
	make download-jepx-playwright
	@echo ""
	make download-tepco-playwright
	@echo ""
	make download-japanesepower-playwright
	@echo ""
	@echo "========================================"
	@echo "✓ All Playwright downloads complete!"
	@echo "========================================"
	@echo ""
	@echo "Downloaded files are in:"
	@echo "  - data/jepx/"
	@echo "  - data/tepco/"
	@echo "  - data/japanesepower/"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Import JEPX: make import-jepx-csv"
	@echo "  2. Process all data and build features"
	@echo "========================================"

import-jepx-csv:
	@echo "Importing manually downloaded JEPX CSV files..."
	@echo "Place CSV files in data/jepx/ directory first!"
	@echo "See docs/JEPX_DATA_GUIDE.md for instructions"
	@if [ -f data/jepx/spot_2025.csv ]; then \
		docker-compose exec -T api python /etl/import_jepx_csv.py --file /app/data/jepx/spot_2025.csv --areas TOKYO,TOHOKU,HOKKAIDO; \
	elif [ -f data/jepx/spot_2024.csv ]; then \
		docker-compose exec -T api python /etl/import_jepx_csv.py --file /app/data/jepx/spot_2024.csv --areas TOKYO,TOHOKU,HOKKAIDO; \
	else \
		echo "ERROR: No CSV files found in data/jepx/"; \
		echo "Download from https://www.jepx.jp/electricpower/market-data/spot/"; \
		exit 1; \
	fi
	@echo "Import complete!"

jepx-etl-pipeline:
	@echo "Running complete JEPX ETL pipeline..."
	@echo "This will: download → decode CP932 → normalize → load to DB"
	@echo "Period: Sept 1 - Nov 11, 2025"
	docker-compose exec -T api python /etl/jepx_etl_pipeline.py \
		--year 2025 \
		--areas TOKYO,TOHOKU,HOKKAIDO \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo "✓ Pipeline complete!"

fetch-real-data:
	@echo "Fetching real data from JEPX and Open-Meteo..."
	@echo "Period: Sept 1 - Nov 11, 2025"
	@echo "Note: JEPX automated download may fail (403). Use 'make import-jepx-csv' for manual import."
	docker-compose exec -T api python /etl/jepx_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --start-date 2025-09-01 --end-date 2025-11-11
	docker-compose exec -T api python /etl/jma_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --start-date 2025-09-01 --end-date 2025-11-11
	docker-compose exec -T api python /etl/build_features.py --areas TOKYO,TOHOKU,HOKKAIDO --start-date 2025-09-01 --end-date 2025-11-11
	@echo "Real data fetched and features built!"

fetch-recent-data:
	@echo "Fetching recent data (last 30 days)..."
	docker-compose exec -T api python /etl/jepx_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
	docker-compose exec -T api python /etl/jma_ingest.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
	docker-compose exec -T api python /etl/build_features.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
	@echo "Recent data fetched!"

# Alternative data sources with Playwright automation

fetch-tepco-demand:
	@echo "⚠️  WARNING: Direct HTTP fetch may return 403 Forbidden"
	@echo "Consider using: make download-tepco-playwright"
	@echo ""
	@echo "Fetching TEPCO demand data (Tokyo area)..."
	@echo "Source: TEPCO official CSV downloads"
	@echo "Period: Sept 1 - Nov 11, 2025"
	docker-compose exec -T api python /etl/tepco_demand_ingest.py \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo "✓ TEPCO demand data fetched!"

fetch-japanesepower-prices:
	@echo "⚠️  WARNING: Direct HTTP fetch may return 403 Forbidden"
	@echo "Consider using: make download-japanesepower-playwright"
	@echo ""
	@echo "Fetching JEPX prices from JapanesePower.org..."
	@echo "Source: JapanesePower.org (JEPX Spot History CSV)"
	@echo "Period: Sept 1 - Nov 11, 2025"
	docker-compose exec -T api python /etl/japanesepower_ingest.py \
		--areas TOKYO,TOHOKU,HOKKAIDO \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo "✓ JEPX prices fetched from JapanesePower.org!"

fetch-alternative-data:
	@echo "⚠️  DEPRECATED: Direct HTTP fetching returns 403 errors"
	@echo "Use Playwright automation instead: make download-all-playwright"
	@echo ""
	@echo "Fetching data from alternative sources..."
	@echo "Using: TEPCO (demand) + JapanesePower.org (JEPX prices) + Open-Meteo (radiation)"
	@echo "Period: Sept 1 - Nov 11, 2025"
	@echo ""
	make fetch-tepco-demand
	make fetch-japanesepower-prices
	make fetch-radiation
	@echo ""
	@echo "✓ All alternative data sources fetched!"
	@echo "Building features..."
	docker-compose exec -T api python /etl/build_features.py \
		--areas TOKYO,TOHOKU,HOKKAIDO \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo "✓ Complete pipeline finished!"

# RECOMMENDED: Complete Playwright pipeline
download-and-process-all:
	@echo "========================================"
	@echo "Complete Data Pipeline with Playwright"
	@echo "========================================"
	@echo "This is the RECOMMENDED approach for collecting Japanese energy data"
	@echo ""
	@echo "Steps:"
	@echo "  1. Download JEPX, TEPCO, JapanesePower.org data (Playwright)"
	@echo "  2. Fetch Open-Meteo solar radiation (API)"
	@echo "  3. Import all downloaded files to database"
	@echo "  4. Build ML features"
	@echo ""
	@echo "Period: September 1 - November 11, 2025"
	@echo "========================================"
	@echo ""
	@echo "Step 1: Downloading with Playwright..."
	make download-all-playwright
	@echo ""
	@echo "Step 2: Fetching solar radiation..."
	make fetch-radiation
	@echo ""
	@echo "Step 3: Importing data to database..."
	@echo "TODO: Add import commands here"
	@echo ""
	@echo "Step 4: Building features..."
	docker-compose exec -T api python /etl/build_features.py \
		--areas TOKYO,TOHOKU,HOKKAIDO \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo ""
	@echo "========================================"
	@echo "✓ Complete pipeline finished!"
	@echo "========================================"

# Quick test - download data for single day
test-download-single-day:
	@echo "========================================"
	@echo "TEST: Single Day Download"
	@echo "========================================"
	@echo "Quick test to verify downloaders work"
	@echo "Downloads data for 1 day (2 days ago)"
	@echo ""
	docker-compose exec -T api python /etl/test_download_single_day.py --area TOKYO
	@echo ""
	@echo "Check results above - at least TEPCO and Open-Meteo should succeed"
	@echo "========================================"

# Debug JEPX import issues
debug-jepx-structure:
	@echo "========================================"
	@echo "DEBUG: JEPX CSV Structure Analysis"
	@echo "========================================"
	@echo "Analyzing column names and data format"
	@echo ""
	docker-compose exec -T api python /etl/debug_jepx_import.py
	@echo ""
	@echo "This shows actual CSV structure and column matching test"
	@echo "========================================"

test-jepx-normalization:
	@echo "========================================"
	@echo "TEST: JEPX Normalization Logic"
	@echo "========================================"
	@echo "Testing data normalization with detailed debug output"
	@echo ""
	docker-compose exec -T api python /etl/test_jepx_normalization.py
	@echo ""
	@echo "This shows why normalization succeeds or fails"
	@echo "========================================"

analyze-jepx-csv:
	@echo "========================================"
	@echo "ANALYZE: JEPX CSV Data Availability"
	@echo "========================================"
	@echo "Checking what data is available in downloaded CSV"
	@echo ""
	docker-compose exec -T api python /etl/analyze_jepx_csv.py /app/data/jepx/spot_2025.csv
	@echo ""
	@echo "========================================"
