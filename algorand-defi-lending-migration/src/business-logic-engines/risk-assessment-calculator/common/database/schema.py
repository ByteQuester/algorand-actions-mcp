"""
Risk Database Schema

PostgreSQL schema for blockchain risk assessment data storage.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class RiskDatabaseSchema:
    """Database schema for risk assessment data"""

    @staticmethod
    def get_schema_sql() -> Dict[str, str]:
        """Get SQL statements for creating database schema"""
        return {
            'risk_profiles': """
                CREATE TABLE IF NOT EXISTS risk_profiles (
                    id SERIAL PRIMARY KEY,
                    entity_id VARCHAR(255) NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    assessment_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    overall_risk_score DECIMAL(5,4) NOT NULL CHECK (overall_risk_score >= 0 AND overall_risk_score <= 1),
                    risk_level VARCHAR(20) NOT NULL,
                    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
                    risk_factor_scores JSONB NOT NULL,
                    risk_factor_weights JSONB NOT NULL,
                    data_completeness DECIMAL(5,4) NOT NULL CHECK (data_completeness >= 0 AND data_completeness <= 1),
                    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    UNIQUE(entity_id, entity_type),
                    INDEX(entity_id),
                    INDEX(entity_type),
                    INDEX(risk_level),
                    INDEX(assessment_timestamp),
                    INDEX(overall_risk_score)
                );
            """,

            'transaction_patterns': """
                CREATE TABLE IF NOT EXISTS transaction_patterns (
                    id SERIAL PRIMARY KEY,
                    wallet_address VARCHAR(255) NOT NULL,
                    pattern_type VARCHAR(50) NOT NULL,
                    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
                    time_window_hours INTEGER NOT NULL,
                    transaction_count INTEGER NOT NULL,
                    total_volume DECIMAL(30,6) NOT NULL,
                    velocity_score DECIMAL(10,4) NOT NULL,
                    anomaly_indicators JSONB NOT NULL,
                    risk_factors JSONB NOT NULL,
                    detection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(wallet_address),
                    INDEX(pattern_type),
                    INDEX(confidence_score),
                    INDEX(detection_timestamp)
                );
            """,

            'anomaly_detections': """
                CREATE TABLE IF NOT EXISTS anomaly_detections (
                    id SERIAL PRIMARY KEY,
                    entity_id VARCHAR(255) NOT NULL,
                    anomaly_type VARCHAR(50) NOT NULL,
                    anomaly_score DECIMAL(5,4) NOT NULL CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
                    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                    deviation_magnitude DECIMAL(10,4) NOT NULL,
                    baseline_reference DECIMAL(20,6),
                    evidence JSONB NOT NULL,
                    detection_method VARCHAR(100) NOT NULL,
                    detection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    resolved_at TIMESTAMP WITH TIME ZONE NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(entity_id),
                    INDEX(anomaly_type),
                    INDEX(anomaly_score),
                    INDEX(detection_timestamp),
                    INDEX(resolved_at)
                );
            """,

            'correlation_matrices': """
                CREATE TABLE IF NOT EXISTS correlation_matrices (
                    id SERIAL PRIMARY KEY,
                    correlation_type VARCHAR(50) NOT NULL,
                    entities JSONB NOT NULL,
                    correlation_matrix JSONB NOT NULL,
                    metadata JSONB NOT NULL,
                    time_window_days INTEGER NOT NULL,
                    creation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(correlation_type),
                    INDEX(creation_timestamp)
                );
            """,

            'correlation_pairs': """
                CREATE TABLE IF NOT EXISTS correlation_pairs (
                    id SERIAL PRIMARY KEY,
                    entity_a VARCHAR(255) NOT NULL,
                    entity_b VARCHAR(255) NOT NULL,
                    correlation_type VARCHAR(50) NOT NULL,
                    correlation_coefficient DECIMAL(6,5) NOT NULL CHECK (correlation_coefficient >= -1 AND correlation_coefficient <= 1),
                    confidence_interval_lower DECIMAL(6,5) NOT NULL,
                    confidence_interval_upper DECIMAL(6,5) NOT NULL,
                    p_value DECIMAL(10,8) NOT NULL,
                    sample_size INTEGER NOT NULL,
                    time_period_days INTEGER NOT NULL,
                    calculation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(entity_a),
                    INDEX(entity_b),
                    INDEX(correlation_type),
                    INDEX(correlation_coefficient),
                    INDEX(calculation_timestamp),
                    UNIQUE(entity_a, entity_b, correlation_type, calculation_timestamp)
                );
            """,

            'cascade_events': """
                CREATE TABLE IF NOT EXISTS cascade_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) NOT NULL UNIQUE,
                    simulation_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    affected_node VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity DECIMAL(5,4) NOT NULL CHECK (severity >= 0 AND severity <= 1),
                    caused_by VARCHAR(255) NULL,
                    impact_magnitude DECIMAL(5,4) NOT NULL,
                    recovery_estimate_hours INTEGER NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(simulation_id),
                    INDEX(affected_node),
                    INDEX(event_type),
                    INDEX(timestamp),
                    INDEX(caused_by)
                );
            """,

            'cascade_simulations': """
                CREATE TABLE IF NOT EXISTS cascade_simulations (
                    id SERIAL PRIMARY KEY,
                    simulation_id VARCHAR(255) NOT NULL UNIQUE,
                    scenario_type VARCHAR(50) NOT NULL,
                    initial_shock JSONB NOT NULL,
                    final_state JSONB NOT NULL,
                    total_impact DECIMAL(10,6) NOT NULL,
                    affected_nodes JSONB NOT NULL,
                    cascade_depth INTEGER NOT NULL,
                    simulation_duration_hours DECIMAL(10,2) NOT NULL,
                    peak_impact_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    recovery_scenarios JSONB NOT NULL,
                    market_conditions JSONB,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(scenario_type),
                    INDEX(total_impact),
                    INDEX(cascade_depth),
                    INDEX(created_at)
                );
            """,

            'risk_alerts': """
                CREATE TABLE IF NOT EXISTS risk_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(255) NOT NULL UNIQUE,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    description TEXT NOT NULL,
                    affected_addresses JSONB NOT NULL,
                    affected_protocols JSONB NOT NULL,
                    risk_score DECIMAL(5,4) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 1),
                    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                    detection_method VARCHAR(100) NOT NULL,
                    evidence JSONB NOT NULL,
                    recommendations JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    acknowledged_at TIMESTAMP WITH TIME ZONE NULL,
                    resolved_at TIMESTAMP WITH TIME ZONE NULL,
                    acknowledged_by VARCHAR(255) NULL,
                    resolved_by VARCHAR(255) NULL,
                    INDEX(alert_type),
                    INDEX(severity),
                    INDEX(risk_score),
                    INDEX(created_at),
                    INDEX(acknowledged_at),
                    INDEX(resolved_at)
                );
            """,

            'mev_patterns': """
                CREATE TABLE IF NOT EXISTS mev_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_id VARCHAR(255) NOT NULL UNIQUE,
                    mev_type VARCHAR(50) NOT NULL,
                    transaction_ids JSONB NOT NULL,
                    extracted_value DECIMAL(30,6) NOT NULL,
                    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
                    victim_addresses JSONB NOT NULL,
                    exploiter_address VARCHAR(255) NOT NULL,
                    time_window_seconds INTEGER NOT NULL,
                    detection_method VARCHAR(100) NOT NULL,
                    evidence JSONB NOT NULL,
                    block_number INTEGER NOT NULL,
                    detection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(mev_type),
                    INDEX(exploiter_address),
                    INDEX(block_number),
                    INDEX(detection_timestamp),
                    INDEX(confidence_score)
                );
            """,

            'wallet_clusters': """
                CREATE TABLE IF NOT EXISTS wallet_clusters (
                    id SERIAL PRIMARY KEY,
                    cluster_id VARCHAR(255) NOT NULL UNIQUE,
                    wallet_addresses JSONB NOT NULL,
                    cluster_score DECIMAL(5,4) NOT NULL CHECK (cluster_score >= 0 AND cluster_score <= 1),
                    connection_strength DECIMAL(5,4) NOT NULL,
                    shared_behaviors JSONB NOT NULL,
                    risk_indicators JSONB NOT NULL,
                    first_activity TIMESTAMP WITH TIME ZONE NOT NULL,
                    last_activity TIMESTAMP WITH TIME ZONE NOT NULL,
                    total_volume DECIMAL(30,6) NOT NULL,
                    transaction_count INTEGER NOT NULL,
                    detection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(cluster_score),
                    INDEX(connection_strength),
                    INDEX(detection_timestamp),
                    INDEX(first_activity),
                    INDEX(last_activity)
                );
            """,

            'bridge_activities': """
                CREATE TABLE IF NOT EXISTS bridge_activities (
                    id SERIAL PRIMARY KEY,
                    bridge_name VARCHAR(255) NOT NULL,
                    bridge_type VARCHAR(50) NOT NULL,
                    source_chain VARCHAR(100) NOT NULL,
                    destination_chain VARCHAR(100) NOT NULL,
                    asset_symbol VARCHAR(50) NOT NULL,
                    amount DECIMAL(30,6) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    transaction_hash VARCHAR(255) NOT NULL,
                    user_address VARCHAR(255) NOT NULL,
                    bridge_fee DECIMAL(30,6) NOT NULL,
                    confirmation_time_seconds INTEGER NOT NULL,
                    risk_score DECIMAL(5,4) CHECK (risk_score >= 0 AND risk_score <= 1),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(bridge_name),
                    INDEX(user_address),
                    INDEX(timestamp),
                    INDEX(source_chain),
                    INDEX(destination_chain),
                    INDEX(asset_symbol)
                );
            """,

            'defi_exposures': """
                CREATE TABLE IF NOT EXISTS defi_exposures (
                    id SERIAL PRIMARY KEY,
                    entity_id VARCHAR(255) NOT NULL,
                    protocol_name VARCHAR(255) NOT NULL,
                    tvl_exposure DECIMAL(30,6) NOT NULL,
                    position_size DECIMAL(30,6) NOT NULL,
                    concentration_risk DECIMAL(5,4) NOT NULL CHECK (concentration_risk >= 0 AND concentration_risk <= 1),
                    liquidity_risk DECIMAL(5,4) NOT NULL CHECK (liquidity_risk >= 0 AND liquidity_risk <= 1),
                    smart_contract_risk DECIMAL(5,4) NOT NULL CHECK (smart_contract_risk >= 0 AND smart_contract_risk <= 1),
                    governance_participation BOOLEAN NOT NULL DEFAULT FALSE,
                    staking_positions JSONB NOT NULL,
                    yield_farming_positions JSONB NOT NULL,
                    cross_protocol_correlations JSONB NOT NULL,
                    exposure_duration_days INTEGER NOT NULL,
                    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(entity_id),
                    INDEX(protocol_name),
                    INDEX(concentration_risk),
                    INDEX(liquidity_risk),
                    INDEX(smart_contract_risk),
                    INDEX(last_updated)
                );
            """,

            'risk_mitigations': """
                CREATE TABLE IF NOT EXISTS risk_mitigations (
                    id SERIAL PRIMARY KEY,
                    mitigation_id VARCHAR(255) NOT NULL UNIQUE,
                    risk_type VARCHAR(50) NOT NULL,
                    strategy VARCHAR(500) NOT NULL,
                    implementation_steps JSONB NOT NULL,
                    effectiveness_score DECIMAL(5,4) NOT NULL CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
                    cost_estimate DECIMAL(20,6) NOT NULL,
                    timeline_days INTEGER NOT NULL,
                    prerequisites JSONB NOT NULL,
                    monitoring_requirements JSONB NOT NULL,
                    success_metrics JSONB NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'proposed',
                    implemented_at TIMESTAMP WITH TIME ZONE NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    INDEX(risk_type),
                    INDEX(effectiveness_score),
                    INDEX(status),
                    INDEX(created_at)
                );
            """
        }

    @staticmethod
    def get_indexes_sql() -> List[str]:
        """Get additional index creation SQL statements"""
        return [
            # Performance indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_profiles_entity_risk ON risk_profiles(entity_id, overall_risk_score);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_patterns_wallet_type ON transaction_patterns(wallet_address, pattern_type);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_anomalies_unresolved ON anomaly_detections(entity_id) WHERE resolved_at IS NULL;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_active ON risk_alerts(alert_type, severity) WHERE resolved_at IS NULL;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_correlations_recent ON correlation_pairs(correlation_type, calculation_timestamp) WHERE calculation_timestamp > NOW() - INTERVAL '7 days';",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mev_recent ON mev_patterns(mev_type, detection_timestamp) WHERE detection_timestamp > NOW() - INTERVAL '30 days';",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bridge_activities_recent ON bridge_activities(bridge_name, timestamp) WHERE timestamp > NOW() - INTERVAL '7 days';",

            # GIN indexes for JSONB columns
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_profiles_factors_gin ON risk_profiles USING GIN (risk_factor_scores);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_patterns_anomalies_gin ON transaction_patterns USING GIN (anomaly_indicators);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_anomaly_evidence_gin ON anomaly_detections USING GIN (evidence);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_affected_addresses_gin ON risk_alerts USING GIN (affected_addresses);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mev_evidence_gin ON mev_patterns USING GIN (evidence);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cluster_addresses_gin ON wallet_clusters USING GIN (wallet_addresses);",

            # Partial indexes for specific queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_high_risk_profiles ON risk_profiles(entity_id, overall_risk_score) WHERE overall_risk_score > 0.7;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_high_confidence_patterns ON transaction_patterns(pattern_type, confidence_score) WHERE confidence_score > 0.8;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_critical_alerts ON risk_alerts(created_at) WHERE severity = 'CRITICAL';",
        ]

    @staticmethod
    def get_views_sql() -> Dict[str, str]:
        """Get view creation SQL statements"""
        return {
            'risk_summary_view': """
                CREATE OR REPLACE VIEW risk_summary_view AS
                SELECT
                    rp.entity_id,
                    rp.entity_type,
                    rp.overall_risk_score,
                    rp.risk_level,
                    rp.confidence_score,
                    rp.assessment_timestamp,
                    COUNT(ra.id) as active_alerts,
                    COUNT(CASE WHEN ra.severity = 'CRITICAL' THEN 1 END) as critical_alerts,
                    COUNT(CASE WHEN ra.severity = 'HIGH' THEN 1 END) as high_alerts,
                    MAX(tp.confidence_score) as max_pattern_confidence,
                    COUNT(ad.id) as unresolved_anomalies
                FROM risk_profiles rp
                LEFT JOIN risk_alerts ra ON rp.entity_id = ANY(SELECT jsonb_array_elements_text(ra.affected_addresses))
                    AND ra.resolved_at IS NULL
                LEFT JOIN transaction_patterns tp ON rp.entity_id = tp.wallet_address
                    AND tp.detection_timestamp > NOW() - INTERVAL '30 days'
                LEFT JOIN anomaly_detections ad ON rp.entity_id = ad.entity_id
                    AND ad.resolved_at IS NULL
                WHERE rp.assessment_timestamp > NOW() - INTERVAL '7 days'
                GROUP BY rp.entity_id, rp.entity_type, rp.overall_risk_score,
                         rp.risk_level, rp.confidence_score, rp.assessment_timestamp;
            """,

            'correlation_trends_view': """
                CREATE OR REPLACE VIEW correlation_trends_view AS
                SELECT
                    cp.entity_a,
                    cp.entity_b,
                    cp.correlation_type,
                    cp.correlation_coefficient,
                    LAG(cp.correlation_coefficient) OVER (
                        PARTITION BY cp.entity_a, cp.entity_b, cp.correlation_type
                        ORDER BY cp.calculation_timestamp
                    ) as prev_correlation,
                    cp.correlation_coefficient - LAG(cp.correlation_coefficient) OVER (
                        PARTITION BY cp.entity_a, cp.entity_b, cp.correlation_type
                        ORDER BY cp.calculation_timestamp
                    ) as correlation_change,
                    cp.calculation_timestamp
                FROM correlation_pairs cp
                WHERE cp.calculation_timestamp > NOW() - INTERVAL '90 days'
                ORDER BY cp.calculation_timestamp DESC;
            """,

            'mev_analytics_view': """
                CREATE OR REPLACE VIEW mev_analytics_view AS
                SELECT
                    DATE_TRUNC('day', mp.detection_timestamp) as date,
                    mp.mev_type,
                    COUNT(*) as pattern_count,
                    SUM(mp.extracted_value) as total_extracted_value,
                    AVG(mp.confidence_score) as avg_confidence,
                    COUNT(DISTINCT mp.exploiter_address) as unique_exploiters,
                    AVG(mp.time_window_seconds) as avg_time_window
                FROM mev_patterns mp
                WHERE mp.detection_timestamp > NOW() - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', mp.detection_timestamp), mp.mev_type
                ORDER BY date DESC, total_extracted_value DESC;
            """,

            'bridge_risk_view': """
                CREATE OR REPLACE VIEW bridge_risk_view AS
                SELECT
                    ba.bridge_name,
                    ba.bridge_type,
                    COUNT(*) as transaction_count,
                    SUM(ba.amount) as total_volume,
                    AVG(ba.amount) as avg_transaction_size,
                    COUNT(DISTINCT ba.user_address) as unique_users,
                    AVG(ba.confirmation_time_seconds) as avg_confirmation_time,
                    AVG(ba.risk_score) as avg_risk_score,
                    MAX(ba.timestamp) as last_activity
                FROM bridge_activities ba
                WHERE ba.timestamp > NOW() - INTERVAL '7 days'
                GROUP BY ba.bridge_name, ba.bridge_type
                ORDER BY avg_risk_score DESC, total_volume DESC;
            """
        }

    @staticmethod
    def get_functions_sql() -> Dict[str, str]:
        """Get stored function creation SQL statements"""
        return {
            'calculate_portfolio_risk': """
                CREATE OR REPLACE FUNCTION calculate_portfolio_risk(
                    wallet_addresses TEXT[]
                ) RETURNS TABLE(
                    overall_risk DECIMAL(5,4),
                    risk_breakdown JSONB
                ) AS $$
                DECLARE
                    risk_data JSONB;
                    total_weight DECIMAL := 0;
                    weighted_risk DECIMAL := 0;
                BEGIN
                    -- Calculate weighted portfolio risk
                    SELECT jsonb_object_agg(
                        rp.entity_id,
                        jsonb_build_object(
                            'risk_score', rp.overall_risk_score,
                            'weight', 1.0 / array_length(wallet_addresses, 1)
                        )
                    ) INTO risk_data
                    FROM risk_profiles rp
                    WHERE rp.entity_id = ANY(wallet_addresses)
                    AND rp.assessment_timestamp > NOW() - INTERVAL '7 days';

                    -- Calculate weighted average
                    SELECT
                        SUM((value->>'risk_score')::DECIMAL * (value->>'weight')::DECIMAL),
                        SUM((value->>'weight')::DECIMAL)
                    INTO weighted_risk, total_weight
                    FROM jsonb_each(risk_data);

                    RETURN QUERY SELECT
                        CASE WHEN total_weight > 0 THEN weighted_risk / total_weight ELSE 0.0 END,
                        risk_data;
                END;
                $$ LANGUAGE plpgsql;
            """,

            'get_risk_trends': """
                CREATE OR REPLACE FUNCTION get_risk_trends(
                    entity_id_param VARCHAR(255),
                    days_back INTEGER DEFAULT 30
                ) RETURNS TABLE(
                    date DATE,
                    risk_score DECIMAL(5,4),
                    risk_level VARCHAR(20),
                    alert_count INTEGER
                ) AS $$
                BEGIN
                    RETURN QUERY
                    WITH daily_risk AS (
                        SELECT
                            DATE(rp.assessment_timestamp) as assessment_date,
                            rp.overall_risk_score,
                            rp.risk_level,
                            ROW_NUMBER() OVER (
                                PARTITION BY DATE(rp.assessment_timestamp)
                                ORDER BY rp.assessment_timestamp DESC
                            ) as rn
                        FROM risk_profiles rp
                        WHERE rp.entity_id = entity_id_param
                        AND rp.assessment_timestamp > NOW() - INTERVAL '1 day' * days_back
                    ),
                    daily_alerts AS (
                        SELECT
                            DATE(ra.created_at) as alert_date,
                            COUNT(*) as alert_count
                        FROM risk_alerts ra
                        WHERE entity_id_param = ANY(SELECT jsonb_array_elements_text(ra.affected_addresses))
                        AND ra.created_at > NOW() - INTERVAL '1 day' * days_back
                        GROUP BY DATE(ra.created_at)
                    )
                    SELECT
                        dr.assessment_date,
                        dr.overall_risk_score,
                        dr.risk_level,
                        COALESCE(da.alert_count, 0)::INTEGER
                    FROM daily_risk dr
                    LEFT JOIN daily_alerts da ON dr.assessment_date = da.alert_date
                    WHERE dr.rn = 1
                    ORDER BY dr.assessment_date;
                END;
                $$ LANGUAGE plpgsql;
            """
        }

    @staticmethod
    def get_cleanup_sql() -> List[str]:
        """Get data cleanup SQL statements"""
        return [
            # Clean old correlation data
            "DELETE FROM correlation_pairs WHERE calculation_timestamp < NOW() - INTERVAL '90 days';",

            # Clean resolved alerts older than 6 months
            "DELETE FROM risk_alerts WHERE resolved_at IS NOT NULL AND resolved_at < NOW() - INTERVAL '6 months';",

            # Clean old anomaly detections
            "DELETE FROM anomaly_detections WHERE resolved_at IS NOT NULL AND resolved_at < NOW() - INTERVAL '90 days';",

            # Clean old transaction patterns
            "DELETE FROM transaction_patterns WHERE detection_timestamp < NOW() - INTERVAL '90 days';",

            # Clean old bridge activities
            "DELETE FROM bridge_activities WHERE timestamp < NOW() - INTERVAL '180 days';",

            # Clean old cascade simulations
            "DELETE FROM cascade_simulations WHERE created_at < NOW() - INTERVAL '90 days';",
            "DELETE FROM cascade_events WHERE created_at < NOW() - INTERVAL '90 days';",
        ]