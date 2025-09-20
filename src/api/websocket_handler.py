"""
WebSocket Handler for Real-time Loan Status Updates

Provides WebSocket endpoints for real-time loan status updates, notifications,
and system events. Supports authenticated connections, subscription management,
and efficient message broadcasting.

Features:
- Real-time loan status updates
- User-specific notifications
- Event filtering and subscription management
- Authentication and authorization
- Connection health monitoring
- Message queuing for offline users
- Performance metrics and monitoring
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Enums and Models

class MessageType(str, Enum):
    """WebSocket message types"""
    LOAN_STATUS_UPDATE = "loan_status_update"
    PAYMENT_REMINDER = "payment_reminder"
    COLLATERAL_ALERT = "collateral_alert"
    SYSTEM_NOTIFICATION = "system_notification"
    RATE_CHANGE = "rate_change"
    APPROVAL_DECISION = "approval_decision"
    EXECUTION_UPDATE = "execution_update"
    ERROR_NOTIFICATION = "error_notification"

class SubscriptionFilter(BaseModel):
    """Subscription filter configuration"""
    loan_ids: Optional[List[str]] = Field(None, description="Filter by specific loan IDs")
    message_types: Optional[List[MessageType]] = Field(None, description="Filter by message types")
    borrower_address: Optional[str] = Field(None, description="Filter by borrower address")
    severity_levels: Optional[List[str]] = Field(None, description="Filter by severity levels")

class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: Optional[str] = None
    loan_id: Optional[str] = None
    priority: int = Field(default=1, description="Message priority (1=low, 5=high)")

class LoanStatusUpdate(BaseModel):
    """Loan status update message"""
    loan_id: str
    status: str
    previous_status: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    next_actions: Optional[List[str]] = None

class ConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: str
    user_id: str
    connected_at: str
    last_activity: str
    subscription_filters: SubscriptionFilter
    messages_sent: int = 0
    messages_failed: int = 0

# WebSocket Connection Management

@dataclass
class WebSocketConnection:
    """Individual WebSocket connection"""
    websocket: WebSocket
    connection_id: str
    user_id: str
    connected_at: float
    last_activity: float
    subscription_filters: SubscriptionFilter
    is_active: bool = True
    messages_sent: int = 0
    messages_failed: int = 0
    message_queue: List[WebSocketMessage] = None

    def __post_init__(self):
        if self.message_queue is None:
            self.message_queue = []

    async def send_message(self, message: WebSocketMessage) -> bool:
        """Send message to WebSocket client"""
        if not self.is_active:
            return False

        try:
            # Check if message matches subscription filters
            if not self._matches_filters(message):
                return False

            message_data = {
                "id": message.id,
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp,
                "priority": message.priority
            }

            await self.websocket.send_text(json.dumps(message_data))
            self.messages_sent += 1
            self.last_activity = time.time()
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            self.messages_failed += 1
            self.is_active = False
            return False

    def _matches_filters(self, message: WebSocketMessage) -> bool:
        """Check if message matches subscription filters"""
        filters = self.subscription_filters

        # Filter by loan IDs
        if filters.loan_ids and message.loan_id not in filters.loan_ids:
            return False

        # Filter by message types
        if filters.message_types and message.type not in filters.message_types:
            return False

        # Filter by user (always allow user's own messages)
        if message.user_id and message.user_id != self.user_id:
            # Check if this is a system message or user has permission
            if message.type not in [MessageType.SYSTEM_NOTIFICATION, MessageType.RATE_CHANGE]:
                return False

        return True

    async def queue_message(self, message: WebSocketMessage):
        """Queue message for later delivery"""
        if len(self.message_queue) < 100:  # Limit queue size
            self.message_queue.append(message)
        else:
            # Remove oldest message
            self.message_queue.pop(0)
            self.message_queue.append(message)

    async def flush_queued_messages(self):
        """Send all queued messages"""
        while self.message_queue and self.is_active:
            message = self.message_queue.pop(0)
            await self.send_message(message)

    async def ping(self):
        """Send ping to maintain connection"""
        try:
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connection_id": self.connection_id
            }
            await self.websocket.send_text(json.dumps(ping_message))
            self.last_activity = time.time()
            return True
        except Exception:
            self.is_active = False
            return False

class WebSocketManager:
    """Manages all WebSocket connections and message broadcasting"""

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.loan_subscribers: Dict[str, Set[str]] = {}  # loan_id -> connection_ids
        self._lock = asyncio.Lock()
        self.redis_client: Optional[redis.Redis] = None
        self.router = APIRouter(prefix="/ws", tags=["WebSocket"])
        self._setup_routes()

    async def initialize(self):
        """Initialize WebSocket manager"""
        try:
            # Initialize Redis for message persistence (optional)
            try:
                self.redis_client = redis.from_url("redis://localhost:6379")
                await self.redis_client.ping()
                logger.info("WebSocket manager: Redis connected for message persistence")
            except Exception as e:
                logger.warning(f"WebSocket manager: Redis not available: {e}")
                self.redis_client = None

            # Start background tasks
            asyncio.create_task(self._connection_monitor())
            asyncio.create_task(self._message_processor())

            logger.info("WebSocket manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            raise

    def _setup_routes(self):
        """Setup WebSocket routes"""

        @self.router.websocket("/loan-updates/{connection_id}")
        async def websocket_endpoint(websocket: WebSocket, connection_id: str, token: str = Query(...)):
            await self._handle_websocket_connection(websocket, connection_id, token)

        @self.router.get("/connections")
        async def get_connections():
            return await self.get_connection_stats()

        @self.router.post("/broadcast/{user_id}")
        async def broadcast_to_user(user_id: str, message: Dict[str, Any]):
            return await self.broadcast_to_user(user_id, message)

    async def _handle_websocket_connection(self, websocket: WebSocket, connection_id: str, token: str):
        """Handle new WebSocket connection"""
        try:
            # Authenticate user (simplified - use proper JWT in production)
            user_info = await self._authenticate_token(token)
            if not user_info:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return

            # Accept connection
            await websocket.accept()

            # Create connection object
            connection = WebSocketConnection(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user_info["user_id"],
                connected_at=time.time(),
                last_activity=time.time(),
                subscription_filters=SubscriptionFilter()
            )

            # Register connection
            await self._register_connection(connection)

            # Send welcome message
            welcome_message = WebSocketMessage(
                type=MessageType.SYSTEM_NOTIFICATION,
                data={
                    "message": "Connected to loan updates service",
                    "connection_id": connection_id,
                    "features": ["loan_status_updates", "payment_reminders", "collateral_alerts"]
                },
                user_id=user_info["user_id"]
            )
            await connection.send_message(welcome_message)

            # Send any queued messages
            await connection.flush_queued_messages()

            # Handle incoming messages
            try:
                while connection.is_active:
                    data = await websocket.receive_text()
                    await self._process_client_message(connection, data)

            except WebSocketDisconnect:
                logger.info(f"WebSocket {connection_id} disconnected normally")
            except Exception as e:
                logger.error(f"WebSocket {connection_id} error: {e}")

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            await self._unregister_connection(connection_id)

    async def _authenticate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate WebSocket token"""
        try:
            # TODO: Implement proper JWT validation
            # For now, return mock user data
            return {
                "user_id": f"user_{token[:8]}",
                "email": f"user_{token[:8]}@example.com",
                "permissions": ["read", "write"]
            }
        except Exception as e:
            logger.error(f"Token authentication failed: {e}")
            return None

    async def _register_connection(self, connection: WebSocketConnection):
        """Register new WebSocket connection"""
        async with self._lock:
            self.connections[connection.connection_id] = connection

            # Add to user connections
            if connection.user_id not in self.user_connections:
                self.user_connections[connection.user_id] = set()
            self.user_connections[connection.user_id].add(connection.connection_id)

            logger.info(
                f"WebSocket connection {connection.connection_id} registered for user {connection.user_id}"
            )

    async def _unregister_connection(self, connection_id: str):
        """Unregister WebSocket connection"""
        async with self._lock:
            if connection_id not in self.connections:
                return

            connection = self.connections[connection_id]
            user_id = connection.user_id

            # Remove from connections
            del self.connections[connection_id]

            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from loan subscribers
            for loan_id, subscribers in self.loan_subscribers.items():
                subscribers.discard(connection_id)

            logger.info(f"WebSocket connection {connection_id} unregistered")

    async def _process_client_message(self, connection: WebSocketConnection, data: str):
        """Process message from WebSocket client"""
        try:
            message = json.loads(data)
            message_type = message.get("type")

            if message_type == "subscribe":
                # Update subscription filters
                filters_data = message.get("filters", {})
                connection.subscription_filters = SubscriptionFilter(**filters_data)

                # Subscribe to specific loans
                if filters_data.get("loan_ids"):
                    for loan_id in filters_data["loan_ids"]:
                        if loan_id not in self.loan_subscribers:
                            self.loan_subscribers[loan_id] = set()
                        self.loan_subscribers[loan_id].add(connection.connection_id)

                await connection.send_message(WebSocketMessage(
                    type=MessageType.SYSTEM_NOTIFICATION,
                    data={"message": "Subscription updated", "filters": filters_data}
                ))

            elif message_type == "pong":
                # Handle pong response
                connection.last_activity = time.time()

            elif message_type == "get_status":
                # Send connection status
                await connection.send_message(WebSocketMessage(
                    type=MessageType.SYSTEM_NOTIFICATION,
                    data={
                        "connection_id": connection.connection_id,
                        "connected_at": connection.connected_at,
                        "messages_sent": connection.messages_sent,
                        "messages_failed": connection.messages_failed,
                        "subscription_filters": connection.subscription_filters.dict()
                    }
                ))

        except json.JSONDecodeError:
            await connection.send_message(WebSocketMessage(
                type=MessageType.ERROR_NOTIFICATION,
                data={"error": "Invalid JSON message"}
            ))
        except Exception as e:
            logger.error(f"Error processing client message: {e}")
            await connection.send_message(WebSocketMessage(
                type=MessageType.ERROR_NOTIFICATION,
                data={"error": "Failed to process message"}
            ))

    async def broadcast_loan_update(self, loan_update: LoanStatusUpdate):
        """Broadcast loan status update to relevant subscribers"""
        message = WebSocketMessage(
            type=MessageType.LOAN_STATUS_UPDATE,
            data=loan_update.dict(),
            loan_id=loan_update.loan_id,
            priority=3
        )

        # Get subscribers for this loan
        subscribers = self.loan_subscribers.get(loan_update.loan_id, set())

        # Also include users who have general subscriptions
        for connection_id, connection in self.connections.items():
            if (connection_id not in subscribers and
                (not connection.subscription_filters.loan_ids or
                 loan_update.loan_id in connection.subscription_filters.loan_ids)):
                subscribers.add(connection_id)

        # Send to all subscribers
        for connection_id in subscribers:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_active:
                    await connection.send_message(message)
                else:
                    await connection.queue_message(message)

        logger.info(f"Broadcasted loan update for {loan_update.loan_id} to {len(subscribers)} subscribers")

    async def broadcast_to_user(self, user_id: str, message_data: Dict[str, Any]) -> bool:
        """Broadcast message to all connections for a specific user"""
        if user_id not in self.user_connections:
            return False

        message = WebSocketMessage(
            type=MessageType.SYSTEM_NOTIFICATION,
            data=message_data,
            user_id=user_id
        )

        connection_ids = self.user_connections[user_id].copy()
        sent_count = 0

        for connection_id in connection_ids:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if await connection.send_message(message):
                    sent_count += 1

        logger.info(f"Broadcasted message to user {user_id}: {sent_count}/{len(connection_ids)} connections")
        return sent_count > 0

    async def notify_payment_reminder(self, loan_id: str, borrower_address: str, amount: int, due_date: str):
        """Send payment reminder notification"""
        message = WebSocketMessage(
            type=MessageType.PAYMENT_REMINDER,
            data={
                "loan_id": loan_id,
                "amount_micro_algos": amount,
                "due_date": due_date,
                "message": f"Payment of {amount/1000000:.2f} ALGO due on {due_date}"
            },
            loan_id=loan_id,
            priority=4
        )

        # Send to relevant users
        subscribers = self.loan_subscribers.get(loan_id, set())
        for connection_id in subscribers:
            if connection_id in self.connections:
                await self.connections[connection_id].send_message(message)

    async def notify_collateral_alert(self, loan_id: str, alert_type: str, details: Dict[str, Any]):
        """Send collateral alert notification"""
        message = WebSocketMessage(
            type=MessageType.COLLATERAL_ALERT,
            data={
                "loan_id": loan_id,
                "alert_type": alert_type,
                "details": details,
                "severity": "high" if alert_type == "liquidation_risk" else "medium"
            },
            loan_id=loan_id,
            priority=5  # High priority for collateral alerts
        )

        # Send to relevant users
        subscribers = self.loan_subscribers.get(loan_id, set())
        for connection_id in subscribers:
            if connection_id in self.connections:
                await self.connections[connection_id].send_message(message)

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        async with self._lock:
            total_connections = len(self.connections)
            active_connections = sum(1 for conn in self.connections.values() if conn.is_active)
            unique_users = len(self.user_connections)

            return {
                "total_connections": total_connections,
                "active_connections": active_connections,
                "unique_users": unique_users,
                "loan_subscriptions": len(self.loan_subscribers),
                "connections_per_user": {
                    user_id: len(connection_ids)
                    for user_id, connection_ids in self.user_connections.items()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _connection_monitor(self):
        """Background task to monitor connection health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                current_time = time.time()
                inactive_connections = []

                for connection_id, connection in self.connections.items():
                    # Check for inactive connections (no activity in 5 minutes)
                    if current_time - connection.last_activity > 300:
                        inactive_connections.append(connection_id)
                        continue

                    # Send ping to active connections every 2 minutes
                    if current_time - connection.last_activity > 120:
                        if not await connection.ping():
                            inactive_connections.append(connection_id)

                # Clean up inactive connections
                for connection_id in inactive_connections:
                    await self._unregister_connection(connection_id)

                if inactive_connections:
                    logger.info(f"Cleaned up {len(inactive_connections)} inactive WebSocket connections")

            except Exception as e:
                logger.error(f"Error in WebSocket connection monitoring: {e}")

    async def _message_processor(self):
        """Background task to process queued messages"""
        while True:
            try:
                await asyncio.sleep(10)  # Process every 10 seconds

                for connection in self.connections.values():
                    if connection.is_active and connection.message_queue:
                        await connection.flush_queued_messages()

            except Exception as e:
                logger.error(f"Error in WebSocket message processing: {e}")

    async def shutdown(self):
        """Shutdown WebSocket manager"""
        try:
            # Close all connections
            for connection in self.connections.values():
                try:
                    await connection.websocket.close()
                except Exception:
                    pass

            # Clear connections
            self.connections.clear()
            self.user_connections.clear()
            self.loan_subscribers.clear()

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            logger.info("WebSocket manager shutdown completed")

        except Exception as e:
            logger.error(f"Error during WebSocket manager shutdown: {e}")