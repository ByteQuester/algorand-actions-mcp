# MCP Services Dependencies & Architecture

## Overview

The Algorand MCP services are built using a modular architecture with shared packages and external integrations. This document maps all dependencies and their relationships.

## Service Architecture

```
apps/mcp-services/
├── algorand-reader-mcp/     # Read-only blockchain data access
└── algorand-writer-mcp/     # Transaction building and submission
```

## Shared Package Dependencies

### Core Packages Used by Both Services

#### @algorand-showcase/algorand-clients
- **Purpose**: Algorand blockchain client abstractions
- **Used by**: Both reader and writer services
- **Key Features**:
  - Algod client management
  - Indexer client management
  - Connection pooling
  - Network configuration

#### @algorand-showcase/config
- **Purpose**: Configuration management utilities
- **Used by**: Both reader and writer services
- **Key Features**:
  - Environment variable handling
  - Network-specific configurations
  - Validation utilities

#### @algorand-showcase/mcp-core
- **Purpose**: Core MCP protocol implementation
- **Used by**: Both reader and writer services
- **Key Features**:
  - MCP server framework
  - Request/response handling
  - Protocol validation
  - Tool registration

#### @algorand-showcase/types
- **Purpose**: Shared TypeScript type definitions
- **Used by**: Both reader and writer services
- **Key Features**:
  - Algorand data types
  - MCP protocol types
  - Service interfaces
  - Validation schemas

## External Dependencies

### Runtime Dependencies

#### Production Dependencies
- **@modelcontextprotocol/sdk**: MCP protocol implementation
- **agents**: Agent framework integration
- **ws**: WebSocket support for MCP
- **zod**: Runtime type validation
- **hono**: HTTP framework (reader service)
- **just-pick**: Object property selection utility
- **hi-base32**: Base32 encoding for Algorand addresses

#### Reader Service Specific
- **@cf-wasm/photon**: Cloudflare WebAssembly utilities
- **@juit/qrcode**: QR code generation
- **qrcode**: QR code library

### Development Dependencies
- **typescript**: TypeScript compiler
- **wrangler**: Cloudflare Workers CLI
- **@biomejs/biome**: Code formatting and linting

## External Service Integrations

### Algorand Network Services

#### Algod Nodes
- **Production (Reader)**: https://mainnet-api.algonode.cloud
- **Production (Writer)**: https://testnet-api.algonode.cloud
- **Purpose**: Transaction submission and blockchain queries

#### Indexer Services
- **Production (Reader)**: https://mainnet-idx.algonode.cloud
- **Production (Writer)**: https://testnet-idx.algonode.cloud
- **Purpose**: Historical data queries and search

### Third-Party APIs

#### NFD (Non-Fungible Domains)
- **URL**: https://api.nf.domains
- **Purpose**: Domain name resolution for Algorand addresses
- **Used by**: Both services

#### Pera Wallet API
- **Mainnet**: https://mainnet.api.perawallet.app/v1/public
- **Testnet**: https://testnet.api.perawallet.app/v1/public
- **Purpose**: Wallet integration and account data

#### Pera Explorer
- **Mainnet**: https://explorer.perawallet.app
- **Testnet**: https://testnet.explorer.perawallet.app
- **Purpose**: Transaction and account exploration

### Authentication Services (Reader Service Only)

#### HashiCorp Vault Worker
- **URL**: Configurable via HCV_WORKER_URL
- **Purpose**: Secure credential management
- **Integration**: OAuth token storage and retrieval

#### OAuth Providers
- **Google**: OAuth 2.0 authentication
- **GitHub**: OAuth 2.0 authentication
- **LinkedIn**: OAuth 2.0 authentication
- **Twitter**: OAuth 2.0 authentication

### Cloudflare Platform Services (Production Deployment)

#### Durable Objects
- **Reader**: AlgorandRemoteMCP
- **Writer**: AlgorandActionsMCP
- **Purpose**: Persistent state management

#### KV Namespaces (Reader Service)
- **OAUTH_KV**: OAuth session storage
- **VAULT_ENTITIES**: Vault entity mappings
- **PUBLIC_KEY_CACHE**: Cached public keys
- **CODE_VERIFIER_KV**: PKCE code verifiers
- **ARC26_KV**: ARC26 metadata cache

#### R2 Object Storage (Reader Service)
- **PLAUSIBLE_AI**: Analytics and public data storage

#### Service Bindings
- **HCV_WORKER**: HashiCorp Vault Worker service

## Network Configuration Matrix

| Service | Environment | Network | Algod | Indexer | Read-Only |
|---------|-------------|---------|-------|---------|-----------|
| Reader  | Production  | Mainnet | mainnet-api.algonode.cloud | mainnet-idx.algonode.cloud | true |
| Reader  | Development | Testnet | testnet-api.algonode.cloud | testnet-idx.algonode.cloud | true |
| Writer  | Production  | Mainnet | mainnet-api.algonode.cloud | mainnet-idx.algonode.cloud | false |
| Writer  | Development | Testnet | testnet-api.algonode.cloud | testnet-idx.algonode.cloud | false |

## Security Dependencies

### Authentication Flow (Reader Service)
1. OAuth provider authentication
2. HashiCorp Vault credential storage
3. MCP client authorization
4. Cloudflare KV session management

### Transaction Security (Writer Service)
- Network restrictions (testnet/mainnet isolation)
- Transaction amount limits
- Confirmation requirements
- Audit logging

## Performance Considerations

### Shared Package Impact
- **Build time**: Shared packages must be built before services
- **Bundle size**: Core packages add ~2MB to each service
- **Runtime**: Client pooling reduces connection overhead

### External Service Limits
- **AlgoNode**: Rate limiting on public endpoints
- **NFD API**: Rate limiting on domain queries
- **OAuth Providers**: Rate limiting on authentication

## Migration Considerations

### Monorepo Integration
- Services expect workspace structure
- Shared packages must be available
- Build order dependencies

### Cloud Platform Migration
- Cloudflare-specific bindings need platform equivalents
- Durable Objects require persistent storage alternatives
- KV namespaces need key-value store mapping

### Environment Variable Mapping
- See `.env.example` files for complete variable lists
- Production secrets require secure injection
- Network configurations must match deployment environment