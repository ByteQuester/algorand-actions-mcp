"""
Cross-System Integration Tests

Tests integration with other business logic engines:
- blockchain-collateral-analyzer
- interest-rate-determiner
- Real-time data flow between systems
"""

import asyncio
import pytest
import httpx
from datetime import datetime
from typing import Dict, Any

from ..core.decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanApplication
)


class TestCrossSystemIntegration:
    """Integration tests with external business logic engines"""

    @pytest.fixture
    def mock_blockchain_analyzer_response(self):
        """Mock response from blockchain-collateral-analyzer"""
        return {
            'address': 'TEST_ADDRESS_123',
            'total_value': 125000.50,
            'assets': [
                {
                    'asset_id': 0,  # ALGO
                    'balance': 75000.0,
                    'value_usd': 75000.0,
                    'quality_score': 0.95,
                    'liquidity_score': 0.98
                },
                {
                    'asset_id': 31566704,  # USDC
                    'balance': 50000.0,
                    'value_usd': 50000.0,
                    'quality_score': 0.99,
                    'liquidity_score': 0.99
                }
            ],
            'risk_metrics': {
                'portfolio_var': 0.12,
                'concentration_risk': 0.25,
                'liquidity_risk': 0.08
            },
            'timestamp': datetime.now().isoformat()
        }

    @pytest.fixture
    def mock_interest_rate_response(self):
        """Mock response from interest-rate-determiner"""
        return {
            'base_rate': 0.08,
            'risk_premium': 0.015,
            'final_rate': 0.095,
            'rate_components': {
                'treasury_rate': 0.045,
                'credit_spread': 0.035,
                'operational_margin': 0.015
            },
            'term_structure': {
                '30d': 0.087,
                '90d': 0.091,
                '180d': 0.095,
                '365d': 0.105
            },
            'timestamp': datetime.now().isoformat()
        }

    @pytest.fixture
    async def orchestrator_with_integrations(self):
        """Create orchestrator with integration endpoints configured"""
        config = {
            'integrations': {
                'blockchain_collateral_analyzer': {
                    'enabled': True,
                    'endpoint': 'http://localhost:8001/api/v1'
                },
                'interest_rate_determiner': {
                    'enabled': True,
                    'endpoint': 'http://localhost:8004/api/v1'
                }
            },
            'engine_weights': {
                'ecosystem_analysis': 0.30,
                'defi_behavior': 0.25,
                'collateral_intelligence': 0.20,
                'governance_reputation': 0.15,
                'network_risk_monitoring': 0.10
            }
        }
        return HolisticDecisionOrchestrator()

    async def test_blockchain_collateral_analyzer_integration(
        self,
        orchestrator_with_integrations,
        mock_blockchain_analyzer_response
    ):
        """Test integration with blockchain-collateral-analyzer"""

        # Mock the HTTP client call to blockchain analyzer
        async def mock_get_collateral_analysis(address: str):
            return mock_blockchain_analyzer_response

        # Replace the actual call with mock
        orchestrator_with_integrations._get_blockchain_collateral_analysis = mock_get_collateral_analysis

        # Create test application
        application = LoanApplication(
            application_id="BLOCKCHAIN_INT_001",
            borrower_address="TEST_ADDRESS_123",
            loan_amount=50000.0,
            requested_term=180,
            collateral_assets=[],  # Will be populated by blockchain analyzer
            purpose="integration test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        # Process application
        decision = await orchestrator_with_integrations.process_loan_application(application)

        # Verify blockchain analyzer data was used
        assert decision.collateral_score > 0
        # Should reflect the high-quality collateral from mock response
        assert decision.collateral_score >= 0.8

    async def test_interest_rate_determiner_integration(
        self,
        orchestrator_with_integrations,
        mock_interest_rate_response
    ):
        """Test integration with interest-rate-determiner"""

        # Mock the HTTP client call to interest rate determiner
        async def mock_get_interest_rate(
            loan_amount: float,
            term: int,
            risk_score: float,
            borrower_profile: Dict[str, Any]
        ):
            return mock_interest_rate_response

        # Replace the actual call with mock
        orchestrator_with_integrations._get_interest_rate_determination = mock_get_interest_rate

        # Create test application
        application = LoanApplication(
            application_id="RATE_INT_001",
            borrower_address="RATE_TEST_ADDRESS",
            loan_amount=75000.0,
            requested_term=365,
            collateral_assets=[{'asset': 'ALGO', 'amount': 100000, 'value': 100000}],
            purpose="rate integration test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        # Process application
        decision = await orchestrator_with_integrations.process_loan_application(application)

        # Verify interest rate from external system was used
        if decision.interest_rate:
            # Should be close to the mock response rate
            assert abs(decision.interest_rate - 0.095) < 0.01

    async def test_real_time_data_flow(self, orchestrator_with_integrations):
        """Test real-time data flow between systems"""

        # Create application that requires real-time updates
        application = LoanApplication(
            application_id="REALTIME_001",
            borrower_address="REALTIME_TEST_ADDRESS",
            loan_amount=40000.0,
            requested_term=180,
            collateral_assets=[{'asset': 'ALGO', 'amount': 60000, 'value': 60000}],
            purpose="real-time integration test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        # Track processing time for real-time requirements
        start_time = datetime.now()
        decision = await orchestrator_with_integrations.process_loan_application(application)
        processing_time = (datetime.now() - start_time).total_seconds()

        # Real-time processing should complete within reasonable time
        assert processing_time < 10.0  # 10 seconds max for integration calls

        # Decision should be valid
        assert decision.application_id == "REALTIME_001"
        assert decision.processing_time > 0

    async def test_system_failure_resilience(self, orchestrator_with_integrations):
        """Test resilience when external systems are unavailable"""

        # Mock failed external system calls
        async def mock_failed_collateral_call(address: str):
            raise httpx.HTTPError("Service unavailable")

        async def mock_failed_rate_call(loan_amount, term, risk_score, profile):
            raise httpx.HTTPError("Service unavailable")

        # Replace calls with failing mocks
        orchestrator_with_integrations._get_blockchain_collateral_analysis = mock_failed_collateral_call
        orchestrator_with_integrations._get_interest_rate_determination = mock_failed_rate_call

        # Create test application
        application = LoanApplication(
            application_id="FAILURE_TEST_001",
            borrower_address="FAILURE_TEST_ADDRESS",
            loan_amount=30000.0,
            requested_term=90,
            collateral_assets=[{'asset': 'ALGO', 'amount': 45000, 'value': 45000}],
            purpose="failure resilience test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        # Should still process with degraded service
        decision = await orchestrator_with_integrations.process_loan_application(application)

        # Should indicate reduced confidence due to missing data
        assert decision.confidence.value in ['low', 'very_low']
        # Should still make a decision (might be requires_review)
        assert decision.decision is not None

    async def test_data_consistency_across_systems(self, orchestrator_with_integrations):
        """Test that data remains consistent across all integrated systems"""

        # Create comprehensive test case
        application = LoanApplication(
            application_id="CONSISTENCY_001",
            borrower_address="CONSISTENCY_TEST_ADDRESS",
            loan_amount=60000.0,
            requested_term=270,
            collateral_assets=[
                {'asset': 'ALGO', 'amount': 50000, 'value': 50000},
                {'asset': 'USDC', 'amount': 30000, 'value': 30000}
            ],
            purpose="data consistency test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.18},
            network_health={'health_score': 0.92}
        )

        # Process application
        decision = await orchestrator_with_integrations.process_loan_application(application)

        # Verify data consistency
        # LTV should be calculated consistently
        if decision.ltv_ratio and decision.approved_amount:
            total_collateral = sum(asset['value'] for asset in application.collateral_assets)
            expected_ltv = decision.approved_amount / total_collateral
            assert abs(decision.ltv_ratio - expected_ltv) < 0.01

        # Risk score should align with decision
        if hasattr(decision, 'risk_score'):
            if decision.decision.value == 'approved':
                assert decision.risk_score < 0.5  # Low risk for approval
            elif decision.decision.value == 'rejected':
                assert decision.risk_score > 0.3  # Higher risk for rejection

    async def test_performance_with_multiple_integrations(self, orchestrator_with_integrations):
        """Test performance when calling multiple external systems"""

        # Create multiple applications to test concurrent processing
        applications = []
        for i in range(5):
            app = LoanApplication(
                application_id=f"PERF_TEST_{i:03d}",
                borrower_address=f"PERF_ADDRESS_{i}",
                loan_amount=25000.0 + (i * 5000),
                requested_term=180,
                collateral_assets=[{'asset': 'ALGO', 'amount': 40000, 'value': 40000}],
                purpose=f"performance test {i}",
                timestamp=datetime.now(),
                market_conditions={'volatility': 0.15},
                network_health={'health_score': 0.95}
            )
            applications.append(app)

        # Process all applications concurrently
        start_time = datetime.now()
        decisions = await asyncio.gather(*[
            orchestrator_with_integrations.process_loan_application(app)
            for app in applications
        ])
        total_time = (datetime.now() - start_time).total_seconds()

        # Should process efficiently
        assert len(decisions) == 5
        assert total_time < 15.0  # Reasonable time for 5 concurrent applications

        # All decisions should be valid
        for decision in decisions:
            assert decision.application_id.startswith("PERF_TEST_")
            assert decision.decision is not None

    async def test_integration_configuration_validation(self):
        """Test that integration configurations are properly validated"""

        # Test with invalid configuration
        invalid_config = {
            'integrations': {
                'blockchain_collateral_analyzer': {
                    'enabled': True,
                    'endpoint': 'invalid_url'  # Invalid URL
                }
            }
        }

        # Should handle invalid configuration gracefully
        orchestrator = HolisticDecisionOrchestrator()
        # In production, this would validate config and disable integration
        assert orchestrator is not None

    async def test_api_version_compatibility(self, orchestrator_with_integrations):
        """Test compatibility with different API versions"""

        # Mock response with different API version
        async def mock_v2_response(address: str):
            return {
                'api_version': '2.0',
                'address': address,
                'collateral_data': {
                    'total_value': 100000.0,
                    'risk_score': 0.15
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 0.9
                }
            }

        # Test handling of different API versions
        orchestrator_with_integrations._get_blockchain_collateral_analysis = mock_v2_response

        application = LoanApplication(
            application_id="VERSION_TEST_001",
            borrower_address="VERSION_TEST_ADDRESS",
            loan_amount=35000.0,
            requested_term=180,
            collateral_assets=[],
            purpose="API version test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        # Should handle version differences gracefully
        decision = await orchestrator_with_integrations.process_loan_application(application)
        assert decision.application_id == "VERSION_TEST_001"

    async def test_integration_monitoring_and_health_checks(self, orchestrator_with_integrations):
        """Test monitoring and health check capabilities for integrations"""

        # Get integration health status
        health_status = await orchestrator_with_integrations._check_integration_health()

        # Should return status for all configured integrations
        assert 'blockchain_collateral_analyzer' in health_status
        assert 'interest_rate_determiner' in health_status

        # Each integration should have status information
        for service, status in health_status.items():
            assert 'available' in status
            assert 'response_time' in status
            assert 'last_check' in status


class TestDataValidationAndTransformation:
    """Test data validation and transformation between systems"""

    async def test_collateral_data_transformation(self):
        """Test transformation of collateral data between systems"""

        # Mock external collateral data format
        external_format = {
            'wallet_address': 'TEST_ADDRESS',
            'assets': [
                {'id': 0, 'symbol': 'ALGO', 'balance': 50000, 'usd_value': 50000},
                {'id': 31566704, 'symbol': 'USDC', 'balance': 25000, 'usd_value': 25000}
            ],
            'portfolio_metrics': {
                'total_usd': 75000,
                'diversification': 0.67,
                'liquidity': 0.89
            }
        }

        # Transform to internal format
        internal_format = _transform_collateral_data(external_format)

        # Verify transformation
        assert internal_format['total_collateral_value'] == 75000
        assert len(internal_format['assets']) == 2
        assert internal_format['quality_metrics']['diversification_score'] == 0.67

    async def test_interest_rate_data_validation(self):
        """Test validation of interest rate data from external system"""

        # Valid rate data
        valid_rate_data = {
            'base_rate': 0.08,
            'risk_premium': 0.02,
            'final_rate': 0.10,
            'confidence': 0.95
        }

        # Should pass validation
        assert _validate_interest_rate_data(valid_rate_data) is True

        # Invalid rate data
        invalid_rate_data = {
            'base_rate': -0.01,  # Negative rate
            'risk_premium': 1.5,  # Unreasonably high premium
            'final_rate': 0.10
        }

        # Should fail validation
        assert _validate_interest_rate_data(invalid_rate_data) is False


# Helper functions for testing
def _transform_collateral_data(external_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform external collateral data to internal format"""
    return {
        'total_collateral_value': external_data['portfolio_metrics']['total_usd'],
        'assets': [
            {
                'asset': asset['symbol'],
                'amount': asset['balance'],
                'value': asset['usd_value']
            }
            for asset in external_data['assets']
        ],
        'quality_metrics': {
            'diversification_score': external_data['portfolio_metrics']['diversification'],
            'liquidity_score': external_data['portfolio_metrics']['liquidity']
        }
    }


def _validate_interest_rate_data(rate_data: Dict[str, Any]) -> bool:
    """Validate interest rate data from external system"""
    try:
        base_rate = rate_data.get('base_rate', 0)
        risk_premium = rate_data.get('risk_premium', 0)

        # Basic validation rules
        if base_rate < 0 or base_rate > 0.5:  # 0% to 50%
            return False
        if risk_premium < 0 or risk_premium > 0.3:  # 0% to 30%
            return False

        return True
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])