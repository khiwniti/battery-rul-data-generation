# Implementation Plan: Battery RUL Prediction & Monitoring System

**Branch**: `001-railway-deployment` | **Date**: 2025-11-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-railway-deployment/spec.md`

## Summary

Build a production-grade Battery RUL (Remaining Useful Life) Prediction & Monitoring System deployed on Railway.com to monitor 1,944 VRLA batteries across 9 Thai data centers. The system provides real-time health monitoring dashboards, ML-based RUL forecasting with physics-based Digital Twin fusion, scenario simulation for training, and historical trend analysis. Core value: prevent unplanned outages by predicting battery failures 90-180 days in advance, enabling proactive maintenance planning aligned with Thai operational constraints (monsoon season, regional temperature differences, grid instability patterns).

**Technical Approach**: Microservices architecture on Railway.com with React frontend, FastAPI backend (REST + WebSocket), TimescaleDB for time-series telemetry storage, separate ML Pipeline service for CatBoost RUL predictions, Digital Twin service for physics-based ECM/EKF estimation, and Sensor Simulator for testing/training scenarios. Hybrid prediction fusion (60% Digital Twin, 40% ML) provides robustness. Temperature-aware features critical for accuracy (35-45% improvement over temperature-agnostic baseline).

## Technical Context

**Language/Version**: Python 3.11 (backend, ML, simulator), TypeScript 5.x (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.x, python-socketio 5.x
- ML: CatBoost 1.2+, NumPy 1.24+, Pandas 2.x, SciPy 1.11+
- Digital Twin: NumPy (EKF implementation), custom ECM battery model
- Frontend: React 18+, Vite 5.x, TanStack Query, Recharts, Socket.IO client
- Database: TimescaleDB (PostgreSQL 15+ with time-series extension)

**Storage**: TimescaleDB with hypertable partitioning for telemetry data (partitioned by month), standard PostgreSQL tables for master data, JSON storage for model artifacts

**Testing**: pytest + pytest-asyncio (backend/ML), Playwright (E2E frontend), contract tests via Pact, load testing via Locust

**Target Platform**: Railway.com cloud platform (Linux containers, auto-scaling, internal networking)

**Project Type**: Web application with microservices backend

**Performance Goals**:
- Dashboard load: <3 seconds for 216-battery location view
- RUL prediction latency: <5 seconds at p95 for fleet query
- Sensor data ingestion: 32.4 req/s sustained (1,944 batteries × 60s sampling)
- WebSocket updates: <100ms message latency at 100 concurrent connections
- Database queries: <2 seconds for historical trend queries (30-day range)

**Constraints**:
- 99.9% uptime SLA (8.76 hours downtime/year maximum)
- Railway.com resource limits: Backend 1GB RAM/1CPU, ML 2GB RAM/2CPU, DB 4GB RAM/50GB storage
- Data retention: 2 years raw telemetry (compressed), 10 years aggregated metrics
- No on-premise infrastructure (100% cloud-native)
- Must handle Thai operational context: monsoon season grid instabilities, hot season temperature peaks (30-40°C), regional diversity (Chiangmai -2°C offset, Bangkok +1.5°C offset)

**Scale/Scope**:
- 1,944 batteries across 9 locations
- 1.02 billion time-series records per year (with compression: ~8GB/year)
- 50 concurrent dashboard users (facility engineers + managers)
- 5 concurrent simulations maximum
- 6 microservices (Frontend, Backend API, ML Pipeline, Digital Twin, Sensor Simulator, TimescaleDB)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Mission-Critical Operations

- [x] **Fail-safe defaults implemented**: Hybrid prediction fusion (Digital Twin + ML) ensures conservative estimates. If ML confidence <50%, weight shifts to Digital Twin (physics-based, inherently conservative).
- [x] **No silent failures**: All RUL predictions include confidence intervals (High/Medium/Low). Low-confidence predictions flagged with "Manual Review Required" alert.
- [x] **Data validation**: Backend validates sensor readings against VRLA physical limits (voltage 10-15V, temperature 10-50°C). Out-of-range readings rejected as "Sensor Malfunction" alerts.
- [x] **Accuracy over speed**: ML models validated on 90-day held-out test set (MAE <10%, R² >0.80) before deployment. Prediction endpoint includes model version + test metrics in response.

### ✅ Real-Time Reliability

- [x] **99.9% uptime SLA**: Railway.com health checks every 30s via `/health` endpoint. Auto-restart on 3 consecutive failures. Circuit breakers for DB timeouts.
- [x] **Sub-5-second latency**: RUL predictions cached (60-minute TTL), indexed queries on battery_id + timestamp. Async task queue for batch predictions.
- [x] **Graceful degradation**: If ML service fails, Backend API falls back to cached predictions or Digital Twin physics-only mode (FR-039).
- [x] **Health checks**: All services expose `/health` (liveliness) and `/ready` (readiness) endpoints per Railway.com requirements.

### ✅ Production Safety

- [x] **Staged rollouts**: Deployment workflow: PR → Staging environment (Railway preview deployments) → Production with Railway.com canary releases.
- [x] **Feature flags**: ML model selection via environment variable `ML_MODEL_VERSION`. Toggle between v1/v2 without redeployment.
- [x] **Rollback plan**: Railway.com maintains deployment history. One-click rollback via CLI: `railway rollback`.
- [x] **Data immutability**: RUL predictions stored with `prediction_timestamp` + `model_version`. Never update existing predictions, only insert new rows.
- [x] **Change log**: Model registry table logs: version, training_date, test_mae, test_r2, training_data_range, approved_by, approved_at.

### ✅ Observability First

- [x] **Structured logging**: Python `structlog` with JSON output: timestamp, level, service, battery_id, location, message, duration_ms, correlation_id.
- [x] **Distributed tracing**: Correlation IDs passed via HTTP headers (X-Correlation-ID) across all microservice calls.
- [x] **Real-time dashboard**: React frontend with:
  - Fleet overview cards (9 locations)
  - Battery health heatmap (color by SOH: green >85%, yellow 80-85%, red <80%)
  - RUL distribution histogram
  - Active alerts feed (WebSocket real-time stream)
  - Thai map overlay with regional temperatures
- [x] **Operational metrics**: Backend exposes Prometheus `/metrics` endpoint tracking:
  - Prediction latency (histogram with p50/p95/p99 buckets)
  - Model accuracy drift (MAE computed on 7-day rolling window of actuals vs predictions)
  - Alert volume counters (by severity, location)
  - Sensor data gap percentage (missing intervals / expected intervals)
  - WebSocket connection count gauge
- [x] **Automated alerting**: Backend checks every 15 minutes:
  - Model MAE >15% → Alert to operations channel
  - Any location >10% missing sensor data >1 hour → Sensor connectivity alert
  - RUL sudden drop >30 days → Data anomaly review alert
  - Critical battery (SOH <80%) + RUL <90 days → Replacement urgent alert
  - HVAC failure (temperature spike +10°C in <30 min) → Environmental alert
- [x] **Audit trail**: All control panel actions logged to `audit_log` table: user_id, action_type, timestamp, parameters_json, ip_address.

### ✅ Temperature-Aware ML

- [x] **Location-specific baselines**: Training dataset includes 90-day data from Chiangmai (northern region, -2°C offset). Production deployment requires multi-location training data (all 5 regions).
- [x] **Arrhenius validation**: Post-training validation script checks: for +10°C temperature increase, predicted RUL should decrease ~40-50%. Violations halt deployment.
- [x] **Seasonal adjustment**: ML features include `season` categorical (hot/rainy/cool) based on month. Models learn seasonal degradation patterns.
- [x] **HVAC failure detection**: Backend monitors temperature rate-of-change. Spike >2°C per 10 minutes triggers immediate "HVAC Degradation Suspected" alert + RUL recalculation for affected batteries.
- [x] **Feature requirements**: Feature engineering pipeline computes:
  - `temperature_mean_30d`: Rolling 30-day average (calendar aging proxy)
  - `temperature_max`: Peak temperature in observation window (stress events)
  - `time_above_30C_hours`: Cumulative hours >30°C (accelerated aging)
  - `temperature_cycles_count`: Number of temperature swings >5°C (thermal fatigue)

### ✅ Facility Engineering Expertise

- [x] **Actionable thresholds**: Alerts use manufacturer specs + Thai facility standards:
  - Float voltage: 13.50-13.80V (HX12-120 VRLA spec)
  - SOH warning: <85% (replace within next 2 quarterly maintenance windows = 6 months)
  - SOH critical: <80% (replace within next quarterly window = 3 months max)
  - Resistance drift: >50% increase from installation baseline (immediate investigation)
- [x] **Maintenance-aligned predictions**: RUL output converted to "Suggested Replacement Quarter" aligned with facility quarterly maintenance schedule (Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec).
- [x] **Thai operational context**: System accounts for:
  - Monsoon season (Jun-Oct): Alert aggregation increased (suppress duplicate alerts during grid instability), deferred non-critical maintenance recommendations
  - Songkran (mid-April): RUL predictions note "Holiday staffing constraints - consider early/late April for replacements"
  - Business hours (8am-8pm): Maintenance scheduler only suggests daytime windows
- [x] **No black boxes**: Every RUL prediction includes:
  - Top 3 contributing factors with % breakdown (e.g., "High temp +42%, Cycling stress +28%, Calendar age +18%")
  - Confidence level: High (>80% similar cases), Medium (60-80%), Low (<60%)
  - Similar historical cases: "Battery B-07 at Bangrak had similar degradation pattern, failed after 4.2 months (predicted 5.1 months)"

### ✅ Railway.com Cloud-Native Architecture

- [x] **Microservices design**: 6 services as documented in constitution topology diagram (Frontend, Backend API, ML Pipeline, Digital Twin, Sensor Simulator, TimescaleDB)
- [x] **Service communication**: Railway.com internal networking via private URLs (e.g., `http://backend-api.railway.internal`). External API calls use HTTPS only.
- [x] **Environment configs**: All secrets managed via Railway.com environment variables:
  - `DATABASE_URL`: TimescaleDB connection string (auto-injected by Railway)
  - `JWT_SECRET_KEY`: Authentication token signing key
  - `ML_MODEL_VERSION`: Feature flag for model selection
  - `REDIS_URL`: Optional caching layer (if deployed)
