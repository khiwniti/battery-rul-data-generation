# Feature Specification: Battery RUL Prediction & Monitoring System

**Feature Branch**: `001-railway-deployment`
**Created**: 2025-11-30
**Status**: Draft
**Input**: User description: "Battery RUL Prediction & Monitoring System with ML pipeline, frontend dashboard, backend API, and sensor simulator deployed on Railway.com"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Battery Health Monitoring (Priority: P1)

A facility engineer at Chiangmai Data Center opens the monitoring dashboard at 8 AM to review the health status of all 216 batteries across the site before the morning maintenance window. The dashboard displays current battery voltage, temperature, State of Health (SOH), and any active alerts. The engineer identifies 3 batteries showing elevated temperature (above 35°C) and voltage drift, allowing them to schedule inspection during the quarterly maintenance window rather than waiting for catastrophic failure.

**Why this priority**: This is the core value proposition - preventing unplanned outages by providing visibility into battery health across all 9 locations (1,944 batteries). Without this, engineers rely on reactive maintenance after failures occur, leading to costly emergency replacements and potential data center downtime.

**Independent Test**: Can be fully tested by connecting real or simulated sensor data streams, opening the dashboard, and verifying that current readings display correctly with proper alert thresholds. Delivers immediate value by replacing manual voltage checks with automated monitoring.

**Acceptance Scenarios**:

1. **Given** 216 batteries are actively reporting telemetry every 60 seconds, **When** engineer opens location dashboard, **Then** system displays current voltage, temperature, and SOH for each battery updated within last 2 minutes
2. **Given** battery temperature exceeds 35°C threshold, **When** condition persists for 5 minutes, **Then** system generates temperature alert visible on dashboard with battery location (string number, position)
3. **Given** battery voltage drops below 12.0V during float mode, **When** engineer views battery detail page, **Then** system shows voltage trend over last 7 days with threshold violation markers
4. **Given** engineer is viewing Bangkok location dashboard, **When** they select filter "Show only batteries with alerts", **Then** system displays only batteries with active critical or warning alerts
5. **Given** HVAC failure occurs at Phuket location, **When** ambient temperature rises above 32°C, **Then** system automatically adjusts temperature alert thresholds and flags affected batteries

---

### User Story 2 - RUL Forecasting for Maintenance Planning (Priority: P1)

The facility manager reviews quarterly maintenance schedules across all 9 locations. The system displays Remaining Useful Life (RUL) predictions for each battery, highlighting 18 batteries predicted to reach End-of-Life (SOH < 80%) within the next 90 days. The system groups these by location and provides recommended replacement dates aligned with scheduled maintenance windows during the cool season (November-February) to avoid monsoon disruptions.

**Why this priority**: Proactive maintenance planning prevents emergency replacements that cost 3× more and require urgent procurement. RUL predictions enable batch replacements during optimal weather windows, critical for Thai operations where monsoon season (June-October) increases outage risk.

**Independent Test**: Can be tested by running ML models on historical or generated battery data, verifying RUL predictions display with confidence intervals, and confirming predictions update after new telemetry data arrives. Delivers value by enabling budget planning and parts procurement 3-6 months in advance.

**Acceptance Scenarios**:

1. **Given** ML model has processed last 30 days of battery telemetry, **When** facility manager opens RUL dashboard, **Then** system displays predicted RUL in months for each battery with confidence level (High/Medium/Low)
2. **Given** battery B-47 at Bangkok site shows accelerated degradation (10% SOH decline in 60 days), **When** system recalculates RUL, **Then** prediction updates from 12 months to 4 months with "High Confidence" and contributing factors displayed (High temp +45%, Cycling stress +30%, Age +15%)
3. **Given** 18 batteries predicted to fail within 90 days, **When** manager requests "Maintenance Schedule Report", **Then** system generates report grouping replacements by location, prioritizing sites with critical batteries, suggesting dates aligned with quarterly maintenance windows
4. **Given** battery temperature history shows 42% more time above 30°C than fleet average, **When** engineer views RUL prediction, **Then** system indicates temperature impact: "Expected life 42% shorter than Chiangmai batteries due to temperature stress"
5. **Given** RUL prediction has Low confidence (data quality issues or unusual pattern), **When** displayed on dashboard, **Then** system flags prediction with "Low Confidence - Manual Review Required" and shows similar historical failure cases for comparison

---

