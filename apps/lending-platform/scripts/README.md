# Scripts Documentation

This directory contains various scripts organized by purpose to support development, testing, demonstration, and deployment of the lending platform.

## Directory Structure

```
scripts/
├── dev/                    # Development tools and utilities
├── test/                   # Testing scripts and validation
├── demo/                   # Demonstration and example scripts
├── deployment/             # Production deployment scripts
└── README.md              # This documentation
```

## Development Scripts (`dev/`)

### Debug Scripts
- **`debug_agent_errors.py`** - Debug agent initialization and error handling
- **`debug_agent_response.py`** - Debug agent response parsing and validation
- **`mcp-toolbox/`** - MCP toolbox integration for development

### Purpose
These scripts help developers troubleshoot issues, test individual components, and debug agent interactions during development.

### Usage
```bash
cd scripts/dev
python debug_agent_errors.py
```

## Testing Scripts (`test/`)

### Integration Tests
- **`test_real_agent.py`** - Test real agent interactions with MCP services
- **`test_negotiation_agent.py`** - Test negotiation agent specifically
- **`test_toolbox_connection.py`** - Test MCP toolbox connectivity
- **`final_comprehensive_test.py`** - Complete end-to-end testing
- **`validate_agents_comprehensive.py`** - Comprehensive agent validation

### Purpose
These scripts provide various levels of testing from unit tests to full integration tests with real blockchain services.

### Usage
```bash
# Run individual test
cd scripts/test
python test_real_agent.py

# Run comprehensive validation
python validate_agents_comprehensive.py

# Run full end-to-end test
python final_comprehensive_test.py
```

## Demo Scripts (`demo/`)

### Demonstration Scripts
- **`demo_adk_agents.py`** - Demonstrate ADK agent patterns
- **`simple_demo.py`** - Simple lending workflow demonstration
- **`simple_agent.py`** - Basic agent example
- **`standalone_demo.py`** - Standalone demonstration without dependencies
- **`example_lending_agent.py`** - Example lending agent implementation

### Purpose
These scripts show how to use the lending platform, provide examples for integration, and demonstrate key features.

### Usage
```bash
cd scripts/demo
python standalone_demo.py

# With ADK integration
python demo_adk_agents.py
```

## Deployment Scripts (`deployment/`)

### Production Deployment
- **`build.py`** - Production build script with Docker support
- **`start_production.py`** - Production server startup (created by build script)
- **`health_check.py`** - Health check for production deployment (created by build script)

### Purpose
These scripts handle production builds, deployments, and monitoring.

### Usage
```bash
# Build production distribution
cd scripts/deployment
python build.py

# Clean build directories
python build.py --clean-only

# After deployment - health check
python health_check.py
```

## Script Categories by Use Case

### 🔧 Development Workflow
1. **Setup**: Use config files in `config/development/`
2. **Debug**: Run `scripts/dev/debug_*.py` scripts
3. **Test**: Run `scripts/test/test_*.py` scripts
4. **Demo**: Run `scripts/demo/simple_demo.py`

### 🧪 Testing Workflow
1. **Unit Tests**: Individual agent tests in `scripts/test/`
2. **Integration**: `scripts/test/final_comprehensive_test.py`
3. **Validation**: `scripts/test/validate_agents_comprehensive.py`
4. **MCP Tests**: `scripts/test/test_toolbox_connection.py`

### 🎯 Demonstration Workflow
1. **Simple**: `scripts/demo/simple_demo.py`
2. **Standalone**: `scripts/demo/standalone_demo.py`
3. **ADK Pattern**: `scripts/demo/demo_adk_agents.py`
4. **Examples**: `scripts/demo/example_lending_agent.py`

### 🚀 Production Deployment
1. **Build**: `scripts/deployment/build.py`
2. **Deploy**: Use generated Docker configuration
3. **Monitor**: Health checks and logging
4. **Scale**: Docker Compose scaling

## Environment Setup

### Development
```bash
# Set environment
export NODE_ENV=development

# Use development config
export CONFIG_PATH=config/development/

# Run scripts
cd scripts/dev
python debug_agent_errors.py
```

### Production
```bash
# Production environment
export NODE_ENV=production

# Build for production
cd scripts/deployment
python build.py
```

## Common Patterns

### Configuration Loading
Most scripts use the configuration system:

```python
from src.core.config import get_config

config = get_config()
mcp_endpoint = config.get_mcp_service_config("algorand_reader").endpoint
```

### Logging
Scripts use the structured logging system:

```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Script started")
```

### Error Handling
Consistent error handling pattern:

```python
try:
    # Script logic
    pass
except Exception as e:
    logger.error(f"Script failed: {e}")
    sys.exit(1)
```

## Script Dependencies

### Required Packages
- All scripts require packages from `src/agents/requirements.txt`
- Development scripts may have additional debug dependencies
- Demo scripts work with minimal dependencies

### Environment Variables
- `GOOGLE_API_KEY` - Required for agent operations
- `MCP_*_ENDPOINT` - MCP service endpoints
- `LOG_LEVEL` - Logging configuration
- `NODE_ENV` - Environment selection

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Add src to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **MCP Connection Errors**
   ```bash
   # Test MCP connectivity
   cd scripts/test
   python test_toolbox_connection.py
   ```

3. **Agent Initialization Errors**
   ```bash
   # Debug agent setup
   cd scripts/dev
   python debug_agent_errors.py
   ```

### Debug Mode
Enable debug logging for any script:

```bash
export LOG_LEVEL=DEBUG
python script_name.py
```

## Contributing

When adding new scripts:

1. **Place in appropriate directory** (`dev/`, `test/`, `demo/`, `deployment/`)
2. **Use configuration system** for environment-specific settings
3. **Add structured logging** for debugging and monitoring
4. **Include error handling** with proper exit codes
5. **Document usage** in this README
6. **Follow naming conventions** (descriptive, lowercase with underscores)

## Migration from Original Structure

These scripts were reorganized from the original `adk-framework/` directory:

### Moved Scripts
- `adk-framework/debug_*.py` → `scripts/dev/`
- `adk-framework/test_*.py` → `scripts/test/`
- `adk-framework/demo_*.py` → `scripts/demo/`
- `adk-framework/simple_*.py` → `scripts/demo/`
- `adk-framework/example_*.py` → `scripts/demo/`
- `adk-framework/validate_*.py` → `scripts/test/`

### Preserved Functionality
All scripts maintain their original functionality while gaining:
- Better organization
- Consistent configuration management
- Structured logging
- Production-ready error handling
- Clear documentation