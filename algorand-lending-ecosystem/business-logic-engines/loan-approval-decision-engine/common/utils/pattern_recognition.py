"""
Pattern Recognition Engine

Advanced pattern recognition for DeFi behavior analysis, risk detection,
and sophisticated borrower behavior identification in the Algorand ecosystem.
"""

import logging
import statistics
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected pattern"""
    pattern_type: str
    confidence: float
    significance: float
    description: str
    evidence: List[str]
    risk_indicator: bool
    metadata: Dict[str, Any]


@dataclass
class BehaviorSignature:
    """Behavioral signature for comparison"""
    signature_id: str
    pattern_features: Dict[str, float]
    behavior_type: str
    risk_level: str
    description: str


class PatternRecognitionEngine:
    """
    Advanced pattern recognition engine for identifying behavioral patterns,
    risk indicators, and sophisticated strategies in DeFi activities.
    """

    def __init__(self):
        self.known_patterns = self._load_known_patterns()
        self.behavior_signatures = self._load_behavior_signatures()
        self.risk_patterns = self._load_risk_patterns()

    async def analyze_transaction_patterns(
        self,
        transactions: List[Dict[str, Any]],
        wallet_address: str
    ) -> List[PatternMatch]:
        """
        Analyze transaction patterns for behavioral insights.

        Args:
            transactions: List of transaction data
            wallet_address: Address being analyzed

        Returns:
            List of detected patterns
        """
        logger.info(f"Analyzing transaction patterns for {wallet_address}")

        if not transactions:
            return []

        patterns = []

        try:
            # Temporal patterns
            temporal_patterns = await self._detect_temporal_patterns(transactions)
            patterns.extend(temporal_patterns)

            # Volume patterns
            volume_patterns = await self._detect_volume_patterns(transactions)
            patterns.extend(volume_patterns)

            # Frequency patterns
            frequency_patterns = await self._detect_frequency_patterns(transactions)
            patterns.extend(frequency_patterns)

            # Counterparty patterns
            counterparty_patterns = await self._detect_counterparty_patterns(transactions)
            patterns.extend(counterparty_patterns)

            # Asset flow patterns
            asset_patterns = await self._detect_asset_flow_patterns(transactions)
            patterns.extend(asset_patterns)

            # Complex behavioral patterns
            behavioral_patterns = await self._detect_behavioral_patterns(transactions)
            patterns.extend(behavioral_patterns)

            logger.info(f"Detected {len(patterns)} patterns for {wallet_address}")
            return patterns

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return []

    async def analyze_defi_strategies(
        self,
        defi_transactions: List[Dict[str, Any]],
        asset_holdings: List[Dict[str, Any]]
    ) -> List[PatternMatch]:
        """
        Analyze DeFi strategies and sophisticated behavior patterns.

        Args:
            defi_transactions: DeFi-specific transactions
            asset_holdings: Current asset holdings

        Returns:
            List of detected DeFi strategy patterns
        """
        patterns = []

        try:
            # Arbitrage patterns
            arbitrage_patterns = await self._detect_arbitrage_patterns(defi_transactions)
            patterns.extend(arbitrage_patterns)

            # Yield farming patterns
            yield_patterns = await self._detect_yield_farming_patterns(defi_transactions)
            patterns.extend(yield_patterns)

            # Liquidity provision patterns
            lp_patterns = await self._detect_liquidity_provision_patterns(defi_transactions)
            patterns.extend(lp_patterns)

            # Risk management patterns
            risk_mgmt_patterns = await self._detect_risk_management_patterns(
                defi_transactions, asset_holdings
            )
            patterns.extend(risk_mgmt_patterns)

            # Flash loan patterns
            flash_loan_patterns = await self._detect_flash_loan_patterns(defi_transactions)
            patterns.extend(flash_loan_patterns)

            return patterns

        except Exception as e:
            logger.error(f"DeFi strategy analysis failed: {e}")
            return []

    async def detect_risk_patterns(
        self,
        all_data: Dict[str, Any]
    ) -> List[PatternMatch]:
        """
        Detect risk patterns across all available data.

        Args:
            all_data: Complete dataset including transactions, holdings, etc.

        Returns:
            List of detected risk patterns
        """
        risk_patterns = []

        try:
            # Wash trading detection
            wash_trading = await self._detect_wash_trading(
                all_data.get('transactions', [])
            )
            risk_patterns.extend(wash_trading)

            # Sybil attack patterns
            sybil_patterns = await self._detect_sybil_patterns(all_data)
            risk_patterns.extend(sybil_patterns)

            # Market manipulation patterns
            manipulation_patterns = await self._detect_market_manipulation(
                all_data.get('transactions', [])
            )
            risk_patterns.extend(manipulation_patterns)

            # Unusual activity patterns
            unusual_patterns = await self._detect_unusual_activity(all_data)
            risk_patterns.extend(unusual_patterns)

            # Governance gaming patterns
            governance_gaming = await self._detect_governance_gaming(
                all_data.get('governance_events', [])
            )
            risk_patterns.extend(governance_gaming)

            return risk_patterns

        except Exception as e:
            logger.error(f"Risk pattern detection failed: {e}")
            return []

    async def identify_behavior_signature(
        self,
        behavioral_data: Dict[str, Any]
    ) -> Optional[BehaviorSignature]:
        """
        Identify behavioral signature by comparing against known patterns.

        Args:
            behavioral_data: Complete behavioral dataset

        Returns:
            Matching behavior signature if found
        """
        try:
            # Extract feature vector from behavioral data
            feature_vector = self._extract_feature_vector(behavioral_data)

            # Find best matching signature
            best_match = None
            best_similarity = 0.0

            for signature in self.behavior_signatures:
                similarity = self._calculate_similarity(
                    feature_vector, signature.pattern_features
                )

                if similarity > best_similarity and similarity > 0.7:  # 70% threshold
                    best_similarity = similarity
                    best_match = signature

            return best_match

        except Exception as e:
            logger.error(f"Behavior signature identification failed: {e}")
            return None

    async def _detect_temporal_patterns(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect time-based patterns in transactions"""
        patterns = []

        if len(transactions) < 10:
            return patterns

        # Extract timestamps
        timestamps = [tx['timestamp'] for tx in transactions if 'timestamp' in tx]
        if not timestamps:
            return patterns

        # Business hours concentration
        business_hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]
        business_hour_txs = sum(1 for ts in timestamps if ts.hour in business_hours)
        business_ratio = business_hour_txs / len(timestamps)

        if business_ratio > 0.8:
            patterns.append(PatternMatch(
                pattern_type="business_hours_concentration",
                confidence=business_ratio,
                significance=0.7,
                description="High concentration of activity during business hours",
                evidence=[f"{business_ratio:.1%} of transactions during business hours"],
                risk_indicator=False,
                metadata={"business_ratio": business_ratio}
            ))

        # Weekend activity
        weekend_txs = sum(1 for ts in timestamps if ts.weekday() >= 5)
        weekend_ratio = weekend_txs / len(timestamps)

        if weekend_ratio > 0.4:
            patterns.append(PatternMatch(
                pattern_type="high_weekend_activity",
                confidence=weekend_ratio,
                significance=0.6,
                description="High activity during weekends",
                evidence=[f"{weekend_ratio:.1%} of transactions on weekends"],
                risk_indicator=False,
                metadata={"weekend_ratio": weekend_ratio}
            ))

        # Night owl pattern (3 AM - 6 AM)
        night_hours = [3, 4, 5, 6]
        night_txs = sum(1 for ts in timestamps if ts.hour in night_hours)
        night_ratio = night_txs / len(timestamps)

        if night_ratio > 0.2:
            patterns.append(PatternMatch(
                pattern_type="night_owl_activity",
                confidence=night_ratio * 2,  # Amplify signal
                significance=0.8,
                description="Unusual late-night activity pattern",
                evidence=[f"{night_ratio:.1%} of transactions between 3-6 AM"],
                risk_indicator=True,
                metadata={"night_ratio": night_ratio}
            ))

        return patterns

    async def _detect_volume_patterns(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect volume-based patterns"""
        patterns = []

        amounts = [tx.get('amount', 0) for tx in transactions if tx.get('amount', 0) > 0]
        if not amounts:
            return patterns

        # Round number bias
        round_amounts = sum(1 for amount in amounts if amount % 1000 == 0)
        round_ratio = round_amounts / len(amounts)

        if round_ratio > 0.5:
            patterns.append(PatternMatch(
                pattern_type="round_number_bias",
                confidence=round_ratio,
                significance=0.6,
                description="High frequency of round number transactions",
                evidence=[f"{round_ratio:.1%} of transactions are round numbers"],
                risk_indicator=False,
                metadata={"round_ratio": round_ratio}
            ))

        # Power law distribution
        if len(amounts) > 20:
            distribution_fit = self._test_power_law_distribution(amounts)
            if distribution_fit > 0.8:
                patterns.append(PatternMatch(
                    pattern_type="power_law_distribution",
                    confidence=distribution_fit,
                    significance=0.7,
                    description="Transaction amounts follow power law distribution",
                    evidence=[f"Distribution fit: {distribution_fit:.2f}"],
                    risk_indicator=False,
                    metadata={"distribution_fit": distribution_fit}
                ))

        # Large transaction concentration
        if amounts:
            total_volume = sum(amounts)
            largest_transactions = sorted(amounts, reverse=True)[:5]
            top5_volume = sum(largest_transactions)
            concentration = top5_volume / total_volume

            if concentration > 0.7:
                patterns.append(PatternMatch(
                    pattern_type="volume_concentration",
                    confidence=concentration,
                    significance=0.8,
                    description="High concentration in few large transactions",
                    evidence=[f"Top 5 transactions represent {concentration:.1%} of volume"],
                    risk_indicator=True,
                    metadata={"concentration": concentration}
                ))

        return patterns

    async def _detect_frequency_patterns(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect frequency-based patterns"""
        patterns = []

        if len(transactions) < 5:
            return patterns

        # Calculate intervals between transactions
        timestamps = sorted([tx['timestamp'] for tx in transactions if 'timestamp' in tx])
        if len(timestamps) < 2:
            return patterns

        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)

        # Regular interval detection
        if len(intervals) > 5:
            interval_cv = statistics.stdev(intervals) / statistics.mean(intervals)
            if interval_cv < 0.3:  # Low coefficient of variation
                patterns.append(PatternMatch(
                    pattern_type="regular_intervals",
                    confidence=1.0 - interval_cv,
                    significance=0.7,
                    description="Highly regular transaction intervals",
                    evidence=[f"Coefficient of variation: {interval_cv:.2f}"],
                    risk_indicator=True,  # Could indicate automation
                    metadata={"interval_cv": interval_cv}
                ))

        # Burst activity detection
        hour_counts = defaultdict(int)
        for ts in timestamps:
            hour_key = ts.replace(minute=0, second=0, microsecond=0)
            hour_counts[hour_key] += 1

        max_hourly = max(hour_counts.values()) if hour_counts else 0
        avg_hourly = sum(hour_counts.values()) / len(hour_counts) if hour_counts else 0

        if max_hourly > avg_hourly * 5:  # 5x average
            patterns.append(PatternMatch(
                pattern_type="burst_activity",
                confidence=min(max_hourly / avg_hourly / 10, 1.0),
                significance=0.8,
                description="Burst activity pattern detected",
                evidence=[f"Max hourly: {max_hourly}, Avg: {avg_hourly:.1f}"],
                risk_indicator=True,
                metadata={"max_hourly": max_hourly, "avg_hourly": avg_hourly}
            ))

        return patterns

    async def _detect_counterparty_patterns(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect counterparty interaction patterns"""
        patterns = []

        counterparties = []
        for tx in transactions:
            if 'receiver' in tx and tx['receiver']:
                counterparties.append(tx['receiver'])

        if not counterparties:
            return patterns

        counterparty_counts = Counter(counterparties)
        unique_counterparties = len(counterparty_counts)
        total_transactions = len(counterparties)

        # High counterparty concentration
        if counterparty_counts:
            most_common_count = counterparty_counts.most_common(1)[0][1]
            concentration = most_common_count / total_transactions

            if concentration > 0.5:
                patterns.append(PatternMatch(
                    pattern_type="counterparty_concentration",
                    confidence=concentration,
                    significance=0.7,
                    description="High concentration with single counterparty",
                    evidence=[f"{concentration:.1%} of transactions with one address"],
                    risk_indicator=True,
                    metadata={"concentration": concentration}
                ))

        # Echo transactions (back and forth)
        echo_count = 0
        sender_receiver_pairs = {}

        for tx in transactions:
            sender = tx.get('sender', '')
            receiver = tx.get('receiver', '')
            if sender and receiver:
                pair = tuple(sorted([sender, receiver]))
                sender_receiver_pairs[pair] = sender_receiver_pairs.get(pair, 0) + 1

        for pair, count in sender_receiver_pairs.items():
            if count > 5:  # More than 5 transactions between same pair
                echo_count += count

        if echo_count > len(transactions) * 0.3:
            echo_ratio = echo_count / len(transactions)
            patterns.append(PatternMatch(
                pattern_type="echo_transactions",
                confidence=echo_ratio,
                significance=0.9,
                description="High frequency echo transactions detected",
                evidence=[f"{echo_ratio:.1%} of transactions are echo patterns"],
                risk_indicator=True,
                metadata={"echo_ratio": echo_ratio}
            ))

        return patterns

    async def _detect_asset_flow_patterns(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect asset flow patterns"""
        patterns = []

        # Group by asset
        asset_flows = defaultdict(list)
        for tx in transactions:
            asset_id = tx.get('asset_id', 0)  # 0 for ALGO
            amount = tx.get('amount', 0)
            if amount > 0:
                asset_flows[asset_id].append(amount)

        # Asset concentration
        if len(asset_flows) > 1:
            total_volume = sum(sum(amounts) for amounts in asset_flows.values())
            largest_asset_volume = max(sum(amounts) for amounts in asset_flows.values())
            concentration = largest_asset_volume / total_volume

            if concentration > 0.8:
                patterns.append(PatternMatch(
                    pattern_type="single_asset_concentration",
                    confidence=concentration,
                    significance=0.6,
                    description="High concentration in single asset",
                    evidence=[f"{concentration:.1%} of volume in one asset"],
                    risk_indicator=False,
                    metadata={"concentration": concentration}
                ))

        # Multi-asset sophistication
        if len(asset_flows) > 5:
            patterns.append(PatternMatch(
                pattern_type="multi_asset_sophistication",
                confidence=min(len(asset_flows) / 10, 1.0),
                significance=0.7,
                description="Sophisticated multi-asset usage",
                evidence=[f"Active with {len(asset_flows)} different assets"],
                risk_indicator=False,
                metadata={"asset_count": len(asset_flows)}
            ))

        return patterns

    async def _detect_behavioral_patterns(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect complex behavioral patterns"""
        patterns = []

        # DCA (Dollar Cost Averaging) pattern
        dca_pattern = self._detect_dca_pattern(transactions)
        if dca_pattern:
            patterns.append(dca_pattern)

        # Panic selling pattern
        panic_pattern = self._detect_panic_pattern(transactions)
        if panic_pattern:
            patterns.append(panic_pattern)

        # HODL pattern
        hodl_pattern = self._detect_hodl_pattern(transactions)
        if hodl_pattern:
            patterns.append(hodl_pattern)

        # Day trading pattern
        day_trading_pattern = self._detect_day_trading_pattern(transactions)
        if day_trading_pattern:
            patterns.append(day_trading_pattern)

        return patterns

    async def _detect_arbitrage_patterns(self, defi_transactions: List[Dict]) -> List[PatternMatch]:
        """Detect arbitrage trading patterns"""
        patterns = []

        # Quick succession buy/sell patterns
        for i in range(len(defi_transactions) - 1):
            current_tx = defi_transactions[i]
            next_tx = defi_transactions[i + 1]

            time_diff = (next_tx['timestamp'] - current_tx['timestamp']).total_seconds()

            if (time_diff < 300 and  # Within 5 minutes
                current_tx.get('app_type') == 'swap' and
                next_tx.get('app_type') == 'swap'):

                patterns.append(PatternMatch(
                    pattern_type="potential_arbitrage",
                    confidence=0.7,
                    significance=0.8,
                    description="Quick successive swaps indicating arbitrage",
                    evidence=[f"Swaps {time_diff:.0f} seconds apart"],
                    risk_indicator=False,
                    metadata={"time_diff": time_diff}
                ))
                break  # Only report once

        return patterns

    async def _detect_yield_farming_patterns(self, defi_transactions: List[Dict]) -> List[PatternMatch]:
        """Detect yield farming patterns"""
        patterns = []

        lp_transactions = [tx for tx in defi_transactions if tx.get('app_type') == 'lp']
        stake_transactions = [tx for tx in defi_transactions if tx.get('app_type') == 'stake']

        if len(lp_transactions) > 5 and len(stake_transactions) > 3:
            patterns.append(PatternMatch(
                pattern_type="yield_farming",
                confidence=min((len(lp_transactions) + len(stake_transactions)) / 20, 1.0),
                significance=0.8,
                description="Active yield farming behavior",
                evidence=[f"{len(lp_transactions)} LP, {len(stake_transactions)} staking transactions"],
                risk_indicator=False,
                metadata={
                    "lp_count": len(lp_transactions),
                    "stake_count": len(stake_transactions)
                }
            ))

        return patterns

    async def _detect_liquidity_provision_patterns(self, defi_transactions: List[Dict]) -> List[PatternMatch]:
        """Detect liquidity provision patterns"""
        patterns = []

        lp_add_txs = [tx for tx in defi_transactions if tx.get('app_type') == 'lp' and tx.get('action') == 'add']
        lp_remove_txs = [tx for tx in defi_transactions if tx.get('app_type') == 'lp' and tx.get('action') == 'remove']

        if len(lp_add_txs) > 3:
            # Check for consistent liquidity provision
            if len(lp_remove_txs) / len(lp_add_txs) < 0.5:  # More adds than removes
                patterns.append(PatternMatch(
                    pattern_type="consistent_liquidity_provider",
                    confidence=0.8,
                    significance=0.7,
                    description="Consistent liquidity provision with minimal withdrawals",
                    evidence=[f"{len(lp_add_txs)} adds vs {len(lp_remove_txs)} removes"],
                    risk_indicator=False,
                    metadata={
                        "lp_adds": len(lp_add_txs),
                        "lp_removes": len(lp_remove_txs)
                    }
                ))

        return patterns

    async def _detect_risk_management_patterns(
        self,
        defi_transactions: List[Dict],
        asset_holdings: List[Dict]
    ) -> List[PatternMatch]:
        """Detect risk management patterns"""
        patterns = []

        # Stop loss detection (quick sells after losses)
        sell_transactions = [tx for tx in defi_transactions if tx.get('action') == 'sell']

        if len(sell_transactions) > 5:
            # Mock implementation - would analyze price movements and sell timing
            patterns.append(PatternMatch(
                pattern_type="stop_loss_usage",
                confidence=0.6,
                significance=0.7,
                description="Evidence of stop-loss risk management",
                evidence=["Pattern of sells following price drops"],
                risk_indicator=False,
                metadata={"sell_count": len(sell_transactions)}
            ))

        return patterns

    async def _detect_flash_loan_patterns(self, defi_transactions: List[Dict]) -> List[PatternMatch]:
        """Detect flash loan usage patterns"""
        patterns = []

        flash_loan_txs = [tx for tx in defi_transactions if 'flash_loan' in tx.get('note', '').lower()]

        if len(flash_loan_txs) > 3:
            patterns.append(PatternMatch(
                pattern_type="flash_loan_user",
                confidence=min(len(flash_loan_txs) / 10, 1.0),
                significance=0.9,
                description="Advanced flash loan usage",
                evidence=[f"{len(flash_loan_txs)} flash loan transactions"],
                risk_indicator=True,  # Sophisticated but potentially risky
                metadata={"flash_loan_count": len(flash_loan_txs)}
            ))

        return patterns

    async def _detect_wash_trading(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect wash trading patterns"""
        patterns = []

        # Look for circular trading patterns
        for i in range(len(transactions) - 2):
            tx1 = transactions[i]
            tx2 = transactions[i + 1]
            tx3 = transactions[i + 2]

            # Check for A->B->A pattern within short time
            if (tx1.get('receiver') == tx3.get('sender') and
                tx1.get('sender') == tx3.get('receiver') and
                (tx3['timestamp'] - tx1['timestamp']).total_seconds() < 3600):  # Within 1 hour

                patterns.append(PatternMatch(
                    pattern_type="wash_trading",
                    confidence=0.8,
                    significance=0.9,
                    description="Potential wash trading pattern detected",
                    evidence=["Circular transaction pattern within short timeframe"],
                    risk_indicator=True,
                    metadata={"pattern_duration": (tx3['timestamp'] - tx1['timestamp']).total_seconds()}
                ))
                break

        return patterns

    async def _detect_sybil_patterns(self, all_data: Dict[str, Any]) -> List[PatternMatch]:
        """Detect Sybil attack patterns"""
        patterns = []

        transactions = all_data.get('transactions', [])
        if len(transactions) < 10:
            return patterns

        # Check for interactions with many new addresses
        counterparties = set()
        for tx in transactions:
            if 'receiver' in tx:
                counterparties.add(tx['receiver'])

        if len(counterparties) > len(transactions) * 0.8:
            patterns.append(PatternMatch(
                pattern_type="sybil_interaction",
                confidence=len(counterparties) / len(transactions),
                significance=0.8,
                description="High interaction with unique addresses",
                evidence=[f"Interacted with {len(counterparties)} unique addresses"],
                risk_indicator=True,
                metadata={"unique_counterparties": len(counterparties)}
            ))

        return patterns

    async def _detect_market_manipulation(self, transactions: List[Dict]) -> List[PatternMatch]:
        """Detect market manipulation patterns"""
        patterns = []

        # Large volume spikes
        if len(transactions) > 20:
            daily_volumes = defaultdict(float)
            for tx in transactions:
                date = tx['timestamp'].date()
                daily_volumes[date] += tx.get('amount', 0)

            volumes = list(daily_volumes.values())
            if volumes:
                avg_volume = statistics.mean(volumes)
                max_volume = max(volumes)

                if max_volume > avg_volume * 10:  # 10x average
                    patterns.append(PatternMatch(
                        pattern_type="volume_manipulation",
                        confidence=min(max_volume / avg_volume / 20, 1.0),
                        significance=0.9,
                        description="Unusual volume spike detected",
                        evidence=[f"Volume spike {max_volume / avg_volume:.1f}x average"],
                        risk_indicator=True,
                        metadata={"volume_spike_ratio": max_volume / avg_volume}
                    ))

        return patterns

    async def _detect_unusual_activity(self, all_data: Dict[str, Any]) -> List[PatternMatch]:
        """Detect unusual activity patterns"""
        patterns = []

        transactions = all_data.get('transactions', [])

        # Sudden activity burst after long dormancy
        if len(transactions) > 10:
            timestamps = sorted([tx['timestamp'] for tx in transactions])
            gaps = []

            for i in range(1, len(timestamps)):
                gap = (timestamps[i] - timestamps[i-1]).days
                gaps.append(gap)

            if gaps:
                max_gap = max(gaps)
                if max_gap > 90:  # 3 months dormancy
                    patterns.append(PatternMatch(
                        pattern_type="dormancy_awakening",
                        confidence=min(max_gap / 365, 1.0),
                        significance=0.7,
                        description="Activity after long dormancy period",
                        evidence=[f"Dormant for {max_gap} days"],
                        risk_indicator=True,
                        metadata={"dormancy_days": max_gap}
                    ))

        return patterns

    async def _detect_governance_gaming(self, governance_events: List[Dict]) -> List[PatternMatch]:
        """Detect governance gaming patterns"""
        patterns = []

        if len(governance_events) < 5:
            return patterns

        # Check for voting pattern manipulation
        vote_events = [e for e in governance_events if e.get('event_type') == 'vote']

        if len(vote_events) > 5:
            # All votes at exactly the same time
            vote_times = [e['timestamp'] for e in vote_events]
            time_diffs = [abs((vote_times[i] - vote_times[0]).total_seconds()) for i in range(1, len(vote_times))]

            if all(diff < 60 for diff in time_diffs):  # All within 1 minute
                patterns.append(PatternMatch(
                    pattern_type="governance_gaming",
                    confidence=0.9,
                    significance=0.9,
                    description="Suspicious simultaneous voting pattern",
                    evidence=["All votes cast within 1 minute"],
                    risk_indicator=True,
                    metadata={"simultaneous_votes": len(vote_events)}
                ))

        return patterns

    def _detect_dca_pattern(self, transactions: List[Dict]) -> Optional[PatternMatch]:
        """Detect Dollar Cost Averaging pattern"""
        if len(transactions) < 10:
            return None

        # Look for regular purchases of similar amounts
        buy_transactions = [tx for tx in transactions if tx.get('action') == 'buy']
        if len(buy_transactions) < 5:
            return None

        amounts = [tx['amount'] for tx in buy_transactions]
        amount_cv = statistics.stdev(amounts) / statistics.mean(amounts)

        timestamps = [tx['timestamp'] for tx in buy_transactions]
        intervals = [(timestamps[i] - timestamps[i-1]).days for i in range(1, len(timestamps))]
        interval_cv = statistics.stdev(intervals) / statistics.mean(intervals) if intervals else 1

        if amount_cv < 0.3 and interval_cv < 0.4:  # Consistent amounts and intervals
            return PatternMatch(
                pattern_type="dollar_cost_averaging",
                confidence=1.0 - max(amount_cv, interval_cv),
                significance=0.8,
                description="Dollar cost averaging investment strategy",
                evidence=[f"Consistent amounts (CV: {amount_cv:.2f}) and intervals (CV: {interval_cv:.2f})"],
                risk_indicator=False,
                metadata={"amount_cv": amount_cv, "interval_cv": interval_cv}
            )

        return None

    def _detect_panic_pattern(self, transactions: List[Dict]) -> Optional[PatternMatch]:
        """Detect panic selling pattern"""
        sell_transactions = [tx for tx in transactions if tx.get('action') == 'sell']
        if len(sell_transactions) < 3:
            return None

        # Look for clustered selling within short timeframe
        timestamps = [tx['timestamp'] for tx in sell_transactions]
        if len(timestamps) < 3:
            return None

        # Check if multiple sells within 24 hours
        for i in range(len(timestamps) - 2):
            time_span = (timestamps[i + 2] - timestamps[i]).total_seconds()
            if time_span < 86400:  # Within 24 hours
                return PatternMatch(
                    pattern_type="panic_selling",
                    confidence=0.7,
                    significance=0.8,
                    description="Panic selling pattern detected",
                    evidence=["Multiple sells within short timeframe"],
                    risk_indicator=True,
                    metadata={"sells_in_24h": 3}
                )

        return None

    def _detect_hodl_pattern(self, transactions: List[Dict]) -> Optional[PatternMatch]:
        """Detect HODL (hold) pattern"""
        buy_transactions = [tx for tx in transactions if tx.get('action') == 'buy']
        sell_transactions = [tx for tx in transactions if tx.get('action') == 'sell']

        if len(buy_transactions) > 0 and len(sell_transactions) == 0:
            return PatternMatch(
                pattern_type="hodl_behavior",
                confidence=1.0,
                significance=0.7,
                description="HODL behavior - buying without selling",
                evidence=[f"{len(buy_transactions)} buys, 0 sells"],
                risk_indicator=False,
                metadata={"buy_count": len(buy_transactions)}
            )

        return None

    def _detect_day_trading_pattern(self, transactions: List[Dict]) -> Optional[PatternMatch]:
        """Detect day trading pattern"""
        trading_days = defaultdict(list)

        for tx in transactions:
            if tx.get('action') in ['buy', 'sell']:
                date = tx['timestamp'].date()
                trading_days[date].append(tx)

        # Count days with multiple trades
        active_trading_days = sum(1 for day_txs in trading_days.values() if len(day_txs) > 2)

        if active_trading_days > 5:
            return PatternMatch(
                pattern_type="day_trading",
                confidence=min(active_trading_days / 10, 1.0),
                significance=0.8,
                description="Active day trading behavior",
                evidence=[f"{active_trading_days} days with multiple trades"],
                risk_indicator=False,
                metadata={"active_trading_days": active_trading_days}
            )

        return None

    def _test_power_law_distribution(self, amounts: List[float]) -> float:
        """Test if amounts follow power law distribution"""
        # Simplified power law test
        sorted_amounts = sorted(amounts, reverse=True)
        ranks = list(range(1, len(sorted_amounts) + 1))

        # Calculate correlation between log(rank) and log(amount)
        try:
            log_ranks = [np.log(r) for r in ranks]
            log_amounts = [np.log(a) for a in sorted_amounts if a > 0]

            if len(log_ranks) != len(log_amounts):
                return 0.0

            correlation = np.corrcoef(log_ranks, log_amounts)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0

    def _extract_feature_vector(self, behavioral_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract feature vector from behavioral data"""
        features = {}

        # Transaction features
        tx_data = behavioral_data.get('transactions', {})
        features['avg_daily_frequency'] = tx_data.get('avg_daily_frequency', 0)
        features['transaction_diversity'] = tx_data.get('transaction_diversity_score', 0)

        # Volume features
        features['total_volume'] = behavioral_data.get('total_volume_algo', 0)
        features['avg_transaction_size'] = tx_data.get('avg_transaction_size', 0)

        # Timing features
        features['business_hours_ratio'] = tx_data.get('business_hours_ratio', 0)
        features['weekend_ratio'] = tx_data.get('weekend_activity_ratio', 0)

        # DeFi features
        defi_data = behavioral_data.get('defi', {})
        features['defi_sophistication'] = defi_data.get('defi_sophistication_score', 0)
        features['protocol_count'] = len(defi_data.get('protocols_used', []))

        # Governance features
        governance_data = behavioral_data.get('governance', {})
        features['governance_participation'] = 1.0 if governance_data.get('votes_cast', 0) > 0 else 0.0

        return features

    def _calculate_similarity(
        self,
        vector1: Dict[str, float],
        vector2: Dict[str, float]
    ) -> float:
        """Calculate cosine similarity between feature vectors"""
        common_keys = set(vector1.keys()) & set(vector2.keys())
        if not common_keys:
            return 0.0

        dot_product = sum(vector1[key] * vector2[key] for key in common_keys)
        norm1 = sum(vector1[key] ** 2 for key in common_keys) ** 0.5
        norm2 = sum(vector2[key] ** 2 for key in common_keys) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _load_known_patterns(self) -> Dict[str, Dict]:
        """Load known pattern definitions"""
        return {
            "wash_trading": {
                "risk_level": "high",
                "indicators": ["circular_transactions", "short_timeframes"],
                "min_confidence": 0.7
            },
            "arbitrage": {
                "risk_level": "low",
                "indicators": ["quick_swaps", "profit_patterns"],
                "min_confidence": 0.6
            },
            "yield_farming": {
                "risk_level": "medium",
                "indicators": ["lp_provision", "staking_activity"],
                "min_confidence": 0.5
            }
        }

    def _load_behavior_signatures(self) -> List[BehaviorSignature]:
        """Load known behavior signatures"""
        return [
            BehaviorSignature(
                signature_id="conservative_hodler",
                pattern_features={
                    "avg_daily_frequency": 0.1,
                    "defi_sophistication": 0.3,
                    "governance_participation": 0.0
                },
                behavior_type="conservative",
                risk_level="low",
                description="Conservative holder with minimal activity"
            ),
            BehaviorSignature(
                signature_id="defi_power_user",
                pattern_features={
                    "avg_daily_frequency": 2.0,
                    "defi_sophistication": 0.9,
                    "protocol_count": 8.0,
                    "governance_participation": 1.0
                },
                behavior_type="sophisticated",
                risk_level="medium",
                description="Highly active DeFi power user"
            )
        ]

    def _load_risk_patterns(self) -> Dict[str, Dict]:
        """Load risk pattern definitions"""
        return {
            "sybil_attack": {
                "indicators": ["many_unique_counterparties", "new_addresses"],
                "risk_weight": 0.9
            },
            "market_manipulation": {
                "indicators": ["volume_spikes", "coordinated_activity"],
                "risk_weight": 0.8
            },
            "governance_gaming": {
                "indicators": ["simultaneous_voting", "proposal_spam"],
                "risk_weight": 0.7
            }
        }