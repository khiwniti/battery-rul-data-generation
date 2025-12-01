# Battery RUL Prediction & Monitoring System - Deployment Guide

**Railway.com Microservices Deployment for Thai Data Center Battery Fleet**

## 🎯 System Overview

Complete full-stack platform for real-time battery health monitoring, ML-powered RUL prediction, and predictive maintenance across 1,944 VRLA batteries in 9 Thai data centers.

### Architecture

```
Frontend (React) ──► Backend API (FastAPI) ──► TimescaleDB
                          │
                          ├──► ML Pipeline (CatBoost)
                          ├──► Digital Twin (ECM/EKF)
                          └──► Sensor Simulator
```

---

## 📋 Prerequisites

- Railway.com account (free tier works for development)
- Python 3.11+
- Node.js 18+
- PostgreSQL with TimescaleDB extension

---

## 🚀 Railway.com Deployment

### Step 1: Create New Project

1. Go to [Railway.com](https://railway.app)
2. Create new project: "Battery RUL Monitoring"
3. Create 6 services

### Step 2: Deploy Database (TimescaleDB)

```bash
# Add PostgreSQL plugin with TimescaleDB
railway add --plugin postgres

# Run initialization script
psql $DATABASE_URL < database/init.sql
```

### Step 3: Deploy Backend API

```bash
cd backend
railway up
```

**Environment Variables** (set in Railway dashboard):
```
DATABASE_URL=<auto-injected by Railway>
JWT_SECRET_KEY=<generate-strong-key-min-32-chars>
CORS_ORIGINS=["https://your-frontend.railway.app"]
ML_PIPELINE_URL=http://ml-pipeline.railway.internal:8001
DIGITAL_TWIN_URL=http://digital-twin.railway.internal:8002
SENSOR_SIMULATOR_URL=http://sensor-simulator.railway.internal:8003
```

### Step 4: Deploy ML Pipeline

```bash
cd ml-pipeline
railway up
```

### Step 5: Deploy Digital Twin

```bash
cd digital-twin
railway up
```

### Step 6: Deploy Sensor Simulator

```bash
cd sensor-simulator
railway up
```

### Step 7: Deploy Frontend

```bash
cd frontend
railway up
```

**Environment Variables**:
```
VITE_API_URL=https://your-backend-api.railway.app
VITE_WS_URL=https://your-backend-api.railway.app
```

---

## 🗄️ Database Setup

### Run Migrations

```bash
cd backend
alembic upgrade head
```

This creates:
- Master data tables (locations, batteries, strings, systems, users)
- Telemetry hypertable with compression & retention policies
- Continuous aggregate for hourly statistics

### Load Initial Data

```bash
# Generate synthetic battery fleet data
cd data-synthesis
python generate_battery_data.py --duration-days 7 --limit-batteries 216

# Load into database (TODO: implement loader script)
```

---

## 🔐 Create Admin User

```bash
# Python script to create admin user
python -c "
from backend.src.core.security import get_password_hash
from backend.src.models.user import User
# ... create user with hashed password
"
```

Or use SQL:
```sql
INSERT INTO "user" (id, user_id, username, email, hashed_password, full_name, role, is_active)
VALUES (
  gen_random_uuid(),
  'admin',
  'admin',
  'admin@example.com',
  '$2b$12$...', -- bcrypt hash of password
  'System Administrator',
  'admin',
  true
);
```

---

## 🧪 Testing Deployment

### Health Checks

```bash
# Backend API
curl https://your-backend.railway.app/health

# ML Pipeline
curl https://your-ml-pipeline.railway.app/health

# Digital Twin
curl https://your-digital-twin.railway.app/health

# Sensor Simulator
curl https://your-sensor-simulator.railway.app/health
```

### API Endpoints

```bash
# Login
curl -X POST https://your-backend.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# List locations
curl https://your-backend.railway.app/api/v1/locations \
  -H "Authorization: Bearer <token>"

# Get batteries at location
curl https://your-backend.railway.app/api/v1/batteries?location_id=DC-CNX-01 \
  -H "Authorization: Bearer <token>"
```

---

## 📊 Monitoring

### Railway.com Dashboard

- View logs for each service
- Monitor memory/CPU usage
- Check health status
- View deployment history

### Application Metrics

```bash
# Backend metrics (Prometheus format)
curl https://your-backend.railway.app:9090/metrics
```

### Database Monitoring

```sql
-- Check TimescaleDB hypertable stats
SELECT * FROM timescaledb_information.hypertables;

-- Check compression status
SELECT * FROM timescaledb_information.chunks;

-- Check continuous aggregate
SELECT * FROM timescaledb_information.continuous_aggregates;
```

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check DATABASE_URL is set
railway variables

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Service Communication Errors

```bash
# Verify internal networking URLs
# Railway uses pattern: service-name.railway.internal

# Test from backend container
curl http://ml-pipeline.railway.internal:8001/health
```

### Frontend Not Loading

```bash
# Check CORS settings in backend
# Verify VITE_API_URL points to backend

# Check browser console for errors
```

---

## 🔧 Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with local database URL

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
# Edit .env with local backend URL

# Start dev server
npm run dev
```

### ML Pipeline

```bash
cd ml-pipeline
pip install -r requirements.txt
cd src/api
uvicorn main:app --reload --port 8001
```

---

## 📈 Performance Tuning

### TimescaleDB Optimization

```sql
-- Adjust chunk interval based on data volume
SELECT set_chunk_time_interval('telemetry', INTERVAL '7 days');

-- Enable parallel queries
ALTER DATABASE battery_rul SET max_parallel_workers_per_gather = 4;

-- Increase work memory for aggregations
ALTER DATABASE battery_rul SET work_mem = '64MB';
```

### Backend Scaling

```yaml
# Railway.com settings
replicas: 2
memory: 512MB
cpu: 1
```

### Frontend CDN

- Enable Railway CDN for static assets
- Configure caching headers
- Minify JavaScript/CSS

---

## 🔒 Security Checklist

- [ ] Change default JWT_SECRET_KEY
- [ ] Use strong passwords (min 12 chars)
- [ ] Enable HTTPS only (Railway auto-provision)
- [ ] Configure CORS properly (no wildcard in production)
- [ ] Rotate secrets every 90 days
- [ ] Enable Railway 2FA
- [ ] Review user permissions regularly
- [ ] Monitor failed login attempts
- [ ] Keep dependencies updated

---

## 📝 Maintenance Tasks

### Daily

- Check health endpoints
- Review error logs
- Monitor alerting system

### Weekly

- Review database size
- Check TimescaleDB compression
- Analyze slow queries

### Monthly

- Update dependencies
- Review access logs
- Database backup verification
- Performance review

### Quarterly

- Security audit
- Load testing
- Disaster recovery drill

---

## 🆘 Support

### Documentation

- Backend API: `https://your-backend.railway.app/api/docs`
- Project spec: `specs/001-railway-deployment/spec.md`
- Data schema: `data-synthesis/docs/data_schema.md`

### Common Issues

1. **"Circuit breaker is open"** - ML service down, check logs
2. **"Could not validate credentials"** - JWT token expired, re-login
3. **"Database connection failed"** - Check DATABASE_URL, verify PostgreSQL running
4. **"CORS error"** - Add frontend URL to CORS_ORIGINS

---

## 🎓 Next Steps

1. **Train ML Model**: Use data-synthesis to generate training data
2. **Implement Alerts**: Complete alert system with notifications
3. **Add WebSocket**: Real-time telemetry streaming
4. **Control Panel**: Sensor simulator scenarios
5. **Reports**: PDF/Excel export for maintenance reports

---

## 📄 License

Research and development use.

---

**Last Updated**: 2025-11-30
**Version**: 1.0.0
**Maintained by**: Battery RUL Engineering Team
