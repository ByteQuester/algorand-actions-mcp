"""
Common Calculation Utilities for Blockchain Collateral Analysis

Shared mathematical functions and calculations used across all analysis engines.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from ..models.blockchain_collateral_models import (
    DigitalAsset,
    CollateralPosition,
    CollateralPortfolio,
    DigitalCollateralType,
)


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between minimum and maximum bounds."""
    return max(min_val, min(max_val, value))


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-1 range based on min/max bounds."""
    if max_val == min_val:
        return 0.0
    return clamp_value((value - min_val) / (max_val - min_val), 0.0, 1.0)


def calculate_asset_haircut(
    asset: DigitalAsset,
    market_conditions: str = "normal",
    base_haircuts: Optional[Dict[DigitalCollateralType, float]] = None,
    volatility_multiplier: float = 2.0,
    max_volatility_adjustment: float = 0.3
) -> float:
    """
    Calculate risk-adjusted haircut for a digital asset.

    Args:
        asset: Digital asset to calculate haircut for
        market_conditions: Current market conditions
        base_haircuts: Base haircut rates by asset type
        volatility_multiplier: Multiplier for volatility adjustment
        max_volatility_adjustment: Maximum volatility adjustment

    Returns:
        Calculated haircut percentage (0.0 to 1.0)
    """
    # Default base haircuts if not provided
    if base_haircuts is None:
        base_haircuts = {
            DigitalCollateralType.ALGO_NATIVE: 0.05,
            DigitalCollateralType.STABLECOIN: 0.02,
            DigitalCollateralType.ASA_TOKEN: 0.15,
            DigitalCollateralType.GOVERNANCE_TOKEN: 0.25,
            DigitalCollateralType.LP_TOKEN: 0.30,
            DigitalCollateralType.LIQUID_STAKING: 0.10,
        }

    # Base haircut from asset type
    base_haircut = base_haircuts.get(asset.asset_type, 0.10)

    # Volatility adjustment
    volatility_adjustment = min(
        asset.volatility_metrics.volatility_30d * volatility_multiplier,
        max_volatility_adjustment
    )

    # Liquidity adjustment
    liquidity_adjustments = {
        "high": 0.0,
        "medium": 0.05,
        "low": 0.15
    }
    liquidity_adjustment = liquidity_adjustments.get(
        asset.liquidity_metrics.liquidity_tier, 0.15
    )

    # Market condition adjustment
    market_adjustments = {
        "bull": -0.02,
        "normal": 0.0,
        "bear": 0.05,
        "crisis": 0.15
    }
    market_adjustment = market_adjustments.get(market_conditions, 0.0)

    # Total haircut
    total_haircut = base_haircut + volatility_adjustment + liquidity_adjustment + market_adjustment

    # Cap between 1% and 50%
    return clamp_value(total_haircut, 0.01, 0.50)


def calculate_herfindahl_hirschman_index(weights: List[float]) -> float:
    """
    Calculate Herfindahl-Hirschman Index for concentration measurement.

    Args:
        weights: List of portfolio weights (should sum to 1.0)

    Returns:
        HHI value (0 to 1, where 1 is maximum concentration)
    """
    return sum(w**2 for w in weights)


def calculate_portfolio_diversification(portfolio: CollateralPortfolio) -> float:
    """
    Calculate portfolio diversification score (0-1, higher is better).

    Args:
        portfolio: Collateral portfolio to analyze

    Returns:
        Diversification score (0.0 to 1.0)
    """
    if len(portfolio.positions) <= 1:
        return 0.0

    total_value = portfolio.total_value_usd
    if total_value <= 0:
        return 0.0

    # Calculate asset type distribution
    type_distribution = {}
    for position in portfolio.positions:
        asset_type = position.asset.asset_type
        if asset_type not in type_distribution:
            type_distribution[asset_type] = 0
        type_distribution[asset_type] += position.value_usd

    # Convert to proportions
    type_proportions = [v / total_value for v in type_distribution.values()]

    # Calculate Herfindahl-Hirschman Index (lower is more diversified)
    hhi = calculate_herfindahl_hirschman_index(type_proportions)

    # Convert to diversification score (0-1, higher is better)
    # Perfect diversification across 5 types would have HHI = 0.2
    max_hhi = 1.0  # Single asset
    min_hhi = 0.2  # Equally distributed across 5 types

    diversification_score = (max_hhi - hhi) / (max_hhi - min_hhi)
    return clamp_value(diversification_score, 0.0, 1.0)


def calculate_portfolio_var(
    portfolio: CollateralPortfolio,
    confidence_level: float = 0.95,
    time_horizon_days: int = 1
) -> float:
    """
    Calculate portfolio Value at Risk.

    Args:
        portfolio: Collateral portfolio to analyze
        confidence_level: Confidence level (0.90, 0.95, 0.99)
        time_horizon_days: Time horizon in days

    Returns:
        Portfolio VaR as percentage of total value
    """
    if not portfolio.positions:
        return 0.0

    portfolio_var = 0.0
    total_value = portfolio.total_value_usd

    for position in portfolio.positions:
        weight = position.value_usd / total_value if total_value > 0 else 0
        asset_var = position.asset.volatility_metrics.value_at_risk_95

        # Scale VaR by position weight (simplified independence assumption)
        weighted_var = (weight * asset_var) ** 2
        portfolio_var += weighted_var

    # Take square root for portfolio VaR
    portfolio_var = math.sqrt(portfolio_var)

    # Adjust for time horizon (assuming normal distribution)
    if time_horizon_days != 1:
        portfolio_var *= math.sqrt(time_horizon_days)

    # Adjust for confidence level if not 95%
    if confidence_level != 0.95:
        confidence_adjustments = {0.90: 0.85, 0.95: 1.0, 0.99: 1.3}
        multiplier = confidence_adjustments.get(confidence_level, 1.0)
        portfolio_var *= multiplier

    return portfolio_var


def calculate_liquidation_slippage(
    position_size_usd: float,
    daily_volume_usd: float,
    market_depth_1pct: float,
    liquidity_tier: str = "medium"
) -> float:
    """
    Calculate expected slippage for liquidating a position.

    Args:
        position_size_usd: Size of position to liquidate
        daily_volume_usd: Average daily trading volume
        market_depth_1pct: Market depth at 1% price impact
        liquidity_tier: Asset liquidity tier

    Returns:
        Expected slippage percentage
    """
    if daily_volume_usd <= 0:
        return 0.10  # 10% default slippage for illiquid assets

    # Base slippage from volume ratio
    volume_ratio = position_size_usd / daily_volume_usd

    # Slippage tiers based on liquidity
    tier_multipliers = {
        "high": 0.5,
        "medium": 1.0,
        "low": 2.0
    }
    multiplier = tier_multipliers.get(liquidity_tier, 2.0)

    # Calculate slippage using square root model
    base_slippage = math.sqrt(volume_ratio) * 0.05 * multiplier

    # Additional slippage if position exceeds market depth
    if position_size_usd > market_depth_1pct:
        depth_excess = (position_size_usd - market_depth_1pct) / market_depth_1pct
        additional_slippage = depth_excess * 0.02  # 2% per depth unit
        base_slippage += additional_slippage

    # Cap slippage between 0.1% and 25%
    return clamp_value(base_slippage, 0.001, 0.25)


def calculate_time_to_liquidate(
    position_size_usd: float,
    daily_volume_usd: float,
    liquidity_tier: str = "medium",
    max_daily_volume_ratio: float = 0.1
) -> float:
    """
    Calculate estimated time to liquidate a position in hours.

    Args:
        position_size_usd: Size of position to liquidate
        daily_volume_usd: Average daily trading volume
        liquidity_tier: Asset liquidity tier
        max_daily_volume_ratio: Maximum ratio of daily volume to use

    Returns:
        Estimated liquidation time in hours
    """
    if daily_volume_usd <= 0:
        return 168.0  # 1 week for illiquid assets

    # Calculate maximum daily liquidation amount
    max_daily_liquidation = daily_volume_usd * max_daily_volume_ratio

    # Time multipliers based on liquidity tier
    tier_multipliers = {
        "high": 0.5,
        "medium": 1.0,
        "low": 3.0
    }
    multiplier = tier_multipliers.get(liquidity_tier, 3.0)

    # Calculate days needed
    if max_daily_liquidation > 0:
        days_needed = position_size_usd / max_daily_liquidation
    else:
        days_needed = 7.0  # Default 1 week

    # Apply tier multiplier and convert to hours
    hours_needed = days_needed * 24 * multiplier

    # Cap between 1 hour and 1 week
    return clamp_value(hours_needed, 1.0, 168.0)


def calculate_confidence_score(
    price_feeds_count: int,
    price_consensus_strength: float,
    oracle_reliability: float,
    data_freshness: float,
    volatility_7d: float
) -> float:
    """
    Calculate confidence score for analysis results.

    Args:
        price_feeds_count: Number of price feeds available
        price_consensus_strength: Strength of price consensus (0-1)
        oracle_reliability: Oracle reliability score (0-1)
        data_freshness: Data freshness score (0-1)
        volatility_7d: 7-day volatility

    Returns:
        Confidence score (0.0 to 1.0)
    """
    # Feed diversity score
    feed_score = min(1.0, price_feeds_count / 5.0)  # Optimal at 5+ feeds

    # Consensus score
    consensus_score = price_consensus_strength

    # Oracle reliability score
    oracle_score = oracle_reliability

    # Data freshness score
    freshness_score = data_freshness

    # Volatility penalty (higher volatility reduces confidence)
    volatility_penalty = min(0.3, volatility_7d * 2.0)  # Max 30% penalty

    # Weighted average
    base_confidence = (
        feed_score * 0.20 +
        consensus_score * 0.25 +
        oracle_score * 0.25 +
        freshness_score * 0.30
    )

    # Apply volatility penalty
    final_confidence = base_confidence * (1.0 - volatility_penalty)

    return clamp_value(final_confidence, 0.0, 1.0)


def calculate_risk_metrics(
    positions: List[CollateralPosition],
    market_conditions: str = "normal"
) -> Dict[str, Any]:
    """
    Calculate comprehensive risk metrics for a list of positions.

    Args:
        positions: List of collateral positions
        market_conditions: Current market conditions

    Returns:
        Dictionary of risk metrics
    """
    if not positions:
        return {
            "total_value_usd": 0.0,
            "total_adjusted_value_usd": 0.0,
            "average_haircut": 0.0,
            "max_haircut": 0.0,
            "weighted_volatility": 0.0,
            "correlation_risk": 0.0,
            "liquidity_score": 0.0,
        }

    total_value = sum(pos.value_usd for pos in positions)
    total_adjusted_value = sum(pos.adjusted_value_usd for pos in positions)

    if total_value <= 0:
        return {
            "total_value_usd": 0.0,
            "total_adjusted_value_usd": 0.0,
            "average_haircut": 0.0,
            "max_haircut": 0.0,
            "weighted_volatility": 0.0,
            "correlation_risk": 0.0,
            "liquidity_score": 0.0,
        }

    # Calculate metrics
    average_haircut = 1.0 - (total_adjusted_value / total_value)
    max_haircut = max(pos.haircut_percentage for pos in positions)

    # Weighted volatility
    weighted_volatility = sum(
        (pos.value_usd / total_value) * pos.asset.volatility_metrics.volatility_30d
        for pos in positions
    )

    # Correlation risk (simplified)
    algo_correlations = [
        abs(pos.asset.volatility_metrics.correlation_with_algo)
        for pos in positions
    ]
    correlation_risk = sum(algo_correlations) / len(algo_correlations) if algo_correlations else 0.0

    # Liquidity score
    liquidity_scores = {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.3
    }
    weighted_liquidity = sum(
        (pos.value_usd / total_value) * liquidity_scores.get(
            pos.asset.liquidity_metrics.liquidity_tier, 0.3
        )
        for pos in positions
    )

    return {
        "total_value_usd": total_value,
        "total_adjusted_value_usd": total_adjusted_value,
        "average_haircut": average_haircut,
        "max_haircut": max_haircut,
        "weighted_volatility": weighted_volatility,
        "correlation_risk": correlation_risk,
        "liquidity_score": weighted_liquidity,
    }