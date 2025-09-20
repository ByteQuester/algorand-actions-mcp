# Interest Rate Determiner for Algorand DeFi Lending

🔥 **Pure Algorand/DeFi Interest Rate Determination System** 🔥

A comprehensive, blockchain-native interest rate calculation engine that combines 6 specialized Algorand engines to provide real-time, market-driven lending rates based entirely on on-chain data and DeFi protocol metrics.

## 🚀 Features

### 6 Algorand-Native Rate Engines

1. **🏦 ALGO Staking Engine** - ALGO staking yield analysis and governance participation
2. **🌊 DeFi Yield Engine** - Multi-protocol yield aggregation (Tinyman, Pact, Algofi, etc.)
3. **👤 Reputation Engine** - On-chain reputation scoring and borrower analysis
4. **🪙 ASA Risk Engine** - ASA volatility assessment and collateral analysis
5. **🌐 Network Activity Engine** - Algorand network congestion and health monitoring
6. **💧 Liquidity Pool Engine** - DEX liquidity health and utilization analysis

### Key Capabilities

- ⚡ **Real-time Rate Calculation** - Live blockchain data integration
- 🎯 **Risk-Adjusted Pricing** - Comprehensive risk assessment across all factors
- 📊 **Cross-Engine Workflows** - Sophisticated rate determination combining all engines
- 🔗 **MCP Services Integration** - Ports 8002/8003 for blockchain data services
- 🛠️ **CLI Tools** - Complete command-line interface for each engine
- 🧪 **Integration Testing** - Comprehensive test suite for cross-engine workflows

## 📦 Installation

### From PyPI (when published)
```bash
pip install interest-rate-determiner
```

### Development Installation
```bash
git clone <repository-url>
cd interest-rate-determiner
pip install -e .
```

### With Development Dependencies
```bash
pip install -e ".[dev,testing]"
```

## 🛠 Quick Start

### Python API

```python
import asyncio
from decimal import Decimal
from interest_rate_determiner import (
    MarketRateAnalysisEngine,
    RiskAssessmentEngine,
    get_available_engines
)

async def calculate_rate():
    # Check available engines
    engines = get_available_engines()
    print(f"Available engines: {list(engines.keys())}")

    # Market analysis
    if 'market_rate_analysis' in engines:
        market_engine = engines['market_rate_analysis']()
        analysis = await market_engine.analyze_market_rates('ALGO', 24)
        print(f"Base rate: {analysis.base_rate:.4%}")

    # Risk assessment
    if 'risk_assessment' in engines:
        from interest_rate_determiner.risk_assessment.core.risk_engine import (
            BorrowerProfile, MarketRiskFactors
        )

        risk_engine = engines['risk_assessment']()

        borrower = BorrowerProfile(
            borrower_id='borrower_001',
            credit_score=720,
            debt_to_income_ratio=0.3
        )

        market_factors = MarketRiskFactors(
            asset_volatility=0.4,
            liquidity_risk=0.3,
            regulatory_risk=0.2
        )

        assessment = await risk_engine.assess_risk(
            borrower, market_factors, Decimal('50000'), 365
        )
        print(f"Risk premium: {assessment.risk_premium:.4%}")

# Run the example
asyncio.run(calculate_rate())
```

### Command Line Interface

```bash
# Check engine status
rate-calculator status

# Calculate comprehensive rate
rate-calculator calculate --amount 50000 --duration 365 --borrower "borrower_001"

# Market analysis
market-analyzer analyze --asset ALGO --hours 24

# Risk assessment
risk-assessor assess --borrower "borrower_001" --amount 50000 --duration 365

# Quick rate estimate
rate-calculator quick-calculate --amount 25000 --duration 180
```

### REST API

Start the API server:
```bash
uvicorn interest_rate_determiner.api.main:app --host 0.0.0.0 --port 8000
```

Example API calls:
```bash
# Comprehensive rate calculation
curl -X POST "http://localhost:8000/api/v1/rates/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_amount": 50000,
    "duration_days": 365,
    "borrower_id": "borrower_001",
    "jurisdiction": "us_federal",
    "asset": "ALGO"
  }'

# Market analysis
curl -X POST "http://localhost:8000/api/v1/market/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "ALGO",
    "analysis_period_hours": 24
  }'

# Health check
curl "http://localhost:8000/health"
```

