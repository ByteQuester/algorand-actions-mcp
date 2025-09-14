# 🚀 Production Deployment Guide - Algorand Lending Platform

> **Complete guide for deploying the Algorand Lending Platform to production**

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Environment Setup](#environment-setup)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Service Configuration](#service-configuration)
6. [Health Checks](#health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)
9. [Maintenance](#maintenance)

---

## 🔧 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **CPU**: 4 cores minimum, 8 cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 100GB minimum, SSD recommended
- **Network**: Public IP, ports 80/443 accessible

### Software Dependencies

#### Required Software
```bash
# Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Node.js 18+ (for UI components)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.9+ (for API services)
sudo apt-get update
sudo apt-get install -y python3.9 python3.9-pip python3.9-venv

# Nginx (reverse proxy)
sudo apt-get install -y nginx

# PostgreSQL client (for database management)
sudo apt-get install -y postgresql-client
```

#### Optional (for advanced deployments)
```bash
# Kubernetes tools
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Terraform (for infrastructure as code)
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Helm (for Kubernetes)
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update && sudo apt-get install helm
```

---

## 🏗️ Architecture Overview

### Production Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                          Load Balancer                         │
│                         (Nginx/CloudLB)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
│Lending UI │  │Lending API│  │MCP Services│
│  (8081)   │  │  (8003)   │  │(8002/3001)│
└───────────┘  └─────┬─────┘  └─────┬─────┘
                     │              │
               ┌─────▼─────┐  ┌─────▼─────┐
               │PostgreSQL │  │ Algorand  │
               │ Database  │  │ Testnet   │
               └───────────┘  └───────────┘
```

### Service Components
- **Nginx**: Reverse proxy and SSL termination
- **Lending UI**: React-based user interface (port 8081)
- **Lending API**: FastAPI backend service (port 8003)
- **MCP Services**: Algorand blockchain integration (ports 8002/3001)
- **PostgreSQL**: Primary database for loans and users
- **Algorand Testnet**: Blockchain network integration

---

## ⚙️ Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/algorand-showcase.git
cd algorand-showcase
```

### 2. Create Environment Files
```bash
# Create production environment file
cp .env.example .env.production

# Edit production configuration
nano .env.production
```

#### Production Environment Variables
```bash
# .env.production

# Environment
NODE_ENV=production
FLASK_ENV=production
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql://lending_user:secure_password@localhost:5432/lending_db
POSTGRES_USER=lending_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=lending_db

# JWT Configuration
JWT_SECRET_KEY=your_super_secure_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=43200

# Algorand Configuration
ALGORAND_NETWORK=testnet
ALGORAND_ALGOD_URL=https://testnet-api.algonode.cloud
ALGORAND_INDEXER_URL=https://testnet-idx.algonode.cloud

# Service URLs
LENDING_API_URL=https://api.yourdomain.com
LENDING_UI_URL=https://yourdomain.com
MCP_READER_URL=http://localhost:8002
MCP_WRITER_URL=http://localhost:3001

# SSL Configuration
SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here
MONITORING_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
```

### 3. SSL Certificate Setup
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Verify certificate
sudo certbot certificates
```

---

## 🚢 Step-by-Step Deployment

### Phase 1: Database Setup

#### 1. Install and Configure PostgreSQL
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER lending_user WITH PASSWORD 'secure_password';
CREATE DATABASE lending_db OWNER lending_user;
GRANT ALL PRIVILEGES ON DATABASE lending_db TO lending_user;
\q
EOF
```

#### 2. Initialize Database Schema
```bash
# Run database migrations
cd algorand-showcase
python3 -m venv venv-prod
source venv-prod/bin/activate
pip install -r requirements.txt

# Initialize database
python scripts/init-database.py --env production
```

### Phase 2: Service Deployment

#### 1. Deploy MCP Services
```bash
# Build and start MCP services
cd deployments
./scripts/deploy-production.sh --component mcp

# Verify MCP services
curl http://localhost:8002/health
curl http://localhost:3001/health
```

#### 2. Deploy Lending API
```bash
# Deploy API service
./scripts/deploy-production.sh --component api

# Verify API service
curl http://localhost:8003/api/v1/health
```

#### 3. Deploy Lending UI
```bash
# Deploy UI service
./scripts/deploy-production.sh --component ui

# Verify UI service
curl http://localhost:8081/health
```

### Phase 3: Reverse Proxy Setup

#### 1. Configure Nginx
```bash
# Copy production Nginx config
sudo cp deployments/nginx/lending-platform.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/lending-platform.conf /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Phase 4: Complete Deployment

#### 1. Full Deployment
```bash
# Run complete deployment
./scripts/deploy-production.sh --full

# Verify all services
./scripts/health-check.sh --all
```

#### 2. Post-Deployment Verification
```bash
# Check service status
sudo systemctl status lending-api
sudo systemctl status lending-ui
sudo systemctl status nginx

# Verify external access
curl https://yourdomain.com/health
curl https://api.yourdomain.com/health
```

---

## ⚙️ Service Configuration

### Systemd Service Files

#### Lending API Service
```ini
# /etc/systemd/system/lending-api.service
[Unit]
Description=Algorand Lending API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/algorand-showcase
Environment=PATH=/var/www/algorand-showcase/venv-prod/bin
EnvironmentFile=/var/www/algorand-showcase/.env.production
ExecStart=/var/www/algorand-showcase/venv-prod/bin/python apps/business/a2a-lending-desk/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Lending UI Service
```ini
# /etc/systemd/system/lending-ui.service
[Unit]
Description=Algorand Lending UI Overlay
After=network.target lending-api.service
Requires=lending-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/algorand-showcase
Environment=PATH=/var/www/algorand-showcase/venv-prod/bin
EnvironmentFile=/var/www/algorand-showcase/.env.production
ExecStart=/var/www/algorand-showcase/venv-prod/bin/python apps/lending-ui-overlay/deployment/overlay-server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable lending-api lending-ui
sudo systemctl start lending-api lending-ui
```

---

## 🔍 Health Checks

### Automated Health Monitoring
```bash
# Run comprehensive health check
./scripts/health-check.sh

# Sample output:
# ✅ Database: Connected
# ✅ Lending API: Healthy (200ms)
# ✅ Lending UI: Healthy (150ms)
# ✅ MCP Reader: Healthy (100ms)
# ✅ MCP Writer: Healthy (120ms)
# ✅ Nginx: Running
# ✅ SSL: Valid (expires 2024-12-14)
```

### Manual Health Checks
```bash
# Database connectivity
pg_isready -h localhost -p 5432

# Service endpoints
curl -f http://localhost:8003/api/v1/health
curl -f http://localhost:8081/health
curl -f http://localhost:8002/health
curl -f http://localhost:3001/health

# External access
curl -f https://yourdomain.com/health
curl -f https://api.yourdomain.com/health
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service logs
sudo journalctl -u lending-api -f
sudo journalctl -u lending-ui -f

# Common fixes
sudo systemctl restart postgresql
sudo systemctl restart nginx
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U lending_user -d lending_db

# Check environment variables
grep DATABASE_URL .env.production
```

#### 3. SSL Certificate Issues
```bash
# Renew certificates
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Test SSL configuration
nginx -t
```

#### 4. Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep -E "(8003|8081|8002|3001)"

# Kill conflicting processes
sudo lsof -ti:8003 | xargs kill -9
```

### Performance Issues

#### 1. High Memory Usage
```bash
# Monitor memory
free -h
htop

# Restart services to clear memory leaks
sudo systemctl restart lending-api lending-ui
```

#### 2. Slow Response Times
```bash
# Check database performance
sudo -u postgres psql -d lending_db -c "SELECT * FROM pg_stat_activity;"

# Monitor API response times
curl -w "Time: %{time_total}s\n" https://api.yourdomain.com/health
```

---

## 🔄 Rollback Procedures

### Emergency Rollback
```bash
# Quick rollback to previous version
./scripts/rollback.sh --emergency

# This will:
# 1. Stop current services
# 2. Restore previous version from backup
# 3. Restart services
# 4. Verify health
```

### Manual Rollback Steps
```bash
# 1. Stop services
sudo systemctl stop lending-api lending-ui

# 2. Restore from backup
./scripts/backup-data.sh --restore --date 2025-01-14

# 3. Restore code
git checkout previous-stable-tag
./scripts/deploy-production.sh --no-backup

# 4. Restart services
sudo systemctl start lending-api lending-ui

# 5. Verify
./scripts/health-check.sh --all
```

### Database Rollback
```bash
# Create database backup before rollback
pg_dump -h localhost -U lending_user lending_db > backup-pre-rollback.sql

# Restore from specific backup
psql -h localhost -U lending_user -d lending_db < backups/lending_db_2025-01-14.sql
```

---

## 🔄 Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor service health
- Check error logs
- Verify SSL certificate status

#### Weekly
- Database backup verification
- Performance metrics review
- Security update check

#### Monthly
- Full system backup
- SSL certificate renewal check
- Dependencies update
- Security audit

### Automated Maintenance
```bash
# Setup cron jobs
sudo crontab -e

# Add maintenance jobs:
# Health check every 5 minutes
*/5 * * * * /var/www/algorand-showcase/scripts/health-check.sh

# Daily backup at 2 AM
0 2 * * * /var/www/algorand-showcase/scripts/backup-data.sh

# Weekly security updates on Sunday at 3 AM
0 3 * * 0 /var/www/algorand-showcase/scripts/security-update.sh
```

### Backup Strategy
```bash
# Database backup (daily)
pg_dump -h localhost -U lending_user lending_db | gzip > backups/lending_db_$(date +%Y-%m-%d).sql.gz

# Application backup (weekly)
tar -czf backups/app_$(date +%Y-%m-%d).tar.gz \
  --exclude=node_modules --exclude=venv* --exclude=.git \
  /var/www/algorand-showcase

# Configuration backup (daily)
cp -r /etc/nginx/sites-enabled /etc/systemd/system/lending-* backups/config_$(date +%Y-%m-%d)/
```

---

## 📊 Monitoring and Alerts

### Metrics to Monitor
- **API Response Times**: < 500ms average
- **Database Connections**: < 80% of max connections
- **Memory Usage**: < 80% of available RAM
- **Disk Usage**: < 85% of available space
- **SSL Certificate**: > 30 days until expiry

### Alert Configuration
```bash
# Example alert script
#!/bin/bash
if ! curl -f https://yourdomain.com/health > /dev/null 2>&1; then
    echo "ALERT: Lending platform is down!" | mail -s "Production Alert" admin@yourdomain.com
fi
```

---

## 🔐 Security Checklist

- [ ] SSL certificates configured and valid
- [ ] Database credentials secured and rotated
- [ ] JWT secrets configured with strong encryption
- [ ] Rate limiting enabled
- [ ] Firewall configured (only necessary ports open)
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Log monitoring configured
- [ ] Intrusion detection enabled

---

## 📞 Support

### Emergency Contacts
- **DevOps Team**: devops@yourdomain.com
- **On-call Engineer**: +1-XXX-XXX-XXXX
- **Platform Status**: https://status.yourdomain.com

### Documentation Links
- **API Documentation**: https://api.yourdomain.com/docs
- **Architecture Guide**: `/coordination-hub/ARCHITECTURE.md`
- **Troubleshooting**: `/deployments/TROUBLESHOOTING.md`

---

**🎉 Production deployment complete! Your Algorand Lending Platform is live!**