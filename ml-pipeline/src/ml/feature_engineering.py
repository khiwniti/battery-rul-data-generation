"""
Feature Engineering for RUL Prediction
Extracts ML features from battery telemetry data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Extract and engineer features for RUL prediction"""

    def __init__(self, lookback_hours: int = 24):
        """
        Initialize feature engineer

        Args:
            lookback_hours: Hours of historical data to use for feature extraction
        """
        self.lookback_hours = lookback_hours

    def extract_features(
        self,
        telemetry_df: pd.DataFrame,
        battery_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract features from battery telemetry data

        Args:
            telemetry_df: Raw telemetry data with columns:
                - battery_id, timestamp, voltage_v, current_a, temperature_c,
                  internal_resistance_mohm, soc_pct, soh_pct
            battery_id: Optional filter for specific battery

        Returns:
            DataFrame with engineered features
        """
        df = telemetry_df.copy()

        # Filter by battery if specified
        if battery_id:
            df = df[df['battery_id'] == battery_id]

        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Sort by battery and timestamp
        df = df.sort_values(['battery_id', 'timestamp'])

        # Group by battery
        features_list = []
        for battery, group in df.groupby('battery_id'):
            battery_features = self._extract_battery_features(group)
            if battery_features is not None:
                features_list.append(battery_features)

        if not features_list:
            return pd.DataFrame()

        return pd.DataFrame(features_list)

    def _extract_battery_features(self, battery_df: pd.DataFrame) -> Optional[Dict]:
        """
        Extract features for a single battery

        Args:
            battery_df: Telemetry data for one battery

        Returns:
            Dictionary of features
        """
        if len(battery_df) < 10:  # Need minimum data points
            return None

        battery_id = battery_df['battery_id'].iloc[0]
        latest_timestamp = battery_df['timestamp'].max()

        # Time-based filtering (last lookback_hours)
        lookback_start = latest_timestamp - timedelta(hours=self.lookback_hours)
        recent_df = battery_df[battery_df['timestamp'] >= lookback_start]

        if len(recent_df) < 5:
            recent_df = battery_df  # Use all available data if insufficient recent data

        features = {
            'battery_id': battery_id,
            'timestamp': latest_timestamp,
        }

        # Voltage features
        features['voltage_mean'] = recent_df['voltage_v'].mean()
        features['voltage_std'] = recent_df['voltage_v'].std()
        features['voltage_min'] = recent_df['voltage_v'].min()
        features['voltage_max'] = recent_df['voltage_v'].max()
        features['voltage_range'] = features['voltage_max'] - features['voltage_min']
        features['voltage_cv'] = features['voltage_std'] / features['voltage_mean'] if features['voltage_mean'] > 0 else 0

        # Temperature features
        features['temperature_mean'] = recent_df['temperature_c'].mean()
        features['temperature_std'] = recent_df['temperature_c'].std()
        features['temperature_max'] = recent_df['temperature_c'].max()
        features['temperature_min'] = recent_df['temperature_c'].min()

        # High temperature exposure (critical for degradation)
        features['temp_above_35c_pct'] = (recent_df['temperature_c'] > 35).sum() / len(recent_df) * 100
        features['temp_above_40c_pct'] = (recent_df['temperature_c'] > 40).sum() / len(recent_df) * 100

        # Internal resistance features (key indicator of degradation)
        if 'internal_resistance_mohm' in recent_df.columns:
            features['resistance_mean'] = recent_df['internal_resistance_mohm'].mean()
            features['resistance_std'] = recent_df['internal_resistance_mohm'].std()
            features['resistance_max'] = recent_df['internal_resistance_mohm'].max()
            features['resistance_trend'] = self._calculate_trend(
                recent_df['timestamp'], recent_df['internal_resistance_mohm']
            )
        else:
            features['resistance_mean'] = 0
            features['resistance_std'] = 0
            features['resistance_max'] = 0
            features['resistance_trend'] = 0

        # SOC features (State of Charge)
        if 'soc_pct' in recent_df.columns:
            features['soc_mean'] = recent_df['soc_pct'].mean()
            features['soc_std'] = recent_df['soc_pct'].std()
            features['soc_min'] = recent_df['soc_pct'].min()
        else:
            features['soc_mean'] = 100
            features['soc_std'] = 0
            features['soc_min'] = 100

        # SOH features (State of Health - target variable)
        if 'soh_pct' in recent_df.columns:
            features['soh_current'] = recent_df['soh_pct'].iloc[-1]
            features['soh_mean'] = recent_df['soh_pct'].mean()
            features['soh_trend'] = self._calculate_trend(
                recent_df['timestamp'], recent_df['soh_pct']
            )
        else:
            features['soh_current'] = 100
            features['soh_mean'] = 100
            features['soh_trend'] = 0

        # Current features
        if 'current_a' in recent_df.columns:
            features['current_mean'] = recent_df['current_a'].mean()
            features['current_std'] = recent_df['current_a'].std()
            features['current_max'] = recent_df['current_a'].abs().max()
        else:
            features['current_mean'] = 0
            features['current_std'] = 0
            features['current_max'] = 0

        # Operational features
        features['data_points_count'] = len(recent_df)
        features['time_span_hours'] = (
            recent_df['timestamp'].max() - recent_df['timestamp'].min()
        ).total_seconds() / 3600

        # Discharge cycle detection (voltage drops below 12V)
        if 'voltage_v' in recent_df.columns:
            features['discharge_cycles'] = self._count_discharge_cycles(recent_df['voltage_v'])
        else:
            features['discharge_cycles'] = 0

        # Voltage stability (important for RUL)
        features['voltage_stability'] = 1.0 / (1.0 + features['voltage_std'])

        return features

    def _calculate_trend(self, timestamps: pd.Series, values: pd.Series) -> float:
        """
        Calculate trend (slope) of a time series

        Args:
            timestamps: Timestamp series
            values: Value series

        Returns:
            Slope of linear regression (trend per day)
        """
        if len(timestamps) < 2 or values.std() == 0:
            return 0.0

        # Convert timestamps to numeric (days since first timestamp)
        time_numeric = (timestamps - timestamps.min()).dt.total_seconds() / 86400

        # Simple linear regression
        x = time_numeric.values
        y = values.values

        # Remove NaN values
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            return 0.0

        # Calculate slope
        try:
            slope = np.polyfit(x, y, 1)[0]
            return float(slope)
        except Exception:
            return 0.0

    def _count_discharge_cycles(self, voltage_series: pd.Series, threshold: float = 12.0) -> int:
        """
        Count number of discharge cycles (voltage drops below threshold)

        Args:
            voltage_series: Voltage time series
            threshold: Voltage threshold for discharge detection

        Returns:
            Number of discharge cycles
        """
        below_threshold = voltage_series < threshold
        # Count transitions from False to True (start of discharge)
        cycles = (below_threshold & ~below_threshold.shift(1, fill_value=False)).sum()
        return int(cycles)

    def prepare_training_data(
        self,
        telemetry_df: pd.DataFrame,
        battery_states: Dict
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data with features (X) and target (y)

        Args:
            telemetry_df: Raw telemetry data
            battery_states: Ground truth battery states with SOH and RUL

        Returns:
            Tuple of (features_df, target_series)
        """
        # Extract features
        features_df = self.extract_features(telemetry_df)

        if features_df.empty:
            return pd.DataFrame(), pd.Series()

        # Add ground truth RUL from battery_states
        rul_values = []
        for _, row in features_df.iterrows():
            battery_id = row['battery_id']
            if battery_id in battery_states:
                state = battery_states[battery_id]
                # RUL in days (approximate from SOH)
                # Assuming healthy battery lasts 1825 days (5 years)
                # RUL = (current_SOH - 80) / (100 - 80) * remaining_life
                soh = state.get('soh_pct', 100)
                if soh >= 80:
                    rul_days = (soh - 80) / 20 * 1825
                else:
                    rul_days = 0  # Battery below 80% SOH is end-of-life
                rul_values.append(rul_days)
            else:
                rul_values.append(None)

        features_df['rul_days'] = rul_values

        # Remove rows with missing RUL
        features_df = features_df.dropna(subset=['rul_days'])

        # Separate features and target
        feature_columns = [col for col in features_df.columns
                          if col not in ['battery_id', 'timestamp', 'rul_days']]
        X = features_df[feature_columns]
        y = features_df['rul_days']

        return X, y
