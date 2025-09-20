#!/bin/bash
#
# Installation script for blockchain-collateral-analyzer package
#
# This script provides an easy way to install the blockchain-collateral-analyzer
# package with all its dependencies and CLI tools.
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="blockchain-collateral-analyzer"
PYTHON_MIN_VERSION="3.8"
VENV_NAME="collateral-analyzer-env"

# Helper functions
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

check_python_version() {
    log_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    required_version=$(echo -e "$python_version\n$PYTHON_MIN_VERSION" | sort -V | head -n1)

    if [ "$required_version" != "$PYTHON_MIN_VERSION" ]; then
        log_error "Python $PYTHON_MIN_VERSION or higher is required. Found: $python_version"
        exit 1
    fi

    log_success "Python $python_version detected"
}

check_pip() {
    log_info "Checking pip installation..."

    if ! command -v pip3 &> /dev/null; then
        log_warning "pip3 not found. Attempting to install..."
        python3 -m ensurepip --upgrade
    fi

    log_success "pip is available"
}

create_virtual_environment() {
    if [ "$USE_VENV" = "true" ]; then
        log_info "Creating virtual environment: $VENV_NAME"

        if [ -d "$VENV_NAME" ]; then
            log_warning "Virtual environment already exists. Removing..."
            rm -rf "$VENV_NAME"
        fi

        python3 -m venv "$VENV_NAME"
        source "$VENV_NAME/bin/activate"

        # Upgrade pip in the virtual environment
        pip install --upgrade pip

        log_success "Virtual environment created and activated"
    else
        log_info "Installing in system Python environment"
    fi
}

install_package() {
    log_info "Installing $PACKAGE_NAME package..."

    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"

    cd "$PACKAGE_DIR"

    if [ "$INSTALL_DEV" = "true" ]; then
        log_info "Installing in development mode with dev dependencies..."
        pip install -e ".[dev]"
    else
        log_info "Installing package..."
        pip install .
    fi

    log_success "Package installation completed"
}

verify_installation() {
    log_info "Verifying installation..."

    # Check if the main CLI command is available
    if command -v collateral-analyzer &> /dev/null; then
        log_success "Main CLI command 'collateral-analyzer' is available"
    else
        log_warning "Main CLI command not found in PATH"
    fi

    # Check individual engine commands
    engines=("asset-valuation" "volatility-assessment" "liquidation-scenarios" "oracle-integration" "portfolio-analysis" "collateral-requirements")

    for engine in "${engines[@]}"; do
        if command -v "$engine" &> /dev/null; then
            log_success "Engine CLI '$engine' is available"
        else
            log_warning "Engine CLI '$engine' not found in PATH"
        fi
    done

    # Test Python import
    if python3 -c "import blockchain_collateral_analyzer; print('Import successful')" &> /dev/null; then
        log_success "Python package import successful"
    else
        log_error "Python package import failed"
        return 1
    fi

    # Check engine availability
    log_info "Checking engine availability..."
    python3 -c "
import sys
sys.path.insert(0, '.')
from __init__ import check_engine_availability
check_engine_availability()
"
}

create_config_files() {
    log_info "Creating configuration files..."

    # Create a basic configuration directory
    mkdir -p ~/.config/blockchain-collateral-analyzer

    # Create a sample configuration file
    cat > ~/.config/blockchain-collateral-analyzer/config.json << EOF
{
    "default_currency": "USD",
    "oracle_timeout": 30,
    "cache_duration": 300,
    "log_level": "INFO",
    "engines": {
        "digital_asset_valuation": {
            "enabled": true,
            "default_sources": ["coingecko", "algorand"]
        },
        "volatility_assessment": {
            "enabled": true,
            "default_period": 30,
            "confidence_level": 0.95
        },
        "liquidation_scenarios": {
            "enabled": true,
            "default_threshold": 0.75
        },
        "oracle_price_integration": {
            "enabled": true,
            "preferred_oracle": "algorand"
        },
        "portfolio_diversification": {
            "enabled": true
        },
        "collateral_requirements": {
            "enabled": true,
            "default_profile": "moderate"
        }
    }
}
EOF

    log_success "Configuration files created in ~/.config/blockchain-collateral-analyzer/"
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev              Install in development mode with dev dependencies"
    echo "  --venv             Create and use a virtual environment"
    echo "  --system           Install in system Python (default)"
    echo "  --no-config        Skip configuration file creation"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Standard installation"
    echo "  $0 --dev --venv    # Development installation in virtual environment"
    echo "  $0 --system        # System-wide installation"
}

print_completion_message() {
    echo ""
    echo "=============================================="
    log_success "Installation completed successfully!"
    echo "=============================================="
    echo ""
    echo "Available CLI commands:"
    echo "  collateral-analyzer         # Main CLI interface"
    echo "  asset-valuation            # Digital asset valuation"
    echo "  volatility-assessment      # Volatility and VaR analysis"
    echo "  liquidation-scenarios      # Liquidation modeling"
    echo "  oracle-integration         # Oracle price feeds"
    echo "  portfolio-analysis         # Portfolio diversification"
    echo "  collateral-requirements    # Collateral calculations"
    echo ""
    echo "Example usage:"
    echo "  collateral-analyzer --check-engines"
    echo "  asset-valuation --asset-id ALGO --amount 1000"
    echo "  volatility-assessment --asset-id ALGO --period 30"
    echo ""

    if [ "$USE_VENV" = "true" ]; then
        echo "Virtual environment: $VENV_NAME"
        echo "To activate: source $VENV_NAME/bin/activate"
        echo ""
    fi

    echo "Configuration: ~/.config/blockchain-collateral-analyzer/"
    echo "Documentation: README.md"
    echo ""
}

# Main installation logic
main() {
    log_info "Starting blockchain-collateral-analyzer installation..."

    # Parse command line arguments
    INSTALL_DEV=false
    USE_VENV=false
    CREATE_CONFIG=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                INSTALL_DEV=true
                shift
                ;;
            --venv)
                USE_VENV=true
                shift
                ;;
            --system)
                USE_VENV=false
                shift
                ;;
            --no-config)
                CREATE_CONFIG=false
                shift
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done

    # Pre-installation checks
    check_python_version
    check_pip

    # Installation steps
    create_virtual_environment
    install_package

    # Post-installation steps
    verify_installation

    if [ "$CREATE_CONFIG" = "true" ]; then
        create_config_files
    fi

    # Completion
    print_completion_message
}

# Handle script interruption
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"