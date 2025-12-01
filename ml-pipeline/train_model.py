"""
Train RUL Prediction Model
Script to train CatBoost model on generated battery data
"""
import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from src.core.config import settings
from src.ml.feature_engineering import FeatureEngineer
from src.ml.model_training import RULModelTrainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_training_data(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    """
    Load training data from generated dataset

    Args:
        data_dir: Directory containing generated data

    Returns:
        Tuple of (telemetry_df, battery_states)
    """
    logger.info(f"Loading training data from {data_dir}")

    # Load telemetry data from by_location directory
    location_dir = data_dir / "by_location"
    if not location_dir.exists():
        raise FileNotFoundError(f"Location directory not found: {location_dir}")

    # Load all battery sensor files
    battery_files = list(location_dir.glob("battery_sensors_*.csv.gz"))
    if not battery_files:
        raise FileNotFoundError(f"No battery sensor files found in {location_dir}")

    logger.info(f"Found {len(battery_files)} battery sensor files")

    # Load and concatenate all telemetry data
    telemetry_dfs = []
    for file_path in battery_files:
        logger.info(f"Loading {file_path.name}")
        df = pd.read_csv(file_path)
        telemetry_dfs.append(df)

    telemetry_df = pd.concat(telemetry_dfs, ignore_index=True)
    logger.info(f"Loaded {len(telemetry_df)} telemetry records")

    # Load battery states (ground truth)
    # For the test dataset, we need to create synthetic RUL labels
    # based on SOH degradation trends
    logger.info("Creating synthetic RUL labels from telemetry data")

    # Group by battery and get latest SOH for each
    battery_states = {}

    if 'soh_pct' in telemetry_df.columns:
        for battery_id in telemetry_df['battery_id'].unique():
            battery_data = telemetry_df[telemetry_df['battery_id'] == battery_id]
            latest_soh = battery_data['soh_pct'].iloc[-1]

            # Calculate RUL based on SOH
            # Assuming healthy battery lasts 1825 days (5 years)
            # RUL = (current_SOH - 80) / (100 - 80) * 1825
            if latest_soh >= 80:
                rul_days = (latest_soh - 80) / 20 * 1825
            else:
                rul_days = 0

            battery_states[battery_id] = {
                'soh_pct': float(latest_soh),
                'rul_days': float(rul_days),
            }
    else:
        # If no SOH data, create dummy states
        logger.warning("No SOH data found, creating dummy battery states")
        for battery_id in telemetry_df['battery_id'].unique():
            battery_states[battery_id] = {
                'soh_pct': 95.0,
                'rul_days': 1369.0,  # ~3.75 years
            }

    logger.info(f"Created states for {len(battery_states)} batteries")

    return telemetry_df, battery_states


def main():
    parser = argparse.ArgumentParser(description="Train RUL prediction model")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=settings.DATA_DIR,
        help="Directory containing training data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.MODEL_DIR,
        help="Directory to save trained model"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=settings.CATBOOST_ITERATIONS,
        help="CatBoost iterations"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set proportion (0-1)"
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=settings.LOOKBACK_HOURS,
        help="Hours of historical data for features"
    )

    args = parser.parse_args()

    try:
        # Load data
        telemetry_df, battery_states = load_training_data(args.data_dir)

        # Initialize feature engineer
        feature_engineer = FeatureEngineer(lookback_hours=args.lookback_hours)

        # Prepare training data
        logger.info("Extracting features...")
        X, y = feature_engineer.prepare_training_data(telemetry_df, battery_states)

        if X.empty or y.empty:
            raise ValueError("Failed to extract features from training data")

        logger.info(f"Feature matrix shape: {X.shape}")
        logger.info(f"Target shape: {y.shape}")
        logger.info(f"Features: {list(X.columns)}")

        # Initialize trainer
        trainer = RULModelTrainer(iterations=args.iterations)

        # Train model
        logger.info("Training CatBoost model...")
        metrics = trainer.train(X, y, test_size=args.test_size)

        # Print metrics
        logger.info("=" * 80)
        logger.info("TRAINING RESULTS")
        logger.info("=" * 80)
        logger.info(f"Train MAE: {metrics['train']['mae']:.2f} days")
        logger.info(f"Train RMSE: {metrics['train']['rmse']:.2f} days")
        logger.info(f"Train R²: {metrics['train']['r2']:.3f}")
        logger.info("")
        logger.info(f"Test MAE: {metrics['test']['mae']:.2f} days")
        logger.info(f"Test RMSE: {metrics['test']['rmse']:.2f} days")
        logger.info(f"Test R²: {metrics['test']['r2']:.3f}")
        logger.info("=" * 80)

        # Print top 10 important features
        logger.info("\nTop 10 Most Important Features:")
        importance = metrics['feature_importance']
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        for i, (feature, imp) in enumerate(sorted_features[:10], 1):
            logger.info(f"{i:2d}. {feature:30s}: {imp:.2f}")

        # Save model
        args.output_dir.mkdir(parents=True, exist_ok=True)
        model_path = args.output_dir / "rul_catboost_model.cbm"
        trainer.save_model(model_path)

        logger.info(f"\nModel saved to: {model_path}")
        logger.info("Training complete!")

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
