# Kubernetes Scope

This document outlines the future Kubernetes integration scope for the Algorand Showcase project.

## Overview

The Kubernetes integration will provide an alternative deployment method for MCP servers as HTTP services, complementing the existing Cloudflare Workers deployment.

## **Explicitly Out-of-Scope for Baseline PR**

This document serves as a future reference only. **No Kubernetes implementation will be done in the baseline refactor.**

## Future Architecture

### HTTP Server Adapter

Each MCP server will have an HTTP adapter that wraps the MCP protocol:

```
┌─────────────────┐    HTTP    ┌─────────────────┐    MCP     ┌─────────────────┐
│   Client        │ ────────── │ HTTP Adapter    │ ────────── │ MCP Server Core │
│   (Claude, etc) │            │                 │            │                 │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

**HTTP Adapter Responsibilities**:
- Convert HTTP requests to MCP protocol messages
- Handle authentication and authorization
- Provide OpenAPI/Swagger documentation
- Rate limiting and request validation
- Health checks and metrics endpoints

### Containerization

Each app will have its own Docker configuration:

```
apps/
├── actions-mcp-worker/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── docker-compose.yml (for local development)
└── remote-mcp-worker/
    ├── Dockerfile
    ├── .dockerignore
    └── docker-compose.yml (for local development)
```

**Dockerfile Strategy**:
- Multi-stage builds for optimized production images
- Node.js Alpine base for minimal size
- Non-root user for security
- Health checks and proper signal handling

### Helm Charts

Kubernetes deployments will use Helm for templating and configuration management:

```
environments/
├── charts/
│   └── mcp-server/              # Shared Helm chart
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── ingress.yaml
│           ├── configmap.yaml
│           └── secret.yaml
├── development/
│   ├── actions-mcp-values.yaml
│   └── remote-mcp-values.yaml
├── staging/
│   ├── actions-mcp-values.yaml
│   └── remote-mcp-values.yaml
└── production/
    ├── actions-mcp-values.yaml
    └── remote-mcp-values.yaml
```

### Environment Overlays

Each environment will have specific configurations:

**Development**:
- Single replica
- Resource limits disabled
- Debug logging enabled
- Local storage for testing

**Staging**:
- 2 replicas for availability
- Moderate resource limits
- Info-level logging
- Persistent volumes for data

**Production**:
- 3+ replicas with pod disruption budgets
- Strict resource limits and requests
- Error-level logging only
- High-availability storage

## Deployment Strategy

### GitOps with ArgoCD (Future)
- Automated deployments from Git
- Environment promotion workflows
- Rollback capabilities
- Configuration drift detection

### CI/CD Integration
- Docker image builds in GitHub Actions
- Push to GitHub Container Registry (ghcr.io)
- Automatic deployment to development
- Manual promotion to staging/production

## Configuration Management

### ConfigMaps
- Non-sensitive configuration
- Feature flags
- API endpoints and timeouts
- Logging configuration

### Secrets
- API keys and tokens
- Database credentials
- TLS certificates
- Encryption keys

### External Secrets Operator (Future)
- Integration with cloud secret managers
- Automatic secret rotation
- Audit logging for secret access

## Monitoring and Observability

### Metrics
- Prometheus metrics endpoint on each pod
- Custom business metrics (transaction counts, errors)
- Resource utilization metrics
- MCP protocol metrics

### Logging
- Structured JSON logging
- Centralized log aggregation with Fluentd/Fluent Bit
- Log retention and rotation policies
- Security event logging

### Tracing
- OpenTelemetry integration
- Distributed tracing across services
- Performance monitoring
- Error tracking and alerting

## Security Considerations

### Network Policies
- Restrict pod-to-pod communication
- Ingress/egress traffic controls
- Namespace isolation

### Pod Security Standards
- Non-root containers
- Read-only root filesystem
- No privileged containers
- Resource limits and requests

### RBAC
- Service account per application
- Minimal required permissions
- Regular access reviews

## Service Mesh Integration (Future)

### Istio Features
- Automatic mTLS between services
- Traffic management and routing
- Circuit breakers and retries
- Observability and security policies

## Storage Requirements

### Stateless Design
- MCP servers should be stateless
- External state in databases/cache
- No persistent volumes required for apps

### Caching Layer
- Redis for response caching
- Session storage
- Rate limiting data

## Implementation Phases

### Phase 1: HTTP Adapter
- Build HTTP wrapper for MCP protocol
- Add health checks and metrics
- Create Dockerfile for each app

### Phase 2: Basic Kubernetes
- Helm chart development
- ConfigMap and Secret management
- Service and Ingress configuration

### Phase 3: Production Readiness
- Monitoring and alerting setup
- Security hardening
- Performance optimization

### Phase 4: Advanced Features
- Service mesh integration
- GitOps deployment
- Advanced monitoring and tracing

## Migration Path

1. **Current**: Cloudflare Workers only
2. **Hybrid**: Both Workers and Kubernetes available
3. **Evaluation**: Performance and cost comparison
4. **Decision**: Choose primary deployment method
5. **Optimization**: Focus on chosen platform

## Out of Scope

- **Database operations** - MCP servers remain stateless
- **Complex orchestration** - Simple HTTP services only  
- **Multi-cluster** - Single cluster deployment initially
- **Service mesh** - Basic Kubernetes services first
- **Advanced networking** - Standard ingress controllers