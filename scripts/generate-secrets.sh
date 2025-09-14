#!/bin/bash

# ==============================================================================
# PRODUCTION SECRETS GENERATOR
# ==============================================================================
# Generates secure random secrets for production deployment
# Creates a properly configured .env.production file with secure defaults
# ==============================================================================

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SECRETS_DIR="/opt/algorand-lending/secrets"
ENV_TEMPLATE=".env.production.template"
ENV_PRODUCTION=".env.production"
BACKUP_DIR="/opt/backups/algorand-lending/secrets"

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

# Generate a secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -base64 $((length * 3 / 4)) | tr -d "=+/" | cut -c1-${length}
}

# Generate a hex secret
generate_hex_secret() {
    local length=${1:-32}
    openssl rand -hex $((length / 2))
}

# Generate a UUID
generate_uuid() {
    if command -v uuidgen &> /dev/null; then
        uuidgen
    else
        python3 -c "import uuid; print(uuid.uuid4())"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if openssl is available
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is required but not installed"
        exit 1
    fi

    # Check if template file exists
    if [[ ! -f "$ENV_TEMPLATE" ]]; then
        error "Environment template file not found: $ENV_TEMPLATE"
        exit 1
    fi

    success "Prerequisites check passed"
}

# Create secrets directory
setup_secrets_directory() {
    log "Setting up secrets directory..."

    sudo mkdir -p "$SECRETS_DIR"
    sudo mkdir -p "$BACKUP_DIR"

    # Set restrictive permissions
    sudo chmod 700 "$SECRETS_DIR"
    sudo chmod 700 "$BACKUP_DIR"

    if [[ -n "${SUDO_USER:-}" ]]; then
        sudo chown -R "$SUDO_USER:$SUDO_USER" "$SECRETS_DIR"
        sudo chown -R "$SUDO_USER:$SUDO_USER" "$BACKUP_DIR"
    fi

    success "Secrets directory created"
}

# Generate all required secrets
generate_all_secrets() {
    log "Generating secure secrets..."

    # Generate secrets and store in associative array
    declare -A SECRETS

    # Database secrets
    SECRETS["POSTGRES_PASSWORD"]=$(generate_secret 32)
    SECRETS["DATABASE_PASSWORD"]=${SECRETS["POSTGRES_PASSWORD"]}

    # Redis secrets
    SECRETS["REDIS_PASSWORD"]=$(generate_secret 32)

    # JWT secrets
    SECRETS["JWT_SECRET"]=$(generate_secret 64)

    # Cookie and session secrets
    SECRETS["COOKIE_SECRET"]=$(generate_secret 32)
    SECRETS["SESSION_SECRET"]=$(generate_secret 32)

    # MCP service secrets
    SECRETS["MCP_AUTH_TOKEN"]=$(generate_secret 32)
    SECRETS["MCP_API_KEY"]=$(generate_secret 32)

    # Grafana admin password
    SECRETS["GRAFANA_PASSWORD"]=$(generate_secret 16)

    # Backup encryption key
    SECRETS["BACKUP_ENCRYPTION_KEY"]=$(generate_hex_secret 64)

    # Generate unique identifiers
    SECRETS["DEPLOYMENT_ID"]=$(generate_uuid)
    SECRETS["BUILD_NUMBER"]=$(date +%Y%m%d%H%M%S)

    success "All secrets generated"

    # Store secrets in individual files for additional security
    for secret_name in "${!SECRETS[@]}"; do
        echo -n "${SECRETS[$secret_name]}" > "$SECRETS_DIR/$secret_name"
        chmod 600 "$SECRETS_DIR/$secret_name"
    done

    success "Secrets stored in $SECRETS_DIR"
}

