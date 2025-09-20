"""
Slippage Calculator - Advanced price impact and slippage modeling for large orders

This module provides sophisticated slippage calculation models to assess the price impact
of large liquidation events across multiple DEXs and market conditions.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlippageModel(Enum):
    """Different slippage calculation models"""
    LINEAR = "linear"
    SQUARE_ROOT = "square_root"
    EXPONENTIAL = "exponential"
    IMPACT_FUNCTION = "impact_function"
    ADAPTIVE = "adaptive"

class OrderType(Enum):
    """Order types for slippage calculation"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    LIQUIDATION = "liquidation"

@dataclass
class OrderSize:
    """Order size categorization"""
    amount_usd: float
    category: str  # small, medium, large, whale
    relative_size: float  # Relative to daily volume

@dataclass
class MarketConditions:
    """Current market conditions affecting slippage"""
    volatility: float
    volume_24h: float
    spread_bps: float
    depth_score: float
    time_of_day: str  # session timing
    market_stress: float  # 0-1 stress indicator

@dataclass
class SlippageResult:
    """Result of slippage calculation"""
    order_amount_usd: float
    side: str
    expected_price: float
    executed_price: float
    slippage_bps: float
    slippage_pct: float
    price_impact_pct: float
    temporary_impact: float
    permanent_impact: float
    model_used: SlippageModel
    confidence_interval: Tuple[float, float]
    market_conditions: MarketConditions

@dataclass
class SlippageProfile:
    """Slippage profile for an asset pair"""
    asset_pair: str
    base_spread_bps: float
    avg_daily_volume: float
    liquidity_depth: Dict[str, float]  # Depth at various price levels
    volatility_profile: Dict[str, float]  # Historical volatility patterns
    model_parameters: Dict[str, float]  # Model-specific parameters

