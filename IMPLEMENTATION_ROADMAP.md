# Implementation Roadmap - Battery RUL Prediction System

**Last Updated**: 2025-11-30
**Current Status**: Backend 85% Complete, Training Data Ready

---

## ✅ Completed Work (Current Session)

### Backend Infrastructure (100%)
- [x] Database models (7 models)
- [x] Alembic migrations (3 migrations)
- [x] TimescaleDB optimization
- [x] JWT authentication system
- [x] User management (CRUD)
- [x] Location API (3 endpoints)
- [x] Battery API (3 endpoints)
- [x] Alert API (5 endpoints)
- [x] WebSocket real-time communication
- [x] Telemetry broadcaster service
- [x] Service communication layer
- [x] Error handling & logging
- [x] API documentation

### Data Generation (100%)
- [x] 90-day training dataset (3.1M records)
- [x] Thai environmental models
- [x] Physics-based degradation
- [x] Feature store generation
- [x] Data validation reports

---

## 🚀 Immediate Next Steps (Priority Order)

### Phase A: Data Loading & Initial Admin User (1-2 hours)

**Why First**: Need real data in database to test frontend and make backend usable

**Tasks**:
1. **Create Data Loader Script** (`backend/scripts/load_training_data.py`)
   - Load CSVs from `output/training_dataset/`
   - Insert into PostgreSQL/TimescaleDB
   - Handle foreign key relationships
   - Bulk insert for performance
   - Progress reporting

2. **Create Admin User Script** (`backend/scripts/create_admin.py`)
   - Interactive prompt for username/password
   - Hash password with bcrypt
   - Insert into user table
   - Verify creation

3. **Test API with Real Data**
   - Run health checks
   - Login with admin user
   - Query locations, batteries, telemetry
   - Verify WebSocket connection

**Deliverables**:
- `backend/scripts/load_training_data.py`
- `backend/scripts/create_admin.py`
- Database populated with 3.1M records
- Admin user created

---

### Phase B: Frontend Dashboard Implementation (8-12 hours)

**Why Second**: Most visible user-facing component, demonstrates system value

#### B.1: Dashboard Layout & Navigation (2 hours)

**Files**:
- `frontend/src/components/Layout.tsx` - Main layout with sidebar
- `frontend/src/components/Sidebar.tsx` - Navigation menu
- `frontend/src/components/Header.tsx` - Top bar with user menu

**Features**:
- Responsive sidebar with menu items
- User profile dropdown
- Logout functionality
- Active route highlighting

#### B.2: Login Page (1 hour)

**Files**:
- `frontend/src/pages/LoginPage.tsx` - Login form

**Features**:
- Username/password form
- Error handling
- JWT token storage
- Redirect to dashboard on success
- Form validation

#### B.3: Dashboard Overview Page (3-4 hours)

**Files**:
- `frontend/src/pages/DashboardPage.tsx` - Main dashboard
- `frontend/src/components/StatCard.tsx` - Metric card component
- `frontend/src/components/AlertList.tsx` - Recent alerts widget
- `frontend/src/components/LocationGrid.tsx` - Location cards

**Features**:
- 4 stat cards (Total Batteries, Active Alerts, Critical Batteries, Avg SOH)
- Location grid with battery counts and health status
- Recent alerts list (last 10)
- Real-time updates via WebSocket
- Responsive grid layout

**API Integration**:
```typescript
GET /api/v1/locations (with stats)
GET /api/v1/alerts?limit=10&active_only=true
WebSocket: subscribe to global alerts
```

#### B.4: Location Detail Page (2-3 hours)

**Files**:
- `frontend/src/pages/LocationPage.tsx` - Location detail view
- `frontend/src/components/BatteryTable.tsx` - Battery list table
- `frontend/src/components/LocationMap.tsx` - Location info card

**Features**:
- Location information (name, region, climate)
- Battery list table with status, voltage, temperature, SOH
- Filter by status (all, healthy, warning, critical)
- Sort by various columns
- Click battery → navigate to battery detail
- Real-time updates via WebSocket location room

