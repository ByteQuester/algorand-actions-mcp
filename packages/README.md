# Algorand Showcase Packages

Production-ready shared packages for the Algorand Showcase ecosystem, organized for both production deployment and development workflows.

## Package Ecosystem

### TypeScript Packages
- **[types/](./types/)** - Shared TypeScript interfaces and type definitions
- **[config/](./config/)** - Environment configuration and validation utilities
- **[algorand-clients/](./algorand-clients/)** - Algorand SDK wrappers and client abstractions
- **[mcp-core/](./mcp-core/)** - MCP protocol implementation patterns and utilities

### Python Packages
- **[lending-core/](./lending-core/)** - Pure business logic for Algorand lending operations
- **[lending-api/](./lending-api/)** - FastAPI wrapper for lending-core

## Production Features

✅ **Clean Production Code** - No console.log or hardcoded values in production builds
✅ **Environment-Based Configuration** - All settings configurable via environment variables
✅ **Preserved Development Tools** - Debug utilities and helpers organized in scripts/ directories
✅ **Standardized Build Process** - Consistent scripts and workflows across all packages
✅ **Comprehensive Documentation** - Complete deployment and usage guides

## Quick Start

### Development Setup
```bash
# Install all dependencies
pnpm install

# Setup development environment for all packages
pnpm run setup-dev

# Build all TypeScript packages
pnpm run build:ts

# Validate all packages
pnpm run validate
```

### Production Build
```bash
# Build for production
NODE_ENV=production pnpm run build:ts

# TypeScript packages ready in dist/ directories
# Python packages: use pip install for deployment
```

## Package Structure

Each package follows a standardized structure:

```
package-name/
├── src/                    # Production source code
├── scripts/               # Development tools (preserved)
│   ├── dev/              # Debug utilities and helpers
│   ├── test/             # Test runners and utilities
│   ├── build/            # Build scripts
│   └── examples/         # Usage examples
├── config/               # Configuration templates
│   └── .env.example      # Environment variable template
├── dist/                 # Built artifacts (TypeScript)
├── package.json          # Standardized package configuration
└── README.md             # Package documentation
```

## Package Dependencies

### Internal Dependencies
```
types (foundation)
  ↑
  ├── config
  ├── algorand-clients
  └── mcp-core
      ↑
      └── (used by apps)

lending-core (standalone)
  ↑
  └── lending-api
```

### External Dependencies
- **TypeScript**: algosdk, zod, buffer
- **Python**: fastapi, uvicorn (api only)
- **Development**: typescript, pytest, black

## Usage Examples

### TypeScript Packages
```typescript
import { AlgorandNetwork, MCPToolResult } from '@algorand-showcase/types';
import { loadNetworkConfig } from '@algorand-showcase/config';
import { AlgodClientWrapper } from '@algorand-showcase/algorand-clients';
import { ResponseProcessor } from '@algorand-showcase/mcp-core';

// Load environment configuration
const config = loadNetworkConfig();

// Create Algorand client
const algod = new AlgodClientWrapper({
  network: config.network,
  algodUrl: process.env.ALGOD_URL || ''
});

// Process responses with pagination
const result = ResponseProcessor.processResponse(data);
```

### Python Packages
```python
from algorand_lending_core.models import MCPServiceConfig, LoanRequest
from algorand_lending_core.lending_engine import LendingEngine

# Load configuration from environment
config = MCPServiceConfig.from_environment()

# Create lending engine
engine = LendingEngine(config)

# Process loan request
await engine.process_loan_request(loan_request)
```

## Development Tools

### Debug Utilities
- `mcp-core/scripts/dev/debug-utils.ts` - Configurable logging
- `config/scripts/dev/network-config-helper.ts` - Network testing
- `lending-core/scripts/dev/config_helper.py` - Configuration presets

### Testing Utilities
- `mcp-core/scripts/examples/test-response-processor.ts`
- Package-specific test runners via `npm run test`

### Environment Setup
- `.env.example` templates in each package's config/ directory
- Automated setup via `npm run setup-dev`

## App Integration

### MCP Services (apps/mcp-services/)
Both algorand-reader-mcp and algorand-writer-mcp use:
- All TypeScript packages via workspace links
- Clean production builds with optional debug logging
- Environment-based configuration

### Lending Platform (apps/lending-platform/)
Can integrate with:
- Python lending packages for business logic
- TypeScript packages for blockchain interactions

## Production Deployment

### Environment Configuration
Copy and customize `.env.example` files:
```bash
# TypeScript packages
cp packages/config/config/.env.example .env

# Python packages
cp packages/lending-core/config/.env.example .env
cp packages/lending-api/config/.env.example .env
```

### Build and Deploy
```bash
# TypeScript packages - build to dist/
NODE_ENV=production pnpm run build:ts

# Python packages - install for deployment
pip install ./packages/lending-core/
pip install ./packages/lending-api/
```

## Documentation

- **[PRODUCTION.md](./docs/PRODUCTION.md)** - Complete production deployment guide
- **[USAGE.md](./docs/USAGE.md)** - Detailed usage examples and integration patterns
- **[dependency-matrix.md](./docs/dependency-matrix.md)** - Complete dependency mapping and analysis
- **[MIGRATION_REPORT.md](./docs/MIGRATION_REPORT.md)** - Detailed migration and cleanup report

## Migration Status

✅ **Production Ready** - All packages cleaned and organized for production
✅ **Development Tools Preserved** - All debug utilities maintained in scripts/
✅ **App Compatible** - Existing applications continue to work unchanged
✅ **Future Ready** - Prepared for hosting-monorepo integration or independent deployment

For detailed migration information, see [MIGRATION_REPORT.md](./docs/MIGRATION_REPORT.md).