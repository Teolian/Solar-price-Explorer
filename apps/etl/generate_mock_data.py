#!/usr/bin/env python3
"""
Mock Data Generator
Generates synthetic JEPX price and JMA radiation data for testing
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List
import pytz
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JST = pytz.timezone('Asia/Tokyo')

# Area to station mapping
AREA_STATION_MAP = {
    "HOKKAIDO": "ABASHIRI",
    "TOHOKU": "TSUKUBA",
    "TOKYO": "TSUKUBA",
    "CHUBU": "TSUKUBA",
    "HOKURIKU": "TSUKUBA",
    "KANSAI": "TSUKUBA",
    "CHUGOKU": "TSUKUBA",
    "SHIKOKU": "TSUKUBA",
    "KYUSHU": "TSUKUBA",
}


def generate_price_data(areas: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Generate synthetic hourly price data

    Pattern:
    - Higher prices during day (solar generation may increase supply, but demand also higher)
    - Lower prices at night
    - Weekend effect
    - Random variations
    """
    logger.info(f"Generating price data for {len(areas)} areas")

    records = []
    current = start_date

    while current <= end_date:
        for hour in range(24):
            timestamp = current.replace(hour=hour, minute=0, second=0, microsecond=0)

            for area in areas:
                # Base price varies by area
                area_base = {
                    'HOKKAIDO': 8.0,
                    'TOHOKU': 9.0,
                    'TOKYO': 12.0,
                    'CHUBU': 10.0,
                    'HOKURIKU': 9.5,
                    'KANSAI': 11.0,
                    'CHUGOKU': 9.5,
                    'SHIKOKU': 9.0,
                    'KYUSHU': 8.5,
                }.get(area, 10.0)

                # Time of day effect
                if 6 <= hour <= 9:  # Morning peak
                    time_multiplier = 1.3
                elif 17 <= hour <= 20:  # Evening peak
                    time_multiplier = 1.4
                elif 22 <= hour or hour <= 5:  # Night
                    time_multiplier = 0.7
                else:  # Day
                    time_multiplier = 1.0

                # Weekend effect
                is_weekend = timestamp.weekday() >= 5
                weekend_multiplier = 0.85 if is_weekend else 1.0

                # Random variation
                random_factor = np.random.uniform(0.9, 1.1)

                # Calculate price
                price = area_base * time_multiplier * weekend_multiplier * random_factor

                # Volume (higher during peak hours)
                base_volume = 500000
                volume = base_volume * time_multiplier * random_factor * np.random.uniform(0.8, 1.2)

                records.append({
                    'timestamp': timestamp,
                    'area': area,
                    'system_price_jpy_kwh': price * np.random.uniform(0.95, 1.05),
                    'area_price_jpy_kwh': price,
                    'volume_total_kwh': volume,
                    'volume_sell_kwh': volume * 0.5,
                    'volume_buy_kwh': volume * 0.5,
                })

        current += timedelta(days=1)

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} price records")
    return df


def generate_radiation_data(areas: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Generate synthetic hourly radiation data

    Pattern:
    - Zero at night
    - Peak around noon
    - Seasonal variation
    - Weather effects (random)
    """
    logger.info(f"Generating radiation data for {len(areas)} areas")

    records = []
    current = start_date

    while current <= end_date:
        # Day of year for seasonal variation
        day_of_year = current.timetuple().tm_yday
        seasonal_factor = 0.5 + 0.5 * np.cos((day_of_year - 172) * 2 * np.pi / 365)  # Peak in summer

        # Random cloud cover for the day
        cloud_factor = np.random.uniform(0.3, 1.0)

        for hour in range(24):
            timestamp = current.replace(hour=hour, minute=0, second=0, microsecond=0)

            # Sun elevation approximation
            if 6 <= hour <= 18:
                # Simple sine curve for sun elevation
                hour_angle = (hour - 12) * 15  # degrees from noon
                sun_factor = max(0, np.cos(np.radians(hour_angle)))
            else:
                sun_factor = 0

            for area in areas:
                station = AREA_STATION_MAP.get(area, 'TSUKUBA')

                if sun_factor > 0:
                    # GHI (Global Horizontal Irradiance)
                    ghi_max = 1000  # W/m²
                    ghi = ghi_max * sun_factor * seasonal_factor * cloud_factor * np.random.uniform(0.9, 1.1)

                    # DNI (Direct Normal Irradiance) - affected more by clouds
                    dni_max = 900
                    dni = dni_max * sun_factor * seasonal_factor * (cloud_factor ** 2) * np.random.uniform(0.9, 1.1)

                    # DHI (Diffuse Horizontal Irradiance)
                    dhi = ghi - dni * sun_factor
                    dhi = max(0, dhi)  # Ensure non-negative
                else:
                    ghi = 0
                    dni = 0
                    dhi = 0

                records.append({
                    'timestamp': timestamp,
                    'station': station,
                    'area': area,
                    'ghi': ghi,
                    'dni': dni,
                    'dhi': dhi,
                    'quality_flag': 'GOOD',
                })

        current += timedelta(days=1)

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} radiation records")
    return df


def main():
    parser = argparse.ArgumentParser(description='Generate mock data for testing')
    parser.add_argument('--areas', type=str, default='TOKYO,TOHOKU',
                        help='Comma-separated list of areas')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to generate (backward from today)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Parse areas
    areas = [a.strip().upper() for a in args.areas.split(',')]

    # Date range
    end_date = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=args.days)

    logger.info(f"Generating mock data for areas: {areas}")
    logger.info(f"Date range: {start_date} to {end_date}")

    # Generate data
    price_data = generate_price_data(areas, start_date, end_date)
    radiation_data = generate_radiation_data(areas, start_date, end_date)

    # Store in database
    engine = create_engine(database_url)

    logger.info("Storing price data...")
    price_data.to_sql('prices', engine, if_exists='append', index=False)

    logger.info("Storing radiation data...")
    radiation_data.to_sql('radiation', engine, if_exists='append', index=False)

    logger.info("Mock data generation complete!")
    logger.info(f"Generated {len(price_data)} price records and {len(radiation_data)} radiation records")


if __name__ == '__main__':
    main()
