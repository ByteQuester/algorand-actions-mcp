"""
Algorand Transaction Pattern Analyzer

Analyzes Algorand transaction patterns for anomaly detection and risk assessment.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import math

from ..models.blockchain_risk import (
    TransactionPattern, BehaviorPattern, RiskLevel, TransactionType
)


@dataclass
class TransactionWindow:
    """Time window for transaction analysis"""
    start_time: datetime
    end_time: datetime
    transaction_count: int
    total_volume: float
    unique_counterparties: int
    asset_types: set
    avg_transaction_size: float
    velocity_score: float


class AlgorandTransactionAnalyzer:
    """Analyzes Algorand transactions for behavior patterns and anomalies"""

    def __init__(self, anomaly_threshold: float = 2.5):
        self.anomaly_threshold = anomaly_threshold
        self.baseline_windows = []
        self.pattern_cache = {}

    async def analyze_wallet_transactions(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]],
        analysis_period: timedelta = timedelta(days=30)
    ) -> List[TransactionPattern]:
        """
        Analyze transaction patterns for a specific wallet

        Args:
            wallet_address: The wallet address to analyze
            transactions: List of transaction data
            analysis_period: Time period for analysis

        Returns:
            List of detected transaction patterns
        """
        patterns = []

        # Group transactions by time windows
        windows = self._create_time_windows(transactions, hours=24)

        # Analyze velocity patterns
        velocity_pattern = await self._analyze_velocity_patterns(
            wallet_address, windows, transactions
        )
        if velocity_pattern:
            patterns.append(velocity_pattern)

        # Analyze dormant activation
        dormant_pattern = await self._analyze_dormant_activation(
            wallet_address, transactions
        )
        if dormant_pattern:
            patterns.append(dormant_pattern)

        # Analyze wash trading patterns
        wash_pattern = await self._analyze_wash_trading(
            wallet_address, transactions
        )
        if wash_pattern:
            patterns.append(wash_pattern)

        # Analyze flash loan patterns
        flash_pattern = await self._analyze_flash_loan_patterns(
            wallet_address, transactions
        )
        if flash_pattern:
            patterns.append(flash_pattern)

        # Analyze MEV exploitation
        mev_pattern = await self._analyze_mev_patterns(
            wallet_address, transactions
        )
        if mev_pattern:
            patterns.append(mev_pattern)

        return patterns

    def _create_time_windows(
        self,
        transactions: List[Dict[str, Any]],
        hours: int = 24
    ) -> List[TransactionWindow]:
        """Create time windows for transaction analysis"""
        if not transactions:
            return []

        # Sort transactions by timestamp
        sorted_txns = sorted(
            transactions,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        windows = []
        window_duration = timedelta(hours=hours)

        start_time = datetime.fromisoformat(sorted_txns[0]['timestamp'])
        end_time = datetime.fromisoformat(sorted_txns[-1]['timestamp'])

        current_start = start_time
        while current_start < end_time:
            current_end = current_start + window_duration

            # Filter transactions in this window
            window_txns = [
                txn for txn in sorted_txns
                if current_start <= datetime.fromisoformat(txn['timestamp']) < current_end
            ]

            if window_txns:
                total_volume = sum(float(txn.get('amount', 0)) for txn in window_txns)
                counterparties = set()
                asset_types = set()

                for txn in window_txns:
                    counterparties.add(txn.get('receiver', ''))
                    counterparties.add(txn.get('sender', ''))
                    asset_types.add(txn.get('asset-id', 0))

                avg_size = total_volume / len(window_txns) if window_txns else 0
                velocity_score = len(window_txns) / hours  # Transactions per hour

                window = TransactionWindow(
                    start_time=current_start,
                    end_time=current_end,
                    transaction_count=len(window_txns),
                    total_volume=total_volume,
                    unique_counterparties=len(counterparties),
                    asset_types=asset_types,
                    avg_transaction_size=avg_size,
                    velocity_score=velocity_score
                )
                windows.append(window)

            current_start = current_end

        return windows

    async def _analyze_velocity_patterns(
        self,
        wallet_address: str,
        windows: List[TransactionWindow],
        transactions: List[Dict[str, Any]]
    ) -> Optional[TransactionPattern]:
        """Analyze transaction velocity for anomalies"""
        if len(windows) < 7:  # Need at least a week of data
            return None

        # Calculate baseline velocity statistics
        velocities = [w.velocity_score for w in windows[:-3]]  # Exclude last 3 days

        if not velocities:
            return None

        baseline_mean = statistics.mean(velocities)
        baseline_std = statistics.stdev(velocities) if len(velocities) > 1 else 0

        # Check recent windows for anomalies
        recent_windows = windows[-3:]
        anomalies = []
        max_velocity = 0

        for window in recent_windows:
            if baseline_std > 0:
                z_score = (window.velocity_score - baseline_mean) / baseline_std
                if abs(z_score) > self.anomaly_threshold:
                    anomalies.append(f"Velocity spike: {window.velocity_score:.2f} txns/hour (z-score: {z_score:.2f})")
                    max_velocity = max(max_velocity, window.velocity_score)

        if anomalies:
            total_recent_volume = sum(w.total_volume for w in recent_windows)
            total_recent_txns = sum(w.transaction_count for w in recent_windows)

            return TransactionPattern(
                wallet_address=wallet_address,
                pattern_type=BehaviorPattern.VELOCITY_SPIKE,
                confidence_score=min(max_velocity / (baseline_mean + 1), 1.0),
                time_window=timedelta(days=3),
                transaction_count=total_recent_txns,
                total_volume=total_recent_volume,
                velocity_score=max_velocity,
                anomaly_indicators=anomalies,
                risk_factors={
                    'velocity_anomaly': min(max_velocity / (baseline_mean + 1), 1.0),
                    'pattern_persistence': len(anomalies) / 3,
                    'volume_concentration': total_recent_volume / max(sum(t.get('amount', 0) for t in transactions), 1)
                }
            )

        return None

    async def _analyze_dormant_activation(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[TransactionPattern]:
        """Analyze for dormant wallet sudden activation"""
        if len(transactions) < 10:
            return None

        # Sort transactions by timestamp
        sorted_txns = sorted(
            transactions,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        # Look for long periods of inactivity followed by high activity
        gaps = []
        for i in range(1, len(sorted_txns)):
            prev_time = datetime.fromisoformat(sorted_txns[i-1]['timestamp'])
            curr_time = datetime.fromisoformat(sorted_txns[i]['timestamp'])
            gap = curr_time - prev_time
            gaps.append(gap)

        # Find the longest gap
        if gaps:
            max_gap = max(gaps)
            max_gap_index = gaps.index(max_gap)

            # Check if there's a significant dormant period (>30 days) followed by activity
            if max_gap > timedelta(days=30):
                # Analyze activity after the gap
                post_gap_txns = sorted_txns[max_gap_index + 1:]

                if len(post_gap_txns) >= 5:  # Significant activity after dormancy
                    post_gap_window = timedelta(days=7)
                    post_gap_start = datetime.fromisoformat(post_gap_txns[0]['timestamp'])

                    recent_activity = [
                        txn for txn in post_gap_txns
                        if datetime.fromisoformat(txn['timestamp']) <= post_gap_start + post_gap_window
                    ]

                    if len(recent_activity) >= 5:
                        total_volume = sum(float(txn.get('amount', 0)) for txn in recent_activity)

                        return TransactionPattern(
                            wallet_address=wallet_address,
                            pattern_type=BehaviorPattern.DORMANT_ACTIVATION,
                            confidence_score=min(len(recent_activity) / 20, 1.0),
                            time_window=post_gap_window,
                            transaction_count=len(recent_activity),
                            total_volume=total_volume,
                            velocity_score=len(recent_activity) / 7,
                            anomaly_indicators=[
                                f"Dormant for {max_gap.days} days",
                                f"Sudden activation with {len(recent_activity)} transactions in 7 days"
                            ],
                            risk_factors={
                                'dormancy_duration': min(max_gap.days / 365, 1.0),
                                'activation_intensity': min(len(recent_activity) / 50, 1.0),
                                'volume_concentration': 0.8  # High risk due to pattern
                            }
                        )

        return None

    async def _analyze_wash_trading(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[TransactionPattern]:
        """Analyze for wash trading patterns"""
        # Group transactions by counterparty
        counterparty_interactions = defaultdict(list)

        for txn in transactions:
            sender = txn.get('sender', '')
            receiver = txn.get('receiver', '')

            if sender == wallet_address:
                counterparty_interactions[receiver].append(txn)
            elif receiver == wallet_address:
                counterparty_interactions[sender].append(txn)

        wash_indicators = []
        total_wash_volume = 0
        max_wash_ratio = 0

        for counterparty, txns in counterparty_interactions.items():
            if len(txns) < 4:  # Need multiple interactions
                continue

            # Analyze round-trip patterns
            sent_volume = sum(
                float(txn.get('amount', 0))
                for txn in txns
                if txn.get('sender') == wallet_address
            )

            received_volume = sum(
                float(txn.get('amount', 0))
                for txn in txns
                if txn.get('receiver') == wallet_address
            )

            # Check for balanced back-and-forth transactions
            if sent_volume > 0 and received_volume > 0:
                balance_ratio = min(sent_volume, received_volume) / max(sent_volume, received_volume)

                if balance_ratio > 0.8 and len(txns) >= 6:  # High balance and frequency
                    wash_volume = min(sent_volume, received_volume)
                    total_wash_volume += wash_volume
                    max_wash_ratio = max(max_wash_ratio, balance_ratio)

                    wash_indicators.append(
                        f"Balanced trading with {counterparty[:8]}... "
                        f"(ratio: {balance_ratio:.2f}, volume: {wash_volume:.2f})"
                    )

        if wash_indicators:
            total_volume = sum(float(txn.get('amount', 0)) for txn in transactions)
            wash_ratio = total_wash_volume / max(total_volume, 1)

            return TransactionPattern(
                wallet_address=wallet_address,
                pattern_type=BehaviorPattern.WASH_TRADING,
                confidence_score=min(wash_ratio * 2, 1.0),
                time_window=timedelta(days=30),
                transaction_count=len(transactions),
                total_volume=total_volume,
                velocity_score=len(transactions) / 30,
                anomaly_indicators=wash_indicators,
                risk_factors={
                    'wash_volume_ratio': wash_ratio,
                    'pattern_sophistication': max_wash_ratio,
                    'counterparty_diversity': 1 / max(len(counterparty_interactions), 1)
                }
            )

        return None

    async def _analyze_flash_loan_patterns(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[TransactionPattern]:
        """Analyze for flash loan arbitrage patterns"""
        # Look for rapid sequences of large transactions within same block/round
        flash_sequences = []

        # Group transactions by round number or timestamp proximity
        rounds = defaultdict(list)
        for txn in transactions:
            round_num = txn.get('confirmed-round', 0)
            if round_num:
                rounds[round_num].append(txn)

        for round_num, round_txns in rounds.items():
            if len(round_txns) >= 3:  # Multiple transactions in same round
                total_volume = sum(float(txn.get('amount', 0)) for txn in round_txns)

                # Check for large volume concentration in single round
                if total_volume > 10000:  # Significant volume threshold
                    asset_types = set(txn.get('asset-id', 0) for txn in round_txns)

                    flash_sequences.append({
                        'round': round_num,
                        'transaction_count': len(round_txns),
                        'volume': total_volume,
                        'assets': len(asset_types)
                    })

        if flash_sequences:
            total_flash_volume = sum(seq['volume'] for seq in flash_sequences)
            total_volume = sum(float(txn.get('amount', 0)) for txn in transactions)
            flash_ratio = total_flash_volume / max(total_volume, 1)

            indicators = [
                f"Flash sequence in round {seq['round']}: {seq['transaction_count']} txns, "
                f"{seq['volume']:.2f} volume"
                for seq in flash_sequences[:5]  # Limit to first 5
            ]

            return TransactionPattern(
                wallet_address=wallet_address,
                pattern_type=BehaviorPattern.FLASH_LOAN_ARBITRAGE,
                confidence_score=min(flash_ratio * 3, 1.0),
                time_window=timedelta(days=30),
                transaction_count=len(transactions),
                total_volume=total_volume,
                velocity_score=len(flash_sequences),
                anomaly_indicators=indicators,
                risk_factors={
                    'flash_volume_ratio': flash_ratio,
                    'sequence_frequency': len(flash_sequences) / 30,
                    'capital_efficiency': total_flash_volume / max(len(flash_sequences), 1)
                }
            )

        return None

    async def _analyze_mev_patterns(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[TransactionPattern]:
        """Analyze for MEV exploitation patterns"""
        mev_indicators = []

        # Look for sandwich attack patterns (before/after target transactions)
        application_calls = [
            txn for txn in transactions
            if txn.get('tx-type') == 'appl'
        ]

        if len(application_calls) < 3:
            return None

        # Analyze timing patterns around application calls
        sandwich_patterns = 0
        total_mev_volume = 0

        for i in range(1, len(application_calls) - 1):
            prev_txn = application_calls[i-1]
            curr_txn = application_calls[i]
            next_txn = application_calls[i+1]

            # Check for rapid sequence targeting same application
            if (prev_txn.get('application-id') == next_txn.get('application-id') and
                curr_txn.get('application-id') == prev_txn.get('application-id')):

                # Analyze timing
                prev_time = datetime.fromisoformat(prev_txn['timestamp'])
                next_time = datetime.fromisoformat(next_txn['timestamp'])
                time_diff = next_time - prev_time

                if time_diff < timedelta(minutes=1):  # Very rapid sequence
                    sandwich_patterns += 1
                    volume = sum(float(txn.get('amount', 0)) for txn in [prev_txn, curr_txn, next_txn])
                    total_mev_volume += volume

                    mev_indicators.append(
                        f"Potential sandwich pattern on app {curr_txn.get('application-id')} "
                        f"(volume: {volume:.2f})"
                    )

        # Look for arbitrage patterns across different applications
        app_interactions = defaultdict(list)
        for txn in application_calls:
            app_id = txn.get('application-id')
            if app_id:
                app_interactions[app_id].append(txn)

        # Check for rapid interactions across multiple protocols
        if len(app_interactions) >= 3:
            arbitrage_sequences = 0
            for app_id, app_txns in app_interactions.items():
                if len(app_txns) >= 2:
                    arbitrage_sequences += 1

            if arbitrage_sequences >= 3:
                mev_indicators.append(
                    f"Cross-protocol arbitrage across {arbitrage_sequences} applications"
                )

        if mev_indicators:
            total_volume = sum(float(txn.get('amount', 0)) for txn in transactions)
            mev_ratio = total_mev_volume / max(total_volume, 1)

            return TransactionPattern(
                wallet_address=wallet_address,
                pattern_type=BehaviorPattern.MEV_EXPLOITATION,
                confidence_score=min((sandwich_patterns + arbitrage_sequences) / 10, 1.0),
                time_window=timedelta(days=30),
                transaction_count=len(transactions),
                total_volume=total_volume,
                velocity_score=sandwich_patterns + arbitrage_sequences,
                anomaly_indicators=mev_indicators,
                risk_factors={
                    'mev_volume_ratio': mev_ratio,
                    'sandwich_frequency': sandwich_patterns / 30,
                    'protocol_diversity': len(app_interactions) / 10
                }
            )

        return None

    def calculate_pattern_risk_score(self, patterns: List[TransactionPattern]) -> float:
        """Calculate overall risk score from detected patterns"""
        if not patterns:
            return 0.0

        # Weight different pattern types by severity
        pattern_weights = {
            BehaviorPattern.NORMAL: 0.0,
            BehaviorPattern.VELOCITY_SPIKE: 0.3,
            BehaviorPattern.DORMANT_ACTIVATION: 0.5,
            BehaviorPattern.WASH_TRADING: 0.8,
            BehaviorPattern.SYBIL_CLUSTER: 0.9,
            BehaviorPattern.MEV_EXPLOITATION: 0.7,
            BehaviorPattern.FLASH_LOAN_ARBITRAGE: 0.6,
            BehaviorPattern.BRIDGE_FARMING: 0.4
        }

        weighted_score = 0.0
        total_weight = 0.0

        for pattern in patterns:
            weight = pattern_weights.get(pattern.pattern_type, 0.5)
            weighted_score += pattern.confidence_score * weight
            total_weight += weight

        return min(weighted_score / max(total_weight, 1), 1.0)