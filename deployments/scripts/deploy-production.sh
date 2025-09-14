#!/bin/bash

# ==============================================================================
# ALGORAND SHOWCASE PRODUCTION DEPLOYMENT SCRIPT
# ==============================================================================
# Agent 1: Production Infrastructure Deployment
# Last Updated: 2025-09-14
#
# This script sets up the complete production environment for the
# Algorand A2A Lending Platform on a cloud server.
# ==============================================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ==============================================================================
# CONFIGURATION VARIABLES
# ==============================================================================

DEPLOY_DIR="/opt/algorand-lending"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"
NGINX_CONFIG_FILE="algorand-lending.nginx.conf"
SSL_EMAIL="admin@yourdomain.com"  # Update this
DOMAIN="lending.yourdomain.com"   # Update this
BACKUP_DIR="/opt/backups/algorand-lending"

# Service ports
ADK_WEB_PORT=8081
LENDING_API_PORT=8003
ACTIONS_MCP_PORT=8788
REMOTE_MCP_PORT=8002
NGINX_PORT=80
NGINX_SSL_PORT=443

# ==============================================================================
# SYSTEM PREREQUISITES CHECK
# ==============================================================================

check_prerequisites() {
    log "Checking system prerequisites..."

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        error "Nginx is not installed. Please install nginx first."
        exit 1
    fi

    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        warning "Certbot is not installed. SSL certificates will need to be set up manually."
    fi

    success "Prerequisites check completed"
}

# ==============================================================================
# PRODUCTION ENVIRONMENT SETUP
# ==============================================================================

setup_directories() {
    log "Setting up production directories..."

    sudo mkdir -p "$DEPLOY_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "/var/log/algorand-lending"
    sudo mkdir -p "/etc/nginx/sites-available"
    sudo mkdir -p "/etc/nginx/sites-enabled"

    # Set proper permissions
    sudo chown -R $USER:$USER "$DEPLOY_DIR"
    sudo chmod -R 755 "$DEPLOY_DIR"

    success "Directories created successfully"
}