- [x] **Autoscaling**: Backend API is stateless (no session storage, JWT tokens, shared-nothing). Railway.com horizontal scaling enabled (2-4 instances based on CPU >70%).
- [x] **Database migrations**: Alembic migration scripts in `backend/alembic/versions/`. CI/CD pipeline tests migrations on staging database first. Each migration includes `downgrade()` for rollback.
- [x] **Health checks**: All services implement:
  - `/health`: Returns 200 OK if service running (liveliness probe)
  - `/ready`: Returns 200 OK if service + dependencies ready (readiness probe - checks DB connection for Backend API)
- [x] **Resource limits**: Railway.com service configs:
  - Frontend: 512MB RAM, 0.5 CPU (static SPA, minimal resources)
  - Backend API: 1GB RAM, 1 CPU (scale to 2GB if p95 latency >5s)
  - ML Pipeline: 2GB RAM, 2 CPU (CatBoost inference + feature engineering)
  - Digital Twin: 1GB RAM, 1 CPU (NumPy EKF computations)
  - Sensor Simulator: 512MB RAM, 0.5 CPU (lightweight data generation)
  - TimescaleDB: 4GB RAM, 2 CPU, 50GB storage (time-series workload)

### Gate Status: ✅ ALL GATES PASSED

No complexity justification required. Architecture aligns with constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/001-railway-deployment/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions and best practices
├── data-model.md        # Phase 1: Entity models and relationships
├── quickstart.md        # Phase 1: Developer setup guide
├── contracts/           # Phase 1: API contracts (OpenAPI specs)
│   ├── backend-api.yaml
│   ├── ml-pipeline.yaml
│   ├── digital-twin.yaml
│   └── sensor-simulator.yaml
└── tasks.md             # Phase 2: Implementation task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routes/              # FastAPI route handlers
│   │   │   ├── batteries.py     # Battery CRUD + health endpoints
│   │   │   ├── predictions.py   # RUL prediction queries
│   │   │   ├── alerts.py        # Alert management
│   │   │   ├── telemetry.py     # Sensor data ingestion
│   │   │   ├── simulations.py   # Simulation control
│   │   │   └── websocket.py     # Real-time WebSocket connections
│   │   ├── middleware/          # CORS, auth, logging
│   │   └── dependencies.py      # Dependency injection (DB sessions, auth)
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── battery.py
│   │   ├── telemetry.py         # TimescaleDB hypertable
│   │   ├── prediction.py
│   │   ├── alert.py
│   │   └── user.py
│   ├── services/                # Business logic layer
│   │   ├── battery_service.py
│   │   ├── prediction_service.py
│   │   ├── alert_service.py
│   │   └── fusion_service.py   # Hybrid ML + Digital Twin fusion
│   ├── schemas/                 # Pydantic request/response models
│   ├── core/                    # Config, security, database
│   │   ├── config.py           # Settings from environment variables
│   │   ├── database.py         # SQLAlchemy session management
│   │   └── security.py         # JWT authentication
│   └── main.py                 # FastAPI application entry point
├── alembic/                    # Database migrations
│   └── versions/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── requirements.txt

