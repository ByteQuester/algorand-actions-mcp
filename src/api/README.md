# Unified API Gateway for Algorand Lending Platform

A comprehensive API gateway that provides unified access to all lending engines with support for both vendor mode (direct imports) and hosted service mode (HTTP calls to deployed services).

## Features

### Core Functionality
- **Unified REST API** for all 4 lending engines (collateral analyzer, rate calculator, loan evaluator, risk assessor)
- **Service Discovery** with automatic vendor vs hosted mode detection
- **WebSocket Support** for real-time loan status updates and notifications
- **Health Monitoring** with comprehensive system and service health checks
- **Load Balancing** with multiple strategies (round-robin, least-connections, response-time)
- **Circuit Breaker** pattern for service resilience

### Monitoring & Observability
- **Prometheus Metrics** for monitoring and alerting
- **Request/Response Logging** with structured logging
- **Performance Tracking** with response time histograms
- **System Resource Monitoring** (CPU, memory, disk usage)
- **Service Availability Tracking** with uptime monitoring

### Security & Reliability
- **JWT Authentication** with configurable token validation
- **Rate Limiting** to prevent abuse and ensure fair usage
- **Request Timeout Management** with configurable timeouts
- **Automatic Retry Logic** with exponential backoff
- **CORS Support** for cross-origin requests

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Port 8000)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   REST API  │  │  WebSocket  │  │   Health Checks     │  │
│  │  Endpoints  │  │   Handler   │  │   & Monitoring      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Service   │  │    Load     │  │   Circuit Breaker   │  │
│  │  Discovery  │  │  Balancer   │  │    & Resilience     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────────┐  ┌──────▼──────┐
            │  Vendor Mode   │  │ Hosted Mode │
            │ (Direct Import)│  │(HTTP Services)│
            └────────────────┘  └─────────────┘
                    │                   │
         ┌──────────▼──────────┐       │
         │algorand_lending_bl  │       │
         │    - Collateral     │       │
         │    - Rates          │  ┌────▼─────┐
         │    - Evaluation     │  │Service A │
         │    - Risk           │  │Service B │
         └─────────────────────┘  │Service C │
                                  │Service D │
                                  └──────────┘
```

## API Endpoints

### Core Lending Services

#### Collateral Analysis
```http
POST /api/v1/collateral/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "collateral_type": "ASA",
  "collateral_amount": 1000000,
  "collateral_asset_id": 123456,
  "borrower_address": "ALGORAND_ADDRESS",
  "loan_amount": 500000000
}
```

#### Rate Calculation
```http
POST /api/v1/rates/calculate
Content-Type: application/json
Authorization: Bearer <token>

{
  "loan_amount": 500000000,
  "duration_days": 30,
  "collateral_type": "ASA",
  "risk_score": 0.15
}
```

#### Loan Evaluation
```http
POST /api/v1/loans/evaluate
Content-Type: application/json
Authorization: Bearer <token>

{
  "borrower_address": "ALGORAND_ADDRESS",
  "loan_amount": 500000000,
  "duration_days": 30,
  "collateral_analysis": { /* CollateralAnalysisResponse */ },
  "rate_calculation": { /* RateCalculationResponse */ }
}
```

#### Risk Assessment
```http
POST /api/v1/risk/assess
Content-Type: application/json
Authorization: Bearer <token>

{
  "borrower_address": "ALGORAND_ADDRESS",
  "loan_amount": 500000000,
  "collateral_value": 1000000,
  "duration_days": 30
}
```

### Health & Monitoring Endpoints

#### Overall Health
```http
GET /health
```

#### Quick Health Check
```http
GET /health/quick
```

#### Service Health Status
```http
GET /health/services
```

#### System Metrics
```http
GET /health/system
```

#### Prometheus Metrics
```http
GET /metrics
```

#### Service Status
```http
GET /api/v1/services/status
Authorization: Bearer <token>
```

### WebSocket Real-time Updates

#### Connect to Loan Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/loan-updates/connection-id?token=AUTH_TOKEN');

// Subscribe to specific loan updates
ws.send(JSON.stringify({
  type: 'subscribe',
  filters: {
    loan_ids: ['loan-123', 'loan-456'],
    message_types: ['loan_status_update', 'payment_reminder']
  }
}));

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

## Configuration

### Environment Variables

#### Deployment Mode
```bash
# Choose deployment mode
LENDING_MODE=vendor  # or "hosted"

# Gateway configuration
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000

# For hosted mode, configure service URLs
COLLATERAL_ANALYZER_URL=http://localhost:8001
RATE_CALCULATOR_URL=http://localhost:8002
LOAN_EVALUATOR_URL=http://localhost:8003
RISK_ASSESSOR_URL=http://localhost:8004
```

#### Database & Cache
```bash
# PostgreSQL database
DATABASE_URL=postgresql://user:password@localhost:5432/lending_platform

# Redis cache (optional)
REDIS_URL=redis://localhost:6379

