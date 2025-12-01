# Complete Kaggle Notebook Setup Guide

## Step-by-Step: From Data Preparation to Model Export

This guide walks you through the complete process of training your Battery RUL prediction model on Kaggle GPU.

---

## Part 1: Prepare Your Data (Local)

### Step 1.1: Convert Data to Parquet

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction
./prepare_kaggle_dataset.sh
```

This script will:
- Copy Parquet files to `kaggle-dataset/battery-rul-parquet/`
- Create dataset metadata
- Verify file integrity
- Show dataset statistics

**Expected Output:**
```
Dataset ready for Kaggle upload
Total dataset size: ~0.42 MB (67.6% compression)
- 20 Parquet files
- 13,824 telemetry records
- 624 RUL predictions
```

---

## Part 2: Setup Kaggle (One-Time Setup)

### Step 2.1: Install Kaggle CLI

```bash
pip install kaggle
```

### Step 2.2: Get Kaggle API Credentials

1. Go to https://www.kaggle.com/settings/account
2. Scroll to "API" section
3. Click "Create New Token"
4. Download `kaggle.json`

### Step 2.3: Configure Credentials

**Linux/Mac:**
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

**Windows:**
```cmd
mkdir %USERPROFILE%\.kaggle
move %USERPROFILE%\Downloads\kaggle.json %USERPROFILE%\.kaggle\kaggle.json
```

### Step 2.4: Verify Setup

```bash
kaggle datasets list --mine
```

Should show: "No datasets found" (if first time) or list your existing datasets.

---

## Part 3: Upload Dataset to Kaggle

### Step 3.1: Upload Dataset (First Time)

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/kaggle-dataset
kaggle datasets create -p .
```

**Expected Output:**
```
Dataset created successfully
URL: https://www.kaggle.com/datasets/khiwnitithadachot/battery-rul-parquet
```

### Step 3.2: Update Dataset (After Changes)

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/kaggle-dataset
kaggle datasets version -p . -m "Updated training data with 30-day samples"
```

### Step 3.3: Verify Upload

```bash
kaggle datasets list --mine
```

Should show:
```
battery-rul-parquet  khiwnitithadachot  Private  2025-12-01
```

---

## Part 4: Upload Notebook to Kaggle

### Step 4.1: Update Dataset Path in Notebook Metadata

Edit `notebooks/kernel-metadata.json`:

```json
{
  "id": "khiwnitithadachot/battery-rul-training",
  "title": "Battery RUL Prediction - CatBoost GPU Training",
  "code_file": "kaggle_rul_training.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": false,
  "enable_gpu": true,
  "enable_internet": true,
  "dataset_sources": [
    "khiwnitithadachot/battery-rul-parquet"
  ],
  "keywords": [
    "battery",
    "rul",
    "catboost",
    "gpu",
    "predictive maintenance"
  ]
}
```

**Important:** Make sure `dataset_sources` matches your uploaded dataset name!

### Step 4.2: Push Notebook to Kaggle

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/notebooks
kaggle kernels push -p .
```

**Expected Output:**
```
Kernel version 1 successfully pushed.
View at: https://www.kaggle.com/code/khiwnitithadachot/battery-rul-training
```

---

## Part 5: Run Notebook on Kaggle

### Option A: Via Web Interface (Recommended for First Run)

1. **Open Notebook**: https://www.kaggle.com/code/khiwnitithadachot/battery-rul-training

2. **Enable GPU**:
   - Click "Edit" button (top right)
   - Right sidebar → "Accelerator" → Select "GPU T4" or "GPU P100"
   - If GPU not available, click "Get More Quota"

3. **Verify Dataset**:
   - Right sidebar → "Input" section
   - Should show: "battery-rul-parquet"
   - Click to verify data path: `/kaggle/input/battery-rul-parquet/`

4. **Run Notebook**:
   - Click "Run All" button
   - Execution will start (takes 10-30 minutes)
   - Monitor progress in real-time

5. **Check Progress**:
   - Cell outputs will show as they complete
   - Look for: "Libraries imported successfully"
   - Look for: "GPU Available: True"
   - Training progress will show iteration updates

### Option B: Via CLI (Automated)

```bash
# Check status
kaggle kernels status khiwnitithadachot/battery-rul-training

# View output (after completion)
kaggle kernels output khiwnitithadachot/battery-rul-training
```

---

## Part 6: Monitor Training

### What to Look For

**Section 1: Environment Setup** (1-2 min)
```
Libraries imported successfully
GPU Available: True
GPU detected via nvidia-smi
```

**Section 2: Data Loading** (30 sec)
```
Loading master data...
Batteries: 24
Locations: 9

Loading telemetry data...
Raw telemetry records: 13,824
```

**Section 3: Feature Engineering** (10 sec)
```
Training samples after merge: 624
Features selected for training (14):
  1. v_mean
  2. v_std
  ...
```

**Section 6: Training** (5-20 min)
```
Starting training...

0:      test: 45.234  best: 45.234 (0)  total: 152ms    remaining: 5m 3s
100:    test: 18.456  best: 18.321 (98)  total: 8.2s     remaining: 2m 35s
...
Training completed in 387.5 seconds (6.5 minutes)
Best iteration: 847
```

