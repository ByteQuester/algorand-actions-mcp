"""
Loan Record Repository

Repository pattern implementation for loan data access with clean interfaces
and comprehensive error handling.
"""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .loan_models import LoanRecord, LoanStatistics, LoanStatus
try:
    from .connection_factory import ConnectionFactory, DatabaseConfig, DatabaseConnectionError
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / "database-schema-manager"))
    from connection_factory import ConnectionFactory, DatabaseConfig, DatabaseConnectionError


class LoanRepositoryError(Exception):
    """Raised when loan repository operations fail"""
    pass


class LoanRecordRepository:
    """Repository for loan data access operations"""

    def __init__(self, db_path: Path, config: Optional[DatabaseConfig] = None):
        self.db_path = Path(db_path)
        self.connection_factory = ConnectionFactory(db_path, config)

    def create_loan(self, loan: LoanRecord) -> str:
        """Create new loan record, return loan_id"""
        if not loan.loan_id:
            loan.loan_id = f"LOAN-{uuid.uuid4().hex[:8].upper()}"

        # Set timestamps if not provided
        now = datetime.now()
        if not loan.created_at:
            loan.created_at = now
        if not loan.updated_at:
            loan.updated_at = now

        try:
            self.connection_factory.execute_query("""
                INSERT INTO loans (
                    loan_id, borrower_name, borrower_address, amount, duration_days,
                    purpose, risk_score, interest_rate, collateral_required,
                    status, decision_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loan.loan_id,
                loan.borrower_name,
                loan.borrower_address,
                loan.amount,
                loan.duration_days,
                loan.purpose,
                loan.risk_score,
                loan.interest_rate,
                loan.collateral_required,
                loan.status.value if isinstance(loan.status, LoanStatus) else loan.status,
                loan.decision_reason,
                loan.created_at.isoformat() if loan.created_at else None,
                loan.updated_at.isoformat() if loan.updated_at else None
            ))
            return loan.loan_id
        except Exception as e:
            raise LoanRepositoryError(f"Failed to create loan: {e}")

    def get_loan_by_id(self, loan_id: str) -> Optional[LoanRecord]:
        """Retrieve loan by ID"""
        try:
            result = self.connection_factory.fetch_one(
                "SELECT * FROM loans WHERE loan_id = ?",
                (loan_id,)
            )
            return LoanRecord.from_dict(result) if result else None
        except Exception as e:
            raise LoanRepositoryError(f"Failed to retrieve loan {loan_id}: {e}")

    def update_loan_status(self, loan_id: str, status: LoanStatus, reason: str) -> None:
        """Update loan status and decision reason"""
        try:
            updated_at = datetime.now().isoformat()
            rows_affected = self.connection_factory.execute_query("""
                UPDATE loans
                SET status = ?, decision_reason = ?, updated_at = ?
                WHERE loan_id = ?
            """, (status.value if isinstance(status, LoanStatus) else status, reason, updated_at, loan_id)).rowcount

            if rows_affected == 0:
                raise LoanRepositoryError(f"Loan {loan_id} not found")
        except LoanRepositoryError:
            raise
        except Exception as e:
            raise LoanRepositoryError(f"Failed to update loan status: {e}")

    def update_loan_terms(self, loan_id: str, **updates) -> None:
        """Update loan terms (amount, interest_rate, collateral_required, etc.)"""
        allowed_fields = {
            'amount', 'duration_days', 'purpose', 'risk_score',
            'interest_rate', 'collateral_required'
        }

        # Filter to only allowed fields
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return

        # Build dynamic update query
        set_clauses = []
        params = []
        for field, value in update_fields.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)

        # Add updated_at
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(loan_id)

        query = f"UPDATE loans SET {', '.join(set_clauses)} WHERE loan_id = ?"

        try:
            rows_affected = self.connection_factory.execute_query(query, tuple(params)).rowcount
            if rows_affected == 0:
                raise LoanRepositoryError(f"Loan {loan_id} not found")
        except LoanRepositoryError:
            raise
        except Exception as e:
            raise LoanRepositoryError(f"Failed to update loan terms: {e}")

    def get_all_loans(self) -> List[LoanRecord]:
        """Retrieve all loans"""
        try:
            results = self.connection_factory.fetch_all(
                "SELECT * FROM loans ORDER BY created_at DESC"
            )
            return [LoanRecord.from_dict(row) for row in results]
        except Exception as e:
            raise LoanRepositoryError(f"Failed to retrieve loans: {e}")

    def get_loans_by_status(self, status: LoanStatus) -> List[LoanRecord]:
        """Retrieve loans by status"""
        try:
            status_value = status.value if isinstance(status, LoanStatus) else status
            results = self.connection_factory.fetch_all(
                "SELECT * FROM loans WHERE status = ? ORDER BY created_at DESC",
                (status_value,)
            )
            return [LoanRecord.from_dict(row) for row in results]
        except Exception as e:
            raise LoanRepositoryError(f"Failed to retrieve loans by status: {e}")

    def get_loans_by_borrower(self, borrower_address: str) -> List[LoanRecord]:
        """Retrieve loans by borrower address"""
        try:
            results = self.connection_factory.fetch_all(
                "SELECT * FROM loans WHERE borrower_address = ? ORDER BY created_at DESC",
                (borrower_address,)
            )
            return [LoanRecord.from_dict(row) for row in results]
        except Exception as e:
            raise LoanRepositoryError(f"Failed to retrieve loans for borrower: {e}")

    def get_loan_statistics(self) -> LoanStatistics:
        """Generate platform statistics"""
        try:
            all_loans = self.get_all_loans()
            return LoanStatistics.calculate_from_loans(all_loans)
        except Exception as e:
            raise LoanRepositoryError(f"Failed to calculate statistics: {e}")

    def search_loans(self, filters: Dict[str, Any]) -> List[LoanRecord]:
        """Search loans with flexible filters"""
        conditions = []
        params = []

        # Build WHERE clause dynamically
        if 'status' in filters:
            conditions.append("status = ?")
            status = filters['status']
            params.append(status.value if isinstance(status, LoanStatus) else status)

        if 'min_amount' in filters:
            conditions.append("amount >= ?")
            params.append(filters['min_amount'])

        if 'max_amount' in filters:
            conditions.append("amount <= ?")
            params.append(filters['max_amount'])

        if 'min_risk_score' in filters:
            conditions.append("risk_score >= ?")
            params.append(filters['min_risk_score'])

        if 'max_risk_score' in filters:
            conditions.append("risk_score <= ?")
            params.append(filters['max_risk_score'])

        if 'borrower_name' in filters:
            conditions.append("borrower_name LIKE ?")
            params.append(f"%{filters['borrower_name']}%")

        if 'purpose' in filters:
            conditions.append("purpose LIKE ?")
            params.append(f"%{filters['purpose']}%")

        # Build final query
        base_query = "SELECT * FROM loans"
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY created_at DESC"

        try:
            results = self.connection_factory.fetch_all(base_query, tuple(params))
            return [LoanRecord.from_dict(row) for row in results]
        except Exception as e:
            raise LoanRepositoryError(f"Failed to search loans: {e}")

    def delete_loan(self, loan_id: str) -> bool:
        """Delete a loan record (use with caution)"""
        try:
            rows_affected = self.connection_factory.execute_query(
                "DELETE FROM loans WHERE loan_id = ?",
                (loan_id,)
            ).rowcount
            return rows_affected > 0
        except Exception as e:
            raise LoanRepositoryError(f"Failed to delete loan: {e}")

    def get_loans_count(self) -> int:
        """Get total number of loans"""
        try:
            result = self.connection_factory.fetch_one("SELECT COUNT(*) as count FROM loans")
            return result['count'] if result else 0
        except Exception as e:
            raise LoanRepositoryError(f"Failed to count loans: {e}")

    def validate_loan_data_integrity(self, loan: LoanRecord) -> Dict[str, bool]:
        """Validate loan data meets business constraints"""
        validation_results = {}

        # Amount validation
        validation_results['amount_positive'] = loan.amount > 0

        # Duration validation
        validation_results['duration_positive'] = loan.duration_days > 0

        # Risk score validation
        if loan.risk_score is not None:
            validation_results['risk_score_valid'] = 0 <= loan.risk_score <= 100
        else:
            validation_results['risk_score_valid'] = True

        # Interest rate validation
        if loan.interest_rate is not None:
            validation_results['interest_rate_valid'] = loan.interest_rate >= 0
        else:
            validation_results['interest_rate_valid'] = True

        # Collateral validation
        if loan.collateral_required is not None:
            validation_results['collateral_valid'] = loan.collateral_required >= 0
        else:
            validation_results['collateral_valid'] = True

        # Status validation
        validation_results['status_valid'] = isinstance(loan.status, LoanStatus)

        # Overall validity
        validation_results['all_valid'] = all(validation_results.values())

        return validation_results