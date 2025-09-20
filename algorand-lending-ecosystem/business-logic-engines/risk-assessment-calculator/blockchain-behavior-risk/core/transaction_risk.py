"""
Transaction Risk Analyzer

Specialized analyzer for transaction velocity, pattern analysis,
and behavioral risk assessment in Algorand transactions.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import logging

from ...common.models.blockchain_risk import TransactionPattern, BehaviorPattern, RiskLevel


@dataclass
class VelocityMetrics:
    """Transaction velocity metrics"""
    transactions_per_hour: float
    volume_per_hour: float
    velocity_z_score: float
    baseline_velocity: float
    velocity_percentile: float


@dataclass
class PatternMetrics:
    """Transaction pattern metrics"""
    pattern_consistency: float
    timing_regularity: float
    amount_distribution: Dict[str, float]
    counterparty_diversity: float
    asset_diversity: float


class TransactionRiskAnalyzer:
    """Specialized transaction behavior risk analyzer"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Configuration parameters
        self.velocity_config = config.get('risk_assessment', {}).get('transaction_patterns', {}).get('velocity_spike', {})
        self.dormant_config = config.get('risk_assessment', {}).get('transaction_patterns', {}).get('dormant_activation', {})
        self.wash_config = config.get('risk_assessment', {}).get('transaction_patterns', {}).get('wash_trading', {})

    async def analyze_transaction_patterns(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive transaction pattern analysis

        Args:
            wallet_address: Wallet address to analyze
            transactions: Transaction history

        Returns:
            Dictionary containing various risk metrics
        """
        if not transactions:
            return self._empty_analysis_result()

        try:
            # Calculate velocity metrics
            velocity_metrics = await self._calculate_velocity_metrics(transactions)

            # Analyze transaction patterns
            pattern_metrics = await self._analyze_pattern_metrics(transactions)

            # Detect suspicious behaviors
            suspicious_behaviors = await self._detect_suspicious_behaviors(
                transactions, velocity_metrics, pattern_metrics
            )

            # Calculate overall transaction risk score
            overall_risk = await self._calculate_overall_transaction_risk(
                velocity_metrics, pattern_metrics, suspicious_behaviors
            )

            return {
                'velocity_metrics': velocity_metrics,
                'pattern_metrics': pattern_metrics,
                'suspicious_behaviors': suspicious_behaviors,
                'overall_risk_score': overall_risk,
                'analysis_timestamp': datetime.utcnow(),
                'transaction_count': len(transactions)
            }

        except Exception as e:
            self.logger.error(f"Transaction pattern analysis failed for {wallet_address}: {e}")
            return self._empty_analysis_result()

    async def _calculate_velocity_metrics(
        self,
        transactions: List[Dict[str, Any]]
    ) -> VelocityMetrics:
        """Calculate transaction velocity metrics"""
        if len(transactions) < 2:
            return VelocityMetrics(0, 0, 0, 0, 0)

        # Sort transactions by timestamp
        sorted_txns = sorted(
            transactions,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        # Calculate hourly metrics
        hourly_counts = defaultdict(int)
        hourly_volumes = defaultdict(float)

        for txn in sorted_txns:
            timestamp = datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0)

            hourly_counts[hour_key] += 1
            hourly_volumes[hour_key] += float(txn.get('amount', 0))

        # Calculate average metrics
        if hourly_counts:
            avg_txns_per_hour = statistics.mean(hourly_counts.values())
            avg_volume_per_hour = statistics.mean(hourly_volumes.values())

            # Calculate velocity z-score for recent period
            recent_hours = sorted(hourly_counts.keys())[-24:]  # Last 24 hours
            if len(recent_hours) > 1:
                recent_velocity = statistics.mean(
                    hourly_counts[hour] for hour in recent_hours
                )

                # Calculate baseline (exclude recent period)
                baseline_hours = [hour for hour in hourly_counts.keys() if hour not in recent_hours]
                if baseline_hours:
                    baseline_velocities = [hourly_counts[hour] for hour in baseline_hours]
                    baseline_mean = statistics.mean(baseline_velocities)
                    baseline_std = statistics.stdev(baseline_velocities) if len(baseline_velocities) > 1 else 1

                    velocity_z_score = (recent_velocity - baseline_mean) / max(baseline_std, 0.1)
                else:
                    velocity_z_score = 0
                    baseline_mean = avg_txns_per_hour
            else:
                velocity_z_score = 0
                baseline_mean = avg_txns_per_hour

            # Calculate percentile
            all_velocities = list(hourly_counts.values())
            all_velocities.sort()
            if all_velocities:
                current_velocity = hourly_counts.get(recent_hours[-1], 0) if recent_hours else 0
                percentile = (
                    sum(1 for v in all_velocities if v <= current_velocity) / len(all_velocities) * 100
                )
            else:
                percentile = 50

        else:
            avg_txns_per_hour = 0
            avg_volume_per_hour = 0
            velocity_z_score = 0
            baseline_mean = 0
            percentile = 50

        return VelocityMetrics(
            transactions_per_hour=avg_txns_per_hour,
            volume_per_hour=avg_volume_per_hour,
            velocity_z_score=velocity_z_score,
            baseline_velocity=baseline_mean,
            velocity_percentile=percentile
        )

    async def _analyze_pattern_metrics(
        self,
        transactions: List[Dict[str, Any]]
    ) -> PatternMetrics:
        """Analyze transaction pattern characteristics"""
        if not transactions:
            return PatternMetrics(0, 0, {}, 0, 0)

        # Timing analysis
        timestamps = [
            datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))
            for txn in transactions
        ]
        timestamps.sort()

        # Calculate timing regularity
        if len(timestamps) > 2:
            time_gaps = [
                (timestamps[i] - timestamps[i-1]).total_seconds()
                for i in range(1, len(timestamps))
            ]

            if time_gaps:
                gap_mean = statistics.mean(time_gaps)
                gap_std = statistics.stdev(time_gaps) if len(time_gaps) > 1 else 0
                timing_regularity = 1.0 / (1.0 + gap_std / max(gap_mean, 1))
            else:
                timing_regularity = 0
        else:
            timing_regularity = 0

        # Amount distribution analysis
        amounts = [float(txn.get('amount', 0)) for txn in transactions if float(txn.get('amount', 0)) > 0]
        if amounts:
            amount_stats = {
                'mean': statistics.mean(amounts),
                'median': statistics.median(amounts),
                'std': statistics.stdev(amounts) if len(amounts) > 1 else 0,
                'unique_count': len(set(amounts)),
                'total_count': len(amounts)
            }

            # Pattern consistency based on amount variance
            if amount_stats['mean'] > 0:
                coefficient_of_variation = amount_stats['std'] / amount_stats['mean']
                pattern_consistency = 1.0 / (1.0 + coefficient_of_variation)
            else:
                pattern_consistency = 0
        else:
            amount_stats = {}
            pattern_consistency = 0

        # Counterparty diversity
        counterparties = set()
        for txn in transactions:
            counterparties.add(txn.get('sender', ''))
            counterparties.add(txn.get('receiver', ''))

        counterparty_diversity = len(counterparties) / max(len(transactions), 1)

        # Asset diversity
        assets = set(txn.get('asset-id', 0) for txn in transactions)
        asset_diversity = len(assets) / max(len(transactions), 1)

        return PatternMetrics(
            pattern_consistency=pattern_consistency,
            timing_regularity=timing_regularity,
            amount_distribution=amount_stats,
            counterparty_diversity=counterparty_diversity,
            asset_diversity=asset_diversity
        )

    async def _detect_suspicious_behaviors(
        self,
        transactions: List[Dict[str, Any]],
        velocity_metrics: VelocityMetrics,
        pattern_metrics: PatternMetrics
    ) -> List[Dict[str, Any]]:
        """Detect suspicious transaction behaviors"""
        suspicious_behaviors = []

        # Velocity spike detection
        velocity_threshold = self.velocity_config.get('z_score_threshold', 2.5)
        if abs(velocity_metrics.velocity_z_score) > velocity_threshold:
            suspicious_behaviors.append({
                'behavior_type': 'velocity_spike',
                'severity': min(abs(velocity_metrics.velocity_z_score) / 5.0, 1.0),
                'description': f"Transaction velocity spike detected (z-score: {velocity_metrics.velocity_z_score:.2f})",
                'evidence': {
                    'current_velocity': velocity_metrics.transactions_per_hour,
                    'baseline_velocity': velocity_metrics.baseline_velocity,
                    'z_score': velocity_metrics.velocity_z_score
                }
            })

        # Highly regular patterns (potentially automated)
        if pattern_metrics.timing_regularity > 0.9 and pattern_metrics.pattern_consistency > 0.9:
            suspicious_behaviors.append({
                'behavior_type': 'automated_pattern',
                'severity': 0.7,
                'description': "Highly regular transaction pattern suggesting automation",
                'evidence': {
                    'timing_regularity': pattern_metrics.timing_regularity,
                    'pattern_consistency': pattern_metrics.pattern_consistency
                }
            })

        # Low diversity patterns (potential circular trading)
        if (pattern_metrics.counterparty_diversity < 0.1 and
            len(transactions) > 10):
            suspicious_behaviors.append({
                'behavior_type': 'low_counterparty_diversity',
                'severity': 0.6,
                'description': "Low counterparty diversity in transaction patterns",
                'evidence': {
                    'counterparty_diversity': pattern_metrics.counterparty_diversity,
                    'transaction_count': len(transactions)
                }
            })

        # Dormant wallet activation
        dormant_threshold = self.dormant_config.get('dormant_days_threshold', 30)
        activation_threshold = self.dormant_config.get('activation_transactions', 5)

        if len(transactions) >= activation_threshold:
            # Check for long gap followed by recent activity
            sorted_txns = sorted(
                transactions,
                key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
            )

            if len(sorted_txns) > 1:
                # Find largest gap
                max_gap = timedelta(0)
                for i in range(1, len(sorted_txns)):
                    prev_time = datetime.fromisoformat(sorted_txns[i-1]['timestamp'])
                    curr_time = datetime.fromisoformat(sorted_txns[i]['timestamp'])
                    gap = curr_time - prev_time
                    max_gap = max(max_gap, gap)

                if max_gap > timedelta(days=dormant_threshold):
                    # Check if recent activity follows dormant period
                    recent_txns = [
                        txn for txn in sorted_txns
                        if datetime.fromisoformat(txn['timestamp']) > datetime.utcnow() - timedelta(days=7)
                    ]

                    if len(recent_txns) >= activation_threshold:
                        suspicious_behaviors.append({
                            'behavior_type': 'dormant_activation',
                            'severity': 0.8,
                            'description': f"Dormant wallet activated after {max_gap.days} days",
                            'evidence': {
                                'dormant_period_days': max_gap.days,
                                'recent_transaction_count': len(recent_txns),
                                'activation_velocity': len(recent_txns) / 7
                            }
                        })

        return suspicious_behaviors

    async def _calculate_overall_transaction_risk(
        self,
        velocity_metrics: VelocityMetrics,
        pattern_metrics: PatternMetrics,
        suspicious_behaviors: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall transaction risk score"""
        risk_components = []

        # Velocity risk
        velocity_risk = min(abs(velocity_metrics.velocity_z_score) / 5.0, 1.0)
        risk_components.append(('velocity', velocity_risk, 0.3))

        # Pattern risk (high consistency + regularity = higher risk)
        pattern_risk = (pattern_metrics.pattern_consistency + pattern_metrics.timing_regularity) / 2
        if pattern_risk > 0.8:
            pattern_risk *= 1.5  # Amplify very regular patterns
        risk_components.append(('pattern', min(pattern_risk, 1.0), 0.2))

        # Diversity risk (low diversity = higher risk)
        diversity_risk = 1.0 - ((pattern_metrics.counterparty_diversity + pattern_metrics.asset_diversity) / 2)
        risk_components.append(('diversity', diversity_risk, 0.2))

        # Suspicious behavior risk
        if suspicious_behaviors:
            behavior_risk = max(behavior['severity'] for behavior in suspicious_behaviors)
        else:
            behavior_risk = 0
        risk_components.append(('suspicious', behavior_risk, 0.3))

        # Calculate weighted risk score
        weighted_risk = sum(score * weight for _, score, weight in risk_components)

        return min(weighted_risk, 1.0)

    def _empty_analysis_result(self) -> Dict[str, Any]:
        """Return empty analysis result structure"""
        return {
            'velocity_metrics': VelocityMetrics(0, 0, 0, 0, 0),
            'pattern_metrics': PatternMetrics(0, 0, {}, 0, 0),
            'suspicious_behaviors': [],
            'overall_risk_score': 0.0,
            'analysis_timestamp': datetime.utcnow(),
            'transaction_count': 0
        }