### User Story 3 - Scenario Simulation for Testing Response Plans (Priority: P2)

A facility engineer needs to test the team's response to an HVAC failure scenario before the hot season (March-May). Using the control panel, they simulate HVAC degradation at the Nonthaburi location, causing indoor temperature to gradually rise from 24°C to 38°C over 2 hours. The system generates realistic sensor data streams showing battery temperatures increasing, RUL predictions dropping, and alert thresholds being crossed. The team practices their escalation procedures using the live dashboard without affecting real operations.

**Why this priority**: Training and incident response testing are critical for mission-critical facilities, but running drills on live systems risks actual outages. Simulation capability enables testing emergency procedures, validating alert thresholds, and training new staff without production impact.

**Independent Test**: Can be tested by starting a simulation scenario (e.g., power outage, temperature spike), verifying sensor streams generate realistic data, confirming dashboard reflects simulated conditions, and stopping simulation cleanly without affecting production data. Delivers value by enabling risk-free training and validation of monitoring thresholds.

**Acceptance Scenarios**:

1. **Given** engineer selects "Simulate HVAC Failure" scenario for Sriracha location, **When** simulation starts, **Then** system generates sensor data showing temperature rising 2°C per hour from baseline 24°C, battery temperatures following with 15-minute lag, and RUL predictions decreasing in response
2. **Given** simulation running with 12 batteries experiencing thermal stress, **When** engineer views dashboard, **Then** dashboard clearly indicates "SIMULATION MODE - Sriracha Location" with visual distinction (e.g., amber border) from production data
3. **Given** simulation has generated 200 temperature alerts, **When** engineer stops simulation, **Then** system purges simulated data, restores dashboard to production view, and clears all simulation-generated alerts within 5 seconds
4. **Given** engineer configures custom scenario with battery resistance increasing 50% over 24 hours, **When** simulation runs, **Then** sensor data reflects voltage sag under load consistent with increased resistance, triggering resistance drift alerts
5. **Given** multiple engineers reviewing the same simulated scenario, **When** one engineer adjusts simulation parameters (e.g., increases temperature rate), **Then** all connected dashboards reflect updated scenario within 2 seconds via real-time updates

---

### User Story 4 - Historical Trend Analysis for Root Cause Investigation (Priority: P2)

An engineer investigates why 3 batteries at Bangrak Data Center failed earlier than expected (RUL predicted 8 months, actual failure at 4 months). Using the dashboard's historical view, they plot temperature, voltage, and SOH trends over the last 12 months. The analysis reveals that these batteries experienced 23% more discharge cycles than predicted due to frequent power grid instabilities in that area, and ambient temperatures during April 2025 peaked at 41°C (7°C above model assumptions).

**Why this priority**: Continuous improvement requires understanding prediction failures. Historical analysis enables model refinement, identification of location-specific environmental factors, and validation that predictions account for Thai operational realities (grid instability, extreme seasonal temperatures).

**Independent Test**: Can be tested by querying stored telemetry data for specific batteries over time ranges, generating trend visualizations, correlating events (outages, alerts, maintenance), and exporting data for analysis. Delivers value by preventing future mispredictions through model tuning.

**Acceptance Scenarios**:

1. **Given** battery B-12 has 18 months of telemetry history, **When** engineer selects "View 12-Month Trend", **Then** system displays interactive time-series charts for voltage, temperature, SOH, and resistance with zoom/pan capability
2. **Given** engineer viewing historical trends for failed battery, **When** they overlay power outage events from event log, **Then** chart shows vertical markers at outage timestamps with correlation to voltage drops and SOH degradation
3. **Given** engineer suspects temperature correlation with failures, **When** they select "Compare Temperatures Across Locations", **Then** system displays box plots showing temperature distribution for all 9 locations, highlighting Bangrak's higher median (31°C vs 26°C fleet average)
4. **Given** model predicted RUL incorrectly for a battery cluster, **When** engineer exports historical data via "Download CSV", **Then** system provides timestamped sensor data including all features used for ML prediction (temperature_mean_30d, cycle_count, ah_throughput, etc.)
5. **Given** engineer analyzing seasonal degradation patterns, **When** they select "Compare Hot Season (Mar-May) vs Cool Season (Nov-Feb)", **Then** system shows SOH decline rates differ by 67% between seasons, with contributing factors breakdown

---

### User Story 5 - Multi-Location Fleet Health Overview (Priority: P3)

