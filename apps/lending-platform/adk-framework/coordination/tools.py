# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Tools for the ADK Coordination Agent
Implements workflow coordination and MCP service integration
"""

import json
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import MCP integration tools from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_tools import check_mcp_services, get_account_balance, get_account_transactions

# Import new corrected MCP integration
from real_mcp_integration_v2 import MCPClient, MCPServiceConfig


def check_mcp_service_health() -> Dict[str, Any]:
    """
    Check health of MCP services for lending operations

    Returns:
        Dict with service health status
    """
    try:
        # This would normally be async, but simulating sync call for ADK
        # In production, you'd use asyncio.run() or proper async handling

        # Simulate MCP service health check
        service_status = {
            "algorand_reader": {
                "status": "healthy",
                "endpoint": "http://localhost:8002",
                "response_time_ms": 45,
                "last_check": datetime.utcnow().isoformat()
            },
            "algorand_writer": {
                "status": "healthy",
                "endpoint": "http://localhost:3001",
                "response_time_ms": 62,
                "last_check": datetime.utcnow().isoformat()
            }
        }

        all_healthy = all(svc["status"] == "healthy" for svc in service_status.values())

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "services": service_status,
            "can_proceed_with_lending": all_healthy,
            "issues": [] if all_healthy else [
                f"Service {name} is {status['status']}"
                for name, status in service_status.items()
                if status["status"] != "healthy"
            ],
            "recommendations": [
                "All services operational - can proceed with lending operations"
            ] if all_healthy else [
                "Check service connectivity before proceeding",
                "Consider using backup endpoints if available"
            ]
        }

    except Exception as e:
        return {
            "overall_status": "error",
            "services": {},
            "can_proceed_with_lending": False,
            "issues": [f"Health check failed: {str(e)}"],
            "recommendations": [
                "Verify MCP services are running",
                "Check network connectivity",
                "Review service configurations"
            ]
        }


def get_borrower_data(borrower_address: str, include_transactions: bool = True) -> Dict[str, Any]:
    """
    Retrieve comprehensive borrower data from Algorand network

    Args:
        borrower_address: Borrower's Algorand address
        include_transactions: Whether to include transaction history

    Returns:
        Dict with borrower data
    """
    try:
        # Simulate getting data from MCP services
        # In production, this would make actual MCP calls

        # Simulated account balance data
        balance_data = {
            "algo_balance_micro": 45_250_000,  # 45.25 ALGO
            "algo_balance": 45.25,
            "usdc_balance_micro": 100_000_000,  # 100 USDC equivalent
            "usdc_balance": 100.0,
            "minimum_balance_micro": 100_000,
            "available_balance_micro": 45_150_000,
            "total_assets": [
                {"asset_id": 0, "name": "ALGO", "balance": 45.25, "decimals": 6},
                {"asset_id": 31566704, "name": "USDC", "balance": 100.0, "decimals": 6}
            ]
        }

        # Simulated transaction history
        transaction_data = {
            "total_transactions": 156,
            "recent_transactions": [
                {
                    "id": "TXN123",
                    "type": "payment",
                    "amount": 5_000_000,
                    "date": "2025-01-10",
                    "counterparty": "EXAMPLE_ADDRESS_1"
                },
                {
                    "id": "TXN124",
                    "type": "payment",
                    "amount": 2_500_000,
                    "date": "2025-01-09",
                    "counterparty": "EXAMPLE_ADDRESS_2"
                }
            ],
            "average_amount": 3_200_000,
            "monthly_frequency": 18,
            "activity_span_days": 245,
            "largest_transaction": 25_000_000,
            "transaction_patterns": {
                "regular_payments": True,
                "consistent_activity": True,
                "high_value_transactions": False
            }
        } if include_transactions else {}

        # Calculate derived metrics
        account_metrics = {
            "account_age_estimated_days": transaction_data.get("activity_span_days", 0),
            "transaction_velocity": transaction_data.get("monthly_frequency", 0) / 30,
            "balance_utilization": balance_data["available_balance_micro"] / balance_data["algo_balance_micro"],
            "asset_diversification": len(balance_data["total_assets"]),
            "creditworthiness_indicators": {
                "balance_stability": "high" if balance_data["algo_balance"] >= 40 else "medium",
                "transaction_consistency": "high" if transaction_data.get("monthly_frequency", 0) >= 15 else "medium",
                "asset_holdings": "diversified" if len(balance_data["total_assets"]) > 1 else "single_asset"
            }
        }

        return {
            "borrower_address": borrower_address,
            "balance_data": balance_data,
            "transaction_data": transaction_data,
            "account_metrics": account_metrics,
            "data_freshness": datetime.utcnow().isoformat(),
            "data_quality": {
                "balance_accuracy": "high",
                "transaction_completeness": "complete" if include_transactions else "basic",
                "last_updated": datetime.utcnow().isoformat()
            },
            "risk_indicators": {
                "balance_risk": "low" if balance_data["algo_balance"] >= 20 else "medium",
                "activity_risk": "low" if transaction_data.get("total_transactions", 0) >= 50 else "medium",
                "overall_risk": "low"
            }
        }

    except Exception as e:
        return {
            "borrower_address": borrower_address,
            "error": f"Failed to retrieve borrower data: {str(e)}",
            "data_available": False,
            "recommendations": [
                "Verify borrower address format",
                "Check MCP service connectivity",
                "Try again with valid address"
            ]
        }


def get_lender_data(lender_address: str, check_lending_capacity: bool = True) -> Dict[str, Any]:
    """
    Retrieve lender data and lending capacity

    Args:
        lender_address: Lender's Algorand address
        check_lending_capacity: Whether to assess lending capacity

    Returns:
        Dict with lender data and capacity
    """
    try:
        # Simulate getting lender data from MCP services

        # Simulated lender balance data
        balance_data = {
            "algo_balance_micro": 125_750_000,  # 125.75 ALGO
            "algo_balance": 125.75,
            "usdc_balance_micro": 50_000_000,   # 50 USDC
            "usdc_balance": 50.0,
            "total_liquidity_algo": 175.75,  # Combined liquidity value
            "available_for_lending": 100.0,  # Conservative estimate
            "reserved_balance": 25.75  # Keep minimum for operations
        }

        # Lender profile information
        lender_profile = {
            "lender_type": "individual",  # individual, institutional, protocol
            "reputation_score": 87,
            "active_loans": 12,
            "total_loans_issued": 45,
            "successful_loan_completion_rate": 0.94,
            "average_loan_size": 25.5,
            "preferred_loan_duration_days": [30, 60, 90],
            "risk_tolerance": ["LOW", "MEDIUM"],
            "lending_history": {
                "first_loan_date": "2024-06-15",
                "total_interest_earned": 45.2,
                "defaults_experienced": 2,
                "average_return_rate": 8.5
            }
        }

        # Lending capacity assessment
        lending_capacity = {}
        if check_lending_capacity:
            max_single_loan = min(balance_data["available_for_lending"] * 0.4, 50.0)
            total_lending_capacity = balance_data["available_for_lending"] * 0.8

            lending_capacity = {
                "max_single_loan_algo": max_single_loan,
                "total_available_capacity_algo": total_lending_capacity,
                "current_utilization_percent": 35.0,  # Current loans / total capacity
                "can_lend_immediately": balance_data["available_for_lending"] >= 10,
                "minimum_loan_size": 1.0,
                "preferred_loan_sizes": [10, 25, 50],
                "rate_preferences": {
                    "minimum_acceptable_rate": 4.0,
                    "target_rate_range": [6.0, 12.0],
                    "risk_adjusted_rates": {
                        "LOW": 5.5,
                        "MEDIUM": 7.5,
                        "HIGH": 10.0
                    }
                }
            }

        return {
            "lender_address": lender_address,
            "balance_data": balance_data,
            "lender_profile": lender_profile,
            "lending_capacity": lending_capacity,
            "data_freshness": datetime.utcnow().isoformat(),
            "lender_status": {
                "active": True,
                "accepting_new_loans": True,
                "last_activity": "2025-01-12",
                "verification_level": "verified"
            },
            "market_position": {
                "rank_in_network": 15,  # Top 15 lender
                "total_network_share": 2.1,
                "competitive_rates": True,
                "response_time": "fast"  # fast, medium, slow
            }
        }

    except Exception as e:
        return {
            "lender_address": lender_address,
            "error": f"Failed to retrieve lender data: {str(e)}",
            "data_available": False,
            "recommendations": [
                "Verify lender address format",
                "Check MCP service connectivity",
                "Ensure lender is registered in system"
            ]
        }


def coordinate_lending_workflow(
    loan_request: Dict[str, Any],
    borrower_data: Dict[str, Any],
    lender_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Coordinate the complete lending workflow across all agents

    Args:
        loan_request: Complete loan request details
        borrower_data: Borrower information from get_borrower_data
        lender_data: Optional lender data if specific lender targeted

    Returns:
        Dict with complete workflow coordination results
    """
    workflow_id = f"WORKFLOW_{uuid.uuid4().hex[:8].upper()}"

    try:
        # Initialize workflow tracking
        workflow_state = {
            "workflow_id": workflow_id,
            "status": "initializing",
            "started_at": datetime.utcnow().isoformat(),
            "steps_completed": [],
            "current_step": "initialization",
            "agent_results": {},
            "errors": [],
            "warnings": []
        }

        # Step 1: Validate inputs
        validation_results = _validate_workflow_inputs(loan_request, borrower_data, lender_data)
        workflow_state["steps_completed"].append("input_validation")

        if not validation_results["valid"]:
            workflow_state["status"] = "failed"
            workflow_state["errors"] = validation_results["errors"]
            return {"workflow_coordination": workflow_state}

        # Step 2: Prepare data for agents
        workflow_state["current_step"] = "data_preparation"

        # Liquidity agent input
        liquidity_input = {
            "loan_request": loan_request,
            "borrower_assessment": {
                "address": borrower_data.get("borrower_address"),
                "balance_data": borrower_data.get("balance_data", {}),
                "transaction_history": borrower_data.get("transaction_data", {}),
                "risk_indicators": borrower_data.get("risk_indicators", {})
            },
            "lender_data": lender_data.get("lender_profile", {}) if lender_data else None
        }

        # Negotiation agent input
        negotiation_input = {
            "loan_request": loan_request,
            "borrower_profile": borrower_data,
            "market_conditions": {
                "base_rate": 7.5,
                "volatility": 0.15,
                "liquidity_available": True
            }
        }

        # Execution agent input
        execution_input = {
            "borrower_address": loan_request.get("borrower_address"),
            "loan_amount": loan_request.get("amount_algos", 0),
            "collateral_amount": loan_request.get("collateral_amount_algos", 0),
            "loan_terms": loan_request
        }

        workflow_state["steps_completed"].append("data_preparation")

        # Step 3: Orchestrate agent execution
        workflow_state["current_step"] = "agent_coordination"

        # In a real implementation, these would be actual agent calls
        # For now, we'll simulate the coordination
        agent_coordination_results = {
            "liquidity_analysis": {
                "status": "completed",
                "lenders_found": 3,
                "best_match": "AlgoCapital Partners",
                "recommended_rate": 7.2
            },
            "negotiation_results": {
                "status": "completed",
                "final_rate": 7.2,
                "terms_agreed": True,
                "collateral_ratio": 1.3
            },
            "execution_planning": {
                "status": "completed",
                "transactions_prepared": 3,
                "estimated_cost": 0.0285,
                "ready_for_execution": True
            }
        }

        workflow_state["agent_results"] = agent_coordination_results
        workflow_state["steps_completed"].append("agent_coordination")

        # Step 4: Final coordination
        workflow_state["current_step"] = "finalization"

        # Compile final results
        final_results = {
            "loan_approved": True,
            "final_terms": {
                "amount_algos": loan_request.get("amount_algos"),
                "interest_rate": 7.2,
                "duration_days": loan_request.get("duration_days"),
                "collateral_ratio": 1.3,
                "lender": "AlgoCapital Partners"
            },
            "execution_ready": True,
            "estimated_completion_time": "15-30 minutes",
            "next_actions": [
                "Review and approve final terms",
                "Sign transaction group",
                "Execute lending agreement",
                "Monitor loan status"
            ]
        }

        workflow_state["status"] = "completed"
        workflow_state["current_step"] = "completed"
        workflow_state["steps_completed"].append("finalization")
        workflow_state["completed_at"] = datetime.utcnow().isoformat()

        return {
            "workflow_coordination": workflow_state,
            "final_results": final_results,
            "success": True,
            "workflow_summary": {
                "total_steps": len(workflow_state["steps_completed"]),
                "processing_time": "estimated 2-5 minutes",
                "agents_involved": 3,
                "mcp_calls_made": 4,
                "success_rate": "100%"
            }
        }

    except Exception as e:
        workflow_state["status"] = "error"
        workflow_state["errors"].append(f"Workflow coordination failed: {str(e)}")

        return {
            "workflow_coordination": workflow_state,
            "success": False,
            "error": str(e),
            "recovery_suggestions": [
                "Check all input data is valid",
                "Verify MCP services are operational",
                "Review agent configurations",
                "Try again with simplified request"
            ]
        }


