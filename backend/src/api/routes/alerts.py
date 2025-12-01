"""
Alert API Routes
Endpoints for battery alert management and acknowledgment
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import joinedload

from ...core.database import get_db
from ...core.logging import logger
from ...api.dependencies import get_current_active_user, require_engineer_or_admin
from ...models.alert import Alert, AlertType, AlertSeverity
from ...models.battery import Battery
from ...models.string import String
from ...models.battery_system import BatterySystem
from ...models.location import Location
from ...models.user import User
from ...schemas.alert import (
    AlertResponse,
    AlertListResponse,
    AlertAcknowledgeRequest,
    AlertStatsResponse,
    AlertWithBatteryInfo,
)

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    location_id: Optional[str] = Query(None, description="Filter by location"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    active_only: bool = Query(True, description="Show only active (unresolved) alerts"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    start_date: Optional[datetime] = Query(None, description="Filter alerts after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter alerts before this date"),
    skip: int = 0,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List battery alerts with filters

    Args:
        location_id: Filter by data center location
        severity: Filter by severity level
        alert_type: Filter by alert type
        active_only: Show only unresolved alerts
        acknowledged: Filter by acknowledgment status
        start_date: Start date for alert search
        end_date: End date for alert search
        skip: Pagination offset
        limit: Maximum results (max 1000)

    Returns:
        List of alerts with statistics
    """
    logger.info(
        "Listing alerts",
        user=current_user.username,
        location_id=location_id,
        severity=severity,
        active_only=active_only,
    )

    # Build query
    query = select(Alert).options(
        joinedload(Alert.battery).joinedload(Battery.string).joinedload(String.battery_system).joinedload(BatterySystem.location)
    )

    # Apply filters
    filters = []

    if location_id:
        filters.append(
            Battery.string.has(
                String.battery_system.has(BatterySystem.location_id == location_id)
            )
        )

    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
            filters.append(Alert.severity == severity_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Must be one of: info, warning, critical",
            )

    if alert_type:
        try:
            alert_type_enum = AlertType(alert_type.lower())
            filters.append(Alert.alert_type == alert_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alert_type: {alert_type}",
            )

    if active_only:
        filters.append(Alert.resolved_at == None)

    if acknowledged is not None:
        filters.append(Alert.is_acknowledged == acknowledged)

    if start_date:
        filters.append(Alert.triggered_at >= start_date)

    if end_date:
        filters.append(Alert.triggered_at <= end_date)

    if filters:
        query = query.where(and_(*filters))

    # Order by triggered_at descending (newest first)
    query = query.order_by(desc(Alert.triggered_at))

    # Count total
    count_query = select(func.count(Alert.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    alerts = result.unique().scalars().all()

    # Count active and pending
    active_count = sum(1 for alert in alerts if alert.is_active)
    pending_count = sum(1 for alert in alerts if alert.is_pending)

    # Convert to response models
    alert_responses = []
    for alert in alerts:
        alert_responses.append(
            AlertResponse(
                **alert.__dict__,
                is_active=alert.is_active,
                is_pending=alert.is_pending,
            )
        )

    return AlertListResponse(
        alerts=alert_responses,
        total=total,
        active_count=active_count,
        pending_count=pending_count,
    )


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    location_id: Optional[str] = Query(None, description="Filter by location"),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get alert statistics

    Args:
        location_id: Filter by location (optional)
        days: Number of days to analyze (default: 7)

    Returns:
        Alert statistics including counts by type, severity, and location
    """
    logger.info(
        "Getting alert statistics",
        user=current_user.username,
        location_id=location_id,
        days=days,
    )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Base query
    query = select(Alert).where(Alert.triggered_at >= start_date)

    if location_id:
        query = query.join(Battery, Alert.battery_id == Battery.battery_id).join(
            String, Battery.string_id == String.id
        ).join(BatterySystem, String.system_id == BatterySystem.id).where(
            BatterySystem.location_id == location_id
        )

    # Execute query
    result = await db.execute(query)
    alerts = result.scalars().all()

    # Calculate statistics
    total_alerts = len(alerts)
    active_alerts = sum(1 for a in alerts if a.is_active)
    critical_alerts = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
    warning_alerts = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)
    info_alerts = sum(1 for a in alerts if a.severity == AlertSeverity.INFO)
    acknowledged_alerts = sum(1 for a in alerts if a.is_acknowledged)

    # Count by alert type
    alerts_by_type = {}
    for alert in alerts:
        alert_type_str = alert.alert_type.value
        alerts_by_type[alert_type_str] = alerts_by_type.get(alert_type_str, 0) + 1

    # Count by location (if not filtered by location)
    alerts_by_location = {}
    if not location_id:
        for alert in alerts:
            # Get location from battery relationship
            if alert.battery and alert.battery.string and alert.battery.string.battery_system:
                loc_id = alert.battery.string.battery_system.location_id
                alerts_by_location[loc_id] = alerts_by_location.get(loc_id, 0) + 1

    return AlertStatsResponse(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        critical_alerts=critical_alerts,
        warning_alerts=warning_alerts,
        info_alerts=info_alerts,
        acknowledged_alerts=acknowledged_alerts,
        alerts_by_type=alerts_by_type,
        alerts_by_location=alerts_by_location,
    )


@router.get("/{alert_id}", response_model=AlertWithBatteryInfo)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get alert details by ID

    Args:
        alert_id: Alert identifier

    Returns:
        Alert with battery context
    """
    logger.info("Getting alert", user=current_user.username, alert_id=alert_id)

    # Query alert with all relationships
    result = await db.execute(
        select(Alert)
        .options(
            joinedload(Alert.battery)
            .joinedload(Battery.string)
            .joinedload(String.battery_system)
            .joinedload(BatterySystem.location)
        )
        .where(Alert.alert_id == alert_id)
    )
    alert = result.unique().scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )

    # Build response with battery context
    battery = alert.battery
    location = battery.string.battery_system.location if battery else None

    return AlertWithBatteryInfo(
        **alert.__dict__,
        is_active=alert.is_active,
        is_pending=alert.is_pending,
        battery_serial=battery.serial_number if battery else "Unknown",
        battery_position=battery.position if battery else 0,
        location_id=location.location_id if location else "Unknown",
        location_name=location.name if location else "Unknown",
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    current_user: User = Depends(require_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Acknowledge an alert

    Args:
        alert_id: Alert identifier
        request: Acknowledgment request with optional note

    Returns:
        Updated alert

    Requires:
        Engineer or Admin role
    """
    logger.info(
        "Acknowledging alert",
        user=current_user.username,
        alert_id=alert_id,
    )

    # Get alert
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )

    if alert.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert has already been acknowledged",
        )

    # Update alert
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.user_id
    alert.acknowledgment_note = request.note

    await db.commit()
    await db.refresh(alert)

    logger.info(
        "Alert acknowledged",
        alert_id=alert_id,
        acknowledged_by=current_user.username,
    )

    return AlertResponse(
        **alert.__dict__,
        is_active=alert.is_active,
        is_pending=alert.is_pending,
    )


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually resolve an alert

    Args:
        alert_id: Alert identifier

    Returns:
        Updated alert

    Requires:
        Engineer or Admin role
    """
    logger.info(
        "Resolving alert",
        user=current_user.username,
        alert_id=alert_id,
    )

    # Get alert
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )

    if not alert.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert has already been resolved",
        )

    # Resolve alert
    alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    logger.info(
        "Alert resolved",
        alert_id=alert_id,
        resolved_by=current_user.username,
    )

    return AlertResponse(
        **alert.__dict__,
        is_active=alert.is_active,
        is_pending=alert.is_pending,
    )
