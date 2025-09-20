"""
Test suite for Risk Premium Assessment Engine

Comprehensive tests for credit scoring, on-chain behavior analysis,
and risk premium calculation functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from ..core import (
    RiskPremiumEngine,
    OnChainBehaviorAnalyzer,
    CreditScoringEngine,
    CreditProfile,
    AlgorandWalletProfile,
    CrossChainProfile,
    MarketConditions,
    RiskAssessment
)
from ..config import RiskPremiumConfig, DEFAULT_CONFIG


class TestCreditProfile:
    """Test CreditProfile data class."""

    def test_credit_profile_creation(self):
        """Test creation of credit profile."""
        profile = CreditProfile(
            credit_score=750,
            credit_age_months=60,
            credit_utilization=0.3,
            payment_history_score=0.95,
            debt_to_income_ratio=0.4
        )

        assert profile.credit_score == 750
        assert profile.credit_age_months == 60
        assert profile.credit_utilization == 0.3
        assert profile.payment_history_score == 0.95
        assert profile.debt_to_income_ratio == 0.4

    def test_credit_profile_defaults(self):
        """Test credit profile with default values."""
        profile = CreditProfile()

        assert profile.credit_score is None
        assert profile.credit_age_months is None
        assert profile.credit_utilization is None


class TestAlgorandWalletProfile:
    """Test AlgorandWalletProfile data class."""

    def test_wallet_profile_creation(self):
        """Test creation of wallet profile."""
        profile = AlgorandWalletProfile(
            wallet_address="ABCD1234EFGH5678IJKL9012MNOP3456QRST7890UVWX1234YZAB",
            wallet_age_days=365,
            total_transactions=1000,
            total_volume_algo=Decimal('50000'),
            governance_participation_count=3,
            defi_protocols_used=['tinyman', 'algofi']
        )

        assert profile.wallet_address == "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890UVWX1234YZAB"
        assert profile.wallet_age_days == 365
        assert profile.total_transactions == 1000
        assert profile.total_volume_algo == Decimal('50000')
        assert profile.governance_participation_count == 3
        assert 'tinyman' in profile.defi_protocols_used


class TestCreditScoringEngine:
    """Test CreditScoringEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create credit scoring engine."""
        config = RiskPremiumConfig()
        return CreditScoringEngine(config)

    @pytest.fixture
    def sample_credit_profile(self):
        """Create sample credit profile."""
        return CreditProfile(
            credit_score=720,
            credit_age_months=48,
            credit_utilization=0.25,
            payment_history_score=0.9,
            credit_mix_score=0.8,
            new_credit_score=0.7,
            debt_to_income_ratio=0.35
        )

    @pytest.mark.asyncio
    async def test_analyze_credit_profile(self, engine, sample_credit_profile):
        """Test credit profile analysis."""
        score, breakdown = await engine.analyze_credit_profile(sample_credit_profile)

        assert 0.0 <= score <= 1.0
        assert isinstance(breakdown, dict)
        assert 'payment_history' in breakdown
        assert 'credit_utilization' in breakdown
        assert 'credit_age' in breakdown
        assert 'credit_mix' in breakdown
        assert 'new_credit' in breakdown

    @pytest.mark.asyncio
    async def test_analyze_credit_profile_missing_data(self, engine):
        """Test credit profile analysis with missing data."""
        profile = CreditProfile(credit_score=650)  # Only credit score provided

        score, breakdown = await engine.analyze_credit_profile(profile)

        assert 0.0 <= score <= 1.0
        assert isinstance(breakdown, dict)
        # Should handle missing data gracefully

    def test_score_payment_history(self, engine):
        """Test payment history scoring."""
        # Test various payment history scores
        assert engine._score_payment_history(1.0) == 1.0
        assert engine._score_payment_history(0.5) == 0.5
        assert engine._score_payment_history(None) == 0.5  # Default for missing data

    def test_score_credit_utilization(self, engine):
        """Test credit utilization scoring."""
        # Test various utilization levels
        assert engine._score_credit_utilization(0.05) == 1.0  # Excellent (5%)
        assert engine._score_credit_utilization(0.2) == 0.8   # Good (20%)
        assert engine._score_credit_utilization(0.8) == 0.2   # Poor (80%)
        assert engine._score_credit_utilization(None) == 0.5  # Missing data

    def test_score_credit_age(self, engine):
        """Test credit age scoring."""
        assert engine._score_credit_age(150) == 1.0  # 12+ years
        assert engine._score_credit_age(72) == 0.8   # 6+ years
        assert engine._score_credit_age(6) == 0.2    # 6 months
        assert engine._score_credit_age(None) == 0.3 # Missing data


class TestOnChainBehaviorAnalyzer:
    """Test OnChainBehaviorAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create on-chain behavior analyzer."""
        config = RiskPremiumConfig()
        return OnChainBehaviorAnalyzer(config)

    @pytest.fixture
    def sample_wallet_profile(self):
        """Create sample wallet profile."""
        return AlgorandWalletProfile(
            wallet_address="ABCD1234EFGH5678IJKL9012MNOP3456QRST7890UVWX1234YZAB",
            wallet_age_days=730,  # 2 years
            total_transactions=2500,
            total_volume_algo=Decimal('100000'),
            average_balance_algo=Decimal('5000'),
            governance_participation_count=4,
            governance_commitment_algo=Decimal('10000'),
            staking_periods=8,
            staking_rewards_algo=Decimal('500'),
            defi_protocols_used=['tinyman', 'algofi', 'folks_finance'],
            smart_contracts_interacted=50,
            asa_tokens_created=2
        )

    @pytest.mark.asyncio
    async def test_analyze_wallet_behavior(self, analyzer, sample_wallet_profile):
        """Test wallet behavior analysis."""
        score, breakdown = await analyzer.analyze_wallet_behavior(sample_wallet_profile)

        assert 0.0 <= score <= 1.0
        assert isinstance(breakdown, dict)
        assert 'wallet_age' in breakdown
        assert 'transaction_volume' in breakdown
        assert 'defi_participation' in breakdown
        assert 'governance_voting' in breakdown
        assert 'staking_history' in breakdown
        assert 'smart_contract_interactions' in breakdown

    def test_score_wallet_age(self, analyzer):
        """Test wallet age scoring."""
        assert analyzer._score_wallet_age(750) == 1.0  # 2+ years
        assert analyzer._score_wallet_age(400) == 0.8  # 1+ year
        assert analyzer._score_wallet_age(200) == 0.6  # 6+ months
        assert analyzer._score_wallet_age(100) == 0.4  # Just above minimum
        assert analyzer._score_wallet_age(30) == 0.1   # Below minimum

    def test_score_transaction_volume(self, analyzer):
        """Test transaction volume scoring."""
        # High volume and count
        score1 = analyzer._score_transaction_volume(1000, Decimal('50000'))
        assert 0.8 <= score1 <= 1.0

        # Low count
        score2 = analyzer._score_transaction_volume(5, Decimal('1000'))
        assert score2 == 0.1

        # No volume
        score3 = analyzer._score_transaction_volume(100, Decimal('0'))
        assert 0.0 <= score3 <= 0.6

    def test_score_defi_participation(self, analyzer):
        """Test DeFi participation scoring."""
        # Multiple whitelisted protocols
        score1 = analyzer._score_defi_participation(['tinyman', 'algofi', 'folks_finance'])
        assert score1 == 1.0

        # Two whitelisted protocols
        score2 = analyzer._score_defi_participation(['tinyman', 'algofi'])
        assert score2 == 0.7

        # One whitelisted protocol
        score3 = analyzer._score_defi_participation(['tinyman'])
        assert score3 == 0.5

        # No protocols
        score4 = analyzer._score_defi_participation([])
        assert score4 == 0.0

    def test_score_governance_participation(self, analyzer):
        """Test governance participation scoring."""
        # High participation and commitment
        score1 = analyzer._score_governance_participation(5, Decimal('15000'))
        assert 0.8 <= score1 <= 1.0

        # No participation
        score2 = analyzer._score_governance_participation(0, Decimal('0'))
        assert score2 == 0.0

    def test_apply_algorand_bonuses(self, analyzer, sample_wallet_profile):
        """Test Algorand-specific bonus application."""
        bonus = analyzer._apply_algorand_bonuses(sample_wallet_profile)

        assert bonus > 0.0  # Should have bonuses with this profile
        assert bonus <= 0.6  # Maximum possible bonus


class TestRiskPremiumEngine:
    """Test RiskPremiumEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create risk premium engine."""
        return RiskPremiumEngine()

    @pytest.fixture
    def sample_credit_profile(self):
        """Create sample credit profile."""
        return CreditProfile(
            credit_score=750,
            credit_age_months=60,
            credit_utilization=0.2,
            payment_history_score=0.95
        )

    @pytest.fixture
    def sample_wallet_profile(self):
        """Create sample wallet profile."""
        return AlgorandWalletProfile(
            wallet_address="SAMPLE1234567890ABCDEF1234567890ABCDEF1234567890ABCD",
            wallet_age_days=365,
            total_transactions=500,
            total_volume_algo=Decimal('25000'),
            governance_participation_count=2,
            defi_protocols_used=['tinyman', 'algofi']
        )

    @pytest.fixture
    def sample_market_conditions(self):
        """Create sample market conditions."""
        return MarketConditions(
            volatility_index=0.25,
            liquidity_ratio=0.8,
            correlation_factor=0.3,
            market_stress_indicator=0.2
        )

    @pytest.mark.asyncio
    async def test_assess_borrower_risk_complete(
        self, engine, sample_credit_profile, sample_wallet_profile, sample_market_conditions
    ):
        """Test complete borrower risk assessment."""
        assessment = await engine.assess_borrower_risk(
            borrower_id="test_borrower_001",
            credit_profile=sample_credit_profile,
            wallet_profile=sample_wallet_profile,
            market_conditions=sample_market_conditions
        )

        assert isinstance(assessment, RiskAssessment)
        assert assessment.borrower_id == "test_borrower_001"
        assert 0.0 <= assessment.credit_score_component <= 1.0
        assert 0.0 <= assessment.onchain_behavior_component <= 1.0
        assert 0.0 <= assessment.final_risk_score <= 1.0
        assert assessment.risk_category in ["excellent", "good", "fair", "poor", "high_risk"]
        assert assessment.risk_premium_rate >= Decimal('0')
        assert assessment.recommended_interest_rate >= Decimal('0')

    @pytest.mark.asyncio
    async def test_assess_borrower_risk_minimal_data(self, engine):
        """Test risk assessment with minimal data."""
        assessment = await engine.assess_borrower_risk(
            borrower_id="test_borrower_002"
        )

        assert isinstance(assessment, RiskAssessment)
        assert assessment.borrower_id == "test_borrower_002"
        # Should use conservative defaults
        assert assessment.credit_score_component == 0.3
        assert assessment.onchain_behavior_component == 0.2

    @pytest.mark.asyncio
    async def test_assess_borrower_risk_credit_only(self, engine, sample_credit_profile):
        """Test risk assessment with credit profile only."""
        assessment = await engine.assess_borrower_risk(
            borrower_id="test_borrower_003",
            credit_profile=sample_credit_profile
        )

        assert isinstance(assessment, RiskAssessment)
        assert assessment.credit_score_component > 0.3  # Better than default
        assert assessment.onchain_behavior_component == 0.2  # Default

    def test_calculate_final_risk_score(self, engine):
        """Test final risk score calculation."""
        component_scores = {
            'credit': 0.8,
            'onchain': 0.7,
            'cross_chain': 0.1,
            'market_adjustment': 1.0
        }

        final_score = engine._calculate_final_risk_score(component_scores)
        assert 0.0 <= final_score <= 1.0

    def test_determine_risk_category(self, engine):
        """Test risk category determination."""
        # Excellent category
        category1 = engine._determine_risk_category(0.85, 0.85)
        assert category1 == "excellent"

        # Good category
        category2 = engine._determine_risk_category(0.7, 0.7)
        assert category2 == "good"

        # Fair category
        category3 = engine._determine_risk_category(0.5, 0.5)
        assert category3 == "fair"

        # Poor category
        category4 = engine._determine_risk_category(0.3, 0.3)
        assert category4 == "poor"

        # High risk category
        category5 = engine._determine_risk_category(0.1, 0.1)
        assert category5 == "high_risk"

    def test_calculate_risk_premium(self, engine):
        """Test risk premium calculation."""
        component_scores = {
            'credit': 0.8,
            'onchain': 0.7,
            'cross_chain': 0.0,
            'market_adjustment': 1.0
        }

        # Excellent category
        premium1 = engine._calculate_risk_premium("excellent", component_scores)
        assert premium1 >= Decimal('0.001')

        # High risk category
        premium2 = engine._calculate_risk_premium("high_risk", component_scores)
        assert premium2 > premium1

    def test_calculate_confidence_score(self, engine, sample_credit_profile, sample_wallet_profile):
        """Test confidence score calculation."""
        # Both profiles provided
        confidence1 = engine._calculate_confidence_score(sample_credit_profile, sample_wallet_profile)
        assert 0.7 <= confidence1 <= 1.0

        # Only credit profile
        confidence2 = engine._calculate_confidence_score(sample_credit_profile, None)
        assert confidence2 < confidence1

        # No profiles
        confidence3 = engine._calculate_confidence_score(None, None)
        assert confidence3 == 0.0

    def test_generate_assessment_report(self, engine):
        """Test assessment report generation."""
        # Create mock assessment
        assessment = RiskAssessment(
            borrower_id="test_001",
            assessment_timestamp=datetime.utcnow(),
            credit_score_component=0.8,
            onchain_behavior_component=0.7,
            cross_chain_component=0.1,
            market_adjustment_component=1.0,
            final_risk_score=0.75,
            risk_category="good",
            risk_premium_rate=Decimal('0.015'),
            recommended_interest_rate=Decimal('0.035'),
            confidence_score=0.85
        )

        report = engine.generate_assessment_report(assessment)

        assert "RISK ASSESSMENT REPORT" in report
        assert "test_001" in report
        assert "good" in report.upper()
        assert "1.50%" in report  # Risk premium
        assert "3.50%" in report  # Recommended rate


class TestMarketConditions:
    """Test MarketConditions data class."""

    def test_market_conditions_creation(self):
        """Test creation of market conditions."""
        conditions = MarketConditions(
            volatility_index=0.35,
            liquidity_ratio=0.75,
            correlation_factor=0.45,
            market_stress_indicator=0.15,
            algo_price_volatility=0.4
        )

        assert conditions.volatility_index == 0.35
        assert conditions.liquidity_ratio == 0.75
        assert conditions.correlation_factor == 0.45
        assert conditions.market_stress_indicator == 0.15
        assert conditions.algo_price_volatility == 0.4


class TestIntegration:
    """Integration tests for the complete risk assessment system."""

    @pytest.fixture
    def complete_engine(self):
        """Create engine with custom configuration."""
        config = RiskPremiumConfig()
        config.risk_thresholds.min_wallet_age_days = 60
        config.risk_thresholds.min_transaction_count = 5
        return RiskPremiumEngine(config)

    @pytest.mark.asyncio
    async def test_end_to_end_assessment(self, complete_engine):
        """Test complete end-to-end risk assessment."""
        # Create comprehensive profiles
        credit_profile = CreditProfile(
            credit_score=720,
            credit_age_months=36,
            credit_utilization=0.3,
            payment_history_score=0.88,
            credit_mix_score=0.75,
            new_credit_score=0.8,
            debt_to_income_ratio=0.42
        )

        wallet_profile = AlgorandWalletProfile(
            wallet_address="INTEGRATION_TEST_WALLET_ADDRESS_1234567890ABCDEF12",
            wallet_age_days=450,
            total_transactions=750,
            total_volume_algo=Decimal('75000'),
            average_balance_algo=Decimal('3500'),
            governance_participation_count=3,
            governance_commitment_algo=Decimal('8000'),
            staking_periods=6,
            staking_rewards_algo=Decimal('350'),
            defi_protocols_used=['tinyman', 'algofi'],
            smart_contracts_interacted=25,
            asa_tokens_created=1
        )

        market_conditions = MarketConditions(
            volatility_index=0.28,
            liquidity_ratio=0.85,
            correlation_factor=0.35,
            market_stress_indicator=0.18,
            algo_price_volatility=0.32
        )

        # Run assessment
        assessment = await complete_engine.assess_borrower_risk(
            borrower_id="integration_test_001",
            credit_profile=credit_profile,
            wallet_profile=wallet_profile,
            market_conditions=market_conditions
        )

        # Verify comprehensive assessment
        assert assessment.borrower_id == "integration_test_001"
        assert assessment.credit_score_component > 0.5  # Decent credit
        assert assessment.onchain_behavior_component > 0.4  # Good on-chain behavior
        assert assessment.risk_category in ["excellent", "good", "fair"]
        assert assessment.confidence_score > 0.7  # High confidence with complete data

        # Generate and verify report
        report = complete_engine.generate_assessment_report(assessment)
        assert len(report) > 500  # Substantial report
        assert "integration_test_001" in report

    @pytest.mark.asyncio
    async def test_stress_scenario_assessment(self, complete_engine):
        """Test assessment under stress conditions."""
        # Create stressed market conditions
        stressed_conditions = MarketConditions(
            volatility_index=0.65,  # High volatility
            liquidity_ratio=0.3,    # Low liquidity
            correlation_factor=0.8,  # High correlation
            market_stress_indicator=0.7,  # High stress
            algo_price_volatility=0.8
        )

        # Basic profiles
        credit_profile = CreditProfile(credit_score=650)
        wallet_profile = AlgorandWalletProfile(
            wallet_address="STRESS_TEST_WALLET_1234567890ABCDEF1234567890ABCD",
            wallet_age_days=120,
            total_transactions=25
        )

        assessment = await complete_engine.assess_borrower_risk(
            borrower_id="stress_test_001",
            credit_profile=credit_profile,
            wallet_profile=wallet_profile,
            market_conditions=stressed_conditions
        )

        # Verify stress conditions increase risk premium
        assert assessment.market_adjustment_component > 1.5
        assert assessment.risk_premium_rate > Decimal('0.03')  # Higher premium under stress


if __name__ == "__main__":
    pytest.main([__file__, "-v"])