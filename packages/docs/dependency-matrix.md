# Package Dependency Matrix

## Overview

This document maps all dependencies within the packages ecosystem, including internal package dependencies, external library dependencies, and app integration dependencies.

## Internal Package Dependencies

### Dependency Graph

```
types (foundation)
  ↑
  ├── config
  ├── algorand-clients
  └── mcp-core
      ↑
      └── (used by apps)

Note: lending-core and lending-api have been moved to
apps/lending-platform/src/ as application-specific modules
```

### Detailed Dependency Matrix

| Package | Depends On | Used By | External Dependencies |
|---------|------------|---------|----------------------|
| **types** | None | config, algorand-clients, mcp-core | buffer (peer) |
| **config** | types | mcp-core, apps | zod |
| **algorand-clients** | types | apps | algosdk, algo-msgpack-with-bigint |
| **mcp-core** | types, config | apps | zod |

## External Dependencies

### Production Dependencies

#### TypeScript Packages

**@algorand-showcase/types**
- `buffer` (peer dependency) - For Algorand address/transaction handling

**@algorand-showcase/config**
- `zod` ^3.23.8 - Runtime validation and schema definition

**@algorand-showcase/algorand-clients**
- `algosdk` 2.11.0 - Official Algorand JavaScript SDK
- `algo-msgpack-with-bigint` ^2.1.1 - MessagePack with BigInt support

**@algorand-showcase/mcp-core**
- `zod` ^3.23.8 - Runtime validation and schema definition

#### Python Packages

**@algorand-showcase/lending-core**
- No production dependencies (pure business logic)
- Optional: `py-algorand-sdk` >=2.0.0 (extras_require)

**@algorand-showcase/lending-api**
- `fastapi` >=0.100.0 - Modern web framework
- `uvicorn` >=0.20.0 - ASGI server
- `@algorand-showcase/lending-core` 1.0.0

### Development Dependencies

#### TypeScript Common
- `typescript` ^5.6.2 - TypeScript compiler
- `@types/node` - Node.js type definitions

#### Python Common
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `black` - Code formatting
- `isort` - Import sorting
- `mypy` - Type checking

## App Integration Dependencies

### MCP Services (apps/mcp-services/)

Both algorand-reader-mcp and algorand-writer-mcp depend on:

**Shared Packages Used:**
- `@algorand-showcase/algorand-clients` - Blockchain client management
- `@algorand-showcase/config` - Environment configuration
- `@algorand-showcase/mcp-core` - MCP protocol implementation
- `@algorand-showcase/types` - Shared type definitions

**External Dependencies:**
- `@modelcontextprotocol/sdk` ^1.12.1 - MCP protocol SDK
- `agents` ^0.0.95 - Agent framework
- `ws` ^8.18.3 - WebSocket support
- `zod` ^4.1.8 - Validation
- `hono` ^4.8.0 - HTTP framework

### Lending Platform (apps/lending-platform/)

**Python Package Dependencies:**
- Uses packages through pip install or local imports
- Not currently using workspace references

**Potential Integration:**
- Could import `@algorand-showcase/lending-core`
- Could import `@algorand-showcase/lending-api`

## Version Compatibility Matrix

### TypeScript Ecosystem

| Package Version | Node.js | TypeScript | Algorand SDK |
|----------------|---------|------------|--------------|
| types@0.1.0 | >=18.0.0 | ^5.6.2 | N/A |
| config@0.1.0 | >=18.0.0 | ^5.6.2 | N/A |
| algorand-clients@0.1.0 | >=18.0.0 | ^5.6.2 | 2.11.0 |
| mcp-core@0.1.0 | >=18.0.0 | ^5.6.2 | N/A |

### Python Ecosystem

| Package Version | Python | FastAPI | Algorand SDK |
|----------------|--------|---------|--------------|
| lending-core@1.0.0 | >=3.8 | N/A | >=2.0.0 (opt) |
| lending-api@1.0.0 | >=3.8 | >=0.100.0 | Via lending-core |

## Build Order Dependencies

### Required Build Sequence

1. **types** (foundation package)
2. **config** (depends on types)
3. **algorand-clients** (depends on types)
4. **mcp-core** (depends on types + config)
5. **lending-core** (standalone)
6. **lending-api** (depends on lending-core)

### Parallel Build Groups

**Group 1** (can build in parallel after types):
- config
- algorand-clients

**Group 2** (can build after Group 1):
- mcp-core

**Group 3** (independent):
- lending-core

**Group 4** (after lending-core):
- lending-api

## Breaking Change Impact Analysis

### If types package changes:
- **Direct impact**: config, algorand-clients, mcp-core
- **Indirect impact**: All apps using MCP services
- **Mitigation**: Semantic versioning, backward compatibility

### If config package changes:
- **Direct impact**: mcp-core
- **Indirect impact**: Apps using MCP services
- **Mitigation**: Environment validation, graceful degradation

### If algorand-clients package changes:
- **Direct impact**: Apps using blockchain functionality
- **Mitigation**: SDK version compatibility testing

### If mcp-core package changes:
- **Direct impact**: All MCP service apps
- **Mitigation**: Protocol compatibility testing

### If lending packages change:
- **Direct impact**: Lending platform app
- **Mitigation**: API versioning, contract testing

## Dependency Management Strategies

### 1. Workspace Dependencies
```json
"dependencies": {
  "@algorand-showcase/types": "workspace:*"
}
```

### 2. Version Pinning
- Pin exact versions for Algorand SDK
- Use semver ranges for utility libraries
- Lock development dependencies

### 3. Peer Dependencies
- Use peer dependencies for large libraries
- Allow consuming apps to control versions
- Avoid duplication in bundles

### 4. Optional Dependencies
- Use extras_require for Python packages
- Separate dev/prod dependency sets
- Allow minimal installations

## Migration Considerations

### From Monorepo to External Hosting

**TypeScript Packages:**
- Can be published to npm as scoped packages
- Maintain workspace references during transition
- Use registry overrides for gradual migration

**Python Packages:**
- Can be published to PyPI
- Use pip install from git for interim
- Maintain editable installs for development

### Dependency Updates

**Algorand SDK Updates:**
- Test compatibility across all packages
- Update in algorand-clients first
- Validate with integration tests

**Framework Updates:**
- Test TypeScript compiler compatibility
- Validate MCP protocol compatibility
- Test FastAPI/uvicorn combinations

## Monitoring and Alerts

### Dependency Health
- Monitor for security vulnerabilities
- Track outdated dependencies
- Automate compatibility testing

### Build Health
- Monitor build order success
- Track build time regression
- Alert on dependency resolution failures

### Runtime Health
- Monitor package load times
- Track memory usage by package
- Alert on import failures