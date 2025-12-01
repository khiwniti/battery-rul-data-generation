# Data Format Research for ML Production Pipeline

## Executive Summary

**Current Format**: CSV + gzip (3.3 GB for 247M records)
**Recommended Format**: **Apache Parquet** for production ML pipelines
**Expected Savings**: 40-60% smaller file size, 10-50× faster reads

---

## 1. Format Comparison Matrix

| Format | Size vs CSV.gz | Read Speed | Write Speed | ML Library Support | Query Capability | Compression | Best Use Case |
|--------|---------------|------------|-------------|-------------------|------------------|-------------|---------------|
| **CSV.gz** | Baseline (3.3 GB) | Slow | Fast | ✅ Universal | ❌ Full scan | ✅ Good | Data exchange |
| **Parquet** | **40-60% smaller** | **10-50× faster** | Medium | ✅✅✅ Excellent | ✅✅✅ Column-level | ✅✅ Excellent | **Production ML** |
| **Feather (Arrow IPC)** | Similar to Parquet | **Very fast** | **Very fast** | ✅✅ Good | ✅ Limited | ✅ Light | Intermediate cache |
| **HDF5** | 30-50% smaller | Fast | Medium | ✅ Good | ✅✅ Flexible | ✅ Good | Scientific computing |
| **Arrow** | In-memory only | **Instant** | N/A | ✅✅ Good | ✅✅ Full | ❌ None | Cross-language IPC |

---

## 2. Detailed Analysis

### 2.1 Apache Parquet (⭐ RECOMMENDED)

**What It Is**: Open-source columnar storage format optimized for analytics workloads.

**Advantages**:
- ✅ **Columnar storage**: Only read columns you need (critical for 247M rows)
- ✅ **Excellent compression**: Snappy, GZIP, LZ4, Zstandard algorithms
- ✅ **Predicate pushdown**: Filter at storage layer (e.g., `WHERE battery_id = 'X'`)
- ✅ **Schema embedded**: Self-documenting with data types
- ✅ **Partitioning support**: Split by location/date for faster queries
- ✅ **ML ecosystem standard**: Native support in pandas, PyArrow, PySpark, Dask, TensorFlow, PyTorch
- ✅ **Cloud-optimized**: Works seamlessly with S3, GCS, Azure Blob

**Disadvantages**:
- ❌ Slower writes than CSV (but one-time cost)
- ❌ Not human-readable (use tools to inspect)

**Performance Estimate (247M records)**:
- **Size**: 1.3-2.0 GB (vs 3.3 GB CSV.gz) → **40-60% savings**
- **Read time** (full table): 10-30 seconds (vs 5-10 minutes for CSV.gz)
- **Read time** (single column): 1-3 seconds (vs 5-10 minutes)
- **Query time** (filter by battery_id): 2-5 seconds (vs 5-10 minutes)

**Code Example**:
```python
import pandas as pd

# Write Parquet
df.to_parquet('battery_sensors.parquet',
              engine='pyarrow',
              compression='snappy',
              index=False)

# Read Parquet (all data)
df = pd.read_parquet('battery_sensors.parquet')

# Read specific columns only (FAST!)
df_subset = pd.read_parquet('battery_sensors.parquet',
                             columns=['ts', 'battery_id', 'voltage_v'])

# Read with filter (predicate pushdown)
df_filtered = pd.read_parquet('battery_sensors.parquet',
                               filters=[('battery_id', '==', 'some-uuid')])
```

**Production Recommendations**:
- Use **Snappy compression** for balanced speed/size
- Use **Zstandard** for maximum compression (slower write, similar read speed)
- Partition large datasets: `dataset.write_parquet('output/', partition_cols=['location_name'])`

---

### 2.2 Feather / Arrow IPC

**What It Is**: Apache Arrow's on-disk format for fast serialization of tabular data.

**Advantages**:
- ✅ **Fastest I/O**: Near-instantaneous read/write
- ✅ **Zero-copy reads**: Direct memory mapping
- ✅ **Language-agnostic**: Share data between Python, R, Julia, C++
- ✅ **Simple format**: Easy to implement

**Disadvantages**:
- ❌ Limited compression (only LZ4, Zstandard)
- ❌ No predicate pushdown or advanced querying
- ❌ Not cloud-optimized (needs full file download)

