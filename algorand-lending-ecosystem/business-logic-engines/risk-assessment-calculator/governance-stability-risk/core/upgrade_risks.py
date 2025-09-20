"""
Protocol Upgrade Risk Assessment
Analyzes risks associated with protocol upgrades, coordination, and implementation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
import re
from collections import defaultdict

class UpgradeRiskLevel(Enum):
    """Protocol upgrade risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"

class UpgradeType(Enum):
    """Types of protocol upgrades"""
    CONSENSUS_CHANGE = "consensus_change"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    FEATURE_ADDITION = "feature_addition"
    BUG_FIX = "bug_fix"
    HARD_FORK = "hard_fork"
    SOFT_FORK = "soft_fork"
    EMERGENCY_PATCH = "emergency_patch"

class UpgradePhase(Enum):
    """Upgrade implementation phases"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    COMPLETED = "completed"

@dataclass
class UpgradeMetrics:
    """Metrics for a protocol upgrade"""
    upgrade_id: str
    name: str
    upgrade_type: UpgradeType
    current_phase: UpgradePhase

    # Timeline metrics
    planned_start: datetime
    planned_completion: datetime
    actual_start: Optional[datetime]
    estimated_completion: Optional[datetime]

    # Scope and impact
    lines_of_code_changed: int
    affected_components: List[str]
    breaking_changes: bool
    backward_compatibility: bool

    # Testing and validation
    test_coverage_percentage: float
    formal_verification_status: bool
    audit_completion_status: bool
    testnet_duration_days: int

    # Coordination requirements
    node_operator_coordination: bool
    dapp_developer_coordination: bool
    user_action_required: bool
    minimum_adoption_threshold: float

    # Risk indicators
    complexity_score: float
    dependency_count: int
    rollback_capability: bool
    emergency_deployment: bool

@dataclass
class UpgradeRisk:
    """Individual upgrade risk assessment"""
    risk_id: str
    risk_type: str
    risk_level: UpgradeRiskLevel
    probability: float  # 0-1
    impact_score: float  # 1-10
    affected_upgrades: List[str]
    mitigation_measures: List[str]
    contingency_plans: List[str]
    monitoring_requirements: List[str]
    description: str
    detected_at: datetime

@dataclass
class CoordinationRisk:
    """Coordination-specific risk assessment"""
    coordination_type: str
    stakeholder_groups: List[str]
    readiness_scores: Dict[str, float]
    communication_effectiveness: float
    timeline_alignment: float
    rollback_coordination: float
    emergency_response_capability: float

@dataclass
class UpgradeRiskReport:
    """Comprehensive upgrade risk assessment report"""
    timestamp: datetime
    total_active_upgrades: int
    overall_risk_score: float
    risk_level: UpgradeRiskLevel

    upgrade_metrics: List[UpgradeMetrics]
    identified_risks: List[UpgradeRisk]
    coordination_risks: List[CoordinationRisk]

    # Timeline analysis
    timeline_conflicts: List[Dict[str, Any]]
    critical_path_risks: List[str]

    # Recommendations
    immediate_actions: List[str]
    risk_mitigation_recommendations: List[str]
    monitoring_recommendations: List[str]

    next_assessment: datetime

class ProtocolUpgradeRiskAnalyzer:
    """Analyzes protocol upgrade risks and coordination challenges"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the protocol upgrade risk analyzer"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.upgrade_history = []
        self.risk_patterns = self._load_risk_patterns()
        self.stakeholder_readiness = {}

    def _load_risk_patterns(self) -> Dict[str, Any]:
        """Load historical upgrade risk patterns"""
        return {
            'high_risk_components': [
                'consensus_algorithm', 'cryptographic_primitives', 'state_machine',
                'network_protocol', 'smart_contract_vm', 'governance_mechanism'
            ],
            'complexity_indicators': [
                'multi_component_changes', 'cross_layer_modifications',
                'timing_sensitive_changes', 'cryptographic_updates'
            ],
            'coordination_challenges': [
                'node_operator_diversity', 'geographic_distribution',
                'stakeholder_alignment', 'communication_barriers'
            ]
        }

    async def assess_upgrade_risks(self,
                                 upgrade_data: Dict[str, Any]) -> UpgradeRiskReport:
        """
        Assess risks for all active protocol upgrades

        Args:
            upgrade_data: Current upgrade status and metrics

        Returns:
            UpgradeRiskReport: Comprehensive upgrade risk assessment
        """
        try:
            self.logger.info("Starting protocol upgrade risk assessment")

            # Process upgrade metrics
            upgrade_metrics = await self._process_upgrade_metrics(upgrade_data)

            # Identify and assess risks
            identified_risks = await self._identify_upgrade_risks(upgrade_metrics)

            # Assess coordination risks
            coordination_risks = await self._assess_coordination_risks(upgrade_metrics, upgrade_data)

            # Analyze timeline conflicts
            timeline_conflicts = self._analyze_timeline_conflicts(upgrade_metrics)

            # Identify critical path risks
            critical_path_risks = self._identify_critical_path_risks(upgrade_metrics, identified_risks)

            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_upgrade_risk(identified_risks, coordination_risks)
            risk_level = self._determine_risk_level(overall_risk_score)

            # Generate recommendations
            immediate_actions = self._generate_immediate_actions(identified_risks, timeline_conflicts)
            mitigation_recommendations = self._generate_mitigation_recommendations(identified_risks)
            monitoring_recommendations = self._generate_monitoring_recommendations(upgrade_metrics)

            report = UpgradeRiskReport(
                timestamp=datetime.utcnow(),
                total_active_upgrades=len(upgrade_metrics),
                overall_risk_score=overall_risk_score,
                risk_level=risk_level,
                upgrade_metrics=upgrade_metrics,
                identified_risks=identified_risks,
                coordination_risks=coordination_risks,
                timeline_conflicts=timeline_conflicts,
                critical_path_risks=critical_path_risks,
                immediate_actions=immediate_actions,
                risk_mitigation_recommendations=mitigation_recommendations,
                monitoring_recommendations=monitoring_recommendations,
                next_assessment=datetime.utcnow() + timedelta(days=1)
            )

            self.logger.info(f"Upgrade risk assessment completed. Overall risk: {risk_level.value}")
            return report

        except Exception as e:
            self.logger.error(f"Upgrade risk assessment failed: {e}")
            raise

    async def _process_upgrade_metrics(self, upgrade_data: Dict[str, Any]) -> List[UpgradeMetrics]:
        """Process raw upgrade data into structured metrics"""
        metrics_list = []

        try:
            upgrades = upgrade_data.get('active_upgrades', [])

            for upgrade_info in upgrades:
                # Parse dates
                planned_start = self._parse_datetime(upgrade_info.get('planned_start'))
                planned_completion = self._parse_datetime(upgrade_info.get('planned_completion'))
                actual_start = self._parse_datetime(upgrade_info.get('actual_start'))
                estimated_completion = self._parse_datetime(upgrade_info.get('estimated_completion'))

                # Parse upgrade type and phase
                upgrade_type = UpgradeType(upgrade_info.get('type', 'feature_addition'))
                current_phase = UpgradePhase(upgrade_info.get('phase', 'planning'))

                # Calculate complexity score
                complexity_score = self._calculate_complexity_score(upgrade_info)

                metrics = UpgradeMetrics(
                    upgrade_id=upgrade_info.get('id', ''),
                    name=upgrade_info.get('name', ''),
                    upgrade_type=upgrade_type,
                    current_phase=current_phase,
                    planned_start=planned_start,
                    planned_completion=planned_completion,
                    actual_start=actual_start,
                    estimated_completion=estimated_completion,
                    lines_of_code_changed=upgrade_info.get('code_changes', 0),
                    affected_components=upgrade_info.get('affected_components', []),
                    breaking_changes=upgrade_info.get('breaking_changes', False),
                    backward_compatibility=upgrade_info.get('backward_compatibility', True),
                    test_coverage_percentage=upgrade_info.get('test_coverage', 0.0),
                    formal_verification_status=upgrade_info.get('formal_verification', False),
                    audit_completion_status=upgrade_info.get('audit_completed', False),
                    testnet_duration_days=upgrade_info.get('testnet_days', 0),
                    node_operator_coordination=upgrade_info.get('node_coordination_required', False),
                    dapp_developer_coordination=upgrade_info.get('dapp_coordination_required', False),
                    user_action_required=upgrade_info.get('user_action_required', False),
                    minimum_adoption_threshold=upgrade_info.get('adoption_threshold', 0.67),
                    complexity_score=complexity_score,
                    dependency_count=len(upgrade_info.get('dependencies', [])),
                    rollback_capability=upgrade_info.get('rollback_possible', True),
                    emergency_deployment=upgrade_info.get('emergency', False)
                )

                metrics_list.append(metrics)

            return metrics_list

        except Exception as e:
            self.logger.error(f"Failed to process upgrade metrics: {e}")
            return []

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string safely"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _calculate_complexity_score(self, upgrade_info: Dict[str, Any]) -> float:
        """Calculate upgrade complexity score"""
        try:
            score = 0.0

            # Code change complexity
            code_changes = upgrade_info.get('code_changes', 0)
            score += min(3.0, code_changes / 1000)  # Normalize by thousands of lines

            # Component complexity
            affected_components = upgrade_info.get('affected_components', [])
            high_risk_components = self.risk_patterns['high_risk_components']
            critical_components = len([c for c in affected_components if c in high_risk_components])
            score += critical_components * 1.5

            # Breaking changes penalty
            if upgrade_info.get('breaking_changes', False):
                score += 2.0

            # Dependency complexity
            dependencies = upgrade_info.get('dependencies', [])
            score += min(2.0, len(dependencies) * 0.3)

            # Emergency deployment risk
            if upgrade_info.get('emergency', False):
                score += 1.5

            return min(10.0, score)

        except Exception as e:
            self.logger.error(f"Complexity score calculation failed: {e}")
            return 5.0

    async def _identify_upgrade_risks(self, upgrade_metrics: List[UpgradeMetrics]) -> List[UpgradeRisk]:
        """Identify specific upgrade risks"""
        risks = []

        try:
            for upgrade in upgrade_metrics:
                # Testing inadequacy risk
                if upgrade.test_coverage_percentage < 80.0:
                    risks.append(self._create_testing_risk(upgrade))

                # Timeline risk
                if self._has_timeline_risk(upgrade):
                    risks.append(self._create_timeline_risk(upgrade))

                # Complexity risk
                if upgrade.complexity_score > 7.0:
                    risks.append(self._create_complexity_risk(upgrade))

                # Coordination risk
                if self._has_coordination_risk(upgrade):
                    risks.append(self._create_coordination_risk_item(upgrade))

                # Breaking changes risk
                if upgrade.breaking_changes and not upgrade.backward_compatibility:
                    risks.append(self._create_breaking_changes_risk(upgrade))

                # Audit risk
                if not upgrade.audit_completion_status and upgrade.complexity_score > 5.0:
                    risks.append(self._create_audit_risk(upgrade))

                # Rollback risk
                if not upgrade.rollback_capability:
                    risks.append(self._create_rollback_risk(upgrade))

                # Emergency deployment risk
                if upgrade.emergency_deployment:
                    risks.append(self._create_emergency_deployment_risk(upgrade))

            return risks

        except Exception as e:
            self.logger.error(f"Risk identification failed: {e}")
            return []

    def _create_testing_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create testing inadequacy risk"""
        return UpgradeRisk(
            risk_id=f"testing_{upgrade.upgrade_id}",
            risk_type="TESTING_INADEQUACY",
            risk_level=UpgradeRiskLevel.HIGH if upgrade.test_coverage_percentage < 60 else UpgradeRiskLevel.MODERATE,
            probability=0.8,
            impact_score=7.0,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Increase test coverage to minimum 90%",
                "Implement comprehensive integration testing",
                "Add stress testing scenarios"
            ],
            contingency_plans=[
                "Prepare immediate rollback procedure",
                "Establish hotfix deployment capability"
            ],
            monitoring_requirements=[
                "Monitor error rates post-deployment",
                "Track performance metrics continuously"
            ],
            description=f"Test coverage at {upgrade.test_coverage_percentage:.1f}% below recommended threshold",
            detected_at=datetime.utcnow()
        )

    def _has_timeline_risk(self, upgrade: UpgradeMetrics) -> bool:
        """Check if upgrade has timeline risks"""
        if not upgrade.planned_completion:
            return False

        now = datetime.utcnow()

        # Check if already behind schedule
        if upgrade.actual_start and upgrade.planned_start:
            delay = (upgrade.actual_start - upgrade.planned_start).days
            if delay > 7:  # More than a week delay
                return True

        # Check if timeline is too aggressive
        if upgrade.planned_completion and upgrade.planned_start:
            duration = (upgrade.planned_completion - upgrade.planned_start).days
            if duration < 30 and upgrade.complexity_score > 6.0:  # Less than 30 days for complex upgrade
                return True

        return False

    def _create_timeline_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create timeline-related risk"""
        return UpgradeRisk(
            risk_id=f"timeline_{upgrade.upgrade_id}",
            risk_type="TIMELINE_PRESSURE",
            risk_level=UpgradeRiskLevel.MODERATE,
            probability=0.6,
            impact_score=6.0,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Extend timeline for adequate testing",
                "Prioritize critical components only",
                "Implement phased deployment approach"
            ],
            contingency_plans=[
                "Prepare scope reduction options",
                "Plan deployment postponement if needed"
            ],
            monitoring_requirements=[
                "Track development milestone progress",
                "Monitor team stress indicators"
            ],
            description="Timeline pressure may compromise upgrade quality",
            detected_at=datetime.utcnow()
        )

    def _create_complexity_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create complexity-related risk"""
        return UpgradeRisk(
            risk_id=f"complexity_{upgrade.upgrade_id}",
            risk_type="HIGH_COMPLEXITY",
            risk_level=UpgradeRiskLevel.HIGH,
            probability=0.7,
            impact_score=8.0,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Break down into smaller components",
                "Increase formal verification requirements",
                "Extend testing and review periods"
            ],
            contingency_plans=[
                "Prepare component-by-component rollback",
                "Establish expert review committee"
            ],
            monitoring_requirements=[
                "Enhanced monitoring of all affected systems",
                "Real-time performance tracking"
            ],
            description=f"High complexity score: {upgrade.complexity_score:.1f}/10",
            detected_at=datetime.utcnow()
        )

    def _has_coordination_risk(self, upgrade: UpgradeMetrics) -> bool:
        """Check if upgrade has coordination risks"""
        coordination_factors = [
            upgrade.node_operator_coordination,
            upgrade.dapp_developer_coordination,
            upgrade.user_action_required
        ]

        return sum(coordination_factors) >= 2  # Multiple coordination requirements

    def _create_coordination_risk_item(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create coordination-related risk"""
        return UpgradeRisk(
            risk_id=f"coordination_{upgrade.upgrade_id}",
            risk_type="COORDINATION_CHALLENGE",
            risk_level=UpgradeRiskLevel.MODERATE,
            probability=0.5,
            impact_score=7.0,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Establish clear communication channels",
                "Provide comprehensive migration guides",
                "Implement phased rollout strategy"
            ],
            contingency_plans=[
                "Prepare extended transition period",
                "Plan fallback to previous version"
            ],
            monitoring_requirements=[
                "Track adoption rates by stakeholder group",
                "Monitor support channel activity"
            ],
            description="Multiple stakeholder groups require coordination",
            detected_at=datetime.utcnow()
        )

    def _create_breaking_changes_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create breaking changes risk"""
        return UpgradeRisk(
            risk_id=f"breaking_{upgrade.upgrade_id}",
            risk_type="BREAKING_CHANGES",
            risk_level=UpgradeRiskLevel.HIGH,
            probability=0.9,
            impact_score=8.0,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Provide comprehensive migration documentation",
                "Implement gradual deprecation process",
                "Offer backward compatibility layer"
            ],
            contingency_plans=[
                "Maintain parallel legacy support",
                "Prepare expedited compatibility patches"
            ],
            monitoring_requirements=[
                "Track application compatibility issues",
                "Monitor user migration progress"
            ],
            description="Breaking changes without backward compatibility",
            detected_at=datetime.utcnow()
        )

    def _create_audit_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create audit-related risk"""
        return UpgradeRisk(
            risk_id=f"audit_{upgrade.upgrade_id}",
            risk_type="AUDIT_INCOMPLETE",
            risk_level=UpgradeRiskLevel.HIGH,
            probability=0.8,
            impact_score=7.5,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Complete security audit before deployment",
                "Engage multiple audit firms",
                "Implement formal verification where possible"
            ],
            contingency_plans=[
                "Delay deployment until audit completion",
                "Implement enhanced monitoring"
            ],
            monitoring_requirements=[
                "Continuous security monitoring",
                "Anomaly detection systems"
            ],
            description="Complex upgrade lacks completed security audit",
            detected_at=datetime.utcnow()
        )

    def _create_rollback_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create rollback capability risk"""
        return UpgradeRisk(
            risk_id=f"rollback_{upgrade.upgrade_id}",
            risk_type="NO_ROLLBACK",
            risk_level=UpgradeRiskLevel.CRITICAL,
            probability=1.0,
            impact_score=9.0,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Develop rollback mechanism before deployment",
                "Test rollback procedures thoroughly",
                "Implement state migration safeguards"
            ],
            contingency_plans=[
                "Prepare manual recovery procedures",
                "Establish emergency response team"
            ],
            monitoring_requirements=[
                "Real-time system health monitoring",
                "Automated failure detection"
            ],
            description="Upgrade cannot be rolled back if issues occur",
            detected_at=datetime.utcnow()
        )

    def _create_emergency_deployment_risk(self, upgrade: UpgradeMetrics) -> UpgradeRisk:
        """Create emergency deployment risk"""
        return UpgradeRisk(
            risk_id=f"emergency_{upgrade.upgrade_id}",
            risk_type="EMERGENCY_DEPLOYMENT",
            risk_level=UpgradeRiskLevel.CRITICAL,
            probability=0.9,
            impact_score=8.5,
            affected_upgrades=[upgrade.upgrade_id],
            mitigation_measures=[
                "Expedite critical testing only",
                "Engage emergency review committee",
                "Prepare immediate hotfix capability"
            ],
            contingency_plans=[
                "Plan immediate rollback if needed",
                "Prepare communication for users"
            ],
            monitoring_requirements=[
                "Enhanced real-time monitoring",
                "Dedicated incident response team"
            ],
            description="Emergency deployment bypasses normal safety processes",
            detected_at=datetime.utcnow()
        )

    async def _assess_coordination_risks(self,
                                       upgrade_metrics: List[UpgradeMetrics],
                                       upgrade_data: Dict[str, Any]) -> List[CoordinationRisk]:
        """Assess coordination-specific risks"""
        coordination_risks = []

        try:
            # Node operator coordination
            node_coordination_risk = await self._assess_node_operator_coordination(upgrade_metrics, upgrade_data)
            if node_coordination_risk:
                coordination_risks.append(node_coordination_risk)

            # DApp developer coordination
            dapp_coordination_risk = await self._assess_dapp_coordination(upgrade_metrics, upgrade_data)
            if dapp_coordination_risk:
                coordination_risks.append(dapp_coordination_risk)

            # User coordination
            user_coordination_risk = await self._assess_user_coordination(upgrade_metrics, upgrade_data)
            if user_coordination_risk:
                coordination_risks.append(user_coordination_risk)

            return coordination_risks

        except Exception as e:
            self.logger.error(f"Coordination risk assessment failed: {e}")
            return []

    async def _assess_node_operator_coordination(self,
                                               upgrade_metrics: List[UpgradeMetrics],
                                               upgrade_data: Dict[str, Any]) -> Optional[CoordinationRisk]:
        """Assess node operator coordination risks"""
        try:
            node_upgrades = [u for u in upgrade_metrics if u.node_operator_coordination]

            if not node_upgrades:
                return None

            # Get node operator readiness data
            node_data = upgrade_data.get('node_operators', {})

            readiness_scores = {
                'preparation': node_data.get('preparation_score', 0.7),
                'communication': node_data.get('communication_score', 0.6),
                'technical_capability': node_data.get('technical_score', 0.8),
                'geographic_distribution': node_data.get('distribution_score', 0.5)
            }

            communication_effectiveness = np.mean([
                node_data.get('announcement_reach', 0.7),
                node_data.get('feedback_response_rate', 0.5),
                node_data.get('documentation_quality', 0.8)
            ])

            return CoordinationRisk(
                coordination_type="NODE_OPERATORS",
                stakeholder_groups=["relay_nodes", "participation_nodes", "archival_nodes"],
                readiness_scores=readiness_scores,
                communication_effectiveness=communication_effectiveness,
                timeline_alignment=node_data.get('timeline_alignment', 0.6),
                rollback_coordination=node_data.get('rollback_capability', 0.7),
                emergency_response_capability=node_data.get('emergency_response', 0.5)
            )

        except Exception as e:
            self.logger.error(f"Node operator coordination assessment failed: {e}")
            return None

    async def _assess_dapp_coordination(self,
                                      upgrade_metrics: List[UpgradeMetrics],
                                      upgrade_data: Dict[str, Any]) -> Optional[CoordinationRisk]:
        """Assess DApp developer coordination risks"""
        try:
            dapp_upgrades = [u for u in upgrade_metrics if u.dapp_developer_coordination]

            if not dapp_upgrades:
                return None

            dapp_data = upgrade_data.get('dapp_developers', {})

            readiness_scores = {
                'api_migration': dapp_data.get('api_readiness', 0.6),
                'testing_completion': dapp_data.get('testing_progress', 0.4),
                'deployment_readiness': dapp_data.get('deployment_readiness', 0.5)
            }

            return CoordinationRisk(
                coordination_type="DAPP_DEVELOPERS",
                stakeholder_groups=["defi_protocols", "nft_platforms", "infrastructure_apps"],
                readiness_scores=readiness_scores,
                communication_effectiveness=dapp_data.get('communication_score', 0.7),
                timeline_alignment=dapp_data.get('timeline_alignment', 0.5),
                rollback_coordination=dapp_data.get('rollback_plans', 0.3),
                emergency_response_capability=dapp_data.get('emergency_response', 0.4)
            )

        except Exception as e:
            self.logger.error(f"DApp coordination assessment failed: {e}")
            return None

    async def _assess_user_coordination(self,
                                      upgrade_metrics: List[UpgradeMetrics],
                                      upgrade_data: Dict[str, Any]) -> Optional[CoordinationRisk]:
        """Assess user coordination risks"""
        try:
            user_upgrades = [u for u in upgrade_metrics if u.user_action_required]

            if not user_upgrades:
                return None

            user_data = upgrade_data.get('users', {})

            readiness_scores = {
                'awareness': user_data.get('awareness_level', 0.3),
                'wallet_compatibility': user_data.get('wallet_readiness', 0.7),
                'migration_readiness': user_data.get('migration_readiness', 0.2)
            }

            return CoordinationRisk(
                coordination_type="USERS",
                stakeholder_groups=["retail_users", "institutional_users", "developers"],
                readiness_scores=readiness_scores,
                communication_effectiveness=user_data.get('communication_reach', 0.4),
                timeline_alignment=user_data.get('timeline_understanding', 0.3),
                rollback_coordination=user_data.get('rollback_awareness', 0.1),
                emergency_response_capability=user_data.get('emergency_communication', 0.2)
            )

        except Exception as e:
            self.logger.error(f"User coordination assessment failed: {e}")
            return None

    def _analyze_timeline_conflicts(self, upgrade_metrics: List[UpgradeMetrics]) -> List[Dict[str, Any]]:
        """Analyze timeline conflicts between upgrades"""
        conflicts = []

        try:
            for i, upgrade1 in enumerate(upgrade_metrics):
                for upgrade2 in upgrade_metrics[i+1:]:
                    conflict = self._check_timeline_conflict(upgrade1, upgrade2)
                    if conflict:
                        conflicts.append(conflict)

            return conflicts

        except Exception as e:
            self.logger.error(f"Timeline conflict analysis failed: {e}")
            return []

    def _check_timeline_conflict(self, upgrade1: UpgradeMetrics, upgrade2: UpgradeMetrics) -> Optional[Dict[str, Any]]:
        """Check for timeline conflict between two upgrades"""
        try:
            if not (upgrade1.planned_start and upgrade1.planned_completion and
                    upgrade2.planned_start and upgrade2.planned_completion):
                return None

            # Check for overlap
            overlap_start = max(upgrade1.planned_start, upgrade2.planned_start)
            overlap_end = min(upgrade1.planned_completion, upgrade2.planned_completion)

            if overlap_start < overlap_end:
                overlap_days = (overlap_end - overlap_start).days

                # Check for resource conflicts
                component_overlap = set(upgrade1.affected_components).intersection(
                    set(upgrade2.affected_components)
                )

                if component_overlap or overlap_days > 7:  # Significant overlap
                    return {
                        'upgrade1': upgrade1.upgrade_id,
                        'upgrade2': upgrade2.upgrade_id,
                        'conflict_type': 'timeline_overlap',
                        'overlap_days': overlap_days,
                        'conflicting_components': list(component_overlap),
                        'severity': 'high' if component_overlap else 'moderate'
                    }

            return None

        except Exception as e:
            self.logger.error(f"Timeline conflict check failed: {e}")
            return None

    def _identify_critical_path_risks(self,
                                    upgrade_metrics: List[UpgradeMetrics],
                                    identified_risks: List[UpgradeRisk]) -> List[str]:
        """Identify critical path risks"""
        critical_risks = []

        try:
            # Find upgrades on critical path (emergency or high-impact)
            critical_upgrades = [
                u for u in upgrade_metrics
                if u.emergency_deployment or u.complexity_score > 8.0 or not u.rollback_capability
            ]

            # Find high-severity risks affecting critical upgrades
            for risk in identified_risks:
                if (risk.risk_level in [UpgradeRiskLevel.CRITICAL, UpgradeRiskLevel.HIGH] and
                    any(upgrade_id in [u.upgrade_id for u in critical_upgrades]
                        for upgrade_id in risk.affected_upgrades)):

                    critical_risks.append(f"{risk.risk_type}: {risk.description}")

            return critical_risks

        except Exception as e:
            self.logger.error(f"Critical path risk identification failed: {e}")
            return []

    def _calculate_overall_upgrade_risk(self,
                                      identified_risks: List[UpgradeRisk],
                                      coordination_risks: List[CoordinationRisk]) -> float:
        """Calculate overall upgrade risk score"""
        try:
            if not identified_risks and not coordination_risks:
                return 0.0

            # Weight individual risks
            risk_scores = []
            for risk in identified_risks:
                severity_weight = {
                    UpgradeRiskLevel.CRITICAL: 10,
                    UpgradeRiskLevel.HIGH: 7,
                    UpgradeRiskLevel.MODERATE: 4,
                    UpgradeRiskLevel.LOW: 2,
                    UpgradeRiskLevel.MINIMAL: 1
                }

                risk_score = risk.probability * risk.impact_score * severity_weight.get(risk.risk_level, 1) / 10
                risk_scores.append(risk_score)

            # Weight coordination risks
            coordination_scores = []
            for coord_risk in coordination_risks:
                avg_readiness = np.mean(list(coord_risk.readiness_scores.values()))
                coordination_score = (1 - avg_readiness) * coord_risk.communication_effectiveness * 8
                coordination_scores.append(coordination_score)

            # Combine scores
            total_risk_score = sum(risk_scores)
            total_coordination_score = sum(coordination_scores)

            # Normalize to 0-10 scale
            overall_score = min(10.0, (total_risk_score * 0.7 + total_coordination_score * 0.3))

            return overall_score

        except Exception as e:
            self.logger.error(f"Overall risk score calculation failed: {e}")
            return 5.0

    def _determine_risk_level(self, risk_score: float) -> UpgradeRiskLevel:
        """Determine risk level from numeric score"""
        if risk_score >= 8.0:
            return UpgradeRiskLevel.CRITICAL
        elif risk_score >= 6.0:
            return UpgradeRiskLevel.HIGH
        elif risk_score >= 4.0:
            return UpgradeRiskLevel.MODERATE
        elif risk_score >= 2.0:
            return UpgradeRiskLevel.LOW
        else:
            return UpgradeRiskLevel.MINIMAL

    def _generate_immediate_actions(self,
                                  identified_risks: List[UpgradeRisk],
                                  timeline_conflicts: List[Dict[str, Any]]) -> List[str]:
        """Generate immediate action recommendations"""
        actions = []

        try:
            # Critical risk actions
            critical_risks = [r for r in identified_risks if r.risk_level == UpgradeRiskLevel.CRITICAL]
            if critical_risks:
                actions.append("Address critical upgrade risks immediately")
                actions.append("Consider postponing non-essential upgrades")

            # Timeline conflict actions
            if timeline_conflicts:
                high_severity_conflicts = [c for c in timeline_conflicts if c.get('severity') == 'high']
                if high_severity_conflicts:
                    actions.append("Resolve high-severity timeline conflicts")

            # Emergency deployment actions
            emergency_risks = [r for r in identified_risks if 'EMERGENCY' in r.risk_type]
            if emergency_risks:
                actions.append("Activate emergency response procedures")
                actions.append("Increase monitoring and incident response readiness")

            return actions[:5]  # Limit to top 5 actions

        except Exception as e:
            self.logger.error(f"Immediate action generation failed: {e}")
            return ["Review upgrade risks and timeline"]

    def _generate_mitigation_recommendations(self, identified_risks: List[UpgradeRisk]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        try:
            # Aggregate mitigation measures
            all_mitigations = []
            for risk in identified_risks:
                all_mitigations.extend(risk.mitigation_measures)

            # Count frequency and prioritize
            from collections import Counter
            mitigation_counts = Counter(all_mitigations)

            # Top mitigation recommendations
            top_mitigations = [mitigation for mitigation, count in mitigation_counts.most_common(7)]
            recommendations.extend(top_mitigations)

            return recommendations

        except Exception as e:
            self.logger.error(f"Mitigation recommendation generation failed: {e}")
            return ["Implement comprehensive upgrade risk management"]

    def _generate_monitoring_recommendations(self, upgrade_metrics: List[UpgradeMetrics]) -> List[str]:
        """Generate monitoring recommendations"""
        recommendations = [
            "Implement real-time upgrade progress tracking",
            "Monitor stakeholder readiness indicators",
            "Track coordination effectiveness metrics",
            "Set up automated risk threshold alerts",
            "Establish upgrade rollback monitoring"
        ]

        # Add specific recommendations based on upgrade types
        upgrade_types = {upgrade.upgrade_type for upgrade in upgrade_metrics}

        if UpgradeType.CONSENSUS_CHANGE in upgrade_types:
            recommendations.append("Monitor consensus participation rates closely")

        if UpgradeType.SECURITY_FIX in upgrade_types:
            recommendations.append("Implement enhanced security monitoring")

        return recommendations[:6]

# Export main classes
__all__ = ['ProtocolUpgradeRiskAnalyzer', 'UpgradeRiskReport', 'UpgradeMetrics', 'UpgradeRisk', 'CoordinationRisk', 'UpgradeRiskLevel', 'UpgradeType']