"""
Unit Tests for Base Rate Calculation Engine
"""

import unittest
import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from core.config import BaseRateCalculationConfig, load_config
from core.base_rate_calculation import (
    BaseRateCalculationEngine,
    RateDataPoint,
    BaseRateResult,
    FederalReserveClient,
    AlgorandDataClient,
    TermStructureCalculator,
    calculate_current_base_rate
)


class TestRateDataPoint(unittest.TestCase):
    """Test RateDataPoint dataclass"""

    def test_rate_data_point_creation(self):
        """Test creating a RateDataPoint"""
        rate = RateDataPoint(
            source='test_source',
            rate_type='test_rate',
            value=0.05,
            timestamp=datetime.now(),
            confidence=0.9
        )

        self.assertEqual(rate.source, 'test_source')
        self.assertEqual(rate.rate_type, 'test_rate')
        self.assertEqual(rate.value, 0.05)
        self.assertEqual(rate.confidence, 0.9)
        self.assertEqual(rate.metadata, {})

    def test_rate_data_point_with_metadata(self):
        """Test RateDataPoint with metadata"""
        metadata = {'series_id': 'FEDFUNDS', 'fred_date': '2024-01-01'}
        rate = RateDataPoint(
            source='federal_reserve',
            rate_type='fed_funds',
            value=0.05,
            timestamp=datetime.now(),
            metadata=metadata
        )

        self.assertEqual(rate.metadata, metadata)


class TestBaseRateResult(unittest.TestCase):
    """Test BaseRateResult dataclass"""

    def test_base_rate_result_creation(self):
        """Test creating a BaseRateResult"""
        term_structure = {'1_year': 0.05, '2_years': 0.055}
        component_rates = {'federal_reserve': 0.045, 'algorand_staking': 0.075}

        result = BaseRateResult(
            base_rate=0.055,
            risk_free_rate=0.05,
            term_structure=term_structure,
            confidence_score=0.85,
            component_rates=component_rates,
            data_sources=['federal_reserve', 'algorand_consensus'],
            calculation_timestamp=datetime.now()
        )

        self.assertEqual(result.base_rate, 0.055)
        self.assertEqual(result.risk_free_rate, 0.05)
        self.assertEqual(result.term_structure, term_structure)
        self.assertEqual(result.confidence_score, 0.85)
        self.assertEqual(result.component_rates, component_rates)
        self.assertEqual(len(result.data_sources), 2)


