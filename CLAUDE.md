# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a synthetic data generation system for Battery RUL (Remaining Useful Life) prediction, designed to produce realistic battery telemetry data for training ML models. The system simulates battery degradation in data centers across Thailand, incorporating real-world environmental factors, physics-based degradation models, and operational scenarios based on 15+ years of Thai facility engineering experience.

**Key Purpose**: Generate training data for ML models that predict battery health and remaining useful life.

## Common Commands

### Data Generation

**Quick test run** (1-2 days, 24 batteries, fast sampling):
```bash
python generate_battery_data.py --duration-days 2 --limit-batteries 24 --sampling-seconds 300
```

**Development dataset** (7 days, 1 string = 24 batteries):
```bash
python generate_battery_data.py --duration-days 7 --limit-batteries 24 --sampling-seconds 60
```

**Training dataset** (30 days, 1 location = 216 batteries, production sampling):
```bash
python generate_battery_data.py --duration-days 30 --limit-batteries 216 --sampling-seconds 5
```

**Full fleet multi-location** (2 years, all 9 locations × 24 batteries):
```bash
python generate_full_dataset.py --days 730 --batteries-per-location 24 --sampling-seconds 60
```

### Key Command-Line Options

- `--duration-days N`: Simulation duration (longer = more degradation visible)
- `--limit-batteries N`: Number of batteries to simulate (24 = 1 string, 216 = 1 location)
- `--sampling-seconds N`: Telemetry sampling interval (5 = production, 60+ = faster testing)
- `--output-dir PATH`: Where to save generated CSV files
- `--seed N`: Random seed for reproducibility

### Output Files

Generated in `./output/` (or specified `--output-dir`):
- `telemetry_jar_raw.csv.gz` - Raw battery sensor data (voltage, temp, resistance)
- `telemetry_jar_calc.csv` - Calculated metrics (SOC, SOH)
- `feature_store.csv.gz` - Hourly aggregated ML features
- `rul_prediction.csv` - RUL predictions
- `alert.csv` - Generated alerts
- `battery_states.json` - Final battery health states (ground truth for ML)
- `DATA_GENERATION_REPORT.md` - Validation report

### Python Environment

Install dependencies:
```bash
pip install -r requirements.txt
```

Key dependencies: numpy, pandas, scipy, pytz, faker, tqdm, matplotlib, seaborn

## Code Architecture

The codebase follows a modular pipeline architecture with clear separation of concerns:

### Generator Pipeline Flow

```
MasterDataGenerator → ThailandEnvironmentModel → BatteryDegradationModel → TelemetryGenerator → CalculatedDataGenerator
```

1. **Master Data** (`src/master_data_generator.py`): Generates reference data (locations, batteries, systems, strings)
2. **Environment Models** (`src/thailand_environment.py`): Thai-specific environmental conditions (seasons, regions, HVAC, power grid)
3. **Degradation Models** (`src/battery_degradation.py`): Physics-based battery aging (Arrhenius, cycling stress, calendar aging)
4. **Telemetry Generation** (`src/telemetry_generator.py`): Time-series sensor data generation with realistic operational patterns
5. **Calculated Data** (`src/calculated_data_generator.py`): Derived metrics (SOC, SOH, features, RUL predictions, alerts)

### Main Orchestration Scripts

- **`generate_battery_data.py`**: Single-location data generation (uses `BatteryDataPipeline` class)
- **`generate_full_dataset.py`**: Multi-location generation with location-specific temperature diversity
- **`Battery_RUL_Training.ipynb`**: Jupyter notebook for training ML models on generated data
- **`Battery_RUL_Hybrid_Training.ipynb`**: Hybrid model training (ML + digital twin)

### Key Classes

**`BatteryDataPipeline`** (generate_battery_data.py:36):
- Main orchestration class that runs the full pipeline
- Coordinates all generators and manages data flow
- Method: `run()` executes the 7-phase generation process

**`MasterDataGenerator`** (src/master_data_generator.py:22):
- Generates 9 Thai locations with regional characteristics
- Creates battery fleet structure (systems → strings → batteries)
- Method: `generate_all()` returns dict with all master data tables

**`ThailandEnvironmentModel`** (src/thailand_environment.py:19):
- Models 3 Thai seasons: hot (Mar-May), rainy (Jun-Oct), cool (Nov-Feb)
- Regional climate offsets for 5 Thai regions (northern, northeastern, central, eastern, southern)
- HVAC operational patterns and failure simulation
- Power grid outage patterns based on regional reliability
- Methods: `get_ambient_conditions(timestamp)`, `generate_power_outage_events()`

