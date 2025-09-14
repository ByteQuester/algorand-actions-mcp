#!/bin/bash

# 💾 Algorand Lending Platform - Backup Script
# Comprehensive backup solution for production data

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_BASE_DIR="/opt/backups/algorand-lending"
LOG_FILE="/var/log/lending-platform-backup.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y-%m-%d)

# Default values
BACKUP_TYPE="full"
COMPRESS=true
ENCRYPT=false
RETENTION_DAYS=30
GPG_RECIPIENT=""
S3_BUCKET=""
VERBOSE=false
DRY_RUN=false

# Database configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="lending_db"
DB_USER="lending_user"
PGPASSWORD=""

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
    exit 1
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

# Usage information
usage() {
    cat << EOF
💾 Algorand Lending Platform - Backup Script

Usage: $0 [OPTIONS]

OPTIONS:
    --type <type>         Backup type: full, database, files, config (default: full)
    --output-dir <path>   Custom backup directory (default: /opt/backups/algorand-lending)
    --retention <days>    Backup retention in days (default: 30)
    --compress            Compress backup files (default: true)
    --no-compress         Disable compression
    --encrypt             Encrypt backup files with GPG
    --gpg-recipient <id>  GPG recipient for encryption
    --s3-bucket <name>    Upload to S3 bucket after backup
    --dry-run             Show what would be backed up without doing it
    --verbose             Verbose output
    --restore <path>      Restore from backup path
    --list                List available backups
    --help                Show this help message

BACKUP TYPES:
    full        Complete backup (database + files + config)
    database    Database backup only
    files       Application files and volumes
    config      Configuration files only

EXAMPLES:
    $0                                    # Full backup
    $0 --type database                   # Database only
    $0 --type full --encrypt --gpg-recipient admin@domain.com
    $0 --restore /opt/backups/algorand-lending/20250914_120000
    $0 --list                            # List available backups
    $0 --s3-bucket my-backup-bucket      # Upload to S3

EOF
}

# Check prerequisites
check_prerequisites() {
    info "Checking backup prerequisites..."

    # Check required commands
    local required_commands=("pg_dump" "tar" "gzip")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command not found: $cmd"
        fi
    done

    # Check compression tools if needed
    if [[ "$COMPRESS" == true ]]; then
        if ! command -v "gzip" &> /dev/null; then
            warning "gzip not found, disabling compression"
            COMPRESS=false
        fi
    fi

    # Check GPG if encryption is enabled
    if [[ "$ENCRYPT" == true ]]; then
        if ! command -v "gpg" &> /dev/null; then
            error "GPG not found but encryption is enabled"
        fi

        if [[ -z "$GPG_RECIPIENT" ]]; then
            error "GPG recipient not specified for encryption"
        fi

        # Verify GPG key exists
        if ! gpg --list-keys "$GPG_RECIPIENT" >/dev/null 2>&1; then
            error "GPG key not found for recipient: $GPG_RECIPIENT"
        fi
    fi

    # Check AWS CLI if S3 upload is enabled
    if [[ -n "$S3_BUCKET" ]]; then
        if ! command -v "aws" &> /dev/null; then
            error "AWS CLI not found but S3 upload is enabled"
        fi

        # Test AWS credentials
        if ! aws sts get-caller-identity >/dev/null 2>&1; then
            error "AWS credentials not configured properly"
        fi
    fi

    # Check disk space
    local backup_dir_parent=$(dirname "$BACKUP_BASE_DIR")
    local available_space=$(df "$backup_dir_parent" | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))

    if [[ $available_gb -lt 5 ]]; then
        error "Insufficient disk space for backup: ${available_gb}GB available"
    elif [[ $available_gb -lt 10 ]]; then
        warning "Low disk space for backup: ${available_gb}GB available"
    fi

    success "Prerequisites check passed"
}

# Create backup directory structure
create_backup_dirs() {
    local backup_dir="$BACKUP_BASE_DIR/$TIMESTAMP"

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would create backup directories: $backup_dir"
        return 0
    fi

    info "Creating backup directories..."

    mkdir -p "$backup_dir"
    mkdir -p "$backup_dir/database"
    mkdir -p "$backup_dir/files"
    mkdir -p "$backup_dir/config"
    mkdir -p "$backup_dir/logs"
    mkdir -p "$backup_dir/metadata"

    # Create backup metadata
    cat > "$backup_dir/metadata/backup_info.json" << EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$DATE_ONLY",
    "type": "$BACKUP_TYPE",
    "hostname": "$(hostname)",
    "script_version": "1.0",
    "compress": $COMPRESS,
    "encrypt": $ENCRYPT,
    "created_by": "$USER"
}
EOF

    success "Backup directories created: $backup_dir"
    echo "$backup_dir" # Return backup directory path
}

