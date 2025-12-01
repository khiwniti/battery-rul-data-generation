# Kaggle Notebook Setup & Execution Guide

## Overview

This guide explains how to upload, run, and download the Battery RUL Prediction training notebook on Kaggle with GPU support.

## Prerequisites

1. **Kaggle Account**: Create account at https://kaggle.com
2. **Kaggle API**: Install Kaggle CLI tool
3. **Training Data**: Parquet files from data generation

## Step 1: Install Kaggle CLI

```bash
pip install kaggle
```

## Step 2: Setup Kaggle API Credentials

1. Go to https://www.kaggle.com/settings/account
2. Scroll to "API" section
3. Click "Create New Token"
4. Download `kaggle.json`
5. Move to credentials directory:

```bash
# Linux/Mac
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
mkdir %USERPROFILE%\.kaggle
move %USERPROFILE%\Downloads\kaggle.json %USERPROFILE%\.kaggle\kaggle.json
```

## Step 3: Upload Training Data as Kaggle Dataset

First, create a Kaggle dataset from your Parquet files:

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction

# Create dataset directory structure
mkdir -p kaggle-dataset/battery-rul-parquet
cp -r backend/data/parquet/* kaggle-dataset/battery-rul-parquet/

# Create dataset metadata
cat > kaggle-dataset/dataset-metadata.json << 'EOF'
{
  "title": "Battery RUL Training Data (Parquet)",
  "id": "khiwnitithadachot/battery-rul-parquet",
  "licenses": [{"name": "CC0-1.0"}],
  "keywords": ["battery", "rul", "parquet", "time-series"],
  "description": "Battery telemetry data in Parquet format for RUL prediction training. Includes master data, raw telemetry, calculated metrics, and RUL labels."
}
EOF

# Upload dataset to Kaggle
cd kaggle-dataset
kaggle datasets create -p .
```

After first upload, to update the dataset:

```bash
kaggle datasets version -p . -m "Updated dataset with new samples"
```

## Step 4: Upload Notebook to Kaggle

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/notebooks

# Push notebook as new kernel
kaggle kernels push -p .
```

**Expected output:**
```
Kernel version X pushed successfully
```

## Step 5: Run Notebook on Kaggle

### Option A: Via Web Interface (Recommended for first run)

1. Go to https://www.kaggle.com/code/khiwnitithadachot/kaggle-notebook-optimized
2. Click "Edit" button
3. In right sidebar:
   - **Accelerator**: Select "GPU P100" (or T4)
   - **Internet**: Enable (for pip installs)
4. Click "Run All" button
5. Monitor execution in real-time
6. Wait for completion (~10-30 minutes depending on data size)

### Option B: Via CLI (Push & Auto-run)

```bash
# Run the notebook remotely
kaggle kernels push -p . --kernel-type notebook
```

## Step 6: Monitor Execution Status

```bash
# Check kernel status
kaggle kernels status khiwnitithadachot/kaggle-notebook-optimized

# View kernel output/logs
kaggle kernels output khiwnitithadachot/kaggle-notebook-optimized
```

## Step 7: Download Trained Model

Once execution completes (status shows "complete"):

```bash
# Download all outputs to local directory
kaggle kernels output khiwnitithadachot/kaggle-notebook-optimized -p ./model

# Or specify custom destination
kaggle kernels output khiwnitithadachot/kaggle-notebook-optimized -p /teamspace/studios/this_studio/NT/RUL_prediction/ml-pipeline/models/
```

**Downloaded files include:**
```
model/
├── rul_model.cbm                      # CatBoost model (main)
├── rul_model.onnx                     # ONNX format (optional)
├── model_metadata.json                # Complete model info
├── feature_importance.csv             # Feature rankings
├── rul_model_deployment.zip           # Complete deployment package
├── TRAINING_REPORT.txt                # Training summary
└── *.png                              # Visualization plots
```

## Step 8: Verify Model Download

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/ml-pipeline/models

# Check downloaded files
ls -lh

# Verify model metadata
cat model_metadata.json | jq '.metrics.test'
```

**Expected output:**
```json
{
  "mae": 15.23,
  "rmse": 21.45,
  "r2": 0.9234
}
```

## Step 9: Test Model Locally

```python
from catboost import CatBoostRegressor
import pandas as pd

# Load model
model = CatBoostRegressor()
model.load_model('model/rul_model.cbm')

# Load test data
test_data = pd.read_parquet('backend/data/parquet/ml/feature_store.parquet')

# Make predictions
predictions = model.predict(test_data[model.feature_names_])

print(f"Predictions: {predictions[:10]}")
```

## Step 10: Deploy to Backend

```bash
# Copy model to backend directory
cp model/rul_model.cbm backend/models/
cp model/model_metadata.json backend/models/

# Update backend to load model
# (See ml-pipeline integration documentation)
```

## Troubleshooting

### Issue: "Dataset not found"
**Solution**: Update notebook cell to use correct dataset path:
```python
DATA_DIR = Path('/kaggle/input/battery-rul-parquet')
```

### Issue: "GPU out of memory"
**Solution**: Reduce batch size or iterations:
```python
model = CatBoostRegressor(
    iterations=1000,  # Reduce from 2000
    # ... other params
)
```

### Issue: "Notebook execution timeout"
**Solution**: Kaggle has 9-hour limit. For large datasets:
- Use smaller sample for initial training
- Save checkpoints during training
- Split into multiple notebooks

### Issue: "Can't download outputs"
**Solution**: Wait for kernel to complete:
```bash
# Check status first
kaggle kernels status khiwnitithadachot/kaggle-notebook-optimized

# Should show: "complete" (not "running" or "error")
```

## Advanced: Automated Pipeline

Create a script to automate the entire process:

```bash
#!/bin/bash
# train_on_kaggle.sh

set -e

echo "1. Uploading dataset..."
cd kaggle-dataset
kaggle datasets version -p . -m "Training run $(date +%Y%m%d)"

echo "2. Pushing notebook..."
cd ../notebooks
kaggle kernels push -p .

echo "3. Waiting for completion..."
while true; do
    STATUS=$(kaggle kernels status khiwnitithadachot/kaggle-notebook-optimized | grep "status" | awk '{print $2}')
    echo "Status: $STATUS"

    if [ "$STATUS" = "complete" ]; then
        break
    elif [ "$STATUS" = "error" ]; then
        echo "Error: Kernel execution failed"
        exit 1
    fi

    sleep 60
done

echo "4. Downloading model..."
kaggle kernels output khiwnitithadachot/kaggle-notebook-optimized -p ../ml-pipeline/models/

echo "5. Done! Model ready for deployment."
```

## Model Update Workflow

When you need to retrain with new data:

1. Generate new training data
2. Update Kaggle dataset: `kaggle datasets version`
3. Re-run notebook on Kaggle
4. Download updated model
5. Deploy to production

## Cost Considerations

- **Kaggle GPU**: FREE (30 hours/week limit)
- **Storage**: FREE (20 GB datasets + 20 GB outputs)
- **Internet**: FREE (enabled by default)

## Performance Expectations

**Training Time (typical dataset):**
- Small (2 days, 24 batteries): ~5 minutes
- Medium (7 days, 216 batteries): ~15 minutes
- Large (30 days, 1944 batteries): ~45 minutes

**Model Performance (expected):**
- MAE: 10-20 days
- RMSE: 15-30 days
- R²: 0.85-0.95

## Next Steps After Training

1. **Validate Model**: Test on held-out batteries
2. **Integrate Backend**: Load model in FastAPI service
3. **Deploy ML Pipeline**: Connect to real-time telemetry
4. **Monitor Performance**: Track prediction accuracy
5. **Retrain Periodically**: Update with new data

## Support

- **Kaggle Docs**: https://www.kaggle.com/docs/api
- **CatBoost Docs**: https://catboost.ai/docs/
- **Project Repo**: (your GitHub URL)

## Quick Reference Commands

```bash
# Upload dataset
kaggle datasets create -p kaggle-dataset/

# Update dataset
kaggle datasets version -p kaggle-dataset/ -m "Update message"

# Push notebook
kaggle kernels push -p notebooks/

# Check status
kaggle kernels status khiwnitithadachot/kaggle-notebook-optimized

# Download model
kaggle kernels output khiwnitithadachot/kaggle-notebook-optimized -p ./model

# List your kernels
kaggle kernels list --mine

# List your datasets
kaggle datasets list --mine
```

## File Checklist

Before pushing to Kaggle, verify these files exist:

- ✅ `notebooks/kaggle_rul_training.ipynb` - Main notebook
- ✅ `notebooks/kernel-metadata.json` - Kaggle kernel config
- ✅ `kaggle-dataset/battery-rul-parquet/` - Training data
- ✅ `kaggle-dataset/dataset-metadata.json` - Dataset config
- ✅ `~/.kaggle/kaggle.json` - API credentials

---

**Ready to train!** Follow steps 1-7 to execute your first GPU training run on Kaggle.
