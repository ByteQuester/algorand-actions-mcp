# Algorand Lending API

Clean FastAPI wrapper for the `algorand-lending-core` package.

## 🎯 What This Package Does

**Provides a clean, configurable REST API** for the lending core business logic.

- ✅ **Factory Pattern** - Create API instances with injected configuration
- ✅ **Dependency Injection** - All external dependencies injected at runtime
- ✅ **Framework Integration** - Clean FastAPI wrapper with proper error handling
- ✅ **Configuration Driven** - No hardcoded values, everything configurable

## 🚀 Quick Start

### Installation

```bash
pip install algorand-lending-api algorand-lending-core
```

### Basic Usage

```python
from lending_api import LendingAPIFactory

# Create configuration (injected, not hardcoded)
config = {
    "api": {
        "title": "My Lending API",
        "version": "1.0.0",
        "cors_origins": ["http://localhost:3000"]
    },
    "blockchain": {
        "algod_url": "https://testnet-api.algonode.cloud",
        "indexer_url": "https://testnet-idx.algonode.cloud",
        "network": "testnet"
    },
    "lending": {
        "agents": {
            "negotiation": {"strategy": "conservative"},
            "liquidity": {"min_threshold": 1000000}
        }
    }
}

# Create app with factory pattern (clean!)
app = LendingAPIFactory.create_app(config)

# Run with any ASGI server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📁 Clean Architecture

This package demonstrates **proper separation of concerns**:

```
Your Environment Config  →  API Factory  →  Pure Business Logic
(injected at runtime)       (this package)   (lending-core)
```

### What's Clean About This:

- ✅ **No hardcoded URLs or configs** - Everything injected
- ✅ **No environment variables in source** - Config passed at runtime
- ✅ **No production code mixed with business logic**
- ✅ **Vendorable and reusable** - Can be deployed anywhere

## 🔧 Configuration Examples

### Development Environment

```python
config = {
    "api": {
        "title": "Development Lending API",
        "cors_origins": ["http://localhost:3000", "http://localhost:8081"]
    },
    "blockchain": {
        "algod_url": "https://testnet-api.algonode.cloud",
        "network": "testnet"
    },
    "lending": {
        "agents": {
            "negotiation": {"strategy": "permissive"},
            "liquidity": {"min_threshold": 100000}
        }
    }
}

app = LendingAPIFactory.create_app(config)
```

### Production Environment

```python
import os

config = {
    "api": {
        "title": "Production Lending API",
        "cors_origins": [os.getenv("FRONTEND_URL")]
    },
    "blockchain": {
        "algod_url": os.getenv("ALGOD_URL"),
        "indexer_url": os.getenv("INDEXER_URL"),
        "network": "mainnet"
    },
    "lending": {
        "agents": {
            "negotiation": {"strategy": "conservative"},
            "liquidity": {"min_threshold": 10_000_000}
        }
    }
}

app = LendingAPIFactory.create_app(config)
```

### Testing Environment

```python
config = {
    "api": {
        "title": "Test Lending API",
        "cors_origins": ["*"]  # Permissive for tests
    },
    "blockchain": {
        "algod_url": "http://localhost:4001",  # Local node
        "network": "private"
    },
    "lending": {
        "agents": {
            "negotiation": {"strategy": "test"},
            "liquidity": {"min_threshold": 1}
        }
    }
}

app = LendingAPIFactory.create_app(config)
```

## 🛠️ API Endpoints

Once configured, the API provides these endpoints:

- `GET /health` - Health check
- `POST /loans/request` - Submit loan request
- `GET /loans/{id}/status` - Check loan status
- `GET /account/{address}/balance` - Get account balance

### Example Request

```bash
curl -X POST "http://localhost:8000/loans/request" \
  -H "Content-Type: application/json" \
  -d '{
    "borrower_address": "BORROWER_ADDRESS",
    "amount_micro_algos": 5000000,
    "duration_days": 30,
    "max_interest_rate": 8.0,
    "collateral_type": "ALGO"
  }'
```

## 🧪 Testing

```python
import pytest
from httpx import AsyncClient
from lending_api import LendingAPIFactory

@pytest.mark.asyncio
async def test_loan_request():
    # Create test configuration
    test_config = {
        "api": {"title": "Test API"},
        "blockchain": {"network": "test"},
        "lending": {"agents": {}}
    }

    app = LendingAPIFactory.create_app(test_config)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/loans/request", json={
            "borrower_address": "TEST_BORROWER",
            "amount_micro_algos": 1000000,
            "duration_days": 30,
            "max_interest_rate": 5.0,
            "collateral_type": "ALGO"
        })

    assert response.status_code == 200
    assert "loan_id" in response.json()
```

## 🎯 Why This Architecture?

### Professional Software Design

1. **Separation of Concerns** - Business logic separate from API concerns
2. **Dependency Injection** - No hardcoded dependencies
3. **Configuration Driven** - Same code works in any environment
4. **Testable** - Easy to test with mock configurations
5. **Vendorable** - Can be sold/deployed anywhere

### Comparison with Bad Architecture

❌ **Bad** (mixed concerns):
```python
# Hardcoded production config in source code
ALGOD_URL = "https://mainnet-api.algonode.cloud"
DATABASE_URL = "postgresql://prod:pass@db:5432/lending"

app = FastAPI()  # Hardcoded configuration
```

✅ **Good** (clean separation):
```python
# Configuration injected at runtime
def create_app(config):
    return LendingAPIFactory.create_app(config)

# No hardcoded values in source
```

## 📦 Package Development

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Start development server
python -c "
from lending_api import LendingAPIFactory
import uvicorn

config = {...}  # Your dev config
app = LendingAPIFactory.create_app(config)
uvicorn.run(app, reload=True)
"
```

## 📄 License

MIT License

---

**This package uses the Factory Pattern with Dependency Injection for clean, vendorable architecture.**