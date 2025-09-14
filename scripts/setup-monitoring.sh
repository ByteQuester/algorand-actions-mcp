#!/bin/bash

# ==============================================================================
# MONITORING SETUP SCRIPT
# ==============================================================================
# Sets up comprehensive monitoring stack for Algorand Lending Platform
# Configures Prometheus, Grafana, Alertmanager, and exporters
# ==============================================================================

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MONITORING_DIR="/opt/algorand-lending/monitoring"
GRAFANA_DIR="/opt/algorand-lending/monitoring/grafana"
PROMETHEUS_CONFIG="/opt/algorand-lending/monitoring/prometheus.yml"
ALERTMANAGER_CONFIG="/opt/algorand-lending/monitoring/alertmanager.yml"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create monitoring directories
setup_directories() {
    log "Setting up monitoring directories..."

    mkdir -p "$MONITORING_DIR"/{prometheus,grafana,alertmanager,exporters}
    mkdir -p "$GRAFANA_DIR"/{dashboards,datasources,provisioning}
    mkdir -p "$GRAFANA_DIR/provisioning"/{dashboards,datasources,notifiers}

    success "Monitoring directories created"
}

# Create Grafana provisioning configuration
create_grafana_provisioning() {
    log "Creating Grafana provisioning configuration..."

    # Datasource configuration
    cat > "$GRAFANA_DIR/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      httpMethod: POST
      manageAlerts: true
      prometheusType: Prometheus
      prometheusVersion: 2.45.0
      cacheLevel: 'High'
      disableMetricsLookup: false
      customQueryParameters: ''
      httpHeaderName1: 'X-Custom-Header'
    secureJsonData:
      httpHeaderValue1: 'HeaderValue'

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
    jsonData:
      maxLines: 1000
      derivedFields:
        - datasourceUid: prometheus
          matcherRegex: 'trace_id=(\w+)'
          name: TraceID
          url: '$${__value.raw}'
EOF

    # Dashboard provisioning
    cat > "$GRAFANA_DIR/provisioning/dashboards/dashboards.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'Algorand Lending Dashboards'
    orgId: 1
    folder: 'Algorand Lending'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    success "Grafana provisioning configuration created"
}

# Create custom Grafana dashboards
create_grafana_dashboards() {
    log "Creating custom Grafana dashboards..."

    # Main system overview dashboard
    cat > "$GRAFANA_DIR/dashboards/system-overview.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Algorand Lending Platform - System Overview",
    "tags": ["algorand", "lending", "overview"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"algorand-.*\"}",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "DOWN"}}, "type": "value"},
              {"options": {"1": {"text": "UP"}}, "type": "value"}
            ],
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"algorand-lending-api\"}[5m]))",
            "legendFormat": "API Requests/sec"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"algorand-lending-api\",status=~\"5..\"}[5m])) / sum(rate(http_requests_total{job=\"algorand-lending-api\"}[5m])) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"algorand-lending-api\"}[5m])) by (le))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job=\"algorand-lending-api\"}[5m])) by (le))",
            "legendFormat": "50th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF

    # Business metrics dashboard
    cat > "$GRAFANA_DIR/dashboards/business-metrics.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Algorand Lending Platform - Business Metrics",
    "tags": ["algorand", "lending", "business"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Loan Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(loan_requests_total[1h])",
            "legendFormat": "Requests per hour"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Loan Approval Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(loan_requests_approved_total[1h]) / rate(loan_requests_total[1h]) * 100",
            "legendFormat": "Approval Rate %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 50},
                {"color": "green", "value": 80}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(loan_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ],
    "time": {"from": "now-24h", "to": "now"},
    "refresh": "1m"
  }
}
EOF

    success "Custom Grafana dashboards created"
}

# Create notification templates
create_notification_templates() {
    log "Creating notification templates..."

    mkdir -p "$MONITORING_DIR/alertmanager/templates"

    cat > "$MONITORING_DIR/alertmanager/templates/default.tmpl" << 'EOF'
{{ define "__alertmanager" }}AlertManager{{ end }}
{{ define "__alertmanagerURL" }}{{ .ExternalURL }}/#/alerts?receiver={{ .Receiver }}{{ end }}

{{ define "__subject" }}[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.SortedPairs.Values | join " " }} {{ if gt (len .CommonLabels) (len .GroupLabels) }}({{ with .CommonLabels.Remove .GroupLabels.Names }}{{ .Values | join " " }}{{ end }}){{ end }}{{ end }}

