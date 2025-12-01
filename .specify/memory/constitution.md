<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 1.1.0
Type: MINOR (Expanded guidance on control panel and operational monitoring)

Modified Principles:
  - Principle IV (Observability First): Added real-time dashboard requirements
  - Principle VI (Facility Engineering Expertise): Enhanced control panel guidance

Added Sections:
  - Control Panel Requirements (under Deployment Architecture)
  - Proactive Problem Prevention Framework
  - Enhanced operational metrics

Templates Requiring Updates:
  ✅ Constitution updated with control panel & monitoring enhancements
  ⚠️ .specify/templates/spec-template.md - Should add control panel acceptance criteria
  ⚠️ .specify/templates/plan-template.md - Should add simulation scenario testing
  ⚠️ .specify/templates/tasks-template.md - Should add control panel UI/UX tasks

Follow-up TODOs:
  - Design control panel UI mockups for scenario simulation
  - Define specific scenario templates (HVAC failure, heat wave, power outage)
  - Create operator training materials for control panel
  - Document WebSocket message format for real-time updates
-->

# Battery RUL Prediction & Monitoring System Constitution

## Core Principles

### I. Mission-Critical Operations (NON-NEGOTIABLE)

**This system protects critical infrastructure.** Failures can lead to unplanned data center outages, equipment damage, and financial losses.

- **Accuracy over speed**: RUL predictions MUST be validated before deployment. A false negative (predicting long life for failing battery) is UNACCEPTABLE.
- **Fail-safe defaults**: System degradation MUST trigger conservative predictions (shorter RUL estimates) never optimistic ones.
- **No silent failures**: Every prediction MUST include confidence intervals. Low-confidence predictions MUST be flagged for human review.
- **Data validation**: Sensor readings outside physical limits (e.g., voltage <10V or >15V) MUST trigger alerts, not predictions.

**Rationale**: 15+ years of Thai facility operations show that battery failures account for 60% of UPS-related incidents. Conservative predictions prevent cascading failures across 9 data centers serving critical infrastructure.

### II. Real-Time Reliability

**The system operates 24/7 monitoring 1,944 batteries across Thailand.** Downtime directly impacts facility safety.

- **99.9% uptime SLA**: Backend services MUST maintain three-nines availability (8.76 hours downtime/year maximum).
- **Sub-5-second latency**: RUL predictions for dashboard queries MUST complete within 5 seconds at p95.
- **Graceful degradation**: If ML model fails, fall back to physics-based Digital Twin predictions.
- **Circuit breakers**: External service failures (database, API) MUST NOT crash the application. Implement timeout + retry with exponential backoff.
- **Health checks**: All services MUST expose `/health` and `/ready` endpoints for Railway.com monitoring.

**Rationale**: Facility engineers rely on real-time dashboards during critical maintenance windows. A 30-second delay in seeing battery alerts during a discharge test is operationally unacceptable.

### III. Production Safety

**Code changes can affect predictions for 216 batteries per site.** Deploy with extreme caution.

- **Staged rollouts**: Changes MUST deploy to staging (single location simulation) → canary (1 site) → full production (9 sites).
- **Feature flags**: ML model updates MUST be toggleable without redeployment. Use environment variables or database flags.
- **Rollback plan**: Every deployment MUST include one-command rollback procedure documented in deployment notes.
- **Data immutability**: Historical predictions MUST NEVER be modified. Store new predictions with timestamps, keep old ones for audit.
- **Change log**: Every model update MUST log: version, training data range, test metrics (MAE, RMSE, R²), approval timestamp.

**Rationale**: In 2023, a Thai data center operator deployed an uncalibrated model that predicted 10-year RUL for batteries already at 70% SOH, leading to 3 emergency replacements during a storm. This principle prevents that.

### IV. Observability First

**You cannot fix what you cannot see.** Comprehensive logging and monitoring are mandatory.

- **Structured logging**: All services MUST log in JSON format with: `timestamp`, `level`, `service`, `battery_id`, `location`, `message`, `duration_ms`.
- **Distributed tracing**: Track requests across frontend → backend → ML pipeline → database with correlation IDs.
- **Real-time dashboard (PRIMARY VIEW)**:
  - **Fleet overview**: 9 location cards showing: battery count, mean SOH, active alerts, last update time
  - **Battery health heatmap**: Color-coded by SOH (green >85%, yellow 80-85%, red <80%)
  - **RUL distribution**: Histogram showing remaining life across fleet
  - **Active alerts feed**: Real-time stream (WebSocket) with severity, location, battery ID, timestamp
  - **Temperature map**: Thai map overlay showing regional temps and HVAC status
