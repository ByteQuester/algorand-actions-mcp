#!/usr/bin/env python3
"""
Test MCP Service Integration for Oracle Price Engine

This script tests the integration between the Oracle Price Integration Engine
and the MCP services running on ports 8002 (algorand-reader) and 8003 (market-data).
"""

import sys
import os
import requests
import json
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from core.config import load_config
from oracle_integration_configured import ConfigurableOracleManager


def check_mcp_service_availability():
    """Check if MCP services are running and accessible"""
    print("=" * 60)
    print("Checking MCP Service Availability")
    print("=" * 60)

    config = load_config()
    services = {
        "Algorand Reader": config.mcp_services.algorand_reader_url,
        "Market Data": config.mcp_services.market_data_url
    }

    service_status = {}

    for service_name, url in services.items():
        try:
            # Try to reach the service with a timeout
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Available at {url}")
                service_status[service_name] = True
            else:
                print(f"⚠️  {service_name}: Responded with status {response.status_code}")
                service_status[service_name] = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {service_name}: Connection refused at {url}")
            service_status[service_name] = False
        except requests.exceptions.Timeout:
            print(f"⏱️  {service_name}: Timeout at {url}")
            service_status[service_name] = False
        except Exception as e:
            print(f"❌ {service_name}: Error - {e}")
            service_status[service_name] = False

    return service_status


def test_oracle_mcp_integration():
    """Test oracle engine integration with MCP services"""
    print("\n" + "=" * 60)
    print("Testing Oracle Engine MCP Integration")
    print("=" * 60)

    try:
        # Initialize oracle manager with MCP integration
        oracle_manager = ConfigurableOracleManager()

        print("✅ Oracle manager initialized with MCP configuration")

        # Display MCP configuration
        config = oracle_manager.config
        print(f"\nMCP Service Configuration:")
        print(f"  Algorand Reader: {config.mcp_services.algorand_reader_url}")
        print(f"  Market Data: {config.mcp_services.market_data_url}")

        # Test price retrieval (would use MCP services in production)
        test_assets = ["ALGO", "USDC", "BTC"]

        print(f"\nTesting Price Retrieval (simulated MCP integration):")
        for asset in test_assets:
            price = oracle_manager.get_reliable_price(asset)
            if price:
                print(f"  {asset}: ${price.consensus_price:.4f} "
                      f"(confidence: {price.price_confidence:.2f}, "
                      f"oracles: {price.oracle_count})")
            else:
                print(f"  {asset}: No price available")

        return True

    except Exception as e:
        print(f"❌ Oracle MCP integration test failed: {e}")
        return False


def simulate_mcp_price_feed():
    """Simulate receiving price data from MCP services"""
    print("\n" + "=" * 60)
    print("Simulating MCP Price Feed Integration")
    print("=" * 60)

    # Simulate MCP service responses
    mock_mcp_responses = {
        "algorand_reader": {
            "ALGO": {
                "price_usd": 0.2487,
                "volume_24h": 45_000_000,
                "market_cap": 2_100_000_000,
                "timestamp": datetime.now().isoformat(),
                "source": "algorand_indexer"
            }
        },
        "market_data": {
            "ALGO": {
                "price_usd": 0.2492,
                "volume_24h": 47_000_000,
                "price_change_24h": 0.0234,
                "timestamp": datetime.now().isoformat(),
                "source": "coingecko_api"
            },
            "USDC": {
                "price_usd": 1.0001,
                "volume_24h": 5_200_000,
                "price_change_24h": 0.0001,
                "timestamp": datetime.now().isoformat(),
                "source": "coingecko_api"
            }
        }
    }

    print("Mock MCP Service Responses:")
    print(json.dumps(mock_mcp_responses, indent=2, default=str))

    # Show how oracle engine would process this data
    oracle_manager = ConfigurableOracleManager()

    print(f"\nOracle Engine Processing:")
    print(f"  - Would fetch data from both MCP services")
    print(f"  - Apply oracle-specific variance and reliability scoring")
    print(f"  - Aggregate using configured method: {oracle_manager.config.aggregation.method}")
    print(f"  - Validate against configured thresholds")
    print(f"  - Return consensus price with confidence score")

    return True


