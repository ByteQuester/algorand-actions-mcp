"""
Interest Rate Determiner Package

Pure Algorand/DeFi interest rate determination engines for blockchain-native lending.
Combines ALGO staking yields, DeFi protocol rates, on-chain reputation, ASA risk analysis,
network activity monitoring, and liquidity pool health analysis.

This package contains 6 Algorand-native engines:
1. ALGO Staking Engine - ALGO staking yield analysis
2. DeFi Yield Engine - DeFi protocol yield aggregation
3. Reputation Engine - On-chain reputation scoring
4. ASA Risk Engine - ASA volatility and risk assessment
5. Network Activity Engine - Algorand network activity monitoring
6. Liquidity Pool Engine - Liquidity pool health analysis
"""

# Core infrastructure imports
from .common.models import (
    AlgorandAccount,
    ASAToken,
    DeFiProtocol,
    ReputationScore,
    GovernanceData,
    NetworkActivity
)

from .common.algorand import (
    AlgorandClient,
    IndexerClient,
    ASAAnalyzer,
    GovernanceTracker
)

from .common.defi import (
    AlgofiClient,
    FolksFinanceClient,
    TinymanClient,
    ProtocolAggregator
)

from .common.utils import (
    YieldCalculator,
    ReputationCalculator,
    VolatilityAnalyzer,
    NetworkHealthMonitor
)

__version__ = "2.0.0"
__author__ = "Algorand DeFi Lending Ecosystem Team"
__email__ = "defi@algorand-lending.io"

__all__ = [
    # Core Data Models
    "AlgorandAccount",
    "ASAToken",
    "DeFiProtocol",
    "ReputationScore",
    "GovernanceData",
    "NetworkActivity",

    # Algorand Blockchain Integration
    "AlgorandClient",
    "IndexerClient",
    "ASAAnalyzer",
    "GovernanceTracker",

    # DeFi Protocol Integration
    "AlgofiClient",
    "FolksFinanceClient",
    "TinymanClient",
    "ProtocolAggregator",

    # Utility Functions
    "YieldCalculator",
    "ReputationCalculator",
    "VolatilityAnalyzer",
    "NetworkHealthMonitor"
]