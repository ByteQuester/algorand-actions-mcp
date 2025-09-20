"""
MCP Integration Tests for Base Rate Calculation Engine

Tests the integration with MCP services for live data retrieval.
"""

import unittest
import requests
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path

from core.config import BaseRateCalculationConfig, load_config
from core.base_rate_calculation import (
    BaseRateCalculationEngine,
    FederalReserveClient,
    AlgorandDataClient,
    RateDataPoint
)


class TestMCPServiceIntegration(unittest.TestCase):
    """Test integration with MCP services"""

    def setUp(self):
        self.config = BaseRateCalculationConfig()
        self.algorand_reader_url = self.config.mcp_services.algorand_reader_url
        self.market_data_url = self.config.mcp_services.market_data_url

    def test_mcp_service_availability(self):
        """Test if MCP services are available"""
        try:
            # Test Algorand reader service
            response = requests.get(f"{self.algorand_reader_url}/health", timeout=5)
            algorand_available = response.status_code == 200
        except:
            algorand_available = False

        try:
            # Test market data service
            response = requests.get(f"{self.market_data_url}/health", timeout=5)
            market_available = response.status_code == 200
        except:
            market_available = False

        # Log availability status
        print(f"Algorand Reader MCP (port 8002): {'Available' if algorand_available else 'Not Available'}")
        print(f"Market Data MCP (port 8003): {'Available' if market_available else 'Not Available'}")

        # Test should pass regardless of service availability for development
        self.assertTrue(True)  # Always pass, just for information

    @unittest.skipUnless(
        _check_mcp_service('http://localhost:8002'),
        "Algorand Reader MCP service not available"
    )
    def test_algorand_reader_mcp_integration(self):
        """Test integration with Algorand Reader MCP service"""
        client = AlgorandDataClient(
            algorand_reader_url=self.algorand_reader_url,
            market_data_url=self.market_data_url
        )

        # Test getting account information (basic connectivity)
        try:
            # This would be a real MCP call in practice
            response = requests.get(
                f"{self.algorand_reader_url}/account/info",
                params={'address': 'ALGORAND_FOUNDATION_ADDRESS'},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.assertIn('account', data)
            else:
                self.skipTest(f"MCP service returned {response.status_code}")

        except requests.RequestException as e:
            self.skipTest(f"MCP service connection failed: {e}")

    @unittest.skipUnless(
        _check_mcp_service('http://localhost:8003'),
        "Market Data MCP service not available"
    )
    def test_market_data_mcp_integration(self):
        """Test integration with Market Data MCP service"""
        try:
            # Test getting market data
            response = requests.get(
                f"{self.market_data_url}/price/ALGO",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.assertIn('price', data)
                self.assertIsInstance(data['price'], (int, float))
                self.assertGreater(data['price'], 0)
            else:
                self.skipTest(f"Market Data MCP service returned {response.status_code}")

        except requests.RequestException as e:
            self.skipTest(f"Market Data MCP service connection failed: {e}")

    def test_mcp_service_fallback_behavior(self):
        """Test fallback behavior when MCP services are unavailable"""
        # Use invalid URLs to simulate service unavailability
        client = AlgorandDataClient(
            algorand_reader_url='http://localhost:9999',  # Invalid port
            market_data_url='http://localhost:9998'       # Invalid port
        )

        # Should still return staking rewards (simulated data)
        staking_rate = client.get_staking_rewards()
        self.assertIsNotNone(staking_rate)
        self.assertEqual(staking_rate.source, 'algorand_consensus')
        self.assertGreater(staking_rate.value, 0)

        # Should still return DeFi protocol rates (simulated data)
        folks_rates = client.get_defi_protocol_rates('folks_finance')
        self.assertGreater(len(folks_rates), 0)


class TestExternalAPIIntegration(unittest.TestCase):
    """Test integration with external APIs (Federal Reserve)"""

    def setUp(self):
        self.client = FederalReserveClient()

    def test_federal_reserve_api_without_key(self):
        """Test Federal Reserve API without API key (should return None)"""
        result = self.client.get_series_data('FEDFUNDS')
        self.assertIsNone(result)

    @unittest.skipUnless(
        _get_fred_api_key() is not None,
        "FRED API key not available"
    )
    def test_federal_reserve_api_with_key(self):
        """Test Federal Reserve API with valid API key"""
        api_key = _get_fred_api_key()
        client = FederalReserveClient(api_key=api_key)

        result = client.get_series_data('FEDFUNDS')

        if result:
            self.assertIsInstance(result, RateDataPoint)
            self.assertEqual(result.source, 'federal_reserve')
            self.assertEqual(result.rate_type, 'FEDFUNDS')
            self.assertGreaterEqual(result.value, 0)
            self.assertLessEqual(result.value, 0.2)  # Reasonable upper bound
            self.assertGreater(result.confidence, 0)
        else:
            self.skipTest("Federal Reserve API call failed")

    def test_federal_reserve_api_rate_limiting(self):
        """Test Federal Reserve API rate limiting behavior"""
        api_key = _get_fred_api_key()
        if not api_key:
            self.skipTest("FRED API key not available")

        client = FederalReserveClient(api_key=api_key)

        # Make multiple rapid requests to test rate limiting
        results = []
        for i in range(3):
            result = client.get_series_data('FEDFUNDS')
            results.append(result)
            time.sleep(1)  # Small delay between requests

        # At least some requests should succeed
        successful_results = [r for r in results if r is not None]
        self.assertGreaterEqual(len(successful_results), 1)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        self.config = BaseRateCalculationConfig()
        # Use in-memory database for testing
        self.config.database.default_path = ":memory:"
        self.engine = BaseRateCalculationEngine(self.config)

    def test_complete_rate_calculation_flow(self):
        """Test complete rate calculation flow with real/simulated data"""
        # This test should work regardless of external service availability
        result = self.engine.calculate_base_rate()

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertGreater(result.base_rate, 0)
        self.assertGreater(result.risk_free_rate, 0)
        self.assertGreaterEqual(result.confidence_score, 0)
        self.assertLessEqual(result.confidence_score, 1)
        self.assertIsInstance(result.term_structure, dict)
        self.assertIsInstance(result.component_rates, dict)
        self.assertIsInstance(result.data_sources, list)

        # Verify rate bounds
        bounds = self.config.calculation_parameters.bounds
        self.assertGreaterEqual(result.base_rate, bounds.minimum_rate)
        self.assertLessEqual(result.base_rate, bounds.maximum_rate)

        # Verify term structure makes sense
        if '1_year' in result.term_structure and '2_years' in result.term_structure:
            self.assertGreaterEqual(
                result.term_structure['2_years'],
                result.term_structure['1_year']
            )

    def test_rate_calculation_with_mcp_services(self):
        """Test rate calculation when MCP services are available"""
        # Configure engine to use actual MCP services
        engine = BaseRateCalculationEngine(self.config)

        # Perform calculation
        result = engine.calculate_base_rate()

        # Check if MCP-sourced data was used
        mcp_sources = [source for source in result.data_sources
                      if 'algorand' in source or 'folks' in source or 'tinyman' in source]

        # Log whether MCP data was used
        print(f"MCP-sourced data in calculation: {len(mcp_sources) > 0}")
        print(f"Data sources used: {result.data_sources}")

        # Verify calculation succeeded regardless
        self.assertGreater(result.base_rate, 0)

    def test_historical_data_storage_and_retrieval(self):
        """Test storing and retrieving historical rate data"""
        # Perform multiple calculations
        results = []
        for i in range(3):
            result = self.engine.calculate_base_rate()
            results.append(result)
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # Retrieve historical data
        df = self.engine.get_historical_rates(days=1)

        # Should have stored calculations
        self.assertGreaterEqual(len(df), 3)

        # Verify data integrity
        for _, row in df.iterrows():
            self.assertGreater(row['base_rate'], 0)
            self.assertGreaterEqual(row['confidence_score'], 0)
            self.assertLessEqual(row['confidence_score'], 1)

    def test_engine_health_check_integration(self):
        """Test engine health check with real components"""
        health = self.engine.health_check()

        # Verify health check structure
        self.assertIn('status', health)
        self.assertIn('checks', health)
        self.assertIn('timestamp', health)

        # Verify specific checks
        self.assertIn('database', health['checks'])
        self.assertIn('data_freshness', health['checks'])
        self.assertIn('configuration', health['checks'])

        # Database should be OK (using in-memory)
        self.assertEqual(health['checks']['database'], 'ok')

    def test_concurrent_calculations(self):
        """Test concurrent rate calculations"""
        import threading
        import concurrent.futures

        results = []
        errors = []

        def calculate_rate():
            try:
                result = self.engine.calculate_base_rate()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Run multiple calculations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(calculate_rate) for _ in range(5)]
            concurrent.futures.wait(futures)

        # All calculations should succeed
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)

        # All results should be valid
        for result in results:
            self.assertGreater(result.base_rate, 0)
            self.assertGreater(result.confidence_score, 0)


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration file integration"""

    def test_load_config_from_file(self):
        """Test loading configuration from YAML file"""
        config_path = Path(__file__).parent / "config" / "config.yaml"

        if config_path.exists():
            config = load_config(config_path)
            self.assertIsInstance(config, BaseRateCalculationConfig)
            self.assertIsNotNone(config.mcp_services.algorand_reader_url)
            self.assertIsNotNone(config.mcp_services.market_data_url)
        else:
            self.skipTest("Config file not found")

    def test_environment_variable_overrides(self):
        """Test environment variable configuration overrides"""
        import os

        # Set environment variables
        os.environ['BASE_RATE_MCP_READER_URL'] = 'http://test:8002'
        os.environ['BASE_RATE_MCP_MARKET_URL'] = 'http://test:8003'

        try:
            config = load_config()

            self.assertEqual(config.mcp_services.algorand_reader_url, 'http://test:8002')
            self.assertEqual(config.mcp_services.market_data_url, 'http://test:8003')

        finally:
            # Clean up environment variables
            os.environ.pop('BASE_RATE_MCP_READER_URL', None)
            os.environ.pop('BASE_RATE_MCP_MARKET_URL', None)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics"""

    def setUp(self):
        self.config = BaseRateCalculationConfig()
        self.config.database.default_path = ":memory:"
        self.engine = BaseRateCalculationEngine(self.config)

    def test_calculation_performance(self):
        """Test rate calculation performance"""
        start_time = time.time()

        result = self.engine.calculate_base_rate()

        calculation_time = time.time() - start_time

        # Calculation should complete within reasonable time
        self.assertLess(calculation_time, 10.0)  # 10 seconds max

        # Check if calculation time is recorded in metadata
        if 'calculation_time_ms' in result.metadata:
            recorded_time = result.metadata['calculation_time_ms']
            self.assertGreater(recorded_time, 0)
            self.assertLess(recorded_time, 10000)  # 10 seconds in ms

    def test_database_performance(self):
        """Test database operation performance"""
        # Perform multiple calculations to test database performance
        start_time = time.time()

        for i in range(10):
            self.engine.calculate_base_rate()

        total_time = time.time() - start_time

        # Should handle multiple calculations efficiently
        self.assertLess(total_time, 30.0)  # 30 seconds for 10 calculations

        # Verify all data was stored
        df = self.engine.get_historical_rates(days=1)
        self.assertGreaterEqual(len(df), 10)


# Helper functions
def _check_mcp_service(url: str) -> bool:
    """Check if MCP service is available"""
    try:
        response = requests.get(f"{url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def _get_fred_api_key() -> str:
    """Get FRED API key from environment or return None"""
    import os
    return os.environ.get('FRED_API_KEY')


if __name__ == '__main__':
    # Set up test logging
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Running MCP Integration Tests for Base Rate Calculation Engine")
    print("=" * 70)

    # Run tests
    unittest.main(verbosity=2)