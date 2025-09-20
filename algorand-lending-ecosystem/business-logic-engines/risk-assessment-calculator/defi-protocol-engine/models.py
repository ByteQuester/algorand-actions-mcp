"""
Data models for DeFi protocol risk assessment
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


class ProtocolType(Enum):
    DEX = "dex"
    LENDING = "lending"
    YIELD_FARMING = "yield_farming"
    STABLECOIN = "stablecoin"
    DERIVATIVES = "derivatives"
    INSURANCE = "insurance"
    BRIDGE = "bridge"
    SYNTHETIC = "synthetic"


class SecurityRiskType(Enum):
    SMART_CONTRACT_BUG = "smart_contract_bug"
    ORACLE_MANIPULATION = "oracle_manipulation"
    GOVERNANCE_ATTACK = "governance_attack"
    FLASH_LOAN_EXPLOIT = "flash_loan_exploit"
    REENTRANCY = "reentrancy"
    FRONT_RUNNING = "front_running"
    MEV_EXPLOITATION = "mev_exploitation"


@dataclass
class ProtocolDependency:
    """Represents a protocol dependency relationship"""
    dependent_protocol_id: int
    dependency_protocol_id: int
    dependency_type: str  # "oracle", "liquidity", "collateral", "yield_source"
    dependency_strength: float  # 0.0 to 1.0
    risk_transmission_factor: float  # How much risk transmits through this dependency
    critical_failure_impact: bool  # Whether dependency failure would be critical
    last_interaction: datetime
    interaction_frequency: int  # Interactions per day
    alternative_protocols_available: int


@dataclass
class CrossProtocolExposure:
    """Cross-protocol exposure analysis"""
    primary_protocol_id: int
    exposed_protocols: List[int]
    total_exposure_value: float
    concentration_risk_score: float
    systemic_risk_multiplier: float  # How exposure amplifies systemic risk
    correlation_matrix: Dict[int, Dict[int, float]]  # Protocol correlation coefficients
    contagion_paths: List[List[int]]  # Paths through which risk can spread
    diversification_score: float  # How well diversified the exposure is
    max_single_protocol_exposure: float
    exposure_by_protocol_type: Dict[ProtocolType, float]


@dataclass
class SmartContractRisk:
    """Smart contract security risk assessment"""
    contract_address: str
    protocol_id: int
    risk_type: SecurityRiskType
    severity_level: RiskLevel
    vulnerability_description: str
    exploit_likelihood: float  # 0.0 to 1.0
    potential_loss_amount: float
    mitigation_measures: List[str]
    audit_status: str  # "audited", "partially_audited", "unaudited"
    audit_firms: List[str]
    time_since_deployment: int  # Days
    code_complexity_score: float
    external_dependencies: List[str]
    upgrade_mechanism: str  # "immutable", "upgradeable", "proxy"


@dataclass
class LiquidityRisk:
    """Liquidity provision and withdrawal risk"""
    protocol_id: int
    pool_address: str
    total_value_locked: float
    liquidity_depth: float
    impermanent_loss_risk: float
    withdrawal_timelock: int  # Hours
    slippage_for_large_trades: Dict[float, float]  # Trade size -> slippage %
    liquidity_concentration: float  # Gini coefficient of LP distribution
    top_lp_percentage: float  # % controlled by top 10 LPs
    historical_volatility: float
    correlation_with_market: float
    emergency_withdrawal_mechanisms: List[str]


@dataclass
class YieldFarmingRisk:
    """Yield farming strategy risk assessment"""
    strategy_id: str
    protocols_involved: List[int]
    estimated_apy: float
    apy_volatility: float
    underlying_asset_risks: List[str]
    smart_contract_risks: List[SmartContractRisk]
    liquidity_risks: List[LiquidityRisk]
    reward_token_risks: Dict[str, float]
    lock_up_period: int  # Days
    early_withdrawal_penalty: float
    strategy_complexity_score: float
    backtesting_performance: Dict[str, float]


@dataclass
class FlashLoanVulnerability:
    """Flash loan exploit vulnerability assessment"""
    protocol_id: int
    vulnerable_functions: List[str]
    max_flash_loan_amount: float
    flash_loan_fee: float
    oracle_dependencies: List[str]
    price_manipulation_risk: float
    reentrancy_protection: bool
    historical_exploits: List[Dict[str, Any]]
    mitigation_effectiveness: float
    monitoring_systems: List[str]


@dataclass
class ProtocolGovernanceRisk:
    """Protocol governance and upgrade risk"""
    protocol_id: int
    governance_token_concentration: float  # Gini coefficient
    voting_power_distribution: Dict[str, float]  # Address -> voting power %
    proposal_threshold: float  # % needed to propose
    quorum_requirement: float  # % needed for quorum
    timelock_duration: int  # Hours
    emergency_pause_capability: bool
    upgrade_mechanism: str
    governance_participation_rate: float
    historical_proposal_success_rate: float
    governance_attack_vectors: List[str]


@dataclass
class DeFiRiskScore:
    """Comprehensive DeFi protocol risk score"""
    cross_protocol_exposure_risk: float
    smart_contract_security_risk: float
    liquidity_provider_risk: float
    yield_farming_risk: float
    flash_loan_vulnerability_risk: float
    governance_risk: float
    overall_score: float
    risk_level: RiskLevel
    confidence_interval: Tuple[float, float]

    # Risk factor breakdowns
    primary_risk_factors: List[str]
    secondary_risk_factors: List[str]
    mitigation_recommendations: List[str]
    monitoring_priorities: List[str]
    risk_correlation_factors: Dict[str, float]


@dataclass
class ProtocolRiskProfile:
    """Comprehensive DeFi protocol risk profile"""
    address: str
    protocol_name: str
    protocol_type: ProtocolType
    assessment_timestamp: datetime

    # Core risk components
    cross_protocol_exposures: List[CrossProtocolExposure]
    smart_contract_risks: List[SmartContractRisk]
    liquidity_risks: List[LiquidityRisk]
    yield_farming_risks: List[YieldFarmingRisk]
    flash_loan_vulnerabilities: List[FlashLoanVulnerability]
    governance_risks: Optional[ProtocolGovernanceRisk]

    # Protocol dependencies and relationships
    protocol_dependencies: List[ProtocolDependency]
    dependent_protocols: List[int]  # Protocols that depend on this one

    # Risk scoring
    risk_score: DeFiRiskScore

    # Protocol metrics
    total_value_locked: float
    daily_volume: float
    user_count_active: int
    transaction_count_daily: int
    protocol_age_days: int
    upgrade_history: List[Dict[str, Any]]

    # External factors
    regulatory_risk_score: float
    market_position: str  # "leader", "established", "emerging", "experimental"
    competitive_moat: float
    team_reputation_score: float

    # Metadata
    data_sources: List[str]
    analysis_version: str
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'address': self.address,
            'protocol_name': self.protocol_name,
            'protocol_type': self.protocol_type.value,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'risk_level': self.risk_score.risk_level.value,
            'overall_risk_score': self.risk_score.overall_score,
            'confidence_interval': self.risk_score.confidence_interval,
            'cross_protocol_exposures_count': len(self.cross_protocol_exposures),
            'smart_contract_risks_count': len(self.smart_contract_risks),
            'liquidity_risks_count': len(self.liquidity_risks),
            'yield_farming_risks_count': len(self.yield_farming_risks),
            'flash_loan_vulnerabilities_count': len(self.flash_loan_vulnerabilities),
            'governance_risk_present': self.governance_risks is not None,
            'protocol_dependencies_count': len(self.protocol_dependencies),
            'total_value_locked': self.total_value_locked,
            'daily_volume': self.daily_volume,
            'protocol_age_days': self.protocol_age_days,
            'primary_risk_factors': self.risk_score.primary_risk_factors,
            'mitigation_recommendations': self.risk_score.mitigation_recommendations
        }

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get summarized risk information"""
        return {
            'overall_risk': self.risk_score.risk_level.value,
            'score': self.risk_score.overall_score,
            'top_risks': self.risk_score.primary_risk_factors[:3],
            'tvl': self.total_value_locked,
            'protocol_type': self.protocol_type.value,
            'cross_protocol_exposure': len(self.cross_protocol_exposures) > 0,
            'smart_contract_risks': len([r for r in self.smart_contract_risks if r.severity_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]),
            'governance_centralization': self.governance_risks.governance_token_concentration if self.governance_risks else 0.0
        }