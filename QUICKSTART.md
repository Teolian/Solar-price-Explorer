# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- 8GB+ RAM recommended
- Ports 3000, 5432, 8000 available

## Setup and Run

1. **Clone repository**
```bash
git clone <repo-url>
cd Solar-price-Explorer
```

2. **Start services**
```bash
make start
```

This will start:
- PostgreSQL database (port 5432)
- FastAPI backend (port 8000)
- Next.js frontend (port 3000)

3. **Initialize database**
```bash
make db-init
```

4. **Generate test data**
```bash
make test-data
```

This generates 30 days of mock data for TOKYO, TOHOKU, and HOKKAIDO areas.

5. **Open application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/healthz

## Test the Application

### 1. Overview Page
Visit http://localhost:3000 to see the landing page.

### 2. Data Explorer
- Navigate to "Data Explorer"
- Select area (e.g., TOKYO)
- Select data type (Prices or Radiation)
- Click "Load Data"
- You should see hourly data in a table

### 3. Correlations
- Navigate to "Correlations"
- Select area and period
- Click "Calculate Correlations"
- View correlation coefficients between radiation and prices

### 4. Forecast
- Navigate to "Forecast"
- Select area
- Click "Generate Forecast" (this will train a model first if none exists)
- View predicted prices for next 24-168 hours

## Verify Data

Check database contents:
```bash
docker-compose exec db psql -U postgres -d solar_explorer -c "SELECT area, COUNT(*) FROM prices GROUP BY area;"
docker-compose exec db psql -U postgres -d solar_explorer -c "SELECT area, COUNT(*) FROM radiation GROUP BY area;"
docker-compose exec db psql -U postgres -d solar_explorer -c "SELECT area, COUNT(*) FROM features GROUP BY area;"
```

## View Logs

```bash
make logs
```

Or specific service:
```bash
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f db
```

## Train a Model

Via API:
```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "Content-Type: application/json" \
  -d '{
    "area": "TOKYO",
    "target": "area_price",
    "features": ["ghi", "dni", "dhi", "hour", "dow", "month", "price_lag_1h", "price_lag_24h"],
    "val_window": "7d"
  }'
```

## Generate Forecast

Via API:
```bash
curl -X POST "http://localhost:8000/api/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "area": "TOKYO",
    "horizon_hours": 24
  }'
```

## Stop Services

```bash
make stop
```

## Clean Everything

```bash
make clean
```

This removes all containers, volumes, and data. Use with caution!

## Troubleshooting

### Port already in use
Stop services using those ports or change ports in `docker-compose.yml`.

### Database connection error
Wait a few seconds for database to initialize, then retry.

### Frontend can't connect to API
Check that CORS is configured correctly in `apps/api/main.py`. Should allow `http://localhost:3000`.

### No data in charts
Ensure you ran `make test-data` after `make db-init`.

## Next Steps

- Add more areas to test data
- Experiment with different forecast horizons
- Try exporting data as CSV
- Check API documentation at http://localhost:8000/docs
