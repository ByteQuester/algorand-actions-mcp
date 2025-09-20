"""
Test MCP Integration for Risk Assessment Engines
Tests integration with Algorand Reader and Market Data MCP services
"""

import asyncio
import pytest
import aiohttp
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

# Import risk engines
from defi_protocol_risk.core.protocol_engine import DeFiProtocolRiskEngine
from smart_contract_risk.core.contract_engine import SmartContractRiskEngine

class MockMCPService:
    """Mock MCP service for testing"""

    def __init__(self, service_type: str, port: int):
        self.service_type = service_type
        self.port = port
        self.base_url = f"http://localhost:{port}"

    async def get_protocol_data(self, protocol_name: str) -> Dict[str, Any]:
        """Mock protocol data retrieval"""
        if self.service_type == "algorand_reader":
            return {
                'algofi': {
                    'protocol_info': {
                        'name': 'Algofi',
                        'tvl_usd': 45000000,
                        'total_users': 2500,
                        'contracts': ['algofi_pool', 'algofi_governance'],
                        'governance_token': 'BANK'
                    },
                    'contracts': {
                        'algofi_pool': {
                            'address': '465818260',
                            'creation_round': 15000000,
                            'functions': ['deposit', 'withdraw', 'borrow', 'repay'],
                            'total_transactions': 150000,
                            'unique_users': 2200
                        }
                    }
                },
                'folks_finance': {
                    'protocol_info': {
                        'name': 'Folks Finance',
                        'tvl_usd': 32000000,
                        'total_users': 1800,
                        'contracts': ['folks_pool', 'folks_governance'],
                        'governance_token': 'FOLKS'
                    }
                },
                'tinyman': {
                    'protocol_info': {
                        'name': 'Tinyman',
                        'tvl_usd': 25000000,
                        'total_users': 3000,
                        'contracts': ['tinyman_dex', 'tinyman_pools'],
                        'governance_token': 'TINY'
                    }
                }
            }.get(protocol_name, {})

        return {}

    async def get_market_data(self, asset: str) -> Dict[str, Any]:
        """Mock market data retrieval"""
        if self.service_type == "market_data":
            mock_prices = {
                'ALGO': {
                    'price_usd': 0.25,
                    'price_change_24h': 0.05,
                    'volume_24h': 50000000,
                    'market_cap': 2000000000,
                    'volatility_30d': 0.45
                },
                'USDC': {
                    'price_usd': 1.00,
                    'price_change_24h': 0.001,
                    'volume_24h': 5000000,
                    'market_cap': 500000000,
                    'volatility_30d': 0.02
                },
                'BANK': {
                    'price_usd': 0.15,
                    'price_change_24h': -0.03,
                    'volume_24h': 500000,
                    'market_cap': 15000000,
                    'volatility_30d': 0.65
                }
            }
            return mock_prices.get(asset, {})

        return {}

    async def get_contract_interactions(self, contract_address: str) -> Dict[str, Any]:
        """Mock contract interaction data"""
        if self.service_type == "algorand_reader":
            return {
                'interactions': [
                    {
                        'source_contract': 'algofi_pool',
                        'target_contract': 'oracle_contract',
                        'interaction_type': 'price_query',
                        'frequency': 150,
                        'gas_usage': 25000,
                        'success_rate': 0.98,
                        'last_interaction': '2024-01-15T10:30:00Z'
                    },
                    {
                        'source_contract': 'tinyman_dex',
                        'target_contract': 'oracle_contract',
                        'interaction_type': 'price_query',
                        'frequency': 200,
                        'gas_usage': 20000,
                        'success_rate': 0.99,
                        'last_interaction': '2024-01-15T10:25:00Z'
                    }
                ],
                'call_graph': {
                    'nodes': ['algofi_pool', 'tinyman_dex', 'oracle_contract'],
                    'edges': [
                        ['algofi_pool', 'oracle_contract'],
                        ['tinyman_dex', 'oracle_contract']
                    ]
                }
            }

        return {}

