#!/usr/bin/env python3
"""
Test Configuration System for Oracle Price Integration Engine
"""

import sys
import os
from pathlib import Path

# Add parent directories to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from core.config import load_config, OracleEngineConfig, ConfigLoader


def test_default_config():
    """Test loading default configuration"""
    print("=" * 60)
    print("Testing Default Configuration")
    print("=" * 60)

    config = OracleEngineConfig()

    print(f"MCP Services:")
    print(f"  Algorand Reader URL: {config.mcp_services.algorand_reader_url}")
    print(f"  Market Data URL: {config.mcp_services.market_data_url}")

    print(f"\nOracle Providers:")
    for name, provider in config.oracle_providers.items():
        print(f"  {name}:")
        print(f"    Enabled: {provider.enabled}")
        print(f"    API URL: {provider.api_url}")
        print(f"    Reliability: {provider.reliability_score}")
        print(f"    Variance: {provider.variance}")
        print(f"    Latency: {provider.latency_seconds}s")

    print(f"\nValidation Settings:")
    print(f"  Confidence Threshold: {config.validation.confidence_threshold}")
    print(f"  Min Data Points: {config.validation.min_data_points}")
    print(f"  Max Price Deviation: {config.validation.max_price_deviation_percent}%")

    print(f"\nFallback Configuration:")
    print(f"  Enabled: {config.fallback.enabled}")
    print(f"  Max Staleness: {config.fallback.max_staleness_minutes} minutes")
    print(f"  Emergency Prices: {list(config.fallback.emergency_prices.keys())}")

    return True


def test_yaml_config_loading():
    """Test loading configuration from YAML file"""
    print("\n" + "=" * 60)
    print("Testing YAML Configuration Loading")
    print("=" * 60)

    config_path = parent_dir / "config" / "config.yaml"

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False

    try:
        config = load_config(config_path)
        print("✅ Successfully loaded configuration from YAML")

        print(f"\nLoaded Oracle Providers:")
        for name, provider in config.oracle_providers.items():
            print(f"  {name}: {provider.enabled} (reliability: {provider.reliability_score})")

        print(f"\nAggregation Method: {config.aggregation.method}")
        print(f"Weight Factors: {config.aggregation.weight_factors}")

        print(f"\nManipulation Detection:")
        print(f"  Enabled: {config.manipulation_detection.enabled}")
        print(f"  Volatility Threshold: {config.manipulation_detection.volatility_threshold}")
        print(f"  Risk Weights: {config.manipulation_detection.risk_weights}")

        return True

    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False


def test_environment_overrides():
    """Test environment variable overrides"""
    print("\n" + "=" * 60)
    print("Testing Environment Variable Overrides")
    print("=" * 60)

    # Set some environment variables
    os.environ['ORACLE_MCP_READER_URL'] = 'http://test-reader:9001'
    os.environ['ORACLE_MCP_MARKET_URL'] = 'http://test-market:9002'
    os.environ['ORACLE_CHAINLINK_API_KEY'] = 'test-chainlink-key'
    os.environ['ORACLE_LOG_LEVEL'] = 'DEBUG'

    try:
        config = load_config()

        print(f"MCP Reader URL: {config.mcp_services.algorand_reader_url}")
        print(f"MCP Market URL: {config.mcp_services.market_data_url}")
        print(f"Chainlink API Key: {config.oracle_providers['chainlink'].api_key}")
        print(f"Log Level: {config.monitoring.log_level}")

        # Verify overrides worked
        assert config.mcp_services.algorand_reader_url == 'http://test-reader:9001'
        assert config.mcp_services.market_data_url == 'http://test-market:9002'
        assert config.oracle_providers['chainlink'].api_key == 'test-chainlink-key'
        assert config.monitoring.log_level == 'DEBUG'

        print("✅ Environment variable overrides working correctly")
        return True

    except Exception as e:
        print(f"❌ Environment override test failed: {e}")
        return False
    finally:
        # Clean up environment variables
        for key in ['ORACLE_MCP_READER_URL', 'ORACLE_MCP_MARKET_URL',
                   'ORACLE_CHAINLINK_API_KEY', 'ORACLE_LOG_LEVEL']:
            if key in os.environ:
                del os.environ[key]


def test_asset_configurations():
    """Test asset-specific configurations"""
    print("\n" + "=" * 60)
    print("Testing Asset-Specific Configurations")
    print("=" * 60)

    try:
        config = load_config()

        print("Asset Configurations:")
        for asset, asset_config in config.asset_configurations.items():
            print(f"  {asset}:")
            print(f"    Priority: {asset_config.priority}")
            print(f"    Refresh Override: {asset_config.refresh_interval_override}")
            print(f"    Confidence Override: {asset_config.confidence_threshold_override}")
            print(f"    Staleness Override: {asset_config.max_staleness_override}")

        # Test priority mapping
        refresh_intervals = config.refresh_intervals
        print(f"\nRefresh Interval Mapping:")
        print(f"  High Priority: {refresh_intervals.high_frequency_seconds}s")
        print(f"  Medium Priority: {refresh_intervals.medium_frequency_seconds}s")
        print(f"  Low Priority: {refresh_intervals.low_frequency_seconds}s")

        print("✅ Asset configuration test passed")
        return True

    except Exception as e:
        print(f"❌ Asset configuration test failed: {e}")
        return False


def test_configuration_validation():
    """Test configuration validation and error handling"""
    print("\n" + "=" * 60)
    print("Testing Configuration Validation")
    print("=" * 60)

    try:
        # Test with non-existent config file
        non_existent_path = Path("/tmp/non_existent_config.yaml")
        config = load_config(non_existent_path)
        print("✅ Gracefully handled missing config file - using defaults")

        # Verify default values are reasonable
        assert 0 < config.validation.confidence_threshold <= 1.0
        assert config.validation.min_data_points >= 1
        assert config.validation.max_price_deviation_percent > 0

        print("✅ Default configuration values are valid")

        return True

    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


def main():
    """Run all configuration tests"""
    print("Oracle Price Integration - Configuration System Tests")
    print("=" * 60)

    tests = [
        test_default_config,
        test_yaml_config_loading,
        test_environment_overrides,
        test_asset_configurations,
        test_configuration_validation
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
    print(f"Configuration Tests Summary: {passed}/{total} passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All configuration tests passed!")
        return 0
    else:
        print("❌ Some configuration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())