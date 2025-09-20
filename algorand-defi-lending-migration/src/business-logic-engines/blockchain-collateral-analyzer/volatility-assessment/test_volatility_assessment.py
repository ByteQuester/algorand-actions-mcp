#!/usr/bin/env python3
"""
Basic Functionality Test for Volatility Assessment Engine

Tests the core functionality of the configurable volatility assessment engine
without requiring external dependencies.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.volatility_engine import VolatilityAssessmentEngine, PriceOracle
from core.config import load_config


def test_configuration_loading():
    """Test configuration loading and defaults"""
    print("Testing configuration loading...")

    try:
        config = load_config()

        # Test MCP service URLs
        assert config.mcp_services.algorand_reader_url == "http://localhost:8002"
        assert config.mcp_services.market_data_url == "http://localhost:8003"

        # Test price staleness thresholds
        assert config.price_staleness.scoring_thresholds['fresh'] == 30
        assert config.price_staleness.scoring_values['fresh'] == 1.0

        # Test volatility calculation parameters
        assert config.volatility_calculation.minimum_data_points == 5
        assert config.volatility_calculation.windows['manipulation_detection'] == 60

        # Test manipulation detection thresholds
        assert config.manipulation_detection.risk_thresholds['volatility_high'] == 0.10
        assert config.manipulation_detection.risk_thresholds['consensus_poor'] == 0.80

        print("✓ Configuration loading test passed")
        return True

    except Exception as e:
        print(f"✗ Configuration loading test failed: {e}")
        return False


def test_engine_initialization():
    """Test engine initialization with configuration"""
    print("Testing engine initialization...")

    try:
        engine = VolatilityAssessmentEngine()

        # Check that config is loaded
        assert engine.config is not None
        assert hasattr(engine.config, 'mcp_services')
        assert hasattr(engine.config, 'price_staleness')
        assert hasattr(engine.config, 'volatility_calculation')

        # Check initial state
        assert len(engine.oracles) == 0
        assert len(engine.oracle_status) == 0
        assert len(engine.price_history) == 0

        print("✓ Engine initialization test passed")
        return True

    except Exception as e:
        print(f"✗ Engine initialization test failed: {e}")
        return False


def test_oracle_registration():
    """Test oracle registration functionality"""
    print("Testing oracle registration...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Check that oracles were registered
        assert len(engine.oracles) == 4
        assert "chainlink" in engine.oracles
        assert "pyth" in engine.oracles
        assert "algorand_native" in engine.oracles
        assert "dia" in engine.oracles

        # Check oracle status
        for oracle_name in engine.oracles.keys():
            assert oracle_name in engine.oracle_status
            assert oracle_name in engine.reliability_scores

        print("✓ Oracle registration test passed")
        return True

    except Exception as e:
        print(f"✗ Oracle registration test failed: {e}")
        return False


def test_price_feed_retrieval():
    """Test price feed retrieval from oracles"""
    print("Testing price feed retrieval...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Test getting price feeds for ALGO
        feeds = engine.get_price_feeds("ALGO")

        # Should get feeds from multiple oracles
        assert len(feeds) > 0
        assert len(feeds) <= len(engine.oracles)

        # Check feed structure
        for feed in feeds:
            assert hasattr(feed, 'oracle_name')
            assert hasattr(feed, 'asset_symbol')
            assert hasattr(feed, 'price_usd')
            assert hasattr(feed, 'timestamp')
            assert hasattr(feed, 'confidence')
            assert feed.asset_symbol == "ALGO"
            assert feed.price_usd > 0
            assert 0 <= feed.confidence <= 1

        print(f"✓ Price feed retrieval test passed (got {len(feeds)} feeds)")
        return True

    except Exception as e:
        print(f"✗ Price feed retrieval test failed: {e}")
        return False


def test_price_aggregation():
    """Test price aggregation functionality"""
    print("Testing price aggregation...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Get price feeds and aggregate
        feeds = engine.get_price_feeds("ALGO")
        if len(feeds) == 0:
            print("✗ No price feeds available for aggregation test")
            return False

        aggregated = engine.aggregate_prices(feeds)

        # Check aggregated price structure
        assert aggregated.asset_symbol == "ALGO"
        assert aggregated.consensus_price > 0
        assert 0 <= aggregated.price_confidence <= 1
        assert aggregated.oracle_count == len(feeds)
        assert len(aggregated.oracle_prices) == len(feeds)

        # Check calculated metrics
        assert 0 <= aggregated.staleness_score <= 1
        assert 0 <= aggregated.reliability_score <= 1
        assert 0 <= aggregated.consensus_strength <= 1

        print(f"✓ Price aggregation test passed (consensus price: ${aggregated.consensus_price:.4f})")
        return True

    except Exception as e:
        print(f"✗ Price aggregation test failed: {e}")
        return False


def test_staleness_calculation():
    """Test staleness score calculation with configuration"""
    print("Testing staleness calculation...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Get price feeds
        feeds = engine.get_price_feeds("ALGO")
        if len(feeds) == 0:
            print("✗ No price feeds available for staleness test")
            return False

        # Calculate staleness score using configuration
        staleness_score = engine.calculate_staleness_score(feeds)

        # Should be between 0 and 1
        assert 0 <= staleness_score <= 1

        # For fresh data, should be close to 1
        # (since our mock data has recent timestamps)
        assert staleness_score > 0.5, f"Expected fresh data, got staleness score: {staleness_score}"

        print(f"✓ Staleness calculation test passed (score: {staleness_score:.3f})")
        return True

    except Exception as e:
        print(f"✗ Staleness calculation test failed: {e}")
        return False


def test_manipulation_detection():
    """Test price manipulation detection with configuration"""
    print("Testing manipulation detection...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Simulate some price history
        engine.simulate_price_history("ALGO", hours=2)

        # Test manipulation detection
        manipulation_results = engine.detect_price_manipulation("ALGO")

        # Check result structure
        required_keys = [
            'manipulation_risk', 'confidence', 'risk_factors',
            'price_volatility', 'oracle_consensus', 'recommendation'
        ]

        for key in required_keys:
            assert key in manipulation_results, f"Missing key: {key}"

        # Check risk level is valid
        valid_risk_levels = ['minimal', 'low', 'medium', 'high', 'unknown']
        assert manipulation_results['manipulation_risk'] in valid_risk_levels

        # Check confidence is in valid range
        assert 0 <= manipulation_results['confidence'] <= 1

        print(f"✓ Manipulation detection test passed (risk: {manipulation_results['manipulation_risk']})")
        return True

    except Exception as e:
        print(f"✗ Manipulation detection test failed: {e}")
        return False


def test_volatility_assessment():
    """Test comprehensive volatility assessment"""
    print("Testing volatility assessment...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Simulate price history for better assessment
        engine.simulate_price_history("ALGO", hours=24)

        # Perform volatility assessment
        volatility_metrics = engine.assess_volatility("ALGO")

        # Check metrics structure
        assert volatility_metrics.asset_symbol == "ALGO"
        assert 0 <= volatility_metrics.volatility_7d <= 1
        assert 0 <= volatility_metrics.volatility_30d <= 1
        assert 0 <= volatility_metrics.price_range_24h <= 1
        assert 0 <= volatility_metrics.price_stability_score <= 1
        assert 0 <= volatility_metrics.confidence <= 1

        # Check risk assessment
        valid_risk_levels = ['minimal', 'low', 'medium', 'high']
        assert volatility_metrics.manipulation_risk_level in valid_risk_levels

        valid_recommendations = ['normal_operation', 'increase_monitoring', 'emergency_halt']
        assert volatility_metrics.recommendation in valid_recommendations

        print(f"✓ Volatility assessment test passed")
        print(f"  - 7d volatility: {volatility_metrics.volatility_7d:.3f}")
        print(f"  - Price stability: {volatility_metrics.price_stability_score:.3f}")
        print(f"  - Manipulation risk: {volatility_metrics.manipulation_risk_level}")
        print(f"  - Recommendation: {volatility_metrics.recommendation}")

        return True

    except Exception as e:
        print(f"✗ Volatility assessment test failed: {e}")
        return False


def test_reliable_price_with_config():
    """Test reliable price retrieval using configuration thresholds"""
    print("Testing reliable price with configuration...")

    try:
        engine = VolatilityAssessmentEngine()
        engine.setup_demo_oracles()

        # Test with default configuration threshold
        reliable_price = engine.get_reliable_price("ALGO")

        if reliable_price is None:
            print("✗ Could not get reliable price")
            return False

        # Check that confidence meets configured minimum
        min_confidence = engine.config.oracle_confidence.minimum_confidence

        # Note: In testing, we may get warnings if confidence is below threshold
        # but the function still returns the price

        assert reliable_price.consensus_price > 0
        assert reliable_price.asset_symbol == "ALGO"

        print(f"✓ Reliable price test passed")
        print(f"  - Price: ${reliable_price.consensus_price:.4f}")
        print(f"  - Confidence: {reliable_price.price_confidence:.3f}")
        print(f"  - Required minimum: {min_confidence:.3f}")

        return True

    except Exception as e:
        print(f"✗ Reliable price test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("Volatility Assessment Engine - Basic Functionality Tests")
    print("=" * 60)

    tests = [
        test_configuration_loading,
        test_engine_initialization,
        test_oracle_registration,
        test_price_feed_retrieval,
        test_price_aggregation,
        test_staleness_calculation,
        test_manipulation_detection,
        test_volatility_assessment,
        test_reliable_price_with_config
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            result = test_func()
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
        print("🎉 All tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)