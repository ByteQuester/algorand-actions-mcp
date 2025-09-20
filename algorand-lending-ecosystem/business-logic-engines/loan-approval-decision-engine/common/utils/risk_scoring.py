"""
Risk Scoring Engine

Blockchain-native risk algorithms for Algorand ecosystem participants.
Calculates comprehensive risk scores based on on-chain behavior patterns.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from ..models.decision_models import (
    AlgorandBorrower, HolisticRiskProfile, RiskLevel,
    EcosystemFootprint, DeFiBehaviorPattern, GovernanceParticipation
)

logger = logging.getLogger(__name__)


@dataclass
class RiskScoringConfig:
    """Configuration for risk scoring algorithms"""
    # Component weights (must sum to 1.0)
    wallet_age_weight: float = 0.15
    transaction_volume_weight: float = 0.20
    asset_diversity_weight: float = 0.15
    governance_weight: float = 0.20
    defi_behavior_weight: float = 0.20
    cross_protocol_weight: float = 0.10

    # Risk thresholds
    high_risk_threshold: float = 70.0
    medium_risk_threshold: float = 40.0

    # Confidence parameters
    min_data_points: int = 10
    confidence_decay_days: int = 30


class RiskScoringEngine:
    """
    Advanced risk scoring engine using blockchain-native metrics
    and behavioral analysis for holistic risk assessment.
    """

    def __init__(self, config: Optional[RiskScoringConfig] = None):
        self.config = config or RiskScoringConfig()
        self._validate_config()

    def calculate_comprehensive_risk_score(
        self,
        borrower: AlgorandBorrower,
        ecosystem_footprint: EcosystemFootprint,
        defi_behavior: DeFiBehaviorPattern,
        governance_participation: GovernanceParticipation,
        requested_amount: float
    ) -> Tuple[float, RiskLevel, Dict[str, Any]]:
        """
        Calculate comprehensive risk score using all available data.

        Args:
            borrower: Basic borrower profile
            ecosystem_footprint: Ecosystem participation data
            defi_behavior: DeFi behavior patterns
            governance_participation: Governance participation data
            requested_amount: Loan amount for context

        Returns:
            Tuple of (risk_score, risk_level, risk_breakdown)
        """
        logger.info(f"Calculating comprehensive risk score for {borrower.wallet_address}")

        try:
            # Calculate individual component scores
            component_scores = self._calculate_component_scores(
                borrower, ecosystem_footprint, defi_behavior, governance_participation
            )

            # Apply context adjustments based on loan amount
            context_adjustments = self._calculate_context_adjustments(
                borrower, requested_amount, component_scores
            )

            # Calculate weighted risk score
            weighted_score = self._calculate_weighted_score(component_scores)

            # Apply context adjustments
            final_score = self._apply_context_adjustments(weighted_score, context_adjustments)

            # Determine risk level
            risk_level = self._determine_risk_level(final_score)

            # Create detailed breakdown
            risk_breakdown = self._create_risk_breakdown(
                component_scores, context_adjustments, weighted_score, final_score
            )

            logger.info(f"Risk score calculated: {final_score:.2f} ({risk_level.value})")
            return final_score, risk_level, risk_breakdown

        except Exception as e:
            logger.error(f"Risk scoring failed: {e}")
            raise

    def _calculate_component_scores(
        self,
        borrower: AlgorandBorrower,
        ecosystem_footprint: EcosystemFootprint,
        defi_behavior: DeFiBehaviorPattern,
        governance_participation: GovernanceParticipation
    ) -> Dict[str, float]:
        """Calculate individual component risk scores (0-100, higher = more risk)"""

        component_scores = {}

        # Wallet age risk (newer wallets = higher risk)
        component_scores['wallet_age'] = self._score_wallet_age_risk(borrower.wallet_age_days)

        # Transaction volume risk (very low or very high volume = higher risk)
        component_scores['transaction_volume'] = self._score_transaction_volume_risk(
            borrower.total_volume_algo, borrower.total_transaction_count
        )

        # Asset diversity risk (lack of diversification = higher risk)
        component_scores['asset_diversity'] = self._score_asset_diversity_risk(
            borrower.asset_count, ecosystem_footprint.asset_diversity_score
        )

        # Governance participation risk (no participation = higher risk)
        component_scores['governance'] = self._score_governance_risk(
            borrower.governance_participation, governance_participation
        )

        # DeFi behavior risk (risky patterns = higher risk)
        component_scores['defi_behavior'] = self._score_defi_behavior_risk(
            defi_behavior, ecosystem_footprint
        )

        # Cross-protocol risk (high exposure to bridges/external chains = higher risk)
        component_scores['cross_protocol'] = self._score_cross_protocol_risk(
            ecosystem_footprint
        )

        return component_scores

    def _score_wallet_age_risk(self, age_days: int) -> float:
        """Score wallet age risk (0-100, higher = more risk)"""
        if age_days >= 730:  # 2+ years
            return 5.0
        elif age_days >= 365:  # 1-2 years
            return 15.0
        elif age_days >= 180:  # 6 months - 1 year
            return 30.0
        elif age_days >= 90:   # 3-6 months
            return 50.0
        elif age_days >= 30:   # 1-3 months
            return 70.0
        else:  # Less than 1 month
            return 90.0

    def _score_transaction_volume_risk(self, total_volume: float, tx_count: int) -> float:
        """Score transaction volume risk"""
        # Very low volume or count suggests minimal usage
        if total_volume < 100 or tx_count < 10:
            return 70.0

        # Moderate volume and activity
        if total_volume < 10000 and tx_count < 100:
            return 40.0

        # Good volume and activity
        if total_volume < 100000 and tx_count < 1000:
            return 20.0

        # High volume - generally good, but check for wash trading patterns
        if total_volume > 1000000 or tx_count > 10000:
            # Very high volume could indicate wash trading or other manipulation
            return 25.0

        # Optimal range
        return 10.0

    def _score_asset_diversity_risk(self, asset_count: int, diversity_score: float) -> float:
        """Score asset portfolio diversity risk"""
        # No assets or very few
        if asset_count <= 1:
            return 80.0
        elif asset_count <= 3:
            return 60.0
        elif asset_count <= 5:
            return 40.0
        elif asset_count <= 10:
            return 20.0
        else:
            # Many assets, but check diversity quality
            if diversity_score < 0.3:
                return 50.0  # Many assets but poor diversification
            elif diversity_score < 0.6:
                return 25.0
            else:
                return 10.0

    def _score_governance_risk(
        self,
        participates: bool,
        governance_data: GovernanceParticipation
    ) -> float:
        """Score governance participation risk"""
        if not participates:
            return 80.0  # High risk for no governance participation

        # Analyze quality of participation
        base_risk = 30.0  # Base risk for participants

        # Reduce risk for consistent participation
        if governance_data.vote_consistency_score > 0.8:
            base_risk -= 15.0
        elif governance_data.vote_consistency_score > 0.6:
            base_risk -= 10.0

        # Reduce risk for long-term participation
        if governance_data.continuous_participation_months > 12:
            base_risk -= 10.0
        elif governance_data.continuous_participation_months > 6:
            base_risk -= 5.0

        # Reduce risk for high community engagement
        if governance_data.community_engagement_score > 0.8:
            base_risk -= 10.0

        # Increase risk for very recent participation (could be gaming)
        if governance_data.continuous_participation_months < 3:
            base_risk += 20.0

        return max(base_risk, 5.0)

    def _score_defi_behavior_risk(
        self,
        defi_behavior: DeFiBehaviorPattern,
        ecosystem_footprint: EcosystemFootprint
    ) -> float:
        """Score DeFi behavior patterns risk"""
        base_risk = 50.0

        # Reduce risk for sophisticated DeFi usage
        if len(ecosystem_footprint.defi_protocols_used) > 3:
            base_risk -= 15.0

        # Risk management indicators
        if defi_behavior.stop_loss_usage > 0.5:
            base_risk -= 10.0

        if defi_behavior.diversification_score > 0.7:
            base_risk -= 10.0

        # Reduce risk for consistent liquidity provision
        if defi_behavior.liquidity_provision_consistency > 0.7:
            base_risk -= 15.0

        # Increase risk for high leverage usage
        if defi_behavior.leverage_usage_frequency > 10:
            base_risk += 20.0

        # Increase risk for poor risk-adjusted returns
        if defi_behavior.risk_adjusted_returns < 0:
            base_risk += 25.0

        # Increase risk for high maximum drawdown
        if defi_behavior.maximum_drawdown > 0.5:  # >50% drawdown
            base_risk += 30.0

        # Increase risk for excessive flash loan usage
        if defi_behavior.flash_loan_usage > 5:
            base_risk += 25.0

        return max(min(base_risk, 95.0), 5.0)

    def _score_cross_protocol_risk(self, ecosystem_footprint: EcosystemFootprint) -> float:
        """Score cross-protocol activity risk"""
        base_risk = 20.0

        # Increase risk for heavy bridge usage
        if len(ecosystem_footprint.bridge_protocols_used) > 2:
            base_risk += 20.0

        # Increase risk for high cross-chain volume
        if ecosystem_footprint.cross_chain_volume > 50000:
            base_risk += 15.0

        # Increase risk for low Algorand native percentage
        if ecosystem_footprint.algorand_native_percentage < 0.5:
            base_risk += 25.0

        # Reduce risk for high return frequency to Algorand
        if ecosystem_footprint.return_frequency_to_algorand > 0.8:
            base_risk -= 10.0

        # Increase risk for suspicious activity flags
        base_risk += len(ecosystem_footprint.suspicious_activity_flags) * 10

        # Critical increase for blacklisted interactions
        if ecosystem_footprint.blacklisted_interactions > 0:
            base_risk += 50.0

        return max(min(base_risk, 95.0), 5.0)

    def _calculate_context_adjustments(
        self,
        borrower: AlgorandBorrower,
        requested_amount: float,
        component_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate context-based risk adjustments"""
        adjustments = {}

        # Loan amount vs portfolio size adjustment
        portfolio_value = getattr(borrower, 'portfolio_value_usd', 0)
        if portfolio_value > 0:
            loan_to_portfolio_ratio = requested_amount / portfolio_value

            if loan_to_portfolio_ratio > 2.0:  # Loan > 2x portfolio
                adjustments['loan_size'] = 25.0
            elif loan_to_portfolio_ratio > 1.0:  # Loan > portfolio
                adjustments['loan_size'] = 15.0
            elif loan_to_portfolio_ratio > 0.5:  # Loan > 50% portfolio
                adjustments['loan_size'] = 10.0
            else:
                adjustments['loan_size'] = -5.0  # Conservative loan size
        else:
            adjustments['loan_size'] = 30.0  # Unknown portfolio size

        # Ecosystem maturity adjustment
        ecosystem_score = (
            (100 - component_scores['wallet_age']) * 0.3 +
            (100 - component_scores['governance']) * 0.4 +
            (100 - component_scores['defi_behavior']) * 0.3
        )

        if ecosystem_score > 70:
            adjustments['ecosystem_maturity'] = -10.0
        elif ecosystem_score < 30:
            adjustments['ecosystem_maturity'] = 15.0
        else:
            adjustments['ecosystem_maturity'] = 0.0

        # Reputation adjustment
        if borrower.reputation_score > 80:
            adjustments['reputation'] = -8.0
        elif borrower.reputation_score < 30:
            adjustments['reputation'] = 12.0
        else:
            adjustments['reputation'] = 0.0

        return adjustments

    def _calculate_weighted_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate weighted risk score from components"""
        weighted_score = (
            component_scores['wallet_age'] * self.config.wallet_age_weight +
            component_scores['transaction_volume'] * self.config.transaction_volume_weight +
            component_scores['asset_diversity'] * self.config.asset_diversity_weight +
            component_scores['governance'] * self.config.governance_weight +
            component_scores['defi_behavior'] * self.config.defi_behavior_weight +
            component_scores['cross_protocol'] * self.config.cross_protocol_weight
        )

        return weighted_score

    def _apply_context_adjustments(
        self,
        base_score: float,
        adjustments: Dict[str, float]
    ) -> float:
        """Apply context adjustments to base risk score"""
        total_adjustment = sum(adjustments.values())
        final_score = base_score + total_adjustment

        # Ensure score stays within bounds
        return max(0.0, min(100.0, final_score))

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from numeric score"""
        if risk_score >= self.config.high_risk_threshold:
            return RiskLevel.HIGH if risk_score < 85 else RiskLevel.VERY_HIGH
        elif risk_score >= self.config.medium_risk_threshold:
            return RiskLevel.MEDIUM
        elif risk_score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW

    def _create_risk_breakdown(
        self,
        component_scores: Dict[str, float],
        context_adjustments: Dict[str, float],
        weighted_score: float,
        final_score: float
    ) -> Dict[str, Any]:
        """Create detailed risk score breakdown"""
        return {
            'component_scores': component_scores,
            'weighted_score': weighted_score,
            'context_adjustments': context_adjustments,
            'final_score': final_score,
            'risk_level': self._determine_risk_level(final_score).value,
            'score_confidence': self._calculate_score_confidence(component_scores),
            'primary_risk_factors': self._identify_primary_risk_factors(component_scores),
            'risk_mitigants': self._identify_risk_mitigants(component_scores),
            'calculation_metadata': {
                'config_version': '1.0',
                'calculation_timestamp': datetime.utcnow().isoformat(),
                'weights_used': {
                    'wallet_age': self.config.wallet_age_weight,
                    'transaction_volume': self.config.transaction_volume_weight,
                    'asset_diversity': self.config.asset_diversity_weight,
                    'governance': self.config.governance_weight,
                    'defi_behavior': self.config.defi_behavior_weight,
                    'cross_protocol': self.config.cross_protocol_weight
                }
            }
        }

    def _calculate_score_confidence(self, component_scores: Dict[str, float]) -> float:
        """Calculate confidence in the risk score based on data availability"""
        # Higher variance in component scores = lower confidence
        scores = list(component_scores.values())
        if len(scores) < 2:
            return 0.5

        score_variance = statistics.variance(scores)

        # Normalize variance to confidence (lower variance = higher confidence)
        # Assuming max reasonable variance is around 1000
        confidence = max(0.3, 1.0 - (score_variance / 1000.0))

        return min(confidence, 1.0)

    def _identify_primary_risk_factors(self, component_scores: Dict[str, float]) -> List[str]:
        """Identify the primary risk factors (highest scoring components)"""
        # Sort components by risk score (highest first)
        sorted_components = sorted(
            component_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Consider components with scores above 50 as primary risk factors
        primary_factors = [
            component for component, score in sorted_components
            if score > 50.0
        ]

        return primary_factors[:3]  # Return top 3 risk factors

    def _identify_risk_mitigants(self, component_scores: Dict[str, float]) -> List[str]:
        """Identify factors that mitigate risk (lowest scoring components)"""
        # Sort components by risk score (lowest first)
        sorted_components = sorted(
            component_scores.items(),
            key=lambda x: x[1]
        )

        # Consider components with scores below 30 as risk mitigants
        mitigants = [
            component for component, score in sorted_components
            if score < 30.0
        ]

        return mitigants[:3]  # Return top 3 mitigating factors

    def calculate_portfolio_risk_score(
        self,
        asset_count: int,
        diversity_score: float,
        volatility_exposure: float,
        concentration_risk: float
    ) -> float:
        """Calculate portfolio-specific risk score"""
        portfolio_risk = 0.0

        # Asset count factor
        if asset_count <= 1:
            portfolio_risk += 40.0
        elif asset_count <= 3:
            portfolio_risk += 25.0
        elif asset_count <= 5:
            portfolio_risk += 15.0
        else:
            portfolio_risk += 5.0

        # Diversity factor
        portfolio_risk += (1.0 - diversity_score) * 30.0

        # Volatility exposure
        portfolio_risk += volatility_exposure * 20.0

        # Concentration risk
        portfolio_risk += concentration_risk * 10.0

        return min(portfolio_risk, 100.0)

    def calculate_behavioral_risk_score(
        self,
        consistency_score: float,
        sophistication_score: float,
        risk_management_score: float
    ) -> float:
        """Calculate behavioral risk score"""
        behavioral_risk = 50.0  # Base behavioral risk

        # Reduce risk for high consistency
        behavioral_risk -= (consistency_score / 100.0) * 20.0

        # Reduce risk for high sophistication
        behavioral_risk -= (sophistication_score / 100.0) * 15.0

        # Reduce risk for good risk management
        behavioral_risk -= (risk_management_score / 100.0) * 15.0

        return max(min(behavioral_risk, 100.0), 0.0)

    def calculate_liquidity_risk_score(
        self,
        stable_asset_percentage: float,
        liquidity_provider_score: float,
        bridge_usage_frequency: int
    ) -> float:
        """Calculate liquidity-related risk score"""
        liquidity_risk = 30.0  # Base liquidity risk

        # Reduce risk for higher stable asset percentage
        liquidity_risk -= stable_asset_percentage * 25.0

        # Reduce risk for liquidity provision
        liquidity_risk -= liquidity_provider_score * 15.0

        # Increase risk for frequent bridge usage (liquidity tied up)
        if bridge_usage_frequency > 5:
            liquidity_risk += 20.0
        elif bridge_usage_frequency > 2:
            liquidity_risk += 10.0

        return max(min(liquidity_risk, 100.0), 0.0)

    def _validate_config(self):
        """Validate risk scoring configuration"""
        total_weight = (
            self.config.wallet_age_weight +
            self.config.transaction_volume_weight +
            self.config.asset_diversity_weight +
            self.config.governance_weight +
            self.config.defi_behavior_weight +
            self.config.cross_protocol_weight
        )

        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Component weights must sum to 1.0, got {total_weight}")

        if not (0 <= self.config.high_risk_threshold <= 100):
            raise ValueError("High risk threshold must be between 0 and 100")

        if not (0 <= self.config.medium_risk_threshold <= 100):
            raise ValueError("Medium risk threshold must be between 0 and 100")

        if self.config.medium_risk_threshold >= self.config.high_risk_threshold:
            raise ValueError("Medium risk threshold must be less than high risk threshold")


class AdvancedRiskMetrics:
    """Advanced risk metrics calculations for sophisticated analysis"""

    @staticmethod
    def calculate_value_at_risk(
        portfolio_values: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """Calculate Value at Risk (VaR) for portfolio"""
        if not portfolio_values:
            return 0.0

        returns = []
        for i in range(1, len(portfolio_values)):
            if portfolio_values[i-1] != 0:
                return_pct = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                returns.append(return_pct)

        if not returns:
            return 0.0

        # Calculate VaR at specified confidence level
        sorted_returns = sorted(returns)
        var_index = int((1 - confidence_level) * len(sorted_returns))

        return abs(sorted_returns[var_index]) if var_index < len(sorted_returns) else 0.0

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio for risk-adjusted returns"""
        if not returns:
            return 0.0

        excess_returns = [r - risk_free_rate/365 for r in returns]  # Daily risk-free rate

        if not excess_returns:
            return 0.0

        mean_excess_return = statistics.mean(excess_returns)

        if len(excess_returns) < 2:
            return mean_excess_return

        std_excess_return = statistics.stdev(excess_returns)

        if std_excess_return == 0:
            return float('inf') if mean_excess_return > 0 else 0.0

        return mean_excess_return / std_excess_return

    @staticmethod
    def calculate_maximum_drawdown(portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown from portfolio values"""
        if not portfolio_values:
            return 0.0

        peak = portfolio_values[0]
        max_drawdown = 0.0

        for value in portfolio_values:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak if peak != 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    @staticmethod
    def calculate_correlation_risk(
        asset_correlations: Dict[str, Dict[str, float]],
        portfolio_weights: Dict[str, float]
    ) -> float:
        """Calculate portfolio correlation risk"""
        if not asset_correlations or not portfolio_weights:
            return 0.5  # Medium risk for unknown correlation

        total_correlation_risk = 0.0
        total_weight_pairs = 0.0

        for asset1, weight1 in portfolio_weights.items():
            for asset2, weight2 in portfolio_weights.items():
                if asset1 != asset2 and asset1 in asset_correlations:
                    correlation = asset_correlations[asset1].get(asset2, 0.0)

                    # High positive correlation increases risk
                    correlation_risk = abs(correlation) * weight1 * weight2
                    total_correlation_risk += correlation_risk
                    total_weight_pairs += weight1 * weight2

        if total_weight_pairs == 0:
            return 0.5

        return total_correlation_risk / total_weight_pairs