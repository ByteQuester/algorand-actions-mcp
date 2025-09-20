"""
Algorand Governance Participation Scoring Engine
Analyzes governance participation, voting behavior, and ALGO commitment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics

from algosdk.v2client import algod, indexer


@dataclass
class GovernancePeriod:
    """Single governance period data"""
    period_id: int
    start_time: datetime
    end_time: datetime
    participated: bool
    algo_committed: float
    votes_cast: int
    total_proposals: int
    voting_consistency: float


@dataclass
class GovernanceHistory:
    """Complete governance participation history"""
    total_periods: int
    participated_periods: int
    participation_rate: float
    avg_algo_committed: float
    total_votes_cast: int
    avg_voting_consistency: float
    recent_activity: bool


@dataclass
class GovernanceScore:
    """Governance participation scoring result"""
    address: str
    participation_score: float
    voting_consistency_score: float
    staking_commitment_score: float
    engagement_score: float
    overall_score: float
    governance_history: GovernanceHistory
    analysis_timestamp: datetime


class GovernanceScorer:
    """Analyzes Algorand governance participation for reputation scoring"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize Algorand clients
        self.indexer_client = indexer.IndexerClient(
            indexer_token="",
            indexer_address=config['algorand_config']['indexer']['url']
        )

        self.algod_client = algod.AlgodClient(
            algod_token="",
            algod_address=config['algorand_config']['node']['url']
        )

        # Governance configuration
        self.governance_config = config['algorand_config']['governance']

        # Known governance period information (simplified - in practice, fetch from official sources)
        self.governance_periods = [
            {
                'period': 1,
                'start': datetime(2021, 10, 1),
                'end': datetime(2021, 12, 31),
                'registration_app': 552635992  # Example app ID
            },
            {
                'period': 2,
                'start': datetime(2022, 1, 1),
                'end': datetime(2022, 3, 31),
                'registration_app': 695820551
            },
            {
                'period': 3,
                'start': datetime(2022, 4, 1),
                'end': datetime(2022, 6, 30),
                'registration_app': 734439564
            },
            {
                'period': 4,
                'start': datetime(2022, 7, 1),
                'end': datetime(2022, 9, 30),
                'registration_app': 745795721
            }
        ]

    async def score_governance_participation(self, wallet_address: str) -> GovernanceScore:
        """Analyze and score governance participation"""
        try:
            self.logger.info(f"Analyzing governance participation for: {wallet_address}")

            # Analyze governance history
            governance_history = await self._analyze_governance_history(wallet_address)

            # Calculate component scores
            participation_score = self._calculate_participation_score(governance_history)
            voting_consistency_score = self._calculate_voting_consistency_score(governance_history)
            staking_commitment_score = self._calculate_staking_commitment_score(governance_history)
            engagement_score = self._calculate_engagement_score(governance_history)

            # Calculate weighted overall score
            weights = self.config['reputation_scoring']['governance_weights']
            overall_score = (
                participation_score * weights['participation_rate'] +
                voting_consistency_score * weights['voting_consistency'] +
                staking_commitment_score * weights['algo_staking'] +
                engagement_score * weights['proposal_engagement']
            )

            return GovernanceScore(
                address=wallet_address,
                participation_score=participation_score,
                voting_consistency_score=voting_consistency_score,
                staking_commitment_score=staking_commitment_score,
                engagement_score=engagement_score,
                overall_score=overall_score,
                governance_history=governance_history,
                analysis_timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Error scoring governance participation: {e}")
            raise

    async def _analyze_governance_history(self, address: str) -> GovernanceHistory:
        """Analyze complete governance participation history"""
        try:
            periods_to_analyze = min(
                self.governance_config['periods_to_analyze'],
                len(self.governance_periods)
            )

            period_analyses = []

            # Analyze each governance period
            for i in range(periods_to_analyze):
                period_data = self.governance_periods[-(i+1)]  # Start from most recent
                period_analysis = await self._analyze_governance_period(address, period_data)
                if period_analysis:
                    period_analyses.append(period_analysis)

            if not period_analyses:
                return GovernanceHistory(
                    total_periods=periods_to_analyze,
                    participated_periods=0,
                    participation_rate=0.0,
                    avg_algo_committed=0.0,
                    total_votes_cast=0,
                    avg_voting_consistency=0.0,
                    recent_activity=False
                )

            # Calculate aggregated statistics
            participated_periods = sum(1 for p in period_analyses if p.participated)
            participation_rate = participated_periods / len(period_analyses)

            participating_periods = [p for p in period_analyses if p.participated]
            avg_algo_committed = (
                statistics.mean([p.algo_committed for p in participating_periods])
                if participating_periods else 0.0
            )

            total_votes_cast = sum(p.votes_cast for p in period_analyses)
            avg_voting_consistency = (
                statistics.mean([p.voting_consistency for p in participating_periods])
                if participating_periods else 0.0
            )

            # Check recent activity (last 2 periods)
            recent_activity = any(p.participated for p in period_analyses[:2])

            return GovernanceHistory(
                total_periods=len(period_analyses),
                participated_periods=participated_periods,
                participation_rate=participation_rate,
                avg_algo_committed=avg_algo_committed,
                total_votes_cast=total_votes_cast,
                avg_voting_consistency=avg_voting_consistency,
                recent_activity=recent_activity
            )

        except Exception as e:
            self.logger.error(f"Error analyzing governance history: {e}")
            return GovernanceHistory(
                total_periods=0,
                participated_periods=0,
                participation_rate=0.0,
                avg_algo_committed=0.0,
                total_votes_cast=0,
                avg_voting_consistency=0.0,
                recent_activity=False
            )

    async def _analyze_governance_period(self, address: str, period_data: Dict) -> Optional[GovernancePeriod]:
        """Analyze participation in a specific governance period"""
        try:
            period_id = period_data['period']
            start_time = period_data['start']
            end_time = period_data['end']
            registration_app = period_data.get('registration_app')

            self.logger.debug(f"Analyzing governance period {period_id} for {address}")

            # Check for governance registration transaction
            participated = False
            algo_committed = 0.0
            votes_cast = 0
            total_proposals = 1  # Simplified - would need to fetch actual proposal count

            if registration_app:
                # Look for application call to governance registration
                participation_data = await self._check_governance_registration(
                    address, registration_app, start_time, end_time
                )

                if participation_data:
                    participated = True
                    algo_committed = participation_data.get('committed_algo', 0.0)

                    # Check for voting transactions
                    votes_cast = await self._count_governance_votes(
                        address, registration_app, start_time, end_time
                    )

            # Calculate voting consistency
            voting_consistency = votes_cast / max(total_proposals, 1) if participated else 0.0

            return GovernancePeriod(
                period_id=period_id,
                start_time=start_time,
                end_time=end_time,
                participated=participated,
                algo_committed=algo_committed,
                votes_cast=votes_cast,
                total_proposals=total_proposals,
                voting_consistency=voting_consistency
            )

        except Exception as e:
            self.logger.error(f"Error analyzing governance period {period_data}: {e}")
            return None

    async def _check_governance_registration(
        self, address: str, app_id: int, start_time: datetime, end_time: datetime
    ) -> Optional[Dict]:
        """Check for governance registration in a period"""
        try:
            # Search for application calls to governance app
            response = self.indexer_client.search_transactions(
                address=address,
                application_id=app_id,
                min_timestamp=int(start_time.timestamp()),
                max_timestamp=int(end_time.timestamp()),
                txn_type='appl'
            )

            transactions = response.get('transactions', [])

            for tx in transactions:
                app_tx = tx.get('application-transaction', {})
                if app_tx.get('application-id') == app_id:
                    # Found governance registration
                    # In practice, would parse app args to get committed amount
                    return {
                        'committed_algo': 1000.0,  # Placeholder - parse from app args
                        'transaction_id': tx.get('id')
                    }

            return None

        except Exception as e:
            self.logger.error(f"Error checking governance registration: {e}")
            return None

    async def _count_governance_votes(
        self, address: str, app_id: int, start_time: datetime, end_time: datetime
    ) -> int:
        """Count governance votes cast in a period"""
        try:
            # Search for voting transactions (application calls)
            response = self.indexer_client.search_transactions(
                address=address,
                application_id=app_id,
                min_timestamp=int(start_time.timestamp()),
                max_timestamp=int(end_time.timestamp()),
                txn_type='appl'
            )

            transactions = response.get('transactions', [])
            vote_count = 0

            for tx in transactions:
                app_tx = tx.get('application-transaction', {})
                app_args = app_tx.get('application-args', [])

                # Check if this is a voting transaction
                # In practice, would parse app args to identify vote transactions
                if len(app_args) > 0:  # Simplified vote detection
                    vote_count += 1

            return max(0, vote_count - 1)  # Subtract registration transaction

        except Exception as e:
            self.logger.error(f"Error counting governance votes: {e}")
            return 0

    async def _analyze_current_governance_status(self, address: str) -> Dict:
        """Analyze current governance participation status"""
        try:
            # Check if currently participating in governance
            # This would involve checking the latest governance app

            # Get account info to check ALGO balance
            account_info = self.algod_client.account_info(address)
            current_balance = account_info.get('amount', 0) / 1e6

            # Simplified current status
            return {
                'currently_participating': False,  # Would check latest governance app
                'current_commitment': 0.0,
                'available_algo': current_balance,
                'eligible_to_participate': current_balance >= 1.0  # Minimum for governance
            }

        except Exception as e:
            self.logger.error(f"Error analyzing current governance status: {e}")
            return {
                'currently_participating': False,
                'current_commitment': 0.0,
                'available_algo': 0.0,
                'eligible_to_participate': False
            }

    def _calculate_participation_score(self, history: GovernanceHistory) -> float:
        """Calculate governance participation score"""
        if history.total_periods == 0:
            return 0.0

        # Base score from participation rate
        base_score = history.participation_rate

        # Bonus for recent activity
        recent_bonus = 0.1 if history.recent_activity else 0.0

        # Minimum participation threshold
        min_threshold = self.governance_config['participation_threshold']
        if history.participation_rate < min_threshold:
            return 0.0

        return min(1.0, base_score + recent_bonus)

    def _calculate_voting_consistency_score(self, history: GovernanceHistory) -> float:
        """Calculate voting consistency score"""
        if history.participated_periods == 0:
            return 0.0

        # Score based on average voting consistency
        consistency_score = history.avg_voting_consistency

        # Bonus for higher total votes cast
        vote_bonus = min(0.2, history.total_votes_cast / 20)  # Max bonus at 20+ votes

        return min(1.0, consistency_score + vote_bonus)

    def _calculate_staking_commitment_score(self, history: GovernanceHistory) -> float:
        """Calculate ALGO staking commitment score"""
        if history.avg_algo_committed == 0:
            return 0.0

        # Score based on committed amount (logarithmic scale)
        import math
        base_score = min(1.0, math.log10(history.avg_algo_committed + 1) / 4)  # Max at 10k ALGO

        # Bonus for consistent participation
        consistency_bonus = history.participation_rate * 0.2

        return min(1.0, base_score + consistency_bonus)

    def _calculate_engagement_score(self, history: GovernanceHistory) -> float:
        """Calculate overall governance engagement score"""
        if history.total_periods == 0:
            return 0.0

        # Combine multiple factors
        participation_factor = history.participation_rate
        voting_factor = history.avg_voting_consistency
        commitment_factor = min(1.0, history.avg_algo_committed / 5000)  # Normalized to 5k ALGO

        # Weight factors
        engagement_score = (
            participation_factor * 0.4 +
            voting_factor * 0.3 +
            commitment_factor * 0.3
        )

        # Bonus for recent activity
        recent_bonus = 0.1 if history.recent_activity else 0.0

        return min(1.0, engagement_score + recent_bonus)

    async def get_governance_leaderboard(self, addresses: List[str]) -> List[Tuple[str, float]]:
        """Get governance participation leaderboard"""
        try:
            scores = []

            # Analyze all addresses
            for address in addresses:
                try:
                    score_result = await self.score_governance_participation(address)
                    scores.append((address, score_result.overall_score))
                except Exception as e:
                    self.logger.error(f"Error scoring {address}: {e}")
                    scores.append((address, 0.0))

            # Sort by score (highest first)
            scores.sort(key=lambda x: x[1], reverse=True)

            return scores

        except Exception as e:
            self.logger.error(f"Error creating governance leaderboard: {e}")
            return []

    def get_participation_requirements(self) -> Dict:
        """Get governance participation requirements"""
        return {
            'minimum_algo': 1.0,
            'commitment_period_days': 90,
            'voting_requirements': {
                'minimum_participation': 0.9,
                'grace_period_hours': 24
            },
            'rewards': {
                'annual_percentage': 8.0,
                'distribution_method': 'quarterly'
            }
        }