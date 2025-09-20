"""
Flash Loan Risk Detector

Specialized detector for flash loan attacks, arbitrage patterns,
and MEV exploitation in DeFi protocols.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from ...common.models.blockchain_risk import RiskLevel, RiskAlert


@dataclass
class FlashLoanPattern:
    """Flash loan pattern detection result"""
    pattern_type: str
    confidence: float
    profit_estimate: float
    risk_level: str
    transactions_involved: int
    time_window: timedelta
    evidence: Dict[str, Any]


class FlashLoanRiskDetector:
    """Specialized flash loan and MEV risk detector"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.flash_loan_config = config.get('risk_assessment', {}).get('transaction_patterns', {}).get('flash_loan_arbitrage', {})

    async def detect_flash_loan_patterns(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ) -> List[FlashLoanPattern]:
        """Detect flash loan and arbitrage patterns"""
        patterns = []

        if not transactions:
            return patterns

        try:
            # Detect atomic arbitrage sequences
            atomic_patterns = await self._detect_atomic_arbitrage(transactions)
            patterns.extend(atomic_patterns)

            # Detect flash loan borrowing patterns
            flash_patterns = await self._detect_flash_loan_usage(transactions)
            patterns.extend(flash_patterns)

            # Detect liquidation front-running
            liquidation_patterns = await self._detect_liquidation_frontrun(transactions)
            patterns.extend(liquidation_patterns)

            # Detect oracle manipulation patterns
            oracle_patterns = await self._detect_oracle_manipulation(transactions)
            patterns.extend(oracle_patterns)

            return patterns

        except Exception as e:
            self.logger.error(f"Flash loan pattern detection failed for {wallet_address}: {e}")
            return []

    async def _detect_atomic_arbitrage(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[FlashLoanPattern]:
        """Detect atomic arbitrage patterns within single blocks"""
        patterns = []

        # Group transactions by block
        block_groups = defaultdict(list)
        for txn in transactions:
            block_num = txn.get('confirmed-round', 0)
            if block_num:
                block_groups[block_num].append(txn)

        for block_num, block_txns in block_groups.items():
            if len(block_txns) < 3:  # Need at least 3 transactions for arbitrage
                continue

            # Sort by transaction position in block
            sorted_txns = sorted(
                block_txns,
                key=lambda x: x.get('intra-round-offset', 0)
            )

            # Look for arbitrage patterns
            arbitrage_pattern = await self._analyze_arbitrage_sequence(sorted_txns, block_num)
            if arbitrage_pattern:
                patterns.append(arbitrage_pattern)

        return patterns

    async def _analyze_arbitrage_sequence(
        self,
        block_transactions: List[Dict[str, Any]],
        block_num: int
    ) -> Optional[FlashLoanPattern]:
        """Analyze a sequence of transactions for arbitrage patterns"""

        # Look for DEX interactions across multiple protocols
        dex_interactions = []
        for txn in block_transactions:
            if txn.get('tx-type') == 'appl':  # Application call
                app_id = txn.get('application-id')
                if app_id:  # Could be DEX interaction
                    dex_interactions.append(txn)

        if len(dex_interactions) < 2:
            return None

        # Calculate potential profit
        total_in = 0
        total_out = 0

        for txn in dex_interactions:
            amount = float(txn.get('amount', 0))
            if txn.get('sender') == txn.get('sender'):  # Outgoing
                total_out += amount
            else:  # Incoming
                total_in += amount

        estimated_profit = total_in - total_out

        # Check profit threshold
        min_profit = self.flash_loan_config.get('min_volume_threshold', 10000)
        if estimated_profit < min_profit:
            return None

        # Calculate confidence based on pattern characteristics
        confidence = 0.7  # Base confidence for atomic sequence

        # Higher confidence for larger profits
        if estimated_profit > min_profit * 10:
            confidence += 0.2

        # Higher confidence for more complex sequences
        if len(dex_interactions) >= 4:
            confidence += 0.1

        return FlashLoanPattern(
            pattern_type="atomic_arbitrage",
            confidence=min(confidence, 1.0),
            profit_estimate=estimated_profit,
            risk_level="MODERATE",
            transactions_involved=len(dex_interactions),
            time_window=timedelta(seconds=0),  # Same block
            evidence={
                'block_number': block_num,
                'dex_interaction_count': len(dex_interactions),
                'estimated_profit': estimated_profit,
                'transaction_sequence': [txn.get('id', '') for txn in dex_interactions]
            }
        )

    async def _detect_flash_loan_usage(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[FlashLoanPattern]:
        """Detect flash loan borrowing and repayment patterns"""
        patterns = []

        # Look for large borrowing followed by repayment in short time
        sorted_txns = sorted(
            transactions,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        for i, txn in enumerate(sorted_txns):
            amount = float(txn.get('amount', 0))

            # Look for large incoming transactions (potential flash loan)
            if amount > 50000 and txn.get('sender') != txn.get('receiver'):
                # Look for repayment within reasonable time window
                repayment_found = False
                txn_time = datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))

                for j in range(i + 1, min(i + 10, len(sorted_txns))):  # Check next 10 transactions
                    later_txn = sorted_txns[j]
                    later_amount = float(later_txn.get('amount', 0))
                    later_time = datetime.fromisoformat(later_txn.get('timestamp', '1970-01-01'))

                    # Check if this could be repayment
                    if (later_time - txn_time) < timedelta(hours=1):  # Within 1 hour
                        if abs(later_amount - amount) / amount < 0.1:  # Similar amount
                            repayment_found = True

                            pattern = FlashLoanPattern(
                                pattern_type="flash_loan_usage",
                                confidence=0.8,
                                profit_estimate=later_amount - amount,  # Interest/fees
                                risk_level="HIGH",
                                transactions_involved=2,
                                time_window=later_time - txn_time,
                                evidence={
                                    'borrow_amount': amount,
                                    'repay_amount': later_amount,
                                    'time_window_minutes': (later_time - txn_time).total_seconds() / 60,
                                    'borrow_txn_id': txn.get('id', ''),
                                    'repay_txn_id': later_txn.get('id', '')
                                }
                            )
                            patterns.append(pattern)
                            break

        return patterns

    async def _detect_liquidation_frontrun(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[FlashLoanPattern]:
        """Detect liquidation front-running patterns"""
        patterns = []

        # Look for liquidation-related transactions
        liquidation_txns = []
        for txn in transactions:
            # Heuristics for liquidation transactions
            if (txn.get('tx-type') == 'appl' and
                float(txn.get('amount', 0)) > 10000):  # Large application call
                liquidation_txns.append(txn)

        if len(liquidation_txns) < 2:
            return patterns

        # Sort by timestamp
        sorted_liquidations = sorted(
            liquidation_txns,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        # Look for rapid sequences that could indicate front-running
        for i in range(len(sorted_liquidations) - 1):
            txn1 = sorted_liquidations[i]
            txn2 = sorted_liquidations[i + 1]

            time1 = datetime.fromisoformat(txn1.get('timestamp', '1970-01-01'))
            time2 = datetime.fromisoformat(txn2.get('timestamp', '1970-01-01'))

            time_diff = time2 - time1

            # Front-running typically happens within seconds
            if time_diff < timedelta(seconds=30):
                amount1 = float(txn1.get('amount', 0))
                amount2 = float(txn2.get('amount', 0))

                pattern = FlashLoanPattern(
                    pattern_type="liquidation_frontrun",
                    confidence=0.6,
                    profit_estimate=max(amount1, amount2) * 0.05,  # Estimated 5% profit
                    risk_level="HIGH",
                    transactions_involved=2,
                    time_window=time_diff,
                    evidence={
                        'time_gap_seconds': time_diff.total_seconds(),
                        'first_txn_amount': amount1,
                        'second_txn_amount': amount2,
                        'first_txn_id': txn1.get('id', ''),
                        'second_txn_id': txn2.get('id', '')
                    }
                )
                patterns.append(pattern)

        return patterns

    async def _detect_oracle_manipulation(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[FlashLoanPattern]:
        """Detect oracle manipulation patterns"""
        patterns = []

        # Look for patterns that could indicate oracle manipulation
        large_volume_txns = [
            txn for txn in transactions
            if float(txn.get('amount', 0)) > 100000  # Large volume threshold
        ]

        if len(large_volume_txns) < 2:
            return patterns

        # Group by time proximity
        time_groups = []
        sorted_txns = sorted(
            large_volume_txns,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
        )

        current_group = [sorted_txns[0]]
        base_time = datetime.fromisoformat(sorted_txns[0].get('timestamp', '1970-01-01'))

        for txn in sorted_txns[1:]:
            txn_time = datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))
            if (txn_time - base_time) < timedelta(minutes=10):  # Within 10 minutes
                current_group.append(txn)
            else:
                if len(current_group) >= 3:  # Potential manipulation sequence
                    time_groups.append(current_group)
                current_group = [txn]
                base_time = txn_time

        if len(current_group) >= 3:
            time_groups.append(current_group)

        # Analyze each group for manipulation patterns
        for group in time_groups:
            if len(group) >= 3:
                total_volume = sum(float(txn.get('amount', 0)) for txn in group)

                first_time = datetime.fromisoformat(group[0].get('timestamp', '1970-01-01'))
                last_time = datetime.fromisoformat(group[-1].get('timestamp', '1970-01-01'))

                pattern = FlashLoanPattern(
                    pattern_type="oracle_manipulation",
                    confidence=0.5,  # Lower confidence as it's harder to detect
                    profit_estimate=total_volume * 0.02,  # Estimated 2% profit
                    risk_level="CRITICAL",
                    transactions_involved=len(group),
                    time_window=last_time - first_time,
                    evidence={
                        'transaction_count': len(group),
                        'total_volume': total_volume,
                        'time_window_minutes': (last_time - first_time).total_seconds() / 60,
                        'transaction_ids': [txn.get('id', '') for txn in group]
                    }
                )
                patterns.append(pattern)

        return patterns