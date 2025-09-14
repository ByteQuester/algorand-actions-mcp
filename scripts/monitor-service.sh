#!/bin/bash

# ==============================================================================
# SERVICE MONITOR SCRIPT
# ==============================================================================
# Monitors a Docker container service and ensures it stays healthy
# Used by systemd services for continuous health monitoring
# ==============================================================================

set -euo pipefail

# Parameters
SERVICE_NAME="${1:-unknown}"
CONTAINER_NAME="${2:-unknown}"
SERVICE_PORT="${3:-80}"
CHECK_INTERVAL="${4:-30}"
MAX_FAILURES="${5:-3}"
RESTART_DELAY="${6:-10}"

# Logging
LOG_FILE="/var/log/algorand-lending/${SERVICE_NAME}.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$SERVICE_NAME] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$SERVICE_NAME] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Health check function
check_health() {
    local container_name="$1"
    local port="$2"

    # Check if container is running
    if ! docker ps --filter name="$container_name" --filter status=running --quiet | grep -q .; then
        error "Container $container_name is not running"
        return 1
    fi

    # Check container health status
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")

    if [[ "$health_status" == "unhealthy" ]]; then
        error "Container $container_name is unhealthy"
        return 1
    fi

    # Check if port is responding (optional, for services with HTTP endpoints)
    if command -v curl &> /dev/null; then
        if ! curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
            # Not all services have /health endpoint, so this is just a warning
            log "Warning: Health endpoint not responding on port $port"
        fi
    fi

    return 0
}

# Restart container function
restart_container() {
    local container_name="$1"

    log "Attempting to restart container $container_name"

    if docker restart "$container_name"; then
        log "Container $container_name restarted successfully"
        sleep "$RESTART_DELAY"
        return 0
    else
        error "Failed to restart container $container_name"
        return 1
    fi
}

# Main monitoring loop
main() {
    log "Starting health monitoring for $SERVICE_NAME (container: $CONTAINER_NAME, port: $SERVICE_PORT)"

    local consecutive_failures=0

    while true; do
        if check_health "$CONTAINER_NAME" "$SERVICE_PORT"; then
            if [[ $consecutive_failures -gt 0 ]]; then
                log "Health check passed after $consecutive_failures failures"
                consecutive_failures=0
            fi

            # Send keepalive to systemd
            systemd-notify --ready 2>/dev/null || true
            systemd-notify WATCHDOG=1 2>/dev/null || true

        else
            ((consecutive_failures++))
            error "Health check failed ($consecutive_failures/$MAX_FAILURES)"

            if [[ $consecutive_failures -ge $MAX_FAILURES ]]; then
                error "Maximum failures reached. Attempting restart."

                if restart_container "$CONTAINER_NAME"; then
                    consecutive_failures=0
                    log "Service recovery successful"
                else
                    error "Service recovery failed. Notifying systemd."
                    systemd-notify --status="Service recovery failed" 2>/dev/null || true
                    exit 1
                fi
            fi
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    log "Received termination signal. Stopping monitor for $SERVICE_NAME"
    systemd-notify --stopping 2>/dev/null || true
    exit 0
}

trap cleanup TERM INT

# Start monitoring
main "$@"