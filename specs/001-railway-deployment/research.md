# Research & Technical Decisions

**Feature**: Battery RUL Prediction & Monitoring System
**Date**: 2025-11-30
**Status**: Complete

## Overview

This document consolidates research findings and technical decisions for implementing the Battery RUL Prediction & Monitoring System on Railway.com. All "NEEDS CLARIFICATION" items from Technical Context have been resolved through research and documented below.

## Decision Summary

| Decision Area | Chosen Solution | Rationale |
|--------------|----------------|-----------|
| Cloud Platform | Railway.com | Per constitution requirement VII. Built-in PostgreSQL/TimescaleDB support, automatic HTTPS, internal networking, simple deployment workflow |
| Backend Framework | FastAPI 0.109+ | Async support for WebSocket connections, automatic OpenAPI docs, Pydantic validation, excellent performance (1000+ req/s) |
| Frontend Framework | React 18 + Vite 5 | Industry standard, excellent ecosystem, Vite for fast dev experience, strong TypeScript support |
| Database | TimescaleDB on PostgreSQL 15+ | Purpose-built for time-series data (1B+ telemetry records), automatic partitioning, compression, continuous aggregates for feature engineering |
| ML Framework | CatBoost 1.2+ | Handles categorical features (location, season) natively, robust to missing data, excellent for time-series regression, interpretable feature importance |
| Digital Twin | Custom ECM + NumPy EKF | VRLA battery-specific Equivalent Circuit Model with Extended Kalman Filter for real-time state estimation, proven in production battery management systems |
| Real-Time Updates | Socket.IO (python-socketio + JS client) | Bi-directional communication for dashboard updates, automatic reconnection, room-based broadcasting for location filtering |
| State Management | TanStack Query + Zustand | TanStack Query for server state caching, Zustand for UI state (simulation mode, auth), avoids Redux complexity |
| API Documentation | OpenAPI 3.1 (FastAPI auto-gen) | Automatic generation from FastAPI route definitions, serves interactive docs at `/docs`, contract-first development |
| Authentication | JWT with httpOnly cookies | Stateless auth for horizontal scaling, secure cookie storage prevents XSS, refresh token rotation |
| Logging | structlog (JSON format) | Structured logging for centralized aggregation, correlation IDs for distributed tracing, Railway.com log streaming compatible |

## Railway.com Deployment Best Practices

### Research Question
How to deploy microservices on Railway.com with optimal cost, performance, and reliability?

### Findings

**Service Configuration**:
- Use Railway.com nixpacks auto-detection for Python/Node.js services (detects `requirements.txt`, `package.json`)
- Set explicit start commands in `railway.json` or Procfile for clarity
- Enable autoscaling only for Backend API (stateless); disable for ML Pipeline (batch jobs), Digital Twin (low load), Simulator (testing only)

**Internal Networking**:
- Railway.com provides private URLs like `http://<service-name>.railway.internal:$PORT`
- Services communicate via internal network (no egress costs, lower latency ~5-10ms)
- Frontend uses public URL, calls Backend API via external HTTPS (Railway.com auto-provisions SSL)

**Database Plugin**:
- Railway.com PostgreSQL plugin auto-injects `DATABASE_URL` environment variable
- Enable TimescaleDB extension: `CREATE EXTENSION IF NOT EXISTS timescaledb;` in init migration
- Use connection pooling (SQLAlchemy `pool_size=10, max_overflow=20`) to handle concurrent requests within 1GB RAM limit

**Environment Variables**:
- Store secrets in Railway.com dashboard (encrypted at rest)
- Use variable references: `${{Postgres.DATABASE_URL}}` to link services
- Separate environments: Production, Staging (Railway.com PR previews)

**Deployment Strategy**:
- Git push to `main` → automatic deploy to Production
- PR opened → automatic preview deployment with ephemeral database
- Use Railway CLI (`railway rollback`) for instant rollback to previous deployment

**Cost Optimization**:
- Frontend: Static site deployment (512MB RAM sufficient, ~$5/month)
- Backend API: Start with 1GB RAM, scale to 2GB if p95 latency >5s (~$20/month)
- TimescaleDB: 4GB RAM for time-series workload (~$40/month)
- Total estimated cost: ~$80-100/month for full production deployment

### Decision
Adopt Railway.com-native deployment patterns: nixpacks auto-build, internal networking for microservice communication, PostgreSQL plugin for TimescaleDB, environment variable linking for service discovery.

## TimescaleDB Time-Series Optimization

### Research Question
How to optimize TimescaleDB for 1B+ records/year with <2s query performance?

### Findings

