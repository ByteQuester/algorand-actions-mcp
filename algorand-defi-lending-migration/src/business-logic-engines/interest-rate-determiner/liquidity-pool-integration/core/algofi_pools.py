"""
Algofi Pools Analyzer

Analyzes Algofi DEX liquidity pools for LP yields and liquidity mining rewards.
Provides comprehensive analysis of AMM pools and yield farming opportunities.
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
class AlgofiPool:
    """Represents an Algofi DEX liquidity pool"""
    pool_id: str
    asset_1_id: str
    asset_2_id: str
    asset_1_name: str
    asset_2_name: str
    liquidity_usd: float
    volume_24h_usd: float
    volume_7d_usd: float
    apy_trading_fees: float
    apy_liquidity_mining: float
    apy_alfi_rewards: float
    total_apy: float
    pool_tokens_outstanding: float
    asset_1_reserves: float
    asset_2_reserves: float
    price_ratio: float
    fee_tier: float
    multiplier_boost: float
    last_update: datetime

@dataclass
class AlgofiPoolData:
    """Complete Algofi pool analysis data"""
    pools: List[AlgofiPool]
    weighted_average_apy: float
    total_tvl: float
    total_volume_24h: float
    average_trading_apy: float
    average_mining_apy: float
    average_alfi_rewards: float
    total_alfi_emissions: float
    confidence_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class LiquidityMiningData:
    """Liquidity mining rewards data"""
    pool_id: str
    alfi_emission_rate: float
    alfi_price_usd: float
    multiplier: float
    lock_period_days: int
    vesting_schedule: str
    effective_apy: float
    risk_adjusted_apy: float

class AlgofiPoolsAnalyzer:
    """
    Analyzer for Algofi DEX liquidity pools and liquidity mining programs.

    Analyzes trading fees, liquidity mining rewards, and ALFI token emissions
    to provide comprehensive yield analysis for LP positions.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Algofi pools analyzer"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.cache = {}
        self.mining_cache = {}

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
                    'algofi_dex': {
                        'api_endpoint': 'https://api.algofi.org/v1/dex',
                        'weight': 0.35,
                        'fee_tier': 0.0025
                    }
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the analyzer"""
        logger = logging.getLogger('algofi_pools_analyzer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def fetch_algofi_pools(self) -> List[AlgofiPool]:
        """
        Fetch current pool data from Algofi DEX

        Returns:
            List[AlgofiPool]: List of Algofi DEX liquidity pools
        """
        try:
            # Check cache first
            if self._is_cache_valid('algofi_pools'):
                return self.cache['algofi_pools']

            # Fetch from Algofi DEX API
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
            self.cache['algofi_pools'] = pools
            self.cache['algofi_pools_timestamp'] = datetime.now()

            return pools

        except Exception as e:
            self.logger.error(f"Error fetching Algofi pools: {e}")
            return self._get_fallback_pools()

    async def _fetch_pools_from_api(self) -> List[Dict]:
        """Fetch pool data from Algofi DEX API"""
        try:
            algofi_config = self.config['dex_protocols']['algofi_dex']
            api_endpoint = algofi_config['api_endpoint']

            async with aiohttp.ClientSession() as session:
                # Try to fetch from actual Algofi DEX API
                async with session.get(f"{api_endpoint}/pools") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('pools', [])
                    else:
                        self.logger.warning(f"Algofi DEX API returned status {response.status}")

        except Exception as e:
            self.logger.warning(f"Direct Algofi DEX API unavailable: {e}")

        # Fallback to MCP service
        return await self._fetch_via_mcp_service()

    async def _fetch_via_mcp_service(self) -> List[Dict]:
        """Fetch pool data via MCP service"""
        try:
            mcp_url = self.config['mcp_services']['market_data_url']

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mcp_url}/dex/algofi/pools") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('pools', [])

        except Exception as e:
            self.logger.warning(f"MCP service unavailable: {e}")

        # Return simulated data if all sources fail
        return self._get_simulated_pool_data()

    def _get_simulated_pool_data(self) -> List[Dict]:
        """Return simulated Algofi DEX pool data for testing"""
        return [
            {
                'pool_id': 'algofi_algo_usdc',
                'asset_1_id': '0',
                'asset_2_id': '31566704',
                'asset_1_name': 'ALGO',
                'asset_2_name': 'USDC',
                'liquidity_usd': 3200000,      # $3.2M liquidity
                'volume_24h_usd': 220000,      # $220K daily volume
                'volume_7d_usd': 1540000,      # $1.54M weekly volume
                'asset_1_reserves': 12800000,  # 12.8M ALGO
                'asset_2_reserves': 3200000,   # 3.2M USDC
                'pool_tokens_outstanding': 6400000,
                'price_ratio': 0.25,           # 1 ALGO = 0.25 USDC
                'fee_tier': 0.0025,            # 0.25% fee
                'multiplier_boost': 1.5,       # 1.5x boost for this pool
                'alfi_emission_rate': 50000    # 50K ALFI per day
            },
            {
                'pool_id': 'algofi_algo_usdt',
                'asset_1_id': '0',
                'asset_2_id': '312769',
                'asset_1_name': 'ALGO',
                'asset_2_name': 'USDT',
                'liquidity_usd': 2400000,      # $2.4M liquidity
                'volume_24h_usd': 165000,      # $165K daily volume
                'volume_7d_usd': 1155000,      # $1.155M weekly volume
                'asset_1_reserves': 9600000,   # 9.6M ALGO
                'asset_2_reserves': 2400000,   # 2.4M USDT
                'pool_tokens_outstanding': 4800000,
                'price_ratio': 0.25,           # 1 ALGO = 0.25 USDT
                'fee_tier': 0.0025,            # 0.25% fee
                'multiplier_boost': 1.3,       # 1.3x boost for this pool
                'alfi_emission_rate': 35000    # 35K ALFI per day
            },
            {
                'pool_id': 'algofi_usdc_usdt',
                'asset_1_id': '31566704',
                'asset_2_id': '312769',
                'asset_1_name': 'USDC',
                'asset_2_name': 'USDT',
                'liquidity_usd': 1100000,      # $1.1M liquidity
                'volume_24h_usd': 45000,       # $45K daily volume
                'volume_7d_usd': 315000,       # $315K weekly volume
                'asset_1_reserves': 550000,    # 550K USDC
                'asset_2_reserves': 550000,    # 550K USDT
                'pool_tokens_outstanding': 1100000,
                'price_ratio': 1.0,            # 1 USDC = 1 USDT
                'fee_tier': 0.0025,            # 0.25% fee
                'multiplier_boost': 1.0,       # 1.0x boost (no boost)
                'alfi_emission_rate': 15000    # 15K ALFI per day
            },
            {
                'pool_id': 'algofi_algo_gobtc',
                'asset_1_id': '0',
                'asset_2_id': '386192725',
                'asset_1_name': 'ALGO',
                'asset_2_name': 'goBTC',
                'liquidity_usd': 750000,       # $750K liquidity
                'volume_24h_usd': 125000,      # $125K daily volume
                'volume_7d_usd': 875000,       # $875K weekly volume
                'asset_1_reserves': 2250000,   # 2.25M ALGO
                'asset_2_reserves': 12.5,      # 12.5 goBTC
                'pool_tokens_outstanding': 1500000,
                'price_ratio': 0.00055556,     # 1 ALGO = 0.00055556 goBTC
                'fee_tier': 0.0025,            # 0.25% fee
                'multiplier_boost': 2.0,       # 2.0x boost for volatile pair
                'alfi_emission_rate': 75000    # 75K ALFI per day
            }
        ]

    def _parse_pool_data(self, pool_data: Dict) -> Optional[AlgofiPool]:
        """Parse raw pool data into AlgofiPool object"""
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

            # Get fee tier and multiplier
            fee_tier = float(pool_data.get('fee_tier', self.config['dex_protocols']['algofi_dex']['fee_tier']))
            multiplier_boost = float(pool_data.get('multiplier_boost', 1.0))

            # Calculate APY components
            apy_trading_fees = self._calculate_trading_fee_apy(volume_24h_usd, liquidity_usd, fee_tier)
            apy_liquidity_mining = self._calculate_liquidity_mining_apy(pool_data, liquidity_usd)
            apy_alfi_rewards = self._calculate_alfi_rewards_apy(pool_data, liquidity_usd, multiplier_boost)

            total_apy = apy_trading_fees + apy_liquidity_mining + apy_alfi_rewards

            return AlgofiPool(
                pool_id=pool_id,
                asset_1_id=asset_1_id,
                asset_2_id=asset_2_id,
                asset_1_name=asset_1_name,
                asset_2_name=asset_2_name,
                liquidity_usd=liquidity_usd,
                volume_24h_usd=volume_24h_usd,
                volume_7d_usd=volume_7d_usd,
                apy_trading_fees=apy_trading_fees,
                apy_liquidity_mining=apy_liquidity_mining,
                apy_alfi_rewards=apy_alfi_rewards,
                total_apy=total_apy,
                pool_tokens_outstanding=pool_tokens_outstanding,
                asset_1_reserves=asset_1_reserves,
                asset_2_reserves=asset_2_reserves,
                price_ratio=price_ratio,
                fee_tier=fee_tier,
                multiplier_boost=multiplier_boost,
                last_update=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error parsing pool data: {e}")
            return None

    def _calculate_trading_fee_apy(self, volume_24h: float, liquidity: float, fee_tier: float) -> float:
        """Calculate APY from trading fees"""
        if liquidity == 0:
            return 0.0

        # Daily fee revenue
        daily_fees = volume_24h * fee_tier

        # Annualized fee APY
        annual_fees = daily_fees * 365
        fee_apy = annual_fees / liquidity if liquidity > 0 else 0.0

        # Cap at reasonable maximum
        return min(fee_apy, 3.0)  # Cap at 300% APY

    def _calculate_liquidity_mining_apy(self, pool_data: Dict, liquidity: float) -> float:
        """Calculate APY from general liquidity mining programs"""
        # Base liquidity mining rewards (not ALFI-specific)
        base_mining_apy = 0.0

        # ALGO pools typically have higher base mining rewards
        pool_id = pool_data.get('pool_id', '')
        if 'algo' in pool_id.lower():
            base_mining_apy = 0.01  # 1% base mining APY

        # Popular pairs get bonus mining rewards
        if any(pair in pool_id.lower() for pair in ['algo_usdc', 'algo_usdt']):
            base_mining_apy += 0.005  # Additional 0.5% for popular pairs

        return base_mining_apy

    def _calculate_alfi_rewards_apy(self, pool_data: Dict, liquidity: float, multiplier: float) -> float:
        """Calculate APY from ALFI token rewards"""
        if liquidity == 0:
            return 0.0

        # ALFI emission data
        alfi_emission_rate = float(pool_data.get('alfi_emission_rate', 0))  # ALFI per day
        alfi_price = 0.08  # Assume $0.08 per ALFI (should fetch real price)

        # Daily USD value of ALFI rewards
        daily_alfi_value = alfi_emission_rate * alfi_price * multiplier

        # Annualized ALFI rewards APY
        annual_alfi_value = daily_alfi_value * 365
        alfi_apy = annual_alfi_value / liquidity if liquidity > 0 else 0.0

        # Apply vesting discount (30% discount for 90-day vesting)
        vesting_discount = 0.7
        alfi_apy *= vesting_discount

        # Cap at reasonable maximum
        return min(alfi_apy, 2.0)  # Cap at 200% APY

    async def analyze_algofi_pools(self) -> AlgofiPoolData:
        """
        Analyze Algofi pools and calculate aggregate metrics

        Returns:
            AlgofiPoolData: Complete Algofi pool analysis
        """
        try:
            # Fetch current pools
            pools = await self.fetch_algofi_pools()

            if not pools:
                return self._get_fallback_pool_data()

            # Filter pools by minimum liquidity threshold
            min_liquidity = self.config['dex_protocols']['algofi_dex']['min_liquidity_threshold']
            filtered_pools = [p for p in pools if p.liquidity_usd >= min_liquidity]

            if not filtered_pools:
                filtered_pools = pools  # Use all pools if none meet threshold

            # Calculate aggregate metrics
            weighted_average_apy = self._calculate_weighted_average_apy(filtered_pools)
            total_tvl = sum(pool.liquidity_usd for pool in filtered_pools)
            total_volume_24h = sum(pool.volume_24h_usd for pool in filtered_pools)
            average_trading_apy = statistics.mean([pool.apy_trading_fees for pool in filtered_pools])
            average_mining_apy = statistics.mean([pool.apy_liquidity_mining for pool in filtered_pools])
            average_alfi_rewards = statistics.mean([pool.apy_alfi_rewards for pool in filtered_pools])

            # Calculate total ALFI emissions
            total_alfi_emissions = self._calculate_total_alfi_emissions(filtered_pools)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(filtered_pools)

            return AlgofiPoolData(
                pools=filtered_pools,
                weighted_average_apy=weighted_average_apy,
                total_tvl=total_tvl,
                total_volume_24h=total_volume_24h,
                average_trading_apy=average_trading_apy,
                average_mining_apy=average_mining_apy,
                average_alfi_rewards=average_alfi_rewards,
                total_alfi_emissions=total_alfi_emissions,
                confidence_score=confidence_score,
                timestamp=datetime.now(),
                metadata={
                    'total_pools': len(pools),
                    'filtered_pools': len(filtered_pools),
                    'min_liquidity_threshold': min_liquidity,
                    'data_source': 'algofi_dex_api'
                }
            )

        except Exception as e:
            self.logger.error(f"Error analyzing Algofi pools: {e}")
            return self._get_fallback_pool_data()

    def _calculate_weighted_average_apy(self, pools: List[AlgofiPool]) -> float:
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

    def _calculate_total_alfi_emissions(self, pools: List[AlgofiPool]) -> float:
        """Calculate total daily ALFI emissions across all pools"""
        # This would typically fetch from the pool data
        # For now, estimate based on pool count and typical emission rates
        base_emission_per_pool = 30000  # 30K ALFI per pool per day (average)
        return len(pools) * base_emission_per_pool

    def _calculate_confidence_score(self, pools: List[AlgofiPool]) -> float:
        """Calculate confidence score for the pool data"""
        if not pools:
            return 0.0

        confidence = 1.0

        # Reduce confidence for low number of pools
        if len(pools) < 3:
            confidence *= 0.8

        # Check data freshness
        oldest_update = min(pool.last_update for pool in pools)
        if datetime.now() - oldest_update > timedelta(minutes=10):
            confidence *= 0.9

        # Check for extreme APY values
        total_apys = [pool.total_apy for pool in pools]
        if any(apy > 5.0 or apy < 0.001 for apy in total_apys):  # > 500% or < 0.1%
            confidence *= 0.7

        # Check ALFI rewards consistency
        alfi_rewards = [pool.apy_alfi_rewards for pool in pools]
        if any(reward > 3.0 for reward in alfi_rewards):  # > 300% ALFI rewards seems high
            confidence *= 0.8

        return max(confidence, 0.1)

    async def get_liquidity_mining_details(self, pool_id: str) -> LiquidityMiningData:
        """
        Get detailed liquidity mining information for a pool

        Args:
            pool_id: ID of the pool

        Returns:
            LiquidityMiningData: Detailed mining information
        """
        try:
            pools = await self.fetch_algofi_pools()
            pool = next((p for p in pools if p.pool_id == pool_id), None)

            if not pool:
                return self._get_fallback_mining_data(pool_id)

            # Get ALFI token details (simulated)
            alfi_emission_rate = 50000  # 50K ALFI per day for this pool
            alfi_price_usd = 0.08       # $0.08 per ALFI
            multiplier = pool.multiplier_boost
            lock_period_days = 0        # No lock period for Algofi
            vesting_schedule = "Linear 90 days"  # 90-day linear vesting

            # Calculate effective APY (including vesting impact)
            raw_apy = pool.apy_alfi_rewards
            vesting_discount = 0.85     # 15% discount for vesting
            effective_apy = raw_apy * vesting_discount

            # Risk-adjusted APY (accounting for ALFI price volatility)
            volatility_discount = 0.9   # 10% discount for token volatility
            risk_adjusted_apy = effective_apy * volatility_discount

            return LiquidityMiningData(
                pool_id=pool_id,
                alfi_emission_rate=alfi_emission_rate,
                alfi_price_usd=alfi_price_usd,
                multiplier=multiplier,
                lock_period_days=lock_period_days,
                vesting_schedule=vesting_schedule,
                effective_apy=effective_apy,
                risk_adjusted_apy=risk_adjusted_apy
            )

        except Exception as e:
            self.logger.error(f"Error getting mining details for {pool_id}: {e}")
            return self._get_fallback_mining_data(pool_id)

    async def get_pool_by_pair(self, asset_1: str, asset_2: str) -> Optional[AlgofiPool]:
        """
        Get pool data for a specific asset pair

        Args:
            asset_1: First asset name
            asset_2: Second asset name

        Returns:
            AlgofiPool or None if not found
        """
        try:
            pools = await self.fetch_algofi_pools()

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

    async def analyze_alfi_emissions_impact(self) -> Dict[str, Any]:
        """
        Analyze the impact of ALFI token emissions on pool yields

        Returns:
            Dict containing emissions impact analysis
        """
        try:
            pool_data = await self.analyze_algofi_pools()

            # Calculate emissions metrics
            total_emissions_per_day = pool_data.total_alfi_emissions
            alfi_price = 0.08  # $0.08 per ALFI
            total_daily_usd_emissions = total_emissions_per_day * alfi_price

            # Analyze distribution across pools
            emissions_by_pool = []
            for pool in pool_data.pools:
                pool_emissions = {
                    'pair': f"{pool.asset_1_name}/{pool.asset_2_name}",
                    'liquidity_usd': pool.liquidity_usd,
                    'alfi_apy': pool.apy_alfi_rewards,
                    'multiplier': pool.multiplier_boost,
                    'emissions_share': pool.apy_alfi_rewards * pool.liquidity_usd / total_daily_usd_emissions if total_daily_usd_emissions > 0 else 0
                }
                emissions_by_pool.append(pool_emissions)

            # Sort by ALFI APY
            emissions_by_pool.sort(key=lambda x: x['alfi_apy'], reverse=True)

            return {
                "analysis_type": "alfi_emissions_impact",
                "total_daily_alfi_emissions": total_emissions_per_day,
                "total_daily_usd_value": total_daily_usd_emissions,
                "alfi_price_usd": alfi_price,
                "average_alfi_apy": pool_data.average_alfi_rewards,
                "weighted_alfi_contribution": pool_data.average_alfi_rewards / pool_data.weighted_average_apy if pool_data.weighted_average_apy > 0 else 0,
                "emissions_by_pool": emissions_by_pool,
                "high_multiplier_pools": [p for p in emissions_by_pool if p['multiplier'] > 1.5],
                "sustainability_score": self._calculate_emissions_sustainability(pool_data),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing ALFI emissions impact: {e}")
            return {"error": str(e)}

    def _calculate_emissions_sustainability(self, pool_data: AlgofiPoolData) -> float:
        """Calculate sustainability score for ALFI emissions"""
        # Factors affecting sustainability:
        # 1. Ratio of trading fees to ALFI rewards
        # 2. Total TVL growth potential
        # 3. Trading volume sustainability

        trading_to_alfi_ratio = pool_data.average_trading_apy / max(pool_data.average_alfi_rewards, 0.001)

        # Higher ratio = more sustainable (less dependent on token emissions)
        sustainability_score = min(trading_to_alfi_ratio / 2.0, 1.0)  # Normalize to 0-1

        # Adjust for TVL size (larger TVL = more sustainable)
        if pool_data.total_tvl > 10000000:  # > $10M
            sustainability_score *= 1.1
        elif pool_data.total_tvl < 1000000:  # < $1M
            sustainability_score *= 0.8

        return min(max(sustainability_score, 0.0), 1.0)

    async def compare_pool_efficiency(self) -> Dict[str, Any]:
        """
        Compare efficiency metrics across pools

        Returns:
            Dict containing pool efficiency comparison
        """
        try:
            pool_data = await self.analyze_algofi_pools()

            efficiency_metrics = []
            for pool in pool_data.pools:
                # Calculate various efficiency metrics
                volume_to_liquidity_ratio = pool.volume_24h_usd / max(pool.liquidity_usd, 1)
                fee_efficiency = pool.apy_trading_fees / max(volume_to_liquidity_ratio, 0.001)
                capital_efficiency = pool.total_apy / max(pool.liquidity_usd / 1000000, 0.001)  # APY per $1M

                efficiency_metrics.append({
                    'pair': f"{pool.asset_1_name}/{pool.asset_2_name}",
                    'liquidity_usd': pool.liquidity_usd,
                    'volume_24h_usd': pool.volume_24h_usd,
                    'total_apy': pool.total_apy,
                    'volume_to_liquidity_ratio': volume_to_liquidity_ratio,
                    'fee_efficiency': fee_efficiency,
                    'capital_efficiency': capital_efficiency,
                    'multiplier_boost': pool.multiplier_boost,
                    'overall_score': (fee_efficiency + capital_efficiency) / 2
                })

            # Sort by overall efficiency score
            efficiency_metrics.sort(key=lambda x: x['overall_score'], reverse=True)

            return {
                "analysis_type": "pool_efficiency_comparison",
                "pools": efficiency_metrics,
                "most_efficient_pool": efficiency_metrics[0] if efficiency_metrics else None,
                "least_efficient_pool": efficiency_metrics[-1] if efficiency_metrics else None,
                "average_efficiency": statistics.mean([p['overall_score'] for p in efficiency_metrics]) if efficiency_metrics else 0,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error comparing pool efficiency: {e}")
            return {"error": str(e)}

    def _get_fallback_pools(self) -> List[AlgofiPool]:
        """Return fallback pools when live data is unavailable"""
        return [
            AlgofiPool(
                pool_id='fallback_algo_usdc',
                asset_1_id='0',
                asset_2_id='31566704',
                asset_1_name='ALGO',
                asset_2_name='USDC',
                liquidity_usd=3000000,
                volume_24h_usd=200000,
                volume_7d_usd=1400000,
                apy_trading_fees=0.022,
                apy_liquidity_mining=0.008,
                apy_alfi_rewards=0.035,
                total_apy=0.065,
                pool_tokens_outstanding=6000000,
                asset_1_reserves=12000000,
                asset_2_reserves=3000000,
                price_ratio=0.25,
                fee_tier=0.0025,
                multiplier_boost=1.5,
                last_update=datetime.now()
            )
        ]

    def _get_fallback_pool_data(self) -> AlgofiPoolData:
        """Return fallback pool data when analysis fails"""
        fallback_pools = self._get_fallback_pools()

        return AlgofiPoolData(
            pools=fallback_pools,
            weighted_average_apy=0.065,
            total_tvl=3000000,
            total_volume_24h=200000,
            average_trading_apy=0.022,
            average_mining_apy=0.008,
            average_alfi_rewards=0.035,
            total_alfi_emissions=120000,
            confidence_score=0.5,
            timestamp=datetime.now(),
            metadata={'fallback': True}
        )

    def _get_fallback_mining_data(self, pool_id: str) -> LiquidityMiningData:
        """Return fallback mining data"""
        return LiquidityMiningData(
            pool_id=pool_id,
            alfi_emission_rate=50000,
            alfi_price_usd=0.08,
            multiplier=1.5,
            lock_period_days=0,
            vesting_schedule="Linear 90 days",
            effective_apy=0.035,
            risk_adjusted_apy=0.030
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
    """Example usage of the AlgofiPoolsAnalyzer"""
    analyzer = AlgofiPoolsAnalyzer()

    print("=== Algofi Pools Analyzer Demo ===")

    # Analyze current pools
    print("\n1. Current Algofi Pool Analysis:")
    pool_data = await analyzer.analyze_algofi_pools()
    print(f"   Weighted Average APY: {pool_data.weighted_average_apy:.2%}")
    print(f"   Total TVL: ${pool_data.total_tvl:,.0f}")
    print(f"   Total 24h Volume: ${pool_data.total_volume_24h:,.0f}")
    print(f"   Average Trading APY: {pool_data.average_trading_apy:.2%}")
    print(f"   Average Mining APY: {pool_data.average_mining_apy:.2%}")
    print(f"   Average ALFI Rewards: {pool_data.average_alfi_rewards:.2%}")
    print(f"   Total ALFI Emissions: {pool_data.total_alfi_emissions:,.0f} ALFI/day")
    print(f"   Confidence Score: {pool_data.confidence_score:.2f}")

    # Show individual pools
    print(f"\n2. Individual Pool Details ({len(pool_data.pools)} pools):")
    for pool in pool_data.pools[:3]:  # Top 3 by liquidity
        print(f"   {pool.asset_1_name}/{pool.asset_2_name}:")
        print(f"     Total APY: {pool.total_apy:.2%}")
        print(f"     Trading Fees APY: {pool.apy_trading_fees:.2%}")
        print(f"     ALFI Rewards APY: {pool.apy_alfi_rewards:.2%}")
        print(f"     Multiplier Boost: {pool.multiplier_boost:.1f}x")
        print(f"     Liquidity: ${pool.liquidity_usd:,.0f}")
        print(f"     24h Volume: ${pool.volume_24h_usd:,.0f}")

    # Get specific pool
    print("\n3. ALGO/USDC Pool Analysis:")
    algo_usdc_pool = await analyzer.get_pool_by_pair('ALGO', 'USDC')
    if algo_usdc_pool:
        print(f"   Total APY: {algo_usdc_pool.total_apy:.2%}")
        print(f"   Fee Tier: {algo_usdc_pool.fee_tier:.2%}")
        print(f"   Multiplier Boost: {algo_usdc_pool.multiplier_boost:.1f}x")
        print(f"   ALGO Reserves: {algo_usdc_pool.asset_1_reserves:,.0f}")
        print(f"   USDC Reserves: {algo_usdc_pool.asset_2_reserves:,.0f}")

        # Get mining details
        print("\n4. Liquidity Mining Details (ALGO/USDC):")
        mining_data = await analyzer.get_liquidity_mining_details(algo_usdc_pool.pool_id)
        print(f"   ALFI Emission Rate: {mining_data.alfi_emission_rate:,.0f} ALFI/day")
        print(f"   ALFI Price: ${mining_data.alfi_price_usd:.3f}")
        print(f"   Effective APY: {mining_data.effective_apy:.2%}")
        print(f"   Risk-Adjusted APY: {mining_data.risk_adjusted_apy:.2%}")
        print(f"   Vesting Schedule: {mining_data.vesting_schedule}")

    # ALFI emissions analysis
    print("\n5. ALFI Emissions Impact Analysis:")
    emissions_analysis = await analyzer.analyze_alfi_emissions_impact()
    if "error" not in emissions_analysis:
        print(f"   Total Daily ALFI Emissions: {emissions_analysis['total_daily_alfi_emissions']:,.0f}")
        print(f"   Total Daily USD Value: ${emissions_analysis['total_daily_usd_value']:,.0f}")
        print(f"   Average ALFI APY: {emissions_analysis['average_alfi_apy']:.2%}")
        print(f"   Sustainability Score: {emissions_analysis['sustainability_score']:.2f}")
        print(f"   High Multiplier Pools: {len(emissions_analysis['high_multiplier_pools'])}")

    # Pool efficiency comparison
    print("\n6. Pool Efficiency Comparison:")
    efficiency_analysis = await analyzer.compare_pool_efficiency()
    if "error" not in efficiency_analysis:
        top_3_efficient = efficiency_analysis['pools'][:3]
        for i, pool in enumerate(top_3_efficient, 1):
            print(f"   {i}. {pool['pair']}:")
            print(f"      Overall Score: {pool['overall_score']:.2f}")
            print(f"      Capital Efficiency: {pool['capital_efficiency']:.2f}")
            print(f"      Volume/Liquidity Ratio: {pool['volume_to_liquidity_ratio']:.3f}")

if __name__ == "__main__":
    asyncio.run(main())