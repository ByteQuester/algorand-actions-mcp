"""
Data models for on-chain reputation analysis
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class ReputationTier(Enum):
    """Reputation tiers for borrowers"""
    EXCELLENT = "excellent"      # 0.9-1.0
    GOOD = "good"               # 0.7-0.89
    FAIR = "fair"               # 0.5-0.69
    POOR = "poor"               # 0.3-0.49
    VERY_POOR = "very_poor"     # 0.0-0.29

@dataclass
class OnChainBehavior:
    """On-chain behavior metrics for an address"""
    address: str
    account_age_days: int
    total_transactions: int
    avg_transaction_size: Decimal
    governance_participation: bool
    nft_holdings: int
    asa_holdings: int
    defi_protocol_interactions: int
    failed_transaction_rate: Decimal
    largest_transaction: Decimal
    consistent_activity: bool
    timestamp: datetime

    def activity_score(self) -> Decimal:
        """Calculate activity score based on transaction patterns"""
        # Factors: transaction count, size, consistency
        tx_score = min(Decimal(self.total_transactions) / Decimal('1000'), Decimal('1'))
        size_score = min(self.avg_transaction_size / Decimal('10000'), Decimal('1'))
        consistency_score = Decimal('1') if self.consistent_activity else Decimal('0.5')

        return (tx_score + size_score + consistency_score) / Decimal('3')

@dataclass
class TransactionPattern:
    """Transaction pattern analysis"""
    address: str
    regular_transaction_intervals: bool
    peak_activity_hours: List[int]
    preferred_transaction_types: List[str]
    gas_optimization_score: Decimal
    multi_sig_usage: bool
    smart_contract_interactions: int
    cross_chain_activity: bool
    timestamp: datetime

    def sophistication_score(self) -> Decimal:
        """Calculate user sophistication score"""
        scores = []

        # Regular intervals indicate planning
        if self.regular_transaction_intervals:
            scores.append(Decimal('0.2'))

        # Gas optimization shows experience
        scores.append(self.gas_optimization_score * Decimal('0.3'))

        # Smart contract interactions show DeFi savviness
        sc_score = min(Decimal(self.smart_contract_interactions) / Decimal('50'), Decimal('0.3'))
        scores.append(sc_score)

        # Multi-sig usage shows security awareness
        if self.multi_sig_usage:
            scores.append(Decimal('0.2'))

        return sum(scores)

@dataclass
class ReputationScore:
    """Complete reputation score for an address"""
    address: str
    overall_score: Decimal  # 0-1
    tier: ReputationTier
    activity_score: Decimal
    reliability_score: Decimal
    sophistication_score: Decimal
    governance_score: Decimal
    defi_score: Decimal
    risk_flags: List[str]
    strengths: List[str]
    improvement_areas: List[str]
    confidence_level: Decimal  # How confident we are in this score
    timestamp: datetime

    def rate_discount(self) -> Decimal:
        """Calculate interest rate discount based on reputation"""
        if self.tier == ReputationTier.EXCELLENT:
            return Decimal('0.02')  # 2% discount
        elif self.tier == ReputationTier.GOOD:
            return Decimal('0.01')  # 1% discount
        elif self.tier == ReputationTier.FAIR:
            return Decimal('0.005')  # 0.5% discount
        else:
            return Decimal('0')  # No discount for poor reputation

    def rate_premium(self) -> Decimal:
        """Calculate interest rate premium for risk"""
        if self.tier == ReputationTier.VERY_POOR:
            return Decimal('0.03')  # 3% premium
        elif self.tier == ReputationTier.POOR:
            return Decimal('0.015')  # 1.5% premium
        else:
            return Decimal('0')

@dataclass
class GovernanceParticipation:
    """Governance participation metrics"""
    address: str
    periods_participated: int
    total_algo_committed: Decimal
    voting_consistency: Decimal  # 0-1
    proposal_submissions: int
    community_engagement_score: Decimal
    timestamp: datetime

@dataclass
class DeFiInteractionHistory:
    """DeFi protocol interaction history"""
    address: str
    protocols_used: List[str]
    total_volume_usd: Decimal
    liquidity_provided: Decimal
    yield_farming_experience: bool
    lending_borrowing_history: Dict[str, int]
    liquidation_events: int
    profit_loss_ratio: Decimal
    timestamp: datetime