# Kaggle Training - Quick Start Checklist

Use this checklist to quickly train your model on Kaggle GPU.

## ✅ Pre-Flight Checklist

### Local Setup
- [ ] Data generated: `13,824 telemetry records ✓`
- [ ] Parquet files ready: `504 KB dataset ✓`
- [ ] Notebook prepared: `kaggle_rul_training.ipynb ✓`

### Kaggle Account
- [ ] Kaggle account created
- [ ] API token downloaded (`kaggle.json`)
- [ ] Kaggle CLI installed: `pip install kaggle`
- [ ] Credentials configured in `~/.kaggle/kaggle.json`

**Verify:** Run `kaggle datasets list --mine`

---

## 🚀 Upload Workflow (5 minutes)

### Step 1: Upload Dataset
```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/kaggle-dataset
kaggle datasets create -p .
```

**Expected:** `Dataset created successfully`
**URL:** https://www.kaggle.com/datasets/khiwnitithadachot/battery-rul-parquet

- [ ] Dataset uploaded successfully
- [ ] Dataset URL noted

### Step 2: Update Notebook Metadata

Edit `notebooks/kernel-metadata.json`:
```json
"dataset_sources": [
  "khiwnitithadachot/battery-rul-parquet"  ← Update this line
]
```

- [ ] Dataset name updated in metadata
- [ ] Metadata file saved

### Step 3: Push Notebook
```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction/notebooks
kaggle kernels push -p .
```

**Expected:** `Kernel version 1 successfully pushed`
**URL:** https://www.kaggle.com/code/khiwnitithadachot/battery-rul-training

- [ ] Notebook pushed successfully
- [ ] Notebook URL noted

---

## 🎯 Execute Training (10-30 minutes)

### Via Web Interface (Recommended)

1. **Open Notebook**
   - [ ] Visit your notebook URL
   - [ ] Click "Edit" button

2. **Configure GPU**
   - [ ] Right sidebar → Accelerator
   - [ ] Select "GPU P100" or "GPU T4"
   - [ ] GPU indicator shows green

3. **Verify Dataset**
   - [ ] Right sidebar → Input
   - [ ] See "battery-rul-parquet" listed
   - [ ] Path: `/kaggle/input/battery-rul-parquet/`

4. **Run Training**
   - [ ] Click "Run All" button
   - [ ] Confirm execution starts
   - [ ] Monitor first cell output

5. **Monitor Progress**
   - [ ] Cell 1: "Libraries imported successfully" ✓
   - [ ] Cell 2: "GPU Available: True" ✓
   - [ ] Cell 3: "Loading master data..." ✓
   - [ ] Cell 6: "Starting training..." ✓
   - [ ] Training iterations display
   - [ ] "Training completed" message ✓

---

## 📊 Training Checkpoints

### Initialization (Minutes 0-2)
```
✓ Libraries imported successfully
✓ GPU Available: True
✓ Loading master data... Batteries: 24
✓ Loading telemetry data... 13,824 records
✓ Loading RUL predictions... 624 records
```

- [ ] All libraries loaded
- [ ] GPU detected
- [ ] All data files loaded

### Feature Engineering (Minutes 2-3)
```
✓ Training samples after merge: 624
✓ Features selected for training (16)
✓ Total features after engineering: 16
```

- [ ] Features merged successfully
- [ ] No missing features warning
- [ ] Feature count correct

### Training Phase (Minutes 3-25)
```
0:      test: 45.234  best: 45.234 (0)
100:    test: 18.456  best: 18.321 (98)
...
1000:   test: 12.543  best: 12.234 (847)

Training completed in 387.5 seconds (6.5 minutes)
Best iteration: 847
```

- [ ] Training iterations start
- [ ] Test score decreasing
- [ ] Training completes successfully
- [ ] Best iteration identified

### Evaluation (Minutes 25-27)
```
MODEL PERFORMANCE
Test Set:
  MAE:  15.67 days
  RMSE: 22.34 days
  R²:   0.9234
```

- [ ] Test MAE < 30 days ✓
- [ ] Test R² > 0.85 ✓
- [ ] Reasonable performance

### Export (Minutes 27-30)
```
Model saved (CatBoost): /kaggle/working/rul_model.cbm
Model saved (ONNX): /kaggle/working/rul_model.onnx
Deployment package created: rul_model_deployment.zip
```

