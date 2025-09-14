#!/bin/bash

# ==============================================================================
# SYSTEMD SERVICES INSTALLATION SCRIPT
# ==============================================================================
# Installs and configures systemd services for Algorand Lending Platform
# Run this script after the main deployment to set up service management
# ==============================================================================

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_USER="algorand"
SERVICE_GROUP="algorand"
DEPLOY_DIR="/opt/algorand-lending"

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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Create service user if it doesn't exist
create_service_user() {
    log "Creating service user and group..."

    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$DEPLOY_DIR" "$SERVICE_USER"
        success "Created user: $SERVICE_USER"
    else
        log "User $SERVICE_USER already exists"
    fi

    # Add user to docker group
    if getent group docker > /dev/null 2>&1; then
        usermod -a -G docker "$SERVICE_USER"
        success "Added $SERVICE_USER to docker group"
    else
        warning "Docker group not found. Make sure Docker is properly installed."
    fi
}

# Set proper permissions
set_permissions() {
    log "Setting up directory permissions..."

    # Create directories if they don't exist
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "/var/log/algorand-lending"

    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$DEPLOY_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "/var/log/algorand-lending"

    # Set permissions
    chmod -R 755 "$DEPLOY_DIR"
    chmod -R 755 "/var/log/algorand-lending"

    # Make scripts executable
    chmod +x "$DEPLOY_DIR"/scripts/*.sh 2>/dev/null || true

    success "Permissions set successfully"
}

# Install systemd service files
install_service_files() {
    log "Installing systemd service files..."

    local service_files=(
        "algorand-lending.service"
        "algorand-adk-web.service"
        "algorand-lending-api.service"
        "algorand-actions-mcp.service"
        "algorand-remote-mcp.service"
        "algorand-lending-stack.target"
    )

    for service_file in "${service_files[@]}"; do
        local source_file="$DEPLOY_DIR/systemd/$service_file"
        local dest_file="$SYSTEMD_DIR/$service_file"

        if [[ -f "$source_file" ]]; then
            cp "$source_file" "$dest_file"
            chmod 644 "$dest_file"
            success "Installed: $service_file"
        else
            error "Service file not found: $source_file"
            return 1
        fi
    done

    success "All service files installed"
}

# Reload systemd and enable services
configure_systemd() {
    log "Configuring systemd services..."

    # Reload systemd daemon
    systemctl daemon-reload

    # Enable services
    local services=(
        "algorand-lending.service"
        "algorand-adk-web.service"
        "algorand-lending-api.service"
        "algorand-actions-mcp.service"
        "algorand-remote-mcp.service"
        "algorand-lending-stack.target"
    )

    for service in "${services[@]}"; do
        if systemctl enable "$service"; then
            success "Enabled: $service"
        else
            error "Failed to enable: $service"
            return 1
        fi
    done

    success "All services enabled"
}

# Create service management aliases
create_aliases() {
    log "Creating service management aliases..."

    cat > /usr/local/bin/algorand-lending << 'EOF'
#!/bin/bash
# Algorand Lending Platform Service Management Script

case "$1" in
    "start")
        systemctl start algorand-lending-stack.target
        ;;
    "stop")
        systemctl stop algorand-lending-stack.target
        ;;
    "restart")
        systemctl restart algorand-lending-stack.target
        ;;
    "status")
        systemctl status algorand-lending-stack.target
        ;;
    "logs")
        service_name="${2:-algorand-lending}"
        journalctl -f -u "$service_name"
        ;;
    "health")
        /opt/algorand-lending/scripts/health-check.sh check
        ;;
    "backup")
        /opt/algorand-lending/backup-database.sh
        /opt/algorand-lending/backup-volumes.sh
        ;;
    *)
        echo "Usage: algorand-lending {start|stop|restart|status|logs [service]|health|backup}"
        echo "Available services: algorand-lending, algorand-adk-web, algorand-lending-api, algorand-actions-mcp, algorand-remote-mcp"
        exit 1
        ;;
esac
EOF

    chmod +x /usr/local/bin/algorand-lending
    success "Service management script created at /usr/local/bin/algorand-lending"
}

# Create log rotation configuration
setup_log_rotation() {
    log "Setting up log rotation..."

    cat > /etc/logrotate.d/algorand-lending << 'EOF'
/var/log/algorand-lending/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 algorand algorand
    postrotate
        systemctl reload-or-restart algorand-lending-stack.target
    endscript
}

# Systemd journal rotation
/var/log/journal/*/*.journal {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
EOF

    success "Log rotation configured"
}

# Test services
test_services() {
    log "Testing systemd service configuration..."

    # Test if services can be loaded
    local services=(
        "algorand-lending.service"
        "algorand-lending-stack.target"
    )

    for service in "${services[@]}"; do
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            success "Service $service is properly configured"
        else
            error "Service $service configuration failed"
            return 1
        fi
    done

    # Check if the management script works
    if /usr/local/bin/algorand-lending status >/dev/null 2>&1; then
        success "Service management script is working"
    else
        warning "Service management script test failed (services may not be running yet)"
    fi

    success "Service configuration tests passed"
}

# Display service management information
display_usage_info() {
    log "================================================================="
    success "Systemd services installation completed successfully!"
    log "================================================================="

    echo ""
    echo "Service Management Commands:"
    echo "  sudo systemctl start algorand-lending-stack.target    # Start all services"
    echo "  sudo systemctl stop algorand-lending-stack.target     # Stop all services"
    echo "  sudo systemctl restart algorand-lending-stack.target  # Restart all services"
    echo "  sudo systemctl status algorand-lending-stack.target   # Check status"
    echo ""
    echo "Individual Service Management:"
    echo "  sudo systemctl start algorand-lending-api.service     # Start API only"
    echo "  sudo systemctl restart algorand-adk-web.service       # Restart frontend"
    echo "  sudo systemctl status algorand-actions-mcp.service    # Check MCP status"
    echo ""
    echo "Convenient Management Script:"
    echo "  sudo algorand-lending start                           # Start all services"
    echo "  sudo algorand-lending stop                            # Stop all services"
    echo "  sudo algorand-lending restart                         # Restart all services"
    echo "  sudo algorand-lending status                          # Show status"
    echo "  sudo algorand-lending logs [service-name]             # View logs"
    echo "  sudo algorand-lending health                          # Health check"
    echo "  sudo algorand-lending backup                          # Backup data"
    echo ""
    echo "Log Files:"
    echo "  journalctl -f -u algorand-lending-stack.target        # Follow logs"
    echo "  tail -f /var/log/algorand-lending/*.log               # Application logs"
    echo ""
    warning "Important Notes:"
    warning "1. Services will auto-start on system boot"
    warning "2. Services will auto-restart on failure"
    warning "3. Make sure Docker is running before starting services"
    warning "4. Monitor logs for any configuration issues"
}

# Main installation function
main() {
    log "Starting Algorand Lending Platform systemd installation"
    log "======================================================="

    check_root
    create_service_user
    set_permissions
    install_service_files
    configure_systemd
    create_aliases
    setup_log_rotation
    test_services

    display_usage_info
}

# Execute main function
main "$@"

exit 0