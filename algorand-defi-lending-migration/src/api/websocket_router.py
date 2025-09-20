"""
WebSocket Router for Real-time Event Streaming

Provides WebSocket endpoints for real-time audit event streaming, enabling
UI updates, monitoring dashboards, and real-time analytics.

Features:
- WebSocket connections with automatic reconnection support
- Event filtering and subscription management
- Authentication and authorization
- Connection health monitoring
- Performance metrics
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
import uuid
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from .auth import get_current_user, AuthHandler
from ..core.audit.event_streaming import (
    get_event_streaming_service,
    EventStreamingService,
    StreamingEvent,
    EventPriority,
    subscribe_to_events,
    unsubscribe_from_events,
    get_streaming_metrics
)
from ..core.audit.models import AuditTrail, AuditEventType, AuditSeverity


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["Event Streaming"])
security = HTTPBearer()


class WebSocketConnection:
    """Manages individual WebSocket connections"""

    def __init__(self, websocket: WebSocket, connection_id: str, user_info: Dict[str, Any]):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_info = user_info
        self.created_at = time.time()
        self.last_ping = time.time()
        self.is_active = True
        self.subscription_filters: Dict[str, Any] = {}
        self.events_sent = 0
        self.events_failed = 0

    async def send_event(self, event: StreamingEvent):
        """Send event to WebSocket client"""
        try:
            # Convert event to JSON-serializable format
            event_data = {
                "id": event.id,
                "event_type": event.event.event_type.value,
                "severity": event.event.severity.value,
                "timestamp": event.event.timestamp.isoformat(),
                "service_name": event.event.service_name,
                "event_data": event.event.event_data.dict(exclude_none=True),
                "correlation_id": event.event.correlation_id,
                "trace_id": event.event.trace_id,
                "priority": event.priority.value if event.priority else 2
            }

            message = {
                "type": "event",
                "data": event_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.websocket.send_text(json.dumps(message))
            self.events_sent += 1

        except Exception as e:
            logger.error(f"Failed to send event to connection {self.connection_id}: {e}")
            self.events_failed += 1
            self.is_active = False
            raise

    async def send_message(self, message_type: str, data: Any):
        """Send a control message to WebSocket client"""
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.websocket.send_text(json.dumps(message))

        except Exception as e:
            logger.error(f"Failed to send {message_type} to connection {self.connection_id}: {e}")
            self.is_active = False
            raise

    async def ping(self):
        """Send ping to client"""
        await self.send_message("ping", {"connection_id": self.connection_id})
        self.last_ping = time.time()

    def update_filters(self, filters: Dict[str, Any]):
        """Update subscription filters"""
        self.subscription_filters = filters


class WebSocketManager:
    """Manages all WebSocket connections"""

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, connection_id: str, user_info: Dict[str, Any]) -> WebSocketConnection:
        """Accept new WebSocket connection"""
        await websocket.accept()

        connection = WebSocketConnection(websocket, connection_id, user_info)

        async with self._lock:
            self.connections[connection_id] = connection

            user_id = user_info.get('user_id', 'anonymous')
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

        logger.info(f"WebSocket connection {connection_id} established for user {user_id}")
        return connection

    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        async with self._lock:
            if connection_id not in self.connections:
                return

            connection = self.connections[connection_id]
            user_id = connection.user_info.get('user_id', 'anonymous')

            # Remove connection
            del self.connections[connection_id]

            # Update user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

        # Unsubscribe from event stream
        await unsubscribe_from_events(connection_id)

        logger.info(f"WebSocket connection {connection_id} disconnected")

    async def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    async def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """Get all connections for a user"""
        async with self._lock:
            connection_ids = self.user_connections.get(user_id, set())
            return [self.connections[conn_id] for conn_id in connection_ids if conn_id in self.connections]

    async def broadcast_to_user(self, user_id: str, message_type: str, data: Any):
        """Broadcast message to all connections for a user"""
        connections = await self.get_user_connections(user_id)
        for connection in connections:
            if connection.is_active:
                try:
                    await connection.send_message(message_type, data)
                except Exception:
                    # Connection will be marked as inactive
                    pass

    async def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        async with self._lock:
            total_connections = len(self.connections)
            active_connections = sum(1 for conn in self.connections.values() if conn.is_active)
            unique_users = len(self.user_connections)

            return {
                "total_connections": total_connections,
                "active_connections": active_connections,
                "unique_users": unique_users,
                "connections_per_user": {
                    user_id: len(connection_ids)
                    for user_id, connection_ids in self.user_connections.items()
                }
            }


# Global WebSocket manager
ws_manager = WebSocketManager()


# Pydantic models for API

class EventSubscriptionRequest(BaseModel):
    """Request model for event subscription"""
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    min_severity: Optional[str] = Field("info", description="Minimum severity level")
    loan_ids: Optional[List[str]] = Field(None, description="Filter by specific loan IDs")
    services: Optional[List[str]] = Field(None, description="Filter by service names")
    include_historical: bool = Field(False, description="Include historical events")

    @validator('event_types')
    def validate_event_types(cls, v):
        if v is not None:
            valid_types = [e.value for e in AuditEventType]
            invalid_types = [t for t in v if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid event types: {invalid_types}")
        return v

    @validator('min_severity')
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = [s.value for s in AuditSeverity]
            if v not in valid_severities:
                raise ValueError(f"Invalid severity: {v}. Valid options: {valid_severities}")
        return v


class StreamingMetricsResponse(BaseModel):
    """Response model for streaming metrics"""
    events_per_second: float
    dropped_events_per_second: float
    average_processing_time_ms: float
    max_processing_time_ms: float
    active_connections: int
    active_subscribers: int
    queue_size: int
    pending_events: int
    timestamp: float


# WebSocket endpoint

@router.websocket("/stream/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    """WebSocket endpoint for real-time event streaming"""

    # Authenticate the WebSocket connection
    # Note: WebSocket auth is challenging, so we'll use a simple token approach
    try:
        # Get token from query parameters or headers
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
            return

        # Validate token (simplified - in production, use proper JWT validation)
        auth_handler = AuthHandler()
        user_info = await auth_handler.validate_token_simple(token)

        if not user_info:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
            return

    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return

    # Establish connection
    try:
        connection = await ws_manager.connect(websocket, connection_id, user_info)

        # Send welcome message
        await connection.send_message("connected", {
            "connection_id": connection_id,
            "user_id": user_info.get("user_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Handle incoming messages
        async def handle_messages():
            """Handle incoming WebSocket messages"""
            try:
                while connection.is_active:
                    message = await websocket.receive_text()
                    await process_websocket_message(connection, message)
            except WebSocketDisconnect:
                logger.info(f"WebSocket {connection_id} disconnected normally")
            except Exception as e:
                logger.error(f"WebSocket {connection_id} error: {e}")
            finally:
                await ws_manager.disconnect(connection_id)

        # Start message handling
        await handle_messages()

    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await ws_manager.disconnect(connection_id)


async def process_websocket_message(connection: WebSocketConnection, message: str):
    """Process incoming WebSocket message"""
    try:
        data = json.loads(message)
        message_type = data.get("type")

        if message_type == "subscribe":
            # Handle subscription request
            filters = data.get("filters", {})
            await handle_subscription(connection, filters)

        elif message_type == "unsubscribe":
            # Handle unsubscription
            await unsubscribe_from_events(connection.connection_id)
            await connection.send_message("unsubscribed", {"connection_id": connection.connection_id})

        elif message_type == "pong":
            # Handle pong response
            connection.last_ping = time.time()

        elif message_type == "get_metrics":
            # Send current metrics
            metrics = await get_streaming_metrics()
            await connection.send_message("metrics", metrics)

        else:
            await connection.send_message("error", {"message": f"Unknown message type: {message_type}"})

    except json.JSONDecodeError:
        await connection.send_message("error", {"message": "Invalid JSON message"})
    except Exception as e:
        logger.error(f"Error processing WebSocket message: {e}")
        await connection.send_message("error", {"message": "Failed to process message"})


async def handle_subscription(connection: WebSocketConnection, filters: Dict[str, Any]):
    """Handle event subscription for WebSocket connection"""
    try:
        # Create event callback for this connection
        async def event_callback(event: StreamingEvent):
            if connection.is_active:
                await connection.send_event(event)

        # Subscribe to event stream
        success = await subscribe_to_events(
            connection.connection_id,
            event_callback,
            event_types=filters.get("event_types"),
            min_severity=filters.get("min_severity", "info"),
            loan_ids=filters.get("loan_ids"),
            services=filters.get("services")
        )

        if success:
            connection.update_filters(filters)
            await connection.send_message("subscribed", {
                "connection_id": connection.connection_id,
                "filters": filters
            })
        else:
            await connection.send_message("error", {"message": "Failed to subscribe to events"})

    except Exception as e:
        logger.error(f"Failed to handle subscription: {e}")
        await connection.send_message("error", {"message": "Subscription failed"})


# REST API endpoints for managing streaming

@router.get("/metrics", response_model=StreamingMetricsResponse)
async def get_streaming_metrics_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current streaming system metrics"""
    try:
        metrics = await get_streaming_metrics()
        return StreamingMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Failed to get streaming metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.get("/connections")