create_production_docker_compose() {
    log "Creating production Docker Compose configuration..."

    cat > "$DEPLOY_DIR/$DOCKER_COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  # ADK Web Frontend
  adk-web:
    build:
      context: apps/core/adk-web
      dockerfile: Dockerfile.production
    container_name: algorand-adk-web
    ports:
      - "8081:80"
    environment:
      - NODE_ENV=production
      - API_BASE_URL=https://api.lending.yourdomain.com
      - LENDING_ONLY_MODE=true
    volumes:
      - ./logs:/var/log/nginx
    networks:
      - algorand-lending
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.adk-web.rule=Host(`lending.yourdomain.com`)"
      - "traefik.http.routers.adk-web.tls=true"
      - "traefik.http.routers.adk-web.tls.certresolver=letsencrypt"

  # A2A Lending API
  lending-api:
    build:
      context: apps/business/a2a-lending-desk
      dockerfile: Dockerfile.production
    container_name: algorand-lending-api
    ports:
      - "8003:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - ALGORAND_NETWORK=testnet
      - MCP_ACTIONS_URL=http://actions-mcp:8080
      - MCP_REMOTE_URL=http://remote-mcp:8080
      - REDIS_URL=${REDIS_URL}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    networks:
      - algorand-lending
    depends_on:
      - postgres
      - redis
      - actions-mcp
      - remote-mcp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.lending-api.rule=Host(`api.lending.yourdomain.com`)"
      - "traefik.http.routers.lending-api.tls=true"
      - "traefik.http.routers.lending-api.tls.certresolver=letsencrypt"

  # Algorand Actions MCP Service
  actions-mcp:
    build:
      context: .
      dockerfile: apps/blockchain/algorand-actions-mcp/Dockerfile
    container_name: algorand-actions-mcp
    ports:
      - "8788:8080"
    environment:
      - NODE_ENV=production
      - PORT=8080
      - ALGORAND_NETWORK=${ALGORAND_NETWORK:-testnet}
      - ALGORAND_ALGOD=${ALGORAND_ALGOD}
      - ALGORAND_TOKEN=${ALGORAND_TOKEN}
      - READ_ONLY=false
    networks:
      - algorand-lending
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Algorand Remote MCP Service
  remote-mcp:
    build:
      context: .
      dockerfile: apps/blockchain/algorand-remote-mcp/Dockerfile
    container_name: algorand-remote-mcp
    ports:
      - "8002:8080"
    environment:
      - NODE_ENV=production
      - PORT=8080
      - ALGORAND_NETWORK=${ALGORAND_NETWORK:-testnet}
      - ALGORAND_ALGOD=${ALGORAND_ALGOD}
      - ALGORAND_INDEXER=${ALGORAND_INDEXER}
      - ALGORAND_TOKEN=${ALGORAND_TOKEN}
      - READ_ONLY=true
    networks:
      - algorand-lending
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: algorand-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=algorand_lending
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - algorand-lending
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d algorand_lending"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: algorand-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - algorand-lending
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Traefik Reverse Proxy
  traefik:
    image: traefik:v2.10
    container_name: algorand-traefik
    command:
      - "--api.dashboard=true"
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=${SSL_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt
    networks:
      - algorand-lending
    restart: unless-stopped

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: algorand-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - algorand-lending
    restart: unless-stopped

  # Grafana Dashboards
  grafana:
    image: grafana/grafana:latest
    container_name: algorand-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    networks:
      - algorand-lending
    restart: unless-stopped

networks:
  algorand-lending:
    driver: bridge
    name: algorand-lending-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
  letsencrypt:
EOF

    success "Production Docker Compose configuration created"
}

create_nginx_config() {
    log "Creating Nginx reverse proxy configuration..."

    sudo tee "/etc/nginx/sites-available/$NGINX_CONFIG_FILE" > /dev/null << EOF
# Algorand Lending Platform Nginx Configuration
# Handles SSL termination and reverse proxy for all services

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=auth:10m rate=2r/s;

# Main application server
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN api.$DOMAIN;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# Frontend HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Frontend static files
    location / {
        proxy_pass http://127.0.0.1:$ADK_WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Caching for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1M;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:$ADK_WEB_PORT/health;
        access_log off;
    }
}

# API HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.$DOMAIN;

    # SSL Configuration (same as above)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # CORS headers for API
    add_header Access-Control-Allow-Origin "https://$DOMAIN" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
    add_header Access-Control-Allow-Credentials "true" always;

    # Handle preflight requests
    location / {
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://$DOMAIN";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With";
            add_header Access-Control-Allow-Credentials "true";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }

        # Rate limiting for API endpoints
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://127.0.0.1:$LENDING_API_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Stricter rate limiting for auth endpoints
    location ~ ^/(auth|login|register) {
        limit_req zone=auth burst=5 nodelay;

        proxy_pass http://127.0.0.1:$LENDING_API_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:$LENDING_API_PORT/health;
        access_log off;
    }
}
EOF

    # Enable the site
    sudo ln -sf "/etc/nginx/sites-available/$NGINX_CONFIG_FILE" "/etc/nginx/sites-enabled/"

    success "Nginx configuration created and enabled"
}

# ==============================================================================
# SSL CERTIFICATE SETUP
# ==============================================================================

setup_ssl_certificates() {
    log "Setting up SSL certificates with Let's Encrypt..."

    if command -v certbot &> /dev/null; then
        # Stop nginx temporarily for certificate issuance
        sudo systemctl stop nginx

        # Request SSL certificate
        sudo certbot certonly --standalone \
            --email "$SSL_EMAIL" \
            --agree-tos \
            --no-eff-email \
            -d "$DOMAIN" \
            -d "api.$DOMAIN"

        # Start nginx again
        sudo systemctl start nginx

        # Set up automatic renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

        success "SSL certificates configured with automatic renewal"
    else
        warning "Certbot not available. SSL certificates need to be configured manually."
        warning "Please install certbot and run: certbot --nginx -d $DOMAIN -d api.$DOMAIN"
    fi
}

