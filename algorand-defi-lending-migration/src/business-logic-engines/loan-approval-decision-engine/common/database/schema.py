"""
Database Schema Definitions

SQLAlchemy table definitions for storing Algorand-native loan decision data.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class BorrowerProfileTable(Base):
    """
    Stores comprehensive borrower profiles based on Algorand ecosystem participation.
    """
    __tablename__ = 'borrower_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(58), unique=True, nullable=False, index=True)

    # Basic wallet characteristics
    wallet_age_days = Column(Integer, nullable=False)
    total_transaction_count = Column(Integer, nullable=False, default=0)
    total_volume_algo = Column(Float, nullable=False, default=0.0)
    asset_count = Column(Integer, nullable=False, default=0)
    nft_count = Column(Integer, nullable=False, default=0)
    smart_contract_interactions = Column(Integer, nullable=False, default=0)
    dapp_count = Column(Integer, nullable=False, default=0)

    # Participation indicators
    governance_participation = Column(Boolean, nullable=False, default=False)
    validator_participation = Column(Boolean, nullable=False, default=False)

    # Reputation and identity
    ens_name = Column(String(255), nullable=True)
    reputation_score = Column(Float, nullable=False, default=0.0)
    ecosystem_tenure_months = Column(Integer, nullable=False, default=0)

    # Metadata and tracking
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analyzed = Column(DateTime, nullable=True)

    # Relationships
    ecosystem_analyses = relationship("EcosystemAnalysisTable", back_populates="borrower_profile")
    risk_assessments = relationship("RiskAssessmentTable", back_populates="borrower_profile")
    loan_decisions = relationship("LoanDecisionTable", back_populates="borrower_profile")

    # Constraints
    __table_args__ = (
        CheckConstraint('wallet_age_days >= 0', name='positive_wallet_age'),
        CheckConstraint('total_transaction_count >= 0', name='positive_transaction_count'),
        CheckConstraint('total_volume_algo >= 0', name='positive_volume'),
        CheckConstraint('reputation_score >= 0 AND reputation_score <= 100', name='valid_reputation_score'),
        Index('idx_borrower_wallet_address', 'wallet_address'),
        Index('idx_borrower_reputation', 'reputation_score'),
        Index('idx_borrower_governance', 'governance_participation'),
    )


class EcosystemAnalysisTable(Base):
    """
    Stores detailed ecosystem analysis results for borrowers.
    """
    __tablename__ = 'ecosystem_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_profile_id = Column(Integer, ForeignKey('borrower_profiles.id'), nullable=False)

    # Protocol participation
    defi_protocols_used = Column(JSON, nullable=True)  # List of protocol names
    dex_trading_volume = Column(Float, nullable=False, default=0.0)
    lending_platform_history = Column(JSON, nullable=True)  # List of lending platforms
    yield_farming_participation = Column(Boolean, nullable=False, default=False)
    liquidity_provision_history = Column(Boolean, nullable=False, default=False)

    # Asset management scores
    asset_diversity_score = Column(Float, nullable=False, default=0.0)
    stable_asset_percentage = Column(Float, nullable=False, default=0.0)
    native_algo_percentage = Column(Float, nullable=False, default=0.0)
    exotic_asset_percentage = Column(Float, nullable=False, default=0.0)

    # Behavioral pattern scores
    transaction_frequency_score = Column(Float, nullable=False, default=0.0)
    weekend_activity_ratio = Column(Float, nullable=False, default=0.0)
    time_zone_consistency = Column(Float, nullable=False, default=0.0)
    gas_optimization_score = Column(Float, nullable=False, default=0.0)

    # Risk indicators
    high_risk_interactions = Column(Integer, nullable=False, default=0)
    suspicious_activity_flags = Column(JSON, nullable=True)  # List of flags
    blacklisted_interactions = Column(Integer, nullable=False, default=0)

    # Cross-protocol activity
    bridge_protocols_used = Column(JSON, nullable=True)  # List of bridge protocols
    cross_chain_volume = Column(Float, nullable=False, default=0.0)
    bridge_frequency = Column(Integer, nullable=False, default=0)
    algorand_native_percentage = Column(Float, nullable=False, default=1.0)
    return_frequency_to_algorand = Column(Float, nullable=False, default=1.0)

    # Analysis metadata
    analysis_period_days = Column(Integer, nullable=False, default=365)
    confidence_score = Column(Float, nullable=False, default=0.0)
    analysis_version = Column(String(50), nullable=False, default='1.0')

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    borrower_profile = relationship("BorrowerProfileTable", back_populates="ecosystem_analyses")

    # Constraints
    __table_args__ = (
        CheckConstraint('asset_diversity_score >= 0 AND asset_diversity_score <= 1', name='valid_diversity_score'),
        CheckConstraint('stable_asset_percentage >= 0 AND stable_asset_percentage <= 1', name='valid_stable_percentage'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='valid_confidence_score'),
        Index('idx_ecosystem_borrower', 'borrower_profile_id'),
        Index('idx_ecosystem_confidence', 'confidence_score'),
    )


class RiskAssessmentTable(Base):
    """
    Stores comprehensive risk assessment results.
    """
    __tablename__ = 'risk_assessments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_profile_id = Column(Integer, ForeignKey('borrower_profiles.id'), nullable=False)

    # Component risk scores (0-100)
    wallet_age_risk = Column(Float, nullable=False, default=50.0)
    transaction_volume_risk = Column(Float, nullable=False, default=50.0)
    asset_diversity_risk = Column(Float, nullable=False, default=50.0)
    governance_participation_risk = Column(Float, nullable=False, default=50.0)
    defi_behavior_risk = Column(Float, nullable=False, default=50.0)
    cross_protocol_risk = Column(Float, nullable=False, default=50.0)

    # Weighted composite scores
    technical_risk_score = Column(Float, nullable=False, default=50.0)
    behavioral_risk_score = Column(Float, nullable=False, default=50.0)
    ecosystem_risk_score = Column(Float, nullable=False, default=50.0)

    # Final assessment
    overall_risk_score = Column(Float, nullable=False, default=50.0)
    risk_level = Column(String(20), nullable=False, default='medium')

    # Risk factors and mitigants
    identified_risks = Column(JSON, nullable=True)  # List of risk factors
    risk_mitigants = Column(JSON, nullable=True)  # List of mitigating factors
    monitoring_recommendations = Column(JSON, nullable=True)  # List of monitoring suggestions

    # Calculation metadata
    calculation_method = Column(String(100), nullable=False, default='weighted_average')
    weights_used = Column(JSON, nullable=True)  # Dictionary of weights
    assessment_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Assessment context
    requested_loan_amount = Column(Float, nullable=True)
    context_adjustments = Column(JSON, nullable=True)  # Context-based adjustments

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    borrower_profile = relationship("BorrowerProfileTable", back_populates="risk_assessments")

    # Constraints
    __table_args__ = (
        CheckConstraint('overall_risk_score >= 0 AND overall_risk_score <= 100', name='valid_overall_risk'),
        CheckConstraint('wallet_age_risk >= 0 AND wallet_age_risk <= 100', name='valid_wallet_age_risk'),
        CheckConstraint('risk_level IN ("very_low", "low", "medium", "high", "very_high")', name='valid_risk_level'),
        Index('idx_risk_borrower', 'borrower_profile_id'),
        Index('idx_risk_overall_score', 'overall_risk_score'),
        Index('idx_risk_level', 'risk_level'),
    )


class LoanDecisionTable(Base):
    """
    Stores loan decisions with complete rationale and conditions.
    """
    __tablename__ = 'loan_decisions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_profile_id = Column(Integer, ForeignKey('borrower_profiles.id'), nullable=False)
    risk_assessment_id = Column(Integer, ForeignKey('risk_assessments.id'), nullable=True)

    # Basic decision
    decision_type = Column(String(30), nullable=False)  # approved, rejected, needs_review, conditional_approval
    approved_amount = Column(Float, nullable=False, default=0.0)
    requested_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False, default=0.0)
    loan_term_days = Column(Integer, nullable=False, default=0)

    # Decision rationale
    primary_decision_factors = Column(JSON, nullable=True)  # List of primary factors
    risk_mitigation_factors = Column(JSON, nullable=True)  # List of mitigating factors

    # Approval conditions (stored as JSON)
    approval_conditions = Column(JSON, nullable=True)  # ApprovalConditions object

    # Confidence and scoring
    decision_confidence = Column(Float, nullable=False, default=0.0)
    algorithm_version = Column(String(50), nullable=False, default='1.0')
    decision_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Review requirements
    requires_manual_review = Column(Boolean, nullable=False, default=False)
    review_priority = Column(String(20), nullable=False, default='normal')  # low, normal, high, urgent
    reviewer_notes = Column(Text, nullable=True)

    # Loan details
    loan_purpose = Column(String(500), nullable=True)
    proposed_collateral_amount = Column(Float, nullable=True)
    proposed_collateral_assets = Column(JSON, nullable=True)  # List of asset IDs

    # Status tracking
    decision_status = Column(String(20), nullable=False, default='pending')  # pending, approved, rejected, executed
    executed_at = Column(DateTime, nullable=True)
    loan_id = Column(String(100), nullable=True, unique=True)  # Actual loan ID if executed

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    borrower_profile = relationship("BorrowerProfileTable", back_populates="loan_decisions")
    risk_assessment = relationship("RiskAssessmentTable")

    # Constraints
    __table_args__ = (
        CheckConstraint('approved_amount >= 0', name='positive_approved_amount'),
        CheckConstraint('requested_amount > 0', name='positive_requested_amount'),
        CheckConstraint('interest_rate >= 0', name='positive_interest_rate'),
        CheckConstraint('decision_confidence >= 0 AND decision_confidence <= 1', name='valid_decision_confidence'),
        CheckConstraint('decision_type IN ("approved", "rejected", "needs_review", "conditional_approval")', name='valid_decision_type'),
        CheckConstraint('review_priority IN ("low", "normal", "high", "urgent")', name='valid_review_priority'),
        CheckConstraint('decision_status IN ("pending", "approved", "rejected", "executed")', name='valid_decision_status'),
        Index('idx_decision_borrower', 'borrower_profile_id'),
        Index('idx_decision_type', 'decision_type'),
        Index('idx_decision_timestamp', 'decision_timestamp'),
        Index('idx_decision_status', 'decision_status'),
        Index('idx_decision_review', 'requires_manual_review'),
    )


class GovernanceTrackingTable(Base):
    """
    Stores governance participation tracking data.
    """
    __tablename__ = 'governance_tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_profile_id = Column(Integer, ForeignKey('borrower_profiles.id'), nullable=False)

    # Participation type and metrics
    participation_type = Column(String(20), nullable=False, default='none')  # voter, proposer, delegator, validator, none
    votes_cast = Column(Integer, nullable=False, default=0)
    proposals_submitted = Column(Integer, nullable=False, default=0)
    delegation_received_algo = Column(Float, nullable=False, default=0.0)
    delegation_given_algo = Column(Float, nullable=False, default=0.0)

    # Participation quality scores
    vote_consistency_score = Column(Float, nullable=False, default=0.0)
    proposal_quality_score = Column(Float, nullable=False, default=0.0)
    community_engagement_score = Column(Float, nullable=False, default=0.0)

    # Historical data
    participation_start_date = Column(DateTime, nullable=True)
    continuous_participation_months = Column(Integer, nullable=False, default=0)
    governance_rewards_earned = Column(Float, nullable=False, default=0.0)

    # Detailed tracking
    governance_periods_participated = Column(JSON, nullable=True)  # List of period numbers
    voting_history = Column(JSON, nullable=True)  # Detailed voting records
    proposal_history = Column(JSON, nullable=True)  # Proposal submission history

    # Analysis period
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    last_governance_activity = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    borrower_profile = relationship("BorrowerProfileTable")

    # Constraints
    __table_args__ = (
        CheckConstraint('votes_cast >= 0', name='positive_votes_cast'),
        CheckConstraint('proposals_submitted >= 0', name='positive_proposals_submitted'),
        CheckConstraint('vote_consistency_score >= 0 AND vote_consistency_score <= 1', name='valid_vote_consistency'),
        CheckConstraint('participation_type IN ("voter", "proposer", "delegator", "validator", "none")', name='valid_participation_type'),
        Index('idx_governance_borrower', 'borrower_profile_id'),
        Index('idx_governance_participation_type', 'participation_type'),
        Index('idx_governance_votes', 'votes_cast'),
    )


class PatternAnalysisTable(Base):
    """
    Stores pattern analysis results for behavioral insights.
    """
    __tablename__ = 'pattern_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_profile_id = Column(Integer, ForeignKey('borrower_profiles.id'), nullable=False)

    # Pattern identification
    pattern_type = Column(String(100), nullable=False)
    pattern_category = Column(String(50), nullable=False)  # temporal, volume, behavioral, risk, etc.
    confidence = Column(Float, nullable=False)
    significance = Column(Float, nullable=False)
    risk_indicator = Column(Boolean, nullable=False, default=False)

    # Pattern details
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)  # List of evidence strings
    metadata = Column(JSON, nullable=True)  # Pattern-specific metadata

    # Pattern context
    data_source = Column(String(50), nullable=False)  # transactions, defi, governance, etc.
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    sample_size = Column(Integer, nullable=False, default=0)

    # Pattern lifecycle
    first_detected = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_confirmed = Column(DateTime, nullable=False, default=datetime.utcnow)
    pattern_status = Column(String(20), nullable=False, default='active')  # active, dormant, resolved

    # Analysis metadata
    detection_algorithm = Column(String(100), nullable=False)
    algorithm_version = Column(String(20), nullable=False, default='1.0')

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    borrower_profile = relationship("BorrowerProfileTable")

    # Constraints
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='valid_confidence'),
        CheckConstraint('significance >= 0 AND significance <= 1', name='valid_significance'),
        CheckConstraint('sample_size >= 0', name='positive_sample_size'),
        CheckConstraint('pattern_status IN ("active", "dormant", "resolved")', name='valid_pattern_status'),
        Index('idx_pattern_borrower', 'borrower_profile_id'),
        Index('idx_pattern_type', 'pattern_type'),
        Index('idx_pattern_category', 'pattern_category'),
        Index('idx_pattern_risk', 'risk_indicator'),
        Index('idx_pattern_confidence', 'confidence'),
    )


class DecisionHistoryTable(Base):
    """
    Stores decision history for analytics and model improvement.
    """
    __tablename__ = 'decision_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_decision_id = Column(Integer, ForeignKey('loan_decisions.id'), nullable=False)

    # Decision outcome tracking
    predicted_risk_score = Column(Float, nullable=False)
    actual_outcome = Column(String(20), nullable=True)  # successful, defaulted, early_repayment
    outcome_date = Column(DateTime, nullable=True)

    # Performance metrics
    days_to_outcome = Column(Integer, nullable=True)
    actual_loss_amount = Column(Float, nullable=True, default=0.0)
    predicted_loss_amount = Column(Float, nullable=True, default=0.0)

    # Model performance
    prediction_accuracy = Column(Float, nullable=True)  # How accurate was the risk assessment
    model_version = Column(String(50), nullable=False)

    # Learning data
    feedback_received = Column(Boolean, nullable=False, default=False)
    feedback_quality = Column(String(20), nullable=True)  # poor, fair, good, excellent
    lessons_learned = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    loan_decision = relationship("LoanDecisionTable")

    # Constraints
    __table_args__ = (
        CheckConstraint('predicted_risk_score >= 0 AND predicted_risk_score <= 100', name='valid_predicted_risk'),
        CheckConstraint('actual_loss_amount >= 0', name='positive_actual_loss'),
        CheckConstraint('predicted_loss_amount >= 0', name='positive_predicted_loss'),
        CheckConstraint('outcome IN ("successful", "defaulted", "early_repayment", NULL)', name='valid_outcome'),
        Index('idx_history_decision', 'loan_decision_id'),
        Index('idx_history_outcome', 'actual_outcome'),
        Index('idx_history_accuracy', 'prediction_accuracy'),
    )


class AuditTrailTable(Base):
    """
    Stores audit trail for all decision-related activities.
    """
    __tablename__ = 'audit_trail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # borrower_profile, risk_assessment, loan_decision
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # created, updated, deleted, analyzed
    user_id = Column(String(100), nullable=True)  # System user or automated process

    # Change details
    changes_made = Column(JSON, nullable=True)  # What changed
    previous_values = Column(JSON, nullable=True)  # Previous values
    new_values = Column(JSON, nullable=True)  # New values

    # Context
    reason = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action'),
    )