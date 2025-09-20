"""
Consolidated Collateral Analysis Engine

Combines all collateral analysis functionality into a single, working module.
Includes asset valuation, risk assessment, liquidation scenarios, and portfolio analysis.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

import httpx

from .models import (
    ASAToken, AssetValuation, CollateralPosition, CollateralAnalysis,
    AssetType, LiquidationScenario, PortfolioRisk, RiskLevel, LiquidityTier,
    AlgorandAddress
)
from .config import CollateralConfig, DEFAULT_COLLATERAL_CONFIG

logger = logging.getLogger(__name__)


class CollateralAnalyzer:
    """
    Unified collateral analysis engine for Algorand lending.

    Provides comprehensive collateral assessment including:
    - Real-time asset valuation with risk metrics
    - Portfolio diversification analysis
    - Liquidation scenario modeling
    - Risk-adjusted collateral requirements
    """

    def __init__(self, config: Optional[CollateralConfig] = None):
        """Initialize the collateral analyzer with configuration."""
        self.config = config or DEFAULT_COLLATERAL_CONFIG
        self._price_cache: Dict[str, Tuple[Decimal, datetime]] = {}
        self._asset_cache: Dict[str, ASAToken] = {}

    async def analyze_collateral(
        self,
        assets: List[ASAToken],
        quantities: List[Decimal],
        loan_amount_usd: Decimal,
        market_condition: str = "normal"
    ) -> CollateralAnalysis:
        """
        Perform comprehensive collateral analysis.

        Args:
            assets: List of ASA tokens being used as collateral
            quantities: Corresponding quantities for each asset
            loan_amount_usd: Loan amount in USD
            market_condition: Current market condition (normal, volatile, bear, crisis)

        Returns:
            Complete collateral analysis result
        """
        try:
            if len(assets) != len(quantities):
                raise ValueError("Assets and quantities lists must have the same length")

            # Step 1: Get asset valuations
            logger.info("Getting asset valuations...")
            valuations = await self._get_asset_valuations(assets, quantities)

            # Step 2: Create collateral positions
            logger.info("Creating collateral positions...")
            positions = await self._create_collateral_positions(
                assets, quantities, valuations, market_condition
            )

            # Step 3: Analyze portfolio risk
            logger.info("Analyzing portfolio risk...")
            portfolio_risk = self._analyze_portfolio_risk(positions)

            # Step 4: Calculate requirements and analysis
            logger.info("Calculating collateral requirements...")
            analysis = self._create_collateral_analysis(
                loan_amount_usd, positions, portfolio_risk, market_condition
            )

            logger.info("Collateral analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Error in collateral analysis: {e}")
            raise

    async def _get_asset_valuations(
        self,
        assets: List[ASAToken],
        quantities: List[Decimal]
    ) -> List[AssetValuation]:
        """Get valuations for all assets in parallel."""
        tasks = []
        for asset, quantity in zip(assets, quantities):
            task = self._get_asset_valuation(asset, quantity)
            tasks.append(task)

        valuations = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions and provide fallbacks
        results = []
        for i, valuation in enumerate(valuations):
            if isinstance(valuation, Exception):
                asset = assets[i]
                logger.error(f"Failed to value {asset.symbol}: {valuation}")
                results.append(self._create_fallback_valuation(asset))
            else:
                results.append(valuation)

        return results

    async def _get_asset_valuation(
        self,
        asset: ASAToken,
        quantity: Decimal = Decimal('1')
    ) -> AssetValuation:
        """Get complete valuation for a single asset."""
        try:
            # Get current price with confidence
            price_data = await self._get_price_with_confidence(asset.symbol)
            current_price = price_data['price']
            confidence = price_data['confidence']

            # Get market data
            market_data = await self._get_market_data(asset.symbol)

            # Calculate volatility metrics
            volatility_data = self._calculate_volatility_metrics(asset.symbol)

            # Determine liquidity tier
            liquidity_tier = self._determine_liquidity_tier(market_data)

            # Calculate correlation with ALGO
            correlation = self._calculate_algo_correlation(asset.symbol)

            return AssetValuation(
                asset=asset,
                current_price_usd=current_price,
                market_cap_usd=market_data['market_cap'],
                daily_volume_usd=market_data['volume_24h'],
                price_confidence=confidence,
                volatility_30d=volatility_data['volatility_30d'],
                volatility_7d=volatility_data['volatility_7d'],
                max_drawdown_30d=volatility_data['max_drawdown_30d'],
                correlation_with_algo=correlation,
                liquidity_tier=liquidity_tier,
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error valuing asset {asset.symbol}: {e}")
            return self._create_fallback_valuation(asset)

    async def _get_price_with_confidence(self, symbol: str) -> Dict[str, Decimal]:
        """Get price with confidence score from multiple sources."""
        # Check cache first
        cache_key = symbol.upper()
        if cache_key in self._price_cache:
            price, timestamp = self._price_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self.config.price_cache_ttl:
                return {'price': price, 'confidence': Decimal('0.85')}

        try:
            # Fetch from external price sources
            prices = await self._fetch_multiple_prices(symbol)

            if not prices:
                fallback_price = self._get_fallback_price(symbol)
                return {'price': fallback_price, 'confidence': Decimal('0.5')}

            # Aggregate prices for higher confidence
            final_price, confidence = self._aggregate_prices(prices)

            # Cache the result
            self._price_cache[cache_key] = (final_price, datetime.utcnow())

            return {'price': final_price, 'confidence': confidence}

        except Exception as e:
            logger.warning(f"Error getting price for {symbol}: {e}")
            fallback_price = self._get_fallback_price(symbol)
            return {'price': fallback_price, 'confidence': Decimal('0.3')}

    async def _fetch_multiple_prices(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch prices from multiple sources for aggregation."""
        prices = []

        # Try external price sources (this would integrate with actual price feeds)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Example: Market data service
                response = await client.get(
                    f"{self.config.service.market_data_url}/price/{symbol}"
                )
                if response.status_code == 200:
                    data = response.json()
                    prices.append({
                        'source': 'market_data',
                        'price': Decimal(str(data.get('price', 0))),
                        'confidence': Decimal(str(data.get('confidence', 0.7)))
                    })
        except Exception as e:
            logger.debug(f"Failed to get price from market data service: {e}")

        # Add more price sources here...

        return prices

    def _aggregate_prices(self, prices: List[Dict[str, Any]]) -> Tuple[Decimal, Decimal]:
        """Aggregate multiple prices with confidence weighting."""
        if not prices:
            raise ValueError("No prices to aggregate")

        if len(prices) == 1:
            return prices[0]['price'], prices[0]['confidence']

        # Confidence-weighted average
        total_weight = sum(p['confidence'] for p in prices)
        if total_weight == 0:
            # Simple average if no confidence scores
            avg_price = sum(p['price'] for p in prices) / len(prices)
            return avg_price, Decimal('0.5')

        weighted_price = sum(
            p['price'] * p['confidence'] for p in prices
        ) / total_weight

        # Confidence is average of individual confidences, boosted by multiple sources
        base_confidence = total_weight / len(prices)
        multi_source_boost = min(Decimal('0.1') * (len(prices) - 1), Decimal('0.3'))
        final_confidence = min(base_confidence + multi_source_boost, Decimal('0.95'))

        return weighted_price, final_confidence

    async def _get_market_data(self, symbol: str) -> Dict[str, Decimal]:
        """Get market data (volume, market cap) for an asset."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.config.service.market_data_url}/asset/{symbol}/market-data"
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'market_cap': Decimal(str(data.get('market_cap', 0))),
                        'volume_24h': Decimal(str(data.get('volume_24h', 0))),
                        'volume_7d': Decimal(str(data.get('volume_7d', 0)))
                    }
        except Exception as e:
            logger.debug(f"Failed to get market data for {symbol}: {e}")

        # Return fallback market data
        return self._get_fallback_market_data(symbol)

    def _calculate_volatility_metrics(self, symbol: str) -> Dict[str, Decimal]:
        """Calculate volatility metrics for an asset."""
        # In a real implementation, this would fetch historical price data
        # For now, return reasonable estimates based on asset type

        symbol_upper = symbol.upper()

        if symbol_upper in ['USDC', 'USDT', 'STBL']:
            return {
                'volatility_30d': Decimal('0.02'),     # 2% for stablecoins
                'volatility_7d': Decimal('0.01'),      # 1% for stablecoins
                'max_drawdown_30d': Decimal('0.01')    # 1% max drawdown
            }
        elif symbol_upper == 'ALGO':
            return {
                'volatility_30d': Decimal('0.4'),      # 40% for ALGO
                'volatility_7d': Decimal('0.3'),       # 30% for ALGO
                'max_drawdown_30d': Decimal('0.25')    # 25% max drawdown
            }
        else:
            return {
                'volatility_30d': Decimal('0.6'),      # 60% for other tokens
                'volatility_7d': Decimal('0.5'),       # 50% for other tokens
                'max_drawdown_30d': Decimal('0.4')     # 40% max drawdown
            }

    def _calculate_algo_correlation(self, symbol: str) -> Decimal:
        """Calculate correlation with ALGO."""
        if symbol.upper() == 'ALGO':
            return Decimal('1.0')

        # Default correlation estimates based on asset type
        if symbol.upper() in ['USDC', 'USDT', 'STBL']:
            return Decimal('0.1')  # Low correlation for stablecoins
        else:
            return Decimal('0.4')  # Moderate correlation for other assets

    def _determine_liquidity_tier(self, market_data: Dict[str, Decimal]) -> LiquidityTier:
        """Determine liquidity tier based on market data."""
        volume_24h = market_data['volume_24h']
        market_cap = market_data['market_cap']

        if volume_24h >= self.config.min_liquidity_usd * 10 and market_cap >= self.config.min_liquidity_usd * 100:
            return LiquidityTier.HIGH
        elif volume_24h >= self.config.min_liquidity_usd and market_cap >= self.config.min_liquidity_usd * 10:
            return LiquidityTier.MEDIUM
        elif volume_24h >= self.config.min_liquidity_usd / 10 and market_cap >= self.config.min_liquidity_usd:
            return LiquidityTier.LOW
        else:
            return LiquidityTier.ILLIQUID

    async def _create_collateral_positions(
        self,
        assets: List[ASAToken],
        quantities: List[Decimal],
        valuations: List[AssetValuation],
        market_condition: str
    ) -> List[CollateralPosition]:
        """Create collateral positions with risk analysis."""
        positions = []

        for asset, quantity, valuation in zip(assets, quantities, valuations):
            # Determine asset type
            asset_type = self._determine_asset_type(asset)

            # Calculate position value
            position_value_usd = valuation.current_price_usd * quantity

            # Create liquidation scenarios
            liquidation_scenarios = self._create_liquidation_scenarios(
                asset, valuation, position_value_usd, asset_type
            )

            # Calculate haircut
            haircut_percentage = self._calculate_position_haircut(
                asset_type, valuation, market_condition
            )

            # Adjusted value after haircut
            adjusted_value_usd = position_value_usd * (Decimal('1') - haircut_percentage)

            # Determine risk level
            risk_level = self._determine_position_risk_level(valuation, liquidation_scenarios)

            # Create position
            position = CollateralPosition(
                asset=asset,
                quantity=quantity,
                valuation=valuation,
                position_value_usd=position_value_usd,
                haircut_percentage=haircut_percentage,
                adjusted_value_usd=adjusted_value_usd,
                asset_type=asset_type,
                liquidation_scenarios=liquidation_scenarios,
                risk_level=risk_level
            )

            positions.append(position)

        return positions

    def _determine_asset_type(self, asset: ASAToken) -> AssetType:
        """Determine the asset type from asset information."""
        symbol = asset.symbol.upper()

        if symbol == 'ALGO':
            return AssetType.ALGO_NATIVE
        elif symbol in ['USDC', 'USDT', 'STBL']:
            return AssetType.STABLECOIN
        elif 'GOV' in symbol or 'VOTE' in symbol:
            return AssetType.GOVERNANCE_TOKEN
        elif 'LP' in symbol or 'POOL' in symbol:
            return AssetType.LP_TOKEN
        elif 'ST' in symbol or 'STAKE' in symbol:
            return AssetType.LIQUID_STAKING
        else:
            return AssetType.ASA_TOKEN

    def _create_liquidation_scenarios(
        self,
        asset: ASAToken,
        valuation: AssetValuation,
        position_value_usd: Decimal,
        asset_type: AssetType
    ) -> List[LiquidationScenario]:
        """Create liquidation scenarios for a position."""
        scenarios = []

        # Base liquidation parameters by asset type
        base_params = {
            AssetType.ALGO_NATIVE: {
                'base_slippage': Decimal('0.02'),
                'base_timeline': Decimal('2'),
                'base_cost': Decimal('0.01')
            },
            AssetType.STABLECOIN: {
                'base_slippage': Decimal('0.005'),
                'base_timeline': Decimal('1'),
                'base_cost': Decimal('0.005')
            },
            AssetType.ASA_TOKEN: {
                'base_slippage': Decimal('0.05'),
                'base_timeline': Decimal('6'),
                'base_cost': Decimal('0.02')
            },
            AssetType.GOVERNANCE_TOKEN: {
                'base_slippage': Decimal('0.03'),
                'base_timeline': Decimal('4'),
                'base_cost': Decimal('0.015')
            },
            AssetType.LP_TOKEN: {
                'base_slippage': Decimal('0.08'),
                'base_timeline': Decimal('12'),
                'base_cost': Decimal('0.03')
            },
            AssetType.LIQUID_STAKING: {
                'base_slippage': Decimal('0.025'),
                'base_timeline': Decimal('3'),
                'base_cost': Decimal('0.012')
            }
        }

        params = base_params.get(asset_type, base_params[AssetType.ASA_TOKEN])

        # Normal market scenario
        scenarios.append(LiquidationScenario(
            scenario_name="normal_market",
            trigger_price_drop=Decimal('0.2'),  # 20% drop
            liquidation_timeline_hours=params['base_timeline'],
            expected_slippage=params['base_slippage'],
            recovery_rate=Decimal('0.9') - params['base_slippage'],
            liquidation_cost=params['base_cost'],
            net_recovery_rate=Decimal('0.9') - params['base_slippage'] - params['base_cost'],
            probability=Decimal('0.6')
        ))

        # Stress market scenario
        scenarios.append(LiquidationScenario(
            scenario_name="stress_market",
            trigger_price_drop=Decimal('0.35'),  # 35% drop
            liquidation_timeline_hours=params['base_timeline'] * Decimal('2'),
            expected_slippage=params['base_slippage'] * Decimal('2'),
            recovery_rate=Decimal('0.75') - params['base_slippage'] * Decimal('2'),
            liquidation_cost=params['base_cost'] * Decimal('1.5'),
            net_recovery_rate=Decimal('0.75') - params['base_slippage'] * Decimal('2') - params['base_cost'] * Decimal('1.5'),
            probability=Decimal('0.3')
        ))

        # Crisis scenario
        scenarios.append(LiquidationScenario(
            scenario_name="crisis_market",
            trigger_price_drop=Decimal('0.5'),  # 50% drop
            liquidation_timeline_hours=params['base_timeline'] * Decimal('4'),
            expected_slippage=params['base_slippage'] * Decimal('3'),
            recovery_rate=Decimal('0.6') - params['base_slippage'] * Decimal('3'),
            liquidation_cost=params['base_cost'] * Decimal('2'),
            net_recovery_rate=Decimal('0.6') - params['base_slippage'] * Decimal('3') - params['base_cost'] * Decimal('2'),
            probability=Decimal('0.1')
        ))

        return scenarios

    def _calculate_position_haircut(
        self,
        asset_type: AssetType,
        valuation: AssetValuation,
        market_condition: str
    ) -> Decimal:
        """Calculate haircut for a position."""
        # Base haircut by asset type
        base_haircuts = {
            AssetType.ALGO_NATIVE: self.config.algo_haircut,
            AssetType.STABLECOIN: self.config.stablecoin_haircut,
            AssetType.ASA_TOKEN: self.config.asa_haircut,
            AssetType.GOVERNANCE_TOKEN: self.config.asa_haircut * Decimal('0.8'),
            AssetType.LP_TOKEN: self.config.lp_token_haircut,
            AssetType.LIQUID_STAKING: self.config.algo_haircut * Decimal('1.2')
        }

        base_haircut = base_haircuts.get(asset_type, self.config.asa_haircut)

        # Volatility adjustment
        vol_adjustment = min(valuation.volatility_30d * Decimal('0.2'), Decimal('0.1'))

        # Liquidity adjustment
        liquidity_adjustments = {
            LiquidityTier.HIGH: Decimal('0'),
            LiquidityTier.MEDIUM: Decimal('0.02'),
            LiquidityTier.LOW: Decimal('0.05'),
            LiquidityTier.ILLIQUID: Decimal('0.1')
        }
        liquidity_adjustment = liquidity_adjustments.get(valuation.liquidity_tier, Decimal('0.05'))

        # Market condition adjustment
        market_adjustments = {
            'normal': Decimal('0'),
            'volatile': Decimal('0.02'),
            'bear': Decimal('0.05'),
            'crisis': Decimal('0.1')
        }
        market_adjustment = market_adjustments.get(market_condition, Decimal('0'))

        # Price confidence adjustment
        confidence_adjustment = (Decimal('1') - valuation.price_confidence) * Decimal('0.05')

        # Combine all adjustments
        total_haircut = (
            base_haircut +
            vol_adjustment +
            liquidity_adjustment +
            market_adjustment +
            confidence_adjustment
        )

        return min(total_haircut, Decimal('0.5'))  # Cap at 50%

    def _determine_position_risk_level(
        self,
        valuation: AssetValuation,
        liquidation_scenarios: List[LiquidationScenario]
    ) -> RiskLevel:
        """Determine risk level for a position."""
        # Start with volatility-based risk
        if valuation.volatility_30d <= Decimal('0.1'):
            risk_score = 1
        elif valuation.volatility_30d <= Decimal('0.3'):
            risk_score = 2
        elif valuation.volatility_30d <= Decimal('0.5'):
            risk_score = 3
        else:
            risk_score = 4

        # Adjust for liquidation risk
        worst_recovery = min(
            scenario.net_recovery_rate for scenario in liquidation_scenarios
        ) if liquidation_scenarios else Decimal('0.8')

        if worst_recovery < Decimal('0.5'):
            risk_score += 1
        elif worst_recovery < Decimal('0.7'):
            risk_score += 0.5

        # Adjust for liquidity
        if valuation.liquidity_tier == LiquidityTier.ILLIQUID:
            risk_score += 1
        elif valuation.liquidity_tier == LiquidityTier.LOW:
            risk_score += 0.5

        # Convert to risk level
        if risk_score <= 1.5:
            return RiskLevel.VERY_LOW
        elif risk_score <= 2.5:
            return RiskLevel.LOW
        elif risk_score <= 3.5:
            return RiskLevel.MEDIUM
        elif risk_score <= 4.5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _analyze_portfolio_risk(self, positions: List[CollateralPosition]) -> PortfolioRisk:
        """Analyze portfolio-level risk metrics."""
        if not positions:
            return self._create_empty_portfolio_risk()

        # Calculate total portfolio value
        total_value = sum(pos.position_value_usd for pos in positions)

        # Calculate concentration risk
        concentration_risk = self._calculate_concentration_risk(positions, total_value)

        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(positions)

        # Calculate liquidity risk
        liquidity_risk = self._calculate_liquidity_risk(positions)

        # Calculate correlation risk
        correlation_risk = self._calculate_correlation_risk(positions)

        # Run stress tests
        stress_test_results = self._run_stress_tests(positions)

        # Determine recommended haircut and collateral ratio
        overall_risk = max(concentration_risk, liquidity_risk, correlation_risk)
        recommended_haircut = min(overall_risk * Decimal('0.3'), Decimal('0.4'))
        min_collateral_ratio = self.config.min_collateral_ratio + (overall_risk * Decimal('0.5'))

        return PortfolioRisk(
            total_value_usd=total_value,
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk,
            correlation_risk=correlation_risk,
            stress_test_results=stress_test_results,
            recommended_haircut=recommended_haircut,
            min_collateral_ratio=min_collateral_ratio
        )

    def _calculate_concentration_risk(
        self,
        positions: List[CollateralPosition],
        total_value: Decimal
    ) -> Decimal:
        """Calculate portfolio concentration risk."""
        if total_value == 0:
            return Decimal('0')

        # Calculate Herfindahl-Hirschman Index for concentration
        hhi = sum(
            (pos.position_value_usd / total_value) ** 2
            for pos in positions
        )

        # Convert HHI to risk score (0-1, higher is worse)
        # Perfect diversification (many equal positions) = low HHI = low risk
        # High concentration = high HHI = high risk
        max_concentration = min(Decimal('1'), hhi * Decimal('2'))

        # Check single asset concentration limit
        max_single_asset = max(
            pos.position_value_usd / total_value for pos in positions
        )

        if max_single_asset > self.config.max_asset_concentration:
            concentration_penalty = (max_single_asset - self.config.max_asset_concentration) * Decimal('2')
            max_concentration = min(Decimal('1'), max_concentration + concentration_penalty)

        return max_concentration

    def _calculate_diversification_score(self, positions: List[CollateralPosition]) -> Decimal:
        """Calculate portfolio diversification score (0-1, higher is better)."""
        if len(positions) <= 1:
            return Decimal('0.2')  # Poor diversification with single asset

        # Asset type diversification
        asset_types = set(pos.asset_type for pos in positions)
        type_diversity = min(Decimal(str(len(asset_types))) / Decimal('4'), Decimal('1'))

        # Liquidity tier diversification
        liquidity_tiers = set(pos.valuation.liquidity_tier for pos in positions)
        liquidity_diversity = min(Decimal(str(len(liquidity_tiers))) / Decimal('3'), Decimal('1'))

        # Number of assets bonus
        count_bonus = min(Decimal(str(len(positions) - 1)) * Decimal('0.1'), Decimal('0.3'))

        return min(type_diversity * Decimal('0.5') + liquidity_diversity * Decimal('0.3') + count_bonus, Decimal('1'))

    def _calculate_liquidity_risk(self, positions: List[CollateralPosition]) -> Decimal:
        """Calculate portfolio liquidity risk."""
        if not positions:
            return Decimal('0')

        total_value = sum(pos.position_value_usd for pos in positions)

        # Weight liquidity risk by position size
        weighted_liquidity_risk = Decimal('0')

        liquidity_risk_scores = {
            LiquidityTier.HIGH: Decimal('0.1'),
            LiquidityTier.MEDIUM: Decimal('0.3'),
            LiquidityTier.LOW: Decimal('0.6'),
            LiquidityTier.ILLIQUID: Decimal('0.9')
        }

        for pos in positions:
            weight = pos.position_value_usd / total_value if total_value > 0 else Decimal('0')
            risk_score = liquidity_risk_scores.get(pos.valuation.liquidity_tier, Decimal('0.5'))
            weighted_liquidity_risk += weight * risk_score

        return min(weighted_liquidity_risk, Decimal('1'))

    def _calculate_correlation_risk(self, positions: List[CollateralPosition]) -> Decimal:
        """Calculate correlation risk in the portfolio."""
        if len(positions) <= 1:
            return Decimal('0.2')  # Low correlation risk with single asset

        # Calculate average correlation with ALGO
        avg_correlation = sum(
            pos.valuation.correlation_with_algo for pos in positions
        ) / len(positions)

        # High correlation with ALGO increases systemic risk
        correlation_risk = avg_correlation * Decimal('0.7')

        # Asset type correlation - similar asset types increase risk
        asset_type_counts = {}
        total_value = sum(pos.position_value_usd for pos in positions)

        for pos in positions:
            asset_type = pos.asset_type
            weight = pos.position_value_usd / total_value if total_value > 0 else Decimal('0')
            asset_type_counts[asset_type] = asset_type_counts.get(asset_type, Decimal('0')) + weight

        # Penalty for over-concentration in similar asset types
        type_concentration_penalty = max(
            Decimal('0'),
            max(asset_type_counts.values()) - Decimal('0.5')
        ) * Decimal('0.5')

        return min(correlation_risk + type_concentration_penalty, Decimal('1'))

    def _run_stress_tests(self, positions: List[CollateralPosition]) -> Dict[str, Decimal]:
        """Run stress tests on the portfolio."""
        stress_scenarios = {
            'market_crash_20': Decimal('0.2'),  # 20% general decline
            'market_crash_35': Decimal('0.35'), # 35% general decline
            'algo_crash_50': Decimal('0.5'),    # 50% ALGO-specific crash
            'liquidity_crisis': Decimal('0.3')  # 30% decline + liquidity issues
        }

        results = {}
        total_value = sum(pos.position_value_usd for pos in positions)

        for scenario, decline_factor in stress_scenarios.items():
            portfolio_impact = Decimal('0')

            for pos in positions:
                # Base decline
                asset_decline = decline_factor

                # ALGO-correlated assets decline more in ALGO crash
                if scenario == 'algo_crash_50':
                    asset_decline = decline_factor * (Decimal('0.5') + pos.valuation.correlation_with_algo * Decimal('0.5'))

                # Liquidity crisis hits illiquid assets harder
                if scenario == 'liquidity_crisis':
                    liquidity_multiplier = {
                        LiquidityTier.HIGH: Decimal('1.0'),
                        LiquidityTier.MEDIUM: Decimal('1.2'),
                        LiquidityTier.LOW: Decimal('1.5'),
                        LiquidityTier.ILLIQUID: Decimal('2.0')
                    }.get(pos.valuation.liquidity_tier, Decimal('1.0'))
                    asset_decline = min(asset_decline * liquidity_multiplier, Decimal('0.8'))

                # Calculate position impact
                position_weight = pos.position_value_usd / total_value if total_value > 0 else Decimal('0')
                portfolio_impact += position_weight * asset_decline

            results[scenario] = portfolio_impact

        return results

    def _create_empty_portfolio_risk(self) -> PortfolioRisk:
        """Create empty portfolio risk for edge cases."""
        return PortfolioRisk(
            total_value_usd=Decimal('0'),
            diversification_score=Decimal('0'),
            concentration_risk=Decimal('0'),
            liquidity_risk=Decimal('0'),
            correlation_risk=Decimal('0'),
            stress_test_results={},
            recommended_haircut=Decimal('0'),
            min_collateral_ratio=self.config.min_collateral_ratio
        )

    def _create_collateral_analysis(
        self,
        loan_amount_usd: Decimal,
        positions: List[CollateralPosition],
        portfolio_risk: PortfolioRisk,
        market_condition: str
    ) -> CollateralAnalysis:
        """Create the final collateral analysis result."""

        # Calculate totals
        total_collateral_value = sum(pos.position_value_usd for pos in positions)
        total_adjusted_value = sum(pos.adjusted_value_usd for pos in positions)

        # Calculate collateral ratios
        current_collateral_ratio = (
            total_adjusted_value / loan_amount_usd if loan_amount_usd > 0 else Decimal('0')
        )

        # Required ratio considers portfolio risk and market conditions
        base_required_ratio = portfolio_risk.min_collateral_ratio
        market_adjustment = {
            'normal': Decimal('0'),
            'volatile': Decimal('0.1'),
            'bear': Decimal('0.2'),
            'crisis': Decimal('0.3')
        }.get(market_condition, Decimal('0'))

        required_collateral_ratio = base_required_ratio + market_adjustment

        # Sufficiency and additional requirements
        is_sufficient = current_collateral_ratio >= required_collateral_ratio
        additional_collateral_needed = max(
            Decimal('0'),
            (required_collateral_ratio * loan_amount_usd) - total_adjusted_value
        )

        # Liquidation threshold (typically lower than required ratio)
        liquidation_threshold = max(
            self.config.liquidation_threshold,
            required_collateral_ratio * Decimal('0.85')
        )

        # Generate alerts and recommendations
        price_alerts = self._generate_price_alerts(positions)
        recommendations = self._generate_recommendations(
            positions, portfolio_risk, current_collateral_ratio, required_collateral_ratio, market_condition
        )

        return CollateralAnalysis(
            loan_amount_usd=loan_amount_usd,
            positions=positions,
            portfolio_risk=portfolio_risk,
            total_collateral_value=total_collateral_value,
            total_adjusted_value=total_adjusted_value,
            current_collateral_ratio=current_collateral_ratio,
            required_collateral_ratio=required_collateral_ratio,
            is_sufficient=is_sufficient,
            additional_collateral_needed=additional_collateral_needed,
            liquidation_threshold=liquidation_threshold,
            price_alerts=price_alerts,
            recommendations=recommendations,
            analysis_timestamp=datetime.utcnow()
        )

    def _generate_price_alerts(self, positions: List[CollateralPosition]) -> List[Dict[str, Any]]:
        """Generate price alerts for positions."""
        alerts = []

        for position in positions:
            # Low confidence alert
            if position.valuation.price_confidence < Decimal('0.7'):
                alerts.append({
                    'asset': position.asset.symbol,
                    'type': 'low_confidence',
                    'message': f"Low price confidence for {position.asset.symbol} ({position.valuation.price_confidence:.1%})",
                    'severity': 'warning'
                })

            # High volatility alert
            if position.valuation.volatility_30d > Decimal('0.6'):
                alerts.append({
                    'asset': position.asset.symbol,
                    'type': 'high_volatility',
                    'message': f"High volatility detected for {position.asset.symbol} ({position.valuation.volatility_30d:.1%})",
                    'severity': 'warning'
                })

            # Liquidation risk alert
            worst_recovery = min(
                s.net_recovery_rate for s in position.liquidation_scenarios
            ) if position.liquidation_scenarios else Decimal('0.8')

            if worst_recovery < Decimal('0.6'):
                alerts.append({
                    'asset': position.asset.symbol,
                    'type': 'liquidation_risk',
                    'message': f"High liquidation risk for {position.asset.symbol} (worst case {worst_recovery:.1%} recovery)",
                    'severity': 'error'
                })

        return alerts

    def _generate_recommendations(
        self,
        positions: List[CollateralPosition],
        portfolio_risk: PortfolioRisk,
        current_ratio: Decimal,
        required_ratio: Decimal,
        market_condition: str
    ) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = []

        # Collateral sufficiency recommendations
        if current_ratio < required_ratio:
            shortage_pct = ((required_ratio - current_ratio) / required_ratio * 100)
            recommendations.append(
                f"Collateral insufficient. Need {shortage_pct:.1f}% more collateral to meet requirements."
            )

        # Portfolio risk recommendations
        if portfolio_risk.concentration_risk > Decimal('0.6'):
            recommendations.append(
                "High concentration risk detected. Consider diversifying across more assets."
            )

        if portfolio_risk.liquidity_risk > Decimal('0.7'):
            recommendations.append(
                "High liquidity risk. Consider including more liquid assets in the portfolio."
            )

        if portfolio_risk.diversification_score < Decimal('0.4'):
            recommendations.append(
                "Poor diversification. Consider adding assets from different categories."
            )

        # Individual position recommendations
        for position in positions:
            if position.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                recommendations.append(
                    f"High risk position: {position.asset.symbol}. Consider reducing size or replacing with safer assets."
                )

            if position.haircut_percentage > Decimal('0.25'):
                recommendations.append(
                    f"Large haircut on {position.asset.symbol} ({position.haircut_percentage:.1%}). Consider more stable alternatives."
                )

        # Market condition recommendations
        if market_condition in ['bear', 'crisis']:
            recommendations.append(
                f"Operating in {market_condition} conditions. Consider conservative positioning and frequent monitoring."
            )

        # Safety margin recommendations
        safety_margin = (current_ratio / required_ratio - 1) if required_ratio > 0 else Decimal('0')
        if safety_margin < Decimal('0.2'):
            recommendations.append(
                "Consider maintaining a larger safety margin above minimum requirements."
            )

        return recommendations[:8]  # Limit to top 8 recommendations

    # Fallback methods
    def _get_fallback_price(self, symbol: str) -> Decimal:
        """Get fallback price for an asset."""
        fallback_prices = {
            'ALGO': Decimal('0.20'),
            'USDC': Decimal('1.00'),
            'USDT': Decimal('1.00'),
            'STBL': Decimal('1.00')
        }
        return fallback_prices.get(symbol.upper(), Decimal('1.00'))

    def _get_fallback_market_data(self, symbol: str) -> Dict[str, Decimal]:
        """Get fallback market data for an asset."""
        symbol_upper = symbol.upper()

        if symbol_upper == 'ALGO':
            return {
                'market_cap': Decimal('2000000000'),  # $2B
                'volume_24h': Decimal('50000000'),    # $50M
                'volume_7d': Decimal('350000000')     # $350M
            }
        elif symbol_upper in ['USDC', 'USDT']:
            return {
                'market_cap': Decimal('100000000'),   # $100M
                'volume_24h': Decimal('10000000'),    # $10M
                'volume_7d': Decimal('70000000')      # $70M
            }
        else:
            return {
                'market_cap': Decimal('10000000'),    # $10M
                'volume_24h': Decimal('100000'),      # $100k
                'volume_7d': Decimal('700000')        # $700k
            }

    def _create_fallback_valuation(self, asset: ASAToken) -> AssetValuation:
        """Create a conservative fallback valuation when data is unavailable."""
        fallback_price = self._get_fallback_price(asset.symbol)
        market_data = self._get_fallback_market_data(asset.symbol)
        volatility_data = self._calculate_volatility_metrics(asset.symbol)

        return AssetValuation(
            asset=asset,
            current_price_usd=fallback_price,
            market_cap_usd=market_data['market_cap'],
            daily_volume_usd=market_data['volume_24h'],
            price_confidence=Decimal('0.3'),  # Low confidence for fallback
            volatility_30d=volatility_data['volatility_30d'],
            volatility_7d=volatility_data['volatility_7d'],
            max_drawdown_30d=volatility_data['max_drawdown_30d'],
            correlation_with_algo=self._calculate_algo_correlation(asset.symbol),
            liquidity_tier=self._determine_liquidity_tier(market_data),
            last_updated=datetime.utcnow()
        )

    # Public utility methods
    async def validate_collateral_assets(self, assets: List[ASAToken]) -> Dict[str, List[str]]:
        """Validate that collateral assets are acceptable."""
        validation_results = {}

        for asset in assets:
            issues = []

            # Check if asset has minimum market data
            try:
                market_data = await self._get_market_data(asset.symbol)
                if market_data['volume_24h'] < self.config.min_liquidity_usd / 10:
                    issues.append("Very low trading volume")
                if market_data['market_cap'] < self.config.min_liquidity_usd:
                    issues.append("Very low market cap")
            except Exception:
                issues.append("Unable to fetch market data")

            # Check price data availability
            try:
                price_data = await self._get_price_with_confidence(asset.symbol)
                if price_data['confidence'] < Decimal('0.5'):
                    issues.append("Low price confidence")
            except Exception:
                issues.append("Unable to fetch price data")

            validation_results[asset.symbol] = issues

        return validation_results

    def get_supported_assets(self) -> List[str]:
        """Get list of well-supported assets for collateral."""
        return ['ALGO', 'USDC', 'USDT', 'STBL']  # Basic supported assets

    def estimate_liquidation_time(self, position: CollateralPosition) -> Decimal:
        """Estimate time to liquidate a position in normal conditions."""
        # Use the normal market scenario
        normal_scenarios = [
            s for s in position.liquidation_scenarios
            if s.scenario_name == "normal_market"
        ]

        if normal_scenarios:
            return normal_scenarios[0].liquidation_timeline_hours
        else:
            # Fallback estimate based on liquidity tier
            liquidity_estimates = {
                LiquidityTier.HIGH: Decimal('2'),
                LiquidityTier.MEDIUM: Decimal('6'),
                LiquidityTier.LOW: Decimal('24'),
                LiquidityTier.ILLIQUID: Decimal('168')  # 1 week
            }
            return liquidity_estimates.get(position.valuation.liquidity_tier, Decimal('24'))