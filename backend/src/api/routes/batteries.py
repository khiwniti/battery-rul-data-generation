"""
Battery API Routes
Endpoints for battery monitoring and telemetry
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from ...core.database import get_db
from ...core.logging import logger
from ...api.dependencies import get_current_active_user
from ...models.battery import Battery
from ...models.telemetry import Telemetry
from ...models.string import String
from ...models.battery_system import BatterySystem
from ...models.location import Location
from ...models.user import User
from ...schemas.battery import (
    BatteryResponse,
    BatteryWithTelemetry,
    BatteryListResponse,
    BatteryDetailResponse,
    TelemetryData,
)

router = APIRouter()


def calculate_battery_status(telemetry: Optional[Telemetry]) -> str:
    """
    Calculate battery status from telemetry

    Args:
        telemetry: Latest telemetry data

    Returns:
        Status: healthy, warning, critical
    """
    if not telemetry:
        return "unknown"

    # Check critical conditions
    if telemetry.voltage < 11.5 or telemetry.voltage > 14.5:
        return "critical"
    if telemetry.temperature > 45.0:
        return "critical"
    if telemetry.soh_pct and telemetry.soh_pct < 80.0:
        return "critical"

    # Check warning conditions
    if telemetry.voltage < 12.0 or telemetry.voltage > 14.0:
        return "warning"
    if telemetry.temperature > 35.0:
        return "warning"
    if telemetry.soh_pct and telemetry.soh_pct < 90.0:
        return "warning"

    return "healthy"


@router.get("/", response_model=BatteryListResponse)
async def list_batteries(
    location_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List batteries with latest telemetry

    Args:
        location_id: Filter by location (optional)
        skip: Pagination offset
        limit: Maximum results (max 1000)

    Returns:
        List of batteries with latest telemetry data
    """
    logger.info(
        "Listing batteries",
        user=current_user.username,
        location_id=location_id,
        skip=skip,
        limit=limit,
    )

    # Build query
    query = select(Battery).options(
        joinedload(Battery.string).joinedload(String.battery_system)
    )

    # Filter by location if specified
    if location_id:
        query = query.join(String, Battery.string_id == String.id).join(
            BatterySystem, String.system_id == BatterySystem.id
        ).where(BatterySystem.location_id == location_id)

    query = query.offset(skip).limit(min(limit, 1000))

    # Execute query
    result = await db.execute(query)
    batteries = result.unique().scalars().all()

    # Get latest telemetry for each battery
    batteries_with_telemetry = []
    for battery in batteries:
        # Get latest telemetry
        telemetry_result = await db.execute(
            select(Telemetry)
            .where(Telemetry.battery_id == battery.battery_id)
            .order_by(desc(Telemetry.timestamp))
            .limit(1)
        )
        latest_telemetry = telemetry_result.scalar_one_or_none()

        # Convert to response model
        batteries_with_telemetry.append(
            BatteryWithTelemetry(
                **battery.__dict__,
                latest_telemetry=TelemetryData(**latest_telemetry.__dict__) if latest_telemetry else None,
                status=calculate_battery_status(latest_telemetry),
                active_alerts=0,  # TODO: Count alerts
            )
        )

    return BatteryListResponse(
        batteries=batteries_with_telemetry,
        total=len(batteries_with_telemetry),
    )


@router.get("/{battery_id}", response_model=BatteryDetailResponse)
async def get_battery(
    battery_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get battery details with latest telemetry

    Args:
        battery_id: Battery identifier

    Returns:
        Detailed battery information
    """
    logger.info("Getting battery", user=current_user.username, battery_id=battery_id)

    # Get battery with relationships
    result = await db.execute(
        select(Battery)
        .options(
            joinedload(Battery.string).joinedload(String.battery_system).joinedload(BatterySystem.location)
        )
        .where(Battery.battery_id == battery_id)
    )
    battery = result.unique().scalar_one_or_none()

    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery {battery_id} not found",
        )

    # Get latest telemetry
    telemetry_result = await db.execute(
        select(Telemetry)
        .where(Telemetry.battery_id == battery.battery_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(1)
    )
    latest_telemetry = telemetry_result.scalar_one_or_none()

    # Build response
    return BatteryDetailResponse(
        **battery.__dict__,
        latest_telemetry=TelemetryData(**latest_telemetry.__dict__) if latest_telemetry else None,
        status=calculate_battery_status(latest_telemetry),
        active_alerts=0,  # TODO: Count alerts
        age_days=battery.age_days,
        is_in_warranty=battery.is_in_warranty,
        string_info={
            "string_id": battery.string.string_id,
            "position": battery.string.position,
        },
        location_info={
            "location_id": battery.string.battery_system.location_id,
            "name": battery.string.battery_system.location.name,
        },
    )


@router.get("/{battery_id}/telemetry")
async def get_battery_telemetry(
    battery_id: str,
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(1000, le=10000, description="Maximum results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get battery telemetry time-series data

    Args:
        battery_id: Battery identifier
        start: Start timestamp (default: 24 hours ago)
        end: End timestamp (default: now)
        limit: Maximum results (max 10000)

    Returns:
        Time-series telemetry data
    """
    logger.info(
        "Getting battery telemetry",
        user=current_user.username,
        battery_id=battery_id,
        start=start,
        end=end,
    )

    # Verify battery exists
    battery_result = await db.execute(
        select(Battery).where(Battery.battery_id == battery_id)
    )
    if not battery_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Battery {battery_id} not found",
        )

    # Default time range: last 24 hours
    if not end:
        end = datetime.utcnow()
    if not start:
        start = end - timedelta(hours=24)

    # Query telemetry
    result = await db.execute(
        select(Telemetry)
        .where(
            Telemetry.battery_id == battery_id,
            Telemetry.timestamp >= start,
            Telemetry.timestamp <= end,
        )
        .order_by(Telemetry.timestamp)
        .limit(limit)
    )
    telemetry_data = result.scalars().all()

    return {
        "battery_id": battery_id,
        "start": start,
        "end": end,
        "data": [TelemetryData(**t.__dict__).dict() for t in telemetry_data],
        "count": len(telemetry_data),
    }
