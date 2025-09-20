#!/bin/bash
# Algorand DeFi Lending Platform - Setup Script

set -e

echo "🏦 Setting up Algorand DeFi Lending Platform..."

# Check dependencies
check_dependencies() {
    echo "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is required but not installed"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required but not installed"
        exit 1
    fi

    echo "✅ All dependencies found"
}

# Install Python dependencies
setup_python() {
    echo "Setting up Python environment..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    pip install -r requirements.txt

    echo "✅ Python environment ready"
}

# Setup Node.js packages
setup_nodejs() {
    echo "Setting up Node.js packages..."

    # Install pnpm globally if not present
    if ! command -v pnpm &> /dev/null; then
        npm install -g pnpm
    fi

    # Install and build packages
    cd src/packages
    pnpm install
    pnpm run build

    # Install and build MCP services
    cd ../mcp-services
    for service in */; do
        echo "Building $service..."
        cd "$service"
        pnpm install
        pnpm run build
        cd ..
    done

    cd ../..
    echo "✅ Node.js packages ready"
}

# Setup database
setup_database() {
    echo "Setting up database..."

    if [ "$1" = "docker" ]; then
        # Start PostgreSQL with Docker
        docker run -d \
            --name defi-postgres \
            -e POSTGRES_PASSWORD=password \
            -e POSTGRES_DB=defi_core_db \
            -p 5432:5432 \
            postgres:15

        # Wait for database to be ready
        echo "Waiting for database to start..."
        sleep 10

        # Apply schema
        docker exec -i defi-postgres psql -U postgres -d defi_core_db < database/schema.sql
        docker exec -i defi-postgres psql -U postgres -d defi_core_db < database/seed-data.sql

    else
        echo "Please ensure PostgreSQL is running and execute:"
        echo "  psql -U postgres -d defi_core_db < database/schema.sql"
        echo "  psql -U postgres -d defi_core_db < database/seed-data.sql"
    fi

    echo "✅ Database setup complete"
}

# Setup Redis
setup_redis() {
    echo "Setting up Redis..."

    if [ "$1" = "docker" ]; then
        # Start Redis with Docker
        docker run -d \
            --name defi-redis \
            -p 6379:6379 \
            redis:7-alpine
    else
        echo "Please ensure Redis is running on port 6379"
    fi

    echo "✅ Redis setup complete"
}

# Create environment file
setup_env() {
    echo "Setting up environment..."

    if [ ! -f ".env" ]; then
        cp config/env-template.yaml .env.yaml
        echo "📝 Created .env.yaml from template"
        echo "   Please update with your specific configuration"
    fi

    echo "✅ Environment file ready"
}

# Run tests
run_tests() {
    echo "Running tests..."

    source venv/bin/activate
    export PYTHONPATH=$PWD/src:$PWD

    # Run Python tests
    pytest tests/ -v

    echo "✅ Tests passed"
}

# Main setup function
main() {
    case "$1" in
        full)
            check_dependencies
            setup_python
            setup_nodejs
            setup_database docker
            setup_redis docker
            setup_env
            run_tests
            echo "🎉 Full setup complete!"
            ;;
        dev)
            check_dependencies
            setup_python
            setup_nodejs
            setup_env
            echo "🎉 Development setup complete!"
            echo "   Remember to start PostgreSQL and Redis manually"
            ;;
        docker)
            check_dependencies
            setup_database docker
            setup_redis docker
            echo "🎉 Docker services started!"
            ;;
        test)
            run_tests
            ;;
        *)
            echo "Usage: $0 {full|dev|docker|test}"
            echo "  full   - Complete setup with Docker services"
            echo "  dev    - Development setup (no Docker services)"
            echo "  docker - Start only Docker services"
            echo "  test   - Run test suite"
            exit 1
            ;;
    esac
}

main "$@"