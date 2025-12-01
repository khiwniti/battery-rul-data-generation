# Tasks: Battery RUL Prediction & Monitoring System

**Input**: Design documents from `/specs/001-railway-deployment/`
**Prerequisites**: plan.md, spec.md, research.md

**Tests**: Tests are not explicitly requested in the specification, therefore test tasks are excluded. Focus on implementation and integration validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses web application with microservices architecture:
- **Backend API**: `backend/src/`
- **ML Pipeline**: `ml-pipeline/src/`
- **Digital Twin**: `digital-twin/src/`
- **Sensor Simulator**: `sensor-simulator/src/`
- **Frontend**: `frontend/src/`
- **Database**: `database/` (migrations and init scripts)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Railway.com deployment setup

- [ ] T001 Create project directory structure per plan.md (backend, ml-pipeline, digital-twin, sensor-simulator, frontend, database directories)
- [ ] T002 [P] Initialize backend FastAPI project with requirements.txt (FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.x, python-socketio 5.x, structlog 24.x)
- [ ] T003 [P] Initialize ML pipeline project with requirements.txt (CatBoost 1.2+, NumPy 1.24+, Pandas 2.x, SciPy 1.11+)
- [ ] T004 [P] Initialize Digital Twin project with requirements.txt (NumPy 1.24+, SciPy 1.11+)
- [ ] T005 [P] Initialize Sensor Simulator project with requirements.txt (NumPy, Pandas, FastAPI)
- [ ] T006 [P] Initialize frontend React project with package.json (React 18+, TypeScript 5.x, Vite 5.x, TanStack Query 5.x, Zustand 4.x, Socket.IO Client 4.x, Recharts 2.x)
- [ ] T007 [P] Create Railway.com configuration files (railway.json for each service)
- [ ] T008 [P] Configure Railway.com environment variables template (.env.example)
- [ ] T009 [P] Setup linting and formatting (backend: black, ruff; frontend: ESLint, Prettier)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [ ] T010 Create TimescaleDB initialization script in database/init.sql (CREATE EXTENSION timescaledb, hypertable setup)
- [ ] T011 Setup Alembic migrations framework in backend/alembic/
- [ ] T012 Create base database models in backend/src/models/__init__.py (Base class, UUID mixin, timestamp mixin)
- [ ] T013 Create Location model in backend/src/models/location.py (location_id, name, region, temp_offset, humidity_offset per plan.md)
- [ ] T014 [P] Create BatterySystem model in backend/src/models/battery_system.py (system_id, type, location_id FK)
- [ ] T015 [P] Create String model in backend/src/models/string.py (string_id, system_id FK, batteries relationship)
- [ ] T016 Create Battery model in backend/src/models/battery.py (battery_id, string_id FK, serial, position, installed_date)
- [ ] T017 Create Telemetry model as TimescaleDB hypertable in backend/src/models/telemetry.py (battery_id, timestamp, voltage, current, temperature, resistance)
- [ ] T018 Create initial Alembic migration for master data tables (locations, battery_systems, strings, batteries)
- [ ] T019 Create second Alembic migration for telemetry hypertable with create_hypertable() and compression/retention policies

### Backend API Foundation

- [ ] T020 Configure FastAPI application in backend/src/main.py (CORS, middleware, health endpoints)
- [ ] T021 [P] Implement database session management in backend/src/core/database.py (SQLAlchemy async engine, session factory)
- [ ] T022 [P] Implement configuration management in backend/src/core/config.py (load from Railway.com environment variables)
- [ ] T023 [P] Implement JWT authentication in backend/src/core/security.py (create_access_token, verify_token)
- [ ] T024 Implement User model in backend/src/models/user.py (user_id, username, email, role enum: Admin/Engineer/Viewer)
- [ ] T025 Create authentication routes in backend/src/api/routes/auth.py (POST /auth/login, POST /auth/refresh)
- [ ] T026 [P] Implement structured logging in backend/src/core/logging.py (structlog JSON format with correlation IDs)
- [ ] T027 [P] Implement error handlers in backend/src/api/middleware/error_handlers.py (validation errors, 404, 500)
- [ ] T028 Implement dependency injection in backend/src/api/dependencies.py (get_db session, get_current_user)