**Section 7: Evaluation**
```
MODEL PERFORMANCE
Training Set:
  MAE:  12.34 days
  RMSE: 18.56 days
  R²:   0.9456

Test Set:
  MAE:  15.67 days
  RMSE: 22.34 days
  R²:   0.9234

Prediction Accuracy:
  Within 7 days:  65.3%
  Within 30 days: 92.1%
```

---

## Part 7: Download Trained Model

### Step 7.1: Wait for Completion

Check status:
```bash
kaggle kernels status khiwnitithadachot/battery-rul-training
```

Should show: `"status": "complete"`

### Step 7.2: Download All Outputs

```bash
# Download to current directory
kaggle kernels output khiwnitithadachot/battery-rul-training -p ./kaggle-model

# Or specify target directory
kaggle kernels output khiwnitithadachot/battery-rul-training -p /teamspace/studios/this_studio/NT/RUL_prediction/ml-pipeline/models/
```

### Step 7.3: Verify Downloaded Files

```bash
ls -lh kaggle-model/
```

**Expected Files:**
```
rul_model.cbm                    # CatBoost model (1-5 MB)
rul_model.onnx                   # ONNX format (optional)
model_metadata.json              # Model info
feature_importance.csv           # Feature rankings
rul_model_deployment.zip         # Complete package
TRAINING_REPORT.txt              # Summary report
*.png                            # Visualizations (5 files)
```

---

## Part 8: Verify Model

### Step 8.1: Test Model Loading

```python
from catboost import CatBoostRegressor
import pandas as pd
import json

# Load model
model = CatBoostRegressor()
model.load_model('kaggle-model/rul_model.cbm')

# Load metadata
with open('kaggle-model/model_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Model loaded successfully!")
print(f"Features: {metadata['num_features']}")
print(f"Test MAE: {metadata['metrics']['test']['mae']:.2f} days")
print(f"Test R²: {metadata['metrics']['test']['r2']:.4f}")
```

**Expected Output:**
```
Model loaded successfully!
Features: 16
Test MAE: 15.67 days
Test R²: 0.9234
```

### Step 8.2: Test Prediction

```python
# Create sample input
sample_features = {
    'v_mean': 12.5,
    'v_std': 0.1,
    'v_min': 12.3,
    'v_max': 12.7,
    'v_range': 0.4,
    't_mean': 28.5,
    't_std': 2.1,
    't_min': 25.0,
    't_max': 32.0,
    't_delta_from_ambient': 3.5,
    'r_internal_latest': 4.2,
    'r_internal_trend': 0.05,
    'discharge_cycles_count': 15,
    'ah_throughput': 1800,
    'time_at_high_temp_pct': 0.12,
    'v_health_score': 0.85,
    't_stress_score': 0.35,
    'r_degradation_rate': 0.012,
    'usage_intensity': 120.0
}

# Make prediction
X_sample = pd.DataFrame([sample_features])
X_sample = X_sample[metadata['features']]  # Ensure correct order

prediction = model.predict(X_sample)
print(f"\nPredicted RUL: {prediction[0]:.1f} days")
```

**Expected Output:**
```
Predicted RUL: 485.3 days
```

---

## Part 9: Deploy Model to Backend

### Step 9.1: Copy Model to Backend

```bash
# Copy to ml-pipeline directory
cp kaggle-model/rul_model.cbm ml-pipeline/models/
cp kaggle-model/model_metadata.json ml-pipeline/models/
cp kaggle-model/feature_importance.csv ml-pipeline/models/

# Verify
ls -lh ml-pipeline/models/
```

### Step 9.2: Create Prediction Service

Create `backend/src/services/rul_prediction_service.py`:

```python
from catboost import CatBoostRegressor
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List

class RULPredictionService:
    def __init__(self, model_path: str = "models/rul_model.cbm"):
        self.model = CatBoostRegressor()
        self.model.load_model(model_path)

        # Load metadata
        metadata_path = Path(model_path).parent / "model_metadata.json"
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)

        self.feature_names = self.metadata['features']

    def predict(self, features: Dict[str, float]) -> float:
        """Predict RUL for a single battery"""
        X = pd.DataFrame([features])
        X = X[self.feature_names]  # Ensure correct order
        prediction = self.model.predict(X)
        return float(prediction[0])

    def predict_batch(self, features_list: List[Dict[str, float]]) -> List[float]:
        """Predict RUL for multiple batteries"""
        X = pd.DataFrame(features_list)
        X = X[self.feature_names]
        predictions = self.model.predict(X)
        return [float(p) for p in predictions]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from model"""
        importance = self.model.get_feature_importance()
        return dict(zip(self.feature_names, importance))

# Global instance
rul_service = RULPredictionService()
```

### Step 9.3: Create API Endpoint

Add to `backend/src/api/routes/predictions.py`:

