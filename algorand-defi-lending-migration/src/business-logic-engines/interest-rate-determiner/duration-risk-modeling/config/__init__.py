"""
Duration Risk Modeling Configuration Module

Provides comprehensive configuration management for duration risk modeling,
term structure analysis, and prepayment risk assessment.
"""

from .duration_risk_config import (
    DurationRiskConfig,
    TermStructureParams,
    PrepaymentRiskParams,
    DurationRiskParams,
    AssetLiabilityParams,
    CryptoSpecificParams,
    MarketRiskParams,
    DEFAULT_DURATION_CONFIG
)

__all__ = [
    'DurationRiskConfig',
    'TermStructureParams',
    'PrepaymentRiskParams',
    'DurationRiskParams',
    'AssetLiabilityParams',
    'CryptoSpecificParams',
    'MarketRiskParams',
    'DEFAULT_DURATION_CONFIG'
]