"""
Data models for blockchain behavior risk assessment
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


class TransactionType(Enum):
    PAYMENT = "payment"
    APP_CALL = "appl"
    ASSET_TRANSFER = "axfer"
    ASSET_CONFIG = "acfg"
    ASSET_FREEZE = "afrz"
    KEY_REGISTRATION = "keyreg"


class MEVType(Enum):
    FRONT_RUNNING = "front_running"
    BACK_RUNNING = "back_running"
    SANDWICH_ATTACK = "sandwich_attack"
    ARBITRAGE = "arbitrage"
    LIQUIDATION_BOT = "liquidation_bot"


@dataclass
class TransactionPattern:
    """Represents a detected transaction pattern"""
    pattern_type: str
    frequency: int
    time_window_hours: int
    addresses_involved: List[str]
    total_algo_volume: float
    avg_transaction_size: float
    risk_indicators: List[str]
    confidence_score: float
    first_seen: datetime
    last_seen: datetime


@dataclass
class WalletCluster:
    """Represents a cluster of related wallets"""
    cluster_id: str
    wallet_addresses: List[str]
    cluster_size: int
    total_balance: float
    shared_transaction_patterns: List[str]
    creation_time_proximity: float  # How close wallet creation times are
    transaction_timing_correlation: float
    shared_apps: List[int]  # Shared application IDs
    risk_score: float
    cluster_type: str  # "sybil", "exchange", "institutional", "family"


@dataclass
class MEVRiskIndicator:
    """MEV exploitation risk indicator"""
    mev_type: MEVType
    target_address: str
    exploiter_address: str
    transaction_sequence: List[str]  # Transaction IDs in sequence
    profit_extracted: float
    block_position_manipulation: bool
    time_between_txns_ms: int
    detection_confidence: float
    impact_severity: RiskLevel


@dataclass
class FlashLoanRisk:
    """Flash loan risk assessment"""
    loan_amount: float
    loan_asset_id: int
    borrower_address: str
    repayment_success: bool
    arbitrage_profit: float
    protocols_involved: List[str]
    execution_time_ms: int
    complexity_score: float  # Based on number of steps
    risk_level: RiskLevel


@dataclass
class BridgeActivityRisk:
    """Cross-chain bridge activity risk"""
    bridge_protocol: str
    source_chain: str
    destination_chain: str
    transfer_amount: float
    transfer_asset: str
    bridge_liquidity_depth: float
    slippage_tolerance: float
    time_to_finality_minutes: int
    validator_set_size: int
    historical_exploit_count: int
    current_risk_level: RiskLevel


@dataclass
class SybilDetectionResult:
    """Sybil attack detection result"""
    suspected_sybil_addresses: List[str]
    control_address: Optional[str]
    correlation_metrics: Dict[str, float]
    behavioral_similarity_score: float
    creation_pattern_analysis: Dict[str, Any]
    transaction_pattern_similarity: float
    funding_source_analysis: Dict[str, Any]
    confidence_level: float
    attack_vector_assessment: List[str]


@dataclass
class BehaviorRiskScore:
    """Individual behavior risk component scores"""
    transaction_anomaly_score: float
    wallet_clustering_risk: float
    mev_exploitation_risk: float
    flash_loan_risk: float
    bridge_activity_risk: float
    sybil_attack_risk: float
    overall_score: float
    risk_level: RiskLevel
    confidence_interval: Tuple[float, float]

    # Detailed breakdowns
    risk_factors: List[str]
    mitigation_recommendations: List[str]
    monitoring_priorities: List[str]


@dataclass
class BehaviorRiskProfile:
    """Comprehensive blockchain behavior risk profile"""
    address: str
    assessment_timestamp: datetime

    # Core risk components
    transaction_patterns: List[TransactionPattern]
    wallet_clusters: List[WalletCluster]
    mev_indicators: List[MEVRiskIndicator]
    flash_loan_activities: List[FlashLoanRisk]
    bridge_activities: List[BridgeActivityRisk]
    sybil_detection: Optional[SybilDetectionResult]

    # Risk scoring
    risk_score: BehaviorRiskScore

    # Historical context
    account_age_days: int
    total_transaction_count: int
    total_volume_algo: float
    unique_counterparties: int
    app_interactions: List[int]

    # Risk metadata
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
            'transaction_patterns_count': len(self.transaction_patterns),
            'wallet_clusters_count': len(self.wallet_clusters),
            'mev_indicators_count': len(self.mev_indicators),
            'flash_loan_activities_count': len(self.flash_loan_activities),
            'bridge_activities_count': len(self.bridge_activities),
            'sybil_risk_detected': self.sybil_detection is not None,
            'account_age_days': self.account_age_days,
            'total_transaction_count': self.total_transaction_count,
            'total_volume_algo': self.total_volume_algo,
            'risk_factors': self.risk_score.risk_factors,
            'mitigation_recommendations': self.risk_score.mitigation_recommendations
        }