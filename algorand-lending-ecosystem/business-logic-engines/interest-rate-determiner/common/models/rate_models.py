"""
Enhanced rate calculation models with Algorand-specific features.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum


class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    EXTREME = "EXTREME"


class LoanPurpose(Enum):
    """Loan purpose classifications"""
    WORKING_CAPITAL = "WORKING_CAPITAL"
    ASSET_PURCHASE = "ASSET_PURCHASE"
    LIQUIDITY = "LIQUIDITY"
    DEFI_FARMING = "DEFI_FARMING"
    ASA_TRADING = "ASA_TRADING"
    SMART_CONTRACT = "SMART_CONTRACT"
    OTHER = "OTHER"


@dataclass
class RateComponent:
    """Individual component of interest rate calculation"""
    name: str
    value: Decimal
    weight: float
    description: str
    confidence: float = 1.0
    source: str = "internal"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConfidenceMetrics:
    """Metrics for confidence scoring"""
    overall_confidence: float
    data_completeness: float
    market_data_quality: float
    credit_data_quality: float
    algorand_data_quality: float
    model_accuracy: float
    temporal_relevance: float


@dataclass
class RateRequest:
    """Enhanced request for interest rate calculation with Algorand features"""

    # Basic loan parameters
    loan_amount: Decimal
    duration_days: int
    purpose: LoanPurpose

    # Algorand-specific parameters
    borrower_wallet_address: str
    collateral_asset_ids: List[int] = field(default_factory=list)
    collateral_values: Dict[int, Decimal] = field(default_factory=dict)

    # Traditional credit parameters
    borrower_credit_score: Optional[int] = None
    debt_to_income_ratio: Optional[float] = None

    # Market conditions
    market_conditions: Dict[str, Any] = field(default_factory=dict)

    # Risk assessment
    risk_score: Optional[int] = None
    manual_risk_override: Optional[RiskLevel] = None

    # Metadata
    request_id: str = field(default_factory=lambda: f"req_{int(datetime.now().timestamp())}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    originator: str = "system"

    # Validation flags
    require_on_chain_verification: bool = True
    require_asa_validation: bool = True
    require_defi_rate_check: bool = True


@dataclass
class RateResponse:
    """Enhanced response containing calculated interest rate and detailed breakdown"""

    # Primary rate information
    annual_interest_rate: Decimal
    effective_annual_rate: Decimal
    monthly_payment: Decimal
    total_interest: Decimal
    total_cost: Decimal

    # Rate breakdown
    rate_components: List[RateComponent]
    base_rate: Decimal
    risk_premium: Decimal
    duration_adjustment: Decimal
    collateral_discount: Decimal
    algorand_premium_discount: Decimal
    defi_market_adjustment: Decimal

    # Confidence and quality metrics
    confidence_metrics: ConfidenceMetrics
    overall_confidence_score: float

    # Risk assessment
    calculated_risk_level: RiskLevel
    risk_factors: List[str]
    risk_mitigants: List[str]

    # Algorand-specific insights
    on_chain_score: Optional[float] = None
    asa_diversity_score: Optional[float] = None
    defi_participation_score: Optional[float] = None
    wallet_age_score: Optional[float] = None

    # Explanations and recommendations
    explanation: str = ""
    detailed_breakdown: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metadata
    response_id: str = field(default_factory=lambda: f"resp_{int(datetime.now().timestamp())}")
    request_id: str = ""
    calculation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    calculation_duration_ms: Optional[float] = None
    engine_version: str = "1.0.0"

    # Market context
    market_snapshot: Dict[str, Any] = field(default_factory=dict)
    comparable_rates: Dict[str, Decimal] = field(default_factory=dict)

    # Validation results
    validation_passed: bool = True
    validation_warnings: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

    def get_rate_component_by_name(self, name: str) -> Optional[RateComponent]:
        """Get a specific rate component by name"""
        return next((comp for comp in self.rate_components if comp.name == name), None)

    def get_total_adjustments(self) -> Decimal:
        """Calculate total adjustments from base rate"""
        return (self.risk_premium + self.duration_adjustment +
                self.algorand_premium_discount + self.defi_market_adjustment -
                self.collateral_discount)

    def is_competitive(self, market_benchmark: Decimal, tolerance: Decimal = Decimal('0.005')) -> bool:
        """Check if rate is competitive within tolerance"""
        return abs(self.annual_interest_rate - market_benchmark) <= tolerance

    def get_confidence_breakdown(self) -> Dict[str, float]:
        """Get detailed confidence breakdown"""
        return {
            'overall': self.confidence_metrics.overall_confidence,
            'data_completeness': self.confidence_metrics.data_completeness,
            'market_data': self.confidence_metrics.market_data_quality,
            'credit_data': self.confidence_metrics.credit_data_quality,
            'algorand_data': self.confidence_metrics.algorand_data_quality,
            'model_accuracy': self.confidence_metrics.model_accuracy,
            'temporal_relevance': self.confidence_metrics.temporal_relevance
        }