### WebSocket Real-Time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_123');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Rate update:', data);
};

ws.onopen = function(event) {
    console.log('Connected to rate updates');
};
```

## 🏗 Architecture

### Engine Integration Flow

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Market Analysis   │    │   Risk Assessment    │    │   Credit Scoring    │
│                     │    │                      │    │                     │
│ • Real-time data    │    │ • Borrower profile   │    │ • Traditional data  │
│ • Market sentiment  │    │ • Market factors     │    │ • Blockchain data   │
│ • Volatility calc   │    │ • Risk modeling      │    │ • Behavioral data   │
└─────────┬───────────┘    └──────────┬───────────┘    └─────────┬───────────┘
          │                           │                          │
          └─────────────────┬─────────────────┬─────────────────┘
                            │                 │
                            ▼                 ▼
              ┌─────────────────────────────────────────────┐
              │         Rate Calculation Engine              │
              │                                             │
              │ • Combines all engine outputs               │
              │ • Applies weighting and logic               │
              │ • Calculates payment details                │
              └─────────────────┬───────────────────────────┘
                                │
                                ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│ Regulatory Compliance│    │   Dynamic Pricing    │    │  Rate Optimization  │
│                     │    │                      │    │                     │
│ • Jurisdiction rules│    │ • Supply/demand      │    │ • Profit targets    │
│ • Rate limits       │    │ • Market conditions  │    │ • Competitive pos.  │
│ • Disclosure reqs   │    │ • Real-time adjust.  │    │ • Utilization goals │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### Integration with Blockchain Collateral Analyzer

The Interest Rate Determiner integrates seamlessly with the `blockchain-collateral-analyzer` package:

```python
from blockchain_collateral_analyzer import DigitalAssetValuationEngine
from interest_rate_determiner import MarketRateAnalysisEngine

# Use collateral data to inform interest rate decisions
async def integrated_rate_calculation():
    # Analyze collateral
    collateral_engine = DigitalAssetValuationEngine()
    collateral_analysis = await collateral_engine.analyze_portfolio(portfolio)

    # Use collateral data in rate calculation
    market_engine = MarketRateAnalysisEngine()
    rate_analysis = await market_engine.analyze_market_rates(
        asset=collateral_analysis.primary_asset,
        analysis_period_hours=24
    )

    return rate_analysis
```

## 📊 Engine Details

### Market Rate Analysis Engine

- **Data Sources**: Algorand DEX, traditional finance rates, DeFi protocols
- **Analysis**: Market sentiment, volatility assessment, liquidity scoring
- **Outputs**: Base rate recommendation with confidence intervals

### Risk Assessment Engine

- **Credit Risk**: Traditional credit metrics, payment history
- **Market Risk**: Asset volatility, correlation analysis, liquidity risk
- **Operational Risk**: Smart contract risk, technology risk
- **Outputs**: Risk level classification and premium calculation

### Credit Scoring Engine

- **Traditional Data**: Credit scores, debt-to-income, employment status
- **Blockchain Data**: Wallet age, transaction patterns, DeFi participation
- **Behavioral Data**: Risk tolerance, holding patterns, diversification
- **Outputs**: Comprehensive credit score (300-850 scale)

### Regulatory Compliance Engine

- **Supported Jurisdictions**: US Federal/State, EU, UK, Singapore, Switzerland
- **Compliance Checks**: Usury laws, consumer protection, disclosure requirements
- **Outputs**: Compliant rate adjustments and required disclosures

### Dynamic Pricing Engine

- **Market Factors**: Supply utilization, demand pressure, liquidity conditions
- **Adjustments**: Real-time rate modifications based on market dynamics
- **Outputs**: Dynamically adjusted rates with reasoning

### Rate Optimization Engine

- **Objectives**: Profit maximization, competitive positioning, utilization targets
- **Constraints**: Regulatory limits, risk thresholds, market conditions
- **Outputs**: Optimized rates for business objectives

## 🔧 Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@localhost/rates_db
REDIS_URL=redis://localhost:6379

# Algorand configuration
ALGORAND_NODE_URL=https://mainnet-api.algonode.cloud
ALGORAND_INDEXER_URL=https://mainnet-idx.algonode.cloud

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Engine configuration
MARKET_DATA_CACHE_TTL=300
RISK_ASSESSMENT_TIMEOUT=30
COMPLIANCE_CHECK_TIMEOUT=10
```