The operations director prepares a monthly report for management covering battery health across all 9 data centers. The fleet dashboard shows aggregated metrics: 94.2% of batteries in "Healthy" status (SOH > 85%), 18 batteries requiring replacement within 90 days, and average RUL by location. The director identifies that southern locations (Phuket, Surat Thani, Hat Yai) show 12% better battery life than central Bangkok locations due to cooler temperatures and more stable grid power.

**Why this priority**: Executive oversight requires fleet-level visibility for budget planning, regional performance comparison, and strategic decisions about equipment procurement or environmental controls (HVAC upgrades). Aggregated view complements detailed per-battery monitoring.

**Independent Test**: Can be tested by aggregating metrics across multiple locations, generating summary statistics, producing exportable reports, and verifying calculations match raw data totals. Delivers value by enabling strategic planning and resource allocation across the facility portfolio.

**Acceptance Scenarios**:

1. **Given** all 9 locations reporting telemetry, **When** director opens fleet dashboard, **Then** system displays location cards showing: battery count, % healthy (SOH > 85%), active alerts count, average RUL, and temperature range
2. **Given** director selects "Fleet Health Trend - Last 6 Months", **When** report generates, **Then** system shows line chart of fleet-wide average SOH declining 2.1% (within normal 2% annual degradation), with location-level breakdown identifying Bangrak as outlier (3.8% decline)
3. **Given** director needs to present to CFO, **When** they click "Export Monthly Report", **Then** system generates PDF report with executive summary, key metrics, predicted replacement costs for next quarter, and location comparison table
4. **Given** budget planning requires 12-month replacement forecast, **When** director requests "Annual Forecast", **Then** system predicts 147 batteries will reach EOL threshold in next 12 months, with cost estimate and suggested quarterly replacement schedule
5. **Given** director wants to justify HVAC upgrade investment, **When** they compare "Temperature Impact on RUL", **Then** system calculates that reducing average temperature 5°C (from 31°C to 26°C) would extend fleet average RUL by 1.8 years, with ROI calculation

---

### Edge Cases

- **What happens when sensor data stream fails?** System detects missing telemetry (no data for 5+ minutes), marks affected batteries as "Data Quality: Unknown" on dashboard, generates alert "Sensor connectivity lost - [location/string]", continues showing last known values with "stale data" indicator, and RUL predictions fallback to Digital Twin physics-based estimates until telemetry resumes.

- **How does system handle extreme temperature readings (e.g., sensor malfunction reporting 80°C)?** System validates sensor readings against physical limits (VRLA operating range 10-50°C). Readings outside this range trigger "Sensor Malfunction Suspected" alert, are excluded from ML features, and trigger notification to engineer to check sensor hardware. Dashboard shows "Invalid Reading" rather than displaying impossible values.

- **What happens during database maintenance or planned downtime?** System enters "maintenance mode" displaying notification banner to all users. Real-time sensor data continues streaming to buffer, dashboard remains read-only showing last known state, ML predictions pause, and alerts continue generating based on buffered data. When maintenance completes, system batch-processes buffered data and updates all predictions within 15 minutes.

- **How does system behave when ML model predictions conflict with Digital Twin estimates?** System implements hybrid fusion approach: if predictions disagree by > 30%, displays both estimates with explanation ("ML predicts 6 months, Physics model predicts 9 months - Conflict: Review manually"). Engineer can view contributing factors for both predictions. System flags these cases for model retraining or calibration.

- **What happens when multiple engineers try to run different simulations simultaneously?** Each simulation is isolated by user session. Dashboard indicates which engineer is viewing which simulation (e.g., "Simulation by User: thai.engineer@company - HVAC Failure - Phuket"). Engineers can view each other's simulations in read-only mode but cannot control them. Maximum 5 concurrent simulations enforced to prevent resource exhaustion.

- **How does system handle monsoon season power instabilities (frequent brief outages)?** System detects patterns of repeated power interruptions, automatically adjusts alert thresholds to reduce noise (e.g., suppress "voltage recovered" alerts if cycling < 10 minutes apart), aggregates outage events into single incident, and factors increased discharge cycling into RUL calculations. Dashboard shows "Grid Instability Detected" indicator for affected locations.

