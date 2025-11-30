#!/usr/bin/env python3
"""
Battery Sensor Data Generator - Raw Telemetry Only

Generates ONLY raw sensor readings:
- Battery voltage (V)
- Battery temperature (°C)
- Battery internal resistance (mΩ)
- String current (A)
- String voltage (V)
- Environmental temperature (°C)
- Environmental humidity (%)

NO calculated fields, NO ML features, NO predictions - just raw sensor data.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from master_data_generator import MasterDataGenerator
from thailand_environment import ThailandEnvironmentModel
from battery_degradation import BatteryDegradationModel
from telemetry_generator import TelemetryGenerator


def generate_sensor_data_only(
    duration_days: int,
    num_batteries: int,
    sampling_seconds: int,
    output_dir: str,
    seed: int = 42
):
    """Generate only raw sensor data."""

    print("="*80)
    print("BATTERY SENSOR DATA GENERATOR - RAW TELEMETRY ONLY")
    print("="*80)
    print(f"Duration: {duration_days} days")
    print(f"Batteries: {num_batteries}")
    print(f"Battery Sampling: {sampling_seconds} seconds")
    print(f"Expected Records: ~{num_batteries * (duration_days * 24 * 3600 / sampling_seconds):,.0f}")
    print(f"Output: {output_dir}")
    print("="*80)
    print()

    os.makedirs(output_dir, exist_ok=True)

    # Generate master data
    print("Step 1: Generating master data...")
    master_gen = MasterDataGenerator(seed=seed)
    master_data = master_gen.generate_all()

    # Limit batteries
    master_data['battery'] = master_data['battery'].head(num_batteries)
    battery_string_ids = master_data['battery']['string_id'].unique()
    master_data['string'] = master_data['string'][
        master_data['string']['string_id'].isin(battery_string_ids)
    ]
    string_system_ids = master_data['string']['system_id'].unique()
    master_data['battery_system'] = master_data['battery_system'][
        master_data['battery_system']['system_id'].isin(string_system_ids)
    ]

    print(f"  Fleet: {len(master_data['battery'])} batteries, "
          f"{len(master_data['string'])} strings")

    # Initialize battery models
    print("\nStep 2: Initializing battery degradation models...")
    battery_models = {}
    for _, battery in master_data['battery'].iterrows():
        battery_id = str(battery['battery_id'])
        model = BatteryDegradationModel(
            battery_id=battery_id,
            initial_capacity_ah=battery['initial_capacity_ah'],
            initial_resistance_mohm=battery['initial_resistance_mohm'],
            installed_date=battery['installed_date'],
            seed=seed + hash(battery_id) % 10000
        )
        battery_models[battery_id] = model

    print(f"  Initialized {len(battery_models)} battery models")

    # Generate power outages
    print("\nStep 3: Simulating power grid...")
    location = master_data['location'].iloc[0]
    env_model = ThailandEnvironmentModel(location['region'], seed=seed)

    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=duration_days)

    outages = env_model.generate_power_outage_events(start_date, end_date)
    print(f"  Generated {len(outages)} power outage events")

    # Generate telemetry (RAW SENSOR DATA ONLY)
    print("\nStep 4: Generating RAW SENSOR DATA...")
    print("  (This may take a while for large datasets)")

    system = master_data['battery_system'].iloc[0]
    strings = master_data['string'][
        master_data['string']['system_id'] == system['system_id']
    ]

    # Initialize telemetry generator
    tel_gen = TelemetryGenerator(
        battery_models=battery_models,
        string_info=strings,
        location_region=location['region'],
        system_type=system['system_type'],
        seed=seed
    )

    # Generate time series
    jar_df, string_df = tel_gen.generate_timeseries(
        start_date,
        end_date,
        sampling_interval_seconds=sampling_seconds,
        outage_events=outages
    )

    print("\n" + "="*80)
    print("SAVING SENSOR DATA...")
    print("="*80)

    # Save only RAW sensor data
    print("\n1. Battery Sensor Data (per battery):")
    jar_path = os.path.join(output_dir, "battery_sensors.csv.gz")
    jar_df.to_csv(jar_path, index=False, compression='gzip')
    print(f"   ✓ {len(jar_df):,} records saved to: battery_sensors.csv.gz")
    print(f"   Columns: ts, battery_id, voltage_v, temperature_c, resistance_mohm")

    print("\n2. String Sensor Data (per string):")
    string_path = os.path.join(output_dir, "string_sensors.csv.gz")
    string_df.to_csv(string_path, index=False, compression='gzip')
    print(f"   ✓ {len(string_df):,} records saved to: string_sensors.csv.gz")
    print(f"   Columns: ts, string_id, voltage_v, current_a, mode")

    print("\n3. Master Data (battery information):")
    battery_info_path = os.path.join(output_dir, "battery_info.csv")
    master_data['battery'].to_csv(battery_info_path, index=False)
    print(f"   ✓ {len(master_data['battery'])} batteries saved to: battery_info.csv")

    print("\n4. Location Info:")
    location_path = os.path.join(output_dir, "location_info.csv")
    master_data['location'].to_csv(location_path, index=False)
    print(f"   ✓ Location data saved to: location_info.csv")

    # Generate summary report
    print("\n5. Summary Report:")
    report_path = os.path.join(output_dir, "SENSOR_DATA_REPORT.md")
    with open(report_path, 'w') as f:
        f.write("# Battery Sensor Data - Generation Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Period**: {start_date} to {end_date}\n\n")
        f.write(f"**Duration**: {duration_days} days\n\n")
        f.write(f"**Sampling Rate**: Every {sampling_seconds} seconds\n\n")

        f.write("## Generated Files\n\n")
        f.write("### 1. battery_sensors.csv.gz\n")
        f.write(f"- **Records**: {len(jar_df):,}\n")
        f.write("- **Columns**:\n")
        f.write("  - `ts`: Timestamp\n")
        f.write("  - `battery_id`: Battery unique ID\n")
        f.write("  - `voltage_v`: Battery voltage (Volts)\n")
        f.write("  - `temperature_c`: Battery temperature (°C)\n")
        f.write("  - `resistance_mohm`: Internal resistance (milliohms)\n")
        f.write("  - `conductance_s`: Conductance (Siemens)\n\n")

        f.write("### 2. string_sensors.csv.gz\n")
        f.write(f"- **Records**: {len(string_df):,}\n")
        f.write("- **Columns**:\n")
        f.write("  - `ts`: Timestamp\n")
        f.write("  - `string_id`: String unique ID\n")
        f.write("  - `voltage_v`: String voltage (Volts)\n")
        f.write("  - `current_a`: String current (Amperes)\n")
        f.write("  - `mode`: Operating mode (float/boost/discharge/idle/equalize)\n")
        f.write("  - `ripple_voltage_rms_v`: AC ripple voltage (V RMS)\n")
        f.write("  - `ripple_current_rms_a`: AC ripple current (A RMS)\n\n")

        f.write("## Data Statistics\n\n")
        f.write(f"- **Batteries**: {num_batteries}\n")
        f.write(f"- **Strings**: {len(strings)}\n")
        f.write(f"- **Voltage Range**: {jar_df['voltage_v'].min():.2f}V - {jar_df['voltage_v'].max():.2f}V\n")
        f.write(f"- **Temperature Range**: {jar_df['temperature_c'].min():.1f}°C - {jar_df['temperature_c'].max():.1f}°C\n")
        f.write(f"- **Resistance Range**: {jar_df['resistance_mohm'].min():.2f}mΩ - {jar_df['resistance_mohm'].max():.2f}mΩ\n")
        f.write(f"- **Power Outages**: {len(outages)}\n")

    print(f"   ✓ Report saved to: SENSOR_DATA_REPORT.md")

    # Sample data preview
    print("\n" + "="*80)
    print("SAMPLE DATA PREVIEW")
    print("="*80)
    print("\nBattery Sensors (first 5 rows):")
    print(jar_df.head())
    print("\nString Sensors (first 5 rows):")
    print(string_df.head())

    print("\n" + "="*80)
    print("✓ SENSOR DATA GENERATION COMPLETE!")
    print("="*80)
    print(f"\nOutput directory: {output_dir}")
    print(f"Total files: 4")
    print(f"Total sensor records: {len(jar_df) + len(string_df):,}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate ONLY raw sensor data (no calculations, no ML features)"
    )
    parser.add_argument("--duration-days", type=int, default=7,
                       help="Simulation duration in days (default: 7)")
    parser.add_argument("--batteries", type=int, default=24,
                       help="Number of batteries (default: 24)")
    parser.add_argument("--sampling-seconds", type=int, default=5,
                       help="Battery sensor sampling interval in seconds (default: 5)")
    parser.add_argument("--env-sampling-seconds", type=int, default=60,
                       help="Environmental sensor sampling interval in seconds (default: 60)")
    parser.add_argument("--output-dir", type=str, default="./output/sensor_data",
                       help="Output directory (default: ./output/sensor_data)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed (default: 42)")

    args = parser.parse_args()

    print(f"NOTE: Battery sampling: {args.sampling_seconds}s, Environment sampling: {args.env_sampling_seconds}s\n")

    generate_sensor_data_only(
        duration_days=args.duration_days,
        num_batteries=args.batteries,
        sampling_seconds=args.sampling_seconds,
        output_dir=args.output_dir,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
