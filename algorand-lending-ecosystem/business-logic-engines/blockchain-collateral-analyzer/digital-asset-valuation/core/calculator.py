"""
Digital Collateral Calculator (Configuration-driven Version)

Core functions for analyzing digital asset collateral requirements and risks,
now using configurable parameters instead of hardcoded constants.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math
from pathlib import Path
import sys

# Import from common shared modules
from ...common.models.blockchain_collateral_models import (
    DigitalAsset, CollateralPosition, CollateralPortfolio,
    LiquidationScenario, CollateralAnalysisResult,
    DigitalCollateralType, VolatilityMetrics, LiquidityMetrics
)
from .config import load_config, DigitalAssetValuationConfig
from .constants import ConfigurableDigitalAssetConstants


class ConfigurableDigitalCollateralCalculator:
    """
    Configuration-driven digital collateral calculator
    """

    def __init__(self, config_path: Path = None):
        """Initialize with configuration"""
        self.config = load_config(config_path)
        self.constants = ConfigurableDigitalAssetConstants(config_path)

    def calculate_asset_haircut(self, asset: DigitalAsset, market_conditions: str = "normal") -> float:
        """Calculate risk-adjusted haircut for a digital asset"""

        # Base haircut from asset type
        base_haircut = self.constants.default_haircuts.get(asset.asset_type, 0.10)

        # Volatility adjustment
        max_volatility_adj = self.config.volatility_parameters.max_volatility_adjustment
        volatility_multiplier = self.config.volatility_parameters.volatility_multiplier
        volatility_adjustment = min(asset.volatility_metrics.volatility_30d * volatility_multiplier, max_volatility_adj)

        # Liquidity adjustment
        liquidity_adjustments = {
            "high": self.config.liquidity_tier_adjustments.high,
            "medium": self.config.liquidity_tier_adjustments.medium,
            "low": self.config.liquidity_tier_adjustments.low
        }
        liquidity_adjustment = liquidity_adjustments.get(
            asset.liquidity_metrics.liquidity_tier,
            self.config.liquidity_tier_adjustments.low
        )

        # Market condition adjustment from config
        market_adjustment = getattr(self.config.market_condition_adjustments, market_conditions, 0.0)

        # Total haircut
        total_haircut = base_haircut + volatility_adjustment + liquidity_adjustment + market_adjustment

        # Cap between 1% and 50%
        return max(0.01, min(0.50, total_haircut))

    def assess_liquidation_urgency(
        self,
        position: CollateralPosition,
        current_ltv: float
    ) -> Tuple[str, float]:
        """Assess liquidation urgency for a collateral position"""

        maintenance_ratio = self.constants.maintenance_ratios.get(
            position.asset.asset_type, 1.5
        )

        # Calculate distance to liquidation
        liquidation_distance = current_ltv - (1.0 / maintenance_ratio)

        # Estimate time to liquidate based on asset liquidity
        daily_volume = position.asset.liquidity_metrics.daily_volume_usd
        position_size = position.value_usd

        if daily_volume > 0:
            volume_ratio = position_size / daily_volume
            base_liquidation_time = max(1, volume_ratio * self.config.liquidation_thresholds.max_liquidation_time)
        else:
            base_liquidation_time = self.config.liquidation_thresholds.max_liquidation_time

        # Adjust for market conditions and asset type
        if position.asset.liquidity_metrics.liquidity_tier == "high":
            time_multiplier = 0.5
        elif position.asset.liquidity_metrics.liquidity_tier == "medium":
            time_multiplier = 1.0
        else:
            time_multiplier = 2.0

        estimated_time = base_liquidation_time * time_multiplier

        # Determine urgency level using configured thresholds
        thresholds = self.constants.liquidation_thresholds
        if liquidation_distance <= -0.05:  # Already underwater
            urgency = "critical"
        elif liquidation_distance <= 0.0:  # At liquidation threshold
            urgency = "high"
        elif liquidation_distance <= thresholds["urgent_threshold"] - thresholds["auto_liquidation"]:
            urgency = "medium"
        else:
            urgency = "low"

        return urgency, estimated_time

    def calculate_portfolio_diversification(self, portfolio: CollateralPortfolio) -> float:
        """Calculate portfolio diversification score (0-1, higher is better)"""

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
        hhi = sum(p**2 for p in type_proportions)

        # Convert to diversification score (0-1, higher is better)
        # Perfect diversification across 5 types would have HHI = 0.2
        max_hhi = 1.0  # Single asset
        min_hhi = 0.2  # Equally distributed across 5 types

        diversification_score = (max_hhi - hhi) / (max_hhi - min_hhi)
        return max(0.0, min(1.0, diversification_score))

    def calculate_portfolio_var(
        self,
        portfolio: CollateralPortfolio,
        confidence_level: float = 0.95,
        time_horizon_days: int = 1
    ) -> float:
        """Calculate portfolio Value at Risk"""

        if not portfolio.positions:
            return 0.0

        portfolio_var = 0.0
        total_value = portfolio.total_value_usd

        for position in portfolio.positions:
            weight = position.value_usd / total_value if total_value > 0 else 0
            asset_var = position.asset.volatility_metrics.value_at_risk_95

            # Scale VaR by position weight
            weighted_var = (weight * asset_var) ** 2
            portfolio_var += weighted_var

        # Take square root for portfolio VaR (assuming independence - simplified)
        portfolio_var = math.sqrt(portfolio_var)

        # Adjust for time horizon (assuming normal distribution)
        if time_horizon_days != 1:
            portfolio_var *= math.sqrt(time_horizon_days)

        # Adjust for confidence level if not 95%
        if confidence_level != 0.95:
            # Simple adjustment - in practice, use inverse normal distribution
            confidence_adjustments = {0.90: 0.85, 0.95: 1.0, 0.99: 1.3}
            multiplier = confidence_adjustments.get(confidence_level, 1.0)
            portfolio_var *= multiplier

        return portfolio_var

    def analyze_digital_collateral_requirement(
        self,
        loan_amount_usd: float,
        collateral_positions: List[CollateralPosition],
        market_conditions: str = "normal",
        stress_test: bool = True
    ) -> CollateralAnalysisResult:
        """
        Comprehensive analysis of digital collateral requirements

        Args:
            loan_amount_usd: USD amount of the loan
            collateral_positions: List of collateral positions
            market_conditions: Current market conditions ("bull", "normal", "bear", "crisis")
            stress_test: Whether to perform stress testing

        Returns:
            CollateralAnalysisResult with complete analysis
        """

        # Create portfolio
        total_value = sum(pos.value_usd for pos in collateral_positions)
        total_adjusted_value = sum(pos.adjusted_value_usd for pos in collateral_positions)

        portfolio = CollateralPortfolio(
            positions=collateral_positions,
            total_value_usd=total_value,
            total_adjusted_value_usd=total_adjusted_value,
            diversification_score=0.0,  # Will calculate below
            correlation_risk=0.0,       # Simplified for now
            portfolio_var_95=0.0,       # Will calculate below
            max_portfolio_drawdown=0.0, # Simplified for now
            liquidity_coverage_ratio=1.0 # Simplified for now
        )

        # Calculate portfolio metrics
        portfolio.diversification_score = self.calculate_portfolio_diversification(portfolio)
        portfolio.portfolio_var_95 = self.calculate_portfolio_var(portfolio)

        # Determine required collateral ratio using configuration
        diversification_bonus = self.config.analysis.diversification_bonus_factor
        if portfolio.diversification_score >= 0.7:
            ratio_adjustment = -diversification_bonus * 2  # 10% reduction for good diversification
        elif portfolio.diversification_score >= 0.4:
            ratio_adjustment = 0.0   # No adjustment
        else:
            ratio_adjustment = diversification_bonus * 4   # 20% increase for poor diversification

        # Use base ratio from configuration
        base_ratio = self.constants.default_collateral_ratios.get(
            DigitalCollateralType.ALGO_NATIVE, 1.5
        )  # Default to ALGO native ratio
        required_ratio = base_ratio + ratio_adjustment

        # Market condition adjustment from configuration
        market_conditions_key = f"{market_conditions}_market" if market_conditions in ["bull", "bear"] else market_conditions
        market_multiplier = self.constants.market_condition_multipliers.get(market_conditions_key, {})
        market_adjustment = market_multiplier.get("collateral_ratio_adjustment", 0.0)
        required_ratio += market_adjustment

        # Apply safety buffer from configuration
        required_ratio += self.config.analysis.safety_buffer

        # Calculate sufficiency
        required_collateral_value = loan_amount_usd * required_ratio
        is_sufficient = total_adjusted_value >= required_collateral_value
        surplus_deficit = total_adjusted_value - required_collateral_value

        # Assess overall risk level
        ltv_ratio = loan_amount_usd / total_adjusted_value if total_adjusted_value > 0 else float('inf')

        if ltv_ratio <= 0.5:
            risk_level = "low"
        elif ltv_ratio <= 0.7:
            risk_level = "medium"
        elif ltv_ratio <= 0.85:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Generate liquidation scenarios
        liquidation_scenarios = []
        for position in collateral_positions:
            urgency, time_hours = self.assess_liquidation_urgency(position, ltv_ratio)

            maintenance_ratio = self.constants.maintenance_ratios.get(position.asset.asset_type, 1.5)
            scenario = LiquidationScenario(
                scenario_name=f"Liquidate {position.asset.symbol}",
                trigger_condition=f"LTV exceeds {maintenance_ratio:.0%}",
                estimated_time_hours=time_hours,
                expected_slippage=0.02,  # 2% default slippage
                recovery_percentage=0.95,  # 95% recovery
                market_impact="low" if position.asset.liquidity_metrics.liquidity_tier == "high" else "medium"
            )
            liquidation_scenarios.append(scenario)

        # Generate recommendations
        recommendations = []
        monitoring_alerts = []

        if not is_sufficient:
            deficit_pct = abs(surplus_deficit) / required_collateral_value * 100
            recommendations.append(f"Add ${abs(surplus_deficit):,.0f} more collateral ({deficit_pct:.1f}% deficit)")

        diversification_targets = self.constants.diversification_targets
        if portfolio.diversification_score < diversification_targets["single_asset_max"]:
            recommendations.append("Improve portfolio diversification across asset types")

        if risk_level in ["high", "critical"]:
            monitoring_alerts.append("Monitor LTV ratio closely - approaching liquidation threshold")

        if any(pos.asset.liquidity_metrics.liquidity_tier == "low" for pos in collateral_positions):
            monitoring_alerts.append("Portfolio contains low-liquidity assets - monitor market conditions")

        # Calculate confidence score using configuration
        confidence_factors = [
            portfolio.diversification_score,
            1.0 - portfolio.portfolio_var_95,  # Lower VaR = higher confidence
            min(1.0, total_value / 1000000),   # Larger portfolios more stable
        ]
        confidence_score = (sum(confidence_factors) / len(confidence_factors)) * self.config.analysis.data_quality_score

        return CollateralAnalysisResult(
            loan_amount_usd=loan_amount_usd,
            required_collateral_ratio=required_ratio,
            collateral_portfolio=portfolio,
            risk_level=risk_level,
            confidence_score=confidence_score,
            is_sufficient=is_sufficient,
            surplus_deficit_usd=surplus_deficit,
            liquidation_scenarios=liquidation_scenarios,
            average_liquidation_time=sum(s.estimated_time_hours for s in liquidation_scenarios) / len(liquidation_scenarios) if liquidation_scenarios else 0,
            recommended_actions=recommendations,
            monitoring_alerts=monitoring_alerts,
            analysis_timestamp=datetime.now(),
            oracle_prices_timestamp=datetime.now(),
            market_conditions=market_conditions
        )

    def calculate_collateral_ratio(
        self,
        loan_amount_usd: float,
        collateral_value_usd: float
    ) -> float:
        """Calculate current collateralization ratio"""
        if loan_amount_usd <= 0:
            return float('inf')
        return collateral_value_usd / loan_amount_usd

    def assess_liquidation_risk(
        self,
        current_ratio: float,
        asset_type: DigitalCollateralType,
        volatility_30d: float
    ) -> Tuple[str, str]:
        """Assess liquidation risk based on current ratio and asset characteristics"""

        maintenance_ratio = self.constants.maintenance_ratios.get(asset_type, 1.5)
        buffer = current_ratio - maintenance_ratio

        # Adjust for volatility
        volatility_factor = min(volatility_30d * 2, 1.0)  # High volatility increases risk

        if buffer <= 0:
            risk_level = "critical"
            explanation = "Below maintenance ratio - liquidation imminent"
        elif buffer <= 0.1 + volatility_factor:
            risk_level = "high"
            explanation = f"Close to liquidation threshold with {volatility_30d:.0%} volatility"
        elif buffer <= 0.3 + volatility_factor:
            risk_level = "medium"
            explanation = "Moderate risk - monitor closely"
        else:
            risk_level = "low"
            explanation = "Safe collateralization level"

        return risk_level, explanation


# Create a global instance for backward compatibility
_default_calculator = None

def get_default_calculator() -> ConfigurableDigitalCollateralCalculator:
    """Get the default calculator instance"""
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = ConfigurableDigitalCollateralCalculator()
    return _default_calculator

# Expose functions for backward compatibility
def calculate_asset_haircut(asset: DigitalAsset, market_conditions: str = "normal") -> float:
    return get_default_calculator().calculate_asset_haircut(asset, market_conditions)

def assess_liquidation_urgency(position: CollateralPosition, current_ltv: float) -> Tuple[str, float]:
    return get_default_calculator().assess_liquidation_urgency(position, current_ltv)

def calculate_portfolio_diversification(portfolio: CollateralPortfolio) -> float:
    return get_default_calculator().calculate_portfolio_diversification(portfolio)

def calculate_portfolio_var(
    portfolio: CollateralPortfolio,
    confidence_level: float = 0.95,
    time_horizon_days: int = 1
) -> float:
    return get_default_calculator().calculate_portfolio_var(portfolio, confidence_level, time_horizon_days)

def analyze_digital_collateral_requirement(
    loan_amount_usd: float,
    collateral_positions: List[CollateralPosition],
    market_conditions: str = "normal",
    stress_test: bool = True
) -> CollateralAnalysisResult:
    return get_default_calculator().analyze_digital_collateral_requirement(
        loan_amount_usd, collateral_positions, market_conditions, stress_test
    )

def calculate_collateral_ratio(loan_amount_usd: float, collateral_value_usd: float) -> float:
    return get_default_calculator().calculate_collateral_ratio(loan_amount_usd, collateral_value_usd)

def assess_liquidation_risk(
    current_ratio: float,
    asset_type: DigitalCollateralType,
    volatility_30d: float
) -> Tuple[str, str]:
    return get_default_calculator().assess_liquidation_risk(current_ratio, asset_type, volatility_30d)