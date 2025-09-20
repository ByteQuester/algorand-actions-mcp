# Volatility Assessment Engine - Configurable Implementation

This directory contains a configurable implementation of the volatility assessment engine that extracts parameters from the original `oracle_integration.py` and makes them configurable via YAML files.

## Overview

The volatility assessment engine provides:
- **Price staleness scoring** with configurable thresholds
- **Volatility calculation** with configurable windows and parameters
- **Price manipulation detection** with configurable risk factors and weights
- **Oracle confidence scoring** with configurable reliability weights
- **MCP service integration** for real-time data feeds

## File Structure

```
volatility-assessment/
├── config/
│   └── config.yaml              # Main configuration file
├── core/
│   ├── __init__.py              # Module initialization
│   ├── config.py                # Configuration loading and management
│   └── volatility_engine.py     # Main volatility assessment engine
├── notebooks/
│   └── volatility_assessment_demo.ipynb  # Jupyter demonstration
├── test_volatility_assessment.py         # Basic functionality tests
├── test_mcp_integration.py              # MCP integration tests
└── README.md                            # This file
```

## Key Configuration Parameters

### Price Staleness Scoring (from `_calculate_staleness_score`)
- **Fresh data** (<30s): Score 1.0
- **Good data** (<5m): Score 0.9
- **Acceptable data** (<15m): Score 0.7
- **Stale data** (<1h): Score 0.5
- **Very stale data** (>1h): Declining score

### Manipulation Detection (from `detect_price_manipulation`)
- **Volatility threshold**: 10% triggers high risk
- **Price range threshold**: 20% triggers suspicious activity
- **Oracle consensus threshold**: <80% triggers alert
- **Risk scoring weights**: Configurable for volatility, price range, consensus

### Oracle Confidence
- **Minimum confidence**: 80% default threshold
- **Single oracle penalty**: 20% confidence reduction
- **Reliability weights**: Consensus (40%), staleness (30%), reliability (30%)

## Usage

### Basic Usage

```python
from core.volatility_engine import VolatilityAssessmentEngine

# Initialize with default configuration
engine = VolatilityAssessmentEngine()

# Setup demo oracles
engine.setup_demo_oracles()

# Assess volatility for an asset
metrics = engine.assess_volatility("ALGO")
print(f"Risk level: {metrics.manipulation_risk_level}")
print(f"Stability score: {metrics.price_stability_score}")
```

### Configuration Customization

Edit `config/config.yaml` to customize parameters:

```yaml
# Example: Make manipulation detection more sensitive
manipulation_detection:
  risk_thresholds:
    volatility_high: 0.05        # 5% instead of 10%
    consensus_poor: 0.90         # 90% instead of 80%

# Example: Adjust staleness scoring
price_staleness:
  scoring_thresholds:
    fresh: 15                    # 15s instead of 30s
    good: 180                    # 3m instead of 5m
```

### Environment Variable Overrides

```bash
export VOLATILITY_MCP_READER_URL=http://localhost:8002
export VOLATILITY_MCP_MARKET_URL=http://localhost:8003
export VOLATILITY_MIN_CONFIDENCE=0.9
export VOLATILITY_CACHE_SECONDS=60
```

## Testing

### Basic Functionality Tests
```bash
python test_volatility_assessment.py
```

### MCP Integration Tests (requires MCP services running)
```bash
python test_mcp_integration.py
```

### Jupyter Demonstration
```bash
jupyter notebook notebooks/volatility_assessment_demo.ipynb
```

## MCP Service Integration

The engine integrates with two MCP services:
- **Algorand Reader MCP** (port 8002): Blockchain data and asset information
- **Market Data MCP** (port 8003): Real-time price feeds and market data

### Starting MCP Services

Ensure both services are running before using MCP integration features:

```bash
# Start Algorand Reader MCP (port 8002)
cd apps/mcp-services/algorand-reader-mcp
npm start

# Start Market Data MCP (port 8003)
cd apps/mcp-services/market-data-mcp
npm start
```

## Configuration Reference

### Complete Configuration Sections

1. **MCP Services**: Service URLs and endpoints
2. **Price Staleness**: Scoring thresholds and values
3. **Volatility Calculation**: Lookback periods and windows
4. **Manipulation Detection**: Risk thresholds and scoring weights
5. **Oracle Confidence**: Reliability weights and penalty factors
6. **Market Analysis**: Asset categorization and volume thresholds
7. **Monitoring**: Alert thresholds and escalation levels
8. **Performance**: Caching and rate limiting settings
9. **Storage**: Data retention and cleanup policies
10. **Analysis**: Simulation and reporting parameters
11. **Database**: Storage configuration and backup settings

## Implementation Notes

### Extracted Parameters

The following hardcoded parameters from `oracle_integration.py` were made configurable:

**From `_calculate_staleness_score` (lines 224-246):**
- Time thresholds: 30s, 5m, 15m, 1h
- Score values: 1.0, 0.9, 0.7, 0.5
- Decline rate calculation

**From `detect_price_manipulation` (lines 271-349):**
- Volatility threshold: 0.1 (10%)
- Price range threshold: 0.2 (20%)
- Consensus threshold: 0.8 (80%)
- Risk level thresholds: 0.2, 0.4, 0.7
- Risk factor weights

**From price aggregation logic:**
- Confidence penalty for single oracle: 0.8
- Consensus strength for single oracle: 0.5
- Reliability weight distribution: 0.4, 0.3, 0.3

### Configuration Benefits

1. **Flexibility**: Easy parameter tuning without code changes
2. **Environment-specific**: Different configs for dev/staging/production
3. **Runtime modification**: Parameters can be adjusted during operation
4. **Auditability**: Configuration changes are tracked and versioned
5. **Testing**: Easy to test different parameter combinations

## Future Enhancements

1. **Real-time configuration updates**: Hot-reload configuration changes
2. **Advanced MCP integration**: Direct WebSocket connections for real-time feeds
3. **Machine learning integration**: AI-powered parameter optimization
4. **Multi-chain support**: Extend beyond Algorand to other blockchains
5. **Historical analysis**: Long-term volatility trend analysis
6. **Risk model sophistication**: More complex manipulation detection algorithms

## Contributing

When adding new configurable parameters:

1. Add the parameter to `config/config.yaml`
2. Update the corresponding dataclass in `core/config.py`
3. Update the `_merge_config` method to handle the new parameter
4. Add environment variable override if needed
5. Update tests to verify the new parameter works
6. Document the parameter in this README

## Dependencies

- `pyyaml`: YAML configuration file parsing
- `aiohttp`: Async HTTP client for MCP integration
- `statistics`: Statistical calculations
- `datetime`: Time-based calculations
- `dataclasses`: Configuration data structures