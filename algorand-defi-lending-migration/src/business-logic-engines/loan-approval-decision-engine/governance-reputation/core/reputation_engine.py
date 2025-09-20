"""
Reputation Engine

Master reputation engine that combines governance participation, community engagement,
consensus participation, and ecosystem commitment for comprehensive reputation scoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path

from .governance_analyzer import GovernanceAnalyzer, GovernanceAnalysis
from .voting_patterns import VotingPatternAnalyzer, VotingPattern
from .community_engagement import CommunityEngagementAnalyzer, CommunityEngagementProfile
from .consensus_participation import ConsensusParticipationAnalyzer, ConsensusParticipationProfile
from .ecosystem_commitment import EcosystemCommitmentAnalyzer, EcosystemCommitmentProfile

logger = logging.getLogger(__name__)


class ReputationTier(Enum):
    UNACCEPTABLE = "unacceptable"
    POOR = "poor"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class ReputationBonus:
    """Reputation bonus details"""
    bonus_type: str
    multiplier: float
    description: str
    applicable: bool


@dataclass
class LoanDecisionImpact:
    """Impact of reputation on loan decisions"""
    ltv_adjustment: float  # Loan-to-value ratio adjustment
    rate_adjustment: float  # Interest rate adjustment
    approval_bias: float  # Approval likelihood adjustment
    auto_reject: bool  # Automatic rejection flag
    manual_review_required: bool  # Manual review requirement


@dataclass
class ComprehensiveReputation:
    """Comprehensive reputation analysis result"""
    address: str
    overall_reputation_score: float
    reputation_tier: ReputationTier

    # Component scores
    governance_score: float
    community_engagement_score: float
    consensus_participation_score: float
    ecosystem_commitment_score: float

    # Detailed analyses
    governance_analysis: Optional[GovernanceAnalysis]
    voting_patterns: Optional[VotingPattern]
    community_profile: Optional[CommunityEngagementProfile]
    consensus_profile: Optional[ConsensusParticipationProfile]
    commitment_profile: Optional[EcosystemCommitmentProfile]

    # Reputation modifiers
    applied_bonuses: List[ReputationBonus]
    time_decay_factor: float
    reputation_trends: Dict[str, float]

    # Risk assessment
    reputation_risks: List[str]
    red_flags: List[str]
    positive_indicators: List[str]

    # Loan decision impact
    loan_decision_impact: LoanDecisionImpact

    # Recommendations
    improvement_recommendations: List[str]

    # Metadata
    analysis_timestamp: datetime
    analysis_period: Tuple[datetime, datetime]
    confidence_score: float


class ReputationEngine:
    """Master reputation engine for comprehensive reputation analysis"""

    def __init__(self, config_path: str = None):
        """Initialize reputation engine with all component analyzers"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.reputation_config = self.config['reputation_engine']
        self.risk_adjustments = self.config['risk_adjustments']

        # Initialize component analyzers
        self.governance_analyzer = GovernanceAnalyzer(config_path)
        self.voting_analyzer = VotingPatternAnalyzer(config_path)
        self.community_analyzer = CommunityEngagementAnalyzer(config_path)
        self.consensus_analyzer = ConsensusParticipationAnalyzer(config_path)
        self.commitment_analyzer = EcosystemCommitmentAnalyzer(config_path)

    async def analyze_comprehensive_reputation(self, address: str,
                                             start_date: Optional[datetime] = None,
                                             end_date: Optional[datetime] = None) -> ComprehensiveReputation:
        """
        Perform comprehensive reputation analysis for an address

        Args:
            address: Algorand address to analyze
            start_date: Analysis start date (default: 2 years ago)
            end_date: Analysis end date (default: now)

        Returns:
            ComprehensiveReputation with detailed analysis
        """
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            if start_date is None:
                start_date = end_date - timedelta(days=730)  # 2 years

            logger.info(f"Starting comprehensive reputation analysis for {address}")

            # Run all component analyses in parallel
            async with self.consensus_analyzer:
                governance_task = self.governance_analyzer.analyze_governance_participation(address, start_date, end_date)
                voting_task = self.voting_analyzer.analyze_voting_patterns(address, start_date, end_date)
                community_task = self.community_analyzer.analyze_community_engagement(address, start_date, end_date)
                consensus_task = self.consensus_analyzer.analyze_consensus_participation(address, start_date, end_date)
                commitment_task = self.commitment_analyzer.analyze_ecosystem_commitment(address, start_date, end_date)

                # Wait for all analyses to complete
                governance_analysis, voting_patterns, community_profile, consensus_profile, commitment_profile = await asyncio.gather(
                    governance_task, voting_task, community_task, consensus_task, commitment_task,
                    return_exceptions=True
                )

            # Handle any exceptions in component analyses
            if isinstance(governance_analysis, Exception):
                logger.error(f"Governance analysis failed: {governance_analysis}")
                governance_analysis = None
            if isinstance(voting_patterns, Exception):
                logger.error(f"Voting patterns analysis failed: {voting_patterns}")
                voting_patterns = None
            if isinstance(community_profile, Exception):
                logger.error(f"Community engagement analysis failed: {community_profile}")
                community_profile = None
            if isinstance(consensus_profile, Exception):
                logger.error(f"Consensus participation analysis failed: {consensus_profile}")
                consensus_profile = None
            if isinstance(commitment_profile, Exception):
                logger.error(f"Ecosystem commitment analysis failed: {commitment_profile}")
                commitment_profile = None

            # Extract component scores
            governance_score = governance_analysis.overall_score if governance_analysis else 0.0
            community_score = community_profile.overall_engagement_score if community_profile else 0.0
            consensus_score = consensus_profile.overall_consensus_score if consensus_profile else 0.0
            commitment_score = commitment_profile.overall_commitment_score if commitment_profile else 0.0

            # Calculate overall reputation score
            overall_score = self._calculate_overall_reputation_score(
                governance_score, community_score, consensus_score, commitment_score
            )

            # Apply reputation modifiers
            applied_bonuses = self._determine_reputation_bonuses(
                governance_analysis, community_profile, consensus_profile, commitment_profile
            )
            time_decay_factor = self._calculate_time_decay_factor(start_date, end_date)

            # Apply bonuses and time decay
            modified_score = self._apply_reputation_modifiers(overall_score, applied_bonuses, time_decay_factor)

            # Determine reputation tier
            reputation_tier = self._determine_reputation_tier(modified_score)

            # Calculate reputation trends
            reputation_trends = self._analyze_reputation_trends(
                governance_analysis, community_profile, consensus_profile, commitment_profile
            )

            # Identify risks and indicators
            reputation_risks = self._consolidate_reputation_risks(
                governance_analysis, community_profile, consensus_profile, commitment_profile
            )
            red_flags = self._identify_red_flags(
                governance_analysis, community_profile, consensus_profile, commitment_profile
            )
            positive_indicators = self._consolidate_positive_indicators(
                governance_analysis, community_profile, consensus_profile, commitment_profile
            )

            # Calculate loan decision impact
            loan_decision_impact = self._calculate_loan_decision_impact(modified_score, reputation_tier, red_flags)

            # Generate improvement recommendations
            improvement_recommendations = self._generate_improvement_recommendations(
                governance_score, community_score, consensus_score, commitment_score
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                governance_analysis, community_profile, consensus_profile, commitment_profile
            )

            return ComprehensiveReputation(
                address=address,
                overall_reputation_score=modified_score,
                reputation_tier=reputation_tier,
                governance_score=governance_score,
                community_engagement_score=community_score,
                consensus_participation_score=consensus_score,
                ecosystem_commitment_score=commitment_score,
                governance_analysis=governance_analysis,
                voting_patterns=voting_patterns,
                community_profile=community_profile,
                consensus_profile=consensus_profile,
                commitment_profile=commitment_profile,
                applied_bonuses=applied_bonuses,
                time_decay_factor=time_decay_factor,
                reputation_trends=reputation_trends,
                reputation_risks=reputation_risks,
                red_flags=red_flags,
                positive_indicators=positive_indicators,
                loan_decision_impact=loan_decision_impact,
                improvement_recommendations=improvement_recommendations,
                analysis_timestamp=datetime.utcnow(),
                analysis_period=(start_date, end_date),
                confidence_score=confidence_score
            )

        except Exception as e:
            logger.error(f"Error in comprehensive reputation analysis for {address}: {e}")
            raise

    def _calculate_overall_reputation_score(self, governance_score: float, community_score: float,
                                          consensus_score: float, commitment_score: float) -> float:
        """Calculate overall reputation score using configured weights"""
        try:
            weights = self.reputation_config['category_weights']

            weighted_score = (
                governance_score * weights['governance_participation'] +
                community_score * weights['community_engagement'] +
                consensus_score * weights['consensus_participation'] +
                commitment_score * weights['ecosystem_commitment']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating overall reputation score: {e}")
            return 0.0

    def _determine_reputation_bonuses(self, governance_analysis, community_profile,
                                    consensus_profile, commitment_profile) -> List[ReputationBonus]:
        """Determine applicable reputation bonuses"""
        bonuses = []
        bonus_config = self.reputation_config['bonuses']

        try:
            # Founding member bonus
            if commitment_profile and hasattr(commitment_profile, 'analysis_period'):
                # Check if user has been active since early ecosystem days
                early_activity = any(
                    engagement.first_interaction < datetime(2021, 6, 1)
                    for engagement in commitment_profile.protocol_relationships
                )
                if early_activity:
                    bonuses.append(ReputationBonus(
                        bonus_type="founding_member",
                        multiplier=bonus_config['founding_member'],
                        description="Early ecosystem participant",
                        applicable=True
                    ))

            # Core contributor bonus
            if community_profile and community_profile.development_contribution_score > 80:
                bonuses.append(ReputationBonus(
                    bonus_type="core_contributor",
                    multiplier=bonus_config['core_contributor'],
                    description="Significant development contributions",
                    applicable=True
                ))

            # Security researcher bonus
            if consensus_profile and consensus_profile.security_contribution_score > 70:
                bonuses.append(ReputationBonus(
                    bonus_type="security_researcher",
                    multiplier=bonus_config['security_researcher'],
                    description="Active security contributions",
                    applicable=True
                ))

            # Ambassador bonus
            if (community_profile and community_profile.ecosystem_advocacy_score > 75 and
                governance_analysis and governance_analysis.overall_score > 70):
                bonuses.append(ReputationBonus(
                    bonus_type="ambassador",
                    multiplier=bonus_config['ambassador'],
                    description="Ecosystem ambassador activities",
                    applicable=True
                ))

            # Educator bonus
            if community_profile and community_profile.community_building_score > 80:
                bonuses.append(ReputationBonus(
                    bonus_type="educator",
                    multiplier=bonus_config['educator'],
                    description="Community education and mentoring",
                    applicable=True
                ))

        except Exception as e:
            logger.error(f"Error determining reputation bonuses: {e}")

        return bonuses

    def _calculate_time_decay_factor(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate time decay factor based on recency of activities"""
        try:
            total_days = (end_date - start_date).days
            recent_period = min(180, total_days // 3)  # Last 6 months or 1/3 of period
            medium_period = min(540, total_days * 2 // 3)  # 6-18 months or 2/3 of period

            # Use configured weights
            weights = self.reputation_config['time_decay']

            # Simplified time decay - in practice, would analyze activity recency
            decay_factor = (
                weights['recent_activity_weight'] * 1.0 +  # Assume recent activity
                weights['medium_term_weight'] * 0.9 +     # Assume some medium-term activity
                weights['historical_weight'] * 0.8        # Assume historical activity
            )

            return decay_factor

        except Exception as e:
            logger.error(f"Error calculating time decay factor: {e}")
            return 1.0

    def _apply_reputation_modifiers(self, base_score: float, bonuses: List[ReputationBonus],
                                   time_decay: float) -> float:
        """Apply reputation bonuses and time decay to base score"""
        try:
            # Apply bonuses multiplicatively
            modified_score = base_score
            for bonus in bonuses:
                if bonus.applicable:
                    modified_score *= bonus.multiplier

            # Apply time decay
            modified_score *= time_decay

            return min(100.0, modified_score)

        except Exception as e:
            logger.error(f"Error applying reputation modifiers: {e}")
            return base_score

    def _determine_reputation_tier(self, score: float) -> ReputationTier:
        """Determine reputation tier based on score"""
        try:
            thresholds = self.reputation_config['thresholds']

            if score >= thresholds['excellent']:
                return ReputationTier.EXCELLENT
            elif score >= thresholds['good']:
                return ReputationTier.GOOD
            elif score >= thresholds['average']:
                return ReputationTier.AVERAGE
            elif score >= thresholds['poor']:
                return ReputationTier.POOR
            else:
                return ReputationTier.UNACCEPTABLE

        except Exception as e:
            logger.error(f"Error determining reputation tier: {e}")
            return ReputationTier.UNACCEPTABLE

    def _analyze_reputation_trends(self, governance_analysis, community_profile,
                                 consensus_profile, commitment_profile) -> Dict[str, float]:
        """Analyze trends in reputation components"""
        trends = {}

        try:
            # Governance trends
            if governance_analysis and hasattr(governance_analysis, 'governance_periods'):
                if governance_analysis.governance_periods > 1:
                    trends['governance_trend'] = 0.05  # Slight positive trend
                else:
                    trends['governance_trend'] = 0.0

            # Community engagement trends
            if community_profile and hasattr(community_profile, 'engagement_trends'):
                if hasattr(community_profile.engagement_trends, 'get'):
                    trends['community_trend'] = community_profile.engagement_trends.get('activity_frequency_trend', 0.0)
                else:
                    trends['community_trend'] = 0.0

            # Default neutral trends for missing data
            trends.setdefault('governance_trend', 0.0)
            trends.setdefault('community_trend', 0.0)
            trends.setdefault('consensus_trend', 0.0)
            trends.setdefault('commitment_trend', 0.0)

        except Exception as e:
            logger.error(f"Error analyzing reputation trends: {e}")

        return trends

    def _consolidate_reputation_risks(self, governance_analysis, community_profile,
                                    consensus_profile, commitment_profile) -> List[str]:
        """Consolidate reputation risks from all components"""
        risks = []

        try:
            if governance_analysis and hasattr(governance_analysis, 'risk_factors'):
                risks.extend(governance_analysis.risk_factors)

            if community_profile and hasattr(community_profile, 'risk_factors'):
                risks.extend(community_profile.risk_factors)

            if consensus_profile and hasattr(consensus_profile, 'risk_factors'):
                risks.extend(consensus_profile.risk_factors)

            if commitment_profile and hasattr(commitment_profile, 'risk_factors'):
                risks.extend(commitment_profile.risk_factors)

            # Remove duplicates while preserving order
            seen = set()
            unique_risks = []
            for risk in risks:
                if risk not in seen:
                    seen.add(risk)
                    unique_risks.append(risk)

            return unique_risks

        except Exception as e:
            logger.error(f"Error consolidating reputation risks: {e}")
            return []

    def _identify_red_flags(self, governance_analysis, community_profile,
                          consensus_profile, commitment_profile) -> List[str]:
        """Identify serious red flags that should trigger manual review"""
        red_flags = []

        try:
            # Governance red flags
            if governance_analysis and governance_analysis.overall_score < 20:
                red_flags.append("Extremely poor governance participation")

            # Community red flags
            if community_profile and community_profile.overall_engagement_score < 15:
                red_flags.append("Minimal community engagement")

            # Consensus red flags
            if (consensus_profile and
                hasattr(consensus_profile, 'risk_factors') and
                any("security" in risk.lower() for risk in consensus_profile.risk_factors)):
                red_flags.append("Security concerns in consensus participation")

            # Commitment red flags
            if (commitment_profile and
                hasattr(commitment_profile, 'risk_factors') and
                any("selling" in risk.lower() for risk in commitment_profile.risk_factors)):
                red_flags.append("Recent significant selling activity")

            # Cross-component red flags
            component_scores = []
            if governance_analysis:
                component_scores.append(governance_analysis.overall_score)
            if community_profile:
                component_scores.append(community_profile.overall_engagement_score)
            if consensus_profile:
                component_scores.append(consensus_profile.overall_consensus_score)
            if commitment_profile:
                component_scores.append(commitment_profile.overall_commitment_score)

            if component_scores and all(score < 30 for score in component_scores):
                red_flags.append("Consistently poor performance across all reputation categories")

        except Exception as e:
            logger.error(f"Error identifying red flags: {e}")

        return red_flags

    def _consolidate_positive_indicators(self, governance_analysis, community_profile,
                                       consensus_profile, commitment_profile) -> List[str]:
        """Consolidate positive indicators from all components"""
        indicators = []

        try:
            if governance_analysis and hasattr(governance_analysis, 'governance_achievements'):
                indicators.extend(governance_analysis.governance_achievements)

            if community_profile and hasattr(community_profile, 'leadership_indicators'):
                indicators.extend(community_profile.leadership_indicators)

            if consensus_profile and hasattr(consensus_profile, 'network_contributions'):
                indicators.extend(consensus_profile.network_contributions)

            if commitment_profile and hasattr(commitment_profile, 'commitment_indicators'):
                indicators.extend(commitment_profile.commitment_indicators)

            # Remove duplicates while preserving order
            seen = set()
            unique_indicators = []
            for indicator in indicators:
                if indicator not in seen:
                    seen.add(indicator)
                    unique_indicators.append(indicator)

            return unique_indicators

        except Exception as e:
            logger.error(f"Error consolidating positive indicators: {e}")
            return []

    def _calculate_loan_decision_impact(self, reputation_score: float, reputation_tier: ReputationTier,
                                      red_flags: List[str]) -> LoanDecisionImpact:
        """Calculate impact of reputation on loan decisions"""
        try:
            impact_config = self.risk_adjustments['loan_decision_impact']

            # Check for automatic rejection
            auto_reject = False
            manual_review = False

            if reputation_tier == ReputationTier.UNACCEPTABLE:
                auto_reject = impact_config['unacceptable_reputation']['auto_reject']
                manual_review = impact_config['unacceptable_reputation']['manual_review_required']

            if red_flags:
                manual_review = True

            # Determine adjustments based on reputation tier
            if reputation_tier == ReputationTier.EXCELLENT:
                adjustments = impact_config['excellent_reputation']
            elif reputation_tier == ReputationTier.GOOD:
                adjustments = impact_config['good_reputation']
            elif reputation_tier == ReputationTier.POOR:
                adjustments = impact_config.get('poor_reputation', {
                    'ltv_penalty': -0.10,
                    'rate_penalty': 0.01,
                    'approval_penalty': -0.20
                })
            else:
                # Average or unacceptable
                adjustments = {
                    'ltv_bonus': 0.0,
                    'rate_discount': 0.0,
                    'approval_bias': 0.0,
                    'ltv_penalty': 0.0,
                    'rate_penalty': 0.0,
                    'approval_penalty': 0.0
                }

            # Calculate final adjustments
            ltv_adjustment = adjustments.get('ltv_bonus', 0) + adjustments.get('ltv_penalty', 0)
            rate_adjustment = -adjustments.get('rate_discount', 0) + adjustments.get('rate_penalty', 0)
            approval_bias = adjustments.get('approval_bias', 0) + adjustments.get('approval_penalty', 0)

            return LoanDecisionImpact(
                ltv_adjustment=ltv_adjustment,
                rate_adjustment=rate_adjustment,
                approval_bias=approval_bias,
                auto_reject=auto_reject,
                manual_review_required=manual_review
            )

        except Exception as e:
            logger.error(f"Error calculating loan decision impact: {e}")
            return LoanDecisionImpact(0.0, 0.0, 0.0, False, True)

    def _generate_improvement_recommendations(self, governance_score: float, community_score: float,
                                            consensus_score: float, commitment_score: float) -> List[str]:
        """Generate comprehensive improvement recommendations"""
        recommendations = []

        try:
            # Identify weakest areas and provide specific recommendations
            scores = {
                'governance': governance_score,
                'community': community_score,
                'consensus': consensus_score,
                'commitment': commitment_score
            }

            # Find the lowest scoring area
            weakest_area = min(scores, key=scores.get)
            weakest_score = scores[weakest_area]

            if weakest_score < 40:
                if weakest_area == 'governance':
                    recommendations.append("Critical: Increase governance participation and voting consistency")
                elif weakest_area == 'community':
                    recommendations.append("Critical: Engage more actively in community forums and development")
                elif weakest_area == 'consensus':
                    recommendations.append("Critical: Consider running a node or contributing to network security")
                elif weakest_area == 'commitment':
                    recommendations.append("Critical: Demonstrate long-term ecosystem commitment through holdings and usage")

            # General recommendations based on overall performance
            avg_score = sum(scores.values()) / len(scores)

            if avg_score < 50:
                recommendations.append("Overall reputation is below average - focus on consistent ecosystem participation")
            elif avg_score > 80:
                recommendations.append("Excellent reputation - consider taking on leadership roles in the ecosystem")

            # Specific actionable recommendations
            if governance_score < 60:
                recommendations.append("Participate more actively in governance voting and provide reasoning for votes")

            if community_score < 60:
                recommendations.append("Contribute to forums, help other developers, or create educational content")

            if consensus_score < 40:
                recommendations.append("Consider operating a participation or relay node")

            if commitment_score < 60:
                recommendations.append("Increase long-term ALGO holdings and engage with more DeFi protocols")

        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {e}")

        return recommendations

    def _calculate_confidence_score(self, governance_analysis, community_profile,
                                   consensus_profile, commitment_profile) -> float:
        """Calculate confidence score for the reputation analysis"""
        try:
            # Base confidence on data availability and quality
            data_sources = 0
            total_sources = 4

            if governance_analysis:
                data_sources += 1
            if community_profile:
                data_sources += 1
            if consensus_profile:
                data_sources += 1
            if commitment_profile:
                data_sources += 1

            # Calculate base confidence
            base_confidence = data_sources / total_sources

            # Adjust for data quality (simplified)
            quality_adjustments = 0
            quality_checks = 0

            if governance_analysis and hasattr(governance_analysis, 'governance_periods'):
                if governance_analysis.governance_periods > 1:
                    quality_adjustments += 0.1
                quality_checks += 1

            if community_profile and hasattr(community_profile, 'total_activities'):
                if community_profile.total_activities > 5:
                    quality_adjustments += 0.1
                quality_checks += 1

            # Calculate final confidence
            quality_bonus = quality_adjustments / max(quality_checks, 1) if quality_checks > 0 else 0
            final_confidence = min(1.0, base_confidence + quality_bonus)

            return final_confidence

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5  # Default moderate confidence