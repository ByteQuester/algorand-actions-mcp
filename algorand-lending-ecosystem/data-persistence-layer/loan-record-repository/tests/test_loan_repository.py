"""
Test Loan Record Repository

Comprehensive tests for loan repository functionality with in-memory database.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from ..loan_repository import LoanRecordRepository, LoanRepositoryError
from ..loan_models import LoanRecord, LoanStatus, LoanStatistics
from ..connection_factory import DatabaseConfig


class TestLoanRecordRepository:
    """Test loan record repository functionality"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository with test database"""
        # First create the schema
        from ...database_schema_manager import DatabaseSchemaManager
        schema_manager = DatabaseSchemaManager(temp_db_path)
        schema_manager.create_initial_schema()

        return LoanRecordRepository(temp_db_path)

    @pytest.fixture
    def sample_loan(self):
        """Create sample loan for testing"""
        return LoanRecord(
            loan_id="TEST-LOAN-001",
            borrower_name="John Doe",
            borrower_address="ABC123XYZ",
            amount=10000.0,
            duration_days=365,
            purpose="home improvement",
            risk_score=75,
            interest_rate=8.5,
            collateral_required=12000.0,
            status=LoanStatus.PENDING
        )

    def test_create_loan_success(self, repository, sample_loan):
        """Test successful loan creation"""
        loan_id = repository.create_loan(sample_loan)
        assert loan_id == sample_loan.loan_id

        # Verify loan was stored
        stored_loan = repository.get_loan_by_id(loan_id)
        assert stored_loan is not None
        assert stored_loan.borrower_name == sample_loan.borrower_name
        assert stored_loan.amount == sample_loan.amount

    def test_create_loan_auto_generates_id(self, repository):
        """Test loan creation with auto-generated ID"""
        loan = LoanRecord(
            loan_id="",  # Empty ID should be auto-generated
            borrower_name="Jane Smith",
            borrower_address="DEF456UVW",
            amount=5000.0,
            duration_days=180
        )

        loan_id = repository.create_loan(loan)
        assert loan_id.startswith("LOAN-")
        assert len(loan_id) == 13  # "LOAN-" + 8 hex characters

    def test_get_loan_by_id_existing(self, repository, sample_loan):
        """Test retrieval of existing loan"""
        repository.create_loan(sample_loan)

        retrieved_loan = repository.get_loan_by_id(sample_loan.loan_id)
        assert retrieved_loan is not None
        assert retrieved_loan.loan_id == sample_loan.loan_id
        assert retrieved_loan.borrower_name == sample_loan.borrower_name

    def test_get_loan_by_id_nonexistent(self, repository):
        """Test graceful handling of missing loans"""
        result = repository.get_loan_by_id("NONEXISTENT-LOAN")
        assert result is None

    def test_update_loan_status(self, repository, sample_loan):
        """Test loan status update"""
        repository.create_loan(sample_loan)

        repository.update_loan_status(
            sample_loan.loan_id,
            LoanStatus.APPROVED,
            "Risk assessment passed"
        )

        updated_loan = repository.get_loan_by_id(sample_loan.loan_id)
        assert updated_loan.status == LoanStatus.APPROVED
        assert updated_loan.decision_reason == "Risk assessment passed"

    def test_update_loan_terms(self, repository, sample_loan):
        """Test loan terms update"""
        repository.create_loan(sample_loan)

        repository.update_loan_terms(
            sample_loan.loan_id,
            amount=15000.0,
            interest_rate=7.5,
            risk_score=80
        )

        updated_loan = repository.get_loan_by_id(sample_loan.loan_id)
        assert updated_loan.amount == 15000.0
        assert updated_loan.interest_rate == 7.5
        assert updated_loan.risk_score == 80

    def test_get_loans_by_status(self, repository):
        """Test filtering loans by status"""
        # Create loans with different statuses
        loan1 = LoanRecord("LOAN-001", "Borrower 1", "ADDR1", 1000, 365, status=LoanStatus.PENDING)
        loan2 = LoanRecord("LOAN-002", "Borrower 2", "ADDR2", 2000, 365, status=LoanStatus.APPROVED)
        loan3 = LoanRecord("LOAN-003", "Borrower 3", "ADDR3", 3000, 365, status=LoanStatus.PENDING)

        repository.create_loan(loan1)
        repository.create_loan(loan2)
        repository.create_loan(loan3)

        pending_loans = repository.get_loans_by_status(LoanStatus.PENDING)
        approved_loans = repository.get_loans_by_status(LoanStatus.APPROVED)

        assert len(pending_loans) == 2
        assert len(approved_loans) == 1
        assert all(loan.status == LoanStatus.PENDING for loan in pending_loans)

    def test_get_loans_by_borrower(self, repository):
        """Test filtering loans by borrower"""
        # Create loans for same borrower
        loan1 = LoanRecord("LOAN-001", "Borrower 1", "ADDR1", 1000, 365)
        loan2 = LoanRecord("LOAN-002", "Borrower 2", "ADDR2", 2000, 365)
        loan3 = LoanRecord("LOAN-003", "Borrower 1", "ADDR1", 3000, 365)

        repository.create_loan(loan1)
        repository.create_loan(loan2)
        repository.create_loan(loan3)

        borrower1_loans = repository.get_loans_by_borrower("ADDR1")
        borrower2_loans = repository.get_loans_by_borrower("ADDR2")

        assert len(borrower1_loans) == 2
        assert len(borrower2_loans) == 1

    def test_search_loans(self, repository):
        """Test loan search functionality"""
        # Create diverse set of loans
        loans_data = [
            {"id": "LOAN-001", "amount": 5000, "risk_score": 85, "status": LoanStatus.APPROVED},
            {"id": "LOAN-002", "amount": 15000, "risk_score": 60, "status": LoanStatus.PENDING},
            {"id": "LOAN-003", "amount": 25000, "risk_score": 45, "status": LoanStatus.REJECTED},
        ]

        for data in loans_data:
            loan = LoanRecord(
                data["id"], f"Borrower {data['id'][-1]}", f"ADDR{data['id'][-1]}",
                data["amount"], 365, risk_score=data["risk_score"], status=data["status"]
            )
            repository.create_loan(loan)

        # Test various search filters
        high_amount_loans = repository.search_loans({"min_amount": 10000})
        assert len(high_amount_loans) == 2

        low_risk_loans = repository.search_loans({"min_risk_score": 70})
        assert len(low_risk_loans) == 1

        approved_loans = repository.search_loans({"status": LoanStatus.APPROVED})
        assert len(approved_loans) == 1

    def test_loan_statistics(self, repository):
        """Test loan statistics calculation"""
        # Create sample loans
        loans_data = [
            {"amount": 10000, "risk_score": 80, "interest_rate": 5.0, "status": LoanStatus.APPROVED},
            {"amount": 20000, "risk_score": 70, "interest_rate": 6.0, "status": LoanStatus.APPROVED},
            {"amount": 15000, "risk_score": 50, "interest_rate": 8.0, "status": LoanStatus.REJECTED},
        ]

        for i, data in enumerate(loans_data):
            loan = LoanRecord(
                f"LOAN-{i+1:03d}", f"Borrower {i+1}", f"ADDR{i+1}",
                data["amount"], 365, risk_score=data["risk_score"],
                interest_rate=data["interest_rate"], status=data["status"]
            )
            repository.create_loan(loan)

        stats = repository.get_loan_statistics()

        assert stats.total_loans == 3
        assert stats.approved_loans == 2
        assert stats.rejected_loans == 1
        assert stats.total_amount_loaned == 45000
        assert stats.average_loan_amount == 15000
        assert stats.approval_rate == 2/3

    def test_validate_loan_data_integrity(self, repository):
        """Test loan data validation"""
        # Valid loan
        valid_loan = LoanRecord("LOAN-001", "Borrower", "ADDR", 1000, 365, risk_score=75)
        validation = repository.validate_loan_data_integrity(valid_loan)
        assert validation['all_valid'] is True

        # Invalid loan (negative amount)
        invalid_loan = LoanRecord("LOAN-002", "Borrower", "ADDR", -1000, 365, risk_score=75)
        validation = repository.validate_loan_data_integrity(invalid_loan)
        assert validation['amount_positive'] is False
        assert validation['all_valid'] is False

    def test_delete_loan(self, repository, sample_loan):
        """Test loan deletion"""
        repository.create_loan(sample_loan)

        # Verify loan exists
        assert repository.get_loan_by_id(sample_loan.loan_id) is not None

        # Delete loan
        deleted = repository.delete_loan(sample_loan.loan_id)
        assert deleted is True

        # Verify loan is gone
        assert repository.get_loan_by_id(sample_loan.loan_id) is None

    def test_loans_count(self, repository):
        """Test loan counting"""
        assert repository.get_loans_count() == 0

        # Add some loans
        for i in range(3):
            loan = LoanRecord(f"LOAN-{i+1:03d}", f"Borrower {i+1}", f"ADDR{i+1}", 1000, 365)
            repository.create_loan(loan)

        assert repository.get_loans_count() == 3

    def test_error_handling(self, temp_db_path):
        """Test error handling for various scenarios"""
        # Test with non-existent database
        repo = LoanRecordRepository(temp_db_path / "nonexistent.db")

        # Should raise error when trying to use without schema
        with pytest.raises(LoanRepositoryError):
            repo.get_loan_by_id("test")

    def test_timestamp_handling(self, repository):
        """Test proper timestamp handling"""
        loan = LoanRecord("LOAN-001", "Borrower", "ADDR", 1000, 365)

        # Test creation with auto timestamps
        before_create = datetime.now()
        repository.create_loan(loan)
        after_create = datetime.now()

        retrieved = repository.get_loan_by_id("LOAN-001")
        assert retrieved.created_at is not None
        assert before_create <= retrieved.created_at <= after_create
        assert retrieved.updated_at is not None


if __name__ == "__main__":
    pytest.main([__file__])