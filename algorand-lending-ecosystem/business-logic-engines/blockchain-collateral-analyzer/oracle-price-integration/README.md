# Oracle Price Integration Engine

A configuration-driven oracle price integration system for the Algorand lending ecosystem that provides reliable, multi-source price feeds with fallback mechanisms and manipulation detection.

## Overview

The Oracle Price Integration Engine aggregates price data from multiple oracle providers to deliver consensus pricing with confidence scoring. It features comprehensive configuration management, circuit breakers, and seamless integration with MCP services.

## Key Features

✅ **Configuration-Driven Architecture**: YAML-based configuration with environment variable overrides
✅ **Multi-Oracle Support**: Chainlink, Pyth, Algorand Native, DIA, and custom providers
✅ **Price Aggregation**: Multiple aggregation methods (weighted median, weighted mean, median, mean)
✅ **Fallback Mechanisms**: Emergency price feeds when oracles fail
✅ **Manipulation Detection**: Configurable risk assessment and anomaly detection
✅ **Circuit Breakers**: Automatic failover and recovery mechanisms
✅ **Health Monitoring**: Real-time oracle status tracking
✅ **MCP Integration**: Ready for integration with MCP services on ports 8002/8003
✅ **Asset-Specific Configuration**: Per-asset refresh intervals and thresholds

## Directory Structure

```
oracle-price-integration/
├── config/
│   └── config.yaml                 # Main configuration file
├── core/
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   └── oracle_engine.py            # Advanced oracle engine (alternative implementation)
├── notebooks/
│   └── oracle_config_testing.ipynb # Interactive testing notebook
├── tests/
│   ├── test_config.py             # Configuration system tests
│   └── test_oracle_engine.py      # Oracle engine functionality tests
├── oracle_integration_configured.py # Main oracle integration module
├── test_mcp_integration.py        # MCP service integration tests
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Configuration

### YAML Configuration (config/config.yaml)

The system is configured through a comprehensive YAML file that includes:

- **MCP Service URLs**: Algorand reader and market data service endpoints
- **Oracle Providers**: Individual oracle configurations with reliability scores
- **Validation Settings**: Confidence thresholds and data quality requirements
- **Aggregation Methods**: Price aggregation strategies and weights
- **Fallback Mechanisms**: Emergency prices and backup data sources
- **Manipulation Detection**: Risk assessment parameters and thresholds
- **Circuit Breakers**: Failure detection and recovery settings
- **Asset-Specific Settings**: Per-asset refresh intervals and overrides

### Environment Variable Overrides

Key settings can be overridden via environment variables:

```bash
export ORACLE_MCP_READER_URL="http://localhost:8002"
export ORACLE_MCP_MARKET_URL="http://localhost:8003"
export ORACLE_CHAINLINK_API_KEY="your-api-key"
export ORACLE_PYTH_API_KEY="your-api-key"
export ORACLE_LOG_LEVEL="DEBUG"
```

## Usage

### Basic Usage

```python
from oracle_integration_configured import ConfigurableOracleManager

# Initialize with default configuration
oracle_manager = ConfigurableOracleManager()

# Get reliable price for an asset
price = oracle_manager.get_reliable_price("ALGO")
if price:
    print(f"ALGO Price: ${price.consensus_price:.4f}")
    print(f"Confidence: {price.price_confidence:.2f}")
    print(f"Oracle Count: {price.oracle_count}")
```

### Advanced Usage

```python
from pathlib import Path
from oracle_integration_configured import ConfigurableOracleManager

# Initialize with custom configuration
config_path = Path("custom_config.yaml")
oracle_manager = ConfigurableOracleManager(config_path)

# Get price feeds from all oracles
feeds = oracle_manager.get_price_feeds("ALGO")
for feed in feeds:
    print(f"{feed.oracle_name}: ${feed.price_usd:.4f}")

# Aggregate prices manually
aggregated = oracle_manager.aggregate_prices(feeds)
print(f"Consensus: ${aggregated.consensus_price:.4f}")

# Check for price manipulation
manipulation = oracle_manager.detect_price_manipulation("ALGO")
print(f"Risk Level: {manipulation['manipulation_risk']}")

# Health check
health = oracle_manager.health_check()
print(f"Status: {health['overall_status']}")
```

## Testing

### Configuration Tests

Test the configuration system:

```bash
cd oracle-price-integration
python tests/test_config.py
```

### Oracle Engine Tests

Test oracle functionality:

```bash
python tests/test_oracle_engine.py
```

### MCP Integration Tests

Test MCP service integration:

```bash
python test_mcp_integration.py
```

### Interactive Testing

Use the Jupyter notebook for interactive testing:

```bash
jupyter notebook notebooks/oracle_config_testing.ipynb
```

## Oracle Providers

### Supported Providers

1. **Chainlink**
   - High reliability (0.95)
   - Low latency (30s)
   - Production-ready

2. **Pyth Network**
   - High reliability (0.92)
   - Very low latency (5s)
   - Real-time data

3. **Algorand Native**
   - Highest reliability (0.98)
   - Minimal latency (1s)
   - Native blockchain data

4. **DIA Data**
   - Moderate reliability (0.85)
   - Higher latency (60s)
   - Diverse data sources

### Adding Custom Oracles

Add new oracle providers in the configuration:

```yaml
oracle_providers:
  custom_oracle:
    enabled: true
    api_url: "https://api.custom-oracle.com"
    api_key: null
    variance: 0.002
    latency_seconds: 15
    reliability_score: 0.90
    timeout_seconds: 10
    retry_attempts: 3
```

## Price Aggregation

### Aggregation Methods

- **weighted_median**: Robust against outliers, uses reliability weights
- **weighted_mean**: Standard weighted average
- **median**: Simple median of all prices
- **mean**: Simple average of all prices

### Weight Factors

Configurable weight factors for aggregation:

- **reliability_weight**: Oracle historical reliability (0.4)
- **confidence_weight**: Individual feed confidence (0.3)
- **freshness_weight**: Data freshness/staleness (0.2)
- **volume_weight**: Trading volume consideration (0.1)

## Fallback Mechanisms

### Emergency Prices

When all oracles fail, the system can use emergency fallback prices:

```yaml
fallback:
  enabled: true
  max_staleness_minutes: 60
  emergency_prices:
    ALGO: 0.25
    USDC: 1.00
    BTC: 45000.0
```

### Fallback Sources (Priority Order)

1. Cached prices (recent valid data)
2. Emergency prices (configured static prices)
3. External API backup (alternative data sources)

## Manipulation Detection

### Risk Factors

The system monitors for:

- **High Volatility**: Unusual price swings
- **Large Price Ranges**: Extreme price differences
- **Poor Oracle Consensus**: Disagreement between oracles
- **Insufficient Coverage**: Too few oracle sources

### Risk Levels

- **Minimal**: Normal operation
- **Low**: Minor anomalies detected
- **Medium**: Moderate risk, increased monitoring
- **High**: Significant risk, manual review required

## Circuit Breakers

### Escalation Thresholds

- **Warning**: 30% oracle failures
- **Critical**: 60% oracle failures
- **Emergency**: 80% oracle failures

### Recovery Mechanisms

- Automatic retry with exponential backoff
- Service health monitoring
- Gradual re-enablement of failed oracles

## MCP Service Integration

### Service Endpoints

- **Algorand Reader**: `http://localhost:8002` - Blockchain data and native prices
- **Market Data**: `http://localhost:8003` - External market data and price feeds

### Integration Flow

1. Oracle engine fetches data from MCP services
2. Applies oracle-specific variance and reliability scoring
3. Aggregates using configured methods
4. Validates against configured thresholds
5. Returns consensus price with confidence score

## Asset-Specific Configuration

### Priority Levels

- **High Priority**: 5-second refresh (ALGO, USDC)
- **Medium Priority**: 30-second refresh (BTC, ETH)
- **Low Priority**: 5-minute refresh (other assets)

### Override Settings

Each asset can have custom:
- Refresh intervals
- Confidence thresholds
- Staleness limits

## Monitoring and Alerting

### Health Metrics

- Oracle uptime and response times
- Price consensus strength
- Manipulation risk scores
- Circuit breaker status

### Alert Thresholds

- Oracle failure rate > 20%
- Consensus failure rate > 10%
- Average latency > 5000ms

## Dependencies

```
pyyaml>=6.0
requests>=2.28.0
aiohttp>=3.8.0
```

## Performance Considerations

### Optimization Features

- Configurable caching with TTL
- Asynchronous oracle requests
- Efficient price aggregation algorithms
- Circuit breakers to prevent cascading failures

### Scalability

- Horizontal scaling support
- Load balancing across oracle providers
- Configurable retry mechanisms
- Graceful degradation under load

## Security Considerations

### API Key Management

- Environment variable storage
- Rotation support
- Per-oracle authentication

### Data Validation

- Price deviation limits
- Confidence thresholds
- Manipulation detection
- Staleness checks

## Integration with Lending Platform

The oracle engine integrates seamlessly with the Algorand lending platform:

1. **Collateral Valuation**: Real-time asset pricing for collateral assessment
2. **Liquidation Triggers**: Reliable price feeds for liquidation decisions
3. **Risk Management**: Manipulation detection for risk mitigation
4. **Health Monitoring**: System status for operational awareness

## Future Enhancements

- [ ] Additional oracle provider integrations
- [ ] Machine learning-based manipulation detection
- [ ] Advanced price prediction models
- [ ] Real-time streaming price feeds
- [ ] Enhanced monitoring and alerting
- [ ] API rate limiting and optimization

## Support

For questions or issues related to the Oracle Price Integration Engine:

1. Check the configuration documentation
2. Run the test suites to verify functionality
3. Review the integration notebook for examples
4. Monitor oracle health status and logs

---

*Part of the Algorand Lending Ecosystem - Oracle Price Integration Engine v1.0.0*