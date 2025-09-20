# Blockchain Collateral Analyzer Integration Tests

Comprehensive integration testing suite for the blockchain collateral analyzer system, covering all 6 engines and their interactions.

## Overview

This test suite verifies that all engines work together correctly and can handle real-world lending scenarios through:

- **Cross-engine workflow testing** - Data flow between engines
- **MCP service integration** - Communication with Model Context Protocol services
- **End-to-end lending scenarios** - Complete lending workflows from application to liquidation
- **Performance benchmarking** - Response times, throughput, and resource usage

## Test Structure

### Test Files

1. **`conftest.py`** - Shared test fixtures, mock services, and test utilities
2. **`test_cross_engine_workflow.py`** - Cross-engine workflow integration tests
3. **`test_mcp_integration.py`** - MCP service integration tests
4. **`test_end_to_end_scenarios.py`** - Complete lending scenario tests
5. **`test_performance.py`** - Performance benchmarking tests

### Engines Covered

1. **Collateral Requirements Engine** - Collateral analysis and risk assessment
2. **Digital Asset Valuation Engine** - Asset pricing and valuation
3. **Oracle Price Integration Engine** - Price data fetching and validation
4. **Portfolio Diversification Engine** - Portfolio analysis and diversification
5. **Volatility Assessment Engine** - Volatility calculations and risk metrics
6. **Liquidation Scenarios Engine** - Liquidation planning and execution

## Quick Start

### Using the Test Runner Script

```bash
# Run all integration tests
./run_integration_tests.sh

# Run with setup and MCP service check
./run_integration_tests.sh -s -m

# Run specific test suite
./run_integration_tests.sh performance

# Run with coverage reporting
./run_integration_tests.sh -c -r all

# Get help
./run_integration_tests.sh --help
```

### Using pytest Directly

```bash
# Run all tests
python -m pytest integration_tests/

# Run specific test file
python -m pytest integration_tests/test_cross_engine_workflow.py

# Run with verbose output
python -m pytest integration_tests/ -v

# Run performance tests only
python -m pytest integration_tests/test_performance.py

# Run with coverage
python -m pytest integration_tests/ --cov=../ --cov-report=html
```

## Test Categories

### Cross-Engine Workflow Tests

Tests the complete workflows that span multiple engines:

- **Portfolio → Risk → Liquidation workflow**
- **Oracle → Volatility → Collateral workflow**
- **Complete lending decision pipeline**
- **Data consistency across engines**
- **Error propagation handling**
- **Concurrent cross-engine operations**

Example test:
```python
async def test_portfolio_to_risk_to_liquidation_workflow(all_engines):
    # Step 1: Portfolio analysis
    portfolio_result = await engines["portfolio"].analyze_portfolio(...)

    # Step 2: Risk assessment using portfolio data
    risk_result = await engines["collateral"].assess_collateral_risk(...)

    # Step 3: Liquidation scenario analysis
    liquidation_scenarios = await engines["liquidation"].analyze_liquidation_scenarios(...)
```

### MCP Service Integration Tests

Tests integration with Model Context Protocol services on ports 8002/8003:

- **Basic connectivity to all engines**
- **Reader service integration (port 8002)**
- **Writer service integration (port 8003)**
- **Health checks and service monitoring**
- **Resilience and error handling**
- **Timeout and partial failure handling**
- **Data integrity in MCP operations**
- **Performance under concurrent access**

Example test:
```python
async def test_all_engines_mcp_connectivity(all_engines, mock_mcp_services):
    for engine_name, engine in all_engines.items():
        await assert_mcp_connectivity(engine, engine_name)
```

### End-to-End Lending Scenarios

Tests complete lending scenarios from application to liquidation:

- **Conservative high-value loans**
- **High-risk borrower edge cases**
- **Institutional large loans**
- **Bear market stress scenarios**
- **Market crash scenarios**
- **Liquidity crisis scenarios**
- **Ongoing loan monitoring**
- **Early warning systems**

Example borrower profiles:
```python
conservative_investor = BorrowerProfile(
    credit_score=850,
    risk_level="low",
    collateral_preference=["ALGO", "USDC"],
    max_loan_amount=500000.0
)
```

### Performance Benchmarking Tests

Tests performance characteristics and scalability:

- **Individual engine response times**
- **Throughput testing**
- **Concurrent request handling**
- **Memory usage monitoring**
- **Scalability with portfolio size**
- **Sustained load testing**

Performance benchmarks:
- Collateral analysis: < 3.0s response time
- Asset valuation: < 2.0s response time
- Oracle price fetch: < 1.0s response time
- Portfolio analysis: < 4.0s response time
- Volatility calculation: < 3.5s response time
- Liquidation analysis: < 5.0s response time

## Configuration

### Environment Variables

