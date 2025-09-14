# 🚀 Algorand Lending Platform - Production Deployment Guide

**Version:** 1.0.0
**Last Updated:** 2025-09-14
**Target Environment:** Production Cloud Infrastructure

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Deployment](#detailed-deployment)
5. [Service Management](#service-management)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Security Configuration](#security-configuration)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## 🎯 Overview

The Algorand Lending Platform is a production-ready A2A (Agent-to-Agent) lending system built on the Algorand blockchain. This deployment guide covers:

- **Frontend**: ADK-Web UI (Angular) - Lending-focused interface
- **API**: FastAPI-based lending service with JWT authentication
- **Blockchain**: MCP services for Algorand testnet integration
- **Database**: PostgreSQL with Redis caching
- **Monitoring**: Prometheus, Grafana, AlertManager
- **Infrastructure**: Docker, Nginx, systemd services

### System Architecture

```
Internet → Nginx → ADK-Web (8081) → Lending API (8003) → MCP Services (8002/8788) → Algorand Testnet
              ↓                         ↓                      ↓
          SSL/TLS                  PostgreSQL              Redis Cache
                                     ↓
                              Prometheus/Grafana
```

## 🔧 Prerequisites

### Server Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 100 GB SSD | 200 GB NVMe SSD |
| Network | 1 Gbps | 10 Gbps |

### Software Dependencies

```bash
# Required packages
- Docker CE 20.10+
- Docker Compose 2.0+
- Nginx 1.18+
- Certbot (Let's Encrypt)
- UFW (Uncomplicated Firewall)
- Fail2ban
- Git
```

### Network Requirements

| Port | Service | Access | Purpose |
|------|---------|---------|---------|
| 80 | HTTP | Public | Redirect to HTTPS |
| 443 | HTTPS | Public | Main application |
| 22 | SSH | Restricted | Server management |
| 8002 | Remote MCP | Internal | Blockchain queries |
| 8003 | Lending API | Internal | Business logic |
| 8081 | ADK-Web | Internal | Frontend service |
| 8788 | Actions MCP | Internal | Transaction submission |
| 3000 | Grafana | Internal | Monitoring dashboard |
| 9090 | Prometheus | Internal | Metrics collection |
| 9093 | AlertManager | Internal | Alert routing |

### Domain Requirements

- Primary domain: `lending.yourdomain.com`
- API subdomain: `api.lending.yourdomain.com`
- Valid SSL certificate (Let's Encrypt recommended)

## ⚡ Quick Start

For experienced operators who want to get up and running quickly:

```bash
# 1. Clone repository
git clone https://github.com/your-org/algorand-showcase.git
cd algorand-showcase

# 2. Generate secrets and configure
sudo ./scripts/generate-secrets.sh
sudo nano .env.production  # Update domain and settings

# 3. Deploy everything
sudo ./deploy-production.sh

# 4. Install systemd services
sudo ./scripts/install-systemd-services.sh

# 5. Set up monitoring
sudo ./scripts/setup-monitoring.sh

# 6. Start services
sudo algorand-lending start

# 7. Check status
sudo algorand-lending status
sudo algorand-lending health
```

## 🔍 Detailed Deployment

### Step 1: Server Preparation

#### 1.1 Update System
```bash
# Update package lists and system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

#### 1.2 Install Docker
```bash
# Install Docker CE
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 1.3 Install Nginx and Certbot
```bash
# Install Nginx and SSL tools
sudo apt install -y nginx certbot python3-certbot-nginx

# Enable Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 1.4 Configure Firewall
```bash
# Install and configure UFW
sudo apt install -y ufw fail2ban

# Configure firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Step 2: Application Deployment

#### 2.1 Download and Prepare
```bash
# Create deployment directory
sudo mkdir -p /opt/algorand-lending
cd /opt/algorand-lending

# Clone repository (or upload your code)
git clone https://github.com/your-org/algorand-showcase.git .

# Set permissions
sudo chown -R $USER:$USER /opt/algorand-lending
chmod +x scripts/*.sh
chmod +x deploy-production.sh
```

#### 2.2 Generate Production Configuration
```bash
# Generate secure secrets and environment
sudo ./scripts/generate-secrets.sh

# This script will:
# - Generate secure random secrets
# - Prompt for domain configuration
# - Create .env.production file
# - Set up secrets directory
```

#### 2.3 Customize Configuration
```bash
# Review and update production environment
sudo nano .env.production

# Key settings to verify:
# - DOMAIN=lending.yourdomain.com
# - API_DOMAIN=api.lending.yourdomain.com
# - SSL_EMAIL=admin@yourdomain.com
# - Database passwords
# - JWT secrets
# - Notification settings
```

#### 2.4 Deploy Services
```bash
# Run the main deployment script
sudo ./deploy-production.sh

# This will:
# - Create Docker containers
# - Set up reverse proxy
# - Configure SSL certificates
# - Create backup scripts
# - Set up monitoring stack
```

### Step 3: Service Management Setup

#### 3.1 Install systemd Services
```bash
# Install and enable systemd services
sudo ./scripts/install-systemd-services.sh

# This creates:
# - algorand-lending.service (main stack)
# - algorand-adk-web.service (frontend)
# - algorand-lending-api.service (API)
# - algorand-actions-mcp.service (blockchain actions)
# - algorand-remote-mcp.service (blockchain queries)
# - algorand-lending-stack.target (grouped services)
```

#### 3.2 Start Services
```bash
# Start all services
sudo systemctl start algorand-lending-stack.target

# Enable auto-start on boot
sudo systemctl enable algorand-lending-stack.target

# Check status
sudo systemctl status algorand-lending-stack.target
```

### Step 4: DNS and SSL Configuration

#### 4.1 Configure DNS
Update your DNS provider to point:
- `lending.yourdomain.com` → Your server's IP address
- `api.lending.yourdomain.com` → Your server's IP address

#### 4.2 Obtain SSL Certificates
```bash
# Request SSL certificates
sudo certbot --nginx -d lending.yourdomain.com -d api.lending.yourdomain.com

# Verify automatic renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

### Step 5: Monitoring Setup

#### 5.1 Configure Monitoring Stack
```bash
# Set up comprehensive monitoring
sudo ./scripts/setup-monitoring.sh

# Start monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

#### 5.2 Configure Notifications
```bash
# Update Slack webhooks
sudo nano monitoring/alertmanager.yml

# Configure email settings
sudo nano .env.production

# Test notifications
curl -X POST http://localhost:9093/api/v1/alerts -d '[{"labels":{"alertname":"test"}}]'
```

## 🎮 Service Management

### Using the Management Script

The `algorand-lending` command provides easy service management:

```bash
# Start all services
sudo algorand-lending start

# Stop all services
sudo algorand-lending stop

# Restart all services
sudo algorand-lending restart

# Check service status
sudo algorand-lending status

# View logs (all services or specific)
sudo algorand-lending logs
sudo algorand-lending logs lending-api

# Run health checks
sudo algorand-lending health

# Create backups
sudo algorand-lending backup
```

### Individual Service Management

```bash
# Control specific services
sudo systemctl start algorand-lending-api.service
sudo systemctl stop algorand-adk-web.service
sudo systemctl restart algorand-actions-mcp.service

# View service logs
sudo journalctl -u algorand-lending-api.service -f
sudo journalctl -u algorand-lending-stack.target -f

# Check service status
sudo systemctl status algorand-lending-stack.target
```

### Docker Container Management

```bash
# View running containers
docker ps

# View container logs
docker logs algorand-lending-api
docker logs algorand-adk-web -f

# Execute commands in containers
docker exec -it algorand-lending-api bash
docker exec -it algorand-postgres psql -U algorand_user -d algorand_lending

# Restart specific containers
docker restart algorand-lending-api
```

## 📊 Monitoring & Alerting

### Access Monitoring Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | `http://your-server:3000` | admin/`<from .env.production>` |
| Prometheus | `http://your-server:9090` | None |
| AlertManager | `http://your-server:9093` | None |

### Key Dashboards

1. **System Overview**
   - Service status and uptime
   - Request rates and response times
   - Error rates and alerts

2. **Business Metrics**
   - Loan request volume
   - Approval/rejection rates
   - Processing times
   - Transaction success rates

3. **Infrastructure**
   - CPU, memory, disk usage
   - Network I/O
   - Database performance
   - Cache hit rates

### Alert Categories

| Category | Severity | Response Time |
|----------|----------|---------------|
| Service Down | Critical | Immediate |
| High Error Rate | Critical | 5 minutes |
| Security Issues | Critical | Immediate |
| Performance Issues | Warning | 30 minutes |
| Resource Usage | Warning | 1 hour |
| Business Metrics | Info | 4 hours |

### Notification Channels

- **Slack**: Real-time alerts to operations team
- **Email**: Critical alerts and daily summaries
- **PagerDuty**: Critical alerts with escalation (optional)
- **Webhooks**: Integration with external systems

## 🔒 Security Configuration

### Firewall Rules

```bash
# View current rules
sudo ufw status numbered

# Add additional restrictions
sudo ufw allow from 10.0.0.0/8 to any port 3000  # Grafana internal only
sudo ufw allow from 192.168.0.0/16 to any port 9090  # Prometheus internal only

# Block specific IPs (if needed)
sudo ufw deny from 192.168.1.100
```

### SSL/TLS Configuration

The Nginx configuration includes:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS headers
- Security headers (CSP, X-Frame-Options, etc.)
- Certificate auto-renewal

### Secret Management

```bash
# View secret files (restricted access)
sudo ls -la /opt/algorand-lending/secrets/

# Rotate secrets (example)
sudo ./scripts/generate-secrets.sh --rotate

# Check secret permissions
sudo find /opt/algorand-lending/secrets -type f -exec ls -la {} \;
```

### Access Control

- SSH access via key authentication only
- Application services bound to internal networks
- Database access restricted to application containers
- Monitoring dashboards on internal network only

## 💾 Backup & Recovery

### Automated Backup Schedule

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Database | Daily 2 AM | 30 days | Local + Remote |
| Docker Volumes | Weekly Sunday 3 AM | 8 weeks | Local + Remote |
| Configuration | On each deployment | 90 days | Local + Git |
| Logs | Daily rotation | 30 days | Local |

### Manual Backup

```bash
# Create immediate backup
sudo algorand-lending backup

# Database-only backup
sudo /opt/algorand-lending/backup-database.sh

# Volume backup
sudo /opt/algorand-lending/backup-volumes.sh

# List available backups
sudo ls -la /opt/backups/algorand-lending/
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop services
sudo algorand-lending stop

# Restore database
gunzip < /opt/backups/algorand-lending/database/algorand_lending_20250914_020000.sql.gz | docker exec -i algorand-postgres psql -U algorand_user -d algorand_lending

# Start services
sudo algorand-lending start
```

#### Full System Recovery
```bash
# Stop all services
sudo algorand-lending stop

# Restore Docker volumes
cd /opt/backups/algorand-lending/volumes/
tar xzf postgres_data_20250914_030000.tar.gz -C /var/lib/docker/volumes/algorand_lending_postgres_data/_data/

# Restore configuration
cp -r /opt/backups/algorand-lending/config/* /opt/algorand-lending/

# Start services
sudo algorand-lending start

# Verify health
sudo algorand-lending health
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptoms**: Services fail to start or immediately exit
```bash
# Check logs
sudo algorand-lending logs
sudo systemctl status algorand-lending-stack.target

# Common fixes
sudo docker system prune  # Clean up Docker resources
sudo systemctl daemon-reload  # Reload systemd configuration
sudo algorand-lending restart  # Restart all services
```

#### 2. High Response Times

**Symptoms**: Slow API responses, timeouts
```bash
# Check resource usage
htop
docker stats

# Check database performance
docker exec -it algorand-postgres psql -U algorand_user -d algorand_lending -c "SELECT * FROM pg_stat_activity;"

# Common fixes
# - Scale up server resources
# - Optimize database queries
# - Increase connection pool size
# - Add Redis caching
```

#### 3. SSL Certificate Issues

**Symptoms**: SSL warnings, certificate expired
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check Nginx configuration
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Database Connection Issues

**Symptoms**: API can't connect to database
```bash
# Check database status
docker exec algorand-postgres pg_isready -U algorand_user

# Check connection string
grep DATABASE_URL /opt/algorand-lending/.env.production

# Reset database password
docker exec -it algorand-postgres psql -U postgres -c "ALTER USER algorand_user PASSWORD 'new_password';"
```

#### 5. Monitoring Issues

**Symptoms**: Grafana/Prometheus not working
```bash
# Check monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Restart monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml down
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

### Log Analysis

```bash
# View application logs
sudo tail -f /var/log/algorand-lending/lending-api.log

# View system logs
sudo journalctl -f -u algorand-lending-stack.target

# View Docker logs
docker logs algorand-lending-api --tail 100 -f

# View Nginx access/error logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Monitoring

```bash
# System resources
htop
iotop
nethogs

# Docker resource usage
docker stats

# Database performance
docker exec -it algorand-postgres psql -U algorand_user -d algorand_lending -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## 🔄 Maintenance

### Regular Tasks

#### Daily
- Monitor system health and alerts
- Review error logs
- Check backup completion
- Monitor resource usage

#### Weekly
- Review security alerts
- Update system packages
- Rotate log files
- Review performance metrics

#### Monthly
- Update Docker images
- Review and optimize database
- Security audit
- Capacity planning review

#### Quarterly
- Rotate secrets and passwords
- Review access permissions
- Update documentation
- Disaster recovery testing

### Update Procedures

#### Application Updates
```bash
# Pull latest code
git pull origin main

# Backup current state
sudo algorand-lending backup

# Update containers
docker-compose pull
docker-compose up -d

# Run health checks
sudo algorand-lending health
```

#### System Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt update docker-ce docker-ce-cli containerd.io

# Restart if kernel updated
sudo reboot
```

### Performance Optimization

#### Database Optimization
```bash
# Analyze database performance
docker exec -it algorand-postgres psql -U algorand_user -d algorand_lending -c "ANALYZE;"

# Vacuum database
docker exec -it algorand-postgres psql -U algorand_user -d algorand_lending -c "VACUUM;"

# Check for unused indexes
docker exec -it algorand-postgres psql -U algorand_user -d algorand_lending -c "SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats WHERE schemaname = 'public';"
```

#### Container Optimization
```bash
# Clean up unused images and containers
docker system prune -a

# Optimize container resources
# Update docker-compose.yml with resource limits
```

## 📞 Support

### Contact Information

- **Technical Issues**: ops@algorand-lending.com
- **Security Issues**: security@algorand-lending.com
- **Business Issues**: support@algorand-lending.com
- **Emergency**: emergency@algorand-lending.com

### Documentation

- **API Documentation**: Available at `/docs` endpoint when enabled
- **Runbooks**: Available in `/docs/runbooks/` directory
- **Architecture**: See `ARCHITECTURE.md`
- **Contributing**: See `CONTRIBUTING.md`

### Community Resources

- **GitHub Issues**: Report bugs and request features
- **Discord**: Real-time community support
- **Documentation Wiki**: Community-maintained guides

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Server meets minimum requirements
- [ ] Domain DNS configured
- [ ] SSL certificate ready
- [ ] Firewall configured
- [ ] Backup strategy planned

### Deployment
- [ ] Services deployed and running
- [ ] Health checks passing
- [ ] SSL certificates active
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Backups scheduled

### Post-Deployment
- [ ] Performance testing completed
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Disaster recovery tested

### Production Readiness
- [ ] All tests passing
- [ ] Monitoring alerts tuned
- [ ] Performance baselines established
- [ ] Incident response procedures documented
- [ ] Maintenance schedules planned

---

**Version History:**
- v1.0.0: Initial production deployment guide
- Add future versions here...

**Last Reviewed:** 2025-09-14
**Next Review:** 2025-10-14