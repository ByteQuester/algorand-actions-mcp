#!/usr/bin/env python3
"""
Example usage of the Audit Trail & Compliance System

Demonstrates the key features and usage patterns of the audit system.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from models import (
    AuditTrail,
    AuditEventType,
    DecisionType,
    ComplianceClassification,
    create_loan_audit_event,
    create_decision_point,
    create_compliance_event,
)


def example_basic_audit_trail():
    """Basic audit trail creation and serialization"""
    print("=== Basic Audit Trail Example ===")

    # Create a loan approval audit event
    audit_event = create_loan_audit_event(
        event_type=AuditEventType.LOAN_APPROVED,
        loan_id="loan_12345",
        borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        service_name="lending-agent-v1",
        lender_address="5XVUDPZNLZRXG3RKL2QMJV4O2MHGF7CVLKGJZQUWQXDX7MRCJM6EQKN2ZY",
        amount_micro_algos=5000000,  # 5 ALGO
        interest_rate=8.5,
        processing_time_ms=250.5
    )

    print(f"Event ID: {audit_event.id}")
    print(f"Event Type: {audit_event.event_type.value}")
    print(f"Classification: {audit_event.classification.value}")
    print(f"Loan ID: {audit_event.event_data.loan_id}")
    print(f"Amount: {audit_event.event_data.amount_micro_algos / 1_000_000} ALGO")

    # Serialize to JSON
    json_data = audit_event.to_json()
    print(f"JSON size: {len(json_data)} bytes")

    # Deserialize from JSON
    restored_event = AuditTrail.from_json(json_data)
    print(f"Restored event ID: {restored_event.id}")

    return audit_event


def example_decision_tracking(audit_event: AuditTrail):
    """Decision point tracking for regulatory compliance"""
    print("\n=== Decision Tracking Example ===")

    decision = create_decision_point(
        decision_type=DecisionType.CREDIT_APPROVAL,
        loan_id="loan_12345",
        borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        decision_maker="risk-assessment-agent-v2.1",
        decision_rationale="Credit score 750 above minimum threshold 650. Collateral ratio 1.5x meets requirement. No previous defaults on record.",
        decision_outcome="approved",
        input_data={
            "credit_score": 750,
            "required_minimum_score": 650,
            "collateral_ratio": 1.5,
            "required_collateral_ratio": 1.2,
            "previous_defaults": 0,
            "debt_to_income_ratio": 0.28,
            "loan_to_value_ratio": 0.67,
            "employment_verified": True,
            "income_verified": True,
            "algorand_balance_algo": 125.5,
            "usdc_balance": 2500.0
        },
        audit_event=audit_event,
        confidence_score=0.92,
        risk_score=15.3,
        risk_factors=[
            "Young borrower profile (age 24)",
            "Limited credit history (2 years)"
        ],
        compliance_flags=[],
        regulatory_requirements=[
            "Fair Credit Reporting Act compliance",
            "Truth in Lending Act disclosure"
        ]
    )

    print(f"Decision ID: {decision.id}")
    print(f"Decision Type: {decision.decision_type.value}")
    print(f"Confidence: {decision.confidence_score:.1%}")
    print(f"Risk Score: {decision.risk_score}/100")
    print(f"Risk Factors: {len(decision.risk_factors)}")

    return decision


def example_compliance_tracking(audit_event: AuditTrail):
    """Compliance event tracking for regulatory requirements"""
    print("\n=== Compliance Tracking Example ===")

    # KYC compliance event
    kyc_event = create_compliance_event(
        regulation_type="KYC",
        compliance_rule="Customer Identity Verification",
        compliance_status="compliant",
        audit_event=audit_event,
        jurisdiction="US",
        loan_id="loan_12345",
        user_id="user_987654",
        evidence_references=[
            "identity_doc_scan_20240916_001.pdf",
            "address_verification_20240916_001.json",
            "biometric_match_score_0.98.json"
        ],
        documentation_links=[
            "https://compliance.example.com/kyc/user_987654/verification",
            "https://audit.example.com/evidence/identity_20240916"
        ]
    )

    print(f"Compliance Event ID: {kyc_event.id}")
    print(f"Regulation: {kyc_event.regulation_type}")
    print(f"Status: {kyc_event.compliance_status}")
    print(f"Evidence Count: {len(kyc_event.evidence_references)}")

    # AML compliance event with violation example
    aml_event = create_compliance_event(
        regulation_type="AML",
        compliance_rule="Suspicious Activity Monitoring",
        compliance_status="non_compliant",
        audit_event=audit_event,
        jurisdiction="US",
        loan_id="loan_12345",
        violation_details="Multiple large transactions from high-risk jurisdiction detected within 24 hours",
        remediation_required=True,
        remediation_steps=[
            "Enhanced due diligence review required",
            "Source of funds documentation needed",
            "Compliance officer approval mandatory",
            "File Suspicious Activity Report (SAR) if confirmed"
        ]
    )

    print(f"AML Event ID: {aml_event.id}")
    print(f"Violation: {aml_event.violation_details}")
    print(f"Remediation Required: {aml_event.remediation_required}")
    print(f"Remediation Steps: {len(aml_event.remediation_steps)}")

    return kyc_event, aml_event


def example_session_management():
    """Audit session management for grouping related events"""
    print("\n=== Session Management Example ===")

    from models import AuditSession

    session = AuditSession(
        session_id=f"session_{uuid4()}",
        user_id="user_987654",
        ip_address="192.168.1.100",
        user_agent="LendingPlatform/1.0.0 (iOS 17.0; iPhone14)",
        authentication_method="oauth2_pkce"
    )

    print(f"Session ID: {session.session_id}")
    print(f"Started: {session.session_start}")
    print(f"User: {session.user_id}")
    print(f"Active: {session.is_active}")

    # Simulate session activity
    session.event_count = 15
    session.error_count = 1
    session.loans_processed = 3
    session.transactions_created = 6

    # End session
    session.end_session("user_logout")

    print(f"Session Ended: {session.session_end}")
    print(f"Duration: {session.session_duration_ms}ms")
    print(f"Events: {session.event_count}")
    print(f"Loans Processed: {session.loans_processed}")

    return session


def example_privacy_profile():
    """User privacy profile for GDPR/CCPA compliance"""
    print("\n=== Privacy Profile Example ===")

    from models import UserAuditProfile

    profile = UserAuditProfile(
        user_id="user_987654",
        algorand_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        audit_level="detailed",
        data_retention_days=2190,  # 6 years instead of default 7
        allow_analytics=True,
        allow_third_party_sharing=False,
        jurisdiction="US",
        gdpr_subject=False,
        ccpa_subject=True,
        privacy_policy_version="2.1.0",
        consent_timestamp=datetime.now(timezone.utc)
    )

    print(f"User: {profile.user_id}")
    print(f"Audit Level: {profile.audit_level}")
    print(f"Retention: {profile.data_retention_days} days")
    print(f"CCPA Subject: {profile.ccpa_subject}")
    print(f"Analytics Allowed: {profile.allow_analytics}")
    print(f"3rd Party Sharing: {profile.allow_third_party_sharing}")

    return profile


def example_high_volume_simulation():
    """Simulate high-volume audit event creation"""
    print("\n=== High Volume Simulation ===")

    events = []
    event_types = [
        AuditEventType.LOAN_REQUEST_CREATED,
        AuditEventType.LOAN_APPROVED,
        AuditEventType.LOAN_FUNDED,
        AuditEventType.TRANSACTION_CREATED,
        AuditEventType.AGENT_INVOKED
    ]

    start_time = datetime.now()

    for i in range(1000):
        event_type = event_types[i % len(event_types)]
        loan_id = f"loan_{10000 + i}"

        audit_event = create_loan_audit_event(
            event_type=event_type,
            loan_id=loan_id,
            borrower_address=f"BORROWER{i:06d}ABCDEFGHIJKLMNOPQRSTUVWXYZ234567890123",
            service_name="batch-processor",
            amount_micro_algos=1000000 * (i % 50 + 1),  # 1-50 ALGO
            interest_rate=5.0 + (i % 20),  # 5-25%
            correlation_id=f"batch_001_{i}"
        )

        events.append(audit_event)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"Created {len(events)} events in {duration:.3f} seconds")
    print(f"Rate: {len(events) / duration:.1f} events/second")

    # Calculate memory usage estimation
    sample_json = events[0].to_json()
    estimated_size_mb = len(events) * len(sample_json) / (1024 * 1024)
    print(f"Estimated memory usage: {estimated_size_mb:.2f} MB")

    return events


def main():
    """Run all examples"""
    print("Audit Trail & Compliance System - Example Usage")
    print("=" * 60)

    # Basic audit trail
    audit_event = example_basic_audit_trail()

    # Decision tracking
    decision = example_decision_tracking(audit_event)

    # Compliance tracking
    kyc_event, aml_event = example_compliance_tracking(audit_event)

    # Session management
    session = example_session_management()

    # Privacy profile
    profile = example_privacy_profile()

    # High volume simulation
    events = example_high_volume_simulation()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("\nNext steps:")
    print("1. Set up PostgreSQL database")
    print("2. Install asyncpg: pip install asyncpg")
    print("3. Configure database connection")
    print("4. Run database migrations")
    print("5. Implement audit storage layer")


if __name__ == "__main__":
    main()