#!/bin/bash
# prepare_kaggle_dataset.sh
# Prepares Parquet data for Kaggle upload

set -e

echo "=========================================="
echo "KAGGLE DATASET PREPARATION"
echo "=========================================="

# Configuration
PROJECT_ROOT="/teamspace/studios/this_studio/NT/RUL_prediction"
BACKEND_DATA="$PROJECT_ROOT/backend/data/parquet"
KAGGLE_DATASET="$PROJECT_ROOT/kaggle-dataset"
DATASET_NAME="battery-rul-parquet"

# Step 1: Create directory structure
echo ""
echo "Step 1: Creating directory structure..."
mkdir -p "$KAGGLE_DATASET/$DATASET_NAME"

# Step 2: Copy Parquet files
echo ""
echo "Step 2: Copying Parquet files..."
if [ -d "$BACKEND_DATA" ]; then
    cp -r "$BACKEND_DATA"/* "$KAGGLE_DATASET/$DATASET_NAME/"
    echo "✓ Parquet files copied"
else
    echo "❌ Error: Parquet data not found at $BACKEND_DATA"
    echo "   Run data generation first: python generate_battery_data.py"
    exit 1
fi

# Step 3: Create dataset metadata
echo ""
echo "Step 3: Creating dataset metadata..."
cat > "$KAGGLE_DATASET/dataset-metadata.json" << 'EOF'
{
  "title": "Battery RUL Training Data (Parquet)",
  "id": "khiwnitithadachot/battery-rul-parquet",
  "licenses": [
    {
      "name": "CC0-1.0"
    }
  ],
  "keywords": [
    "battery",
    "rul",
    "remaining useful life",
    "parquet",
    "time-series",
    "predictive maintenance",
    "telemetry",
    "vrla battery"
  ],
  "description": "## Battery RUL Training Data\n\nThis dataset contains battery telemetry data in Parquet format for training Remaining Useful Life (RUL) prediction models.\n\n### Contents\n\n**Master Data** (`master/`):\n- `location.parquet` - Data center locations (9 sites in Thailand)\n- `battery_model.parquet` - Battery model specifications\n- `battery_system.parquet` - UPS/Rectifier system configurations\n- `string.parquet` - Battery string metadata\n- `battery.parquet` - Individual battery metadata\n\n**Telemetry Data** (`telemetry/`):\n- `raw_telemetry.parquet` - Raw sensor readings (voltage, temperature, resistance)\n- `calc_telemetry.parquet` - Calculated metrics (SOC, SOH)\n- `string_raw.parquet` - String-level telemetry\n- `string_calc.parquet` - String-level calculated data\n\n**ML Data** (`ml/`):\n- `rul_predictions.parquet` - RUL labels for supervised learning\n- `feature_store.parquet` - Pre-aggregated ML features\n\n**Operational Data** (`operational/`):\n- `alerts.parquet` - Alert events\n- `maintenance_events.parquet` - Maintenance records\n- `capacity_test_*.parquet` - Capacity test results\n- `impedance_measurement_*.parquet` - Impedance measurements\n\n### Data Schema\n\nSee notebook for detailed schema and usage examples.\n\n### Usage\n\n```python\nimport pandas as pd\nfrom pathlib import Path\n\n# Load telemetry\ndf = pd.read_parquet('/kaggle/input/battery-rul-parquet/telemetry/raw_telemetry.parquet')\n\n# Load RUL labels\ndf_rul = pd.read_parquet('/kaggle/input/battery-rul-parquet/ml/rul_predictions.parquet')\n```\n\n### Source\n\nGenerated using physics-based VRLA battery degradation simulation incorporating Thai environmental conditions (3 seasons, 5 regions)."
}
EOF
echo "✓ Dataset metadata created"

# Step 4: Display dataset statistics
echo ""
echo "Step 4: Dataset statistics..."
echo ""
echo "Directory structure:"
tree -L 2 "$KAGGLE_DATASET/$DATASET_NAME" 2>/dev/null || find "$KAGGLE_DATASET/$DATASET_NAME" -type d | head -20

echo ""
echo "File sizes:"
du -h "$KAGGLE_DATASET/$DATASET_NAME" | sort -h | tail -20

echo ""
echo "Total dataset size:"
du -sh "$KAGGLE_DATASET/$DATASET_NAME"

# Step 5: Verify Parquet files
echo ""
echo "Step 5: Verifying Parquet files..."
python3 << 'PYTHON_SCRIPT'
import pandas as pd
from pathlib import Path

dataset_dir = Path("/teamspace/studios/this_studio/NT/RUL_prediction/kaggle-dataset/battery-rul-parquet")

print("\nParquet file verification:")
print("=" * 60)

parquet_files = list(dataset_dir.rglob("*.parquet"))
total_rows = 0

for pf in sorted(parquet_files):
    try:
        df = pd.read_parquet(pf)
        rows = len(df)
        cols = len(df.columns)
        size_mb = pf.stat().st_size / 1024 / 1024
        rel_path = pf.relative_to(dataset_dir)
        print(f"{str(rel_path):50s} {rows:8,} rows  {cols:3} cols  {size_mb:6.2f} MB")
        total_rows += rows
    except Exception as e:
        print(f"{str(pf):50s} ERROR: {e}")

print("=" * 60)
print(f"Total: {len(parquet_files)} files, {total_rows:,} rows")
PYTHON_SCRIPT

# Step 6: Instructions
echo ""
echo "=========================================="
echo "DATASET READY FOR KAGGLE UPLOAD"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Install Kaggle CLI (if not installed):"
echo "   pip install kaggle"
echo ""
echo "2. Setup Kaggle API credentials:"
echo "   - Download kaggle.json from https://www.kaggle.com/settings/account"
echo "   - Place in ~/.kaggle/kaggle.json"
echo "   - Run: chmod 600 ~/.kaggle/kaggle.json"
echo ""
echo "3. Upload dataset (first time):"
echo "   cd $KAGGLE_DATASET"
echo "   kaggle datasets create -p ."
echo ""
echo "4. Update dataset (subsequent uploads):"
echo "   cd $KAGGLE_DATASET"
echo "   kaggle datasets version -p . -m 'Updated training data'"
echo ""
echo "5. Verify upload:"
echo "   kaggle datasets list --mine"
echo ""
echo "Dataset location: $KAGGLE_DATASET"
echo ""
echo "For full instructions, see: notebooks/KAGGLE_SETUP.md"
echo "=========================================="