# Prompt for user-specific configuration
collect_user_configuration() {
    log "Collecting user-specific configuration..."

    declare -A USER_CONFIG

    # Domain configuration
    read -p "Enter your domain name (e.g., lending.example.com): " domain
    USER_CONFIG["DOMAIN"]=${domain:-"lending.yourdomain.com"}
    USER_CONFIG["API_DOMAIN"]="api.${USER_CONFIG["DOMAIN"]}"

    # SSL email
    read -p "Enter email for SSL certificates: " ssl_email
    USER_CONFIG["SSL_EMAIL"]=${ssl_email:-"admin@${USER_CONFIG["DOMAIN"]}"}

    # Notification email
    read -p "Enter notification from email: " notification_email
    USER_CONFIG["NOTIFICATION_FROM"]=${notification_email:-"noreply@${USER_CONFIG["DOMAIN"]}"}

    # Database settings
    read -p "Enter PostgreSQL database name [algorand_lending]: " db_name
    USER_CONFIG["POSTGRES_DB"]=${db_name:-"algorand_lending"}

    read -p "Enter PostgreSQL username [algorand_user]: " db_user
    USER_CONFIG["POSTGRES_USER"]=${db_user:-"algorand_user"}

    # Feature flags
    read -p "Enable user registration? (y/N): " enable_reg
    USER_CONFIG["ENABLE_USER_REGISTRATION"]=$(if [[ "$enable_reg" =~ ^[Yy]$ ]]; then echo "true"; else echo "false"; fi)

    read -p "Enable Grafana admin access? (Y/n): " enable_grafana
    USER_CONFIG["GRAFANA_ENABLED"]=$(if [[ "$enable_grafana" =~ ^[Nn]$ ]]; then echo "false"; else echo "true"; fi)

    success "User configuration collected"

    # Store user config
    for config_name in "${!USER_CONFIG[@]}"; do
        echo -n "${USER_CONFIG[$config_name]}" > "$SECRETS_DIR/USER_$config_name"
        chmod 600 "$SECRETS_DIR/USER_$config_name"
    done
}