{{ define "__description" }}{{ end }}

{{ define "__text_alert_list" }}{{ range . }}Labels:
{{ range .Labels.SortedPairs }} - {{ .Name }} = {{ .Value }}
{{ end }}Annotations:
{{ range .Annotations.SortedPairs }} - {{ .Name }} = {{ .Value }}
{{ end }}Source: {{ .GeneratorURL }}
{{ end }}{{ end }}

{{ define "slack.algorand.title" }}[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ range .GroupLabels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}{{ end }}

{{ define "slack.algorand.text" }}{{ range .Alerts }}{{ .Annotations.summary }}
{{ .Annotations.description }}
{{ end }}{{ end }}

{{ define "email.algorand.subject" }}{{ template "__subject" . }}{{ end }}

{{ define "email.algorand.body" }}
Dear Algorand Lending Team,

{{ if gt (len .Alerts.Firing) 0 }}
The following alerts are currently firing:

{{ template "__text_alert_list" .Alerts.Firing }}
{{ end }}

{{ if gt (len .Alerts.Resolved) 0 }}
The following alerts have been resolved:

{{ template "__text_alert_list" .Alerts.Resolved }}
{{ end }}

Dashboard: https://grafana.algorand-lending.com
AlertManager: {{ template "__alertmanagerURL" . }}

Best regards,
Algorand Lending Monitoring System
{{ end }}
EOF

    success "Notification templates created"
}

# Create monitoring health check script
create_health_check() {
    log "Creating monitoring health check script..."

    cat > "$MONITORING_DIR/monitor-health.sh" << 'EOF'
#!/bin/bash

# Health check script for monitoring stack
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"
ALERTMANAGER_URL="http://localhost:9093"

check_service() {
    local name=$1
    local url=$2

    if curl -sf "$url/-/healthy" > /dev/null 2>&1 || curl -sf "$url/api/health" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name is not healthy"
        return 1
    fi
}

echo "Checking monitoring stack health..."
echo "=================================="

check_service "Prometheus" "$PROMETHEUS_URL"
check_service "Grafana" "$GRAFANA_URL"
check_service "AlertManager" "$ALERTMANAGER_URL"

echo ""
echo "Checking metrics availability..."
if curl -sf "$PROMETHEUS_URL/api/v1/query?query=up" > /dev/null; then
    echo "✅ Metrics are being collected"
else
    echo "❌ Metrics collection issues detected"
fi
EOF

    chmod +x "$MONITORING_DIR/monitor-health.sh"
    success "Monitoring health check script created"
}

