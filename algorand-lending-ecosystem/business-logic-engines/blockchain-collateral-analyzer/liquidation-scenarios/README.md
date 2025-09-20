# Liquidation Scenarios Engine

A configuration-driven liquidation scenarios engine for digital asset collateral analysis, providing advanced liquidation scenario modeling and optimal liquidation strategies with integrated MCP services support.

## 🎯 Overview

This engine provides sophisticated liquidation scenario analysis with configurable parameters for:
- Slippage calculations with market conditions
- Liquidation time estimation
- Multiple liquidation strategies (immediate, gradual, selective, waterfall)
- Emergency scenario handling (oracle failure, volatility spikes, black swan events)
- Flash loan integration
- Dutch auction mechanisms
- Risk assessment and feasibility analysis

## 📁 Project Structure

```
liquidation-scenarios/
├── config/
│   └── config.yaml              # Configuration file with all parameters
├── core/
│   ├── __init__.py
│   ├── config.py                # Configuration loader and data classes
│   ├── liquidation_engine.py    # Core liquidation functions (updated)
│   └── liquidation_scenarios_engine.py  # Main engine class
├── notebooks/
│   └── liquidation_scenarios_demo.ipynb # Jupyter notebook demo
├── tests/
│   ├── __init__.py
│   ├── test_configuration.py    # Configuration tests
│   └── test_engine_functionality.py # Engine functionality tests
├── blockchain_collateral_models.py  # Data models
├── test_config_simple.py        # Simple configuration test
├── test_mcp_integration.py      # MCP integration tests
└── README.md                    # This file
```

## ⚙️ Configuration System

### Configuration Categories

1. **MCP Services Integration**
   - Algorand Reader URL (port 8002)
   - Market Data URL (port 8003)

2. **Slippage Calculation Parameters**
   - Maximum slippage cap (50%)
   - Volume ratio power factor (0.7)
   - Base slippage factor (0.1)
   - Depth penalty factors

3. **Liquidation Timing Parameters**
   - Volume thresholds for different time brackets
   - Base liquidation times by volume impact
   - Liquidity tier adjustments
   - Urgency level multipliers

4. **Liquidation Strategies**
   - **Immediate**: 15% max slippage, 1 hour completion
   - **Gradual**: 5% max slippage, 24 hour completion
   - **Selective**: 8% max slippage, 2 hour completion

5. **Emergency Scenarios**
   - Oracle failure handling
   - Volatility spike responses
   - Black swan event parameters

6. **Flash Loan Integration**
   - Maximum loan amount ($10M)
   - Fee rates (0.09%)
   - Gas cost multipliers
   - Supported protocols (Aave, dYdX, Balancer)

7. **Auction Mechanisms**
   - Dutch auction parameters
   - Sealed bid auction configuration

## 🚀 Key Features

### 1. Configuration-Driven Parameters
All hardcoded values have been moved to YAML configuration:
- Liquidation thresholds and triggers
- Slippage estimates for different market conditions
- Gas costs and transaction fees
- Time delays and auction parameters
- Market impact calculations
- Recovery rates and liquidation penalties
- Emergency liquidation scenarios
- Flash loan integration parameters

### 2. Advanced Liquidation Strategies

#### Waterfall Liquidation
Prioritizes assets by liquidity tier and market depth for optimal execution.

#### Emergency Scenarios
- **Oracle Failure**: Fallback pricing with confidence penalties
- **Volatility Spike**: Enhanced slippage multipliers and immediate execution
- **Black Swan**: Emergency protocols with high slippage tolerance

#### Risk Assessment
Feasibility analysis based on:
- Volume impact ratios
- Confidence scoring
- Time constraint validation

### 3. Flash Loan Integration
- Capital-efficient liquidations
- Protocol-agnostic implementation
- Cost optimization calculations
- Gas estimation with multipliers

### 4. Auction Mechanisms
- **Dutch Auctions**: Declining price discovery
- **Sealed Bid**: Competitive bidding
- Configurable timing and discount parameters

## 🛠️ Installation and Setup

### Prerequisites
- Python 3.8+
- MCP services running on ports 8002 and 8003
- Required Python packages: `pyyaml`, `requests`, `pandas`, `matplotlib`, `seaborn`

### Quick Start

1. **Load Configuration**:
```python
from core.config import load_config
config = load_config()
```

2. **Initialize Engine**:
```python
from core.liquidation_scenarios_engine import LiquidationScenariosEngine
engine = LiquidationScenariosEngine()
```

3. **Calculate Slippage**:
```python
slippage = engine.calculate_slippage(
    position_size_usd=100_000,
    daily_volume_usd=50_000_000,
    market_depth_1pct=1_000_000
)
```

