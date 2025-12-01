"""
Battery Schemas
Pydantic models for battery API requests/responses
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class BatteryBase(BaseModel):
    """Base battery schema"""
    battery_id: str
    serial_number: str
    position: int
    manufacturer: str
    model: str
    nominal_voltage_v: float
    nominal_capacity_ah: float
    installed_date: date
    warranty_months: int


class BatteryResponse(BatteryBase):
    """Battery response with metadata"""
    string_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TelemetryData(BaseModel):
    """Telemetry data point"""
    timestamp: datetime
    voltage: float
    current: Optional[float]
    temperature: float
    internal_resistance: Optional[float]
    soc_pct: Optional[float]
    soh_pct: Optional[float]

    class Config:
        from_attributes = True


class BatteryWithTelemetry(BatteryResponse):
    """Battery with latest telemetry"""
    latest_telemetry: Optional[TelemetryData] = None
    status: str = Field(description="healthy, warning, critical")
    active_alerts: int = Field(default=0)


class BatteryListResponse(BaseModel):
    """List of batteries with telemetry"""
    batteries: list[BatteryWithTelemetry]
    total: int


class BatteryDetailResponse(BatteryResponse):
    """Detailed battery information"""
    latest_telemetry: Optional[TelemetryData]
    status: str
    active_alerts: int
    age_days: int
    is_in_warranty: bool
    string_info: dict
    location_info: dict
