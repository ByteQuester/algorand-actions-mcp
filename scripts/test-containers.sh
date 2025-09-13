#!/bin/bash

# Container Testing Script for Algorand MCP Workers
# This script validates that containers work correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Algorand MCP Worker Containers${NC}"
echo "==========================================="

# Configuration
ACTIONS_PORT=8788
REMOTE_PORT=8789
TIMEOUT=30

# Helper function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local timeout=$3
    
    echo -e "${YELLOW}⏳ Waiting for ${name} to start...${NC}"
    
    for i in $(seq 1 $timeout); do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ${name} is ready${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ ${name} failed to start within ${timeout}s${NC}"
    return 1
}

# Helper function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_status=$3
    
    echo -n "  Testing ${name}... "
    
    if [ -n "$expected_status" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
        if [ "$status" = "$expected_status" ]; then
            echo -e "${GREEN}✅ (${status})${NC}"
            return 0
        else
            echo -e "${RED}❌ (${status}, expected ${expected_status})${NC}"
            return 1
        fi
    else
        if curl -f -s "$url" > /dev/null; then
            echo -e "${GREEN}✅${NC}"
            return 0
        else
            echo -e "${RED}❌${NC}"
            return 1
        fi
    fi
}

# Start containers
echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker compose up -d

# Wait for services
if ! wait_for_service "http://localhost:${ACTIONS_PORT}/health" "Actions MCP Worker" $TIMEOUT; then
    echo -e "${RED}❌ Actions MCP Worker startup failed${NC}"
    docker compose logs actions-mcp
    exit 1
fi

if ! wait_for_service "http://localhost:${REMOTE_PORT}/health" "Remote MCP Worker" $TIMEOUT; then
    echo -e "${RED}❌ Remote MCP Worker startup failed${NC}"
    docker compose logs remote-mcp
    exit 1
fi

# Test Actions MCP Worker
echo -e "${BLUE}🧪 Testing Actions MCP Worker (port ${ACTIONS_PORT})${NC}"

ACTIONS_FAILED=0

test_endpoint "http://localhost:${ACTIONS_PORT}/health" "Health check" "200" || ((ACTIONS_FAILED++))
test_endpoint "http://localhost:${ACTIONS_PORT}/metrics" "Metrics" "200" || ((ACTIONS_FAILED++))
test_endpoint "http://localhost:${ACTIONS_PORT}/tools/list" "Tools list" "200" || ((ACTIONS_FAILED++))
test_endpoint "http://localhost:${ACTIONS_PORT}/openapi.json" "OpenAPI spec" "200" || ((ACTIONS_FAILED++))
test_endpoint "http://localhost:${ACTIONS_PORT}/docs" "Swagger UI" "200" || ((ACTIONS_FAILED++))

# Test Actions MCP API calls
echo "  Testing payment transaction build... "
PAYMENT_RESULT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"fromAddress":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","toAddress":"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB","microAlgos":1000}' \
    "http://localhost:${ACTIONS_PORT}/tools/build_payment" \
    -w "%{http_code}")

if echo "$PAYMENT_RESULT" | tail -c 4 | grep -q "200\|400"; then
    echo -e "${GREEN}✅ (API responds correctly)${NC}"
else
    echo -e "${RED}❌ (Unexpected response)${NC}"
    ((ACTIONS_FAILED++))
fi

# Test Remote MCP Worker
echo -e "${BLUE}🧪 Testing Remote MCP Worker (port ${REMOTE_PORT})${NC}"

REMOTE_FAILED=0

test_endpoint "http://localhost:${REMOTE_PORT}/health" "Health check" "200" || ((REMOTE_FAILED++))
test_endpoint "http://localhost:${REMOTE_PORT}/metrics" "Metrics" "200" || ((REMOTE_FAILED++))
test_endpoint "http://localhost:${REMOTE_PORT}/tools/list" "Tools list" "200" || ((REMOTE_FAILED++))
test_endpoint "http://localhost:${REMOTE_PORT}/openapi.json" "OpenAPI spec" "200" || ((REMOTE_FAILED++))
test_endpoint "http://localhost:${REMOTE_PORT}/docs" "Swagger UI" "200" || ((REMOTE_FAILED++))

# Test Remote MCP API calls
echo "  Testing account info query... "
ACCOUNT_RESULT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"address":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}' \
    "http://localhost:${REMOTE_PORT}/api/account" \
    -w "%{http_code}")

if echo "$ACCOUNT_RESULT" | tail -c 4 | grep -q "200\|400"; then
    echo -e "${GREEN}✅ (API responds correctly)${NC}"
else
    echo -e "${RED}❌ (Unexpected response)${NC}"
    ((REMOTE_FAILED++))
fi

# Test container health
echo -e "${BLUE}🏥 Testing container health${NC}"

ACTIONS_HEALTH=$(docker inspect algorand-actions-mcp --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
REMOTE_HEALTH=$(docker inspect algorand-remote-mcp --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")

echo "  Actions MCP Health: $ACTIONS_HEALTH"
echo "  Remote MCP Health: $REMOTE_HEALTH"

# Test resource usage
echo -e "${BLUE}📊 Container resource usage${NC}"

docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
    algorand-actions-mcp algorand-remote-mcp

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
docker compose down

# Summary
echo -e "${BLUE}📋 Test Summary${NC}"
echo "==============="

TOTAL_FAILED=$((ACTIONS_FAILED + REMOTE_FAILED))

if [ $ACTIONS_FAILED -eq 0 ]; then
    echo -e "Actions MCP Worker: ${GREEN}✅ All tests passed${NC}"
else
    echo -e "Actions MCP Worker: ${RED}❌ ${ACTIONS_FAILED} tests failed${NC}"
fi

if [ $REMOTE_FAILED -eq 0 ]; then
    echo -e "Remote MCP Worker: ${GREEN}✅ All tests passed${NC}"
else
    echo -e "Remote MCP Worker: ${RED}❌ ${REMOTE_FAILED} tests failed${NC}"
fi

echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All container tests passed!${NC}"
    echo -e "${BLUE}The containers are ready for production deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ ${TOTAL_FAILED} test(s) failed.${NC}"
    echo -e "${YELLOW}Please check the logs and fix the issues before deploying.${NC}"
    exit 1
fi