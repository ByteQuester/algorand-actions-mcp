"""
Reputation Engine

Analyzes on-chain behavior to determine borrower reputation scores
and appropriate interest rate adjustments.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from algosdk.v2client import algod, indexer
from algosdk import account, encoding

from .models import (
    ReputationScore,
    OnChainBehavior,
    TransactionPattern,
    GovernanceParticipation,
    DeFiInteractionHistory,
    ReputationTier
)

logger = logging.getLogger(__name__)

class ReputationEngine:
    """
    Engine for analyzing on-chain behavior and determining reputation scores
    for interest rate adjustments.
    """

    def __init__(
        self,
        algod_client: algod.AlgodClient,
        indexer_client: indexer.IndexerClient,
        cache_ttl: int = 3600  # 1 hour
    ):
        self.algod_client = algod_client
        self.indexer_client = indexer_client
        self.cache_ttl = cache_ttl
        self._cache: Dict = {}
        self._cache_timestamps: Dict = {}

    async def calculate_reputation(
        self,
        address: str,
        analysis_period_days: int = 365
    ) -> ReputationScore:
        """
        Calculate comprehensive reputation score for an address
        """
        try:
            # Validate address
            if not encoding.is_valid_address(address):
                raise ValueError(f"Invalid Algorand address: {address}")

            # Get on-chain behavior data
            behavior = await self._analyze_onchain_behavior(address, analysis_period_days)

            # Get transaction patterns
            patterns = await self._analyze_transaction_patterns(address, analysis_period_days)

            # Get governance participation
            governance = await self._analyze_governance_participation(address)

            # Get DeFi interaction history
            defi_history = await self._analyze_defi_interactions(address, analysis_period_days)

            # Calculate component scores
            activity_score = behavior.activity_score()
            reliability_score = await self._calculate_reliability_score(behavior, patterns)
            sophistication_score = patterns.sophistication_score()
            governance_score = await self._calculate_governance_score(governance)
            defi_score = await self._calculate_defi_score(defi_history)

            # Calculate overall score with weights
            weights = {
                'activity': Decimal('0.25'),
                'reliability': Decimal('0.30'),
                'sophistication': Decimal('0.20'),
                'governance': Decimal('0.15'),
                'defi': Decimal('0.10')
            }

            overall_score = (
                activity_score * weights['activity'] +
                reliability_score * weights['reliability'] +
                sophistication_score * weights['sophistication'] +
                governance_score * weights['governance'] +
                defi_score * weights['defi']
            )

            # Determine tier
            tier = self._determine_tier(overall_score)

            # Identify risk flags and strengths
            risk_flags = await self._identify_risk_flags(behavior, patterns, defi_history)
            strengths = await self._identify_strengths(behavior, patterns, governance, defi_history)

            # Calculate confidence level
            confidence_level = await self._calculate_confidence(behavior, patterns)

            return ReputationScore(
                address=address,
                overall_score=overall_score,
                tier=tier,
                activity_score=activity_score,
                reliability_score=reliability_score,
                sophistication_score=sophistication_score,
                governance_score=governance_score,
                defi_score=defi_score,
                risk_flags=risk_flags,
                strengths=strengths,
                improvement_areas=await self._suggest_improvements(overall_score, behavior, patterns),
                confidence_level=confidence_level,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error calculating reputation for {address}: {e}")
            raise

    async def _analyze_onchain_behavior(
        self,
        address: str,
        days: int
    ) -> OnChainBehavior:
        """Analyze on-chain behavior metrics"""
        cache_key = f"behavior_{address}_{days}"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            # Get account information
            account_info = self.algod_client.account_info(address)

            # Get transaction history
            txns = await self._get_transaction_history(address, days)

            # Calculate metrics
            account_age = await self._calculate_account_age(address)
            total_transactions = len(txns)

            if total_transactions > 0:
                transaction_sizes = [Decimal(str(txn.get('payment-transaction', {}).get('amount', 0))) for txn in txns]
                avg_transaction_size = sum(transaction_sizes) / len(transaction_sizes)
                largest_transaction = max(transaction_sizes)

                # Calculate failed transaction rate
                failed_txns = sum(1 for txn in txns if txn.get('confirmed-round') is None)
                failed_rate = Decimal(failed_txns) / Decimal(total_transactions)
            else:
                avg_transaction_size = Decimal('0')
                largest_transaction = Decimal('0')
                failed_rate = Decimal('0')

            # Check for consistent activity
            consistent_activity = await self._check_activity_consistency(txns, days)

            # Count holdings
            assets = account_info.get('assets', [])
            nft_count = sum(1 for asset in assets if await self._is_nft(asset['asset-id']))
            asa_count = len(assets)

            # Count DeFi interactions
            defi_interactions = await self._count_defi_interactions(txns)

            # Check governance participation
            governance_participation = await self._check_governance_participation(address)

            behavior = OnChainBehavior(
                address=address,
                account_age_days=account_age,
                total_transactions=total_transactions,
                avg_transaction_size=avg_transaction_size,
                governance_participation=governance_participation,
                nft_holdings=nft_count,
                asa_holdings=asa_count,
                defi_protocol_interactions=defi_interactions,
                failed_transaction_rate=failed_rate,
                largest_transaction=largest_transaction,
                consistent_activity=consistent_activity,
                timestamp=datetime.utcnow()
            )

            self._cache[cache_key] = behavior
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return behavior

        except Exception as e:
            logger.error(f"Error analyzing on-chain behavior for {address}: {e}")
            raise

    async def _analyze_transaction_patterns(
        self,
        address: str,
        days: int
    ) -> TransactionPattern:
        """Analyze transaction patterns for sophistication scoring"""

        try:
            txns = await self._get_transaction_history(address, days)

            # Analyze timing patterns
            regular_intervals = await self._check_regular_intervals(txns)

            # Peak activity hours
            peak_hours = await self._calculate_peak_hours(txns)

            # Transaction types
            tx_types = [txn.get('tx-type', 'pay') for txn in txns]
            preferred_types = list(set(tx_types))

            # Gas optimization (fee analysis)
            gas_score = await self._calculate_gas_optimization(txns)

            # Multi-sig usage
            multi_sig = any(txn.get('multisig') for txn in txns)

            # Smart contract interactions
            sc_interactions = sum(1 for txn in txns if txn.get('tx-type') == 'appl')

            # Cross-chain activity (placeholder - would need bridge analysis)
            cross_chain = False

            return TransactionPattern(
                address=address,
                regular_transaction_intervals=regular_intervals,
                peak_activity_hours=peak_hours,
                preferred_transaction_types=preferred_types,
                gas_optimization_score=gas_score,
                multi_sig_usage=multi_sig,
                smart_contract_interactions=sc_interactions,
                cross_chain_activity=cross_chain,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error analyzing transaction patterns for {address}: {e}")
            # Return default pattern
            return TransactionPattern(
                address=address,
                regular_transaction_intervals=False,
                peak_activity_hours=[],
                preferred_transaction_types=['pay'],
                gas_optimization_score=Decimal('0.5'),
                multi_sig_usage=False,
                smart_contract_interactions=0,
                cross_chain_activity=False,
                timestamp=datetime.utcnow()
            )

    async def _get_transaction_history(self, address: str, days: int) -> List[Dict]:
        """Get transaction history for an address"""
        try:
            # Calculate date range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            # Query indexer for transactions
            txn_iter = self.indexer_client.search_transactions(
                address=address,
                start_time=start_time,
                limit=1000  # Limit to prevent excessive queries
            )

            transactions = []
            for txn in txn_iter:
                transactions.append(txn)

            return transactions

        except Exception as e:
            logger.warning(f"Error getting transaction history: {e}")
            return []

    async def _calculate_account_age(self, address: str) -> int:
        """Calculate account age in days"""
        try:
            # Get first transaction
            txn_iter = self.indexer_client.search_transactions(
                address=address,
                limit=1
            )

            first_txn = next(txn_iter, None)
            if first_txn:
                first_round = first_txn.get('confirmed-round', 0)
                # Approximate: 1 round ≈ 4.5 seconds
                age_seconds = first_round * 4.5
                return int(age_seconds / (24 * 3600))

            return 0

        except Exception:
            return 0

    async def _calculate_reliability_score(
        self,
        behavior: OnChainBehavior,
        patterns: TransactionPattern
    ) -> Decimal:
        """Calculate reliability score based on behavior and patterns"""

        scores = []

        # Low failed transaction rate is good
        failure_score = Decimal('1') - behavior.failed_transaction_rate
        scores.append(failure_score * Decimal('0.4'))

        # Consistent activity is good
        consistency_score = Decimal('1') if behavior.consistent_activity else Decimal('0.5')
        scores.append(consistency_score * Decimal('0.3'))

        # Regular intervals show planning
        interval_score = Decimal('1') if patterns.regular_transaction_intervals else Decimal('0.7')
        scores.append(interval_score * Decimal('0.3'))

        return sum(scores)

    async def _analyze_governance_participation(self, address: str) -> GovernanceParticipation:
        """Analyze governance participation"""
        # This would integrate with Algorand governance APIs
        # For now, return mock data
        return GovernanceParticipation(
            address=address,
            periods_participated=2,
            total_algo_committed=Decimal('10000'),
            voting_consistency=Decimal('0.8'),
            proposal_submissions=0,
            community_engagement_score=Decimal('0.6'),
            timestamp=datetime.utcnow()
        )

    async def _analyze_defi_interactions(self, address: str, days: int) -> DeFiInteractionHistory:
        """Analyze DeFi protocol interactions"""
        # This would analyze smart contract interactions with known DeFi protocols
        # For now, return mock data
        return DeFiInteractionHistory(
            address=address,
            protocols_used=['Tinyman', 'Algofi'],
            total_volume_usd=Decimal('50000'),
            liquidity_provided=Decimal('25000'),
            yield_farming_experience=True,
            lending_borrowing_history={'loans': 3, 'repayments': 3},
            liquidation_events=0,
            profit_loss_ratio=Decimal('1.2'),
            timestamp=datetime.utcnow()
        )

    async def _calculate_governance_score(self, governance: GovernanceParticipation) -> Decimal:
        """Calculate governance participation score"""
        if governance.periods_participated == 0:
            return Decimal('0')

        participation_score = min(Decimal(governance.periods_participated) / Decimal('4'), Decimal('1'))
        consistency_score = governance.voting_consistency
        engagement_score = governance.community_engagement_score

        return (participation_score + consistency_score + engagement_score) / Decimal('3')

    async def _calculate_defi_score(self, defi_history: DeFiInteractionHistory) -> Decimal:
        """Calculate DeFi experience score"""
        if not defi_history.protocols_used:
            return Decimal('0')

        protocol_diversity = min(Decimal(len(defi_history.protocols_used)) / Decimal('5'), Decimal('1'))
        volume_score = min(defi_history.total_volume_usd / Decimal('100000'), Decimal('1'))
        experience_score = Decimal('1') if defi_history.yield_farming_experience else Decimal('0.5')
        safety_score = Decimal('1') if defi_history.liquidation_events == 0 else Decimal('0.7')

        return (protocol_diversity + volume_score + experience_score + safety_score) / Decimal('4')

    def _determine_tier(self, score: Decimal) -> ReputationTier:
        """Determine reputation tier based on overall score"""
        if score >= Decimal('0.9'):
            return ReputationTier.EXCELLENT
        elif score >= Decimal('0.7'):
            return ReputationTier.GOOD
        elif score >= Decimal('0.5'):
            return ReputationTier.FAIR
        elif score >= Decimal('0.3'):
            return ReputationTier.POOR
        else:
            return ReputationTier.VERY_POOR

    # Helper methods (simplified implementations)
    async def _check_activity_consistency(self, txns: List[Dict], days: int) -> bool:
        """Check if account has consistent activity"""
        if len(txns) < 10:
            return False

        # Simple check: transactions in at least 30% of weeks
        weeks_with_activity = len(set(
            datetime.fromtimestamp(txn.get('round-time', 0)).isocalendar()[1]
            for txn in txns
        ))

        expected_weeks = max(days // 7, 1)
        return weeks_with_activity >= (expected_weeks * 0.3)

    async def _is_nft(self, asset_id: int) -> bool:
        """Check if an asset is an NFT"""
        # Simple heuristic: total supply = 1 and decimals = 0
        try:
            asset_info = self.algod_client.asset_info(asset_id)
            params = asset_info.get('params', {})
            return params.get('total', 0) == 1 and params.get('decimals', 0) == 0
        except:
            return False

    async def _count_defi_interactions(self, txns: List[Dict]) -> int:
        """Count DeFi protocol interactions"""
        # Count application calls (smart contract interactions)
        return sum(1 for txn in txns if txn.get('tx-type') == 'appl')

    async def _check_governance_participation(self, address: str) -> bool:
        """Check if address participates in governance"""
        # This would check against governance contract
        # For now, return mock data
        return True

    async def _check_regular_intervals(self, txns: List[Dict]) -> bool:
        """Check for regular transaction intervals"""
        if len(txns) < 5:
            return False

        # Simple check for some regularity
        timestamps = [txn.get('round-time', 0) for txn in txns]
        timestamps.sort()

        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval = sum(intervals) / len(intervals)

        # Check if most intervals are within 20% of average
        regular_count = sum(1 for interval in intervals if abs(interval - avg_interval) < avg_interval * 0.2)
        return regular_count >= len(intervals) * 0.6

    async def _calculate_peak_hours(self, txns: List[Dict]) -> List[int]:
        """Calculate peak activity hours"""
        hours = [datetime.fromtimestamp(txn.get('round-time', 0)).hour for txn in txns]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Return top 3 hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]

    async def _calculate_gas_optimization(self, txns: List[Dict]) -> Decimal:
        """Calculate gas optimization score based on fee patterns"""
        if not txns:
            return Decimal('0.5')

        fees = [Decimal(str(txn.get('fee', 1000))) for txn in txns]
        avg_fee = sum(fees) / len(fees)

        # Lower fees suggest optimization
        if avg_fee <= Decimal('1000'):  # Minimum fee
            return Decimal('1.0')
        elif avg_fee <= Decimal('2000'):
            return Decimal('0.8')
        else:
            return Decimal('0.5')

    async def _identify_risk_flags(
        self,
        behavior: OnChainBehavior,
        patterns: TransactionPattern,
        defi_history: DeFiInteractionHistory
    ) -> List[str]:
        """Identify potential risk flags"""
        flags = []

        if behavior.failed_transaction_rate > Decimal('0.1'):
            flags.append("High failed transaction rate")

        if defi_history.liquidation_events > 0:
            flags.append("Previous liquidation events")

        if behavior.account_age_days < 30:
            flags.append("New account")

        if behavior.total_transactions < 10:
            flags.append("Low transaction history")

        return flags

    async def _identify_strengths(
        self,
        behavior: OnChainBehavior,
        patterns: TransactionPattern,
        governance: GovernanceParticipation,
        defi_history: DeFiInteractionHistory
    ) -> List[str]:
        """Identify strengths in the profile"""
        strengths = []

        if behavior.governance_participation:
            strengths.append("Active governance participation")

        if patterns.multi_sig_usage:
            strengths.append("Security-conscious (multi-sig usage)")

        if behavior.consistent_activity:
            strengths.append("Consistent on-chain activity")

        if defi_history.yield_farming_experience:
            strengths.append("Experienced DeFi user")

        if patterns.gas_optimization_score > Decimal('0.8'):
            strengths.append("Fee optimization")

        return strengths

    async def _suggest_improvements(
        self,
        score: Decimal,
        behavior: OnChainBehavior,
        patterns: TransactionPattern
    ) -> List[str]:
        """Suggest areas for improvement"""
        improvements = []

        if not behavior.governance_participation:
            improvements.append("Participate in Algorand governance")

        if behavior.total_transactions < 50:
            improvements.append("Increase on-chain activity")

        if not patterns.multi_sig_usage and behavior.largest_transaction > Decimal('100000'):
            improvements.append("Consider multi-sig for large transactions")

        if score < Decimal('0.7'):
            improvements.append("Diversify DeFi protocol usage")

        return improvements

    async def _calculate_confidence(
        self,
        behavior: OnChainBehavior,
        patterns: TransactionPattern
    ) -> Decimal:
        """Calculate confidence level in the reputation score"""
        factors = []

        # More transactions = higher confidence
        tx_confidence = min(Decimal(behavior.total_transactions) / Decimal('100'), Decimal('1'))
        factors.append(tx_confidence * Decimal('0.4'))

        # Longer account age = higher confidence
        age_confidence = min(Decimal(behavior.account_age_days) / Decimal('365'), Decimal('1'))
        factors.append(age_confidence * Decimal('0.3'))

        # More interactions = higher confidence
        interaction_confidence = min(Decimal(behavior.defi_protocol_interactions) / Decimal('20'), Decimal('1'))
        factors.append(interaction_confidence * Decimal('0.3'))

        return sum(factors)

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self._cache:
            return False

        cache_time = self._cache_timestamps.get(key)
        if not cache_time:
            return False

        return (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl