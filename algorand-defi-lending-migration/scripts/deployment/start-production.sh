#!/bin/bash
set -e

echo "🚀 Starting Algorand Showcase Production Environment"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$DEPLOYMENT_DIR")"

echo "📁 Deployment directory: $DEPLOYMENT_DIR"

# Check if production environment file exists
ENV_FILE="$DEPLOYMENT_DIR/production/configs/.env.production"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Production environment file not found: $ENV_FILE"
    echo "   Please copy .env.production.template and configure with real values"
    exit 1
fi

# Load environment variables
source "$ENV_FILE"

# Validate required environment variables
REQUIRED_VARS=("DB_USER" "DB_PASSWORD" "JWT_SECRET")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   %s\n' "${MISSING_VARS[@]}"
    exit 1
fi

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p "$DEPLOYMENT_DIR/production/monitoring"
mkdir -p "$DEPLOYMENT_DIR/production/secrets"
mkdir -p /var/log/lending-api

# Ensure proper permissions
chmod 755 "$DEPLOYMENT_DIR/production/monitoring"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check Docker Compose version
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "🏗️  Building and starting production services..."
cd "$DEPLOYMENT_DIR/docker"

# Build images without cache to ensure latest code
docker compose -f docker-compose.production.yml build --no-cache

# Start services with production configuration
docker compose -f docker-compose.production.yml up -d

echo "⏳ Waiting for services to be healthy..."

# Function to check service health
check_health() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f "$url" > /dev/null 2>&1; then
            echo "✅ $service is healthy"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done

    echo "❌ $service failed to become healthy"
    return 1
}

# Check each service
check_health "PostgreSQL Database" "http://localhost:5432" || {
    echo "   Note: Direct HTTP check may fail, checking Docker health..."
    docker compose -f docker-compose.production.yml ps postgres
}

check_health "Remote MCP Service" "http://localhost:8002/health"
check_health "Actions MCP Service" "http://localhost:3001/health"
check_health "Lending API" "http://localhost:8003/health"

echo ""
echo "🎉 Production environment started successfully!"
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.production.yml ps

echo ""
echo "🔗 Service URLs:"
echo "   Lending API:     http://localhost:8003"
echo "   Remote MCP:      http://localhost:8002"
echo "   Actions MCP:     http://localhost:3001"
echo "   Nginx Proxy:     http://localhost"
echo ""

echo "📋 Management Commands:"
echo "   View logs:       docker compose -f docker-compose.production.yml logs -f [service]"
echo "   Stop services:   docker compose -f docker-compose.production.yml down"
echo "   Restart:         docker compose -f docker-compose.production.yml restart [service]"
echo ""

echo "📈 Monitoring:"
echo "   Logs directory:  $DEPLOYMENT_DIR/production/monitoring"
echo "   Database logs:   docker compose -f docker-compose.production.yml logs postgres"
echo ""

echo "🔧 Production environment ready for deployment!"

# Optional: Run health checks on all services
if [ "$1" = "--verify" ]; then
    echo "🔍 Running comprehensive health checks..."

    # Test database connection
    echo "   Testing database connection..."
    docker compose -f docker-compose.production.yml exec postgres psql -U $DB_USER -d algorand_lending -c "SELECT 1;" > /dev/null

    # Test API endpoints
    echo "   Testing API endpoints..."
    curl -f http://localhost:8003/health > /dev/null
    curl -f http://localhost:8002/health > /dev/null
    curl -f http://localhost:3001/health > /dev/null

    echo "✅ All health checks passed!"
fi