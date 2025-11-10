#!/bin/bash
set -e

# Setup database schema
# Usage: ./scripts/setup_db.sh

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable not set"
    exit 1
fi

echo "Applying database migrations..."
psql "$DATABASE_URL" < db/migrations/001_initial_schema.sql

echo "Database setup complete!"
echo "Tables created: prices, radiation, features, models"
