"""
Anomaly Detection for Blockchain Risk Assessment

ML-based pattern anomaly detection for blockchain transactions and behaviors.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import statistics
from enum import Enum
from collections import defaultdict, deque
import json

from ..models.blockchain_risk import RiskLevel, RiskAlert


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    STATISTICAL = "statistical"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    VOLUME = "volume"
    FREQUENCY = "frequency"
    PATTERN = "pattern"


@dataclass
class AnomalyScore:
    """Anomaly score and metadata"""
    score: float
    anomaly_type: AnomalyType
    confidence: float
    deviation_magnitude: float
    baseline_reference: float
    evidence: Dict[str, Any]
    detection_method: str


@dataclass
class TimeSeriesPoint:
    """Time series data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = None


class AnomalyDetector:
    """Advanced anomaly detection system for blockchain risk assessment"""

    def __init__(self, sensitivity: float = 2.5):
        self.sensitivity = sensitivity  # Z-score threshold for anomaly detection
        self.baseline_window = timedelta(days=30)
        self.detection_models = {}
        self.feature_extractors = {}
        self.historical_baselines = {}

    async def detect_transaction_anomalies(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]],
        analysis_window: timedelta = timedelta(days=7)
    ) -> List[AnomalyScore]:
        """
        Detect transaction anomalies for a wallet

        Args:
            wallet_address: Wallet address to analyze
            transactions: Transaction history
            analysis_window: Window for anomaly detection

        Returns:
            List of detected anomalies with scores
        """
        anomalies = []

        # Extract time series features
        features = await self._extract_transaction_features(transactions)

        # Detect different types of anomalies
        statistical_anomalies = await self._detect_statistical_anomalies(features)
        anomalies.extend(statistical_anomalies)

        temporal_anomalies = await self._detect_temporal_anomalies(features)
        anomalies.extend(temporal_anomalies)

        volume_anomalies = await self._detect_volume_anomalies(features)
        anomalies.extend(volume_anomalies)

        frequency_anomalies = await self._detect_frequency_anomalies(features)
        anomalies.extend(frequency_anomalies)

        behavioral_anomalies = await self._detect_behavioral_anomalies(features)
        anomalies.extend(behavioral_anomalies)

        # Filter and rank anomalies
        significant_anomalies = [
            anomaly for anomaly in anomalies
            if anomaly.score > 0.5 and anomaly.confidence > 0.6
        ]

        return sorted(significant_anomalies, key=lambda x: x.score, reverse=True)

    async def _extract_transaction_features(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, List[TimeSeriesPoint]]:
        """Extract time series features from transactions"""
        features = {
            'transaction_volume': [],
            'transaction_count': [],
            'gas_usage': [],
            'fee_amounts': [],
            'counterparty_diversity': [],
            'asset_diversity': [],
            'application_usage': []
        }

        if not transactions:
            return features

        # Group transactions by time windows (daily)
        daily_groups = defaultdict(list)
        for txn in transactions:
            timestamp = datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))
            date_key = timestamp.date()
            daily_groups[date_key].append(txn)

        # Extract daily features
        for date, daily_txns in daily_groups.items():
            timestamp = datetime.combine(date, datetime.min.time())

            # Volume features
            total_volume = sum(float(txn.get('amount', 0)) for txn in daily_txns)
            features['transaction_volume'].append(
                TimeSeriesPoint(timestamp, total_volume, {'count': len(daily_txns)})
            )

            # Count features
            features['transaction_count'].append(
                TimeSeriesPoint(timestamp, len(daily_txns))
            )

            # Gas usage features
            total_gas = sum(int(txn.get('gas-used', 0)) for txn in daily_txns)
            features['gas_usage'].append(
                TimeSeriesPoint(timestamp, total_gas)
            )

            # Fee features
            total_fees = sum(float(txn.get('fee', 0)) for txn in daily_txns)
            features['fee_amounts'].append(
                TimeSeriesPoint(timestamp, total_fees)
            )

            # Counterparty diversity
            counterparties = set()
            for txn in daily_txns:
                counterparties.add(txn.get('sender', ''))
                counterparties.add(txn.get('receiver', ''))
            features['counterparty_diversity'].append(
                TimeSeriesPoint(timestamp, len(counterparties))
            )

            # Asset diversity
            assets = set(txn.get('asset-id', 0) for txn in daily_txns)
            features['asset_diversity'].append(
                TimeSeriesPoint(timestamp, len(assets))
            )

            # Application usage
            apps = set(txn.get('application-id', 0) for txn in daily_txns if txn.get('application-id'))
            features['application_usage'].append(
                TimeSeriesPoint(timestamp, len(apps))
            )

        return features

    async def _detect_statistical_anomalies(
        self,
        features: Dict[str, List[TimeSeriesPoint]]
    ) -> List[AnomalyScore]:
        """Detect statistical anomalies using z-score analysis"""
        anomalies = []

        for feature_name, time_series in features.items():
            if len(time_series) < 7:  # Need minimum data points
                continue

            values = [point.value for point in time_series]

            # Calculate baseline statistics
            mean_value = statistics.mean(values)
            std_value = statistics.stdev(values) if len(values) > 1 else 0

            if std_value == 0:  # No variation
                continue

            # Detect outliers using z-score
            for i, point in enumerate(time_series):
                z_score = abs((point.value - mean_value) / std_value)

                if z_score > self.sensitivity:
                    anomaly_score = min(z_score / 5.0, 1.0)  # Normalize to 0-1
                    confidence = min(z_score / 3.0, 1.0)

                    anomaly = AnomalyScore(
                        score=anomaly_score,
                        anomaly_type=AnomalyType.STATISTICAL,
                        confidence=confidence,
                        deviation_magnitude=z_score,
                        baseline_reference=mean_value,
                        evidence={
                            'feature': feature_name,
                            'value': point.value,
                            'mean': mean_value,
                            'std': std_value,
                            'z_score': z_score,
                            'timestamp': point.timestamp.isoformat()
                        },
                        detection_method="Z-Score Analysis"
                    )
                    anomalies.append(anomaly)

        return anomalies

    async def _detect_temporal_anomalies(
        self,
        features: Dict[str, List[TimeSeriesPoint]]
    ) -> List[AnomalyScore]:
        """Detect temporal pattern anomalies"""
        anomalies = []

        for feature_name, time_series in features.items():
            if len(time_series) < 14:  # Need at least 2 weeks of data
                continue

            # Analyze day-of-week patterns
            weekday_patterns = defaultdict(list)
            for point in time_series:
                weekday = point.timestamp.weekday()
                weekday_patterns[weekday].append(point.value)

            # Calculate expected values for each weekday
            weekday_means = {}
            for weekday, values in weekday_patterns.items():
                if len(values) >= 2:
                    weekday_means[weekday] = statistics.mean(values)

            # Detect deviations from weekday patterns
            for point in time_series[-7:]:  # Check last week
                weekday = point.timestamp.weekday()
                if weekday in weekday_means:
                    expected = weekday_means[weekday]
                    if expected > 0:
                        deviation_ratio = abs(point.value - expected) / expected

                        if deviation_ratio > 2.0:  # 200% deviation
                            anomaly_score = min(deviation_ratio / 5.0, 1.0)
                            confidence = 0.7

                            anomaly = AnomalyScore(
                                score=anomaly_score,
                                anomaly_type=AnomalyType.TEMPORAL,
                                confidence=confidence,
                                deviation_magnitude=deviation_ratio,
                                baseline_reference=expected,
                                evidence={
                                    'feature': feature_name,
                                    'value': point.value,
                                    'expected_weekday_value': expected,
                                    'weekday': weekday,
                                    'deviation_ratio': deviation_ratio,
                                    'timestamp': point.timestamp.isoformat()
                                },
                                detection_method="Temporal Pattern Analysis"
                            )
                            anomalies.append(anomaly)

        return anomalies

    async def _detect_volume_anomalies(
        self,
        features: Dict[str, List[TimeSeriesPoint]]
    ) -> List[AnomalyScore]:
        """Detect volume-based anomalies"""
        anomalies = []

        volume_features = ['transaction_volume', 'gas_usage', 'fee_amounts']

        for feature_name in volume_features:
            if feature_name not in features:
                continue

            time_series = features[feature_name]
            if len(time_series) < 5:
                continue

            values = [point.value for point in time_series]

            # Use percentile-based detection for volume spikes
            if len(values) >= 10:
                p95 = np.percentile(values, 95)
                p50 = np.percentile(values, 50)

                # Check recent values
                for point in time_series[-3:]:  # Last 3 data points
                    if point.value > p95 and p50 > 0:
                        spike_ratio = point.value / p50

                        if spike_ratio > 5.0:  # 5x median
                            anomaly_score = min(np.log(spike_ratio) / 3.0, 1.0)
                            confidence = 0.8

                            anomaly = AnomalyScore(
                                score=anomaly_score,
                                anomaly_type=AnomalyType.VOLUME,
                                confidence=confidence,
                                deviation_magnitude=spike_ratio,
                                baseline_reference=p50,
                                evidence={
                                    'feature': feature_name,
                                    'value': point.value,
                                    'median_baseline': p50,
                                    'p95_threshold': p95,
                                    'spike_ratio': spike_ratio,
                                    'timestamp': point.timestamp.isoformat()
                                },
                                detection_method="Volume Spike Detection"
                            )
                            anomalies.append(anomaly)

        return anomalies

    async def _detect_frequency_anomalies(
        self,
        features: Dict[str, List[TimeSeriesPoint]]
    ) -> List[AnomalyScore]:
        """Detect frequency-based anomalies"""
        anomalies = []

        if 'transaction_count' not in features:
            return anomalies

        time_series = features['transaction_count']
        if len(time_series) < 7:
            return anomalies

        values = [point.value for point in time_series]

        # Detect sudden frequency changes
        if len(values) >= 14:
            # Compare recent period to historical baseline
            recent_period = values[-7:]  # Last week
            baseline_period = values[-21:-7]  # Previous 2 weeks

            if baseline_period:
                recent_avg = statistics.mean(recent_period)
                baseline_avg = statistics.mean(baseline_period)

                if baseline_avg > 0:
                    frequency_ratio = recent_avg / baseline_avg

                    # Detect significant increases or decreases
                    if frequency_ratio > 3.0 or frequency_ratio < 0.3:
                        anomaly_score = min(abs(np.log(frequency_ratio)) / 2.0, 1.0)
                        confidence = 0.75

                        anomaly = AnomalyScore(
                            score=anomaly_score,
                            anomaly_type=AnomalyType.FREQUENCY,
                            confidence=confidence,
                            deviation_magnitude=frequency_ratio,
                            baseline_reference=baseline_avg,
                            evidence={
                                'recent_avg_frequency': recent_avg,
                                'baseline_avg_frequency': baseline_avg,
                                'frequency_ratio': frequency_ratio,
                                'change_type': 'increase' if frequency_ratio > 1 else 'decrease'
                            },
                            detection_method="Frequency Change Detection"
                        )
                        anomalies.append(anomaly)

        return anomalies

    async def _detect_behavioral_anomalies(
        self,
        features: Dict[str, List[TimeSeriesPoint]]
    ) -> List[AnomalyScore]:
        """Detect behavioral pattern anomalies"""
        anomalies = []

        # Analyze diversity patterns
        diversity_features = ['counterparty_diversity', 'asset_diversity', 'application_usage']

        for feature_name in diversity_features:
            if feature_name not in features:
                continue

            time_series = features[feature_name]
            if len(time_series) < 10:
                continue

            values = [point.value for point in time_series]

            # Detect sudden drops in diversity (potential consolidation behavior)
            if len(values) >= 14:
                recent_values = values[-7:]
                baseline_values = values[-21:-7]

                if baseline_values:
                    recent_avg = statistics.mean(recent_values)
                    baseline_avg = statistics.mean(baseline_values)

                    if baseline_avg > 0:
                        diversity_ratio = recent_avg / baseline_avg

                        # Detect significant drops in diversity
                        if diversity_ratio < 0.5:  # 50% drop
                            anomaly_score = min((0.5 - diversity_ratio) * 2, 1.0)
                            confidence = 0.7

                            anomaly = AnomalyScore(
                                score=anomaly_score,
                                anomaly_type=AnomalyType.BEHAVIORAL,
                                confidence=confidence,
                                deviation_magnitude=1 - diversity_ratio,
                                baseline_reference=baseline_avg,
                                evidence={
                                    'feature': feature_name,
                                    'recent_diversity': recent_avg,
                                    'baseline_diversity': baseline_avg,
                                    'diversity_ratio': diversity_ratio,
                                    'behavior_change': 'consolidation'
                                },
                                detection_method="Behavioral Pattern Analysis"
                            )
                            anomalies.append(anomaly)

        return anomalies

    async def detect_network_anomalies(
        self,
        network_metrics: Dict[str, List[TimeSeriesPoint]]
    ) -> List[AnomalyScore]:
        """Detect network-wide anomalies"""
        anomalies = []

        # Analyze network-level patterns
        for metric_name, time_series in network_metrics.items():
            if len(time_series) < 20:
                continue

            # Use exponential smoothing for trend detection
            smoothed_values = self._exponential_smoothing(
                [point.value for point in time_series],
                alpha=0.3
            )

            # Detect trend changes
            trend_anomalies = await self._detect_trend_anomalies(
                time_series, smoothed_values, metric_name
            )
            anomalies.extend(trend_anomalies)

        return anomalies

    def _exponential_smoothing(self, values: List[float], alpha: float = 0.3) -> List[float]:
        """Apply exponential smoothing to time series"""
        if not values:
            return []

        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed_value = alpha * values[i] + (1 - alpha) * smoothed[i-1]
            smoothed.append(smoothed_value)

        return smoothed

    async def _detect_trend_anomalies(
        self,
        time_series: List[TimeSeriesPoint],
        smoothed_values: List[float],
        metric_name: str
    ) -> List[AnomalyScore]:
        """Detect anomalies in trends"""
        anomalies = []

        if len(smoothed_values) < 10:
            return anomalies

        # Calculate trend slopes
        window_size = 5
        for i in range(window_size, len(smoothed_values)):
            recent_slope = self._calculate_slope(
                smoothed_values[i-window_size:i]
            )

            # Compare to historical slopes
            historical_slopes = []
            for j in range(window_size, i-window_size):
                slope = self._calculate_slope(
                    smoothed_values[j-window_size:j]
                )
                historical_slopes.append(slope)

            if historical_slopes:
                mean_slope = statistics.mean(historical_slopes)
                std_slope = statistics.stdev(historical_slopes) if len(historical_slopes) > 1 else 0

                if std_slope > 0:
                    slope_z_score = abs((recent_slope - mean_slope) / std_slope)

                    if slope_z_score > 3.0:
                        anomaly_score = min(slope_z_score / 5.0, 1.0)
                        confidence = 0.8

                        anomaly = AnomalyScore(
                            score=anomaly_score,
                            anomaly_type=AnomalyType.PATTERN,
                            confidence=confidence,
                            deviation_magnitude=slope_z_score,
                            baseline_reference=mean_slope,
                            evidence={
                                'metric': metric_name,
                                'recent_slope': recent_slope,
                                'mean_historical_slope': mean_slope,
                                'slope_z_score': slope_z_score,
                                'timestamp': time_series[i].timestamp.isoformat()
                            },
                            detection_method="Trend Anomaly Detection"
                        )
                        anomalies.append(anomaly)

        return anomalies

    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate slope of values using linear regression"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        y = values

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def create_anomaly_alert(
        self,
        wallet_address: str,
        anomaly: AnomalyScore
    ) -> RiskAlert:
        """Create an alert from detected anomaly"""
        severity = RiskLevel.HIGH if anomaly.score > 0.8 else RiskLevel.MODERATE

        return RiskAlert(
            alert_id=f"anomaly_{wallet_address}_{datetime.utcnow().timestamp()}",
            alert_type=f"ANOMALY_{anomaly.anomaly_type.value.upper()}",
            severity=severity,
            title=f"Anomaly Detected: {anomaly.anomaly_type.value.replace('_', ' ').title()}",
            description=f"Detected {anomaly.anomaly_type.value} anomaly with score {anomaly.score:.2f}",
            affected_addresses=[wallet_address],
            affected_protocols=[],
            risk_score=anomaly.score,
            confidence=anomaly.confidence,
            detection_method=anomaly.detection_method,
            evidence=anomaly.evidence,
            recommendations=[
                "Investigate recent transaction patterns",
                "Monitor for continued anomalous behavior",
                "Review account security measures",
                "Consider enhanced verification procedures"
            ]
        )

    def update_baseline(
        self,
        feature_name: str,
        time_series: List[TimeSeriesPoint]
    ) -> None:
        """Update baseline statistics for a feature"""
        if len(time_series) < 10:
            return

        values = [point.value for point in time_series]

        self.historical_baselines[feature_name] = {
            'mean': statistics.mean(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0,
            'median': statistics.median(values),
            'p95': np.percentile(values, 95),
            'p05': np.percentile(values, 5),
            'last_updated': datetime.utcnow()
        }