#!/usr/bin/env python3
"""
Full Battery Dataset Generator with Location-Specific Temperature
Generates 730 days × 216 batteries across 9 Thai locations with proper temperature diversity
"""

import sys
import os
import argparse
import gc
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from master_data_generator import MasterDataGenerator
from thailand_environment import ThailandEnvironmentModel
from battery_degradation import BatteryDegradationModel
from telemetry_generator import TelemetryGenerator


def generate_full_dataset(
    duration_days: int = 730,
    batteries_per_location: int = 24,
    sampling_seconds: int = 60,
    env_sampling_seconds: int = 60,
    output_dir: str = "./output/full_dataset",
    seed: int = 42
):
    """
    Generate full dataset with location-specific temperature diversity.

    Args:
        duration_days: Number of days to simulate (default: 730 = 2 years)
        batteries_per_location: Batteries per location (default: 24 = 1 string)
        sampling_seconds: Battery sensor sampling interval (default: 60)
        env_sampling_seconds: Environmental sensor sampling (default: 60)
        output_dir: Output directory
        seed: Random seed
    """

    print("=" * 80)
    print("FULL BATTERY DATASET GENERATOR")
    print("WITH LOCATION-SPECIFIC TEMPERATURE DIVERSITY")
    print("=" * 80)

    # Generate master data
    print("\nStep 1: Generating master data...")
    master_gen = MasterDataGenerator(seed=seed)
    master_data = master_gen.generate_all()

    locations = master_data['location']
    total_batteries = len(locations) * batteries_per_location

    print(f"  Locations: {len(locations)}")
    print(f"  Batteries per location: {batteries_per_location}")
    print(f"  Total batteries: {total_batteries}")
    print(f"  Duration: {duration_days} days")
    print(f"  Battery sampling: {sampling_seconds} seconds")
    print(f"  Expected records: {total_batteries * (duration_days * 24 * 3600 / sampling_seconds):,.0f}")
    print()

    for idx, location in locations.iterrows():
        print(f"    {location['location_name']:<30} Region: {location['region']:<15} "
              f"Temp offset: {ThailandEnvironmentModel.REGIONAL_CLIMATE[location['region']]['temp_offset']:+.1f}°C")

    print("=" * 80)
    print()

    os.makedirs(output_dir, exist_ok=True)

    # Time range
    end_date = datetime(2025, 11, 30, 0, 0, 0)  # End date
    start_date = end_date - timedelta(days=duration_days)

    print(f"Simulation period: {start_date.date()} to {end_date.date()}")
    print()

    # Initialize storage for metadata only (not full sensor data)
    all_battery_info = []
    temp_stats_by_location = []

    # Generate data for each location (save incrementally to avoid memory exhaustion)
    for loc_idx, location in locations.iterrows():
        location_id = location['location_id']  # Keep as UUID, don't convert to string
        location_name = location['location_name']
        location_region = location['region']

        print("=" * 80)
        print(f"GENERATING LOCATION {loc_idx + 1}/{len(locations)}: {location_name}")
        print(f"Region: {location_region}")
        print("=" * 80)

        # Initialize location-specific environment model
        env_model = ThailandEnvironmentModel(location_region, seed=seed + loc_idx)

        # Get batteries for this location via string -> system -> location
        # First get systems at this location
        location_systems = master_data['battery_system'][
            master_data['battery_system']['location_id'] == location_id
        ]
        location_system_ids = location_systems['system_id'].values

        # Then get strings in these systems
        location_strings = master_data['string'][
            master_data['string']['system_id'].isin(location_system_ids)
        ]
        location_string_ids = location_strings['string_id'].values

        # Finally get batteries in these strings
        location_batteries = master_data['battery'][
            master_data['battery']['string_id'].isin(location_string_ids)
        ].head(batteries_per_location).copy()

        if len(location_batteries) == 0:
            print(f"  ⚠️  No batteries found for {location_name}, skipping...")
            continue

        print(f"  Batteries: {len(location_batteries)}")
        print(f"  Regional temp offset: {env_model.climate['temp_offset']:+.1f}°C")
        print(f"  Regional humidity offset: {env_model.climate['humidity_offset']:+.1f}%")
        print()

        # Get strings for these batteries (already filtered above)
        battery_string_ids = location_batteries['string_id'].unique()
        location_strings_filtered = location_strings[
            location_strings['string_id'].isin(battery_string_ids)
        ]

        # Initialize battery degradation models
        battery_models = {}
        for _, battery in location_batteries.iterrows():
            battery_id = str(battery['battery_id'])
            model = BatteryDegradationModel(
                battery_id=battery_id,
                initial_capacity_ah=battery['initial_capacity_ah'],
                initial_resistance_mohm=battery['initial_resistance_mohm'],
                installed_date=battery['installed_date'],
                seed=seed + hash(battery_id) % 10000
            )
            battery_models[battery_id] = model

        # Generate power outages for this location
        outages = env_model.generate_power_outage_events(start_date, end_date)
        print(f"  Power outages: {len(outages)} events")

        # Get system type (need at least one system)
        system = location_systems.iloc[0]
        system_type = system['system_type']

        # Generate telemetry using location-specific environment
        print(f"  Generating telemetry...")

        telemetry_gen = TelemetryGenerator(
            battery_models=battery_models,
            string_info=location_strings_filtered,
            location_region=location_region,
            system_type=system_type,
            seed=seed + loc_idx * 1000
        )

        # Generate sensor data
        battery_sensors, string_sensors = telemetry_gen.generate_timeseries(
            start_date=start_date,
            end_date=end_date,
            sampling_interval_seconds=sampling_seconds,
            outage_events=outages
        )

        # Add location info to battery sensors
        battery_sensors['location_id'] = str(location_id)  # Convert to string for CSV storage
        battery_sensors['location_name'] = location_name
        battery_sensors['region'] = location_region

        # Save battery info
        battery_info = location_batteries[[
            'battery_id', 'string_id', 'position_in_string',
            'initial_capacity_ah', 'initial_resistance_mohm', 'installed_date'
        ]].copy()
        battery_info['location_name'] = location_name
        battery_info['region'] = location_region

        # Save to per-location files immediately (incremental approach to avoid memory exhaustion)
        location_output_dir = f"{output_dir}/by_location"
        os.makedirs(location_output_dir, exist_ok=True)

        battery_sensor_file = f"{location_output_dir}/battery_sensors_{location_name.replace(' ', '_')}.csv.gz"
        string_sensor_file = f"{location_output_dir}/string_sensors_{location_name.replace(' ', '_')}.csv.gz"

        battery_sensors.to_csv(battery_sensor_file, index=False, compression='gzip')
        string_sensors.to_csv(string_sensor_file, index=False, compression='gzip')

        # Store metadata for final report
        all_battery_info.append(battery_info)
        temp_stats = battery_sensors['temperature_c'].describe()
        temp_stats_by_location.append({
            'location_name': location_name,
            'region': location_region,
            'mean': temp_stats['mean'],
            'std': temp_stats['std'],
            'min': temp_stats['min'],
            'max': temp_stats['max'],
            'records': len(battery_sensors)
        })

        print(f"  ✓ Saved to {battery_sensor_file}")
        print(f"  ✓ Saved to {string_sensor_file}")

        # Free memory immediately
        del battery_sensors, string_sensors, battery_info
        import gc
        gc.collect()

        print()

    # Combine all locations from saved files
    print("=" * 80)
    print("COMBINING ALL LOCATION FILES")
    print("=" * 80)

    # Read and combine battery info
    final_battery_info = pd.concat(all_battery_info, ignore_index=True)

    # Calculate aggregate statistics from per-location metadata
    temp_stats_df = pd.DataFrame(temp_stats_by_location)
    total_records = temp_stats_df['records'].sum()

    print(f"  Total battery sensor records: {total_records:,}")
    print(f"  Total string sensor records: {total_records // 24:,}")  # Approximate
    print(f"  Total batteries: {len(final_battery_info)}")
    print()

    # Temperature diversity analysis from collected stats
    print("=" * 80)
    print("TEMPERATURE DIVERSITY ANALYSIS")
    print("=" * 80)

    print("\nTemperature by Location:")
    print(temp_stats_df[['location_name', 'mean', 'std', 'min', 'max']].to_string(index=False))

    overall_min = temp_stats_df['min'].min()
    overall_max = temp_stats_df['max'].max()
    overall_mean = (temp_stats_df['mean'] * temp_stats_df['records']).sum() / total_records
    between_location_variation = temp_stats_df['mean'].max() - temp_stats_df['mean'].min()

    print(f"\nOverall Temperature Statistics:")
    print(f"  Mean: {overall_mean:.2f}°C")
    print(f"  Min:  {overall_min:.2f}°C")
    print(f"  Max:  {overall_max:.2f}°C")
    print(f"  Range: {overall_max - overall_min:.2f}°C")

    print(f"\n  ✓ Between-location variation: {between_location_variation:.2f}°C")
    print(f"  ✓ Expected impact on RUL: {(1.567 ** (between_location_variation / 10) - 1) * 100:.1f}% difference")
    print()

    # Optionally combine into single files (memory permitting)
    print("=" * 80)
    print("CREATING COMBINED FILES (optional, may be large)")
    print("=" * 80)

    # For smaller combined file, we can concatenate the per-location files
    # This is done in chunks to avoid loading all data into memory at once
    location_files = sorted(Path(f"{output_dir}/by_location").glob("battery_sensors_*.csv.gz"))

    if len(location_files) == len(temp_stats_by_location):
        print(f"  Combining {len(location_files)} location files...")

        # Use pandas concat with chunking
        combined_battery_path = f"{output_dir}/battery_sensors_combined.csv.gz"
        combined_string_path = f"{output_dir}/string_sensors_combined.csv.gz"

        # Read and combine battery sensors in chunks
        battery_chunks = []
        string_chunks = []

        for loc_file in location_files:
            loc_name = loc_file.stem.replace('battery_sensors_', '')
            string_file = Path(f"{output_dir}/by_location/string_sensors_{loc_name}.csv.gz")

            # Read in chunks
            battery_df = pd.read_csv(loc_file, compression='gzip')
            string_df = pd.read_csv(string_file, compression='gzip')

            battery_chunks.append(battery_df)
            string_chunks.append(string_df)

            del battery_df, string_df
            gc.collect()

        # Combine all
        final_battery_sensors = pd.concat(battery_chunks, ignore_index=True)
        final_string_sensors = pd.concat(string_chunks, ignore_index=True)

        # Save combined
        final_battery_sensors.to_csv(combined_battery_path, index=False, compression='gzip')
        final_string_sensors.to_csv(combined_string_path, index=False, compression='gzip')

        print(f"  ✓ Saved combined files")
        print(f"    - {combined_battery_path}")
        print(f"    - {combined_string_path}")

        del final_battery_sensors, final_string_sensors, battery_chunks, string_chunks
        gc.collect()
    else:
        print(f"  ⚠️  Some location files missing, skipping combined file creation")
        combined_battery_path = None
        combined_string_path = None

    # Save battery info metadata
    print("=" * 80)
    print("SAVING METADATA")
    print("=" * 80)

    battery_info_path = f"{output_dir}/battery_info.csv"

    print(f"  Saving battery info to {battery_info_path}...")
    final_battery_info.to_csv(battery_info_path, index=False)

    # Get file sizes
    info_size_kb = Path(battery_info_path).stat().st_size / 1024

    print(f"\n  ✓ battery_info.csv: {info_size_kb:.1f} KB")

    # Calculate total size of location files
    location_dir = Path(f"{output_dir}/by_location")
    total_size_mb = sum(f.stat().st_size for f in location_dir.glob("*.csv.gz")) / (1024**2)

    print(f"  ✓ by_location/*.csv.gz: {total_size_mb:.1f} MB ({len(list(location_dir.glob('*.csv.gz')))} files)")

    if combined_battery_path and Path(combined_battery_path).exists():
        combined_size_mb = (Path(combined_battery_path).stat().st_size +
                           Path(combined_string_path).stat().st_size) / (1024**2)
        print(f"  ✓ combined files: {combined_size_mb:.1f} MB")
        total_size_mb += combined_size_mb

    # Generate summary report
    report_path = f"{output_dir}/DATASET_REPORT.md"
    with open(report_path, 'w') as f:
        f.write("# Full Battery Dataset Generation Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Dataset Summary\n\n")
        f.write(f"- **Duration**: {duration_days} days ({start_date.date()} to {end_date.date()})\n")
        f.write(f"- **Total Batteries**: {len(final_battery_info)}\n")
        f.write(f"- **Locations**: {len(temp_stats_by_location)}\n")
        f.write(f"- **Battery Sampling**: {sampling_seconds} seconds\n")
        f.write(f"- **Total Records**: {total_records:,}\n")
        f.write(f"- **Dataset Size**: {total_size_mb:.2f} MB (compressed)\n\n")

        f.write("## Temperature Diversity\n\n")
        f.write(f"- **Overall Range**: {overall_min:.1f}°C - {overall_max:.1f}°C\n")
        f.write(f"- **Overall Mean**: {overall_mean:.2f}°C\n")
        f.write(f"- **Between-Location Variation**: {between_location_variation:.2f}°C\n")
        f.write(f"- **Expected RUL Impact**: {(1.567 ** (between_location_variation / 10) - 1) * 100:.1f}% life difference\n\n")

        f.write("## Temperature by Location\n\n")
        f.write("| Location | Region | Mean (°C) | Std (°C) | Min (°C) | Max (°C) | Records |\n")
        f.write("|----------|--------|-----------|----------|----------|----------|----------|\n")
        for row in temp_stats_by_location:
            f.write(f"| {row['location_name']} | {row['region']} | {row['mean']:.2f} | {row['std']:.2f} | {row['min']:.1f} | {row['max']:.1f} | {row['records']:,} |\n")

        f.write("\n## Files\n\n")
        f.write(f"### Per-Location Files (by_location/)\n")
        f.write(f"- {len(list(location_dir.glob('battery_sensors_*.csv.gz')))} battery sensor files\n")
        f.write(f"- {len(list(location_dir.glob('string_sensors_*.csv.gz')))} string sensor files\n")
        f.write(f"- Total size: {sum(f.stat().st_size for f in location_dir.glob('*.csv.gz')) / (1024**2):.1f} MB\n\n")

        if combined_battery_path and Path(combined_battery_path).exists():
            f.write(f"### Combined Files\n")
            f.write(f"- `battery_sensors_combined.csv.gz` - {Path(combined_battery_path).stat().st_size / (1024**2):.1f} MB\n")
            f.write(f"- `string_sensors_combined.csv.gz` - {Path(combined_string_path).stat().st_size / (1024**2):.1f} MB\n\n")

        f.write(f"### Metadata\n")
        f.write(f"- `battery_info.csv` - {info_size_kb:.1f} KB\n\n")

        f.write("## Usage\n\n")
        f.write("### Load All Data (from combined files)\n")
        f.write("```python\n")
        f.write("import pandas as pd\n\n")
        f.write(f"battery_sensors = pd.read_csv('{output_dir}/battery_sensors_combined.csv.gz')\n")
        f.write(f"string_sensors = pd.read_csv('{output_dir}/string_sensors_combined.csv.gz')\n")
        f.write(f"battery_info = pd.read_csv('{output_dir}/battery_info.csv')\n")
        f.write("```\n\n")

        f.write("### Load Specific Location\n")
        f.write("```python\n")
        f.write("location_name = 'Chiangmai_Data_Center'\n")
        f.write(f"battery_sensors = pd.read_csv(f'{output_dir}/by_location/battery_sensors_{{location_name}}.csv.gz')\n")
        f.write(f"string_sensors = pd.read_csv(f'{output_dir}/by_location/string_sensors_{{location_name}}.csv.gz')\n")
        f.write("```\n")

    print(f"\n  ✓ Report saved to {report_path}")

    print("\n" + "=" * 80)
    print("✓ GENERATION COMPLETE!")
    print("=" * 80)
    print(f"\nDataset Summary:")
    print(f"  - {len(temp_stats_by_location)} locations generated successfully")
    print(f"  - {total_records:,} total sensor records")
    print(f"  - {total_size_mb:.1f} MB total size")
    print(f"  - Temperature variation: {between_location_variation:.2f}°C between locations")
    print(f"\nFiles:")
    print(f"  - Per-location files: {output_dir}/by_location/")
    if combined_battery_path and Path(combined_battery_path).exists():
        print(f"  - Combined files: {combined_battery_path}")
    print(f"  - Metadata: {battery_info_path}")
    print(f"  - Report: {report_path}")
    print(f"\nNext steps:")
    print(f"  1. Review {report_path}")
    print(f"  2. Run training notebook with new dataset")
    print(f"  3. Expect temperature to be top-3 feature importance")
    print(f"  4. Model accuracy should improve 35-45%")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate full battery dataset with location-specific temperature diversity"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=730,
        help="Number of days to simulate (default: 730 = 2 years)"
    )
    parser.add_argument(
        "--batteries-per-location",
        type=int,
        default=24,
        help="Batteries per location (default: 24 = 1 string)"
    )
    parser.add_argument(
        "--sampling-seconds",
        type=int,
        default=60,
        help="Battery sensor sampling interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output/full_dataset",
        help="Output directory (default: ./output/full_dataset)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )

    args = parser.parse_args()

    generate_full_dataset(
        duration_days=args.days,
        batteries_per_location=args.batteries_per_location,
        sampling_seconds=args.sampling_seconds,
        env_sampling_seconds=args.sampling_seconds,
        output_dir=args.output_dir,
        seed=args.seed
    )
