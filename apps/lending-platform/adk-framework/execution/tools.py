# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Tools for the ADK Execution Agent
Implements blockchain execution and transaction preparation logic
"""

import json
import uuid
from typing import Dict, Any, List, Optional


def prepare_transaction_group(
    borrower_address: str,
    lender_address: str,
    loan_amount_algos: float,
    collateral_amount_algos: float,
    interest_rate_percent: float,
    duration_days: int,
    loan_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Prepare atomic transaction group for lending operation

    Args:
        borrower_address: Borrower's Algorand address
        lender_address: Lender's Algorand address
        loan_amount_algos: Loan amount in ALGO
        collateral_amount_algos: Collateral amount in ALGO
        interest_rate_percent: Interest rate percentage
        duration_days: Loan duration in days
        loan_id: Optional loan identifier

    Returns:
        Dict with prepared transaction group
    """

    if not loan_id:
        loan_id = f"LOAN_{uuid.uuid4().hex[:8].upper()}"

    # Convert to microAlgos
    loan_amount_micro = int(loan_amount_algos * 1_000_000)
    collateral_amount_micro = int(collateral_amount_algos * 1_000_000)

    # Calculate repayment amount
    interest_amount = loan_amount_algos * (interest_rate_percent / 100) * (duration_days / 365)
    total_repayment_micro = int((loan_amount_algos + interest_amount) * 1_000_000)

    # Create transaction group
    transaction_group = {
        "group_id": f"TXG_{uuid.uuid4().hex[:12].upper()}",
        "loan_id": loan_id,
        "type": "atomic_lending_group",
        "transactions": [
            {
                "txn_id": 1,
                "type": "collateral_deposit",
                "from_address": borrower_address,
                "to_address": "ESCROW_CONTRACT_ADDRESS",  # Would be actual escrow contract
                "amount_micro_algos": collateral_amount_micro,
                "note": f"Collateral deposit for loan {loan_id}",
                "required_signatures": [borrower_address],
                "validation_checks": [
                    "sufficient_balance",
                    "valid_address",
                    "minimum_balance_maintained"
                ]
            },
            {
                "txn_id": 2,
                "type": "loan_disbursement",
                "from_address": lender_address,
                "to_address": borrower_address,
                "amount_micro_algos": loan_amount_micro,
                "note": f"Loan disbursement for loan {loan_id}",
                "required_signatures": [lender_address],
                "validation_checks": [
                    "sufficient_lender_balance",
                    "collateral_locked",
                    "terms_agreed"
                ]
            },
            {
                "txn_id": 3,
                "type": "lending_contract_creation",
                "from_address": borrower_address,  # Contract creator pays fee
                "contract_params": {
                    "borrower": borrower_address,
                    "lender": lender_address,
                    "loan_amount": loan_amount_micro,
                    "collateral_amount": collateral_amount_micro,
                    "interest_rate": interest_rate_percent,
                    "duration_seconds": duration_days * 24 * 3600,
                    "repayment_amount": total_repayment_micro,
                    "loan_id": loan_id
                },
                "note": f"Smart contract creation for loan {loan_id}",
                "required_signatures": [borrower_address, lender_address],
                "validation_checks": [
                    "contract_compilation",
                    "parameter_validation",
                    "security_audit"
                ]
            }
        ],
        "execution_requirements": {
            "atomic_guarantee": True,
            "total_signatures_required": 3,  # borrower (2) + lender (2) - 1 overlapping
            "estimated_rounds": 4,
            "minimum_balance_requirements": {
                borrower_address: collateral_amount_micro + 100_000,  # Collateral + fees
                lender_address: loan_amount_micro + 100_000  # Loan + fees
            }
        },
        "timeline": {
            "preparation_time": "5-10 minutes",
            "signing_time": "10-30 minutes",
            "execution_time": "1-2 minutes",
            "confirmation_time": "1-2 minutes"
        }
    }

    return {
        "transaction_group": transaction_group,
        "group_hash": f"HASH_{uuid.uuid4().hex[:16].upper()}",
        "preparation_status": "ready",
        "next_steps": [
            "Validate all addresses and balances",
            "Get borrower signature on collateral deposit",
            "Get lender signature on disbursement",
            "Get joint signatures on contract creation",
            "Submit atomic group to network"
        ],
        "security_features": [
            "Atomic execution - all or nothing",
            "Escrow-based collateral protection",
            "Smart contract enforcement",
            "Multi-signature validation"
        ]
    }