**Hypertable Partitioning**:
- Convert telemetry table to hypertable: `SELECT create_hypertable('telemetry', 'timestamp', chunk_time_interval => INTERVAL '1 month');`
- Month-based chunks balance query performance (typical queries: last 7-30 days) with maintenance overhead
- Automatic chunk creation as data arrives

**Compression Policies**:
- Compress chunks older than 7 days: `ALTER TABLE telemetry SET (timescaledb.compress);`
- Compression ratio: ~10:1 for time-series data (8GB/year compressed from 80GB raw)
- Add compression policy: `SELECT add_compression_policy('telemetry', INTERVAL '7 days');`
- Queries on compressed chunks ~20% slower but acceptable for historical analysis (non-critical path)

**Retention Policies**:
- Drop chunks older than 2 years: `SELECT add_retention_policy('telemetry', INTERVAL '2 years');`
- Keeps database under 50GB Railway.com limit
- Archive old data to S3/GCS before drop if regulatory compliance required (out of scope for v1)

**Continuous Aggregates (for ML features)**:
- Pre-compute hourly statistics: `CREATE MATERIALIZED VIEW telemetry_hourly WITH (timescaledb.continuous) AS SELECT time_bucket('1 hour', timestamp) AS bucket, battery_id, AVG(temperature_c), MAX(temperature_c), ... FROM telemetry GROUP BY bucket, battery_id;`
- Real-time refresh: `SELECT add_continuous_aggregate_policy('telemetry_hourly', start_offset => INTERVAL '1 hour', end_offset => INTERVAL '1 minute', schedule_interval => INTERVAL '1 hour');`
- ML feature queries hit pre-aggregated view (millisecond response) instead of scanning raw telemetry

**Indexing Strategy**:
- Primary index: `(battery_id, timestamp DESC)` for per-battery queries
- Secondary index: `(location_id, timestamp DESC)` for location dashboard queries
- Avoid index on `temperature_c`, `voltage_v` (high cardinality, low selectivity)
- Use partial indexes for active alerts: `CREATE INDEX alerts_active_idx ON alerts (battery_id) WHERE acknowledged = false AND cleared_at IS NULL;`

**Query Optimization**:
- Use `time_bucket()` for time-range queries instead of `DATE_TRUNC()` (TimescaleDB-optimized)
- Fetch only needed columns: `SELECT battery_id, timestamp, voltage_v, temperature_c` not `SELECT *`
- Limit result sets: Dashboard queries fetch last 1000 points max, paginate historical exports

### Decision
Implement TimescaleDB hypertables with monthly chunks, compression after 7 days, 2-year retention, continuous aggregates for hourly ML features. This keeps queries <2s and database <50GB while handling 1B+ records/year.

## FastAPI WebSocket Implementation

### Research Question
How to implement real-time dashboard updates with FastAPI WebSocket supporting 50+ concurrent connections?

### Findings

**Library Choice**:
- FastAPI native WebSocket support (`@app.websocket("/ws")`) sufficient for simple use cases
- python-socketio (Socket.IO) chosen for production: automatic reconnection, room-based broadcasting, fallback to long-polling if WebSocket blocked
- Socket.IO client libraries available for React (socket.io-client npm package)

**Connection Management**:
- Use Socket.IO rooms for location-based filtering: `sio.enter_room(sid, f"location:{location_id}")`
- Broadcast alerts to specific locations: `await sio.emit('alert', alert_data, room=f"location:{location_id}")`
- Track connections in-memory dict: `{session_id: {user_id, location_ids, connected_at}}`
- Cleanup on disconnect: `@sio.event async def disconnect(sid): await cleanup_session(sid)`

**Message Types**:
- `telemetry_update`: New sensor readings arrived (pushed every 60 seconds)
- `alert_triggered`: New alert created (immediate push)
- `alert_acknowledged`: User acknowledged alert (broadcast to other users)
- `prediction_updated`: RUL prediction recalculated (pushed every hour)
- `simulation_started`/`simulation_stopped`: Simulation state changes

**Performance Optimization**:
- Batch telemetry updates: Send 1 message with 24 batteries instead of 24 messages
- Throttle updates: Max 1 update per battery per 5 seconds (prevents flooding during data backfill)
- Use Redis pub/sub for multi-instance broadcasting (if Backend API scales >1 instance): `await redis.publish(f"location:{loc_id}", message)`

**Error Handling**:
- Automatic reconnection with exponential backoff (Socket.IO built-in)
- Queue missed messages server-side (up to 100 per connection): Send on reconnect with `missed_updates` event
- Heartbeat every 30 seconds: Client sends `ping`, server responds `pong` to detect stale connections

