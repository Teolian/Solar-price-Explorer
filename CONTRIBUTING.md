# Contributing to Solar×Price Explorer

## Development Setup

1. Clone repository
2. Install dependencies (Python 3.11+, Node.js 20+)
3. Setup environment variables (`.env`)
4. Initialize database with `scripts/setup_db.sh`
5. Run backend: `cd apps/api && uvicorn main:app --reload`
6. Run frontend: `cd apps/frontend && npm run dev`

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Run tests: `pytest`
- Format: `black .`

### TypeScript
- Use TypeScript strict mode
- Follow Next.js conventions
- Run linter: `npm run lint`
- Format: `prettier --write .`

## Project Structure

```
apps/
  api/         # FastAPI backend
    main.py    # API routes
    database.py # SQLAlchemy models
    ml_model.py # ML logic
  etl/         # Data ingestion
  frontend/    # Next.js app
    src/
      app/     # Pages
      components/ # React components
      lib/     # Utilities
```

## Adding Features

1. Backend: Update `apps/api/main.py` for new endpoints
2. Frontend: Create pages in `apps/frontend/src/app/`
3. Database: Add migrations in `db/migrations/`
4. ETL: Extend scripts in `apps/etl/`

## Testing

```bash
# Backend tests
cd apps/api
pytest

# Frontend tests
cd apps/frontend
npm test
```

## Pull Requests

1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Submit PR with description

## Questions

Open an issue for questions or suggestions.
