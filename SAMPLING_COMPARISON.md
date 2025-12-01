# Battery Sensor Sampling - Comparison Guide

## Current Running Generation
- **Sampling**: 300 seconds (5 minutes)
- **Duration**: 730 days (2 years)
- **Batteries**: 216
- **Expected records**: ~45 million
- **File size**: ~400-500 MB compressed
- **Generation time**: ~30-60 minutes

## With 5-Second Sampling (NEW)
- **Sampling**: 5 seconds
- **Duration**: 730 days (2 years)
- **Batteries**: 216
- **Expected records**: ~2.7 BILLION (60× more!)
- **File size**: ~25-30 GB compressed
- **Generation time**: ~6-12 hours

## Comparison Table

| Parameter | 5-Min Sampling | 5-Sec Sampling | Ratio |
|-----------|----------------|----------------|-------|
| **Samples/day** | 288 | 17,280 | 60× |
| **Total records** | 45M | 2.7B | 60× |
| **File size** | 500 MB | 30 GB | 60× |
| **Generation time** | 1 hour | 10 hours | 10× |
| **Data resolution** | Low | High | - |

## Recommendations

### Use 5-Second Sampling For:
✅ **Training deep learning models** (RNN, LSTM, Transformer)
✅ **Capturing rapid dynamics** (discharge events, transients)
✅ **High-resolution trend analysis**
✅ **Detecting early warning signs** (voltage drops, temperature spikes)
✅ **Production-grade monitoring systems**

### Use 5-Minute Sampling For:
✅ **Quick prototyping and testing**
✅ **Traditional ML models** (Random Forest, XGBoost)
✅ **Long-term trend analysis**
✅ **Storage-constrained environments**
✅ **Fast iteration during development**

## Commands

### Stop Current Generation (5-min sampling)
```bash
# Find and kill the process
ps aux | grep generate_sensor_data.py
# Then kill the specific PID
```

### Start 5-Second Sampling
```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction

# Full 2 years (WARNING: ~30GB, 10 hours)
python generate_sensor_data.py \
    --duration-days 730 \
    --batteries 216 \
    --sampling-seconds 5 \
    --output-dir ./output/sensor_data_only/training_2years_5sec
```

### Recommended: Start with Shorter Duration
```bash
# Test 30 days first (~1.1GB, 30 min)
python generate_sensor_data.py \
    --duration-days 30 \
    --batteries 216 \
    --sampling-seconds 5 \
    --output-dir ./output/sensor_data_only/test_30days_5sec

# Then 90 days (~3.3GB, 2 hours)
python generate_sensor_data.py \
    --duration-days 90 \
    --batteries 216 \
    --sampling-seconds 5 \
    --output-dir ./output/sensor_data_only/train_90days_5sec
```

## Data Volume Calculator

| Duration | Batteries | Sampling | Records | Size (compressed) |
|----------|-----------|----------|---------|-------------------|
| 1 day | 216 | 5s | 3.7M | 35 MB |
| 7 days | 216 | 5s | 26M | 250 MB |
| 30 days | 216 | 5s | 112M | 1.1 GB |
| 90 days | 216 | 5s | 336M | 3.3 GB |
| 180 days | 216 | 5s | 672M | 6.6 GB |
| 365 days | 216 | 5s | 1.36B | 13 GB |
| **730 days** | **216** | **5s** | **2.72B** | **26 GB** |

## Disk Space Check

```bash
# Check available disk space
df -h /teamspace/studios/this_studio/NT/RUL_prediction/output

# Check current usage
du -sh output/*
```

## Current Status

**Background Job ID**: 6b57a3
**Status**: Running (5-minute sampling)
**Output**: `./output/sensor_data_only/training_2years/`

**Options**:
1. **Let it finish** - Get 5-minute data (useful for testing)
2. **Stop and restart** - Switch to 5-second data (production quality)
3. **Run both** - Different output folders (comparison)

---

**Note**: 5-second sampling captures realistic sensor behavior including:
- Voltage transients during load changes
- Temperature rise/fall dynamics
- Current spikes during discharge events
- String mode transitions
- All critical battery dynamics for accurate RUL prediction
