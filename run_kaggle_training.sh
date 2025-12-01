#!/bin/bash
# run_kaggle_training.sh
# Complete end-to-end Kaggle training automation
# From dataset upload to model download

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/teamspace/studios/this_studio/NT/RUL_prediction"
DATASET_DIR="$PROJECT_ROOT/kaggle-dataset"
NOTEBOOK_DIR="$PROJECT_ROOT/notebooks"
OUTPUT_DIR="$PROJECT_ROOT/kaggle-model"
DATASET_NAME="battery-rul-parquet"
KERNEL_NAME="battery-rul-training"

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_header "STEP 1: Checking Prerequisites"

    # Check kaggle CLI
    print_step "Checking Kaggle CLI..."
    if ! command -v kaggle &> /dev/null; then
        print_error "Kaggle CLI not installed"
        echo "Install with: pip install kaggle"
        exit 1
    fi
    print_success "Kaggle CLI installed"

    # Check credentials
    print_step "Checking Kaggle credentials..."
    if [ ! -f ~/.kaggle/kaggle.json ]; then
        print_error "Kaggle credentials not found"
        echo "Download kaggle.json from https://www.kaggle.com/settings/account"
        echo "Place it in ~/.kaggle/kaggle.json"
        exit 1
    fi
    print_success "Kaggle credentials found"

    # Check dataset directory
    print_step "Checking dataset..."
    if [ ! -d "$DATASET_DIR/$DATASET_NAME" ]; then
        print_error "Dataset not prepared"
        echo "Run: ./prepare_kaggle_dataset.sh"
        exit 1
    fi
    print_success "Dataset prepared ($(du -sh $DATASET_DIR/$DATASET_NAME | cut -f1))"

    # Check notebook
    print_step "Checking notebook..."
    if [ ! -f "$NOTEBOOK_DIR/kaggle_rul_training.ipynb" ]; then
        print_error "Notebook not found"
        exit 1
    fi
    print_success "Notebook ready"
}

# Function to upload or update dataset
upload_dataset() {
    print_header "STEP 2: Uploading Dataset to Kaggle"

    cd "$DATASET_DIR"

    # Check if dataset already exists
    print_step "Checking if dataset exists..."
    DATASET_EXISTS=$(kaggle datasets list --mine | grep -c "$DATASET_NAME" || true)

    if [ "$DATASET_EXISTS" -eq "0" ]; then
        print_info "Creating new dataset..."
        kaggle datasets create -p .
        print_success "Dataset created"
    else
        print_info "Updating existing dataset..."
        kaggle datasets version -p . -m "Updated: $(date '+%Y-%m-%d %H:%M:%S')"
        print_success "Dataset updated"
    fi

    # Get dataset URL
    print_step "Getting dataset info..."
    DATASET_URL=$(kaggle datasets list --mine | grep "$DATASET_NAME" | awk '{print $1}')
    print_success "Dataset available at: https://www.kaggle.com/datasets/$DATASET_URL"

    # Extract username and dataset name
    USERNAME=$(echo $DATASET_URL | cut -d'/' -f1)
    DATASET_SLUG="$USERNAME/$DATASET_NAME"

    cd "$PROJECT_ROOT"
}

# Function to update kernel metadata
update_kernel_metadata() {
    print_header "STEP 3: Configuring Notebook Metadata"

    print_step "Updating dataset reference..."

    # Update kernel-metadata.json with correct dataset
    cat > "$NOTEBOOK_DIR/kernel-metadata.json" << EOF
{
  "id": "$USERNAME/$KERNEL_NAME",
  "title": "Battery RUL Prediction - CatBoost GPU Training",
  "code_file": "kaggle_rul_training.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": false,
  "enable_gpu": true,
  "enable_internet": true,
  "dataset_sources": [
    "$DATASET_SLUG"
  ],
  "keywords": [
    "battery",
    "rul",
    "remaining useful life",
    "catboost",
    "gpu",
    "regression",
    "predictive maintenance",
    "time series",
    "parquet"
  ]
}
EOF

    print_success "Metadata updated with dataset: $DATASET_SLUG"
}

# Function to push notebook
push_notebook() {
    print_header "STEP 4: Pushing Notebook to Kaggle"

    cd "$NOTEBOOK_DIR"

    print_step "Pushing kernel..."
    kaggle kernels push -p .

    print_success "Notebook pushed successfully"

    KERNEL_URL="https://www.kaggle.com/code/$USERNAME/$KERNEL_NAME"
    print_info "Notebook URL: $KERNEL_URL"

    cd "$PROJECT_ROOT"
}

# Function to monitor execution
monitor_execution() {
    print_header "STEP 5: Monitoring Training Execution"

    print_info "You can now:"
    echo ""
    echo "  1. Open notebook in browser:"
    echo "     $KERNEL_URL"
    echo ""
    echo "  2. Enable GPU and click 'Run All'"
    echo ""
    echo "  3. Monitor status via CLI:"
    echo "     kaggle kernels status $USERNAME/$KERNEL_NAME"
    echo ""
    echo "  4. Wait for completion (10-30 minutes)"
    echo ""

    read -p "Press Enter to continue monitoring, or Ctrl+C to exit..."

    print_step "Checking kernel status..."
    while true; do
        STATUS=$(kaggle kernels status "$USERNAME/$KERNEL_NAME" 2>/dev/null | grep '"status"' | cut -d'"' -f4 || echo "unknown")

        case "$STATUS" in
            "complete")
                print_success "Training completed!"
                break
                ;;
            "running")
                print_info "Training in progress..."
                sleep 30
                ;;
            "error")
                print_error "Training failed"
                echo "Check logs at: $KERNEL_URL"
                exit 1
                ;;
            "cancelAcknowledged"|"cancelled")
                print_error "Training was cancelled"
                exit 1
                ;;
            *)
                print_info "Status: $STATUS (waiting...)"
                sleep 30
                ;;
        esac
    done
}

