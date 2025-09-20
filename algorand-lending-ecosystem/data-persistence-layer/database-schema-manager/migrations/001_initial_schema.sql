-- Description: Initial database schema for lending platform
-- UP

-- Create schema versions table for tracking migrations
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- Create loans table with optimized schema and constraints
CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    borrower_name TEXT NOT NULL,
    borrower_address TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    purpose TEXT,
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    interest_rate REAL CHECK (interest_rate >= 0),
    collateral_required REAL CHECK (collateral_required >= 0),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'active', 'completed', 'defaulted')),
    decision_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit trail table
CREATE TABLE IF NOT EXISTS audit_trail (
    event_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans (loan_id) ON DELETE CASCADE
);

-- Create risk assessments table
CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    credit_score INTEGER CHECK (credit_score >= 300 AND credit_score <= 850),
    debt_to_income REAL CHECK (debt_to_income >= 0 AND debt_to_income <= 1),
    payment_history_score INTEGER CHECK (payment_history_score >= 0 AND payment_history_score <= 100),
    collateral_value REAL CHECK (collateral_value >= 0),
    final_risk_score INTEGER CHECK (final_risk_score >= 0 AND final_risk_score <= 100),
    risk_level TEXT CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'VERY HIGH')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans (loan_id) ON DELETE CASCADE
);

-- DOWN

DROP TABLE IF EXISTS risk_assessments;
DROP TABLE IF EXISTS audit_trail;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS schema_versions;