### Decision
Use python-socketio for robust WebSocket implementation with room-based broadcasting for location filtering, batch updates to reduce message volume, Redis pub/sub for multi-instance support (future scaling).

## CatBoost Hyperparameter Tuning for RUL Prediction

### Research Question
What CatBoost hyperparameters optimize MAE <10% and R² >0.80 for battery RUL time-series regression?

### Findings

**Model Configuration**:
- Task type: `CatBoostRegressor(loss_function='RMSE', eval_metric='MAE')` - regression with MAE evaluation
- Iterations: 1000 (with early stopping patience=50) - prevents overfitting
- Learning rate: 0.03 (conservative for time-series)
- Depth: 6 (balance between expressiveness and overfitting risk)
- L2 regularization: 3.0 (reduces overfitting on small training set)

**Categorical Features**:
- `location_id`: CatBoost handles directly with `cat_features=['location_id', 'season', 'profile']`
- `season`: hot/rainy/cool (captures seasonal degradation patterns)
- `profile`: healthy/accelerated/failing (if known from historical data)

**Numerical Features** (temperature-aware per constitution):
- `temperature_mean_30d`: Rolling 30-day average
- `temperature_max`: Peak temperature in window
- `time_above_30C_hours`: Cumulative thermal stress
- `temperature_cycles_count`: Thermal fatigue
- `cycle_count`: Discharge cycles
- `ah_throughput`: Cumulative amp-hours
- `calendar_age_days`: Days since installation
- `resistance_trend_30d`: Slope of resistance over 30 days
- `soh_pct`: Current SOH (target is RUL, not SOH prediction)

**Cross-Validation**:
- Time-series split: Train on days 1-60, validate on days 61-75, test on days 76-90
- DO NOT use random K-fold (breaks temporal ordering)
- Separate test set by location: Train on Chiangmai + Bangkok, test on Phuket (geographic generalization)

**Feature Importance**:
- After training, extract: `model.get_feature_importance(type='ShapValues')`
- Validate temperature features in top 5 (per constitution requirement V)
- If temperature not important → model bug or data quality issue, halt deployment

**Deployment Validation**:
- Test MAE: <10% of mean RUL (if mean RUL = 15 months, MAE <1.5 months)
- Test R²: >0.80 (explains >80% of variance)
- Arrhenius check: Increase temperature +10°C in test set, predicted RUL should decrease ~40-50%

### Decision
Use CatBoost with conservative hyperparameters (1000 trees, depth=6, lr=0.03, L2=3.0), categorical encoding for location/season, temperature-aware features validated as top contributors, time-series cross-validation, Arrhenius validation before deployment.

## Hybrid Prediction Fusion (ML + Digital Twin)

### Research Question
How to fuse ML and Digital Twin RUL predictions for robustness and accuracy?

### Findings

**Fusion Strategies Evaluated**:

1. **Weighted Average (Baseline)**:
   - `RUL_hybrid = w_dt * RUL_dt + w_ml * RUL_ml` where `w_dt + w_ml = 1`
   - Constitution default: 60% Digital Twin, 40% ML
   - Pros: Simple, interpretable, conservative (Digital Twin physics-based)
   - Cons: Fixed weights ignore data quality variations

2. **Bayesian Fusion**:
   - Model prediction uncertainty as Gaussian: `RUL_dt ~ N(μ_dt, σ_dt²)`, `RUL_ml ~ N(μ_ml, σ_ml²)`
   - Fused estimate: `μ_hybrid = (μ_dt/σ_dt² + μ_ml/σ_ml²) / (1/σ_dt² + 1/σ_ml²)`
   - Pros: Incorporates uncertainty, weights high-confidence predictions more
   - Cons: Requires uncertainty quantification (not native in CatBoost, need quantile regression)

3. **Adaptive Weighting (Based on Digital Twin Accuracy)**:
   - Compute Digital Twin voltage prediction error: `mae_voltage = mean(|V_measured - V_predicted|)`
   - If `mae_voltage < 0.1V` → high accuracy → weight Digital Twin 80%, ML 20%
   - If `mae_voltage > 0.5V` → poor accuracy → weight Digital Twin 20%, ML 80%
   - Pros: Dynamically adjusts to battery-specific conditions (e.g., unusual aging pattern where physics model breaks down)
   - Cons: More complex logic, requires real-time voltage prediction evaluation

**Conflict Detection**:
- If `|RUL_dt - RUL_ml| / mean(RUL_dt, RUL_ml) > 0.3` (30% disagreement) → flag for manual review
- Display both estimates in dashboard: "ML: 6 months, Digital Twin: 9 months - Review Required"
- Log disagreement cases for model retraining data augmentation