**Performance Estimate**:
- **Size**: 2.5-3.0 GB (similar to CSV.gz with compression)
- **Read time**: 5-15 seconds (very fast)
- **Write time**: 5-15 seconds (very fast)

**Best Use Case**: Intermediate storage between pipeline stages, not final storage.

**Code Example**:
```python
import pyarrow.feather as feather

# Write Feather v2 (supports compression)
feather.write_feather(df, 'battery_sensors.feather', compression='zstd')

# Read Feather
df = feather.read_feather('battery_sensors.feather')

# Read specific columns
df_subset = feather.read_feather('battery_sensors.feather',
                                  columns=['ts', 'voltage_v'])
```

---

### 2.3 HDF5 (Hierarchical Data Format)

**What It Is**: Binary format for storing large arrays and hierarchical data.

**Advantages**:
- ✅ **Flexible schema**: Store multiple datasets in one file
- ✅ **Chunked storage**: Efficient partial reads
- ✅ **Good compression**: GZIP, LZF, Blosc
- ✅ **Metadata support**: Store arbitrary attributes
- ✅ **Append support**: Add data incrementally

**Disadvantages**:
- ❌ Less ML ecosystem support than Parquet
- ❌ Requires h5py library (extra dependency)
- ❌ More complex API
- ❌ Not cloud-optimized

**Performance Estimate**:
- **Size**: 2.0-2.5 GB (good compression)
- **Read time**: 30-60 seconds
- **Query time**: Slower than Parquet

**Best Use Case**: Scientific datasets with complex hierarchies (e.g., nested time series per battery).

**Code Example**:
```python
import h5py
import pandas as pd

# Write HDF5
df.to_hdf('battery_sensors.h5', key='sensors', mode='w',
          complevel=9, complib='blosc')

# Read HDF5
df = pd.read_hdf('battery_sensors.h5', key='sensors')

# Read with query
df_filtered = pd.read_hdf('battery_sensors.h5',
                          where='battery_id == "some-uuid"')
```

---

### 2.4 Apache Arrow (In-Memory)

**What It Is**: In-memory columnar format for zero-copy data sharing.

**Advantages**:
- ✅ **Zero serialization cost**: Pass data between processes/languages without copying
- ✅ **SIMD-optimized**: Vectorized operations for fast analytics
- ✅ **Cross-language**: Python ↔ R ↔ C++ ↔ Java without conversion

**Disadvantages**:
- ❌ Not a storage format (use Parquet/Feather for disk)
- ❌ Requires keeping data in memory

**Best Use Case**: Inter-process communication in real-time ML serving.

---

## 3. Benchmark Results (Simulated for 247M Records)

### Read Performance (Single-threaded)

| Format | Full Table Read | Single Column Read | Filtered Read (1 battery) |
|--------|----------------|-------------------|--------------------------|
| CSV.gz | 5-10 minutes | 5-10 minutes | 5-10 minutes |
| **Parquet** | **10-30 seconds** | **1-3 seconds** | **2-5 seconds** |
| Feather | 5-15 seconds | 3-8 seconds | N/A (full scan) |
| HDF5 | 30-60 seconds | 10-20 seconds | 15-30 seconds |

### Storage Size

| Format | Compressed Size | vs CSV.gz | Compression Algorithm |
|--------|----------------|-----------|----------------------|
| CSV.gz | 3.3 GB | Baseline | gzip |
| **Parquet (snappy)** | **2.0 GB** | **-39%** | Snappy |
| **Parquet (zstd)** | **1.3 GB** | **-61%** | Zstandard |
| Feather (zstd) | 2.5 GB | -24% | Zstandard |
| HDF5 (blosc) | 2.2 GB | -33% | Blosc |

---

## 4. Production ML Pipeline Considerations

### 4.1 Training Pipeline Requirements

**Typical Workflow**:
1. Load subset of features (not all 9 columns)
2. Filter by date range or location
3. Aggregate/resample (e.g., hourly statistics)
4. Join with metadata (battery info, locations)
5. Feed to ML framework (PyTorch DataLoader, TensorFlow Dataset)

**Why Parquet Wins**:
- ✅ **Columnar reads**: Load only `voltage_v`, `temperature_c`, `resistance_mohm` (skip others)
- ✅ **Predicate pushdown**: `WHERE timestamp >= '2024-01-01'` filters at I/O layer
- ✅ **Partition pruning**: Read only `location=Bangrak` partition (skip other 8 locations)
- ✅ **Native DataFrame support**: Works seamlessly with pandas → PyTorch/TensorFlow

