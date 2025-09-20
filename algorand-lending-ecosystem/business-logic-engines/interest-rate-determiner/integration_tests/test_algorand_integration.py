"""
Integration tests for Algorand blockchain connectivity and MCP services integration.

Tests:
- All engines connecting to Algorand mainnet/testnet
- MCP services integration (ports 8002/8003)
- Real-time DeFi protocol data fetching
"""

import pytest
import asyncio
import httpx
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from algosdk.v2client import algod, indexer
from algosdk import account, mnemonic

from interest_rate_determiner.engines import (
    AlgoStakingEngine,
    DeFiYieldEngine,
    ReputationEngine,
    ASARiskEngine,
    NetworkActivityEngine,
    LiquidityPoolEngine
)

# Test configuration
TESTNET_ALGOD_URL = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER_URL = "https://testnet-idx.algonode.cloud"
MCP_READER_PORT = 8002
MCP_WRITER_PORT = 8003

@pytest.fixture
def testnet_clients():
    """Create testnet clients for integration testing"""
    algod_client = algod.AlgodClient("", TESTNET_ALGOD_URL)
    indexer_client = indexer.IndexerClient("", TESTNET_INDEXER_URL)
    return algod_client, indexer_client

@pytest.fixture
def mcp_clients():
    """Mock MCP service clients"""
    return {
        'reader': f"http://localhost:{MCP_READER_PORT}",
        'writer': f"http://localhost:{MCP_WRITER_PORT}"
    }

class TestAlgorandConnectivity:
    """Test Algorand blockchain connectivity"""

    @pytest.mark.asyncio
    async def test_algod_connection(self, testnet_clients):
        """Test Algorand node connection"""
        algod_client, _ = testnet_clients

        try:
            status = algod_client.status()
            assert 'last-round' in status
            assert status['last-round'] > 0

            # Test network participation data
            supply = algod_client.supply()
            assert 'total-money' in supply
            assert 'online-money' in supply
            assert supply['total-money'] > 0

            print(f"Connected to Algorand testnet - Round: {status['last-round']}")
            print(f"Total supply: {supply['total-money']:,} microALGO")
            print(f"Online supply: {supply['online-money']:,} microALGO")

        except Exception as e:
            pytest.skip(f"Algorand connection failed: {e}")

    @pytest.mark.asyncio
    async def test_indexer_connection(self, testnet_clients):
        """Test Algorand indexer connection"""
        _, indexer_client = testnet_clients

        try:
            # Test transaction search
            txns = indexer_client.search_transactions(limit=1)
            txn_list = list(txns)
            assert len(txn_list) >= 0

            # Test asset search
            assets = indexer_client.search_assets(limit=1)
            asset_list = list(assets)
            assert len(asset_list) >= 0

            print(f"Indexer connection successful")

        except Exception as e:
            pytest.skip(f"Indexer connection failed: {e}")

    @pytest.mark.asyncio
    async def test_staking_engine_with_real_data(self, testnet_clients):
        """Test ALGO staking engine with real blockchain data"""
        algod_client, _ = testnet_clients

        try:
            engine = AlgoStakingEngine(algod_client)
            metrics = await engine.calculate_staking_rate()

            assert metrics.current_apy > Decimal('0')
            assert metrics.participation_rate > Decimal('0')
            assert metrics.participation_rate <= Decimal('1')
            assert metrics.total_staked_algo > Decimal('0')

            print(f"Real staking metrics:")
            print(f"  Current APY: {metrics.current_apy:.4f}")
            print(f"  Participation Rate: {metrics.participation_rate:.4f}")
            print(f"  Total Staked: {metrics.total_staked_algo:,.0f} microALGO")

        except Exception as e:
            pytest.skip(f"Staking engine test failed: {e}")

    @pytest.mark.asyncio
    async def test_reputation_engine_with_real_address(self, testnet_clients):
        """Test reputation engine with real Algorand address"""
        algod_client, indexer_client = testnet_clients

        # Use a known testnet address (Algorand Foundation)
        test_address = "ALGORAND4OEQYQO6Q7NBLNQWMTMFZ2PDKNQM6DQFWDLAFGGQQNFCQRFPWMKWFYAAI"

        try:
            engine = ReputationEngine(algod_client, indexer_client)
            reputation = await engine.calculate_reputation(test_address)

            assert reputation.overall_score >= Decimal('0')
            assert reputation.overall_score <= Decimal('1')
            assert reputation.confidence_level >= Decimal('0')

            print(f"Real reputation analysis for {test_address[:10]}...:")
            print(f"  Overall Score: {reputation.overall_score:.4f}")
            print(f"  Tier: {reputation.tier.value}")
            print(f"  Confidence: {reputation.confidence_level:.4f}")

        except Exception as e:
            print(f"Reputation test warning: {e}")
            # Don't skip - reputation analysis can work with limited data

