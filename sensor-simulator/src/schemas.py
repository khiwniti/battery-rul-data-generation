"""
Pydantic schemas for Sensor Simulator API
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class OperatingMode(str, Enum):
    """Battery operating modes"""
    FLOAT = "float"
    DISCHARGE = "discharge"
    BOOST = "boost"
    EQUALIZE = "equalize"


class BatteryProfile(str, Enum):
    """Battery degradation profiles"""
    HEALTHY = "healthy"
    ACCELERATED = "accelerated"
    FAILING = "failing"


class ScenarioType(str, Enum):
    """Test scenarios"""
    NORMAL_OPERATION = "normal_operation"
    HIGH_TEMPERATURE = "high_temperature"
    POWER_OUTAGE = "power_outage"
    HVAC_FAILURE = "hvac_failure"
    BATTERY_DEGRADATION = "battery_degradation"
    THERMAL_RUNAWAY = "thermal_runaway"


class BatteryConfig(BaseModel):
    """Battery configuration for simulation"""
    battery_id: str = Field(..., description="Battery identifier")
    profile: BatteryProfile = Field(
        default=BatteryProfile.HEALTHY,
        description="Degradation profile"
    )
    initial_soh: float = Field(
        default=100.0,
        ge=0,
        le=100,
        description="Initial State of Health (%)"
    )


class SimulationStartRequest(BaseModel):
    """Request to start simulation"""
    batteries: List[BatteryConfig] = Field(
        ...,
        description="List of batteries to simulate",
        min_items=1
    )
    interval_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Telemetry generation interval in seconds"
    )
    scenario: Optional[ScenarioType] = Field(
        default=None,
        description="Optional scenario to apply"
    )


class SimulationStatus(BaseModel):
    """Current simulation status"""
    is_running: bool
    batteries_count: int
    interval_seconds: int
    scenario: Optional[ScenarioType]
    started_at: Optional[datetime]
    readings_generated: int


class ScenarioRequest(BaseModel):
    """Request to apply a scenario"""
    scenario: ScenarioType = Field(..., description="Scenario to apply")
    battery_ids: Optional[List[str]] = Field(
        default=None,
        description="Battery IDs to apply scenario to (None = all)"
    )
    ambient_temp: Optional[float] = Field(
        default=None,
        ge=-10,
        le=60,
        description="Override ambient temperature"
    )


class ScenarioInfo(BaseModel):
    """Information about a test scenario"""
    scenario: ScenarioType
    name: str
    description: str
    typical_conditions: dict


class TelemetryReading(BaseModel):
    """Single telemetry reading"""
    battery_id: str
    timestamp: datetime
    voltage_v: float
    current_a: float
    temperature_c: float
    internal_resistance_mohm: float
    soh_pct: float
    mode: OperatingMode


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # "telemetry", "alert", "status"
    data: dict
    timestamp: datetime
