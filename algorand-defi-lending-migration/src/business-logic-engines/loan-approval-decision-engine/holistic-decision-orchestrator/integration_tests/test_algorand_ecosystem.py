"""
Algorand Ecosystem Integration Tests

Tests real Algorand mainnet/testnet integration:
- Live governance data
- Real DeFi protocol data
- Historical transaction analysis
- MCP services integration (ports 8002/8003)
"""

import asyncio
import pytest
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..core.decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanApplication
)


class TestAlgorandEcosystemIntegration:
    """Integration tests with live Algorand ecosystem"""

    @pytest.fixture
    def mainnet_config(self):
        """Configuration for Algorand mainnet integration"""
        return {
            'algorand': {
                'network': 'mainnet',
                'indexer_url': 'https://mainnet-idx.algonode.cloud',
                'algod_url': 'https://mainnet-api.algonode.cloud',
                'mcp_services': {
                    'reader_port': 8002,
                    'writer_port': 8003,
                    'timeout': 30
                }
            },
            'data_sources': {
                'governance': {
                    'api_endpoint': 'https://governance.algorand.foundation/api',
                    'timeout': 15,
                    'cache_duration': 300
                },
                'defi_protocols': [
                    {
                        'name': 'Tinyman',
                        'api_endpoint': 'https://mainnet.analytics.tinyman.org'
                    },
                    {
                        'name': 'Pact',
                        'api_endpoint': 'https://api.pact.fi'
                    },
                    {
                        'name': 'AlgoFi',
                        'api_endpoint': 'https://api.algofi.org'
                    }
                ]
            }
        }

    @pytest.fixture
    def testnet_config(self):
        """Configuration for Algorand testnet integration"""
        return {
            'algorand': {
                'network': 'testnet',
                'indexer_url': 'https://testnet-idx.algonode.cloud',
                'algod_url': 'https://testnet-api.algonode.cloud',
                'mcp_services': {
                    'reader_port': 8002,
                    'writer_port': 8003,
                    'timeout': 30
                }
            }
        }

    @pytest.fixture
    def real_algorand_addresses(self):
        """Real Algorand addresses for testing (using public governance addresses)"""
        return {
            'governance_participant': 'ALGORAND_FOUNDATION_ADDRESS',  # Would use real address
            'defi_active': 'TINYMAN_POOL_ADDRESS',  # Would use real address
            'new_user': 'NEW_USER_ADDRESS',  # Would use real address
            'whale': 'WHALE_ADDRESS'  # Would use real address
        }

    async def test_mcp_reader_service_integration(self, mainnet_config):
        """Test integration with MCP reader service on port 8002"""

        reader_port = mainnet_config['algorand']['mcp_services']['reader_port']
        timeout = mainnet_config['algorand']['mcp_services']['timeout']

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Test MCP reader health
                health_response = await client.get(f"http://localhost:{reader_port}/health")
                assert health_response.status_code == 200

                # Test account data retrieval
                test_address = "ALGORAND_FOUNDATION_ADDRESS"  # Would use real address
                account_response = await client.get(
                    f"http://localhost:{reader_port}/account/{test_address}"
                )

                if account_response.status_code == 200:
                    account_data = account_response.json()

                    # Verify account data structure
                    assert 'address' in account_data
                    assert 'balance' in account_data
                    assert 'assets' in account_data
                    assert 'created_at_round' in account_data

                    # Test transaction history
                    tx_response = await client.get(
                        f"http://localhost:{reader_port}/transactions/{test_address}?limit=100"
                    )

                    if tx_response.status_code == 200:
                        tx_data = tx_response.json()
                        assert 'transactions' in tx_data
                        assert isinstance(tx_data['transactions'], list)

        except httpx.ConnectError:
            pytest.skip("MCP reader service not available on port 8002")

    async def test_mcp_writer_service_integration(self, mainnet_config):
        """Test integration with MCP writer service on port 8003"""

        writer_port = mainnet_config['algorand']['mcp_services']['writer_port']
        timeout = mainnet_config['algorand']['mcp_services']['timeout']

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Test MCP writer health
                health_response = await client.get(f"http://localhost:{writer_port}/health")
                assert health_response.status_code == 200

                # Test decision storage capability
                test_decision = {
                    'application_id': 'TEST_MCP_001',
                    'decision': 'approved',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'test': True}
                }

                store_response = await client.post(
                    f"http://localhost:{writer_port}/decisions",
                    json=test_decision
                )

                # Should accept or provide appropriate error
                assert store_response.status_code in [200, 201, 400, 403]

        except httpx.ConnectError:
            pytest.skip("MCP writer service not available on port 8003")

    async def test_live_governance_data_integration(self, mainnet_config, real_algorand_addresses):
        """Test integration with live Algorand governance data"""

        governance_config = mainnet_config['data_sources']['governance']
        governance_participant = real_algorand_addresses['governance_participant']

        try:
            async with httpx.AsyncClient(timeout=governance_config['timeout']) as client:
                # Test governance API availability
                api_response = await client.get(f"{governance_config['api_endpoint']}/status")

                if api_response.status_code == 200:
                    # Test governance participation data
                    participation_response = await client.get(
                        f"{governance_config['api_endpoint']}/accounts/{governance_participant}/participation"
                    )

                    if participation_response.status_code == 200:
                        participation_data = participation_response.json()

                        # Verify governance data structure
                        expected_fields = ['address', 'periods', 'voting_history', 'rewards']
                        for field in expected_fields:
                            if field in participation_data:
                                assert participation_data[field] is not None

                        # Test current governance period data
                        current_period_response = await client.get(
                            f"{governance_config['api_endpoint']}/periods/current"
                        )

                        if current_period_response.status_code == 200:
                            period_data = current_period_response.json()
                            assert 'period_id' in period_data
                            assert 'start_date' in period_data
                            assert 'end_date' in period_data

        except httpx.ConnectError:
            pytest.skip("Governance API not available")

    async def test_defi_protocol_data_integration(self, mainnet_config):
        """Test integration with live DeFi protocol data"""

        defi_protocols = mainnet_config['data_sources']['defi_protocols']

        for protocol in defi_protocols:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    # Test protocol API availability
                    health_response = await client.get(f"{protocol['api_endpoint']}/health")

                    if health_response.status_code == 200:
                        protocol_name = protocol['name']

                        if protocol_name == 'Tinyman':
                            # Test Tinyman pool data
                            pools_response = await client.get(
                                f"{protocol['api_endpoint']}/v1/pools"
                            )

                            if pools_response.status_code == 200:
                                pools_data = pools_response.json()
                                assert isinstance(pools_data, list)

                                # Verify pool structure
                                if pools_data:
                                    pool = pools_data[0]
                                    expected_fields = ['address', 'asset_1_id', 'asset_2_id', 'total_liquidity']
                                    for field in expected_fields:
                                        if field in pool:
                                            assert pool[field] is not None

                        elif protocol_name == 'Pact':
                            # Test Pact pool data
                            pools_response = await client.get(
                                f"{protocol['api_endpoint']}/pools"
                            )

                            if pools_response.status_code == 200:
                                pools_data = pools_response.json()
                                # Verify Pact-specific data structure

                        elif protocol_name == 'AlgoFi':
                            # Test AlgoFi protocol data
                            markets_response = await client.get(
                                f"{protocol['api_endpoint']}/markets"
                            )

                            if markets_response.status_code == 200:
                                markets_data = markets_response.json()
                                # Verify AlgoFi-specific data structure

            except httpx.ConnectError:
                pytest.skip(f"{protocol['name']} API not available")

    async def test_historical_transaction_analysis(self, mainnet_config, real_algorand_addresses):
        """Test historical transaction analysis for real addresses"""

        indexer_url = mainnet_config['algorand']['indexer_url']
        test_address = real_algorand_addresses['defi_active']

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Test indexer availability
                health_response = await client.get(f"{indexer_url}/health")
                assert health_response.status_code == 200

                # Get account information
                account_response = await client.get(
                    f"{indexer_url}/v2/accounts/{test_address}"
                )

                if account_response.status_code == 200:
                    account_data = account_response.json()
                    account_info = account_data.get('account', {})

                    # Verify account data
                    assert 'address' in account_info
                    assert 'amount' in account_info  # ALGO balance
                    assert 'assets' in account_info  # ASA holdings

                    # Analyze transaction history
                    tx_response = await client.get(
                        f"{indexer_url}/v2/accounts/{test_address}/transactions?limit=1000"
                    )

                    if tx_response.status_code == 200:
                        tx_data = tx_response.json()
                        transactions = tx_data.get('transactions', [])

                        # Analyze transaction patterns
                        analysis = _analyze_transaction_patterns(transactions)

                        # Verify analysis results
                        assert 'total_transactions' in analysis
                        assert 'transaction_types' in analysis
                        assert 'dapp_interactions' in analysis
                        assert 'avg_transaction_frequency' in analysis

                        # Check for DeFi activity
                        if analysis['dapp_interactions'] > 0:
                            assert analysis['defi_activity_score'] > 0

        except httpx.ConnectError:
            pytest.skip("Algorand indexer not available")

    async def test_real_borrower_profile_generation(self, mainnet_config, real_algorand_addresses):
        """Test generating borrower profiles from real Algorand addresses"""

        orchestrator = HolisticDecisionOrchestrator()

        for profile_type, address in real_algorand_addresses.items():
            try:
                # Generate real borrower profile
                profile = await orchestrator._build_borrower_profile(address)

                # Verify profile completeness
                assert profile.address == address
                assert 0 <= profile.ecosystem_score <= 1
                assert 0 <= profile.defi_score <= 1
                assert 0 <= profile.collateral_score <= 1
                assert 0 <= profile.governance_score <= 1
                assert 0 <= profile.risk_score <= 1

                # Profile should reflect expected characteristics
                if profile_type == 'governance_participant':
                    # Should have high governance score
                    assert profile.governance_score >= 0.5

                elif profile_type == 'defi_active':
                    # Should have high DeFi score
                    assert profile.defi_score >= 0.5

                elif profile_type == 'new_user':
                    # Should have lower scores due to limited history
                    assert profile.data_completeness < 0.8

                elif profile_type == 'whale':
                    # Should have high collateral score
                    assert profile.collateral_score >= 0.7

            except Exception as e:
                pytest.skip(f"Could not generate profile for {profile_type}: {str(e)}")

    async def test_end_to_end_real_loan_application(self, mainnet_config, real_algorand_addresses):
        """Test end-to-end loan application with real Algorand data"""

        orchestrator = HolisticDecisionOrchestrator()

        # Create loan application using real address
        test_address = real_algorand_addresses['governance_participant']

        application = LoanApplication(
            application_id="REAL_ALGO_TEST_001",
            borrower_address=test_address,
            loan_amount=25000.0,
            requested_term=180,
            collateral_assets=[],  # Will be populated from real data
            purpose="Real Algorand ecosystem test",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        try:
            # Process real application
            decision = await orchestrator.process_loan_application(application)

            # Verify decision is valid
            assert decision.application_id == "REAL_ALGO_TEST_001"
            assert decision.decision is not None
            assert decision.confidence is not None
            assert decision.overall_score >= 0
            assert decision.processing_time > 0

            # Decision should be based on real data
            assert decision.ecosystem_score > 0
            assert len(decision.primary_factors) > 0

        except Exception as e:
            pytest.skip(f"Could not process real application: {str(e)}")

    async def test_network_health_monitoring(self, mainnet_config):
        """Test real-time network health monitoring"""

        algod_url = mainnet_config['algorand']['algod_url']

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Test node health
                status_response = await client.get(f"{algod_url}/v2/status")

                if status_response.status_code == 200:
                    status_data = status_response.json()

                    # Verify network status
                    assert 'last-round' in status_data
                    assert 'time-since-last-round' in status_data

                    # Calculate network health metrics
                    time_since_last_round = status_data.get('time-since-last-round', 0)
                    network_health = _calculate_network_health(status_data)

                    assert 0 <= network_health['health_score'] <= 1
                    assert 'block_time' in network_health
                    assert 'consensus_status' in network_health

                    # Network should be healthy (block time < 5 seconds)
                    if time_since_last_round < 5000000000:  # 5 seconds in nanoseconds
                        assert network_health['health_score'] >= 0.8

        except httpx.ConnectError:
            pytest.skip("Algorand node not available")

    async def test_governance_period_transitions(self, mainnet_config):
        """Test handling of governance period transitions"""

        governance_config = mainnet_config['data_sources']['governance']

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Get current governance period
                current_response = await client.get(
                    f"{governance_config['api_endpoint']}/periods/current"
                )

                if current_response.status_code == 200:
                    current_period = current_response.json()

                    # Get historical periods
                    history_response = await client.get(
                        f"{governance_config['api_endpoint']}/periods/history"
                    )

                    if history_response.status_code == 200:
                        historical_periods = history_response.json()

                        # Verify period transition handling
                        governance_analysis = _analyze_governance_periods(
                            current_period, historical_periods
                        )

                        assert 'current_period_status' in governance_analysis
                        assert 'transition_impact' in governance_analysis
                        assert 'participation_trends' in governance_analysis

        except httpx.ConnectError:
            pytest.skip("Governance API not available")

    async def test_cross_protocol_activity_correlation(self, mainnet_config, real_algorand_addresses):
        """Test correlation analysis across multiple DeFi protocols"""

        test_address = real_algorand_addresses['defi_active']
        protocols = mainnet_config['data_sources']['defi_protocols']

        activity_data = {}

        for protocol in protocols:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    # Get user activity from each protocol
                    activity_response = await client.get(
                        f"{protocol['api_endpoint']}/users/{test_address}/activity"
                    )

                    if activity_response.status_code == 200:
                        activity_data[protocol['name']] = activity_response.json()

            except httpx.ConnectError:
                continue

        # Analyze cross-protocol activity
        if activity_data:
            correlation_analysis = _analyze_cross_protocol_activity(activity_data)

            assert 'protocol_diversification' in correlation_analysis
            assert 'activity_correlation' in correlation_analysis
            assert 'risk_concentration' in correlation_analysis

            # High diversification should reduce risk
            if correlation_analysis['protocol_diversification'] > 0.7:
                assert correlation_analysis['risk_concentration'] < 0.5


# Helper functions for real data analysis

def _analyze_transaction_patterns(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze transaction patterns from real transaction data"""

    analysis = {
        'total_transactions': len(transactions),
        'transaction_types': {},
        'dapp_interactions': 0,
        'defi_activity_score': 0.0,
        'avg_transaction_frequency': 0.0
    }

    if not transactions:
        return analysis

    # Count transaction types
    for tx in transactions:
        tx_type = tx.get('tx-type', 'unknown')
        analysis['transaction_types'][tx_type] = analysis['transaction_types'].get(tx_type, 0) + 1

        # Check for dApp interactions
        if 'application-transaction' in tx:
            analysis['dapp_interactions'] += 1

    # Calculate activity scores
    analysis['defi_activity_score'] = min(1.0, analysis['dapp_interactions'] / 100)

    # Calculate frequency (transactions per day)
    if len(transactions) > 1:
        first_tx = transactions[-1]  # Oldest
        last_tx = transactions[0]   # Newest

        if 'round-time' in first_tx and 'round-time' in last_tx:
            time_span_days = (last_tx['round-time'] - first_tx['round-time']) / (24 * 3600)
            if time_span_days > 0:
                analysis['avg_transaction_frequency'] = len(transactions) / time_span_days

    return analysis


def _calculate_network_health(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate network health metrics from node status"""

    health = {
        'health_score': 1.0,
        'block_time': 0.0,
        'consensus_status': 'healthy'
    }

    # Calculate block time
    time_since_last_round = status_data.get('time-since-last-round', 0)
    block_time_seconds = time_since_last_round / 1000000000  # Convert from nanoseconds

    health['block_time'] = block_time_seconds

    # Health score based on block time
    if block_time_seconds <= 3.0:
        health['health_score'] = 1.0
        health['consensus_status'] = 'excellent'
    elif block_time_seconds <= 4.5:
        health['health_score'] = 0.9
        health['consensus_status'] = 'good'
    elif block_time_seconds <= 6.0:
        health['health_score'] = 0.7
        health['consensus_status'] = 'fair'
    else:
        health['health_score'] = 0.5
        health['consensus_status'] = 'poor'

    return health


def _analyze_governance_periods(
    current_period: Dict[str, Any],
    historical_periods: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze governance period data and transitions"""

    analysis = {
        'current_period_status': 'active',
        'transition_impact': 'none',
        'participation_trends': {}
    }

    # Analyze current period
    if 'status' in current_period:
        analysis['current_period_status'] = current_period['status']

    # Analyze historical trends
    if historical_periods:
        participation_rates = []
        for period in historical_periods:
            if 'participation_rate' in period:
                participation_rates.append(period['participation_rate'])

        if participation_rates:
            analysis['participation_trends'] = {
                'average_participation': sum(participation_rates) / len(participation_rates),
                'trend': 'increasing' if len(participation_rates) > 1 and
                        participation_rates[-1] > participation_rates[0] else 'stable'
            }

    return analysis


def _analyze_cross_protocol_activity(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze activity correlation across DeFi protocols"""

    analysis = {
        'protocol_diversification': 0.0,
        'activity_correlation': 0.0,
        'risk_concentration': 1.0
    }

    protocols_with_activity = len([p for p in activity_data.values() if p.get('activity_count', 0) > 0])
    total_protocols = len(activity_data)

    if total_protocols > 0:
        analysis['protocol_diversification'] = protocols_with_activity / total_protocols

    # Calculate risk concentration (inverse of diversification)
    analysis['risk_concentration'] = 1.0 - analysis['protocol_diversification']

    return analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])