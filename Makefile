.PHONY: help setup start stop clean test lint

help:
	@echo "Solar×Price Explorer - Development Commands"
	@echo ""
	@echo "make setup    - Setup development environment"
	@echo "make start    - Start all services with Docker Compose"
	@echo "make stop     - Stop all services"
	@echo "make clean    - Clean all containers and volumes"
	@echo "make test     - Run all tests"
	@echo "make lint     - Run linters"
	@echo "make db-init  - Initialize database"
	@echo "make etl      - Run ETL pipeline"

setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Created .env file - please update with your credentials"
	cd apps/api && pip install -r requirements.txt
	cd apps/frontend && npm install
	@echo "Setup complete!"

start:
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Docs: http://localhost:8000/docs"

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
	./scripts/setup_db.sh

etl:
	@echo "Running ETL pipeline..."
	./scripts/run_etl.sh TOKYO,TOHOKU 7
