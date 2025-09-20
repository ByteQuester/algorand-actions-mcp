"""
Regulatory Pressure and Compliance Risk Monitoring
Monitors regulatory developments, enforcement actions, and compliance risks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class RegulatoryEventType(Enum):
    """Types of regulatory events"""
    ENFORCEMENT_ACTION = "enforcement_action"
    POLICY_PROPOSAL = "policy_proposal"
    GUIDANCE_UPDATE = "guidance_update"
    JURISDICTION_BAN = "jurisdiction_ban"
    INVESTIGATION = "investigation"
    LEGISLATION = "legislation"
    COURT_RULING = "court_ruling"
    INTERNATIONAL_STANDARD = "international_standard"

class RiskSeverity(Enum):
    """Regulatory risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INFORMATIONAL = "informational"

class Jurisdiction(Enum):
    """Major jurisdictions for regulatory monitoring"""
    US = "US"
    EU = "EU"
    UK = "UK"
    CN = "CN"
    JP = "JP"
    SG = "SG"
    GLOBAL = "GLOBAL"

@dataclass
class RegulatoryEvent:
    """Individual regulatory event"""
    event_id: str
    event_type: RegulatoryEventType
    jurisdiction: Jurisdiction
    title: str
    description: str

    # Impact assessment
    severity: RiskSeverity
    impact_score: float  # 1-10
    urgency: float  # 1-10

    # Timing
    event_date: datetime
    effective_date: Optional[datetime]
    deadline: Optional[datetime]

    # Content analysis
    affects_algorand: bool
    affects_defi: bool
    affects_governance: bool
    keywords: List[str]

    # Confidence and sources
    confidence_level: float  # 0-1
    sources: List[str]
    reliability_score: float  # 0-1

@dataclass
class ComplianceRequirement:
    """Specific compliance requirement"""
    requirement_id: str
    jurisdiction: Jurisdiction
    category: str  # kyc, aml, reporting, licensing

    description: str
    applicability_score: float  # 0-1 how much it applies to Algorand
    implementation_complexity: float  # 1-10

    current_status: str  # compliant, partial, non_compliant, unknown
    compliance_gap: float  # 0-1

    deadline: Optional[datetime]
    estimated_cost: Optional[float]

    related_events: List[str]

@dataclass
class JurisdictionalRisk:
    """Risk assessment for specific jurisdiction"""
    jurisdiction: Jurisdiction
    overall_risk_score: float
    trend_direction: str  # increasing, decreasing, stable

    # Specific risk factors
    enforcement_intensity: float
    policy_clarity: float
    regulatory_stability: float

    # Recent activity
    recent_events: List[str]
    active_investigations: int
    pending_legislation: int

    # Recommendations
    recommended_actions: List[str]
    monitoring_priority: str  # high, medium, low

@dataclass
class RegulatoryRiskReport:
    """Comprehensive regulatory risk assessment"""
    timestamp: datetime
    overall_risk_score: float
    trend_analysis: Dict[str, float]

    # Events and requirements
    recent_events: List[RegulatoryEvent]
    compliance_requirements: List[ComplianceRequirement]
    jurisdictional_risks: List[JurisdictionalRisk]

    # Risk assessment
    high_priority_risks: List[str]
    immediate_actions: List[str]
    monitoring_recommendations: List[str]

    # Predictive analysis
    risk_projections: Dict[str, float]
    early_warning_indicators: List[str]

    next_update: datetime

