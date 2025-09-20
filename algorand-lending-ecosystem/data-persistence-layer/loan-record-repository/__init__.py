"""
Loan Record Repository Module

Provides clean data access patterns for loan records with proper separation
of concerns and testable interfaces.
"""

from .loan_repository import LoanRecordRepository
from .loan_models import LoanRecord, LoanStatistics, LoanStatus
from .connection_factory import ConnectionFactory

__all__ = ['LoanRecordRepository', 'LoanRecord', 'LoanStatistics', 'LoanStatus', 'ConnectionFactory']