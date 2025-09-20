"""
Event Processing Engine for Real-time Audit Events

High-performance event processor that handles transformation, enrichment, filtering,
and routing of audit events before they are streamed to subscribers.

Features:
- Event transformation and enrichment
- Real-time filtering and routing
- Batch processing optimization
- Data validation and sanitization
- Performance monitoring and analytics
- Error handling and recovery
"""

import asyncio
import logging
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Set, Callable, Union, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import uuid
import re
from abc import ABC, abstractmethod

from .models import AuditTrail, AuditEventType, AuditSeverity, AuditEventData
from .event_streaming import StreamingEvent, EventPriority


logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Event processing pipeline stages"""
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    TRANSFORMATION = "transformation"
    FILTERING = "filtering"
    ROUTING = "routing"
    DELIVERY = "delivery"


class ProcessingResult(Enum):
    """Result of event processing"""
    SUCCESS = "success"
    FILTERED_OUT = "filtered_out"
    TRANSFORMED = "transformed"
    ENRICHED = "enriched"
    FAILED = "failed"
    RETRY_REQUIRED = "retry_required"


@dataclass
class ProcessingMetrics:
    """Metrics for event processing performance"""
    events_processed: int = 0
    events_filtered: int = 0
    events_transformed: int = 0
    events_enriched: int = 0
    events_failed: int = 0
    total_processing_time_ms: float = 0
    average_processing_time_ms: float = 0
    max_processing_time_ms: float = 0
    stage_times: Dict[ProcessingStage, float] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)

    def update_processing_time(self, processing_time_ms: float):
        """Update processing time statistics"""
        self.events_processed += 1
        self.total_processing_time_ms += processing_time_ms
        self.average_processing_time_ms = self.total_processing_time_ms / self.events_processed
        self.max_processing_time_ms = max(self.max_processing_time_ms, processing_time_ms)


@dataclass
class ProcessedEvent:
    """Event that has been processed through the pipeline"""
    original_event: StreamingEvent
    processed_event: StreamingEvent
    processing_stages: List[ProcessingStage] = field(default_factory=list)
    processing_time_ms: float = 0
    enriched_data: Dict[str, Any] = field(default_factory=dict)
    transformation_log: List[str] = field(default_factory=list)
    target_subscribers: Set[str] = field(default_factory=set)
    routing_metadata: Dict[str, Any] = field(default_factory=dict)


class EventProcessor(ABC):
    """Base class for event processors"""

    @abstractmethod
    async def process(self, event: StreamingEvent) -> Tuple[ProcessingResult, StreamingEvent]:
        """Process an event and return result and modified event"""
        pass

    @property
    @abstractmethod
    def processor_name(self) -> str:
        """Name of the processor"""
        pass

    @property
    def processor_priority(self) -> int:
        """Priority for processor ordering (lower number = higher priority)"""
        return 100


class ValidationProcessor(EventProcessor):
    """Validates event data and structure"""

    def __init__(self):
        self.validation_rules = {
            'required_fields': ['event_type', 'timestamp', 'service_name'],
            'max_field_length': 10000,
            'allowed_event_types': [e.value for e in AuditEventType],
            'allowed_severities': [s.value for s in AuditSeverity]
        }

    @property
    def processor_name(self) -> str:
        return "validation_processor"

    @property
    def processor_priority(self) -> int:
        return 1  # Highest priority - run first

    async def process(self, event: StreamingEvent) -> Tuple[ProcessingResult, StreamingEvent]:
        """Validate event structure and data"""
        try:
            # Check required fields
            for field in self.validation_rules['required_fields']:
                if not hasattr(event.event, field) or getattr(event.event, field) is None:
                    raise ValueError(f"Missing required field: {field}")

            # Validate event type
            if event.event.event_type.value not in self.validation_rules['allowed_event_types']:
                raise ValueError(f"Invalid event type: {event.event.event_type.value}")

            # Validate severity
            if event.event.severity.value not in self.validation_rules['allowed_severities']:
                raise ValueError(f"Invalid severity: {event.event.severity.value}")

            # Validate field lengths
            for field_name in ['service_name', 'correlation_id', 'trace_id']:
                field_value = getattr(event.event, field_name, None)
                if field_value and len(str(field_value)) > self.validation_rules['max_field_length']:
                    raise ValueError(f"Field {field_name} exceeds maximum length")

            # Validate timestamp is recent (within 24 hours)
            if event.event.timestamp:
                time_diff = datetime.now(timezone.utc) - event.event.timestamp
                if time_diff > timedelta(hours=24):
                    logger.warning(f"Event timestamp is old: {time_diff}")

            return ProcessingResult.SUCCESS, event

        except Exception as e:
            logger.error(f"Event validation failed: {e}")
            return ProcessingResult.FAILED, event


class EnrichmentProcessor(EventProcessor):
    """Enriches events with additional contextual data"""

    def __init__(self):
        self.geo_cache: Dict[str, Dict[str, Any]] = {}
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        self.loan_cache: Dict[str, Dict[str, Any]] = {}

    @property
    def processor_name(self) -> str:
        return "enrichment_processor"

    @property
    def processor_priority(self) -> int:
        return 10

    async def process(self, event: StreamingEvent) -> Tuple[ProcessingResult, StreamingEvent]:
        """Enrich event with additional contextual data"""
        try:
            enrichment_data = {}

            # Enrich with user information
            user_id = getattr(event.event.event_data, 'user_id', None)
            if user_id and user_id not in self.user_cache:
                user_info = await self._fetch_user_info(user_id)
                if user_info:
                    self.user_cache[user_id] = user_info
                    enrichment_data['user_info'] = user_info
            elif user_id in self.user_cache:
                enrichment_data['user_info'] = self.user_cache[user_id]

            # Enrich with loan information
            loan_id = getattr(event.event.event_data, 'loan_id', None)
            if loan_id and loan_id not in self.loan_cache:
                loan_info = await self._fetch_loan_info(loan_id)
                if loan_info:
                    self.loan_cache[loan_id] = loan_info
                    enrichment_data['loan_info'] = loan_info
            elif loan_id in self.loan_cache:
                enrichment_data['loan_info'] = self.loan_cache[loan_id]

            # Enrich with blockchain information
            transaction_id = getattr(event.event.event_data, 'transaction_id', None)
            if transaction_id:
                blockchain_info = await self._fetch_blockchain_info(transaction_id)
                if blockchain_info:
                    enrichment_data['blockchain_info'] = blockchain_info

            # Enrich with time-based context
            enrichment_data['time_context'] = {
                'day_of_week': event.event.timestamp.weekday(),
                'hour_of_day': event.event.timestamp.hour,
                'is_business_hours': 9 <= event.event.timestamp.hour <= 17,
                'is_weekend': event.event.timestamp.weekday() >= 5,
                'processing_delay_ms': (time.time() - event.timestamp_received) * 1000
            }

            # Add enrichment data to event metadata
            if enrichment_data:
                if not hasattr(event.event.event_data, 'metadata') or not event.event.event_data.metadata:
                    event.event.event_data.metadata = {}

                event.event.event_data.metadata.setdefault('enrichment', {}).update(enrichment_data)
                return ProcessingResult.ENRICHED, event

            return ProcessingResult.SUCCESS, event

        except Exception as e:
            logger.error(f"Event enrichment failed: {e}")
            return ProcessingResult.SUCCESS, event  # Don't fail on enrichment errors

    async def _fetch_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user information for enrichment"""
        try:
            # Mock user info - in production, this would query a user service
            return {
                'user_type': 'borrower',
                'registration_date': '2024-01-15',
                'verification_status': 'verified',
                'risk_score': 0.25
            }
        except Exception as e:
            logger.debug(f"Failed to fetch user info for {user_id}: {e}")
            return None

    async def _fetch_loan_info(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Fetch loan information for enrichment"""
        try:
            # Mock loan info - in production, this would query a loan service
            return {
                'loan_status': 'active',
                'creation_date': '2024-02-01',
                'due_date': '2024-03-01',
                'collateral_ratio': 1.5,
                'payment_history': 'good'
            }
        except Exception as e:
            logger.debug(f"Failed to fetch loan info for {loan_id}: {e}")
            return None

    async def _fetch_blockchain_info(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Fetch blockchain transaction information"""
        try:
            # Mock blockchain info - in production, this would query blockchain
            return {
                'block_height': 12345678,
                'confirmations': 5,
                'gas_fee': 1000,
                'network': 'algorand-testnet'
            }
        except Exception as e:
            logger.debug(f"Failed to fetch blockchain info for {transaction_id}: {e}")
            return None


class TransformationProcessor(EventProcessor):
    """Transforms events for different subscriber needs"""

    def __init__(self):
        self.transformation_rules = {
            'ui_events': {
                'include_fields': ['event_type', 'timestamp', 'severity', 'loan_id', 'status'],
                'exclude_sensitive': True,
                'format': 'compact'
            },
            'analytics_events': {
                'include_fields': '*',
                'exclude_sensitive': False,
                'format': 'full',
                'add_metrics': True
            },
            'compliance_events': {
                'include_fields': '*',
                'exclude_sensitive': False,
                'format': 'audit_trail',
                'require_signature': True
            }
        }

    @property
    def processor_name(self) -> str:
        return "transformation_processor"

    @property
    def processor_priority(self) -> int:
        return 20

    async def process(self, event: StreamingEvent) -> Tuple[ProcessingResult, StreamingEvent]:
        """Transform event based on subscriber requirements"""
        try:
            # Get subscriber types from event metadata
            subscriber_types = getattr(event, 'target_subscriber_types', ['default'])

            transformations_applied = []

            for sub_type in subscriber_types:
                if sub_type in self.transformation_rules:
                    rules = self.transformation_rules[sub_type]

                    # Apply field filtering
                    if rules.get('include_fields') != '*':
                        event = self._filter_fields(event, rules['include_fields'])
                        transformations_applied.append(f"field_filter_{sub_type}")

                    # Remove sensitive data if required
                    if rules.get('exclude_sensitive'):
                        event = self._remove_sensitive_data(event)
                        transformations_applied.append(f"sensitivity_filter_{sub_type}")

                    # Apply format transformations
                    if rules.get('format') == 'compact':
                        event = self._apply_compact_format(event)
                        transformations_applied.append(f"compact_format_{sub_type}")
                    elif rules.get('format') == 'audit_trail':
                        event = self._apply_audit_format(event)
                        transformations_applied.append(f"audit_format_{sub_type}")

                    # Add metrics if required
                    if rules.get('add_metrics'):
                        event = self._add_metrics(event)
                        transformations_applied.append(f"metrics_{sub_type}")

            if transformations_applied:
                # Add transformation metadata
                if not hasattr(event.event.event_data, 'metadata') or not event.event.event_data.metadata:
                    event.event.event_data.metadata = {}

                event.event.event_data.metadata['transformations'] = transformations_applied
                return ProcessingResult.TRANSFORMED, event

            return ProcessingResult.SUCCESS, event

        except Exception as e:
            logger.error(f"Event transformation failed: {e}")
            return ProcessingResult.SUCCESS, event

    def _filter_fields(self, event: StreamingEvent, include_fields: List[str]) -> StreamingEvent:
        """Filter event to include only specified fields"""
        # Implementation would filter the event data structure
        return event

    def _remove_sensitive_data(self, event: StreamingEvent) -> StreamingEvent:
        """Remove sensitive information from event"""
        sensitive_patterns = [
            r'password', r'secret', r'key', r'token',
            r'private.*key', r'mnemonic', r'seed'
        ]

        if hasattr(event.event.event_data, 'metadata') and event.event.event_data.metadata:
            for key, value in list(event.event.event_data.metadata.items()):
                if any(re.search(pattern, key, re.IGNORECASE) for pattern in sensitive_patterns):
                    event.event.event_data.metadata[key] = "<REDACTED>"
                elif isinstance(value, str) and len(value) > 100:
                    # Truncate very long strings that might contain sensitive data
                    event.event.event_data.metadata[key] = value[:100] + "...<TRUNCATED>"

        return event

    def _apply_compact_format(self, event: StreamingEvent) -> StreamingEvent:
        """Apply compact formatting for UI events"""
        # Remove verbose metadata, keep only essential information
        if hasattr(event.event.event_data, 'metadata') and event.event.event_data.metadata:
            essential_keys = ['loan_id', 'user_id', 'transaction_id', 'status']
            filtered_metadata = {
                key: value for key, value in event.event.event_data.metadata.items()
                if key in essential_keys
            }
            event.event.event_data.metadata = filtered_metadata

        return event

    def _apply_audit_format(self, event: StreamingEvent) -> StreamingEvent:
        """Apply audit trail formatting for compliance"""
        # Ensure all audit fields are present and properly formatted
        if not hasattr(event.event.event_data, 'metadata') or not event.event.event_data.metadata:
            event.event.event_data.metadata = {}

        event.event.event_data.metadata.update({
            'audit_version': '1.0',
            'compliance_flag': True,
            'retention_required': True,
            'processed_at': datetime.now(timezone.utc).isoformat()
        })

        return event

    def _add_metrics(self, event: StreamingEvent) -> StreamingEvent:
        """Add performance and analytics metrics"""
        if not hasattr(event.event.event_data, 'metadata') or not event.event.event_data.metadata:
            event.event.event_data.metadata = {}

        event.event.event_data.metadata.update({
            'processing_latency_ms': (time.time() - event.timestamp_received) * 1000,
            'queue_depth': 0,  # Would be set by the processor
            'event_sequence': event.id,
            'analytics_enabled': True
        })

        return event


class FilteringProcessor(EventProcessor):
    """Filters events based on business rules and subscriber preferences"""

    def __init__(self):
        self.filter_rules = {
            'severity_threshold': AuditSeverity.INFO,
            'rate_limit_window_seconds': 60,
            'rate_limit_max_events': 100,
            'duplicate_suppression_window': 30,
            'business_hours_only': False,
            'exclude_test_events': True
        }
        self.rate_limit_cache: Dict[str, deque] = defaultdict(deque)
        self.duplicate_cache: Set[str] = set()

    @property
    def processor_name(self) -> str:
        return "filtering_processor"

    @property
    def processor_priority(self) -> int:
        return 30

    async def process(self, event: StreamingEvent) -> Tuple[ProcessingResult, StreamingEvent]:
        """Filter events based on configured rules"""
        try:
            # Check severity threshold
            if self._is_below_severity_threshold(event):
                return ProcessingResult.FILTERED_OUT, event

            # Check rate limiting
            if self._is_rate_limited(event):
                return ProcessingResult.FILTERED_OUT, event

            # Check for duplicates
            if self._is_duplicate(event):
                return ProcessingResult.FILTERED_OUT, event

            # Check business hours filter
            if self._is_outside_business_hours(event):
                return ProcessingResult.FILTERED_OUT, event

            # Check test event filter
            if self._is_test_event(event):
                return ProcessingResult.FILTERED_OUT, event

            return ProcessingResult.SUCCESS, event

        except Exception as e:
            logger.error(f"Event filtering failed: {e}")
            return ProcessingResult.SUCCESS, event  # Allow through on filter errors

    def _is_below_severity_threshold(self, event: StreamingEvent) -> bool:
        """Check if event is below severity threshold"""
        severity_order = list(AuditSeverity)
        event_severity_index = severity_order.index(event.event.severity)
        threshold_index = severity_order.index(self.filter_rules['severity_threshold'])
        return event_severity_index < threshold_index

    def _is_rate_limited(self, event: StreamingEvent) -> bool:
        """Check if event should be rate limited"""
        # Use service name + event type as rate limit key
        rate_key = f"{event.event.service_name}:{event.event.event_type.value}"
        current_time = time.time()
        window_start = current_time - self.filter_rules['rate_limit_window_seconds']

        # Clean old entries
        while (self.rate_limit_cache[rate_key] and
               self.rate_limit_cache[rate_key][0] < window_start):
            self.rate_limit_cache[rate_key].popleft()

        # Check if we're over the limit
        if len(self.rate_limit_cache[rate_key]) >= self.filter_rules['rate_limit_max_events']:
            return True

        # Add current event to rate limit cache
        self.rate_limit_cache[rate_key].append(current_time)
        return False

    def _is_duplicate(self, event: StreamingEvent) -> bool:
        """Check if event is a duplicate"""
        if event.dedupe_hash in self.duplicate_cache:
            return True

        self.duplicate_cache.add(event.dedupe_hash)

        # Clean cache periodically (simple cleanup)
        if len(self.duplicate_cache) > 10000:
            # Remove oldest 20% of entries (simple approach)
            cache_list = list(self.duplicate_cache)
            self.duplicate_cache = set(cache_list[-8000:])

        return False

    def _is_outside_business_hours(self, event: StreamingEvent) -> bool:
        """Check if event is outside business hours"""
        if not self.filter_rules['business_hours_only']:
            return False

        hour = event.event.timestamp.hour
        weekday = event.event.timestamp.weekday()

        # Business hours: 9 AM to 5 PM, Monday to Friday
        is_business_hours = (9 <= hour <= 17) and (weekday < 5)
        return not is_business_hours

    def _is_test_event(self, event: StreamingEvent) -> bool:
        """Check if event is a test event"""
        if not self.filter_rules['exclude_test_events']:
            return False

        # Check for test indicators in the event data
        test_indicators = ['test', 'mock', 'demo', 'example']

        # Check service name
        if any(indicator in event.event.service_name.lower() for indicator in test_indicators):
            return True

        # Check metadata
        if hasattr(event.event.event_data, 'metadata') and event.event.event_data.metadata:
            metadata_str = json.dumps(event.event.event_data.metadata).lower()
            if any(indicator in metadata_str for indicator in test_indicators):
                return True

        return False


class RoutingProcessor(EventProcessor):
    """Routes events to appropriate subscribers based on routing rules"""

    def __init__(self):
        self.routing_rules = {
            'ui_subscribers': {
                'event_types': ['loan_request_created', 'loan_approved', 'loan_rejected'],
                'severities': ['info', 'warning', 'error'],
                'priority': EventPriority.NORMAL
            },
            'analytics_subscribers': {
                'event_types': '*',
                'severities': '*',
                'priority': EventPriority.LOW
            },
            'compliance_subscribers': {
                'event_types': ['loan_approved', 'loan_rejected', 'liquidation_triggered'],
                'severities': ['warning', 'error', 'critical'],
                'priority': EventPriority.HIGH
            },
            'monitoring_subscribers': {
                'event_types': ['system_error', 'performance_warning'],
                'severities': ['error', 'critical'],
                'priority': EventPriority.CRITICAL
            }
        }

    @property
    def processor_name(self) -> str:
        return "routing_processor"

    @property
    def processor_priority(self) -> int:
        return 40

    async def process(self, event: StreamingEvent) -> Tuple[ProcessingResult, StreamingEvent]:
        """Route event to appropriate subscribers"""
        try:
            target_subscriber_types = []
            routing_metadata = {}

            event_type = event.event.event_type.value
            event_severity = event.event.severity.value

            for subscriber_type, rules in self.routing_rules.items():
                # Check event type match
                if (rules['event_types'] == '*' or
                    event_type in rules['event_types']):

                    # Check severity match
                    if (rules['severities'] == '*' or
                        event_severity in rules['severities']):

                        target_subscriber_types.append(subscriber_type)
                        routing_metadata[subscriber_type] = {
                            'priority': rules['priority'].value,
                            'matched_rule': {
                                'event_type': event_type in rules['event_types'] if rules['event_types'] != '*' else '*',
                                'severity': event_severity in rules['severities'] if rules['severities'] != '*' else '*'
                            }
                        }

            # Add routing information to event
            if target_subscriber_types:
                if not hasattr(event.event.event_data, 'metadata') or not event.event.event_data.metadata:
                    event.event.event_data.metadata = {}

                event.event.event_data.metadata['routing'] = {
                    'target_subscriber_types': target_subscriber_types,
                    'routing_metadata': routing_metadata,
                    'routed_at': datetime.now(timezone.utc).isoformat()
                }

                # Set event priority based on highest priority subscriber
                max_priority = max([rules['priority'] for subscriber_type, rules in self.routing_rules.items()
                                   if subscriber_type in target_subscriber_types])
                event.priority = max_priority

            return ProcessingResult.SUCCESS, event

        except Exception as e:
            logger.error(f"Event routing failed: {e}")
            return ProcessingResult.SUCCESS, event


class EventProcessingPipeline:
    """Main event processing pipeline that orchestrates all processors"""

    def __init__(self, processors: Optional[List[EventProcessor]] = None):
        # Default processors in priority order
        if processors is None:
            processors = [
                ValidationProcessor(),
                EnrichmentProcessor(),
                TransformationProcessor(),
                FilteringProcessor(),
                RoutingProcessor()
            ]

        # Sort processors by priority
        self.processors = sorted(processors, key=lambda p: p.processor_priority)
        self.metrics = ProcessingMetrics()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Processing configuration
        self.max_processing_time_ms = 1000
        self.enable_parallel_processing = True
        self.batch_processing = True
        self.batch_size = 10

        logger.info(f"Event processing pipeline initialized with {len(self.processors)} processors")

    async def process_event(self, event: StreamingEvent) -> Optional[ProcessedEvent]:
        """Process a single event through the pipeline"""
        start_time = time.time()

        try:
            processed_event = ProcessedEvent(
                original_event=event,
                processed_event=event,
                processing_stages=[],
                processing_time_ms=0,
                enriched_data={},
                transformation_log=[],
                target_subscribers=set(),
                routing_metadata={}
            )

            # Process through each stage
            current_event = event
            for processor in self.processors:
                stage_start = time.time()

                try:
                    result, current_event = await processor.process(current_event)

                    stage_time = (time.time() - stage_start) * 1000
                    stage_enum = ProcessingStage(processor.processor_name.replace('_processor', ''))

                    processed_event.processing_stages.append(stage_enum)
                    self.metrics.stage_times[stage_enum] = self.metrics.stage_times.get(stage_enum, 0) + stage_time

                    # Handle processing result
                    if result == ProcessingResult.FAILED:
                        logger.warning(f"Event processing failed at {processor.processor_name}")
                        self.metrics.events_failed += 1
                        return None
                    elif result == ProcessingResult.FILTERED_OUT:
                        logger.debug(f"Event filtered out at {processor.processor_name}")
                        self.metrics.events_filtered += 1
                        return None
                    elif result == ProcessingResult.ENRICHED:
                        self.metrics.events_enriched += 1
                        processed_event.transformation_log.append(f"Enriched by {processor.processor_name}")
                    elif result == ProcessingResult.TRANSFORMED:
                        self.metrics.events_transformed += 1
                        processed_event.transformation_log.append(f"Transformed by {processor.processor_name}")

                except Exception as e:
                    logger.error(f"Error in processor {processor.processor_name}: {e}")
                    self.metrics.error_counts[processor.processor_name] = (
                        self.metrics.error_counts.get(processor.processor_name, 0) + 1
                    )
                    # Continue with next processor
                    continue

            # Update final processed event
            processed_event.processed_event = current_event
            processing_time = (time.time() - start_time) * 1000
            processed_event.processing_time_ms = processing_time

            # Update metrics
            self.metrics.update_processing_time(processing_time)

            # Check for processing time threshold
            if processing_time > self.max_processing_time_ms:
                logger.warning(f"Event processing took {processing_time}ms (threshold: {self.max_processing_time_ms}ms)")

            return processed_event

        except Exception as e:
            logger.error(f"Event processing pipeline failed: {e}")
            self.metrics.events_failed += 1
            return None

    async def process_batch(self, events: List[StreamingEvent]) -> List[ProcessedEvent]:
        """Process multiple events in batch"""
        if not self.batch_processing or len(events) <= 1:
            # Process individually
            results = []
            for event in events:
                result = await self.process_event(event)
                if result:
                    results.append(result)
            return results

        # Batch processing
        try:
            if self.enable_parallel_processing:
                # Process events in parallel
                tasks = [self.process_event(event) for event in events]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Filter out exceptions and None results
                processed_events = [
                    result for result in results
                    if isinstance(result, ProcessedEvent)
                ]
            else:
                # Sequential processing
                processed_events = []
                for event in events:
                    result = await self.process_event(event)
                    if result:
                        processed_events.append(result)

            return processed_events

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return []

    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics"""
        return {
            'events_processed': self.metrics.events_processed,
            'events_filtered': self.metrics.events_filtered,
            'events_transformed': self.metrics.events_transformed,
            'events_enriched': self.metrics.events_enriched,
            'events_failed': self.metrics.events_failed,
            'average_processing_time_ms': self.metrics.average_processing_time_ms,
            'max_processing_time_ms': self.metrics.max_processing_time_ms,
            'stage_times_ms': {stage.value: time_ms for stage, time_ms in self.metrics.stage_times.items()},
            'error_counts': dict(self.metrics.error_counts),
            'processor_count': len(self.processors),
            'processors': [p.processor_name for p in self.processors]
        }

    async def shutdown(self):
        """Shutdown the processing pipeline"""
        logger.info("Shutting down event processing pipeline")
        self.executor.shutdown(wait=True)


# Global processing pipeline instance
_processing_pipeline: Optional[EventProcessingPipeline] = None


async def get_processing_pipeline() -> EventProcessingPipeline:
    """Get or create the global processing pipeline"""
    global _processing_pipeline

    if _processing_pipeline is None:
        _processing_pipeline = EventProcessingPipeline()

    return _processing_pipeline


async def process_audit_event(event: StreamingEvent) -> Optional[ProcessedEvent]:
    """Process a single audit event through the global pipeline"""
    pipeline = await get_processing_pipeline()
    return await pipeline.process_event(event)


async def process_audit_events_batch(events: List[StreamingEvent]) -> List[ProcessedEvent]:
    """Process multiple audit events through the global pipeline"""
    pipeline = await get_processing_pipeline()
    return await pipeline.process_batch(events)


async def get_processing_metrics() -> Dict[str, Any]:
    """Get processing pipeline metrics"""
    pipeline = await get_processing_pipeline()
    return pipeline.get_processing_metrics()


async def shutdown_processing_pipeline():
    """Shutdown the global processing pipeline"""
    global _processing_pipeline

    if _processing_pipeline:
        await _processing_pipeline.shutdown()
        _processing_pipeline = None