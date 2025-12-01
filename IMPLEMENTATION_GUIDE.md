# Battery RUL System - Complete Implementation Guide

## Status: Ready for Implementation

This document provides the complete implementation roadmap for the Battery RUL Prediction System based on deep architectural analysis.

---

## IMMEDIATE NEXT STEPS

### Step 1: Complete Frontend Implementation (3-4 hours)

The frontend is the highest-priority item as it provides immediate visible value and can be developed independently while waiting for the Kaggle 2-year dataset to complete.

#### 1.1 Create Layout System (30 minutes)

**Create these files:**

`frontend/src/components/Layout/MainLayout.tsx` - Main app container with sidebar
`frontend/src/components/Layout/Sidebar.tsx` - Navigation sidebar
`frontend/src/components/Layout/Header.tsx` - Page header with breadcrumbs
`frontend/src/App.tsx` - Update to use MainLayout wrapper

**Key features:**
- Responsive sidebar (collapsible on mobile)
- Navigation: Dashboard, Locations, Batteries, Alerts, Users (admin only)
- User profile dropdown in header
- WebSocket connection status indicator
- Alert bell with badge count

#### 1.2 Implement Dashboard Page (1 hour)

**Update:** `frontend/src/pages/Dashboard.tsx`

**Create components:**
- `frontend/src/components/Dashboard/StatCard.tsx` - Metric display cards
- `frontend/src/components/Dashboard/LocationGrid.tsx` - 9 location cards
- `frontend/src/components/Dashboard/RecentAlerts.tsx` - Latest alerts list
- `frontend/src/components/Dashboard/FleetHealthChart.tsx` - SOH distribution

**Features:**
- 4 stat cards: Total Batteries, Active Alerts, Critical Count, Avg SOH
- Location grid showing battery counts and alert counts per location
- Recent alerts list (last 10) with severity badges
- Fleet health chart (Recharts bar chart of SOH distribution)
- Real-time updates via WebSocket

**API calls:**
```typescript
GET /api/v1/locations
GET /api/v1/batteries (with summary)
GET /api/v1/alerts?limit=10
WebSocket: connect(), subscribe to 'alert' events
```

#### 1.3 Implement Battery Detail Page (1.5 hours)

**Update:** `frontend/src/pages/BatteryDetail.tsx`

**Create components:**
- `frontend/src/components/Battery/BatteryHeader.tsx` - Title and status
- `frontend/src/components/Battery/BatterySpecs.tsx` - Specifications card
- `frontend/src/components/Battery/TelemetryChart.tsx` - Reusable chart
- `frontend/src/components/Battery/RULCard.tsx` - RUL prediction display
- `frontend/src/components/Battery/AlertHistory.tsx` - Past alerts

**Features:**
- Battery header with breadcrumbs and status badge
- Specifications: manufacturer, model, serial, install date, warranty
- Current status: latest voltage, temp, SOC, SOH (real-time)
- 4 telemetry charts (24h): Voltage, Temperature, SOH, Resistance
- RUL prediction card (placeholder until ML deployed): RUL days, confidence, risk level
- Alert history table
- Real-time updates: WebSocket subscribeToBattery()

**API calls:**
```typescript
GET /api/v1/batteries/{batteryId}
GET /api/v1/batteries/{batteryId}/telemetry?hours=24
GET /api/v1/alerts?battery_id={batteryId}
WebSocket: subscribeToBattery(batteryId)
```

#### 1.4 Implement Location Detail Page (1 hour)

**Update:** `frontend/src/pages/Location.tsx`

**Create components:**
- `frontend/src/components/Location/LocationHeader.tsx` - Location info
- `frontend/src/components/Location/BatteryTable.tsx` - Sortable battery table
- `frontend/src/components/Location/StatusFilter.tsx` - Filter buttons
- `frontend/src/components/Location/EnvironmentCard.tsx` - Climate info

**Features:**
- Location header with region and climate info
- Environment card: current temp, humidity, HVAC status
- Battery table with columns: ID, Position, Voltage, Temp, SOH, Status
- Filters: All/Healthy/Warning/Critical
- Search by battery ID
- Sortable columns
- Pagination (50 per page)
- Real-time row updates

