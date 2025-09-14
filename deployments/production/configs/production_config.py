"""
Production Configuration for Lending API
Agent 2: Production Deployment
"""
import os
from typing import Optional

class ProductionConfig:
    """Production-ready configuration for the lending API"""

    # Database Configuration (PostgreSQL)
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/algorand_showcase")

    # Rate Limiting (ENABLED for production)
    RATE_LIMITING_ENABLED = True
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_BURST_SIZE = 10

    # Production Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "/var/log/lending-api/app.log"

    # Security
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "GENERATE_SECURE_KEY_AND_PUT_IN_ENV")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 1

    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8003

    # MCP Services (Production endpoints)
    REMOTE_MCP_URL = os.getenv("REMOTE_MCP_URL", "http://localhost:8002")
    ACTIONS_MCP_URL = os.getenv("ACTIONS_MCP_URL", "http://localhost:3001")

    # Blockchain Configuration
    ALGORAND_NETWORK = "testnet"  # Production will use mainnet
    ALGOD_URL = "https://testnet-api.algonode.cloud"
    INDEXER_URL = "https://testnet-idx.algonode.cloud"

    # Transaction Configuration
    ENABLE_REAL_TRANSACTIONS = True
    REQUIRE_SIGNATURE = True  # Production requires wallet signatures

    # Monitoring
    HEALTH_CHECK_INTERVAL = 30
    METRICS_ENABLED = True

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required production configuration is present"""
        required_env_vars = [
            "DATABASE_URL",
            "JWT_SECRET",
            "REMOTE_MCP_URL",
            "ACTIONS_MCP_URL"
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            return False

        print("✅ Production configuration validated")
        return True

# PostgreSQL Database Models
POSTGRESQL_SCHEMA = """
-- Loans table for persistence
CREATE TABLE IF NOT EXISTS loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id VARCHAR(255) UNIQUE NOT NULL,
    borrower_address VARCHAR(255) NOT NULL,
    lender_address VARCHAR(255) NOT NULL,
    amount_micro_algos BIGINT NOT NULL,
    duration_days INTEGER NOT NULL,
    interest_rate DECIMAL(5,2) NOT NULL,
    collateral_type VARCHAR(50) NOT NULL,
    collateral_amount BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    terms JSONB,
    workflow_result JSONB
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_borrower ON loans(borrower_address);
CREATE INDEX IF NOT EXISTS idx_loans_created ON loans(created_at);

-- API rate limiting table
CREATE TABLE IF NOT EXISTS api_rate_limits (
    id SERIAL PRIMARY KEY,
    client_ip INET NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_ip, endpoint, window_start)
);
"""

# Production Environment Template
PRODUCTION_ENV_TEMPLATE = """
# Production Environment Variables
# Copy to .env.production and fill with real values

# Database
DATABASE_URL=postgresql://lending_user:secure_password@localhost:5432/algorand_lending

# Security
JWT_SECRET=generate_secure_256_bit_key_here

# MCP Services
REMOTE_MCP_URL=http://localhost:8002
ACTIONS_MCP_URL=http://localhost:3001

# API Configuration
API_HOST=0.0.0.0
API_PORT=8003

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true

# Algorand Network
ALGORAND_NETWORK=testnet
ALGOD_URL=https://testnet-api.algonode.cloud
INDEXER_URL=https://testnet-idx.algonode.cloud
"""