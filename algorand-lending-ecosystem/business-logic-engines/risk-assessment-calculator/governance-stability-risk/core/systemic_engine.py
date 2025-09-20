"""
Master Systemic Risk Assessment Engine
Integrates all governance and systemic risk components for holistic assessment
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import json

# Import all risk analysis components
from .governance_analyzer import GovernanceAnalyzer, GovernanceStabilityReport, RiskLevel
from .voting_concentration import VotingConcentrationAnalyzer, VotingPowerMetrics, ConcentrationAlert
from .proposal_manipulation import ProposalManipulationDetector, ProposalManipulationReport
from .emergency_response import EmergencyResponseAnalyzer, ResponseReadinessReport
from .upgrade_risks import ProtocolUpgradeRiskAnalyzer, UpgradeRiskReport
from .regulatory_monitor import RegulatoryMonitor, RegulatoryRiskReport
from .network_security import NetworkSecurityMetrics, SecurityRiskLevel
from .foundation_dependency import FoundationDependencyAnalyzer, DependencyRiskLevel

class SystemicRiskLevel(Enum):
    """Overall systemic risk levels"""
    CATASTROPHIC = "catastrophic"
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"

@dataclass
class SystemicRiskMetrics:
    """Comprehensive systemic risk metrics"""
    timestamp: datetime

    # Individual component scores
    governance_risk_score: float
    voting_concentration_score: float
    proposal_manipulation_score: float
    emergency_readiness_score: float
    upgrade_risk_score: float
    regulatory_risk_score: float
    network_security_score: float
    foundation_dependency_score: float

    # Composite scores
    overall_systemic_risk: float
    stability_index: float
    resilience_score: float

    # Risk level classifications
    overall_risk_level: SystemicRiskLevel
    component_risk_levels: Dict[str, str]

    # Trend indicators
    risk_trend_direction: str
    trend_confidence: float

@dataclass
class SystemicAlert:
    """Systemic risk alert"""
    alert_id: str
    alert_type: str
    severity: str
    component: str
    message: str
    recommendations: List[str]
    timestamp: datetime
    requires_immediate_action: bool

@dataclass
class SystemicRiskReport:
    """Comprehensive systemic risk assessment report"""
    timestamp: datetime
    assessment_id: str

    # Executive summary
    executive_summary: Dict[str, Any]

    # Detailed metrics
    systemic_metrics: SystemicRiskMetrics

    # Component reports
    governance_report: Optional[GovernanceStabilityReport]
    voting_concentration_report: Optional[Dict[str, Any]]
    proposal_manipulation_report: Optional[ProposalManipulationReport]
    emergency_readiness_report: Optional[ResponseReadinessReport]
    upgrade_risk_report: Optional[UpgradeRiskReport]
    regulatory_risk_report: Optional[RegulatoryRiskReport]
    network_security_report: Optional[Dict[str, Any]]
    foundation_dependency_report: Optional[Dict[str, Any]]

    # Integrated analysis
    risk_correlations: Dict[str, float]
    cascade_risk_analysis: Dict[str, Any]
    scenario_assessments: List[Dict[str, Any]]

    # Alerts and recommendations
    active_alerts: List[SystemicAlert]
    priority_recommendations: List[str]
    monitoring_requirements: List[str]

    # Forward-looking analysis
    risk_projections: Dict[str, float]
    early_warning_indicators: List[str]

    next_assessment: datetime

class SystemicRiskEngine:
    """Master engine for comprehensive systemic risk assessment"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the systemic risk engine"""
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.governance_analyzer = GovernanceAnalyzer(config_path)
        self.config = self.governance_analyzer.config

        # Initialize component analyzers
        self.voting_analyzer = VotingConcentrationAnalyzer(self.config)
        self.proposal_detector = ProposalManipulationDetector(self.config)
        self.emergency_analyzer = EmergencyResponseAnalyzer(self.config)
        self.upgrade_analyzer = ProtocolUpgradeRiskAnalyzer(self.config)
        self.regulatory_monitor = RegulatoryMonitor(self.config)
        self.network_security = NetworkSecurityMetrics(self.config)
        self.foundation_analyzer = FoundationDependencyAnalyzer(self.config)

        # Historical data storage
        self.historical_assessments = []
        self.active_alerts = []

        # Risk correlation matrix
        self.risk_correlations = self._initialize_risk_correlations()

    def _initialize_risk_correlations(self) -> Dict[str, Dict[str, float]]:
        """Initialize risk correlation matrix between components"""
        return {
            'governance': {
                'voting_concentration': 0.8,
                'proposal_manipulation': 0.7,
                'regulatory': 0.5,
                'emergency_readiness': 0.6
            },
            'voting_concentration': {
                'governance': 0.8,
                'proposal_manipulation': 0.6,
                'foundation_dependency': 0.4
            },
            'proposal_manipulation': {
                'governance': 0.7,
                'voting_concentration': 0.6,
                'emergency_readiness': 0.5
            },
            'regulatory': {
                'governance': 0.5,
                'upgrade_risks': 0.4,
                'foundation_dependency': 0.6
            },
            'network_security': {
                'upgrade_risks': 0.7,
                'emergency_readiness': 0.5,
                'foundation_dependency': 0.3
            }
        }

    async def assess_systemic_risk(self,
                                 input_data: Dict[str, Any]) -> SystemicRiskReport:
        """
        Perform comprehensive systemic risk assessment

        Args:
            input_data: Comprehensive data for all risk components

        Returns:
            SystemicRiskReport: Complete systemic risk assessment
        """
        try:
            self.logger.info("Starting comprehensive systemic risk assessment")
            assessment_id = f"systemic_assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Run all component analyses in parallel
            component_results = await self._run_component_analyses(input_data)

            # Calculate systemic metrics
            systemic_metrics = self._calculate_systemic_metrics(component_results)

            # Perform integrated analysis
            risk_correlations = self._analyze_risk_correlations(component_results)
            cascade_analysis = await self._analyze_cascade_risks(component_results, systemic_metrics)
            scenario_assessments = await self._assess_risk_scenarios(component_results, systemic_metrics)

            # Generate alerts
            active_alerts = self._generate_systemic_alerts(component_results, systemic_metrics)

            # Generate recommendations
            priority_recommendations = self._generate_priority_recommendations(
                component_results, systemic_metrics, active_alerts
            )
            monitoring_requirements = self._generate_monitoring_requirements(component_results)

            # Forward-looking analysis
            risk_projections = await self._project_future_risks(component_results, systemic_metrics)
            early_warning_indicators = self._identify_early_warning_indicators(
                component_results, systemic_metrics
            )

            # Create executive summary
            executive_summary = self._create_executive_summary(
                systemic_metrics, active_alerts, priority_recommendations
            )

            # Compile comprehensive report
            report = SystemicRiskReport(
                timestamp=datetime.utcnow(),
                assessment_id=assessment_id,
                executive_summary=executive_summary,
                systemic_metrics=systemic_metrics,
                governance_report=component_results.get('governance'),
                voting_concentration_report=component_results.get('voting_concentration'),
                proposal_manipulation_report=component_results.get('proposal_manipulation'),
                emergency_readiness_report=component_results.get('emergency_readiness'),
                upgrade_risk_report=component_results.get('upgrade_risks'),
                regulatory_risk_report=component_results.get('regulatory'),
                network_security_report=component_results.get('network_security'),
                foundation_dependency_report=component_results.get('foundation_dependency'),
                risk_correlations=risk_correlations,
                cascade_risk_analysis=cascade_analysis,
                scenario_assessments=scenario_assessments,
                active_alerts=active_alerts,
                priority_recommendations=priority_recommendations,
                monitoring_requirements=monitoring_requirements,
                risk_projections=risk_projections,
                early_warning_indicators=early_warning_indicators,
                next_assessment=datetime.utcnow() + timedelta(hours=24)
            )

            # Store historical data
            self._store_assessment_results(report)

            self.logger.info(f"Systemic risk assessment completed. "
                           f"Overall risk level: {systemic_metrics.overall_risk_level.value}")

            return report

        except Exception as e:
            self.logger.error(f"Systemic risk assessment failed: {e}")
            raise

    async def _run_component_analyses(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all component risk analyses in parallel"""
        try:
            # Prepare tasks for parallel execution
            tasks = []

            # Governance analysis
            if 'governance_data' in input_data:
                tasks.append(('governance',
                             self.governance_analyzer.analyze_governance_stability(
                                 input_data['governance_data'])))

            # Voting concentration analysis
            if 'voting_data' in input_data:
                tasks.append(('voting_concentration',
                             self.voting_analyzer.analyze_voting_concentration(
                                 input_data['voting_data'])))

            # Proposal manipulation analysis
            if 'proposals_data' in input_data and 'voting_data' in input_data:
                tasks.append(('proposal_manipulation',
                             self.proposal_detector.analyze_proposal_manipulation(
                                 input_data['proposals_data'], input_data['voting_data'])))

            # Emergency readiness analysis
            if 'emergency_data' in input_data:
                tasks.append(('emergency_readiness',
                             self.emergency_analyzer.analyze_emergency_readiness(
                                 input_data['emergency_data'])))

            # Upgrade risk analysis
            if 'upgrade_data' in input_data:
                tasks.append(('upgrade_risks',
                             self.upgrade_analyzer.assess_upgrade_risks(
                                 input_data['upgrade_data'])))

            # Regulatory monitoring
            if 'regulatory_data' in input_data:
                tasks.append(('regulatory',
                             self.regulatory_monitor.monitor_regulatory_landscape(
                                 input_data['regulatory_data'])))

            # Network security analysis
            if 'network_data' in input_data:
                tasks.append(('network_security',
                             self.network_security.assess_network_security(
                                 input_data['network_data'])))

            # Foundation dependency analysis
            if 'foundation_data' in input_data:
                tasks.append(('foundation_dependency',
                             self.foundation_analyzer.analyze_foundation_dependencies(
                                 input_data['foundation_data'])))

            # Execute all tasks in parallel
            results = {}
            for component_name, task in tasks:
                try:
                    result = await task
                    results[component_name] = result
                except Exception as e:
                    self.logger.error(f"Component analysis failed for {component_name}: {e}")
                    results[component_name] = None

            return results

        except Exception as e:
            self.logger.error(f"Component analyses execution failed: {e}")
            return {}

    def _calculate_systemic_metrics(self, component_results: Dict[str, Any]) -> SystemicRiskMetrics:
        """Calculate comprehensive systemic risk metrics"""
        try:
            # Extract individual component scores
            governance_score = self._extract_risk_score(component_results.get('governance'), 'overall_risk_score')
            voting_score = self._extract_voting_concentration_score(component_results.get('voting_concentration'))
            manipulation_score = self._extract_risk_score(component_results.get('proposal_manipulation'), 'risk_score')
            emergency_score = self._extract_risk_score(component_results.get('emergency_readiness'), 'overall_readiness_score')
            upgrade_score = self._extract_risk_score(component_results.get('upgrade_risks'), 'overall_risk_score')
            regulatory_score = self._extract_risk_score(component_results.get('regulatory'), 'overall_risk_score')
            network_score = self._extract_network_security_score(component_results.get('network_security'))
            foundation_score = self._extract_foundation_dependency_score(component_results.get('foundation_dependency'))

            # Calculate weighted overall systemic risk
            component_weights = self.config.get('monitoring', {}).get('weights', {})
            weights = {
                'governance': component_weights.get('governance_weight', 0.25),
                'voting': 0.15,
                'manipulation': 0.10,
                'emergency': component_weights.get('upgrade_weight', 0.10),
                'upgrade': component_weights.get('upgrade_weight', 0.20),
                'regulatory': component_weights.get('regulatory_weight', 0.15),
                'network': component_weights.get('network_weight', 0.20),
                'foundation': component_weights.get('systemic_weight', 0.10)
            }

            # Normalize weights
            total_weight = sum(weights.values())
            weights = {k: v/total_weight for k, v in weights.items()}

            # Calculate overall systemic risk (higher = more risk)
            overall_risk = (
                governance_score * weights['governance'] +
                voting_score * weights['voting'] +
                manipulation_score * weights['manipulation'] +
                (10 - emergency_score) * weights['emergency'] +  # Invert emergency score
                upgrade_score * weights['upgrade'] +
                regulatory_score * weights['regulatory'] +
                (10 - network_score) * weights['network'] +  # Invert network score
                foundation_score * weights['foundation']
            )

            # Calculate stability index (inverse of risk)
            stability_index = max(0, 10 - overall_risk)

            # Calculate resilience score (based on emergency readiness and network security)
            resilience_score = (emergency_score * 0.6 + network_score * 0.4)

            # Determine overall risk level
            overall_risk_level = self._determine_systemic_risk_level(overall_risk)

            # Component risk levels
            component_risk_levels = {
                'governance': self._score_to_risk_level(governance_score),
                'voting_concentration': self._score_to_risk_level(voting_score),
                'proposal_manipulation': self._score_to_risk_level(manipulation_score),
                'emergency_readiness': self._score_to_risk_level(10 - emergency_score),
                'upgrade_risks': self._score_to_risk_level(upgrade_score),
                'regulatory': self._score_to_risk_level(regulatory_score),
                'network_security': self._score_to_risk_level(10 - network_score),
                'foundation_dependency': self._score_to_risk_level(foundation_score)
            }

            # Trend analysis
            trend_direction, trend_confidence = self._analyze_overall_trend()

            return SystemicRiskMetrics(
                timestamp=datetime.utcnow(),
                governance_risk_score=governance_score,
                voting_concentration_score=voting_score,
                proposal_manipulation_score=manipulation_score,
                emergency_readiness_score=emergency_score,
                upgrade_risk_score=upgrade_score,
                regulatory_risk_score=regulatory_score,
                network_security_score=network_score,
                foundation_dependency_score=foundation_score,
                overall_systemic_risk=overall_risk,
                stability_index=stability_index,
                resilience_score=resilience_score,
                overall_risk_level=overall_risk_level,
                component_risk_levels=component_risk_levels,
                risk_trend_direction=trend_direction,
                trend_confidence=trend_confidence
            )

        except Exception as e:
            self.logger.error(f"Systemic metrics calculation failed: {e}")
            return self._create_default_systemic_metrics()

    def _extract_risk_score(self, component_result: Any, score_field: str) -> float:
        """Extract risk score from component result"""
        try:
            if component_result is None:
                return 5.0  # Default moderate risk

            if hasattr(component_result, score_field):
                return getattr(component_result, score_field)
            elif isinstance(component_result, dict):
                return component_result.get(score_field, 5.0)
            else:
                return 5.0

        except Exception as e:
            self.logger.error(f"Risk score extraction failed: {e}")
            return 5.0

    def _extract_voting_concentration_score(self, voting_result: Any) -> float:
        """Extract voting concentration risk score"""
        try:
            if voting_result is None:
                return 5.0

            if isinstance(voting_result, tuple):
                metrics, alerts = voting_result
                # Convert concentration metrics to risk score
                if hasattr(metrics, 'top_1_percentage'):
                    return min(10.0, metrics.top_1_percentage * 50)  # Scale to 0-10

            return 5.0

        except Exception as e:
            self.logger.error(f"Voting concentration score extraction failed: {e}")
            return 5.0

    def _extract_network_security_score(self, network_result: Any) -> float:
        """Extract network security score"""
        try:
            if network_result is None:
                return 5.0

            if isinstance(network_result, dict):
                return network_result.get('overall_security_score', 5.0)

            return 5.0

        except Exception as e:
            self.logger.error(f"Network security score extraction failed: {e}")
            return 5.0

    def _extract_foundation_dependency_score(self, foundation_result: Any) -> float:
        """Extract foundation dependency risk score"""
        try:
            if foundation_result is None:
                return 5.0

            if isinstance(foundation_result, dict):
                return foundation_result.get('overall_dependency_risk', 5.0)

            return 5.0

        except Exception as e:
            self.logger.error(f"Foundation dependency score extraction failed: {e}")
            return 5.0

    def _determine_systemic_risk_level(self, overall_risk: float) -> SystemicRiskLevel:
        """Determine systemic risk level from overall score"""
        if overall_risk >= 9.0:
            return SystemicRiskLevel.CATASTROPHIC
        elif overall_risk >= 8.0:
            return SystemicRiskLevel.CRITICAL
        elif overall_risk >= 6.5:
            return SystemicRiskLevel.HIGH
        elif overall_risk >= 4.5:
            return SystemicRiskLevel.MODERATE
        elif overall_risk >= 2.0:
            return SystemicRiskLevel.LOW
        else:
            return SystemicRiskLevel.MINIMAL

    def _score_to_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level string"""
        if score >= 8.0:
            return "critical"
        elif score >= 6.0:
            return "high"
        elif score >= 4.0:
            return "moderate"
        elif score >= 2.0:
            return "low"
        else:
            return "minimal"

    def _analyze_overall_trend(self) -> Tuple[str, float]:
        """Analyze overall risk trend direction"""
        try:
            if len(self.historical_assessments) < 2:
                return "stable", 0.5

            # Compare recent assessments
            recent_scores = [assessment['overall_risk'] for assessment in self.historical_assessments[-5:]]

            if len(recent_scores) < 2:
                return "stable", 0.5

            # Calculate trend
            trend_slope = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)

            if trend_slope > 0.5:
                return "increasing", min(1.0, abs(trend_slope) / 2)
            elif trend_slope < -0.5:
                return "decreasing", min(1.0, abs(trend_slope) / 2)
            else:
                return "stable", 0.8

        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return "stable", 0.5

    def _create_default_systemic_metrics(self) -> SystemicRiskMetrics:
        """Create default systemic metrics when calculation fails"""
        return SystemicRiskMetrics(
            timestamp=datetime.utcnow(),
            governance_risk_score=5.0,
            voting_concentration_score=5.0,
            proposal_manipulation_score=5.0,
            emergency_readiness_score=5.0,
            upgrade_risk_score=5.0,
            regulatory_risk_score=5.0,
            network_security_score=5.0,
            foundation_dependency_score=5.0,
            overall_systemic_risk=5.0,
            stability_index=5.0,
            resilience_score=5.0,
            overall_risk_level=SystemicRiskLevel.MODERATE,
            component_risk_levels={},
            risk_trend_direction="stable",
            trend_confidence=0.5
        )

    def _analyze_risk_correlations(self, component_results: Dict[str, Any]) -> Dict[str, float]:
        """Analyze correlations between risk components"""
        try:
            correlations = {}

            # Calculate correlations based on predefined relationships
            for component1, relationships in self.risk_correlations.items():
                for component2, base_correlation in relationships.items():
                    if component1 in component_results and component2 in component_results:
                        # Adjust correlation based on actual risk levels
                        score1 = self._extract_component_score(component_results[component1])
                        score2 = self._extract_component_score(component_results[component2])

                        # Higher correlation when both scores are high
                        risk_amplification = min(1.0, (score1 + score2) / 10)
                        adjusted_correlation = base_correlation * (0.5 + risk_amplification * 0.5)

                        correlations[f"{component1}_{component2}"] = adjusted_correlation

            return correlations

        except Exception as e:
            self.logger.error(f"Risk correlation analysis failed: {e}")
            return {}

    def _extract_component_score(self, component_result: Any) -> float:
        """Extract normalized score from component result"""
        try:
            if component_result is None:
                return 5.0

            # Try different score field names
            score_fields = ['overall_risk_score', 'risk_score', 'overall_dependency_risk', 'overall_security_score']

            for field in score_fields:
                if hasattr(component_result, field):
                    return getattr(component_result, field)
                elif isinstance(component_result, dict):
                    if field in component_result:
                        return component_result[field]

            return 5.0

        except Exception as e:
            self.logger.error(f"Component score extraction failed: {e}")
            return 5.0

    async def _analyze_cascade_risks(self,
                                   component_results: Dict[str, Any],
                                   systemic_metrics: SystemicRiskMetrics) -> Dict[str, Any]:
        """Analyze potential cascade risks between components"""
        try:
            cascade_risks = {
                'high_cascade_potential': [],
                'cascade_scenarios': [],
                'amplification_factors': {}
            }

            # Identify high-risk components that could trigger cascades
            high_risk_components = [
                component for component, risk_level in systemic_metrics.component_risk_levels.items()
                if risk_level in ['critical', 'high']
            ]

            # Analyze potential cascade scenarios
            for component in high_risk_components:
                cascade_scenario = {
                    'trigger_component': component,
                    'potential_impacts': [],
                    'cascade_probability': 0.0,
                    'mitigation_requirements': []
                }

                # Find components that could be affected
                for other_component, relationships in self.risk_correlations.items():
                    if component in relationships and relationships[component] > 0.6:
                        cascade_scenario['potential_impacts'].append(other_component)
                        cascade_scenario['cascade_probability'] += relationships[component] * 0.2

                if cascade_scenario['potential_impacts']:
                    cascade_risks['cascade_scenarios'].append(cascade_scenario)

            return cascade_risks

        except Exception as e:
            self.logger.error(f"Cascade risk analysis failed: {e}")
            return {}

    async def _assess_risk_scenarios(self,
                                   component_results: Dict[str, Any],
                                   systemic_metrics: SystemicRiskMetrics) -> List[Dict[str, Any]]:
        """Assess various risk scenarios"""
        try:
            scenarios = []

            # Scenario 1: Governance Crisis
            governance_crisis = {
                'scenario_name': 'Governance Crisis',
                'description': 'Major governance attack or manipulation event',
                'probability': 0.15,
                'impact_score': 8.5,
                'affected_components': ['governance', 'voting_concentration', 'proposal_manipulation'],
                'mitigation_requirements': [
                    'Emergency governance procedures',
                    'Enhanced voting security',
                    'Community coordination'
                ]
            }
            scenarios.append(governance_crisis)

            # Scenario 2: Regulatory Crackdown
            regulatory_crisis = {
                'scenario_name': 'Multi-Jurisdiction Regulatory Crackdown',
                'description': 'Coordinated regulatory action across major jurisdictions',
                'probability': 0.25,
                'impact_score': 7.0,
                'affected_components': ['regulatory', 'foundation_dependency', 'governance'],
                'mitigation_requirements': [
                    'Legal compliance framework',
                    'Jurisdiction diversification',
                    'Regulatory engagement'
                ]
            }
            scenarios.append(regulatory_crisis)

            # Scenario 3: Technical Crisis
            technical_crisis = {
                'scenario_name': 'Major Technical Failure',
                'description': 'Critical protocol vulnerability or consensus failure',
                'probability': 0.10,
                'impact_score': 9.0,
                'affected_components': ['network_security', 'upgrade_risks', 'emergency_readiness'],
                'mitigation_requirements': [
                    'Emergency response activation',
                    'Technical recovery procedures',
                    'Communication protocols'
                ]
            }
            scenarios.append(technical_crisis)

            return scenarios

        except Exception as e:
            self.logger.error(f"Risk scenario assessment failed: {e}")
            return []

    def _generate_systemic_alerts(self,
                                component_results: Dict[str, Any],
                                systemic_metrics: SystemicRiskMetrics) -> List[SystemicAlert]:
        """Generate systemic risk alerts"""
        alerts = []

        try:
            alert_counter = 0

            # Overall systemic risk alert
            if systemic_metrics.overall_risk_level in [SystemicRiskLevel.CRITICAL, SystemicRiskLevel.CATASTROPHIC]:
                alerts.append(SystemicAlert(
                    alert_id=f"systemic_alert_{alert_counter}",
                    alert_type="SYSTEMIC_RISK_CRITICAL",
                    severity="CRITICAL",
                    component="overall",
                    message=f"Critical systemic risk detected: {systemic_metrics.overall_risk_level.value}",
                    recommendations=[
                        "Activate emergency response procedures",
                        "Convene risk management committee",
                        "Implement immediate risk mitigation measures"
                    ],
                    timestamp=datetime.utcnow(),
                    requires_immediate_action=True
                ))
                alert_counter += 1

            # Component-specific alerts
            for component, risk_level in systemic_metrics.component_risk_levels.items():
                if risk_level in ['critical', 'high']:
                    alerts.append(SystemicAlert(
                        alert_id=f"component_alert_{alert_counter}",
                        alert_type=f"{component.upper()}_RISK_HIGH",
                        severity="HIGH" if risk_level == "high" else "CRITICAL",
                        component=component,
                        message=f"High {component} risk detected",
                        recommendations=[f"Address {component} risk factors immediately"],
                        timestamp=datetime.utcnow(),
                        requires_immediate_action=(risk_level == "critical")
                    ))
                    alert_counter += 1

            # Trend-based alerts
            if (systemic_metrics.risk_trend_direction == "increasing" and
                systemic_metrics.trend_confidence > 0.7):
                alerts.append(SystemicAlert(
                    alert_id=f"trend_alert_{alert_counter}",
                    alert_type="RISK_TREND_INCREASING",
                    severity="MODERATE",
                    component="trend",
                    message="Systemic risk trend is increasing",
                    recommendations=["Monitor risk trends closely", "Implement preventive measures"],
                    timestamp=datetime.utcnow(),
                    requires_immediate_action=False
                ))

            return alerts

        except Exception as e:
            self.logger.error(f"Systemic alert generation failed: {e}")
            return []

    def _generate_priority_recommendations(self,
                                         component_results: Dict[str, Any],
                                         systemic_metrics: SystemicRiskMetrics,
                                         active_alerts: List[SystemicAlert]) -> List[str]:
        """Generate priority recommendations for systemic risk mitigation"""
        recommendations = []

        try:
            # Critical systemic risk recommendations
            if systemic_metrics.overall_risk_level in [SystemicRiskLevel.CRITICAL, SystemicRiskLevel.CATASTROPHIC]:
                recommendations.extend([
                    "Implement emergency risk management protocols",
                    "Activate crisis communication procedures",
                    "Convene emergency governance committee"
                ])

            # Component-specific recommendations
            critical_components = [
                component for component, risk_level in systemic_metrics.component_risk_levels.items()
                if risk_level == "critical"
            ]

            for component in critical_components:
                if component == "governance":
                    recommendations.append("Implement enhanced governance security measures")
                elif component == "regulatory":
                    recommendations.append("Engage legal counsel for regulatory compliance")
                elif component == "network_security":
                    recommendations.append("Strengthen network security protocols")

            # Alert-based recommendations
            critical_alerts = [alert for alert in active_alerts if alert.severity == "CRITICAL"]
            for alert in critical_alerts:
                recommendations.extend(alert.recommendations[:1])  # Top recommendation per alert

            # General systemic recommendations
            recommendations.extend([
                "Enhance cross-component risk monitoring",
                "Develop integrated risk response procedures",
                "Improve ecosystem resilience mechanisms"
            ])

            # Remove duplicates and limit
            recommendations = list(dict.fromkeys(recommendations))
            return recommendations[:10]

        except Exception as e:
            self.logger.error(f"Priority recommendation generation failed: {e}")
            return ["Review systemic risk management procedures"]

    def _generate_monitoring_requirements(self, component_results: Dict[str, Any]) -> List[str]:
        """Generate monitoring requirements for systemic risk management"""
        requirements = [
            "Continuous monitoring of all risk components",
            "Real-time alert system for critical risk thresholds",
            "Daily systemic risk dashboard updates",
            "Weekly comprehensive risk assessment reports",
            "Monthly risk trend analysis and projections",
            "Quarterly systemic risk strategy review"
        ]

        return requirements

    async def _project_future_risks(self,
                                  component_results: Dict[str, Any],
                                  systemic_metrics: SystemicRiskMetrics) -> Dict[str, float]:
        """Project future risk levels based on current trends"""
        try:
            current_risk = systemic_metrics.overall_systemic_risk

            # Simple linear projection based on trend
            if systemic_metrics.risk_trend_direction == "increasing":
                trend_factor = 1.1
            elif systemic_metrics.risk_trend_direction == "decreasing":
                trend_factor = 0.9
            else:
                trend_factor = 1.0

            projections = {
                '7_days': min(10.0, current_risk * trend_factor),
                '30_days': min(10.0, current_risk * (trend_factor ** 2)),
                '90_days': min(10.0, current_risk * (trend_factor ** 3)),
                '180_days': min(10.0, current_risk * (trend_factor ** 4))
            }

            return projections

        except Exception as e:
            self.logger.error(f"Risk projection failed: {e}")
            return {}

    def _identify_early_warning_indicators(self,
                                         component_results: Dict[str, Any],
                                         systemic_metrics: SystemicRiskMetrics) -> List[str]:
        """Identify early warning indicators for systemic risks"""
        indicators = []

        try:
            # High overall risk indicator
            if systemic_metrics.overall_systemic_risk > 7.0:
                indicators.append("Overall systemic risk above warning threshold")

            # Low resilience indicator
            if systemic_metrics.resilience_score < 4.0:
                indicators.append("Low ecosystem resilience detected")

            # Multiple high-risk components
            high_risk_count = sum(1 for level in systemic_metrics.component_risk_levels.values()
                                if level in ['critical', 'high'])
            if high_risk_count > 2:
                indicators.append(f"Multiple components ({high_risk_count}) at high risk")

            # Trend indicators
            if (systemic_metrics.risk_trend_direction == "increasing" and
                systemic_metrics.trend_confidence > 0.8):
                indicators.append("Strong upward risk trend detected")

            return indicators

        except Exception as e:
            self.logger.error(f"Early warning indicator identification failed: {e}")
            return []

    def _create_executive_summary(self,
                                systemic_metrics: SystemicRiskMetrics,
                                active_alerts: List[SystemicAlert],
                                priority_recommendations: List[str]) -> Dict[str, Any]:
        """Create executive summary of systemic risk assessment"""
        try:
            critical_alerts = len([alert for alert in active_alerts if alert.severity == "CRITICAL"])
            high_alerts = len([alert for alert in active_alerts if alert.severity == "HIGH"])

            return {
                'overall_risk_level': systemic_metrics.overall_risk_level.value,
                'overall_risk_score': round(systemic_metrics.overall_systemic_risk, 2),
                'stability_index': round(systemic_metrics.stability_index, 2),
                'resilience_score': round(systemic_metrics.resilience_score, 2),
                'risk_trend': systemic_metrics.risk_trend_direction,
                'critical_alerts_count': critical_alerts,
                'high_alerts_count': high_alerts,
                'top_risks': [
                    component for component, level in systemic_metrics.component_risk_levels.items()
                    if level in ['critical', 'high']
                ][:3],
                'immediate_actions_required': critical_alerts > 0,
                'top_recommendations': priority_recommendations[:3]
            }

        except Exception as e:
            self.logger.error(f"Executive summary creation failed: {e}")
            return {'error': 'Failed to create executive summary'}

    def _store_assessment_results(self, report: SystemicRiskReport):
        """Store assessment results for historical analysis"""
        try:
            # Store summary data for trend analysis
            summary = {
                'timestamp': report.timestamp,
                'assessment_id': report.assessment_id,
                'overall_risk': report.systemic_metrics.overall_systemic_risk,
                'risk_level': report.systemic_metrics.overall_risk_level.value,
                'stability_index': report.systemic_metrics.stability_index,
                'critical_alerts': len([a for a in report.active_alerts if a.severity == "CRITICAL"])
            }

            self.historical_assessments.append(summary)

            # Keep only recent assessments (last 90 days)
            cutoff_time = datetime.utcnow() - timedelta(days=90)
            self.historical_assessments = [
                assessment for assessment in self.historical_assessments
                if assessment['timestamp'] > cutoff_time
            ]

            # Update active alerts
            self.active_alerts = report.active_alerts

        except Exception as e:
            self.logger.error(f"Failed to store assessment results: {e}")

    async def get_real_time_risk_status(self) -> Dict[str, Any]:
        """Get real-time risk status summary"""
        try:
            if not self.historical_assessments:
                return {'status': 'No assessments available'}

            latest = self.historical_assessments[-1]

            return {
                'current_risk_level': latest['risk_level'],
                'current_risk_score': latest['overall_risk'],
                'stability_index': latest['stability_index'],
                'active_critical_alerts': len([a for a in self.active_alerts if a.severity == "CRITICAL"]),
                'last_assessment': latest['timestamp'],
                'trend': self._calculate_recent_trend()
            }

        except Exception as e:
            self.logger.error(f"Real-time status retrieval failed: {e}")
            return {'status': 'Error retrieving status'}

    def _calculate_recent_trend(self) -> str:
        """Calculate recent risk trend"""
        try:
            if len(self.historical_assessments) < 3:
                return "insufficient_data"

            recent_scores = [a['overall_risk'] for a in self.historical_assessments[-3:]]
            if recent_scores[-1] > recent_scores[0] * 1.1:
                return "increasing"
            elif recent_scores[-1] < recent_scores[0] * 0.9:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            self.logger.error(f"Recent trend calculation failed: {e}")
            return "unknown"

# Export main classes
__all__ = ['SystemicRiskEngine', 'SystemicRiskReport', 'SystemicRiskMetrics', 'SystemicAlert', 'SystemicRiskLevel']