**API calls:**
```typescript
GET /api/v1/locations/{locationId}
GET /api/v1/batteries?location_id={locationId}
GET /api/v1/alerts?location_id={locationId}
WebSocket: subscribeToLocation(locationId)
```

---

### Step 2: Implement Sensor Simulator (2-3 hours)

The Sensor Simulator is essential for testing and demos, allowing real-time telemetry generation without waiting for actual hardware.

#### 2.1 Core Telemetry Generation (1.5 hours)

**Create these files:**

`sensor-simulator/src/core/config.py` - Configuration settings
`sensor-simulator/src/simulator/telemetry_generator.py` - Telemetry generation engine
`sensor-simulator/src/simulator/battery_state.py` - Battery state tracking
`sensor-simulator/src/simulator/scenarios.py` - Predefined test scenarios
`sensor-simulator/src/schemas/simulation.py` - Pydantic schemas

**Reuse from data-synthesis:**
- Copy `data-synthesis/src/battery_degradation.py` → `sensor-simulator/src/simulator/degradation_model.py`
- Copy `data-synthesis/src/thailand_environment.py` → `sensor-simulator/src/simulator/environment_model.py`
- Adapt for real-time generation (not batch)

**Features:**
- Generate telemetry every N seconds (configurable, default 5s)
- Support 1-24 batteries simultaneously
- Apply degradation over time
- Support predefined scenarios:
  - Normal Operation
  - HVAC Failure (temp rises to 40°C)
  - Power Outage (discharge cycle)
  - Thermal Runaway (single battery to 60°C)
  - Accelerated Degradation
- Batch insert into database (50 records per 10s)
- State persistence

#### 2.2 Control Panel API (1 hour)

**Update:** `sensor-simulator/src/api/main.py`

**Create:** `sensor-simulator/src/api/routes/simulation.py`

**Endpoints:**
```python
POST /api/v1/simulation/start
POST /api/v1/simulation/stop
GET /api/v1/simulation/status
GET /api/v1/scenarios
POST /api/v1/scenarios/apply
POST /api/v1/simulation/adjust
```

**Features:**
- Start/stop simulation
- Apply scenarios dynamically
- Adjust parameters (temp offset, voltage offset, discharge rate)
- Report status (uptime, records generated, current scenario)

#### 2.3 Database Integration (30 minutes)

**Use asyncpg for high-performance inserts:**
```python
# Batch insert telemetry
await db.execute(
    "INSERT INTO telemetry (...) VALUES (...)",
    batch_records
)

# Trigger backend broadcast (HTTP callback)
await httpx.post(
    f"{BACKEND_URL}/api/v1/internal/broadcast_telemetry",
    json={"battery_ids": [...]},
    headers={"X-Internal-API-Key": SHARED_SECRET}
)
```

---

### Step 3: ML Model Training (1 hour, when data ready)

Once the Kaggle 2-year dataset completes:

```bash
# Download from Kaggle
kaggle kernels output YOUR_USERNAME/battery-rul-generation

# Extract
tar -xzf battery_rul_2year_dataset.tar.gz

# Train model
cd ml-pipeline
python train_model.py \
  --data-dir ../kaggle_dataset/output/production_2years \
  --output-dir ./models \
  --iterations 1000 \
  --lookback-hours 24

# Verify model
ls -lh models/rul_catboost_model.cbm  # Should be 5-10MB
```

**Expected metrics:**
- MAE: 30-50 days
- RMSE: 50-70 days
- R²: 0.90-0.95

---

### Step 4: Railway Deployment (2-3 hours)

#### 4.1 Deploy Services in Order

**1. Database (if not already deployed)**
```bash
# Railway dashboard
- Create project: "Battery RUL Monitoring"
- Add PostgreSQL plugin
- Note DATABASE_URL
```

