"""
Database Models for Risk Assessment

SQLAlchemy models for blockchain risk assessment data.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, Boolean, Text,
    JSON, Index, UniqueConstraint, CheckConstraint, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()


class RiskProfileTable(Base):
    """Risk profile table model"""
    __tablename__ = 'risk_profiles'

    id = Column(Integer, primary_key=True)
    entity_id = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    assessment_timestamp = Column(DateTime(timezone=True), nullable=False)
    overall_risk_score = Column(Numeric(5, 4), nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    risk_factor_scores = Column(JSONB, nullable=False)
    risk_factor_weights = Column(JSONB, nullable=False)
    data_completeness = Column(Numeric(5, 4), nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        UniqueConstraint('entity_id', 'entity_type', name='uq_risk_profile_entity'),
        CheckConstraint('overall_risk_score >= 0 AND overall_risk_score <= 1', name='ck_overall_risk_score'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='ck_confidence_score'),
        CheckConstraint('data_completeness >= 0 AND data_completeness <= 1', name='ck_data_completeness'),
        Index('idx_risk_profiles_entity_id', 'entity_id'),
        Index('idx_risk_profiles_entity_type', 'entity_type'),
        Index('idx_risk_profiles_risk_level', 'risk_level'),
        Index('idx_risk_profiles_assessment_timestamp', 'assessment_timestamp'),
        Index('idx_risk_profiles_overall_risk_score', 'overall_risk_score'),
    )


class TransactionPatternTable(Base):
    """Transaction pattern table model"""
    __tablename__ = 'transaction_patterns'

    id = Column(Integer, primary_key=True)
    wallet_address = Column(String(255), nullable=False)
    pattern_type = Column(String(50), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    time_window_hours = Column(Integer, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    total_volume = Column(Numeric(30, 6), nullable=False)
    velocity_score = Column(Numeric(10, 4), nullable=False)
    anomaly_indicators = Column(JSONB, nullable=False)
    risk_factors = Column(JSONB, nullable=False)
    detection_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='ck_confidence_score'),
        Index('idx_transaction_patterns_wallet_address', 'wallet_address'),
        Index('idx_transaction_patterns_pattern_type', 'pattern_type'),
        Index('idx_transaction_patterns_confidence_score', 'confidence_score'),
        Index('idx_transaction_patterns_detection_timestamp', 'detection_timestamp'),
    )


class AnomalyTable(Base):
    """Anomaly detection table model"""
    __tablename__ = 'anomaly_detections'

    id = Column(Integer, primary_key=True)
    entity_id = Column(String(255), nullable=False)
    anomaly_type = Column(String(50), nullable=False)
    anomaly_score = Column(Numeric(5, 4), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    deviation_magnitude = Column(Numeric(10, 4), nullable=False)
    baseline_reference = Column(Numeric(20, 6))
    evidence = Column(JSONB, nullable=False)
    detection_method = Column(String(100), nullable=False)
    detection_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('anomaly_score >= 0 AND anomaly_score <= 1', name='ck_anomaly_score'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_confidence'),
        Index('idx_anomaly_detections_entity_id', 'entity_id'),
        Index('idx_anomaly_detections_anomaly_type', 'anomaly_type'),
        Index('idx_anomaly_detections_anomaly_score', 'anomaly_score'),
        Index('idx_anomaly_detections_detection_timestamp', 'detection_timestamp'),
        Index('idx_anomaly_detections_resolved_at', 'resolved_at'),
    )


class CorrelationTable(Base):
    """Correlation pairs table model"""
    __tablename__ = 'correlation_pairs'

    id = Column(Integer, primary_key=True)
    entity_a = Column(String(255), nullable=False)
    entity_b = Column(String(255), nullable=False)
    correlation_type = Column(String(50), nullable=False)
    correlation_coefficient = Column(Numeric(6, 5), nullable=False)
    confidence_interval_lower = Column(Numeric(6, 5), nullable=False)
    confidence_interval_upper = Column(Numeric(6, 5), nullable=False)
    p_value = Column(Numeric(10, 8), nullable=False)
    sample_size = Column(Integer, nullable=False)
    time_period_days = Column(Integer, nullable=False)
    calculation_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('correlation_coefficient >= -1 AND correlation_coefficient <= 1', name='ck_correlation_coefficient'),
        UniqueConstraint('entity_a', 'entity_b', 'correlation_type', 'calculation_timestamp', name='uq_correlation_pair'),
        Index('idx_correlation_pairs_entity_a', 'entity_a'),
        Index('idx_correlation_pairs_entity_b', 'entity_b'),
        Index('idx_correlation_pairs_correlation_type', 'correlation_type'),
        Index('idx_correlation_pairs_correlation_coefficient', 'correlation_coefficient'),
        Index('idx_correlation_pairs_calculation_timestamp', 'calculation_timestamp'),
    )


class CascadeEventTable(Base):
    """Cascade event table model"""
    __tablename__ = 'cascade_events'

    id = Column(Integer, primary_key=True)
    event_id = Column(String(255), nullable=False, unique=True)
    simulation_id = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    affected_node = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(Numeric(5, 4), nullable=False)
    caused_by = Column(String(255))
    impact_magnitude = Column(Numeric(5, 4), nullable=False)
    recovery_estimate_hours = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('severity >= 0 AND severity <= 1', name='ck_severity'),
        Index('idx_cascade_events_simulation_id', 'simulation_id'),
        Index('idx_cascade_events_affected_node', 'affected_node'),
        Index('idx_cascade_events_event_type', 'event_type'),
        Index('idx_cascade_events_timestamp', 'timestamp'),
        Index('idx_cascade_events_caused_by', 'caused_by'),
    )


class CascadeSimulationTable(Base):
    """Cascade simulation table model"""
    __tablename__ = 'cascade_simulations'

    id = Column(Integer, primary_key=True)
    simulation_id = Column(String(255), nullable=False, unique=True)
    scenario_type = Column(String(50), nullable=False)
    initial_shock = Column(JSONB, nullable=False)
    final_state = Column(JSONB, nullable=False)
    total_impact = Column(Numeric(10, 6), nullable=False)
    affected_nodes = Column(JSONB, nullable=False)
    cascade_depth = Column(Integer, nullable=False)
    simulation_duration_hours = Column(Numeric(10, 2), nullable=False)
    peak_impact_time = Column(DateTime(timezone=True), nullable=False)
    recovery_scenarios = Column(JSONB, nullable=False)
    market_conditions = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        Index('idx_cascade_simulations_scenario_type', 'scenario_type'),
        Index('idx_cascade_simulations_total_impact', 'total_impact'),
        Index('idx_cascade_simulations_cascade_depth', 'cascade_depth'),
        Index('idx_cascade_simulations_created_at', 'created_at'),
    )


class AlertTable(Base):
    """Risk alert table model"""
    __tablename__ = 'risk_alerts'

    id = Column(Integer, primary_key=True)
    alert_id = Column(String(255), nullable=False, unique=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    affected_addresses = Column(JSONB, nullable=False)
    affected_protocols = Column(JSONB, nullable=False)
    risk_score = Column(Numeric(5, 4), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    detection_method = Column(String(100), nullable=False)
    evidence = Column(JSONB, nullable=False)
    recommendations = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(255))
    resolved_by = Column(String(255))

    __table_args__ = (
        CheckConstraint('risk_score >= 0 AND risk_score <= 1', name='ck_risk_score'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_confidence'),
        Index('idx_risk_alerts_alert_type', 'alert_type'),
        Index('idx_risk_alerts_severity', 'severity'),
        Index('idx_risk_alerts_risk_score', 'risk_score'),
        Index('idx_risk_alerts_created_at', 'created_at'),
        Index('idx_risk_alerts_acknowledged_at', 'acknowledged_at'),
        Index('idx_risk_alerts_resolved_at', 'resolved_at'),
    )


class MEVPatternTable(Base):
    """MEV pattern table model"""
    __tablename__ = 'mev_patterns'

    id = Column(Integer, primary_key=True)
    pattern_id = Column(String(255), nullable=False, unique=True)
    mev_type = Column(String(50), nullable=False)
    transaction_ids = Column(JSONB, nullable=False)
    extracted_value = Column(Numeric(30, 6), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    victim_addresses = Column(JSONB, nullable=False)
    exploiter_address = Column(String(255), nullable=False)
    time_window_seconds = Column(Integer, nullable=False)
    detection_method = Column(String(100), nullable=False)
    evidence = Column(JSONB, nullable=False)
    block_number = Column(Integer, nullable=False)
    detection_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='ck_confidence_score'),
        Index('idx_mev_patterns_mev_type', 'mev_type'),
        Index('idx_mev_patterns_exploiter_address', 'exploiter_address'),
        Index('idx_mev_patterns_block_number', 'block_number'),
        Index('idx_mev_patterns_detection_timestamp', 'detection_timestamp'),
        Index('idx_mev_patterns_confidence_score', 'confidence_score'),
    )


class WalletClusterTable(Base):
    """Wallet cluster table model"""
    __tablename__ = 'wallet_clusters'

    id = Column(Integer, primary_key=True)
    cluster_id = Column(String(255), nullable=False, unique=True)
    wallet_addresses = Column(JSONB, nullable=False)
    cluster_score = Column(Numeric(5, 4), nullable=False)
    connection_strength = Column(Numeric(5, 4), nullable=False)
    shared_behaviors = Column(JSONB, nullable=False)
    risk_indicators = Column(JSONB, nullable=False)
    first_activity = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    total_volume = Column(Numeric(30, 6), nullable=False)
    transaction_count = Column(Integer, nullable=False)
    detection_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('cluster_score >= 0 AND cluster_score <= 1', name='ck_cluster_score'),
        Index('idx_wallet_clusters_cluster_score', 'cluster_score'),
        Index('idx_wallet_clusters_connection_strength', 'connection_strength'),
        Index('idx_wallet_clusters_detection_timestamp', 'detection_timestamp'),
        Index('idx_wallet_clusters_first_activity', 'first_activity'),
        Index('idx_wallet_clusters_last_activity', 'last_activity'),
    )


class BridgeActivityTable(Base):
    """Bridge activity table model"""
    __tablename__ = 'bridge_activities'

    id = Column(Integer, primary_key=True)
    bridge_name = Column(String(255), nullable=False)
    bridge_type = Column(String(50), nullable=False)
    source_chain = Column(String(100), nullable=False)
    destination_chain = Column(String(100), nullable=False)
    asset_symbol = Column(String(50), nullable=False)
    amount = Column(Numeric(30, 6), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    transaction_hash = Column(String(255), nullable=False)
    user_address = Column(String(255), nullable=False)
    bridge_fee = Column(Numeric(30, 6), nullable=False)
    confirmation_time_seconds = Column(Integer, nullable=False)
    risk_score = Column(Numeric(5, 4))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1)', name='ck_risk_score'),
        Index('idx_bridge_activities_bridge_name', 'bridge_name'),
        Index('idx_bridge_activities_user_address', 'user_address'),
        Index('idx_bridge_activities_timestamp', 'timestamp'),
        Index('idx_bridge_activities_source_chain', 'source_chain'),
        Index('idx_bridge_activities_destination_chain', 'destination_chain'),
        Index('idx_bridge_activities_asset_symbol', 'asset_symbol'),
    )


class DeFiExposureTable(Base):
    """DeFi exposure table model"""
    __tablename__ = 'defi_exposures'

    id = Column(Integer, primary_key=True)
    entity_id = Column(String(255), nullable=False)
    protocol_name = Column(String(255), nullable=False)
    tvl_exposure = Column(Numeric(30, 6), nullable=False)
    position_size = Column(Numeric(30, 6), nullable=False)
    concentration_risk = Column(Numeric(5, 4), nullable=False)
    liquidity_risk = Column(Numeric(5, 4), nullable=False)
    smart_contract_risk = Column(Numeric(5, 4), nullable=False)
    governance_participation = Column(Boolean, nullable=False, default=False)
    staking_positions = Column(JSONB, nullable=False)
    yield_farming_positions = Column(JSONB, nullable=False)
    cross_protocol_correlations = Column(JSONB, nullable=False)
    exposure_duration_days = Column(Integer, nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('concentration_risk >= 0 AND concentration_risk <= 1', name='ck_concentration_risk'),
        CheckConstraint('liquidity_risk >= 0 AND liquidity_risk <= 1', name='ck_liquidity_risk'),
        CheckConstraint('smart_contract_risk >= 0 AND smart_contract_risk <= 1', name='ck_smart_contract_risk'),
        Index('idx_defi_exposures_entity_id', 'entity_id'),
        Index('idx_defi_exposures_protocol_name', 'protocol_name'),
        Index('idx_defi_exposures_concentration_risk', 'concentration_risk'),
        Index('idx_defi_exposures_liquidity_risk', 'liquidity_risk'),
        Index('idx_defi_exposures_smart_contract_risk', 'smart_contract_risk'),
        Index('idx_defi_exposures_last_updated', 'last_updated'),
    )


class RiskMitigationTable(Base):
    """Risk mitigation table model"""
    __tablename__ = 'risk_mitigations'

    id = Column(Integer, primary_key=True)
    mitigation_id = Column(String(255), nullable=False, unique=True)
    risk_type = Column(String(50), nullable=False)
    strategy = Column(String(500), nullable=False)
    implementation_steps = Column(JSONB, nullable=False)
    effectiveness_score = Column(Numeric(5, 4), nullable=False)
    cost_estimate = Column(Numeric(20, 6), nullable=False)
    timeline_days = Column(Integer, nullable=False)
    prerequisites = Column(JSONB, nullable=False)
    monitoring_requirements = Column(JSONB, nullable=False)
    success_metrics = Column(JSONB, nullable=False)
    status = Column(String(50), nullable=False, default='proposed')
    implemented_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        CheckConstraint('effectiveness_score >= 0 AND effectiveness_score <= 1', name='ck_effectiveness_score'),
        Index('idx_risk_mitigations_risk_type', 'risk_type'),
        Index('idx_risk_mitigations_effectiveness_score', 'effectiveness_score'),
        Index('idx_risk_mitigations_status', 'status'),
        Index('idx_risk_mitigations_created_at', 'created_at'),
    )