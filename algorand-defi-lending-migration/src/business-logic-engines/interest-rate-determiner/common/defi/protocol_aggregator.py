"""
DeFi protocol aggregator for cross-protocol rate comparison and optimization.

Aggregates data from multiple DeFi protocols to provide:
- Best rate discovery across protocols
- Risk-adjusted yield comparisons
- Protocol health monitoring
- Yield optimization strategies
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum
import logging

from .algofi_client import AlgofiClient, AlgofiRates
from .folks_finance_client import FolksFinanceClient, FolksRates
from .tinyman_client import TinymanClient, TinymanPools
from ..models.defi_models import DeFiYield, ProtocolComparison

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of DeFi strategies"""
    LENDING = "lending"
    BORROWING = "borrowing"
    LIQUIDITY_PROVISION = "liquidity_provision"
    YIELD_FARMING = "yield_farming"
    STAKING = "staking"
    ARBITRAGE = "arbitrage"


@dataclass
class AggregatedRates:
    """Aggregated rates across all protocols"""
    timestamp: datetime
    asset_id: int

    # Best rates across protocols
    best_lending_rate: Decimal = Decimal('0')
    best_lending_protocol: str = ""
    best_borrowing_rate: Decimal = Decimal('0')  # Lowest rate
    best_borrowing_protocol: str = ""

    # Protocol rates
    protocol_rates: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)

    # Risk-adjusted rankings
    risk_adjusted_lending: List[Tuple[str, Decimal]] = field(default_factory=list)
    risk_adjusted_borrowing: List[Tuple[str, Decimal]] = field(default_factory=list)

    # Market metrics
    total_liquidity_across_protocols: Decimal = Decimal('0')
    average_utilization: Decimal = Decimal('0')
    rate_volatility: Decimal = Decimal('0')

    def get_rate_spread(self) -> Decimal:
        """Calculate spread between best lending and borrowing rates"""
        return self.best_borrowing_rate - self.best_lending_rate

    def get_protocol_comparison(self) -> ProtocolComparison:
        """Get comparison object for this asset"""
        protocols = list(self.protocol_rates.keys())
        lending_rates = [self.protocol_rates[p].get('lending', Decimal('0')) for p in protocols]
        borrowing_rates = [self.protocol_rates[p].get('borrowing', Decimal('0')) for p in protocols]

        return ProtocolComparison(
            asset_id=self.asset_id,
            comparison_timestamp=self.timestamp,
            protocols=protocols,
            lending_rates=lending_rates,
            borrowing_rates=borrowing_rates
        )


