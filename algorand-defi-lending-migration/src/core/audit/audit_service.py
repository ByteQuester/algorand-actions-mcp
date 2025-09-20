"""
Audit Service Layer

Business logic layer for audit trail retrieval and processing.
Provides high-level operations for session data, decisions, tools, and compliance.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from uuid import UUID
import asyncpg
import json
from dataclasses import asdict

from .models import (
    AuditTrail, DecisionPoint, ComplianceEvent, AuditSession,
    AuditEventType, DecisionType, AuditSeverity
)

logger = logging.getLogger(__name__)


class AuditService:
    """
    High-performance audit service for retrieval and analysis

    Provides business logic for:
    - Session timeline reconstruction
    - Decision reasoning chains
    - Tool usage analytics
    - Real-time audit data processing
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection_pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=30
            )
            logger.info("Audit service initialized with database connection pool")
        except Exception as e:
            logger.error(f"Failed to initialize audit service: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Audit service connection pool closed")

    async def get_session_timeline(self, loan_id: str) -> Dict[str, Any]:
        """
        Get complete session timeline for a loan

        Returns:
            Complete chronological timeline with session grouping
        """
        async with self.connection_pool.acquire() as conn:
            # Get all audit events for the loan
            events_query = """
                SELECT
                    at.id,
                    at.event_type,
                    at.severity,
                    at.timestamp,
                    at.event_data,
                    at.service_name,
                    at.session_id,
                    at.correlation_id,
                    at.trace_id,
                    at.span_id
                FROM audit_trails at
                WHERE at.event_data->>'loan_id' = $1
                ORDER BY at.timestamp ASC
            """

            # Get session information
            sessions_query = """
                SELECT DISTINCT
                    s.session_id,
                    s.user_id,
                    s.session_start,
                    s.session_end,
                    s.session_duration_ms,
                    s.ip_address,
                    s.user_agent,
                    s.event_count,
                    s.error_count,
                    s.warning_count,
                    s.loans_processed,
                    s.transactions_created,
                    s.decisions_made,
                    s.is_active
                FROM audit_sessions s
                JOIN audit_trails at ON s.session_id = at.session_id
                WHERE at.event_data->>'loan_id' = $1
                ORDER BY s.session_start ASC
            """

            # Execute both queries concurrently
            events_result, sessions_result = await asyncio.gather(
                conn.fetch(events_query, loan_id),
                conn.fetch(sessions_query, loan_id)
            )

            # Process events
            events = []
            for row in events_result:
                event = {
                    'id': str(row['id']),
                    'event_type': row['event_type'],
                    'severity': row['severity'],
                    'timestamp': row['timestamp'].isoformat(),
                    'event_data': dict(row['event_data']),
                    'service_name': row['service_name'],
                    'session_id': row['session_id'],
                    'correlation_id': row['correlation_id'],
                    'trace_id': row['trace_id'],
                    'span_id': row['span_id']
                }
                events.append(event)

            # Process sessions
            sessions = []
            for row in sessions_result:
                session = {
                    'session_id': row['session_id'],
                    'user_id': row['user_id'],
                    'session_start': row['session_start'].isoformat(),
                    'session_end': row['session_end'].isoformat() if row['session_end'] else None,
                    'session_duration_ms': row['session_duration_ms'],
                    'ip_address': row['ip_address'],
                    'user_agent': row['user_agent'],
                    'event_count': row['event_count'],
                    'error_count': row['error_count'],
                    'warning_count': row['warning_count'],
                    'loans_processed': row['loans_processed'],
                    'transactions_created': row['transactions_created'],
                    'decisions_made': row['decisions_made'],
                    'is_active': row['is_active']
                }
                sessions.append(session)

            # Create session-grouped timeline
            session_map = {s['session_id']: s for s in sessions}
            for event in events:
                if event['session_id'] and event['session_id'] in session_map:
                    event['session_info'] = session_map[event['session_id']]

            return {
                'loan_id': loan_id,
                'total_events': len(events),
                'total_sessions': len(sessions),
                'timeline_start': events[0]['timestamp'] if events else None,
                'timeline_end': events[-1]['timestamp'] if events else None,
                'sessions': sessions,
                'events': events
            }

    async def get_decision_breakdown(self, loan_id: str) -> Dict[str, Any]:
        """
        Get complete decision breakdown with reasoning chains

        Returns:
            All decisions made during loan processing with full context
        """
        async with self.connection_pool.acquire() as conn:
            # Get all decision points for the loan
            decisions_query = """
                SELECT
                    dp.id,
                    dp.decision_type,
                    dp.decision_timestamp,
                    dp.decision_maker,
                    dp.decision_rationale,
                    dp.decision_outcome,
                    dp.input_data,
                    dp.risk_factors,
                    dp.compliance_flags,
                    dp.regulatory_requirements,
                    dp.confidence_score,
                    dp.risk_score,
                    dp.audit_event_id,
                    at.event_type,
                    at.timestamp as audit_timestamp,
                    at.event_data as audit_data
                FROM decision_points dp
                JOIN audit_trails at ON dp.audit_event_id = at.id
                WHERE dp.loan_id = $1
                ORDER BY dp.decision_timestamp ASC
            """

            result = await conn.fetch(decisions_query, loan_id)

            decisions = []
            decision_chain = []

            for row in result:
                decision = {
                    'id': str(row['id']),
                    'decision_type': row['decision_type'],
                    'decision_timestamp': row['decision_timestamp'].isoformat(),
                    'decision_maker': row['decision_maker'],
                    'decision_rationale': row['decision_rationale'],
                    'decision_outcome': row['decision_outcome'],
                    'input_data': dict(row['input_data']),
                    'risk_factors': list(row['risk_factors']) if row['risk_factors'] else [],
                    'compliance_flags': list(row['compliance_flags']) if row['compliance_flags'] else [],
                    'regulatory_requirements': list(row['regulatory_requirements']) if row['regulatory_requirements'] else [],
                    'confidence_score': float(row['confidence_score']) if row['confidence_score'] else None,
                    'risk_score': float(row['risk_score']) if row['risk_score'] else None,
                    'audit_event': {
                        'id': str(row['audit_event_id']),
                        'event_type': row['event_type'],
                        'timestamp': row['audit_timestamp'].isoformat(),
                        'event_data': dict(row['audit_data'])
                    }
                }
                decisions.append(decision)

                # Build decision chain summary
                decision_chain.append({
                    'type': row['decision_type'],
                    'timestamp': row['decision_timestamp'].isoformat(),
                    'outcome': row['decision_outcome'],
                    'confidence': float(row['confidence_score']) if row['confidence_score'] else None
                })

            # Calculate decision metrics
            risk_scores = [d['risk_score'] for d in decisions if d['risk_score'] is not None]
            confidence_scores = [d['confidence_score'] for d in decisions if d['confidence_score'] is not None]

            return {
                'loan_id': loan_id,
                'total_decisions': len(decisions),
                'decision_types': list(set(d['decision_type'] for d in decisions)),
                'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else None,
                'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else None,
                'decision_chain': decision_chain,
                'decisions': decisions
            }

    async def get_tool_usage_analysis(self, loan_id: str) -> Dict[str, Any]:
        """
        Get tool usage and impact analysis

        Returns:
            Analysis of all tools used and their impact on loan processing
        """
        async with self.connection_pool.acquire() as conn:
            # Get all tool execution events
            tools_query = """
                SELECT
                    at.id,
                    at.timestamp,
                    at.event_data,
                    at.service_name,
                    at.session_id,
                    at.severity
                FROM audit_trails at
                WHERE at.event_data->>'loan_id' = $1
                  AND at.event_type = 'tool_executed'
                ORDER BY at.timestamp ASC
            """

            # Get performance metrics for tools
            performance_query = """
                SELECT
                    at.event_data->>'tool_name' as tool_name,
                    COUNT(*) as execution_count,
                    AVG(CAST(at.event_data->>'processing_time_ms' AS FLOAT)) as avg_processing_time,
                    MAX(CAST(at.event_data->>'processing_time_ms' AS FLOAT)) as max_processing_time,
                    MIN(CAST(at.event_data->>'processing_time_ms' AS FLOAT)) as min_processing_time,
                    COUNT(*) FILTER (WHERE at.severity = 'error') as error_count,
                    COUNT(*) FILTER (WHERE at.severity = 'warning') as warning_count
                FROM audit_trails at
                WHERE at.event_data->>'loan_id' = $1
                  AND at.event_type = 'tool_executed'
                  AND at.event_data->>'tool_name' IS NOT NULL
                GROUP BY at.event_data->>'tool_name'
                ORDER BY execution_count DESC
            """

            tools_result, performance_result = await asyncio.gather(
                conn.fetch(tools_query, loan_id),
                conn.fetch(performance_query, loan_id)
            )

            # Process tool executions
            tool_executions = []
            for row in tools_result:
                execution = {
                    'id': str(row['id']),
                    'timestamp': row['timestamp'].isoformat(),
                    'tool_name': row['event_data'].get('tool_name'),
                    'tool_input': row['event_data'].get('tool_input'),
                    'tool_output': row['event_data'].get('tool_output'),
                    'processing_time_ms': row['event_data'].get('processing_time_ms'),
                    'memory_usage_mb': row['event_data'].get('memory_usage_mb'),
                    'error_code': row['event_data'].get('error_code'),
                    'error_message': row['event_data'].get('error_message'),
                    'service_name': row['service_name'],
                    'session_id': row['session_id'],
                    'severity': row['severity']
                }
                tool_executions.append(execution)

            # Process performance metrics
            tool_performance = []
            for row in performance_result:
                performance = {
                    'tool_name': row['tool_name'],
                    'execution_count': row['execution_count'],
                    'avg_processing_time_ms': float(row['avg_processing_time']) if row['avg_processing_time'] else None,
                    'max_processing_time_ms': float(row['max_processing_time']) if row['max_processing_time'] else None,
                    'min_processing_time_ms': float(row['min_processing_time']) if row['min_processing_time'] else None,
                    'error_count': row['error_count'],
                    'warning_count': row['warning_count'],
                    'success_rate': (row['execution_count'] - row['error_count']) / row['execution_count'] if row['execution_count'] > 0 else 0
                }
                tool_performance.append(performance)

            # Calculate overall metrics
            total_executions = len(tool_executions)
            total_errors = sum(1 for ex in tool_executions if ex['severity'] == 'error')
            total_warnings = sum(1 for ex in tool_executions if ex['severity'] == 'warning')

            processing_times = [ex['processing_time_ms'] for ex in tool_executions if ex['processing_time_ms']]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None

            return {
                'loan_id': loan_id,
                'total_tool_executions': total_executions,
                'unique_tools_used': len(set(ex['tool_name'] for ex in tool_executions if ex['tool_name'])),
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'success_rate': (total_executions - total_errors) / total_executions if total_executions > 0 else 1,
                'average_processing_time_ms': avg_processing_time,
                'tool_performance': tool_performance,
                'tool_executions': tool_executions
            }

    async def get_raw_events(self, session_id: str, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """
        Get raw audit events for a session

        Args:
            session_id: Session identifier
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            Raw audit events with pagination
        """
        async with self.connection_pool.acquire() as conn:
            # Get events with pagination
            events_query = """
                SELECT
                    at.id,
                    at.event_type,
                    at.severity,
                    at.timestamp,
                    at.event_data,
                    at.service_name,
                    at.service_version,
                    at.environment,
                    at.classification,
                    at.correlation_id,
                    at.trace_id,
                    at.span_id,
                    at.parent_event_id
                FROM audit_trails at
                WHERE at.session_id = $1
                ORDER BY at.timestamp DESC
                LIMIT $2 OFFSET $3
            """

            # Get total count
            count_query = """
                SELECT COUNT(*) as total
                FROM audit_trails at
                WHERE at.session_id = $1
            """

            events_result, count_result = await asyncio.gather(
                conn.fetch(events_query, session_id, limit, offset),
                conn.fetchrow(count_query, session_id)
            )

            events = []
            for row in events_result:
                event = {
                    'id': str(row['id']),
                    'event_type': row['event_type'],
                    'severity': row['severity'],
                    'timestamp': row['timestamp'].isoformat(),
                    'event_data': dict(row['event_data']),
                    'service_name': row['service_name'],
                    'service_version': row['service_version'],
                    'environment': row['environment'],
                    'classification': row['classification'],
                    'correlation_id': row['correlation_id'],
                    'trace_id': row['trace_id'],
                    'span_id': row['span_id'],
                    'parent_event_id': str(row['parent_event_id']) if row['parent_event_id'] else None
                }
                events.append(event)

            total_events = count_result['total']

            return {
                'session_id': session_id,
                'total_events': total_events,
                'returned_events': len(events),
                'limit': limit,
                'offset': offset,
                'has_more': offset + len(events) < total_events,
                'events': events
            }

    async def get_visual_timeline_data(self, loan_id: str) -> Dict[str, Any]:
        """
        Get timeline data optimized for visualization

        Returns:
            Timeline data with aggregated events suitable for charts/graphs
        """
        async with self.connection_pool.acquire() as conn:
            # Get event distribution by type and time
            timeline_query = """
                SELECT
                    DATE_TRUNC('minute', at.timestamp) as time_bucket,
                    at.event_type,
                    at.severity,
                    COUNT(*) as event_count,
                    AVG(CAST(at.event_data->>'processing_time_ms' AS FLOAT)) as avg_processing_time
                FROM audit_trails at
                WHERE at.event_data->>'loan_id' = $1
                GROUP BY time_bucket, at.event_type, at.severity
                ORDER BY time_bucket ASC
            """

            # Get key milestones
            milestones_query = """
                SELECT
                    at.timestamp,
                    at.event_type,
                    at.event_data->>'status' as status,
                    at.event_data->>'amount_micro_algos' as amount,
                    at.service_name
                FROM audit_trails at
                WHERE at.event_data->>'loan_id' = $1
                  AND at.event_type IN (
                    'loan_request_created', 'loan_approved', 'loan_rejected',
                    'loan_funded', 'loan_repaid', 'loan_defaulted'
                  )
                ORDER BY at.timestamp ASC
            """

            timeline_result, milestones_result = await asyncio.gather(
                conn.fetch(timeline_query, loan_id),
                conn.fetch(milestones_query, loan_id)
            )

            # Process timeline data
            timeline_data = []
            for row in timeline_result:
                data_point = {
                    'time': row['time_bucket'].isoformat(),
                    'event_type': row['event_type'],
                    'severity': row['severity'],
                    'event_count': row['event_count'],
                    'avg_processing_time_ms': float(row['avg_processing_time']) if row['avg_processing_time'] else None
                }
                timeline_data.append(data_point)

            # Process milestones
            milestones = []
            for row in milestones_result:
                milestone = {
                    'timestamp': row['timestamp'].isoformat(),
                    'event_type': row['event_type'],
                    'status': row['status'],
                    'amount_micro_algos': int(row['amount']) if row['amount'] else None,
                    'service_name': row['service_name']
                }
                milestones.append(milestone)

            # Calculate summary statistics
            total_time_buckets = len(set(point['time'] for point in timeline_data))
            event_types = list(set(point['event_type'] for point in timeline_data))
            severity_distribution = {}
            for point in timeline_data:
                severity = point['severity']
                severity_distribution[severity] = severity_distribution.get(severity, 0) + point['event_count']

            return {
                'loan_id': loan_id,
                'timeline_buckets': total_time_buckets,
                'event_types': event_types,
                'severity_distribution': severity_distribution,
                'milestones': milestones,
                'timeline_data': timeline_data,
                'visualization_ready': True
            }

    async def search_audit_events(
        self,
        query: str,
        loan_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search audit events using full-text search

        Args:
            query: Search query string
            loan_id: Optional loan ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum results to return

        Returns:
            Search results with relevance ranking
        """
        async with self.connection_pool.acquire() as conn:
            conditions = ["at.search_vector @@ plainto_tsquery('english', $1)"]
            params = [query]
            param_count = 1

            if loan_id:
                param_count += 1
                conditions.append(f"at.event_data->>'loan_id' = ${param_count}")
                params.append(loan_id)

            if start_date:
                param_count += 1
                conditions.append(f"at.timestamp >= ${param_count}")
                params.append(start_date)

            if end_date:
                param_count += 1
                conditions.append(f"at.timestamp <= ${param_count}")
                params.append(end_date)

            search_query = f"""
                SELECT
                    at.id,
                    at.event_type,
                    at.severity,
                    at.timestamp,
                    at.event_data,
                    at.service_name,
                    at.session_id,
                    ts_rank(at.search_vector, plainto_tsquery('english', $1)) as relevance
                FROM audit_trails at
                WHERE {' AND '.join(conditions)}
                ORDER BY relevance DESC, at.timestamp DESC
                LIMIT ${param_count + 1}
            """

            params.append(limit)
            result = await conn.fetch(search_query, *params)

            events = []
            for row in result:
                event = {
                    'id': str(row['id']),
                    'event_type': row['event_type'],
                    'severity': row['severity'],
                    'timestamp': row['timestamp'].isoformat(),
                    'event_data': dict(row['event_data']),
                    'service_name': row['service_name'],
                    'session_id': row['session_id'],
                    'relevance_score': float(row['relevance'])
                }
                events.append(event)

            return {
                'query': query,
                'total_results': len(events),
                'filters': {
                    'loan_id': loan_id,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                },
                'events': events
            }