- **Operational metrics dashboards**:
  - Prediction latency (p50, p95, p99) - MUST be <5s at p95
  - Model accuracy drift (MAE over 7-day rolling window) - MUST stay <15%
  - Alert volume by severity and location - Track anomaly spikes
  - Sensor data gaps (missing telemetry intervals) - MUST be <10% per location
  - WebSocket connection health - Track dropped connections
- **Automated alerting**: Trigger PagerDuty/Slack when:
  - Model MAE exceeds 15% (from baseline 10%)
  - Any location has >10% missing sensor data for >1 hour
  - RUL predictions show sudden -30 day jump (data anomaly)
  - Critical battery (SOH <80%) with RUL <90 days
  - HVAC failure detected (temperature spike >10°C in <30 min)
- **Audit trail**: Log every user action on control panel (parameter changes, alert acknowledgments, manual overrides, scenario simulations).

**Rationale**: Thai monsoon season causes sporadic power outages affecting sensor telemetry. Without observability, we cannot distinguish between real battery degradation and data quality issues. Facility engineers need real-time situational awareness during critical maintenance windows.

### V. Temperature-Aware ML (DOMAIN-CRITICAL)

**Temperature explains 35-45% of RUL variance.** Ignoring it guarantees model failure.

- **Location-specific baselines**: Models MUST train on data from all 5 Thai regions (northern, northeastern, central, eastern, southern).
- **Arrhenius validation**: Predicted RUL MUST align with physics: 10°C increase → ~50% life reduction. Violations flag model bugs.
- **Seasonal adjustment**: Bangkok hot season (Mar-May, 30-40°C) predictions MUST differ from cool season (Nov-Feb, 22-32°C) for same battery.
- **HVAC failure detection**: Sudden +10°C temperature spike MUST trigger immediate alert and RUL recalculation.
- **Feature requirements**: Models MUST include:
  - `temperature_mean_30d` (calendar aging)
  - `temperature_max` (peak stress)
  - `time_above_30C_hours` (cumulative damage)
  - `temperature_cycles_count` (thermal fatigue)

**Rationale**: Research shows Chiangmai batteries (24°C avg) last 42% longer than Bangkok batteries (31°C avg) under identical usage. Models ignoring this fail in production within 3 months.

### VI. Facility Engineering Expertise Over Academic Theory

**This system serves working engineers, not researchers.** Practicality trumps novelty.

- **Actionable thresholds**: Alerts MUST use industry-standard limits:
  - Float voltage: 13.50-13.80V (manufacturer spec)
  - SOH warning: <85% (replace within 6 months)
  - SOH critical: <80% (replace within 30 days)
  - Resistance drift: >50% increase from baseline (investigate immediately)
- **Maintenance-aligned predictions**: RUL MUST output in "months until next quarterly maintenance window" not abstract days.
- **Thai operational context**: System MUST account for:
  - Monsoon season (Jun-Oct): Higher outage probability, defer non-critical maintenance
  - Songkran (mid-April): Holiday staffing constraints
  - Business hours (8am-8pm): Maintenance only during these windows
- **No black boxes**: Every RUL prediction MUST include:
  - Top 3 contributing factors (e.g., "High temp +40%, Cycling stress +30%, Age +20%")
  - Confidence level (High/Medium/Low based on data quality)
  - Similar historical cases (e.g., "Battery X at same site had similar pattern, failed after 4 months")

**Rationale**: Engineers trust systems they understand. A model predicting "RUL = 847 days" without explanation gets ignored. A model saying "Replace in Q2 maintenance window (high temp stress, similar to Battery B-07 last year)" gets acted upon.

### VII. Railway.com Cloud-Native Architecture

**The system deploys on Railway.com with zero on-premise infrastructure.**

