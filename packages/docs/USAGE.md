# Package Usage Guide

## Overview

This guide demonstrates how to use each package in the Algorand Showcase ecosystem, with practical examples and best practices.

## TypeScript Packages

### @algorand-showcase/types

**Purpose**: Shared TypeScript type definitions for all packages

```typescript
import type {
  AlgorandNetwork,
  NetworkConfig,
  MCPToolResult,
  MCPPaginatedResponse
} from '@algorand-showcase/types';

// Network configuration
const network: AlgorandNetwork = 'testnet';

// MCP response handling
function processResponse(result: MCPToolResult): void {
  result.content.forEach(content => {
    if (content.type === 'text') {
      console.log('Response:', content.text);
    }
  });
}
```

### @algorand-showcase/config

**Purpose**: Environment configuration and validation utilities

```typescript
import {
  loadNetworkConfig,
  validateNetworkConfig,
  getNetworkUrls,
  isMainnetAllowed
} from '@algorand-showcase/config';

// Load configuration from environment
const config = loadNetworkConfig();
console.log('Network:', config.network);
console.log('Allow mainnet:', config.allowMainnet);

// Get network-specific URLs
const urls = getNetworkUrls('testnet');
console.log('Algod URL:', urls.algod);
console.log('Indexer URL:', urls.indexer);

// Validate custom environment
const customEnv = {
  ALGORAND_NETWORK: 'mainnet',
  ALLOW_MAINNET: 'true'
};
const validatedConfig = validateNetworkConfig(customEnv);
```

**Development Usage**:
```bash
# Test network configurations
cd packages/config
npm run test

# Setup development environment
npm run setup-dev
```

### @algorand-showcase/algorand-clients

**Purpose**: Algorand SDK wrappers and client utilities

```typescript
import {
  AlgodClientWrapper,
  IndexerClientWrapper,
  createTransactionUrl,
  createAddressUrl
} from '@algorand-showcase/algorand-clients';

// Create wrapped clients
const algod = new AlgodClientWrapper({
  network: 'testnet',
  algodUrl: 'https://testnet-api.algonode.cloud',
  algodToken: ''
});

const indexer = new IndexerClientWrapper({
  network: 'testnet',
  indexerUrl: 'https://testnet-idx.algonode.cloud',
  indexerToken: ''
});

// Use clients
async function getAccountInfo(address: string) {
  const accountInfo = await algod.getAccountInfo(address);
  console.log('Balance:', accountInfo.amount);

  // Get transaction history
  const transactions = await indexer.getAccountTransactions(address);
  console.log('Transactions:', transactions.transactions.length);
}

// Generate explorer URLs
const txUrl = createTransactionUrl('testnet', 'ABC123...');
const addressUrl = createAddressUrl('testnet', 'ADDR123...');
```

### @algorand-showcase/mcp-core

**Purpose**: MCP protocol implementation patterns and utilities

```typescript
import { ResponseProcessor } from '@algorand-showcase/mcp-core';

// Configure pagination
ResponseProcessor.setItemsPerPage(20);

// Process array response with pagination
const largeDataset = Array.from({ length: 100 }, (_, i) => ({ id: i }));
const result = ResponseProcessor.processResponse(largeDataset);

// The result includes pagination metadata
console.log('Response:', JSON.parse(result.content[0].text));

// Process with page token
const nextPageResult = ResponseProcessor.processResponse(
  largeDataset,
  'some-page-token'
);

// Error handling
const errorResult = ResponseProcessor.createErrorResponse('Something went wrong');
console.log('Error:', errorResult.isError);
```

**Development Usage**:
```typescript
// Enable debug logging for development
import { responseProcessorLogger } from '@algorand-showcase/mcp-core/scripts/dev/debug-utils';

ResponseProcessor.setLogger(responseProcessorLogger);

// Test response processing
import { testResponseProcessor } from '@algorand-showcase/mcp-core/scripts/examples/test-response-processor';
testResponseProcessor();
```

## Python Packages

### @algorand-showcase/lending-core

**Purpose**: Pure business logic for Algorand lending operations

```python
from algorand_lending_core.models import (
    LoanRequest,
    LoanOffer,
    CollateralInfo,
    MCPServiceConfig
)
from algorand_lending_core.lending_engine import LendingEngine
from algorand_lending_core.workflow import LendingWorkflow

# Create configuration
config = MCPServiceConfig.from_environment()
# Or create manually:
# config = MCPServiceConfig(
#     reader_endpoint="https://reader.example.com",
#     writer_endpoint="https://writer.example.com"
# )

# Create lending engine
engine = LendingEngine(config)

# Create loan request
loan_request = LoanRequest(
    borrower_address="BORROWER123...",
    requested_amount=1000.0,  # ALGO
    duration_days=30,
    interest_rate=5.0,
    collateral=CollateralInfo(
        asset_id=31566704,  # USDC
        amount=1500.0  # 150% collateral ratio
    )
)

# Process loan request
try:
    result = await engine.process_loan_request(loan_request)
    print(f"Loan processed: {result.status}")
except Exception as e:
    print(f"Error: {e}")

# Use workflow for complex operations
workflow = LendingWorkflow(config)
await workflow.execute_full_lending_cycle(loan_request)
```

**Configuration Management**:
```python
# Development configuration helper
from scripts.dev.config_helper import ConfigPresets, display_config

# Use predefined configurations
dev_config = ConfigPresets.local_development()
prod_config = ConfigPresets.production()

display_config(dev_config, "Development")
display_config(prod_config, "Production")

# Generate environment files
from scripts.dev.config_helper import generate_env_file
generate_env_file("production", ".env.prod")
```