**`BatteryDegradationModel`** (src/battery_degradation.py:20):
- Physics-based VRLA degradation (Arrhenius temperature acceleration)
- Three degradation profiles: healthy (85%), accelerated (12%), failing (3%)
- Tracks SOH, internal resistance, capacity fade, sudden failures
- Methods: `update_state(timestamp, temperature_c, voltage, current_a)`, `get_current_state()`

**`TelemetryGenerator`** (src/telemetry_generator.py):
- Generates time-series telemetry at specified sampling intervals
- Simulates operational modes: float, boost, discharge, idle, equalize
- Incorporates power outages and environmental conditions
- Method: `generate_timeseries(start_date, end_date, sampling_interval_seconds, outage_events)`

**`CalculatedDataGenerator`** (src/calculated_data_generator.py):
- Computes derived metrics from raw telemetry
- Generates ML feature store (hourly aggregations)
- Creates RUL predictions and alerts
- Method: `generate_all_calculated_data(raw_telemetry, battery_states)`

### Important Data Generation Patterns

**Always follow the dependency order**:
1. Generate master data first
2. Initialize environment and degradation models
3. Generate raw telemetry (depends on #1 and #2)
4. Calculate derived metrics (depends on #3)
5. Generate predictions and alerts (depends on #4)

**Location-specific generation** (for full fleet):
- Each location has unique regional climate offsets
- Temperature variations affect degradation rates (Arrhenius: +10°C = 2× aging)
- Use `generate_full_dataset.py` for proper multi-location handling

**Memory management for large datasets**:
- `generate_full_dataset.py` uses incremental saving (per-location files)
- Avoid loading all data in memory at once
- Use chunked processing for combining location files

## Thailand-Specific Environmental Realism

This generator incorporates real-world Thai facility conditions:

### Three Seasons
- **Hot** (Mar-May): 30-40°C, high HVAC stress, increased battery aging
- **Rainy** (Jun-Oct): Monsoon storms, power outages spike, 70-95% humidity
- **Cool** (Nov-Feb): 22-32°C, optimal battery conditions

### Five Regions
- **Northern** (Chiangmai): -2°C cooler, fewer power outages
- **Northeastern** (Khon Kaen): +1°C offset, hot and dry in summer
- **Central** (Bangkok): +1.5°C urban heat island effect
- **Eastern** (Sriracha): Coastal, +10% humidity
- **Southern** (Phuket, Hat Yai): Tropical, +15% humidity, storm-prone (8 outages/year)

### Power Grid Reliability
- Region-dependent outage frequency: 2-8 outages/year
- Outage duration: 30-90 minutes average
- Correlated with monsoon season (rainy months have more outages)
- Each outage causes battery discharge cycle → accelerated aging

### HVAC Simulation
- Normal operation: ±1°C temperature stability
- Degraded state: ±3°C control, 2× battery aging
- Failed state: Drifts toward outdoor temp, 3× aging
- Failure rate increases in hot season due to equipment stress

## Data Schema Overview

The generated data follows a 7-phase schema with clear dependencies:

**Phase 1 - Master Data**: Locations, battery systems, strings, batteries (static reference data)
**Phase 2-3 - Raw Data**: Telemetry readings, maintenance events (direct sensor/transactional data)
**Phase 4-5 - Calculated Data**: SOC, SOH, aggregated features (derived from raw data)
**Phase 6-7 - Predictions**: RUL predictions, alerts, incidents (ML/rule-engine outputs)

### Critical Data Dependencies

Always generate in order:
1. Master Data → 2. Raw Telemetry → 3. Maintenance Events → 4. Calculated Metrics → 5. Feature Store → 6. RUL Predictions → 7. Alerts

Raw telemetry must exist before calculating SOC/SOH. Feature store requires both raw and calculated data. RUL predictions need feature store and battery states.

### Fleet Specifications

- **9 locations** across Thailand (Chiangmai, Khon Kaen, Nonthaburi, Bangkok ×2, Sriracha, Rayong, Phuket, Hat Yai)
- **1,944 batteries** total (216 per location)
- **81 strings** (9 per location, 24 batteries per string)
- **21 battery systems** (UPS + Rectifier combinations)

### Telemetry Volume (5-second sampling)
- Per-battery telemetry: 33.6M records/day (all 1,944 batteries)
- Per-string telemetry: 1.4M records/day
- Environmental sensors: 26K-52K records/day (60-second sampling)
- ML feature store: 46.7K records/day (hourly aggregation)

## Battery Degradation Models

### VRLA Chemistry Specifications
- Nominal voltage: 12.0V per jar (6 cells × 2.0V)
- Typical capacity: 120 Ah
- Float voltage: 13.65V (2.275V/cell)
- End-of-discharge: 10.5V (1.75V/cell)
- String configuration: 24 batteries in series = 288V nominal
- Internal resistance: 3-5 mΩ (increases with age)

### Three Degradation Profiles

**Healthy (85% of fleet)**:
- 2% SOH decline/year, 5% resistance increase/year
- Normal calendar and cycling aging
- Very low sudden failure probability

**Accelerated (12% of fleet)**:
- 8% SOH decline/year, 15% resistance increase/year
- Higher temperature stress or cycling stress
- Moderate failure probability

**Failing (3% of fleet)**:
- 25% SOH decline/year, 40% resistance increase/year
- End-of-life degradation
- High sudden failure probability
- Failure modes: thermal runaway, sulfation, grid corrosion, dry-out, internal short

### Physics-Based Degradation

**Arrhenius Temperature Acceleration**:
- Every 10°C increase doubles aging rate
- Formula: `aging_rate = base_rate × exp(Ea/kB × (1/T_ref - 1/T))`
- This is why regional temperature differences matter for RUL

**Cycling Stress**:
- Depth-of-discharge (DOD) dependent: deeper discharge = more stress
- Each full discharge cycle reduces capacity by ~0.1%
- Stress factor: `DOD²` (quadratic relationship)

**Calendar Aging**:
- Time-based capacity fade even at float voltage
- Accelerated by temperature
- Approximately 1-2% per year at 25°C

**Float Voltage Stress**:
- Overcharging accelerates grid corrosion
- Undercharging allows sulfation
- Optimal float voltage: 13.65V at 25°C (temperature compensated)

## Working with Generated Data

### Loading Data for ML Training

```python
import pandas as pd
import json

# Load features (hourly aggregated statistics)
features = pd.read_csv('output/feature_store.csv.gz')

# Load ground truth battery states
with open('output/battery_states.json') as f:
    battery_states = json.load(f)

# Convert to DataFrame and merge
states_df = pd.DataFrame(battery_states).T
train_data = features.merge(states_df, left_on='battery_id', right_index=True)

# ML training
X = train_data[['v_mean', 'v_std', 't_mean', 't_max', 'r_internal_latest', 'ah_throughput']]
y = train_data['soh_pct']  # Target: State of Health
```

### Key ML Features (in feature_store.csv)

**Voltage statistics**: `v_mean`, `v_std`, `v_min`, `v_max`, `v_range`
**Temperature statistics**: `t_mean`, `t_max`, `t_delta_from_ambient`
**Resistance metrics**: `r_internal_latest`, `r_internal_trend`
**Operational metrics**: `discharge_cycles_count`, `ah_throughput`, `time_at_high_temp_pct`

### Validation Checks

After generation, verify in `DATA_GENERATION_REPORT.md`:
- Degradation profile distribution: ~85% healthy, ~12% accelerated, ~3% failing
- Mean SOH: 90-100% for short sims (<7 days), 70-90% for long sims (>90 days)
- Temperature range: 20-50°C (varies by region and season)
- Voltage range: 11.5-14.5V per battery
- Failed batteries increase with simulation duration
- Alert counts correlate with degraded batteries

## Alert System

The generator creates realistic alerts based on threshold violations and ML predictions:

**Threshold-based alerts**:
- `voltage_low`/`voltage_high`: Outside 11.5-14.5V range
- `temperature_high`: Above 45°C
- `current_high`: Excessive discharge current
- `ripple_high`: High AC ripple (indicates failing rectifier)

**Calculated alerts**:
- `resistance_drift`: Internal resistance increasing >20% from baseline
- `soh_degraded`: SOH below 80%

**ML-generated alerts**:
- `rul_warning`: RUL < 180 days
- `rul_critical`: RUL < 90 days
- `anomaly_detected`: Unusual patterns detected

Severity levels: `info`, `warning`, `critical`

## Maintenance Schedule Simulation

The generator includes realistic Thai data center maintenance patterns:

- **Monthly**: Visual inspection, voltage measurement (2-3 hours)
- **Quarterly**: IR thermal survey (4 hours)
- **Semi-annual**: Torque check, impedance test (4-6 hours)
- **Annual**: Full capacity discharge test (8 hours)
- **As-needed**: Battery replacement, corrective maintenance

## Operational Modes Simulated

- **Float charging**: Normal standby operation at 13.65V
- **Discharge**: During power outages, voltage drops to 10.5-12.0V
- **Boost charging**: Post-discharge recovery at 14.0V
- **Equalization charging**: Quarterly maintenance at 14.4V (controlled overcharge)
- **Idle**: Brief transitions between modes