# Database backup
backup_database() {
    local backup_dir="$1"
    local db_backup_file="$backup_dir/database/lending_db.sql"

    info "Starting database backup..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would backup database $DB_NAME to $db_backup_file"
        return 0
    fi

    # Test database connection
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        error "Database connection failed. Cannot create backup."
    fi

    # Create database dump
    local start_time=$(date +%s)
    info "Dumping database: $DB_NAME"

    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --no-password --clean --if-exists > "$db_backup_file" 2>"$backup_dir/logs/database_backup.log"; then

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local file_size=$(du -sh "$db_backup_file" | cut -f1)

        success "Database backup completed in ${duration}s (size: $file_size)"
    else
        error "Database backup failed. Check logs: $backup_dir/logs/database_backup.log"
    fi

    # Create database schema info
    info "Collecting database schema information..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "\d+" > "$backup_dir/database/schema_info.txt" 2>/dev/null || true

    # Compress database backup if requested
    if [[ "$COMPRESS" == true ]]; then
        info "Compressing database backup..."
        gzip -9 "$db_backup_file"
        success "Database backup compressed"
    fi
}

# Application files backup
backup_files() {
    local backup_dir="$1"

    info "Starting application files backup..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would backup application files from $PROJECT_ROOT"
        return 0
    fi

    # Application source code and configuration
    info "Backing up application source..."
    local app_backup_file="$backup_dir/files/application.tar"

    tar -cf "$app_backup_file" \
        --exclude=node_modules \
        --exclude=venv* \
        --exclude=.git \
        --exclude=__pycache__ \
        --exclude=*.log \
        --exclude=.env.local \
        --exclude=backups \
        -C "$PROJECT_ROOT" . 2>"$backup_dir/logs/files_backup.log"

    local file_size=$(du -sh "$app_backup_file" | cut -f1)
    success "Application files backup completed (size: $file_size)"

    # Docker volumes backup (if Docker is running)
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        info "Backing up Docker volumes..."

        local volumes=(
            "algorand_lending_postgres_data"
            "algorand_lending_redis_data"
            "algorand_lending_grafana_data"
            "algorand_lending_letsencrypt"
        )

        for volume in "${volumes[@]}"; do
            if docker volume inspect "$volume" >/dev/null 2>&1; then
                local volume_backup="$backup_dir/files/${volume}.tar"

                docker run --rm \
                    -v "$volume":/data \
                    -v "$backup_dir/files":/backup \
                    alpine tar -cf "/backup/$(basename "$volume_backup")" -C /data . \
                    2>>"$backup_dir/logs/files_backup.log"

                info "Volume backed up: $volume"
            else
                warning "Volume not found: $volume"
            fi
        done

        success "Docker volumes backup completed"
    else
        info "Docker not available, skipping volumes backup"
    fi

    # Compress files backup if requested
    if [[ "$COMPRESS" == true ]]; then
        info "Compressing files backup..."
        gzip -9 "$app_backup_file"

        # Compress volume backups
        for file in "$backup_dir/files"/*.tar; do
            if [[ -f "$file" ]]; then
                gzip -9 "$file"
            fi
        done

        success "Files backup compressed"
    fi
}

# Configuration backup
backup_config() {
    local backup_dir="$1"

    info "Starting configuration backup..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would backup configuration files"
        return 0
    fi

    local config_backup_file="$backup_dir/config/configuration.tar"

    # System configuration files
    info "Backing up system configuration..."

    local config_sources=(
        "/etc/nginx/sites-enabled"
        "/etc/systemd/system/lending-*.service"
        "/etc/letsencrypt"
        "/etc/crontab"
        "/etc/logrotate.d/algorand-lending"
        "$PROJECT_ROOT/.env.production"
        "$PROJECT_ROOT/deployments"
    )

    tar -cf "$config_backup_file" \
        --ignore-failed-read \
        "${config_sources[@]}" \
        2>"$backup_dir/logs/config_backup.log"

    local file_size=$(du -sh "$config_backup_file" | cut -f1)
    success "Configuration backup completed (size: $file_size)"

    # Create environment snapshot
    info "Creating environment snapshot..."
    cat > "$backup_dir/config/environment.txt" << EOF
Hostname: $(hostname)
Date: $(date)
User: $USER
Working Directory: $(pwd)
Git Commit: $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "N/A")
Git Branch: $(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo "N/A")
Docker Version: $(docker --version 2>/dev/null || echo "N/A")
Docker Compose Version: $(docker-compose --version 2>/dev/null || echo "N/A")
System Info: $(uname -a)
Disk Usage: $(df -h /)
Memory Usage: $(free -h)
Services Status:
$(systemctl --no-pager status lending-api lending-ui nginx 2>/dev/null || echo "N/A")
EOF

    # Compress config backup if requested
    if [[ "$COMPRESS" == true ]]; then
        info "Compressing configuration backup..."
        gzip -9 "$config_backup_file"
        success "Configuration backup compressed"
    fi
}

# Encrypt backup if requested
encrypt_backup() {
    local backup_dir="$1"

    if [[ "$ENCRYPT" != true ]]; then
        return 0
    fi

    info "Encrypting backup files..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would encrypt backup files with GPG"
        return 0
    fi

    # Find all backup files
    local files_to_encrypt=()
    while IFS= read -r -d '' file; do
        files_to_encrypt+=("$file")
    done < <(find "$backup_dir" -type f \( -name "*.sql" -o -name "*.tar" -o -name "*.gz" \) -print0)

    for file in "${files_to_encrypt[@]}"; do
        info "Encrypting: $(basename "$file")"

        if gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" --cipher-algo AES256 \
            --output "$file.gpg" "$file" 2>>"$backup_dir/logs/encryption.log"; then

            # Remove original file after successful encryption
            rm "$file"
            info "Encrypted: $(basename "$file").gpg"
        else
            error "Failed to encrypt: $file"
        fi
    done

    success "Backup encryption completed"
}

# Upload to S3 if configured
upload_to_s3() {
    local backup_dir="$1"

    if [[ -z "$S3_BUCKET" ]]; then
        return 0
    fi

    info "Uploading backup to S3: $S3_BUCKET"

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would upload backup to S3 bucket: $S3_BUCKET"
        return 0
    fi

    local s3_path="s3://$S3_BUCKET/algorand-lending/backups/$(basename "$backup_dir")"

    if aws s3 sync "$backup_dir" "$s3_path" \
        --delete \
        --storage-class STANDARD_IA \
        2>"$backup_dir/logs/s3_upload.log"; then

        success "Backup uploaded to S3: $s3_path"

        # Create S3 manifest
        aws s3 ls --recursive "$s3_path" > "$backup_dir/metadata/s3_manifest.txt"
    else
        error "Failed to upload backup to S3. Check logs: $backup_dir/logs/s3_upload.log"
    fi
}

# Clean old backups
cleanup_old_backups() {
    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would clean backups older than $RETENTION_DAYS days"
        return 0
    fi

    info "Cleaning backups older than $RETENTION_DAYS days..."

    local deleted_count=0
    local saved_space=0

    # Find and delete old backups
    while IFS= read -r -d '' backup_path; do
        local size=$(du -sb "$backup_path" | cut -f1)
        saved_space=$((saved_space + size))
        deleted_count=$((deleted_count + 1))

        info "Deleting old backup: $(basename "$backup_path")"
        rm -rf "$backup_path"
    done < <(find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -mtime +$RETENTION_DAYS -print0 2>/dev/null)

    if [[ $deleted_count -gt 0 ]]; then
        local saved_gb=$((saved_space / 1024 / 1024 / 1024))
        success "Cleaned $deleted_count old backups (saved ${saved_gb}GB space)"
    else
        info "No old backups to clean"
    fi
}

# List available backups
list_backups() {
    echo -e "${CYAN}📁 Available Backups${NC}"
    echo -e "${CYAN}==================${NC}"

    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        warning "No backup directory found: $BACKUP_BASE_DIR"
        return 1
    fi

    local backup_count=0
    for backup_dir in "$BACKUP_BASE_DIR"/*/; do
        if [[ -d "$backup_dir" ]]; then
            local backup_name=$(basename "$backup_dir")
            local backup_date=$(echo "$backup_name" | cut -d'_' -f1)
            local backup_time=$(echo "$backup_name" | cut -d'_' -f2)
            local formatted_date=$(date -d "${backup_date:0:4}-${backup_date:4:2}-${backup_date:6:2}" '+%Y-%m-%d' 2>/dev/null || echo "$backup_date")
            local formatted_time="${backup_time:0:2}:${backup_time:2:2}:${backup_time:4:2}"
            local size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1)

            # Read backup metadata if available
            local backup_type="unknown"
            local metadata_file="$backup_dir/metadata/backup_info.json"
            if [[ -f "$metadata_file" ]]; then
                backup_type=$(grep '"type"' "$metadata_file" | cut -d'"' -f4 2>/dev/null || echo "unknown")
            fi

            echo -e "${GREEN}$backup_name${NC} - ${formatted_date} ${formatted_time} - Type: $backup_type - Size: $size"
            backup_count=$((backup_count + 1))
        fi
    done

    if [[ $backup_count -eq 0 ]]; then
        info "No backups found"
    else
        echo
        success "Found $backup_count backup(s)"
    fi
}

