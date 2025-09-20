"""
Essential data models for vendorable lending logic.
Ultra-minimal, zero dependencies except Python stdlib.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal


class LoanStatus(Enum):
    """Loan application status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    DEFAULTED = "defaulted"
    PAID_OFF = "paid_off"


class CollateralType(Enum):
    """Supported collateral types"""
    ALGO = "ALGO"
    USDC = "USDC"
    USDT = "USDT"
    OTHER = "OTHER"


@dataclass
class Borrower:
    """Borrower information"""
    address: str
    credit_score: Optional[int] = None
    loan_history: List[str] = None

    def __post_init__(self):
        if self.loan_history is None:
            self.loan_history = []


@dataclass
class Collateral:
    """Collateral information"""
    asset_type: CollateralType
    amount: Decimal
    current_price: Decimal

    @property
    def value_usd(self) -> Decimal:
        """Current USD value of collateral"""
        return self.amount * self.current_price


@dataclass
class LoanTerms:
    """Loan terms and conditions"""
    principal: Decimal
    interest_rate: Decimal  # Annual percentage rate
    duration_days: int
    ltv_ratio: Decimal  # Loan-to-value ratio


@dataclass
class LoanRequest:
    """Complete loan application"""
    borrower: Borrower
    requested_amount: Decimal
    collateral: Collateral
    duration_days: int

    @property
    def requested_ltv(self) -> Decimal:
        """Calculate requested loan-to-value ratio"""
        if self.collateral.value_usd == 0:
            return Decimal('0')
        return self.requested_amount / self.collateral.value_usd


@dataclass
class RiskAssessment:
    """Risk assessment results"""
    score: int  # 0-100, higher is better
    factors: Dict[str, Any]
    recommendation: str


@dataclass
class LoanDecision:
    """Final loan decision"""
    approved: bool
    terms: Optional[LoanTerms]
    risk_assessment: RiskAssessment
    reason: str


@dataclass
class LoanContract:
    """Active loan contract"""
    loan_id: str
    borrower: Borrower
    terms: LoanTerms
    collateral: Collateral
    status: LoanStatus
    created_at: str

    @property
    def current_ltv(self) -> Decimal:
        """Current loan-to-value ratio"""
        if self.collateral.value_usd == 0:
            return Decimal('0')
        return self.terms.principal / self.collateral.value_usd