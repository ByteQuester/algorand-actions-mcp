"""
Integration Tests for Blockchain Collateral Analyzer

This package contains comprehensive integration tests for all 6 engines
in the blockchain collateral analyzer system.

Test Modules:
- conftest.py: Shared fixtures and test configuration
- test_cross_engine_workflow.py: Cross-engine workflow tests
- test_mcp_integration.py: MCP service integration tests
- test_end_to_end_scenarios.py: Complete lending scenario tests
- test_performance.py: Performance benchmarking tests

Usage:
    # Run all integration tests
    python -m pytest integration_tests/

    # Run specific test module
    python -m pytest integration_tests/test_cross_engine_workflow.py

    # Run with coverage
    python -m pytest integration_tests/ --cov=../ --cov-report=html

    # Run performance tests only
    python -m pytest integration_tests/test_performance.py

    # Use the convenient script
    ./run_integration_tests.sh
"""

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

# Test categories for pytest markers
PYTEST_MARKERS = {
    "slow": "Tests that take longer than 30 seconds",
    "stress": "Stress/load testing scenarios",
    "mcp": "Tests requiring MCP services",
    "e2e": "End-to-end scenario tests",
    "performance": "Performance benchmarking tests",
    "cross_engine": "Cross-engine workflow tests"
}

# Test configuration constants
TEST_CONFIG = {
    "default_timeout": 300,  # 5 minutes
    "mcp_reader_url": "http://localhost:8002",
    "mcp_writer_url": "http://localhost:8003",
    "max_concurrent_requests": 25,
    "performance_tolerance": 0.1  # 10% performance tolerance
}

# Engine test priorities (for sequential testing if needed)
ENGINE_PRIORITIES = {
    "oracle": 1,     # Lowest latency, test first
    "valuation": 2,  # Depends on oracle
    "volatility": 3, # Independent analysis
    "portfolio": 4,  # Portfolio analysis
    "collateral": 5, # Depends on multiple engines
    "liquidation": 6 # Final decision making
}

__all__ = [
    "__version__",
    "__author__",
    "PYTEST_MARKERS",
    "TEST_CONFIG",
    "ENGINE_PRIORITIES"
]