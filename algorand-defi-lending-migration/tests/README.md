# Tests Directory 🧪

This directory contains all test files for the Algorand Lending Platform.

## Directory Structure

```
tests/
├── integration/          # Integration tests for full system workflows
├── unit/                # Unit tests for individual components
├── performance/         # Performance and load testing
└── archive/            # Archived legacy test files
```

## Test Categories

### Integration Tests (`integration/`)
- **test_complete_audit_system.py** - Comprehensive audit system testing
- **test_audit_api.py** - API endpoint testing
- **test_event_streaming_system.py** - Real-time event streaming tests
- **test_escrow_enforcement.py** - Escrow and enforcement system tests
- **test_final_comprehensive.py** - Complete system integration test
- **test_real_agent.py** - Real agent workflow testing
- **test_toolbox_connection.py** - Toolbox connectivity tests
- **test_negotiation_agent.py** - Negotiation agent testing

### Unit Tests (`unit/`)
- **test_event_streaming.py** - Event streaming unit tests
- **test_event_streaming_direct.py** - Direct event streaming tests
- **test_event_streaming_simple.py** - Simple event streaming tests

### Archive (`archive/`)
- Legacy test files preserved for reference
- Historical test implementations
- Deprecated testing approaches

## Running Tests

### All Integration Tests
```bash
cd apps/lending-platform
python -m pytest tests/integration/ -v
```

### Specific Test Suite
```bash
python tests/integration/test_complete_audit_system.py
```

### Unit Tests
```bash
python -m pytest tests/unit/ -v
```

## Test Requirements

Most tests require:
- PostgreSQL database for audit storage
- MCP services running (ports 3001, 8002)
- Environment variables configured
- Test authentication tokens

See individual test files for specific requirements.