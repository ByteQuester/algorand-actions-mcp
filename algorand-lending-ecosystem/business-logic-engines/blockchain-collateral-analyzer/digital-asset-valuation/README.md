# Digital Asset Valuation Engine

A production-ready, configuration-driven digital asset valuation engine for Algorand lending platforms with MCP service integration.

## Overview

This engine provides comprehensive digital asset valuation and collateral analysis capabilities with the following features:

- **Configuration-driven architecture** - All parameters configurable via YAML
- **MCP service integration** - Real-time price feeds from MCP services on ports 8002 and 8003
- **Risk-based asset valuation** - Dynamic haircuts based on volatility and liquidity
- **Portfolio analysis** - Comprehensive collateral assessment and diversification analysis
- **Market condition adaptation** - Dynamic requirements based on market state
- **Stress testing** - Multiple scenario analysis capabilities
- **Flexible asset classification** - Configurable asset types and properties

## Architecture

```
digital-asset-valuation/
├── config/
│   └── config.yaml              # Main configuration file
├── core/
│   ├── __init__.py             # Core module exports
│   ├── config.py               # Configuration management classes
│   ├── constants.py            # Configurable constants wrapper
│   ├── calculator.py           # Risk calculation engine
│   └── engine.py               # Main valuation engine
├── tests/
│   ├── test_config.py          # Configuration system tests
│   └── test_mcp_integration.py # MCP integration tests
├── notebooks/
│   └── digital_asset_valuation_demo.ipynb  # Interactive demo
├── test_digital_asset_valuation.py         # Integration test script
└── README.md                   # This file
```

## Key Components

### 1. Configuration System (`core/config.py`)

- **DigitalAssetValuationConfig**: Complete configuration dataclass
- **DigitalAssetConfigLoader**: Loads and merges YAML configuration
- Environment variable overrides support
- Type-safe configuration with defaults

### 2. Constants Management (`core/constants.py`)

- **ConfigurableDigitalAssetConstants**: Configuration-driven constants
- Backward compatibility with hardcoded constants
- Dynamic parameter access based on configuration

### 3. Calculation Engine (`core/calculator.py`)

- **ConfigurableDigitalCollateralCalculator**: Risk calculation engine
- Asset haircut calculations with market conditions
- Portfolio diversification scoring
- Value at Risk (VaR) calculations
- Liquidation urgency assessment

### 4. Valuation Engine (`core/engine.py`)

- **DigitalAssetValuationEngine**: Main engine class
- MCP service integration for real-time pricing
- Asset creation and classification
- Portfolio analysis workflows
- Stress testing capabilities

## Configuration

### Main Configuration File: `config/config.yaml`

Key configuration sections:

```yaml
# MCP Service URLs
mcp_services:
  algorand_reader_url: "http://localhost:8002"
  market_data_url: "http://localhost:8003"

# Collateral ratios by asset type
default_collateral_ratios:
  algo_native: 1.5       # 150% for ALGO
  stablecoin: 1.1        # 110% for stablecoins
  asa_token: 2.0         # 200% for ASA tokens

# Risk parameters
risk_parameters:
  conservative:
    max_volatility_30d: 0.3
    min_liquidity_tier: "medium"
    max_correlation: 0.7
    min_market_cap: 100000000

# Analysis parameters
analysis:
  safety_buffer: 0.1               # 10% safety buffer
  cache_expiry_minutes: 5
  max_position_concentration: 0.6

# Asset-specific data
algorand_assets:
  ALGO:
    name: "Algorand"
    type: "algo_native"
    asset_id: "0"
    typical_volatility: 0.4
    liquidity_tier: "high"
```

### Environment Variable Overrides

- `DIGITAL_ASSET_MCP_READER_URL` - Override MCP reader service URL
- `DIGITAL_ASSET_MCP_MARKET_URL` - Override MCP market data service URL
- `DIGITAL_ASSET_DB_PATH` - Override database path

## Usage

### Basic Usage

```python
from core import DigitalAssetValuationEngine

# Initialize engine (loads config automatically)
engine = DigitalAssetValuationEngine()

# Get asset price (with MCP integration)
price = await engine.get_asset_price('ALGO')

# Create digital asset
asset = engine.create_digital_asset('ALGO', price)

# Create collateral position
position = engine.create_collateral_position(asset, 10000, "normal", price)

# Analyze portfolio
portfolio_data = [
    {'symbol': 'ALGO', 'quantity': 10000},
    {'symbol': 'USDC', 'quantity': 2000}
]

result = await engine.analyze_portfolio_collateral(
    portfolio_data,
    loan_amount_usd=3000,
    market_conditions="normal"
)
```

