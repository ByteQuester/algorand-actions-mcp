# Algorand Showcase Data Pipeline

A comprehensive real-time data pipeline that connects all 3 MCP services and provides unified data access for the Algorand lending platform.

## Overview

The data pipeline provides:

- **MCP Service Connectivity**: Unified interface to Reader, Writer, and Market Data MCP services
- **Real-time Data Aggregation**: Combines data from multiple sources with intelligent caching
- **Performance Optimization**: Multi-layer caching with memory and file backends
- **Failure Resilience**: Circuit breakers, retries, and fallback mechanisms
- **Live Data Feeds**: WebSocket subscriptions for real-time price and market updates
- **Unified API**: Single interface for all lending engine data needs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Lending Engines                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Data Aggregator                              │
│  • Account data aggregation                                 │
│  • Market data consolidation                                │
│  • Collateral value calculation                             │
│  • Real-time subscriptions                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Cache Manager                                │
│  • Memory cache (LRU/LFU)                                   │
│  • File cache (persistent)                                  │
│  • Hybrid strategy                                          │
│  • Performance metrics                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                MCP Connector                                │
│  • Service health monitoring                                │
│  • Circuit breakers                                         │
│  • Retry mechanisms                                         │
│  • WebSocket subscriptions                                  │
└─────┬───────────────┬───────────────┬─────────────────────────┘
      │               │               │
┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
│  Reader   │   │  Writer   │   │  Market   │
│    MCP    │   │    MCP    │   │ Data MCP  │
│ :8002     │   │ :3001     │   │ :8789     │
└───────────┘   └───────────┘   └───────────┘
```

## Components

### 1. MCP Connector (`src/data_pipeline/mcp_connector.py`)

Unified interface to all MCP services with:

- **Service Management**: Health monitoring, circuit breakers, failover
- **Request Handling**: Automatic retries, timeout management, error handling
- **Real-time Feeds**: WebSocket subscriptions for live data
- **Service-Specific Methods**: Optimized calls for each MCP service type

```python
from src.data_pipeline import get_mcp_connector

connector = await get_mcp_connector()

# Reader MCP
account_info = await connector.get_account_info(address)
transactions = await connector.get_account_transactions(address)

# Writer MCP
simulation = await connector.simulate_transaction(txn_data)
fee_estimate = await connector.estimate_fee(txn_data)

# Market Data MCP
asset_price = await connector.get_asset_price(asset_id)
defi_yields = await connector.get_defi_yields()
```

### 2. Data Aggregator (`src/data_pipeline/data_aggregator.py`)

Intelligent data aggregation and real-time processing:

- **Account Data**: Comprehensive account information with asset valuations
- **Market Data**: Multi-asset price data with history and DeFi yields
- **Collateral Calculation**: Risk-adjusted collateral values
- **Real-time Subscriptions**: Live data feeds with callbacks
- **Performance Metrics**: Request tracking and optimization

```python
from src.data_pipeline import get_data_aggregator

aggregator = await get_data_aggregator()

# Get comprehensive account data
account_data = await aggregator.get_account_data(
    address, include_history=True
)

# Calculate collateral value
collateral = await aggregator.calculate_collateral_value(address)

# Subscribe to real-time updates
config = SubscriptionConfig(
    data_type=DataType.MARKET_DATA,
    parameters={"asset_ids": [0, 31566704]},
    update_interval=30.0,
    callback=my_callback
)
subscription_id = await aggregator.subscribe_to_real_time_data(config)
```

### 3. Cache Manager (`src/data_pipeline/cache_manager.py`)

Multi-layer caching with performance optimization:

- **Memory Cache**: Fast LRU/LFU cache for hot data
- **File Cache**: Persistent storage for larger datasets
- **Hybrid Strategy**: Automatic data placement based on access patterns
- **Performance Monitoring**: Hit rates, response times, optimization metrics

```python
from src.data_pipeline import get_cache_manager

cache = await get_cache_manager()

# Basic operations
await cache.set("key", data, ttl=300)
value = await cache.get("key")

# Batch operations
await cache.set_multiple(data_dict, ttl=60)
results = await cache.get_multiple(key_list)

