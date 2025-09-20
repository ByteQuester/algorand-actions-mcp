#!/bin/bash

# Blockchain Collateral Analyzer Integration Tests Runner
#
# This script provides easy execution of the comprehensive integration testing suite
# for all 6 engines in the blockchain collateral analyzer.

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
INTEGRATION_TESTS_DIR="$PROJECT_ROOT/integration_tests"
VENV_PATH="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
PYTHON_CMD="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Help function
show_help() {
    cat << EOF
Blockchain Collateral Analyzer Integration Tests Runner

USAGE:
    $0 [OPTIONS] [TEST_SUITE]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Run tests with verbose output
    -q, --quiet             Run tests with minimal output
    -f, --fast              Skip slow/stress tests
    -c, --coverage          Run tests with coverage reporting
    -p, --parallel          Run tests in parallel where possible
    -m, --mcp-check         Check MCP services before running tests
    -s, --setup             Setup test environment (install dependencies)
    -r, --report            Generate detailed test report
    --python PATH           Specify Python executable path
    --venv PATH             Specify virtual environment path

TEST_SUITES:
    all                     Run all integration tests (default)
    cross-engine            Run cross-engine workflow tests
    mcp                     Run MCP service integration tests
    e2e                     Run end-to-end lending scenario tests
    performance             Run performance benchmarking tests
    quick                   Run quick smoke tests only
    stress                  Run stress/load tests only

EXAMPLES:
    $0                      # Run all tests with default settings
    $0 -v performance       # Run performance tests with verbose output
    $0 -c -r all            # Run all tests with coverage and generate report
    $0 -m -s quick          # Setup environment, check MCP, run quick tests
    $0 --fast cross-engine  # Run cross-engine tests, skip slow tests

ENVIRONMENT:
    MCP_READER_URL          MCP reader service URL (default: http://localhost:8002)
    MCP_WRITER_URL          MCP writer service URL (default: http://localhost:8003)
    TEST_TIMEOUT            Test timeout in seconds (default: 300)
    PYTEST_WORKERS          Number of parallel workers (default: auto)

EOF
}

# Default configuration
VERBOSE=false
QUIET=false
FAST=false
COVERAGE=false
PARALLEL=false
MCP_CHECK=false
SETUP=false
REPORT=false
TEST_SUITE="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -f|--fast)
            FAST=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -m|--mcp-check)
            MCP_CHECK=true
            shift
            ;;
        -s|--setup)
            SETUP=true
            shift
            ;;
        -r|--report)
            REPORT=true
            shift
            ;;
        --python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        --venv)
            VENV_PATH="$2"
            shift 2
            ;;
        all|cross-engine|mcp|e2e|performance|quick|stress)
            TEST_SUITE="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