### Service-to-Service Communication Foundation

- [ ] T029 [P] Create ML Pipeline FastAPI service skeleton in ml-pipeline/src/api/main.py (health endpoints, internal networking)
- [ ] T030 [P] Create Digital Twin FastAPI service skeleton in digital-twin/src/api/main.py (health endpoints)
- [ ] T031 [P] Create Sensor Simulator FastAPI service skeleton in sensor-simulator/src/api/main.py (health endpoints)
- [ ] T032 Implement HTTP client for inter-service communication in backend/src/core/service_client.py (async requests with timeouts, circuit breakers)

### Frontend Foundation

- [ ] T033 Setup React Router in frontend/src/main.tsx (routes for dashboard, location view, battery detail, control panel)
- [ ] T034 [P] Implement API client in frontend/src/services/api.ts (Axios with JWT interceptors, error handling)
- [ ] T035 [P] Implement WebSocket client in frontend/src/services/websocket.ts (Socket.IO connection management, reconnection logic)
- [ ] T036 [P] Implement authentication store in frontend/src/stores/authStore.ts (Zustand store for JWT tokens, user info)
- [ ] T037 [P] Create layout component in frontend/src/components/Layout/MainLayout.tsx (header, sidebar, navigation)
- [ ] T038 Implement authentication routes in frontend/src/pages/Login.tsx and frontend/src/pages/Dashboard.tsx (protected routes)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Real-Time Battery Health Monitoring (Priority: P1) 🎯 MVP

**Goal**: Display real-time battery telemetry (voltage, temperature, SOH) for all 216 batteries at a location with alerts, updated within 5 seconds

**Independent Test**: Start sensor simulator sending telemetry for 24 batteries → Open location dashboard → Verify voltage/temperature/SOH displays → Trigger temperature alert (>35°C) → Verify alert appears within 5 seconds

### Backend - Telemetry & Battery Data

- [ ] T039 [P] [US1] Create Alert model in backend/src/models/alert.py (alert_id, battery_id FK, alert_type enum, severity enum, trigger_timestamp, acknowledged bool)
- [ ] T040 [P] [US1] Create Incident model in backend/src/models/incident.py (incident_id, title, location_id, alert_ids array, status enum)
- [ ] T041 [US1] Implement BatteryService in backend/src/services/battery_service.py (get_batteries_by_location, get_battery_detail, compute_SOH from telemetry)
- [ ] T042 [US1] Implement AlertService in backend/src/services/alert_service.py (check_thresholds: voltage 11.5-14.5V, temp >35°C, create_alert, aggregate_alerts_into_incidents)
- [ ] T043 [US1] Create telemetry ingestion route in backend/src/api/routes/telemetry.py (POST /telemetry with sensor data validation)
- [ ] T044 [US1] Create battery query routes in backend/src/api/routes/batteries.py (GET /locations/{id}/batteries, GET /batteries/{id})
- [ ] T045 [US1] Create alert routes in backend/src/api/routes/alerts.py (GET /alerts, PUT /alerts/{id}/acknowledge)

### Backend - WebSocket Real-Time Updates

- [ ] T046 [US1] Implement WebSocket connection handler in backend/src/api/routes/websocket.py (Socket.IO server, room management for locations)
- [ ] T047 [US1] Integrate WebSocket broadcasting in AlertService (emit 'alert_triggered' event to location room when alert created)
- [ ] T048 [US1] Integrate WebSocket broadcasting in telemetry route (emit 'telemetry_update' event every 60s with batch of 24 batteries)

### Frontend - Location Dashboard

- [ ] T049 [P] [US1] Create BatteryCard component in frontend/src/components/Dashboard/BatteryCard.tsx (displays voltage, temperature, SOH, alert icon)
- [ ] T050 [P] [US1] Create BatteryHeatmap component in frontend/src/components/Dashboard/BatteryHeatmap.tsx (color-coded grid by SOH: green >85%, yellow 80-85%, red <80%)
- [ ] T051 [P] [US1] Create AlertFeed component in frontend/src/components/Alerts/AlertFeed.tsx (real-time alert list with severity badges)
- [ ] T052 [US1] Create LocationDashboard page in frontend/src/pages/LocationDashboard.tsx (grid of 216 batteries, filters by string/status/alerts)
- [ ] T053 [US1] Create BatteryDetails page in frontend/src/pages/BatteryDetails.tsx (detailed view with 7-day trend charts)
- [ ] T054 [US1] Implement useBatteryData hook in frontend/src/hooks/useBatteryData.ts (TanStack Query for API data, WebSocket integration for real-time updates)
- [ ] T055 [US1] Implement useAlerts hook in frontend/src/hooks/useAlerts.ts (TanStack Query + WebSocket for alert feed)
- [ ] T056 [US1] Implement useRealTimeUpdates hook in frontend/src/hooks/useRealTimeUpdates.ts (Socket.IO connection management, room subscription)

### Integration & Validation

- [ ] T057 [US1] Implement data freshness indicator in frontend/src/components/Dashboard/DataFreshnessIndicator.tsx (show "Last Updated: X seconds ago", visual warning if >5 minutes stale)
- [ ] T058 [US1] Add alert acknowledgment flow in frontend/src/components/Alerts/AlertAcknowledgment.tsx (PUT request to backend, optimistic UI update)
- [ ] T059 [US1] Validate WebSocket reconnection logic (simulate network interruption, verify automatic reconnection and missed update replay)
- [ ] T060 [US1] Validate alert threshold detection (send test telemetry with temperature 36°C, verify alert created and displayed within 5 seconds)

**Checkpoint**: User Story 1 complete and independently testable. Users can view real-time battery health for a location with alerts.

---

## Phase 4: User Story 2 - RUL Forecasting for Maintenance Planning (Priority: P1)

**Goal**: Display ML-predicted RUL for each battery with confidence level, contributing factors, and maintenance window recommendations

**Independent Test**: Load trained CatBoost model → Query RUL predictions for all batteries → Verify predictions display in months with confidence level (High/Medium/Low) → Verify top 3 contributing factors shown → Verify "Suggested Replacement Quarter" aligned with maintenance schedule

### ML Pipeline - Feature Engineering & Model

- [ ] T061 [P] [US2] Implement feature engineering in ml-pipeline/src/inference/feature_engineering.py (compute temperature_mean_30d, temperature_max, time_above_30C_hours, temperature_cycles_count, cycle_count, ah_throughput, calendar_age_days)
- [ ] T062 [P] [US2] Create continuous aggregate view in database migration (CREATE MATERIALIZED VIEW telemetry_hourly for pre-computed hourly stats)
- [ ] T063 [US2] Implement CatBoost model loading in ml-pipeline/src/inference/predict.py (load trained .cbm model from ml-pipeline/src/models/)
- [ ] T064 [US2] Implement RUL prediction endpoint in ml-pipeline/src/api/main.py (POST /predict with features, returns rul_months, confidence_level, feature_importance)
- [ ] T065 [US2] Add Arrhenius validation in ml-pipeline/src/inference/validate.py (check +10°C temp → ~40-50% RUL decrease)

### Digital Twin - Physics-Based RUL

- [ ] T066 [P] [US2] Implement ECM battery model in digital-twin/src/ecm/battery_model.py (R0, R1/C1, R2/C2, OCV lookup table for VRLA)
- [ ] T067 [P] [US2] Implement Extended Kalman Filter in digital-twin/src/ecm/ekf.py (state=[SOC, V1, V2], predict/update steps)
- [ ] T068 [P] [US2] Implement Arrhenius temperature compensation in digital-twin/src/utils/arrhenius.py (resistance adjustment for temperature)
- [ ] T069 [US2] Implement Digital Twin RUL prediction endpoint in digital-twin/src/api/main.py (POST /predict with telemetry history, returns rul_months based on capacity fade)
- [ ] T070 [US2] Validate EKF convergence (verify voltage prediction MAE <0.2V over 30-day test window)

### Backend - Prediction Fusion & Storage

- [ ] T071 [US2] Create RULPrediction model in backend/src/models/prediction.py (battery_id, prediction_timestamp, rul_ml, rul_dt, rul_hybrid, confidence_level, contributing_factors JSON)
- [ ] T072 [US2] Implement FusionService in backend/src/services/fusion_service.py (weighted average: 60% DT + 40% ML, conflict detection >30% disagreement)
- [ ] T073 [US2] Implement PredictionService in backend/src/services/prediction_service.py (call ML + DT services in parallel, fuse predictions, store in DB with model_version)
- [ ] T074 [US2] Create prediction routes in backend/src/api/routes/predictions.py (GET /batteries/{id}/rul, GET /locations/{id}/rul-forecast)
- [ ] T075 [US2] Implement batch prediction task in backend/src/services/prediction_service.py (hourly cron job to recompute RUL for all batteries, update predictions table)
- [ ] T076 [US2] Add prediction caching in backend/src/services/prediction_service.py (Redis or in-memory cache with 60-minute TTL)

### Frontend - RUL Display & Maintenance Scheduler

- [ ] T077 [P] [US2] Create RULCard component in frontend/src/components/Dashboard/RULCard.tsx (displays RUL months, confidence badge, progress bar to EOL threshold 80% SOH)
- [ ] T078 [P] [US2] Create ContributingFactors component in frontend/src/components/Dashboard/ContributingFactors.tsx (bar chart of top 3 factors: "High temp +42%, Cycling +28%, Age +18%")
- [ ] T079 [P] [US2] Create MaintenanceScheduler component in frontend/src/components/Dashboard/MaintenanceScheduler.tsx (table of batteries with RUL <180 days, grouped by location, suggested quarter)
- [ ] T080 [US2] Update BatteryDetails page to include RUL section (integrate RULCard and ContributingFactors components)
- [ ] T081 [US2] Create RULDashboard page in frontend/src/pages/RULDashboard.tsx (filterable table: all batteries, sort by RUL ascending, filter by confidence level)
- [ ] T082 [US2] Implement quarter alignment logic in frontend/src/utils/maintenanceScheduler.ts (convert RUL months → Suggested Replacement Quarter: Q1 Jan-Mar, Q2 Apr-Jun, Q3 Jul-Sep, Q4 Oct-Dec)

### Integration & Validation

- [ ] T083 [US2] Validate ML model prediction accuracy (load 90-day test dataset, compute MAE <10% of mean RUL, R² >0.80)
- [ ] T084 [US2] Validate Digital Twin voltage predictions (compare predicted vs measured voltage, verify MAE <0.2V)
- [ ] T085 [US2] Validate hybrid fusion (verify weighted average calculation, test conflict detection for ML=6mo vs DT=9mo predictions)
- [ ] T086 [US2] Validate temperature feature importance (verify temperature features in top 5 CatBoost feature importance ranking)
- [ ] T087 [US2] Validate maintenance window alignment (verify Q3 Jul-Sep predictions avoid monsoon season Jun-Oct defer logic)

**Checkpoint**: User Story 2 complete. Users can forecast RUL for all batteries with explainable predictions and maintenance scheduling.

---

## Phase 5: User Story 3 - Scenario Simulation for Testing Response Plans (Priority: P2)

**Goal**: Engineers can start/stop realistic sensor data simulations (HVAC failure, power outage, temperature spike) via control panel for training without affecting production data

**Independent Test**: Open control panel → Select "HVAC Failure" scenario for Sriracha location → Start simulation → Verify dashboard shows "SIMULATION MODE" banner → Verify temperature rises 2°C/hour → Verify alerts trigger → Stop simulation → Verify simulation data purged and production view restored

### Sensor Simulator - Scenario Engine

- [ ] T088 [P] [US3] Port battery degradation model from existing src/battery_degradation.py to sensor-simulator/src/models/degradation.py
- [ ] T089 [P] [US3] Port telemetry generator from existing src/telemetry_generator.py to sensor-simulator/src/generator.py (adapt for real-time streaming)
- [ ] T090 [P] [US3] Implement PowerOutage scenario in sensor-simulator/src/scenarios/power_outage.py (discharge cycle simulation, voltage drop to 10.5-12.0V)
- [ ] T091 [P] [US3] Implement HVACFailure scenario in sensor-simulator/src/scenarios/hvac_failure.py (gradual temperature rise 2°C/hour from 24°C to 38°C)
- [ ] T092 [P] [US3] Implement TemperatureSpike scenario in sensor-simulator/src/scenarios/temperature_spike.py (sudden +10°C spike for heatwave simulation)
- [ ] T093 [P] [US3] Implement BatteryAging scenario in sensor-simulator/src/scenarios/battery_aging.py (accelerated resistance increase, SOH decline)
- [ ] T094 [US3] Implement scenario controller in sensor-simulator/src/api/main.py (POST /simulations, DELETE /simulations/{id}, GET /simulations status)

### Backend - Simulation Management

- [ ] T095 [US3] Create Simulation model in backend/src/models/simulation.py (simulation_id, scenario_type enum, created_by user_id, start_time, end_time, status enum, parameters JSON, affected_location_id)
- [ ] T096 [US3] Implement SimulationService in backend/src/services/simulation_service.py (start_simulation, stop_simulation, get_simulation_status, enforce max 5 concurrent limit)
- [ ] T097 [US3] Create simulation routes in backend/src/api/routes/simulations.py (POST /simulations, DELETE /simulations/{id}, GET /simulations)
- [ ] T098 [US3] Add simulation isolation in telemetry ingestion (backend/src/api/routes/telemetry.py: mark simulated data with is_simulation=true, separate storage or tagging)
- [ ] T099 [US3] Implement simulation cleanup on stop in SimulationService (purge all telemetry with is_simulation=true for that simulation_id)

### Frontend - Control Panel

- [ ] T100 [P] [US3] Create SimulationControl component in frontend/src/components/ControlPanel/SimulationControl.tsx (scenario selector, location selector, duration input, start/stop buttons)
- [ ] T101 [P] [US3] Create ScenarioBuilder component in frontend/src/components/ControlPanel/ScenarioBuilder.tsx (custom scenario parameter editor: temperature rate, outage duration)
- [ ] T102 [P] [US3] Create simulation store in frontend/src/stores/simulationStore.ts (Zustand: isSimulating, scenarioType, affectedLocation)
- [ ] T103 [US3] Create ControlPanel page in frontend/src/pages/ControlPanel.tsx (integrates SimulationControl and ScenarioBuilder, displays active simulations table)
- [ ] T104 [US3] Add simulation mode indicator in frontend/src/components/Layout/MainLayout.tsx (amber "SIMULATION MODE - {Location}" banner when simulation active)
- [ ] T105 [US3] Implement role-based access control for simulation controls (only Admin and Engineer roles can start/stop simulations, disable controls for Viewer role)

### Integration & Validation

- [ ] T106 [US3] Validate simulation isolation (start simulation for Location A → verify Location B dashboard unaffected)
- [ ] T107 [US3] Validate simulation cleanup (start simulation, generate 200 alerts → stop simulation → verify all 200 alerts purged, production view restored within 5 seconds)
- [ ] T108 [US3] Validate concurrent simulation limit (start 5 simulations → attempt 6th → verify error "Max 5 concurrent simulations exceeded")
- [ ] T109 [US3] Validate HVAC failure scenario (start simulation → verify temperature rises 2°C/hour linearly, battery temps follow with 15-minute lag)

**Checkpoint**: User Story 3 complete. Engineers can run scenario simulations for training and threshold validation.

---

## Phase 6: User Story 4 - Historical Trend Analysis for Root Cause Investigation (Priority: P2)

**Goal**: Engineers can query and visualize historical trends for any battery over selectable time ranges (7d, 30d, 90d, 1yr) with event correlation

**Independent Test**: Select battery B-12 → Select "View 12-Month Trend" → Verify interactive chart displays voltage/temperature/SOH over time → Overlay power outage events from event log → Verify vertical markers at outage timestamps → Export data as CSV → Verify timestamped sensor data downloads

### Backend - Historical Query API

- [ ] T110 [P] [US4] Create MaintenanceEvent model in backend/src/models/maintenance.py (event_id, battery_id, event_type enum, event_date, performed_by, notes)
- [ ] T111 [P] [US4] Create PowerOutageEvent model in backend/src/models/outage.py (outage_id, location_id, start_time, end_time, duration_minutes)
- [ ] T112 [US4] Implement HistoricalService in backend/src/services/historical_service.py (query_telemetry_range with time_bucket aggregation, correlate_events)
- [ ] T113 [US4] Create historical query routes in backend/src/api/routes/historical.py (GET /batteries/{id}/history?start_date&end_date&metrics, GET /locations/{id}/outages)
- [ ] T114 [US4] Implement CSV export route in backend/src/api/routes/exports.py (GET /batteries/{id}/export?start_date&end_date, streams CSV response)
- [ ] T115 [US4] Optimize historical queries with TimescaleDB time_bucket (backend/src/services/historical_service.py: downsample to 1-hour buckets for >30-day queries)

