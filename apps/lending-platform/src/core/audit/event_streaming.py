"""
Real-time Event Streaming System for Audit Trail

High-performance event streaming infrastructure that captures, processes, and streams
audit events in real-time for compliance monitoring and analytics.

Features:
- WebSocket-based real-time streaming
- Event deduplication and ordering
- Error recovery and retry mechanisms
- Performance monitoring
- Scalable architecture with event bus
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Set, Callable, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import uuid
from enum import Enum
import weakref
import threading
from queue import Queue, Empty, Full
import hashlib

from .models import AuditTrail, AuditEventType, AuditSeverity


logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for processing"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class StreamingStatus(Enum):
    """Status of streaming connections"""
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class EventStreamConfig:
    """Configuration for event streaming system"""
    # Performance settings
    max_queue_size: int = 10000
    batch_size: int = 50
    flush_interval_ms: int = 100
    max_latency_ms: int = 50

    # Deduplication settings
    dedup_window_seconds: int = 60
    dedup_cache_size: int = 10000

    # Retry settings
    max_retries: int = 3
    retry_delay_ms: int = 1000
    retry_backoff_factor: float = 2.0

    # WebSocket settings
    max_connections: int = 1000
    heartbeat_interval_ms: int = 30000
    connection_timeout_ms: int = 60000

    # Monitoring settings
    metrics_window_seconds: int = 300
    performance_threshold_ms: int = 100


@dataclass
class StreamingEvent:
    """Wrapper for events in the streaming system"""
    id: str
    event: AuditTrail
    priority: EventPriority = EventPriority.NORMAL
    timestamp_received: float = field(default_factory=time.time)
    retry_count: int = 0
    dedupe_hash: Optional[str] = None
    subscribers: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.dedupe_hash:
            self.dedupe_hash = self._calculate_dedupe_hash()

    def _calculate_dedupe_hash(self) -> str:
        """Calculate hash for deduplication"""
        # Use event type, loan_id, timestamp, and key data fields
        hash_data = {
            'event_type': self.event.event_type.value,
            'timestamp': self.event.timestamp.isoformat(),
            'loan_id': getattr(self.event.event_data, 'loan_id', None),
            'transaction_id': getattr(self.event.event_data, 'transaction_id', None),
            'service_name': self.event.service_name,
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()


class EventDeduplicator:
    """Handles event deduplication with sliding window"""

    def __init__(self, window_seconds: int = 60, cache_size: int = 10000):
        self.window_seconds = window_seconds
        self.cache_size = cache_size
        self.seen_events: Dict[str, float] = {}
        self._lock = threading.Lock()

    def is_duplicate(self, event: StreamingEvent) -> bool:
        """Check if event is a duplicate within the time window"""
        with self._lock:
            current_time = time.time()

            # Clean up old entries
            self._cleanup_expired(current_time)

            # Check if we've seen this event hash recently
            if event.dedupe_hash in self.seen_events:
                return True

            # Add to seen events if cache has space
            if len(self.seen_events) < self.cache_size:
                self.seen_events[event.dedupe_hash] = current_time

            return False

    def _cleanup_expired(self, current_time: float):
        """Remove expired entries from cache"""
        expired_keys = [
            key for key, timestamp in self.seen_events.items()
            if current_time - timestamp > self.window_seconds
        ]
        for key in expired_keys:
            del self.seen_events[key]


class EventMetrics:
    """Real-time metrics collection for the streaming system"""

    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self.events_processed: deque = deque()
        self.events_dropped: deque = deque()
        self.processing_times: deque = deque()
        self.connection_count = 0
        self.active_subscribers: Set[str] = set()
        self._lock = threading.Lock()

    def record_event_processed(self, processing_time_ms: float):
        """Record a successfully processed event"""
        with self._lock:
            current_time = time.time()
            self.events_processed.append(current_time)
            self.processing_times.append(processing_time_ms)
            self._cleanup_old_metrics(current_time)

    def record_event_dropped(self, reason: str = "unknown"):
        """Record a dropped event"""
        with self._lock:
            current_time = time.time()
            self.events_dropped.append((current_time, reason))
            self._cleanup_old_metrics(current_time)

    def update_connection_count(self, count: int):
        """Update active connection count"""
        self.connection_count = count

    def add_subscriber(self, subscriber_id: str):
        """Add active subscriber"""
        self.active_subscribers.add(subscriber_id)

    def remove_subscriber(self, subscriber_id: str):
        """Remove subscriber"""
        self.active_subscribers.discard(subscriber_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        with self._lock:
            current_time = time.time()
            self._cleanup_old_metrics(current_time)

            return {
                'events_per_second': len(self.events_processed) / self.window_seconds,
                'dropped_events_per_second': len(self.events_dropped) / self.window_seconds,
                'average_processing_time_ms': (
                    sum(self.processing_times) / len(self.processing_times)
                    if self.processing_times else 0
                ),
                'max_processing_time_ms': max(self.processing_times) if self.processing_times else 0,
                'active_connections': self.connection_count,
                'active_subscribers': len(self.active_subscribers),
                'window_seconds': self.window_seconds,
                'timestamp': current_time
            }

    def _cleanup_old_metrics(self, current_time: float):
        """Remove metrics outside the time window"""
        cutoff_time = current_time - self.window_seconds

        # Clean up events processed
        while self.events_processed and self.events_processed[0] < cutoff_time:
            self.events_processed.popleft()

        # Clean up events dropped
        while self.events_dropped and self.events_dropped[0][0] < cutoff_time:
            self.events_dropped.popleft()

        # Keep only recent processing times (approximate cleanup)
        if len(self.processing_times) > 10000:
            self.processing_times = deque(list(self.processing_times)[-5000:])


class EventSubscriber:
    """Represents a subscriber to the event stream"""

    def __init__(self, subscriber_id: str, callback: Callable, filters: Optional[Dict[str, Any]] = None):
        self.subscriber_id = subscriber_id
        self.callback = callback
        self.filters = filters or {}
        self.created_at = time.time()
        self.last_heartbeat = time.time()
        self.status = StreamingStatus.CONNECTED
        self.events_received = 0
        self.events_dropped = 0

    def matches_filter(self, event: StreamingEvent) -> bool:
        """Check if event matches subscriber filters"""
        if not self.filters:
            return True

        # Event type filter
        if 'event_types' in self.filters:
            if event.event.event_type.value not in self.filters['event_types']:
                return False

        # Severity filter
        if 'min_severity' in self.filters:
            min_severity = AuditSeverity(self.filters['min_severity'])
            event_severity_value = list(AuditSeverity).index(event.event.severity)
            min_severity_value = list(AuditSeverity).index(min_severity)
            if event_severity_value < min_severity_value:
                return False

        # Loan ID filter
        if 'loan_ids' in self.filters:
            event_loan_id = getattr(event.event.event_data, 'loan_id', None)
            if event_loan_id not in self.filters['loan_ids']:
                return False

        # Service filter
        if 'services' in self.filters:
            if event.event.service_name not in self.filters['services']:
                return False

        return True

    async def notify(self, event: StreamingEvent) -> bool:
        """Notify subscriber of new event"""
        try:
            if self.matches_filter(event):
                await self.callback(event)
                self.events_received += 1
                return True
            return True  # Filtered out, but not an error
        except Exception as e:
            logger.error(f"Failed to notify subscriber {self.subscriber_id}: {e}")
            self.events_dropped += 1
            return False

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = time.time()


class EventStreamingService:
    """Main event streaming service"""

    def __init__(self, config: Optional[EventStreamConfig] = None):
        self.config = config or EventStreamConfig()

        # Core components
        self.event_queue: Queue = Queue(maxsize=self.config.max_queue_size)
        self.deduplicator = EventDeduplicator(
            window_seconds=self.config.dedup_window_seconds,
            cache_size=self.config.dedup_cache_size
        )
        self.metrics = EventMetrics(window_seconds=self.config.metrics_window_seconds)

        # Subscribers management
        self.subscribers: Dict[str, EventSubscriber] = {}
        self.subscriber_lock = asyncio.Lock()

        # Processing state
        self.is_running = False
        self.processor_task: Optional[asyncio.Task] = None
        self.flush_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None

        # Batching
        self.pending_events: List[StreamingEvent] = []
        self.last_flush = time.time()

        # Thread pool for non-async operations
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def start(self):
        """Start the event streaming service"""
        if self.is_running:
            logger.warning("Event streaming service already running")
            return

        logger.info("Starting event streaming service")
        self.is_running = True

        # Start background tasks
        self.processor_task = asyncio.create_task(self._process_events())
        self.flush_task = asyncio.create_task(self._flush_events_periodically())
        self.monitoring_task = asyncio.create_task(self._monitor_performance())

        logger.info("Event streaming service started successfully")

    async def stop(self):
        """Stop the event streaming service"""
        if not self.is_running:
            return

        logger.info("Stopping event streaming service")
        self.is_running = False

        # Cancel background tasks
        if self.processor_task:
            self.processor_task.cancel()
        if self.flush_task:
            self.flush_task.cancel()
        if self.monitoring_task:
            self.monitoring_task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(
            self.processor_task,
            self.flush_task,
            self.monitoring_task,
            return_exceptions=True
        )

        # Flush any remaining events
        await self._flush_pending_events()

        # Clean up executor
        self.executor.shutdown(wait=True)

        logger.info("Event streaming service stopped")

    def submit_event(self, event: AuditTrail, priority: EventPriority = EventPriority.NORMAL) -> bool:
        """Submit an event for streaming"""
        streaming_event = StreamingEvent(
            id=str(uuid.uuid4()),
            event=event,
            priority=priority
        )

        # Check for duplicates
        if self.deduplicator.is_duplicate(streaming_event):
            logger.debug(f"Dropping duplicate event: {streaming_event.dedupe_hash}")
            self.metrics.record_event_dropped("duplicate")
            return False

        # Try to add to queue
        try:
            self.event_queue.put_nowait(streaming_event)
            return True
        except Full:
            logger.warning("Event queue full, dropping event")
            self.metrics.record_event_dropped("queue_full")
            return False

    async def subscribe(
        self,
        subscriber_id: str,
        callback: Callable,
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Subscribe to event stream"""
        async with self.subscriber_lock:
            if subscriber_id in self.subscribers:
                logger.warning(f"Subscriber {subscriber_id} already exists")
                return False

            if len(self.subscribers) >= self.config.max_connections:
                logger.warning(f"Maximum connections reached: {self.config.max_connections}")
                return False

            subscriber = EventSubscriber(subscriber_id, callback, filters)
            self.subscribers[subscriber_id] = subscriber
            self.metrics.add_subscriber(subscriber_id)

            logger.info(f"Subscriber {subscriber_id} added successfully")
            return True

    async def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from event stream"""
        async with self.subscriber_lock:
            if subscriber_id not in self.subscribers:
                return False

            del self.subscribers[subscriber_id]
            self.metrics.remove_subscriber(subscriber_id)

            logger.info(f"Subscriber {subscriber_id} removed")
            return True

    async def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics"""
        base_metrics = self.metrics.get_metrics()

        async with self.subscriber_lock:
            subscriber_metrics = {
                subscriber_id: {
                    'events_received': sub.events_received,
                    'events_dropped': sub.events_dropped,
                    'status': sub.status.value,
                    'last_heartbeat': sub.last_heartbeat,
                    'filters': sub.filters
                }
                for subscriber_id, sub in self.subscribers.items()
            }

        return {
            **base_metrics,
            'queue_size': self.event_queue.qsize(),
            'pending_events': len(self.pending_events),
            'deduplicator_cache_size': len(self.deduplicator.seen_events),
            'subscribers': subscriber_metrics
        }

    async def _process_events(self):
        """Main event processing loop"""
        while self.is_running:
            try:
                # Get event from queue (non-blocking)
                try:
                    streaming_event = self.event_queue.get_nowait()
                except Empty:
                    await asyncio.sleep(0.01)  # Short sleep to prevent busy waiting
                    continue

                start_time = time.time()

                # Add to pending batch
                self.pending_events.append(streaming_event)

                # Check if we should flush
                should_flush = (
                    len(self.pending_events) >= self.config.batch_size or
                    (time.time() - self.last_flush) * 1000 >= self.config.flush_interval_ms
                )

                if should_flush:
                    await self._flush_pending_events()

                # Record processing metrics
                processing_time = (time.time() - start_time) * 1000
                self.metrics.record_event_processed(processing_time)

                # Check latency threshold
                if processing_time > self.config.performance_threshold_ms:
                    logger.warning(f"High processing latency: {processing_time}ms")

            except Exception as e:
                logger.error(f"Error processing events: {e}")
                await asyncio.sleep(0.1)  # Back off on error

    async def _flush_pending_events(self):
        """Flush pending events to subscribers"""
        if not self.pending_events:
            return

        events_to_process = self.pending_events.copy()
        self.pending_events.clear()
        self.last_flush = time.time()

        # Sort by priority and timestamp
        events_to_process.sort(
            key=lambda e: (e.priority.value, e.timestamp_received),
            reverse=True
        )

        # Notify all subscribers
        async with self.subscriber_lock:
            subscribers_copy = list(self.subscribers.values())

        for event in events_to_process:
            await self._notify_subscribers(event, subscribers_copy)

    async def _notify_subscribers(self, event: StreamingEvent, subscribers: List[EventSubscriber]):
        """Notify all subscribers of an event"""
        notification_tasks = []

        for subscriber in subscribers:
            # Skip disconnected subscribers
            if subscriber.status == StreamingStatus.DISCONNECTED:
                continue

            # Create notification task
            task = asyncio.create_task(
                self._notify_subscriber_with_retry(event, subscriber)
            )
            notification_tasks.append(task)

        # Wait for all notifications (with timeout)
        if notification_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*notification_tasks, return_exceptions=True),
                    timeout=self.config.max_latency_ms / 1000
                )
            except asyncio.TimeoutError:
                logger.warning("Subscriber notifications timed out")

    async def _notify_subscriber_with_retry(self, event: StreamingEvent, subscriber: EventSubscriber):
        """Notify subscriber with retry logic"""
        retry_count = 0
        delay = self.config.retry_delay_ms / 1000

        while retry_count <= self.config.max_retries:
            try:
                success = await subscriber.notify(event)
                if success:
                    return

                # If notification failed, update subscriber status
                if retry_count == self.config.max_retries:
                    subscriber.status = StreamingStatus.ERROR
                    logger.warning(f"Subscriber {subscriber.subscriber_id} marked as error after {retry_count} retries")

                break

            except Exception as e:
                retry_count += 1
                if retry_count <= self.config.max_retries:
                    logger.debug(f"Retrying subscriber {subscriber.subscriber_id} (attempt {retry_count}): {e}")
                    await asyncio.sleep(delay)
                    delay *= self.config.retry_backoff_factor
                else:
                    logger.error(f"Failed to notify subscriber {subscriber.subscriber_id} after {retry_count} attempts: {e}")
                    subscriber.status = StreamingStatus.ERROR

    async def _flush_events_periodically(self):
        """Periodic flush of pending events"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.flush_interval_ms / 1000)
                if self.pending_events:
                    await self._flush_pending_events()
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def _monitor_performance(self):
        """Monitor system performance and health"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                metrics = await self.get_metrics()

                # Check for performance issues
                if metrics['average_processing_time_ms'] > self.config.performance_threshold_ms:
                    logger.warning(f"High average processing time: {metrics['average_processing_time_ms']}ms")

                if metrics['queue_size'] > self.config.max_queue_size * 0.8:
                    logger.warning(f"Event queue getting full: {metrics['queue_size']}/{self.config.max_queue_size}")

                # Update connection count metric
                self.metrics.update_connection_count(len(self.subscribers))

                # Clean up disconnected subscribers
                await self._cleanup_disconnected_subscribers()

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")

    async def _cleanup_disconnected_subscribers(self):
        """Remove disconnected or timed-out subscribers"""
        current_time = time.time()
        timeout_threshold = self.config.connection_timeout_ms / 1000

        async with self.subscriber_lock:
            disconnected_ids = []

            for subscriber_id, subscriber in self.subscribers.items():
                # Check for timeout
                if (current_time - subscriber.last_heartbeat) > timeout_threshold:
                    logger.info(f"Removing timed-out subscriber: {subscriber_id}")
                    disconnected_ids.append(subscriber_id)
                # Check for error status
                elif subscriber.status == StreamingStatus.ERROR:
                    logger.info(f"Removing error subscriber: {subscriber_id}")
                    disconnected_ids.append(subscriber_id)

            # Remove disconnected subscribers
            for subscriber_id in disconnected_ids:
                del self.subscribers[subscriber_id]
                self.metrics.remove_subscriber(subscriber_id)


