# 🚀 One-Command Kaggle Training

## Complete End-to-End Automation

Train your Battery RUL prediction model on Kaggle GPU with a single command!

```bash
./run_kaggle_training.sh
```

That's it! The script handles everything:
- ✅ Dataset upload
- ✅ Notebook configuration
- ✅ GPU training
- ✅ Model download
- ✅ Verification

---

## What This Script Does

### Automatic Steps (7 phases)

**1. Prerequisites Check** (30 seconds)
- Verifies Kaggle CLI installed
- Checks API credentials
- Validates dataset prepared
- Confirms notebook ready

**2. Dataset Upload** (1-2 minutes)
- Uploads Parquet files to Kaggle
- Or updates existing dataset
- Gets dataset URL automatically
- Shows upload status

**3. Notebook Configuration** (5 seconds)
- Auto-updates `kernel-metadata.json`
- Sets correct dataset reference
- Enables GPU and internet
- Validates configuration

**4. Notebook Push** (30 seconds)
- Pushes notebook to Kaggle
- Gets kernel URL
- Confirms successful upload

**5. Training Monitoring** (10-30 minutes)
- Opens notebook URL for you
- Optional CLI monitoring
- Checks status every 30 seconds
- Waits for completion

**6. Model Download** (1 minute)
- Downloads all outputs
- Lists downloaded files
- Shows file sizes

**7. Model Verification** (30 seconds)
- Checks model file exists
- Loads and tests model
- Shows performance metrics
- Confirms deployment-ready

---

## Quick Start

### Prerequisites (One-Time Setup)

1. **Install Kaggle CLI**:
   ```bash
   pip install kaggle
   ```

2. **Get API Token**:
   - Visit https://www.kaggle.com/settings/account
   - Click "Create New Token"
   - Download `kaggle.json`

3. **Configure Credentials**:
   ```bash
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

4. **Prepare Dataset**:
   ```bash
   ./prepare_kaggle_dataset.sh
   ```

### Run Training

```bash
./run_kaggle_training.sh
```

Follow the prompts:
1. Press Enter to start
2. Wait for dataset upload
3. Choose manual or CLI monitoring
4. Wait for training to complete
5. Model auto-downloads when done

---

## Script Output Example

```
╔════════════════════════════════════════════════════════╗
║ STEP 1: Checking Prerequisites
╚════════════════════════════════════════════════════════╝

▶ Checking Kaggle CLI...
✓ Kaggle CLI installed
▶ Checking Kaggle credentials...
✓ Kaggle credentials found
▶ Checking dataset...
✓ Dataset prepared (504K)
▶ Checking notebook...
✓ Notebook ready

╔════════════════════════════════════════════════════════╗
║ STEP 2: Uploading Dataset to Kaggle
╚════════════════════════════════════════════════════════╝

▶ Checking if dataset exists...
ℹ Creating new dataset...
✓ Dataset created
▶ Getting dataset info...
✓ Dataset available at: https://www.kaggle.com/datasets/khiwnitithadachot/battery-rul-parquet

╔════════════════════════════════════════════════════════╗
║ STEP 3: Configuring Notebook Metadata
╚════════════════════════════════════════════════════════╝

▶ Updating dataset reference...
✓ Metadata updated with dataset: khiwnitithadachot/battery-rul-parquet

╔════════════════════════════════════════════════════════╗
║ STEP 4: Pushing Notebook to Kaggle
╚════════════════════════════════════════════════════════╝

▶ Pushing kernel...
✓ Notebook pushed successfully
ℹ Notebook URL: https://www.kaggle.com/code/khiwnitithadachot/battery-rul-training

╔════════════════════════════════════════════════════════╗
║ STEP 5: Monitoring Training Execution
╚════════════════════════════════════════════════════════╝

ℹ Training in progress...
ℹ Training in progress...
✓ Training completed!

╔════════════════════════════════════════════════════════╗
║ STEP 6: Downloading Trained Model
╚════════════════════════════════════════════════════════╝

▶ Downloading outputs...
✓ Model downloaded to: /teamspace/studios/this_studio/NT/RUL_prediction/kaggle-model
▶ Downloaded files:
  - rul_model.cbm (2.3M)
  - model_metadata.json (1.2K)
  - feature_importance.csv (856B)
  - TRAINING_REPORT.txt (2.1K)
  - rul_distribution.png (45K)
  - feature_correlations.png (52K)
  - prediction_analysis.png (89K)
  - error_distribution.png (67K)
  - feature_importance.png (71K)
  - rul_model_deployment.zip (2.5M)

╔════════════════════════════════════════════════════════╗
║ STEP 7: Verifying Model
╚════════════════════════════════════════════════════════╝

▶ Checking model file...
✓ Model file exists (2.3M)
▶ Checking metadata...
✓ Metadata exists
ℹ Model Performance:
  - Test MAE: 15.67 days
  - Test RMSE: 22.34 days
  - Test R²: 0.9234
  - Features: 16
  - Training samples: 499
▶ Testing model loading...
✓ Model loaded and tested successfully
  Sample prediction: 485.3 days
✓ Model verification complete

╔════════════════════════════════════════════════════════╗
║ COMPLETE! Next Steps
╚════════════════════════════════════════════════════════╝

Your trained model is ready for deployment:

  1. Model location: kaggle-model/rul_model.cbm

  2. Copy to backend:
     cp kaggle-model/rul_model.cbm ml-pipeline/models/
     cp kaggle-model/model_metadata.json ml-pipeline/models/

  3. Test API integration:
     python ml-pipeline/test_model.py

  4. Deploy to Railway:
     git add ml-pipeline/models/
     git commit -m "feat: Add trained RUL model"
     git push

