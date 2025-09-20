"""
Credit assessment models with on-chain behavior analysis.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum


class CreditRating(Enum):
    """Credit rating classifications"""
    AAA = "AAA"  # Exceptional
    AA = "AA"    # Excellent
    A = "A"      # Good
    BBB = "BBB"  # Fair
    BB = "BB"    # Poor
    B = "B"      # Very Poor
    CCC = "CCC"  # Extremely Poor
    D = "D"      # Default


class TransactionType(Enum):
    """Types of Algorand transactions"""
    PAYMENT = "PAYMENT"
    ASSET_TRANSFER = "ASSET_TRANSFER"
    ASSET_CONFIG = "ASSET_CONFIG"
    ASSET_FREEZE = "ASSET_FREEZE"
    APPLICATION_CALL = "APPLICATION_CALL"
    KEY_REGISTRATION = "KEY_REGISTRATION"
    STATE_PROOF = "STATE_PROOF"


class BehaviorPattern(Enum):
    """On-chain behavior patterns"""
    CONSERVATIVE = "CONSERVATIVE"      # Low risk, steady transactions
    ACTIVE_TRADER = "ACTIVE_TRADER"   # High volume trading
    DEFI_FARMER = "DEFI_FARMER"       # Yield farming activities
    HOLDER = "HOLDER"                 # Long-term holding
    SPECULATOR = "SPECULATOR"         # High risk trading
    INSTITUTIONAL = "INSTITUTIONAL"    # Large, regular transactions
    DORMANT = "DORMANT"               # Inactive wallet


@dataclass
class TransactionPattern:
    """Analysis of transaction patterns"""

    # Volume metrics
    total_transactions: int
    transaction_frequency: float  # transactions per day
    average_transaction_size: Decimal
    median_transaction_size: Decimal
    largest_transaction: Decimal

    # Timing patterns
    most_active_hours: List[int] = field(default_factory=list)
    weekend_activity_ratio: float = 0.0
    consistency_score: float = 0.0  # How regular are transactions

    # Transaction types
    transaction_type_distribution: Dict[TransactionType, int] = field(default_factory=dict)
    smart_contract_interaction_count: int = 0
    defi_protocol_interactions: Set[str] = field(default_factory=set)

    # Risk indicators
    failed_transaction_rate: float = 0.0
    dust_transaction_count: int = 0  # Very small transactions
    round_number_preference: float = 0.0  # Preference for round numbers

    # Metadata
    analysis_period_days: int = 365
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OnChainBehavior:
    """Comprehensive on-chain behavior analysis"""

    # Wallet basics
    wallet_age_days: int
    first_transaction_date: datetime
    last_transaction_date: datetime

    # Activity patterns
    transaction_patterns: TransactionPattern
    behavior_classification: BehaviorPattern

    # Portfolio composition
    algo_balance: Decimal
    total_asa_count: int
    asa_diversity_score: float  # Shannon diversity index
    largest_asa_holding_pct: float

    # DeFi participation
    defi_protocols_used: Set[str] = field(default_factory=set)
    liquidity_providing_history: bool = False
    yield_farming_activity: bool = False
    governance_participation: bool = False

    # Risk indicators
    high_risk_asa_exposure: float = 0.0  # Percentage in high-risk assets
    leverage_indicators: List[str] = field(default_factory=list)
    rugpull_exposure_count: int = 0  # Exposure to failed projects

    # Social/Network analysis
    unique_counterparties: int = 0
    whale_interactions: int = 0  # Interactions with large wallets
    exchange_deposit_frequency: float = 0.0

    # Compliance indicators
    suspicious_activity_flags: List[str] = field(default_factory=list)
    kyc_associated_exchanges: Set[str] = field(default_factory=set)

    # Metadata
    confidence_score: float = 1.0
    last_analysis: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WalletAnalysis:
    """Deep wallet analysis with predictive insights"""

    # Current state
    current_algo_balance: Decimal
    current_usd_value: Decimal
    total_assets_count: int

    # Historical performance
    balance_volatility: float
    maximum_balance_historical: Decimal
    minimum_balance_historical: Decimal
    balance_trend_6m: float  # Positive = growing, negative = declining

    # Liquidity analysis
    liquid_asset_percentage: float
    estimated_liquidation_time_days: int
    liquidity_stress_score: float  # 0 = very liquid, 1 = illiquid

    # Creditworthiness indicators
    payment_reliability_score: float  # Based on regular payments
    debt_service_capacity: Decimal  # Estimated monthly capacity
    collateral_quality_score: float

    # Predictive metrics
    default_probability_1y: float
    expected_balance_6m: Decimal
    stress_test_scenarios: Dict[str, float] = field(default_factory=dict)

    # Metadata
    analysis_confidence: float = 1.0
    model_version: str = "1.0.0"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CreditProfile:
    """Comprehensive credit profile combining traditional and on-chain data"""

    # Basic information
    wallet_address: str
    profile_creation_date: datetime

    # Traditional credit (if available)
    traditional_credit_score: Optional[int] = None
    debt_to_income_ratio: Optional[float] = None
    employment_verification: bool = False
    income_verification: bool = False

    # On-chain credit assessment
    on_chain_behavior: OnChainBehavior
    wallet_analysis: WalletAnalysis

    # Derived credit metrics
    composite_credit_score: int  # 300-850 scale
    algorand_native_score: int   # 0-100 scale specific to Algorand
    credit_rating: CreditRating

    # Risk assessment
    overall_risk_level: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    risk_factors: List[str] = field(default_factory=list)
    risk_mitigants: List[str] = field(default_factory=list)

    # Lending capacity
    max_unsecured_loan: Decimal
    max_secured_loan: Decimal
    recommended_ltv_ratio: float  # Loan-to-value ratio

    # Dynamic adjustments
    seasonal_adjustments: Dict[str, float] = field(default_factory=dict)
    market_condition_adjustments: Dict[str, float] = field(default_factory=dict)

    # Monitoring and alerts
    requires_enhanced_monitoring: bool = False
    alert_triggers: List[str] = field(default_factory=list)

    # Metadata
    profile_confidence: float = 1.0
    last_comprehensive_review: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    next_review_due: Optional[datetime] = None

    def calculate_default_probability(self, loan_amount: Decimal, duration_days: int) -> float:
        """Calculate probability of default for specific loan parameters"""
        # Base probability from wallet analysis
        base_prob = self.wallet_analysis.default_probability_1y

        # Adjust for loan size relative to capacity
        size_factor = float(loan_amount / max(self.wallet_analysis.current_usd_value, Decimal('1')))
        size_adjustment = min(size_factor * 0.1, 0.5)  # Cap at 50% increase

        # Adjust for duration
        duration_factor = (duration_days / 365.0)
        duration_adjustment = duration_factor * 0.05  # 5% per year

        # Combine factors
        adjusted_prob = base_prob + size_adjustment + duration_adjustment
        return min(max(adjusted_prob, 0.0), 1.0)  # Clamp between 0 and 1

    def get_recommended_rate_adjustment(self) -> Decimal:
        """Get recommended rate adjustment based on credit profile"""
        # Map credit rating to rate adjustment
        rating_adjustments = {
            CreditRating.AAA: Decimal('-0.02'),   # -2% discount
            CreditRating.AA: Decimal('-0.01'),    # -1% discount
            CreditRating.A: Decimal('0.00'),      # No adjustment
            CreditRating.BBB: Decimal('0.01'),    # +1% premium
            CreditRating.BB: Decimal('0.025'),    # +2.5% premium
            CreditRating.B: Decimal('0.05'),      # +5% premium
            CreditRating.CCC: Decimal('0.10'),    # +10% premium
            CreditRating.D: Decimal('0.20')       # +20% premium (if lending at all)
        }

        base_adjustment = rating_adjustments.get(self.credit_rating, Decimal('0.05'))

        # Additional adjustments based on Algorand-specific factors
        algo_adjustment = Decimal('0')

        # Reward long-term Algorand participation
        if self.on_chain_behavior.wallet_age_days > 730:  # 2+ years
            algo_adjustment -= Decimal('0.005')

        # Reward DeFi participation
        if len(self.on_chain_behavior.defi_protocols_used) > 2:
            algo_adjustment -= Decimal('0.005')

        # Reward governance participation
        if self.on_chain_behavior.governance_participation:
            algo_adjustment -= Decimal('0.002')

        return base_adjustment + algo_adjustment

    def is_eligible_for_unsecured_loan(self, amount: Decimal) -> bool:
        """Check if profile is eligible for unsecured loan of given amount"""
        return (amount <= self.max_unsecured_loan and
                self.credit_rating.value not in ['CCC', 'D'] and
                not self.requires_enhanced_monitoring)

    def get_collateral_requirements(self, loan_amount: Decimal) -> Dict[str, Any]:
        """Get collateral requirements for loan amount"""
        if self.is_eligible_for_unsecured_loan(loan_amount):
            return {"required": False, "ratio": 0.0}

        # Calculate required collateral ratio
        base_ratio = 1.2  # 120% minimum

        # Adjust based on credit rating
        rating_multipliers = {
            CreditRating.BBB: 1.0,
            CreditRating.BB: 1.2,
            CreditRating.B: 1.5,
            CreditRating.CCC: 2.0,
            CreditRating.D: 3.0
        }

        multiplier = rating_multipliers.get(self.credit_rating, 1.5)
        required_ratio = base_ratio * multiplier

        return {
            "required": True,
            "ratio": required_ratio,
            "min_collateral_value": loan_amount * Decimal(str(required_ratio)),
            "acceptable_assets": self._get_acceptable_collateral_assets()
        }

    def _get_acceptable_collateral_assets(self) -> List[str]:
        """Get list of acceptable collateral asset types"""
        # Based on credit rating and risk profile
        if self.credit_rating.value in ['AAA', 'AA', 'A']:
            return ['ALGO', 'USDC', 'BTC', 'ETH', 'GOLD', 'HIGH_GRADE_ASA']
        elif self.credit_rating.value in ['BBB', 'BB']:
            return ['ALGO', 'USDC', 'BTC', 'ETH']
        else:
            return ['ALGO', 'USDC']  # Only most liquid assets