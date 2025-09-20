# External Data MCP Service

A Model Context Protocol (MCP) service for accessing external data sources including price feeds, oracle data, and market information. This service is designed to work with the Algorand lending platform for real-time price data and oracle information needed for collateral valuation and risk assessment.

## Features

### Data Sources
- **Price Feeds**: Real-time cryptocurrency price data from multiple sources
  - CoinGecko API
  - Coinbase API
  - Mock providers for testing

- **Oracle Data**: Decentralized oracle feeds
  - Chainlink Data Feeds
  - Pyth Network
  - Band Protocol

- **Market Data**: Comprehensive market information
  - Volume, market cap, price changes
  - Historical price data
  - DeFi protocol metrics (TVL, APY)

### Tools Available

1. **get_price_feed** - Get real-time price data for cryptocurrency pairs
   - Supports pairs like ALGO/USDC, BTC/USD, ETH/USD
   - Multiple data source options
   - Configurable intervals

2. **get_oracle_data** - Access oracle data from various providers
   - Chainlink, Pyth, Band Protocol support
   - Network-specific queries (mainnet/testnet)
   - Confidence intervals and heartbeat data

3. **get_market_data** - Comprehensive market information
   - Price, volume, market cap data
   - Customizable metric selection
   - Real-time updates

4. **get_historical_prices** - Historical price analysis
   - Date range queries
   - Multiple interval options
   - OHLCV data format

5. **get_defi_data** - DeFi protocol information
   - Total Value Locked (TVL)
   - Annual Percentage Yield (APY)
   - Volume and user metrics

## Configuration

### Environment Variables

```bash
# Optional API keys for enhanced functionality
COINGECKO_API_KEY=your_coingecko_api_key
CHAINLINK_API_KEY=your_chainlink_api_key
PYTH_API_KEY=your_pyth_api_key
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

### Development

```bash
# Install dependencies
npm install

# Start development server on port 8789
npm run dev

# Build for production
npm run build

# Deploy to Cloudflare Workers
npm run deploy
```

### Usage Examples

#### Get ALGO/USDC Price
```bash
curl -X POST http://localhost:8789/api/price-feed \
  -H "Content-Type: application/json" \
  -d '{"pair": "ALGO/USDC", "source": "coingecko"}'
```

#### Get Chainlink Oracle Data
```bash
curl -X POST http://localhost:8789/api/oracle-data \
  -H "Content-Type: application/json" \
  -d '{"oracle": "chainlink", "feed_id": "ALGO/USD", "network": "mainnet"}'
```

#### Get Market Data
```bash
curl -X POST http://localhost:8789/api/market-data \
  -H "Content-Type: application/json" \
  -d '{"symbol": "ALGO", "metrics": ["price", "volume", "market_cap"]}'
```

## API Endpoints

- `GET /health` - Health check
- `GET /tools/list` - List available MCP tools
- `POST /api/price-feed` - Price feed data
- `POST /api/oracle-data` - Oracle data
- `POST /api/market-data` - Market information
- `POST /api/historical-prices` - Historical price data
- `POST /api/defi-data` - DeFi protocol data
- `GET /docs` - Swagger documentation
- `GET /openapi.json` - OpenAPI specification

## Production Deployment

The service is configured to run on Cloudflare Workers and listens on port 8789. It includes:

- Automatic failover to mock data when external APIs are unavailable
- Comprehensive error handling and validation
- CORS support for web applications
- Prometheus-style metrics endpoint
- OpenAPI documentation generation

## Integration with Lending Platform

This service provides critical external data for the Algorand lending platform:

- **Collateral Valuation**: Real-time price feeds for accurate asset pricing
- **Risk Assessment**: Oracle data for reliable price references
- **Market Analysis**: Historical and current market data for risk modeling
- **DeFi Integration**: Protocol data for yield farming and liquidity analysis

The service operates independently from Algorand blockchain data, focusing solely on external market and oracle information.