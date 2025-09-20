"""
Pool Yield Calculator

Comprehensive calculator for LP token yields across multiple DEX protocols.
Analyzes trading fees, liquidity mining rewards, and impermanent loss risks.
"""

import asyncio
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
import statistics
import math

# Import individual DEX analyzers
from .tinyman_pools import TinymanPoolsAnalyzer, TinymanYieldData, ImpermanentLossAnalysis
from .algofi_pools import AlgofiPoolsAnalyzer, AlgofiPoolData, LiquidityMiningData

@dataclass
class PoolYieldSummary:
    """Summary of yield data for a single pool across all DEXes"""
    asset_pair: str
    dex_yields: Dict[str, float]  # DEX name -> total APY
    trading_fee_yields: Dict[str, float]
    reward_yields: Dict[str, float]
    liquidity_values: Dict[str, float]
    volume_24h_values: Dict[str, float]
    best_yield_dex: str
    worst_yield_dex: str
    yield_spread: float
    weighted_average_yield: float
    confidence_score: float

@dataclass
class AggregatedPoolYields:
    """Aggregated yield data across all pools and DEXes"""
    pool_summaries: List[PoolYieldSummary]
    overall_weighted_yield: float
    total_tvl_across_dexes: float
    total_volume_24h: float
    dex_market_shares: Dict[str, float]
    top_yield_opportunities: List[Dict[str, Any]]
    average_il_risk: float
    sustainability_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class YieldProjection:
    """Yield projection with risk analysis"""
    pool_pair: str
    dex_name: str
    projected_7d_yield: float
    projected_30d_yield: float
    projected_90d_yield: float
    confidence_intervals: Dict[str, Tuple[float, float]]
    risk_factors: List[str]
    impermanent_loss_estimate: float
    net_yield_after_il: float

