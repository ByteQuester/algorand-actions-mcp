"""
Database Models

Pydantic models for database operations and data serialization.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DecisionTypeEnum(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    CONDITIONAL_APPROVAL = "conditional_approval"


class RiskLevelEnum(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ParticipationTypeEnum(str, Enum):
    VOTER = "voter"
    PROPOSER = "proposer"
    DELEGATOR = "delegator"
    VALIDATOR = "validator"
    NONE = "none"


class DatabaseBorrowerProfile(BaseModel):
    """Database model for borrower profiles"""

    id: Optional[int] = None
    wallet_address: str = Field(..., min_length=58, max_length=58)

    # Basic wallet characteristics
    wallet_age_days: int = Field(ge=0)
    total_transaction_count: int = Field(ge=0, default=0)
    total_volume_algo: float = Field(ge=0.0, default=0.0)
    asset_count: int = Field(ge=0, default=0)
    nft_count: int = Field(ge=0, default=0)
    smart_contract_interactions: int = Field(ge=0, default=0)
    dapp_count: int = Field(ge=0, default=0)

    # Participation indicators
    governance_participation: bool = False
    validator_participation: bool = False

    # Reputation and identity
    ens_name: Optional[str] = None
    reputation_score: float = Field(ge=0.0, le=100.0, default=0.0)
    ecosystem_tenure_months: int = Field(ge=0, default=0)

    # Metadata and tracking
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_analyzed: Optional[datetime] = None

    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v or len(v) != 58:
            raise ValueError('Algorand wallet address must be 58 characters')
        return v

    class Config:
        orm_mode = True


class DatabaseEcosystemAnalysis(BaseModel):
    """Database model for ecosystem analysis"""

    id: Optional[int] = None
    borrower_profile_id: int

    # Protocol participation
    defi_protocols_used: Optional[List[str]] = []
    dex_trading_volume: float = Field(ge=0.0, default=0.0)
    lending_platform_history: Optional[List[str]] = []
    yield_farming_participation: bool = False
    liquidity_provision_history: bool = False

    # Asset management scores
    asset_diversity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    stable_asset_percentage: float = Field(ge=0.0, le=1.0, default=0.0)
    native_algo_percentage: float = Field(ge=0.0, le=1.0, default=0.0)
    exotic_asset_percentage: float = Field(ge=0.0, le=1.0, default=0.0)

    # Behavioral pattern scores
    transaction_frequency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    weekend_activity_ratio: float = Field(ge=0.0, le=1.0, default=0.0)
    time_zone_consistency: float = Field(ge=0.0, le=1.0, default=0.0)
    gas_optimization_score: float = Field(ge=0.0, le=1.0, default=0.0)

    # Risk indicators
    high_risk_interactions: int = Field(ge=0, default=0)
    suspicious_activity_flags: Optional[List[str]] = []
    blacklisted_interactions: int = Field(ge=0, default=0)

    # Cross-protocol activity
    bridge_protocols_used: Optional[List[str]] = []
    cross_chain_volume: float = Field(ge=0.0, default=0.0)
    bridge_frequency: int = Field(ge=0, default=0)
    algorand_native_percentage: float = Field(ge=0.0, le=1.0, default=1.0)
    return_frequency_to_algorand: float = Field(ge=0.0, le=1.0, default=1.0)

    # Analysis metadata
    analysis_period_days: int = Field(ge=1, default=365)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    analysis_version: str = "1.0"

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DatabaseRiskAssessment(BaseModel):
    """Database model for risk assessments"""

    id: Optional[int] = None
    borrower_profile_id: int

    # Component risk scores (0-100)
    wallet_age_risk: float = Field(ge=0.0, le=100.0, default=50.0)
    transaction_volume_risk: float = Field(ge=0.0, le=100.0, default=50.0)
    asset_diversity_risk: float = Field(ge=0.0, le=100.0, default=50.0)
    governance_participation_risk: float = Field(ge=0.0, le=100.0, default=50.0)
    defi_behavior_risk: float = Field(ge=0.0, le=100.0, default=50.0)
    cross_protocol_risk: float = Field(ge=0.0, le=100.0, default=50.0)

    # Weighted composite scores
    technical_risk_score: float = Field(ge=0.0, le=100.0, default=50.0)
    behavioral_risk_score: float = Field(ge=0.0, le=100.0, default=50.0)
    ecosystem_risk_score: float = Field(ge=0.0, le=100.0, default=50.0)

    # Final assessment
    overall_risk_score: float = Field(ge=0.0, le=100.0, default=50.0)
    risk_level: RiskLevelEnum = RiskLevelEnum.MEDIUM

    # Risk factors and mitigants
    identified_risks: Optional[List[str]] = []
    risk_mitigants: Optional[List[str]] = []
    monitoring_recommendations: Optional[List[str]] = []

    # Calculation metadata
    calculation_method: str = "weighted_average"
    weights_used: Optional[Dict[str, float]] = None
    assessment_timestamp: Optional[datetime] = None

    # Assessment context
    requested_loan_amount: Optional[float] = None
    context_adjustments: Optional[Dict[str, float]] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DatabaseLoanDecision(BaseModel):
    """Database model for loan decisions"""

    id: Optional[int] = None
    borrower_profile_id: int
    risk_assessment_id: Optional[int] = None

    # Basic decision
    decision_type: DecisionTypeEnum
    approved_amount: float = Field(ge=0.0, default=0.0)
    requested_amount: float = Field(gt=0.0)
    interest_rate: float = Field(ge=0.0, default=0.0)
    loan_term_days: int = Field(ge=0, default=0)

    # Decision rationale
    primary_decision_factors: Optional[List[str]] = []
    risk_mitigation_factors: Optional[List[str]] = []

    # Approval conditions (stored as JSON)
    approval_conditions: Optional[Dict[str, Any]] = None

    # Confidence and scoring
    decision_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    algorithm_version: str = "1.0"
    decision_timestamp: Optional[datetime] = None

    # Review requirements
    requires_manual_review: bool = False
    review_priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")
    reviewer_notes: Optional[str] = None

    # Loan details
    loan_purpose: Optional[str] = Field(None, max_length=500)
    proposed_collateral_amount: Optional[float] = Field(None, ge=0.0)
    proposed_collateral_assets: Optional[List[str]] = []

    # Status tracking
    decision_status: str = Field(default="pending", regex="^(pending|approved|rejected|executed)$")
    executed_at: Optional[datetime] = None
    loan_id: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('approved_amount')
    def validate_approved_amount(cls, v, values):
        if 'decision_type' in values and values['decision_type'] == DecisionTypeEnum.APPROVED:
            if v <= 0:
                raise ValueError('Approved amount must be positive for approved loans')
        return v

    class Config:
        orm_mode = True


class DatabaseGovernanceTracking(BaseModel):
    """Database model for governance tracking"""

    id: Optional[int] = None
    borrower_profile_id: int

    # Participation type and metrics
    participation_type: ParticipationTypeEnum = ParticipationTypeEnum.NONE
    votes_cast: int = Field(ge=0, default=0)
    proposals_submitted: int = Field(ge=0, default=0)
    delegation_received_algo: float = Field(ge=0.0, default=0.0)
    delegation_given_algo: float = Field(ge=0.0, default=0.0)

    # Participation quality scores
    vote_consistency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    proposal_quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    community_engagement_score: float = Field(ge=0.0, le=1.0, default=0.0)

    # Historical data
    participation_start_date: Optional[datetime] = None
    continuous_participation_months: int = Field(ge=0, default=0)
    governance_rewards_earned: float = Field(ge=0.0, default=0.0)

    # Detailed tracking
    governance_periods_participated: Optional[List[int]] = []
    voting_history: Optional[List[Dict[str, Any]]] = []
    proposal_history: Optional[List[Dict[str, Any]]] = []

    # Analysis period
    analysis_period_start: datetime
    analysis_period_end: datetime
    last_governance_activity: Optional[datetime] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DatabasePatternAnalysis(BaseModel):
    """Database model for pattern analysis"""

    id: Optional[int] = None
    borrower_profile_id: int

    # Pattern identification
    pattern_type: str = Field(..., min_length=1, max_length=100)
    pattern_category: str = Field(..., min_length=1, max_length=50)
    confidence: float = Field(ge=0.0, le=1.0)
    significance: float = Field(ge=0.0, le=1.0)
    risk_indicator: bool = False

    # Pattern details
    description: str = Field(..., min_length=1)
    evidence: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = None

    # Pattern context
    data_source: str = Field(..., min_length=1, max_length=50)
    analysis_period_start: datetime
    analysis_period_end: datetime
    sample_size: int = Field(ge=0, default=0)

    # Pattern lifecycle
    first_detected: Optional[datetime] = None
    last_confirmed: Optional[datetime] = None
    pattern_status: str = Field(default="active", regex="^(active|dormant|resolved)$")

    # Analysis metadata
    detection_algorithm: str = Field(..., min_length=1, max_length=100)
    algorithm_version: str = "1.0"

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DatabaseDecisionHistory(BaseModel):
    """Database model for decision history tracking"""

    id: Optional[int] = None
    loan_decision_id: int

    # Decision outcome tracking
    predicted_risk_score: float = Field(ge=0.0, le=100.0)
    actual_outcome: Optional[str] = Field(None, regex="^(successful|defaulted|early_repayment)$")
    outcome_date: Optional[datetime] = None

    # Performance metrics
    days_to_outcome: Optional[int] = Field(None, ge=0)
    actual_loss_amount: Optional[float] = Field(None, ge=0.0)
    predicted_loss_amount: Optional[float] = Field(None, ge=0.0)

    # Model performance
    prediction_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: str

    # Learning data
    feedback_received: bool = False
    feedback_quality: Optional[str] = Field(None, regex="^(poor|fair|good|excellent)$")
    lessons_learned: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DatabaseAuditTrail(BaseModel):
    """Database model for audit trail"""

    id: Optional[int] = None
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: int
    action: str = Field(..., min_length=1, max_length=50)
    user_id: Optional[str] = Field(None, max_length=100)

    # Change details
    changes_made: Optional[Dict[str, Any]] = None
    previous_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

    # Context
    reason: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)

    # Timestamps
    timestamp: Optional[datetime] = None

    class Config:
        orm_mode = True


# Request/Response models for API operations

class CreateBorrowerProfileRequest(BaseModel):
    """Request model for creating borrower profile"""
    wallet_address: str = Field(..., min_length=58, max_length=58)
    wallet_age_days: int = Field(ge=0)
    total_transaction_count: int = Field(ge=0, default=0)
    total_volume_algo: float = Field(ge=0.0, default=0.0)
    asset_count: int = Field(ge=0, default=0)
    nft_count: int = Field(ge=0, default=0)
    smart_contract_interactions: int = Field(ge=0, default=0)
    dapp_count: int = Field(ge=0, default=0)
    governance_participation: bool = False
    validator_participation: bool = False
    ens_name: Optional[str] = None
    reputation_score: float = Field(ge=0.0, le=100.0, default=0.0)
    ecosystem_tenure_months: int = Field(ge=0, default=0)
    metadata: Optional[Dict[str, Any]] = None


class UpdateBorrowerProfileRequest(BaseModel):
    """Request model for updating borrower profile"""
    total_transaction_count: Optional[int] = Field(None, ge=0)
    total_volume_algo: Optional[float] = Field(None, ge=0.0)
    asset_count: Optional[int] = Field(None, ge=0)
    nft_count: Optional[int] = Field(None, ge=0)
    smart_contract_interactions: Optional[int] = Field(None, ge=0)
    dapp_count: Optional[int] = Field(None, ge=0)
    governance_participation: Optional[bool] = None
    validator_participation: Optional[bool] = None
    reputation_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    ecosystem_tenure_months: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class CreateLoanDecisionRequest(BaseModel):
    """Request model for creating loan decision"""
    borrower_profile_id: int
    risk_assessment_id: Optional[int] = None
    decision_type: DecisionTypeEnum
    approved_amount: float = Field(ge=0.0, default=0.0)
    requested_amount: float = Field(gt=0.0)
    interest_rate: float = Field(ge=0.0, default=0.0)
    loan_term_days: int = Field(ge=0, default=0)
    primary_decision_factors: Optional[List[str]] = []
    risk_mitigation_factors: Optional[List[str]] = []
    approval_conditions: Optional[Dict[str, Any]] = None
    decision_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    algorithm_version: str = "1.0"
    requires_manual_review: bool = False
    review_priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")
    reviewer_notes: Optional[str] = None
    loan_purpose: Optional[str] = Field(None, max_length=500)
    proposed_collateral_amount: Optional[float] = Field(None, ge=0.0)
    proposed_collateral_assets: Optional[List[str]] = []


class BorrowerProfileResponse(DatabaseBorrowerProfile):
    """Response model for borrower profile"""
    pass


class RiskAssessmentResponse(DatabaseRiskAssessment):
    """Response model for risk assessment"""
    pass


class LoanDecisionResponse(DatabaseLoanDecision):
    """Response model for loan decision"""
    pass


class SearchBorrowersRequest(BaseModel):
    """Request model for searching borrowers"""
    wallet_address: Optional[str] = None
    min_reputation_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_reputation_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    governance_participation: Optional[bool] = None
    min_wallet_age_days: Optional[int] = Field(None, ge=0)
    max_wallet_age_days: Optional[int] = Field(None, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class SearchBorrowersResponse(BaseModel):
    """Response model for borrower search"""
    borrowers: List[BorrowerProfileResponse]
    total_count: int
    limit: int
    offset: int