ml-pipeline/
├── src/
│   ├── training/
│   │   ├── train_model.py      # CatBoost training script
│   │   └── evaluate.py         # Model evaluation metrics
│   ├── inference/
│   │   ├── predict.py          # RUL prediction endpoint
│   │   └── feature_engineering.py  # Compute ML features from raw telemetry
│   ├── api/
│   │   └── main.py             # FastAPI service for ML endpoints
│   └── models/                 # Trained model artifacts (.cbm files)
├── tests/
└── requirements.txt

digital-twin/
├── src/
│   ├── ecm/
│   │   ├── battery_model.py    # Equivalent Circuit Model (R0, R1/C1, R2/C2, OCV)
│   │   └── ekf.py              # Extended Kalman Filter state estimation
│   ├── api/
│   │   └── main.py             # FastAPI service for Digital Twin endpoints
│   └── utils/
│       └── arrhenius.py        # Temperature acceleration functions
├── tests/
└── requirements.txt

sensor-simulator/
├── src/
│   ├── scenarios/
│   │   ├── power_outage.py
│   │   ├── hvac_failure.py
│   │   ├── temperature_spike.py
│   │   └── battery_aging.py
│   ├── generator.py            # Telemetry data generation engine
│   ├── api/
│   │   └── main.py             # FastAPI service for simulation control
│   └── models/
│       └── degradation.py      # Battery degradation physics
├── tests/
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── FleetOverview.tsx
│   │   │   ├── LocationDashboard.tsx
│   │   │   ├── BatteryDetail.tsx
│   │   │   └── BatteryHeatmap.tsx
│   │   ├── Alerts/
│   │   │   ├── AlertFeed.tsx
│   │   │   └── AlertAcknowledgment.tsx
│   │   ├── Charts/
│   │   │   ├── TrendChart.tsx
│   │   │   ├── RULHistogram.tsx
│   │   │   └── TemperatureMap.tsx
│   │   └── ControlPanel/
│   │       ├── SimulationControl.tsx
│   │       └── ScenarioBuilder.tsx
│   ├── pages/
│   │   ├── FleetDashboard.tsx
│   │   ├── LocationDashboard.tsx
│   │   ├── BatteryDetails.tsx
│   │   ├── HistoricalAnalysis.tsx
│   │   └── ControlPanel.tsx
│   ├── services/
│   │   ├── api.ts              # Axios HTTP client
│   │   ├── websocket.ts        # Socket.IO client for real-time updates
│   │   └── auth.ts             # Authentication service
│   ├── hooks/
│   │   ├── useRealTimeUpdates.ts
│   │   ├── useBatteryData.ts
│   │   └── useAlerts.ts
│   ├── stores/                 # Zustand state management
│   │   ├── authStore.ts
│   │   └── simulationStore.ts
│   └── main.tsx                # Vite + React entry point
├── tests/
│   └── e2e/                   # Playwright tests
└── package.json

