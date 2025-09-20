"""
Smart Contract Templates for Escrow Collateral Management
Implements TEAL/PyTeal contracts for programmatic enforcement
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import base64

class EscrowStatus(Enum):
    """Escrow contract status"""
    CREATED = "created"
    FUNDED = "funded"
    ACTIVE = "active"
    COMPLETED = "completed"
    LIQUIDATED = "liquidated"
    CANCELLED = "cancelled"

class LiquidationTriggerType(Enum):
    """Types of liquidation triggers"""
    TIME_BASED = "time_based"
    PRICE_BASED = "price_based"
    PAYMENT_DEFAULT = "payment_default"
    MANUAL = "manual"

@dataclass
class LiquidationTrigger:
    """Liquidation trigger configuration"""
    trigger_type: LiquidationTriggerType
    condition: Dict[str, Any]
    activated: bool = False
    activation_time: Optional[datetime] = None
    activation_reason: Optional[str] = None

@dataclass
class EscrowParties:
    """Parties involved in the escrow"""
    borrower: str
    lender: str
    platform: str
    arbitrator: Optional[str] = None

@dataclass
class EscrowContractTemplate:
    """
    Escrow contract template for collateral management
    This generates the TEAL logic for the smart contract
    """
    loan_id: str
    parties: EscrowParties
    collateral_amount: int
    loan_amount: int
    duration_days: int
    interest_rate: float
    liquidation_triggers: List[LiquidationTrigger]
    created_at: datetime

    def generate_teal_approval(self) -> str:
        """
        Generate TEAL approval program for the escrow contract
        Implements multi-sig logic and liquidation conditions
        """
        return f"""
#pragma version 8

// Escrow Contract for Loan {self.loan_id}
// Multi-signature escrow with automatic liquidation

// Application State Schema:
// Global:
// - "borrower": Address
// - "lender": Address
// - "platform": Address
// - "collateral": Uint64
// - "loan_amount": Uint64
// - "locked_until": Uint64
// - "status": Bytes
// - "liquidation_price": Uint64

// Transaction types
txn ApplicationID
int 0
==
bnz handle_creation

// Handle application calls
txn OnCompletion
int NoOp
==
bnz handle_noop

txn OnCompletion
int OptIn
==
bnz handle_optin

txn OnCompletion
int CloseOut
==
bnz handle_closeout

txn OnCompletion
int DeleteApplication
==
bnz handle_delete

// Reject unknown operations
err

handle_creation:
    // Initialize escrow state
    byte "borrower"
    byte "{self.parties.borrower}"
    app_global_put

    byte "lender"
    byte "{self.parties.lender}"
    app_global_put

    byte "platform"
    byte "{self.parties.platform}"
    app_global_put

    byte "collateral"
    int {self.collateral_amount}
    app_global_put

    byte "loan_amount"
    int {self.loan_amount}
    app_global_put

    byte "locked_until"
    global LatestTimestamp
    int {86400 * self.duration_days}
    +
    app_global_put

    byte "status"
    byte "created"
    app_global_put

    int 1
    return

handle_noop:
    // Route based on application arguments
    txna ApplicationArgs 0
    byte "fund"
    ==
    bnz handle_fund

    txna ApplicationArgs 0
    byte "liquidate"
    ==
    bnz handle_liquidate

    txna ApplicationArgs 0
    byte "release"
    ==
    bnz handle_release

    txna ApplicationArgs 0
    byte "repay"
    ==
    bnz handle_repay

    err

handle_fund:
    // Verify sender is borrower
    txn Sender
    byte "borrower"
    app_global_get
    ==
    assert

    // Verify collateral amount
    gtxn 1 Amount
    byte "collateral"
    app_global_get
    >=
    assert

    // Update status
    byte "status"
    byte "funded"
    app_global_put

    int 1
    return

handle_liquidate:
    // Check liquidation conditions
    global LatestTimestamp
    byte "locked_until"
    app_global_get
    >
    bnz liquidation_allowed

    // Check if called by authorized party
    txn Sender
    byte "platform"
    app_global_get
    ==
    txn Sender
    byte "lender"
    app_global_get
    ==
    ||
    assert

    liquidation_allowed:
    // Perform liquidation
    byte "status"
    byte "liquidated"
    app_global_put

    // Transfer collateral to lender
    itxn_begin
    int pay
    itxn_field TypeEnum
    byte "lender"
    app_global_get
    itxn_field Receiver
    byte "collateral"
    app_global_get
    itxn_field Amount
    itxn_submit

    int 1
    return

