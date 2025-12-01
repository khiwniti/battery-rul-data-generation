"""
Parquet Service
Utilities for reading and writing Parquet files for battery telemetry data
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from ..core.logging import logger


class ParquetService:
    """Service for managing Parquet-based data storage"""

    def __init__(self, base_path: str = "data/parquet"):
        """
        Initialize Parquet service

        Args:
            base_path: Base directory for Parquet files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def write_telemetry(
        self,
        df: pd.DataFrame,
        partition_cols: Optional[List[str]] = None,
        compression: str = "snappy"
    ) -> Path:
        """
        Write telemetry data to Parquet format

        Args:
            df: DataFrame with telemetry data
            partition_cols: Columns to partition by (e.g., ['year', 'month'])
            compression: Compression algorithm (snappy, gzip, brotli)

        Returns:
            Path to written Parquet file/directory
        """
        output_path = self.base_path / "telemetry"
        output_path.mkdir(parents=True, exist_ok=True)

        if partition_cols:
            # Partitioned write (for large datasets)
            pq.write_to_dataset(
                pa.Table.from_pandas(df),
                root_path=str(output_path),
                partition_cols=partition_cols,
                compression=compression,
                existing_data_behavior='overwrite_or_ignore'
            )
            logger.info(
                "Wrote partitioned telemetry",
                path=str(output_path),
                partitions=partition_cols,
                rows=len(df)
            )
        else:
            # Single file write
            filename = f"telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            file_path = output_path / filename
            df.to_parquet(file_path, compression=compression, index=False)
            logger.info(
                "Wrote telemetry file",
                path=str(file_path),
                rows=len(df)
            )
            return file_path

        return output_path

    def read_telemetry(
        self,
        battery_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read telemetry data from Parquet files

        Args:
            battery_id: Filter by specific battery
            start_date: Filter records after this date
            end_date: Filter records before this date
            columns: Specific columns to read (for efficiency)

        Returns:
            DataFrame with filtered telemetry data
        """
        telemetry_path = self.base_path / "telemetry"

        if not telemetry_path.exists():
            logger.warning("Telemetry path not found", path=str(telemetry_path))
            return pd.DataFrame()

        # Build filters for efficient reading
        filters = []
        if battery_id:
            filters.append(('battery_id', '=', battery_id))
        if start_date:
            filters.append(('timestamp', '>=', start_date))
        if end_date:
            filters.append(('timestamp', '<=', end_date))

        try:
            # Read parquet with filters (pushdown optimization)
            if telemetry_path.is_dir():
                # Read partitioned dataset
                dataset = pq.ParquetDataset(telemetry_path, filters=filters if filters else None)
                df = dataset.read(columns=columns).to_pandas()
            else:
                # Read single file
                df = pd.read_parquet(telemetry_path, columns=columns, filters=filters if filters else None)

            logger.info(
                "Read telemetry data",
                rows=len(df),
                battery_id=battery_id,
                start_date=start_date,
                end_date=end_date
            )
            return df

        except Exception as e:
            logger.error("Error reading telemetry", error=str(e), exc_info=True)
            return pd.DataFrame()

    def write_feature_store(self, df: pd.DataFrame, name: str = "feature_store") -> Path:
        """
        Write ML feature store to Parquet

        Args:
            df: DataFrame with ML features
            name: Feature store name

        Returns:
            Path to written file
        """
        output_path = self.base_path / "features"
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{name}.parquet"
        df.to_parquet(file_path, compression="snappy", index=False)

        logger.info(
            "Wrote feature store",
            path=str(file_path),
            rows=len(df),
            columns=list(df.columns)
        )
        return file_path

    def read_feature_store(self, name: str = "feature_store") -> pd.DataFrame:
        """
        Read ML feature store from Parquet

        Args:
            name: Feature store name

        Returns:
            DataFrame with ML features
        """
        file_path = self.base_path / "features" / f"{name}.parquet"

        if not file_path.exists():
            logger.warning("Feature store not found", path=str(file_path))
            return pd.DataFrame()

        df = pd.read_parquet(file_path)
        logger.info("Read feature store", path=str(file_path), rows=len(df))
        return df

    def write_training_data(
        self,
        telemetry_df: pd.DataFrame,
        features_df: pd.DataFrame,
        labels_df: pd.DataFrame,
        name: str = "training_dataset"
    ) -> Dict[str, Path]:
        """
        Write complete training dataset (telemetry, features, labels)

        Args:
            telemetry_df: Raw telemetry data
            features_df: Engineered features
            labels_df: Target labels (SOH, RUL, etc.)
            name: Dataset name

        Returns:
            Dictionary mapping data type to file paths
        """
        output_path = self.base_path / "training" / name
        output_path.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Write telemetry
        telemetry_path = output_path / "telemetry.parquet"
        telemetry_df.to_parquet(telemetry_path, compression="snappy", index=False)
        paths['telemetry'] = telemetry_path

        # Write features
        features_path = output_path / "features.parquet"
        features_df.to_parquet(features_path, compression="snappy", index=False)
        paths['features'] = features_path

        # Write labels
        labels_path = output_path / "labels.parquet"
        labels_df.to_parquet(labels_path, compression="snappy", index=False)
        paths['labels'] = labels_path

        logger.info(
            "Wrote training dataset",
            name=name,
            telemetry_rows=len(telemetry_df),
            features_rows=len(features_df),
            labels_rows=len(labels_df)
        )

        return paths

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for Parquet files

        Returns:
            Dictionary with storage metrics
        """
        stats = {
            'base_path': str(self.base_path),
            'total_size_mb': 0,
            'file_count': 0,
            'datasets': {}
        }

        if not self.base_path.exists():
            return stats

        for path in self.base_path.rglob('*.parquet'):
            size_mb = path.stat().st_size / (1024 * 1024)
            stats['total_size_mb'] += size_mb
            stats['file_count'] += 1

            # Categorize by dataset type
            dataset_type = path.parent.name
            if dataset_type not in stats['datasets']:
                stats['datasets'][dataset_type] = {
                    'size_mb': 0,
                    'file_count': 0
                }
            stats['datasets'][dataset_type]['size_mb'] += size_mb
            stats['datasets'][dataset_type]['file_count'] += 1

        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        for dataset in stats['datasets'].values():
            dataset['size_mb'] = round(dataset['size_mb'], 2)

        return stats


# Global instance
parquet_service = ParquetService()