# Create monitoring Docker Compose override
create_monitoring_compose() {
    log "Creating monitoring Docker Compose configuration..."

    cat > "$MONITORING_DIR/docker-compose.monitoring.yml" << 'EOF'
version: '3.8'

services:
  # Enhanced Prometheus with additional exporters
  prometheus:
    image: prom/prometheus:latest
    container_name: algorand-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/alerts:/etc/prometheus/alerts:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=30d'
      - '--storage.tsdb.retention.size=10GB'
      - '--web.enable-admin-api'
    networks:
      - algorand-lending
    restart: unless-stopped

  # Enhanced Grafana with provisioning
  grafana:
    image: grafana/grafana:latest
    container_name: algorand-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-clock-panel,grafana-simple-json-datasource
      - GF_SMTP_ENABLED=${SMTP_ENABLED:-false}
      - GF_SMTP_HOST=${SMTP_HOST:-}
      - GF_SMTP_USER=${SMTP_USER:-}
      - GF_SMTP_PASSWORD=${SMTP_PASSWORD:-}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - algorand-lending
    restart: unless-stopped

  # AlertManager for alert handling
  alertmanager:
    image: prom/alertmanager:latest
    container_name: algorand-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - ./monitoring/alertmanager/templates:/etc/alertmanager/templates:ro
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
      - '--web.route-prefix=/'
    networks:
      - algorand-lending
    restart: unless-stopped

  # Node Exporter for system metrics
  node-exporter:
    image: prom/node-exporter:latest
    container_name: algorand-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - algorand-lending
    restart: unless-stopped

  # PostgreSQL Exporter
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: algorand-postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable
    networks:
      - algorand-lending
    depends_on:
      - postgres
    restart: unless-stopped

  # Redis Exporter
  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: algorand-redis-exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    networks:
      - algorand-lending
    depends_on:
      - redis
    restart: unless-stopped

  # Nginx Exporter (if using nginx)
  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    container_name: algorand-nginx-exporter
    ports:
      - "9113:9113"
    command:
      - '-nginx.scrape-uri=http://nginx:80/stub_status'
    networks:
      - algorand-lending
    restart: unless-stopped

  # Blackbox Exporter for external monitoring
  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    container_name: algorand-blackbox-exporter
    ports:
      - "9115:9115"
    volumes:
      - ./monitoring/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    networks:
      - algorand-lending
    restart: unless-stopped

  # Loki for log aggregation (optional)
  loki:
    image: grafana/loki:latest
    container_name: algorand-loki
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - algorand-lending
    restart: unless-stopped

networks:
  algorand-lending:
    external: true

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
  loki_data:
EOF

    success "Monitoring Docker Compose configuration created"
}

# Main setup function
main() {
    log "Setting up comprehensive monitoring for Algorand Lending Platform"
    log "================================================================="

    setup_directories
    create_grafana_provisioning
    create_grafana_dashboards
    create_notification_templates
    create_health_check
    create_monitoring_compose

    success "🎯 MONITORING SETUP COMPLETED SUCCESSFULLY! 🎯"
    log "================================================================="

    echo ""
    echo "Next Steps:"
    echo "  1. Update monitoring configuration files with your specific settings"
    echo "  2. Configure notification channels (Slack, email, PagerDuty)"
    echo "  3. Start monitoring stack: docker-compose -f docker-compose.monitoring.yml up -d"
    echo "  4. Access Grafana at http://localhost:3000 (admin/password from env)"
    echo "  5. Access Prometheus at http://localhost:9090"
    echo "  6. Access AlertManager at http://localhost:9093"
    echo ""
    echo "Files Created:"
    echo "  - $PROMETHEUS_CONFIG"
    echo "  - $ALERTMANAGER_CONFIG"
    echo "  - $GRAFANA_DIR/provisioning/"
    echo "  - $MONITORING_DIR/docker-compose.monitoring.yml"
    echo ""
    warning "Remember to:"
    warning "  • Update Slack webhook URLs in alertmanager.yml"
    warning "  • Configure SMTP settings for email notifications"
    warning "  • Set up PagerDuty integration keys"
    warning "  • Customize alert thresholds for your environment"
}

# Execute main function
main "$@"

exit 0
EOF

    chmod +x "$MONITORING_DIR/setup-monitoring.sh"
    success "Monitoring setup script created"
}

