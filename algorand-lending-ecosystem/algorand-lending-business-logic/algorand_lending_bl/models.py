"""
Unified Models for Algorand Lending Business Logic

Consolidated data models from all engines into a single, clean module.
All models are designed for easy serialization and cross-service communication.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json


# =============================================================================
# Core Enums
# =============================================================================

class AssetType(Enum):
    """Algorand asset types"""
    ALGO_NATIVE = "algo_native"
    ASA_TOKEN = "asa_token"
    STABLECOIN = "stablecoin"
    GOVERNANCE_TOKEN = "governance_token"
    LP_TOKEN = "lp_token"
    LIQUID_STAKING = "liquid_staking"


class LiquidityTier(Enum):
    """Asset liquidity tiers"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ILLIQUID = "illiquid"


class RiskLevel(Enum):
    """Risk assessment levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskTier(Enum):
    """Borrower risk tiers"""
    PRIME = "prime"
    STANDARD = "standard"
    SUBPRIME = "subprime"
    HIGH_RISK = "high_risk"


class DecisionType(Enum):
    """Loan decision types"""
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class DecisionConfidence(Enum):
    """Decision confidence levels"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class NetworkHealth(Enum):
    """Algorand network health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


# =============================================================================
# Core Data Models
# =============================================================================

@dataclass
class AlgorandAddress:
    """Algorand address with basic validation"""
    address: str

    def __post_init__(self):
        """Basic validation - disabled for simplicity in demo"""
        # Simple validation could be added here if needed
        pass

    def is_valid(self) -> bool:
        """Basic Algorand address validation"""
        return self.address and len(self.address) == 58 and self.address.isalnum()


@dataclass
class ASAToken:
    """Algorand Standard Asset token information"""
    asset_id: str
    symbol: str
    name: str
    decimals: int
    total_supply: Decimal
    circulating_supply: Decimal
    creator_address: str
    unit_name: Optional[str] = None
    url: Optional[str] = None
    metadata_hash: Optional[str] = None


# =============================================================================
# Collateral Models
# =============================================================================

@dataclass
class AssetValuation:
    """Asset valuation with risk metrics"""
    asset: ASAToken
    current_price_usd: Decimal
    market_cap_usd: Decimal
    daily_volume_usd: Decimal
    price_confidence: Decimal  # 0-1 scale
    volatility_30d: Decimal
    volatility_7d: Decimal
    max_drawdown_30d: Decimal
    correlation_with_algo: Decimal
    liquidity_tier: LiquidityTier
    last_updated: datetime

    def risk_adjusted_value(self, haircut: Decimal) -> Decimal:
        """Calculate risk-adjusted value with haircut"""
        return self.current_price_usd * (Decimal('1') - haircut)


@dataclass
class LiquidationScenario:
    """Liquidation scenario analysis"""
    scenario_name: str
    trigger_price_drop: Decimal  # Percentage drop that triggers liquidation
    liquidation_timeline_hours: Decimal
    expected_slippage: Decimal  # Expected price impact during liquidation
    recovery_rate: Decimal  # Expected recovery as percentage of original value
    liquidation_cost: Decimal  # Gas + penalties + fees
    net_recovery_rate: Decimal  # Final recovery after all costs
    probability: Decimal  # Estimated probability of this scenario

    def expected_loss(self, position_value: Decimal) -> Decimal:
        """Calculate expected loss for this scenario"""
        return position_value * (Decimal('1') - self.net_recovery_rate) * self.probability


@dataclass
class CollateralPosition:
    """Individual collateral position"""
    asset: ASAToken
    quantity: Decimal
    valuation: AssetValuation
    position_value_usd: Decimal
    haircut_percentage: Decimal
    adjusted_value_usd: Decimal
    asset_type: AssetType
    liquidation_scenarios: List[LiquidationScenario]
    risk_level: RiskLevel

    def weighted_expected_loss(self) -> Decimal:
        """Calculate weighted expected loss across all liquidation scenarios"""
        total_expected_loss = Decimal('0')
        for scenario in self.liquidation_scenarios:
            total_expected_loss += scenario.expected_loss(self.position_value_usd)
        return total_expected_loss


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics"""
    total_value_usd: Decimal
    diversification_score: Decimal  # 0-1, higher is better
    concentration_risk: Decimal  # 0-1, higher is worse
    liquidity_risk: Decimal  # 0-1, higher is worse
    correlation_risk: Decimal  # 0-1, higher is worse
    stress_test_results: Dict[str, Decimal]  # scenario -> impact percentage
    recommended_haircut: Decimal
    min_collateral_ratio: Decimal

    def overall_risk_score(self) -> Decimal:
        """Calculate overall portfolio risk score (0-1, higher is worse)"""
        weights = {
            'concentration': Decimal('0.3'),
            'liquidity': Decimal('0.25'),
            'correlation': Decimal('0.25'),
            'diversification': Decimal('0.2')
        }

        # Invert diversification score (higher diversification = lower risk)
        diversification_risk = Decimal('1') - self.diversification_score

        return (
            self.concentration_risk * weights['concentration'] +
            self.liquidity_risk * weights['liquidity'] +
            self.correlation_risk * weights['correlation'] +
            diversification_risk * weights['diversification']
        )


