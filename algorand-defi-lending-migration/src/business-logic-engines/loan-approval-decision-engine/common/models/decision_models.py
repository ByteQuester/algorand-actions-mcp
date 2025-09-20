"""
Algorand-Native Decision Models

Data models representing Algorand ecosystem participants and their
behavior patterns for holistic loan approval decisions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class DecisionType(Enum):
    """Loan decision types"""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    CONDITIONAL_APPROVAL = "conditional_approval"


class RiskLevel(Enum):
    """Risk assessment levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ParticipationType(Enum):
    """Types of governance participation"""
    VOTER = "voter"
    PROPOSER = "proposer"
    DELEGATOR = "delegator"
    VALIDATOR = "validator"
    NONE = "none"


@dataclass
class AlgorandBorrower:
    """
    Represents a borrower in the Algorand ecosystem with their
    complete on-chain identity and behavior patterns.
    """
    wallet_address: str
    wallet_age_days: int
    total_transaction_count: int
    total_volume_algo: float
    asset_count: int
    nft_count: int
    smart_contract_interactions: int
    dapp_count: int
    governance_participation: bool
    validator_participation: bool

    # Identity and reputation
    ens_name: Optional[str] = None
    reputation_score: float = 0.0
    ecosystem_tenure_months: int = 0

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EcosystemFootprint:
    """
    Comprehensive footprint of a borrower's participation
    across the Algorand ecosystem.
    """
    # Protocol participation
    defi_protocols_used: List[str] = field(default_factory=list)
    dex_trading_volume: float = 0.0
    lending_platform_history: List[str] = field(default_factory=list)
    yield_farming_participation: bool = False
    liquidity_provision_history: bool = False

    # Asset management
    asset_diversity_score: float = 0.0
    stable_asset_percentage: float = 0.0
    native_algo_percentage: float = 0.0
    exotic_asset_percentage: float = 0.0

    # Behavioral patterns
    transaction_frequency_score: float = 0.0
    weekend_activity_ratio: float = 0.0
    time_zone_consistency: float = 0.0
    gas_optimization_score: float = 0.0

    # Risk indicators
    high_risk_interactions: int = 0
    suspicious_activity_flags: List[str] = field(default_factory=list)
    blacklisted_interactions: int = 0


@dataclass
class DeFiBehaviorPattern:
    """
    Analysis of DeFi behavior patterns indicating
    financial sophistication and risk management.
    """
    # Trading patterns
    average_hold_time_days: float = 0.0
    profit_loss_ratio: float = 0.0
    maximum_drawdown: float = 0.0
    risk_adjusted_returns: float = 0.0

    # Liquidity management
    liquidity_provision_consistency: float = 0.0
    impermanent_loss_tolerance: float = 0.0
    staking_behavior_score: float = 0.0

    # Risk management
    diversification_score: float = 0.0
    leverage_usage_frequency: int = 0
    stop_loss_usage: float = 0.0
    position_sizing_consistency: float = 0.0

    # Protocol interaction sophistication
    protocol_diversity: int = 0
    advanced_strategy_usage: bool = False
    yield_optimization_score: float = 0.0
    flash_loan_usage: int = 0


@dataclass
class GovernanceParticipation:
    """
    Track governance participation across Algorand ecosystem.
    """
    participation_type: ParticipationType
    votes_cast: int = 0
    proposals_submitted: int = 0
    delegation_received_algo: float = 0.0
    delegation_given_algo: float = 0.0

    # Participation quality
    vote_consistency_score: float = 0.0
    proposal_quality_score: float = 0.0
    community_engagement_score: float = 0.0

    # Historical data
    participation_start_date: Optional[datetime] = None
    continuous_participation_months: int = 0
    governance_rewards_earned: float = 0.0


@dataclass
class CrossProtocolActivity:
    """
    Analysis of activity across different protocols and bridges.
    """
    # Bridge usage
    bridge_protocols_used: List[str] = field(default_factory=list)
    cross_chain_volume: float = 0.0
    bridge_frequency: int = 0

    # Multi-protocol behavior
    simultaneous_protocol_usage: int = 0
    protocol_migration_patterns: List[str] = field(default_factory=list)
    arbitrage_activity: bool = False

    # Ecosystem loyalty
    algorand_native_percentage: float = 0.0
    external_chain_activity: Dict[str, float] = field(default_factory=dict)
    return_frequency_to_algorand: float = 0.0


@dataclass
class HolisticRiskProfile:
    """
    Comprehensive risk assessment combining all ecosystem factors.
    """
    # Overall scores
    ecosystem_trust_score: float = 0.0
    financial_sophistication_score: float = 0.0
    long_term_commitment_score: float = 0.0
    community_standing_score: float = 0.0

    # Risk factors
    volatility_exposure_score: float = 0.0
    concentration_risk_score: float = 0.0
    counterparty_risk_score: float = 0.0
    technical_risk_score: float = 0.0

    # Behavioral indicators
    consistency_score: float = 0.0
    growth_trajectory_score: float = 0.0
    adaptation_score: float = 0.0

    # Final assessment
    overall_risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = 50.0  # 0-100 scale
    confidence_level: float = 0.0  # 0-1 scale