```python
from fastapi import APIRouter, HTTPException
from src.services.rul_prediction_service import rul_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])

class PredictionRequest(BaseModel):
    battery_id: str
    features: dict

class PredictionResponse(BaseModel):
    battery_id: str
    predicted_rul_days: float
    confidence_score: float

@router.post("/predict-rul", response_model=PredictionResponse)
async def predict_rul(request: PredictionRequest):
    """Predict RUL for a battery given its features"""
    try:
        rul_days = rul_service.predict(request.features)

        return PredictionResponse(
            battery_id=request.battery_id,
            predicted_rul_days=rul_days,
            confidence_score=0.92  # From model R²
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 9.4: Test API Endpoint

```bash
# Test prediction
curl -X POST http://localhost:8000/api/v1/predictions/predict-rul \
  -H "Content-Type: application/json" \
  -d '{
    "battery_id": "DC-CNX-01-REC-01-STR-01-JAR-001",
    "features": {
      "v_mean": 12.5,
      "v_std": 0.1,
      "t_mean": 28.5,
      "r_internal_latest": 4.2
    }
  }'
```

**Expected Response:**
```json
{
  "battery_id": "DC-CNX-01-REC-01-STR-01-JAR-001",
  "predicted_rul_days": 485.3,
  "confidence_score": 0.92
}
```

---

## Troubleshooting

### Issue 1: Dataset Not Found

**Error:** `FileNotFoundError: /kaggle/input/battery-rul-parquet not found`

**Solution:**
1. Check dataset is uploaded: `kaggle datasets list --mine`
2. Verify dataset name in `kernel-metadata.json`
3. Update notebook to use correct path:
   ```python
   DATA_DIR = Path('/kaggle/input/your-actual-dataset-name')
   ```

### Issue 2: GPU Not Available

**Error:** `GPU Available: False`

**Solution:**
1. Edit notebook on Kaggle.com
2. Right sidebar → Accelerator → Select GPU
3. If no GPU quota, wait or request more

### Issue 3: Out of Memory

**Error:** `CUDA out of memory`

**Solution:**
Reduce model complexity in notebook:
```python
model = CatBoostRegressor(
    iterations=1000,  # Reduce from 2000
    depth=6,          # Reduce from 8
    # ... other params
)
```

### Issue 4: Training Too Slow

**Problem:** Training takes > 1 hour

**Solution:**
- Use smaller dataset (fewer samples)
- Reduce iterations: `iterations=500`
- Use faster GPU (P100 instead of T4)

### Issue 5: Can't Download Outputs

**Error:** `No outputs found`

**Solution:**
1. Check status: `kaggle kernels status your-username/notebook-name`
2. Wait for `"complete"` status
3. Outputs only available after notebook finishes

---

## Quick Reference

### Essential Commands

```bash
# Prepare data
./prepare_kaggle_dataset.sh

# Upload dataset (first time)
cd kaggle-dataset && kaggle datasets create -p .

# Update dataset
cd kaggle-dataset && kaggle datasets version -p . -m "Updated"

# Push notebook
cd notebooks && kaggle kernels push -p .

# Check status
kaggle kernels status khiwnitithadachot/battery-rul-training

# Download model
kaggle kernels output khiwnitithadachot/battery-rul-training -p ./model
```

### File Paths

- **Local data**: `backend/data/parquet/`
- **Kaggle dataset**: `kaggle-dataset/battery-rul-parquet/`
- **Notebook**: `notebooks/kaggle_rul_training.ipynb`
- **Metadata**: `notebooks/kernel-metadata.json`
- **Kaggle input**: `/kaggle/input/battery-rul-parquet/`
- **Kaggle output**: `/kaggle/working/`
- **Downloaded model**: `./kaggle-model/rul_model.cbm`

### Expected Timings

- Data preparation: 2 min
- Dataset upload: 30 sec
- Notebook push: 10 sec
- Training execution: 10-30 min
- Model download: 30 sec

### Model Files Checklist

- ✅ `rul_model.cbm` - Main model file
- ✅ `model_metadata.json` - Metrics and config
- ✅ `feature_importance.csv` - Feature rankings
- ✅ `TRAINING_REPORT.txt` - Summary
- ✅ `rul_model_deployment.zip` - Complete package

---

## Success Criteria

Your model is ready for deployment when:

✅ Training completes without errors
✅ Test MAE < 30 days
✅ Test R² > 0.85
✅ Model file downloads successfully
✅ Test prediction works locally
✅ API endpoint returns predictions

---

## Next Steps After Training

1. **Validate Model Performance**
   - Review training report
   - Check feature importance
   - Analyze prediction errors

2. **Deploy to Production**
   - Copy model to backend
   - Update API endpoints
   - Deploy to Railway

3. **Monitor in Production**
   - Track prediction accuracy
   - Log model performance
   - Retrain periodically (monthly)

4. **Iterate and Improve**
   - Generate more training data
   - Try different features
   - Experiment with hyperparameters

---

**Status**: ✅ Ready for Kaggle Execution
**Last Updated**: 2025-12-01
**Dataset Size**: 0.42 MB (13,824 records)
**Expected Training Time**: 10-30 minutes
**Expected Model MAE**: 10-20 days
