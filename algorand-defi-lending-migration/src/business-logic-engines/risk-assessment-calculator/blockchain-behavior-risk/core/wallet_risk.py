"""
Wallet Risk Analyzer

Specialized analyzer for wallet-level risk assessment including
clustering analysis, funding patterns, and behavioral consistency.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from ...common.models.blockchain_risk import RiskLevel, RiskAlert


@dataclass
class WalletRiskProfile:
    """Wallet-specific risk profile"""
    wallet_address: str
    age_days: int
    transaction_frequency: float
    volume_consistency: float
    counterparty_network_size: int
    funding_source_diversity: float
    behavioral_consistency: float
    clustering_risk: float
    overall_wallet_risk: float


class WalletRiskAnalyzer:
    """Specialized wallet behavior and clustering risk analyzer"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.clustering_config = config.get('risk_assessment', {}).get('wallet_clustering', {})

    async def analyze_clustering_risk(
        self,
        wallet_address: str,
        related_wallets: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze wallet clustering and Sybil attack risks"""
        try:
            if not related_wallets or wallet_address not in related_wallets:
                return {'clustering_risk': 0.0, 'cluster_indicators': []}

            wallet_transactions = related_wallets[wallet_address]

            # Analyze funding patterns
            funding_analysis = await self._analyze_funding_patterns(
                wallet_address, related_wallets
            )

            # Analyze behavioral similarities
            behavioral_analysis = await self._analyze_behavioral_similarities(
                wallet_address, related_wallets
            )

            # Analyze temporal correlations
            temporal_analysis = await self._analyze_temporal_correlations(
                wallet_address, related_wallets
            )

            # Calculate overall clustering risk
            clustering_risk = await self._calculate_clustering_risk(
                funding_analysis, behavioral_analysis, temporal_analysis
            )

            return {
                'clustering_risk': clustering_risk,
                'funding_analysis': funding_analysis,
                'behavioral_analysis': behavioral_analysis,
                'temporal_analysis': temporal_analysis,
                'cluster_indicators': self._generate_cluster_indicators(
                    funding_analysis, behavioral_analysis, temporal_analysis
                )
            }

        except Exception as e:
            self.logger.error(f"Clustering analysis failed for {wallet_address}: {e}")
            return {'clustering_risk': 0.0, 'cluster_indicators': []}

    async def _analyze_funding_patterns(
        self,
        target_wallet: str,
        wallet_transactions: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze funding source patterns across related wallets"""
        funding_sources = {}
        wallet_first_txns = {}

        for wallet, transactions in wallet_transactions.items():
            if not transactions:
                continue

            # Sort by timestamp to find first transaction
            sorted_txns = sorted(
                transactions,
                key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01'))
            )

            first_txn = sorted_txns[0]
            funding_source = first_txn.get('sender', 'unknown')
            funding_amount = float(first_txn.get('amount', 0))

            if funding_source != wallet:  # External funding
                if funding_source not in funding_sources:
                    funding_sources[funding_source] = []
                funding_sources[funding_source].append({
                    'wallet': wallet,
                    'amount': funding_amount,
                    'timestamp': first_txn.get('timestamp')
                })

            wallet_first_txns[wallet] = first_txn

        # Calculate funding correlation metrics
        common_funding_sources = [
            source for source, wallets in funding_sources.items()
            if len(wallets) >= 2
        ]

        funding_concentration = 0.0
        if funding_sources:
            max_funded_wallets = max(len(wallets) for wallets in funding_sources.values())
            total_wallets = len(wallet_transactions)
            funding_concentration = max_funded_wallets / max(total_wallets, 1)

        return {
            'common_funding_sources': common_funding_sources,
            'funding_concentration': funding_concentration,
            'funding_source_count': len(funding_sources),
            'total_wallets': len(wallet_transactions)
        }

    async def _analyze_behavioral_similarities(
        self,
        target_wallet: str,
        wallet_transactions: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze behavioral similarities between wallets"""
        wallet_behaviors = {}

        for wallet, transactions in wallet_transactions.items():
            if not transactions:
                continue

            # Calculate behavioral features
            amounts = [float(txn.get('amount', 0)) for txn in transactions]
            timestamps = [
                datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))
                for txn in transactions
            ]

            # Transaction timing patterns
            if len(timestamps) > 1:
                timestamps.sort()
                time_gaps = [
                    (timestamps[i] - timestamps[i-1]).total_seconds()
                    for i in range(1, len(timestamps))
                ]
                avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 0
            else:
                avg_gap = 0

            # Active hours analysis
            hours = [ts.hour for ts in timestamps]
            hour_distribution = {h: hours.count(h) for h in range(24)}
            primary_hours = [h for h, count in hour_distribution.items() if count > 0]

            wallet_behaviors[wallet] = {
                'avg_amount': sum(amounts) / len(amounts) if amounts else 0,
                'transaction_count': len(transactions),
                'avg_time_gap': avg_gap,
                'primary_hours': set(primary_hours),
                'unique_counterparties': len(set(
                    txn.get('sender', '') for txn in transactions
                ).union(set(
                    txn.get('receiver', '') for txn in transactions
                )))
            }

        # Calculate similarity scores
        similarities = {}
        wallets = list(wallet_behaviors.keys())

        for i in range(len(wallets)):
            for j in range(i + 1, len(wallets)):
                wallet_a, wallet_b = wallets[i], wallets[j]
                behavior_a = wallet_behaviors[wallet_a]
                behavior_b = wallet_behaviors[wallet_b]

                similarity = self._calculate_behavioral_similarity(behavior_a, behavior_b)
                similarities[f"{wallet_a}_{wallet_b}"] = similarity

        avg_similarity = sum(similarities.values()) / len(similarities) if similarities else 0

        return {
            'wallet_behaviors': wallet_behaviors,
            'pairwise_similarities': similarities,
            'average_similarity': avg_similarity,
            'high_similarity_pairs': [
                pair for pair, sim in similarities.items() if sim > 0.8
            ]
        }

    def _calculate_behavioral_similarity(
        self,
        behavior_a: Dict[str, Any],
        behavior_b: Dict[str, Any]
    ) -> float:
        """Calculate behavioral similarity between two wallets"""
        similarity_components = []

        # Amount similarity
        amount_a = behavior_a.get('avg_amount', 0)
        amount_b = behavior_b.get('avg_amount', 0)
        if amount_a > 0 and amount_b > 0:
            amount_ratio = min(amount_a, amount_b) / max(amount_a, amount_b)
            similarity_components.append(amount_ratio)

        # Transaction count similarity
        count_a = behavior_a.get('transaction_count', 0)
        count_b = behavior_b.get('transaction_count', 0)
        if count_a > 0 and count_b > 0:
            count_ratio = min(count_a, count_b) / max(count_a, count_b)
            similarity_components.append(count_ratio)

        # Time gap similarity
        gap_a = behavior_a.get('avg_time_gap', 0)
        gap_b = behavior_b.get('avg_time_gap', 0)
        if gap_a > 0 and gap_b > 0:
            gap_ratio = min(gap_a, gap_b) / max(gap_a, gap_b)
            similarity_components.append(gap_ratio)

        # Hour overlap similarity
        hours_a = behavior_a.get('primary_hours', set())
        hours_b = behavior_b.get('primary_hours', set())
        if hours_a and hours_b:
            intersection = len(hours_a & hours_b)
            union = len(hours_a | hours_b)
            hour_similarity = intersection / max(union, 1)
            similarity_components.append(hour_similarity)

        return sum(similarity_components) / len(similarity_components) if similarity_components else 0

    async def _analyze_temporal_correlations(
        self,
        target_wallet: str,
        wallet_transactions: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze temporal correlations between wallet activities"""
        wallet_timelines = {}

        # Create activity timelines for each wallet
        for wallet, transactions in wallet_transactions.items():
            timeline = []
            for txn in transactions:
                timestamp = datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))
                timeline.append(timestamp)

            wallet_timelines[wallet] = sorted(timeline)

        # Analyze creation time correlations
        creation_times = {}
        for wallet, timeline in wallet_timelines.items():
            if timeline:
                creation_times[wallet] = timeline[0]

        creation_correlations = []
        wallets = list(creation_times.keys())
        for i in range(len(wallets)):
            for j in range(i + 1, len(wallets)):
                wallet_a, wallet_b = wallets[i], wallets[j]
                time_diff = abs((creation_times[wallet_a] - creation_times[wallet_b]).total_seconds())

                # Consider wallets created within 24 hours as correlated
                if time_diff < 24 * 3600:
                    correlation_strength = 1.0 - (time_diff / (24 * 3600))
                    creation_correlations.append({
                        'wallet_pair': f"{wallet_a}_{wallet_b}",
                        'time_difference_hours': time_diff / 3600,
                        'correlation_strength': correlation_strength
                    })

        # Analyze activity synchronization
        activity_correlations = []
        for i in range(len(wallets)):
            for j in range(i + 1, len(wallets)):
                wallet_a, wallet_b = wallets[i], wallets[j]
                timeline_a = wallet_timelines[wallet_a]
                timeline_b = wallet_timelines[wallet_b]

                # Calculate activity overlap
                overlap_score = self._calculate_activity_overlap(timeline_a, timeline_b)
                if overlap_score > 0.5:
                    activity_correlations.append({
                        'wallet_pair': f"{wallet_a}_{wallet_b}",
                        'overlap_score': overlap_score
                    })

        return {
            'creation_correlations': creation_correlations,
            'activity_correlations': activity_correlations,
            'coordinated_creation_count': len(creation_correlations),
            'synchronized_activity_count': len(activity_correlations)
        }

    def _calculate_activity_overlap(
        self,
        timeline_a: List[datetime],
        timeline_b: List[datetime]
    ) -> float:
        """Calculate activity overlap between two timelines"""
        if not timeline_a or not timeline_b:
            return 0.0

        # Convert to hour buckets for comparison
        hours_a = set()
        hours_b = set()

        for timestamp in timeline_a:
            hour_bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            hours_a.add(hour_bucket)

        for timestamp in timeline_b:
            hour_bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            hours_b.add(hour_bucket)

        # Calculate Jaccard similarity
        intersection = len(hours_a & hours_b)
        union = len(hours_a | hours_b)

        return intersection / max(union, 1)

    async def _calculate_clustering_risk(
        self,
        funding_analysis: Dict[str, Any],
        behavioral_analysis: Dict[str, Any],
        temporal_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall clustering risk score"""
        risk_components = []

        # Funding concentration risk
        funding_concentration = funding_analysis.get('funding_concentration', 0)
        funding_risk = funding_concentration
        risk_components.append(('funding', funding_risk, 0.4))

        # Behavioral similarity risk
        avg_similarity = behavioral_analysis.get('average_similarity', 0)
        behavioral_risk = avg_similarity
        risk_components.append(('behavioral', behavioral_risk, 0.3))

        # Temporal correlation risk
        creation_correlations = temporal_analysis.get('coordinated_creation_count', 0)
        activity_correlations = temporal_analysis.get('synchronized_activity_count', 0)
        temporal_risk = min((creation_correlations + activity_correlations) / 10, 1.0)
        risk_components.append(('temporal', temporal_risk, 0.3))

        # Calculate weighted risk
        weighted_risk = sum(score * weight for _, score, weight in risk_components)

        return min(weighted_risk, 1.0)

    def _generate_cluster_indicators(
        self,
        funding_analysis: Dict[str, Any],
        behavioral_analysis: Dict[str, Any],
        temporal_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate list of clustering risk indicators"""
        indicators = []

        # Funding indicators
        if funding_analysis.get('funding_concentration', 0) > 0.5:
            indicators.append("High funding source concentration detected")

        if len(funding_analysis.get('common_funding_sources', [])) > 0:
            indicators.append("Common funding sources identified across wallets")

        # Behavioral indicators
        if behavioral_analysis.get('average_similarity', 0) > 0.8:
            indicators.append("High behavioral similarity across wallet cluster")

        high_sim_pairs = behavioral_analysis.get('high_similarity_pairs', [])
        if len(high_sim_pairs) > 2:
            indicators.append(f"Multiple high-similarity wallet pairs detected ({len(high_sim_pairs)})")

        # Temporal indicators
        if temporal_analysis.get('coordinated_creation_count', 0) > 2:
            indicators.append("Coordinated wallet creation pattern detected")

        if temporal_analysis.get('synchronized_activity_count', 0) > 1:
            indicators.append("Synchronized activity patterns across wallets")

        return indicators