#!/bin/bash

# Docker Build Script for Algorand MCP Workers
# This script builds both MCP worker containers and provides validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY=${DOCKER_REGISTRY:-""}
TAG=${TAG:-"latest"}
PUSH=${PUSH:-false}

echo -e "${BLUE}🐳 Building Algorand MCP Worker Containers${NC}"
echo "================================================"

# Check dependencies
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}❌ pnpm is not installed${NC}"
    exit 1
fi

# Build workspace packages first
echo -e "${YELLOW}📦 Building workspace packages...${NC}"
pnpm install --frozen-lockfile
pnpm --filter "@algorand-showcase/*" run build

# Build Actions MCP Worker
echo -e "${YELLOW}🔨 Building Actions MCP Worker...${NC}"
ACTIONS_IMAGE="algorand-actions-mcp:${TAG}"
if [ -n "$DOCKER_REGISTRY" ]; then
    ACTIONS_IMAGE="${DOCKER_REGISTRY}/${ACTIONS_IMAGE}"
fi

docker build \
    -f apps/actions-mcp-worker/Dockerfile \
    -t "$ACTIONS_IMAGE" \
    --target runner \
    .

echo -e "${GREEN}✅ Actions MCP Worker built: ${ACTIONS_IMAGE}${NC}"

# Build Remote MCP Worker
echo -e "${YELLOW}🔨 Building Remote MCP Worker...${NC}"
REMOTE_IMAGE="algorand-remote-mcp:${TAG}"
if [ -n "$DOCKER_REGISTRY" ]; then
    REMOTE_IMAGE="${DOCKER_REGISTRY}/${REMOTE_IMAGE}"
fi

docker build \
    -f apps/remote-mcp-worker/Dockerfile \
    -t "$REMOTE_IMAGE" \
    --target runner \
    .

echo -e "${GREEN}✅ Remote MCP Worker built: ${REMOTE_IMAGE}${NC}"

# Validate images
echo -e "${YELLOW}🔍 Validating Docker images...${NC}"

# Check image sizes
ACTIONS_SIZE=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "algorand-actions-mcp:${TAG}" | awk '{print $2}')
REMOTE_SIZE=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "algorand-remote-mcp:${TAG}" | awk '{print $2}')

echo "📊 Image Sizes:"
echo "  • Actions MCP: $ACTIONS_SIZE"
echo "  • Remote MCP: $REMOTE_SIZE"

# Test containers can start
echo -e "${YELLOW}🧪 Testing container startup...${NC}"

# Test Actions MCP Worker
echo "Testing Actions MCP Worker..."
ACTIONS_CONTAINER=$(docker run -d \
    -e ALGORAND_NETWORK=testnet \
    -e READ_ONLY=true \
    -p 8788:8080 \
    "$ACTIONS_IMAGE")

sleep 5

if docker ps | grep -q "$ACTIONS_CONTAINER"; then
    echo -e "${GREEN}✅ Actions MCP Worker started successfully${NC}"
    
    # Test health endpoint
    if curl -f -s http://localhost:8788/health > /dev/null; then
        echo -e "${GREEN}✅ Actions MCP Worker health check passed${NC}"
    else
        echo -e "${RED}❌ Actions MCP Worker health check failed${NC}"
    fi
else
    echo -e "${RED}❌ Actions MCP Worker failed to start${NC}"
    docker logs "$ACTIONS_CONTAINER"
fi

docker stop "$ACTIONS_CONTAINER" > /dev/null
docker rm "$ACTIONS_CONTAINER" > /dev/null

# Test Remote MCP Worker
echo "Testing Remote MCP Worker..."
REMOTE_CONTAINER=$(docker run -d \
    -e ALGORAND_NETWORK=mainnet \
    -e READ_ONLY=true \
    -p 8789:8080 \
    "$REMOTE_IMAGE")

sleep 5

if docker ps | grep -q "$REMOTE_CONTAINER"; then
    echo -e "${GREEN}✅ Remote MCP Worker started successfully${NC}"
    
    # Test health endpoint
    if curl -f -s http://localhost:8789/health > /dev/null; then
        echo -e "${GREEN}✅ Remote MCP Worker health check passed${NC}"
    else
        echo -e "${RED}❌ Remote MCP Worker health check failed${NC}"
    fi
else
    echo -e "${RED}❌ Remote MCP Worker failed to start${NC}"
    docker logs "$REMOTE_CONTAINER"
fi

docker stop "$REMOTE_CONTAINER" > /dev/null
docker rm "$REMOTE_CONTAINER" > /dev/null

# Push to registry if requested
if [ "$PUSH" = "true" ] && [ -n "$DOCKER_REGISTRY" ]; then
    echo -e "${YELLOW}📤 Pushing images to registry...${NC}"
    docker push "$ACTIONS_IMAGE"
    docker push "$REMOTE_IMAGE"
    echo -e "${GREEN}✅ Images pushed to registry${NC}"
fi

echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  • Start with: docker compose up"
echo "  • Access Actions MCP: http://localhost:8788/docs"
echo "  • Access Remote MCP: http://localhost:8789/docs"
echo "  • Monitor with: docker compose --profile monitoring up"