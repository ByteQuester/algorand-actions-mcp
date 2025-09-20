"""
Monitoring Scheduler for Holistic Loan Decisions

Schedules ongoing monitoring activities and risk assessment updates
based on loan terms, borrower profile, and market conditions.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from .decision_orchestrator import BorrowerProfile, LoanApplication, HolisticDecision, LoanDecision


class MonitoringFrequency(Enum):
    """Monitoring frequency options"""
    REAL_TIME = "real-time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ON_DEMAND = "on-demand"


class MonitoringParameter(Enum):
    """Parameters to monitor"""
    COLLATERAL_VALUE = "collateral_value"
    LTV_RATIO = "ltv_ratio"
    PAYMENT_STATUS = "payment_status"
    ECOSYSTEM_ACTIVITY = "ecosystem_activity"
    DEFI_POSITIONS = "defi_positions"
    GOVERNANCE_PARTICIPATION = "governance_participation"
    MARKET_CONDITIONS = "market_conditions"
    NETWORK_HEALTH = "network_health"
    COUNTERPARTY_RISK = "counterparty_risk"
    LIQUIDITY_STATUS = "liquidity_status"


@dataclass
class MonitoringTask:
    """Individual monitoring task"""
    parameter: MonitoringParameter
    frequency: MonitoringFrequency
    threshold: Optional[float]
    alert_conditions: List[str]
    auto_actions: List[str]
    priority: int  # 1 = highest, 5 = lowest


@dataclass
class MonitoringSchedule:
    """Complete monitoring schedule for a loan"""
    loan_id: str
    borrower_address: str
    monitoring_tasks: List[MonitoringTask]
    escalation_triggers: Dict[str, Any]
    review_schedule: List[datetime]
    emergency_contacts: List[str]


class MonitoringScheduler:
    """
    Creates comprehensive monitoring schedules for approved loans.

    Determines monitoring frequency, parameters, and escalation procedures
    based on risk assessment and loan characteristics.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
        self.logger = logging.getLogger("monitoring_scheduler")

        # Alert thresholds from config
        self.alert_thresholds = self.monitoring_config.get('alert_thresholds', {})

    async def schedule_monitoring(
        self,
        decision_result: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Dict[str, Any]:
        """
        Create comprehensive monitoring schedule for approved loan.

        Returns monitoring configuration with frequencies and parameters.
        """

        if decision_result['decision'] == LoanDecision.REJECTED:
            return self._create_minimal_monitoring()

        self.logger.info(f"Creating monitoring schedule for application {application.application_id}")

        # Determine base monitoring level
        monitoring_level = self._determine_monitoring_level(decision_result, profile)

        # Create monitoring tasks
        monitoring_tasks = self._create_monitoring_tasks(
            monitoring_level, decision_result, application, profile
        )

        # Set up escalation triggers
        escalation_triggers = self._create_escalation_triggers(
            decision_result, application, profile
        )

        # Schedule regular reviews
        review_schedule = self._create_review_schedule(
            decision_result, application, profile
        )

        # Compile monitoring response
        return {
            'frequency': monitoring_level['base_frequency'],
            'parameters': [task.parameter.value for task in monitoring_tasks],
            'monitoring_tasks': [
                {
                    'parameter': task.parameter.value,
                    'frequency': task.frequency.value,
                    'threshold': task.threshold,
                    'alert_conditions': task.alert_conditions,
                    'auto_actions': task.auto_actions,
                    'priority': task.priority
                }
                for task in monitoring_tasks
            ],
            'escalation_triggers': escalation_triggers,
            'review_dates': [date.isoformat() for date in review_schedule],
            'monitoring_metadata': {
                'monitoring_level': monitoring_level['level'],
                'risk_score': decision_result.get('risk_score', 0),
                'confidence': decision_result.get('confidence', 'medium'),
                'created_at': datetime.now().isoformat()
            }
        }

    def _determine_monitoring_level(
        self,
        decision_result: Dict[str, Any],
        profile: BorrowerProfile
    ) -> Dict[str, Any]:
        """
        Determine appropriate monitoring level based on risk assessment.
        """

        risk_score = decision_result.get('risk_score', 0.5)
        overall_score = decision_result.get('overall_score', 0.5)
        confidence = decision_result.get('confidence', 'medium')

        # Base monitoring frequency
        if risk_score >= 0.7 or overall_score < 0.4:
            level = "intensive"
            base_frequency = MonitoringFrequency.DAILY
        elif risk_score >= 0.5 or overall_score < 0.6:
            level = "enhanced"
            base_frequency = MonitoringFrequency.WEEKLY
        elif risk_score >= 0.3 or overall_score < 0.8:
            level = "standard"
            base_frequency = MonitoringFrequency.WEEKLY
        else:
            level = "minimal"
            base_frequency = MonitoringFrequency.MONTHLY

        # Adjust for confidence level
        if confidence in ['low', 'very_low']:
            if level == "minimal":
                level = "standard"
                base_frequency = MonitoringFrequency.WEEKLY
            elif level == "standard":
                level = "enhanced"

        return {
            'level': level,
            'base_frequency': base_frequency,
            'risk_score': risk_score,
            'overall_score': overall_score,
            'confidence': confidence
        }

    def _create_monitoring_tasks(
        self,
        monitoring_level: Dict[str, Any],
        decision_result: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[MonitoringTask]:
        """
        Create specific monitoring tasks based on risk profile.
        """

        tasks = []
        level = monitoring_level['level']
        base_frequency = monitoring_level['base_frequency']

        # 1. Collateral monitoring (always required)
        tasks.append(MonitoringTask(
            parameter=MonitoringParameter.COLLATERAL_VALUE,
            frequency=MonitoringFrequency.REAL_TIME if level == "intensive" else MonitoringFrequency.DAILY,
            threshold=self.alert_thresholds.get('ltv_warning', 0.75),
            alert_conditions=[
                "Collateral value drops below warning threshold",
                "Single asset concentration > 50%",
                "Liquidity score drops below 0.7"
            ],
            auto_actions=[
                "Send margin call notification",
                "Request additional collateral",
                "Escalate to risk management"
            ],
            priority=1
        ))

        # 2. LTV ratio monitoring
        tasks.append(MonitoringTask(
            parameter=MonitoringParameter.LTV_RATIO,
            frequency=MonitoringFrequency.REAL_TIME if level == "intensive" else MonitoringFrequency.DAILY,
            threshold=self.alert_thresholds.get('ltv_liquidation', 0.85),
            alert_conditions=[
                "LTV ratio exceeds warning threshold",
                "LTV ratio approaching liquidation threshold",
                "Rapid LTV deterioration"
            ],
            auto_actions=[
                "Trigger margin call",
                "Initiate liquidation procedures if threshold breached",
                "Lock additional borrowing"
            ],
            priority=1
        ))

        # 3. Payment status monitoring
        tasks.append(MonitoringTask(
            parameter=MonitoringParameter.PAYMENT_STATUS,
            frequency=MonitoringFrequency.DAILY,
            threshold=None,
            alert_conditions=[
                "Payment overdue by 1 day",
                "Partial payment received",
                "Payment from unusual source"
            ],
            auto_actions=[
                "Send payment reminder",
                "Apply late fees if applicable",
                "Escalate after 5 days overdue"
            ],
            priority=2
        ))

        # 4. Ecosystem activity monitoring
        ecosystem_frequency = base_frequency
        if profile.ecosystem_score < 0.5:
            ecosystem_frequency = MonitoringFrequency.WEEKLY

        tasks.append(MonitoringTask(
            parameter=MonitoringParameter.ECOSYSTEM_ACTIVITY,
            frequency=ecosystem_frequency,
            threshold=0.4,  # Minimum ecosystem score
            alert_conditions=[
                "Significant decrease in ecosystem participation",
                "Wallet inactivity for extended period",
                "Suspicious transaction patterns"
            ],
            auto_actions=[
                "Request borrower update",
                "Review risk assessment",
                "Consider early intervention"
            ],
            priority=3
        ))

        # 5. DeFi positions monitoring (if applicable)
        if profile.defi_score > 0:
            defi_frequency = MonitoringFrequency.DAILY if level in ["intensive", "enhanced"] else MonitoringFrequency.WEEKLY

            tasks.append(MonitoringTask(
                parameter=MonitoringParameter.DEFI_POSITIONS,
                frequency=defi_frequency,
                threshold=None,
                alert_conditions=[
                    "High-risk DeFi strategy deployment",
                    "Excessive leverage usage",
                    "Smart contract interaction failures"
                ],
                auto_actions=[
                    "Review DeFi strategy",
                    "Request position disclosure",
                    "Apply behavioral restrictions if needed"
                ],
                priority=2 if level == "intensive" else 3
            ))

        # 6. Governance participation monitoring
        if profile.governance_score > 0:
            tasks.append(MonitoringTask(
                parameter=MonitoringParameter.GOVERNANCE_PARTICIPATION,
                frequency=MonitoringFrequency.MONTHLY,
                threshold=None,
                alert_conditions=[
                    "Cessation of governance participation",
                    "Voting pattern changes",
                    "Community standing deterioration"
                ],
                auto_actions=[
                    "Note participation changes",
                    "Adjust governance incentives",
                    "Update reputation scoring"
                ],
                priority=4
            ))

        # 7. Market conditions monitoring
        tasks.append(MonitoringTask(
            parameter=MonitoringParameter.MARKET_CONDITIONS,
            frequency=MonitoringFrequency.HOURLY if level == "intensive" else MonitoringFrequency.DAILY,
            threshold=self.alert_thresholds.get('price_volatility', 0.20),
            alert_conditions=[
                "High market volatility detected",
                "Significant price drops in collateral assets",
                "Liquidity crisis indicators"
            ],
            auto_actions=[
                "Increase monitoring frequency",
                "Review all loan positions",
                "Prepare contingency measures"
            ],
            priority=2
        ))

        # 8. Network health monitoring
        tasks.append(MonitoringTask(
            parameter=MonitoringParameter.NETWORK_HEALTH,
            frequency=MonitoringFrequency.DAILY,
            threshold=0.8,  # Minimum network health score
            alert_conditions=[
                "Network health degradation",
                "Consensus issues",
                "Protocol upgrade risks"
            ],
            auto_actions=[
                "Monitor network status",
                "Assess systemic risks",
                "Communicate with borrowers if needed"
            ],
            priority=3
        ))

        # Additional tasks for high-risk loans
        if level == "intensive":
            # Counterparty risk monitoring
            tasks.append(MonitoringTask(
                parameter=MonitoringParameter.COUNTERPARTY_RISK,
                frequency=MonitoringFrequency.DAILY,
                threshold=None,
                alert_conditions=[
                    "Counterparty credit downgrades",
                    "Related party transaction risks",
                    "Concentration risk increases"
                ],
                auto_actions=[
                    "Review counterparty exposure",
                    "Assess contagion risks",
                    "Consider position limits"
                ],
                priority=2
            ))

            # Liquidity status monitoring
            tasks.append(MonitoringTask(
                parameter=MonitoringParameter.LIQUIDITY_STATUS,
                frequency=MonitoringFrequency.REAL_TIME,
                threshold=0.6,  # Minimum liquidity score
                alert_conditions=[
                    "Liquidity shortage indicators",
                    "Market making disruptions",
                    "Slippage increases"
                ],
                auto_actions=[
                    "Alert liquidity team",
                    "Review liquidation procedures",
                    "Consider position adjustments"
                ],
                priority=1
            ))

        return tasks

    def _create_escalation_triggers(
        self,
        decision_result: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> Dict[str, Any]:
        """
        Create escalation triggers for various risk scenarios.
        """

        return {
            'ltv_triggers': {
                'warning_level': 0.75,
                'critical_level': 0.85,
                'liquidation_level': 0.90,
                'actions': {
                    'warning': ['notify_borrower', 'increase_monitoring'],
                    'critical': ['margin_call', 'restrict_withdrawals'],
                    'liquidation': ['initiate_liquidation', 'notify_legal']
                }
            },
            'payment_triggers': {
                'grace_period_days': 5,
                'default_days': 30,
                'actions': {
                    'late': ['late_fee', 'payment_reminder'],
                    'default': ['acceleration_notice', 'legal_action'],
                    'cure': ['reinstate_loan', 'update_terms']
                }
            },
            'ecosystem_triggers': {
                'score_degradation_threshold': 0.20,  # 20% drop in ecosystem score
                'inactivity_days': 90,
                'actions': {
                    'degradation': ['review_terms', 'request_explanation'],
                    'inactivity': ['wellness_check', 'consider_early_review']
                }
            },
            'market_triggers': {
                'volatility_threshold': 0.30,  # 30% volatility
                'systemic_risk_level': 'high',
                'actions': {
                    'high_volatility': ['daily_monitoring', 'stress_test'],
                    'systemic_risk': ['freeze_new_loans', 'review_all_positions']
                }
            },
            'technical_triggers': {
                'smart_contract_failure': True,
                'oracle_failure': True,
                'network_congestion': True,
                'actions': {
                    'technical_failure': ['manual_override', 'emergency_procedures'],
                    'oracle_issues': ['use_backup_feeds', 'manual_pricing'],
                    'network_issues': ['delay_liquidations', 'extend_grace_periods']
                }
            }
        }

    def _create_review_schedule(
        self,
        decision_result: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[datetime]:
        """
        Create schedule for formal loan reviews.
        """

        review_dates = []
        loan_start = datetime.now()
        loan_term_days = application.requested_term

        risk_score = decision_result.get('risk_score', 0.5)

        # Determine review frequency
        if risk_score >= 0.7:
            review_interval_days = 30  # Monthly reviews
        elif risk_score >= 0.5:
            review_interval_days = 60  # Bi-monthly reviews
        else:
            review_interval_days = 90  # Quarterly reviews

        # Schedule reviews throughout loan term
        current_date = loan_start + timedelta(days=review_interval_days)
        while current_date < loan_start + timedelta(days=loan_term_days):
            review_dates.append(current_date)
            current_date += timedelta(days=review_interval_days)

        # Always include mid-term review
        mid_term_date = loan_start + timedelta(days=loan_term_days // 2)
        if mid_term_date not in review_dates:
            review_dates.append(mid_term_date)

        # Add final review before maturity
        final_review_date = loan_start + timedelta(days=loan_term_days - 30)
        if final_review_date not in review_dates:
            review_dates.append(final_review_date)

        return sorted(review_dates)

    def _create_minimal_monitoring(self) -> Dict[str, Any]:
        """Create minimal monitoring for rejected applications"""
        return {
            'frequency': 'none',
            'parameters': [],
            'monitoring_tasks': [],
            'escalation_triggers': {},
            'review_dates': [],
            'monitoring_metadata': {
                'monitoring_level': 'none',
                'reason': 'application_rejected'
            }
        }

    def update_monitoring_schedule(
        self,
        loan_id: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update monitoring schedule based on loan performance.
        """

        self.logger.info(f"Updating monitoring schedule for loan {loan_id}")

        # Analyze performance trends
        payment_history = performance_data.get('payment_history', [])
        collateral_stability = performance_data.get('collateral_stability', 0.5)
        borrower_behavior = performance_data.get('borrower_behavior', {})

        # Determine if monitoring should be adjusted
        if self._is_performing_well(payment_history, collateral_stability, borrower_behavior):
            adjustment = "reduce_frequency"
        elif self._has_concerning_patterns(payment_history, collateral_stability, borrower_behavior):
            adjustment = "increase_frequency"
        else:
            adjustment = "maintain"

        return {
            'adjustment': adjustment,
            'rationale': self._get_adjustment_rationale(performance_data),
            'new_frequency': self._calculate_new_frequency(adjustment),
            'updated_at': datetime.now().isoformat()
        }

    def _is_performing_well(self, payment_history, collateral_stability, borrower_behavior) -> bool:
        """Determine if loan is performing well"""
        on_time_payments = len([p for p in payment_history if p.get('on_time', False)])
        total_payments = len(payment_history)

        return (
            total_payments > 0 and
            on_time_payments / total_payments >= 0.95 and
            collateral_stability >= 0.8 and
            borrower_behavior.get('ecosystem_score_trend', 0) >= 0
        )

    def _has_concerning_patterns(self, payment_history, collateral_stability, borrower_behavior) -> bool:
        """Determine if there are concerning patterns"""
        late_payments = len([p for p in payment_history if not p.get('on_time', True)])
        total_payments = len(payment_history)

        return (
            (total_payments > 0 and late_payments / total_payments > 0.1) or
            collateral_stability < 0.6 or
            borrower_behavior.get('ecosystem_score_trend', 0) < -0.1
        )

    def _get_adjustment_rationale(self, performance_data) -> str:
        """Get rationale for monitoring adjustment"""
        # Implementation would analyze specific performance indicators
        return "Performance analysis indicates monitoring adjustment needed"

    def _calculate_new_frequency(self, adjustment) -> str:
        """Calculate new monitoring frequency"""
        frequency_map = {
            "reduce_frequency": "monthly",
            "maintain": "weekly",
            "increase_frequency": "daily"
        }
        return frequency_map.get(adjustment, "weekly")