# 🚀 Algorand Showcase: AI-Powered Lending Platform

**Production-ready AI lending platform with real blockchain connectivity**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![Blockchain](https://img.shields.io/badge/Blockchain-Algorand%20Testnet-blue)]()
[![AI](https://img.shields.io/badge/AI-Google%20Gemini%201.5%20Flash-orange)]()
[![Architecture](https://img.shields.io/badge/Architecture-MCP%20Protocol-purple)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Transform lending with AI and blockchain - Two production-ready systems demonstrating real-world AI-powered finance**

The Algorand Showcase demonstrates AI-powered lending with **real blockchain connectivity**. It features two production-ready systems built with different architectural approaches, both integrating Google Gemini AI with Algorand blockchain through the MCP (Model Context Protocol).

## ✨ What Makes This Special?

🤖 **AI-Native Design**: Built from the ground up for AI agents using the Model Context Protocol (MCP) standard
🚀 **Production-Ready**: Complete infrastructure with monitoring, security, and scalability
🔄 **Dual Deployment**: Choose between serverless Cloudflare Workers or containerized Kubernetes
⚡ **Real-Time Communication**: Server-Sent Events (SSE) support for live blockchain updates
📊 **Comprehensive Tooling**: From transaction building to account analytics

## 🛠️ Core Components

### **Actions MCP Worker** - Transaction Operations
Build, simulate, and submit Algorand transactions with enterprise-grade reliability.

**Features:**
- 📝 Transaction building with parameter validation
- 🧪 Transaction simulation and testing
- 🚀 Secure transaction submission to testnet/mainnet
- 📊 Real-time transaction status monitoring
- 🔐 Multi-signature transaction support

### **Remote MCP Worker** - Blockchain Data Access
Query Algorand blockchain data with optimized performance and caching.

**Features:**
- 👤 Account information and balance tracking
- 📈 Transaction history and analytics
- 🪙 Asset information and metadata
- ⛓️ Block data and network statistics
- 🔍 Advanced search and filtering capabilities

## 🚀 Deployment Options

| Method | Use Case | Complexity | Scaling |
|--------|----------|------------|---------|
| 🐳 **Docker** | Local development, testing | Low | Manual |
| ☁️ **Cloudflare Workers** | Global edge deployment | Medium | Automatic |
| ☸️ **Kubernetes** | Enterprise production | High | Auto-scaling |

## ⚡ Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Docker and Docker Compose (for local development)
- kubectl and Helm (for Kubernetes deployment)

### 🐳 Option 1: Docker (5-minute setup)
Perfect for development and testing:

```bash
# Clone the repository
git clone https://github.com/ByteQuester/algorand-showcase.git
cd algorand-showcase

# One-command setup and start
make quick-start

# Access the services
# Actions MCP Worker: http://localhost:8788/docs
# Remote MCP Worker:  http://localhost:8789/docs
```

### ☁️ Option 2: Cloudflare Workers
Deploy globally in minutes:

```bash
# Install dependencies
pnpm install

# Deploy Actions MCP Worker
cd apps/blockchain/algorand-actions-mcp
pnpm run deploy

# Deploy Remote MCP Worker
cd apps/blockchain/algorand-remote-mcp
pnpm run deploy
```

### ☸️ Option 3: Kubernetes
Production-grade deployment:

```bash
# Validate configuration
cd environments && ./validate.sh

# Deploy to development
./deploy.sh -e development -w all

# Deploy to production
./deploy.sh -e production -w all
```

## 🧪 Test Your Installation

```bash
# Test Actions MCP Worker (transaction building)
curl -X POST http://localhost:8788/tools/build_payment \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "SENDER_ADDRESS",
    "receiver": "RECEIVER_ADDRESS",
    "amount": 1000000
  }'

# Test Remote MCP Worker (account data)
curl -X POST http://localhost:8789/api/account \
  -H "Content-Type: application/json" \
  -d '{"address": "ACCOUNT_ADDRESS"}'
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agents & Applications                     │
│         (Claude, GPT, Custom Apps, Web Interfaces)              │
└─────────────────┬───────────────────────────┬───────────────────┘
                  │                           │
                  │ HTTP REST API             │ Server-Sent Events
                  │ MCP Protocol              │ Real-time Updates
                  │                           │
┌─────────────────▼───────────────┐  ┌────────▼──────────────────┐
│      Actions MCP Worker         │  │     Remote MCP Worker     │
│                                 │  │                           │
│ 🔧 Transaction Operations       │  │ 📊 Blockchain Data Access │
│ • Build Payment Transactions    │  │ • Account Information     │
│ • Simulate Before Submit        │  │ • Transaction History     │
│ • Multi-sig Support             │  │ • Asset Metadata          │
│ • Error Handling & Retry        │  │ • Block Explorer Data     │
│ • Rate Limiting                 │  │ • Search & Analytics      │
└─────────────────┬───────────────┘  └───────┬───────────────────┘
                  │                          │
                  └─────────────┬────────────┘
                                │
                      ┌─────────▼─────────┐
                      │  Algorand Network │
                      │                   │
                      │ ⚡ Testnet         │
                      │ 🌐 Mainnet        │
                      │ 🔗 AlgoNode APIs  │
                      └───────────────────┘
```

### Key Design Principles

- **🔌 Modular**: Each worker focuses on specific functionality
- **🔄 Stateless**: Horizontally scalable without session dependencies
- **🛡️ Secure**: Multi-layer security with rate limiting and validation
- **📈 Observable**: Complete monitoring and logging infrastructure
- **🚀 Fast**: Optimized for low-latency blockchain operations

## 📖 API Documentation

### Actions MCP Worker - Transaction Operations

**Base URL**: `http://localhost:8788` (Docker) or your deployed URL

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs` | GET | 📖 Interactive Swagger/OpenAPI documentation |
| `/health` | GET | ❤️ Service health check and status |
| `/metrics` | GET | 📊 Prometheus metrics for monitoring |
| `/tools/list` | GET | 📋 List all available MCP tools |
| `/tools/build_payment` | POST | 💰 Build unsigned payment transactions |
| `/tools/simulate` | POST | 🧪 Simulate transactions before submission |
| `/tools/submit` | POST | 🚀 Submit signed transactions to network |

### Remote MCP Worker - Blockchain Data Access

**Base URL**: `http://localhost:8789` (Docker) or your deployed URL

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs` | GET | 📖 Interactive API documentation |
| `/health` | GET | ❤️ Service health and network status |
| `/metrics` | GET | 📊 Performance and usage metrics |
| `/api/account` | POST | 👤 Get account information and balances |
| `/api/transaction` | POST | 📋 Get transaction details and status |
| `/api/asset` | POST | 🪙 Get asset information and metadata |
| `/api/block` | POST | ⛓️ Get block information and contents |
| `/api/search/transactions` | POST | 🔍 Search transactions with filters |

### Example API Usage

```bash
# Build a payment transaction
curl -X POST http://localhost:8788/tools/build_payment \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
    "receiver": "GD64YIY3TWGDMCNPP553DZPPR6LDUSFQOIJVFDPPXWEG3FVOJCCDBBHU5A",
    "amount": 1000000,
    "note": "Test payment"
  }'

# Get account information
curl -X POST http://localhost:8789/api/account \
  -H "Content-Type: application/json" \
  -d '{
    "address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
  }'
```

## 📁 Project Structure

```
algorand-showcase/
├── 🏢 apps/                        # MCP Worker Applications
│   ├── actions-mcp-worker/         # 🔧 Transaction Operations
│   │   ├── src/
│   │   │   ├── index.ts           # Core MCP server implementation
│   │   │   ├── http-adapter.ts    # HTTP REST API wrapper
│   │   │   └── tools/             # MCP tools (build, simulate, submit)
│   │   ├── server.js              # Node.js production server
│   │   ├── Dockerfile             # Multi-stage container build
│   │   └── wrangler.toml          # Cloudflare Workers config
│   └── remote-mcp-worker/          # 📊 Blockchain Data Access
│       ├── src/
│       │   ├── index.ts           # Core MCP server implementation
│       │   ├── http-adapter.ts    # HTTP REST API wrapper
│       │   ├── tools/             # MCP tools (account, transaction, etc.)
│       │   └── oauth-*.ts         # OAuth authentication handlers
│       ├── server.js              # Node.js production server
│       ├── Dockerfile             # Multi-stage container build
│       └── wrangler.toml          # Cloudflare Workers config
├── 📦 packages/                    # Shared Libraries
│   ├── mcp-core/                  # Core MCP utilities
│   │   ├── src/tool-base.ts       # Base class for MCP tools
│   │   └── src/openapi-generator.ts # Auto-generate API docs
│   ├── algorand-clients/          # Algorand SDK wrappers
│   │   ├── src/algod-client.ts    # Algod client with retries
│   │   └── src/indexer-client.ts  # Indexer client with caching
│   ├── config/                    # Configuration management
│   │   ├── src/network.ts         # Network configurations
│   │   └── src/loader.ts          # Environment-based config
│   └── types/                     # TypeScript definitions
├── ☸️ environments/                # Kubernetes Infrastructure
│   ├── charts/mcp-server/         # Helm chart for MCP workers
│   │   ├── templates/             # K8s resource templates
│   │   └── values.yaml            # Default configuration
│   ├── development/               # Dev environment overrides
│   ├── staging/                   # Staging environment overrides
│   ├── production/                # Production environment overrides
│   ├── deploy.sh                  # 🚀 Automated deployment script
│   └── validate.sh                # ✅ Configuration validation
├── 🔧 scripts/                     # Development & Operations
│   ├── dev-setup.sh               # Local development setup
│   ├── build-docker.sh            # Docker build automation
│   └── test-containers.sh         # Container testing
├── 📚 docs/                        # Documentation
│   ├── DOCKER.md                  # Docker deployment guide
│   └── K8S_SCOPE.md               # Kubernetes implementation
├── 🐳 docker-compose.yml           # Local development orchestration
├── 📋 Makefile                     # Build and deployment automation
└── 🔒 .github/                     # CI/CD and community templates
    ├── workflows/                 # GitHub Actions
    └── ISSUE_TEMPLATE/            # Issue templates
```
## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|-----------|
| `ALGOD_ADDR` | Algorand node API endpoint | `https://testnet-api.algonode.cloud` | No |
| `ALGOD_TOKEN` | Algorand node API token | `""` | No |
| `INDEXER_URL` | Algorand indexer endpoint | `https://testnet-idx.algonode.cloud` | No |
| `NFD_API_URL` | NFD (Name Service) API | `https://api.nf.domains` | No |
| `NETWORK` | Network type | `testnet` | No |
| `LOG_LEVEL` | Logging level | `info` | No |
| `RATE_LIMIT_REQUESTS` | Rate limit per minute | `100` | No |
| `ENABLE_CORS` | Enable CORS headers | `true` | No |

### Network Configurations

The system supports multiple Algorand networks with automatic endpoint selection:

```typescript
// Testnet (default)
ALGOD_ADDR=https://testnet-api.algonode.cloud
INDEXER_URL=https://testnet-idx.algonode.cloud

// Mainnet
ALGOD_ADDR=https://mainnet-api.algonode.cloud
INDEXER_URL=https://mainnet-idx.algonode.cloud

// Local development
ALGOD_ADDR=http://localhost:4001
INDEXER_URL=http://localhost:8980
```

## 🔍 Use Cases & Examples

### 1. AI Agent Transaction Building
```python
# Claude AI Agent using MCP
import mcp

# Build a payment transaction
response = await mcp.call_tool("build_payment", {
    "sender": "SENDER_ADDRESS",
    "receiver": "RECEIVER_ADDRESS",
    "amount": 1000000,
    "note": "AI-generated payment"
})
```

### 2. Portfolio Management
```bash
# Get account portfolio
curl -X POST http://localhost:8789/api/account \
  -d '{"address": "PORTFOLIO_ADDRESS"}' | \
  jq '.assets[] | select(.amount > 0)'
```

### 3. Transaction Monitoring
```javascript
// Real-time transaction updates via SSE
const events = new EventSource('/api/transactions/stream?account=ADDRESS');
events.onmessage = (event) => {
    const transaction = JSON.parse(event.data);
    console.log('New transaction:', transaction);
};
```

### 4. Multi-signature Workflows
```bash
# Build multi-sig transaction
curl -X POST http://localhost:8788/tools/build_payment \
  -d '{
    "sender": "MULTISIG_ADDRESS",
    "receiver": "RECEIVER_ADDRESS",
    "amount": 5000000,
    "multisig": {
      "version": 1,
      "threshold": 2,
      "addresses": ["ADDR1", "ADDR2", "ADDR3"]
    }
  }'
```

## 🚀 Production Deployment

### Kubernetes Production Checklist

- [ ] **Environment Validation**: Run `./environments/validate.sh`
- [ ] **Resource Limits**: Configure appropriate CPU/memory limits
- [ ] **Monitoring**: Deploy Prometheus and Grafana dashboards
- [ ] **Security**: Enable NetworkPolicies and Pod Security Standards
- [ ] **Backup**: Configure persistent volume backups
- [ ] **Scaling**: Set up HorizontalPodAutoscaler
- [ ] **SSL/TLS**: Configure Let's Encrypt or custom certificates
- [ ] **Logging**: Deploy centralized logging (ELK/Fluentd)

### Cloudflare Workers Production

- [ ] **Custom Domain**: Configure custom domain routing
- [ ] **Rate Limiting**: Set appropriate rate limits
- [ ] **Environment Variables**: Configure production secrets
- [ ] **Analytics**: Enable Cloudflare Analytics
- [ ] **Caching**: Configure cache headers
- [ ] **KV Storage**: Set up KV for session management

## 🤝 Contributing

We welcome contributions from developers of all skill levels! Whether you're fixing bugs, adding features, improving documentation, or helping with community support, your contributions make this project better.

### Ways to Contribute

🐛 **Report Bugs** - Found an issue? [Create a bug report](https://github.com/ByteQuester/algorand-showcase/issues/new?template=bug_report.yml)
✨ **Suggest Features** - Have an idea? [Submit a feature request](https://github.com/ByteQuester/algorand-showcase/issues/new?template=feature_request.yml)
📖 **Improve Docs** - Help make our documentation clearer and more comprehensive
💻 **Write Code** - Fix bugs, implement features, or improve performance
🧪 **Write Tests** - Help us maintain quality with better test coverage
🎯 **Review PRs** - Help review pull requests and provide feedback

### Quick Start for Contributors

1. **Fork** the repository and **star** it ⭐
2. **Clone** your fork: `git clone https://github.com/your-username/algorand-showcase.git`
3. **Install** dependencies: `pnpm install`
4. **Create** a feature branch: `git checkout -b feature/amazing-feature`
5. **Make** your changes and **test** them: `pnpm test`
6. **Submit** a Pull Request with a clear description

**First time contributing?** Look for issues labeled [`good first issue`](https://github.com/ByteQuester/algorand-showcase/labels/good%20first%20issue) to get started!

📚 **Read our [Contributing Guide](CONTRIBUTING.md)** for detailed guidelines, coding standards, and development setup.

### Development Commands

```bash
# Install dependencies
pnpm install

# Build all packages
pnpm build

# Run tests
pnpm test

# Lint code
pnpm lint

# Type checking
pnpm typecheck

# Local development
make dev

# Docker development
make docker-up
```

## 📊 Monitoring & Observability

### Health Checks
- **Actions Worker**: `GET /health` - Transaction service status
- **Remote Worker**: `GET /health` - Blockchain data service status

### Metrics (Prometheus)
- **Request latency**: `http_request_duration_seconds`
- **Request count**: `http_requests_total`
- **Error rate**: `http_requests_errors_total`
- **Algorand API calls**: `algorand_api_calls_total`

### Logging
All services use structured JSON logging with configurable levels:
- `ERROR`: Critical errors requiring immediate attention
- `WARN`: Important issues that don't stop operation
- `INFO`: General operational information
- `DEBUG`: Detailed debugging information (development only)

## 🛡️ Security

### Security Features
- **Rate Limiting**: Configurable per-endpoint rate limiting
- **Input Validation**: Comprehensive request validation
- **CORS Protection**: Configurable CORS policies
- **Network Policies**: Kubernetes network segmentation
- **Container Security**: Non-root containers, read-only filesystems

### Vulnerability Reporting
Please report security vulnerabilities to [security@example.com](mailto:security@example.com) or see our [Security Policy](SECURITY.md).

## 🆘 Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Container won't start
docker-compose logs actions-mcp-worker
docker-compose logs remote-mcp-worker

# Port conflicts
docker-compose down && docker-compose up
```

#### Kubernetes Issues
```bash
# Pod status
kubectl get pods -n mcp-workers

# Pod logs
kubectl logs -n mcp-workers deployment/actions-mcp-worker

# Service endpoints
kubectl get endpoints -n mcp-workers
```

#### Algorand Connection Issues
```bash
# Test algod connection
curl -H "X-Algo-API-Token: $ALGOD_TOKEN" $ALGOD_ADDR/v2/status

# Test indexer connection
curl $INDEXER_URL/health
```

## 📚 Additional Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Algorand Developer Documentation](https://developer.algorand.org/)
- [Docker Deployment Guide](docs/DOCKER.md)
- [Kubernetes Implementation](docs/K8S_SCOPE.md)
- [API Documentation](http://localhost:8788/docs) (when running locally)

## 👥 Community

### Join Our Growing Community

We're building a vibrant community of developers, AI researchers, and blockchain enthusiasts who are passionate about bridging AI and blockchain technology.

**🌟 GitHub Community**
- ⭐ [Star the repository](https://github.com/ByteQuester/algorand-showcase) to show your support
- 🔔 [Watch releases](https://github.com/ByteQuester/algorand-showcase/subscription) to stay updated
- 💬 [Join Discussions](https://github.com/ByteQuester/algorand-showcase/discussions) for Q&A and feature ideas
- 🐛 [Report Issues](https://github.com/ByteQuester/algorand-showcase/issues) to help improve the project

**📢 Stay Connected**
- 📰 Follow our [release notes](https://github.com/ByteQuester/algorand-showcase/releases) for updates
- 🎯 Check out [good first issues](https://github.com/ByteQuester/algorand-showcase/labels/good%20first%20issue) to get started contributing
- 📚 Read our [blog posts](https://github.com/ByteQuester/algorand-showcase/wiki) about MCP and Algorand integration

**🤝 Community Guidelines**

We're committed to fostering a welcoming and inclusive community. Please read our:
- 📋 [Code of Conduct](CODE_OF_CONDUCT.md) - Community standards and behavior
- 🔒 [Security Policy](SECURITY.md) - Responsible disclosure and security practices
- 🤝 [Contributing Guide](CONTRIBUTING.md) - How to contribute effectively

### Community Stats

[![GitHub stars](https://img.shields.io/github/stars/ByteQuester/algorand-showcase?style=social)](https://github.com/ByteQuester/algorand-showcase/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ByteQuester/algorand-showcase?style=social)](https://github.com/ByteQuester/algorand-showcase/network)
[![GitHub watchers](https://img.shields.io/github/watchers/ByteQuester/algorand-showcase?style=social)](https://github.com/ByteQuester/algorand-showcase/watchers)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ByteQuester/algorand-showcase&type=Date)](https://star-history.com/#ByteQuester/algorand-showcase&Date)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Algorand Foundation](https://algorand.org/) for the amazing blockchain platform
- [Model Context Protocol](https://modelcontextprotocol.io/) for the AI agent integration standard
- [Cloudflare](https://cloudflare.com/) for the serverless platform
- All contributors who make this project possible

---

<div align="center">
  <p>Made with ❤️ for the Algorand and AI community</p>
  <p>
    <a href="https://github.com/ByteQuester/algorand-showcase">⭐ Star us on GitHub</a> •
    <a href="https://github.com/ByteQuester/algorand-showcase/issues">🐛 Report Issues</a> •
    <a href="https://github.com/ByteQuester/algorand-showcase/discussions">💬 Discussions</a>
  </p>
</div>


