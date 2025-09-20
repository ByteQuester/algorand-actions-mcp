"""
Common Models Module for Blockchain Collateral Analyzer

This module provides shared data models used across all blockchain collateral analysis engines.
"""

from .blockchain_collateral_models import (
    # Enums
    DigitalCollateralType,

    # Data Models
    VolatilityMetrics,
    LiquidityMetrics,
    PriceOracle,
    DigitalAsset,
    CollateralPosition,
    CollateralPortfolio,
    LiquidationScenario,
    CollateralAnalysisResult,

    # Validation Functions
    validate_volatility_metrics,
    validate_liquidity_metrics,
    validate_digital_asset,
)

__all__ = [
    # Enums
    "DigitalCollateralType",

    # Data Models
    "VolatilityMetrics",
    "LiquidityMetrics",
    "PriceOracle",
    "DigitalAsset",
    "CollateralPosition",
    "CollateralPortfolio",
    "LiquidationScenario",
    "CollateralAnalysisResult",

    # Validation Functions
    "validate_volatility_metrics",
    "validate_liquidity_metrics",
    "validate_digital_asset",
]