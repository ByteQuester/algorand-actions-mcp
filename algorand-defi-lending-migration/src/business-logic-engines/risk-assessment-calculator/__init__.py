"""
Algorand Holistic Risk Assessment Calculator

Comprehensive risk orchestration system for Algorand ecosystem providing:
- Blockchain Behavior Risk Analysis
- DeFi Protocol Risk Assessment
- Liquidity Cascade Risk Modeling
- Governance Stability Risk Evaluation
- Holistic Risk Orchestration with Cross-Engine Correlation Analysis
"""

# Core orchestrator
try:
    from .holistic_risk_orchestrator.risk_orchestrator import HolisticRiskOrchestrator
    from .holistic_risk_orchestrator.models import (
        HolisticRiskProfile, HolisticRiskScore, RiskLevel, RiskEngine,
        CrossEngineCorrelation, RiskAlert, MitigationStrategy
    )
    from .holistic_risk_orchestrator.real_time_monitor import RealTimeRiskMonitor
except ImportError:
    # Fallback for development/partial installations
    HolisticRiskOrchestrator = None
    RealTimeRiskMonitor = None

# Individual risk engines
try:
    from .blockchain_behavior_engine.behavior_analyzer import BlockchainBehaviorAnalyzer
    from .defi_protocol_engine.protocol_analyzer import DeFiProtocolAnalyzer
    from .liquidity_cascade_engine.cascade_analyzer import LiquidityCascadeAnalyzer
    from .governance_stability_engine.governance_analyzer import GovernanceStabilityAnalyzer
except ImportError:
    # Fallback for development/partial installations
    BlockchainBehaviorAnalyzer = None
    DeFiProtocolAnalyzer = None
    LiquidityCascadeAnalyzer = None
    GovernanceStabilityAnalyzer = None

# Legacy risk calculator for backward compatibility
try:
    from .risk_calculator import RiskCalculator, RiskAssessment, BorrowerProfile, LoanDetails
except ImportError:
    RiskCalculator = None
    RiskAssessment = None
    BorrowerProfile = None
    LoanDetails = None

__version__ = "1.0.0"
__author__ = "Algorand Risk Assessment Team"

__all__ = [
    # Core orchestrator
    'HolisticRiskOrchestrator',
    'HolisticRiskProfile',
    'HolisticRiskScore',
    'RiskLevel',
    'RiskEngine',
    'CrossEngineCorrelation',
    'RiskAlert',
    'MitigationStrategy',

    # Individual engines
    'BlockchainBehaviorAnalyzer',
    'DeFiProtocolAnalyzer',
    'LiquidityCascadeAnalyzer',
    'GovernanceStabilityAnalyzer',

    # Monitoring
    'RealTimeRiskMonitor',

    # Legacy components
    'RiskCalculator',
    'RiskAssessment',
    'BorrowerProfile',
    'LoanDetails'
]