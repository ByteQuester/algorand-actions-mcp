# Repository Structure

This document outlines the intended monorepo structure and how current folders will be organized in the future.

## Intended Structure

```
algorand-showcase/
├── apps/                    # Application deployments
│   ├── actions-mcp-worker/  # Cloudflare Worker for actions-mcp
│   └── remote-mcp-worker/   # Cloudflare Worker for remote-mcp
├── packages/                # Shared libraries and utilities
│   ├── mcp-core/           # Core MCP functionality
│   ├── algorand-clients/   # Algorand SDK wrappers and utilities
│   ├── config/             # Shared configuration schemas
│   └── types/              # Shared TypeScript types
├── docs/                    # Documentation and guides
├── environments/            # Environment configurations
│   ├── development/
│   ├── staging/
│   └── production/
├── scripts/                 # Build and deployment scripts
├── .github/                # GitHub Actions workflows
├── etl/                    # Data processing (existing)
├── web/                    # Frontend applications (existing)
└── vendors/                # Third-party dependencies (existing)
```

## Current Folder Mapping

### Moving to `apps/`
- `vendors/algorand-actions-mcp/` → `apps/actions-mcp-worker/`
- `vendors/algorand-remote-mcp/` → `apps/remote-mcp-worker/`

Each app will maintain its own:
- `wrangler.toml` configuration
- Environment-specific settings
- Deployment scripts
- App-specific dependencies

### Moving to `packages/`
Shared code will be extracted from current apps into:
- `packages/mcp-core/` - Common MCP server patterns, utilities
- `packages/algorand-clients/` - Algod/Indexer client wrappers
- `packages/config/` - Configuration schemas and validation
- `packages/types/` - Shared TypeScript interfaces

### Staying in place
- `etl/` - Data processing workflows
- `web/` - Frontend applications
- `scripts/` - Build and utility scripts (expanded)
- `.github/` - CI/CD workflows (enhanced)

## Migration Approach

### Phase 1: Baseline (This PR)
- Create directory structure
- Add documentation and plans
- No code movement yet

### Phase 2: Package Extraction
- Identify shared code patterns
- Extract to `packages/`
- Set up workspace dependencies

### Phase 3: App Migration
- Move apps to new structure
- Update configurations
- Test deployments

### Phase 4: CI/CD Enhancement
- Workspace-aware builds
- Parallel testing
- Environment deployments

## Benefits

1. **Clear separation** between deployable apps and shared code
2. **Workspace management** with pnpm workspaces
3. **Scalable CI/CD** with matrix builds per app/package
4. **Environment management** with dedicated config directories
5. **Code reuse** through shared packages