**2. Backend API**
```bash
cd backend
railway link
railway service  # Select "backend"
railway up

# Set environment variables via Railway dashboard:
JWT_SECRET_KEY=<openssl rand -hex 32>
CORS_ORIGINS=["https://frontend-production.up.railway.app"]
ML_PIPELINE_URL=http://ml-pipeline.railway.internal:8001

# Run migrations
railway run alembic upgrade head

# Create admin user
railway run python -c "from src.scripts.create_admin_quick import create_admin; create_admin('admin', 'Admin123!')"
```

**3. ML Pipeline**
```bash
cd ml-pipeline

# Ensure model is trained and in ./models/
ls -lh models/rul_catboost_model.cbm

railway link
railway service  # Select "ml-pipeline"
railway up

# Verify
curl https://ml-pipeline-production.up.railway.app/health
curl https://ml-pipeline-production.up.railway.app/api/v1/model/info
```

**4. Sensor Simulator**
```bash
cd sensor-simulator
railway link
railway service  # Select "sensor-simulator"

# Set environment variables:
DATABASE_URL=<same as backend>
BACKEND_API_URL=http://backend.railway.internal:8000

railway up
```

**5. Frontend**
```bash
cd frontend

# Create railway.json if doesn't exist
cat > railway.json <<EOF
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm install && npm run build"
  },
  "deploy": {
    "startCommand": "npm run preview -- --host 0.0.0.0 --port \$PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 30
  }
}
EOF

# Set environment variables:
VITE_API_URL=https://backend-production-6266.up.railway.app
VITE_WS_URL=https://backend-production-6266.up.railway.app

railway link
railway service  # Select "frontend"
railway up

# Update backend CORS
railway variables set CORS_ORIGINS='["https://frontend-production.up.railway.app"]' --service backend
```

#### 4.2 Load Initial Data

```bash
# Load master data (locations, batteries, systems, strings)
railway run --service backend python scripts/load_master_data.py

# OR start simulator for real-time data
curl -X POST https://sensor-simulator-production.up.railway.app/api/v1/simulation/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{
    "battery_ids": "all",
    "sampling_interval_seconds": 60,
    "scenario": "normal_operation"
  }'
```

#### 4.3 Verification Checklist

Backend:
- [ ] Health check: `curl https://backend-production-6266.up.railway.app/health`
- [ ] Login works: `POST /api/v1/auth/login`
- [ ] Locations API: `GET /api/v1/locations` returns 9 locations
- [ ] WebSocket connects: Check browser console

ML Pipeline:
- [ ] Health check: `curl https://ml-pipeline-production.up.railway.app/health`
- [ ] Model loaded: `model_loaded: true` in health response
- [ ] Model info: `GET /api/v1/model/info` returns metrics

Sensor Simulator:
- [ ] Health check works
- [ ] Simulation starts: `POST /api/v1/simulation/start`
- [ ] Data appears in backend: `GET /api/v1/batteries/{id}/telemetry`

Frontend:
- [ ] Login page loads
- [ ] Login succeeds
- [ ] Dashboard shows data
- [ ] Location page works
- [ ] Battery detail shows charts
- [ ] WebSocket indicator shows "Connected"

---

## KEY FILES REFERENCE

### Frontend (Priority 1)
1. `frontend/src/components/Layout/MainLayout.tsx` - App layout
2. `frontend/src/components/Layout/Sidebar.tsx` - Navigation
3. `frontend/src/pages/Dashboard.tsx` - Main dashboard
4. `frontend/src/pages/BatteryDetail.tsx` - Battery detail with charts
5. `frontend/src/pages/Location.tsx` - Location detail
6. `frontend/src/components/Battery/TelemetryChart.tsx` - Reusable chart component
7. `frontend/src/components/Battery/RULCard.tsx` - RUL prediction display
8. `frontend/railway.json` - Deployment config (create)

### Sensor Simulator (Priority 2)
1. `sensor-simulator/src/simulator/telemetry_generator.py` - Core generation logic
2. `sensor-simulator/src/simulator/scenarios.py` - Test scenarios
3. `sensor-simulator/src/api/routes/simulation.py` - Control API
4. `sensor-simulator/src/core/config.py` - Configuration

