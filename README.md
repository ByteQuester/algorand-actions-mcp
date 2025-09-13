# Algorand MCP Workers - Production-Ready Showcase

A comprehensive Model Context Protocol (MCP) implementation for Algorand blockchain interaction, featuring **dual deployment options**: Cloudflare Workers and Kubernetes with complete production-ready infrastructure.

## 🌟 Key Features

### **Dual MCP Workers**
- **Actions MCP Worker**: Transaction building, simulation, and submission
- **Remote MCP Worker**: Blockchain data access and account querying

### **Deployment Options**
- 🔷 **Cloudflare Workers** - Serverless edge deployment
- ☸️ **Kubernetes** - Container orchestration with Helm charts
- 🐳 **Docker** - Local development and testing

### **Production Features**
- ✅ HTTP REST API with OpenAPI/Swagger documentation
- ✅ Server-Sent Events (SSE) for real-time communication
- ✅ Multi-environment support (dev/staging/production)
- ✅ Comprehensive monitoring and health checks
- ✅ Security hardening and network policies
- ✅ Horizontal Pod Autoscaling
- ✅ CI/CD pipeline with GitHub Actions

## 🚀 Quick Start

### Option 1: Docker (Recommended for Development)
```bash
# Complete setup and start
make quick-start

# Or step by step
make install build docker-build docker-up
```

### Option 2: Kubernetes
```bash
# Deploy to development environment
cd environments
./deploy.sh -e development -w all

# Deploy to production
./validate.sh && ./deploy.sh -e production -w all
```

### Option 3: Cloudflare Workers
```bash
# Deploy Actions MCP Worker
cd apps/actions-mcp-worker
npm run deploy

# Deploy Remote MCP Worker
cd apps/remote-mcp-worker
npm run deploy
```

## 📚 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│                     (Claude, Custom Apps)                       │
└─────────────────┬───────────────────────────┬───────────────────┘
                  │                           │
                  │ HTTP REST API             │ SSE/MCP Protocol
                  │                           │
┌─────────────────▼───────────────┐  ┌───────▼───────────────────┐
│      Actions MCP Worker         │  │     Remote MCP Worker     │
│                                 │  │                           │
│ • Build Payment Transactions    │  │ • Account Information     │
│ • Simulate Transactions         │  │ • Transaction History     │
│ • Submit Signed Transactions    │  │ • Asset Information       │
│ • Testnet/Mainnet Support       │  │ • Block Data             │
└─────────────────┬───────────────┘  └───────┬───────────────────┘
                  │                          │
                  └─────┬────────────────────┘
                        │
              ┌─────────▼─────────┐
              │  Algorand Network │
              │   (Testnet/Mainnet) │
              └───────────────────┘
```

## 🔗 API Endpoints

### Actions MCP Worker
- **Base URL**: `http://localhost:8788` (Docker) or your deployed URL
- **Documentation**: `/docs` - Interactive Swagger UI
- **Health Check**: `/health` - Service health status
- **Metrics**: `/metrics` - Prometheus metrics

**Available Tools**:
- `POST /tools/build_payment` - Build unsigned payment transactions
- `POST /tools/simulate` - Simulate raw transactions
- `POST /tools/submit` - Submit signed transactions
- `GET /tools/list` - List all available tools

### Remote MCP Worker
- **Base URL**: `http://localhost:8789` (Docker) or your deployed URL
- **Documentation**: `/docs` - Interactive Swagger UI
- **Health Check**: `/health` - Service health status
- **Metrics**: `/metrics` - Prometheus metrics

**Available APIs**:
- `POST /api/account` - Get account information
- `POST /api/transaction` - Get transaction details
- `POST /api/asset` - Get asset information
- `POST /api/block` - Get block information
- `POST /api/search/transactions` - Search transactions

## 📁 Project Structure

```
algorand-showcase/
├── apps/                           # MCP Worker applications
│   ├── actions-mcp-worker/         # Transaction operations
│   │   ├── src/http-adapter.ts     # HTTP REST adapter
│   │   ├── server.js              # Node.js server wrapper
│   │   └── Dockerfile             # Container configuration
│   └── remote-mcp-worker/          # Blockchain data access
│       ├── src/http-adapter.ts     # HTTP REST adapter
│       ├── server.js              # Node.js server wrapper
│       └── Dockerfile             # Container configuration
├── packages/                       # Shared libraries
│   ├── mcp-core/                  # MCP utilities & OpenAPI generator
│   ├── algorand-clients/          # Algorand SDK wrappers
│   ├── config/                    # Configuration management
│   └── types/                     # TypeScript definitions
├── environments/                   # Kubernetes deployment
│   ├── charts/mcp-server/         # Helm chart templates
│   ├── development/               # Dev environment values
│   ├── staging/                   # Staging environment values
│   ├── production/                # Production environment values
│   ├── deploy.sh                  # Automated deployment
│   └── validate.sh                # Configuration validation
├── scripts/                       # Utility scripts
├── docs/                          # Documentation
└── docker-compose.yml             # Local development setup
```
   - Override endpoints via query params:
     - `?indexer=https://mainnet-idx.algonode.cloud&nfd=https://api.nf.domains`
   ```bash
   ./scripts/account_summary.sh "ADDRESS_OR_NFD"
   # Uses INDEXER_URL if set; otherwise falls back to local algod
   ```

## Remote MCP (optional)

This scaffold includes the Algorand Remote MCP server as a git submodule under `vendors/algorand-remote-mcp`. It exposes a comprehensive toolset (Indexer/algod/NFD/TEAL/tx ops). See the project for details:

- Algorand Remote MCP: [algorand-remote-mcp](https://github.com/ByteQuester/algorand-remote-mcp)

You can deploy the Worker later (e.g., with Wrangler). 
The included scripts are sufficient for a quick demo.

## Deploying the static UI

- Any static host works (GitHub Pages, Cloudflare Pages, Netlify, S3+CloudFront).
- Publish the `web/` directory as-is. No build step required.

## Environment

See `.env.example` for defaults. Common settings:

- `ALGOD_ADDR` (default `http://127.0.0.1:8080`)
- `ALGOD_TOKEN_FILE` (default `/var/lib/algorand/algod.token`)
- `INDEXER_URL` (e.g. `https://mainnet-idx.algonode.cloud`)
- `NFD_API_URL` (default `https://api.nf.domains`)

## License

MIT