@dataclass
class CollateralAnalysis:
    """Complete collateral analysis result"""
    loan_amount_usd: Decimal
    positions: List[CollateralPosition]
    portfolio_risk: PortfolioRisk
    total_collateral_value: Decimal
    total_adjusted_value: Decimal
    current_collateral_ratio: Decimal
    required_collateral_ratio: Decimal
    is_sufficient: bool
    additional_collateral_needed: Decimal
    liquidation_threshold: Decimal
    price_alerts: List[Dict[str, Any]]  # Alerts for price movements
    recommendations: List[str]
    analysis_timestamp: datetime

    def safety_margin(self) -> Decimal:
        """Calculate safety margin above minimum requirements"""
        if self.required_collateral_ratio == 0:
            return Decimal('0')
        excess_ratio = self.current_collateral_ratio - self.required_collateral_ratio
        return excess_ratio / self.required_collateral_ratio


# =============================================================================
# Interest Rate Models
# =============================================================================

@dataclass
class StakingMetrics:
    """ALGO staking and consensus participation metrics"""
    current_apy: Decimal
    historical_avg_apy: Decimal
    participation_rate: Decimal
    total_staked_algo: Decimal
    governance_participation: Decimal
    validator_performance: Decimal
    staking_rewards_30d: Decimal
    consensus_uptime: Decimal
    timestamp: datetime

    def base_rate(self) -> Decimal:
        """Calculate base lending rate from staking yield"""
        spread = Decimal('0.02')  # 2% spread
        return self.current_apy + spread


@dataclass
class DeFiYieldData:
    """DeFi protocol yield data from Algorand ecosystem"""
    protocol_name: str
    base_yield: Decimal
    reward_token_apy: Decimal
    total_apy: Decimal
    tvl_usd: Decimal
    volume_24h: Decimal
    protocol_health_score: Decimal
    risk_premium: Decimal
    last_updated: datetime

    def effective_yield(self) -> Decimal:
        """Calculate effective yield after risk adjustments"""
        return self.total_apy - self.risk_premium


@dataclass
class ReputationScore:
    """On-chain reputation scoring for borrowers"""
    address: AlgorandAddress
    overall_score: Decimal  # 0-1 scale, higher is better
    transaction_history_score: Decimal
    asset_diversity_score: Decimal
    defi_participation_score: Decimal
    governance_participation_score: Decimal
    liquidation_history_score: Decimal
    account_age_score: Decimal
    volume_score: Decimal
    risk_tier: RiskTier
    confidence_level: Decimal
    last_calculated: datetime

    def rate_adjustment(self) -> Decimal:
        """Calculate interest rate adjustment based on reputation"""
        base_adjustment = (Decimal('1') - self.overall_score) * Decimal('0.1')  # Up to 10%

        risk_adjustments = {
            RiskTier.PRIME: Decimal('-0.01'),      # -1% for prime borrowers
            RiskTier.STANDARD: Decimal('0'),       # No adjustment
            RiskTier.SUBPRIME: Decimal('0.025'),   # +2.5%
            RiskTier.HIGH_RISK: Decimal('0.05')    # +5%
        }

        tier_adjustment = risk_adjustments.get(self.risk_tier, Decimal('0'))
        return base_adjustment + tier_adjustment