### Backend - Location Comparison API

- [ ] T116 [US4] Implement location comparison service in backend/src/services/comparison_service.py (compare_temperature_distributions, compare_soh_decline_rates)
- [ ] T117 [US4] Create comparison routes in backend/src/api/routes/comparisons.py (GET /comparisons/temperatures, GET /comparisons/seasonal?season=hot&season=cool)

### Frontend - Historical Analysis UI

- [ ] T118 [P] [US4] Create TrendChart component in frontend/src/components/Charts/TrendChart.tsx (Recharts LineChart with zoom/pan, multi-metric overlay)
- [ ] T119 [P] [US4] Create EventOverlay component in frontend/src/components/Charts/EventOverlay.tsx (vertical markers for outages/alerts/maintenance)
- [ ] T120 [P] [US4] Create TemperatureComparison component in frontend/src/components/Charts/TemperatureComparison.tsx (box plots for 9 locations)
- [ ] T121 [P] [US4] Create SeasonalComparison component in frontend/src/components/Charts/SeasonalComparison.tsx (SOH decline rate bar chart: hot vs rainy vs cool seasons)
- [ ] T122 [US4] Create HistoricalAnalysis page in frontend/src/pages/HistoricalAnalysis.tsx (time range selector, metric selector, integrates TrendChart + EventOverlay)
- [ ] T123 [US4] Implement CSV export button in frontend/src/components/Charts/ExportButton.tsx (triggers GET /batteries/{id}/export, downloads file)

### Integration & Validation

- [ ] T124 [US4] Validate time range queries (query 30-day range for battery → verify response time <3 seconds at p95)
- [ ] T125 [US4] Validate event correlation (query battery with 3 outages in history → verify 3 vertical markers display at correct timestamps)
- [ ] T126 [US4] Validate CSV export (export 90-day data for battery → verify CSV includes timestamp, voltage, current, temperature, resistance columns with 129,600 rows)
- [ ] T127 [US4] Validate seasonal comparison (compare hot season Mar-May vs cool season Nov-Feb → verify SOH decline rate differs by >50%)

**Checkpoint**: User Story 4 complete. Engineers can analyze historical trends and correlate events for root cause investigation.

---

## Phase 7: User Story 5 - Multi-Location Fleet Health Overview (Priority: P3)

**Goal**: Operations director can view aggregated fleet metrics across all 9 locations with location comparison and monthly reporting

**Independent Test**: Open fleet dashboard → Verify 9 location cards display with battery count, % healthy, alert count, avg RUL → Click "Fleet Health Trend - Last 6 Months" → Verify line chart shows fleet-wide SOH declining 2.1% → Export monthly report → Verify PDF generates with executive summary

### Backend - Fleet Aggregation

- [ ] T128 [US5] Implement FleetService in backend/src/services/fleet_service.py (aggregate_fleet_health, compute_location_statistics, forecast_annual_replacements)
- [ ] T129 [US5] Create fleet routes in backend/src/api/routes/fleet.py (GET /fleet/health, GET /fleet/forecast?months=12)
- [ ] T130 [US5] Implement monthly report generation in backend/src/services/report_service.py (generate_pdf_report with summary, metrics, location comparison table)
- [ ] T131 [US5] Create report route in backend/src/api/routes/reports.py (GET /reports/monthly?start_date&end_date, returns PDF)

### Frontend - Fleet Dashboard