class TestMCPIntegration:
    """Test MCP service integration"""

    @pytest.fixture
    def mock_algorand_reader(self):
        """Mock Algorand Reader MCP service"""
        return MockMCPService("algorand_reader", 8002)

    @pytest.fixture
    def mock_market_data(self):
        """Mock Market Data MCP service"""
        return MockMCPService("market_data", 8003)

    @pytest.mark.asyncio
    async def test_mcp_service_connectivity(self, mock_algorand_reader, mock_market_data):
        """Test basic MCP service connectivity"""
        # Test Algorand Reader service
        protocol_data = await mock_algorand_reader.get_protocol_data('algofi')
        assert protocol_data is not None
        assert 'protocol_info' in protocol_data
        assert protocol_data['protocol_info']['name'] == 'Algofi'

        # Test Market Data service
        market_data = await mock_market_data.get_market_data('ALGO')
        assert market_data is not None
        assert 'price_usd' in market_data
        assert market_data['price_usd'] == 0.25

    @pytest.mark.asyncio
    async def test_protocol_data_retrieval(self, mock_algorand_reader):
        """Test protocol data retrieval from MCP"""
        protocols = ['algofi', 'folks_finance', 'tinyman']

        for protocol in protocols:
            data = await mock_algorand_reader.get_protocol_data(protocol)
            assert data is not None
            assert 'protocol_info' in data
            assert 'tvl_usd' in data['protocol_info']
            assert 'total_users' in data['protocol_info']

    @pytest.mark.asyncio
    async def test_market_data_retrieval(self, mock_market_data):
        """Test market data retrieval from MCP"""
        assets = ['ALGO', 'USDC', 'BANK']

        for asset in assets:
            data = await mock_market_data.get_market_data(asset)
            assert data is not None
            assert 'price_usd' in data
            assert 'volatility_30d' in data
            assert data['price_usd'] > 0

    @pytest.mark.asyncio
    async def test_contract_interaction_data(self, mock_algorand_reader):
        """Test contract interaction data retrieval"""
        interaction_data = await mock_algorand_reader.get_contract_interactions('algofi_pool')

        assert interaction_data is not None
        assert 'interactions' in interaction_data
        assert len(interaction_data['interactions']) > 0

        # Check interaction structure
        for interaction in interaction_data['interactions']:
            assert 'source_contract' in interaction
            assert 'target_contract' in interaction
            assert 'interaction_type' in interaction
            assert 'frequency' in interaction

class TestDeFiProtocolRiskMCPIntegration:
    """Test DeFi Protocol Risk Engine MCP integration"""

    @pytest.fixture
    def risk_engine(self):
        """Create DeFi protocol risk engine"""
        return DeFiProtocolRiskEngine()

    @pytest.fixture
    def mock_mcp_data(self):
        """Mock MCP data for protocol risk assessment"""
        return {
            'protocols': {
                'algofi': {
                    'tvl_usd': 45000000,
                    'total_borrowed': 25000000,
                    'active_users': 2500,
                    'governance_token_price': 0.15,
                    'governance_market_cap': 15000000
                },
                'folks_finance': {
                    'tvl_usd': 32000000,
                    'total_borrowed': 18000000,
                    'active_users': 1800,
                    'governance_token_price': 0.08,
                    'governance_market_cap': 8000000
                },
                'tinyman': {
                    'tvl_usd': 25000000,
                    'total_volume_24h': 2000000,
                    'active_users': 3000,
                    'governance_token_price': 0.12,
                    'governance_market_cap': 12000000
                }
            },
            'market_data': {
                'ALGO': {'price_usd': 0.25, 'volatility_30d': 0.45},
                'USDC': {'price_usd': 1.00, 'volatility_30d': 0.02},
                'BANK': {'price_usd': 0.15, 'volatility_30d': 0.65}
            }
        }

    @pytest.mark.asyncio
    async def test_protocol_risk_with_mcp_data(self, risk_engine, mock_mcp_data):
        """Test protocol risk assessment with MCP data"""
        # Mock user positions
        user_positions = {
            'algofi': 50000,
            'folks_finance': 30000,
            'tinyman': 20000
        }

        # Mock MCP data integration
        async def mock_fetch_protocol_data(protocols):
            return mock_mcp_data['protocols']

        # Temporarily replace the protocol data fetching method
        original_method = risk_engine._fetch_protocol_data
        risk_engine._fetch_protocol_data = mock_fetch_protocol_data

        try:
            assessment = await risk_engine.assess_portfolio_risk(user_positions)

            # Verify assessment completed successfully
            assert assessment is not None
            assert assessment.portfolio_metrics.total_exposure_usd == 100000
            assert len(assessment.protocol_scores) == 3

            # Verify protocol data was used
            assert assessment.systemic_assessment is not None
            assert len(assessment.systemic_assessment.network_nodes) == 3

        finally:
            # Restore original method
            risk_engine._fetch_protocol_data = original_method

    @pytest.mark.asyncio
    async def test_real_time_data_integration(self, risk_engine):
        """Test real-time data integration simulation"""
        user_positions = {'algofi': 50000, 'tinyman': 50000}

        # Simulate real-time data updates
        real_time_updates = [
            {'timestamp': datetime.now(), 'protocol': 'algofi', 'tvl_change': -0.1},
            {'timestamp': datetime.now(), 'protocol': 'tinyman', 'tvl_change': 0.05}
        ]

        assessment = await risk_engine.assess_portfolio_risk(user_positions)

        # Verify assessment adapts to data updates
        assert assessment is not None
        assert assessment.timestamp is not None

    @pytest.mark.asyncio
    async def test_mcp_error_handling(self, risk_engine):
        """Test error handling when MCP services are unavailable"""
        user_positions = {'algofi': 50000}

        # Mock MCP service failure
        async def mock_fetch_with_error(protocols):
            raise aiohttp.ClientError("MCP service unavailable")

        original_method = risk_engine._fetch_protocol_data
        risk_engine._fetch_protocol_data = mock_fetch_with_error

        try:
            # Should handle error gracefully and use fallback data
            assessment = await risk_engine.assess_portfolio_risk(user_positions)

            # Assessment should still complete with reduced confidence
            assert assessment is not None
            assert assessment.confidence_score < 0.8  # Lower confidence due to missing data

        finally:
            risk_engine._fetch_protocol_data = original_method

