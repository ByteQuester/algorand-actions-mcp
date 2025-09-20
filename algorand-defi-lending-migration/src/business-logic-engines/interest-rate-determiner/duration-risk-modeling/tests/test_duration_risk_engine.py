"""
Test suite for Duration Risk Modeling Engine

Comprehensive tests for term structure analysis, prepayment risk modeling,
and duration-based risk assessment functionality.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from ..core import (
    DurationRiskEngine,
    YieldCurveBuilder,
    PrepaymentRiskAnalyzer,
    DurationCalculator,
    LoanTerms,
    YieldCurvePoint,
    YieldCurve,
    PrepaymentModel,
    DurationMetrics,
    TermStructureAnalysis,
    AssetLiabilityPosition,
    DurationRiskAssessment
)
from ..config import DurationRiskConfig, DEFAULT_DURATION_CONFIG


class TestLoanTerms:
    """Test LoanTerms data class."""

    def test_loan_terms_creation(self):
        """Test creation of loan terms."""
        terms = LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=365,
            interest_rate=Decimal('0.05'),
            collateral_type="ALGO",
            collateral_amount=Decimal('150000'),
            ltv_ratio=0.67
        )

        assert terms.principal_amount == Decimal('100000')
        assert terms.term_days == 365
        assert terms.interest_rate == Decimal('0.05')
        assert terms.collateral_type == "ALGO"
        assert terms.ltv_ratio == 0.67
        assert terms.payment_frequency == "monthly"  # Default
        assert terms.prepayment_allowed is True  # Default

    def test_loan_terms_with_custom_values(self):
        """Test loan terms with custom payment frequency and prepayment settings."""
        terms = LoanTerms(
            principal_amount=Decimal('50000'),
            term_days=180,
            interest_rate=Decimal('0.08'),
            collateral_type="BTC",
            collateral_amount=Decimal('2.5'),
            ltv_ratio=0.5,
            payment_frequency="quarterly",
            prepayment_allowed=False,
            early_termination_penalty=Decimal('0.02')
        )

        assert terms.payment_frequency == "quarterly"
        assert terms.prepayment_allowed is False
        assert terms.early_termination_penalty == Decimal('0.02')


class TestYieldCurvePoint:
    """Test YieldCurvePoint data class."""

    def test_yield_curve_point_creation(self):
        """Test creation of yield curve point."""
        timestamp = datetime.utcnow()
        point = YieldCurvePoint(
            term_days=90,
            yield_rate=Decimal('0.03'),
            timestamp=timestamp,
            source="test_source"
        )

        assert point.term_days == 90
        assert point.yield_rate == Decimal('0.03')
        assert point.timestamp == timestamp
        assert point.source == "test_source"


class TestYieldCurveBuilder:
    """Test YieldCurveBuilder functionality."""

    @pytest.fixture
    def builder(self):
        """Create yield curve builder."""
        config = DurationRiskConfig()
        return YieldCurveBuilder(config)

    @pytest.fixture
    def sample_market_rates(self):
        """Create sample market rates."""
        return {
            30: Decimal('0.02'),
            90: Decimal('0.025'),
            180: Decimal('0.03'),
            365: Decimal('0.035'),
            730: Decimal('0.04')
        }

    @pytest.mark.asyncio
    async def test_build_yield_curve(self, builder, sample_market_rates):
        """Test yield curve construction."""
        curve_date = datetime.utcnow()
        curve = await builder.build_yield_curve(sample_market_rates, curve_date)

        assert isinstance(curve, YieldCurve)
        assert curve.curve_date == curve_date
        assert len(curve.curve_points) >= len(sample_market_rates)

        # Check that original points are included
        original_terms = set(sample_market_rates.keys())
        curve_terms = {point.term_days for point in curve.curve_points}
        assert original_terms.issubset(curve_terms)

    def test_get_rate_for_term_exact_match(self, builder, sample_market_rates):
        """Test getting rate for exact term match."""
        # Create simple curve
        curve_points = [
            YieldCurvePoint(30, Decimal('0.02'), datetime.utcnow(), "test"),
            YieldCurvePoint(90, Decimal('0.025'), datetime.utcnow(), "test"),
            YieldCurvePoint(365, Decimal('0.035'), datetime.utcnow(), "test")
        ]
        curve = YieldCurve(curve_points, datetime.utcnow(), "linear")

        rate = builder.get_rate_for_term(curve, 90)
        assert rate == Decimal('0.025')

    def test_get_rate_for_term_interpolation(self, builder):
        """Test getting rate for term requiring interpolation."""
        curve_points = [
            YieldCurvePoint(30, Decimal('0.02'), datetime.utcnow(), "test"),
            YieldCurvePoint(365, Decimal('0.04'), datetime.utcnow(), "test")
        ]
        curve = YieldCurve(curve_points, datetime.utcnow(), "linear")

        # Should interpolate between 30 and 365 days
        rate = builder.get_rate_for_term(curve, 180)
        assert Decimal('0.02') < rate < Decimal('0.04')

    def test_get_rate_for_term_extrapolation(self, builder):
        """Test getting rate for term requiring extrapolation."""
        curve_points = [
            YieldCurvePoint(90, Decimal('0.025'), datetime.utcnow(), "test"),
            YieldCurvePoint(365, Decimal('0.035'), datetime.utcnow(), "test")
        ]
        curve = YieldCurve(curve_points, datetime.utcnow(), "linear")

        # Short end extrapolation
        rate_short = builder.get_rate_for_term(curve, 30)
        assert rate_short == Decimal('0.025')

        # Long end extrapolation
        rate_long = builder.get_rate_for_term(curve, 1095)
        assert rate_long == Decimal('0.035')


class TestPrepaymentRiskAnalyzer:
    """Test PrepaymentRiskAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create prepayment risk analyzer."""
        config = DurationRiskConfig()
        return PrepaymentRiskAnalyzer(config)

    @pytest.fixture
    def sample_loan_terms(self):
        """Create sample loan terms."""
        return LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=365,
            interest_rate=Decimal('0.06'),
            collateral_type="ALGO",
            collateral_amount=Decimal('150000'),
            ltv_ratio=0.67
        )

    @pytest.fixture
    def sample_market_conditions(self):
        """Create sample market conditions."""
        return {
            'volatility': 0.3,
            'risk_free_rate': 0.04,
            'liquidity': 0.8
        }

    @pytest.mark.asyncio
    async def test_analyze_prepayment_risk(self, analyzer, sample_loan_terms, sample_market_conditions):
        """Test prepayment risk analysis."""
        model = await analyzer.analyze_prepayment_risk(
            sample_loan_terms,
            sample_market_conditions
        )

        assert isinstance(model, PrepaymentModel)
        assert 0.0 <= model.base_prepayment_probability <= 1.0
        assert 0.0 <= model.adjusted_prepayment_probability <= 1.0
        assert model.expected_prepayment_time > 0
        assert model.prepayment_penalty_amount >= Decimal('0')
        assert 0.0 <= model.model_confidence <= 1.0

    def test_get_base_prepayment_probability(self, analyzer):
        """Test base prepayment probability calculation."""
        # Test exact matches
        prob_90 = analyzer._get_base_prepayment_probability(90)
        assert prob_90 > 0

        prob_365 = analyzer._get_base_prepayment_probability(365)
        assert prob_365 > prob_90  # Longer terms have higher prepayment probability

        # Test interpolation
        prob_120 = analyzer._get_base_prepayment_probability(120)
        assert prob_90 < prob_120 < prob_365

    def test_calculate_ltv_adjustment(self, analyzer):
        """Test LTV adjustment calculation."""
        # High LTV should increase prepayment risk
        high_ltv_adj = analyzer._calculate_ltv_adjustment(0.85)
        normal_ltv_adj = analyzer._calculate_ltv_adjustment(0.7)
        low_ltv_adj = analyzer._calculate_ltv_adjustment(0.5)

        assert high_ltv_adj > normal_ltv_adj > low_ltv_adj

    def test_calculate_volatility_adjustment(self, analyzer):
        """Test volatility adjustment calculation."""
        # High volatility should increase prepayment risk
        high_vol_adj = analyzer._calculate_volatility_adjustment({'volatility': 0.6})
        normal_vol_adj = analyzer._calculate_volatility_adjustment({'volatility': 0.3})
        low_vol_adj = analyzer._calculate_volatility_adjustment({'volatility': 0.15})

        assert high_vol_adj > normal_vol_adj > low_vol_adj

    def test_calculate_rate_differential_adjustment(self, analyzer, sample_loan_terms):
        """Test rate differential adjustment calculation."""
        # Loan rate above market should increase prepayment
        high_rate_conditions = {'risk_free_rate': 0.03}  # Loan at 6%, market at 3%
        high_adj = analyzer._calculate_rate_differential_adjustment(
            sample_loan_terms, high_rate_conditions
        )

        # Loan rate at market
        market_rate_conditions = {'risk_free_rate': 0.06}  # Loan at 6%, market at 6%
        market_adj = analyzer._calculate_rate_differential_adjustment(
            sample_loan_terms, market_rate_conditions
        )

        # Loan rate below market should decrease prepayment
        low_rate_conditions = {'risk_free_rate': 0.08}  # Loan at 6%, market at 8%
        low_adj = analyzer._calculate_rate_differential_adjustment(
            sample_loan_terms, low_rate_conditions
        )

        assert high_adj > market_adj > low_adj

    def test_calculate_crypto_adjustment(self, analyzer):
        """Test crypto-specific adjustment calculation."""
        # Test with staking borrower
        staking_profile = {'staking_participation': True, 'high_activity': True}
        staking_adj = analyzer._calculate_crypto_adjustment("ALGO", staking_profile)

        # Test with governance locked borrower
        governance_profile = {'governance_locked': True}
        governance_adj = analyzer._calculate_crypto_adjustment("ALGO", governance_profile)

        # Test with no profile
        no_profile_adj = analyzer._calculate_crypto_adjustment("ALGO", None)

        assert staking_adj < no_profile_adj  # Staking reduces prepayment
        assert governance_adj > no_profile_adj  # Governance lock increases duration risk

    def test_calculate_expected_prepayment_time(self, analyzer):
        """Test expected prepayment time calculation."""
        # High probability should result in earlier expected time
        early_time = analyzer._calculate_expected_prepayment_time(365, 0.8)
        late_time = analyzer._calculate_expected_prepayment_time(365, 0.2)

        assert early_time < late_time
        assert early_time <= 365 * 0.9  # Capped at 90% of term

    def test_calculate_prepayment_penalty(self, analyzer, sample_loan_terms):
        """Test prepayment penalty calculation."""
        # Early prepayment should have higher penalty
        early_penalty = analyzer._calculate_prepayment_penalty(sample_loan_terms, 50)
        late_penalty = analyzer._calculate_prepayment_penalty(sample_loan_terms, 300)

        assert early_penalty > late_penalty

        # No prepayment allowed
        no_prepay_terms = LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=365,
            interest_rate=Decimal('0.06'),
            collateral_type="ALGO",
            collateral_amount=Decimal('150000'),
            ltv_ratio=0.67,
            prepayment_allowed=False
        )
        no_penalty = analyzer._calculate_prepayment_penalty(no_prepay_terms, 100)
        assert no_penalty == Decimal('0')


class TestDurationCalculator:
    """Test DurationCalculator functionality."""

    @pytest.fixture
    def calculator(self):
        """Create duration calculator."""
        config = DurationRiskConfig()
        return DurationCalculator(config)

    @pytest.fixture
    def sample_loan_terms(self):
        """Create sample loan terms."""
        return LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=365,
            interest_rate=Decimal('0.05'),
            collateral_type="ALGO",
            collateral_amount=Decimal('150000'),
            ltv_ratio=0.67
        )

    @pytest.fixture
    def sample_yield_curve(self):
        """Create sample yield curve."""
        curve_points = [
            YieldCurvePoint(30, Decimal('0.02'), datetime.utcnow(), "test"),
            YieldCurvePoint(90, Decimal('0.025'), datetime.utcnow(), "test"),
            YieldCurvePoint(180, Decimal('0.03'), datetime.utcnow(), "test"),
            YieldCurvePoint(365, Decimal('0.035'), datetime.utcnow(), "test"),
            YieldCurvePoint(730, Decimal('0.04'), datetime.utcnow(), "test")
        ]
        return YieldCurve(curve_points, datetime.utcnow(), "linear")

    @pytest.fixture
    def sample_prepayment_model(self, sample_loan_terms):
        """Create sample prepayment model."""
        return PrepaymentModel(
            loan_terms=sample_loan_terms,
            base_prepayment_probability=0.3,
            adjusted_prepayment_probability=0.35,
            expected_prepayment_time=250.0,
            prepayment_penalty_amount=Decimal('2000'),
            model_confidence=0.8
        )

    @pytest.mark.asyncio
    async def test_calculate_duration_metrics(
        self, calculator, sample_loan_terms, sample_yield_curve, sample_prepayment_model
    ):
        """Test duration metrics calculation."""
        metrics = await calculator.calculate_duration_metrics(
            sample_loan_terms, sample_yield_curve, sample_prepayment_model
        )

        assert isinstance(metrics, DurationMetrics)
        assert metrics.modified_duration > 0
        assert metrics.macaulay_duration > 0
        assert metrics.effective_duration > 0
        assert metrics.convexity >= 0
        assert metrics.basis_point_value > Decimal('0')
        assert metrics.yield_sensitivity > 0
        assert metrics.duration_bucket in [
            "very_short", "short", "medium", "long", "very_long"
        ]

    def test_calculate_modified_duration(
        self, calculator, sample_loan_terms, sample_prepayment_model
    ):
        """Test modified duration calculation."""
        duration = calculator._calculate_modified_duration(
            sample_loan_terms, 0.05, sample_prepayment_model
        )

        assert duration > 0
        assert duration <= sample_loan_terms.term_days / 365.25  # Cannot exceed term

        # Test with zero yield
        zero_yield_duration = calculator._calculate_modified_duration(
            sample_loan_terms, 0.0, sample_prepayment_model
        )
        assert zero_yield_duration > 0

    def test_calculate_macaulay_duration(
        self, calculator, sample_loan_terms, sample_prepayment_model
    ):
        """Test Macaulay duration calculation."""
        duration = calculator._calculate_macaulay_duration(
            sample_loan_terms, 0.05, sample_prepayment_model
        )

        assert duration > 0
        # Should be affected by prepayment expectations
        expected_life_ratio = sample_prepayment_model.expected_prepayment_time / sample_loan_terms.term_days
        assert duration <= sample_loan_terms.term_days / 365.25

    def test_calculate_convexity(
        self, calculator, sample_loan_terms, sample_prepayment_model
    ):
        """Test convexity calculation."""
        convexity = calculator._calculate_convexity(
            sample_loan_terms, 0.05, sample_prepayment_model
        )

        assert convexity >= 0
        # Prepayment should reduce convexity
        assert convexity <= (sample_loan_terms.term_days / 365.25) ** 2

    def test_calculate_basis_point_value(self, calculator, sample_loan_terms):
        """Test basis point value calculation."""
        bpv = calculator._calculate_basis_point_value(sample_loan_terms, 2.5)

        assert bpv > Decimal('0')
        # Should be proportional to principal and duration
        expected_bpv = 2.5 * float(sample_loan_terms.principal_amount) * 0.0001
        assert abs(float(bpv) - expected_bpv) < 1.0

    def test_determine_duration_bucket(self, calculator):
        """Test duration bucket determination."""
        assert calculator._determine_duration_bucket(0.1) == "very_short"
        assert calculator._determine_duration_bucket(0.5) == "short"
        assert calculator._determine_duration_bucket(2.0) == "medium"
        assert calculator._determine_duration_bucket(5.0) == "long"
        assert calculator._determine_duration_bucket(10.0) == "very_long"

    @pytest.mark.asyncio
    async def test_calculate_effective_duration(
        self, calculator, sample_loan_terms, sample_yield_curve, sample_prepayment_model
    ):
        """Test effective duration calculation."""
        effective_duration = await calculator._calculate_effective_duration(
            sample_loan_terms, sample_yield_curve, sample_prepayment_model
        )

        assert effective_duration >= 0
        # Should be reasonable for 1-year loan
        assert effective_duration <= 5.0


class TestDurationRiskEngine:
    """Test DurationRiskEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create duration risk engine."""
        return DurationRiskEngine()

    @pytest.fixture
    def sample_loan_terms(self):
        """Create sample loan terms."""
        return LoanTerms(
            principal_amount=Decimal('250000'),
            term_days=730,  # 2 years
            interest_rate=Decimal('0.065'),
            collateral_type="ALGO",
            collateral_amount=Decimal('400000'),
            ltv_ratio=0.625
        )

    @pytest.fixture
    def sample_market_rates(self):
        """Create sample market rates."""
        return {
            30: Decimal('0.025'),
            90: Decimal('0.03'),
            180: Decimal('0.035'),
            365: Decimal('0.04'),
            730: Decimal('0.045'),
            1095: Decimal('0.05')
        }

    @pytest.fixture
    def sample_market_conditions(self):
        """Create sample market conditions."""
        return {
            'volatility': 0.25,
            'risk_free_rate': 0.035,
            'liquidity': 0.85,
            'correlation': 0.3
        }

    @pytest.fixture
    def sample_portfolio_context(self):
        """Create sample portfolio context."""
        return [
            AssetLiabilityPosition(
                position_id="pos_001",
                asset_type="loan",
                notional_amount=Decimal('100000'),
                duration=1.8,
                yield_rate=Decimal('0.055'),
                maturity_bucket="medium",
                weight_in_portfolio=0.3
            ),
            AssetLiabilityPosition(
                position_id="pos_002",
                asset_type="deposit",
                notional_amount=Decimal('200000'),
                duration=0.5,
                yield_rate=Decimal('0.025'),
                maturity_bucket="short",
                weight_in_portfolio=0.7
            )
        ]

    @pytest.mark.asyncio
    async def test_analyze_duration_risk_complete(
        self, engine, sample_loan_terms, sample_market_rates,
        sample_market_conditions, sample_portfolio_context
    ):
        """Test complete duration risk analysis."""
        borrower_profile = {
            'staking_participation': True,
            'high_activity': True,
            'governance_locked': False
        }

        assessment = await engine.analyze_duration_risk(
            loan_terms=sample_loan_terms,
            market_rates=sample_market_rates,
            market_conditions=sample_market_conditions,
            borrower_profile=borrower_profile,
            portfolio_context=sample_portfolio_context
        )

        assert isinstance(assessment, DurationRiskAssessment)
        assert assessment.assessment_id.startswith("duration_risk_")
        assert isinstance(assessment.term_structure_analysis, TermStructureAnalysis)
        assert 0.0 <= assessment.duration_risk_score <= 1.0
        assert 0.0 <= assessment.asset_liability_mismatch <= 1.0
        assert len(assessment.stress_test_results) > 0
        assert len(assessment.recommended_adjustments) > 0
        assert assessment.final_duration_premium >= Decimal('0')

    @pytest.mark.asyncio
    async def test_analyze_duration_risk_minimal(self, engine, sample_loan_terms, sample_market_rates):
        """Test duration risk analysis with minimal inputs."""
        market_conditions = {'volatility': 0.3}

        assessment = await engine.analyze_duration_risk(
            loan_terms=sample_loan_terms,
            market_rates=sample_market_rates,
            market_conditions=market_conditions
        )

        assert isinstance(assessment, DurationRiskAssessment)
        assert assessment.asset_liability_mismatch == 0.0  # No portfolio context
        assert len(assessment.stress_test_results) > 0
        assert assessment.final_duration_premium >= Decimal('0')

    def test_calculate_duration_risk_score(self, engine):
        """Test duration risk score calculation."""
        # Create mock duration metrics
        duration_metrics = DurationMetrics(
            modified_duration=2.5,
            macaulay_duration=2.7,
            effective_duration=2.4,
            convexity=6.5,
            basis_point_value=Decimal('250'),
            yield_sensitivity=2.6,
            duration_bucket="medium"
        )

        # Create mock prepayment model
        prepayment_model = PrepaymentModel(
            loan_terms=LoanTerms(
                principal_amount=Decimal('100000'),
                term_days=730,
                interest_rate=Decimal('0.06'),
                collateral_type="ALGO",
                collateral_amount=Decimal('150000'),
                ltv_ratio=0.67
            ),
            base_prepayment_probability=0.4,
            adjusted_prepayment_probability=0.45,
            expected_prepayment_time=400.0,
            prepayment_penalty_amount=Decimal('2000'),
            model_confidence=0.8
        )

        market_conditions = {
            'volatility': 0.3,
            'liquidity': 0.8
        }

        score = engine._calculate_duration_risk_score(
            duration_metrics, prepayment_model, market_conditions
        )

        assert 0.0 <= score <= 1.0

    def test_analyze_asset_liability_mismatch(self, engine, sample_portfolio_context):
        """Test asset-liability mismatch analysis."""
        duration_metrics = DurationMetrics(
            modified_duration=2.0,
            macaulay_duration=2.1,
            effective_duration=1.9,
            convexity=5.0,
            basis_point_value=Decimal('200'),
            yield_sensitivity=2.1,
            duration_bucket="medium"
        )

        mismatch = engine._analyze_asset_liability_mismatch(
            duration_metrics, sample_portfolio_context
        )

        assert 0.0 <= mismatch <= 1.0

        # Test with no portfolio context
        no_context_mismatch = engine._analyze_asset_liability_mismatch(
            duration_metrics, None
        )
        assert no_context_mismatch == 0.0

    def test_stress_test_rate_shock(self, engine, sample_loan_terms):
        """Test rate shock stress test."""
        duration_metrics = DurationMetrics(
            modified_duration=2.0,
            macaulay_duration=2.1,
            effective_duration=1.9,
            convexity=5.0,
            basis_point_value=Decimal('200'),
            yield_sensitivity=2.1,
            duration_bucket="medium"
        )

        # Test upward rate shock
        stress_result = engine._stress_test_rate_shock(
            sample_loan_terms,
            None,  # yield_curve not used in this test
            duration_metrics,
            0.02  # 200 bp shock
        )

        assert 0.0 <= stress_result <= 1.0

    def test_generate_recommendations(self, engine):
        """Test recommendation generation."""
        # High risk scenario
        high_risk_stress = {
            "rate_shock_up_200bp": 0.9,
            "volatility_spike": 0.7,
            "liquidity_crisis": 0.6
        }

        high_risk_recommendations = engine._generate_recommendations(
            duration_risk_score=0.8,
            al_mismatch=0.6,
            stress_test_results=high_risk_stress
        )

        assert len(high_risk_recommendations) > 1
        assert any("hedging" in rec.lower() for rec in high_risk_recommendations)

        # Low risk scenario
        low_risk_stress = {
            "rate_shock_up_200bp": 0.2,
            "volatility_spike": 0.1,
            "liquidity_crisis": 0.15
        }

        low_risk_recommendations = engine._generate_recommendations(
            duration_risk_score=0.3,
            al_mismatch=0.2,
            stress_test_results=low_risk_stress
        )

        assert "acceptable parameters" in low_risk_recommendations[0].lower()

    def test_calculate_duration_premium(self, engine):
        """Test duration premium calculation."""
        duration_metrics = DurationMetrics(
            modified_duration=3.5,
            macaulay_duration=3.7,
            effective_duration=3.4,
            convexity=12.0,
            basis_point_value=Decimal('350'),
            yield_sensitivity=3.6,
            duration_bucket="long"
        )

        # Normal market conditions
        normal_conditions = {'volatility': 0.25}
        normal_premium = engine._calculate_duration_premium(
            duration_risk_score=0.6,
            duration_metrics=duration_metrics,
            market_conditions=normal_conditions
        )

        # High volatility conditions
        high_vol_conditions = {'volatility': 0.6}
        high_vol_premium = engine._calculate_duration_premium(
            duration_risk_score=0.6,
            duration_metrics=duration_metrics,
            market_conditions=high_vol_conditions
        )

        assert normal_premium >= Decimal('0.001')  # Minimum premium
        assert high_vol_premium > normal_premium  # Higher premium for high volatility

    def test_generate_assessment_report(self, engine):
        """Test assessment report generation."""
        # Create mock assessment
        loan_terms = LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=365,
            interest_rate=Decimal('0.06'),
            collateral_type="ALGO",
            collateral_amount=Decimal('150000'),
            ltv_ratio=0.67
        )

        duration_metrics = DurationMetrics(
            modified_duration=2.5,
            macaulay_duration=2.7,
            effective_duration=2.4,
            convexity=6.5,
            basis_point_value=Decimal('250'),
            yield_sensitivity=2.6,
            duration_bucket="medium"
        )

        assessment = DurationRiskAssessment(
            assessment_id="test_001",
            assessment_timestamp=datetime.utcnow(),
            loan_terms=loan_terms,
            term_structure_analysis=Mock(duration_metrics=duration_metrics),
            duration_risk_score=0.65,
            asset_liability_mismatch=0.3,
            stress_test_results={"rate_shock_up_200bp": 0.4},
            recommended_adjustments=["Test recommendation"],
            final_duration_premium=Decimal('0.025')
        )

        # Mock the term structure analysis to avoid complex object creation
        assessment.term_structure_analysis.prepayment_model = Mock()
        assessment.term_structure_analysis.prepayment_model.base_prepayment_probability = 0.3
        assessment.term_structure_analysis.prepayment_model.adjusted_prepayment_probability = 0.35
        assessment.term_structure_analysis.prepayment_model.expected_prepayment_time = 250
        assessment.term_structure_analysis.prepayment_model.prepayment_penalty_amount = Decimal('2000')

        report = engine.generate_assessment_report(assessment)

        assert "DURATION RISK ASSESSMENT REPORT" in report
        assert "test_001" in report
        assert "100,000.00" in report  # Principal amount
        assert "2.50" in report  # Modified duration
        assert "0.650" in report  # Risk score


class TestIntegration:
    """Integration tests for the complete duration risk system."""

    @pytest.fixture
    def complete_engine(self):
        """Create engine with custom configuration."""
        config = DurationRiskConfig()
        config.term_structure.standard_terms = [30, 90, 180, 365, 730]
        config.monte_carlo_simulations = 1000  # Reduced for testing
        return DurationRiskEngine(config)

    @pytest.mark.asyncio
    async def test_end_to_end_duration_analysis(self, complete_engine):
        """Test complete end-to-end duration risk analysis."""
        # Create comprehensive loan
        loan_terms = LoanTerms(
            principal_amount=Decimal('500000'),
            term_days=1095,  # 3 years
            interest_rate=Decimal('0.075'),
            collateral_type="ALGO",
            collateral_amount=Decimal('800000'),
            ltv_ratio=0.625,
            payment_frequency="quarterly"
        )

        # Market rates
        market_rates = {
            30: Decimal('0.02'),
            90: Decimal('0.025'),
            180: Decimal('0.03'),
            365: Decimal('0.038'),
            730: Decimal('0.045'),
            1095: Decimal('0.052')
        }

        # Market conditions
        market_conditions = {
            'volatility': 0.35,
            'risk_free_rate': 0.03,
            'liquidity': 0.75,
            'correlation': 0.4
        }

        # Borrower profile
        borrower_profile = {
            'staking_participation': True,
            'high_activity': False,
            'governance_locked': True
        }

        # Portfolio context
        portfolio_context = [
            AssetLiabilityPosition(
                position_id="loan_001",
                asset_type="loan",
                notional_amount=Decimal('300000'),
                duration=2.8,
                yield_rate=Decimal('0.07'),
                maturity_bucket="medium",
                weight_in_portfolio=0.4
            ),
            AssetLiabilityPosition(
                position_id="deposit_001",
                asset_type="deposit",
                notional_amount=Decimal('450000'),
                duration=0.8,
                yield_rate=Decimal('0.03'),
                maturity_bucket="short",
                weight_in_portfolio=0.6
            )
        ]

        # Run complete analysis
        assessment = await complete_engine.analyze_duration_risk(
            loan_terms=loan_terms,
            market_rates=market_rates,
            market_conditions=market_conditions,
            borrower_profile=borrower_profile,
            portfolio_context=portfolio_context
        )

        # Comprehensive validation
        assert isinstance(assessment, DurationRiskAssessment)
        assert assessment.duration_risk_score > 0.4  # 3-year loan should have meaningful risk
        assert assessment.asset_liability_mismatch > 0.1  # Should have some mismatch
        assert len(assessment.stress_test_results) >= 3  # Multiple stress scenarios
        assert assessment.final_duration_premium > Decimal('0.01')  # Meaningful premium

        # Generate comprehensive report
        report = complete_engine.generate_assessment_report(assessment)
        assert len(report) > 1000  # Substantial report
        assert "3 years" in report or "1095" in report  # Term information

    @pytest.mark.asyncio
    async def test_short_term_vs_long_term_comparison(self, complete_engine):
        """Test comparison between short-term and long-term loans."""
        market_rates = {
            30: Decimal('0.025'),
            90: Decimal('0.03'),
            365: Decimal('0.04'),
            730: Decimal('0.045')
        }

        market_conditions = {'volatility': 0.3}

        # Short-term loan (90 days)
        short_term_loan = LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=90,
            interest_rate=Decimal('0.035'),
            collateral_type="ALGO",
            collateral_amount=Decimal('130000'),
            ltv_ratio=0.77
        )

        # Long-term loan (2 years)
        long_term_loan = LoanTerms(
            principal_amount=Decimal('100000'),
            term_days=730,
            interest_rate=Decimal('0.065'),
            collateral_type="ALGO",
            collateral_amount=Decimal('130000'),
            ltv_ratio=0.77
        )

        # Analyze both
        short_assessment = await complete_engine.analyze_duration_risk(
            short_term_loan, market_rates, market_conditions
        )

        long_assessment = await complete_engine.analyze_duration_risk(
            long_term_loan, market_rates, market_conditions
        )

        # Long-term should have higher duration risk and premium
        assert long_assessment.duration_risk_score > short_assessment.duration_risk_score
        assert long_assessment.final_duration_premium > short_assessment.final_duration_premium

        # Duration metrics should reflect term differences
        short_duration = short_assessment.term_structure_analysis.duration_metrics.modified_duration
        long_duration = long_assessment.term_structure_analysis.duration_metrics.modified_duration
        assert long_duration > short_duration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])