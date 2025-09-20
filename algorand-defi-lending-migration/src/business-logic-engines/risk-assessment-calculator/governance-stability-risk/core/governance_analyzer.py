"""
Governance Stability and Attack Vector Analysis Engine
Comprehensive analysis of governance security, attack vectors, and stability risks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
import numpy as np
from pathlib import Path

class RiskLevel(Enum):
    """Risk level enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"

class AttackVector(Enum):
    """Governance attack vector types"""
    FLASH_GOVERNANCE = "flash_governance"
    VOTE_BUYING = "vote_buying"
    WHALE_MANIPULATION = "whale_manipulation"
    QUORUM_GAMING = "quorum_gaming"
    PROPOSAL_SPAM = "proposal_spam"
    DELEGATION_ATTACK = "delegation_attack"
    SYBIL_ATTACK = "sybil_attack"
    GOVERNANCE_TOKEN_ATTACK = "governance_token_attack"

@dataclass
class GovernanceMetrics:
    """Governance stability metrics"""
    total_voting_power: float
    active_voters: int
    proposal_count: int
    average_participation_rate: float
    voting_power_concentration: Dict[str, float]
    delegation_statistics: Dict[str, Any]
    recent_proposals: List[Dict[str, Any]]
    emergency_procedures_active: bool
    upgrade_proposals_pending: int
    governance_token_price_volatility: float

@dataclass
class AttackVectorAssessment:
    """Attack vector risk assessment"""
    vector_type: AttackVector
    risk_level: RiskLevel
    probability_score: float
    impact_score: float
    mitigation_strength: float
    current_indicators: List[str]
    risk_factors: List[str]
    mitigation_recommendations: List[str]
    last_updated: datetime

@dataclass
class GovernanceStabilityReport:
    """Comprehensive governance stability report"""
    timestamp: datetime
    overall_risk_score: float
    overall_risk_level: RiskLevel
    governance_metrics: GovernanceMetrics
    attack_vector_assessments: List[AttackVectorAssessment]
    stability_indicators: Dict[str, float]
    trend_analysis: Dict[str, float]
    recommendations: List[str]
    alert_level: str
    next_assessment_time: datetime

