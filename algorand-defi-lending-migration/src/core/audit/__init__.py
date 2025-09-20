"""
Audit Trail and Compliance System

High-performance audit trail system designed for regulatory compliance
and operational monitoring in the Algorand lending platform.

Features:
- JSONB event storage with sub-second query performance
- Automatic partitioning for scalability
- Full-text search capabilities
- Regulatory compliance tracking
- Privacy controls and data retention
- Immutable audit trails for integrity

Usage:
    from src.core.audit import AuditTrail, DecisionPoint, ComplianceEvent
    from src.core.audit.database import setup_audit_database
"""

# Core models
from .models import (
    # Enums
    AuditEventType,
    ComplianceClassification,
    DecisionType,
    AuditSeverity,

    # Main data models
    AuditTrail,
    AuditEventData,
    DecisionPoint,
    ComplianceEvent,
    AuditSession,
    UserAuditProfile,

    # Legacy compatibility
    AuditTrailLegacy,

    # Helper functions
    create_loan_audit_event,
    create_decision_point,
    create_compliance_event,
)

# Database utilities
from .database.migrations import (
    DatabaseConfig,
    AuditDatabaseManager,
    AuditDatabaseMigrator,
    MigrationStatus,
    setup_audit_database,
    run_maintenance,
    backup_audit_data,
)

# Compliance and bias detection
from .compliance_service import (
    ComplianceService,
    ComplianceMetrics,
    InterestRateJustification,
    BiasAnalysisResult,
    BiasType,
    RegulatoryFramework,
)

from .bias_detection import (
    BiasDetector,
    FairnessResult,
    BiasTestConfig,
    FairnessMetric,
    ProtectedAttribute,
)

from .report_generator import (
    ComplianceReportGenerator,
    ReportConfiguration,
    ReportMetadata,
)

# Audit service
from .audit_service import AuditService

__version__ = "1.0.0"

__all__ = [
    # Enums
    "AuditEventType",
    "ComplianceClassification",
    "DecisionType",
    "AuditSeverity",
    "BiasType",
    "RegulatoryFramework",
    "FairnessMetric",
    "ProtectedAttribute",

    # Models
    "AuditTrail",
    "AuditEventData",
    "DecisionPoint",
    "ComplianceEvent",
    "AuditSession",
    "UserAuditProfile",
    "AuditTrailLegacy",
    "ComplianceMetrics",
    "InterestRateJustification",
    "BiasAnalysisResult",
    "FairnessResult",
    "BiasTestConfig",
    "ReportConfiguration",
    "ReportMetadata",

    # Helper functions
    "create_loan_audit_event",
    "create_decision_point",
    "create_compliance_event",

    # Database
    "DatabaseConfig",
    "AuditDatabaseManager",
    "AuditDatabaseMigrator",
    "MigrationStatus",
    "setup_audit_database",
    "run_maintenance",
    "backup_audit_data",

    # Services
    "AuditService",
    "ComplianceService",
    "BiasDetector",
    "ComplianceReportGenerator",
]