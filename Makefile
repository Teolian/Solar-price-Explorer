.PHONY: help setup start stop clean test lint logs test-data db-clean

help:
	@echo "Solar×Price Explorer - Development Commands"
	@echo ""
	@echo "make setup     - Setup development environment"
	@echo "make start     - Start all services with Docker Compose"
	@echo "make stop      - Stop all services"
	@echo "make clean     - Clean all containers and volumes"
	@echo "make logs      - View logs from all services"
	@echo "make db-init   - Initialize database schema"
	@echo "make db-clean  - Clear all data from tables"
	@echo "make test-data - Generate mock test data"
	@echo "make test      - Run all tests"
	@echo "make lint      - Run linters"

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