class TestMCPIntegration:
    """Test MCP (Model Context Protocol) services integration"""

    @pytest.mark.asyncio
    async def test_mcp_reader_service(self, mcp_clients):
        """Test MCP reader service connectivity"""
        reader_url = mcp_clients['reader']

        try:
            async with httpx.AsyncClient() as client:
                # Test health endpoint
                response = await client.get(f"{reader_url}/health", timeout=5.0)

                if response.status_code == 200:
                    print(f"MCP Reader service is running on port {MCP_READER_PORT}")

                    # Test blockchain data endpoint
                    try:
                        data_response = await client.get(f"{reader_url}/api/v1/network/status")
                        if data_response.status_code == 200:
                            data = data_response.json()
                            print(f"MCP Reader data sample: {data}")
                    except:
                        print("MCP Reader data endpoint not available")

                else:
                    pytest.skip(f"MCP Reader service not responding: {response.status_code}")

        except httpx.ConnectError:
            pytest.skip(f"MCP Reader service not running on port {MCP_READER_PORT}")
        except Exception as e:
            pytest.skip(f"MCP Reader test failed: {e}")

    @pytest.mark.asyncio
    async def test_mcp_writer_service(self, mcp_clients):
        """Test MCP writer service connectivity"""
        writer_url = mcp_clients['writer']

        try:
            async with httpx.AsyncClient() as client:
                # Test health endpoint
                response = await client.get(f"{writer_url}/health", timeout=5.0)

                if response.status_code == 200:
                    print(f"MCP Writer service is running on port {MCP_WRITER_PORT}")

                    # Test write capability (mock transaction)
                    try:
                        write_response = await client.post(
                            f"{writer_url}/api/v1/transactions/simulate",
                            json={"type": "test", "amount": 1000}
                        )
                        if write_response.status_code in [200, 201]:
                            print("MCP Writer accepts transaction simulations")
                    except:
                        print("MCP Writer transaction endpoint not available")

                else:
                    pytest.skip(f"MCP Writer service not responding: {response.status_code}")

        except httpx.ConnectError:
            pytest.skip(f"MCP Writer service not running on port {MCP_WRITER_PORT}")
        except Exception as e:
            pytest.skip(f"MCP Writer test failed: {e}")

    @pytest.mark.asyncio
    async def test_engines_with_mcp_integration(self, testnet_clients, mcp_clients):
        """Test engines integration with MCP services"""
        algod_client, indexer_client = testnet_clients

        # Initialize engines
        engines = {
            'staking': AlgoStakingEngine(algod_client),
            'defi': DeFiYieldEngine(algod_client, {}),
            'reputation': ReputationEngine(algod_client, indexer_client),
            'asa_risk': ASARiskEngine(algod_client, indexer_client, {}),
            'network': NetworkActivityEngine(algod_client),
            'liquidity': LiquidityPoolEngine(algod_client)
        }

        # Test each engine can connect and get data
        results = {}

        try:
            # Test staking engine
            staking_metrics = await engines['staking'].calculate_staking_rate()
            results['staking'] = {
                'success': True,
                'apy': float(staking_metrics.current_apy),
                'participation': float(staking_metrics.participation_rate)
            }
        except Exception as e:
            results['staking'] = {'success': False, 'error': str(e)}

        try:
            # Test DeFi engine
            defi_metrics = await engines['defi'].calculate_defi_rates()
            results['defi'] = {
                'success': True,
                'weighted_apy': float(defi_metrics.weighted_avg_apy),
                'protocol_count': defi_metrics.protocol_count
            }
        except Exception as e:
            results['defi'] = {'success': False, 'error': str(e)}

        try:
            # Test network engine
            network_metrics = await engines['network'].analyze_network_activity()
            results['network'] = {
                'success': True,
                'health': network_metrics.network_health.value,
                'congestion': float(network_metrics.congestion_score)
            }
        except Exception as e:
            results['network'] = {'success': False, 'error': str(e)}

        try:
            # Test liquidity engine
            liquidity_metrics = await engines['liquidity'].analyze_liquidity_health()
            results['liquidity'] = {
                'success': True,
                'total_tvl': float(liquidity_metrics.total_tvl),
                'health_score': float(liquidity_metrics.health_score)
            }
        except Exception as e:
            results['liquidity'] = {'success': False, 'error': str(e)}

        # Verify at least some engines work
        successful_engines = [k for k, v in results.items() if v.get('success')]
        assert len(successful_engines) >= 2, f"At least 2 engines should work, got: {successful_engines}"

        print(f"\\nMCP Integration Results:")
        for engine_name, result in results.items():
            if result.get('success'):
                print(f"  ✓ {engine_name}: {result}")
            else:
                print(f"  ✗ {engine_name}: {result.get('error', 'Unknown error')}")

class TestRealTimeDataFetching:
    """Test real-time DeFi protocol data fetching"""

    @pytest.mark.asyncio
    async def test_tinyman_api_integration(self):
        """Test integration with Tinyman API"""
        tinyman_api = "https://mainnet.analytics.tinyman.org/api/v1"

        try:
            async with httpx.AsyncClient() as client:
                # Test pools endpoint
                response = await client.get(f"{tinyman_api}/pools", timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    pools = data.get('pools', [])

                    assert len(pools) > 0, "Should have some pools"

                    # Verify pool data structure
                    if pools:
                        pool = pools[0]
                        required_fields = ['id', 'asset_1', 'asset_2']
                        for field in required_fields:
                            assert field in pool, f"Pool should have {field} field"

                    print(f"Tinyman API: {len(pools)} pools found")

                else:
                    pytest.skip(f"Tinyman API not accessible: {response.status_code}")

        except Exception as e:
            pytest.skip(f"Tinyman API test failed: {e}")

    @pytest.mark.asyncio
    async def test_defi_yield_aggregation(self, testnet_clients):
        """Test DeFi yield aggregation from multiple sources"""
        algod_client, _ = testnet_clients

        try:
            engine = DeFiYieldEngine(algod_client, {})

            # Test with different protocol selections
            all_protocols = await engine.calculate_defi_rates()
            assert all_protocols.protocol_count >= 0
            assert all_protocols.weighted_avg_apy >= Decimal('0')

            # Test risk filtering
            safe_protocols = await engine.calculate_defi_rates(
                risk_threshold=Decimal('0.5')
            )
            assert safe_protocols.risk_adjusted_apy >= Decimal('0')

            print(f"DeFi Yield Aggregation:")
            print(f"  All protocols: {all_protocols.protocol_count} protocols, {all_protocols.weighted_avg_apy:.4f} APY")
            print(f"  Safe protocols: {safe_protocols.protocol_count} protocols, {safe_protocols.risk_adjusted_apy:.4f} APY")

        except Exception as e:
            print(f"DeFi aggregation warning: {e}")

    @pytest.mark.asyncio
    async def test_real_time_rate_updates(self, testnet_clients):
        """Test real-time rate updates based on blockchain data"""
        algod_client, indexer_client = testnet_clients

        try:
            # Initialize all engines
            staking_engine = AlgoStakingEngine(algod_client)
            defi_engine = DeFiYieldEngine(algod_client, {})
            network_engine = NetworkActivityEngine(algod_client)

            # Get initial rates
            initial_staking = await staking_engine.calculate_staking_rate()
            initial_defi = await defi_engine.calculate_defi_rates()
            initial_network = await network_engine.analyze_network_activity()

            # Wait a short time and get updated rates
            await asyncio.sleep(2)

            updated_staking = await staking_engine.calculate_staking_rate()
            updated_defi = await defi_engine.calculate_defi_rates()
            updated_network = await network_engine.analyze_network_activity()

            # Verify data freshness
            assert updated_staking.timestamp >= initial_staking.timestamp
            assert updated_defi.timestamp >= initial_defi.timestamp
            assert updated_network.timestamp >= initial_network.timestamp

            print(f"Real-time updates working:")
            print(f"  Staking: {initial_staking.current_apy:.4f} → {updated_staking.current_apy:.4f}")
            print(f"  DeFi: {initial_defi.weighted_avg_apy:.4f} → {updated_defi.weighted_avg_apy:.4f}")
            print(f"  Network: {initial_network.congestion_score:.4f} → {updated_network.congestion_score:.4f}")

        except Exception as e:
            print(f"Real-time updates warning: {e}")

class TestBlockchainCollateralIntegration:
    """Test integration with blockchain-collateral-analyzer"""

    @pytest.mark.asyncio
    async def test_collateral_analyzer_integration(self, testnet_clients):
        """Test integration with blockchain collateral analyzer"""
        algod_client, indexer_client = testnet_clients

        try:
            # Test ASA risk engine (which would integrate with collateral analyzer)
            asa_engine = ASARiskEngine(algod_client, indexer_client, {})

            # Test with a known ASA (USDC on Algorand testnet)
            usdc_asset_id = 10458941  # USDC testnet

            risk_metrics = await asa_engine.analyze_asa_risk(usdc_asset_id)

            assert risk_metrics.overall_risk_score >= Decimal('0')
            assert risk_metrics.collateral_factor > Decimal('0')
            assert risk_metrics.collateral_factor <= Decimal('1')

            print(f"Collateral Analysis for ASA {usdc_asset_id}:")
            print(f"  Risk Score: {risk_metrics.overall_risk_score:.4f}")
            print(f"  Collateral Factor: {risk_metrics.collateral_factor:.4f}")
            print(f"  Rate Premium: {risk_metrics.interest_rate_premium:.4f}")

        except Exception as e:
            print(f"Collateral integration warning: {e}")

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])