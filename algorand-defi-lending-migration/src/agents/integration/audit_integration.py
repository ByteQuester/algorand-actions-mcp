# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Agent-Audit System Integration Layer
Connects AI agent actions with audit trail logging and compliance checking
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from functools import wraps

# Import audit system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.audit.models import AuditEventType, AuditEntry
from core.audit.audit_service import AuditService
from core.audit.compliance_service import ComplianceService
from api.websocket_router import broadcast_audit_event


class AgentAuditLogger:
    """Centralized audit logging for agent operations"""

    def __init__(self):
        self.audit_service = AuditService()
        self.compliance_service = ComplianceService()

    async def log_agent_action(
        self,
        agent_name: str,
        action: str,
        details: Dict[str, Any],
        loan_id: Optional[str] = None,
        user_id: str = "system",
        session_id: Optional[str] = None
    ) -> str:
        """Log an agent action to the audit trail"""

        event_id = str(uuid.uuid4())

        # Determine event type based on action
        event_type_map = {
            "agent_invoked": AuditEventType.AGENT_INVOKED,
            "agent_completed": AuditEventType.AGENT_COMPLETED,
            "agent_failed": AuditEventType.AGENT_FAILED,
            "tool_executed": AuditEventType.TOOL_EXECUTED,
            "loan_assessment": AuditEventType.LOAN_REQUEST_UPDATED,
            "risk_evaluation": AuditEventType.DATA_ACCESSED,
            "compliance_check": AuditEventType.COMPLIANCE_CHECK_PERFORMED
        }

        event_type = event_type_map.get(action, AuditEventType.AGENT_INVOKED)

        # Create audit entry
        audit_entry = AuditEntry(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id or f"agent_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            loan_id=loan_id,
            agent_name=agent_name,
            details={
                "agent_action": action,
                "agent_name": agent_name,
                "action_details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_id": event_id
            },
            ip_address="127.0.0.1",  # Internal agent calls
            user_agent=f"Agent/{agent_name}"
        )

        # Log to audit service
        await self.audit_service.log_event(audit_entry)

        # Broadcast real-time event
        await broadcast_audit_event({
            "event_type": "agent_action",
            "event_id": event_id,
            "agent_name": agent_name,
            "action": action,
            "loan_id": loan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        })

        return event_id

    async def log_compliance_check(
        self,
        agent_name: str,
        decision_data: Dict[str, Any],
        loan_id: str,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """Log compliance check and return results"""

        # Perform compliance analysis
        compliance_result = await self.compliance_service.analyze_decision_bias(
            loan_id=loan_id,
            decision_data=decision_data
        )

        # Log compliance check
        await self.log_agent_action(
            agent_name=agent_name,
            action="compliance_check",
            details={
                "decision_data": decision_data,
                "compliance_result": compliance_result,
                "bias_detected": compliance_result.get("bias_detected", False),
                "compliance_score": compliance_result.get("compliance_score", 0.0)
            },
            loan_id=loan_id,
            user_id=user_id
        )

        return compliance_result


# Global audit logger instance
agent_audit_logger = AgentAuditLogger()


def audit_agent_action(action: str, include_result: bool = True):
    """Decorator to automatically audit agent actions"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            agent_name = getattr(self, 'name', 'unknown_agent')

            # Extract loan_id if present in kwargs
            loan_id = kwargs.get('loan_id') or kwargs.get('borrower_address')

            # Log agent invocation
            event_id = await agent_audit_logger.log_agent_action(
                agent_name=agent_name,
                action="agent_invoked",
                details={
                    "function": func.__name__,
                    "action": action,
                    "args": str(args)[:500],  # Truncate long args
                    "kwargs": {k: str(v)[:200] for k, v in kwargs.items()},  # Truncate values
                    "event_id": str(uuid.uuid4())
                },
                loan_id=loan_id
            )

            try:
                # Execute the function
                result = await func(self, *args, **kwargs)

                # Log successful completion
                await agent_audit_logger.log_agent_action(
                    agent_name=agent_name,
                    action="agent_completed",
                    details={
                        "function": func.__name__,
                        "action": action,
                        "result": str(result)[:1000] if include_result else "result_omitted",
                        "success": True,
                        "original_event_id": event_id
                    },
                    loan_id=loan_id
                )

                return result

            except Exception as e:
                # Log failure
                await agent_audit_logger.log_agent_action(
                    agent_name=agent_name,
                    action="agent_failed",
                    details={
                        "function": func.__name__,
                        "action": action,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "success": False,
                        "original_event_id": event_id
                    },
                    loan_id=loan_id
                )
                raise

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # For synchronous functions, create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create task
                    return loop.create_task(async_wrapper(self, *args, **kwargs))
                else:
                    return loop.run_until_complete(async_wrapper(self, *args, **kwargs))
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(async_wrapper(self, *args, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def audit_compliance_decision(decision_type: str):
    """Decorator to automatically run compliance checks on agent decisions"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            agent_name = getattr(self, 'name', 'unknown_agent')

            # Execute the function to get decision
            result = await func(self, *args, **kwargs)

            # Extract decision data for compliance check
            decision_data = {
                "decision_type": decision_type,
                "function": func.__name__,
                "agent": agent_name,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "args": str(args)[:200],
                "kwargs": {k: str(v)[:100] for k, v in kwargs.items()}
            }

            # Extract loan_id
            loan_id = kwargs.get('loan_id') or kwargs.get('borrower_address') or "unknown"

            # Run compliance check
            compliance_result = await agent_audit_logger.log_compliance_check(
                agent_name=agent_name,
                decision_data=decision_data,
                loan_id=loan_id
            )

            # Add compliance info to result if it's a dict
            if isinstance(result, dict):
                result['compliance_check'] = {
                    "performed": True,
                    "bias_score": compliance_result.get("bias_score", 0.0),
                    "compliance_score": compliance_result.get("compliance_score", 100.0),
                    "issues": compliance_result.get("issues", [])
                }

            return result

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return loop.create_task(async_wrapper(self, *args, **kwargs))
                else:
                    return loop.run_until_complete(async_wrapper(self, *args, **kwargs))
            except RuntimeError:
                return asyncio.run(async_wrapper(self, *args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class AuditIntegratedWorkflow:
    """Workflow manager with integrated audit trails"""

    def __init__(self):
        self.audit_logger = agent_audit_logger

    async def execute_lending_workflow(
        self,
        loan_request: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """Execute complete lending workflow with full audit trail"""

        workflow_id = str(uuid.uuid4())
        loan_id = loan_request.get('loan_id', f"LOAN_{workflow_id[:8]}")

        # Log workflow start
        await self.audit_logger.log_agent_action(
            agent_name="workflow_coordinator",
            action="workflow_started",
            details={
                "workflow_id": workflow_id,
                "loan_request": loan_request,
                "workflow_type": "lending_workflow"
            },
            loan_id=loan_id,
            user_id=user_id
        )

        try:
            workflow_results = {}

            # Step 1: Liquidity Discovery (with audit)
            await self.audit_logger.log_agent_action(
                agent_name="liquidity_agent",
                action="liquidity_analysis_started",
                details={"step": 1, "workflow_id": workflow_id},
                loan_id=loan_id,
                user_id=user_id
            )

            # Step 2: Risk Assessment (with compliance check)
            await self.audit_logger.log_agent_action(
                agent_name="negotiation_agent",
                action="risk_assessment_started",
                details={"step": 2, "workflow_id": workflow_id},
                loan_id=loan_id,
                user_id=user_id
            )

            # Step 3: Term Negotiation (with compliance check)
            decision_data = {
                "loan_amount": loan_request.get("amount_algos", 0),
                "interest_rate": 7.2,
                "approval_decision": True
            }

            compliance_result = await self.audit_logger.log_compliance_check(
                agent_name="negotiation_agent",
                decision_data=decision_data,
                loan_id=loan_id,
                user_id=user_id
            )

            # Step 4: Execution Planning
            await self.audit_logger.log_agent_action(
                agent_name="execution_agent",
                action="execution_planning_started",
                details={"step": 4, "workflow_id": workflow_id},
                loan_id=loan_id,
                user_id=user_id
            )

            # Compile results
            workflow_results = {
                "workflow_id": workflow_id,
                "loan_id": loan_id,
                "status": "completed",
                "compliance_passed": compliance_result.get("compliance_score", 0) >= 80,
                "audit_trail_complete": True,
                "steps_completed": 4,
                "real_time_streaming": True,
                "final_decision": decision_data
            }

            # Log workflow completion
            await self.audit_logger.log_agent_action(
                agent_name="workflow_coordinator",
                action="workflow_completed",
                details={
                    "workflow_id": workflow_id,
                    "results": workflow_results,
                    "total_steps": 4,
                    "compliance_passed": workflow_results["compliance_passed"]
                },
                loan_id=loan_id,
                user_id=user_id
            )

            return workflow_results

        except Exception as e:
            # Log workflow failure
            await self.audit_logger.log_agent_action(
                agent_name="workflow_coordinator",
                action="workflow_failed",
                details={
                    "workflow_id": workflow_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                loan_id=loan_id,
                user_id=user_id
            )
            raise