def _validate_workflow_inputs(
    loan_request: Dict[str, Any],
    borrower_data: Dict[str, Any],
    lender_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate inputs for workflow coordination

    Args:
        loan_request: Loan request to validate
        borrower_data: Borrower data to validate
        lender_data: Optional lender data to validate

    Returns:
        Dict with validation results
    """
    errors = []
    warnings = []

    # Validate loan request
    required_loan_fields = ["borrower_address", "amount_algos", "duration_days"]
    for field in required_loan_fields:
        if not loan_request.get(field):
            errors.append(f"Missing required loan field: {field}")

    if loan_request.get("amount_algos", 0) <= 0:
        errors.append("Loan amount must be positive")

    if loan_request.get("duration_days", 0) <= 0:
        errors.append("Loan duration must be positive")

    # Validate borrower data
    if not borrower_data.get("borrower_address"):
        errors.append("Missing borrower address")

    if borrower_data.get("error"):
        errors.append(f"Borrower data error: {borrower_data['error']}")

    balance_data = borrower_data.get("balance_data", {})
    if balance_data.get("algo_balance", 0) < 1.0:
        warnings.append("Low borrower balance may affect loan approval")

    # Validate lender data if provided
    if lender_data:
        if lender_data.get("error"):
            errors.append(f"Lender data error: {lender_data['error']}")

        lending_capacity = lender_data.get("lending_capacity", {})
        requested_amount = loan_request.get("amount_algos", 0)

        if not lending_capacity.get("can_lend_immediately", False):
            warnings.append("Lender may not have immediate lending capacity")

        if requested_amount > lending_capacity.get("max_single_loan_algo", 0):
            warnings.append("Requested amount exceeds lender's single loan limit")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "validation_summary": f"{len(errors)} errors, {len(warnings)} warnings"
    }