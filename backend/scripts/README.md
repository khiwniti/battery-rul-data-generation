# Backend Scripts

Utility scripts for database management and system administration.

---

## Overview

- **load_training_data.py** - Load training data CSVs into PostgreSQL/TimescaleDB
- **create_admin.py** - Create admin user interactively or via CLI

---

## Prerequisites

1. **Database Running**: PostgreSQL with TimescaleDB extension
2. **Migrations Applied**: `alembic upgrade head`
3. **Environment Variables**: `DATABASE_URL` set in `.env` or environment
4. **Training Data**: CSV files in `output/training_dataset/`

---

## Load Training Data

### Interactive Mode

```bash
cd backend
python scripts/load_training_data.py
```

### Custom Data Directory

```bash
python scripts/load_training_data.py --data-dir /path/to/data
```

### What It Loads

- ✅ Locations (9 Thai data centers)
- ✅ Battery systems (1 system in test dataset)
- ✅ Battery strings (1 string in test dataset)
- ✅ Batteries (24 batteries in test dataset)
- ⚠️  Telemetry (skipped - use psql COPY for bulk loading)

### For Large Telemetry Datasets

Use PostgreSQL COPY command for fast bulk insert:

```bash
# Extract gzipped file
gunzip output/training_dataset/telemetry_jar_calc.csv.gz

# Load via psql
psql $DATABASE_URL -c "\COPY telemetry(battery_id, timestamp, voltage, current, temperature, internal_resistance, soc_pct, soh_pct) FROM 'output/training_dataset/telemetry_jar_calc.csv' CSV HEADER"
```

**Note**: Adjust column list based on your CSV structure.

---

## Create Admin User

### Interactive Mode (Recommended)

```bash
cd backend
python scripts/create_admin.py
```

Prompts for:
- User ID (e.g., `admin`)
- Username (e.g., `admin`)
- Email (e.g., `admin@example.com`)
- Full Name (e.g., `System Administrator`)
- Password (with validation)

**Password Requirements**:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

### Non-Interactive Mode

```bash
python scripts/create_admin.py \
  --user-id admin \
  --username admin \
  --email admin@example.com \
  --password YourSecurePassword123 \
  --full-name "System Administrator"
```

**⚠️ Security Warning**: Non-interactive mode exposes password in command history. Use only for testing.

---

## Complete Setup Workflow

### 1. Setup Database

```bash
# Start PostgreSQL with TimescaleDB (Railway.com or local)
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/battery_rul"
```

### 2. Run Migrations

```bash
cd backend
alembic upgrade head
```

### 3. Load Training Data

```bash
python scripts/load_training_data.py
```

### 4. Create Admin User

```bash
python scripts/create_admin.py
```

### 5. Start Backend

```bash
uvicorn src.main:app_with_sockets --reload
```

### 6. Test API

Open browser: `http://localhost:8000/api/docs`

Login with admin credentials:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'
```

---

## Troubleshooting

### "Database not found" Error

```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Create database if needed
createdb battery_rul
```

### "Data directory not found" Error

```bash
# Generate training data first
cd data-synthesis
python generate_battery_data.py --duration-days 90 --limit-batteries 24
```

### "User already exists" Error

```bash
# List existing users
psql $DATABASE_URL -c "SELECT user_id, username, email, role FROM \"user\";"

# Delete user if needed
psql $DATABASE_URL -c "DELETE FROM \"user\" WHERE user_id='admin';"
```

### "Migration not applied" Error

```bash
# Check current migration version
alembic current

# Apply migrations
alembic upgrade head

# Reset migrations (WARNING: drops all data)
alembic downgrade base
alembic upgrade head
```

---

## Advanced Usage

### Load Partial Data

Edit `load_training_data.py` and comment out sections you don't need.

### Bulk Create Users

Create a CSV with user data and write a custom script:

```python
import asyncio
from create_admin import quick_create_admin

async def bulk_create():
    users = [
        ("engineer1", "john_doe", "john@example.com", "password123", "John Doe"),
        ("engineer2", "jane_smith", "jane@example.com", "password456", "Jane Smith"),
    ]
    for user_id, username, email, password, full_name in users:
        await quick_create_admin(user_id, username, email, password, full_name)

asyncio.run(bulk_create())
```

### Verify Data Loaded Correctly

```bash
psql $DATABASE_URL <<EOF
SELECT 'Locations' as table_name, COUNT(*) as count FROM location
UNION ALL
SELECT 'Systems', COUNT(*) FROM battery_system
UNION ALL
SELECT 'Strings', COUNT(*) FROM string
UNION ALL
SELECT 'Batteries', COUNT(*) FROM battery
UNION ALL
SELECT 'Users', COUNT(*) FROM "user"
UNION ALL
SELECT 'Telemetry', COUNT(*) FROM telemetry;
EOF
```

Expected output (after loading test dataset):
```
  table_name | count
-------------+-------
 Locations   |     9
 Systems     |     1
 Strings     |     1
 Batteries   |    24
 Users       |     1
 Telemetry   |     0 (or 3.1M if loaded)
```

---

## Script Architecture

### load_training_data.py

**Design**:
- Async SQLAlchemy for performance
- Loads data in dependency order (locations → systems → strings → batteries)
- Skips telemetry to avoid long loading times
- Transaction-based (rollback on error)

**Limitations**:
- Telemetry loading requires psql COPY for performance
- Does not handle data conflicts (use `--force` to drop existing data)

### create_admin.py

**Design**:
- Interactive prompts with validation
- Password strength checking
- Email format validation
- Duplicate user detection
- Bcrypt password hashing

**Security**:
- Passwords never shown on screen (uses getpass)
- Hashed with bcrypt before storage
- Admin role assigned automatically

---

## Next Steps After Setup

1. **Test Authentication**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"your-password"}'
   ```

2. **List Locations**:
   ```bash
   curl http://localhost:8000/api/v1/locations \
     -H "Authorization: Bearer <token>"
   ```

3. **List Batteries**:
   ```bash
   curl http://localhost:8000/api/v1/batteries?limit=10 \
     -H "Authorization: Bearer <token>"
   ```

4. **Connect via WebSocket**:
   ```javascript
   const socket = io('http://localhost:8000', {
     auth: { token: '<your-jwt-token>' }
   });
   ```

---

## Additional Resources

- **API Documentation**: http://localhost:8000/api/docs
- **Project Status**: ../PROJECT_STATUS.md
- **API Reference**: ../API_REFERENCE.md
- **Deployment Guide**: ../DEPLOYMENT.md
- **Implementation Roadmap**: ../IMPLEMENTATION_ROADMAP.md

---

**Last Updated**: 2025-11-30