- **Microservices design**:
  - **Frontend**: React SPA (Vite) serving dashboard + control panel
  - **Backend API**: FastAPI Python service (REST + WebSocket for real-time updates)
  - **ML Pipeline**: Separate service for model training/inference (async processing)
  - **Sensor Simulator**: Standalone service generating realistic telemetry streams
  - **TimescaleDB**: PostgreSQL time-series extension for sensor data
- **Service communication**: Use Railway's internal networking (private URLs). External API calls MUST use HTTPS only.
- **Environment configs**: All secrets (DB passwords, API keys) via Railway environment variables. NEVER hardcode credentials.
- **Autoscaling**: Backend API MUST scale horizontally (stateless design, shared-nothing architecture).
- **Database migrations**: Use Alembic for schema changes. Test on staging database first. Include rollback migrations.
- **Health checks**: Railway.com monitors `/health` every 30s. Failing 3 consecutive checks triggers restart.
- **Resource limits**: Set Railway.com limits:
  - Backend: 1GB RAM, 1 CPU (scale to 2GB if latency >5s)
  - ML Pipeline: 2GB RAM, 2 CPU (training jobs)
  - Database: 4GB RAM, 50GB storage (time-series data retention: 2 years)

**Rationale**: Railway.com's ephemeral containers require stateless services. Previous monolithic design failed during automatic restarts, losing in-memory prediction cache. This architecture prevents that.

## Deployment Architecture

### Service Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     Railway.com Platform                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │   Frontend   │────▶ │  Backend API │                   │
│  │  (React SPA) │      │   (FastAPI)  │                   │
│  │              │      │              │                   │
│  │  - Dashboard │      │  - REST API  │                   │
│  │  - Control   │      │  - WebSocket │                   │
│  │    Panel     │      │  - Auth      │                   │
│  └──────────────┘      └───────┬──────┘                   │
│                                 │                           │
│                        ┌────────▼────────┐                 │
│                        │   TimescaleDB   │                 │
│                        │  (PostgreSQL +  │                 │
│                        │  time-series)   │                 │
│                        └────────┬────────┘                 │
│                                 │                           │
│         ┌───────────────────────┼───────────────────────┐  │
│         │                       │                       │  │
│  ┌──────▼──────┐        ┌──────▼──────┐       ┌───────▼──┐│
│  │ ML Pipeline │        │   Sensor    │       │  Digital │││
│  │  Service    │        │  Simulator  │       │   Twin   │││
│  │             │        │             │       │  Service │││
│  │ - Training  │        │ - Real-time │       │          │││
│  │ - Inference │        │   telemetry │       │ - Physics│││
│  │ - Model Reg │        │ - Scenario  │       │   model  │││
│  │             │        │   control   │       │ - EKF    │││
│  └─────────────┘        └─────────────┘       └──────────┘││
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Sensor Simulator** → Generates realistic telemetry → **TimescaleDB**
2. **Backend API** → Reads latest telemetry → **Frontend Dashboard** (WebSocket push)
3. **ML Pipeline** → Batch processes hourly features → Generates RUL predictions → **TimescaleDB**
4. **Digital Twin** → Real-time EKF updates → Fuses with ML predictions → **Backend API**
5. **Control Panel** → User adjusts simulation scenarios → **Sensor Simulator** updates parameters

### Control Panel Requirements (CRITICAL FOR OPERATIONS)

The control panel MUST provide facility engineers with **scenario simulation and what-if analysis** capabilities:

#### Core Simulation Controls

1. **Environmental Scenario Injection**
   - **Heat Wave Simulation**: Increase ambient temp by +5°C to +15°C for selected location(s)
     - Observe RUL impact in real-time (expected: 15-30% reduction based on Arrhenius)
     - Trigger: Button "Simulate Heat Wave" → Duration selector (1 day to 30 days)
   - **HVAC Failure Simulation**: Disable cooling for selected location
     - Temperature drifts toward outdoor conditions
     - RUL predictions recalculate with accelerated degradation
   - **Monsoon Season**: Increase power outage frequency +50% for location
     - More discharge cycles → increased cycling stress
     - Expected: 5-10% RUL reduction

2. **Power Grid Controls**
   - **Manual Outage Trigger**: Inject power outage event
     - Duration: 30-180 minutes (realistic range)
     - Location selector: Single site or multi-site outage
     - Observe: Battery discharge, SOC drop, voltage curves
   - **Outage Frequency Adjustment**: Change regional outage rate (2-8/year slider)
   - **Grid Stability Indicator**: Show current outage probability by region