**Implementation Architecture**:
- Backend API calls both ML Pipeline service and Digital Twin service in parallel (async)
- Fusion Service (backend) combines predictions using selected strategy
- Store all 3 values in database: `rul_ml`, `rul_dt`, `rul_hybrid` for audit trail

### Decision
Implement weighted average fusion (60% Digital Twin, 40% ML) as v1 baseline per constitution. Implement adaptive weighting as v2 enhancement using Digital Twin voltage prediction accuracy. Flag predictions with >30% ML/DT disagreement for manual review.

## React State Management (TanStack Query + Zustand)

### Research Question
How to manage real-time dashboard state (WebSocket updates + API queries) without Redux complexity?

### Findings

**State Categories**:
1. **Server State (API data)**: Battery telemetry, RUL predictions, alerts - use TanStack Query
2. **WebSocket State (real-time updates)**: Live telemetry streams, new alerts - integrate with TanStack Query via `queryClient.setQueryData()`
3. **UI State (client-only)**: Simulation mode toggle, selected location filter, auth status - use Zustand

**TanStack Query Benefits**:
- Automatic caching with staleness detection: `staleTime: 60000` (60-second TTL for telemetry data)
- Background refetching: `refetchInterval: 60000` (re-query every 60s to catch missed WebSocket messages)
- Optimistic updates: Acknowledge alert immediately in UI before API confirms
- Devtools for debugging query state

**WebSocket Integration Pattern**:
```typescript
// Hook combining TanStack Query + Socket.IO
function useBatteryTelemetry(batteryId: string) {
  const queryClient = useQueryClient();

  // Initial data fetch via REST API
  const query = useQuery({
    queryKey: ['battery', batteryId],
    queryFn: () => fetchBattery(batteryId),
    staleTime: 60000,
  });

  // Real-time updates via WebSocket
  useEffect(() => {
    socket.on('telemetry_update', (data) => {
      if (data.battery_id === batteryId) {
        // Update React Query cache with WebSocket data
        queryClient.setQueryData(['battery', batteryId], (old) => ({
          ...old,
          ...data,
          last_updated: new Date(),
        }));
      }
    });

    return () => socket.off('telemetry_update');
  }, [batteryId]);

  return query;
}
```

**Zustand for UI State**:
```typescript
// stores/simulationStore.ts
import create from 'zustand';

export const useSimulationStore = create((set) => ({
  isSimulating: false,
  scenarioType: null,
  affectedLocation: null,
  startSimulation: (type, location) => set({ isSimulating: true, scenarioType: type, affectedLocation: location }),
  stopSimulation: () => set({ isSimulating: false, scenarioType: null, affectedLocation: null }),
}));
```

**Performance Optimization**:
- Virtualize long lists (1,944 batteries): Use `react-window` for battery table rendering
- Debounce filter inputs: `useDeferredValue()` for search queries
- Memoize expensive computations: `useMemo()` for RUL distribution histogram calculations
- Code-split dashboard pages: `React.lazy(() => import('./LocationDashboard'))` for faster initial load

### Decision
Use TanStack Query for server state (API + WebSocket integration), Zustand for UI state (simulation mode, auth), react-window for virtualized lists, React.lazy for code splitting. Avoid Redux to reduce complexity and bundle size.

## Battery ECM/EKF Implementation

### Research Question
How to implement VRLA battery Equivalent Circuit Model (ECM) with Extended Kalman Filter (EKF) for real-time state estimation?

### Findings

**ECM Model Structure** (2nd-order R-C network):
- **R0**: Series resistance (3-5 mΩ for new VRLA, increases with aging)
- **R1/C1**: Short-term polarization (charge transfer, ~seconds time constant)
- **R2/C2**: Long-term polarization (diffusion, ~minutes time constant)
- **OCV(SOC)**: Open-circuit voltage as function of State of Charge (nonlinear lookup table)

**Voltage Equation**:
```
V_terminal = OCV(SOC) - I*R0 - V1 - V2
where:
  V1 = R1 * I * (1 - exp(-dt / (R1*C1)))
  V2 = R2 * I * (1 - exp(-dt / (R2*C2)))
```

**EKF State Vector**:
- `x = [SOC, V1, V2]` (3 states)
- **State transition**: `SOC_k+1 = SOC_k - (I * dt) / (3600 * Capacity)`
- **Measurement**: `z_k = V_terminal` (voltage sensor reading)