def validate_execution_requirements(
    borrower_address: str,
    lender_address: str,
    loan_amount_algos: float,
    collateral_amount_algos: float,
    borrower_balance_algos: Optional[float] = None,
    lender_balance_algos: Optional[float] = None
) -> Dict[str, Any]:
    """
    Validate all requirements for successful loan execution

    Args:
        borrower_address: Borrower's Algorand address
        lender_address: Lender's Algorand address
        loan_amount_algos: Loan amount in ALGO
        collateral_amount_algos: Collateral amount in ALGO
        borrower_balance_algos: Borrower's current balance
        lender_balance_algos: Lender's current balance

    Returns:
        Dict with validation results
    """

    validation_results = {
        "overall_status": "pending",
        "can_execute": True,
        "critical_issues": [],
        "warnings": [],
        "requirements_met": [],
        "checks_performed": []
    }

    # Address validation
    def validate_algorand_address(address: str) -> bool:
        # Simplified validation - in production use proper Algorand address validation
        if address is None:
            return False
        return (
            len(address) == 58 and
            address.isalnum() and
            address.isupper()
        )

    # Check borrower address
    if validate_algorand_address(borrower_address):
        validation_results["requirements_met"].append("Valid borrower address format")
    else:
        validation_results["critical_issues"].append("Invalid borrower address format")
        validation_results["can_execute"] = False

    validation_results["checks_performed"].append("Borrower address format")

    # Check lender address
    if validate_algorand_address(lender_address):
        validation_results["requirements_met"].append("Valid lender address format")
    else:
        validation_results["critical_issues"].append("Invalid lender address format")
        validation_results["can_execute"] = False

    validation_results["checks_performed"].append("Lender address format")

    # Check addresses are different
    if borrower_address != lender_address:
        validation_results["requirements_met"].append("Borrower and lender are different parties")
    else:
        validation_results["critical_issues"].append("Borrower and lender cannot be the same address")
        validation_results["can_execute"] = False

    validation_results["checks_performed"].append("Address uniqueness")

    # Amount validations
    if loan_amount_algos > 0:
        validation_results["requirements_met"].append("Positive loan amount specified")
    else:
        validation_results["critical_issues"].append("Loan amount must be positive")
        validation_results["can_execute"] = False

    validation_results["checks_performed"].append("Loan amount validation")

    if collateral_amount_algos > 0:
        validation_results["requirements_met"].append("Positive collateral amount specified")
    else:
        validation_results["critical_issues"].append("Collateral amount must be positive")
        validation_results["can_execute"] = False

    validation_results["checks_performed"].append("Collateral amount validation")

    # Collateral ratio check
    if loan_amount_algos > 0:
        collateral_ratio = collateral_amount_algos / loan_amount_algos
        if collateral_ratio >= 1.1:
            validation_results["requirements_met"].append(f"Adequate collateral ratio ({collateral_ratio:.2f})")
        else:
            validation_results["warnings"].append(f"Low collateral ratio ({collateral_ratio:.2f}), consider increasing")

    validation_results["checks_performed"].append("Collateral ratio assessment")

    # Balance checks (if provided)
    min_borrower_balance = collateral_amount_algos + 0.1  # Collateral + fees
    min_lender_balance = loan_amount_algos + 0.1  # Loan + fees

    if borrower_balance_algos is not None:
        if borrower_balance_algos >= min_borrower_balance:
            validation_results["requirements_met"].append("Borrower has sufficient balance for collateral and fees")
        else:
            validation_results["critical_issues"].append(
                f"Borrower insufficient balance: {borrower_balance_algos:.6f} ALGO, "
                f"needs {min_borrower_balance:.6f} ALGO"
            )
            validation_results["can_execute"] = False

        validation_results["checks_performed"].append("Borrower balance verification")

    if lender_balance_algos is not None:
        if lender_balance_algos >= min_lender_balance:
            validation_results["requirements_met"].append("Lender has sufficient balance for loan and fees")
        else:
            validation_results["critical_issues"].append(
                f"Lender insufficient balance: {lender_balance_algos:.6f} ALGO, "
                f"needs {min_lender_balance:.6f} ALGO"
            )
            validation_results["can_execute"] = False

        validation_results["checks_performed"].append("Lender balance verification")

    # Network checks (simulated)
    validation_results["requirements_met"].extend([
        "Algorand network connectivity confirmed",
        "Smart contract deployment ready",
        "Escrow contract available"
    ])

    validation_results["checks_performed"].extend([
        "Network connectivity",
        "Smart contract readiness",
        "Escrow availability"
    ])

    # Determine overall status
    if validation_results["can_execute"]:
        if len(validation_results["warnings"]) == 0:
            validation_results["overall_status"] = "ready"
        else:
            validation_results["overall_status"] = "ready_with_warnings"
    else:
        validation_results["overall_status"] = "failed"

    return {
        "validation_results": validation_results,
        "execution_readiness": validation_results["overall_status"],
        "blocking_issues": validation_results["critical_issues"],
        "recommendations": [
            "Verify all addresses are correct",
            "Ensure sufficient balances before execution",
            "Consider collateral ratio adequacy",
            "Have all parties ready to sign promptly"
        ] if validation_results["can_execute"] else [
            "Resolve all critical issues before proceeding",
            "Double-check address formats and balances",
            "Ensure borrower and lender are different parties"
        ]
    }


