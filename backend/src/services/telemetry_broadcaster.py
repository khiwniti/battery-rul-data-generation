"""
Telemetry Broadcasting Service
Background service for broadcasting real-time battery telemetry updates
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..core.database import get_db
from ..core.logging import logger
from ..core.websocket import ws_manager
from ..models.telemetry import Telemetry
from ..models.battery import Battery
from ..models.string import String
from ..models.battery_system import BatterySystem
from ..api.routes.batteries import calculate_battery_status


class TelemetryBroadcaster:
    """
    Service for broadcasting real-time telemetry updates via WebSocket

    This service:
    - Polls for new telemetry data
    - Broadcasts updates to subscribed WebSocket clients
    - Handles battery status changes
    - Triggers alerts when thresholds are violated
    """

    def __init__(self, poll_interval: float = 5.0):
        """
        Initialize broadcaster

        Args:
            poll_interval: Seconds between telemetry polls (default: 5.0)
        """
        self.poll_interval = poll_interval
        self.last_check: Dict[str, datetime] = {}
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

        logger.info(
            "Telemetry broadcaster initialized",
            poll_interval=poll_interval,
        )

    async def start(self):
        """Start the broadcasting service"""
        if self.is_running:
            logger.warning("Telemetry broadcaster already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._broadcast_loop())
        logger.info("Telemetry broadcaster started")

    async def stop(self):
        """Stop the broadcasting service"""
        if not self.is_running:
            return

        self.is_running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Telemetry broadcaster stopped")

    async def _broadcast_loop(self):
        """Main broadcasting loop"""
        while self.is_running:
            try:
                await self._check_and_broadcast()
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in telemetry broadcast loop",
                    error=str(e),
                    exc_info=True,
                )
                await asyncio.sleep(self.poll_interval)

    async def _check_and_broadcast(self):
        """Check for new telemetry and broadcast updates"""
        # Get database session
        async for db in get_db():
            try:
                # Check if there are any active WebSocket connections
                if ws_manager.get_connection_count() == 0:
                    return

                # Get recent telemetry (last 30 seconds)
                cutoff_time = datetime.utcnow()

                # Query latest telemetry for each subscribed battery
                # For now, we'll query all batteries with recent updates
                result = await db.execute(
                    select(Telemetry)
                    .where(Telemetry.timestamp >= self._get_last_check_time())
                    .order_by(desc(Telemetry.timestamp))
                    .limit(1000)  # Limit to prevent overload
                )
                telemetry_records = result.scalars().all()

                if not telemetry_records:
                    return

                # Broadcast each telemetry update
                for telemetry in telemetry_records:
                    await self._broadcast_telemetry(telemetry)

                # Update last check time
                self._update_last_check_time()

            except Exception as e:
                logger.error(
                    "Error checking/broadcasting telemetry",
                    error=str(e),
                )
            finally:
                await db.close()

    async def _broadcast_telemetry(self, telemetry: Telemetry):
        """
        Broadcast single telemetry record

        Args:
            telemetry: Telemetry record to broadcast
        """
        try:
            telemetry_data = {
                'timestamp': telemetry.timestamp.isoformat(),
                'voltage': telemetry.voltage,
                'current': telemetry.current,
                'temperature': telemetry.temperature,
                'internal_resistance': telemetry.internal_resistance,
                'soc_pct': telemetry.soc_pct,
                'soh_pct': telemetry.soh_pct,
            }

            # Broadcast to WebSocket clients
            await ws_manager.broadcast_telemetry(
                battery_id=telemetry.battery_id,
                telemetry_data=telemetry_data,
            )

            # Check if battery status changed
            status = calculate_battery_status(telemetry)
            if status in ['warning', 'critical']:
                await self._broadcast_status_change(
                    telemetry.battery_id,
                    status,
                    telemetry,
                )

        except Exception as e:
            logger.error(
                "Error broadcasting telemetry",
                error=str(e),
                battery_id=telemetry.battery_id,
            )

    async def _broadcast_status_change(
        self,
        battery_id: str,
        status: str,
        telemetry: Telemetry,
    ):
        """
        Broadcast battery status change

        Args:
            battery_id: Battery identifier
            status: New status (warning, critical)
            telemetry: Latest telemetry data
        """
        try:
            status_data = {
                'status': status,
                'soh_pct': telemetry.soh_pct,
                'voltage': telemetry.voltage,
                'temperature': telemetry.temperature,
            }

            await ws_manager.broadcast_battery_status(
                battery_id=battery_id,
                status_data=status_data,
            )

        except Exception as e:
            logger.error(
                "Error broadcasting status change",
                error=str(e),
                battery_id=battery_id,
            )

    def _get_last_check_time(self) -> datetime:
        """Get timestamp of last check (default: 30 seconds ago)"""
        from datetime import timedelta
        return datetime.utcnow() - timedelta(seconds=30)

    def _update_last_check_time(self):
        """Update last check timestamp"""
        self.last_check_time = datetime.utcnow()

    async def broadcast_alert_created(self, alert_data: Dict[str, Any]):
        """
        Broadcast when new alert is created

        Args:
            alert_data: Alert data dict
        """
        try:
            await ws_manager.broadcast_alert(alert_data)

            logger.info(
                "Alert broadcasted",
                alert_id=alert_data.get('alert_id'),
                battery_id=alert_data.get('battery_id'),
                severity=alert_data.get('severity'),
            )

        except Exception as e:
            logger.error("Error broadcasting alert", error=str(e))


# Global telemetry broadcaster instance
telemetry_broadcaster = TelemetryBroadcaster(poll_interval=5.0)
