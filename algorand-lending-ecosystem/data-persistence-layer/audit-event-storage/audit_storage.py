"""
Audit Event Storage

Repository for audit trail persistence and retrieval with comprehensive
event management and analysis capabilities.
"""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .audit_models import AuditEvent, EventType, AuditTrailSummary
try:
    from .connection_factory import ConnectionFactory, DatabaseConfig, DatabaseConnectionError
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / "database-schema-manager"))
    from connection_factory import ConnectionFactory, DatabaseConfig, DatabaseConnectionError


class AuditStorageError(Exception):
    """Raised when audit storage operations fail"""
    pass


class AuditEventStorage:
    """Manages audit trail persistence and retrieval"""

    def __init__(self, db_path: Path, config: Optional[DatabaseConfig] = None):
        self.db_path = Path(db_path)
        self.connection_factory = ConnectionFactory(db_path, config)

    def log_event(self, loan_id: str, event_type: EventType, event_data: Dict[str, Any]) -> str:
        """Store audit event, return event_id"""
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            event_id=event_id,
            loan_id=loan_id,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.now()
        )

        try:
            self.connection_factory.execute_query("""
                INSERT INTO audit_trail (event_id, loan_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.loan_id,
                event.event_type.value if isinstance(event.event_type, EventType) else event.event_type,
                event.event_data if isinstance(event.event_data, str) else str(event.event_data),
                event.timestamp.isoformat() if event.timestamp else None
            ))
            return event_id
        except Exception as e:
            raise AuditStorageError(f"Failed to log audit event: {e}")

    def get_loan_audit_trail(self, loan_id: str) -> List[AuditEvent]:
        """Retrieve complete audit trail for loan"""
        try:
            results = self.connection_factory.fetch_all(
                "SELECT * FROM audit_trail WHERE loan_id = ? ORDER BY timestamp",
                (loan_id,)
            )
            return [AuditEvent.from_dict(row) for row in results]
        except Exception as e:
            raise AuditStorageError(f"Failed to retrieve audit trail for loan {loan_id}: {e}")

    def get_events_by_type(self, event_type: EventType, limit: Optional[int] = None) -> List[AuditEvent]:
        """Get all events of specific type"""
        try:
            query = "SELECT * FROM audit_trail WHERE event_type = ? ORDER BY timestamp DESC"
            params = [event_type.value if isinstance(event_type, EventType) else event_type]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            results = self.connection_factory.fetch_all(query, tuple(params))
            return [AuditEvent.from_dict(row) for row in results]
        except Exception as e:
            raise AuditStorageError(f"Failed to retrieve events by type: {e}")

    def get_recent_events(self, hours: int = 24, limit: Optional[int] = None) -> List[AuditEvent]:
        """Get recent audit events"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            query = "SELECT * FROM audit_trail WHERE timestamp >= ? ORDER BY timestamp DESC"
            params = [cutoff_time.isoformat()]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            results = self.connection_factory.fetch_all(query, tuple(params))
            return [AuditEvent.from_dict(row) for row in results]
        except Exception as e:
            raise AuditStorageError(f"Failed to retrieve recent events: {e}")

    def get_audit_trail_summary(self, loan_id: str) -> AuditTrailSummary:
        """Get summary of audit trail for a loan"""
        try:
            events = self.get_loan_audit_trail(loan_id)
            return AuditTrailSummary.from_events(loan_id, events)
        except Exception as e:
            raise AuditStorageError(f"Failed to generate audit trail summary: {e}")

    def search_events(self, filters: Dict[str, Any]) -> List[AuditEvent]:
        """Search audit events with flexible filters"""
        conditions = []
        params = []

        # Build WHERE clause dynamically
        if 'loan_id' in filters:
            conditions.append("loan_id = ?")
            params.append(filters['loan_id'])

        if 'event_type' in filters:
            event_type = filters['event_type']
            conditions.append("event_type = ?")
            params.append(event_type.value if isinstance(event_type, EventType) else event_type)

        if 'start_date' in filters:
            conditions.append("timestamp >= ?")
            start_date = filters['start_date']
            params.append(start_date.isoformat() if isinstance(start_date, datetime) else start_date)

        if 'end_date' in filters:
            conditions.append("timestamp <= ?")
            end_date = filters['end_date']
            params.append(end_date.isoformat() if isinstance(end_date, datetime) else end_date)

        if 'event_data_contains' in filters:
            conditions.append("event_data LIKE ?")
            params.append(f"%{filters['event_data_contains']}%")

        # Build final query
        base_query = "SELECT * FROM audit_trail"
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY timestamp DESC"

        # Add limit if specified
        if 'limit' in filters:
            base_query += " LIMIT ?"
            params.append(filters['limit'])

        try:
            results = self.connection_factory.fetch_all(base_query, tuple(params))
            return [AuditEvent.from_dict(row) for row in results]
        except Exception as e:
            raise AuditStorageError(f"Failed to search events: {e}")

    def get_event_statistics(self) -> Dict[str, Any]:
        """Get audit event statistics"""
        try:
            stats = {}

            # Total events
            result = self.connection_factory.fetch_one("SELECT COUNT(*) as count FROM audit_trail")
            stats['total_events'] = result['count'] if result else 0

            # Events by type
            results = self.connection_factory.fetch_all("""
                SELECT event_type, COUNT(*) as count
                FROM audit_trail
                GROUP BY event_type
                ORDER BY count DESC
            """)
            stats['events_by_type'] = {row['event_type']: row['count'] for row in results}

            # Recent activity (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            result = self.connection_factory.fetch_one("""
                SELECT COUNT(*) as count FROM audit_trail WHERE timestamp >= ?
            """, (cutoff_time.isoformat(),))
            stats['events_last_24h'] = result['count'] if result else 0

            # Events per loan
            result = self.connection_factory.fetch_one("""
                SELECT AVG(event_count) as avg_events
                FROM (
                    SELECT loan_id, COUNT(*) as event_count
                    FROM audit_trail
                    GROUP BY loan_id
                ) as loan_stats
            """)
            stats['avg_events_per_loan'] = round(result['avg_events'], 2) if result and result['avg_events'] else 0

            # Most active loans
            results = self.connection_factory.fetch_all("""
                SELECT loan_id, COUNT(*) as event_count
                FROM audit_trail
                GROUP BY loan_id
                ORDER BY event_count DESC
                LIMIT 10
            """)
            stats['most_active_loans'] = [
                {'loan_id': row['loan_id'], 'event_count': row['event_count']}
                for row in results
            ]

            return stats
        except Exception as e:
            raise AuditStorageError(f"Failed to calculate event statistics: {e}")

    def cleanup_old_events(self, days_to_keep: int = 365) -> int:
        """Clean up old audit events (use with caution)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            rows_affected = self.connection_factory.execute_query(
                "DELETE FROM audit_trail WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            ).rowcount
            return rows_affected
        except Exception as e:
            raise AuditStorageError(f"Failed to cleanup old events: {e}")

    def export_audit_trail(self, loan_id: str, format: str = 'json') -> str:
        """Export audit trail for a loan in specified format"""
        try:
            events = self.get_loan_audit_trail(loan_id)

            if format.lower() == 'json':
                import json
                event_dicts = [event.to_dict() for event in events]
                return json.dumps(event_dicts, indent=2)

            elif format.lower() == 'csv':
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)

                # Header
                writer.writerow(['event_id', 'loan_id', 'event_type', 'event_data', 'timestamp'])

                # Data
                for event in events:
                    writer.writerow([
                        event.event_id,
                        event.loan_id,
                        event.event_type.value if isinstance(event.event_type, EventType) else event.event_type,
                        str(event.event_data),
                        event.timestamp.isoformat() if event.timestamp else ''
                    ])

                return output.getvalue()

            else:
                raise AuditStorageError(f"Unsupported export format: {format}")

        except Exception as e:
            raise AuditStorageError(f"Failed to export audit trail: {e}")

    def validate_audit_integrity(self, loan_id: str) -> Dict[str, bool]:
        """Validate audit trail integrity for a loan"""
        try:
            events = self.get_loan_audit_trail(loan_id)
            validation_results = {}

            # Check if events exist
            validation_results['events_exist'] = len(events) > 0

            # Check timestamp ordering
            timestamps = [e.timestamp for e in events if e.timestamp]
            validation_results['timestamps_ordered'] = timestamps == sorted(timestamps)

            # Check for required event types
            event_types = set(e.event_type for e in events)
            required_types = {EventType.APPLICATION_RECEIVED, EventType.DECISION_MADE}
            validation_results['required_events_present'] = required_types.issubset(event_types)

            # Check event data integrity
            validation_results['all_events_have_data'] = all(
                isinstance(e.event_data, dict) and e.event_data for e in events
            )

            # Overall validity
            validation_results['all_valid'] = all(validation_results.values())

            return validation_results
        except Exception as e:
            raise AuditStorageError(f"Failed to validate audit integrity: {e}")