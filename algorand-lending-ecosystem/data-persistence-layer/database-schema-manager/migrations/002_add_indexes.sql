-- Description: Add performance indexes for optimized queries
-- UP

-- Indexes for loans table
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_created_at ON loans(created_at);
CREATE INDEX IF NOT EXISTS idx_loans_risk_score ON loans(risk_score);
CREATE INDEX IF NOT EXISTS idx_loans_amount ON loans(amount);

-- Indexes for audit_trail table
CREATE INDEX IF NOT EXISTS idx_audit_trail_loan_id ON audit_trail(loan_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type ON audit_trail(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail(timestamp);

-- Indexes for risk_assessments table
CREATE INDEX IF NOT EXISTS idx_risk_assessments_loan_id ON risk_assessments(loan_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_level ON risk_assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_final_score ON risk_assessments(final_risk_score);

-- DOWN

-- Drop all indexes
DROP INDEX IF EXISTS idx_loans_status;
DROP INDEX IF EXISTS idx_loans_created_at;
DROP INDEX IF EXISTS idx_loans_risk_score;
DROP INDEX IF EXISTS idx_loans_amount;
DROP INDEX IF EXISTS idx_audit_trail_loan_id;
DROP INDEX IF EXISTS idx_audit_trail_event_type;
DROP INDEX IF EXISTS idx_audit_trail_timestamp;
DROP INDEX IF EXISTS idx_risk_assessments_loan_id;
DROP INDEX IF EXISTS idx_risk_assessments_risk_level;
DROP INDEX IF EXISTS idx_risk_assessments_final_score;