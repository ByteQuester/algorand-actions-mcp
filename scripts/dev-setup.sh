#!/bin/bash

# Development Setup Script for Algorand MCP Workers
# This script helps developers get started quickly with the containerized setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Algorand MCP Workers - Development Setup${NC}"
echo "=============================================="

# Check dependencies
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"

MISSING_DEPS=()

if ! command -v docker &> /dev/null; then
    MISSING_DEPS+=("docker")
fi

if ! docker compose version &> /dev/null; then
    MISSING_DEPS+=("docker compose")
fi

if ! command -v pnpm &> /dev/null; then
    MISSING_DEPS+=("pnpm")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing dependencies:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  • $dep"
    done
    echo ""
    echo "Please install the missing dependencies and run this script again."
    exit 1
fi

echo -e "${GREEN}✅ All dependencies found${NC}"

# Setup environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating environment file...${NC}"
    cp .env.docker .env
    echo -e "${GREEN}✅ Environment file created (.env)${NC}"
    echo -e "${BLUE}💡 Edit .env to customize your configuration${NC}"
else
    echo -e "${BLUE}📝 Environment file already exists${NC}"
fi

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pnpm install --frozen-lockfile

# Build packages
echo -e "${YELLOW}🔨 Building workspace packages...${NC}"
pnpm --filter "@algorand-showcase/*" run build

# Build Docker images
echo -e "${YELLOW}🐳 Building Docker images...${NC}"
docker compose build

echo -e "${GREEN}🎉 Setup completed!${NC}"
echo ""
echo "Available commands:"
echo "  • ${GREEN}docker compose up${NC}                    - Start both workers"
echo "  • ${GREEN}docker compose up actions-mcp${NC}        - Start only Actions worker"
echo "  • ${GREEN}docker compose up remote-mcp${NC}         - Start only Remote worker"
echo "  • ${GREEN}docker compose --profile proxy up${NC}    - Start with Traefik proxy"
echo "  • ${GREEN}docker compose --profile monitoring up${NC} - Start with monitoring"
echo "  • ${GREEN}docker compose logs -f${NC}               - View logs"
echo "  • ${GREEN}docker compose down${NC}                  - Stop all services"
echo ""
echo "Endpoints:"
echo "  • Actions MCP Worker: ${BLUE}http://localhost:8788${NC}"
echo "    - Health: http://localhost:8788/health"
echo "    - Docs: http://localhost:8788/docs"
echo "    - Metrics: http://localhost:8788/metrics"
echo ""
echo "  • Remote MCP Worker: ${BLUE}http://localhost:8789${NC}"
echo "    - Health: http://localhost:8789/health"
echo "    - Docs: http://localhost:8789/docs" 
echo "    - Metrics: http://localhost:8789/metrics"
echo ""
echo "  • Monitoring (if enabled):"
echo "    - Prometheus: ${BLUE}http://localhost:9090${NC}"
echo "    - Grafana: ${BLUE}http://localhost:3000${NC} (admin/admin)"
echo ""
echo -e "${YELLOW}💡 Pro tip: Use 'docker compose up -d' to run in background${NC}"