- **What happens when RUL prediction suddenly drops dramatically (e.g., from 12 months to 2 months)?** System generates "Critical RUL Change" alert requiring engineer acknowledgment, displays comparison of before/after contributing factors, checks if sudden change correlates with recent events (power outage, temperature spike, maintenance), and prompts engineer to either confirm prediction or flag for manual inspection. Prevents false alarms from data anomalies.

- **How does system handle batteries replaced during warranty period (fresh install)?** Engineer logs replacement event via dashboard, selecting "Battery Replaced" action and entering new battery serial number and installation date. System resets SOH to 100%, clears historical data for that position (preserving archived history for replaced unit), initializes new battery profile, and begins fresh RUL prediction cycle. Old battery data preserved for warranty analysis.

- **What happens when browser loses network connectivity mid-session?** Dashboard detects disconnect (WebSocket heartbeat failure), displays "Connection Lost - Attempting Reconnect" banner, queues any user actions (simulation control, alert acknowledgments) locally, automatically attempts reconnection with exponential backoff, and when reconnected, syncs queued actions and refreshes dashboard state. No data loss for user actions taken during outage.

## Requirements *(mandatory)*

### Functional Requirements

**Dashboard & Visualization**

- **FR-001**: System MUST display real-time battery telemetry (voltage, temperature, current, resistance, SOH) for all 1,944 batteries across 9 locations, updated within 5 seconds of sensor reading
- **FR-002**: System MUST provide location-level dashboards showing all batteries for a single data center with filtering by string, status (healthy/warning/critical), and alert presence
- **FR-003**: System MUST provide fleet-level dashboard aggregating metrics across all 9 locations showing: total battery count, health distribution (% healthy/warning/critical), active alerts by severity, average RUL per location
- **FR-004**: System MUST display battery detail view showing: current readings, 7-day trend charts, historical events (alerts, maintenance, outages), and RUL prediction with contributing factors
- **FR-005**: System MUST indicate data freshness with timestamp "Last Updated: [time]" and visually distinguish stale data (> 5 minutes old) from current readings

**RUL Prediction & Alerts**

- **FR-006**: System MUST generate RUL predictions for each battery in months remaining until EOL threshold (SOH < 80%), updated hourly using latest telemetry and ML model
- **FR-007**: System MUST display RUL prediction confidence level (High/Medium/Low) based on data quality and historical prediction accuracy for similar batteries
- **FR-008**: System MUST explain RUL predictions by showing top 3 contributing factors with percentage impact (e.g., "High temp +40%, Cycling stress +30%, Age +20%")
- **FR-009**: System MUST generate alerts when batteries exceed thresholds: voltage out of range (float: 13.5-13.8V), temperature > 35°C, SOH < 85% (warning) or < 80% (critical), resistance drift > 50% from baseline
- **FR-010**: System MUST apply location-specific and seasonal alert threshold adjustments (e.g., higher temperature tolerance during hot season March-May)
- **FR-011**: System MUST aggregate related alerts into incidents (e.g., if entire string shows voltage low, create single "String Voltage Low" incident rather than 24 separate battery alerts)
- **FR-012**: System MUST allow engineers to acknowledge alerts with notes and track acknowledgment history (user, timestamp, resolution notes)

**Sensor Simulation & Testing**

- **FR-013**: System MUST provide control panel for starting/stopping sensor data simulations with pre-defined scenarios: power outage, HVAC failure, HVAC degradation, temperature heatwave, battery aging acceleration, resistance drift
- **FR-014**: System MUST allow engineers to customize simulation parameters: duration, rate of change (e.g., temperature rise speed), affected location, affected battery count/selection
- **FR-015**: System MUST visually distinguish simulated data from production data on dashboard with clear indicators (e.g., "SIMULATION MODE" banner, colored borders, separate simulation tab)
- **FR-016**: System MUST isolate simulations by user session, preventing simulation data from affecting production dashboards or other users' views
- **FR-017**: System MUST cleanly terminate simulations, purging all simulated telemetry and alerts, restoring production view within 5 seconds of stop command
- **FR-018**: System MUST prevent more than 5 concurrent simulations to protect system resources

**Historical Analysis & Reporting**

- **FR-019**: System MUST provide historical trend visualization for any battery over selectable time ranges: 24 hours, 7 days, 30 days, 90 days, 1 year, with zoom/pan capability
- **FR-020**: System MUST allow overlaying multiple metrics on same timeline (voltage + temperature + SOH) and correlating with events (power outages, alerts, maintenance)
- **FR-021**: System MUST provide comparison views showing metric distribution across locations (box plots, histograms) for identifying environmental differences
- **FR-022**: System MUST export historical data and reports in CSV format for offline analysis, including all sensor readings and calculated features
- **FR-023**: System MUST generate monthly summary reports showing: fleet health statistics, batteries requiring replacement next quarter, location performance comparison, prediction accuracy metrics