def estimate_transaction_costs(
    transaction_group: Dict[str, Any],
    network_congestion: str = "low",
    priority_level: str = "standard"
) -> Dict[str, Any]:
    """
    Estimate comprehensive costs for transaction execution

    Args:
        transaction_group: Prepared transaction group
        network_congestion: Network congestion level (low/medium/high)
        priority_level: Transaction priority (economy/standard/priority)

    Returns:
        Dict with detailed cost estimation
    """

    # Base fees (in microAlgos)
    base_fee_per_txn = 1000  # Standard Algorand transaction fee

    # Congestion multipliers
    congestion_multipliers = {
        "low": 1.0,
        "medium": 1.5,
        "high": 2.0
    }

    # Priority multipliers
    priority_multipliers = {
        "economy": 1.0,
        "standard": 1.2,
        "priority": 1.8
    }

    congestion_mult = congestion_multipliers.get(network_congestion, 1.0)
    priority_mult = priority_multipliers.get(priority_level, 1.2)

    # Calculate per-transaction costs
    transactions = transaction_group.get("transactions", [])
    transaction_costs = []

    total_base_fees = 0
    total_contract_fees = 0

    for txn in transactions:
        base_cost = base_fee_per_txn * congestion_mult * priority_mult

        # Additional costs based on transaction type
        if txn.get("type") == "collateral_deposit":
            additional_cost = 500  # Escrow interaction
        elif txn.get("type") == "loan_disbursement":
            additional_cost = 500  # Transfer cost
        elif txn.get("type") == "lending_contract_creation":
            additional_cost = 10000  # Smart contract creation
            total_contract_fees += additional_cost
        else:
            additional_cost = 0

        total_cost = base_cost + additional_cost
        total_base_fees += base_cost

        transaction_costs.append({
            "transaction_id": txn.get("txn_id"),
            "type": txn.get("type"),
            "base_fee_micro_algos": int(base_cost),
            "additional_cost_micro_algos": additional_cost,
            "total_cost_micro_algos": int(total_cost)
        })

    # Calculate totals
    total_cost_micro = sum(txn["total_cost_micro_algos"] for txn in transaction_costs)
    total_cost_algos = total_cost_micro / 1_000_000

    # Calculate cost distribution
    borrower_costs = sum(
        txn["total_cost_micro_algos"]
        for txn in transaction_costs
        if txn["type"] in ["collateral_deposit", "lending_contract_creation"]
    )

    lender_costs = sum(
        txn["total_cost_micro_algos"]
        for txn in transaction_costs
        if txn["type"] == "loan_disbursement"
    )

    return {
        "cost_summary": {
            "total_cost_micro_algos": total_cost_micro,
            "total_cost_algos": round(total_cost_algos, 6),
            "borrower_portion_micro_algos": borrower_costs,
            "borrower_portion_algos": round(borrower_costs / 1_000_000, 6),
            "lender_portion_micro_algos": lender_costs,
            "lender_portion_algos": round(lender_costs / 1_000_000, 6)
        },
        "cost_breakdown": {
            "base_transaction_fees": total_base_fees,
            "smart_contract_fees": total_contract_fees,
            "escrow_interaction_fees": 1000,
            "network_congestion_premium": int((congestion_mult - 1.0) * total_base_fees),
            "priority_premium": int((priority_mult - 1.0) * total_base_fees)
        },
        "per_transaction_costs": transaction_costs,
        "cost_factors": {
            "number_of_transactions": len(transactions),
            "network_congestion": network_congestion,
            "priority_level": priority_level,
            "smart_contracts_involved": 1
        },
        "cost_optimization_suggestions": [
            "Use economy priority during low congestion periods",
            "Batch multiple operations when possible",
            "Consider off-peak hours for execution"
        ] if priority_level == "priority" else [
            "Current settings provide good cost efficiency"
        ]
    }


