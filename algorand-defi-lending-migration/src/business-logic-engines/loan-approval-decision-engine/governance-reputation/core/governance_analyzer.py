"""
Governance Analyzer

Comprehensive analysis of Algorand governance participation including voting,
proposal activity, and governance leadership for reputation scoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class GovernanceParticipationType(Enum):
    VOTER = "voter"
    DELEGATE = "delegate"
    PROPOSER = "proposer"
    GOVERNOR = "governor"


@dataclass
class GovernanceRecord:
    """Individual governance participation record"""
    address: str
    participation_type: GovernanceParticipationType
    period: str
    voting_power: float
    proposals_voted: int
    proposals_created: int
    governance_rewards: float
    participation_rate: float
    consistency_score: float
    leadership_activities: List[str]
    timestamp: datetime


@dataclass
class GovernanceAnalysis:
    """Comprehensive governance analysis result"""
    address: str
    overall_score: float
    participation_score: float
    leadership_score: float
    consistency_score: float
    voting_quality_score: float
    proposal_activity_score: float
    governance_periods: int
    total_voting_power: float
    average_participation_rate: float
    governance_achievements: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    analysis_timestamp: datetime


class GovernanceAnalyzer:
    """Analyzes Algorand governance participation and engagement"""

    def __init__(self, config_path: str = None):
        """Initialize governance analyzer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.governance_config = self.config['governance_scoring']
        self.data_sources = self.config['data_sources']
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def analyze_governance_participation(self, address: str) -> GovernanceAnalysis:
        """
        Analyze comprehensive governance participation for an address

        Args:
            address: Algorand address to analyze

        Returns:
            GovernanceAnalysis with detailed participation metrics
        """
        try:
            logger.info(f"Starting governance analysis for address: {address}")

            # Gather governance data from multiple sources
            governance_data = await self._fetch_governance_data(address)
            voting_history = await self._fetch_voting_history(address)
            proposal_activity = await self._fetch_proposal_activity(address)
            delegation_data = await self._fetch_delegation_data(address)

            # Analyze different aspects of governance participation
            participation_score = self._calculate_participation_score(governance_data, voting_history)
            leadership_score = self._calculate_leadership_score(proposal_activity, governance_data)
            consistency_score = self._calculate_consistency_score(voting_history)
            voting_quality_score = self._calculate_voting_quality_score(voting_history)
            proposal_activity_score = self._calculate_proposal_activity_score(proposal_activity)

            # Calculate overall governance score
            overall_score = self._calculate_overall_governance_score(
                participation_score,
                leadership_score,
                consistency_score,
                voting_quality_score,
                proposal_activity_score
            )

            # Identify achievements and risk factors
            achievements = self._identify_governance_achievements(governance_data, voting_history, proposal_activity)
            risk_factors = self._identify_governance_risks(governance_data, voting_history)
            recommendations = self._generate_governance_recommendations(
                participation_score, leadership_score, consistency_score
            )

            # Calculate aggregate metrics
            total_periods = len(governance_data.get('periods', []))
            total_voting_power = sum(period.get('voting_power', 0) for period in governance_data.get('periods', []))
            avg_participation_rate = sum(period.get('participation_rate', 0) for period in governance_data.get('periods', [])) / max(total_periods, 1)

            return GovernanceAnalysis(
                address=address,
                overall_score=overall_score,
                participation_score=participation_score,
                leadership_score=leadership_score,
                consistency_score=consistency_score,
                voting_quality_score=voting_quality_score,
                proposal_activity_score=proposal_activity_score,
                governance_periods=total_periods,
                total_voting_power=total_voting_power,
                average_participation_rate=avg_participation_rate,
                governance_achievements=achievements,
                risk_factors=risk_factors,
                recommendations=recommendations,
                analysis_timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error analyzing governance participation for {address}: {e}")
            raise

    async def _fetch_governance_data(self, address: str) -> Dict[str, Any]:
        """Fetch governance participation data from Algorand Foundation APIs"""
        try:
            governance_api = self.data_sources['algorand_foundation']['governance_api']

            # Simulate API response - in production, use real API calls
            governance_data = {
                'address': address,
                'periods': [
                    {
                        'period_id': 'period_1',
                        'start_date': '2021-10-01',
                        'end_date': '2021-12-31',
                        'voting_power': 10000.0,
                        'proposals_voted': 8,
                        'total_proposals': 10,
                        'participation_rate': 0.8,
                        'governance_rewards': 250.0,
                        'status': 'completed'
                    },
                    {
                        'period_id': 'period_2',
                        'start_date': '2022-01-01',
                        'end_date': '2022-03-31',
                        'voting_power': 12000.0,
                        'proposals_voted': 12,
                        'total_proposals': 12,
                        'participation_rate': 1.0,
                        'governance_rewards': 300.0,
                        'status': 'completed'
                    },
                    {
                        'period_id': 'period_3',
                        'start_date': '2022-04-01',
                        'end_date': '2022-06-30',
                        'voting_power': 15000.0,
                        'proposals_voted': 15,
                        'total_proposals': 18,
                        'participation_rate': 0.83,
                        'governance_rewards': 375.0,
                        'status': 'completed'
                    }
                ],
                'total_committed': 37000.0,
                'total_rewards': 925.0,
                'delegate_status': False,
                'governor_status': True
            }

            return governance_data

        except Exception as e:
            logger.error(f"Error fetching governance data: {e}")
            return {'periods': [], 'total_committed': 0, 'total_rewards': 0}

    async def _fetch_voting_history(self, address: str) -> Dict[str, Any]:
        """Fetch detailed voting history and patterns"""
        try:
            # Simulate voting history data
            voting_history = {
                'votes': [
                    {
                        'proposal_id': 'prop_001',
                        'vote': 'yes',
                        'vote_power': 10000,
                        'timestamp': '2021-10-15T10:00:00Z',
                        'reasoning_provided': True,
                        'debate_participation': True
                    },
                    {
                        'proposal_id': 'prop_002',
                        'vote': 'no',
                        'vote_power': 10000,
                        'timestamp': '2021-11-01T14:00:00Z',
                        'reasoning_provided': True,
                        'debate_participation': False
                    },
                    {
                        'proposal_id': 'prop_003',
                        'vote': 'abstain',
                        'vote_power': 12000,
                        'timestamp': '2022-01-15T09:00:00Z',
                        'reasoning_provided': False,
                        'debate_participation': True
                    }
                ],
                'voting_patterns': {
                    'consistency_score': 0.85,
                    'informed_voting_rate': 0.75,
                    'debate_participation_rate': 0.67,
                    'early_voting_rate': 0.80
                }
            }

            return voting_history

        except Exception as e:
            logger.error(f"Error fetching voting history: {e}")
            return {'votes': [], 'voting_patterns': {}}

    async def _fetch_proposal_activity(self, address: str) -> Dict[str, Any]:
        """Fetch proposal creation and leadership activity"""
        try:
            # Simulate proposal activity data
            proposal_activity = {
                'proposals_created': [
                    {
                        'proposal_id': 'user_prop_001',
                        'title': 'Enhance DeFi Integration',
                        'status': 'approved',
                        'support_votes': 850000,
                        'opposition_votes': 150000,
                        'community_feedback_score': 0.92,
                        'implementation_success': True,
                        'created_date': '2022-02-01T10:00:00Z'
                    }
                ],
                'proposal_support': [
                    {
                        'proposal_id': 'prop_004',
                        'support_type': 'co_sponsor',
                        'contribution_type': 'technical_review'
                    },
                    {
                        'proposal_id': 'prop_005',
                        'support_type': 'advocate',
                        'contribution_type': 'community_outreach'
                    }
                ],
                'leadership_metrics': {
                    'proposal_success_rate': 1.0,
                    'community_support_average': 0.85,
                    'technical_contribution_score': 0.78
                }
            }

            return proposal_activity

        except Exception as e:
            logger.error(f"Error fetching proposal activity: {e}")
            return {'proposals_created': [], 'proposal_support': [], 'leadership_metrics': {}}

    async def _fetch_delegation_data(self, address: str) -> Dict[str, Any]:
        """Fetch delegation patterns and relationships"""
        try:
            # Simulate delegation data
            delegation_data = {
                'as_delegator': {
                    'delegates_to': None,
                    'delegation_history': [],
                    'delegation_stability': 0.0
                },
                'as_delegate': {
                    'delegators': [],
                    'total_delegated_power': 0,
                    'delegate_reputation': 0.0
                }
            }

            return delegation_data

        except Exception as e:
            logger.error(f"Error fetching delegation data: {e}")
            return {'as_delegator': {}, 'as_delegate': {}}

    def _calculate_participation_score(self, governance_data: Dict, voting_history: Dict) -> float:
        """Calculate governance participation score"""
        try:
            periods = governance_data.get('periods', [])
            if not periods:
                return 0.0

            # Calculate average participation rate
            total_participation = sum(period.get('participation_rate', 0) for period in periods)
            avg_participation = total_participation / len(periods)

            # Apply weights from config
            participation_weight = self.governance_config['voting_participation']['weight']
            min_threshold = self.governance_config['voting_participation']['min_participation_rate']
            excellent_threshold = self.governance_config['voting_participation']['excellent_threshold']

            # Normalize score
            if avg_participation < min_threshold:
                score = (avg_participation / min_threshold) * 30
            elif avg_participation >= excellent_threshold:
                score = 90 + (avg_participation - excellent_threshold) * 50
            else:
                score = 30 + ((avg_participation - min_threshold) / (excellent_threshold - min_threshold)) * 60

            # Apply consistency bonus
            voting_patterns = voting_history.get('voting_patterns', {})
            consistency = voting_patterns.get('consistency_score', 0)
            consistency_bonus = self.governance_config['voting_participation']['consistency_bonus']

            final_score = min(100, score + (consistency * consistency_bonus * 100))

            return final_score

        except Exception as e:
            logger.error(f"Error calculating participation score: {e}")
            return 0.0

    def _calculate_leadership_score(self, proposal_activity: Dict, governance_data: Dict) -> float:
        """Calculate governance leadership score"""
        try:
            proposals_created = proposal_activity.get('proposals_created', [])
            leadership_metrics = proposal_activity.get('leadership_metrics', {})

            # Base score from proposal creation
            proposal_count = len(proposals_created)
            proposal_score = min(40, proposal_count * 10)

            # Quality bonus
            success_rate = leadership_metrics.get('proposal_success_rate', 0)
            community_support = leadership_metrics.get('community_support_average', 0)
            technical_score = leadership_metrics.get('technical_contribution_score', 0)

            quality_score = (success_rate * 30) + (community_support * 20) + (technical_score * 10)

            # Governor status bonus
            governor_bonus = 10 if governance_data.get('governor_status', False) else 0

            total_score = min(100, proposal_score + quality_score + governor_bonus)

            return total_score

        except Exception as e:
            logger.error(f"Error calculating leadership score: {e}")
            return 0.0

    def _calculate_consistency_score(self, voting_history: Dict) -> float:
        """Calculate voting consistency and reliability score"""
        try:
            voting_patterns = voting_history.get('voting_patterns', {})
            votes = voting_history.get('votes', [])

            if not votes:
                return 0.0

            # Base consistency from patterns
            consistency = voting_patterns.get('consistency_score', 0) * 100

            # Informed voting bonus
            informed_rate = voting_patterns.get('informed_voting_rate', 0)
            informed_bonus = informed_rate * 20

            # Debate participation bonus
            debate_rate = voting_patterns.get('debate_participation_rate', 0)
            debate_bonus = debate_rate * 15

            # Early voting bonus (shows engagement)
            early_rate = voting_patterns.get('early_voting_rate', 0)
            early_bonus = early_rate * 10

            total_score = min(100, consistency + informed_bonus + debate_bonus + early_bonus)

            return total_score

        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.0

    def _calculate_voting_quality_score(self, voting_history: Dict) -> float:
        """Calculate voting quality and engagement score"""
        try:
            votes = voting_history.get('votes', [])
            if not votes:
                return 0.0

            # Analyze vote quality factors
            reasoning_provided = sum(1 for vote in votes if vote.get('reasoning_provided', False))
            debate_participation = sum(1 for vote in votes if vote.get('debate_participation', False))

            reasoning_rate = reasoning_provided / len(votes)
            debate_rate = debate_participation / len(votes)

            # Apply config weights
            quality_weight = self.governance_config['voting_quality']['weight']

            quality_score = (reasoning_rate * 50) + (debate_rate * 30) + 20  # Base engagement score

            return min(100, quality_score)

        except Exception as e:
            logger.error(f"Error calculating voting quality score: {e}")
            return 0.0

    def _calculate_proposal_activity_score(self, proposal_activity: Dict) -> float:
        """Calculate proposal activity and contribution score"""
        try:
            proposals_created = proposal_activity.get('proposals_created', [])
            proposal_support = proposal_activity.get('proposal_support', [])
            leadership_metrics = proposal_activity.get('leadership_metrics', {})

            # Score for creating proposals
            creation_score = min(40, len(proposals_created) * 15)

            # Score for supporting proposals
            support_score = min(30, len(proposal_support) * 5)

            # Quality metrics
            success_rate = leadership_metrics.get('proposal_success_rate', 0)
            community_support = leadership_metrics.get('community_support_average', 0)

            quality_score = (success_rate * 20) + (community_support * 10)

            total_score = min(100, creation_score + support_score + quality_score)

            return total_score

        except Exception as e:
            logger.error(f"Error calculating proposal activity score: {e}")
            return 0.0

    def _calculate_overall_governance_score(self, participation: float, leadership: float,
                                          consistency: float, voting_quality: float,
                                          proposal_activity: float) -> float:
        """Calculate overall governance reputation score"""
        try:
            # Apply weights from config
            weights = self.governance_config

            weighted_score = (
                participation * weights['voting_participation']['weight'] +
                voting_quality * weights['voting_quality']['weight'] +
                proposal_activity * weights['proposal_activity']['weight'] +
                leadership * 0.15 +  # Leadership weight
                consistency * 0.10   # Consistency weight
            )

            return min(100, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating overall governance score: {e}")
            return 0.0

    def _identify_governance_achievements(self, governance_data: Dict, voting_history: Dict,
                                        proposal_activity: Dict) -> List[str]:
        """Identify notable governance achievements"""
        achievements = []

        try:
            # Check for consistent participation
            periods = governance_data.get('periods', [])
            if len(periods) >= 3:
                avg_participation = sum(p.get('participation_rate', 0) for p in periods) / len(periods)
                if avg_participation >= 0.9:
                    achievements.append("Excellent governance participation (90%+ average)")

            # Check for governance rewards
            total_rewards = governance_data.get('total_rewards', 0)
            if total_rewards > 1000:
                achievements.append(f"High governance rewards earned ({total_rewards:.0f} ALGO)")

            # Check for proposal success
            proposals = proposal_activity.get('proposals_created', [])
            successful_proposals = [p for p in proposals if p.get('status') == 'approved']
            if successful_proposals:
                achievements.append(f"Successful proposal creator ({len(successful_proposals)} approved)")

            # Check for high voting power commitment
            max_voting_power = max((p.get('voting_power', 0) for p in periods), default=0)
            if max_voting_power > 50000:
                achievements.append("High-commitment governance participant (50K+ ALGO)")

            # Check for governor status
            if governance_data.get('governor_status', False):
                achievements.append("Recognized ecosystem governor")

        except Exception as e:
            logger.error(f"Error identifying achievements: {e}")

        return achievements

    def _identify_governance_risks(self, governance_data: Dict, voting_history: Dict) -> List[str]:
        """Identify governance-related risk factors"""
        risks = []

        try:
            # Check for low participation
            periods = governance_data.get('periods', [])
            if periods:
                avg_participation = sum(p.get('participation_rate', 0) for p in periods) / len(periods)
                if avg_participation < 0.5:
                    risks.append("Low governance participation rate")

            # Check for voting inconsistency
            voting_patterns = voting_history.get('voting_patterns', {})
            consistency = voting_patterns.get('consistency_score', 0)
            if consistency < 0.7:
                risks.append("Inconsistent voting patterns")

            # Check for lack of informed voting
            informed_rate = voting_patterns.get('informed_voting_rate', 0)
            if informed_rate < 0.6:
                risks.append("Limited evidence of informed voting decisions")

            # Check for recent inactivity
            if periods:
                latest_period = max(periods, key=lambda p: p.get('start_date', ''))
                latest_participation = latest_period.get('participation_rate', 0)
                if latest_participation < 0.3:
                    risks.append("Recent decline in governance participation")

        except Exception as e:
            logger.error(f"Error identifying risks: {e}")

        return risks

    def _generate_governance_recommendations(self, participation: float, leadership: float,
                                           consistency: float) -> List[str]:
        """Generate recommendations for improving governance reputation"""
        recommendations = []

        try:
            if participation < 70:
                recommendations.append("Increase voting participation in governance periods")

            if leadership < 50:
                recommendations.append("Consider creating or supporting governance proposals")

            if consistency < 60:
                recommendations.append("Provide reasoning for votes and participate in governance discussions")

            if participation > 80 and leadership > 70 and consistency > 80:
                recommendations.append("Excellent governance participation - consider becoming a delegate")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

        return recommendations