**Data Integrity & Quality**

- **FR-024**: System MUST validate sensor readings against physical limits (voltage 10-15V, temperature 10-50°C, resistance 0-100 mΩ) and reject out-of-range values as sensor errors
- **FR-025**: System MUST detect missing telemetry (no data received for > 5 minutes) and mark affected batteries as "Data Quality: Unknown" with alert generation
- **FR-026**: System MUST buffer sensor data during temporary backend unavailability (up to 15 minutes) and batch-process buffered data when service recovers
- **FR-027**: System MUST maintain audit trail of all battery replacement events, recording: old battery serial, new battery serial, installation date, engineer name, reason for replacement

**ML Model & Hybrid Prediction**

- **FR-028**: System MUST run ML-based RUL prediction using trained CatBoost model processing features: temperature statistics (mean/max/time_above_30C), cycle count, ah_throughput, calendar age, resistance trend
- **FR-029**: System MUST run physics-based Digital Twin RUL prediction in parallel using Equivalent Circuit Model (ECM) with Extended Kalman Filter (EKF) state estimation
- **FR-030**: System MUST fuse ML and Digital Twin predictions using weighted average (default: 60% Digital Twin, 40% ML) or adaptive fusion based on Digital Twin voltage prediction accuracy
- **FR-031**: System MUST flag predictions where ML and Digital Twin disagree by > 30%, prompting manual review and showing both estimates with contributing factors
- **FR-032**: System MUST track prediction accuracy by comparing predicted RUL vs actual time-to-failure for replaced batteries, storing metrics for model evaluation

**User Management & Access Control**

- **FR-033**: System MUST authenticate users via username/password with role-based access: Admin (full access), Engineer (view + acknowledge alerts + run simulations), Viewer (read-only dashboard access)
- **FR-034**: System MUST restrict simulation controls to Engineer and Admin roles only, preventing Viewers from modifying system state
- **FR-035**: System MUST log all user actions (login, alert acknowledgment, simulation start/stop, configuration changes) with timestamp and user ID for audit trail

**System Health & Monitoring**

- **FR-036**: System MUST expose health check endpoints indicating service status: Frontend (HTTP /health), Backend API (/api/health), ML Pipeline (/ml/health), Sensor Simulator (/simulator/health), Database (connection test)
- **FR-037**: System MUST self-monitor and alert when: prediction latency exceeds 10 seconds, database query time > 2 seconds, sensor data ingestion drops below expected rate, service memory usage exceeds 80% of allocated resources
- **FR-038**: System MUST maintain 99.9% uptime for backend API services (maximum 8.76 hours downtime per year)
- **FR-039**: System MUST support graceful degradation: if ML service fails, fallback to Digital Twin predictions; if database query times out, serve cached dashboard data with staleness indicator

**Real-Time Updates**

- **FR-040**: System MUST push real-time dashboard updates via WebSocket connections when: new sensor data arrives, alerts trigger, RUL predictions update, battery status changes
- **FR-041**: System MUST maintain WebSocket connection with automatic reconnection on disconnect (exponential backoff), queueing missed updates and replaying on reconnect
- **FR-042**: System MUST support minimum 50 concurrent dashboard users with < 100ms WebSocket message latency at 100 connections

### Key Entities

- **Battery**: Individual VRLA battery jar (12V, 120Ah nominal capacity). Attributes: unique ID, serial number, position in string, installed date, current SOH, current SOC, voltage, temperature, resistance, RUL prediction, alert status. Relationships: belongs to one String, has many TelemetryReadings, has many Alerts.

- **String**: Series-connected group of 24 batteries forming 288V nominal DC bus. Attributes: string ID, system ID it belongs to, location, operating mode (float/boost/discharge/idle/equalize), total voltage, total current, health summary (count of healthy/warning/critical batteries). Relationships: belongs to one BatterySystem, contains 24 Batteries.

- **Location**: Data center facility site. Attributes: location ID, name (e.g., "Chiangmai Data Center"), region (northern/northeastern/central/eastern/southern), geographic coordinates, regional temperature offset, regional humidity offset. Relationships: contains multiple BatterySystems, aggregates fleet statistics.

