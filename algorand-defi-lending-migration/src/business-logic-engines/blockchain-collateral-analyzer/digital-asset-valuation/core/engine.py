"""
Digital Asset Valuation Engine

High-level interface for digital asset valuation with MCP integration.
"""

import asyncio
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys

# Import from common shared modules
from ...common.models.blockchain_collateral_models import (
    DigitalAsset, CollateralPosition, CollateralPortfolio,
    LiquidationScenario, CollateralAnalysisResult,
    DigitalCollateralType, VolatilityMetrics, LiquidityMetrics, PriceOracle
)
from .config import load_config, DigitalAssetValuationConfig
from .constants import ConfigurableDigitalAssetConstants
from .calculator import ConfigurableDigitalCollateralCalculator


class DigitalAssetValuationEngine:
    """
    Main engine for digital asset valuation with configurable parameters
    and MCP service integration.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the valuation engine"""
        self.config = load_config(config_path)
        self.constants = ConfigurableDigitalAssetConstants(config_path)
        self.calculator = ConfigurableDigitalCollateralCalculator(config_path)
        self._price_cache = {}
        self._last_price_update = None

    async def get_asset_price(self, symbol: str) -> Optional[float]:
        """Get current asset price from MCP services or fallback"""

        # Check cache first
        cache_expiry = self.config.analysis.cache_expiry_minutes * 60  # Convert to seconds
        if (self._last_price_update and
            (datetime.now() - self._last_price_update).seconds < cache_expiry and
            symbol in self._price_cache):
            return self._price_cache[symbol]

        try:
            # Try market data MCP service
            market_data_url = self.config.mcp_services.market_data_url
            response = requests.get(
                f"{market_data_url}/price/{symbol}",
                timeout=self.config.price_feeds.max_staleness_seconds
            )

            if response.status_code == 200:
                price_data = response.json()
                price = float(price_data.get('price', 0))

                if price > 0:
                    self._price_cache[symbol] = price
                    self._last_price_update = datetime.now()
                    return price

        except Exception as e:
            print(f"Failed to fetch price for {symbol} from MCP: {e}")

        # Fallback to configured prices
        fallback_price = self.constants.get_fallback_price(symbol)
        if fallback_price > 0:
            self._price_cache[symbol] = fallback_price
            return fallback_price

        return None

    def create_digital_asset(
        self,
        symbol: str,
        current_price_usd: float,
        asset_type: Optional[DigitalCollateralType] = None
    ) -> DigitalAsset:
        """Create a DigitalAsset instance with configured parameters"""

        # Get asset info from configuration
        asset_info = self.constants.algorand_assets.get(symbol, {})

        # Determine asset type
        if asset_type is None:
            asset_type_str = asset_info.get('type', 'asa_token')
            asset_type = getattr(DigitalCollateralType, asset_type_str.upper(), DigitalCollateralType.ASA_TOKEN)

        # Get volatility metrics
        volatility_data = self.constants.get_volatility_estimate(symbol)
        volatility_metrics = VolatilityMetrics(
            volatility_30d=volatility_data['volatility_30d'],
            volatility_7d=volatility_data['volatility_7d'],
            max_drawdown_30d=volatility_data['max_drawdown_30d'],
            value_at_risk_95=volatility_data['value_at_risk_95'],
            correlation_with_algo=volatility_data.get('correlation_with_algo', 0.3),
            stress_test_scenarios=volatility_data.get('stress_test_scenarios', {
                'market_crash': -0.5,
                'regulatory_shock': -0.3,
                'technical_failure': -0.4
            })
        )

        # Get liquidity metrics
        liquidity_data = self.constants.get_liquidity_estimate(symbol)
        liquidity_metrics = LiquidityMetrics(
            daily_volume_usd=liquidity_data['daily_volume_usd'],
            market_cap_usd=liquidity_data['market_cap_usd'],
            depth_1_percent=liquidity_data.get('depth_1_percent', 100000.0),
            largest_liquidation_size=liquidity_data.get('largest_liquidation_size', 50000.0),
            average_spread_bps=liquidity_data.get('average_spread_bps', 10.0),
            liquidity_tier=liquidity_data['liquidity_tier']
        )

        # Create price oracle
        oracle_config = self.constants.default_oracle_config
        price_oracle = PriceOracle(
            primary_oracle=oracle_config['primary_oracle'],
            backup_oracles=oracle_config['backup_oracles'],
            update_frequency=oracle_config['update_frequency'],
            reliability_score=oracle_config['reliability_threshold'],
            price_deviation_threshold=oracle_config['max_price_deviation'],
            fallback_mechanism=oracle_config['fallback_strategy']
        )

        # Get collateral parameters
        collateral_ratios = self.constants.default_collateral_ratios
        maintenance_ratios = self.constants.maintenance_ratios
        liquidation_penalties = self.constants.liquidation_penalties

        return DigitalAsset(
            asset_id=asset_info.get('asset_id', '0'),
            symbol=symbol,
            name=asset_info.get('name', symbol),
            asset_type=asset_type,
            volatility_metrics=volatility_metrics,
            liquidity_metrics=liquidity_metrics,
            price_oracle=price_oracle,
            base_collateral_ratio=collateral_ratios.get(asset_type, 1.5),
            maintenance_ratio=maintenance_ratios.get(asset_type, 1.25),
            liquidation_penalty=liquidation_penalties.get(asset_type, 0.05),
            decimals=asset_info.get('decimals', 6),
            is_active=True
        )

    def create_collateral_position(
        self,
        asset: DigitalAsset,
        quantity: float,
        market_conditions: str = "normal",
        current_price_usd: Optional[float] = None
    ) -> CollateralPosition:
        """Create a CollateralPosition with risk-adjusted values"""

        if current_price_usd is None:
            # Extract price from asset - this might be in asset metadata or we need to get it elsewhere
            # For now, we'll use a fallback price mechanism
            current_price_usd = self.constants.get_fallback_price(asset.symbol)
            if current_price_usd == 0.0:
                current_price_usd = 1.0  # Default fallback

        value_usd = current_price_usd * quantity
        haircut = self.calculator.calculate_asset_haircut(asset, market_conditions)
        adjusted_value_usd = value_usd * (1.0 - haircut)

        return CollateralPosition(
            asset=asset,
            quantity=quantity,
            current_price_usd=current_price_usd,
            value_usd=value_usd,
            haircut_percentage=haircut,
            adjusted_value_usd=adjusted_value_usd,
            price_confidence=0.85,  # Default confidence
            liquidation_urgency="low",  # Default urgency
            time_to_liquidate_hours=24.0  # Default liquidation time
        )

    async def analyze_portfolio_collateral(
        self,
        portfolio_data: List[Dict[str, Any]],
        loan_amount_usd: float,
        market_conditions: str = "normal"
    ) -> CollateralAnalysisResult:
        """
        Analyze a portfolio for collateral requirements

        Args:
            portfolio_data: List of dicts with 'symbol', 'quantity' keys
            loan_amount_usd: Loan amount in USD
            market_conditions: Market condition string

        Returns:
            CollateralAnalysisResult
        """

        positions = []

        for position_data in portfolio_data:
            symbol = position_data['symbol']
            quantity = position_data['quantity']

            # Get current price
            price = await self.get_asset_price(symbol)
            if price is None:
                raise ValueError(f"Could not get price for {symbol}")

            # Create asset and position
            asset = self.create_digital_asset(symbol, price)
            position = self.create_collateral_position(asset, quantity, market_conditions)
            positions.append(position)

        return self.calculator.analyze_digital_collateral_requirement(
            loan_amount_usd=loan_amount_usd,
            collateral_positions=positions,
            market_conditions=market_conditions,
            stress_test=True
        )

    def run_stress_test(
        self,
        positions: List[CollateralPosition],
        scenario_name: str
    ) -> Dict[str, Any]:
        """Run a stress test scenario on the portfolio"""

        scenarios = self.constants.stress_test_scenarios
        if scenario_name not in scenarios:
            raise ValueError(f"Unknown stress test scenario: {scenario_name}")

        scenario = scenarios[scenario_name]

        # Apply scenario impacts to positions
        stressed_positions = []
        for position in positions:
            stressed_asset = position.asset

            # Apply price impact
            if stressed_asset.asset_type == DigitalCollateralType.ALGO_NATIVE:
                price_impact = scenario['algo_impact']
            else:
                # Apply correlation-based impact for other assets
                correlation = scenario.get('correlation_increase', 0.3)
                price_impact = scenario['algo_impact'] * correlation

            new_price = stressed_asset.current_price_usd * (1 + price_impact)
            new_value_usd = position.quantity * new_price

            # Apply liquidity reduction
            liquidity_reduction = scenario['liquidity_reduction']
            adjusted_liquidity_tier = "low" if liquidity_reduction > 0.5 else stressed_asset.liquidity_metrics.liquidity_tier

            # Create stressed position
            stressed_position = CollateralPosition(
                asset=DigitalAsset(
                    symbol=stressed_asset.symbol,
                    name=stressed_asset.name,
                    asset_type=stressed_asset.asset_type,
                    current_price_usd=new_price,
                    volatility_metrics=stressed_asset.volatility_metrics,
                    liquidity_metrics=LiquidityMetrics(
                        daily_volume_usd=stressed_asset.liquidity_metrics.daily_volume_usd * (1 - liquidity_reduction),
                        market_cap_usd=stressed_asset.liquidity_metrics.market_cap_usd,
                        liquidity_tier=adjusted_liquidity_tier
                    ),
                    algorithm_asset_id=stressed_asset.algorithm_asset_id,
                    decimals=stressed_asset.decimals,
                    is_native_algo=stressed_asset.is_native_algo
                ),
                quantity=position.quantity,
                value_usd=new_value_usd,
                adjusted_value_usd=new_value_usd * (1.0 - self.calculator.calculate_asset_haircut(
                    stressed_asset, "crisis"
                )),
                haircut_percentage=self.calculator.calculate_asset_haircut(stressed_asset, "crisis"),
                last_updated=datetime.now()
            )
            stressed_positions.append(stressed_position)

        return {
            'scenario_name': scenario_name,
            'scenario_description': scenario['description'],
            'original_total_value': sum(p.value_usd for p in positions),
            'stressed_total_value': sum(p.value_usd for p in stressed_positions),
            'original_adjusted_value': sum(p.adjusted_value_usd for p in positions),
            'stressed_adjusted_value': sum(p.adjusted_value_usd for p in stressed_positions),
            'value_impact_percentage': (sum(p.value_usd for p in stressed_positions) - sum(p.value_usd for p in positions)) / sum(p.value_usd for p in positions) * 100,
            'stressed_positions': stressed_positions
        }

    def get_asset_classification(self, symbol: str) -> DigitalCollateralType:
        """Classify an asset based on configured patterns"""

        symbol_upper = symbol.upper()
        asset_config = self.constants.algorand_assets.get(symbol, {})

        if 'type' in asset_config:
            type_str = asset_config['type']
            return getattr(DigitalCollateralType, type_str.upper(), DigitalCollateralType.ASA_TOKEN)

        # Fallback to pattern matching (if this was implemented in config)
        if symbol_upper in ["USDC", "USDT", "STBL"]:
            return DigitalCollateralType.STABLECOIN
        elif symbol_upper == "ALGO":
            return DigitalCollateralType.ALGO_NATIVE
        else:
            return DigitalCollateralType.ASA_TOKEN

    def get_recommended_collateral_ratio(
        self,
        asset_type: DigitalCollateralType,
        portfolio_diversification: float = 0.5,
        market_conditions: str = "normal"
    ) -> float:
        """Get recommended collateral ratio for an asset type"""

        base_ratio = self.constants.default_collateral_ratios.get(asset_type, 1.5)

        # Diversification adjustment
        if portfolio_diversification >= 0.7:
            diversification_adjustment = -self.config.analysis.diversification_bonus_factor * 2
        elif portfolio_diversification >= 0.4:
            diversification_adjustment = 0.0
        else:
            diversification_adjustment = self.config.analysis.diversification_bonus_factor * 4

        # Market condition adjustment
        market_conditions_key = f"{market_conditions}_market" if market_conditions in ["bull", "bear"] else market_conditions
        market_multiplier = self.constants.market_condition_multipliers.get(market_conditions_key, {})
        market_adjustment = market_multiplier.get("collateral_ratio_adjustment", 0.0)

        # Safety buffer
        safety_buffer = self.config.analysis.safety_buffer

        return base_ratio + diversification_adjustment + market_adjustment + safety_buffer

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'mcp_services': {
                'algorand_reader_url': self.config.mcp_services.algorand_reader_url,
                'market_data_url': self.config.mcp_services.market_data_url
            },
            'collateral_ratios': {
                'algo_native': self.config.default_collateral_ratios.algo_native,
                'stablecoin': self.config.default_collateral_ratios.stablecoin,
                'asa_token': self.config.default_collateral_ratios.asa_token,
                'governance_token': self.config.default_collateral_ratios.governance_token,
                'lp_token': self.config.default_collateral_ratios.lp_token,
                'liquid_staking': self.config.default_collateral_ratios.liquid_staking,
            },
            'analysis_parameters': {
                'safety_buffer': self.config.analysis.safety_buffer,
                'cache_expiry_minutes': self.config.analysis.cache_expiry_minutes,
                'diversification_bonus_factor': self.config.analysis.diversification_bonus_factor,
                'max_position_concentration': self.config.analysis.max_position_concentration
            },
            'supported_assets': list(self.constants.algorand_assets.keys()),
            'stress_test_scenarios': list(self.constants.stress_test_scenarios.keys())
        }