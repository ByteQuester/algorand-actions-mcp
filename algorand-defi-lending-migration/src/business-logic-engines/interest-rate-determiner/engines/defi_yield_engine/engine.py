"""
DeFi Yield Engine

Analyzes yields from various DeFi protocols on Algorand to determine
competitive rates and market-based pricing.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import httpx
import aiohttp
from algosdk.v2client import algod

from .models import (
    DeFiProtocolData,
    YieldMetrics,
    PoolData,
    DeFiMarketData,
    ProtocolType
)

logger = logging.getLogger(__name__)

class DeFiYieldEngine:
    """
    Engine for analyzing DeFi protocol yields on Algorand to determine
    competitive interest rates for lending platforms.
    """

    def __init__(
        self,
        algod_client: algod.AlgodClient,
        protocol_apis: Dict[str, str],
        cache_ttl: int = 180  # 3 minutes
    ):
        self.algod_client = algod_client
        self.protocol_apis = protocol_apis
        self.cache_ttl = cache_ttl
        self._cache: Dict = {}
        self._cache_timestamps: Dict = {}

        # Default Algorand DeFi protocol APIs
        self.default_apis = {
            'tinyman': 'https://mainnet.analytics.tinyman.org/api/v1',
            'pact': 'https://api.pact.fi/api/v1',
            'humble_swap': 'https://analytics.humble.sh/api/v1',
            'algofi': 'https://api.algofi.org/v1',
            'folks_finance': 'https://api.folksfinance.io/api/v1'
        }

    async def calculate_defi_rates(
        self,
        include_protocols: Optional[List[str]] = None,
        risk_threshold: Decimal = Decimal('0.7')
    ) -> YieldMetrics:
        """
        Calculate aggregated DeFi yields across Algorand protocols
        """
        try:
            # Get data from all protocols
            protocol_data = await self._fetch_all_protocol_data(include_protocols)

            # Filter by risk threshold
            safe_protocols = [
                p for p in protocol_data
                if p.risk_score <= risk_threshold
            ]

            if not safe_protocols:
                logger.warning("No protocols meet risk threshold, using all protocols")
                safe_protocols = protocol_data

            # Calculate metrics
            metrics = self._calculate_yield_metrics(safe_protocols)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating DeFi rates: {e}")
            raise

    async def _fetch_all_protocol_data(
        self,
        include_protocols: Optional[List[str]] = None
    ) -> List[DeFiProtocolData]:
        """Fetch data from all configured DeFi protocols"""

        protocols_to_fetch = include_protocols or list(self.default_apis.keys())

        tasks = [
            self._fetch_protocol_data(protocol_name)
            for protocol_name in protocols_to_fetch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        protocol_data = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch data for {protocols_to_fetch[i]}: {result}")
            else:
                protocol_data.extend(result)

        return protocol_data

    async def _fetch_protocol_data(self, protocol_name: str) -> List[DeFiProtocolData]:
        """Fetch data for a specific protocol"""
        cache_key = f"protocol_data_{protocol_name}"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            if protocol_name == 'tinyman':
                data = await self._fetch_tinyman_data()
            elif protocol_name == 'pact':
                data = await self._fetch_pact_data()
            elif protocol_name == 'humble_swap':
                data = await self._fetch_humble_data()
            elif protocol_name == 'algofi':
                data = await self._fetch_algofi_data()
            elif protocol_name == 'folks_finance':
                data = await self._fetch_folks_data()
            else:
                logger.warning(f"Unknown protocol: {protocol_name}")
                data = []

            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return data

        except Exception as e:
            logger.error(f"Error fetching {protocol_name} data: {e}")
            return []

    async def _fetch_tinyman_data(self) -> List[DeFiProtocolData]:
        """Fetch Tinyman DEX data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get pool data
                async with session.get(f"{self.default_apis['tinyman']}/pools") as resp:
                    pools_data = await resp.json()

                # Get protocol stats
                async with session.get(f"{self.default_apis['tinyman']}/stats") as resp:
                    stats_data = await resp.json()

            # Process pools and calculate average APY
            total_tvl = Decimal('0')
            weighted_apy = Decimal('0')
            pool_count = len(pools_data.get('pools', []))

            for pool in pools_data.get('pools', [])[:10]:  # Top 10 pools
                tvl = Decimal(str(pool.get('tvl_usd', 0)))
                apy = Decimal(str(pool.get('apy', 0)))

                total_tvl += tvl
                weighted_apy += apy * tvl

            avg_apy = weighted_apy / total_tvl if total_tvl > 0 else Decimal('0')

            return [DeFiProtocolData(
                protocol_name='Tinyman',
                protocol_type=ProtocolType.DEX,
                tvl_usd=total_tvl,
                apy=avg_apy,
                volume_24h=Decimal(str(stats_data.get('volume_24h', 0))),
                fees_24h=Decimal(str(stats_data.get('fees_24h', 0))),
                token_address=None,
                pool_count=pool_count,
                active_users=stats_data.get('active_users', 0),
                risk_score=Decimal('0.3'),  # Low risk for established DEX
                timestamp=datetime.utcnow()
            )]

        except Exception as e:
            logger.error(f"Error fetching Tinyman data: {e}")
            # Return mock data if API fails
            return [DeFiProtocolData(
                protocol_name='Tinyman',
                protocol_type=ProtocolType.DEX,
                tvl_usd=Decimal('50000000'),  # $50M
                apy=Decimal('0.12'),  # 12%
                volume_24h=Decimal('5000000'),
                fees_24h=Decimal('15000'),
                token_address=None,
                pool_count=50,
                active_users=5000,
                risk_score=Decimal('0.3'),
                timestamp=datetime.utcnow()
            )]

    async def _fetch_algofi_data(self) -> List[DeFiProtocolData]:
        """Fetch Algofi lending protocol data"""
        try:
            # Mock Algofi data (would be real API in production)
            return [DeFiProtocolData(
                protocol_name='Algofi',
                protocol_type=ProtocolType.LENDING,
                tvl_usd=Decimal('100000000'),  # $100M
                apy=Decimal('0.08'),  # 8% lending APY
                volume_24h=Decimal('2000000'),
                fees_24h=Decimal('8000'),
                token_address=None,
                pool_count=8,
                active_users=3000,
                risk_score=Decimal('0.4'),  # Medium risk for lending
                timestamp=datetime.utcnow()
            )]

        except Exception as e:
            logger.error(f"Error fetching Algofi data: {e}")
            return []

    async def _fetch_pact_data(self) -> List[DeFiProtocolData]:
        """Fetch Pact DEX data"""
        try:
            # Mock Pact data
            return [DeFiProtocolData(
                protocol_name='Pact',
                protocol_type=ProtocolType.DEX,
                tvl_usd=Decimal('25000000'),  # $25M
                apy=Decimal('0.15'),  # 15%
                volume_24h=Decimal('1500000'),
                fees_24h=Decimal('4500'),
                token_address=None,
                pool_count=30,
                active_users=2500,
                risk_score=Decimal('0.35'),
                timestamp=datetime.utcnow()
            )]

        except Exception as e:
            logger.error(f"Error fetching Pact data: {e}")
            return []

    async def _fetch_humble_data(self) -> List[DeFiProtocolData]:
        """Fetch Humble Swap data"""
        try:
            # Mock Humble data
            return [DeFiProtocolData(
                protocol_name='Humble',
                protocol_type=ProtocolType.DEX,
                tvl_usd=Decimal('15000000'),  # $15M
                apy=Decimal('0.18'),  # 18%
                volume_24h=Decimal('800000'),
                fees_24h=Decimal('2400'),
                token_address=None,
                pool_count=20,
                active_users=1500,
                risk_score=Decimal('0.45'),  # Higher risk for smaller protocol
                timestamp=datetime.utcnow()
            )]

        except Exception as e:
            logger.error(f"Error fetching Humble data: {e}")
            return []

    async def _fetch_folks_data(self) -> List[DeFiProtocolData]:
        """Fetch Folks Finance data"""
        try:
            # Mock Folks Finance data
            return [DeFiProtocolData(
                protocol_name='Folks Finance',
                protocol_type=ProtocolType.LENDING,
                tvl_usd=Decimal('75000000'),  # $75M
                apy=Decimal('0.09'),  # 9% lending APY
                volume_24h=Decimal('1200000'),
                fees_24h=Decimal('3600'),
                token_address=None,
                pool_count=12,
                active_users=2000,
                risk_score=Decimal('0.38'),
                timestamp=datetime.utcnow()
            )]

        except Exception as e:
            logger.error(f"Error fetching Folks Finance data: {e}")
            return []

    def _calculate_yield_metrics(self, protocol_data: List[DeFiProtocolData]) -> YieldMetrics:
        """Calculate aggregated yield metrics"""

        if not protocol_data:
            return YieldMetrics(
                weighted_avg_apy=Decimal('0.05'),  # 5% default
                median_apy=Decimal('0.05'),
                top_quartile_apy=Decimal('0.08'),
                total_tvl=Decimal('0'),
                protocol_count=0,
                risk_adjusted_apy=Decimal('0.04'),
                volatility_score=Decimal('0.5'),
                timestamp=datetime.utcnow()
            )

        # Calculate weighted average APY
        total_tvl = sum(p.tvl_usd for p in protocol_data)
        weighted_sum = sum(p.apy * p.tvl_usd for p in protocol_data)
        weighted_avg_apy = weighted_sum / total_tvl if total_tvl > 0 else Decimal('0')

        # Calculate median APY
        apys = sorted([p.apy for p in protocol_data])
        n = len(apys)
        median_apy = apys[n // 2] if n % 2 == 1 else (apys[n // 2 - 1] + apys[n // 2]) / 2

        # Calculate top quartile APY
        top_quartile_idx = int(n * 0.75)
        top_quartile_apy = apys[top_quartile_idx] if top_quartile_idx < n else apys[-1]

        # Calculate risk-adjusted APY
        risk_weighted_sum = sum(p.risk_adjusted_apy() * p.tvl_usd for p in protocol_data)
        risk_adjusted_apy = risk_weighted_sum / total_tvl if total_tvl > 0 else Decimal('0')

        # Calculate volatility score
        apy_variance = sum((p.apy - weighted_avg_apy) ** 2 for p in protocol_data) / len(protocol_data)
        volatility_score = min(apy_variance.sqrt() / weighted_avg_apy if weighted_avg_apy > 0 else Decimal('1'), Decimal('1'))

        return YieldMetrics(
            weighted_avg_apy=weighted_avg_apy,
            median_apy=median_apy,
            top_quartile_apy=top_quartile_apy,
            total_tvl=total_tvl,
            protocol_count=len(protocol_data),
            risk_adjusted_apy=risk_adjusted_apy,
            volatility_score=volatility_score,
            timestamp=datetime.utcnow()
        )

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self._cache:
            return False

        cache_time = self._cache_timestamps.get(key)
        if not cache_time:
            return False

        return (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl

    async def get_competitive_rates(
        self,
        loan_amount: Decimal,
        target_utilization: Decimal = Decimal('0.8')
    ) -> Dict[str, Decimal]:
        """
        Get competitive rates based on DeFi market conditions
        """
        yield_metrics = await self.calculate_defi_rates()

        # Base competitive rate (slightly below market average)
        competitive_rate = yield_metrics.weighted_avg_apy * Decimal('0.85')

        # Utilization adjustment
        util_adjustment = (target_utilization - Decimal('0.5')) * Decimal('0.1')

        # Volatility adjustment
        volatility_adjustment = yield_metrics.volatility_score * Decimal('0.05')

        final_rate = competitive_rate + util_adjustment + volatility_adjustment

        return {
            'market_avg_apy': yield_metrics.weighted_avg_apy,
            'risk_adjusted_apy': yield_metrics.risk_adjusted_apy,
            'competitive_rate': competitive_rate,
            'volatility_adjustment': volatility_adjustment,
            'utilization_adjustment': util_adjustment,
            'final_rate': final_rate,
            'market_volatility': yield_metrics.volatility_score
        }