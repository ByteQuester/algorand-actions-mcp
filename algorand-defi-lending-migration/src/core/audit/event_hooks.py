"""
Integration Hooks for Real-time Event Capture

This module provides hooks and decorators to capture audit events from various
components of the lending platform, including:
- ADK session events
- MCP transaction events
- Lending workflow transitions
- Enforcement actions
- Agent decisions

Features:
- Automatic event capture with decorators
- Context-aware event enrichment
- Performance-optimized hooks
- Error handling and fallback mechanisms
"""

import asyncio
import logging
import functools
import inspect
import time
import traceback
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone
from contextlib import contextmanager, asynccontextmanager
import threading
from dataclasses import dataclass, field

from .models import (
    AuditTrail, AuditEventType, AuditSeverity, AuditEventData,
    create_loan_audit_event, create_decision_point, DecisionType
)
from .event_streaming import stream_audit_event, EventPriority


logger = logging.getLogger(__name__)


@dataclass
class EventContext:
    """Context information for event capture"""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    loan_id: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    service_name: Optional[str] = None
    operation_name: Optional[str] = None
    start_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()


# Thread-local storage for context
_context_storage = threading.local()


def get_current_context() -> Optional[EventContext]:
    """Get current event context from thread-local storage"""
    return getattr(_context_storage, 'context', None)


def set_current_context(context: Optional[EventContext]):
    """Set current event context in thread-local storage"""
    _context_storage.context = context


@contextmanager
def event_context(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    loan_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    service_name: Optional[str] = None,
    operation_name: Optional[str] = None,
    **metadata
):
    """Context manager for setting event context"""
    previous_context = get_current_context()

    # Inherit from previous context if available
    context = EventContext(
        session_id=session_id or (previous_context.session_id if previous_context else None),
        user_id=user_id or (previous_context.user_id if previous_context else None),
        loan_id=loan_id or (previous_context.loan_id if previous_context else None),
        correlation_id=correlation_id or (previous_context.correlation_id if previous_context else None),
        trace_id=trace_id or (previous_context.trace_id if previous_context else None),
        service_name=service_name,
        operation_name=operation_name,
        metadata=metadata
    )

    set_current_context(context)
    try:
        yield context
    finally:
        set_current_context(previous_context)


@asynccontextmanager
async def async_event_context(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    loan_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    service_name: Optional[str] = None,
    operation_name: Optional[str] = None,
    **metadata
):
    """Async context manager for setting event context"""
    with event_context(
        session_id=session_id,
        user_id=user_id,
        loan_id=loan_id,
        correlation_id=correlation_id,
        trace_id=trace_id,
        service_name=service_name,
        operation_name=operation_name,
        **metadata
    ) as context:
        yield context


async def create_and_stream_event(
    event_type: AuditEventType,
    severity: AuditSeverity = AuditSeverity.INFO,
    priority: EventPriority = EventPriority.NORMAL,
    context: Optional[EventContext] = None,
    **event_data
) -> bool:
    """Create and stream an audit event with current context"""
    try:
        # Get context if not provided
        if context is None:
            context = get_current_context()

        # Create event data
        audit_data = AuditEventData(
            session_id=context.session_id if context else None,
            user_id=context.user_id if context else None,
            loan_id=context.loan_id if context else None,
            **event_data
        )

        # Create audit trail
        audit_event = AuditTrail(
            event_type=event_type,
            severity=severity,
            event_data=audit_data,
            service_name=context.service_name if context else "unknown",
            correlation_id=context.correlation_id if context else None,
            trace_id=context.trace_id if context else None,
            span_id=context.span_id if context else None
        )

        # Stream the event
        return await stream_audit_event(audit_event, priority)

    except Exception as e:
        logger.error(f"Failed to create and stream event: {e}")
        return False


# Decorators for automatic event capture

