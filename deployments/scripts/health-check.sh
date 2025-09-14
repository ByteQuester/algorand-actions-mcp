#!/bin/bash

# 🔍 Algorand Lending Platform - Health Check Script
# Comprehensive health monitoring for all services

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
LOG_FILE="/var/log/lending-platform-health.log"
TIMEOUT=10
RETRIES=3
VERBOSE=false
JSON_OUTPUT=false

# Service endpoints
declare -A ENDPOINTS=(
    ["api"]="http://localhost:8003/api/v1/health"
    ["ui"]="http://localhost:8081/health"
    ["mcp-reader"]="http://localhost:8002/health"
    ["mcp-writer"]="http://localhost:3001/health"
)

# Service names for systemd
declare -A SERVICES=(
    ["api"]="lending-api"
    ["ui"]="lending-ui"
)

# Database configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="lending_db"
DB_USER="lending_user"

# Results tracking
declare -A RESULTS=()
FAILED_CHECKS=0
TOTAL_CHECKS=0

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
    ((FAILED_CHECKS++))
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
🔍 Algorand Lending Platform - Health Check

Usage: $0 [OPTIONS]

OPTIONS:
    --all               Check all services (default)
    --service <name>    Check specific service (api|ui|mcp|database|nginx)
    --endpoint <url>    Check specific endpoint
    --timeout <sec>     Request timeout in seconds (default: 10)
    --retries <num>     Number of retries (default: 3)
    --verbose           Verbose output
    --json              Output results in JSON format
    --continuous        Run continuously every 30 seconds (Ctrl+C to stop)
    --help              Show this help message

SERVICES:
    api        Lending API service
    ui         Lending UI service
    mcp        MCP services (reader/writer)
    database   PostgreSQL database
    nginx      Reverse proxy server
    all        All services (default)

EXAMPLES:
    $0                           # Check all services
    $0 --service api            # Check only API
    $0 --service database       # Check database connectivity
    $0 --verbose --json         # Detailed output in JSON
    $0 --continuous             # Monitor continuously

EOF
}

