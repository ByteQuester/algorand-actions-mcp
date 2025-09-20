"""
Audit Trail and Compliance Data Models

High-performance data models for audit trails, compliance tracking, and regulatory reporting.
Designed to handle millions of entries with sub-second query performance.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Literal
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
import json
from pydantic import BaseModel, Field, ConfigDict, validator, root_validator
from pydantic.types import Json


class AuditEventType(Enum):
    """Types of audit events that can be recorded"""
    # Lending Operations
    LOAN_REQUEST_CREATED = "loan_request_created"
    LOAN_REQUEST_UPDATED = "loan_request_updated"
    LOAN_APPROVED = "loan_approved"
    LOAN_REJECTED = "loan_rejected"
    LOAN_FUNDED = "loan_funded"
    LOAN_REPAID = "loan_repaid"
    LOAN_DEFAULTED = "loan_defaulted"

    # Authentication & Authorization
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"

    # Blockchain Operations
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_SIGNED = "transaction_signed"
    TRANSACTION_SUBMITTED = "transaction_submitted"
    TRANSACTION_CONFIRMED = "transaction_confirmed"
    TRANSACTION_FAILED = "transaction_failed"

    # Agent Operations
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    TOOL_EXECUTED = "tool_executed"

    # Data Operations
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_ACCESSED = "data_accessed"

    # Compliance Events
    COMPLIANCE_CHECK = "compliance_check"
    REGULATORY_REPORT = "regulatory_report"
    PRIVACY_ACCESS = "privacy_access"
    DATA_EXPORT = "data_export"

    # System Events
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGED = "configuration_changed"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"


class ComplianceClassification(Enum):
    """Regulatory classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class DecisionType(Enum):
    """Types of lending decisions"""
    RISK_ASSESSMENT = "risk_assessment"
    CREDIT_APPROVAL = "credit_approval"
    COLLATERAL_EVALUATION = "collateral_evaluation"
    INTEREST_RATE_DETERMINATION = "interest_rate_determination"
    LOAN_TERMS_NEGOTIATION = "loan_terms_negotiation"
    DEFAULT_DETERMINATION = "default_determination"
    LIQUIDATION_TRIGGER = "liquidation_trigger"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Pydantic Models for Validation and Serialization

class AuditEventData(BaseModel):
    """Flexible container for event-specific data"""
    model_config = ConfigDict(
        extra='allow',  # Allow additional fields for flexibility
        validate_assignment=True,
        frozen=True  # Immutability for audit integrity
    )

    # Common fields that many events will have
    transaction_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Business object identifiers
    loan_id: Optional[str] = None
    borrower_address: Optional[str] = None
    lender_address: Optional[str] = None

    # Amounts and values
    amount_micro_algos: Optional[int] = None
    interest_rate: Optional[float] = None

    # Status and results
    status: Optional[str] = None
    result: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Performance metrics
    processing_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    # Additional context
    metadata: Optional[Dict[str, Any]] = None


class AuditTrail(BaseModel):
    """Main audit trail entry with full event details"""
    model_config = ConfigDict(
        frozen=True,  # Immutable for audit integrity
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )

    # Primary identifiers
    id: UUID = Field(default_factory=uuid4)
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO

    # Temporal information
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_start: Optional[datetime] = None

    # Event details
    event_data: AuditEventData

    # Security and compliance
    classification: ComplianceClassification = ComplianceClassification.INTERNAL
    requires_retention: bool = True
    retention_days: int = 2555  # 7 years default

    # Traceability
    correlation_id: Optional[str] = None
    parent_event_id: Optional[UUID] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    # Source information
    service_name: str
    service_version: str
    environment: str = "production"

    # Integrity
    checksum: Optional[str] = None  # For tamper detection

    @validator('timestamp', pre=True)
    def ensure_utc_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @validator('event_data', pre=True)
    def validate_event_data(cls, v):
        if isinstance(v, dict):
            return AuditEventData(**v)
        return v

    def to_json(self) -> str:
        """Convert to JSON string for storage"""
        return self.model_dump_json(exclude_none=True)

    @classmethod
    def from_json(cls, json_str: str) -> 'AuditTrail':
        """Create from JSON string"""
        return cls.model_validate_json(json_str)


