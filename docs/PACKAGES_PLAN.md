# Packages Plan

This document outlines the shared library boundaries, responsibilities, and API design for the `packages/` directory.

## Package Structure

Each package will be structured as follows:
```
packages/
├── mcp-core/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
├── algorand-clients/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
├── config/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
└── types/
    ├── src/
    ├── package.json
    ├── tsconfig.json
    └── README.md
```

## Package Responsibilities

### `packages/mcp-core/`
**Purpose**: Common MCP server patterns, utilities, and base classes

**Responsibilities**:
- MCP server initialization and setup
- Common request/response handling patterns
- Tool registration and execution framework
- Error handling and logging utilities
- Request validation and sanitization
- Response formatting helpers

**API Surface**:
```typescript
// Core server setup
export class MCPServer {
  constructor(config: MCPConfig)
  registerTool(tool: MCPTool): void
  start(): Promise<void>
}

// Tool framework
export abstract class MCPTool {
  abstract execute(params: unknown): Promise<unknown>
  validate(params: unknown): boolean
}

// Utilities
export const createStandardResponse: (data: unknown) => MCPResponse
export const validateRequest: (req: MCPRequest) => boolean
export const formatError: (error: Error) => MCPError
```

### `packages/algorand-clients/`
**Purpose**: Algorand SDK wrappers and client abstractions

**Responsibilities**:
- Algod client wrapper with retry logic
- Indexer client wrapper with pagination
- Network configuration management
- Transaction utilities and helpers
- Account information caching
- Rate limiting and circuit breaker patterns

**API Surface**:
```typescript
// Client wrappers
export class AlgodClient {
  constructor(config: NetworkConfig)
  getAccount(address: string): Promise<AccountInfo>
  submitTransaction(txn: Transaction): Promise<TxnResult>
  simulateTransaction(txn: Transaction): Promise<SimResult>
}

export class IndexerClient {
  constructor(config: NetworkConfig)
  searchTransactions(params: SearchParams): Promise<Transaction[]>
  lookupAccount(address: string): Promise<AccountDetails>
}

// Utilities
export const buildPaymentTxn: (params: PaymentParams) => Transaction
export const parseTransaction: (txn: unknown) => Transaction
export const formatAmount: (microAlgos: number) => string
```

### `packages/config/`
**Purpose**: Shared configuration schemas and validation

**Responsibilities**:
- Environment configuration schemas
- Network settings validation
- API key and secret management
- Configuration loading utilities
- Environment-specific defaults
- Schema validation using Zod or similar

**API Surface**:
```typescript
// Configuration schemas
export const NetworkConfigSchema: z.ZodSchema<NetworkConfig>
export const MCPConfigSchema: z.ZodSchema<MCPConfig>
export const AppConfigSchema: z.ZodSchema<AppConfig>

// Configuration loading
export const loadConfig: (env?: string) => Promise<Config>
export const validateConfig: (config: unknown) => Config
export const getNetworkConfig: (network: string) => NetworkConfig

// Types
export interface NetworkConfig {
  algodUrl: string
  indexerUrl: string
  apiKey?: string
  network: 'mainnet' | 'testnet' | 'betanet'
}
```

### `packages/types/`
**Purpose**: Shared TypeScript type definitions

**Responsibilities**:
- Common interface definitions
- Algorand-specific types
- MCP protocol types
- API response types
- Error type definitions
- Utility types and generics

**API Surface**:
```typescript
// MCP Types
export interface MCPRequest {
  method: string
  params: Record<string, unknown>
  id: string
}

export interface MCPResponse {
  result?: unknown
  error?: MCPError
  id: string
}

// Algorand Types
export interface AccountInfo {
  address: string
  amount: number
  assets: Asset[]
  apps: Application[]
}

export interface Transaction {
  id: string
  type: string
  sender: string
  receiver?: string
  amount?: number
}

// Utility Types
export type Result<T, E = Error> = { success: true; data: T } | { success: false; error: E }
export type AsyncResult<T, E = Error> = Promise<Result<T, E>>
```

## Package Dependencies

### Internal Dependencies
```
mcp-core → config, types
algorand-clients → config, types
config → types
types → (no dependencies)
```

### External Dependencies
- `mcp-core`: @modelcontextprotocol/sdk, zod
- `algorand-clients`: algosdk, node-fetch
- `config`: zod, dotenv
- `types`: (no external dependencies)

## API Design Principles

1. **Consistent Error Handling**: All packages use Result<T, E> pattern
2. **Strong Typing**: Full TypeScript coverage with strict mode
3. **Async by Default**: All I/O operations return promises
4. **Configuration-Driven**: Behavior controlled through config objects
5. **Testable**: All functions are pure or dependency-injected
6. **Extensible**: Plugin/middleware patterns for customization

## Migration Strategy

1. **Identify Common Code**: Audit current apps for shared functionality
2. **Extract Core Patterns**: Start with `packages/types/` and `packages/config/`
3. **Build Clients**: Extract Algorand client code to `packages/algorand-clients/`
4. **Create Framework**: Build `packages/mcp-core/` with common patterns
5. **Update Apps**: Refactor apps to use packages
6. **Add Tests**: Comprehensive test coverage for each package
7. **Documentation**: API docs and usage examples

## Package Publishing

- All packages will be private (not published to npm)
- Managed through pnpm workspaces
- Version-locked to prevent dependency mismatches
- Shared build and test scripts