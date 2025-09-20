# 🔗 Blockchain Collateral Analyzer

**Configurable collateral requirements engine for Algorand-based DeFi lending with real-time data integration and risk assessment.**

## ✅ **What's Been Implemented**

This collateral analyzer now features a **production-ready, configuration-driven system** with:

### 🔧 **Configuration System**
- **YAML-based configuration** with sensible defaults (`collateral-requirements/config.yaml`)
- **Environment variable overrides** for production deployment
- **Comprehensive parameter management** for all risk factors
- **Asset-specific pricing and volatility data**

### 🚀 **Core Engine** (`collateral-requirements/`)
- **Real-time asset price fetching** with graceful fallbacks
- **Risk-adjusted collateral ratio calculations** based on volatility and liquidity
- **Portfolio diversification analysis** with correlation assessment
- **Liquidation scenario modeling** with market impact estimation
- **Multi-asset portfolio support** across all Algorand asset types

### 🔌 **MCP Service Integration**
- **Algorand Reader MCP** integration for blockchain data
- **Market Data MCP** integration for real-time prices
- **Configurable service endpoints** via configuration
- **Graceful fallback** to configured values when services unavailable

### 🗄️ **Data Management**
- **SQLite database** for analysis storage and audit trail
- **Market data caching** with configurable TTL
- **Historical analysis tracking** for trend analysis
- **Comprehensive audit trail** for compliance

## 🚀 Quick Start

### 1. Test the Configuration System

```bash
# Test the configuration and engine
python3 test_collateral_engine.py
```

### 2. Start MCP Services (Optional for Live Data)

```bash
# Start Algorand Reader and Market Data services
./start-mcp-services.sh

# Stop services when done
./stop-mcp-services.sh
```

### 3. CLI Usage

```bash
cd collateral-requirements

# Simple ALGO analysis
python3 analyze_collateral.py --loan-amount 25000 --collateral "0:ALGO:100000"

# Mixed portfolio analysis
python3 analyze_collateral.py --loan-amount 50000 \
  --collateral "0:ALGO:75000" "31566704:USDC:20000" \
  --market-conditions volatile

# Quick ALGO analysis
python3 analyze_collateral.py --quick-algo --amount 100000 --loan 25000

# View analysis history
python3 analyze_collateral.py --history --limit 10

# Database statistics
python3 analyze_collateral.py --stats
```

### 4. Interactive Testing (Step-by-Step Notebook)

```bash
# Small, focused testing steps in Jupyter
cd collateral-requirements
jupyter lab notebooks/collateral_analyzer_testing.ipynb
```

**Note**: The notebook is now broken into small, manageable steps - each cell focuses on one specific aspect of testing.

## 📁 Updated Module Structure

## 🎯 Key Features

### Digital Asset Support
- **ALGO Native** - Algorand cryptocurrency
- **ASA Tokens** - Algorand Standard Assets
- **Stablecoins** - USDC, USDT on Algorand
- **Governance Tokens** - Protocol voting tokens
- **LP Tokens** - Liquidity pool positions
- **Liquid Staking** - Staked ALGO derivatives

### Risk Analysis
- **Real-time Valuation** - Oracle-based asset pricing
- **Volatility Modeling** - Historical and predictive volatility
- **Liquidation Planning** - Optimal liquidation strategies
- **Portfolio Theory** - Diversification and correlation analysis
- **Stress Testing** - Scenario-based risk assessment

### Smart Contract Ready
- **Pure Functions** - No side effects for smart contract integration
- **Gas Optimized** - Efficient calculations for on-chain deployment
- **Fail-safe Design** - Robust error handling and fallbacks

## 🚀 Quick Start

```python
from blockchain_collateral_analyzer import (
    analyze_digital_collateral_requirement,
    DigitalAsset, DigitalCollateralType,
    VolatilityMetrics, LiquidityMetrics
)

# Create digital asset
algo_asset = DigitalAsset(
    asset_id="0",
    symbol="ALGO",
    name="Algorand",
    asset_type=DigitalCollateralType.ALGO_NATIVE,
    volatility_metrics=VolatilityMetrics(...),
    liquidity_metrics=LiquidityMetrics(...),
    base_collateral_ratio=1.5
)

# Analyze collateral requirement
result = analyze_digital_collateral_requirement(
    loan_amount_usd=50000,
    collateral_positions=[position],
    market_conditions="normal"
)

print(f"Required Collateral: ${result.required_collateral_ratio * 50000:,.0f}")
print(f"Risk Level: {result.risk_level}")
print(f"Confidence: {result.confidence_score:.0%}")
```