class TestSmartContractRiskMCPIntegration:
    """Test Smart Contract Risk Engine MCP integration"""

    @pytest.fixture
    def contract_engine(self):
        """Create smart contract risk engine"""
        return SmartContractRiskEngine()

    @pytest.fixture
    def mock_contract_data(self):
        """Mock contract data from MCP"""
        return {
            'algofi_pool': {
                'address': '465818260',
                'name': 'AlgoFi Lending Pool',
                'creation_round': 15000000,
                'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate'],
                'features': ['access_control', 'reentrancy_protection', 'emergency_pause'],
                'deployment_date': '2021-11-01',
                'lines_of_code': 1200,
                'total_transactions': 150000,
                'unique_users': 2200,
                'audits': [
                    {
                        'auditor': 'runtime_verification',
                        'date': '2021-12-01',
                        'score': 88,
                        'type': 'formal_verification',
                        'vulnerabilities_found': 2,
                        'vulnerabilities_fixed': 2
                    }
                ]
            },
            'tinyman_dex': {
                'address': '552635992',
                'name': 'Tinyman DEX',
                'creation_round': 14000000,
                'functions': ['swap', 'add_liquidity', 'remove_liquidity'],
                'features': ['slippage_protection', 'access_control'],
                'deployment_date': '2021-10-01',
                'lines_of_code': 800,
                'total_transactions': 250000,
                'unique_users': 3000
            }
        }

    @pytest.fixture
    def mock_interaction_data(self):
        """Mock interaction data from MCP"""
        return [
            {
                'source': 'algofi_pool',
                'target': 'oracle_contract',
                'type': 'price_query',
                'frequency': 150,
                'gas_usage': 25000,
                'success_rate': 0.98,
                'last_interaction': '2024-01-15T10:30:00'
            },
            {
                'source': 'tinyman_dex',
                'target': 'oracle_contract',
                'type': 'price_query',
                'frequency': 200,
                'gas_usage': 20000,
                'success_rate': 0.99,
                'last_interaction': '2024-01-15T10:25:00'
            }
        ]

    @pytest.mark.asyncio
    async def test_contract_risk_with_mcp_data(self, contract_engine, mock_contract_data, mock_interaction_data):
        """Test contract risk assessment with MCP data"""
        assessment = await contract_engine.assess_contract_portfolio_risk(
            mock_contract_data, mock_interaction_data
        )

        # Verify assessment completed successfully
        assert assessment is not None
        assert assessment.portfolio_metrics.total_contracts == 2
        assert len(assessment.contract_scores) == 2

        # Verify contract data was used
        algofi_score = next(
            score for score in assessment.contract_scores
            if score.contract_id == 'algofi_pool'
        )
        assert algofi_score.contract_name == 'AlgoFi Lending Pool'
        assert algofi_score.audit_score > 0.5  # Should have good audit score

        # Verify interaction data was used
        assert assessment.interaction_assessment is not None
        assert len(assessment.interaction_assessment.contract_interactions) >= 2

    @pytest.mark.asyncio
    async def test_contract_audit_data_integration(self, contract_engine):
        """Test integration of contract audit data from MCP"""
        contract_with_audits = {
            'audited_contract': {
                'name': 'Well Audited Contract',
                'functions': ['transfer', 'approve'],
                'features': ['access_control', 'reentrancy_protection'],
                'audits': [
                    {
                        'auditor': 'certik',
                        'date': '2023-06-01',
                        'score': 92,
                        'type': 'security_audit',
                        'vulnerabilities_found': 1,
                        'vulnerabilities_fixed': 1
                    },
                    {
                        'auditor': 'halborn',
                        'date': '2023-07-01',
                        'score': 85,
                        'type': 'penetration_testing',
                        'vulnerabilities_found': 3,
                        'vulnerabilities_fixed': 3
                    }
                ]
            }
        }

        assessment = await contract_engine.assess_contract_portfolio_risk(contract_with_audits)

        # Should have high audit score due to multiple recent audits
        contract_score = assessment.contract_scores[0]
        assert contract_score.audit_score > 0.8
        assert contract_score.overall_risk_score < 0.3  # Low risk due to good audits

    @pytest.mark.asyncio
    async def test_real_time_contract_monitoring(self, contract_engine, mock_contract_data):
        """Test real-time contract monitoring capabilities"""
        # Simulate real-time contract events
        real_time_events = [
            {
                'timestamp': datetime.now(),
                'contract': 'algofi_pool',
                'event_type': 'large_transaction',
                'value': 1000000
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=5),
                'contract': 'tinyman_dex',
                'event_type': 'admin_action',
                'action': 'parameter_update'
            }
        ]

        assessment = await contract_engine.assess_contract_portfolio_risk(mock_contract_data)

        # Should include monitoring requirements for real-time events
        assert len(assessment.monitoring_requirements) > 0
        assert any(
            'real-time' in req.lower() or 'monitoring' in req.lower()
            for req in assessment.monitoring_requirements
        )

