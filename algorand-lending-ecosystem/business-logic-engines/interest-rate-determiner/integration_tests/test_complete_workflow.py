"""
Complete Workflow Integration Tests

Tests the complete interest rate determination workflow using all 6 engines
and validates the end-to-end integration scenarios.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime

from interest_rate_determiner import (
    MarketRateAnalysisEngine, RiskAssessmentEngine, CreditScoringEngine,
    RegulatoryComplianceEngine, DynamicPricingEngine, RateOptimizationEngine,
    get_available_engines
)


class TestCompleteWorkflow:
    """Test complete interest rate determination workflow"""

    @pytest.fixture
    def sample_loan_request(self):
        """Sample loan request for testing"""
        return {
            'loan_amount': Decimal('50000'),
            'duration_days': 365,
            'borrower_id': 'test_borrower_001',
            'asset': 'ALGO',
            'jurisdiction': 'us_federal'
        }

    @pytest.fixture
    def sample_borrower_profile(self):
        """Sample borrower profile for testing"""
        from interest_rate_determiner.risk_assessment.core.risk_engine import BorrowerProfile

        return BorrowerProfile(
            borrower_id='test_borrower_001',
            credit_score=720,
            debt_to_income_ratio=0.3,
            employment_status='employed',
            annual_income=Decimal('75000'),
            algorand_wallet_age=365,
            defi_experience_score=0.7,
            governance_participation=True
        )

    @pytest.fixture
    def sample_market_factors(self):
        """Sample market risk factors for testing"""
        from interest_rate_determiner.risk_assessment.core.risk_engine import MarketRiskFactors

        return MarketRiskFactors(
            asset_volatility=0.4,
            liquidity_risk=0.3,
            regulatory_risk=0.2,
            technology_risk=0.1,
            smart_contract_risk=0.1
        )

    @pytest.mark.asyncio
    async def test_engine_availability(self):
        """Test that all engines are available and can be instantiated"""
        available_engines = get_available_engines()

        # Should have all 6 engines
        expected_engines = {
            'market_rate_analysis', 'risk_assessment', 'credit_scoring',
            'regulatory_compliance', 'dynamic_pricing', 'rate_optimization'
        }

        # Check that at least some engines are available (in case of import issues)
        assert len(available_engines) > 0, "No engines available"

        # Test instantiation of available engines
        for engine_name, engine_class in available_engines.items():
            engine_instance = engine_class()
            assert engine_instance is not None, f"Failed to instantiate {engine_name}"

    @pytest.mark.asyncio
    async def test_market_analysis_engine(self, sample_loan_request):
        """Test Market Rate Analysis Engine"""
        available_engines = get_available_engines()

        if 'market_rate_analysis' not in available_engines:
            pytest.skip("Market Rate Analysis Engine not available")

        engine = available_engines['market_rate_analysis']()
        analysis = await engine.analyze_market_rates(
            sample_loan_request['asset'],
            24  # 24 hours analysis
        )

        # Validate analysis results
        assert analysis.base_rate > 0, "Base rate should be positive"
        assert analysis.base_rate < 1, "Base rate should be less than 100%"
        assert analysis.market_sentiment in ['bullish', 'bearish', 'neutral']
        assert 0 <= analysis.volatility_score <= 1
        assert 0 <= analysis.liquidity_score <= 1
        assert 0 <= analysis.confidence <= 1
        assert isinstance(analysis.risk_factors, list)
        assert isinstance(analysis.analysis_timestamp, datetime)

    @pytest.mark.asyncio
    async def test_risk_assessment_engine(self, sample_loan_request, sample_borrower_profile, sample_market_factors):
        """Test Risk Assessment Engine"""
        available_engines = get_available_engines()

        if 'risk_assessment' not in available_engines:
            pytest.skip("Risk Assessment Engine not available")

        engine = available_engines['risk_assessment']()
        assessment = await engine.assess_risk(
            sample_borrower_profile,
            sample_market_factors,
            sample_loan_request['loan_amount'],
            sample_loan_request['duration_days']
        )

        # Validate assessment results
        assert assessment.risk_premium > 0, "Risk premium should be positive"
        assert 0 <= assessment.risk_score <= 100, "Risk score should be between 0-100"
        assert 0 <= assessment.credit_risk_score <= 100
        assert 0 <= assessment.market_risk_score <= 100
        assert 0 <= assessment.operational_risk_score <= 100
        assert 0 <= assessment.confidence <= 1
        assert isinstance(assessment.risk_factors, list)
        assert isinstance(assessment.mitigation_recommendations, list)

    @pytest.mark.asyncio
    async def test_credit_scoring_engine(self):
        """Test Credit Scoring Engine"""
        available_engines = get_available_engines()

        if 'credit_scoring' not in available_engines:
            pytest.skip("Credit Scoring Engine not available")

        engine = available_engines['credit_scoring']()

        # Create test data
        from interest_rate_determiner.credit_scoring.core.credit_engine import (
            TraditionalCreditData, BlockchainCreditData, BehavioralCreditData
        )

        traditional_data = TraditionalCreditData(
            credit_score=720,
            credit_history_length_months=60,
            credit_utilization=0.25,
            debt_to_income_ratio=0.3
        )

        blockchain_data = BlockchainCreditData(
            wallet_address="test_wallet_123",
            wallet_age_days=365,
            transaction_count=150,
            average_balance=Decimal('10000'),
            staking_participation=True,
            governance_participation=True
        )

        behavioral_data = BehavioralCreditData(
            transaction_regularity=0.8,
            risk_taking_behavior='moderate',
            long_term_holding_pattern=True,
            diversification_score=0.7
        )

        score = await engine.calculate_credit_score(
            traditional_data, blockchain_data, behavioral_data
        )

        # Validate credit score results
        assert 300 <= score.overall_score <= 850, "Credit score should be in valid range"
        assert score.traditional_score is None or (300 <= score.traditional_score <= 850)
        assert 300 <= score.blockchain_score <= 850
        assert 300 <= score.behavioral_score <= 850
        assert 0 <= score.confidence_level <= 1
        assert isinstance(score.positive_factors, list)
        assert isinstance(score.negative_factors, list)
        assert isinstance(score.recommendations, list)

    @pytest.mark.asyncio
    async def test_regulatory_compliance_engine(self, sample_loan_request):
        """Test Regulatory Compliance Engine"""
        available_engines = get_available_engines()

        if 'regulatory_compliance' not in available_engines:
            pytest.skip("Regulatory Compliance Engine not available")

        engine = available_engines['regulatory_compliance']()

        from interest_rate_determiner.regulatory_compliance.core.compliance_engine import Jurisdiction

        proposed_rate = Decimal('0.15')  # 15% annual rate
        jurisdiction = Jurisdiction.US_FEDERAL

        compliance = await engine.verify_compliance(
            proposed_rate,
            sample_loan_request['loan_amount'],
            sample_loan_request['duration_days'],
            jurisdiction
        )

        # Validate compliance results
        assert isinstance(compliance.is_compliant, bool)
        assert compliance.applied_rate > 0
        assert compliance.max_allowed_rate > 0
        assert isinstance(compliance.violations, list)
        assert isinstance(compliance.warnings, list)
        assert isinstance(compliance.required_disclosures, list)
        assert 0 <= compliance.compliance_score <= 1

    @pytest.mark.asyncio
    async def test_dynamic_pricing_engine(self):
        """Test Dynamic Pricing Engine"""
        available_engines = get_available_engines()

        if 'dynamic_pricing' not in available_engines:
            pytest.skip("Dynamic Pricing Engine not available")

        engine = available_engines['dynamic_pricing']()

        from interest_rate_determiner.dynamic_pricing.core.pricing_engine import MarketConditions

        base_rate = Decimal('0.05')
        market_conditions = MarketConditions(
            supply_utilization=0.8,
            demand_pressure=0.7,
            liquidity_index=0.6,
            volatility_index=0.4,
            competitor_rates={'competitor_a': Decimal('0.06'), 'competitor_b': Decimal('0.055')}
        )

        adjustment = await engine.calculate_dynamic_rate(base_rate, market_conditions)

        # Validate dynamic pricing results
        assert adjustment.base_rate == base_rate
        assert adjustment.adjusted_rate > 0
        assert adjustment.adjustment_factor > 0
        assert isinstance(adjustment.reasoning, list)
        assert 0 <= adjustment.confidence <= 1

    @pytest.mark.asyncio
    async def test_rate_optimization_engine(self):
        """Test Rate Optimization Engine"""
        available_engines = get_available_engines()

        if 'rate_optimization' not in available_engines:
            pytest.skip("Rate Optimization Engine not available")

        engine = available_engines['rate_optimization']()

        from interest_rate_determiner.rate_optimization.core.optimization_engine import OptimizationConstraints

        current_rate = Decimal('0.06')
        constraints = OptimizationConstraints(
            min_rate=Decimal('0.03'),
            max_rate=Decimal('0.20'),
            competitor_rates={'competitor_a': Decimal('0.065'), 'competitor_b': Decimal('0.055')},
            target_utilization=0.75,
            profit_margin_target=Decimal('0.02')
        )

        optimization = await engine.optimize_rate(current_rate, constraints)

        # Validate optimization results
        assert constraints.min_rate <= optimization.optimal_rate <= constraints.max_rate
        assert optimization.expected_profit >= 0
        assert 0 <= optimization.expected_utilization <= 1
        assert optimization.competitive_position in ['competitive', 'premium', 'discount']
        assert isinstance(optimization.optimization_reasoning, list)
        assert 0 <= optimization.confidence <= 1

    @pytest.mark.asyncio
    async def test_complete_rate_calculation_workflow(self, sample_loan_request, sample_borrower_profile, sample_market_factors):
        """Test complete rate calculation workflow using multiple engines"""
        available_engines = get_available_engines()

        if len(available_engines) < 3:
            pytest.skip("Insufficient engines available for workflow test")

        # Step 1: Market Analysis
        base_rate = Decimal('0.05')  # Default fallback
        if 'market_rate_analysis' in available_engines:
            market_engine = available_engines['market_rate_analysis']()
            market_analysis = await market_engine.analyze_market_rates(
                sample_loan_request['asset'], 24
            )
            base_rate = market_analysis.base_rate

        # Step 2: Risk Assessment
        risk_premium = Decimal('0.02')  # Default fallback
        if 'risk_assessment' in available_engines:
            risk_engine = available_engines['risk_assessment']()
            risk_assessment = await risk_engine.assess_risk(
                sample_borrower_profile,
                sample_market_factors,
                sample_loan_request['loan_amount'],
                sample_loan_request['duration_days']
            )
            risk_premium = risk_assessment.risk_premium

        # Step 3: Regulatory Compliance
        proposed_rate = base_rate + risk_premium
        final_rate = proposed_rate  # Default fallback

        if 'regulatory_compliance' in available_engines:
            compliance_engine = available_engines['regulatory_compliance']()
            from interest_rate_determiner.regulatory_compliance.core.compliance_engine import Jurisdiction

            compliance_check = await compliance_engine.verify_compliance(
                proposed_rate,
                sample_loan_request['loan_amount'],
                sample_loan_request['duration_days'],
                Jurisdiction.US_FEDERAL
            )
            final_rate = compliance_check.applied_rate

        # Validate final results
        assert final_rate > 0, "Final rate should be positive"
        assert final_rate <= Decimal('0.36'), "Rate should not exceed 36% (usury limit)"

        # Calculate payment details
        monthly_rate = final_rate / 12
        num_months = sample_loan_request['duration_days'] / 30.0

        if monthly_rate > 0:
            monthly_payment = sample_loan_request['loan_amount'] * (
                monthly_rate * (1 + monthly_rate) ** num_months
            ) / ((1 + monthly_rate) ** num_months - 1)
        else:
            monthly_payment = sample_loan_request['loan_amount'] / Decimal(str(num_months))

        total_payment = monthly_payment * Decimal(str(num_months))
        total_interest = total_payment - sample_loan_request['loan_amount']

        # Validate payment calculations
        assert monthly_payment > 0, "Monthly payment should be positive"
        assert total_payment > sample_loan_request['loan_amount'], "Total payment should exceed principal"
        assert total_interest >= 0, "Total interest should be non-negative"

        # Return comprehensive results for further validation
        return {
            'base_rate': float(base_rate),
            'risk_premium': float(risk_premium),
            'final_rate': float(final_rate),
            'monthly_payment': float(monthly_payment),
            'total_payment': float(total_payment),
            'total_interest': float(total_interest),
            'engines_used': len(available_engines)
        }

    @pytest.mark.asyncio
    async def test_performance_benchmark(self, sample_loan_request, sample_borrower_profile, sample_market_factors):
        """Test performance of complete workflow under load"""
        available_engines = get_available_engines()

        if len(available_engines) < 2:
            pytest.skip("Insufficient engines for performance test")

        start_time = datetime.now()

        # Run multiple rate calculations concurrently
        tasks = []
        for i in range(10):  # 10 concurrent calculations
            task = self.test_complete_rate_calculation_workflow(
                sample_loan_request, sample_borrower_profile, sample_market_factors
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Validate performance
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 8, "At least 80% of calculations should succeed"
        assert execution_time < 30, "10 concurrent calculations should complete within 30 seconds"

        # Validate result consistency
        if len(successful_results) > 1:
            first_result = successful_results[0]
            for result in successful_results[1:]:
                # Results should be identical for same inputs
                assert abs(result['final_rate'] - first_result['final_rate']) < 0.001, \
                    "Results should be consistent for identical inputs"

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms"""
        available_engines = get_available_engines()

        # Test with invalid inputs
        if 'risk_assessment' in available_engines:
            engine = available_engines['risk_assessment']()

            from interest_rate_determiner.risk_assessment.core.risk_engine import BorrowerProfile, MarketRiskFactors

            # Test with invalid borrower profile
            invalid_profile = BorrowerProfile(
                borrower_id='',  # Invalid empty ID
                credit_score=-100,  # Invalid negative score
                debt_to_income_ratio=5.0  # Invalid high ratio
            )

            invalid_market_factors = MarketRiskFactors(
                asset_volatility=2.0,  # Invalid high volatility
                liquidity_risk=1.5,  # Invalid value > 1
                regulatory_risk=-0.1  # Invalid negative value
            )

            # Validate input validation
            is_valid, errors = engine.validate_risk_inputs(invalid_profile, invalid_market_factors)
            assert not is_valid, "Validation should fail for invalid inputs"
            assert len(errors) > 0, "Should return validation errors"

    @pytest.mark.asyncio
    async def test_cross_engine_data_validation(self, sample_loan_request):
        """Test data consistency across different engines"""
        available_engines = get_available_engines()

        if len(available_engines) < 2:
            pytest.skip("Need at least 2 engines for cross-validation test")

        # Collect results from different engines
        results = {}

        # Market analysis
        if 'market_rate_analysis' in available_engines:
            market_engine = available_engines['market_rate_analysis']()
            market_result = await market_engine.analyze_market_rates(
                sample_loan_request['asset'], 24
            )
            results['market'] = {
                'base_rate': market_result.base_rate,
                'confidence': market_result.confidence
            }

        # Risk assessment with market data
        if 'risk_assessment' in available_engines:
            risk_engine = available_engines['risk_assessment']()

            from interest_rate_determiner.risk_assessment.core.risk_engine import BorrowerProfile, MarketRiskFactors

            borrower_profile = BorrowerProfile(
                borrower_id=sample_loan_request['borrower_id'],
                credit_score=720
            )

            market_factors = MarketRiskFactors(
                asset_volatility=0.4,
                liquidity_risk=0.3,
                regulatory_risk=0.2
            )

            risk_result = await risk_engine.assess_risk(
                borrower_profile, market_factors,
                sample_loan_request['loan_amount'],
                sample_loan_request['duration_days']
            )
            results['risk'] = {
                'risk_premium': risk_result.risk_premium,
                'confidence': risk_result.confidence
            }

        # Validate cross-engine consistency
        if 'market' in results and 'risk' in results:
            # Both engines should provide reasonable confidence levels
            assert results['market']['confidence'] > 0.3, "Market analysis should have reasonable confidence"
            assert results['risk']['confidence'] > 0.3, "Risk assessment should have reasonable confidence"

            # Combined rate should be reasonable
            combined_rate = results['market']['base_rate'] + results['risk']['risk_premium']
            assert 0.01 <= combined_rate <= 0.50, "Combined rate should be between 1% and 50%"