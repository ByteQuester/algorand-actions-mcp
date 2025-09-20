-- =====================================================
-- AUDIT TRAIL & COMPLIANCE DATABASE SCHEMA
-- =====================================================
-- High-performance schema designed for millions of audit entries
-- Optimized for sub-second query times and regulatory compliance
-- PostgreSQL 14+ with JSONB and full-text search support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- AUDIT SESSIONS TABLE
-- =====================================================
-- Session management for grouping related audit events
-- Optimized for session-based queries and cleanup

CREATE TABLE audit_sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(128),
    correlation_id VARCHAR(128),

    -- Session lifecycle
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    session_duration_ms INTEGER,

    -- Session context
    ip_address INET,
    user_agent TEXT,
    authentication_method VARCHAR(50),

    -- Activity counters
    event_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,

    -- Business metrics
    loans_processed INTEGER DEFAULT 0,
    transactions_created INTEGER DEFAULT 0,
    decisions_made INTEGER DEFAULT 0,

    -- Session status
    is_active BOOLEAN DEFAULT TRUE,
    termination_reason VARCHAR(255),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for audit_sessions
CREATE INDEX idx_audit_sessions_user_id ON audit_sessions(user_id);
CREATE INDEX idx_audit_sessions_correlation_id ON audit_sessions(correlation_id);
CREATE INDEX idx_audit_sessions_active ON audit_sessions(is_active, session_start);
CREATE INDEX idx_audit_sessions_timerange ON audit_sessions(session_start, session_end);

-- =====================================================
-- USER AUDIT PROFILES TABLE
-- =====================================================
-- Privacy and audit preferences for users
-- GDPR and CCPA compliance tracking

CREATE TABLE user_audit_profiles (
    user_id VARCHAR(128) PRIMARY KEY,
    algorand_address VARCHAR(58),

    -- Privacy controls
    data_retention_days INTEGER DEFAULT 2555, -- 7 years
    audit_level VARCHAR(20) DEFAULT 'standard' CHECK (audit_level IN ('minimal', 'standard', 'detailed', 'comprehensive')),

    -- Data sharing preferences
    allow_analytics BOOLEAN DEFAULT TRUE,
    allow_third_party_sharing BOOLEAN DEFAULT FALSE,

    -- Geographic and regulatory
    jurisdiction VARCHAR(10) DEFAULT 'US',
    gdpr_subject BOOLEAN DEFAULT FALSE,
    ccpa_subject BOOLEAN DEFAULT FALSE,

    -- Consent tracking
    privacy_policy_version VARCHAR(20) NOT NULL,
    consent_timestamp TIMESTAMPTZ NOT NULL,
    consent_withdrawn BOOLEAN DEFAULT FALSE,
    withdrawal_timestamp TIMESTAMPTZ,

    -- Profile metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for user_audit_profiles
CREATE INDEX idx_user_audit_profiles_algorand_address ON user_audit_profiles(algorand_address);
CREATE INDEX idx_user_audit_profiles_jurisdiction ON user_audit_profiles(jurisdiction);
CREATE INDEX idx_user_audit_profiles_gdpr ON user_audit_profiles(gdpr_subject) WHERE gdpr_subject = TRUE;
CREATE INDEX idx_user_audit_profiles_ccpa ON user_audit_profiles(ccpa_subject) WHERE ccpa_subject = TRUE;
CREATE INDEX idx_user_audit_profiles_consent ON user_audit_profiles(consent_withdrawn, withdrawal_timestamp);

-- =====================================================
-- AUDIT TRAILS TABLE (MAIN TABLE)
-- =====================================================
-- Primary audit trail storage with JSONB event data
-- Partitioned by timestamp for performance
-- Immutable design for audit integrity

CREATE TABLE audit_trails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),

    -- Temporal information (partitioning key)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_start TIMESTAMPTZ,

    -- Event details (JSONB for flexibility and performance)
    event_data JSONB NOT NULL DEFAULT '{}',

    -- Security and compliance
    classification VARCHAR(20) DEFAULT 'internal' CHECK (classification IN ('public', 'internal', 'confidential', 'restricted', 'top_secret')),
    requires_retention BOOLEAN DEFAULT TRUE,
    retention_days INTEGER DEFAULT 2555,

    -- Traceability
    correlation_id VARCHAR(128),
    parent_event_id UUID REFERENCES audit_trails(id),
    trace_id VARCHAR(128),
    span_id VARCHAR(128),

    -- Source information
    service_name VARCHAR(100) NOT NULL,
    service_version VARCHAR(20) NOT NULL,
    environment VARCHAR(20) DEFAULT 'production',

    -- Session reference
    session_id VARCHAR(128) REFERENCES audit_sessions(session_id),

    -- Integrity and compliance
    checksum VARCHAR(64), -- SHA-256 for tamper detection

    -- Full-text search vector (computed)
    search_vector TSVECTOR,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create initial partitions (current month and next 12 months)