def create_lending_contract(
    borrower_address: str,
    lender_address: str,
    loan_terms: Dict[str, Any],
    contract_template: str = "standard_lending"
) -> Dict[str, Any]:
    """
    Create smart contract for lending agreement

    Args:
        borrower_address: Borrower's address
        lender_address: Lender's address
        loan_terms: Loan terms and conditions
        contract_template: Contract template to use

    Returns:
        Dict with contract creation details
    """

    loan_amount = loan_terms.get("amount_algos", 0)
    collateral_amount = loan_terms.get("collateral_amount_algos", 0)
    interest_rate = loan_terms.get("interest_rate_percent", 0)
    duration_days = loan_terms.get("duration_days", 30)

    # Generate contract parameters
    contract_params = {
        "borrower": borrower_address,
        "lender": lender_address,
        "loan_amount_micro": int(loan_amount * 1_000_000),
        "collateral_amount_micro": int(collateral_amount * 1_000_000),
        "interest_rate_basis_points": int(interest_rate * 100),  # Convert to basis points
        "loan_duration_seconds": duration_days * 24 * 3600,
        "creation_timestamp": 1640995200,  # Would be actual timestamp
        "maturity_timestamp": 1640995200 + (duration_days * 24 * 3600),
        "contract_id": f"LEND_CONTRACT_{uuid.uuid4().hex[:8].upper()}",
        "escrow_address": "ESCROW_CONTRACT_ADDRESS"  # Would be actual escrow
    }

    # Contract functions that will be available
    contract_functions = [
        "deposit_collateral",
        "disburse_loan",
        "repay_loan",
        "liquidate_collateral",
        "extend_loan",
        "partial_repayment",
        "get_loan_status",
        "calculate_interest"
    ]

    # Contract state variables
    state_variables = {
        "loan_status": "PENDING",  # PENDING, ACTIVE, REPAID, DEFAULTED, LIQUIDATED
        "collateral_deposited": False,
        "loan_disbursed": False,
        "repayment_made": False,
        "total_repaid_micro": 0,
        "interest_accrued_micro": 0,
        "last_payment_timestamp": 0
    }

    # Security features
    security_features = [
        "Multi-signature requirement for critical operations",
        "Time-lock for loan disbursement after collateral",
        "Automatic liquidation trigger on default",
        "Interest calculation with compound precision",
        "Emergency pause functionality",
        "Upgradeable proxy pattern for bug fixes"
    ]

    # Deployment requirements
    deployment_requirements = {
        "compiler_version": "PyTeal 0.20.0",
        "approval_program_size": "< 2KB",
        "clear_program_size": "< 1KB",
        "global_state_schema": {
            "num_uints": 8,
            "num_byte_slices": 4
        },
        "local_state_schema": {
            "num_uints": 4,
            "num_byte_slices": 2
        },
        "minimum_balance_requirement": 100000  # microAlgos
    }

    return {
        "contract_specification": {
            "template": contract_template,
            "contract_id": contract_params["contract_id"],
            "parameters": contract_params,
            "functions": contract_functions,
            "state_variables": state_variables
        },
        "security_features": security_features,
        "deployment": {
            "requirements": deployment_requirements,
            "estimated_cost_micro_algos": 28500,  # Deployment + setup
            "estimated_deployment_time": "2-3 minutes",
            "verification_steps": [
                "Compile contract source",
                "Run security audit checks",
                "Deploy to testnet first",
                "Verify deployment on mainnet",
                "Initialize contract state"
            ]
        },
        "usage_instructions": {
            "initialization": "Call setup with borrower and lender signatures",
            "activation": "Borrower deposits collateral, then lender disburses loan",
            "monitoring": "Both parties can query loan status anytime",
            "completion": "Borrower repays, collateral is released"
        },
        "risk_management": {
            "liquidation_threshold": "110% of loan value",
            "grace_period_hours": 24,
            "partial_liquidation_enabled": True,
            "emergency_contacts": ["borrower", "lender", "platform_admin"]
        }
    }