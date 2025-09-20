"""
ALGO Staking Engine

Main engine for analyzing ALGO staking yields and determining base rates
for DeFi lending based on blockchain consensus participation.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import httpx
from algosdk.v2client import algod
from algosdk import account, transaction

from .models import StakingMetrics, GovernanceData, ValidatorMetrics

logger = logging.getLogger(__name__)

class AlgoStakingEngine:
    """
    Engine for analyzing ALGO staking yields and participation rates
    to determine base interest rates for lending protocols.
    """

    def __init__(
        self,
        algod_client: algod.AlgodClient,
        governance_api_url: str = "https://governance.algorand.foundation/api/v1",
        cache_ttl: int = 300  # 5 minutes
    ):
        self.algod_client = algod_client
        self.governance_api_url = governance_api_url
        self.cache_ttl = cache_ttl
        self._cache: Dict = {}
        self._cache_timestamps: Dict = {}

    async def calculate_staking_rate(
        self,
        historical_periods: int = 12,
        risk_adjustment: bool = True
    ) -> StakingMetrics:
        """
        Calculate current ALGO staking rate based on consensus participation
        and governance rewards.
        """
        try:
            # Get current network participation
            participation_data = await self._get_participation_metrics()

            # Get governance data
            governance_data = await self._get_governance_data(historical_periods)

            # Get validator performance
            validator_metrics = await self._get_validator_metrics()

            # Calculate APY based on rewards and participation
            current_apy = await self._calculate_current_apy(
                participation_data, governance_data
            )

            # Historical average
            historical_apy = await self._calculate_historical_apy(historical_periods)

            metrics = StakingMetrics(
                current_apy=current_apy,
                historical_avg_apy=historical_apy,
                participation_rate=participation_data['participation_rate'],
                total_staked_algo=participation_data['total_online'],
                governance_participation=governance_data.participation_rate,
                validator_performance=validator_metrics['avg_performance'],
                timestamp=datetime.utcnow()
            )

            if risk_adjustment:
                return self._apply_risk_adjustment(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating staking rate: {e}")
            raise

    async def _get_participation_metrics(self) -> Dict:
        """Get current network participation metrics"""
        cache_key = "participation_metrics"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            # Get network status
            status = self.algod_client.status()
            supply = self.algod_client.supply()

            # Calculate participation rate
            total_supply = Decimal(str(supply.get('total-money', 0)))
            online_supply = Decimal(str(supply.get('online-money', 0)))

            participation_rate = online_supply / total_supply if total_supply > 0 else Decimal('0')

            data = {
                'participation_rate': participation_rate,
                'total_online': online_supply,
                'total_supply': total_supply,
                'last_round': status.get('last-round', 0)
            }

            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return data

        except Exception as e:
            logger.error(f"Error getting participation metrics: {e}")
            raise

    async def _get_governance_data(self, periods: int = 12) -> GovernanceData:
        """Get Algorand governance participation data"""
        cache_key = f"governance_data_{periods}"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            async with httpx.AsyncClient() as client:
                # Get current governance period
                response = await client.get(f"{self.governance_api_url}/periods/current")
                current_period = response.json()

                # Get historical data
                historical_response = await client.get(
                    f"{self.governance_api_url}/periods",
                    params={'limit': periods}
                )
                historical_periods = historical_response.json()

            # Process current period data
            governance_data = GovernanceData(
                period_id=current_period.get('id', 'unknown'),
                total_eligible_algo=Decimal(str(current_period.get('eligible_algo', 0))),
                committed_algo=Decimal(str(current_period.get('committed_algo', 0))),
                participation_rate=Decimal(str(current_period.get('participation_rate', 0))),
                expected_rewards=Decimal(str(current_period.get('expected_rewards', 0))),
                voting_sessions=current_period.get('voting_sessions', 0),
                completed_votes=current_period.get('completed_votes', 0),
                timestamp=datetime.utcnow()
            )

            self._cache[cache_key] = governance_data
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return governance_data

        except Exception as e:
            logger.warning(f"Error getting governance data: {e}")
            # Return default governance data
            return GovernanceData(
                period_id="default",
                total_eligible_algo=Decimal('0'),
                committed_algo=Decimal('0'),
                participation_rate=Decimal('0.7'),  # Assume 70% participation
                expected_rewards=Decimal('0.08'),  # 8% APY default
                voting_sessions=4,
                completed_votes=3,
                timestamp=datetime.utcnow()
            )

    async def _get_validator_metrics(self) -> Dict:
        """Get validator performance metrics"""
        cache_key = "validator_metrics"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            # In a real implementation, this would query validator APIs
            # For now, we'll simulate based on network health
            status = self.algod_client.status()
            last_round = status.get('last-round', 0)

            # Simulate validator performance based on block production consistency
            # This is a simplified metric - real implementation would be more complex
            avg_performance = Decimal('0.95')  # 95% average performance

            data = {
                'avg_performance': avg_performance,
                'active_validators': 120,  # Estimated
                'last_round': last_round
            }

            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return data

        except Exception as e:
            logger.error(f"Error getting validator metrics: {e}")
            return {
                'avg_performance': Decimal('0.90'),
                'active_validators': 100,
                'last_round': 0
            }

    async def _calculate_current_apy(
        self,
        participation_data: Dict,
        governance_data: GovernanceData
    ) -> Decimal:
        """Calculate current APY based on participation and governance rewards"""

        # Base rate from network participation
        participation_rate = participation_data['participation_rate']
        base_rate = Decimal('0.05')  # 5% base rate

        # Governance bonus
        governance_bonus = governance_data.expected_rewards * Decimal('0.5')

        # Participation adjustment
        participation_adjustment = participation_rate * Decimal('0.02')  # Up to 2% bonus

        current_apy = base_rate + governance_bonus + participation_adjustment

        return min(current_apy, Decimal('0.15'))  # Cap at 15%

    async def _calculate_historical_apy(self, periods: int = 12) -> Decimal:
        """Calculate historical average APY"""
        # This would query historical data in a real implementation
        # For now, return a reasonable historical average
        return Decimal('0.08')  # 8% historical average

    def _apply_risk_adjustment(self, metrics: StakingMetrics) -> StakingMetrics:
        """Apply risk adjustments to staking metrics"""

        # Risk factors
        participation_risk = max(Decimal('0'), Decimal('0.7') - metrics.participation_rate)
        validator_risk = max(Decimal('0'), Decimal('0.95') - metrics.validator_performance)

        # Total risk adjustment (negative impact on yield)
        risk_adjustment = (participation_risk + validator_risk) * Decimal('0.1')

        # Apply adjustment
        adjusted_apy = max(
            metrics.current_apy - risk_adjustment,
            Decimal('0.02')  # Minimum 2% APY
        )

        return StakingMetrics(
            current_apy=adjusted_apy,
            historical_avg_apy=metrics.historical_avg_apy,
            participation_rate=metrics.participation_rate,
            total_staked_algo=metrics.total_staked_algo,
            governance_participation=metrics.governance_participation,
            validator_performance=metrics.validator_performance,
            timestamp=metrics.timestamp
        )

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self._cache:
            return False

        cache_time = self._cache_timestamps.get(key)
        if not cache_time:
            return False

        return (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl

    async def get_rate_recommendations(
        self,
        loan_amount: Decimal,
        loan_term_days: int,
        borrower_reputation: Optional[Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        Get interest rate recommendations based on staking yields
        """
        staking_metrics = await self.calculate_staking_rate()

        # Base rate from staking
        base_rate = staking_metrics.risk_adjusted_yield()

        # Term adjustment
        term_years = Decimal(loan_term_days) / Decimal('365')
        term_adjustment = term_years * Decimal('0.005')  # 0.5% per year

        # Reputation adjustment
        reputation_adjustment = Decimal('0')
        if borrower_reputation is not None:
            reputation_adjustment = (Decimal('1') - borrower_reputation) * Decimal('0.02')

        recommended_rate = base_rate + term_adjustment + reputation_adjustment

        return {
            'base_staking_rate': base_rate,
            'term_adjustment': term_adjustment,
            'reputation_adjustment': reputation_adjustment,
            'recommended_rate': recommended_rate,
            'min_rate': recommended_rate * Decimal('0.8'),
            'max_rate': recommended_rate * Decimal('1.2')
        }