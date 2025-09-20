"""
Liquidation Monitoring System
Monitors escrow contracts and triggers automatic liquidation
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass

from .models import (
    EscrowContract, EscrowStatus, TriggerStatus,
    LiquidationTrigger, EscrowMonitoringConfig,
    EscrowEvent, LiquidationRequest
)
from .escrow_service import EscrowService
from .mcp_integration import MCPBlockchainClient, MCPConfig

logger = logging.getLogger(__name__)

@dataclass
class MonitoringResult:
    """Result of monitoring check"""
    escrow_id: str
    check_time: datetime
    triggers_checked: int
    triggers_fired: int
    action_taken: Optional[str] = None
    error: Optional[str] = None

class LiquidationMonitor:
    """
    Automated monitoring system for escrow liquidation triggers
    Runs periodic checks and executes liquidations when conditions are met
    """

    def __init__(
        self,
        escrow_service: EscrowService,
        config: Optional[EscrowMonitoringConfig] = None
    ):
        """Initialize liquidation monitor"""
        self.escrow_service = escrow_service
        self.config = config or EscrowMonitoringConfig()
        self.mcp_config = MCPConfig()
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_results: List[MonitoringResult] = []
        self.alert_handlers: List[Any] = []

    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self.is_running:
            logger.warning("Monitoring already running")
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started liquidation monitoring (interval: {self.config.check_interval_seconds}s)")

    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped liquidation monitoring")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Check all active escrows
                await self._check_all_escrows()

                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval_seconds)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)  # Brief pause before retry

    async def _check_all_escrows(self):
        """Check all escrows for liquidation conditions"""
        active_escrows = self._get_active_escrows()

        for escrow in active_escrows:
            try:
                result = await self._check_escrow(escrow)
                self.monitoring_results.append(result)

                # Keep only recent results (last 24 hours)
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.monitoring_results = [
                    r for r in self.monitoring_results
                    if r.check_time > cutoff
                ]

            except Exception as e:
                logger.error(f"Error checking escrow {escrow.escrow_id}: {e}")

    async def _check_escrow(self, escrow: EscrowContract) -> MonitoringResult:
        """Check a single escrow for liquidation conditions"""
        result = MonitoringResult(
            escrow_id=escrow.escrow_id,
            check_time=datetime.utcnow(),
            triggers_checked=0,
            triggers_fired=0
        )

        try:
            # Check each liquidation trigger
            for trigger in escrow.liquidation_triggers:
                result.triggers_checked += 1

                if await self._evaluate_trigger(escrow, trigger):
                    result.triggers_fired += 1
                    trigger.status = TriggerStatus.TRIGGERED
                    trigger.triggered_at = datetime.utcnow()

                    # Send alert
                    await self._send_alert(escrow, trigger, "TRIGGER_ACTIVATED")

            # Execute liquidation if triggers fired and auto-liquidation enabled
            if result.triggers_fired > 0 and self.config.enable_auto_liquidation:
                success = await self._execute_auto_liquidation(escrow)
                result.action_taken = "AUTO_LIQUIDATION" if success else "LIQUIDATION_FAILED"

                # Send liquidation alert
                await self._send_alert(
                    escrow,
                    None,
                    "AUTO_LIQUIDATION_EXECUTED" if success else "AUTO_LIQUIDATION_FAILED"
                )

            # Check for warnings
            elif await self._check_warning_conditions(escrow):
                await self._send_alert(escrow, None, "LIQUIDATION_WARNING")

        except Exception as e:
            logger.error(f"Error evaluating escrow {escrow.escrow_id}: {e}")
            result.error = str(e)

        return result

    async def _evaluate_trigger(
        self,
        escrow: EscrowContract,
        trigger: LiquidationTrigger
    ) -> bool:
        """Evaluate if a liquidation trigger should fire"""

        # Skip already triggered
        if trigger.status in [TriggerStatus.TRIGGERED, TriggerStatus.EXECUTED]:
            return False

        if trigger.trigger_type == "time_based":
            return await self._check_time_trigger(escrow, trigger)

        elif trigger.trigger_type == "price_based":
            return await self._check_price_trigger(escrow, trigger)

        elif trigger.trigger_type == "payment_default":
            return await self._check_payment_trigger(escrow, trigger)

        return False

    async def _check_time_trigger(
        self,
        escrow: EscrowContract,
        trigger: LiquidationTrigger
    ) -> bool:
        """Check time-based liquidation trigger"""

        if not escrow.locked_until:
            return False

        days_overdue = trigger.condition.get("days_overdue", 0)
        grace_period = trigger.condition.get("grace_period_hours", 0)

        deadline = escrow.locked_until + timedelta(
            days=days_overdue,
            hours=grace_period
        )

        current_time = datetime.utcnow()
        trigger.current_value = (current_time - escrow.locked_until).days

        return current_time > deadline

    async def _check_price_trigger(
        self,
        escrow: EscrowContract,
        trigger: LiquidationTrigger
    ) -> bool:
        """Check price-based liquidation trigger"""

        try:
            # Get current collateral value (would integrate with price oracle)
            async with MCPBlockchainClient(self.mcp_config) as mcp_client:
                balance_result = await mcp_client.get_escrow_balance(escrow.escrow_address)

                if not balance_result.get("success"):
                    return False

                current_collateral = balance_result.get("balance", 0)

            # Calculate collateralization ratio
            if escrow.loan_amount == 0:
                return False

            current_ratio = current_collateral / escrow.loan_amount
            trigger.current_value = current_ratio

            threshold = trigger.condition.get("collateral_ratio_threshold", 1.5)
            trigger.threshold_value = threshold

            return current_ratio < threshold

        except Exception as e:
            logger.error(f"Price check failed: {e}")
            return False

    async def _check_payment_trigger(
        self,
        escrow: EscrowContract,
        trigger: LiquidationTrigger
    ) -> bool:
        """Check payment default trigger"""

        # This would integrate with payment tracking system
        # For now, check if past due date
        if not escrow.locked_until:
            return False

        return datetime.utcnow() > escrow.locked_until

    async def _check_warning_conditions(self, escrow: EscrowContract) -> bool:
        """Check if warning should be sent"""

        if not escrow.locked_until:
            return False

        warning_time = escrow.locked_until - timedelta(
            hours=self.config.liquidation_warning_hours
        )

        return datetime.utcnow() > warning_time

    async def _execute_auto_liquidation(self, escrow: EscrowContract) -> bool:
        """Execute automatic liquidation"""

        try:
            logger.info(f"Executing auto-liquidation for escrow {escrow.escrow_id}")

            # Prepare liquidation request
            triggered_triggers = [
                t for t in escrow.liquidation_triggers
                if t.status == TriggerStatus.TRIGGERED
            ]

            evidence = {
                "triggers": [
                    {
                        "id": t.trigger_id,
                        "type": t.trigger_type,
                        "condition": t.condition,
                        "triggered_at": t.triggered_at.isoformat() if t.triggered_at else None
                    }
                    for t in triggered_triggers
                ],
                "monitoring_timestamp": datetime.utcnow().isoformat(),
                "auto_liquidation": True
            }

            request = LiquidationRequest(
                escrow_id=escrow.escrow_id,
                reason="Automatic liquidation - triggers activated",
                evidence=evidence,
                requestor="liquidation_monitor",
                force=True  # Override manual checks since we've verified
            )

            # Execute liquidation
            result = await self.escrow_service.liquidate_escrow(request)

            if result.success:
                logger.info(f"Auto-liquidation successful: {result.transaction_id}")

                # Update trigger status
                for trigger in triggered_triggers:
                    trigger.status = TriggerStatus.EXECUTED

                # Add audit entry
                escrow.add_audit_entry(
                    action="AUTO_LIQUIDATION",
                    details={
                        "transaction_id": result.transaction_id,
                        "triggers": len(triggered_triggers)
                    },
                    actor="liquidation_monitor"
                )

                return True
            else:
                logger.error(f"Auto-liquidation failed: {result.error_message}")
                return False

        except Exception as e:
            logger.error(f"Auto-liquidation execution error: {e}")
            return False

    async def _send_alert(
        self,
        escrow: EscrowContract,
        trigger: Optional[LiquidationTrigger],
        alert_type: str
    ):
        """Send alert to registered handlers"""

        alert = {
            "alert_id": str(uuid.uuid4()),
            "alert_type": alert_type,
            "escrow_id": escrow.escrow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "escrow_data": {
                "borrower": escrow.borrower,
                "lender": escrow.lender,
                "loan_amount": escrow.loan_amount,
                "collateral_amount": escrow.collateral_amount,
                "locked_until": escrow.locked_until.isoformat() if escrow.locked_until else None
            }
        }

        if trigger:
            alert["trigger_data"] = {
                "trigger_id": trigger.trigger_id,
                "trigger_type": trigger.trigger_type,
                "condition": trigger.condition,
                "current_value": trigger.current_value,
                "threshold_value": trigger.threshold_value
            }

        # Emit event
        event = EscrowEvent(
            event_id=alert["alert_id"],
            escrow_id=escrow.escrow_id,
            event_type=f"ALERT_{alert_type}",
            timestamp=datetime.utcnow(),
            data=alert
        )

        await self.escrow_service._emit_event(event)

        # Send to alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

    def _get_active_escrows(self) -> List[EscrowContract]:
        """Get list of active escrows to monitor"""
        return [
            escrow for escrow in self.escrow_service.escrow_storage.values()
            if escrow.status in [EscrowStatus.FUNDED, EscrowStatus.ACTIVE]
        ]

    def register_alert_handler(self, handler):
        """Register an alert handler"""
        self.alert_handlers.append(handler)

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        if not self.monitoring_results:
            return {
                "total_checks": 0,
                "total_triggers_fired": 0,
                "auto_liquidations": 0,
                "last_check": None
            }

        return {
            "total_checks": len(self.monitoring_results),
            "total_triggers_fired": sum(r.triggers_fired for r in self.monitoring_results),
            "auto_liquidations": sum(
                1 for r in self.monitoring_results
                if r.action_taken == "AUTO_LIQUIDATION"
            ),
            "last_check": max(r.check_time for r in self.monitoring_results).isoformat(),
            "active_escrows": len(self._get_active_escrows()),
            "monitoring_interval": self.config.check_interval_seconds
        }