"""
Ecosystem Health Monitor

Real-time monitoring of Algorand ecosystem health including TVL changes,
protocol growth/decline, adoption metrics, and overall ecosystem vitality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import numpy as np
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    CRITICAL = "critical"
    CONCERNING = "concerning"
    MODERATE = "moderate"
    GOOD = "good"
    EXCELLENT = "excellent"


class TrendDirection(Enum):
    STRONG_DECLINE = "strong_decline"
    DECLINE = "decline"
    STABLE = "stable"
    GROWTH = "growth"
    STRONG_GROWTH = "strong_growth"


@dataclass
class ProtocolMetrics:
    """Individual protocol health metrics"""
    protocol_name: str
    tvl_usd: float
    daily_volume_usd: float
    active_users_24h: int
    transaction_count_24h: int
    tvl_change_24h: float
    tvl_change_7d: float
    tvl_change_30d: float
    health_score: float
    trend_direction: TrendDirection
    last_updated: datetime


@dataclass
class EcosystemMetrics:
    """Overall ecosystem health metrics"""
    total_tvl_usd: float
    total_daily_volume_usd: float
    total_active_protocols: int
    new_protocols_30d: int
    total_transactions_24h: int
    total_active_users_24h: int
    average_tps: float
    network_utilization: float
    developer_activity_score: float
    governance_participation_rate: float


@dataclass
class HealthAlert:
    """Health monitoring alert"""
    alert_id: str
    severity: str
    alert_type: str
    message: str
    affected_protocols: List[str]
    metric_values: Dict[str, float]
    timestamp: datetime
    resolved: bool = False


@dataclass
class EcosystemHealthReport:
    """Comprehensive ecosystem health report"""
    overall_health_score: float
    health_status: HealthStatus
    ecosystem_metrics: EcosystemMetrics
    protocol_metrics: List[ProtocolMetrics]
    health_trends: Dict[str, float]
    risk_factors: List[str]
    positive_indicators: List[str]
    active_alerts: List[HealthAlert]
    recommendations: List[str]
    analysis_timestamp: datetime


class EcosystemHealthMonitor:
    """Monitors real-time Algorand ecosystem health"""

    def __init__(self, config_path: str = None):
        """Initialize ecosystem health monitor"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.health_config = self.config['ecosystem_health']
        self.data_sources = self.config['data_sources']
        self.session = None
        self.historical_data = {}  # Cache for trend analysis

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def assess_ecosystem_health(self) -> EcosystemHealthReport:
        """
        Perform comprehensive ecosystem health assessment

        Returns:
            EcosystemHealthReport with detailed health analysis
        """
        try:
            logger.info("Starting ecosystem health assessment")

            # Gather health data from multiple sources
            ecosystem_metrics = await self._fetch_ecosystem_metrics()
            protocol_metrics = await self._fetch_protocol_metrics()
            developer_activity = await self._fetch_developer_activity()
            governance_health = await self._fetch_governance_health()

            # Calculate component health scores
            tvl_health_score = self._calculate_tvl_health_score(ecosystem_metrics, protocol_metrics)
            growth_health_score = self._calculate_growth_health_score(protocol_metrics)
            activity_health_score = self._calculate_activity_health_score(ecosystem_metrics)
            dev_health_score = self._calculate_developer_health_score(developer_activity)
            governance_health_score = self._calculate_governance_health_score(governance_health)
            security_health_score = self._calculate_security_health_score()

            # Calculate overall health score
            overall_score = self._calculate_overall_health_score(
                tvl_health_score, growth_health_score, activity_health_score,
                dev_health_score, governance_health_score, security_health_score
            )

            # Determine health status
            health_status = self._determine_health_status(overall_score)

            # Analyze trends and patterns
            health_trends = self._analyze_health_trends(ecosystem_metrics, protocol_metrics)
            risk_factors = self._identify_risk_factors(ecosystem_metrics, protocol_metrics)
            positive_indicators = self._identify_positive_indicators(ecosystem_metrics, protocol_metrics)

            # Check for active alerts
            active_alerts = await self._check_health_alerts(ecosystem_metrics, protocol_metrics)

            # Generate recommendations
            recommendations = self._generate_health_recommendations(
                overall_score, risk_factors, health_trends
            )

            return EcosystemHealthReport(
                overall_health_score=overall_score,
                health_status=health_status,
                ecosystem_metrics=ecosystem_metrics,
                protocol_metrics=protocol_metrics,
                health_trends=health_trends,
                risk_factors=risk_factors,
                positive_indicators=positive_indicators,
                active_alerts=active_alerts,
                recommendations=recommendations,
                analysis_timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error assessing ecosystem health: {e}")
            raise

    async def _fetch_ecosystem_metrics(self) -> EcosystemMetrics:
        """Fetch overall ecosystem metrics"""
        try:
            # Simulate ecosystem metrics - in production, use real API calls
            ecosystem_metrics = EcosystemMetrics(
                total_tvl_usd=2850000000.0,  # $2.85B total TVL
                total_daily_volume_usd=125000000.0,  # $125M daily volume
                total_active_protocols=45,
                new_protocols_30d=3,
                total_transactions_24h=1250000,
                total_active_users_24h=15600,
                average_tps=890.5,
                network_utilization=0.68,
                developer_activity_score=78.5,
                governance_participation_rate=0.72
            )

            return ecosystem_metrics

        except Exception as e:
            logger.error(f"Error fetching ecosystem metrics: {e}")
            return EcosystemMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    async def _fetch_protocol_metrics(self) -> List[ProtocolMetrics]:
        """Fetch individual protocol metrics"""
        try:
            # Simulate protocol metrics data
            protocols = [
                ProtocolMetrics(
                    protocol_name="Tinyman",
                    tvl_usd=825000000.0,
                    daily_volume_usd=45000000.0,
                    active_users_24h=4500,
                    transaction_count_24h=125000,
                    tvl_change_24h=0.02,
                    tvl_change_7d=0.08,
                    tvl_change_30d=0.15,
                    health_score=85.5,
                    trend_direction=TrendDirection.GROWTH,
                    last_updated=datetime.utcnow()
                ),
                ProtocolMetrics(
                    protocol_name="Folks Finance",
                    tvl_usd=560000000.0,
                    daily_volume_usd=28000000.0,
                    active_users_24h=2800,
                    transaction_count_24h=89000,
                    tvl_change_24h=-0.01,
                    tvl_change_7d=0.03,
                    tvl_change_30d=0.12,
                    health_score=82.3,
                    trend_direction=TrendDirection.STABLE,
                    last_updated=datetime.utcnow()
                ),
                ProtocolMetrics(
                    protocol_name="AlgoFi",
                    tvl_usd=390000000.0,
                    daily_volume_usd=18000000.0,
                    active_users_24h=1950,
                    transaction_count_24h=67000,
                    tvl_change_24h=-0.03,
                    tvl_change_7d=-0.08,
                    tvl_change_30d=-0.15,
                    health_score=65.8,
                    trend_direction=TrendDirection.DECLINE,
                    last_updated=datetime.utcnow()
                ),
                ProtocolMetrics(
                    protocol_name="Pact",
                    tvl_usd=185000000.0,
                    daily_volume_usd=12000000.0,
                    active_users_24h=1200,
                    transaction_count_24h=45000,
                    tvl_change_24h=0.05,
                    tvl_change_7d=0.12,
                    tvl_change_30d=0.35,
                    health_score=88.2,
                    trend_direction=TrendDirection.STRONG_GROWTH,
                    last_updated=datetime.utcnow()
                ),
                ProtocolMetrics(
                    protocol_name="Humble DeFi",
                    tvl_usd=95000000.0,
                    daily_volume_usd=5000000.0,
                    active_users_24h=680,
                    transaction_count_24h=23000,
                    tvl_change_24h=0.01,
                    tvl_change_7d=0.04,
                    tvl_change_30d=0.18,
                    health_score=76.9,
                    trend_direction=TrendDirection.GROWTH,
                    last_updated=datetime.utcnow()
                )
            ]

            return protocols

        except Exception as e:
            logger.error(f"Error fetching protocol metrics: {e}")
            return []

    async def _fetch_developer_activity(self) -> Dict[str, Any]:
        """Fetch developer activity metrics"""
        try:
            # Simulate developer activity data
            dev_activity = {
                "github_commits_30d": 1250,
                "active_repositories": 89,
                "new_repositories_30d": 12,
                "pull_requests_30d": 567,
                "issues_opened_30d": 234,
                "issues_closed_30d": 298,
                "active_developers_30d": 145,
                "bounty_programs_active": 8,
                "grants_awarded_30d": 3,
                "hackathon_projects_30d": 23
            }

            return dev_activity

        except Exception as e:
            logger.error(f"Error fetching developer activity: {e}")
            return {}

    async def _fetch_governance_health(self) -> Dict[str, Any]:
        """Fetch governance health metrics"""
        try:
            # Simulate governance health data
            governance_health = {
                "current_period_participation": 0.72,
                "average_participation_3_periods": 0.68,
                "active_governors": 25600,
                "proposals_active": 3,
                "proposals_passed_30d": 2,
                "proposals_rejected_30d": 1,
                "voting_power_distribution_gini": 0.45,  # Gini coefficient
                "delegate_participation_rate": 0.89
            }

            return governance_health

        except Exception as e:
            logger.error(f"Error fetching governance health: {e}")
            return {}

    def _calculate_tvl_health_score(self, ecosystem_metrics: EcosystemMetrics,
                                   protocol_metrics: List[ProtocolMetrics]) -> float:
        """Calculate TVL stability and health score"""
        try:
            config = self.health_config['health_metrics']

            # Analyze TVL stability across protocols
            tvl_changes_24h = [p.tvl_change_24h for p in protocol_metrics]
            tvl_changes_7d = [p.tvl_change_7d for p in protocol_metrics]

            # Calculate stability score
            volatility_24h = np.std(tvl_changes_24h) if tvl_changes_24h else 0
            volatility_7d = np.std(tvl_changes_7d) if tvl_changes_7d else 0

            # Lower volatility = higher stability score
            stability_score = max(0, 100 - (volatility_24h * 1000 + volatility_7d * 500))

            # Growth score
            avg_growth_24h = np.mean(tvl_changes_24h) if tvl_changes_24h else 0
            growth_score = min(100, max(0, 50 + (avg_growth_24h * 1000)))

            # Combined TVL health score
            tvl_score = (stability_score * 0.6 + growth_score * 0.4)

            return min(100.0, tvl_score)

        except Exception as e:
            logger.error(f"Error calculating TVL health score: {e}")
            return 0.0

    def _calculate_growth_health_score(self, protocol_metrics: List[ProtocolMetrics]) -> float:
        """Calculate protocol growth and adoption health score"""
        try:
            if not protocol_metrics:
                return 0.0

            # Analyze growth trends
            growing_protocols = sum(1 for p in protocol_metrics if p.tvl_change_30d > 0)
            total_protocols = len(protocol_metrics)

            growth_ratio = growing_protocols / total_protocols

            # Calculate average growth rate
            avg_growth_30d = np.mean([p.tvl_change_30d for p in protocol_metrics])

            # Score based on growth ratio and average growth
            growth_score = (growth_ratio * 60) + min(40, max(0, avg_growth_30d * 200))

            return min(100.0, growth_score)

        except Exception as e:
            logger.error(f"Error calculating growth health score: {e}")
            return 0.0

    def _calculate_activity_health_score(self, ecosystem_metrics: EcosystemMetrics) -> float:
        """Calculate network activity and usage health score"""
        try:
            # Base activity score from TPS and utilization
            tps_score = min(100, (ecosystem_metrics.average_tps / 1000) * 100)
            utilization_score = ecosystem_metrics.network_utilization * 100

            # Transaction volume relative to TVL
            volume_to_tvl_ratio = ecosystem_metrics.total_daily_volume_usd / max(ecosystem_metrics.total_tvl_usd, 1)
            volume_score = min(100, volume_to_tvl_ratio * 2000)  # Scale factor

            # User activity score
            user_activity_score = min(100, (ecosystem_metrics.total_active_users_24h / 20000) * 100)

            # Combined activity score
            activity_score = (
                tps_score * 0.25 +
                utilization_score * 0.25 +
                volume_score * 0.25 +
                user_activity_score * 0.25
            )

            return min(100.0, activity_score)

        except Exception as e:
            logger.error(f"Error calculating activity health score: {e}")
            return 0.0

    def _calculate_developer_health_score(self, developer_activity: Dict[str, Any]) -> float:
        """Calculate developer activity health score"""
        try:
            if not developer_activity:
                return 0.0

            # Commit activity score
            commits = developer_activity.get('github_commits_30d', 0)
            commit_score = min(100, (commits / 1000) * 100)

            # Repository activity score
            new_repos = developer_activity.get('new_repositories_30d', 0)
            repo_score = min(100, new_repos * 8)

            # Developer engagement score
            active_devs = developer_activity.get('active_developers_30d', 0)
            dev_score = min(100, (active_devs / 150) * 100)

            # Bounty and grant activity
            bounties = developer_activity.get('bounty_programs_active', 0)
            grants = developer_activity.get('grants_awarded_30d', 0)
            incentive_score = min(100, (bounties * 8 + grants * 15))

            # Combined developer health score
            dev_health_score = (
                commit_score * 0.3 +
                repo_score * 0.2 +
                dev_score * 0.3 +
                incentive_score * 0.2
            )

            return min(100.0, dev_health_score)

        except Exception as e:
            logger.error(f"Error calculating developer health score: {e}")
            return 0.0

    def _calculate_governance_health_score(self, governance_health: Dict[str, Any]) -> float:
        """Calculate governance health score"""
        try:
            if not governance_health:
                return 0.0

            # Participation score
            participation = governance_health.get('current_period_participation', 0)
            participation_score = participation * 100

            # Proposal activity score
            proposals_active = governance_health.get('proposals_active', 0)
            proposals_passed = governance_health.get('proposals_passed_30d', 0)
            proposal_score = min(100, (proposals_active * 20 + proposals_passed * 15))

            # Distribution score (lower Gini = better distribution)
            gini = governance_health.get('voting_power_distribution_gini', 0.5)
            distribution_score = max(0, (1 - gini) * 100)

            # Delegate participation
            delegate_participation = governance_health.get('delegate_participation_rate', 0)
            delegate_score = delegate_participation * 100

            # Combined governance health score
            governance_score = (
                participation_score * 0.4 +
                proposal_score * 0.2 +
                distribution_score * 0.2 +
                delegate_score * 0.2
            )

            return min(100.0, governance_score)

        except Exception as e:
            logger.error(f"Error calculating governance health score: {e}")
            return 0.0

    def _calculate_security_health_score(self) -> float:
        """Calculate security health score based on recent incidents"""
        try:
            # Simplified security scoring - in production, would analyze actual incidents
            # Assume no major security incidents recently
            base_security_score = 85.0

            # Deduct points for any recent security issues
            # This would be calculated from real security incident data
            recent_incidents = 0  # Placeholder
            incident_penalty = recent_incidents * 15

            security_score = max(0, base_security_score - incident_penalty)

            return min(100.0, security_score)

        except Exception as e:
            logger.error(f"Error calculating security health score: {e}")
            return 0.0

    def _calculate_overall_health_score(self, tvl_score: float, growth_score: float,
                                       activity_score: float, dev_score: float,
                                       governance_score: float, security_score: float) -> float:
        """Calculate overall ecosystem health score"""
        try:
            weights = self.health_config['health_metrics']

            overall_score = (
                tvl_score * weights['tvl_stability'] +
                growth_score * weights['protocol_growth'] +
                activity_score * weights['transaction_volume'] +
                dev_score * weights['developer_activity'] +
                governance_score * weights['governance_health'] +
                security_score * weights['security_incidents']
            )

            return min(100.0, overall_score)

        except Exception as e:
            logger.error(f"Error calculating overall health score: {e}")
            return 0.0

    def _determine_health_status(self, health_score: float) -> HealthStatus:
        """Determine health status based on score"""
        try:
            thresholds = self.health_config['health_thresholds']

            if health_score >= thresholds['excellent']:
                return HealthStatus.EXCELLENT
            elif health_score >= thresholds['good']:
                return HealthStatus.GOOD
            elif health_score >= thresholds['moderate']:
                return HealthStatus.MODERATE
            elif health_score >= thresholds['concerning']:
                return HealthStatus.CONCERNING
            else:
                return HealthStatus.CRITICAL

        except Exception as e:
            logger.error(f"Error determining health status: {e}")
            return HealthStatus.CRITICAL

    def _analyze_health_trends(self, ecosystem_metrics: EcosystemMetrics,
                              protocol_metrics: List[ProtocolMetrics]) -> Dict[str, float]:
        """Analyze health trends over time"""
        try:
            trends = {}

            # TVL trend analysis
            if protocol_metrics:
                avg_tvl_change_7d = np.mean([p.tvl_change_7d for p in protocol_metrics])
                avg_tvl_change_30d = np.mean([p.tvl_change_30d for p in protocol_metrics])
                trends['tvl_trend_7d'] = avg_tvl_change_7d
                trends['tvl_trend_30d'] = avg_tvl_change_30d

            # Activity trends (would be calculated from historical data)
            trends['activity_trend'] = 0.05  # Placeholder positive trend
            trends['developer_trend'] = 0.08  # Placeholder positive trend
            trends['governance_trend'] = -0.02  # Placeholder slight decline

            return trends

        except Exception as e:
            logger.error(f"Error analyzing health trends: {e}")
            return {}

    def _identify_risk_factors(self, ecosystem_metrics: EcosystemMetrics,
                              protocol_metrics: List[ProtocolMetrics]) -> List[str]:
        """Identify ecosystem health risk factors"""
        risks = []

        try:
            # TVL concentration risk
            if protocol_metrics:
                sorted_protocols = sorted(protocol_metrics, key=lambda p: p.tvl_usd, reverse=True)
                top_3_tvl = sum(p.tvl_usd for p in sorted_protocols[:3])
                concentration_ratio = top_3_tvl / ecosystem_metrics.total_tvl_usd

                if concentration_ratio > 0.7:
                    risks.append("High TVL concentration in top 3 protocols")

            # Declining protocols
            declining_protocols = [p for p in protocol_metrics if p.tvl_change_30d < -0.1]
            if len(declining_protocols) > len(protocol_metrics) * 0.3:
                risks.append("Multiple protocols showing significant decline")

            # Low network utilization
            if ecosystem_metrics.network_utilization < 0.5:
                risks.append("Low network utilization indicates reduced activity")

            # Governance participation
            if ecosystem_metrics.governance_participation_rate < 0.6:
                risks.append("Below-average governance participation")

            # Developer activity
            if ecosystem_metrics.developer_activity_score < 60:
                risks.append("Declining developer activity and momentum")

        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")

        return risks

    def _identify_positive_indicators(self, ecosystem_metrics: EcosystemMetrics,
                                     protocol_metrics: List[ProtocolMetrics]) -> List[str]:
        """Identify positive ecosystem health indicators"""
        indicators = []

        try:
            # Growing protocols
            growing_protocols = [p for p in protocol_metrics if p.tvl_change_30d > 0.1]
            if growing_protocols:
                indicators.append(f"{len(growing_protocols)} protocols showing strong growth")

            # High network activity
            if ecosystem_metrics.average_tps > 800:
                indicators.append("High transaction throughput indicates strong usage")

            # Strong governance participation
            if ecosystem_metrics.governance_participation_rate > 0.7:
                indicators.append("Strong governance participation")

            # Developer momentum
            if ecosystem_metrics.developer_activity_score > 75:
                indicators.append("Strong developer activity and ecosystem growth")

            # Protocol diversity
            if ecosystem_metrics.total_active_protocols > 40:
                indicators.append("Diverse protocol ecosystem with strong activity")

            # TVL growth
            if protocol_metrics:
                total_tvl_change = np.mean([p.tvl_change_30d for p in protocol_metrics])
                if total_tvl_change > 0.05:
                    indicators.append("Positive TVL growth across ecosystem")

        except Exception as e:
            logger.error(f"Error identifying positive indicators: {e}")

        return indicators

    async def _check_health_alerts(self, ecosystem_metrics: EcosystemMetrics,
                                  protocol_metrics: List[ProtocolMetrics]) -> List[HealthAlert]:
        """Check for health-related alerts"""
        alerts = []

        try:
            # TVL crash alerts
            critical_tvl_drops = [p for p in protocol_metrics if p.tvl_change_24h < -0.2]
            if critical_tvl_drops:
                alerts.append(HealthAlert(
                    alert_id=f"tvl_crash_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    severity="critical",
                    alert_type="tvl_crash",
                    message=f"{len(critical_tvl_drops)} protocols experiencing significant TVL drops",
                    affected_protocols=[p.protocol_name for p in critical_tvl_drops],
                    metric_values={p.protocol_name: p.tvl_change_24h for p in critical_tvl_drops},
                    timestamp=datetime.utcnow()
                ))

            # Network congestion alerts
            if ecosystem_metrics.average_tps < 200:
                alerts.append(HealthAlert(
                    alert_id=f"congestion_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    severity="warning",
                    alert_type="network_congestion",
                    message="Network experiencing low throughput",
                    affected_protocols=[],
                    metric_values={"tps": ecosystem_metrics.average_tps},
                    timestamp=datetime.utcnow()
                ))

            # Governance participation alerts
            if ecosystem_metrics.governance_participation_rate < 0.5:
                alerts.append(HealthAlert(
                    alert_id=f"governance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    severity="warning",
                    alert_type="governance_decline",
                    message="Governance participation below healthy threshold",
                    affected_protocols=[],
                    metric_values={"participation_rate": ecosystem_metrics.governance_participation_rate},
                    timestamp=datetime.utcnow()
                ))

        except Exception as e:
            logger.error(f"Error checking health alerts: {e}")

        return alerts

    def _generate_health_recommendations(self, health_score: float, risk_factors: List[str],
                                        health_trends: Dict[str, float]) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        try:
            if health_score < 50:
                recommendations.append("Ecosystem health is concerning - monitor closely for loan decisions")

            if "High TVL concentration" in str(risk_factors):
                recommendations.append("Diversify lending across protocols to reduce concentration risk")

            if "declining protocols" in str(risk_factors).lower():
                recommendations.append("Avoid lending to users heavily invested in declining protocols")

            if health_trends.get('tvl_trend_7d', 0) < -0.05:
                recommendations.append("Recent TVL decline suggests increased market risk")

            if health_score > 80:
                recommendations.append("Strong ecosystem health supports favorable lending conditions")

        except Exception as e:
            logger.error(f"Error generating health recommendations: {e}")

        return recommendations