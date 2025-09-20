"""
Tinyman DEX client for liquidity pool analysis and swap rate data.

Provides integration with Tinyman DEX including:
- Liquidity pool metrics and yields
- Swap rates and price impact
- LP token rewards and farming
- Pool health and risk assessment
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
import logging

from ..models.defi_models import LiquidityPool, PoolType, DeFiYield

logger = logging.getLogger(__name__)


@dataclass
class TinymanPools:
    """Tinyman pool data and metrics"""
    timestamp: datetime

    # Pool information
    pools: List[LiquidityPool] = field(default_factory=list)
    total_tvl: Decimal = Decimal('0')
    total_volume_24h: Decimal = Decimal('0')
    total_fees_24h: Decimal = Decimal('0')

    # Top pools by TVL
    top_pools_by_tvl: List[str] = field(default_factory=list)

    # Price data
    algo_price_usd: Decimal = Decimal('0')
    asset_prices: Dict[int, Decimal] = field(default_factory=dict)  # asset_id -> price_usd

    def get_pool_by_assets(self, asset_a: int, asset_b: int) -> Optional[LiquidityPool]:
        """Get pool by asset pair (order independent)"""
        for pool in self.pools:
            if {pool.asset_a, pool.asset_b} == {asset_a, asset_b}:
                return pool
        return None

    def get_pools_with_asset(self, asset_id: int) -> List[LiquidityPool]:
        """Get all pools containing a specific asset"""
        return [pool for pool in self.pools if asset_id in {pool.asset_a, pool.asset_b}]

    @property
    def average_fee_apy(self) -> Decimal:
        """Calculate average fee APY across all pools"""
        if not self.pools:
            return Decimal('0')

        total_weighted_apy = Decimal('0')
        total_tvl = Decimal('0')

        for pool in self.pools:
            if pool.total_liquidity_usd > 0:
                total_weighted_apy += pool.base_apy * pool.total_liquidity_usd
                total_tvl += pool.total_liquidity_usd

        return total_weighted_apy / total_tvl if total_tvl > 0 else Decimal('0')


class TinymanClient:
    """
    Tinyman DEX client for liquidity analysis and yield opportunities.

    Provides comprehensive data on liquidity pools, trading volumes,
    yields, and market-making opportunities on Tinyman.
    """

    def __init__(self, algorand_client=None):
        self.algorand_client = algorand_client
        self._cache: Dict[str, Any] = {}
        self._cache_timeout = 300  # 5 minutes

        # Tinyman protocol configuration
        self.protocol_config = {
            'name': 'Tinyman',
            'type': 'dex',
            'validator_app_id': 552635992,  # Tinyman v1.1 validator
            'fee_rate': Decimal('0.003'),   # 0.3% trading fee
            'supported_pool_types': [PoolType.CONSTANT_PRODUCT],
            'major_assets': {
                0: 'ALGO',
                31566704: 'USDC',
                312769: 'USDT',
                287867876: 'OPUL',
                226701642: 'goBTC',
                386192725: 'goETH'
            }
        }

    async def connect(self) -> bool:
        """Initialize connection to Tinyman"""
        try:
            status = await self.get_protocol_status()
            logger.info(f"Connected to Tinyman DEX - TVL: ${status.get('tvl', 0):,.2f}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Tinyman: {e}")
            return False

    async def get_all_pools(self) -> TinymanPools:
        """
        Get data for all active Tinyman pools.

        Returns comprehensive pool data including liquidity,
        volume, fees, and yield opportunities.
        """
        cache_key = "all_pools"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_timeout:
                return cached_data

        try:
            # Fetch pool data from Tinyman
            pools_data = await self._fetch_pools_data()
            asset_prices = await self._fetch_asset_prices()

            pools = []
            total_tvl = Decimal('0')
            total_volume_24h = Decimal('0')
            total_fees_24h = Decimal('0')

            for pool_data in pools_data:
                pool = self._create_pool_from_data(pool_data, asset_prices)
                pools.append(pool)

                total_tvl += pool.total_liquidity_usd
                total_volume_24h += pool.volume_24h_usd
                total_fees_24h += pool.fee_revenue_24h

            # Sort pools by TVL for ranking
            pools.sort(key=lambda p: p.total_liquidity_usd, reverse=True)
            top_pools = [pool.pool_id for pool in pools[:10]]

            tinyman_pools = TinymanPools(
                timestamp=datetime.now(),
                pools=pools,
                total_tvl=total_tvl,
                total_volume_24h=total_volume_24h,
                total_fees_24h=total_fees_24h,
                top_pools_by_tvl=top_pools,
                algo_price_usd=asset_prices.get(0, Decimal('0.15')),  # Default ALGO price
                asset_prices=asset_prices
            )

            self._cache[cache_key] = (tinyman_pools, datetime.now())
            return tinyman_pools

        except Exception as e:
            logger.error(f"Error fetching Tinyman pools: {e}")
            raise

    async def get_pool_data(self, asset_a: int, asset_b: int) -> Optional[LiquidityPool]:
        """Get data for a specific pool by asset pair"""
        try:
            pools = await self.get_all_pools()
            return pools.get_pool_by_assets(asset_a, asset_b)
        except Exception as e:
            logger.error(f"Error getting pool data for {asset_a}/{asset_b}: {e}")
            raise

    async def get_swap_quote(
        self,
        asset_in: int,
        asset_out: int,
        amount_in: Decimal
    ) -> Dict[str, Any]:
        """
        Get swap quote including price impact and fees.

        Returns detailed swap information including expected output,
        price impact, and minimum received.
        """
        try:
            pool = await self.get_pool_data(asset_in, asset_out)
            if not pool:
                raise ValueError(f"No pool found for {asset_in}/{asset_out}")

            # Calculate swap using constant product formula
            if asset_in == pool.asset_a:
                reserve_in = pool.reserve_a
                reserve_out = pool.reserve_b
            else:
                reserve_in = pool.reserve_b
                reserve_out = pool.reserve_a

            # Apply trading fee
            amount_in_with_fee = amount_in * (Decimal('1') - self.protocol_config['fee_rate'])

            # Constant product: x * y = k
            # amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
            amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)

            # Calculate price impact
            spot_price = reserve_out / reserve_in
            effective_price = amount_out / amount_in
            price_impact = abs(spot_price - effective_price) / spot_price

            # Calculate minimum received (with 0.5% slippage tolerance)
            slippage_tolerance = Decimal('0.005')
            minimum_received = amount_out * (Decimal('1') - slippage_tolerance)

            return {
                'amount_in': amount_in,
                'amount_out': amount_out,
                'minimum_received': minimum_received,
                'price_impact': float(price_impact),
                'effective_price': effective_price,
                'spot_price': spot_price,
                'trading_fee': amount_in * self.protocol_config['fee_rate'],
                'pool_id': pool.pool_id,
                'liquidity': pool.total_liquidity_usd
            }

        except Exception as e:
            logger.error(f"Error calculating swap quote: {e}")
            raise

    async def get_liquidity_mining_opportunities(self) -> List[DeFiYield]:
        """
        Get liquidity mining opportunities with yield calculations.

        Returns LP opportunities with APY from trading fees
        and potential reward token incentives.
        """
        try:
            pools = await self.get_all_pools()
            opportunities = []

            # Focus on high-volume, stable pools
            for pool in pools.pools:
                if pool.total_liquidity_usd < Decimal('50000'):  # Minimum $50k TVL
                    continue

                # Calculate annualized fee yield
                if pool.total_liquidity_usd > 0:
                    daily_fee_yield = pool.fee_revenue_24h / pool.total_liquidity_usd
                    annual_fee_yield = daily_fee_yield * Decimal('365')
                else:
                    annual_fee_yield = Decimal('0')

                # Assess risk level based on assets
                risk_level = self._assess_pool_risk(pool)

                # Get asset names for strategy name
                asset_a_name = self.protocol_config['major_assets'].get(pool.asset_a, f"ASA-{pool.asset_a}")
                asset_b_name = self.protocol_config['major_assets'].get(pool.asset_b, f"ASA-{pool.asset_b}")

                yield_opp = DeFiYield(
                    protocol="Tinyman",
                    strategy_name=f"{asset_a_name}/{asset_b_name} LP",
                    asset_id=pool.asset_a,  # Primary asset
                    current_apy=annual_fee_yield,
                    strategy_risk_level=risk_level,
                    smart_contract_risk=0.15,  # Tinyman is well-established
                    liquidity_risk=0.3,       # LP tokens have IL risk
                    min_deposit_amount=Decimal('10'),  # $10 minimum
                    compounding_frequency="continuous",  # Fees compound continuously
                    total_value_locked=pool.total_liquidity_usd
                )

                opportunities.append(yield_opp)

            # Sort by risk-adjusted yield
            opportunities.sort(key=lambda x: x.risk_adjusted_yield, reverse=True)
            return opportunities[:10]  # Top 10 opportunities

        except Exception as e:
            logger.error(f"Error getting liquidity mining opportunities: {e}")
            raise

    async def calculate_impermanent_loss(
        self,
        asset_a: int,
        asset_b: int,
        price_change_a: Decimal,
        price_change_b: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate impermanent loss for a pool given price changes.

        Args:
            asset_a: First asset ID
            asset_b: Second asset ID
            price_change_a: Price change ratio for asset A (1.0 = no change)
            price_change_b: Price change ratio for asset B (1.0 = no change)
        """
        try:
            # Impermanent loss formula for constant product pools
            # IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
            price_ratio = price_change_a / price_change_b

            sqrt_ratio = price_ratio ** Decimal('0.5')
            il_multiplier = (2 * sqrt_ratio) / (1 + price_ratio)
            impermanent_loss = il_multiplier - 1

            # Calculate breakeven fee yield needed to offset IL
            pool = await self.get_pool_data(asset_a, asset_b)
            current_fee_apy = pool.base_apy if pool else Decimal('0')

            return {
                'impermanent_loss_pct': abs(impermanent_loss) * 100,
                'current_fee_apy': current_fee_apy * 100,
                'net_yield': (current_fee_apy + impermanent_loss) * 100,
                'breakeven_fee_apy': abs(impermanent_loss) * 100,
                'is_profitable': current_fee_apy > abs(impermanent_loss)
            }

        except Exception as e:
            logger.error(f"Error calculating impermanent loss: {e}")
            raise

    async def get_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify potential arbitrage opportunities across pools.

        Returns price discrepancies that could be profitable
        after accounting for fees and slippage.
        """
        try:
            pools = await self.get_all_pools()
            opportunities = []

            # Look for triangular arbitrage opportunities
            # Example: ALGO -> USDC -> OTHER -> ALGO
            algo_pools = pools.get_pools_with_asset(0)  # ALGO pools

            for usdc_pool in algo_pools:
                if usdc_pool.asset_a == 31566704 or usdc_pool.asset_b == 31566704:  # USDC
                    # Found ALGO/USDC pool, look for other assets with both USDC and ALGO pools
                    other_asset = usdc_pool.asset_a if usdc_pool.asset_b == 31566704 else usdc_pool.asset_b

                    if other_asset != 0:  # Not ALGO
                        other_algo_pool = pools.get_pool_by_assets(0, other_asset)
                        other_usdc_pool = pools.get_pool_by_assets(31566704, other_asset)

                        if other_algo_pool and other_usdc_pool:
                            # Calculate potential arbitrage
                            arbitrage = await self._calculate_arbitrage(
                                usdc_pool, other_algo_pool, other_usdc_pool
                            )

                            if arbitrage['profit_pct'] > 0.5:  # >0.5% profit threshold
                                opportunities.append(arbitrage)

            return sorted(opportunities, key=lambda x: x['profit_pct'], reverse=True)

        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {e}")
            raise

    async def get_protocol_status(self) -> Dict[str, Any]:
        """Get overall Tinyman protocol status and metrics"""
        try:
            pools = await self.get_all_pools()

            return {
                'tvl': float(pools.total_tvl),
                'volume_24h': float(pools.total_volume_24h),
                'fees_24h': float(pools.total_fees_24h),
                'total_pools': len(pools.pools),
                'active_pools': len([p for p in pools.pools if p.is_active]),
                'average_fee_apy': float(pools.average_fee_apy),
                'protocol_age_days': 500,  # Tinyman has been around
                'last_update': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting protocol status: {e}")
            raise

    async def _fetch_pools_data(self) -> List[Dict[str, Any]]:
        """Fetch pool data from Tinyman smart contracts"""
        # Mock implementation - would query actual pool data
        return [
            {
                'asset_a': 0,         # ALGO
                'asset_b': 31566704,  # USDC
                'reserve_a': Decimal('1000000'),    # 1M ALGO
                'reserve_b': Decimal('150000'),     # $150k USDC
                'lp_token_supply': Decimal('387298'), # LP tokens
                'volume_24h': Decimal('50000'),     # $50k volume
                'trades_24h': 150,
                'fees_24h': Decimal('150')          # $150 fees
            },
            {
                'asset_a': 0,         # ALGO
                'asset_b': 312769,    # USDT
                'reserve_a': Decimal('800000'),     # 800k ALGO
                'reserve_b': Decimal('120000'),     # $120k USDT
                'lp_token_supply': Decimal('309838'),
                'volume_24h': Decimal('35000'),
                'trades_24h': 120,
                'fees_24h': Decimal('105')
            },
            {
                'asset_a': 31566704,  # USDC
                'asset_b': 312769,    # USDT
                'reserve_a': Decimal('100000'),     # $100k USDC
                'reserve_b': Decimal('100000'),     # $100k USDT
                'lp_token_supply': Decimal('100000'),
                'volume_24h': Decimal('20000'),
                'trades_24h': 80,
                'fees_24h': Decimal('60')
            }
        ]

    async def _fetch_asset_prices(self) -> Dict[int, Decimal]:
        """Fetch current asset prices"""
        # Mock implementation
        return {
            0: Decimal('0.15'),        # ALGO = $0.15
            31566704: Decimal('1.0'),  # USDC = $1.00
            312769: Decimal('1.0'),    # USDT = $1.00
            287867876: Decimal('0.05'), # OPUL = $0.05
        }

    def _create_pool_from_data(self, pool_data: Dict[str, Any], prices: Dict[int, Decimal]) -> LiquidityPool:
        """Create LiquidityPool object from raw data"""
        asset_a = pool_data['asset_a']
        asset_b = pool_data['asset_b']

        # Calculate USD values
        price_a = prices.get(asset_a, Decimal('0'))
        price_b = prices.get(asset_b, Decimal('0'))

        liquidity_usd = (
            pool_data['reserve_a'] * price_a +
            pool_data['reserve_b'] * price_b
        )

        # Calculate APY from fees
        if liquidity_usd > 0:
            daily_yield = pool_data['fees_24h'] / liquidity_usd
            annual_yield = daily_yield * Decimal('365')
        else:
            annual_yield = Decimal('0')

        return LiquidityPool(
            pool_id=f"{asset_a}-{asset_b}",
            protocol="Tinyman",
            app_id=self.protocol_config['validator_app_id'],
            pool_type=PoolType.CONSTANT_PRODUCT,
            asset_a=asset_a,
            asset_b=asset_b,
            reserve_a=pool_data['reserve_a'],
            reserve_b=pool_data['reserve_b'],
            total_liquidity_usd=liquidity_usd,
            lp_token_supply=pool_data['lp_token_supply'],
            volume_24h_usd=pool_data['volume_24h'],
            trades_24h=pool_data['trades_24h'],
            fee_revenue_24h=pool_data['fees_24h'],
            base_apy=annual_yield,
            total_apy=annual_yield,  # No additional rewards on Tinyman
            is_active=True,
            created_timestamp=datetime.now()  # Mock timestamp
        )

    def _assess_pool_risk(self, pool: LiquidityPool) -> str:
        """Assess risk level for a liquidity pool"""
        # Check if both assets are major/stable
        major_assets = {0, 31566704, 312769}  # ALGO, USDC, USDT

        if pool.asset_a in major_assets and pool.asset_b in major_assets:
            return "low"
        elif pool.asset_a in major_assets or pool.asset_b in major_assets:
            return "medium"
        else:
            return "high"

    async def _calculate_arbitrage(
        self,
        pool1: LiquidityPool,
        pool2: LiquidityPool,
        pool3: LiquidityPool
    ) -> Dict[str, Any]:
        """Calculate triangular arbitrage opportunity"""
        # Simplified arbitrage calculation
        # In practice, would need to account for fees, slippage, and gas costs

        return {
            'type': 'triangular',
            'pools': [pool1.pool_id, pool2.pool_id, pool3.pool_id],
            'profit_pct': 0.8,  # Mock 0.8% profit
            'required_capital': Decimal('10000'),  # $10k required
            'execution_complexity': 'medium'
        }

    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()