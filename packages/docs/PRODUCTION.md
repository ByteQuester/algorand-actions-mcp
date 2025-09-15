# Production Deployment Guide

## Overview

This guide covers deploying the Algorand Showcase packages in production environments. All packages have been cleaned and organized for production readiness while preserving development tools.

## Package Architecture

### TypeScript Packages
- **@algorand-showcase/types**: Shared TypeScript type definitions
- **@algorand-showcase/config**: Environment configuration and validation
- **@algorand-showcase/algorand-clients**: Algorand SDK wrappers and utilities
- **@algorand-showcase/mcp-core**: MCP protocol implementation patterns

### Python Packages
- **@algorand-showcase/lending-core**: Pure business logic for lending operations
- **@algorand-showcase/lending-api**: FastAPI wrapper for lending-core

## Production Structure

Each package follows this standardized structure:

```
package-name/
├── src/                    # Production source code
│   ├── index.ts/py        # Main package export
│   └── lib/               # Library modules
├── scripts/               # Development tools (preserved)
│   ├── dev/              # Debug utilities and helpers
│   ├── test/             # Test runners and utilities
│   ├── build/            # Build scripts
│   └── examples/         # Usage examples
├── config/               # Configuration templates
│   └── .env.example      # Environment variable template
├── dist/                 # Built artifacts (TypeScript)
├── package.json          # Standardized package configuration
├── tsconfig.json         # TypeScript configuration
└── README.md             # Package documentation
```

## Environment Configuration

### Required Environment Variables

#### All Packages
```bash
NODE_ENV=production                    # Environment mode
```

#### Config Package
```bash
ALGORAND_NETWORK=mainnet              # Network selection
ALLOW_MAINNET=true                    # Enable mainnet operations
```

#### MCP Core Package
```bash
# Logging disabled in production by default
# No additional environment variables required
```

#### Lending Core Package
```bash
LENDING_READER_ENDPOINT=https://reader.your-domain.com
LENDING_WRITER_ENDPOINT=https://writer.your-domain.com
LENDING_TIMEOUT_SECONDS=30
LENDING_RETRY_COUNT=3
ALGORAND_NETWORK=mainnet
```

#### Lending API Package
```bash
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://your-frontend.com,https://your-app.com
LENDING_READER_ENDPOINT=https://reader.your-domain.com
LENDING_WRITER_ENDPOINT=https://writer.your-domain.com
```

## Build Process

### TypeScript Packages

1. **Install dependencies**:
   ```bash
   cd packages/
   pnpm install
   ```

2. **Build all packages**:
   ```bash
   pnpm run build
   ```

3. **Type checking**:
   ```bash
   pnpm run validate
   ```

### Python Packages

1. **Install dependencies**:
   ```bash
   cd packages/lending-core/
   pip install -e .

   cd packages/lending-api/
   pip install -e .
   ```

2. **Build packages**:
   ```bash
   python setup.py sdist bdist_wheel
   ```

## Deployment Configurations

### TypeScript Packages (Node.js/Cloudflare Workers)

#### Production Build
```bash
# Build for production
NODE_ENV=production pnpm run build

# Validate production build
NODE_ENV=production pnpm run validate
```

#### Cloudflare Workers
```bash
# Use built packages in worker applications
# Import from dist/ directories
import { ResponseProcessor } from '@algorand-showcase/mcp-core';
import { loadNetworkConfig } from '@algorand-showcase/config';
```

### Python Packages (Docker/Server)

#### Dockerfile Example
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy and install lending-core
COPY packages/lending-core/ ./lending-core/
RUN pip install ./lending-core/

# Copy and install lending-api
COPY packages/lending-api/ ./lending-api/
RUN pip install ./lending-api/

# Set production environment
ENV NODE_ENV=production
ENV PYTHONPATH=/app

# Start API server
CMD ["uvicorn", "lending_api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use secure secret management systems
- Rotate API keys and tokens regularly

### 2. Network Configuration
- Verify `ALLOW_MAINNET` settings in production
- Use secure HTTPS endpoints
- Implement rate limiting

### 3. CORS Configuration
- Restrict CORS origins to known domains
- Avoid wildcard origins in production
- Validate all incoming requests

### 4. Logging
- Debug logging is disabled by default in production
- Use structured logging for monitoring
- Avoid logging sensitive information

## Monitoring and Health Checks

### TypeScript Packages
```typescript
// Health check endpoint
import { loadNetworkConfig } from '@algorand-showcase/config';

export function healthCheck() {
  try {
    const config = loadNetworkConfig();
    return { status: 'healthy', network: config.network };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}
```

### Python Packages
```python
# Health check endpoint
from lending_api.server import app

@app.get("/health")
async def health_check():
    try:
        # Validate configuration
        config = MCPServiceConfig.from_environment()
        return {"status": "healthy", "endpoints": {
            "reader": config.reader_endpoint,
            "writer": config.writer_endpoint
        }}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Performance Optimization

### 1. Build Optimization
- Use production builds for all TypeScript packages
- Enable dead code elimination
- Minimize bundle sizes

### 2. Runtime Optimization
- Configure appropriate timeout values
- Implement connection pooling for Algorand clients
- Use caching for frequently accessed data

### 3. Scaling Considerations
- Use horizontal scaling for API servers
- Implement load balancing
- Monitor resource usage

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Check `.env.example` files for required variables
   - Validate configuration using development scripts

2. **Network Configuration Errors**
   - Use `packages/config/scripts/dev/network-config-helper.js` to test configurations
   - Verify ALLOW_MAINNET settings

3. **Package Dependencies**
   - Ensure all workspace dependencies are built
   - Check import paths and package exports

4. **CORS Issues**
   - Verify CORS_ORIGINS configuration
   - Check for trailing slashes in URLs

### Debug Mode

To enable debug mode in production (temporarily):

```bash
# TypeScript packages
NODE_ENV=development

# Python packages
LENDING_DEBUG=true
```

## Migration from Development

1. **Update Environment Variables**
   - Copy `.env.example` to `.env`
   - Update all URLs and endpoints
   - Set production-appropriate values

2. **Build and Test**
   - Run full build process
   - Execute validation scripts
   - Test health checks

3. **Deploy**
   - Use production Docker images
   - Configure monitoring
   - Set up logging

## Support

For production support:
- Check package READMEs for specific configuration
- Use development scripts in `scripts/` directories for debugging
- Review logs for configuration errors
- Test network connectivity using provided utilities