✓ Training pipeline completed successfully!
```

---

## Manual Training (Alternative)

If you prefer manual control:

### 1. Upload Dataset
```bash
cd kaggle-dataset
kaggle datasets create -p .
```

### 2. Update Metadata
Edit `notebooks/kernel-metadata.json`:
```json
"dataset_sources": ["your-username/battery-rul-parquet"]
```

### 3. Push Notebook
```bash
cd notebooks
kaggle kernels push -p .
```

### 4. Run on Kaggle
- Open: https://www.kaggle.com/code/your-username/battery-rul-training
- Enable GPU (P100 or T4)
- Click "Run All"
- Wait 10-30 minutes

### 5. Download Model
```bash
kaggle kernels output your-username/battery-rul-training -p ./kaggle-model
```

---

## Features

### Smart Configuration
- Auto-detects dataset on Kaggle
- Updates metadata automatically
- Validates configuration
- Handles errors gracefully

### Progress Tracking
- Clear step-by-step output
- Color-coded messages
- Progress indicators
- Time estimates

### Robust Execution
- Checks all prerequisites
- Validates each step
- Provides helpful error messages
- Safe to re-run (idempotent)

### Complete Verification
- Tests model loading
- Checks performance metrics
- Validates all output files
- Confirms deployment-ready

---

## Troubleshooting

### Script Fails: "Kaggle CLI not installed"
```bash
pip install kaggle
```

### Script Fails: "Credentials not found"
1. Download `kaggle.json` from https://www.kaggle.com/settings/account
2. Place in `~/.kaggle/kaggle.json`
3. Run: `chmod 600 ~/.kaggle/kaggle.json`

### Script Fails: "Dataset not prepared"
```bash
./prepare_kaggle_dataset.sh
```

### Training Hangs on Kaggle
- Open notebook URL in browser
- Check for errors in cell outputs
- Ensure GPU is enabled
- Check Kaggle quota (30 hours/week)

### Download Fails: "No outputs found"
Wait for training to complete:
```bash
kaggle kernels status your-username/battery-rul-training
```
Should show: `"status": "complete"`

---

## Advanced Options

### Run Without Monitoring
```bash
# Edit script, comment out monitor_execution call
# Or just run steps 1-4 manually
```

### Custom Output Directory
```bash
# Edit script, change OUTPUT_DIR variable
OUTPUT_DIR="$PROJECT_ROOT/my-models"
```

### Use Different Dataset
```bash
# Edit DATASET_NAME variable in script
DATASET_NAME="my-custom-dataset"
```

---

## What You Get

### Model Files
- `rul_model.cbm` (1-5 MB) - CatBoost model
- `rul_model.onnx` - ONNX format (optional)
- `model_metadata.json` - Metrics and configuration
- `feature_importance.csv` - Feature rankings

### Documentation
- `TRAINING_REPORT.txt` - Complete summary
- 5 visualization plots (PNG)

### Deployment Package
- `rul_model_deployment.zip` - Everything bundled

---

## Timeline

| Step | Duration | Activity |
|------|----------|----------|
| Prerequisites | 30 sec | Checks and validation |
| Dataset Upload | 1-2 min | Upload to Kaggle |
| Configuration | 5 sec | Auto-update metadata |
| Notebook Push | 30 sec | Push to Kaggle |
| **Training** | **10-30 min** | **GPU training (automated)** |
| Model Download | 1 min | Download outputs |
| Verification | 30 sec | Test model |
| **Total** | **~15-35 min** | **Complete pipeline** |

---

## Cost

**$0 - Completely FREE!**

Kaggle provides:
- FREE GPU (P100/T4)
- 30 hours/week quota
- 20 GB storage
- Unlimited bandwidth

Compare to AWS P3: **$1.53 saved per run**

---

## Success Criteria

You know it worked when:

✅ All 7 steps complete without errors
✅ Model file exists (1-5 MB)
✅ Test MAE < 30 days
✅ Test R² > 0.85
✅ Sample prediction runs successfully
✅ All output files present

---

## Next Steps After Training

1. **Copy Model to Backend**
   ```bash
   cp kaggle-model/rul_model.cbm ml-pipeline/models/
   cp kaggle-model/model_metadata.json ml-pipeline/models/
   ```

2. **Test Locally**
   ```python
   from catboost import CatBoostRegressor
   model = CatBoostRegressor()
   model.load_model('ml-pipeline/models/rul_model.cbm')
   ```

3. **Deploy to Production**
   ```bash
   git add ml-pipeline/models/
   git commit -m "feat: Add trained RUL model"
   git push
   ```

4. **Monitor Performance**
   - Track prediction accuracy
   - Log model metrics
   - Retrain monthly

---

## Related Documentation

- **Complete Guide**: `notebooks/KAGGLE_COMPLETE_GUIDE.md`
- **Quick Checklist**: `notebooks/KAGGLE_CHECKLIST.md`
- **Visual Overview**: `notebooks/START_HERE_KAGGLE.md`
- **Technical Setup**: `notebooks/KAGGLE_SETUP.md`

---

## Support

### Script Issues
Check the colored output:
- 🟢 Green ✓ = Success
- 🔴 Red ✗ = Error (with explanation)
- 🟡 Yellow ℹ = Information
- 🔵 Blue ▶ = Action in progress

### Kaggle Issues
- Status: `kaggle kernels status your-username/battery-rul-training`
- Logs: Open notebook URL in browser
- Quota: https://www.kaggle.com/settings

### Model Issues
Review training report:
```bash
cat kaggle-model/TRAINING_REPORT.txt
```

---

**Ready to train? Just run:**
```bash
./run_kaggle_training.sh
```

**Total time:** ~15-35 minutes from start to trained model! 🚀
