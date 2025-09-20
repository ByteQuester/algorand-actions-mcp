"""
Governance Tracker

Tracks and analyzes governance participation across the Algorand ecosystem
to assess long-term commitment and community engagement.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import statistics

from ..models.decision_models import ParticipationType, GovernanceParticipation

logger = logging.getLogger(__name__)


@dataclass
class GovernanceEvent:
    """Represents a single governance event"""
    event_type: str  # 'vote', 'proposal', 'delegation', 'committee'
    timestamp: datetime
    proposal_id: str
    vote_choice: Optional[str] = None
    vote_weight: float = 0.0
    delegation_amount: float = 0.0
    proposal_title: Optional[str] = None
    proposal_category: Optional[str] = None


@dataclass
class GovernanceMetrics:
    """Governance participation metrics"""
    participation_score: float
    consistency_score: float
    influence_score: float
    commitment_score: float
    community_engagement_score: float
    expertise_score: float


@dataclass
class GovernanceAnalysisResult:
    """Comprehensive governance analysis results"""
    participation_type: ParticipationType
    participation_metrics: GovernanceMetrics
    governance_events: List[GovernanceEvent]
    governance_periods: List[Dict[str, Any]]
    behavioral_patterns: Dict[str, Any]
    risk_indicators: Dict[str, Any]
    recommendations: List[str]


class GovernanceTracker:
    """
    Tracks and analyzes governance participation to assess
    community commitment and institutional reliability.
    """

    def __init__(self):
        self.governance_periods = self._load_governance_periods()
        self.proposal_categories = self._load_proposal_categories()

    async def analyze_governance_participation(
        self,
        wallet_address: str,
        analysis_period_months: int = 24
    ) -> GovernanceAnalysisResult:
        """
        Analyze complete governance participation history.

        Args:
            wallet_address: Address to analyze
            analysis_period_months: Period to analyze (default 24 months)

        Returns:
            Comprehensive governance analysis results
        """
        logger.info(f"Analyzing governance participation for {wallet_address}")

        try:
            # Fetch governance data
            governance_events = await self._fetch_governance_events(
                wallet_address, analysis_period_months
            )

            if not governance_events:
                logger.info(f"No governance participation found for {wallet_address}")
                return self._create_no_participation_result()

            # Parallel analysis of different aspects
            tasks = [
                self._analyze_voting_patterns(governance_events),
                self._analyze_proposal_activity(governance_events),
                self._analyze_delegation_behavior(governance_events),
                self._analyze_participation_consistency(governance_events),
                self._analyze_expertise_indicators(governance_events),
                self._analyze_community_engagement(governance_events),
                self._detect_governance_gaming(governance_events)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract analysis results
            voting_analysis = results[0] if not isinstance(results[0], Exception) else {}
            proposal_analysis = results[1] if not isinstance(results[1], Exception) else {}
            delegation_analysis = results[2] if not isinstance(results[2], Exception) else {}
            consistency_analysis = results[3] if not isinstance(results[3], Exception) else {}
            expertise_analysis = results[4] if not isinstance(results[4], Exception) else {}
            engagement_analysis = results[5] if not isinstance(results[5], Exception) else {}
            gaming_analysis = results[6] if not isinstance(results[6], Exception) else {}

            # Determine participation type
            participation_type = self._determine_participation_type(
                voting_analysis, proposal_analysis, delegation_analysis
            )

            # Calculate metrics
            participation_metrics = self._calculate_governance_metrics(
                voting_analysis, proposal_analysis, delegation_analysis,
                consistency_analysis, expertise_analysis, engagement_analysis
            )

            # Analyze governance periods
            governance_periods = self._analyze_governance_periods(governance_events)

            # Compile behavioral patterns
            behavioral_patterns = self._compile_behavioral_patterns(
                voting_analysis, consistency_analysis, engagement_analysis
            )

            # Identify risk indicators
            risk_indicators = self._compile_risk_indicators(gaming_analysis)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                participation_type, participation_metrics, behavioral_patterns
            )

            return GovernanceAnalysisResult(
                participation_type=participation_type,
                participation_metrics=participation_metrics,
                governance_events=governance_events,
                governance_periods=governance_periods,
                behavioral_patterns=behavioral_patterns,
                risk_indicators=risk_indicators,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Governance analysis failed for {wallet_address}: {e}")
            raise

    async def _fetch_governance_events(
        self,
        address: str,
        period_months: int
    ) -> List[GovernanceEvent]:
        """Fetch governance events from Algorand governance APIs"""
        # Mock implementation - would integrate with Algorand governance APIs
        events = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=period_months * 30)

        # Generate mock governance events
        current_time = start_time

        # Simulate participation in multiple governance periods
        governance_periods = [
            {'start': start_time, 'end': start_time + timedelta(days=90), 'period': 1},
            {'start': start_time + timedelta(days=120), 'end': start_time + timedelta(days=210), 'period': 2},
            {'start': start_time + timedelta(days=240), 'end': start_time + timedelta(days=330), 'period': 3},
            {'start': start_time + timedelta(days=360), 'end': end_time, 'period': 4}
        ]

        for period in governance_periods:
            # Generate votes for this period
            proposals_in_period = [
                f"proposal_{period['period']}_1",
                f"proposal_{period['period']}_2",
                f"proposal_{period['period']}_3"
            ]

            for proposal_id in proposals_in_period:
                vote_time = period['start'] + timedelta(
                    days=__import__('random').randint(10, 60)
                )

                if vote_time <= end_time:
                    event = GovernanceEvent(
                        event_type='vote',
                        timestamp=vote_time,
                        proposal_id=proposal_id,
                        vote_choice='yes',  # Consistent voter
                        vote_weight=__import__('random').uniform(1000, 5000),
                        proposal_title=f"Governance Proposal {proposal_id}",
                        proposal_category='protocol_upgrade'
                    )
                    events.append(event)

            # Occasional delegation events
            if __import__('random').random() > 0.7:  # 30% chance
                delegation_time = period['start'] + timedelta(days=5)
                if delegation_time <= end_time:
                    event = GovernanceEvent(
                        event_type='delegation',
                        timestamp=delegation_time,
                        proposal_id='',
                        delegation_amount=__import__('random').uniform(2000, 8000)
                    )
                    events.append(event)

        # Occasional proposal submissions
        if __import__('random').random() > 0.8:  # 20% chance of being a proposer
            proposal_time = start_time + timedelta(days=200)
            if proposal_time <= end_time:
                event = GovernanceEvent(
                    event_type='proposal',
                    timestamp=proposal_time,
                    proposal_id='user_proposal_1',
                    proposal_title='Community Improvement Proposal',
                    proposal_category='community'
                )
                events.append(event)

        return sorted(events, key=lambda x: x.timestamp)

    async def _analyze_voting_patterns(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Analyze voting behavior and patterns"""
        vote_events = [e for e in events if e.event_type == 'vote']

        if not vote_events:
            return {}

        # Basic voting metrics
        total_votes = len(vote_events)
        yes_votes = sum(1 for e in vote_events if e.vote_choice == 'yes')
        no_votes = sum(1 for e in vote_events if e.vote_choice == 'no')
        abstain_votes = sum(1 for e in vote_events if e.vote_choice == 'abstain')

        # Vote weights
        vote_weights = [e.vote_weight for e in vote_events if e.vote_weight > 0]
        avg_vote_weight = statistics.mean(vote_weights) if vote_weights else 0
        total_vote_weight = sum(vote_weights)

        # Voting consistency (tendency to vote the same way)
        yes_ratio = yes_votes / total_votes if total_votes > 0 else 0
        consistency_score = max(yes_ratio, 1 - yes_ratio)  # How consistent in direction

        # Participation in different proposal categories
        categories = defaultdict(int)
        for event in vote_events:
            if event.proposal_category:
                categories[event.proposal_category] += 1

        return {
            'total_votes_cast': total_votes,
            'yes_vote_ratio': yes_ratio,
            'no_vote_ratio': no_votes / total_votes if total_votes > 0 else 0,
            'abstain_ratio': abstain_votes / total_votes if total_votes > 0 else 0,
            'vote_consistency_score': consistency_score,
            'avg_vote_weight': avg_vote_weight,
            'total_vote_weight': total_vote_weight,
            'category_participation': dict(categories),
            'category_diversity': len(categories)
        }

    async def _analyze_proposal_activity(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Analyze proposal submission and quality"""
        proposal_events = [e for e in events if e.event_type == 'proposal']

        analysis = {
            'proposals_submitted': len(proposal_events),
            'proposal_categories': [],
            'proposal_quality_score': 0.0,
            'proposal_success_rate': 0.0
        }

        if proposal_events:
            # Analyze proposal categories
            categories = [e.proposal_category for e in proposal_events if e.proposal_category]
            analysis['proposal_categories'] = list(set(categories))

            # Mock quality score based on variety and number
            quality_score = min(len(proposal_events) * 20 + len(set(categories)) * 10, 100)
            analysis['proposal_quality_score'] = quality_score

            # Mock success rate
            analysis['proposal_success_rate'] = 0.75  # 75% success rate

        return analysis

    async def _analyze_delegation_behavior(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Analyze delegation patterns"""
        delegation_events = [e for e in events if e.event_type == 'delegation']

        analysis = {
            'delegation_events': len(delegation_events),
            'total_delegation_amount': 0.0,
            'avg_delegation_amount': 0.0,
            'delegation_consistency': 0.0
        }

        if delegation_events:
            amounts = [e.delegation_amount for e in delegation_events if e.delegation_amount > 0]
            analysis['total_delegation_amount'] = sum(amounts)
            analysis['avg_delegation_amount'] = statistics.mean(amounts) if amounts else 0

            # Consistency in delegation amounts
            if len(amounts) > 1:
                cv = statistics.stdev(amounts) / statistics.mean(amounts) if statistics.mean(amounts) > 0 else 1
                analysis['delegation_consistency'] = max(0, 1 - cv)

        return analysis

    async def _analyze_participation_consistency(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Analyze consistency of participation across governance periods"""
        # Group events by governance periods
        period_participation = defaultdict(list)

        for event in events:
            # Determine which governance period this event belongs to
            period = self._determine_governance_period(event.timestamp)
            period_participation[period].append(event)

        # Calculate participation metrics per period
        period_metrics = {}
        for period, period_events in period_participation.items():
            vote_count = sum(1 for e in period_events if e.event_type == 'vote')
            proposal_count = sum(1 for e in period_events if e.event_type == 'proposal')
            delegation_count = sum(1 for e in period_events if e.event_type == 'delegation')

            period_metrics[period] = {
                'votes': vote_count,
                'proposals': proposal_count,
                'delegations': delegation_count,
                'total_events': len(period_events)
            }

        # Calculate consistency scores
        periods_with_activity = len([p for p in period_metrics.values() if p['total_events'] > 0])
        total_periods = len(self.governance_periods)

        participation_rate = periods_with_activity / total_periods if total_periods > 0 else 0

        # Vote consistency across periods
        vote_counts = [p['votes'] for p in period_metrics.values()]
        vote_consistency = 1.0 - (statistics.stdev(vote_counts) / statistics.mean(vote_counts)) if vote_counts and statistics.mean(vote_counts) > 0 else 0

        return {
            'periods_participated': periods_with_activity,
            'total_governance_periods': total_periods,
            'participation_rate': participation_rate,
            'vote_consistency_across_periods': max(vote_consistency, 0),
            'period_metrics': period_metrics,
            'continuous_participation_months': self._calculate_continuous_participation(period_metrics)
        }

    async def _analyze_expertise_indicators(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Analyze indicators of governance expertise and understanding"""
        expertise_indicators = {
            'early_voter': False,
            'informed_voting': False,
            'category_expertise': [],
            'leadership_indicators': False,
            'expertise_score': 0.0
        }

        vote_events = [e for e in events if e.event_type == 'vote']
        proposal_events = [e for e in events if e.event_type == 'proposal']

        if vote_events:
            # Early voting behavior (votes within first 25% of voting period)
            # Mock implementation - would calculate based on actual voting periods
            early_votes = sum(1 for _ in vote_events if __import__('random').random() > 0.7)
            expertise_indicators['early_voter'] = early_votes / len(vote_events) > 0.3

            # Category expertise (consistent participation in specific categories)
            categories = defaultdict(int)
            for event in vote_events:
                if event.proposal_category:
                    categories[event.proposal_category] += 1

            # Identify categories with significant participation
            total_votes = len(vote_events)
            expertise_categories = [
                cat for cat, count in categories.items()
                if count / total_votes > 0.3  # >30% of votes in this category
            ]
            expertise_indicators['category_expertise'] = expertise_categories

        # Leadership indicators
        if proposal_events:
            expertise_indicators['leadership_indicators'] = True

        # Calculate overall expertise score
        expertise_score = 0
        if expertise_indicators['early_voter']:
            expertise_score += 25
        if expertise_indicators['leadership_indicators']:
            expertise_score += 30
        expertise_score += len(expertise_indicators['category_expertise']) * 15
        if len(vote_events) > 10:
            expertise_score += 20

        expertise_indicators['expertise_score'] = min(expertise_score, 100)

        return expertise_indicators

    async def _analyze_community_engagement(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Analyze broader community engagement beyond just voting"""
        engagement_metrics = {
            'engagement_breadth': 0.0,
            'consistent_participation': False,
            'community_contribution_score': 0.0,
            'influence_building': False
        }

        # Engagement breadth (variety of governance activities)
        event_types = set(e.event_type for e in events)
        engagement_metrics['engagement_breadth'] = len(event_types) / 3.0  # Normalize by max types

        # Consistent participation over time
        if events:
            time_span = (events[-1].timestamp - events[0].timestamp).days
            if time_span > 90:  # More than 3 months
                event_frequency = len(events) / (time_span / 30)  # Events per month
                engagement_metrics['consistent_participation'] = event_frequency > 0.5

        # Community contribution score
        contribution_score = 0
        vote_events = sum(1 for e in events if e.event_type == 'vote')
        proposal_events = sum(1 for e in events if e.event_type == 'proposal')
        delegation_events = sum(1 for e in events if e.event_type == 'delegation')

        contribution_score += min(vote_events * 2, 40)  # Max 40 points for voting
        contribution_score += min(proposal_events * 20, 40)  # Max 40 points for proposals
        contribution_score += min(delegation_events * 5, 20)  # Max 20 points for delegation

        engagement_metrics['community_contribution_score'] = contribution_score

        # Influence building (delegation received)
        delegation_events_received = [e for e in events if e.event_type == 'delegation' and e.delegation_amount > 1000]
        engagement_metrics['influence_building'] = len(delegation_events_received) > 0

        return engagement_metrics

    async def _detect_governance_gaming(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """Detect potential gaming or manipulation of governance"""
        gaming_indicators = {
            'vote_timing_manipulation': False,
            'proposal_spam': False,
            'delegation_gaming': False,
            'suspicious_patterns': [],
            'risk_score': 0.0
        }

        vote_events = [e for e in events if e.event_type == 'vote']
        proposal_events = [e for e in events if e.event_type == 'proposal']

        # Vote timing analysis (all votes at the same time could indicate gaming)
        if len(vote_events) > 5:
            vote_times = [e.timestamp for e in vote_events]
            time_diffs = [(vote_times[i] - vote_times[i-1]).total_seconds() for i in range(1, len(vote_times))]
            avg_time_diff = statistics.mean(time_diffs) if time_diffs else 0

            # If average time between votes is very small, might indicate gaming
            if avg_time_diff < 300:  # Less than 5 minutes between votes
                gaming_indicators['vote_timing_manipulation'] = True
                gaming_indicators['suspicious_patterns'].append('rapid_consecutive_voting')

        # Proposal spam detection
        if len(proposal_events) > 5:
            proposal_times = [e.timestamp for e in proposal_events]
            if len(proposal_times) > 1:
                time_span = (proposal_times[-1] - proposal_times[0]).days
                if time_span < 30:  # More than 5 proposals in 30 days
                    gaming_indicators['proposal_spam'] = True
                    gaming_indicators['suspicious_patterns'].append('proposal_spam')

        # Calculate risk score
        risk_score = 0
        if gaming_indicators['vote_timing_manipulation']:
            risk_score += 30
        if gaming_indicators['proposal_spam']:
            risk_score += 40
        if gaming_indicators['delegation_gaming']:
            risk_score += 25

        gaming_indicators['risk_score'] = min(risk_score, 100)

        return gaming_indicators

    def _determine_participation_type(
        self,
        voting_analysis: Dict,
        proposal_analysis: Dict,
        delegation_analysis: Dict
    ) -> ParticipationType:
        """Determine the primary type of governance participation"""
        votes_cast = voting_analysis.get('total_votes_cast', 0)
        proposals_submitted = proposal_analysis.get('proposals_submitted', 0)
        delegation_events = delegation_analysis.get('delegation_events', 0)
        total_delegation = delegation_analysis.get('total_delegation_amount', 0)

        # Determine primary participation type
        if proposals_submitted > 2:
            return ParticipationType.PROPOSER
        elif total_delegation > 10000:  # Significant delegation
            return ParticipationType.DELEGATOR
        elif votes_cast > 5:
            return ParticipationType.VOTER
        elif votes_cast > 0 or proposals_submitted > 0 or delegation_events > 0:
            return ParticipationType.VOTER
        else:
            return ParticipationType.NONE

    def _calculate_governance_metrics(
        self,
        voting_analysis: Dict,
        proposal_analysis: Dict,
        delegation_analysis: Dict,
        consistency_analysis: Dict,
        expertise_analysis: Dict,
        engagement_analysis: Dict
    ) -> GovernanceMetrics:
        """Calculate comprehensive governance metrics"""

        # Participation score (0-100)
        participation_score = 0
        participation_score += min(voting_analysis.get('total_votes_cast', 0) * 5, 50)
        participation_score += min(proposal_analysis.get('proposals_submitted', 0) * 15, 30)
        participation_score += min(delegation_analysis.get('delegation_events', 0) * 5, 20)

        # Consistency score
        consistency_score = (
            consistency_analysis.get('vote_consistency_across_periods', 0) * 0.4 +
            consistency_analysis.get('participation_rate', 0) * 0.6
        ) * 100

        # Influence score
        influence_score = 0
        if voting_analysis.get('total_vote_weight', 0) > 0:
            influence_score += min(voting_analysis.get('total_vote_weight', 0) / 1000, 50)
        influence_score += proposal_analysis.get('proposal_quality_score', 0) * 0.3
        if engagement_analysis.get('influence_building', False):
            influence_score += 20

        # Commitment score
        continuous_months = consistency_analysis.get('continuous_participation_months', 0)
        commitment_score = min(continuous_months / 12.0 * 100, 100)  # Normalize to 12 months

        # Community engagement score
        community_engagement_score = engagement_analysis.get('community_contribution_score', 0)

        # Expertise score
        expertise_score = expertise_analysis.get('expertise_score', 0)

        return GovernanceMetrics(
            participation_score=min(participation_score, 100),
            consistency_score=consistency_score,
            influence_score=min(influence_score, 100),
            commitment_score=commitment_score,
            community_engagement_score=min(community_engagement_score, 100),
            expertise_score=expertise_score
        )

    def _analyze_governance_periods(self, events: List[GovernanceEvent]) -> List[Dict[str, Any]]:
        """Analyze participation across different governance periods"""
        periods = []

        for i, period_info in enumerate(self.governance_periods):
            period_events = [
                e for e in events
                if period_info['start'] <= e.timestamp <= period_info['end']
            ]

            period_data = {
                'period_number': i + 1,
                'start_date': period_info['start'],
                'end_date': period_info['end'],
                'events_count': len(period_events),
                'votes_cast': sum(1 for e in period_events if e.event_type == 'vote'),
                'proposals_submitted': sum(1 for e in period_events if e.event_type == 'proposal'),
                'participated': len(period_events) > 0
            }
            periods.append(period_data)

        return periods

    def _compile_behavioral_patterns(
        self,
        voting_analysis: Dict,
        consistency_analysis: Dict,
        engagement_analysis: Dict
    ) -> Dict[str, Any]:
        """Compile governance behavioral patterns"""
        return {
            'voting_tendency': self._determine_voting_tendency(voting_analysis),
            'participation_pattern': self._determine_participation_pattern(consistency_analysis),
            'engagement_level': self._determine_engagement_level(engagement_analysis),
            'governance_maturity': self._assess_governance_maturity(
                voting_analysis, consistency_analysis, engagement_analysis
            )
        }

    def _compile_risk_indicators(self, gaming_analysis: Dict) -> Dict[str, Any]:
        """Compile governance-related risk indicators"""
        return {
            'gaming_risk_score': gaming_analysis.get('risk_score', 0),
            'suspicious_patterns': gaming_analysis.get('suspicious_patterns', []),
            'manipulation_indicators': {
                'vote_timing': gaming_analysis.get('vote_timing_manipulation', False),
                'proposal_spam': gaming_analysis.get('proposal_spam', False),
                'delegation_gaming': gaming_analysis.get('delegation_gaming', False)
            }
        }

    def _generate_recommendations(
        self,
        participation_type: ParticipationType,
        metrics: GovernanceMetrics,
        patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate governance improvement recommendations"""
        recommendations = []

        # Low participation
        if metrics.participation_score < 30:
            recommendations.append("Consider increasing governance participation to demonstrate commitment")

        # Low consistency
        if metrics.consistency_score < 50:
            recommendations.append("Improve consistency in governance participation across periods")

        # Limited engagement
        if metrics.community_engagement_score < 40:
            recommendations.append("Expand community engagement beyond basic voting")

        # No expertise development
        if metrics.expertise_score < 30:
            recommendations.append("Develop expertise in specific governance areas")

        # Specific recommendations by participation type
        if participation_type == ParticipationType.VOTER:
            if metrics.influence_score < 30:
                recommendations.append("Consider increasing vote weight or submitting proposals")
        elif participation_type == ParticipationType.NONE:
            recommendations.append("Begin participating in governance to demonstrate ecosystem commitment")

        return recommendations

    def _determine_governance_period(self, timestamp: datetime) -> int:
        """Determine which governance period a timestamp belongs to"""
        for i, period in enumerate(self.governance_periods):
            if period['start'] <= timestamp <= period['end']:
                return i + 1
        return 0  # No period found

    def _calculate_continuous_participation(self, period_metrics: Dict) -> int:
        """Calculate months of continuous participation"""
        # Find longest streak of consecutive periods with activity
        periods = sorted(period_metrics.keys())
        max_streak = 0
        current_streak = 0

        for period in periods:
            if period_metrics[period]['total_events'] > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak * 3  # Assume 3 months per period

    def _determine_voting_tendency(self, voting_analysis: Dict) -> str:
        """Determine overall voting tendency"""
        yes_ratio = voting_analysis.get('yes_vote_ratio', 0.5)
        consistency = voting_analysis.get('vote_consistency_score', 0)

        if consistency > 0.8:
            if yes_ratio > 0.7:
                return "consistently_supportive"
            elif yes_ratio < 0.3:
                return "consistently_conservative"
            else:
                return "consistently_moderate"
        else:
            return "variable_voting_pattern"

    def _determine_participation_pattern(self, consistency_analysis: Dict) -> str:
        """Determine participation pattern"""
        participation_rate = consistency_analysis.get('participation_rate', 0)

        if participation_rate > 0.8:
            return "highly_consistent"
        elif participation_rate > 0.5:
            return "moderately_consistent"
        elif participation_rate > 0.2:
            return "sporadic"
        else:
            return "minimal"

    def _determine_engagement_level(self, engagement_analysis: Dict) -> str:
        """Determine engagement level"""
        contribution_score = engagement_analysis.get('community_contribution_score', 0)

        if contribution_score > 80:
            return "highly_engaged"
        elif contribution_score > 50:
            return "moderately_engaged"
        elif contribution_score > 20:
            return "basic_engagement"
        else:
            return "minimal_engagement"

    def _assess_governance_maturity(
        self,
        voting_analysis: Dict,
        consistency_analysis: Dict,
        engagement_analysis: Dict
    ) -> str:
        """Assess overall governance maturity"""
        total_votes = voting_analysis.get('total_votes_cast', 0)
        participation_rate = consistency_analysis.get('participation_rate', 0)
        contribution_score = engagement_analysis.get('community_contribution_score', 0)

        maturity_score = (total_votes * 2) + (participation_rate * 50) + (contribution_score * 0.5)

        if maturity_score > 80:
            return "highly_mature"
        elif maturity_score > 50:
            return "mature"
        elif maturity_score > 25:
            return "developing"
        else:
            return "nascent"

    def _create_no_participation_result(self) -> GovernanceAnalysisResult:
        """Create result for addresses with no governance participation"""
        empty_metrics = GovernanceMetrics(
            participation_score=0.0,
            consistency_score=0.0,
            influence_score=0.0,
            commitment_score=0.0,
            community_engagement_score=0.0,
            expertise_score=0.0
        )

        return GovernanceAnalysisResult(
            participation_type=ParticipationType.NONE,
            participation_metrics=empty_metrics,
            governance_events=[],
            governance_periods=[],
            behavioral_patterns={
                'voting_tendency': 'no_participation',
                'participation_pattern': 'no_participation',
                'engagement_level': 'no_participation',
                'governance_maturity': 'no_participation'
            },
            risk_indicators={'gaming_risk_score': 0},
            recommendations=['Begin participating in governance to demonstrate ecosystem commitment']
        )

    def _load_governance_periods(self) -> List[Dict[str, datetime]]:
        """Load historical governance periods"""
        base_date = datetime.utcnow() - timedelta(days=720)  # 2 years ago

        return [
            {
                'start': base_date,
                'end': base_date + timedelta(days=90)
            },
            {
                'start': base_date + timedelta(days=120),
                'end': base_date + timedelta(days=210)
            },
            {
                'start': base_date + timedelta(days=240),
                'end': base_date + timedelta(days=330)
            },
            {
                'start': base_date + timedelta(days=360),
                'end': datetime.utcnow()
            }
        ]

    def _load_proposal_categories(self) -> List[str]:
        """Load known proposal categories"""
        return [
            'protocol_upgrade',
            'economic_parameters',
            'governance_process',
            'community_fund',
            'technical_improvement',
            'ecosystem_development',
            'partnership',
            'treasury_management'
        ]