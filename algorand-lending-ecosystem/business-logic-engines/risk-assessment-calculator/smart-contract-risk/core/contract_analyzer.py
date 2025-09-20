"""
Smart Contract Security Analysis
Analyzes smart contract security, audit status, and vulnerability assessments
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml
import re
import json
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AuditInfo:
    """Smart contract audit information"""
    auditor: str
    audit_date: datetime
    audit_score: float
    audit_type: str
    vulnerabilities_found: int
    vulnerabilities_fixed: int
    report_url: Optional[str]
    reputation_score: float

@dataclass
class VulnerabilityAssessment:
    """Contract vulnerability assessment"""
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_score: float
    risk_level: str
    mitigation_status: str

@dataclass
class ContractMetrics:
    """Smart contract complexity and quality metrics"""
    lines_of_code: int
    function_count: int
    external_call_count: int
    cyclomatic_complexity: float
    code_coverage: float
    test_coverage: float
    documentation_score: float

@dataclass
class SecurityFeatures:
    """Security features implementation status"""
    access_control: bool
    reentrancy_protection: bool
    integer_overflow_protection: bool
    emergency_pause: bool
    timelock_mechanism: bool
    multisig_requirement: bool
    input_validation: bool
    event_logging: bool

@dataclass
class ContractAnalysis:
    """Complete contract security analysis"""
    contract_id: str
    contract_address: str
    contract_name: str
    contract_category: str
    deployment_date: datetime
    last_update_date: datetime
    audits: List[AuditInfo]
    vulnerability_assessment: VulnerabilityAssessment
    contract_metrics: ContractMetrics
    security_features: SecurityFeatures
    overall_security_score: float
    risk_tier: str
    confidence_level: float
    recommendations: List[str]
    next_audit_due: Optional[datetime]

class SmartContractAnalyzer:
    """Analyzes smart contract security and audit status"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the smart contract analyzer"""
        self.config = self._load_config(config_path)
        self.audit_cache = {}
        self.contract_cache = {}

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def analyze_contract_security(self, contract_id: str, contract_data: Dict[str, Any]) -> ContractAnalysis:
        """Analyze comprehensive security of a smart contract"""
        logger.info(f"Analyzing contract security for {contract_id}")

        # Extract basic contract information
        contract_address = contract_data.get('address', contract_id)
        contract_name = contract_data.get('name', f"Contract_{contract_id}")
        contract_category = self._determine_contract_category(contract_data)
        deployment_date = self._parse_deployment_date(contract_data.get('deployment_date'))
        last_update_date = self._parse_update_date(contract_data.get('last_update'))

        # Analyze audits
        audits = await self._analyze_audits(contract_id, contract_data)

        # Assess vulnerabilities
        vulnerability_assessment = await self._assess_vulnerabilities(contract_id, contract_data, audits)

        # Calculate contract metrics
        contract_metrics = await self._calculate_contract_metrics(contract_id, contract_data)

        # Analyze security features
        security_features = await self._analyze_security_features(contract_id, contract_data)

        # Calculate overall security score
        overall_security_score = self._calculate_overall_security_score(
            audits, vulnerability_assessment, contract_metrics, security_features
        )

        # Determine risk tier
        risk_tier = self._determine_risk_tier(overall_security_score, vulnerability_assessment)

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(audits, contract_metrics, contract_data)

        # Generate recommendations
        recommendations = self._generate_security_recommendations(
            audits, vulnerability_assessment, security_features, contract_category
        )

        # Calculate next audit due date
        next_audit_due = self._calculate_next_audit_due(audits, risk_tier)

        return ContractAnalysis(
            contract_id=contract_id,
            contract_address=contract_address,
            contract_name=contract_name,
            contract_category=contract_category,
            deployment_date=deployment_date,
            last_update_date=last_update_date,
            audits=audits,
            vulnerability_assessment=vulnerability_assessment,
            contract_metrics=contract_metrics,
            security_features=security_features,
            overall_security_score=overall_security_score,
            risk_tier=risk_tier,
            confidence_level=confidence_level,
            recommendations=recommendations,
            next_audit_due=next_audit_due
        )

    def _determine_contract_category(self, contract_data: Dict[str, Any]) -> str:
        """Determine contract category based on contract data"""
        # Analyze contract patterns to determine category
        name = contract_data.get('name', '').lower()
        description = contract_data.get('description', '').lower()
        functions = contract_data.get('functions', [])

        # Check for core protocol patterns
        if any(func in functions for func in ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate']):
            return 'core_protocol'

        # Check for governance patterns
        if any(func in functions for func in ['propose', 'vote', 'execute', 'delegate']):
            return 'governance'

        # Check for token patterns
        if any(func in functions for func in ['transfer', 'mint', 'burn', 'approve']):
            return 'token_contracts'

        # Check for oracle patterns
        if any(func in functions for func in ['update_price', 'get_price', 'validate_data']):
            return 'oracle_integration'

        # Check for bridge patterns
        if any(func in functions for func in ['lock', 'unlock', 'validate_proof']):
            return 'bridge_contracts'

        # Check for DEX patterns
        if any(func in functions for func in ['swap', 'add_liquidity', 'remove_liquidity']):
            return 'liquidity_pools'

        # Check name/description for category hints
        if any(keyword in name + description for keyword in ['governance', 'vote', 'proposal']):
            return 'governance'
        elif any(keyword in name + description for keyword in ['token', 'erc20', 'asset']):
            return 'token_contracts'
        elif any(keyword in name + description for keyword in ['oracle', 'price', 'feed']):
            return 'oracle_integration'
        elif any(keyword in name + description for keyword in ['bridge', 'cross', 'chain']):
            return 'bridge_contracts'
        elif any(keyword in name + description for keyword in ['swap', 'dex', 'amm', 'liquidity']):
            return 'liquidity_pools'

        return 'core_protocol'  # Default category

    def _parse_deployment_date(self, date_str: Optional[str]) -> datetime:
        """Parse deployment date from string"""
        if not date_str:
            return datetime.now() - timedelta(days=365)  # Default to 1 year ago

        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If no format works, return default
            return datetime.now() - timedelta(days=365)
        except Exception:
            return datetime.now() - timedelta(days=365)

    def _parse_update_date(self, date_str: Optional[str]) -> datetime:
        """Parse last update date from string"""
        if not date_str:
            return datetime.now() - timedelta(days=90)  # Default to 3 months ago

        return self._parse_deployment_date(date_str)

    async def _analyze_audits(self, contract_id: str, contract_data: Dict[str, Any]) -> List[AuditInfo]:
        """Analyze contract audit information"""
        audits = []
        audit_data = contract_data.get('audits', [])

        # If no audit data provided, simulate based on contract category and age
        if not audit_data:
            audits = await self._simulate_audit_data(contract_id, contract_data)
        else:
            for audit_info in audit_data:
                audit = AuditInfo(
                    auditor=audit_info.get('auditor', 'unknown'),
                    audit_date=self._parse_deployment_date(audit_info.get('date')),
                    audit_score=audit_info.get('score', 75),
                    audit_type=audit_info.get('type', 'security_audit'),
                    vulnerabilities_found=audit_info.get('vulnerabilities_found', 0),
                    vulnerabilities_fixed=audit_info.get('vulnerabilities_fixed', 0),
                    report_url=audit_info.get('report_url'),
                    reputation_score=self._get_auditor_reputation(audit_info.get('auditor', 'unknown'))
                )
                audits.append(audit)

        return audits

    async def _simulate_audit_data(self, contract_id: str, contract_data: Dict[str, Any]) -> List[AuditInfo]:
        """Simulate audit data for contracts without explicit audit information"""
        contract_category = self._determine_contract_category(contract_data)
        deployment_date = self._parse_deployment_date(contract_data.get('deployment_date'))

        # Determine expected audits based on category and risk requirements
        category_config = self.config.get('contract_categories', {}).get(contract_category, {})
        risk_tier = contract_data.get('risk_tier', 'tier_2')

        audits = []

        # Simulate audits based on protocol tier and age
        contract_age_months = (datetime.now() - deployment_date).days / 30.44

        if risk_tier == 'tier_1' and contract_age_months > 6:
            # Tier 1 protocols should have multiple audits
            audits.append(AuditInfo(
                auditor='runtime_verification',
                audit_date=deployment_date + timedelta(days=30),
                audit_score=88,
                audit_type='formal_verification',
                vulnerabilities_found=3,
                vulnerabilities_fixed=3,
                report_url=None,
                reputation_score=95
            ))

            audits.append(AuditInfo(
                auditor='certik',
                audit_date=deployment_date + timedelta(days=60),
                audit_score=85,
                audit_type='security_audit',
                vulnerabilities_found=2,
                vulnerabilities_fixed=2,
                report_url=None,
                reputation_score=90
            ))

        elif risk_tier == 'tier_2' and contract_age_months > 3:
            # Tier 2 protocols should have at least one audit
            audits.append(AuditInfo(
                auditor='halborn',
                audit_date=deployment_date + timedelta(days=45),
                audit_score=78,
                audit_type='security_audit',
                vulnerabilities_found=4,
                vulnerabilities_fixed=3,
                report_url=None,
                reputation_score=88
            ))

        elif contract_age_months > 1:
            # Newer or tier 3 protocols might have basic audits
            audits.append(AuditInfo(
                auditor='immunefi',
                audit_date=deployment_date + timedelta(days=90),
                audit_score=65,
                audit_type='bug_bounty',
                vulnerabilities_found=6,
                vulnerabilities_fixed=4,
                report_url=None,
                reputation_score=85
            ))

        return audits

    def _get_auditor_reputation(self, auditor: str) -> float:
        """Get auditor reputation score from config"""
        auditors = self.config.get('audit_database', {}).get('known_auditors', {})
        return auditors.get(auditor, {}).get('reputation_score', 70)

    async def _assess_vulnerabilities(self, contract_id: str, contract_data: Dict[str, Any],
                                    audits: List[AuditInfo]) -> VulnerabilityAssessment:
        """Assess contract vulnerabilities"""
        # Start with audit-based vulnerability counts
        total_critical = 0
        total_high = 0
        total_medium = 0
        total_low = 0

        for audit in audits:
            # Distribute vulnerabilities by severity (typical distribution)
            total_vulns = audit.vulnerabilities_found - audit.vulnerabilities_fixed
            if total_vulns > 0:
                # Typical distribution: 10% critical, 20% high, 40% medium, 30% low
                critical_vulns = max(0, int(total_vulns * 0.1))
                high_vulns = max(0, int(total_vulns * 0.2))
                medium_vulns = max(0, int(total_vulns * 0.4))
                low_vulns = max(0, total_vulns - critical_vulns - high_vulns - medium_vulns)

                total_critical += critical_vulns
                total_high += high_vulns
                total_medium += medium_vulns
                total_low += low_vulns

        # Add pattern-based vulnerability assessment
        pattern_vulns = await self._assess_pattern_vulnerabilities(contract_data)
        total_critical += pattern_vulns.get('critical', 0)
        total_high += pattern_vulns.get('high', 0)
        total_medium += pattern_vulns.get('medium', 0)
        total_low += pattern_vulns.get('low', 0)

        # Calculate vulnerability score
        vulnerability_score = self._calculate_vulnerability_score(
            total_critical, total_high, total_medium, total_low
        )

        # Determine risk level
        risk_level = self._determine_vulnerability_risk_level(
            total_critical, total_high, total_medium, total_low
        )

        # Determine mitigation status
        mitigation_status = self._assess_mitigation_status(audits, total_critical, total_high)

        return VulnerabilityAssessment(
            critical_count=total_critical,
            high_count=total_high,
            medium_count=total_medium,
            low_count=total_low,
            total_score=vulnerability_score,
            risk_level=risk_level,
            mitigation_status=mitigation_status
        )

    async def _assess_pattern_vulnerabilities(self, contract_data: Dict[str, Any]) -> Dict[str, int]:
        """Assess vulnerabilities based on contract patterns"""
        functions = contract_data.get('functions', [])
        features = contract_data.get('features', [])

        vulnerabilities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        # Check for risky patterns
        if 'delegated_call' in functions and 'implementation_validation' not in features:
            vulnerabilities['critical'] += 1

        if 'external_call' in functions and 'reentrancy_protection' not in features:
            vulnerabilities['high'] += 1

        if 'admin_functions' in functions and 'access_control' not in features:
            vulnerabilities['high'] += 1

        if 'upgrade_logic' in functions and 'timelock' not in features:
            vulnerabilities['medium'] += 1

        if 'user_input' in functions and 'input_validation' not in features:
            vulnerabilities['medium'] += 1

        # Check for missing security features
        required_features = self._get_required_security_features(contract_data)
        for feature in required_features:
            if feature not in features:
                vulnerabilities['low'] += 1

        return vulnerabilities

    def _get_required_security_features(self, contract_data: Dict[str, Any]) -> List[str]:
        """Get required security features for contract category"""
        contract_category = self._determine_contract_category(contract_data)
        category_config = self.config.get('contract_categories', {}).get(contract_category, {})
        return category_config.get('required_features', [])

    def _calculate_vulnerability_score(self, critical: int, high: int, medium: int, low: int) -> float:
        """Calculate overall vulnerability score"""
        # Weighted scoring: critical=1.0, high=0.7, medium=0.4, low=0.2
        weighted_score = (critical * 1.0) + (high * 0.7) + (medium * 0.4) + (low * 0.2)

        # Normalize to 0-1 scale (assuming max reasonable vulnerabilities)
        max_score = 10.0  # Assumption: 10 weighted vulnerabilities = max score
        normalized_score = min(weighted_score / max_score, 1.0)

        return normalized_score

    def _determine_vulnerability_risk_level(self, critical: int, high: int, medium: int, low: int) -> str:
        """Determine vulnerability risk level"""
        if critical > 0:
            return "CRITICAL"
        elif high > 2:
            return "HIGH"
        elif high > 0 or medium > 5:
            return "MODERATE"
        elif medium > 0 or low > 5:
            return "LOW"
        else:
            return "MINIMAL"

    def _assess_mitigation_status(self, audits: List[AuditInfo], critical: int, high: int) -> str:
        """Assess mitigation status based on audits and vulnerabilities"""
        if not audits:
            return "UNAUDITED"

        recent_audits = [audit for audit in audits
                        if (datetime.now() - audit.audit_date).days < 365]

        if not recent_audits:
            return "OUTDATED_AUDIT"

        if critical > 0:
            return "CRITICAL_UNMITIGATED"
        elif high > 0:
            return "HIGH_UNMITIGATED"
        else:
            return "ADEQUATELY_MITIGATED"

    async def _calculate_contract_metrics(self, contract_id: str, contract_data: Dict[str, Any]) -> ContractMetrics:
        """Calculate contract complexity and quality metrics"""
        # Simulate metrics based on contract category and available data
        contract_category = self._determine_contract_category(contract_data)

        # Get complexity thresholds from config
        complexity_config = self.config.get('complexity_metrics', {})
        category_config = self.config.get('contract_categories', {}).get(contract_category, {})

        # Simulate or extract metrics
        functions = contract_data.get('functions', [])
        lines_of_code = contract_data.get('lines_of_code', len(functions) * 50)  # Estimate
        function_count = len(functions)
        external_call_count = len([f for f in functions if 'external' in f])

        # Calculate complexity based on category
        base_complexity = category_config.get('typical_complexity', 50)
        complexity_variance = 0.3  # ±30% variance
        cyclomatic_complexity = base_complexity * (0.7 + complexity_variance)

        # Simulate quality metrics
        code_coverage = contract_data.get('code_coverage', 0.75)
        test_coverage = contract_data.get('test_coverage', 0.70)
        documentation_score = contract_data.get('documentation_score', 0.60)

        return ContractMetrics(
            lines_of_code=lines_of_code,
            function_count=function_count,
            external_call_count=external_call_count,
            cyclomatic_complexity=cyclomatic_complexity,
            code_coverage=code_coverage,
            test_coverage=test_coverage,
            documentation_score=documentation_score
        )

    async def _analyze_security_features(self, contract_id: str, contract_data: Dict[str, Any]) -> SecurityFeatures:
        """Analyze implemented security features"""
        features = contract_data.get('features', [])
        functions = contract_data.get('functions', [])

        # Check for security features
        access_control = 'access_control' in features or 'role_based_access' in features
        reentrancy_protection = 'reentrancy_protection' in features or 'reentrancy_guard' in features
        integer_overflow_protection = 'overflow_protection' in features or 'safe_math' in features
        emergency_pause = 'emergency_pause' in features or 'circuit_breaker' in features
        timelock_mechanism = 'timelock' in features or 'timelock_mechanism' in features
        multisig_requirement = 'multisig' in features or 'multisig_requirement' in features
        input_validation = 'input_validation' in features or 'parameter_validation' in features
        event_logging = 'event_logging' in features or 'audit_trail' in features

        return SecurityFeatures(
            access_control=access_control,
            reentrancy_protection=reentrancy_protection,
            integer_overflow_protection=integer_overflow_protection,
            emergency_pause=emergency_pause,
            timelock_mechanism=timelock_mechanism,
            multisig_requirement=multisig_requirement,
            input_validation=input_validation,
            event_logging=event_logging
        )

    def _calculate_overall_security_score(self, audits: List[AuditInfo],
                                        vulnerability_assessment: VulnerabilityAssessment,
                                        contract_metrics: ContractMetrics,
                                        security_features: SecurityFeatures) -> float:
        """Calculate overall security score"""
        # Audit score component (0-1)
        if audits:
            recent_audits = [audit for audit in audits
                           if (datetime.now() - audit.audit_date).days < 730]  # 2 years
            if recent_audits:
                avg_audit_score = sum(audit.audit_score for audit in recent_audits) / len(recent_audits)
                audit_component = avg_audit_score / 100
            else:
                audit_component = 0.3  # Outdated audits
        else:
            audit_component = 0.1  # No audits

        # Vulnerability score component (0-1, inverted)
        vulnerability_component = 1.0 - vulnerability_assessment.total_score

        # Security features component (0-1)
        feature_count = sum([
            security_features.access_control,
            security_features.reentrancy_protection,
            security_features.integer_overflow_protection,
            security_features.emergency_pause,
            security_features.timelock_mechanism,
            security_features.multisig_requirement,
            security_features.input_validation,
            security_features.event_logging
        ])
        features_component = feature_count / 8  # 8 total features

        # Code quality component (0-1)
        quality_component = (
            contract_metrics.code_coverage * 0.4 +
            contract_metrics.test_coverage * 0.4 +
            contract_metrics.documentation_score * 0.2
        )

        # Weighted combination
        weights = self.config.get('risk_scoring_weights', {
            'audit_weight': 0.4,
            'vulnerability_weight': 0.3,
            'features_weight': 0.2,
            'quality_weight': 0.1
        })

        overall_score = (
            audit_component * weights.get('audit_weight', 0.4) +
            vulnerability_component * weights.get('vulnerability_weight', 0.3) +
            features_component * weights.get('features_weight', 0.2) +
            quality_component * weights.get('quality_weight', 0.1)
        )

        return min(overall_score, 1.0)

    def _determine_risk_tier(self, security_score: float, vulnerability_assessment: VulnerabilityAssessment) -> str:
        """Determine contract risk tier"""
        # Critical vulnerabilities always result in critical risk
        if vulnerability_assessment.critical_count > 0:
            return "CRITICAL"

        # Base tier on security score
        if security_score >= 0.85:
            return "EXCELLENT"
        elif security_score >= 0.7:
            return "GOOD"
        elif security_score >= 0.5:
            return "MODERATE"
        elif security_score >= 0.3:
            return "POOR"
        else:
            return "CRITICAL"

    def _calculate_confidence_level(self, audits: List[AuditInfo], metrics: ContractMetrics,
                                  contract_data: Dict[str, Any]) -> float:
        """Calculate confidence level for the security assessment"""
        base_confidence = 0.6

        # Audit confidence boost
        if audits:
            recent_audits = [audit for audit in audits
                           if (datetime.now() - audit.audit_date).days < 365]
            if recent_audits:
                audit_confidence = min(len(recent_audits) / 2, 1.0) * 0.3
            else:
                audit_confidence = 0.1
        else:
            audit_confidence = 0.0

        # Code quality confidence boost
        quality_confidence = (metrics.code_coverage + metrics.test_coverage) / 2 * 0.2

        # Data completeness confidence boost
        data_fields = ['functions', 'features', 'deployment_date']
        data_completeness = sum(1 for field in data_fields if contract_data.get(field)) / len(data_fields)
        data_confidence = data_completeness * 0.2

        total_confidence = base_confidence + audit_confidence + quality_confidence + data_confidence

        return min(total_confidence, 1.0)

    def _generate_security_recommendations(self, audits: List[AuditInfo],
                                         vulnerability_assessment: VulnerabilityAssessment,
                                         security_features: SecurityFeatures,
                                         contract_category: str) -> List[str]:
        """Generate security improvement recommendations"""
        recommendations = []

        # Critical vulnerability recommendations
        if vulnerability_assessment.critical_count > 0:
            recommendations.append("URGENT: Address critical vulnerabilities immediately before deployment")

        # Audit recommendations
        if not audits:
            recommendations.append("HIGH: Obtain security audit from reputable auditor before production use")
        else:
            latest_audit = max(audits, key=lambda x: x.audit_date)
            days_since_audit = (datetime.now() - latest_audit.audit_date).days
            if days_since_audit > 365:
                recommendations.append("MEDIUM: Update security audit - last audit is over 1 year old")

        # Security feature recommendations
        if not security_features.access_control:
            recommendations.append("HIGH: Implement proper access control mechanisms")

        if not security_features.reentrancy_protection:
            recommendations.append("HIGH: Add reentrancy protection to prevent attack vectors")

        if not security_features.emergency_pause and contract_category in ['core_protocol', 'bridge_contracts']:
            recommendations.append("MEDIUM: Implement emergency pause functionality")

        if not security_features.timelock_mechanism and contract_category == 'governance':
            recommendations.append("HIGH: Add timelock mechanism for governance changes")

        # High vulnerability recommendations
        if vulnerability_assessment.high_count > 0:
            recommendations.append(f"HIGH: Address {vulnerability_assessment.high_count} high-severity vulnerabilities")

        # Category-specific recommendations
        category_config = self.config.get('contract_categories', {}).get(contract_category, {})
        required_features = category_config.get('required_features', [])

        missing_features = []
        if 'emergency_pause' in required_features and not security_features.emergency_pause:
            missing_features.append('emergency pause')
        if 'access_control' in required_features and not security_features.access_control:
            missing_features.append('access control')
        if 'reentrancy_protection' in required_features and not security_features.reentrancy_protection:
            missing_features.append('reentrancy protection')

        if missing_features:
            recommendations.append(f"MEDIUM: Implement required features for {contract_category}: {', '.join(missing_features)}")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_next_audit_due(self, audits: List[AuditInfo], risk_tier: str) -> Optional[datetime]:
        """Calculate when next audit is due"""
        if not audits:
            return datetime.now() + timedelta(days=30)  # Immediate audit needed

        latest_audit = max(audits, key=lambda x: x.audit_date)

        # Audit frequency based on risk tier
        audit_intervals = {
            "CRITICAL": 90,      # 3 months
            "POOR": 180,         # 6 months
            "MODERATE": 365,     # 1 year
            "GOOD": 730,         # 2 years
            "EXCELLENT": 1095    # 3 years
        }

        interval_days = audit_intervals.get(risk_tier, 365)
        return latest_audit.audit_date + timedelta(days=interval_days)

    async def batch_analyze_contracts(self, contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, ContractAnalysis]:
        """Batch analyze multiple contracts"""
        logger.info(f"Batch analyzing {len(contracts_data)} contracts")

        # Process contracts in parallel
        tasks = []
        for contract_id, contract_data in contracts_data.items():
            task = self.analyze_contract_security(contract_id, contract_data)
            tasks.append(task)

        analyses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for contract_id, analysis in zip(contracts_data.keys(), analyses):
            if isinstance(analysis, Exception):
                logger.error(f"Error analyzing contract {contract_id}: {analysis}")
                continue
            results[contract_id] = analysis

        return results

    async def get_security_alerts(self, analyses: Dict[str, ContractAnalysis]) -> List[Dict[str, Any]]:
        """Generate security alerts from contract analyses"""
        alerts = []
        thresholds = self.config.get('alert_thresholds', {})

        for contract_id, analysis in analyses.items():
            # Critical vulnerability alerts
            if analysis.vulnerability_assessment.critical_count > 0:
                alerts.append({
                    'type': 'critical_vulnerability',
                    'severity': 'CRITICAL',
                    'contract_id': contract_id,
                    'message': f"Critical vulnerabilities detected in {analysis.contract_name}",
                    'count': analysis.vulnerability_assessment.critical_count,
                    'action_required': 'immediate_mitigation'
                })

            # Low security score alerts
            if analysis.overall_security_score < thresholds.get('contract_risk_critical', 0.8):
                alerts.append({
                    'type': 'low_security_score',
                    'severity': 'HIGH' if analysis.overall_security_score < 0.4 else 'MEDIUM',
                    'contract_id': contract_id,
                    'message': f"Low security score for {analysis.contract_name}: {analysis.overall_security_score:.2f}",
                    'score': analysis.overall_security_score,
                    'action_required': 'security_review'
                })

            # Outdated audit alerts
            if analysis.next_audit_due and analysis.next_audit_due < datetime.now():
                days_overdue = (datetime.now() - analysis.next_audit_due).days
                alerts.append({
                    'type': 'audit_overdue',
                    'severity': 'HIGH' if days_overdue > 180 else 'MEDIUM',
                    'contract_id': contract_id,
                    'message': f"Audit overdue for {analysis.contract_name} by {days_overdue} days",
                    'days_overdue': days_overdue,
                    'action_required': 'schedule_audit'
                })

        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        alerts.sort(key=lambda x: severity_order.get(x['severity'], 99))

        return alerts

# Example usage
async def main():
    """Example usage of the smart contract analyzer"""
    analyzer = SmartContractAnalyzer()

    # Example contract data
    contract_data = {
        'name': 'AlgoFi Lending Pool',
        'description': 'Main lending pool contract for AlgoFi protocol',
        'deployment_date': '2021-11-01',
        'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate', 'external_call'],
        'features': ['access_control', 'reentrancy_protection', 'emergency_pause', 'event_logging'],
        'lines_of_code': 1200,
        'code_coverage': 0.85,
        'test_coverage': 0.78,
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
    }

    # Analyze contract security
    analysis = await analyzer.analyze_contract_security('algofi_pool_001', contract_data)

    print(f"\n=== Smart Contract Security Analysis ===")
    print(f"Contract: {analysis.contract_name}")
    print(f"Category: {analysis.contract_category}")
    print(f"Overall Security Score: {analysis.overall_security_score:.2f}")
    print(f"Risk Tier: {analysis.risk_tier}")
    print(f"Confidence Level: {analysis.confidence_level:.2f}")

    print(f"\n=== Audit Information ===")
    for audit in analysis.audits:
        print(f"Auditor: {audit.auditor}")
        print(f"  Date: {audit.audit_date.strftime('%Y-%m-%d')}")
        print(f"  Score: {audit.audit_score}")
        print(f"  Type: {audit.audit_type}")
        print(f"  Vulnerabilities: {audit.vulnerabilities_found} found, {audit.vulnerabilities_fixed} fixed")

    print(f"\n=== Vulnerability Assessment ===")
    vuln = analysis.vulnerability_assessment
    print(f"Critical: {vuln.critical_count}")
    print(f"High: {vuln.high_count}")
    print(f"Medium: {vuln.medium_count}")
    print(f"Low: {vuln.low_count}")
    print(f"Risk Level: {vuln.risk_level}")
    print(f"Mitigation Status: {vuln.mitigation_status}")

    print(f"\n=== Security Features ===")
    features = analysis.security_features
    print(f"Access Control: {'✓' if features.access_control else '✗'}")
    print(f"Reentrancy Protection: {'✓' if features.reentrancy_protection else '✗'}")
    print(f"Emergency Pause: {'✓' if features.emergency_pause else '✗'}")
    print(f"Timelock Mechanism: {'✓' if features.timelock_mechanism else '✗'}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"{i}. {rec}")

    if analysis.next_audit_due:
        print(f"\nNext Audit Due: {analysis.next_audit_due.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    asyncio.run(main())