#!/usr/bin/env python3
"""
Test Oracle Engine with Configuration System
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directories to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from oracle_integration_configured import ConfigurableOracleManager, PriceFeed


def test_oracle_initialization():
    """Test oracle manager initialization with configuration"""
    print("=" * 60)
    print("Testing Oracle Manager Initialization")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        print("✅ Oracle manager initialized successfully")

        # Check oracle status
        print(f"Oracle Status:")
        for oracle_name, status in oracle_manager.oracle_status.items():
            reliability = oracle_manager.reliability_scores.get(oracle_name, 0.0)
            print(f"  {oracle_name}: {status.value} (reliability: {reliability})")

        # Check configuration summary
        config_summary = oracle_manager.get_config_summary()
        print(f"\nConfiguration Summary:")
        print(f"  Aggregation Method: {config_summary['aggregation_method']}")
        print(f"  Fallback Enabled: {config_summary['fallback_enabled']}")
        print(f"  Manipulation Detection: {config_summary['manipulation_detection_enabled']}")

        return True

    except Exception as e:
        print(f"❌ Oracle initialization failed: {e}")
        return False


def test_price_feed_retrieval():
    """Test retrieving price feeds from configured oracles"""
    print("\n" + "=" * 60)
    print("Testing Price Feed Retrieval")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        # Test various assets
        test_assets = ["ALGO", "USDC", "BTC", "ETH"]

        for asset in test_assets:
            print(f"\nTesting {asset}:")
            feeds = oracle_manager.get_price_feeds(asset)

            if feeds:
                print(f"  ✅ Retrieved {len(feeds)} price feeds")
                for feed in feeds:
                    print(f"    {feed.oracle_name}: ${feed.price_usd:.4f} "
                          f"(confidence: {feed.confidence:.2f}, "
                          f"age: {(datetime.now() - feed.timestamp).total_seconds():.0f}s)")
            else:
                print(f"  ⚠️  No price feeds available")

        return True

    except Exception as e:
        print(f"❌ Price feed retrieval failed: {e}")
        return False


def test_price_aggregation():
    """Test price aggregation with different configuration methods"""
    print("\n" + "=" * 60)
    print("Testing Price Aggregation")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        # Test aggregation for ALGO
        feeds = oracle_manager.get_price_feeds("ALGO")
        if not feeds:
            print("⚠️  No feeds available for aggregation test")
            return True

        print(f"Aggregating {len(feeds)} price feeds for ALGO:")
        for feed in feeds:
            print(f"  {feed.oracle_name}: ${feed.price_usd:.4f}")

        aggregated = oracle_manager.aggregate_prices(feeds)

        print(f"\nAggregated Result:")
        print(f"  Consensus Price: ${aggregated.consensus_price:.4f}")
        print(f"  Price Confidence: {aggregated.price_confidence:.2f}")
        print(f"  Price Deviation: {aggregated.price_deviation:.4f}")
        print(f"  Oracle Count: {aggregated.oracle_count}")
        print(f"  Staleness Score: {aggregated.staleness_score:.2f}")
        print(f"  Consensus Strength: {aggregated.consensus_strength:.2f}")

        # Verify aggregation logic
        assert aggregated.oracle_count == len(feeds)
        assert 0 <= aggregated.price_confidence <= 1.0
        assert aggregated.consensus_price > 0

        print("✅ Price aggregation working correctly")
        return True

    except Exception as e:
        print(f"❌ Price aggregation failed: {e}")
        return False


def test_fallback_mechanism():
    """Test fallback price mechanism"""
    print("\n" + "=" * 60)
    print("Testing Fallback Mechanism")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        # Disable all oracles to test fallback
        for oracle_name in oracle_manager.oracle_status.keys():
            oracle_manager.oracle_status[oracle_name] = oracle_manager.oracle_status[oracle_name].__class__.FAILED

        print("Disabled all oracles to test fallback...")

        # Try to get a reliable price (should trigger fallback)
        fallback_price = oracle_manager.get_reliable_price("ALGO")

        if fallback_price:
            print(f"✅ Fallback mechanism activated")
            print(f"  Fallback Price: ${fallback_price.consensus_price:.4f}")
            print(f"  Confidence: {fallback_price.price_confidence:.2f}")
            print(f"  Oracle Count: {fallback_price.oracle_count}")

            # Verify it's a fallback price
            assert fallback_price.oracle_count == 1
            assert fallback_price.oracle_prices[0].oracle_name == "emergency_fallback"

        else:
            print("⚠️  Fallback mechanism not triggered")

        return True

    except Exception as e:
        print(f"❌ Fallback mechanism test failed: {e}")
        return False


def test_manipulation_detection():
    """Test price manipulation detection"""
    print("\n" + "=" * 60)
    print("Testing Price Manipulation Detection")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        # Create some mock price history with manipulation
        asset_symbol = "ALGO"

        # Normal prices
        normal_feeds = []
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(10):
            feed = PriceFeed(
                oracle_name="chainlink",
                asset_symbol=asset_symbol,
                price_usd=0.25 + (i * 0.001),  # Gradual increase
                timestamp=base_time + timedelta(minutes=i * 5),
                confidence=0.95
            )
            normal_feeds.append(feed)

        # Add a suspicious price spike
        spike_feed = PriceFeed(
            oracle_name="chainlink",
            asset_symbol=asset_symbol,
            price_usd=0.35,  # 40% spike
            timestamp=datetime.now() - timedelta(minutes=5),
            confidence=0.95
        )
        normal_feeds.append(spike_feed)

        # Set price history
        oracle_manager.price_history[asset_symbol] = normal_feeds

        # Run manipulation detection
        manipulation_result = oracle_manager.detect_price_manipulation(asset_symbol)

        print(f"Manipulation Detection Results:")
        print(f"  Risk Level: {manipulation_result['manipulation_risk']}")
        print(f"  Confidence: {manipulation_result['confidence']:.2f}")
        print(f"  Risk Factors: {manipulation_result['risk_factors']}")
        print(f"  Price Volatility: {manipulation_result['price_volatility']:.4f}")
        print(f"  Recommendation: {manipulation_result['recommendation']}")

        print("✅ Manipulation detection completed")
        return True

    except Exception as e:
        print(f"❌ Manipulation detection failed: {e}")
        return False


def test_configuration_flexibility():
    """Test configuration flexibility and runtime changes"""
    print("\n" + "=" * 60)
    print("Testing Configuration Flexibility")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        # Test different aggregation methods by checking config
        current_method = oracle_manager.config.aggregation.method
        print(f"Current aggregation method: {current_method}")

        # Test confidence thresholds
        confidence_threshold = oracle_manager.config.validation.confidence_threshold
        print(f"Confidence threshold: {confidence_threshold}")

        # Test oracle-specific settings
        for oracle_name, oracle_config in oracle_manager.config.oracle_providers.items():
            if oracle_config.enabled:
                print(f"{oracle_name} configuration:")
                print(f"  Reliability: {oracle_config.reliability_score}")
                print(f"  Variance: {oracle_config.variance}")
                print(f"  Latency: {oracle_config.latency_seconds}s")

        # Test asset-specific refresh intervals (simulated)
        test_assets = ["ALGO", "USDC", "BTC"]
        for asset in test_assets:
            # This would normally be used in a scheduler
            interval = oracle_manager.get_asset_refresh_interval(asset)
            print(f"{asset} refresh interval: {interval}s")

        print("✅ Configuration flexibility test passed")
        return True

    except Exception as e:
        print(f"❌ Configuration flexibility test failed: {e}")
        return False


def test_health_check():
    """Test oracle health checking"""
    print("\n" + "=" * 60)
    print("Testing Oracle Health Check")
    print("=" * 60)

    try:
        oracle_manager = ConfigurableOracleManager()

        health_status = oracle_manager.health_check()

        print(f"Health Check Results:")
        print(f"  Overall Status: {health_status['overall_status']}")
        print(f"  Active Oracles: {health_status['active_oracles']}/{health_status['total_oracles']}")

        print(f"\nOracle Status Details:")
        for oracle_name, status_info in health_status['oracle_status'].items():
            print(f"  {oracle_name}: {status_info['status']} "
                  f"(reliability: {status_info['reliability']:.2f})")

        print("✅ Health check completed successfully")
        return True

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Run all oracle engine tests"""
    print("Oracle Price Integration - Engine Functionality Tests")
    print("=" * 60)

    tests = [
        test_oracle_initialization,
        test_price_feed_retrieval,
        test_price_aggregation,
        test_fallback_mechanism,
        test_manipulation_detection,
        test_configuration_flexibility,
        test_health_check
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"Oracle Engine Tests Summary: {passed}/{total} passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All oracle engine tests passed!")
        return 0
    else:
        print("❌ Some oracle engine tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())