"""
MEV (Maximal Extractable Value) Detection and Analysis

Detects and analyzes MEV exploitation patterns on Algorand,
including sandwich attacks, arbitrage, and front-running.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics

from ..models.blockchain_risk import RiskLevel, RiskAlert


class MEVType(Enum):
    """Types of MEV exploitation"""
    SANDWICH_ATTACK = "sandwich_attack"
    FRONT_RUNNING = "front_running"
    BACK_RUNNING = "back_running"
    ARBITRAGE = "arbitrage"
    LIQUIDATION = "liquidation"
    FLASH_LOAN = "flash_loan"
    JIT_LIQUIDITY = "jit_liquidity"


@dataclass
class MEVTransaction:
    """MEV-related transaction data"""
    txn_id: str
    block_number: int
    position_in_block: int
    timestamp: datetime
    sender: str
    receiver: str
    amount: float
    asset_id: int
    application_id: Optional[int]
    fee: float
    gas_used: Optional[int]
    transaction_type: str


@dataclass
class MEVPattern:
    """Detected MEV pattern"""
    pattern_id: str
    mev_type: MEVType
    transactions: List[MEVTransaction]
    extracted_value: float
    confidence_score: float
    victim_addresses: List[str]
    exploiter_address: str
    time_window: timedelta
    detection_method: str
    evidence: Dict[str, Any]


@dataclass
class MEVAnalytics:
    """MEV analytics and metrics"""
    total_mev_extracted: float
    mev_per_block: float
    mev_transactions_ratio: float
    top_mev_extractors: List[Tuple[str, float]]
    victim_impact_analysis: Dict[str, float]
    temporal_patterns: Dict[str, Any]


class MEVDetector:
    """Advanced MEV detection and analysis system"""

    def __init__(self):
        self.detection_thresholds = {
            'sandwich_time_window': timedelta(seconds=30),
            'arbitrage_profit_threshold': 100.0,
            'min_confidence_score': 0.7,
            'front_run_time_window': timedelta(seconds=10)
        }
        self.known_dex_apps = set()  # Would be populated with known DEX application IDs
        self.price_impact_cache = {}

    async def detect_mev_patterns(
        self,
        transactions: List[MEVTransaction],
        time_window: timedelta = timedelta(hours=24)
    ) -> List[MEVPattern]:
        """
        Detect MEV patterns in transaction data

        Args:
            transactions: List of transactions to analyze
            time_window: Time window for pattern detection

        Returns:
            List of detected MEV patterns
        """
        patterns = []

        # Sort transactions by block number and position
        sorted_txns = sorted(
            transactions,
            key=lambda x: (x.block_number, x.position_in_block)
        )

        # Group transactions by blocks for efficient analysis
        blocks = self._group_transactions_by_block(sorted_txns)

        # Detect different MEV patterns
        for block_number, block_txns in blocks.items():
            # Detect sandwich attacks
            sandwich_patterns = await self._detect_sandwich_attacks(block_txns)
            patterns.extend(sandwich_patterns)

            # Detect front-running
            front_run_patterns = await self._detect_front_running(block_txns)
            patterns.extend(front_run_patterns)

            # Detect arbitrage
            arbitrage_patterns = await self._detect_arbitrage(block_txns)
            patterns.extend(arbitrage_patterns)

            # Detect liquidation MEV
            liquidation_patterns = await self._detect_liquidation_mev(block_txns)
            patterns.extend(liquidation_patterns)

        # Cross-block analysis for complex patterns
        cross_block_patterns = await self._detect_cross_block_patterns(sorted_txns)
        patterns.extend(cross_block_patterns)

        # Filter patterns by confidence threshold
        high_confidence_patterns = [
            pattern for pattern in patterns
            if pattern.confidence_score >= self.detection_thresholds['min_confidence_score']
        ]

        return high_confidence_patterns

    def _group_transactions_by_block(
        self,
        transactions: List[MEVTransaction]
    ) -> Dict[int, List[MEVTransaction]]:
        """Group transactions by block number"""
        blocks = defaultdict(list)
        for txn in transactions:
            blocks[txn.block_number].append(txn)
        return dict(blocks)

    async def _detect_sandwich_attacks(
        self,
        block_transactions: List[MEVTransaction]
    ) -> List[MEVPattern]:
        """Detect sandwich attack patterns in a block"""
        patterns = []

        if len(block_transactions) < 3:
            return patterns

        # Look for DEX transactions that could be sandwiched
        dex_transactions = [
            txn for txn in block_transactions
            if txn.application_id in self.known_dex_apps or
            self._is_likely_dex_transaction(txn)
        ]

        if len(dex_transactions) < 3:
            return patterns

        # Analyze transaction sequences for sandwich patterns
        for i in range(len(dex_transactions) - 2):
            front_txn = dex_transactions[i]
            victim_txn = dex_transactions[i + 1]
            back_txn = dex_transactions[i + 2]

            # Check if this could be a sandwich attack
            if await self._is_sandwich_pattern(front_txn, victim_txn, back_txn):
                # Calculate extracted value
                extracted_value = await self._calculate_sandwich_value(
                    front_txn, victim_txn, back_txn
                )

                # Calculate confidence score
                confidence = await self._calculate_sandwich_confidence(
                    front_txn, victim_txn, back_txn
                )

                if confidence >= 0.5:  # Minimum confidence for detection
                    pattern = MEVPattern(
                        pattern_id=f"sandwich_{front_txn.block_number}_{i}",
                        mev_type=MEVType.SANDWICH_ATTACK,
                        transactions=[front_txn, victim_txn, back_txn],
                        extracted_value=extracted_value,
                        confidence_score=confidence,
                        victim_addresses=[victim_txn.sender],
                        exploiter_address=front_txn.sender,
                        time_window=back_txn.timestamp - front_txn.timestamp,
                        detection_method="Block Analysis",
                        evidence={
                            'front_position': front_txn.position_in_block,
                            'victim_position': victim_txn.position_in_block,
                            'back_position': back_txn.position_in_block,
                            'same_asset': front_txn.asset_id == back_txn.asset_id,
                            'opposite_direction': self._check_opposite_direction(front_txn, back_txn)
                        }
                    )
                    patterns.append(pattern)

        return patterns

    async def _detect_front_running(
        self,
        block_transactions: List[MEVTransaction]
    ) -> List[MEVPattern]:
        """Detect front-running patterns"""
        patterns = []

        # Group transactions by application/asset
        app_groups = defaultdict(list)
        for txn in block_transactions:
            key = (txn.application_id, txn.asset_id)
            app_groups[key].append(txn)

        # Analyze each group for front-running
        for (app_id, asset_id), group_txns in app_groups.items():
            if len(group_txns) < 2:
                continue

            # Sort by position in block
            sorted_group = sorted(group_txns, key=lambda x: x.position_in_block)

            for i in range(len(sorted_group) - 1):
                front_txn = sorted_group[i]
                following_txn = sorted_group[i + 1]

                # Check for front-running indicators
                if await self._is_front_running_pattern(front_txn, following_txn):
                    extracted_value = await self._calculate_front_run_value(
                        front_txn, following_txn
                    )

                    confidence = await self._calculate_front_run_confidence(
                        front_txn, following_txn
                    )

                    if confidence >= 0.6:
                        pattern = MEVPattern(
                            pattern_id=f"frontrun_{front_txn.block_number}_{i}",
                            mev_type=MEVType.FRONT_RUNNING,
                            transactions=[front_txn, following_txn],
                            extracted_value=extracted_value,
                            confidence_score=confidence,
                            victim_addresses=[following_txn.sender],
                            exploiter_address=front_txn.sender,
                            time_window=following_txn.timestamp - front_txn.timestamp,
                            detection_method="Front-Run Detection",
                            evidence={
                                'position_advantage': front_txn.position_in_block < following_txn.position_in_block,
                                'higher_fee': front_txn.fee > following_txn.fee,
                                'same_action': self._check_similar_action(front_txn, following_txn)
                            }
                        )
                        patterns.append(pattern)

        return patterns

    async def _detect_arbitrage(
        self,
        block_transactions: List[MEVTransaction]
    ) -> List[MEVPattern]:
        """Detect arbitrage MEV patterns"""
        patterns = []

        # Group transactions by sender to find arbitrage sequences
        sender_groups = defaultdict(list)
        for txn in block_transactions:
            sender_groups[txn.sender].append(txn)

        # Analyze each sender's transactions for arbitrage
        for sender, txns in sender_groups.items():
            if len(txns) < 2:
                continue

            # Look for round-trip arbitrage patterns
            arbitrage_sequences = await self._find_arbitrage_sequences(txns)

            for sequence in arbitrage_sequences:
                extracted_value = await self._calculate_arbitrage_value(sequence)
                confidence = await self._calculate_arbitrage_confidence(sequence)

                if confidence >= 0.7 and extracted_value > self.detection_thresholds['arbitrage_profit_threshold']:
                    pattern = MEVPattern(
                        pattern_id=f"arbitrage_{sequence[0].block_number}_{sender}",
                        mev_type=MEVType.ARBITRAGE,
                        transactions=sequence,
                        extracted_value=extracted_value,
                        confidence_score=confidence,
                        victim_addresses=[],  # Arbitrage typically doesn't have direct victims
                        exploiter_address=sender,
                        time_window=sequence[-1].timestamp - sequence[0].timestamp,
                        detection_method="Arbitrage Detection",
                        evidence={
                            'round_trip': self._check_round_trip(sequence),
                            'multiple_apps': len(set(txn.application_id for txn in sequence)) > 1,
                            'profit_extracted': extracted_value
                        }
                    )
                    patterns.append(pattern)

        return patterns

    async def _detect_liquidation_mev(
        self,
        block_transactions: List[MEVTransaction]
    ) -> List[MEVPattern]:
        """Detect liquidation MEV patterns"""
        patterns = []

        # Look for transactions that might be liquidations
        potential_liquidations = [
            txn for txn in block_transactions
            if self._is_likely_liquidation(txn)
        ]

        for liquidation_txn in potential_liquidations:
            # Look for related transactions that might be MEV extraction
            related_txns = await self._find_liquidation_related_transactions(
                liquidation_txn, block_transactions
            )

            if related_txns:
                extracted_value = await self._calculate_liquidation_mev_value(
                    liquidation_txn, related_txns
                )

                confidence = await self._calculate_liquidation_confidence(
                    liquidation_txn, related_txns
                )

                if confidence >= 0.6:
                    all_txns = [liquidation_txn] + related_txns
                    pattern = MEVPattern(
                        pattern_id=f"liquidation_{liquidation_txn.block_number}_{liquidation_txn.txn_id}",
                        mev_type=MEVType.LIQUIDATION,
                        transactions=all_txns,
                        extracted_value=extracted_value,
                        confidence_score=confidence,
                        victim_addresses=[liquidation_txn.receiver],
                        exploiter_address=liquidation_txn.sender,
                        time_window=timedelta(0),  # Same block
                        detection_method="Liquidation MEV Detection",
                        evidence={
                            'liquidation_bonus': extracted_value,
                            'related_transactions': len(related_txns)
                        }
                    )
                    patterns.append(pattern)

        return patterns

    async def _detect_cross_block_patterns(
        self,
        transactions: List[MEVTransaction]
    ) -> List[MEVPattern]:
        """Detect MEV patterns that span multiple blocks"""
        patterns = []

        # Group by sender for cross-block analysis
        sender_groups = defaultdict(list)
        for txn in transactions:
            sender_groups[txn.sender].append(txn)

        # Look for flash loan patterns across blocks
        for sender, txns in sender_groups.items():
            flash_loan_patterns = await self._detect_flash_loan_patterns(txns)
            patterns.extend(flash_loan_patterns)

        return patterns

    async def _is_sandwich_pattern(
        self,
        front_txn: MEVTransaction,
        victim_txn: MEVTransaction,
        back_txn: MEVTransaction
    ) -> bool:
        """Check if three transactions form a sandwich pattern"""
        # Check if front and back transactions are from the same sender
        if front_txn.sender != back_txn.sender:
            return False

        # Check if they're in the correct order
        if not (front_txn.position_in_block < victim_txn.position_in_block < back_txn.position_in_block):
            return False

        # Check if they involve the same asset or application
        if front_txn.asset_id != back_txn.asset_id and front_txn.application_id != back_txn.application_id:
            return False

        # Check if front and back transactions are opposite directions
        if not self._check_opposite_direction(front_txn, back_txn):
            return False

        return True

    def _check_opposite_direction(self, txn1: MEVTransaction, txn2: MEVTransaction) -> bool:
        """Check if two transactions are in opposite directions (simplified)"""
        # This would need more sophisticated logic based on the actual transaction data
        # For now, we'll use a simplified heuristic
        return txn1.amount != txn2.amount or abs(txn1.amount - txn2.amount) > min(txn1.amount, txn2.amount) * 0.1

    async def _calculate_sandwich_value(
        self,
        front_txn: MEVTransaction,
        victim_txn: MEVTransaction,
        back_txn: MEVTransaction
    ) -> float:
        """Calculate the extracted value from a sandwich attack"""
        # Simplified calculation - would need more sophisticated price impact modeling
        # This would involve calculating the price impact of the victim transaction
        # and how the front/back transactions exploit that impact

        # Placeholder calculation
        price_impact = victim_txn.amount * 0.01  # 1% price impact assumption
        extracted_value = price_impact * 0.5  # 50% of price impact captured

        return extracted_value

    async def _calculate_sandwich_confidence(
        self,
        front_txn: MEVTransaction,
        victim_txn: MEVTransaction,
        back_txn: MEVTransaction
    ) -> float:
        """Calculate confidence score for sandwich attack detection"""
        confidence = 0.0

        # Same sender for front and back
        if front_txn.sender == back_txn.sender:
            confidence += 0.3

        # Correct positioning
        if front_txn.position_in_block < victim_txn.position_in_block < back_txn.position_in_block:
            confidence += 0.2

        # Same asset/application
        if front_txn.asset_id == back_txn.asset_id or front_txn.application_id == back_txn.application_id:
            confidence += 0.2

        # Opposite directions
        if self._check_opposite_direction(front_txn, back_txn):
            confidence += 0.15

        # Higher fees for priority
        if front_txn.fee > victim_txn.fee:
            confidence += 0.1

        if back_txn.fee >= victim_txn.fee:
            confidence += 0.05

        return min(confidence, 1.0)

    def _is_likely_dex_transaction(self, txn: MEVTransaction) -> bool:
        """Check if transaction is likely a DEX transaction"""
        # Heuristics for DEX transactions
        if txn.application_id and txn.application_id > 0:
            return True

        # Check for asset transfers which might be DEX swaps
        if txn.asset_id and txn.asset_id > 0:
            return True

        return False

    async def _is_front_running_pattern(
        self,
        front_txn: MEVTransaction,
        following_txn: MEVTransaction
    ) -> bool:
        """Check if two transactions form a front-running pattern"""
        # Check positioning
        if front_txn.position_in_block >= following_txn.position_in_block:
            return False

        # Check if they target the same opportunity
        if front_txn.application_id != following_txn.application_id:
            return False

        # Check if front transaction has higher fee (priority)
        if front_txn.fee <= following_txn.fee:
            return False

        # Check if they're similar actions
        if not self._check_similar_action(front_txn, following_txn):
            return False

        return True

    def _check_similar_action(self, txn1: MEVTransaction, txn2: MEVTransaction) -> bool:
        """Check if two transactions represent similar actions"""
        # Simplified check - would need more sophisticated analysis
        return (txn1.asset_id == txn2.asset_id or
                txn1.application_id == txn2.application_id)

    async def _calculate_front_run_value(
        self,
        front_txn: MEVTransaction,
        following_txn: MEVTransaction
    ) -> float:
        """Calculate extracted value from front-running"""
        # Simplified calculation
        return front_txn.amount * 0.005  # 0.5% of transaction value

    async def _calculate_front_run_confidence(
        self,
        front_txn: MEVTransaction,
        following_txn: MEVTransaction
    ) -> float:
        """Calculate confidence for front-running detection"""
        confidence = 0.0

        # Position advantage
        if front_txn.position_in_block < following_txn.position_in_block:
            confidence += 0.25

        # Fee advantage
        if front_txn.fee > following_txn.fee:
            confidence += 0.25

        # Same target
        if front_txn.application_id == following_txn.application_id:
            confidence += 0.25

        # Similar action
        if self._check_similar_action(front_txn, following_txn):
            confidence += 0.25

        return confidence

    async def _find_arbitrage_sequences(
        self,
        transactions: List[MEVTransaction]
    ) -> List[List[MEVTransaction]]:
        """Find arbitrage sequences in a sender's transactions"""
        sequences = []

        if len(transactions) < 2:
            return sequences

        # Look for round-trip patterns
        for i in range(len(transactions)):
            for j in range(i + 1, len(transactions)):
                if self._check_round_trip([transactions[i], transactions[j]]):
                    sequences.append([transactions[i], transactions[j]])

        return sequences

    def _check_round_trip(self, transactions: List[MEVTransaction]) -> bool:
        """Check if transactions form a round-trip arbitrage"""
        if len(transactions) < 2:
            return False

        # Simplified check - would need more sophisticated analysis
        start_txn = transactions[0]
        end_txn = transactions[-1]

        # Check if starting and ending assets are related
        return start_txn.asset_id != end_txn.asset_id

    async def _calculate_arbitrage_value(self, sequence: List[MEVTransaction]) -> float:
        """Calculate arbitrage profit"""
        # Simplified calculation - would need price feed data
        total_in = sum(txn.amount for txn in sequence if txn.amount > 0)
        return total_in * 0.02  # 2% profit assumption

    async def _calculate_arbitrage_confidence(self, sequence: List[MEVTransaction]) -> float:
        """Calculate confidence for arbitrage detection"""
        confidence = 0.0

        # Multiple applications involved
        apps = set(txn.application_id for txn in sequence if txn.application_id)
        if len(apps) > 1:
            confidence += 0.4

        # Round-trip pattern
        if self._check_round_trip(sequence):
            confidence += 0.3

        # Profit potential
        if len(sequence) >= 3:
            confidence += 0.3

        return confidence

    def _is_likely_liquidation(self, txn: MEVTransaction) -> bool:
        """Check if transaction is likely a liquidation"""
        # Heuristics for liquidation transactions
        # This would need to be customized based on lending protocol specifics
        return txn.amount > 10000  # Large amount threshold

    async def _find_liquidation_related_transactions(
        self,
        liquidation_txn: MEVTransaction,
        block_transactions: List[MEVTransaction]
    ) -> List[MEVTransaction]:
        """Find transactions related to a liquidation"""
        related = []

        for txn in block_transactions:
            if (txn.sender == liquidation_txn.sender and
                txn.txn_id != liquidation_txn.txn_id and
                abs(txn.position_in_block - liquidation_txn.position_in_block) <= 3):
                related.append(txn)

        return related

    async def _calculate_liquidation_mev_value(
        self,
        liquidation_txn: MEVTransaction,
        related_txns: List[MEVTransaction]
    ) -> float:
        """Calculate MEV value from liquidation"""
        # Simplified calculation - would need liquidation bonus data
        return liquidation_txn.amount * 0.05  # 5% liquidation bonus

    async def _calculate_liquidation_confidence(
        self,
        liquidation_txn: MEVTransaction,
        related_txns: List[MEVTransaction]
    ) -> float:
        """Calculate confidence for liquidation MEV"""
        confidence = 0.5  # Base confidence for identified liquidation

        # Additional related transactions
        confidence += min(len(related_txns) * 0.1, 0.3)

        # Large amount
        if liquidation_txn.amount > 50000:
            confidence += 0.2

        return min(confidence, 1.0)

    async def _detect_flash_loan_patterns(
        self,
        transactions: List[MEVTransaction]
    ) -> List[MEVPattern]:
        """Detect flash loan MEV patterns"""
        patterns = []

        # Look for large borrowing followed by repayment patterns
        # This would need more sophisticated analysis of lending protocols

        return patterns

    def generate_mev_analytics(self, patterns: List[MEVPattern]) -> MEVAnalytics:
        """Generate analytics from detected MEV patterns"""
        if not patterns:
            return MEVAnalytics(
                total_mev_extracted=0,
                mev_per_block=0,
                mev_transactions_ratio=0,
                top_mev_extractors=[],
                victim_impact_analysis={},
                temporal_patterns={}
            )

        # Total MEV extracted
        total_mev = sum(pattern.extracted_value for pattern in patterns)

        # MEV per block
        blocks = set(txn.block_number for pattern in patterns for txn in pattern.transactions)
        mev_per_block = total_mev / len(blocks) if blocks else 0

        # Top extractors
        extractor_totals = defaultdict(float)
        for pattern in patterns:
            extractor_totals[pattern.exploiter_address] += pattern.extracted_value

        top_extractors = sorted(
            extractor_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Victim impact
        victim_impacts = defaultdict(float)
        for pattern in patterns:
            for victim in pattern.victim_addresses:
                victim_impacts[victim] += pattern.extracted_value

        # Temporal patterns
        pattern_types_by_hour = defaultdict(list)
        for pattern in patterns:
            if pattern.transactions:
                hour = pattern.transactions[0].timestamp.hour
                pattern_types_by_hour[hour].append(pattern.mev_type.value)

        temporal_patterns = {
            'hourly_distribution': dict(pattern_types_by_hour),
            'peak_hours': sorted(
                pattern_types_by_hour.keys(),
                key=lambda h: len(pattern_types_by_hour[h]),
                reverse=True
            )[:3]
        }

        return MEVAnalytics(
            total_mev_extracted=total_mev,
            mev_per_block=mev_per_block,
            mev_transactions_ratio=len(patterns) / max(len(set(
                txn.txn_id for pattern in patterns for txn in pattern.transactions
            )), 1),
            top_mev_extractors=top_extractors,
            victim_impact_analysis=dict(victim_impacts),
            temporal_patterns=temporal_patterns
        )

    def create_mev_alert(self, pattern: MEVPattern) -> RiskAlert:
        """Create an alert for detected MEV pattern"""
        severity = RiskLevel.HIGH if pattern.confidence_score > 0.8 else RiskLevel.MODERATE

        return RiskAlert(
            alert_id=f"mev_{pattern.pattern_id}",
            alert_type=f"MEV_{pattern.mev_type.value.upper()}",
            severity=severity,
            title=f"MEV Detected: {pattern.mev_type.value.replace('_', ' ').title()}",
            description=f"Detected {pattern.mev_type.value} with extracted value of {pattern.extracted_value:.2f}",
            affected_addresses=pattern.victim_addresses,
            affected_protocols=[],
            risk_score=pattern.confidence_score,
            confidence=pattern.confidence_score,
            detection_method=pattern.detection_method,
            evidence=pattern.evidence,
            recommendations=[
                "Monitor affected addresses for continued exploitation",
                "Consider implementing MEV protection mechanisms",
                "Review transaction ordering policies",
                "Implement fair sequencing protocols"
            ]
        )