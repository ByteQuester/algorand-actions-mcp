# MCP Services Production Deployment Guide

## Overview

This guide covers deploying the Algorand MCP services to production environments. The services are designed for hosting-monorepo integration with standardized Docker configurations.

## Prerequisites

### System Requirements
- **Node.js**: 20.x LTS
- **pnpm**: 8.x or higher
- **Docker**: 24.x or higher
- **Docker Compose**: 2.x or higher

### Network Access
- Outbound HTTPS to Algorand node endpoints
- Outbound HTTPS to external APIs (NFD, Pera Wallet)
- Inbound HTTP/HTTPS on service ports

## Service Architecture

### Algorand Reader MCP Service
- **Purpose**: Read-only blockchain data access and MCP protocol serving
- **Port**: 8080
- **Network**: Mainnet (production) / Testnet (development)
- **Security**: OAuth integration, rate limiting

### Algorand Writer MCP Service
- **Purpose**: Transaction building, simulation, and submission
- **Port**: 8080
- **Network**: Testnet (default) / Mainnet (with ALLOW_MAINNET=true)
- **Security**: Transaction limits, confirmation requirements

## Configuration

### Environment Variables

Each service uses environment-based configuration:

```bash
# Copy and customize environment files
cp apps/mcp-services/algorand-reader-mcp/.env.example .env.reader
cp apps/mcp-services/algorand-writer-mcp/.env.example .env.writer
```

### Required Production Variables

#### Reader Service (Minimum)
```bash
NODE_ENV=production
ALGORAND_NETWORK=mainnet
ALGORAND_ALGOD=https://mainnet-api.algonode.cloud
ALGORAND_INDEXER=https://mainnet-idx.algonode.cloud
READ_ONLY=true
LOG_LEVEL=warn
```

#### Writer Service (Minimum)
```bash
NODE_ENV=production
ALGORAND_NETWORK=testnet  # or mainnet with ALLOW_MAINNET=true
ALGORAND_ALGOD=https://testnet-api.algonode.cloud
ALGORAND_INDEXER=https://testnet-idx.algonode.cloud
READ_ONLY=false
ALLOW_MAINNET=false  # Set to true for mainnet operations
MAX_TRANSACTION_AMOUNT=10000000000
```

### Optional OAuth Configuration (Reader Service)
```bash
# For full OAuth capabilities
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
HCV_WORKER_URL=your_vault_worker_url
VAULT_OIDC_ACCESSOR=your_vault_accessor
```

## Docker Deployment

### Build Production Images

```bash
# Build reader service
docker build -f apps/mcp-services/algorand-reader-mcp/Dockerfile \
  -t algorand-reader-mcp:latest .

# Build writer service
docker build -f apps/mcp-services/algorand-writer-mcp/Dockerfile \
  -t algorand-writer-mcp:latest .
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  algorand-reader-mcp:
    image: algorand-reader-mcp:latest
    ports:
      - "8080:8080"
    env_file:
      - .env.reader
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: false
    tmpfs:
      - /app/tmp:size=100M,noexec,nosuid,nodev

  algorand-writer-mcp:
    image: algorand-writer-mcp:latest
    ports:
      - "8081:8080"
    env_file:
      - .env.writer
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: false
    tmpfs:
      - /app/tmp:size=100M,noexec,nosuid,nodev
```

### Start Services

```bash
docker-compose up -d
```

## Kubernetes Deployment

### ConfigMaps and Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: algorand-reader-config
data:
  NODE_ENV: "production"
  ALGORAND_NETWORK: "mainnet"
  ALGORAND_ALGOD: "https://mainnet-api.algonode.cloud"
  ALGORAND_INDEXER: "https://mainnet-idx.algonode.cloud"
  READ_ONLY: "true"
  LOG_LEVEL: "warn"

---
apiVersion: v1
kind: Secret
metadata:
  name: algorand-reader-secrets
type: Opaque
data:
  GOOGLE_CLIENT_SECRET: <base64-encoded-secret>
  VAULT_OIDC_ACCESSOR: <base64-encoded-secret>
