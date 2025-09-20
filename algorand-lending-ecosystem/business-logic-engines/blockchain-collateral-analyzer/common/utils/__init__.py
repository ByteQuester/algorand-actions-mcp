"""
Common Utilities Module for Blockchain Collateral Analyzer

This module provides shared utility functions used across all blockchain collateral analysis engines.
"""

from .calculations import (
    calculate_asset_haircut,
    calculate_portfolio_diversification,
    calculate_portfolio_var,
    calculate_herfindahl_hirschman_index,
    calculate_liquidation_slippage,
    calculate_time_to_liquidate,
    calculate_confidence_score,
    calculate_risk_metrics,
    normalize_value,
    clamp_value,
)

from .validation import (
    validate_positive_number,
    validate_percentage,
    validate_ratio,
    validate_portfolio_weights,
    validate_market_conditions,
    validate_asset_symbol,
    validate_timestamp,
    ValidationError,
)

__all__ = [
    # Calculation utilities
    "calculate_asset_haircut",
    "calculate_portfolio_diversification",
    "calculate_portfolio_var",
    "calculate_herfindahl_hirschman_index",
    "calculate_liquidation_slippage",
    "calculate_time_to_liquidate",
    "calculate_confidence_score",
    "calculate_risk_metrics",
    "normalize_value",
    "clamp_value",

    # Validation utilities
    "validate_positive_number",
    "validate_percentage",
    "validate_ratio",
    "validate_portfolio_weights",
    "validate_market_conditions",
    "validate_asset_symbol",
    "validate_timestamp",
    "ValidationError",
]