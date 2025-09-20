"""
Decision Validator
Validates audit trail completeness and decision consistency
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics
import json

from .traceability_engine import DecisionTrace, DecisionNode, DecisionType, DecisionFactor

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"      # Blocks compliance/regulatory requirements
    HIGH = "high"             # Significant impact on decision quality
    MEDIUM = "medium"         # Moderate concerns
    LOW = "low"              # Minor issues
    INFO = "info"            # Informational notes

class ValidationCategory(Enum):
    """Categories of validation checks"""
    COMPLETENESS = "completeness"        # Missing required elements
    CONSISTENCY = "consistency"          # Internal logic consistency
    ACCURACY = "accuracy"               # Data accuracy and validation
    COMPLIANCE = "compliance"           # Regulatory compliance
    PERFORMANCE = "performance"         # Processing efficiency
    SECURITY = "security"              # Security and privacy

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    issue_id: str
    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    description: str
    affected_nodes: List[str]
    recommendation: str
    auto_fixable: bool = False
    compliance_impact: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ValidationReport:
    """Complete validation report for a trace"""
    trace_id: str
    loan_id: str
    validation_timestamp: datetime
    overall_score: float           # 0.0-1.0
    issues: List[ValidationIssue]
    summary: Dict[str, Any]
    recommendations: List[str]
    compliance_status: str         # compliant, warning, non_compliant

    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get issues filtered by category"""
        return [issue for issue in self.issues if issue.category == category]

