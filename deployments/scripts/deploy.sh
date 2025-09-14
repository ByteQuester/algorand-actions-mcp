#!/bin/bash

# Deployment script for Algorand Customer Lending API
# Agent 2: Strategic Integration API Layer

set -e

echo "🏛️  Algorand Customer Lending API - Deployment Script"
echo "=" * 60

# Configuration
API_PORT=${API_PORT:-8003}
LOG_FILE=${LOG_FILE:-"lending_api.log"}
PID_FILE=${PID_FILE:-"lending_api.pid"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python version
    if ! python3 --version | grep -q "Python 3"; then
        log_error "Python 3 is required"
        exit 1
    fi
    log_success "Python 3 is available"

    # Check virtual environment
    if [ ! -d "/home/mpo/algorand-showcase/venv-adk" ]; then
        log_error "ADK virtual environment not found"
        exit 1
    fi
    log_success "ADK virtual environment found"

    # Check if port is available
    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $API_PORT is already in use"
        read -p "Kill existing process? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill_existing_process
        else
            log_error "Port $API_PORT is not available"
            exit 1
        fi
    fi
    log_success "Port $API_PORT is available"
}

# Function to kill existing process
kill_existing_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            log_info "Stopping existing process (PID: $PID)"
            kill $PID
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                log_warning "Process didn't stop gracefully, forcing kill"
                kill -9 $PID
            fi
            rm -f $PID_FILE
            log_success "Existing process stopped"
        else
            log_warning "PID file exists but process is not running"
            rm -f $PID_FILE
        fi
    else
        # Kill by port
        PID=$(lsof -ti:$API_PORT)
        if [ ! -z "$PID" ]; then
            log_info "Killing process using port $API_PORT (PID: $PID)"
            kill $PID 2>/dev/null || true
            sleep 1
        fi
    fi
}

# Function to start the API server
start_server() {
    log_info "Starting Lending API server..."

    # Activate virtual environment and start server
    source /home/mpo/algorand-showcase/venv-adk/bin/activate

    # Start server in background
    nohup python minimal_api_server.py > $LOG_FILE 2>&1 &
    SERVER_PID=$!

    # Save PID
    echo $SERVER_PID > $PID_FILE

    # Wait a moment and check if server started successfully
    sleep 3

    if kill -0 $SERVER_PID 2>/dev/null; then
        log_success "API server started successfully (PID: $SERVER_PID)"
        log_info "Server logs: $LOG_FILE"
        log_info "Server PID file: $PID_FILE"
    else
        log_error "Failed to start API server"
        log_error "Check logs in $LOG_FILE for details"
        exit 1
    fi
}

# Function to test the API
test_api() {
    log_info "Testing API endpoints..."

    # Wait for server to be fully ready
    sleep 2

    # Test health endpoint
    if curl -s -f http://localhost:$API_PORT/api/v1/health > /dev/null; then
        log_success "Health endpoint is responding"
    else
        log_error "Health endpoint is not responding"
        return 1
    fi

    # Test authentication endpoint
    if curl -s -f -H "Authorization: Bearer test-user" \
       http://localhost:$API_PORT/api/v1/account/balance > /dev/null; then
        log_success "Authentication is working"
    else
        log_warning "Authentication test failed (may need valid token)"
    fi

    log_success "API testing completed"
}

# Function to show server status
show_status() {
    log_info "Server Status:"
    echo "  API URL: http://localhost:$API_PORT"
    echo "  Documentation: http://localhost:$API_PORT/api/v1/docs"
    echo "  Health Check: http://localhost:$API_PORT/api/v1/health"
    echo "  Log File: $LOG_FILE"

    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            echo "  Process Status: Running (PID: $PID)"
        else
            echo "  Process Status: Stopped (stale PID file)"
        fi
    else
        echo "  Process Status: Unknown (no PID file)"
    fi
}

# Function to stop the server
stop_server() {
    log_info "Stopping Lending API server..."
    kill_existing_process
    log_success "Server stopped"
}

# Function to restart the server
restart_server() {
    log_info "Restarting Lending API server..."
    stop_server
    sleep 2
    start_server
    test_api
    show_status
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Last 50 lines of $LOG_FILE ==="
        tail -n 50 $LOG_FILE
    else
        log_warning "Log file $LOG_FILE not found"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the API server"
    echo "  stop      Stop the API server"
    echo "  restart   Restart the API server"
    echo "  status    Show server status"
    echo "  logs      Show recent logs"
    echo "  test      Test API endpoints"
    echo "  deploy    Full deployment (start + test + status)"
    echo "  help      Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  API_PORT    API server port (default: 8003)"
    echo "  LOG_FILE    Log file path (default: lending_api.log)"
    echo "  PID_FILE    PID file path (default: lending_api.pid)"
}

# Main deployment function
deploy() {
    log_info "Starting full deployment..."
    check_prerequisites
    start_server
    test_api
    show_status
    log_success "Deployment completed successfully!"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Test the API: curl http://localhost:$API_PORT/api/v1/health"
    echo "2. View documentation: http://localhost:$API_PORT/api/v1/docs"
    echo "3. Monitor logs: tail -f $LOG_FILE"
    echo "4. Integrate with ADK-Web on port 8000"
}

# Parse command line arguments
case "${1:-deploy}" in
    start)
        check_prerequisites
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_api
        ;;
    deploy)
        deploy
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac