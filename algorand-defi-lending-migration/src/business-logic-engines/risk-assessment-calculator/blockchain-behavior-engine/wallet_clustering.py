"""
Wallet Clustering and Relationship Analysis Engine

Identifies clusters of related wallets that may indicate:
- Sybil attack networks
- Exchange clustering
- Institutional wallet management
- Family/individual multi-wallet usage
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
import numpy as np
from collections import defaultdict

from .models import WalletCluster, RiskLevel

logger = logging.getLogger(__name__)


class WalletClusteringEngine:
    """
    Analyzes wallet relationships and clustering patterns
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for wallet clustering"""
        return {
            'max_cluster_depth': 3,
            'min_shared_transactions': 3,
            'timing_correlation_threshold': 0.7,
            'creation_time_window_hours': 24,
            'shared_app_weight': 0.3,
            'transaction_pattern_weight': 0.4,
            'timing_weight': 0.3,
            'min_cluster_size': 2,
            'max_wallets_analyzed': 1000
        }

    async def analyze_clusters(
        self,
        root_address: str,
        include_related: bool = True
    ) -> List[WalletCluster]:
        """
        Analyze wallet clustering around a root address

        Args:
            root_address: Primary address to analyze
            include_related: Whether to analyze related addresses

        Returns:
            List of identified wallet clusters
        """
        try:
            logger.info(f"Starting wallet clustering analysis for {root_address}")

            # Get related addresses
            related_addresses = await self._get_related_addresses(root_address)

            if not include_related:
                related_addresses = [root_address]

            if len(related_addresses) < self.config['min_cluster_size']:
                logger.info("Insufficient related addresses for clustering")
                return []

            # Analyze relationships between addresses
            relationship_matrix = await self._build_relationship_matrix(related_addresses)

            # Identify clusters using multiple methods
            clusters = await self._identify_clusters(relationship_matrix, related_addresses)

            # Score and classify clusters
            scored_clusters = []
            for cluster in clusters:
                cluster_analysis = await self._analyze_cluster(cluster, related_addresses)
                if cluster_analysis:
                    scored_clusters.append(cluster_analysis)

            logger.info(f"Identified {len(scored_clusters)} wallet clusters")
            return scored_clusters

        except Exception as e:
            logger.error(f"Error in wallet clustering analysis: {e}")
            raise

    async def _get_related_addresses(self, root_address: str) -> List[str]:
        """Get addresses related to the root address"""
        try:
            related_addresses = set([root_address])

            # Get direct transaction counterparties
            counterparties = await self._get_transaction_counterparties(root_address)
            related_addresses.update(counterparties[:50])  # Limit to top 50

            # Get addresses with shared app interactions
            app_addresses = await self._get_shared_app_addresses(root_address)
            related_addresses.update(app_addresses[:30])  # Limit to top 30

            # Get addresses with similar creation times
            similar_creation_addresses = await self._get_similar_creation_addresses(root_address)
            related_addresses.update(similar_creation_addresses[:20])

            return list(related_addresses)[:self.config['max_wallets_analyzed']]

        except Exception as e:
            logger.error(f"Error getting related addresses: {e}")
            return [root_address]

    async def _build_relationship_matrix(self, addresses: List[str]) -> Dict[str, Dict[str, float]]:
        """Build relationship strength matrix between addresses"""
        matrix = defaultdict(lambda: defaultdict(float))

        try:
            # Calculate pairwise relationships
            for i, addr1 in enumerate(addresses):
                for j, addr2 in enumerate(addresses[i+1:], i+1):
                    relationship_score = await self._calculate_relationship_score(addr1, addr2)
                    matrix[addr1][addr2] = relationship_score
                    matrix[addr2][addr1] = relationship_score

            return matrix

        except Exception as e:
            logger.error(f"Error building relationship matrix: {e}")
            return matrix

    async def _calculate_relationship_score(self, addr1: str, addr2: str) -> float:
        """Calculate relationship strength between two addresses"""
        try:
            total_score = 0.0

            # Transaction pattern similarity
            pattern_score = await self._calculate_transaction_pattern_similarity(addr1, addr2)
            total_score += pattern_score * self.config['transaction_pattern_weight']

            # Timing correlation
            timing_score = await self._calculate_timing_correlation(addr1, addr2)
            total_score += timing_score * self.config['timing_weight']

            # Shared app interactions
            app_score = await self._calculate_shared_app_score(addr1, addr2)
            total_score += app_score * self.config['shared_app_weight']

            return min(total_score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating relationship score: {e}")
            return 0.0

    async def _calculate_transaction_pattern_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate transaction pattern similarity between addresses"""
        try:
            # Get transaction patterns for both addresses
            patterns1 = await self._get_transaction_patterns(addr1)
            patterns2 = await self._get_transaction_patterns(addr2)

            if not patterns1 or not patterns2:
                return 0.0

            # Calculate similarity metrics
            timing_similarity = self._calculate_timing_similarity(patterns1, patterns2)
            amount_similarity = self._calculate_amount_similarity(patterns1, patterns2)
            frequency_similarity = self._calculate_frequency_similarity(patterns1, patterns2)

            # Weighted average
            similarity = (timing_similarity * 0.4 + amount_similarity * 0.3 + frequency_similarity * 0.3)
            return similarity

        except Exception as e:
            logger.error(f"Error calculating transaction pattern similarity: {e}")
            return 0.0

    async def _calculate_timing_correlation(self, addr1: str, addr2: str) -> float:
        """Calculate timing correlation between address activities"""
        try:
            # Get transaction timestamps for both addresses
            times1 = await self._get_transaction_times(addr1)
            times2 = await self._get_transaction_times(addr2)

            if len(times1) < 5 or len(times2) < 5:
                return 0.0

            # Convert to hourly activity patterns
            hourly_activity1 = self._get_hourly_activity_pattern(times1)
            hourly_activity2 = self._get_hourly_activity_pattern(times2)

            # Calculate correlation
            correlation = np.corrcoef(hourly_activity1, hourly_activity2)[0, 1]

            # Handle NaN correlation
            if np.isnan(correlation):
                return 0.0

            return max(0, correlation)  # Only positive correlations

        except Exception as e:
            logger.error(f"Error calculating timing correlation: {e}")
            return 0.0

    async def _calculate_shared_app_score(self, addr1: str, addr2: str) -> float:
        """Calculate score based on shared application interactions"""
        try:
            apps1 = await self._get_app_interactions(addr1)
            apps2 = await self._get_app_interactions(addr2)

            if not apps1 or not apps2:
                return 0.0

            shared_apps = set(apps1) & set(apps2)
            total_unique_apps = len(set(apps1) | set(apps2))

            if total_unique_apps == 0:
                return 0.0

            jaccard_similarity = len(shared_apps) / total_unique_apps
            return jaccard_similarity

        except Exception as e:
            logger.error(f"Error calculating shared app score: {e}")
            return 0.0

    async def _identify_clusters(
        self,
        relationship_matrix: Dict[str, Dict[str, float]],
        addresses: List[str]
    ) -> List[List[str]]:
        """Identify clusters using relationship matrix"""
        try:
            clusters = []
            visited = set()

            # Use a simple clustering approach based on relationship thresholds
            for address in addresses:
                if address in visited:
                    continue

                cluster = await self._expand_cluster(
                    address, relationship_matrix, visited, threshold=0.5
                )

                if len(cluster) >= self.config['min_cluster_size']:
                    clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"Error identifying clusters: {e}")
            return []

    async def _expand_cluster(
        self,
        seed_address: str,
        relationship_matrix: Dict[str, Dict[str, float]],
        visited: Set[str],
        threshold: float = 0.5
    ) -> List[str]:
        """Expand cluster starting from seed address"""
        cluster = [seed_address]
        visited.add(seed_address)
        queue = [seed_address]

        while queue:
            current = queue.pop(0)

            for neighbor, strength in relationship_matrix[current].items():
                if neighbor not in visited and strength >= threshold:
                    cluster.append(neighbor)
                    visited.add(neighbor)
                    queue.append(neighbor)

        return cluster

    async def _analyze_cluster(self, cluster_addresses: List[str], all_addresses: List[str]) -> Optional[WalletCluster]:
        """Analyze and score a cluster"""
        try:
            if len(cluster_addresses) < self.config['min_cluster_size']:
                return None

            cluster_id = f"cluster_{hash(''.join(sorted(cluster_addresses))) % 1000000}"

            # Calculate cluster metrics
            total_balance = await self._calculate_cluster_balance(cluster_addresses)
            shared_patterns = await self._identify_shared_patterns(cluster_addresses)
            creation_proximity = await self._calculate_creation_proximity(cluster_addresses)
            timing_correlation = await self._calculate_cluster_timing_correlation(cluster_addresses)
            shared_apps = await self._get_cluster_shared_apps(cluster_addresses)

            # Determine cluster type and risk score
            cluster_type, risk_score = await self._classify_cluster(
                cluster_addresses, shared_patterns, creation_proximity, timing_correlation
            )

            return WalletCluster(
                cluster_id=cluster_id,
                wallet_addresses=cluster_addresses,
                cluster_size=len(cluster_addresses),
                total_balance=total_balance,
                shared_transaction_patterns=shared_patterns,
                creation_time_proximity=creation_proximity,
                transaction_timing_correlation=timing_correlation,
                shared_apps=shared_apps,
                risk_score=risk_score,
                cluster_type=cluster_type
            )

        except Exception as e:
            logger.error(f"Error analyzing cluster: {e}")
            return None

    async def _classify_cluster(
        self,
        cluster_addresses: List[str],
        shared_patterns: List[str],
        creation_proximity: float,
        timing_correlation: float
    ) -> Tuple[str, float]:
        """Classify cluster type and calculate risk score"""

        risk_score = 0.0
        cluster_type = "unknown"

        # Sybil detection
        if (creation_proximity > 0.8 and timing_correlation > 0.7 and
            len(cluster_addresses) > 5):
            cluster_type = "sybil"
            risk_score = 85.0

        # Exchange pattern
        elif "high_volume" in shared_patterns and len(cluster_addresses) > 10:
            cluster_type = "exchange"
            risk_score = 30.0

        # Institutional pattern
        elif "regular_timing" in shared_patterns and timing_correlation > 0.6:
            cluster_type = "institutional"
            risk_score = 20.0

        # Family/individual pattern
        elif len(cluster_addresses) <= 5 and timing_correlation > 0.5:
            cluster_type = "family"
            risk_score = 15.0

        else:
            cluster_type = "unknown"
            risk_score = 40.0

        return cluster_type, risk_score

    # Helper methods with placeholder implementations

    async def _get_transaction_counterparties(self, address: str) -> List[str]:
        """Get addresses that have transacted with this address"""
        # Placeholder - would query blockchain data
        return [f"COUNTERPARTY_{i}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" for i in range(20)]

    async def _get_shared_app_addresses(self, address: str) -> List[str]:
        """Get addresses that interact with the same apps"""
        # Placeholder
        return [f"APPUSER_{i}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" for i in range(15)]

    async def _get_similar_creation_addresses(self, address: str) -> List[str]:
        """Get addresses created around the same time"""
        # Placeholder
        return [f"NEWADDR_{i}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" for i in range(10)]

    async def _get_transaction_patterns(self, address: str) -> Dict[str, Any]:
        """Get transaction patterns for an address"""
        # Placeholder
        return {
            'avg_amount': 1000000,
            'frequency_per_day': 5,
            'peak_hours': [9, 10, 14, 15],
            'preferred_counterparties': []
        }

    async def _get_transaction_times(self, address: str) -> List[datetime]:
        """Get transaction timestamps for an address"""
        # Placeholder
        base_time = datetime.utcnow() - timedelta(days=30)
        return [base_time + timedelta(hours=i*2) for i in range(50)]

    async def _get_app_interactions(self, address: str) -> List[int]:
        """Get app IDs that this address has interacted with"""
        # Placeholder
        return [123, 456, 789, 101112]

    def _calculate_timing_similarity(self, patterns1: Dict, patterns2: Dict) -> float:
        """Calculate timing pattern similarity"""
        hours1 = set(patterns1.get('peak_hours', []))
        hours2 = set(patterns2.get('peak_hours', []))

        if not hours1 or not hours2:
            return 0.0

        intersection = len(hours1 & hours2)
        union = len(hours1 | hours2)

        return intersection / union if union > 0 else 0.0

    def _calculate_amount_similarity(self, patterns1: Dict, patterns2: Dict) -> float:
        """Calculate amount pattern similarity"""
        amt1 = patterns1.get('avg_amount', 0)
        amt2 = patterns2.get('avg_amount', 0)

        if amt1 == 0 or amt2 == 0:
            return 0.0

        ratio = min(amt1, amt2) / max(amt1, amt2)
        return ratio

    def _calculate_frequency_similarity(self, patterns1: Dict, patterns2: Dict) -> float:
        """Calculate frequency pattern similarity"""
        freq1 = patterns1.get('frequency_per_day', 0)
        freq2 = patterns2.get('frequency_per_day', 0)

        if freq1 == 0 or freq2 == 0:
            return 0.0

        ratio = min(freq1, freq2) / max(freq1, freq2)
        return ratio

    def _get_hourly_activity_pattern(self, timestamps: List[datetime]) -> List[float]:
        """Convert timestamps to 24-hour activity pattern"""
        hourly_counts = [0] * 24

        for timestamp in timestamps:
            hour = timestamp.hour
            hourly_counts[hour] += 1

        # Normalize
        total = sum(hourly_counts)
        if total > 0:
            return [count / total for count in hourly_counts]
        else:
            return [0.0] * 24

    async def _calculate_cluster_balance(self, addresses: List[str]) -> float:
        """Calculate total balance of cluster"""
        # Placeholder
        return len(addresses) * 10000.0  # Mock balance

    async def _identify_shared_patterns(self, addresses: List[str]) -> List[str]:
        """Identify shared transaction patterns in cluster"""
        # Placeholder
        patterns = []
        if len(addresses) > 5:
            patterns.append("high_volume")
        if len(addresses) > 3:
            patterns.append("regular_timing")
        return patterns

    async def _calculate_creation_proximity(self, addresses: List[str]) -> float:
        """Calculate how close in time the addresses were created"""
        # Placeholder - would check actual creation times
        return 0.6

    async def _calculate_cluster_timing_correlation(self, addresses: List[str]) -> float:
        """Calculate timing correlation across cluster"""
        # Placeholder
        return 0.7

    async def _get_cluster_shared_apps(self, addresses: List[str]) -> List[int]:
        """Get apps used by multiple addresses in cluster"""
        # Placeholder
        return [123, 456]