#!/bin/bash
# Production Startup Script for Algorand Lending Platform
# Agent 3: UI Customization for focused lending experience

echo "🚀 Starting Algorand Lending Platform..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Set production mode
export ADK_PRODUCTION_MODE=true
export LENDING_PLATFORM_MODE=true

# Database configuration for production
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://user:pass@localhost:5432/algorand_showcase

# Authentication configuration
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-"production-secret-key-change-me"}
export JWT_ALGORITHM=HS256
export TOKEN_EXPIRY=3600

# Logging configuration
export LOG_LEVEL=INFO
export ENVIRONMENT=production

# Activate virtual environment
source /home/mpo/algorand-showcase/venv-adk/bin/activate

# Change to working directory
cd /home/mpo/algorand-showcase

echo "✅ Environment configured for lending platform"
echo "✅ Production mode: $ADK_PRODUCTION_MODE"
echo "✅ Platform type: Lending-focused UI"

# Start ADK-Web with production configuration
echo "🎯 Starting ADK-Web UI (Lending Platform Mode)..."
echo "   Port: 8081"
echo "   Mode: Production (filtered agents)"
echo "   Branding: Algorand Lending Platform"

adk web --port 8081 --host 0.0.0.0 apps/core/adk-python/contributing/samples/