@dataclass
class ASARiskMetrics:
    """Risk metrics for Algorand Standard Assets"""
    asset_id: str
    symbol: str
    volatility_30d: Decimal
    volatility_90d: Decimal
    liquidity_score: Decimal
    market_cap_usd: Decimal
    trading_volume_24h: Decimal
    holder_count: int
    concentration_risk: Decimal
    smart_contract_risk: Decimal
    regulatory_risk: Decimal
    overall_risk_score: Decimal  # 0-1, higher is riskier
    last_updated: datetime

    def risk_premium(self) -> Decimal:
        """Calculate risk premium for this ASA"""
        base_premium = self.overall_risk_score * Decimal('0.05')  # Up to 5%
        vol_premium = min(self.volatility_30d * Decimal('0.1'), Decimal('0.03'))  # Max 3%
        liquidity_premium = (Decimal('1') - self.liquidity_score) * Decimal('0.02')  # Up to 2%
        return base_premium + vol_premium + liquidity_premium


@dataclass
class NetworkMetrics:
    """Algorand network activity and health metrics"""
    current_tps: Decimal
    average_tps_24h: Decimal
    block_time_avg: Decimal
    finality_time: Decimal
    total_accounts: int
    active_accounts_24h: int
    total_transactions_24h: int
    network_congestion: Decimal  # 0-1, higher is more congested
    gas_price_trend: Decimal
    network_health: NetworkHealth
    consensus_status: str
    last_updated: datetime

    def network_risk_adjustment(self) -> Decimal:
        """Calculate rate adjustment based on network conditions"""
        congestion_adj = self.network_congestion * Decimal('0.005')  # Up to 0.5%

        health_adjustments = {
            NetworkHealth.EXCELLENT: Decimal('-0.001'),  # -0.1% discount
            NetworkHealth.GOOD: Decimal('0'),            # No adjustment
            NetworkHealth.FAIR: Decimal('0.002'),        # +0.2%
            NetworkHealth.POOR: Decimal('0.005')         # +0.5%
        }

        health_adj = health_adjustments.get(self.network_health, Decimal('0'))
        return congestion_adj + health_adj


@dataclass
class LiquidityMetrics:
    """Liquidity pool and market depth metrics"""
    pool_name: str
    asset_pair: str
    total_liquidity_usd: Decimal
    volume_24h: Decimal
    volume_to_liquidity_ratio: Decimal
    price_impact_1k_usd: Decimal
    price_impact_10k_usd: Decimal
    impermanent_loss_potential: Decimal
    pool_health_score: Decimal
    yield_farming_apy: Decimal
    last_updated: datetime


@dataclass
class RateFactors:
    """All factors contributing to interest rate calculation"""
    base_rate: Decimal
    risk_premium: Decimal
    liquidity_premium: Decimal
    duration_premium: Decimal
    market_conditions_adjustment: Decimal
    reputation_adjustment: Decimal
    collateral_adjustment: Decimal
    network_adjustment: Decimal
    defi_yield_adjustment: Decimal
    governance_adjustment: Decimal

    def total_rate(self) -> Decimal:
        """Calculate total interest rate from all factors"""
        return (
            self.base_rate +
            self.risk_premium +
            self.liquidity_premium +
            self.duration_premium +
            self.market_conditions_adjustment +
            self.reputation_adjustment +
            self.collateral_adjustment +
            self.network_adjustment +
            self.defi_yield_adjustment +
            self.governance_adjustment
        )


@dataclass
class RateCalculation:
    """Complete interest rate calculation result"""
    borrower_address: AlgorandAddress
    loan_amount_usd: Decimal
    loan_duration_days: int
    collateral_assets: List[str]
    collateral_value_usd: Decimal
    rate_factors: RateFactors
    final_interest_rate: Decimal
    effective_apr: Decimal
    staking_metrics: StakingMetrics
    reputation_score: ReputationScore
    network_metrics: NetworkMetrics
    market_condition: str
    borrower_risk_tier: RiskTier
    loan_risk_score: Decimal  # 0-1, higher is riskier
    collateral_risk_score: Decimal
    min_rate: Decimal
    max_rate: Decimal
    confidence_interval: Decimal
    calculation_timestamp: datetime
    model_version: str
    data_freshness_score: Decimal


