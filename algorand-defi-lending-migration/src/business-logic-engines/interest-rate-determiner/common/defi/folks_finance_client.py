"""
Folks Finance protocol client for lending pools and yield farming data.

Provides integration with Folks Finance including:
- Lending pool rates and metrics
- Governance token staking
- Cross-chain bridge yields
- Liquid staking opportunities
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
import logging

from ..models.defi_models import DeFiProtocol, ProtocolRates, DeFiYield

logger = logging.getLogger(__name__)


@dataclass
class FolksRates:
    """Folks Finance protocol rates and metrics"""
    timestamp: datetime

    # Lending pool rates
    algo_pool_apy: Decimal = Decimal('0')
    usdc_pool_apy: Decimal = Decimal('0')
    usdt_pool_apy: Decimal = Decimal('0')
    opul_pool_apy: Decimal = Decimal('0')

    # Governance staking
    folks_staking_apy: Decimal = Decimal('0')
    xalgo_apy: Decimal = Decimal('0')  # Liquid ALGO staking

    # Liquidity mining rewards
    algo_rewards_apy: Decimal = Decimal('0')
    folks_rewards_apy: Decimal = Decimal('0')

    # Pool utilization and metrics
    total_deposits: Dict[int, Decimal] = field(default_factory=dict)
    total_borrowed: Dict[int, Decimal] = field(default_factory=dict)
    pool_utilization: Dict[int, Decimal] = field(default_factory=dict)

    # Protocol metrics
    total_value_locked: Decimal = Decimal('0')
    folks_token_price: Decimal = Decimal('0')
    daily_volume: Decimal = Decimal('0')

    def get_pool_apy(self, asset_id: int) -> Decimal:
        """Get lending pool APY for specific asset"""
        pool_mapping = {
            0: self.algo_pool_apy,          # ALGO
            31566704: self.usdc_pool_apy,   # USDC
            312769: self.usdt_pool_apy,     # USDT
            287867876: self.opul_pool_apy   # OPUL (example)
        }
        return pool_mapping.get(asset_id, Decimal('0'))

    def get_total_apy(self, asset_id: int) -> Decimal:
        """Get total APY including base rate and rewards"""
        base_apy = self.get_pool_apy(asset_id)

        # Add FOLKS token rewards for all pools
        reward_apy = self.folks_rewards_apy

        # Special case for ALGO - add xALGO liquid staking component
        if asset_id == 0:
            reward_apy += self.algo_rewards_apy

        return base_apy + reward_apy


class FolksFinanceClient:
    """
    Folks Finance protocol client for DeFi yield analysis.

    Provides access to lending pools, governance staking,
    and liquid staking opportunities on Folks Finance.
    """

    def __init__(self, algorand_client=None):
        self.algorand_client = algorand_client
        self._cache: Dict[str, Any] = {}
        self._cache_timeout = 300  # 5 minutes

        # Folks Finance protocol configuration
        self.protocol_config = {
            'name': 'Folks Finance',
            'type': 'lending_and_staking',
            'main_app_id': 234567890,  # Main Folks Finance app ID
            'supported_assets': {
                0: 'ALGO',
                31566704: 'USDC',
                312769: 'USDT',
                287867876: 'OPUL'
            },
            'governance_token': 'FOLKS',
            'governance_token_id': 345678901,
            'xalgo_token_id': 456789012  # xALGO liquid staking token
        }

    async def connect(self) -> bool:
        """Initialize connection to Folks Finance protocol"""
        try:
            status = await self.get_protocol_status()
            logger.info(f"Connected to Folks Finance - TVL: ${status.get('tvl', 0):,.2f}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Folks Finance: {e}")
            return False

    async def get_current_rates(self) -> FolksRates:
        """
        Get current rates from all Folks Finance pools and staking.

        Returns comprehensive rate data including lending pools,
        governance staking, and liquid staking yields.
        """
        cache_key = "current_rates"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_timeout:
                return cached_data

        try:
            # Fetch rates from various Folks Finance components
            pool_rates = await self._fetch_pool_rates()
            staking_rates = await self._fetch_staking_rates()
            reward_rates = await self._fetch_reward_rates()

            rates = FolksRates(
                timestamp=datetime.now(),
                algo_pool_apy=pool_rates.get('algo_apy', Decimal('0.055')),    # Mock 5.5%
                usdc_pool_apy=pool_rates.get('usdc_apy', Decimal('0.09')),     # Mock 9%
                usdt_pool_apy=pool_rates.get('usdt_apy', Decimal('0.085')),    # Mock 8.5%
                opul_pool_apy=pool_rates.get('opul_apy', Decimal('0.12')),     # Mock 12%
                folks_staking_apy=staking_rates.get('folks_apy', Decimal('0.25')), # Mock 25%
                xalgo_apy=staking_rates.get('xalgo_apy', Decimal('0.06')),     # Mock 6%
                algo_rewards_apy=reward_rates.get('algo_rewards', Decimal('0.08')), # Mock 8%
                folks_rewards_apy=reward_rates.get('folks_rewards', Decimal('0.15')), # Mock 15%
                total_value_locked=pool_rates.get('tvl', Decimal('25000000')), # Mock $25M
                folks_token_price=staking_rates.get('folks_price', Decimal('0.15')), # Mock $0.15
                daily_volume=pool_rates.get('volume_24h', Decimal('2000000'))  # Mock $2M
            )

            # Add pool utilization data
            rates.total_deposits = pool_rates.get('deposits', {})
            rates.total_borrowed = pool_rates.get('borrowed', {})
            rates.pool_utilization = pool_rates.get('utilization', {})

            self._cache[cache_key] = (rates, datetime.now())
            return rates

        except Exception as e:
            logger.error(f"Error fetching Folks Finance rates: {e}")
            raise

    async def get_liquid_staking_data(self) -> Dict[str, Any]:
        """
        Get xALGO liquid staking metrics and opportunities.

        Returns detailed information about liquid ALGO staking
        including conversion rates, yields, and liquidity.
        """
        try:
            staking_data = await self._fetch_xalgo_data()

            return {
                'xalgo_to_algo_rate': staking_data.get('exchange_rate', Decimal('1.05')), # Mock 5% premium
                'current_apy': staking_data.get('apy', Decimal('0.06')),  # Mock 6% APY
                'total_algo_staked': staking_data.get('total_staked', Decimal('5000000')), # 5M ALGO
                'total_xalgo_supply': staking_data.get('xalgo_supply', Decimal('4761904')), # Calculated
                'liquidity_pools': [
                    {
                        'pool': 'xALGO/ALGO',
                        'liquidity_usd': Decimal('500000'),  # $500k liquidity
                        'volume_24h': Decimal('100000'),     # $100k volume
                        'fee_apy': Decimal('0.025')          # 2.5% fee APY
                    },
                    {
                        'pool': 'xALGO/USDC',
                        'liquidity_usd': Decimal('300000'),
                        'volume_24h': Decimal('50000'),
                        'fee_apy': Decimal('0.02')
                    }
                ],
                'compound_frequency': 'daily',
                'unbonding_period_days': 0,  # Liquid - no unbonding
                'slashing_risk': False       # No slashing risk
            }

        except Exception as e:
            logger.error(f"Error getting liquid staking data: {e}")
            raise

    async def get_governance_staking(self) -> Dict[str, Any]:
        """
        Get FOLKS token governance staking information.

        Returns staking rewards, lock periods, and governance benefits.
        """
        try:
            governance_data = await self._fetch_governance_data()

            return {
                'staking_apy': governance_data.get('apy', Decimal('0.25')),  # 25% APY
                'total_staked': governance_data.get('total_staked', Decimal('10000000')), # 10M FOLKS
                'staking_ratio': governance_data.get('staking_ratio', 0.4),  # 40% of supply staked
                'lock_periods': [
                    {'duration_days': 30, 'multiplier': 1.0},
                    {'duration_days': 90, 'multiplier': 1.2},
                    {'duration_days': 180, 'multiplier': 1.5},
                    {'duration_days': 365, 'multiplier': 2.0}
                ],
                'governance_benefits': {
                    'voting_power': True,
                    'proposal_creation': True,  # For large stakers
                    'protocol_fee_share': True,
                    'early_access_features': True
                },
                'reward_distribution': 'weekly',
                'auto_compound': True
            }

        except Exception as e:
            logger.error(f"Error getting governance staking data: {e}")
            raise

    async def get_yield_opportunities(self) -> List[DeFiYield]:
        """Get all yield opportunities available on Folks Finance"""
        try:
            rates = await self.get_current_rates()
            opportunities = []

            # Lending pool opportunities
            for asset_id, asset_name in self.protocol_config['supported_assets'].items():
                pool_apy = rates.get_pool_apy(asset_id)
                total_apy = rates.get_total_apy(asset_id)

                if pool_apy > 0:
                    yield_opp = DeFiYield(
                        protocol="Folks Finance",
                        strategy_name=f"{asset_name} Lending Pool",
                        asset_id=asset_id,
                        current_apy=total_apy,
                        strategy_risk_level="low" if asset_name in ['USDC', 'USDT'] else "medium",
                        smart_contract_risk=0.25,  # Slightly higher than Algofi (newer)
                        liquidity_risk=0.15,
                        min_deposit_amount=Decimal('1'),
                        reward_tokens=[self.protocol_config['governance_token_id']],
                        compounding_frequency="daily",
                        auto_compound=True,
                        total_value_locked=rates.total_deposits.get(asset_id, Decimal('0'))
                    )
                    opportunities.append(yield_opp)

            # xALGO liquid staking
            xalgo_yield = DeFiYield(
                protocol="Folks Finance",
                strategy_name="xALGO Liquid Staking",
                asset_id=0,  # ALGO
                current_apy=rates.xalgo_apy,
                strategy_risk_level="low",
                smart_contract_risk=0.2,
                liquidity_risk=0.1,  # Liquid - can exit anytime
                min_deposit_amount=Decimal('1'),
                lock_period_days=0,  # No lock period
                reward_tokens=[],  # Native ALGO rewards
                compounding_frequency="daily",
                auto_compound=True,
                total_value_locked=Decimal('5000000')  # Mock TVL
            )
            opportunities.append(xalgo_yield)

            # FOLKS governance staking
            folks_yield = DeFiYield(
                protocol="Folks Finance",
                strategy_name="FOLKS Governance Staking",
                asset_id=self.protocol_config['governance_token_id'],
                current_apy=rates.folks_staking_apy,
                strategy_risk_level="medium",
                smart_contract_risk=0.3,
                liquidity_risk=0.5,  # Higher due to lock periods
                min_deposit_amount=Decimal('100'),  # 100 FOLKS minimum
                lock_period_days=30,  # Minimum lock period
                reward_tokens=[self.protocol_config['governance_token_id']],
                compounding_frequency="weekly",
                auto_compound=True,
                total_value_locked=Decimal('1500000')  # Mock TVL
            )
            opportunities.append(folks_yield)

            return opportunities

        except Exception as e:
            logger.error(f"Error getting yield opportunities: {e}")
            raise

    async def get_pool_analytics(self, asset_id: int) -> Dict[str, Any]:
        """Get detailed analytics for a specific lending pool"""
        try:
            pool_data = await self._fetch_pool_analytics(asset_id)
            rates = await self.get_current_rates()

            analytics = {
                'asset_id': asset_id,
                'total_deposits': pool_data.get('deposits', Decimal('0')),
                'total_borrowed': pool_data.get('borrowed', Decimal('0')),
                'utilization_rate': pool_data.get('utilization', Decimal('0')),
                'deposit_apy': rates.get_pool_apy(asset_id),
                'borrow_apy': pool_data.get('borrow_apy', Decimal('0')),
                'reserve_factor': pool_data.get('reserve_factor', Decimal('0.1')),
                'unique_depositors': pool_data.get('depositors', 0),
                'unique_borrowers': pool_data.get('borrowers', 0),
                'average_deposit_size': pool_data.get('avg_deposit', Decimal('0')),
                'largest_deposit': pool_data.get('max_deposit', Decimal('0')),
                'pool_age_days': pool_data.get('age_days', 0),
                'historical_performance': {
                    'avg_apy_30d': pool_data.get('avg_apy_30d', Decimal('0')),
                    'max_apy_30d': pool_data.get('max_apy_30d', Decimal('0')),
                    'min_apy_30d': pool_data.get('min_apy_30d', Decimal('0')),
                    'volatility_30d': pool_data.get('volatility_30d', Decimal('0'))
                }
            }

            return analytics

        except Exception as e:
            logger.error(f"Error getting pool analytics for asset {asset_id}: {e}")
            raise

    async def get_protocol_status(self) -> Dict[str, Any]:
        """Get overall protocol status and health metrics"""
        try:
            return {
                'tvl': 25000000,  # $25M TVL
                'total_users': 8000,
                'total_pools': 4,
                'governance_participation': 0.35,  # 35% of tokens staked
                'protocol_age_days': 180,
                'last_update': datetime.now(),
                'health_score': 0.9  # 90% health score
            }
        except Exception as e:
            logger.error(f"Error getting protocol status: {e}")
            raise

    async def _fetch_pool_rates(self) -> Dict[str, Any]:
        """Fetch current pool rates from smart contracts"""
        # Mock implementation
        return {
            'algo_apy': Decimal('0.055'),
            'usdc_apy': Decimal('0.09'),
            'usdt_apy': Decimal('0.085'),
            'opul_apy': Decimal('0.12'),
            'tvl': Decimal('25000000'),
            'volume_24h': Decimal('2000000'),
            'deposits': {
                0: Decimal('10000000'),        # 10M ALGO
                31566704: Decimal('8000000'),  # $8M USDC
                312769: Decimal('5000000'),    # $5M USDT
                287867876: Decimal('2000000')  # $2M OPUL equivalent
            },
            'borrowed': {
                0: Decimal('6000000'),         # 6M ALGO borrowed
                31566704: Decimal('6000000'),  # $6M USDC borrowed
                312769: Decimal('4000000'),    # $4M USDT borrowed
                287867876: Decimal('1000000')  # $1M OPUL borrowed
            },
            'utilization': {
                0: Decimal('0.6'),        # 60%
                31566704: Decimal('0.75'), # 75%
                312769: Decimal('0.8'),   # 80%
                287867876: Decimal('0.5') # 50%
            }
        }

    async def _fetch_staking_rates(self) -> Dict[str, Any]:
        """Fetch staking rates from governance contracts"""
        # Mock implementation
        return {
            'folks_apy': Decimal('0.25'),      # 25% FOLKS staking
            'xalgo_apy': Decimal('0.06'),      # 6% xALGO staking
            'folks_price': Decimal('0.15')     # $0.15 FOLKS price
        }

    async def _fetch_reward_rates(self) -> Dict[str, Any]:
        """Fetch liquidity mining reward rates"""
        # Mock implementation
        return {
            'algo_rewards': Decimal('0.08'),   # 8% additional ALGO rewards
            'folks_rewards': Decimal('0.15')   # 15% FOLKS token rewards
        }

    async def _fetch_xalgo_data(self) -> Dict[str, Any]:
        """Fetch xALGO liquid staking data"""
        # Mock implementation
        return {
            'exchange_rate': Decimal('1.05'),      # 1 xALGO = 1.05 ALGO
            'apy': Decimal('0.06'),                # 6% APY
            'total_staked': Decimal('5000000'),    # 5M ALGO staked
            'xalgo_supply': Decimal('4761904')     # xALGO supply
        }

    async def _fetch_governance_data(self) -> Dict[str, Any]:
        """Fetch governance staking data"""
        # Mock implementation
        return {
            'apy': Decimal('0.25'),                # 25% APY
            'total_staked': Decimal('10000000'),   # 10M FOLKS staked
            'staking_ratio': 0.4                   # 40% of supply
        }

    async def _fetch_pool_analytics(self, asset_id: int) -> Dict[str, Any]:
        """Fetch detailed analytics for a pool"""
        # Mock implementation
        mock_data = {
            0: {  # ALGO
                'deposits': Decimal('10000000'),
                'borrowed': Decimal('6000000'),
                'utilization': Decimal('0.6'),
                'borrow_apy': Decimal('0.08'),
                'reserve_factor': Decimal('0.1'),
                'depositors': 2500,
                'borrowers': 800,
                'avg_deposit': Decimal('4000'),
                'max_deposit': Decimal('500000'),
                'age_days': 180,
                'avg_apy_30d': Decimal('0.052'),
                'max_apy_30d': Decimal('0.065'),
                'min_apy_30d': Decimal('0.045'),
                'volatility_30d': Decimal('0.015')
            }
        }
        return mock_data.get(asset_id, {})

    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()