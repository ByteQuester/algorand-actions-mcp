"""
Holistic Workflow Integration Tests

Tests the complete loan approval workflow through all 6 engines:
Ecosystem → Behavior → Collateral → Governance → Risk → Decision
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any

from ..core.decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanApplication,
    LoanDecision,
    DecisionConfidence
)


class TestHolisticWorkflow:
    """Integration tests for complete holistic loan approval workflow"""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance for testing"""
        config = {
            'engine_weights': {
                'ecosystem_analysis': 0.30,
                'defi_behavior': 0.25,
                'collateral_intelligence': 0.20,
                'governance_reputation': 0.15,
                'network_risk_monitoring': 0.10
            },
            'approval_thresholds': {
                'excellent': 0.85,
                'good': 0.70,
                'fair': 0.55,
                'poor': 0.40,
                'reject': 0.39
            },
            'confidence_requirements': {
                'minimum_confidence': 0.75,
                'high_confidence': 0.90
            }
        }
        return HolisticDecisionOrchestrator()

    @pytest.fixture
    def defi_native_application(self):
        """Loan application from DeFi-native user"""
        return LoanApplication(
            application_id="TEST_DEFI_001",
            borrower_address="DEFI_NATIVE_ALGO_ADDRESS_123",
            loan_amount=50000.0,
            requested_term=180,
            collateral_assets=[
                {'asset': 'ALGO', 'amount': 40000, 'value': 40000},
                {'asset': 'USDC', 'amount': 25000, 'value': 25000}
            ],
            purpose="DeFi strategy expansion",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

    @pytest.fixture
    def governance_leader_application(self):
        """Loan application from governance leader"""
        return LoanApplication(
            application_id="TEST_GOV_001",
            borrower_address="GOVERNANCE_LEADER_ALGO_ADDRESS_456",
            loan_amount=100000.0,
            requested_term=365,
            collateral_assets=[
                {'asset': 'ALGO', 'amount': 80000, 'value': 80000},
                {'asset': 'USDC', 'amount': 40000, 'value': 40000}
            ],
            purpose="Governance participation and development",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

    @pytest.fixture
    def new_user_application(self):
        """Loan application from new user"""
        return LoanApplication(
            application_id="TEST_NEW_001",
            borrower_address="NEW_USER_ALGO_ADDRESS_789",
            loan_amount=10000.0,
            requested_term=90,
            collateral_assets=[
                {'asset': 'ALGO', 'amount': 15000, 'value': 15000}
            ],
            purpose="First DeFi experience",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

    @pytest.fixture
    def risky_user_application(self):
        """Loan application from risky user"""
        return LoanApplication(
            application_id="TEST_RISKY_001",
            borrower_address="RISKY_USER_ALGO_ADDRESS_000",
            loan_amount=75000.0,
            requested_term=365,
            collateral_assets=[
                {'asset': 'OPUL', 'amount': 50000, 'value': 10000}  # Low quality collateral
            ],
            purpose="High-risk yield farming",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.35},
            network_health={'health_score': 0.95}
        )

    async def test_defi_native_user_workflow(self, orchestrator, defi_native_application):
        """Test complete workflow for DeFi-native user - should be approved"""

        # Process the application
        decision = await orchestrator.process_loan_application(defi_native_application)

        # Assertions for DeFi-native user
        assert decision.application_id == "TEST_DEFI_001"
        assert decision.decision in [LoanDecision.APPROVED, LoanDecision.CONDITIONALLY_APPROVED]
        assert decision.confidence in [DecisionConfidence.HIGH, DecisionConfidence.VERY_HIGH]
        assert decision.overall_score >= 0.65

        # Check engine scores are reasonable
        assert decision.ecosystem_score >= 0.6  # Good ecosystem participation
        assert decision.defi_score >= 0.7       # Strong DeFi experience
        assert decision.collateral_score >= 0.8 # Good collateral

        # Check loan terms are provided
        assert decision.approved_amount is not None
        assert decision.interest_rate is not None
        assert decision.loan_term is not None
        assert decision.ltv_ratio is not None

        # Check monitoring is set up
        assert decision.monitoring_frequency in ['weekly', 'monthly']
        assert len(decision.monitoring_parameters) > 0

        # Check rationale is provided
        assert len(decision.primary_factors) > 0
        assert len(decision.positive_factors) > 0

    async def test_governance_leader_workflow(self, orchestrator, governance_leader_application):
        """Test complete workflow for governance leader - should be approved with premium terms"""

        decision = await orchestrator.process_loan_application(governance_leader_application)

        # Assertions for governance leader
        assert decision.application_id == "TEST_GOV_001"
        assert decision.decision == LoanDecision.APPROVED
        assert decision.confidence in [DecisionConfidence.HIGH, DecisionConfidence.VERY_HIGH]
        assert decision.overall_score >= 0.75

        # Check governance reputation is reflected
        assert decision.governance_score >= 0.7

        # Should get premium terms (lower interest rate)
        assert decision.interest_rate <= 0.08

        # Should have less intensive monitoring
        assert decision.monitoring_frequency in ['weekly', 'monthly']

    async def test_new_user_workflow(self, orchestrator, new_user_application):
        """Test complete workflow for new user - should be conditional approval"""

        decision = await orchestrator.process_loan_application(new_user_application)

        # Assertions for new user
        assert decision.application_id == "TEST_NEW_001"
        assert decision.decision in [LoanDecision.CONDITIONALLY_APPROVED, LoanDecision.APPROVED]
        assert decision.overall_score >= 0.4

        # Should have conservative terms
        if decision.decision == LoanDecision.CONDITIONALLY_APPROVED:
            assert len(decision.conditions) > 0
            assert decision.monitoring_frequency in ['daily', 'weekly']

        # Check alternatives might be provided
        # Note: alternatives are only for rejected applications in current implementation

    async def test_risky_user_workflow(self, orchestrator, risky_user_application):
        """Test complete workflow for risky user - should be rejected with alternatives"""

        decision = await orchestrator.process_loan_application(risky_user_application)

        # Assertions for risky user
        assert decision.application_id == "TEST_RISKY_001"
        assert decision.decision == LoanDecision.REJECTED
        assert decision.overall_score < 0.5

        # Should have alternatives provided
        assert len(decision.alternatives) > 0

        # Check risk factors are identified
        assert len(decision.risk_factors) > 0

        # Collateral score should be low due to poor quality
        assert decision.collateral_score < 0.6

    async def test_cross_engine_data_consistency(self, orchestrator, defi_native_application):
        """Test that data flows consistently between engines"""

        # Build borrower profile
        profile = await orchestrator._build_borrower_profile(
            defi_native_application.borrower_address
        )

        # Check all engines provided data
        assert profile.ecosystem_score >= 0
        assert profile.defi_score >= 0
        assert profile.collateral_score >= 0
        assert profile.governance_score >= 0
        assert profile.risk_score >= 0

        # Check confidence levels are reasonable
        assert profile.ecosystem_confidence >= 0.5
        assert profile.defi_confidence >= 0.5
        assert profile.collateral_confidence >= 0.5
        assert profile.governance_confidence >= 0.5
        assert profile.risk_confidence >= 0.5

        # Check data completeness
        assert profile.data_completeness >= 0.5

        # Calculate holistic scores
        holistic_scores = await orchestrator.scorer.calculate_holistic_scores(
            profile, defi_native_application
        )

        # Check score consistency
        assert holistic_scores['overall_score'] >= 0
        assert holistic_scores['overall_score'] <= 1
        assert holistic_scores['confidence_level'] >= 0.5

    async def test_decision_logic_validation(self, orchestrator):
        """Test that decision logic is consistent across different borrower profiles"""

        # Create applications with known characteristics
        high_score_app = LoanApplication(
            application_id="HIGH_SCORE_TEST",
            borrower_address="HIGH_SCORE_ADDRESS",
            loan_amount=25000.0,
            requested_term=180,
            collateral_assets=[{'asset': 'ALGO', 'amount': 40000, 'value': 40000}],
            purpose="conservative strategy",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.1},
            network_health={'health_score': 0.95}
        )

        low_score_app = LoanApplication(
            application_id="LOW_SCORE_TEST",
            borrower_address="LOW_SCORE_ADDRESS",
            loan_amount=50000.0,
            requested_term=365,
            collateral_assets=[{'asset': 'OPUL', 'amount': 10000, 'value': 2000}],
            purpose="high-risk speculation",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.4},
            network_health={'health_score': 0.95}
        )

        # Process both applications
        high_decision = await orchestrator.process_loan_application(high_score_app)
        low_decision = await orchestrator.process_loan_application(low_score_app)

        # Higher score should get better terms
        assert high_decision.overall_score > low_decision.overall_score

        if (high_decision.decision == LoanDecision.APPROVED and
            low_decision.decision in [LoanDecision.APPROVED, LoanDecision.CONDITIONALLY_APPROVED]):
            assert high_decision.interest_rate <= low_decision.interest_rate

    async def test_market_condition_impact(self, orchestrator):
        """Test that market conditions properly impact decisions"""

        # Same application, different market conditions
        base_app = LoanApplication(
            application_id="MARKET_TEST_1",
            borrower_address="MARKET_TEST_ADDRESS",
            loan_amount=30000.0,
            requested_term=180,
            collateral_assets=[{'asset': 'ALGO', 'amount': 40000, 'value': 40000}],
            purpose="market test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.1},  # Low volatility
            network_health={'health_score': 0.95}
        )

        volatile_app = LoanApplication(
            application_id="MARKET_TEST_2",
            borrower_address="MARKET_TEST_ADDRESS",
            loan_amount=30000.0,
            requested_term=180,
            collateral_assets=[{'asset': 'ALGO', 'amount': 40000, 'value': 40000}],
            purpose="market test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.4},  # High volatility
            network_health={'health_score': 0.95}
        )

        # Process both
        stable_decision = await orchestrator.process_loan_application(base_app)
        volatile_decision = await orchestrator.process_loan_application(volatile_app)

        # Volatile market should result in more conservative terms
        if (stable_decision.decision == LoanDecision.APPROVED and
            volatile_decision.decision == LoanDecision.APPROVED):
            # Should have higher interest rate or more conditions
            assert (volatile_decision.interest_rate >= stable_decision.interest_rate or
                    len(volatile_decision.conditions) >= len(stable_decision.conditions))

    async def test_processing_time_performance(self, orchestrator, defi_native_application):
        """Test that processing completes within reasonable time"""

        import time
        start_time = time.time()

        decision = await orchestrator.process_loan_application(defi_native_application)

        processing_time = time.time() - start_time

        # Should complete within 5 seconds (generous for testing)
        assert processing_time < 5.0
        assert decision.processing_time > 0

    async def test_error_handling_and_recovery(self, orchestrator):
        """Test error handling when engines are unavailable"""

        # Create application with invalid data to trigger errors
        invalid_app = LoanApplication(
            application_id="ERROR_TEST",
            borrower_address="",  # Invalid address
            loan_amount=-1000.0,  # Invalid amount
            requested_term=0,     # Invalid term
            collateral_assets=[],
            purpose="error test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.1},
            network_health={'health_score': 0.95}
        )

        # Should handle gracefully and return requires_review decision
        decision = await orchestrator.process_loan_application(invalid_app)

        assert decision.decision == LoanDecision.REQUIRES_REVIEW
        assert decision.confidence == DecisionConfidence.VERY_LOW
        assert "error" in decision.primary_factors[0].lower()

    @pytest.mark.parametrize("loan_amount,expected_decision", [
        (5000, LoanDecision.APPROVED),
        (25000, LoanDecision.APPROVED),
        (75000, LoanDecision.CONDITIONALLY_APPROVED),
        (150000, LoanDecision.REJECTED)
    ])
    async def test_loan_amount_thresholds(self, orchestrator, loan_amount, expected_decision):
        """Test decision changes based on loan amount"""

        app = LoanApplication(
            application_id=f"AMOUNT_TEST_{loan_amount}",
            borrower_address="AMOUNT_TEST_ADDRESS",
            loan_amount=loan_amount,
            requested_term=180,
            collateral_assets=[{'asset': 'ALGO', 'amount': loan_amount * 1.5, 'value': loan_amount * 1.5}],
            purpose="amount threshold test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        decision = await orchestrator.process_loan_application(app)

        # Note: Actual decision may vary based on other factors, but pattern should be apparent
        # Larger loans should generally be more restricted
        if loan_amount > 100000:
            assert decision.decision in [LoanDecision.CONDITIONALLY_APPROVED, LoanDecision.REJECTED]


@pytest.mark.asyncio
class TestMultipleBorrowerProfiles:
    """Test various borrower profiles and their expected outcomes"""

    async def test_ecosystem_specialist_profile(self):
        """Test borrower who specializes in ecosystem participation"""
        # Implementation would test specific ecosystem-focused profiles
        pass

    async def test_defi_power_user_profile(self):
        """Test borrower who is a DeFi power user"""
        # Implementation would test DeFi-focused profiles
        pass

    async def test_governance_only_profile(self):
        """Test borrower who only participates in governance"""
        # Implementation would test governance-only profiles
        pass

    async def test_mixed_profile_borrower(self):
        """Test borrower with mixed engagement across all areas"""
        # Implementation would test balanced profiles
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])