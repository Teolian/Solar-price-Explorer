#!/bin/bash
set -e

# Generate mock test data
# Usage: ./scripts/generate_test_data.sh [areas] [days]

AREAS=${1:-"TOKYO,TOHOKU,HOKKAIDO"}
DAYS=${2:-30}

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable not set"
    exit 1
fi

echo "Generating mock test data..."
echo "Areas: $AREAS"
echo "Days: $DAYS"

python apps/etl/generate_mock_data.py --areas "$AREAS" --days "$DAYS"

echo ""
echo "Building features from generated data..."
python apps/etl/build_features.py --areas "$AREAS" --days "$DAYS"

echo ""
echo "Test data generation complete!"
echo "You can now test the application with this data."
