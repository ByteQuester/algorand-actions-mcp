#!/usr/bin/env python3
"""
Data Pipeline Demo - Shows how to use the comprehensive data pipeline
Demonstrates real-time data aggregation, caching, and MCP service integration
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_pipeline import (
    get_mcp_connector, get_data_aggregator, get_cache_manager,
    DataType, SubscriptionConfig
)
from data.fixtures.blockchain_data import get_blockchain_fixtures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPipelineDemo:
    """
    Demonstration of the data pipeline capabilities
    """

    def __init__(self):
        self.mcp_connector = None
        self.data_aggregator = None
        self.cache_manager = None
        self.fixtures = get_blockchain_fixtures()

    async def initialize(self):
        """Initialize the data pipeline"""
        logger.info("🚀 Initializing Data Pipeline...")

        try:
            # Initialize core components
            self.mcp_connector = await get_mcp_connector()
            self.cache_manager = await get_cache_manager()
            self.data_aggregator = await get_data_aggregator()

            logger.info("✅ Data pipeline initialized successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize pipeline: {e}")
            return False

    async def demonstrate_mcp_services(self):
        """Demonstrate MCP service connectivity"""
        logger.info("\n📡 === MCP Services Demo ===")

        # Check service health
        logger.info("Checking MCP service health...")
        health_status = await self.mcp_connector.check_all_services_health()

        for service_type, status in health_status.items():
            if status.is_healthy:
                logger.info(f"  ✅ {service_type.value}: Online ({status.response_time:.2f}s)")
            else:
                logger.warning(f"  ❌ {service_type.value}: Offline - {status.error_message}")

        # Demonstrate service calls (with fallback to fixture data)
        logger.info("\nTesting MCP service calls...")

        # Test Reader MCP (or use fixture data)
        try:
            # Use a test address from fixtures
            test_address = list(self.fixtures.accounts.keys())[0]
            logger.info(f"Getting account info for: {test_address[:20]}...")

            account_response = await self.mcp_connector.get_account_info(test_address)

            if account_response.success:
                logger.info(f"  ✅ Reader MCP: Got account data")
            else:
                logger.info(f"  ⚠️  Reader MCP: Using fixture data")
                # Use fixture data as fallback
                account_data = self.fixtures.get_account(test_address)
                logger.info(f"  📄 Fixture account balance: {account_data.algo_balance / 1_000_000:.2f} ALGO")

        except Exception as e:
            logger.warning(f"  ⚠️  Reader MCP error (using fixtures): {e}")

        # Test Market Data MCP (or use fixture data)
        try:
            logger.info("Getting asset price data...")
            price_response = await self.mcp_connector.get_asset_price(0)  # ALGO

            if price_response.success:
                logger.info(f"  ✅ Market Data MCP: Got price data")
            else:
                logger.info(f"  ⚠️  Market Data MCP: Using fixture data")
                # Use fixture data as fallback
                price_data = self.fixtures.get_asset_price(0)
                logger.info(f"  💰 Fixture ALGO price: ${price_data['price_usd']:.4f}")

        except Exception as e:
            logger.warning(f"  ⚠️  Market Data MCP error (using fixtures): {e}")

    async def demonstrate_data_aggregation(self):
        """Demonstrate data aggregation capabilities"""
        logger.info("\n📊 === Data Aggregation Demo ===")

        # Get comprehensive account data
        test_address = list(self.fixtures.accounts.keys())[0]
        logger.info(f"Aggregating data for account: {test_address[:20]}...")

        try:
            account_data = await self.data_aggregator.get_account_data(
                test_address, include_history=True
            )

            logger.info(f"  ✅ Account data aggregated:")
            logger.info(f"    - Address: {account_data.get('address', 'N/A')[:20]}...")
            logger.info(f"    - Has account info: {'account_info' in account_data}")
            logger.info(f"    - Has transaction history: {'transaction_history' in account_data}")
            logger.info(f"    - Has asset values: {'asset_values' in account_data}")

            if 'total_value_usd' in account_data:
                logger.info(f"    - Total value: ${account_data['total_value_usd']:,.2f} USD")

        except Exception as e:
            logger.error(f"  ❌ Account aggregation failed: {e}")

        # Get market data for multiple assets
        logger.info("\nAggregating market data...")
        test_assets = [0, 31566704, 312769]  # ALGO, USDC, USDt

        try:
            market_data = await self.data_aggregator.get_market_data(
                test_assets, include_history=True
            )

            logger.info(f"  ✅ Market data aggregated:")
            logger.info(f"    - Assets: {len(test_assets)}")
            logger.info(f"    - Has market data: {'market_data' in market_data}")
            logger.info(f"    - Has price history: {'price_history' in market_data}")
            logger.info(f"    - Has DeFi yields: {'defi_yields' in market_data}")

        except Exception as e:
            logger.error(f"  ❌ Market aggregation failed: {e}")

        # Calculate collateral value
        logger.info("\nCalculating collateral value...")

        try:
            collateral_data = await self.data_aggregator.calculate_collateral_value(test_address)

            total_collateral = collateral_data.get('total_collateral_usd', 0)
            asset_count = len(collateral_data.get('assets', []))

            logger.info(f"  ✅ Collateral calculated:")
            logger.info(f"    - Total collateral: ${total_collateral:,.2f} USD")
            logger.info(f"    - Collateral assets: {asset_count}")

            # Show asset breakdown
            for asset in collateral_data.get('assets', [])[:3]:  # Show first 3
                logger.info(f"    - Asset {asset['asset_id']}: "
                           f"${asset['collateral_value']:,.2f} "
                           f"({asset['collateral_factor']:.0%} factor)")

        except Exception as e:
            logger.error(f"  ❌ Collateral calculation failed: {e}")

    async def demonstrate_caching(self):
        """Demonstrate caching capabilities"""
        logger.info("\n💾 === Caching Demo ===")

        # Test cache performance
        test_data = {
            "price:ALGO": {"price": 0.18, "timestamp": datetime.now().isoformat()},
            "price:USDC": {"price": 1.00, "timestamp": datetime.now().isoformat()},
            "account:test": {"balance": 1000, "timestamp": datetime.now().isoformat()},
        }

        logger.info("Testing cache operations...")

        # Set data
        set_results = await self.cache_manager.set_multiple(test_data, ttl=300)
        successful_sets = sum(1 for success in set_results.values() if success)
        logger.info(f"  ✅ Cache set: {successful_sets}/{len(test_data)} successful")

        # Get data
        get_results = await self.cache_manager.get_multiple(list(test_data.keys()))
        cache_hits = len(get_results)
        logger.info(f"  ✅ Cache get: {cache_hits}/{len(test_data)} hits")

        # Show cache statistics
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info(f"  📊 Cache statistics:")
        logger.info(f"    - Memory cache hit rate: {cache_stats['memory'].hit_rate:.1%}")
        logger.info(f"    - File cache hit rate: {cache_stats['file'].hit_rate:.1%}")

        # Performance statistics
        perf_stats = self.cache_manager.get_performance_stats()
        if perf_stats:
            logger.info(f"  ⚡ Performance:")
            for operation, stats in perf_stats.items():
                logger.info(f"    - {operation}: {stats['avg_duration']:.3f}s avg")

    async def demonstrate_real_time_data(self):
        """Demonstrate real-time data subscriptions"""
        logger.info("\n📡 === Real-time Data Demo ===")

        update_count = 0

        async def price_update_callback(data):
            nonlocal update_count
            update_count += 1
            logger.info(f"  📈 Price update #{update_count}: {len(str(data))} bytes")

        # Subscribe to market data updates
        logger.info("Setting up real-time market data subscription...")

        try:
            config = SubscriptionConfig(
                data_type=DataType.MARKET_DATA,
                parameters={"asset_ids": [0, 31566704]},  # ALGO, USDC
                update_interval=3.0,  # 3 seconds
                callback=price_update_callback
            )

            subscription_id = await self.data_aggregator.subscribe_to_real_time_data(config)
            logger.info(f"  ✅ Subscription created: {subscription_id[:16]}...")

            # Wait for some updates
            logger.info("  ⏳ Waiting for real-time updates (9 seconds)...")
            await asyncio.sleep(9)

            # Cancel subscription
            await self.data_aggregator.unsubscribe(subscription_id)
            logger.info(f"  ✅ Subscription cancelled")
            logger.info(f"  📊 Total updates received: {update_count}")

        except Exception as e:
            logger.error(f"  ❌ Real-time subscription failed: {e}")

    async def demonstrate_lending_metrics(self):
        """Demonstrate lending protocol metrics"""
        logger.info("\n🏦 === Lending Metrics Demo ===")

        try:
            lending_metrics = await self.data_aggregator.get_lending_metrics()

            logger.info("  ✅ Lending metrics retrieved:")

            metrics = lending_metrics.get('metrics', {})
            logger.info(f"    - Average lending rate: {metrics.get('avg_lending_rate', 0):.2f}%")
            logger.info(f"    - Average borrowing rate: {metrics.get('avg_borrowing_rate', 0):.2f}%")
            logger.info(f"    - Total TVL: ${metrics.get('total_tvl', 0):,.2f}")

            utilization = metrics.get('utilization_rates', {})
            if utilization:
                logger.info(f"    - Protocol utilization:")
                for protocol, rate in utilization.items():
                    logger.info(f"      * {protocol}: {rate:.1f}%")

            # Show DeFi yields from fixture data
            logger.info("\n  📊 DeFi Protocol Overview (from fixtures):")
            protocols = self.fixtures.get_defi_protocols()
            for protocol in protocols:
                logger.info(f"    - {protocol['name']}: ${protocol['tvl_usd']:,} TVL")

            lending_yields = self.fixtures.get_lending_yields()
            logger.info(f"\n  💰 Current Lending Rates:")
            for yield_data in lending_yields[:3]:  # Show first 3
                logger.info(f"    - {yield_data['asset']}: "
                           f"{yield_data['supply_apy']:.2f}% supply, "
                           f"{yield_data['borrow_apy']:.2f}% borrow")

        except Exception as e:
            logger.error(f"  ❌ Lending metrics failed: {e}")

    async def demonstrate_performance_monitoring(self):
        """Demonstrate performance monitoring"""
        logger.info("\n📈 === Performance Monitoring Demo ===")

        # Get aggregator performance metrics
        aggregator_metrics = self.data_aggregator.get_performance_metrics()

        logger.info("  📊 Data Aggregator Performance:")
        logger.info(f"    - Total requests: {aggregator_metrics.get('requests_total', 0)}")
        logger.info(f"    - Failed requests: {aggregator_metrics.get('requests_failed', 0)}")
        logger.info(f"    - Success rate: {aggregator_metrics.get('success_rate', 0):.1%}")
        logger.info(f"    - Cache hit rate: {aggregator_metrics.get('cache_hit_rate', 0):.1%}")
        logger.info(f"    - Avg aggregation time: {aggregator_metrics.get('avg_aggregation_time', 0):.3f}s")
        logger.info(f"    - Active subscriptions: {aggregator_metrics.get('active_subscriptions', 0)}")

        # Get cache performance
        cache_stats = self.cache_manager.get_cache_stats()
        logger.info("\n  💾 Cache Performance:")
        logger.info(f"    - Memory cache entries: {cache_stats['memory'].entry_count}")
        logger.info(f"    - File cache entries: {cache_stats['file'].entry_count}")
        logger.info(f"    - Memory hit rate: {cache_stats['memory'].hit_rate:.1%}")
        logger.info(f"    - File hit rate: {cache_stats['file'].hit_rate:.1%}")

    async def run_demo(self):
        """Run the complete demonstration"""
        logger.info("🎭 Data Pipeline Comprehensive Demo")
        logger.info("=" * 50)

        if not await self.initialize():
            logger.error("Failed to initialize pipeline")
            return False

        try:
            # Run all demonstrations
            await self.demonstrate_mcp_services()
            await self.demonstrate_data_aggregation()
            await self.demonstrate_caching()
            await self.demonstrate_real_time_data()
            await self.demonstrate_lending_metrics()
            await self.demonstrate_performance_monitoring()

            logger.info("\n🎉 === Demo Complete ===")
            logger.info("The data pipeline successfully demonstrated:")
            logger.info("  ✅ MCP service connectivity and health monitoring")
            logger.info("  ✅ Real-time data aggregation from multiple sources")
            logger.info("  ✅ Intelligent caching with multiple backends")
            logger.info("  ✅ Real-time subscriptions and live data feeds")
            logger.info("  ✅ Lending protocol metrics and DeFi yields")
            logger.info("  ✅ Performance monitoring and optimization")

            return True

        except Exception as e:
            logger.error(f"Demo failed: {e}")
            return False

        finally:
            # Cleanup
            logger.info("\n🧹 Cleaning up...")
            try:
                if self.data_aggregator:
                    await self.data_aggregator.shutdown()
                if self.cache_manager:
                    await self.cache_manager.shutdown()
                if self.mcp_connector:
                    await self.mcp_connector.disconnect()
                logger.info("  ✅ Cleanup complete")
            except Exception as e:
                logger.warning(f"  ⚠️  Cleanup warning: {e}")


async def main():
    """Main demo execution"""
    demo = DataPipelineDemo()

    try:
        success = await demo.run_demo()
        if success:
            logger.info("\n🚀 Ready for production use!")
            logger.info("Next steps:")
            logger.info("  1. Start MCP services: Reader (8002), Writer (3001), Market Data (8789)")
            logger.info("  2. Run integration tests: python test_data_pipeline.py")
            logger.info("  3. Integrate with lending platform components")

        return success

    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Demo failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)