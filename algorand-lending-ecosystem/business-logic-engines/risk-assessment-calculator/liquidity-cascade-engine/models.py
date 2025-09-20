"""
Data models for liquidity cascade risk assessment
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LiquidationType(Enum):
    INDIVIDUAL = "individual"
    CASCADE = "cascade"
    SPIRAL = "spiral"
    FLASH_CRASH = "flash_crash"


class StablecoinType(Enum):
    ALGORITHMIC = "algorithmic"
    COLLATERALIZED = "collateralized"
    HYBRID = "hybrid"
    FIAT_BACKED = "fiat_backed"


@dataclass
class LiquidationEvent:
    """Individual liquidation event data"""
    event_id: str
    timestamp: datetime
    liquidated_address: str
    liquidator_address: str
    collateral_asset_id: int
    debt_asset_id: int
    collateral_amount: float
    debt_amount: float
    liquidation_penalty: float
    price_at_liquidation: float
    market_impact: float  # Price impact of the liquidation
    triggered_by: str  # "price_drop", "health_factor", "cascade"
    cascade_depth: int  # How many hops from original trigger
    time_to_liquidation_ms: int  # Time from trigger to liquidation


@dataclass
class MarketDepthRisk:
    """Market depth and liquidity risk assessment"""
    asset_id: int
    asset_symbol: str
    total_liquidity: float
    order_book_depth: Dict[float, float]  # Price level -> Available liquidity
    bid_ask_spread: float
    price_impact_analysis: Dict[float, float]  # Trade size -> Price impact %
    liquidity_concentration: float  # Gini coefficient of liquidity distribution
    large_trader_exposure: float  # % of liquidity held by top 10 traders
    average_daily_volume: float
    volume_volatility: float
    liquidity_withdrawal_risk: float  # Risk of sudden liquidity reduction
    cross_exchange_arbitrage_efficiency: float


@dataclass
class StablecoinRisk:
    """Stablecoin stability and depeg risk"""
    stablecoin_id: int
    stablecoin_symbol: str
    stablecoin_type: StablecoinType
    current_peg_deviation: float  # Deviation from $1.00
    historical_max_depeg: float
    depeg_frequency: int  # Number of significant depegs in last year
    collateralization_ratio: float  # For collateralized stablecoins
    collateral_diversity: float  # Diversification of backing assets
    redemption_mechanism_efficiency: float
    mint_burn_asymmetry: float  # Difference in mint vs burn dynamics
    governance_centralization: float
    regulatory_risk_score: float
    liquidity_depth: float  # Liquidity available for large trades
    stress_test_results: Dict[str, float]  # Scenario -> Stability score


@dataclass
class CorrelationRisk:
    """Asset correlation and systemic risk assessment"""
    asset_correlation_matrix: Dict[int, Dict[int, float]]  # Asset ID correlation matrix
    liquidation_correlation: Dict[int, float]  # Asset -> Liquidation correlation
    market_beta: Dict[int, float]  # Asset -> Market beta
    systemic_risk_factors: List[str]
    contagion_pathways: List[List[int]]  # Asset chains that spread risk
    diversification_effectiveness: float
    tail_risk_correlation: float  # Correlation during extreme events
    volatility_clustering: float  # Tendency for volatile periods to cluster
    jump_risk_correlation: float  # Correlation of sudden price jumps


@dataclass
class CascadeSimulationResult:
    """Results from liquidation cascade simulation"""
    scenario_name: str
    initial_trigger: Dict[str, Any]  # What triggered the cascade
    total_liquidated_value: float
    liquidation_events: List[LiquidationEvent]
    max_cascade_depth: int
    time_to_resolution_hours: float
    worst_price_impact: Dict[int, float]  # Asset -> Max price impact
    systemic_risk_materialized: bool
    recovery_time_estimate_hours: float
    residual_risk_factors: List[str]


@dataclass
class StressTestScenario:
    """Stress testing scenario configuration and results"""
    scenario_name: str
    scenario_type: str  # "market_crash", "liquidity_crisis", "stablecoin_depeg"
    parameters: Dict[str, Any]
    price_shocks: Dict[int, float]  # Asset ID -> Price change %
    liquidity_shocks: Dict[int, float]  # Asset ID -> Liquidity reduction %
    correlation_stress: float  # Increased correlation factor
    simulation_results: Optional[CascadeSimulationResult]
    confidence_level: float  # Confidence in scenario likelihood
    historical_precedent: Optional[str]


@dataclass
class CascadeRiskScore:
    """Comprehensive cascade risk scoring"""
    liquidation_modeling_risk: float
    market_depth_risk: float
    stablecoin_stability_risk: float
    correlation_amplification_risk: float
    systemic_contagion_risk: float
    overall_score: float
    risk_level: RiskLevel
    confidence_interval: Tuple[float, float]

    # Risk factor analysis
    primary_vulnerability_sources: List[str]
    cascade_trigger_probabilities: Dict[str, float]
    worst_case_scenario_impact: float
    mitigation_effectiveness: Dict[str, float]
    monitoring_priorities: List[str]


@dataclass
class CascadeRiskProfile:
    """Comprehensive liquidity cascade risk profile"""
    address: str
    assessment_timestamp: datetime

    # Core risk components
    liquidation_events: List[LiquidationEvent]
    market_depth_risks: List[MarketDepthRisk]
    stablecoin_risks: List[StablecoinRisk]
    correlation_risks: Optional[CorrelationRisk]

    # Simulation and stress testing
    cascade_simulations: List[CascadeSimulationResult]
    stress_test_scenarios: List[StressTestScenario]

    # Risk scoring
    risk_score: CascadeRiskScore

    # Portfolio and position analysis
    position_concentration: Dict[int, float]  # Asset ID -> Position size
    leverage_metrics: Dict[str, float]
    collateral_diversity: float
    liquidation_thresholds: Dict[int, float]  # Asset -> Liquidation price
    health_factor_history: List[Tuple[datetime, float]]

    # Market environment factors
    market_volatility_regime: str  # "low", "medium", "high", "extreme"
    liquidity_environment: str  # "abundant", "normal", "constrained", "stressed"
    correlation_regime: str  # "normal", "elevated", "crisis"

    # Metadata
    data_sources: List[str]
    analysis_version: str
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'address': self.address,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'risk_level': self.risk_score.risk_level.value,
            'overall_risk_score': self.risk_score.overall_score,
            'confidence_interval': self.risk_score.confidence_interval,
            'liquidation_events_count': len(self.liquidation_events),
            'market_depth_risks_count': len(self.market_depth_risks),
            'stablecoin_risks_count': len(self.stablecoin_risks),
            'cascade_simulations_count': len(self.cascade_simulations),
            'stress_test_scenarios_count': len(self.stress_test_scenarios),
            'position_concentration': self.position_concentration,
            'leverage_metrics': self.leverage_metrics,
            'collateral_diversity': self.collateral_diversity,
            'market_volatility_regime': self.market_volatility_regime,
            'liquidity_environment': self.liquidity_environment,
            'correlation_regime': self.correlation_regime,
            'primary_vulnerabilities': self.risk_score.primary_vulnerability_sources,
            'worst_case_impact': self.risk_score.worst_case_scenario_impact
        }

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get summarized risk information"""
        return {
            'overall_risk': self.risk_score.risk_level.value,
            'score': self.risk_score.overall_score,
            'liquidation_risk': self.risk_score.liquidation_modeling_risk,
            'market_depth_risk': self.risk_score.market_depth_risk,
            'stablecoin_risk': self.risk_score.stablecoin_stability_risk,
            'systemic_risk': self.risk_score.systemic_contagion_risk,
            'position_concentration': max(self.position_concentration.values()) if self.position_concentration else 0,
            'leverage_ratio': self.leverage_metrics.get('total_leverage', 1.0),
            'health_factor': self.health_factor_history[-1][1] if self.health_factor_history else 1.0,
            'market_regime': {
                'volatility': self.market_volatility_regime,
                'liquidity': self.liquidity_environment,
                'correlation': self.correlation_regime
            }
        }