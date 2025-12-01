# Data Loading Guide - Railway PostgreSQL

## 📊 Dataset Overview

**Available**: 247 million records (3.3 GB compressed)
**Location**: `battery-rul-data-generation/output/production_2years/by_location/`
**Format**: CSV (gzip compressed)
**Ready**: ✅ Complete and validated

---

## 🎯 Loading Options

### Option 1: Direct PostgreSQL COPY (Fastest)
**Time**: ~30-60 minutes
**Complexity**: Medium
**Recommended for**: Production deployment

### Option 2: Backend API Bulk Upload (Safest)
**Time**: ~2-4 hours
**Complexity**: Low
**Recommended for**: First-time loading with validation

### Option 3: Python Script with SQLAlchemy (Flexible)
**Time**: ~1-2 hours
**Complexity**: Medium
**Recommended for**: Custom transformations

---

## 🚀 Option 1: Direct PostgreSQL COPY (Recommended)

### Step 1: Connect to Railway PostgreSQL

```bash
# Get database URL from Railway
railway variables --service backend | grep DATABASE_URL

# Or get connection details
railway run --service backend env | grep DATABASE
```

### Step 2: Prepare COPY Script

Create `load_data.sql`:

```sql
-- Create temporary staging table
CREATE TEMP TABLE telemetry_staging (
    ts TIMESTAMP,
    battery_id VARCHAR(50),
    voltage_v FLOAT,
    temperature_c FLOAT,
    resistance_mohm FLOAT,
    conductance_s FLOAT,
    location_id VARCHAR(50),
    location_name VARCHAR(100),
    region VARCHAR(50)
);

-- Load data from CSV (one location at a time)
\COPY telemetry_staging FROM PROGRAM 'zcat /path/to/battery_sensors_Bangrak_Data_Center.csv.gz' CSV HEADER;

-- Insert into main telemetry table
INSERT INTO telemetry (battery_id, timestamp, voltage, temperature, internal_resistance)
SELECT
    battery_id,
    ts,
    voltage_v,
    temperature_c,
    resistance_mohm
FROM telemetry_staging
ON CONFLICT (battery_id, timestamp) DO NOTHING;

-- Clean up
TRUNCATE telemetry_staging;
```

### Step 3: Execute for All Locations

```bash
# Load each location
for location in Bangrak Chiangmai HatYai KhonKaen Nonthaburi Phrakhanong Phuket Sriracha SuratThani; do
    echo "Loading $location..."
    psql $DATABASE_URL -c "\COPY telemetry_staging FROM PROGRAM 'zcat battery_sensors_${location}_Data_Center.csv.gz' CSV HEADER;"
    psql $DATABASE_URL -c "INSERT INTO telemetry SELECT * FROM telemetry_staging ON CONFLICT DO NOTHING;"
    psql $DATABASE_URL -c "TRUNCATE telemetry_staging;"
done
```

---

## 🔧 Option 2: Backend API Bulk Upload

### Step 1: Create Upload Script

Create `upload_data.py`:

```python
import pandas as pd
import requests
import gzip
from tqdm import tqdm

API_URL = "https://backend-production-6266.up.railway.app/api/v1"
TOKEN = "your_admin_jwt_token"  # Get from /auth/login

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def upload_location(file_path, batch_size=10000):
    """Upload data from one location file"""
    print(f"Loading {file_path}...")

    # Read compressed CSV
    df = pd.read_csv(file_path, compression='gzip')

    # Convert to API format
    total_batches = len(df) // batch_size + 1

    for i in tqdm(range(0, len(df), batch_size), total=total_batches):
        batch = df.iloc[i:i+batch_size]

        records = []
        for _, row in batch.iterrows():
            records.append({
                "battery_id": row['battery_id'],
                "timestamp": row['ts'],
                "voltage": float(row['voltage_v']),
                "temperature": float(row['temperature_c']),
                "internal_resistance": float(row['resistance_mohm'])
            })

        # Upload batch
        try:
            response = requests.post(
                f"{API_URL}/telemetry/bulk",
                headers=headers,
                json={"records": records}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Error uploading batch {i}: {e}")
            continue

    print(f"Completed {file_path}")

# Upload all locations
locations = [
    "Bangrak", "Chiangmai", "HatYai", "KhonKaen",
    "Nonthaburi", "Phrakhanong", "Phuket", "Sriracha", "SuratThani"
]

for location in locations:
    file_path = f"output/production_2years/by_location/battery_sensors_{location}_Data_Center.csv.gz"
    upload_location(file_path)
```

