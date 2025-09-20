"""
Real-time Risk Monitoring System

Provides continuous monitoring, alerting, and automated response capabilities
for Algorand risk assessment across all engines.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import json
from dataclasses import asdict

from .models import (
    HolisticRiskProfile, RiskAlert, AlertSeverity, RiskLevel,
    MonitoringConfiguration, RiskEngine
)

logger = logging.getLogger(__name__)


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring and alerting system
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.monitored_addresses: Dict[str, MonitoringConfiguration] = {}
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.alert_history: List[RiskAlert] = []
        self.notification_queue = asyncio.Queue()
        self.is_running = False

    def _default_config(self) -> Dict[str, Any]:
        """Default monitoring configuration"""
        return {
            'max_monitored_addresses': 1000,
            'alert_batch_size': 50,
            'notification_retry_attempts': 3,
            'notification_retry_delay_seconds': 60,
            'alert_cooldown_minutes': 15,
            'monitoring_health_check_interval': 300,  # 5 minutes
            'enable_automated_responses': True,
            'enable_alert_aggregation': True
        }

    async def start_monitoring_system(self):
        """Start the real-time monitoring system"""
        if self.is_running:
            logger.warning("Monitoring system already running")
            return

        self.is_running = True
        logger.info("Starting real-time risk monitoring system")

        # Start background tasks
        tasks = [
            asyncio.create_task(self._notification_processor()),
            asyncio.create_task(self._monitoring_health_checker()),
            asyncio.create_task(self._alert_aggregator())
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring system error: {e}")
            self.is_running = False
            raise

    async def stop_monitoring_system(self):
        """Stop the real-time monitoring system"""
        if not self.is_running:
            return

        logger.info("Stopping real-time risk monitoring system")
        self.is_running = False

        # Cancel all active monitors
        for address, task in self.active_monitors.items():
            logger.info(f"Stopping monitor for {address}")
            task.cancel()

        self.active_monitors.clear()
        self.monitored_addresses.clear()

    async def add_address_monitoring(
        self,
        address: str,
        config: MonitoringConfiguration,
        profile: Optional[HolisticRiskProfile] = None
    ):
        """Add an address to real-time monitoring"""

        if len(self.monitored_addresses) >= self.config['max_monitored_addresses']:
            raise ValueError("Maximum monitored addresses limit reached")

        if address in self.monitored_addresses:
            logger.warning(f"Address {address} already being monitored")
            return

        # Store monitoring configuration
        self.monitored_addresses[address] = config

        # Start monitoring task
        monitor_task = asyncio.create_task(
            self._monitor_address(address, config, profile)
        )
        self.active_monitors[address] = monitor_task

        logger.info(f"Started monitoring for address: {address}")

    async def remove_address_monitoring(self, address: str):
        """Remove an address from monitoring"""

        if address not in self.monitored_addresses:
            logger.warning(f"Address {address} not being monitored")
            return

        # Cancel monitoring task
        if address in self.active_monitors:
            self.active_monitors[address].cancel()
            del self.active_monitors[address]

        # Remove configuration
        del self.monitored_addresses[address]

        logger.info(f"Stopped monitoring for address: {address}")

    async def update_monitoring_config(
        self,
        address: str,
        new_config: MonitoringConfiguration
    ):
        """Update monitoring configuration for an address"""

        if address not in self.monitored_addresses:
            raise ValueError(f"Address {address} not being monitored")

        # Update configuration
        self.monitored_addresses[address] = new_config

        # Restart monitoring with new config
        if address in self.active_monitors:
            self.active_monitors[address].cancel()

        monitor_task = asyncio.create_task(
            self._monitor_address(address, new_config)
        )
        self.active_monitors[address] = monitor_task

        logger.info(f"Updated monitoring configuration for: {address}")

    async def _monitor_address(
        self,
        address: str,
        config: MonitoringConfiguration,
        initial_profile: Optional[HolisticRiskProfile] = None
    ):
        """Monitor a single address for risk changes"""

        logger.info(f"Starting address monitoring: {address}")
        last_assessment = initial_profile
        last_alert_time = {}  # Track last alert time by type

        try:
            while self.is_running and address in self.monitored_addresses:
                start_time = datetime.utcnow()

                try:
                    # Get fresh risk assessment
                    from .risk_orchestrator import HolisticRiskOrchestrator
                    orchestrator = HolisticRiskOrchestrator()

                    current_profile = await orchestrator.assess_holistic_risk(
                        address=address,
                        include_scenario_analysis=False,  # Faster for monitoring
                        include_trend_analysis=False,
                        enable_real_time_monitoring=False  # Avoid recursion
                    )

                    # Check for risk threshold breaches
                    alerts = await self._check_risk_thresholds(
                        address, current_profile, last_assessment, config
                    )

                    # Filter alerts by cooldown period
                    filtered_alerts = self._filter_alerts_by_cooldown(
                        alerts, last_alert_time
                    )

                    # Process new alerts
                    for alert in filtered_alerts:
                        await self._process_alert(alert, config)
                        last_alert_time[alert.alert_type] = datetime.utcnow()

                    # Update last assessment
                    last_assessment = current_profile

                    # Log monitoring status
                    logger.debug(
                        f"Monitor check completed for {address}: "
                        f"Risk={current_profile.holistic_risk_score.overall_holistic_score:.1f}, "
                        f"Alerts={len(filtered_alerts)}"
                    )

                except Exception as e:
                    logger.error(f"Error monitoring {address}: {e}")

                # Wait for next check
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                sleep_time = max(0, config.monitoring_frequency_seconds - elapsed)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for address: {address}")
        except Exception as e:
            logger.error(f"Fatal error monitoring {address}: {e}")

    async def _check_risk_thresholds(
        self,
        address: str,
        current_profile: HolisticRiskProfile,
        last_profile: Optional[HolisticRiskProfile],
        config: MonitoringConfiguration
    ) -> List[RiskAlert]:
        """Check for risk threshold breaches and generate alerts"""

        alerts = []
        current_score = current_profile.holistic_risk_score.overall_holistic_score

        # Check overall risk threshold breaches
        for risk_level, threshold in config.risk_threshold_levels.items():
            if current_score >= threshold:
                severity = self._map_risk_level_to_alert_severity(risk_level)

                # Check if this is a new breach or significant increase
                is_new_breach = True
                if last_profile:
                    last_score = last_profile.holistic_risk_score.overall_holistic_score
                    if last_score >= threshold:
                        is_new_breach = False

                if is_new_breach:
                    alert = self._create_threshold_breach_alert(
                        address, risk_level, current_score, threshold, severity
                    )
                    alerts.append(alert)

        # Check individual engine threshold breaches
        engine_scores = {
            RiskEngine.BLOCKCHAIN_BEHAVIOR: current_profile.holistic_risk_score.blockchain_behavior_score,
            RiskEngine.DEFI_PROTOCOL: current_profile.holistic_risk_score.defi_protocol_score,
            RiskEngine.LIQUIDITY_CASCADE: current_profile.holistic_risk_score.liquidity_cascade_score,
            RiskEngine.GOVERNANCE_STABILITY: current_profile.holistic_risk_score.governance_stability_score
        }

        for engine, score in engine_scores.items():
            if score >= 80:  # High threshold for individual engines
                alert = self._create_engine_specific_alert(address, engine, score)
                alerts.append(alert)

        # Check for correlation spikes
        if current_profile.holistic_risk_score.correlation_amplification_score >= 75:
            alert = self._create_correlation_spike_alert(
                address, current_profile.holistic_risk_score.correlation_amplification_score
            )
            alerts.append(alert)

        return alerts

    def _filter_alerts_by_cooldown(
        self,
        alerts: List[RiskAlert],
        last_alert_times: Dict[str, datetime]
    ) -> List[RiskAlert]:
        """Filter alerts based on cooldown periods"""

        cooldown_minutes = self.config['alert_cooldown_minutes']
        filtered_alerts = []

        for alert in alerts:
            last_time = last_alert_times.get(alert.alert_type)
            if last_time is None:
                filtered_alerts.append(alert)
            else:
                time_since_last = datetime.utcnow() - last_time
                if time_since_last.total_seconds() > cooldown_minutes * 60:
                    filtered_alerts.append(alert)

        return filtered_alerts

    async def _process_alert(self, alert: RiskAlert, config: MonitoringConfiguration):
        """Process a risk alert"""

        # Add to alert history
        self.alert_history.append(alert)

        # Queue for notification
        await self.notification_queue.put(alert)

        # Trigger automated responses if enabled
        if (self.config['enable_automated_responses'] and
            config.automated_response_enabled and
            alert.auto_mitigation_triggered):
            await self._trigger_automated_response(alert)

        logger.info(f"Processed {alert.severity.value} alert: {alert.title}")

    async def _trigger_automated_response(self, alert: RiskAlert):
        """Trigger automated response to critical alerts"""

        logger.info(f"Triggering automated response for alert: {alert.alert_id}")

        # Automated responses could include:
        # - Position size reduction recommendations
        # - Liquidity increase alerts
        # - Emergency protocol notifications
        # - Risk mitigation strategy activation

        # Placeholder for automated response logic
        automated_actions = alert.immediate_actions

        for action in automated_actions:
            logger.info(f"Automated action: {action}")
            # Execute automated action
            await self._execute_automated_action(action, alert)

    async def _execute_automated_action(self, action: str, alert: RiskAlert):
        """Execute a specific automated action"""

        # Placeholder for automated action execution
        logger.info(f"Executing automated action: {action} for alert {alert.alert_id}")

        # Examples of automated actions:
        # - Send webhook notifications
        # - Update monitoring frequencies
        # - Trigger risk mitigation workflows
        # - Alert other systems

    async def _notification_processor(self):
        """Process notification queue"""

        while self.is_running:
            try:
                # Get alert from queue
                alert = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )

                # Send notifications
                await self._send_alert_notifications(alert)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Notification processing error: {e}")

    async def _send_alert_notifications(self, alert: RiskAlert):
        """Send alert notifications via configured channels"""

        # Email notifications
        if 'email' in self.config.get('notification_channels', []):
            await self._send_email_notification(alert)

        # Slack notifications
        if 'slack' in self.config.get('notification_channels', []):
            await self._send_slack_notification(alert)

        # Webhook notifications
        if 'webhook' in self.config.get('notification_channels', []):
            await self._send_webhook_notification(alert)

    async def _send_email_notification(self, alert: RiskAlert):
        """Send email notification"""
        # Placeholder for email notification
        logger.info(f"Sending email notification for alert: {alert.alert_id}")

    async def _send_slack_notification(self, alert: RiskAlert):
        """Send Slack notification"""
        # Placeholder for Slack notification
        logger.info(f"Sending Slack notification for alert: {alert.alert_id}")

    async def _send_webhook_notification(self, alert: RiskAlert):
        """Send webhook notification"""
        # Placeholder for webhook notification
        logger.info(f"Sending webhook notification for alert: {alert.alert_id}")

    async def _monitoring_health_checker(self):
        """Monitor the health of the monitoring system itself"""

        while self.is_running:
            try:
                # Check monitor task health
                healthy_monitors = 0
                total_monitors = len(self.active_monitors)

                for address, task in self.active_monitors.items():
                    if not task.done():
                        healthy_monitors += 1
                    else:
                        logger.warning(f"Monitor task died for address: {address}")
                        # Restart dead monitor
                        config = self.monitored_addresses.get(address)
                        if config:
                            new_task = asyncio.create_task(
                                self._monitor_address(address, config)
                            )
                            self.active_monitors[address] = new_task

                # Log health status
                logger.info(f"Monitor health: {healthy_monitors}/{total_monitors} healthy")

                # Check notification queue size
                queue_size = self.notification_queue.qsize()
                if queue_size > 100:
                    logger.warning(f"Large notification queue: {queue_size} items")

                await asyncio.sleep(self.config['monitoring_health_check_interval'])

            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _alert_aggregator(self):
        """Aggregate and analyze alert patterns"""

        while self.is_running:
            try:
                if self.config['enable_alert_aggregation']:
                    # Analyze recent alerts for patterns
                    recent_alerts = [
                        alert for alert in self.alert_history
                        if (datetime.utcnow() - alert.timestamp).total_seconds() < 3600
                    ]

                    if len(recent_alerts) > 10:
                        logger.info(f"High alert volume: {len(recent_alerts)} alerts in last hour")

                await asyncio.sleep(600)  # Run every 10 minutes

            except Exception as e:
                logger.error(f"Alert aggregation error: {e}")

    def _map_risk_level_to_alert_severity(self, risk_level: RiskLevel) -> AlertSeverity:
        """Map risk level to alert severity"""
        mapping = {
            RiskLevel.LOW: AlertSeverity.INFO,
            RiskLevel.MEDIUM: AlertSeverity.WARNING,
            RiskLevel.HIGH: AlertSeverity.HIGH,
            RiskLevel.CRITICAL: AlertSeverity.CRITICAL
        }
        return mapping.get(risk_level, AlertSeverity.WARNING)

    def _create_threshold_breach_alert(
        self,
        address: str,
        risk_level: RiskLevel,
        current_score: float,
        threshold: float,
        severity: AlertSeverity
    ) -> RiskAlert:
        """Create a threshold breach alert"""

        from .models import RiskAlert
        import uuid

        return RiskAlert(
            alert_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=severity,
            risk_engines_involved=[RiskEngine.BLOCKCHAIN_BEHAVIOR],  # Could be multiple
            alert_type="threshold_breach",
            title=f"Risk Threshold Breach - {risk_level.value}",
            description=f"Risk score {current_score:.1f} exceeded {risk_level.value} threshold ({threshold})",
            risk_score_threshold_exceeded=threshold,
            current_risk_score=current_score,
            affected_addresses=[address],
            triggers=[f"Score exceeded {threshold}"],
            immediate_actions=["Review risk factors", "Consider position adjustments"],
            escalation_path=["Risk team", "Portfolio manager"],
            estimated_impact={"financial": current_score * 1000},
            time_to_critical=None,
            auto_mitigation_triggered=severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY],
            acknowledgment_required=severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
            related_alerts=[]
        )

    def _create_engine_specific_alert(self, address: str, engine: RiskEngine, score: float) -> RiskAlert:
        """Create an engine-specific alert"""

        from .models import RiskAlert
        import uuid

        return RiskAlert(
            alert_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=AlertSeverity.HIGH,
            risk_engines_involved=[engine],
            alert_type="engine_specific",
            title=f"High {engine.value.replace('_', ' ').title()} Risk",
            description=f"{engine.value} risk score reached {score:.1f}",
            risk_score_threshold_exceeded=80.0,
            current_risk_score=score,
            affected_addresses=[address],
            triggers=[f"{engine.value} risk spike"],
            immediate_actions=[f"Review {engine.value} factors"],
            escalation_path=["Risk team"],
            estimated_impact={"operational": score},
            time_to_critical=None,
            auto_mitigation_triggered=False,
            acknowledgment_required=True,
            related_alerts=[]
        )

    def _create_correlation_spike_alert(self, address: str, correlation_score: float) -> RiskAlert:
        """Create a correlation spike alert"""

        from .models import RiskAlert
        import uuid

        return RiskAlert(
            alert_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=AlertSeverity.HIGH,
            risk_engines_involved=list(RiskEngine),
            alert_type="correlation_spike",
            title="Cross-Engine Risk Correlation Spike",
            description=f"Risk correlation amplification reached {correlation_score:.1f}",
            risk_score_threshold_exceeded=75.0,
            current_risk_score=correlation_score,
            affected_addresses=[address],
            triggers=["High cross-engine correlation"],
            immediate_actions=["Review portfolio diversification", "Check systemic factors"],
            escalation_path=["Risk team", "Chief Risk Officer"],
            estimated_impact={"systemic": correlation_score * 100},
            time_to_critical=None,
            auto_mitigation_triggered=True,
            acknowledgment_required=True,
            related_alerts=[]
        )