class GovernanceAnalyzer:
    """Main governance stability and attack vector analysis engine"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the governance analyzer"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.governance_metrics_cache = {}
        self.historical_data = []
        self.attack_vector_cache = {}

        # Initialize sub-analyzers
        self.voting_analyzer = None  # Will be set by systemic engine
        self.proposal_analyzer = None  # Will be set by systemic engine
        self.emergency_analyzer = None  # Will be set by systemic engine

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'governance_risk': {
                'voting_concentration': {
                    'critical_whale_threshold': 0.20,
                    'high_risk_threshold': 0.15,
                    'moderate_risk_threshold': 0.10
                },
                'proposal_risks': {
                    'flash_governance_window': 7200,
                    'minimum_deliberation_time': 172800,
                    'quorum_manipulation_threshold': 0.05
                }
            },
            'monitoring': {
                'intervals': {
                    'governance_check_seconds': 300
                },
                'alerts': {
                    'critical_risk_score': 8.0,
                    'high_risk_score': 6.0,
                    'moderate_risk_score': 4.0
                }
            }
        }

    async def analyze_governance_stability(self,
                                         governance_data: Optional[Dict[str, Any]] = None) -> GovernanceStabilityReport:
        """
        Perform comprehensive governance stability analysis

        Args:
            governance_data: Optional pre-fetched governance data

        Returns:
            GovernanceStabilityReport: Comprehensive stability assessment
        """
        try:
            self.logger.info("Starting governance stability analysis")

            # Fetch or use provided governance data
            if governance_data is None:
                governance_data = await self._fetch_governance_data()

            # Extract governance metrics
            governance_metrics = await self._extract_governance_metrics(governance_data)

            # Assess attack vectors
            attack_assessments = await self._assess_attack_vectors(governance_data, governance_metrics)

            # Calculate stability indicators
            stability_indicators = await self._calculate_stability_indicators(governance_metrics, attack_assessments)

            # Perform trend analysis
            trend_analysis = await self._perform_trend_analysis(governance_metrics)

            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(stability_indicators, attack_assessments)
            overall_risk_level = self._determine_risk_level(overall_risk_score)

            # Generate recommendations
            recommendations = self._generate_recommendations(attack_assessments, stability_indicators)

            # Determine alert level
            alert_level = self._determine_alert_level(overall_risk_score, attack_assessments)

            # Create comprehensive report
            report = GovernanceStabilityReport(
                timestamp=datetime.utcnow(),
                overall_risk_score=overall_risk_score,
                overall_risk_level=overall_risk_level,
                governance_metrics=governance_metrics,
                attack_vector_assessments=attack_assessments,
                stability_indicators=stability_indicators,
                trend_analysis=trend_analysis,
                recommendations=recommendations,
                alert_level=alert_level,
                next_assessment_time=datetime.utcnow() + timedelta(
                    seconds=self.config.get('monitoring', {}).get('intervals', {}).get('governance_check_seconds', 300)
                )
            )

            # Cache results
            self._cache_results(report)

            self.logger.info(f"Governance stability analysis completed. Risk level: {overall_risk_level.value}")
            return report

        except Exception as e:
            self.logger.error(f"Governance stability analysis failed: {e}")
            raise

    async def _fetch_governance_data(self) -> Dict[str, Any]:
        """Fetch current governance data from various sources"""
        try:
            # Simulate fetching data from Algorand governance APIs
            # In production, this would integrate with actual APIs

            governance_data = {
                'total_voting_power': 5_000_000_000,  # Total Algo staked
                'active_voters': 145_000,
                'current_proposals': [],
                'voting_power_distribution': {},
                'delegation_data': {},
                'recent_governance_events': [],
                'emergency_procedures': {
                    'active': False,
                    'procedures_available': True,
                    'response_time_capability': 2.5  # hours
                },
                'upgrade_status': {
                    'pending_upgrades': 0,
                    'testing_phase_upgrades': 1,
                    'community_discussion_upgrades': 2
                },
                'governance_token_metrics': {
                    'price_24h_change': -0.03,
                    'volume_24h': 150_000_000,
                    'market_cap': 3_200_000_000
                }
            }

            # Add simulated voting power concentration data
            governance_data['voting_power_distribution'] = {
                'top_1_percentage': 0.12,
                'top_5_percentage': 0.35,
                'top_10_percentage': 0.52,
                'top_50_percentage': 0.78,
                'gini_coefficient': 0.71
            }

            # Add simulated delegation data
            governance_data['delegation_data'] = {
                'total_delegated_power': 0.45,  # 45% of voting power delegated
                'top_delegate_percentage': 0.08,
                'delegates_count': 1_250,
                'average_delegation_size': 1_800  # Algo
            }

            return governance_data

        except Exception as e:
            self.logger.error(f"Failed to fetch governance data: {e}")
            raise

    async def _extract_governance_metrics(self, governance_data: Dict[str, Any]) -> GovernanceMetrics:
        """Extract and structure governance metrics"""
        try:
            return GovernanceMetrics(
                total_voting_power=governance_data.get('total_voting_power', 0),
                active_voters=governance_data.get('active_voters', 0),
                proposal_count=len(governance_data.get('current_proposals', [])),
                average_participation_rate=governance_data.get('average_participation_rate', 0.65),
                voting_power_concentration=governance_data.get('voting_power_distribution', {}),
                delegation_statistics=governance_data.get('delegation_data', {}),
                recent_proposals=governance_data.get('current_proposals', []),
                emergency_procedures_active=governance_data.get('emergency_procedures', {}).get('active', False),
                upgrade_proposals_pending=governance_data.get('upgrade_status', {}).get('pending_upgrades', 0),
                governance_token_price_volatility=abs(governance_data.get('governance_token_metrics', {}).get('price_24h_change', 0))
            )

        except Exception as e:
            self.logger.error(f"Failed to extract governance metrics: {e}")
            raise

    async def _assess_attack_vectors(self,
                                   governance_data: Dict[str, Any],
                                   metrics: GovernanceMetrics) -> List[AttackVectorAssessment]:
        """Assess all governance attack vectors"""
        assessments = []

        # Flash Governance Attack Assessment
        flash_assessment = await self._assess_flash_governance_risk(governance_data, metrics)
        assessments.append(flash_assessment)

        # Vote Buying Assessment
        vote_buying_assessment = await self._assess_vote_buying_risk(governance_data, metrics)
        assessments.append(vote_buying_assessment)

        # Whale Manipulation Assessment
        whale_assessment = await self._assess_whale_manipulation_risk(governance_data, metrics)
        assessments.append(whale_assessment)

        # Quorum Gaming Assessment
        quorum_assessment = await self._assess_quorum_gaming_risk(governance_data, metrics)
        assessments.append(quorum_assessment)

        # Proposal Spam Assessment
        spam_assessment = await self._assess_proposal_spam_risk(governance_data, metrics)
        assessments.append(spam_assessment)

        # Delegation Attack Assessment
        delegation_assessment = await self._assess_delegation_attack_risk(governance_data, metrics)
        assessments.append(delegation_assessment)

        # Sybil Attack Assessment
        sybil_assessment = await self._assess_sybil_attack_risk(governance_data, metrics)
        assessments.append(sybil_assessment)

        # Governance Token Attack Assessment
        token_assessment = await self._assess_governance_token_attack_risk(governance_data, metrics)
        assessments.append(token_assessment)

        return assessments

    async def _assess_flash_governance_risk(self,
                                          governance_data: Dict[str, Any],
                                          metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess flash governance attack risk"""
        try:
            current_indicators = []
            risk_factors = []

            # Check for rapid proposal submission
            recent_proposals = governance_data.get('current_proposals', [])
            rapid_proposals = sum(1 for p in recent_proposals
                                if self._is_recent_proposal(p, hours=2))

            if rapid_proposals > 1:
                current_indicators.append(f"Multiple proposals ({rapid_proposals}) submitted in last 2 hours")
                risk_factors.append("Rapid proposal submission detected")

            # Check minimum deliberation time
            min_deliberation = self.config['governance_risk']['proposal_risks']['minimum_deliberation_time']
            for proposal in recent_proposals:
                if proposal.get('deliberation_time', min_deliberation) < min_deliberation:
                    current_indicators.append("Proposal with insufficient deliberation time")
                    risk_factors.append("Insufficient deliberation period")

            # Calculate probability and impact scores
            probability_score = min(8.0, rapid_proposals * 2.0 + len(risk_factors))
            impact_score = 9.0 if rapid_proposals > 2 else 6.0

            # Assess mitigation strength
            mitigation_strength = 7.0  # Algorand has built-in governance delays
            if governance_data.get('emergency_procedures', {}).get('active', False):
                mitigation_strength = 4.0  # Emergency mode reduces protections

            risk_level = self._determine_risk_level((probability_score + impact_score) / 2)

            return AttackVectorAssessment(
                vector_type=AttackVector.FLASH_GOVERNANCE,
                risk_level=risk_level,
                probability_score=probability_score,
                impact_score=impact_score,
                mitigation_strength=mitigation_strength,
                current_indicators=current_indicators,
                risk_factors=risk_factors,
                mitigation_recommendations=[
                    "Enforce minimum deliberation periods",
                    "Implement proposal rate limiting",
                    "Require supermajority for rapid proposals",
                    "Deploy timelock mechanisms"
                ],
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Flash governance risk assessment failed: {e}")
            raise

    async def _assess_vote_buying_risk(self,
                                     governance_data: Dict[str, Any],
                                     metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess vote buying attack risk"""
        try:
            current_indicators = []
            risk_factors = []

            # Check delegation concentration
            delegation_stats = metrics.delegation_statistics
            top_delegate_pct = delegation_stats.get('top_delegate_percentage', 0)

            if top_delegate_pct > 0.15:
                current_indicators.append(f"High delegation concentration: {top_delegate_pct:.1%}")
                risk_factors.append("Concentrated delegation power")

            # Check for unusual delegation patterns
            total_delegated = delegation_stats.get('total_delegated_power', 0)
            if total_delegated > 0.60:
                current_indicators.append(f"High delegation rate: {total_delegated:.1%}")
                risk_factors.append("High percentage of delegated voting power")

            # Check governance token volatility (can indicate manipulation)
            price_volatility = metrics.governance_token_price_volatility
            if price_volatility > 0.10:
                current_indicators.append(f"High token price volatility: {price_volatility:.1%}")
                risk_factors.append("Governance token price manipulation potential")

            # Calculate scores
            probability_score = min(8.0, (top_delegate_pct * 20) + (total_delegated * 5) + (price_volatility * 10))
            impact_score = 8.0 if top_delegate_pct > 0.20 else 6.0
            mitigation_strength = 6.0  # Moderate protections in place

            risk_level = self._determine_risk_level((probability_score + impact_score) / 2)

            return AttackVectorAssessment(
                vector_type=AttackVector.VOTE_BUYING,
                risk_level=risk_level,
                probability_score=probability_score,
                impact_score=impact_score,
                mitigation_strength=mitigation_strength,
                current_indicators=current_indicators,
                risk_factors=risk_factors,
                mitigation_recommendations=[
                    "Implement delegation caps",
                    "Monitor unusual delegation patterns",
                    "Require delegation transparency",
                    "Implement vote verification mechanisms"
                ],
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Vote buying risk assessment failed: {e}")
            raise

    async def _assess_whale_manipulation_risk(self,
                                            governance_data: Dict[str, Any],
                                            metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess whale manipulation risk"""
        try:
            current_indicators = []
            risk_factors = []

            concentration = metrics.voting_power_concentration
            top_1_pct = concentration.get('top_1_percentage', 0)
            top_10_pct = concentration.get('top_10_percentage', 0)
            gini_coeff = concentration.get('gini_coefficient', 0)

            # Check critical thresholds
            critical_threshold = self.config['governance_risk']['voting_concentration']['critical_whale_threshold']
            high_threshold = self.config['governance_risk']['voting_concentration']['high_risk_threshold']

            if top_1_pct > critical_threshold:
                current_indicators.append(f"Critical whale concentration: {top_1_pct:.1%}")
                risk_factors.append("Single entity controls critical voting power")
            elif top_1_pct > high_threshold:
                current_indicators.append(f"High whale concentration: {top_1_pct:.1%}")
                risk_factors.append("Single entity controls significant voting power")

            if top_10_pct > 0.60:
                current_indicators.append(f"Top 10 holders control {top_10_pct:.1%}")
                risk_factors.append("High concentration among top holders")

            if gini_coeff > 0.80:
                current_indicators.append(f"High inequality (Gini: {gini_coeff:.2f})")
                risk_factors.append("Highly unequal voting power distribution")

            # Calculate scores
            probability_score = min(10.0, (top_1_pct * 30) + (gini_coeff * 5))
            impact_score = 9.0 if top_1_pct > critical_threshold else 7.0
            mitigation_strength = 5.0  # Limited built-in protections

            risk_level = self._determine_risk_level((probability_score + impact_score) / 2)

            return AttackVectorAssessment(
                vector_type=AttackVector.WHALE_MANIPULATION,
                risk_level=risk_level,
                probability_score=probability_score,
                impact_score=impact_score,
                mitigation_strength=mitigation_strength,
                current_indicators=current_indicators,
                risk_factors=risk_factors,
                mitigation_recommendations=[
                    "Implement voting power caps",
                    "Encourage broader token distribution",
                    "Implement quadratic voting mechanisms",
                    "Monitor large token movements"
                ],
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Whale manipulation risk assessment failed: {e}")
            raise

    async def _assess_quorum_gaming_risk(self,
                                       governance_data: Dict[str, Any],
                                       metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess quorum gaming attack risk"""
        try:
            current_indicators = []
            risk_factors = []

            participation_rate = metrics.average_participation_rate
            active_voters = metrics.active_voters

            # Check low participation (easier to game quorum)
            if participation_rate < 0.30:
                current_indicators.append(f"Very low participation: {participation_rate:.1%}")
                risk_factors.append("Low participation enables quorum gaming")
            elif participation_rate < 0.50:
                current_indicators.append(f"Low participation: {participation_rate:.1%}")
                risk_factors.append("Moderate participation gaming risk")

            # Check absolute voter count
            if active_voters < 50_000:
                current_indicators.append(f"Low absolute voter count: {active_voters:,}")
                risk_factors.append("Small voter base vulnerable to coordination")

            # Check for recent participation swings
            # In production, this would analyze historical data
            participation_volatility = 0.05  # Simulated
            if participation_volatility > 0.10:
                current_indicators.append(f"High participation volatility: {participation_volatility:.1%}")
                risk_factors.append("Unstable participation patterns")

            # Calculate scores
            probability_score = min(8.0, (1 - participation_rate) * 10 + participation_volatility * 20)
            impact_score = 7.0 if participation_rate < 0.30 else 5.0
            mitigation_strength = 6.0  # Moderate quorum protections

            risk_level = self._determine_risk_level((probability_score + impact_score) / 2)

            return AttackVectorAssessment(
                vector_type=AttackVector.QUORUM_GAMING,
                risk_level=risk_level,
                probability_score=probability_score,
                impact_score=impact_score,
                mitigation_strength=mitigation_strength,
                current_indicators=current_indicators,
                risk_factors=risk_factors,
                mitigation_recommendations=[
                    "Implement dynamic quorum requirements",
                    "Encourage broader participation",
                    "Monitor participation patterns",
                    "Implement anti-gaming mechanisms"
                ],
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Quorum gaming risk assessment failed: {e}")
            raise

    async def _assess_proposal_spam_risk(self,
                                       governance_data: Dict[str, Any],
                                       metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess proposal spam attack risk"""
        # Implementation similar to other attack vector assessments
        # Focus on proposal frequency, quality, and resource consumption
        return AttackVectorAssessment(
            vector_type=AttackVector.PROPOSAL_SPAM,
            risk_level=RiskLevel.LOW,
            probability_score=2.0,
            impact_score=4.0,
            mitigation_strength=8.0,
            current_indicators=[],
            risk_factors=[],
            mitigation_recommendations=[
                "Implement proposal fees",
                "Rate limit proposal submissions",
                "Require proposal quality standards"
            ],
            last_updated=datetime.utcnow()
        )

    async def _assess_delegation_attack_risk(self,
                                           governance_data: Dict[str, Any],
                                           metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess delegation attack risk"""
        # Implementation for delegation-specific attacks
        return AttackVectorAssessment(
            vector_type=AttackVector.DELEGATION_ATTACK,
            risk_level=RiskLevel.MODERATE,
            probability_score=4.0,
            impact_score=6.0,
            mitigation_strength=6.0,
            current_indicators=[],
            risk_factors=[],
            mitigation_recommendations=[
                "Monitor delegation patterns",
                "Implement delegation limits",
                "Require delegation transparency"
            ],
            last_updated=datetime.utcnow()
        )

    async def _assess_sybil_attack_risk(self,
                                      governance_data: Dict[str, Any],
                                      metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess Sybil attack risk"""
        # Implementation for Sybil attack assessment
        return AttackVectorAssessment(
            vector_type=AttackVector.SYBIL_ATTACK,
            risk_level=RiskLevel.LOW,
            probability_score=3.0,
            impact_score=5.0,
            mitigation_strength=7.0,
            current_indicators=[],
            risk_factors=[],
            mitigation_recommendations=[
                "Implement identity verification",
                "Monitor address clustering",
                "Analyze voting patterns"
            ],
            last_updated=datetime.utcnow()
        )

    async def _assess_governance_token_attack_risk(self,
                                                 governance_data: Dict[str, Any],
                                                 metrics: GovernanceMetrics) -> AttackVectorAssessment:
        """Assess governance token-specific attack risks"""
        # Implementation for governance token attacks
        return AttackVectorAssessment(
            vector_type=AttackVector.GOVERNANCE_TOKEN_ATTACK,
            risk_level=RiskLevel.MODERATE,
            probability_score=5.0,
            impact_score=7.0,
            mitigation_strength=5.0,
            current_indicators=[],
            risk_factors=[],
            mitigation_recommendations=[
                "Monitor token market manipulation",
                "Implement flash loan protections",
                "Diversify governance token sources"
            ],
            last_updated=datetime.utcnow()
        )

    async def _calculate_stability_indicators(self,
                                            metrics: GovernanceMetrics,
                                            assessments: List[AttackVectorAssessment]) -> Dict[str, float]:
        """Calculate governance stability indicators"""
        try:
            indicators = {}

            # Participation stability
            indicators['participation_stability'] = min(10.0, metrics.average_participation_rate * 10)

            # Concentration risk
            concentration = metrics.voting_power_concentration
            top_1_pct = concentration.get('top_1_percentage', 0)
            indicators['concentration_risk'] = min(10.0, top_1_pct * 50)

            # Delegation health
            delegation_stats = metrics.delegation_statistics
            total_delegated = delegation_stats.get('total_delegated_power', 0)
            indicators['delegation_health'] = max(0, 10 - (total_delegated * 15))

            # Proposal activity health
            proposal_count = metrics.proposal_count
            indicators['proposal_activity'] = min(10.0, max(0, 5 - abs(proposal_count - 2)))

            # Emergency readiness
            indicators['emergency_readiness'] = 8.0 if not metrics.emergency_procedures_active else 3.0

            # Attack vector resistance
            avg_mitigation = np.mean([assessment.mitigation_strength for assessment in assessments])
            indicators['attack_resistance'] = avg_mitigation

            # Overall governance health
            indicators['governance_health'] = np.mean([
                indicators['participation_stability'],
                10 - indicators['concentration_risk'],
                indicators['delegation_health'],
                indicators['proposal_activity'],
                indicators['emergency_readiness'],
                indicators['attack_resistance']
            ])

            return indicators

        except Exception as e:
            self.logger.error(f"Failed to calculate stability indicators: {e}")
            raise

    async def _perform_trend_analysis(self, metrics: GovernanceMetrics) -> Dict[str, float]:
        """Perform trend analysis on governance metrics"""
        try:
            # In production, this would analyze historical data
            # For now, return simulated trend analysis

            trends = {
                'participation_trend': 0.02,  # 2% increase trend
                'concentration_trend': -0.01,  # 1% decrease in concentration
                'delegation_trend': 0.03,  # 3% increase in delegation
                'proposal_activity_trend': 0.00,  # Stable proposal activity
                'voter_growth_trend': 0.05,  # 5% voter growth
                'engagement_trend': 0.01  # 1% increase in engagement
            }

            return trends

        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return {}

    def _calculate_overall_risk_score(self,
                                    stability_indicators: Dict[str, float],
                                    assessments: List[AttackVectorAssessment]) -> float:
        """Calculate overall governance risk score"""
        try:
            # Weight different components
            weights = self.config.get('monitoring', {}).get('weights', {})
            governance_weight = weights.get('governance_weight', 0.25)

            # Attack vector risk (higher scores = higher risk)
            attack_risks = [assessment.probability_score * assessment.impact_score / 10
                          for assessment in assessments]
            avg_attack_risk = np.mean(attack_risks) if attack_risks else 0

            # Stability indicators (lower scores = higher risk for some indicators)
            concentration_risk = stability_indicators.get('concentration_risk', 0)
            participation_stability = stability_indicators.get('participation_stability', 10)
            delegation_health = stability_indicators.get('delegation_health', 10)

            # Calculate composite risk score (0-10 scale, higher = more risk)
            risk_score = (
                avg_attack_risk * 0.40 +
                concentration_risk * 0.25 +
                (10 - participation_stability) * 0.20 +
                (10 - delegation_health) * 0.15
            ) * governance_weight * 4  # Scale to 0-10

            return min(10.0, max(0.0, risk_score))

        except Exception as e:
            self.logger.error(f"Risk score calculation failed: {e}")
            return 5.0  # Default moderate risk

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from numeric score"""
        if risk_score >= 8.0:
            return RiskLevel.CRITICAL
        elif risk_score >= 6.0:
            return RiskLevel.HIGH
        elif risk_score >= 4.0:
            return RiskLevel.MODERATE
        elif risk_score >= 2.0:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    def _generate_recommendations(self,
                                assessments: List[AttackVectorAssessment],
                                stability_indicators: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # High-risk attack vectors
        high_risk_vectors = [a for a in assessments if a.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        for assessment in high_risk_vectors:
            recommendations.extend(assessment.mitigation_recommendations[:2])  # Top 2 recommendations

        # Stability-based recommendations
        concentration_risk = stability_indicators.get('concentration_risk', 0)
        if concentration_risk > 6.0:
            recommendations.append("Implement measures to improve voting power distribution")

        participation_stability = stability_indicators.get('participation_stability', 10)
        if participation_stability < 5.0:
            recommendations.append("Launch initiatives to increase governance participation")

        delegation_health = stability_indicators.get('delegation_health', 10)
        if delegation_health < 6.0:
            recommendations.append("Review and optimize delegation mechanisms")

        # Remove duplicates and limit to top recommendations
        recommendations = list(dict.fromkeys(recommendations))[:5]

        return recommendations

    def _determine_alert_level(self,
                             risk_score: float,
                             assessments: List[AttackVectorAssessment]) -> str:
        """Determine alert level based on risk assessment"""
        critical_assessments = [a for a in assessments if a.risk_level == RiskLevel.CRITICAL]

        if critical_assessments or risk_score >= 8.0:
            return "CRITICAL"
        elif risk_score >= 6.0:
            return "HIGH"
        elif risk_score >= 4.0:
            return "MODERATE"
        else:
            return "LOW"

    def _is_recent_proposal(self, proposal: Dict[str, Any], hours: int = 24) -> bool:
        """Check if proposal was submitted recently"""
        # In production, this would parse actual timestamps
        return True  # Simplified for example

    def _cache_results(self, report: GovernanceStabilityReport):
        """Cache analysis results"""
        self.historical_data.append({
            'timestamp': report.timestamp,
            'risk_score': report.overall_risk_score,
            'risk_level': report.overall_risk_level.value,
            'stability_indicators': report.stability_indicators
        })

        # Keep only recent data (last 30 days)
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        self.historical_data = [
            entry for entry in self.historical_data
            if entry['timestamp'] > cutoff_time
        ]

    def get_historical_data(self) -> List[Dict[str, Any]]:
        """Get cached historical analysis data"""
        return self.historical_data.copy()

    async def get_real_time_alerts(self) -> List[Dict[str, Any]]:
        """Get real-time governance alerts"""
        try:
            # Perform quick risk assessment
            report = await self.analyze_governance_stability()

            alerts = []

            if report.alert_level in ["CRITICAL", "HIGH"]:
                alerts.append({
                    'level': report.alert_level,
                    'message': f"Governance risk level: {report.overall_risk_level.value}",
                    'score': report.overall_risk_score,
                    'recommendations': report.recommendations[:3],
                    'timestamp': datetime.utcnow()
                })

            # Check for specific attack vector alerts
            critical_vectors = [a for a in report.attack_vector_assessments
                              if a.risk_level == RiskLevel.CRITICAL]
            for vector in critical_vectors:
                alerts.append({
                    'level': 'CRITICAL',
                    'message': f"Critical {vector.vector_type.value} risk detected",
                    'indicators': vector.current_indicators,
                    'recommendations': vector.mitigation_recommendations[:2],
                    'timestamp': datetime.utcnow()
                })

            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get real-time alerts: {e}")
            return []

# Export main class
__all__ = ['GovernanceAnalyzer', 'GovernanceStabilityReport', 'AttackVectorAssessment', 'RiskLevel', 'AttackVector']