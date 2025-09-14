-- Production Database Initialization
-- This file is automatically run when PostgreSQL container starts

-- Create the database and user if they don't exist
SELECT 'CREATE DATABASE algorand_lending'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'algorand_lending')\gexec

-- Connect to the database
\c algorand_lending;

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

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_borrower ON loans(borrower_address);
CREATE INDEX IF NOT EXISTS idx_loans_created ON loans(created_at);
CREATE INDEX IF NOT EXISTS idx_loans_transaction ON loans(transaction_id);

-- API rate limiting table
CREATE TABLE IF NOT EXISTS api_rate_limits (
    id SERIAL PRIMARY KEY,
    client_ip INET NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_ip, endpoint, window_start)
);

-- Audit log table for compliance
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    loan_id VARCHAR(255),
    transaction_id VARCHAR(255),
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms NUMERIC(10,3) NOT NULL,
    status_code INTEGER NOT NULL,
    client_ip INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for monitoring queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_endpoint ON performance_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_performance_created ON performance_metrics(created_at);

-- Create views for monitoring dashboards
CREATE OR REPLACE VIEW loan_summary AS
SELECT
    status,
    COUNT(*) as count,
    SUM(amount_micro_algos) as total_amount_micro_algos,
    AVG(amount_micro_algos) as avg_amount_micro_algos,
    AVG(interest_rate) as avg_interest_rate
FROM loans
GROUP BY status;

CREATE OR REPLACE VIEW daily_performance AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    endpoint,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_time,
    MAX(response_time_ms) as max_response_time,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
FROM performance_metrics
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY date, endpoint
ORDER BY date DESC, endpoint;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lending_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lending_user;