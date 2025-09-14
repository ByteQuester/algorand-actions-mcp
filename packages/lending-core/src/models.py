"""
Pure data models for A2A lending
NO configuration, NO environment dependencies
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class LoanStatus(Enum):
    """Loan status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"

class CollateralType(Enum):
    """Supported collateral types"""
    ALGO = "ALGO"
    USDC = "USDC"
    ASA = "ASA"

@dataclass
class LoanRequest:
    """Pure loan request model"""
    borrower_address: str
    lender_address: Optional[str]
    amount_micro_algos: int
    duration_days: int
    max_interest_rate: float
    collateral_type: CollateralType
    collateral_amount: Optional[int] = None

    @property
    def amount_algos(self) -> float:
        """Convert microAlgos to Algos"""
        return self.amount_micro_algos / 1_000_000

    def validate(self) -> List[str]:
        """Validate loan request - pure business logic"""
        errors = []

        if self.amount_micro_algos <= 0:
            errors.append("Loan amount must be positive")

        if self.duration_days <= 0 or self.duration_days > 365:
            errors.append("Duration must be between 1-365 days")

        if self.max_interest_rate < 0 or self.max_interest_rate > 100:
            errors.append("Interest rate must be between 0-100%")

        if not self._is_valid_algorand_address(self.borrower_address):
            errors.append("Invalid borrower address")

        if self.lender_address and not self._is_valid_algorand_address(self.lender_address):
            errors.append("Invalid lender address")

        return errors

    def _is_valid_algorand_address(self, address: str) -> bool:
        """Basic Algorand address validation"""
        return (
            isinstance(address, str) and
            len(address) == 58 and
            address.isalnum()
        )

@dataclass
class LoanTerms:
    """Negotiated loan terms"""
    amount: int
    interest_rate: float
    duration_days: int
    collateral_amount: int
    collateral_type: CollateralType
    lender: str
    borrower: str

@dataclass
class LoanResult:
    """Result of loan processing"""
    loan_id: str
    status: LoanStatus
    terms: Optional[LoanTerms]
    transaction_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    @property
    def is_successful(self) -> bool:
        """Check if loan processing was successful"""
        return self.status in [LoanStatus.APPROVED, LoanStatus.ACTIVE, LoanStatus.COMPLETED]

@dataclass
class AgentResult:
    """Result from individual agent processing"""
    agent_type: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None

@dataclass
class AccountBalance:
    """Account balance information"""
    address: str
    algo_balance_micro: int
    usdc_balance_micro: int
    asa_balances: Dict[str, int]

    @property
    def algo_balance(self) -> float:
        """ALGO balance in standard units"""
        return self.algo_balance_micro / 1_000_000

    @property
    def usdc_balance(self) -> float:
        """USDC balance in standard units"""
        return self.usdc_balance_micro / 1_000_000


@dataclass
class MCPServiceConfig:
    """Configuration for MCP services"""
    reader_endpoint: str = "http://localhost:8002"
    writer_endpoint: str = "http://localhost:3001"
    timeout_seconds: int = 30
    retry_count: int = 3