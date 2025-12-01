"""
Location API Routes
Endpoints for managing and retrieving location data
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.logging import logger
from ...api.dependencies import get_current_active_user
from ...models.location import Location
from ...models.battery_system import BatterySystem
from ...models.string import String
from ...models.battery import Battery
from ...models.user import User
from ...schemas.location import (
    LocationResponse,
    LocationWithStats,
    LocationListResponse,
)

router = APIRouter()


@router.get("/", response_model=LocationListResponse)
async def list_locations(
    include_stats: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all data center locations

    Returns:
        List of locations with optional battery statistics
    """
    logger.info("Listing locations", user=current_user.username, include_stats=include_stats)

    # Get all locations
    result = await db.execute(
        select(Location).order_by(Location.name)
    )
    locations = result.scalars().all()

    if not include_stats:
        return LocationListResponse(
            locations=[LocationWithStats(**loc.__dict__, total_batteries=0, active_batteries=0, critical_batteries=0, active_alerts=0) for loc in locations],
            total=len(locations),
        )

    # Get battery counts per location
    location_data = []
    for location in locations:
        # Count batteries at this location
        battery_count_result = await db.execute(
            select(func.count(Battery.id))
            .join(String, Battery.string_id == String.id)
            .join(BatterySystem, String.system_id == BatterySystem.id)
            .where(BatterySystem.location_id == location.location_id)
        )
        total_batteries = battery_count_result.scalar() or 0

        # TODO: Add real-time telemetry stats, critical battery count, active alerts
        # For now, return placeholder values
        location_data.append(
            LocationWithStats(
                **location.__dict__,
                total_batteries=total_batteries,
                active_batteries=total_batteries,
                critical_batteries=0,
                average_soh=None,
                active_alerts=0,
            )
        )

    return LocationListResponse(
        locations=location_data,
        total=len(location_data),
    )


@router.get("/{location_id}", response_model=LocationWithStats)
async def get_location(
    location_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get location details by ID

    Args:
        location_id: Location identifier (e.g., DC-CNX-01)

    Returns:
        Location with battery statistics
    """
    logger.info("Getting location", user=current_user.username, location_id=location_id)

    # Get location
    result = await db.execute(
        select(Location).where(Location.location_id == location_id)
    )
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )

    # Count batteries
    battery_count_result = await db.execute(
        select(func.count(Battery.id))
        .join(String, Battery.string_id == String.id)
        .join(BatterySystem, String.system_id == BatterySystem.id)
        .where(BatterySystem.location_id == location.location_id)
    )
    total_batteries = battery_count_result.scalar() or 0

    # TODO: Add real-time telemetry stats
    return LocationWithStats(
        **location.__dict__,
        total_batteries=total_batteries,
        active_batteries=total_batteries,
        critical_batteries=0,
        average_soh=None,
        active_alerts=0,
    )


@router.get("/{location_id}/batteries")
async def get_location_batteries(
    location_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all batteries at a location

    Args:
        location_id: Location identifier
        skip: Pagination offset
        limit: Maximum results (max 1000)

    Returns:
        List of batteries with latest telemetry
    """
    logger.info(
        "Getting location batteries",
        user=current_user.username,
        location_id=location_id,
        skip=skip,
        limit=limit,
    )

    # Validate location exists
    location_result = await db.execute(
        select(Location).where(Location.location_id == location_id)
    )
    if not location_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found",
        )

    # Get batteries at location
    result = await db.execute(
        select(Battery)
        .join(String, Battery.string_id == String.id)
        .join(BatterySystem, String.system_id == BatterySystem.id)
        .where(BatterySystem.location_id == location_id)
        .order_by(BatterySystem.system_id, String.position, Battery.position)
        .offset(skip)
        .limit(min(limit, 1000))
    )
    batteries = result.scalars().all()

    # TODO: Add latest telemetry data
    return {
        "batteries": [battery.__dict__ for battery in batteries],
        "total": len(batteries),
    }
