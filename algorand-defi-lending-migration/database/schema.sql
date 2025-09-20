-- Algorand DeFi Lending Platform Database Schema
-- Target: PostgreSQL 13+

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
    kyc_status VARCHAR(50) DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'approved', 'rejected', 'expired')),
    kyc_tier INTEGER DEFAULT 1 CHECK (kyc_tier IN (1, 2, 3)),
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    wallet_address VARCHAR(58),  -- Algorand address format
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Wallets and Assets
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(58) UNIQUE NOT NULL,  -- Algorand address
    wallet_type VARCHAR(50) NOT NULL CHECK (wallet_type IN ('metamask', 'walletconnect', 'algorand_mobile', 'pera', 'defly')),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'compromised'))
);

CREATE TABLE asset_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id VARCHAR(20) UNIQUE NOT NULL,  -- Algorand asset ID or 'ALGO'
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    decimals INTEGER NOT NULL DEFAULT 6,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('algo_native', 'asa_token', 'stablecoin', 'governance', 'lp_token', 'liquid_staking')),
    contract_address VARCHAR(58),  -- For smart contracts
    is_active BOOLEAN DEFAULT TRUE,

    -- Collateral parameters
    base_collateral_ratio DECIMAL(5,4) NOT NULL,
    maintenance_ratio DECIMAL(5,4) NOT NULL,
    liquidation_penalty DECIMAL(5,4) NOT NULL,

    -- Risk metrics
    volatility_30d DECIMAL(8,6),
    volatility_7d DECIMAL(8,6),
    max_drawdown_30d DECIMAL(8,6),
    correlation_with_algo DECIMAL(8,6),

    -- Liquidity metrics
    daily_volume_usd DECIMAL(18,2),
    market_cap_usd DECIMAL(18,2),
    liquidity_tier VARCHAR(20) CHECK (liquidity_tier IN ('high', 'medium', 'low')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wallet_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES asset_definitions(id),
    balance DECIMAL(20,6) NOT NULL DEFAULT 0,
    available_balance DECIMAL(20,6) NOT NULL DEFAULT 0,  -- Excluding locked amounts
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(wallet_id, asset_id)
);

-- Lending Operations
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    borrower_id UUID NOT NULL REFERENCES users(id),
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    loan_amount_usd DECIMAL(18,2) NOT NULL,
    loan_asset_id UUID NOT NULL REFERENCES asset_definitions(id),
    loan_asset_amount DECIMAL(20,6) NOT NULL,

    -- Interest and terms
    interest_rate DECIMAL(8,6) NOT NULL,  -- Annual percentage rate
    origination_fee DECIMAL(8,6) DEFAULT 0,
    term_days INTEGER,  -- NULL for perpetual loans

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'defaulted', 'liquidated', 'repaid', 'cancelled')),

    -- Collateral requirements
    required_collateral_ratio DECIMAL(5,4) NOT NULL,
    current_collateral_ratio DECIMAL(5,4),
    liquidation_threshold DECIMAL(5,4) NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE,
    funded_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    repaid_at TIMESTAMP WITH TIME ZONE,
    liquidated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE collateral_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES asset_definitions(id),
    quantity DECIMAL(20,6) NOT NULL,
    locked_quantity DECIMAL(20,6) NOT NULL DEFAULT 0,

    -- Valuation
    entry_price_usd DECIMAL(18,8) NOT NULL,
    current_price_usd DECIMAL(18,8),
    value_usd DECIMAL(18,2),
    haircut_percentage DECIMAL(5,4) NOT NULL,
    adjusted_value_usd DECIMAL(18,2),

    -- Risk metrics
    price_confidence DECIMAL(3,2),
    liquidation_urgency VARCHAR(20) CHECK (liquidation_urgency IN ('low', 'medium', 'high')),
    time_to_liquidate_hours DECIMAL(8,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interest_accruals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    accrual_date DATE NOT NULL,
    principal_balance DECIMAL(20,6) NOT NULL,
    interest_rate DECIMAL(8,6) NOT NULL,
    daily_interest DECIMAL(20,6) NOT NULL,
    cumulative_interest DECIMAL(20,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(loan_id, accrual_date)
);

-- Risk Management
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_id UUID NOT NULL REFERENCES loans(id),
    assessment_type VARCHAR(50) NOT NULL CHECK (assessment_type IN ('origination', 'periodic', 'liquidation')),

    -- Risk scores
    overall_risk_score DECIMAL(5,2) NOT NULL,
    credit_risk_score DECIMAL(5,2),
    market_risk_score DECIMAL(5,2),
    liquidity_risk_score DECIMAL(5,2),

    -- Portfolio metrics
    portfolio_var_95 DECIMAL(8,6),
    max_portfolio_drawdown DECIMAL(8,6),
    diversification_score DECIMAL(3,2),
    correlation_risk DECIMAL(3,2),

    -- Recommendations
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    confidence_score DECIMAL(3,2),
    recommended_actions JSONB,
    monitoring_alerts JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE
);

