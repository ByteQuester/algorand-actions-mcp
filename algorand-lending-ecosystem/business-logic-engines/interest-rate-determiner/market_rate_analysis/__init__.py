"""
Market Rate Analysis Module

Analyzes market conditions to determine appropriate base interest rates for DeFi lending.
This module integrates with various data sources to provide real-time market-based pricing.
"""

from .core.market_engine import MarketRateAnalysisEngine

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = ["MarketRateAnalysisEngine"]