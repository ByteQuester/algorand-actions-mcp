# Shared Packages

This directory contains shared packages extracted from the Algorand MCP Workers to enable code reuse and maintain consistency across the monorepo.

## Package Structure

- **[types/](./types/)** - Shared TypeScript interfaces and types
- **[config/](./config/)** - Environment configuration and validation schemas  
- **[algorand-clients/](./algorand-clients/)** - Algod/Indexer client wrappers and utilities
- **[mcp-core/](./mcp-core/)** - Common MCP server patterns and utilities

## Development

### Building All Packages
```bash
cd packages
pnpm build
```

### Type Checking
```bash
cd packages  
pnpm type-check
```

### Clean Build Artifacts
```bash
cd packages
pnpm clean
```

## Package Dependencies

```
mcp-core → config, types
algorand-clients → types
config → types
types → (no dependencies)
```

## Usage in Workers

Workers can now import shared functionality:

```typescript
import { AlgorandNetwork, NetworkConfig } from '@algorand-showcase/types';
import { loadNetworkConfig, parseNetwork } from '@algorand-showcase/config';
import { AlgodClientWrapper } from '@algorand-showcase/algorand-clients';
import { ResponseProcessor } from '@algorand-showcase/mcp-core';
```

## Migration Notes

These packages were extracted from the existing Workers:
- Response processing logic from `algorand-remote-mcp`
- Configuration parsing patterns from both Workers
- Algorand SDK wrapper patterns from both Workers
- Common type definitions consolidated from both codebases

The extraction maintains backward compatibility - existing Workers continue to work unchanged.