# Create production environment file
create_production_env() {
    log "Creating production environment file..."

    # Backup existing file if it exists
    if [[ -f "$ENV_PRODUCTION" ]]; then
        cp "$ENV_PRODUCTION" "$ENV_PRODUCTION.backup.$(date +%s)"
        warning "Existing $ENV_PRODUCTION backed up"
    fi

    # Start with template
    cp "$ENV_TEMPLATE" "$ENV_PRODUCTION"

    # Read generated secrets
    local postgres_password
    local redis_password
    local jwt_secret
    local cookie_secret
    local session_secret
    local mcp_auth_token
    local mcp_api_key
    local grafana_password
    local backup_encryption_key

    postgres_password=$(cat "$SECRETS_DIR/POSTGRES_PASSWORD")
    redis_password=$(cat "$SECRETS_DIR/REDIS_PASSWORD")
    jwt_secret=$(cat "$SECRETS_DIR/JWT_SECRET")
    cookie_secret=$(cat "$SECRETS_DIR/COOKIE_SECRET")
    session_secret=$(cat "$SECRETS_DIR/SESSION_SECRET")
    mcp_auth_token=$(cat "$SECRETS_DIR/MCP_AUTH_TOKEN")
    mcp_api_key=$(cat "$SECRETS_DIR/MCP_API_KEY")
    grafana_password=$(cat "$SECRETS_DIR/GRAFANA_PASSWORD")
    backup_encryption_key=$(cat "$SECRETS_DIR/BACKUP_ENCRYPTION_KEY")

    # Read user configuration
    local domain
    local api_domain
    local ssl_email
    local notification_from
    local postgres_db
    local postgres_user
    local enable_registration
    local grafana_enabled

    domain=$(cat "$SECRETS_DIR/USER_DOMAIN" 2>/dev/null || echo "lending.yourdomain.com")
    api_domain=$(cat "$SECRETS_DIR/USER_API_DOMAIN" 2>/dev/null || echo "api.lending.yourdomain.com")
    ssl_email=$(cat "$SECRETS_DIR/USER_SSL_EMAIL" 2>/dev/null || echo "admin@yourdomain.com")
    notification_from=$(cat "$SECRETS_DIR/USER_NOTIFICATION_FROM" 2>/dev/null || echo "noreply@yourdomain.com")
    postgres_db=$(cat "$SECRETS_DIR/USER_POSTGRES_DB" 2>/dev/null || echo "algorand_lending")
    postgres_user=$(cat "$SECRETS_DIR/USER_POSTGRES_USER" 2>/dev/null || echo "algorand_user")
    enable_registration=$(cat "$SECRETS_DIR/USER_ENABLE_USER_REGISTRATION" 2>/dev/null || echo "true")
    grafana_enabled=$(cat "$SECRETS_DIR/USER_GRAFANA_ENABLED" 2>/dev/null || echo "true")

    # Replace placeholders in the environment file
    sed -i "s/DOMAIN=lending.yourdomain.com/DOMAIN=$domain/g" "$ENV_PRODUCTION"
    sed -i "s/API_DOMAIN=api.lending.yourdomain.com/API_DOMAIN=$api_domain/g" "$ENV_PRODUCTION"
    sed -i "s/SSL_EMAIL=admin@yourdomain.com/SSL_EMAIL=$ssl_email/g" "$ENV_PRODUCTION"
    sed -i "s/NOTIFICATION_FROM=noreply@yourdomain.com/NOTIFICATION_FROM=$notification_from/g" "$ENV_PRODUCTION"
    sed -i "s/POSTGRES_DB=algorand_lending/POSTGRES_DB=$postgres_db/g" "$ENV_PRODUCTION"
    sed -i "s/POSTGRES_USER=algorand_user/POSTGRES_USER=$postgres_user/g" "$ENV_PRODUCTION"
    sed -i "s/ENABLE_USER_REGISTRATION=true/ENABLE_USER_REGISTRATION=$enable_registration/g" "$ENV_PRODUCTION"

    # Replace secret placeholders
    sed -i "s/CHANGEME_SECURE_DB_PASSWORD_32_CHARS_MIN/$postgres_password/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_SECURE_REDIS_PASSWORD_32_CHARS_MIN/$redis_password/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_SUPER_SECURE_JWT_SECRET_MINIMUM_32_CHARACTERS_LONG_FOR_PRODUCTION/$jwt_secret/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_SECURE_COOKIE_SECRET_32_CHARS_MIN/$cookie_secret/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_SECURE_SESSION_SECRET_32_CHARS_MIN/$session_secret/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_MCP_AUTH_TOKEN_32_CHARS_MIN/$mcp_auth_token/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_MCP_API_KEY_32_CHARS_MIN/$mcp_api_key/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_SECURE_GRAFANA_PASSWORD/$grafana_password/g" "$ENV_PRODUCTION"
    sed -i "s/CHANGEME_BACKUP_ENCRYPTION_KEY_32_CHARS_MIN/$backup_encryption_key/g" "$ENV_PRODUCTION"

    # Update CORS origins
    sed -i "s/CORS_ORIGINS=https:\/\/lending.yourdomain.com,https:\/\/api.lending.yourdomain.com/CORS_ORIGINS=https:\/\/$domain,https:\/\/$api_domain/g" "$ENV_PRODUCTION"

    # Add build information
    local build_timestamp
    local git_commit
    build_timestamp=$(date -Iseconds)
    git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

    echo "" >> "$ENV_PRODUCTION"
    echo "# Build Information (Auto-generated)" >> "$ENV_PRODUCTION"
    echo "BUILD_TIMESTAMP=$build_timestamp" >> "$ENV_PRODUCTION"
    echo "GIT_COMMIT_HASH=$git_commit" >> "$ENV_PRODUCTION"
    echo "BUILD_NUMBER=$(cat "$SECRETS_DIR/BUILD_NUMBER")" >> "$ENV_PRODUCTION"

    # Set restrictive permissions
    chmod 600 "$ENV_PRODUCTION"

    success "Production environment file created: $ENV_PRODUCTION"
}

