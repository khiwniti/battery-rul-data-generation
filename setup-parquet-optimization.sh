#!/bin/bash
# Quick Data Optimization Setup
# Run this script to convert your training data to Parquet format

set -e

echo "============================================"
echo "Battery RUL Data Optimization Setup"
echo "============================================"
echo ""

# Check if data directory exists
DATA_DIR="battery-rul-data-generation/output/production_2years/by_location"

if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Error: Data directory not found: $DATA_DIR"
    echo ""
    echo "Please generate training data first using:"
    echo "  cd battery-rul-data-generation"
    echo "  python generate_full_dataset.py --days 730"
    exit 1
fi

# Count CSV files
CSV_COUNT=$(ls -1 "$DATA_DIR"/*.csv.gz 2>/dev/null | wc -l)

if [ "$CSV_COUNT" -eq 0 ]; then
    echo "❌ Error: No CSV.gz files found in $DATA_DIR"
    exit 1
fi

echo "✅ Found $CSV_COUNT CSV.gz files to convert"
echo ""

# Check if pyarrow is installed
python3 -c "import pyarrow" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required dependencies (pyarrow)..."
    pip install pyarrow
    echo ""
fi

# Create output directory
OUTPUT_DIR="battery-rul-data-generation/output/production_2years/parquet"
mkdir -p "$OUTPUT_DIR"

echo "🚀 Starting conversion to Parquet format..."
echo "   Input:  $DATA_DIR"
echo "   Output: $OUTPUT_DIR"
echo "   Workers: 4 (parallel processing)"
echo "   Compression: Snappy (recommended for ML)"
echo ""

# Run conversion
python3 battery-rul-data-generation/scripts/convert_all_to_parquet.py \
    --input-dir "$DATA_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --workers 4 \
    --compression snappy

echo ""
echo "============================================"
echo "✅ Conversion Complete!"
echo "============================================"
echo ""
echo "📊 Next Steps:"
echo ""
echo "1. Update notebooks to use Parquet:"
echo "   - Open: battery-rul-data-generation/notebooks/Battery_RUL_Training.ipynb"
echo "   - Set: USE_PARQUET = True"
echo "   - Run all cells"
echo ""
echo "2. Verify storage savings:"
echo "   du -sh $DATA_DIR"
echo "   du -sh $OUTPUT_DIR"
echo ""
echo "3. Start training:"
echo "   cd battery-rul-data-generation/notebooks"
echo "   jupyter notebook"
echo ""
echo "📚 Documentation:"
echo "   - Format research: DATA_FORMAT_RESEARCH.md"
echo "   - Notebook updates: battery-rul-data-generation/notebooks/NOTEBOOK_UPDATES.md"
echo "   - Complete summary: DATA_OPTIMIZATION_COMPLETE.md"
echo ""