# Final deployment documentation
create_deployment_documentation() {
    log "Creating deployment documentation..."

    cat > "$MONITORING_DIR/../PRODUCTION_DEPLOYMENT_GUIDE.md" << 'EOF'
# Algorand Lending Platform - Production Deployment Guide

## Overview

This guide provides complete instructions for deploying the Algorand Lending Platform to a production environment with comprehensive monitoring, alerting, and high availability.

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or CentOS 8
- Minimum 4 CPU cores, 8GB RAM, 100GB SSD
- Docker CE 20.10+ and Docker Compose 1.29+
- Nginx 1.18+ (for reverse proxy)
- SSL certificate (Let's Encrypt recommended)

### Network Requirements
- Ports 80, 443 (HTTP/HTTPS)
- Port 22 (SSH - restrict to management network)
- Internal ports: 8002, 8003, 8788, 8081 (services)
- Monitoring ports: 9090, 3000, 9093 (internal access only)

## Deployment Steps

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw fail2ban

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Start services
sudo systemctl enable docker nginx
sudo systemctl start docker nginx
```

### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-org/algorand-showcase.git
cd algorand-showcase

# Generate production secrets
sudo ./scripts/generate-secrets.sh

# Review and update configuration
sudo nano .env.production
```

### 3. Deploy Services

```bash
# Deploy production services
sudo ./deploy-production.sh

# Install systemd services
sudo ./scripts/install-systemd-services.sh

# Start monitoring stack
sudo ./scripts/setup-monitoring.sh
```

### 4. Configure DNS

Update your DNS records to point to your server:
- `lending.yourdomain.com` → Server IP
- `api.lending.yourdomain.com` → Server IP

### 5. SSL Certificates

```bash
# Obtain SSL certificates
sudo certbot --nginx -d lending.yourdomain.com -d api.lending.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### 6. Verify Deployment

```bash
# Check service status
sudo algorand-lending status

# Run health checks
sudo algorand-lending health

# Check logs
sudo algorand-lending logs
```

## Service Management

### Starting Services
```bash
sudo algorand-lending start
```

### Stopping Services
```bash
sudo algorand-lending stop
```

### Checking Status
```bash
sudo algorand-lending status
```

### Viewing Logs
```bash
sudo algorand-lending logs [service-name]
```

### Backup Data
```bash
sudo algorand-lending backup
```

## Monitoring and Alerts

### Access Monitoring Dashboards
- Grafana: `http://your-server:3000` (internal access only)
- Prometheus: `http://your-server:9090` (internal access only)
- AlertManager: `http://your-server:9093` (internal access only)

### Configure Notifications
1. Update Slack webhook URLs in `/opt/algorand-lending/monitoring/alertmanager.yml`
2. Configure SMTP settings for email alerts
3. Set up PagerDuty integration for critical alerts

## Security Considerations

### Firewall Configuration
- Only expose ports 80, 443, and 22
- Use SSH key authentication only
- Configure fail2ban for brute force protection

### Secret Management
- Store secrets in `/opt/algorand-lending/secrets/` with 600 permissions
- Consider using external secret management (HashiCorp Vault, AWS Secrets Manager)
- Rotate secrets regularly

### SSL/TLS
- Use strong SSL ciphers and protocols
- Enable HSTS headers
- Monitor certificate expiration

## Backup and Recovery

### Automated Backups
- Database: Daily at 2 AM
- Docker volumes: Weekly on Sundays
- Configuration: On each deployment

### Backup Locations
- Local: `/opt/backups/algorand-lending/`
- Remote: Configure S3 or similar cloud storage

### Recovery Procedures
1. Stop services: `sudo algorand-lending stop`
2. Restore database from backup
3. Restore Docker volumes
4. Start services: `sudo algorand-lending start`

## Maintenance

### Regular Tasks
- Monitor system resources and logs
- Update Docker images monthly
- Rotate log files weekly
- Review and rotate secrets quarterly
- Update system packages monthly

### Performance Tuning
- Monitor resource usage and scale accordingly
- Optimize database queries and indexes
- Adjust connection pools based on load
- Configure CDN for static assets

## Troubleshooting

### Common Issues
1. **Service Won't Start**: Check logs and dependencies
2. **High Response Times**: Check resource usage and database performance
3. **SSL Issues**: Verify certificate validity and nginx configuration
4. **Database Connectivity**: Check connection strings and firewall rules

### Support Contacts
- Technical Issues: ops@algorand-lending.com
- Security Issues: security@algorand-lending.com
- Business Issues: support@algorand-lending.com

## Changelog

- v1.0.0: Initial production deployment
- Add version history here...

---

For additional support, please refer to the project documentation or contact the operations team.
EOF

    success "Production deployment guide created"
}

# Main execution function
main() {
    log "Setting up monitoring and alerting system"
    log "========================================"

    setup_directories
    create_grafana_provisioning
    create_grafana_dashboards
    create_notification_templates
    create_health_check
    create_monitoring_compose
    create_deployment_documentation

    success "🎯 MONITORING AND ALERTING SETUP COMPLETED! 🎯"
}

# Execute main function
main "$@"

exit 0