# Local Testing Instructions

## Quick Start

1. **Start services**
```bash
make start
```

Wait ~10 seconds for all services to start.

2. **Initialize database**
```bash
make db-init
```

3. **Generate test data**
```bash
make test-data
```

This creates 30 days of synthetic data for TOKYO, TOHOKU, and HOKKAIDO.

4. **Open browser**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Testing Checklist

### 1. API Health Check
```bash
curl http://localhost:8000/healthz
```

Expected: `{"status":"ok","timezone":"Asia/Tokyo"}`

### 2. Check Data in Database
```bash
# Count price records
docker-compose exec db psql -U postgres -d solar_explorer -c \
  "SELECT area, COUNT(*) as count FROM prices GROUP BY area;"

# Count radiation records
docker-compose exec db psql -U postgres -d solar_explorer -c \
  "SELECT area, COUNT(*) as count FROM radiation GROUP BY area;"

# Count features
docker-compose exec db psql -U postgres -d solar_explorer -c \
  "SELECT area, COUNT(*) as count FROM features GROUP BY area;"
```

Expected: Each area should have ~720 records (30 days × 24 hours).

### 3. Test API Endpoints

**Get areas:**
```bash
curl http://localhost:8000/api/areas
```

**Get prices:**
```bash
curl "http://localhost:8000/api/prices?area=TOKYO" | jq '.data | length'
```

**Get radiation:**
```bash
curl "http://localhost:8000/api/radiation?area=TOKYO" | jq '.data | length'
```

**Get correlations:**
```bash
curl "http://localhost:8000/api/corr?area=TOKYO&period=30d" | jq
```

Expected: Correlation coefficients (r_ghi, r_dni, r_dhi) and sample size (n).

### 4. Test Model Training

```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "Content-Type: application/json" \
  -d '{
    "area": "TOKYO",
    "target": "area_price",
    "features": ["ghi", "dni", "dhi", "hour", "dow", "month", "price_lag_1h", "price_lag_24h", "ghi_lag_1h", "ghi_roll3h", "volume_kwh", "is_weekend"],
    "val_window": "7d"
  }' | jq
```

Expected: Model ID, MAE, and trained_at timestamp.

### 5. Test Forecasting

```bash
curl -X POST "http://localhost:8000/api/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "area": "TOKYO",
    "horizon_hours": 24
  }' | jq '.points | length'
```

Expected: 24 forecast points.

### 6. Test Frontend

#### Data Explorer
1. Go to http://localhost:3000/data
2. Select area: TOKYO
3. Select type: Prices
4. Click "Load Data"
5. Verify table shows hourly prices
6. Click "Export CSV" (downloads file)

#### Correlations
1. Go to http://localhost:3000/correlations
2. Select area: TOKYO
3. Select period: 30d
4. Click "Calculate Correlations"
5. Verify correlation coefficients display
6. Values should be between -1 and 1

#### Forecast
1. Go to http://localhost:3000/forecast
2. Select area: TOKYO
3. Select horizon: 24 hours
4. Click "Generate Forecast"
5. Wait for model training (first time ~10-30 seconds)
6. Verify chart displays
7. Verify forecast table shows 24 hours

### 7. Test with Different Areas

Repeat tests for TOHOKU and HOKKAIDO:
```bash
curl "http://localhost:8000/api/corr?area=TOHOKU&period=30d" | jq
curl "http://localhost:8000/api/corr?area=HOKKAIDO&period=30d" | jq
```

### 8. Check Logs

If anything fails, check logs:
```bash
make logs
```

Or specific service:
```bash
docker-compose logs api
docker-compose logs frontend
docker-compose logs db
```

## Expected Results

### Mock Data Characteristics

**Prices:**
- Range: 5-20 JPY/kWh
- Higher during peak hours (morning/evening)
- Lower at night and weekends
- Tokyo has highest prices, Hokkaido lowest

**Radiation:**
- Zero at night (22:00-05:00)
- Peak around noon
- GHI: 0-1000 W/m²
- DNI: 0-900 W/m²
- DHI: derived from GHI-DNI

**Correlations:**
- Expected r_ghi: negative to slightly positive (-0.3 to 0.3)
- Mock data has realistic but random patterns
- Correlations may vary due to synthetic generation

**Forecasts:**
- MAE: typically 1-3 JPY/kWh on mock data
- Predictions follow daily patterns
- Should not have extreme outliers

## Troubleshooting

### "Connection refused" errors
Services still starting. Wait 10-20 seconds and retry.

### "No data available" in frontend
1. Verify `make test-data` completed successfully
2. Check database has data: see step 2 above
3. Check API logs for errors

### Model training fails
1. Ensure sufficient data (need at least 7 days)
2. Check features are available in database
3. Look for errors in API logs

### Frontend shows empty charts
1. Check browser console for errors
2. Verify CORS is allowing localhost:3000
3. Check API is responding: `curl http://localhost:8000/healthz`

### Database connection errors
1. Ensure database is healthy: `docker-compose ps`
2. Wait for health check to pass
3. Restart if needed: `make stop && make start`

## Performance Notes

- First model training: 10-30 seconds
- Subsequent forecasts: 1-3 seconds
- Data generation: 5-10 seconds
- Chart rendering: 1-2 seconds

## Clean Up

Stop services:
```bash
make stop
```

Remove all data:
```bash
make clean
```

## Next Steps

After successful testing:
1. Review code and logs for any issues
2. Adjust mock data parameters if needed
3. Test with longer periods (60-90 days)
4. Try different feature combinations
5. Prepare for production deployment
