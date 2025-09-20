"""
Algorand Decision Logic Engine

Holistic decision tree logic for Algorand-native loan approvals based on
ecosystem participation, DeFi behavior, and governance engagement.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

from ..models.decision_models import (
    AlgorandBorrower, LoanDecision, DecisionType, RiskLevel,
    ApprovalConditions, RiskAssessment, HolisticRiskProfile
)
from .risk_scoring import RiskScoringEngine, RiskScoringConfig

logger = logging.getLogger(__name__)


@dataclass
class DecisionCriteria:
    """Decision criteria configuration"""
    # Automatic approval thresholds
    auto_approval_max_amount: float = 50000.0
    auto_approval_max_risk_score: float = 30.0
    auto_approval_min_ecosystem_score: float = 70.0

    # Automatic rejection thresholds
    auto_reject_min_risk_score: float = 80.0
    auto_reject_blacklist_interactions: int = 1
    auto_reject_min_wallet_age_days: int = 30

    # Manual review triggers
    review_large_amount_threshold: float = 100000.0
    review_medium_risk_threshold: float = 60.0
    review_new_borrower_threshold_days: int = 90

    # Collateral requirements
    base_collateral_ratio: float = 1.3
    high_risk_collateral_ratio: float = 2.0
    max_collateral_ratio: float = 3.0


@dataclass
class LoanRequest:
    """Loan request data structure"""
    borrower_address: str
    requested_amount: float
    loan_purpose: str
    duration_days: int
    proposed_collateral_amount: float
    proposed_collateral_assets: List[str]
    interest_rate_preference: Optional[float] = None


class AlgorandDecisionEngine:
    """
    Main decision engine for Algorand-native loan approvals.
    Integrates ecosystem analysis, risk scoring, and decision logic.
    """

    def __init__(
        self,
        decision_criteria: Optional[DecisionCriteria] = None,
        risk_scoring_config: Optional[RiskScoringConfig] = None
    ):
        self.criteria = decision_criteria or DecisionCriteria()
        self.risk_engine = RiskScoringEngine(risk_scoring_config)
        self.decision_history = {}

    async def evaluate_loan_request(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_profile: HolisticRiskProfile,
        ecosystem_data: Dict[str, Any]
    ) -> LoanDecision:
        """
        Evaluate loan request and make comprehensive decision.

        Args:
            loan_request: Loan request details
            borrower_profile: Complete borrower profile
            risk_profile: Comprehensive risk assessment
            ecosystem_data: Additional ecosystem analysis data

        Returns:
            Complete loan decision with conditions and rationale
        """
        logger.info(f"Evaluating loan request for {loan_request.borrower_address}")

        try:
            # Step 1: Quick eligibility checks
            eligibility_result = self._check_basic_eligibility(loan_request, borrower_profile)
            if eligibility_result['auto_reject']:
                return self._create_rejection_decision(
                    loan_request, borrower_profile, risk_profile,
                    eligibility_result['reasons']
                )

            # Step 2: Comprehensive risk assessment
            risk_assessment = await self._create_comprehensive_risk_assessment(
                borrower_profile, risk_profile, loan_request, ecosystem_data
            )

            # Step 3: Apply decision logic
            decision_result = await self._apply_decision_logic(
                loan_request, borrower_profile, risk_assessment, ecosystem_data
            )

            # Step 4: Generate final decision
            final_decision = self._create_final_decision(
                loan_request, borrower_profile, risk_assessment, decision_result
            )

            # Step 5: Store decision history
            self._store_decision_history(loan_request.borrower_address, final_decision)

            logger.info(f"Decision completed: {final_decision.decision_type.value}")
            return final_decision

        except Exception as e:
            logger.error(f"Decision evaluation failed: {e}")
            raise

    def _check_basic_eligibility(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower
    ) -> Dict[str, Any]:
        """Perform basic eligibility checks for immediate rejection"""
        reasons = []
        auto_reject = False

        # Wallet age check
        if borrower_profile.wallet_age_days < self.criteria.auto_reject_min_wallet_age_days:
            reasons.append(f"Wallet too new: {borrower_profile.wallet_age_days} days")
            auto_reject = True

        # Blacklist interactions check
        blacklist_count = getattr(borrower_profile, 'blacklisted_interactions', 0)
        if blacklist_count >= self.criteria.auto_reject_blacklist_interactions:
            reasons.append(f"Blacklisted interactions detected: {blacklist_count}")
            auto_reject = True

        # Basic transaction history check
        if borrower_profile.total_transaction_count < 5:
            reasons.append("Insufficient transaction history")
            auto_reject = True

        # Minimum ecosystem participation
        if (not borrower_profile.governance_participation and
            borrower_profile.dapp_count < 2 and
            borrower_profile.asset_count < 3):
            reasons.append("Minimal ecosystem participation")
            auto_reject = True

        return {
            'auto_reject': auto_reject,
            'reasons': reasons,
            'warnings': []
        }

    async def _create_comprehensive_risk_assessment(
        self,
        borrower_profile: AlgorandBorrower,
        risk_profile: HolisticRiskProfile,
        loan_request: LoanRequest,
        ecosystem_data: Dict[str, Any]
    ) -> RiskAssessment:
        """Create comprehensive risk assessment"""

        # Extract ecosystem components
        ecosystem_footprint = ecosystem_data.get('ecosystem_footprint')
        defi_behavior = ecosystem_data.get('defi_behavior')
        governance_participation = ecosystem_data.get('governance_participation')

        if not all([ecosystem_footprint, defi_behavior, governance_participation]):
            logger.warning("Incomplete ecosystem data for risk assessment")

        # Calculate risk scores using risk engine
        overall_risk_score, risk_level, risk_breakdown = self.risk_engine.calculate_comprehensive_risk_score(
            borrower_profile,
            ecosystem_footprint,
            defi_behavior,
            governance_participation,
            loan_request.requested_amount
        )

        # Calculate component risk scores
        component_risks = self._calculate_component_risks(
            borrower_profile, risk_profile, loan_request
        )

        # Identify specific risks and mitigants
        identified_risks = self._identify_specific_risks(
            borrower_profile, risk_profile, loan_request, risk_breakdown
        )

        risk_mitigants = self._identify_risk_mitigants(
            borrower_profile, risk_profile, ecosystem_data
        )

        monitoring_recommendations = self._generate_monitoring_recommendations(
            risk_level, identified_risks, loan_request
        )

        return RiskAssessment(
            wallet_age_risk=component_risks['wallet_age'],
            transaction_volume_risk=component_risks['transaction_volume'],
            asset_diversity_risk=component_risks['asset_diversity'],
            governance_participation_risk=component_risks['governance'],
            defi_behavior_risk=component_risks['defi_behavior'],
            cross_protocol_risk=component_risks['cross_protocol'],
            technical_risk_score=risk_breakdown['component_scores'].get('technical', 50.0),
            behavioral_risk_score=risk_breakdown['component_scores'].get('behavioral', 50.0),
            ecosystem_risk_score=risk_breakdown['component_scores'].get('ecosystem', 50.0),
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            identified_risks=identified_risks,
            risk_mitigants=risk_mitigants,
            monitoring_recommendations=monitoring_recommendations,
            weights_used=risk_breakdown['calculation_metadata']['weights_used']
        )

    async def _apply_decision_logic(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment,
        ecosystem_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply comprehensive decision logic"""

        decision_factors = []
        decision_type = DecisionType.NEEDS_REVIEW  # Default to review
        approved_amount = loan_request.requested_amount
        conditions = []

        # Auto-approval logic
        auto_approval_result = self._check_auto_approval_criteria(
            loan_request, borrower_profile, risk_assessment
        )

        if auto_approval_result['approve']:
            decision_type = DecisionType.APPROVED
            decision_factors.extend(auto_approval_result['factors'])
        else:
            # Auto-rejection logic
            auto_reject_result = self._check_auto_rejection_criteria(
                loan_request, borrower_profile, risk_assessment
            )

            if auto_reject_result['reject']:
                decision_type = DecisionType.REJECTED
                approved_amount = 0.0
                decision_factors.extend(auto_reject_result['factors'])
            else:
                # Conditional approval logic
                conditional_result = await self._evaluate_conditional_approval(
                    loan_request, borrower_profile, risk_assessment, ecosystem_data
                )

                decision_type = conditional_result['decision_type']
                approved_amount = conditional_result['approved_amount']
                conditions = conditional_result['conditions']
                decision_factors.extend(conditional_result['factors'])

        return {
            'decision_type': decision_type,
            'approved_amount': approved_amount,
            'decision_factors': decision_factors,
            'conditions': conditions,
            'confidence': self._calculate_decision_confidence(
                borrower_profile, risk_assessment, ecosystem_data
            )
        }

    def _check_auto_approval_criteria(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment
    ) -> Dict[str, Any]:
        """Check criteria for automatic approval"""
        factors = []
        approve = False

        # Check all auto-approval criteria
        amount_ok = loan_request.requested_amount <= self.criteria.auto_approval_max_amount
        risk_ok = risk_assessment.overall_risk_score <= self.criteria.auto_approval_max_risk_score
        ecosystem_ok = self._calculate_ecosystem_score(borrower_profile) >= self.criteria.auto_approval_min_ecosystem_score

        if amount_ok and risk_ok and ecosystem_ok:
            # Additional checks for auto-approval
            governance_ok = borrower_profile.governance_participation
            age_ok = borrower_profile.wallet_age_days >= 180  # 6 months
            activity_ok = borrower_profile.total_transaction_count >= 100

            if governance_ok and age_ok and activity_ok:
                approve = True
                factors = [
                    "Low risk score",
                    "Strong ecosystem participation",
                    "Governance participation",
                    "Mature wallet with good activity",
                    "Conservative loan amount"
                ]

        return {'approve': approve, 'factors': factors}

    def _check_auto_rejection_criteria(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment
    ) -> Dict[str, Any]:
        """Check criteria for automatic rejection"""
        factors = []
        reject = False

        # High risk score
        if risk_assessment.overall_risk_score >= self.criteria.auto_reject_min_risk_score:
            reject = True
            factors.append("Very high risk score")

        # Specific risk factors
        if 'blacklisted_interactions' in risk_assessment.identified_risks:
            reject = True
            factors.append("Blacklisted protocol interactions")

        if 'wash_trading_patterns' in risk_assessment.identified_risks:
            reject = True
            factors.append("Suspicious trading patterns")

        if 'governance_manipulation' in risk_assessment.identified_risks:
            reject = True
            factors.append("Governance manipulation detected")

        # Insufficient collateral
        required_collateral = self._calculate_required_collateral(
            loan_request.requested_amount, risk_assessment.overall_risk_score
        )
        if loan_request.proposed_collateral_amount < required_collateral:
            reject = True
            factors.append(f"Insufficient collateral: {loan_request.proposed_collateral_amount} < {required_collateral}")

        return {'reject': reject, 'factors': factors}

    async def _evaluate_conditional_approval(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment,
        ecosystem_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate conditions for conditional approval"""
        factors = []
        conditions = []
        decision_type = DecisionType.CONDITIONAL_APPROVAL
        approved_amount = loan_request.requested_amount

        # Risk-based amount adjustment
        if risk_assessment.overall_risk_score > 50:
            # Reduce loan amount for higher risk
            risk_factor = (100 - risk_assessment.overall_risk_score) / 100
            approved_amount = loan_request.requested_amount * max(risk_factor, 0.3)
            factors.append(f"Loan amount reduced due to risk score: {risk_assessment.overall_risk_score}")

        # Generate conditions based on risk factors
        conditions = self._generate_approval_conditions(
            loan_request, borrower_profile, risk_assessment
        )

        # Determine if manual review is needed
        if (loan_request.requested_amount > self.criteria.review_large_amount_threshold or
            risk_assessment.overall_risk_score > self.criteria.review_medium_risk_threshold or
            borrower_profile.wallet_age_days < self.criteria.review_new_borrower_threshold_days):
            decision_type = DecisionType.NEEDS_REVIEW
            factors.append("Manual review required")

        return {
            'decision_type': decision_type,
            'approved_amount': approved_amount,
            'conditions': conditions,
            'factors': factors
        }

    def _generate_approval_conditions(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment
    ) -> ApprovalConditions:
        """Generate specific approval conditions based on risk assessment"""

        # Calculate collateral requirements
        collateral_ratio = self._calculate_collateral_ratio(risk_assessment.overall_risk_score)

        # Determine accepted collateral types
        accepted_collateral = self._determine_accepted_collateral_types(
            borrower_profile, risk_assessment
        )

        # Monitoring requirements
        monitoring_required = risk_assessment.overall_risk_score > 40
        reporting_frequency = self._calculate_reporting_frequency(risk_assessment.overall_risk_score)

        # Behavioral constraints
        constraints = self._generate_behavioral_constraints(
            borrower_profile, risk_assessment
        )

        return ApprovalConditions(
            minimum_collateral_ratio=collateral_ratio,
            accepted_collateral_types=accepted_collateral,
            collateral_lock_period_days=max(30, loan_request.duration_days),
            continuous_monitoring_required=monitoring_required,
            reporting_frequency_days=reporting_frequency,
            governance_participation_required=risk_assessment.overall_risk_score > 60,
            maximum_new_protocol_interactions=constraints['max_new_protocols'],
            minimum_ecosystem_activity_score=constraints['min_activity_score'],
            blacklisted_protocol_restrictions=constraints['blacklisted_protocols'],
            maximum_additional_leverage=constraints['max_leverage'],
            minimum_stable_asset_percentage=constraints['min_stable_percentage'],
            drawdown_monitoring_threshold=constraints['drawdown_threshold']
        )

    def _create_final_decision(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment,
        decision_result: Dict[str, Any]
    ) -> LoanDecision:
        """Create final loan decision with all details"""

        # Calculate interest rate based on risk
        interest_rate = self._calculate_risk_adjusted_interest_rate(
            risk_assessment.overall_risk_score,
            loan_request.duration_days
        )

        # Create approval conditions if approved
        approval_conditions = None
        if decision_result['decision_type'] in [DecisionType.APPROVED, DecisionType.CONDITIONAL_APPROVAL]:
            approval_conditions = self._generate_approval_conditions(
                loan_request, borrower_profile, risk_assessment
            )

        # Determine review requirements
        requires_review = (
            decision_result['decision_type'] == DecisionType.NEEDS_REVIEW or
            loan_request.requested_amount > self.criteria.review_large_amount_threshold
        )

        review_priority = self._determine_review_priority(
            risk_assessment.overall_risk_score,
            loan_request.requested_amount
        )

        return LoanDecision(
            decision_type=decision_result['decision_type'],
            approved_amount=decision_result['approved_amount'],
            requested_amount=loan_request.requested_amount,
            interest_rate=interest_rate,
            loan_term_days=loan_request.duration_days,
            primary_decision_factors=decision_result['decision_factors'][:5],
            risk_mitigation_factors=risk_assessment.risk_mitigants[:3],
            approval_conditions=approval_conditions,
            decision_confidence=decision_result['confidence'],
            algorithm_version="algorand-native-v1.0",
            borrower_profile=borrower_profile,
            risk_profile=None,  # Would include HolisticRiskProfile
            requires_manual_review=requires_review,
            review_priority=review_priority,
            reviewer_notes=self._generate_reviewer_notes(
                borrower_profile, risk_assessment, decision_result
            )
        )

    def _create_rejection_decision(
        self,
        loan_request: LoanRequest,
        borrower_profile: AlgorandBorrower,
        risk_profile: Optional[HolisticRiskProfile],
        reasons: List[str]
    ) -> LoanDecision:
        """Create rejection decision with clear reasoning"""
        return LoanDecision(
            decision_type=DecisionType.REJECTED,
            approved_amount=0.0,
            requested_amount=loan_request.requested_amount,
            interest_rate=0.0,
            loan_term_days=0,
            primary_decision_factors=reasons,
            risk_mitigation_factors=[],
            approval_conditions=None,
            decision_confidence=0.95,  # High confidence in rejection
            algorithm_version="algorand-native-v1.0",
            borrower_profile=borrower_profile,
            risk_profile=risk_profile,
            requires_manual_review=False,
            review_priority="low",
            reviewer_notes=f"Automatic rejection: {', '.join(reasons)}"
        )

    def _calculate_ecosystem_score(self, borrower_profile: AlgorandBorrower) -> float:
        """Calculate overall ecosystem participation score"""
        score = 0.0

        # Governance participation (0-30 points)
        if borrower_profile.governance_participation:
            score += 25.0
        if borrower_profile.validator_participation:
            score += 5.0

        # DApp usage (0-25 points)
        score += min(borrower_profile.dapp_count * 3, 25.0)

        # Asset diversity (0-20 points)
        score += min(borrower_profile.asset_count * 2, 20.0)

        # Transaction activity (0-15 points)
        score += min(borrower_profile.total_transaction_count / 100 * 15, 15.0)

        # Wallet maturity (0-10 points)
        score += min(borrower_profile.wallet_age_days / 365 * 10, 10.0)

        return min(score, 100.0)

    def _calculate_component_risks(
        self,
        borrower_profile: AlgorandBorrower,
        risk_profile: HolisticRiskProfile,
        loan_request: LoanRequest
    ) -> Dict[str, float]:
        """Calculate individual component risk scores"""
        return {
            'wallet_age': max(0, 100 - borrower_profile.wallet_age_days / 10),
            'transaction_volume': 100 - min(borrower_profile.total_volume_algo / 1000, 100),
            'asset_diversity': 100 - min(borrower_profile.asset_count * 10, 100),
            'governance': 0 if borrower_profile.governance_participation else 80,
            'defi_behavior': 100 - min(borrower_profile.dapp_count * 15, 100),
            'cross_protocol': 30  # Default medium risk
        }

    def _identify_specific_risks(
        self,
        borrower_profile: AlgorandBorrower,
        risk_profile: HolisticRiskProfile,
        loan_request: LoanRequest,
        risk_breakdown: Dict[str, Any]
    ) -> List[str]:
        """Identify specific risk factors"""
        risks = []

        if borrower_profile.wallet_age_days < 90:
            risks.append("new_wallet")

        if not borrower_profile.governance_participation:
            risks.append("no_governance_participation")

        if borrower_profile.dapp_count < 3:
            risks.append("limited_defi_experience")

        if risk_profile.volatility_exposure_score > 80:
            risks.append("high_volatility_exposure")

        if risk_profile.concentration_risk_score > 70:
            risks.append("portfolio_concentration")

        return risks

    def _identify_risk_mitigants(
        self,
        borrower_profile: AlgorandBorrower,
        risk_profile: HolisticRiskProfile,
        ecosystem_data: Dict[str, Any]
    ) -> List[str]:
        """Identify factors that mitigate risk"""
        mitigants = []

        if borrower_profile.governance_participation:
            mitigants.append("active_governance_participation")

        if borrower_profile.wallet_age_days > 365:
            mitigants.append("mature_wallet")

        if borrower_profile.reputation_score > 75:
            mitigants.append("high_reputation_score")

        if risk_profile.ecosystem_trust_score > 70:
            mitigants.append("strong_ecosystem_trust")

        if risk_profile.financial_sophistication_score > 70:
            mitigants.append("high_financial_sophistication")

        return mitigants

    def _generate_monitoring_recommendations(
        self,
        risk_level: RiskLevel,
        identified_risks: List[str],
        loan_request: LoanRequest
    ) -> List[str]:
        """Generate monitoring recommendations based on risk"""
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            recommendations.append("Daily portfolio monitoring required")
            recommendations.append("Weekly governance participation check")

        if "high_volatility_exposure" in identified_risks:
            recommendations.append("Monitor asset volatility and drawdowns")

        if "portfolio_concentration" in identified_risks:
            recommendations.append("Track diversification changes")

        if loan_request.requested_amount > 50000:
            recommendations.append("Monitor large transaction patterns")

        return recommendations

    def _calculate_required_collateral(self, loan_amount: float, risk_score: float) -> float:
        """Calculate required collateral based on loan amount and risk"""
        base_ratio = self.criteria.base_collateral_ratio

        if risk_score > 70:
            ratio = self.criteria.high_risk_collateral_ratio
        elif risk_score > 50:
            ratio = base_ratio + (risk_score - 50) / 50 * (self.criteria.high_risk_collateral_ratio - base_ratio)
        else:
            ratio = base_ratio

        return loan_amount * min(ratio, self.criteria.max_collateral_ratio)

    def _calculate_collateral_ratio(self, risk_score: float) -> float:
        """Calculate collateral ratio based on risk score"""
        if risk_score > 70:
            return self.criteria.high_risk_collateral_ratio
        elif risk_score > 50:
            return self.criteria.base_collateral_ratio + (risk_score - 50) / 50 * 0.5
        else:
            return self.criteria.base_collateral_ratio

    def _determine_accepted_collateral_types(
        self,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment
    ) -> List[str]:
        """Determine accepted collateral asset types"""
        accepted_types = ["ALGO", "USDC", "USDT"]  # Always accept stable assets

        # Add other assets based on risk level
        if risk_assessment.overall_risk_score < 50:
            accepted_types.extend(["goBTC", "goETH"])

        if risk_assessment.overall_risk_score < 30:
            accepted_types.extend(["LP_TOKENS"])

        return accepted_types

    def _calculate_reporting_frequency(self, risk_score: float) -> int:
        """Calculate reporting frequency in days based on risk"""
        if risk_score > 70:
            return 7   # Weekly
        elif risk_score > 50:
            return 14  # Bi-weekly
        elif risk_score > 30:
            return 30  # Monthly
        else:
            return 90  # Quarterly

    def _generate_behavioral_constraints(
        self,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment
    ) -> Dict[str, Any]:
        """Generate behavioral constraints based on risk"""
        return {
            'max_new_protocols': 3 if risk_assessment.overall_risk_score > 60 else 5,
            'min_activity_score': 0.7 if risk_assessment.overall_risk_score > 50 else 0.5,
            'blacklisted_protocols': [],  # Would be populated from risk analysis
            'max_leverage': 1.5 if risk_assessment.overall_risk_score > 60 else 2.0,
            'min_stable_percentage': 0.3 if risk_assessment.overall_risk_score > 60 else 0.2,
            'drawdown_threshold': 0.2 if risk_assessment.overall_risk_score > 50 else 0.3
        }

    def _calculate_risk_adjusted_interest_rate(
        self,
        risk_score: float,
        duration_days: int
    ) -> float:
        """Calculate risk-adjusted interest rate"""
        base_rate = 0.05  # 5% base annual rate

        # Risk adjustment
        risk_premium = risk_score / 100 * 0.1  # Up to 10% additional for high risk

        # Duration adjustment
        duration_premium = max(0, (duration_days - 365) / 365 * 0.02)  # 2% for each year beyond 1

        annual_rate = base_rate + risk_premium + duration_premium
        return min(annual_rate, 0.25)  # Cap at 25%

    def _determine_review_priority(self, risk_score: float, loan_amount: float) -> str:
        """Determine review priority"""
        if risk_score > 80 or loan_amount > 200000:
            return "urgent"
        elif risk_score > 60 or loan_amount > 100000:
            return "high"
        elif risk_score > 40 or loan_amount > 50000:
            return "normal"
        else:
            return "low"

    def _calculate_decision_confidence(
        self,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment,
        ecosystem_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence in decision"""
        confidence = 0.7  # Base confidence

        # More data = higher confidence
        if borrower_profile.total_transaction_count > 100:
            confidence += 0.1

        if borrower_profile.wallet_age_days > 180:
            confidence += 0.1

        if borrower_profile.governance_participation:
            confidence += 0.05

        # Risk assessment quality
        if len(risk_assessment.risk_mitigants) > 2:
            confidence += 0.05

        return min(confidence, 0.95)

    def _generate_reviewer_notes(
        self,
        borrower_profile: AlgorandBorrower,
        risk_assessment: RiskAssessment,
        decision_result: Dict[str, Any]
    ) -> str:
        """Generate notes for manual reviewers"""
        notes = []

        notes.append(f"Risk Score: {risk_assessment.overall_risk_score:.1f}")
        notes.append(f"Wallet Age: {borrower_profile.wallet_age_days} days")
        notes.append(f"Governance: {'Yes' if borrower_profile.governance_participation else 'No'}")

        if risk_assessment.identified_risks:
            notes.append(f"Key Risks: {', '.join(risk_assessment.identified_risks[:3])}")

        if risk_assessment.risk_mitigants:
            notes.append(f"Mitigants: {', '.join(risk_assessment.risk_mitigants[:3])}")

        return " | ".join(notes)

    def _store_decision_history(self, borrower_address: str, decision: LoanDecision):
        """Store decision in history for future reference"""
        if borrower_address not in self.decision_history:
            self.decision_history[borrower_address] = []

        self.decision_history[borrower_address].append({
            'timestamp': decision.decision_timestamp,
            'decision_type': decision.decision_type,
            'amount': decision.approved_amount,
            'risk_score': decision.risk_profile.overall_risk_score if decision.risk_profile else 0
        })

        # Keep only last 10 decisions
        self.decision_history[borrower_address] = self.decision_history[borrower_address][-10:]

    def get_borrower_history(self, borrower_address: str) -> List[Dict[str, Any]]:
        """Get decision history for a borrower"""
        return self.decision_history.get(borrower_address, [])