"""
Escrow Service for Collateral Management
Handles escrow lifecycle and enforcement logic
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import json

from .models import (
    EscrowContract, EscrowStatus, EscrowDeploymentRequest,
    EscrowDeploymentResponse, EscrowStatusResponse,
    LiquidationRequest, LiquidationResponse,
    ReleaseRequest, ReleaseResponse, EscrowEvent,
    TriggerStatus, LiquidationTrigger, EscrowParty
)
from .smart_contracts import EscrowContractFactory, EscrowContractTemplate
from .mcp_integration import MCPBlockchainClient, MCPConfig, MCPTransactionBuilder
from ..lending.models import CollateralType
from ..audit.event_hooks import (
    EnforcementHooks, event_context, audit_function, monitor_performance
)
from ..audit.models import AuditEventType, AuditSeverity, create_loan_audit_event
from ..audit.event_streaming import stream_audit_event, EventPriority
from ..audit.event_processor import process_audit_event

logger = logging.getLogger(__name__)

class EscrowService:
    """
    Main service for managing escrow contracts
    Provides high-level API for escrow operations
    """

    def __init__(self, mcp_config: Optional[MCPConfig] = None):
        """Initialize escrow service"""
        self.mcp_config = mcp_config or MCPConfig()
        self.escrow_storage: Dict[str, EscrowContract] = {}
        self.event_handlers: List[Any] = []
        self.platform_address = "PLATFORM_ADDRESS_HERE"  # Should be configured

    @audit_function(
        event_type=AuditEventType.TRANSACTION_CREATED,
        severity=AuditSeverity.INFO,
        capture_args=True,
        capture_result=True
    )
    @monitor_performance(threshold_ms=5000)
    async def deploy_escrow(
        self,
        request: EscrowDeploymentRequest
    ) -> EscrowDeploymentResponse:
        """
        Deploy a new escrow smart contract for loan collateral

        Args:
            request: Escrow deployment request with loan details

        Returns:
            Deployment response with escrow details
        """
        async with event_context(
            loan_id=request.loan_id,
            service_name="escrow_service",
            operation_name="deploy_escrow"
        ):
            try:
                # Generate unique escrow ID
                escrow_id = f"escrow_{request.loan_id}_{uuid.uuid4().hex[:8]}"

                # Create smart contract template
                contract_template = EscrowContractFactory.create_loan_escrow(
                    loan_id=request.loan_id,
                    borrower=request.borrower,
                    lender=request.lender,
                    platform_address=self.platform_address,
                    loan_amount=request.amount,
                    collateral_amount=request.collateral,
                    duration_days=request.duration,
                    interest_rate=request.interest_rate
                )

                # Generate TEAL programs
                approval_program = contract_template.generate_teal_approval()
                clear_program = contract_template.generate_teal_clear()

                # Deploy using MCP client
                async with MCPBlockchainClient(self.mcp_config) as mcp_client:
                deployment_result = await mcp_client.deploy_smart_contract(
                    approval_program=approval_program,
                    clear_program=clear_program,
                    global_schema={"num_uints": 8, "num_bytes": 8},
                    local_schema={"num_uints": 2, "num_bytes": 2},
                    creator_address=self.platform_address,
                    app_args=[request.loan_id]
                )

                if not deployment_result.get("success"):
                    return EscrowDeploymentResponse(
                        success=False,
                        error_message=deployment_result.get("error", "Deployment failed")
                    )

                app_id = deployment_result.get("app_id")
                escrow_address = contract_template.get_contract_address(app_id)

                # Create escrow contract record
                escrow = EscrowContract(
                    escrow_id=escrow_id,
                    escrow_address=escrow_address,
                    app_id=app_id,
                    loan_id=request.loan_id,
                    borrower=request.borrower,
                    lender=request.lender,
                    platform=self.platform_address,
                    loan_amount=request.amount,
                    collateral_amount=request.collateral,
                    collateral_type=CollateralType[request.collateral_type],
                    interest_rate=request.interest_rate,
                    duration_days=request.duration,
                    created_at=datetime.utcnow(),
                    deployed_at=datetime.utcnow(),
                    locked_until=datetime.utcnow() + timedelta(days=request.duration),
                    status=EscrowStatus.DEPLOYED,
                    deployment_transaction_id=deployment_result.get("transaction_id"),
                    liquidation_price=contract_template.calculate_liquidation_price(),
                    liquidation_triggers=self._create_liquidation_triggers(request),
                    parties=[
                        EscrowParty(address=request.borrower, role="borrower", signature_required=True),
                        EscrowParty(address=request.lender, role="lender", signature_required=True),
                        EscrowParty(address=self.platform_address, role="platform")
                    ]
                )

                # Add audit entry
                escrow.add_audit_entry(
                    action="ESCROW_DEPLOYED",
                    details={
                        "app_id": app_id,
                        "transaction_id": deployment_result.get("transaction_id")
                    },
                    actor="system"
                )

                # Store escrow contract
                self.escrow_storage[escrow_id] = escrow

                # Emit audit hook for escrow deployment
                await EnforcementHooks.escrow_deployed(
                    escrow_id=escrow_id,
                    loan_id=request.loan_id,
                    app_id=app_id,
                    escrow_address=escrow_address
                )

                # Create and stream detailed enforcement event with critical priority
                enforcement_event = create_loan_audit_event(
                    event_type=AuditEventType.TRANSACTION_CONFIRMED,
                    loan_id=request.loan_id,
                    borrower_address=request.borrower,
                    service_name="escrow_enforcement",
                    amount_micro_algos=request.collateral,
                    transaction_id=deployment_result.get("transaction_id"),
                    metadata={
                        "operation": "escrow_deployment",
                        "escrow_id": escrow_id,
                        "app_id": app_id,
                        "escrow_address": escrow_address,
                        "collateral_type": request.collateral_type,
                        "duration_days": request.duration,
                        "interest_rate": request.interest_rate,
                        "liquidation_price": contract_template.calculate_liquidation_price(),
                        "enforcement_triggers": [
                            {
                                "trigger_id": trigger.trigger_id,
                                "trigger_type": trigger.trigger_type,
                                "threshold": trigger.threshold_value
                            }
                            for trigger in self._create_liquidation_triggers(request)
                        ],
                        "real_time_streaming": True,
                        "subscriber_types": ["ui_subscribers", "compliance_subscribers", "analytics_subscribers"]
                    }
                )

                # Stream with critical priority for immediate UI updates
                await stream_audit_event(enforcement_event, EventPriority.CRITICAL)

                # Emit deployment event
                await self._emit_event(EscrowEvent(
                    event_id=str(uuid.uuid4()),
                    escrow_id=escrow_id,
                    event_type="ESCROW_DEPLOYED",
                    timestamp=datetime.utcnow(),
                    data={"app_id": app_id, "escrow_address": escrow_address},
                    transaction_id=deployment_result.get("transaction_id")
                ))

                return EscrowDeploymentResponse(
                    success=True,
                    escrow_id=escrow_id,
                    escrow_address=escrow_address,
                    app_id=app_id,
                    transaction_id=deployment_result.get("transaction_id"),
                    status="deployed"
                )

        except Exception as e:
            logger.error(f"Escrow deployment failed: {e}")
            return EscrowDeploymentResponse(
                success=False,
                error_message=f"Deployment error: {str(e)}"
            )

    async def get_escrow_status(self, escrow_id: str) -> EscrowStatusResponse:
        """
        Get current status of an escrow contract

        Args:
            escrow_id: Unique escrow identifier

        Returns:
            Status response with escrow details
        """
        try:
            escrow = self.escrow_storage.get(escrow_id)
            if not escrow:
                raise ValueError(f"Escrow {escrow_id} not found")

            # Get current balance from blockchain
            async with MCPBlockchainClient(self.mcp_config) as mcp_client:
                balance_result = await mcp_client.get_escrow_balance(escrow.escrow_address)
                current_balance = balance_result.get("balance", 0) if balance_result.get("success") else 0

            # Check liquidation triggers
            can_liquidate = await self._check_liquidation_conditions(escrow)
            can_release = escrow.status == EscrowStatus.REPAID

            return EscrowStatusResponse(
                escrow_id=escrow_id,
                status=escrow.status.value,
                balance=current_balance,
                locked_until=escrow.locked_until.isoformat() if escrow.locked_until else None,
                liquidation_price=escrow.liquidation_price,
                parties={
                    "borrower": escrow.borrower,
                    "lender": escrow.lender,
                    "platform": escrow.platform
                },
                triggers=[
                    {
                        "id": trigger.trigger_id,
                        "type": trigger.trigger_type,
                        "status": trigger.status.value,
                        "threshold": trigger.threshold_value,
                        "current": trigger.current_value
                    }
                    for trigger in escrow.liquidation_triggers
                ],
                can_liquidate=can_liquidate,
                can_release=can_release
            )

        except Exception as e:
            logger.error(f"Failed to get escrow status: {e}")
            raise

    @audit_function(
        event_type=AuditEventType.SYSTEM_ERROR,
        severity=AuditSeverity.CRITICAL,
        capture_args=True,
        capture_result=True
    )
    @monitor_performance(threshold_ms=10000)
    async def liquidate_escrow(
        self,
        request: LiquidationRequest
    ) -> LiquidationResponse:
        """
        Liquidate escrow collateral

        Args:
            request: Liquidation request with evidence

        Returns:
            Liquidation response with transaction details
        """
        async with event_context(
            service_name="escrow_service",
            operation_name="liquidate_escrow"
        ):
            try:
                escrow = self.escrow_storage.get(request.escrow_id)
                if not escrow:
                    return LiquidationResponse(
                        success=False,
                        error_message=f"Escrow {request.escrow_id} not found"
                    )

                # Verify liquidation conditions
                if not request.force:
                    can_liquidate = await self._check_liquidation_conditions(escrow)
                    if not can_liquidate:
                        return LiquidationResponse(
                            success=False,
                            error_message="Liquidation conditions not met"
                        )

                # Execute liquidation via MCP
                async with MCPBlockchainClient(self.mcp_config) as mcp_client:
                liquidation_result = await mcp_client.execute_liquidation(
                    app_id=escrow.app_id,
                    escrow_address=escrow.escrow_address,
                    lender_address=escrow.lender,
                    collateral_amount=escrow.collateral_amount,
                    evidence=request.evidence
                )

                if not liquidation_result.get("success"):
                    return LiquidationResponse(
                        success=False,
                        error_message=liquidation_result.get("error", "Liquidation failed")
                    )

                # Update escrow status
                escrow.status = EscrowStatus.LIQUIDATED
                escrow.liquidation_transaction_id = liquidation_result.get("transaction_id")
                escrow.completed_at = datetime.utcnow()

                # Add audit entry
                escrow.add_audit_entry(
                    action="ESCROW_LIQUIDATED",
                    details={
                        "reason": request.reason,
                        "evidence": request.evidence,
                        "transaction_id": liquidation_result.get("transaction_id")
                    },
                    actor=request.requestor
                )

                # Emit audit hook for liquidation
                await EnforcementHooks.liquidation_triggered(
                    escrow_id=request.escrow_id,
                    loan_id=escrow.loan_id,
                    reason=request.reason,
                    trigger_data={
                        "evidence": request.evidence,
                        "transaction_id": liquidation_result.get("transaction_id"),
                        "collateral_amount": escrow.collateral_amount
                    }
                )

                # Create and stream critical liquidation event for immediate alerts
                liquidation_event = create_loan_audit_event(
                    event_type=AuditEventType.SYSTEM_ERROR,  # Using SYSTEM_ERROR for critical liquidation events
                    loan_id=escrow.loan_id,
                    borrower_address=escrow.borrower,
                    service_name="escrow_enforcement",
                    amount_micro_algos=escrow.collateral_amount,
                    transaction_id=liquidation_result.get("transaction_id"),
                    metadata={
                        "operation": "liquidation_triggered",
                        "escrow_id": request.escrow_id,
                        "liquidation_reason": request.reason,
                        "evidence": request.evidence,
                        "collateral_amount": escrow.collateral_amount,
                        "distribution": liquidation_result.get("distribution", {}),
                        "trigger_timestamp": datetime.utcnow().isoformat(),
                        "real_time_streaming": True,
                        "priority_alert": True,
                        "subscriber_types": ["ui_subscribers", "compliance_subscribers", "monitoring_subscribers"],
                        "enforcement_action": "liquidation"
                    }
                )

                # Stream with critical priority for immediate notifications
                await stream_audit_event(liquidation_event, EventPriority.CRITICAL)

                # Emit liquidation event
                await self._emit_event(EscrowEvent(
                    event_id=str(uuid.uuid4()),
                    escrow_id=request.escrow_id,
                    event_type="ESCROW_LIQUIDATED",
                    timestamp=datetime.utcnow(),
                    data={
                        "reason": request.reason,
                        "distribution": liquidation_result.get("distribution", {})
                    },
                    transaction_id=liquidation_result.get("transaction_id")
                ))

                return LiquidationResponse(
                    success=True,
                    transaction_id=liquidation_result.get("transaction_id"),
                    distribution=liquidation_result.get("distribution", {}),
                    status="liquidated"
                )

        except Exception as e:
            logger.error(f"Liquidation failed: {e}")
            return LiquidationResponse(
                success=False,
                error_message=f"Liquidation error: {str(e)}"
            )

    @audit_function(
        event_type=AuditEventType.TRANSACTION_CONFIRMED,
        severity=AuditSeverity.INFO,
        capture_args=True,
        capture_result=True
    )
    @monitor_performance(threshold_ms=5000)
    async def release_collateral(
        self,
        request: ReleaseRequest
    ) -> ReleaseResponse:
        """
        Release collateral back to borrower

        Args:
            request: Release request with authorization

        Returns:
            Release response with transaction details
        """
        async with event_context(
            service_name="escrow_service",
            operation_name="release_collateral"
        ):
            try:
                escrow = self.escrow_storage.get(request.escrow_id)
            if not escrow:
                return ReleaseResponse(
                    success=False,
                    error_message=f"Escrow {request.escrow_id} not found"
                )

            # Verify release conditions
            if escrow.status != EscrowStatus.REPAID:
                return ReleaseResponse(
                    success=False,
                    error_message="Loan must be repaid before collateral release"
                )

            # Execute release via MCP
            async with MCPBlockchainClient(self.mcp_config) as mcp_client:
                release_result = await mcp_client.release_collateral(
                    app_id=escrow.app_id,
                    escrow_address=escrow.escrow_address,
                    borrower_address=escrow.borrower,
                    collateral_amount=escrow.collateral_amount,
                    proof_of_payment=request.proof_of_payment or ""
                )

                if not release_result.get("success"):
                    return ReleaseResponse(
                        success=False,
                        error_message=release_result.get("error", "Release failed")
                    )

                # Update escrow status
                escrow.status = EscrowStatus.RELEASED
                escrow.release_transaction_id = release_result.get("transaction_id")
                escrow.completed_at = datetime.utcnow()

                # Add audit entry
                escrow.add_audit_entry(
                    action="COLLATERAL_RELEASED",
                    details={
                        "authorization": request.authorization,
                        "transaction_id": release_result.get("transaction_id")
                    },
                    actor=request.requestor
                )

                # Emit audit hook for collateral release
                await EnforcementHooks.collateral_released(
                    escrow_id=request.escrow_id,
                    loan_id=escrow.loan_id,
                    amount=escrow.collateral_amount,
                    recipient=escrow.borrower
                )

                # Create and stream collateral release event for real-time updates
                release_event = create_loan_audit_event(
                    event_type=AuditEventType.TRANSACTION_CONFIRMED,
                    loan_id=escrow.loan_id,
                    borrower_address=escrow.borrower,
                    service_name="escrow_enforcement",
                    amount_micro_algos=escrow.collateral_amount,
                    transaction_id=release_result.get("transaction_id"),
                    metadata={
                        "operation": "collateral_release",
                        "escrow_id": request.escrow_id,
                        "released_amount": escrow.collateral_amount,
                        "recipient": escrow.borrower,
                        "authorization": request.authorization,
                        "release_timestamp": datetime.utcnow().isoformat(),
                        "real_time_streaming": True,
                        "subscriber_types": ["ui_subscribers", "compliance_subscribers", "analytics_subscribers"],
                        "enforcement_action": "release"
                    }
                )

                # Stream with high priority for immediate UI feedback
                await stream_audit_event(release_event, EventPriority.HIGH)

                # Emit release event
                await self._emit_event(EscrowEvent(
                    event_id=str(uuid.uuid4()),
                    escrow_id=request.escrow_id,
                    event_type="COLLATERAL_RELEASED",
                    timestamp=datetime.utcnow(),
                    data={
                        "released_amount": escrow.collateral_amount,
                        "recipient": escrow.borrower
                    },
                    transaction_id=release_result.get("transaction_id")
                ))

                return ReleaseResponse(
                    success=True,
                    transaction_id=release_result.get("transaction_id"),
                    released_amount=escrow.collateral_amount,
                    recipient=escrow.borrower,
                    status="released"
                )

        except Exception as e:
            logger.error(f"Collateral release failed: {e}")
            return ReleaseResponse(
                success=False,
                error_message=f"Release error: {str(e)}"
            )

    async def _check_liquidation_conditions(self, escrow: EscrowContract) -> bool:
        """Check if liquidation conditions are met"""

        # Check time-based triggers
        if escrow.locked_until and datetime.utcnow() > escrow.locked_until:
            return True

        # Check other triggers
        for trigger in escrow.liquidation_triggers:
            if trigger.status == TriggerStatus.TRIGGERED:
                return True

        return False

    def _create_liquidation_triggers(
        self,
        request: EscrowDeploymentRequest
    ) -> List[LiquidationTrigger]:
        """Create liquidation triggers for the escrow"""

        return [
            LiquidationTrigger(
                trigger_id=f"trigger_time_{uuid.uuid4().hex[:8]}",
                trigger_type="time_based",
                condition={"days_overdue": 7},
                status=TriggerStatus.MONITORING,
                threshold_value=float(request.duration + 7)
            ),
            LiquidationTrigger(
                trigger_id=f"trigger_price_{uuid.uuid4().hex[:8]}",
                trigger_type="price_based",
                condition={"collateral_ratio": 1.2},
                status=TriggerStatus.MONITORING,
                threshold_value=1.2
            )
        ]

    async def _emit_event(self, event: EscrowEvent):
        """Emit an escrow event to registered handlers"""
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def register_event_handler(self, handler):
        """Register an event handler"""
        self.event_handlers.append(handler)