def audit_function(
    event_type: Union[AuditEventType, str],
    severity: AuditSeverity = AuditSeverity.INFO,
    priority: EventPriority = EventPriority.NORMAL,
    capture_args: bool = False,
    capture_result: bool = False,
    capture_errors: bool = True
):
    """Decorator to automatically audit function calls"""

    def decorator(func: Callable) -> Callable:
        # Handle string event type
        audit_event_type = event_type if isinstance(event_type, AuditEventType) else AuditEventType.AGENT_INVOKED

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = get_current_context()
            start_time = time.time()

            # Create operation context
            operation_name = f"{func.__module__}.{func.__name__}"

            try:
                # Capture function invocation
                event_data = {
                    'operation': operation_name,
                    'start_time': datetime.fromtimestamp(start_time, timezone.utc).isoformat()
                }

                if capture_args:
                    # Capture function arguments (be careful with sensitive data)
                    event_data['args'] = _sanitize_args(args)
                    event_data['kwargs'] = _sanitize_kwargs(kwargs)

                await create_and_stream_event(
                    audit_event_type,
                    severity,
                    priority,
                    context,
                    **event_data
                )

                # Execute the function
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Capture successful completion
                processing_time = (time.time() - start_time) * 1000
                completion_data = {
                    'operation': operation_name,
                    'status': 'completed',
                    'processing_time_ms': processing_time
                }

                if capture_result and result is not None:
                    completion_data['result'] = _sanitize_result(result)

                await create_and_stream_event(
                    AuditEventType.AGENT_COMPLETED,
                    AuditSeverity.INFO,
                    priority,
                    context,
                    **completion_data
                )

                return result

            except Exception as e:
                if capture_errors:
                    processing_time = (time.time() - start_time) * 1000
                    error_data = {
                        'operation': operation_name,
                        'status': 'failed',
                        'processing_time_ms': processing_time,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'error_traceback': traceback.format_exc()
                    }

                    await create_and_stream_event(
                        AuditEventType.AGENT_FAILED,
                        AuditSeverity.ERROR,
                        EventPriority.HIGH,
                        context,
                        **error_data
                    )

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we'll create a task to handle the audit events
            context = get_current_context()
            start_time = time.time()
            operation_name = f"{func.__module__}.{func.__name__}"

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Schedule async audit events
                processing_time = (time.time() - start_time) * 1000
                asyncio.create_task(_async_audit_completion(
                    audit_event_type, operation_name, processing_time, result if capture_result else None, context
                ))

                return result

            except Exception as e:
                if capture_errors:
                    processing_time = (time.time() - start_time) * 1000
                    asyncio.create_task(_async_audit_error(
                        operation_name, processing_time, e, context
                    ))
                raise

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _async_audit_completion(event_type: AuditEventType, operation_name: str, processing_time: float, result: Any, context: Optional[EventContext]):
    """Helper to audit function completion asynchronously"""
    try:
        completion_data = {
            'operation': operation_name,
            'status': 'completed',
            'processing_time_ms': processing_time
        }

        if result is not None:
            completion_data['result'] = _sanitize_result(result)

        await create_and_stream_event(
            AuditEventType.AGENT_COMPLETED,
            AuditSeverity.INFO,
            EventPriority.NORMAL,
            context,
            **completion_data
        )
    except Exception as e:
        logger.error(f"Failed to audit completion for {operation_name}: {e}")


async def _async_audit_error(operation_name: str, processing_time: float, error: Exception, context: Optional[EventContext]):
    """Helper to audit function errors asynchronously"""
    try:
        error_data = {
            'operation': operation_name,
            'status': 'failed',
            'processing_time_ms': processing_time,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_traceback': traceback.format_exc()
        }

        await create_and_stream_event(
            AuditEventType.AGENT_FAILED,
            AuditSeverity.ERROR,
            EventPriority.HIGH,
            context,
            **error_data
        )
    except Exception as e:
        logger.error(f"Failed to audit error for {operation_name}: {e}")


def _sanitize_args(args) -> List[Any]:
    """Sanitize function arguments for logging"""
    sanitized = []
    for arg in args:
        if isinstance(arg, (str, int, float, bool, list, dict)):
            sanitized.append(_sanitize_value(arg))
        else:
            sanitized.append(f"<{type(arg).__name__} object>")
    return sanitized


def _sanitize_kwargs(kwargs) -> Dict[str, Any]:
    """Sanitize function keyword arguments for logging"""
    sanitized = {}
    sensitive_keys = {'password', 'secret', 'key', 'token', 'private_key', 'mnemonic'}

    for key, value in kwargs.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "<REDACTED>"
        elif isinstance(value, (str, int, float, bool, list, dict)):
            sanitized[key] = _sanitize_value(value)
        else:
            sanitized[key] = f"<{type(value).__name__} object>"

    return sanitized


def _sanitize_result(result) -> Any:
    """Sanitize function result for logging"""
    if isinstance(result, (str, int, float, bool)):
        return result
    elif isinstance(result, (list, tuple)):
        return [_sanitize_value(item) for item in result[:10]]  # Limit to first 10 items
    elif isinstance(result, dict):
        return _sanitize_value(result)
    else:
        return f"<{type(result).__name__} object>"