# Restore from backup
restore_backup() {
    local backup_path="$1"

    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
    fi

    warning "RESTORE OPERATION - THIS WILL OVERWRITE CURRENT DATA!"
    echo -e "${RED}Are you sure you want to restore from: $(basename "$backup_path")?${NC}"
    echo -e "${RED}This will stop services and overwrite current data. Type 'YES' to continue:${NC}"

    read -r confirmation
    if [[ "$confirmation" != "YES" ]]; then
        info "Restore cancelled"
        exit 0
    fi

    info "Starting restore from: $backup_path"

    # Stop services
    info "Stopping services..."
    sudo systemctl stop lending-api lending-ui nginx 2>/dev/null || true

    # Restore database
    if [[ -f "$backup_path/database/lending_db.sql" ]] || [[ -f "$backup_path/database/lending_db.sql.gz" ]]; then
        info "Restoring database..."

        local db_file="$backup_path/database/lending_db.sql"
        if [[ -f "$backup_path/database/lending_db.sql.gz" ]]; then
            db_file="$backup_path/database/lending_db.sql.gz"
            gunzip -c "$db_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
        else
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$db_file"
        fi

        success "Database restored"
    fi

    # Restore application files
    if [[ -f "$backup_path/files/application.tar" ]] || [[ -f "$backup_path/files/application.tar.gz" ]]; then
        info "Restoring application files..."

        local app_file="$backup_path/files/application.tar"
        if [[ -f "$backup_path/files/application.tar.gz" ]]; then
            app_file="$backup_path/files/application.tar.gz"
            tar -xzf "$app_file" -C "$PROJECT_ROOT"
        else
            tar -xf "$app_file" -C "$PROJECT_ROOT"
        fi

        success "Application files restored"
    fi

    # Restore configuration
    if [[ -f "$backup_path/config/configuration.tar" ]] || [[ -f "$backup_path/config/configuration.tar.gz" ]]; then
        info "Restoring configuration files..."

        local config_file="$backup_path/config/configuration.tar"
        if [[ -f "$backup_path/config/configuration.tar.gz" ]]; then
            config_file="$backup_path/config/configuration.tar.gz"
            sudo tar -xzf "$config_file" -C /
        else
            sudo tar -xf "$config_file" -C /
        fi

        success "Configuration files restored"
    fi

    # Restart services
    info "Restarting services..."
    sudo systemctl daemon-reload
    sudo systemctl start lending-api lending-ui nginx

    success "🎉 Restore completed successfully!"
    warning "Please verify all services are working correctly"
}