4. **Create Liquidation Plan**:
```python
plan = engine.create_liquidation_plan(
    positions=collateral_positions,
    liquidation_target_usd=500_000,
    strategy="gradual"
)
```

## 🧪 Testing

### Configuration Tests
```bash
cd liquidation-scenarios
python test_config_simple.py
```

### MCP Integration Tests
```bash
python test_mcp_integration.py
```

### Expected Output
```
✓ Algorand Reader MCP is responding
✓ Market Data MCP is responding
✓ Flash loan integration is enabled
✓ Configuration loaded successfully
```

## 📊 Example Usage

### Basic Slippage Analysis
```python
# Test different liquidation sizes
sizes = [10_000, 100_000, 1_000_000]
for size in sizes:
    slippage = engine.calculate_slippage(
        position_size_usd=size,
        daily_volume_usd=50_000_000,
        market_depth_1pct=1_000_000
    )
    print(f"${size:,.0f} → {slippage:.2%} slippage")
```

### Emergency Scenario Handling
```python
# Get oracle failure parameters
oracle_params = engine.get_emergency_parameters('oracle_failure')
print(f"Fallback discount: {oracle_params['fallback_discount']:.1%}")
print(f"Confidence penalty: {oracle_params['confidence_penalty']:.1%}")
```

### Flash Loan Integration
```python
# Calculate flash loan costs
flash_params = engine.calculate_flash_loan_parameters(
    liquidation_amount=1_000_000,
    protocol="aave"
)
print(f"Total cost: ${flash_params['total_cost']:,.0f}")
```

## 🔧 Configuration

### Environment Variables
```bash
export LIQUIDATION_MCP_READER_URL="http://localhost:8002"
export LIQUIDATION_MCP_MARKET_URL="http://localhost:8003"
export LIQUIDATION_DB_PATH="/custom/path/liquidation.db"
export LIQUIDATION_FLASH_LOAN_ENABLED="true"
```

### Custom Configuration File
```python
from pathlib import Path
config = load_config(Path("/custom/config.yaml"))
engine = LiquidationScenariosEngine(config)
```

## 🔗 MCP Services Integration

The engine integrates with two MCP services:

1. **Algorand Reader MCP** (port 8002)
   - Blockchain data access
   - Asset information retrieval
   - Transaction monitoring

2. **Market Data MCP** (port 8003)
   - Real-time price feeds
   - Volume and liquidity metrics
   - Market condition analysis

### Service Connectivity
```python
# Test connectivity
response = requests.get("http://localhost:8002/health")
assert response.status_code == 200
```

## 📈 Performance Characteristics

### Slippage Scaling
- **Small liquidations (<1% volume)**: ~0.1-0.5% slippage
- **Medium liquidations (1-5% volume)**: ~0.5-2% slippage
- **Large liquidations (>5% volume)**: ~2-10% slippage

### Timing Estimates
- **High liquidity assets**: 0.5-24 hours
- **Medium liquidity assets**: 2-48 hours
- **Low liquidity assets**: 8-168 hours

### Emergency Response
- **Oracle failure**: 2-hour max delay, 20% fallback discount
- **Volatility spike**: Immediate execution, 1.5x slippage multiplier
- **Black swan**: 25% emergency slippage tolerance

## 🚨 Risk Considerations

1. **Market Impact**: Large liquidations may significantly impact asset prices
2. **Liquidity Risk**: Low-liquidity assets may not liquidate within expected timeframes
3. **Oracle Risk**: Price oracle failures require fallback mechanisms
4. **Gas Cost Risk**: Network congestion can significantly increase transaction costs
5. **Counterparty Risk**: Flash loan protocols may have their own risks

## 🔄 Configuration Updates

The system supports dynamic configuration updates:

```python
# Reload configuration
engine.reload_config()

# Update specific parameters
engine.config.liquidation_strategies.immediate.max_slippage_tolerance = 0.20
```

## 📝 Changelog

### v1.0.0 - Configuration-Driven Implementation
- ✅ Moved all hardcoded parameters to YAML configuration
- ✅ Created comprehensive configuration loader system
- ✅ Updated liquidation engine to use configuration
- ✅ Added MCP services integration (ports 8002/8003)
- ✅ Implemented flash loan integration
- ✅ Added emergency scenario handling
- ✅ Created Dutch auction mechanism
- ✅ Added comprehensive test suite
- ✅ Created interactive Jupyter notebook demo

## 🤝 Contributing

When modifying the engine:

1. Update configuration parameters in `config/config.yaml`
2. Add new configuration classes in `core/config.py`
3. Update the engine logic in `core/liquidation_engine.py`
4. Add tests in the `tests/` directory
5. Update documentation and examples

## 📄 License

This project is part of the Algorand Lending Ecosystem and follows the same licensing terms.