def _sanitize_value(value, max_depth=3, current_depth=0) -> Any:
    """Recursively sanitize values for logging"""
    if current_depth > max_depth:
        return "<MAX_DEPTH_REACHED>"

    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, str) and len(value) > 1000:
            return value[:1000] + "... (truncated)"
        return value
    elif isinstance(value, list):
        return [_sanitize_value(item, max_depth, current_depth + 1) for item in value[:10]]
    elif isinstance(value, dict):
        sanitized = {}
        sensitive_keys = {'password', 'secret', 'key', 'token', 'private_key', 'mnemonic'}
        for k, v in list(value.items())[:20]:  # Limit to first 20 items
            if str(k).lower() in sensitive_keys:
                sanitized[k] = "<REDACTED>"
            else:
                sanitized[k] = _sanitize_value(v, max_depth, current_depth + 1)
        return sanitized
    else:
        return f"<{type(value).__name__} object>"


# Specific hooks for different components

class LendingWorkflowHooks:
    """Hooks for lending workflow events"""

    @staticmethod
    async def loan_request_created(loan_id: str, borrower_address: str, request_data: Dict[str, Any]):
        """Hook for when a new loan request is created"""
        await create_and_stream_event(
            AuditEventType.LOAN_REQUEST_CREATED,
            AuditSeverity.INFO,
            EventPriority.NORMAL,
            loan_id=loan_id,
            borrower_address=borrower_address,
            amount_micro_algos=request_data.get('amount'),
            collateral_type=request_data.get('collateral_type'),
            duration_days=request_data.get('duration'),
            interest_rate=request_data.get('interest_rate'),
            metadata=request_data
        )

    @staticmethod
    async def loan_approved(loan_id: str, borrower_address: str, terms: Dict[str, Any]):
        """Hook for loan approval"""
        await create_and_stream_event(
            AuditEventType.LOAN_APPROVED,
            AuditSeverity.INFO,
            EventPriority.HIGH,
            loan_id=loan_id,
            borrower_address=borrower_address,
            amount_micro_algos=terms.get('amount'),
            interest_rate=terms.get('interest_rate'),
            metadata=terms
        )

    @staticmethod
    async def loan_rejected(loan_id: str, borrower_address: str, reason: str, details: Dict[str, Any]):
        """Hook for loan rejection"""
        await create_and_stream_event(
            AuditEventType.LOAN_REJECTED,
            AuditSeverity.WARNING,
            EventPriority.NORMAL,
            loan_id=loan_id,
            borrower_address=borrower_address,
            status=reason,
            metadata=details
        )

    @staticmethod
    async def loan_funded(loan_id: str, transaction_id: str, amount: int):
        """Hook for loan funding"""
        await create_and_stream_event(
            AuditEventType.LOAN_FUNDED,
            AuditSeverity.INFO,
            EventPriority.HIGH,
            loan_id=loan_id,
            transaction_id=transaction_id,
            amount_micro_algos=amount
        )


class BlockchainHooks:
    """Hooks for blockchain transaction events"""

    @staticmethod
    async def transaction_created(transaction_id: str, loan_id: str, transaction_type: str, details: Dict[str, Any]):
        """Hook for transaction creation"""
        await create_and_stream_event(
            AuditEventType.TRANSACTION_CREATED,
            AuditSeverity.INFO,
            EventPriority.NORMAL,
            transaction_id=transaction_id,
            loan_id=loan_id,
            status=transaction_type,
            metadata=details
        )

    @staticmethod
    async def transaction_confirmed(transaction_id: str, loan_id: str, block_height: int):
        """Hook for transaction confirmation"""
        await create_and_stream_event(
            AuditEventType.TRANSACTION_CONFIRMED,
            AuditSeverity.INFO,
            EventPriority.HIGH,
            transaction_id=transaction_id,
            loan_id=loan_id,
            metadata={'block_height': block_height}
        )

    @staticmethod
    async def transaction_failed(transaction_id: str, loan_id: str, error_message: str):
        """Hook for transaction failure"""
        await create_and_stream_event(
            AuditEventType.TRANSACTION_FAILED,
            AuditSeverity.ERROR,
            EventPriority.CRITICAL,
            transaction_id=transaction_id,
            loan_id=loan_id,
            error_message=error_message
        )


class EnforcementHooks:
    """Hooks for enforcement and escrow events"""

    @staticmethod
    async def escrow_deployed(escrow_id: str, loan_id: str, app_id: int, escrow_address: str):
        """Hook for escrow deployment"""
        await create_and_stream_event(
            AuditEventType.TRANSACTION_CREATED,  # Using closest available event type
            AuditSeverity.INFO,
            EventPriority.HIGH,
            loan_id=loan_id,
            status='escrow_deployed',
            metadata={
                'escrow_id': escrow_id,
                'app_id': app_id,
                'escrow_address': escrow_address
            }
        )

    @staticmethod
    async def liquidation_triggered(escrow_id: str, loan_id: str, reason: str, trigger_data: Dict[str, Any]):
        """Hook for liquidation trigger"""
        await create_and_stream_event(
            AuditEventType.SYSTEM_ERROR,  # Using closest available event type
            AuditSeverity.CRITICAL,
            EventPriority.CRITICAL,
            loan_id=loan_id,
            status='liquidation_triggered',
            metadata={
                'escrow_id': escrow_id,
                'reason': reason,
                **trigger_data
            }
        )

    @staticmethod
    async def collateral_released(escrow_id: str, loan_id: str, amount: int, recipient: str):
        """Hook for collateral release"""
        await create_and_stream_event(
            AuditEventType.TRANSACTION_CONFIRMED,
            AuditSeverity.INFO,
            EventPriority.HIGH,
            loan_id=loan_id,
            amount_micro_algos=amount,
            status='collateral_released',
            metadata={
                'escrow_id': escrow_id,
                'recipient': recipient
            }
        )