**EKF Algorithm**:
1. **Predict**: `x_pred = f(x_prev, u)` where `u = current`
2. **Update**: `K = P_pred * H^T / (H * P_pred * H^T + R)` (Kalman gain)
3. **Correct**: `x_updated = x_pred + K * (z_measured - h(x_pred))` where `h(x) = voltage model`
4. **Covariance**: `P_updated = (I - K*H) * P_pred`

**Parameter Identification** (from training data):
- R0: Voltage drop at current step divided by current change: `R0 = ΔV / ΔI`
- R1/C1, R2/C2: Fit exponential decay during relaxation after current pulse
- OCV curve: Measure voltage after 2-hour rest at various SOC levels (use manufacturer datasheet or lab measurements)

**Temperature Compensation** (Arrhenius):
- Resistance increases at low temperature: `R(T) = R_25C * exp(E_a / k * (1/T - 1/298.15))`
- Capacity decreases at low temperature: `C(T) = C_25C * (1 - α * (298.15 - T))`
- Parameters E_a, α from VRLA manufacturer specs

**RUL Prediction from ECM**:
- Track capacity fade: `C_current / C_nominal` = SOH%
- Predict EOL when SOH < 80%
- Estimate remaining cycles: `Cycles_remaining = (0.80 - SOH_current) / degradation_rate_per_cycle`
- Convert to months: `RUL_months = Cycles_remaining / avg_cycles_per_month`

### Decision
Implement 2nd-order ECM (R0, R1/C1, R2/C2, OCV lookup) with EKF state estimation. Use NumPy for matrix operations. Identify parameters from training data via exponential fitting. Apply Arrhenius temperature compensation. Predict RUL from capacity fade tracking. Validate voltage predictions against measurements (MAE <0.2V) to ensure EKF converging correctly.

## Summary of Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React | 18.x | UI framework |
| | TypeScript | 5.x | Type safety |
| | Vite | 5.x | Build tool, dev server |
| | TanStack Query | 5.x | Server state management |
| | Zustand | 4.x | UI state management |
| | Socket.IO Client | 4.x | WebSocket connection |
| | Recharts | 2.x | Charts and visualizations |
| | react-window | 1.x | Virtualized lists |
| **Backend API** | FastAPI | 0.109+ | REST + WebSocket server |
| | python-socketio | 5.x | Socket.IO implementation |
| | SQLAlchemy | 2.0+ | ORM |
| | Pydantic | 2.x | Request/response validation |
| | structlog | 24.x | Structured logging |
| **ML Pipeline** | CatBoost | 1.2+ | Gradient boosting |
| | NumPy | 1.24+ | Numerical computations |
| | Pandas | 2.x | Data manipulation |
| | SciPy | 1.11+ | Scientific computing |
| **Digital Twin** | NumPy | 1.24+ | EKF matrix operations |
| | SciPy | 1.11+ | Exponential fitting |
| **Database** | TimescaleDB | 2.13+ | Time-series extension |
| | PostgreSQL | 15+ | Relational database |
| **Testing** | pytest | 8.x | Backend unit tests |
| | Playwright | 1.x | E2E tests |
| | Locust | 2.x | Load testing |
| **Deployment** | Railway.com | - | Cloud platform |
| | Docker | - | Containerization (Railway auto-builds) |

## Implementation Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| TimescaleDB query performance degrades with data volume | High (dashboard unusable if >5s) | Medium | Continuous aggregates for ML features, compression policies, query optimization with EXPLAIN ANALYZE |
| WebSocket connections drop during high load | Medium (users miss real-time updates) | Medium | Socket.IO automatic reconnection, Redis pub/sub for multi-instance, connection pooling |
| ML model prediction accuracy degrades over time | Critical (wrong RUL → missed failures) | High | Monitor MAE drift (7-day rolling window), retrain quarterly on new data, hybrid fusion provides backup |
| Railway.com resource limits insufficient | High (service crashes) | Low | Load testing before production, autoscaling for Backend API, optimize memory usage |
| Digital Twin parameters drift for aged batteries | Medium (fusion weight shifts to ML) | Medium | Adaptive weighting based on voltage prediction accuracy, periodic recalibration |

## References

- TimescaleDB Best Practices: https://docs.timescale.com/timescaledb/latest/how-to-guides/hypertables/
- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets/
- CatBoost Time-Series: https://catboost.ai/en/docs/concepts/python-usages-examples
- Battery ECM Models: Plett, G.L. (2015). Battery Management Systems, Volume I: Battery Modeling
- Railway.com Docs: https://docs.railway.app/

---

**Research Status**: ✅ Complete - All technical decisions documented and justified. Ready for Phase 1 (Data Model & Contracts).
