"""
Wallet Clustering and Sybil Attack Detection

Analyzes wallet relationships and clustering patterns to detect
Sybil attacks and coordinated behaviors on Algorand.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import math
import networkx as nx

from ..models.blockchain_risk import (
    TransactionPattern, BehaviorPattern, RiskLevel, RiskAlert
)


@dataclass
class WalletCluster:
    """Represents a cluster of potentially related wallets"""
    cluster_id: str
    wallet_addresses: Set[str]
    cluster_score: float
    connection_strength: float
    shared_behaviors: List[str]
    risk_indicators: List[str]
    first_activity: datetime
    last_activity: datetime
    total_volume: float
    transaction_count: int


@dataclass
class WalletRelationship:
    """Represents a relationship between two wallets"""
    wallet_a: str
    wallet_b: str
    relationship_type: str
    strength: float
    evidence: List[str]
    first_interaction: datetime
    last_interaction: datetime
    interaction_count: int
    shared_volume: float


class WalletClusteringAnalyzer:
    """Analyzes wallet relationships and clustering patterns"""

    def __init__(self, sybil_threshold: float = 0.7):
        self.sybil_threshold = sybil_threshold
        self.graph = nx.Graph()
        self.wallet_features = {}
        self.cluster_cache = {}

    async def analyze_wallet_relationships(
        self,
        wallet_transactions: Dict[str, List[Dict[str, Any]]],
        time_window: timedelta = timedelta(days=30)
    ) -> List[WalletCluster]:
        """
        Analyze relationships between wallets to identify clusters

        Args:
            wallet_transactions: Dictionary mapping wallet addresses to their transactions
            time_window: Time window for analysis

        Returns:
            List of detected wallet clusters
        """
        # Build relationship graph
        relationships = await self._build_relationship_graph(wallet_transactions)

        # Extract wallet features
        features = await self._extract_wallet_features(wallet_transactions)

        # Detect clusters using multiple methods
        clusters = await self._detect_clusters(relationships, features)

        # Analyze clusters for Sybil patterns
        sybil_clusters = await self._analyze_sybil_patterns(clusters, relationships, features)

        return sybil_clusters

    async def _build_relationship_graph(
        self,
        wallet_transactions: Dict[str, List[Dict[str, Any]]]
    ) -> List[WalletRelationship]:
        """Build graph of wallet relationships"""
        relationships = []
        interaction_matrix = defaultdict(lambda: defaultdict(list))

        # Build interaction matrix
        for wallet, transactions in wallet_transactions.items():
            for txn in transactions:
                sender = txn.get('sender', '')
                receiver = txn.get('receiver', '')
                amount = float(txn.get('amount', 0))
                timestamp = datetime.fromisoformat(txn.get('timestamp', '1970-01-01'))

                if sender in wallet_transactions and receiver in wallet_transactions:
                    interaction_matrix[sender][receiver].append({
                        'amount': amount,
                        'timestamp': timestamp,
                        'txn_id': txn.get('id', '')
                    })

        # Analyze interactions to create relationships
        for wallet_a, interactions in interaction_matrix.items():
            for wallet_b, txn_list in interactions.items():
                if wallet_a != wallet_b and len(txn_list) >= 2:
                    relationship = await self._analyze_interaction_pattern(
                        wallet_a, wallet_b, txn_list
                    )
                    if relationship:
                        relationships.append(relationship)

        return relationships

    async def _analyze_interaction_pattern(
        self,
        wallet_a: str,
        wallet_b: str,
        transactions: List[Dict[str, Any]]
    ) -> Optional[WalletRelationship]:
        """Analyze interaction pattern between two wallets"""
        if len(transactions) < 2:
            return None

        # Sort transactions by timestamp
        sorted_txns = sorted(transactions, key=lambda x: x['timestamp'])

        total_volume = sum(txn['amount'] for txn in transactions)
        first_interaction = sorted_txns[0]['timestamp']
        last_interaction = sorted_txns[-1]['timestamp']

        # Analyze patterns
        evidence = []
        relationship_type = "direct_transfer"
        strength = 0.0

        # Check for round-robin patterns
        amounts = [txn['amount'] for txn in transactions]
        if len(set(amounts)) == 1:
            evidence.append("Identical transaction amounts")
            strength += 0.3

        # Check for rapid interactions
        time_gaps = []
        for i in range(1, len(sorted_txns)):
            gap = sorted_txns[i]['timestamp'] - sorted_txns[i-1]['timestamp']
            time_gaps.append(gap.total_seconds())

        avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 0
        if avg_gap < 3600:  # Less than 1 hour average
            evidence.append("Rapid sequential transactions")
            strength += 0.4

        # Check for volume concentration
        volume_variance = sum((amt - sum(amounts)/len(amounts))**2 for amt in amounts) / len(amounts)
        if volume_variance < (sum(amounts)/len(amounts)) * 0.1:  # Low variance
            evidence.append("Consistent transaction sizes")
            strength += 0.2

        # Check for timing patterns (e.g., same time of day)
        hours = [txn['timestamp'].hour for txn in sorted_txns]
        hour_variance = sum((h - sum(hours)/len(hours))**2 for h in hours) / len(hours)
        if hour_variance < 4:  # Transactions tend to happen at similar times
            evidence.append("Consistent transaction timing")
            strength += 0.2

        if strength >= 0.3:  # Minimum threshold for relationship
            return WalletRelationship(
                wallet_a=wallet_a,
                wallet_b=wallet_b,
                relationship_type=relationship_type,
                strength=min(strength, 1.0),
                evidence=evidence,
                first_interaction=first_interaction,
                last_interaction=last_interaction,
                interaction_count=len(transactions),
                shared_volume=total_volume
            )

        return None

    async def _extract_wallet_features(
        self,
        wallet_transactions: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract behavioral features for each wallet"""
        features = {}

        for wallet, transactions in wallet_transactions.items():
            if not transactions:
                continue

            # Basic statistics
            total_volume = sum(float(txn.get('amount', 0)) for txn in transactions)
            transaction_count = len(transactions)

            # Timing features
            timestamps = [datetime.fromisoformat(txn.get('timestamp', '1970-01-01')) for txn in transactions]
            timestamps.sort()

            first_activity = timestamps[0]
            last_activity = timestamps[-1]
            activity_span = (last_activity - first_activity).days

            # Transaction patterns
            amounts = [float(txn.get('amount', 0)) for txn in transactions]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            amount_variance = (
                sum((amt - avg_amount)**2 for amt in amounts) / len(amounts)
                if len(amounts) > 1 else 0
            )

            # Counterparty analysis
            counterparties = set()
            for txn in transactions:
                counterparties.add(txn.get('sender', ''))
                counterparties.add(txn.get('receiver', ''))
            counterparties.discard(wallet)

            # Time-of-day patterns
            hours = [ts.hour for ts in timestamps]
            hour_distribution = {h: hours.count(h) for h in range(24)}
            primary_hours = [h for h, count in hour_distribution.items() if count > len(hours) * 0.1]

            # Asset diversity
            asset_types = set(txn.get('asset-id', 0) for txn in transactions)

            features[wallet] = {
                'total_volume': total_volume,
                'transaction_count': transaction_count,
                'avg_amount': avg_amount,
                'amount_variance': amount_variance,
                'counterparty_count': len(counterparties),
                'activity_span_days': activity_span,
                'first_activity': first_activity,
                'last_activity': last_activity,
                'primary_hours': primary_hours,
                'asset_diversity': len(asset_types),
                'transactions_per_day': transaction_count / max(activity_span, 1)
            }

        return features

    async def _detect_clusters(
        self,
        relationships: List[WalletRelationship],
        features: Dict[str, Dict[str, Any]]
    ) -> List[WalletCluster]:
        """Detect wallet clusters using graph analysis"""
        # Build NetworkX graph
        self.graph.clear()

        for rel in relationships:
            self.graph.add_edge(
                rel.wallet_a,
                rel.wallet_b,
                weight=rel.strength,
                relationship=rel
            )

        # Find connected components
        components = list(nx.connected_components(self.graph))
        clusters = []

        for i, component in enumerate(components):
            if len(component) < 2:
                continue

            cluster_id = f"cluster_{i}_{datetime.utcnow().timestamp()}"

            # Calculate cluster metrics
            cluster_relationships = [
                rel for rel in relationships
                if rel.wallet_a in component and rel.wallet_b in component
            ]

            total_volume = sum(
                features.get(wallet, {}).get('total_volume', 0)
                for wallet in component
            )

            total_transactions = sum(
                features.get(wallet, {}).get('transaction_count', 0)
                for wallet in component
            )

            # Calculate connection strength
            if len(component) > 1:
                possible_connections = len(component) * (len(component) - 1) / 2
                actual_connections = len(cluster_relationships)
                connection_density = actual_connections / possible_connections
            else:
                connection_density = 0

            avg_strength = (
                sum(rel.strength for rel in cluster_relationships) / len(cluster_relationships)
                if cluster_relationships else 0
            )

            # Identify shared behaviors
            shared_behaviors = await self._identify_shared_behaviors(component, features)

            # Calculate cluster score
            cluster_score = self._calculate_cluster_score(
                component, cluster_relationships, features, connection_density
            )

            # Get activity timeframe
            all_first = [features.get(w, {}).get('first_activity') for w in component]
            all_last = [features.get(w, {}).get('last_activity') for w in component]
            all_first = [d for d in all_first if d is not None]
            all_last = [d for d in all_last if d is not None]

            first_activity = min(all_first) if all_first else datetime.utcnow()
            last_activity = max(all_last) if all_last else datetime.utcnow()

            cluster = WalletCluster(
                cluster_id=cluster_id,
                wallet_addresses=component,
                cluster_score=cluster_score,
                connection_strength=avg_strength,
                shared_behaviors=shared_behaviors,
                risk_indicators=[],
                first_activity=first_activity,
                last_activity=last_activity,
                total_volume=total_volume,
                transaction_count=total_transactions
            )

            clusters.append(cluster)

        return clusters

    async def _identify_shared_behaviors(
        self,
        wallets: Set[str],
        features: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Identify shared behavioral patterns across wallets"""
        shared_behaviors = []

        if len(wallets) < 2:
            return shared_behaviors

        wallet_list = list(wallets)

        # Check for similar transaction patterns
        avg_amounts = [features.get(w, {}).get('avg_amount', 0) for w in wallet_list]
        if avg_amounts and max(avg_amounts) > 0:
            amount_cv = (
                (sum((amt - sum(avg_amounts)/len(avg_amounts))**2 for amt in avg_amounts) / len(avg_amounts))**0.5
                / (sum(avg_amounts)/len(avg_amounts))
            )
            if amount_cv < 0.2:  # Low coefficient of variation
                shared_behaviors.append("Similar average transaction amounts")

        # Check for similar activity patterns
        tx_counts = [features.get(w, {}).get('transaction_count', 0) for w in wallet_list]
        if tx_counts:
            tx_cv = (
                (sum((count - sum(tx_counts)/len(tx_counts))**2 for count in tx_counts) / len(tx_counts))**0.5
                / max(sum(tx_counts)/len(tx_counts), 1)
            )
            if tx_cv < 0.3:
                shared_behaviors.append("Similar transaction frequency")

        # Check for similar timing patterns
        all_primary_hours = [features.get(w, {}).get('primary_hours', []) for w in wallet_list]
        if all_primary_hours:
            common_hours = set(all_primary_hours[0])
            for hours in all_primary_hours[1:]:
                common_hours &= set(hours)

            if len(common_hours) >= 2:
                shared_behaviors.append(f"Active during same hours: {sorted(common_hours)}")

        # Check for coordinated account creation
        creation_times = [features.get(w, {}).get('first_activity') for w in wallet_list]
        creation_times = [t for t in creation_times if t is not None]

        if len(creation_times) >= 2:
            time_spans = []
            for i in range(len(creation_times)):
                for j in range(i+1, len(creation_times)):
                    span = abs((creation_times[i] - creation_times[j]).total_seconds())
                    time_spans.append(span)

            avg_span = sum(time_spans) / len(time_spans) if time_spans else 0
            if avg_span < 86400:  # Within 24 hours
                shared_behaviors.append("Coordinated account creation")

        return shared_behaviors

    def _calculate_cluster_score(
        self,
        wallets: Set[str],
        relationships: List[WalletRelationship],
        features: Dict[str, Dict[str, Any]],
        connection_density: float
    ) -> float:
        """Calculate overall cluster risk score"""
        if len(wallets) < 2:
            return 0.0

        # Base score from connection density
        density_score = connection_density

        # Relationship strength score
        avg_strength = (
            sum(rel.strength for rel in relationships) / len(relationships)
            if relationships else 0
        )

        # Behavioral similarity score
        wallet_list = list(wallets)
        behavioral_similarity = 0.0

        if len(wallet_list) >= 2:
            # Calculate similarity in transaction patterns
            features_matrix = []
            for wallet in wallet_list:
                wallet_features = features.get(wallet, {})
                feature_vector = [
                    wallet_features.get('avg_amount', 0),
                    wallet_features.get('transaction_count', 0),
                    wallet_features.get('transactions_per_day', 0),
                    wallet_features.get('counterparty_count', 0),
                    wallet_features.get('asset_diversity', 0)
                ]
                features_matrix.append(feature_vector)

            # Calculate pairwise similarities
            similarities = []
            for i in range(len(features_matrix)):
                for j in range(i+1, len(features_matrix)):
                    vec1 = features_matrix[i]
                    vec2 = features_matrix[j]

                    # Cosine similarity
                    dot_product = sum(a * b for a, b in zip(vec1, vec2))
                    magnitude1 = sum(a * a for a in vec1) ** 0.5
                    magnitude2 = sum(a * a for a in vec2) ** 0.5

                    if magnitude1 > 0 and magnitude2 > 0:
                        similarity = dot_product / (magnitude1 * magnitude2)
                        similarities.append(similarity)

            behavioral_similarity = sum(similarities) / len(similarities) if similarities else 0

        # Combined cluster score
        cluster_score = (
            density_score * 0.4 +
            avg_strength * 0.35 +
            behavioral_similarity * 0.25
        )

        return min(cluster_score, 1.0)

    async def _analyze_sybil_patterns(
        self,
        clusters: List[WalletCluster],
        relationships: List[WalletRelationship],
        features: Dict[str, Dict[str, Any]]
    ) -> List[WalletCluster]:
        """Analyze clusters for Sybil attack patterns"""
        sybil_clusters = []

        for cluster in clusters:
            risk_indicators = []

            # Check cluster size (larger clusters more suspicious)
            if len(cluster.wallet_addresses) >= 5:
                risk_indicators.append(f"Large cluster size: {len(cluster.wallet_addresses)} wallets")

            # Check for high behavioral similarity
            if len(cluster.shared_behaviors) >= 3:
                risk_indicators.append(f"High behavioral similarity: {len(cluster.shared_behaviors)} shared patterns")

            # Check for rapid account creation
            creation_times = [
                features.get(wallet, {}).get('first_activity')
                for wallet in cluster.wallet_addresses
                if features.get(wallet, {}).get('first_activity')
            ]

            if len(creation_times) >= 3:
                time_range = max(creation_times) - min(creation_times)
                if time_range < timedelta(days=7):
                    risk_indicators.append("Rapid coordinated account creation")

            # Check for circular transaction patterns
            cluster_relationships = [
                rel for rel in relationships
                if rel.wallet_a in cluster.wallet_addresses and rel.wallet_b in cluster.wallet_addresses
            ]

            circular_patterns = self._detect_circular_patterns(cluster_relationships)
            if circular_patterns:
                risk_indicators.append(f"Circular transaction patterns detected: {circular_patterns}")

            # Check for funding patterns (common source)
            funding_analysis = await self._analyze_funding_patterns(cluster.wallet_addresses, features)
            if funding_analysis['common_funding_ratio'] > 0.7:
                risk_indicators.append("Common funding source detected")

            # Update cluster with risk indicators
            cluster.risk_indicators = risk_indicators

            # Determine if cluster meets Sybil threshold
            sybil_score = (
                cluster.cluster_score * 0.5 +
                len(risk_indicators) / 10 * 0.3 +
                cluster.connection_strength * 0.2
            )

            if sybil_score >= self.sybil_threshold:
                cluster.cluster_score = sybil_score
                sybil_clusters.append(cluster)

        return sybil_clusters

    def _detect_circular_patterns(self, relationships: List[WalletRelationship]) -> int:
        """Detect circular transaction patterns in relationships"""
        # Build directed graph for cycle detection
        directed_graph = nx.DiGraph()

        for rel in relationships:
            directed_graph.add_edge(rel.wallet_a, rel.wallet_b, weight=rel.strength)

        # Find simple cycles
        try:
            cycles = list(nx.simple_cycles(directed_graph))
            return len([cycle for cycle in cycles if len(cycle) >= 3])
        except:
            return 0

    async def _analyze_funding_patterns(
        self,
        wallets: Set[str],
        features: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze funding patterns for cluster of wallets"""
        # This would analyze the first transactions of each wallet
        # to identify common funding sources

        # Simplified analysis for now
        return {
            'common_funding_ratio': 0.5,  # Placeholder
            'funding_sources': [],
            'funding_timeline': {}
        }

    def create_sybil_alert(self, cluster: WalletCluster) -> RiskAlert:
        """Create a Sybil attack risk alert"""
        return RiskAlert(
            alert_id=f"sybil_{cluster.cluster_id}",
            alert_type="SYBIL_ATTACK",
            severity=RiskLevel.HIGH if cluster.cluster_score > 0.8 else RiskLevel.MODERATE,
            title=f"Potential Sybil Attack Cluster Detected",
            description=f"Identified cluster of {len(cluster.wallet_addresses)} wallets "
                       f"with suspicious coordinated behavior patterns.",
            affected_addresses=list(cluster.wallet_addresses),
            affected_protocols=[],
            risk_score=cluster.cluster_score,
            confidence=cluster.connection_strength,
            detection_method="Wallet Clustering Analysis",
            evidence={
                'shared_behaviors': cluster.shared_behaviors,
                'risk_indicators': cluster.risk_indicators,
                'cluster_metrics': {
                    'total_volume': cluster.total_volume,
                    'transaction_count': cluster.transaction_count,
                    'connection_strength': cluster.connection_strength
                }
            },
            recommendations=[
                "Implement enhanced KYC verification for cluster addresses",
                "Monitor transaction patterns for coordinated activities",
                "Consider limiting transaction volumes from cluster addresses",
                "Investigate funding sources and relationships"
            ]
        )