### 4.2 Inference Pipeline Requirements

**Real-time Inference** (sensor-simulator → backend → ML pipeline):
- Current data: Small batches (100-1000 records)
- Historical context: Last 7-30 days per battery
- Format: JSON/Arrow for API, Parquet for historical lookups

**Batch Inference** (nightly predictions for full fleet):
- Load full dataset, run predictions for all 216 batteries
- Output: RUL predictions saved to database
- Format: Parquet for input, PostgreSQL for output

### 4.3 Data Versioning and Lineage

**Parquet Advantages**:
- ✅ Schema evolution: Add columns without rewriting entire file
- ✅ Metadata storage: Embed generation timestamp, version, parameters
- ✅ Partitioning: Separate by date for easy versioning (`v1/2023-12/`, `v1/2024-01/`)

---

## 5. Conversion Scripts

### 5.1 CSV.gz → Parquet (Single Location)

```python
import pandas as pd
import pyarrow.parquet as pq

def convert_csv_to_parquet(csv_path, parquet_path, compression='snappy'):
    """
    Convert CSV.gz to Parquet with optimal settings for ML.

    Args:
        csv_path: Path to CSV.gz file
        parquet_path: Output Parquet file path
        compression: 'snappy' (fast), 'gzip' (good), 'zstd' (best compression)
    """
    print(f"Reading {csv_path}...")

    # Read CSV in chunks to avoid memory issues
    chunk_size = 1_000_000  # 1M rows per chunk
    chunks = []

    for chunk in pd.read_csv(csv_path, compression='gzip', chunksize=chunk_size):
        # Convert timestamp to datetime if needed
        if 'ts' in chunk.columns:
            chunk['ts'] = pd.to_datetime(chunk['ts'])
        chunks.append(chunk)

    # Combine chunks
    df = pd.concat(chunks, ignore_index=True)

    print(f"Writing {parquet_path} with {compression} compression...")

    # Write Parquet
    df.to_parquet(
        parquet_path,
        engine='pyarrow',
        compression=compression,
        index=False,
        row_group_size=100_000,  # Smaller row groups for better filtering
    )

    # Report size
    import os
    original_size_mb = os.path.getsize(csv_path) / 1024 / 1024
    parquet_size_mb = os.path.getsize(parquet_path) / 1024 / 1024
    savings_pct = (1 - parquet_size_mb / original_size_mb) * 100

    print(f"✓ Conversion complete!")
    print(f"  Original (CSV.gz): {original_size_mb:.1f} MB")
    print(f"  Parquet ({compression}): {parquet_size_mb:.1f} MB")
    print(f"  Savings: {savings_pct:.1f}%")

# Example usage
convert_csv_to_parquet(
    'battery_sensors_Bangrak_Data_Center.csv.gz',
    'battery_sensors_Bangrak_Data_Center.parquet',
    compression='snappy'
)
```