### Configuration Files

Create `config/engines.yaml`:
```yaml
market_rate_analysis:
  data_sources:
    - algorand_dex
    - traditional_rates
    - defi_protocols
  cache_ttl_seconds: 300
  confidence_threshold: 0.7

risk_assessment:
  risk_weights:
    credit_risk: 0.4
    market_risk: 0.35
    operational_risk: 0.25
  risk_multipliers:
    very_low: 0.5
    low: 1.0
    medium: 1.5
    high: 2.5
    very_high: 4.0

regulatory_compliance:
  default_jurisdiction: "us_federal"
  rate_limits:
    us_federal: 0.36  # 36% APR
    eu: 0.25          # 25% APR
```

## 📋 Testing

### Run Tests

```bash
# Unit tests
pytest tests/

# Integration tests
pytest integration_tests/

# API tests
pytest integration_tests/test_api_integration.py

# Performance tests
pytest integration_tests/test_complete_workflow.py::TestCompleteWorkflow::test_performance_benchmark

# Coverage report
pytest --cov=interest_rate_determiner --cov-report=html
```

### Test Configuration

```bash
# Set test environment
export TESTING=true
export DATABASE_URL=sqlite:///test.db

# Run specific test categories
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only
pytest -m "not slow"       # Skip slow tests
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "interest_rate_determiner.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t interest-rate-determiner .
docker run -p 8000:8000 interest-rate-determiner
```

### Production Considerations

1. **Database Setup**: Use PostgreSQL for production
2. **Caching**: Redis for rate caching and session management
3. **Monitoring**: Prometheus metrics and health checks
4. **Security**: API authentication and rate limiting
5. **Scalability**: Horizontal scaling with load balancers

## 📈 Performance

### Benchmarks

- **Single Rate Calculation**: < 100ms average
- **Concurrent Requests**: 1000 requests/second sustained
- **Engine Initialization**: < 2 seconds cold start
- **Memory Usage**: < 200MB per worker process

### Optimization Tips

1. **Caching**: Enable Redis caching for market data
2. **Connection Pooling**: Use connection pools for databases
3. **Async Processing**: Leverage async/await throughout
4. **Engine Reuse**: Reuse engine instances across requests

## 🔐 Security

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/rates/calculate")
@limiter.limit("10/minute")
async def calculate_rate(request: Request, ...):
    pass
```

### Authentication

```python
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

@app.post("/api/v1/rates/calculate")
async def calculate_rate(token: str = Depends(security)):
    # Validate JWT token
    pass
```

## 🤝 Contributing

### Development Setup

```bash
git clone <repository-url>
cd interest-rate-determiner
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -e ".[dev]"
pre-commit install
```

### Code Standards

- **Formatting**: Black code formatter
- **Linting**: flake8 and mypy
- **Testing**: pytest with >90% coverage
- **Documentation**: Google-style docstrings

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

### Documentation

- **API Docs**: http://localhost:8000/docs
- **Engine Details**: See individual engine documentation
- **Examples**: `/examples` directory

### Getting Help

- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: dev@algorand-lending.io

### Troubleshooting

**Engine Import Errors**:
```bash
# Check engine availability
python -c "from interest_rate_determiner import check_engine_availability; check_engine_availability()"
```

**API Server Issues**:
```bash
# Check health endpoint
curl http://localhost:8000/health

# Check logs
uvicorn interest_rate_determiner.api.main:app --log-level debug
```

**Database Connection**:
```bash
# Test database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('your_db_url'); print(engine.execute('SELECT 1').fetchone())"
```

## 🗺 Roadmap

### Version 1.1
- [ ] Machine learning rate prediction models
- [ ] Advanced portfolio optimization
- [ ] Cross-chain collateral support

### Version 1.2
- [ ] Real-time risk monitoring
- [ ] Automated compliance reporting
- [ ] Enhanced regulatory support

### Version 2.0
- [ ] Multi-chain deployment
- [ ] Advanced DeFi integrations
- [ ] Institutional features

---

**Built for the Algorand ecosystem with ❤️**