# Performance monitoring
stats = cache.get_cache_stats()
performance = cache.get_performance_stats()
```

### 4. Blockchain Data Fixtures (`data/fixtures/blockchain_data.py`)

Real Algorand blockchain data for development and testing:

- **Real Assets**: ALGO, USDC, USDt, WBTC, WETH, DeFi tokens
- **Account Data**: Representative account structures with realistic balances
- **Transaction Patterns**: Real transaction types and amounts
- **DeFi Protocols**: Lending, DEX, yield farming applications
- **Market Data**: Current prices, yields, and protocol metrics

```python
from data.fixtures.blockchain_data import get_blockchain_fixtures

fixtures = get_blockchain_fixtures()

# Get real asset data
asset = fixtures.get_asset(31566704)  # USDC
price = fixtures.get_asset_price(0)   # ALGO price

# Get account data
account = fixtures.get_account(address)
high_value_accounts = fixtures.get_high_value_accounts(50000)

# Get DeFi data
protocols = fixtures.get_defi_protocols()
yields = fixtures.get_lending_yields()
```

## Configuration

### MCP Service URLs

The pipeline connects to these MCP services:

- **Reader MCP**: `http://localhost:8002` - Account and transaction data
- **Writer MCP**: `http://localhost:3001` - Transaction building and simulation
- **Market Data MCP**: `http://localhost:8789` - Prices and DeFi yields

### Cache Configuration

```python
# Memory cache settings
memory_cache_size = 1000      # Max entries
memory_cache_mb = 100         # Max memory usage

# File cache settings
file_cache_max_files = 10000  # Max files
cache_directory = "/tmp/algorand_cache"

# Cache strategy
backend = CacheBackend.HYBRID  # MEMORY, FILE, or HYBRID
```

### Performance Tuning

```python
# Request timeouts
timeout = 30                  # Default request timeout
retry_attempts = 3            # Max retry attempts
retry_delay = 1.0            # Base retry delay

# Circuit breaker
failure_threshold = 5         # Failures before opening circuit
circuit_timeout = 60          # Seconds before retry
```

## Usage Examples

### Basic Account Analysis

```python
async def analyze_account(address: str):
    aggregator = await get_data_aggregator()

    # Get comprehensive account data
    account_data = await aggregator.get_account_data(address)

    # Calculate collateral value
    collateral = await aggregator.calculate_collateral_value(address)

    print(f"Account: {address}")
    print(f"Total Value: ${account_data.get('total_value_usd', 0):,.2f}")
    print(f"Collateral: ${collateral['total_collateral_usd']:,.2f}")

    return {
        'total_value': account_data.get('total_value_usd', 0),
        'collateral_value': collateral['total_collateral_usd'],
        'loan_to_value': collateral['total_collateral_usd'] / account_data.get('total_value_usd', 1)
    }
```

### Real-time Price Monitoring

```python
async def monitor_prices(asset_ids: List[int]):
    aggregator = await get_data_aggregator()

    async def price_callback(data):
        print(f"Price update: {data}")
        # Process price update

    config = SubscriptionConfig(
        data_type=DataType.MARKET_DATA,
        parameters={"asset_ids": asset_ids},
        update_interval=10.0,
        callback=price_callback
    )

    subscription_id = await aggregator.subscribe_to_real_time_data(config)
    return subscription_id
```

### Lending Risk Analysis

```python
async def analyze_lending_risk():
    aggregator = await get_data_aggregator()

    # Get current lending metrics
    metrics = await aggregator.get_lending_metrics()

    # Get market data for major assets
    market_data = await aggregator.get_market_data([0, 31566704, 312769])

    # Calculate risk metrics
    utilization = metrics['metrics']['utilization_rates']
    avg_utilization = sum(utilization.values()) / len(utilization)

    return {
        'avg_lending_rate': metrics['metrics']['avg_lending_rate'],
        'avg_borrowing_rate': metrics['metrics']['avg_borrowing_rate'],
        'avg_utilization': avg_utilization,
        'total_tvl': metrics['metrics']['total_tvl'],
        'risk_level': 'high' if avg_utilization > 80 else 'medium' if avg_utilization > 60 else 'low'
    }
```

## Testing

### Run Integration Tests