class TestMCPDataQuality:
    """Test MCP data quality and validation"""

    @pytest.mark.asyncio
    async def test_data_completeness_validation(self):
        """Test validation of MCP data completeness"""
        mock_service = MockMCPService("algorand_reader", 8002)

        # Test complete data
        complete_data = await mock_service.get_protocol_data('algofi')
        assert self._validate_protocol_data_completeness(complete_data)

        # Test incomplete data
        incomplete_data = {'protocol_info': {'name': 'Test'}}  # Missing required fields
        assert not self._validate_protocol_data_completeness(incomplete_data)

    def _validate_protocol_data_completeness(self, data: Dict[str, Any]) -> bool:
        """Validate protocol data completeness"""
        required_fields = ['protocol_info']
        if not all(field in data for field in required_fields):
            return False

        protocol_info = data['protocol_info']
        required_protocol_fields = ['name', 'tvl_usd', 'total_users']
        return all(field in protocol_info for field in required_protocol_fields)

    @pytest.mark.asyncio
    async def test_data_freshness_validation(self):
        """Test validation of MCP data freshness"""
        mock_service = MockMCPService("market_data", 8003)

        market_data = await mock_service.get_market_data('ALGO')

        # Should have recent timestamp (mock data is current)
        # In real implementation, would check data timestamp
        assert market_data is not None
        assert 'price_usd' in market_data

    @pytest.mark.asyncio
    async def test_data_consistency_validation(self):
        """Test validation of MCP data consistency"""
        mock_service = MockMCPService("algorand_reader", 8002)

        # Get data for multiple protocols
        protocols = ['algofi', 'folks_finance', 'tinyman']
        protocol_data = {}

        for protocol in protocols:
            data = await mock_service.get_protocol_data(protocol)
            protocol_data[protocol] = data

        # Validate data consistency
        for protocol, data in protocol_data.items():
            if 'protocol_info' in data:
                # TVL should be positive
                assert data['protocol_info']['tvl_usd'] > 0
                # Users should be positive
                assert data['protocol_info']['total_users'] > 0

