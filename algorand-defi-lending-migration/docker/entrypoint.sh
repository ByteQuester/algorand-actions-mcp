#!/bin/bash
set -e

# Algorand DeFi Lending Platform - Container Entry Point

# Wait for database to be ready
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
        sleep 1
    done
    echo "Database is ready!"
}

# Wait for Redis to be ready
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    cd /app
    python -c "
import asyncio
import asyncpg
import os

async def run_schema():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    with open('database/schema.sql', 'r') as f:
        await conn.execute(f.read())
    with open('database/seed-data.sql', 'r') as f:
        await conn.execute(f.read())
    await conn.close()
    print('Database schema and seed data applied')

asyncio.run(run_schema())
"
}

# Start MCP services in background
start_mcp_services() {
    echo "Starting MCP services..."
    cd /app/mcp-services

    # Start Algorand Reader MCP
    PORT=8001 node algorand-reader-mcp/server.js &

    # Start Algorand Writer MCP
    PORT=8002 node algorand-writer-mcp/server.js &

    # Start Market Data MCP
    PORT=8003 node market-data-mcp/server.js &

    echo "MCP services started"
}

# Start the main application
start_api() {
    echo "Starting API server..."
    cd /app

    # Set Python path
    export PYTHONPATH=/app/src:/app

    # Start the FastAPI application
    python -m uvicorn src.api.server:app \
        --host 0.0.0.0 \
        --port ${PORT:-8080} \
        --workers ${WORKERS:-4} \
        --log-level ${LOG_LEVEL:-info}
}

# Start agent system
start_agents() {
    echo "Starting agent system..."
    cd /app
    export PYTHONPATH=/app/src:/app
    python src/agents/root_agent.py
}

# Start working lending system (standalone)
start_standalone() {
    echo "Starting standalone lending system..."
    cd /app
    export PYTHONPATH=/app/src:/app
    python src/working_lending_system.py
}

# Main execution
case "$1" in
    api)
        wait_for_db
        wait_for_redis
        run_migrations
        start_mcp_services
        start_api
        ;;
    agents)
        wait_for_db
        wait_for_redis
        start_mcp_services
        start_agents
        ;;
    standalone)
        start_standalone
        ;;
    mcp-only)
        start_mcp_services
        # Keep container running
        tail -f /dev/null
        ;;
    *)
        echo "Usage: $0 {api|agents|standalone|mcp-only}"
        echo "  api        - Start complete API server with MCP services"
        echo "  agents     - Start agent system"
        echo "  standalone - Start standalone lending system"
        echo "  mcp-only   - Start only MCP services"
        exit 1
        ;;
esac