# ==============================================================================
# ENVIRONMENT CONFIGURATION
# ==============================================================================

create_production_env() {
    log "Creating production environment configuration..."

    cat > "$DEPLOY_DIR/.env.production" << 'EOF'
# ==============================================================================
# ALGORAND LENDING PLATFORM - PRODUCTION ENVIRONMENT
# ==============================================================================
# IMPORTANT: Update all values marked with # UPDATE THIS
# Store sensitive values in a secure secrets manager in production

# Application Environment
ENVIRONMENT=production
NODE_ENV=production

# Domain Configuration
DOMAIN=lending.yourdomain.com  # UPDATE THIS
SSL_EMAIL=admin@yourdomain.com  # UPDATE THIS

# Database Configuration
DATABASE_URL=postgresql://algorand_user:secure_password_here@postgres:5432/algorand_lending  # UPDATE THIS
POSTGRES_USER=algorand_user  # UPDATE THIS
POSTGRES_PASSWORD=secure_password_here  # UPDATE THIS
POSTGRES_DB=algorand_lending

# Redis Configuration
REDIS_URL=redis://:redis_password_here@redis:6379/0  # UPDATE THIS
REDIS_PASSWORD=redis_password_here  # UPDATE THIS

# JWT Configuration
JWT_SECRET=your-super-secure-jwt-secret-minimum-32-characters  # UPDATE THIS
JWT_EXPIRY=24h

# Algorand Network Configuration
ALGORAND_NETWORK=testnet
ALGORAND_ALGOD=https://testnet-api.algonode.cloud
ALGORAND_INDEXER=https://testnet-idx.algonode.cloud
ALGORAND_TOKEN=  # Usually empty for public endpoints

# MCP Service URLs (internal Docker network)
MCP_ACTIONS_URL=http://actions-mcp:8080
MCP_REMOTE_URL=http://remote-mcp:8080

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10

# Monitoring Configuration
GRAFANA_USER=admin  # UPDATE THIS
GRAFANA_PASSWORD=secure_grafana_password  # UPDATE THIS

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Configuration
CORS_ORIGINS=https://lending.yourdomain.com  # UPDATE THIS
COOKIE_SECURE=true
COOKIE_SAMESITE=strict

# Feature Flags
LENDING_ONLY_MODE=true
HIDE_GENERIC_AGENTS=true
ENABLE_REGISTRATION=true
ENABLE_KYC=false  # Set to true when KYC is implemented

# Notification Configuration (optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_FROM=noreply@yourdomain.com  # UPDATE THIS

# Blockchain Transaction Settings
DEFAULT_TRANSACTION_FEE=1000  # microAlgos
TRANSACTION_TIMEOUT=30  # seconds
MAX_TRANSACTION_RETRIES=3

# API Documentation
API_DOCS_ENABLED=false  # Set to true for development only
API_DOCS_PATH=/docs

# Health Check Configuration
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_RETRIES=3
EOF

    warning "Production environment file created at $DEPLOY_DIR/.env.production"
    warning "IMPORTANT: Please update all values marked with '# UPDATE THIS'"
    warning "Consider using a secrets management system for sensitive values"

    success "Environment configuration created"
}

# ==============================================================================
# BACKUP SYSTEM SETUP
# ==============================================================================