```bash
python test_data_pipeline.py
```

Tests include:
- MCP service connectivity
- Data aggregation accuracy
- Cache performance
- Real-time subscriptions
- Error handling and resilience

### Run Demo

```bash
python demo_data_pipeline.py
```

Demonstrates:
- All pipeline capabilities
- Real-time data flows
- Performance monitoring
- Error handling

### Test Results

The test suite generates `test_results.json` with detailed metrics:

```json
{
  "summary": {
    "total_tests": 9,
    "passed": 9,
    "failed": 0,
    "success_rate": 1.0,
    "total_time": 45.67
  },
  "mcp_health": {
    "healthy_services": 3,
    "service_status": {...}
  },
  "performance_metrics": {
    "cache_hit_rate": 0.85,
    "avg_aggregation_time": 0.234
  }
}
```

## Performance Benchmarks

Typical performance metrics on localhost:

- **Account Data Aggregation**: 200-500ms
- **Market Data Retrieval**: 100-300ms
- **Cache Hit Response**: <10ms
- **Cache Miss Response**: 50-200ms
- **Real-time Update Latency**: <100ms
- **Memory Usage**: 50-200MB
- **Cache Hit Rate**: 80-95%

## Integration with Lending Platform

The data pipeline integrates with the lending platform through:

```python
# In lending engine
from src.data_pipeline import get_data_aggregator

class LendingEngine:
    async def __init__(self):
        self.data_aggregator = await get_data_aggregator()

    async def evaluate_loan_request(self, borrower_address: str, amount: int):
        # Get borrower's collateral
        collateral = await self.data_aggregator.calculate_collateral_value(borrower_address)

        # Get current market rates
        metrics = await self.data_aggregator.get_lending_metrics()

        # Calculate loan parameters
        max_loan = collateral['total_collateral_usd'] * 0.75  # 75% LTV
        interest_rate = metrics['metrics']['avg_borrowing_rate']

        return {
            'approved': amount <= max_loan,
            'max_amount': max_loan,
            'interest_rate': interest_rate,
            'collateral_required': amount / 0.75
        }
```

## Monitoring and Observability

### Health Checks

```python
# Check pipeline health
connector = await get_mcp_connector()
health_status = await connector.check_all_services_health()

# Check performance
aggregator = await get_data_aggregator()
metrics = aggregator.get_performance_metrics()
```

### Metrics Collection

The pipeline exposes metrics for monitoring:

- Request counts and success rates
- Response times and latencies
- Cache hit/miss rates
- Error rates by service
- Real-time subscription counts
- Memory and storage usage

### Alerting

Set up alerts for:
- MCP service downtime
- High error rates (>5%)
- Low cache hit rates (<70%)
- High response times (>1s)
- Memory usage (>500MB)

## Production Deployment

### Environment Variables

```bash
export ALGORAND_READER_MCP_URL="http://reader-mcp:8002"
export ALGORAND_WRITER_MCP_URL="http://writer-mcp:3001"
export ALGORAND_MARKET_DATA_MCP_URL="http://market-data-mcp:8789"
export CACHE_DIRECTORY="/var/cache/algorand"
export CACHE_MAX_MEMORY_MB="500"
export LOG_LEVEL="INFO"
```

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY data/ data/

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.data_pipeline"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-pipeline
  template:
    metadata:
      labels:
        app: data-pipeline
    spec:
      containers:
      - name: data-pipeline
        image: algorand-showcase/data-pipeline:latest
        env:
        - name: CACHE_DIRECTORY
          value: "/cache"
        volumeMounts:
        - name: cache-volume
          mountPath: /cache
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: cache-volume
        persistentVolumeClaim:
          claimName: data-pipeline-cache
```

## Contributing

1. **Code Style**: Follow PEP 8 and use type hints
2. **Testing**: Add tests for new features
3. **Documentation**: Update docstrings and README
4. **Performance**: Profile critical paths
5. **Security**: Validate inputs and handle errors gracefully

## License

This project is part of the Algorand Showcase and follows the same licensing terms.

## Support

For issues and questions:
- Check the test results and logs
- Review the demo output
- File issues with detailed error messages
- Include performance metrics when reporting problems