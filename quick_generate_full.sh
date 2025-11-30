#!/bin/bash
# Quick script to generate data for all 9 locations sequentially

echo "================================================================================"
echo "GENERATING FULL DATASET - 9 LOCATIONS × 24 BATTERIES × 730 DAYS"
echo "================================================================================"
echo

# Create output directory
mkdir -p ./output/full_dataset_combined

# Generate for each location (using existing working script)
# This is simpler and more reliable than creating a new complex script

for i in {1..9}; do
    offset=$((($i - 1) * 24))
    
    echo "Location $i/9: Generating batteries $offset to $(($offset + 23))..."
    
    python3 generate_sensor_data.py \
        --days 730 \
        --batteries 24 \
        --sampling-seconds 60 \
        --output-dir "./output/full_dataset_combined/location_$i" \
        --seed $((42 + $i))
    
    if [ $? -eq 0 ]; then
        echo "✓ Location $i complete"
    else
        echo "✗ Location $i failed!"
        exit 1
    fi
    echo
done

echo "================================================================================"
echo "✓ ALL 9 LOCATIONS GENERATED"
echo "================================================================================"
echo
echo "Next: Combine all locations into single dataset"
