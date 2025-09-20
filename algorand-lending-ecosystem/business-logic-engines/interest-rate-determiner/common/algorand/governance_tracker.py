"""
Algorand governance participation tracker for reputation scoring.

Tracks and analyzes governance participation including:
- Voting history and patterns
- Commitment tracking
- Reward calculation
- Participation quality assessment
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging

from ..models.algorand_models import GovernanceData, GovernanceStatus
from ..models.reputation_models import GovernanceParticipation

logger = logging.getLogger(__name__)


@dataclass
class GovernanceMetrics:
    """Comprehensive governance participation metrics"""
    address: str
    total_periods_eligible: int
    periods_participated: int
    total_algo_committed: Decimal
    total_votes_cast: int
    total_rewards_earned: Decimal

    # Participation quality
    average_commitment_size: Decimal = Decimal('0')
    participation_consistency: float = 0.0  # 0-1
    voting_engagement: float = 0.0  # 0-1
    early_adopter_bonus: float = 0.0  # 0-1

    # Current period status
    current_period: Optional[int] = None
    current_commitment: Decimal = Decimal('0')
    current_status: GovernanceStatus = GovernanceStatus.INELIGIBLE

    # Historical performance
    best_period_commitment: Decimal = Decimal('0')
    longest_streak: int = 0
    missed_periods: int = 0

    @property
    def participation_rate(self) -> float:
        """Calculate overall participation rate"""
        if self.total_periods_eligible == 0:
            return 0.0
        return self.periods_participated / self.total_periods_eligible

    @property
    def governance_score(self) -> float:
        """Calculate overall governance score (0-100)"""
        # Base score from participation rate
        base_score = self.participation_rate * 40

        # Consistency bonus
        consistency_bonus = self.participation_consistency * 25

        # Engagement bonus
        engagement_bonus = self.voting_engagement * 20

        # Early adopter bonus
        early_bonus = self.early_adopter_bonus * 10

        # Streak bonus
        streak_bonus = min(self.longest_streak * 2, 10)

        total = base_score + consistency_bonus + engagement_bonus + early_bonus + streak_bonus
        return min(100.0, total)


class GovernanceTracker:
    """
    Algorand governance participation tracker.

    Provides comprehensive tracking and analysis of governance
    participation for reputation and risk assessment.
    """

    def __init__(self, indexer_client=None, governance_app_id: int = 123456789):
        self.indexer_client = indexer_client
        self.governance_app_id = governance_app_id
        self._governance_cache: Dict[str, GovernanceParticipation] = {}
        self._metrics_cache: Dict[str, GovernanceMetrics] = {}

        # Known governance periods with their details
        self.governance_periods = {
            1: {
                'start_date': datetime(2021, 10, 1),
                'end_date': datetime(2021, 12, 31),
                'reward_rate': Decimal('0.334'),  # 33.4% APY
                'min_commitment': Decimal('1'),
                'voting_sessions': 5
            },
            2: {
                'start_date': datetime(2022, 1, 1),
                'end_date': datetime(2022, 3, 31),
                'reward_rate': Decimal('0.282'),  # 28.2% APY
                'min_commitment': Decimal('1'),
                'voting_sessions': 3
            },
            3: {
                'start_date': datetime(2022, 4, 1),
                'end_date': datetime(2022, 6, 30),
                'reward_rate': Decimal('0.224'),  # 22.4% APY
                'min_commitment': Decimal('1'),
                'voting_sessions': 4
            },
            # Add more periods as they occur
        }

    async def track_governance_participation(self, address: str) -> GovernanceParticipation:
        """
        Track complete governance participation history for an address.

        Returns detailed participation data including voting patterns,
        commitment history, and reward calculations.
        """
        if address in self._governance_cache:
            return self._governance_cache[address]

        try:
            participation = GovernanceParticipation(address=address)

            # Analyze participation for each known period
            for period_id, period_info in self.governance_periods.items():
                period_data = await self._analyze_period_participation(
                    address, period_id, period_info
                )

                if period_data['participated']:
                    participation.periods_participated.append(period_id)
                    participation.total_algo_committed[period_id] = period_data['commitment']
                    participation.votes_cast[period_id] = period_data['votes_cast']
                    participation.voting_power_used[period_id] = period_data['voting_power_used']
                    participation.rewards_earned[period_id] = period_data['rewards']
                    participation.penalties_incurred[period_id] = period_data['penalties']

            # Calculate derived metrics
            self._calculate_participation_metrics(participation)

            self._governance_cache[address] = participation
            return participation

        except Exception as e:
            logger.error(f"Error tracking governance for {address}: {e}")
            raise

    async def get_governance_metrics(self, address: str) -> GovernanceMetrics:
        """
        Get comprehensive governance metrics for an address.

        Returns quantified governance participation metrics
        suitable for risk assessment and reputation scoring.
        """
        if address in self._metrics_cache:
            return self._metrics_cache[address]

        try:
            participation = await self.track_governance_participation(address)

            metrics = GovernanceMetrics(
                address=address,
                total_periods_eligible=len(self.governance_periods),
                periods_participated=len(participation.periods_participated),
                total_algo_committed=sum(participation.total_algo_committed.values()),
                total_votes_cast=sum(participation.votes_cast.values()),
                total_rewards_earned=sum(participation.rewards_earned.values())
            )

            # Calculate quality metrics
            await self._calculate_governance_metrics(metrics, participation)

            self._metrics_cache[address] = metrics
            return metrics

        except Exception as e:
            logger.error(f"Error calculating governance metrics for {address}: {e}")
            raise

    async def get_current_governance_status(self, address: str) -> Dict[str, Any]:
        """Get current governance period status for an address"""
        current_period = max(self.governance_periods.keys())

        try:
            # Check current commitment and voting status
            commitment_data = await self._get_period_commitment(address, current_period)
            voting_data = await self._get_period_voting(address, current_period)

            status = {
                'period': current_period,
                'is_committed': commitment_data['amount'] > 0,
                'commitment_amount': commitment_data['amount'],
                'commitment_round': commitment_data.get('round'),
                'votes_cast': voting_data['votes_cast'],
                'total_votes_available': voting_data['total_available'],
                'voting_power_used': voting_data['voting_power_used'],
                'eligible_for_rewards': self._is_eligible_for_rewards(
                    commitment_data, voting_data, current_period
                ),
                'estimated_rewards': self._estimate_rewards(
                    commitment_data['amount'], current_period
                )
            }

            return status

        except Exception as e:
            logger.error(f"Error getting current governance status for {address}: {e}")
            raise

    async def analyze_voting_patterns(self, address: str) -> Dict[str, Any]:
        """
        Analyze voting patterns and behavior.

        Returns insights into voting consistency, timing,
        and decision patterns.
        """
        try:
            participation = await self.track_governance_participation(address)

            analysis = {
                'total_votes': sum(participation.votes_cast.values()),
                'periods_with_votes': len([p for p in participation.votes_cast.values() if p > 0]),
                'average_participation_rate': participation.average_voting_power_used,
                'consistency_score': self._calculate_voting_consistency(participation),
                'early_voter_score': await self._analyze_voting_timing(address),
                'decision_patterns': await self._analyze_decision_patterns(address)
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing voting patterns for {address}: {e}")
            raise

    async def get_governance_reputation_impact(self, address: str) -> float:
        """
        Calculate governance impact on overall reputation score.

        Returns a multiplier (0.8-1.2) to apply to base reputation score.
        """
        try:
            metrics = await self.get_governance_metrics(address)

            # Base impact from governance score
            governance_score = metrics.governance_score
            base_impact = 0.8 + (governance_score / 100) * 0.4  # 0.8 to 1.2 range

            # Bonus for high commitment amounts
            if metrics.total_algo_committed > Decimal('10000'):  # >10k ALGO total
                base_impact += 0.05
            elif metrics.total_algo_committed > Decimal('1000'):  # >1k ALGO total
                base_impact += 0.02

            # Bonus for consistency
            if metrics.longest_streak >= 3:
                base_impact += 0.03

            return min(1.2, base_impact)

        except Exception as e:
            logger.error(f"Error calculating governance reputation impact for {address}: {e}")
            return 1.0  # Neutral impact on error

    async def _analyze_period_participation(
        self,
        address: str,
        period_id: int,
        period_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze participation in a specific governance period"""
        # Mock implementation - would query actual governance data
        mock_participated = period_id <= 2  # Mock: participated in first 2 periods

        if mock_participated:
            return {
                'participated': True,
                'commitment': Decimal('1000'),  # Mock 1000 ALGO commitment
                'votes_cast': period_info['voting_sessions'],
                'voting_power_used': 1.0,  # 100% voting power used
                'rewards': Decimal('100'),  # Mock rewards
                'penalties': Decimal('0')
            }
        else:
            return {
                'participated': False,
                'commitment': Decimal('0'),
                'votes_cast': 0,
                'voting_power_used': 0.0,
                'rewards': Decimal('0'),
                'penalties': Decimal('0')
            }

    def _calculate_participation_metrics(self, participation: GovernanceParticipation):
        """Calculate derived metrics from participation data"""
        if participation.periods_participated:
            # Average voting power used
            total_power = sum(participation.voting_power_used.values())
            participation.average_voting_power_used = total_power / len(participation.periods_participated)

            # Calculate consecutive periods
            sorted_periods = sorted(participation.periods_participated)
            max_consecutive = 1
            current_consecutive = 1

            for i in range(1, len(sorted_periods)):
                if sorted_periods[i] == sorted_periods[i-1] + 1:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 1

            participation.consecutive_periods = max_consecutive

            # Calculate missed periods
            all_periods = set(range(1, max(self.governance_periods.keys()) + 1))
            participated_periods = set(participation.periods_participated)
            participation.missed_periods = len(all_periods - participated_periods)

    async def _calculate_governance_metrics(
        self,
        metrics: GovernanceMetrics,
        participation: GovernanceParticipation
    ):
        """Calculate quality metrics for governance participation"""
        if participation.periods_participated:
            # Average commitment size
            total_commitment = sum(participation.total_algo_committed.values())
            metrics.average_commitment_size = total_commitment / len(participation.periods_participated)

            # Participation consistency
            metrics.participation_consistency = participation.average_voting_power_used

            # Voting engagement
            total_possible_votes = sum(
                self.governance_periods[p]['voting_sessions']
                for p in participation.periods_participated
            )
            actual_votes = sum(participation.votes_cast.values())
            metrics.voting_engagement = actual_votes / max(total_possible_votes, 1)

            # Early adopter bonus (participated in period 1)
            metrics.early_adopter_bonus = 1.0 if 1 in participation.periods_participated else 0.0

            # Best period commitment
            if participation.total_algo_committed:
                metrics.best_period_commitment = max(participation.total_algo_committed.values())

            # Longest streak
            metrics.longest_streak = participation.consecutive_periods

            # Missed periods
            metrics.missed_periods = participation.missed_periods

    async def _get_period_commitment(self, address: str, period: int) -> Dict[str, Any]:
        """Get commitment data for a specific period"""
        # Mock implementation
        return {
            'amount': Decimal('500'),  # Mock commitment
            'round': 12345678,
            'timestamp': datetime.now()
        }

    async def _get_period_voting(self, address: str, period: int) -> Dict[str, Any]:
        """Get voting data for a specific period"""
        # Mock implementation
        period_info = self.governance_periods.get(period, {})
        total_votes = period_info.get('voting_sessions', 0)

        return {
            'votes_cast': total_votes,  # Mock: voted on all measures
            'total_available': total_votes,
            'voting_power_used': 1.0 if total_votes > 0 else 0.0
        }

    def _is_eligible_for_rewards(
        self,
        commitment_data: Dict[str, Any],
        voting_data: Dict[str, Any],
        period: int
    ) -> bool:
        """Check if address is eligible for rewards in period"""
        has_commitment = commitment_data['amount'] > 0
        voting_threshold = voting_data['voting_power_used'] >= 0.9  # 90% voting requirement
        return has_commitment and voting_threshold

    def _estimate_rewards(self, commitment_amount: Decimal, period: int) -> Decimal:
        """Estimate governance rewards for a commitment"""
        period_info = self.governance_periods.get(period, {})
        reward_rate = period_info.get('reward_rate', Decimal('0'))

        # Quarterly rate, so divide by 4 for quarterly payout
        quarterly_rate = reward_rate / 4
        return commitment_amount * quarterly_rate

    def _calculate_voting_consistency(self, participation: GovernanceParticipation) -> float:
        """Calculate voting consistency score"""
        if not participation.periods_participated:
            return 0.0

        # Check if voted in all participated periods
        periods_with_votes = sum(1 for votes in participation.votes_cast.values() if votes > 0)
        return periods_with_votes / len(participation.periods_participated)

    async def _analyze_voting_timing(self, address: str) -> float:
        """Analyze if user votes early in voting periods"""
        # Mock implementation - would analyze actual voting timestamps
        return 0.8  # Mock: votes relatively early

    async def _analyze_decision_patterns(self, address: str) -> Dict[str, Any]:
        """Analyze voting decision patterns"""
        # Mock implementation - would analyze actual vote choices
        return {
            'independent_voter': True,  # Doesn't always follow majority
            'consistent_philosophy': True,  # Consistent voting pattern
            'engagement_level': 'high'  # High engagement with proposals
        }