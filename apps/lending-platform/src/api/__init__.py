"""
Algorand A2A Lending API Package
Shared API components for lending platform
"""

from .api_factory import LendingAPIFactory
# from .auth import AuthHandler  # Requires jwt dependency
from .storage import LoanStorage, DatabaseLoanStorage

__version__ = "1.0.0"
__author__ = "Lending Platform Team"

__all__ = [
    # API Factory
    "LendingAPIFactory",
    # Storage
    "LoanStorage",
    "DatabaseLoanStorage"
]