# MCP Integration Test Framework

Comprehensive automated testing framework for integrating MCP (Model Context Protocol) services with Algorand lending engines. This framework provides thorough testing of data pipelines, service integration, and complete lending workflows.

## Overview

The framework tests integration between:

### MCP Services
- **Reader MCP** (localhost:8002) - Blockchain data reading and account information
- **Writer MCP** (localhost:3001) - Transaction execution and blockchain writes
- **Market Data MCP** (localhost:8789) - Real-time price feeds and market data

### Lending Engines
- **Collateral Analyzer** - Asset valuation and collateral analysis
- **Interest Rate Engine** - Dynamic interest rate calculation
- **Loan Approval Engine** - Comprehensive loan decision making
- **Risk Assessment Engine** - Cross-engine risk correlation analysis

## Key Features

- **Async Test Execution** - Concurrent testing for performance optimization
- **Real Data Integration** - Tests with actual blockchain data and market feeds
- **Mock/Real Data Switching** - Configurable data sources for different test scenarios
- **Performance Benchmarking** - Detailed metrics collection and analysis
- **Service Health Monitoring** - Continuous health checks and failure detection
- **Cross-Engine Integration** - Tests integration between all lending components
- **Error Handling & Recovery** - Comprehensive error scenarios and fallback testing
- **Comprehensive Reporting** - Detailed test results with multiple output formats

## Quick Start

### Prerequisites

1. **MCP Services Running**:
   ```bash
   # Reader MCP on port 8002
   # Writer MCP on port 3001
   # Market Data MCP on port 8789
   ```

2. **Lending Engines Available**:
   ```bash
   # Ensure algorand-lending-business-logic is accessible
   export PYTHONPATH="/path/to/algorand-lending-ecosystem/algorand-lending-business-logic:$PYTHONPATH"
   ```

3. **Dependencies**:
   ```bash
   pip install aiohttp asyncio
   ```

### Running Tests

#### Run All Tests
```bash
cd /home/mpo/algorand-showcase/tests/mcp_integration
python run_all_tests.py
```

#### Run Individual Test Suites

**Framework Tests** (Basic connectivity and health):
```bash
python test_framework.py
```

**Data Pipeline Tests** (Data quality and consistency):
```bash
python test_data_pipeline.py
```

**End-to-End Tests** (Complete lending workflows):
```bash
python test_end_to_end.py
```

#### Custom Configuration
```bash
python run_all_tests.py \
    --reader-url http://localhost:8002 \
    --writer-url http://localhost:3001 \
    --market-data-url http://localhost:8789 \
    --performance-mode \
    --concurrent-requests 10 \
    --timeout 45
```

## Test Suites

### 1. Framework Tests (`test_framework.py`)

**Purpose**: Basic connectivity, health checks, and service integration validation.

**Tests Include**:
- MCP service connectivity and health monitoring
- Data pipeline integration between services
- Lending engine performance benchmarking
- Cross-service data correlation

**Key Metrics**:
- Service response times
- Success rates across all services
- Engine processing performance
- Data consistency checks

### 2. Data Pipeline Tests (`test_data_pipeline.py`)

**Purpose**: Comprehensive data quality, validation, and pipeline testing.

**Tests Include**:
- Account data retrieval and validation
- Asset information accuracy and consistency
- Market data freshness and reasonableness
- Cross-service data correlation
- Performance under concurrent load
- Error handling and recovery

**Data Validation**:
- Account structure and field validation
- Asset parameter completeness
- Market data timestamp freshness
- Price reasonableness checks
- Data consistency across services

### 3. End-to-End Tests (`test_end_to_end.py`)

**Purpose**: Complete lending workflow testing with real-world scenarios.

**Test Scenarios**:
- Conservative ALGO loans with USDC collateral
- High-value multi-asset collateral loans
- Risky loans during volatile market conditions
- Under-collateralized loan rejections
- Optimal DeFi yield farming loans

**Workflow Steps Tested**:
1. Market data gathering and validation
2. Borrower profile analysis from blockchain
3. Comprehensive collateral analysis
4. Multi-factor risk assessment
5. Dynamic interest rate calculation
6. Final loan approval decision
7. Transaction preparation (mock)
8. End-to-end workflow validation

## Configuration

### Service Configuration

```python
from test_framework import ServiceConfig

config = ServiceConfig(
    reader_url="http://localhost:8002",
    writer_url="http://localhost:3001",
    market_data_url="http://localhost:8789",
    timeout=30,
    retry_attempts=3,
    retry_delay=1.0
)
```

### Pipeline Configuration

```python
from test_data_pipeline import PipelineTestConfig

config = PipelineTestConfig(
    use_real_data=True,
    performance_mode=True,
    concurrent_requests=5,
    data_consistency_checks=True,
    error_injection=False,
    timeout_multiplier=1.0
)
```

## Test Scenarios

### Loan Test Scenarios

The framework includes comprehensive loan scenarios:

1. **Conservative Loans**: Low-risk scenarios with sufficient collateral
2. **High-Value Loans**: Large loans with multi-asset collateral
3. **Volatile Market**: Testing under market stress conditions
4. **Edge Cases**: Under-collateralized and risky scenarios
5. **Optimal Conditions**: Best-case scenarios for yield farming

### Performance Testing

- **Concurrent Load**: Multiple simultaneous requests
- **Service Stress**: High-frequency API calls
- **Engine Performance**: Lending engine processing speed
- **Data Throughput**: Large dataset processing

## Output and Reporting

### Test Results

Results are saved in multiple formats:

- **JSON**: Detailed machine-readable results
- **Text**: Human-readable summary reports
- **Console**: Real-time progress and summary

### Sample Output Location

```
/home/mpo/algorand-showcase/tests/mcp_integration/
├── comprehensive_test_results_20240920_143022.json
├── test_summary_20240920_143022.txt
├── pipeline_test_results_20240920_143015.json
└── e2e_test_results_20240920_143018.json
```

### Report Contents

- **Execution Summary**: Overall success/failure status
- **Service Health**: MCP service availability and performance
- **Performance Metrics**: Response times, throughput, success rates
- **Test Details**: Individual test results and errors
- **Recommendations**: Actionable insights for improvements

## Performance Metrics

The framework collects detailed performance metrics:

### Response Time Metrics
- Average service response times
- P95/P99 percentiles for latency analysis
- Service-specific performance breakdown

### Throughput Metrics
- Requests per second capabilities
- Concurrent request handling
- Data processing throughput

### Success Rate Metrics
- Service availability percentages
- Test pass rates by category
- Error rate analysis

### Engine Performance
- Lending engine processing times
- Cross-engine correlation performance
- Memory usage and efficiency

## Error Handling

### Automatic Recovery
- Service retry logic with exponential backoff
- Fallback mechanisms for service failures
- Graceful degradation when services are unavailable

### Error Categories
- **Network Errors**: Connection timeouts, service unavailable
- **Data Errors**: Invalid responses, missing fields
- **Logic Errors**: Inconsistent results between engines
- **Performance Errors**: Slow responses, resource exhaustion

## Troubleshooting

### Common Issues

**Services Not Available**:
```bash
# Check if MCP services are running
curl http://localhost:8002/health
curl http://localhost:3001/health
curl http://localhost:8789/health
```

**Lending Engines Not Found**:
```bash
# Verify Python path includes lending engines
python -c "from algorand_lending_bl import CollateralAnalyzer"
```

**Performance Issues**:
- Reduce concurrent_requests parameter
- Increase timeout values
- Check system resources

### Debug Mode

Enable debug logging:
```bash
python run_all_tests.py --log-level DEBUG
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: MCP Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Start MCP Services
        run: |
          # Start your MCP services here

      - name: Run Integration Tests
        run: |
          cd tests/mcp_integration
          python run_all_tests.py --performance-mode

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: tests/mcp_integration/*_results_*.json
```

## Architecture

### Framework Components

```
┌─────────────────────────────────────────────────────────────┐
│                 MCP Integration Test Framework               │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │  Framework      │ │  Data Pipeline  │ │  End-to-End     │ │
│ │  Tests          │ │  Tests          │ │  Tests          │ │
│ │                 │ │                 │ │                 │ │
│ │ • Connectivity  │ │ • Data Quality  │ │ • Loan Scenarios│ │
│ │ • Health Checks │ │ • Validation    │ │ • Full Workflow │ │
│ │ • Performance   │ │ • Consistency   │ │ • Integration   │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    MCP Service Clients                      │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │  Reader MCP     │ │  Writer MCP     │ │ Market Data MCP │ │
│ │  :8002          │ │  :3001          │ │  :8789          │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Lending Engines                          │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │  Collateral     │ │  Interest Rate  │ │  Loan Approval  │ │
│ │  Analyzer       │ │  Engine         │ │  Engine         │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│ ┌─────────────────┐                                         │
│ │  Risk           │                                         │
│ │  Assessment     │                                         │
│ └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

## Contributing

### Adding New Tests

1. **Extend Test Scenarios**: Add new loan scenarios to `test_end_to_end.py`
2. **Add Data Validators**: Extend validation logic in `test_data_pipeline.py`
3. **Performance Tests**: Add new benchmarks to `test_framework.py`

### Custom Metrics

Implement custom performance metrics:

```python
from test_framework import PerformanceMetrics

# Add custom metric
metric = PerformanceMetrics(
    operation="custom_operation",
    duration=1.5,
    success=True,
    timestamp=datetime.now(),
    service="custom_service",
    engine="custom_engine"
)
framework.add_performance_metric(metric)
```

## License

This testing framework is part of the Algorand Lending Platform and follows the same licensing terms.

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review error logs in the output files
3. Enable debug mode for detailed logging
4. Contact the development team for framework-specific issues