# =============================================================================
# Loan Models
# =============================================================================

@dataclass
class LoanRequest:
    """Loan application request"""
    application_id: str
    borrower_address: AlgorandAddress
    loan_amount: Decimal  # Amount requested
    loan_currency: str  # ALGO or ASA symbol
    requested_term_days: int
    purpose: str
    collateral_assets: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LoanTerms:
    """Approved loan terms"""
    approved_amount: Decimal
    interest_rate: Decimal
    loan_term_days: int
    ltv_ratio: Decimal
    collateral_requirements: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    monitoring_requirements: List[str] = field(default_factory=list)


@dataclass
class LoanDecision:
    """Final loan approval decision"""
    application_id: str
    borrower_address: AlgorandAddress
    decision: DecisionType
    confidence: DecisionConfidence
    overall_score: Decimal
    primary_factors: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    positive_factors: List[str] = field(default_factory=list)
    loan_terms: Optional[LoanTerms] = None
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    decision_timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    processing_time_seconds: Decimal = Decimal('0.0')
    algorithm_version: str = "1.0.0"


# =============================================================================
# Risk Assessment Models
# =============================================================================

@dataclass
class RiskScore:
    """Risk score with metadata"""
    value: Decimal  # 0-100 scale
    confidence: Decimal  # 0-1 scale
    level: RiskLevel
    factors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskProfile:
    """Comprehensive risk assessment"""
    address: AlgorandAddress
    overall_risk_score: Decimal
    risk_level: RiskLevel
    confidence: Decimal
    key_risk_factors: List[str]
    recommended_actions: List[str]
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    address: AlgorandAddress
    risk_profile: RiskProfile
    individual_profiles: Dict[str, Any] = field(default_factory=dict)
    assessment_metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Utility Functions
# =============================================================================

def risk_level_from_score(score: Decimal) -> RiskLevel:
    """Convert numeric score to risk level"""
    if score <= 20:
        return RiskLevel.VERY_LOW
    elif score <= 40:
        return RiskLevel.LOW
    elif score <= 60:
        return RiskLevel.MEDIUM
    elif score <= 80:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def confidence_from_completeness(completeness: Decimal) -> DecisionConfidence:
    """Convert data completeness to confidence level"""
    if completeness >= Decimal('0.95'):
        return DecisionConfidence.VERY_HIGH
    elif completeness >= Decimal('0.85'):
        return DecisionConfidence.HIGH
    elif completeness >= Decimal('0.70'):
        return DecisionConfidence.MEDIUM
    elif completeness >= Decimal('0.50'):
        return DecisionConfidence.LOW
    else:
        return DecisionConfidence.VERY_LOW


def validate_loan_request(request: LoanRequest) -> List[str]:
    """Validate loan request and return list of issues"""
    issues = []

    if request.loan_amount <= 0:
        issues.append("Loan amount must be positive")

    if request.requested_term_days <= 0:
        issues.append("Loan term must be positive")

    if not request.purpose.strip():
        issues.append("Loan purpose is required")

    if not request.borrower_address.is_valid():
        issues.append("Invalid borrower address")

    return issues


# Export all models for easy importing
__all__ = [
    # Enums
    "AssetType", "LiquidityTier", "RiskLevel", "RiskTier", "DecisionType",
    "DecisionConfidence", "NetworkHealth",

    # Core models
    "AlgorandAddress", "ASAToken",

    # Collateral models
    "AssetValuation", "LiquidationScenario", "CollateralPosition",
    "PortfolioRisk", "CollateralAnalysis",

    # Interest rate models
    "StakingMetrics", "DeFiYieldData", "ReputationScore", "ASARiskMetrics",
    "NetworkMetrics", "LiquidityMetrics", "RateFactors", "RateCalculation",

    # Loan models
    "LoanRequest", "LoanTerms", "LoanDecision",

    # Risk models
    "RiskScore", "RiskProfile", "RiskAssessment",

    # Utility functions
    "risk_level_from_score", "confidence_from_completeness", "validate_loan_request"
]