### Custom Configuration

```python
from pathlib import Path
from core import DigitalAssetValuationEngine

# Load with custom config file
engine = DigitalAssetValuationEngine(Path("my_config.yaml"))

# Get configuration summary
summary = engine.get_configuration_summary()
```

### Stress Testing

```python
# Run stress test
stress_result = engine.run_stress_test(positions, "market_crash")
print(f"Value impact: {stress_result['value_impact_percentage']:.1f}%")
```

## Testing

### Run Configuration Tests

```bash
python tests/test_config.py
```

### Run MCP Integration Tests

```bash
python tests/test_mcp_integration.py
```

### Run Full Integration Test

```bash
python test_digital_asset_valuation.py
```

### Interactive Demo

```bash
jupyter notebook notebooks/digital_asset_valuation_demo.ipynb
```

## MCP Service Integration

The engine integrates with MCP services running on:

- **Port 8002**: Algorand Reader Service - Account and transaction data
- **Port 8003**: Market Data Service - Real-time price feeds

### Price Fetching Strategy

1. **Primary**: Fetch from MCP market data service
2. **Fallback**: Use configured fallback prices
3. **Default**: Use reasonable defaults for known assets

### Service Health Monitoring

```python
# Check MCP service status
from core import DigitalAssetValuationEngine
engine = DigitalAssetValuationEngine()

# This will show service availability
summary = engine.get_configuration_summary()
```

## Supported Assets

Currently configured assets:

- **ALGO**: Native Algorand token (Asset ID: 0)
- **USDC**: USD Coin stablecoin (Asset ID: 31566704)
- **USDT**: Tether USD stablecoin (Asset ID: 312769)
- **GOBTC**: GoETH Bitcoin token (Asset ID: 386192725)

### Asset Classification

Assets are automatically classified into types:

- `algo_native`: ALGO tokens
- `stablecoin`: USDC, USDT, etc.
- `asa_token`: General Algorand Standard Assets
- `governance_token`: Protocol governance tokens
- `lp_token`: Liquidity pool tokens
- `liquid_staking`: Liquid staking derivatives

## Risk Parameters

### Collateral Ratios by Asset Type

- **ALGO Native**: 150% (conservative, highly liquid)
- **Stablecoins**: 110% (low volatility)
- **ASA Tokens**: 200% (variable liquidity)
- **Governance Tokens**: 250% (higher risk)
- **LP Tokens**: 300% (complex risk profile)
- **Liquid Staking**: 180% (moderate risk)

### Market Condition Adjustments

- **Bull Market**: -10% ratio reduction, 2% liquidation buffer
- **Bear Market**: +20% ratio increase, 5% liquidation buffer
- **High Volatility**: +15% ratio increase, 3% liquidation buffer
- **Low Volatility**: -5% ratio reduction, 1% liquidation buffer

### Stress Test Scenarios

1. **Market Crash**: 50% price drop, increased correlation
2. **Regulatory Shock**: 30% impact, reduced liquidity
3. **Technical Failure**: 40% impact, high correlation
4. **Liquidity Crisis**: 20% price impact, 90% liquidity reduction

## Production Deployment

### Requirements

- Python 3.8+
- MCP services running on ports 8002 and 8003
- YAML configuration file
- Access to Algorand network

### Configuration Checklist

1. ✅ Update MCP service URLs for production
2. ✅ Set appropriate collateral ratios for risk tolerance
3. ✅ Configure asset-specific parameters
4. ✅ Set safety buffers and cache settings
5. ✅ Define stress test scenarios
6. ✅ Configure environment variables

### Monitoring

Monitor these key metrics:

- MCP service availability
- Price feed staleness
- Portfolio concentration ratios
- Liquidation urgency levels
- Configuration parameter effectiveness

## Development

### Adding New Assets

1. Add asset to `algorand_assets` in config.yaml
2. Add volatility estimates
3. Add liquidity estimates
4. Set asset classification
5. Test with new asset

### Customizing Risk Parameters

1. Modify `risk_parameters` section in config
2. Adjust `market_condition_multipliers`
3. Update stress test scenarios
4. Validate with backtesting

### Integration Testing

The engine provides comprehensive test coverage:

- ✅ Configuration loading and merging
- ✅ MCP service integration
- ✅ Asset creation and classification
- ✅ Risk calculation accuracy
- ✅ Portfolio analysis workflows
- ✅ Stress testing functionality
- ✅ Market condition handling

## License

This digital asset valuation engine is part of the Algorand Lending Ecosystem and follows the same license terms.