# Create secrets summary
create_secrets_summary() {
    log "Creating secrets summary..."

    cat > "$SECRETS_DIR/SECRETS_SUMMARY.txt" << EOF
# Algorand Lending Platform - Production Secrets Summary
# Generated on: $(date)
# Deployment ID: $(cat "$SECRETS_DIR/DEPLOYMENT_ID")

## Critical Information:
- All secrets are stored in: $SECRETS_DIR
- Production environment: $ENV_PRODUCTION
- Backup location: $BACKUP_DIR

## Database Access:
- Database: $(cat "$SECRETS_DIR/USER_POSTGRES_DB")
- Username: $(cat "$SECRETS_DIR/USER_POSTGRES_USER")
- Password: Stored in $SECRETS_DIR/POSTGRES_PASSWORD

## Web Access:
- Frontend: https://$(cat "$SECRETS_DIR/USER_DOMAIN")
- API: https://$(cat "$SECRETS_DIR/USER_API_DOMAIN")
- Grafana: http://localhost:3000 (admin/$(cat "$SECRETS_DIR/GRAFANA_PASSWORD"))

## Important Files:
1. $ENV_PRODUCTION - Main environment configuration
2. $SECRETS_DIR/* - Individual secret files
3. $(pwd)/deploy-production.sh - Deployment script

## Security Notes:
- All secret files have 600 permissions (owner read/write only)
- Secrets directory has 700 permissions (owner access only)
- Never commit .env.production to version control
- Regularly rotate secrets in production
- Use external secrets manager in enterprise deployments

## Next Steps:
1. Review and customize $ENV_PRODUCTION
2. Update DNS records to point to this server
3. Run deployment script: sudo ./deploy-production.sh
4. Install systemd services: sudo ./scripts/install-systemd-services.sh
EOF

    chmod 600 "$SECRETS_DIR/SECRETS_SUMMARY.txt"

    success "Secrets summary created: $SECRETS_DIR/SECRETS_SUMMARY.txt"
}

# Validate generated configuration
validate_configuration() {
    log "Validating generated configuration..."

    # Check environment file syntax
    if ! grep -q "^POSTGRES_PASSWORD=" "$ENV_PRODUCTION"; then
        error "Database password not set correctly"
        return 1
    fi

    if ! grep -q "^JWT_SECRET=" "$ENV_PRODUCTION"; then
        error "JWT secret not set correctly"
        return 1
    fi

    # Check if secrets contain expected patterns
    local postgres_password
    postgres_password=$(cat "$SECRETS_DIR/POSTGRES_PASSWORD")

    if [[ ${#postgres_password} -lt 32 ]]; then
        error "Generated password is too short"
        return 1
    fi

    if [[ "$postgres_password" =~ [[:space:]] ]]; then
        error "Generated password contains whitespace"
        return 1
    fi

    success "Configuration validation passed"
}

# Create backup of secrets
backup_secrets() {
    log "Creating encrypted backup of secrets..."

    local backup_file="$BACKUP_DIR/secrets-backup-$(date +%Y%m%d_%H%M%S).tar.gz.enc"

    # Create encrypted backup
    tar -czf - -C "$SECRETS_DIR" . | openssl enc -aes-256-cbc -salt -pbkdf2 -out "$backup_file"

    echo "Backup created: $backup_file"
    echo "Backup password: $(generate_secret 16)"
    echo "Store the backup password separately and securely!"

    success "Encrypted backup created"
}

# Display final instructions
display_instructions() {
    log "================================================================="
    success "🔐 PRODUCTION SECRETS GENERATION COMPLETED! 🔐"
    log "================================================================="

    echo ""
    echo "Generated Files:"
    echo "  📄 $ENV_PRODUCTION - Production environment configuration"
    echo "  📁 $SECRETS_DIR/ - Individual secret files"
    echo "  📋 $SECRETS_DIR/SECRETS_SUMMARY.txt - Configuration summary"
    echo ""
    echo "Next Steps:"
    echo "  1️⃣  Review $ENV_PRODUCTION and customize as needed"
    echo "  2️⃣  Update DNS records to point your domain to this server"
    echo "  3️⃣  Run: sudo ./deploy-production.sh"
    echo "  4️⃣  Run: sudo ./scripts/install-systemd-services.sh"
    echo "  5️⃣  Test deployment with health checks"
    echo ""
    warning "🔒 SECURITY REMINDERS:"
    warning "  • Never commit .env.production to version control"
    warning "  • Restrict access to $SECRETS_DIR (chmod 700)"
    warning "  • Regularly rotate secrets in production"
    warning "  • Use external secrets manager for enterprise deployments"
    warning "  • Monitor access logs for unauthorized attempts"
    echo ""
    echo "Access Information:"
    echo "  🌐 Frontend: https://$(cat "$SECRETS_DIR/USER_DOMAIN" 2>/dev/null || echo "your-domain.com")"
    echo "  🔧 API: https://$(cat "$SECRETS_DIR/USER_API_DOMAIN" 2>/dev/null || echo "api.your-domain.com")"
    echo "  📊 Grafana: http://localhost:3000 (admin/$(cat "$SECRETS_DIR/GRAFANA_PASSWORD"))"
    echo ""
    success "Secrets generation complete! Review the summary and proceed with deployment."
}

# Main execution function
main() {
    log "Starting production secrets generation"
    log "====================================="

    check_prerequisites
    setup_secrets_directory
    generate_all_secrets
    collect_user_configuration
    create_production_env
    create_secrets_summary
    validate_configuration
    backup_secrets
    display_instructions
}

# Execute main function
main "$@"

exit 0