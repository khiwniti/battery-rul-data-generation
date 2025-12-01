"""
Location Schemas
Pydantic models for location API requests/responses
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    """Base location schema"""
    location_id: str
    name: str
    region: str
    city: str
    latitude: float
    longitude: float
    temp_offset_c: float
    humidity_offset_pct: float
    power_outage_frequency_per_year: int


class LocationResponse(LocationBase):
    """Location response with metadata"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationWithStats(LocationResponse):
    """Location with battery statistics"""
    total_batteries: int = Field(description="Total batteries at location")
    active_batteries: int = Field(description="Active batteries")
    critical_batteries: int = Field(description="Batteries with critical alerts")
    average_soh: Optional[float] = Field(None, description="Average State of Health (%)")
    active_alerts: int = Field(description="Number of active alerts")


class LocationListResponse(BaseModel):
    """List of locations"""
    locations: list[LocationWithStats]
    total: int