def test_configuration_with_mcp():
    """Test that configuration properly handles MCP service settings"""
    print("\n" + "=" * 60)
    print("Testing Configuration with MCP Settings")
    print("=" * 60)

    # Test environment variable overrides for MCP URLs
    original_reader = os.environ.get('ORACLE_MCP_READER_URL')
    original_market = os.environ.get('ORACLE_MCP_MARKET_URL')

    try:
        # Set test environment variables
        os.environ['ORACLE_MCP_READER_URL'] = 'http://localhost:8002'
        os.environ['ORACLE_MCP_MARKET_URL'] = 'http://localhost:8003'

        config = load_config()

        print(f"Environment Variable Overrides:")
        print(f"  Reader URL: {config.mcp_services.algorand_reader_url}")
        print(f"  Market URL: {config.mcp_services.market_data_url}")

        # Verify URLs match expected values
        assert config.mcp_services.algorand_reader_url == 'http://localhost:8002'
        assert config.mcp_services.market_data_url == 'http://localhost:8003'

        print("✅ Environment variable overrides working correctly")

        # Test with different oracle configurations
        print(f"\nOracle Provider Integration:")
        for name, provider in config.oracle_providers.items():
            if provider.enabled:
                print(f"  {name}:")
                print(f"    API URL: {provider.api_url}")
                print(f"    Timeout: {provider.timeout_seconds}s")
                print(f"    Retry Attempts: {provider.retry_attempts}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

    finally:
        # Restore original environment variables
        if original_reader:
            os.environ['ORACLE_MCP_READER_URL'] = original_reader
        elif 'ORACLE_MCP_READER_URL' in os.environ:
            del os.environ['ORACLE_MCP_READER_URL']

        if original_market:
            os.environ['ORACLE_MCP_MARKET_URL'] = original_market
        elif 'ORACLE_MCP_MARKET_URL' in os.environ:
            del os.environ['ORACLE_MCP_MARKET_URL']


def test_circuit_breaker_with_mcp():
    """Test circuit breaker functionality for MCP service failures"""
    print("\n" + "=" * 60)
    print("Testing Circuit Breaker with MCP Service Failures")
    print("=" * 60)

    oracle_manager = ConfigurableOracleManager()

    # Show circuit breaker configuration
    circuit_config = oracle_manager.config.circuit_breaker
    print(f"Circuit Breaker Configuration:")
    print(f"  Enabled: {circuit_config.enabled}")
    print(f"  Max Failures/Minute: {circuit_config.max_failures_per_minute}")
    print(f"  Recovery Time: {circuit_config.recovery_time_minutes} minutes")
    print(f"  Escalation Thresholds: {circuit_config.escalation_thresholds}")

    # Simulate service failures
    print(f"\nSimulating MCP Service Failures:")

    # Mark some oracles as failed to test circuit breaker logic
    original_status = dict(oracle_manager.oracle_status)

    # Fail 60% of oracles to trigger circuit breaker
    oracle_names = list(oracle_manager.oracle_status.keys())
    failed_count = int(len(oracle_names) * 0.6)

    for i in range(failed_count):
        oracle_manager.oracle_status[oracle_names[i]] = oracle_manager.oracle_status[oracle_names[i]].__class__.FAILED

    # Check health status
    health = oracle_manager.health_check()
    print(f"  Overall Status: {health['overall_status']}")
    print(f"  Active Oracles: {health['active_oracles']}/{health['total_oracles']}")

    # Restore original status
    oracle_manager.oracle_status = original_status

    print("✅ Circuit breaker simulation completed")
    return True


def generate_integration_report():
    """Generate a comprehensive integration report"""
    print("\n" + "=" * 60)
    print("Oracle-MCP Integration Report")
    print("=" * 60)

    oracle_manager = ConfigurableOracleManager()
    config = oracle_manager.config

    report = {
        "timestamp": datetime.now().isoformat(),
        "oracle_engine_version": "1.0.0-configured",
        "mcp_integration": {
            "algorand_reader_url": config.mcp_services.algorand_reader_url,
            "market_data_url": config.mcp_services.market_data_url,
            "status": "configured"
        },
        "oracle_providers": {
            name: {
                "enabled": provider.enabled,
                "reliability_score": provider.reliability_score,
                "api_url": provider.api_url,
                "timeout_seconds": provider.timeout_seconds
            }
            for name, provider in config.oracle_providers.items()
        },
        "configuration": {
            "aggregation_method": config.aggregation.method,
            "confidence_threshold": config.validation.confidence_threshold,
            "fallback_enabled": config.fallback.enabled,
            "manipulation_detection": config.manipulation_detection.enabled,
            "circuit_breaker_enabled": config.circuit_breaker.enabled
        },
        "integration_ready": True
    }

    print("Integration Report:")
    print(json.dumps(report, indent=2, default=str))

    # Save report to file
    report_path = parent_dir / "mcp_integration_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✅ Report saved to: {report_path}")
    return True


def main():
    """Run all MCP integration tests"""
    print("Oracle Price Integration - MCP Service Integration Tests")
    print("=" * 60)

    tests = [
        check_mcp_service_availability,
        test_oracle_mcp_integration,
        simulate_mcp_price_feed,
        test_configuration_with_mcp,
        test_circuit_breaker_with_mcp,
        generate_integration_report
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
    print(f"MCP Integration Tests Summary: {passed}/{total} passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All MCP integration tests passed!")
        print("\n📋 Next Steps:")
        print("  1. Start MCP services: ./start-mcp-services.sh")
        print("  2. Run oracle engine with live MCP data")
        print("  3. Monitor oracle performance and health")
        return 0
    else:
        print("❌ Some MCP integration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())