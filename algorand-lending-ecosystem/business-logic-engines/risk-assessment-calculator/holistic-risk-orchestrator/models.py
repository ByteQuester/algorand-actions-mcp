"""
Data models for holistic risk orchestration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class MitigationPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RiskEngine(Enum):
    BLOCKCHAIN_BEHAVIOR = "blockchain_behavior"
    DEFI_PROTOCOL = "defi_protocol"
    LIQUIDITY_CASCADE = "liquidity_cascade"
    GOVERNANCE_STABILITY = "governance_stability"


@dataclass
class CrossEngineCorrelation:
    """Correlation analysis between different risk engines"""
    engine_1: RiskEngine
    engine_2: RiskEngine
    correlation_coefficient: float  # -1.0 to 1.0
    correlation_strength: str  # "weak", "moderate", "strong", "very_strong"
    risk_amplification_factor: float  # How much risks amplify each other
    historical_correlation_trend: List[Tuple[datetime, float]]
    common_risk_factors: List[str]
    interaction_mechanisms: List[str]  # How the risks interact
    systemic_risk_contribution: float  # Contribution to systemic risk
    confidence_level: float


@dataclass
class RiskAlert:
    """Risk alert with escalation information"""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    risk_engines_involved: List[RiskEngine]
    alert_type: str
    title: str
    description: str
    risk_score_threshold_exceeded: float
    current_risk_score: float
    affected_addresses: List[str]
    triggers: List[str]  # What triggered the alert
    immediate_actions: List[str]
    escalation_path: List[str]
    estimated_impact: Dict[str, float]
    time_to_critical: Optional[int]  # Minutes until critical threshold
    auto_mitigation_triggered: bool
    acknowledgment_required: bool
    related_alerts: List[str]  # Related alert IDs


@dataclass
class MitigationStrategy:
    """Risk mitigation strategy recommendation"""
    strategy_id: str
    priority: MitigationPriority
    target_risk_engines: List[RiskEngine]
    strategy_type: str  # "immediate", "short_term", "long_term", "structural"
    title: str
    description: str
    implementation_steps: List[str]
    estimated_cost: Dict[str, float]  # Cost type -> Amount
    estimated_time_to_implement: int  # Hours
    expected_risk_reduction: Dict[RiskEngine, float]  # Engine -> Risk reduction %
    success_probability: float
    dependencies: List[str]  # Dependencies on other strategies
    side_effects: List[str]  # Potential negative side effects
    monitoring_requirements: List[str]
    rollback_capability: bool
    regulatory_implications: List[str]


@dataclass
class MonitoringConfiguration:
    """Configuration for ongoing risk monitoring"""
    monitoring_frequency_seconds: int
    risk_threshold_levels: Dict[RiskLevel, float]
    alert_escalation_rules: Dict[AlertSeverity, Dict[str, Any]]
    correlation_monitoring_enabled: bool
    real_time_data_sources: List[str]
    historical_analysis_window_days: int
    anomaly_detection_sensitivity: float
    automated_response_enabled: bool
    notification_channels: List[str]
    monitoring_scope: Dict[RiskEngine, bool]


@dataclass
class HolisticRiskScore:
    """Comprehensive holistic risk score across all engines"""
    # Individual engine scores
    blockchain_behavior_score: float
    defi_protocol_score: float
    liquidity_cascade_score: float
    governance_stability_score: float

    # Cross-engine analysis
    correlation_amplification_score: float
    systemic_risk_score: float

    # Overall assessment
    overall_holistic_score: float
    risk_level: RiskLevel
    confidence_interval: Tuple[float, float]

    # Risk breakdown and analysis
    primary_risk_drivers: List[Tuple[RiskEngine, str, float]]  # Engine, factor, contribution
    cross_engine_vulnerabilities: List[str]
    systemic_failure_probability: float
    time_to_critical_risk: Optional[int]  # Minutes until critical risk

    # Scoring metadata
    scoring_methodology: str
    risk_weights: Dict[RiskEngine, float]
    correlation_matrix: Dict[RiskEngine, Dict[RiskEngine, float]]
    confidence_factors: Dict[str, float]


@dataclass
class ScenarioAnalysis:
    """Scenario analysis and stress testing results"""
    scenario_name: str
    scenario_type: str  # "historical", "synthetic", "stress_test", "black_swan"
    scenario_description: str
    probability_estimate: float

    # Scenario parameters
    market_conditions: Dict[str, float]
    external_shocks: Dict[str, float]
    behavioral_assumptions: Dict[str, Any]

    # Impact assessment
    impact_by_engine: Dict[RiskEngine, float]
    overall_impact_score: float
    cascading_effects: List[str]
    recovery_time_estimate_hours: float

    # Mitigation analysis
    current_resilience_score: float
    recommended_preparations: List[str]
    early_warning_indicators: List[str]


@dataclass
class RiskTrend:
    """Risk trend analysis over time"""
    engine: RiskEngine
    time_period_days: int
    trend_direction: str  # "increasing", "decreasing", "stable", "volatile"
    trend_strength: float  # 0.0 to 1.0
    risk_score_history: List[Tuple[datetime, float]]
    volatility: float
    momentum: float  # Rate of change
    seasonal_patterns: Dict[str, float]
    anomalies_detected: List[Tuple[datetime, str, float]]
    forecast_next_30_days: List[Tuple[datetime, float, float]]  # Date, predicted score, confidence


@dataclass
class HolisticRiskProfile:
    """Comprehensive holistic risk profile combining all engines"""
    address: str
    assessment_timestamp: datetime

    # Individual engine risk profiles
    blockchain_behavior_profile: Optional[Any]  # BehaviorRiskProfile
    defi_protocol_profile: Optional[Any]       # ProtocolRiskProfile
    liquidity_cascade_profile: Optional[Any]   # CascadeRiskProfile
    governance_stability_profile: Optional[Any] # GovernanceRiskProfile

    # Cross-engine analysis
    cross_engine_correlations: List[CrossEngineCorrelation]
    systemic_risk_factors: List[str]
    risk_amplification_chains: List[List[RiskEngine]]  # Risk propagation paths

    # Holistic scoring
    holistic_risk_score: HolisticRiskScore

    # Alerts and monitoring
    active_alerts: List[RiskAlert]
    monitoring_configuration: MonitoringConfiguration

    # Mitigation and recommendations
    recommended_mitigations: List[MitigationStrategy]
    implemented_mitigations: List[str]

    # Scenario analysis and forecasting
    scenario_analyses: List[ScenarioAnalysis]
    risk_trends: List[RiskTrend]

    # Portfolio and position context
    portfolio_value_at_risk: float
    position_concentration_risk: Dict[str, float]
    diversification_effectiveness: float
    hedging_effectiveness: float

    # External factors
    market_regime: Dict[str, str]  # volatility, liquidity, correlation regimes
    regulatory_environment: str
    competitive_landscape: str

    # Metadata and quality
    data_quality_score: float
    analysis_completeness: float
    limitations: List[str]
    data_sources: List[str]
    analysis_version: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'address': self.address,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'overall_risk_level': self.holistic_risk_score.risk_level.value,
            'overall_risk_score': self.holistic_risk_score.overall_holistic_score,
            'confidence_interval': self.holistic_risk_score.confidence_interval,
            'risk_scores_by_engine': {
                'blockchain_behavior': self.holistic_risk_score.blockchain_behavior_score,
                'defi_protocol': self.holistic_risk_score.defi_protocol_score,
                'liquidity_cascade': self.holistic_risk_score.liquidity_cascade_score,
                'governance_stability': self.holistic_risk_score.governance_stability_score,
            },
            'systemic_risk_score': self.holistic_risk_score.systemic_risk_score,
            'correlation_amplification': self.holistic_risk_score.correlation_amplification_score,
            'active_alerts_count': len(self.active_alerts),
            'high_severity_alerts': len([a for a in self.active_alerts if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]),
            'cross_engine_correlations_count': len(self.cross_engine_correlations),
            'strong_correlations': len([c for c in self.cross_engine_correlations if c.correlation_strength in ["strong", "very_strong"]]),
            'recommended_mitigations_count': len(self.recommended_mitigations),
            'urgent_mitigations': len([m for m in self.recommended_mitigations if m.priority == MitigationPriority.URGENT]),
            'portfolio_var': self.portfolio_value_at_risk,
            'diversification_score': self.diversification_effectiveness,
            'systemic_failure_probability': self.holistic_risk_score.systemic_failure_probability,
            'time_to_critical_risk': self.holistic_risk_score.time_to_critical_risk,
            'data_quality': self.data_quality_score,
            'primary_risk_drivers': [{'engine': driver[0].value, 'factor': driver[1], 'contribution': driver[2]} for driver in self.holistic_risk_score.primary_risk_drivers]
        }

    def get_executive_summary(self) -> Dict[str, Any]:
        """Get executive summary of risk assessment"""
        return {
            'overall_assessment': {
                'risk_level': self.holistic_risk_score.risk_level.value,
                'score': self.holistic_risk_score.overall_holistic_score,
                'confidence': 1 - (self.holistic_risk_score.confidence_interval[1] - self.holistic_risk_score.confidence_interval[0]) / 100
            },
            'key_risks': {
                'systemic_failure_probability': self.holistic_risk_score.systemic_failure_probability,
                'time_to_critical': self.holistic_risk_score.time_to_critical_risk,
                'portfolio_at_risk': self.portfolio_value_at_risk,
                'top_risk_factors': [f"{driver[0].value}: {driver[1]}" for driver in self.holistic_risk_score.primary_risk_drivers[:3]]
            },
            'immediate_actions': {
                'critical_alerts': len([a for a in self.active_alerts if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]),
                'urgent_mitigations': len([m for m in self.recommended_mitigations if m.priority == MitigationPriority.URGENT]),
                'monitoring_required': any(alert.acknowledgment_required for alert in self.active_alerts)
            },
            'risk_distribution': {
                engine.value: getattr(self.holistic_risk_score, f"{engine.value}_score")
                for engine in RiskEngine
            },
            'market_environment': self.market_regime,
            'assessment_quality': {
                'data_quality': self.data_quality_score,
                'completeness': self.analysis_completeness,
                'limitations_count': len(self.limitations)
            }
        }