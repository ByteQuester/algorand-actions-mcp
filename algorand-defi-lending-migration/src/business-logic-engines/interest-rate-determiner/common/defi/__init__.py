"""
DeFi protocol integration for Algorand ecosystem.

Provides integration with major DeFi protocols on Algorand including:
- Algofi lending and borrowing rates
- Folks Finance yield data
- Tinyman DEX liquidity and rates
- Cross-protocol yield aggregation
"""

from .algofi_client import AlgofiClient, AlgofiRates
from .folks_finance_client import FolksFinanceClient, FolksRates
from .tinyman_client import TinymanClient, TinymanPools
from .protocol_aggregator import ProtocolAggregator, AggregatedRates

__all__ = [
    # Protocol clients
    "AlgofiClient",
    "AlgofiRates",
    "FolksFinanceClient",
    "FolksRates",
    "TinymanClient",
    "TinymanPools",

    # Aggregation
    "ProtocolAggregator",
    "AggregatedRates"
]