"""
Transaction Anomaly Detection Engine

Detects unusual transaction patterns that may indicate risk:
- High frequency transaction bursts
- Unusual timing patterns
- Abnormal transaction amounts
- Suspicious recipient patterns
- Round-trip transaction analysis
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from collections import defaultdict, Counter

from .models import TransactionPattern, TransactionType, RiskLevel

logger = logging.getLogger(__name__)


class TransactionAnomalyDetector:
    """
    Detects anomalous transaction patterns that may indicate risk
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for transaction analysis"""
        return {
            'min_transactions_for_analysis': 10,
            'burst_detection_threshold': 5,  # Transactions per minute
            'timing_anomaly_std_threshold': 3.0,
            'amount_anomaly_std_threshold': 2.5,
            'round_trip_detection_window_minutes': 30,
            'suspicious_pattern_confidence_threshold': 0.7,
            'max_analysis_transactions': 10000
        }

    async def detect_anomalies(
        self,
        address: str,
        analysis_days: int
    ) -> List[TransactionPattern]:
        """
        Detect transaction anomalies for an address

        Args:
            address: Address to analyze
            analysis_days: Number of days to analyze

        Returns:
            List of detected transaction patterns
        """
        try:
            logger.info(f"Starting transaction anomaly detection for {address}")

            # Get transaction history
            transactions = await self._get_transaction_history(address, analysis_days)

            if len(transactions) < self.config['min_transactions_for_analysis']:
                logger.info(f"Insufficient transactions ({len(transactions)}) for analysis")
                return []

            # Run parallel anomaly detection
            detection_tasks = [
                self._detect_burst_patterns(transactions),
                self._detect_timing_anomalies(transactions),
                self._detect_amount_anomalies(transactions),
                self._detect_recipient_patterns(transactions),
                self._detect_round_trip_patterns(transactions),
                self._detect_app_interaction_anomalies(transactions),
                self._detect_asset_manipulation_patterns(transactions)
            ]

            anomaly_results = await asyncio.gather(*detection_tasks, return_exceptions=True)

            # Consolidate all detected patterns
            all_patterns = []
            for result in anomaly_results:
                if isinstance(result, list):
                    all_patterns.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Anomaly detection error: {result}")

            # Filter and rank patterns by confidence
            significant_patterns = [
                p for p in all_patterns
                if p.confidence_score >= self.config['suspicious_pattern_confidence_threshold']
            ]

            logger.info(f"Detected {len(significant_patterns)} significant transaction patterns")
            return sorted(significant_patterns, key=lambda x: x.confidence_score, reverse=True)

        except Exception as e:
            logger.error(f"Error in transaction anomaly detection: {e}")
            raise

    async def _detect_burst_patterns(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect high-frequency transaction bursts"""
        patterns = []

        try:
            # Group transactions by time windows (1-minute intervals)
            time_buckets = defaultdict(list)
            for txn in transactions:
                timestamp = datetime.fromisoformat(txn['confirmed_time'])
                bucket_key = timestamp.replace(second=0, microsecond=0)
                time_buckets[bucket_key].append(txn)

            # Find burst patterns
            burst_threshold = self.config['burst_detection_threshold']
            for time_bucket, txns in time_buckets.items():
                if len(txns) >= burst_threshold:
                    # Analyze burst characteristics
                    burst_volume = sum(txn.get('amount', 0) for txn in txns)
                    unique_recipients = len(set(txn.get('receiver', '') for txn in txns))
                    avg_amount = burst_volume / len(txns) if len(txns) > 0 else 0

                    # Calculate risk indicators
                    risk_indicators = []
                    if len(txns) > burst_threshold * 2:
                        risk_indicators.append("extreme_frequency")
                    if unique_recipients == 1:
                        risk_indicators.append("single_recipient_burst")
                    if unique_recipients > len(txns) * 0.8:
                        risk_indicators.append("spray_pattern")

                    # Calculate confidence based on deviation from normal
                    confidence = min(len(txns) / (burst_threshold * 3), 1.0)

                    pattern = TransactionPattern(
                        pattern_type="high_frequency_burst",
                        frequency=len(txns),
                        time_window_hours=1/60,  # 1 minute
                        addresses_involved=[txn.get('receiver', '') for txn in txns],
                        total_algo_volume=burst_volume / 1_000_000,  # Convert microALGOs
                        avg_transaction_size=avg_amount / 1_000_000,
                        risk_indicators=risk_indicators,
                        confidence_score=confidence,
                        first_seen=time_bucket,
                        last_seen=time_bucket
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in burst pattern detection: {e}")

        return patterns

    async def _detect_timing_anomalies(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect unusual timing patterns in transactions"""
        patterns = []

        try:
            if len(transactions) < 10:
                return patterns

            # Calculate time intervals between consecutive transactions
            timestamps = [datetime.fromisoformat(txn['confirmed_time']) for txn in transactions]
            timestamps.sort()

            intervals = []
            for i in range(1, len(timestamps)):
                interval_seconds = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval_seconds)

            if not intervals:
                return patterns

            # Statistical analysis of intervals
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            threshold = self.config['timing_anomaly_std_threshold']

            # Detect regular timing patterns (potential automation)
            interval_counter = Counter([round(interval) for interval in intervals])
            most_common_intervals = interval_counter.most_common(3)

            for interval, count in most_common_intervals:
                if count >= len(intervals) * 0.3:  # 30% of transactions have same interval
                    risk_indicators = ["regular_timing_pattern"]
                    if interval < 60:  # Less than 1 minute
                        risk_indicators.append("automated_execution")

                    confidence = min(count / len(intervals), 1.0)

                    pattern = TransactionPattern(
                        pattern_type="regular_timing_pattern",
                        frequency=count,
                        time_window_hours=len(intervals) * interval / 3600,
                        addresses_involved=[],
                        total_algo_volume=0,
                        avg_transaction_size=0,
                        risk_indicators=risk_indicators,
                        confidence_score=confidence,
                        first_seen=timestamps[0],
                        last_seen=timestamps[-1]
                    )
                    patterns.append(pattern)

            # Detect unusually fast sequences
            fast_sequences = []
            for i, interval in enumerate(intervals):
                if interval < mean_interval - (threshold * std_interval) and interval < 10:  # Very fast
                    fast_sequences.append(i)

            if len(fast_sequences) > len(intervals) * 0.1:  # 10% are unusually fast
                pattern = TransactionPattern(
                    pattern_type="unusually_fast_sequence",
                    frequency=len(fast_sequences),
                    time_window_hours=(timestamps[-1] - timestamps[0]).total_seconds() / 3600,
                    addresses_involved=[],
                    total_algo_volume=0,
                    avg_transaction_size=0,
                    risk_indicators=["rapid_execution", "potential_automation"],
                    confidence_score=min(len(fast_sequences) / (len(intervals) * 0.2), 1.0),
                    first_seen=timestamps[0],
                    last_seen=timestamps[-1]
                )
                patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in timing anomaly detection: {e}")

        return patterns

    async def _detect_amount_anomalies(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect unusual transaction amount patterns"""
        patterns = []

        try:
            amounts = [txn.get('amount', 0) for txn in transactions if txn.get('amount', 0) > 0]

            if len(amounts) < 5:
                return patterns

            # Statistical analysis
            amounts_algo = [amt / 1_000_000 for amt in amounts]  # Convert to ALGO
            mean_amount = np.mean(amounts_algo)
            std_amount = np.std(amounts_algo)
            threshold = self.config['amount_anomaly_std_threshold']

            # Detect outlier amounts
            outliers = []
            for i, amount in enumerate(amounts_algo):
                if abs(amount - mean_amount) > threshold * std_amount:
                    outliers.append((i, amount))

            if outliers and len(outliers) > len(amounts) * 0.05:  # 5% are outliers
                outlier_amounts = [amount for _, amount in outliers]
                risk_indicators = []

                if max(outlier_amounts) > mean_amount * 10:
                    risk_indicators.append("extremely_large_transactions")
                if min(outlier_amounts) < mean_amount * 0.01:
                    risk_indicators.append("dust_transactions")

                pattern = TransactionPattern(
                    pattern_type="amount_outliers",
                    frequency=len(outliers),
                    time_window_hours=24,  # Assume daily analysis
                    addresses_involved=[],
                    total_algo_volume=sum(outlier_amounts),
                    avg_transaction_size=np.mean(outlier_amounts),
                    risk_indicators=risk_indicators,
                    confidence_score=min(len(outliers) / (len(amounts) * 0.1), 1.0),
                    first_seen=datetime.utcnow() - timedelta(days=1),
                    last_seen=datetime.utcnow()
                )
                patterns.append(pattern)

            # Detect round number patterns (potential artificial amounts)
            round_amounts = []
            for amount in amounts_algo:
                if amount == round(amount) and amount >= 1:  # Round ALGOs
                    round_amounts.append(amount)

            if len(round_amounts) > len(amounts) * 0.7:  # 70% are round numbers
                pattern = TransactionPattern(
                    pattern_type="round_amount_pattern",
                    frequency=len(round_amounts),
                    time_window_hours=24,
                    addresses_involved=[],
                    total_algo_volume=sum(round_amounts),
                    avg_transaction_size=np.mean(round_amounts),
                    risk_indicators=["artificial_amounts", "potential_automation"],
                    confidence_score=len(round_amounts) / len(amounts),
                    first_seen=datetime.utcnow() - timedelta(days=1),
                    last_seen=datetime.utcnow()
                )
                patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in amount anomaly detection: {e}")

        return patterns

    async def _detect_recipient_patterns(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect suspicious recipient patterns"""
        patterns = []

        try:
            recipients = [txn.get('receiver', '') for txn in transactions if txn.get('receiver')]
            if not recipients:
                return patterns

            recipient_counts = Counter(recipients)

            # Detect concentration risk
            total_transactions = len(recipients)
            top_recipients = recipient_counts.most_common(5)

            for recipient, count in top_recipients:
                concentration = count / total_transactions
                if concentration > 0.5:  # More than 50% to one recipient
                    risk_indicators = ["high_concentration"]
                    if concentration > 0.8:
                        risk_indicators.append("extreme_concentration")

                    pattern = TransactionPattern(
                        pattern_type="recipient_concentration",
                        frequency=count,
                        time_window_hours=24,
                        addresses_involved=[recipient],
                        total_algo_volume=0,  # Would need to calculate
                        avg_transaction_size=0,
                        risk_indicators=risk_indicators,
                        confidence_score=concentration,
                        first_seen=datetime.utcnow() - timedelta(days=1),
                        last_seen=datetime.utcnow()
                    )
                    patterns.append(pattern)

            # Detect spray patterns (many unique recipients)
            unique_recipients = len(set(recipients))
            if unique_recipients > total_transactions * 0.8:  # 80% unique recipients
                pattern = TransactionPattern(
                    pattern_type="spray_pattern",
                    frequency=unique_recipients,
                    time_window_hours=24,
                    addresses_involved=list(set(recipients)),
                    total_algo_volume=0,
                    avg_transaction_size=0,
                    risk_indicators=["spray_distribution", "potential_money_laundering"],
                    confidence_score=unique_recipients / total_transactions,
                    first_seen=datetime.utcnow() - timedelta(days=1),
                    last_seen=datetime.utcnow()
                )
                patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in recipient pattern detection: {e}")

        return patterns

    async def _detect_round_trip_patterns(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect round-trip transaction patterns (A->B->A)"""
        patterns = []

        try:
            window_minutes = self.config['round_trip_detection_window_minutes']

            # Group transactions by time windows
            for i, txn in enumerate(transactions):
                if not txn.get('receiver'):
                    continue

                txn_time = datetime.fromisoformat(txn['confirmed_time'])
                potential_returns = []

                # Look for return transactions within the window
                for j, other_txn in enumerate(transactions[i+1:], i+1):
                    other_time = datetime.fromisoformat(other_txn['confirmed_time'])
                    time_diff = (other_time - txn_time).total_seconds() / 60

                    if time_diff > window_minutes:
                        break

                    # Check if it's a return transaction
                    if (other_txn.get('sender') == txn.get('receiver') and
                        other_txn.get('receiver') == txn.get('sender')):
                        potential_returns.append((j, other_txn, time_diff))

                if potential_returns:
                    # Calculate pattern characteristics
                    avg_return_time = np.mean([time_diff for _, _, time_diff in potential_returns])
                    total_volume = txn.get('amount', 0) + sum(ret_txn.get('amount', 0) for _, ret_txn, _ in potential_returns)

                    risk_indicators = ["round_trip_detected"]
                    if avg_return_time < 5:  # Very fast return
                        risk_indicators.append("rapid_round_trip")
                    if len(potential_returns) > 1:
                        risk_indicators.append("multiple_round_trips")

                    pattern = TransactionPattern(
                        pattern_type="round_trip_pattern",
                        frequency=len(potential_returns) + 1,
                        time_window_hours=avg_return_time / 60,
                        addresses_involved=[txn.get('receiver', ''), txn.get('sender', '')],
                        total_algo_volume=total_volume / 1_000_000,
                        avg_transaction_size=(total_volume / (len(potential_returns) + 1)) / 1_000_000,
                        risk_indicators=risk_indicators,
                        confidence_score=min(len(potential_returns) / 3, 1.0),
                        first_seen=txn_time,
                        last_seen=datetime.fromisoformat(potential_returns[-1][1]['confirmed_time'])
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in round-trip pattern detection: {e}")

        return patterns

    async def _detect_app_interaction_anomalies(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect unusual application interaction patterns"""
        patterns = []

        try:
            app_calls = [txn for txn in transactions if txn.get('tx_type') == 'appl']
            if len(app_calls) < 5:
                return patterns

            # Analyze application interaction patterns
            app_ids = [txn.get('application_id', 0) for txn in app_calls]
            app_counts = Counter(app_ids)

            # Detect high-frequency app interactions
            for app_id, count in app_counts.items():
                if count > len(app_calls) * 0.6:  # 60% of app calls to one app
                    risk_indicators = ["high_app_concentration"]

                    # Check for rapid-fire calls
                    app_txns = [txn for txn in app_calls if txn.get('application_id') == app_id]
                    times = [datetime.fromisoformat(txn['confirmed_time']) for txn in app_txns]
                    times.sort()

                    rapid_calls = 0
                    for i in range(1, len(times)):
                        if (times[i] - times[i-1]).total_seconds() < 10:  # Within 10 seconds
                            rapid_calls += 1

                    if rapid_calls > count * 0.5:
                        risk_indicators.append("rapid_app_calls")

                    pattern = TransactionPattern(
                        pattern_type="app_interaction_anomaly",
                        frequency=count,
                        time_window_hours=24,
                        addresses_involved=[],
                        total_algo_volume=0,
                        avg_transaction_size=0,
                        risk_indicators=risk_indicators,
                        confidence_score=count / len(app_calls),
                        first_seen=times[0],
                        last_seen=times[-1]
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in app interaction anomaly detection: {e}")

        return patterns

    async def _detect_asset_manipulation_patterns(self, transactions: List[Dict]) -> List[TransactionPattern]:
        """Detect potential asset manipulation patterns"""
        patterns = []

        try:
            asset_transfers = [txn for txn in transactions if txn.get('tx_type') == 'axfer']
            if len(asset_transfers) < 5:
                return patterns

            # Group by asset ID
            asset_groups = defaultdict(list)
            for txn in asset_transfers:
                asset_id = txn.get('asset_id', 0)
                asset_groups[asset_id].append(txn)

            for asset_id, txns in asset_groups.items():
                if len(txns) < 3:
                    continue

                # Analyze trading patterns for this asset
                amounts = [txn.get('amount', 0) for txn in txns]
                times = [datetime.fromisoformat(txn['confirmed_time']) for txn in txns]

                # Check for pump and dump patterns
                if len(amounts) >= 5:
                    # Look for increasing then decreasing amounts
                    mid_point = len(amounts) // 2
                    first_half_avg = np.mean(amounts[:mid_point])
                    second_half_avg = np.mean(amounts[mid_point:])

                    if first_half_avg < second_half_avg * 0.5:  # Significant decrease
                        risk_indicators = ["potential_pump_dump"]

                        pattern = TransactionPattern(
                            pattern_type="asset_manipulation",
                            frequency=len(txns),
                            time_window_hours=(max(times) - min(times)).total_seconds() / 3600,
                            addresses_involved=[],
                            total_algo_volume=0,
                            avg_transaction_size=np.mean(amounts),
                            risk_indicators=risk_indicators,
                            confidence_score=0.7,  # Medium confidence for this pattern
                            first_seen=min(times),
                            last_seen=max(times)
                        )
                        patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in asset manipulation detection: {e}")

        return patterns

    async def _get_transaction_history(self, address: str, days: int) -> List[Dict]:
        """Get transaction history for an address"""
        # Placeholder implementation - would connect to Algorand indexer
        # This would return actual transaction data from the blockchain

        # Mock data for demonstration
        mock_transactions = []
        base_time = datetime.utcnow() - timedelta(days=days)

        for i in range(min(100, self.config['max_analysis_transactions'])):
            mock_transactions.append({
                'id': f'txn_{i}',
                'sender': address,
                'receiver': f'RECEIVER_{i % 10}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                'amount': 1000000 + (i * 100000),  # microALGOs
                'confirmed_time': (base_time + timedelta(minutes=i*10)).isoformat(),
                'tx_type': 'pay',
                'round_number': 1000000 + i
            })

        return mock_transactions