class DecisionPoint(BaseModel):
    """Key lending decisions for regulatory compliance"""
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )

    # Identifiers
    id: UUID = Field(default_factory=uuid4)
    decision_type: DecisionType

    # Business context
    loan_id: str
    borrower_address: str
    lender_address: Optional[str] = None

    # Decision details
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_maker: str  # Agent or system component
    decision_rationale: str
    decision_outcome: str

    # Input data (what information was considered)
    input_data: Dict[str, Any]

    # Risk and compliance
    risk_factors: List[str] = Field(default_factory=list)
    compliance_flags: List[str] = Field(default_factory=list)
    regulatory_requirements: List[str] = Field(default_factory=list)

    # Quantitative measures
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Audit trail reference
    audit_event_id: UUID

    @validator('decision_timestamp', pre=True)
    def ensure_utc_timezone(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class ComplianceEvent(BaseModel):
    """Regulatory and compliance tracking"""
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )

    # Identifiers
    id: UUID = Field(default_factory=uuid4)
    event_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Regulatory context
    regulation_type: str  # e.g., "KYC", "AML", "GDPR", "SOX"
    compliance_rule: str
    jurisdiction: str = "US"  # Default jurisdiction

    # Business context
    loan_id: Optional[str] = None
    user_id: Optional[str] = None
    transaction_id: Optional[str] = None

    # Compliance status
    compliance_status: Literal["compliant", "non_compliant", "pending", "exempt"]
    violation_details: Optional[str] = None
    remediation_required: bool = False
    remediation_steps: List[str] = Field(default_factory=list)

    # Evidence and documentation
    evidence_references: List[str] = Field(default_factory=list)
    documentation_links: List[str] = Field(default_factory=list)

    # Review and approval
    reviewed_by: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    # Audit trail reference
    audit_event_id: UUID

    @validator('event_timestamp', 'review_timestamp', 'approval_timestamp', pre=True)
    def ensure_utc_timezone(cls, v):
        if v is not None and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AuditSession(BaseModel):
    """Session management for audit trails"""
    model_config = ConfigDict(
        validate_assignment=True
    )

    # Identifiers
    session_id: str
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Session lifecycle
    session_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_end: Optional[datetime] = None
    session_duration_ms: Optional[int] = None

    # Session context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    authentication_method: Optional[str] = None

    # Activity tracking
    event_count: int = 0
    error_count: int = 0
    warning_count: int = 0

    # Business metrics
    loans_processed: int = 0
    transactions_created: int = 0
    decisions_made: int = 0

    # Session status
    is_active: bool = True
    termination_reason: Optional[str] = None

    @validator('session_start', 'session_end', pre=True)
    def ensure_utc_timezone(cls, v):
        if v is not None and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    def end_session(self, reason: Optional[str] = None):
        """End the audit session"""
        self.session_end = datetime.now(timezone.utc)
        self.is_active = False
        self.termination_reason = reason
        if self.session_end and self.session_start:
            delta = self.session_end - self.session_start
            self.session_duration_ms = int(delta.total_seconds() * 1000)


class UserAuditProfile(BaseModel):
    """User privacy and audit preferences"""
    model_config = ConfigDict(
        validate_assignment=True
    )

    # User identification
    user_id: str
    algorand_address: Optional[str] = None

    # Privacy controls
    data_retention_days: int = 2555  # 7 years default
    audit_level: Literal["minimal", "standard", "detailed", "comprehensive"] = "standard"

    # Data sharing preferences
    allow_analytics: bool = True
    allow_third_party_sharing: bool = False

    # Geographic and regulatory
    jurisdiction: str = "US"
    gdpr_subject: bool = False
    ccpa_subject: bool = False

    # Consent tracking
    privacy_policy_version: str
    consent_timestamp: datetime
    consent_withdrawn: bool = False
    withdrawal_timestamp: Optional[datetime] = None

    # Profile metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    @validator('consent_timestamp', 'withdrawal_timestamp', 'created_at', 'updated_at', pre=True)
    def ensure_utc_timezone(cls, v):
        if v is not None and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


# Legacy dataclass models for backward compatibility

@dataclass(frozen=True)
class AuditTrailLegacy:
    """Legacy dataclass version for backward compatibility"""
    id: str
    event_type: str
    timestamp: datetime
    event_data: Dict[str, Any]
    service_name: str
    severity: str = "info"
    classification: str = "internal"
    correlation_id: Optional[str] = None

    def to_pydantic(self) -> AuditTrail:
        """Convert to Pydantic model"""
        return AuditTrail(
            id=UUID(self.id) if isinstance(self.id, str) else self.id,
            event_type=AuditEventType(self.event_type),
            timestamp=self.timestamp,
            event_data=AuditEventData(**self.event_data),
            service_name=self.service_name,
            service_version="1.0.0",  # Default
            severity=AuditSeverity(self.severity),
            classification=ComplianceClassification(self.classification),
            correlation_id=self.correlation_id
        )


# Helper functions for model creation

def create_loan_audit_event(
    event_type: AuditEventType,
    loan_id: str,
    borrower_address: str,
    service_name: str,
    lender_address: Optional[str] = None,
    amount_micro_algos: Optional[int] = None,
    interest_rate: Optional[float] = None,
    **additional_data
) -> AuditTrail:
    """Create a standardized loan-related audit event"""
    event_data = AuditEventData(
        loan_id=loan_id,
        borrower_address=borrower_address,
        lender_address=lender_address,
        amount_micro_algos=amount_micro_algos,
        interest_rate=interest_rate,
        **additional_data
    )

    return AuditTrail(
        event_type=event_type,
        event_data=event_data,
        service_name=service_name,
        service_version="1.0.0",
        classification=ComplianceClassification.CONFIDENTIAL
    )


def create_decision_point(
    decision_type: DecisionType,
    loan_id: str,
    borrower_address: str,
    decision_maker: str,
    decision_rationale: str,
    decision_outcome: str,
    input_data: Dict[str, Any],
    audit_event: AuditTrail,
    **additional_fields
) -> DecisionPoint:
    """Create a standardized decision point"""
    return DecisionPoint(
        decision_type=decision_type,
        loan_id=loan_id,
        borrower_address=borrower_address,
        decision_maker=decision_maker,
        decision_rationale=decision_rationale,
        decision_outcome=decision_outcome,
        input_data=input_data,
        audit_event_id=audit_event.id,
        **additional_fields
    )


def create_compliance_event(
    regulation_type: str,
    compliance_rule: str,
    compliance_status: Literal["compliant", "non_compliant", "pending", "exempt"],
    audit_event: AuditTrail,
    jurisdiction: str = "US",
    **additional_fields
) -> ComplianceEvent:
    """Create a standardized compliance event"""
    return ComplianceEvent(
        regulation_type=regulation_type,
        compliance_rule=compliance_rule,
        compliance_status=compliance_status,
        jurisdiction=jurisdiction,
        audit_event_id=audit_event.id,
        **additional_fields
    )