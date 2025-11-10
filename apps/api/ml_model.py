"""
ML Model Module
Baseline price forecasting using XGBoost
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
import joblib
import pytz

logger = logging.getLogger(__name__)
JST = pytz.timezone('Asia/Tokyo')

class PriceForecaster:
    """
    Baseline price forecasting model using XGBoost
    """

    def __init__(self, model_path: str = "models"):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)
        self.model = None
        self.feature_names = None

    def prepare_features(self, df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target from dataframe

        Args:
            df: Features dataframe
            feature_cols: List of feature column names

        Returns:
            X: Features dataframe
            y: Target series
        """
        # Filter to available features
        available_features = [col for col in feature_cols if col in df.columns]

        if not available_features:
            raise ValueError(f"No features available from: {feature_cols}")

        X = df[available_features].copy()
        y = df['target_price'].copy() if 'target_price' in df.columns else None

        # Handle missing values
        X = X.fillna(0)

        return X, y

    def train(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        val_ratio: float = 0.2
    ) -> Dict:
        """
        Train the forecasting model

        Args:
            df: Training data with features and target
            feature_cols: List of feature columns to use
            val_ratio: Validation set ratio

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training model with {len(df)} samples")

        X, y = self.prepare_features(df, feature_cols)

        if y is None or y.isna().all():
            raise ValueError("No target values available for training")

        # Drop rows with missing target
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]

        if len(X) < 168:  # Less than 1 week of hourly data
            raise ValueError(f"Insufficient training data: {len(X)} samples (need at least 168)")

        # Time-based split (validation = last val_ratio of data)
        split_idx = int(len(X) * (1 - val_ratio))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        logger.info(f"Train size: {len(X_train)}, Validation size: {len(X_val)}")

        # Train XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)
        self.feature_names = X.columns.tolist()

        # Evaluate
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_mae = mean_absolute_error(y_train, train_pred)
        val_mae = mean_absolute_error(y_val, val_pred)

        # Benchmark: naive "yesterday at this hour" forecast
        # For validation set, use value from 24 hours ago
        if 'price_lag_24h' in X_val.columns:
            naive_pred = X_val['price_lag_24h'].values
            naive_mae = mean_absolute_error(y_val, naive_pred)
        else:
            naive_mae = None

        metrics = {
            'train_mae': float(train_mae),
            'val_mae': float(val_mae),
            'naive_mae': float(naive_mae) if naive_mae else None,
            'n_train': len(X_train),
            'n_val': len(X_val),
            'features': self.feature_names
        }

        logger.info(f"Training MAE: {train_mae:.2f}, Validation MAE: {val_mae:.2f}")
        if naive_mae:
            logger.info(f"Naive benchmark MAE: {naive_mae:.2f}")

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Features dataframe

        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        # Ensure features match training
        if self.feature_names:
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                logger.warning(f"Missing features: {missing_features}, filling with zeros")
                for feat in missing_features:
                    X[feat] = 0

            X = X[self.feature_names]

        X = X.fillna(0)
        return self.model.predict(X)

    def forecast(
        self,
        last_features: pd.DataFrame,
        horizon_hours: int,
        future_radiation: Optional[List[Dict]] = None
    ) -> pd.DataFrame:
        """
        Generate multi-step forecast

        Args:
            last_features: Most recent feature row(s)
            horizon_hours: Number of hours to forecast
            future_radiation: Optional future radiation values

        Returns:
            Dataframe with forecast timestamps and predictions
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        logger.info(f"Generating {horizon_hours}h forecast")

        # Start from last timestamp
        last_ts = pd.to_datetime(last_features['timestamp'].iloc[-1])

        forecasts = []

        # Simple approach: use latest features, update time-based features
        base_features = last_features.iloc[-1].copy()

        for h in range(1, horizon_hours + 1):
            forecast_ts = last_ts + pd.Timedelta(hours=h)

            # Update calendar features
            base_features['hour'] = forecast_ts.hour
            base_features['dow'] = forecast_ts.dayofweek
            base_features['month'] = forecast_ts.month
            base_features['is_weekend'] = 1 if forecast_ts.dayofweek >= 5 else 0

            # Update radiation if provided
            if future_radiation and h - 1 < len(future_radiation):
                rad_data = future_radiation[h - 1]
                base_features['ghi'] = rad_data.get('ghi', 0)
                base_features['dni'] = rad_data.get('dni', 0)
                base_features['dhi'] = rad_data.get('dhi', 0)
            else:
                # Use zero radiation (conservative for nighttime)
                # In production, should use weather forecast or historical patterns
                if forecast_ts.hour < 6 or forecast_ts.hour > 18:
                    base_features['ghi'] = 0
                    base_features['dni'] = 0
                    base_features['dhi'] = 0

            # Make prediction
            X_pred = pd.DataFrame([base_features])
            pred = self.predict(X_pred)[0]

            forecasts.append({
                'timestamp': forecast_ts,
                'price_pred': pred
            })

            # Update lags for next iteration
            # This is simplified - in production would need more sophisticated lag updates
            base_features['price_lag_1h'] = pred

        return pd.DataFrame(forecasts)

    def save(self, model_id: str):
        """Save model to disk"""
        model_file = os.path.join(self.model_path, f"{model_id}.pkl")
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names
        }, model_file)
        logger.info(f"Model saved to {model_file}")
        return model_file

    def load(self, model_id: str):
        """Load model from disk"""
        model_file = os.path.join(self.model_path, f"{model_id}.pkl")
        if not os.path.exists(model_file):
            raise FileNotFoundError(f"Model file not found: {model_file}")

        data = joblib.load(model_file)
        self.model = data['model']
        self.feature_names = data['feature_names']
        logger.info(f"Model loaded from {model_file}")


def compute_correlations(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute correlations between radiation and price

    Args:
        df: Dataframe with radiation and price columns

    Returns:
        Dictionary with correlation coefficients
    """
    if len(df) < 2:
        return {'r_ghi': None, 'r_dni': None, 'r_dhi': None, 'n': 0}

    # Filter to daytime (when solar matters)
    if 'hour' in df.columns:
        df = df[(df['hour'] >= 6) & (df['hour'] <= 18)]

    correlations = {}
    target_col = 'target_price' if 'target_price' in df.columns else 'price'

    if target_col not in df.columns:
        return {'r_ghi': None, 'r_dni': None, 'r_dhi': None, 'n': 0}

    for rad_col in ['ghi', 'dni', 'dhi']:
        if rad_col in df.columns:
            # Drop NaN pairs
            mask = df[rad_col].notna() & df[target_col].notna()
            if mask.sum() > 2:
                corr = df.loc[mask, rad_col].corr(df.loc[mask, target_col])
                correlations[f'r_{rad_col}'] = float(corr) if not pd.isna(corr) else None
            else:
                correlations[f'r_{rad_col}'] = None
        else:
            correlations[f'r_{rad_col}'] = None

    correlations['n'] = len(df)

    return correlations