**API Integration**:
```typescript
GET /api/v1/locations/{location_id}
GET /api/v1/locations/{location_id}/batteries
WebSocket: subscribe_location
```

#### B.5: Battery Detail Page (2-3 hours)

**Files**:
- `frontend/src/pages/BatteryDetailPage.tsx` - Battery detail view
- `frontend/src/components/TelemetryChart.tsx` - Time-series chart (Recharts)
- `frontend/src/components/BatteryInfo.tsx` - Battery specs card
- `frontend/src/components/BatteryAlerts.tsx` - Battery alerts list

**Features**:
- Battery specifications (manufacturer, model, serial, age, warranty)
- Latest telemetry values (voltage, temperature, SOC, SOH)
- Telemetry charts (last 24 hours):
  - Voltage over time
  - Temperature over time
  - SOH trend
- Alert history for this battery
- Real-time updates via WebSocket battery room

**API Integration**:
```typescript
GET /api/v1/batteries/{battery_id}
GET /api/v1/batteries/{battery_id}/telemetry?start=...&end=...
GET /api/v1/alerts?battery_id=...
WebSocket: subscribe_battery
```

---

### Phase C: Alert Management UI (3-4 hours)

**Files**:
- `frontend/src/pages/AlertsPage.tsx` - Alert list page
- `frontend/src/components/AlertFilters.tsx` - Filter sidebar
- `frontend/src/components/AlertTable.tsx` - Alert data table
- `frontend/src/components/AlertDetailModal.tsx` - Alert detail popup
- `frontend/src/components/AlertNotification.tsx` - Toast notification

**Features**:
- Alert list with filters (location, severity, type, date range)
- Acknowledge button (engineer+ only)
- Resolve button (engineer+ only)
- Alert detail modal with battery context
- Real-time alert notifications (toast)
- Sound notification for critical alerts

**API Integration**:
```typescript
GET /api/v1/alerts (with filters)
GET /api/v1/alerts/{alert_id}
POST /api/v1/alerts/{alert_id}/acknowledge
POST /api/v1/alerts/{alert_id}/resolve
WebSocket: listen for 'alert' events
```

---

### Phase D: User Management UI (2-3 hours, Admin Only)

**Files**:
- `frontend/src/pages/UsersPage.tsx` - User management page
- `frontend/src/components/UserTable.tsx` - User list table
- `frontend/src/components/CreateUserModal.tsx` - Create user form
- `frontend/src/components/EditUserModal.tsx` - Edit user form

**Features**:
- User list table
- Create user button → modal
- Edit user → modal
- Delete user (with confirmation)
- Role badge (color-coded)
- Active/inactive status toggle

**API Integration**:
```typescript
GET /api/v1/auth/users
POST /api/v1/auth/users
PATCH /api/v1/auth/users/{user_id}
DELETE /api/v1/auth/users/{user_id}
```

---

### Phase E: ML Pipeline Service (6-8 hours)

**Tasks**:
1. **Train CatBoost Model** (2 hours)
   - Load feature store from CSV
   - Load battery states (ground truth)
   - Train/validation split
   - Hyperparameter tuning
   - Model evaluation
   - Save model artifact

2. **Prediction API** (2 hours)
   - `POST /predict/rul` - Single battery prediction
   - `POST /predict/rul/batch` - Bulk prediction
   - Feature preprocessing
   - Model loading
   - Response caching

3. **Feature Engineering Service** (2 hours)
   - Calculate rolling statistics
   - Generate derived features
   - Align with training features

4. **Model Management** (2 hours)
   - Model versioning
   - A/B testing support
   - Model registry
   - Retraining pipeline

**Files**:
- `ml-pipeline/src/train_model.py` - Training script
- `ml-pipeline/src/api/predict.py` - Prediction endpoints
- `ml-pipeline/src/features/engineer.py` - Feature engineering
- `ml-pipeline/models/catboost_v1.cbm` - Trained model

---

### Phase F: Sensor Simulator Service (4-6 hours)

**Tasks**:
1. **Telemetry Generation** (2 hours)
   - Real-time telemetry generation
   - Configurable sampling rate
   - Multi-battery simulation
   - Insert into database

