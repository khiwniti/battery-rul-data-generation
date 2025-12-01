# Battery Telemetry Data Generation - Usage Guide

## Quick Start Examples

### 1. Test Run (2 days, 24 batteries, 5-min sampling)
```bash
python generate_battery_data.py \
    --duration-days 2 \
    --limit-batteries 24 \
    --sampling-seconds 300 \
    --output-dir ./output/test
```

**Expected output**: ~7K telemetry records, completes in 1-2 minutes

### 2. Development Dataset (7 days, 1 string = 24 batteries)
```bash
python generate_battery_data.py \
    --duration-days 7 \
    --limit-batteries 24 \
    --sampling-seconds 60 \
    --output-dir ./output/dev_7days
```

**Expected output**: ~241K telemetry records, completes in 5-10 minutes

### 3. Training Dataset (30 days, 1 location = 216 batteries)
```bash
python generate_battery_data.py \
    --duration-days 30 \
    --limit-batteries 216 \
    --sampling-seconds 5 \
    --output-dir ./output/training_30days
```

**Expected output**: ~55M telemetry records, completes in 30-60 minutes

### 4. Full Fleet Production (90 days, all 1,944 batteries)
```bash
python generate_battery_data.py \
    --duration-days 90 \
    --sampling-seconds 5 \
    --output-dir ./output/production_90days
```

**Expected output**: ~3B telemetry records, ~15GB compressed, 6-12 hours

## Understanding the Output

### Directory Structure
```
output/
├── location.csv                      # 9 data centers
├── battery.csv                       # Battery master data
├── telemetry_jar_raw.csv.gz         # Voltage, temp, resistance (per battery)
├── telemetry_jar_calc.csv           # SOC, SOH (calculated)
├── feature_store.csv.gz             # Hourly aggregated ML features
├── rul_prediction.csv               # RUL predictions
├── alert.csv                        # Generated alerts
├── maintenance_event.csv            # Maintenance records
└── DATA_GENERATION_REPORT.md        # Validation report
```

### Key Generated Files for ML Training

**Primary Features** (feature_store.csv.gz):
- `v_mean`, `v_std`, `v_min`, `v_max` - Voltage statistics
- `t_mean`, `t_max` - Temperature statistics
- `r_internal_latest` - Internal resistance
- `discharge_cycles_count` - Cycle count
- `ah_throughput` - Cumulative throughput

**Target Variable** (battery_states.json):
- `soh_pct` - State of Health (current capacity %)
- `rul_days` - Remaining Useful Life estimate
- `failed` - Failure flag
- `failure_mode` - Failure type if failed

### Data Quality Indicators

Check the report for:
- ✅ Degradation profile distribution (should be ~85% healthy, 12% accelerated, 3% failing)
- ✅ Mean SOH should be 90-100% for short simulations
- ✅ Failed batteries increase with simulation duration
- ✅ Alert counts should correlate with degraded batteries

## Real-World Scenarios Included

### 1. Seasonal Effects (Thailand)
- **Hot season** (Mar-May): Higher temperature stress, HVAC load
- **Rainy season** (Jun-Oct): Humidity spikes, power outages increase
- **Cool season** (Nov-Feb): Optimal conditions, lower stress

### 2. Regional Variations
- **Northern** (Chiangmai): Cooler (-2°C), fewer outages
- **Southern** (Phuket, Hat Yai): Tropical (+15% humidity), storm outages
- **Central** (Bangkok): Urban heat island (+1.5°C)

### 3. Operational Events
- **Power outages**: 2-8 per year per location, causing discharge cycles
- **HVAC failures**: 2-8% annual failure rate, causing temperature excursions
- **Equalization charging**: Quarterly scheduled events
- **Capacity tests**: Annual full discharge tests

### 4. Degradation Patterns
- **Normal aging**: 2% SOH/year, 5% resistance increase/year
- **Accelerated aging**: 8% SOH/year, 15% resistance increase/year
- **End-of-life**: 25% SOH/year, 40% resistance increase/year
- **Sudden failures**: Thermal runaway, sulfation, grid corrosion

## Scaling Considerations

### Memory Usage
| Batteries | Duration | Sampling | RAM Required |
|-----------|----------|----------|--------------|
| 24        | 7 days   | 5 min    | ~100 MB      |
| 216       | 30 days  | 5 sec    | ~2 GB        |
| 1,944     | 90 days  | 5 sec    | ~16 GB       |

**Tip**: Use `--sampling-seconds 60` (1 min) or higher for lower memory

### Processing Time
| Batteries | Duration | Sampling | Est. Time |
|-----------|----------|----------|-----------|
| 24        | 1 day    | 10 min   | 30 sec    |
| 216       | 7 days   | 1 min    | 10 min    |
| 1,944     | 30 days  | 5 sec    | 4-6 hours |

### Disk Space (compressed)
| Batteries | Duration | Sampling | Disk Space |
|-----------|----------|----------|------------|
| 24        | 7 days   | 5 min    | ~2 MB      |
| 216       | 30 days  | 5 sec    | ~500 MB    |
| 1,944     | 90 days  | 5 sec    | ~15 GB     |

## Advanced Usage

### Custom Random Seed
```bash
python generate_battery_data.py --seed 12345
```
Use different seeds for train/validation/test splits

### Multi-Location Simulation
Currently generates for first location only. To generate for all locations, modify line 233 in `generate_battery_data.py`:
```python
# Change from:
location = self.master_data['location'].iloc[0]

# To:
for _, location in self.master_data['location'].iterrows():
    # ... generate telemetry
```

### Custom Degradation Profiles
Edit `battery_degradation.py` line 41-62 to adjust degradation rates

## Loading Data for ML Training

### Python Example
```python
import pandas as pd
import json

# Load features
features = pd.read_csv('output/feature_store.csv.gz')

# Load battery states (ground truth)
with open('output/battery_states.json') as f:
    states = json.load(f)

# Join for training data
train_data = features.merge(
    pd.DataFrame(states).T,
    left_on='battery_id',
    right_index=True
)

# Target variable
y = train_data['soh_pct']
X = train_data[['v_mean', 'v_std', 't_mean', 'r_internal_latest']]
```

## Troubleshooting

### Out of Memory
- Increase `--sampling-seconds` (e.g., 60 or 300)
- Reduce `--duration-days`
- Use `--limit-batteries` for testing

### Slow Generation
- Reduce `--sampling-seconds` interval
- Use fewer batteries for testing
- Check available CPU (telemetry generation is CPU-intensive)

### No Failures in Short Simulations
- Failures are rare events (3% of fleet)
- Use longer simulations (30+ days) or
- Manually set battery profiles in code

## Validation Checklist

After generation, verify:
- [ ] All CSV files created without errors
- [ ] Telemetry record counts match expected (duration × batteries × samples/day)
- [ ] SOH values decrease over time (check battery_states.json)
- [ ] Temperature ranges are realistic (20-50°C)
- [ ] Voltage ranges are realistic (11.5-14.5V per battery)
- [ ] Alerts generated for out-of-range conditions
- [ ] Maintenance events scheduled appropriately

## Citation

When using this data generator, please reference:
```
Battery RUL Prediction Data Generator
Thailand Data Center Operations - Realistic Telemetry Synthesis
Based on 15+ years facility engineering experience
```

## Support

For issues or questions:
1. Check the DATA_GENERATION_REPORT.md in output directory
2. Verify battery_states.json for battery health distribution
3. Review sample telemetry data for anomalies
4. Open an issue with error logs and configuration

---

**Last Updated**: 2025-11-29
**Version**: 1.0