handle_release:
    // Verify multi-sig authorization
    txn Sender
    byte "platform"
    app_global_get
    ==
    assert

    // Verify loan repaid
    byte "status"
    app_global_get
    byte "repaid"
    ==
    assert

    // Release collateral to borrower
    itxn_begin
    int pay
    itxn_field TypeEnum
    byte "borrower"
    app_global_get
    itxn_field Receiver
    byte "collateral"
    app_global_get
    itxn_field Amount
    itxn_submit

    byte "status"
    byte "completed"
    app_global_put

    int 1
    return

handle_repay:
    // Verify repayment from borrower
    txn Sender
    byte "borrower"
    app_global_get
    ==
    assert

    // Verify repayment amount
    gtxn 1 Amount
    byte "loan_amount"
    app_global_get
    int {int(self.loan_amount * (1 + self.interest_rate/100))}
    >=
    assert

    // Update status
    byte "status"
    byte "repaid"
    app_global_put

    int 1
    return

handle_optin:
    int 1
    return

handle_closeout:
    int 1
    return

handle_delete:
    // Only allow deletion if completed or cancelled
    byte "status"
    app_global_get
    byte "completed"
    ==
    byte "status"
    app_global_get
    byte "cancelled"
    ==
    ||
    return
"""

    def generate_teal_clear(self) -> str:
        """Generate TEAL clear state program"""
        return """
#pragma version 8
int 1
return
"""

    def calculate_liquidation_price(self) -> int:
        """Calculate liquidation trigger price based on loan terms"""
        # 150% collateralization ratio
        return int(self.loan_amount * 1.5)

    def get_contract_address(self, app_id: int) -> str:
        """Calculate the contract escrow address from app ID"""
        # This would use actual Algorand SDK in production
        app_bytes = app_id.to_bytes(8, 'big')
        hash_input = b'appID' + app_bytes
        address_hash = hashlib.sha512_256(hash_input).digest()
        # Add Algorand address checksum (simplified)
        checksum = hashlib.sha512_256(address_hash + b'appID').digest()[:4]
        address_bytes = address_hash + checksum
        return base64.b32encode(address_bytes).decode('utf-8').rstrip('=')

class EscrowContractFactory:
    """Factory for creating escrow contracts"""

    @staticmethod
    def create_loan_escrow(
        loan_id: str,
        borrower: str,
        lender: str,
        platform_address: str,
        loan_amount: int,
        collateral_amount: int,
        duration_days: int,
        interest_rate: float
    ) -> EscrowContractTemplate:
        """Create a new loan escrow contract"""

        parties = EscrowParties(
            borrower=borrower,
            lender=lender,
            platform=platform_address,
            arbitrator=platform_address  # Platform acts as arbitrator
        )

        # Define liquidation triggers
        triggers = [
            LiquidationTrigger(
                trigger_type=LiquidationTriggerType.TIME_BASED,
                condition={
                    "days_overdue": 7,
                    "grace_period_hours": 24
                }
            ),
            LiquidationTrigger(
                trigger_type=LiquidationTriggerType.PRICE_BASED,
                condition={
                    "collateral_ratio_threshold": 1.2,  # 120% collateralization
                    "price_oracle": "algorand_defi_oracle"
                }
            ),
            LiquidationTrigger(
                trigger_type=LiquidationTriggerType.PAYMENT_DEFAULT,
                condition={
                    "missed_payments": 1,
                    "notification_required": True
                }
            )
        ]

        return EscrowContractTemplate(
            loan_id=loan_id,
            parties=parties,
            collateral_amount=collateral_amount,
            loan_amount=loan_amount,
            duration_days=duration_days,
            interest_rate=interest_rate,
            liquidation_triggers=triggers,
            created_at=datetime.utcnow()
        )

    @staticmethod
    def create_atomic_swap_escrow(
        loan_id: str,
        parties: EscrowParties,
        amounts: Dict[str, int],
        timeout_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Create atomic swap escrow for simultaneous exchange"""

        return {
            "loan_id": loan_id,
            "type": "atomic_swap",
            "parties": {
                "party_a": parties.borrower,
                "party_b": parties.lender,
                "escrow": parties.platform
            },
            "amounts": amounts,
            "timeout": timeout_seconds,
            "hash_lock": hashlib.sha256(f"{loan_id}_{datetime.utcnow()}".encode()).hexdigest(),
            "status": "pending"
        }