class TestFederalReserveClient(unittest.TestCase):
    """Test Federal Reserve API client"""

    def setUp(self):
        self.client = FederalReserveClient(api_key='test_key')

    @patch('requests.Session.get')
    def test_get_series_data_success(self, mock_get):
        """Test successful API call"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'observations': [{
                'date': '2024-01-01',
                'value': '5.25'
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.get_series_data('FEDFUNDS')

        self.assertIsNotNone(result)
        self.assertEqual(result.source, 'federal_reserve')
        self.assertEqual(result.rate_type, 'FEDFUNDS')
        self.assertEqual(result.value, 0.0525)  # 5.25% converted to decimal
        self.assertEqual(result.confidence, 0.95)

    @patch('requests.Session.get')
    def test_get_series_data_failure(self, mock_get):
        """Test API call failure"""
        mock_get.side_effect = Exception('API Error')

        result = self.client.get_series_data('FEDFUNDS')

        self.assertIsNone(result)

    def test_get_series_data_no_api_key(self):
        """Test API call without API key"""
        client = FederalReserveClient()
        result = client.get_series_data('FEDFUNDS')

        self.assertIsNone(result)


class TestAlgorandDataClient(unittest.TestCase):
    """Test Algorand data client"""

    def setUp(self):
        self.client = AlgorandDataClient(
            algorand_reader_url='http://localhost:8002',
            market_data_url='http://localhost:8003'
        )

    def test_get_staking_rewards(self):
        """Test getting Algorand staking rewards"""
        result = self.client.get_staking_rewards()

        self.assertIsNotNone(result)
        self.assertEqual(result.source, 'algorand_consensus')
        self.assertEqual(result.rate_type, 'staking_rewards')
        self.assertGreater(result.value, 0)
        self.assertEqual(result.confidence, 0.9)

    def test_get_defi_protocol_rates_folks_finance(self):
        """Test getting Folks Finance rates"""
        rates = self.client.get_defi_protocol_rates('folks_finance')

        self.assertGreater(len(rates), 0)
        algo_rate = next((r for r in rates if 'ALGO' in r.rate_type), None)
        self.assertIsNotNone(algo_rate)
        self.assertEqual(algo_rate.source, 'folks_finance')

    def test_get_defi_protocol_rates_tinyman(self):
        """Test getting Tinyman LP rates"""
        rates = self.client.get_defi_protocol_rates('tinyman')

        self.assertGreater(len(rates), 0)
        lp_rate = next((r for r in rates if 'ALGO_USDC' in r.rate_type), None)
        self.assertIsNotNone(lp_rate)
        self.assertEqual(lp_rate.source, 'tinyman')

    def test_get_defi_protocol_rates_unknown(self):
        """Test getting rates for unknown protocol"""
        rates = self.client.get_defi_protocol_rates('unknown_protocol')

        self.assertEqual(len(rates), 0)


class TestTermStructureCalculator(unittest.TestCase):
    """Test term structure calculator"""

    def setUp(self):
        self.config = BaseRateCalculationConfig()
        self.calculator = TermStructureCalculator(self.config)

    def test_calculate_term_structure(self):
        """Test term structure calculation"""
        base_rate = 0.05

        term_structure = self.calculator.calculate_term_structure(base_rate)

        self.assertIn('1_day', term_structure)
        self.assertIn('1_year', term_structure)
        self.assertGreaterEqual(term_structure['1_year'], base_rate)
        self.assertGreaterEqual(term_structure['5_years'], term_structure['1_year'])

    def test_interpolate_curve(self):
        """Test yield curve interpolation"""
        known_points = {0.25: 0.04, 1.0: 0.045, 2.0: 0.05}

        interpolated = self.calculator.interpolate_curve(known_points)

        self.assertGreater(len(interpolated), 0)
        # Check that interpolated values are reasonable
        for term, rate in interpolated.items():
            self.assertGreaterEqual(rate, 0.035)
            self.assertLessEqual(rate, 0.055)

    def test_interpolate_curve_insufficient_points(self):
        """Test interpolation with insufficient data points"""
        known_points = {1.0: 0.05}

        interpolated = self.calculator.interpolate_curve(known_points)

        self.assertEqual(len(interpolated), 0)


class TestBaseRateCalculationEngine(unittest.TestCase):
    """Test main base rate calculation engine"""

    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # Create test config
        self.config = BaseRateCalculationConfig()
        self.config.database.default_path = self.temp_db.name

        self.engine = BaseRateCalculationEngine(self.config)

    def tearDown(self):
        # Clean up temporary database
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_engine_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine.config)
        self.assertIsNotNone(self.engine.fed_client)
        self.assertIsNotNone(self.engine.algorand_client)
        self.assertIsNotNone(self.engine.term_calculator)

    def test_database_initialization(self):
        """Test database table creation"""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

        self.assertIn('rate_history', tables)
        self.assertIn('base_rate_calculations', tables)

    @patch.object(BaseRateCalculationEngine, 'fetch_federal_reserve_rates')
    @patch.object(BaseRateCalculationEngine, 'fetch_algorand_rates')
    def test_calculate_base_rate_success(self, mock_algo_rates, mock_fed_rates):
        """Test successful base rate calculation"""
        # Mock rate data
        mock_fed_rates.return_value = [
            RateDataPoint('federal_reserve', 'FEDFUNDS', 0.05, datetime.now(), 0.95)
        ]
        mock_algo_rates.return_value = [
            RateDataPoint('algorand_consensus', 'staking_rewards', 0.075, datetime.now(), 0.9)
        ]

        result = self.engine.calculate_base_rate()

        self.assertIsInstance(result, BaseRateResult)
        self.assertGreater(result.base_rate, 0)
        self.assertGreater(result.confidence_score, 0)
        self.assertIn('federal_reserve', result.component_rates)

    @patch.object(BaseRateCalculationEngine, 'fetch_federal_reserve_rates')
    @patch.object(BaseRateCalculationEngine, 'fetch_algorand_rates')
    def test_calculate_base_rate_no_data(self, mock_algo_rates, mock_fed_rates):
        """Test base rate calculation with no data (fallback)"""
        mock_fed_rates.return_value = []
        mock_algo_rates.return_value = []

        result = self.engine.calculate_base_rate()

        self.assertIsInstance(result, BaseRateResult)
        self.assertEqual(result.base_rate, 0.05)  # Fallback rate
        self.assertEqual(result.confidence_score, 0.1)
        self.assertIn('emergency_fallback', result.data_sources)

    def test_calculate_weighted_average(self):
        """Test weighted average calculation"""
        rates = [
            RateDataPoint('source1', 'rate1', 0.04, datetime.now(), 1.0),
            RateDataPoint('source2', 'rate2', 0.06, datetime.now(), 1.0)
        ]
        weights = {'source1': 0.6, 'source2': 0.4}

        avg = self.engine.calculate_weighted_average(rates, weights)

        expected = 0.04 * 0.6 + 0.06 * 0.4
        self.assertAlmostEqual(avg, expected, places=6)

    def test_calculate_weighted_average_empty(self):
        """Test weighted average with empty rates"""
        avg = self.engine.calculate_weighted_average([], {})
        self.assertEqual(avg, 0.0)

    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        rates = [
            RateDataPoint('source1', 'rate1', 0.05, datetime.now(), 0.95),
            RateDataPoint('source2', 'rate2', 0.05, datetime.now() - timedelta(hours=1), 0.9)
        ]

        confidence = self.engine.calculate_confidence_score(rates)

        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 1)

    def test_store_and_retrieve_rate_data(self):
        """Test storing and retrieving rate data"""
        rates = [
            RateDataPoint('test_source', 'test_rate', 0.05, datetime.now(), 0.9, {'test': 'metadata'})
        ]

        self.engine._store_rate_data(rates)

        # Verify data was stored
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM rate_history')
            count = cursor.fetchone()[0]

        self.assertEqual(count, 1)

    def test_get_historical_rates(self):
        """Test getting historical rates"""
        # Create a calculation result to store
        result = BaseRateResult(
            base_rate=0.055,
            risk_free_rate=0.05,
            term_structure={'1_year': 0.055},
            confidence_score=0.85,
            component_rates={'test': 0.05},
            data_sources=['test'],
            calculation_timestamp=datetime.now()
        )

        self.engine._store_calculation_result(result)

        # Retrieve historical data
        df = self.engine.get_historical_rates(days=7)

        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df.iloc[0]['base_rate'], 0.055, places=6)

    def test_health_check(self):
        """Test engine health check"""
        health = self.engine.health_check()

        self.assertIn('status', health)
        self.assertIn('checks', health)
        self.assertIn('database', health['checks'])
        self.assertIn('timestamp', health)

    @patch.object(BaseRateCalculationEngine, 'calculate_base_rate')
    def test_get_current_rate_calculate_new(self, mock_calculate):
        """Test getting current rate when calculation is needed"""
        mock_result = BaseRateResult(
            base_rate=0.055,
            risk_free_rate=0.05,
            term_structure={'1_year': 0.055},
            confidence_score=0.85,
            component_rates={'test': 0.05},
            data_sources=['test'],
            calculation_timestamp=datetime.now()
        )
        mock_calculate.return_value = mock_result

        result = self.engine.get_current_rate(max_age_minutes=15)

        self.assertEqual(result, mock_result)
        mock_calculate.assert_called_once()

    def test_get_current_rate_use_cached(self):
        """Test getting current rate when cached data is available"""
        # Store a recent calculation
        result = BaseRateResult(
            base_rate=0.055,
            risk_free_rate=0.05,
            term_structure={'1_year': 0.055},
            confidence_score=0.85,
            component_rates={'test': 0.05},
            data_sources=['test'],
            calculation_timestamp=datetime.now()
        )
        self.engine._store_calculation_result(result)

        # Get current rate (should use cached)
        current = self.engine.get_current_rate(max_age_minutes=15)

        self.assertIsNotNone(current)
        self.assertAlmostEqual(current.base_rate, 0.055, places=6)


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration integration"""

    def test_load_default_config(self):
        """Test loading default configuration"""
        config = load_config()

        self.assertIsInstance(config, BaseRateCalculationConfig)
        self.assertIsNotNone(config.mcp_services)
        self.assertIsNotNone(config.federal_reserve_rates)
        self.assertIsNotNone(config.algorand_defi_rates)

    def test_engine_with_custom_config(self):
        """Test engine with custom configuration"""
        config = BaseRateCalculationConfig()
        config.calculation_parameters.update_frequency_minutes = 30

        engine = BaseRateCalculationEngine(config)

        self.assertEqual(engine.config.calculation_parameters.update_frequency_minutes, 30)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""

    @patch('core.base_rate_calculation.BaseRateCalculationEngine')
    def test_calculate_current_base_rate(self, mock_engine_class):
        """Test convenience function for calculating current base rate"""
        mock_engine = Mock()
        mock_result = BaseRateResult(
            base_rate=0.055,
            risk_free_rate=0.05,
            term_structure={'1_year': 0.055},
            confidence_score=0.85,
            component_rates={'test': 0.05},
            data_sources=['test'],
            calculation_timestamp=datetime.now()
        )
        mock_engine.calculate_base_rate.return_value = mock_result
        mock_engine_class.return_value = mock_engine

        result = calculate_current_base_rate()

        self.assertEqual(result, mock_result)
        mock_engine.calculate_base_rate.assert_called_once()


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""

    def setUp(self):
        self.config = BaseRateCalculationConfig()
        self.config.database.default_path = ":memory:"  # Use in-memory database
        self.engine = BaseRateCalculationEngine(self.config)

    @patch('core.base_rate_calculation.FederalReserveClient.get_series_data')
    def test_federal_reserve_api_error(self, mock_get_data):
        """Test handling of Federal Reserve API errors"""
        mock_get_data.side_effect = Exception('API Error')

        fed_rates = self.engine.fetch_federal_reserve_rates()

        # Should still return fallback rates
        self.assertGreater(len(fed_rates), 0)
        # Check that fallback rates are used
        fallback_rate = next((r for r in fed_rates if 'fallback' in r.source), None)
        self.assertIsNotNone(fallback_rate)

    def test_database_error_handling(self):
        """Test handling of database errors"""
        # Use invalid database path
        self.engine.db_path = Path('/invalid/path/db.sqlite')

        # Health check should detect database issues
        health = self.engine.health_check()

        self.assertIn('error', health['checks']['database'])
        self.assertEqual(health['status'], 'degraded')


if __name__ == '__main__':
    # Set up test logging
    import logging
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    unittest.main(verbosity=2)