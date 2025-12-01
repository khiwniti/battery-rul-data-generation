# Battery RUL Data Generation on Kaggle

Complete guide to generate the full 2-year dataset on Kaggle with GPU acceleration.

## Repository Information

**GitHub Repository**: https://github.com/khiwniti/battery-rul-data-generation

**Features:**
- Physics-based battery degradation models
- Thai environmental simulation (9 locations, 3 seasons)
- 227+ million telemetry records for 2-year dataset
- GPU-accelerated generation on Kaggle

---

## Quick Start on Kaggle

### Step 1: Create New Kaggle Notebook

1. Go to https://www.kaggle.com/
2. Click **"Code"** > **"New Notebook"**
3. Set accelerator to **GPU T4 x2** (recommended) or **GPU P100**
4. Enable **Internet** access in notebook settings

### Step 2: Setup Environment

```python
# Install dependencies
!pip install numpy pandas scipy pytz faker tqdm matplotlib seaborn

# Clone repository
!git clone https://github.com/khiwniti/battery-rul-data-generation.git
%cd battery-rul-data-generation

# Verify files
!ls -la
```

### Step 3: Generate Full 2-Year Dataset

```python
# Generate full production dataset (2 years, 216 batteries)
ho
# This will take approximately 6-7 hours
# Expected output: 227+ million telemetry records
```

### Step 4: Monitor Progress

```python
# Check generation progress (run in separate cell)
!tail -50 ./output/kaggle_dataset/generation.log
```

### Step 5: Verify Generated Data

```python
import pandas as pd
import os

# Check output directory
output_dir = './output/kaggle_dataset/by_location'
files = os.listdir(output_dir)
print(f"Generated {len(files)} files")

# Load sample data
df = pd.read_csv(f'{output_dir}/battery_sensors_Bangkok_Data_Center.csv.gz')
print(f"\nSample dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst few records:")
print(df.head())
```

---

## Alternative: Faster Test Dataset

For quick testing (30 days, fewer batteries):

```python
# Quick test dataset (30 days, 1 battery per location = 9 batteries)
!python generate_full_dataset.py \
    --days 30 \
    --batteries-per-location 1 \
    --sampling-seconds 300 \
    --output-dir ./output/test_dataset

# This completes in ~20 minutes
```

---

## Download Generated Data

### Option 1: Download via Kaggle UI

1. After generation completes, go to **File** menu
2. Click **"Output"** tab
3. Download the compressed files

### Option 2: Save to Kaggle Dataset

```python
# Create Kaggle dataset from output
import os
from kaggle import api

# Compress output
!cd output && tar -czf battery_rul_2year_dataset.tar.gz kaggle_dataset/

# Create dataset metadata
metadata = {
    "title": "Battery RUL 2-Year Dataset",
    "id": "YOUR_USERNAME/battery-rul-2year-dataset",
    "licenses": [{"name": "CC0-1.0"}]
}

import json
with open('dataset-metadata.json', 'w') as f:
    json.dump(metadata, f)

# Upload to Kaggle Datasets
api.dataset_create_new(folder='./output', public=True)
```

### Option 3: Upload to Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')

# Copy to Google Drive
!cp -r ./output/kaggle_dataset /content/drive/MyDrive/battery_rul_dataset
```

---

## Dataset Structure

### Output Files (per location)

- `battery_sensors_[Location].csv.gz` - Raw battery telemetry
- `string_sensors_[Location].csv.gz` - String-level telemetry

### Combined Files

- `battery_sensors_combined.csv.gz` - All locations merged
- `DATA_GENERATION_REPORT.md` - Quality validation report

### Data Schema

**Battery Telemetry:**
- `battery_id`: Unique identifier
- `timestamp`: Measurement time
- `voltage`: Battery voltage (V)
- `current`: Charge/discharge current (A)
- `temperature`: Battery temperature (°C)
- `internal_resistance`: Internal resistance (mΩ)
- `soc_pct`: State of Charge (%)
- `soh_pct`: State of Health (%)

---

## Performance Optimization on Kaggle

### GPU Acceleration

While the data generation is CPU-bound, Kaggle GPUs provide:
- **Faster CPU**: Better single-thread performance
- **More RAM**: 16-30 GB for large datasets
- **Persistent storage**: Save intermediate results

### Parallel Generation

For even faster generation, split by location:

```python
# Generate one location at a time
locations = [
    "Chiangmai", "Khon Kaen", "Nonthaburi", 
    "Bangrak", "Phrakhanong", "Sriracha",
    "Surat Thani", "Phuket", "Hat Yai"
]

for loc in locations:
    print(f"Generating {loc}...")
    !python generate_battery_data.py \
        --location {loc} \
        --days 730 \
        --batteries 24 \
        --sampling-seconds 60
```

---

## Troubleshooting

### Out of Memory

If you run out of memory:

```python
# Reduce sampling frequency
!python generate_full_dataset.py --sampling-seconds 300  # 5 minutes instead of 1 minute

# Or reduce duration
!python generate_full_dataset.py --days 365  # 1 year instead of 2 years
```

### Session Timeout

Kaggle notebooks timeout after 12 hours. For long runs:

```python
# Save checkpoints
import pickle

# After each location completes, save state
with open('generation_checkpoint.pkl', 'wb') as f:
    pickle.dump(generation_state, f)

# Resume from checkpoint if needed
with open('generation_checkpoint.pkl', 'rb') as f:
    generation_state = pickle.load(f)
```

---

## Next Steps: ML Training

After generating data, train ML models:

```python
# Load features for ML training
import pandas as pd

features = pd.read_csv('output/kaggle_dataset/feature_store.csv.gz')
print(f"ML features: {features.shape}")

# Example: Train CatBoost model
from catboost import CatBoostRegressor

X = features[['v_mean', 'v_std', 't_mean', 't_max', 'r_internal_latest']]
y = features['soh_pct']

model = CatBoostRegressor(
    iterations=1000,
    learning_rate=0.03,
    depth=6,
    task_type='GPU'  # Use Kaggle GPU
)

model.fit(X, y)
print(f"Model trained! R² score: {model.score(X, y):.4f}")
```

---

## Complete Kaggle Notebook Example

```python
# === CELL 1: Setup ===
!pip install -q numpy pandas scipy pytz faker tqdm matplotlib seaborn
!git clone https://github.com/khiwniti/battery-rul-data-generation.git
%cd battery-rul-data-generation

# === CELL 2: Generate Data ===
!python generate_full_dataset.py \
    --days 730 \
    --batteries-per-location 24 \
    --sampling-seconds 60 \
    --output-dir /kaggle/working/output

# === CELL 3: Verify ===
import pandas as pd
import glob

files = glob.glob('/kaggle/working/output/by_location/*.csv.gz')
print(f"Generated {len(files)} files")

total_records = 0
for file in files:
    df = pd.read_csv(file)
    total_records += len(df)
    print(f"{file.split('/')[-1]}: {len(df):,} records")

print(f"\nTotal records: {total_records:,}")

# === CELL 4: Sample Analysis ===
df_sample = pd.read_csv(files[0])
print(df_sample.describe())

# === CELL 5: Download ===
!zip -r battery_rul_dataset.zip /kaggle/working/output
print("Dataset ready for download!")
```

---

## Support

- **GitHub Issues**: https://github.com/khiwniti/battery-rul-data-generation/issues
- **Dataset Documentation**: See README.md in repository

---

**Ready to generate production-grade battery RUL training data on Kaggle!** 🚀