# Main backup function
run_backup() {
    local backup_dir

    echo -e "${CYAN}💾 Algorand Lending Platform Backup${NC}"
    echo -e "${CYAN}===================================${NC}"
    echo

    check_prerequisites
    backup_dir=$(create_backup_dirs)

    case "$BACKUP_TYPE" in
        "database")
            backup_database "$backup_dir"
            ;;
        "files")
            backup_files "$backup_dir"
            ;;
        "config")
            backup_config "$backup_dir"
            ;;
        "full")
            backup_database "$backup_dir"
            backup_files "$backup_dir"
            backup_config "$backup_dir"
            ;;
        *)
            error "Unknown backup type: $BACKUP_TYPE"
            ;;
    esac

    if [[ "$DRY_RUN" != true ]]; then
        encrypt_backup "$backup_dir"
        upload_to_s3 "$backup_dir"
        cleanup_old_backups

        # Create latest symlink
        ln -sfn "$backup_dir" "$BACKUP_BASE_DIR/latest"

        # Generate backup summary
        local total_size=$(du -sh "$backup_dir" | cut -f1)
        local file_count=$(find "$backup_dir" -type f | wc -l)

        success "🎉 Backup completed successfully!"
        success "Location: $backup_dir"
        success "Total size: $total_size ($file_count files)"

        if [[ -n "$S3_BUCKET" ]]; then
            success "Uploaded to S3: s3://$S3_BUCKET/algorand-lending/backups/$(basename "$backup_dir")"
        fi
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            --output-dir)
                BACKUP_BASE_DIR="$2"
                shift 2
                ;;
            --retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --compress)
                COMPRESS=true
                shift
                ;;
            --no-compress)
                COMPRESS=false
                shift
                ;;
            --encrypt)
                ENCRYPT=true
                shift
                ;;
            --gpg-recipient)
                GPG_RECIPIENT="$2"
                shift 2
                ;;
            --s3-bucket)
                S3_BUCKET="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --restore)
                restore_backup "$2"
                exit $?
                ;;
            --list)
                list_backups
                exit $?
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
}

# Create log file if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Load environment variables if available
if [[ -f "$PROJECT_ROOT/.env.production" ]]; then
    # Source only database-related variables
    eval $(grep -E '^(POSTGRES_|DATABASE_|PGPASSWORD)' "$PROJECT_ROOT/.env.production" | sed 's/POSTGRES_USER/DB_USER/' | sed 's/POSTGRES_PASSWORD/PGPASSWORD/')
fi

# Execute main function
parse_args "$@"
run_backup