create_backup_scripts() {
    log "Creating backup scripts..."

    # Database backup script
    cat > "$DEPLOY_DIR/backup-database.sh" << 'EOF'
#!/bin/bash
# Database backup script for Algorand Lending Platform

set -euo pipefail

BACKUP_DIR="/opt/backups/algorand-lending"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="algorand-postgres"

# Create backup directory
mkdir -p "$BACKUP_DIR/database"

# Perform database backup
docker exec "$CONTAINER_NAME" pg_dump -U algorand_user algorand_lending | gzip > "$BACKUP_DIR/database/algorand_lending_$TIMESTAMP.sql.gz"

# Remove backups older than 30 days
find "$BACKUP_DIR/database" -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: algorand_lending_$TIMESTAMP.sql.gz"
EOF

    # Application data backup script
    cat > "$DEPLOY_DIR/backup-volumes.sh" << 'EOF'
#!/bin/bash
# Docker volumes backup script for Algorand Lending Platform

set -euo pipefail

BACKUP_DIR="/opt/backups/algorand-lending"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/volumes"

# Backup Docker volumes
docker run --rm -v algorand_lending_postgres_data:/data -v "$BACKUP_DIR/volumes":/backup alpine tar czf /backup/postgres_data_$TIMESTAMP.tar.gz -C /data .
docker run --rm -v algorand_lending_redis_data:/data -v "$BACKUP_DIR/volumes":/backup alpine tar czf /backup/redis_data_$TIMESTAMP.tar.gz -C /data .
docker run --rm -v algorand_lending_grafana_data:/data -v "$BACKUP_DIR/volumes":/backup alpine tar czf /backup/grafana_data_$TIMESTAMP.tar.gz -C /data .

# Remove backups older than 30 days
find "$BACKUP_DIR/volumes" -name "*.tar.gz" -mtime +30 -delete

echo "Volume backups completed: $TIMESTAMP"
EOF

    # Make scripts executable
    chmod +x "$DEPLOY_DIR/backup-database.sh"
    chmod +x "$DEPLOY_DIR/backup-volumes.sh"

    # Set up cron jobs for automated backups
    cat > "$DEPLOY_DIR/backup-crontab" << 'EOF'
# Algorand Lending Platform Backup Schedule
# Database backup daily at 2 AM
0 2 * * * /opt/algorand-lending/backup-database.sh >> /var/log/algorand-lending/backup.log 2>&1

# Volume backup weekly on Sundays at 3 AM
0 3 * * 0 /opt/algorand-lending/backup-volumes.sh >> /var/log/algorand-lending/backup.log 2>&1
EOF

    success "Backup scripts created and configured"
}

# ==============================================================================
# MONITORING CONFIGURATION
# ==============================================================================

create_monitoring_config() {
    log "Creating monitoring configuration files..."

    mkdir -p "$DEPLOY_DIR/monitoring"

    # Prometheus configuration
    cat > "$DEPLOY_DIR/monitoring/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'algorand-lending-api'
    static_configs:
      - targets: ['lending-api:8000']
    scrape_interval: 5s
    metrics_path: /metrics

  - job_name: 'algorand-actions-mcp'
    static_configs:
      - targets: ['actions-mcp:8080']
    scrape_interval: 10s
    metrics_path: /metrics

  - job_name: 'algorand-remote-mcp'
    static_configs:
      - targets: ['remote-mcp:8080']
    scrape_interval: 10s
    metrics_path: /metrics

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis:9121']

  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
EOF

    # Grafana provisioning
    mkdir -p "$DEPLOY_DIR/monitoring/grafana/provisioning/datasources"
    mkdir -p "$DEPLOY_DIR/monitoring/grafana/provisioning/dashboards"

    cat > "$DEPLOY_DIR/monitoring/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    success "Monitoring configuration created"
}

# ==============================================================================
# DEPLOYMENT FUNCTIONS
# ==============================================================================