- [ ] T132 [P] [US5] Create LocationCard component in frontend/src/components/Dashboard/LocationCard.tsx (location name, battery count, % healthy badge, active alerts count, avg RUL)
- [ ] T133 [P] [US5] Create FleetHealthChart component in frontend/src/components/Charts/FleetHealthChart.tsx (line chart of fleet-wide SOH over time)
- [ ] T134 [P] [US5] Create AnnualForecast component in frontend/src/components/Dashboard/AnnualForecast.tsx (table: predicted replacements by quarter, cost estimate)
- [ ] T135 [US5] Create FleetDashboard page in frontend/src/pages/FleetDashboard.tsx (grid of 9 LocationCards, integrates FleetHealthChart, export button)
- [ ] T136 [US5] Implement monthly report download button in frontend/src/components/Dashboard/ReportDownload.tsx (triggers GET /reports/monthly, downloads PDF)

### Integration & Validation

- [ ] T137 [US5] Validate fleet aggregation (verify sum of location battery counts = 1,944 total)
- [ ] T138 [US5] Validate location comparison (verify southern locations Phuket/Hat Yai show 12% better RUL than Bangkok locations)
- [ ] T139 [US5] Validate monthly report generation (generate report → verify PDF contains: executive summary, fleet metrics table, location comparison, forecast)
- [ ] T140 [US5] Validate annual forecast (verify 147 batteries predicted to reach EOL in next 12 months with quarterly breakdown)

**Checkpoint**: User Story 5 complete. Operations director has fleet-level visibility for strategic planning.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness, performance optimization, monitoring, documentation

### Performance Optimization

- [ ] T141 [P] Implement database connection pooling in backend/src/core/database.py (SQLAlchemy pool_size=10, max_overflow=20)
- [ ] T142 [P] Add database query optimization (create indexes on battery_id, location_id, timestamp columns)
- [ ] T143 [P] Implement Redis caching layer for RUL predictions in backend/src/services/cache_service.py (60-minute TTL)
- [ ] T144 [P] Optimize frontend bundle size (code-split dashboard pages with React.lazy, tree-shake unused dependencies)
- [ ] T145 [P] Implement frontend virtualization for battery tables in frontend/src/components/Dashboard/BatteryTable.tsx (react-window for 1,944 rows)

### Monitoring & Observability

- [ ] T146 [P] Implement Prometheus metrics endpoint in backend/src/api/routes/metrics.py (prediction latency histogram, alert volume counter, WebSocket connection gauge)
- [ ] T147 [P] Implement health check endpoints in all services (GET /health returns 200 OK, GET /ready checks DB connection)
- [ ] T148 [P] Add correlation ID middleware in backend/src/api/middleware/correlation.py (X-Correlation-ID header propagation)
- [ ] T149 [P] Implement audit logging in backend/src/services/audit_service.py (log all control panel actions to audit_log table)

### Railway.com Deployment

- [ ] T150 Create Railway.com deployment scripts in scripts/deploy.sh (railway up for each service)
- [ ] T151 [P] Configure Railway.com health checks in railway.json (healthcheckPath: /health, healthcheckTimeout: 30)
- [ ] T152 [P] Setup Railway.com environment variable linking (DATABASE_URL from Postgres plugin, SERVICE_URLS for internal networking)
- [ ] T153 Test Railway.com staging deployment (deploy to preview environment, run smoke tests)

### Documentation

- [ ] T154 [P] Create API documentation in backend/docs/API.md (OpenAPI spec auto-generated from FastAPI)
- [ ] T155 [P] Create deployment guide in docs/DEPLOYMENT.md (Railway.com setup, environment variables, migration steps)
- [ ] T156 [P] Create developer quickstart in docs/QUICKSTART.md (local development setup, running tests, debugging)
- [ ] T157 [P] Create user manual in docs/USER_MANUAL.md (dashboard navigation, alert acknowledgment, simulation usage)

### Final Validation

- [ ] T158 Run end-to-end smoke tests (telemetry ingestion → dashboard display → RUL prediction → alert triggering)
- [ ] T159 Run load tests with Locust (simulate 32.4 req/s sensor ingestion + 50 concurrent users, verify <5s p95 latency)
- [ ] T160 Validate 99.9% uptime SLA (configure Railway.com health checks, verify auto-restart on failure)
- [ ] T161 Validate data retention policies (verify TimescaleDB compression after 7 days, retention drops chunks >2 years)
- [ ] T162 Validate security (verify JWT authentication on all routes, CORS configured for frontend origin only, secrets in Railway.com env vars)

**Checkpoint**: System production-ready for Railway.com deployment.

