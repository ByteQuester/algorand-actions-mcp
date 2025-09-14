#!/bin/bash

# 🔄 Algorand Lending Platform - Rollback Script
# Emergency rollback system for production deployments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_BASE_DIR="/opt/backups/algorand-lending"
LOG_FILE="/var/log/lending-platform-rollback.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Rollback configuration
ROLLBACK_TYPE="full"
TARGET_BACKUP=""
AUTO_CONFIRM=false
EMERGENCY_MODE=false
SKIP_TESTS=false
PRESERVE_DATA=false
VERBOSE=false

# Service management
SERVICES=("lending-api" "lending-ui" "nginx")
DOCKER_SERVICES=("adk-web" "lending-api" "actions-mcp" "remote-mcp" "postgres" "redis")

# Health check endpoints
declare -A HEALTH_ENDPOINTS=(
    ["api"]="http://localhost:8003/api/v1/health"
    ["ui"]="http://localhost:8081/health"
    ["mcp-reader"]="http://localhost:8002/health"
    ["mcp-writer"]="http://localhost:3001/health"
)

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [$level] $message" | tee -a "$LOG_FILE"
}

# Output functions
success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "INFO" "SUCCESS: $1"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR" "$1"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARN" "$1"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    if [[ "$VERBOSE" == true ]]; then
        log "INFO" "$1"
    fi
}

emergency() {
    echo -e "${PURPLE}🚨 EMERGENCY: $1${NC}"
    log "EMERGENCY" "$1"
}

# Usage information
usage() {
    cat << EOF
🔄 Algorand Lending Platform - Rollback Script

Usage: $0 [OPTIONS]

OPTIONS:
    --to <backup>         Rollback to specific backup (timestamp or 'latest')
    --type <type>         Rollback type: full, code, config, database (default: full)
    --emergency           Emergency rollback mode (fastest, minimal checks)
    --auto-confirm        Skip confirmation prompts (DANGEROUS)
    --preserve-data       Keep current database during code rollback
    --skip-tests          Skip post-rollback health checks
    --list                List available rollback points
    --status              Show current system status
    --verbose             Verbose output
    --help                Show this help message

ROLLBACK TYPES:
    full        Complete rollback (code + config + database)
    code        Application code and services only
    config      Configuration files only
    database    Database rollback only

EXAMPLES:
    $0 --list                           # List available backups
    $0 --to latest                      # Rollback to latest backup
    $0 --to 20250914_120000            # Rollback to specific backup
    $0 --type code --preserve-data      # Rollback code only, keep current data
    $0 --emergency --to latest          # Emergency rollback (fastest)
    $0 --status                         # Check current system status

EMERGENCY ROLLBACK:
    For critical issues, use: $0 --emergency --to latest --auto-confirm

EOF
}

# Safety checks
run_safety_checks() {
    if [[ "$EMERGENCY_MODE" == true ]]; then
        warning "Emergency mode: Skipping safety checks"
        return 0
    fi

    info "Running pre-rollback safety checks..."

    # Check if we're running as appropriate user
    if [[ $EUID -eq 0 ]] && [[ "$AUTO_CONFIRM" != true ]]; then
        warning "Running as root. This may cause permission issues."
        echo -e "${YELLOW}Continue anyway? (y/N):${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            error "Rollback cancelled"
            exit 1
        fi
    fi

    # Check system resources
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))

    if [[ $available_gb -lt 2 ]]; then
        error "Insufficient disk space for rollback: ${available_gb}GB available"
        exit 1
    fi

    # Check if backup exists
    if [[ -n "$TARGET_BACKUP" ]] && [[ "$TARGET_BACKUP" != "latest" ]]; then
        local backup_path="$BACKUP_BASE_DIR/$TARGET_BACKUP"
        if [[ ! -d "$backup_path" ]]; then
            error "Backup not found: $backup_path"
            exit 1
        fi
    fi

    success "Safety checks passed"
}