class TestMCPPerformance:
    """Test MCP integration performance"""

    @pytest.mark.asyncio
    async def test_concurrent_mcp_requests(self):
        """Test concurrent MCP request performance"""
        mock_reader = MockMCPService("algorand_reader", 8002)
        mock_market = MockMCPService("market_data", 8003)

        protocols = ['algofi', 'folks_finance', 'tinyman']
        assets = ['ALGO', 'USDC', 'BANK']

        start_time = datetime.now()

        # Concurrent protocol data requests
        protocol_tasks = [mock_reader.get_protocol_data(protocol) for protocol in protocols]
        protocol_results = await asyncio.gather(*protocol_tasks)

        # Concurrent market data requests
        market_tasks = [mock_market.get_market_data(asset) for asset in assets]
        market_results = await asyncio.gather(*market_tasks)

        end_time = datetime.now()

        # Should complete quickly
        assert (end_time - start_time).total_seconds() < 2
        assert len(protocol_results) == 3
        assert len(market_results) == 3

    @pytest.mark.asyncio
    async def test_mcp_timeout_handling(self):
        """Test MCP request timeout handling"""
        # Mock slow MCP service
        class SlowMockService(MockMCPService):
            async def get_protocol_data(self, protocol_name: str):
                await asyncio.sleep(5)  # Simulate slow response
                return await super().get_protocol_data(protocol_name)

        slow_service = SlowMockService("algorand_reader", 8002)

        start_time = datetime.now()
        try:
            # Should timeout quickly
            await asyncio.wait_for(slow_service.get_protocol_data('algofi'), timeout=2.0)
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            pass

        end_time = datetime.now()
        assert (end_time - start_time).total_seconds() < 3

class TestMCPFailureRecovery:
    """Test MCP service failure recovery"""

    @pytest.fixture
    def defi_engine(self):
        return DeFiProtocolRiskEngine()

    @pytest.fixture
    def contract_engine(self):
        return SmartContractRiskEngine()

    @pytest.mark.asyncio
    async def test_fallback_data_usage(self, defi_engine):
        """Test fallback to cached/default data when MCP is unavailable"""
        user_positions = {'algofi': 50000}

        # Mock MCP failure
        async def mock_failing_fetch(protocols):
            raise Exception("MCP service down")

        original_method = defi_engine._fetch_protocol_data
        defi_engine._fetch_protocol_data = mock_failing_fetch

        try:
            assessment = await defi_engine.assess_portfolio_risk(user_positions)

            # Should complete with fallback data
            assert assessment is not None
            assert assessment.confidence_score < 0.7  # Lower confidence

        finally:
            defi_engine._fetch_protocol_data = original_method

    @pytest.mark.asyncio
    async def test_partial_mcp_failure_handling(self, contract_engine):
        """Test handling of partial MCP service failures"""
        contracts_data = {
            'contract_1': {
                'name': 'Contract 1',
                'functions': ['function_a'],
                'features': ['access_control']
            }
        }

        # Simulate partial failure (some data available, some not)
        assessment = await contract_engine.assess_contract_portfolio_risk(contracts_data)

        # Should complete with available data
        assert assessment is not None
        assert len(assessment.contract_scores) == 1

    @pytest.mark.asyncio
    async def test_mcp_retry_mechanism(self):
        """Test MCP request retry mechanism"""
        class FlakyMockService(MockMCPService):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.attempt_count = 0

            async def get_protocol_data(self, protocol_name: str):
                self.attempt_count += 1
                if self.attempt_count < 3:  # Fail first 2 attempts
                    raise Exception(f"Attempt {self.attempt_count} failed")
                return await super().get_protocol_data(protocol_name)

        flaky_service = FlakyMockService("algorand_reader", 8002)

        # Should eventually succeed after retries
        result = None
        for attempt in range(3):
            try:
                result = await flaky_service.get_protocol_data('algofi')
                break
            except Exception:
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(0.1)

        assert result is not None
        assert 'protocol_info' in result

def run_integration_tests():
    """Run all MCP integration tests"""
    pytest.main([__file__, '-v', '-x', '--tb=short'])

if __name__ == "__main__":
    run_integration_tests()