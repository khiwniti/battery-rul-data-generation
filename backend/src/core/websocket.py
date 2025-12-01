"""
WebSocket Manager
Real-time communication using Socket.IO for telemetry updates and alerts
"""
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
import socketio
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import logger
from ..core.security import verify_token
from ..models.user import User


class WebSocketManager:
    """
    WebSocket connection manager using Socket.IO

    Handles:
    - Client authentication via JWT tokens
    - Room-based subscriptions (locations, batteries)
    - Real-time telemetry broadcasting
    - Alert notifications
    - Connection lifecycle management
    """

    def __init__(self):
        """Initialize Socket.IO async server"""
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',  # Configure in production
            logger=False,
            engineio_logger=False,
        )

        # Track subscriptions: {sid: {user_id, location_ids, battery_ids}}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

        # Setup event handlers
        self._setup_handlers()

        logger.info("WebSocket manager initialized")

    def _setup_handlers(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        async def connect(sid: str, environ: dict, auth: dict):
            """Handle client connection with JWT authentication"""
            try:
                # Extract token from auth
                token = auth.get('token') if auth else None

                if not token:
                    logger.warning("WebSocket connection rejected: No token", sid=sid)
                    return False

                # Verify JWT token
                user_id = verify_token(token)

                if not user_id:
                    logger.warning("WebSocket connection rejected: Invalid token", sid=sid)
                    return False

                # Store subscription info
                self.subscriptions[sid] = {
                    'user_id': user_id,
                    'location_ids': set(),
                    'battery_ids': set(),
                    'connected_at': datetime.utcnow(),
                }

                logger.info(
                    "WebSocket client connected",
                    sid=sid,
                    user_id=user_id,
                    total_connections=len(self.subscriptions),
                )

                # Send welcome message
                await self.sio.emit('connected', {
                    'message': 'Connected to Battery RUL Monitoring',
                    'timestamp': datetime.utcnow().isoformat(),
                }, room=sid)

                return True

            except Exception as e:
                logger.error("WebSocket connection error", error=str(e), sid=sid)
                return False

        @self.sio.event
        async def disconnect(sid: str):
            """Handle client disconnection"""
            subscription = self.subscriptions.pop(sid, None)

            if subscription:
                # Leave all rooms
                for location_id in subscription.get('location_ids', set()):
                    await self.sio.leave_room(sid, f"location:{location_id}")

                for battery_id in subscription.get('battery_ids', set()):
                    await self.sio.leave_room(sid, f"battery:{battery_id}")

                logger.info(
                    "WebSocket client disconnected",
                    sid=sid,
                    user_id=subscription.get('user_id'),
                    total_connections=len(self.subscriptions),
                )

        @self.sio.event
        async def subscribe_location(sid: str, data: dict):
            """Subscribe to location updates"""
            try:
                location_id = data.get('location_id')

                if not location_id:
                    await self.sio.emit('error', {
                        'message': 'location_id required'
                    }, room=sid)
                    return

                # Join location room
                room = f"location:{location_id}"
                await self.sio.enter_room(sid, room)

                # Track subscription
                if sid in self.subscriptions:
                    self.subscriptions[sid]['location_ids'].add(location_id)

                logger.info(
                    "Client subscribed to location",
                    sid=sid,
                    location_id=location_id,
                    user_id=self.subscriptions.get(sid, {}).get('user_id'),
                )

                await self.sio.emit('subscribed', {
                    'type': 'location',
                    'location_id': location_id,
                    'timestamp': datetime.utcnow().isoformat(),
                }, room=sid)

            except Exception as e:
                logger.error("Subscribe location error", error=str(e), sid=sid)
                await self.sio.emit('error', {'message': str(e)}, room=sid)

        @self.sio.event
        async def unsubscribe_location(sid: str, data: dict):
            """Unsubscribe from location updates"""
            try:
                location_id = data.get('location_id')

                if not location_id:
                    return

                # Leave location room
                room = f"location:{location_id}"
                await self.sio.leave_room(sid, room)

                # Update subscription tracking
                if sid in self.subscriptions:
                    self.subscriptions[sid]['location_ids'].discard(location_id)

                logger.info(
                    "Client unsubscribed from location",
                    sid=sid,
                    location_id=location_id,
                )

            except Exception as e:
                logger.error("Unsubscribe location error", error=str(e), sid=sid)

        @self.sio.event
        async def subscribe_battery(sid: str, data: dict):
            """Subscribe to battery updates"""
            try:
                battery_id = data.get('battery_id')

                if not battery_id:
                    await self.sio.emit('error', {
                        'message': 'battery_id required'
                    }, room=sid)
                    return

                # Join battery room
                room = f"battery:{battery_id}"
                await self.sio.enter_room(sid, room)

                # Track subscription
                if sid in self.subscriptions:
                    self.subscriptions[sid]['battery_ids'].add(battery_id)

                logger.info(
                    "Client subscribed to battery",
                    sid=sid,
                    battery_id=battery_id,
                    user_id=self.subscriptions.get(sid, {}).get('user_id'),
                )

                await self.sio.emit('subscribed', {
                    'type': 'battery',
                    'battery_id': battery_id,
                    'timestamp': datetime.utcnow().isoformat(),
                }, room=sid)

            except Exception as e:
                logger.error("Subscribe battery error", error=str(e), sid=sid)
                await self.sio.emit('error', {'message': str(e)}, room=sid)

        @self.sio.event
        async def unsubscribe_battery(sid: str, data: dict):
            """Unsubscribe from battery updates"""
            try:
                battery_id = data.get('battery_id')

                if not battery_id:
                    return

                # Leave battery room
                room = f"battery:{battery_id}"
                await self.sio.leave_room(sid, room)

                # Update subscription tracking
                if sid in self.subscriptions:
                    self.subscriptions[sid]['battery_ids'].discard(battery_id)

                logger.info(
                    "Client unsubscribed from battery",
                    sid=sid,
                    battery_id=battery_id,
                )

            except Exception as e:
                logger.error("Unsubscribe battery error", error=str(e), sid=sid)

        @self.sio.event
        async def ping(sid: str, data: dict):
            """Heartbeat/keepalive"""
            await self.sio.emit('pong', {
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)

    async def broadcast_telemetry(self, battery_id: str, telemetry_data: dict):
        """
        Broadcast telemetry update to subscribed clients

        Args:
            battery_id: Battery identifier
            telemetry_data: Telemetry data dict
        """
        try:
            # Broadcast to battery-specific room
            battery_room = f"battery:{battery_id}"
            await self.sio.emit('telemetry_update', {
                'battery_id': battery_id,
                'data': telemetry_data,
                'timestamp': datetime.utcnow().isoformat(),
            }, room=battery_room)

            # TODO: Also broadcast to location room if battery location is known

        except Exception as e:
            logger.error(
                "Failed to broadcast telemetry",
                error=str(e),
                battery_id=battery_id,
            )

    async def broadcast_alert(self, alert_data: dict):
        """
        Broadcast alert to subscribed clients

        Args:
            alert_data: Alert data dict with battery_id, location_id, severity, message
        """
        try:
            battery_id = alert_data.get('battery_id')
            location_id = alert_data.get('location_id')

            # Broadcast to battery room
            if battery_id:
                battery_room = f"battery:{battery_id}"
                await self.sio.emit('alert', alert_data, room=battery_room)

            # Broadcast to location room
            if location_id:
                location_room = f"location:{location_id}"
                await self.sio.emit('alert', alert_data, room=location_room)

            # Broadcast to global alerts room (all connected clients)
            await self.sio.emit('alert', alert_data)

            logger.info(
                "Alert broadcasted",
                battery_id=battery_id,
                location_id=location_id,
                severity=alert_data.get('severity'),
            )

        except Exception as e:
            logger.error("Failed to broadcast alert", error=str(e))

    async def broadcast_battery_status(self, battery_id: str, status_data: dict):
        """
        Broadcast battery status change

        Args:
            battery_id: Battery identifier
            status_data: Status data dict (status, soh_pct, etc.)
        """
        try:
            battery_room = f"battery:{battery_id}"
            await self.sio.emit('battery_status_update', {
                'battery_id': battery_id,
                'data': status_data,
                'timestamp': datetime.utcnow().isoformat(),
            }, room=battery_room)

        except Exception as e:
            logger.error(
                "Failed to broadcast battery status",
                error=str(e),
                battery_id=battery_id,
            )

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.subscriptions)

    def get_room_subscribers(self, room: str) -> int:
        """Get number of subscribers to a room"""
        # Socket.IO doesn't provide direct room subscriber count
        # We track this manually in subscriptions
        count = 0
        room_type, room_id = room.split(':', 1) if ':' in room else ('', '')

        for subscription in self.subscriptions.values():
            if room_type == 'location' and room_id in subscription.get('location_ids', set()):
                count += 1
            elif room_type == 'battery' and room_id in subscription.get('battery_ids', set()):
                count += 1

        return count


# Global WebSocket manager instance
ws_manager = WebSocketManager()