- `MCP_READER_URL` - MCP reader service URL (default: http://localhost:8002)
- `MCP_WRITER_URL` - MCP writer service URL (default: http://localhost:8003)
- `TEST_TIMEOUT` - Test timeout in seconds (default: 300)
- `PYTEST_WORKERS` - Number of parallel workers (default: auto)

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only fast tests
pytest -m "not slow and not stress"

# Run only MCP integration tests
pytest -m mcp

# Run only performance tests
pytest -m performance

# Run stress tests
pytest -m stress
```

Available markers:
- `slow` - Tests taking longer than 30 seconds
- `stress` - Stress/load testing scenarios
- `mcp` - Tests requiring MCP services
- `e2e` - End-to-end scenario tests
- `performance` - Performance benchmarking tests
- `cross_engine` - Cross-engine workflow tests

## Mock Services

The test suite includes comprehensive mock services to ensure tests can run without external dependencies:

### MockMCPService

Simulates MCP reader and writer services:
- Health checks
- Asset information endpoints
- Price data endpoints
- Data storage and retrieval

### Mock Asset Data

Predefined mock data for testing:
- ALGO (Algorand native token)
- USDC (USD Coin stablecoin)
- USDT (Tether stablecoin)
- Historical price data
- Market conditions

### Test Data Generators

Utilities for generating test data:
- Portfolio positions
- Price history
- Market conditions
- Borrower profiles
- Lending scenarios

## Test Fixtures

### Engine Fixtures

Each engine has a dedicated fixture that:
- Initializes the engine with test configuration
- Sets up mock MCP service connections
- Provides cleanup after tests
- Handles async lifecycle management

### Shared Fixtures

- `all_engines` - Dictionary of all 6 engine instances
- `mock_mcp_services` - Mock MCP reader and writer services
- `temp_database` - Temporary database for testing
- `sample_collateral_positions` - Sample collateral data
- `performance_monitor` - Performance monitoring utilities

## Running Tests

### Prerequisites

1. Python 3.8+
2. Virtual environment (recommended)
3. Required dependencies (installed by setup script)

### Installation

```bash
# Clone repository and navigate to integration tests
cd blockchain-collateral-analyzer/integration_tests

# Setup environment (installs dependencies)
../run_integration_tests.sh -s

# Or manually install dependencies
pip install pytest pytest-asyncio pytest-xdist pytest-cov aiohttp psutil
```

### Test Execution Options

#### Full Test Suite
```bash
# Run everything with setup and reporting
./run_integration_tests.sh -s -m -c -r
```

#### Quick Smoke Tests
```bash
# Fast tests only, skip slow/stress tests
./run_integration_tests.sh -f quick
```

#### Performance Testing
```bash
# Performance benchmarks with detailed reporting
./run_integration_tests.sh -v -r performance
```

#### Parallel Execution
```bash
# Run tests in parallel for faster execution
./run_integration_tests.sh -p
```

#### Coverage Analysis
```bash
# Generate coverage report
./run_integration_tests.sh -c -r
# View coverage report: htmlcov/index.html
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all engines are properly installed
   - Check PYTHONPATH includes project root
   - Run setup: `./run_integration_tests.sh -s`

2. **MCP Service Connection Failures**
   - Start MCP services: `./start-mcp-services.sh`
   - Use mock services: Tests fallback automatically
   - Check ports 8002 and 8003 are available

3. **Test Timeouts**
   - Increase timeout: `TEST_TIMEOUT=600 pytest ...`
   - Use fast mode: `./run_integration_tests.sh -f`
   - Check system resources

4. **Memory Issues**
   - Run tests sequentially: Avoid `-p` flag
   - Monitor memory usage during tests
   - Ensure adequate system memory (>2GB recommended)

5. **Performance Test Failures**
   - Check system load during tests
   - Adjust performance benchmarks if needed
   - Run on dedicated test environment

### Debug Mode

```bash
# Run with maximum verbosity and no capture
pytest integration_tests/ -vvv -s --tb=long

# Run single test with debugging
pytest integration_tests/test_cross_engine_workflow.py::test_portfolio_to_risk_to_liquidation_workflow -vvv -s
```

## Contributing

### Adding New Tests

1. **Follow naming convention**: `test_*.py` for files, `test_*` for functions
2. **Use appropriate markers**: Add `@pytest.mark.slow` for long tests
3. **Include documentation**: Document test purpose and expected behavior
4. **Handle async properly**: Use `@pytest.mark.asyncio` for async tests
5. **Clean up resources**: Ensure proper cleanup in fixtures

### Test Structure Guidelines

```python
class TestNewFeature:
    """Test class for new feature"""

    @pytest.mark.asyncio
    async def test_basic_functionality(self, all_engines):
        """Test basic functionality of new feature"""
        # Arrange
        test_data = create_test_data()

        # Act
        result = await all_engines["engine"].new_method(test_data)

        # Assert
        assert result is not None
        assert result["status"] == "success"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_performance(self, all_engines, performance_monitor):
        """Test performance characteristics"""
        performance_monitor.start()

        # Test execution
        result = await all_engines["engine"].complex_operation()

        performance_monitor.stop()

        # Verify performance
        assert performance_monitor.get_duration() < 5.0
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Minimal test run for CI
./run_integration_tests.sh -q -f quick

# Full test suite with coverage for main branch
./run_integration_tests.sh -s -m -c -r all

# Performance regression testing
./run_integration_tests.sh performance
```

## Support

For issues or questions about the integration tests:

1. Check this documentation
2. Review test logs and error messages
3. Check individual engine documentation
4. Verify MCP service status
5. Run setup script: `./run_integration_tests.sh -s`

The integration test suite is designed to provide comprehensive validation of the blockchain collateral analyzer system while being maintainable and easy to extend.