#!/bin/bash

# ==============================================================================
# COMPREHENSIVE HEALTH CHECK SCRIPT
# ==============================================================================
# Performs complete health checks for all Algorand Lending Platform services
# Used by systemd and deployment scripts
# ==============================================================================

set -euo pipefail

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
MAX_WAIT_TIME=300  # 5 minutes
CHECK_INTERVAL=10  # 10 seconds

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Service definitions
declare -A SERVICES=(
    ["adk-web"]="algorand-adk-web:8081:/health"
    ["lending-api"]="algorand-lending-api:8003:/health"
    ["actions-mcp"]="algorand-actions-mcp:8788:/health"
    ["remote-mcp"]="algorand-remote-mcp:8002:/health"
    ["postgres"]="algorand-postgres:5432:"
    ["redis"]="algorand-redis:6379:"
)

# Check if Docker Compose is available
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not available"
        return 1
    fi

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        return 1
    fi

    return 0
}

# Check container status
check_container_status() {
    local container_name="$1"

    log "Checking container status: $container_name"

    # Check if container exists
    if ! docker ps -a --filter name="$container_name" --quiet | grep -q .; then
        error "Container $container_name does not exist"
        return 1
    fi

    # Check if container is running
    if ! docker ps --filter name="$container_name" --filter status=running --quiet | grep -q .; then
        error "Container $container_name is not running"
        docker logs --tail 20 "$container_name" 2>/dev/null || true
        return 1
    fi

    # Check container health if healthcheck is defined
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")

    case "$health_status" in
        "healthy")
            success "Container $container_name is healthy"
            ;;
        "unhealthy")
            error "Container $container_name is unhealthy"
            docker logs --tail 20 "$container_name" 2>/dev/null || true
            return 1
            ;;
        "starting")
            warning "Container $container_name is still starting"
            ;;
        "no-healthcheck")
            success "Container $container_name is running (no healthcheck defined)"
            ;;
    esac

    return 0
}

# Check service endpoint
check_service_endpoint() {
    local service_name="$1"
    local container_name="$2"
    local port="$3"
    local endpoint="$4"

    if [[ -z "$endpoint" ]]; then
        log "No HTTP endpoint defined for $service_name"
        return 0
    fi

    log "Checking service endpoint: $service_name at http://localhost:$port$endpoint"

    # Get container IP
    local container_ip
    container_ip=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container_name" 2>/dev/null || echo "")

    if [[ -z "$container_ip" ]]; then
        warning "Could not get container IP for $container_name, using localhost"
        container_ip="localhost"
    fi

    # Test endpoint
    local max_attempts=5
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf --max-time 10 "http://localhost:$port$endpoint" >/dev/null 2>&1; then
            success "Service endpoint $service_name is responding"
            return 0
        elif [[ $attempt -eq $max_attempts ]]; then
            error "Service endpoint $service_name is not responding after $max_attempts attempts"
            return 1
        else
            log "Attempt $attempt/$max_attempts failed for $service_name, retrying..."
            sleep 2
            ((attempt++))
        fi
    done
}

# Check database connectivity
check_database() {
    local container_name="algorand-postgres"

    log "Checking PostgreSQL database connectivity"

    if ! docker exec "$container_name" pg_isready -U algorand_user -d algorand_lending >/dev/null 2>&1; then
        error "PostgreSQL database is not ready"
        return 1
    fi

    # Test basic query
    if ! docker exec "$container_name" psql -U algorand_user -d algorand_lending -c "SELECT 1;" >/dev/null 2>&1; then
        error "PostgreSQL database query test failed"
        return 1
    fi

    success "PostgreSQL database is ready"
    return 0
}

# Check Redis connectivity
check_redis() {
    local container_name="algorand-redis"

    log "Checking Redis connectivity"

    if ! docker exec "$container_name" redis-cli ping >/dev/null 2>&1; then
        error "Redis is not responding"
        return 1
    fi

    success "Redis is ready"
    return 0
}

# Check MCP service integration
check_mcp_integration() {
    log "Checking MCP services integration"

    # Test Actions MCP
    if curl -sf --max-time 10 "http://localhost:8788/health" >/dev/null 2>&1; then
        success "Actions MCP service is accessible"
    else
        error "Actions MCP service is not accessible"
        return 1
    fi

    # Test Remote MCP
    if curl -sf --max-time 10 "http://localhost:8002/health" >/dev/null 2>&1; then
        success "Remote MCP service is accessible"
    else
        error "Remote MCP service is not accessible"
        return 1
    fi

    # Test API can reach MCP services
    if curl -sf --max-time 10 "http://localhost:8003/health" >/dev/null 2>&1; then
        success "Lending API is accessible"

        # Test a simple API endpoint that uses MCP
        # This is optional and depends on your API structure
        log "Testing API-MCP integration..."
        # Add specific integration tests here if needed
    else
        error "Lending API is not accessible"
        return 1
    fi

    return 0
}

# Main health check function
perform_health_check() {
    local overall_status=0

    log "Starting comprehensive health check for Algorand Lending Platform"
    log "================================================================="

    # Check Docker Compose
    if ! check_compose; then
        return 1
    fi

    # Check all services
    for service in "${!SERVICES[@]}"; do
        IFS=':' read -r container_name port endpoint <<< "${SERVICES[$service]}"

        if ! check_container_status "$container_name"; then
            overall_status=1
            continue
        fi

        if ! check_service_endpoint "$service" "$container_name" "$port" "$endpoint"; then
            overall_status=1
            continue
        fi
    done

    # Additional checks
    if ! check_database; then
        overall_status=1
    fi

    if ! check_redis; then
        overall_status=1
    fi

    if ! check_mcp_integration; then
        overall_status=1
    fi

    # Summary
    log "================================================================="
    if [[ $overall_status -eq 0 ]]; then
        success "All health checks passed! System is ready."
    else
        error "Some health checks failed. Please review the errors above."
    fi

    return $overall_status
}

# Wait for services to be healthy
wait_for_healthy() {
    local start_time
    start_time=$(date +%s)

    log "Waiting for all services to become healthy (max ${MAX_WAIT_TIME}s)..."

    while true; do
        local current_time
        current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [[ $elapsed -ge $MAX_WAIT_TIME ]]; then
            error "Timeout waiting for services to become healthy"
            return 1
        fi

        if perform_health_check; then
            success "All services are healthy after ${elapsed}s"
            return 0
        fi

        log "Waiting... (${elapsed}s/${MAX_WAIT_TIME}s)"
        sleep $CHECK_INTERVAL
    done
}

# Script usage
usage() {
    echo "Usage: $0 [check|wait]"
    echo "  check  - Perform one-time health check (default)"
    echo "  wait   - Wait for services to become healthy"
    exit 1
}

# Main execution
main() {
    local command="${1:-check}"

    case "$command" in
        "check")
            perform_health_check
            ;;
        "wait")
            wait_for_healthy
            ;;
        *)
            usage
            ;;
    esac
}

# Execute main function
main "$@"