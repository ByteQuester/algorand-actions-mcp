"""
Algorand network health and activity metrics utilities.

Provides comprehensive analysis of network health including:
- Consensus participation and performance
- Transaction throughput and capacity
- Network decentralization metrics
- Economic activity indicators
"""

import math
import statistics
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum


class NetworkPhase(Enum):
    """Algorand network phases"""
    HEALTHY = "healthy"
    CONGESTED = "congested"
    STRESSED = "stressed"
    CRITICAL = "critical"


@dataclass
class ConsensusMetrics:
    """Consensus participation and performance metrics"""
    timestamp: datetime

    # Participation metrics
    total_stake_online: Decimal = Decimal('0')
    total_stake_offline: Decimal = Decimal('0')
    participation_rate: float = 0.0  # Percentage of stake online

    # Performance metrics
    average_block_time: float = 0.0  # Seconds
    block_time_variance: float = 0.0
    fork_rate: float = 0.0  # Percentage of blocks that were forks

    # Consensus quality
    consensus_efficiency: float = 0.0  # 0-1 score
    validator_diversity: float = 0.0   # Geographic/entity diversity
    nakamoto_coefficient: int = 0      # Decentralization measure

    @property
    def network_security_score(self) -> float:
        """Calculate overall network security score (0-100)"""
        # Weight different factors
        participation_score = self.participation_rate
        efficiency_score = self.consensus_efficiency * 100
        diversity_score = min(100, self.validator_diversity * 100)
        decentralization_score = min(100, self.nakamoto_coefficient * 5)

        weights = [0.3, 0.25, 0.25, 0.2]  # Participation, efficiency, diversity, decentralization
        scores = [participation_score, efficiency_score, diversity_score, decentralization_score]

        return sum(w * s for w, s in zip(weights, scores))


@dataclass
class NetworkActivity:
    """Network activity and economic metrics"""
    timestamp: datetime
    measurement_period_hours: int = 24

    # Transaction metrics
    total_transactions: int = 0
    payment_transactions: int = 0
    app_call_transactions: int = 0
    asset_transfer_transactions: int = 0

    # Throughput metrics
    transactions_per_second: float = 0.0
    peak_tps: float = 0.0
    average_block_utilization: float = 0.0  # 0-1

    # Economic metrics
    total_fees_paid: Decimal = Decimal('0')
    total_value_transferred: Decimal = Decimal('0')
    unique_active_accounts: int = 0

    # DeFi activity
    defi_transaction_ratio: float = 0.0
    total_defi_volume: Decimal = Decimal('0')

    @property
    def network_utilization_score(self) -> float:
        """Calculate network utilization health score (0-100)"""
        # Optimal utilization is around 30-70%
        utilization = self.average_block_utilization

        if 0.3 <= utilization <= 0.7:
            score = 100.0
        elif utilization < 0.3:
            # Under-utilized
            score = utilization / 0.3 * 100
        else:
            # Over-utilized (potential congestion)
            score = max(0, 100 - (utilization - 0.7) * 200)

        return score


