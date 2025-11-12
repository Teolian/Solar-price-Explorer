# Start Here - Local Testing

## Prerequisites

1. **Install Docker Desktop** (if not installed)
   - Download: https://www.docker.com/products/docker-desktop
   - macOS: Install and open Docker.app
   - Verify: `docker --version` and `docker-compose --version`

2. **Ensure Docker is running**
   ```bash
   # Check Docker status
   docker ps
   # Should NOT show "Cannot connect to the Docker daemon"
   ```

## Quick Start (5 minutes)

### Step 1: Create environment file
```bash
cp .env.example .env
```

The default values are already set for local development.

### Step 2: Start services
```bash
make start
```

Wait ~10 seconds for services to start. You should see:
```
Services ready!
API: http://localhost:8000
API Docs: http://localhost:8000/docs
Frontend: http://localhost:3000
```

### Step 3: Initialize database
```bash
make db-init
```

### Step 4: Generate test data
```bash
make test-data
```

This creates 30 days of synthetic data (~21,600 records).

### Step 5: Open in browser
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Common Issues

### "Cannot connect to the Docker daemon"
**Solution**: Start Docker Desktop application
```bash
# macOS
open -a Docker

# Wait for Docker to start, then retry
docker ps
```

### "Port already in use"
**Solution**: Stop the process using the port or change ports in `docker-compose.yml`
```bash
# Find process on port 3000
lsof -ti:3000 | xargs kill -9

# Find process on port 8000
lsof -ti:8000 | xargs kill -9
```

### "make: command not found"
**Solution**: Run commands directly
```bash
docker-compose up -d
docker-compose exec db psql -U postgres -d solar_explorer < db/migrations/001_initial_schema.sql
docker-compose exec api python /etl/generate_mock_data.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
docker-compose exec api python /etl/build_features.py --areas TOKYO,TOHOKU,HOKKAIDO --days 30
```

### Services not starting
**Solution**: Check logs
```bash
docker-compose logs api
docker-compose logs frontend
docker-compose logs db
```

## What to Test

### 1. Data Explorer (http://localhost:3000/data)
- Select area: TOKYO
- Select type: Prices
- Click "Load Data" → Should show table with prices
- Click "Export CSV" → Should download file

### 2. Correlations (http://localhost:3000/correlations)
- Select area: TOKYO
- Select period: 30d
- Click "Calculate Correlations" → Should show r_ghi, r_dni, r_dhi

### 3. Forecast (http://localhost:3000/forecast)
- Select area: TOKYO
- Select horizon: 24 hours
- Click "Generate Forecast" → Waits ~10-30s first time, then shows chart

### 4. API Endpoints (http://localhost:8000/docs)
- Try endpoints directly in Swagger UI
- Test /api/areas, /api/prices, /api/radiation, /api/corr

## Stop and Clean

```bash
# Stop services
make stop

# Remove all containers and data
make clean
```

## Next Steps

After successful testing:
1. Check all 4 frontend pages work
2. Test with different areas (TOKYO, TOHOKU, HOKKAIDO)
3. Try different forecast horizons (24h, 48h, 72h, 168h)
4. Export data to CSV
5. Ready for deployment!

## Need Help?

See detailed instructions:
- **QUICKSTART.md** - Quick start guide
- **TEST_INSTRUCTIONS.md** - Comprehensive testing
- **README.md** - Full documentation