async def get_connection_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get WebSocket connection statistics"""
    try:
        return await ws_manager.get_stats()
    except Exception as e:
        logger.error(f"Failed to get connection stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection stats")


@router.post("/broadcast/{user_id}")
async def broadcast_to_user(
    user_id: str,
    message_type: str,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Broadcast message to all connections for a specific user"""
    try:
        # Check if current user has permission to broadcast to target user
        if current_user.get("user_id") != user_id and not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Not authorized to broadcast to this user")

        await ws_manager.broadcast_to_user(user_id, message_type, data)
        return {"success": True, "message": f"Broadcasted to user {user_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to broadcast to user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


@router.post("/test-event")
async def send_test_event(
    event_type: str = "system_test",
    severity: str = "info",
    loan_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Send a test event for testing purposes"""
    try:
        from ..core.audit.models import create_loan_audit_event, AuditEventType, AuditSeverity
        from ..core.audit.event_streaming import stream_audit_event, EventPriority

        # Create test audit event
        test_event = create_loan_audit_event(
            event_type=AuditEventType.SYSTEM_ERROR,  # Use a generic event type
            loan_id=loan_id or "test-loan-123",
            borrower_address=current_user.get("algorand_address", "test-address"),
            service_name="websocket_test",
            amount_micro_algos=1000000,
            metadata={
                "test": True,
                "user_id": current_user.get("user_id"),
                "message": "This is a test event for WebSocket streaming"
            }
        )

        # Set severity
        test_event.severity = AuditSeverity(severity)

        # Stream the event
        success = await stream_audit_event(test_event, EventPriority.NORMAL)

        if success:
            return {"success": True, "message": "Test event sent successfully"}
        else:
            return {"success": False, "message": "Failed to queue test event"}

    except Exception as e:
        logger.error(f"Failed to send test event: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test event")


# Background task for connection health monitoring

async def monitor_connections():
    """Monitor WebSocket connections health"""
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds

            current_time = time.time()
            inactive_connections = []

            for connection_id, connection in ws_manager.connections.items():
                # Check for inactive connections (no ping in 5 minutes)
                if current_time - connection.last_ping > 300:
                    inactive_connections.append(connection_id)
                    continue

                # Send ping to active connections
                if connection.is_active:
                    try:
                        await connection.ping()
                    except Exception:
                        inactive_connections.append(connection_id)

            # Clean up inactive connections
            for connection_id in inactive_connections:
                await ws_manager.disconnect(connection_id)

            if inactive_connections:
                logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")

        except Exception as e:
            logger.error(f"Error in connection monitoring: {e}")


# Start background monitoring when router is imported
asyncio.create_task(monitor_connections())