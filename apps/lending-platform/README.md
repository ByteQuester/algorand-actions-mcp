# Lending Platform

A complete, production-ready lending platform for Algorand-based agent-to-agent lending operations.

## Overview

This lending platform provides clean, vendorable business logic and a production-ready API for facilitating automated lending between agents on the Algorand blockchain. The platform is designed for seamless integration with ADK-Web UI systems and supports real-world lending operations.

### Architecture Update

**🏗️ Consolidated Structure** - The lending-core and lending-api modules have been moved from `packages/` into this application directory (`src/core/lending/` and `src/api/`) to maintain proper architectural separation between shared packages and application-specific code.

## Architecture

**🚀 REORGANIZED FOR PRODUCTION** - The platform has been restructured for production readiness while maintaining full development functionality. See [PRODUCTION.md](PRODUCTION.md) for detailed deployment guide.

```
lending-platform/
├── src/                    # Production source code
│   ├── agents/            # ADK agents and core logic
│   │   ├── coordination/  # Master coordination agent
│   │   ├── negotiation/   # Term negotiation agent
│   │   ├── liquidity/     # Liquidity discovery agent
│   │   ├── execution/     # Transaction execution agent
│   │   ├── schemas/       # JSON schemas and validation
│   │   └── manifest.json  # Agent manifest
│   ├── core/              # Platform core modules
│   │   ├── lending/       # 🆕 Pure lending business logic (moved from packages)
│   │   ├── lending_platform/  # Original platform code
│   │   ├── config.py      # Configuration management
│   │   └── logging_config.py  # Structured logging
│   ├── api/               # 🆕 FastAPI wrapper (moved from packages)
│   │   ├── src/           # API implementation
│   │   ├── config/        # API configuration
│   │   └── scripts/       # API scripts
│   └── ui/                # UI components and overlays
├── scripts/               # Organized development tools
│   ├── dev/              # Development utilities
│   ├── test/             # Testing and validation
│   ├── demo/             # Demonstrations and examples
│   └── deployment/       # Production deployment
├── config/                # Environment configurations
│   ├── default.json      # Base configuration
│   ├── development/      # Development settings
│   └── production/       # Production settings
├── tests/                 # Organized test suites
├── docs/                  # Documentation
└── .env.example           # Environment template
```

### Core Components

#### 1. Production Source Code (`src/`)

**Agents** (`src/agents/`):
- **Coordination Agent** - Master workflow orchestration with Gemini 2.0
- **Negotiation Agent** - AI-powered term negotiation and risk assessment
- **Liquidity Agent** - Intelligent lender discovery and matching
- **Execution Agent** - Blockchain transaction coordination
- **Schemas** - Professional JSON schemas with validation

**Core Platform** (`src/core/`):
- **Configuration System** - Environment-based configuration management
- **Logging System** - Structured logging with business event tracking
- **Original Platform** - Preserved lending platform logic

**UI Integration** (`src/ui/`):
- **ADK Web UI** - Production-ready web interface components

#### 2. Development & Operations (`scripts/`)

**Development Tools** (`scripts/dev/`):
- Debug utilities for agent troubleshooting
- MCP toolbox integration for development

**Testing Suite** (`scripts/test/`):
- Comprehensive integration tests
- Agent validation scripts
- MCP connectivity testing

**Demonstrations** (`scripts/demo/`):
- Standalone demos for quick testing
- ADK pattern examples
- Reference implementations

**Production Deployment** (`scripts/deployment/`):
- Automated build system with Docker
- Production startup scripts
- Health check utilities

#### 3. Configuration Management (`config/`)

**Environment-Based Configuration**:
- **Base Settings** - Common defaults and fallbacks
- **Development** - Debug settings, local endpoints
- **Production** - Secure settings, production endpoints

**Features**:
- Environment variable overrides
- Validation and type checking
- Production security settings

## Features

### Core Features

✅ **Production-Ready Architecture** - Organized structure with clear separation of concerns
✅ **Environment-Based Configuration** - Development and production configurations
✅ **Structured Logging** - Business event tracking and performance monitoring
✅ **Automated Build System** - Docker-based production deployment
✅ **ADK Agent Integration** - Google ADK with Gemini 2.0 and specialized agents
✅ **MCP Services Integration** - Real blockchain data and transaction execution
✅ **Development Tools** - Comprehensive testing, debugging, and demo scripts

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

### 🚀 Production Deployment

For production deployment, see [PRODUCTION.md](PRODUCTION.md) for the complete guide.

```bash
# Build production distribution
cd scripts/deployment
python build.py

# Deploy with Docker
cd build/
docker-compose -f docker-compose.production.yml up -d
```

### 🛠️ Development Setup

#### 1. Environment Setup

```bash
# Set up Python environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pip install -r src/agents/requirements.txt
```

#### 2. Configuration

```bash
# Copy development environment template
cp config/development/.env.development.template .env.development

# Edit with your development values
export GOOGLE_API_KEY="your-google-api-key"
export NODE_ENV=development
```

#### 3. Run Development Scripts

```bash
# Try a simple demo
cd scripts/demo
python standalone_demo.py

# Run comprehensive tests
cd scripts/test
python final_comprehensive_test.py

# Debug agents
cd scripts/dev
python debug_agent_errors.py
```

### 🎯 ADK Web Integration

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