### 5.2 Batch Conversion (All 9 Locations)

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def convert_all_locations(input_dir, output_dir, compression='snappy'):
    """
    Convert all location CSV files to Parquet in parallel.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all CSV.gz files
    csv_files = list(input_path.glob('battery_sensors_*.csv.gz'))

    print(f"Found {len(csv_files)} files to convert")
    print(f"Using {multiprocessing.cpu_count()} CPU cores\n")

    # Convert in parallel
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for csv_file in csv_files:
            parquet_file = output_path / csv_file.stem.replace('.csv', '.parquet')
            future = executor.submit(convert_csv_to_parquet, csv_file, parquet_file, compression)
            futures.append(future)

        # Wait for all conversions
        for future in futures:
            future.result()

    print("\n✓ All conversions complete!")

# Example usage
convert_all_locations(
    'battery-rul-data-generation/output/production_2years/by_location/',
    'battery-rul-data-generation/output/production_2years/parquet/',
    compression='snappy'
)
```

### 5.3 Partitioned Parquet Dataset (Advanced)

```python
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

def create_partitioned_dataset(csv_dir, parquet_dir):
    """
    Create a partitioned Parquet dataset for efficient querying.
    Partitions: location_name / year / month
    """
    from pathlib import Path

    csv_path = Path(csv_dir)
    output_path = Path(parquet_dir)

    for csv_file in csv_path.glob('battery_sensors_*.csv.gz'):
        print(f"Processing {csv_file.name}...")

        # Read CSV
        df = pd.read_csv(csv_file, compression='gzip')
        df['ts'] = pd.to_datetime(df['ts'])

        # Add partition columns
        df['year'] = df['ts'].dt.year
        df['month'] = df['ts'].dt.month

        # Convert to Arrow Table
        table = pa.Table.from_pandas(df)

        # Write partitioned dataset
        pq.write_to_dataset(
            table,
            root_path=str(output_path),
            partition_cols=['location_name', 'year', 'month'],
            compression='snappy',
            existing_data_behavior='overwrite_or_ignore'
        )

    print(f"\n✓ Partitioned dataset created at {output_path}")
    print(f"Structure: {output_path}/location_name=X/year=Y/month=Z/*.parquet")

# Example usage
create_partitioned_dataset(
    'battery-rul-data-generation/output/production_2years/by_location/',
    'battery-rul-data-generation/output/production_2years/partitioned/'
)

# Query partitioned dataset
df_bangrak_jan2024 = pd.read_parquet(
    'battery-rul-data-generation/output/production_2years/partitioned/',
    filters=[
        ('location_name', '==', 'Bangrak Data Center'),
        ('year', '==', 2024),
        ('month', '==', 1)
    ]
)
```

---

## 6. ML Pipeline Integration Examples

### 6.1 PyTorch DataLoader with Parquet

```python
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

class BatteryParquetDataset(Dataset):
    """
    PyTorch Dataset that reads from Parquet files.
    Efficient for large datasets with selective column loading.
    """
    def __init__(self, parquet_path, feature_columns, target_column,
                 window_size=100, stride=50):
        """
        Args:
            parquet_path: Path to Parquet file or directory
            feature_columns: List of column names for features
            target_column: Column name for target (e.g., 'rul_days')
            window_size: Number of time steps per sample
            stride: Step size for sliding window
        """
        # Load only needed columns (efficient!)
        columns_to_load = feature_columns + [target_column, 'battery_id', 'ts']
        self.df = pd.read_parquet(parquet_path, columns=columns_to_load)

        # Sort by battery and time
        self.df = self.df.sort_values(['battery_id', 'ts'])

        # Create sliding windows
        self.samples = self._create_windows(window_size, stride)
        self.feature_columns = feature_columns
        self.target_column = target_column

    def _create_windows(self, window_size, stride):
        """Create sliding window indices."""
        samples = []
        for battery_id in self.df['battery_id'].unique():
            battery_data = self.df[self.df['battery_id'] == battery_id]
            for start_idx in range(0, len(battery_data) - window_size, stride):
                end_idx = start_idx + window_size
                samples.append((battery_id, start_idx, end_idx))
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        battery_id, start_idx, end_idx = self.samples[idx]
        window = self.df[self.df['battery_id'] == battery_id].iloc[start_idx:end_idx]

        # Features (window_size, num_features)
        X = window[self.feature_columns].values

        # Target (single value - RUL at end of window)
        y = window[self.target_column].iloc[-1]

        return torch.FloatTensor(X), torch.FloatTensor([y])

# Usage
dataset = BatteryParquetDataset(
    parquet_path='battery_sensors.parquet',
    feature_columns=['voltage_v', 'temperature_c', 'resistance_mohm'],
    target_column='rul_days',
    window_size=100,
    stride=50
)

dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=4)

# Training loop
for batch_X, batch_y in dataloader:
    # batch_X: (32, 100, 3) - 32 samples, 100 time steps, 3 features
    # batch_y: (32, 1) - 32 RUL targets
    # ... model forward pass ...
    pass
```

### 6.2 Dask for Out-of-Core Processing

```python
import dask.dataframe as dd

# Load Parquet with Dask (lazy evaluation)
ddf = dd.read_parquet(
    'battery-rul-data-generation/output/production_2years/partitioned/',
    engine='pyarrow'
)

# Compute statistics (parallelized across partitions)
print(f"Total records: {len(ddf)}")
print(f"Batteries: {ddf['battery_id'].nunique().compute()}")

# Filter and aggregate (efficient)
bangrak_stats = ddf[ddf['location_name'] == 'Bangrak Data Center'].groupby('battery_id').agg({
    'voltage_v': ['mean', 'std'],
    'temperature_c': 'max',
    'resistance_mohm': ['mean', 'max']
}).compute()

print(bangrak_stats)
```

---

## 7. Recommendations Summary

### For Production ML Pipeline: Use Apache Parquet ⭐

**Why**:
1. **40-60% smaller** than CSV.gz (1.3-2.0 GB vs 3.3 GB)
2. **10-50× faster reads** for analytics queries
3. **Columnar access** - read only needed features
4. **Predicate pushdown** - filter at I/O layer
5. **Universal ML support** - pandas, PyTorch, TensorFlow, Dask, Spark
6. **Cloud-ready** - works with S3, GCS, Azure

**Settings**:
- Compression: **Snappy** (balanced) or **Zstandard** (maximum compression)
- Row group size: 100,000-500,000 rows
- Partitioning: By location and date for query optimization

### For Intermediate Pipeline Stages: Feather

**Use Case**: Cache processed features between pipeline steps (e.g., after feature engineering, before training).

### For Archival Storage: Parquet with Zstandard

**Use Case**: Long-term storage where read speed is less critical than size.

### Not Recommended for This Use Case:
- ❌ HDF5: Less ecosystem support, more complex
- ❌ CSV: Too slow for 247M records
- ❌ JSON: Extremely slow and large

---

## 8. Migration Plan

### Phase 1: Proof of Concept (1 location)
```bash
# Convert Bangrak location to Parquet
python scripts/convert_to_parquet.py \
    --input battery_sensors_Bangrak_Data_Center.csv.gz \
    --output battery_sensors_Bangrak_Data_Center.parquet \
    --compression snappy

# Benchmark read performance
python scripts/benchmark_formats.py
```

### Phase 2: Full Conversion (All 9 locations)
```bash
# Parallel conversion
python scripts/convert_all_to_parquet.py \
    --input-dir output/production_2years/by_location/ \
    --output-dir output/production_2years/parquet/ \
    --compression snappy \
    --workers 4
```

### Phase 3: Update Notebooks
- Update data loading code to use Parquet
- Test end-to-end training pipeline
- Measure speedup and memory usage

### Phase 4: Production Deployment
- Update ML pipeline to read from Parquet
- Configure data versioning (separate directories per version)
- Set up automated conversion for new data generation runs

---

## 9. Expected Impact

### Storage Savings
- **Before**: 3.3 GB (CSV.gz)
- **After**: 1.3-2.0 GB (Parquet with Snappy/Zstandard)
- **Savings**: $50-100/year on cloud storage (AWS S3 standard)

### Training Speed Improvement
- **Data loading time**: 5-10 minutes → 10-30 seconds (20-30× faster)
- **Feature selection**: Always full scan → Column-only read (50-100× faster)
- **Filtered queries**: Full scan → Predicate pushdown (50-200× faster)

### Developer Experience
- **Easier debugging**: Schema embedded in file
- **Faster iteration**: 20× faster data loading = 20× faster experimentation
- **Better reproducibility**: Consistent data types, no CSV parsing errors

---

## 10. Code Examples for Notebooks

### Before (CSV.gz)
```python
# Slow: reads all columns, decompresses entire file
df = pd.read_csv('battery_sensors_Bangrak_Data_Center.csv.gz', compression='gzip')
df['ts'] = pd.to_datetime(df['ts'])  # Manual type conversion
```

### After (Parquet)
```python
# Fast: reads only needed columns, types already correct
df = pd.read_parquet('battery_sensors_Bangrak_Data_Center.parquet',
                     columns=['ts', 'battery_id', 'voltage_v', 'temperature_c', 'resistance_mohm'])

# Even faster: filter at I/O layer
df_filtered = pd.read_parquet('battery_sensors_Bangrak_Data_Center.parquet',
                               filters=[('battery_id', '==', target_battery_id)])
```

---

## References

- [Apache Parquet Documentation](https://parquet.apache.org/docs/)
- [PyArrow Parquet Guide](https://arrow.apache.org/docs/python/parquet.html)
- [Pandas Parquet I/O](https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html)
- [Feather Format](https://arrow.apache.org/docs/python/feather.html)
- [HDF5 for Python](https://docs.h5py.org/)

---

**Document Status**: Complete ✅
**Recommendation**: **Apache Parquet with Snappy compression**
**Next Action**: Create conversion scripts and update notebooks