-- This enables automatic partition pruning for better performance
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
    i INTEGER;
BEGIN
    FOR i IN 0..12 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'audit_trails_' || TO_CHAR(start_date, 'YYYY_MM');

        EXECUTE FORMAT(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_trails
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        start_date := end_date;
    END LOOP;
END $$;

-- Primary indexes on audit_trails
CREATE INDEX idx_audit_trails_event_type ON audit_trails(event_type, timestamp DESC);
CREATE INDEX idx_audit_trails_severity ON audit_trails(severity, timestamp DESC);
CREATE INDEX idx_audit_trails_correlation_id ON audit_trails(correlation_id, timestamp DESC);
CREATE INDEX idx_audit_trails_session_id ON audit_trails(session_id, timestamp DESC);
CREATE INDEX idx_audit_trails_service ON audit_trails(service_name, timestamp DESC);
CREATE INDEX idx_audit_trails_trace ON audit_trails(trace_id, span_id);
CREATE INDEX idx_audit_trails_parent ON audit_trails(parent_event_id);

-- JSONB indexes for high-performance queries on event_data
CREATE INDEX idx_audit_trails_event_data_gin ON audit_trails USING GIN(event_data);
CREATE INDEX idx_audit_trails_loan_id ON audit_trails USING GIN((event_data->'loan_id'));
CREATE INDEX idx_audit_trails_user_id ON audit_trails USING GIN((event_data->'user_id'));
CREATE INDEX idx_audit_trails_borrower_address ON audit_trails USING GIN((event_data->'borrower_address'));
CREATE INDEX idx_audit_trails_lender_address ON audit_trails USING GIN((event_data->'lender_address'));
CREATE INDEX idx_audit_trails_transaction_id ON audit_trails USING GIN((event_data->'transaction_id'));

-- Composite indexes for common query patterns
CREATE INDEX idx_audit_trails_loan_timeline ON audit_trails((event_data->'loan_id'), timestamp DESC);
CREATE INDEX idx_audit_trails_user_activity ON audit_trails((event_data->'user_id'), timestamp DESC, event_type);
CREATE INDEX idx_audit_trails_error_tracking ON audit_trails(severity, timestamp DESC) WHERE severity IN ('error', 'critical');

-- Full-text search index
CREATE INDEX idx_audit_trails_search ON audit_trails USING GIN(search_vector);

-- =====================================================
-- DECISION POINTS TABLE
-- =====================================================
-- Key lending decisions for regulatory compliance
-- Linked to main audit trail for complete traceability

CREATE TABLE decision_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_type VARCHAR(50) NOT NULL CHECK (decision_type IN (
        'risk_assessment', 'credit_approval', 'collateral_evaluation',
        'interest_rate_determination', 'loan_terms_negotiation',
        'default_determination', 'liquidation_trigger'
    )),

    -- Business context
    loan_id VARCHAR(128) NOT NULL,
    borrower_address VARCHAR(58) NOT NULL,
    lender_address VARCHAR(58),

    -- Decision details
    decision_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decision_maker VARCHAR(255) NOT NULL,
    decision_rationale TEXT NOT NULL,
    decision_outcome TEXT NOT NULL,

    -- Input data (JSONB for flexibility)
    input_data JSONB NOT NULL DEFAULT '{}',

    -- Risk and compliance arrays
    risk_factors TEXT[],
    compliance_flags TEXT[],
    regulatory_requirements TEXT[],

    -- Quantitative measures
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    risk_score DECIMAL(5,2) CHECK (risk_score >= 0.0 AND risk_score <= 100.0),

    -- Audit trail reference (mandatory)
    audit_event_id UUID NOT NULL REFERENCES audit_trails(id),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for decision_points
CREATE INDEX idx_decision_points_loan_id ON decision_points(loan_id, decision_timestamp DESC);
CREATE INDEX idx_decision_points_borrower ON decision_points(borrower_address, decision_timestamp DESC);
CREATE INDEX idx_decision_points_type ON decision_points(decision_type, decision_timestamp DESC);
CREATE INDEX idx_decision_points_maker ON decision_points(decision_maker, decision_timestamp DESC);
CREATE INDEX idx_decision_points_risk ON decision_points(risk_score DESC, confidence_score DESC);
CREATE INDEX idx_decision_points_audit_ref ON decision_points(audit_event_id);

-- JSONB index for input_data queries
CREATE INDEX idx_decision_points_input_data ON decision_points USING GIN(input_data);

-- Array indexes for compliance tracking
CREATE INDEX idx_decision_points_risk_factors ON decision_points USING GIN(risk_factors);
CREATE INDEX idx_decision_points_compliance_flags ON decision_points USING GIN(compliance_flags);

-- =====================================================
-- COMPLIANCE EVENTS TABLE
-- =====================================================
-- Regulatory and compliance event tracking
-- Supports multiple jurisdictions and regulations

CREATE TABLE compliance_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Regulatory context
    regulation_type VARCHAR(50) NOT NULL, -- 'KYC', 'AML', 'GDPR', 'SOX', etc.
    compliance_rule VARCHAR(255) NOT NULL,
    jurisdiction VARCHAR(10) DEFAULT 'US',

    -- Business context
    loan_id VARCHAR(128),
    user_id VARCHAR(128),
    transaction_id VARCHAR(128),

    -- Compliance status
    compliance_status VARCHAR(20) NOT NULL CHECK (compliance_status IN ('compliant', 'non_compliant', 'pending', 'exempt')),
    violation_details TEXT,
    remediation_required BOOLEAN DEFAULT FALSE,
    remediation_steps TEXT[],

    -- Evidence and documentation
    evidence_references TEXT[],
    documentation_links TEXT[],

    -- Review and approval workflow
    reviewed_by VARCHAR(128),
    review_timestamp TIMESTAMPTZ,
    approved_by VARCHAR(128),
    approval_timestamp TIMESTAMPTZ,

    -- Audit trail reference (mandatory)
    audit_event_id UUID NOT NULL REFERENCES audit_trails(id),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for compliance_events
CREATE INDEX idx_compliance_events_regulation ON compliance_events(regulation_type, jurisdiction, event_timestamp DESC);
CREATE INDEX idx_compliance_events_status ON compliance_events(compliance_status, event_timestamp DESC);
CREATE INDEX idx_compliance_events_loan_id ON compliance_events(loan_id, event_timestamp DESC);
CREATE INDEX idx_compliance_events_user_id ON compliance_events(user_id, event_timestamp DESC);
CREATE INDEX idx_compliance_events_violations ON compliance_events(compliance_status, event_timestamp DESC)
    WHERE compliance_status = 'non_compliant';
CREATE INDEX idx_compliance_events_pending ON compliance_events(compliance_status, event_timestamp DESC)
    WHERE compliance_status = 'pending';
CREATE INDEX idx_compliance_events_audit_ref ON compliance_events(audit_event_id);

-- Array indexes for evidence tracking
CREATE INDEX idx_compliance_events_evidence ON compliance_events USING GIN(evidence_references);
CREATE INDEX idx_compliance_events_remediation ON compliance_events USING GIN(remediation_steps);

-- Workflow indexes
CREATE INDEX idx_compliance_events_review_workflow ON compliance_events(reviewed_by, review_timestamp);
CREATE INDEX idx_compliance_events_approval_workflow ON compliance_events(approved_by, approval_timestamp);

-- =====================================================
-- PERFORMANCE VIEWS
-- =====================================================

-- Recent audit activity view (last 24 hours)
CREATE VIEW v_recent_audit_activity AS
SELECT
    id,
    event_type,
    severity,
    timestamp,
    event_data,
    service_name,
    session_id,
    correlation_id
FROM audit_trails
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Loan audit timeline view
CREATE VIEW v_loan_audit_timeline AS
SELECT
    at.id,
    at.event_type,
    at.timestamp,
    at.event_data->>'loan_id' as loan_id,
    at.event_data->>'borrower_address' as borrower_address,
    at.event_data->>'lender_address' as lender_address,
    at.event_data->>'amount_micro_algos' as amount_micro_algos,
    at.severity,
    at.service_name
FROM audit_trails at
WHERE at.event_data->>'loan_id' IS NOT NULL
ORDER BY at.event_data->>'loan_id', at.timestamp;

-- Compliance dashboard view
CREATE VIEW v_compliance_dashboard AS
SELECT
    regulation_type,
    jurisdiction,
    compliance_status,
    COUNT(*) as event_count,
    COUNT(*) FILTER (WHERE compliance_status = 'non_compliant') as violations,
    COUNT(*) FILTER (WHERE compliance_status = 'pending') as pending_reviews,
    MAX(event_timestamp) as last_event
FROM compliance_events
WHERE event_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY regulation_type, jurisdiction, compliance_status
ORDER BY regulation_type, jurisdiction;

-- Active sessions view
CREATE VIEW v_active_sessions AS
SELECT
    session_id,
    user_id,
    session_start,
    ip_address,
    event_count,
    error_count,
    loans_processed
FROM audit_sessions
WHERE is_active = TRUE
ORDER BY session_start DESC;

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update search_vector for full-text search
CREATE OR REPLACE FUNCTION update_audit_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.event_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.service_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.event_data::text, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update search_vector
CREATE TRIGGER trigger_update_audit_search_vector
    BEFORE INSERT OR UPDATE ON audit_trails
    FOR EACH ROW EXECUTE FUNCTION update_audit_search_vector();

-- Function to update session counters
CREATE OR REPLACE FUNCTION update_session_counters()
RETURNS TRIGGER AS $$
BEGIN
    -- Update event counters in audit_sessions
    UPDATE audit_sessions
    SET
        event_count = event_count + 1,
        error_count = error_count + CASE WHEN NEW.severity IN ('error', 'critical') THEN 1 ELSE 0 END,
        warning_count = warning_count + CASE WHEN NEW.severity = 'warning' THEN 1 ELSE 0 END,
        loans_processed = loans_processed + CASE WHEN NEW.event_data->>'loan_id' IS NOT NULL THEN 1 ELSE 0 END,
        transactions_created = transactions_created + CASE WHEN NEW.event_type LIKE '%transaction%' THEN 1 ELSE 0 END,
        updated_at = NOW()
    WHERE session_id = NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update session counters
CREATE TRIGGER trigger_update_session_counters
    AFTER INSERT ON audit_trails
    FOR EACH ROW
    WHEN (NEW.session_id IS NOT NULL)
    EXECUTE FUNCTION update_session_counters();

-- Function to auto-create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_audit_partition(target_date DATE)
RETURNS TEXT AS $$
DECLARE
    start_date DATE := DATE_TRUNC('month', target_date);
    end_date DATE := start_date + INTERVAL '1 month';
    partition_name TEXT := 'audit_trails_' || TO_CHAR(start_date, 'YYYY_MM');
BEGIN
    EXECUTE FORMAT(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_trails
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Function for audit trail cleanup based on retention policies
CREATE OR REPLACE FUNCTION cleanup_expired_audit_trails()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    partition_name TEXT;
    min_date DATE;
BEGIN
    -- Find the oldest date that should be retained
    SELECT MIN(DATE_TRUNC('month', NOW() - INTERVAL '1 day' * retention_days))
    INTO min_date
    FROM audit_trails
    WHERE requires_retention = FALSE;

    -- If no cleanup date found, exit
    IF min_date IS NULL THEN
        RETURN 0;
    END IF;

    -- Drop old partitions that are entirely before the retention date
    FOR partition_name IN
        SELECT schemaname||'.'||tablename
        FROM pg_tables
        WHERE tablename ~ '^audit_trails_\d{4}_\d{2}$'
        AND TO_DATE(RIGHT(tablename, 7), 'YYYY_MM') < min_date
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || partition_name;
        deleted_count := deleted_count + 1;
    END LOOP;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INITIAL DATA AND CONFIGURATION
-- =====================================================

-- Create default service account audit profile
INSERT INTO user_audit_profiles (
    user_id,
    audit_level,
    data_retention_days,
    privacy_policy_version,
    consent_timestamp,
    jurisdiction
) VALUES (
    'system_service',
    'comprehensive',
    7300, -- 20 years for system events
    '1.0.0',
    NOW(),
    'GLOBAL'
) ON CONFLICT (user_id) DO NOTHING;

-- =====================================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- =====================================================

-- Optimize for time-series workloads
ALTER TABLE audit_trails SET (
    fillfactor = 90,  -- Leave room for HOT updates
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- Optimize decision_points for frequent lookups
ALTER TABLE decision_points SET (
    fillfactor = 95,  -- Mostly read-only after insert
    autovacuum_vacuum_scale_factor = 0.2
);

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE audit_trails IS 'Primary audit trail storage with JSONB event data, partitioned by timestamp for performance';
COMMENT ON TABLE decision_points IS 'Key lending decisions for regulatory compliance and explainable AI';
COMMENT ON TABLE compliance_events IS 'Regulatory and compliance event tracking for multiple jurisdictions';
COMMENT ON TABLE audit_sessions IS 'Session management for grouping related audit events';
COMMENT ON TABLE user_audit_profiles IS 'User privacy preferences and regulatory compliance settings';

COMMENT ON COLUMN audit_trails.event_data IS 'JSONB storage for flexible event data with GIN indexes for fast queries';
COMMENT ON COLUMN audit_trails.search_vector IS 'Full-text search vector automatically maintained by trigger';
COMMENT ON COLUMN audit_trails.checksum IS 'SHA-256 checksum for tamper detection and audit integrity';
COMMENT ON COLUMN decision_points.input_data IS 'JSONB storage for all input data considered in the decision';
COMMENT ON COLUMN compliance_events.remediation_steps IS 'Array of steps required to achieve compliance';