### Backend (Already Complete)
1. `backend/src/api/routes/predictions.py` - RUL proxy endpoint (create)
2. `backend/scripts/load_master_data.py` - Data loader (create if needed)

### ML Pipeline (Already Complete)
1. `ml-pipeline/train_model.py` - Training script (ready to use)
2. `ml-pipeline/models/` - Model storage directory

---

## ENVIRONMENT VARIABLES

### Backend
```bash
DATABASE_URL=<auto-injected by Railway>
JWT_SECRET_KEY=<openssl rand -hex 32>
CORS_ORIGINS=["https://frontend-production.up.railway.app"]
ML_PIPELINE_URL=http://ml-pipeline.railway.internal:8001
SENSOR_SIMULATOR_URL=http://sensor-simulator.railway.internal:8003
ENVIRONMENT=production
LOG_LEVEL=INFO
DB_POOL_SIZE=20
```

### ML Pipeline
```bash
PORT=8001
MODEL_PATH=/app/models/rul_catboost_model.cbm
LOOKBACK_HOURS=24
RUL_WARNING_DAYS=180
RUL_CRITICAL_DAYS=90
```

### Sensor Simulator
```bash
PORT=8003
DATABASE_URL=<same as backend>
BACKEND_API_URL=http://backend.railway.internal:8000
BACKEND_API_KEY=<shared-secret>
SIMULATION_BATCH_SIZE=50
```

### Frontend
```bash
VITE_API_URL=https://backend-production-6266.up.railway.app
VITE_WS_URL=https://backend-production-6266.up.railway.app
```

---

## IMPLEMENTATION PRIORITY

**Priority 1 (Start Now):**
1. Frontend Layout System (30 min)
2. Dashboard Page (1 hour)
3. Battery Detail Page (1.5 hours)
4. Location Detail Page (1 hour)

**Priority 2 (Parallel):**
1. Sensor Simulator Core (1.5 hours)
2. Sensor Simulator API (1 hour)

**Priority 3 (When Data Ready):**
1. Train ML Model (1 hour)
2. Deploy ML Pipeline (30 min)

**Priority 4 (Final Assembly):**
1. Deploy all services to Railway (2-3 hours)
2. Load data and verify end-to-end flow (1 hour)

**Total Estimated Time**: 10-12 hours of focused development

---

## CURRENT STATUS SUMMARY

✅ **Complete:**
- Backend API (deployed, functional)
- ML Pipeline service code (needs model training)
- Data generation system (running on Kaggle)
- Documentation and architecture

🚧 **In Progress:**
- Frontend (skeleton exists, pages need implementation)
- Kaggle dataset generation (27% complete, ~5 hours remaining)

⏳ **Not Started:**
- Sensor Simulator (skeleton only)
- Multi-service Railway deployment
- End-to-end integration testing

---

## SUCCESS CRITERIA

**Minimum Viable Product (MVP):**
- [ ] User can log in
- [ ] Dashboard shows 9 locations with battery counts
- [ ] Battery detail page shows telemetry charts
- [ ] Real-time updates work (WebSocket)
- [ ] Sensor Simulator can generate test data
- [ ] All services deployed to Railway
- [ ] ML model predicts RUL (after training)

**Full Feature Set:**
- [ ] Alert management UI
- [ ] RUL predictions displayed throughout frontend
- [ ] Multiple scenarios in sensor simulator
- [ ] User management (admin panel)
- [ ] Historical analysis and reporting
- [ ] PDF/Excel export

---

## NEXT SESSION CONTINUATION

If continuing this work in a new session:

1. **Check Kaggle dataset status**: Is the 2-year generation complete?
2. **Train ML model** if data ready: `python ml-pipeline/train_model.py`
3. **Implement Frontend pages** following this guide
4. **Implement Sensor Simulator** following this guide
5. **Deploy all services** following Railway deployment section
6. **Verify end-to-end** using checklist above

**Estimated completion time**: 10-12 hours from current state

---

**Last Updated**: 2025-11-30 16:15 UTC
**Status**: Implementation guide complete, ready for execution
**Next Action**: Begin Frontend Layout System implementation
