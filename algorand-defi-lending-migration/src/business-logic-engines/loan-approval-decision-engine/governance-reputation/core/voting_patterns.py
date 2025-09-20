"""
Voting Patterns Analyzer

Analyzes voting consistency, proposal engagement, delegation patterns,
and decision-making quality for governance reputation assessment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class VoteType(Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    NO_VOTE = "no_vote"


class ProposalCategory(Enum):
    TECHNICAL = "technical"
    ECONOMIC = "economic"
    GOVERNANCE = "governance"
    COMMUNITY = "community"
    PROTOCOL = "protocol"


@dataclass
class Vote:
    """Individual vote record"""
    proposal_id: str
    vote_type: VoteType
    voting_power: float
    timestamp: datetime
    proposal_category: ProposalCategory
    reasoning_provided: bool
    reasoning_quality: float
    debate_participation: bool
    vote_timing_score: float  # Early/late voting pattern
    informed_decision_score: float


@dataclass
class VotingPattern:
    """Voting pattern analysis result"""
    address: str
    total_votes: int
    participation_rate: float
    consistency_score: float
    informed_voting_score: float
    debate_engagement_score: float
    timing_consistency_score: float
    category_expertise: Dict[ProposalCategory, float]
    voting_alignment_score: float
    independence_score: float
    quality_metrics: Dict[str, float]
    risk_indicators: List[str]
    strengths: List[str]
    analysis_period: Tuple[datetime, datetime]


class VotingPatternAnalyzer:
    """Analyzes voting patterns for governance reputation assessment"""

    def __init__(self, config_path: str = None):
        """Initialize voting pattern analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.voting_config = self.config['governance_scoring']['voting_quality']

    async def analyze_voting_patterns(self, address: str,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> VotingPattern:
        """
        Analyze comprehensive voting patterns for an address

        Args:
            address: Algorand address to analyze
            start_date: Analysis start date (default: 2 years ago)
            end_date: Analysis end date (default: now)

        Returns:
            VotingPattern with detailed analysis
        """
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            if start_date is None:
                start_date = end_date - timedelta(days=730)  # 2 years

            logger.info(f"Analyzing voting patterns for {address} from {start_date} to {end_date}")

            # Fetch voting data
            votes = await self._fetch_voting_data(address, start_date, end_date)
            proposal_data = await self._fetch_proposal_metadata(votes)

            # Calculate pattern metrics
            participation_rate = self._calculate_participation_rate(votes, proposal_data)
            consistency_score = self._calculate_consistency_score(votes)
            informed_voting_score = self._calculate_informed_voting_score(votes)
            debate_engagement_score = self._calculate_debate_engagement_score(votes)
            timing_consistency_score = self._calculate_timing_consistency_score(votes)
            category_expertise = self._analyze_category_expertise(votes)
            voting_alignment_score = self._calculate_voting_alignment_score(votes, proposal_data)
            independence_score = self._calculate_independence_score(votes, proposal_data)
            quality_metrics = self._calculate_quality_metrics(votes)

            # Identify patterns and risks
            risk_indicators = self._identify_voting_risks(votes, quality_metrics)
            strengths = self._identify_voting_strengths(votes, quality_metrics)

            return VotingPattern(
                address=address,
                total_votes=len(votes),
                participation_rate=participation_rate,
                consistency_score=consistency_score,
                informed_voting_score=informed_voting_score,
                debate_engagement_score=debate_engagement_score,
                timing_consistency_score=timing_consistency_score,
                category_expertise=category_expertise,
                voting_alignment_score=voting_alignment_score,
                independence_score=independence_score,
                quality_metrics=quality_metrics,
                risk_indicators=risk_indicators,
                strengths=strengths,
                analysis_period=(start_date, end_date)
            )

        except Exception as e:
            logger.error(f"Error analyzing voting patterns for {address}: {e}")
            raise

    async def _fetch_voting_data(self, address: str, start_date: datetime,
                               end_date: datetime) -> List[Vote]:
        """Fetch detailed voting data for the address"""
        try:
            # Simulate voting data - in production, use real API calls
            votes = [
                Vote(
                    proposal_id="prop_001",
                    vote_type=VoteType.YES,
                    voting_power=10000.0,
                    timestamp=datetime(2022, 1, 15),
                    proposal_category=ProposalCategory.TECHNICAL,
                    reasoning_provided=True,
                    reasoning_quality=0.85,
                    debate_participation=True,
                    vote_timing_score=0.9,  # Early voter
                    informed_decision_score=0.8
                ),
                Vote(
                    proposal_id="prop_002",
                    vote_type=VoteType.NO,
                    voting_power=10000.0,
                    timestamp=datetime(2022, 2, 1),
                    proposal_category=ProposalCategory.ECONOMIC,
                    reasoning_provided=True,
                    reasoning_quality=0.92,
                    debate_participation=False,
                    vote_timing_score=0.6,  # Late voter
                    informed_decision_score=0.9
                ),
                Vote(
                    proposal_id="prop_003",
                    vote_type=VoteType.ABSTAIN,
                    voting_power=12000.0,
                    timestamp=datetime(2022, 3, 10),
                    proposal_category=ProposalCategory.GOVERNANCE,
                    reasoning_provided=False,
                    reasoning_quality=0.0,
                    debate_participation=True,
                    vote_timing_score=0.8,
                    informed_decision_score=0.4
                ),
                Vote(
                    proposal_id="prop_004",
                    vote_type=VoteType.YES,
                    voting_power=12000.0,
                    timestamp=datetime(2022, 4, 5),
                    proposal_category=ProposalCategory.PROTOCOL,
                    reasoning_provided=True,
                    reasoning_quality=0.78,
                    debate_participation=True,
                    vote_timing_score=0.95,
                    informed_decision_score=0.85
                ),
                Vote(
                    proposal_id="prop_005",
                    vote_type=VoteType.YES,
                    voting_power=15000.0,
                    timestamp=datetime(2022, 5, 20),
                    proposal_category=ProposalCategory.COMMUNITY,
                    reasoning_provided=True,
                    reasoning_quality=0.88,
                    debate_participation=False,
                    vote_timing_score=0.7,
                    informed_decision_score=0.75
                )
            ]

            # Filter by date range
            filtered_votes = [
                vote for vote in votes
                if start_date <= vote.timestamp <= end_date
            ]

            return filtered_votes

        except Exception as e:
            logger.error(f"Error fetching voting data: {e}")
            return []

    async def _fetch_proposal_metadata(self, votes: List[Vote]) -> Dict[str, Any]:
        """Fetch metadata about proposals that were voted on"""
        try:
            # Simulate proposal metadata
            proposal_metadata = {
                "prop_001": {
                    "title": "Upgrade consensus mechanism",
                    "total_votes": 1500000,
                    "yes_votes": 1200000,
                    "no_votes": 250000,
                    "abstain_votes": 50000,
                    "controversy_score": 0.3,
                    "technical_complexity": 0.9,
                    "community_impact": 0.8
                },
                "prop_002": {
                    "title": "Adjust governance rewards",
                    "total_votes": 1800000,
                    "yes_votes": 800000,
                    "no_votes": 900000,
                    "abstain_votes": 100000,
                    "controversy_score": 0.8,
                    "technical_complexity": 0.4,
                    "community_impact": 0.9
                },
                "prop_003": {
                    "title": "Update voting procedures",
                    "total_votes": 1300000,
                    "yes_votes": 1000000,
                    "no_votes": 200000,
                    "abstain_votes": 100000,
                    "controversy_score": 0.4,
                    "technical_complexity": 0.6,
                    "community_impact": 0.7
                },
                "prop_004": {
                    "title": "Protocol parameter adjustment",
                    "total_votes": 1600000,
                    "yes_votes": 1300000,
                    "no_votes": 250000,
                    "abstain_votes": 50000,
                    "controversy_score": 0.2,
                    "technical_complexity": 0.8,
                    "community_impact": 0.6
                },
                "prop_005": {
                    "title": "Community fund allocation",
                    "total_votes": 1400000,
                    "yes_votes": 1100000,
                    "no_votes": 200000,
                    "abstain_votes": 100000,
                    "controversy_score": 0.3,
                    "technical_complexity": 0.3,
                    "community_impact": 0.95
                }
            }

            return proposal_metadata

        except Exception as e:
            logger.error(f"Error fetching proposal metadata: {e}")
            return {}

    def _calculate_participation_rate(self, votes: List[Vote],
                                    proposal_data: Dict[str, Any]) -> float:
        """Calculate overall voting participation rate"""
        try:
            if not proposal_data:
                return 0.0

            total_proposals = len(proposal_data)
            actual_votes = len([v for v in votes if v.vote_type != VoteType.NO_VOTE])

            return actual_votes / total_proposals if total_proposals > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating participation rate: {e}")
            return 0.0

    def _calculate_consistency_score(self, votes: List[Vote]) -> float:
        """Calculate voting consistency across similar proposals"""
        try:
            if len(votes) < 2:
                return 1.0

            # Group votes by category
            category_votes = defaultdict(list)
            for vote in votes:
                category_votes[vote.proposal_category].append(vote)

            consistency_scores = []

            for category, category_vote_list in category_votes.items():
                if len(category_vote_list) < 2:
                    continue

                # Calculate consistency within each category
                vote_types = [v.vote_type for v in category_vote_list]
                unique_votes = len(set(vote_types))
                total_votes = len(vote_types)

                # Higher consistency = fewer different vote types
                category_consistency = 1.0 - (unique_votes - 1) / max(total_votes - 1, 1)
                consistency_scores.append(category_consistency)

            return np.mean(consistency_scores) if consistency_scores else 1.0

        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.0

    def _calculate_informed_voting_score(self, votes: List[Vote]) -> float:
        """Calculate score based on evidence of informed decision-making"""
        try:
            if not votes:
                return 0.0

            # Weight factors for informed voting
            reasoning_scores = [v.reasoning_quality for v in votes if v.reasoning_provided]
            informed_scores = [v.informed_decision_score for v in votes]

            # Calculate weighted average
            reasoning_weight = 0.6
            informed_weight = 0.4

            avg_reasoning = np.mean(reasoning_scores) if reasoning_scores else 0.0
            avg_informed = np.mean(informed_scores) if informed_scores else 0.0

            # Apply reasoning provided rate
            reasoning_rate = len(reasoning_scores) / len(votes)

            final_score = (
                (avg_reasoning * reasoning_weight * reasoning_rate) +
                (avg_informed * informed_weight)
            )

            return min(1.0, final_score)

        except Exception as e:
            logger.error(f"Error calculating informed voting score: {e}")
            return 0.0

    def _calculate_debate_engagement_score(self, votes: List[Vote]) -> float:
        """Calculate engagement in governance debates and discussions"""
        try:
            if not votes:
                return 0.0

            debate_participants = sum(1 for v in votes if v.debate_participation)
            debate_rate = debate_participants / len(votes)

            # Bonus for high-quality reasoning when participating in debates
            debate_votes = [v for v in votes if v.debate_participation]
            quality_bonus = 0.0

            if debate_votes:
                avg_quality = np.mean([v.reasoning_quality for v in debate_votes])
                quality_bonus = avg_quality * 0.2

            return min(1.0, debate_rate + quality_bonus)

        except Exception as e:
            logger.error(f"Error calculating debate engagement score: {e}")
            return 0.0

    def _calculate_timing_consistency_score(self, votes: List[Vote]) -> float:
        """Calculate consistency in voting timing patterns"""
        try:
            if not votes:
                return 0.0

            timing_scores = [v.vote_timing_score for v in votes]

            # Reward consistency in timing patterns
            avg_timing = np.mean(timing_scores)
            timing_variance = np.var(timing_scores)

            # Lower variance indicates more consistent timing
            consistency_bonus = max(0, 1.0 - timing_variance)

            return min(1.0, avg_timing * 0.7 + consistency_bonus * 0.3)

        except Exception as e:
            logger.error(f"Error calculating timing consistency score: {e}")
            return 0.0

    def _analyze_category_expertise(self, votes: List[Vote]) -> Dict[ProposalCategory, float]:
        """Analyze expertise and performance across different proposal categories"""
        try:
            category_expertise = {}

            for category in ProposalCategory:
                category_votes = [v for v in votes if v.proposal_category == category]

                if not category_votes:
                    category_expertise[category] = 0.0
                    continue

                # Calculate expertise metrics for this category
                avg_reasoning_quality = np.mean([v.reasoning_quality for v in category_votes])
                avg_informed_score = np.mean([v.informed_decision_score for v in category_votes])
                debate_participation_rate = sum(1 for v in category_votes if v.debate_participation) / len(category_votes)

                # Combine metrics
                expertise_score = (
                    avg_reasoning_quality * 0.4 +
                    avg_informed_score * 0.4 +
                    debate_participation_rate * 0.2
                )

                category_expertise[category] = min(1.0, expertise_score)

            return category_expertise

        except Exception as e:
            logger.error(f"Error analyzing category expertise: {e}")
            return {category: 0.0 for category in ProposalCategory}

    def _calculate_voting_alignment_score(self, votes: List[Vote],
                                        proposal_data: Dict[str, Any]) -> float:
        """Calculate how well votes align with eventual outcomes"""
        try:
            if not votes or not proposal_data:
                return 0.5  # Neutral score

            alignment_scores = []

            for vote in votes:
                proposal_meta = proposal_data.get(vote.proposal_id, {})
                if not proposal_meta:
                    continue

                total_votes = proposal_meta.get('total_votes', 1)
                yes_votes = proposal_meta.get('yes_votes', 0)
                no_votes = proposal_meta.get('no_votes', 0)

                # Determine majority outcome
                if yes_votes > no_votes:
                    majority_outcome = VoteType.YES
                    majority_strength = yes_votes / total_votes
                else:
                    majority_outcome = VoteType.NO
                    majority_strength = no_votes / total_votes

                # Score alignment with majority
                if vote.vote_type == majority_outcome:
                    alignment_scores.append(majority_strength)
                elif vote.vote_type == VoteType.ABSTAIN:
                    alignment_scores.append(0.5)  # Neutral for abstain
                else:
                    alignment_scores.append(1.0 - majority_strength)

            return np.mean(alignment_scores) if alignment_scores else 0.5

        except Exception as e:
            logger.error(f"Error calculating voting alignment score: {e}")
            return 0.5

    def _calculate_independence_score(self, votes: List[Vote],
                                    proposal_data: Dict[str, Any]) -> float:
        """Calculate independence in decision-making (not just following the crowd)"""
        try:
            if not votes or not proposal_data:
                return 0.5

            independence_indicators = []

            for vote in votes:
                proposal_meta = proposal_data.get(vote.proposal_id, {})
                if not proposal_meta:
                    continue

                controversy_score = proposal_meta.get('controversy_score', 0.5)

                # Higher independence score for thoughtful votes on controversial proposals
                if vote.reasoning_provided and controversy_score > 0.6:
                    independence_indicators.append(vote.reasoning_quality * controversy_score)
                elif vote.vote_type == VoteType.ABSTAIN and controversy_score > 0.7:
                    # Thoughtful abstention on highly controversial topics
                    independence_indicators.append(0.7)
                else:
                    independence_indicators.append(0.5)

            return np.mean(independence_indicators) if independence_indicators else 0.5

        except Exception as e:
            logger.error(f"Error calculating independence score: {e}")
            return 0.5

    def _calculate_quality_metrics(self, votes: List[Vote]) -> Dict[str, float]:
        """Calculate comprehensive quality metrics"""
        try:
            if not votes:
                return {}

            metrics = {
                'average_reasoning_quality': np.mean([v.reasoning_quality for v in votes if v.reasoning_provided]),
                'reasoning_provided_rate': sum(1 for v in votes if v.reasoning_provided) / len(votes),
                'debate_participation_rate': sum(1 for v in votes if v.debate_participation) / len(votes),
                'average_timing_score': np.mean([v.vote_timing_score for v in votes]),
                'average_informed_score': np.mean([v.informed_decision_score for v in votes]),
                'vote_diversity': len(set(v.vote_type for v in votes)) / len(VoteType),
                'category_coverage': len(set(v.proposal_category for v in votes)) / len(ProposalCategory)
            }

            # Handle NaN values
            for key, value in metrics.items():
                if np.isnan(value):
                    metrics[key] = 0.0

            return metrics

        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {}

    def _identify_voting_risks(self, votes: List[Vote],
                             quality_metrics: Dict[str, float]) -> List[str]:
        """Identify potential risks in voting patterns"""
        risks = []

        try:
            if not votes:
                risks.append("No voting history available")
                return risks

            # Check for low participation indicators
            if quality_metrics.get('reasoning_provided_rate', 0) < 0.3:
                risks.append("Low rate of providing reasoning for votes")

            if quality_metrics.get('debate_participation_rate', 0) < 0.2:
                risks.append("Minimal participation in governance debates")

            if quality_metrics.get('average_informed_score', 0) < 0.5:
                risks.append("Evidence suggests uninformed voting decisions")

            # Check for concerning patterns
            if quality_metrics.get('vote_diversity', 0) < 0.3:
                risks.append("Very limited vote type diversity - may indicate bias")

            if quality_metrics.get('category_coverage', 0) < 0.4:
                risks.append("Limited engagement across proposal categories")

            # Check for timing issues
            if quality_metrics.get('average_timing_score', 0) < 0.3:
                risks.append("Consistently late voting may indicate disengagement")

            # Check for recent activity
            recent_votes = [v for v in votes if v.timestamp > datetime.utcnow() - timedelta(days=180)]
            if len(recent_votes) < len(votes) * 0.3:
                risks.append("Declining recent voting activity")

        except Exception as e:
            logger.error(f"Error identifying voting risks: {e}")

        return risks

    def _identify_voting_strengths(self, votes: List[Vote],
                                 quality_metrics: Dict[str, float]) -> List[str]:
        """Identify strengths in voting patterns"""
        strengths = []

        try:
            if not votes:
                return strengths

            # Check for high-quality participation
            if quality_metrics.get('reasoning_provided_rate', 0) > 0.8:
                strengths.append("Consistently provides reasoning for votes")

            if quality_metrics.get('average_reasoning_quality', 0) > 0.8:
                strengths.append("High-quality vote reasoning and analysis")

            if quality_metrics.get('debate_participation_rate', 0) > 0.6:
                strengths.append("Active participant in governance debates")

            if quality_metrics.get('average_informed_score', 0) > 0.8:
                strengths.append("Evidence of well-informed decision making")

            # Check for good patterns
            if quality_metrics.get('category_coverage', 0) > 0.7:
                strengths.append("Engaged across diverse proposal categories")

            if quality_metrics.get('average_timing_score', 0) > 0.8:
                strengths.append("Consistent and timely voting participation")

            # Check for expertise
            reasoning_quality = quality_metrics.get('average_reasoning_quality', 0)
            debate_rate = quality_metrics.get('debate_participation_rate', 0)
            if reasoning_quality > 0.85 and debate_rate > 0.7:
                strengths.append("Demonstrates governance thought leadership")

        except Exception as e:
            logger.error(f"Error identifying voting strengths: {e}")

        return strengths