3. **Battery Stress Testing**
   - **Accelerated Aging**: Increase degradation rate for specific battery string
     - Useful for testing alert thresholds and maintenance workflows
     - Safety check: Confirm before applying (irreversible in simulation)
   - **SOH Override**: Manually set battery SOH (for testing edge cases)
     - Range: 50-100%
     - Triggers: Recalculate RUL, generate alerts if <80%
   - **Temperature Spike**: Inject thermal event for specific battery
     - Simulate thermal runaway scenario
     - Expected: Immediate critical alert + RUL recalculation

4. **Maintenance Workflow Testing**
   - **Schedule Maintenance Window**: Mark location as "under maintenance"
     - Suppress non-critical alerts during window
     - Log maintenance activities
   - **Battery Replacement**: Mark battery as replaced
     - Reset SOH to 100%, resistance to baseline
     - Update installed_date timestamp
   - **Capacity Test Simulation**: Run virtual capacity test
     - Observe: Discharge curve, capacity measurement, SOH update

5. **Real-Time Status Display**
   - **Active Scenarios**: List all running simulations with time remaining
   - **Pause/Resume/Stop**: Full control over scenario execution
   - **Scenario History**: Log of past simulations with outcomes
   - **Prediction Comparison**: Show "Baseline RUL" vs "Scenario RUL" side-by-side

#### Control Panel UI/UX Requirements

- **Response time**: Control changes MUST reflect in dashboard within 3 seconds
- **Visual feedback**: Loading indicators for async operations
- **Undo capability**: Allow reverting scenario changes (restore last known state)
- **Confirmation dialogs**: For destructive actions (accelerated aging, manual SOH override)
- **Scenario templates**: Pre-configured scenarios (e.g., "Bangkok Summer Heat Wave", "Southern Storm Season")
- **Export results**: Download scenario report (CSV/PDF) with before/after metrics

**Rationale**: Facility engineers need to test "what if" scenarios before making capital expenditure decisions. Example: "If we delay HVAC upgrade by 6 months, how many batteries will need emergency replacement?" Control panel provides this analysis capability without waiting for real-world events.

## Proactive Problem Prevention Framework

The system MUST prevent problems across ALL operational dimensions:

### 1. Battery Health Degradation Prevention

- **Early Warning System**: Flag batteries at 85% SOH (6-month lead time before critical)
- **Predictive Maintenance**: Schedule replacements during next quarterly window
- **Trend Analysis**: Detect accelerating degradation (SOH dropping >2%/month)
- **String Imbalance Detection**: Identify weak batteries in string (voltage delta >0.5V)

### 2. Environmental Risk Mitigation

- **HVAC Performance Monitoring**: Alert when temperature variance increases (±1°C → ±3°C)
- **Seasonal Planning**: Pre-position spare batteries before hot season (Mar-May)
- **Regional Risk Scoring**: Rank locations by failure probability (temperature + outage frequency)
- **Storm Season Preparation**: Increase monitoring frequency during monsoon (Jun-Oct)

### 3. Power Quality Protection

- **Voltage Stability Tracking**: Detect ripple voltage increases (indicates rectifier wear)
- **Discharge Event Analysis**: Log every outage with duration, depth-of-discharge, recovery time
- **Grid Reliability Forecasting**: Predict outage probability based on weather + historical patterns
- **Backup Capacity Validation**: Ensure string can handle N-hour discharge (configurable per site)

### 4. Operational Efficiency

- **Maintenance Optimization**: Batch battery replacements to minimize truck rolls
- **Spare Parts Inventory**: Predict required stock levels by location (based on RUL forecasts)
- **Cost-Benefit Analysis**: Compare "replace now" vs "defer 3 months" total cost
- **Downtime Risk Assessment**: Calculate probability of unplanned outage by location

### 5. Data Quality Assurance

- **Sensor Health Monitoring**: Detect stuck sensors (reading unchanged for >1 hour)
- **Missing Data Imputation**: Use physics-based model to fill gaps (not blind interpolation)
- **Anomaly Detection**: Flag physically impossible readings (voltage >15V, temp >60°C)
- **Calibration Drift**: Track sensor accuracy over time (compare to periodic manual measurements)

