"""
Data Validation Module for Battery Telemetry

Provides production-grade validation for generated datasets:
- Schema validation
- Range checks
- Anomaly detection
- Statistical quality checks
- Data completeness verification

CRITICAL for production use - prevents corrupted data from entering ML pipelines.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataValidator:
    """Validates generated battery telemetry data for production use."""

    # Expected schemas for each data type
    BATTERY_SENSOR_SCHEMA = {
        'ts': 'datetime64[ns]',
        'battery_id': 'object',
        'voltage_v': 'float64',
        'temperature_c': 'float64',
        'resistance_mohm': 'float64',
        'conductance_s': 'float64',
        'soc_pct': 'float64',
        'soh_pct': 'float64'
    }

    STRING_SENSOR_SCHEMA = {
        'ts': 'datetime64[ns]',
        'string_id': 'object',
        'voltage_v': 'float64',
        'current_a': 'float64',
        'mode': 'object',
        'ripple_voltage_rms_v': 'float64',
        'ripple_current_rms_a': 'float64'
    }

    # Realistic value ranges for VRLA batteries
    BATTERY_RANGES = {
        'voltage_v': (10.5, 15.0),  # VRLA operating range
        'temperature_c': (10.0, 50.0),  # Safe operating range
        'resistance_mohm': (2.0, 50.0),  # Typical range (new to aged)
        'conductance_s': (20.0, 500.0),  # Inverse of resistance
        'soc_pct': (0.0, 100.0),
        'soh_pct': (0.0, 100.0)
    }

    STRING_RANGES = {
        'voltage_v': (250.0, 360.0),  # 24 jars × 10.5-15V
        'current_a': (-250.0, 250.0),  # Discharge (negative) to charge (positive)
        'ripple_voltage_rms_v': (0.0, 2.0),
        'ripple_current_rms_a': (0.0, 5.0)
    }

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.

        Args:
            strict_mode: If True, raise exceptions on validation failures.
                        If False, log warnings and continue.
        """
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.validation_warnings = []

    def validate_schema(self, df: pd.DataFrame, expected_schema: Dict[str, str], data_type: str) -> bool:
        """
        Validate DataFrame schema matches expected structure.

        Args:
            df: DataFrame to validate
            expected_schema: Dictionary of {column_name: dtype}
            data_type: Description of data type (for error messages)

        Returns:
            True if schema is valid, False otherwise
        """
        logger.info(f"Validating schema for {data_type}...")

        is_valid = True

        # Check for missing columns
        expected_cols = set(expected_schema.keys())
        actual_cols = set(df.columns)
        missing_cols = expected_cols - actual_cols

        if missing_cols:
            msg = f"Missing columns in {data_type}: {missing_cols}"
            self._handle_error(msg)
            is_valid = False

        # Check for extra columns (warning only)
        extra_cols = actual_cols - expected_cols
        if extra_cols:
            msg = f"Extra columns in {data_type}: {extra_cols}"
            self._handle_warning(msg)

        # Check data types for existing columns
        for col in expected_cols & actual_cols:
            expected_dtype = expected_schema[col]
            actual_dtype = str(df[col].dtype)

            # Convert timestamp to datetime if needed
            if 'datetime' in expected_dtype and df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                    actual_dtype = str(df[col].dtype)
                except Exception as e:
                    msg = f"Cannot convert {col} to datetime: {e}"
                    self._handle_error(msg)
                    is_valid = False

            # Flexible dtype matching (allow int for float, etc.)
            if not self._dtype_compatible(actual_dtype, expected_dtype):
                msg = f"Column {col} has type {actual_dtype}, expected {expected_dtype}"
                self._handle_error(msg)
                is_valid = False

        if is_valid:
            logger.info(f"  ✓ Schema validation passed for {data_type}")

        return is_valid

    def validate_ranges(self, df: pd.DataFrame, range_spec: Dict[str, Tuple], data_type: str) -> bool:
        """
        Validate all values are within expected physical ranges.

        Args:
            df: DataFrame to validate
            range_spec: Dictionary of {column_name: (min, max)}
            data_type: Description of data type

        Returns:
            True if all ranges are valid, False otherwise
        """
        logger.info(f"Validating value ranges for {data_type}...")

        is_valid = True

        for col, (min_val, max_val) in range_spec.items():
            if col not in df.columns:
                continue

            # Check for out-of-range values
            out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]

            if len(out_of_range) > 0:
                pct = (len(out_of_range) / len(df)) * 100
                actual_min = df[col].min()
                actual_max = df[col].max()

                msg = (f"Column {col}: {len(out_of_range)} values ({pct:.2f}%) out of range "
                       f"[{min_val}, {max_val}]. Actual range: [{actual_min:.3f}, {actual_max:.3f}]")

                # If > 1% out of range, it's an error
                if pct > 1.0:
                    self._handle_error(msg)
                    is_valid = False
                else:
                    self._handle_warning(msg)

        if is_valid:
            logger.info(f"  ✓ Range validation passed for {data_type}")

        return is_valid

    def validate_completeness(self, df: pd.DataFrame, data_type: str) -> bool:
        """
        Check for missing values and data completeness.

        Args:
            df: DataFrame to validate
            data_type: Description of data type

        Returns:
            True if data is complete, False otherwise
        """
        logger.info(f"Validating completeness for {data_type}...")

        is_valid = True

        # Check for null values
        null_counts = df.isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0]

        if len(cols_with_nulls) > 0:
            for col, count in cols_with_nulls.items():
                pct = (count / len(df)) * 100
                msg = f"Column {col}: {count} null values ({pct:.2f}%)"

                # If > 0.1% null, it's an error
                if pct > 0.1:
                    self._handle_error(msg)
                    is_valid = False
                else:
                    self._handle_warning(msg)

        # Check for duplicate timestamps (for time series)
        if 'ts' in df.columns and 'battery_id' in df.columns:
            duplicates = df.duplicated(subset=['ts', 'battery_id'], keep=False)
            if duplicates.sum() > 0:
                msg = f"Found {duplicates.sum()} duplicate timestamps"
                self._handle_error(msg)
                is_valid = False

        if is_valid:
            logger.info(f"  ✓ Completeness validation passed for {data_type}")

        return is_valid

    def validate_time_series(self, df: pd.DataFrame, expected_interval_sec: int, data_type: str) -> bool:
        """
        Validate time series continuity and sampling rate.

        Args:
            df: DataFrame with 'ts' column
            expected_interval_sec: Expected sampling interval in seconds
            data_type: Description of data type

        Returns:
            True if time series is valid, False otherwise
        """
        logger.info(f"Validating time series for {data_type}...")

        is_valid = True

        if 'ts' not in df.columns:
            self._handle_warning(f"No timestamp column in {data_type}")
            return True

        # Convert to datetime if needed
        if df['ts'].dtype == 'object':
            df['ts'] = pd.to_datetime(df['ts'])

        # Check sampling interval
        df_sorted = df.sort_values('ts')
        time_diffs = df_sorted['ts'].diff()
        median_interval = time_diffs.median().total_seconds()

        tolerance = expected_interval_sec * 0.1  # 10% tolerance
        if abs(median_interval - expected_interval_sec) > tolerance:
            msg = (f"Median sampling interval {median_interval:.1f}s differs from expected "
                   f"{expected_interval_sec}s by more than 10%")
            self._handle_warning(msg)

        # Check for large gaps (> 2x expected interval)
        large_gaps = time_diffs[time_diffs > pd.Timedelta(seconds=expected_interval_sec * 2)]
        if len(large_gaps) > 0:
            msg = f"Found {len(large_gaps)} time gaps > 2× expected interval"
            self._handle_warning(msg)

        if is_valid:
            logger.info(f"  ✓ Time series validation passed for {data_type}")

        return is_valid

    def validate_physical_consistency(self, df: pd.DataFrame, data_type: str) -> bool:
        """
        Validate physical consistency (e.g., SOH shouldn't increase over time).

        Args:
            df: DataFrame to validate
            data_type: Description of data type

        Returns:
            True if physically consistent, False otherwise
        """
        logger.info(f"Validating physical consistency for {data_type}...")

        is_valid = True

        # Check SOH monotonicity (SOH should never increase)
        if 'soh_pct' in df.columns and 'battery_id' in df.columns:
            for battery_id in df['battery_id'].unique()[:10]:  # Sample first 10 batteries
                battery_data = df[df['battery_id'] == battery_id].sort_values('ts')
                soh_values = battery_data['soh_pct'].values

                # Check for increases (allowing small noise)
                soh_increases = np.diff(soh_values)
                significant_increases = soh_increases[soh_increases > 0.1]  # > 0.1% increase

                if len(significant_increases) > 0:
                    msg = f"Battery {battery_id}: SOH increased {len(significant_increases)} times (physically impossible)"
                    self._handle_error(msg)
                    is_valid = False
                    break

        # Check voltage-SOC relationship (higher SOC should correlate with higher voltage)
        if 'voltage_v' in df.columns and 'soc_pct' in df.columns:
            # Sample correlation check
            sample_size = min(10000, len(df))
            sample = df.sample(n=sample_size, random_state=42)
            correlation = sample['voltage_v'].corr(sample['soc_pct'])

            if correlation < 0.3:  # Should be positive correlation
                msg = f"Weak voltage-SOC correlation ({correlation:.3f}), expected > 0.3"
                self._handle_warning(msg)

        if is_valid:
            logger.info(f"  ✓ Physical consistency validation passed for {data_type}")

        return is_valid

    def validate_battery_sensors(
        self,
        df: pd.DataFrame,
        expected_interval_sec: int = 60
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Complete validation suite for battery sensor data.

        Args:
            df: Battery sensor DataFrame
            expected_interval_sec: Expected sampling interval

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        logger.info("="*80)
        logger.info("VALIDATING BATTERY SENSOR DATA")
        logger.info("="*80)

        self.validation_errors = []
        self.validation_warnings = []

        # Run all validation checks
        checks = [
            self.validate_schema(df, self.BATTERY_SENSOR_SCHEMA, "battery sensors"),
            self.validate_ranges(df, self.BATTERY_RANGES, "battery sensors"),
            self.validate_completeness(df, "battery sensors"),
            self.validate_time_series(df, expected_interval_sec, "battery sensors"),
            self.validate_physical_consistency(df, "battery sensors")
        ]

        is_valid = all(checks)

        # Summary
        logger.info("="*80)
        if is_valid:
            logger.info("✓ ALL VALIDATION CHECKS PASSED")
        else:
            logger.error(f"✗ VALIDATION FAILED: {len(self.validation_errors)} errors")

        logger.info(f"Errors: {len(self.validation_errors)}")
        logger.info(f"Warnings: {len(self.validation_warnings)}")
        logger.info("="*80)

        return is_valid, self.validation_errors, self.validation_warnings

    def validate_string_sensors(
        self,
        df: pd.DataFrame,
        expected_interval_sec: int = 60
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Complete validation suite for string sensor data.

        Args:
            df: String sensor DataFrame
            expected_interval_sec: Expected sampling interval

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        logger.info("="*80)
        logger.info("VALIDATING STRING SENSOR DATA")
        logger.info("="*80)

        self.validation_errors = []
        self.validation_warnings = []

        checks = [
            self.validate_schema(df, self.STRING_SENSOR_SCHEMA, "string sensors"),
            self.validate_ranges(df, self.STRING_RANGES, "string sensors"),
            self.validate_completeness(df, "string sensors"),
            self.validate_time_series(df, expected_interval_sec, "string sensors")
        ]

        is_valid = all(checks)

        logger.info("="*80)
        if is_valid:
            logger.info("✓ ALL VALIDATION CHECKS PASSED")
        else:
            logger.error(f"✗ VALIDATION FAILED: {len(self.validation_errors)} errors")

        logger.info(f"Errors: {len(self.validation_errors)}")
        logger.info(f"Warnings: {len(self.validation_warnings)}")
        logger.info("="*80)

        return is_valid, self.validation_errors, self.validation_warnings

    def _dtype_compatible(self, actual: str, expected: str) -> bool:
        """Check if data types are compatible."""
        # Allow flexible matching
        if actual == expected:
            return True
        if 'int' in actual and 'int' in expected:
            return True
        if 'float' in actual and 'float' in expected:
            return True
        if 'object' in actual and 'object' in expected:
            return True
        if 'datetime' in actual and 'datetime' in expected:
            return True
        return False

    def _handle_error(self, message: str):
        """Handle validation error."""
        self.validation_errors.append(message)
        if self.strict_mode:
            logger.error(f"  ✗ {message}")
            raise ValueError(message)
        else:
            logger.error(f"  ✗ {message}")

    def _handle_warning(self, message: str):
        """Handle validation warning."""
        self.validation_warnings.append(message)
        logger.warning(f"  ⚠ {message}")
