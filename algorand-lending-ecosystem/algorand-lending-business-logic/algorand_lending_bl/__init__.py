"""
Algorand Lending Business Logic

A unified, vendorable package for Algorand-native lending business logic engines.
Consolidates collateral analysis, interest rate calculation, loan approval, and risk
assessment into clean, vendorable interfaces with all CLI dependencies removed.

Key Components:
- Collateral Analysis: Comprehensive collateral evaluation with real-time pricing
- Interest Rate Calculation: Multi-factor rate determination based on Algorand ecosystem data
- Loan Approval Engine: Holistic loan approval decisions
- Risk Assessment Engine: Comprehensive risk analysis with cross-engine correlation
"""

__version__ = "1.0.0"

# Core engines - simple direct imports
from .collateral import CollateralAnalyzer
from .interest_rates import InterestRateEngine
from .loan_approval import LoanApprovalEngine
from .risk_assessment import RiskAssessmentEngine

# Core models - consolidated from all engines
from .models import (
    # Core data models
    AlgorandAddress,
    ASAToken,

    # Collateral models
    AssetValuation,
    CollateralPosition,
    CollateralAnalysis,
    PortfolioRisk,
    LiquidationScenario,
    AssetType,
    LiquidityTier,

    # Interest rate models
    RateCalculation,
    RateFactors,
    StakingMetrics,
    ReputationScore,
    ASARiskMetrics,
    NetworkMetrics,
    DeFiYieldData,
    LiquidityMetrics,
    RiskTier,
    NetworkHealth,

    # Loan approval models
    LoanRequest,
    LoanDecision,
    LoanTerms,
    DecisionType,
    DecisionConfidence,

    # Risk assessment models
    RiskAssessment,
    RiskProfile,
    RiskScore,
    RiskLevel,

    # Utility functions
    risk_level_from_score,
    confidence_from_completeness,
    validate_loan_request
)

# Configuration classes - simplified
from .config import (
    AlgorandLendingConfig,
    NetworkConfig,
    CollateralConfig,
    InterestRateConfig,
    LoanApprovalConfig,
    RiskAssessmentConfig,
    ServiceConfig,
    DEFAULT_CONFIG,
    create_config_from_env,
    create_testnet_config,
    create_mainnet_config,
    validate_config
)

# All exports for external use
__all__ = [
    # Core engines
    "CollateralAnalyzer",
    "InterestRateEngine",
    "LoanApprovalEngine",
    "RiskAssessmentEngine",

    # Core data models
    "AlgorandAddress",
    "ASAToken",

    # Collateral models
    "AssetValuation",
    "CollateralPosition",
    "CollateralAnalysis",
    "PortfolioRisk",
    "LiquidationScenario",
    "AssetType",
    "LiquidityTier",

    # Interest rate models
    "RateCalculation",
    "RateFactors",
    "StakingMetrics",
    "ReputationScore",
    "ASARiskMetrics",
    "NetworkMetrics",
    "DeFiYieldData",
    "LiquidityMetrics",
    "RiskTier",
    "NetworkHealth",

    # Loan approval models
    "LoanRequest",
    "LoanDecision",
    "LoanTerms",
    "DecisionType",
    "DecisionConfidence",

    # Risk assessment models
    "RiskAssessment",
    "RiskProfile",
    "RiskScore",
    "RiskLevel",

    # Configuration
    "AlgorandLendingConfig",
    "NetworkConfig",
    "CollateralConfig",
    "InterestRateConfig",
    "LoanApprovalConfig",
    "RiskAssessmentConfig",
    "ServiceConfig",
    "DEFAULT_CONFIG",
    "create_config_from_env",
    "create_testnet_config",
    "create_mainnet_config",
    "validate_config",

    # Utility functions
    "risk_level_from_score",
    "confidence_from_completeness",
    "validate_loan_request"
]

# Package metadata for vendoring
VENDOR_INFO = {
    "name": "algorand-lending-business-logic",
    "version": __version__,
    "description": "Algorand-native lending business logic engines with collateral analysis and interest rate calculation",
    "protocols": ["direct"],
    "dependencies": ["algorand-sdk"],
    "min_python": "3.9",
    "engines": {
        "collateral_analyzer": "Comprehensive collateral analysis with real-time pricing and risk assessment",
        "interest_rate_engine": "Multi-factor interest rate calculation based on Algorand ecosystem data",
        "loan_approval": "Holistic loan approval decisions with ecosystem analysis",
        "risk_assessment": "Cross-engine risk correlation analysis"
    },
    "integration_guide": "README.md"
}

# Convenience function for quick setup
def create_lending_engines(config: AlgorandLendingConfig = None):
    """
    Create pre-configured lending engines.

    Args:
        config: Optional configuration object. Uses default if not provided.

    Returns:
        Tuple of (CollateralAnalyzer, InterestRateEngine, LoanApprovalEngine, RiskAssessmentEngine)
    """
    if config is None:
        config = DEFAULT_CONFIG

    collateral_analyzer = CollateralAnalyzer(config.collateral)
    interest_rate_engine = InterestRateEngine(config.interest_rates)
    loan_approval_engine = LoanApprovalEngine(config.loan_approval)
    risk_assessment_engine = RiskAssessmentEngine(config.risk_assessment)

    return collateral_analyzer, interest_rate_engine, loan_approval_engine, risk_assessment_engine


def create_lending_service(config: AlgorandLendingConfig = None):
    """
    Create a unified lending service with all engines.

    Args:
        config: Optional configuration object. Uses default if not provided.

    Returns:
        Dictionary with all engine instances
    """
    collateral_analyzer, interest_rate_engine, loan_approval_engine, risk_assessment_engine = create_lending_engines(config)

    return {
        "collateral": collateral_analyzer,
        "interest_rates": interest_rate_engine,
        "loan_approval": loan_approval_engine,
        "risk_assessment": risk_assessment_engine,
        "config": config or DEFAULT_CONFIG
    }


# Add convenience functions to exports
__all__.extend([
    "create_lending_engines",
    "create_lending_service",
    "VENDOR_INFO"
])