```

### Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: algorand-reader-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: algorand-reader-mcp
  template:
    metadata:
      labels:
        app: algorand-reader-mcp
    spec:
      containers:
      - name: algorand-reader-mcp
        image: algorand-reader-mcp:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: algorand-reader-config
        - secretRef:
            name: algorand-reader-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
```

### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: algorand-reader-mcp-service
spec:
  selector:
    app: algorand-reader-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

## Health Monitoring

### Health Check Endpoints

Both services expose health check endpoints:

- **Reader**: `GET /health`
- **Writer**: `GET /health`

### Monitoring Metrics

Production deployments should monitor:

- **HTTP Response Times**: P50, P95, P99 latencies
- **Error Rates**: 4xx and 5xx response rates
- **Algorand Node Connectivity**: Connection success rates
- **Memory Usage**: Heap and process memory
- **CPU Usage**: Process CPU utilization

### Alerting

Configure alerts for:

- Health check failures (3+ consecutive failures)
- High error rates (>5% over 5 minutes)
- Algorand node connectivity issues
- High response times (P95 > 2 seconds)
- Memory usage >80% of limit

## Security Configuration

### Network Security

```bash
# Firewall rules (iptables example)
# Allow inbound on service ports
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 8081 -j ACCEPT

# Allow outbound HTTPS to Algorand nodes
iptables -A OUTPUT -p tcp --dport 443 -d mainnet-api.algonode.cloud -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d mainnet-idx.algonode.cloud -j ACCEPT
```

### Container Security

- Services run as non-root user (UID 1001)
- Read-only root filesystem where possible
- Minimal attack surface with Alpine Linux base
- No unnecessary privileges

### Secrets Management

- Use environment variables for configuration
- Store secrets in secure secret management systems
- Rotate OAuth credentials regularly
- Monitor for credential exposure

## Performance Tuning

### Node.js Optimization

```bash
# Environment variables for production
NODE_ENV=production
NODE_OPTIONS="--max-old-space-size=512 --optimize-for-size"
```

### Resource Allocation

#### Recommended Resources
- **CPU**: 250m requests, 500m limits
- **Memory**: 256Mi requests, 512Mi limits
- **Storage**: Ephemeral only, no persistent storage needed

#### Scaling
- **Reader Service**: Can scale horizontally (stateless)
- **Writer Service**: Can scale horizontally (stateless)
- **Load Balancing**: Round-robin or least-connections

## Troubleshooting

### Common Issues

#### Service Won't Start
1. Check environment variable configuration
2. Verify Algorand node connectivity
3. Check Docker image build logs
4. Verify shared package dependencies

#### High Response Times
1. Check Algorand node performance
2. Monitor memory usage
3. Check for rate limiting
4. Verify network connectivity

#### Authentication Failures (Reader Service)
1. Verify OAuth client credentials
2. Check Vault worker connectivity
3. Validate KV namespace access
4. Check CORS configuration

### Debug Mode

For troubleshooting, temporarily enable debug logging:

```bash
# Add to environment
LOG_LEVEL=debug
DEVELOPMENT_MODE=true  # For non-production environments only
```

## Backup and Recovery

### Configuration Backup
- Environment files and configurations
- OAuth client credentials
- Vault accessor tokens

### Data Recovery
- Services are stateless
- No persistent data storage
- Recovery is redeployment with proper configuration

## Compliance and Auditing

### Logging
- All requests are logged with request IDs
- OAuth flows are audited
- Transaction attempts are logged (writer service)

### Data Privacy
- No persistent user data storage
- OAuth tokens are temporary and encrypted
- All data processing is ephemeral

## Support and Maintenance

### Regular Maintenance
- Update base images monthly
- Rotate OAuth credentials quarterly
- Monitor Algorand node endpoints for changes
- Review and update rate limits

### Version Updates
- Services follow semantic versioning
- Test in staging environment first
- Rolling deployments for zero-downtime updates
- Rollback procedures for failed deployments