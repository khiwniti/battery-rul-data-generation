"""
Calculated Data Generator

Generates derived/calculated data from raw telemetry:
- Telemetry calculated fields (SOC, SOH, power, THD)
- Feature store (aggregated features for ML)
- Digital twin state
- RUL predictions
- Alerts
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import uuid


class CalculatedDataGenerator:
    """Generate calculated and derived data from raw telemetry."""

    def __init__(self, seed: int = None):
        """Initialize calculated data generator."""
        if seed is not None:
            np.random.seed(seed)

    def calculate_telemetry_jar_calc(
        self,
        telemetry_jar_raw: pd.DataFrame,
        battery_degradation_states: Dict
    ) -> pd.DataFrame:
        """
        Calculate SOC and SOH from raw telemetry.

        Args:
            telemetry_jar_raw: Raw jar telemetry
            battery_degradation_states: Battery states from simulation

        Returns:
            Calculated jar telemetry DataFrame
        """
        print("Calculating jar telemetry (SOC, SOH)...")

        calc_data = []

        # Group by battery
        for battery_id, group in telemetry_jar_raw.groupby('battery_id'):
            battery_id_str = str(battery_id)

            if battery_id_str not in battery_degradation_states:
                continue

            state = battery_degradation_states[battery_id_str]

            # Simple SOC estimation (would use more sophisticated methods in production)
            # For now, use voltage-based OCV lookup
            for _, row in group.iterrows():
                # Estimate SOC from voltage (simplified)
                voltage = row['voltage_v']

                # VRLA OCV-SOC relationship (approximate)
                if voltage >= 12.65:
                    soc_pct = 90 + (voltage - 12.65) * 100
                elif voltage >= 12.30:
                    soc_pct = 50 + (voltage - 12.30) * 114.3
                else:
                    soc_pct = max(0, (voltage - 11.80) * 100)

                soc_pct = np.clip(soc_pct, 0, 100)

                # SOH from degradation model (or estimate from resistance)
                soh_pct = state['soh_pct']

                calc_data.append({
                    'ts': row['ts'],
                    'battery_id': battery_id,
                    'soc_pct': round(soc_pct, 2),
                    'soh_pct': round(soh_pct, 2)
                })

        df = pd.DataFrame(calc_data)
        print(f"  Generated {len(df):,} calculated jar telemetry records")

        return df

    def calculate_telemetry_string_calc(
        self,
        telemetry_string_raw: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate power and THD from raw string telemetry.

        Args:
            telemetry_string_raw: Raw string telemetry

        Returns:
            Calculated string telemetry DataFrame
        """
        print("Calculating string telemetry (power, THD)...")

        calc_data = []

        for _, row in telemetry_string_raw.iterrows():
            # Power = V × I
            power_w = row['voltage_v'] * abs(row['current_a'])

            # THD estimation (simplified)
            # THD is related to ripple content
            if row['mode'] in ['float', 'boost', 'equalize']:
                # Rectifier introduces harmonics
                thd_pct = (row['ripple_voltage_rms_v'] / row['voltage_v']) * 100 * 1.5
            else:
                # Battery output is clean
                thd_pct = (row['ripple_voltage_rms_v'] / row['voltage_v']) * 100 * 0.5

            thd_pct = np.clip(thd_pct, 0, 10)

            calc_data.append({
                'ts': row['ts'],
                'string_id': row['string_id'],
                'power_w': round(power_w, 2),
                'thd_pct': round(thd_pct, 2)
            })

        df = pd.DataFrame(calc_data)
        print(f"  Generated {len(df):,} calculated string telemetry records")

        return df

    def generate_feature_store(
        self,
        telemetry_jar_raw: pd.DataFrame,
        telemetry_jar_calc: pd.DataFrame,
        telemetry_string_raw: pd.DataFrame,
        window_hours: int = 1
    ) -> pd.DataFrame:
        """
        Generate aggregated features for ML.

        Args:
            telemetry_jar_raw: Raw jar telemetry
            telemetry_jar_calc: Calculated jar telemetry
            telemetry_string_raw: Raw string telemetry
            window_hours: Aggregation window

        Returns:
            Feature store DataFrame
        """
        print(f"Generating feature store (window: {window_hours}h)...")

        # Merge raw and calc jar telemetry
        jar_merged = pd.merge(
            telemetry_jar_raw,
            telemetry_jar_calc,
            on=['ts', 'battery_id'],
            how='left'
        )

        # Ensure ts is datetime
        jar_merged['ts'] = pd.to_datetime(jar_merged['ts'])

        # Create time window bins
        jar_merged['window_end'] = jar_merged['ts'].dt.floor(f'{window_hours}H') + pd.Timedelta(hours=window_hours)

        features_list = []

        # Group by battery and time window
        for (battery_id, window_end), group in jar_merged.groupby(['battery_id', 'window_end']):
            if len(group) == 0:
                continue

            # Voltage features
            v_mean = group['voltage_v'].mean()
            v_std = group['voltage_v'].std()
            v_min = group['voltage_v'].min()
            v_max = group['voltage_v'].max()

            # Temperature features
            t_mean = group['temperature_c'].mean()
            t_max = group['temperature_c'].max()

            # Resistance features
            r_latest = group['resistance_mohm'].iloc[-1]

            # Get string data for this battery (simplified - would need proper join)
            # For now, use placeholder values
            discharge_cycles = 0
            ah_throughput = 0

            features_list.append({
                'feature_ts': window_end,
                'battery_id': battery_id,
                'feature_window_hours': window_hours,
                'v_mean': round(v_mean, 3),
                'v_std': round(v_std if not pd.isna(v_std) else 0, 4),
                'v_min': round(v_min, 3),
                'v_max': round(v_max, 3),
                'v_balance_mean': 0.0,  # Would need string-level calculation
                't_mean': round(t_mean, 1),
                't_max': round(t_max, 1),
                't_delta_ambient_mean': round(t_mean - 24.0, 2),
                'r_internal_latest': round(r_latest, 3),
                'r_internal_baseline_pct': 100.0,  # Would need baseline comparison
                'discharge_cycles_count': discharge_cycles,
                'ah_throughput': ah_throughput,
                'time_below_float_min': 0,
                'time_above_float_max': 0,
                'surge_events_count': 0,
                'ripple_rms_mean': 0.5,
                'thd_mean': 1.5
            })

        df = pd.DataFrame(features_list)
        print(f"  Generated {len(df):,} feature store records")

        return df

    def generate_rul_predictions(
        self,
        feature_store: pd.DataFrame,
        battery_degradation_states: Dict,
        ml_models: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate RUL predictions using battery states.

        Args:
            feature_store: Feature store DataFrame
            battery_degradation_states: Battery states
            ml_models: ML models DataFrame

        Returns:
            RUL predictions DataFrame
        """
        print("Generating RUL predictions...")

        predictions = []

        # Get production model
        prod_model = ml_models[ml_models['status'] == 'production'].iloc[0]

        # For each battery, generate predictions at regular intervals
        for battery_id, state in battery_degradation_states.items():
            # Generate predictions every 7 days
            prediction_dates = pd.date_range(
                start=pd.Timestamp.now() - pd.Timedelta(days=180),
                end=pd.Timestamp.now(),
                freq='7D'
            )

            for pred_date in prediction_dates:
                # Estimate RUL (simplified)
                soh = state['soh_pct']

                if soh >= 90:
                    rul_days = np.random.uniform(800, 1200)
                elif soh >= 80:
                    rul_days = np.random.uniform(300, 600)
                elif soh >= 70:
                    rul_days = np.random.uniform(100, 300)
                else:
                    rul_days = np.random.uniform(10, 100)

                # Confidence intervals (wider for longer predictions)
                ci_width = rul_days * 0.3
                rul_lower = max(0, rul_days - ci_width)
                rul_upper = rul_days + ci_width

                # Failure probabilities
                if soh < 70:
                    prob_30d = 0.15
                    prob_90d = 0.35
                elif soh < 80:
                    prob_30d = 0.05
                    prob_90d = 0.15
                else:
                    prob_30d = 0.01
                    prob_90d = 0.03

                predictions.append({
                    'prediction_id': uuid.uuid4(),
                    'battery_id': battery_id,
                    'model_id': prod_model['model_id'],
                    'predicted_at': pred_date,
                    'rul_days': round(rul_days, 1),
                    'rul_lower_ci_days': round(rul_lower, 1),
                    'rul_upper_ci_days': round(rul_upper, 1),
                    'failure_probability_30d': round(prob_30d, 4),
                    'failure_probability_90d': round(prob_90d, 4),
                    'confidence_score': round(np.random.uniform(0.75, 0.95), 4),
                    'source': 'ml_model',
                    'feature_snapshot_json': {},
                    'explanation_json': {}
                })

        df = pd.DataFrame(predictions)
        print(f"  Generated {len(df):,} RUL predictions")

        return df

    def generate_alerts(
        self,
        telemetry_jar_raw: pd.DataFrame,
        telemetry_jar_calc: pd.DataFrame,
        rul_predictions: pd.DataFrame,
        batteries: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate alerts from telemetry and predictions.

        Args:
            telemetry_jar_raw: Raw jar telemetry
            telemetry_jar_calc: Calculated jar telemetry
            rul_predictions: RUL predictions
            batteries: Batteries DataFrame

        Returns:
            Alerts DataFrame
        """
        print("Generating alerts...")

        alerts = []

        # Voltage alerts
        voltage_low = telemetry_jar_raw[telemetry_jar_raw['voltage_v'] < 11.5]
        for _, row in voltage_low.head(100).iterrows():  # Limit for demo
            alerts.append({
                'alert_id': uuid.uuid4(),
                'battery_id': row['battery_id'],
                'string_id': None,
                'location_id': None,
                'alert_type': 'voltage_low',
                'severity': 'critical',
                'source': 'rule_engine',
                'model_id': None,
                'triggered_at': row['ts'],
                'resolved_at': row['ts'] + timedelta(hours=2),
                'status': 'resolved',
                'acknowledged_by': None,
                'message': f"Battery voltage critically low: {row['voltage_v']:.2f}V",
                'context_json': {'voltage': row['voltage_v'], 'threshold': 11.5},
                'incident_id': None
            })

        # Temperature alerts
        temp_high = telemetry_jar_raw[telemetry_jar_raw['temperature_c'] > 45]
        for _, row in temp_high.head(100).iterrows():
            alerts.append({
                'alert_id': uuid.uuid4(),
                'battery_id': row['battery_id'],
                'string_id': None,
                'location_id': None,
                'alert_type': 'temperature_high',
                'severity': 'warning',
                'source': 'rule_engine',
                'model_id': None,
                'triggered_at': row['ts'],
                'resolved_at': row['ts'] + timedelta(hours=1),
                'status': 'resolved',
                'acknowledged_by': None,
                'message': f"Battery temperature high: {row['temperature_c']:.1f}°C",
                'context_json': {'temperature': row['temperature_c'], 'threshold': 45.0},
                'incident_id': None
            })

        # RUL warning alerts
        rul_warning = rul_predictions[rul_predictions['rul_days'] < 90]
        for _, row in rul_warning.head(100).iterrows():
            severity = 'critical' if row['rul_days'] < 30 else 'warning'
            alert_type = 'rul_critical' if row['rul_days'] < 30 else 'rul_warning'

            alerts.append({
                'alert_id': uuid.uuid4(),
                'battery_id': row['battery_id'],
                'string_id': None,
                'location_id': None,
                'alert_type': alert_type,
                'severity': severity,
                'source': 'ml_model',
                'model_id': row['model_id'],
                'triggered_at': row['predicted_at'],
                'resolved_at': None,
                'status': 'active',
                'acknowledged_by': None,
                'message': f"Battery RUL low: {row['rul_days']:.0f} days remaining",
                'context_json': {
                    'rul_days': row['rul_days'],
                    'failure_prob_30d': row['failure_probability_30d']
                },
                'incident_id': None
            })

        df = pd.DataFrame(alerts)
        print(f"  Generated {len(df):,} alerts")

        return df
