"""
Main Liquidation Scenarios Engine with Configuration Support

This module provides the main interface for the liquidation scenarios engine,
integrating with MCP services and using configuration-driven parameters.
"""

from typing import List, Dict, Optional, Any
import asyncio
import logging
from pathlib import Path

from .config import LiquidationEngineConfig, load_config
from .liquidation_engine import (
    LiquidationTrigger,
    LiquidationStrategy,
    LiquidationParameters,
    LiquidationExecutionPlan,
    calculate_liquidation_slippage,
    estimate_liquidation_time,
    create_waterfall_liquidation_plan,
    simulate_liquidation_scenarios,
    assess_liquidation_feasibility
)
# Import from common shared modules
from ...common.models.blockchain_collateral_models import CollateralPosition, LiquidationScenario


class LiquidationScenariosEngine:
    """
    Main engine for liquidation scenario analysis and execution planning.
    """

    def __init__(self, config: Optional[LiquidationEngineConfig] = None):
        """
        Initialize the liquidation scenarios engine.

        Args:
            config: Optional configuration. If None, loads from default location.
        """
        self.config = config or load_config()
        self.logger = logging.getLogger(__name__)

        # Initialize connections to MCP services
        self.algorand_reader_url = self.config.mcp_services.algorand_reader_url
        self.market_data_url = self.config.mcp_services.market_data_url

    def calculate_slippage(
        self,
        position_size_usd: float,
        daily_volume_usd: float,
        market_depth_1pct: float,
        liquidation_speed_factor: float = 1.0
    ) -> float:
        """
        Calculate expected slippage for liquidating a position.

        Args:
            position_size_usd: Size of position to liquidate
            daily_volume_usd: Average daily trading volume
            market_depth_1pct: Market depth at 1% price impact
            liquidation_speed_factor: Speed multiplier (1.0 = normal, 2.0 = urgent)

        Returns:
            Expected slippage as decimal (0.05 = 5%)
        """
        return calculate_liquidation_slippage(
            position_size_usd,
            daily_volume_usd,
            market_depth_1pct,
            liquidation_speed_factor,
            self.config
        )

    def estimate_execution_time(
        self,
        position_size_usd: float,
        daily_volume_usd: float,
        liquidity_tier: str,
        urgency_level: str = "normal"
    ) -> float:
        """
        Estimate time required to liquidate a position.

        Args:
            position_size_usd: Size of position to liquidate
            daily_volume_usd: Average daily trading volume
            liquidity_tier: Asset liquidity tier ("high", "medium", "low")
            urgency_level: Urgency of liquidation

        Returns:
            Estimated time in hours
        """
        return estimate_liquidation_time(
            position_size_usd,
            daily_volume_usd,
            liquidity_tier,
            urgency_level,
            self.config
        )

    def create_liquidation_plan(
        self,
        positions: List[CollateralPosition],
        liquidation_target_usd: float,
        strategy: str = "waterfall"
    ) -> List[LiquidationExecutionPlan]:
        """
        Create a detailed liquidation execution plan.

        Args:
            positions: List of collateral positions to potentially liquidate
            liquidation_target_usd: Target USD amount to liquidate
            strategy: Liquidation strategy to use

        Returns:
            List of execution plans for each asset
        """
        # Get strategy parameters from config
        if strategy == "immediate":
            strategy_config = self.config.liquidation_strategies.immediate
        elif strategy == "gradual":
            strategy_config = self.config.liquidation_strategies.gradual
        elif strategy == "selective":
            strategy_config = self.config.liquidation_strategies.selective
        else:
            # Default to gradual for waterfall
            strategy_config = self.config.liquidation_strategies.gradual

        parameters = LiquidationParameters(
            max_slippage_tolerance=strategy_config.max_slippage_tolerance,
            target_completion_time=strategy_config.target_completion_time,
            min_recovery_rate=strategy_config.min_recovery_rate,
            gas_cost_consideration=strategy_config.gas_cost_consideration,
            market_impact_limit=strategy_config.market_impact_limit
        )

        return create_waterfall_liquidation_plan(
            positions,
            liquidation_target_usd,
            parameters,
            self.config
        )

    def simulate_scenarios(
        self,
        positions: List[CollateralPosition],
        liquidation_target_usd: float
    ) -> List[LiquidationScenario]:
        """
        Simulate different liquidation scenarios and their outcomes.

        Args:
            positions: List of collateral positions
            liquidation_target_usd: Target USD amount to liquidate

        Returns:
            List of liquidation scenarios with analysis
        """
        return simulate_liquidation_scenarios(
            positions,
            liquidation_target_usd,
            self.config
        )

    def assess_feasibility(
        self,
        position: CollateralPosition,
        required_liquidation_usd: float,
        time_constraint_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assess whether a liquidation is feasible within given constraints.

        Args:
            position: Collateral position to assess
            required_liquidation_usd: Required liquidation amount
            time_constraint_hours: Time constraint in hours

        Returns:
            Dictionary with feasibility analysis
        """
        if time_constraint_hours is None:
            time_constraint_hours = self.config.liquidation_strategies.gradual.target_completion_time

        return assess_liquidation_feasibility(
            position,
            required_liquidation_usd,
            time_constraint_hours,
            self.config
        )

    def get_emergency_parameters(self, scenario_type: str) -> Dict[str, Any]:
        """
        Get emergency liquidation parameters for specific scenarios.

        Args:
            scenario_type: Type of emergency scenario

        Returns:
            Emergency parameters dictionary
        """
        emergency_scenarios = {
            'oracle_failure': self.config.emergency_scenarios.oracle_failure,
            'volatility_spike': self.config.emergency_scenarios.volatility_spike,
            'black_swan': self.config.emergency_scenarios.black_swan
        }

        scenario = emergency_scenarios.get(scenario_type)
        if not scenario:
            raise ValueError(f"Unknown emergency scenario type: {scenario_type}")

        return {
            'fallback_discount': scenario.fallback_discount,
            'max_liquidation_delay': scenario.max_liquidation_delay,
            'confidence_penalty': scenario.confidence_penalty,
            'volatility_threshold': getattr(scenario, 'volatility_threshold', None),
            'slippage_multiplier': getattr(scenario, 'slippage_multiplier', None),
            'urgency_override': getattr(scenario, 'urgency_override', None),
            'market_crash_threshold': getattr(scenario, 'market_crash_threshold', None),
            'emergency_slippage_tolerance': getattr(scenario, 'emergency_slippage_tolerance', None),
            'override_recovery_requirements': getattr(scenario, 'override_recovery_requirements', None),
            'priority_liquidation_only': getattr(scenario, 'priority_liquidation_only', None)
        }

    def calculate_flash_loan_parameters(
        self,
        liquidation_amount: float,
        protocol: str = "aave"
    ) -> Dict[str, Any]:
        """
        Calculate flash loan parameters for liquidation.

        Args:
            liquidation_amount: Amount to liquidate
            protocol: Flash loan protocol to use

        Returns:
            Flash loan parameters
        """
        if not self.config.flash_loan_integration.enabled:
            raise ValueError("Flash loan integration is disabled")

        if protocol not in self.config.flash_loan_integration.supported_protocols:
            raise ValueError(f"Unsupported flash loan protocol: {protocol}")

        max_amount = self.config.flash_loan_integration.max_flash_loan_amount
        if liquidation_amount > max_amount:
            raise ValueError(f"Liquidation amount {liquidation_amount} exceeds max flash loan {max_amount}")

        fee_amount = liquidation_amount * self.config.flash_loan_integration.flash_loan_fee_rate
        gas_multiplier = self.config.flash_loan_integration.flash_loan_gas_multiplier
        estimated_gas = self.config.execution_parameters.default_gas_cost_usd * gas_multiplier

        return {
            'protocol': protocol,
            'loan_amount': liquidation_amount,
            'fee_amount': fee_amount,
            'estimated_gas_cost': estimated_gas,
            'total_cost': fee_amount + estimated_gas
        }

    def get_auction_parameters(self, auction_type: str = "dutch") -> Dict[str, Any]:
        """
        Get auction parameters for liquidation.

        Args:
            auction_type: Type of auction ("dutch" or "sealed_bid")

        Returns:
            Auction parameters
        """
        if auction_type == "dutch":
            auction = self.config.auction_parameters.dutch_auction
            if not auction.enabled:
                raise ValueError("Dutch auction is disabled")

            return {
                'type': 'dutch',
                'enabled': auction.enabled,
                'starting_discount': auction.starting_discount,
                'discount_increment': auction.discount_increment,
                'time_interval_minutes': auction.time_interval_minutes,
                'max_discount': auction.max_discount
            }

        elif auction_type == "sealed_bid":
            auction = self.config.auction_parameters.sealed_bid_auction
            if not auction.enabled:
                raise ValueError("Sealed bid auction is disabled")

            return {
                'type': 'sealed_bid',
                'enabled': auction.enabled,
                'minimum_bid_increment': auction.minimum_bid_increment,
                'auction_duration_hours': auction.auction_duration_hours,
                'reserve_price_discount': auction.reserve_price_discount
            }

        else:
            raise ValueError(f"Unknown auction type: {auction_type}")

    def calculate_recovery_rate(
        self,
        asset_type: str,
        market_condition: str = "normal_market"
    ) -> float:
        """
        Calculate expected recovery rate for an asset.

        Args:
            asset_type: Type of asset ("highly_liquid", "liquid", "illiquid")
            market_condition: Current market condition

        Returns:
            Expected recovery rate (0.0 to 1.0)
        """
        asset_adjustment = self.config.recovery_rates.asset_type_adjustments.get(asset_type, 0.85)
        market_adjustment = self.config.recovery_rates.market_condition_adjustments.get(market_condition, 1.0)

        return min(1.0, asset_adjustment * market_adjustment)

    def get_penalty_structure(self) -> Dict[str, float]:
        """
        Get the current penalty and fee structure.

        Returns:
            Dictionary of penalty rates
        """
        return {
            'borrower_penalty_rate': self.config.liquidation_penalties.borrower_penalty_rate,
            'liquidator_bonus_rate': self.config.liquidation_penalties.liquidator_bonus_rate,
            'protocol_fee_rate': self.config.liquidation_penalties.protocol_fee_rate,
            'insurance_fund_rate': self.config.liquidation_penalties.insurance_fund_rate
        }

    def check_risk_thresholds(
        self,
        position_concentration: float,
        portfolio_correlation: float,
        volatility_multiplier: float,
        liquidity_ratio: float
    ) -> Dict[str, bool]:
        """
        Check if various risk metrics exceed configured thresholds.

        Args:
            position_concentration: Concentration ratio of largest position
            portfolio_correlation: Correlation between portfolio assets
            volatility_multiplier: Current volatility vs normal
            liquidity_ratio: Current liquidity vs normal

        Returns:
            Dictionary of threshold breach flags
        """
        risk_config = self.config.risk_monitoring

        return {
            'concentration_breach': position_concentration > risk_config.position_concentration_limit,
            'correlation_breach': portfolio_correlation > risk_config.portfolio_correlation_limit,
            'volatility_spike': volatility_multiplier > risk_config.volatility_spike_threshold,
            'liquidity_drop': liquidity_ratio < risk_config.liquidity_drop_threshold
        }

    def reload_config(self, config_path: Optional[Path] = None):
        """
        Reload configuration from file.

        Args:
            config_path: Optional path to config file
        """
        self.config = load_config(config_path)
        self.algorand_reader_url = self.config.mcp_services.algorand_reader_url
        self.market_data_url = self.config.mcp_services.market_data_url
        self.logger.info("Configuration reloaded successfully")


# Convenience functions for backward compatibility
def create_liquidation_engine(config_path: Optional[Path] = None) -> LiquidationScenariosEngine:
    """
    Create a liquidation scenarios engine instance.

    Args:
        config_path: Optional path to configuration file

    Returns:
        LiquidationScenariosEngine instance
    """
    config = load_config(config_path) if config_path else None
    return LiquidationScenariosEngine(config)