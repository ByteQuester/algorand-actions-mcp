# Service Dependencies Mapping

## Shared Package Integration

This document provides detailed mapping of how the MCP services integrate with shared packages in the monorepo structure.

## Package Dependency Tree

```
apps/mcp-services/
├── algorand-reader-mcp/
│   └── Dependencies:
│       ├── @algorand-showcase/algorand-clients
│       ├── @algorand-showcase/config
│       ├── @algorand-showcase/mcp-core
│       └── @algorand-showcase/types
└── algorand-writer-mcp/
    └── Dependencies:
        ├── @algorand-showcase/algorand-clients
        ├── @algorand-showcase/config
        ├── @algorand-showcase/mcp-core
        └── @algorand-showcase/types
```

## Package Descriptions and Usage

### @algorand-showcase/algorand-clients

**Location**: `packages/algorand-clients/`
**Purpose**: Centralized Algorand blockchain client management

#### Key Exports
```typescript
// Client factory and management
export class AlgorandClientFactory {
  createAlgodClient(config: AlgodConfig): algosdk.Algodv2;
  createIndexerClient(config: IndexerConfig): algosdk.Indexer;
  createClientPool(config: PoolConfig): ClientPool;
}

// Connection management
export class ConnectionManager {
  validateConnection(client: algosdk.Algodv2): Promise<boolean>;
  getNetworkInfo(client: algosdk.Algodv2): Promise<NetworkInfo>;
  healthCheck(): Promise<HealthStatus>;
}

// Client configuration types
export interface AlgodConfig {
  server: string;
  port: string;
  token: string;
  headers?: Record<string, string>;
}
```

#### Usage in Services
- **Reader Service**: Creates read-only clients for account queries
- **Writer Service**: Creates clients for transaction simulation and submission
- **Connection Pooling**: Manages client lifecycle and connection reuse
- **Health Monitoring**: Validates Algorand node connectivity

### @algorand-showcase/config

**Location**: `packages/config/`
**Purpose**: Configuration management and validation utilities

#### Key Exports
```typescript
// Environment configuration
export class ConfigManager {
  loadEnvironment(env: string): EnvironmentConfig;
  validateConfig(config: object): ValidationResult;
  getNetworkConfig(network: string): NetworkConfig;
}

// Configuration schemas
export const ConfigSchemas = {
  algodConfig: ZodSchema,
  indexerConfig: ZodSchema,
  mcpConfig: ZodSchema,
  oauthConfig: ZodSchema
};

// Network presets
export const NetworkPresets = {
  mainnet: NetworkConfig,
  testnet: NetworkConfig,
  betanet: NetworkConfig,
  localnet: NetworkConfig
};
```

#### Usage in Services
- **Environment Loading**: Loads and validates environment variables
- **Network Configuration**: Provides network-specific settings
- **Schema Validation**: Validates configuration objects
- **Default Values**: Provides sensible defaults for missing configuration

### @algorand-showcase/mcp-core

**Location**: `packages/mcp-core/`
**Purpose**: Core MCP protocol implementation and utilities

#### Key Exports
```typescript
// MCP Server framework
export class MCPServer {
  constructor(config: MCPServerConfig);
  registerTool(tool: ToolDefinition): void;
  registerResource(resource: ResourceDefinition): void;
  start(): Promise<void>;
  stop(): Promise<void>;
}

// Protocol handling
export class ProtocolHandler {
  handleRequest(request: MCPRequest): Promise<MCPResponse>;
  validateRequest(request: object): ValidationResult;
  formatResponse(data: any): MCPResponse;
}

// Tool utilities
export abstract class BaseTool {
  abstract name: string;
  abstract description: string;
  abstract inputSchema: JSONSchema;
  abstract execute(params: any): Promise<any>;
}
```

#### Usage in Services
- **Server Initialization**: Bootstraps MCP server with service-specific configuration
- **Tool Registration**: Registers Algorand-specific tools with the MCP framework
- **Request Handling**: Processes incoming MCP requests and routes to appropriate handlers
- **Response Formatting**: Ensures responses conform to MCP protocol standards

### @algorand-showcase/types

**Location**: `packages/types/`
**Purpose**: Shared TypeScript type definitions

#### Key Exports
```typescript
// Algorand types
export interface AlgorandAccount {
  address: string;
  amount: number;
  assets?: AssetHolding[];
  apps?: ApplicationLocalState[];
}

export interface AlgorandTransaction {
  id: string;
  type: TransactionType;
  sender: string;
  receiver?: string;
  amount?: number;
  fee: number;
  round: number;
}

// MCP types
export interface MCPToolCall {
  tool: string;
  arguments: Record<string, any>;
}

export interface MCPResponse {
  content: Content[];
  isError?: boolean;
}

// Service configuration types
export interface ServiceConfig {
  port: number;
  network: AlgorandNetwork;
  algod: AlgodConfig;
  indexer: IndexerConfig;
  mcp: MCPConfig;
}
```

#### Usage in Services
- **Type Safety**: Ensures type consistency across service boundaries
- **Interface Definitions**: Defines contracts between services and shared packages
- **Validation Schemas**: Used with runtime validation libraries
- **Documentation**: Serves as API documentation through TypeScript definitions

## Build Dependencies

### Build Order Requirements

The monorepo build system requires packages to be built before services:

```bash
# Required build order
1. packages/types          # Base types needed by all
2. packages/config         # Configuration utilities
3. packages/algorand-clients  # Client libraries
4. packages/mcp-core       # MCP framework
5. apps/mcp-services/*     # Finally, the services
```

### Package.json Scripts

