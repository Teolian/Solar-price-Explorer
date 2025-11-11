.PHONY: help setup start stop clean test lint logs test-data db-clean fetch-real-data fetch-jepx fetch-radiation

help:
	@echo "Solar×Price Explorer - Development Commands"
	@echo ""
	@echo "make setup          - Setup development environment"
	@echo "make start          - Start all services with Docker Compose"
	@echo "make stop           - Stop all services"
	@echo "make clean          - Clean all containers and volumes"
	@echo "make logs           - View logs from all services"
	@echo "make db-init        - Initialize database schema"
	@echo "make db-clean       - Clear all data from tables"
	@echo "make test-data      - Generate mock test data"
	@echo "make fetch-real-data - Fetch real JEPX and radiation data (last 7 days)"
	@echo "make fetch-jepx     - Fetch real JEPX price data only"
	@echo "make fetch-radiation - Fetch real solar radiation data only"
	@echo "make test           - Run all tests"
	@echo "make lint           - Run linters"

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

# Alternative data sources (recommended - no 403 errors!)

fetch-tepco-demand:
	@echo "Fetching TEPCO demand data (Tokyo area)..."
	@echo "Source: TEPCO official CSV downloads"
	@echo "Period: Sept 1 - Nov 11, 2025"
	docker-compose exec -T api python /etl/tepco_demand_ingest.py \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo "✓ TEPCO demand data fetched!"

fetch-japanesepower-prices:
	@echo "Fetching JEPX prices from JapanesePower.org..."
	@echo "Source: JapanesePower.org (JEPX Spot History CSV)"
	@echo "Period: Sept 1 - Nov 11, 2025"
	docker-compose exec -T api python /etl/japanesepower_ingest.py \
		--areas TOKYO,TOHOKU,HOKKAIDO \
		--start-date 2025-09-01 \
		--end-date 2025-11-11
	@echo "✓ JEPX prices fetched from JapanesePower.org!"

fetch-alternative-data:
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
