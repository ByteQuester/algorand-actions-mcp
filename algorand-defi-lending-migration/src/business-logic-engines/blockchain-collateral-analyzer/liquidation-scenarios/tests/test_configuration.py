#!/usr/bin/env python3
"""
Test Configuration System for Liquidation Scenarios Engine

This script validates that the configuration system works correctly
and all parameters are loaded properly.
"""

import sys
import os
from pathlib import Path
import tempfile
import yaml

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from liquidation_scenarios.core.config import (
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
        },
        'flash_loan_integration': {
            'enabled': False,
            'max_flash_loan_amount': 5_000_000
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
        assert config.flash_loan_integration.enabled == False
        assert config.flash_loan_integration.max_flash_loan_amount == 5_000_000

        # Verify non-overridden values remain default
        assert config.liquidation_timing.volume_thresholds['very_small'] == 0.01
        assert config.urgency_adjustments.immediate == 0.25

    finally:
        # Clean up temporary file
        os.unlink(config_path)

    print("✓ YAML configuration loading test passed")


def test_environment_variable_overrides():
    """Test environment variable overrides"""
    print("Testing environment variable overrides...")

    # Set environment variables
    os.environ['LIQUIDATION_MCP_READER_URL'] = 'http://env:8002'
    os.environ['LIQUIDATION_MCP_MARKET_URL'] = 'http://env:8003'
    os.environ['LIQUIDATION_DB_PATH'] = '/tmp/test_liquidation.db'
    os.environ['LIQUIDATION_FLASH_LOAN_ENABLED'] = 'false'

    try:
        config = load_config()

        # Verify environment overrides
        assert config.mcp_services.algorand_reader_url == 'http://env:8002'
        assert config.mcp_services.market_data_url == 'http://env:8003'
        assert config.database.default_path == '/tmp/test_liquidation.db'
        assert config.flash_loan_integration.enabled == False

    finally:
        # Clean up environment variables
        for key in ['LIQUIDATION_MCP_READER_URL', 'LIQUIDATION_MCP_MARKET_URL',
                   'LIQUIDATION_DB_PATH', 'LIQUIDATION_FLASH_LOAN_ENABLED']:
            if key in os.environ:
                del os.environ[key]

    print("✓ Environment variable overrides test passed")


def test_config_structure_validation():
    """Test that all required configuration sections exist"""
    print("Testing configuration structure validation...")

    config = load_config()

    # Test all major sections exist
    assert hasattr(config, 'mcp_services')
    assert hasattr(config, 'slippage_calculation')
    assert hasattr(config, 'liquidation_timing')
    assert hasattr(config, 'liquidity_adjustments')
    assert hasattr(config, 'urgency_adjustments')
    assert hasattr(config, 'market_impact_thresholds')
    assert hasattr(config, 'liquidation_strategies')
    assert hasattr(config, 'execution_parameters')
    assert hasattr(config, 'feasibility_assessment')
    assert hasattr(config, 'flash_loan_integration')
    assert hasattr(config, 'emergency_scenarios')
    assert hasattr(config, 'auction_parameters')
    assert hasattr(config, 'recovery_rates')
    assert hasattr(config, 'liquidation_penalties')
    assert hasattr(config, 'risk_monitoring')
    assert hasattr(config, 'analysis')
    assert hasattr(config, 'database')

    # Test liquidation strategies have all required strategies
    assert hasattr(config.liquidation_strategies, 'immediate')
    assert hasattr(config.liquidation_strategies, 'gradual')
    assert hasattr(config.liquidation_strategies, 'selective')

    # Test emergency scenarios
    assert hasattr(config.emergency_scenarios, 'oracle_failure')
    assert hasattr(config.emergency_scenarios, 'volatility_spike')
    assert hasattr(config.emergency_scenarios, 'black_swan')

    # Test auction parameters
    assert hasattr(config.auction_parameters, 'dutch_auction')
    assert hasattr(config.auction_parameters, 'sealed_bid_auction')

    print("✓ Configuration structure validation test passed")


def test_parameter_ranges():
    """Test that parameters are within reasonable ranges"""
    print("Testing parameter ranges...")

    config = load_config()

    # Test slippage parameters
    assert 0.0 <= config.slippage_calculation.max_slippage_cap <= 1.0
    assert 0.0 < config.slippage_calculation.volume_ratio_power <= 2.0
    assert 0.0 < config.slippage_calculation.base_slippage_factor <= 1.0

    # Test timing parameters
    assert all(0.0 < threshold <= 1.0 for threshold in config.liquidation_timing.volume_thresholds.values())
    assert all(time > 0.0 for time in config.liquidation_timing.base_liquidation_times.values())

    # Test liquidation strategies
    for strategy in [config.liquidation_strategies.immediate,
                    config.liquidation_strategies.gradual,
                    config.liquidation_strategies.selective]:
        assert 0.0 <= strategy.max_slippage_tolerance <= 1.0
        assert strategy.target_completion_time > 0.0
        assert 0.0 <= strategy.min_recovery_rate <= 1.0
        assert 0.0 <= strategy.market_impact_limit <= 1.0

    # Test feasibility assessment thresholds
    thresholds = config.feasibility_assessment.volume_impact_thresholds
    assert thresholds['very_high'] < thresholds['high'] < thresholds['medium'] < thresholds['low']

    confidence_scores = config.feasibility_assessment.confidence_scores
    assert all(0.0 <= score <= 1.0 for score in confidence_scores.values())

    # Test flash loan parameters
    assert config.flash_loan_integration.max_flash_loan_amount > 0
    assert 0.0 <= config.flash_loan_integration.flash_loan_fee_rate <= 1.0
    assert config.flash_loan_integration.flash_loan_gas_multiplier >= 1.0

    print("✓ Parameter ranges test passed")


def test_config_file_loading():
    """Test loading the actual config file from the project"""
    print("Testing actual config file loading...")

    # Try to load the actual config file
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    if config_path.exists():
        config = load_config(config_path)

        # Basic validation that the file loaded
        assert config.mcp_services.algorand_reader_url.startswith('http')
        assert config.mcp_services.market_data_url.startswith('http')
        assert config.execution_parameters.default_gas_cost_usd > 0

        print("✓ Actual config file loading test passed")
    else:
        print("⚠ Config file not found, skipping actual file test")


def run_all_tests():
    """Run all configuration tests"""
    print("=" * 60)
    print("LIQUIDATION SCENARIOS ENGINE - CONFIGURATION TESTS")
    print("=" * 60)

    tests = [
        test_default_config,
        test_yaml_config_loading,
        test_environment_variable_overrides,
        test_config_structure_validation,
        test_parameter_ranges,
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
    success = run_all_tests()
    sys.exit(0 if success else 1)