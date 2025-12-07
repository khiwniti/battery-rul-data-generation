#!/usr/bin/env python3
"""
Production Dataset Validation Script

Validates generated battery dataset for production ML use.
Checks physics correctness, data quality, and ML readiness.

Usage:
    python validate_production_dataset.py --data-dir ./output/full_dataset
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_validator import DataValidator


def print_header(title):
    """Print formatted header."""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def validate_production_dataset(data_dir: str, strict: bool = False):
    """
    Run complete production validation suite.

    Args:
        data_dir: Directory containing generated data
        strict: If True, fail on any warnings

    Returns:
        True if validation passes, False otherwise
    """
    print_header("PRODUCTION DATASET VALIDATION")
    print(f"Data directory: {data_dir}")
    print(f"Validation mode: {'STRICT' if strict else 'PERMISSIVE'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"\n✗ ERROR: Data directory does not exist: {data_dir}")
        return False

    validation_passed = True
    warnings_count = 0
    errors_count = 0

    # =========================================================================
    # PART 1: File Existence Check
    # =========================================================================
    print_header("1. FILE EXISTENCE CHECK")

    # Check for combined files or per-location files
    combined_battery = data_path / "battery_sensors_combined.csv.gz"
    combined_string = data_path / "string_sensors_combined.csv.gz"
    location_dir = data_path / "by_location"

    has_combined = combined_battery.exists() and combined_string.exists()
    has_location_files = location_dir.exists() and len(list(location_dir.glob("battery_sensors_*.csv.gz"))) > 0

    if not (has_combined or has_location_files):
        print("✗ ERROR: No sensor data files found")
        print(f"  Expected either:")
        print(f"  - Combined files: {combined_battery} and {combined_string}")
        print(f"  - Location files: {location_dir}/battery_sensors_*.csv.gz")
        return False

    print(f"✓ Data files found:")
    if has_combined:
        print(f"  - Combined battery sensors: {combined_battery}")
        print(f"  - Combined string sensors: {combined_string}")
    if has_location_files:
        battery_files = list(location_dir.glob("battery_sensors_*.csv.gz"))
        string_files = list(location_dir.glob("string_sensors_*.csv.gz"))
        print(f"  - Location battery files: {len(battery_files)} files")
        print(f"  - Location string files: {len(string_files)} files")

    # =========================================================================
    # PART 2: Load Data
    # =========================================================================
    print_header("2. LOADING DATA")

    try:
        if has_combined:
            print("Loading combined dataset...")
            battery_sensors = pd.read_csv(combined_battery, compression='gzip')
            string_sensors = pd.read_csv(combined_string, compression='gzip')
        else:
            print("Loading and combining location files...")
            battery_files = sorted(location_dir.glob("battery_sensors_*.csv.gz"))
            string_files = sorted(location_dir.glob("string_sensors_*.csv.gz"))

            battery_chunks = [pd.read_csv(f, compression='gzip') for f in battery_files]
            string_chunks = [pd.read_csv(f, compression='gzip') for f in string_files]

            battery_sensors = pd.concat(battery_chunks, ignore_index=True)
            string_sensors = pd.concat(string_chunks, ignore_index=True)

        print(f"✓ Loaded {len(battery_sensors):,} battery sensor records")
        print(f"✓ Loaded {len(string_sensors):,} string sensor records")

    except Exception as e:
        print(f"✗ ERROR loading data: {e}")
        return False

    # =========================================================================
    # PART 3: Schema and Range Validation
    # =========================================================================
    print_header("3. SCHEMA AND RANGE VALIDATION")

    validator = DataValidator(strict_mode=strict)

    # Validate battery sensors
    try:
        is_valid, errors, warnings = validator.validate_battery_sensors(
            battery_sensors,
            expected_interval_sec=60
        )

        errors_count += len(errors)
        warnings_count += len(warnings)

        if not is_valid:
            validation_passed = False
            print("\n✗ Battery sensor validation FAILED")
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("\n✓ Battery sensor validation PASSED")

        if warnings:
            for warning in warnings:
                print(f"  WARNING: {warning}")

    except Exception as e:
        print(f"\n✗ Battery sensor validation FAILED with exception: {e}")
        validation_passed = False

    # Validate string sensors
    try:
        is_valid, errors, warnings = validator.validate_string_sensors(
            string_sensors,
            expected_interval_sec=60
        )

        errors_count += len(errors)
        warnings_count += len(warnings)

        if not is_valid:
            validation_passed = False
            print("\n✗ String sensor validation FAILED")
            for error in errors:
                print(f"  ERROR: {error}")
        else:
            print("\n✓ String sensor validation PASSED")

        if warnings:
            for warning in warnings:
                print(f"  WARNING: {warning}")

    except Exception as e:
        print(f"\n✗ String sensor validation FAILED with exception: {e}")
        validation_passed = False

    # =========================================================================
    # PART 4: ML Readiness Checks
    # =========================================================================
    print_header("4. ML READINESS CHECKS")

    # Check for essential features
    required_features = ['voltage_v', 'temperature_c', 'resistance_mohm', 'soc_pct', 'soh_pct']
    missing_features = [f for f in required_features if f not in battery_sensors.columns]

    if missing_features:
        print(f"✗ Missing essential features: {missing_features}")
        validation_passed = False
    else:
        print(f"✓ All essential features present: {required_features}")

    # Check temperature diversity (critical for RUL prediction)
    if 'temperature_c' in battery_sensors.columns:
        temp_stats = battery_sensors['temperature_c'].describe()
        temp_range = temp_stats['max'] - temp_stats['min']

        print(f"\nTemperature diversity:")
        print(f"  Mean: {temp_stats['mean']:.2f}°C")
        print(f"  Std: {temp_stats['std']:.2f}°C")
        print(f"  Range: {temp_stats['min']:.1f}°C - {temp_stats['max']:.1f}°C ({temp_range:.1f}°C)")

        if temp_range < 10.0:
            print(f"  ⚠ WARNING: Low temperature diversity ({temp_range:.1f}°C)")
            print(f"     ML models may not learn temperature effects well")
            warnings_count += 1
        else:
            print(f"  ✓ Good temperature diversity for ML training")

    # Check SOH distribution
    if 'soh_pct' in battery_sensors.columns:
        # Sample one record per battery to get final SOH
        latest_soh = battery_sensors.groupby('battery_id')['soh_pct'].last()
        soh_stats = latest_soh.describe()

        print(f"\nSOH Distribution:")
        print(f"  Mean: {soh_stats['mean']:.2f}%")
        print(f"  Std: {soh_stats['std']:.2f}%")
        print(f"  Range: {soh_stats['min']:.1f}% - {soh_stats['max']:.1f}%")

        # Check for degradation
        if soh_stats['min'] > 95.0:
            print(f"  ⚠ WARNING: Limited degradation (min SOH = {soh_stats['min']:.1f}%)")
            print(f"     Consider longer simulation or accelerated profiles")
            warnings_count += 1
        else:
            print(f"  ✓ Good SOH variation for ML training")

    # Check class balance (for classification tasks)
    if 'soh_pct' in battery_sensors.columns:
        latest_soh = battery_sensors.groupby('battery_id')['soh_pct'].last()

        # Define health categories
        healthy = (latest_soh >= 90).sum()
        degraded = ((latest_soh >= 80) & (latest_soh < 90)).sum()
        critical = (latest_soh < 80).sum()

        total = len(latest_soh)
        print(f"\nHealth Class Distribution:")
        print(f"  Healthy (≥90%): {healthy} ({healthy/total*100:.1f}%)")
        print(f"  Degraded (80-90%): {degraded} ({degraded/total*100:.1f}%)")
        print(f"  Critical (<80%): {critical} ({critical/total*100:.1f}%)")

        if critical < total * 0.01:
            print(f"  ⚠ WARNING: Very few critical batteries ({critical/total*100:.1f}%)")
            print(f"     May have insufficient examples for failure prediction")
            warnings_count += 1

    # =========================================================================
    # PART 5: Physics Sanity Checks
    # =========================================================================
    print_header("5. PHYSICS SANITY CHECKS")

    # Check Arrhenius relationship (temperature vs degradation)
    if 'temperature_c' in battery_sensors.columns and 'soh_pct' in battery_sensors.columns:
        # Sample for performance
        sample = battery_sensors.sample(n=min(50000, len(battery_sensors)), random_state=42)
        correlation = sample['temperature_c'].corr(sample['soh_pct'])

        print(f"Temperature-SOH correlation: {correlation:.3f}")
        if correlation > -0.1:  # Should be negative (higher temp = faster degradation)
            print(f"  ⚠ WARNING: Weak temperature effect on SOH")
            print(f"     Expected negative correlation (higher temp = lower SOH)")
            warnings_count += 1
        else:
            print(f"  ✓ Realistic temperature effect (negative correlation)")

    # Check voltage-SOC monotonicity
    if 'voltage_v' in battery_sensors.columns and 'soc_pct' in battery_sensors.columns:
        sample = battery_sensors.sample(n=min(10000, len(battery_sensors)), random_state=42)
        correlation = sample['voltage_v'].corr(sample['soc_pct'])

        print(f"Voltage-SOC correlation: {correlation:.3f}")
        if correlation < 0.5:  # Should be strong positive
            print(f"  ⚠ WARNING: Weak voltage-SOC correlation")
            print(f"     Expected strong positive correlation (higher SOC = higher voltage)")
            warnings_count += 1
        else:
            print(f"  ✓ Realistic voltage-SOC relationship")

    # =========================================================================
    # PART 6: Final Summary
    # =========================================================================
    print_header("VALIDATION SUMMARY")

    print(f"\nErrors: {errors_count}")
    print(f"Warnings: {warnings_count}")
    print(f"Total records: {len(battery_sensors):,} battery sensors, {len(string_sensors):,} string sensors")

    if validation_passed and (not strict or warnings_count == 0):
        print("\n" + "="*80)
        print("✓✓✓ VALIDATION PASSED - DATASET IS PRODUCTION-READY ✓✓✓")
        print("="*80)
        print("\nThis dataset is safe for:")
        print("  ✓ ML model training")
        print("  ✓ Algorithm validation")
        print("  ✓ Production deployment")
        print("\nRecommended next steps:")
        print("  1. Train baseline RUL prediction model")
        print("  2. Evaluate feature importance (temperature should be top-3)")
        print("  3. Test with different ML algorithms (GBM, XGBoost, LSTM)")
        print("  4. Validate model performance on holdout set")
        return True
    else:
        print("\n" + "="*80)
        print("✗✗✗ VALIDATION FAILED - REVIEW REQUIRED ✗✗✗")
        print("="*80)
        print(f"\nFound {errors_count} errors and {warnings_count} warnings")
        print("Review the issues above before using this dataset for production ML.")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate generated battery dataset for production ML use"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./output/full_dataset",
        help="Directory containing generated data"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (strict mode)"
    )

    args = parser.parse_args()

    # Run validation
    passed = validate_production_dataset(args.data_dir, args.strict)

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
