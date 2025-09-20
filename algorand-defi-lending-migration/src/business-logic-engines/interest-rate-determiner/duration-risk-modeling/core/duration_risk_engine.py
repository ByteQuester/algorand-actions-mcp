"""
Duration Risk Modeling Engine

Comprehensive engine for term structure analysis, prepayment risk modeling,
and duration-based risk assessment for cryptocurrency-backed loans.
"""

import asyncio
import logging
import math
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
from scipy import optimize, interpolate
from scipy.stats import norm
import concurrent.futures

from ..config import DurationRiskConfig, DEFAULT_DURATION_CONFIG


@dataclass
class LoanTerms:
    """Loan term specifications."""
    principal_amount: Decimal
    term_days: int
    interest_rate: Decimal
    collateral_type: str
    collateral_amount: Decimal
    ltv_ratio: float
    payment_frequency: str = "monthly"  # monthly, quarterly, annual
    prepayment_allowed: bool = True
    early_termination_penalty: Optional[Decimal] = None


@dataclass
class YieldCurvePoint:
    """Single point on yield curve."""
    term_days: int
    yield_rate: Decimal
    timestamp: datetime
    source: str


@dataclass
class YieldCurve:
    """Complete yield curve representation."""
    curve_points: List[YieldCurvePoint]
    curve_date: datetime
    interpolation_method: str
    base_currency: str = "USD"


@dataclass
class PrepaymentModel:
    """Prepayment probability model results."""
    loan_terms: LoanTerms
    base_prepayment_probability: float
    adjusted_prepayment_probability: float
    expected_prepayment_time: float  # Days
    prepayment_penalty_amount: Decimal
    model_confidence: float
    risk_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class DurationMetrics:
    """Duration and interest rate sensitivity metrics."""
    modified_duration: float
    macaulay_duration: float
    effective_duration: float
    convexity: float
    basis_point_value: Decimal
    yield_sensitivity: float
    duration_bucket: str


@dataclass
class TermStructureAnalysis:
    """Term structure analysis results."""
    loan_terms: LoanTerms
    yield_curve: YieldCurve
    term_spread: Decimal
    duration_metrics: DurationMetrics
    prepayment_model: PrepaymentModel
    risk_adjusted_rate: Decimal
    confidence_interval: Tuple[Decimal, Decimal]


@dataclass
class AssetLiabilityPosition:
    """Asset-liability position for duration matching."""
    position_id: str
    asset_type: str
    notional_amount: Decimal
    duration: float
    yield_rate: Decimal
    maturity_bucket: str
    weight_in_portfolio: float


@dataclass
class DurationRiskAssessment:
    """Complete duration risk assessment."""
    assessment_id: str
    assessment_timestamp: datetime
    loan_terms: LoanTerms
    term_structure_analysis: TermStructureAnalysis
    duration_risk_score: float
    asset_liability_mismatch: float
    stress_test_results: Dict[str, float]
    recommended_adjustments: List[str]
    final_duration_premium: Decimal


