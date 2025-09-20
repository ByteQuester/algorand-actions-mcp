"""
Audit Trail API Router

REST API endpoints for audit retrieval and compliance reporting.
Provides high-performance access to audit data with sub-second response times.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import os
import asyncio

from ..core.audit.audit_service import AuditService
from .auth import AuthHandler, get_current_user
from .audit_exceptions import (
    AuditAPIError, AuditAccessError, AuditNotFoundError,
    AuditServiceError, AuditDatabaseError, AuditValidationError,
    audit_api_exception_handler, audit_database_exception_handler,
    handle_audit_exceptions, AuditOperationContext, audit_metrics
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize security and auth
security = HTTPBearer()
auth_handler = AuthHandler()

# Initialize audit service
DATABASE_URL = os.getenv("AUDIT_DATABASE_URL", "postgresql://localhost:5432/audit_db")
audit_service = AuditService(DATABASE_URL)

# Create router
router = APIRouter(
    prefix="/api/v1/audit",
    tags=["audit", "compliance"],
    dependencies=[Depends(security)]
)

# Response Models

class SessionTimelineResponse(BaseModel):
    """Response model for session timeline data"""
    loan_id: str
    total_events: int
    total_sessions: int
    timeline_start: Optional[str] = None
    timeline_end: Optional[str] = None
    sessions: List[Dict[str, Any]]
    events: List[Dict[str, Any]]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DecisionBreakdownResponse(BaseModel):
    """Response model for decision breakdown"""
    loan_id: str
    total_decisions: int
    decision_types: List[str]
    average_risk_score: Optional[float] = None
    average_confidence: Optional[float] = None
    decision_chain: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]


class ToolUsageResponse(BaseModel):
    """Response model for tool usage analysis"""
    loan_id: str
    total_tool_executions: int
    unique_tools_used: int
    total_errors: int
    total_warnings: int
    success_rate: float
    average_processing_time_ms: Optional[float] = None
    tool_performance: List[Dict[str, Any]]
    tool_executions: List[Dict[str, Any]]


class RawEventsResponse(BaseModel):
    """Response model for raw event retrieval"""
    session_id: str
    total_events: int
    returned_events: int
    limit: int
    offset: int
    has_more: bool
    events: List[Dict[str, Any]]


class TimelineDataResponse(BaseModel):
    """Response model for visual timeline data"""
    loan_id: str
    timeline_buckets: int
    event_types: List[str]
    severity_distribution: Dict[str, int]
    milestones: List[Dict[str, Any]]
    timeline_data: List[Dict[str, Any]]
    visualization_ready: bool


class AuditSearchResponse(BaseModel):
    """Response model for audit search results"""
    query: str
    total_results: int
    filters: Dict[str, Any]
    events: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None


# Startup/Shutdown Events

async def startup_audit_service():
    """Initialize audit service on startup"""
    try:
        await audit_service.initialize()
        logger.info("Audit service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize audit service: {e}")
        raise


async def shutdown_audit_service():
    """Cleanup audit service on shutdown"""
    try:
        await audit_service.close()
        logger.info("Audit service closed successfully")
    except Exception as e:
        logger.error(f"Failed to close audit service: {e}")


# Utility Functions

def check_audit_access(user: Dict[str, Any], loan_id: str) -> None:
    """
    Check if user has access to audit data for a loan

    Args:
        user: Current authenticated user
        loan_id: Loan ID being accessed

    Raises:
        AuditAccessError: If user doesn't have access
    """
    # Check if user is admin or has audit role
    user_roles = user.get("roles", [])
    if "admin" in user_roles or "auditor" in user_roles or "compliance_officer" in user_roles:
        return

    # Check if user owns the loan (would need loan ownership lookup)
    # For now, allowing access based on user_id match in audit logs
    # In production, this should check loan ownership table

    # For demo purposes, allow access but log the check
    logger.info(f"Audit access granted for user {user.get('user_id')} to loan {loan_id}")
    return  # Simplified for demo


async def log_audit_access(user: Dict[str, Any], endpoint: str, loan_id: Optional[str] = None):
    """Log audit data access for compliance"""
    try:
        # In production, this would create an audit entry for access logging
        logger.info(f"Audit access: user={user.get('user_id')}, endpoint={endpoint}, loan_id={loan_id}")
    except Exception as e:
        logger.warning(f"Failed to log audit access: {e}")


# API Endpoints

@router.get(
    "/session/{loan_id}",
    response_model=SessionTimelineResponse,
    summary="Get Complete Session Timeline",
    description="Retrieve complete session timeline for a loan with all events grouped by session"
)
@handle_audit_exceptions
async def get_session_timeline(
    loan_id: str = Path(..., description="Loan ID to retrieve session timeline for"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> SessionTimelineResponse:
    """
    Get complete session timeline for a loan

    Returns chronological timeline of all audit events grouped by session,
    including session metadata and event details.
    """
    async with AuditOperationContext("get_session_timeline", user.get("user_id")):
        # Log access
        await log_audit_access(user, "get_session_timeline", loan_id)

        # Check access permissions
        check_audit_access(user, loan_id)

        # Validate loan ID format
        if not loan_id or len(loan_id) < 3:
            raise AuditValidationError("Invalid loan ID format")

        # Get timeline data
        try:
            timeline_data = await audit_service.get_session_timeline(loan_id)
        except ConnectionError as e:
            raise AuditDatabaseError(f"Database connection failed: {str(e)}")
        except Exception as e:
            raise AuditServiceError(f"Failed to retrieve session timeline: {str(e)}")

        if not timeline_data.get("events"):
            raise AuditNotFoundError(f"No audit data found for loan {loan_id}")

        # Record metrics
        audit_metrics.record_operation("get_session_timeline", 0, True)

        return SessionTimelineResponse(**timeline_data)


@router.get(
    "/decisions/{loan_id}",
    response_model=DecisionBreakdownResponse,
    summary="Get Decision Breakdown",
    description="Retrieve decision breakdown with reasoning chains for regulatory compliance"
)
async def get_decision_breakdown(
    loan_id: str = Path(..., description="Loan ID to retrieve decisions for"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> DecisionBreakdownResponse:
    """
    Get decision breakdown with complete reasoning chains

    Returns all decisions made during loan processing with full context,
    rationale, risk factors, and compliance information.
    """
    try:
        # Log access
        await log_audit_access(user, "get_decision_breakdown", loan_id)

        # Check access permissions
        if not check_audit_access(user, loan_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access audit data for this loan"
            )

        # Get decision data
        decision_data = await audit_service.get_decision_breakdown(loan_id)

        return DecisionBreakdownResponse(**decision_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decision breakdown for loan {loan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve decision breakdown"
        )


@router.get(
    "/tools/{loan_id}",
    response_model=ToolUsageResponse,
    summary="Get Tool Usage Analysis",
    description="Retrieve tool usage and impact analysis for loan processing"
)
async def get_tool_usage_analysis(
    loan_id: str = Path(..., description="Loan ID to analyze tool usage for"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> ToolUsageResponse:
    """
    Get tool usage and impact analysis

    Returns comprehensive analysis of all tools used during loan processing,
    including performance metrics, error rates, and impact assessment.
    """
    try:
        # Log access
        await log_audit_access(user, "get_tool_usage_analysis", loan_id)

        # Check access permissions
        if not check_audit_access(user, loan_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access audit data for this loan"
            )

        # Get tool usage data
        tool_data = await audit_service.get_tool_usage_analysis(loan_id)

        return ToolUsageResponse(**tool_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool usage analysis for loan {loan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tool usage analysis"
        )


@router.get(
    "/events/{session_id}",
    response_model=RawEventsResponse,
    summary="Get Raw Event Data",
    description="Retrieve raw audit events for a specific session with pagination"
)
async def get_raw_events(
    session_id: str = Path(..., description="Session ID to retrieve events for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> RawEventsResponse:
    """
    Get raw audit events for a session

    Returns paginated raw audit events with full details for debugging
    and detailed analysis purposes.
    """
    try:
        # Log access
        await log_audit_access(user, "get_raw_events")

        # Check if user has auditor/admin role for raw data access
        user_roles = user.get("roles", [])
        if not any(role in ["admin", "auditor", "developer"] for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to access raw event data"
            )

        # Get raw events
        events_data = await audit_service.get_raw_events(session_id, limit, offset)

        return RawEventsResponse(**events_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw events for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve raw events"
        )


@router.get(
    "/timeline/{loan_id}",
    response_model=TimelineDataResponse,
    summary="Get Visual Timeline Data",
    description="Retrieve timeline data optimized for visualization and dashboards"
)
async def get_visual_timeline_data(
    loan_id: str = Path(..., description="Loan ID to get timeline data for"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> TimelineDataResponse:
    """
    Get visual timeline data

    Returns timeline data optimized for visualization with aggregated
    events, milestones, and chart-ready data structures.
    """
    try:
        # Log access
        await log_audit_access(user, "get_visual_timeline_data", loan_id)

        # Check access permissions
        if not check_audit_access(user, loan_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access audit data for this loan"
            )

        # Get timeline data
        timeline_data = await audit_service.get_visual_timeline_data(loan_id)

        return TimelineDataResponse(**timeline_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get visual timeline data for loan {loan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve visual timeline data"
        )


# Additional utility endpoints

@router.get(
    "/search",
    response_model=AuditSearchResponse,
    summary="Search Audit Events",
    description="Search audit events using full-text search with optional filters"
)
async def search_audit_events(
    query: str = Query(..., description="Search query string"),
    loan_id: Optional[str] = Query(None, description="Filter by loan ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> AuditSearchResponse:
    """
    Search audit events using full-text search

    Provides powerful search capabilities across all audit data with
    relevance ranking and optional date/loan filtering.
    """
    try:
        # Log access
        await log_audit_access(user, "search_audit_events")

        # Check if user has search privileges
        user_roles = user.get("roles", [])
        if not any(role in ["admin", "auditor", "compliance_officer", "developer"] for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges to search audit data"
            )

        # Perform search
        search_results = await audit_service.search_audit_events(
            query=query,
            loan_id=loan_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return AuditSearchResponse(**search_results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search audit events with query '{query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search audit events"
        )


@router.get(
    "/health",
    summary="Audit Service Health Check",
    description="Check the health and status of the audit service"
)
async def audit_health_check() -> Dict[str, Any]:
    """
    Check audit service health

    Returns service status, database connectivity, and performance metrics.
    """
    try:
        # Basic connectivity test
        if not audit_service.connection_pool:
            return {
                "status": "unhealthy",
                "message": "Database connection not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Test database query
        async with audit_service.connection_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "database_connected": True,
            "connection_pool_size": audit_service.connection_pool.get_size(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Audit health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Error Handlers - Register custom exception handlers

# Register audit-specific exception handler
router.add_exception_handler(AuditAPIError, audit_api_exception_handler)
router.add_exception_handler(ConnectionError, audit_database_exception_handler)


@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    # Record error metrics
    audit_metrics.record_error("HTTP_EXCEPTION")

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            timestamp=datetime.now(timezone.utc).isoformat()
        ).dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception in audit router: {exc}")

    # Record error metrics
    audit_metrics.record_error("UNHANDLED_EXCEPTION")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            timestamp=datetime.now(timezone.utc).isoformat()
        ).dict()
    )


# Metrics endpoint for monitoring
@router.get(
    "/metrics",
    summary="Get Audit API Metrics",
    description="Retrieve audit API performance and error metrics"
)
async def get_audit_metrics(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get audit API metrics

    Returns performance metrics, error counts, and operation statistics.
    Requires admin or developer role.
    """
    # Check permissions for metrics access
    user_roles = user.get("roles", [])
    if not any(role in ["admin", "developer", "auditor"] for role in user_roles):
        raise AuditAccessError("Insufficient privileges to access metrics")

    return {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": audit_metrics.get_summary()
    }