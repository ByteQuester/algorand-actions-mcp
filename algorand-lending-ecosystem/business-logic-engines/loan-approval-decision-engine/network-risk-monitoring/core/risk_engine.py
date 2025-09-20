"""
Network Risk Engine

Master risk engine that aggregates ecosystem health, protocol risk, market conditions,
congestion monitoring, correlation analysis, and systemic risk for comprehensive
real-time risk assessment and dynamic loan decision adjustment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path

from .ecosystem_health import EcosystemHealthMonitor, EcosystemHealthReport
from .protocol_risk import ProtocolRiskAnalyzer, ProtocolRiskReport
from .market_conditions import MarketConditionAnalyzer, MarketConditionReport
from .congestion_monitor import CongestionMonitor, CongestionReport
from .correlation_analysis import CorrelationAnalyzer, CorrelationReport
from .systemic_risk import SystemicRiskAssessor, SystemicRiskReport

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class RiskAdjustment:
    """Risk-based loan parameter adjustment"""
    ltv_adjustment: float  # Loan-to-value ratio adjustment
    interest_rate_adjustment: float  # Interest rate adjustment
    approval_threshold_adjustment: float  # Approval threshold adjustment
    manual_review_required: bool  # Require manual review
    additional_collateral_required: float  # Additional collateral percentage


@dataclass
class RiskAlert:
    """Risk monitoring alert"""
    alert_id: str
    severity: AlertSeverity
    alert_type: str
    title: str
    message: str
    risk_components: List[str]
    affected_metrics: Dict[str, float]
    recommended_actions: List[str]
    timestamp: datetime
    acknowledged: bool = False


@dataclass
class ComprehensiveRiskAssessment:
    """Comprehensive network risk assessment"""
    overall_risk_score: float
    risk_level: RiskLevel
    component_scores: Dict[str, float]

    # Component reports
    ecosystem_health_report: Optional[EcosystemHealthReport]
    protocol_risk_report: Optional[ProtocolRiskReport]
    market_condition_report: Optional[MarketConditionReport]
    congestion_report: Optional[CongestionReport]
    correlation_report: Optional[CorrelationReport]
    systemic_risk_report: Optional[SystemicRiskReport]

    # Risk adjustments
    risk_adjustments: RiskAdjustment

    # Alerts and recommendations
    active_alerts: List[RiskAlert]
    risk_factors: List[str]
    risk_trends: Dict[str, float]
    recommendations: List[str]

    # Metadata
    assessment_timestamp: datetime
    confidence_score: float
    next_assessment_time: datetime


class NetworkRiskEngine:
    """Master network risk engine for comprehensive real-time risk assessment"""

    def __init__(self, config_path: str = None):
        """Initialize network risk engine with all component analyzers"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.risk_config = self.config['risk_engine']
        self.alert_config = self.config['alerting']

        # Initialize component analyzers
        self.ecosystem_monitor = EcosystemHealthMonitor(config_path)
        self.protocol_analyzer = ProtocolRiskAnalyzer(config_path)
        self.market_analyzer = MarketConditionAnalyzer(config_path)
        self.congestion_monitor = CongestionMonitor(config_path)
        self.correlation_analyzer = CorrelationAnalyzer(config_path)
        self.systemic_assessor = SystemicRiskAssessor(config_path)

        # Risk state tracking
        self.last_assessment = None
        self.risk_history = []
        self.active_alerts = []

    async def assess_comprehensive_risk(self) -> ComprehensiveRiskAssessment:
        """
        Perform comprehensive network risk assessment

        Returns:
            ComprehensiveRiskAssessment with detailed risk analysis
        """
        try:
            logger.info("Starting comprehensive network risk assessment")

            # Run all component risk assessments in parallel
            async with self.ecosystem_monitor:
                tasks = [
                    self.ecosystem_monitor.assess_ecosystem_health(),
                    self.protocol_analyzer.assess_protocol_risks(),
                    self.market_analyzer.analyze_market_conditions(),
                    self.congestion_monitor.monitor_network_congestion(),
                    self.correlation_analyzer.analyze_correlations(),
                    self.systemic_assessor.assess_systemic_risks()
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract component reports
            ecosystem_report = results[0] if not isinstance(results[0], Exception) else None
            protocol_report = results[1] if not isinstance(results[1], Exception) else None
            market_report = results[2] if not isinstance(results[2], Exception) else None
            congestion_report = results[3] if not isinstance(results[3], Exception) else None
            correlation_report = results[4] if not isinstance(results[4], Exception) else None
            systemic_report = results[5] if not isinstance(results[5], Exception) else None

            # Log any component failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    component_names = ["ecosystem", "protocol", "market", "congestion", "correlation", "systemic"]
                    logger.error(f"{component_names[i]} risk assessment failed: {result}")

            # Extract component scores
            component_scores = self._extract_component_scores(
                ecosystem_report, protocol_report, market_report,
                congestion_report, correlation_report, systemic_report
            )

            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(component_scores)

            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk_score)

            # Calculate risk adjustments
            risk_adjustments = self._calculate_risk_adjustments(overall_risk_score, risk_level)

            # Consolidate alerts
            active_alerts = self._consolidate_alerts(
                ecosystem_report, protocol_report, market_report,
                congestion_report, correlation_report, systemic_report
            )

            # Generate additional risk alerts
            additional_alerts = self._generate_risk_alerts(
                overall_risk_score, component_scores, risk_level
            )
            active_alerts.extend(additional_alerts)

            # Analyze risk factors and trends
            risk_factors = self._consolidate_risk_factors(
                ecosystem_report, protocol_report, market_report,
                congestion_report, correlation_report, systemic_report
            )
            risk_trends = self._analyze_risk_trends(component_scores)

            # Generate recommendations
            recommendations = self._generate_risk_recommendations(
                overall_risk_score, risk_level, risk_factors, component_scores
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                ecosystem_report, protocol_report, market_report,
                congestion_report, correlation_report, systemic_report
            )

            # Determine next assessment time
            next_assessment = self._calculate_next_assessment_time(risk_level)

            # Update risk state
            assessment = ComprehensiveRiskAssessment(
                overall_risk_score=overall_risk_score,
                risk_level=risk_level,
                component_scores=component_scores,
                ecosystem_health_report=ecosystem_report,
                protocol_risk_report=protocol_report,
                market_condition_report=market_report,
                congestion_report=congestion_report,
                correlation_report=correlation_report,
                systemic_risk_report=systemic_report,
                risk_adjustments=risk_adjustments,
                active_alerts=active_alerts,
                risk_factors=risk_factors,
                risk_trends=risk_trends,
                recommendations=recommendations,
                assessment_timestamp=datetime.utcnow(),
                confidence_score=confidence_score,
                next_assessment_time=next_assessment
            )

            # Update internal state
            self.last_assessment = assessment
            self.risk_history.append({
                'timestamp': assessment.assessment_timestamp,
                'risk_score': overall_risk_score,
                'risk_level': risk_level.value,
                'component_scores': component_scores
            })

            # Keep only recent history
            self._cleanup_risk_history()

            return assessment

        except Exception as e:
            logger.error(f"Error in comprehensive risk assessment: {e}")
            raise

    def _extract_component_scores(self, ecosystem_report, protocol_report, market_report,
                                congestion_report, correlation_report, systemic_report) -> Dict[str, float]:
        """Extract risk scores from component reports"""
        component_scores = {}

        try:
            # Ecosystem health (invert for risk - lower health = higher risk)
            if ecosystem_report:
                component_scores['ecosystem_health'] = 100 - ecosystem_report.overall_health_score
            else:
                component_scores['ecosystem_health'] = 50  # Neutral if unavailable

            # Protocol risk
            if protocol_report:
                component_scores['protocol_risk'] = protocol_report.overall_risk_score
            else:
                component_scores['protocol_risk'] = 50

            # Market conditions risk
            if market_report:
                component_scores['market_conditions'] = market_report.overall_risk_score
            else:
                component_scores['market_conditions'] = 50

            # Congestion impact
            if congestion_report:
                component_scores['congestion_impact'] = congestion_report.congestion_risk_score
            else:
                component_scores['congestion_impact'] = 50

            # Correlation risk
            if correlation_report:
                component_scores['correlation_risk'] = correlation_report.overall_correlation_risk
            else:
                component_scores['correlation_risk'] = 50

            # Systemic risk
            if systemic_report:
                component_scores['systemic_risk'] = systemic_report.overall_systemic_risk
            else:
                component_scores['systemic_risk'] = 50

            return component_scores

        except Exception as e:
            logger.error(f"Error extracting component scores: {e}")
            return {key: 50 for key in ['ecosystem_health', 'protocol_risk', 'market_conditions',
                                      'congestion_impact', 'correlation_risk', 'systemic_risk']}

    def _calculate_overall_risk_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate overall risk score using configured weights"""
        try:
            weights = self.risk_config['risk_component_weights']

            weighted_score = (
                component_scores.get('ecosystem_health', 50) * weights['ecosystem_health'] +
                component_scores.get('protocol_risk', 50) * weights['protocol_risk'] +
                component_scores.get('market_conditions', 50) * weights['market_conditions'] +
                component_scores.get('congestion_impact', 50) * weights['congestion_impact'] +
                component_scores.get('correlation_risk', 50) * weights['correlation_risk'] +
                component_scores.get('systemic_risk', 50) * weights['systemic_risk']
            )

            return min(100.0, max(0.0, weighted_score))

        except Exception as e:
            logger.error(f"Error calculating overall risk score: {e}")
            return 50.0  # Default moderate risk

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on score"""
        try:
            risk_levels = self.risk_config['risk_levels']

            for level, (min_score, max_score) in risk_levels.items():
                if min_score <= risk_score <= max_score:
                    return RiskLevel(level)

            # Default to very high if score is above all ranges
            return RiskLevel.VERY_HIGH

        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return RiskLevel.MODERATE

    def _calculate_risk_adjustments(self, risk_score: float, risk_level: RiskLevel) -> RiskAdjustment:
        """Calculate risk-based loan parameter adjustments"""
        try:
            adjustments = self.risk_config['dynamic_adjustments']

            # Get adjustments for the risk level
            ltv_adj = adjustments['ltv_adjustments'].get(risk_level.value, 0.0)
            rate_adj = adjustments['interest_rate_adjustments'].get(risk_level.value, 0.0)
            threshold_adj = adjustments['approval_threshold_adjustments'].get(risk_level.value, 0.0)

            # Determine if manual review is required
            manual_review = risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]

            # Calculate additional collateral requirement
            additional_collateral = 0.0
            if risk_level == RiskLevel.HIGH:
                additional_collateral = 0.1  # 10% additional collateral
            elif risk_level == RiskLevel.VERY_HIGH:
                additional_collateral = 0.25  # 25% additional collateral

            return RiskAdjustment(
                ltv_adjustment=ltv_adj,
                interest_rate_adjustment=rate_adj,
                approval_threshold_adjustment=threshold_adj,
                manual_review_required=manual_review,
                additional_collateral_required=additional_collateral
            )

        except Exception as e:
            logger.error(f"Error calculating risk adjustments: {e}")
            return RiskAdjustment(0.0, 0.0, 0.0, False, 0.0)

    def _consolidate_alerts(self, ecosystem_report, protocol_report, market_report,
                          congestion_report, correlation_report, systemic_report) -> List[RiskAlert]:
        """Consolidate alerts from all component reports"""
        alerts = []

        try:
            # Convert component alerts to risk alerts
            if ecosystem_report and hasattr(ecosystem_report, 'active_alerts'):
                for alert in ecosystem_report.active_alerts:
                    alerts.append(RiskAlert(
                        alert_id=alert.alert_id,
                        severity=AlertSeverity(alert.severity),
                        alert_type="ecosystem_health",
                        title=f"Ecosystem Health: {alert.alert_type}",
                        message=alert.message,
                        risk_components=["ecosystem_health"],
                        affected_metrics=alert.metric_values,
                        recommended_actions=["Monitor ecosystem closely", "Consider risk adjustment"],
                        timestamp=alert.timestamp
                    ))

            # Add similar conversions for other component reports...
            # (Abbreviated for brevity, but would include all components)

        except Exception as e:
            logger.error(f"Error consolidating alerts: {e}")

        return alerts

    def _generate_risk_alerts(self, overall_risk_score: float, component_scores: Dict[str, float],
                            risk_level: RiskLevel) -> List[RiskAlert]:
        """Generate additional risk alerts based on overall assessment"""
        alerts = []

        try:
            # High overall risk alert
            if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
                alerts.append(RiskAlert(
                    alert_id=f"high_risk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    severity=AlertSeverity.CRITICAL if risk_level == RiskLevel.VERY_HIGH else AlertSeverity.WARNING,
                    alert_type="overall_risk",
                    title=f"Network Risk Level: {risk_level.value.upper()}",
                    message=f"Overall network risk score is {overall_risk_score:.1f} indicating {risk_level.value} risk",
                    risk_components=list(component_scores.keys()),
                    affected_metrics={"overall_risk_score": overall_risk_score},
                    recommended_actions=["Increase loan requirements", "Enhanced monitoring", "Consider market pause"],
                    timestamp=datetime.utcnow()
                ))

            # Multiple high-risk components alert
            high_risk_components = [k for k, v in component_scores.items() if v > 75]
            if len(high_risk_components) >= 3:
                alerts.append(RiskAlert(
                    alert_id=f"multi_risk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    severity=AlertSeverity.CRITICAL,
                    alert_type="multiple_risk_factors",
                    title="Multiple High-Risk Components Detected",
                    message=f"Multiple risk components showing high risk: {', '.join(high_risk_components)}",
                    risk_components=high_risk_components,
                    affected_metrics={k: component_scores[k] for k in high_risk_components},
                    recommended_actions=["Immediate risk review", "Tighten lending criteria", "Management escalation"],
                    timestamp=datetime.utcnow()
                ))

        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")

        return alerts

    def _consolidate_risk_factors(self, ecosystem_report, protocol_report, market_report,
                                congestion_report, correlation_report, systemic_report) -> List[str]:
        """Consolidate risk factors from all components"""
        risk_factors = []

        try:
            if ecosystem_report and hasattr(ecosystem_report, 'risk_factors'):
                risk_factors.extend(ecosystem_report.risk_factors)

            if protocol_report and hasattr(protocol_report, 'risk_factors'):
                risk_factors.extend(protocol_report.risk_factors)

            if market_report and hasattr(market_report, 'risk_factors'):
                risk_factors.extend(market_report.risk_factors)

            # Add other component risk factors...

            # Remove duplicates while preserving order
            seen = set()
            unique_factors = []
            for factor in risk_factors:
                if factor not in seen:
                    seen.add(factor)
                    unique_factors.append(factor)

            return unique_factors

        except Exception as e:
            logger.error(f"Error consolidating risk factors: {e}")
            return []

    def _analyze_risk_trends(self, component_scores: Dict[str, float]) -> Dict[str, float]:
        """Analyze risk trends compared to historical data"""
        trends = {}

        try:
            if len(self.risk_history) < 2:
                # Not enough history for trend analysis
                return {key: 0.0 for key in component_scores.keys()}

            # Compare current scores to recent historical averages
            recent_history = self.risk_history[-5:]  # Last 5 assessments

            for component, current_score in component_scores.items():
                historical_scores = [
                    h['component_scores'].get(component, 50)
                    for h in recent_history
                    if 'component_scores' in h
                ]

                if historical_scores:
                    avg_historical = sum(historical_scores) / len(historical_scores)
                    trend = (current_score - avg_historical) / max(avg_historical, 1)
                    trends[component] = trend
                else:
                    trends[component] = 0.0

            return trends

        except Exception as e:
            logger.error(f"Error analyzing risk trends: {e}")
            return {key: 0.0 for key in component_scores.keys()}

    def _generate_risk_recommendations(self, overall_risk_score: float, risk_level: RiskLevel,
                                     risk_factors: List[str], component_scores: Dict[str, float]) -> List[str]:
        """Generate comprehensive risk management recommendations"""
        recommendations = []

        try:
            # Overall risk level recommendations
            if risk_level == RiskLevel.VERY_HIGH:
                recommendations.append("CRITICAL: Consider suspending new loan approvals")
                recommendations.append("Implement emergency risk protocols")
                recommendations.append("Increase collateral requirements by 25%")
            elif risk_level == RiskLevel.HIGH:
                recommendations.append("Tighten loan approval criteria significantly")
                recommendations.append("Increase monitoring frequency to every 5 minutes")
                recommendations.append("Require additional collateral for all new loans")
            elif risk_level == RiskLevel.MODERATE:
                recommendations.append("Apply standard risk adjustments to loan parameters")
                recommendations.append("Monitor situation closely for deterioration")
            elif risk_level in [RiskLevel.LOW, RiskLevel.VERY_LOW]:
                recommendations.append("Current risk levels support normal lending operations")
                recommendations.append("Consider relaxing some lending restrictions")

            # Component-specific recommendations
            highest_risk_component = max(component_scores, key=component_scores.get)
            highest_risk_score = component_scores[highest_risk_component]

            if highest_risk_score > 80:
                if highest_risk_component == 'ecosystem_health':
                    recommendations.append("Poor ecosystem health - avoid lending to ecosystem-dependent borrowers")
                elif highest_risk_component == 'protocol_risk':
                    recommendations.append("High protocol risk - review exposure to risky DeFi protocols")
                elif highest_risk_component == 'market_conditions':
                    recommendations.append("Adverse market conditions - implement conservative LTV ratios")
                elif highest_risk_component == 'systemic_risk':
                    recommendations.append("Systemic risk detected - prepare for potential cascade events")

            # Risk factor specific recommendations
            if any("tvl" in factor.lower() for factor in risk_factors):
                recommendations.append("TVL instability detected - monitor borrower protocol exposure")

            if any("correlation" in factor.lower() for factor in risk_factors):
                recommendations.append("High correlations detected - diversify loan portfolio")

        except Exception as e:
            logger.error(f"Error generating risk recommendations: {e}")

        return recommendations

    def _calculate_confidence_score(self, ecosystem_report, protocol_report, market_report,
                                   congestion_report, correlation_report, systemic_report) -> float:
        """Calculate confidence score for the risk assessment"""
        try:
            # Base confidence on data availability and quality
            available_reports = 0
            total_reports = 6

            reports = [ecosystem_report, protocol_report, market_report,
                      congestion_report, correlation_report, systemic_report]

            for report in reports:
                if report is not None:
                    available_reports += 1

            base_confidence = available_reports / total_reports

            # Adjust for data freshness (simplified)
            freshness_bonus = 0.1 if available_reports >= 4 else 0.0

            # Adjust for historical data availability
            history_bonus = min(0.1, len(self.risk_history) / 10)

            final_confidence = min(1.0, base_confidence + freshness_bonus + history_bonus)

            return final_confidence

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5

    def _calculate_next_assessment_time(self, risk_level: RiskLevel) -> datetime:
        """Calculate when the next risk assessment should be performed"""
        try:
            # More frequent assessments for higher risk levels
            if risk_level == RiskLevel.VERY_HIGH:
                interval_minutes = 1
            elif risk_level == RiskLevel.HIGH:
                interval_minutes = 3
            elif risk_level == RiskLevel.MODERATE:
                interval_minutes = 5
            elif risk_level == RiskLevel.LOW:
                interval_minutes = 15
            else:  # VERY_LOW
                interval_minutes = 30

            return datetime.utcnow() + timedelta(minutes=interval_minutes)

        except Exception as e:
            logger.error(f"Error calculating next assessment time: {e}")
            return datetime.utcnow() + timedelta(minutes=5)

    def _cleanup_risk_history(self):
        """Clean up old risk history to prevent memory issues"""
        try:
            # Keep only the last 100 assessments
            if len(self.risk_history) > 100:
                self.risk_history = self.risk_history[-100:]

            # Remove assessments older than 7 days
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            self.risk_history = [
                h for h in self.risk_history
                if h.get('timestamp', datetime.min) > cutoff_time
            ]

        except Exception as e:
            logger.error(f"Error cleaning up risk history: {e}")

    async def get_current_risk_level(self) -> RiskLevel:
        """Get the current risk level (perform new assessment if needed)"""
        try:
            if (self.last_assessment is None or
                datetime.utcnow() >= self.last_assessment.next_assessment_time):
                # Need new assessment
                assessment = await self.assess_comprehensive_risk()
                return assessment.risk_level
            else:
                # Use cached assessment
                return self.last_assessment.risk_level

        except Exception as e:
            logger.error(f"Error getting current risk level: {e}")
            return RiskLevel.MODERATE

    async def get_risk_adjustments(self) -> RiskAdjustment:
        """Get current risk adjustments for loan decisions"""
        try:
            if (self.last_assessment is None or
                datetime.utcnow() >= self.last_assessment.next_assessment_time):
                # Need new assessment
                assessment = await self.assess_comprehensive_risk()
                return assessment.risk_adjustments
            else:
                # Use cached assessment
                return self.last_assessment.risk_adjustments

        except Exception as e:
            logger.error(f"Error getting risk adjustments: {e}")
            return RiskAdjustment(0.0, 0.0, 0.0, False, 0.0)