### @algorand-showcase/lending-api

**Purpose**: FastAPI wrapper providing REST API for lending operations

```python
# Basic usage
from algorand_lending_api.api_factory import LendingAPIFactory
from algorand_lending_api.server import app

# Create API with configuration
api_config = {
    "cors_origins": ["https://myapp.com"],
    "algorithm_config": {
        "algod_url": "https://testnet-api.algonode.cloud",
        "network": "testnet"
    }
}

factory = LendingAPIFactory(api_config)
app = factory.create_app()

# Start server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**API Usage**:
```bash
# Request a loan
curl -X POST "http://localhost:8000/loans/request" \
  -H "Content-Type: application/json" \
  -d '{
    "borrower_address": "BORROWER123...",
    "requested_amount": 1000.0,
    "duration_days": 30,
    "interest_rate": 5.0,
    "collateral": {
      "asset_id": 31566704,
      "amount": 1500.0
    }
  }'

# Get loan status
curl "http://localhost:8000/loans/LOAN_ID/status"

# Health check
curl "http://localhost:8000/health"
```

**Development Usage**:
```bash
# Start development server
cd packages/lending-api
npm run dev

# Setup development environment
npm run setup-dev

# Install in development mode
npm run install-dev
```

## Integration Examples

### Using Packages Together

```typescript
// TypeScript integration example
import { loadNetworkConfig } from '@algorand-showcase/config';
import { AlgodClientWrapper } from '@algorand-showcase/algorand-clients';
import { ResponseProcessor } from '@algorand-showcase/mcp-core';
import type { AlgorandNetwork } from '@algorand-showcase/types';

class AlgorandService {
  private algod: AlgodClientWrapper;
  private network: AlgorandNetwork;

  constructor() {
    // Load configuration
    const config = loadNetworkConfig();
    this.network = config.network;

    // Create client
    this.algod = new AlgodClientWrapper({
      network: this.network,
      algodUrl: process.env.ALGOD_URL || '',
      algodToken: process.env.ALGOD_TOKEN || ''
    });

    // Configure response processing
    ResponseProcessor.setItemsPerPage(10);
  }

  async getAccountTransactions(address: string, pageToken?: string) {
    try {
      const transactions = await this.algod.getAccountTransactions(address);
      return ResponseProcessor.processResponse(transactions, pageToken);
    } catch (error) {
      return ResponseProcessor.createErrorResponse(error.message);
    }
  }
}
```

### Python-TypeScript Bridge

```python
# Python service that communicates with TypeScript MCP services
import httpx
from algorand_lending_core.models import MCPServiceConfig

class MCPBridge:
    def __init__(self, config: MCPServiceConfig):
        self.config = config
        self.client = httpx.AsyncClient()

    async def call_reader_service(self, tool_name: str, params: dict):
        """Call TypeScript MCP reader service"""
        response = await self.client.post(
            f"{self.config.reader_endpoint}/call",
            json={"tool": tool_name, "params": params}
        )
        return response.json()

    async def call_writer_service(self, tool_name: str, params: dict):
        """Call TypeScript MCP writer service"""
        response = await self.client.post(
            f"{self.config.writer_endpoint}/call",
            json={"tool": tool_name, "params": params}
        )
        return response.json()
```

## Development Workflows

### Setting Up Development Environment

```bash
# 1. Install root dependencies
cd packages/
pnpm install

# 2. Setup development for all packages
pnpm run setup-dev

# 3. Build all packages
pnpm run build

# 4. Validate all packages
pnpm run validate
```

### Testing Package Changes

```bash
# 1. Make changes to a package
# 2. Build the package
cd packages/your-package
npm run build

# 3. Test in development mode
npm run dev

# 4. Run package-specific tests
npm run test

# 5. Validate integration
cd packages/
pnpm run validate
```

### Adding New Dependencies

```typescript
// 1. Add to package.json
{
  "dependencies": {
    "@algorand-showcase/types": "workspace:*",
    "new-library": "^1.0.0"
  }
}

// 2. Update imports
import { SomeType } from '@algorand-showcase/types';
import { newFunction } from 'new-library';

// 3. Rebuild and test
npm run build
npm run validate
```

## Best Practices

### 1. Type Safety
- Always use TypeScript types from @algorand-showcase/types
- Validate inputs using config package utilities
- Handle errors gracefully with proper typing

### 2. Configuration Management
- Use environment variables for all configuration
- Validate configuration at startup
- Provide sensible defaults for development

### 3. Error Handling
- Use ResponseProcessor for consistent error responses
- Log errors appropriately for debugging
- Provide meaningful error messages

### 4. Performance
- Use pagination for large datasets
- Cache frequently accessed data
- Monitor memory usage in long-running processes

### 5. Security
- Validate all inputs
- Use secure endpoints in production
- Avoid logging sensitive information

## Troubleshooting

### Common Issues

**TypeScript compilation errors:**
```bash
# Clear dist and rebuild
npm run clean
npm run build
```

**Import resolution issues:**
```bash
# Check workspace references
cat package.json | grep workspace
pnpm install
```

**Python import errors:**
```bash
# Install in development mode
pip install -e .
```

**Configuration errors:**
```bash
# Test configuration
npm run config-test  # For config package
python scripts/dev/config_helper.py test  # For Python packages
```