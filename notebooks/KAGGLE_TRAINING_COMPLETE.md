# Kaggle ML Training Setup - Complete

## Summary

Successfully created complete Kaggle GPU training infrastructure for Battery RUL Prediction model.

## Files Created

### 1. Training Notebook
**File**: `notebooks/kaggle_rul_training.ipynb`
- **Size**: Complete Jupyter notebook with 10 sections
- **Features**:
  - GPU-accelerated CatBoost training
  - Loads data from Parquet files
  - Comprehensive feature engineering (14+ features)
  - Derived features (health scores, stress indicators)
  - EDA with visualizations
  - Model evaluation (MAE, RMSE, R²)
  - Feature importance analysis
  - Multiple export formats (CBM, ONNX)
  - Deployment package creation
  - Complete training report

### 2. Kernel Metadata
**File**: `notebooks/kernel-metadata.json`
- Kaggle kernel configuration
- GPU enabled
- Internet enabled for pip installs
- Keywords for discovery

### 3. Setup Guide
**File**: `notebooks/KAGGLE_SETUP.md`
- **Sections**: 10 step-by-step sections
- Complete instructions from API setup to model deployment
- Troubleshooting guide
- Automated pipeline script
- Quick reference commands

### 4. Dataset Preparation Script
**File**: `prepare_kaggle_dataset.sh`
- Automated Parquet dataset packaging
- Metadata generation
- File verification
- Upload instructions

## Notebook Features

### Data Loading
```python
# Loads from Kaggle input directory
DATA_DIR = Path('/kaggle/input/battery-rul-parquet')

# Master data
df_battery = pd.read_parquet(DATA_DIR / 'master' / 'battery.parquet')
df_location = pd.read_parquet(DATA_DIR / 'master' / 'location.parquet')

# Telemetry
df_raw_telemetry = pd.read_parquet(DATA_DIR / 'telemetry' / 'raw_telemetry.parquet')
df_calc_telemetry = pd.read_parquet(DATA_DIR / 'telemetry' / 'calc_telemetry.parquet')

# RUL labels
df_rul = pd.read_parquet(DATA_DIR / 'ml' / 'rul_predictions.parquet')
```

### Feature Engineering
**Voltage Features**:
- `v_mean`, `v_std`, `v_min`, `v_max`, `v_range`
- `v_health_score` (normalized voltage health)

**Temperature Features**:
- `t_mean`, `t_std`, `t_min`, `t_max`, `t_delta_from_ambient`
- `t_stress_score` (temperature stress indicator)

**Resistance Features**:
- `r_internal_latest`, `r_internal_trend`
- `r_degradation_rate` (resistance increase rate)

**Operational Features**:
- `discharge_cycles_count`, `ah_throughput`, `time_at_high_temp_pct`
- `usage_intensity` (Ah per cycle)

### Model Configuration
```python
model = CatBoostRegressor(
    # GPU acceleration
    task_type='GPU',
    devices='0',

    # Hyperparameters
    iterations=2000,
    learning_rate=0.05,
    depth=8,
    l2_leaf_reg=3,

    # Loss & metrics
    loss_function='RMSE',
    eval_metric='MAE',

    # Early stopping
    early_stopping_rounds=100,
    use_best_model=True,

    verbose=100,
    random_seed=42
)
```

### Outputs Generated
1. **rul_model.cbm** - CatBoost model (deployment ready)
2. **rul_model.onnx** - ONNX format (cross-platform)
3. **model_metadata.json** - Complete model info (metrics, features, hyperparameters)
4. **feature_importance.csv** - Feature rankings
5. **rul_model_deployment.zip** - Complete deployment package
6. **TRAINING_REPORT.txt** - Training summary report
7. **Visualizations** (PNG):
   - RUL distribution
   - Feature correlations
   - Predicted vs Actual scatter
   - Residual plots
   - Error distribution
   - Feature importance chart

## Usage Workflow

### 1. Prepare Dataset
```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction
./prepare_kaggle_dataset.sh
```

### 2. Upload to Kaggle
```bash
# First time
cd kaggle-dataset
kaggle datasets create -p .

# Updates
kaggle datasets version -p . -m "Updated data"
```

### 3. Push Notebook
```bash
cd notebooks
kaggle kernels push -p .
```

### 4. Run on Kaggle
- Open notebook on Kaggle.com
- Enable GPU (P100 or T4)
- Click "Run All"
- Wait for completion (~10-30 mins)

### 5. Download Model
```bash
kaggle kernels output khiwnitithadachot/kaggle-notebook-optimized -p ./model
```

### 6. Deploy to Backend
```bash
cp model/rul_model.cbm backend/models/
cp model/model_metadata.json backend/models/
```

