"""
ML Pipeline Configuration
Settings for model training and inference
"""
import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ML Pipeline service configuration"""

    # Service
    SERVICE_NAME: str = "ml-pipeline"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database (for feature extraction from production data)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/battery_rul"
    )

    # Model paths
    MODEL_DIR: Path = Path(__file__).parent.parent.parent / "models"
    MODEL_PATH: Path = MODEL_DIR / "rul_catboost_model.cbm"
    FEATURE_CONFIG_PATH: Path = MODEL_DIR / "feature_config.json"

    # Training data paths
    DATA_DIR: Path = Path(__file__).parent.parent.parent.parent / "output" / "deployment_dataset"

    # Model parameters
    CATBOOST_ITERATIONS: int = 1000
    CATBOOST_LEARNING_RATE: float = 0.03
    CATBOOST_DEPTH: int = 6
    CATBOOST_L2_LEAF_REG: float = 3.0

    # Feature engineering
    LOOKBACK_HOURS: int = 24  # Use last 24 hours of data for features
    AGGREGATION_INTERVALS: List[str] = ["1h", "6h", "24h"]

    # RUL thresholds
    RUL_WARNING_DAYS: int = 180
    RUL_CRITICAL_DAYS: int = 90

    # Prediction confidence
    MIN_CONFIDENCE_SCORE: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure model directory exists
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