### Step 2: Get Admin Token

```bash
curl -X POST https://backend-production-6266.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'

# Copy the access_token from response
```

### Step 3: Run Upload

```bash
cd battery-rul-data-generation
python upload_data.py
```

---

## 🐍 Option 3: Python Script with SQLAlchemy

### Step 1: Create Loading Script

Create `load_to_db.py`:

```python
import pandas as pd
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

DATABASE_URL = "postgresql+asyncpg://user:pass@host:port/db"  # From Railway

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def load_location(file_path, batch_size=10000):
    """Load data from one location file"""
    print(f"Loading {file_path}...")

    # Read compressed CSV in chunks
    chunks = pd.read_csv(file_path, compression='gzip', chunksize=batch_size)

    async with AsyncSessionLocal() as session:
        for chunk in tqdm(chunks):
            # Prepare records
            records = []
            for _, row in chunk.iterrows():
                records.append({
                    "battery_id": row['battery_id'],
                    "timestamp": pd.to_datetime(row['ts']),
                    "voltage": float(row['voltage_v']),
                    "temperature": float(row['temperature_c']),
                    "internal_resistance": float(row['resistance_mohm']),
                })

            # Bulk insert
            try:
                await session.execute(
                    "INSERT INTO telemetry (battery_id, timestamp, voltage, temperature, internal_resistance) "
                    "VALUES (:battery_id, :timestamp, :voltage, :temperature, :internal_resistance) "
                    "ON CONFLICT (battery_id, timestamp) DO NOTHING",
                    records
                )
                await session.commit()
            except Exception as e:
                print(f"Error: {e}")
                await session.rollback()
                continue

    print(f"Completed {file_path}")

async def main():
    locations = [
        "Bangrak", "Chiangmai", "HatYai", "KhonKaen",
        "Nonthaburi", "Phrakhanong", "Phuket", "Sriracha", "SuratThani"
    ]

    for location in locations:
        file_path = f"output/production_2years/by_location/battery_sensors_{location}_Data_Center.csv.gz"
        await load_location(file_path)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Install Dependencies

```bash
pip install pandas sqlalchemy asyncpg tqdm
```

### Step 3: Run Loading

```bash
cd battery-rul-data-generation
python load_to_db.py
```

---

## ⚡ Performance Optimization

### Database Configuration

```sql
-- Temporarily disable indexes for faster loading
DROP INDEX IF EXISTS ix_telemetry_battery_id;
DROP INDEX IF EXISTS ix_telemetry_timestamp;
DROP INDEX IF EXISTS ix_telemetry_battery_timestamp;

-- Increase work_mem for bulk operations
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';

-- Load data here...

-- Recreate indexes
CREATE INDEX ix_telemetry_battery_id ON telemetry(battery_id);
CREATE INDEX ix_telemetry_timestamp ON telemetry(timestamp) USING brin;
CREATE INDEX ix_telemetry_battery_timestamp ON telemetry(battery_id, timestamp);

-- Analyze tables
ANALYZE telemetry;
```

### Batch Size Tuning

| Method | Recommended Batch Size | Memory Usage |
|--------|----------------------|--------------|
| PostgreSQL COPY | Full file | High |
| API Upload | 10,000 records | Medium |
| SQLAlchemy | 50,000 records | Medium-High |

---

## 📊 Monitoring Progress

### Check Record Count

```sql
-- Count records by location
SELECT
    LEFT(battery_id, 8) as location_prefix,
    COUNT(*) as record_count
FROM telemetry
GROUP BY LEFT(battery_id, 8)
ORDER BY location_prefix;

-- Total records
SELECT COUNT(*) FROM telemetry;

-- Date range
SELECT MIN(timestamp), MAX(timestamp) FROM telemetry;
```

### Check Loading Speed

```bash
# Monitor database size
watch -n 5 'psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"'

