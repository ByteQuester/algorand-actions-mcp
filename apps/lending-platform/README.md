# Lending Platform

A complete, production-ready lending platform for Algorand-based agent-to-agent lending operations.

## Overview

This lending platform provides clean, vendorable business logic and a production-ready API for facilitating automated lending between agents on the Algorand blockchain. The platform is designed for seamless integration with ADK-Web UI systems and supports real-world lending operations.

## Architecture

```
apps/lending-platform/
├── lending-core/       # Pure business logic (vendorable)
├── lending-api/        # FastAPI server (production-ready)
└── lending-agents/     # Agent schema definitions
```

### Core Components

#### 1. Lending Core (`lending-core/`)

Pure business logic without external dependencies, suitable for vendoring:

- **`models.py`** - Core data models and enums
- **`workflow.py`** - Main lending workflow orchestration
- **`error_handling.py`** - Comprehensive error management
- **`api_models.py`** - API contract models with validation
- **`blockchain.py`** - Blockchain transaction logic
- **`__init__.py`** - Clean exports for library usage

#### 2. Lending API (`lending-api/`)

Production-ready FastAPI server:

- **`server.py`** - Main FastAPI application
- **`auth.py`** - Authentication and authorization
- **`storage.py`** - Data storage abstraction
- **`requirements.txt`** - Python dependencies

#### 3. Lending Agents (`lending-agents/`)

Agent schema definitions for MCP integration:

- **`liquidity-agent/`** - Liquidity discovery and management
- **`negotiation-agent/`** - Term negotiation logic
- **`execution-agent/`** - Transaction execution handling

## Features

### Core Features

✅ **Clean Architecture** - Separation of concerns between business logic and API layers
✅ **Production Ready** - Comprehensive error handling, logging, and monitoring
✅ **Vendorable Core** - Business logic can be used as a standalone library
✅ **API-First Design** - RESTful API with OpenAPI/Swagger documentation
✅ **Authentication** - JWT-based auth with ADK-Web integration
✅ **Blockchain Integration** - Native Algorand transaction handling
✅ **Agent Integration** - MCP-compatible agent schemas

### Lending Operations

- **Loan Origination** - Submit and validate loan requests
- **Liquidity Discovery** - Find available lenders and capital
- **Term Negotiation** - Automated term negotiation between agents
- **Risk Assessment** - Collateral validation and risk evaluation
- **Transaction Execution** - Blockchain transaction orchestration
- **Loan Monitoring** - Track loan lifecycle and status

### Integration Capabilities

- **ADK-Web UI** - Seamless integration with web interfaces
- **MCP Services** - Compatible with Model Context Protocol
- **Coordination Hub** - Uses shared configuration and status reporting
- **OAuth/JWT** - Modern authentication standards
- **RESTful API** - Standard HTTP API for external integrations

## Quick Start

### 1. Environment Setup

```bash
cd apps/lending-platform/lending-api
pip install -r requirements.txt
```

### 2. Configuration

Set environment variables:

```bash
export JWT_SECRET_KEY="your-secret-key"
export ADK_WEB_BASE_URL="http://localhost:8000"
export LOAN_DATA_DIR="./data"
export PORT=8003
```

### 3. Start the API Server

```bash
cd apps/lending-platform/lending-api
python server.py
```

The API will be available at:
- **API**: http://localhost:8003
- **Documentation**: http://localhost:8003/api/v1/docs
- **Health Check**: http://localhost:8003/api/v1/health

### 4. Using the Core Library

```python
from apps.lending_platform.lending_core import LendingWorkflow, LoanRequestAPI

# Initialize workflow
workflow = LendingWorkflow()

# Process a lending request
request_data = {
    "borrower": "ALGORAND_ADDRESS_HERE",
    "amount": 10000000,  # 10 ALGO in microAlgos
    "duration": 30,      # 30 days
    "max_interest_rate": 8.5,
    "collateral_type": "ALGO",
    "collateral_amount": 13000000  # 13 ALGO collateral
}

result = await workflow.process_lending_request(request_data)
print(f"Loan status: {result['status']}")
```

## API Documentation

### Authentication

All endpoints require a Bearer token in the Authorization header:

```bash
curl -H "Authorization: Bearer <your-jwt-token>" \
     http://localhost:8003/api/v1/loans
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/loans/request` | Submit new loan application |
| GET | `/api/v1/loans/{loan_id}` | Get loan status |
| POST | `/api/v1/loans/{loan_id}/accept` | Accept/reject loan terms |
| GET | `/api/v1/loans` | List user's loans |
| GET | `/api/v1/health` | Service health check |

### Example Request

```json
POST /api/v1/loans/request
{
  "amount_micro_algos": 10000000,
  "duration_days": 30,
  "max_interest_rate": 8.5,
  "collateral_type": "ALGO",
  "collateral_amount": 13000000,
  "borrower_address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
}
```

### Example Response

```json
{
  "loan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "requested",
  "created_at": "2025-01-15T10:30:00Z",
  "amount_micro_algos": 10000000,
  "duration_days": 30,
  "collateral_type": "ALGO",
  "next_actions": ["Processing loan request", "Analyzing liquidity"]
}
```

## Integration with ADK-Web

The lending platform integrates seamlessly with ADK-Web UI systems:

### 1. Authentication Flow

```javascript
// Frontend authentication
const token = await adkWeb.auth.getToken();
const response = await fetch('/api/v1/loans/request', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(loanRequest)
});
```