- [ ] Model saved successfully
- [ ] Metadata saved
- [ ] Deployment package created
- [ ] Training report generated

---

## 📥 Download Model

### Check Status
```bash
kaggle kernels status khiwnitithadachot/battery-rul-training
```

**Expected:** `"status": "complete"`

- [ ] Kernel status is "complete"
- [ ] No error messages

### Download Files
```bash
kaggle kernels output khiwnitithadachot/battery-rul-training -p ./kaggle-model
```

**Expected Files:**
```
kaggle-model/
├── rul_model.cbm                 ✓ Main model
├── rul_model.onnx                ✓ ONNX format
├── model_metadata.json           ✓ Metrics
├── feature_importance.csv        ✓ Rankings
├── rul_model_deployment.zip      ✓ Package
├── TRAINING_REPORT.txt           ✓ Summary
└── *.png (5 files)               ✓ Plots
```

- [ ] All files downloaded
- [ ] Model file exists (1-5 MB)
- [ ] Metadata file valid JSON

---

## ✅ Verification

### Test Model Loading
```python
from catboost import CatBoostRegressor
model = CatBoostRegressor()
model.load_model('kaggle-model/rul_model.cbm')
print("Model loaded successfully!")
```

- [ ] Model loads without errors
- [ ] No import errors

### Test Prediction
```python
import pandas as pd
sample = pd.DataFrame([{
    'v_mean': 12.5, 'v_std': 0.1, 't_mean': 28.5,
    'r_internal_latest': 4.2, # ... other features
}])
prediction = model.predict(sample)
print(f"Predicted RUL: {prediction[0]:.1f} days")
```

- [ ] Prediction runs successfully
- [ ] Prediction value reasonable (100-800 days)

### Review Metrics
```bash
cat kaggle-model/TRAINING_REPORT.txt
```

**Check:**
- [ ] Test MAE: _____ days (should be < 30)
- [ ] Test R²: _____ (should be > 0.85)
- [ ] Training time: _____ minutes
- [ ] Best iteration: _____

---

## 🎉 Success Criteria

Your model is production-ready when ALL of these are true:

- [x] Training completed without errors
- [x] Test MAE < 30 days
- [x] Test R² > 0.85
- [x] Within 30 days accuracy > 80%
- [x] Model file downloaded successfully
- [x] Test prediction works locally
- [x] All output files present

**Overall Status:** ☐ READY FOR DEPLOYMENT

---

## 🚨 Common Issues & Quick Fixes

### Issue: Dataset Not Found
**Symptom:** `FileNotFoundError: /kaggle/input/battery-rul-parquet`

**Fix:**
1. Check dataset uploaded: `kaggle datasets list --mine`
2. Update `kernel-metadata.json` with correct dataset name
3. Re-push notebook: `kaggle kernels push -p .`

### Issue: No GPU Available
**Symptom:** `GPU Available: False`

**Fix:**
1. Edit notebook on Kaggle.com
2. Right sidebar → Accelerator → Select GPU
3. Save and re-run

### Issue: Training Too Slow
**Symptom:** > 1 hour training time

**Fix:**
Reduce iterations in notebook cell:
```python
model = CatBoostRegressor(
    iterations=1000,  # Reduce from 2000
    depth=6,          # Reduce from 8
```

### Issue: Can't Download Outputs
**Symptom:** `No outputs found`

**Fix:**
1. Wait for kernel to finish
2. Check status shows "complete"
3. Refresh outputs: `kaggle kernels output ...`

---

## 📝 Notes & Observations

**Training Date:** _________________
**Training Duration:** _______ minutes
**Test MAE:** _______ days
**Test R²:** _______
**GPU Used:** P100 / T4 (circle one)

**Issues Encountered:**
-
-

**Performance Notes:**
-
-

**Next Actions:**
- [ ] Deploy model to backend
- [ ] Test API endpoint
- [ ] Update Railway deployment
- [ ] Generate larger training dataset
- [ ] Retrain with more data

---

**Checklist Complete:** ☐ YES ☐ NO
**Ready for Deployment:** ☐ YES ☐ NO
**Completed By:** _________________
**Date:** _________________
