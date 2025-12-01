#!/usr/bin/env python3
"""
Convert CSV training data to Parquet format
Provides significant compression and faster loading for ML pipelines
"""
import sys
import pandas as pd
from pathlib import Path
import gzip

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.services.parquet_service import parquet_service
from src.core.logging import logger


def convert_csv_to_parquet(csv_dir: str, output_dir: str = "data/parquet"):
    """
    Convert all CSV files from data generator to Parquet format

    Args:
        csv_dir: Directory containing CSV files
        output_dir: Output directory for Parquet files
    """
    csv_path = Path(csv_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"❌ CSV directory not found: {csv_path}")
        return

    print(f"\n{'='*80}")
    print("CSV TO PARQUET CONVERSION")
    print(f"{'='*80}\n")
    print(f"Input directory: {csv_path}")
    print(f"Output directory: {output_path}\n")

    # Files to convert
    conversions = [
        # Master data (small files - keep as single Parquet)
        ("location.csv", "master/location.parquet"),
        ("battery_model.csv", "master/battery_model.parquet"),
        ("battery_system.csv", "master/battery_system.parquet"),
        ("string.csv", "master/string.parquet"),
        ("battery.csv", "master/battery.parquet"),
        ("environmental_sensor.csv", "master/environmental_sensor.parquet"),
        ("user.csv", "master/user.parquet"),
        ("ml_model.csv", "master/ml_model.parquet"),

        # Time-series data (large files - use compression)
        ("telemetry_jar_raw.csv.gz", "telemetry/raw_telemetry.parquet"),
        ("telemetry_jar_calc.csv", "telemetry/calc_telemetry.parquet"),
        ("telemetry_string_raw.csv.gz", "telemetry/string_raw.parquet"),
        ("telemetry_string_calc.csv", "telemetry/string_calc.parquet"),

        # ML data
        ("feature_store.csv", "ml/feature_store.parquet"),
        ("rul_prediction.csv", "ml/rul_predictions.parquet"),

        # Operational data
        ("alert.csv", "operational/alerts.parquet"),
        ("maintenance_event.csv", "operational/maintenance_events.parquet"),
        ("capacity_test_raw.csv", "operational/capacity_test_raw.parquet"),
        ("capacity_test_calc.csv", "operational/capacity_test_calc.parquet"),
        ("impedance_measurement_raw.csv", "operational/impedance_raw.parquet"),
        ("impedance_measurement_calc.csv", "operational/impedance_calc.parquet"),
    ]

    stats = {
        'files_converted': 0,
        'csv_total_size_mb': 0,
        'parquet_total_size_mb': 0,
        'compression_ratio': 0
    }

    for csv_file, parquet_file in conversions:
        csv_file_path = csv_path / csv_file
        parquet_file_path = output_path / parquet_file

        if not csv_file_path.exists():
            print(f"⏭️  Skipping {csv_file} (not found)")
            continue

        try:
            # Get original size
            csv_size_mb = csv_file_path.stat().st_size / (1024 * 1024)
            stats['csv_total_size_mb'] += csv_size_mb

            # Read CSV (handle gzip compression)
            if csv_file.endswith('.gz'):
                with gzip.open(csv_file_path, 'rt') as f:
                    df = pd.read_csv(f)
            else:
                df = pd.read_csv(csv_file_path)

            # Create output directory
            parquet_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert timestamp columns if present
            timestamp_columns = ['timestamp', 'triggered_at', 'resolved_at', 'acknowledged_at',
                               'scheduled_at', 'started_at', 'completed_at', 'created_at', 'updated_at']
            for col in timestamp_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Write to Parquet with Snappy compression
            df.to_parquet(parquet_file_path, compression='snappy', index=False)

            # Get Parquet size
            parquet_size_mb = parquet_file_path.stat().st_size / (1024 * 1024)
            stats['parquet_total_size_mb'] += parquet_size_mb

            compression = (1 - parquet_size_mb / csv_size_mb) * 100 if csv_size_mb > 0 else 0

            print(f"✅ {csv_file:<40} → {parquet_file}")
            print(f"   {len(df):,} rows | CSV: {csv_size_mb:.2f}MB → Parquet: {parquet_size_mb:.2f}MB ({compression:.1f}% smaller)")

            stats['files_converted'] += 1

        except Exception as e:
            print(f"❌ Error converting {csv_file}: {e}")
            continue

    # Calculate overall compression
    if stats['csv_total_size_mb'] > 0:
        stats['compression_ratio'] = (1 - stats['parquet_total_size_mb'] / stats['csv_total_size_mb']) * 100

    print(f"\n{'='*80}")
    print("CONVERSION SUMMARY")
    print(f"{'='*80}")
    print(f"Files converted: {stats['files_converted']}")
    print(f"Total CSV size: {stats['csv_total_size_mb']:.2f} MB")
    print(f"Total Parquet size: {stats['parquet_total_size_mb']:.2f} MB")
    print(f"Overall compression: {stats['compression_ratio']:.1f}% smaller")
    print(f"Storage saved: {stats['csv_total_size_mb'] - stats['parquet_total_size_mb']:.2f} MB\n")

    logger.info(
        "CSV to Parquet conversion complete",
        **stats
    )

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert CSV data to Parquet format")
    parser.add_argument(
        "--csv-dir",
        default="../data-synthesis/output/sample_2day",
        help="Directory containing CSV files"
    )
    parser.add_argument(
        "--output-dir",
        default="data/parquet",
        help="Output directory for Parquet files"
    )

    args = parser.parse_args()

    convert_csv_to_parquet(args.csv_dir, args.output_dir)
