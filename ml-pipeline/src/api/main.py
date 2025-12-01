"""
ML Pipeline Service
CatBoost inference service for RUL prediction
"""
import logging
from datetime import datetime
from typing import Dict

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .ml.feature_engineering import FeatureEngineer
from .ml.model_training import RULModelTrainer
from .schemas.prediction import (
    RULPredictionRequest,
    RULPredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelInfoResponse,
    HealthCheckResponse,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ML Pipeline Service",
    version=settings.VERSION,
    description="CatBoost-based ML inference for battery RUL prediction",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Internal service, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model trainer and feature engineer
model_trainer: RULModelTrainer = RULModelTrainer()
feature_engineer: FeatureEngineer = FeatureEngineer(
    lookback_hours=settings.LOOKBACK_HOURS
)


@app.on_event("startup")
async def startup_event():
    """Load model on startup if it exists"""
    try:
        if settings.MODEL_PATH.exists():
            model_trainer.load_model()
            logger.info(f"Model loaded successfully from {settings.MODEL_PATH}")
        else:
            logger.warning(f"No pre-trained model found at {settings.MODEL_PATH}")
            logger.warning("Train a model using the /api/v1/model/train endpoint")
    except Exception as e:
        logger.error(f"Error loading model: {e}")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for Railway.com"""
    return HealthCheckResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        model_loaded=model_trainer.is_trained,
        model_path=str(settings.MODEL_PATH) if model_trainer.is_trained else None,
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ML Pipeline Service",
        "version": settings.VERSION,
        "endpoints": {
            "health": "/health",
            "predict_rul": "/api/v1/predict/rul",
            "batch_predict": "/api/v1/predict/batch",
            "model_info": "/api/v1/model/info",
        },
        "model_loaded": model_trainer.is_trained,
    }


@app.post("/api/v1/predict/rul", response_model=RULPredictionResponse)
async def predict_rul(request: RULPredictionRequest):
    """
    Predict Remaining Useful Life for a battery

    Uses CatBoost model with temperature-aware features
    """
    if not model_trainer.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train or load a model first."
        )

    try:
        # Convert telemetry history to DataFrame
        telemetry_data = [t.model_dump() for t in request.telemetry_history]
        telemetry_df = pd.DataFrame(telemetry_data)

        # Extract features
        features_df = feature_engineer.extract_features(
            telemetry_df,
            battery_id=request.battery_id
        )

        if features_df.empty:
            raise HTTPException(
                status_code=400,
                detail="Insufficient telemetry data to extract features"
            )

        # Get latest features
        latest_features = features_df.iloc[-1]

        # Prepare feature matrix for prediction
        feature_columns = [col for col in latest_features.index
                          if col not in ['battery_id', 'timestamp']]
        X = latest_features[feature_columns].to_frame().T

        # Make prediction
        rul_prediction, confidence = model_trainer.predict_with_confidence(X)
        rul_days = float(rul_prediction[0])
        confidence_score = float(confidence[0])

        # Determine risk level
        if rul_days < settings.RUL_CRITICAL_DAYS:
            risk_level = "critical"
        elif rul_days < settings.RUL_WARNING_DAYS:
            risk_level = "warning"
        else:
            risk_level = "normal"

        # Get current SOH
        soh_current = float(latest_features.get('soh_current', 100.0))

        # Convert features to dict
        features_dict = latest_features[feature_columns].to_dict()

        return RULPredictionResponse(
            battery_id=request.battery_id,
            rul_days=rul_days,
            confidence_score=confidence_score,
            soh_current=soh_current,
            risk_level=risk_level,
            prediction_timestamp=datetime.utcnow(),
            features_used=features_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error for battery {request.battery_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/api/v1/predict/batch", response_model=BatchPredictionResponse)
async def batch_predict(request: BatchPredictionRequest):
    """
    Batch RUL prediction for multiple batteries
    """
    if not model_trainer.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train or load a model first."
        )

    predictions = []
    failed_count = 0

    for battery_request in request.batteries:
        try:
            prediction = await predict_rul(battery_request)
            predictions.append(prediction)
        except Exception as e:
            logger.error(f"Failed to predict for battery {battery_request.battery_id}: {e}")
            failed_count += 1

    return BatchPredictionResponse(
        predictions=predictions,
        total_batteries=len(request.batteries),
        successful_predictions=len(predictions),
        failed_predictions=failed_count,
    )


@app.get("/api/v1/model/info", response_model=ModelInfoResponse)
async def model_info():
    """
    Get current ML model information
    """
    if not model_trainer.is_trained:
        raise HTTPException(
            status_code=404,
            detail="No model loaded"
        )

    training_date = None
    if settings.MODEL_PATH.exists():
        training_date = datetime.fromtimestamp(settings.MODEL_PATH.stat().st_mtime)

    return ModelInfoResponse(
        model_version=settings.VERSION,
        training_date=training_date,
        training_metrics=model_trainer.training_metrics,
        feature_count=len(model_trainer.feature_names) if model_trainer.feature_names else 0,
        feature_names=model_trainer.feature_names or [],
        model_params={
            'iterations': model_trainer.iterations,
            'learning_rate': model_trainer.learning_rate,
            'depth': model_trainer.depth,
            'l2_leaf_reg': model_trainer.l2_leaf_reg,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