class PoolYieldCalculator:
    """
    Comprehensive pool yield calculator that aggregates data from multiple DEXes
    to provide unified yield analysis and optimal LP positioning recommendations.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the pool yield calculator"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()

        # Initialize DEX analyzers
        self.analyzers = {
            'tinyman': TinymanPoolsAnalyzer(config_path),
            'algofi': AlgofiPoolsAnalyzer(config_path)
        }

        self.cache = {}
        self.yield_history = []

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            # Fallback configuration
            return {
                'dex_protocols': {
                    'tinyman': {'weight': 0.45, 'enabled': True},
                    'algofi_dex': {'weight': 0.35, 'enabled': True}
                },
                'asset_pairs': {
                    'ALGO/USDC': {'target_apy': 0.08},
                    'ALGO/USDT': {'target_apy': 0.075}
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the calculator"""
        logger = logging.getLogger('pool_yield_calculator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def calculate_all_pool_yields(self) -> AggregatedPoolYields:
        """
        Calculate yields for all pools across all DEXes

        Returns:
            AggregatedPoolYields: Comprehensive yield analysis
        """
        try:
            # Check cache first
            if self._is_cache_valid('aggregated_pool_yields'):
                return self.cache['aggregated_pool_yields']

            # Fetch data from all DEXes
            dex_data = await self._fetch_all_dex_data()

            # Extract unique asset pairs
            asset_pairs = self._extract_asset_pairs(dex_data)

            # Calculate yield summaries for each pair
            pool_summaries = []
            for pair in asset_pairs:
                summary = await self._calculate_pair_yield_summary(pair, dex_data)
                if summary:
                    pool_summaries.append(summary)

            # Calculate aggregated metrics
            aggregated = self._calculate_aggregated_metrics(pool_summaries, dex_data)

            # Cache the result
            self.cache['aggregated_pool_yields'] = aggregated
            self.cache['aggregated_pool_yields_timestamp'] = datetime.now()

            # Store in history
            self.yield_history.append(aggregated)
            if len(self.yield_history) > 100:
                self.yield_history.pop(0)

            return aggregated

        except Exception as e:
            self.logger.error(f"Error calculating pool yields: {e}")
            return self._get_fallback_aggregated_yields()

    async def _fetch_all_dex_data(self) -> Dict[str, Any]:
        """Fetch yield data from all enabled DEXes"""
        dex_data = {}
        enabled_dexes = {
            name: config for name, config in self.config['dex_protocols'].items()
            if config.get('enabled', True)
        }

        # Fetch data from all DEXes concurrently
        tasks = []
        for dex_name in enabled_dexes.keys():
            if dex_name == 'tinyman' and 'tinyman' in self.analyzers:
                tasks.append(('tinyman', self.analyzers['tinyman'].analyze_tinyman_yields()))
            elif dex_name == 'algofi_dex' and 'algofi' in self.analyzers:
                tasks.append(('algofi', self.analyzers['algofi'].analyze_algofi_pools()))

        # Wait for all tasks to complete
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

        # Process results
        for i, (dex_name, _) in enumerate(tasks):
            result = results[i]
            if not isinstance(result, Exception):
                dex_data[dex_name] = result
            else:
                self.logger.error(f"Error fetching data from {dex_name}: {result}")

        return dex_data

    def _extract_asset_pairs(self, dex_data: Dict[str, Any]) -> List[str]:
        """Extract unique asset pairs from all DEX data"""
        asset_pairs = set()

        for dex_name, data in dex_data.items():
            if dex_name == 'tinyman' and isinstance(data, TinymanYieldData):
                for pool in data.pools:
                    pair = f"{pool.asset_1_name}/{pool.asset_2_name}"
                    asset_pairs.add(pair)
            elif dex_name == 'algofi' and isinstance(data, AlgofiPoolData):
                for pool in data.pools:
                    pair = f"{pool.asset_1_name}/{pool.asset_2_name}"
                    asset_pairs.add(pair)

        return list(asset_pairs)

    async def _calculate_pair_yield_summary(self, asset_pair: str,
                                          dex_data: Dict[str, Any]) -> Optional[PoolYieldSummary]:
        """Calculate yield summary for a specific asset pair"""
        try:
            assets = asset_pair.split('/')
            if len(assets) != 2:
                return None

            asset_1, asset_2 = assets

            dex_yields = {}
            trading_fee_yields = {}
            reward_yields = {}
            liquidity_values = {}
            volume_24h_values = {}

            # Collect data from each DEX
            for dex_name, data in dex_data.items():
                pool_data = None

                if dex_name == 'tinyman' and isinstance(data, TinymanYieldData):
                    # Find matching pool in Tinyman
                    for pool in data.pools:
                        if ((pool.asset_1_name == asset_1 and pool.asset_2_name == asset_2) or
                            (pool.asset_1_name == asset_2 and pool.asset_2_name == asset_1)):
                            pool_data = pool
                            break

                    if pool_data:
                        dex_yields['Tinyman'] = pool_data.total_apy
                        trading_fee_yields['Tinyman'] = pool_data.apy_fees
                        reward_yields['Tinyman'] = pool_data.apy_rewards
                        liquidity_values['Tinyman'] = pool_data.liquidity_usd
                        volume_24h_values['Tinyman'] = pool_data.volume_24h_usd

                elif dex_name == 'algofi' and isinstance(data, AlgofiPoolData):
                    # Find matching pool in Algofi
                    for pool in data.pools:
                        if ((pool.asset_1_name == asset_1 and pool.asset_2_name == asset_2) or
                            (pool.asset_1_name == asset_2 and pool.asset_2_name == asset_1)):
                            pool_data = pool
                            break

                    if pool_data:
                        dex_yields['Algofi'] = pool_data.total_apy
                        trading_fee_yields['Algofi'] = pool_data.apy_trading_fees
                        reward_yields['Algofi'] = pool_data.apy_liquidity_mining + pool_data.apy_alfi_rewards
                        liquidity_values['Algofi'] = pool_data.liquidity_usd
                        volume_24h_values['Algofi'] = pool_data.volume_24h_usd

            if not dex_yields:
                return None

            # Calculate metrics
            best_yield_dex = max(dex_yields, key=dex_yields.get)
            worst_yield_dex = min(dex_yields, key=dex_yields.get)
            yield_spread = max(dex_yields.values()) - min(dex_yields.values())

            # Calculate weighted average yield
            total_weight = sum(liquidity_values.values())
            if total_weight > 0:
                weighted_average = sum(
                    yield_val * liquidity_values.get(dex, 0) for dex, yield_val in dex_yields.items()
                ) / total_weight
            else:
                weighted_average = statistics.mean(dex_yields.values())

            # Calculate confidence score
            confidence_score = self._calculate_pair_confidence(dex_yields, liquidity_values)

            return PoolYieldSummary(
                asset_pair=asset_pair,
                dex_yields=dex_yields,
                trading_fee_yields=trading_fee_yields,
                reward_yields=reward_yields,
                liquidity_values=liquidity_values,
                volume_24h_values=volume_24h_values,
                best_yield_dex=best_yield_dex,
                worst_yield_dex=worst_yield_dex,
                yield_spread=yield_spread,
                weighted_average_yield=weighted_average,
                confidence_score=confidence_score
            )

        except Exception as e:
            self.logger.error(f"Error calculating yield summary for {asset_pair}: {e}")
            return None

    def _calculate_pair_confidence(self, dex_yields: Dict[str, float],
                                 liquidity_values: Dict[str, float]) -> float:
        """Calculate confidence score for a pair's yield data"""
        confidence = 1.0

        # Reduce confidence for fewer DEXes
        if len(dex_yields) < 2:
            confidence *= 0.7

        # Reduce confidence for high yield variance
        if len(dex_yields) > 1:
            yield_values = list(dex_yields.values())
            if statistics.stdev(yield_values) > 0.05:  # > 5% std dev
                confidence *= 0.8

        # Reduce confidence for low total liquidity
        total_liquidity = sum(liquidity_values.values())
        if total_liquidity < 500000:  # < $500K total liquidity
            confidence *= 0.6

        return max(confidence, 0.1)

    def _calculate_aggregated_metrics(self, pool_summaries: List[PoolYieldSummary],
                                    dex_data: Dict[str, Any]) -> AggregatedPoolYields:
        """Calculate aggregated metrics from pool summaries"""
        if not pool_summaries:
            return self._get_fallback_aggregated_yields()

        # Calculate overall weighted yield
        total_weighted_yield = 0.0
        total_weight = 0.0

        for summary in pool_summaries:
            total_liquidity = sum(summary.liquidity_values.values())
            total_weighted_yield += summary.weighted_average_yield * total_liquidity
            total_weight += total_liquidity

        overall_weighted_yield = total_weighted_yield / total_weight if total_weight > 0 else 0.0

        # Calculate total TVL and volume
        total_tvl = sum(sum(summary.liquidity_values.values()) for summary in pool_summaries)
        total_volume_24h = sum(sum(summary.volume_24h_values.values()) for summary in pool_summaries)

        # Calculate DEX market shares
        dex_market_shares = self._calculate_dex_market_shares(pool_summaries)

        # Find top yield opportunities
        top_opportunities = self._find_top_yield_opportunities(pool_summaries)

        # Calculate average IL risk
        average_il_risk = self._estimate_average_il_risk(pool_summaries)

        # Calculate sustainability score
        sustainability_score = self._calculate_sustainability_score(pool_summaries)

        return AggregatedPoolYields(
            pool_summaries=pool_summaries,
            overall_weighted_yield=overall_weighted_yield,
            total_tvl_across_dexes=total_tvl,
            total_volume_24h=total_volume_24h,
            dex_market_shares=dex_market_shares,
            top_yield_opportunities=top_opportunities,
            average_il_risk=average_il_risk,
            sustainability_score=sustainability_score,
            timestamp=datetime.now(),
            metadata={
                'total_pairs': len(pool_summaries),
                'dex_count': len(dex_data),
                'calculation_method': 'liquidity_weighted_aggregation'
            }
        )

    def _calculate_dex_market_shares(self, pool_summaries: List[PoolYieldSummary]) -> Dict[str, float]:
        """Calculate market share for each DEX by TVL"""
        dex_tvls = {}
        total_tvl = 0.0

        for summary in pool_summaries:
            for dex, liquidity in summary.liquidity_values.items():
                dex_tvls[dex] = dex_tvls.get(dex, 0) + liquidity
                total_tvl += liquidity

        if total_tvl > 0:
            return {dex: tvl / total_tvl for dex, tvl in dex_tvls.items()}
        else:
            return {}

    def _find_top_yield_opportunities(self, pool_summaries: List[PoolYieldSummary]) -> List[Dict[str, Any]]:
        """Find top yield opportunities across all pools and DEXes"""
        opportunities = []

        for summary in pool_summaries:
            for dex, yield_val in summary.dex_yields.items():
                liquidity = summary.liquidity_values.get(dex, 0)
                volume_24h = summary.volume_24h_values.get(dex, 0)

                # Only include opportunities with sufficient liquidity
                if liquidity >= 100000:  # $100K minimum
                    opportunities.append({
                        'pair': summary.asset_pair,
                        'dex': dex,
                        'total_apy': yield_val,
                        'trading_fee_apy': summary.trading_fee_yields.get(dex, 0),
                        'reward_apy': summary.reward_yields.get(dex, 0),
                        'liquidity_usd': liquidity,
                        'volume_24h_usd': volume_24h,
                        'confidence_score': summary.confidence_score,
                        'risk_score': self._calculate_opportunity_risk_score(summary.asset_pair, yield_val)
                    })

        # Sort by total APY, then by confidence
        opportunities.sort(key=lambda x: (x['total_apy'], x['confidence_score']), reverse=True)

        return opportunities[:20]  # Top 20 opportunities

    def _calculate_opportunity_risk_score(self, asset_pair: str, yield_apy: float) -> float:
        """Calculate risk score for a yield opportunity"""
        risk_score = 0.0

        # Base risk from yield level
        if yield_apy > 1.0:  # > 100% APY
            risk_score += 0.8
        elif yield_apy > 0.5:  # > 50% APY
            risk_score += 0.5
        elif yield_apy > 0.2:  # > 20% APY
            risk_score += 0.3
        else:
            risk_score += 0.1

        # Asset-specific risk
        if 'goBTC' in asset_pair or 'goETH' in asset_pair:
            risk_score += 0.2  # Higher risk for wrapped assets
        elif 'USDC/USDT' in asset_pair:
            risk_score -= 0.1  # Lower risk for stablecoin pairs

        return min(max(risk_score, 0.0), 1.0)

    def _estimate_average_il_risk(self, pool_summaries: List[PoolYieldSummary]) -> float:
        """Estimate average impermanent loss risk across all pools"""
        il_estimates = []

        for summary in pool_summaries:
            # Estimate IL risk based on asset pair
            pair_config = self.config.get('asset_pairs', {}).get(summary.asset_pair, {})
            il_risk_factor = pair_config.get('il_risk_factor', 0.7)
            il_estimates.append(il_risk_factor)

        return statistics.mean(il_estimates) if il_estimates else 0.7

    def _calculate_sustainability_score(self, pool_summaries: List[PoolYieldSummary]) -> float:
        """Calculate sustainability score for the overall yield ecosystem"""
        sustainability_factors = []

        for summary in pool_summaries:
            # Factor 1: Trading fees vs. rewards ratio
            total_trading_fees = sum(summary.trading_fee_yields.values())
            total_rewards = sum(summary.reward_yields.values())

            if total_rewards > 0:
                fee_to_rewards_ratio = total_trading_fees / total_rewards
                sustainability_factor = min(fee_to_rewards_ratio / 2.0, 1.0)
            else:
                sustainability_factor = 1.0  # All fees, highly sustainable

            # Factor 2: Liquidity distribution
            if len(summary.liquidity_values) > 1:
                liquidity_values = list(summary.liquidity_values.values())
                liquidity_distribution = statistics.stdev(liquidity_values) / statistics.mean(liquidity_values)
                distribution_factor = max(0.0, 1.0 - liquidity_distribution)
            else:
                distribution_factor = 0.5  # Single DEX is less sustainable

            # Combine factors
            combined_factor = (sustainability_factor + distribution_factor) / 2
            sustainability_factors.append(combined_factor)

        return statistics.mean(sustainability_factors) if sustainability_factors else 0.5

    async def get_optimal_lp_allocation(self, target_apy: float = 0.08,
                                      risk_tolerance: str = "medium") -> Dict[str, Any]:
        """
        Get optimal LP allocation strategy

        Args:
            target_apy: Target APY for the allocation
            risk_tolerance: Risk tolerance level ("low", "medium", "high")

        Returns:
            Dict containing optimal allocation strategy
        """
        try:
            # Get current yield data
            aggregated_yields = await self.calculate_all_pool_yields()

            # Filter opportunities by risk tolerance
            risk_thresholds = {
                'low': 0.3,
                'medium': 0.6,
                'high': 1.0
            }
            max_risk = risk_thresholds.get(risk_tolerance, 0.6)

            eligible_opportunities = [
                opp for opp in aggregated_yields.top_yield_opportunities
                if opp['risk_score'] <= max_risk and opp['total_apy'] >= target_apy * 0.5
            ]

            if not eligible_opportunities:
                return {"error": "No opportunities found matching criteria"}

            # Calculate optimal allocation
            allocation = self._calculate_optimal_allocation(eligible_opportunities, target_apy, max_risk)

            # Calculate expected metrics
            expected_apy = sum(
                alloc['weight'] * alloc['total_apy'] for alloc in allocation['allocations']
            )
            expected_il_risk = sum(
                alloc['weight'] * alloc['risk_score'] for alloc in allocation['allocations']
            )

            return {
                "target_apy": target_apy,
                "risk_tolerance": risk_tolerance,
                "expected_apy": expected_apy,
                "expected_il_risk": expected_il_risk,
                "allocations": allocation['allocations'],
                "diversification_score": allocation['diversification_score'],
                "total_opportunities_considered": len(eligible_opportunities),
                "allocation_strategy": "risk_adjusted_yield_optimization",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error calculating optimal LP allocation: {e}")
            return {"error": str(e)}

    def _calculate_optimal_allocation(self, opportunities: List[Dict[str, Any]],
                                    target_apy: float, max_risk: float) -> Dict[str, Any]:
        """Calculate optimal allocation weights for given opportunities"""
        # Sort opportunities by risk-adjusted yield
        risk_adjusted_opportunities = []
        for opp in opportunities:
            risk_adjusted_yield = opp['total_apy'] * (1 - opp['risk_score'] * 0.5)
            risk_adjusted_opportunities.append({
                **opp,
                'risk_adjusted_yield': risk_adjusted_yield
            })

        risk_adjusted_opportunities.sort(key=lambda x: x['risk_adjusted_yield'], reverse=True)

        # Simple allocation strategy: weight by risk-adjusted yield
        total_risk_adjusted_yield = sum(opp['risk_adjusted_yield'] for opp in risk_adjusted_opportunities[:10])

        allocations = []
        for opp in risk_adjusted_opportunities[:10]:  # Top 10 opportunities
            weight = opp['risk_adjusted_yield'] / total_risk_adjusted_yield
            allocations.append({
                'pair': opp['pair'],
                'dex': opp['dex'],
                'weight': weight,
                'total_apy': opp['total_apy'],
                'risk_score': opp['risk_score'],
                'liquidity_usd': opp['liquidity_usd']
            })

        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(allocations)

        return {
            'allocations': allocations,
            'diversification_score': diversification_score
        }

    def _calculate_diversification_score(self, allocations: List[Dict[str, Any]]) -> float:
        """Calculate diversification score for an allocation"""
        if not allocations:
            return 0.0

        # Factor 1: Number of positions
        position_factor = min(len(allocations) / 5.0, 1.0)  # Max at 5 positions

        # Factor 2: Weight distribution
        weights = [alloc['weight'] for alloc in allocations]
        max_weight = max(weights)
        concentration_factor = 1.0 - max_weight  # Lower when one position dominates

        # Factor 3: DEX diversification
        dexes = set(alloc['dex'] for alloc in allocations)
        dex_factor = min(len(dexes) / 3.0, 1.0)  # Max at 3 DEXes

        # Factor 4: Asset diversification
        pairs = set(alloc['pair'] for alloc in allocations)
        pair_factor = min(len(pairs) / 4.0, 1.0)  # Max at 4 pairs

        # Combine factors
        diversification_score = (position_factor + concentration_factor + dex_factor + pair_factor) / 4

        return diversification_score

    async def project_yields(self, days: int = 30) -> List[YieldProjection]:
        """
        Project yields for the next specified number of days

        Args:
            days: Number of days to project

        Returns:
            List of yield projections
        """
        try:
            # Get current yield data
            aggregated_yields = await self.calculate_all_pool_yields()

            projections = []
            for summary in aggregated_yields.pool_summaries:
                for dex, current_yield in summary.dex_yields.items():
                    # Simple projection model (in practice, would use more sophisticated forecasting)
                    projection = self._create_yield_projection(
                        summary.asset_pair, dex, current_yield, days
                    )
                    projections.append(projection)

            return projections

        except Exception as e:
            self.logger.error(f"Error projecting yields: {e}")
            return []

    def _create_yield_projection(self, pair: str, dex: str, current_yield: float, days: int) -> YieldProjection:
        """Create yield projection for a specific pool"""
        # Simple projection model with some randomness
        base_volatility = 0.1  # 10% base volatility

        # Adjust volatility based on asset pair
        if 'goBTC' in pair or 'goETH' in pair:
            volatility = base_volatility * 1.5
        elif 'USDC/USDT' in pair:
            volatility = base_volatility * 0.3
        else:
            volatility = base_volatility

        # Project yields with decreasing confidence over time
        projected_7d = current_yield * (1 + (0.02 - 0.04 * (days > 7)))  # Small trend adjustment
        projected_30d = current_yield * (1 + (0.01 - 0.03 * (days > 30)))
        projected_90d = current_yield * (1 + (0.005 - 0.02 * (days > 90)))

        # Calculate confidence intervals
        confidence_intervals = {
            '68%': (projected_30d * (1 - volatility), projected_30d * (1 + volatility)),
            '95%': (projected_30d * (1 - 2 * volatility), projected_30d * (1 + 2 * volatility))
        }

        # Identify risk factors
        risk_factors = []
        if current_yield > 0.5:  # > 50% APY
            risk_factors.append("High yield sustainability risk")
        if 'goBTC' in pair:
            risk_factors.append("High impermanent loss risk")
        if volatility > 0.15:
            risk_factors.append("High yield volatility")

        # Estimate impermanent loss
        pair_config = self.config.get('asset_pairs', {}).get(pair, {})
        il_factor = pair_config.get('il_risk_factor', 0.7)
        impermanent_loss_estimate = current_yield * (1 - il_factor) * 0.5  # Simplified IL estimate

        # Net yield after IL
        net_yield = max(0, projected_30d - impermanent_loss_estimate)

        return YieldProjection(
            pool_pair=pair,
            dex_name=dex,
            projected_7d_yield=projected_7d,
            projected_30d_yield=projected_30d,
            projected_90d_yield=projected_90d,
            confidence_intervals=confidence_intervals,
            risk_factors=risk_factors,
            impermanent_loss_estimate=impermanent_loss_estimate,
            net_yield_after_il=net_yield
        )

    def _get_fallback_aggregated_yields(self) -> AggregatedPoolYields:
        """Return fallback aggregated yields when calculation fails"""
        fallback_summary = PoolYieldSummary(
            asset_pair='ALGO/USDC',
            dex_yields={'Tinyman': 0.04, 'Algofi': 0.06},
            trading_fee_yields={'Tinyman': 0.025, 'Algofi': 0.022},
            reward_yields={'Tinyman': 0.015, 'Algofi': 0.038},
            liquidity_values={'Tinyman': 2000000, 'Algofi': 3000000},
            volume_24h_values={'Tinyman': 120000, 'Algofi': 200000},
            best_yield_dex='Algofi',
            worst_yield_dex='Tinyman',
            yield_spread=0.02,
            weighted_average_yield=0.052,
            confidence_score=0.5
        )

        return AggregatedPoolYields(
            pool_summaries=[fallback_summary],
            overall_weighted_yield=0.052,
            total_tvl_across_dexes=5000000,
            total_volume_24h=320000,
            dex_market_shares={'Tinyman': 0.4, 'Algofi': 0.6},
            top_yield_opportunities=[{
                'pair': 'ALGO/USDC',
                'dex': 'Algofi',
                'total_apy': 0.06,
                'liquidity_usd': 3000000,
                'risk_score': 0.3
            }],
            average_il_risk=0.7,
            sustainability_score=0.6,
            timestamp=datetime.now(),
            metadata={'fallback': True}
        )

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False

        timestamp_key = f"{key}_timestamp"
        if timestamp_key not in self.cache:
            return False

        cache_expiry = self.config.get('historical_data', {}).get('cache_expiry_minutes', 3)
        expiry_time = self.cache[timestamp_key] + timedelta(minutes=cache_expiry)

        return datetime.now() < expiry_time

# Example usage and testing
async def main():
    """Example usage of the PoolYieldCalculator"""
    calculator = PoolYieldCalculator()

    print("=== Pool Yield Calculator Demo ===")

    # Calculate all pool yields
    print("\n1. Aggregated Pool Yield Analysis:")
    aggregated = await calculator.calculate_all_pool_yields()
    print(f"   Overall Weighted Yield: {aggregated.overall_weighted_yield:.2%}")
    print(f"   Total TVL Across DEXes: ${aggregated.total_tvl_across_dexes:,.0f}")
    print(f"   Total 24h Volume: ${aggregated.total_volume_24h:,.0f}")
    print(f"   Average IL Risk: {aggregated.average_il_risk:.2%}")
    print(f"   Sustainability Score: {aggregated.sustainability_score:.2f}")

    # Show DEX market shares
    print(f"\n2. DEX Market Shares:")
    for dex, share in aggregated.dex_market_shares.items():
        print(f"   {dex}: {share:.1%}")

    # Show pool summaries
    print(f"\n3. Pool Yield Summaries ({len(aggregated.pool_summaries)} pairs):")
    for summary in aggregated.pool_summaries[:3]:  # Top 3
        print(f"   {summary.asset_pair}:")
        print(f"     Weighted Average Yield: {summary.weighted_average_yield:.2%}")
        print(f"     Best Yield: {summary.best_yield_dex} ({summary.dex_yields[summary.best_yield_dex]:.2%})")
        print(f"     Yield Spread: {summary.yield_spread:.2%}")
        print(f"     Total Liquidity: ${sum(summary.liquidity_values.values()):,.0f}")

    # Show top opportunities
    print(f"\n4. Top Yield Opportunities:")
    for i, opp in enumerate(aggregated.top_yield_opportunities[:5], 1):
        print(f"   {i}. {opp['pair']} on {opp['dex']}:")
        print(f"      Total APY: {opp['total_apy']:.2%}")
        print(f"      Trading Fee APY: {opp['trading_fee_apy']:.2%}")
        print(f"      Reward APY: {opp['reward_apy']:.2%}")
        print(f"      Liquidity: ${opp['liquidity_usd']:,.0f}")
        print(f"      Risk Score: {opp['risk_score']:.2f}")

    # Get optimal allocation
    print(f"\n5. Optimal LP Allocation (8% target, medium risk):")
    allocation = await calculator.get_optimal_lp_allocation(0.08, "medium")
    if "error" not in allocation:
        print(f"   Expected APY: {allocation['expected_apy']:.2%}")
        print(f"   Expected IL Risk: {allocation['expected_il_risk']:.2f}")
        print(f"   Diversification Score: {allocation['diversification_score']:.2f}")
        print(f"   Top Allocations:")
        for alloc in allocation['allocations'][:3]:
            print(f"     {alloc['pair']} on {alloc['dex']}: {alloc['weight']:.1%} ({alloc['total_apy']:.2%} APY)")

    # Yield projections
    print(f"\n6. Yield Projections (30 days):")
    projections = await calculator.project_yields(30)
    for proj in projections[:3]:  # Top 3
        print(f"   {proj.pool_pair} on {proj.dex_name}:")
        print(f"     30-day Projected: {proj.projected_30d_yield:.2%}")
        print(f"     Net After IL: {proj.net_yield_after_il:.2%}")
        print(f"     Risk Factors: {len(proj.risk_factors)}")

if __name__ == "__main__":
    asyncio.run(main())