2. **Control Panel API** (2 hours)
   - Start/stop simulation
   - Configure scenarios (HVAC failure, thermal runaway)
   - Adjust parameters (temperature, voltage)
   - Simulation status

3. **Integration with Broadcaster** (2 hours)
   - Trigger WebSocket broadcasts
   - Alert generation
   - Database inserts

**Files**:
- `sensor-simulator/src/simulator/telemetry.py` - Generation logic
- `sensor-simulator/src/api/control.py` - Control panel API
- `sensor-simulator/src/scenarios/` - Scenario definitions

---

### Phase G: Digital Twin Service (8-10 hours)

**Tasks**:
1. **ECM Implementation** (4 hours)
   - Equivalent circuit model
   - Battery state equations
   - Parameter estimation

2. **EKF Implementation** (4 hours)
   - Extended Kalman Filter
   - State estimation
   - Uncertainty quantification

3. **Hybrid Fusion** (2 hours)
   - Combine ML (60%) + Digital Twin (40%)
   - Weighted prediction
   - Confidence intervals

**Files**:
- `digital-twin/src/models/ecm.py` - ECM model
- `digital-twin/src/models/ekf.py` - EKF filter
- `digital-twin/src/api/simulate.py` - Simulation API

---

## 📊 Time Estimates

| Phase | Description | Hours | Priority |
|-------|-------------|-------|----------|
| A | Data Loading & Admin | 1-2 | **Critical** |
| B | Frontend Dashboard | 8-12 | **High** |
| C | Alert Management UI | 3-4 | **High** |
| D | User Management UI | 2-3 | **Medium** |
| E | ML Pipeline | 6-8 | **High** |
| F | Sensor Simulator | 4-6 | **Medium** |
| G | Digital Twin | 8-10 | **Low** |
| **Total** | | **32-45 hours** | |

---

## 🎯 Recommended Execution Order

### Week 1: Core Functionality
1. **Day 1**: Phase A (Data Loading)
2. **Day 2-3**: Phase B.1-B.3 (Dashboard Layout + Overview)
3. **Day 4**: Phase B.4 (Location Detail)
4. **Day 5**: Phase B.5 (Battery Detail)

### Week 2: Advanced Features
1. **Day 1**: Phase C (Alert Management UI)
2. **Day 2**: Phase D (User Management UI)
3. **Day 3-4**: Phase E (ML Pipeline)
4. **Day 5**: Testing & Bug Fixes

### Week 3: Optional Advanced Services
1. **Day 1-2**: Phase F (Sensor Simulator)
2. **Day 3-5**: Phase G (Digital Twin)

---

## 🔑 Success Criteria

### Minimum Viable Product (MVP)
- [x] Backend API functional
- [x] Authentication working
- [ ] Dashboard displays real data
- [ ] Location/battery detail pages work
- [ ] Real-time updates via WebSocket
- [ ] Alert list and acknowledgment
- [ ] Admin can manage users

### Full Production System
- [ ] ML predictions integrated
- [ ] Sensor simulator running
- [ ] Digital twin validation
- [ ] Automated testing (80% coverage)
- [ ] CI/CD pipeline
- [ ] Monitoring dashboards

---

## 📝 Notes

- **Backend is production-ready** - Can deploy to Railway.com immediately
- **Training data is ready** - 3.1M records, 90 days, 24 batteries
- **Focus on frontend first** - Most visible impact
- **ML pipeline second** - Core value proposition
- **Digital twin last** - Nice-to-have, not critical

---

## 🚀 Quick Start for Next Developer

```bash
# 1. Load training data
cd backend
python scripts/load_training_data.py

# 2. Create admin user
python scripts/create_admin.py

# 3. Start backend
uvicorn src.main:app_with_sockets --reload

# 4. Start frontend
cd ../frontend
npm install
npm run dev

# 5. Login at http://localhost:5173
# Username: admin
# Password: <your-password>
```

---

**Ready to begin Phase A: Data Loading & Initial Admin User**

This is the critical next step to make the system functional end-to-end.
