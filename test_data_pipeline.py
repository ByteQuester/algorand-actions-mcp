#!/usr/bin/env python3
"""
Data Pipeline Integration Test
Tests the complete data pipeline with real Algorand blockchain data
"""

import asyncio
import json
import logging
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_pipeline.mcp_connector import MCPConnector, MCPServiceType, get_mcp_connector
from src.data_pipeline.data_aggregator import DataAggregator, DataType, SubscriptionConfig, get_data_aggregator
from src.data_pipeline.cache_manager import CacheManager, CacheBackend, get_cache_manager
from data.fixtures.blockchain_data import get_blockchain_fixtures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPipelineIntegrationTest:
    """
    Comprehensive test suite for the data pipeline
    """

    def __init__(self):
        self.mcp_connector: MCPConnector = None
        self.data_aggregator: DataAggregator = None
        self.cache_manager: CacheManager = None
        self.fixtures = get_blockchain_fixtures()

        self.test_results = {}
        self.start_time = None

    async def setup(self):
        """Setup test environment"""
        logger.info("Setting up data pipeline test environment...")
        self.start_time = time.time()

        try:
            # Initialize components
            self.mcp_connector = await get_mcp_connector()
            self.cache_manager = await get_cache_manager()
            self.data_aggregator = await get_data_aggregator()

            logger.info("✓ Data pipeline components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to setup test environment: {e}")
            return False

    async def teardown(self):
        """Cleanup test environment"""
        logger.info("Cleaning up test environment...")

        try:
            if self.data_aggregator:
                await self.data_aggregator.shutdown()
            if self.cache_manager:
                await self.cache_manager.shutdown()
            if self.mcp_connector:
                await self.mcp_connector.disconnect()

            logger.info("✓ Test environment cleaned up successfully")

        except Exception as e:
            logger.error(f"✗ Error during cleanup: {e}")

    async def test_mcp_service_health(self):
        """Test MCP service health and connectivity"""
        logger.info("\n=== Testing MCP Service Health ===")

        try:
            health_status = await self.mcp_connector.check_all_services_health()

            for service_type, status in health_status.items():
                if status.is_healthy:
                    logger.info(f"✓ {service_type.value}: Healthy "
                               f"({status.response_time:.2f}s)")
                else:
                    logger.warning(f"✗ {service_type.value}: Unhealthy - "
                                 f"{status.error_message}")

            healthy_services = [st for st, s in health_status.items() if s.is_healthy]

            self.test_results['mcp_health'] = {
                'total_services': len(health_status),
                'healthy_services': len(healthy_services),
                'service_status': {st.value: s.is_healthy for st, s in health_status.items()}
            }

            return len(healthy_services) > 0

        except Exception as e:
            logger.error(f"✗ MCP health check failed: {e}")
            self.test_results['mcp_health'] = {'error': str(e)}
            return False

    async def test_cache_performance(self):
        """Test cache manager performance"""
        logger.info("\n=== Testing Cache Performance ===")

        try:
            # Test data
            test_data = {
                f"test_key_{i}": {"value": f"test_value_{i}", "timestamp": datetime.now().isoformat()}
                for i in range(100)
            }

            # Test batch set
            start_time = time.time()
            set_results = await self.cache_manager.set_multiple(test_data, ttl=300)
            set_time = time.time() - start_time

            successful_sets = sum(1 for success in set_results.values() if success)
            logger.info(f"✓ Batch set: {successful_sets}/{len(test_data)} successful "
                       f"({set_time:.3f}s)")

            # Test batch get
            start_time = time.time()
            get_results = await self.cache_manager.get_multiple(list(test_data.keys()))
            get_time = time.time() - start_time

            cache_hits = len(get_results)
            logger.info(f"✓ Batch get: {cache_hits}/{len(test_data)} cache hits "
                       f"({get_time:.3f}s)")

            # Get cache statistics
            cache_stats = self.cache_manager.get_cache_stats()
            perf_stats = self.cache_manager.get_performance_stats()

            self.test_results['cache_performance'] = {
                'set_time': set_time,
                'get_time': get_time,
                'cache_hit_rate': cache_hits / len(test_data),
                'cache_stats': {
                    'memory': {
                        'hits': cache_stats['memory'].hits,
                        'misses': cache_stats['memory'].misses,
                        'hit_rate': cache_stats['memory'].hit_rate
                    },
                    'file': {
                        'hits': cache_stats['file'].hits,
                        'misses': cache_stats['file'].misses,
                        'hit_rate': cache_stats['file'].hit_rate
                    }
                },
                'performance_stats': perf_stats
            }

            return cache_hits > 0

        except Exception as e:
            logger.error(f"✗ Cache performance test failed: {e}")
            self.test_results['cache_performance'] = {'error': str(e)}
            return False

    async def test_account_data_aggregation(self):
        """Test account data aggregation"""
        logger.info("\n=== Testing Account Data Aggregation ===")

        try:
            # Use fixture data for testing
            test_addresses = list(self.fixtures.accounts.keys())[:2]  # Test first 2 accounts

            results = []
            for address in test_addresses:
                try:
                    start_time = time.time()
                    account_data = await self.data_aggregator.get_account_data(
                        address, include_history=True
                    )
                    processing_time = time.time() - start_time

                    logger.info(f"✓ Account {address[:20]}... processed "
                               f"({processing_time:.2f}s)")

                    # Validate data structure
                    required_fields = ['address', 'account_info', 'timestamp']
                    missing_fields = [field for field in required_fields
                                    if field not in account_data]

                    if missing_fields:
                        logger.warning(f"  Missing fields: {missing_fields}")
                    else:
                        logger.info(f"  ✓ All required fields present")

                    results.append({
                        'address': address,
                        'processing_time': processing_time,
                        'has_assets': 'asset_values' in account_data,
                        'has_history': 'transaction_history' in account_data,
                        'data_size': len(str(account_data))
                    })

                except Exception as e:
                    logger.error(f"✗ Failed to process account {address}: {e}")
                    results.append({'address': address, 'error': str(e)})

            self.test_results['account_aggregation'] = {
                'total_accounts': len(test_addresses),
                'successful_accounts': len([r for r in results if 'error' not in r]),
                'avg_processing_time': sum(r.get('processing_time', 0) for r in results) / len(results),
                'results': results
            }

            return len([r for r in results if 'error' not in r]) > 0

        except Exception as e:
            logger.error(f"✗ Account data aggregation test failed: {e}")
            self.test_results['account_aggregation'] = {'error': str(e)}
            return False

    async def test_market_data_aggregation(self):
        """Test market data aggregation"""
        logger.info("\n=== Testing Market Data Aggregation ===")

        try:
            # Test with fixture asset IDs
            test_asset_ids = [0, 31566704, 312769]  # ALGO, USDC, USDt

            start_time = time.time()
            market_data = await self.data_aggregator.get_market_data(
                test_asset_ids, include_history=True
            )
            processing_time = time.time() - start_time

            logger.info(f"✓ Market data processed for {len(test_asset_ids)} assets "
                       f"({processing_time:.2f}s)")

            # Validate data structure
            required_fields = ['asset_ids', 'market_data', 'timestamp']
            missing_fields = [field for field in required_fields
                            if field not in market_data]

            if missing_fields:
                logger.warning(f"  Missing fields: {missing_fields}")
            else:
                logger.info(f"  ✓ All required fields present")

            # Check for additional data
            has_history = 'price_history' in market_data
            has_yields = 'defi_yields' in market_data

            logger.info(f"  Price history: {'✓' if has_history else '✗'}")
            logger.info(f"  DeFi yields: {'✓' if has_yields else '✗'}")

            self.test_results['market_aggregation'] = {
                'processing_time': processing_time,
                'asset_count': len(test_asset_ids),
                'has_history': has_history,
                'has_yields': has_yields,
                'data_size': len(str(market_data))
            }

            return True

        except Exception as e:
            logger.error(f"✗ Market data aggregation test failed: {e}")
            self.test_results['market_aggregation'] = {'error': str(e)}
            return False

    async def test_collateral_calculation(self):
        """Test collateral value calculation"""
        logger.info("\n=== Testing Collateral Calculation ===")

        try:
            # Test with high-value accounts from fixtures
            high_value_accounts = self.fixtures.get_high_value_accounts(10000)  # $10k+
            test_addresses = high_value_accounts[:2]  # Test first 2

            results = []
            for address in test_addresses:
                try:
                    start_time = time.time()
                    collateral_data = await self.data_aggregator.calculate_collateral_value(address)
                    processing_time = time.time() - start_time

                    total_collateral = collateral_data.get('total_collateral_usd', 0)
                    asset_count = len(collateral_data.get('assets', []))

                    logger.info(f"✓ Collateral for {address[:20]}...: "
                               f"${total_collateral:,.2f} ({asset_count} assets, "
                               f"{processing_time:.2f}s)")

                    results.append({
                        'address': address,
                        'total_collateral_usd': total_collateral,
                        'asset_count': asset_count,
                        'processing_time': processing_time
                    })

                except Exception as e:
                    logger.error(f"✗ Failed to calculate collateral for {address}: {e}")
                    results.append({'address': address, 'error': str(e)})

            successful = [r for r in results if 'error' not in r]
            total_collateral = sum(r['total_collateral_usd'] for r in successful)

            self.test_results['collateral_calculation'] = {
                'total_accounts': len(test_addresses),
                'successful_accounts': len(successful),
                'total_collateral_usd': total_collateral,
                'avg_processing_time': sum(r.get('processing_time', 0) for r in results) / len(results),
                'results': results
            }

            return len(successful) > 0

        except Exception as e:
            logger.error(f"✗ Collateral calculation test failed: {e}")
            self.test_results['collateral_calculation'] = {'error': str(e)}
            return False

    async def test_lending_metrics(self):
        """Test lending metrics aggregation"""
        logger.info("\n=== Testing Lending Metrics ===")

        try:
            start_time = time.time()
            lending_metrics = await self.data_aggregator.get_lending_metrics()
            processing_time = time.time() - start_time

            logger.info(f"✓ Lending metrics processed ({processing_time:.2f}s)")

            # Validate metrics structure
            metrics = lending_metrics.get('metrics', {})
            avg_lending_rate = metrics.get('avg_lending_rate', 0)
            avg_borrowing_rate = metrics.get('avg_borrowing_rate', 0)
            total_tvl = metrics.get('total_tvl', 0)

            logger.info(f"  Average lending rate: {avg_lending_rate:.2f}%")
            logger.info(f"  Average borrowing rate: {avg_borrowing_rate:.2f}%")
            logger.info(f"  Total TVL: ${total_tvl:,.2f}")

            utilization_rates = metrics.get('utilization_rates', {})
            logger.info(f"  Protocols tracked: {len(utilization_rates)}")

            self.test_results['lending_metrics'] = {
                'processing_time': processing_time,
                'avg_lending_rate': avg_lending_rate,
                'avg_borrowing_rate': avg_borrowing_rate,
                'total_tvl': total_tvl,
                'protocol_count': len(utilization_rates)
            }

            return True

        except Exception as e:
            logger.error(f"✗ Lending metrics test failed: {e}")
            self.test_results['lending_metrics'] = {'error': str(e)}
            return False

    async def test_real_time_subscriptions(self):
        """Test real-time data subscriptions"""
        logger.info("\n=== Testing Real-time Subscriptions ===")

        try:
            received_updates = []

            async def test_callback(data):
                received_updates.append(data)
                logger.info(f"  📡 Received update: {len(str(data))} bytes")

            # Subscribe to market data updates
            config = SubscriptionConfig(
                data_type=DataType.MARKET_DATA,
                parameters={"asset_ids": [0, 31566704]},
                update_interval=2.0,  # 2 seconds for testing
                callback=test_callback
            )

            subscription_id = await self.data_aggregator.subscribe_to_real_time_data(config)
            logger.info(f"✓ Subscription created: {subscription_id}")

            # Wait for a few updates
            await asyncio.sleep(6)

            # Unsubscribe
            await self.data_aggregator.unsubscribe(subscription_id)
            logger.info(f"✓ Subscription cancelled")

            self.test_results['real_time_subscriptions'] = {
                'subscription_created': True,
                'updates_received': len(received_updates),
                'test_duration': 6
            }

            return True

        except Exception as e:
            logger.error(f"✗ Real-time subscription test failed: {e}")
            self.test_results['real_time_subscriptions'] = {'error': str(e)}
            return False

    async def test_transaction_simulation(self):
        """Test transaction simulation"""
        logger.info("\n=== Testing Transaction Simulation ===")

        try:
            # Use fixture accounts for simulation
            test_accounts = list(self.fixtures.accounts.keys())[:2]

            if len(test_accounts) < 2:
                logger.warning("Not enough test accounts for simulation")
                return False

            sender = test_accounts[0]
            receiver = test_accounts[1]

            # Simulate a payment transaction
            transaction_data = {
                "type": "pay",
                "sender": sender,
                "receiver": receiver,
                "amount": 1000000,  # 1 ALGO
                "fee": 1000
            }

            start_time = time.time()
            simulation_result = await self.data_aggregator.simulate_transaction_impact(
                transaction_data
            )
            processing_time = time.time() - start_time

            logger.info(f"✓ Transaction simulation completed ({processing_time:.2f}s)")

            has_simulation = 'simulation' in simulation_result
            has_fee_estimate = 'estimated_fee' in simulation_result

            logger.info(f"  Simulation data: {'✓' if has_simulation else '✗'}")
            logger.info(f"  Fee estimate: {'✓' if has_fee_estimate else '✗'}")

            self.test_results['transaction_simulation'] = {
                'processing_time': processing_time,
                'has_simulation': has_simulation,
                'has_fee_estimate': has_fee_estimate,
                'sender': sender[:20] + "...",
                'receiver': receiver[:20] + "..."
            }

            return True

        except Exception as e:
            logger.error(f"✗ Transaction simulation test failed: {e}")
            self.test_results['transaction_simulation'] = {'error': str(e)}
            return False

    async def test_performance_metrics(self):
        """Test performance metrics collection"""
        logger.info("\n=== Testing Performance Metrics ===")

        try:
            # Get aggregator performance metrics
            aggregator_metrics = self.data_aggregator.get_performance_metrics()
            logger.info(f"✓ Aggregator metrics collected")

            # Get cache performance metrics
            cache_perf = self.cache_manager.get_performance_stats()
            cache_stats = self.cache_manager.get_cache_stats()
            logger.info(f"✓ Cache metrics collected")

            # Log key metrics
            logger.info(f"  Requests total: {aggregator_metrics.get('requests_total', 0)}")
            logger.info(f"  Success rate: {aggregator_metrics.get('success_rate', 0):.2%}")
            logger.info(f"  Cache hit rate: {aggregator_metrics.get('cache_hit_rate', 0):.2%}")
            logger.info(f"  Avg aggregation time: {aggregator_metrics.get('avg_aggregation_time', 0):.3f}s")

            self.test_results['performance_metrics'] = {
                'aggregator_metrics': aggregator_metrics,
                'cache_performance': cache_perf,
                'cache_stats': {
                    'memory_hit_rate': cache_stats['memory'].hit_rate,
                    'file_hit_rate': cache_stats['file'].hit_rate
                }
            }

            return True

        except Exception as e:
            logger.error(f"✗ Performance metrics test failed: {e}")
            self.test_results['performance_metrics'] = {'error': str(e)}
            return False

    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting Data Pipeline Integration Tests")
        logger.info("=" * 60)

        if not await self.setup():
            logger.error("Failed to setup test environment")
            return False

        tests = [
            ("MCP Service Health", self.test_mcp_service_health),
            ("Cache Performance", self.test_cache_performance),
            ("Account Data Aggregation", self.test_account_data_aggregation),
            ("Market Data Aggregation", self.test_market_data_aggregation),
            ("Collateral Calculation", self.test_collateral_calculation),
            ("Lending Metrics", self.test_lending_metrics),
            ("Real-time Subscriptions", self.test_real_time_subscriptions),
            ("Transaction Simulation", self.test_transaction_simulation),
            ("Performance Metrics", self.test_performance_metrics),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                logger.info(f"\n--- Running {test_name} ---")
                if await test_func():
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    failed += 1
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                failed += 1
                logger.error(f"❌ {test_name}: FAILED with exception: {e}")

        # Summary
        total_time = time.time() - self.start_time
        logger.info("\n" + "=" * 60)
        logger.info("🏁 Test Summary")
        logger.info("=" * 60)
        logger.info(f"Total tests: {len(tests)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success rate: {passed/len(tests):.1%}")
        logger.info(f"Total time: {total_time:.2f}s")

        # Save detailed results
        self.test_results['summary'] = {
            'total_tests': len(tests),
            'passed': passed,
            'failed': failed,
            'success_rate': passed/len(tests),
            'total_time': total_time,
            'timestamp': datetime.now().isoformat()
        }

        # Export results
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        logger.info("📄 Detailed results saved to test_results.json")

        await self.teardown()
        return failed == 0


async def main():
    """Main test execution"""
    test_suite = DataPipelineIntegrationTest()

    try:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        await test_suite.teardown()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        await test_suite.teardown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())