## Expected Performance

### Training Time
- **Small dataset** (2 days, 24 batteries): ~5 minutes
- **Medium dataset** (7 days, 216 batteries): ~15 minutes
- **Large dataset** (30 days, 1,944 batteries): ~45 minutes

### Model Metrics (Expected)
- **MAE**: 10-20 days
- **RMSE**: 15-30 days
- **R²**: 0.85-0.95
- **Accuracy within 7 days**: 60-70%
- **Accuracy within 30 days**: 85-95%

## Cost
- **Kaggle GPU**: FREE (30 hours/week)
- **Storage**: FREE (20 GB datasets + 20 GB outputs)
- **Internet**: FREE

## Integration with ML Pipeline

Once model is trained and downloaded:

1. **Load model in FastAPI**:
```python
# backend/src/services/ml_service.py
from catboost import CatBoostRegressor

class MLService:
    def __init__(self):
        self.model = CatBoostRegressor()
        self.model.load_model('models/rul_model.cbm')

    def predict_rul(self, features: dict) -> float:
        X = pd.DataFrame([features])
        prediction = self.model.predict(X[self.model.feature_names_])
        return float(prediction[0])
```

2. **Create API endpoint**:
```python
# backend/src/api/v1/ml.py
@router.post("/predict-rul")
async def predict_rul(battery_id: str):
    features = await feature_service.get_latest_features(battery_id)
    rul_days = ml_service.predict_rul(features)
    return {"battery_id": battery_id, "rul_days": rul_days}
```

3. **Connect to real-time telemetry**:
- Sensor simulator → PostgreSQL → Feature extraction → ML prediction
- Store predictions in `rul_predictions` table
- Trigger alerts if RUL < threshold

## Next Steps

1. **Generate larger training dataset**:
   ```bash
   cd data-synthesis
   python generate_battery_data.py --duration-days 30 --limit-batteries 216 --sampling-seconds 60
   ```

2. **Convert to Parquet and upload**:
   ```bash
   cd backend
   python scripts/convert_to_parquet.py --csv-dir ../data-synthesis/output/30day
   cd ..
   ./prepare_kaggle_dataset.sh
   kaggle datasets version -p kaggle-dataset/ -m "30-day training data"
   ```

3. **Retrain model**:
   - Kaggle will automatically use updated dataset
   - Re-run notebook
   - Download improved model

4. **Deploy to production**:
   - Load model in backend
   - Test API endpoints
   - Connect to Railway deployment
   - Monitor prediction accuracy

## Troubleshooting

### Common Issues

**1. Dataset not found**
- Verify dataset upload: `kaggle datasets list --mine`
- Check notebook DATA_DIR path
- Ensure dataset is public or notebook has access

**2. GPU not available**
- Check kernel settings: Enable GPU (P100 or T4)
- Verify in notebook: `CatBoostRegressor()._get_gpu_device_count() > 0`

**3. Out of memory**
- Reduce iterations: `iterations=1000`
- Reduce tree depth: `depth=6`
- Sample data: `df = df.sample(frac=0.5)`

**4. Training timeout**
- Kaggle limit: 9 hours
- Split into multiple notebooks
- Save checkpoints
- Use smaller sample for testing

## Files Reference

```
RUL_prediction/
├── notebooks/
│   ├── kaggle_rul_training.ipynb      # Main training notebook
│   ├── kernel-metadata.json           # Kaggle kernel config
│   ├── KAGGLE_SETUP.md               # Complete setup guide
│   └── KAGGLE_TRAINING_COMPLETE.md   # This file
├── kaggle-dataset/                    # Created by prepare script
│   ├── dataset-metadata.json
│   └── battery-rul-parquet/          # Parquet data copy
│       ├── master/
│       ├── telemetry/
│       ├── ml/
│       └── operational/
└── prepare_kaggle_dataset.sh         # Dataset preparation script
```

## Status

✅ **Notebook Created**: Complete 10-section training pipeline
✅ **Metadata Configured**: Kaggle kernel setup
✅ **Documentation Complete**: Setup guide with troubleshooting
✅ **Preparation Script**: Automated dataset packaging

## Ready for Upload

All files are ready for Kaggle upload. Follow the steps in `KAGGLE_SETUP.md` to:
1. Setup Kaggle API
2. Upload dataset
3. Push notebook
4. Run training
5. Download trained model

**Estimated time to first trained model**: 30-60 minutes (including setup)

---

**Status**: 🟢 Complete and ready for Kaggle execution
**Created**: 2025-12-01
**Next Action**: Follow KAGGLE_SETUP.md steps 1-7
