#!/usr/bin/env python3
"""
Test MCP Integration for Liquidation Scenarios Engine

This script tests the integration with MCP services running on ports 8002 and 8003.
"""

import sys
import requests
import json
from pathlib import Path
from core.config import load_config

def test_mcp_service_connectivity():
    """Test connectivity to MCP services"""
    print("=== Testing MCP Service Connectivity ===")

    config = load_config()

    # Test Algorand Reader MCP (port 8002)
    algorand_reader_url = config.mcp_services.algorand_reader_url
    print(f"Testing Algorand Reader MCP at {algorand_reader_url}")

    try:
        response = requests.get(f"{algorand_reader_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Algorand Reader MCP is responding")
        else:
            print(f"⚠ Algorand Reader MCP returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Algorand Reader MCP is not accessible: {e}")

    # Test Market Data MCP (port 8003)
    market_data_url = config.mcp_services.market_data_url
    print(f"Testing Market Data MCP at {market_data_url}")

    try:
        response = requests.get(f"{market_data_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Market Data MCP is responding")
        else:
            print(f"⚠ Market Data MCP returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Market Data MCP is not accessible: {e}")


def test_configuration_mcp_integration():
    """Test that configuration properly integrates MCP service URLs"""
    print("\n=== Testing Configuration MCP Integration ===")

    config = load_config()

    # Verify default MCP service URLs
    expected_reader_url = "http://localhost:8002"
    expected_market_url = "http://localhost:8003"

    assert config.mcp_services.algorand_reader_url == expected_reader_url, \
        f"Expected {expected_reader_url}, got {config.mcp_services.algorand_reader_url}"

    assert config.mcp_services.market_data_url == expected_market_url, \
        f"Expected {expected_market_url}, got {config.mcp_services.market_data_url}"

    print(f"✓ Algorand Reader URL configured: {config.mcp_services.algorand_reader_url}")
    print(f"✓ Market Data URL configured: {config.mcp_services.market_data_url}")


def test_liquidation_engine_with_mcp_config():
    """Test that the liquidation engine properly uses MCP configuration"""
    print("\n=== Testing Liquidation Engine with MCP Config ===")

    # Add the core directory to path
    sys.path.append(str(Path(__file__).parent / 'core'))

    try:
        from liquidation_scenarios_engine import LiquidationScenariosEngine

        # Create engine instance
        engine = LiquidationScenariosEngine()

        # Verify MCP URLs are properly configured
        assert engine.algorand_reader_url == "http://localhost:8002"
        assert engine.market_data_url == "http://localhost:8003"

        print("✓ Liquidation engine initialized with MCP configuration")
        print(f"  Algorand Reader: {engine.algorand_reader_url}")
        print(f"  Market Data: {engine.market_data_url}")

        # Test configuration reloading
        engine.reload_config()
        print("✓ Configuration reload successful")

    except ImportError as e:
        print(f"✗ Failed to import liquidation engine: {e}")
    except Exception as e:
        print(f"✗ Error testing liquidation engine: {e}")


def test_flash_loan_integration():
    """Test flash loan integration parameters"""
    print("\n=== Testing Flash Loan Integration ===")

    config = load_config()

    if config.flash_loan_integration.enabled:
        print("✓ Flash loan integration is enabled")
        print(f"  Max amount: ${config.flash_loan_integration.max_flash_loan_amount:,.0f}")
        print(f"  Fee rate: {config.flash_loan_integration.flash_loan_fee_rate:.3%}")
        print(f"  Gas multiplier: {config.flash_loan_integration.flash_loan_gas_multiplier}x")
        print(f"  Supported protocols: {', '.join(config.flash_loan_integration.supported_protocols)}")

        # Test flash loan calculation
        try:
            sys.path.append(str(Path(__file__).parent / 'core'))
            from liquidation_scenarios_engine import LiquidationScenariosEngine

            engine = LiquidationScenariosEngine()
            flash_params = engine.calculate_flash_loan_parameters(1_000_000, "aave")

            print("✓ Flash loan calculation successful")
            print(f"  Loan amount: ${flash_params['loan_amount']:,.0f}")
            print(f"  Fee amount: ${flash_params['fee_amount']:,.0f}")
            print(f"  Total cost: ${flash_params['total_cost']:,.0f}")

        except Exception as e:
            print(f"✗ Flash loan calculation failed: {e}")
    else:
        print("⚠ Flash loan integration is disabled")


def test_emergency_scenarios():
    """Test emergency scenario configurations"""
    print("\n=== Testing Emergency Scenarios ===")

    config = load_config()

    scenarios = ['oracle_failure', 'volatility_spike', 'black_swan']

    for scenario in scenarios:
        try:
            sys.path.append(str(Path(__file__).parent / 'core'))
            from liquidation_scenarios_engine import LiquidationScenariosEngine

            engine = LiquidationScenariosEngine()
            params = engine.get_emergency_parameters(scenario)

            print(f"✓ {scenario.replace('_', ' ').title()} scenario configured")
            print(f"  Fallback discount: {params['fallback_discount']:.1%}")
            print(f"  Max delay: {params['max_delay_hours']:.1f}h")

        except Exception as e:
            print(f"✗ Error testing {scenario}: {e}")


def run_mcp_integration_tests():
    """Run all MCP integration tests"""
    print("=" * 60)
    print("LIQUIDATION SCENARIOS ENGINE - MCP INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        test_mcp_service_connectivity,
        test_configuration_mcp_integration,
        test_liquidation_engine_with_mcp_config,
        test_flash_loan_integration,
        test_emergency_scenarios
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")

    print("\n" + "=" * 60)
    print("MCP Integration tests completed.")
    print("Note: Some tests may fail if MCP services are not running.")
    print("To start MCP services, run: ./start-mcp-services.sh")
    print("=" * 60)


if __name__ == "__main__":
    run_mcp_integration_tests()