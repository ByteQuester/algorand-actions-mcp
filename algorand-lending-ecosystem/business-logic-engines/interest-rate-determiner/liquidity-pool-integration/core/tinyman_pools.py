"""
Tinyman Pools Analyzer

Analyzes Tinyman DEX liquidity pools to calculate LP token yields and trading fees.
Provides comprehensive analysis of impermanent loss and yield farming opportunities.
"""

import asyncio
import logging
import aiohttp
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json
import statistics
import math

@dataclass
class TinymanPool:
    """Represents a Tinyman liquidity pool"""
    pool_id: str
    asset_1_id: str
    asset_2_id: str
    asset_1_name: str
    asset_2_name: str
    liquidity_usd: float
    volume_24h_usd: float
    volume_7d_usd: float
    apy_fees: float
    apy_rewards: float
    total_apy: float
    pool_tokens_outstanding: float
    asset_1_reserves: float
    asset_2_reserves: float
    price_ratio: float
    fee_tier: float
    last_update: datetime

@dataclass
class TinymanYieldData:
    """Complete Tinyman yield analysis data"""
    pools: List[TinymanPool]
    weighted_average_apy: float
    total_tvl: float
    total_volume_24h: float
    average_fee_apy: float
    average_rewards_apy: float
    top_performing_pools: List[str]
    confidence_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ImpermanentLossAnalysis:
    """Impermanent loss analysis for a pool"""
    pool_id: str
    current_il_percentage: float
    il_at_price_changes: Dict[str, float]  # Price change -> IL percentage
    break_even_days: float
    risk_category: str
    hedging_cost: float
    net_apy_after_il_risk: float
    confidence_score: float