# Algorand node
ALGORAND_NODE_URL=https://testnet-api.algonode.cloud
```

#### Security & Authentication
```bash
# JWT configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS configuration
CORS_ORIGINS=http://localhost:8000,http://localhost:8081
```

### Service Configuration Files

The gateway uses JSON configuration files to define service endpoints and behavior:

- **`config/services.json`** - Vendor mode configuration
- **`config/services-hosted.json`** - Hosted service mode configuration

Example service configuration:
```json
{
  "name": "collateral_analyzer",
  "mode": "vendor",
  "description": "Collateral analysis service",
  "import_path": "algorand_lending_bl.engines.collateral",
  "class_name": "CollateralAnalyzer",
  "load_balancing_strategy": "round_robin",
  "health_check_interval": 30,
  "timeout": 30,
  "retry_attempts": 3
}
```

## Deployment

### Vendor Mode (Direct Import)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
pip install algorand-lending-bl  # Your lending business logic package
```

2. **Set Environment Variables**
```bash
export LENDING_MODE=vendor
export DATABASE_URL=postgresql://user:password@localhost:5432/lending_platform
```

3. **Run the Gateway**
```bash
python -m src.api.gateway
```

### Hosted Service Mode

1. **Deploy Individual Services** (each listening on different ports)
```bash
# Deploy collateral analyzer service on port 8001
# Deploy rate calculator service on port 8002
# Deploy loan evaluator service on port 8003
# Deploy risk assessor service on port 8004
```

2. **Configure Service URLs**
```bash
export LENDING_MODE=hosted
export COLLATERAL_ANALYZER_URL=http://localhost:8001
export RATE_CALCULATOR_URL=http://localhost:8002
export LOAN_EVALUATOR_URL=http://localhost:8003
export RISK_ASSESSOR_URL=http://localhost:8004
```

3. **Run the Gateway**
```bash
python -m src.api.gateway
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 8000

CMD ["python", "-m", "src.api.gateway"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lending-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lending-gateway
  template:
    metadata:
      labels:
        app: lending-gateway
    spec:
      containers:
      - name: gateway
        image: algorand-lending/gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: LENDING_MODE
          value: "hosted"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: lending-secrets
              key: database-url
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Monitoring & Observability

### Prometheus Metrics

The gateway exposes various metrics for monitoring:

- **Request Metrics**
  - `gateway_requests_total` - Total number of requests
  - `gateway_request_duration_seconds` - Request duration histogram

- **Service Metrics**
  - `gateway_service_calls_total` - Service call counts
  - `gateway_circuit_breaker_open` - Circuit breaker status
  - `service_availability` - Service availability gauge

- **System Metrics**
  - `system_cpu_usage_percent` - CPU usage
  - `system_memory_usage_percent` - Memory usage
  - `system_disk_usage_percent` - Disk usage

### Health Checks

The gateway provides comprehensive health monitoring:

- **Service Health** - Monitors all registered lending services
- **Database Health** - Checks PostgreSQL connectivity
- **Cache Health** - Verifies Redis availability
- **Blockchain Health** - Tests Algorand node connectivity
- **System Health** - Monitors system resources

### Logging

Structured logging with configurable levels:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Development

### Running Locally

1. **Clone Repository**
```bash
git clone <repository-url>
cd algorand-showcase
```

2. **Install Dependencies**
```bash
pip install -r src/api/requirements.txt
```

3. **Set Environment Variables**
```bash
export LENDING_MODE=vendor
export DATABASE_URL=postgresql://localhost:5432/lending_test
```

4. **Run Gateway**
```bash
cd src/api
python gateway.py
```

### Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Test with coverage
pytest --cov=src/api tests/
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Performance Tuning

### Load Balancing Strategies

- **Round Robin** - Distributes requests evenly across endpoints
- **Least Connections** - Routes to endpoint with fewest active connections
- **Response Time** - Routes to endpoint with best response time
- **Random** - Randomly selects endpoint
- **Failover** - Uses primary endpoint, fails over to backup

### Circuit Breaker Configuration

```python
circuit_breaker = CircuitBreaker(
    failure_threshold=5,    # Open after 5 failures
    timeout=60             # Try again after 60 seconds
)
```

### Rate Limiting

```python
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def api_endpoint():
    pass
```

## Security Considerations

1. **Authentication** - Implement proper JWT validation
2. **Rate Limiting** - Prevent abuse with configurable limits
3. **Input Validation** - Validate all input parameters
4. **CORS Policy** - Configure appropriate CORS settings
5. **TLS/SSL** - Use HTTPS in production
6. **Secret Management** - Use environment variables for secrets

## Troubleshooting

### Common Issues

1. **Service Discovery Failures**
   - Check service configuration files
   - Verify import paths for vendor mode
   - Test service URLs for hosted mode

2. **Health Check Failures**
   - Verify database connectivity
   - Check service endpoint availability
   - Review circuit breaker status

3. **WebSocket Connection Issues**
   - Verify authentication token
   - Check CORS configuration
   - Monitor connection limits

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.api.gateway
```

## Contributing

1. Follow Python coding standards (PEP 8)
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use type hints throughout the codebase
5. Ensure all health checks pass before deployment

## License

This project is part of the Algorand Lending Platform and follows the same licensing terms.