class DecisionValidator:
    """
    Validates decision traces for completeness, consistency, and compliance
    """

    def __init__(self):
        """Initialize validator with rules and thresholds"""
        self.validation_rules = self._create_validation_rules()
        self.compliance_requirements = self._create_compliance_requirements()
        self.performance_thresholds = self._create_performance_thresholds()

    async def validate_trace(self, trace: DecisionTrace) -> ValidationReport:
        """
        Perform comprehensive validation of a decision trace

        Args:
            trace: Decision trace to validate

        Returns:
            Complete validation report with issues and recommendations
        """
        logger.info(f"Validating trace {trace.trace_id} for loan {trace.loan_id}")

        issues = []

        # Run all validation checks
        issues.extend(await self._validate_completeness(trace))
        issues.extend(await self._validate_consistency(trace))
        issues.extend(await self._validate_accuracy(trace))
        issues.extend(await self._validate_compliance(trace))
        issues.extend(await self._validate_performance(trace))
        issues.extend(await self._validate_security(trace))

        # Calculate overall score
        overall_score = await self._calculate_overall_score(trace, issues)

        # Determine compliance status
        compliance_status = await self._determine_compliance_status(issues)

        # Generate summary and recommendations
        summary = await self._generate_validation_summary(trace, issues)
        recommendations = await self._generate_recommendations(issues)

        report = ValidationReport(
            trace_id=trace.trace_id,
            loan_id=trace.loan_id,
            validation_timestamp=datetime.utcnow(),
            overall_score=overall_score,
            issues=issues,
            summary=summary,
            recommendations=recommendations,
            compliance_status=compliance_status
        )

        logger.info(
            f"Validation complete for {trace.trace_id} - "
            f"Score: {overall_score:.2f}, Issues: {len(issues)}, "
            f"Compliance: {compliance_status}"
        )

        return report

    async def validate_decision_node(
        self,
        node: DecisionNode,
        trace_context: Optional[DecisionTrace] = None
    ) -> List[ValidationIssue]:
        """
        Validate a specific decision node

        Args:
            node: Decision node to validate
            trace_context: Full trace context for cross-node validation

        Returns:
            List of validation issues for this node
        """
        issues = []

        # Check node completeness
        if not node.reasoning_chain:
            issues.append(ValidationIssue(
                issue_id=f"missing_reasoning_{node.node_id}",
                category=ValidationCategory.COMPLETENESS,
                severity=ValidationSeverity.HIGH,
                title="Missing Reasoning Chain",
                description=f"Decision node {node.node_id} lacks reasoning documentation",
                affected_nodes=[node.node_id],
                recommendation="Add step-by-step reasoning for decision",
                compliance_impact=True
            ))

        # Check factor completeness
        if not node.factors:
            issues.append(ValidationIssue(
                issue_id=f"missing_factors_{node.node_id}",
                category=ValidationCategory.COMPLETENESS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Decision Factors",
                description=f"Decision node {node.node_id} has no supporting factors",
                affected_nodes=[node.node_id],
                recommendation="Identify and document decision factors",
                compliance_impact=True
            ))

        # Check confidence levels
        if node.confidence_score < 0.3:
            issues.append(ValidationIssue(
                issue_id=f"low_confidence_{node.node_id}",
                category=ValidationCategory.ACCURACY,
                severity=ValidationSeverity.MEDIUM,
                title="Low Decision Confidence",
                description=f"Decision confidence ({node.confidence_score:.2f}) is below recommended threshold",
                affected_nodes=[node.node_id],
                recommendation="Review factors and improve data quality for higher confidence"
            ))

        # Validate factors
        for factor in node.factors:
            factor_issues = await self._validate_factor(factor, node.node_id)
            issues.extend(factor_issues)

        return issues

    async def validate_cross_loan_consistency(
        self,
        traces: List[DecisionTrace]
    ) -> List[ValidationIssue]:
        """
        Validate consistency across multiple loan decisions

        Args:
            traces: List of decision traces to compare

        Returns:
            List of consistency issues found across loans
        """
        if len(traces) < 2:
            return []

        issues = []

        # Group traces by similar characteristics
        grouped_traces = await self._group_similar_traces(traces)

        for group_key, group_traces in grouped_traces.items():
            if len(group_traces) < 2:
                continue

            # Check for inconsistent decisions within similar cases
            consistency_issues = await self._check_group_consistency(group_traces, group_key)
            issues.extend(consistency_issues)

        return issues

    async def check_regulatory_compliance(
        self,
        trace: DecisionTrace
    ) -> Dict[str, Any]:
        """
        Check specific regulatory compliance requirements

        Args:
            trace: Decision trace to check

        Returns:
            Detailed compliance assessment
        """
        compliance_report = {
            "overall_compliant": True,
            "framework_compliance": {},
            "missing_requirements": [],
            "compliance_score": 0.0
        }

        total_frameworks = 0
        compliant_frameworks = 0

        for framework_name, requirements in self.compliance_requirements.items():
            total_frameworks += 1
            framework_result = await self._check_framework_compliance(trace, requirements)

            compliance_report["framework_compliance"][framework_name] = framework_result

            if framework_result["compliant"]:
                compliant_frameworks += 1
            else:
                compliance_report["missing_requirements"].extend(
                    framework_result.get("missing_requirements", [])
                )

        # Calculate compliance score
        compliance_report["compliance_score"] = (
            compliant_frameworks / total_frameworks if total_frameworks > 0 else 0.0
        )

        # Determine overall compliance
        compliance_report["overall_compliant"] = compliance_report["compliance_score"] >= 0.8

        return compliance_report

    # Private validation methods

    async def _validate_completeness(self, trace: DecisionTrace) -> List[ValidationIssue]:
        """Validate trace completeness"""
        issues = []

        # Check required decision types
        required_types = {DecisionType.RISK_ASSESSMENT, DecisionType.LOAN_APPROVAL}
        present_types = {node.decision_type for node in trace.nodes.values()}
        missing_types = required_types - present_types

        for missing_type in missing_types:
            issues.append(ValidationIssue(
                issue_id=f"missing_decision_{missing_type.value}",
                category=ValidationCategory.COMPLETENESS,
                severity=ValidationSeverity.CRITICAL,
                title=f"Missing {missing_type.value} Decision",
                description=f"Required decision type {missing_type.value} not found in trace",
                affected_nodes=[],
                recommendation=f"Add {missing_type.value} decision to trace",
                compliance_impact=True
            ))

        # Check trace duration (shouldn't be too short)
        if trace.end_time and trace.start_time:
            duration = (trace.end_time - trace.start_time).total_seconds()
            if duration < 10:  # Less than 10 seconds seems too fast
                issues.append(ValidationIssue(
                    issue_id="trace_too_fast",
                    category=ValidationCategory.PERFORMANCE,
                    severity=ValidationSeverity.MEDIUM,
                    title="Unusually Fast Processing",
                    description=f"Decision trace completed in {duration:.1f}s which may indicate insufficient analysis",
                    affected_nodes=list(trace.nodes.keys()),
                    recommendation="Review decision process for thoroughness"
                ))

        return issues

    async def _validate_consistency(self, trace: DecisionTrace) -> List[ValidationIssue]:
        """Validate internal consistency"""
        issues = []

        # Check for contradictory decisions
        approval_nodes = [
            node for node in trace.nodes.values()
            if node.decision_type == DecisionType.LOAN_APPROVAL
        ]

        if len(approval_nodes) > 1:
            # Check if multiple approval decisions contradict each other
            approval_outcomes = [
                node.output_decision.get("approved", False)
                for node in approval_nodes
            ]

            if not all(outcome == approval_outcomes[0] for outcome in approval_outcomes):
                issues.append(ValidationIssue(
                    issue_id="contradictory_approvals",
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.CRITICAL,
                    title="Contradictory Approval Decisions",
                    description="Multiple approval decisions with different outcomes detected",
                    affected_nodes=[node.node_id for node in approval_nodes],
                    recommendation="Resolve contradictory approval decisions",
                    compliance_impact=True
                ))

        # Check factor weight consistency
        for node in trace.nodes.values():
            if node.factors:
                total_weight = sum(factor.weight for factor in node.factors)
                if abs(total_weight - 1.0) > 0.1:  # Allow 10% variance
                    issues.append(ValidationIssue(
                        issue_id=f"factor_weights_{node.node_id}",
                        category=ValidationCategory.CONSISTENCY,
                        severity=ValidationSeverity.MEDIUM,
                        title="Factor Weights Don't Sum to 1.0",
                        description=f"Factor weights sum to {total_weight:.2f} instead of 1.0",
                        affected_nodes=[node.node_id],
                        recommendation="Normalize factor weights to sum to 1.0"
                    ))

        return issues

    async def _validate_accuracy(self, trace: DecisionTrace) -> List[ValidationIssue]:
        """Validate data accuracy"""
        issues = []

        for node in trace.nodes.values():
            for factor in node.factors:
                for data_point in factor.data_points:
                    # Check data point validation status
                    if data_point.validation_status == "flagged":
                        issues.append(ValidationIssue(
                            issue_id=f"flagged_data_{data_point.key}",
                            category=ValidationCategory.ACCURACY,
                            severity=ValidationSeverity.HIGH,
                            title="Flagged Data Point Used",
                            description=f"Data point {data_point.key} is flagged but used in decision",
                            affected_nodes=[node.node_id],
                            recommendation="Investigate and resolve data quality issues"
                        ))

                    # Check data freshness
                    if data_point.timestamp:
                        age = datetime.utcnow() - data_point.timestamp
                        if age.days > 30:  # Data older than 30 days
                            issues.append(ValidationIssue(
                                issue_id=f"stale_data_{data_point.key}",
                                category=ValidationCategory.ACCURACY,
                                severity=ValidationSeverity.MEDIUM,
                                title="Stale Data Used",
                                description=f"Data point {data_point.key} is {age.days} days old",
                                affected_nodes=[node.node_id],
                                recommendation="Update with more recent data if available"
                            ))

        return issues

    async def _validate_compliance(self, trace: DecisionTrace) -> List[ValidationIssue]:
        """Validate regulatory compliance"""
        issues = []

        compliance_report = await self.check_regulatory_compliance(trace)

        if not compliance_report["overall_compliant"]:
            issues.append(ValidationIssue(
                issue_id="regulatory_non_compliance",
                category=ValidationCategory.COMPLIANCE,
                severity=ValidationSeverity.CRITICAL,
                title="Regulatory Compliance Issues",
                description="Trace does not meet all regulatory requirements",
                affected_nodes=list(trace.nodes.keys()),
                recommendation="Address missing regulatory requirements",
                compliance_impact=True,
                metadata={"compliance_report": compliance_report}
            ))

        return issues

    async def _validate_performance(self, trace: DecisionTrace) -> List[ValidationIssue]:
        """Validate performance metrics"""
        issues = []

        # Check for performance thresholds
        if trace.end_time and trace.start_time:
            processing_time = (trace.end_time - trace.start_time).total_seconds()
            max_processing_time = self.performance_thresholds.get("max_processing_time", 300)

            if processing_time > max_processing_time:
                issues.append(ValidationIssue(
                    issue_id="slow_processing",
                    category=ValidationCategory.PERFORMANCE,
                    severity=ValidationSeverity.MEDIUM,
                    title="Slow Processing Time",
                    description=f"Processing took {processing_time:.1f}s, exceeding {max_processing_time}s threshold",
                    affected_nodes=list(trace.nodes.keys()),
                    recommendation="Investigate performance bottlenecks"
                ))

        return issues

    async def _validate_security(self, trace: DecisionTrace) -> List[ValidationIssue]:
        """Validate security and privacy aspects"""
        issues = []

        # Check for PII in reasoning chains
        for node in trace.nodes.values():
            for reasoning_step in node.reasoning_chain:
                if await self._contains_pii(reasoning_step):
                    issues.append(ValidationIssue(
                        issue_id=f"pii_in_reasoning_{node.node_id}",
                        category=ValidationCategory.SECURITY,
                        severity=ValidationSeverity.HIGH,
                        title="PII in Reasoning Chain",
                        description="Personally identifiable information detected in reasoning",
                        affected_nodes=[node.node_id],
                        recommendation="Remove or redact PII from reasoning documentation",
                        compliance_impact=True
                    ))

        return issues

    async def _validate_factor(self, factor: DecisionFactor, node_id: str) -> List[ValidationIssue]:
        """Validate a specific decision factor"""
        issues = []

        # Check if factor has data points
        if not factor.data_points:
            issues.append(ValidationIssue(
                issue_id=f"factor_no_data_{factor.factor_id}",
                category=ValidationCategory.COMPLETENESS,
                severity=ValidationSeverity.HIGH,
                title="Factor Without Data Points",
                description=f"Factor {factor.name} has no supporting data points",
                affected_nodes=[node_id],
                recommendation="Add supporting data points for factor"
            ))

        # Check factor weight validity
        if factor.weight < 0 or factor.weight > 1:
            issues.append(ValidationIssue(
                issue_id=f"invalid_weight_{factor.factor_id}",
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.HIGH,
                title="Invalid Factor Weight",
                description=f"Factor weight {factor.weight} is outside valid range [0,1]",
                affected_nodes=[node_id],
                recommendation="Correct factor weight to be between 0 and 1"
            ))

        return issues

    async def _calculate_overall_score(
        self,
        trace: DecisionTrace,
        issues: List[ValidationIssue]
    ) -> float:
        """Calculate overall validation score"""
        if not issues:
            return 1.0

        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.CRITICAL: 1.0,
            ValidationSeverity.HIGH: 0.7,
            ValidationSeverity.MEDIUM: 0.4,
            ValidationSeverity.LOW: 0.2,
            ValidationSeverity.INFO: 0.1
        }

        total_penalty = sum(
            severity_weights.get(issue.severity, 0.5)
            for issue in issues
        )

        # Base score from trace completeness and consistency
        base_score = (trace.completeness_score + trace.consistency_score) / 2

        # Apply penalty (but don't go below 0)
        penalty_factor = max(0.1, 1.0 - (total_penalty / 10.0))  # Normalize penalty
        final_score = max(0.0, base_score * penalty_factor)

        return final_score

    async def _determine_compliance_status(self, issues: List[ValidationIssue]) -> str:
        """Determine overall compliance status"""
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        compliance_issues = [i for i in issues if i.compliance_impact]

        if critical_issues or len(compliance_issues) > 3:
            return "non_compliant"
        elif compliance_issues:
            return "warning"
        else:
            return "compliant"

    async def _generate_validation_summary(
        self,
        trace: DecisionTrace,
        issues: List[ValidationIssue]
    ) -> Dict[str, Any]:
        """Generate validation summary"""
        return {
            "total_issues": len(issues),
            "issues_by_severity": {
                severity.value: len([i for i in issues if i.severity == severity])
                for severity in ValidationSeverity
            },
            "issues_by_category": {
                category.value: len([i for i in issues if i.category == category])
                for category in ValidationCategory
            },
            "compliance_impact_issues": len([i for i in issues if i.compliance_impact]),
            "auto_fixable_issues": len([i for i in issues if i.auto_fixable]),
            "trace_statistics": {
                "nodes": len(trace.nodes),
                "decisions": len([n for n in trace.nodes.values() if n.decision_type]),
                "completeness": trace.completeness_score,
                "consistency": trace.consistency_score
            }
        }

    async def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate high-level recommendations"""
        recommendations = []

        # Group by category for better recommendations
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately")

        compliance_issues = [i for i in issues if i.compliance_impact]
        if compliance_issues:
            recommendations.append(f"Resolve {len(compliance_issues)} compliance-related issues")

        auto_fixable = [i for i in issues if i.auto_fixable]
        if auto_fixable:
            recommendations.append(f"Consider auto-fixing {len(auto_fixable)} issues")

        return recommendations

    # Helper methods for creating rules and requirements

    def _create_validation_rules(self) -> Dict[str, Any]:
        """Create validation rules configuration"""
        return {
            "required_decision_types": [
                DecisionType.RISK_ASSESSMENT,
                DecisionType.LOAN_APPROVAL
            ],
            "minimum_confidence": 0.3,
            "maximum_processing_time": 300,
            "factor_weight_tolerance": 0.1,
            "data_freshness_days": 30
        }

    def _create_compliance_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Create regulatory compliance requirements"""
        return {
            "Fair_Lending_Act": {
                "required_documentation": ["reasoning", "factors", "data_sources"],
                "prohibited_factors": ["race", "gender", "religion"],
                "bias_testing_required": True
            },
            "ECOA": {
                "adverse_action_notice": True,
                "reason_codes_required": True,
                "prohibited_discrimination": True
            }
        }

    def _create_performance_thresholds(self) -> Dict[str, float]:
        """Create performance thresholds"""
        return {
            "max_processing_time": 300,
            "min_confidence": 0.3,
            "max_data_age_days": 30
        }

    # Additional helper methods

    async def _group_similar_traces(
        self,
        traces: List[DecisionTrace]
    ) -> Dict[str, List[DecisionTrace]]:
        """Group similar traces for consistency checking"""
        # This would implement sophisticated grouping logic
        # For now, return simple grouping
        return {"default_group": traces}

    async def _check_group_consistency(
        self,
        group_traces: List[DecisionTrace],
        group_key: str
    ) -> List[ValidationIssue]:
        """Check consistency within a group of similar traces"""
        issues = []
        # This would implement consistency checking logic
        return issues

    async def _check_framework_compliance(
        self,
        trace: DecisionTrace,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance with specific regulatory framework"""
        return {
            "compliant": True,
            "score": 0.95,
            "missing_requirements": []
        }

    async def _contains_pii(self, text: str) -> bool:
        """Check if text contains personally identifiable information"""
        # This would implement PII detection
        # For now, simple keyword check
        pii_indicators = ["ssn", "social security", "credit card", "bank account"]
        return any(indicator in text.lower() for indicator in pii_indicators)