class NetworkHealthMonitor:
    """
    Comprehensive Algorand network health monitor.

    Tracks consensus performance, transaction throughput,
    and overall network stability.
    """

    def __init__(self):
        self.health_history: List[Tuple[datetime, float]] = []
        self.alert_thresholds = {
            'participation_rate': 0.8,      # 80% minimum
            'block_time_variance': 0.5,     # 0.5s maximum variance
            'tps_degradation': 0.3,         # 30% degradation threshold
            'consensus_efficiency': 0.9      # 90% minimum efficiency
        }

    def assess_network_health(
        self,
        consensus_metrics: ConsensusMetrics,
        activity_metrics: NetworkActivity
    ) -> Dict[str, any]:
        """
        Comprehensive network health assessment.

        Args:
            consensus_metrics: Consensus performance data
            activity_metrics: Network activity data

        Returns:
            Health assessment with scores and alerts
        """
        assessment = {
            'overall_health_score': 0.0,
            'consensus_health': 0.0,
            'activity_health': 0.0,
            'network_phase': NetworkPhase.HEALTHY,
            'alerts': [],
            'recommendations': []
        }

        # Assess consensus health
        consensus_health = self._assess_consensus_health(consensus_metrics)
        assessment['consensus_health'] = consensus_health

        # Assess activity health
        activity_health = self._assess_activity_health(activity_metrics)
        assessment['activity_health'] = activity_health

        # Calculate overall health
        overall_health = (consensus_health + activity_health) / 2
        assessment['overall_health_score'] = overall_health

        # Determine network phase
        assessment['network_phase'] = self._determine_network_phase(
            consensus_metrics, activity_metrics
        )

        # Generate alerts
        alerts = self._generate_health_alerts(consensus_metrics, activity_metrics)
        assessment['alerts'] = alerts

        # Generate recommendations
        recommendations = self._generate_recommendations(consensus_metrics, activity_metrics)
        assessment['recommendations'] = recommendations

        # Store in history
        self.health_history.append((datetime.now(), overall_health))

        return assessment

    def _assess_consensus_health(self, metrics: ConsensusMetrics) -> float:
        """Assess consensus mechanism health"""
        health_score = 0.0

        # Participation rate score (0-30 points)
        participation_score = min(30, metrics.participation_rate * 30 / 100)
        health_score += participation_score

        # Block time consistency (0-25 points)
        if metrics.average_block_time > 0:
            # Algorand targets ~3.3 second blocks
            target_block_time = 3.3
            time_deviation = abs(metrics.average_block_time - target_block_time) / target_block_time

            # Penalize deviation from target
            time_score = max(0, 25 - time_deviation * 50)
            health_score += time_score

        # Consensus efficiency (0-25 points)
        efficiency_score = metrics.consensus_efficiency * 25
        health_score += efficiency_score

        # Decentralization (0-20 points)
        # Higher Nakamoto coefficient is better
        decentralization_score = min(20, metrics.nakamoto_coefficient * 2)
        health_score += decentralization_score

        return min(100.0, health_score)

    def _assess_activity_health(self, metrics: NetworkActivity) -> float:
        """Assess network activity health"""
        health_score = 0.0

        # Utilization score (0-40 points)
        utilization_score = metrics.network_utilization_score * 0.4
        health_score += utilization_score

        # TPS performance (0-30 points)
        # Algorand can handle ~1000 TPS, score based on current usage
        if metrics.transactions_per_second >= 0:
            tps_efficiency = min(1.0, metrics.transactions_per_second / 1000)
            tps_score = tps_efficiency * 30
            health_score += tps_score

        # Economic activity (0-20 points)
        if metrics.total_transactions > 0:
            # Score based on transaction diversity
            payment_ratio = metrics.payment_transactions / metrics.total_transactions
            app_ratio = metrics.app_call_transactions / metrics.total_transactions
            asset_ratio = metrics.asset_transfer_transactions / metrics.total_transactions

            # Balanced activity is healthier
            diversity_score = 1 - max(payment_ratio, app_ratio, asset_ratio)
            economic_score = diversity_score * 20
            health_score += economic_score

        # DeFi activity bonus (0-10 points)
        defi_score = min(10, metrics.defi_transaction_ratio * 20)
        health_score += defi_score

        return min(100.0, health_score)

    def _determine_network_phase(
        self,
        consensus_metrics: ConsensusMetrics,
        activity_metrics: NetworkActivity
    ) -> NetworkPhase:
        """Determine current network phase based on metrics"""

        # Critical issues
        if (consensus_metrics.participation_rate < 70 or
            activity_metrics.average_block_utilization > 0.95):
            return NetworkPhase.CRITICAL

        # Stressed conditions
        if (consensus_metrics.participation_rate < 80 or
            activity_metrics.average_block_utilization > 0.85 or
            consensus_metrics.average_block_time > 5.0):
            return NetworkPhase.STRESSED

        # Congestion
        if (activity_metrics.average_block_utilization > 0.75 or
            activity_metrics.transactions_per_second > 800):
            return NetworkPhase.CONGESTED

        # Healthy
        return NetworkPhase.HEALTHY

    def _generate_health_alerts(
        self,
        consensus_metrics: ConsensusMetrics,
        activity_metrics: NetworkActivity
    ) -> List[Dict[str, str]]:
        """Generate health alerts based on threshold violations"""
        alerts = []

        # Participation rate alert
        if consensus_metrics.participation_rate < self.alert_thresholds['participation_rate'] * 100:
            alerts.append({
                'type': 'consensus',
                'severity': 'high',
                'message': f"Low participation rate: {consensus_metrics.participation_rate:.1f}%",
                'threshold': f"{self.alert_thresholds['participation_rate'] * 100}%"
            })

        # Block time variance alert
        if consensus_metrics.block_time_variance > self.alert_thresholds['block_time_variance']:
            alerts.append({
                'type': 'consensus',
                'severity': 'medium',
                'message': f"High block time variance: {consensus_metrics.block_time_variance:.2f}s",
                'threshold': f"{self.alert_thresholds['block_time_variance']}s"
            })

        # Network congestion alert
        if activity_metrics.average_block_utilization > 0.9:
            alerts.append({
                'type': 'capacity',
                'severity': 'high',
                'message': f"Network congestion: {activity_metrics.average_block_utilization:.1%} utilization",
                'threshold': "90%"
            })

        # Consensus efficiency alert
        if consensus_metrics.consensus_efficiency < self.alert_thresholds['consensus_efficiency']:
            alerts.append({
                'type': 'consensus',
                'severity': 'medium',
                'message': f"Low consensus efficiency: {consensus_metrics.consensus_efficiency:.1%}",
                'threshold': f"{self.alert_thresholds['consensus_efficiency']:.1%}"
            })

        return alerts

    def _generate_recommendations(
        self,
        consensus_metrics: ConsensusMetrics,
        activity_metrics: NetworkActivity
    ) -> List[str]:
        """Generate recommendations based on current metrics"""
        recommendations = []

        # Participation recommendations
        if consensus_metrics.participation_rate < 85:
            recommendations.append(
                "Consider incentivizing more ALGO holders to participate in consensus"
            )

        # Capacity recommendations
        if activity_metrics.average_block_utilization > 0.8:
            recommendations.append(
                "Monitor network capacity closely; consider protocol upgrades for scalability"
            )

        # Decentralization recommendations
        if consensus_metrics.nakamoto_coefficient < 20:
            recommendations.append(
                "Work on improving validator decentralization"
            )

        # DeFi activity recommendations
        if activity_metrics.defi_transaction_ratio < 0.1:
            recommendations.append(
                "Consider initiatives to increase DeFi adoption and usage"
            )

        return recommendations

    def get_network_trends(self, days: int = 7) -> Dict[str, any]:
        """
        Analyze network health trends over specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis including direction and volatility
        """
        if len(self.health_history) < 2:
            return {"trend": "insufficient_data"}

        # Filter recent history
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            (timestamp, score) for timestamp, score in self.health_history
            if timestamp >= cutoff_date
        ]

        if len(recent_history) < 2:
            return {"trend": "insufficient_recent_data"}

        # Calculate trend
        scores = [score for _, score in recent_history]
        timestamps = [ts for ts, _ in recent_history]

        # Linear regression for trend
        n = len(scores)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(scores) / n

        numerator = sum((x_values[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # Determine trend direction
        if slope > 0.5:
            trend_direction = "improving"
        elif slope < -0.5:
            trend_direction = "declining"
        else:
            trend_direction = "stable"

        # Calculate volatility
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0

        return {
            "trend": trend_direction,
            "slope": slope,
            "volatility": volatility,
            "current_score": scores[-1],
            "average_score": y_mean,
            "data_points": len(scores),
            "period_days": days
        }


class ActivityScorer:
    """
    Activity scoring for individual addresses and overall network.

    Provides normalized scoring for different types of activity
    relative to network-wide patterns.
    """

    @staticmethod
    def calculate_network_activity_score(
        current_metrics: NetworkActivity,
        historical_baseline: Optional[NetworkActivity] = None
    ) -> Dict[str, float]:
        """
        Calculate network activity score relative to baseline.

        Args:
            current_metrics: Current network activity
            historical_baseline: Historical baseline for comparison

        Returns:
            Activity scores for different dimensions
        """
        scores = {
            "transaction_volume": 0.0,
            "transaction_diversity": 0.0,
            "economic_activity": 0.0,
            "defi_adoption": 0.0,
            "overall_activity": 0.0
        }

        # Transaction volume score
        if current_metrics.transactions_per_second > 0:
            # Score based on percentage of network capacity
            capacity_utilization = current_metrics.transactions_per_second / 1000  # Algorand capacity
            scores["transaction_volume"] = min(100.0, capacity_utilization * 100)

        # Transaction diversity score
        if current_metrics.total_transactions > 0:
            payment_ratio = current_metrics.payment_transactions / current_metrics.total_transactions
            app_ratio = current_metrics.app_call_transactions / current_metrics.total_transactions
            asset_ratio = current_metrics.asset_transfer_transactions / current_metrics.total_transactions

            # Calculate Shannon diversity index
            ratios = [payment_ratio, app_ratio, asset_ratio]
            ratios = [r for r in ratios if r > 0]  # Remove zero ratios

            if ratios:
                entropy = -sum(r * math.log2(r) for r in ratios)
                max_entropy = math.log2(3)  # Maximum possible with 3 categories
                diversity_score = (entropy / max_entropy) * 100
                scores["transaction_diversity"] = diversity_score

        # Economic activity score
        if historical_baseline:
            # Compare to historical baseline
            volume_ratio = float(current_metrics.total_value_transferred) / max(
                float(historical_baseline.total_value_transferred), 1
            )
            scores["economic_activity"] = min(100.0, volume_ratio * 50)  # Cap at 100
        else:
            # Score based on absolute activity
            scores["economic_activity"] = min(100.0,
                float(current_metrics.total_value_transferred) / 1000000 * 10)  # Per $1M

        # DeFi adoption score
        scores["defi_adoption"] = min(100.0, current_metrics.defi_transaction_ratio * 200)

        # Overall activity score (weighted average)
        weights = [0.3, 0.2, 0.3, 0.2]  # Volume, diversity, economic, DeFi
        component_scores = [
            scores["transaction_volume"],
            scores["transaction_diversity"],
            scores["economic_activity"],
            scores["defi_adoption"]
        ]

        scores["overall_activity"] = sum(w * s for w, s in zip(weights, component_scores))

        return scores

    @staticmethod
    def score_address_activity_relative_to_network(
        address_activity: Dict[str, any],
        network_percentiles: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Score individual address activity relative to network distribution.

        Args:
            address_activity: Activity metrics for specific address
            network_percentiles: Network-wide percentile distributions

        Returns:
            Percentile scores for address across different metrics
        """
        scores = {}

        metrics_to_score = [
            "total_transactions",
            "transaction_volume_usd",
            "unique_counterparties",
            "defi_transactions"
        ]

        for metric in metrics_to_score:
            address_value = address_activity.get(metric, 0)

            # Find percentile in network distribution
            percentile = ActivityScorer._find_percentile(
                address_value,
                network_percentiles.get(metric, {})
            )

            scores[f"{metric}_percentile"] = percentile

        return scores

    @staticmethod
    def _find_percentile(value: float, percentile_data: Dict[str, float]) -> float:
        """Find which percentile a value falls into"""
        if not percentile_data:
            return 50.0  # Default to median

        # Common percentiles
        percentiles = [10, 25, 50, 75, 90, 95, 99]

        for p in percentiles:
            threshold = percentile_data.get(f"p{p}", float('inf'))
            if value <= threshold:
                return p

        return 99.0  # Above 99th percentile


class BlockchainAnalyzer:
    """
    Comprehensive blockchain analysis for economic and technical health.

    Provides insights into blockchain economic activity,
    technical performance, and ecosystem growth.
    """

    @staticmethod
    def analyze_economic_health(
        fee_data: List[Decimal],
        volume_data: List[Decimal],
        active_accounts: List[int],
        timestamps: List[datetime]
    ) -> Dict[str, any]:
        """
        Analyze economic health of the blockchain.

        Args:
            fee_data: Historical fee data
            volume_data: Historical transaction volume
            active_accounts: Historical active account counts
            timestamps: Corresponding timestamps

        Returns:
            Economic health analysis
        """
        if not all([fee_data, volume_data, active_accounts, timestamps]):
            return {"health_score": 0.0, "trend": "insufficient_data"}

        analysis = {
            "fee_trend": "stable",
            "volume_trend": "stable",
            "adoption_trend": "stable",
            "economic_health_score": 0.0,
            "sustainability_score": 0.0
        }

        # Analyze fee trends
        if len(fee_data) >= 7:  # Need at least a week of data
            recent_fees = fee_data[-7:]
            older_fees = fee_data[-14:-7] if len(fee_data) >= 14 else fee_data[:-7]

            if older_fees:
                recent_avg = sum(recent_fees) / len(recent_fees)
                older_avg = sum(older_fees) / len(older_fees)

                if recent_avg > older_avg * Decimal('1.2'):  # 20% increase
                    analysis["fee_trend"] = "increasing"
                elif recent_avg < older_avg * Decimal('0.8'):  # 20% decrease
                    analysis["fee_trend"] = "decreasing"

        # Analyze volume trends
        if len(volume_data) >= 7:
            recent_volume = volume_data[-7:]
            older_volume = volume_data[-14:-7] if len(volume_data) >= 14 else volume_data[:-7]

            if older_volume:
                recent_avg = sum(recent_volume) / len(recent_volume)
                older_avg = sum(older_volume) / len(older_volume)

                if recent_avg > older_avg * Decimal('1.2'):
                    analysis["volume_trend"] = "increasing"
                elif recent_avg < older_avg * Decimal('0.8'):
                    analysis["volume_trend"] = "decreasing"

        # Analyze adoption trends
        if len(active_accounts) >= 7:
            recent_accounts = active_accounts[-7:]
            older_accounts = active_accounts[-14:-7] if len(active_accounts) >= 14 else active_accounts[:-7]

            if older_accounts:
                recent_avg = sum(recent_accounts) / len(recent_accounts)
                older_avg = sum(older_accounts) / len(older_accounts)

                if recent_avg > older_avg * 1.1:  # 10% increase
                    analysis["adoption_trend"] = "increasing"
                elif recent_avg < older_avg * 0.9:  # 10% decrease
                    analysis["adoption_trend"] = "decreasing"

        # Calculate economic health score
        trend_scores = {
            "increasing": 100,
            "stable": 80,
            "decreasing": 40
        }

        fee_score = trend_scores[analysis["fee_trend"]]
        volume_score = trend_scores[analysis["volume_trend"]]
        adoption_score = trend_scores[analysis["adoption_trend"]]

        # Weight adoption more heavily
        economic_health = (fee_score * 0.25 + volume_score * 0.35 + adoption_score * 0.4)
        analysis["economic_health_score"] = economic_health

        # Calculate sustainability score based on fee coverage
        if volume_data and fee_data:
            latest_volume = volume_data[-1]
            latest_fees = fee_data[-1]

            if latest_volume > 0:
                fee_ratio = float(latest_fees / latest_volume)
                # Sustainable if fees are meaningful but not excessive
                if 0.001 <= fee_ratio <= 0.01:  # 0.1% to 1%
                    sustainability = 100
                elif fee_ratio < 0.001:
                    sustainability = fee_ratio / 0.001 * 80  # Scale to 80 max
                else:
                    sustainability = max(0, 100 - (fee_ratio - 0.01) * 2000)  # Penalty for high fees

                analysis["sustainability_score"] = sustainability
            else:
                analysis["sustainability_score"] = 50  # Neutral

        return analysis