### 2. Wallet Integration

The platform automatically uses the user's linked Algorand wallet:

- Borrower address from user profile
- Transaction signing via wallet integration
- Balance checks and validation

### 3. UI Components

Recommended UI components for integration:

- **Loan Request Form** - Input validation with real-time feedback
- **Loan Status Dashboard** - Track multiple loans and their progress
- **Terms Review Interface** - Accept/reject negotiated terms
- **Transaction Monitor** - View blockchain transaction status

## MCP Integration

### Service Configuration

The platform works with MCP services defined in `apps/mcp-services/`:

- **algorand-reader-mcp** - Read blockchain data (port 8002)
- **algorand-writer-mcp** - Execute transactions (port 8001)

### Agent Schemas

Agent schemas in `lending-agents/` define:

```yaml
# Example: liquidity-agent schema
agent_type: "liquidity_provider"
capabilities:
  - discover_available_funds
  - assess_lending_capacity
  - provide_market_rates
mcp_endpoints:
  - "http://localhost:8002"  # reader service
  - "http://localhost:8001"  # writer service
```

## Coordination Hub Integration

The lending platform integrates with the coordination hub for:

### Shared Configuration

Uses `coordination-hub/shared-config.yaml` for:

```yaml
# Lending platform configuration
lending:
  default_interest_rate: 7.5
  max_loan_amount: 100000000000  # 100k ALGO
  min_collateral_ratio: 1.3
  supported_collateral: ["ALGO", "USDC"]

# MCP service endpoints
mcp_services:
  algorand_reader: "http://localhost:8002"
  algorand_writer: "http://localhost:8001"
```

### Status Reporting

Updates `coordination-hub/status-board.md` with:

- Service health status
- Active loan counts
- Error rates and performance metrics
- Integration test results

## Error Handling

The platform provides comprehensive error handling:

### Error Categories

- **ValidationError** - Input validation failures
- **LiquidityError** - Insufficient funds or liquidity
- **NegotiationError** - Term negotiation failures
- **ExecutionError** - Blockchain execution issues
- **SystemError** - Infrastructure or service errors

### Error Recovery

Each error provides:

- Detailed error messages
- Recovery suggestions
- Retry recommendations
- Support contact information

### Example Error Response

```json
{
  "error": "LiquidityError",
  "message": "Insufficient liquidity for requested loan amount",
  "category": "liquidity_shortage",
  "severity": "high",
  "recovery_suggestions": [
    "Try requesting a smaller loan amount",
    "Offer higher interest rate",
    "Use different collateral type"
  ]
}
```

## Testing

### Unit Tests

```bash
cd apps/lending-platform/lending-core
python -m pytest tests/
```

### Integration Tests

```bash
# Test with coordination hub
cd coordination-hub/test-results
python test_lending_integration.py
```

### API Testing

```bash
# Test API endpoints
curl -X GET http://localhost:8003/api/v1/health
curl -X POST http://localhost:8003/api/v1/loans/request \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @test_loan_request.json
```

## Monitoring and Observability

### Health Checks

The platform provides comprehensive health monitoring:

```bash
GET /api/v1/health
```

Returns service status including:
- API server health
- Database connectivity
- MCP service availability
- Active loan counts
- Error rates

### Logging

Structured logging with:

- Request/response logging
- Error tracking with stack traces
- Performance metrics
- Business event logging

### Metrics

Key metrics tracked:

- **Request Volume** - API requests per second
- **Response Times** - Average response latency
- **Error Rates** - Error percentage by category
- **Loan Metrics** - Success rates, amounts, durations
- **User Activity** - Active users, loan completion rates

## Production Deployment

### Requirements

- **Python 3.9+** with asyncio support
- **FastAPI/Uvicorn** for API server
- **JWT libraries** for authentication
- **File system access** for data storage (or database)
- **Network access** to Algorand nodes and MCP services

### Security Considerations

- **JWT Secret Key** - Use secure, randomly generated keys
- **HTTPS** - Always use HTTPS in production
- **Rate Limiting** - Implement API rate limiting
- **Input Validation** - Comprehensive input sanitization
- **Audit Logging** - Log all financial transactions
- **Access Control** - Proper user authorization

### Scaling

- **Horizontal Scaling** - Stateless API design supports load balancing
- **Database Migration** - Replace file storage with database for production
- **Caching** - Add Redis for session and data caching
- **Message Queues** - Use queues for async workflow processing

## Contributing

### Code Structure

Follow the established patterns:

1. **Core Logic** - Pure functions in `lending-core/`
2. **API Layer** - HTTP handling in `lending-api/`
3. **Error Handling** - Use the error handling framework
4. **Testing** - Add tests for new functionality
5. **Documentation** - Update README and API docs

### Development Workflow

1. Check coordination hub for current status
2. Update your progress in status board
3. Follow the clean architecture patterns
4. Add comprehensive error handling
5. Test integration with MCP services
6. Update documentation

## Support

For issues, questions, or contributions:

1. **Check Status Board** - `coordination-hub/status-board.md`
2. **Review Blockers** - `coordination-hub/blockers/`
3. **Integration Tests** - Run full test suite
4. **Documentation** - API docs at `/api/v1/docs`

## License

This lending platform is part of the Algorand Showcase project and follows the project's licensing terms.

---

**Ready for production use with Algorand-based agent-to-agent lending operations.**