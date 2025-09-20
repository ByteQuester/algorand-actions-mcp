"""
Consolidated Loan Approval Engine

Combines all loan approval functionality into a single, working module.
Includes ecosystem analysis, borrower assessment, risk evaluation, and decision logic.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

import httpx

from .models import (
    LoanRequest, LoanDecision, LoanTerms, DecisionType, DecisionConfidence,
    AlgorandAddress, RiskLevel
)
from .config import LoanApprovalConfig, DEFAULT_LOAN_APPROVAL_CONFIG

logger = logging.getLogger(__name__)


class LoanApprovalEngine:
    """
    Unified loan approval engine for Algorand lending.

    Provides comprehensive loan approval decisions including:
    - Borrower ecosystem analysis
    - DeFi behavior assessment
    - Risk-based loan terms generation
    - Alternative proposal generation
    """

    def __init__(self, config: Optional[LoanApprovalConfig] = None):
        """Initialize the loan approval engine with configuration."""
        self.config = config or DEFAULT_LOAN_APPROVAL_CONFIG
        self._decision_cache: Dict[str, tuple] = {}
        self._borrower_cache: Dict[str, tuple] = {}

    async def evaluate_loan_application(self, request: LoanRequest) -> LoanDecision:
        """
        Evaluate a loan application and make approval decision.

        Args:
            request: Complete loan application request

        Returns:
            Comprehensive loan decision with terms and rationale
        """
        start_time = time.time()

        try:
            logger.info(
                f"Evaluating loan application {request.application_id} "
                f"for {request.borrower_address.address}"
            )

            # Validate the loan request
            validation_issues = self._validate_request(request)
            if validation_issues:
                return self._create_validation_error_decision(request, validation_issues)

            # Check cache for recent decision
            cache_key = self._generate_cache_key(request)
            cached_decision = self._get_cached_decision(cache_key)
            if cached_decision:
                logger.info(f"Returning cached decision for {request.application_id}")
                return cached_decision

            # Build comprehensive borrower profile
            borrower_profile = await self._build_borrower_profile(request.borrower_address)

            # Calculate risk scores
            risk_scores = await self._calculate_risk_scores(borrower_profile, request)

            # Make approval decision
            decision_result = await self._make_approval_decision(risk_scores, borrower_profile, request)

            # Generate loan terms if approved
            loan_terms = None
            if decision_result['decision'] in [DecisionType.APPROVED, DecisionType.CONDITIONALLY_APPROVED]:
                loan_terms = await self._generate_loan_terms(risk_scores, borrower_profile, request)

            # Generate alternatives if rejected
            alternatives = []
            if decision_result['decision'] == DecisionType.REJECTED:
                alternatives = await self._generate_alternatives(risk_scores, borrower_profile, request)

            # Calculate processing time
            processing_time = Decimal(str(time.time() - start_time))

            # Create final decision
            decision = LoanDecision(
                application_id=request.application_id,
                borrower_address=request.borrower_address,
                decision=decision_result['decision'],
                confidence=decision_result['confidence'],
                overall_score=risk_scores['overall_score'],
                primary_factors=decision_result['primary_factors'],
                risk_factors=decision_result['risk_factors'],
                positive_factors=decision_result['positive_factors'],
                loan_terms=loan_terms,
                alternatives=alternatives,
                expires_at=datetime.utcnow() + timedelta(days=7),
                processing_time_seconds=processing_time
            )

            # Cache the decision
            self._cache_decision(cache_key, decision)

            logger.info(
                f"Loan evaluation completed for {request.application_id}: "
                f"{decision.decision.value} with {decision.confidence.value} confidence"
            )

            return decision

        except Exception as e:
            logger.error(f"Error evaluating loan application {request.application_id}: {e}")
            processing_time = Decimal(str(time.time() - start_time))

            # Return error decision
            return LoanDecision(
                application_id=request.application_id,
                borrower_address=request.borrower_address,
                decision=DecisionType.NEEDS_REVIEW,
                confidence=DecisionConfidence.VERY_LOW,
                overall_score=Decimal('0.0'),
                primary_factors=[f"Processing error: {str(e)}"],
                risk_factors=["System error"],
                positive_factors=[],
                processing_time_seconds=processing_time
            )

    async def _build_borrower_profile(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Build comprehensive borrower profile from multiple data sources."""
        logger.debug(f"Building borrower profile for {address.address}")

        # Check cache for recent profile
        cache_key = f"borrower_{address.address}"
        cached_profile = self._get_cached_borrower_profile(cache_key)
        if cached_profile:
            return cached_profile

        try:
            # Execute analyses in parallel
            account_analysis_task = self._analyze_account_activity(address)
            ecosystem_analysis_task = self._analyze_ecosystem_participation(address)
            defi_analysis_task = self._analyze_defi_behavior(address)
            governance_analysis_task = self._analyze_governance_participation(address)

            # Gather results
            account_analysis, ecosystem_analysis, defi_analysis, governance_analysis = await asyncio.gather(
                account_analysis_task, ecosystem_analysis_task, defi_analysis_task, governance_analysis_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(account_analysis, Exception):
                logger.warning(f"Account analysis failed: {account_analysis}")
                account_analysis = self._get_default_account_analysis()

            if isinstance(ecosystem_analysis, Exception):
                logger.warning(f"Ecosystem analysis failed: {ecosystem_analysis}")
                ecosystem_analysis = self._get_default_ecosystem_analysis()

            if isinstance(defi_analysis, Exception):
                logger.warning(f"DeFi analysis failed: {defi_analysis}")
                defi_analysis = self._get_default_defi_analysis()

            if isinstance(governance_analysis, Exception):
                logger.warning(f"Governance analysis failed: {governance_analysis}")
                governance_analysis = self._get_default_governance_analysis()

            # Combine into comprehensive profile
            profile = {
                'address': address,
                'account_analysis': account_analysis,
                'ecosystem_analysis': ecosystem_analysis,
                'defi_analysis': defi_analysis,
                'governance_analysis': governance_analysis,
                'profile_completeness': self._calculate_profile_completeness(
                    account_analysis, ecosystem_analysis, defi_analysis, governance_analysis
                ),
                'last_updated': datetime.utcnow()
            }

            # Cache the profile
            self._cache_borrower_profile(cache_key, profile)

            return profile

        except Exception as e:
            logger.error(f"Error building borrower profile: {e}")
            return self._get_minimal_borrower_profile(address)

    async def _analyze_account_activity(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze basic account activity and history."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get account information
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()

                    # Calculate account metrics
                    balance = Decimal(str(account_data.get('amount', 0))) / Decimal('1000000')  # Convert microalgos
                    assets_count = len(account_data.get('assets', []))
                    apps_opted_in = account_data.get('total-apps-opted-in', 0)
                    created_round = account_data.get('created-at-round', 0)

                    # Estimate account age (simplified calculation)
                    estimated_age_days = max(1, (datetime.utcnow() - datetime(2021, 1, 1)).days)

                    # Calculate activity score
                    balance_score = min(balance / Decimal('10000'), Decimal('1'))  # Up to 10k ALGO
                    assets_score = min(Decimal(str(assets_count)) / Decimal('10'), Decimal('1'))  # Up to 10 assets
                    apps_score = min(Decimal(str(apps_opted_in)) / Decimal('5'), Decimal('1'))  # Up to 5 apps
                    age_score = min(Decimal(str(estimated_age_days)) / Decimal('365'), Decimal('1'))  # Up to 1 year

                    activity_score = (balance_score + assets_score + apps_score + age_score) / 4

                    return {
                        'balance_algo': balance,
                        'assets_count': assets_count,
                        'apps_opted_in': apps_opted_in,
                        'estimated_age_days': estimated_age_days,
                        'activity_score': activity_score,
                        'balance_score': balance_score,
                        'assets_score': assets_score,
                        'apps_score': apps_score,
                        'age_score': age_score,
                        'data_quality': Decimal('0.8'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze account activity: {e}")

        return self._get_default_account_analysis()

    async def _analyze_ecosystem_participation(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze participation in the Algorand ecosystem."""
        try:
            # This would integrate with ecosystem analytics
            # For now, return reasonable estimates based on account data

            # Get transaction count (simplified)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}/transactions?limit=1000"
                )

                if response.status_code == 200:
                    tx_data = response.json()
                    tx_count = len(tx_data.get('transactions', []))

                    # Calculate ecosystem participation scores
                    transaction_diversity = min(Decimal(str(tx_count)) / Decimal('100'), Decimal('1'))
                    ecosystem_engagement = min(transaction_diversity * Decimal('1.2'), Decimal('1'))

                    # Estimate ecosystem tenure
                    ecosystem_tenure_score = min(transaction_diversity, Decimal('1'))

                    # Calculate overall ecosystem score
                    ecosystem_score = (transaction_diversity + ecosystem_engagement + ecosystem_tenure_score) / 3

                    return {
                        'transaction_count': tx_count,
                        'transaction_diversity': transaction_diversity,
                        'ecosystem_engagement': ecosystem_engagement,
                        'ecosystem_tenure_score': ecosystem_tenure_score,
                        'ecosystem_score': ecosystem_score,
                        'data_quality': Decimal('0.7'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze ecosystem participation: {e}")

        return self._get_default_ecosystem_analysis()

    async def _analyze_defi_behavior(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze DeFi protocol usage and behavior patterns."""
        try:
            # This would integrate with DeFi protocol analytics
            # For now, return conservative estimates

            # Estimate DeFi participation based on app interactions
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()
                    apps_opted_in = account_data.get('total-apps-opted-in', 0)

                    # Simple DeFi scoring based on app interactions
                    defi_participation = min(Decimal(str(apps_opted_in)) / Decimal('3'), Decimal('1'))
                    risk_management_score = defi_participation * Decimal('0.8')  # Conservative estimate
                    sophistication_score = defi_participation * Decimal('0.9')

                    # Overall DeFi score
                    defi_score = (defi_participation + risk_management_score + sophistication_score) / 3

                    return {
                        'apps_interacted': apps_opted_in,
                        'defi_participation': defi_participation,
                        'risk_management_score': risk_management_score,
                        'sophistication_score': sophistication_score,
                        'defi_score': defi_score,
                        'data_quality': Decimal('0.6'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze DeFi behavior: {e}")

        return self._get_default_defi_analysis()

    async def _analyze_governance_participation(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze governance participation and reputation."""
        try:
            # This would check governance voting records
            # For now, return moderate estimates

            # Check if address holds ALGO (potential governance participant)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()
                    balance = Decimal(str(account_data.get('amount', 0))) / Decimal('1000000')

                    # Estimate governance participation based on balance
                    if balance >= Decimal('1000'):  # 1000+ ALGO
                        participation_likelihood = Decimal('0.8')
                    elif balance >= Decimal('100'):  # 100+ ALGO
                        participation_likelihood = Decimal('0.6')
                    elif balance >= Decimal('10'):   # 10+ ALGO
                        participation_likelihood = Decimal('0.4')
                    else:
                        participation_likelihood = Decimal('0.2')

                    governance_score = participation_likelihood * Decimal('0.9')  # Conservative

                    return {
                        'algo_balance': balance,
                        'participation_likelihood': participation_likelihood,
                        'governance_score': governance_score,
                        'estimated_participation': balance >= Decimal('100'),
                        'data_quality': Decimal('0.5'),  # Low since this is estimated
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze governance participation: {e}")

        return self._get_default_governance_analysis()

    async def _calculate_risk_scores(
        self,
        profile: Dict[str, Any],
        request: LoanRequest
    ) -> Dict[str, Decimal]:
        """Calculate comprehensive risk scores from borrower profile."""

        # Extract component scores
        account_score = profile['account_analysis'].get('activity_score', Decimal('0.5'))
        ecosystem_score = profile['ecosystem_analysis'].get('ecosystem_score', Decimal('0.5'))
        defi_score = profile['defi_analysis'].get('defi_score', Decimal('0.5'))
        governance_score = profile['governance_analysis'].get('governance_score', Decimal('0.5'))

        # Calculate loan-specific risk factors
        loan_amount_score = self._calculate_loan_amount_score(request.loan_amount)
        loan_duration_score = self._calculate_loan_duration_score(request.requested_term_days)
        collateral_score = self._calculate_collateral_score(request)

        # Apply weights to calculate overall score
        weights = {
            'account': Decimal('0.25'),
            'ecosystem': Decimal('0.25'),
            'defi': Decimal('0.15'),
            'governance': Decimal('0.1'),
            'loan_amount': Decimal('0.1'),
            'loan_duration': Decimal('0.05'),
            'collateral': Decimal('0.1')
        }

        overall_score = (
            account_score * weights['account'] +
            ecosystem_score * weights['ecosystem'] +
            defi_score * weights['defi'] +
            governance_score * weights['governance'] +
            loan_amount_score * weights['loan_amount'] +
            loan_duration_score * weights['loan_duration'] +
            collateral_score * weights['collateral']
        )

        return {
            'overall_score': overall_score,
            'account_score': account_score,
            'ecosystem_score': ecosystem_score,
            'defi_score': defi_score,
            'governance_score': governance_score,
            'loan_amount_score': loan_amount_score,
            'loan_duration_score': loan_duration_score,
            'collateral_score': collateral_score
        }

    def _calculate_loan_amount_score(self, loan_amount: Decimal) -> Decimal:
        """Calculate score based on loan amount (lower amounts = lower risk)."""
        if loan_amount <= self.config.min_loan_amount_usd:
            return Decimal('0.9')
        elif loan_amount <= self.config.min_loan_amount_usd * 10:
            return Decimal('0.7')
        elif loan_amount <= self.config.min_loan_amount_usd * 100:
            return Decimal('0.5')
        elif loan_amount <= self.config.max_loan_amount_usd:
            return Decimal('0.3')
        else:
            return Decimal('0.1')  # Above maximum

    def _calculate_loan_duration_score(self, duration_days: int) -> Decimal:
        """Calculate score based on loan duration (shorter terms = lower risk)."""
        if duration_days <= 30:
            return Decimal('0.9')
        elif duration_days <= 90:
            return Decimal('0.8')
        elif duration_days <= 180:
            return Decimal('0.7')
        elif duration_days <= 365:
            return Decimal('0.6')
        elif duration_days <= self.config.max_loan_term_days:
            return Decimal('0.4')
        else:
            return Decimal('0.2')  # Above maximum

    def _calculate_collateral_score(self, request: LoanRequest) -> Decimal:
        """Calculate score based on collateral assets provided."""
        if not request.collateral_assets:
            return Decimal('0.2')  # No collateral

        # Simple scoring based on collateral asset count
        collateral_count = len(request.collateral_assets)

        if collateral_count >= 3:
            return Decimal('0.9')  # Well diversified
        elif collateral_count == 2:
            return Decimal('0.7')  # Moderately diversified
        else:
            return Decimal('0.5')  # Single asset

    async def _make_approval_decision(
        self,
        scores: Dict[str, Decimal],
        profile: Dict[str, Any],
        request: LoanRequest
    ) -> Dict[str, Any]:
        """Make the final approval decision based on risk scores."""

        overall_score = scores['overall_score']

        # Determine decision based on score and thresholds
        if overall_score >= self.config.min_approval_score:
            if overall_score >= Decimal('0.8'):
                decision = DecisionType.APPROVED
            elif overall_score >= Decimal('0.7'):
                decision = DecisionType.APPROVED
            else:
                decision = DecisionType.CONDITIONALLY_APPROVED
        elif overall_score >= Decimal('0.4'):
            decision = DecisionType.NEEDS_REVIEW
        else:
            decision = DecisionType.REJECTED

        # Determine confidence based on data quality
        confidence = self._determine_confidence(profile, scores)

        # Generate decision factors
        primary_factors = self._generate_primary_factors(scores, profile)
        risk_factors = self._generate_risk_factors(scores, profile)
        positive_factors = self._generate_positive_factors(scores, profile)

        return {
            'decision': decision,
            'confidence': confidence,
            'primary_factors': primary_factors,
            'risk_factors': risk_factors,
            'positive_factors': positive_factors
        }

    def _determine_confidence(self, profile: Dict[str, Any], scores: Dict[str, Decimal]) -> DecisionConfidence:
        """Determine decision confidence level based on data quality and score."""

        # Calculate average data quality
        data_qualities = [
            profile['account_analysis'].get('data_quality', Decimal('0.5')),
            profile['ecosystem_analysis'].get('data_quality', Decimal('0.5')),
            profile['defi_analysis'].get('data_quality', Decimal('0.5')),
            profile['governance_analysis'].get('data_quality', Decimal('0.5'))
        ]
        avg_data_quality = sum(data_qualities) / len(data_qualities)

        # Adjust confidence based on profile completeness
        profile_completeness = profile.get('profile_completeness', Decimal('0.5'))

        # Calculate overall confidence score
        confidence_score = (avg_data_quality + profile_completeness) / 2

        # Convert to confidence level
        if confidence_score >= Decimal('0.9') and scores['overall_score'] >= Decimal('0.8'):
            return DecisionConfidence.VERY_HIGH
        elif confidence_score >= Decimal('0.8'):
            return DecisionConfidence.HIGH
        elif confidence_score >= Decimal('0.6'):
            return DecisionConfidence.MEDIUM
        elif confidence_score >= Decimal('0.4'):
            return DecisionConfidence.LOW
        else:
            return DecisionConfidence.VERY_LOW

    def _generate_primary_factors(self, scores: Dict[str, Decimal], profile: Dict[str, Any]) -> List[str]:
        """Generate primary decision factors."""
        factors = []

        # Account-based factors
        if scores['account_score'] >= Decimal('0.8'):
            factors.append("Strong account activity and asset diversity")
        elif scores['account_score'] >= Decimal('0.6'):
            factors.append("Good account fundamentals")

        # Ecosystem factors
        if scores['ecosystem_score'] >= Decimal('0.8'):
            factors.append("Excellent ecosystem participation")
        elif scores['ecosystem_score'] >= Decimal('0.6'):
            factors.append("Good ecosystem engagement")

        # DeFi factors
        if scores['defi_score'] >= Decimal('0.7'):
            factors.append("Sophisticated DeFi behavior")

        # Governance factors
        if scores['governance_score'] >= Decimal('0.7'):
            factors.append("Active governance participation")

        # Loan structure factors
        if scores['collateral_score'] >= Decimal('0.7'):
            factors.append("Well-structured collateral portfolio")

        if not factors:
            factors.append("Standard risk assessment completed")

        return factors

    def _generate_risk_factors(self, scores: Dict[str, Decimal], profile: Dict[str, Any]) -> List[str]:
        """Generate risk factors that concern the decision."""
        factors = []

        # Low scores
        if scores['overall_score'] < Decimal('0.5'):
            factors.append("Below-average overall risk profile")

        if scores['account_score'] < Decimal('0.4'):
            factors.append("Limited account activity or asset holdings")

        if scores['ecosystem_score'] < Decimal('0.4'):
            factors.append("Minimal ecosystem participation")

        # Loan-specific risks
        if scores['loan_amount_score'] < Decimal('0.5'):
            factors.append("Large loan amount relative to risk profile")

        if scores['loan_duration_score'] < Decimal('0.5'):
            factors.append("Extended loan duration increases risk")

        if scores['collateral_score'] < Decimal('0.5'):
            factors.append("Limited or inadequate collateral")

        # Data quality concerns
        profile_completeness = profile.get('profile_completeness', Decimal('0.5'))
        if profile_completeness < Decimal('0.7'):
            factors.append("Incomplete borrower data limits assessment accuracy")

        return factors

    def _generate_positive_factors(self, scores: Dict[str, Decimal], profile: Dict[str, Any]) -> List[str]:
        """Generate positive factors supporting the decision."""
        factors = []

        # Strong performance areas
        if scores['account_score'] >= Decimal('0.8'):
            factors.append("Mature account with significant on-chain activity")

        if scores['ecosystem_score'] >= Decimal('0.8'):
            factors.append("Deep engagement with Algorand ecosystem")

        if scores['defi_score'] >= Decimal('0.7'):
            factors.append("Demonstrated DeFi protocol expertise")

        if scores['governance_score'] >= Decimal('0.7'):
            factors.append("Commitment to network governance")

        # Account specifics
        account_analysis = profile['account_analysis']
        if account_analysis.get('balance_algo', Decimal('0')) >= Decimal('1000'):
            factors.append("Substantial ALGO holdings demonstrate commitment")

        if account_analysis.get('assets_count', 0) >= 5:
            factors.append("Diversified asset portfolio")

        if account_analysis.get('estimated_age_days', 0) >= 365:
            factors.append("Long-established account history")

        # Loan structure
        if scores['collateral_score'] >= Decimal('0.8'):
            factors.append("Strong collateral diversification")

        if scores['loan_duration_score'] >= Decimal('0.7'):
            factors.append("Conservative loan duration")

        return factors

    async def _generate_loan_terms(
        self,
        scores: Dict[str, Decimal],
        profile: Dict[str, Any],
        request: LoanRequest
    ) -> LoanTerms:
        """Generate loan terms based on risk assessment."""

        # Base terms
        base_interest_rate = Decimal('0.08')  # 8% base rate
        base_ltv = Decimal('0.7')  # 70% LTV

        # Calculate interest rate adjustments
        risk_adjustment = self._calculate_interest_rate_adjustment(scores['overall_score'])
        final_interest_rate = base_interest_rate + risk_adjustment

        # Calculate LTV adjustment
        ltv_adjustment = self._calculate_ltv_adjustment(scores['overall_score'])
        final_ltv = min(Decimal('0.8'), max(Decimal('0.5'), base_ltv + ltv_adjustment))

        # Determine approved amount (may be less than requested)
        max_approved_ratio = min(Decimal('1'), scores['overall_score'] + Decimal('0.2'))
        approved_amount = request.loan_amount * max_approved_ratio

        # Cap approved amount by configured limits
        approved_amount = min(approved_amount, self.config.max_loan_amount_usd)
        approved_amount = max(approved_amount, self.config.min_loan_amount_usd)

        # Determine loan term (may be shorter than requested)
        max_term_ratio = min(Decimal('1'), scores['overall_score'] + Decimal('0.3'))
        approved_term = min(
            request.requested_term_days,
            int(self.config.max_loan_term_days * max_term_ratio)
        )
        approved_term = max(approved_term, self.config.min_loan_term_days)

        # Generate conditions and monitoring requirements
        conditions = self._generate_loan_conditions(scores, profile)
        monitoring_requirements = self._generate_monitoring_requirements(scores, profile)

        return LoanTerms(
            approved_amount=approved_amount,
            interest_rate=final_interest_rate,
            loan_term_days=approved_term,
            ltv_ratio=final_ltv,
            conditions=conditions,
            monitoring_requirements=monitoring_requirements
        )

    def _calculate_interest_rate_adjustment(self, overall_score: Decimal) -> Decimal:
        """Calculate interest rate adjustment based on risk score."""
        if overall_score >= Decimal('0.9'):
            return Decimal('-0.01')  # -1% for excellent borrowers
        elif overall_score >= Decimal('0.8'):
            return Decimal('0')      # No adjustment for good borrowers
        elif overall_score >= Decimal('0.7'):
            return Decimal('0.005')  # +0.5% for fair borrowers
        elif overall_score >= Decimal('0.6'):
            return Decimal('0.01')   # +1% for marginal borrowers
        else:
            return Decimal('0.02')   # +2% for conditional approvals

    def _calculate_ltv_adjustment(self, overall_score: Decimal) -> Decimal:
        """Calculate LTV ratio adjustment based on risk score."""
        if overall_score >= Decimal('0.9'):
            return Decimal('0.1')    # Up to 80% LTV for excellent borrowers
        elif overall_score >= Decimal('0.8'):
            return Decimal('0.05')   # Up to 75% LTV for good borrowers
        elif overall_score >= Decimal('0.7'):
            return Decimal('0')      # 70% LTV for fair borrowers
        elif overall_score >= Decimal('0.6'):
            return Decimal('-0.1')   # 60% LTV for marginal borrowers
        else:
            return Decimal('-0.2')   # 50% LTV for conditional approvals

    def _generate_loan_conditions(self, scores: Dict[str, Decimal], profile: Dict[str, Any]) -> List[str]:
        """Generate specific loan conditions."""
        conditions = []

        if scores['overall_score'] < Decimal('0.7'):
            conditions.append("Enhanced monitoring of collateral ratios required")

        if scores['collateral_score'] < Decimal('0.6'):
            conditions.append("Additional collateral may be required if ratios fall below threshold")

        if scores['defi_score'] < Decimal('0.5'):
            conditions.append("Restriction on additional DeFi protocol interactions during loan term")

        if profile.get('profile_completeness', Decimal('0.5')) < Decimal('0.7'):
            conditions.append("Borrower must provide additional documentation for verification")

        return conditions

    def _generate_monitoring_requirements(self, scores: Dict[str, Decimal], profile: Dict[str, Any]) -> List[str]:
        """Generate monitoring requirements for the loan."""
        requirements = []

        if scores['overall_score'] < Decimal('0.8'):
            requirements.append("Weekly collateral ratio monitoring")

        if scores['overall_score'] < Decimal('0.6'):
            requirements.append("Daily account activity monitoring")

        if scores['defi_score'] < Decimal('0.6'):
            requirements.append("Monthly DeFi position review")

        if scores['loan_amount_score'] < Decimal('0.6'):
            requirements.append("Enhanced risk monitoring due to loan size")

        return requirements

    async def _generate_alternatives(
        self,
        scores: Dict[str, Decimal],
        profile: Dict[str, Any],
        request: LoanRequest
    ) -> List[Dict[str, Any]]:
        """Generate alternative proposals for rejected applications."""
        alternatives = []

        overall_score = scores['overall_score']

        # Reduced amount alternative
        if overall_score >= Decimal('0.3'):
            reduced_amount = request.loan_amount * Decimal('0.5')
            if reduced_amount >= self.config.min_loan_amount_usd:
                alternatives.append({
                    'type': 'reduced_amount',
                    'description': f'Reduced loan amount to ${reduced_amount:,.2f}',
                    'modified_amount': reduced_amount,
                    'rationale': 'Lower amount reduces risk exposure and may be approvable'
                })

        # Shorter term alternative
        if overall_score >= Decimal('0.4'):
            shorter_term = min(request.requested_term_days // 2, 90)  # Max 90 days
            if shorter_term >= self.config.min_loan_term_days:
                alternatives.append({
                    'type': 'shorter_term',
                    'description': f'Reduced loan term to {shorter_term} days',
                    'modified_term_days': shorter_term,
                    'rationale': 'Shorter duration reduces long-term risk exposure'
                })

        # Increased collateral alternative
        if scores['collateral_score'] < Decimal('0.6') and overall_score >= Decimal('0.4'):
            alternatives.append({
                'type': 'increased_collateral',
                'description': 'Provide additional collateral for improved terms',
                'required_ltv': Decimal('0.5'),  # 50% LTV instead of standard
                'rationale': 'Additional collateral significantly reduces lender risk'
            })

        # Wait and reapply alternative
        if overall_score >= Decimal('0.2'):
            alternatives.append({
                'type': 'wait_and_reapply',
                'description': 'Increase ecosystem participation and reapply in 30-90 days',
                'waiting_period_days': 60,
                'rationale': 'Building stronger on-chain history will improve approval chances'
            })

        return alternatives

    # Validation and utility methods
    def _validate_request(self, request: LoanRequest) -> List[str]:
        """Validate loan request for basic requirements."""
        issues = []

        if request.loan_amount <= 0:
            issues.append("Loan amount must be positive")

        if request.loan_amount < self.config.min_loan_amount_usd:
            issues.append(f"Loan amount below minimum of ${self.config.min_loan_amount_usd:,.2f}")

        if request.loan_amount > self.config.max_loan_amount_usd:
            issues.append(f"Loan amount exceeds maximum of ${self.config.max_loan_amount_usd:,.2f}")

        if request.requested_term_days <= 0:
            issues.append("Loan term must be positive")

        if request.requested_term_days < self.config.min_loan_term_days:
            issues.append(f"Loan term below minimum of {self.config.min_loan_term_days} days")

        if request.requested_term_days > self.config.max_loan_term_days:
            issues.append(f"Loan term exceeds maximum of {self.config.max_loan_term_days} days")

        if not request.purpose.strip():
            issues.append("Loan purpose is required")

        if not request.borrower_address.is_valid():
            issues.append("Invalid borrower address")

        return issues

    def _create_validation_error_decision(
        self,
        request: LoanRequest,
        issues: List[str]
    ) -> LoanDecision:
        """Create decision for validation errors."""
        return LoanDecision(
            application_id=request.application_id,
            borrower_address=request.borrower_address,
            decision=DecisionType.NEEDS_REVIEW,
            confidence=DecisionConfidence.VERY_LOW,
            overall_score=Decimal('0.0'),
            primary_factors=["Validation errors prevent processing"],
            risk_factors=issues,
            positive_factors=[]
        )

    # Cache management methods
    def _generate_cache_key(self, request: LoanRequest) -> str:
        """Generate cache key for loan decision."""
        return f"decision_{request.borrower_address.address}_{request.loan_amount}_{request.requested_term_days}"

    def _get_cached_decision(self, cache_key: str) -> Optional[LoanDecision]:
        """Get cached decision if still valid."""
        if cache_key in self._decision_cache:
            decision, timestamp = self._decision_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self.config.decision_cache_ttl:
                return decision
        return None

    def _cache_decision(self, cache_key: str, decision: LoanDecision) -> None:
        """Cache loan decision."""
        self._decision_cache[cache_key] = (decision, datetime.utcnow())

    def _get_cached_borrower_profile(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached borrower profile if still valid."""
        if cache_key in self._borrower_cache:
            profile, timestamp = self._borrower_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < 1800:  # 30 minutes
                return profile
        return None

    def _cache_borrower_profile(self, cache_key: str, profile: Dict[str, Any]) -> None:
        """Cache borrower profile."""
        self._borrower_cache[cache_key] = (profile, datetime.utcnow())

    def _calculate_profile_completeness(self, *analyses) -> Decimal:
        """Calculate overall profile completeness score."""
        quality_scores = []
        for analysis in analyses:
            if isinstance(analysis, dict):
                quality_scores.append(analysis.get('data_quality', Decimal('0.5')))
            else:
                quality_scores.append(Decimal('0.5'))

        return sum(quality_scores) / len(quality_scores) if quality_scores else Decimal('0.5')

    # Default analysis methods
    def _get_default_account_analysis(self) -> Dict[str, Any]:
        """Get default account analysis when data unavailable."""
        return {
            'balance_algo': Decimal('0'),
            'assets_count': 0,
            'apps_opted_in': 0,
            'estimated_age_days': 1,
            'activity_score': Decimal('0.3'),
            'balance_score': Decimal('0.1'),
            'assets_score': Decimal('0.1'),
            'apps_score': Decimal('0.1'),
            'age_score': Decimal('0.1'),
            'data_quality': Decimal('0.2'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_ecosystem_analysis(self) -> Dict[str, Any]:
        """Get default ecosystem analysis."""
        return {
            'transaction_count': 0,
            'transaction_diversity': Decimal('0.3'),
            'ecosystem_engagement': Decimal('0.3'),
            'ecosystem_tenure_score': Decimal('0.3'),
            'ecosystem_score': Decimal('0.3'),
            'data_quality': Decimal('0.2'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_defi_analysis(self) -> Dict[str, Any]:
        """Get default DeFi analysis."""
        return {
            'apps_interacted': 0,
            'defi_participation': Decimal('0.2'),
            'risk_management_score': Decimal('0.3'),
            'sophistication_score': Decimal('0.2'),
            'defi_score': Decimal('0.25'),
            'data_quality': Decimal('0.2'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_governance_analysis(self) -> Dict[str, Any]:
        """Get default governance analysis."""
        return {
            'algo_balance': Decimal('0'),
            'participation_likelihood': Decimal('0.2'),
            'governance_score': Decimal('0.3'),
            'estimated_participation': False,
            'data_quality': Decimal('0.2'),
            'last_updated': datetime.utcnow()
        }

    def _get_minimal_borrower_profile(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Get minimal borrower profile for error cases."""
        return {
            'address': address,
            'account_analysis': self._get_default_account_analysis(),
            'ecosystem_analysis': self._get_default_ecosystem_analysis(),
            'defi_analysis': self._get_default_defi_analysis(),
            'governance_analysis': self._get_default_governance_analysis(),
            'profile_completeness': Decimal('0.2'),
            'last_updated': datetime.utcnow()
        }

    # Public utility methods
    def get_approval_thresholds(self) -> Dict[str, Decimal]:
        """Get current approval score thresholds."""
        return {
            'minimum_approval': self.config.min_approval_score,
            'confident_approval': Decimal('0.8'),
            'conditional_approval': Decimal('0.6'),
            'review_required': Decimal('0.4')
        }

    def estimate_approval_probability(self, borrower_address: AlgorandAddress) -> Dict[str, Any]:
        """Estimate approval probability for a borrower (quick assessment)."""
        # This would do a lightweight analysis
        return {
            'estimated_probability': Decimal('0.5'),
            'confidence': 'low',
            'recommendation': 'Submit full application for detailed assessment'
        }

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._decision_cache.clear()
        self._borrower_cache.clear()
        logger.info("Loan approval engine cache cleared")