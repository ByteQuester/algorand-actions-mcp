# Docker Containerization Guide

This guide covers the Docker containerization of both Algorand MCP Workers, enabling production-ready deployments with Kubernetes support.

## 🐳 Container Architecture

### Multi-Stage Build Strategy
Both workers use optimized multi-stage Dockerfiles:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Base Stage    │───▶│  Builder Stage  │───▶│  Runner Stage   │
│                 │    │                 │    │                 │
│ • Node.js 20    │    │ • Install deps  │    │ • Production    │
│ • System deps   │    │ • Build packages│    │ • Non-root user │
│ • pnpm enabled  │    │ • Compile TS    │    │ • Health checks │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Features
- **Security**: Non-root user (`worker:worker`)  
- **Health Checks**: Built-in health monitoring
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT
- **Resource Optimized**: Alpine-based images
- **Multi-platform**: Support for AMD64 and ARM64

## 📦 Available Images

### Actions MCP Worker
```bash
# Build locally
docker build -f apps/blockchain/algorand-actions-mcp/Dockerfile -t algorand-actions-mcp .

# Run container
docker run -p 8080:8080 -e ALGORAND_NETWORK=testnet algorand-actions-mcp
```

**Endpoints:**
- Health: `GET /health`
- Metrics: `GET /metrics` 
- Tools: `GET /tools/list`
- Build Payment: `POST /tools/build_payment`
- Simulate: `POST /tools/simulate`
- Submit: `POST /tools/submit`
- Documentation: `GET /docs`

### Remote MCP Worker
```bash
# Build locally  
docker build -f apps/blockchain/algorand-remote-mcp/Dockerfile -t algorand-remote-mcp .

# Run container
docker run -p 8080:8080 -e ALGORAND_NETWORK=mainnet algorand-remote-mcp
```

**Endpoints:**
- Health: `GET /health`
- Metrics: `GET /metrics`
- Tools: `GET /tools/list`
- Account Info: `POST /api/account`
- Transaction: `POST /api/transaction`
- Asset Info: `POST /api/asset`
- Block Info: `POST /api/block`
- Search Transactions: `POST /api/search/transactions`
- Documentation: `GET /docs`

## 🚀 Quick Start

### Option 1: Using Make (Recommended)
```bash
# Complete setup and start
make quick-start

# Or step by step
make install
make build  
make docker-build
make docker-up
```

### Option 2: Using Scripts
```bash
# Development setup
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh

# Start services
docker-compose up
```

### Option 3: Manual Docker Compose
```bash
# Copy environment template
cp .env.docker .env

# Install dependencies
pnpm install --frozen-lockfile
pnpm --filter "@algorand-showcase/*" run build

# Start containers
docker-compose up -d
```

## ⚙️ Configuration

### Environment Variables

#### Actions MCP Worker
```bash
# Network configuration
ALGORAND_NETWORK=testnet          # "testnet" or "mainnet"
ALGORAND_ALGOD=                   # Custom Algod URL (optional)
ALGORAND_TOKEN=                   # API token (optional)
READ_ONLY=false                   # Disable transaction operations

# Container settings
NODE_ENV=production
PORT=8080
```

#### Remote MCP Worker
```bash
# Network configuration  
ALGORAND_NETWORK=mainnet          # "testnet" or "mainnet"
ALGORAND_ALGOD=                   # Custom Algod URL (optional)
ALGORAND_INDEXER=                 # Custom Indexer URL (optional)
ALGORAND_TOKEN=                   # API token (optional)
READ_ONLY=true                    # Disable wallet operations

# OAuth settings (for full mode)
HCV_WORKER=                       # HashiCorp Vault Worker
HCV_WORKER_URL=                   # Vault Worker URL
VAULT_ENTITIES=                   # Vault entities
VAULT_OIDC_ACCESSOR=              # OIDC accessor
GOOGLE_CLIENT_ID=                 # Google OAuth client ID
GOOGLE_CLIENT_SECRET=             # Google OAuth secret
COOKIE_ENCRYPTION_KEY=            # Cookie encryption key

# Container settings
NODE_ENV=production
PORT=8080
```

## 🔧 Docker Compose Profiles

### Default Profile
```bash
docker-compose up
```
Starts both MCP workers.

### Proxy Profile
```bash
docker-compose --profile proxy up
```
Includes Traefik reverse proxy:
- Actions MCP: `http://actions.localhost`
- Remote MCP: `http://remote.localhost`
- Traefik Dashboard: `http://localhost:8080`

### Monitoring Profile
```bash
docker-compose --profile monitoring up
```
Includes monitoring stack:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)

## 🧪 Testing

### Container Health Tests
```bash
# Run comprehensive tests
make docker-test

# Or manually
chmod +x scripts/test-containers.sh
./scripts/test-containers.sh
```

### Manual Health Checks
```bash
# Actions MCP Worker
curl http://localhost:8788/health
curl http://localhost:8788/metrics
curl -X POST -H "Content-Type: application/json" \
  -d '{"fromAddress":"AAAA...","toAddress":"BBBB...","microAlgos":1000}' \
  http://localhost:8788/tools/build_payment

# Remote MCP Worker  
curl http://localhost:8789/health
curl http://localhost:8789/metrics
curl -X POST -H "Content-Type: application/json" \
  -d '{"address":"AAAA..."}' \
  http://localhost:8789/api/account
```

## 🏗️ Build Automation

### GitHub Actions
Automated CI/CD pipeline (`.github/workflows/docker-build.yml`):

1. **Build**: Multi-architecture Docker images (AMD64/ARM64)
2. **Test**: Container functionality and security scanning
3. **Push**: Images to GitHub Container Registry
4. **Deploy**: Automatic staging/production deployment

### Local Build Scripts
```bash
# Production build with testing
scripts/build-docker.sh

# Push to registry
TAG=v1.0.0 PUSH=true DOCKER_REGISTRY=ghcr.io/yourorg scripts/build-docker.sh
```

## 📊 Monitoring & Observability

### Health Checks
Both containers include built-in health checks:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1
```

### Metrics
Prometheus-compatible metrics available at `/metrics`:
```bash
# Example metrics
actions_mcp_up 1
actions_mcp_info{network="testnet",readonly="false"} 1
```

### Logging
Structured JSON logs with request tracing:
```bash
# View logs
docker-compose logs -f actions-mcp
docker-compose logs -f remote-mcp
```

## 🔒 Security Features

### Container Security
- **Non-root execution**: Containers run as `worker` user (UID 1001)
- **Read-only filesystem**: Application code mounted read-only
- **Minimal attack surface**: Alpine-based images with minimal packages
- **No secrets in images**: All secrets via environment variables

### Network Security
- **CORS protection**: Proper CORS headers on all endpoints
- **Input validation**: Zod-based schema validation
- **Rate limiting**: Built-in request throttling
- **Health-only exposure**: Only health endpoints accessible without auth

## 🚀 Production Deployment

### Kubernetes Deployment
```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: algorand-actions-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: algorand-actions-mcp
  template:
    metadata:
      labels:
        app: algorand-actions-mcp
    spec:
      containers:
      - name: actions-mcp
        image: ghcr.io/yourorg/algorand-actions-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: ALGORAND_NETWORK
          value: "testnet"
        - name: READ_ONLY
          value: "false"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Resource Requirements
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi" 
    cpu: "500m"
```

## 🛠️ Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs actions-mcp
docker-compose logs remote-mcp

# Check health
docker inspect algorand-actions-mcp --format='{{.State.Health.Status}}'
```

**Port conflicts:**
```bash
# Use different ports
ACTIONS_PORT=8799 REMOTE_PORT=8798 docker-compose up
```

**Build failures:**
```bash
# Clean and rebuild
make clean-all
make docker-build
```

**Network issues:**
```bash
# Verify network connectivity
docker exec algorand-actions-mcp wget -O- https://testnet-api.algonode.cloud/health
```

### Debug Mode
```bash
# Run with debug logging
docker-compose up -e NODE_ENV=development
```

## 📚 Additional Resources

- [Kubernetes Deployment Guide](./K8S.md)
- [API Documentation](./API.md)
- [Security Best Practices](./SECURITY.md)
- [Performance Tuning](./PERFORMANCE.md)