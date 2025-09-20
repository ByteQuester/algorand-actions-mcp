"""
Audit API Exception Handling

Custom exceptions and error handlers for audit trail API operations.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class AuditAPIError(Exception):
    """Base exception for audit API operations"""

    def __init__(
        self,
        message: str,
        error_code: str = "AUDIT_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(message)


class AuditAccessError(AuditAPIError):
    """Exception for audit access permission issues"""

    def __init__(self, message: str = "Access denied to audit data", **kwargs):
        super().__init__(
            message=message,
            error_code="AUDIT_ACCESS_DENIED",
            status_code=403,
            **kwargs
        )


class AuditNotFoundError(AuditAPIError):
    """Exception for audit data not found"""

    def __init__(self, message: str = "Audit data not found", **kwargs):
        super().__init__(
            message=message,
            error_code="AUDIT_NOT_FOUND",
            status_code=404,
            **kwargs
        )


class AuditServiceError(AuditAPIError):
    """Exception for audit service internal errors"""

    def __init__(self, message: str = "Audit service error", **kwargs):
        super().__init__(
            message=message,
            error_code="AUDIT_SERVICE_ERROR",
            status_code=500,
            **kwargs
        )


class AuditDatabaseError(AuditAPIError):
    """Exception for audit database connection/query issues"""

    def __init__(self, message: str = "Database operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUDIT_DATABASE_ERROR",
            status_code=503,
            **kwargs
        )


class AuditValidationError(AuditAPIError):
    """Exception for audit request validation issues"""

    def __init__(self, message: str = "Request validation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUDIT_VALIDATION_ERROR",
            status_code=400,
            **kwargs
        )


class AuditRateLimitError(AuditAPIError):
    """Exception for audit API rate limiting"""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            message=message,
            error_code="AUDIT_RATE_LIMIT",
            status_code=429,
            **kwargs
        )


# Response Models

class ErrorDetail(BaseModel):
    """Individual error detail"""
    field: Optional[str] = None
    code: str
    message: str
    context: Optional[Dict[str, Any]] = None


class AuditErrorResponse(BaseModel):
    """Standardized audit error response"""
    success: bool = False
    error_code: str
    message: str
    timestamp: str
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[ErrorDetail]] = None
    support_reference: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditOperationResult(BaseModel):
    """Result wrapper for audit operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[AuditErrorResponse] = None
    metadata: Optional[Dict[str, Any]] = None


# Error Handler Utilities

def generate_support_reference(error: AuditAPIError, request_info: Optional[Dict[str, Any]] = None) -> str:
    """Generate support reference for error tracking"""
    timestamp = error.timestamp.strftime("%Y%m%d-%H%M%S")
    error_hash = abs(hash(f"{error.error_code}:{error.message}")) % 10000
    return f"AUD-{timestamp}-{error_hash:04d}"


def sanitize_error_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize error details to remove sensitive information"""
    sensitive_keys = ['password', 'token', 'secret', 'key', 'private']

    def _sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in d.items():
            # Check if key contains sensitive terms
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = _sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [_sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        return sanitized

    return _sanitize_dict(details)


def create_error_response(
    error: AuditAPIError,
    request_id: Optional[str] = None,
    include_stack_trace: bool = False
) -> AuditErrorResponse:
    """Create standardized error response"""

    # Sanitize error details
    details = sanitize_error_details(error.details) if error.details else None

    # Add stack trace in development mode
    if include_stack_trace and details is not None:
        import traceback
        details["stack_trace"] = traceback.format_exc()

    # Generate support reference
    support_ref = generate_support_reference(error)

    return AuditErrorResponse(
        error_code=error.error_code,
        message=error.message,
        timestamp=error.timestamp.isoformat(),
        request_id=request_id,
        details=details,
        support_reference=support_ref
    )


# Exception Handlers

async def audit_api_exception_handler(request: Request, exc: AuditAPIError) -> JSONResponse:
    """Handle custom audit API exceptions"""
    try:
        # Log the error
        logger.error(
            f"Audit API Error: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "request_url": str(request.url),
                "request_method": request.method,
                "timestamp": exc.timestamp.isoformat()
            }
        )

        # Get request ID if available
        request_id = request.headers.get("X-Request-ID")

        # Determine if we should include stack trace
        include_trace = request.headers.get("X-Debug-Mode") == "true"

        # Create error response
        error_response = create_error_response(exc, request_id, include_trace)

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )

    except Exception as handler_error:
        # Fallback error handling
        logger.critical(f"Error in audit exception handler: {handler_error}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "HANDLER_ERROR",
                "message": "Internal error handler failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "support_reference": "CRITICAL-ERROR"
            }
        )


async def audit_database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle database-related exceptions"""
    logger.error(f"Database error in audit API: {exc}")

    # Convert to audit database error
    audit_error = AuditDatabaseError(
        message="Database operation failed",
        details={"original_error": str(exc)}
    )

    return await audit_api_exception_handler(request, audit_error)


