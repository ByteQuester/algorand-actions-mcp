"""
Liquidation Scenarios Module

Advanced liquidation scenario modeling for digital asset collateral.
Analyzes speed vs slippage trade-offs and optimal liquidation strategies.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

# Import from common shared modules
from ...common.models.blockchain_collateral_models import (
    DigitalAsset, CollateralPosition, LiquidationScenario
)
from .config import LiquidationEngineConfig, load_config


class LiquidationTrigger(Enum):
    """Types of liquidation triggers"""
    LTV_BREACH = "ltv_breach"                    # LTV ratio exceeded
    MARGIN_CALL = "margin_call"                  # Margin call not met
    VOLATILITY_SPIKE = "volatility_spike"        # Sudden volatility increase
    ORACLE_FAILURE = "oracle_failure"            # Price oracle failed
    MANUAL_TRIGGER = "manual_trigger"            # Manual intervention


class LiquidationStrategy(Enum):
    """Liquidation execution strategies"""
    IMMEDIATE = "immediate"                      # Liquidate immediately
    GRADUAL = "gradual"                         # Gradual liquidation over time
    WATERFALL = "waterfall"                     # Liquidate by liquidity tier
    SELECTIVE = "selective"                     # Cherry-pick most liquid assets


@dataclass
class LiquidationParameters:
    """Parameters controlling liquidation execution"""
    max_slippage_tolerance: float               # Maximum acceptable slippage
    target_completion_time: float               # Target time to complete (hours)
    min_recovery_rate: float                    # Minimum recovery rate required
    gas_cost_consideration: bool                # Include gas costs in calculations
    market_impact_limit: float                 # Maximum market impact allowed


@dataclass
class LiquidationExecutionPlan:
    """Detailed execution plan for liquidation"""
    asset_symbol: str
    liquidation_amount: float                   # Amount to liquidate
    execution_tranches: List[Dict]              # How to split the liquidation
    estimated_duration: float                  # Total execution time (hours)
    expected_slippage: float                    # Expected price slippage
    recovery_estimate: float                    # Expected recovery amount
    gas_cost_estimate: float                   # Estimated gas costs
    market_impact_score: str                    # "low", "medium", "high"


def calculate_liquidation_slippage(
    position_size_usd: float,
    daily_volume_usd: float,
    market_depth_1pct: float,
    liquidation_speed_factor: float = 1.0,
    config: Optional[LiquidationEngineConfig] = None
) -> float:
    """
    Calculate expected slippage for liquidating a position

    Args:
        position_size_usd: Size of position to liquidate
        daily_volume_usd: Average daily trading volume
        market_depth_1pct: Market depth at 1% price impact
        liquidation_speed_factor: Speed multiplier (1.0 = normal, 2.0 = urgent)

    Returns:
        Expected slippage as decimal (0.05 = 5%)
    """

    if config is None:
        config = load_config()

    # Base slippage from position size vs daily volume
    volume_ratio = position_size_usd / daily_volume_usd if daily_volume_usd > 0 else 1.0

    # Slippage increases non-linearly with volume ratio
    base_slippage = min(
        config.slippage_calculation.max_slippage_cap,
        volume_ratio ** config.slippage_calculation.volume_ratio_power * config.slippage_calculation.base_slippage_factor
    )

    # Market depth consideration
    if position_size_usd > market_depth_1pct:
        depth_penalty = (position_size_usd - market_depth_1pct) / market_depth_1pct * config.slippage_calculation.depth_penalty_factor
        base_slippage += min(depth_penalty, config.slippage_calculation.max_depth_penalty)

    # Speed factor increases slippage
    speed_multiplier = liquidation_speed_factor ** config.slippage_calculation.speed_power_factor
    final_slippage = base_slippage * speed_multiplier

    return min(config.slippage_calculation.max_slippage_cap, final_slippage)


def estimate_liquidation_time(
    position_size_usd: float,
    daily_volume_usd: float,
    liquidity_tier: str,
    urgency_level: str = "normal",
    config: Optional[LiquidationEngineConfig] = None
) -> float:
    """
    Estimate time required to liquidate a position

    Returns:
        Estimated time in hours
    """

    if config is None:
        config = load_config()

    # Base time calculation from volume
    if daily_volume_usd <= 0:
        return config.liquidation_timing.base_liquidation_times['very_large']

    # Calculate what percentage of daily volume this represents
    volume_percentage = position_size_usd / daily_volume_usd

    # Base liquidation time (hours) based on configured thresholds
    if volume_percentage <= config.liquidation_timing.volume_thresholds['very_small']:
        base_time = config.liquidation_timing.base_liquidation_times['very_small']
    elif volume_percentage <= config.liquidation_timing.volume_thresholds['small']:
        base_time = config.liquidation_timing.base_liquidation_times['small']
    elif volume_percentage <= config.liquidation_timing.volume_thresholds['medium']:
        base_time = config.liquidation_timing.base_liquidation_times['medium']
    elif volume_percentage <= config.liquidation_timing.volume_thresholds['large']:
        base_time = config.liquidation_timing.base_liquidation_times['large']
    else:
        base_time = config.liquidation_timing.base_liquidation_times['very_large']

    # Liquidity tier adjustments
    liquidity_factor = getattr(config.liquidity_adjustments, liquidity_tier, 1.0)

    # Urgency adjustments
    urgency_factor = getattr(config.urgency_adjustments, urgency_level, 1.0)

    total_time = base_time * liquidity_factor * urgency_factor

    return max(
        config.liquidation_timing.time_constraints['min_hours'],
        min(config.liquidation_timing.time_constraints['max_hours'], total_time)
    )


def create_waterfall_liquidation_plan(
    positions: List[CollateralPosition],
    liquidation_target_usd: float,
    parameters: LiquidationParameters,
    config: Optional[LiquidationEngineConfig] = None
) -> List[LiquidationExecutionPlan]:
    """
    Create a waterfall liquidation plan prioritizing most liquid assets
    """

    # Sort positions by liquidity (high to low)
    sorted_positions = sorted(
        positions,
        key=lambda p: (
            p.asset.liquidity_metrics.liquidity_tier == "high",
            p.asset.liquidity_metrics.daily_volume_usd,
            -p.asset.volatility_metrics.volatility_30d  # Lower volatility better
        ),
        reverse=True
    )

    execution_plans = []
    remaining_target = liquidation_target_usd

    for position in sorted_positions:
        if remaining_target <= 0:
            break

        # Determine how much to liquidate from this position
        position_value = position.adjusted_value_usd
        liquidation_amount = min(remaining_target, position_value)

        # Calculate liquidation metrics
        slippage = calculate_liquidation_slippage(
            liquidation_amount,
            position.asset.liquidity_metrics.daily_volume_usd,
            position.asset.liquidity_metrics.depth_1_percent,
            config=config
        )

        # Check if slippage is acceptable
        if slippage > parameters.max_slippage_tolerance:
            # Reduce liquidation amount to meet slippage target
            if config is None:
                config = load_config()
            max_safe_amount = position.asset.liquidity_metrics.depth_1_percent * config.execution_parameters.depth_safety_factor
            liquidation_amount = min(liquidation_amount, max_safe_amount)
            slippage = calculate_liquidation_slippage(
                liquidation_amount,
                position.asset.liquidity_metrics.daily_volume_usd,
                position.asset.liquidity_metrics.depth_1_percent,
                config=config
            )

        execution_time = estimate_liquidation_time(
            liquidation_amount,
            position.asset.liquidity_metrics.daily_volume_usd,
            position.asset.liquidity_metrics.liquidity_tier,
            "urgent" if parameters.target_completion_time < 4 else "normal",
            config=config
        )

        # Calculate recovery after slippage
        recovery_amount = liquidation_amount * (1.0 - slippage)

        # Estimate market impact
        if config is None:
            config = load_config()
        volume_ratio = liquidation_amount / position.asset.liquidity_metrics.daily_volume_usd
        if volume_ratio < config.market_impact_thresholds.low:
            market_impact = "low"
        elif volume_ratio < config.market_impact_thresholds.medium:
            market_impact = "medium"
        else:
            market_impact = "high"

        # Create execution tranches if large liquidation
        tranches = []
        if liquidation_amount > position.asset.liquidity_metrics.depth_1_percent:
            # Split into multiple tranches
            tranche_size = position.asset.liquidity_metrics.depth_1_percent * config.execution_parameters.depth_safety_factor
            num_tranches = min(
                math.ceil(liquidation_amount / tranche_size),
                config.execution_parameters.max_tranches
            )

            for i in range(num_tranches):
                tranche_amount = min(tranche_size, liquidation_amount - i * tranche_size)
                tranches.append({
                    "tranche_number": i + 1,
                    "amount": tranche_amount,
                    "delay_hours": i * config.execution_parameters.tranche_delay_hours
                })
        else:
            tranches.append({
                "tranche_number": 1,
                "amount": liquidation_amount,
                "delay_hours": 0
            })

        plan = LiquidationExecutionPlan(
            asset_symbol=position.asset.symbol,
            liquidation_amount=liquidation_amount,
            execution_tranches=tranches,
            estimated_duration=execution_time,
            expected_slippage=slippage,
            recovery_estimate=recovery_amount,
            gas_cost_estimate=config.execution_parameters.default_gas_cost_usd,
            market_impact_score=market_impact
        )

        execution_plans.append(plan)
        remaining_target -= liquidation_amount

    return execution_plans


def simulate_liquidation_scenarios(
    positions: List[CollateralPosition],
    liquidation_target_usd: float,
    config: Optional[LiquidationEngineConfig] = None
) -> List[LiquidationScenario]:
    """
    Simulate different liquidation scenarios and their outcomes
    """

    if config is None:
        config = load_config()

    scenarios = []

    # Scenario 1: Immediate liquidation
    immediate_params = LiquidationParameters(
        max_slippage_tolerance=config.liquidation_strategies.immediate.max_slippage_tolerance,
        target_completion_time=config.liquidation_strategies.immediate.target_completion_time,
        min_recovery_rate=config.liquidation_strategies.immediate.min_recovery_rate,
        gas_cost_consideration=config.liquidation_strategies.immediate.gas_cost_consideration,
        market_impact_limit=config.liquidation_strategies.immediate.market_impact_limit
    )

    immediate_plan = create_waterfall_liquidation_plan(
        positions, liquidation_target_usd, immediate_params, config
    )

    total_recovery = sum(plan.recovery_estimate for plan in immediate_plan)
    avg_slippage = sum(plan.expected_slippage * plan.liquidation_amount
                     for plan in immediate_plan) / liquidation_target_usd
    max_time = max(plan.estimated_duration for plan in immediate_plan) if immediate_plan else 0

    scenarios.append(LiquidationScenario(
        scenario_name="Immediate Liquidation",
        trigger_condition="LTV breach - urgent liquidation needed",
        estimated_time_hours=max_time,
        expected_slippage=avg_slippage,
        recovery_percentage=total_recovery / liquidation_target_usd,
        market_impact="high"
    ))

    # Scenario 2: Gradual liquidation
    gradual_params = LiquidationParameters(
        max_slippage_tolerance=config.liquidation_strategies.gradual.max_slippage_tolerance,
        target_completion_time=config.liquidation_strategies.gradual.target_completion_time,
        min_recovery_rate=config.liquidation_strategies.gradual.min_recovery_rate,
        gas_cost_consideration=config.liquidation_strategies.gradual.gas_cost_consideration,
        market_impact_limit=config.liquidation_strategies.gradual.market_impact_limit
    )

    gradual_plan = create_waterfall_liquidation_plan(
        positions, liquidation_target_usd, gradual_params, config
    )

    total_recovery = sum(plan.recovery_estimate for plan in gradual_plan)
    avg_slippage = sum(plan.expected_slippage * plan.liquidation_amount
                     for plan in gradual_plan) / liquidation_target_usd if gradual_plan else 0

    scenarios.append(LiquidationScenario(
        scenario_name="Gradual Liquidation",
        trigger_condition="Margin call - controlled liquidation",
        estimated_time_hours=24.0,
        expected_slippage=avg_slippage,
        recovery_percentage=total_recovery / liquidation_target_usd if liquidation_target_usd > 0 else 0,
        market_impact="low"
    ))

    # Scenario 3: Selective liquidation (best assets only)
    high_liquidity_positions = [
        p for p in positions
        if p.asset.liquidity_metrics.liquidity_tier == "high"
    ]

    if high_liquidity_positions:
        selective_plan = create_waterfall_liquidation_plan(
            high_liquidity_positions, liquidation_target_usd, immediate_params, config
        )

        total_recovery = sum(plan.recovery_estimate for plan in selective_plan)
        avg_slippage = sum(plan.expected_slippage * plan.liquidation_amount
                         for plan in selective_plan) / liquidation_target_usd if selective_plan else 0

        scenarios.append(LiquidationScenario(
            scenario_name="Selective Liquidation",
            trigger_condition="Partial liquidation - high liquidity assets only",
            estimated_time_hours=2.0,
            expected_slippage=avg_slippage,
            recovery_percentage=total_recovery / liquidation_target_usd if liquidation_target_usd > 0 else 0,
            market_impact="medium"
        ))

    return scenarios


def assess_liquidation_feasibility(
    position: CollateralPosition,
    required_liquidation_usd: float,
    time_constraint_hours: float = 24.0,
    config: Optional[LiquidationEngineConfig] = None
) -> Dict[str, any]:
    """
    Assess whether a liquidation is feasible within given constraints
    """

    daily_volume = position.asset.liquidity_metrics.daily_volume_usd
    market_depth = position.asset.liquidity_metrics.depth_1_percent

    if config is None:
        config = load_config()

    # Calculate what percentage of daily volume this represents
    volume_impact = required_liquidation_usd / daily_volume if daily_volume > 0 else float('inf')

    # Estimate if liquidation is feasible based on configured thresholds
    feasibility_thresholds = config.feasibility_assessment.volume_impact_thresholds
    confidence_scores = config.feasibility_assessment.confidence_scores

    if volume_impact <= feasibility_thresholds['very_high']:
        feasibility = "very_high"
        confidence = confidence_scores['very_high']
    elif volume_impact <= feasibility_thresholds['high']:
        feasibility = "high"
        confidence = confidence_scores['high']
    elif volume_impact <= feasibility_thresholds['medium']:
        feasibility = "medium"
        confidence = confidence_scores['medium']
    elif volume_impact <= feasibility_thresholds['low']:
        feasibility = "low"
        confidence = confidence_scores['low']
    else:
        feasibility = "very_low"
        confidence = confidence_scores['very_low']

    # Time feasibility
    estimated_time = estimate_liquidation_time(
        required_liquidation_usd,
        daily_volume,
        position.asset.liquidity_metrics.liquidity_tier,
        config=config
    )

    time_feasible = estimated_time <= time_constraint_hours

    # Slippage estimate
    expected_slippage = calculate_liquidation_slippage(
        required_liquidation_usd,
        daily_volume,
        market_depth,
        config=config
    )

    return {
        "feasibility_level": feasibility,
        "confidence_score": confidence,
        "time_feasible": time_feasible,
        "estimated_time_hours": estimated_time,
        "expected_slippage": expected_slippage,
        "volume_impact_ratio": volume_impact,
        "recommended_strategy": "gradual" if volume_impact > config.market_impact_thresholds.medium else "immediate"
    }