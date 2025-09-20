#!/bin/bash

# Startup script for MCP services supporting the collateral analyzer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
ALGORAND_READER_DIR="/home/mpo/algorand-showcase/apps/mcp-services/algorand-reader-mcp"
MARKET_DATA_DIR="/home/mpo/algorand-showcase/apps/mcp-services/market-data-mcp"
BASE_DIR="/home/mpo/algorand-showcase/algorand-lending-ecosystem/business-logic-engines/blockchain-collateral-analyzer"

echo -e "${BLUE}🚀 Starting MCP Services for Collateral Analyzer${NC}"
echo "=================================================="

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    local start_command=$4

    echo -e "${YELLOW}Starting ${service_name} on port ${port}...${NC}"

    if check_port $port; then
        echo -e "${GREEN}✅ ${service_name} already running on port ${port}${NC}"
        return
    fi

    cd "$service_dir"

    # Check if package.json exists and run npm install if needed
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ]; then
            echo "Installing dependencies for ${service_name}..."
            npm install
        fi
    fi

    # Start the service in background
    echo "Executing: $start_command"
    eval "$start_command" &
    local pid=$!

    # Wait a moment and check if service started
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ ${service_name} started successfully (PID: $pid)${NC}"
        echo $pid > "${BASE_DIR}/.${service_name,,}_pid"
    else
        echo -e "${RED}❌ Failed to start ${service_name}${NC}"
    fi
}

# Function to test service health
test_service_health() {
    local service_name=$1
    local url=$2

    echo -e "${YELLOW}Testing ${service_name} health...${NC}"

    # Try health endpoint first
    if curl -s "${url}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${service_name} health check passed${NC}"
    elif curl -s "${url}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${service_name} responding (no health endpoint)${NC}"
    else
        echo -e "${RED}❌ ${service_name} health check failed${NC}"
        return 1
    fi
}

# Start Algorand Reader MCP (port 8002)
if [ -d "$ALGORAND_READER_DIR" ]; then
    start_service "Algorand-Reader" "$ALGORAND_READER_DIR" "8002" \
        "ALGORAND_NETWORK=testnet ALGORAND_ALGOD=https://testnet-api.algonode.cloud ALGORAND_INDEXER=https://testnet-idx.algonode.cloud READ_ONLY=true PORT=8002 node server.js"
else
    echo -e "${RED}❌ Algorand Reader MCP directory not found: $ALGORAND_READER_DIR${NC}"
fi

# Start Market Data MCP (port 8003)
if [ -d "$MARKET_DATA_DIR" ]; then
    start_service "Market-Data" "$MARKET_DATA_DIR" "8003" \
        "PORT=8003 npx wrangler dev --local --port 8003"
else
    echo -e "${YELLOW}⚠️  Market Data MCP directory not found: $MARKET_DATA_DIR${NC}"
    echo -e "${YELLOW}   Collateral analyzer will use fallback prices${NC}"
fi

echo ""
echo -e "${BLUE}⏳ Waiting for services to initialize...${NC}"
sleep 5

echo ""
echo -e "${BLUE}🔍 Testing service connectivity...${NC}"
echo "=================================="

# Test services
test_service_health "Algorand Reader" "http://localhost:8002"

if [ -d "$MARKET_DATA_DIR" ]; then
    test_service_health "Market Data" "http://localhost:8003"
fi

echo ""
echo -e "${BLUE}📋 Service Status Summary${NC}"
echo "========================="
echo -e "Algorand Reader MCP: ${GREEN}http://localhost:8002${NC}"
if [ -d "$MARKET_DATA_DIR" ]; then
    echo -e "Market Data MCP:     ${GREEN}http://localhost:8003${NC}"
else
    echo -e "Market Data MCP:     ${YELLOW}Not available (using fallbacks)${NC}"
fi

echo ""
echo -e "${BLUE}📚 Available Endpoints:${NC}"
echo "http://localhost:8002/health      - Algorand Reader health"
echo "http://localhost:8002/docs        - Algorand Reader documentation"
echo "http://localhost:8002/accounts    - Account information endpoint"
echo "http://localhost:8002/assets      - Asset information endpoint"

echo ""
echo -e "${GREEN}🎉 MCP services ready for collateral analysis!${NC}"
echo ""
echo -e "${YELLOW}💡 Usage Tips:${NC}"
echo "• Services run in background - use 'stop-mcp-services.sh' to stop them"
echo "• Check logs with: tail -f /tmp/algorand-reader.log"
echo "• Test the collateral analyzer with: cd collateral-requirements && python3 analyze_collateral.py --help"
echo "• Use the Jupyter notebook for interactive testing: notebooks/collateral_analyzer_testing.ipynb"

# Create stop script
cat > "${BASE_DIR}/stop-mcp-services.sh" << 'EOF'
#!/bin/bash

# Stop MCP services for collateral analyzer

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_DIR="/home/mpo/algorand-showcase/algorand-lending-ecosystem/business-logic-engines/blockchain-collateral-analyzer"

echo -e "${YELLOW}🛑 Stopping MCP Services...${NC}"

# Stop services by PID
for service in algorand-reader market-data; do
    pidfile="${BASE_DIR}/.${service}_pid"
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping ${service} (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                echo -e "${RED}Force killing ${service}...${NC}"
                kill -9 $pid
            fi
            echo -e "${GREEN}✅ ${service} stopped${NC}"
        fi
        rm -f "$pidfile"
    fi
done

# Also kill any remaining processes on our ports
for port in 8002 8003; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)...${NC}"
        kill $pid 2>/dev/null || true
        sleep 1
        kill -9 $pid 2>/dev/null || true
    fi
done

echo -e "${GREEN}🎉 All MCP services stopped${NC}"
EOF

chmod +x "${BASE_DIR}/stop-mcp-services.sh"

echo ""
echo -e "${BLUE}📝 Created stop script: ${BASE_DIR}/stop-mcp-services.sh${NC}"