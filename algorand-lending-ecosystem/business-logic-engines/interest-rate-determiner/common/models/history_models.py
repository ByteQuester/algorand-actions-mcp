"""
Models for rate calculation history and performance tracking.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum
import json


class CalculationStatus(Enum):
    """Status of rate calculation"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ModelType(Enum):
    """Types of rate calculation models"""
    BASIC = "BASIC"
    ENHANCED = "ENHANCED"
    ALGORAND_NATIVE = "ALGORAND_NATIVE"
    DEFI_OPTIMIZED = "DEFI_OPTIMIZED"
    MACHINE_LEARNING = "MACHINE_LEARNING"
    HYBRID = "HYBRID"


class PerformanceMetric(Enum):
    """Performance tracking metrics"""
    ACCURACY = "ACCURACY"
    PRECISION = "PRECISION"
    RECALL = "RECALL"
    F1_SCORE = "F1_SCORE"
    AUC_ROC = "AUC_ROC"
    MEAN_ABSOLUTE_ERROR = "MEAN_ABSOLUTE_ERROR"
    ROOT_MEAN_SQUARE_ERROR = "RMSE"
    CALCULATION_TIME = "CALCULATION_TIME"
    CONFIDENCE_CORRELATION = "CONFIDENCE_CORRELATION"


@dataclass
class CalculationMetrics:
    """Metrics for a single rate calculation"""

    # Timing metrics
    calculation_start_time: datetime
    calculation_end_time: datetime
    total_duration_ms: float

    # Component timing
    data_retrieval_ms: float = 0.0
    market_data_fetch_ms: float = 0.0
    credit_analysis_ms: float = 0.0
    algorand_analysis_ms: float = 0.0
    rate_computation_ms: float = 0.0
    validation_ms: float = 0.0

    # Data quality metrics
    data_completeness_score: float = 1.0
    market_data_freshness_score: float = 1.0
    credit_data_confidence: float = 1.0
    algorand_data_quality: float = 1.0

    # Calculation metrics
    iterations_required: int = 1
    convergence_achieved: bool = True
    confidence_score: float = 1.0

    # Resource usage
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    network_calls_count: int = 0

    # Error tracking
    errors_encountered: List[str] = field(default_factory=list)
    warnings_generated: List[str] = field(default_factory=list)

    # Metadata
    model_version: str = "1.0.0"
    calculation_id: str = ""

    def get_total_data_quality_score(self) -> float:
        """Calculate overall data quality score"""
        scores = [
            self.data_completeness_score,
            self.market_data_freshness_score,
            self.credit_data_confidence,
            self.algorand_data_quality
        ]
        return sum(scores) / len(scores)

    def is_performance_acceptable(self) -> bool:
        """Check if calculation performance meets standards"""
        return (
            self.total_duration_ms < 10000 and  # Less than 10 seconds
            self.confidence_score > 0.7 and     # At least 70% confidence
            self.get_total_data_quality_score() > 0.8 and  # Good data quality
            len(self.errors_encountered) == 0   # No errors
        )


@dataclass
class RateHistory:
    """Historical record of rate calculation"""

    # Request identification
    request_id: str
    response_id: str
    calculation_timestamp: datetime

    # Request details
    borrower_wallet: str
    loan_amount: Decimal
    duration_days: int
    loan_purpose: str

    # Calculated results
    annual_interest_rate: Decimal
    confidence_score: float
    risk_level: str

    # Rate components
    base_rate: Decimal
    risk_premium: Decimal
    duration_adjustment: Decimal
    collateral_discount: Decimal
    algorand_adjustment: Decimal
    defi_adjustment: Decimal

    # Market context
    fed_funds_rate: Decimal
    algo_price_usd: Decimal
    defi_avg_rate: Decimal
    market_volatility: float

    # Credit assessment results
    credit_score: Optional[int] = None
    on_chain_score: Optional[float] = None
    wallet_age_days: Optional[int] = None
    asa_diversity_score: Optional[float] = None

    # Calculation metadata
    model_type: ModelType = ModelType.BASIC
    model_version: str = "1.0.0"
    calculation_status: CalculationStatus = CalculationStatus.COMPLETED
    calculation_metrics: Optional[CalculationMetrics] = None

    # Actual outcomes (filled later)
    loan_approved: Optional[bool] = None
    actual_default: Optional[bool] = None
    actual_performance: Optional[str] = None

    # Validation results
    passed_validation: bool = True
    validation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = {
            'request_id': self.request_id,
            'response_id': self.response_id,
            'calculation_timestamp': self.calculation_timestamp.isoformat(),
            'borrower_wallet': self.borrower_wallet,
            'loan_amount': str(self.loan_amount),
            'duration_days': self.duration_days,
            'loan_purpose': self.loan_purpose,
            'annual_interest_rate': str(self.annual_interest_rate),
            'confidence_score': self.confidence_score,
            'risk_level': self.risk_level,
            'base_rate': str(self.base_rate),
            'risk_premium': str(self.risk_premium),
            'duration_adjustment': str(self.duration_adjustment),
            'collateral_discount': str(self.collateral_discount),
            'algorand_adjustment': str(self.algorand_adjustment),
            'defi_adjustment': str(self.defi_adjustment),
            'fed_funds_rate': str(self.fed_funds_rate),
            'algo_price_usd': str(self.algo_price_usd),
            'defi_avg_rate': str(self.defi_avg_rate),
            'market_volatility': self.market_volatility,
            'credit_score': self.credit_score,
            'on_chain_score': self.on_chain_score,
            'wallet_age_days': self.wallet_age_days,
            'asa_diversity_score': self.asa_diversity_score,
            'model_type': self.model_type.value,
            'model_version': self.model_version,
            'calculation_status': self.calculation_status.value,
            'loan_approved': self.loan_approved,
            'actual_default': self.actual_default,
            'actual_performance': self.actual_performance,
            'passed_validation': self.passed_validation,
            'validation_notes': self.validation_notes
        }

        # Add calculation metrics if available
        if self.calculation_metrics:
            data['calculation_metrics'] = {
                'total_duration_ms': self.calculation_metrics.total_duration_ms,
                'data_quality_score': self.calculation_metrics.get_total_data_quality_score(),
                'confidence_score': self.calculation_metrics.confidence_score,
                'errors_count': len(self.calculation_metrics.errors_encountered),
                'warnings_count': len(self.calculation_metrics.warnings_generated)
            }

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RateHistory':
        """Create from dictionary"""
        # Convert string decimals back to Decimal objects
        decimal_fields = [
            'loan_amount', 'annual_interest_rate', 'base_rate', 'risk_premium',
            'duration_adjustment', 'collateral_discount', 'algorand_adjustment',
            'defi_adjustment', 'fed_funds_rate', 'algo_price_usd', 'defi_avg_rate'
        ]

        for field in decimal_fields:
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))

        # Convert timestamp
        if isinstance(data['calculation_timestamp'], str):
            data['calculation_timestamp'] = datetime.fromisoformat(data['calculation_timestamp'])

        # Convert enums
        if 'model_type' in data:
            data['model_type'] = ModelType(data['model_type'])
        if 'calculation_status' in data:
            data['calculation_status'] = CalculationStatus(data['calculation_status'])

        # Remove calculation_metrics from data as it's handled separately
        data.pop('calculation_metrics', None)

        return cls(**data)


