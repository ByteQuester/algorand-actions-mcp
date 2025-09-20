"""
Consensus Participation Analyzer

Analyzes node operation, relay participation, and network security contributions
for comprehensive consensus engagement assessment.
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


class NodeType(Enum):
    PARTICIPATION_NODE = "participation_node"
    RELAY_NODE = "relay_node"
    ARCHIVAL_NODE = "archival_node"
    INDEXER_NODE = "indexer_node"


class ParticipationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OFFLINE = "offline"
    SUSPENDED = "suspended"


@dataclass
class NodeRecord:
    """Individual node operation record"""
    node_id: str
    node_type: NodeType
    address: str
    status: ParticipationStatus
    uptime_percentage: float
    blocks_proposed: int
    votes_cast: int
    stake_amount: float
    first_online: datetime
    last_online: datetime
    performance_metrics: Dict[str, float]
    security_score: float
    network_contribution_score: float


@dataclass
class ConsensusMetrics:
    """Consensus participation metrics"""
    total_stake: float
    online_stake_percentage: float
    consensus_participation_rate: float
    block_proposal_efficiency: float
    voting_consistency: float
    network_uptime: float
    performance_reliability: float


@dataclass
class ConsensusParticipationProfile:
    """Comprehensive consensus participation analysis"""
    address: str
    overall_consensus_score: float
    node_operation_score: float
    relay_participation_score: float
    security_contribution_score: float
    total_nodes_operated: int
    active_nodes: int
    total_stake_committed: float
    average_uptime: float
    consensus_metrics: ConsensusMetrics
    network_contributions: List[str]
    security_activities: List[str]
    reliability_indicators: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    analysis_period: Tuple[datetime, datetime]


class ConsensusParticipationAnalyzer:
    """Analyzes consensus participation for governance reputation"""

    def __init__(self, config_path: str = None):
        """Initialize consensus participation analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.consensus_config = self.config['consensus_participation']
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

    async def analyze_consensus_participation(self, address: str,
                                            start_date: Optional[datetime] = None,
                                            end_date: Optional[datetime] = None) -> ConsensusParticipationProfile:
        """
        Analyze comprehensive consensus participation for an address

        Args:
            address: Algorand address to analyze
            start_date: Analysis start date (default: 1 year ago)
            end_date: Analysis end date (default: now)

        Returns:
            ConsensusParticipationProfile with detailed participation analysis
        """
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            if start_date is None:
                start_date = end_date - timedelta(days=365)  # 1 year

            logger.info(f"Analyzing consensus participation for {address} from {start_date} to {end_date}")

            # Fetch consensus participation data
            node_records = await self._fetch_node_records(address, start_date, end_date)
            participation_data = await self._fetch_participation_data(address, start_date, end_date)
            security_activities = await self._fetch_security_activities(address, start_date, end_date)

            # Calculate participation scores
            node_operation_score = self._calculate_node_operation_score(node_records)
            relay_participation_score = self._calculate_relay_participation_score(node_records)
            security_contribution_score = self._calculate_security_contribution_score(security_activities)

            # Calculate overall consensus score
            overall_score = self._calculate_overall_consensus_score(
                node_operation_score, relay_participation_score, security_contribution_score
            )

            # Calculate consensus metrics
            consensus_metrics = self._calculate_consensus_metrics(node_records, participation_data)

            # Analyze contributions and activities
            network_contributions = self._identify_network_contributions(node_records, participation_data)
            security_activities_list = self._identify_security_activities(security_activities)
            reliability_indicators = self._identify_reliability_indicators(node_records)
            risk_factors = self._identify_consensus_risks(node_records, participation_data)
            recommendations = self._generate_consensus_recommendations(
                node_operation_score, relay_participation_score, security_contribution_score
            )

            # Calculate aggregate metrics
            total_nodes = len(node_records)
            active_nodes = len([n for n in node_records if n.status == ParticipationStatus.ACTIVE])
            total_stake = sum(n.stake_amount for n in node_records)
            avg_uptime = sum(n.uptime_percentage for n in node_records) / max(total_nodes, 1)

            return ConsensusParticipationProfile(
                address=address,
                overall_consensus_score=overall_score,
                node_operation_score=node_operation_score,
                relay_participation_score=relay_participation_score,
                security_contribution_score=security_contribution_score,
                total_nodes_operated=total_nodes,
                active_nodes=active_nodes,
                total_stake_committed=total_stake,
                average_uptime=avg_uptime,
                consensus_metrics=consensus_metrics,
                network_contributions=network_contributions,
                security_activities=security_activities_list,
                reliability_indicators=reliability_indicators,
                risk_factors=risk_factors,
                recommendations=recommendations,
                analysis_period=(start_date, end_date)
            )

        except Exception as e:
            logger.error(f"Error analyzing consensus participation for {address}: {e}")
            raise

    async def _fetch_node_records(self, address: str, start_date: datetime,
                                end_date: datetime) -> List[NodeRecord]:
        """Fetch node operation records for the address"""
        try:
            # Simulate node records data - in production, use real API calls
            node_records = [
                NodeRecord(
                    node_id="node_001",
                    node_type=NodeType.PARTICIPATION_NODE,
                    address=address,
                    status=ParticipationStatus.ACTIVE,
                    uptime_percentage=98.5,
                    blocks_proposed=245,
                    votes_cast=15680,
                    stake_amount=50000.0,
                    first_online=datetime(2021, 6, 1),
                    last_online=datetime.utcnow(),
                    performance_metrics={
                        "average_response_time": 0.045,
                        "sync_efficiency": 0.97,
                        "memory_usage": 0.65,
                        "cpu_efficiency": 0.88
                    },
                    security_score=0.92,
                    network_contribution_score=0.89
                ),
                NodeRecord(
                    node_id="relay_001",
                    node_type=NodeType.RELAY_NODE,
                    address=address,
                    status=ParticipationStatus.ACTIVE,
                    uptime_percentage=99.2,
                    blocks_proposed=0,  # Relay nodes don't propose blocks
                    votes_cast=0,       # Relay nodes don't vote
                    stake_amount=0.0,   # Relay nodes don't stake
                    first_online=datetime(2021, 8, 15),
                    last_online=datetime.utcnow(),
                    performance_metrics={
                        "bandwidth_provided": 0.95,
                        "connection_stability": 0.98,
                        "geographic_coverage": 0.85,
                        "latency_optimization": 0.91
                    },
                    security_score=0.94,
                    network_contribution_score=0.93
                )
            ]

            return node_records

        except Exception as e:
            logger.error(f"Error fetching node records: {e}")
            return []

    async def _fetch_participation_data(self, address: str, start_date: datetime,
                                      end_date: datetime) -> Dict[str, Any]:
        """Fetch detailed participation data from Algorand APIs"""
        try:
            # Simulate participation data
            participation_data = {
                "total_participation_periods": 8,
                "active_periods": 7,
                "participation_rate": 0.875,
                "average_stake_per_period": 45000.0,
                "consensus_participation_history": [
                    {
                        "period": "2022-Q1",
                        "stake_amount": 40000.0,
                        "uptime": 0.985,
                        "blocks_proposed": 52,
                        "votes_cast": 3456,
                        "performance_score": 0.92
                    },
                    {
                        "period": "2022-Q2",
                        "stake_amount": 45000.0,
                        "uptime": 0.988,
                        "blocks_proposed": 67,
                        "votes_cast": 4123,
                        "performance_score": 0.94
                    },
                    {
                        "period": "2022-Q3",
                        "stake_amount": 50000.0,
                        "uptime": 0.982,
                        "blocks_proposed": 58,
                        "votes_cast": 3891,
                        "performance_score": 0.91
                    }
                ],
                "network_metrics": {
                    "total_transactions_processed": 2456789,
                    "average_tps_contribution": 12.5,
                    "network_stability_contribution": 0.87
                }
            }

            return participation_data

        except Exception as e:
            logger.error(f"Error fetching participation data: {e}")
            return {}

    async def _fetch_security_activities(self, address: str, start_date: datetime,
                                       end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch security-related activities and contributions"""
        try:
            # Simulate security activities data
            security_activities = [
                {
                    "activity_id": "sec_001",
                    "type": "vulnerability_report",
                    "title": "Potential DoS vector in relay message handling",
                    "severity": "medium",
                    "date": datetime(2022, 2, 15),
                    "status": "resolved",
                    "impact_score": 0.78,
                    "reward_received": 500.0
                },
                {
                    "activity_id": "sec_002",
                    "type": "security_audit",
                    "title": "Peer review of consensus mechanism update",
                    "severity": "informational",
                    "date": datetime(2022, 4, 8),
                    "status": "completed",
                    "impact_score": 0.65,
                    "reward_received": 0.0
                },
                {
                    "activity_id": "sec_003",
                    "type": "incident_response",
                    "title": "Assisted in network congestion analysis",
                    "severity": "low",
                    "date": datetime(2022, 5, 22),
                    "status": "completed",
                    "impact_score": 0.72,
                    "reward_received": 200.0
                }
            ]

            return security_activities

        except Exception as e:
            logger.error(f"Error fetching security activities: {e}")
            return []

    def _calculate_node_operation_score(self, node_records: List[NodeRecord]) -> float:
        """Calculate node operation score"""
        try:
            if not node_records:
                return 0.0

            config = self.consensus_config['node_operation']

            # Filter participation nodes
            participation_nodes = [n for n in node_records if n.node_type == NodeType.PARTICIPATION_NODE]

            if not participation_nodes:
                return 0.0

            # Calculate component scores
            uptime_scores = [n.uptime_percentage / 100 for n in participation_nodes]
            performance_scores = [n.network_contribution_score for n in participation_nodes]
            security_scores = [n.security_score for n in participation_nodes]

            # Calculate weighted average
            uptime_weight = config['uptime_consistency']
            performance_weight = config['performance_metrics']
            security_weight = config['security_practices']

            avg_uptime = sum(uptime_scores) / len(uptime_scores)
            avg_performance = sum(performance_scores) / len(performance_scores)
            avg_security = sum(security_scores) / len(security_scores)

            weighted_score = (
                avg_uptime * uptime_weight +
                avg_performance * performance_weight +
                avg_security * security_weight
            ) * 100

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating node operation score: {e}")
            return 0.0

    def _calculate_relay_participation_score(self, node_records: List[NodeRecord]) -> float:
        """Calculate relay participation score"""
        try:
            config = self.consensus_config['relay_participation']

            # Filter relay nodes
            relay_nodes = [n for n in node_records if n.node_type == NodeType.RELAY_NODE]

            if not relay_nodes:
                return 0.0

            # Calculate component scores
            uptime_scores = [n.uptime_percentage / 100 for n in relay_nodes]
            performance_scores = []

            for node in relay_nodes:
                bandwidth = node.performance_metrics.get('bandwidth_provided', 0)
                stability = node.performance_metrics.get('connection_stability', 0)
                coverage = node.performance_metrics.get('geographic_coverage', 0)

                node_performance = (bandwidth * 0.4 + stability * 0.4 + coverage * 0.2)
                performance_scores.append(node_performance)

            # Apply config weights
            uptime_weight = config['relay_uptime']
            bandwidth_weight = config['bandwidth_contribution']

            avg_uptime = sum(uptime_scores) / len(uptime_scores)
            avg_performance = sum(performance_scores) / len(performance_scores)

            weighted_score = (
                avg_uptime * uptime_weight +
                avg_performance * bandwidth_weight
            ) * 100

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating relay participation score: {e}")
            return 0.0

    def _calculate_security_contribution_score(self, security_activities: List[Dict[str, Any]]) -> float:
        """Calculate security contribution score"""
        try:
            if not security_activities:
                return 0.0

            config = self.consensus_config['security_contributions']

            # Categorize security activities
            vulnerability_reports = [a for a in security_activities if a['type'] == 'vulnerability_report']
            security_audits = [a for a in security_activities if a['type'] == 'security_audit']
            incident_responses = [a for a in security_activities if a['type'] == 'incident_response']

            # Calculate scores for each category
            vulnerability_score = 0.0
            if vulnerability_reports:
                avg_impact = sum(a['impact_score'] for a in vulnerability_reports) / len(vulnerability_reports)
                vulnerability_score = avg_impact * len(vulnerability_reports) * 20  # Scale factor

            audit_score = 0.0
            if security_audits:
                avg_impact = sum(a['impact_score'] for a in security_audits) / len(security_audits)
                audit_score = avg_impact * len(security_audits) * 15

            incident_score = 0.0
            if incident_responses:
                avg_impact = sum(a['impact_score'] for a in incident_responses) / len(incident_responses)
                incident_score = avg_impact * len(incident_responses) * 10

            # Apply config weights
            weighted_score = (
                vulnerability_score * config['vulnerability_reporting'] +
                audit_score * config['security_auditing'] +
                incident_score * config['incident_response']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating security contribution score: {e}")
            return 0.0

    def _calculate_overall_consensus_score(self, node_operation_score: float,
                                         relay_participation_score: float,
                                         security_contribution_score: float) -> float:
        """Calculate overall consensus participation score"""
        try:
            weights = self.consensus_config

            # Apply category weights
            weighted_score = (
                node_operation_score * weights['node_operation']['weight'] +
                relay_participation_score * weights['relay_participation']['weight'] +
                security_contribution_score * weights['security_contributions']['weight']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating overall consensus score: {e}")
            return 0.0

    def _calculate_consensus_metrics(self, node_records: List[NodeRecord],
                                   participation_data: Dict[str, Any]) -> ConsensusMetrics:
        """Calculate detailed consensus metrics"""
        try:
            # Calculate stake metrics
            total_stake = sum(n.stake_amount for n in node_records if n.node_type == NodeType.PARTICIPATION_NODE)
            active_nodes = [n for n in node_records if n.status == ParticipationStatus.ACTIVE]
            online_stake = sum(n.stake_amount for n in active_nodes if n.node_type == NodeType.PARTICIPATION_NODE)
            online_stake_percentage = (online_stake / total_stake) if total_stake > 0 else 0

            # Calculate participation metrics
            participation_rate = participation_data.get('participation_rate', 0)

            # Calculate performance metrics
            participation_nodes = [n for n in node_records if n.node_type == NodeType.PARTICIPATION_NODE]
            avg_uptime = sum(n.uptime_percentage for n in participation_nodes) / max(len(participation_nodes), 1)

            # Calculate block proposal efficiency
            total_blocks = sum(n.blocks_proposed for n in participation_nodes)
            total_votes = sum(n.votes_cast for n in participation_nodes)
            block_efficiency = (total_blocks / max(total_votes, 1)) if total_votes > 0 else 0

            # Calculate voting consistency (simplified)
            voting_consistency = 0.95  # Would be calculated from actual voting data

            # Calculate performance reliability
            performance_scores = [n.network_contribution_score for n in participation_nodes]
            performance_reliability = sum(performance_scores) / max(len(performance_scores), 1)

            return ConsensusMetrics(
                total_stake=total_stake,
                online_stake_percentage=online_stake_percentage,
                consensus_participation_rate=participation_rate,
                block_proposal_efficiency=block_efficiency,
                voting_consistency=voting_consistency,
                network_uptime=avg_uptime / 100,
                performance_reliability=performance_reliability
            )

        except Exception as e:
            logger.error(f"Error calculating consensus metrics: {e}")
            return ConsensusMetrics(0, 0, 0, 0, 0, 0, 0)

    def _identify_network_contributions(self, node_records: List[NodeRecord],
                                      participation_data: Dict[str, Any]) -> List[str]:
        """Identify notable network contributions"""
        contributions = []

        try:
            # Check for relay node operation
            relay_nodes = [n for n in node_records if n.node_type == NodeType.RELAY_NODE]
            if relay_nodes:
                contributions.append(f"Operating {len(relay_nodes)} relay node(s) for network infrastructure")

            # Check for high-stake participation
            participation_nodes = [n for n in node_records if n.node_type == NodeType.PARTICIPATION_NODE]
            if participation_nodes:
                total_stake = sum(n.stake_amount for n in participation_nodes)
                if total_stake > 100000:
                    contributions.append(f"High-stake consensus participation ({total_stake:,.0f} ALGO)")

            # Check for consistent uptime
            if participation_nodes:
                avg_uptime = sum(n.uptime_percentage for n in participation_nodes) / len(participation_nodes)
                if avg_uptime > 98:
                    contributions.append(f"Excellent node uptime ({avg_uptime:.1f}%)")

            # Check for block proposal activity
            total_blocks = sum(n.blocks_proposed for n in participation_nodes)
            if total_blocks > 100:
                contributions.append(f"Active block proposer ({total_blocks} blocks)")

            # Check for long-term participation
            oldest_node = min(node_records, key=lambda n: n.first_online, default=None)
            if oldest_node and oldest_node.first_online < datetime.utcnow() - timedelta(days=365):
                contributions.append("Long-term consensus participant (1+ years)")

        except Exception as e:
            logger.error(f"Error identifying network contributions: {e}")

        return contributions

    def _identify_security_activities(self, security_activities: List[Dict[str, Any]]) -> List[str]:
        """Identify security-related activities"""
        activities = []

        try:
            vulnerability_reports = [a for a in security_activities if a['type'] == 'vulnerability_report']
            if vulnerability_reports:
                activities.append(f"Reported {len(vulnerability_reports)} security vulnerabilities")

            security_audits = [a for a in security_activities if a['type'] == 'security_audit']
            if security_audits:
                activities.append(f"Participated in {len(security_audits)} security audits")

            incident_responses = [a for a in security_activities if a['type'] == 'incident_response']
            if incident_responses:
                activities.append(f"Assisted in {len(incident_responses)} security incidents")

            # Check for security rewards
            total_rewards = sum(a.get('reward_received', 0) for a in security_activities)
            if total_rewards > 0:
                activities.append(f"Security contributions rewarded ({total_rewards:,.0f} ALGO)")

        except Exception as e:
            logger.error(f"Error identifying security activities: {e}")

        return activities

    def _identify_reliability_indicators(self, node_records: List[NodeRecord]) -> List[str]:
        """Identify reliability and performance indicators"""
        indicators = []

        try:
            # Check for high uptime consistency
            if node_records:
                avg_uptime = sum(n.uptime_percentage for n in node_records) / len(node_records)
                if avg_uptime > 99:
                    indicators.append("Exceptional node uptime reliability (>99%)")
                elif avg_uptime > 95:
                    indicators.append("High node uptime reliability (>95%)")

            # Check for performance consistency
            performance_scores = [n.network_contribution_score for n in node_records]
            if performance_scores:
                avg_performance = sum(performance_scores) / len(performance_scores)
                if avg_performance > 0.9:
                    indicators.append("Consistently high performance metrics")

            # Check for multi-node operation
            if len(node_records) > 1:
                indicators.append(f"Operating multiple nodes ({len(node_records)} nodes)")

            # Check for diverse node types
            node_types = set(n.node_type for n in node_records)
            if len(node_types) > 1:
                indicators.append("Diverse node operation (participation + relay)")

            # Check for security track record
            high_security_nodes = [n for n in node_records if n.security_score > 0.9]
            if len(high_security_nodes) == len(node_records) and node_records:
                indicators.append("Excellent security practices across all nodes")

        except Exception as e:
            logger.error(f"Error identifying reliability indicators: {e}")

        return indicators

    def _identify_consensus_risks(self, node_records: List[NodeRecord],
                                participation_data: Dict[str, Any]) -> List[str]:
        """Identify potential risks in consensus participation"""
        risks = []

        try:
            if not node_records:
                risks.append("No consensus participation detected")
                return risks

            # Check for low uptime
            low_uptime_nodes = [n for n in node_records if n.uptime_percentage < 95]
            if low_uptime_nodes:
                risks.append(f"{len(low_uptime_nodes)} node(s) with sub-optimal uptime")

            # Check for inactive nodes
            inactive_nodes = [n for n in node_records if n.status != ParticipationStatus.ACTIVE]
            if inactive_nodes:
                risks.append(f"{len(inactive_nodes)} inactive node(s)")

            # Check for poor performance
            poor_performance_nodes = [n for n in node_records if n.network_contribution_score < 0.7]
            if poor_performance_nodes:
                risks.append("Some nodes showing poor performance metrics")

            # Check for security concerns
            low_security_nodes = [n for n in node_records if n.security_score < 0.8]
            if low_security_nodes:
                risks.append("Security score below recommended threshold for some nodes")

            # Check for stake concentration
            participation_nodes = [n for n in node_records if n.node_type == NodeType.PARTICIPATION_NODE]
            if len(participation_nodes) == 1:
                risks.append("Single node operation may pose availability risk")

            # Check for recent inactivity
            recent_activity = [n for n in node_records if n.last_online > datetime.utcnow() - timedelta(days=7)]
            if len(recent_activity) < len(node_records):
                risks.append("Some nodes not recently active")

        except Exception as e:
            logger.error(f"Error identifying consensus risks: {e}")

        return risks

    def _generate_consensus_recommendations(self, node_operation_score: float,
                                          relay_participation_score: float,
                                          security_contribution_score: float) -> List[str]:
        """Generate recommendations for improving consensus participation"""
        recommendations = []

        try:
            if node_operation_score < 50:
                recommendations.append("Improve node uptime and performance metrics")

            if relay_participation_score == 0:
                recommendations.append("Consider operating a relay node to support network infrastructure")

            if security_contribution_score < 30:
                recommendations.append("Participate in security audits or vulnerability reporting")

            if node_operation_score > 80 and security_contribution_score > 60:
                recommendations.append("Excellent consensus participation - consider expanding network contribution")

            if relay_participation_score > 70:
                recommendations.append("Strong relay operation - consider geographic diversity expansion")

        except Exception as e:
            logger.error(f"Error generating consensus recommendations: {e}")

        return recommendations