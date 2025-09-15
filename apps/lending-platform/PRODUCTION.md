# Production Deployment Guide

## 🎯 Overview

The lending platform has been reorganized for production readiness while maintaining full development functionality. This guide covers the new structure, deployment process, and operational considerations.

## 📁 New Directory Structure

```
lending-platform/
├── src/                          # Production source code
│   ├── agents/                   # ADK agents and core logic
│   │   ├── coordination/         # Master coordination agent
│   │   ├── negotiation/          # Term negotiation agent
│   │   ├── liquidity/            # Liquidity discovery agent
│   │   ├── execution/            # Transaction execution agent
│   │   ├── schemas/              # JSON schemas and validation
│   │   ├── manifest.json         # Agent manifest
│   │   ├── requirements.txt      # Python dependencies
│   │   └── *.py                  # Core agent modules
│   ├── core/                     # Platform core modules
│   │   ├── lending_platform/     # Original platform code
│   │   ├── config.py             # Configuration management
│   │   └── logging_config.py     # Structured logging
│   └── ui/                       # UI components and overlays
│       └── ui-overlay/           # ADK web UI integration
├── scripts/                      # Organized development tools
│   ├── dev/                      # Development utilities
│   ├── test/                     # Testing and validation
│   ├── demo/                     # Demonstrations and examples
│   └── deployment/               # Production deployment
├── config/                       # Environment configurations
│   ├── default.json              # Base configuration
│   ├── development/              # Development settings
│   └── production/               # Production settings
├── tests/                        # Organized test suites
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── docs/                         # Documentation
├── .env.example                  # Environment template
└── README.md                     # Updated main documentation
```

## 🔧 Configuration Strategy

### Environment-Based Configuration

The platform now uses a three-tier configuration system:

1. **Base Configuration** (`config/default.json`)
   - Default values for all environments
   - Common settings and fallbacks

2. **Environment-Specific** (`config/{environment}/{environment}.json`)
   - Development: Debug settings, local endpoints
   - Production: Secure settings, production endpoints

3. **Environment Variables** (`.env` files)
   - Sensitive data (API keys, secrets)
   - Deployment-specific values

### Configuration Files

#### Development Configuration
```json
{
  "lending": {
    "max_loan_amount": 10000000000,
    "default_interest_rate": 5.0
  },
  "logging": {
    "level": "DEBUG",
    "console": true,
    "file": true
  },
  "monitoring": {
    "debug_mode": true
  }
}
```

#### Production Configuration
```json
{
  "lending": {
    "max_loan_amount": 100000000000,
    "strict_validation": true
  },
  "logging": {
    "level": "INFO",
    "console": false,
    "file": true,
    "structured": true
  },
  "security": {
    "jwt_secret": "${JWT_SECRET}",
    "rate_limiting": true
  }
}
```

## 📊 Structured Logging

### Logging System Features

- **Environment-aware**: Debug in development, structured in production
- **Performance tracking**: Agent and MCP call metrics
- **Business events**: Loan lifecycle tracking
- **Error handling**: Comprehensive error logging with context

### Usage Examples

```python
from src.core.logging_config import get_logger, BusinessLogger

# Standard logging
logger = get_logger(__name__)
logger.info("Agent operation completed")

# Business logging
business_logger = BusinessLogger()
business_logger.log_loan_request(
    borrower="ALGORAND_ADDRESS",
    amount=10000000,
    collateral_type="ALGO"
)
```

### Log Formats

**Development (Human-readable)**:
```
2025-01-15 10:30:00 - lending.coordination - INFO - Processing loan request
```

**Production (Structured JSON)**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "lending.coordination",
  "message": "Processing loan request",
  "event_type": "loan_request",
  "borrower": "ALGORAND_ADDRESS",
  "amount_micro_algos": 10000000
}
```

## 🚀 Production Deployment

### Quick Start

1. **Build Production Distribution**
   ```bash
   cd scripts/deployment
   python build.py
   ```

2. **Configure Environment**
   ```bash
   cp config/production/.env.production.template .env.production
   # Edit .env.production with your values
   ```

3. **Deploy with Docker**
   ```bash
   cd build/
   docker-compose -f docker-compose.production.yml up -d
   ```

### Build Process

The build script creates a production-ready distribution:

- **Source Code**: Only production-ready files
- **Dependencies**: Production requirements (excludes dev/test packages)
- **Docker**: Multi-stage build for smaller images
- **Configuration**: Environment-based configuration
- **Documentation**: Deployment guides and troubleshooting

### Production Features

#### Docker Configuration
- **Multi-stage builds** for smaller production images
- **Non-root user** for security
- **Health checks** for monitoring
- **Volume management** for data persistence

#### Security Considerations
- **JWT authentication** with configurable secrets
- **Rate limiting** for API protection
- **CORS configuration** for cross-origin requests
- **Input validation** with comprehensive sanitization

#### Monitoring & Observability
- **Health endpoints** for load balancer integration
- **Metrics collection** for Prometheus
- **Structured logging** for log aggregation
- **Performance tracking** for optimization

## 🛠️ Development Workflow

### Local Development

1. **Environment Setup**
   ```bash
   export NODE_ENV=development
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Install Dependencies**
   ```bash
   pip install -r src/agents/requirements.txt
   ```

