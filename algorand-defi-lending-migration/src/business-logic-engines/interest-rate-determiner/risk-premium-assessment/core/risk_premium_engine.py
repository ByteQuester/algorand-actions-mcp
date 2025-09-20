"""
Risk Premium Assessment Engine

Comprehensive risk assessment engine that combines traditional credit scoring with
Algorand-specific on-chain behavior analysis to determine appropriate risk premiums
for loan pricing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import hashlib

from ..config import RiskPremiumConfig, DEFAULT_CONFIG


@dataclass
class CreditProfile:
    """Traditional credit profile information."""
    credit_score: Optional[int] = None
    credit_age_months: Optional[int] = None
    credit_utilization: Optional[float] = None
    payment_history_score: Optional[float] = None
    credit_mix_score: Optional[float] = None
    new_credit_score: Optional[float] = None
    debt_to_income_ratio: Optional[float] = None
    employment_history_months: Optional[int] = None


@dataclass
class AlgorandWalletProfile:
    """Algorand wallet behavior profile."""
    wallet_address: str
    wallet_age_days: int = 0
    total_transactions: int = 0
    total_volume_algo: Decimal = Decimal('0')
    average_balance_algo: Decimal = Decimal('0')
    governance_participation_count: int = 0
    governance_commitment_algo: Decimal = Decimal('0')
    staking_periods: int = 0
    staking_rewards_algo: Decimal = Decimal('0')
    defi_protocols_used: List[str] = field(default_factory=list)
    smart_contracts_interacted: int = 0
    asa_tokens_held: int = 0
    asa_tokens_created: int = 0
    consensus_participation_periods: int = 0


@dataclass
class CrossChainProfile:
    """Cross-chain activity profile."""
    ethereum_activity: Dict[str, Any] = field(default_factory=dict)
    polygon_activity: Dict[str, Any] = field(default_factory=dict)
    avalanche_activity: Dict[str, Any] = field(default_factory=dict)
    fantom_activity: Dict[str, Any] = field(default_factory=dict)
    total_cross_chain_score: float = 0.0


@dataclass
class MarketConditions:
    """Current market condition indicators."""
    volatility_index: float = 0.0
    liquidity_ratio: float = 1.0
    correlation_factor: float = 0.0
    market_stress_indicator: float = 0.0
    algo_price_volatility: float = 0.0


@dataclass
class RiskAssessment:
    """Complete risk assessment result."""
    borrower_id: str
    assessment_timestamp: datetime
    credit_score_component: float
    onchain_behavior_component: float
    cross_chain_component: float
    market_adjustment_component: float
    final_risk_score: float
    risk_category: str
    risk_premium_rate: Decimal
    recommended_interest_rate: Decimal
    confidence_score: float
    assessment_details: Dict[str, Any] = field(default_factory=dict)


class OnChainBehaviorAnalyzer:
    """Analyzes Algorand on-chain behavior for risk assessment."""

    def __init__(self, config: RiskPremiumConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def analyze_wallet_behavior(self, wallet_profile: AlgorandWalletProfile) -> Tuple[float, Dict[str, float]]:
        """
        Analyze wallet behavior and return score and detailed breakdown.

        Args:
            wallet_profile: Algorand wallet profile data

        Returns:
            Tuple of (overall_score, score_breakdown)
        """
        scores = {}
        weights = self.config.onchain_behavior_weights

        # Wallet age scoring
        scores['wallet_age'] = self._score_wallet_age(wallet_profile.wallet_age_days)

        # Transaction volume scoring
        scores['transaction_volume'] = self._score_transaction_volume(
            wallet_profile.total_transactions,
            wallet_profile.total_volume_algo
        )

        # DeFi participation scoring
        scores['defi_participation'] = self._score_defi_participation(
            wallet_profile.defi_protocols_used
        )

        # Governance voting scoring
        scores['governance_voting'] = self._score_governance_participation(
            wallet_profile.governance_participation_count,
            wallet_profile.governance_commitment_algo
        )

        # Staking history scoring
        scores['staking_history'] = self._score_staking_history(
            wallet_profile.staking_periods,
            wallet_profile.staking_rewards_algo
        )

        # Smart contract interaction scoring
        scores['smart_contract_interactions'] = self._score_smart_contract_interactions(
            wallet_profile.smart_contracts_interacted,
            wallet_profile.asa_tokens_created
        )

        # Calculate weighted overall score
        overall_score = (
            scores['wallet_age'] * weights.wallet_age +
            scores['transaction_volume'] * weights.transaction_volume +
            scores['defi_participation'] * weights.defi_participation +
            scores['governance_voting'] * weights.governance_voting +
            scores['staking_history'] * weights.staking_history +
            scores['smart_contract_interactions'] * weights.smart_contract_interactions
        )

        # Apply Algorand-specific bonuses
        bonus_score = self._apply_algorand_bonuses(wallet_profile)
        overall_score = min(1.0, overall_score + bonus_score)

        self.logger.info(f"Wallet behavior analysis completed. Overall score: {overall_score:.3f}")

        return overall_score, scores

    def _score_wallet_age(self, wallet_age_days: int) -> float:
        """Score based on wallet age."""
        if wallet_age_days >= 365 * 2:  # 2+ years
            return 1.0
        elif wallet_age_days >= 365:  # 1+ year
            return 0.8
        elif wallet_age_days >= 180:  # 6+ months
            return 0.6
        elif wallet_age_days >= self.config.risk_thresholds.min_wallet_age_days:
            return 0.4
        else:
            return 0.1

    def _score_transaction_volume(self, tx_count: int, total_volume: Decimal) -> float:
        """Score based on transaction count and volume."""
        if tx_count < self.config.risk_thresholds.min_transaction_count:
            return 0.1

        # Normalize transaction count (log scale)
        tx_score = min(1.0, tx_count / 1000)

        # Normalize volume score (log scale)
        volume_float = float(total_volume)
        if volume_float > 0:
            volume_score = min(1.0, volume_float / 100000)  # 100K ALGO as reference
        else:
            volume_score = 0.0

        return (tx_score * 0.6) + (volume_score * 0.4)

    def _score_defi_participation(self, protocols_used: List[str]) -> float:
        """Score based on DeFi protocol participation."""
        if not protocols_used:
            return 0.0

        whitelisted_protocols = set(self.config.algorand_specific_params.defi_protocol_whitelist)
        used_whitelisted = len(set(protocols_used) & whitelisted_protocols)

        if used_whitelisted >= 3:
            return 1.0
        elif used_whitelisted == 2:
            return 0.7
        elif used_whitelisted == 1:
            return 0.5
        else:
            return 0.2  # Used non-whitelisted protocols

    def _score_governance_participation(self, participation_count: int, commitment_algo: Decimal) -> float:
        """Score based on governance participation."""
        if participation_count == 0:
            return 0.0

        participation_score = min(1.0, participation_count / 10)  # 10 periods = max score

        commitment_float = float(commitment_algo)
        min_commitment = self.config.algorand_specific_params.min_governance_commitment_algo
        commitment_score = min(1.0, commitment_float / min_commitment) if min_commitment > 0 else 0.0

        return (participation_score * 0.6) + (commitment_score * 0.4)

    def _score_staking_history(self, staking_periods: int, rewards_algo: Decimal) -> float:
        """Score based on staking history."""
        if staking_periods == 0:
            return 0.0

        period_score = min(1.0, staking_periods / 20)  # 20 periods = max score
        reward_score = min(1.0, float(rewards_algo) / 1000)  # 1000 ALGO rewards = max score

        return (period_score * 0.7) + (reward_score * 0.3)

    def _score_smart_contract_interactions(self, interactions: int, asa_created: int) -> float:
        """Score based on smart contract interactions and ASA creation."""
        interaction_score = min(1.0, interactions / 100)  # 100 interactions = max score
        creation_score = min(1.0, asa_created / 5)  # 5 ASAs created = max score

        return (interaction_score * 0.8) + (creation_score * 0.2)

    def _apply_algorand_bonuses(self, wallet_profile: AlgorandWalletProfile) -> float:
        """Apply Algorand-specific bonus scores."""
        bonus = 0.0
        params = self.config.algorand_specific_params

        # Governance participation bonus
        if (wallet_profile.governance_participation_count > 0 and
            wallet_profile.governance_commitment_algo >= params.min_governance_commitment_algo):
            bonus += params.governance_period_bonus

        # Consensus participation bonus
        if wallet_profile.consensus_participation_periods > 0:
            bonus += params.consensus_participation_bonus

        # ASA creation bonus
        if wallet_profile.asa_tokens_created > 0:
            bonus += params.asa_creation_bonus

        # Smart contract deployment bonus (inferred from high interaction count)
        if wallet_profile.smart_contracts_interacted > 50:
            bonus += params.smart_contract_deployment_bonus

        return bonus


class CreditScoringEngine:
    """Traditional credit scoring engine."""

    def __init__(self, config: RiskPremiumConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def analyze_credit_profile(self, credit_profile: CreditProfile) -> Tuple[float, Dict[str, float]]:
        """
        Analyze traditional credit profile and return score and breakdown.

        Args:
            credit_profile: Traditional credit profile data

        Returns:
            Tuple of (overall_score, score_breakdown)
        """
        scores = {}
        weights = self.config.credit_scoring_weights

        # Payment history scoring
        scores['payment_history'] = self._score_payment_history(credit_profile.payment_history_score)

        # Credit utilization scoring
        scores['credit_utilization'] = self._score_credit_utilization(credit_profile.credit_utilization)

        # Credit age scoring
        scores['credit_age'] = self._score_credit_age(credit_profile.credit_age_months)

        # Credit mix scoring
        scores['credit_mix'] = self._score_credit_mix(credit_profile.credit_mix_score)

        # New credit scoring
        scores['new_credit'] = self._score_new_credit(credit_profile.new_credit_score)

        # Calculate weighted overall score
        overall_score = (
            scores['payment_history'] * weights.payment_history +
            scores['credit_utilization'] * weights.credit_utilization +
            scores['credit_age'] * weights.credit_age +
            scores['credit_mix'] * weights.credit_mix +
            scores['new_credit'] * weights.new_credit
        )

        self.logger.info(f"Credit profile analysis completed. Overall score: {overall_score:.3f}")

        return overall_score, scores

    def _score_payment_history(self, payment_score: Optional[float]) -> float:
        """Score payment history component."""
        if payment_score is None:
            return 0.5  # Neutral score for missing data
        return max(0.0, min(1.0, payment_score))

    def _score_credit_utilization(self, utilization: Optional[float]) -> float:
        """Score credit utilization component."""
        if utilization is None:
            return 0.5  # Neutral score for missing data

        if utilization <= 0.1:  # Under 10%
            return 1.0
        elif utilization <= 0.3:  # Under 30%
            return 0.8
        elif utilization <= 0.5:  # Under 50%
            return 0.6
        elif utilization <= 0.7:  # Under 70%
            return 0.4
        else:
            return 0.2

    def _score_credit_age(self, age_months: Optional[int]) -> float:
        """Score credit age component."""
        if age_months is None:
            return 0.3  # Lower score for missing data

        if age_months >= 120:  # 10+ years
            return 1.0
        elif age_months >= 60:  # 5+ years
            return 0.8
        elif age_months >= 24:  # 2+ years
            return 0.6
        elif age_months >= 12:  # 1+ year
            return 0.4
        else:
            return 0.2

    def _score_credit_mix(self, mix_score: Optional[float]) -> float:
        """Score credit mix component."""
        if mix_score is None:
            return 0.5  # Neutral score for missing data
        return max(0.0, min(1.0, mix_score))

    def _score_new_credit(self, new_credit_score: Optional[float]) -> float:
        """Score new credit component."""
        if new_credit_score is None:
            return 0.5  # Neutral score for missing data
        return max(0.0, min(1.0, new_credit_score))


class RiskPremiumEngine:
    """Main risk premium assessment engine."""

    def __init__(self, config: RiskPremiumConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.logger = logging.getLogger(__name__)

        self.credit_engine = CreditScoringEngine(self.config)
        self.onchain_analyzer = OnChainBehaviorAnalyzer(self.config)

    async def assess_borrower_risk(
        self,
        borrower_id: str,
        credit_profile: Optional[CreditProfile] = None,
        wallet_profile: Optional[AlgorandWalletProfile] = None,
        cross_chain_profile: Optional[CrossChainProfile] = None,
        market_conditions: Optional[MarketConditions] = None
    ) -> RiskAssessment:
        """
        Comprehensive borrower risk assessment.

        Args:
            borrower_id: Unique borrower identifier
            credit_profile: Traditional credit profile
            wallet_profile: Algorand wallet behavior profile
            cross_chain_profile: Cross-chain activity profile
            market_conditions: Current market conditions

        Returns:
            Complete risk assessment with scoring and rate recommendations
        """
        self.logger.info(f"Starting risk assessment for borrower: {borrower_id}")

        assessment_details = {}
        component_scores = {}

        # Analyze credit profile
        if credit_profile:
            credit_score, credit_breakdown = await self.credit_engine.analyze_credit_profile(credit_profile)
            component_scores['credit'] = credit_score
            assessment_details['credit_breakdown'] = credit_breakdown
        else:
            component_scores['credit'] = 0.3  # Conservative default
            self.logger.warning("No credit profile provided, using conservative default")

        # Analyze on-chain behavior
        if wallet_profile:
            onchain_score, onchain_breakdown = await self.onchain_analyzer.analyze_wallet_behavior(wallet_profile)
            component_scores['onchain'] = onchain_score
            assessment_details['onchain_breakdown'] = onchain_breakdown
        else:
            component_scores['onchain'] = 0.2  # Conservative default
            self.logger.warning("No wallet profile provided, using conservative default")

        # Analyze cross-chain profile
        if cross_chain_profile:
            cross_chain_score = self._analyze_cross_chain_profile(cross_chain_profile)
            component_scores['cross_chain'] = cross_chain_score
            assessment_details['cross_chain_score'] = cross_chain_score
        else:
            component_scores['cross_chain'] = 0.0

        # Apply market condition adjustments
        if market_conditions:
            market_adjustment = self._calculate_market_adjustment(market_conditions)
            component_scores['market_adjustment'] = market_adjustment
            assessment_details['market_conditions'] = market_conditions
        else:
            component_scores['market_adjustment'] = 1.0  # Neutral

        # Calculate final risk score
        final_risk_score = self._calculate_final_risk_score(component_scores)

        # Determine risk category and premium
        risk_category = self._determine_risk_category(final_risk_score, component_scores['credit'])
        risk_premium_rate = self._calculate_risk_premium(risk_category, component_scores)

        # Calculate recommended interest rate
        recommended_rate = self.config.risk_premium_rates.base_rate + risk_premium_rate

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(credit_profile, wallet_profile)

        assessment = RiskAssessment(
            borrower_id=borrower_id,
            assessment_timestamp=datetime.utcnow(),
            credit_score_component=component_scores['credit'],
            onchain_behavior_component=component_scores['onchain'],
            cross_chain_component=component_scores['cross_chain'],
            market_adjustment_component=component_scores['market_adjustment'],
            final_risk_score=final_risk_score,
            risk_category=risk_category,
            risk_premium_rate=risk_premium_rate,
            recommended_interest_rate=recommended_rate,
            confidence_score=confidence_score,
            assessment_details=assessment_details
        )

        self.logger.info(f"Risk assessment completed for {borrower_id}. "
                        f"Category: {risk_category}, Premium: {risk_premium_rate:.3%}")

        return assessment

    def _analyze_cross_chain_profile(self, cross_chain_profile: CrossChainProfile) -> float:
        """Analyze cross-chain activity profile."""
        if not self.config.cross_chain_scoring.enabled_chains:
            return 0.0

        total_score = 0.0
        chain_weights = self.config.cross_chain_scoring.chain_weights

        # Score activity on each chain
        for chain in self.config.cross_chain_scoring.enabled_chains:
            chain_activity = getattr(cross_chain_profile, f"{chain}_activity", {})
            if chain_activity:
                chain_score = min(1.0, len(chain_activity.get('protocols', [])) / 5)
                total_score += chain_score * chain_weights.get(chain, 0.0)

        # Apply cross-chain bonus if minimum activity threshold met
        if cross_chain_profile.total_cross_chain_score >= self.config.cross_chain_scoring.min_cross_chain_activity:
            total_score += self.config.cross_chain_scoring.cross_chain_bonus

        return min(1.0, total_score)

    def _calculate_market_adjustment(self, market_conditions: MarketConditions) -> float:
        """Calculate market condition adjustment factor."""
        factors = self.config.market_condition_factors

        adjustment = 1.0

        # Volatility adjustment
        if market_conditions.volatility_index > 0.3:
            adjustment *= factors.volatility_multiplier

        # Liquidity adjustment
        if market_conditions.liquidity_ratio < 0.5:
            adjustment *= factors.liquidity_adjustment

        # Correlation penalty
        if market_conditions.correlation_factor > 0.7:
            adjustment *= factors.correlation_penalty

        # Market stress adjustment
        if market_conditions.market_stress_indicator > 0.5:
            adjustment *= factors.market_stress_multiplier

        return adjustment

    def _calculate_final_risk_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate final weighted risk score."""
        # Weight components based on data availability and reliability
        credit_weight = 0.5 if component_scores['credit'] > 0.3 else 0.3
        onchain_weight = 0.4 if component_scores['onchain'] > 0.2 else 0.6
        cross_chain_weight = 0.1 if component_scores['cross_chain'] > 0 else 0.0

        # Normalize weights
        total_weight = credit_weight + onchain_weight + cross_chain_weight
        if total_weight > 0:
            credit_weight /= total_weight
            onchain_weight /= total_weight
            cross_chain_weight /= total_weight

        base_score = (
            component_scores['credit'] * credit_weight +
            component_scores['onchain'] * onchain_weight +
            component_scores['cross_chain'] * cross_chain_weight
        )

        # Apply market adjustment
        adjusted_score = base_score / component_scores['market_adjustment']

        return max(0.0, min(1.0, adjusted_score))

    def _determine_risk_category(self, final_score: float, credit_score: float) -> str:
        """Determine risk category based on scores."""
        thresholds = self.config.risk_thresholds

        if final_score >= 0.8 and credit_score >= 0.8:
            return "excellent"
        elif final_score >= 0.6 and credit_score >= 0.6:
            return "good"
        elif final_score >= 0.4 and credit_score >= 0.4:
            return "fair"
        elif final_score >= 0.2:
            return "poor"
        else:
            return "high_risk"

    def _calculate_risk_premium(self, risk_category: str, component_scores: Dict[str, float]) -> Decimal:
        """Calculate risk premium based on category and component scores."""
        rates = self.config.risk_premium_rates

        # Base premium by category
        category_premiums = {
            "excellent": rates.excellent_premium,
            "good": rates.good_premium,
            "fair": rates.fair_premium,
            "poor": rates.poor_premium,
            "high_risk": rates.high_risk_premium
        }

        base_premium = category_premiums.get(risk_category, rates.high_risk_premium)

        # Apply on-chain behavior adjustments
        onchain_score = component_scores['onchain']
        if onchain_score >= 0.8:
            if risk_category in ["excellent", "good"]:
                base_premium -= rates.excellent_onchain_discount
            else:
                base_premium -= rates.good_onchain_discount
        elif onchain_score <= 0.3:
            base_premium += rates.poor_onchain_penalty

        # Apply market adjustment
        market_factor = Decimal(str(component_scores['market_adjustment']))
        adjusted_premium = base_premium * market_factor

        return max(Decimal('0.001'), adjusted_premium)  # Minimum 0.1% premium

    def _calculate_confidence_score(
        self,
        credit_profile: Optional[CreditProfile],
        wallet_profile: Optional[AlgorandWalletProfile]
    ) -> float:
        """Calculate confidence score based on data completeness and quality."""
        confidence = 0.0

        # Credit profile confidence
        if credit_profile:
            credit_data_points = sum(1 for field in [
                credit_profile.credit_score,
                credit_profile.credit_age_months,
                credit_profile.credit_utilization,
                credit_profile.payment_history_score
            ] if field is not None)
            confidence += (credit_data_points / 4) * 0.5

        # Wallet profile confidence
        if wallet_profile:
            wallet_confidence = 0.0
            if wallet_profile.wallet_age_days > 90:
                wallet_confidence += 0.2
            if wallet_profile.total_transactions > 10:
                wallet_confidence += 0.2
            if wallet_profile.defi_protocols_used:
                wallet_confidence += 0.2
            if wallet_profile.governance_participation_count > 0:
                wallet_confidence += 0.2
            if wallet_profile.smart_contracts_interacted > 0:
                wallet_confidence += 0.2

            confidence += wallet_confidence * 0.5

        return min(1.0, confidence)

    def generate_assessment_report(self, assessment: RiskAssessment) -> str:
        """Generate a detailed assessment report."""
        report = f"""
RISK ASSESSMENT REPORT
======================

Borrower ID: {assessment.borrower_id}
Assessment Date: {assessment.assessment_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

RISK SCORES
-----------
Credit Score Component: {assessment.credit_score_component:.3f}
On-Chain Behavior Component: {assessment.onchain_behavior_component:.3f}
Cross-Chain Component: {assessment.cross_chain_component:.3f}
Market Adjustment Factor: {assessment.market_adjustment_component:.3f}

FINAL ASSESSMENT
----------------
Final Risk Score: {assessment.final_risk_score:.3f}
Risk Category: {assessment.risk_category.upper()}
Risk Premium Rate: {assessment.risk_premium_rate:.3%}
Recommended Interest Rate: {assessment.recommended_interest_rate:.3%}
Confidence Score: {assessment.confidence_score:.3f}

DETAILED BREAKDOWN
------------------
{json.dumps(assessment.assessment_details, indent=2, default=str)}
"""
        return report