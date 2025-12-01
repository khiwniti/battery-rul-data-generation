"""
FastAPI Main Application
Battery RUL Prediction & Monitoring System
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import socketio

from .core.config import settings
from .core.database import close_db, init_db
from .core.logging import setup_logging, logger
from .core.websocket import ws_manager
from .api.middleware.error_handlers import setup_error_handlers
from .services.telemetry_broadcaster import telemetry_broadcaster


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Battery RUL Prediction API", environment=settings.ENVIRONMENT)

    # Initialize database (development only - use Alembic in production)
    if settings.is_development:
        logger.info("Development mode: Initializing database tables")
        # await init_db()  # Commented out - use Alembic migrations instead

    # Start telemetry broadcaster (only in production or if enabled)
    if not settings.is_development or settings.ENABLE_TELEMETRY_BROADCAST:
        logger.info("Starting telemetry broadcaster")
        await telemetry_broadcaster.start()

    logger.info(
        "API started successfully",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )

    yield

    # Shutdown
    logger.info("Shutting down Battery RUL Prediction API")

    # Stop telemetry broadcaster
    await telemetry_broadcaster.stop()

    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Battery RUL Prediction & Monitoring System - Real-time battery health monitoring with ML-powered RUL forecasting",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Setup structured logging
setup_logging()

# Setup error handlers
setup_error_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Railway.com

    Returns basic service status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "backend-api",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint

    Validates database connectivity and service dependencies
    """
    try:
        from .core.database import engine
        import sqlalchemy as sa

        # Test database connection
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))

        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "service": "backend-api",
                "database": "connected",
                "ml_pipeline": settings.ML_PIPELINE_URL,
                "digital_twin": settings.DIGITAL_TWIN_URL,
            },
        )
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "backend-api",
                "error": str(e),
            },
        )


# Import and register API routers
from .api.routes import locations, batteries, alerts, auth

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)
app.include_router(
    locations.router,
    prefix=f"{settings.API_V1_PREFIX}/locations",
    tags=["Locations"]
)
app.include_router(
    batteries.router,
    prefix=f"{settings.API_V1_PREFIX}/batteries",
    tags=["Batteries"]
)
app.include_router(
    alerts.router,
    prefix=f"{settings.API_V1_PREFIX}/alerts",
    tags=["Alerts"]
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/api/docs" if settings.is_development else None,
        "health": "/health",
        "websocket": "/socket.io",
    }


# Mount Socket.IO ASGI app for WebSocket connections
socket_app = socketio.ASGIApp(
    ws_manager.sio,
    other_asgi_app=app,
    socketio_path='/socket.io',
)

# Export the combined app
app_with_sockets = socket_app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app_with_sockets",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
