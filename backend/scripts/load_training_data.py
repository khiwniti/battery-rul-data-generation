#!/usr/bin/env python3
"""
Data Loader Script
Loads training data CSVs into PostgreSQL/TimescaleDB database
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Location, BatterySystem, String, Battery, User
from src.models.user import UserRole
from src.core.config import settings
from src.core.security import get_password_hash


async def load_data(data_dir: str = "output/training_dataset"):
    """
    Load training data from CSV files into database

    Args:
        data_dir: Directory containing CSV files
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        print(f"❌ Error: Data directory not found: {data_path}")
        print(f"   Please run data generation first:")
        print(f"   cd data-synthesis && python generate_battery_data.py")
        sys.exit(1)

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create async session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    print("=" * 80)
    print("BATTERY RUL PREDICTION - DATA LOADER")
    print("=" * 80)
    print(f"Data directory: {data_path}")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    print()

    async with async_session() as session:
        try:
            # Check if data already exists
            result = await session.execute(text("SELECT COUNT(*) FROM location"))
            location_count = result.scalar()

            if location_count > 0:
                print(f"⚠️  Warning: Database already contains {location_count} locations")
                response = input("Do you want to proceed? This will add more data (y/n): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return

            print("Phase 1: Loading Master Data")
            print("-" * 80)

            # Load locations
            print("📍 Loading locations...", end=" ", flush=True)
            locations_df = pd.read_csv(data_path / "location.csv")
            for _, row in locations_df.iterrows():
                location = Location(
                    location_id=row['location_id'],
                    name=row['name'],
                    region=row['region'],
                    city=row['city'],
                    country=row['country'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    temp_offset_c=row['temp_offset_c'],
                    humidity_offset_pct=row['humidity_offset_pct'],
                    power_outage_frequency_per_year=row['power_outage_frequency_per_year'],
                )
                session.add(location)
            await session.commit()
            print(f"✅ {len(locations_df)} locations")

            # Load battery systems
            print("🔌 Loading battery systems...", end=" ", flush=True)
            systems_df = pd.read_csv(data_path / "battery_system.csv")
            for _, row in systems_df.iterrows():
                system = BatterySystem(
                    system_id=row['system_id'],
                    location_id=row['location_id'],
                    system_type=row['system_type'],
                    manufacturer=row['manufacturer'],
                    model=row['model'],
                    nominal_voltage_v=row['nominal_voltage_v'],
                    max_current_a=row['max_current_a'],
                    installed_date=datetime.fromisoformat(row['installed_date']).date(),
                )
                session.add(system)
            await session.commit()
            print(f"✅ {len(systems_df)} systems")

            # Load strings
            print("🔗 Loading battery strings...", end=" ", flush=True)
            strings_df = pd.read_csv(data_path / "string.csv")
            for _, row in strings_df.iterrows():
                string = String(
                    string_id=row['string_id'],
                    system_id=row['system_id'],
                    position=row['position'],
                    battery_count=row['battery_count'],
                )
                session.add(string)
            await session.commit()
            print(f"✅ {len(strings_df)} strings")

            # Load batteries
            print("🔋 Loading batteries...", end=" ", flush=True)
            batteries_df = pd.read_csv(data_path / "battery.csv")

            # Get string IDs mapping (string_id -> UUID)
            result = await session.execute(text("SELECT string_id, id FROM string"))
            string_id_map = {row[0]: row[1] for row in result}

            for _, row in batteries_df.iterrows():
                battery = Battery(
                    battery_id=row['battery_id'],
                    string_id=string_id_map[row['string_id']],
                    serial_number=row['serial_number'],
                    position=row['position'],
                    manufacturer=row['manufacturer'],
                    model=row['model'],
                    nominal_voltage_v=row['nominal_voltage_v'],
                    nominal_capacity_ah=row['nominal_capacity_ah'],
                    installed_date=datetime.fromisoformat(row['installed_date']).date(),
                    warranty_months=row['warranty_months'],
                )
                session.add(battery)
            await session.commit()
            print(f"✅ {len(batteries_df)} batteries")

            print()
            print("Phase 2: Loading Telemetry Data (This may take a while...)")
            print("-" * 80)

            # Load telemetry (if file exists and is not too large)
            telemetry_file = data_path / "telemetry_jar_calc.csv"
            if telemetry_file.exists():
                print("📊 Loading telemetry data...")
                print("   (This will take several minutes for large datasets)")

                # Use COPY for fast bulk insert
                import gzip
                import csv

                # Check if file is gzipped
                if telemetry_file.suffix == '.gz' or (data_path / "telemetry_jar_calc.csv.gz").exists():
                    telemetry_file = data_path / "telemetry_jar_calc.csv.gz"
                    print(f"   Reading compressed file: {telemetry_file.name}")

                # Use PostgreSQL COPY command for fast bulk insert
                # This requires the file to be accessible by PostgreSQL
                print("   ⚠️  Note: Telemetry loading via COPY is not yet implemented")
                print("   Please use psql COPY command for large datasets:")
                print(f"   \\COPY telemetry FROM '{telemetry_file}' CSV HEADER")
                print()
                print("   For now, skipping telemetry data to avoid long loading times.")
                print("   The database structure is ready for telemetry data.")

            print()
            print("=" * 80)
            print("✅ DATA LOADING COMPLETE!")
            print("=" * 80)
            print(f"Loaded:")
            print(f"  - {len(locations_df)} locations")
            print(f"  - {len(systems_df)} battery systems")
            print(f"  - {len(strings_df)} battery strings")
            print(f"  - {len(batteries_df)} batteries")
            print()
            print("Next steps:")
            print("  1. Create admin user: python scripts/create_admin.py")
            print("  2. Start backend: uvicorn src.main:app_with_sockets --reload")
            print("  3. Test API: http://localhost:8000/api/docs")
            print()

        except Exception as e:
            print(f"\n❌ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load training data into database")
    parser.add_argument(
        "--data-dir",
        default="output/training_dataset",
        help="Directory containing CSV files (default: output/training_dataset)",
    )

    args = parser.parse_args()

    asyncio.run(load_data(args.data_dir))