## 📊 Collateral Analysis Process

### 1. Asset Valuation
- Fetch real-time prices from multiple oracles
- Apply confidence-based haircuts
- Account for liquidity and market depth

### 2. Risk Assessment
- Calculate 30-day and 7-day volatility
- Compute Value at Risk (VaR) at 95% confidence
- Assess correlation with other portfolio assets

### 3. Liquidation Analysis
- Model liquidation scenarios (immediate, gradual, selective)
- Estimate slippage and market impact
- Calculate optimal liquidation timing

### 4. Portfolio Optimization
- Analyze asset diversification
- Compute portfolio-level risk metrics
- Recommend optimal collateral mix

### 5. Final Requirements
- Determine minimum collateral ratios
- Set maintenance thresholds
- Provide monitoring alerts

## 🔧 Configuration

### Default Collateral Ratios
- **ALGO Native**: 150% (highly liquid)
- **Stablecoins**: 110% (low volatility)
- **ASA Tokens**: 200% (variable liquidity)
- **Governance Tokens**: 250% (higher risk)
- **LP Tokens**: 300% (complex risk profile)

### Risk Parameters
- **Conservative**: 30% max volatility, high liquidity required
- **Moderate**: 50% max volatility, medium liquidity acceptable
- **Aggressive**: 80% max volatility, lower liquidity acceptable

## 📈 Supported Algorand Assets

### Native Assets
- **ALGO** - Primary collateral with highest confidence
- **Liquid Staking ALGO** - Staked ALGO with liquidity

### Algorand Standard Assets (ASAs)
- **USDC** (ASA 31566704) - USD Coin stablecoin
- **USDT** (ASA 312769) - Tether USD stablecoin
- **goBTC** (ASA 386192725) - Wrapped Bitcoin
- **goETH** (ASA 386195940) - Wrapped Ethereum

### DeFi Tokens
- DEX liquidity pool tokens
- Governance tokens from Algorand protocols
- Yield farming position tokens

## 🧪 Testing

Comprehensive test suite covering:
- Individual asset valuation
- Portfolio risk calculations
- Liquidation scenario modeling
- Oracle price aggregation
- Stress testing under market conditions

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific module
python -m pytest tests/test_digital_collateral.py -v
```

## 🔗 Integration

### With DeFi Protocols
```python
# Real-time collateral monitoring
def monitor_loan_health(loan_id):
    positions = get_collateral_positions(loan_id)
    analysis = analyze_digital_collateral_requirement(
        loan_amount_usd=get_loan_amount(loan_id),
        collateral_positions=positions
    )

    if analysis.risk_level in ["high", "critical"]:
        trigger_margin_call(loan_id)
```

### With Smart Contracts
The module provides pure functions suitable for smart contract integration:
- No external dependencies during calculation
- Deterministic results for same inputs
- Gas-efficient algorithms

## 📚 Learning Path

Start with the [Learning Path](learning-path/) for comprehensive tutorials:

1. **Digital Collateral Concepts** - Understanding crypto collateral
2. **Asset Valuation** - Real-time pricing and haircuts
3. **Volatility Assessment** - Risk measurement techniques
4. **Liquidation Scenarios** - Execution strategies
5. **Portfolio Diversification** - Risk reduction methods
6. **Oracle Integration** - Reliable price feeds
7. **Complete Workflow** - End-to-end analysis

## 🎓 Educational Value

Perfect for:
- **DeFi Development** - Building collateral management systems
- **Risk Management** - Understanding crypto asset risks
- **Academic Research** - Digital asset portfolio theory
- **Financial Engineering** - Quantitative risk modeling

## 🔄 Continuous Improvement

The module is designed to evolve with the DeFi ecosystem:
- Regular updates to asset parameters
- New risk models as markets mature
- Enhanced oracle integrations
- Expanded asset type support

---

**Ready to analyze digital collateral?** Start with the [Learning Path](learning-path/) or jump into the [examples](examples/) for hands-on experience! 🚀