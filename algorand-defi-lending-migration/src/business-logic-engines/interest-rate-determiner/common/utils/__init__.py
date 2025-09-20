"""
Algorand-specific utilities for DeFi interest rate determination.

Provides utility functions and calculations for:
- DeFi yield mathematics and compounding
- On-chain reputation scoring algorithms
- ASA volatility and risk analysis
- Network activity and health metrics
"""

from .yield_calculations import (
    YieldCalculator,
    CompoundingCalculator,
    APYConverter,
    ImpermanentLossCalculator
)

from .reputation_scoring import (
    ReputationCalculator,
    OnChainScorer,
    GovernanceScorer,
    BehaviorAnalyzer
)

from .volatility_analysis import (
    VolatilityAnalyzer,
    RiskMetrics,
    CorrelationAnalyzer,
    VaRCalculator
)

from .network_metrics import (
    NetworkHealthMonitor,
    ActivityScorer,
    ConsensusMetrics,
    BlockchainAnalyzer
)

__all__ = [
    # Yield calculations
    "YieldCalculator",
    "CompoundingCalculator",
    "APYConverter",
    "ImpermanentLossCalculator",

    # Reputation scoring
    "ReputationCalculator",
    "OnChainScorer",
    "GovernanceScorer",
    "BehaviorAnalyzer",

    # Volatility analysis
    "VolatilityAnalyzer",
    "RiskMetrics",
    "CorrelationAnalyzer",
    "VaRCalculator",

    # Network metrics
    "NetworkHealthMonitor",
    "ActivityScorer",
    "ConsensusMetrics",
    "BlockchainAnalyzer"
]