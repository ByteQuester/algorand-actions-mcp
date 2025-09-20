"""
Data models for governance stability risk assessment
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


class GovernanceType(Enum):
    ON_CHAIN = "on_chain"
    OFF_CHAIN = "off_chain"
    HYBRID = "hybrid"
    DELEGATED = "delegated"


class ProposalType(Enum):
    PARAMETER_CHANGE = "parameter_change"
    UPGRADE = "upgrade"
    TREASURY = "treasury"
    EMERGENCY = "emergency"
    ROUTINE = "routine"


class RegulatoryJurisdiction(Enum):
    US = "united_states"
    EU = "european_union"
    ASIA_PACIFIC = "asia_pacific"
    GLOBAL = "global"
    UNCERTAIN = "uncertain"


@dataclass
class VotingConcentrationRisk:
    """Voting power concentration analysis"""
    total_voting_power: float
    top_voter_percentage: float  # % held by largest voter
    top_5_voters_percentage: float  # % held by top 5 voters
    top_10_voters_percentage: float  # % held by top 10 voters
    gini_coefficient: float  # Inequality measure (0 = equal, 1 = total inequality)
    nakamoto_coefficient: int  # Min entities needed for 51% control
    voting_power_distribution: Dict[str, float]  # Address -> Voting power %
    delegation_concentration: float  # Concentration in delegated voting
    institutional_dominance: float  # % controlled by known institutions
    whale_threshold_analysis: Dict[float, int]  # Threshold -> Number of accounts above
    coordination_risk_score: float  # Risk of voter coordination
    sybil_resistance_score: float  # Resistance to sybil attacks


@dataclass
class ProposalRisk:
    """Individual governance proposal risk"""
    proposal_id: str
    proposal_type: ProposalType
    proposer_address: str
    proposer_voting_power: float
    proposal_content_hash: str
    quorum_requirement: float
    approval_threshold: float
    voting_period_hours: int
    current_participation_rate: float
    support_percentage: float
    opposition_percentage: float
    abstention_percentage: float
    whale_influence_score: float  # Influence of large voters
    last_minute_voting_pattern: bool  # Suspicious late voting
    proposal_complexity_score: float  # Technical complexity
    economic_impact_estimate: float  # Estimated economic impact
    controversy_score: float  # Level of community controversy
    manipulation_risk_indicators: List[str]


@dataclass
class ConsensusRisk:
    """Blockchain consensus mechanism risks"""
    consensus_mechanism: str  # "pure_pos", "dpos", "poa", etc.
    validator_count: int
    validator_concentration: float  # Gini coefficient of stake distribution
    validator_geographic_distribution: Dict[str, float]  # Country -> % of validators
    validator_infrastructure_diversity: Dict[str, float]  # Provider -> % of validators
    slashing_conditions: List[str]
    slashing_history: List[Dict[str, Any]]
    finality_time_seconds: float
    fork_choice_rule: str
    long_range_attack_resistance: float
    nothing_at_stake_resistance: float
    bribery_attack_cost: float  # Cost to bribe majority
    censorship_resistance_score: float
    liveness_guarantees: float
    safety_guarantees: float


@dataclass
class NetworkUpgradeRisk:
    """Network upgrade and protocol change risks"""
    upgrade_mechanism: str  # "hard_fork", "soft_fork", "governance_vote"
    upgrade_frequency: float  # Upgrades per year
    upgrade_testing_period_days: int
    backward_compatibility_policy: str
    emergency_upgrade_capability: bool
    upgrade_proposal_threshold: float  # % needed to propose upgrade
    upgrade_approval_threshold: float  # % needed to approve upgrade
    developer_concentration: float  # Concentration of core developers
    upgrade_coordination_risk: float  # Risk of coordination failures
    contentious_upgrade_history: List[Dict[str, Any]]
    rollback_capability: bool
    upgrade_monitoring_systems: List[str]


@dataclass
class RegulatoryRisk:
    """Regulatory and compliance risk assessment"""
    primary_jurisdiction: RegulatoryJurisdiction
    regulatory_clarity_score: float  # How clear regulations are
    compliance_burden_score: float  # Cost/complexity of compliance
    regulatory_change_frequency: float  # How often regulations change
    enforcement_risk_score: float  # Risk of enforcement action
    cross_border_complexity: float  # Complexity of multi-jurisdiction compliance
    aml_kyc_requirements: List[str]
    securities_law_exposure: float  # Risk of being classified as security
    taxation_complexity: float
    data_privacy_requirements: List[str]
    operational_restrictions: List[str]
    regulatory_sandboxes_available: List[str]
    industry_lobbying_strength: float
    regulatory_precedents: List[Dict[str, Any]]


@dataclass
class SystemicEcosystemRisk:
    """Systemic risks to the broader ecosystem"""
    ecosystem_dependency_concentration: float  # Concentration of ecosystem dependencies
    infrastructure_provider_concentration: float  # Concentration of infrastructure
    oracle_dependency_risk: float  # Risk from oracle dependencies
    bridge_dependency_risk: float  # Risk from cross-chain bridges
    stablecoin_ecosystem_exposure: float  # Exposure to stablecoin risks
    defi_protocol_concentration: float  # Concentration in DeFi protocols
    institutional_adoption_risk: float  # Risk from institutional dependency
    developer_ecosystem_health: float  # Health of developer ecosystem
    community_governance_maturity: float  # Maturity of governance processes
    economic_incentive_alignment: float  # Alignment of economic incentives
    network_effect_sustainability: float  # Sustainability of network effects
    competitive_threats: List[str]
    systemic_failure_scenarios: List[Dict[str, Any]]


@dataclass
class GovernanceAttackVector:
    """Identified governance attack vectors"""
    attack_type: str
    required_resources: Dict[str, float]  # Resource type -> Amount needed
    execution_complexity: float  # Complexity of executing attack
    detection_difficulty: float  # Difficulty of detecting attack
    potential_damage: float  # Potential damage if successful
    existing_defenses: List[str]
    mitigation_strategies: List[str]
    historical_precedents: List[str]
    current_threat_level: RiskLevel


@dataclass
class GovernanceRiskScore:
    """Comprehensive governance risk scoring"""
    voting_concentration_risk: float
    proposal_manipulation_risk: float
    consensus_mechanism_risk: float
    network_upgrade_risk: float
    regulatory_compliance_risk: float
    systemic_ecosystem_risk: float
    overall_score: float
    risk_level: RiskLevel
    confidence_interval: Tuple[float, float]

    # Risk analysis
    primary_governance_vulnerabilities: List[str]
    attack_vector_probabilities: Dict[str, float]
    governance_maturity_score: float
    decentralization_index: float
    resilience_factors: List[str]
    monitoring_priorities: List[str]


@dataclass
class GovernanceRiskProfile:
    """Comprehensive governance stability risk profile"""
    network_identifier: str  # Network or protocol identifier
    assessment_timestamp: datetime

    # Core governance components
    voting_concentration: Optional[VotingConcentrationRisk]
    active_proposals: List[ProposalRisk]
    consensus_risks: Optional[ConsensusRisk]
    upgrade_risks: Optional[NetworkUpgradeRisk]
    regulatory_risks: Optional[RegulatoryRisk]
    systemic_risks: Optional[SystemicEcosystemRisk]

    # Attack vectors and threats
    identified_attack_vectors: List[GovernanceAttackVector]
    threat_intelligence: Dict[str, Any]

    # Risk scoring
    risk_score: GovernanceRiskScore

    # Governance metrics
    governance_type: GovernanceType
    governance_maturity_years: float
    total_stakeholders: int
    active_governance_participants: int
    governance_participation_rate: float
    proposal_success_rate: float
    average_voting_duration_hours: float
    governance_treasury_size: float

    # Network characteristics
    network_value_locked: float
    daily_active_users: int
    transaction_volume_24h: float
    validator_uptime_percentage: float

    # External factors
    media_sentiment_score: float
    developer_activity_score: float
    community_health_score: float
    partnership_diversity_score: float

    # Metadata
    data_sources: List[str]
    analysis_version: str
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'network_identifier': self.network_identifier,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'risk_level': self.risk_score.risk_level.value,
            'overall_risk_score': self.risk_score.overall_score,
            'confidence_interval': self.risk_score.confidence_interval,
            'governance_type': self.governance_type.value,
            'voting_concentration_present': self.voting_concentration is not None,
            'active_proposals_count': len(self.active_proposals),
            'consensus_risks_present': self.consensus_risks is not None,
            'regulatory_risks_present': self.regulatory_risks is not None,
            'systemic_risks_present': self.systemic_risks is not None,
            'identified_attack_vectors_count': len(self.identified_attack_vectors),
            'governance_maturity_years': self.governance_maturity_years,
            'governance_participation_rate': self.governance_participation_rate,
            'decentralization_index': self.risk_score.decentralization_index,
            'primary_vulnerabilities': self.risk_score.primary_governance_vulnerabilities,
            'network_value_locked': self.network_value_locked,
            'validator_uptime_percentage': self.validator_uptime_percentage
        }

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get summarized risk information"""
        return {
            'overall_risk': self.risk_score.risk_level.value,
            'score': self.risk_score.overall_score,
            'voting_concentration': self.voting_concentration.top_10_voters_percentage if self.voting_concentration else 0,
            'consensus_risk': self.risk_score.consensus_mechanism_risk,
            'regulatory_risk': self.risk_score.regulatory_compliance_risk,
            'systemic_risk': self.risk_score.systemic_ecosystem_risk,
            'governance_maturity': self.risk_score.governance_maturity_score,
            'decentralization_index': self.risk_score.decentralization_index,
            'participation_rate': self.governance_participation_rate,
            'attack_vectors_count': len(self.identified_attack_vectors),
            'network_health': {
                'value_locked': self.network_value_locked,
                'daily_users': self.daily_active_users,
                'validator_uptime': self.validator_uptime_percentage
            }
        }