"""
Approval Logic Engine for Holistic Loan Decisions

Implements sophisticated decision logic that considers holistic scores,
risk factors, and Algorand ecosystem context to make final approval decisions.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from .decision_orchestrator import LoanDecision, DecisionConfidence, BorrowerProfile, LoanApplication


class RiskLevel(Enum):
    """Risk level categories"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ApprovalLogic:
    """
    Advanced approval logic that makes final loan decisions based on
    holistic scores and comprehensive risk assessment.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.thresholds = config.get('approval_thresholds', {})
        self.confidence_req = config.get('confidence_requirements', {})
        self.logger = logging.getLogger("approval_logic")

        # Decision parameters
        self.max_loan_amount = config.get('risk_management', {}).get('max_loan_amount', 1000000)
        self.min_confidence = self.confidence_req.get('minimum_confidence', 0.75)

    async def make_decision(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Dict[str, Any]:
        """
        Make final loan approval decision based on holistic analysis.

        Returns comprehensive decision with rationale and loan terms.
        """

        self.logger.info(f"Making decision for application {application.application_id}")

        # Step 1: Extract key metrics
        overall_score = holistic_scores['overall_score']
        confidence_level = holistic_scores['confidence_level']
        data_completeness = holistic_scores['data_completeness']

        # Step 2: Assess risk factors
        risk_assessment = self._assess_risk_factors(holistic_scores, application, profile)

        # Step 3: Check minimum requirements
        eligibility_check = self._check_eligibility(overall_score, confidence_level, data_completeness)

        # Step 4: Determine base decision
        base_decision = self._determine_base_decision(overall_score, risk_assessment)

        # Step 5: Apply risk adjustments
        adjusted_decision = self._apply_risk_adjustments(
            base_decision, risk_assessment, application
        )

        # Step 6: Calculate loan terms
        loan_terms = self._calculate_loan_terms(
            adjusted_decision, overall_score, application, risk_assessment
        )

        # Step 7: Generate decision rationale
        rationale = self._generate_decision_rationale(
            overall_score, risk_assessment, adjusted_decision, holistic_scores
        )

        # Step 8: Determine final confidence
        decision_confidence = self._calculate_decision_confidence(
            confidence_level, data_completeness, risk_assessment
        )

        return {
            'decision': adjusted_decision,
            'confidence': decision_confidence,
            'overall_score': overall_score,

            'approved_amount': loan_terms.get('approved_amount'),
            'interest_rate': loan_terms.get('interest_rate'),
            'loan_term': loan_terms.get('loan_term'),
            'ltv_ratio': loan_terms.get('ltv_ratio'),

            'risk_level': risk_assessment['risk_level'],
            'risk_score': risk_assessment['risk_score'],

            'primary_factors': rationale['primary_factors'],
            'risk_factors': rationale['risk_factors'],
            'positive_factors': rationale['positive_factors'],

            'eligibility_check': eligibility_check,
            'base_decision': base_decision,

            'decision_metadata': {
                'timestamp': datetime.now(),
                'confidence_level': confidence_level,
                'data_completeness': data_completeness,
                'processing_version': '1.0.0'
            }
        }

    def _assess_risk_factors(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Dict[str, Any]:
        """
        Comprehensive risk factor assessment.
        """

        risk_factors = []
        risk_score = 0.0
        risk_weights = {}

        # 1. Score-based risk assessment
        overall_score = holistic_scores['overall_score']
        if overall_score < 0.4:
            risk_factors.append("Low overall creditworthiness score")
            risk_score += 0.3
            risk_weights['score_risk'] = 0.3

        # 2. Confidence-based risk
        confidence_level = holistic_scores['confidence_level']
        if confidence_level < 0.6:
            risk_factors.append("Low confidence in assessment due to limited data")
            risk_score += 0.2
            risk_weights['confidence_risk'] = 0.2

        # 3. Individual engine risks
        engine_scores = holistic_scores['engine_scores']

        # Ecosystem risk
        ecosystem_score = engine_scores['ecosystem_analysis']['score']
        if ecosystem_score < 0.5:
            risk_factors.append("Limited Algorand ecosystem participation")
            risk_score += 0.15
            risk_weights['ecosystem_risk'] = 0.15

        # DeFi behavior risk
        defi_score = engine_scores['defi_behavior']['score']
        if defi_score < 0.4:
            risk_factors.append("Poor DeFi risk management history")
            risk_score += 0.2
            risk_weights['defi_risk'] = 0.2

        # Collateral risk
        collateral_score = engine_scores['collateral_intelligence']['score']
        if collateral_score < 0.6:
            risk_factors.append("High collateral risk or poor asset quality")
            risk_score += 0.25
            risk_weights['collateral_risk'] = 0.25

        # Governance risk
        governance_score = engine_scores['governance_reputation']['score']
        if governance_score < 0.3:
            risk_factors.append("No governance participation or community engagement")
            risk_score += 0.1
            risk_weights['governance_risk'] = 0.1

        # Network risk
        network_risk_score = engine_scores['network_risk_monitoring']['score']
        if network_risk_score < 0.6:
            risk_factors.append("High network or systemic risk exposure")
            risk_score += 0.15
            risk_weights['network_risk'] = 0.15

        # 4. Application-specific risks
        loan_amount = application.loan_amount
        collateral_value = self._estimate_collateral_value(profile)

        if collateral_value > 0:
            ltv_ratio = loan_amount / collateral_value
            if ltv_ratio > 0.8:
                risk_factors.append(f"High LTV ratio: {ltv_ratio:.2f}")
                risk_score += 0.2
                risk_weights['ltv_risk'] = 0.2
            elif ltv_ratio > 0.7:
                risk_factors.append(f"Elevated LTV ratio: {ltv_ratio:.2f}")
                risk_score += 0.1
                risk_weights['ltv_risk'] = 0.1

        # Large loan risk
        if loan_amount > self.max_loan_amount * 0.5:
            risk_factors.append("Large loan amount relative to platform limits")
            risk_score += 0.1
            risk_weights['amount_risk'] = 0.1

        # 5. Market condition risks
        market_conditions = getattr(application, 'market_conditions', {})
        volatility = market_conditions.get('volatility', 0.2)
        if volatility > 0.4:
            risk_factors.append("High market volatility conditions")
            risk_score += 0.15
            risk_weights['market_risk'] = 0.15

        # 6. Determine overall risk level
        risk_level = self._categorize_risk_level(risk_score)

        return {
            'risk_score': min(1.0, risk_score),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_weights': risk_weights,
            'individual_risks': {
                'score_risk': risk_weights.get('score_risk', 0),
                'confidence_risk': risk_weights.get('confidence_risk', 0),
                'ecosystem_risk': risk_weights.get('ecosystem_risk', 0),
                'defi_risk': risk_weights.get('defi_risk', 0),
                'collateral_risk': risk_weights.get('collateral_risk', 0),
                'governance_risk': risk_weights.get('governance_risk', 0),
                'network_risk': risk_weights.get('network_risk', 0),
                'ltv_risk': risk_weights.get('ltv_risk', 0),
                'amount_risk': risk_weights.get('amount_risk', 0),
                'market_risk': risk_weights.get('market_risk', 0)
            }
        }

    def _categorize_risk_level(self, risk_score: float) -> RiskLevel:
        """Categorize risk score into risk levels"""
        if risk_score >= 0.8:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW

    def _check_eligibility(
        self,
        overall_score: float,
        confidence_level: float,
        data_completeness: float
    ) -> Dict[str, Any]:
        """
        Check basic eligibility requirements.
        """

        eligibility_checks = {}
        is_eligible = True

        # Minimum score requirement
        min_score = 0.3  # Very low threshold for consideration
        eligibility_checks['min_score'] = overall_score >= min_score
        if not eligibility_checks['min_score']:
            is_eligible = False

        # Minimum confidence requirement
        eligibility_checks['min_confidence'] = confidence_level >= self.min_confidence
        if not eligibility_checks['min_confidence']:
            is_eligible = False

        # Minimum data completeness
        min_completeness = 0.5
        eligibility_checks['min_data'] = data_completeness >= min_completeness
        if not eligibility_checks['min_data']:
            is_eligible = False

        return {
            'is_eligible': is_eligible,
            'checks': eligibility_checks,
            'requirements': {
                'min_score': min_score,
                'min_confidence': self.min_confidence,
                'min_data_completeness': min_completeness
            }
        }

    def _determine_base_decision(
        self,
        overall_score: float,
        risk_assessment: Dict[str, Any]
    ) -> LoanDecision:
        """
        Determine base decision based on score and risk thresholds.
        """

        # Get configured thresholds
        excellent_threshold = self.thresholds.get('excellent', 0.85)
        good_threshold = self.thresholds.get('good', 0.70)
        fair_threshold = self.thresholds.get('fair', 0.55)
        poor_threshold = self.thresholds.get('poor', 0.40)

        risk_level = risk_assessment['risk_level']

        # Excellent score
        if overall_score >= excellent_threshold:
            if risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]:
                return LoanDecision.APPROVED
            elif risk_level == RiskLevel.MEDIUM:
                return LoanDecision.CONDITIONALLY_APPROVED
            else:
                return LoanDecision.REQUIRES_REVIEW

        # Good score
        elif overall_score >= good_threshold:
            if risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]:
                return LoanDecision.APPROVED
            elif risk_level == RiskLevel.MEDIUM:
                return LoanDecision.CONDITIONALLY_APPROVED
            else:
                return LoanDecision.REJECTED

        # Fair score
        elif overall_score >= fair_threshold:
            if risk_level == RiskLevel.VERY_LOW:
                return LoanDecision.CONDITIONALLY_APPROVED
            elif risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                return LoanDecision.CONDITIONALLY_APPROVED
            else:
                return LoanDecision.REJECTED

        # Poor score
        elif overall_score >= poor_threshold:
            if risk_level == RiskLevel.VERY_LOW:
                return LoanDecision.CONDITIONALLY_APPROVED
            else:
                return LoanDecision.REJECTED

        # Very poor score
        else:
            return LoanDecision.REJECTED

    def _apply_risk_adjustments(
        self,
        base_decision: LoanDecision,
        risk_assessment: Dict[str, Any],
        application: LoanApplication
    ) -> LoanDecision:
        """
        Apply risk-based adjustments to base decision.
        """

        adjusted_decision = base_decision
        risk_score = risk_assessment['risk_score']
        risk_level = risk_assessment['risk_level']

        # High risk adjustments
        if risk_level == RiskLevel.VERY_HIGH:
            if adjusted_decision == LoanDecision.APPROVED:
                adjusted_decision = LoanDecision.CONDITIONALLY_APPROVED
            elif adjusted_decision == LoanDecision.CONDITIONALLY_APPROVED:
                adjusted_decision = LoanDecision.REJECTED

        elif risk_level == RiskLevel.HIGH:
            if adjusted_decision == LoanDecision.APPROVED:
                adjusted_decision = LoanDecision.CONDITIONALLY_APPROVED

        # Large loan amount adjustments
        if application.loan_amount > self.max_loan_amount * 0.7:
            if adjusted_decision == LoanDecision.APPROVED:
                adjusted_decision = LoanDecision.CONDITIONALLY_APPROVED

        return adjusted_decision

    def _calculate_loan_terms(
        self,
        decision: LoanDecision,
        overall_score: float,
        application: LoanApplication,
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate loan terms based on decision and risk assessment.
        """

        if decision == LoanDecision.REJECTED:
            return {}

        # Base terms from config
        loan_conditions = self.config.get('loan_conditions', {})
        ltv_ratios = loan_conditions.get('ltv_ratios', {})
        rate_adjustments = loan_conditions.get('interest_rate_adjustments', {})

        # Determine borrower tier
        if overall_score >= 0.85:
            tier = 'excellent'
        elif overall_score >= 0.70:
            tier = 'good'
        elif overall_score >= 0.55:
            tier = 'fair'
        else:
            tier = 'poor'

        # Calculate approved amount
        requested_amount = application.loan_amount
        max_ltv = ltv_ratios.get(tier, 0.70)

        # Estimate collateral value and calculate max loan
        collateral_value = self._estimate_collateral_value(application)
        max_loan_from_collateral = collateral_value * max_ltv if collateral_value > 0 else requested_amount

        # Apply risk adjustments to amount
        risk_multiplier = 1.0 - (risk_assessment['risk_score'] * 0.3)
        risk_adjusted_max = max_loan_from_collateral * risk_multiplier

        approved_amount = min(requested_amount, risk_adjusted_max, self.max_loan_amount)

        # Calculate interest rate adjustment
        base_rate = 0.08  # 8% base rate
        rate_adjustment = rate_adjustments.get(tier, 0.0)
        risk_premium = risk_assessment['risk_score'] * 0.05  # Up to 5% risk premium

        interest_rate = base_rate + rate_adjustment + risk_premium

        # Calculate final LTV
        final_ltv = approved_amount / collateral_value if collateral_value > 0 else 0.0

        return {
            'approved_amount': approved_amount,
            'interest_rate': interest_rate,
            'loan_term': application.requested_term,
            'ltv_ratio': final_ltv,
            'tier': tier,
            'max_ltv': max_ltv,
            'risk_premium': risk_premium,
            'collateral_value': collateral_value
        }

    def _estimate_collateral_value(self, source) -> float:
        """
        Estimate total collateral value from profile or application.
        """

        if hasattr(source, 'collateral_assets'):
            # From application
            total_value = 0.0
            for asset in source.collateral_assets:
                total_value += asset.get('value', 0.0)
            return total_value

        elif hasattr(source, 'collateral_data'):
            # From profile
            return source.collateral_data.get('total_collateral_value', 0.0)

        return 0.0

    def _generate_decision_rationale(
        self,
        overall_score: float,
        risk_assessment: Dict[str, Any],
        decision: LoanDecision,
        holistic_scores: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate human-readable rationale for the decision.
        """

        primary_factors = []
        risk_factors = risk_assessment['risk_factors']
        positive_factors = []

        # Primary decision factors
        if overall_score >= 0.85:
            primary_factors.append("Excellent overall creditworthiness score")
        elif overall_score >= 0.70:
            primary_factors.append("Good overall creditworthiness score")
        elif overall_score >= 0.55:
            primary_factors.append("Fair overall creditworthiness score")
        else:
            primary_factors.append("Poor overall creditworthiness score")

        # Positive factors from engine scores
        engine_scores = holistic_scores['engine_scores']

        if engine_scores['ecosystem_analysis']['score'] >= 0.7:
            positive_factors.append("Strong Algorand ecosystem participation")

        if engine_scores['defi_behavior']['score'] >= 0.7:
            positive_factors.append("Excellent DeFi risk management history")

        if engine_scores['collateral_intelligence']['score'] >= 0.8:
            positive_factors.append("High-quality collateral portfolio")

        if engine_scores['governance_reputation']['score'] >= 0.6:
            positive_factors.append("Active governance participation")

        if engine_scores['network_risk_monitoring']['score'] >= 0.8:
            positive_factors.append("Low network risk exposure")

        # Data quality factors
        if holistic_scores['confidence_level'] >= 0.9:
            positive_factors.append("High confidence in assessment data")

        if holistic_scores['data_completeness'] >= 0.9:
            positive_factors.append("Comprehensive data availability")

        # Decision-specific factors
        if decision == LoanDecision.APPROVED:
            primary_factors.append("Meets all approval criteria")
        elif decision == LoanDecision.CONDITIONALLY_APPROVED:
            primary_factors.append("Approved with additional conditions")
        elif decision == LoanDecision.REJECTED:
            primary_factors.append("Does not meet minimum approval criteria")

        return {
            'primary_factors': primary_factors,
            'risk_factors': risk_factors,
            'positive_factors': positive_factors
        }

    def _calculate_decision_confidence(
        self,
        confidence_level: float,
        data_completeness: float,
        risk_assessment: Dict[str, Any]
    ) -> DecisionConfidence:
        """
        Calculate confidence in the final decision.
        """

        # Base confidence from data quality
        base_confidence = (confidence_level + data_completeness) / 2

        # Adjust for risk clarity
        risk_score = risk_assessment['risk_score']
        if risk_score < 0.2 or risk_score > 0.8:
            # Clear risk profile increases confidence
            risk_clarity_bonus = 0.1
        else:
            # Ambiguous risk profile decreases confidence
            risk_clarity_bonus = -0.1

        final_confidence = base_confidence + risk_clarity_bonus

        # Categorize confidence
        if final_confidence >= 0.9:
            return DecisionConfidence.VERY_HIGH
        elif final_confidence >= 0.8:
            return DecisionConfidence.HIGH
        elif final_confidence >= 0.7:
            return DecisionConfidence.MEDIUM
        elif final_confidence >= 0.6:
            return DecisionConfidence.LOW
        else:
            return DecisionConfidence.VERY_LOW