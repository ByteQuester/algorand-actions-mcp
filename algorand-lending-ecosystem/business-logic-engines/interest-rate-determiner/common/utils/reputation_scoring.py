"""
On-chain reputation scoring utilities for Algorand addresses.

Provides sophisticated algorithms for calculating creditworthiness
based on blockchain activity, governance participation, and DeFi behavior.
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum

from ..models.reputation_models import (
    ReputationScore, OnChainBehavior, GovernanceParticipation,
    LiquidityProvision, ReputationTier, BehaviorType
)


class ScoringMethod(Enum):
    """Different scoring methodologies"""
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    EXPONENTIAL = "exponential"
    SIGMOID = "sigmoid"


@dataclass
class ScoringWeights:
    """Weights for different reputation components"""
    activity_weight: float = 0.25
    consistency_weight: float = 0.25
    defi_engagement_weight: float = 0.20
    governance_weight: float = 0.15
    liquidity_provision_weight: float = 0.10
    risk_penalty_weight: float = 0.05


class ReputationCalculator:
    """
    Main reputation calculator for Algorand addresses.

    Combines multiple scoring algorithms to create a comprehensive
    reputation score suitable for lending risk assessment.
    """

    def __init__(self, scoring_weights: Optional[ScoringWeights] = None):
        self.weights = scoring_weights or ScoringWeights()
        self.min_data_threshold = 30  # Minimum days of data required

    def calculate_comprehensive_score(
        self,
        address: str,
        on_chain_behavior: OnChainBehavior,
        governance_participation: Optional[GovernanceParticipation] = None,
        liquidity_provision: Optional[LiquidityProvision] = None
    ) -> ReputationScore:
        """
        Calculate comprehensive reputation score from all available data.

        Args:
            address: Algorand address
            on_chain_behavior: On-chain activity analysis
            governance_participation: Governance participation data
            liquidity_provision: LP activity data

        Returns:
            Complete reputation score with tier assignment
        """
        # Calculate individual component scores
        activity_score = self._calculate_activity_score(on_chain_behavior)
        consistency_score = self._calculate_consistency_score(on_chain_behavior)
        defi_score = self._calculate_defi_engagement_score(on_chain_behavior)
        governance_score = self._calculate_governance_score(governance_participation)
        lp_score = self._calculate_lp_score(liquidity_provision)
        risk_score = self._calculate_risk_behavior_score(on_chain_behavior)

        # Create reputation score object
        reputation = ReputationScore(
            address=address,
            calculation_timestamp=datetime.now(),
            activity_score=activity_score,
            consistency_score=consistency_score,
            defi_engagement_score=defi_score,
            governance_score=governance_score,
            liquidity_provision_score=lp_score,
            risk_behavior_score=risk_score,
            on_chain_behavior=on_chain_behavior,
            governance_participation=governance_participation,
            liquidity_provision=liquidity_provision
        )

        # Calculate overall score and determine tier
        reputation.calculate_overall_score()
        reputation.determine_reputation_tier()

        # Calculate confidence level
        confidence = self._calculate_confidence_level(
            on_chain_behavior, governance_participation, liquidity_provision
        )
        reputation.confidence_level = confidence

        return reputation

    def _calculate_activity_score(self, behavior: OnChainBehavior) -> float:
        """
        Calculate activity score based on transaction volume and frequency.

        Uses logarithmic scaling to prevent extreme values from dominating.
        """
        if behavior.analysis_period_days < self.min_data_threshold:
            return 0.0

        # Transaction frequency score (0-40 points)
        daily_tx_rate = behavior.total_transactions / behavior.analysis_period_days
        frequency_score = min(40, math.log10(max(1, daily_tx_rate * 10)) * 15)

        # Volume score (0-40 points)
        avg_daily_volume = behavior.total_volume_usd / behavior.analysis_period_days
        volume_score = min(40, math.log10(max(1, float(avg_daily_volume))) * 8)

        # Protocol diversity score (0-20 points)
        diversity_score = min(20, behavior.unique_protocols_used * 4)

        total_score = frequency_score + volume_score + diversity_score
        return min(100.0, total_score)

    def _calculate_consistency_score(self, behavior: OnChainBehavior) -> float:
        """
        Calculate consistency score based on regular activity patterns.

        Rewards consistent, predictable behavior over sporadic high activity.
        """
        if behavior.analysis_period_days < self.min_data_threshold:
            return 0.0

        # Active days ratio (0-50 points)
        activity_ratio = behavior.active_days / behavior.analysis_period_days
        activity_score = activity_ratio * 50

        # Inactivity penalty (0-30 points deduction)
        max_inactive_penalty = min(30, behavior.max_inactive_period_days / 7 * 5)
        inactivity_score = max(0, 30 - max_inactive_penalty)

        # Regularity bonus (0-20 points)
        # Award bonus for regular monthly activity
        expected_monthly_activity = behavior.analysis_period_days / 30
        regularity_score = min(20, behavior.average_monthly_activity / expected_monthly_activity * 20)

        total_score = activity_score + inactivity_score + regularity_score
        return min(100.0, total_score)

    def _calculate_defi_engagement_score(self, behavior: OnChainBehavior) -> float:
        """
        Calculate DeFi engagement score based on protocol usage.

        Rewards active participation in DeFi protocols and yield farming.
        """
        if behavior.total_transactions == 0:
            return 0.0

        # DeFi transaction ratio (0-40 points)
        defi_ratio = behavior.defi_transactions / behavior.total_transactions
        ratio_score = defi_ratio * 40

        # Protocol diversity (0-30 points)
        protocol_score = min(30, len(behavior.preferred_protocols) * 6)

        # Yield farming participation (0-20 points)
        farming_score = 20 if behavior.yield_farming_participation else 0

        # Liquidity provision (0-10 points)
        lp_score = min(10, behavior.liquidity_provision_days / 30)

        total_score = ratio_score + protocol_score + farming_score + lp_score
        return min(100.0, total_score)

    def _calculate_governance_score(
        self,
        governance: Optional[GovernanceParticipation]
    ) -> float:
        """Calculate governance participation score"""
        if not governance:
            return 0.0

        return governance.governance_reputation_score

    def _calculate_lp_score(
        self,
        liquidity_provision: Optional[LiquidityProvision]
    ) -> float:
        """Calculate liquidity provision score"""
        if not liquidity_provision:
            return 0.0

        return liquidity_provision.lp_reputation_score

    def _calculate_risk_behavior_score(self, behavior: OnChainBehavior) -> float:
        """
        Calculate risk behavior score (higher = more risky).

        This is a penalty score that reduces overall reputation.
        """
        risk_score = 0.0

        # Failed transaction penalty
        if behavior.total_transactions > 0:
            failure_rate = behavior.failed_transactions / behavior.total_transactions
            risk_score += failure_rate * 30  # Up to 30 points penalty

        # High slippage penalty
        if behavior.defi_transactions > 0:
            slippage_rate = behavior.high_slippage_trades / behavior.defi_transactions
            risk_score += slippage_rate * 20  # Up to 20 points penalty

        # Bot-like behavior penalty
        risk_score += behavior.bot_like_behavior_score * 50  # Up to 50 points penalty

        return min(100.0, risk_score)

    def _calculate_confidence_level(
        self,
        behavior: OnChainBehavior,
        governance: Optional[GovernanceParticipation],
        lp: Optional[LiquidityProvision]
    ) -> float:
        """
        Calculate confidence level in the reputation assessment.

        Higher confidence when more data is available and consistent.
        """
        confidence = 0.5  # Base confidence

        # Data quantity bonus
        if behavior.analysis_period_days >= 90:  # 3+ months
            confidence += 0.2
        elif behavior.analysis_period_days >= 30:  # 1+ month
            confidence += 0.1

        # Data quality bonus
        if behavior.total_transactions >= 100:
            confidence += 0.15
        elif behavior.total_transactions >= 20:
            confidence += 0.1

        # Governance data bonus
        if governance and len(governance.periods_participated) >= 2:
            confidence += 0.1

        # LP data bonus
        if lp and lp.total_lp_periods >= 3:
            confidence += 0.05

        return min(1.0, confidence)


class OnChainScorer:
    """
    Specialized scorer for on-chain behavior analysis.

    Focuses on transaction patterns, value flows, and interaction patterns.
    """

    @staticmethod
    def calculate_transaction_pattern_score(
        transaction_counts: List[int],
        time_intervals: List[datetime]
    ) -> float:
        """
        Analyze transaction patterns for regularity and predictability.

        Args:
            transaction_counts: Number of transactions per time period
            time_intervals: Time periods for analysis

        Returns:
            Pattern regularity score (0-100)
        """
        if len(transaction_counts) < 7:  # Need at least a week of data
            return 0.0

        # Calculate coefficient of variation (lower = more regular)
        mean_txns = sum(transaction_counts) / len(transaction_counts)
        if mean_txns == 0:
            return 0.0

        variance = sum((x - mean_txns) ** 2 for x in transaction_counts) / len(transaction_counts)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_txns

        # Convert to score (lower CV = higher score)
        regularity_score = max(0, 100 - cv * 50)
        return min(100.0, regularity_score)

    @staticmethod
    def calculate_counterparty_diversity_score(
        unique_counterparties: int,
        total_transactions: int
    ) -> float:
        """
        Calculate diversity score based on counterparty interactions.

        Higher diversity suggests more legitimate, varied activity.
        """
        if total_transactions == 0:
            return 0.0

        # Diversity ratio
        diversity_ratio = unique_counterparties / total_transactions

        # Optimal ratio is around 0.3-0.7 (not too concentrated, not too scattered)
        if 0.3 <= diversity_ratio <= 0.7:
            score = 100.0
        elif diversity_ratio < 0.3:
            # Too concentrated
            score = diversity_ratio / 0.3 * 100
        else:
            # Too scattered (might be bot behavior)
            score = max(0, 100 - (diversity_ratio - 0.7) * 200)

        return min(100.0, score)

    @staticmethod
    def analyze_value_flow_patterns(
        incoming_values: List[Decimal],
        outgoing_values: List[Decimal],
        timestamps: List[datetime]
    ) -> Dict[str, float]:
        """
        Analyze value flow patterns for legitimacy indicators.

        Returns various metrics about spending/receiving patterns.
        """
        if not incoming_values or not outgoing_values:
            return {"legitimacy_score": 0.0, "balance_score": 0.0}

        total_incoming = sum(incoming_values)
        total_outgoing = sum(outgoing_values)

        # Balance score (how well balanced are flows)
        if total_incoming + total_outgoing == 0:
            balance_score = 50.0
        else:
            balance_ratio = min(total_incoming, total_outgoing) / max(total_incoming, total_outgoing)
            balance_score = balance_ratio * 100

        # Legitimacy score based on value distribution
        all_values = incoming_values + outgoing_values
        if len(all_values) < 5:
            legitimacy_score = 50.0
        else:
            # Check for suspiciously round numbers (possible bot activity)
            round_numbers = sum(1 for v in all_values if float(v) % 1.0 == 0.0)
            round_ratio = round_numbers / len(all_values)

            # Penalty for too many round numbers
            round_penalty = min(50, round_ratio * 100)
            legitimacy_score = max(0, 100 - round_penalty)

        return {
            "legitimacy_score": legitimacy_score,
            "balance_score": balance_score,
            "total_flow_volume": float(total_incoming + total_outgoing),
            "flow_balance_ratio": float(balance_ratio) if 'balance_ratio' in locals() else 0.0
        }


class GovernanceScorer:
    """
    Specialized scorer for Algorand governance participation.

    Evaluates quality and consistency of governance engagement.
    """

    @staticmethod
    def calculate_participation_quality_score(
        periods_participated: List[int],
        voting_records: Dict[int, float],  # period -> voting percentage
        commitment_amounts: Dict[int, Decimal]  # period -> ALGO committed
    ) -> float:
        """
        Calculate quality score for governance participation.

        Considers consistency, voting engagement, and commitment size.
        """
        if not periods_participated:
            return 0.0

        # Consistency score (0-40 points)
        total_periods = max(periods_participated) - min(periods_participated) + 1
        consistency_ratio = len(periods_participated) / total_periods
        consistency_score = consistency_ratio * 40

        # Voting engagement score (0-40 points)
        avg_voting_percentage = sum(voting_records.values()) / len(voting_records)
        voting_score = avg_voting_percentage * 40

        # Commitment growth score (0-20 points)
        if len(commitment_amounts) >= 2:
            amounts = list(commitment_amounts.values())
            growth_ratio = amounts[-1] / amounts[0]
            growth_score = min(20, math.log10(growth_ratio + 1) * 10)
        else:
            growth_score = 10  # Neutral score for single period

        total_score = consistency_score + voting_score + growth_score
        return min(100.0, total_score)

    @staticmethod
    def calculate_governance_leadership_score(
        periods_participated: List[int],
        voting_records: Dict[int, float],
        early_participation: bool
    ) -> float:
        """
        Calculate leadership score based on early adoption and high engagement.
        """
        leadership_score = 0.0

        # Early adopter bonus (0-30 points)
        if early_participation and 1 in periods_participated:
            leadership_score += 30

        # Long-term participation (0-30 points)
        participation_streak = GovernanceScorer._calculate_longest_streak(periods_participated)
        streak_score = min(30, participation_streak * 7.5)
        leadership_score += streak_score

        # High engagement (0-40 points)
        high_engagement_periods = sum(1 for v in voting_records.values() if v >= 0.9)
        engagement_ratio = high_engagement_periods / len(voting_records)
        engagement_score = engagement_ratio * 40
        leadership_score += engagement_score

        return min(100.0, leadership_score)

    @staticmethod
    def _calculate_longest_streak(periods: List[int]) -> int:
        """Calculate longest consecutive participation streak"""
        if not periods:
            return 0

        sorted_periods = sorted(periods)
        longest_streak = 1
        current_streak = 1

        for i in range(1, len(sorted_periods)):
            if sorted_periods[i] == sorted_periods[i-1] + 1:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 1

        return longest_streak


class BehaviorAnalyzer:
    """
    Advanced behavior pattern analyzer for detecting sophisticated patterns.

    Uses machine learning-inspired techniques to identify behavior patterns
    that indicate trustworthiness or risk.
    """

    @staticmethod
    def detect_bot_behavior(
        transaction_timestamps: List[datetime],
        transaction_amounts: List[Decimal],
        transaction_types: List[str]
    ) -> float:
        """
        Detect bot-like behavior patterns.

        Returns bot probability score (0-1, higher = more bot-like).
        """
        if len(transaction_timestamps) < 10:
            return 0.0

        bot_indicators = []

        # Check for overly regular timing patterns
        time_intervals = []
        for i in range(1, len(transaction_timestamps)):
            interval = (transaction_timestamps[i] - transaction_timestamps[i-1]).total_seconds()
            time_intervals.append(interval)

        if time_intervals:
            # Calculate coefficient of variation for timing
            mean_interval = sum(time_intervals) / len(time_intervals)
            if mean_interval > 0:
                variance = sum((x - mean_interval) ** 2 for x in time_intervals) / len(time_intervals)
                cv = math.sqrt(variance) / mean_interval

                # Very regular timing is suspicious
                if cv < 0.1:  # Very low variation
                    bot_indicators.append(0.8)
                elif cv < 0.3:  # Low variation
                    bot_indicators.append(0.4)

        # Check for round number bias
        round_amounts = sum(1 for amount in transaction_amounts if float(amount) % 1.0 == 0.0)
        round_ratio = round_amounts / len(transaction_amounts)
        if round_ratio > 0.8:  # 80%+ round numbers
            bot_indicators.append(0.7)
        elif round_ratio > 0.6:  # 60%+ round numbers
            bot_indicators.append(0.4)

        # Check for repetitive patterns
        if len(set(transaction_types)) == 1:  # Only one type of transaction
            bot_indicators.append(0.6)

        # Combine indicators
        if not bot_indicators:
            return 0.0

        return min(1.0, sum(bot_indicators) / len(bot_indicators))

    @staticmethod
    def analyze_sophistication_level(
        protocols_used: List[str],
        transaction_complexity: List[float],  # Complexity score per transaction
        defi_strategies: List[str]
    ) -> float:
        """
        Analyze sophistication level of DeFi usage.

        Higher sophistication indicates better understanding of DeFi
        and potentially lower risk.
        """
        sophistication_score = 0.0

        # Protocol diversity score (0-30 points)
        unique_protocols = len(set(protocols_used))
        protocol_score = min(30, unique_protocols * 5)
        sophistication_score += protocol_score

        # Transaction complexity score (0-40 points)
        if transaction_complexity:
            avg_complexity = sum(transaction_complexity) / len(transaction_complexity)
            complexity_score = min(40, avg_complexity * 40)
            sophistication_score += complexity_score

        # Strategy diversity score (0-30 points)
        unique_strategies = len(set(defi_strategies))
        strategy_score = min(30, unique_strategies * 7.5)
        sophistication_score += strategy_score

        return min(100.0, sophistication_score)

    @staticmethod
    def calculate_risk_tolerance_indicator(
        high_risk_transactions: int,
        total_transactions: int,
        max_single_transaction: Decimal,
        average_transaction: Decimal
    ) -> Dict[str, float]:
        """
        Calculate indicators of risk tolerance based on transaction behavior.

        Returns risk profile suitable for lending assessment.
        """
        risk_profile = {
            "risk_appetite": 0.0,
            "position_sizing": 0.0,
            "overall_risk_tolerance": 0.0
        }

        if total_transactions == 0:
            return risk_profile

        # Risk appetite based on high-risk transaction ratio
        risk_ratio = high_risk_transactions / total_transactions
        risk_profile["risk_appetite"] = min(100.0, risk_ratio * 100)

        # Position sizing discipline
        if average_transaction > 0:
            size_ratio = float(max_single_transaction / average_transaction)
            # Good discipline = max position not too much larger than average
            if size_ratio <= 3:  # Max is 3x average or less
                position_score = 100.0
            elif size_ratio <= 10:  # Max is 10x average or less
                position_score = max(0, 100 - (size_ratio - 3) * 10)
            else:  # Very large positions relative to average
                position_score = 0.0

            risk_profile["position_sizing"] = position_score

        # Overall risk tolerance (balanced view)
        # Moderate risk appetite with good position sizing = good for lending
        appetite = risk_profile["risk_appetite"]
        sizing = risk_profile["position_sizing"]

        if 20 <= appetite <= 60 and sizing >= 70:  # Moderate risk, good discipline
            overall = 80.0
        elif appetite <= 20 and sizing >= 80:  # Conservative with discipline
            overall = 90.0
        elif appetite >= 80:  # Very high risk appetite
            overall = max(0, sizing - 20)  # Heavily penalized
        else:
            overall = (appetite + sizing) / 2  # Average the scores

        risk_profile["overall_risk_tolerance"] = overall

        return risk_profile