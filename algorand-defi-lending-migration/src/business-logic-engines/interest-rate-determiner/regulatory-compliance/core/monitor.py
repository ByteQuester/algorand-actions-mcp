"""
Compliance Monitor

Real-time monitoring system for regulatory compliance, tracking changes in
regulations, monitoring loan portfolios, and providing alerts for compliance issues.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from .config import RegulatoryComplianceConfig
from .constants import RegulatoryComplianceConstants, ComplianceLevel
from .validator import ComplianceValidator, ValidationResult, LoanParameters
from .jurisdictions import JurisdictionManager


class MonitoringEvent(Enum):
    """Types of monitoring events"""
    COMPLIANCE_VIOLATION = "compliance_violation"
    REGULATORY_CHANGE = "regulatory_change"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUDIT_REQUIRED = "audit_required"
    LICENSE_EXPIRING = "license_expiring"
    THRESHOLD_BREACH = "threshold_breach"


@dataclass
class ComplianceAlert:
    """Represents a compliance monitoring alert"""
    alert_id: str
    event_type: MonitoringEvent
    severity: ComplianceLevel
    jurisdiction: str
    loan_id: Optional[str]
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution_notes: str = ""
    escalation_required: bool = False


@dataclass
class MonitoredLoan:
    """Represents a loan being monitored for compliance"""
    loan_id: str
    loan_params: LoanParameters
    applicable_jurisdictions: List[str]
    last_validation: Optional[ValidationResult] = None
    last_check: Optional[datetime] = None
    compliance_score: float = 100.0
    active_issues: List[str] = field(default_factory=list)
    monitoring_enabled: bool = True


@dataclass
class RegulatoryUpdate:
    """Represents a regulatory update or change"""
    update_id: str
    jurisdiction: str
    regulation_type: str
    effective_date: datetime
    description: str
    impact_assessment: str
    affected_loan_types: List[str]
    action_required: bool = False


class ComplianceMonitor:
    """
    Real-time compliance monitoring system for lending operations
    """

    def __init__(self, config: RegulatoryComplianceConfig):
        """Initialize the compliance monitor"""
        self.config = config
        self.constants = RegulatoryComplianceConstants()
        self.validator = ComplianceValidator(config)
        self.jurisdiction_manager = JurisdictionManager(config)

        self.logger = logging.getLogger(__name__)

        # Monitoring state
        self._monitored_loans: Dict[str, MonitoredLoan] = {}
        self._active_alerts: Dict[str, ComplianceAlert] = {}
        self._regulatory_updates: List[RegulatoryUpdate] = []
        self._alert_callbacks: List[Callable[[ComplianceAlert], None]] = []

        # Monitoring control
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        self._last_regulatory_check = datetime.now()

        # Statistics
        self._monitoring_stats = {
            'loans_monitored': 0,
            'alerts_generated': 0,
            'violations_detected': 0,
            'last_full_scan': None
        }

    async def start_monitoring(self) -> None:
        """Start the compliance monitoring service"""
        if self._running:
            self.logger.warning("Compliance monitor is already running")
            return

        self._running = True
        self.logger.info("Starting compliance monitoring service")

        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop the compliance monitoring service"""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping compliance monitoring service")

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    def add_loan_to_monitoring(
        self,
        loan_id: str,
        loan_params: LoanParameters,
        jurisdictions: List[str]
    ) -> None:
        """Add a loan to compliance monitoring"""
        monitored_loan = MonitoredLoan(
            loan_id=loan_id,
            loan_params=loan_params,
            applicable_jurisdictions=jurisdictions,
            last_check=datetime.now()
        )

        self._monitored_loans[loan_id] = monitored_loan
        self._monitoring_stats['loans_monitored'] = len(self._monitored_loans)

        self.logger.info(f"Added loan {loan_id} to compliance monitoring")

    def remove_loan_from_monitoring(self, loan_id: str) -> None:
        """Remove a loan from compliance monitoring"""
        if loan_id in self._monitored_loans:
            del self._monitored_loans[loan_id]
            self._monitoring_stats['loans_monitored'] = len(self._monitored_loans)
            self.logger.info(f"Removed loan {loan_id} from compliance monitoring")

    def add_alert_callback(self, callback: Callable[[ComplianceAlert], None]) -> None:
        """Add callback function for compliance alerts"""
        self._alert_callbacks.append(callback)

    async def perform_compliance_check(self, loan_id: str) -> ValidationResult:
        """Perform immediate compliance check for a specific loan"""
        if loan_id not in self._monitored_loans:
            raise ValueError(f"Loan {loan_id} is not being monitored")

        monitored_loan = self._monitored_loans[loan_id]

        # Perform validation
        validation_result = await self.validator.validate_loan_compliance(
            monitored_loan.loan_params,
            monitored_loan.applicable_jurisdictions
        )

        # Update monitoring record
        monitored_loan.last_validation = validation_result
        monitored_loan.last_check = datetime.now()
        monitored_loan.compliance_score = validation_result.overall_score

        # Process any new violations
        await self._process_validation_result(loan_id, validation_result)

        return validation_result

    async def check_regulatory_updates(self) -> List[RegulatoryUpdate]:
        """Check for new regulatory updates"""
        # This would integrate with external regulatory databases
        # For now, we'll simulate checking for updates

        new_updates = []

        # Check if it's time for regulatory update check
        time_since_check = datetime.now() - self._last_regulatory_check
        if time_since_check.total_seconds() < self.config.integration.legal_update_check_hours * 3600:
            return new_updates

        # Simulate regulatory update detection
        # In practice, this would query regulatory APIs or databases
        self._last_regulatory_check = datetime.now()

        # Example: Detect rate changes
        for jurisdiction_code in self.config.get_applicable_jurisdictions():
            # Simulate checking for rate limit changes
            # This would be replaced with actual API calls
            pass

        self.logger.info(f"Checked for regulatory updates. Found {len(new_updates)} new updates.")
        return new_updates

    async def generate_compliance_report(
        self,
        include_resolved_alerts: bool = False,
        jurisdiction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        report_data = {
            'report_timestamp': datetime.now().isoformat(),
            'monitoring_summary': self._monitoring_stats.copy(),
            'loan_portfolio_summary': {},
            'active_alerts': [],
            'compliance_trends': {},
            'regulatory_updates': [],
            'recommendations': []
        }

        # Loan portfolio summary
        total_loans = len(self._monitored_loans)
        compliant_loans = sum(1 for loan in self._monitored_loans.values()
                            if loan.compliance_score >= 70)

        avg_score = (sum(loan.compliance_score for loan in self._monitored_loans.values()) /
                    total_loans if total_loans > 0 else 0)

        report_data['loan_portfolio_summary'] = {
            'total_loans_monitored': total_loans,
            'compliant_loans': compliant_loans,
            'non_compliant_loans': total_loans - compliant_loans,
            'average_compliance_score': avg_score,
            'compliance_rate': (compliant_loans / total_loans * 100) if total_loans > 0 else 0
        }

        # Active alerts
        active_alerts = [alert for alert in self._active_alerts.values()
                        if not alert.resolved]

        if include_resolved_alerts:
            active_alerts.extend([alert for alert in self._active_alerts.values()
                                if alert.resolved])

        if jurisdiction:
            active_alerts = [alert for alert in active_alerts
                           if alert.jurisdiction == jurisdiction]

        report_data['active_alerts'] = [
            {
                'alert_id': alert.alert_id,
                'event_type': alert.event_type.value,
                'severity': alert.severity.value,
                'jurisdiction': alert.jurisdiction,
                'description': alert.description,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved
            }
            for alert in active_alerts
        ]

        # Compliance trends (last 30 days)
        report_data['compliance_trends'] = await self._calculate_compliance_trends()

        # Recent regulatory updates
        recent_updates = [update for update in self._regulatory_updates
                         if (datetime.now() - update.effective_date).days <= 30]
        report_data['regulatory_updates'] = [
            {
                'update_id': update.update_id,
                'jurisdiction': update.jurisdiction,
                'regulation_type': update.regulation_type,
                'effective_date': update.effective_date.isoformat(),
                'description': update.description,
                'action_required': update.action_required
            }
            for update in recent_updates
        ]

        # Generate recommendations
        report_data['recommendations'] = await self._generate_compliance_recommendations()

        return report_data

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                # Check for regulatory updates
                if self.config.monitoring.enable_real_time_monitoring:
                    await self.check_regulatory_updates()

                # Monitor active loans
                await self._monitor_active_loans()

                # Clean up old alerts
                await self._cleanup_old_alerts()

                # Sleep until next monitoring cycle
                await asyncio.sleep(self.config.monitoring.monitoring_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _monitor_active_loans(self) -> None:
        """Monitor all active loans for compliance"""
        if not self._monitored_loans:
            return

        self.logger.debug(f"Monitoring {len(self._monitored_loans)} loans for compliance")

        # Check each loan
        for loan_id, monitored_loan in self._monitored_loans.items():
            if not monitored_loan.monitoring_enabled:
                continue

            try:
                # Determine if loan needs checking
                if self._needs_compliance_check(monitored_loan):
                    await self.perform_compliance_check(loan_id)

            except Exception as e:
                self.logger.error(f"Error monitoring loan {loan_id}: {e}")

        self._monitoring_stats['last_full_scan'] = datetime.now()

    def _needs_compliance_check(self, monitored_loan: MonitoredLoan) -> bool:
        """Determine if a loan needs compliance checking"""
        if not monitored_loan.last_check:
            return True

        # Check if enough time has passed since last check
        time_since_check = datetime.now() - monitored_loan.last_check
        check_interval = timedelta(seconds=self.config.monitoring.monitoring_interval_seconds)

        return time_since_check >= check_interval

    async def _process_validation_result(
        self,
        loan_id: str,
        validation_result: ValidationResult
    ) -> None:
        """Process validation result and generate alerts if needed"""
        monitored_loan = self._monitored_loans[loan_id]

        # Check for new violations
        current_violations = set(issue.issue_id for issue in validation_result.issues
                               if issue.severity.value in ['error', 'critical'])

        previous_violations = set(monitored_loan.active_issues)

        # New violations
        new_violations = current_violations - previous_violations
        for violation_id in new_violations:
            issue = next(issue for issue in validation_result.issues
                        if issue.issue_id == violation_id)
            await self._create_compliance_alert(loan_id, issue)

        # Resolved violations
        resolved_violations = previous_violations - current_violations
        for violation_id in resolved_violations:
            await self._resolve_compliance_alert(loan_id, violation_id)

        # Update active issues
        monitored_loan.active_issues = list(current_violations)

    async def _create_compliance_alert(self, loan_id: str, issue) -> None:
        """Create a compliance alert"""
        alert = ComplianceAlert(
            alert_id=f"{loan_id}_{issue.issue_id}_{datetime.now().isoformat()}",
            event_type=MonitoringEvent.COMPLIANCE_VIOLATION,
            severity=ComplianceLevel.CRITICAL if issue.severity.value == 'critical' else ComplianceLevel.VIOLATION,
            jurisdiction=issue.jurisdiction,
            loan_id=loan_id,
            description=issue.description,
            details={
                'issue_type': issue.issue_type,
                'rule_reference': issue.rule_reference,
                'current_value': issue.current_value,
                'limit_value': issue.limit_value,
                'remediation_suggestion': issue.remediation_suggestion
            },
            timestamp=datetime.now(),
            escalation_required=issue.severity.value == 'critical'
        )

        self._active_alerts[alert.alert_id] = alert
        self._monitoring_stats['alerts_generated'] += 1
        self._monitoring_stats['violations_detected'] += 1

        # Notify callbacks
        await self._notify_alert_callbacks(alert)

        self.logger.warning(f"Created compliance alert: {alert.description}")

    async def _resolve_compliance_alert(self, loan_id: str, violation_id: str) -> None:
        """Resolve a compliance alert"""
        # Find and resolve matching alerts
        for alert_id, alert in self._active_alerts.items():
            if alert.loan_id == loan_id and violation_id in alert_id:
                alert.resolved = True
                alert.resolution_notes = "Issue automatically resolved"
                self.logger.info(f"Resolved compliance alert: {alert.description}")
                break

    async def _notify_alert_callbacks(self, alert: ComplianceAlert) -> None:
        """Notify all registered alert callbacks"""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

    async def _cleanup_old_alerts(self) -> None:
        """Clean up old resolved alerts"""
        cutoff_date = datetime.now() - timedelta(days=self.config.audit.audit_retention_years * 365)

        alerts_to_remove = []
        for alert_id, alert in self._active_alerts.items():
            if alert.resolved and alert.timestamp < cutoff_date:
                alerts_to_remove.append(alert_id)

        for alert_id in alerts_to_remove:
            del self._active_alerts[alert_id]

        if alerts_to_remove:
            self.logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts")

    async def _calculate_compliance_trends(self) -> Dict[str, Any]:
        """Calculate compliance trends over time"""
        # This would typically involve historical data analysis
        # For now, we'll provide current snapshot trends

        trends = {
            'average_compliance_score_trend': 'stable',
            'violation_rate_trend': 'decreasing',
            'most_common_violations': [],
            'jurisdiction_compliance_rates': {}
        }

        # Analyze most common violations
        violation_counts = {}
        for alert in self._active_alerts.values():
            if alert.event_type == MonitoringEvent.COMPLIANCE_VIOLATION:
                violation_type = alert.details.get('issue_type', 'unknown')
                violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1

        trends['most_common_violations'] = [
            {'type': vtype, 'count': count}
            for vtype, count in sorted(violation_counts.items(),
                                     key=lambda x: x[1], reverse=True)[:5]
        ]

        # Calculate jurisdiction compliance rates
        jurisdiction_scores = {}
        for loan in self._monitored_loans.values():
            for jurisdiction in loan.applicable_jurisdictions:
                if jurisdiction not in jurisdiction_scores:
                    jurisdiction_scores[jurisdiction] = []
                jurisdiction_scores[jurisdiction].append(loan.compliance_score)

        for jurisdiction, scores in jurisdiction_scores.items():
            trends['jurisdiction_compliance_rates'][jurisdiction] = {
                'average_score': sum(scores) / len(scores) if scores else 0,
                'loan_count': len(scores)
            }

        return trends

    async def _generate_compliance_recommendations(self) -> List[str]:
        """Generate compliance recommendations based on monitoring data"""
        recommendations = []

        # Analyze common issues
        issue_types = {}
        for alert in self._active_alerts.values():
            if not alert.resolved:
                issue_type = alert.details.get('issue_type', 'unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        # Generate recommendations based on common issues
        if issue_types.get('usury_violation', 0) > 0:
            recommendations.append(
                "Review interest rate policies to ensure compliance with usury laws"
            )

        if issue_types.get('fee_violation', 0) > 0:
            recommendations.append(
                "Audit fee structure to ensure compliance with regulatory limits"
            )

        if issue_types.get('predatory_lending', 0) > 0:
            recommendations.append(
                "Implement stronger consumer protection measures and ability-to-repay verification"
            )

        # Check compliance scores
        low_score_count = sum(1 for loan in self._monitored_loans.values()
                            if loan.compliance_score < 70)

        if low_score_count > len(self._monitored_loans) * 0.1:  # More than 10% non-compliant
            recommendations.append(
                "Conduct comprehensive review of lending policies and procedures"
            )

        # Check for regulatory updates
        pending_updates = [update for update in self._regulatory_updates
                         if update.action_required and
                         update.effective_date > datetime.now()]

        if pending_updates:
            recommendations.append(
                f"Prepare for {len(pending_updates)} upcoming regulatory changes"
            )

        return recommendations

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        return {
            **self._monitoring_stats,
            'active_alerts': len([alert for alert in self._active_alerts.values()
                                if not alert.resolved]),
            'resolved_alerts': len([alert for alert in self._active_alerts.values()
                                  if alert.resolved]),
            'monitoring_status': 'running' if self._running else 'stopped'
        }