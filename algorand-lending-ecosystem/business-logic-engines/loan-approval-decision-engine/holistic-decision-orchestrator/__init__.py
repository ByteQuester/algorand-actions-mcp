"""
Holistic Decision Orchestrator for Algorand-Native Loan Approval

Master orchestration system that combines 6 specialized engines:
1. Ecosystem Analysis Engine (30% weight)
2. DeFi Behavior Engine (25% weight)
3. Collateral Intelligence Engine (20% weight)
4. Governance Reputation Engine (15% weight)
5. Network Risk Monitoring Engine (10% weight)
6. Holistic Decision Orchestrator (master coordinator)

This system implements a revolutionary approach to loan approval that considers
borrower participation in the Algorand ecosystem rather than traditional
banking metrics.
"""

__version__ = "1.0.0"
__author__ = "Algorand Lending Team"
__email__ = "lending@algorand.com"
__license__ = "MIT"

from .core.decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanDecision,
    DecisionConfidence,
    BorrowerProfile,
    LoanApplication,
    HolisticDecision
)

from .core.holistic_scoring import (
    HolisticScorer,
    EngineScore,
    HolisticScores
)

from .core.approval_logic import (
    ApprovalLogic,
    RiskLevel
)

from .core.conditions_generator import (
    ConditionsGenerator,
    LoanCondition,
    ConditionType,
    ConditionSeverity
)

from .core.alternative_proposer import (
    AlternativeProposer,
    Alternative,
    AlternativeType
)

from .core.monitoring_scheduler import (
    MonitoringScheduler,
    MonitoringTask,
    MonitoringFrequency,
    MonitoringParameter
)

# Main exports for the package
__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",

    # Core orchestrator
    "HolisticDecisionOrchestrator",

    # Main data models
    "LoanDecision",
    "DecisionConfidence",
    "BorrowerProfile",
    "LoanApplication",
    "HolisticDecision",

    # Scoring system
    "HolisticScorer",
    "EngineScore",
    "HolisticScores",

    # Decision logic
    "ApprovalLogic",
    "RiskLevel",

    # Conditions generation
    "ConditionsGenerator",
    "LoanCondition",
    "ConditionType",
    "ConditionSeverity",

    # Alternatives proposal
    "AlternativeProposer",
    "Alternative",
    "AlternativeType",

    # Monitoring system
    "MonitoringScheduler",
    "MonitoringTask",
    "MonitoringFrequency",
    "MonitoringParameter"
]

# Package configuration
PACKAGE_NAME = "algorand-holistic-decision-orchestrator"
SUPPORTED_PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

# Algorand network configuration defaults
DEFAULT_ALGORAND_CONFIG = {
    "network": "mainnet",
    "indexer_url": "https://mainnet-idx.algonode.cloud",
    "algod_url": "https://mainnet-api.algonode.cloud",
    "mcp_services": {
        "reader_port": 8002,
        "writer_port": 8003,
        "timeout": 30
    }
}

# Engine weight defaults
DEFAULT_ENGINE_WEIGHTS = {
    "ecosystem_analysis": 0.30,      # Algorand ecosystem participation
    "defi_behavior": 0.25,          # DeFi protocol behavior patterns
    "collateral_intelligence": 0.20, # Smart collateral analysis
    "governance_reputation": 0.15,   # Community governance participation
    "network_risk_monitoring": 0.10  # Real-time network risk assessment
}

# Approval threshold defaults
DEFAULT_APPROVAL_THRESHOLDS = {
    "excellent": 0.85,   # Auto-approve with premium terms
    "good": 0.70,       # Approve with standard terms
    "fair": 0.55,       # Approve with conservative terms
    "poor": 0.40,       # Conditional approval with strict terms
    "reject": 0.39      # Reject but offer alternatives
}

# CLI entry points
CLI_COMMANDS = {
    "holistic-loan-approver": "Master loan approval interface",
    "ecosystem-analyzer": "Borrower ecosystem analysis",
    "defi-behavior-checker": "DeFi behavior assessment",
    "collateral-intelligence": "Smart collateral analysis",
    "governance-reputation": "Community reputation checker",
    "network-risk-monitor": "Real-time risk monitoring"
}

def get_version() -> str:
    """Get the current version of the package."""
    return __version__

def get_default_config() -> dict:
    """Get default configuration for the orchestrator."""
    return {
        "algorand": DEFAULT_ALGORAND_CONFIG,
        "engine_weights": DEFAULT_ENGINE_WEIGHTS,
        "approval_thresholds": DEFAULT_APPROVAL_THRESHOLDS
    }

def get_cli_commands() -> dict:
    """Get available CLI commands and their descriptions."""
    return CLI_COMMANDS.copy()

# Package initialization message
import logging
logger = logging.getLogger(__name__)
logger.info(f"Algorand Holistic Decision Orchestrator v{__version__} initialized")
logger.info("Ready for Algorand-native loan approval decisions")

# Verify Python version compatibility
import sys
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
if python_version not in SUPPORTED_PYTHON_VERSIONS:
    logger.warning(
        f"Python {python_version} is not officially supported. "
        f"Supported versions: {', '.join(SUPPORTED_PYTHON_VERSIONS)}"
    )