# Function to download model
download_model() {
    print_header "STEP 6: Downloading Trained Model"

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    print_step "Downloading outputs..."
    kaggle kernels output "$USERNAME/$KERNEL_NAME" -p "$OUTPUT_DIR"

    print_success "Model downloaded to: $OUTPUT_DIR"

    # List downloaded files
    print_step "Downloaded files:"
    ls -lh "$OUTPUT_DIR" | tail -n +2 | while read line; do
        filename=$(echo "$line" | awk '{print $9}')
        size=$(echo "$line" | awk '{print $5}')
        echo "  - $filename ($size)"
    done
}

# Function to verify model
verify_model() {
    print_header "STEP 7: Verifying Model"

    print_step "Checking model file..."
    if [ -f "$OUTPUT_DIR/rul_model.cbm" ]; then
        SIZE=$(du -h "$OUTPUT_DIR/rul_model.cbm" | cut -f1)
        print_success "Model file exists ($SIZE)"
    else
        print_error "Model file not found"
        exit 1
    fi

    print_step "Checking metadata..."
    if [ -f "$OUTPUT_DIR/model_metadata.json" ]; then
        print_success "Metadata exists"

        # Show key metrics
        print_info "Model Performance:"
        python3 << EOF
import json
with open("$OUTPUT_DIR/model_metadata.json") as f:
    meta = json.load(f)
    print(f"  - Test MAE: {meta['metrics']['test']['mae']:.2f} days")
    print(f"  - Test RMSE: {meta['metrics']['test']['rmse']:.2f} days")
    print(f"  - Test R²: {meta['metrics']['test']['r2']:.4f}")
    print(f"  - Features: {meta['num_features']}")
    print(f"  - Training samples: {meta['training_samples']:,}")
EOF
    else
        print_error "Metadata not found"
    fi

    print_step "Testing model loading..."
    python3 << 'EOF'
try:
    from catboost import CatBoostRegressor
    import pandas as pd

    model = CatBoostRegressor()
    model.load_model('kaggle-model/rul_model.cbm')

    # Test prediction with dummy data
    sample = pd.DataFrame([{
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
        'v_health_score': 0.85
    }])

    # Get model features
    with open('kaggle-model/model_metadata.json') as f:
        import json
        meta = json.load(f)
        features = meta['features']

    # Reorder columns
    sample = sample[[f for f in features if f in sample.columns]]

    prediction = model.predict(sample)
    print(f"\033[0;32m✓\033[0m Model loaded and tested successfully")
    print(f"  Sample prediction: {prediction[0]:.1f} days")
except Exception as e:
    print(f"\033[0;31m✗\033[0m Model test failed: {e}")
    exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_success "Model verification complete"
    else
        print_error "Model verification failed"
        exit 1
    fi
}

# Function to show next steps
show_next_steps() {
    print_header "COMPLETE! Next Steps"

    echo "Your trained model is ready for deployment:"
    echo ""
    echo "  1. Model location: $OUTPUT_DIR/rul_model.cbm"
    echo ""
    echo "  2. Copy to backend:"
    echo "     cp $OUTPUT_DIR/rul_model.cbm ml-pipeline/models/"
    echo "     cp $OUTPUT_DIR/model_metadata.json ml-pipeline/models/"
    echo ""
    echo "  3. Test API integration:"
    echo "     python ml-pipeline/test_model.py"
    echo ""
    echo "  4. Deploy to Railway:"
    echo "     git add ml-pipeline/models/"
    echo "     git commit -m \"feat: Add trained RUL model\""
    echo "     git push"
    echo ""
    echo "  5. Review training report:"
    echo "     cat $OUTPUT_DIR/TRAINING_REPORT.txt"
    echo ""

    print_success "Training pipeline completed successfully!"
}

# Main execution
main() {
    clear
    print_header "KAGGLE END-TO-END TRAINING AUTOMATION"

    echo "This script will:"
    echo "  1. Check prerequisites"
    echo "  2. Upload/update dataset"
    echo "  3. Configure notebook"
    echo "  4. Push to Kaggle"
    echo "  5. Monitor training"
    echo "  6. Download model"
    echo "  7. Verify model"
    echo ""

    read -p "Press Enter to continue or Ctrl+C to cancel..."

    check_prerequisites
    upload_dataset
    update_kernel_metadata
    push_notebook

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo ""
    print_info "Notebook is now on Kaggle. You have two options:"
    echo ""
    echo "  A. Run manually on Kaggle website (recommended for first time)"
    echo "     - Open: $KERNEL_URL"
    echo "     - Enable GPU (P100 or T4)"
    echo "     - Click 'Run All'"
    echo "     - Wait 10-30 minutes"
    echo ""
    echo "  B. Monitor from command line (experimental)"
    echo "     - Script will check status every 30 seconds"
    echo "     - You still need to click 'Run All' on website first"
    echo ""

    read -p "Do you want to monitor from CLI? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        monitor_execution
        download_model
        verify_model
        show_next_steps
    else
        echo ""
        print_info "To download model after training completes, run:"
        echo "  kaggle kernels output $USERNAME/$KERNEL_NAME -p $OUTPUT_DIR"
        echo ""
        print_success "Setup complete! Open Kaggle and start training."
    fi
}

# Run main function
main
