"""
Alternative Proposer for Holistic Loan Decisions

Generates alternative loan terms and strategies when the original application
is rejected, helping borrowers understand paths to approval.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .decision_orchestrator import BorrowerProfile, LoanApplication


class AlternativeType(Enum):
    """Types of alternatives that can be proposed"""
    REDUCED_AMOUNT = "reduced_amount"
    ADDITIONAL_COLLATERAL = "additional_collateral"
    CO_SIGNER = "co_signer"
    SHORTER_TERM = "shorter_term"
    HIGHER_INTEREST = "higher_interest"
    IMPROVEMENT_PLAN = "improvement_plan"
    STAGED_APPROVAL = "staged_approval"


@dataclass
class Alternative:
    """Individual alternative proposal"""
    alternative_type: AlternativeType
    title: str
    description: str
    new_terms: Dict[str, Any]
    requirements: List[str]
    timeline: str
    probability_improvement: float  # Expected score improvement
    rationale: str


class AlternativeProposer:
    """
    Generates intelligent alternatives for rejected loan applications.

    Analyzes the specific reasons for rejection and proposes concrete
    alternatives that address the identified deficiencies.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.alternatives_config = config.get('alternative_terms', {})
        self.logger = logging.getLogger("alternative_proposer")

        # Alternative generation is enabled by default
        self.enabled = self.alternatives_config.get('enable_alternatives', True)
        self.max_alternatives = self.alternatives_config.get('max_alternatives', 3)

    async def propose_alternatives(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative proposals for rejected applications.

        Returns list of alternative options with specific terms and requirements.
        """

        if not self.enabled:
            return []

        self.logger.info(f"Generating alternatives for application {application.application_id}")

        # Analyze rejection reasons
        rejection_analysis = self._analyze_rejection_reasons(holistic_scores, application, profile)

        # Generate alternatives based on analysis
        alternatives = self._generate_alternatives(
            rejection_analysis, holistic_scores, application, profile
        )

        # Rank and filter alternatives
        ranked_alternatives = self._rank_alternatives(alternatives, rejection_analysis)

        # Convert to dictionaries for JSON serialization
        alternative_dicts = []
        for alt in ranked_alternatives[:self.max_alternatives]:
            alternative_dicts.append({
                'type': alt.alternative_type.value,
                'title': alt.title,
                'description': alt.description,
                'new_terms': alt.new_terms,
                'requirements': alt.requirements,
                'timeline': alt.timeline,
                'probability_improvement': alt.probability_improvement,
                'rationale': alt.rationale
            })

        self.logger.info(f"Generated {len(alternative_dicts)} alternatives")
        return alternative_dicts

    def _analyze_rejection_reasons(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Dict[str, Any]:
        """
        Analyze specific reasons for rejection to guide alternative generation.
        """

        overall_score = holistic_scores['overall_score']
        engine_scores = holistic_scores['engine_scores']
        confidence_level = holistic_scores['confidence_level']

        analysis = {
            'overall_score': overall_score,
            'confidence_level': confidence_level,
            'primary_weaknesses': [],
            'addressable_issues': [],
            'score_gaps': {}
        }

        # Identify primary weaknesses in each engine
        for engine_name, engine_data in engine_scores.items():
            score = engine_data['score']
            confidence = engine_data['confidence']

            if score < 0.5:
                analysis['primary_weaknesses'].append(engine_name)

            # Calculate score gap to approval threshold
            gap_to_good = max(0, 0.70 - score)
            analysis['score_gaps'][engine_name] = gap_to_good

        # Identify addressable issues
        if 'ecosystem_analysis' in analysis['primary_weaknesses']:
            analysis['addressable_issues'].append('ecosystem_participation')

        if 'collateral_intelligence' in analysis['primary_weaknesses']:
            analysis['addressable_issues'].append('collateral_quality')

        if 'defi_behavior' in analysis['primary_weaknesses']:
            analysis['addressable_issues'].append('defi_experience')

        if 'governance_reputation' in analysis['primary_weaknesses']:
            analysis['addressable_issues'].append('governance_participation')

        # Check if low confidence is due to insufficient data
        if confidence_level < 0.7:
            analysis['addressable_issues'].append('data_insufficiency')

        # Check loan-specific issues
        collateral_value = profile.collateral_data.get('total_collateral_value', 0)
        if collateral_value > 0:
            ltv_ratio = application.loan_amount / collateral_value
            if ltv_ratio > 0.8:
                analysis['addressable_issues'].append('high_ltv')

        return analysis

    def _generate_alternatives(
        self,
        rejection_analysis: Dict[str, Any],
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[Alternative]:
        """
        Generate specific alternatives based on rejection analysis.
        """

        alternatives = []
        addressable_issues = rejection_analysis['addressable_issues']

        # 1. Reduced loan amount alternative
        if 'high_ltv' in addressable_issues or 'collateral_quality' in addressable_issues:
            reduced_alt = self._create_reduced_amount_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(reduced_alt)

        # 2. Additional collateral alternative
        if 'collateral_quality' in addressable_issues or 'high_ltv' in addressable_issues:
            collateral_alt = self._create_additional_collateral_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(collateral_alt)

        # 3. Co-signer alternative
        if rejection_analysis['overall_score'] < 0.5:
            cosigner_alt = self._create_cosigner_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(cosigner_alt)

        # 4. Shorter term alternative
        if application.requested_term > 180:  # More than 6 months
            shorter_term_alt = self._create_shorter_term_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(shorter_term_alt)

        # 5. Higher interest rate alternative
        if rejection_analysis['overall_score'] > 0.35:  # Not completely hopeless
            higher_rate_alt = self._create_higher_interest_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(higher_rate_alt)

        # 6. Improvement plan alternative
        if 'ecosystem_participation' in addressable_issues or 'defi_experience' in addressable_issues:
            improvement_alt = self._create_improvement_plan_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(improvement_alt)

        # 7. Staged approval alternative
        if len(addressable_issues) <= 2:  # Limited number of issues
            staged_alt = self._create_staged_approval_alternative(
                rejection_analysis, application, profile
            )
            alternatives.append(staged_alt)

        return alternatives

    def _create_reduced_amount_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create reduced loan amount alternative"""

        # Calculate safe loan amount based on collateral
        collateral_value = profile.collateral_data.get('total_collateral_value', 0)
        safe_ltv = 0.60  # Conservative LTV for approval

        if collateral_value > 0:
            safe_amount = collateral_value * safe_ltv
            reduction_percentage = (application.loan_amount - safe_amount) / application.loan_amount
        else:
            safe_amount = application.loan_amount * 0.5  # 50% reduction
            reduction_percentage = 0.5

        return Alternative(
            alternative_type=AlternativeType.REDUCED_AMOUNT,
            title="Reduced Loan Amount",
            description=f"Approve loan for {safe_amount:,.0f} ALGO ({reduction_percentage*100:.0f}% reduction)",
            new_terms={
                'loan_amount': safe_amount,
                'ltv_ratio': safe_amount / collateral_value if collateral_value > 0 else 0,
                'interest_rate': 0.08,  # Base rate
                'term': application.requested_term
            },
            requirements=[
                "Accept reduced loan amount",
                "Maintain current collateral level",
                "Standard monitoring requirements"
            ],
            timeline="Immediate approval upon acceptance",
            probability_improvement=0.15,  # Expected score improvement
            rationale="Lower loan amount reduces risk and improves loan-to-value ratio"
        )

    def _create_additional_collateral_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create additional collateral alternative"""

        current_collateral = profile.collateral_data.get('total_collateral_value', 0)
        target_ltv = 0.65
        required_collateral = application.loan_amount / target_ltv
        additional_needed = required_collateral - current_collateral

        return Alternative(
            alternative_type=AlternativeType.ADDITIONAL_COLLATERAL,
            title="Additional Collateral Required",
            description=f"Provide additional {additional_needed:,.0f} ALGO worth of collateral",
            new_terms={
                'loan_amount': application.loan_amount,
                'total_collateral_required': required_collateral,
                'ltv_ratio': target_ltv,
                'interest_rate': 0.075,  # Slight discount for better collateral
                'term': application.requested_term
            },
            requirements=[
                f"Deposit additional {additional_needed:,.0f} ALGO equivalent in approved assets",
                "Diversify collateral across at least 3 asset types",
                "Maintain enhanced monitoring agreement"
            ],
            timeline="7-14 days to provide additional collateral",
            probability_improvement=0.20,
            rationale="Stronger collateral position significantly improves risk profile"
        )

    def _create_cosigner_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create co-signer alternative"""

        return Alternative(
            alternative_type=AlternativeType.CO_SIGNER,
            title="Co-signer Required",
            description="Obtain qualified co-signer with strong Algorand ecosystem profile",
            new_terms={
                'loan_amount': application.loan_amount,
                'cosigner_required': True,
                'joint_liability': True,
                'interest_rate': 0.08,
                'term': application.requested_term
            },
            requirements=[
                "Co-signer with ecosystem score > 0.75",
                "Co-signer with governance participation",
                "Joint and several liability agreement",
                "Co-signer financial verification"
            ],
            timeline="30 days to identify and qualify co-signer",
            probability_improvement=0.25,
            rationale="Co-signer with strong profile significantly reduces default risk"
        )

    def _create_shorter_term_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create shorter term alternative"""

        new_term = min(90, application.requested_term // 2)  # Maximum 3 months

        return Alternative(
            alternative_type=AlternativeType.SHORTER_TERM,
            title="Shorter Loan Term",
            description=f"Reduce loan term to {new_term} days for approval",
            new_terms={
                'loan_amount': application.loan_amount,
                'term': new_term,
                'interest_rate': 0.09,  # Slight premium for shorter term risk
                'payment_frequency': 'weekly'
            },
            requirements=[
                f"Accept {new_term}-day loan term",
                "Weekly payment schedule",
                "Accelerated monitoring requirements"
            ],
            timeline="Immediate approval upon acceptance",
            probability_improvement=0.12,
            rationale="Shorter term reduces exposure time and default risk"
        )

    def _create_higher_interest_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create higher interest rate alternative"""

        base_rate = 0.08
        risk_premium = 0.06  # 6% additional premium
        new_rate = base_rate + risk_premium

        return Alternative(
            alternative_type=AlternativeType.HIGHER_INTEREST,
            title="Risk-Adjusted Interest Rate",
            description=f"Approve at {new_rate*100:.1f}% interest rate (risk premium applied)",
            new_terms={
                'loan_amount': application.loan_amount,
                'interest_rate': new_rate,
                'term': application.requested_term,
                'risk_premium': risk_premium
            },
            requirements=[
                f"Accept {new_rate*100:.1f}% interest rate",
                "Enhanced monitoring requirements",
                "Quarterly risk assessment reviews"
            ],
            timeline="Immediate approval upon acceptance",
            probability_improvement=0.10,
            rationale="Higher interest rate compensates for elevated risk profile"
        )

    def _create_improvement_plan_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create improvement plan alternative"""

        improvement_areas = []
        timeline_items = []

        if 'ecosystem_participation' in analysis['addressable_issues']:
            improvement_areas.append("Increase Algorand ecosystem participation")
            timeline_items.append("Complete 10+ dApp interactions (90 days)")

        if 'defi_experience' in analysis['addressable_issues']:
            improvement_areas.append("Build DeFi track record")
            timeline_items.append("Maintain DeFi positions for 6 months")

        if 'governance_participation' in analysis['addressable_issues']:
            improvement_areas.append("Join governance program")
            timeline_items.append("Participate in next governance period")

        return Alternative(
            alternative_type=AlternativeType.IMPROVEMENT_PLAN,
            title="Credit Improvement Plan",
            description="Follow structured plan to improve creditworthiness for future approval",
            new_terms={
                'deferred_approval': True,
                'improvement_period': 180,  # 6 months
                'target_score': 0.70,
                'reserved_terms': {
                    'loan_amount': application.loan_amount,
                    'interest_rate': 0.08,
                    'term': application.requested_term
                }
            },
            requirements=timeline_items + [
                "Monthly progress reviews",
                "Maintain current collateral",
                "Complete financial education modules"
            ],
            timeline="6-month improvement program with quarterly reviews",
            probability_improvement=0.30,
            rationale="Structured improvement addresses specific weaknesses in credit profile"
        )

    def _create_staged_approval_alternative(
        self,
        analysis: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Alternative:
        """Create staged approval alternative"""

        stage1_amount = application.loan_amount * 0.4  # 40% initial
        stage2_amount = application.loan_amount * 0.6  # 60% after performance

        return Alternative(
            alternative_type=AlternativeType.STAGED_APPROVAL,
            title="Staged Approval Process",
            description=f"Initial approval for {stage1_amount:,.0f} ALGO with option for additional {stage2_amount:,.0f} ALGO",
            new_terms={
                'stage1_amount': stage1_amount,
                'stage2_amount': stage2_amount,
                'stage1_term': 90,  # 3 months initial
                'stage2_qualification_period': 60,  # 2 months performance
                'interest_rate': 0.085,
                'performance_metrics': ['on_time_payments', 'collateral_maintenance', 'ecosystem_activity']
            },
            requirements=[
                "Accept staged approval process",
                "Perfect payment history for stage 1",
                "Maintain or improve ecosystem scores",
                "Meet stage 2 qualification metrics"
            ],
            timeline="Immediate stage 1 approval, stage 2 review in 60 days",
            probability_improvement=0.18,
            rationale="Proves borrower reliability with smaller initial exposure"
        )

    def _rank_alternatives(
        self,
        alternatives: List[Alternative],
        rejection_analysis: Dict[str, Any]
    ) -> List[Alternative]:
        """
        Rank alternatives by effectiveness and feasibility.
        """

        def calculate_alternative_score(alt: Alternative) -> float:
            """Calculate ranking score for alternative"""
            score = 0.0

            # Base score from probability improvement
            score += alt.probability_improvement * 100

            # Bonus for addressing primary weaknesses
            if alt.alternative_type in [AlternativeType.ADDITIONAL_COLLATERAL, AlternativeType.REDUCED_AMOUNT]:
                if 'collateral_quality' in rejection_analysis['addressable_issues']:
                    score += 20

            if alt.alternative_type == AlternativeType.IMPROVEMENT_PLAN:
                if 'ecosystem_participation' in rejection_analysis['addressable_issues']:
                    score += 15

            # Penalty for complex requirements
            requirement_count = len(alt.requirements)
            if requirement_count > 4:
                score -= 5

            # Bonus for quick implementation
            if 'immediate' in alt.timeline.lower():
                score += 10

            return score

        # Calculate scores and sort
        scored_alternatives = [(alt, calculate_alternative_score(alt)) for alt in alternatives]
        scored_alternatives.sort(key=lambda x: x[1], reverse=True)

        return [alt for alt, score in scored_alternatives]

    def get_alternatives_summary(self, alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of proposed alternatives"""

        if not alternatives:
            return {
                'total_alternatives': 0,
                'recommendation': 'Focus on building stronger Algorand ecosystem profile before reapplying'
            }

        # Categorize alternatives
        immediate_options = [alt for alt in alternatives if 'immediate' in alt['timeline'].lower()]
        improvement_options = [alt for alt in alternatives if alt['type'] == 'improvement_plan']
        staged_options = [alt for alt in alternatives if alt['type'] == 'staged_approval']

        # Find best option by probability improvement
        best_option = max(alternatives, key=lambda x: x['probability_improvement'])

        return {
            'total_alternatives': len(alternatives),
            'immediate_options': len(immediate_options),
            'improvement_programs': len(improvement_options),
            'staged_programs': len(staged_options),
            'best_option': {
                'type': best_option['type'],
                'title': best_option['title'],
                'improvement_probability': best_option['probability_improvement']
            },
            'recommendation': f"Consider {best_option['title']} for best approval chances"
        }