3. **Configure Development Environment**
   ```bash
   cp config/development/.env.development.template .env.development
   # Edit with your development values
   ```

4. **Run Development Scripts**
   ```bash
   # Debug agents
   cd scripts/dev
   python debug_agent_errors.py

   # Run tests
   cd scripts/test
   python test_real_agent.py

   # Try demo
   cd scripts/demo
   python standalone_demo.py
   ```

### Testing Strategy

#### Unit Tests
- Individual agent testing
- Tool function validation
- Configuration testing

#### Integration Tests
- End-to-end workflow testing
- MCP service integration
- Database operations

#### Demo Scripts
- Standalone demonstrations
- ADK pattern examples
- Real blockchain integration

## 📁 Preserved Scripts and Tools

### Development Tools (`scripts/dev/`)
- **Debug scripts**: Agent error debugging and response validation
- **MCP toolbox**: Development MCP integration tools
- **Utilities**: Development helper scripts

### Testing Scripts (`scripts/test/`)
- **Integration tests**: Full workflow validation
- **Agent tests**: Individual agent testing
- **Validation scripts**: Comprehensive system validation
- **MCP tests**: Service connectivity testing

### Demo Scripts (`scripts/demo/`)
- **Simple demos**: Basic functionality demonstration
- **ADK examples**: ADK pattern implementation examples
- **Standalone demos**: Self-contained demonstrations
- **Example agents**: Reference implementations

## 🔄 Migration from Original Structure

### What Was Preserved
- **All functionality**: Every script and tool is preserved
- **Development workflow**: Original development process maintained
- **Test coverage**: All tests moved to organized structure
- **Documentation**: All guides moved to docs/ directory

### What Was Improved
- **Organization**: Clear separation of concerns
- **Configuration**: Environment-based configuration system
- **Logging**: Structured, production-ready logging
- **Build process**: Automated production builds
- **Documentation**: Comprehensive deployment guides

### File Mapping
```
Original Location                    → New Location
Original adk-framework/            → Removed (duplicated)
adk-framework/coordination/        → src/agents/coordination/
adk-framework/debug_*.py          → scripts/dev/
adk-framework/test_*.py           → scripts/test/
adk-framework/demo_*.py           → scripts/demo/
adk-framework/schemas/            → src/agents/schemas/
adk-framework/*.md                → docs/
```

## 🎯 Environment Variables

### Required for Production
```bash
# Google API
GOOGLE_API_KEY=your_production_key
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Security
JWT_SECRET=secure_64_char_secret_key

# MCP Services
ALGORAND_READER_ENDPOINT=https://reader.production.com
ALGORAND_WRITER_ENDPOINT=https://writer.production.com
LENDING_TOOLBOX_ENDPOINT=https://toolbox.production.com
```

### Optional Configuration
```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=structured

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=60

# Security
RATE_LIMIT_ENABLED=true
CORS_ENABLED=true
```

## 📈 Monitoring and Maintenance

### Health Checks
- `/health` - Basic application health
- `/health/detailed` - Comprehensive system status
- `/metrics` - Prometheus metrics

### Log Management
- **Structured logs**: JSON format for production
- **Log rotation**: Automatic file rotation
- **Debug mode**: Temporary debug logging

### Performance Monitoring
- **Agent performance**: Operation timing and success rates
- **MCP calls**: Service response times and error rates
- **Business metrics**: Loan processing statistics

## 🆘 Troubleshooting

### Common Issues

1. **Configuration Issues**
   ```bash
   # Validate configuration
   python -c "from src.core.config import get_config; config = get_config(); print(config.validate_configuration())"
   ```

2. **Import Errors**
   ```bash
   # Set Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

3. **MCP Connectivity**
   ```bash
   # Test MCP services
   cd scripts/test
   python test_toolbox_connection.py
   ```

4. **Agent Errors**
   ```bash
   # Debug agent initialization
   cd scripts/dev
   python debug_agent_errors.py
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug configuration
export NODE_ENV=development
python your_script.py
```

## 🎉 Summary

The lending platform reorganization provides:

✅ **Production-ready structure** with clear separation of concerns
✅ **Environment-based configuration** for development and production
✅ **Structured logging** for monitoring and debugging
✅ **Automated build process** with Docker support
✅ **Preserved functionality** - all original features maintained
✅ **Improved organization** - easier navigation and maintenance
✅ **Comprehensive documentation** - clear guides for all use cases

The platform remains fully functional in its current location while being ready for production deployment in hosting environments.