**Key Metric**: System MUST achieve <2% unplanned battery failures (failures not predicted 30+ days in advance). Current industry average: 8-12%.

## Development Workflow

### Testing Gates (MANDATORY)

1. **Unit Tests** (80% coverage minimum)
   - All ML pipeline functions (feature engineering, model inference)
   - API endpoints (request validation, response serialization)
   - Digital Twin physics calculations (voltage, SOC, SOH)

2. **Integration Tests**
   - Frontend → Backend → Database end-to-end flows
   - Sensor Simulator → Database → Dashboard real-time updates
   - ML Pipeline → Model Registry → Inference API

3. **Load Tests** (before production deployment)
   - 1,944 batteries × 60s sampling = 32.4 req/s sustained for 1 hour
   - Dashboard must handle 50 concurrent users
   - WebSocket connections must maintain <100ms latency at 100 connections

4. **Accuracy Validation**
   - New ML models MUST achieve:
     - MAE < 1,500 days (10% of mean RUL)
     - R² > 0.80
     - No systematic bias (predictions vs actuals correlation > 0.85)
   - Test on held-out locations (train on 8 sites, validate on 9th)

### Code Review Requirements

- **ML Changes**: Reviewed by someone with battery domain knowledge (verify Arrhenius assumptions, threshold sanity)
- **Backend API**: Reviewed for security (SQL injection, XSS, authentication bypass)
- **Database Schema**: Reviewed for performance (indexing strategy, partition key selection)
- **Frontend**: Reviewed for UX (accessibility, mobile responsiveness, color-blind friendly charts)

### Deployment Process

1. **PR merged** → Triggers Railway.com GitHub integration
2. **Staging deployment** (automatic) → Run smoke tests
3. **Canary deployment** (manual approval) → 10% traffic for 1 hour
4. **Monitor metrics**: If error rate <1% and latency p95 <5s → proceed
5. **Full production** (manual approval) → 100% traffic
6. **Post-deployment verification**:
   - Check Grafana dashboards for anomalies
   - Review Sentry error logs
   - Verify latest RUL predictions match expected ranges

## Governance

### Constitution Authority

This constitution is the **supreme governing document** for the Battery RUL Prediction & Monitoring System. It supersedes:
- Individual developer preferences
- Ad-hoc architecture decisions
- Conflicting legacy documentation

When in doubt, this constitution takes precedence.

### Amendment Procedure

1. **Proposal**: Submit GitHub issue with `constitution-amendment` label
2. **Review**: Requires approval from:
   - Technical lead (architecture + performance impact)
   - Domain expert (battery engineering + facility operations)
   - Product owner (user impact + business value)
3. **Documentation**: Amendment MUST include:
   - Rationale (why change is necessary)
   - Migration plan (how existing code adapts)
   - Success metrics (how to measure if amendment works)
4. **Version bump**: Follow semantic versioning:
   - MAJOR: Removing/contradicting existing principle
   - MINOR: Adding new principle or expanding scope
   - PATCH: Clarifying existing principle without changing enforcement

### Compliance Review

- **Weekly**: Check Sentry error logs for Constitution Principle violations
- **Monthly**: Review Grafana dashboards for SLA compliance (99.9% uptime, <5s latency)
- **Quarterly**: Audit ML model accuracy drift (MAE should remain <1,500 days)
- **Annually**: Full constitution review and update with lessons learned

### Enforcement

**Violations MUST be treated as bugs.** If code violates a principle:
1. Create P0 bug ticket
2. Roll back deployment if in production
3. Fix root cause (not symptoms)
4. Add regression test to prevent recurrence

**Principle waivers** (temporary exceptions) require:
- Written justification
- Time-bound expiration (max 3 months)
- Documented technical debt for future resolution
- Sign-off from technical lead

### Runtime Guidance

For day-to-day development decisions not covered by this constitution, refer to:
- `CLAUDE.md` - Project context and domain knowledge
- `README.md` - Quick start and usage examples
- `data_schema.md` - Database design patterns
- Railway.com deployment docs

**Version**: 1.1.0 | **Ratified**: 2025-11-30 | **Last Amended**: 2025-11-30
