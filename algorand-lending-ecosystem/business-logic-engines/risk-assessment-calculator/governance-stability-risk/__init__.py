"""
Governance Stability and Systemic Risk Assessment Module

This module provides comprehensive governance stability and systemic risk assessment
capabilities for the Algorand ecosystem, including:

- Governance attack vector analysis and detection
- Voting concentration and power distribution monitoring
- Proposal manipulation detection systems
- Emergency response capability assessment
- Protocol upgrade risk analysis
- Regulatory compliance monitoring
- Network security assessment
- Foundation dependency analysis
- Integrated systemic risk evaluation

Key Components:
- GovernanceAnalyzer: Main governance stability analysis
- VotingConcentrationAnalyzer: Voting power concentration monitoring
- ProposalManipulationDetector: Proposal manipulation detection
- EmergencyResponseAnalyzer: Emergency response assessment
- ProtocolUpgradeRiskAnalyzer: Protocol upgrade risk analysis
- RegulatoryMonitor: Regulatory landscape monitoring
- NetworkSecurityMetrics: Network security assessment
- FoundationDependencyAnalyzer: Foundation dependency analysis
- SystemicRiskEngine: Master systemic risk assessment engine

Usage:
    from governance_stability_risk import SystemicRiskEngine

    engine = SystemicRiskEngine()
    report = await engine.assess_systemic_risk(input_data)
"""

from .core.systemic_engine import (
    SystemicRiskEngine,
    SystemicRiskReport,
    SystemicRiskMetrics,
    SystemicAlert,
    SystemicRiskLevel
)

from .core.governance_analyzer import (
    GovernanceAnalyzer,
    GovernanceStabilityReport,
    AttackVectorAssessment,
    RiskLevel,
    AttackVector
)

from .core.voting_concentration import (
    VotingConcentrationAnalyzer,
    VotingPowerMetrics,
    ConcentrationAlert,
    ConcentrationTrend,
    ConcentrationRiskLevel
)

from .core.proposal_manipulation import (
    ProposalManipulationDetector,
    ProposalManipulationReport,
    ManipulationIndicator,
    ManipulationType,
    ManipulationSeverity
)

from .core.emergency_response import (
    EmergencyResponseAnalyzer,
    ResponseReadinessReport,
    EmergencyProcedure,
    ResponseTeam,
    EmergencyScenario,
    EmergencyType,
    ResponseCapability
)

from .core.upgrade_risks import (
    ProtocolUpgradeRiskAnalyzer,
    UpgradeRiskReport,
    UpgradeMetrics,
    UpgradeRisk,
    CoordinationRisk,
    UpgradeRiskLevel,
    UpgradeType
)

from .core.regulatory_monitor import (
    RegulatoryMonitor,
    RegulatoryRiskReport,
    RegulatoryEvent,
    ComplianceRequirement,
    JurisdictionalRisk,
    RegulatoryEventType,
    RiskSeverity
)

from .core.network_security import (
    NetworkSecurityMetrics,
    SecurityRiskLevel
)

from .core.foundation_dependency import (
    FoundationDependencyAnalyzer,
    DependencyRiskLevel
)

__version__ = "1.0.0"
__author__ = "Algorand Ecosystem Risk Assessment Team"
__license__ = "MIT"

__all__ = [
    # Main systemic risk engine
    'SystemicRiskEngine',
    'SystemicRiskReport',
    'SystemicRiskMetrics',
    'SystemicAlert',
    'SystemicRiskLevel',

    # Governance analysis
    'GovernanceAnalyzer',
    'GovernanceStabilityReport',
    'AttackVectorAssessment',
    'RiskLevel',
    'AttackVector',

    # Voting concentration
    'VotingConcentrationAnalyzer',
    'VotingPowerMetrics',
    'ConcentrationAlert',
    'ConcentrationTrend',
    'ConcentrationRiskLevel',

    # Proposal manipulation
    'ProposalManipulationDetector',
    'ProposalManipulationReport',
    'ManipulationIndicator',
    'ManipulationType',
    'ManipulationSeverity',

    # Emergency response
    'EmergencyResponseAnalyzer',
    'ResponseReadinessReport',
    'EmergencyProcedure',
    'ResponseTeam',
    'EmergencyScenario',
    'EmergencyType',
    'ResponseCapability',

    # Upgrade risks
    'ProtocolUpgradeRiskAnalyzer',
    'UpgradeRiskReport',
    'UpgradeMetrics',
    'UpgradeRisk',
    'CoordinationRisk',
    'UpgradeRiskLevel',
    'UpgradeType',

    # Regulatory monitoring
    'RegulatoryMonitor',
    'RegulatoryRiskReport',
    'RegulatoryEvent',
    'ComplianceRequirement',
    'JurisdictionalRisk',
    'RegulatoryEventType',
    'RiskSeverity',

    # Network security
    'NetworkSecurityMetrics',
    'SecurityRiskLevel',

    # Foundation dependency
    'FoundationDependencyAnalyzer',
    'DependencyRiskLevel'
]

# Module metadata
GOVERNANCE_RISK_THRESHOLDS = {
    'critical_whale_threshold': 0.20,
    'high_risk_threshold': 0.15,
    'moderate_risk_threshold': 0.10,
    'flash_governance_window': 7200,  # 2 hours
    'minimum_deliberation_time': 172800  # 48 hours
}

SUPPORTED_ATTACK_VECTORS = [
    'flash_governance',
    'vote_buying',
    'whale_manipulation',
    'quorum_gaming',
    'proposal_spam',
    'delegation_attack',
    'sybil_attack',
    'governance_token_attack'
]

RISK_ASSESSMENT_COMPONENTS = [
    'governance_stability',
    'voting_concentration',
    'proposal_manipulation',
    'emergency_response',
    'upgrade_risks',
    'regulatory_compliance',
    'network_security',
    'foundation_dependency'
]

def get_version():
    """Get the current version of the governance risk assessment module"""
    return __version__

def get_supported_features():
    """Get list of supported risk assessment features"""
    return {
        'attack_vectors': SUPPORTED_ATTACK_VECTORS,
        'risk_components': RISK_ASSESSMENT_COMPONENTS,
        'risk_thresholds': GOVERNANCE_RISK_THRESHOLDS
    }

def create_default_engine():
    """Create a SystemicRiskEngine with default configuration"""
    return SystemicRiskEngine()

async def quick_assessment(input_data: dict) -> SystemicRiskReport:
    """
    Perform a quick systemic risk assessment

    Args:
        input_data: Dictionary containing governance, network, and other risk data

    Returns:
        SystemicRiskReport: Comprehensive risk assessment report
    """
    engine = create_default_engine()
    return await engine.assess_systemic_risk(input_data)