class YieldCurveBuilder:
    """Builds and manages yield curves for duration analysis."""

    def __init__(self, config: DurationRiskConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def build_yield_curve(
        self,
        market_rates: Dict[int, Decimal],
        curve_date: Optional[datetime] = None
    ) -> YieldCurve:
        """
        Build yield curve from market rates.

        Args:
            market_rates: Dictionary mapping term (days) to yield rates
            curve_date: Date for the curve (defaults to current time)

        Returns:
            Complete yield curve object
        """
        curve_date = curve_date or datetime.utcnow()

        # Create curve points
        curve_points = []
        for term_days, rate in market_rates.items():
            point = YieldCurvePoint(
                term_days=term_days,
                yield_rate=rate,
                timestamp=curve_date,
                source=self.config.yield_curve_source
            )
            curve_points.append(point)

        # Sort by term
        curve_points.sort(key=lambda x: x.term_days)

        yield_curve = YieldCurve(
            curve_points=curve_points,
            curve_date=curve_date,
            interpolation_method=self.config.term_structure.interpolation_method
        )

        # Interpolate missing points for standard terms
        interpolated_curve = await self._interpolate_curve(yield_curve)

        self.logger.info(f"Built yield curve with {len(interpolated_curve.curve_points)} points")

        return interpolated_curve

    async def _interpolate_curve(self, yield_curve: YieldCurve) -> YieldCurve:
        """Interpolate yield curve for standard terms."""
        existing_terms = [point.term_days for point in yield_curve.curve_points]
        existing_rates = [float(point.yield_rate) for point in yield_curve.curve_points]

        standard_terms = self.config.term_structure.standard_terms
        method = self.config.term_structure.interpolation_method

        # Create interpolation function
        if method == "cubic_spline":
            interp_func = interpolate.CubicSpline(
                existing_terms, existing_rates,
                bc_type='natural'
            )
        elif method == "linear":
            interp_func = interpolate.interp1d(
                existing_terms, existing_rates,
                kind='linear', fill_value='extrapolate'
            )
        else:  # Default to linear
            interp_func = interpolate.interp1d(
                existing_terms, existing_rates,
                kind='linear', fill_value='extrapolate'
            )

        # Generate interpolated points
        interpolated_points = list(yield_curve.curve_points)

        for term in standard_terms:
            if term not in existing_terms:
                interpolated_rate = float(interp_func(term))
                point = YieldCurvePoint(
                    term_days=term,
                    yield_rate=Decimal(str(interpolated_rate)),
                    timestamp=yield_curve.curve_date,
                    source=f"{self.config.yield_curve_source}_interpolated"
                )
                interpolated_points.append(point)

        # Sort and return new curve
        interpolated_points.sort(key=lambda x: x.term_days)

        return YieldCurve(
            curve_points=interpolated_points,
            curve_date=yield_curve.curve_date,
            interpolation_method=yield_curve.interpolation_method
        )

    def get_rate_for_term(self, yield_curve: YieldCurve, term_days: int) -> Decimal:
        """Get interpolated rate for specific term."""
        # Find exact match first
        for point in yield_curve.curve_points:
            if point.term_days == term_days:
                return point.yield_rate

        # Interpolate
        terms = [point.term_days for point in yield_curve.curve_points]
        rates = [float(point.yield_rate) for point in yield_curve.curve_points]

        if term_days < min(terms):
            # Extrapolate short end
            return Decimal(str(rates[0]))
        elif term_days > max(terms):
            # Extrapolate long end
            return Decimal(str(rates[-1]))
        else:
            # Interpolate
            interp_rate = np.interp(term_days, terms, rates)
            return Decimal(str(interp_rate))


class PrepaymentRiskAnalyzer:
    """Analyzes prepayment risk for crypto-backed loans."""

    def __init__(self, config: DurationRiskConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def analyze_prepayment_risk(
        self,
        loan_terms: LoanTerms,
        market_conditions: Dict[str, float],
        borrower_profile: Optional[Dict[str, Any]] = None
    ) -> PrepaymentModel:
        """
        Analyze prepayment risk for given loan terms.

        Args:
            loan_terms: Loan specifications
            market_conditions: Current market conditions
            borrower_profile: Optional borrower risk profile

        Returns:
            Prepayment model with probabilities and timing
        """
        # Get base prepayment probability
        base_probability = self._get_base_prepayment_probability(loan_terms.term_days)

        # Calculate adjustment factors
        ltv_adjustment = self._calculate_ltv_adjustment(loan_terms.ltv_ratio)
        volatility_adjustment = self._calculate_volatility_adjustment(market_conditions)
        rate_adjustment = self._calculate_rate_differential_adjustment(loan_terms, market_conditions)

        # Apply crypto-specific adjustments
        crypto_adjustment = self._calculate_crypto_adjustment(loan_terms.collateral_type, borrower_profile)

        # Calculate adjusted probability
        adjusted_probability = base_probability * ltv_adjustment * volatility_adjustment * rate_adjustment * crypto_adjustment
        adjusted_probability = max(0.01, min(0.95, adjusted_probability))  # Cap between 1% and 95%

        # Calculate expected prepayment timing
        expected_time = self._calculate_expected_prepayment_time(
            loan_terms.term_days, adjusted_probability
        )

        # Calculate prepayment penalty
        penalty_amount = self._calculate_prepayment_penalty(loan_terms, expected_time)

        # Calculate model confidence
        confidence = self._calculate_model_confidence(loan_terms, market_conditions, borrower_profile)

        risk_factors = {
            'ltv_adjustment': ltv_adjustment,
            'volatility_adjustment': volatility_adjustment,
            'rate_adjustment': rate_adjustment,
            'crypto_adjustment': crypto_adjustment
        }

        model = PrepaymentModel(
            loan_terms=loan_terms,
            base_prepayment_probability=base_probability,
            adjusted_prepayment_probability=adjusted_probability,
            expected_prepayment_time=expected_time,
            prepayment_penalty_amount=penalty_amount,
            model_confidence=confidence,
            risk_factors=risk_factors
        )

        self.logger.info(f"Prepayment analysis completed. Probability: {adjusted_probability:.2%}")

        return model

    def _get_base_prepayment_probability(self, term_days: int) -> float:
        """Get base prepayment probability for term."""
        rates = self.config.prepayment_risk.base_prepayment_rates

        # Find exact match or interpolate
        if term_days in rates:
            return rates[term_days]

        # Interpolate between nearest points
        sorted_terms = sorted(rates.keys())

        if term_days <= sorted_terms[0]:
            return rates[sorted_terms[0]]
        elif term_days >= sorted_terms[-1]:
            return rates[sorted_terms[-1]]

        # Linear interpolation
        for i in range(len(sorted_terms) - 1):
            if sorted_terms[i] <= term_days <= sorted_terms[i + 1]:
                lower_term, upper_term = sorted_terms[i], sorted_terms[i + 1]
                lower_rate, upper_rate = rates[lower_term], rates[upper_term]

                ratio = (term_days - lower_term) / (upper_term - lower_term)
                return lower_rate + ratio * (upper_rate - lower_rate)

        return 0.3  # Default

    def _calculate_ltv_adjustment(self, ltv_ratio: float) -> float:
        """Calculate LTV-based adjustment factor."""
        factor = self.config.prepayment_risk.ltv_prepayment_factor

        if ltv_ratio > 0.8:
            return factor * 1.2  # High LTV increases prepayment risk
        elif ltv_ratio > 0.6:
            return factor
        else:
            return factor * 0.8  # Low LTV reduces prepayment risk

    def _calculate_volatility_adjustment(self, market_conditions: Dict[str, float]) -> float:
        """Calculate volatility-based adjustment factor."""
        volatility = market_conditions.get('volatility', 0.3)
        factor = self.config.prepayment_risk.volatility_prepayment_factor

        if volatility > 0.5:
            return factor * 1.3  # High volatility increases prepayment
        elif volatility > 0.3:
            return factor
        else:
            return factor * 0.8  # Low volatility reduces prepayment

    def _calculate_rate_differential_adjustment(
        self,
        loan_terms: LoanTerms,
        market_conditions: Dict[str, float]
    ) -> float:
        """Calculate rate differential adjustment."""
        current_market_rate = market_conditions.get('risk_free_rate', 0.05)
        loan_rate = float(loan_terms.interest_rate)
        rate_spread = loan_rate - current_market_rate

        factor = self.config.prepayment_risk.rate_differential_factor

        if rate_spread > 0.02:  # Loan rate 2%+ above market
            return factor * 1.4  # High incentive to prepay
        elif rate_spread > 0.005:  # Loan rate 0.5%+ above market
            return factor * 1.1
        elif rate_spread < -0.01:  # Loan rate below market
            return factor * 0.6  # Low incentive to prepay
        else:
            return factor

    def _calculate_crypto_adjustment(
        self,
        collateral_type: str,
        borrower_profile: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate crypto-specific adjustment factors."""
        adjustment = 1.0

        # Collateral type adjustments
        if collateral_type.lower() == 'algo':
            adjustment *= self.config.crypto_specific.algo_volatility_adjustment

        # Borrower profile adjustments
        if borrower_profile:
            # Staking reduces prepayment likelihood
            if borrower_profile.get('staking_participation', False):
                adjustment *= self.config.crypto_specific.staking_duration_bonus

            # High on-chain activity reduces prepayment risk
            if borrower_profile.get('high_activity', False):
                adjustment *= self.config.crypto_specific.high_activity_duration_discount

            # Governance participation locks reduce prepayment
            if borrower_profile.get('governance_locked', False):
                adjustment *= self.config.crypto_specific.governance_lock_penalty

        return adjustment

    def _calculate_expected_prepayment_time(self, term_days: int, probability: float) -> float:
        """Calculate expected time to prepayment."""
        if probability <= 0.01:
            return term_days  # No expected prepayment

        # Model as exponential distribution
        lambda_param = -math.log(1 - probability) / term_days
        expected_time = 1 / lambda_param

        return min(expected_time, term_days * 0.9)  # Cap at 90% of term

    def _calculate_prepayment_penalty(self, loan_terms: LoanTerms, expected_time: float) -> Decimal:
        """Calculate prepayment penalty amount."""
        if not loan_terms.prepayment_allowed:
            return Decimal('0')

        penalty_rates = self.config.prepayment_risk.prepayment_penalty_rates
        penalty_rate = penalty_rates.get('early_exit', Decimal('0.02'))

        # Penalty scales with remaining term
        remaining_ratio = max(0, (loan_terms.term_days - expected_time) / loan_terms.term_days)
        scaled_penalty = penalty_rate * Decimal(str(remaining_ratio))

        return loan_terms.principal_amount * scaled_penalty

    def _calculate_model_confidence(
        self,
        loan_terms: LoanTerms,
        market_conditions: Dict[str, float],
        borrower_profile: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in prepayment model."""
        confidence = 0.5  # Base confidence

        # Increase confidence with more data
        if borrower_profile:
            confidence += 0.2

        # Standard term increases confidence
        if loan_terms.term_days in self.config.term_structure.standard_terms:
            confidence += 0.1

        # Market data availability
        if len(market_conditions) >= 3:
            confidence += 0.1

        # Stable market conditions increase confidence
        volatility = market_conditions.get('volatility', 0.5)
        if volatility < 0.3:
            confidence += 0.1

        return min(1.0, confidence)


class DurationCalculator:
    """Calculates duration and interest rate sensitivity metrics."""

    def __init__(self, config: DurationRiskConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def calculate_duration_metrics(
        self,
        loan_terms: LoanTerms,
        yield_curve: YieldCurve,
        prepayment_model: PrepaymentModel
    ) -> DurationMetrics:
        """
        Calculate comprehensive duration metrics.

        Args:
            loan_terms: Loan specifications
            yield_curve: Current yield curve
            prepayment_model: Prepayment risk model

        Returns:
            Complete duration metrics
        """
        # Get appropriate yield for loan term
        loan_yield = self._get_loan_yield(loan_terms, yield_curve)

        # Calculate different duration measures
        modified_duration = self._calculate_modified_duration(loan_terms, loan_yield, prepayment_model)
        macaulay_duration = self._calculate_macaulay_duration(loan_terms, loan_yield, prepayment_model)
        effective_duration = await self._calculate_effective_duration(loan_terms, yield_curve, prepayment_model)

        # Calculate convexity
        convexity = self._calculate_convexity(loan_terms, loan_yield, prepayment_model)

        # Calculate basis point value
        bpv = self._calculate_basis_point_value(loan_terms, modified_duration)

        # Calculate yield sensitivity
        yield_sensitivity = self._calculate_yield_sensitivity(modified_duration, convexity)

        # Determine duration bucket
        duration_bucket = self._determine_duration_bucket(modified_duration)

        metrics = DurationMetrics(
            modified_duration=modified_duration,
            macaulay_duration=macaulay_duration,
            effective_duration=effective_duration,
            convexity=convexity,
            basis_point_value=bpv,
            yield_sensitivity=yield_sensitivity,
            duration_bucket=duration_bucket
        )

        self.logger.info(f"Duration metrics calculated. Modified duration: {modified_duration:.2f}")

        return metrics

    def _get_loan_yield(self, loan_terms: LoanTerms, yield_curve: YieldCurve) -> float:
        """Get appropriate yield for loan term from curve."""
        # Simple implementation - could be enhanced with credit spread
        curve_builder = YieldCurveBuilder(self.config)
        base_rate = curve_builder.get_rate_for_term(yield_curve, loan_terms.term_days)
        return float(base_rate)

    def _calculate_modified_duration(
        self,
        loan_terms: LoanTerms,
        yield_rate: float,
        prepayment_model: PrepaymentModel
    ) -> float:
        """Calculate modified duration with prepayment adjustment."""
        # Basic calculation for bullet payment (can be enhanced for amortizing loans)
        term_years = loan_terms.term_days / 365.25

        if yield_rate <= 0:
            return term_years

        # Standard modified duration formula
        duration = term_years / (1 + yield_rate)

        # Adjust for prepayment risk
        prepayment_adjustment = 1 - (prepayment_model.adjusted_prepayment_probability * 0.3)
        adjusted_duration = duration * prepayment_adjustment

        return max(0.1, adjusted_duration)

    def _calculate_macaulay_duration(
        self,
        loan_terms: LoanTerms,
        yield_rate: float,
        prepayment_model: PrepaymentModel
    ) -> float:
        """Calculate Macaulay duration."""
        term_years = loan_terms.term_days / 365.25

        # For bullet payment, Macaulay duration approximates term
        duration = term_years

        # Adjust for prepayment
        expected_life_ratio = prepayment_model.expected_prepayment_time / loan_terms.term_days
        adjusted_duration = duration * expected_life_ratio

        return max(0.1, adjusted_duration)

    async def _calculate_effective_duration(
        self,
        loan_terms: LoanTerms,
        yield_curve: YieldCurve,
        prepayment_model: PrepaymentModel
    ) -> float:
        """Calculate effective duration using yield curve shifts."""
        base_price = self._calculate_loan_price(loan_terms, yield_curve, prepayment_model)

        # Shift yield curve up by 100 basis points
        shifted_up_curve = self._shift_yield_curve(yield_curve, 0.01)
        price_up = self._calculate_loan_price(loan_terms, shifted_up_curve, prepayment_model)

        # Shift yield curve down by 100 basis points
        shifted_down_curve = self._shift_yield_curve(yield_curve, -0.01)
        price_down = self._calculate_loan_price(loan_terms, shifted_down_curve, prepayment_model)

        # Effective duration formula
        if base_price > 0:
            effective_duration = (price_down - price_up) / (2 * base_price * 0.01)
        else:
            effective_duration = 0.0

        return max(0.0, effective_duration)

    def _calculate_convexity(
        self,
        loan_terms: LoanTerms,
        yield_rate: float,
        prepayment_model: PrepaymentModel
    ) -> float:
        """Calculate convexity measure."""
        term_years = loan_terms.term_days / 365.25

        if yield_rate <= 0:
            return 0.0

        # Simplified convexity calculation
        convexity = term_years * (term_years + 1) / ((1 + yield_rate) ** 2)

        # Adjust for prepayment (negative convexity effect)
        prepayment_factor = 1 - prepayment_model.adjusted_prepayment_probability
        adjusted_convexity = convexity * prepayment_factor

        return max(0.0, adjusted_convexity)

    def _calculate_basis_point_value(self, loan_terms: LoanTerms, modified_duration: float) -> Decimal:
        """Calculate basis point value (dollar duration)."""
        # BPV = Modified Duration × Principal × 0.0001
        bpv = modified_duration * float(loan_terms.principal_amount) * 0.0001
        return Decimal(str(bpv))

    def _calculate_yield_sensitivity(self, modified_duration: float, convexity: float) -> float:
        """Calculate yield sensitivity including convexity."""
        # For small yield changes, include convexity effect
        yield_change = 0.01  # 1% change
        sensitivity = modified_duration + 0.5 * convexity * (yield_change ** 2)
        return sensitivity

    def _determine_duration_bucket(self, duration: float) -> str:
        """Determine duration risk bucket."""
        buckets = self.config.duration_risk.duration_buckets

        for bucket_name, (min_dur, max_dur) in buckets.items():
            if min_dur <= duration < max_dur:
                return bucket_name

        return "very_long"  # Default for high duration

    def _calculate_loan_price(
        self,
        loan_terms: LoanTerms,
        yield_curve: YieldCurve,
        prepayment_model: PrepaymentModel
    ) -> float:
        """Calculate loan price given yield curve and prepayment model."""
        # Simplified pricing - present value of cash flows
        discount_rate = self._get_loan_yield(loan_terms, yield_curve)
        term_years = loan_terms.term_days / 365.25

        # Adjust for prepayment probability
        expected_life = prepayment_model.expected_prepayment_time / 365.25
        effective_term = min(term_years, expected_life)

        if discount_rate <= 0:
            return float(loan_terms.principal_amount)

        # Present value calculation
        pv = float(loan_terms.principal_amount) / ((1 + discount_rate) ** effective_term)
        return pv

    def _shift_yield_curve(self, yield_curve: YieldCurve, shift_amount: float) -> YieldCurve:
        """Shift entire yield curve by specified amount."""
        shifted_points = []

        for point in yield_curve.curve_points:
            shifted_rate = point.yield_rate + Decimal(str(shift_amount))
            shifted_point = YieldCurvePoint(
                term_days=point.term_days,
                yield_rate=shifted_rate,
                timestamp=point.timestamp,
                source=f"{point.source}_shifted"
            )
            shifted_points.append(shifted_point)

        return YieldCurve(
            curve_points=shifted_points,
            curve_date=yield_curve.curve_date,
            interpolation_method=yield_curve.interpolation_method
        )


class DurationRiskEngine:
    """Main duration risk modeling engine."""

    def __init__(self, config: DurationRiskConfig = None):
        self.config = config or DEFAULT_DURATION_CONFIG
        self.logger = logging.getLogger(__name__)

        self.yield_curve_builder = YieldCurveBuilder(self.config)
        self.prepayment_analyzer = PrepaymentRiskAnalyzer(self.config)
        self.duration_calculator = DurationCalculator(self.config)

    async def analyze_duration_risk(
        self,
        loan_terms: LoanTerms,
        market_rates: Dict[int, Decimal],
        market_conditions: Dict[str, float],
        borrower_profile: Optional[Dict[str, Any]] = None,
        portfolio_context: Optional[List[AssetLiabilityPosition]] = None
    ) -> DurationRiskAssessment:
        """
        Comprehensive duration risk analysis.

        Args:
            loan_terms: Loan specifications
            market_rates: Current market rates by term
            market_conditions: Market condition indicators
            borrower_profile: Optional borrower profile
            portfolio_context: Optional portfolio context for AL matching

        Returns:
            Complete duration risk assessment
        """
        assessment_id = f"duration_risk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(f"Starting duration risk analysis: {assessment_id}")

        # Build yield curve
        yield_curve = await self.yield_curve_builder.build_yield_curve(market_rates)

        # Analyze prepayment risk
        prepayment_model = await self.prepayment_analyzer.analyze_prepayment_risk(
            loan_terms, market_conditions, borrower_profile
        )

        # Calculate duration metrics
        duration_metrics = await self.duration_calculator.calculate_duration_metrics(
            loan_terms, yield_curve, prepayment_model
        )

        # Create term structure analysis
        term_structure_analysis = await self._create_term_structure_analysis(
            loan_terms, yield_curve, duration_metrics, prepayment_model
        )

        # Calculate duration risk score
        duration_risk_score = self._calculate_duration_risk_score(
            duration_metrics, prepayment_model, market_conditions
        )

        # Analyze asset-liability mismatch
        al_mismatch = self._analyze_asset_liability_mismatch(
            duration_metrics, portfolio_context
        )

        # Run stress tests
        stress_test_results = await self._run_stress_tests(
            loan_terms, yield_curve, duration_metrics, prepayment_model
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            duration_risk_score, al_mismatch, stress_test_results
        )

        # Calculate final duration premium
        duration_premium = self._calculate_duration_premium(
            duration_risk_score, duration_metrics, market_conditions
        )

        assessment = DurationRiskAssessment(
            assessment_id=assessment_id,
            assessment_timestamp=datetime.utcnow(),
            loan_terms=loan_terms,
            term_structure_analysis=term_structure_analysis,
            duration_risk_score=duration_risk_score,
            asset_liability_mismatch=al_mismatch,
            stress_test_results=stress_test_results,
            recommended_adjustments=recommendations,
            final_duration_premium=duration_premium
        )

        self.logger.info(f"Duration risk analysis completed. Risk score: {duration_risk_score:.3f}")

        return assessment

    async def _create_term_structure_analysis(
        self,
        loan_terms: LoanTerms,
        yield_curve: YieldCurve,
        duration_metrics: DurationMetrics,
        prepayment_model: PrepaymentModel
    ) -> TermStructureAnalysis:
        """Create comprehensive term structure analysis."""
        # Calculate term spread
        base_rate = self.yield_curve_builder.get_rate_for_term(yield_curve, loan_terms.term_days)
        term_spread_config = self.config.term_structure.term_spreads.get(
            loan_terms.term_days, Decimal('0.02')
        )
        term_spread = term_spread_config

        # Calculate risk-adjusted rate
        risk_adjusted_rate = base_rate + term_spread

        # Calculate confidence interval (simplified)
        confidence_width = Decimal('0.005')  # 50 basis points
        confidence_interval = (
            risk_adjusted_rate - confidence_width,
            risk_adjusted_rate + confidence_width
        )

        return TermStructureAnalysis(
            loan_terms=loan_terms,
            yield_curve=yield_curve,
            term_spread=term_spread,
            duration_metrics=duration_metrics,
            prepayment_model=prepayment_model,
            risk_adjusted_rate=risk_adjusted_rate,
            confidence_interval=confidence_interval
        )

    def _calculate_duration_risk_score(
        self,
        duration_metrics: DurationMetrics,
        prepayment_model: PrepaymentModel,
        market_conditions: Dict[str, float]
    ) -> float:
        """Calculate overall duration risk score."""
        score = 0.0

        # Duration bucket scoring
        bucket_multipliers = self.config.duration_risk.duration_risk_multipliers
        bucket_multiplier = bucket_multipliers.get(duration_metrics.duration_bucket, 1.0)
        duration_component = min(1.0, duration_metrics.modified_duration / 10.0) * bucket_multiplier

        # Prepayment risk component
        prepayment_component = prepayment_model.adjusted_prepayment_probability

        # Market volatility component
        volatility = market_conditions.get('volatility', 0.3)
        volatility_component = min(1.0, volatility / 0.5)

        # Convexity component (negative convexity increases risk)
        convexity_component = max(0.0, 1.0 - (duration_metrics.convexity / 10.0))

        # Weight components
        score = (
            duration_component * 0.4 +
            prepayment_component * 0.3 +
            volatility_component * 0.2 +
            convexity_component * 0.1
        )

        return min(1.0, max(0.0, score))

    def _analyze_asset_liability_mismatch(
        self,
        duration_metrics: DurationMetrics,
        portfolio_context: Optional[List[AssetLiabilityPosition]]
    ) -> float:
        """Analyze asset-liability duration mismatch."""
        if not portfolio_context:
            return 0.0  # No mismatch data available

        # Calculate portfolio average duration
        total_notional = sum(pos.notional_amount for pos in portfolio_context)
        if total_notional == 0:
            return 0.0

        weighted_duration = sum(
            pos.duration * float(pos.notional_amount) for pos in portfolio_context
        ) / float(total_notional)

        # Calculate mismatch
        duration_mismatch = abs(duration_metrics.modified_duration - weighted_duration)
        tolerance = self.config.asset_liability.duration_matching_tolerance

        # Normalize mismatch score
        mismatch_score = min(1.0, duration_mismatch / (tolerance * 2))

        return mismatch_score

    async def _run_stress_tests(
        self,
        loan_terms: LoanTerms,
        yield_curve: YieldCurve,
        duration_metrics: DurationMetrics,
        prepayment_model: PrepaymentModel
    ) -> Dict[str, float]:
        """Run stress test scenarios."""
        stress_results = {}

        scenarios = self.config.stress_test_scenarios

        for scenario in scenarios:
            if scenario == "rate_shock_up_200bp":
                stress_results[scenario] = self._stress_test_rate_shock(
                    loan_terms, yield_curve, duration_metrics, 0.02
                )
            elif scenario == "rate_shock_down_100bp":
                stress_results[scenario] = self._stress_test_rate_shock(
                    loan_terms, yield_curve, duration_metrics, -0.01
                )
            elif scenario == "volatility_spike":
                stress_results[scenario] = self._stress_test_volatility_spike(
                    prepayment_model, duration_metrics
                )
            elif scenario == "liquidity_crisis":
                stress_results[scenario] = self._stress_test_liquidity_crisis(
                    duration_metrics, prepayment_model
                )

        return stress_results

    def _stress_test_rate_shock(
        self,
        loan_terms: LoanTerms,
        yield_curve: YieldCurve,
        duration_metrics: DurationMetrics,
        rate_shock: float
    ) -> float:
        """Test impact of parallel rate shock."""
        # Price change approximation using duration and convexity
        price_change = -(duration_metrics.modified_duration * rate_shock) + \
                      (0.5 * duration_metrics.convexity * (rate_shock ** 2))

        # Convert to risk score (higher absolute change = higher risk)
        risk_score = min(1.0, abs(price_change))
        return risk_score

    def _stress_test_volatility_spike(
        self,
        prepayment_model: PrepaymentModel,
        duration_metrics: DurationMetrics
    ) -> float:
        """Test impact of volatility spike."""
        # Higher volatility increases prepayment and duration risk
        vol_impact = prepayment_model.adjusted_prepayment_probability * 1.5
        duration_impact = duration_metrics.modified_duration / 10.0

        risk_score = min(1.0, (vol_impact + duration_impact) / 2)
        return risk_score

    def _stress_test_liquidity_crisis(
        self,
        duration_metrics: DurationMetrics,
        prepayment_model: PrepaymentModel
    ) -> float:
        """Test impact of liquidity crisis."""
        # Liquidity crisis affects longer duration assets more
        duration_impact = min(1.0, duration_metrics.modified_duration / 5.0)

        # Reduced prepayment ability increases duration risk
        prepayment_impact = 1.0 - prepayment_model.adjusted_prepayment_probability

        risk_score = (duration_impact + prepayment_impact) / 2
        return min(1.0, risk_score)

    def _generate_recommendations(
        self,
        duration_risk_score: float,
        al_mismatch: float,
        stress_test_results: Dict[str, float]
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []

        if duration_risk_score > 0.7:
            recommendations.append("Consider shortening loan term or adding prepayment options")

        if al_mismatch > 0.5:
            recommendations.append("Implement duration hedging to reduce asset-liability mismatch")

        # Stress test based recommendations
        max_stress = max(stress_test_results.values()) if stress_test_results else 0.0
        if max_stress > 0.8:
            recommendations.append("Consider stress testing hedging strategies")

        if "rate_shock_up_200bp" in stress_test_results and stress_test_results["rate_shock_up_200bp"] > 0.6:
            recommendations.append("Add rate caps or consider floating rate structure")

        if not recommendations:
            recommendations.append("Duration risk within acceptable parameters")

        return recommendations

    def _calculate_duration_premium(
        self,
        duration_risk_score: float,
        duration_metrics: DurationMetrics,
        market_conditions: Dict[str, float]
    ) -> Decimal:
        """Calculate final duration risk premium."""
        # Base premium from duration bucket
        bucket_multipliers = self.config.duration_risk.duration_risk_multipliers
        base_multiplier = bucket_multipliers.get(duration_metrics.duration_bucket, 1.0)
        base_premium = Decimal('0.01') * Decimal(str(base_multiplier))  # 1% base * multiplier

        # Risk score adjustment
        risk_adjustment = Decimal(str(duration_risk_score))
        adjusted_premium = base_premium * risk_adjustment

        # Market condition adjustments
        volatility = market_conditions.get('volatility', 0.3)
        if volatility > 0.5:
            vol_multiplier = self.config.market_risk.high_volatility_multiplier
            adjusted_premium *= Decimal(str(vol_multiplier))

        return max(Decimal('0.001'), adjusted_premium)  # Minimum 10 basis points

    def generate_assessment_report(self, assessment: DurationRiskAssessment) -> str:
        """Generate detailed duration risk assessment report."""
        report = f"""
DURATION RISK ASSESSMENT REPORT
===============================

Assessment ID: {assessment.assessment_id}
Assessment Date: {assessment.assessment_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

LOAN TERMS
----------
Principal: {assessment.loan_terms.principal_amount:,.2f}
Term: {assessment.loan_terms.term_days} days
Interest Rate: {assessment.loan_terms.interest_rate:.3%}
Collateral: {assessment.loan_terms.collateral_type}
LTV Ratio: {assessment.loan_terms.ltv_ratio:.1%}

DURATION METRICS
----------------
Modified Duration: {assessment.term_structure_analysis.duration_metrics.modified_duration:.2f}
Macaulay Duration: {assessment.term_structure_analysis.duration_metrics.macaulay_duration:.2f}
Effective Duration: {assessment.term_structure_analysis.duration_metrics.effective_duration:.2f}
Convexity: {assessment.term_structure_analysis.duration_metrics.convexity:.2f}
Duration Bucket: {assessment.term_structure_analysis.duration_metrics.duration_bucket}

PREPAYMENT ANALYSIS
-------------------
Base Prepayment Probability: {assessment.term_structure_analysis.prepayment_model.base_prepayment_probability:.2%}
Adjusted Prepayment Probability: {assessment.term_structure_analysis.prepayment_model.adjusted_prepayment_probability:.2%}
Expected Prepayment Time: {assessment.term_structure_analysis.prepayment_model.expected_prepayment_time:.0f} days
Prepayment Penalty: {assessment.term_structure_analysis.prepayment_model.prepayment_penalty_amount:,.2f}

RISK ASSESSMENT
---------------
Duration Risk Score: {assessment.duration_risk_score:.3f}
Asset-Liability Mismatch: {assessment.asset_liability_mismatch:.3f}
Duration Premium: {assessment.final_duration_premium:.3%}

STRESS TEST RESULTS
-------------------
{json.dumps(assessment.stress_test_results, indent=2)}

RECOMMENDATIONS
---------------
{chr(10).join(f"• {rec}" for rec in assessment.recommended_adjustments)}
"""
        return report