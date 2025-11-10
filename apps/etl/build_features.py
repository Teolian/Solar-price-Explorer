#!/usr/bin/env python3
"""
Feature Builder Script
Creates ML features from raw price and radiation data
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List
import pytz
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JST = pytz.timezone('Asia/Tokyo')

class FeatureBuilder:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def fetch_raw_data(self, area: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch and merge price and radiation data
        """
        logger.info(f"Fetching raw data for {area}: {start_date} to {end_date}")

        # Fetch prices
        price_query = text("""
            SELECT timestamp, area_price_jpy_kwh as price, volume_total_kwh as volume
            FROM prices
            WHERE area = :area
              AND timestamp >= :start_date
              AND timestamp <= :end_date
            ORDER BY timestamp
        """)

        # Fetch radiation
        radiation_query = text("""
            SELECT timestamp, ghi, dni, dhi
            FROM radiation
            WHERE area = :area
              AND timestamp >= :start_date
              AND timestamp <= :end_date
            ORDER BY timestamp
        """)

        with self.engine.connect() as conn:
            prices_df = pd.read_sql(
                price_query,
                conn,
                params={'area': area, 'start_date': start_date, 'end_date': end_date}
            )

            radiation_df = pd.read_sql(
                radiation_query,
                conn,
                params={'area': area, 'start_date': start_date, 'end_date': end_date}
            )

        # Merge on timestamp
        if not prices_df.empty and not radiation_df.empty:
            merged = pd.merge(prices_df, radiation_df, on='timestamp', how='outer')
            merged = merged.sort_values('timestamp').reset_index(drop=True)
            logger.info(f"Merged {len(merged)} records for {area}")
            return merged
        else:
            logger.warning(f"Insufficient data for {area}")
            return pd.DataFrame()

    def build_features(self, df: pd.DataFrame, area: str) -> pd.DataFrame:
        """
        Build ML features from raw data

        Features:
        - target_price: area price (target variable)
        - ghi, dni, dhi: current radiation values
        - volume_kwh: trading volume
        - price_lag_1h, price_lag_24h: lagged prices
        - ghi_lag_1h: lagged radiation
        - ghi_roll3h: 3-hour rolling mean of GHI
        - hour, dow, month: calendar features
        - is_weekend: weekend indicator
        """
        if df.empty:
            return pd.DataFrame()

        logger.info(f"Building features for {area}")

        features = df.copy()
        features['area'] = area

        # Rename target
        if 'price' in features.columns:
            features['target_price'] = features['price']

        # Lagged features
        if 'price' in features.columns:
            features['price_lag_1h'] = features['price'].shift(1)
            features['price_lag_24h'] = features['price'].shift(24)

        if 'ghi' in features.columns:
            features['ghi_lag_1h'] = features['ghi'].shift(1)
            features['ghi_roll3h'] = features['ghi'].rolling(window=3, min_periods=1).mean()

        # Rename volume
        if 'volume' in features.columns:
            features['volume_kwh'] = features['volume']

        # Calendar features
        features['timestamp'] = pd.to_datetime(features['timestamp'])
        features['hour'] = features['timestamp'].dt.hour
        features['dow'] = features['timestamp'].dt.dayofweek
        features['month'] = features['timestamp'].dt.month
        features['is_weekend'] = (features['dow'] >= 5).astype(int)

        # Select final columns
        final_cols = [
            'timestamp', 'area', 'target_price',
            'ghi', 'dni', 'dhi', 'volume_kwh',
            'price_lag_1h', 'price_lag_24h',
            'ghi_lag_1h', 'ghi_roll3h',
            'hour', 'dow', 'month', 'is_weekend'
        ]

        # Keep only columns that exist
        final_cols = [col for col in final_cols if col in features.columns]
        features = features[final_cols]

        # Drop rows with insufficient lags
        features = features.dropna(subset=['price_lag_1h'])

        logger.info(f"Built {len(features)} feature records for {area}")
        return features

    def store_features(self, df: pd.DataFrame):
        """
        Store features in database
        """
        if df.empty:
            logger.warning("No features to store")
            return

        try:
            # Delete existing features for this period to avoid duplicates
            with self.engine.connect() as conn:
                area = df['area'].iloc[0]
                min_ts = df['timestamp'].min()
                max_ts = df['timestamp'].max()

                delete_query = text("""
                    DELETE FROM features
                    WHERE area = :area
                      AND timestamp >= :min_ts
                      AND timestamp <= :max_ts
                """)
                conn.execute(delete_query, {'area': area, 'min_ts': min_ts, 'max_ts': max_ts})
                conn.commit()

            # Insert new features
            df.to_sql('features', self.engine, if_exists='append', index=False)
            logger.info(f"Stored {len(df)} feature records")
        except Exception as e:
            logger.error(f"Error storing features: {e}")
            raise

    def run(self, areas: List[str], days: int = 7):
        """
        Build features for specified areas
        """
        logger.info(f"Building features for areas: {areas}")

        end_date = datetime.now(JST)
        start_date = end_date - timedelta(days=days)

        for area in areas:
            try:
                # Fetch raw data with extra buffer for lags
                fetch_start = start_date - timedelta(days=2)
                raw_data = self.fetch_raw_data(area, fetch_start, end_date)

                if not raw_data.empty:
                    features = self.build_features(raw_data, area)

                    # Features already filtered by build_features dropna()
                    # No need for additional date filtering
                    self.store_features(features)
                else:
                    logger.warning(f"No raw data available for {area}")
            except Exception as e:
                logger.error(f"Error building features for {area}: {e}")

        logger.info("Feature building completed")

def main():
    parser = argparse.ArgumentParser(description='Build ML features')
    parser.add_argument('--areas', type=str, default='TOKYO,TOHOKU',
                        help='Comma-separated list of areas')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to process (backward from today)')
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
        # Use explicit date range (not used in run(), but for clarity)
        logger.info(f"Building features from {args.start_date} to {args.end_date}")
        days = (datetime.strptime(args.end_date, '%Y-%m-%d') -
                datetime.strptime(args.start_date, '%Y-%m-%d')).days
    else:
        days = args.days

    # Run feature building
    builder = FeatureBuilder(database_url)
    builder.run(areas, args.days)

if __name__ == '__main__':
    main()