# Global event streaming service instance
_event_streaming_service: Optional[EventStreamingService] = None


async def get_event_streaming_service() -> EventStreamingService:
    """Get or create the global event streaming service"""
    global _event_streaming_service

    if _event_streaming_service is None:
        _event_streaming_service = EventStreamingService()
        await _event_streaming_service.start()

    return _event_streaming_service


async def shutdown_event_streaming_service():
    """Shutdown the global event streaming service"""
    global _event_streaming_service

    if _event_streaming_service:
        await _event_streaming_service.stop()
        _event_streaming_service = None


# Convenience functions for common operations

async def stream_audit_event(
    event: AuditTrail,
    priority: EventPriority = EventPriority.NORMAL
) -> bool:
    """Stream an audit event through the global service"""
    service = await get_event_streaming_service()
    return service.submit_event(event, priority)


async def subscribe_to_events(
    subscriber_id: str,
    callback: Callable,
    event_types: Optional[List[str]] = None,
    min_severity: str = "info",
    loan_ids: Optional[List[str]] = None,
    services: Optional[List[str]] = None
) -> bool:
    """Subscribe to audit event stream with filters"""
    filters = {}

    if event_types:
        filters['event_types'] = event_types
    if min_severity:
        filters['min_severity'] = min_severity
    if loan_ids:
        filters['loan_ids'] = loan_ids
    if services:
        filters['services'] = services

    service = await get_event_streaming_service()
    return await service.subscribe(subscriber_id, callback, filters)


async def unsubscribe_from_events(subscriber_id: str) -> bool:
    """Unsubscribe from audit event stream"""
    service = await get_event_streaming_service()
    return await service.unsubscribe(subscriber_id)


async def get_streaming_metrics() -> Dict[str, Any]:
    """Get current streaming system metrics"""
    service = await get_event_streaming_service()
    return await service.get_metrics()