class SlippageCalculator:
    """
    Advanced slippage calculator that models price impact across multiple DEXs
    and market conditions for the Algorand ecosystem.
    """

    def __init__(self, config_path: str = None):
        """Initialize the slippage calculator"""
        self.config = self._load_config(config_path)
        self.slippage_config = self.config['slippage']
        self.models = self.slippage_config['models']

        # Initialize slippage profiles for major pairs
        self.asset_profiles: Dict[str, SlippageProfile] = {}
        self.market_data: Dict[str, Any] = {}
        self.calculation_history: List[SlippageResult] = []

        # Model parameters
        self.model_weights = {
            SlippageModel.LINEAR: 0.2,
            SlippageModel.SQUARE_ROOT: 0.3,
            SlippageModel.EXPONENTIAL: 0.2,
            SlippageModel.IMPACT_FUNCTION: 0.3
        }

        self._initialize_asset_profiles()

        logger.info("Slippage Calculator initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_asset_profiles(self):
        """Initialize slippage profiles for major asset pairs"""
        # Major Algorand trading pairs
        pairs = {
            'ALGO/USDC': {
                'base_spread_bps': 5,
                'avg_daily_volume': 2_000_000,
                'depth_score': 0.8,
                'volatility': 0.25
            },
            'ALGO/USDT': {
                'base_spread_bps': 8,
                'avg_daily_volume': 1_000_000,
                'depth_score': 0.6,
                'volatility': 0.27
            },
            'GARD/ALGO': {
                'base_spread_bps': 15,
                'avg_daily_volume': 500_000,
                'depth_score': 0.5,
                'volatility': 0.35
            },
            'BANK/ALGO': {
                'base_spread_bps': 25,
                'avg_daily_volume': 200_000,
                'depth_score': 0.4,
                'volatility': 0.45
            },
            'OPUL/ALGO': {
                'base_spread_bps': 30,
                'avg_daily_volume': 150_000,
                'depth_score': 0.3,
                'volatility': 0.5
            }
        }

        for pair, data in pairs.items():
            self.asset_profiles[pair] = SlippageProfile(
                asset_pair=pair,
                base_spread_bps=data['base_spread_bps'],
                avg_daily_volume=data['avg_daily_volume'],
                liquidity_depth=self._generate_depth_profile(data['depth_score']),
                volatility_profile=self._generate_volatility_profile(data['volatility']),
                model_parameters=self._generate_model_parameters(pair, data)
            )

    def _generate_depth_profile(self, depth_score: float) -> Dict[str, float]:
        """Generate liquidity depth profile"""
        base_depth = depth_score * 1_000_000  # Base depth in USD

        return {
            '0.1%': base_depth * 0.8,
            '0.25%': base_depth * 0.9,
            '0.5%': base_depth * 1.0,
            '1.0%': base_depth * 1.2,
            '2.5%': base_depth * 1.5,
            '5.0%': base_depth * 2.0,
            '10.0%': base_depth * 3.0
        }

    def _generate_volatility_profile(self, base_volatility: float) -> Dict[str, float]:
        """Generate volatility profile across timeframes"""
        return {
            '1m': base_volatility * 2.0,
            '5m': base_volatility * 1.5,
            '15m': base_volatility * 1.2,
            '1h': base_volatility * 1.0,
            '4h': base_volatility * 0.9,
            '24h': base_volatility * 0.8
        }

    def _generate_model_parameters(self, pair: str, data: Dict[str, Any]) -> Dict[str, float]:
        """Generate model-specific parameters for asset pair"""
        return {
            # Linear model parameters
            'linear_slope': data['volatility'] * 0.001,

            # Square root model parameters
            'sqrt_coefficient': data['volatility'] * 0.05,

            # Exponential model parameters
            'exp_decay_factor': 0.1 / data['depth_score'],

            # Impact function parameters
            'impact_exponent': 0.5 + (1 - data['depth_score']) * 0.3,
            'impact_coefficient': data['base_spread_bps'] / 10000
        }

    async def calculate_slippage(
        self,
        asset_pair: str,
        order_amount_usd: float,
        side: str = "sell",
        order_type: OrderType = OrderType.MARKET,
        market_conditions: MarketConditions = None,
        model: SlippageModel = SlippageModel.ADAPTIVE
    ) -> SlippageResult:
        """
        Calculate slippage for a given order

        Args:
            asset_pair: Trading pair (e.g., 'ALGO/USDC')
            order_amount_usd: Order size in USD
            side: 'buy' or 'sell'
            order_type: Type of order
            market_conditions: Current market conditions
            model: Slippage calculation model to use

        Returns:
            Detailed slippage analysis result
        """
        logger.info(f"Calculating slippage for {order_amount_usd:,.0f} USD {side} of {asset_pair}")

        if asset_pair not in self.asset_profiles:
            raise ValueError(f"No profile available for {asset_pair}")

        profile = self.asset_profiles[asset_pair]

        if market_conditions is None:
            market_conditions = self._get_current_market_conditions(asset_pair)

        # Get order size categorization
        order_size = self._categorize_order_size(order_amount_usd, profile.avg_daily_volume)

        # Calculate slippage using specified model
        if model == SlippageModel.ADAPTIVE:
            slippage_result = await self._calculate_adaptive_slippage(
                profile, order_amount_usd, side, order_type, market_conditions, order_size
            )
        else:
            slippage_result = await self._calculate_model_slippage(
                profile, order_amount_usd, side, order_type, market_conditions, order_size, model
            )

        # Add confidence interval
        slippage_result.confidence_interval = self._calculate_confidence_interval(
            slippage_result, profile, market_conditions
        )

        self.calculation_history.append(slippage_result)

        return slippage_result

    def _categorize_order_size(self, amount_usd: float, daily_volume: float) -> OrderSize:
        """Categorize order size relative to market"""
        relative_size = amount_usd / daily_volume

        if relative_size < 0.001:  # < 0.1% of daily volume
            category = "small"
        elif relative_size < 0.01:  # < 1% of daily volume
            category = "medium"
        elif relative_size < 0.1:   # < 10% of daily volume
            category = "large"
        else:
            category = "whale"

        return OrderSize(
            amount_usd=amount_usd,
            category=category,
            relative_size=relative_size
        )

    def _get_current_market_conditions(self, asset_pair: str) -> MarketConditions:
        """Get current market conditions for asset pair"""
        profile = self.asset_profiles[asset_pair]

        # Simulate current market conditions
        # In production, this would fetch real-time data
        current_hour = datetime.now().hour

        return MarketConditions(
            volatility=profile.volatility_profile['1h'],
            volume_24h=profile.avg_daily_volume,
            spread_bps=profile.base_spread_bps,
            depth_score=profile.liquidity_depth['1.0%'] / 1_000_000,
            time_of_day=self._get_trading_session(current_hour),
            market_stress=0.2  # Default moderate stress
        )

    def _get_trading_session(self, hour: int) -> str:
        """Determine trading session based on hour"""
        if 6 <= hour < 12:
            return "asia"
        elif 12 <= hour < 18:
            return "europe"
        elif 18 <= hour < 24:
            return "america"
        else:
            return "overnight"

    async def _calculate_adaptive_slippage(
        self,
        profile: SlippageProfile,
        order_amount_usd: float,
        side: str,
        order_type: OrderType,
        market_conditions: MarketConditions,
        order_size: OrderSize
    ) -> SlippageResult:
        """Calculate slippage using adaptive model combining multiple approaches"""

        # Calculate slippage using each model
        model_results = {}

        for model in [SlippageModel.LINEAR, SlippageModel.SQUARE_ROOT,
                     SlippageModel.EXPONENTIAL, SlippageModel.IMPACT_FUNCTION]:
            result = await self._calculate_model_slippage(
                profile, order_amount_usd, side, order_type, market_conditions, order_size, model
            )
            model_results[model] = result

        # Weight models based on market conditions and order characteristics
        adaptive_weights = self._calculate_adaptive_weights(
            order_size, market_conditions, profile
        )

        # Combine results using adaptive weights
        weighted_slippage = sum(
            result.slippage_pct * adaptive_weights[model]
            for model, result in model_results.items()
        )

        weighted_price_impact = sum(
            result.price_impact_pct * adaptive_weights[model]
            for model, result in model_results.items()
        )

        # Calculate expected and executed prices
        mid_price = 0.5  # Simplified - would get from market data

        if side == "sell":
            executed_price = mid_price * (1 - weighted_slippage)
        else:
            executed_price = mid_price * (1 + weighted_slippage)

        # Decompose into temporary and permanent impact
        temporary_impact = weighted_price_impact * 0.7  # 70% temporary
        permanent_impact = weighted_price_impact * 0.3   # 30% permanent

        return SlippageResult(
            order_amount_usd=order_amount_usd,
            side=side,
            expected_price=mid_price,
            executed_price=executed_price,
            slippage_bps=weighted_slippage * 10000,
            slippage_pct=weighted_slippage,
            price_impact_pct=weighted_price_impact,
            temporary_impact=temporary_impact,
            permanent_impact=permanent_impact,
            model_used=SlippageModel.ADAPTIVE,
            confidence_interval=(0.0, 0.0),  # Will be calculated later
            market_conditions=market_conditions
        )

    def _calculate_adaptive_weights(
        self,
        order_size: OrderSize,
        market_conditions: MarketConditions,
        profile: SlippageProfile
    ) -> Dict[SlippageModel, float]:
        """Calculate adaptive weights for different models"""

        # Base weights
        weights = self.model_weights.copy()

        # Adjust weights based on order size
        if order_size.category == "small":
            weights[SlippageModel.LINEAR] *= 1.5  # Linear works better for small orders
            weights[SlippageModel.EXPONENTIAL] *= 0.5
        elif order_size.category == "whale":
            weights[SlippageModel.EXPONENTIAL] *= 1.8  # Exponential better for large orders
            weights[SlippageModel.LINEAR] *= 0.3

        # Adjust weights based on market conditions
        if market_conditions.volatility > 0.4:  # High volatility
            weights[SlippageModel.IMPACT_FUNCTION] *= 1.5
            weights[SlippageModel.LINEAR] *= 0.5

        if market_conditions.market_stress > 0.7:  # High stress
            weights[SlippageModel.EXPONENTIAL] *= 1.3
            weights[SlippageModel.SQUARE_ROOT] *= 0.7

        # Normalize weights
        total_weight = sum(weights.values())
        return {model: weight / total_weight for model, weight in weights.items()}

    async def _calculate_model_slippage(
        self,
        profile: SlippageProfile,
        order_amount_usd: float,
        side: str,
        order_type: OrderType,
        market_conditions: MarketConditions,
        order_size: OrderSize,
        model: SlippageModel
    ) -> SlippageResult:
        """Calculate slippage using a specific model"""

        params = profile.model_parameters

        # Base slippage calculation
        if model == SlippageModel.LINEAR:
            base_slippage = self._linear_slippage_model(order_amount_usd, params)
        elif model == SlippageModel.SQUARE_ROOT:
            base_slippage = self._sqrt_slippage_model(order_amount_usd, params)
        elif model == SlippageModel.EXPONENTIAL:
            base_slippage = self._exponential_slippage_model(order_amount_usd, params)
        elif model == SlippageModel.IMPACT_FUNCTION:
            base_slippage = self._impact_function_model(order_amount_usd, params, profile)
        else:
            raise ValueError(f"Unknown slippage model: {model}")

        # Apply market condition adjustments
        adjusted_slippage = self._apply_market_adjustments(
            base_slippage, market_conditions, order_type, profile
        )

        # Calculate price impact (usually slightly higher than slippage)
        price_impact = adjusted_slippage * 1.2

        # Calculate execution price
        mid_price = 0.5  # Simplified

        if side == "sell":
            executed_price = mid_price * (1 - adjusted_slippage)
        else:
            executed_price = mid_price * (1 + adjusted_slippage)

        # Temporary vs permanent impact
        temporary_impact = price_impact * 0.75
        permanent_impact = price_impact * 0.25

        return SlippageResult(
            order_amount_usd=order_amount_usd,
            side=side,
            expected_price=mid_price,
            executed_price=executed_price,
            slippage_bps=adjusted_slippage * 10000,
            slippage_pct=adjusted_slippage,
            price_impact_pct=price_impact,
            temporary_impact=temporary_impact,
            permanent_impact=permanent_impact,
            model_used=model,
            confidence_interval=(0.0, 0.0),
            market_conditions=market_conditions
        )

    def _linear_slippage_model(self, order_amount_usd: float, params: Dict[str, float]) -> float:
        """Linear slippage model: slippage = slope * amount"""
        slope = params['linear_slope']
        return slope * order_amount_usd

    def _sqrt_slippage_model(self, order_amount_usd: float, params: Dict[str, float]) -> float:
        """Square root slippage model: slippage = coefficient * sqrt(amount)"""
        coefficient = params['sqrt_coefficient']
        return coefficient * np.sqrt(order_amount_usd / 1_000_000)  # Normalize to millions

    def _exponential_slippage_model(self, order_amount_usd: float, params: Dict[str, float]) -> float:
        """Exponential slippage model for large orders"""
        decay_factor = params['exp_decay_factor']
        normalized_amount = order_amount_usd / 10_000_000  # Normalize to 10M
        return (1 - np.exp(-normalized_amount * decay_factor)) * 0.1  # Cap at 10%

    def _impact_function_model(
        self,
        order_amount_usd: float,
        params: Dict[str, float],
        profile: SlippageProfile
    ) -> float:
        """Advanced impact function model"""
        coefficient = params['impact_coefficient']
        exponent = params['impact_exponent']

        # Normalize by average daily volume
        volume_ratio = order_amount_usd / profile.avg_daily_volume

        # Impact function: coefficient * (volume_ratio)^exponent
        slippage = coefficient * (volume_ratio ** exponent)

        return min(slippage, 0.2)  # Cap at 20%

    def _apply_market_adjustments(
        self,
        base_slippage: float,
        market_conditions: MarketConditions,
        order_type: OrderType,
        profile: SlippageProfile
    ) -> float:
        """Apply market condition adjustments to base slippage"""

        adjusted_slippage = base_slippage

        # Volatility adjustment
        volatility_factor = 1 + (market_conditions.volatility - 0.2) * 2  # Base 20% vol
        adjusted_slippage *= volatility_factor

        # Market stress adjustment
        stress_factor = 1 + market_conditions.market_stress
        adjusted_slippage *= stress_factor

        # Time of day adjustment
        time_factors = {
            'asia': 1.1,      # Lower liquidity
            'europe': 0.9,    # Higher liquidity
            'america': 1.0,   # Normal liquidity
            'overnight': 1.3  # Lowest liquidity
        }
        time_factor = time_factors.get(market_conditions.time_of_day, 1.0)
        adjusted_slippage *= time_factor

        # Order type adjustment
        order_type_factors = {
            OrderType.MARKET: 1.0,
            OrderType.LIMIT: 0.8,
            OrderType.STOP_LOSS: 1.2,
            OrderType.LIQUIDATION: 1.5  # Liquidations have higher slippage
        }
        order_factor = order_type_factors.get(order_type, 1.0)
        adjusted_slippage *= order_factor

        # Spread adjustment
        spread_factor = 1 + (market_conditions.spread_bps - profile.base_spread_bps) / 1000
        adjusted_slippage *= spread_factor

        return max(adjusted_slippage, profile.base_spread_bps / 10000)  # Minimum = spread

    def _calculate_confidence_interval(
        self,
        result: SlippageResult,
        profile: SlippageProfile,
        market_conditions: MarketConditions
    ) -> Tuple[float, float]:
        """Calculate confidence interval for slippage estimate"""

        # Base confidence based on model accuracy
        base_std = result.slippage_pct * 0.2  # 20% standard deviation

        # Adjust for market conditions
        if market_conditions.volatility > 0.4:
            base_std *= 1.5

        if market_conditions.market_stress > 0.7:
            base_std *= 1.3

        # 95% confidence interval
        margin_of_error = base_std * 1.96

        lower_bound = max(0, result.slippage_pct - margin_of_error)
        upper_bound = result.slippage_pct + margin_of_error

        return (lower_bound, upper_bound)

    async def calculate_cascade_slippage(
        self,
        liquidation_events: List[Dict[str, Any]],
        time_window_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate aggregate slippage for a cascade of liquidation events

        Args:
            liquidation_events: List of liquidation events
            time_window_minutes: Time window over which events occur

        Returns:
            Aggregate slippage analysis
        """
        logger.info(f"Calculating cascade slippage for {len(liquidation_events)} events")

        # Group events by asset pair
        events_by_pair = {}
        for event in liquidation_events:
            pair = event.get('asset_pair', 'ALGO/USDC')
            if pair not in events_by_pair:
                events_by_pair[pair] = []
            events_by_pair[pair].append(event)

        # Calculate slippage for each pair
        pair_results = {}
        total_impact = 0

        for pair, events in events_by_pair.items():
            # Calculate cumulative order size
            total_amount = sum(event['amount_usd'] for event in events)

            # Adjust for time compression (events happening quickly increase impact)
            time_compression_factor = max(1.0, 60 / time_window_minutes)
            adjusted_amount = total_amount * time_compression_factor

            # Calculate market conditions during stress
            stress_conditions = self._get_stress_market_conditions(pair, len(events))

            # Calculate slippage
            result = await self.calculate_slippage(
                asset_pair=pair,
                order_amount_usd=adjusted_amount,
                side="sell",  # Liquidations are typically sells
                order_type=OrderType.LIQUIDATION,
                market_conditions=stress_conditions,
                model=SlippageModel.ADAPTIVE
            )

            pair_results[pair] = {
                'individual_events': len(events),
                'total_amount_usd': total_amount,
                'adjusted_amount_usd': adjusted_amount,
                'slippage_result': result,
                'recovery_time_minutes': self._estimate_slippage_recovery_time(result)
            }

            total_impact += result.price_impact_pct * total_amount

        # Calculate system-wide impact
        total_volume = sum(event['amount_usd'] for event in liquidation_events)
        weighted_avg_slippage = sum(
            r['slippage_result'].slippage_pct * r['total_amount_usd']
            for r in pair_results.values()
        ) / total_volume if total_volume > 0 else 0

        return {
            'total_events': len(liquidation_events),
            'total_volume_usd': total_volume,
            'time_window_minutes': time_window_minutes,
            'weighted_avg_slippage_pct': weighted_avg_slippage,
            'weighted_avg_slippage_bps': weighted_avg_slippage * 10000,
            'total_market_impact': total_impact / total_volume if total_volume > 0 else 0,
            'pair_breakdown': pair_results,
            'systemic_risk_level': self._assess_systemic_slippage_risk(pair_results, total_volume)
        }

    def _get_stress_market_conditions(self, asset_pair: str, num_events: int) -> MarketConditions:
        """Get market conditions during liquidation stress"""
        normal_conditions = self._get_current_market_conditions(asset_pair)

        # Increase stress factors based on number of concurrent events
        stress_multiplier = 1 + (num_events - 1) * 0.2  # 20% increase per additional event

        return MarketConditions(
            volatility=normal_conditions.volatility * stress_multiplier,
            volume_24h=normal_conditions.volume_24h,
            spread_bps=normal_conditions.spread_bps * stress_multiplier,
            depth_score=normal_conditions.depth_score / stress_multiplier,
            time_of_day=normal_conditions.time_of_day,
            market_stress=min(1.0, normal_conditions.market_stress * stress_multiplier)
        )

    def _estimate_slippage_recovery_time(self, result: SlippageResult) -> float:
        """Estimate time for market to recover from slippage"""
        # Base recovery time
        base_time = 15  # 15 minutes

        # Scale with impact size
        impact_factor = result.price_impact_pct * 100  # Per 1% impact

        # Temporary vs permanent impact affects recovery
        temp_recovery = result.temporary_impact * 30  # 30 min per 1% temporary impact
        perm_recovery = result.permanent_impact * 120  # 120 min per 1% permanent impact

        total_recovery = base_time + temp_recovery + perm_recovery

        return min(total_recovery, 240)  # Cap at 4 hours

    def _assess_systemic_slippage_risk(
        self,
        pair_results: Dict[str, Any],
        total_volume: float
    ) -> str:
        """Assess systemic risk level from slippage analysis"""

        # Calculate weighted average slippage
        avg_slippage = sum(
            r['slippage_result'].slippage_pct * r['total_amount_usd']
            for r in pair_results.values()
        ) / total_volume if total_volume > 0 else 0

        # Number of affected pairs
        affected_pairs = len(pair_results)

        # Maximum single-pair impact
        max_impact = max(
            r['slippage_result'].price_impact_pct for r in pair_results.values()
        ) if pair_results else 0

        # Risk assessment
        if avg_slippage < 0.005 and max_impact < 0.02:  # <0.5% avg, <2% max
            return "LOW"
        elif avg_slippage < 0.015 and max_impact < 0.05 and affected_pairs < 3:
            return "MEDIUM"
        elif avg_slippage < 0.03 and max_impact < 0.10:
            return "HIGH"
        else:
            return "CRITICAL"

    async def optimize_execution_strategy(
        self,
        asset_pair: str,
        total_amount_usd: float,
        max_slippage_bps: float,
        time_horizon_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Optimize execution strategy to minimize slippage

        Args:
            asset_pair: Trading pair
            total_amount_usd: Total amount to execute
            max_slippage_bps: Maximum acceptable slippage
            time_horizon_minutes: Time horizon for execution

        Returns:
            Optimized execution strategy
        """
        logger.info(f"Optimizing execution for {total_amount_usd:,.0f} USD of {asset_pair}")

        # Get current market conditions
        market_conditions = self._get_current_market_conditions(asset_pair)
        profile = self.asset_profiles[asset_pair]

        # Test different chunking strategies
        strategies = []

        # Strategy 1: Single large order
        single_order = await self.calculate_slippage(
            asset_pair, total_amount_usd, "sell", OrderType.MARKET, market_conditions
        )
        strategies.append({
            'name': 'Single Order',
            'chunks': 1,
            'chunk_size': total_amount_usd,
            'total_slippage_bps': single_order.slippage_bps,
            'execution_time_minutes': 1,
            'result': single_order
        })

        # Strategy 2-5: Multiple chunks
        for num_chunks in [2, 5, 10, 20]:
            chunk_size = total_amount_usd / num_chunks
            chunk_interval = time_horizon_minutes / num_chunks

            # Calculate slippage for each chunk (with recovery between chunks)
            total_slippage = 0
            for i in range(num_chunks):
                # Market recovers slightly between chunks
                recovery_factor = 1 - (i * 0.05)  # 5% recovery per chunk
                adjusted_conditions = self._apply_recovery_factor(
                    market_conditions, recovery_factor
                )

                chunk_result = await self.calculate_slippage(
                    asset_pair, chunk_size, "sell", OrderType.MARKET, adjusted_conditions
                )
                total_slippage += chunk_result.slippage_bps

            avg_slippage = total_slippage / num_chunks

            strategies.append({
                'name': f'{num_chunks} Chunks',
                'chunks': num_chunks,
                'chunk_size': chunk_size,
                'chunk_interval_minutes': chunk_interval,
                'total_slippage_bps': avg_slippage,
                'execution_time_minutes': time_horizon_minutes,
                'meets_constraint': avg_slippage <= max_slippage_bps
            })

        # Select optimal strategy
        valid_strategies = [s for s in strategies if s.get('meets_constraint', False)]

        if valid_strategies:
            optimal = min(valid_strategies, key=lambda x: x['total_slippage_bps'])
        else:
            # If no strategy meets constraints, select best available
            optimal = min(strategies, key=lambda x: x['total_slippage_bps'])
            optimal['constraint_violated'] = True

        return {
            'asset_pair': asset_pair,
            'total_amount_usd': total_amount_usd,
            'max_slippage_bps': max_slippage_bps,
            'time_horizon_minutes': time_horizon_minutes,
            'optimal_strategy': optimal,
            'all_strategies': strategies,
            'market_conditions': market_conditions.__dict__
        }

    def _apply_recovery_factor(
        self,
        market_conditions: MarketConditions,
        recovery_factor: float
    ) -> MarketConditions:
        """Apply market recovery factor to conditions"""
        return MarketConditions(
            volatility=market_conditions.volatility * recovery_factor,
            volume_24h=market_conditions.volume_24h,
            spread_bps=market_conditions.spread_bps * recovery_factor,
            depth_score=market_conditions.depth_score / recovery_factor,
            time_of_day=market_conditions.time_of_day,
            market_stress=market_conditions.market_stress * recovery_factor
        )

    def get_slippage_statistics(self) -> Dict[str, Any]:
        """Get statistics from historical slippage calculations"""
        if not self.calculation_history:
            return {"error": "No calculation history available"}

        history = self.calculation_history

        return {
            'total_calculations': len(history),
            'avg_slippage_bps': np.mean([r.slippage_bps for r in history]),
            'median_slippage_bps': np.median([r.slippage_bps for r in history]),
            'max_slippage_bps': max(r.slippage_bps for r in history),
            'avg_price_impact_pct': np.mean([r.price_impact_pct for r in history]),
            'model_usage': {
                model.value: sum(1 for r in history if r.model_used == model)
                for model in SlippageModel
            },
            'order_size_distribution': self._analyze_order_size_distribution(),
            'slippage_by_pair': self._analyze_slippage_by_pair()
        }

    def _analyze_order_size_distribution(self) -> Dict[str, int]:
        """Analyze distribution of order sizes in history"""
        distribution = {'small': 0, 'medium': 0, 'large': 0, 'whale': 0}

        for result in self.calculation_history:
            amount = result.order_amount_usd
            if amount < 1000:
                distribution['small'] += 1
            elif amount < 10000:
                distribution['medium'] += 1
            elif amount < 100000:
                distribution['large'] += 1
            else:
                distribution['whale'] += 1

        return distribution

    def _analyze_slippage_by_pair(self) -> Dict[str, Dict[str, float]]:
        """Analyze slippage statistics by asset pair"""
        pair_stats = {}

        for pair in self.asset_profiles.keys():
            pair_history = [r for r in self.calculation_history if pair in str(r)]

            if pair_history:
                pair_stats[pair] = {
                    'count': len(pair_history),
                    'avg_slippage_bps': np.mean([r.slippage_bps for r in pair_history]),
                    'max_slippage_bps': max(r.slippage_bps for r in pair_history),
                    'avg_impact_pct': np.mean([r.price_impact_pct for r in pair_history])
                }

        return pair_stats


# Example usage and testing
async def main():
    """Example usage of the slippage calculator"""
    calculator = SlippageCalculator()

    # Calculate slippage for a large order
    result = await calculator.calculate_slippage(
        asset_pair='ALGO/USDC',
        order_amount_usd=2_000_000,
        side='sell',
        order_type=OrderType.LIQUIDATION,
        model=SlippageModel.ADAPTIVE
    )

    print(f"Slippage Analysis:")
    print(f"Order: ${result.order_amount_usd:,.0f} {result.side}")
    print(f"Slippage: {result.slippage_bps:.1f} bps ({result.slippage_pct:.3%})")
    print(f"Price Impact: {result.price_impact_pct:.3%}")
    print(f"Temporary Impact: {result.temporary_impact:.3%}")
    print(f"Permanent Impact: {result.permanent_impact:.3%}")
    print(f"Confidence Interval: {result.confidence_interval[0]:.3%} - {result.confidence_interval[1]:.3%}")

    # Optimize execution strategy
    optimization = await calculator.optimize_execution_strategy(
        asset_pair='ALGO/USDC',
        total_amount_usd=5_000_000,
        max_slippage_bps=100,
        time_horizon_minutes=60
    )

    print(f"\nExecution Optimization:")
    optimal = optimization['optimal_strategy']
    print(f"Optimal Strategy: {optimal['name']}")
    print(f"Chunks: {optimal['chunks']}")
    print(f"Total Slippage: {optimal['total_slippage_bps']:.1f} bps")

if __name__ == "__main__":
    asyncio.run(main())