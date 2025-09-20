"""
Loan Data Models

Clean data models for loan records and related entities.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class LoanStatus(Enum):
    """Loan status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"


@dataclass
class LoanRecord:
    """Loan record data model"""
    loan_id: str
    borrower_name: str
    borrower_address: str
    amount: float
    duration_days: int
    purpose: Optional[str] = None
    risk_score: Optional[int] = None
    interest_rate: Optional[float] = None
    collateral_required: Optional[float] = None
    status: LoanStatus = LoanStatus.PENDING
    decision_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'loan_id': self.loan_id,
            'borrower_name': self.borrower_name,
            'borrower_address': self.borrower_address,
            'amount': self.amount,
            'duration_days': self.duration_days,
            'purpose': self.purpose,
            'risk_score': self.risk_score,
            'interest_rate': self.interest_rate,
            'collateral_required': self.collateral_required,
            'status': self.status.value if isinstance(self.status, LoanStatus) else self.status,
            'decision_reason': self.decision_reason,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoanRecord':
        """Create from dictionary (database row)"""
        # Handle datetime parsing
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                try:
                    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                except ValueError:
                    # Handle SQLite timestamp format
                    created_at = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            elif isinstance(data['created_at'], datetime):
                created_at = data['created_at']

        updated_at = None
        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                try:
                    updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                except ValueError:
                    updated_at = datetime.strptime(data['updated_at'], '%Y-%m-%d %H:%M:%S')
            elif isinstance(data['updated_at'], datetime):
                updated_at = data['updated_at']

        # Handle status enum
        status = LoanStatus(data['status']) if data.get('status') else LoanStatus.PENDING

        return cls(
            loan_id=data['loan_id'],
            borrower_name=data['borrower_name'],
            borrower_address=data['borrower_address'],
            amount=float(data['amount']),
            duration_days=int(data['duration_days']),
            purpose=data.get('purpose'),
            risk_score=int(data['risk_score']) if data.get('risk_score') is not None else None,
            interest_rate=float(data['interest_rate']) if data.get('interest_rate') is not None else None,
            collateral_required=float(data['collateral_required']) if data.get('collateral_required') is not None else None,
            status=status,
            decision_reason=data.get('decision_reason'),
            created_at=created_at,
            updated_at=updated_at
        )

    def is_approved(self) -> bool:
        """Check if loan is approved"""
        return self.status == LoanStatus.APPROVED

    def is_active(self) -> bool:
        """Check if loan is active"""
        return self.status == LoanStatus.ACTIVE

    def is_completed(self) -> bool:
        """Check if loan is completed"""
        return self.status in [LoanStatus.COMPLETED, LoanStatus.DEFAULTED]


@dataclass
class LoanStatistics:
    """Platform loan statistics"""
    total_loans: int
    approved_loans: int
    rejected_loans: int
    active_loans: int
    completed_loans: int
    total_amount_loaned: float
    average_loan_amount: float
    average_risk_score: Optional[float]
    average_interest_rate: Optional[float]
    approval_rate: float

    @classmethod
    def calculate_from_loans(cls, loans: list[LoanRecord]) -> 'LoanStatistics':
        """Calculate statistics from a list of loans"""
        if not loans:
            return cls(
                total_loans=0,
                approved_loans=0,
                rejected_loans=0,
                active_loans=0,
                completed_loans=0,
                total_amount_loaned=0.0,
                average_loan_amount=0.0,
                average_risk_score=None,
                average_interest_rate=None,
                approval_rate=0.0
            )

        total_loans = len(loans)
        approved_loans = sum(1 for loan in loans if loan.status == LoanStatus.APPROVED)
        rejected_loans = sum(1 for loan in loans if loan.status == LoanStatus.REJECTED)
        active_loans = sum(1 for loan in loans if loan.status == LoanStatus.ACTIVE)
        completed_loans = sum(1 for loan in loans if loan.is_completed())

        total_amount_loaned = sum(loan.amount for loan in loans)
        average_loan_amount = total_amount_loaned / total_loans

        risk_scores = [loan.risk_score for loan in loans if loan.risk_score is not None]
        average_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else None

        interest_rates = [loan.interest_rate for loan in loans if loan.interest_rate is not None]
        average_interest_rate = sum(interest_rates) / len(interest_rates) if interest_rates else None

        approval_rate = approved_loans / total_loans if total_loans > 0 else 0.0

        return cls(
            total_loans=total_loans,
            approved_loans=approved_loans,
            rejected_loans=rejected_loans,
            active_loans=active_loans,
            completed_loans=completed_loans,
            total_amount_loaned=total_amount_loaned,
            average_loan_amount=average_loan_amount,
            average_risk_score=average_risk_score,
            average_interest_rate=average_interest_rate,
            approval_rate=approval_rate
        )