CREATE TABLE liquidation_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_id UUID NOT NULL REFERENCES loans(id),
    triggered_by VARCHAR(100) NOT NULL,  -- 'system', 'manual', 'user_request'
    trigger_condition TEXT NOT NULL,

    -- Liquidation details
    collateral_asset_id UUID NOT NULL REFERENCES asset_definitions(id),
    liquidated_quantity DECIMAL(20,6) NOT NULL,
    liquidation_price DECIMAL(18,8) NOT NULL,
    proceeds_usd DECIMAL(18,2) NOT NULL,

    -- Costs and recovery
    liquidation_penalty DECIMAL(18,2) NOT NULL,
    gas_fees DECIMAL(18,2) NOT NULL,
    net_recovery DECIMAL(18,2) NOT NULL,
    recovery_percentage DECIMAL(5,4) NOT NULL,

    -- Market impact
    estimated_slippage DECIMAL(5,4),
    actual_slippage DECIMAL(5,4),
    market_impact VARCHAR(20),

    -- Transaction details
    blockchain_txn_id VARCHAR(100),
    execution_time_seconds INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Market Data
CREATE TABLE price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES asset_definitions(id),
    price_usd DECIMAL(18,8) NOT NULL,
    volume_24h DECIMAL(18,2),
    market_cap DECIMAL(18,2),

    -- Oracle information
    oracle_source VARCHAR(50) NOT NULL,
    confidence_level DECIMAL(3,2),
    price_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, oracle_source, price_timestamp)
);

CREATE TABLE volatility_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES asset_definitions(id),
    calculation_date DATE NOT NULL,

    -- Volatility measurements
    volatility_1d DECIMAL(8,6),
    volatility_7d DECIMAL(8,6),
    volatility_30d DECIMAL(8,6),
    volatility_90d DECIMAL(8,6),

    -- Risk metrics
    value_at_risk_95 DECIMAL(8,6),
    value_at_risk_99 DECIMAL(8,6),
    expected_shortfall_95 DECIMAL(8,6),
    max_drawdown DECIMAL(8,6),

    -- Stress test results
    stress_test_scenarios JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, calculation_date)
);

-- Audit and Compliance
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID,
    user_id UUID REFERENCES users(id),
    wallet_address VARCHAR(58),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL CHECK (event_category IN ('authentication', 'transaction', 'admin', 'compliance', 'system')),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,

    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id UUID,

    -- Data
    event_data JSONB,
    old_values JSONB,
    new_values JSONB,

    -- Results
    success BOOLEAN NOT NULL,
    error_message TEXT,
    response_time_ms INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_loans_borrower_id ON loans(borrower_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loans_created_at ON loans(created_at);
CREATE INDEX idx_collateral_positions_loan_id ON collateral_positions(loan_id);
CREATE INDEX idx_price_history_asset_timestamp ON price_history(asset_id, price_timestamp);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_correlation_id ON audit_logs(correlation_id);

-- Updated timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_asset_definitions_updated_at BEFORE UPDATE ON asset_definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_collateral_positions_updated_at BEFORE UPDATE ON collateral_positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();