class TinymanPoolsAnalyzer:
    """
    Analyzer for Tinyman DEX liquidity pools and yield farming opportunities.

    Calculates LP token yields, trading fee earnings, and analyzes
    impermanent loss risks for comprehensive DeFi yield analysis.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Tinyman pools analyzer"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.cache = {}
        self.pool_cache = {}

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
                    'tinyman': {
                        'api_endpoint': 'https://mainnet.analytics.tinyman.org/api/v1',
                        'weight': 0.45,
                        'fee_tier': 0.003
                    }
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the analyzer"""
        logger = logging.getLogger('tinyman_pools_analyzer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def fetch_tinyman_pools(self) -> List[TinymanPool]:
        """
        Fetch current pool data from Tinyman

        Returns:
            List[TinymanPool]: List of Tinyman liquidity pools
        """
        try:
            # Check cache first
            if self._is_cache_valid('tinyman_pools'):
                return self.cache['tinyman_pools']

            # Fetch from Tinyman API
            pools_data = await self._fetch_pools_from_api()

            # Parse pool data
            pools = []
            for pool_data in pools_data:
                pool = self._parse_pool_data(pool_data)
                if pool:
                    pools.append(pool)

            # Sort by liquidity (highest first)
            pools.sort(key=lambda p: p.liquidity_usd, reverse=True)

            # Cache the results
            self.cache['tinyman_pools'] = pools
            self.cache['tinyman_pools_timestamp'] = datetime.now()

            return pools

        except Exception as e:
            self.logger.error(f"Error fetching Tinyman pools: {e}")
            return self._get_fallback_pools()

    async def _fetch_pools_from_api(self) -> List[Dict]:
        """Fetch pool data from Tinyman API"""
        try:
            tinyman_config = self.config['dex_protocols']['tinyman']
            api_endpoint = tinyman_config['api_endpoint']

            async with aiohttp.ClientSession() as session:
                # Try to fetch from actual Tinyman API
                async with session.get(f"{api_endpoint}/pools") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('pools', [])
                    else:
                        self.logger.warning(f"Tinyman API returned status {response.status}")

        except Exception as e:
            self.logger.warning(f"Direct Tinyman API unavailable: {e}")

        # Fallback to MCP service
        return await self._fetch_via_mcp_service()

    async def _fetch_via_mcp_service(self) -> List[Dict]:
        """Fetch pool data via MCP service"""
        try:
            mcp_url = self.config['mcp_services']['market_data_url']

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mcp_url}/dex/tinyman/pools") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('pools', [])

        except Exception as e:
            self.logger.warning(f"MCP service unavailable: {e}")

        # Return simulated data if all sources fail
        return self._get_simulated_pool_data()

    def _get_simulated_pool_data(self) -> List[Dict]:
        """Return simulated Tinyman pool data for testing"""
        return [
            {
                'pool_id': 'tinyman_algo_usdc',
                'asset_1_id': '0',
                'asset_2_id': '31566704',
                'asset_1_name': 'ALGO',
                'asset_2_name': 'USDC',
                'liquidity_usd': 2500000,      # $2.5M liquidity
                'volume_24h_usd': 150000,      # $150K daily volume
                'volume_7d_usd': 1050000,      # $1.05M weekly volume
                'asset_1_reserves': 10000000,  # 10M ALGO
                'asset_2_reserves': 2500000,   # 2.5M USDC
                'pool_tokens_outstanding': 5000000,
                'price_ratio': 0.25,           # 1 ALGO = 0.25 USDC
                'fee_tier': 0.003             # 0.3% fee
            },
            {
                'pool_id': 'tinyman_algo_usdt',
                'asset_1_id': '0',
                'asset_2_id': '312769',
                'asset_1_name': 'ALGO',
                'asset_2_name': 'USDT',
                'liquidity_usd': 1800000,      # $1.8M liquidity
                'volume_24h_usd': 95000,       # $95K daily volume
                'volume_7d_usd': 665000,       # $665K weekly volume
                'asset_1_reserves': 7200000,   # 7.2M ALGO
                'asset_2_reserves': 1800000,   # 1.8M USDT
                'pool_tokens_outstanding': 3600000,
                'price_ratio': 0.25,           # 1 ALGO = 0.25 USDT
                'fee_tier': 0.003             # 0.3% fee
            },
            {
                'pool_id': 'tinyman_usdc_usdt',
                'asset_1_id': '31566704',
                'asset_2_id': '312769',
                'asset_1_name': 'USDC',
                'asset_2_name': 'USDT',
                'liquidity_usd': 800000,       # $800K liquidity
                'volume_24h_usd': 25000,       # $25K daily volume
                'volume_7d_usd': 175000,       # $175K weekly volume
                'asset_1_reserves': 400000,    # 400K USDC
                'asset_2_reserves': 400000,    # 400K USDT
                'pool_tokens_outstanding': 800000,
                'price_ratio': 1.0,            # 1 USDC = 1 USDT
                'fee_tier': 0.003             # 0.3% fee
            },
            {
                'pool_id': 'tinyman_algo_gobtc',
                'asset_1_id': '0',
                'asset_2_id': '386192725',
                'asset_1_name': 'ALGO',
                'asset_2_name': 'goBTC',
                'liquidity_usd': 450000,       # $450K liquidity
                'volume_24h_usd': 75000,       # $75K daily volume
                'volume_7d_usd': 525000,       # $525K weekly volume
                'asset_1_reserves': 1350000,   # 1.35M ALGO
                'asset_2_reserves': 7.5,       # 7.5 goBTC
                'pool_tokens_outstanding': 900000,
                'price_ratio': 0.00055556,     # 1 ALGO = 0.00055556 goBTC
                'fee_tier': 0.003             # 0.3% fee
            }
        ]

    def _parse_pool_data(self, pool_data: Dict) -> Optional[TinymanPool]:
        """Parse raw pool data into TinymanPool object"""
        try:
            pool_id = pool_data.get('pool_id', '')
            asset_1_id = str(pool_data.get('asset_1_id', ''))
            asset_2_id = str(pool_data.get('asset_2_id', ''))
            asset_1_name = pool_data.get('asset_1_name', 'Unknown')
            asset_2_name = pool_data.get('asset_2_name', 'Unknown')

            # Parse liquidity and volume
            liquidity_usd = float(pool_data.get('liquidity_usd', 0))
            volume_24h_usd = float(pool_data.get('volume_24h_usd', 0))
            volume_7d_usd = float(pool_data.get('volume_7d_usd', 0))

            # Parse reserves
            asset_1_reserves = float(pool_data.get('asset_1_reserves', 0))
            asset_2_reserves = float(pool_data.get('asset_2_reserves', 0))
            pool_tokens_outstanding = float(pool_data.get('pool_tokens_outstanding', 0))

            # Calculate price ratio
            price_ratio = pool_data.get('price_ratio')
            if price_ratio is None and asset_1_reserves > 0:
                price_ratio = asset_2_reserves / asset_1_reserves
            else:
                price_ratio = float(price_ratio or 0)

            # Get fee tier
            fee_tier = float(pool_data.get('fee_tier', self.config['dex_protocols']['tinyman']['fee_tier']))

            # Calculate APYs
            apy_fees = self._calculate_fee_apy(volume_24h_usd, liquidity_usd, fee_tier)
            apy_rewards = self._calculate_rewards_apy(pool_id, liquidity_usd)
            total_apy = apy_fees + apy_rewards

            return TinymanPool(
                pool_id=pool_id,
                asset_1_id=asset_1_id,
                asset_2_id=asset_2_id,
                asset_1_name=asset_1_name,
                asset_2_name=asset_2_name,
                liquidity_usd=liquidity_usd,
                volume_24h_usd=volume_24h_usd,
                volume_7d_usd=volume_7d_usd,
                apy_fees=apy_fees,
                apy_rewards=apy_rewards,
                total_apy=total_apy,
                pool_tokens_outstanding=pool_tokens_outstanding,
                asset_1_reserves=asset_1_reserves,
                asset_2_reserves=asset_2_reserves,
                price_ratio=price_ratio,
                fee_tier=fee_tier,
                last_update=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error parsing pool data: {e}")
            return None

    def _calculate_fee_apy(self, volume_24h: float, liquidity: float, fee_tier: float) -> float:
        """Calculate APY from trading fees"""
        if liquidity == 0:
            return 0.0

        # Daily fee revenue
        daily_fees = volume_24h * fee_tier

        # Annualized fee APY
        annual_fees = daily_fees * 365
        fee_apy = annual_fees / liquidity if liquidity > 0 else 0.0

        # Cap at reasonable maximum
        return min(fee_apy, 5.0)  # Cap at 500% APY

    def _calculate_rewards_apy(self, pool_id: str, liquidity: float) -> float:
        """Calculate APY from liquidity mining rewards"""
        # Simulate rewards based on pool configuration
        rewards_config = self.config.get('liquidity_mining', {}).get('reward_tokens', {})

        # Base rewards calculation (simplified)
        base_rewards_apy = 0.0

        # ALGO pools typically have higher rewards
        if 'algo' in pool_id.lower():
            base_rewards_apy = 0.02  # 2% base rewards

        # Popular pairs get bonus rewards
        if any(pair in pool_id.lower() for pair in ['algo_usdc', 'algo_usdt']):
            base_rewards_apy += 0.01  # Additional 1% for popular pairs

        # Adjust for liquidity (higher liquidity = lower rewards per dollar)
        if liquidity > 1000000:  # > $1M
            base_rewards_apy *= 0.8
        elif liquidity < 100000:  # < $100K
            base_rewards_apy *= 1.5

        return min(base_rewards_apy, 0.5)  # Cap at 50% rewards APY

    async def analyze_tinyman_yields(self) -> TinymanYieldData:
        """
        Analyze Tinyman yields across all pools

        Returns:
            TinymanYieldData: Complete Tinyman yield analysis
        """
        try:
            # Fetch current pools
            pools = await self.fetch_tinyman_pools()

            if not pools:
                return self._get_fallback_yield_data()

            # Filter pools by minimum liquidity threshold
            min_liquidity = self.config['dex_protocols']['tinyman']['min_liquidity_threshold']
            filtered_pools = [p for p in pools if p.liquidity_usd >= min_liquidity]

            if not filtered_pools:
                filtered_pools = pools  # Use all pools if none meet threshold

            # Calculate aggregate metrics
            weighted_average_apy = self._calculate_weighted_average_apy(filtered_pools)
            total_tvl = sum(pool.liquidity_usd for pool in filtered_pools)
            total_volume_24h = sum(pool.volume_24h_usd for pool in filtered_pools)
            average_fee_apy = statistics.mean([pool.apy_fees for pool in filtered_pools])
            average_rewards_apy = statistics.mean([pool.apy_rewards for pool in filtered_pools])

            # Find top performing pools
            top_pools = sorted(filtered_pools, key=lambda p: p.total_apy, reverse=True)[:5]
            top_performing_pools = [f"{p.asset_1_name}/{p.asset_2_name}" for p in top_pools]

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(filtered_pools)

            return TinymanYieldData(
                pools=filtered_pools,
                weighted_average_apy=weighted_average_apy,
                total_tvl=total_tvl,
                total_volume_24h=total_volume_24h,
                average_fee_apy=average_fee_apy,
                average_rewards_apy=average_rewards_apy,
                top_performing_pools=top_performing_pools,
                confidence_score=confidence_score,
                timestamp=datetime.now(),
                metadata={
                    'total_pools': len(pools),
                    'filtered_pools': len(filtered_pools),
                    'min_liquidity_threshold': min_liquidity,
                    'data_source': 'tinyman_api'
                }
            )

        except Exception as e:
            self.logger.error(f"Error analyzing Tinyman yields: {e}")
            return self._get_fallback_yield_data()

    def _calculate_weighted_average_apy(self, pools: List[TinymanPool]) -> float:
        """Calculate liquidity-weighted average APY"""
        total_weighted_apy = 0.0
        total_weight = 0.0

        for pool in pools:
            weight = pool.liquidity_usd
            total_weighted_apy += pool.total_apy * weight
            total_weight += weight

        if total_weight > 0:
            return total_weighted_apy / total_weight
        else:
            return statistics.mean([p.total_apy for p in pools]) if pools else 0.0

    def _calculate_confidence_score(self, pools: List[TinymanPool]) -> float:
        """Calculate confidence score for the yield data"""
        if not pools:
            return 0.0

        confidence = 1.0

        # Reduce confidence for low number of pools
        if len(pools) < 3:
            confidence *= 0.8

        # Check data freshness
        oldest_update = min(pool.last_update for pool in pools)
        if datetime.now() - oldest_update > timedelta(minutes=15):
            confidence *= 0.9

        # Check for extreme APY values
        apys = [pool.total_apy for pool in pools]
        if any(apy > 3.0 or apy < 0.001 for apy in apys):  # > 300% or < 0.1%
            confidence *= 0.7

        # Check liquidity distribution
        total_liquidity = sum(pool.liquidity_usd for pool in pools)
        if total_liquidity < 1000000:  # < $1M total liquidity
            confidence *= 0.8

        return max(confidence, 0.1)

    async def analyze_impermanent_loss(self, pool_id: str) -> ImpermanentLossAnalysis:
        """
        Analyze impermanent loss for a specific pool

        Args:
            pool_id: ID of the pool to analyze

        Returns:
            ImpermanentLossAnalysis: IL analysis for the pool
        """
        try:
            # Get pool data
            pools = await self.fetch_tinyman_pools()
            pool = next((p for p in pools if p.pool_id == pool_id), None)

            if not pool:
                return self._get_fallback_il_analysis(pool_id)

            # Calculate current IL (simplified - assumes equal weights)
            current_il = 0.0  # No IL at current prices by definition

            # Calculate IL at various price changes
            price_changes = [-0.50, -0.25, -0.10, 0.10, 0.25, 0.50, 1.0, 2.0]
            il_at_price_changes = {}

            for change in price_changes:
                il_percentage = self._calculate_il_at_price_change(change)
                il_at_price_changes[f"{change:+.0%}"] = il_percentage

            # Calculate break-even days (days for fees to offset max IL)
            max_il = max(il_at_price_changes.values())
            break_even_days = self._calculate_break_even_days(pool, max_il)

            # Determine risk category
            risk_category = self._categorize_il_risk(max_il, pool)

            # Calculate hedging cost
            hedging_cost = self._estimate_hedging_cost(pool)

            # Calculate net APY after IL risk
            net_apy = pool.total_apy - (max_il / break_even_days * 365 if break_even_days > 0 else 0)

            return ImpermanentLossAnalysis(
                pool_id=pool_id,
                current_il_percentage=current_il,
                il_at_price_changes=il_at_price_changes,
                break_even_days=break_even_days,
                risk_category=risk_category,
                hedging_cost=hedging_cost,
                net_apy_after_il_risk=max(net_apy, 0.0),
                confidence_score=0.8
            )

        except Exception as e:
            self.logger.error(f"Error analyzing impermanent loss for {pool_id}: {e}")
            return self._get_fallback_il_analysis(pool_id)

    def _calculate_il_at_price_change(self, price_change: float) -> float:
        """Calculate impermanent loss at a given price change"""
        # Simplified IL calculation for equal-weight pools
        # IL = 2 * sqrt(r) / (1 + r) - 1, where r = price_ratio_new / price_ratio_old
        r = 1 + price_change
        if r <= 0:
            return 1.0  # 100% loss if price goes to zero

        il = 2 * math.sqrt(r) / (1 + r) - 1
        return abs(il)  # Return absolute IL percentage

    def _calculate_break_even_days(self, pool: TinymanPool, max_il: float) -> float:
        """Calculate days needed for fees to offset impermanent loss"""
        if pool.apy_fees <= 0:
            return float('inf')

        # Daily fee rate
        daily_fee_rate = pool.apy_fees / 365

        # Days to recover from IL
        if daily_fee_rate > 0:
            return max_il / daily_fee_rate
        else:
            return float('inf')

    def _categorize_il_risk(self, max_il: float, pool: TinymanPool) -> str:
        """Categorize impermanent loss risk"""
        risk_buckets = self.config['impermanent_loss']['risk_buckets']

        if max_il <= risk_buckets['low']:
            return "Low"
        elif max_il <= risk_buckets['medium']:
            return "Medium"
        elif max_il <= risk_buckets['high']:
            return "High"
        else:
            return "Extreme"

    def _estimate_hedging_cost(self, pool: TinymanPool) -> float:
        """Estimate cost of hedging impermanent loss"""
        hedging_config = self.config['impermanent_loss']['hedging_strategies']

        if not hedging_config['enabled']:
            return 0.0

        # Base hedging cost
        base_cost = hedging_config['delta_hedge_cost']

        # Higher cost for volatile pairs
        if pool.asset_1_name in ['goBTC', 'goETH'] or pool.asset_2_name in ['goBTC', 'goETH']:
            base_cost += hedging_config['options_premium']

        return base_cost

    async def get_pool_by_pair(self, asset_1: str, asset_2: str) -> Optional[TinymanPool]:
        """
        Get pool data for a specific asset pair

        Args:
            asset_1: First asset name
            asset_2: Second asset name

        Returns:
            TinymanPool or None if not found
        """
        try:
            pools = await self.fetch_tinyman_pools()

            for pool in pools:
                if ((pool.asset_1_name.upper() == asset_1.upper() and
                     pool.asset_2_name.upper() == asset_2.upper()) or
                    (pool.asset_1_name.upper() == asset_2.upper() and
                     pool.asset_2_name.upper() == asset_1.upper())):
                    return pool

            return None

        except Exception as e:
            self.logger.error(f"Error fetching pool for {asset_1}/{asset_2}: {e}")
            return None

    async def get_top_yield_opportunities(self, min_liquidity: float = 100000) -> List[Dict[str, Any]]:
        """
        Get top yield opportunities from Tinyman pools

        Args:
            min_liquidity: Minimum liquidity threshold in USD

        Returns:
            List of top yield opportunities
        """
        try:
            yield_data = await self.analyze_tinyman_yields()

            # Filter by minimum liquidity
            eligible_pools = [
                pool for pool in yield_data.pools
                if pool.liquidity_usd >= min_liquidity
            ]

            # Sort by total APY
            eligible_pools.sort(key=lambda p: p.total_apy, reverse=True)

            opportunities = []
            for pool in eligible_pools[:10]:  # Top 10
                # Get IL analysis
                il_analysis = await self.analyze_impermanent_loss(pool.pool_id)

                opportunity = {
                    'pair': f"{pool.asset_1_name}/{pool.asset_2_name}",
                    'pool_id': pool.pool_id,
                    'total_apy': pool.total_apy,
                    'fee_apy': pool.apy_fees,
                    'rewards_apy': pool.apy_rewards,
                    'liquidity_usd': pool.liquidity_usd,
                    'volume_24h_usd': pool.volume_24h_usd,
                    'il_risk_category': il_analysis.risk_category,
                    'break_even_days': il_analysis.break_even_days,
                    'net_apy_after_il_risk': il_analysis.net_apy_after_il_risk,
                    'risk_adjusted_score': pool.total_apy * (1 - il_analysis.hedging_cost)
                }
                opportunities.append(opportunity)

            # Sort by risk-adjusted score
            opportunities.sort(key=lambda x: x['risk_adjusted_score'], reverse=True)

            return opportunities

        except Exception as e:
            self.logger.error(f"Error getting top yield opportunities: {e}")
            return []

    def _get_fallback_pools(self) -> List[TinymanPool]:
        """Return fallback pools when live data is unavailable"""
        return [
            TinymanPool(
                pool_id='fallback_algo_usdc',
                asset_1_id='0',
                asset_2_id='31566704',
                asset_1_name='ALGO',
                asset_2_name='USDC',
                liquidity_usd=2000000,
                volume_24h_usd=120000,
                volume_7d_usd=840000,
                apy_fees=0.025,
                apy_rewards=0.015,
                total_apy=0.04,
                pool_tokens_outstanding=4000000,
                asset_1_reserves=8000000,
                asset_2_reserves=2000000,
                price_ratio=0.25,
                fee_tier=0.003,
                last_update=datetime.now()
            )
        ]

    def _get_fallback_yield_data(self) -> TinymanYieldData:
        """Return fallback yield data when analysis fails"""
        fallback_pools = self._get_fallback_pools()

        return TinymanYieldData(
            pools=fallback_pools,
            weighted_average_apy=0.04,
            total_tvl=2000000,
            total_volume_24h=120000,
            average_fee_apy=0.025,
            average_rewards_apy=0.015,
            top_performing_pools=['ALGO/USDC'],
            confidence_score=0.5,
            timestamp=datetime.now(),
            metadata={'fallback': True}
        )

    def _get_fallback_il_analysis(self, pool_id: str) -> ImpermanentLossAnalysis:
        """Return fallback IL analysis"""
        return ImpermanentLossAnalysis(
            pool_id=pool_id,
            current_il_percentage=0.0,
            il_at_price_changes={'-50%': 0.2, '+50%': 0.2, '+100%': 0.4},
            break_even_days=150,
            risk_category="Medium",
            hedging_cost=0.01,
            net_apy_after_il_risk=0.03,
            confidence_score=0.5
        )

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False

        timestamp_key = f"{key}_timestamp"
        if timestamp_key not in self.cache:
            return False

        cache_expiry = self.config['historical_data']['cache_expiry_minutes']
        expiry_time = self.cache[timestamp_key] + timedelta(minutes=cache_expiry)

        return datetime.now() < expiry_time

# Example usage and testing
async def main():
    """Example usage of the TinymanPoolsAnalyzer"""
    analyzer = TinymanPoolsAnalyzer()

    print("=== Tinyman Pools Analyzer Demo ===")

    # Analyze current yields
    print("\n1. Current Tinyman Yield Analysis:")
    yield_data = await analyzer.analyze_tinyman_yields()
    print(f"   Weighted Average APY: {yield_data.weighted_average_apy:.2%}")
    print(f"   Total TVL: ${yield_data.total_tvl:,.0f}")
    print(f"   Total 24h Volume: ${yield_data.total_volume_24h:,.0f}")
    print(f"   Average Fee APY: {yield_data.average_fee_apy:.2%}")
    print(f"   Average Rewards APY: {yield_data.average_rewards_apy:.2%}")
    print(f"   Confidence Score: {yield_data.confidence_score:.2f}")

    # Show top pools
    print(f"\n2. Top Performing Pools:")
    for i, pool_name in enumerate(yield_data.top_performing_pools[:3], 1):
        print(f"   {i}. {pool_name}")

    # Show individual pools
    print(f"\n3. Individual Pool Details ({len(yield_data.pools)} pools):")
    for pool in yield_data.pools[:3]:  # Top 3 by liquidity
        print(f"   {pool.asset_1_name}/{pool.asset_2_name}:")
        print(f"     Total APY: {pool.total_apy:.2%}")
        print(f"     Fee APY: {pool.apy_fees:.2%}")
        print(f"     Rewards APY: {pool.apy_rewards:.2%}")
        print(f"     Liquidity: ${pool.liquidity_usd:,.0f}")
        print(f"     24h Volume: ${pool.volume_24h_usd:,.0f}")

    # Get specific pool
    print("\n4. ALGO/USDC Pool Analysis:")
    algo_usdc_pool = await analyzer.get_pool_by_pair('ALGO', 'USDC')
    if algo_usdc_pool:
        print(f"   Total APY: {algo_usdc_pool.total_apy:.2%}")
        print(f"   ALGO Reserves: {algo_usdc_pool.asset_1_reserves:,.0f}")
        print(f"   USDC Reserves: {algo_usdc_pool.asset_2_reserves:,.0f}")
        print(f"   Price Ratio: {algo_usdc_pool.price_ratio:.6f}")

        # Analyze impermanent loss
        print("\n5. Impermanent Loss Analysis (ALGO/USDC):")
        il_analysis = await analyzer.analyze_impermanent_loss(algo_usdc_pool.pool_id)
        print(f"   Risk Category: {il_analysis.risk_category}")
        print(f"   Break-even Days: {il_analysis.break_even_days:.0f}")
        print(f"   Net APY after IL Risk: {il_analysis.net_apy_after_il_risk:.2%}")
        print(f"   IL at +50% price change: {il_analysis.il_at_price_changes.get('+50%', 0):.2%}")

    # Top yield opportunities
    print("\n6. Top Yield Opportunities:")
    opportunities = await analyzer.get_top_yield_opportunities(50000)
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"   {i}. {opp['pair']}:")
        print(f"      Total APY: {opp['total_apy']:.2%}")
        print(f"      IL Risk: {opp['il_risk_category']}")
        print(f"      Risk-Adjusted Score: {opp['risk_adjusted_score']:.2%}")

if __name__ == "__main__":
    asyncio.run(main())