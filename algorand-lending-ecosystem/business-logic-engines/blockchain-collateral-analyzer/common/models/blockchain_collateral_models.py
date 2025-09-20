"""
Blockchain Collateral Data Models

Shared data models for digital asset collateral analysis on Algorand.
This module provides the common data structures used across all
blockchain collateral analysis engines.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class DigitalCollateralType(Enum):
    """Types of digital collateral supported"""
    ALGO_NATIVE = "algo_native"          # Native ALGO tokens
    ASA_TOKEN = "asa_token"              # Algorand Standard Assets
    STABLECOIN = "stablecoin"            # USDC, USDT, etc.
    GOVERNANCE_TOKEN = "governance"       # Protocol governance tokens
    LP_TOKEN = "lp_token"                # Liquidity pool tokens
    LIQUID_STAKING = "liquid_staking"    # Liquid staking derivatives


@dataclass
class VolatilityMetrics:
    """Volatility and risk metrics for digital assets"""
    volatility_30d: float                # 30-day historical volatility
    volatility_7d: float                 # 7-day historical volatility
    max_drawdown_30d: float              # Maximum 30-day drawdown
    value_at_risk_95: float              # 95% Value at Risk
    correlation_with_algo: float         # Correlation with ALGO
    stress_test_scenarios: Dict[str, float]  # Stress test results


@dataclass
class LiquidityMetrics:
    """Liquidity metrics for digital assets"""
    daily_volume_usd: float              # Average daily trading volume
    market_cap_usd: float                # Market capitalization
    depth_1_percent: float               # Market depth at 1% price impact
    largest_liquidation_size: float      # Largest liquidation without impact
    average_spread_bps: float            # Average bid-ask spread in basis points
    liquidity_tier: str                  # "high", "medium", "low"


@dataclass
class PriceOracle:
    """Price oracle configuration and reliability metrics"""
    primary_oracle: str                  # Primary price oracle source
    backup_oracles: List[str]            # Backup oracle sources
    update_frequency: int                # Update frequency in seconds
    reliability_score: float            # Oracle reliability (0-1)
    price_deviation_threshold: float    # Maximum acceptable price deviation
    fallback_mechanism: str             # Fallback strategy description


@dataclass
class DigitalAsset:
    """Digital asset definition with risk parameters"""
    asset_id: str                        # Unique asset identifier
    symbol: str                          # Asset symbol (e.g., "ALGO", "USDC")
    name: str                            # Full asset name
    asset_type: DigitalCollateralType    # Type of digital asset

    # Risk metrics
    volatility_metrics: VolatilityMetrics
    liquidity_metrics: LiquidityMetrics
    price_oracle: PriceOracle

    # Collateral parameters
    base_collateral_ratio: float        # Base required collateral ratio
    maintenance_ratio: float            # Maintenance threshold ratio
    liquidation_penalty: float          # Liquidation penalty percentage

    # Additional metadata
    contract_address: Optional[str] = None  # Smart contract address if applicable
    decimals: int = 6                    # Token decimal places
    is_active: bool = True               # Whether asset is actively supported


@dataclass
class CollateralPosition:
    """Individual collateral position"""
    asset: DigitalAsset
    quantity: float                      # Amount of asset held
    current_price_usd: float            # Current USD price
    value_usd: float                     # Total USD value
    haircut_percentage: float           # Applied haircut percentage
    adjusted_value_usd: float           # Value after haircut

    # Risk metrics
    price_confidence: float              # Price confidence level (0-1)
    liquidation_urgency: str             # "low", "medium", "high"
    time_to_liquidate_hours: float      # Estimated liquidation time


@dataclass
class CollateralPortfolio:
    """Portfolio of collateral positions"""
    positions: List[CollateralPosition]
    total_value_usd: float               # Total portfolio value
    total_adjusted_value_usd: float      # Total after haircuts
    diversification_score: float        # Portfolio diversification (0-1)
    correlation_risk: float              # Portfolio correlation risk

    # Portfolio-level risk metrics
    portfolio_var_95: float              # Portfolio VaR at 95%
    max_portfolio_drawdown: float       # Maximum expected drawdown
    liquidity_coverage_ratio: float     # Liquidity coverage ratio


@dataclass
class LiquidationScenario:
    """Liquidation scenario analysis"""
    scenario_name: str                   # Scenario description
    trigger_condition: str               # What triggers liquidation
    estimated_time_hours: float         # Time to complete liquidation
    expected_slippage: float             # Expected price slippage
    recovery_percentage: float          # Expected recovery rate
    market_impact: str                   # Expected market impact level


@dataclass
class CollateralAnalysisResult:
    """Complete collateral analysis result"""
    # Input parameters
    loan_amount_usd: float
    required_collateral_ratio: float

    # Portfolio analysis
    collateral_portfolio: CollateralPortfolio

    # Risk assessment
    risk_level: str                      # "low", "medium", "high", "critical"
    confidence_score: float              # Analysis confidence (0-1)

    # Collateral adequacy
    is_sufficient: bool                  # Whether collateral is sufficient
    surplus_deficit_usd: float           # Surplus (+) or deficit (-)

    # Liquidation analysis
    liquidation_scenarios: List[LiquidationScenario]
    average_liquidation_time: float     # Average time to liquidate

    # Recommendations
    recommended_actions: List[str]       # Specific recommendations
    monitoring_alerts: List[str]        # What to monitor closely

    # Metadata
    analysis_timestamp: datetime
    oracle_prices_timestamp: datetime
    market_conditions: str              # Current market condition assessment


# Utility functions for model validation

def validate_volatility_metrics(metrics: VolatilityMetrics) -> bool:
    """Validate volatility metrics are within reasonable bounds"""
    return (
        0 <= metrics.volatility_30d <= 5.0 and
        0 <= metrics.volatility_7d <= 5.0 and
        0 <= metrics.max_drawdown_30d <= 1.0 and
        0 <= metrics.value_at_risk_95 <= 1.0 and
        -1.0 <= metrics.correlation_with_algo <= 1.0
    )


def validate_liquidity_metrics(metrics: LiquidityMetrics) -> bool:
    """Validate liquidity metrics are reasonable"""
    return (
        metrics.daily_volume_usd >= 0 and
        metrics.market_cap_usd >= 0 and
        metrics.depth_1_percent >= 0 and
        metrics.average_spread_bps >= 0 and
        metrics.liquidity_tier in ["high", "medium", "low"]
    )


def validate_digital_asset(asset: DigitalAsset) -> bool:
    """Validate complete digital asset configuration"""
    return (
        validate_volatility_metrics(asset.volatility_metrics) and
        validate_liquidity_metrics(asset.liquidity_metrics) and
        1.0 <= asset.base_collateral_ratio <= 5.0 and
        1.0 <= asset.maintenance_ratio <= asset.base_collateral_ratio and
        0.0 <= asset.liquidation_penalty <= 0.5
    )


def validate_collateral_position(position: CollateralPosition) -> bool:
    """Validate collateral position data"""
    return (
        validate_digital_asset(position.asset) and
        position.quantity >= 0 and
        position.current_price_usd >= 0 and
        position.value_usd >= 0 and
        0.0 <= position.haircut_percentage <= 1.0 and
        position.adjusted_value_usd >= 0 and
        0.0 <= position.price_confidence <= 1.0 and
        position.liquidation_urgency in ["low", "medium", "high"] and
        position.time_to_liquidate_hours >= 0
    )


def validate_collateral_portfolio(portfolio: CollateralPortfolio) -> bool:
    """Validate complete collateral portfolio"""
    return (
        len(portfolio.positions) > 0 and
        all(validate_collateral_position(pos) for pos in portfolio.positions) and
        portfolio.total_value_usd >= 0 and
        portfolio.total_adjusted_value_usd >= 0 and
        0.0 <= portfolio.diversification_score <= 1.0 and
        0.0 <= portfolio.correlation_risk <= 1.0 and
        portfolio.portfolio_var_95 >= 0 and
        0.0 <= portfolio.max_portfolio_drawdown <= 1.0 and
        portfolio.liquidity_coverage_ratio >= 0
    )