# Helm Chart Environments

This directory contains Helm chart configuration for deploying Algorand MCP Workers across different environments.

## 📁 Directory Structure

```
environments/
├── charts/
│   └── mcp-server/                 # Shared Helm chart
│       ├── Chart.yaml              # Chart metadata
│       ├── values.yaml             # Default values
│       └── templates/              # Kubernetes templates
│           ├── deployment.yaml     # Pod deployment
│           ├── service.yaml        # Service configuration
│           ├── ingress.yaml        # Ingress rules
│           ├── configmap.yaml      # Configuration data
│           ├── secret.yaml         # Sensitive data
│           ├── hpa.yaml           # Horizontal Pod Autoscaler
│           ├── poddisruptionbudget.yaml # Pod disruption budget
│           ├── serviceaccount.yaml # Service account
│           ├── servicemonitor.yaml # Prometheus monitoring
│           ├── networkpolicy.yaml  # Network policies
│           └── _helpers.tpl        # Template helpers
├── development/                    # Development environment
│   ├── actions-mcp-values.yaml    # Actions worker dev config
│   └── remote-mcp-values.yaml     # Remote worker dev config
├── staging/                        # Staging environment
│   ├── actions-mcp-values.yaml    # Actions worker staging config
│   └── remote-mcp-values.yaml     # Remote worker staging config
└── production/                     # Production environment
    ├── actions-mcp-values.yaml    # Actions worker prod config
    └── remote-mcp-values.yaml     # Remote worker prod config
```

## 🚀 Quick Deployment

### Prerequisites
```bash
# Install Helm 3.x
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Add required repositories
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add cert-manager https://charts.jetstack.io
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
```

### Deploy Development Environment
```bash
# Actions MCP Worker
helm install actions-mcp-dev ./charts/mcp-server \
  -f development/actions-mcp-values.yaml \
  --namespace algorand-mcp-dev \
  --create-namespace

# Remote MCP Worker
helm install remote-mcp-dev ./charts/mcp-server \
  -f development/remote-mcp-values.yaml \
  --namespace algorand-mcp-dev
```

### Deploy Staging Environment
```bash
# Actions MCP Worker
helm install actions-mcp-staging ./charts/mcp-server \
  -f staging/actions-mcp-values.yaml \
  --namespace algorand-mcp-staging \
  --create-namespace

# Remote MCP Worker
helm install remote-mcp-staging ./charts/mcp-server \
  -f staging/remote-mcp-values.yaml \
  --namespace algorand-mcp-staging
```

### Deploy Production Environment
```bash
# Actions MCP Worker
helm install actions-mcp-prod ./charts/mcp-server \
  -f production/actions-mcp-values.yaml \
  --namespace algorand-mcp-prod \
  --create-namespace

# Remote MCP Worker
helm install remote-mcp-prod ./charts/mcp-server \
  -f production/remote-mcp-values.yaml \
  --namespace algorand-mcp-prod
```

## 🔧 Environment Configurations

### Development
- **Replicas**: 1
- **Resources**: Low (50m CPU, 64Mi RAM)
- **Logging**: Debug level with pretty formatting
- **Probes**: Relaxed timeouts
- **Ingress**: Local domains (.local)
- **Autoscaling**: Disabled
- **Security**: Minimal restrictions

### Staging
- **Replicas**: 2
- **Resources**: Moderate (100m CPU, 128Mi RAM)
- **Logging**: Info level with JSON formatting
- **Probes**: Production-like settings
- **Ingress**: Staging domains with TLS
- **Autoscaling**: Enabled (2-5 replicas)
- **Security**: Network policies enabled

### Production
- **Replicas**: 3+
- **Resources**: High (250m CPU, 256Mi RAM)
- **Logging**: Warn level with JSON formatting
- **Probes**: Strict timeouts and health checks
- **Ingress**: Production domains with strict TLS
- **Autoscaling**: Aggressive (3-10/12 replicas)
- **Security**: Full network policies, strict security context

## 🛠️ Customization

### Override Values
```bash
# Custom values file
helm install my-release ./charts/mcp-server \
  -f development/actions-mcp-values.yaml \
  -f my-custom-values.yaml

# Command line overrides
helm install my-release ./charts/mcp-server \
  -f development/actions-mcp-values.yaml \
  --set replicaCount=2 \
  --set image.tag=v1.2.3
```

### Environment Variables
```bash
# Set secrets via command line
helm install my-release ./charts/mcp-server \
  -f development/actions-mcp-values.yaml \
  --set secret.ALGORAND_TOKEN="your-token"
```

## 📊 Monitoring

### Prometheus Integration
All environments include ServiceMonitor resources for Prometheus:

```yaml
serviceMonitor:
  enabled: true
  interval: 30s
  path: /metrics
```

### Available Metrics Endpoints
- Actions MCP: `/metrics`
- Remote MCP: `/metrics`
- Health checks: `/health`

## 🔒 Security

### Network Policies
Production and staging environments include NetworkPolicy resources:

```yaml
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
```

### Pod Security Standards
All environments use strict security contexts:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

## 🔄 Updates and Rollbacks

### Update Deployment
```bash
# Upgrade with new values
helm upgrade actions-mcp-dev ./charts/mcp-server \
  -f development/actions-mcp-values.yaml

# Update image tag
helm upgrade actions-mcp-dev ./charts/mcp-server \
  -f development/actions-mcp-values.yaml \
  --set image.tag=v1.2.3
```

### Rollback
```bash
# View release history
helm history actions-mcp-dev

# Rollback to previous version
helm rollback actions-mcp-dev 1
```

## 🧪 Testing

### Validate Configuration
```bash
# Dry run deployment
helm install actions-mcp-test ./charts/mcp-server \
  -f development/actions-mcp-values.yaml \
  --dry-run --debug

# Template rendering
helm template actions-mcp-test ./charts/mcp-server \
  -f development/actions-mcp-values.yaml
```

### Health Checks
```bash
# Check pod status
kubectl get pods -n algorand-mcp-dev

# Check service endpoints
kubectl get svc -n algorand-mcp-dev

# Test health endpoint
kubectl port-forward svc/actions-mcp-dev 8080:80 -n algorand-mcp-dev
curl http://localhost:8080/health
```

## 📚 Additional Resources

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Algorand MCP Documentation](../docs/)
- [Monitoring Setup](../monitoring/)

## 🆘 Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   ```

2. **Failed Health Checks**
   ```bash
   kubectl logs <pod-name> -n <namespace>
   ```

3. **Ingress Issues**
   ```bash
   kubectl describe ingress <ingress-name> -n <namespace>
   ```

4. **Resource Limits**
   ```bash
   kubectl top pods -n <namespace>
   kubectl describe node <node-name>
   ```

### Support
For issues and questions:
- GitHub Issues: [Repository Issues](https://github.com/username/algorand-showcase/issues)
- Documentation: [K8s Deployment Guide](../docs/K8S.md)
- Monitoring: [Monitoring Guide](../docs/MONITORING.md)