- **BatterySystem**: UPS or Rectifier system at a location. Attributes: system ID, system type (UPS/Rectifier), location, rated power, number of strings. Relationships: belongs to one Location, contains multiple Strings.

- **TelemetryReading**: Time-stamped sensor measurement. Attributes: battery ID, timestamp, voltage, current, temperature, resistance, conductance, data source (real sensor vs simulation). Stored as time-series data partitioned by month.

- **RULPrediction**: Forecasted remaining useful life for a battery. Attributes: battery ID, prediction timestamp, predicted RUL (months), confidence level (High/Medium/Low), ML prediction value, Digital Twin prediction value, fused prediction value, contributing factors breakdown (temperature impact %, cycling impact %, age impact %), historical prediction accuracy for similar batteries.

- **Alert**: Threshold violation or anomaly detection event. Attributes: alert ID, battery ID or string ID, alert type (voltage_low/voltage_high/temperature_high/soh_degraded/resistance_drift/anomaly_detected), severity (warning/critical), trigger timestamp, clearance timestamp, acknowledged (yes/no), acknowledged by (user ID), acknowledgment notes. Relationships: belongs to Battery or String, may aggregate into Incident.

- **Incident**: Correlated group of related alerts. Attributes: incident ID, title, affected location, affected component (battery/string/system), alert IDs included, start timestamp, resolution timestamp, assigned engineer, resolution notes. Relationships: aggregates multiple Alerts.

- **Simulation**: Scenario test session. Attributes: simulation ID, scenario type (power_outage/hvac_failure/temperature_spike/battery_aging), created by user, start timestamp, end timestamp, status (running/stopped), parameters (location, duration, rate of change), simulated battery IDs. Relationships: generates simulated TelemetryReadings.

- **User**: System operator or viewer. Attributes: user ID, username, email, role (Admin/Engineer/Viewer), location assignments (which locations user can access), last login timestamp. Relationships: creates Simulations, acknowledges Alerts, generates AuditLogs.

- **MaintenanceEvent**: Logged maintenance activity. Attributes: event ID, battery ID, event type (replacement/inspection/capacity_test/impedance_test/visual_inspection), event date, performed by engineer, notes, replaced battery serial (if replacement), new battery serial (if replacement). Relationships: associated with Battery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Facility engineers can view current health status of all 216 batteries at their assigned location within 3 seconds of opening dashboard, with telemetry updated within last 5 seconds
- **SC-002**: System processes and displays RUL predictions for all 1,944 fleet batteries within 5 seconds at p95 latency when queried
- **SC-003**: Dashboard supports 50 concurrent users viewing live data with < 100ms WebSocket update latency and maintains responsiveness (page interactions < 200ms)
- **SC-004**: RUL predictions achieve Mean Absolute Error (MAE) < 1,500 days (< 10% of mean battery life) and R² > 0.80 on validation dataset
- **SC-005**: Alert noise reduced by 60% through intelligent aggregation (e.g., 24 battery voltage alerts consolidated into 1 string incident)
- **SC-006**: Simulation mode starts within 5 seconds of engineer triggering scenario and generates realistic sensor data streams matching expected patterns (e.g., temperature rise follows thermal lag, voltage sags under load)
- **SC-007**: Historical trend queries for any battery over any time range complete within 3 seconds, returning all requested metrics with visualization
- **SC-008**: System maintains 99.9% uptime for backend services (< 8.76 hours downtime per year), measured via health check endpoint availability
- **SC-009**: Zero data loss during network interruptions up to 15 minutes (sensor data buffered and batch-processed on reconnect)
- **SC-010**: Engineers can complete common workflows in < 2 minutes: acknowledge alert (< 30 seconds), start simulation (< 1 minute), generate monthly report (< 2 minutes)
- **SC-011**: System scales to handle 32.4 requests/second sustained sensor data ingestion (1,944 batteries × 60-second sampling) without degradation
- **SC-012**: Facility managers can identify batteries requiring replacement next quarter within 1 minute using fleet dashboard filtering and sorting
- **SC-013**: Temperature-aware ML features improve prediction accuracy by 35-45% compared to temperature-agnostic baseline (as validated by research)
- **SC-014**: Prediction explanations provide actionable insights: engineers report 90% of RUL predictions include clear contributing factors that inform maintenance decisions
- **SC-015**: System successfully handles edge cases without crashes: sensor malfunction, database timeout, ML service failure, network interruption, simultaneous simulations

