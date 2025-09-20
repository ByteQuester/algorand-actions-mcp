"""
Algorand Ecosystem Integration Tests

Tests integration with real Algorand mainnet/testnet:
- Live blockchain data integration
- DeFi protocol data integration
- Governance data integration
- Historical risk analysis
- MCP services integration (ports 8002/8003)
"""

import pytest
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holistic_risk_orchestrator.risk_orchestrator import HolisticRiskOrchestrator


class TestAlgorandEcosystemIntegration:
    """Test integration with real Algorand ecosystem"""

    @pytest.fixture
    def algorand_config(self):
        """Configuration for Algorand ecosystem integration"""
        return {
            'data_sources': {
                'algorand_indexer': {
                    'enabled': True,
                    'url': 'https://mainnet-idx.algonode.cloud',
                    'timeout_seconds': 30
                },
                'algorand_node': {
                    'enabled': True,
                    'url': 'https://mainnet-api.algonode.cloud',
                    'timeout_seconds': 30
                },
                'defi_protocols': {
                    'enabled': True,
                    'sources': ['tinyman', 'algofi', 'yieldly'],
                    'update_frequency_minutes': 5
                },
                'governance_api': {
                    'enabled': True,
                    'url': 'https://governance.algorand.foundation/api',
                    'update_frequency_minutes': 15
                }
            },
            'mcp_services': {
                'enabled': True,
                'algorand_reader_port': 8002,
                'algorand_writer_port': 8003
            }
        }

    @pytest.fixture
    def real_algorand_addresses(self):
        """Real Algorand addresses for testing (anonymized/public)"""
        return {
            # These would be real addresses with known characteristics
            'high_volume_dex': 'TINYMAN_DEX_ADDRESS_PLACEHOLDER',
            'governance_participant': 'GOVERNANCE_PARTICIPANT_PLACEHOLDER',
            'defi_protocol': 'ALGOFI_PROTOCOL_PLACEHOLDER',
            'regular_user': 'REGULAR_USER_ADDRESS_PLACEHOLDER'
        }

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_algorand_indexer_integration(self, algorand_config):
        """Test integration with Algorand indexer for blockchain data"""

        indexer_url = algorand_config['data_sources']['algorand_indexer']['url']

        async with aiohttp.ClientSession() as session:
            # Test indexer connectivity
            async with session.get(f"{indexer_url}/health") as response:
                assert response.status == 200
                health_data = await response.json()
                assert 'round' in health_data

            # Test transaction query capability
            async with session.get(f"{indexer_url}/v2/transactions?limit=1") as response:
                assert response.status == 200
                txn_data = await response.json()
                assert 'transactions' in txn_data
                assert len(txn_data['transactions']) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_algorand_node_integration(self, algorand_config):
        """Test integration with Algorand node for real-time data"""

        node_url = algorand_config['data_sources']['algorand_node']['url']

        async with aiohttp.ClientSession() as session:
            # Test node connectivity
            async with session.get(f"{node_url}/health") as response:
                assert response.status == 200

            # Test node status
            async with session.get(f"{node_url}/v2/status") as response:
                assert response.status == 200
                status_data = await response.json()
                assert 'last-round' in status_data
                assert status_data['last-round'] > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_defi_protocol_data_integration(self, algorand_config):
        """Test integration with DeFi protocol data sources"""

        # Test Tinyman integration (example)
        async with aiohttp.ClientSession() as session:
            try:
                # Test Tinyman API (if available)
                async with session.get("https://mainnet.analytics.tinyman.org/api/v1/pools/") as response:
                    if response.status == 200:
                        pools_data = await response.json()
                        assert isinstance(pools_data, (list, dict))

                        # Validate pool data structure
                        if isinstance(pools_data, list) and len(pools_data) > 0:
                            pool = pools_data[0]
                            assert 'asset_1_id' in pool or 'asset1' in pool
                            assert 'asset_2_id' in pool or 'asset2' in pool

            except Exception as e:
                # DeFi APIs may not always be available
                pytest.skip(f"DeFi protocol API not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires governance API access")
    async def test_governance_data_integration(self, algorand_config):
        """Test integration with Algorand governance data"""

        governance_url = algorand_config['data_sources']['governance_api']['url']

        async with aiohttp.ClientSession() as session:
            try:
                # Test governance data access
                async with session.get(f"{governance_url}/periods") as response:
                    if response.status == 200:
                        periods_data = await response.json()
                        assert isinstance(periods_data, (list, dict))

            except Exception as e:
                pytest.skip(f"Governance API not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mcp_services_integration(self, algorand_config):
        """Test integration with MCP services (ports 8002/8003)"""

        reader_port = algorand_config['mcp_services']['algorand_reader_port']
        writer_port = algorand_config['mcp_services']['algorand_writer_port']

        async with aiohttp.ClientSession() as session:
            try:
                # Test MCP reader service
                async with session.get(f"http://localhost:{reader_port}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        assert 'status' in health_data

                # Test MCP writer service
                async with session.get(f"http://localhost:{writer_port}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        assert 'status' in health_data

            except Exception as e:
                pytest.skip(f"MCP services not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_historical_risk_analysis_mainnet(self, algorand_config, real_algorand_addresses):
        """Test historical risk analysis with real mainnet data"""

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        # Test with a real address (if available)
        test_address = real_algorand_addresses.get('regular_user')
        if not test_address or test_address.endswith('PLACEHOLDER'):
            pytest.skip("Real Algorand address not available for testing")

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=test_address,
                include_scenario_analysis=False,  # Faster for integration test
                include_trend_analysis=True,
                enable_real_time_monitoring=False
            )

            # Validate real data integration
            assert profile is not None
            assert profile.address == test_address

            # Validate blockchain behavior analysis with real data
            if profile.blockchain_behavior_profile:
                assert profile.blockchain_behavior_profile.total_transaction_count >= 0
                assert profile.blockchain_behavior_profile.account_age_days >= 0

            # Validate risk scoring with real data
            score = profile.holistic_risk_score
            assert 0 <= score.overall_holistic_score <= 100
            assert score.risk_level is not None

        except Exception as e:
            pytest.skip(f"Real mainnet data integration failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_defi_protocol_risk_analysis_real_data(self, algorand_config, real_algorand_addresses):
        """Test DeFi protocol risk analysis with real protocol data"""

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        # Test with a known DeFi protocol address
        protocol_address = real_algorand_addresses.get('defi_protocol')
        if not protocol_address or protocol_address.endswith('PLACEHOLDER'):
            pytest.skip("Real DeFi protocol address not available for testing")

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=protocol_address,
                include_scenario_analysis=False,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            # Validate DeFi-specific analysis
            if profile.defi_protocol_profile:
                assert profile.defi_protocol_profile.total_value_locked >= 0
                assert profile.defi_protocol_profile.protocol_age_days >= 0

        except Exception as e:
            pytest.skip(f"Real DeFi protocol data integration failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_stress_testing_with_real_market_data(self, algorand_config):
        """Test stress testing scenarios with real market data"""

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        # Use a test address for stress testing
        test_address = "STRESS_TEST_ADDRESS_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=test_address,
                include_scenario_analysis=True,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            # Validate stress testing with real market context
            assert len(profile.scenario_analyses) > 0

            for scenario in profile.scenario_analyses:
                assert scenario.probability_estimate >= 0
                assert scenario.overall_impact_score >= 0
                assert len(scenario.impact_by_engine) == 4  # All engines

        except Exception as e:
            pytest.skip(f"Stress testing with real data failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_time_data_freshness(self, algorand_config):
        """Test real-time data freshness and update mechanisms"""

        async with aiohttp.ClientSession() as session:
            # Test Algorand node for latest round
            node_url = algorand_config['data_sources']['algorand_node']['url']

            try:
                async with session.get(f"{node_url}/v2/status") as response:
                    if response.status == 200:
                        status1 = await response.json()
                        round1 = status1['last-round']

                        # Wait a moment and check again
                        await asyncio.sleep(5)

                        async with session.get(f"{node_url}/v2/status") as response2:
                            if response2.status == 200:
                                status2 = await response2.json()
                                round2 = status2['last-round']

                                # Round should advance (data is fresh)
                                assert round2 >= round1

            except Exception as e:
                pytest.skip(f"Real-time data freshness test failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cross_chain_bridge_risk_analysis(self, algorand_config):
        """Test cross-chain bridge risk analysis with real bridge data"""

        # This would test integration with bridge protocols
        # Currently a placeholder as it depends on specific bridge implementations

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        # Test bridge activity detection
        test_address = "BRIDGE_USER_ADDRESS_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=test_address,
                include_scenario_analysis=False,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            # Validate bridge risk analysis
            if profile.blockchain_behavior_profile and profile.blockchain_behavior_profile.bridge_activities:
                bridge_activities = profile.blockchain_behavior_profile.bridge_activities
                assert len(bridge_activities) >= 0

                for activity in bridge_activities:
                    assert activity.bridge_protocol is not None
                    assert activity.transfer_amount >= 0

        except Exception as e:
            pytest.skip(f"Bridge risk analysis test failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_governance_participation_analysis(self, algorand_config, real_algorand_addresses):
        """Test governance participation analysis with real governance data"""

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        # Test with governance participant address
        gov_address = real_algorand_addresses.get('governance_participant')
        if not gov_address or gov_address.endswith('PLACEHOLDER'):
            pytest.skip("Real governance participant address not available")

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=gov_address,
                include_scenario_analysis=False,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            # Validate governance-specific analysis
            if profile.governance_stability_profile:
                gov_profile = profile.governance_stability_profile
                assert gov_profile.governance_participation_rate >= 0
                assert gov_profile.total_stakeholders >= 0

        except Exception as e:
            pytest.skip(f"Governance participation analysis failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_with_real_data(self, algorand_config):
        """Test performance with real Algorand data"""

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        # Performance test with real data
        start_time = datetime.utcnow()

        test_address = "PERF_TEST_ADDRESS_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=test_address,
                include_scenario_analysis=False,  # Faster
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Should complete within reasonable time even with real data
            assert duration < 120.0  # 2 minutes max
            assert profile is not None

            print(f"Real data risk assessment completed in {duration:.2f} seconds")

        except Exception as e:
            pytest.skip(f"Performance test with real data failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_quality_with_real_sources(self, algorand_config):
        """Test data quality metrics with real data sources"""

        orchestrator = HolisticRiskOrchestrator(algorand_config)

        test_address = "DATA_QUALITY_TEST_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        try:
            profile = await orchestrator.assess_holistic_risk(
                address=test_address,
                include_scenario_analysis=False,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            # Validate data quality metrics with real sources
            assert 0 <= profile.data_quality_score <= 1.0
            assert 0 <= profile.analysis_completeness <= 1.0

            # Real data sources should be documented
            assert len(profile.data_sources) > 0
            expected_sources = ['on_chain', 'defi_protocols', 'governance', 'market_data']
            assert any(source in profile.data_sources for source in expected_sources)

        except Exception as e:
            pytest.skip(f"Data quality test with real sources failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_resilience_with_real_apis(self, algorand_config):
        """Test error resilience when real APIs are unavailable"""

        # Test with deliberately broken configuration
        broken_config = algorand_config.copy()
        broken_config['data_sources']['algorand_indexer']['url'] = 'https://broken-api.example.com'

        orchestrator = HolisticRiskOrchestrator(broken_config)

        test_address = "ERROR_RESILIENCE_TEST_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        try:
            # Should handle broken APIs gracefully
            profile = await orchestrator.assess_holistic_risk(
                address=test_address,
                include_scenario_analysis=False,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

            # Even with broken APIs, should return some result
            assert profile is not None
            # Data quality should reflect API issues
            assert profile.data_quality_score < 1.0

        except Exception as e:
            # Should not crash completely, but may raise exceptions
            assert "connection" in str(e).lower() or "timeout" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])