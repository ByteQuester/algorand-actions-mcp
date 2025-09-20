"""
Algofi protocol client for lending/borrowing rates and liquidity data.

Provides integration with Algofi lending protocol including:
- Current lending and borrowing rates
- Protocol utilization metrics
- Liquidity pool data
- User position analysis
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
class AlgofiRates:
    """Algofi protocol rates and metrics"""
    timestamp: datetime

    # Lending rates (APY that suppliers earn)
    algo_supply_apy: Decimal = Decimal('0')
    usdc_supply_apy: Decimal = Decimal('0')
    usdt_supply_apy: Decimal = Decimal('0')

    # Borrowing rates (APY that borrowers pay)
    algo_borrow_apy: Decimal = Decimal('0')
    usdc_borrow_apy: Decimal = Decimal('0')
    usdt_borrow_apy: Decimal = Decimal('0')

    # Utilization rates
    algo_utilization: Decimal = Decimal('0')
    usdc_utilization: Decimal = Decimal('0')
    usdt_utilization: Decimal = Decimal('0')

    # Protocol metrics
    total_value_locked: Decimal = Decimal('0')
    total_borrowed: Decimal = Decimal('0')
    protocol_revenue_24h: Decimal = Decimal('0')

    # Governance token rewards
    algo_governance_rewards: bool = False
    reward_token_apy: Decimal = Decimal('0')

    @property
    def algo_spread(self) -> Decimal:
        """Calculate spread between borrowing and lending rates for ALGO"""
        return self.algo_borrow_apy - self.algo_supply_apy

    @property
    def usdc_spread(self) -> Decimal:
        """Calculate spread between borrowing and lending rates for USDC"""
        return self.usdc_borrow_apy - self.usdc_supply_apy

    def get_asset_rates(self, asset_id: int) -> Dict[str, Decimal]:
        """Get rates for specific asset by ID"""
        # Map common asset IDs to rates
        asset_mapping = {
            0: {  # ALGO
                'supply_apy': self.algo_supply_apy,
                'borrow_apy': self.algo_borrow_apy,
                'utilization': self.algo_utilization
            },
            31566704: {  # USDC (example ID)
                'supply_apy': self.usdc_supply_apy,
                'borrow_apy': self.usdc_borrow_apy,
                'utilization': self.usdc_utilization
            },
            312769: {  # USDT (example ID)
                'supply_apy': self.usdt_supply_apy,
                'borrow_apy': self.usdt_borrow_apy,
                'utilization': self.usdt_utilization
            }
        }

        return asset_mapping.get(asset_id, {
            'supply_apy': Decimal('0'),
            'borrow_apy': Decimal('0'),
            'utilization': Decimal('0')
        })


class AlgofiClient:
    """
    Algofi protocol client for DeFi rate analysis.

    Provides real-time and historical data from Algofi lending protocol
    for interest rate determination and risk assessment.
    """

    def __init__(self, algorand_client=None):
        self.algorand_client = algorand_client
        self._cache: Dict[str, Any] = {}
        self._cache_timeout = 300  # 5 minutes

        # Algofi protocol configuration
        self.protocol_config = {
            'name': 'Algofi',
            'type': 'lending',
            'main_app_id': 123456789,  # Main Algofi app ID
            'supported_assets': {
                0: 'ALGO',
                31566704: 'USDC',
                312769: 'USDT'
            },
            'governance_token': 'BANK',
            'governance_token_id': 234567890
        }

    async def connect(self) -> bool:
        """Initialize connection to Algofi protocol"""
        try:
            # Test connection by fetching protocol status
            status = await self.get_protocol_status()
            logger.info(f"Connected to Algofi protocol - TVL: ${status.get('tvl', 0):,.2f}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Algofi: {e}")
            return False

    async def get_current_rates(self) -> AlgofiRates:
        """
        Get current lending and borrowing rates from Algofi.

        Returns real-time rates for all supported assets.
        """
        cache_key = "current_rates"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_timeout:
                return cached_data

        try:
            # Fetch current rates from Algofi smart contracts
            rates_data = await self._fetch_protocol_rates()

            rates = AlgofiRates(
                timestamp=datetime.now(),
                algo_supply_apy=rates_data.get('algo_supply_apy', Decimal('0.045')),  # Mock 4.5%
                usdc_supply_apy=rates_data.get('usdc_supply_apy', Decimal('0.08')),   # Mock 8%
                usdt_supply_apy=rates_data.get('usdt_supply_apy', Decimal('0.075')), # Mock 7.5%
                algo_borrow_apy=rates_data.get('algo_borrow_apy', Decimal('0.065')), # Mock 6.5%
                usdc_borrow_apy=rates_data.get('usdc_borrow_apy', Decimal('0.12')),  # Mock 12%
                usdt_borrow_apy=rates_data.get('usdt_borrow_apy', Decimal('0.115')), # Mock 11.5%
                algo_utilization=rates_data.get('algo_utilization', Decimal('0.7')), # Mock 70%
                usdc_utilization=rates_data.get('usdc_utilization', Decimal('0.85')), # Mock 85%
                usdt_utilization=rates_data.get('usdt_utilization', Decimal('0.9')), # Mock 90%
                total_value_locked=rates_data.get('tvl', Decimal('50000000')),      # Mock $50M
                total_borrowed=rates_data.get('total_borrowed', Decimal('35000000')), # Mock $35M
                protocol_revenue_24h=rates_data.get('revenue_24h', Decimal('50000')), # Mock $50k
                reward_token_apy=rates_data.get('bank_apy', Decimal('0.15'))        # Mock 15%
            )

            self._cache[cache_key] = (rates, datetime.now())
            return rates

        except Exception as e:
            logger.error(f"Error fetching Algofi rates: {e}")
            raise

    async def get_asset_rates(self, asset_id: int) -> Dict[str, Decimal]:
        """Get rates for a specific asset"""
        rates = await self.get_current_rates()
        return rates.get_asset_rates(asset_id)

    async def get_utilization_rate(self, asset_id: int) -> Decimal:
        """Get current utilization rate for an asset"""
        asset_rates = await self.get_asset_rates(asset_id)
        return asset_rates.get('utilization', Decimal('0'))

    async def get_available_liquidity(self, asset_id: int) -> Decimal:
        """Get available liquidity for borrowing"""
        try:
            protocol_data = await self._fetch_asset_data(asset_id)
            total_supplied = protocol_data.get('total_supplied', Decimal('0'))
            total_borrowed = protocol_data.get('total_borrowed', Decimal('0'))
            return total_supplied - total_borrowed
        except Exception as e:
            logger.error(f"Error getting liquidity for asset {asset_id}: {e}")
            return Decimal('0')

    async def get_protocol_status(self) -> Dict[str, Any]:
        """Get overall protocol status and metrics"""
        try:
            # Mock implementation
            return {
                'tvl': 50000000,  # $50M TVL
                'total_borrowed': 35000000,  # $35M borrowed
                'total_suppliers': 15000,
                'total_borrowers': 8000,
                'protocol_age_days': 365,
                'last_update': datetime.now(),
                'health_score': 0.95  # 95% health score
            }
        except Exception as e:
            logger.error(f"Error getting protocol status: {e}")
            raise

    async def get_user_position(self, address: str) -> Dict[str, Any]:
        """Get user's position in Algofi protocol"""
        try:
            # Query user's positions across all markets
            position_data = await self._fetch_user_data(address)

            position = {
                'total_supplied_usd': position_data.get('supplied', Decimal('0')),
                'total_borrowed_usd': position_data.get('borrowed', Decimal('0')),
                'net_apy': position_data.get('net_apy', Decimal('0')),
                'health_factor': position_data.get('health_factor', Decimal('1.5')),
                'liquidation_threshold': position_data.get('liquidation_threshold', Decimal('0.8')),
                'positions': []
            }

            # Add individual asset positions
            for asset_id in self.protocol_config['supported_assets']:
                asset_position = position_data.get(f'asset_{asset_id}', {})
                if asset_position:
                    position['positions'].append({
                        'asset_id': asset_id,
                        'supplied_amount': asset_position.get('supplied', Decimal('0')),
                        'borrowed_amount': asset_position.get('borrowed', Decimal('0')),
                        'collateral_enabled': asset_position.get('collateral', False)
                    })

            return position

        except Exception as e:
            logger.error(f"Error getting user position for {address}: {e}")
            raise

    async def get_yield_opportunities(self) -> List[DeFiYield]:
        """Get current yield farming opportunities in Algofi"""
        try:
            rates = await self.get_current_rates()
            opportunities = []

            # ALGO lending opportunity
            algo_yield = DeFiYield(
                protocol="Algofi",
                strategy_name="ALGO Lending",
                asset_id=0,
                current_apy=rates.algo_supply_apy + rates.reward_token_apy,
                strategy_risk_level="low",
                smart_contract_risk=0.2,  # Low risk - established protocol
                liquidity_risk=0.1,       # Low risk - high liquidity
                min_deposit_amount=Decimal('1'),  # 1 ALGO minimum
                reward_tokens=[self.protocol_config['governance_token_id']],
                total_value_locked=rates.total_value_locked * Decimal('0.4')  # 40% in ALGO
            )
            opportunities.append(algo_yield)

            # USDC lending opportunity
            usdc_yield = DeFiYield(
                protocol="Algofi",
                strategy_name="USDC Lending",
                asset_id=31566704,
                current_apy=rates.usdc_supply_apy + rates.reward_token_apy,
                strategy_risk_level="very_low",  # Stablecoin
                smart_contract_risk=0.2,
                liquidity_risk=0.05,  # Very low risk
                min_deposit_amount=Decimal('10'),  # $10 minimum
                reward_tokens=[self.protocol_config['governance_token_id']],
                total_value_locked=rates.total_value_locked * Decimal('0.35')  # 35% in USDC
            )
            opportunities.append(usdc_yield)

            return opportunities

        except Exception as e:
            logger.error(f"Error getting yield opportunities: {e}")
            raise

    async def calculate_borrowing_cost(
        self,
        asset_id: int,
        amount: Decimal,
        duration_days: int
    ) -> Dict[str, Decimal]:
        """Calculate total borrowing cost for specified amount and duration"""
        try:
            asset_rates = await self.get_asset_rates(asset_id)
            borrow_apy = asset_rates['borrow_apy']

            # Calculate daily rate
            daily_rate = borrow_apy / Decimal('365')

            # Calculate total interest for duration
            total_interest = amount * daily_rate * Decimal(str(duration_days))

            # Add protocol fees (mock 0.1% origination fee)
            origination_fee = amount * Decimal('0.001')

            return {
                'principal': amount,
                'interest': total_interest,
                'origination_fee': origination_fee,
                'total_cost': total_interest + origination_fee,
                'effective_apy': borrow_apy + (origination_fee / amount) * (Decimal('365') / Decimal(str(duration_days)))
            }

        except Exception as e:
            logger.error(f"Error calculating borrowing cost: {e}")
            raise

    async def _fetch_protocol_rates(self) -> Dict[str, Decimal]:
        """Fetch current rates from Algofi smart contracts"""
        # Mock implementation - would query actual smart contracts
        return {
            'algo_supply_apy': Decimal('0.045'),
            'usdc_supply_apy': Decimal('0.08'),
            'usdt_supply_apy': Decimal('0.075'),
            'algo_borrow_apy': Decimal('0.065'),
            'usdc_borrow_apy': Decimal('0.12'),
            'usdt_borrow_apy': Decimal('0.115'),
            'algo_utilization': Decimal('0.7'),
            'usdc_utilization': Decimal('0.85'),
            'usdt_utilization': Decimal('0.9'),
            'tvl': Decimal('50000000'),
            'total_borrowed': Decimal('35000000'),
            'revenue_24h': Decimal('50000'),
            'bank_apy': Decimal('0.15')
        }

    async def _fetch_asset_data(self, asset_id: int) -> Dict[str, Decimal]:
        """Fetch detailed data for specific asset"""
        # Mock implementation
        mock_data = {
            0: {  # ALGO
                'total_supplied': Decimal('20000000'),
                'total_borrowed': Decimal('14000000'),
                'reserve_factor': Decimal('0.1')
            },
            31566704: {  # USDC
                'total_supplied': Decimal('17500000'),
                'total_borrowed': Decimal('14875000'),
                'reserve_factor': Decimal('0.1')
            }
        }
        return mock_data.get(asset_id, {})

    async def _fetch_user_data(self, address: str) -> Dict[str, Any]:
        """Fetch user position data from smart contracts"""
        # Mock implementation
        return {
            'supplied': Decimal('5000'),  # $5k supplied
            'borrowed': Decimal('2000'),  # $2k borrowed
            'net_apy': Decimal('0.035'),  # 3.5% net APY
            'health_factor': Decimal('2.1'),  # 2.1 health factor
            'liquidation_threshold': Decimal('0.8'),
            'asset_0': {  # ALGO position
                'supplied': Decimal('100'),  # 100 ALGO
                'borrowed': Decimal('0'),
                'collateral': True
            },
            'asset_31566704': {  # USDC position
                'supplied': Decimal('1000'),  # $1000 USDC
                'borrowed': Decimal('500'),   # $500 USDC borrowed
                'collateral': True
            }
        }

    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()