# Monitor record count
watch -n 10 'psql $DATABASE_URL -c "SELECT COUNT(*) FROM telemetry;"'
```

---

## 🚨 Troubleshooting

### Issue: Out of Memory

**Solution**: Reduce batch size or use streaming

```python
# Instead of:
df = pd.read_csv(file)  # Loads all into memory

# Use:
for chunk in pd.read_csv(file, chunksize=10000):  # Streams
    process(chunk)
```

### Issue: Duplicate Key Errors

**Solution**: Use ON CONFLICT DO NOTHING

```sql
INSERT INTO telemetry (...)
VALUES (...)
ON CONFLICT (battery_id, timestamp) DO NOTHING;
```

### Issue: Slow Performance

**Solution**: Drop indexes during load, recreate after

```sql
-- Before loading
DROP INDEX ix_telemetry_timestamp;

-- After loading
CREATE INDEX ix_telemetry_timestamp ON telemetry(timestamp) USING brin;
```

### Issue: Connection Timeout

**Solution**: Increase timeout in connection string

```python
DATABASE_URL = "postgresql://...?connect_timeout=60"
```

---

## ✅ Verification Checklist

After loading:

- [ ] Total record count matches expected (~247M)
- [ ] Date range is 2023-12-01 to 2025-11-30
- [ ] All 216 batteries have data
- [ ] No NULL values in critical columns
- [ ] Voltage range is 11.5-14.5V
- [ ] Temperature range is 20-50°C
- [ ] Resistance values are positive
- [ ] Timestamps are sequential
- [ ] Indexes are recreated
- [ ] ANALYZE has been run

### Verification SQL

```sql
-- Record count by date
SELECT DATE(timestamp), COUNT(*)
FROM telemetry
GROUP BY DATE(timestamp)
ORDER BY DATE(timestamp)
LIMIT 10;

-- Battery coverage
SELECT COUNT(DISTINCT battery_id) FROM telemetry;
-- Should be 216

-- Value ranges
SELECT
    MIN(voltage) as min_voltage,
    MAX(voltage) as max_voltage,
    MIN(temperature) as min_temp,
    MAX(temperature) as max_temp,
    MIN(internal_resistance) as min_resistance,
    MAX(internal_resistance) as max_resistance
FROM telemetry;

-- NULL check
SELECT
    SUM(CASE WHEN battery_id IS NULL THEN 1 ELSE 0 END) as null_battery_id,
    SUM(CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END) as null_timestamp,
    SUM(CASE WHEN voltage IS NULL THEN 1 ELSE 0 END) as null_voltage,
    SUM(CASE WHEN temperature IS NULL THEN 1 ELSE 0 END) as null_temperature
FROM telemetry;
```

---

## 📈 Expected Results

### Loading Time Estimates

| Method | Time | Records/sec |
|--------|------|-------------|
| PostgreSQL COPY | 30-60 min | 60,000-120,000 |
| API Bulk Upload | 2-4 hours | 15,000-30,000 |
| SQLAlchemy | 1-2 hours | 30,000-60,000 |

### Database Size

| Component | Size |
|-----------|------|
| Table Data | ~20 GB |
| Indexes | ~10 GB |
| **Total** | **~30 GB** |

---

## 🎯 Next Steps After Loading

1. **Verify Data**: Run verification SQL queries
2. **Create Aggregations**: Build hourly/daily rollups
3. **Train Models**: Use loaded data for ML training
4. **Enable Predictions**: Deploy ML pipeline
5. **Test API**: Query telemetry via backend API

---

## 📚 Additional Resources

- **Backend API Docs**: https://backend-production-6266.up.railway.app/docs
- **Database Schema**: See backend/alembic/versions/
- **Data Analysis**: See Battery_RUL_Training.ipynb
- **Data Overview**: See DATA_COMPLETE.md

---

**Status**: Ready to Load ✅
**Dataset**: 247M records, 3.3 GB
**Recommended**: Option 1 (PostgreSQL COPY) for speed
**Alternative**: Option 2 (API) for safety

**The data loading guide is complete!** 🚀