@dataclass
class ApprovalConditions:
    """
    Specific conditions that must be met for loan approval.
    """
    # Collateral requirements
    minimum_collateral_ratio: float = 1.5
    accepted_collateral_types: List[str] = field(default_factory=list)
    collateral_lock_period_days: int = 30

    # Monitoring requirements
    continuous_monitoring_required: bool = False
    reporting_frequency_days: int = 30
    governance_participation_required: bool = False

    # Behavioral constraints
    maximum_new_protocol_interactions: int = 5
    minimum_ecosystem_activity_score: float = 0.7
    blacklisted_protocol_restrictions: List[str] = field(default_factory=list)

    # Financial constraints
    maximum_additional_leverage: float = 2.0
    minimum_stable_asset_percentage: float = 0.2
    drawdown_monitoring_threshold: float = 0.3


@dataclass
class LoanDecision:
    """
    Final loan decision with comprehensive justification.
    """
    # Basic decision
    decision_type: DecisionType
    approved_amount: float = 0.0
    requested_amount: float = 0.0
    interest_rate: float = 0.0
    loan_term_days: int = 0

    # Decision rationale
    primary_decision_factors: List[str] = field(default_factory=list)
    risk_mitigation_factors: List[str] = field(default_factory=list)
    approval_conditions: Optional[ApprovalConditions] = None

    # Confidence and scoring
    decision_confidence: float = 0.0
    algorithm_version: str = "1.0"
    decision_timestamp: datetime = field(default_factory=datetime.utcnow)

    # Supporting data
    borrower_profile: Optional[AlgorandBorrower] = None
    risk_profile: Optional[HolisticRiskProfile] = None

    # Review requirements
    requires_manual_review: bool = False
    review_priority: str = "normal"  # low, normal, high, urgent
    reviewer_notes: str = ""


@dataclass
class RiskAssessment:
    """
    Detailed risk assessment breakdown for transparency.
    """
    # Component risk scores (0-100)
    wallet_age_risk: float = 0.0
    transaction_volume_risk: float = 0.0
    asset_diversity_risk: float = 0.0
    governance_participation_risk: float = 0.0
    defi_behavior_risk: float = 0.0
    cross_protocol_risk: float = 0.0

    # Weighted composite scores
    technical_risk_score: float = 0.0
    behavioral_risk_score: float = 0.0
    ecosystem_risk_score: float = 0.0

    # Final assessment
    overall_risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Risk factors and mitigants
    identified_risks: List[str] = field(default_factory=list)
    risk_mitigants: List[str] = field(default_factory=list)
    monitoring_recommendations: List[str] = field(default_factory=list)

    # Calculation metadata
    calculation_method: str = "weighted_average"
    weights_used: Dict[str, float] = field(default_factory=dict)
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'wallet_age_risk': self.wallet_age_risk,
            'transaction_volume_risk': self.transaction_volume_risk,
            'asset_diversity_risk': self.asset_diversity_risk,
            'governance_participation_risk': self.governance_participation_risk,
            'defi_behavior_risk': self.defi_behavior_risk,
            'cross_protocol_risk': self.cross_protocol_risk,
            'technical_risk_score': self.technical_risk_score,
            'behavioral_risk_score': self.behavioral_risk_score,
            'ecosystem_risk_score': self.ecosystem_risk_score,
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level.value,
            'identified_risks': self.identified_risks,
            'risk_mitigants': self.risk_mitigants,
            'monitoring_recommendations': self.monitoring_recommendations,
            'calculation_method': self.calculation_method,
            'weights_used': self.weights_used,
            'assessment_timestamp': self.assessment_timestamp.isoformat()
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


# Utility functions for model validation and conversion

def validate_algorand_address(address: str) -> bool:
    """Validate Algorand wallet address format"""
    if not address or len(address) != 58:
        return False
    # Basic validation - in practice would use algosdk
    return address.isalnum()


def calculate_ecosystem_maturity_score(
    wallet_age_days: int,
    transaction_count: int,
    governance_participation: bool,
    protocol_count: int
) -> float:
    """Calculate overall ecosystem maturity score"""
    age_score = min(wallet_age_days / 365.0, 1.0) * 30  # Max 30 points for 1+ year
    activity_score = min(transaction_count / 1000.0, 1.0) * 25  # Max 25 points for 1000+ txns
    governance_score = 20 if governance_participation else 0  # 20 points for governance
    protocol_score = min(protocol_count / 10.0, 1.0) * 25  # Max 25 points for 10+ protocols

    return age_score + activity_score + governance_score + protocol_score


def risk_level_from_score(score: float) -> RiskLevel:
    """Convert numeric risk score to risk level enum"""
    if score <= 20:
        return RiskLevel.VERY_LOW
    elif score <= 40:
        return RiskLevel.LOW
    elif score <= 60:
        return RiskLevel.MEDIUM
    elif score <= 80:
        return RiskLevel.HIGH
    else:
        return RiskLevel.VERY_HIGH