Each service references shared packages using workspace protocol:

```json
{
  "dependencies": {
    "@algorand-showcase/algorand-clients": "workspace:*",
    "@algorand-showcase/config": "workspace:*",
    "@algorand-showcase/mcp-core": "workspace:*",
    "@algorand-showcase/types": "workspace:*"
  }
}
```

### Build Configuration

Services inherit build configuration from workspace root:

```json
// Root package.json
{
  "scripts": {
    "build": "pnpm --filter '@algorand-showcase/*' run build",
    "build:services": "pnpm --filter 'apps/*' run build"
  }
}
```

## Runtime Dependencies

### Import Patterns

Services import from shared packages using standard ES modules:

```typescript
// Reader service imports
import { AlgorandClientFactory } from '@algorand-showcase/algorand-clients';
import { ConfigManager } from '@algorand-showcase/config';
import { MCPServer, BaseTool } from '@algorand-showcase/mcp-core';
import { AlgorandAccount, MCPResponse } from '@algorand-showcase/types';

// Usage in service
const clientFactory = new AlgorandClientFactory();
const algodClient = clientFactory.createAlgodClient(config.algod);
```

### Dependency Injection

Services use dependency injection for better testability:

```typescript
// Service initialization
class ReaderService {
  constructor(
    private clientFactory: AlgorandClientFactory,
    private configManager: ConfigManager,
    private mcpServer: MCPServer
  ) {}

  async initialize(): Promise<void> {
    const config = this.configManager.loadEnvironment(process.env.NODE_ENV);
    const client = this.clientFactory.createAlgodClient(config.algod);

    // Register tools with MCP server
    this.mcpServer.registerTool(new GetAccountTool(client));
  }
}
```

## Version Management

### Semantic Versioning

All packages follow semantic versioning:

```json
{
  "name": "@algorand-showcase/mcp-core",
  "version": "1.2.3",
  "description": "Core MCP protocol implementation"
}
```

### Breaking Change Impact

Breaking changes in shared packages affect all dependent services:

| Package | Breaking Change | Impact |
|---------|----------------|---------|
| types | Interface changes | Compilation errors in all services |
| config | Schema changes | Runtime configuration errors |
| algorand-clients | API changes | Client initialization failures |
| mcp-core | Protocol changes | MCP communication failures |

### Update Strategy

1. **Minor Updates**: Backward compatible, safe to update
2. **Major Updates**: Breaking changes, requires testing and code updates
3. **Patch Updates**: Bug fixes, recommended for security updates

## Integration Testing

### Package Integration Tests

Test shared package integration in isolation:

```typescript
// Integration test example
describe('AlgorandClientFactory Integration', () => {
  it('should create functional clients with config package', async () => {
    const configManager = new ConfigManager();
    const config = configManager.getNetworkConfig('testnet');

    const factory = new AlgorandClientFactory();
    const client = factory.createAlgodClient(config.algod);

    const status = await client.status().do();
    expect(status).toBeDefined();
  });
});
```

### End-to-End Testing

Test complete service functionality with all packages:

```typescript
// E2E test example
describe('Reader Service E2E', () => {
  it('should handle MCP requests end-to-end', async () => {
    const service = new ReaderService(
      new AlgorandClientFactory(),
      new ConfigManager(),
      new MCPServer()
    );

    await service.initialize();

    const response = await service.handleMCPRequest({
      tool: 'getAccount',
      arguments: { address: 'EXAMPLE_ADDRESS' }
    });

    expect(response.content).toBeDefined();
  });
});
```

## Performance Impact

### Bundle Size Analysis

Shared packages contribute to service bundle size:

| Package | Approximate Size | Impact |
|---------|-----------------|---------|
| types | ~50KB | Type definitions only |
| config | ~100KB | Validation schemas |
| algorand-clients | ~500KB | Algorand SDK dependencies |
| mcp-core | ~200KB | MCP protocol implementation |
| **Total Overhead** | **~850KB** | Added to each service |

### Runtime Performance

- **Initialization**: Shared packages add ~200ms to service startup
- **Memory**: Additional ~50MB heap usage per service
- **Network**: Connection pooling reduces per-request overhead

## Migration Considerations

### Package Extraction

When extracting functionality to shared packages:

1. **Identify Common Code**: Look for duplicated logic across services
2. **Define Clear Interfaces**: Create stable APIs for package consumers
3. **Minimize Dependencies**: Keep package dependencies minimal
4. **Document Breaking Changes**: Clearly communicate API changes

### Platform Migration

When migrating to different platforms:

1. **Package Compatibility**: Ensure packages work on target platform
2. **Build System**: Adapt build configuration for new environment
3. **Dependency Resolution**: Verify workspace protocol support
4. **Runtime Environment**: Test package loading in target runtime

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Package not found
Error: Cannot resolve '@algorand-showcase/types'
Solution: Run `pnpm install` to link workspace packages

# Build order issues
Error: Cannot find module '@algorand-showcase/config'
Solution: Build packages in correct order with `pnpm build`
```

#### Runtime Errors
```typescript
// Module not found at runtime
ModuleNotFoundError: No module named '@algorand-showcase/types'
Solution: Verify package is built and properly linked

// Version conflicts
Error: Package version mismatch
Solution: Update all packages to compatible versions
```

### Debug Steps

1. **Verify Package Structure**: Check package.json and file structure
2. **Check Build Output**: Ensure packages compile successfully
3. **Validate Imports**: Verify import paths and exported modules
4. **Test Isolation**: Test packages independently before integration
5. **Check Versions**: Ensure compatible versions across all packages