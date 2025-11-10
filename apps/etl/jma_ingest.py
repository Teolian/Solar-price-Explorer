#!/usr/bin/env python3
"""
JMA Radiation Data Ingestion Script
Downloads and processes JMA solar radiation data
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import pytz
import pandas as pd
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JST = pytz.timezone('Asia/Tokyo')

# Using Open-Meteo Satellite Radiation API for Japan (Himawari satellite)
OPEN_METEO_BASE = "https://archive-api.open-meteo.com/v1/archive"

# Representative coordinates for each JEPX area
AREA_COORDINATES = {
    "HOKKAIDO": {"lat": 43.06, "lon": 141.35, "name": "Sapporo"},      # Sapporo
    "TOHOKU": {"lat": 38.27, "lon": 140.87, "name": "Sendai"},         # Sendai
    "TOKYO": {"lat": 35.68, "lon": 139.65, "name": "Tokyo"},           # Tokyo
    "CHUBU": {"lat": 35.18, "lon": 136.91, "name": "Nagoya"},          # Nagoya
    "HOKURIKU": {"lat": 36.59, "lon": 136.63, "name": "Kanazawa"},     # Kanazawa
    "KANSAI": {"lat": 34.69, "lon": 135.50, "name": "Osaka"},          # Osaka
    "CHUGOKU": {"lat": 34.39, "lon": 132.46, "name": "Hiroshima"},     # Hiroshima
    "SHIKOKU": {"lat": 33.84, "lon": 132.77, "name": "Matsuyama"},     # Matsuyama
    "KYUSHU": {"lat": 33.59, "lon": 130.40, "name": "Fukuoka"}         # Fukuoka
}

class JMAIngester:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def fetch_area_data(self, area: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch radiation data for a specific area using Open-Meteo Satellite API
        Uses Himawari satellite data for Japan
        """
        if area not in AREA_COORDINATES:
            logger.warning(f"Area {area} not found in coordinates map")
            return None

        coords = AREA_COORDINATES[area]
        logger.info(f"Fetching radiation data for {area} ({coords['name']}) from {start_date.date()} to {end_date.date()}")

        try:
            # Format dates for API (UTC timezone)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Build API request
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'start_date': start_str,
                'end_date': end_str,
                'hourly': 'shortwave_radiation,direct_radiation,diffuse_radiation',
                'timezone': 'Asia/Tokyo'
            }

            with httpx.Client(timeout=60.0) as client:
                response = client.get(OPEN_METEO_BASE, params=params)
                response.raise_for_status()
                data = response.json()

            # Parse response
            if 'hourly' not in data:
                logger.warning(f"No hourly data in response for {area}")
                return None

            hourly = data['hourly']
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(hourly['time']),
                'ghi': hourly.get('shortwave_radiation', []),
                'dni': hourly.get('direct_radiation', []),
                'dhi': hourly.get('diffuse_radiation', []),
            })

            logger.info(f"Fetched {len(df)} hourly records for {area}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {area}: {e}")
            return None

    def normalize_data(self, raw_df: pd.DataFrame, area: str) -> pd.DataFrame:
        """
        Normalize radiation data to standard format
        """
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()

        normalized = raw_df.copy()

        # Add area and station metadata
        coords = AREA_COORDINATES.get(area, {})
        normalized['area'] = area
        normalized['station'] = coords.get('name', area)

        # Ensure timezone awareness
        if normalized['timestamp'].dt.tz is None:
            normalized['timestamp'] = normalized['timestamp'].dt.tz_localize(JST)

        # Handle missing values and convert to float
        for col in ['ghi', 'dni', 'dhi']:
            if col in normalized.columns:
                normalized[col] = pd.to_numeric(normalized[col], errors='coerce')
                # Replace null values with None
                normalized[col] = normalized[col].where(pd.notna(normalized[col]), None)

        return normalized

    def store_data(self, df: pd.DataFrame):
        """
        Store normalized data in database using upsert to handle duplicates
        """
        if df.empty:
            logger.warning("No data to store")
            return

        try:
            from sqlalchemy import text

            # Use INSERT ... ON CONFLICT DO UPDATE to handle duplicates
            with self.engine.connect() as conn:
                for _, row in df.iterrows():
                    query = text("""
                        INSERT INTO radiation (
                            timestamp, station, area, ghi, dni, dhi
                        ) VALUES (
                            :timestamp, :station, :area, :ghi, :dni, :dhi
                        )
                        ON CONFLICT (timestamp, station, area)
                        DO UPDATE SET
                            ghi = EXCLUDED.ghi,
                            dni = EXCLUDED.dni,
                            dhi = EXCLUDED.dhi
                    """)

                    conn.execute(query, {
                        'timestamp': row['timestamp'],
                        'station': row['station'],
                        'area': row['area'],
                        'ghi': row['ghi'],
                        'dni': row['dni'],
                        'dhi': row['dhi']
                    })

                conn.commit()
                logger.info(f"Stored/updated {len(df)} radiation records")

        except Exception as e:
            logger.error(f"Error storing data: {e}")
            raise

    def run(self, areas: List[str], start_date: datetime, end_date: datetime):
        """
        Run ingestion for specified areas and date range
        Fetches satellite radiation data from Open-Meteo for each area
        """
        logger.info(f"Starting radiation data ingestion for areas: {areas}")
        logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        for area in areas:
            try:
                # Fetch data for this area
                raw_data = self.fetch_area_data(area, start_date, end_date)

                if raw_data is not None and not raw_data.empty:
                    # Normalize and store
                    normalized_data = self.normalize_data(raw_data, area)
                    self.store_data(normalized_data)
                else:
                    logger.warning(f"No data fetched for {area}")

            except Exception as e:
                logger.error(f"Error processing {area}: {e}")
                import traceback
                logger.error(traceback.format_exc())

        logger.info("Radiation data ingestion completed")

def main():
    parser = argparse.ArgumentParser(description='Ingest JMA radiation data')
    parser.add_argument('--areas', type=str, default='TOKYO,TOHOKU',
                        help='Comma-separated list of areas')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to fetch (backward from today)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Parse areas
    areas = [a.strip().upper() for a in args.areas.split(',')]

    # Parse date range
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=JST)
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').replace(tzinfo=JST)
    else:
        end_date = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=args.days)

    # Run ingestion
    ingester = JMAIngester(database_url)
    ingester.run(areas, start_date, end_date)

if __name__ == '__main__':
    main()
