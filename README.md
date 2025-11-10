# Solar×Price Explorer

Price analysis and forecasting for JEPX electricity spot market using JMA solar radiation data.

## Architecture

- **Frontend**: Next.js (TypeScript), Tailwind CSS
- **Backend**: FastAPI (Python), PostgreSQL
- **ETL**: Scheduled ingestion via GitHub Actions
- **ML**: XGBoost baseline model for price forecasting

## Data Sources

- **JEPX**: Day-ahead spot market prices and volumes (9 power areas)
- **JMA**: Solar radiation measurements (GHI, DNI, DHI) from observation stations

## Project Structure

```
apps/
  frontend/    # Next.js application
  api/         # FastAPI backend
  etl/         # Data ingestion scripts
db/
  migrations/  # Database schema
.github/
  workflows/   # CI/CD and scheduled ETL
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL database

### Environment Variables

Create `.env` file:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
API_TOKEN=your-secret-token
TZ=Asia/Tokyo
NEXT_PUBLIC_API_BASE=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000
```

### Database

```bash
psql $DATABASE_URL < db/migrations/001_initial_schema.sql
```

### Backend

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

## ETL

Manual execution:

```bash
export DATABASE_URL=postgresql://...
python apps/etl/jepx_ingest.py --areas TOKYO,TOHOKU --days 7
python apps/etl/jma_ingest.py --areas TOKYO,TOHOKU --days 7
python apps/etl/build_features.py --areas TOKYO,TOHOKU --days 7
```

Automated via GitHub Actions (schedule: 05:00, 17:00 UTC).

## Deployment

### Free Tier Stack

- **Frontend**: Vercel
- **Backend**: Railway or Render
- **Database**: Neon (serverless PostgreSQL)
- **ETL**: GitHub Actions

See `deployment_guide_solar_price_explorer_free_tier.md` for details.

## API Endpoints

- `GET /api/areas` - List power areas
- `GET /api/prices` - Hourly price data
- `GET /api/radiation` - Solar radiation data
- `GET /api/corr` - Price-radiation correlations
- `POST /api/train` - Train forecasting model
- `POST /api/forecast` - Generate price forecast
- `GET /api/export` - Export dataset

## Features

- Hourly price and radiation time series
- Correlation analysis (GHI/DNI/DHI ↔ price)
- ML-based price forecasting (24-168h horizon)
- Area comparison
- Data export (CSV, Parquet)

## Timezone

All timestamps in JST (Asia/Tokyo, UTC+9).

## License

MIT
