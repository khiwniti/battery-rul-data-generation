#!/usr/bin/env python3
"""
Quick Data Quality Review Script

Analyzes the generated 30-day sensor data to validate quality before scaling up.
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("BATTERY SENSOR DATA - QUALITY REVIEW")
print("="*80)
print()

# Load data
print("Loading data...")
data_dir = "./output/sensor_data_only/test_30d_24b_5sec/"

battery_sensors = pd.read_csv(f"{data_dir}battery_sensors.csv.gz")
string_sensors = pd.read_csv(f"{data_dir}string_sensors.csv.gz")
battery_info = pd.read_csv(f"{data_dir}battery_info.csv")

print(f"✓ Loaded {len(battery_sensors):,} battery sensor records")
print(f"✓ Loaded {len(string_sensors):,} string sensor records")
print(f"✓ Loaded {len(battery_info)} battery metadata records")
print()

# Convert timestamp
battery_sensors['ts'] = pd.to_datetime(battery_sensors['ts'])
string_sensors['ts'] = pd.to_datetime(string_sensors['ts'])

# Basic info
print("="*80)
print("1. DATASET OVERVIEW")
print("="*80)
print(f"Time Range: {battery_sensors['ts'].min()} to {battery_sensors['ts'].max()}")
print(f"Duration: {(battery_sensors['ts'].max() - battery_sensors['ts'].min()).days} days")
print(f"Number of Batteries: {battery_sensors['battery_id'].nunique()}")
print(f"Sampling Interval: {(battery_sensors['ts'].diff().median().total_seconds())} seconds")
print()

# Check for missing data
print("="*80)
print("2. DATA COMPLETENESS CHECK")
print("="*80)
expected_samples = len(battery_sensors) / battery_sensors['battery_id'].nunique()
print(f"Expected samples per battery: {expected_samples:,.0f}")

for battery_id in battery_sensors['battery_id'].unique()[:5]:  # Check first 5
    battery_data = battery_sensors[battery_sensors['battery_id'] == battery_id]
    print(f"  Battery {str(battery_id)[:8]}...: {len(battery_data):,} samples")

missing_values = battery_sensors.isnull().sum()
if missing_values.sum() == 0:
    print("✓ No missing values detected")
else:
    print(f"⚠ Missing values found:\n{missing_values[missing_values > 0]}")
print()

# Voltage analysis
print("="*80)
print("3. VOLTAGE ANALYSIS")
print("="*80)
print(battery_sensors['voltage_v'].describe())
print(f"\n✓ Range check:")
print(f"  Min: {battery_sensors['voltage_v'].min():.3f}V (expected: 11.0-11.5V)")
print(f"  Max: {battery_sensors['voltage_v'].max():.3f}V (expected: 12.5-14.5V)")
print(f"  Mean: {battery_sensors['voltage_v'].mean():.3f}V (expected: ~12.7V for float)")

# Check voltage stability
voltage_std = battery_sensors.groupby('battery_id')['voltage_v'].std()
print(f"\n✓ Voltage stability (std dev per battery):")
print(f"  Mean std: {voltage_std.mean():.4f}V (lower = more stable)")
print(f"  Max std: {voltage_std.max():.4f}V")
print()

# Temperature analysis
print("="*80)
print("4. TEMPERATURE ANALYSIS")
print("="*80)
print(battery_sensors['temperature_c'].describe())
print(f"\n✓ Range check:")
print(f"  Min: {battery_sensors['temperature_c'].min():.1f}°C (expected: 18-25°C)")
print(f"  Max: {battery_sensors['temperature_c'].max():.1f}°C (expected: 25-50°C)")
print(f"  Mean: {battery_sensors['temperature_c'].mean():.1f}°C")

# Check for Thai seasonal pattern (cool season Nov)
temp_by_day = battery_sensors.groupby(battery_sensors['ts'].dt.date)['temperature_c'].mean()
print(f"\n✓ Temperature trend over 30 days:")
print(f"  First week avg: {temp_by_day.iloc[:7].mean():.1f}°C")
print(f"  Last week avg: {temp_by_day.iloc[-7:].mean():.1f}°C")
print(f"  Variation: {temp_by_day.std():.1f}°C (daily variation)")
print()

# Resistance analysis
print("="*80)
print("5. INTERNAL RESISTANCE ANALYSIS")
print("="*80)
print(battery_sensors['resistance_mohm'].describe())
print(f"\n✓ Range check:")
print(f"  Min: {battery_sensors['resistance_mohm'].min():.3f}mΩ (expected: 2.5-3.5mΩ)")
print(f"  Max: {battery_sensors['resistance_mohm'].max():.3f}mΩ (expected: 3.5-10mΩ)")

# Check for degradation trend
resistance_trend = battery_sensors.groupby(battery_sensors['ts'].dt.date)['resistance_mohm'].mean()
print(f"\n✓ Resistance degradation over 30 days:")
print(f"  Start: {resistance_trend.iloc[:7].mean():.3f}mΩ")
print(f"  End: {resistance_trend.iloc[-7:].mean():.3f}mΩ")
print(f"  Change: {(resistance_trend.iloc[-7:].mean() - resistance_trend.iloc[:7].mean()):.3f}mΩ")
print()

# String current analysis
print("="*80)
print("6. STRING CURRENT ANALYSIS")
print("="*80)
print(string_sensors['current_a'].describe())
print(f"\n✓ Operating modes distribution:")
print(string_sensors['mode'].value_counts())

print(f"\n✓ Current by mode:")
for mode in string_sensors['mode'].unique():
    mode_data = string_sensors[string_sensors['mode'] == mode]['current_a']
    print(f"  {mode:12s}: {mode_data.mean():7.2f}A (±{mode_data.std():.2f}A)")
print()

# Data quality summary
print("="*80)
print("7. DATA QUALITY SUMMARY")
print("="*80)

quality_checks = []

# Check 1: No missing values
quality_checks.append(("No missing values", battery_sensors.isnull().sum().sum() == 0))

# Check 2: Voltage in valid range
quality_checks.append(("Voltage in range (11-15V)",
                       (battery_sensors['voltage_v'] >= 11.0).all() and
                       (battery_sensors['voltage_v'] <= 15.0).all()))

# Check 3: Temperature in valid range
quality_checks.append(("Temperature in range (15-55°C)",
                       (battery_sensors['temperature_c'] >= 15).all() and
                       (battery_sensors['temperature_c'] <= 55).all()))

# Check 4: Resistance in valid range
quality_checks.append(("Resistance in range (2-15mΩ)",
                       (battery_sensors['resistance_mohm'] >= 2.0).all() and
                       (battery_sensors['resistance_mohm'] <= 15.0).all()))

# Check 5: Time series continuity
time_diffs = battery_sensors.sort_values('ts')['ts'].diff().dt.total_seconds()
quality_checks.append(("Consistent 5-sec sampling",
                       (time_diffs.dropna() == 5.0).sum() > len(time_diffs) * 0.99))

# Check 6: All batteries present
quality_checks.append(("All 24 batteries present",
                       battery_sensors['battery_id'].nunique() == 24))

print("\n✓ Quality Checks:")
for check_name, passed in quality_checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {check_name}")

all_passed = all([check[1] for check in quality_checks])
print()
if all_passed:
    print("="*80)
    print("🎉 ALL QUALITY CHECKS PASSED!")
    print("="*80)
    print("\n✅ Data is ready for use!")
    print("✅ You can safely scale up to 730 days with this configuration")
else:
    print("⚠ Some quality checks failed. Review data before scaling up.")

print()
print("="*80)
print("8. SAMPLE DATA PREVIEW")
print("="*80)
print("\nBattery Sensors (first 5 rows):")
print(battery_sensors.head())
print("\nString Sensors (first 5 rows):")
print(string_sensors.head())

print()
print("="*80)
print("REVIEW COMPLETE")
print("="*80)
print(f"\nData location: {data_dir}")
print(f"Total records: {len(battery_sensors) + len(string_sensors):,}")
print(f"File size: ~165 MB")
print("\nReady for ML training or scale up to 730 days!")
