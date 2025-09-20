"""
Core Lending Workflow Logic
Pure business logic without external dependencies
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from .models import (
    LoanRequest, LoanTerms, LoanResult,
    LoanStatus, CollateralType, AgentResult, AccountBalance, MCPServiceConfig
)
from .error_handling import LendingError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)


class LendingWorkflow:
    """
    Core lending workflow orchestrator
    Contains pure business logic for lending operations
    """

    def __init__(self, mcp_config: Optional[MCPServiceConfig] = None):
        self.mcp_config = mcp_config or MCPServiceConfig()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}

        logger.info("LendingWorkflow initialized")

    async def process_lending_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to process a complete lending request
        Pure business logic without external service dependencies
        """
        workflow_id = str(uuid.uuid4())

        # Initialize workflow tracking
        self.active_workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "status": LoanStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "request": request_data,
            "steps": [],
            "errors": [],
            "current_step": None
        }

        try:
            logger.info(f"[{workflow_id}] Starting lending workflow for {request_data.get('amount', 0)/1_000_000} ALGO")

            # Step 1: Validate and create request
            request = self._create_lending_request(request_data, workflow_id)

            # Step 2: Simulate liquidity discovery (core logic only)
            logger.info(f"[{workflow_id}] Processing liquidity requirements...")
            self._update_workflow_step(workflow_id, "liquidity_analysis", LoanStatus.PENDING)

            liquidity_analysis = await self._analyze_liquidity_requirements(request)

            if not liquidity_analysis["feasible"]:
                return self._handle_workflow_failure(
                    workflow_id,
                    liquidity_analysis["reason"],
                    ErrorCategory.LIQUIDITY_SHORTAGE
                )

            # Step 3: Generate term recommendations
            logger.info(f"[{workflow_id}] Generating term recommendations...")
            self._update_workflow_step(workflow_id, "term_analysis", LoanStatus.APPROVED)

            recommended_terms = await self._generate_recommended_terms(request, liquidity_analysis)

            # Step 4: Validate execution requirements
            logger.info(f"[{workflow_id}] Validating execution requirements...")
            self._update_workflow_step(workflow_id, "execution_validation", LoanStatus.ACTIVE)

            execution_validation = await self._validate_execution_requirements(recommended_terms)

            if execution_validation["ready"]:
                self._update_workflow_step(workflow_id, "completed", LoanStatus.COMPLETED)
                logger.info(f"[{workflow_id}] Lending workflow analysis completed!")

                return {
                    "workflow_id": workflow_id,
                    "status": "ready_for_execution",
                    "recommended_terms": {
                        "amount": recommended_terms["amount_micro_algos"],
                        "interest_rate": recommended_terms["interest_rate"],
                        "duration_days": recommended_terms["duration_days"],
                        "collateral_type": recommended_terms["collateral_type"],
                        "collateral_amount": recommended_terms["collateral_amount"]
                    },
                    "liquidity_analysis": liquidity_analysis,
                    "execution_requirements": execution_validation,
                    "next_steps": [
                        "Connect to lender network",
                        "Execute term negotiation",
                        "Prepare blockchain transactions",
                        "Execute lending agreement"
                    ]
                }
            else:
                return self._handle_workflow_failure(
                    workflow_id,
                    execution_validation["issue"],
                    ErrorCategory.EXECUTION_FAILED
                )

        except LendingError as e:
            logger.error(f"[{workflow_id}] Lending workflow error: {e}")
            return self._handle_workflow_failure(workflow_id, str(e), e.category)

        except Exception as e:
            logger.error(f"[{workflow_id}] Unexpected workflow error: {e}")
            return self._handle_workflow_failure(
                workflow_id,
                f"Unexpected error: {str(e)}",
                ErrorCategory.SYSTEM_ERROR
            )

    def _create_lending_request(self, request_data: Dict[str, Any], workflow_id: str) -> LoanRequest:
        """Create and validate lending request"""
        try:
            return LoanRequest(
                borrower_address=request_data["borrower"],
                lender_address=request_data.get("lender"),
                amount_micro_algos=request_data["amount"],
                duration_days=request_data["duration"],
                max_interest_rate=request_data.get("max_interest_rate", 10.0),
                collateral_type=CollateralType(request_data.get("collateral_type", "ALGO")),
                collateral_amount=request_data.get("collateral_amount", int(request_data["amount"] * 1.3))
            )
        except Exception as e:
            raise LendingError(
                f"Invalid lending request: {str(e)}",
                ErrorCategory.VALIDATION_ERROR,
                ErrorSeverity.HIGH
            )

    async def _analyze_liquidity_requirements(self, request: LoanRequest) -> Dict[str, Any]:
        """Analyze liquidity requirements for the request"""

        # Core business logic for liquidity analysis
        amount_algos = request.amount_micro_algos / 1_000_000

        # Basic feasibility checks
        if amount_algos > 100_000:  # Max loan size
            return {
                "feasible": False,
                "reason": "Loan amount exceeds maximum limit of 100,000 ALGO",
                "max_available": 100_000
            }

        if request.duration_days > 365:  # Max duration
            return {
                "feasible": False,
                "reason": "Loan duration exceeds maximum of 365 days",
                "max_duration": 365
            }

        # Simulate realistic analysis
        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            "feasible": True,
            "estimated_availability": amount_algos * 1.2,  # 20% buffer
            "market_interest_rate": 8.5,
            "collateral_ratio_required": 1.3,
            "estimated_processing_time": "2-4 hours"
        }

    async def _generate_recommended_terms(self, request: LoanRequest, liquidity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommended terms based on request and market conditions"""

        # Core business logic for term generation
        base_rate = liquidity_analysis.get("market_interest_rate", 8.5)

        # Adjust rate based on duration and collateral
        duration_factor = min(0.02 * (request.duration_days / 30), 2.0)  # Up to 2% adjustment
        collateral_factor = -0.5 if request.collateral_type == CollateralType.ALGO else 0.5

        recommended_rate = min(
            base_rate + duration_factor + collateral_factor,
            request.max_interest_rate
        )

        await asyncio.sleep(0.05)  # Simulate processing

        return {
            "amount_micro_algos": request.amount_micro_algos,
            "interest_rate": recommended_rate,
            "duration_days": request.duration_days,
            "collateral_type": request.collateral_type.value,
            "collateral_amount": request.collateral_amount,
            "estimated_total_repayment": request.amount_micro_algos * (1 + recommended_rate/100 * request.duration_days/365),
            "risk_assessment": "medium" if recommended_rate < 10 else "high"
        }

    async def _validate_execution_requirements(self, terms: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that execution requirements can be met"""

        # Core business logic for execution validation
        checks = {
            "blockchain_connectivity": True,  # Would check actual connectivity
            "smart_contract_availability": True,  # Would verify contract deployment
            "collateral_validation": True,  # Would validate collateral tokens
            "regulatory_compliance": True   # Would check compliance requirements
        }

        await asyncio.sleep(0.05)  # Simulate validation time

        all_checks_pass = all(checks.values())

        return {
            "ready": all_checks_pass,
            "checks": checks,
            "issue": None if all_checks_pass else "Some validation checks failed",
            "estimated_execution_time": "5-10 minutes" if all_checks_pass else None
        }

    def _update_workflow_step(self, workflow_id: str, step_name: str, status: LoanStatus):
        """Update workflow step and status"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["current_step"] = step_name
            self.active_workflows[workflow_id]["status"] = status

            step_info = {
                "step_name": step_name,
                "status": status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.active_workflows[workflow_id]["steps"].append(step_info)

    def _handle_workflow_failure(self, workflow_id: str, error_message: str, category: ErrorCategory) -> Dict[str, Any]:
        """Handle workflow failure"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["status"] = LoanStatus.DEFAULTED
            self.active_workflows[workflow_id]["error"] = error_message
            self.active_workflows[workflow_id]["error_category"] = category.value

        return {
            "workflow_id": workflow_id,
            "status": "failed",
            "error": error_message,
            "error_category": category.value,
            "recovery_suggestions": self._get_recovery_suggestions(category)
        }

    def _get_recovery_suggestions(self, category: ErrorCategory) -> List[str]:
        """Get recovery suggestions based on error category"""
        suggestions = {
            ErrorCategory.LIQUIDITY_SHORTAGE: [
                "Try requesting a smaller loan amount",
                "Offer higher interest rate",
                "Use different collateral type",
                "Try again later when more liquidity is available"
            ],
            ErrorCategory.NEGOTIATION_FAILED: [
                "Adjust your maximum interest rate",
                "Offer more collateral",
                "Reduce loan duration",
                "Try different collateral types"
            ],
            ErrorCategory.EXECUTION_FAILED: [
                "Verify your Algorand address is valid",
                "Ensure sufficient balance for transaction fees",
                "Check network connectivity",
                "Contact support if problem persists"
            ],
            ErrorCategory.VALIDATION_ERROR: [
                "Check all required fields are provided",
                "Verify Algorand address format",
                "Ensure loan amount is within limits",
                "Review collateral requirements"
            ],
            ErrorCategory.SYSTEM_ERROR: [
                "Try again in a few minutes",
                "Check service status",
                "Contact support if problem persists"
            ]
        }
        return suggestions.get(category, ["Contact support for assistance"])

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            raise LendingError(
                f"Workflow {workflow_id} not found",
                ErrorCategory.VALIDATION_ERROR,
                ErrorSeverity.LOW
            )

        workflow = self.active_workflows[workflow_id]

        return {
            "workflow_id": workflow_id,
            "status": workflow["status"].value if hasattr(workflow["status"], 'value') else str(workflow["status"]),
            "current_step": workflow.get("current_step"),
            "created_at": workflow["created_at"],
            "steps_completed": len([s for s in workflow.get("steps", []) if s.get("status") != "in_progress"]),
            "total_steps": len(workflow.get("steps", [])),
            "progress_percentage": self._calculate_progress_percentage(workflow),
            "error": workflow.get("error"),
            "error_category": workflow.get("error_category")
        }

    def _calculate_progress_percentage(self, workflow: Dict[str, Any]) -> float:
        """Calculate workflow progress percentage"""
        steps = workflow.get("steps", [])
        if not steps:
            return 0.0

        completed_steps = len([s for s in steps if s.get("status") not in ["in_progress", "failed"]])
        total_expected_steps = 4  # liquidity_analysis, term_analysis, execution_validation, completed

        return min(100.0, (completed_steps / total_expected_steps) * 100.0)