validate_environment() {
    log_info "Validating environment..."

    # Check Python
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        log_error "Python executable not found: $PYTHON_CMD"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    log_info "Using Python: $PYTHON_VERSION"

    # Check if we're in the right directory
    if [[ ! -d "$INTEGRATION_TESTS_DIR" ]]; then
        log_error "Integration tests directory not found: $INTEGRATION_TESTS_DIR"
        log_error "Please run this script from the blockchain-collateral-analyzer root directory"
        exit 1
    fi

    # Check project structure
    local missing_dirs=()
    for dir in "collateral-requirements" "digital-asset-valuation" "oracle-price-integration" \
               "portfolio-diversification" "volatility-assessment" "liquidation-scenarios"; do
        if [[ ! -d "$PROJECT_ROOT/$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done

    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        log_warning "Missing engine directories: ${missing_dirs[*]}"
        log_warning "Some tests may fail or be skipped"
    fi
}

# Setup test environment
setup_environment() {
    log_info "Setting up test environment..."

    # Create virtual environment if it doesn't exist
    if [[ ! -d "$VENV_PATH" ]]; then
        log_info "Creating virtual environment at $VENV_PATH"
        $PYTHON_CMD -m venv "$VENV_PATH"
    fi

    # Activate virtual environment
    if [[ -f "$VENV_PATH/bin/activate" ]]; then
        source "$VENV_PATH/bin/activate"
        log_info "Activated virtual environment"
    else
        log_warning "Virtual environment activation script not found"
    fi

    # Upgrade pip
    $PYTHON_CMD -m pip install --upgrade pip

    # Install test dependencies
    log_info "Installing test dependencies..."

    # Install pytest and related packages
    $PYTHON_CMD -m pip install pytest pytest-asyncio pytest-xdist pytest-cov pytest-html pytest-timeout

    # Install performance monitoring dependencies
    $PYTHON_CMD -m pip install psutil memory-profiler

    # Install async HTTP client
    $PYTHON_CMD -m pip install aiohttp

    # Install project requirements if available
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        log_info "Installing project requirements from $REQUIREMENTS_FILE"
        $PYTHON_CMD -m pip install -r "$REQUIREMENTS_FILE"
    fi

    # Install engines in development mode
    for engine_dir in "collateral-requirements" "digital-asset-valuation" "oracle-price-integration" \
                     "portfolio-diversification" "volatility-assessment" "liquidation-scenarios"; do
        if [[ -d "$PROJECT_ROOT/$engine_dir" && -f "$PROJECT_ROOT/$engine_dir/setup.py" ]]; then
            log_info "Installing $engine_dir in development mode"
            cd "$PROJECT_ROOT/$engine_dir"
            $PYTHON_CMD -m pip install -e .
            cd "$PROJECT_ROOT"
        fi
    done

    log_success "Test environment setup completed"
}

# Check MCP services
check_mcp_services() {
    log_info "Checking MCP services..."

    local mcp_reader_url="${MCP_READER_URL:-http://localhost:8002}"
    local mcp_writer_url="${MCP_WRITER_URL:-http://localhost:8003}"

    # Check reader service
    if curl -s --max-time 5 "$mcp_reader_url/health" > /dev/null 2>&1; then
        log_success "MCP Reader service is available at $mcp_reader_url"
    else
        log_warning "MCP Reader service not available at $mcp_reader_url"
        log_warning "Tests will use mock services"
    fi

    # Check writer service
    if curl -s --max-time 5 "$mcp_writer_url/health" > /dev/null 2>&1; then
        log_success "MCP Writer service is available at $mcp_writer_url"
    else
        log_warning "MCP Writer service not available at $mcp_writer_url"
        log_warning "Tests will use mock services"
    fi
}

# Start MCP services if available
start_mcp_services() {
    log_info "Attempting to start MCP services..."

    if [[ -f "$PROJECT_ROOT/start-mcp-services.sh" ]]; then
        log_info "Found MCP services startup script"
        bash "$PROJECT_ROOT/start-mcp-services.sh" &

        # Wait a moment for services to start
        sleep 5

        check_mcp_services
    else
        log_warning "MCP services startup script not found"
        log_warning "Please start MCP services manually if needed"
    fi
}

# Build pytest command
build_pytest_command() {
    local pytest_cmd="$PYTHON_CMD -m pytest"
    local pytest_args=""

    # Add test directory
    pytest_args="$pytest_args $INTEGRATION_TESTS_DIR"

    # Verbosity settings
    if [[ "$VERBOSE" == true ]]; then
        pytest_args="$pytest_args -v -s"
    elif [[ "$QUIET" == true ]]; then
        pytest_args="$pytest_args -q"
    fi

    # Coverage settings
    if [[ "$COVERAGE" == true ]]; then
        pytest_args="$pytest_args --cov=$PROJECT_ROOT --cov-report=html --cov-report=term"
    fi

    # Parallel execution
    if [[ "$PARALLEL" == true ]]; then
        local workers="${PYTEST_WORKERS:-auto}"
        pytest_args="$pytest_args -n $workers"
    fi

    # Test timeout
    local timeout="${TEST_TIMEOUT:-300}"
    pytest_args="$pytest_args --timeout=$timeout"

    # Test selection based on suite
    case "$TEST_SUITE" in
        cross-engine)
            pytest_args="$pytest_args -k test_cross_engine"
            ;;
        mcp)
            pytest_args="$pytest_args integration_tests/test_mcp_integration.py"
            ;;
        e2e)
            pytest_args="$pytest_args integration_tests/test_end_to_end_scenarios.py"
            ;;
        performance)
            pytest_args="$pytest_args integration_tests/test_performance.py"
            ;;
        quick)
            pytest_args="$pytest_args -m 'not slow and not stress'"
            ;;
        stress)
            pytest_args="$pytest_args -m stress"
            ;;
        all)
            # Run all tests
            ;;
    esac

    # Fast mode - skip slow tests
    if [[ "$FAST" == true ]]; then
        pytest_args="$pytest_args -m 'not slow and not stress'"
    fi

    # HTML report
    if [[ "$REPORT" == true ]]; then
        pytest_args="$pytest_args --html=test_report.html --self-contained-html"
    fi

    echo "$pytest_cmd $pytest_args"
}

# Run tests
run_tests() {
    log_info "Running integration tests for suite: $TEST_SUITE"

    # Change to project root
    cd "$PROJECT_ROOT"

    # Build and execute pytest command
    local pytest_command
    pytest_command=$(build_pytest_command)

    log_info "Executing: $pytest_command"

    # Run tests
    if eval "$pytest_command"; then
        log_success "All tests passed!"
        return 0
    else
        log_error "Some tests failed!"
        return 1
    fi
}

# Generate summary report
generate_summary() {
    log_info "Generating test summary..."

    echo
    echo "=================================="
    echo "Integration Test Run Summary"
    echo "=================================="
    echo "Date: $(date)"
    echo "Test Suite: $TEST_SUITE"
    echo "Configuration:"
    echo "  - Verbose: $VERBOSE"
    echo "  - Fast Mode: $FAST"
    echo "  - Coverage: $COVERAGE"
    echo "  - Parallel: $PARALLEL"
    echo "  - MCP Check: $MCP_CHECK"
    echo

    # Display coverage report if available
    if [[ "$COVERAGE" == true && -f "htmlcov/index.html" ]]; then
        log_info "Coverage report generated: htmlcov/index.html"
    fi

    # Display HTML report if available
    if [[ "$REPORT" == true && -f "test_report.html" ]]; then
        log_info "Test report generated: test_report.html"
    fi

    echo "=================================="
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."

    # Kill any background processes (like MCP services we started)
    if [[ -n "$MCP_SERVICES_PID" ]]; then
        kill "$MCP_SERVICES_PID" 2>/dev/null || true
    fi
}

# Main execution
main() {
    log_info "Starting Blockchain Collateral Analyzer Integration Tests"
    log_info "Test Suite: $TEST_SUITE"

    # Setup trap for cleanup
    trap cleanup EXIT

    # Validate environment
    validate_environment

    # Setup if requested
    if [[ "$SETUP" == true ]]; then
        setup_environment
    fi

    # Check or start MCP services if requested
    if [[ "$MCP_CHECK" == true ]]; then
        check_mcp_services

        # Try to start services if they're not running
        if ! curl -s --max-time 2 "${MCP_READER_URL:-http://localhost:8002}/health" > /dev/null 2>&1; then
            start_mcp_services
        fi
    fi

    # Run tests
    local test_result=0
    if ! run_tests; then
        test_result=1
    fi

    # Generate summary
    generate_summary

    # Exit with test result
    exit $test_result
}

# Execute main function
main "$@"