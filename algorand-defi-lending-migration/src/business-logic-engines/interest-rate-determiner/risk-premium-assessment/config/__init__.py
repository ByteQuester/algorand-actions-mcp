"""
Risk Premium Assessment Configuration Module

Provides comprehensive configuration management for risk assessment engines including
traditional credit scoring, Algorand on-chain behavior analysis, and market condition factors.
"""

from .risk_premium_config import (
    RiskPremiumConfig,
    CreditScoringWeights,
    OnChainBehaviorWeights,
    RiskThresholds,
    MarketConditionFactors,
    AlgorandSpecificParams,
    RiskPremiumRates,
    CrossChainScoringConfig,
    DEFAULT_CONFIG
)

__all__ = [
    'RiskPremiumConfig',
    'CreditScoringWeights',
    'OnChainBehaviorWeights',
    'RiskThresholds',
    'MarketConditionFactors',
    'AlgorandSpecificParams',
    'RiskPremiumRates',
    'CrossChainScoringConfig',
    'DEFAULT_CONFIG'
]