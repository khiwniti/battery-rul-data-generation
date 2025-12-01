#!/usr/bin/env python3
"""
Load data from Parquet files to PostgreSQL database
Hybrid architecture: Master data + sample telemetry in PostgreSQL
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import AsyncSessionLocal
from src.core.config import settings
from src.models.location import Location
from src.models.battery_system import BatterySystem
from src.models.string import String
from src.models.battery import Battery
from src.models.telemetry import Telemetry
from src.models.alert import Alert, AlertType, AlertSeverity
from sqlalchemy import select


async def load_master_data(parquet_dir: str = "data/parquet"):
    """Load master data from Parquet to PostgreSQL"""

    parquet_path = Path(parquet_dir)
    master_path = parquet_path / "master"

    if not master_path.exists():
        print(f"❌ Master data path not found: {master_path}")
        return

    print(f"\n{'='*80}")
    print("LOADING MASTER DATA FROM PARQUET TO POSTGRESQL")
    print(f"{'='*80}\n")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    print(f"Source: {master_path}\n")

    async with AsyncSessionLocal() as session:
        stats = {'loaded': 0, 'skipped': 0, 'errors': 0}

        # 1. Load Locations
        print("📍 Loading locations...")
        location_file = master_path / "location.parquet"
        if location_file.exists():
            df = pd.read_parquet(location_file)
            for _, row in df.iterrows():
                try:
                    # Check if exists
                    result = await session.execute(
                        select(Location).where(Location.location_id == row['location_id'])
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        location = Location(
                            location_id=row['location_id'],
                            name=row['location_name'],
                            region=row['region'],
                            city=row['city'],
                            latitude=row['latitude'],
                            longitude=row['longitude']
                        )
                        session.add(location)
                        stats['loaded'] += 1
                    else:
                        stats['skipped'] += 1

                except Exception as e:
                    print(f"   ❌ Error loading location {row.get('location_id', 'unknown')}: {e}")
                    stats['errors'] += 1

            await session.commit()
            print(f"   ✅ Loaded: {stats['loaded']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        # Reset stats
        stats = {'loaded': 0, 'skipped': 0, 'errors': 0}

        # 2. Load Battery Systems
        print("\n🔋 Loading battery systems...")
        system_file = master_path / "battery_system.parquet"
        if system_file.exists():
            df = pd.read_parquet(system_file)
            for _, row in df.iterrows():
                try:
                    result = await session.execute(
                        select(BatterySystem).where(BatterySystem.system_id == row['system_id'])
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        system = BatterySystem(
                            system_id=row['system_id'],
                            location_id=row['location_id'],
                            system_name=row['system_name'],
                            system_type=row['system_type'],
                            capacity_kva=row.get('capacity_kva'),
                            voltage_v=row.get('voltage_v'),
                            commissioned_date=row.get('commissioned_date')
                        )
                        session.add(system)
                        stats['loaded'] += 1
                    else:
                        stats['skipped'] += 1

                except Exception as e:
                    print(f"   ❌ Error loading system {row.get('system_id', 'unknown')}: {e}")
                    stats['errors'] += 1

            await session.commit()
            print(f"   ✅ Loaded: {stats['loaded']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        # Reset stats
        stats = {'loaded': 0, 'skipped': 0, 'errors': 0}

        # 3. Load Strings
        print("\n🔗 Loading strings...")
        string_file = master_path / "string.parquet"
        if string_file.exists():
            df = pd.read_parquet(string_file)
            for _, row in df.iterrows():
                try:
                    result = await session.execute(
                        select(String).where(String.string_id == row['string_id'])
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        string = String(
                            string_id=row['string_id'],
                            system_id=row['system_id'],
                            string_name=row['string_name'],
                            battery_count=row.get('battery_count', 24),
                            total_voltage_v=row.get('total_voltage_v')
                        )
                        session.add(string)
                        stats['loaded'] += 1
                    else:
                        stats['skipped'] += 1

                except Exception as e:
                    print(f"   ❌ Error loading string {row.get('string_id', 'unknown')}: {e}")
                    stats['errors'] += 1

            await session.commit()
            print(f"   ✅ Loaded: {stats['loaded']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        # Reset stats
        stats = {'loaded': 0, 'skipped': 0, 'errors': 0}

        # 4. Load Batteries
        print("\n🔋 Loading batteries...")
        battery_file = master_path / "battery.parquet"
        if battery_file.exists():
            df = pd.read_parquet(battery_file)
            for _, row in df.iterrows():
                try:
                    result = await session.execute(
                        select(Battery).where(Battery.battery_id == row['battery_id'])
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        battery = Battery(
                            battery_id=row['battery_id'],
                            string_id=row['string_id'],
                            battery_code=row.get('battery_code'),
                            serial_number=row.get('serial_number'),
                            position_in_string=row.get('position_in_string'),
                            manufacture_date=row.get('manufacture_date'),
                            installed_date=row.get('installed_date')
                        )
                        session.add(battery)
                        stats['loaded'] += 1
                    else:
                        stats['skipped'] += 1

                except Exception as e:
                    print(f"   ❌ Error loading battery {row.get('battery_id', 'unknown')}: {e}")
                    stats['errors'] += 1

            await session.commit()
            print(f"   ✅ Loaded: {stats['loaded']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

        print(f"\n{'='*80}")
        print("MASTER DATA LOADING COMPLETE")
        print(f"{'='*80}\n")


async def load_telemetry_sample(parquet_dir: str = "data/parquet", limit: int = 1000):
    """Load sample telemetry data for API testing"""

    parquet_path = Path(parquet_dir)
    telemetry_file = parquet_path / "telemetry" / "raw_telemetry.parquet"

    if not telemetry_file.exists():
        print(f"❌ Telemetry file not found: {telemetry_file}")
        return

    print(f"\n{'='*80}")
    print(f"LOADING SAMPLE TELEMETRY (limit: {limit} records)")
    print(f"{'='*80}\n")

    df = pd.read_parquet(telemetry_file)
    print(f"Total records in Parquet: {len(df):,}")

    # Take sample
    df_sample = df.head(limit)

    async with AsyncSessionLocal() as session:
        stats = {'loaded': 0, 'skipped': 0, 'errors': 0}

        for _, row in df_sample.iterrows():
            try:
                # Parse timestamp
                timestamp = pd.to_datetime(row['ts'])

                telemetry = Telemetry(
                    battery_id=row['battery_id'],
                    timestamp=timestamp,
                    voltage_v=row['voltage_v'],
                    temperature_c=row['temperature_c'],
                    internal_resistance_mohm=row['resistance_mohm']
                )
                session.add(telemetry)
                stats['loaded'] += 1

                # Commit in batches
                if stats['loaded'] % 100 == 0:
                    await session.commit()
                    print(f"   📊 Progress: {stats['loaded']}/{limit} records...")

            except Exception as e:
                stats['errors'] += 1
                if stats['errors'] <= 5:  # Show first 5 errors only
                    print(f"   ❌ Error: {e}")

        await session.commit()
        print(f"\n   ✅ Loaded: {stats['loaded']:,}, Errors: {stats['errors']}")

    print(f"\n{'='*80}")
    print("TELEMETRY LOADING COMPLETE")
    print(f"{'='*80}\n")


async def load_alerts_sample(parquet_dir: str = "data/parquet", limit: int = 50):
    """Load sample alerts for testing"""

    parquet_path = Path(parquet_dir)
    alert_file = parquet_path / "operational" / "alerts.parquet"

    if not alert_file.exists():
        print(f"❌ Alert file not found: {alert_file}")
        return

    print(f"\n{'='*80}")
    print(f"LOADING SAMPLE ALERTS (limit: {limit} records)")
    print(f"{'='*80}\n")

    df = pd.read_parquet(alert_file)
    print(f"Total alerts in Parquet: {len(df):,}")

    # Take sample of unresolved alerts
    df_sample = df[df['resolved_at'].isna()].head(limit)

    async with AsyncSessionLocal() as session:
        stats = {'loaded': 0, 'skipped': 0, 'errors': 0}

        for _, row in df_sample.iterrows():
            try:
                alert = Alert(
                    alert_id=row['alert_id'],
                    battery_id=row['battery_id'],
                    alert_type=AlertType(row['alert_type']),
                    severity=AlertSeverity(row['severity']),
                    message=row['message'],
                    triggered_at=pd.to_datetime(row['triggered_at']),
                    is_acknowledged=False
                )
                session.add(alert)
                stats['loaded'] += 1

            except Exception as e:
                stats['errors'] += 1
                if stats['errors'] <= 5:
                    print(f"   ❌ Error: {e}")

        await session.commit()
        print(f"\n   ✅ Loaded: {stats['loaded']}, Errors: {stats['errors']}")

    print(f"\n{'='*80}")
    print("ALERTS LOADING COMPLETE")
    print(f"{'='*80}\n")


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Load data from Parquet to PostgreSQL")
    parser.add_argument("--parquet-dir", default="data/parquet", help="Parquet directory")
    parser.add_argument("--telemetry-limit", type=int, default=1000, help="Number of telemetry records to load")
    parser.add_argument("--alert-limit", type=int, default=50, help="Number of alerts to load")
    parser.add_argument("--master-only", action="store_true", help="Load master data only")

    args = parser.parse_args()

    # Load master data
    await load_master_data(args.parquet_dir)

    if not args.master_only:
        # Load sample telemetry
        await load_telemetry_sample(args.parquet_dir, args.telemetry_limit)

        # Load sample alerts
        await load_alerts_sample(args.parquet_dir, args.alert_limit)

    print("\n✅ ALL DATA LOADING COMPLETE!\n")
    print("Next steps:")
    print("1. Test API: curl http://localhost:8000/api/v1/locations")
    print("2. Test batteries: curl http://localhost:8000/api/v1/batteries")
    print("3. View API docs: http://localhost:8000/api/docs\n")


if __name__ == "__main__":
    asyncio.run(main())