deploy_services() {
    log "Deploying production services..."

    cd "$DEPLOY_DIR"

    # Copy source code
    if [ -d "/home/mpo/algorand-showcase" ]; then
        log "Copying source code..."
        cp -r /home/mpo/algorand-showcase/* .
        success "Source code copied"
    else
        error "Source directory not found. Please ensure the code is available."
        exit 1
    fi

    # Load environment variables
    if [ -f ".env.production" ]; then
        export $(grep -v '^#' .env.production | xargs)
    else
        error "Production environment file not found"
        exit 1
    fi

    # Build and start services
    log "Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache

    log "Starting production services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log "Waiting for services to become healthy..."
    sleep 30

    # Check service health
    check_service_health

    success "All services deployed successfully"
}

check_service_health() {
    log "Checking service health..."

    local services=("adk-web" "lending-api" "actions-mcp" "remote-mcp" "postgres" "redis")

    for service in "${services[@]}"; do
        log "Checking $service health..."

        local max_attempts=10
        local attempt=1

        while [ $attempt -le $max_attempts ]; do
            if docker-compose -f "$DEPLOY_DIR/$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up (healthy)"; then
                success "$service is healthy"
                break
            elif [ $attempt -eq $max_attempts ]; then
                error "$service failed to become healthy"
                docker-compose -f "$DEPLOY_DIR/$DOCKER_COMPOSE_FILE" logs "$service"
                exit 1
            else
                log "Waiting for $service to become healthy (attempt $attempt/$max_attempts)..."
                sleep 10
                ((attempt++))
            fi
        done
    done

    success "All services are healthy"
}

# ==============================================================================
# POST-DEPLOYMENT SETUP
# ==============================================================================

setup_firewall() {
    log "Configuring firewall rules..."

    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        warning "UFW not installed. Firewall setup skipped."
        return
    fi

    # Reset UFW to defaults
    sudo ufw --force reset

    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing

    # SSH access (be careful!)
    sudo ufw allow ssh

    # HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp

    # Monitoring (restrict to internal network)
    sudo ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
    sudo ufw allow from 10.0.0.0/8 to any port 3000  # Grafana

    # Enable firewall
    sudo ufw --force enable

    success "Firewall configured"
}

perform_security_hardening() {
    log "Performing security hardening..."

    # Update system packages
    sudo apt-get update && sudo apt-get upgrade -y

    # Install fail2ban
    sudo apt-get install -y fail2ban

    # Configure fail2ban for nginx
    sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true

[nginx-botsearch]
enabled = true
EOF

    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban

    # Set up log rotation
    sudo tee /etc/logrotate.d/algorand-lending > /dev/null << 'EOF'
/var/log/algorand-lending/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

    success "Security hardening completed"
}

# ==============================================================================
# MAIN DEPLOYMENT FUNCTION
# ==============================================================================

main() {
    log "Starting Algorand Lending Platform Production Deployment"
    log "=========================================================="

    # Pre-deployment checks
    check_prerequisites

    # Setup
    setup_directories
    create_production_docker_compose
    create_nginx_config
    create_production_env
    create_backup_scripts
    create_monitoring_config

    # Deployment
    deploy_services

    # SSL setup (after services are running)
    setup_ssl_certificates

    # Post-deployment security
    setup_firewall
    perform_security_hardening

    # Final status
    log "=========================================================="
    success "🚀 PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY! 🚀"
    log "=========================================================="

    log "Services Status:"
    docker-compose -f "$DEPLOY_DIR/$DOCKER_COMPOSE_FILE" ps

    log ""
    log "Access URLs:"
    log "  Frontend: https://$DOMAIN"
    log "  API: https://api.$DOMAIN"
    log "  Grafana: http://localhost:3000 (internal access only)"
    log "  Prometheus: http://localhost:9090 (internal access only)"

    log ""
    warning "IMPORTANT POST-DEPLOYMENT TASKS:"
    warning "1. Update DNS records to point $DOMAIN to this server"
    warning "2. Review and update all configuration in $DEPLOY_DIR/.env.production"
    warning "3. Set up external monitoring and alerting"
    warning "4. Configure automated testing pipeline"
    warning "5. Review security settings and perform penetration testing"

    log ""
    success "Deployment log saved to: /var/log/algorand-lending/deployment.log"
}

# ==============================================================================
# SCRIPT EXECUTION
# ==============================================================================

# Create log directory if it doesn't exist
sudo mkdir -p /var/log/algorand-lending
sudo chown $USER:$USER /var/log/algorand-lending

# Execute main function and log output
main 2>&1 | tee /var/log/algorand-lending/deployment.log

# Exit with success
exit 0