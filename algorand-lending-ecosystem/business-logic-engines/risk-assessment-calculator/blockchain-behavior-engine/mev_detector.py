"""
MEV (Maximal Extractable Value) Exploitation Detection Engine

Detects and analyzes MEV extraction patterns including:
- Front-running attacks
- Back-running strategies
- Sandwich attacks
- Arbitrage exploitation
- Liquidation bot activities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from collections import defaultdict

from .models import MEVRiskIndicator, MEVType, RiskLevel

logger = logging.getLogger(__name__)


class MEVExploitationDetector:
    """
    Detects MEV exploitation patterns and calculates associated risks
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for MEV detection"""
        return {
            'front_running_window_seconds': 30,
            'sandwich_detection_window_seconds': 60,
            'arbitrage_profit_threshold': 0.01,  # 1% minimum profit
            'liquidation_bot_frequency_threshold': 5,  # transactions per hour
            'mev_detection_confidence_threshold': 0.6,
            'block_position_analysis_enabled': True,
            'max_blocks_analyzed': 1000
        }

    async def detect_mev_activity(
        self,
        address: str,
        analysis_days: int
    ) -> List[MEVRiskIndicator]:
        """
        Detect MEV exploitation activities for an address

        Args:
            address: Address to analyze for MEV activity
            analysis_days: Number of days to analyze

        Returns:
            List of MEV risk indicators
        """
        try:
            logger.info(f"Starting MEV detection for address: {address}")

            # Get transaction history with block positioning
            transactions = await self._get_detailed_transaction_history(address, analysis_days)

            if not transactions:
                logger.info("No transactions found for MEV analysis")
                return []

            # Run parallel MEV detection strategies
            detection_tasks = [
                self._detect_front_running(address, transactions),
                self._detect_back_running(address, transactions),
                self._detect_sandwich_attacks(address, transactions),
                self._detect_arbitrage_patterns(address, transactions),
                self._detect_liquidation_bot_activity(address, transactions)
            ]

            mev_results = await asyncio.gather(*detection_tasks, return_exceptions=True)

            # Consolidate all MEV indicators
            all_indicators = []
            for result in mev_results:
                if isinstance(result, list):
                    all_indicators.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"MEV detection error: {result}")

            # Filter high-confidence indicators
            significant_indicators = [
                indicator for indicator in all_indicators
                if indicator.detection_confidence >= self.config['mev_detection_confidence_threshold']
            ]

            logger.info(f"Detected {len(significant_indicators)} high-confidence MEV indicators")
            return sorted(significant_indicators, key=lambda x: x.detection_confidence, reverse=True)

        except Exception as e:
            logger.error(f"Error in MEV detection: {e}")
            raise

    async def _detect_front_running(self, address: str, transactions: List[Dict]) -> List[MEVRiskIndicator]:
        """Detect front-running attack patterns"""
        indicators = []

        try:
            window_seconds = self.config['front_running_window_seconds']

            # Group transactions by blocks to analyze ordering
            block_groups = defaultdict(list)
            for txn in transactions:
                block_num = txn.get('confirmed_round', 0)
                block_groups[block_num].append(txn)

            for block_num, block_txns in block_groups.items():
                if len(block_txns) < 2:
                    continue

                # Sort by intra-block position
                sorted_txns = sorted(block_txns, key=lambda x: x.get('intra_round_offset', 0))

                # Look for front-running patterns
                for i, txn in enumerate(sorted_txns[:-1]):
                    next_txn = sorted_txns[i + 1]

                    # Check if this could be front-running
                    if await self._is_potential_front_running(txn, next_txn):
                        profit = await self._calculate_front_running_profit(txn, next_txn)

                        if profit > 0:
                            confidence = self._calculate_front_running_confidence(
                                txn, next_txn, profit
                            )

                            indicator = MEVRiskIndicator(
                                mev_type=MEVType.FRONT_RUNNING,
                                target_address=next_txn.get('sender', ''),
                                exploiter_address=address,
                                transaction_sequence=[txn['id'], next_txn['id']],
                                profit_extracted=profit,
                                block_position_manipulation=True,
                                time_between_txns_ms=0,  # Same block
                                detection_confidence=confidence,
                                impact_severity=self._determine_impact_severity(profit)
                            )
                            indicators.append(indicator)

        except Exception as e:
            logger.error(f"Error in front-running detection: {e}")

        return indicators

    async def _detect_back_running(self, address: str, transactions: List[Dict]) -> List[MEVRiskIndicator]:
        """Detect back-running strategy patterns"""
        indicators = []

        try:
            # Look for transactions that follow large transactions quickly
            for i, txn in enumerate(transactions[1:], 1):
                prev_txn = transactions[i-1]

                # Check timing
                time_diff = await self._calculate_time_difference(prev_txn, txn)
                if time_diff > 60:  # More than 1 minute apart
                    continue

                # Check if this is back-running
                if await self._is_potential_back_running(prev_txn, txn):
                    profit = await self._calculate_back_running_profit(prev_txn, txn)

                    if profit > 0:
                        confidence = self._calculate_back_running_confidence(
                            prev_txn, txn, profit, time_diff
                        )

                        indicator = MEVRiskIndicator(
                            mev_type=MEVType.BACK_RUNNING,
                            target_address=prev_txn.get('sender', ''),
                            exploiter_address=address,
                            transaction_sequence=[prev_txn['id'], txn['id']],
                            profit_extracted=profit,
                            block_position_manipulation=time_diff < 30,  # Very fast follow-up
                            time_between_txns_ms=int(time_diff * 1000),
                            detection_confidence=confidence,
                            impact_severity=self._determine_impact_severity(profit)
                        )
                        indicators.append(indicator)

        except Exception as e:
            logger.error(f"Error in back-running detection: {e}")

        return indicators

    async def _detect_sandwich_attacks(self, address: str, transactions: List[Dict]) -> List[MEVRiskIndicator]:
        """Detect sandwich attack patterns"""
        indicators = []

        try:
            window_seconds = self.config['sandwich_detection_window_seconds']

            # Look for buy-victim-sell patterns
            for i, buy_txn in enumerate(transactions):
                if not await self._is_buy_transaction(buy_txn):
                    continue

                # Look for victim transactions within window
                for j, victim_txn in enumerate(transactions[i+1:], i+1):
                    if not await self._is_victim_transaction(buy_txn, victim_txn):
                        continue

                    time_to_victim = await self._calculate_time_difference(buy_txn, victim_txn)
                    if time_to_victim > window_seconds:
                        break

                    # Look for corresponding sell transaction
                    for k, sell_txn in enumerate(transactions[j+1:], j+1):
                        if not await self._is_sell_transaction(buy_txn, sell_txn):
                            continue

                        time_to_sell = await self._calculate_time_difference(victim_txn, sell_txn)
                        if time_to_sell > window_seconds:
                            break

                        # Calculate sandwich profit
                        profit = await self._calculate_sandwich_profit(buy_txn, sell_txn, victim_txn)

                        if profit > 0:
                            confidence = self._calculate_sandwich_confidence(
                                buy_txn, victim_txn, sell_txn, profit
                            )

                            indicator = MEVRiskIndicator(
                                mev_type=MEVType.SANDWICH_ATTACK,
                                target_address=victim_txn.get('sender', ''),
                                exploiter_address=address,
                                transaction_sequence=[buy_txn['id'], victim_txn['id'], sell_txn['id']],
                                profit_extracted=profit,
                                block_position_manipulation=True,
                                time_between_txns_ms=int((time_to_victim + time_to_sell) * 1000),
                                detection_confidence=confidence,
                                impact_severity=self._determine_impact_severity(profit)
                            )
                            indicators.append(indicator)

        except Exception as e:
            logger.error(f"Error in sandwich attack detection: {e}")

        return indicators

    async def _detect_arbitrage_patterns(self, address: str, transactions: List[Dict]) -> List[MEVRiskIndicator]:
        """Detect arbitrage exploitation patterns"""
        indicators = []

        try:
            # Group transactions by asset to detect arbitrage cycles
            asset_groups = defaultdict(list)
            for txn in transactions:
                if txn.get('tx_type') == 'axfer':  # Asset transfer
                    asset_id = txn.get('asset_id', 0)
                    asset_groups[asset_id].append(txn)

            for asset_id, asset_txns in asset_groups.items():
                if len(asset_txns) < 2:
                    continue

                # Look for buy-sell cycles that indicate arbitrage
                arbitrage_cycles = await self._identify_arbitrage_cycles(asset_txns)

                for cycle in arbitrage_cycles:
                    profit = await self._calculate_arbitrage_profit(cycle)

                    if profit >= self.config['arbitrage_profit_threshold']:
                        confidence = self._calculate_arbitrage_confidence(cycle, profit)

                        indicator = MEVRiskIndicator(
                            mev_type=MEVType.ARBITRAGE,
                            target_address='',  # No specific target for arbitrage
                            exploiter_address=address,
                            transaction_sequence=[txn['id'] for txn in cycle],
                            profit_extracted=profit,
                            block_position_manipulation=False,
                            time_between_txns_ms=await self._calculate_cycle_duration_ms(cycle),
                            detection_confidence=confidence,
                            impact_severity=self._determine_impact_severity(profit)
                        )
                        indicators.append(indicator)

        except Exception as e:
            logger.error(f"Error in arbitrage detection: {e}")

        return indicators

    async def _detect_liquidation_bot_activity(self, address: str, transactions: List[Dict]) -> List[MEVRiskIndicator]:
        """Detect automated liquidation bot patterns"""
        indicators = []

        try:
            # Look for high-frequency liquidation patterns
            liquidation_txns = [
                txn for txn in transactions
                if await self._is_liquidation_transaction(txn)
            ]

            if len(liquidation_txns) < self.config['liquidation_bot_frequency_threshold']:
                return indicators

            # Analyze liquidation frequency and timing
            hourly_buckets = defaultdict(list)
            for txn in liquidation_txns:
                timestamp = datetime.fromisoformat(txn['confirmed_time'])
                hour_bucket = timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_buckets[hour_bucket].append(txn)

            # Find high-frequency liquidation periods
            for hour, hour_txns in hourly_buckets.items():
                if len(hour_txns) >= self.config['liquidation_bot_frequency_threshold']:
                    total_profit = sum(
                        await self._calculate_liquidation_profit(txn) for txn in hour_txns
                    )

                    confidence = self._calculate_liquidation_bot_confidence(hour_txns)

                    indicator = MEVRiskIndicator(
                        mev_type=MEVType.LIQUIDATION_BOT,
                        target_address='',  # Multiple targets
                        exploiter_address=address,
                        transaction_sequence=[txn['id'] for txn in hour_txns],
                        profit_extracted=total_profit,
                        block_position_manipulation=False,
                        time_between_txns_ms=3600000,  # 1 hour window
                        detection_confidence=confidence,
                        impact_severity=self._determine_impact_severity(total_profit)
                    )
                    indicators.append(indicator)

        except Exception as e:
            logger.error(f"Error in liquidation bot detection: {e}")

        return indicators

    def _determine_impact_severity(self, profit: float) -> RiskLevel:
        """Determine impact severity based on profit extracted"""
        if profit >= 1000:  # 1000 ALGO or equivalent
            return RiskLevel.CRITICAL
        elif profit >= 100:
            return RiskLevel.HIGH
        elif profit >= 10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_front_running_confidence(self, front_txn: Dict, victim_txn: Dict, profit: float) -> float:
        """Calculate confidence for front-running detection"""
        confidence = 0.0

        # Block position factor
        if front_txn.get('intra_round_offset', 0) < victim_txn.get('intra_round_offset', 0):
            confidence += 0.4

        # Profit factor
        if profit > 10:
            confidence += 0.3
        elif profit > 1:
            confidence += 0.2

        # Transaction similarity factor
        if await self._transactions_target_same_asset(front_txn, victim_txn):
            confidence += 0.3

        return min(confidence, 1.0)

    def _calculate_back_running_confidence(self, prev_txn: Dict, back_txn: Dict, profit: float, time_diff: float) -> float:
        """Calculate confidence for back-running detection"""
        confidence = 0.0

        # Timing factor
        if time_diff < 10:  # Very quick follow-up
            confidence += 0.4
        elif time_diff < 30:
            confidence += 0.2

        # Profit factor
        if profit > 5:
            confidence += 0.3

        # Transaction relationship factor
        if await self._is_related_to_previous_transaction(prev_txn, back_txn):
            confidence += 0.3

        return min(confidence, 1.0)

    def _calculate_sandwich_confidence(self, buy_txn: Dict, victim_txn: Dict, sell_txn: Dict, profit: float) -> float:
        """Calculate confidence for sandwich attack detection"""
        confidence = 0.0

        # Pattern completeness
        confidence += 0.3

        # Profit factor
        if profit > 10:
            confidence += 0.4
        elif profit > 1:
            confidence += 0.2

        # Asset consistency
        if await self._sandwich_targets_consistent_asset(buy_txn, victim_txn, sell_txn):
            confidence += 0.3

        return min(confidence, 1.0)

    def _calculate_arbitrage_confidence(self, cycle: List[Dict], profit: float) -> float:
        """Calculate confidence for arbitrage detection"""
        confidence = 0.0

        # Cycle completeness
        if len(cycle) >= 2:
            confidence += 0.3

        # Profit margin
        if profit >= 0.05:  # 5% profit
            confidence += 0.4
        elif profit >= 0.02:
            confidence += 0.2

        # Time efficiency
        cycle_duration = await self._calculate_cycle_duration_ms(cycle)
        if cycle_duration < 300000:  # Less than 5 minutes
            confidence += 0.3

        return min(confidence, 1.0)

    def _calculate_liquidation_bot_confidence(self, liquidation_txns: List[Dict]) -> float:
        """Calculate confidence for liquidation bot detection"""
        frequency = len(liquidation_txns)

        # Base confidence from frequency
        confidence = min(frequency / 20, 0.5)  # Max 0.5 from frequency

        # Timing regularity
        times = [datetime.fromisoformat(txn['confirmed_time']) for txn in liquidation_txns]
        if len(times) > 1:
            intervals = [(times[i] - times[i-1]).total_seconds() for i in range(1, len(times))]
            if np.std(intervals) < np.mean(intervals) * 0.5:  # Regular intervals
                confidence += 0.3

        # Success rate
        successful = sum(1 for txn in liquidation_txns if txn.get('success', True))
        success_rate = successful / len(liquidation_txns)
        confidence += success_rate * 0.2

        return min(confidence, 1.0)

    # Helper methods with placeholder implementations

    async def _get_detailed_transaction_history(self, address: str, days: int) -> List[Dict]:
        """Get detailed transaction history with block positioning"""
        # Placeholder - would get actual blockchain data with intra-block positioning
        mock_transactions = []
        base_time = datetime.utcnow() - timedelta(days=days)

        for i in range(50):
            mock_transactions.append({
                'id': f'mev_txn_{i}',
                'sender': address,
                'receiver': f'RECEIVER_{i % 5}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                'amount': 1000000 + (i * 50000),
                'confirmed_time': (base_time + timedelta(minutes=i*15)).isoformat(),
                'confirmed_round': 1000000 + (i // 5),
                'intra_round_offset': i % 5,
                'tx_type': 'pay',
                'asset_id': 123 if i % 3 == 0 else None
            })

        return mock_transactions

    async def _calculate_time_difference(self, txn1: Dict, txn2: Dict) -> float:
        """Calculate time difference between transactions in seconds"""
        time1 = datetime.fromisoformat(txn1['confirmed_time'])
        time2 = datetime.fromisoformat(txn2['confirmed_time'])
        return abs((time2 - time1).total_seconds())

    async def _is_potential_front_running(self, txn1: Dict, txn2: Dict) -> bool:
        """Check if transaction pair indicates front-running"""
        # Placeholder logic
        return (txn1.get('intra_round_offset', 0) < txn2.get('intra_round_offset', 0) and
                await self._transactions_target_same_asset(txn1, txn2))

    async def _is_potential_back_running(self, prev_txn: Dict, txn: Dict) -> bool:
        """Check if transaction indicates back-running"""
        # Placeholder logic
        return await self._is_related_to_previous_transaction(prev_txn, txn)

    async def _is_buy_transaction(self, txn: Dict) -> bool:
        """Check if transaction is a buy order"""
        # Placeholder logic
        return txn.get('tx_type') == 'axfer' and txn.get('amount', 0) > 0

    async def _is_sell_transaction(self, buy_txn: Dict, sell_txn: Dict) -> bool:
        """Check if transaction is a corresponding sell order"""
        # Placeholder logic
        return (sell_txn.get('tx_type') == 'axfer' and
                sell_txn.get('asset_id') == buy_txn.get('asset_id'))

    async def _is_victim_transaction(self, buy_txn: Dict, victim_txn: Dict) -> bool:
        """Check if transaction is a potential sandwich victim"""
        # Placeholder logic
        return (victim_txn.get('tx_type') == 'axfer' and
                victim_txn.get('asset_id') == buy_txn.get('asset_id'))

    async def _is_liquidation_transaction(self, txn: Dict) -> bool:
        """Check if transaction is a liquidation"""
        # Placeholder logic - would check for liquidation app calls
        return txn.get('tx_type') == 'appl' and 'liquidate' in str(txn.get('app_args', []))

    async def _transactions_target_same_asset(self, txn1: Dict, txn2: Dict) -> bool:
        """Check if transactions target the same asset"""
        return txn1.get('asset_id') == txn2.get('asset_id')

    async def _is_related_to_previous_transaction(self, prev_txn: Dict, txn: Dict) -> bool:
        """Check if transaction is related to previous one"""
        # Placeholder logic
        return prev_txn.get('receiver') == txn.get('sender')

    async def _sandwich_targets_consistent_asset(self, buy_txn: Dict, victim_txn: Dict, sell_txn: Dict) -> bool:
        """Check if sandwich attack targets consistent asset"""
        asset_id = buy_txn.get('asset_id')
        return (asset_id == victim_txn.get('asset_id') and
                asset_id == sell_txn.get('asset_id'))

    async def _identify_arbitrage_cycles(self, asset_txns: List[Dict]) -> List[List[Dict]]:
        """Identify potential arbitrage cycles"""
        # Placeholder - would implement cycle detection algorithm
        cycles = []
        if len(asset_txns) >= 2:
            cycles.append(asset_txns[:2])  # Simple 2-transaction cycle
        return cycles

    async def _calculate_cycle_duration_ms(self, cycle: List[Dict]) -> int:
        """Calculate duration of arbitrage cycle in milliseconds"""
        if len(cycle) < 2:
            return 0

        start_time = datetime.fromisoformat(cycle[0]['confirmed_time'])
        end_time = datetime.fromisoformat(cycle[-1]['confirmed_time'])
        return int((end_time - start_time).total_seconds() * 1000)

    # Profit calculation methods (placeholders)
    async def _calculate_front_running_profit(self, front_txn: Dict, victim_txn: Dict) -> float:
        """Calculate profit from front-running"""
        return 5.0  # Placeholder

    async def _calculate_back_running_profit(self, prev_txn: Dict, back_txn: Dict) -> float:
        """Calculate profit from back-running"""
        return 3.0  # Placeholder

    async def _calculate_sandwich_profit(self, buy_txn: Dict, sell_txn: Dict, victim_txn: Dict) -> float:
        """Calculate profit from sandwich attack"""
        return 15.0  # Placeholder

    async def _calculate_arbitrage_profit(self, cycle: List[Dict]) -> float:
        """Calculate profit from arbitrage cycle"""
        return 0.03  # 3% placeholder

    async def _calculate_liquidation_profit(self, txn: Dict) -> float:
        """Calculate profit from liquidation"""
        return 2.0  # Placeholder