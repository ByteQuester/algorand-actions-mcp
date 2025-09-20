"""
On-chain reputation and behavior models for Algorand DeFi.

Models for calculating creditworthiness based on blockchain activity,
governance participation, and DeFi protocol interactions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum


class ReputationTier(Enum):
    """Reputation tiers based on on-chain behavior"""
    UNVERIFIED = "unverified"  # New or insufficient data
    BRONZE = "bronze"  # Basic activity, some history
    SILVER = "silver"  # Consistent activity, good behavior
    GOLD = "gold"  # Excellent history, high value activity
    PLATINUM = "platinum"  # Exceptional history, governance participation
    DIAMOND = "diamond"  # Top tier, protocol contributor


class BehaviorType(Enum):
    """Types of on-chain behavior patterns"""
    TRADING = "trading"
    DEFI_PARTICIPATION = "defi_participation"
    GOVERNANCE_VOTING = "governance_voting"
    LIQUIDITY_PROVISION = "liquidity_provision"
    ASSET_HOLDING = "asset_holding"
    PROTOCOL_INTERACTION = "protocol_interaction"
    YIELD_FARMING = "yield_farming"


@dataclass
class OnChainBehavior:
    """On-chain behavior analysis for an address"""
    address: str
    analysis_period_days: int

    # Activity metrics
    total_transactions: int
    unique_protocols_used: int
    total_volume_algo: Decimal
    total_volume_usd: Decimal

    # Consistency metrics
    active_days: int
    max_inactive_period_days: int
    average_monthly_activity: float

    # DeFi behavior
    defi_transactions: int = 0
    yield_farming_participation: bool = False
    liquidity_provision_days: int = 0
    governance_votes_cast: int = 0

    # Risk behavior indicators
    failed_transactions: int = 0
    high_slippage_trades: int = 0
    bot_like_behavior_score: float = 0.0  # 0-1, higher = more bot-like

    # Value behavior
    largest_single_transaction: Decimal = Decimal('0')
    total_fees_paid: Decimal = Decimal('0')
    average_transaction_size: Decimal = Decimal('0')

    # Behavior patterns
    preferred_protocols: List[str] = field(default_factory=list)
    trading_patterns: Dict[str, Any] = field(default_factory=dict)
    time_zone_activity: Dict[int, int] = field(default_factory=dict)  # hour -> count

    @property
    def activity_consistency_score(self) -> float:
        """Calculate activity consistency (0-100)"""
        if self.analysis_period_days == 0:
            return 0.0

        consistency = (self.active_days / self.analysis_period_days) * 100

        # Penalty for long inactive periods
        if self.max_inactive_period_days > 30:
            penalty = min(20, (self.max_inactive_period_days - 30) / 10)
            consistency -= penalty

        return max(0.0, min(100.0, consistency))

    @property
    def defi_engagement_score(self) -> float:
        """Calculate DeFi engagement level (0-100)"""
        if self.total_transactions == 0:
            return 0.0

        defi_ratio = self.defi_transactions / self.total_transactions
        protocol_diversity = min(self.unique_protocols_used / 5, 1.0)  # Max 5 protocols

        base_score = defi_ratio * 70
        diversity_bonus = protocol_diversity * 20
        governance_bonus = 10 if self.governance_votes_cast > 0 else 0

        return min(100.0, base_score + diversity_bonus + governance_bonus)


@dataclass
class GovernanceParticipation:
    """Algorand governance participation history"""
    address: str

    # Participation history by period
    periods_participated: List[int] = field(default_factory=list)
    total_algo_committed: Dict[int, Decimal] = field(default_factory=dict)  # period -> amount
    votes_cast: Dict[int, int] = field(default_factory=dict)  # period -> vote count
    voting_power_used: Dict[int, float] = field(default_factory=dict)  # period -> percentage

    # Rewards and penalties
    rewards_earned: Dict[int, Decimal] = field(default_factory=dict)
    penalties_incurred: Dict[int, Decimal] = field(default_factory=dict)

    # Participation quality
    average_voting_power_used: float = 0.0
    consecutive_periods: int = 0
    missed_periods: int = 0

    @property
    def governance_reputation_score(self) -> float:
        """Calculate governance reputation score (0-100)"""
        if not self.periods_participated:
            return 0.0

        # Base score from participation
        participation_score = len(self.periods_participated) * 10

        # Bonus for consistency
        consistency_bonus = self.consecutive_periods * 5

        # Bonus for voting engagement
        engagement_bonus = self.average_voting_power_used * 30

        # Penalty for missed periods
        miss_penalty = self.missed_periods * 5

        total_score = participation_score + consistency_bonus + engagement_bonus - miss_penalty
        return max(0.0, min(100.0, total_score))

    @property
    def is_committed_governor(self) -> bool:
        """Check if address is a committed governance participant"""
        return (
            len(self.periods_participated) >= 2 and
            self.consecutive_periods >= 1 and
            self.average_voting_power_used > 0.5
        )


@dataclass
class LiquidityProvision:
    """Liquidity provision behavior analysis"""
    address: str

    # LP position history
    pools_participated: List[str] = field(default_factory=list)
    total_lp_periods: int = 0
    average_position_duration_days: float = 0.0
    total_liquidity_provided_usd: Decimal = Decimal('0')

    # LP performance
    total_fees_earned: Decimal = Decimal('0')
    total_rewards_earned: Decimal = Decimal('0')
    impermanent_loss_incurred: Decimal = Decimal('0')
    net_lp_performance: Decimal = Decimal('0')

    # LP behavior patterns
    prefers_stable_pools: bool = False
    prefers_volatile_pools: bool = False
    early_adopter_bonus: int = 0  # Number of pools joined early

    # Risk tolerance indicators
    max_single_position_usd: Decimal = Decimal('0')
    diversification_score: float = 0.0  # Pool diversity

    @property
    def lp_reputation_score(self) -> float:
        """Calculate liquidity provision reputation (0-100)"""
        # Base score from participation
        participation_score = min(len(self.pools_participated) * 15, 60)

        # Duration bonus (longer = better)
        duration_score = min(self.average_position_duration_days / 30 * 10, 20)

        # Performance bonus
        performance_score = 10 if self.net_lp_performance > 0 else 0

        # Early adopter bonus
        early_bonus = min(self.early_adopter_bonus * 2, 10)

        return min(100.0, participation_score + duration_score + performance_score + early_bonus)


@dataclass
class ReputationScore:
    """Comprehensive reputation score for an Algorand address"""
    address: str
    calculation_timestamp: datetime

    # Component scores (0-100 each)
    activity_score: float = 0.0
    consistency_score: float = 0.0
    defi_engagement_score: float = 0.0
    governance_score: float = 0.0
    liquidity_provision_score: float = 0.0
    risk_behavior_score: float = 0.0  # Lower is better

    # Behavior analysis
    on_chain_behavior: Optional[OnChainBehavior] = None
    governance_participation: Optional[GovernanceParticipation] = None
    liquidity_provision: Optional[LiquidityProvision] = None

    # Overall metrics
    reputation_tier: ReputationTier = ReputationTier.UNVERIFIED
    overall_score: float = 0.0
    confidence_level: float = 0.0  # How confident we are in this assessment

    # Historical tracking
    score_history: List[tuple[datetime, float]] = field(default_factory=list)
    tier_progression: List[tuple[datetime, ReputationTier]] = field(default_factory=list)

    def calculate_overall_score(self) -> float:
        """Calculate weighted overall reputation score"""
        weights = {
            'activity': 0.20,
            'consistency': 0.25,
            'defi_engagement': 0.20,
            'governance': 0.15,
            'liquidity_provision': 0.10,
            'risk_behavior': 0.10  # Penalty weight
        }

        weighted_score = (
            self.activity_score * weights['activity'] +
            self.consistency_score * weights['consistency'] +
            self.defi_engagement_score * weights['defi_engagement'] +
            self.governance_score * weights['governance'] +
            self.liquidity_provision_score * weights['liquidity_provision'] -
            self.risk_behavior_score * weights['risk_behavior']  # Subtract risk penalty
        )

        self.overall_score = max(0.0, min(100.0, weighted_score))
        return self.overall_score

    def determine_reputation_tier(self) -> ReputationTier:
        """Determine reputation tier based on overall score and specific criteria"""
        score = self.calculate_overall_score()

        # Check for specific tier requirements
        if score >= 90 and self._meets_diamond_criteria():
            tier = ReputationTier.DIAMOND
        elif score >= 80 and self._meets_platinum_criteria():
            tier = ReputationTier.PLATINUM
        elif score >= 65 and self._meets_gold_criteria():
            tier = ReputationTier.GOLD
        elif score >= 45 and self._meets_silver_criteria():
            tier = ReputationTier.SILVER
        elif score >= 25:
            tier = ReputationTier.BRONZE
        else:
            tier = ReputationTier.UNVERIFIED

        self.reputation_tier = tier
        return tier

    def _meets_diamond_criteria(self) -> bool:
        """Check if address meets Diamond tier criteria"""
        return (
            self.governance_score >= 80 and
            self.defi_engagement_score >= 70 and
            self.consistency_score >= 80 and
            self.risk_behavior_score <= 10
        )

    def _meets_platinum_criteria(self) -> bool:
        """Check if address meets Platinum tier criteria"""
        return (
            self.governance_score >= 60 and
            self.defi_engagement_score >= 50 and
            self.consistency_score >= 70
        )

    def _meets_gold_criteria(self) -> bool:
        """Check if address meets Gold tier criteria"""
        return (
            self.defi_engagement_score >= 40 and
            self.consistency_score >= 60
        )

    def _meets_silver_criteria(self) -> bool:
        """Check if address meets Silver tier criteria"""
        return (
            self.activity_score >= 30 and
            self.consistency_score >= 40
        )

    def get_lending_risk_adjustment(self) -> float:
        """Get risk adjustment factor for lending (0.5 = 50% of base rate, 1.5 = 150%)"""
        tier_adjustments = {
            ReputationTier.DIAMOND: 0.6,      # 40% discount
            ReputationTier.PLATINUM: 0.7,     # 30% discount
            ReputationTier.GOLD: 0.8,         # 20% discount
            ReputationTier.SILVER: 0.9,       # 10% discount
            ReputationTier.BRONZE: 1.0,       # No adjustment
            ReputationTier.UNVERIFIED: 1.3,   # 30% premium
        }
        return tier_adjustments.get(self.reputation_tier, 1.0)

    def get_collateral_discount(self) -> float:
        """Get collateral requirement discount (0.1 = 10% lower requirement)"""
        tier_discounts = {
            ReputationTier.DIAMOND: 0.15,     # 15% lower collateral requirement
            ReputationTier.PLATINUM: 0.12,    # 12% lower
            ReputationTier.GOLD: 0.08,        # 8% lower
            ReputationTier.SILVER: 0.05,      # 5% lower
            ReputationTier.BRONZE: 0.0,       # No discount
            ReputationTier.UNVERIFIED: 0.0,   # No discount
        }
        return tier_discounts.get(self.reputation_tier, 0.0)

    def add_score_to_history(self):
        """Add current score to historical tracking"""
        self.score_history.append((self.calculation_timestamp, self.overall_score))
        self.tier_progression.append((self.calculation_timestamp, self.reputation_tier))

        # Keep only last 100 entries
        if len(self.score_history) > 100:
            self.score_history = self.score_history[-100:]
        if len(self.tier_progression) > 100:
            self.tier_progression = self.tier_progression[-100:]