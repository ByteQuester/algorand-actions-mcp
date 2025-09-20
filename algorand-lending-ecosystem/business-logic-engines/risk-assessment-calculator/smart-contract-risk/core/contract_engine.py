"""
Smart Contract Risk Engine
Master engine for comprehensive smart contract security and interaction risk assessment
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import yaml
import json
from pathlib import Path

from .contract_analyzer import SmartContractAnalyzer, ContractAnalysis
from .interaction_risk import InteractionRiskAnalyzer, InteractionRiskAssessment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContractRiskScore:
    """Individual contract risk score breakdown"""
    contract_id: str
    contract_name: str
    contract_category: str
    security_score: float
    audit_score: float
    complexity_score: float
    vulnerability_score: float
    interaction_risk_score: float
    overall_risk_score: float
    risk_tier: str
    confidence_level: float
    last_updated: datetime

@dataclass
class PortfolioContractMetrics:
    """Portfolio-level contract metrics"""
    total_contracts: int
    audited_contracts: int
    high_risk_contracts: int
    critical_vulnerabilities: int
    outdated_audits: int
    complex_interactions: int
    cross_protocol_dependencies: int
    upgrade_risks: int
    admin_key_risks: int

@dataclass
class ContractRiskAlert:
    """Contract risk alert"""
    alert_type: str
    severity: str
    contract_id: Optional[str]
    message: str
    risk_score: float
    threshold: float
    recommended_action: str
    urgency_level: int
    auto_mitigation_available: bool

@dataclass
class ComprehensiveContractRiskAssessment:
    """Complete smart contract risk assessment"""
    portfolio_metrics: PortfolioContractMetrics
    contract_scores: List[ContractRiskScore]
    contract_analyses: Dict[str, ContractAnalysis]
    interaction_assessment: InteractionRiskAssessment
    exploit_proximity_analysis: Dict[str, float]
    upgrade_risk_analysis: Dict[str, float]
    admin_key_analysis: Dict[str, float]
    dependency_risk_analysis: Dict[str, float]
    overall_portfolio_risk: float
    risk_level: str
    confidence_score: float
    risk_alerts: List[ContractRiskAlert]
    recommendations: List[str]
    monitoring_requirements: List[str]
    next_review_date: datetime
    timestamp: datetime

class SmartContractRiskEngine:
    """Master engine for comprehensive smart contract risk assessment"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the smart contract risk engine"""
        self.config = self._load_config(config_path)
        self.contract_analyzer = SmartContractAnalyzer(config_path)
        self.interaction_analyzer = InteractionRiskAnalyzer(config_path)

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def assess_contract_portfolio_risk(self, contracts_data: Dict[str, Dict[str, Any]],
                                           interaction_history: Optional[List[Dict]] = None,
                                           include_exploit_analysis: bool = True) -> ComprehensiveContractRiskAssessment:
        """Perform comprehensive contract portfolio risk assessment"""
        logger.info("Starting comprehensive smart contract portfolio risk assessment...")

        if not contracts_data:
            raise ValueError("No contract data provided for risk assessment")

        # Run contract security analysis
        contract_analyses = await self.contract_analyzer.batch_analyze_contracts(contracts_data)

        # Run interaction risk analysis
        interaction_assessment = await self.interaction_analyzer.analyze_interaction_risks(
            contracts_data, interaction_history
        )

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(contract_analyses, interaction_assessment)

        # Calculate individual contract risk scores
        contract_scores = await self._calculate_contract_risk_scores(
            contract_analyses, interaction_assessment, contracts_data
        )

        # Analyze exploit proximity if requested
        exploit_proximity_analysis = {}
        if include_exploit_analysis:
            exploit_proximity_analysis = await self._analyze_exploit_proximity(contract_analyses, contracts_data)

        # Analyze upgrade risks
        upgrade_risk_analysis = await self._analyze_upgrade_risks(contracts_data, contract_analyses)

        # Analyze admin key risks
        admin_key_analysis = await self._analyze_admin_key_risks(contracts_data, contract_analyses)

        # Analyze dependency risks
        dependency_risk_analysis = await self._analyze_dependency_risks(contracts_data, interaction_assessment)

        # Calculate overall portfolio risk
        overall_portfolio_risk = self._calculate_overall_portfolio_risk(
            contract_scores, interaction_assessment, exploit_proximity_analysis,
            upgrade_risk_analysis, admin_key_analysis, dependency_risk_analysis
        )

        # Determine risk level
        risk_level = self._determine_portfolio_risk_level(overall_portfolio_risk, portfolio_metrics)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(contract_analyses, interaction_assessment)

        # Generate risk alerts
        risk_alerts = await self._generate_risk_alerts(
            contract_scores, portfolio_metrics, interaction_assessment,
            exploit_proximity_analysis, upgrade_risk_analysis, admin_key_analysis
        )

        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations(
            contract_scores, portfolio_metrics, interaction_assessment, risk_alerts, overall_portfolio_risk
        )

        # Generate monitoring requirements
        monitoring_requirements = self._generate_monitoring_requirements(
            contract_scores, interaction_assessment, risk_alerts
        )

        # Determine next review date
        next_review_date = self._determine_next_review_date(risk_level, risk_alerts)

        return ComprehensiveContractRiskAssessment(
            portfolio_metrics=portfolio_metrics,
            contract_scores=contract_scores,
            contract_analyses=contract_analyses,
            interaction_assessment=interaction_assessment,
            exploit_proximity_analysis=exploit_proximity_analysis,
            upgrade_risk_analysis=upgrade_risk_analysis,
            admin_key_analysis=admin_key_analysis,
            dependency_risk_analysis=dependency_risk_analysis,
            overall_portfolio_risk=overall_portfolio_risk,
            risk_level=risk_level,
            confidence_score=confidence_score,
            risk_alerts=risk_alerts,
            recommendations=recommendations,
            monitoring_requirements=monitoring_requirements,
            next_review_date=next_review_date,
            timestamp=datetime.now()
        )

    def _calculate_portfolio_metrics(self, contract_analyses: Dict[str, ContractAnalysis],
                                   interaction_assessment: InteractionRiskAssessment) -> PortfolioContractMetrics:
        """Calculate portfolio-level contract metrics"""
        total_contracts = len(contract_analyses)
        audited_contracts = len([
            analysis for analysis in contract_analyses.values()
            if analysis.audits and any(
                (datetime.now() - audit.audit_date).days < 730
                for audit in analysis.audits
            )
        ])

        high_risk_contracts = len([
            analysis for analysis in contract_analyses.values()
            if analysis.overall_security_score < 0.5
        ])

        critical_vulnerabilities = sum(
            analysis.vulnerability_assessment.critical_count
            for analysis in contract_analyses.values()
        )

        outdated_audits = len([
            analysis for analysis in contract_analyses.values()
            if analysis.audits and all(
                (datetime.now() - audit.audit_date).days > 730
                for audit in analysis.audits
            )
        ])

        # Interaction-based metrics
        complex_interactions = len([
            pattern for pattern in interaction_assessment.interaction_patterns
            if pattern.risk_level in ['HIGH', 'CRITICAL']
        ])

        cross_protocol_dependencies = len(interaction_assessment.cross_protocol_risks)

        # Estimate upgrade and admin key risks
        upgrade_risks = len([
            analysis for analysis in contract_analyses.values()
            if not analysis.security_features.timelock_mechanism
        ])

        admin_key_risks = len([
            analysis for analysis in contract_analyses.values()
            if not analysis.security_features.multisig_requirement
        ])

        return PortfolioContractMetrics(
            total_contracts=total_contracts,
            audited_contracts=audited_contracts,
            high_risk_contracts=high_risk_contracts,
            critical_vulnerabilities=critical_vulnerabilities,
            outdated_audits=outdated_audits,
            complex_interactions=complex_interactions,
            cross_protocol_dependencies=cross_protocol_dependencies,
            upgrade_risks=upgrade_risks,
            admin_key_risks=admin_key_risks
        )

    async def _calculate_contract_risk_scores(self, contract_analyses: Dict[str, ContractAnalysis],
                                            interaction_assessment: InteractionRiskAssessment,
                                            contracts_data: Dict[str, Dict[str, Any]]) -> List[ContractRiskScore]:
        """Calculate individual contract risk scores"""
        contract_scores = []

        for contract_id, analysis in contract_analyses.items():
            # Security score from contract analysis
            security_score = analysis.overall_security_score

            # Audit score
            audit_score = self._calculate_audit_score(analysis.audits)

            # Complexity score
            complexity_score = self._calculate_complexity_score(analysis.contract_metrics)

            # Vulnerability score
            vulnerability_score = analysis.vulnerability_assessment.total_score

            # Interaction risk score
            interaction_risk_score = self._calculate_contract_interaction_risk(
                contract_id, interaction_assessment
            )

            # Overall risk score (inverted for consistency - lower security = higher risk)
            overall_risk_score = self._calculate_contract_overall_risk(
                security_score, audit_score, complexity_score,
                vulnerability_score, interaction_risk_score
            )

            # Risk tier
            risk_tier = self._determine_contract_risk_tier(overall_risk_score)

            contract_score = ContractRiskScore(
                contract_id=contract_id,
                contract_name=analysis.contract_name,
                contract_category=analysis.contract_category,
                security_score=security_score,
                audit_score=audit_score,
                complexity_score=complexity_score,
                vulnerability_score=vulnerability_score,
                interaction_risk_score=interaction_risk_score,
                overall_risk_score=overall_risk_score,
                risk_tier=risk_tier,
                confidence_level=analysis.confidence_level,
                last_updated=analysis.last_update_date
            )

            contract_scores.append(contract_score)

        return contract_scores

    def _calculate_audit_score(self, audits: List) -> float:
        """Calculate audit quality score"""
        if not audits:
            return 0.0

        recent_audits = [
            audit for audit in audits
            if (datetime.now() - audit.audit_date).days < 365
        ]

        if not recent_audits:
            return 0.3  # Outdated audits

        # Weight by auditor reputation and recency
        weighted_scores = []
        for audit in recent_audits:
            age_factor = max(0.5, 1.0 - ((datetime.now() - audit.audit_date).days / 365))
            reputation_factor = audit.reputation_score / 100
            weighted_score = (audit.audit_score / 100) * age_factor * reputation_factor
            weighted_scores.append(weighted_score)

        return sum(weighted_scores) / len(weighted_scores)

    def _calculate_complexity_score(self, metrics) -> float:
        """Calculate complexity risk score"""
        complexity_config = self.config.get('complexity_metrics', {})

        # Normalize metrics to 0-1 scale
        loc_score = min(metrics.lines_of_code / complexity_config.get('critical_threshold', 2000), 1.0)
        function_score = min(metrics.function_count / complexity_config.get('critical_threshold', 50), 1.0)
        complexity_score = min(metrics.cyclomatic_complexity / complexity_config.get('critical_threshold', 30), 1.0)
        calls_score = min(metrics.external_call_count / complexity_config.get('critical_threshold', 20), 1.0)

        # Weighted combination
        overall_complexity = (
            loc_score * 0.3 +
            function_score * 0.25 +
            complexity_score * 0.25 +
            calls_score * 0.2
        )

        return min(overall_complexity, 1.0)

    def _calculate_contract_interaction_risk(self, contract_id: str,
                                           interaction_assessment: InteractionRiskAssessment) -> float:
        """Calculate interaction risk for specific contract"""
        # Find interactions involving this contract
        contract_interactions = [
            interaction for interaction in interaction_assessment.contract_interactions
            if interaction.source_contract == contract_id or interaction.target_contract == contract_id
        ]

        if not contract_interactions:
            return 0.0

        # Average risk of interactions
        avg_risk = sum(inter.risk_score for inter in contract_interactions) / len(contract_interactions)

        # Check if contract is in high-risk patterns
        pattern_risk = 0.0
        for pattern in interaction_assessment.interaction_patterns:
            if contract_id in pattern.contracts_involved and pattern.risk_level == 'HIGH':
                pattern_risk = max(pattern_risk, 0.7)

        return min(avg_risk + pattern_risk, 1.0)

    def _calculate_contract_overall_risk(self, security_score: float, audit_score: float,
                                       complexity_score: float, vulnerability_score: float,
                                       interaction_risk_score: float) -> float:
        """Calculate overall contract risk score"""
        weights = self.config.get('risk_scoring_weights', {
            'security_analysis_weight': 0.3,
            'audit_weight': 0.25,
            'complexity_weight': 0.15,
            'vulnerability_weight': 0.2,
            'interaction_weight': 0.1
        })

        # Invert security and audit scores (higher security = lower risk)
        risk_score = (
            (1.0 - security_score) * weights.get('security_analysis_weight', 0.3) +
            (1.0 - audit_score) * weights.get('audit_weight', 0.25) +
            complexity_score * weights.get('complexity_weight', 0.15) +
            vulnerability_score * weights.get('vulnerability_weight', 0.2) +
            interaction_risk_score * weights.get('interaction_weight', 0.1)
        )

        return min(risk_score, 1.0)

    def _determine_contract_risk_tier(self, risk_score: float) -> str:
        """Determine contract risk tier"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MODERATE"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    async def _analyze_exploit_proximity(self, contract_analyses: Dict[str, ContractAnalysis],
                                       contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Analyze proximity to known exploits"""
        proximity_scores = {}
        exploit_db = self.config.get('exploit_database', {})

        for contract_id, analysis in contract_analyses.items():
            contract_data = contracts_data.get(contract_id, {})

            # Calculate proximity based on:
            # 1. Contract category vulnerabilities
            # 2. Missing security features
            # 3. Historical exploit patterns

            category_exploits = exploit_db.get('algorand_specific_exploits', {})
            contract_category = analysis.contract_category

            proximity_score = 0.0

            # Check category-specific exploits
            for exploit_type, exploit_info in category_exploits.items():
                if contract_category in exploit_info.get('affected_contracts', []):
                    exploit_frequency = exploit_info.get('historical_frequency', 0.01)
                    severity_multiplier = {
                        'critical': 1.0,
                        'high': 0.7,
                        'medium': 0.4,
                        'low': 0.2
                    }.get(exploit_info.get('severity', 'medium'), 0.4)

                    # Check if mitigation is in place
                    mitigation = exploit_info.get('mitigation', '')
                    has_mitigation = self._check_mitigation_present(analysis, mitigation)

                    if not has_mitigation:
                        proximity_score += exploit_frequency * severity_multiplier

            # Check cross-protocol exploits
            cross_exploits = exploit_db.get('cross_protocol_exploits', {})
            for exploit_type, exploit_info in cross_exploits.items():
                affected_protocols = exploit_info.get('affected_protocols', [])
                if any(protocol in contract_id.lower() for protocol in affected_protocols):
                    exploit_frequency = exploit_info.get('historical_frequency', 0.05)
                    proximity_score += exploit_frequency * 0.8

            proximity_scores[contract_id] = min(proximity_score, 1.0)

        return proximity_scores

    def _check_mitigation_present(self, analysis: ContractAnalysis, mitigation: str) -> bool:
        """Check if mitigation is present in contract"""
        mitigations_map = {
            'formal_verification': analysis.audits and any(
                audit.audit_type == 'formal_verification' for audit in analysis.audits
            ),
            'access_control': analysis.security_features.access_control,
            'multiple_oracles': True,  # Assume implemented if oracle contract
            'reentrancy_guards': analysis.security_features.reentrancy_protection,
            'price_oracle_validation': analysis.contract_category == 'oracle_integration',
            'timelock_governance': analysis.security_features.timelock_mechanism,
            'multisig_validation': analysis.security_features.multisig_requirement
        }

        return mitigations_map.get(mitigation, False)

    async def _analyze_upgrade_risks(self, contracts_data: Dict[str, Dict[str, Any]],
                                   contract_analyses: Dict[str, ContractAnalysis]) -> Dict[str, float]:
        """Analyze contract upgrade risks"""
        upgrade_risks = {}
        upgrade_config = self.config.get('upgrade_patterns', {})

        for contract_id, contract_data in contracts_data.items():
            analysis = contract_analyses.get(contract_id)
            if not analysis:
                continue

            # Determine upgrade pattern
            upgrade_pattern = self._determine_upgrade_pattern(contract_data, analysis)

            # Get base risk from configuration
            pattern_config = upgrade_config.get(upgrade_pattern, {})
            base_upgrade_risk = pattern_config.get('upgrade_risk', 0.5)
            governance_risk = pattern_config.get('governance_risk', 0.5)
            centralization_risk = pattern_config.get('centralization_risk', 0.5)

            # Adjust based on security features
            if analysis.security_features.timelock_mechanism:
                base_upgrade_risk *= 0.7
                governance_risk *= 0.8

            if analysis.security_features.multisig_requirement:
                centralization_risk *= 0.5

            # Combined upgrade risk
            combined_risk = (base_upgrade_risk + governance_risk + centralization_risk) / 3
            upgrade_risks[contract_id] = min(combined_risk, 1.0)

        return upgrade_risks

    def _determine_upgrade_pattern(self, contract_data: Dict[str, Any], analysis: ContractAnalysis) -> str:
        """Determine contract upgrade pattern"""
        features = contract_data.get('features', [])
        functions = contract_data.get('functions', [])

        if 'immutable' in features or analysis.contract_category == 'token_contracts':
            return 'immutable_contracts'
        elif 'proxy_pattern' in features or 'upgradeable' in functions:
            return 'proxy_upgradeable'
        elif 'admin_upgrade' in functions or not analysis.security_features.timelock_mechanism:
            return 'admin_upgradeable'
        else:
            return 'governance_upgradeable'

    async def _analyze_admin_key_risks(self, contracts_data: Dict[str, Dict[str, Any]],
                                     contract_analyses: Dict[str, ContractAnalysis]) -> Dict[str, float]:
        """Analyze admin key concentration risks"""
        admin_risks = {}
        admin_config = self.config.get('admin_key_patterns', {})

        for contract_id, contract_data in contracts_data.items():
            analysis = contract_analyses.get(contract_id)
            if not analysis:
                continue

            # Determine admin pattern
            admin_pattern = self._determine_admin_pattern(contract_data, analysis)

            # Get base risk from configuration
            pattern_config = admin_config.get(admin_pattern, {})
            centralization_risk = pattern_config.get('centralization_risk', 0.5)

            # Adjust based on security features
            if analysis.security_features.multisig_requirement:
                centralization_risk *= 0.3

            if analysis.security_features.timelock_mechanism:
                centralization_risk *= 0.7

            admin_risks[contract_id] = min(centralization_risk, 1.0)

        return admin_risks

    def _determine_admin_pattern(self, contract_data: Dict[str, Any], analysis: ContractAnalysis) -> str:
        """Determine admin key pattern"""
        if analysis.security_features.multisig_requirement:
            return 'multisig_admin'
        elif analysis.security_features.timelock_mechanism:
            return 'timelock_admin'
        elif analysis.contract_category == 'governance':
            return 'dao_admin'
        else:
            return 'single_admin'

    async def _analyze_dependency_risks(self, contracts_data: Dict[str, Dict[str, Any]],
                                      interaction_assessment: InteractionRiskAssessment) -> Dict[str, float]:
        """Analyze contract dependency risks"""
        dependency_risks = {}

        # Analyze each contract's dependencies
        for contract_id in contracts_data.keys():
            # Find contracts this one depends on
            dependencies = [
                interaction.target_contract
                for interaction in interaction_assessment.contract_interactions
                if interaction.source_contract == contract_id
            ]

            if not dependencies:
                dependency_risks[contract_id] = 0.0
                continue

            # Calculate dependency risk based on:
            # 1. Number of dependencies
            # 2. Risk level of dependencies
            # 3. Criticality of dependency relationships

            dependency_count_risk = min(len(dependencies) / 10, 0.5)  # Cap at 0.5

            # Risk from dependency quality
            dependency_quality_risk = 0.0
            for dep_contract in dependencies:
                # Check if dependency is in critical paths
                if dep_contract in interaction_assessment.critical_interactions:
                    dependency_quality_risk += 0.2

                # Check interaction risk
                dep_interactions = [
                    inter for inter in interaction_assessment.contract_interactions
                    if inter.source_contract == contract_id and inter.target_contract == dep_contract
                ]
                if dep_interactions:
                    avg_dep_risk = sum(inter.risk_score for inter in dep_interactions) / len(dep_interactions)
                    dependency_quality_risk += avg_dep_risk * 0.3

            # Circular dependency risk
            circular_risk = 0.0
            for circular_dep in interaction_assessment.call_graph.circular_dependencies:
                if contract_id in circular_dep:
                    circular_risk = 0.4
                    break

            total_risk = dependency_count_risk + dependency_quality_risk + circular_risk
            dependency_risks[contract_id] = min(total_risk, 1.0)

        return dependency_risks

    def _calculate_overall_portfolio_risk(self, contract_scores: List[ContractRiskScore],
                                        interaction_assessment: InteractionRiskAssessment,
                                        exploit_proximity: Dict[str, float],
                                        upgrade_risks: Dict[str, float],
                                        admin_key_risks: Dict[str, float],
                                        dependency_risks: Dict[str, float]) -> float:
        """Calculate overall portfolio risk score"""
        if not contract_scores:
            return 0.5

        # Contract risk component
        contract_risk = sum(score.overall_risk_score for score in contract_scores) / len(contract_scores)

        # Interaction risk component
        interaction_risk = interaction_assessment.overall_interaction_risk

        # Exploit proximity component
        exploit_risk = max(exploit_proximity.values()) if exploit_proximity else 0.0

        # Upgrade risk component
        upgrade_risk = max(upgrade_risks.values()) if upgrade_risks else 0.0

        # Admin key risk component
        admin_risk = max(admin_key_risks.values()) if admin_key_risks else 0.0

        # Dependency risk component
        dependency_risk = max(dependency_risks.values()) if dependency_risks else 0.0

        # Weighted combination
        weights = {
            'contracts': 0.35,
            'interactions': 0.25,
            'exploits': 0.15,
            'upgrades': 0.1,
            'admin_keys': 0.1,
            'dependencies': 0.05
        }

        overall_risk = (
            contract_risk * weights['contracts'] +
            interaction_risk * weights['interactions'] +
            exploit_risk * weights['exploits'] +
            upgrade_risk * weights['upgrades'] +
            admin_risk * weights['admin_keys'] +
            dependency_risk * weights['dependencies']
        )

        return min(overall_risk, 1.0)

    def _determine_portfolio_risk_level(self, overall_risk: float, portfolio_metrics: PortfolioContractMetrics) -> str:
        """Determine overall portfolio risk level"""
        # Base level from overall risk
        if overall_risk >= 0.8:
            base_level = "CRITICAL"
        elif overall_risk >= 0.6:
            base_level = "HIGH"
        elif overall_risk >= 0.4:
            base_level = "MODERATE"
        elif overall_risk >= 0.2:
            base_level = "LOW"
        else:
            base_level = "MINIMAL"

        # Adjust for specific concerns
        if portfolio_metrics.critical_vulnerabilities > 0:
            if base_level in ["MINIMAL", "LOW"]:
                return "MODERATE"
            elif base_level == "MODERATE":
                return "HIGH"

        if portfolio_metrics.high_risk_contracts > portfolio_metrics.total_contracts * 0.3:
            if base_level in ["MINIMAL", "LOW"]:
                return "MODERATE"

        return base_level

    def _calculate_confidence_score(self, contract_analyses: Dict[str, ContractAnalysis],
                                  interaction_assessment: InteractionRiskAssessment) -> float:
        """Calculate confidence score for the overall assessment"""
        if not contract_analyses:
            return 0.5

        # Contract analysis confidence
        contract_confidence = sum(
            analysis.confidence_level for analysis in contract_analyses.values()
        ) / len(contract_analyses)

        # Interaction analysis confidence (based on data completeness)
        interaction_confidence = 0.8  # Assume good confidence for interaction analysis

        # Data completeness confidence
        audited_contracts = len([
            analysis for analysis in contract_analyses.values()
            if analysis.audits
        ])
        audit_confidence = audited_contracts / len(contract_analyses)

        # Combined confidence
        overall_confidence = (
            contract_confidence * 0.5 +
            interaction_confidence * 0.3 +
            audit_confidence * 0.2
        )

        return min(overall_confidence, 1.0)

    async def _generate_risk_alerts(self, contract_scores: List[ContractRiskScore],
                                  portfolio_metrics: PortfolioContractMetrics,
                                  interaction_assessment: InteractionRiskAssessment,
                                  exploit_proximity: Dict[str, float],
                                  upgrade_risks: Dict[str, float],
                                  admin_key_risks: Dict[str, float]) -> List[ContractRiskAlert]:
        """Generate comprehensive risk alerts"""
        alerts = []
        thresholds = self.config.get('alert_thresholds', {})

        # Critical vulnerability alerts
        if portfolio_metrics.critical_vulnerabilities > 0:
            alerts.append(ContractRiskAlert(
                alert_type='critical_vulnerabilities',
                severity='CRITICAL',
                contract_id=None,
                message=f"{portfolio_metrics.critical_vulnerabilities} critical vulnerabilities detected across portfolio",
                risk_score=1.0,
                threshold=0.0,
                recommended_action="Immediate security audit and vulnerability remediation required",
                urgency_level=10,
                auto_mitigation_available=False
            ))

        # High-risk contract alerts
        high_risk_contracts = [score for score in contract_scores if score.overall_risk_score >= 0.7]
        for contract_score in high_risk_contracts:
            alerts.append(ContractRiskAlert(
                alert_type='high_risk_contract',
                severity='HIGH',
                contract_id=contract_score.contract_id,
                message=f"High risk detected in {contract_score.contract_name} (risk: {contract_score.overall_risk_score:.2f})",
                risk_score=contract_score.overall_risk_score,
                threshold=0.7,
                recommended_action=f"Review and mitigate risks in {contract_score.contract_name}",
                urgency_level=8,
                auto_mitigation_available=False
            ))

        # Exploit proximity alerts
        for contract_id, proximity in exploit_proximity.items():
            if proximity > thresholds.get('exploit_proximity_critical', 0.7):
                contract_name = next(
                    (score.contract_name for score in contract_scores if score.contract_id == contract_id),
                    contract_id
                )
                alerts.append(ContractRiskAlert(
                    alert_type='exploit_proximity',
                    severity='HIGH',
                    contract_id=contract_id,
                    message=f"High exploit proximity for {contract_name} (proximity: {proximity:.2f})",
                    risk_score=proximity,
                    threshold=thresholds.get('exploit_proximity_critical', 0.7),
                    recommended_action="Implement additional security measures and monitoring",
                    urgency_level=7,
                    auto_mitigation_available=True
                ))

        # Interaction risk alerts
        if interaction_assessment.overall_interaction_risk > 0.7:
            alerts.append(ContractRiskAlert(
                alert_type='interaction_risk',
                severity='HIGH',
                contract_id=None,
                message=f"High interaction risk detected (risk: {interaction_assessment.overall_interaction_risk:.2f})",
                risk_score=interaction_assessment.overall_interaction_risk,
                threshold=0.7,
                recommended_action="Review and secure contract interaction patterns",
                urgency_level=6,
                auto_mitigation_available=True
            ))

        # Admin key concentration alerts
        for contract_id, admin_risk in admin_key_risks.items():
            if admin_risk > thresholds.get('admin_centralization_critical', 0.8):
                contract_name = next(
                    (score.contract_name for score in contract_scores if score.contract_id == contract_id),
                    contract_id
                )
                alerts.append(ContractRiskAlert(
                    alert_type='admin_centralization',
                    severity='MEDIUM',
                    contract_id=contract_id,
                    message=f"High admin key centralization in {contract_name} (risk: {admin_risk:.2f})",
                    risk_score=admin_risk,
                    threshold=thresholds.get('admin_centralization_critical', 0.8),
                    recommended_action="Implement multi-signature or DAO governance",
                    urgency_level=5,
                    auto_mitigation_available=True
                ))

        # Sort alerts by urgency
        alerts.sort(key=lambda x: x.urgency_level, reverse=True)

        return alerts

    def _generate_comprehensive_recommendations(self, contract_scores: List[ContractRiskScore],
                                              portfolio_metrics: PortfolioContractMetrics,
                                              interaction_assessment: InteractionRiskAssessment,
                                              risk_alerts: List[ContractRiskAlert],
                                              overall_risk: float) -> List[str]:
        """Generate comprehensive risk management recommendations"""
        recommendations = []

        # High-priority recommendations from alerts
        critical_alerts = [alert for alert in risk_alerts if alert.severity == 'CRITICAL']
        for alert in critical_alerts[:2]:  # Top 2 critical alerts
            recommendations.append(f"URGENT: {alert.recommended_action}")

        # Portfolio-level recommendations
        if portfolio_metrics.critical_vulnerabilities > 0:
            recommendations.append("CRITICAL: Immediately patch all critical vulnerabilities before production use")

        if portfolio_metrics.audited_contracts / portfolio_metrics.total_contracts < 0.7:
            recommendations.append("HIGH: Increase audit coverage - less than 70% of contracts are audited")

        if portfolio_metrics.outdated_audits > 0:
            recommendations.append(f"MEDIUM: Update {portfolio_metrics.outdated_audits} outdated security audits")

        # Interaction-specific recommendations
        if interaction_assessment.overall_interaction_risk > 0.6:
            recommendations.append("HIGH: Implement interaction monitoring and circuit breakers")

        if len(interaction_assessment.call_graph.circular_dependencies) > 0:
            recommendations.append("MEDIUM: Resolve circular dependencies to prevent recursive vulnerabilities")

        # Contract-specific recommendations
        high_risk_contracts = [score for score in contract_scores if score.overall_risk_score > 0.7]
        for contract in high_risk_contracts[:2]:  # Top 2 riskiest contracts
            if contract.audit_score < 0.5:
                recommendations.append(f"HIGH: Priority audit needed for {contract.contract_name}")
            if contract.complexity_score > 0.7:
                recommendations.append(f"MEDIUM: Simplify {contract.contract_name} to reduce complexity risk")

        # General security improvements
        if overall_risk > 0.5:
            recommendations.append("Implement comprehensive security monitoring and incident response procedures")

        return recommendations[:8]  # Limit to top 8 recommendations

    def _generate_monitoring_requirements(self, contract_scores: List[ContractRiskScore],
                                        interaction_assessment: InteractionRiskAssessment,
                                        risk_alerts: List[ContractRiskAlert]) -> List[str]:
        """Generate monitoring requirements"""
        requirements = []

        # Contract-specific monitoring
        high_risk_contracts = [score for score in contract_scores if score.overall_risk_score > 0.6]
        if high_risk_contracts:
            contract_names = [contract.contract_name for contract in high_risk_contracts[:3]]
            requirements.append(f"Real-time monitoring for high-risk contracts: {', '.join(contract_names)}")

        # Interaction monitoring
        if interaction_assessment.critical_interactions:
            requirements.append("Monitor critical contract interactions for anomalous patterns")

        if interaction_assessment.overall_interaction_risk > 0.5:
            requirements.append("Implement MEV and front-running detection systems")

        # Alert-based monitoring
        critical_alerts = [alert for alert in risk_alerts if alert.severity in ['CRITICAL', 'HIGH']]
        if critical_alerts:
            requirements.append("Set up automated alerting for critical security events")

        # General monitoring
        requirements.append("Weekly security posture assessment and risk score updates")
        requirements.append("Continuous vulnerability scanning and exploit database monitoring")

        return requirements

    def _determine_next_review_date(self, risk_level: str, risk_alerts: List[ContractRiskAlert]) -> datetime:
        """Determine when next risk review should occur"""
        base_days = {
            "CRITICAL": 1,
            "HIGH": 3,
            "MODERATE": 7,
            "LOW": 14,
            "MINIMAL": 30
        }

        days = base_days.get(risk_level, 7)

        # Adjust for critical alerts
        critical_alert_count = len([alert for alert in risk_alerts if alert.severity == 'CRITICAL'])
        if critical_alert_count > 0:
            days = 1  # Daily review for critical issues

        return datetime.now() + timedelta(days=days)

    async def export_assessment_report(self, assessment: ComprehensiveContractRiskAssessment,
                                     output_path: Optional[str] = None) -> str:
        """Export comprehensive assessment report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"contract_risk_assessment_{timestamp}.json"

        # Convert assessment to dict for JSON serialization
        report_data = {
            'assessment_metadata': {
                'timestamp': assessment.timestamp.isoformat(),
                'overall_risk': assessment.overall_portfolio_risk,
                'risk_level': assessment.risk_level,
                'confidence_score': assessment.confidence_score,
                'next_review_date': assessment.next_review_date.isoformat()
            },
            'portfolio_metrics': asdict(assessment.portfolio_metrics),
            'contract_scores': [asdict(score) for score in assessment.contract_scores],
            'risk_alerts': [asdict(alert) for alert in assessment.risk_alerts],
            'recommendations': assessment.recommendations,
            'monitoring_requirements': assessment.monitoring_requirements,
            'interaction_summary': {
                'overall_interaction_risk': assessment.interaction_assessment.overall_interaction_risk,
                'risk_level': assessment.interaction_assessment.risk_level,
                'pattern_count': len(assessment.interaction_assessment.interaction_patterns),
                'critical_interactions': assessment.interaction_assessment.critical_interactions
            },
            'exploit_proximity_summary': {
                'max_proximity': max(assessment.exploit_proximity_analysis.values()) if assessment.exploit_proximity_analysis else 0,
                'high_risk_contracts': [
                    contract_id for contract_id, proximity in assessment.exploit_proximity_analysis.items()
                    if proximity > 0.7
                ]
            }
        }

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Contract risk assessment report exported to: {output_path}")
        return output_path

# Example usage
async def main():
    """Example usage of the smart contract risk engine"""
    engine = SmartContractRiskEngine()

    # Example contracts data
    contracts_data = {
        'algofi_pool': {
            'name': 'AlgoFi Lending Pool',
            'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate', 'external_call'],
            'features': ['access_control', 'reentrancy_protection', 'emergency_pause'],
            'deployment_date': '2021-11-01',
            'lines_of_code': 1200,
            'audits': [
                {
                    'auditor': 'runtime_verification',
                    'date': '2021-12-01',
                    'score': 88,
                    'type': 'formal_verification',
                    'vulnerabilities_found': 2,
                    'vulnerabilities_fixed': 2
                }
            ]
        },
        'tinyman_dex': {
            'name': 'Tinyman DEX',
            'functions': ['swap', 'add_liquidity', 'remove_liquidity', 'external_call'],
            'features': ['slippage_protection', 'access_control'],
            'deployment_date': '2021-10-01',
            'lines_of_code': 800
        },
        'oracle_contract': {
            'name': 'Price Oracle',
            'functions': ['update_price', 'get_price', 'validate_data'],
            'features': ['access_control', 'staleness_check'],
            'deployment_date': '2022-01-01',
            'lines_of_code': 400
        }
    }

    # Example interaction history
    interaction_history = [
        {
            'source': 'algofi_pool',
            'target': 'oracle_contract',
            'type': 'price_query',
            'frequency': 150,
            'gas_usage': 25000,
            'success_rate': 0.98,
            'last_interaction': '2024-01-15T10:30:00'
        }
    ]

    # Perform comprehensive risk assessment
    assessment = await engine.assess_contract_portfolio_risk(contracts_data, interaction_history)

    print(f"\n=== Smart Contract Portfolio Risk Assessment ===")
    print(f"Overall Portfolio Risk: {assessment.overall_portfolio_risk:.2f}")
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Confidence Score: {assessment.confidence_score:.2f}")
    print(f"Next Review Date: {assessment.next_review_date.strftime('%Y-%m-%d')}")

    print(f"\n=== Portfolio Metrics ===")
    metrics = assessment.portfolio_metrics
    print(f"Total Contracts: {metrics.total_contracts}")
    print(f"Audited Contracts: {metrics.audited_contracts}")
    print(f"High Risk Contracts: {metrics.high_risk_contracts}")
    print(f"Critical Vulnerabilities: {metrics.critical_vulnerabilities}")
    print(f"Complex Interactions: {metrics.complex_interactions}")

    print(f"\n=== Contract Risk Scores ===")
    for score in assessment.contract_scores:
        print(f"{score.contract_name} ({score.contract_category}):")
        print(f"  Overall Risk: {score.overall_risk_score:.2f} ({score.risk_tier})")
        print(f"  Security Score: {score.security_score:.2f}")
        print(f"  Audit Score: {score.audit_score:.2f}")
        print(f"  Complexity Score: {score.complexity_score:.2f}")
        print(f"  Interaction Risk: {score.interaction_risk_score:.2f}")

    print(f"\n=== Risk Alerts ===")
    for alert in assessment.risk_alerts:
        severity_emoji = "🚨" if alert.severity == "CRITICAL" else "⚠️" if alert.severity == "HIGH" else "⚡"
        print(f"{severity_emoji} {alert.severity}: {alert.message}")
        print(f"   Action: {alert.recommended_action}")

    print(f"\n=== Interaction Assessment ===")
    interaction = assessment.interaction_assessment
    print(f"Interaction Risk: {interaction.overall_interaction_risk:.2f} ({interaction.risk_level})")
    print(f"Patterns Detected: {len(interaction.interaction_patterns)}")
    print(f"Critical Interactions: {len(interaction.critical_interactions)}")
    print(f"Call Graph Complexity: {interaction.call_graph.complexity_score:.2f}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(assessment.recommendations, 1):
        print(f"{i}. {rec}")

    print(f"\n=== Monitoring Requirements ===")
    for req in assessment.monitoring_requirements:
        print(f"• {req}")

    # Export report
    report_path = await engine.export_assessment_report(assessment)
    print(f"\n=== Report Exported ===")
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())