@dataclass
class PerformanceMetrics:
    """Performance tracking for rate calculation models"""

    # Time period
    period_start: datetime
    period_end: datetime
    total_calculations: int

    # Accuracy metrics
    prediction_accuracy: float = 0.0
    confidence_accuracy: float = 0.0
    mean_absolute_error: float = 0.0
    root_mean_square_error: float = 0.0

    # Performance distribution
    accuracy_by_risk_level: Dict[str, float] = field(default_factory=dict)
    accuracy_by_loan_size: Dict[str, float] = field(default_factory=dict)
    accuracy_by_duration: Dict[str, float] = field(default_factory=dict)

    # Speed metrics
    average_calculation_time_ms: float = 0.0
    p95_calculation_time_ms: float = 0.0
    slowest_calculation_time_ms: float = 0.0

    # Data quality impact
    accuracy_vs_data_quality_correlation: float = 0.0
    confidence_vs_accuracy_correlation: float = 0.0

    # Model comparison
    model_performance_comparison: Dict[str, float] = field(default_factory=dict)

    # Error analysis
    total_errors: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0

    # Business impact metrics
    loan_approval_rate: float = 0.0
    default_prediction_accuracy: float = 0.0
    revenue_impact_estimate: Decimal = Decimal('0')

    # Metadata
    model_version: str = "1.0.0"
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_overall_score(self) -> float:
        """Calculate overall performance score (0-1)"""
        # Weighted combination of key metrics
        accuracy_weight = 0.4
        speed_weight = 0.2
        reliability_weight = 0.2
        business_impact_weight = 0.2

        # Normalize speed (assuming target is 1 second)
        speed_score = max(0, 1 - (self.average_calculation_time_ms / 1000.0))

        # Reliability score (inverse of error rate)
        reliability_score = max(0, 1 - self.error_rate)

        # Business impact (normalize approval rate)
        business_score = self.loan_approval_rate

        overall_score = (
            self.prediction_accuracy * accuracy_weight +
            speed_score * speed_weight +
            reliability_score * reliability_weight +
            business_score * business_impact_weight
        )

        return min(max(overall_score, 0.0), 1.0)

    def get_performance_grade(self) -> str:
        """Get letter grade for performance"""
        score = self.calculate_overall_score()
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        elif score >= 0.55:
            return "C"
        elif score >= 0.5:
            return "C-"
        else:
            return "F"


@dataclass
class AuditTrail:
    """Audit trail for rate calculations and model changes"""

    # Event identification
    event_id: str
    event_type: str  # "calculation", "model_update", "config_change", "manual_override"
    timestamp: datetime
    user_id: Optional[str] = None

    # Event details
    description: str = ""
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)

    # Related objects
    request_id: Optional[str] = None
    response_id: Optional[str] = None
    model_version: Optional[str] = None

    # Compliance and governance
    approval_required: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    # Impact assessment
    impact_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    affected_calculations: int = 0
    business_justification: str = ""

    # Technical details
    system_context: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None

    # Metadata
    created_by: str = "system"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_audit_log_entry(self) -> str:
        """Convert to standardized audit log entry"""
        entry = {
            'timestamp': self.timestamp.isoformat(),
            'event_id': self.event_id,
            'event_type': self.event_type,
            'description': self.description,
            'impact_level': self.impact_level,
            'user_id': self.user_id,
            'approved_by': self.approved_by
        }

        # Add old/new values if present
        if self.old_values:
            entry['old_values'] = self.old_values
        if self.new_values:
            entry['new_values'] = self.new_values

        return json.dumps(entry, default=str, sort_keys=True)

    def requires_approval(self) -> bool:
        """Check if this event requires approval"""
        return (
            self.approval_required or
            self.impact_level in ["HIGH", "CRITICAL"] or
            self.event_type in ["model_update", "manual_override"]
        )

    def is_approved(self) -> bool:
        """Check if event is approved (if approval required)"""
        if not self.requires_approval():
            return True
        return self.approved_by is not None and self.approval_timestamp is not None