# List available rollback points
list_rollback_points() {
    echo -e "${CYAN}📋 Available Rollback Points${NC}"
    echo -e "${CYAN}=============================${NC}"

    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        warning "No backup directory found: $BACKUP_BASE_DIR"
        return 1
    fi

    local backup_count=0
    local current_version=""

    # Try to get current version info
    if [[ -f "$PROJECT_ROOT/.git/HEAD" ]]; then
        current_version=$(cd "$PROJECT_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    fi

    echo -e "${GREEN}Current Version:${NC} $current_version"
    echo

    # List backups in reverse chronological order
    for backup_dir in $(ls -1t "$BACKUP_BASE_DIR"/ 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}$' || echo ""); do
        if [[ -d "$BACKUP_BASE_DIR/$backup_dir" ]]; then
            local backup_date=$(echo "$backup_dir" | cut -d'_' -f1)
            local backup_time=$(echo "$backup_dir" | cut -d'_' -f2)
            local formatted_date=$(date -d "${backup_date:0:4}-${backup_date:4:2}-${backup_date:6:2}" '+%Y-%m-%d' 2>/dev/null || echo "$backup_date")
            local formatted_time="${backup_time:0:2}:${backup_time:2:2}:${backup_time:4:2}"
            local size=$(du -sh "$BACKUP_BASE_DIR/$backup_dir" 2>/dev/null | cut -f1 || echo "unknown")

            # Read backup metadata if available
            local backup_type="unknown"
            local git_commit="unknown"
            local metadata_file="$BACKUP_BASE_DIR/$backup_dir/metadata/backup_info.json"

            if [[ -f "$metadata_file" ]]; then
                backup_type=$(grep '"type"' "$metadata_file" | cut -d'"' -f4 2>/dev/null || echo "unknown")
            fi

            # Check for environment snapshot
            local env_file="$BACKUP_BASE_DIR/$backup_dir/config/environment.txt"
            if [[ -f "$env_file" ]]; then
                git_commit=$(grep "Git Commit:" "$env_file" | cut -d' ' -f3 2>/dev/null || echo "unknown")
                if [[ ${#git_commit} -gt 8 ]]; then
                    git_commit=${git_commit:0:8}
                fi
            fi

            local age_days=$(( ($(date +%s) - $(date -d "$formatted_date" +%s)) / 86400 ))

            printf "${GREEN}%-17s${NC} %s %s (${CYAN}%s${NC}) - Type: %-8s - Size: %-8s - Age: %d days\n" \
                "$backup_dir" "$formatted_date" "$formatted_time" "$git_commit" "$backup_type" "$size" "$age_days"

            backup_count=$((backup_count + 1))
        fi
    done

    if [[ $backup_count -eq 0 ]]; then
        warning "No rollback points found"
        return 1
    else
        echo
        success "Found $backup_count rollback point(s)"

        # Show latest backup info
        local latest_backup=$(ls -1t "$BACKUP_BASE_DIR"/ 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}$' | head -n1)
        if [[ -n "$latest_backup" ]]; then
            info "Latest backup: $latest_backup"
            if [[ -L "$BACKUP_BASE_DIR/latest" ]]; then
                info "Latest symlink: $(readlink "$BACKUP_BASE_DIR/latest" | xargs basename)"
            fi
        fi
    fi
}

# Show current system status
show_system_status() {
    echo -e "${CYAN}📊 Current System Status${NC}"
    echo -e "${CYAN}========================${NC}"

    # Git information
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        local git_branch=$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo "unknown")
        local git_commit=$(cd "$PROJECT_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        local git_status=$(cd "$PROJECT_ROOT" && git status --porcelain 2>/dev/null | wc -l || echo "unknown")

        echo -e "${GREEN}Git Branch:${NC} $git_branch"
        echo -e "${GREEN}Git Commit:${NC} $git_commit"
        echo -e "${GREEN}Uncommitted Changes:${NC} $git_status files"
    else
        warning "Not a git repository"
    fi

    echo

    # Service status
    echo -e "${BLUE}Service Status:${NC}"
    for service in "${SERVICES[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo -e "  ${GREEN}✅ $service${NC}: Running"
        else
            echo -e "  ${RED}❌ $service${NC}: Stopped"
        fi
    done

    echo

    # Docker status (if available)
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        echo -e "${BLUE}Docker Container Status:${NC}"
        local compose_file="$PROJECT_ROOT/deployments/docker-compose.production.yml"

        if [[ -f "$compose_file" ]]; then
            for service in "${DOCKER_SERVICES[@]}"; do
                local status=$(docker-compose -f "$compose_file" ps "$service" 2>/dev/null | tail -n +3 | awk '{print $NF}' || echo "not found")
                if [[ "$status" =~ "Up" ]]; then
                    echo -e "  ${GREEN}✅ $service${NC}: $status"
                else
                    echo -e "  ${RED}❌ $service${NC}: $status"
                fi
            done
        else
            info "Docker Compose file not found"
        fi
    else
        info "Docker not available"
    fi

    echo

    # Health check status
    echo -e "${BLUE}Health Check Status:${NC}"
    for service in "${!HEALTH_ENDPOINTS[@]}"; do
        local endpoint="${HEALTH_ENDPOINTS[$service]}"
        if curl -f -s -m 5 "$endpoint" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅ $service${NC}: Healthy"
        else
            echo -e "  ${RED}❌ $service${NC}: Unhealthy"
        fi
    done

    echo

    # System resources
    local disk_usage=$(df / | awk 'NR==2 {print $5}')
    local memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

    echo -e "${BLUE}System Resources:${NC}"
    echo -e "  Disk Usage: $disk_usage"
    echo -e "  Memory Usage: ${memory_usage}%"
    echo -e "  Load Average: $load_avg"

    echo

    # Last deployment info
    if [[ -f "/var/log/lending-platform-deploy.log" ]]; then
        local last_deploy=$(tail -n 20 /var/log/lending-platform-deploy.log | grep "Deployment complete" | tail -n1)
        if [[ -n "$last_deploy" ]]; then
            echo -e "${BLUE}Last Deployment:${NC} $last_deploy"
        fi
    fi
}

# Create pre-rollback backup
create_pre_rollback_backup() {
    if [[ "$EMERGENCY_MODE" == true ]]; then
        warning "Emergency mode: Skipping pre-rollback backup"
        return 0
    fi

    info "Creating pre-rollback backup..."

    local pre_rollback_dir="$BACKUP_BASE_DIR/pre-rollback-$TIMESTAMP"
    mkdir -p "$pre_rollback_dir"

    # Quick backup of critical files
    info "Backing up current state..."

    # Git state
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        cd "$PROJECT_ROOT" && git stash push -u -m "Pre-rollback backup $TIMESTAMP" 2>/dev/null || true
        echo "$(git rev-parse HEAD)" > "$pre_rollback_dir/git_commit.txt"
        echo "$(git branch --show-current)" > "$pre_rollback_dir/git_branch.txt"
    fi

    # Environment and configuration
    cp "$PROJECT_ROOT/.env.production" "$pre_rollback_dir/" 2>/dev/null || true
    cp -r /etc/nginx/sites-enabled "$pre_rollback_dir/nginx_sites" 2>/dev/null || true

    # Service status
    systemctl status "${SERVICES[@]}" > "$pre_rollback_dir/service_status.txt" 2>/dev/null || true

    success "Pre-rollback backup created: $pre_rollback_dir"
}

# Stop all services
stop_services() {
    info "Stopping services for rollback..."

    # Stop systemd services
    for service in "${SERVICES[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            info "Stopping service: $service"
            sudo systemctl stop "$service" || warning "Failed to stop $service"
        fi
    done

    # Stop Docker services if available
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.production.yml"
    if [[ -f "$compose_file" ]] && command -v docker-compose >/dev/null 2>&1; then
        info "Stopping Docker services..."
        docker-compose -f "$compose_file" down --timeout 30 2>/dev/null || warning "Failed to stop Docker services"
    fi

    # Give services time to stop gracefully
    sleep 5

    success "Services stopped"
}

# Start all services
start_services() {
    info "Starting services after rollback..."

    # Reload systemd daemon in case service files changed
    sudo systemctl daemon-reload

    # Start Docker services first if available
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.production.yml"
    if [[ -f "$compose_file" ]] && command -v docker-compose >/dev/null 2>&1; then
        info "Starting Docker services..."
        docker-compose -f "$compose_file" up -d 2>/dev/null || warning "Failed to start Docker services"
        sleep 10
    fi

    # Start systemd services
    for service in "${SERVICES[@]}"; do
        info "Starting service: $service"
        sudo systemctl start "$service" || warning "Failed to start $service"
    done

    # Give services time to start
    sleep 10

    success "Services started"
}

# Rollback application code
rollback_code() {
    local backup_path="$1"

    info "Rolling back application code..."

    # Check for code backup files
    local code_files=()
    if [[ -f "$backup_path/files/application.tar.gz" ]]; then
        code_files+=("$backup_path/files/application.tar.gz")
    elif [[ -f "$backup_path/files/application.tar" ]]; then
        code_files+=("$backup_path/files/application.tar")
    fi

    if [[ ${#code_files[@]} -eq 0 ]]; then
        error "No application code backup found in: $backup_path"
        return 1
    fi

    # Extract application code
    for code_file in "${code_files[@]}"; do
        info "Extracting: $(basename "$code_file")"

        if [[ "$code_file" =~ \.gz$ ]]; then
            tar -xzf "$code_file" -C "$PROJECT_ROOT" || error "Failed to extract $code_file"
        else
            tar -xf "$code_file" -C "$PROJECT_ROOT" || error "Failed to extract $code_file"
        fi
    done

    # Restore Docker volumes if available
    for volume_file in "$backup_path/files"/*.tar.gz "$backup_path/files"/*.tar; do
        if [[ -f "$volume_file" ]] && [[ "$(basename "$volume_file")" =~ ^algorand_lending_ ]]; then
            local volume_name=$(basename "$volume_file" .tar.gz)
            volume_name=$(basename "$volume_name" .tar)

            if docker volume inspect "$volume_name" >/dev/null 2>&1; then
                info "Restoring Docker volume: $volume_name"

                if [[ "$volume_file" =~ \.gz$ ]]; then
                    docker run --rm -v "$volume_name":/data -v "$(dirname "$volume_file")":/backup \
                        alpine sh -c "cd /data && tar -xzf /backup/$(basename "$volume_file")" || warning "Failed to restore volume $volume_name"
                else
                    docker run --rm -v "$volume_name":/data -v "$(dirname "$volume_file")":/backup \
                        alpine sh -c "cd /data && tar -xf /backup/$(basename "$volume_file")" || warning "Failed to restore volume $volume_name"
                fi
            fi
        fi
    done

    success "Application code rollback completed"
}

# Rollback configuration
rollback_config() {
    local backup_path="$1"

    info "Rolling back configuration files..."

    local config_files=()
    if [[ -f "$backup_path/config/configuration.tar.gz" ]]; then
        config_files+=("$backup_path/config/configuration.tar.gz")
    elif [[ -f "$backup_path/config/configuration.tar" ]]; then
        config_files+=("$backup_path/config/configuration.tar")
    fi

    if [[ ${#config_files[@]} -eq 0 ]]; then
        error "No configuration backup found in: $backup_path"
        return 1
    fi

    # Extract configuration files
    for config_file in "${config_files[@]}"; do
        info "Extracting configuration: $(basename "$config_file")"

        if [[ "$config_file" =~ \.gz$ ]]; then
            sudo tar -xzf "$config_file" -C / || error "Failed to extract $config_file"
        else
            sudo tar -xf "$config_file" -C / || error "Failed to extract $config_file"
        fi
    done

    success "Configuration rollback completed"
}

# Rollback database
rollback_database() {
    local backup_path="$1"

    if [[ "$PRESERVE_DATA" == true ]]; then
        warning "Preserving current database data (--preserve-data flag)"
        return 0
    fi

    info "Rolling back database..."

    local db_files=()
    if [[ -f "$backup_path/database/lending_db.sql.gz" ]]; then
        db_files+=("$backup_path/database/lending_db.sql.gz")
    elif [[ -f "$backup_path/database/lending_db.sql" ]]; then
        db_files+=("$backup_path/database/lending_db.sql")
    fi

    if [[ ${#db_files[@]} -eq 0 ]]; then
        error "No database backup found in: $backup_path"
        return 1
    fi

    # Restore database
    for db_file in "${db_files[@]}"; do
        info "Restoring database: $(basename "$db_file")"

        if [[ "$db_file" =~ \.gz$ ]]; then
            gunzip -c "$db_file" | psql -h localhost -U lending_user -d lending_db || error "Failed to restore database"
        else
            psql -h localhost -U lending_user -d lending_db < "$db_file" || error "Failed to restore database"
        fi
    done

    success "Database rollback completed"
}

# Run post-rollback health checks
run_health_checks() {
    if [[ "$SKIP_TESTS" == true ]]; then
        warning "Skipping post-rollback health checks"
        return 0
    fi

    info "Running post-rollback health checks..."

    local failed_checks=0

    # Wait for services to stabilize
    sleep 15

    # Check service status
    for service in "${SERVICES[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            success "Service healthy: $service"
        else
            error "Service unhealthy: $service"
            failed_checks=$((failed_checks + 1))
        fi
    done

    # Check health endpoints
    for service in "${!HEALTH_ENDPOINTS[@]}"; do
        local endpoint="${HEALTH_ENDPOINTS[$service]}"
        local attempts=0
        local max_attempts=3

        while [[ $attempts -lt $max_attempts ]]; do
            if curl -f -s -m 10 "$endpoint" >/dev/null 2>&1; then
                success "Health check passed: $service"
                break
            else
                attempts=$((attempts + 1))
                if [[ $attempts -eq $max_attempts ]]; then
                    error "Health check failed: $service ($endpoint)"
                    failed_checks=$((failed_checks + 1))
                else
                    warning "Health check failed: $service (attempt $attempts/$max_attempts)"
                    sleep 5
                fi
            fi
        done
    done

    if [[ $failed_checks -eq 0 ]]; then
        success "All post-rollback health checks passed"
        return 0
    else
        error "$failed_checks health checks failed"
        return $failed_checks
    fi
}

# Main rollback function
perform_rollback() {
    local backup_path="$BACKUP_BASE_DIR/$TARGET_BACKUP"

    if [[ "$TARGET_BACKUP" == "latest" ]]; then
        local latest_backup=$(ls -1t "$BACKUP_BASE_DIR"/ 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}$' | head -n1)
        if [[ -z "$latest_backup" ]]; then
            error "No latest backup found"
            exit 1
        fi
        backup_path="$BACKUP_BASE_DIR/$latest_backup"
        TARGET_BACKUP="$latest_backup"
    fi

    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
        exit 1
    fi

    # Show rollback information
    echo -e "${CYAN}🔄 Algorand Lending Platform Rollback${NC}"
    echo -e "${CYAN}====================================${NC}"
    echo
    info "Rollback Type: $ROLLBACK_TYPE"
    info "Target Backup: $TARGET_BACKUP"
    info "Backup Path: $backup_path"
    info "Emergency Mode: $EMERGENCY_MODE"
    info "Preserve Data: $PRESERVE_DATA"
    echo

    # Read backup metadata
    local metadata_file="$backup_path/metadata/backup_info.json"
    if [[ -f "$metadata_file" ]]; then
        local backup_date=$(grep '"date"' "$metadata_file" | cut -d'"' -f4 2>/dev/null || echo "unknown")
        local backup_type=$(grep '"type"' "$metadata_file" | cut -d'"' -f4 2>/dev/null || echo "unknown")
        info "Backup Date: $backup_date"
        info "Backup Type: $backup_type"
        echo
    fi

    # Final confirmation
    if [[ "$AUTO_CONFIRM" != true ]]; then
        echo -e "${RED}⚠️  WARNING: This will rollback your system to a previous state!${NC}"
        echo -e "${RED}⚠️  Current data and configuration may be lost!${NC}"
        echo
        echo -e "${YELLOW}Are you sure you want to proceed with the rollback? (type 'YES' to confirm):${NC}"
        read -r confirmation

        if [[ "$confirmation" != "YES" ]]; then
            info "Rollback cancelled by user"
            exit 0
        fi
    fi

    # Start rollback process
    emergency "STARTING ROLLBACK TO $TARGET_BACKUP"

    create_pre_rollback_backup
    stop_services

    case "$ROLLBACK_TYPE" in
        "full")
            rollback_config "$backup_path"
            rollback_code "$backup_path"
            rollback_database "$backup_path"
            ;;
        "code")
            rollback_code "$backup_path"
            ;;
        "config")
            rollback_config "$backup_path"
            ;;
        "database")
            rollback_database "$backup_path"
            ;;
        *)
            error "Unknown rollback type: $ROLLBACK_TYPE"
            exit 1
            ;;
    esac

    start_services

    if run_health_checks; then
        emergency "🎉 ROLLBACK COMPLETED SUCCESSFULLY!"
        success "System rolled back to: $TARGET_BACKUP"
        success "All health checks passed"

        # Log successful rollback
        log "INFO" "ROLLBACK_SUCCESS: Rolled back to $TARGET_BACKUP (type: $ROLLBACK_TYPE)"
    else
        emergency "⚠️  ROLLBACK COMPLETED WITH ISSUES!"
        warning "Some health checks failed - please investigate immediately"
        warning "Check logs: $LOG_FILE"

        # Log rollback with issues
        log "WARN" "ROLLBACK_ISSUES: Rolled back to $TARGET_BACKUP but health checks failed"

        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --to)
                TARGET_BACKUP="$2"
                shift 2
                ;;
            --type)
                ROLLBACK_TYPE="$2"
                shift 2
                ;;
            --emergency)
                EMERGENCY_MODE=true
                shift
                ;;
            --auto-confirm)
                AUTO_CONFIRM=true
                shift
                ;;
            --preserve-data)
                PRESERVE_DATA=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --list)
                list_rollback_points
                exit $?
                ;;
            --status)
                show_system_status
                exit $?
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Validate required parameters
    if [[ -z "$TARGET_BACKUP" ]]; then
        error "No target backup specified. Use --to <backup> or --to latest"
        usage
        exit 1
    fi
}

# Create log file if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Execute main function
parse_args "$@"
run_safety_checks
perform_rollback