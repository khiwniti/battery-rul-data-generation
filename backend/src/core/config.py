"""
Configuration Management
Loads settings from Railway.com environment variables
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Battery RUL Prediction API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Internal Service URLs (Railway.com private networking)
    ML_PIPELINE_URL: str = "http://ml-pipeline.railway.internal:8001"
    DIGITAL_TWIN_URL: str = "http://digital-twin.railway.internal:8002"
    SENSOR_SIMULATOR_URL: str = "http://sensor-simulator.railway.internal:8003"

    # Model Configuration
    ML_MODEL_VERSION: str = "v1.0.0"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Feature Flags
    ENABLE_SIMULATION: bool = True
    ENABLE_ML_PREDICTIONS: bool = True
    ENABLE_DIGITAL_TWIN: bool = True
    ENABLE_TELEMETRY_BROADCAST: bool = False  # Enable real-time WebSocket broadcasting

    # Performance
    PREDICTION_CACHE_TTL_SECONDS: int = 3600  # 60 minutes

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to create singleton pattern
    """
    return Settings()


# Global settings instance
settings = get_settings()
