"""
Data models for ALGO staking analysis
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class StakingMetrics:
    """Metrics for ALGO staking performance"""
    current_apy: Decimal
    historical_avg_apy: Decimal
    participation_rate: Decimal
    total_staked_algo: Decimal
    governance_participation: Decimal
    validator_performance: Decimal
    timestamp: datetime

    def risk_adjusted_yield(self) -> Decimal:
        """Calculate risk-adjusted yield based on participation and validator performance"""
        base_yield = self.current_apy
        participation_bonus = self.participation_rate * Decimal('0.1')  # Up to 10% bonus
        validator_penalty = (Decimal('1.0') - self.validator_performance) * Decimal('0.05')  # Up to 5% penalty

        return base_yield + participation_bonus - validator_penalty

@dataclass
class GovernanceData:
    """Algorand governance participation data"""
    period_id: str
    total_eligible_algo: Decimal
    committed_algo: Decimal
    participation_rate: Decimal
    expected_rewards: Decimal
    voting_sessions: int
    completed_votes: int
    timestamp: datetime

    def governance_score(self) -> Decimal:
        """Calculate governance participation score"""
        voting_completion = Decimal(self.completed_votes) / Decimal(self.voting_sessions) if self.voting_sessions > 0 else Decimal('0')
        return (self.participation_rate + voting_completion) / Decimal('2')

@dataclass
class ValidatorMetrics:
    """Validator performance metrics"""
    validator_id: str
    uptime_percentage: Decimal
    block_proposal_success: Decimal
    attestation_success: Decimal
    commission_rate: Decimal
    total_stake: Decimal
    delegator_count: int
    timestamp: datetime

    def performance_score(self) -> Decimal:
        """Calculate overall validator performance score"""
        weights = {
            'uptime': Decimal('0.4'),
            'proposals': Decimal('0.3'),
            'attestations': Decimal('0.3')
        }

        score = (
            self.uptime_percentage * weights['uptime'] +
            self.block_proposal_success * weights['proposals'] +
            self.attestation_success * weights['attestations']
        )

        return score