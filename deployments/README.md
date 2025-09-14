# Algorand Showcase - Production Deployments

This directory contains all production deployment configurations, separated cleanly from source code to ensure vendorable, professional software architecture.

## 🏗️ Directory Structure

```
deployments/
├── docker/                     # Docker configurations
│   ├── Dockerfile.*           # Service-specific Dockerfiles
│   └── docker-compose.*.yml   # Compose files for different environments
├── kubernetes/                 # Kubernetes manifests
│   ├── namespace.yaml         # K8s namespace
│   └── *.yaml                # Service deployments, ConfigMaps, Secrets
├── production/                 # Production-specific configurations
│   ├── configs/               # Application configurations
│   │   ├── *.py              # Production config modules
│   │   ├── nginx.conf        # Reverse proxy configuration
│   │   └── init.sql          # Database initialization
│   ├── monitoring/           # Monitoring and alerting
│   │   ├── prometheus.yml    # Metrics collection
│   │   └── alerts/           # Alert rules
│   └── secrets/              # SSL certificates, keys (gitignored)
└── scripts/                   # Deployment automation
    ├── start-production.sh   # Main production startup
    └── deploy-production.sh  # Full deployment script
```

## 🚀 Quick Start

### 1. Configure Production Environment

```bash
# Copy environment template
cp production/configs/.env.production.template production/configs/.env.production

# Edit with your production values
vim production/configs/.env.production
```

### 2. Start Production Services

```bash
# Start all production services
./scripts/start-production.sh

# Or with verification
./scripts/start-production.sh --verify
```

### 3. Monitor Services

```bash
# View service status
docker compose -f docker/docker-compose.production.yml ps

# View logs
docker compose -f docker/docker-compose.production.yml logs -f [service]
```

## 🐳 Docker Deployment

### Production Stack

```bash
cd deployments/docker
docker compose -f docker-compose.production.yml up -d
```

### Development/Testing

```bash
cd deployments/docker
docker compose -f docker-compose.yml up -d
```

## ☸️ Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Deploy PostgreSQL
kubectl apply -f kubernetes/postgres.yaml

# Deploy application services
kubectl apply -f kubernetes/
```

## 🔧 Configuration Management

### Environment Variables

Production configurations are loaded via:
- `production/configs/.env.production` - Main environment file
- `production/configs/environment_loader.py` - Configuration loader
- `production/configs/production_config.py` - Application config

### Database Setup

- Database schema: `production/configs/init.sql`
- Automatic initialization on first run
- Monitoring tables and views included

### Monitoring

- Prometheus metrics: `production/monitoring/prometheus.yml`
- Alert rules: `production/monitoring/alerts/`
- Log aggregation: Structured logging to `/var/log/lending-api`

## 🔐 Security

### SSL/TLS Configuration

```bash
# Place certificates in:
production/secrets/ssl/cert.pem
production/secrets/ssl/key.pem
```

### Secrets Management

- Environment variables for sensitive data
- Docker secrets support
- Kubernetes secrets integration

## 📊 Service Architecture

```
Internet
    ↓
[Nginx Reverse Proxy] :80/443
    ↓
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Lending API     │  │ Remote MCP      │  │ Actions MCP     │
│ :8003           │  │ :8002           │  │ :3001           │
└─────────────────┘  └─────────────────┘  └─────────────────┘
    ↓                    ↓                    ↓
[PostgreSQL Database] :5432
```

## 🎯 Production Checklist

### Before Deployment

- [ ] Configure `.env.production` with real values
- [ ] Generate secure JWT secrets
- [ ] Set up SSL certificates
- [ ] Configure database credentials
- [ ] Set up monitoring endpoints

### After Deployment

- [ ] Verify all services are healthy
- [ ] Check database connectivity
- [ ] Test API endpoints
- [ ] Verify log aggregation
- [ ] Monitor resource usage

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**: Check environment variables in `.env.production`
2. **Database connection failed**: Verify PostgreSQL service is running
3. **API not responding**: Check Docker container logs
4. **SSL errors**: Ensure certificates are in `production/secrets/ssl/`

### Debugging Commands

```bash
# Check service health
curl http://localhost:8003/health

# View service logs
docker compose -f docker-compose.production.yml logs lending-api

# Connect to database
docker compose -f docker-compose.production.yml exec postgres psql -U username -d algorand_lending

# Check resource usage
docker stats
```

## 📈 Monitoring and Metrics

### Health Endpoints

- Lending API: `http://localhost:8003/health`
- Remote MCP: `http://localhost:8002/health`
- Actions MCP: `http://localhost:3001/health`

### Log Files

- Application logs: `production/monitoring/app.log`
- Security events: `production/monitoring/security.log`
- Audit trail: `production/monitoring/audit.log`

### Performance Monitoring

- Response time tracking
- Database query performance
- Error rate monitoring
- Resource utilization alerts

---

## 🏆 Clean Architecture Benefits

This deployment structure ensures:

✅ **Vendorable Codebase**: Source code contains only business logic
✅ **Production Ready**: Complete deployment automation
✅ **Security Focused**: Separated secrets and configurations
✅ **Monitoring Built-in**: Comprehensive observability
✅ **Scalable Design**: Docker and Kubernetes support
✅ **Professional Grade**: Industry-standard practices

The clean separation between source code (`/apps/`) and deployment (`/deployments/`) enables professional software distribution and enterprise deployment scenarios.