class AgentDecisionHooks:
    """Hooks for agent decision events"""

    @staticmethod
    async def decision_made(
        loan_id: str,
        decision_type: DecisionType,
        decision_maker: str,
        outcome: str,
        rationale: str,
        input_data: Dict[str, Any],
        confidence_score: Optional[float] = None,
        risk_score: Optional[float] = None
    ):
        """Hook for agent decisions"""
        # Create audit event first
        audit_event = create_loan_audit_event(
            event_type=AuditEventType.AGENT_COMPLETED,
            loan_id=loan_id,
            borrower_address=input_data.get('borrower_address', 'unknown'),
            service_name=decision_maker,
            metadata={
                'decision_type': decision_type.value,
                'outcome': outcome,
                'rationale': rationale,
                'confidence_score': confidence_score,
                'risk_score': risk_score
            }
        )

        # Stream the event
        await stream_audit_event(audit_event, EventPriority.HIGH)

        # Also create decision point for compliance
        try:
            from .audit_service import AuditService
            # This would integrate with the audit service to record the decision point
            # Implementation would depend on having an audit service instance available
        except Exception as e:
            logger.warning(f"Could not record decision point: {e}")


class SystemHooks:
    """Hooks for system-level events"""

    @staticmethod
    async def service_started(service_name: str, version: str):
        """Hook for service startup"""
        await create_and_stream_event(
            AuditEventType.SERVICE_STARTED,
            AuditSeverity.INFO,
            EventPriority.NORMAL,
            metadata={
                'service_name': service_name,
                'version': version,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

    @staticmethod
    async def service_stopped(service_name: str, reason: Optional[str] = None):
        """Hook for service shutdown"""
        await create_and_stream_event(
            AuditEventType.SERVICE_STOPPED,
            AuditSeverity.INFO,
            EventPriority.NORMAL,
            metadata={
                'service_name': service_name,
                'reason': reason or 'normal_shutdown',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

    @staticmethod
    async def configuration_changed(service_name: str, changes: Dict[str, Any]):
        """Hook for configuration changes"""
        await create_and_stream_event(
            AuditEventType.CONFIGURATION_CHANGED,
            AuditSeverity.WARNING,
            EventPriority.HIGH,
            metadata={
                'service_name': service_name,
                'changes': _sanitize_value(changes),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )


# Performance monitoring decorator

def monitor_performance(threshold_ms: float = 1000):
    """Decorator to monitor function performance and alert on slow operations"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                processing_time = (time.time() - start_time) * 1000

                if processing_time > threshold_ms:
                    await create_and_stream_event(
                        AuditEventType.SYSTEM_ERROR,
                        AuditSeverity.WARNING,
                        EventPriority.HIGH,
                        operation=f"{func.__module__}.{func.__name__}",
                        processing_time_ms=processing_time,
                        threshold_ms=threshold_ms,
                        status='performance_warning'
                    )

                return result

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                await create_and_stream_event(
                    AuditEventType.SYSTEM_ERROR,
                    AuditSeverity.ERROR,
                    EventPriority.CRITICAL,
                    operation=f"{func.__module__}.{func.__name__}",
                    processing_time_ms=processing_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    status='performance_error'
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                processing_time = (time.time() - start_time) * 1000

                if processing_time > threshold_ms:
                    asyncio.create_task(create_and_stream_event(
                        AuditEventType.SYSTEM_ERROR,
                        AuditSeverity.WARNING,
                        EventPriority.HIGH,
                        operation=f"{func.__module__}.{func.__name__}",
                        processing_time_ms=processing_time,
                        threshold_ms=threshold_ms,
                        status='performance_warning'
                    ))

                return result

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                asyncio.create_task(create_and_stream_event(
                    AuditEventType.SYSTEM_ERROR,
                    AuditSeverity.ERROR,
                    EventPriority.CRITICAL,
                    operation=f"{func.__module__}.{func.__name__}",
                    processing_time_ms=processing_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    status='performance_error'
                ))
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator