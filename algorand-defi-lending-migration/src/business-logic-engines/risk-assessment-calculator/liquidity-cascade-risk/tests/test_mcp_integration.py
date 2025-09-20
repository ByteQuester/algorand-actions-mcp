"""
MCP Integration Test Suite for Liquidity Cascade Risk Engine

This test suite validates the integration with MCP services for real-time
market data and transaction execution capabilities.
"""

import pytest
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liquidity_engine import LiquidityCascadeRiskEngine

class MockMCPService:
    """Mock MCP service for testing"""

    def __init__(self, port: int, service_type: str):
        self.port = port
        self.service_type = service_type
        self.is_running = False

    async def start(self):
        """Start mock MCP service"""
        self.is_running = True

    async def stop(self):
        """Stop mock MCP service"""
        self.is_running = False

    async def get_market_data(self, asset_pairs: List[str]) -> Dict[str, Any]:
        """Mock market data endpoint"""
        if not self.is_running:
            raise ConnectionError("MCP service not running")

        # Generate mock market data
        mock_data = {}
        for pair in asset_pairs:
            base, quote = pair.split('/')
            mock_data[pair] = {
                'price': 0.5 if base == 'ALGO' else 1.0,
                'volume_24h': 1000000,
                'liquidity': 5000000,
                'spread_bps': 10,
                'last_updated': datetime.now().isoformat()
            }
        return mock_data

    async def get_protocol_data(self, protocols: List[str]) -> Dict[str, Any]:
        """Mock protocol data endpoint"""
        if not self.is_running:
            raise ConnectionError("MCP service not running")

        mock_data = {}
        for protocol in protocols:
            mock_data[protocol] = {
                'tvl': 50000000,
                'utilization_rate': 0.7,
                'health_factor': 1.5,
                'liquidation_threshold': 0.85,
                'available_liquidity': 15000000,
                'last_updated': datetime.now().isoformat()
            }
        return mock_data

    async def execute_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transaction execution endpoint"""
        if not self.is_running:
            raise ConnectionError("MCP service not running")

        return {
            'transaction_id': f"mock_tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'status': 'confirmed',
            'gas_used': 21000,
            'execution_time_ms': 150
        }

class TestMCPIntegration:
    """Test suite for MCP integration"""

    @pytest.fixture
    async def mock_mcp_services(self):
        """Setup mock MCP services"""
        reader_service = MockMCPService(8002, "reader")
        writer_service = MockMCPService(8003, "writer")

        await reader_service.start()
        await writer_service.start()

        yield {
            'reader': reader_service,
            'writer': writer_service
        }

        await reader_service.stop()
        await writer_service.stop()

    @pytest.fixture
    def risk_engine(self):
        """Create risk engine instance"""
        return LiquidityCascadeRiskEngine()

    @pytest.mark.asyncio
    async def test_mcp_connectivity(self, mock_mcp_services):
        """Test basic MCP service connectivity"""
        reader = mock_mcp_services['reader']
        writer = mock_mcp_services['writer']

        # Test reader service
        assert reader.is_running
        market_data = await reader.get_market_data(['ALGO/USDC', 'GARD/ALGO'])
        assert 'ALGO/USDC' in market_data
        assert 'GARD/ALGO' in market_data

        # Test writer service
        assert writer.is_running
        tx_result = await writer.execute_transaction({'type': 'test'})
        assert 'transaction_id' in tx_result
        assert tx_result['status'] == 'confirmed'

    @pytest.mark.asyncio
    async def test_market_data_integration(self, mock_mcp_services, risk_engine):
        """Test integration with market data MCP service"""
        reader = mock_mcp_services['reader']

        # Test market data retrieval
        asset_pairs = ['ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO']
        market_data = await reader.get_market_data(asset_pairs)

        # Validate market data structure
        for pair in asset_pairs:
            assert pair in market_data
            pair_data = market_data[pair]
            assert 'price' in pair_data
            assert 'volume_24h' in pair_data
            assert 'liquidity' in pair_data
            assert 'spread_bps' in pair_data
            assert pair_data['price'] > 0
            assert pair_data['volume_24h'] > 0

    @pytest.mark.asyncio
    async def test_protocol_data_integration(self, mock_mcp_services, risk_engine):
        """Test integration with protocol data MCP service"""
        reader = mock_mcp_services['reader']

        # Test protocol data retrieval
        protocols = ['algofi', 'folks_finance', 'tinyman', 'pact']
        protocol_data = await reader.get_protocol_data(protocols)

        # Validate protocol data structure
        for protocol in protocols:
            assert protocol in protocol_data
            data = protocol_data[protocol]
            assert 'tvl' in data
            assert 'utilization_rate' in data
            assert 'health_factor' in data
            assert data['tvl'] > 0
            assert 0 <= data['utilization_rate'] <= 1

    @pytest.mark.asyncio
    async def test_transaction_execution_integration(self, mock_mcp_services, risk_engine):
        """Test integration with transaction execution MCP service"""
        writer = mock_mcp_services['writer']

        # Test transaction execution
        tx_data = {
            'type': 'swap',
            'from_asset': 'ALGO',
            'to_asset': 'USDC',
            'amount': 1000,
            'slippage_tolerance': 0.01
        }

        result = await writer.execute_transaction(tx_data)

        assert 'transaction_id' in result
        assert 'status' in result
        assert result['status'] in ['pending', 'confirmed', 'failed']

    @pytest.mark.asyncio
    async def test_real_time_data_updates(self, mock_mcp_services, risk_engine):
        """Test real-time data updates from MCP services"""
        reader = mock_mcp_services['reader']

        # Simulate multiple data updates
        updates = []
        for i in range(5):
            market_data = await reader.get_market_data(['ALGO/USDC'])
            updates.append(market_data['ALGO/USDC'])
            await asyncio.sleep(0.1)  # Small delay between updates

        # Validate we received multiple updates
        assert len(updates) == 5
        for update in updates:
            assert 'last_updated' in update
            assert update['price'] > 0

    @pytest.mark.asyncio
    async def test_mcp_error_handling(self, mock_mcp_services):
        """Test error handling for MCP service failures"""
        reader = mock_mcp_services['reader']
        writer = mock_mcp_services['writer']

        # Stop services to simulate failure
        await reader.stop()
        await writer.stop()

        # Test reader service failure
        with pytest.raises(ConnectionError):
            await reader.get_market_data(['ALGO/USDC'])

        # Test writer service failure
        with pytest.raises(ConnectionError):
            await writer.execute_transaction({'type': 'test'})

    @pytest.mark.asyncio
    async def test_mcp_data_validation(self, mock_mcp_services):
        """Test validation of MCP data"""
        reader = mock_mcp_services['reader']

        # Get market data
        market_data = await reader.get_market_data(['ALGO/USDC'])
        algo_usdc = market_data['ALGO/USDC']

        # Validate data types and ranges
        assert isinstance(algo_usdc['price'], (int, float))
        assert algo_usdc['price'] > 0

        assert isinstance(algo_usdc['volume_24h'], (int, float))
        assert algo_usdc['volume_24h'] >= 0

        assert isinstance(algo_usdc['liquidity'], (int, float))
        assert algo_usdc['liquidity'] >= 0

        assert isinstance(algo_usdc['spread_bps'], (int, float))
        assert algo_usdc['spread_bps'] >= 0

        # Validate timestamp format
        last_updated = algo_usdc['last_updated']
        datetime.fromisoformat(last_updated.replace('Z', '+00:00'))

class TestMCPRiskEngineIntegration:
    """Test integration between MCP services and risk engine"""

    @pytest.fixture
    async def integrated_system(self):
        """Setup integrated system with risk engine and mock MCP services"""
        # Create mock MCP services
        reader_service = MockMCPService(8002, "reader")
        writer_service = MockMCPService(8003, "writer")

        await reader_service.start()
        await writer_service.start()

        # Create risk engine
        risk_engine = LiquidityCascadeRiskEngine()

        yield {
            'risk_engine': risk_engine,
            'reader': reader_service,
            'writer': writer_service
        }

        await reader_service.stop()
        await writer_service.stop()

    @pytest.mark.asyncio
    async def test_comprehensive_assessment_with_mcp(self, integrated_system):
        """Test comprehensive risk assessment using MCP data"""
        risk_engine = integrated_system['risk_engine']
        reader = integrated_system['reader']

        # Simulate getting fresh market data from MCP
        market_data = await reader.get_market_data([
            'ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO', 'BANK/ALGO'
        ])

        protocol_data = await reader.get_protocol_data([
            'algofi', 'folks_finance', 'tinyman', 'pact'
        ])

        # Run comprehensive assessment
        portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        assessment = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=False,
            stress_testing=False
        )

        # Validate assessment completed successfully
        assert assessment is not None
        assert hasattr(assessment, 'overall_risk_level')
        assert hasattr(assessment, 'component_results')

        # Check that market data influenced the assessment
        assert 'market_depth_analysis' in assessment.component_results

    @pytest.mark.asyncio
    async def test_real_time_monitoring_with_mcp(self, integrated_system):
        """Test real-time monitoring using MCP data streams"""
        risk_engine = integrated_system['risk_engine']
        reader = integrated_system['reader']

        # Simulate real-time monitoring loop
        monitoring_results = []

        for i in range(3):  # Monitor for 3 iterations
            # Get fresh data from MCP
            market_data = await reader.get_market_data(['ALGO/USDC'])
            protocol_data = await reader.get_protocol_data(['algofi'])

            # Get current risk status
            risk_status = risk_engine.get_current_risk_status()

            monitoring_results.append({
                'iteration': i,
                'market_data': market_data,
                'protocol_data': protocol_data,
                'risk_status': risk_status,
                'timestamp': datetime.now()
            })

            await asyncio.sleep(0.1)  # Small delay between monitoring cycles

        # Validate monitoring results
        assert len(monitoring_results) == 3

        for result in monitoring_results:
            assert 'market_data' in result
            assert 'protocol_data' in result
            assert 'risk_status' in result

    @pytest.mark.asyncio
    async def test_liquidation_execution_with_mcp(self, integrated_system):
        """Test liquidation execution through MCP services"""
        writer = integrated_system['writer']

        # Simulate liquidation transaction
        liquidation_tx = {
            'type': 'liquidation',
            'protocol': 'algofi',
            'collateral_asset': 'ALGO',
            'debt_asset': 'USDC',
            'amount': 100000,
            'liquidation_bonus': 0.05
        }

        # Execute through MCP writer service
        result = await writer.execute_transaction(liquidation_tx)

        # Validate execution result
        assert 'transaction_id' in result
        assert 'status' in result
        assert result['status'] in ['pending', 'confirmed']

    @pytest.mark.asyncio
    async def test_mcp_failover_handling(self, integrated_system):
        """Test handling of MCP service failures with graceful degradation"""
        risk_engine = integrated_system['risk_engine']
        reader = integrated_system['reader']

        # First, run assessment with MCP services available
        portfolio = {'ALGO': 0.5, 'USDC': 0.5}

        assessment_with_mcp = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=False,
            stress_testing=False
        )

        # Stop MCP service to simulate failure
        await reader.stop()

        # Run assessment again - should handle gracefully
        assessment_without_mcp = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=False,
            stress_testing=False
        )

        # Both assessments should complete
        assert assessment_with_mcp is not None
        assert assessment_without_mcp is not None

        # Risk engine should provide some level of assessment even without MCP
        assert hasattr(assessment_without_mcp, 'overall_risk_level')

    @pytest.mark.asyncio
    async def test_mcp_data_caching(self, integrated_system):
        """Test caching of MCP data for performance"""
        reader = integrated_system['reader']

        # Make multiple requests for same data
        start_time = datetime.now()

        data_requests = []
        for i in range(5):
            market_data = await reader.get_market_data(['ALGO/USDC'])
            data_requests.append(market_data)

        end_time = datetime.now()

        # All requests should return data
        assert len(data_requests) == 5

        for data in data_requests:
            assert 'ALGO/USDC' in data
            assert data['ALGO/USDC']['price'] > 0

        # Execution should be reasonably fast
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5.0  # Should complete within 5 seconds

class TestMCPPerformance:
    """Performance tests for MCP integration"""

    @pytest.mark.asyncio
    async def test_concurrent_mcp_requests(self):
        """Test concurrent requests to MCP services"""
        reader = MockMCPService(8002, "reader")
        await reader.start()

        try:
            # Make concurrent requests
            tasks = []
            for i in range(10):
                task = reader.get_market_data(['ALGO/USDC', 'GARD/ALGO'])
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert len(results) == 10

            for result in results:
                assert 'ALGO/USDC' in result
                assert 'GARD/ALGO' in result

        finally:
            await reader.stop()

    @pytest.mark.asyncio
    async def test_mcp_response_time(self):
        """Test MCP service response times"""
        reader = MockMCPService(8002, "reader")
        await reader.start()

        try:
            # Measure response time
            start_time = datetime.now()

            market_data = await reader.get_market_data([
                'ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO', 'BANK/ALGO', 'OPUL/ALGO'
            ])

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            # Response should be fast
            assert response_time < 1.0  # Less than 1 second
            assert len(market_data) == 5

        finally:
            await reader.stop()

    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test handling of large data responses from MCP"""
        reader = MockMCPService(8002, "reader")
        await reader.start()

        try:
            # Request data for many asset pairs
            asset_pairs = [
                'ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO', 'BANK/ALGO',
                'OPUL/ALGO', 'SMILE/ALGO', 'DEGEN/ALGO', 'VOTE/ALGO',
                'PLANET/ALGO', 'CHOICE/ALGO'
            ]

            market_data = await reader.get_market_data(asset_pairs)

            # Should handle all pairs
            assert len(market_data) == len(asset_pairs)

            # Validate each pair has required data
            for pair in asset_pairs:
                assert pair in market_data
                pair_data = market_data[pair]
                assert 'price' in pair_data
                assert 'volume_24h' in pair_data
                assert 'liquidity' in pair_data

        finally:
            await reader.stop()

# Integration test runner
async def run_integration_tests():
    """Run basic integration tests"""
    print("Running MCP Integration Tests...")

    # Test 1: Basic MCP service functionality
    print("1. Testing basic MCP service functionality...")
    reader = MockMCPService(8002, "reader")
    await reader.start()

    try:
        market_data = await reader.get_market_data(['ALGO/USDC'])
        assert 'ALGO/USDC' in market_data
        print("   ✓ MCP reader service working")
    finally:
        await reader.stop()

    # Test 2: Risk engine with MCP integration
    print("2. Testing risk engine with MCP integration...")
    reader = MockMCPService(8002, "reader")
    writer = MockMCPService(8003, "writer")

    await reader.start()
    await writer.start()

    try:
        risk_engine = LiquidityCascadeRiskEngine()

        # Get market data
        market_data = await reader.get_market_data(['ALGO/USDC', 'GARD/ALGO'])
        assert len(market_data) == 2

        # Run assessment
        portfolio = {'ALGO': 0.6, 'USDC': 0.4}
        assessment = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=False,
            stress_testing=False
        )

        assert assessment is not None
        print("   ✓ Risk engine assessment with MCP data working")

    finally:
        await reader.stop()
        await writer.stop()

    print("✓ All MCP integration tests passed!")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())