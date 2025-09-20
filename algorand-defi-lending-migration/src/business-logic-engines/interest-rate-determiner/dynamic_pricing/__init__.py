"""
Dynamic Pricing Module

Real-time interest rate adjustments based on market conditions, supply/demand,
and liquidity factors for responsive pricing in DeFi lending.
"""

from .core.pricing_engine import DynamicPricingEngine

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = ["DynamicPricingEngine"]