#!/bin/bash
set -e

# Run ETL pipeline
# Usage: ./scripts/run_etl.sh [areas] [days]

AREAS=${1:-"TOKYO,TOHOKU"}
DAYS=${2:-7}

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable not set"
    exit 1
fi

echo "Running ETL for areas: $AREAS (last $DAYS days)"

echo "Step 1: Ingest JEPX prices..."
python apps/etl/jepx_ingest.py --areas "$AREAS" --days "$DAYS"

echo "Step 2: Ingest JMA radiation..."
python apps/etl/jma_ingest.py --areas "$AREAS" --days "$DAYS"

echo "Step 3: Build features..."
python apps/etl/build_features.py --areas "$AREAS" --days "$DAYS"

echo "ETL pipeline complete!"