# HTTP health check with retry logic
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    ((TOTAL_CHECKS++))

    info "Checking $name endpoint: $url"

    for ((i=1; i<=RETRIES; i++)); do
        local start_time=$(date +%s.%N)

        if response=$(curl -s -f -m "$TIMEOUT" -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" "$url" 2>/dev/null); then
            local end_time=$(date +%s.%N)
            local response_time=$(echo "scale=0; ($end_time - $start_time) * 1000 / 1" | bc)

            local http_status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
            local time_total=$(echo "$response" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
            local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*;TIME:[0-9.]*$//')

            if [[ "$http_status" == "$expected_status" ]]; then
                success "$name: Healthy (${time_total}s response time)"
                RESULTS["$name"]="healthy|$http_status|$time_total"
                return 0
            else
                warning "$name: Unexpected status code $http_status (attempt $i/$RETRIES)"
            fi
        else
            warning "$name: Connection failed (attempt $i/$RETRIES)"
        fi

        if [[ $i -lt $RETRIES ]]; then
            sleep 2
        fi
    done

    error "$name: Health check failed after $RETRIES attempts"
    RESULTS["$name"]="failed|0|0"
    return 1
}

# Database connectivity check
check_database() {
    ((TOTAL_CHECKS++))

    info "Checking database connectivity..."

    # Check if PostgreSQL is listening
    if ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        error "Database: Port $DB_PORT not accessible on $DB_HOST"
        RESULTS["database"]="failed|connection|0"
        return 1
    fi

    # Check database connection and query
    for ((i=1; i<=RETRIES; i++)); do
        local start_time=$(date +%s.%N)

        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            local end_time=$(date +%s.%N)
            local response_time=$(echo "scale=3; ($end_time - $start_time)" | bc)

            # Test actual query
            if echo "SELECT 1;" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
                success "Database: Connected and responsive (${response_time}s)"
                RESULTS["database"]="healthy|connected|$response_time"
                return 0
            else
                warning "Database: Connected but query failed (attempt $i/$RETRIES)"
            fi
        else
            warning "Database: Connection failed (attempt $i/$RETRIES)"
        fi

        if [[ $i -lt $RETRIES ]]; then
            sleep 2
        fi
    done

    error "Database: Connection failed after $RETRIES attempts"
    RESULTS["database"]="failed|query|0"
    return 1
}

# Systemd service check
check_systemd_service() {
    local service_name=$1
    local display_name=$2

    ((TOTAL_CHECKS++))

    info "Checking systemd service: $service_name"

    if systemctl is-active --quiet "$service_name"; then
        if systemctl is-enabled --quiet "$service_name"; then
            success "$display_name: Service running and enabled"
            RESULTS["${display_name,,}"]="healthy|active|enabled"
            return 0
        else
            warning "$display_name: Service running but not enabled"
            RESULTS["${display_name,,}"]="warning|active|disabled"
            return 1
        fi
    else
        local status=$(systemctl is-active "$service_name" 2>/dev/null || echo "unknown")
        error "$display_name: Service not running (status: $status)"
        RESULTS["${display_name,,}"]="failed|$status|unknown"
        return 1
    fi
}

# Docker container health check
check_docker_containers() {
    ((TOTAL_CHECKS++))

    info "Checking Docker containers..."

    if ! command -v docker >/dev/null 2>&1; then
        warning "Docker: Command not found, skipping container checks"
        return 0
    fi

    local compose_file="$PROJECT_ROOT/deployments/docker-compose.production.yml"
    if [[ ! -f "$compose_file" ]]; then
        info "Docker: No production compose file found, skipping"
        return 0
    fi

    local containers=$(docker-compose -f "$compose_file" ps --services 2>/dev/null || echo "")
    if [[ -z "$containers" ]]; then
        info "Docker: No containers defined in compose file"
        return 0
    fi

    local failed_containers=()
    local healthy_containers=()

    while IFS= read -r container; do
        if [[ -n "$container" ]]; then
            local status=$(docker-compose -f "$compose_file" ps "$container" 2>/dev/null | tail -n +3 | awk '{print $NF}')

            if [[ "$status" =~ "Up" ]]; then
                if [[ "$status" =~ "healthy" ]]; then
                    healthy_containers+=("$container")
                else
                    warning "Docker: $container is up but not healthy"
                fi
            else
                failed_containers+=("$container")
                error "Docker: $container is not running (status: $status)"
            fi
        fi
    done <<< "$containers"

    if [[ ${#failed_containers[@]} -eq 0 ]]; then
        success "Docker: All containers are running (${#healthy_containers[@]} healthy)"
        RESULTS["docker"]="healthy|${#healthy_containers[@]}|${#failed_containers[@]}"
        return 0
    else
        error "Docker: ${#failed_containers[@]} containers failed: ${failed_containers[*]}"
        RESULTS["docker"]="failed|${#healthy_containers[@]}|${#failed_containers[@]}"
        return 1
    fi
}

# SSL certificate check
check_ssl_certificates() {
    ((TOTAL_CHECKS++))

    info "Checking SSL certificates..."

    local cert_path="/etc/letsencrypt/live"
    if [[ ! -d "$cert_path" ]]; then
        warning "SSL: Let's Encrypt directory not found"
        RESULTS["ssl"]="warning|no_letsencrypt|0"
        return 1
    fi

    local domains=$(find "$cert_path" -maxdepth 1 -type d -not -path "$cert_path" -exec basename {} \; 2>/dev/null || echo "")

    if [[ -z "$domains" ]]; then
        warning "SSL: No certificates found"
        RESULTS["ssl"]="warning|no_certificates|0"
        return 1
    fi

    local expired_certs=()
    local valid_certs=()

    while IFS= read -r domain; do
        if [[ -n "$domain" ]]; then
            local cert_file="$cert_path/$domain/cert.pem"

            if [[ -f "$cert_file" ]]; then
                local expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
                local expiry_epoch=$(date -d "$expiry_date" +%s)
                local current_epoch=$(date +%s)
                local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))

                if [[ $days_until_expiry -lt 0 ]]; then
                    expired_certs+=("$domain")
                    error "SSL: Certificate for $domain expired $((days_until_expiry * -1)) days ago"
                elif [[ $days_until_expiry -lt 30 ]]; then
                    warning "SSL: Certificate for $domain expires in $days_until_expiry days"
                    valid_certs+=("$domain")
                else
                    valid_certs+=("$domain")
                    if [[ "$VERBOSE" == true ]]; then
                        success "SSL: Certificate for $domain valid ($days_until_expiry days remaining)"
                    fi
                fi
            else
                error "SSL: Certificate file not found for $domain"
            fi
        fi
    done <<< "$domains"

    if [[ ${#expired_certs[@]} -eq 0 ]]; then
        success "SSL: All certificates are valid (${#valid_certs[@]} certificates)"
        RESULTS["ssl"]="healthy|${#valid_certs[@]}|0"
        return 0
    else
        error "SSL: ${#expired_certs[@]} certificates expired: ${expired_certs[*]}"
        RESULTS["ssl"]="failed|${#valid_certs[@]}|${#expired_certs[@]}"
        return 1
    fi
}

# System resources check
check_system_resources() {
    ((TOTAL_CHECKS++))

    info "Checking system resources..."

    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local available_gb=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')

    if [[ $disk_usage -gt 85 ]]; then
        error "System: Disk usage critical ($disk_usage%, ${available_gb}GB available)"
        RESULTS["disk"]="failed|$disk_usage|$available_gb"
    elif [[ $disk_usage -gt 75 ]]; then
        warning "System: Disk usage high ($disk_usage%, ${available_gb}GB available)"
        RESULTS["disk"]="warning|$disk_usage|$available_gb"
    else
        success "System: Disk usage healthy ($disk_usage%, ${available_gb}GB available)"
        RESULTS["disk"]="healthy|$disk_usage|$available_gb"
    fi

    # Check memory usage
    local memory_info=$(free | grep Mem)
    local total_mem=$(echo "$memory_info" | awk '{print $2}')
    local used_mem=$(echo "$memory_info" | awk '{print $3}')
    local memory_percent=$(( (used_mem * 100) / total_mem ))
    local available_mem_gb=$(( (total_mem - used_mem) / 1024 / 1024 ))

    if [[ $memory_percent -gt 85 ]]; then
        error "System: Memory usage critical ($memory_percent%, ${available_mem_gb}GB available)"
        RESULTS["memory"]="failed|$memory_percent|$available_mem_gb"
    elif [[ $memory_percent -gt 75 ]]; then
        warning "System: Memory usage high ($memory_percent%, ${available_mem_gb}GB available)"
        RESULTS["memory"]="warning|$memory_percent|$available_mem_gb"
    else
        success "System: Memory usage healthy ($memory_percent%, ${available_mem_gb}GB available)"
        RESULTS["memory"]="healthy|$memory_percent|$available_mem_gb"
    fi

    # Check load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_count=$(nproc)
    local load_percent=$(echo "scale=0; $load_avg * 100 / $cpu_count" | bc)

    if [[ $load_percent -gt 80 ]]; then
        error "System: Load average high ($load_avg on $cpu_count cores)"
        RESULTS["load"]="failed|$load_avg|$cpu_count"
    elif [[ $load_percent -gt 60 ]]; then
        warning "System: Load average elevated ($load_avg on $cpu_count cores)"
        RESULTS["load"]="warning|$load_avg|$cpu_count"
    else
        success "System: Load average normal ($load_avg on $cpu_count cores)"
        RESULTS["load"]="healthy|$load_avg|$cpu_count"
    fi
}

# Generate JSON output
output_json() {
    local timestamp=$(date -Iseconds)
    local overall_status="healthy"

    if [[ $FAILED_CHECKS -gt 0 ]]; then
        overall_status="unhealthy"
    fi

    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"overall_status\": \"$overall_status\","
    echo "  \"total_checks\": $TOTAL_CHECKS,"
    echo "  \"failed_checks\": $FAILED_CHECKS,"
    echo "  \"checks\": {"

    local first=true
    for service in "${!RESULTS[@]}"; do
        local result="${RESULTS[$service]}"
        local status=$(echo "$result" | cut -d'|' -f1)
        local detail1=$(echo "$result" | cut -d'|' -f2)
        local detail2=$(echo "$result" | cut -d'|' -f3)

        if [[ "$first" == true ]]; then
            first=false
        else
            echo ","
        fi

        echo -n "    \"$service\": {"
        echo -n "\"status\": \"$status\", \"detail1\": \"$detail1\", \"detail2\": \"$detail2\""
        echo -n "}"
    done

    echo ""
    echo "  }"
    echo "}"
}

# Main health check function
run_health_checks() {
    local service_filter="$1"

    # Reset counters
    FAILED_CHECKS=0
    TOTAL_CHECKS=0
    RESULTS=()

    echo -e "${CYAN}🔍 Algorand Lending Platform Health Check${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo

    case "$service_filter" in
        "api")
            check_endpoint "Lending API" "${ENDPOINTS[api]}"
            check_systemd_service "${SERVICES[api]}" "Lending API"
            ;;
        "ui")
            check_endpoint "Lending UI" "${ENDPOINTS[ui]}"
            check_systemd_service "${SERVICES[ui]}" "Lending UI"
            ;;
        "mcp")
            check_endpoint "MCP Reader" "${ENDPOINTS[mcp-reader]}"
            check_endpoint "MCP Writer" "${ENDPOINTS[mcp-writer]}"
            ;;
        "database")
            check_database
            ;;
        "nginx")
            check_systemd_service "nginx" "Nginx"
            ;;
        "system")
            check_system_resources
            ;;
        "ssl")
            check_ssl_certificates
            ;;
        "docker")
            check_docker_containers
            ;;
        "all"|*)
            # Check all services
            for service in "${!ENDPOINTS[@]}"; do
                check_endpoint "${service^}" "${ENDPOINTS[$service]}"
            done

            for service in "${!SERVICES[@]}"; do
                check_systemd_service "${SERVICES[$service]}" "${service^}"
            done

            check_database
            check_systemd_service "nginx" "Nginx"
            check_docker_containers
            check_ssl_certificates
            check_system_resources
            ;;
    esac

    echo
    echo -e "${CYAN}===========================================${NC}"

    if [[ $FAILED_CHECKS -eq 0 ]]; then
        success "All health checks passed! ($TOTAL_CHECKS/$TOTAL_CHECKS)"
        echo -e "${GREEN}🎉 Algorand Lending Platform is healthy!${NC}"
    else
        error "$FAILED_CHECKS out of $TOTAL_CHECKS health checks failed"
        echo -e "${RED}⚠️  Algorand Lending Platform needs attention!${NC}"
    fi

    if [[ "$JSON_OUTPUT" == true ]]; then
        echo
        output_json
    fi

    return $FAILED_CHECKS
}

# Parse command line arguments
parse_args() {
    local service_filter="all"
    local continuous=false
    local custom_endpoint=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --service)
                service_filter="$2"
                shift 2
                ;;
            --endpoint)
                custom_endpoint="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --retries)
                RETRIES="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --continuous)
                continuous=true
                shift
                ;;
            --all)
                service_filter="all"
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

    # Handle custom endpoint
    if [[ -n "$custom_endpoint" ]]; then
        check_endpoint "Custom Endpoint" "$custom_endpoint"
        exit $?
    fi

    # Handle continuous monitoring
    if [[ "$continuous" == true ]]; then
        echo -e "${BLUE}Starting continuous health monitoring (Ctrl+C to stop)...${NC}"
        echo

        while true; do
            run_health_checks "$service_filter"

            if [[ $FAILED_CHECKS -gt 0 ]]; then
                echo -e "${RED}Waiting 30 seconds before next check...${NC}"
            else
                echo -e "${GREEN}Waiting 30 seconds before next check...${NC}"
            fi

            sleep 30
            echo
            echo -e "${CYAN}$(date): Running health checks...${NC}"
        done
    else
        run_health_checks "$service_filter"
        exit $FAILED_CHECKS
    fi
}

# Create log file if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Execute main function
parse_args "$@"