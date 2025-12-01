"""
Pydantic Schemas for ML Pipeline API
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BatteryTelemetryInput(BaseModel):
    """Input telemetry data for RUL prediction"""
    battery_id: str
    timestamp: datetime
    voltage_v: float = Field(..., ge=0, le=20, description="Battery voltage in volts")
    current_a: float = Field(..., description="Battery current in amperes")
    temperature_c: float = Field(..., ge=-50, le=100, description="Battery temperature in Celsius")
    internal_resistance_mohm: Optional[float] = Field(None, ge=0, description="Internal resistance in milliohms")
    soc_pct: Optional[float] = Field(None, ge=0, le=100, description="State of Charge percentage")
    soh_pct: Optional[float] = Field(None, ge=0, le=100, description="State of Health percentage")


class RULPredictionRequest(BaseModel):
    """Request for single battery RUL prediction"""
    battery_id: str
    telemetry_history: List[BatteryTelemetryInput] = Field(
        ...,
        min_length=10,
        description="Historical telemetry data (minimum 10 data points)"
    )


class RULPredictionResponse(BaseModel):
    """Response with RUL prediction"""
    battery_id: str
    rul_days: float = Field(..., description="Predicted Remaining Useful Life in days")
    confidence_score: float = Field(..., ge=0, le=1, description="Prediction confidence (0-1)")
    soh_current: float = Field(..., description="Current State of Health percentage")
    risk_level: str = Field(..., description="Risk level: normal, warning, critical")
    prediction_timestamp: datetime
    features_used: Dict[str, float] = Field(..., description="Extracted features used for prediction")


class BatchPredictionRequest(BaseModel):
    """Request for batch RUL predictions"""
    batteries: List[RULPredictionRequest] = Field(
        ...,
        max_length=100,
        description="List of batteries to predict (max 100)"
    )


class BatchPredictionResponse(BaseModel):
    """Response with batch predictions"""
    predictions: List[RULPredictionResponse]
    total_batteries: int
    successful_predictions: int
    failed_predictions: int


class ModelInfoResponse(BaseModel):
    """Model information response"""
    model_version: str
    training_date: Optional[datetime]
    training_metrics: Optional[Dict]
    feature_count: int
    feature_names: List[str]
    model_params: Dict


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    model_loaded: bool
    model_path: Optional[str]
