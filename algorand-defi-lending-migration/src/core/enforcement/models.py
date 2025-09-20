"""
Data Models for Escrow Contract Management
Defines the data structures for collateral enforcement
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from ..lending.models import LoanStatus, CollateralType

class EscrowStatus(Enum):
    """Escrow contract lifecycle status"""
    PENDING = "pending"              # Contract created but not deployed
    DEPLOYED = "deployed"            # Contract deployed on blockchain
    FUNDED = "funded"                # Collateral deposited
    ACTIVE = "active"                # Loan disbursed, escrow active
    REPAID = "repaid"                # Loan repaid, awaiting release
    RELEASED = "released"            # Collateral released to borrower
    LIQUIDATED = "liquidated"        # Collateral liquidated to lender
    EXPIRED = "expired"              # Contract expired without resolution
    FAILED = "failed"                # Deployment or execution failed

class TriggerStatus(Enum):
    """Status of liquidation triggers"""
    MONITORING = "monitoring"        # Actively monitoring
    WARNING = "warning"              # Warning threshold reached
    TRIGGERED = "triggered"          # Liquidation condition met
    EXECUTED = "executed"            # Liquidation executed
    CLEARED = "cleared"              # Condition cleared/resolved

@dataclass
class EscrowParty:
    """Party involved in escrow"""
    address: str
    role: str  # 'borrower', 'lender', 'platform', 'arbitrator'
    signature_required: bool = False
    has_signed: bool = False
    signed_at: Optional[datetime] = None

@dataclass
class LiquidationTrigger:
    """Liquidation trigger configuration and status"""
    trigger_id: str
    trigger_type: str  # 'time_based', 'price_based', 'payment_default'
    condition: Dict[str, Any]
    status: TriggerStatus = TriggerStatus.MONITORING
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    triggered_at: Optional[datetime] = None
    evidence: Optional[Dict[str, Any]] = None

@dataclass
class EscrowContract:
    """
    Main escrow contract data model
    Represents the complete state of an escrow contract
    """
    escrow_id: str
    escrow_address: str
    app_id: int
    loan_id: str

    # Parties
    borrower: str
    lender: str
    platform: str
    parties: List[EscrowParty] = field(default_factory=list)

    # Financial terms
    loan_amount: int                 # in microAlgos
    collateral_amount: int           # in microAlgos
    collateral_type: CollateralType
    interest_rate: float             # percentage
    duration_days: int

    # Dates
    created_at: datetime
    deployed_at: Optional[datetime] = None
    funded_at: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Status
    status: EscrowStatus = EscrowStatus.PENDING
    loan_status: Optional[LoanStatus] = None

    # Liquidation
    liquidation_triggers: List[LiquidationTrigger] = field(default_factory=list)
    liquidation_price: Optional[int] = None
    liquidation_transaction_id: Optional[str] = None

    # Blockchain data
    deployment_transaction_id: Optional[str] = None
    funding_transaction_id: Optional[str] = None
    release_transaction_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    audit_log: List[Dict[str, Any]] = field(default_factory=list)

    def add_audit_entry(self, action: str, details: Dict[str, Any], actor: str):
        """Add an entry to the audit log"""
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "details": details
        })

    def is_liquidatable(self) -> bool:
        """Check if any liquidation trigger is active"""
        return any(
            trigger.status == TriggerStatus.TRIGGERED
            for trigger in self.liquidation_triggers
        )

    def get_collateral_ratio(self) -> float:
        """Calculate current collateralization ratio"""
        if self.loan_amount == 0:
            return float('inf')
        return self.collateral_amount / self.loan_amount

@dataclass
class EscrowDeploymentRequest:
    """Request to deploy a new escrow contract"""
    loan_id: str
    borrower: str
    lender: str
    amount: int
    collateral: int
    duration: int
    interest_rate: float = 5.0
    collateral_type: str = "ALGO"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EscrowDeploymentResponse:
    """Response from escrow deployment"""
    success: bool
    escrow_id: Optional[str] = None
    escrow_address: Optional[str] = None
    app_id: Optional[int] = None
    transaction_id: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None

@dataclass
class EscrowStatusResponse:
    """Response for escrow status queries"""
    escrow_id: str
    status: str
    balance: int
    locked_until: Optional[str] = None
    liquidation_price: Optional[int] = None
    parties: Dict[str, str]
    triggers: List[Dict[str, Any]]
    can_liquidate: bool = False
    can_release: bool = False

@dataclass
class LiquidationRequest:
    """Request to liquidate an escrow"""
    escrow_id: str
    reason: str
    evidence: Dict[str, Any]
    requestor: str
    force: bool = False

@dataclass
class LiquidationResponse:
    """Response from liquidation request"""
    success: bool
    transaction_id: Optional[str] = None
    distribution: Dict[str, int] = field(default_factory=dict)
    status: str = "pending"
    error_message: Optional[str] = None

@dataclass
class ReleaseRequest:
    """Request to release escrow collateral"""
    escrow_id: str
    authorization: Dict[str, Any]
    proof_of_payment: Optional[str] = None
    requestor: str

@dataclass
class ReleaseResponse:
    """Response from release request"""
    success: bool
    transaction_id: Optional[str] = None
    released_amount: int = 0
    recipient: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None

@dataclass
class EscrowMonitoringConfig:
    """Configuration for escrow monitoring system"""
    check_interval_seconds: int = 60
    liquidation_warning_hours: int = 24
    price_check_frequency: int = 300  # 5 minutes
    max_retries: int = 3
    enable_auto_liquidation: bool = False
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class EscrowEvent:
    """Event emitted by escrow system"""
    event_id: str
    escrow_id: str
    event_type: str  # 'deployed', 'funded', 'liquidated', 'released', etc.
    timestamp: datetime
    data: Dict[str, Any]
    transaction_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "escrow_id": self.escrow_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "transaction_id": self.transaction_id
        }