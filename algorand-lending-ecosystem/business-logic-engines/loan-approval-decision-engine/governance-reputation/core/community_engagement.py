"""
Community Engagement Analyzer

Analyzes forum participation, development contributions, ecosystem building,
and social engagement for comprehensive community reputation assessment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class EngagementType(Enum):
    FORUM_POST = "forum_post"
    FORUM_REPLY = "forum_reply"
    CODE_CONTRIBUTION = "code_contribution"
    BUG_REPORT = "bug_report"
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    SOCIAL_MEDIA = "social_media"
    EVENT_PARTICIPATION = "event_participation"
    MENTORING = "mentoring"
    MODERATION = "moderation"


class ContentQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


@dataclass
class EngagementActivity:
    """Individual community engagement activity"""
    activity_id: str
    engagement_type: EngagementType
    platform: str
    title: str
    content_summary: str
    timestamp: datetime
    quality_score: float
    helpfulness_score: float
    community_impact_score: float
    upvotes: int
    downvotes: int
    replies: int
    views: int
    technical_depth: float
    educational_value: float


@dataclass
class CommunityEngagementProfile:
    """Comprehensive community engagement analysis"""
    address: str
    overall_engagement_score: float
    forum_participation_score: float
    development_contribution_score: float
    community_building_score: float
    ecosystem_advocacy_score: float
    total_activities: int
    activity_consistency_score: float
    content_quality_average: float
    community_impact_score: float
    leadership_indicators: List[str]
    expertise_areas: List[str]
    engagement_trends: Dict[str, float]
    risk_factors: List[str]
    recommendations: List[str]
    analysis_period: Tuple[datetime, datetime]


class CommunityEngagementAnalyzer:
    """Analyzes community engagement for governance reputation"""

    def __init__(self, config_path: str = None):
        """Initialize community engagement analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.engagement_config = self.config['community_engagement']
        self.data_sources = self.config['data_sources']

    async def analyze_community_engagement(self, address: str,
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> CommunityEngagementProfile:
        """
        Analyze comprehensive community engagement for an address

        Args:
            address: Algorand address to analyze
            start_date: Analysis start date (default: 1 year ago)
            end_date: Analysis end date (default: now)

        Returns:
            CommunityEngagementProfile with detailed engagement analysis
        """
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            if start_date is None:
                start_date = end_date - timedelta(days=365)  # 1 year

            logger.info(f"Analyzing community engagement for {address} from {start_date} to {end_date}")

            # Gather engagement data from multiple sources
            forum_activities = await self._fetch_forum_activities(address, start_date, end_date)
            development_activities = await self._fetch_development_activities(address, start_date, end_date)
            social_activities = await self._fetch_social_activities(address, start_date, end_date)
            event_activities = await self._fetch_event_activities(address, start_date, end_date)

            all_activities = forum_activities + development_activities + social_activities + event_activities

            # Calculate engagement scores
            forum_score = self._calculate_forum_participation_score(forum_activities)
            development_score = self._calculate_development_contribution_score(development_activities)
            community_building_score = self._calculate_community_building_score(all_activities)
            advocacy_score = self._calculate_ecosystem_advocacy_score(social_activities, event_activities)

            # Calculate overall metrics
            overall_score = self._calculate_overall_engagement_score(
                forum_score, development_score, community_building_score, advocacy_score
            )
            consistency_score = self._calculate_activity_consistency_score(all_activities)
            content_quality = self._calculate_average_content_quality(all_activities)
            community_impact = self._calculate_community_impact_score(all_activities)

            # Analyze patterns and trends
            leadership_indicators = self._identify_leadership_indicators(all_activities)
            expertise_areas = self._identify_expertise_areas(all_activities)
            engagement_trends = self._analyze_engagement_trends(all_activities)
            risk_factors = self._identify_engagement_risks(all_activities)
            recommendations = self._generate_engagement_recommendations(
                forum_score, development_score, community_building_score, advocacy_score
            )

            return CommunityEngagementProfile(
                address=address,
                overall_engagement_score=overall_score,
                forum_participation_score=forum_score,
                development_contribution_score=development_score,
                community_building_score=community_building_score,
                ecosystem_advocacy_score=advocacy_score,
                total_activities=len(all_activities),
                activity_consistency_score=consistency_score,
                content_quality_average=content_quality,
                community_impact_score=community_impact,
                leadership_indicators=leadership_indicators,
                expertise_areas=expertise_areas,
                engagement_trends=engagement_trends,
                risk_factors=risk_factors,
                recommendations=recommendations,
                analysis_period=(start_date, end_date)
            )

        except Exception as e:
            logger.error(f"Error analyzing community engagement for {address}: {e}")
            raise

    async def _fetch_forum_activities(self, address: str, start_date: datetime,
                                    end_date: datetime) -> List[EngagementActivity]:
        """Fetch forum participation activities"""
        try:
            # Simulate forum activities data
            activities = [
                EngagementActivity(
                    activity_id="forum_001",
                    engagement_type=EngagementType.FORUM_POST,
                    platform="algorand_forum",
                    title="Best practices for DeFi smart contracts",
                    content_summary="Detailed guide on security considerations for DeFi protocols",
                    timestamp=datetime(2022, 1, 15),
                    quality_score=0.92,
                    helpfulness_score=0.88,
                    community_impact_score=0.85,
                    upvotes=45,
                    downvotes=2,
                    replies=23,
                    views=1200,
                    technical_depth=0.9,
                    educational_value=0.95
                ),
                EngagementActivity(
                    activity_id="forum_002",
                    engagement_type=EngagementType.FORUM_REPLY,
                    platform="algorand_forum",
                    title="Help with PyTeal implementation",
                    content_summary="Provided solution to complex smart contract issue",
                    timestamp=datetime(2022, 2, 3),
                    quality_score=0.87,
                    helpfulness_score=0.95,
                    community_impact_score=0.78,
                    upvotes=32,
                    downvotes=0,
                    replies=8,
                    views=450,
                    technical_depth=0.85,
                    educational_value=0.8
                ),
                EngagementActivity(
                    activity_id="forum_003",
                    engagement_type=EngagementType.FORUM_POST,
                    platform="algorand_forum",
                    title="Algorand consensus mechanism explanation",
                    content_summary="Educational post explaining Pure Proof of Stake",
                    timestamp=datetime(2022, 3, 20),
                    quality_score=0.94,
                    helpfulness_score=0.91,
                    community_impact_score=0.88,
                    upvotes=67,
                    downvotes=1,
                    replies=34,
                    views=2100,
                    technical_depth=0.88,
                    educational_value=0.97
                )
            ]

            return [a for a in activities if start_date <= a.timestamp <= end_date]

        except Exception as e:
            logger.error(f"Error fetching forum activities: {e}")
            return []

    async def _fetch_development_activities(self, address: str, start_date: datetime,
                                          end_date: datetime) -> List[EngagementActivity]:
        """Fetch development contribution activities"""
        try:
            # Simulate development activities
            activities = [
                EngagementActivity(
                    activity_id="dev_001",
                    engagement_type=EngagementType.CODE_CONTRIBUTION,
                    platform="github",
                    title="Add multi-signature support to SDK",
                    content_summary="Implemented multi-sig functionality with comprehensive tests",
                    timestamp=datetime(2022, 1, 25),
                    quality_score=0.89,
                    helpfulness_score=0.85,
                    community_impact_score=0.92,
                    upvotes=0,  # GitHub doesn't have upvotes
                    downvotes=0,
                    replies=12,  # Comments/reviews
                    views=0,
                    technical_depth=0.95,
                    educational_value=0.7
                ),
                EngagementActivity(
                    activity_id="dev_002",
                    engagement_type=EngagementType.BUG_REPORT,
                    platform="github",
                    title="Memory leak in transaction batching",
                    content_summary="Detailed bug report with reproduction steps and proposed fix",
                    timestamp=datetime(2022, 2, 18),
                    quality_score=0.91,
                    helpfulness_score=0.95,
                    community_impact_score=0.88,
                    upvotes=0,
                    downvotes=0,
                    replies=8,
                    views=0,
                    technical_depth=0.87,
                    educational_value=0.75
                ),
                EngagementActivity(
                    activity_id="dev_003",
                    engagement_type=EngagementType.DOCUMENTATION,
                    platform="github",
                    title="Updated API documentation for new features",
                    content_summary="Comprehensive documentation update with examples",
                    timestamp=datetime(2022, 4, 5),
                    quality_score=0.88,
                    helpfulness_score=0.92,
                    community_impact_score=0.85,
                    upvotes=0,
                    downvotes=0,
                    replies=5,
                    views=0,
                    technical_depth=0.75,
                    educational_value=0.95
                )
            ]

            return [a for a in activities if start_date <= a.timestamp <= end_date]

        except Exception as e:
            logger.error(f"Error fetching development activities: {e}")
            return []

    async def _fetch_social_activities(self, address: str, start_date: datetime,
                                     end_date: datetime) -> List[EngagementActivity]:
        """Fetch social media and advocacy activities"""
        try:
            # Simulate social activities
            activities = [
                EngagementActivity(
                    activity_id="social_001",
                    engagement_type=EngagementType.SOCIAL_MEDIA,
                    platform="twitter",
                    title="Thread on Algorand's environmental benefits",
                    content_summary="Educational Twitter thread about carbon-negative blockchain",
                    timestamp=datetime(2022, 2, 10),
                    quality_score=0.83,
                    helpfulness_score=0.78,
                    community_impact_score=0.89,
                    upvotes=145,  # Likes
                    downvotes=3,
                    replies=32,  # Comments
                    views=5600,
                    technical_depth=0.6,
                    educational_value=0.85
                ),
                EngagementActivity(
                    activity_id="social_002",
                    engagement_type=EngagementType.SOCIAL_MEDIA,
                    platform="reddit",
                    title="AMA responses about DeFi development",
                    content_summary="Answered community questions about building on Algorand",
                    timestamp=datetime(2022, 3, 15),
                    quality_score=0.86,
                    helpfulness_score=0.91,
                    community_impact_score=0.84,
                    upvotes=89,
                    downvotes=4,
                    replies=67,
                    views=3200,
                    technical_depth=0.8,
                    educational_value=0.88
                )
            ]

            return [a for a in activities if start_date <= a.timestamp <= end_date]

        except Exception as e:
            logger.error(f"Error fetching social activities: {e}")
            return []

    async def _fetch_event_activities(self, address: str, start_date: datetime,
                                    end_date: datetime) -> List[EngagementActivity]:
        """Fetch event participation and community building activities"""
        try:
            # Simulate event activities
            activities = [
                EngagementActivity(
                    activity_id="event_001",
                    engagement_type=EngagementType.EVENT_PARTICIPATION,
                    platform="conference",
                    title="Speaker at Algorand Developer Conference",
                    content_summary="Presented workshop on smart contract optimization",
                    timestamp=datetime(2022, 1, 30),
                    quality_score=0.92,
                    helpfulness_score=0.89,
                    community_impact_score=0.95,
                    upvotes=0,
                    downvotes=0,
                    replies=0,
                    views=450,  # Attendees
                    technical_depth=0.9,
                    educational_value=0.95
                ),
                EngagementActivity(
                    activity_id="event_002",
                    engagement_type=EngagementType.MENTORING,
                    platform="discord",
                    title="Mentoring session for new developers",
                    content_summary="Guided 15 new developers through first smart contract deployment",
                    timestamp=datetime(2022, 3, 8),
                    quality_score=0.87,
                    helpfulness_score=0.95,
                    community_impact_score=0.91,
                    upvotes=0,
                    downvotes=0,
                    replies=0,
                    views=15,  # Mentees
                    technical_depth=0.85,
                    educational_value=0.98
                )
            ]

            return [a for a in activities if start_date <= a.timestamp <= end_date]

        except Exception as e:
            logger.error(f"Error fetching event activities: {e}")
            return []

    def _calculate_forum_participation_score(self, forum_activities: List[EngagementActivity]) -> float:
        """Calculate forum participation score"""
        try:
            if not forum_activities:
                return 0.0

            config = self.engagement_config['forum_participation']

            # Calculate component scores
            post_quality = sum(a.quality_score for a in forum_activities) / len(forum_activities)
            helpfulness = sum(a.helpfulness_score for a in forum_activities) / len(forum_activities)

            # Calculate engagement metrics
            total_upvotes = sum(a.upvotes for a in forum_activities)
            total_replies = sum(a.replies for a in forum_activities)
            total_views = sum(a.views for a in forum_activities)

            # Normalize engagement metrics
            engagement_score = min(1.0, (total_upvotes * 0.3 + total_replies * 0.4 + total_views * 0.0001) / len(forum_activities))

            # Apply config weights
            weighted_score = (
                post_quality * config['weight'] * 100 +
                helpfulness * config['helpful_responses'] * 100 +
                engagement_score * 30  # Engagement bonus
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating forum participation score: {e}")
            return 0.0

    def _calculate_development_contribution_score(self, dev_activities: List[EngagementActivity]) -> float:
        """Calculate development contribution score"""
        try:
            if not dev_activities:
                return 0.0

            config = self.engagement_config['development_contributions']

            # Categorize activities
            code_contributions = [a for a in dev_activities if a.engagement_type == EngagementType.CODE_CONTRIBUTION]
            bug_reports = [a for a in dev_activities if a.engagement_type == EngagementType.BUG_REPORT]
            documentation = [a for a in dev_activities if a.engagement_type == EngagementType.DOCUMENTATION]

            # Calculate scores for each category
            code_score = 0.0
            if code_contributions:
                code_score = sum(a.quality_score * a.technical_depth for a in code_contributions) / len(code_contributions) * 100

            bug_score = 0.0
            if bug_reports:
                bug_score = sum(a.helpfulness_score for a in bug_reports) / len(bug_reports) * 100

            docs_score = 0.0
            if documentation:
                docs_score = sum(a.educational_value for a in documentation) / len(documentation) * 100

            # Apply config weights
            weighted_score = (
                code_score * config['code_contributions'] +
                bug_score * config['bug_reports'] +
                docs_score * 0.15  # Documentation weight
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating development contribution score: {e}")
            return 0.0

    def _calculate_community_building_score(self, all_activities: List[EngagementActivity]) -> float:
        """Calculate community building and leadership score"""
        try:
            if not all_activities:
                return 0.0

            config = self.engagement_config['community_building']

            # Identify community building activities
            mentoring_activities = [a for a in all_activities if a.engagement_type == EngagementType.MENTORING]
            event_activities = [a for a in all_activities if a.engagement_type == EngagementType.EVENT_PARTICIPATION]
            educational_activities = [a for a in all_activities if a.educational_value > 0.8]

            # Calculate scores
            mentoring_score = 0.0
            if mentoring_activities:
                mentoring_score = sum(a.community_impact_score for a in mentoring_activities) / len(mentoring_activities) * 100

            event_score = 0.0
            if event_activities:
                event_score = sum(a.community_impact_score for a in event_activities) / len(event_activities) * 100

            educational_score = 0.0
            if educational_activities:
                educational_score = sum(a.educational_value for a in educational_activities) / len(educational_activities) * 100

            # Apply config weights
            weighted_score = (
                mentoring_score * config['mentoring_activity'] +
                educational_score * config['educational_content'] +
                event_score * config['event_participation']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating community building score: {e}")
            return 0.0

    def _calculate_ecosystem_advocacy_score(self, social_activities: List[EngagementActivity],
                                          event_activities: List[EngagementActivity]) -> float:
        """Calculate ecosystem advocacy and promotion score"""
        try:
            config = self.engagement_config['ecosystem_advocacy']

            social_score = 0.0
            if social_activities:
                # Calculate reach and engagement
                total_reach = sum(a.views for a in social_activities)
                avg_quality = sum(a.quality_score for a in social_activities) / len(social_activities)
                social_score = min(100.0, (total_reach * 0.001 + avg_quality * 50))

            event_score = 0.0
            if event_activities:
                avg_impact = sum(a.community_impact_score for a in event_activities) / len(event_activities)
                event_score = avg_impact * 100

            # Apply config weights
            weighted_score = (
                social_score * config['social_promotion'] +
                event_score * config['ambassador_activities']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating ecosystem advocacy score: {e}")
            return 0.0

    def _calculate_overall_engagement_score(self, forum_score: float, development_score: float,
                                          community_building_score: float, advocacy_score: float) -> float:
        """Calculate overall community engagement score"""
        try:
            weights = self.engagement_config

            weighted_score = (
                forum_score * weights['forum_participation']['weight'] +
                development_score * weights['development_contributions']['weight'] +
                community_building_score * weights['community_building']['weight'] +
                advocacy_score * weights['ecosystem_advocacy']['weight']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating overall engagement score: {e}")
            return 0.0

    def _calculate_activity_consistency_score(self, activities: List[EngagementActivity]) -> float:
        """Calculate consistency of community engagement over time"""
        try:
            if len(activities) < 2:
                return 0.0

            # Group activities by month
            monthly_activity = {}
            for activity in activities:
                month_key = activity.timestamp.strftime("%Y-%m")
                monthly_activity[month_key] = monthly_activity.get(month_key, 0) + 1

            if not monthly_activity:
                return 0.0

            # Calculate consistency (lower variance = higher consistency)
            activity_counts = list(monthly_activity.values())
            mean_activity = sum(activity_counts) / len(activity_counts)
            variance = sum((count - mean_activity) ** 2 for count in activity_counts) / len(activity_counts)

            # Normalize consistency score
            consistency = max(0.0, 1.0 - (variance / (mean_activity + 1)))

            return consistency * 100

        except Exception as e:
            logger.error(f"Error calculating activity consistency score: {e}")
            return 0.0

    def _calculate_average_content_quality(self, activities: List[EngagementActivity]) -> float:
        """Calculate average content quality across all activities"""
        try:
            if not activities:
                return 0.0

            total_quality = sum(a.quality_score for a in activities)
            return (total_quality / len(activities)) * 100

        except Exception as e:
            logger.error(f"Error calculating average content quality: {e}")
            return 0.0

    def _calculate_community_impact_score(self, activities: List[EngagementActivity]) -> float:
        """Calculate overall community impact score"""
        try:
            if not activities:
                return 0.0

            total_impact = sum(a.community_impact_score for a in activities)
            return (total_impact / len(activities)) * 100

        except Exception as e:
            logger.error(f"Error calculating community impact score: {e}")
            return 0.0

    def _identify_leadership_indicators(self, activities: List[EngagementActivity]) -> List[str]:
        """Identify indicators of community leadership"""
        indicators = []

        try:
            # Check for mentoring activities
            mentoring_count = sum(1 for a in activities if a.engagement_type == EngagementType.MENTORING)
            if mentoring_count > 0:
                indicators.append(f"Active mentor ({mentoring_count} mentoring sessions)")

            # Check for speaking/teaching
            event_count = sum(1 for a in activities if a.engagement_type == EngagementType.EVENT_PARTICIPATION)
            if event_count > 0:
                indicators.append(f"Community speaker ({event_count} events)")

            # Check for high-impact content
            high_impact_content = [a for a in activities if a.community_impact_score > 0.85]
            if len(high_impact_content) > 3:
                indicators.append("Consistent high-impact content creator")

            # Check for technical contributions
            code_contributions = [a for a in activities if a.engagement_type == EngagementType.CODE_CONTRIBUTION]
            if len(code_contributions) > 2:
                indicators.append("Active code contributor")

            # Check for educational content
            educational_content = [a for a in activities if a.educational_value > 0.9]
            if len(educational_content) > 2:
                indicators.append("Educator and knowledge sharer")

        except Exception as e:
            logger.error(f"Error identifying leadership indicators: {e}")

        return indicators

    def _identify_expertise_areas(self, activities: List[EngagementActivity]) -> List[str]:
        """Identify areas of technical and community expertise"""
        expertise_areas = []

        try:
            # Analyze content for technical depth
            technical_activities = [a for a in activities if a.technical_depth > 0.8]
            if len(technical_activities) > 2:
                expertise_areas.append("Technical expert")

            # Check for smart contract expertise
            smart_contract_keywords = ["smart contract", "pyteal", "reach", "teal"]
            smart_contract_activities = [
                a for a in activities
                if any(keyword in a.content_summary.lower() for keyword in smart_contract_keywords)
            ]
            if len(smart_contract_activities) > 1:
                expertise_areas.append("Smart contract development")

            # Check for DeFi expertise
            defi_keywords = ["defi", "dex", "amm", "liquidity", "yield"]
            defi_activities = [
                a for a in activities
                if any(keyword in a.content_summary.lower() for keyword in defi_keywords)
            ]
            if len(defi_activities) > 1:
                expertise_areas.append("DeFi protocols")

            # Check for consensus/governance expertise
            consensus_keywords = ["consensus", "governance", "voting", "proposals"]
            consensus_activities = [
                a for a in activities
                if any(keyword in a.content_summary.lower() for keyword in consensus_keywords)
            ]
            if len(consensus_activities) > 1:
                expertise_areas.append("Governance and consensus")

            # Check for developer education
            education_activities = [a for a in activities if a.educational_value > 0.85]
            if len(education_activities) > 3:
                expertise_areas.append("Developer education")

        except Exception as e:
            logger.error(f"Error identifying expertise areas: {e}")

        return expertise_areas

    def _analyze_engagement_trends(self, activities: List[EngagementActivity]) -> Dict[str, float]:
        """Analyze trends in engagement over time"""
        trends = {}

        try:
            if len(activities) < 3:
                return {"insufficient_data": 1.0}

            # Sort activities by timestamp
            sorted_activities = sorted(activities, key=lambda a: a.timestamp)

            # Split into first and second half
            mid_point = len(sorted_activities) // 2
            first_half = sorted_activities[:mid_point]
            second_half = sorted_activities[mid_point:]

            # Calculate average scores for each half
            first_quality = sum(a.quality_score for a in first_half) / len(first_half)
            second_quality = sum(a.quality_score for a in second_half) / len(second_half)

            first_impact = sum(a.community_impact_score for a in first_half) / len(first_half)
            second_impact = sum(a.community_impact_score for a in second_half) / len(second_half)

            # Calculate trends
            trends["quality_trend"] = (second_quality - first_quality) / first_quality if first_quality > 0 else 0
            trends["impact_trend"] = (second_impact - first_impact) / first_impact if first_impact > 0 else 0
            trends["activity_frequency_trend"] = len(second_half) / len(first_half) - 1

        except Exception as e:
            logger.error(f"Error analyzing engagement trends: {e}")

        return trends

    def _identify_engagement_risks(self, activities: List[EngagementActivity]) -> List[str]:
        """Identify potential risks in community engagement"""
        risks = []

        try:
            if not activities:
                risks.append("No community engagement activity found")
                return risks

            # Check for declining activity
            if len(activities) > 5:
                recent_activities = [a for a in activities if a.timestamp > datetime.utcnow() - timedelta(days=90)]
                if len(recent_activities) < len(activities) * 0.3:
                    risks.append("Declining recent engagement activity")

            # Check for low quality content
            low_quality_activities = [a for a in activities if a.quality_score < 0.5]
            if len(low_quality_activities) > len(activities) * 0.3:
                risks.append("High proportion of low-quality content")

            # Check for limited community impact
            low_impact_activities = [a for a in activities if a.community_impact_score < 0.4]
            if len(low_impact_activities) > len(activities) * 0.5:
                risks.append("Limited community impact from engagement")

            # Check for narrow engagement
            engagement_types = set(a.engagement_type for a in activities)
            if len(engagement_types) < 2:
                risks.append("Very narrow community engagement scope")

            # Check for lack of technical depth
            technical_activities = [a for a in activities if a.technical_depth > 0.6]
            if len(technical_activities) < len(activities) * 0.3:
                risks.append("Limited technical depth in community contributions")

        except Exception as e:
            logger.error(f"Error identifying engagement risks: {e}")

        return risks

    def _generate_engagement_recommendations(self, forum_score: float, development_score: float,
                                           community_building_score: float, advocacy_score: float) -> List[str]:
        """Generate recommendations for improving community engagement"""
        recommendations = []

        try:
            if forum_score < 50:
                recommendations.append("Increase forum participation with helpful, high-quality posts")

            if development_score < 40:
                recommendations.append("Consider contributing to open-source projects or reporting bugs")

            if community_building_score < 30:
                recommendations.append("Engage in mentoring or educational content creation")

            if advocacy_score < 25:
                recommendations.append("Share knowledge about Algorand on social media or at events")

            # Positive reinforcement for strong areas
            if forum_score > 80 and development_score > 70:
                recommendations.append("Excellent technical community engagement - consider becoming a community moderator")

            if community_building_score > 80:
                recommendations.append("Strong community leadership - consider formal ambassador role")

        except Exception as e:
            logger.error(f"Error generating engagement recommendations: {e}")

        return recommendations