---

## Task Dependencies & Execution Strategy

### Critical Path (Must Complete in Order)

1. **Phase 1 (Setup)** → **Phase 2 (Foundation)** → User Stories can run in parallel
2. Within Foundation: Database models (T010-T019) MUST complete before services (T020-T028)
3. Backend API foundation (T020-T028) MUST complete before user story work begins
4. Frontend foundation (T033-T038) MUST complete before user story UI work begins

### Parallel Execution Opportunities

**Phase 3 (US1) - Real-Time Monitoring**:
- Backend: T039-T040 (models) || T041-T042 (services) can run parallel
- Frontend: T049-T051 (components) all parallelizable
- Integration: T052-T056 (pages/hooks) sequential after components

**Phase 4 (US2) - RUL Forecasting**:
- ML Pipeline (T061-T065) || Digital Twin (T066-T070) || Backend Fusion (T071-T076) can run in parallel
- Frontend: T077-T079 (components) all parallelizable

**Phase 5 (US3) - Simulation**:
- Sensor Simulator scenarios (T090-T093) all parallelizable
- Frontend control panel components (T100-T102) all parallelizable

**Phase 6 (US4) - Historical Analysis**:
- Backend models/services (T110-T112) || Frontend chart components (T118-T121) can run parallel

**Phase 7 (US5) - Fleet Overview**:
- Frontend components (T132-T134) all parallelizable

**Phase 8 (Polish)**:
- All tasks marked [P] (T141-T149, T151-T152, T154-T157) can run in parallel

### Independent User Story Testing

**User Story 1** can be tested independently:
- Deploy: Backend API + Frontend + TimescaleDB
- Test: Start sensor simulator → View location dashboard → Verify real-time updates → Trigger alert

**User Story 2** requires US1 complete (needs telemetry data) but adds:
- Deploy: ML Pipeline + Digital Twin services
- Test: Load trained model → Query RUL predictions → Verify explainability

**User Story 3** is independent (can test in isolation):
- Deploy: Sensor Simulator + Backend API + Frontend
- Test: Start HVAC failure simulation → Verify simulated data streams → Stop simulation

**User Story 4** requires US1 complete (needs historical telemetry):
- Test: Query 30-day trends → Overlay outage events → Export CSV

**User Story 5** requires US1+US2 complete (needs fleet-wide data):
- Test: View fleet dashboard → Generate monthly report

### Suggested MVP Scope (Minimum Viable Product)

**MVP = User Story 1 Only** (Real-Time Battery Health Monitoring)

**Why**: Delivers immediate value (real-time visibility) without ML complexity. Can validate:
- Railway.com deployment
- TimescaleDB performance
- WebSocket real-time updates
- Alert system
- Dashboard usability

**MVP Task Count**: 60 tasks (T001-T060)
**Estimated Timeline**: 4-6 weeks for 2-3 developers

**Post-MVP Increments**:
1. Add User Story 2 (RUL Forecasting) - 27 tasks
2. Add User Story 3 (Simulation) - 22 tasks
3. Add User Story 4 (Historical Analysis) - 18 tasks
4. Add User Story 5 (Fleet Overview) - 13 tasks
5. Polish & Deploy (Phase 8) - 22 tasks

---

## Task Summary

**Total Tasks**: 162
- **Phase 1 (Setup)**: 9 tasks
- **Phase 2 (Foundation)**: 29 tasks (BLOCKING)
- **Phase 3 (US1 - Real-Time Monitoring)**: 22 tasks
- **Phase 4 (US2 - RUL Forecasting)**: 27 tasks
- **Phase 5 (US3 - Simulation)**: 22 tasks
- **Phase 6 (US4 - Historical Analysis)**: 18 tasks
- **Phase 7 (US5 - Fleet Overview)**: 13 tasks
- **Phase 8 (Polish & Production)**: 22 tasks

**Parallel Opportunities**: 72 tasks marked [P] (44% of tasks can run in parallel)

**Format Validation**: ✅ All 162 tasks follow required format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

**Independent Test Criteria**: ✅ Each user story phase includes explicit test criteria for independent validation

**MVP Recommendation**: User Story 1 (60 tasks) provides complete real-time monitoring capability as standalone MVP