database/
├── init.sql                   # TimescaleDB initialization (hypertable creation)
└── migrations/                # Alembic migrations (also in backend/)
```

**Structure Decision**: Web application with microservices backend. Chose this structure because:
1. Frontend and Backend are independently deployable services on Railway.com
2. ML Pipeline and Digital Twin are separate services for independent scaling (ML is compute-heavy during batch predictions, Digital Twin is lightweight real-time)
3. Sensor Simulator is standalone for testing isolation (can deploy/undeploy without affecting production)
4. Separation allows different technology stacks (Frontend: TypeScript/React, Backend/ML: Python/FastAPI)

## Complexity Tracking

> No violations of constitution complexity gates. Table not applicable.

## Phase 0: Research & Decisions

See [research.md](./research.md) for detailed research findings on:
- Railway.com deployment best practices for microservices
- TimescaleDB time-series optimization (hypertable partitioning, compression policies, retention policies)
- FastAPI WebSocket implementation for real-time dashboard updates
- CatBoost hyperparameter tuning for time-series regression (RUL prediction)
- Hybrid prediction fusion algorithms (weighted average vs Bayesian vs adaptive)
- React state management for real-time data (TanStack Query + Socket.IO)
- Battery ECM/EKF implementation patterns for VRLA chemistry

## Phase 1: Design Artifacts

- **Data Model**: See [data-model.md](./data-model.md) for entity definitions, relationships, and TimescaleDB schema
- **API Contracts**: See [contracts/](./contracts/) for OpenAPI 3.1 specifications
- **Developer Setup**: See [quickstart.md](./quickstart.md) for local development environment setup

## Implementation Notes

### Critical Path Dependencies

1. **TimescaleDB setup first**: Database schema must exist before backend can start. Alembic migrations create hypertables.
2. **Backend API before Frontend**: Frontend depends on Backend API endpoints + WebSocket server.
3. **Sensor Simulator parallel**: Can develop/test independently, deployed separately for demo/testing scenarios.
4. **ML Pipeline after Backend**: ML service calls Backend API to store predictions in database.
5. **Digital Twin parallel with ML**: Independent prediction service, Backend API calls both ML and Digital Twin for fusion.

### Railway.com Deployment Order

1. Deploy TimescaleDB (Railway.com PostgreSQL plugin with TimescaleDB enabled)
2. Deploy Backend API (runs Alembic migrations on startup)
3. Deploy ML Pipeline (reads trained model from `/models` directory)
4. Deploy Digital Twin service
5. Deploy Sensor Simulator (optional, for demo/testing)
6. Deploy Frontend (points to Backend API via environment variable `VITE_API_URL`)

### Testing Strategy

- **Unit tests**: Each service has unit tests (pytest for Python, Vitest for TypeScript)
- **Integration tests**: Backend tests with real TimescaleDB instance (Railway.com preview database)
- **Contract tests**: Pact consumer/provider tests between Frontend ↔ Backend, Backend ↔ ML Pipeline
- **E2E tests**: Playwright tests covering critical user flows (view dashboard, acknowledge alert, run simulation)
- **Load tests**: Locust scripts simulating 32.4 req/s sensor data ingestion + 50 concurrent dashboard users

### Monitoring & Observability

- **Railway.com built-in**: Service logs (stdout/stderr), deployment history, resource usage graphs
- **Custom Prometheus metrics**: Backend API exposes `/metrics` endpoint (prediction latency, model accuracy drift, alert volume)
- **Structured logging**: All services use JSON logging for centralized log aggregation
- **Health checks**: Railway.com monitors `/health` and `/ready` endpoints, auto-restarts unhealthy services

## Next Steps

After `/speckit.plan` completes (Phase 0 + Phase 1), run `/speckit.tasks` to generate detailed implementation task breakdown in `tasks.md`.
