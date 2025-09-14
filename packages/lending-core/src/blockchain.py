"""
Blockchain Integration for Lending Platform Core
Pure blockchain logic without external service dependencies
"""

import os
import json
import base64
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TransactionSpec:
    """Specification for a blockchain transaction"""
    transaction_type: str
    sender: str
    receiver: str
    amount: int
    note_data: Dict[str, Any]
    requires_signature: bool = True


@dataclass
class LendingTransactionGroup:
    """Group of transactions for a lending operation"""
    group_id: str
    transactions: List[TransactionSpec]
    estimated_fee: int
    requires_signatures: List[str]
    metadata: Dict[str, Any]


class BlockchainTransactionBuilder:
    """Builder for blockchain transactions related to lending"""

    def __init__(self):
        self.network = os.getenv("ALGORAND_NETWORK", "testnet")
        logger.info(f"BlockchainTransactionBuilder initialized for {self.network}")

    def build_lending_transaction_group(
        self,
        lender_address: str,
        borrower_address: str,
        loan_amount: int,
        collateral_amount: int,
        duration_days: int,
        interest_rate: float
    ) -> LendingTransactionGroup:
        """Build a complete lending transaction group"""

        # Generate deterministic group ID
        import hashlib
        group_data = f"{lender_address}{borrower_address}{loan_amount}{datetime.utcnow().date()}"
        group_id = hashlib.sha256(group_data.encode()).hexdigest()[:16]

        # Generate escrow address for collateral
        escrow_address = self._generate_escrow_address(lender_address, borrower_address)

        # Transaction 1: Collateral deposit (borrower -> escrow)
        collateral_tx = TransactionSpec(
            transaction_type="collateral_deposit",
            sender=borrower_address,
            receiver=escrow_address,
            amount=collateral_amount,
            note_data={
                "type": "collateral_deposit",
                "loan_amount": loan_amount,
                "duration_days": duration_days,
                "interest_rate": interest_rate,
                "due_date": self._calculate_due_date(duration_days),
                "group_id": group_id
            }
        )

        # Transaction 2: Loan disbursement (lender -> borrower)
        loan_tx = TransactionSpec(
            transaction_type="loan_disbursement",
            sender=lender_address,
            receiver=borrower_address,
            amount=loan_amount,
            note_data={
                "type": "loan_disbursement",
                "collateral_amount": collateral_amount,
                "collateral_address": escrow_address,
                "repayment_amount": self._calculate_repayment_amount(loan_amount, interest_rate, duration_days),
                "group_id": group_id
            }
        )

        # Build transaction group
        transaction_group = LendingTransactionGroup(
            group_id=group_id,
            transactions=[collateral_tx, loan_tx],
            estimated_fee=2000,  # 2000 microAlgos (0.002 ALGO) per transaction
            requires_signatures=[borrower_address, lender_address],
            metadata={
                "loan_amount": loan_amount,
                "collateral_amount": collateral_amount,
                "interest_rate": interest_rate,
                "duration_days": duration_days,
                "escrow_address": escrow_address,
                "created_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Built lending transaction group {group_id} for {loan_amount/1_000_000} ALGO loan"
        )

        return transaction_group

    def build_repayment_transaction_group(
        self,
        borrower_address: str,
        lender_address: str,
        escrow_address: str,
        principal_amount: int,
        interest_amount: int,
        collateral_amount: int
    ) -> LendingTransactionGroup:
        """Build a loan repayment transaction group"""

        # Generate group ID for repayment
        import hashlib
        group_data = f"repay_{borrower_address}{lender_address}{principal_amount}{datetime.utcnow().date()}"
        group_id = hashlib.sha256(group_data.encode()).hexdigest()[:16]

        total_repayment = principal_amount + interest_amount

        # Transaction 1: Repayment (borrower -> lender)
        repayment_tx = TransactionSpec(
            transaction_type="loan_repayment",
            sender=borrower_address,
            receiver=lender_address,
            amount=total_repayment,
            note_data={
                "type": "loan_repayment",
                "principal": principal_amount,
                "interest": interest_amount,
                "total": total_repayment,
                "group_id": group_id
            }
        )

        # Transaction 2: Collateral release (escrow -> borrower)
        collateral_release_tx = TransactionSpec(
            transaction_type="collateral_release",
            sender=escrow_address,
            receiver=borrower_address,
            amount=collateral_amount,
            note_data={
                "type": "collateral_release",
                "original_loan": principal_amount,
                "group_id": group_id
            }
        )

        transaction_group = LendingTransactionGroup(
            group_id=group_id,
            transactions=[repayment_tx, collateral_release_tx],
            estimated_fee=2000,
            requires_signatures=[borrower_address],  # Escrow is automated
            metadata={
                "repayment_amount": total_repayment,
                "collateral_released": collateral_amount,
                "created_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Built repayment transaction group {group_id} for {total_repayment/1_000_000} ALGO"
        )

        return transaction_group

    def build_liquidation_transaction_group(
        self,
        lender_address: str,
        borrower_address: str,
        escrow_address: str,
        outstanding_debt: int,
        collateral_amount: int
    ) -> LendingTransactionGroup:
        """Build a loan liquidation transaction group"""

        import hashlib
        group_data = f"liquidate_{lender_address}{borrower_address}{outstanding_debt}{datetime.utcnow().date()}"
        group_id = hashlib.sha256(group_data.encode()).hexdigest()[:16]

        # Calculate liquidation amounts
        liquidation_amount = min(outstanding_debt, collateral_amount)
        remaining_collateral = collateral_amount - liquidation_amount

        transactions = []

        # Transaction 1: Liquidation payment (escrow -> lender)
        liquidation_tx = TransactionSpec(
            transaction_type="loan_liquidation",
            sender=escrow_address,
            receiver=lender_address,
            amount=liquidation_amount,
            note_data={
                "type": "loan_liquidation",
                "outstanding_debt": outstanding_debt,
                "liquidation_amount": liquidation_amount,
                "group_id": group_id
            }
        )
        transactions.append(liquidation_tx)

        # Transaction 2: Return remaining collateral (if any)
        if remaining_collateral > 0:
            remaining_tx = TransactionSpec(
                transaction_type="collateral_return",
                sender=escrow_address,
                receiver=borrower_address,
                amount=remaining_collateral,
                note_data={
                    "type": "collateral_return",
                    "original_collateral": collateral_amount,
                    "liquidation_amount": liquidation_amount,
                    "group_id": group_id
                }
            )
            transactions.append(remaining_tx)

        transaction_group = LendingTransactionGroup(
            group_id=group_id,
            transactions=transactions,
            estimated_fee=len(transactions) * 1000,
            requires_signatures=[],  # Automated liquidation
            metadata={
                "liquidation_amount": liquidation_amount,
                "remaining_collateral": remaining_collateral,
                "outstanding_debt": outstanding_debt,
                "created_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Built liquidation transaction group {group_id} for {liquidation_amount/1_000_000} ALGO"
        )

        return transaction_group

    def _generate_escrow_address(self, lender: str, borrower: str) -> str:
        """Generate deterministic escrow address for the loan"""
        # In production, this would deploy a smart contract
        # For now, generate a deterministic address
        import hashlib
        combined = f"ESCROW_{lender}_{borrower}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()

        # Generate a valid Algorand address format
        # This is a placeholder - in production, deploy actual escrow contract
        from base64 import b32encode
        address_bytes = hash_bytes[:32]
        # Add checksum (simplified)
        checksum = hashlib.sha512(address_bytes).digest()[:4]
        full_address = address_bytes + checksum

        # Convert to base32 (similar to Algorand addresses)
        b32_address = b32encode(full_address).decode().replace('=', '')

        # Format to look like an Algorand address (58 characters)
        formatted_address = b32_address[:58]

        return formatted_address

    def _calculate_due_date(self, duration_days: int) -> str:
        """Calculate loan due date"""
        due_date = datetime.utcnow() + timedelta(days=duration_days)
        return due_date.isoformat()

    def _calculate_repayment_amount(self, principal: int, interest_rate: float, duration_days: int) -> int:
        """Calculate total repayment amount including interest"""
        annual_interest = interest_rate / 100
        daily_interest = annual_interest / 365
        interest_amount = int(principal * daily_interest * duration_days)
        return principal + interest_amount

    def estimate_transaction_fees(self, transaction_group: LendingTransactionGroup) -> Dict[str, Any]:
        """Estimate transaction fees for a transaction group"""

        base_fee_per_tx = 1000  # 1000 microAlgos base fee
        num_transactions = len(transaction_group.transactions)

        # Add complexity fees
        complexity_fee = 0
        for tx in transaction_group.transactions:
            if tx.note_data:
                complexity_fee += len(json.dumps(tx.note_data)) * 10  # Fee for note data

        total_fee = (base_fee_per_tx * num_transactions) + complexity_fee

        return {
            "base_fee": base_fee_per_tx * num_transactions,
            "complexity_fee": complexity_fee,
            "total_fee": total_fee,
            "fee_in_algos": total_fee / 1_000_000,
            "transactions": num_transactions
        }

    def validate_transaction_group(self, transaction_group: LendingTransactionGroup) -> Dict[str, Any]:
        """Validate a transaction group before execution"""

        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }

        # Check transaction count
        if len(transaction_group.transactions) == 0:
            validation_results["valid"] = False
            validation_results["errors"].append("Transaction group is empty")

        validation_results["checks"]["transaction_count"] = len(transaction_group.transactions)

        # Check addresses
        for i, tx in enumerate(transaction_group.transactions):
            if len(tx.sender) != 58:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Transaction {i}: Invalid sender address length")

            if len(tx.receiver) != 58:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Transaction {i}: Invalid receiver address length")

            if tx.amount <= 0:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Transaction {i}: Invalid amount")

        # Check for circular transactions
        addresses = set()
        for tx in transaction_group.transactions:
            addresses.add(tx.sender)
            addresses.add(tx.receiver)

        validation_results["checks"]["unique_addresses"] = len(addresses)

        # Fee validation
        fee_estimate = self.estimate_transaction_fees(transaction_group)
        if transaction_group.estimated_fee < fee_estimate["total_fee"]:
            validation_results["warnings"].append("Estimated fee may be too low")

        validation_results["checks"]["fee_estimate"] = fee_estimate

        return validation_results


# Utility functions for blockchain operations
def create_loan_note(note_type: str, data: Dict[str, Any]) -> bytes:
    """Create standardized loan note for blockchain"""
    note_data = {
        "type": note_type,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0",
        **data
    }
    return json.dumps(note_data).encode()


def parse_loan_note(note_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Parse loan note from blockchain transaction"""
    try:
        note_str = note_bytes.decode('utf-8')
        return json.loads(note_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to parse loan note: {e}")
        return None


def format_transaction_for_signing(tx_spec: TransactionSpec) -> Dict[str, Any]:
    """Format transaction spec for external signing"""
    return {
        "type": tx_spec.transaction_type,
        "from": tx_spec.sender,
        "to": tx_spec.receiver,
        "amount": tx_spec.amount,
        "note": create_loan_note(tx_spec.transaction_type, tx_spec.note_data).decode('utf-8'),
        "requires_signature": tx_spec.requires_signature
    }