class ProtocolAggregator:
    """
    Multi-protocol DeFi aggregator for Algorand ecosystem.

    Provides unified access to rates, yields, and opportunities
    across all major DeFi protocols on Algorand.
    """

    def __init__(self, algorand_client=None):
        self.algorand_client = algorand_client

        # Initialize protocol clients
        self.algofi = AlgofiClient(algorand_client)
        self.folks_finance = FolksFinanceClient(algorand_client)
        self.tinyman = TinymanClient(algorand_client)

        # Cache for aggregated data
        self._cache: Dict[str, Any] = {}
        self._cache_timeout = 300  # 5 minutes

        # Protocol weights for risk assessment
        self.protocol_weights = {
            'Algofi': {
                'security_score': 0.9,   # High security
                'liquidity_score': 0.85, # Good liquidity
                'maturity_score': 0.95   # Very mature
            },
            'Folks Finance': {
                'security_score': 0.8,   # Good security
                'liquidity_score': 0.75, # Moderate liquidity
                'maturity_score': 0.7    # Less mature
            },
            'Tinyman': {
                'security_score': 0.85,  # Good security
                'liquidity_score': 0.9,  # Excellent liquidity
                'maturity_score': 0.9    # Mature DEX
            }
        }

    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all protocols and return connection status"""
        connections = {}

        try:
            connections['Algofi'] = await self.algofi.connect()
        except Exception as e:
            logger.warning(f"Failed to connect to Algofi: {e}")
            connections['Algofi'] = False

        try:
            connections['Folks Finance'] = await self.folks_finance.connect()
        except Exception as e:
            logger.warning(f"Failed to connect to Folks Finance: {e}")
            connections['Folks Finance'] = False

        try:
            connections['Tinyman'] = await self.tinyman.connect()
        except Exception as e:
            logger.warning(f"Failed to connect to Tinyman: {e}")
            connections['Tinyman'] = False

        logger.info(f"Protocol connections: {connections}")
        return connections

    async def get_aggregated_rates(self, asset_id: int) -> AggregatedRates:
        """
        Get aggregated rates for an asset across all protocols.

        Returns best rates, protocol comparison, and risk-adjusted rankings.
        """
        cache_key = f"aggregated_rates_{asset_id}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_timeout:
                return cached_data

        try:
            # Fetch rates from all protocols concurrently
            algofi_task = self._safe_get_algofi_rates(asset_id)
            folks_task = self._safe_get_folks_rates(asset_id)

            algofi_rates, folks_rates = await asyncio.gather(
                algofi_task, folks_task, return_exceptions=True
            )

            # Build aggregated rates
            aggregated = AggregatedRates(
                timestamp=datetime.now(),
                asset_id=asset_id
            )

            protocol_data = {}

            # Process Algofi rates
            if isinstance(algofi_rates, dict) and algofi_rates:
                lending_rate = algofi_rates.get('supply_apy', Decimal('0'))
                borrowing_rate = algofi_rates.get('borrow_apy', Decimal('0'))

                protocol_data['Algofi'] = {
                    'lending': lending_rate,
                    'borrowing': borrowing_rate,
                    'utilization': algofi_rates.get('utilization', Decimal('0'))
                }

                # Update best rates
                if lending_rate > aggregated.best_lending_rate:
                    aggregated.best_lending_rate = lending_rate
                    aggregated.best_lending_protocol = 'Algofi'

                if borrowing_rate > 0 and (aggregated.best_borrowing_rate == 0 or borrowing_rate < aggregated.best_borrowing_rate):
                    aggregated.best_borrowing_rate = borrowing_rate
                    aggregated.best_borrowing_protocol = 'Algofi'

            # Process Folks Finance rates
            if isinstance(folks_rates, dict) and folks_rates:
                lending_rate = folks_rates.get('pool_apy', Decimal('0'))
                total_apy = folks_rates.get('total_apy', Decimal('0'))

                protocol_data['Folks Finance'] = {
                    'lending': lending_rate,
                    'lending_with_rewards': total_apy,
                    'borrowing': Decimal('0'),  # Folks is primarily lending
                    'utilization': folks_rates.get('utilization', Decimal('0'))
                }

                # Update best rates (use total APY including rewards)
                if total_apy > aggregated.best_lending_rate:
                    aggregated.best_lending_rate = total_apy
                    aggregated.best_lending_protocol = 'Folks Finance'

            aggregated.protocol_rates = protocol_data

            # Calculate risk-adjusted rankings
            await self._calculate_risk_adjusted_rankings(aggregated)

            # Cache the result
            self._cache[cache_key] = (aggregated, datetime.now())
            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating rates for asset {asset_id}: {e}")
            raise

    async def get_all_yield_opportunities(self) -> List[DeFiYield]:
        """
        Get all yield opportunities across all protocols.

        Returns comprehensive list of yield farming, lending,
        and staking opportunities ranked by risk-adjusted yield.
        """
        try:
            opportunities = []

            # Fetch opportunities from all protocols
            tasks = [
                self._safe_get_algofi_opportunities(),
                self._safe_get_folks_opportunities(),
                self._safe_get_tinyman_opportunities()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    opportunities.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Error fetching opportunities: {result}")

            # Sort by risk-adjusted yield
            opportunities.sort(key=lambda x: x.risk_adjusted_yield, reverse=True)

            return opportunities

        except Exception as e:
            logger.error(f"Error getting all yield opportunities: {e}")
            raise

    async def find_best_strategy(
        self,
        strategy_type: StrategyType,
        asset_id: int,
        amount: Decimal,
        risk_tolerance: str = "medium"  # "low", "medium", "high"
    ) -> Dict[str, Any]:
        """
        Find the best strategy for a given asset and amount.

        Returns optimized strategy recommendation based on
        risk tolerance and expected returns.
        """
        try:
            if strategy_type == StrategyType.LENDING:
                return await self._find_best_lending_strategy(asset_id, amount, risk_tolerance)
            elif strategy_type == StrategyType.BORROWING:
                return await self._find_best_borrowing_strategy(asset_id, amount, risk_tolerance)
            elif strategy_type == StrategyType.LIQUIDITY_PROVISION:
                return await self._find_best_lp_strategy(asset_id, amount, risk_tolerance)
            elif strategy_type == StrategyType.YIELD_FARMING:
                return await self._find_best_yield_strategy(asset_id, amount, risk_tolerance)
            else:
                raise ValueError(f"Unsupported strategy type: {strategy_type}")

        except Exception as e:
            logger.error(f"Error finding best strategy: {e}")
            raise

    async def get_protocol_health_scores(self) -> Dict[str, Dict[str, float]]:
        """
        Get health scores for all protocols.

        Returns comprehensive health assessment including
        security, liquidity, and operational metrics.
        """
        try:
            health_scores = {}

            # Algofi health
            try:
                algofi_status = await self.algofi.get_protocol_status()
                health_scores['Algofi'] = {
                    'overall_score': algofi_status.get('health_score', 0.9),
                    'tvl_score': min(1.0, float(algofi_status.get('tvl', 0)) / 100000000),  # Normalize by $100M
                    'utilization_score': 0.8,  # Mock score
                    'security_score': self.protocol_weights['Algofi']['security_score'],
                    'maturity_score': self.protocol_weights['Algofi']['maturity_score']
                }
            except Exception:
                health_scores['Algofi'] = {'overall_score': 0.0}

            # Folks Finance health
            try:
                folks_status = await self.folks_finance.get_protocol_status()
                health_scores['Folks Finance'] = {
                    'overall_score': folks_status.get('health_score', 0.85),
                    'tvl_score': min(1.0, float(folks_status.get('tvl', 0)) / 50000000),  # Normalize by $50M
                    'utilization_score': 0.75,
                    'security_score': self.protocol_weights['Folks Finance']['security_score'],
                    'maturity_score': self.protocol_weights['Folks Finance']['maturity_score']
                }
            except Exception:
                health_scores['Folks Finance'] = {'overall_score': 0.0}

            # Tinyman health
            try:
                tinyman_status = await self.tinyman.get_protocol_status()
                health_scores['Tinyman'] = {
                    'overall_score': 0.9,  # Generally very healthy
                    'tvl_score': min(1.0, float(tinyman_status.get('tvl', 0)) / 75000000),  # Normalize by $75M
                    'volume_score': min(1.0, float(tinyman_status.get('volume_24h', 0)) / 5000000),  # Normalize by $5M daily
                    'security_score': self.protocol_weights['Tinyman']['security_score'],
                    'maturity_score': self.protocol_weights['Tinyman']['maturity_score']
                }
            except Exception:
                health_scores['Tinyman'] = {'overall_score': 0.0}

            return health_scores

        except Exception as e:
            logger.error(f"Error getting protocol health scores: {e}")
            raise

    async def monitor_rate_changes(self, asset_id: int, threshold_pct: float = 5.0) -> Dict[str, Any]:
        """
        Monitor rate changes across protocols for significant movements.

        Returns alerts for rate changes above the threshold percentage.
        """
        try:
            # Get current rates
            current_rates = await self.get_aggregated_rates(asset_id)

            # Get historical rates (mock implementation)
            historical_rates = await self._get_historical_rates(asset_id)

            alerts = []

            for protocol, rates in current_rates.protocol_rates.items():
                if protocol in historical_rates:
                    historical = historical_rates[protocol]

                    # Check lending rate changes
                    if 'lending' in rates and 'lending' in historical:
                        current_lending = rates['lending']
                        historical_lending = historical['lending']

                        if historical_lending > 0:
                            change_pct = abs(current_lending - historical_lending) / historical_lending * 100

                            if change_pct > threshold_pct:
                                alerts.append({
                                    'protocol': protocol,
                                    'type': 'lending_rate_change',
                                    'change_pct': float(change_pct),
                                    'current_rate': float(current_lending),
                                    'previous_rate': float(historical_lending),
                                    'direction': 'up' if current_lending > historical_lending else 'down'
                                })

            return {
                'asset_id': asset_id,
                'alerts': alerts,
                'monitoring_threshold': threshold_pct,
                'timestamp': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error monitoring rate changes: {e}")
            raise

    async def _safe_get_algofi_rates(self, asset_id: int) -> Dict[str, Any]:
        """Safely get Algofi rates with error handling"""
        try:
            return await self.algofi.get_asset_rates(asset_id)
        except Exception as e:
            logger.warning(f"Error getting Algofi rates: {e}")
            return {}

    async def _safe_get_folks_rates(self, asset_id: int) -> Dict[str, Any]:
        """Safely get Folks Finance rates with error handling"""
        try:
            rates = await self.folks_finance.get_current_rates()
            return {
                'pool_apy': rates.get_pool_apy(asset_id),
                'total_apy': rates.get_total_apy(asset_id),
                'utilization': Decimal('0.7')  # Mock utilization
            }
        except Exception as e:
            logger.warning(f"Error getting Folks Finance rates: {e}")
            return {}

    async def _safe_get_algofi_opportunities(self) -> List[DeFiYield]:
        """Safely get Algofi opportunities"""
        try:
            return await self.algofi.get_yield_opportunities()
        except Exception as e:
            logger.warning(f"Error getting Algofi opportunities: {e}")
            return []

    async def _safe_get_folks_opportunities(self) -> List[DeFiYield]:
        """Safely get Folks Finance opportunities"""
        try:
            return await self.folks_finance.get_yield_opportunities()
        except Exception as e:
            logger.warning(f"Error getting Folks Finance opportunities: {e}")
            return []

    async def _safe_get_tinyman_opportunities(self) -> List[DeFiYield]:
        """Safely get Tinyman opportunities"""
        try:
            return await self.tinyman.get_liquidity_mining_opportunities()
        except Exception as e:
            logger.warning(f"Error getting Tinyman opportunities: {e}")
            return []

    async def _calculate_risk_adjusted_rankings(self, aggregated: AggregatedRates):
        """Calculate risk-adjusted rankings for protocols"""
        risk_adjusted_lending = []
        risk_adjusted_borrowing = []

        for protocol, rates in aggregated.protocol_rates.items():
            weights = self.protocol_weights.get(protocol, {})
            risk_factor = (
                weights.get('security_score', 0.8) *
                weights.get('liquidity_score', 0.8) *
                weights.get('maturity_score', 0.8)
            )

            # Adjust lending rates (higher risk factor = better)
            if 'lending' in rates:
                lending_rate = rates['lending']
                risk_adjusted_rate = lending_rate * Decimal(str(risk_factor))
                risk_adjusted_lending.append((protocol, risk_adjusted_rate))

            # Adjust borrowing rates (lower is better, so invert risk factor)
            if 'borrowing' in rates and rates['borrowing'] > 0:
                borrowing_rate = rates['borrowing']
                risk_adjusted_rate = borrowing_rate / Decimal(str(risk_factor))
                risk_adjusted_borrowing.append((protocol, risk_adjusted_rate))

        # Sort by risk-adjusted rates
        risk_adjusted_lending.sort(key=lambda x: x[1], reverse=True)
        risk_adjusted_borrowing.sort(key=lambda x: x[1])

        aggregated.risk_adjusted_lending = risk_adjusted_lending
        aggregated.risk_adjusted_borrowing = risk_adjusted_borrowing

    async def _find_best_lending_strategy(
        self,
        asset_id: int,
        amount: Decimal,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Find the best lending strategy"""
        rates = await self.get_aggregated_rates(asset_id)

        if risk_tolerance == "low":
            # Prefer established protocols
            best_option = rates.risk_adjusted_lending[0] if rates.risk_adjusted_lending else ("", Decimal('0'))
        else:
            # Go for highest yield
            best_option = (rates.best_lending_protocol, rates.best_lending_rate)

        return {
            'strategy': 'lending',
            'recommended_protocol': best_option[0],
            'expected_apy': float(best_option[1]),
            'estimated_annual_return': float(amount * best_option[1]),
            'risk_level': risk_tolerance,
            'alternatives': rates.risk_adjusted_lending[:3]
        }

    async def _find_best_borrowing_strategy(
        self,
        asset_id: int,
        amount: Decimal,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Find the best borrowing strategy"""
        rates = await self.get_aggregated_rates(asset_id)

        best_option = (rates.best_borrowing_protocol, rates.best_borrowing_rate)

        return {
            'strategy': 'borrowing',
            'recommended_protocol': best_option[0],
            'borrowing_rate': float(best_option[1]),
            'estimated_annual_cost': float(amount * best_option[1]),
            'alternatives': rates.risk_adjusted_borrowing[:3]
        }

    async def _find_best_lp_strategy(
        self,
        asset_id: int,
        amount: Decimal,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Find the best liquidity provision strategy"""
        opportunities = await self.tinyman.get_liquidity_mining_opportunities()

        # Filter by asset and risk tolerance
        suitable_opportunities = [
            opp for opp in opportunities
            if opp.asset_id == asset_id and self._matches_risk_tolerance(opp, risk_tolerance)
        ]

        best_opp = suitable_opportunities[0] if suitable_opportunities else None

        if best_opp:
            return {
                'strategy': 'liquidity_provision',
                'recommended_pool': best_opp.strategy_name,
                'expected_apy': float(best_opp.current_apy),
                'risk_level': best_opp.strategy_risk_level,
                'impermanent_loss_risk': 'medium',
                'alternatives': suitable_opportunities[1:3]
            }
        else:
            return {
                'strategy': 'liquidity_provision',
                'error': 'No suitable LP opportunities found'
            }

    async def _find_best_yield_strategy(
        self,
        asset_id: int,
        amount: Decimal,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Find the best yield farming strategy"""
        all_opportunities = await self.get_all_yield_opportunities()

        # Filter and rank opportunities
        suitable_opportunities = [
            opp for opp in all_opportunities
            if opp.asset_id == asset_id and self._matches_risk_tolerance(opp, risk_tolerance)
        ]

        if suitable_opportunities:
            best_opp = suitable_opportunities[0]
            return {
                'strategy': 'yield_farming',
                'recommended_protocol': best_opp.protocol,
                'strategy_name': best_opp.strategy_name,
                'expected_apy': float(best_opp.current_apy),
                'risk_adjusted_apy': float(best_opp.risk_adjusted_yield),
                'alternatives': suitable_opportunities[1:3]
            }
        else:
            return {
                'strategy': 'yield_farming',
                'error': 'No suitable yield farming opportunities found'
            }

    def _matches_risk_tolerance(self, opportunity: DeFiYield, risk_tolerance: str) -> bool:
        """Check if opportunity matches risk tolerance"""
        risk_mapping = {
            "low": ["very_low", "low"],
            "medium": ["very_low", "low", "medium"],
            "high": ["very_low", "low", "medium", "high", "very_high"]
        }

        return opportunity.strategy_risk_level in risk_mapping.get(risk_tolerance, [])

    async def _get_historical_rates(self, asset_id: int) -> Dict[str, Dict[str, Decimal]]:
        """Get historical rates for comparison (mock implementation)"""
        # Mock historical data
        return {
            'Algofi': {
                'lending': Decimal('0.04'),  # Previous lending rate
                'borrowing': Decimal('0.06')
            },
            'Folks Finance': {
                'lending': Decimal('0.05'),
                'lending_with_rewards': Decimal('0.08')
            }
        }

    def clear_cache(self):
        """Clear all caches"""
        self._cache.clear()
        self.algofi.clear_cache()
        self.folks_finance.clear_cache()
        self.tinyman.clear_cache()