"""
Alert Schemas
Pydantic models for alert API requests/responses
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class AlertBase(BaseModel):
    """Base alert schema"""
    alert_id: str
    battery_id: str
    alert_type: str
    severity: str
    message: str
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    triggered_at: datetime


class AlertResponse(AlertBase):
    """Alert response with full details"""
    id: UUID
    resolved_at: Optional[datetime] = None
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledgment_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed properties
    is_active: bool = Field(description="Whether alert is still active (not resolved)")
    is_pending: bool = Field(description="Whether alert is pending acknowledgment")

    class Config:
        from_attributes = True


class AlertWithBatteryInfo(AlertResponse):
    """Alert with battery context"""
    battery_serial: str
    battery_position: int
    location_id: str
    location_name: str


class AlertListResponse(BaseModel):
    """List of alerts"""
    alerts: list[AlertResponse]
    total: int
    active_count: int = Field(description="Number of active (unresolved) alerts")
    pending_count: int = Field(description="Number of pending (unacknowledged) alerts")


class AlertAcknowledgeRequest(BaseModel):
    """Request to acknowledge an alert"""
    note: Optional[str] = Field(None, max_length=1000, description="Optional acknowledgment note")


class AlertStatsResponse(BaseModel):
    """Alert statistics"""
    total_alerts: int
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    acknowledged_alerts: int
    alerts_by_type: dict[str, int]
    alerts_by_location: dict[str, int]


class AlertCreateRequest(BaseModel):
    """Request to create a new alert (internal use)"""
    battery_id: str
    alert_type: str
    severity: str
    message: str
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
