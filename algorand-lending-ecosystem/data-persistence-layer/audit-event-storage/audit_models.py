"""
Audit Event Data Models

Clean data models for audit events and related entities.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class EventType(Enum):
    """Audit event types"""
    APPLICATION_RECEIVED = "APPLICATION_RECEIVED"
    RISK_ASSESSED = "RISK_ASSESSED"
    RATE_CALCULATED = "RATE_CALCULATED"
    COLLATERAL_CALCULATED = "COLLATERAL_CALCULATED"
    DECISION_MADE = "DECISION_MADE"
    LOAN_ACTIVATED = "LOAN_ACTIVATED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    LOAN_COMPLETED = "LOAN_COMPLETED"
    LOAN_DEFAULTED = "LOAN_DEFAULTED"
    STATUS_UPDATED = "STATUS_UPDATED"
    TERMS_MODIFIED = "TERMS_MODIFIED"
    SYSTEM_EVENT = "SYSTEM_EVENT"


@dataclass
class AuditEvent:
    """Audit event data model"""
    event_id: str
    loan_id: str
    event_type: EventType
    event_data: Dict[str, Any]
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'event_id': self.event_id,
            'loan_id': self.loan_id,
            'event_type': self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            'event_data': json.dumps(self.event_data) if isinstance(self.event_data, dict) else self.event_data,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create from dictionary (database row)"""
        # Handle timestamp parsing
        timestamp = None
        if data.get('timestamp'):
            if isinstance(data['timestamp'], str):
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    # Handle SQLite timestamp format
                    timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            elif isinstance(data['timestamp'], datetime):
                timestamp = data['timestamp']

        # Handle event type enum
        event_type = EventType(data['event_type']) if data.get('event_type') else EventType.SYSTEM_EVENT

        # Handle event data JSON
        event_data = {}
        if data.get('event_data'):
            if isinstance(data['event_data'], str):
                try:
                    event_data = json.loads(data['event_data'])
                except json.JSONDecodeError:
                    event_data = {'raw_data': data['event_data']}
            elif isinstance(data['event_data'], dict):
                event_data = data['event_data']

        return cls(
            event_id=data['event_id'],
            loan_id=data['loan_id'],
            event_type=event_type,
            event_data=event_data,
            timestamp=timestamp
        )

    def get_event_summary(self) -> str:
        """Get human-readable event summary"""
        summaries = {
            EventType.APPLICATION_RECEIVED: "Loan application received",
            EventType.RISK_ASSESSED: "Risk assessment completed",
            EventType.RATE_CALCULATED: "Interest rate calculated",
            EventType.COLLATERAL_CALCULATED: "Collateral requirement calculated",
            EventType.DECISION_MADE: "Loan decision made",
            EventType.LOAN_ACTIVATED: "Loan activated",
            EventType.PAYMENT_RECEIVED: "Payment received",
            EventType.LOAN_COMPLETED: "Loan completed",
            EventType.LOAN_DEFAULTED: "Loan defaulted",
            EventType.STATUS_UPDATED: "Loan status updated",
            EventType.TERMS_MODIFIED: "Loan terms modified",
            EventType.SYSTEM_EVENT: "System event"
        }
        return summaries.get(self.event_type, f"Unknown event: {self.event_type}")

    def extract_key_data(self) -> Dict[str, Any]:
        """Extract key data points from event data"""
        key_data = {}

        if self.event_type == EventType.RISK_ASSESSED:
            key_data['risk_score'] = self.event_data.get('final_risk_score')
            key_data['risk_level'] = self.event_data.get('risk_level')

        elif self.event_type == EventType.RATE_CALCULATED:
            key_data['interest_rate'] = self.event_data.get('interest_rate')

        elif self.event_type == EventType.COLLATERAL_CALCULATED:
            key_data['collateral_required'] = self.event_data.get('required')

        elif self.event_type == EventType.DECISION_MADE:
            key_data['status'] = self.event_data.get('status')
            key_data['reason'] = self.event_data.get('reason')

        elif self.event_type == EventType.APPLICATION_RECEIVED:
            key_data['amount'] = self.event_data.get('amount')
            key_data['borrower'] = self.event_data.get('borrower_name')

        return key_data


@dataclass
class AuditTrailSummary:
    """Summary of audit trail for a loan"""
    loan_id: str
    total_events: int
    first_event_time: Optional[datetime]
    last_event_time: Optional[datetime]
    event_types: List[EventType]
    key_events: Dict[EventType, AuditEvent]
    processing_duration: Optional[float]  # in seconds

    @classmethod
    def from_events(cls, loan_id: str, events: List[AuditEvent]) -> 'AuditTrailSummary':
        """Create summary from list of audit events"""
        if not events:
            return cls(
                loan_id=loan_id,
                total_events=0,
                first_event_time=None,
                last_event_time=None,
                event_types=[],
                key_events={},
                processing_duration=None
            )

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp or datetime.min)

        first_event_time = sorted_events[0].timestamp
        last_event_time = sorted_events[-1].timestamp

        # Calculate processing duration
        processing_duration = None
        if first_event_time and last_event_time:
            processing_duration = (last_event_time - first_event_time).total_seconds()

        # Extract event types
        event_types = list(set(event.event_type for event in events))

        # Identify key events (latest of each type)
        key_events = {}
        for event in reversed(sorted_events):
            if event.event_type not in key_events:
                key_events[event.event_type] = event

        return cls(
            loan_id=loan_id,
            total_events=len(events),
            first_event_time=first_event_time,
            last_event_time=last_event_time,
            event_types=event_types,
            key_events=key_events,
            processing_duration=processing_duration
        )