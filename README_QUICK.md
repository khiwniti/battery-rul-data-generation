# Battery RUL Prediction - Data Generation System

Comprehensive synthetic data generator for battery Remaining Useful Life (RUL) prediction in Thai data center facilities.

## Overview

This system generates realistic battery telemetry data based on **15+ years of facility engineering experience in Thailand**, incorporating:

- **Thailand-specific environmental conditions**: 3 seasons (hot, rainy, cool), 5 regional climate zones, monsoon effects
- **Real operational patterns**: HVAC failures, power grid instability, seasonal load variations
- **Physics-based degradation**: Electrochemical aging, temperature acceleration (Arrhenius), cycling stress
- **Thai maintenance practices**: Monthly inspections, quarterly thermal surveys, annual capacity tests
- **Realistic failure modes**: Thermal runaway, sulfation, grid corrosion, dry-out

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Generate Sample Data (Quick Test)

```bash
# Generate 2 days of data for 24 batteries (5-minute sampling)
python generate_battery_data.py --duration-days 2 --limit-batteries 24 --sampling-seconds 300
```

### Generate Training Dataset

```bash
# Generate 90 days for full fleet
python generate_battery_data.py --duration-days 90 --sampling-seconds 5
```

## Command-Line Options

```
--duration-days INT        Simulation duration in days (default: 7)
--output-dir PATH          Output directory (default: ./output)
--seed INT                 Random seed for reproducibility (default: 42)
--sampling-seconds INT     Telemetry sampling interval (default: 300 = 5 min)
--limit-batteries INT      Limit batteries for testing (default: None = all 1944)
```

## Fleet Configuration

- **9 locations** across Thai regions (Chiangmai, Khon Kaen, Bangkok, Phuket, Hat Yai, etc.)
- **1,944 batteries** total (216 per site)
- **81 strings** (9 per site, 24 batteries per string)
- **18-27 battery systems** (2-3 per site: Rectifier + UPS)

## Thai Facility Conditions Modeled

### Seasonal Effects
- **Hot season** (Mar-May): 30-40°C, high HVAC load
- **Rainy season** (Jun-Oct): Monsoon storms, high humidity
- **Cool season** (Nov-Feb): 22-32°C, lower HVAC load

### Power Grid Reliability (by region)
- Central: 2 outages/year, 30 min avg
- Northern: 4 outages/year, 45 min avg
- Southern: 8 outages/year, 90 min avg (storm-prone)

### Maintenance Schedule
- Monthly: Visual inspection, voltage measurement
- Quarterly: Thermal survey (IR scan)
- Semi-annual: Impedance test
- Annual: Capacity test

## Output Files

- **Master data**: location, battery_model, battery_system, string, battery, user, ml_model
- **Telemetry** (compressed): telemetry_jar_raw, telemetry_string_raw, telemetry_jar_calc
- **Maintenance**: maintenance_event, capacity_test, impedance_measurement
- **ML data**: feature_store, rul_prediction, alert
- **Metadata**: battery_states.json, DATA_GENERATION_REPORT.md

## Data Volume (90 days, 1944 batteries, 5s sampling)

| Data Type | Records | Size (compressed) |
|-----------|--------:|------------------:|
| Jar telemetry | 3.02B | ~15 GB |
| String telemetry | 126M | ~800 MB |
| Feature store | 4.2M | ~200 MB |

**Generated with Thai facility engineering expertise** 🇹🇭