async def audit_validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation-related exceptions"""
    logger.warning(f"Validation error in audit API: {exc}")

    # Convert to audit validation error
    audit_error = AuditValidationError(
        message="Request validation failed",
        details={"validation_error": str(exc)}
    )

    return await audit_api_exception_handler(request, audit_error)


# Decorators for Error Handling

def handle_audit_exceptions(func):
    """Decorator to handle common audit exceptions"""
    import functools
    import asyncio

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AuditAPIError:
            # Re-raise custom audit errors
            raise
        except ConnectionError as e:
            raise AuditDatabaseError(f"Database connection failed: {str(e)}")
        except TimeoutError as e:
            raise AuditServiceError(f"Operation timeout: {str(e)}")
        except ValueError as e:
            raise AuditValidationError(f"Invalid input: {str(e)}")
        except PermissionError as e:
            raise AuditAccessError(f"Permission denied: {str(e)}")
        except Exception as e:
            # Catch-all for unexpected errors
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            raise AuditServiceError(
                message=f"Unexpected error in {func.__name__}",
                details={"original_error": str(e)}
            )

    return wrapper


# Context Managers for Error Handling

class AuditOperationContext:
    """Context manager for audit operations with error handling"""

    def __init__(self, operation_name: str, user_id: Optional[str] = None):
        self.operation_name = operation_name
        self.user_id = user_id
        self.start_time = None
        self.end_time = None

    async def __aenter__(self):
        self.start_time = datetime.now(timezone.utc)
        logger.info(f"Starting audit operation: {self.operation_name}", extra={
            "operation": self.operation_name,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat()
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now(timezone.utc)
        duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        if exc_type is None:
            # Success
            logger.info(f"Completed audit operation: {self.operation_name}", extra={
                "operation": self.operation_name,
                "user_id": self.user_id,
                "duration_ms": duration_ms,
                "status": "success"
            })
        else:
            # Error
            logger.error(f"Failed audit operation: {self.operation_name}", extra={
                "operation": self.operation_name,
                "user_id": self.user_id,
                "duration_ms": duration_ms,
                "status": "error",
                "error_type": exc_type.__name__,
                "error_message": str(exc_val)
            })

            # Convert to audit error if needed
            if not isinstance(exc_val, AuditAPIError):
                return False  # Re-raise as audit service error

        return False  # Don't suppress exceptions


# Metrics and Monitoring

class AuditMetrics:
    """Metrics collection for audit operations"""

    def __init__(self):
        self.operation_counts = {}
        self.error_counts = {}
        self.response_times = {}

    def record_operation(self, operation: str, duration_ms: float, success: bool):
        """Record operation metrics"""
        if operation not in self.operation_counts:
            self.operation_counts[operation] = {"success": 0, "error": 0}
            self.response_times[operation] = []

        if success:
            self.operation_counts[operation]["success"] += 1
        else:
            self.operation_counts[operation]["error"] += 1

        self.response_times[operation].append(duration_ms)

    def record_error(self, error_code: str):
        """Record error occurrence"""
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {
            "operations": self.operation_counts,
            "errors": self.error_counts,
            "avg_response_times": {}
        }

        for operation, times in self.response_times.items():
            if times:
                summary["avg_response_times"][operation] = sum(times) / len(times)

        return summary


# Global metrics instance
audit_metrics = AuditMetrics()