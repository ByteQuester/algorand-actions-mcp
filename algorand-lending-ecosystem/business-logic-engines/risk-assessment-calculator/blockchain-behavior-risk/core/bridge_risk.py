"""
Bridge Risk Analyzer

Specialized analyzer for cross-chain bridge risk patterns,
unusual activity detection, and concentration risk assessment.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import logging

from ...common.models.blockchain_risk import RiskLevel


@dataclass
class BridgeRiskMetrics:
    """Bridge activity risk metrics"""
    volume_risk: float
    frequency_risk: float
    concentration_risk: float
    pattern_risk: float
    overall_risk: float
    risk_indicators: List[str]


class BridgeRiskAnalyzer:
    """Specialized cross-chain bridge risk analyzer"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.bridge_config = config.get('risk_assessment', {}).get('bridge_risk', {})

    async def analyze_bridge_risk_patterns(
        self,
        wallet_address: str,
        bridge_activities: List[Dict[str, Any]]
    ) -> BridgeRiskMetrics:
        """Analyze bridge activity patterns for risk assessment"""
        try:
            if not bridge_activities:
                return BridgeRiskMetrics(0, 0, 0, 0, 0, [])

            # Analyze volume patterns
            volume_risk = await self._analyze_volume_risk(bridge_activities)

            # Analyze frequency patterns
            frequency_risk = await self._analyze_frequency_risk(bridge_activities)

            # Analyze concentration risk
            concentration_risk = await self._analyze_concentration_risk(bridge_activities)

            # Analyze behavioral patterns
            pattern_risk = await self._analyze_pattern_risk(bridge_activities)

            # Calculate overall risk
            overall_risk = self._calculate_overall_bridge_risk(
                volume_risk, frequency_risk, concentration_risk, pattern_risk
            )

            # Generate risk indicators
            risk_indicators = self._generate_risk_indicators(
                bridge_activities, volume_risk, frequency_risk, concentration_risk, pattern_risk
            )

            return BridgeRiskMetrics(
                volume_risk=volume_risk,
                frequency_risk=frequency_risk,
                concentration_risk=concentration_risk,
                pattern_risk=pattern_risk,
                overall_risk=overall_risk,
                risk_indicators=risk_indicators
            )

        except Exception as e:
            self.logger.error(f"Bridge risk analysis failed for {wallet_address}: {e}")
            return BridgeRiskMetrics(0, 0, 0, 0, 0, [])

    async def _analyze_volume_risk(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze volume-based risks"""
        if not activities:
            return 0.0

        volumes = [float(activity.get('amount', 0)) for activity in activities]

        # Calculate daily volumes
        daily_volumes = defaultdict(float)
        for activity in activities:
            timestamp = datetime.fromisoformat(activity.get('timestamp', '1970-01-01'))
            date_key = timestamp.date()
            daily_volumes[date_key] += float(activity.get('amount', 0))

        if not daily_volumes:
            return 0.0

        daily_volume_list = list(daily_volumes.values())

        # Calculate baseline statistics
        if len(daily_volume_list) > 7:
            baseline_volumes = daily_volume_list[:-3]  # Exclude last 3 days
            recent_volumes = daily_volume_list[-3:]   # Last 3 days

            if baseline_volumes:
                baseline_mean = statistics.mean(baseline_volumes)
                baseline_std = statistics.stdev(baseline_volumes) if len(baseline_volumes) > 1 else baseline_mean * 0.1

                # Check for volume spikes
                volume_risk = 0.0
                spike_threshold = self.bridge_config.get('activity_monitoring', {}).get('volume_spike_threshold', 5.0)

                for recent_volume in recent_volumes:
                    if baseline_std > 0:
                        z_score = (recent_volume - baseline_mean) / baseline_std
                        if z_score > spike_threshold:
                            spike_risk = min(z_score / (spike_threshold * 2), 1.0)
                            volume_risk = max(volume_risk, spike_risk)

                return volume_risk
        else:
            # Not enough data for meaningful analysis
            max_volume = max(volumes) if volumes else 0
            if max_volume > 1000000:  # $1M threshold
                return 0.3
            return 0.0

        return 0.0

    async def _analyze_frequency_risk(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze frequency-based risks"""
        if not activities:
            return 0.0

        # Calculate daily frequencies
        daily_counts = defaultdict(int)
        for activity in activities:
            timestamp = datetime.fromisoformat(activity.get('timestamp', '1970-01-01'))
            date_key = timestamp.date()
            daily_counts[date_key] += 1

        if not daily_counts:
            return 0.0

        daily_count_list = list(daily_counts.values())

        # Calculate baseline statistics
        if len(daily_count_list) > 7:
            baseline_counts = daily_count_list[:-3]  # Exclude last 3 days
            recent_counts = daily_count_list[-3:]   # Last 3 days

            if baseline_counts:
                baseline_mean = statistics.mean(baseline_counts)
                baseline_std = statistics.stdev(baseline_counts) if len(baseline_counts) > 1 else baseline_mean * 0.1

                # Check for frequency spikes
                frequency_risk = 0.0
                spike_threshold = self.bridge_config.get('activity_monitoring', {}).get('frequency_spike_threshold', 3.0)

                for recent_count in recent_counts:
                    if baseline_std > 0:
                        z_score = (recent_count - baseline_mean) / baseline_std
                        if z_score > spike_threshold:
                            spike_risk = min(z_score / (spike_threshold * 2), 1.0)
                            frequency_risk = max(frequency_risk, spike_risk)

                return frequency_risk
        else:
            # Check absolute frequency
            max_daily_count = max(daily_count_list) if daily_count_list else 0
            if max_daily_count > 50:  # More than 50 transactions per day
                return min(max_daily_count / 100, 1.0)
            return 0.0

        return 0.0

    async def _analyze_concentration_risk(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze concentration risks"""
        if not activities:
            return 0.0

        # Analyze time concentration
        time_concentration_risk = await self._analyze_time_concentration(activities)

        # Analyze bridge concentration
        bridge_concentration_risk = await self._analyze_bridge_concentration(activities)

        # Analyze asset concentration
        asset_concentration_risk = await self._analyze_asset_concentration(activities)

        # Return maximum concentration risk
        return max(time_concentration_risk, bridge_concentration_risk, asset_concentration_risk)

    async def _analyze_time_concentration(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze temporal concentration of activities"""
        if len(activities) < 5:
            return 0.0

        # Group activities by hour
        hourly_counts = defaultdict(int)
        total_daily_volume = defaultdict(float)

        for activity in activities:
            timestamp = datetime.fromisoformat(activity.get('timestamp', '1970-01-01'))
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
            date_key = timestamp.date()

            hourly_counts[hour_key] += 1
            total_daily_volume[date_key] += float(activity.get('amount', 0))

        # Check for high concentration in single hours
        for date, daily_volume in total_daily_volume.items():
            date_hours = [hour for hour in hourly_counts.keys() if hour.date() == date]
            date_activities = [activity for activity in activities
                             if datetime.fromisoformat(activity.get('timestamp', '1970-01-01')).date() == date]

            if len(date_activities) > 0:
                # Calculate volume in peak hour
                hourly_volumes = defaultdict(float)
                for activity in date_activities:
                    timestamp = datetime.fromisoformat(activity.get('timestamp', '1970-01-01'))
                    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                    hourly_volumes[hour_key] += float(activity.get('amount', 0))

                if hourly_volumes and daily_volume > 0:
                    max_hourly_volume = max(hourly_volumes.values())
                    concentration_ratio = max_hourly_volume / daily_volume

                    threshold = self.bridge_config.get('concentration_risk', {}).get('time_concentration_threshold', 0.5)
                    if concentration_ratio > threshold:
                        return min(concentration_ratio * 2, 1.0)

        return 0.0

    async def _analyze_bridge_concentration(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze concentration across different bridges"""
        bridge_usage = defaultdict(float)
        total_volume = 0

        for activity in activities:
            bridge_name = activity.get('bridge_name', 'unknown')
            volume = float(activity.get('amount', 0))
            bridge_usage[bridge_name] += volume
            total_volume += volume

        if total_volume == 0:
            return 0.0

        # Calculate concentration ratio for top bridge
        max_bridge_volume = max(bridge_usage.values()) if bridge_usage else 0
        concentration_ratio = max_bridge_volume / total_volume

        # High concentration in single bridge is risky
        if concentration_ratio > 0.8:
            return min(concentration_ratio * 1.25, 1.0)

        return 0.0

    async def _analyze_asset_concentration(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze concentration across different assets"""
        asset_usage = defaultdict(float)
        total_volume = 0

        for activity in activities:
            asset_symbol = activity.get('asset_symbol', 'unknown')
            volume = float(activity.get('amount', 0))
            asset_usage[asset_symbol] += volume
            total_volume += volume

        if total_volume == 0:
            return 0.0

        # Calculate concentration ratio for top asset
        max_asset_volume = max(asset_usage.values()) if asset_usage else 0
        concentration_ratio = max_asset_volume / total_volume

        # High concentration in single asset
        if concentration_ratio > 0.9:
            return min(concentration_ratio * 1.1, 1.0)

        return 0.0

    async def _analyze_pattern_risk(self, activities: List[Dict[str, Any]]) -> float:
        """Analyze suspicious patterns in bridge activities"""
        if len(activities) < 3:
            return 0.0

        pattern_risks = []

        # Check for round-trip patterns
        round_trip_risk = await self._detect_round_trip_patterns(activities)
        pattern_risks.append(round_trip_risk)

        # Check for identical amounts
        identical_amount_risk = await self._detect_identical_amounts(activities)
        pattern_risks.append(identical_amount_risk)

        # Check for rapid sequences
        rapid_sequence_risk = await self._detect_rapid_sequences(activities)
        pattern_risks.append(rapid_sequence_risk)

        return max(pattern_risks) if pattern_risks else 0.0

    async def _detect_round_trip_patterns(self, activities: List[Dict[str, Any]]) -> float:
        """Detect round-trip bridging patterns"""
        # Group by chains
        chain_pairs = defaultdict(list)

        for activity in activities:
            source = activity.get('source_chain', '')
            dest = activity.get('destination_chain', '')
            if source and dest:
                pair_key = tuple(sorted([source, dest]))
                chain_pairs[pair_key].append(activity)

        round_trip_risk = 0.0

        for pair, pair_activities in chain_pairs.items():
            if len(pair_activities) >= 4:  # At least 2 round trips
                # Sort by timestamp
                sorted_activities = sorted(
                    pair_activities,
                    key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
                )

                # Look for alternating patterns
                chain_sequence = [
                    (activity.get('source_chain'), activity.get('destination_chain'))
                    for activity in sorted_activities
                ]

                alternating_count = 0
                for i in range(1, len(chain_sequence)):
                    curr_source, curr_dest = chain_sequence[i]
                    prev_source, prev_dest = chain_sequence[i-1]

                    # Check if current transaction reverses previous one
                    if curr_source == prev_dest and curr_dest == prev_source:
                        alternating_count += 1

                if alternating_count >= 2:
                    risk = min(alternating_count / 5, 1.0)
                    round_trip_risk = max(round_trip_risk, risk)

        return round_trip_risk

    async def _detect_identical_amounts(self, activities: List[Dict[str, Any]]) -> float:
        """Detect suspicious identical amounts"""
        amounts = [float(activity.get('amount', 0)) for activity in activities]

        if len(amounts) < 3:
            return 0.0

        # Count identical amounts
        amount_counts = defaultdict(int)
        for amount in amounts:
            # Round to avoid floating point precision issues
            rounded_amount = round(amount, 2)
            amount_counts[rounded_amount] += 1

        # Find maximum repetition
        max_repetition = max(amount_counts.values()) if amount_counts else 0

        # High repetition is suspicious
        if max_repetition >= 5:
            return min(max_repetition / 10, 1.0)

        return 0.0

    async def _detect_rapid_sequences(self, activities: List[Dict[str, Any]]) -> float:
        """Detect rapid transaction sequences"""
        if len(activities) < 3:
            return 0.0

        # Sort by timestamp
        sorted_activities = sorted(
            activities,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        rapid_sequences = 0
        consecutive_rapid = 0

        for i in range(1, len(sorted_activities)):
            prev_time = datetime.fromisoformat(sorted_activities[i-1].get('timestamp', '1970-01-01'))
            curr_time = datetime.fromisoformat(sorted_activities[i].get('timestamp', '1970-01-01'))

            time_diff = (curr_time - prev_time).total_seconds()

            # Transactions within 60 seconds are considered rapid
            if time_diff < 60:
                consecutive_rapid += 1
            else:
                if consecutive_rapid >= 2:
                    rapid_sequences += 1
                consecutive_rapid = 0

        # Check final sequence
        if consecutive_rapid >= 2:
            rapid_sequences += 1

        # Calculate risk based on number of rapid sequences
        if rapid_sequences > 0:
            return min(rapid_sequences / 5, 1.0)

        return 0.0

    def _calculate_overall_bridge_risk(
        self,
        volume_risk: float,
        frequency_risk: float,
        concentration_risk: float,
        pattern_risk: float
    ) -> float:
        """Calculate overall bridge risk score"""
        # Weight different risk components
        weights = {
            'volume': 0.3,
            'frequency': 0.25,
            'concentration': 0.25,
            'pattern': 0.2
        }

        overall_risk = (
            volume_risk * weights['volume'] +
            frequency_risk * weights['frequency'] +
            concentration_risk * weights['concentration'] +
            pattern_risk * weights['pattern']
        )

        return min(overall_risk, 1.0)

    def _generate_risk_indicators(
        self,
        activities: List[Dict[str, Any]],
        volume_risk: float,
        frequency_risk: float,
        concentration_risk: float,
        pattern_risk: float
    ) -> List[str]:
        """Generate risk indicators based on analysis"""
        indicators = []

        if volume_risk > 0.5:
            indicators.append("Unusual volume spike detected in bridge activities")

        if frequency_risk > 0.5:
            indicators.append("Unusual frequency spike detected in bridge activities")

        if concentration_risk > 0.7:
            indicators.append("High concentration risk in bridge usage patterns")

        if pattern_risk > 0.6:
            indicators.append("Suspicious patterns detected in bridge activities")

        # Activity-specific indicators
        if len(activities) > 100:
            indicators.append(f"High bridge activity volume: {len(activities)} transactions")

        unique_bridges = len(set(activity.get('bridge_name', '') for activity in activities))
        if unique_bridges == 1 and len(activities) > 20:
            indicators.append("All bridge activities concentrated on single bridge")

        return indicators