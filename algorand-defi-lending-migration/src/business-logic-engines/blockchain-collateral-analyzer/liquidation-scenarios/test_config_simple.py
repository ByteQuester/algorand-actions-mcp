#!/usr/bin/env python3
"""
Simple Configuration Test for Liquidation Scenarios Engine

This script validates that the configuration system works correctly.
"""

import sys
import os
from pathlib import Path
import tempfile
import yaml

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import (
    LiquidationEngineConfig,
    ConfigLoader,
    load_config
)


def test_default_config():
    """Test that default configuration loads correctly"""
    print("Testing default configuration...")

    config = LiquidationEngineConfig()

    # Test MCP services
    assert config.mcp_services.algorand_reader_url == "http://localhost:8002"
    assert config.mcp_services.market_data_url == "http://localhost:8003"

    # Test slippage calculation
    assert config.slippage_calculation.max_slippage_cap == 0.50
    assert config.slippage_calculation.volume_ratio_power == 0.7

    # Test liquidation timing
    assert config.liquidation_timing.volume_thresholds['very_small'] == 0.01
    assert config.liquidation_timing.base_liquidation_times['small'] == 2.0

    # Test liquidation strategies
    assert config.liquidation_strategies.immediate.max_slippage_tolerance == 0.15
    assert config.liquidation_strategies.gradual.target_completion_time == 24.0

    # Test execution parameters
    assert config.execution_parameters.default_gas_cost_usd == 50.0
    assert config.execution_parameters.tranche_delay_hours == 0.5

    # Test flash loan integration
    assert config.flash_loan_integration.enabled == True
    assert config.flash_loan_integration.max_flash_loan_amount == 10_000_000

    print("✓ Default configuration test passed")


def test_yaml_config_loading():
    """Test loading configuration from YAML file"""
    print("Testing YAML configuration loading...")

    # Create a temporary YAML config file
    test_config = {
        'mcp_services': {
            'algorand_reader_url': 'http://test:8002',
            'market_data_url': 'http://test:8003'
        },
        'slippage_calculation': {
            'max_slippage_cap': 0.30,
            'volume_ratio_power': 0.8
        },
        'liquidation_strategies': {
            'immediate': {
                'max_slippage_tolerance': 0.20,
                'target_completion_time': 0.5,
                'min_recovery_rate': 0.75,
                'market_impact_limit': 0.15,
                'gas_cost_consideration': True
            }
        },
        'execution_parameters': {
            'default_gas_cost_usd': 100.0,
            'max_tranches': 5
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        config_path = Path(f.name)

    try:
        # Load configuration from the temporary file
        config = load_config(config_path)

        # Verify overrides were applied
        assert config.mcp_services.algorand_reader_url == 'http://test:8002'
        assert config.mcp_services.market_data_url == 'http://test:8003'
        assert config.slippage_calculation.max_slippage_cap == 0.30
        assert config.slippage_calculation.volume_ratio_power == 0.8
        assert config.liquidation_strategies.immediate.max_slippage_tolerance == 0.20
        assert config.liquidation_strategies.immediate.target_completion_time == 0.5
        assert config.execution_parameters.default_gas_cost_usd == 100.0
        assert config.execution_parameters.max_tranches == 5

        # Verify non-overridden values remain default
        assert config.liquidation_timing.volume_thresholds['very_small'] == 0.01
        assert config.urgency_adjustments.immediate == 0.25

    finally:
        # Clean up temporary file
        os.unlink(config_path)

    print("✓ YAML configuration loading test passed")


def test_config_file_loading():
    """Test loading the actual config file from the project"""
    print("Testing actual config file loading...")

    # Try to load the actual config file
    config_path = Path(__file__).parent / "config" / "config.yaml"

    if config_path.exists():
        config = load_config(config_path)

        # Basic validation that the file loaded
        assert config.mcp_services.algorand_reader_url.startswith('http')
        assert config.mcp_services.market_data_url.startswith('http')
        assert config.execution_parameters.default_gas_cost_usd > 0

        print("✓ Actual config file loading test passed")
    else:
        print("⚠ Config file not found, skipping actual file test")


def run_tests():
    """Run all configuration tests"""
    print("=" * 60)
    print("LIQUIDATION SCENARIOS ENGINE - CONFIGURATION TESTS")
    print("=" * 60)

    tests = [
        test_default_config,
        test_yaml_config_loading,
        test_config_file_loading
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)