class RegulatoryMonitor:
    """Monitors regulatory developments and compliance risks"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the regulatory monitor"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.event_history = []
        self.compliance_database = {}
        self.risk_weights = self._load_risk_weights()
        self.keyword_patterns = self._load_monitoring_patterns()

    def _load_risk_weights(self) -> Dict[str, float]:
        """Load regulatory risk weights from config"""
        return {
            'enforcement_action_weight': self.config.get('regulatory_compliance', {})
                .get('pressure_indicators', {}).get('enforcement_action_weight', 10),
            'policy_proposal_weight': self.config.get('regulatory_compliance', {})
                .get('pressure_indicators', {}).get('policy_proposal_weight', 5),
            'jurisdiction_ban_weight': self.config.get('regulatory_compliance', {})
                .get('pressure_indicators', {}).get('jurisdiction_ban_weight', 15),
            'investigation_weight': self.config.get('regulatory_compliance', {})
                .get('pressure_indicators', {}).get('investigation_weight', 7),
            'guidance_update_weight': self.config.get('regulatory_compliance', {})
                .get('pressure_indicators', {}).get('guidance_update_weight', 3)
        }

    def _load_monitoring_patterns(self) -> Dict[str, List[str]]:
        """Load keyword patterns for regulatory monitoring"""
        return {
            'algorand_specific': [
                'algorand', 'algo', 'proof of stake', 'pos', 'state proof',
                'algorand foundation', 'algorand governance'
            ],
            'defi_related': [
                'defi', 'decentralized finance', 'lending protocol', 'dex',
                'automated market maker', 'yield farming', 'liquidity mining'
            ],
            'governance_related': [
                'dao', 'governance token', 'voting mechanism', 'proposal system',
                'decentralized governance', 'governance attack'
            ],
            'high_risk_terms': [
                'ban', 'prohibition', 'enforcement', 'investigation', 'lawsuit',
                'criminal charges', 'sanctions', 'suspension'
            ],
            'compliance_terms': [
                'kyc', 'aml', 'reporting requirement', 'licensing', 'registration',
                'compliance framework', 'regulatory approval'
            ]
        }

    async def monitor_regulatory_landscape(self,
                                         regulatory_data: Dict[str, Any]) -> RegulatoryRiskReport:
        """
        Monitor regulatory landscape and assess compliance risks

        Args:
            regulatory_data: Current regulatory information and events

        Returns:
            RegulatoryRiskReport: Comprehensive regulatory risk assessment
        """
        try:
            self.logger.info("Starting regulatory landscape monitoring")

            # Process regulatory events
            recent_events = await self._process_regulatory_events(regulatory_data)

            # Assess compliance requirements
            compliance_requirements = await self._assess_compliance_requirements(regulatory_data)

            # Analyze jurisdictional risks
            jurisdictional_risks = await self._analyze_jurisdictional_risks(regulatory_data, recent_events)

            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_regulatory_risk(
                recent_events, compliance_requirements, jurisdictional_risks
            )

            # Perform trend analysis
            trend_analysis = await self._perform_regulatory_trend_analysis(recent_events)

            # Identify high-priority risks
            high_priority_risks = self._identify_high_priority_risks(
                recent_events, compliance_requirements, jurisdictional_risks
            )

            # Generate recommendations
            immediate_actions = self._generate_immediate_actions(high_priority_risks, recent_events)
            monitoring_recommendations = self._generate_monitoring_recommendations(jurisdictional_risks)

            # Predictive analysis
            risk_projections = await self._generate_risk_projections(trend_analysis, recent_events)
            early_warning_indicators = self._identify_early_warning_indicators(recent_events, trend_analysis)

            report = RegulatoryRiskReport(
                timestamp=datetime.utcnow(),
                overall_risk_score=overall_risk_score,
                trend_analysis=trend_analysis,
                recent_events=recent_events,
                compliance_requirements=compliance_requirements,
                jurisdictional_risks=jurisdictional_risks,
                high_priority_risks=high_priority_risks,
                immediate_actions=immediate_actions,
                monitoring_recommendations=monitoring_recommendations,
                risk_projections=risk_projections,
                early_warning_indicators=early_warning_indicators,
                next_update=datetime.utcnow() + timedelta(hours=6)
            )

            # Store historical data
            self._store_regulatory_data(report)

            self.logger.info(f"Regulatory monitoring completed. Overall risk: {overall_risk_score:.2f}")
            return report

        except Exception as e:
            self.logger.error(f"Regulatory monitoring failed: {e}")
            raise

    async def _process_regulatory_events(self, regulatory_data: Dict[str, Any]) -> List[RegulatoryEvent]:
        """Process and analyze regulatory events"""
        events = []

        try:
            raw_events = regulatory_data.get('events', [])

            for event_data in raw_events:
                # Parse event type and jurisdiction
                event_type = RegulatoryEventType(event_data.get('type', 'guidance_update'))
                jurisdiction = Jurisdiction(event_data.get('jurisdiction', 'GLOBAL'))

                # Assess impact and relevance
                impact_assessment = await self._assess_event_impact(event_data)

                # Parse dates
                event_date = self._parse_datetime(event_data.get('date'))
                effective_date = self._parse_datetime(event_data.get('effective_date'))
                deadline = self._parse_datetime(event_data.get('deadline'))

                # Analyze content relevance
                content_analysis = self._analyze_event_content(event_data.get('description', ''))

                event = RegulatoryEvent(
                    event_id=event_data.get('id', ''),
                    event_type=event_type,
                    jurisdiction=jurisdiction,
                    title=event_data.get('title', ''),
                    description=event_data.get('description', ''),
                    severity=RiskSeverity(event_data.get('severity', 'low')),
                    impact_score=impact_assessment['impact_score'],
                    urgency=impact_assessment['urgency'],
                    event_date=event_date or datetime.utcnow(),
                    effective_date=effective_date,
                    deadline=deadline,
                    affects_algorand=content_analysis['affects_algorand'],
                    affects_defi=content_analysis['affects_defi'],
                    affects_governance=content_analysis['affects_governance'],
                    keywords=content_analysis['keywords'],
                    confidence_level=event_data.get('confidence', 0.7),
                    sources=event_data.get('sources', []),
                    reliability_score=event_data.get('reliability', 0.8)
                )

                events.append(event)

            return events

        except Exception as e:
            self.logger.error(f"Failed to process regulatory events: {e}")
            return []

    async def _assess_event_impact(self, event_data: Dict[str, Any]) -> Dict[str, float]:
        """Assess the impact and urgency of a regulatory event"""
        try:
            event_type = event_data.get('type', 'guidance_update')
            jurisdiction = event_data.get('jurisdiction', 'GLOBAL')

            # Base impact scores by event type
            base_impacts = {
                'enforcement_action': 8.0,
                'jurisdiction_ban': 9.0,
                'investigation': 7.0,
                'policy_proposal': 5.0,
                'guidance_update': 3.0,
                'legislation': 6.0,
                'court_ruling': 7.0,
                'international_standard': 4.0
            }

            impact_score = base_impacts.get(event_type, 5.0)

            # Adjust for jurisdiction importance
            jurisdiction_multipliers = {
                'US': 1.3,
                'EU': 1.2,
                'UK': 1.1,
                'CN': 1.0,
                'JP': 1.0,
                'SG': 0.9,
                'GLOBAL': 1.4
            }

            impact_score *= jurisdiction_multipliers.get(jurisdiction, 1.0)

            # Calculate urgency based on deadlines and severity
            urgency = 5.0  # Default
            if event_data.get('deadline'):
                deadline = self._parse_datetime(event_data['deadline'])
                if deadline:
                    days_until_deadline = (deadline - datetime.utcnow()).days
                    if days_until_deadline < 30:
                        urgency = 9.0
                    elif days_until_deadline < 90:
                        urgency = 7.0
                    elif days_until_deadline < 180:
                        urgency = 5.0

            return {
                'impact_score': min(10.0, impact_score),
                'urgency': urgency
            }

        except Exception as e:
            self.logger.error(f"Event impact assessment failed: {e}")
            return {'impact_score': 5.0, 'urgency': 5.0}

    def _analyze_event_content(self, description: str) -> Dict[str, Any]:
        """Analyze event content for relevance to Algorand ecosystem"""
        try:
            if not description:
                return {
                    'affects_algorand': False,
                    'affects_defi': False,
                    'affects_governance': False,
                    'keywords': []
                }

            description_lower = description.lower()
            found_keywords = []

            # Check for Algorand-specific terms
            algorand_keywords = self.keyword_patterns['algorand_specific']
            affects_algorand = any(keyword in description_lower for keyword in algorand_keywords)
            found_keywords.extend([kw for kw in algorand_keywords if kw in description_lower])

            # Check for DeFi-related terms
            defi_keywords = self.keyword_patterns['defi_related']
            affects_defi = any(keyword in description_lower for keyword in defi_keywords)
            found_keywords.extend([kw for kw in defi_keywords if kw in description_lower])

            # Check for governance-related terms
            governance_keywords = self.keyword_patterns['governance_related']
            affects_governance = any(keyword in description_lower for keyword in governance_keywords)
            found_keywords.extend([kw for kw in governance_keywords if kw in description_lower])

            # If no specific matches, check for general crypto/blockchain terms
            if not (affects_algorand or affects_defi or affects_governance):
                general_crypto_terms = [
                    'cryptocurrency', 'blockchain', 'digital asset', 'crypto', 'token',
                    'smart contract', 'consensus', 'decentralized'
                ]
                if any(term in description_lower for term in general_crypto_terms):
                    affects_defi = True  # Assume general crypto regulation affects DeFi

            return {
                'affects_algorand': affects_algorand,
                'affects_defi': affects_defi,
                'affects_governance': affects_governance,
                'keywords': list(set(found_keywords))
            }

        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {
                'affects_algorand': False,
                'affects_defi': False,
                'affects_governance': False,
                'keywords': []
            }

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string safely"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    async def _assess_compliance_requirements(self, regulatory_data: Dict[str, Any]) -> List[ComplianceRequirement]:
        """Assess current compliance requirements"""
        requirements = []

        try:
            compliance_data = regulatory_data.get('compliance_requirements', [])

            for req_data in compliance_data:
                jurisdiction = Jurisdiction(req_data.get('jurisdiction', 'GLOBAL'))

                # Assess applicability to Algorand
                applicability_score = self._calculate_applicability_score(req_data)

                # Assess implementation complexity
                complexity_score = self._calculate_implementation_complexity(req_data)

                # Determine current compliance status
                current_status = self._assess_compliance_status(req_data)
                compliance_gap = self._calculate_compliance_gap(req_data, current_status)

                requirement = ComplianceRequirement(
                    requirement_id=req_data.get('id', ''),
                    jurisdiction=jurisdiction,
                    category=req_data.get('category', 'general'),
                    description=req_data.get('description', ''),
                    applicability_score=applicability_score,
                    implementation_complexity=complexity_score,
                    current_status=current_status,
                    compliance_gap=compliance_gap,
                    deadline=self._parse_datetime(req_data.get('deadline')),
                    estimated_cost=req_data.get('estimated_cost'),
                    related_events=req_data.get('related_events', [])
                )

                requirements.append(requirement)

            return requirements

        except Exception as e:
            self.logger.error(f"Compliance requirements assessment failed: {e}")
            return []

    def _calculate_applicability_score(self, req_data: Dict[str, Any]) -> float:
        """Calculate how much a requirement applies to Algorand"""
        try:
            base_score = 0.5  # Default applicability

            # Check for specific applicability indicators
            description = req_data.get('description', '').lower()
            category = req_data.get('category', '').lower()

            # High applicability for certain categories
            if category in ['defi', 'governance', 'blockchain', 'consensus']:
                base_score = 0.9
            elif category in ['kyc', 'aml', 'reporting']:
                base_score = 0.7

            # Adjust based on description content
            if any(term in description for term in self.keyword_patterns['algorand_specific']):
                base_score = 1.0
            elif any(term in description for term in self.keyword_patterns['defi_related']):
                base_score = max(base_score, 0.8)

            return min(1.0, base_score)

        except Exception as e:
            self.logger.error(f"Applicability score calculation failed: {e}")
            return 0.5

    def _calculate_implementation_complexity(self, req_data: Dict[str, Any]) -> float:
        """Calculate implementation complexity score"""
        try:
            category = req_data.get('category', '').lower()
            scope = req_data.get('scope', 'limited')

            # Base complexity by category
            category_complexity = {
                'kyc': 6.0,
                'aml': 7.0,
                'reporting': 5.0,
                'licensing': 8.0,
                'governance': 4.0,
                'technical': 6.0
            }

            complexity = category_complexity.get(category, 5.0)

            # Adjust for scope
            scope_multipliers = {
                'limited': 0.8,
                'moderate': 1.0,
                'extensive': 1.3,
                'comprehensive': 1.5
            }

            complexity *= scope_multipliers.get(scope, 1.0)

            return min(10.0, complexity)

        except Exception as e:
            self.logger.error(f"Implementation complexity calculation failed: {e}")
            return 5.0

    def _assess_compliance_status(self, req_data: Dict[str, Any]) -> str:
        """Assess current compliance status"""
        # This would integrate with actual compliance systems
        # For now, return simulated status

        category = req_data.get('category', '').lower()

        # Simulate compliance status based on category
        if category in ['governance', 'technical']:
            return 'compliant'
        elif category in ['reporting']:
            return 'partial'
        elif category in ['licensing', 'aml']:
            return 'non_compliant'
        else:
            return 'unknown'

    def _calculate_compliance_gap(self, req_data: Dict[str, Any], current_status: str) -> float:
        """Calculate compliance gap score"""
        status_gaps = {
            'compliant': 0.0,
            'partial': 0.5,
            'non_compliant': 1.0,
            'unknown': 0.7
        }

        return status_gaps.get(current_status, 0.7)

    async def _analyze_jurisdictional_risks(self,
                                          regulatory_data: Dict[str, Any],
                                          recent_events: List[RegulatoryEvent]) -> List[JurisdictionalRisk]:
        """Analyze risks by jurisdiction"""
        jurisdictional_risks = []

        try:
            # Group events by jurisdiction
            events_by_jurisdiction = {}
            for event in recent_events:
                if event.jurisdiction not in events_by_jurisdiction:
                    events_by_jurisdiction[event.jurisdiction] = []
                events_by_jurisdiction[event.jurisdiction].append(event)

            # Analyze each jurisdiction
            for jurisdiction in Jurisdiction:
                jurisdiction_events = events_by_jurisdiction.get(jurisdiction, [])

                # Calculate risk metrics
                risk_metrics = self._calculate_jurisdictional_risk_metrics(
                    jurisdiction, jurisdiction_events, regulatory_data
                )

                # Determine trend direction
                trend_direction = self._analyze_jurisdictional_trend(jurisdiction, jurisdiction_events)

                # Generate recommendations
                recommendations = self._generate_jurisdictional_recommendations(
                    jurisdiction, risk_metrics, jurisdiction_events
                )

                jurisdictional_risk = JurisdictionalRisk(
                    jurisdiction=jurisdiction,
                    overall_risk_score=risk_metrics['overall_risk'],
                    trend_direction=trend_direction,
                    enforcement_intensity=risk_metrics['enforcement_intensity'],
                    policy_clarity=risk_metrics['policy_clarity'],
                    regulatory_stability=risk_metrics['regulatory_stability'],
                    recent_events=[event.event_id for event in jurisdiction_events],
                    active_investigations=len([e for e in jurisdiction_events
                                             if e.event_type == RegulatoryEventType.INVESTIGATION]),
                    pending_legislation=len([e for e in jurisdiction_events
                                           if e.event_type == RegulatoryEventType.LEGISLATION]),
                    recommended_actions=recommendations,
                    monitoring_priority=self._determine_monitoring_priority(risk_metrics['overall_risk'])
                )

                jurisdictional_risks.append(jurisdictional_risk)

            return jurisdictional_risks

        except Exception as e:
            self.logger.error(f"Jurisdictional risk analysis failed: {e}")
            return []

    def _calculate_jurisdictional_risk_metrics(self,
                                             jurisdiction: Jurisdiction,
                                             events: List[RegulatoryEvent],
                                             regulatory_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate risk metrics for a jurisdiction"""
        try:
            # Base risk scores by jurisdiction
            base_risks = {
                Jurisdiction.US: 6.0,
                Jurisdiction.EU: 5.0,
                Jurisdiction.UK: 5.5,
                Jurisdiction.CN: 8.0,
                Jurisdiction.JP: 4.0,
                Jurisdiction.SG: 3.5,
                Jurisdiction.GLOBAL: 5.0
            }

            overall_risk = base_risks.get(jurisdiction, 5.0)

            # Adjust based on recent events
            if events:
                high_impact_events = len([e for e in events if e.impact_score > 7.0])
                enforcement_events = len([e for e in events
                                        if e.event_type == RegulatoryEventType.ENFORCEMENT_ACTION])

                overall_risk += high_impact_events * 0.5
                overall_risk += enforcement_events * 1.0

            # Calculate specific metrics
            enforcement_intensity = min(10.0, len([e for e in events
                                                 if e.event_type == RegulatoryEventType.ENFORCEMENT_ACTION]) * 2)

            # Policy clarity (inverse of guidance updates and policy proposals)
            policy_events = len([e for e in events if e.event_type in [
                RegulatoryEventType.POLICY_PROPOSAL, RegulatoryEventType.GUIDANCE_UPDATE
            ]])
            policy_clarity = max(1.0, 8.0 - policy_events)

            # Regulatory stability (inverse of regulatory changes)
            regulatory_changes = len(events)
            regulatory_stability = max(1.0, 9.0 - regulatory_changes * 0.5)

            return {
                'overall_risk': min(10.0, overall_risk),
                'enforcement_intensity': enforcement_intensity,
                'policy_clarity': policy_clarity,
                'regulatory_stability': regulatory_stability
            }

        except Exception as e:
            self.logger.error(f"Jurisdictional risk metrics calculation failed: {e}")
            return {
                'overall_risk': 5.0,
                'enforcement_intensity': 5.0,
                'policy_clarity': 5.0,
                'regulatory_stability': 5.0
            }

    def _analyze_jurisdictional_trend(self,
                                    jurisdiction: Jurisdiction,
                                    events: List[RegulatoryEvent]) -> str:
        """Analyze trend direction for jurisdiction"""
        try:
            if len(events) < 2:
                return "stable"

            # Sort events by date
            sorted_events = sorted(events, key=lambda x: x.event_date)

            # Compare recent vs older events
            mid_point = len(sorted_events) // 2
            recent_events = sorted_events[mid_point:]
            older_events = sorted_events[:mid_point]

            recent_severity = np.mean([e.impact_score for e in recent_events])
            older_severity = np.mean([e.impact_score for e in older_events])

            if recent_severity > older_severity * 1.2:
                return "increasing"
            elif recent_severity < older_severity * 0.8:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            self.logger.error(f"Jurisdictional trend analysis failed: {e}")
            return "stable"

    def _generate_jurisdictional_recommendations(self,
                                               jurisdiction: Jurisdiction,
                                               risk_metrics: Dict[str, float],
                                               events: List[RegulatoryEvent]) -> List[str]:
        """Generate recommendations for specific jurisdiction"""
        recommendations = []

        try:
            overall_risk = risk_metrics['overall_risk']

            if overall_risk > 7.0:
                recommendations.append(f"Consider reducing exposure in {jurisdiction.value}")
                recommendations.append("Engage legal counsel for compliance review")

            if risk_metrics['enforcement_intensity'] > 6.0:
                recommendations.append("Monitor enforcement actions closely")
                recommendations.append("Review compliance posture")

            if risk_metrics['policy_clarity'] < 4.0:
                recommendations.append("Seek regulatory clarity through engagement")
                recommendations.append("Monitor policy developments actively")

            # Event-specific recommendations
            enforcement_events = [e for e in events if e.event_type == RegulatoryEventType.ENFORCEMENT_ACTION]
            if enforcement_events:
                recommendations.append("Review practices against enforcement precedents")

            ban_events = [e for e in events if e.event_type == RegulatoryEventType.JURISDICTION_BAN]
            if ban_events:
                recommendations.append("Prepare contingency plans for service restrictions")

            return recommendations[:5]  # Limit to top 5

        except Exception as e:
            self.logger.error(f"Jurisdictional recommendation generation failed: {e}")
            return ["Monitor regulatory developments"]

    def _determine_monitoring_priority(self, risk_score: float) -> str:
        """Determine monitoring priority based on risk score"""
        if risk_score > 7.0:
            return "high"
        elif risk_score > 4.0:
            return "medium"
        else:
            return "low"

    def _calculate_overall_regulatory_risk(self,
                                         recent_events: List[RegulatoryEvent],
                                         compliance_requirements: List[ComplianceRequirement],
                                         jurisdictional_risks: List[JurisdictionalRisk]) -> float:
        """Calculate overall regulatory risk score"""
        try:
            if not recent_events and not compliance_requirements and not jurisdictional_risks:
                return 0.0

            # Weight recent events
            event_risk = 0.0
            if recent_events:
                high_impact_events = [e for e in recent_events if e.impact_score > 6.0]
                event_risk = min(10.0, len(high_impact_events) * 1.5 +
                               sum(e.impact_score for e in recent_events) / len(recent_events))

            # Weight compliance gaps
            compliance_risk = 0.0
            if compliance_requirements:
                high_gap_requirements = [r for r in compliance_requirements if r.compliance_gap > 0.7]
                compliance_risk = min(10.0, len(high_gap_requirements) * 2.0)

            # Weight jurisdictional risks
            jurisdictional_risk = 0.0
            if jurisdictional_risks:
                high_risk_jurisdictions = [j for j in jurisdictional_risks if j.overall_risk_score > 7.0]
                jurisdictional_risk = min(10.0, len(high_risk_jurisdictions) * 1.5)

            # Combine with weights
            overall_risk = (event_risk * 0.4 + compliance_risk * 0.3 + jurisdictional_risk * 0.3)

            return min(10.0, overall_risk)

        except Exception as e:
            self.logger.error(f"Overall regulatory risk calculation failed: {e}")
            return 5.0

    async def _perform_regulatory_trend_analysis(self, recent_events: List[RegulatoryEvent]) -> Dict[str, float]:
        """Perform trend analysis on regulatory developments"""
        try:
            # Analyze trends by event type
            event_types_count = {}
            for event in recent_events:
                event_types_count[event.event_type.value] = event_types_count.get(event.event_type.value, 0) + 1

            # Analyze severity trends
            if recent_events:
                avg_severity = np.mean([e.impact_score for e in recent_events])
                enforcement_trend = len([e for e in recent_events
                                       if e.event_type == RegulatoryEventType.ENFORCEMENT_ACTION]) / max(len(recent_events), 1)
            else:
                avg_severity = 0.0
                enforcement_trend = 0.0

            return {
                'average_severity_trend': avg_severity,
                'enforcement_intensity_trend': enforcement_trend * 10,
                'regulatory_activity_trend': len(recent_events),
                'policy_development_trend': len([e for e in recent_events
                                               if e.event_type == RegulatoryEventType.POLICY_PROPOSAL])
            }

        except Exception as e:
            self.logger.error(f"Regulatory trend analysis failed: {e}")
            return {}

    def _identify_high_priority_risks(self,
                                     recent_events: List[RegulatoryEvent],
                                     compliance_requirements: List[ComplianceRequirement],
                                     jurisdictional_risks: List[JurisdictionalRisk]) -> List[str]:
        """Identify high-priority regulatory risks"""
        high_priority_risks = []

        try:
            # High-impact recent events
            critical_events = [e for e in recent_events if e.severity == RiskSeverity.CRITICAL]
            for event in critical_events:
                high_priority_risks.append(f"Critical regulatory event: {event.title}")

            # High-gap compliance requirements
            critical_compliance = [r for r in compliance_requirements
                                 if r.compliance_gap > 0.8 and r.applicability_score > 0.7]
            for req in critical_compliance:
                high_priority_risks.append(f"Critical compliance gap: {req.category} in {req.jurisdiction.value}")

            # High-risk jurisdictions
            high_risk_jurisdictions = [j for j in jurisdictional_risks if j.overall_risk_score > 8.0]
            for jurisdiction in high_risk_jurisdictions:
                high_priority_risks.append(f"High regulatory risk in {jurisdiction.jurisdiction.value}")

            return high_priority_risks

        except Exception as e:
            self.logger.error(f"High-priority risk identification failed: {e}")
            return []

    def _generate_immediate_actions(self,
                                  high_priority_risks: List[str],
                                  recent_events: List[RegulatoryEvent]) -> List[str]:
        """Generate immediate action recommendations"""
        actions = []

        try:
            if high_priority_risks:
                actions.append("Address critical regulatory risks immediately")

            # Event-specific actions
            critical_events = [e for e in recent_events if e.severity == RiskSeverity.CRITICAL]
            if critical_events:
                actions.append("Assess impact of critical regulatory events")

            ban_events = [e for e in recent_events if e.event_type == RegulatoryEventType.JURISDICTION_BAN]
            if ban_events:
                actions.append("Implement service restrictions if necessary")

            enforcement_events = [e for e in recent_events if e.event_type == RegulatoryEventType.ENFORCEMENT_ACTION]
            if enforcement_events:
                actions.append("Review compliance posture against enforcement precedents")

            # General actions
            actions.extend([
                "Update regulatory risk assessment",
                "Engage legal and compliance teams",
                "Monitor regulatory developments daily"
            ])

            return actions[:7]  # Limit to top actions

        except Exception as e:
            self.logger.error(f"Immediate action generation failed: {e}")
            return ["Review regulatory risk exposure"]

    def _generate_monitoring_recommendations(self, jurisdictional_risks: List[JurisdictionalRisk]) -> List[str]:
        """Generate monitoring recommendations"""
        recommendations = []

        try:
            high_priority_jurisdictions = [j for j in jurisdictional_risks if j.monitoring_priority == "high"]

            if high_priority_jurisdictions:
                jurisdictions_list = [j.jurisdiction.value for j in high_priority_jurisdictions]
                recommendations.append(f"Intensify monitoring in: {', '.join(jurisdictions_list)}")

            recommendations.extend([
                "Set up automated regulatory news monitoring",
                "Establish regulatory advisory board",
                "Implement compliance dashboard",
                "Schedule regular regulatory risk reviews",
                "Monitor enforcement action databases"
            ])

            return recommendations

        except Exception as e:
            self.logger.error(f"Monitoring recommendation generation failed: {e}")
            return ["Establish regulatory monitoring procedures"]

    async def _generate_risk_projections(self,
                                       trend_analysis: Dict[str, float],
                                       recent_events: List[RegulatoryEvent]) -> Dict[str, float]:
        """Generate risk projections for future periods"""
        try:
            # Simple linear projection based on trends
            current_activity = trend_analysis.get('regulatory_activity_trend', 0)
            current_severity = trend_analysis.get('average_severity_trend', 5.0)

            # Project 30, 90, and 180 days
            projections = {
                '30_day_risk': min(10.0, current_severity + current_activity * 0.1),
                '90_day_risk': min(10.0, current_severity + current_activity * 0.2),
                '180_day_risk': min(10.0, current_severity + current_activity * 0.3)
            }

            return projections

        except Exception as e:
            self.logger.error(f"Risk projection generation failed: {e}")
            return {'30_day_risk': 5.0, '90_day_risk': 5.0, '180_day_risk': 5.0}

    def _identify_early_warning_indicators(self,
                                         recent_events: List[RegulatoryEvent],
                                         trend_analysis: Dict[str, float]) -> List[str]:
        """Identify early warning indicators"""
        indicators = []

        try:
            # Check for increasing enforcement activity
            enforcement_trend = trend_analysis.get('enforcement_intensity_trend', 0)
            if enforcement_trend > 3.0:
                indicators.append("Increasing enforcement activity detected")

            # Check for policy development acceleration
            policy_trend = trend_analysis.get('policy_development_trend', 0)
            if policy_trend > 2:
                indicators.append("Accelerated policy development activity")

            # Check for jurisdiction-specific warning signs
            ban_events = [e for e in recent_events if e.event_type == RegulatoryEventType.JURISDICTION_BAN]
            if ban_events:
                indicators.append("Jurisdiction bans indicate broader regulatory hostility")

            # Check for severity escalation
            avg_severity = trend_analysis.get('average_severity_trend', 5.0)
            if avg_severity > 7.0:
                indicators.append("Average event severity above warning threshold")

            return indicators

        except Exception as e:
            self.logger.error(f"Early warning indicator identification failed: {e}")
            return []

    def _store_regulatory_data(self, report: RegulatoryRiskReport):
        """Store regulatory data for historical analysis"""
        try:
            self.event_history.append({
                'timestamp': report.timestamp,
                'overall_risk_score': report.overall_risk_score,
                'event_count': len(report.recent_events),
                'high_priority_count': len(report.high_priority_risks)
            })

            # Keep only recent data (last 90 days)
            cutoff_time = datetime.utcnow() - timedelta(days=90)
            self.event_history = [
                entry for entry in self.event_history
                if entry['timestamp'] > cutoff_time
            ]

        except Exception as e:
            self.logger.error(f"Failed to store regulatory data: {e}")

# Export main classes
__all__ = ['RegulatoryMonitor', 'RegulatoryRiskReport', 'RegulatoryEvent', 'ComplianceRequirement', 'JurisdictionalRisk', 'RegulatoryEventType', 'RiskSeverity']