### Assumptions & Constraints

**Assumptions**:

- Railway.com cloud platform provides: PostgreSQL/TimescaleDB for time-series data storage, sufficient compute resources (Backend: 1GB RAM/1 CPU, ML: 2GB RAM/2 CPU, Database: 4GB RAM/50GB storage), WebSocket support for real-time connections, environment variable management for secrets
- Sensor data arrives via HTTP POST to backend API at 60-second intervals per battery (32.4 req/s total) with JSON payload: battery_id, timestamp, voltage, current, temperature, resistance
- ML model (CatBoost RUL predictor) is pre-trained on 730-day × 216-battery historical dataset with location-specific temperature diversity
- Digital Twin ECM parameters (R0, R1, C1, R2, C2) and OCV curves are pre-calibrated for VRLA battery chemistry (HX12-120 model)
- Users access dashboard via modern web browsers (Chrome/Firefox/Edge/Safari last 2 versions) with JavaScript enabled and screen resolution ≥ 1280×720
- Internet connectivity between data centers and Railway.com cloud is reliable (< 1% packet loss) with latency < 200ms
- Battery replacement events are manually logged by engineers (no automated detection of physical replacements)
- Alert thresholds are initially configured based on Thai facility engineering expertise and manufacturer specifications, tuned post-deployment based on false positive rates

**Constraints**:

- Must deploy on Railway.com platform (no on-premise components, no alternative cloud providers)
- Must comply with 99.9% uptime SLA (constitution mandates mission-critical reliability)
- Must handle 1,944 batteries × 365 days × 1,440 readings/day = 1.02 billion records per year time-series data volume
- Must keep database storage under 50GB limit via data retention policy (2 years raw telemetry, 10 years aggregated metrics)
- Must maintain sub-5-second prediction latency at p95 (constitution requirement for dashboard queries)
- Must implement conservative fail-safe defaults (constitution: degradation triggers conservative predictions, never optimistic)
- Must avoid silent failures (constitution: all predictions include confidence intervals, low-confidence flagged for review)
- Must provide explainable predictions (constitution: top 3 contributing factors mandatory for facility engineer trust)
- Must account for Thai operational context: monsoon season (June-October) grid instabilities, hot season (March-May) temperature peaks, Songkran holiday (mid-April) staffing constraints, business-hours-only maintenance windows (8 AM-8 PM)
- Must not include implementation details in user-facing UI (no technology names, framework versions, API endpoint URLs visible to operators)

### Out of Scope

The following are explicitly NOT included in this feature and may be considered for future iterations:

- **Automated battery replacements**: System predicts when replacement is needed but does not automatically order parts, schedule maintenance, or dispatch technicians
- **Mobile native applications**: Initial release targets web browser access only. Native iOS/Android apps for field engineers are out of scope
- **Integration with existing CMMS/ITSM systems**: No connectors to ServiceNow, Jira, Maximo, or other enterprise ticketing systems. Work orders must be manually created based on system alerts
- **Advanced analytics**: No root cause analysis beyond contributing factors, no anomaly detection beyond threshold alerts, no predictive outage probability modeling
- **Multi-language support**: UI is English-only. Thai language localization deferred to future release
- **Capacity planning optimization**: System does not recommend optimal battery string configurations, UPS sizing, or load balancing across systems
- **Financial modeling**: No TCO calculator, ROI analysis, or warranty tracking integrated into system
- **Video surveillance integration**: No correlation with security camera footage for physical tampering detection or visual inspection augmentation
- **Weather API integration**: Temperature data comes from facility sensors only, no external weather service correlation (though monsoon/season awareness is built into alert threshold logic)
- **Supplier/vendor management**: No integration with battery manufacturers for warranty claims, no automated procurement workflows
- **Energy efficiency optimization**: System monitors battery health only, not broader facility power usage effectiveness (PUE) or load optimization
- **Legacy system migration**: No data import from previous monitoring systems. Fresh start with new sensor data streams
- **Email/SMS alert delivery**: Alerts visible in dashboard only. External notification channels (email, SMS, Slack, PagerDuty) out of scope for v1
- **Customizable dashboards**: Layout and widgets are fixed. User-configurable dashboard creation deferred to future release
