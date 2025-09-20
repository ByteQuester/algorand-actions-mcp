"""
Blockchain Risk Models

Comprehensive data models for blockchain-native risk assessment
focusing on Algorand DeFi lending protocols.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json


class RiskLevel(Enum):
    """Risk level enumeration for blockchain behaviors"""
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransactionType(Enum):
    """Algorand transaction types for risk analysis"""
    PAYMENT = "pay"
    KEY_REGISTRATION = "keyreg"
    ASSET_CONFIG = "acfg"
    ASSET_TRANSFER = "axfer"
    ASSET_FREEZE = "afrz"
    APPLICATION_CALL = "appl"
    STATE_PROOF = "stpf"


class BehaviorPattern(Enum):
    """Blockchain behavior patterns"""
    NORMAL = "NORMAL"
    VELOCITY_SPIKE = "VELOCITY_SPIKE"
    DORMANT_ACTIVATION = "DORMANT_ACTIVATION"
    WASH_TRADING = "WASH_TRADING"
    SYBIL_CLUSTER = "SYBIL_CLUSTER"
    MEV_EXPLOITATION = "MEV_EXPLOITATION"
    FLASH_LOAN_ARBITRAGE = "FLASH_LOAN_ARBITRAGE"
    BRIDGE_FARMING = "BRIDGE_FARMING"


@dataclass
class TransactionPattern:
    """Transaction pattern analysis for risk assessment"""
    wallet_address: str
    pattern_type: BehaviorPattern
    confidence_score: float
    time_window: timedelta
    transaction_count: int
    total_volume: float
    velocity_score: float
    anomaly_indicators: List[str]
    risk_factors: Dict[str, float]
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'wallet_address': self.wallet_address,
            'pattern_type': self.pattern_type.value,
            'confidence_score': self.confidence_score,
            'time_window_hours': self.time_window.total_seconds() / 3600,
            'transaction_count': self.transaction_count,
            'total_volume': self.total_volume,
            'velocity_score': self.velocity_score,
            'anomaly_indicators': self.anomaly_indicators,
            'risk_factors': self.risk_factors,
            'detection_timestamp': self.detection_timestamp.isoformat()
        }


@dataclass
class DeFiExposure:
    """DeFi protocol exposure analysis"""
    protocol_name: str
    tvl_exposure: float
    position_size: float
    concentration_risk: float
    liquidity_risk: float
    smart_contract_risk: float
    governance_participation: bool
    staking_positions: Dict[str, float]
    yield_farming_positions: Dict[str, float]
    cross_protocol_correlations: Dict[str, float]
    exposure_duration: timedelta
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def calculate_overall_exposure_risk(self) -> float:
        """Calculate overall exposure risk score"""
        base_risk = (
            self.concentration_risk * 0.3 +
            self.liquidity_risk * 0.25 +
            self.smart_contract_risk * 0.25 +
            sum(self.cross_protocol_correlations.values()) / len(self.cross_protocol_correlations) * 0.2
            if self.cross_protocol_correlations else 0
        )
        return min(base_risk, 1.0)


@dataclass
class SmartContractRisk:
    """Smart contract risk assessment"""
    contract_address: str
    audit_status: str
    vulnerability_score: float
    code_complexity_score: float
    upgrade_risk: float
    admin_key_risk: float
    oracle_dependency_risk: float
    interaction_frequency: int
    gas_efficiency_score: float
    time_lock_protection: bool
    multi_sig_protection: bool
    bug_bounty_coverage: bool
    formal_verification: bool
    risk_assessment_date: datetime = field(default_factory=datetime.utcnow)

    def calculate_contract_risk_score(self) -> float:
        """Calculate overall smart contract risk score"""
        base_risk = (
            self.vulnerability_score * 0.35 +
            self.upgrade_risk * 0.20 +
            self.admin_key_risk * 0.15 +
            self.oracle_dependency_risk * 0.15 +
            self.code_complexity_score * 0.15
        )

        # Apply protection factors
        protection_factor = 1.0
        if self.time_lock_protection:
            protection_factor *= 0.9
        if self.multi_sig_protection:
            protection_factor *= 0.85
        if self.bug_bounty_coverage:
            protection_factor *= 0.9
        if self.formal_verification:
            protection_factor *= 0.8

        return min(base_risk * protection_factor, 1.0)


@dataclass
class LiquidityRisk:
    """Liquidity risk assessment for assets and pools"""
    asset_id: str
    pool_address: Optional[str]
    daily_volume: float
    liquidity_depth: float
    bid_ask_spread: float
    slippage_1_percent: float
    slippage_5_percent: float
    market_cap: float
    circulating_supply: float
    holder_concentration: float
    exchange_listings: List[str]
    amm_pool_count: int
    impermanent_loss_risk: float
    correlation_with_algo: float

    def calculate_liquidity_risk_score(self) -> float:
        """Calculate overall liquidity risk score"""
        # Volume to market cap ratio
        volume_ratio = self.daily_volume / max(self.market_cap, 1)

        # Liquidity score components
        spread_risk = min(self.bid_ask_spread / 0.01, 1.0)  # Normalize to 1% spread
        slippage_risk = (self.slippage_1_percent + self.slippage_5_percent) / 2
        concentration_risk = self.holder_concentration

        base_risk = (
            spread_risk * 0.3 +
            slippage_risk * 0.3 +
            concentration_risk * 0.25 +
            (1 - min(volume_ratio * 10, 1.0)) * 0.15  # Lower volume = higher risk
        )

        return min(base_risk, 1.0)


@dataclass
class GovernanceRisk:
    """Protocol governance risk assessment"""
    protocol_name: str
    governance_token: str
    voter_participation_rate: float
    proposal_execution_delay: timedelta
    multi_sig_threshold: int
    total_multi_sig_signers: int
    community_treasury_size: float
    developer_fund_allocation: float
    governance_centralization_score: float
    recent_controversial_proposals: int
    upgrade_mechanism_risk: float
    emergency_pause_capability: bool

    def calculate_governance_risk_score(self) -> float:
        """Calculate overall governance risk score"""
        participation_risk = 1 - min(self.voter_participation_rate, 1.0)
        centralization_risk = self.governance_centralization_score

        # Multi-sig risk (lower threshold = higher risk)
        multisig_risk = 1 - min(self.multi_sig_threshold / max(self.total_multi_sig_signers, 1), 1.0)

        controversy_risk = min(self.recent_controversial_proposals / 10, 1.0)

        base_risk = (
            participation_risk * 0.25 +
            centralization_risk * 0.3 +
            multisig_risk * 0.2 +
            self.upgrade_mechanism_risk * 0.15 +
            controversy_risk * 0.1
        )

        return min(base_risk, 1.0)


@dataclass
class ASARisk:
    """Algorand Standard Asset (ASA) specific risk assessment"""
    asset_id: int
    asset_name: str
    creator_address: str
    total_supply: float
    circulating_supply: float
    freeze_enabled: bool
    clawback_enabled: bool
    manager_address: Optional[str]
    reserve_address: Optional[str]
    metadata_hash: Optional[str]
    url: Optional[str]
    creator_reputation_score: float
    asset_age_days: int
    holder_count: int
    transaction_count: int
    burn_history: List[Dict[str, Any]]
    mint_history: List[Dict[str, Any]]

    def calculate_asa_risk_score(self) -> float:
        """Calculate ASA-specific risk score"""
        # Admin control risks
        admin_risk = 0.0
        if self.freeze_enabled:
            admin_risk += 0.3
        if self.clawback_enabled:
            admin_risk += 0.4
        if self.manager_address:
            admin_risk += 0.2

        # Supply and distribution risks
        supply_concentration = 1 - (self.circulating_supply / max(self.total_supply, 1))
        holder_diversity = 1 / max(self.holder_count, 1)

        # Age and activity risks
        age_risk = max(0, (30 - self.asset_age_days) / 30)  # Higher risk for newer assets
        activity_risk = 1 / max(self.transaction_count, 1)

        # Creator reputation
        creator_risk = 1 - self.creator_reputation_score

        base_risk = (
            admin_risk * 0.35 +
            supply_concentration * 0.2 +
            holder_diversity * 0.15 +
            age_risk * 0.15 +
            activity_risk * 0.1 +
            creator_risk * 0.05
        )

        return min(base_risk, 1.0)


@dataclass
class ProtocolRisk:
    """DeFi protocol risk assessment"""
    protocol_name: str
    protocol_type: str  # AMM, Lending, Staking, etc.
    tvl: float
    daily_volume: float
    user_count: int
    smart_contract_addresses: List[str]
    audit_reports: List[Dict[str, Any]]
    bug_bounty_program: bool
    insurance_coverage: float
    governance_token: Optional[str]
    team_doxxed: bool
    regulatory_compliance: float
    oracle_dependencies: List[str]
    bridge_dependencies: List[str]
    yield_sustainability_score: float

    def calculate_protocol_risk_score(self) -> float:
        """Calculate overall protocol risk score"""
        # Size and maturity factors
        size_factor = min(self.tvl / 1_000_000, 1.0)  # Normalize to $1M TVL
        activity_factor = min(self.daily_volume / 100_000, 1.0)  # Normalize to $100k volume
        user_factor = min(self.user_count / 1000, 1.0)  # Normalize to 1k users

        # Security factors
        audit_factor = len(self.audit_reports) / 3  # Expect at least 3 audits
        insurance_factor = min(self.insurance_coverage / self.tvl, 1.0) if self.tvl > 0 else 0

        # Governance and compliance
        team_factor = 1.0 if self.team_doxxed else 0.5
        compliance_factor = self.regulatory_compliance

        # Calculate base risk (lower is better for these factors)
        security_score = (
            audit_factor * 0.4 +
            (1.0 if self.bug_bounty_program else 0.0) * 0.3 +
            insurance_factor * 0.3
        )

        maturity_score = (
            size_factor * 0.4 +
            activity_factor * 0.3 +
            user_factor * 0.3
        )

        governance_score = (
            team_factor * 0.6 +
            compliance_factor * 0.4
        )

        # Higher scores = lower risk
        overall_score = (
            security_score * 0.4 +
            maturity_score * 0.35 +
            governance_score * 0.25
        )

        return max(0, 1.0 - overall_score)


@dataclass
class SystemicRisk:
    """Systemic risk assessment across DeFi ecosystem"""
    assessment_date: datetime
    overall_market_volatility: float
    correlation_breakdown_risk: float
    liquidity_crunch_probability: float
    oracle_failure_risk: float
    bridge_failure_risk: float
    regulatory_crackdown_risk: float
    black_swan_event_probability: float
    cascade_failure_risk: float
    market_concentration_risk: float
    interconnectedness_score: float

    def calculate_systemic_risk_score(self) -> float:
        """Calculate overall systemic risk score"""
        return (
            self.overall_market_volatility * 0.15 +
            self.correlation_breakdown_risk * 0.12 +
            self.liquidity_crunch_probability * 0.15 +
            self.oracle_failure_risk * 0.10 +
            self.bridge_failure_risk * 0.08 +
            self.regulatory_crackdown_risk * 0.12 +
            self.black_swan_event_probability * 0.08 +
            self.cascade_failure_risk * 0.10 +
            self.market_concentration_risk * 0.05 +
            self.interconnectedness_score * 0.05
        )


@dataclass
class RiskAlert:
    """Risk alert for anomalous behavior or conditions"""
    alert_id: str
    alert_type: str
    severity: RiskLevel
    title: str
    description: str
    affected_addresses: List[str]
    affected_protocols: List[str]
    risk_score: float
    confidence: float
    detection_method: str
    evidence: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'affected_addresses': self.affected_addresses,
            'affected_protocols': self.affected_protocols,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'detection_method': self.detection_method,
            'evidence': self.evidence,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


@dataclass
class RiskMitigation:
    """Risk mitigation strategies and measures"""
    mitigation_id: str
    risk_type: str
    strategy: str
    implementation_steps: List[str]
    effectiveness_score: float
    cost_estimate: float
    timeline_days: int
    prerequisites: List[str]
    monitoring_requirements: List[str]
    success_metrics: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mitigation_id': self.mitigation_id,
            'risk_type': self.risk_type,
            'strategy': self.strategy,
            'implementation_steps': self.implementation_steps,
            'effectiveness_score': self.effectiveness_score,
            'cost_estimate': self.cost_estimate,
            'timeline_days': self.timeline_days,
            'prerequisites': self.prerequisites,
            'monitoring_requirements': self.monitoring_requirements,
            'success_metrics': self.success_metrics
        }


@dataclass
class HolisticRiskProfile:
    """Comprehensive risk profile for an entity or protocol"""
    entity_id: str
    entity_type: str  # wallet, protocol, asset
    assessment_timestamp: datetime

    # Core risk components
    transaction_patterns: List[TransactionPattern]
    defi_exposures: List[DeFiExposure]
    smart_contract_risks: List[SmartContractRisk]
    liquidity_risks: List[LiquidityRisk]
    governance_risks: List[GovernanceRisk]
    asa_risks: List[ASARisk]
    protocol_risks: List[ProtocolRisk]

    # Aggregated scores
    overall_risk_score: float
    risk_level: RiskLevel
    confidence_score: float

    # Risk factors breakdown
    risk_factor_scores: Dict[str, float]
    risk_factor_weights: Dict[str, float]

    # Alerts and mitigations
    active_alerts: List[RiskAlert]
    recommended_mitigations: List[RiskMitigation]

    # Metadata
    data_completeness: float
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def calculate_overall_risk(self) -> tuple[float, RiskLevel]:
        """Calculate overall risk score and level"""
        weighted_score = sum(
            self.risk_factor_scores.get(factor, 0) * weight
            for factor, weight in self.risk_factor_weights.items()
        )

        # Determine risk level
        if weighted_score <= 0.2:
            level = RiskLevel.MINIMAL
        elif weighted_score <= 0.4:
            level = RiskLevel.LOW
        elif weighted_score <= 0.6:
            level = RiskLevel.MODERATE
        elif weighted_score <= 0.8:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return weighted_score, level

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level.value,
            'confidence_score': self.confidence_score,
            'risk_factor_scores': self.risk_factor_scores,
            'risk_factor_weights': self.risk_factor_weights,
            'active_alerts': [alert.to_dict() for alert in self.active_alerts],
            'recommended_mitigations': [mitigation.to_dict() for mitigation in self.recommended_mitigations],
            'data_completeness': self.data_completeness,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class BlockchainRisk:
    """Main blockchain risk assessment container"""
    risk_profile: HolisticRiskProfile
    systemic_risk: SystemicRisk
    assessment_metadata: Dict[str, Any] = field(default_factory=dict)

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        return {
            'entity_id': self.risk_profile.entity_id,
            'overall_risk_score': self.risk_profile.overall_risk_score,
            'risk_level': self.risk_profile.risk_level.value,
            'systemic_risk_score': self.systemic_risk.calculate_systemic_risk_score(),
            'active_alert_count': len(self.risk_profile.active_alerts),
            'critical_alerts': [
                alert.to_dict() for alert in self.risk_profile.active_alerts
                if alert.severity == RiskLevel.CRITICAL
            ],
            'confidence': self.risk_profile.confidence_score,
            'last_updated': self.risk_profile.last_updated.isoformat()
        }