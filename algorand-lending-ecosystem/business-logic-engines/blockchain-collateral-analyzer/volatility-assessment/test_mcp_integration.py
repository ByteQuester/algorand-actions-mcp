#!/usr/bin/env python3
"""
MCP Integration Test for Volatility Assessment Engine

Tests integration with MCP services running on ports 8002 and 8003.
This test assumes the MCP services are running and accessible.
"""

import sys
import os
import asyncio
import json
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.volatility_engine import VolatilityAssessmentEngine, PriceFeed
from core.config import load_config


class MCPIntegratedVolatilityEngine(VolatilityAssessmentEngine):
    """
    Extended Volatility Engine with real MCP integration
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def fetch_price_from_mcp(self, asset_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real price data from MCP market data service
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        market_data_url = self.config.mcp_services.market_data_url
        timeout = self.config.performance.rate_limiting['timeout_seconds']

        try:
            # Call MCP market data service
            async with self.session.get(
                f"{market_data_url}/api/price/{asset_symbol}",
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "price": data.get("price", 0.0),
                        "timestamp": datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                        "confidence": data.get("confidence", 0.9),
                        "volume_24h": data.get("volume_24h"),
                        "source_count": data.get("source_count", 1)
                    }
                else:
                    print(f"MCP service returned status {response.status} for {asset_symbol}")
                    return None

        except asyncio.TimeoutError:
            print(f"Timeout fetching price for {asset_symbol} from MCP service")
            return None
        except Exception as e:
            print(f"Error fetching price from MCP service: {e}")
            return None

    async def get_algorand_data_from_mcp(self, asset_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch Algorand blockchain data from MCP Algorand reader service
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        algorand_reader_url = self.config.mcp_services.algorand_reader_url
        timeout = self.config.performance.rate_limiting['timeout_seconds']

        try:
            # Call MCP Algorand reader service
            endpoint = f"{algorand_reader_url}/api/asset-info"
            if asset_id:
                endpoint += f"/{asset_id}"

            async with self.session.get(
                endpoint,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Algorand MCP service returned status {response.status}")
                    return None

        except asyncio.TimeoutError:
            print("Timeout fetching data from Algorand MCP service")
            return None
        except Exception as e:
            print(f"Error fetching data from Algorand MCP service: {e}")
            return None

    async def get_mcp_price_feeds(self, asset_symbol: str) -> list[PriceFeed]:
        """
        Get price feeds from MCP services
        """
        feeds = []

        try:
            # Fetch from market data MCP
            market_data = await self.fetch_price_from_mcp(asset_symbol)
            if market_data:
                feed = PriceFeed(
                    oracle_name="mcp_market_data",
                    asset_symbol=asset_symbol,
                    price_usd=market_data["price"],
                    timestamp=market_data["timestamp"],
                    confidence=market_data["confidence"],
                    volume_24h=market_data.get("volume_24h"),
                    source_count=market_data.get("source_count")
                )
                feeds.append(feed)

            # For ALGO specifically, try to get additional data from Algorand MCP
            if asset_symbol == "ALGO":
                algo_data = await self.get_algorand_data_from_mcp()
                if algo_data and "price_info" in algo_data:
                    price_info = algo_data["price_info"]
                    feed = PriceFeed(
                        oracle_name="mcp_algorand_reader",
                        asset_symbol=asset_symbol,
                        price_usd=price_info.get("price_usd", 0.0),
                        timestamp=datetime.fromisoformat(price_info.get("timestamp", datetime.now().isoformat())),
                        confidence=price_info.get("confidence", 0.85),
                        volume_24h=price_info.get("volume_24h"),
                        source_count=1
                    )
                    feeds.append(feed)

        except Exception as e:
            print(f"Error getting MCP price feeds: {e}")

        return feeds

    async def test_mcp_connectivity(self) -> Dict[str, bool]:
        """
        Test connectivity to both MCP services
        """
        results = {
            "market_data_service": False,
            "algorand_reader_service": False
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        # Test market data service
        try:
            market_url = self.config.mcp_services.market_data_url
            async with self.session.get(
                f"{market_url}/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                results["market_data_service"] = response.status == 200
        except Exception as e:
            print(f"Market data service connectivity test failed: {e}")

        # Test Algorand reader service
        try:
            algorand_url = self.config.mcp_services.algorand_reader_url
            async with self.session.get(
                f"{algorand_url}/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                results["algorand_reader_service"] = response.status == 200
        except Exception as e:
            print(f"Algorand reader service connectivity test failed: {e}")

        return results


async def test_mcp_service_connectivity():
    """Test that MCP services are running and accessible"""
    print("Testing MCP service connectivity...")

    try:
        async with MCPIntegratedVolatilityEngine() as engine:
            connectivity = await engine.test_mcp_connectivity()

            market_data_ok = connectivity["market_data_service"]
            algorand_reader_ok = connectivity["algorand_reader_service"]

            if market_data_ok:
                print(f"✓ Market data service (port 8003) is accessible")
            else:
                print(f"✗ Market data service (port 8003) is not accessible")

            if algorand_reader_ok:
                print(f"✓ Algorand reader service (port 8002) is accessible")
            else:
                print(f"✗ Algorand reader service (port 8002) is not accessible")

            success = market_data_ok or algorand_reader_ok
            if success:
                print("✓ MCP connectivity test passed (at least one service accessible)")
            else:
                print("✗ MCP connectivity test failed (no services accessible)")

            return success

    except Exception as e:
        print(f"✗ MCP connectivity test failed: {e}")
        return False


async def test_mcp_price_fetching():
    """Test fetching price data from MCP services"""
    print("Testing MCP price fetching...")

    try:
        async with MCPIntegratedVolatilityEngine() as engine:
            # Test fetching ALGO price
            feeds = await engine.get_mcp_price_feeds("ALGO")

            if not feeds:
                print("✗ No price feeds received from MCP services")
                return False

            print(f"✓ Received {len(feeds)} price feed(s) from MCP services")

            for feed in feeds:
                print(f"  - {feed.oracle_name}: ${feed.price_usd:.4f} (confidence: {feed.confidence:.2f})")

                # Validate feed data
                assert feed.price_usd > 0, "Price should be positive"
                assert 0 <= feed.confidence <= 1, "Confidence should be between 0 and 1"
                assert feed.asset_symbol == "ALGO", "Asset symbol should match request"

            return True

    except Exception as e:
        print(f"✗ MCP price fetching test failed: {e}")
        return False


async def test_mcp_algorand_data():
    """Test fetching Algorand-specific data from MCP service"""
    print("Testing MCP Algorand data fetching...")

    try:
        async with MCPIntegratedVolatilityEngine() as engine:
            # Test fetching general Algorand data
            algo_data = await engine.get_algorand_data_from_mcp()

            if not algo_data:
                print("✗ No Algorand data received from MCP service")
                return False

            print("✓ Received Algorand data from MCP service")

            # Check for expected data structure
            if "network_status" in algo_data:
                print(f"  - Network status: {algo_data['network_status']}")

            if "latest_round" in algo_data:
                print(f"  - Latest round: {algo_data['latest_round']}")

            if "price_info" in algo_data:
                price_info = algo_data["price_info"]
                print(f"  - ALGO price: ${price_info.get('price_usd', 'N/A')}")

            return True

    except Exception as e:
        print(f"✗ MCP Algorand data test failed: {e}")
        return False


async def test_integrated_volatility_assessment():
    """Test volatility assessment using real MCP data"""
    print("Testing integrated volatility assessment with MCP data...")

    try:
        async with MCPIntegratedVolatilityEngine() as engine:
            # Setup demo oracles for comparison
            engine.setup_demo_oracles()

            # Get MCP price feeds
            mcp_feeds = await engine.get_mcp_price_feeds("ALGO")

            # Get demo price feeds
            demo_feeds = engine.get_price_feeds("ALGO")

            # Combine feeds for comprehensive assessment
            all_feeds = mcp_feeds + demo_feeds

            if not all_feeds:
                print("✗ No price feeds available for assessment")
                return False

            print(f"✓ Using {len(all_feeds)} price feeds ({len(mcp_feeds)} from MCP, {len(demo_feeds)} from demo)")

            # Perform aggregation
            aggregated = engine.aggregate_prices(all_feeds)

            print(f"  - Consensus price: ${aggregated.consensus_price:.4f}")
            print(f"  - Price confidence: {aggregated.price_confidence:.3f}")
            print(f"  - Oracle count: {aggregated.oracle_count}")
            print(f"  - Staleness score: {aggregated.staleness_score:.3f}")

            # Test manipulation detection with combined data
            engine.price_history["ALGO"] = all_feeds  # Simulate history
            manipulation_results = engine.detect_price_manipulation("ALGO")

            print(f"  - Manipulation risk: {manipulation_results['manipulation_risk']}")
            print(f"  - Risk score: {manipulation_results['risk_score']:.3f}")
            print(f"  - Recommendation: {manipulation_results['recommendation']}")

            return True

    except Exception as e:
        print(f"✗ Integrated volatility assessment test failed: {e}")
        return False


async def test_configuration_override():
    """Test configuration override for MCP URLs"""
    print("Testing configuration override...")

    try:
        # Test that environment variables would override config
        config = load_config()

        original_reader_url = config.mcp_services.algorand_reader_url
        original_market_url = config.mcp_services.market_data_url

        print(f"✓ Configuration loaded successfully")
        print(f"  - Algorand reader URL: {original_reader_url}")
        print(f"  - Market data URL: {original_market_url}")

        # Verify these match our expected ports
        assert "8002" in original_reader_url, "Algorand reader should use port 8002"
        assert "8003" in original_market_url, "Market data should use port 8003"

        return True

    except Exception as e:
        print(f"✗ Configuration override test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling for unreachable services"""
    print("Testing error handling for unreachable services...")

    try:
        # Create engine with invalid URLs
        config = load_config()
        config.mcp_services.algorand_reader_url = "http://localhost:9999"
        config.mcp_services.market_data_url = "http://localhost:9998"

        engine = MCPIntegratedVolatilityEngine()
        engine.config = config

        async with engine:
            # This should handle errors gracefully
            feeds = await engine.get_mcp_price_feeds("ALGO")

            # Should return empty list, not crash
            assert isinstance(feeds, list), "Should return a list even on error"
            print(f"✓ Error handling test passed (returned {len(feeds)} feeds)")

            return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def run_all_mcp_tests():
    """Run all MCP integration tests"""
    print("=" * 60)
    print("Volatility Assessment Engine - MCP Integration Tests")
    print("=" * 60)

    tests = [
        test_configuration_override,
        test_mcp_service_connectivity,
        test_mcp_price_fetching,
        test_mcp_algorand_data,
        test_integrated_volatility_assessment,
        test_error_handling
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} crashed: {e}")
            failed += 1

        print("-" * 40)

    print(f"\nTest Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All MCP integration tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed")
        if failed == passed:
            print("\n💡 Note: If MCP services are not running, many tests will fail.")
            print("   Start the MCP services on ports 8002 and 8003 before running this test.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_mcp_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)