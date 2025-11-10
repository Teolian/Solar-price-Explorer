#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -U postgres; do
  sleep 1
done

echo "Database ready!"

echo "Applying migrations..."
psql $DATABASE_URL < /app/db/migrations/001_initial_schema.sql || echo "Migrations already applied"

echo "Starting API server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
