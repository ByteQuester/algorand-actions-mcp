#!/bin/bash

# Algorand Testnet MCP Services Startup Script
# This script starts both MCP services needed for Algorand testnet connectivity

# Load Gemini API configuration
export GOOGLE_API_KEY=AIzaSyDYGxsZFS4pl5-3mnxVwrp3YqCe67DPuB4
export GOOGLE_GENAI_USE_VERTEXAI=FALSE

echo "🚀 Starting Algorand Testnet MCP Services..."
echo "🤖 Gemini AI configured and ready"

# Kill any existing processes on ports 8002 and 3001
echo "📍 Checking for existing services..."
lsof -ti:8002 | xargs -r kill -9 2>/dev/null
lsof -ti:3001 | xargs -r kill -9 2>/dev/null

# Start Remote MCP (read-only operations) on port 8002
echo "📖 Starting Remote MCP (read-only) on port 8002..."
cd /home/mpo/algorand-showcase/apps/mcp-services/algorand-reader-mcp
PORT=8002 ALGORAND_NETWORK=testnet ALGORAND_ALGOD=https://testnet-api.algonode.cloud ALGORAND_INDEXER=https://testnet-idx.algonode.cloud READ_ONLY=true GOOGLE_API_KEY=$GOOGLE_API_KEY GOOGLE_GENAI_USE_VERTEXAI=$GOOGLE_GENAI_USE_VERTEXAI node server.js &
REMOTE_PID=$!

# Start Actions MCP (write operations) via Docker on port 3001
echo "✍️  Starting Actions MCP (write) on port 3001..."
docker start test-actions-mcp 2>/dev/null || docker run -d --name test-actions-mcp -p 3001:8080 algorand-actions-mcp:latest

# Wait for services to start
sleep 3

# Test connectivity
echo ""
echo "🔍 Testing service connectivity..."
echo ""

# Test Remote MCP
echo "Remote MCP (port 8002):"
curl -s http://localhost:8002/health | jq '.' || echo "❌ Remote MCP not responding"

echo ""

# Test Actions MCP
echo "Actions MCP (port 3001):"
docker exec test-actions-mcp curl -s http://localhost:8080/health | jq '.' || echo "❌ Actions MCP not responding"

echo ""
echo "✅ Services started!"
echo ""
echo "📚 Service URLs:"
echo "  - Remote MCP (read-only): http://localhost:8002"
echo "    Docs: http://localhost:8002/docs"
echo "  - Actions MCP (write):    http://localhost:3001"
echo "    Docs: http://localhost:3001/docs"
echo ""
echo "🧪 Test Commands:"
echo "  Query account: curl http://localhost:8002/tools/call -X POST -H 'Content-Type: application/json' -d '{\"name\":\"get_account_info\",\"arguments\":{\"address\":\"<ALGORAND_ADDRESS>\"}}'"
echo "  List tools: curl http://localhost:8002/tools/list | jq '.tools[].name'"
echo ""
echo "💡 Note: The lending desk app is now configured for ports 8002 and 3001."
echo "   Configuration updated in apps/business/a2a-lending-desk/main.py"