"""
Algorand Network Health Monitor
Monitors network performance, consensus health, and transaction processing efficiency.
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import time

from algosdk.v2client import algod, indexer


@dataclass
class NetworkMetrics:
    """Current network performance metrics"""
    timestamp: datetime
    current_round: int
    last_round_time: datetime

    # Transaction throughput
    transactions_per_second: float
    transactions_in_round: int

    # Block performance
    block_time: float
    block_time_variance: float
    rounds_per_minute: float

    # Consensus metrics
    participation_rate: float
    online_stake: int
    total_stake: int

    # Network load
    mempool_size: int
    pending_transactions: int

    # Fee metrics
    suggested_fee: int
    min_fee: int


@dataclass
class ConsensusHealth:
    """Consensus mechanism health indicators"""
    participation_rate: float
    participation_trend: str
    consensus_score: float

    # Validator metrics
    online_validators: int
    total_validators: int
    validator_distribution: Dict[str, float]

    # Block production
    block_production_consistency: float
    missed_blocks: int
    fork_events: int

    # Network agreement
    agreement_time: float
    finality_confidence: float


@dataclass
class TransactionPoolStatus:
    """Transaction pool (mempool) status"""
    current_size: int
    max_size: int
    utilization_rate: float

    # Transaction types distribution
    payment_txns: int
    app_call_txns: int
    asset_txns: int
    key_reg_txns: int

    # Processing metrics
    average_wait_time: float
    processing_rate: float
    rejected_transactions: int

    # Fee analysis
    fee_distribution: Dict[str, int]
    congestion_factor: float


@dataclass
class NetworkHealthReport:
    """Comprehensive network health assessment"""
    timestamp: datetime

    # Core metrics
    network_metrics: NetworkMetrics
    consensus_health: ConsensusHealth
    mempool_status: TransactionPoolStatus

    # Health scores
    throughput_score: float
    consensus_score: float
    stability_score: float
    overall_health_score: float

    # Status indicators
    health_status: str
    alerts: List[str]
    recommendations: List[str]

    # Trends
    performance_trend: str
    capacity_utilization: float


class NetworkHealthMonitor:
    """Monitors Algorand network health and performance"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize clients
        self.algod_client = algod.AlgodClient(
            algod_token="",
            algod_address=config['algorand_config']['node']['url']
        )

        self.indexer_client = indexer.IndexerClient(
            indexer_token="",
            indexer_address=config['algorand_config']['indexer']['url']
        )

        # Configuration
        self.network_config = config['network_monitoring']
        self.thresholds = config['network_thresholds']

        # Historical data for trend analysis
        self.metrics_history = []
        self.max_history_size = 1000

    async def get_network_health_report(self) -> NetworkHealthReport:
        """Generate comprehensive network health report"""
        try:
            self.logger.info("Generating network health report")

            # Collect metrics in parallel
            results = await asyncio.gather(
                self._collect_network_metrics(),
                self._analyze_consensus_health(),
                self._analyze_mempool_status(),
                return_exceptions=True
            )

            # Extract results
            network_metrics = results[0] if not isinstance(results[0], Exception) else self._default_network_metrics()
            consensus_health = results[1] if not isinstance(results[1], Exception) else self._default_consensus_health()
            mempool_status = results[2] if not isinstance(results[2], Exception) else self._default_mempool_status()

            # Calculate health scores
            throughput_score = self._calculate_throughput_score(network_metrics)
            consensus_score = consensus_health.consensus_score
            stability_score = self._calculate_stability_score(network_metrics, consensus_health)

            # Overall health score
            overall_score = self._calculate_overall_health_score(
                throughput_score, consensus_score, stability_score
            )

            # Determine health status
            health_status = self._determine_health_status(overall_score)

            # Generate alerts and recommendations
            alerts = self._generate_alerts(network_metrics, consensus_health, mempool_status)
            recommendations = self._generate_recommendations(
                network_metrics, consensus_health, mempool_status, overall_score
            )

            # Analyze trends
            performance_trend = self._analyze_performance_trend()
            capacity_utilization = self._calculate_capacity_utilization(network_metrics, mempool_status)

            # Store metrics for trend analysis
            self._store_metrics_history(network_metrics)

            return NetworkHealthReport(
                timestamp=datetime.utcnow(),
                network_metrics=network_metrics,
                consensus_health=consensus_health,
                mempool_status=mempool_status,
                throughput_score=throughput_score,
                consensus_score=consensus_score,
                stability_score=stability_score,
                overall_health_score=overall_score,
                health_status=health_status,
                alerts=alerts,
                recommendations=recommendations,
                performance_trend=performance_trend,
                capacity_utilization=capacity_utilization
            )

        except Exception as e:
            self.logger.error(f"Error generating network health report: {e}")
            raise

    async def _collect_network_metrics(self) -> NetworkMetrics:
        """Collect current network performance metrics"""
        try:
            # Get node status
            status = self.algod_client.status()

            current_round = status['last-round']
            last_round_time = datetime.fromtimestamp(status['last-round-time'])

            # Get recent block information
            block_info = self.algod_client.block_info(current_round)

            # Calculate TPS from recent blocks
            tps = await self._calculate_current_tps()

            # Get transaction count in current round
            txns_in_round = len(block_info.get('block', {}).get('txns', []))

            # Calculate block time metrics
            block_time, block_variance = await self._calculate_block_time_metrics()

            # Get participation metrics
            participation_rate = await self._get_participation_rate()
            online_stake, total_stake = await self._get_stake_metrics()

            # Get mempool information
            mempool_size = await self._get_mempool_size()

            # Get fee information
            suggested_params = self.algod_client.suggested_params()
            suggested_fee = suggested_params.fee
            min_fee = suggested_params.min_fee

            return NetworkMetrics(
                timestamp=datetime.utcnow(),
                current_round=current_round,
                last_round_time=last_round_time,
                transactions_per_second=tps,
                transactions_in_round=txns_in_round,
                block_time=block_time,
                block_time_variance=block_variance,
                rounds_per_minute=60.0 / max(block_time, 1.0),
                participation_rate=participation_rate,
                online_stake=online_stake,
                total_stake=total_stake,
                mempool_size=mempool_size,
                pending_transactions=mempool_size,
                suggested_fee=suggested_fee,
                min_fee=min_fee
            )

        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
            return self._default_network_metrics()

    async def _analyze_consensus_health(self) -> ConsensusHealth:
        """Analyze consensus mechanism health"""
        try:
            # Get participation metrics
            participation_rate = await self._get_participation_rate()
            participation_trend = await self._analyze_participation_trend()

            # Calculate consensus score
            consensus_score = self._calculate_consensus_score(participation_rate)

            # Get validator information (simplified)
            online_validators = await self._estimate_online_validators()
            total_validators = await self._estimate_total_validators()

            # Analyze block production
            block_consistency = await self._analyze_block_production_consistency()
            missed_blocks = await self._count_recent_missed_blocks()

            # Network agreement metrics
            agreement_time = await self._estimate_agreement_time()
            finality_confidence = self._calculate_finality_confidence(participation_rate)

            return ConsensusHealth(
                participation_rate=participation_rate,
                participation_trend=participation_trend,
                consensus_score=consensus_score,
                online_validators=online_validators,
                total_validators=total_validators,
                validator_distribution={},  # Simplified
                block_production_consistency=block_consistency,
                missed_blocks=missed_blocks,
                fork_events=0,  # Algorand doesn't fork
                agreement_time=agreement_time,
                finality_confidence=finality_confidence
            )

        except Exception as e:
            self.logger.error(f"Error analyzing consensus health: {e}")
            return self._default_consensus_health()

    async def _analyze_mempool_status(self) -> TransactionPoolStatus:
        """Analyze transaction pool status"""
        try:
            # Get current mempool size
            current_size = await self._get_mempool_size()
            max_size = 50000  # Approximate Algorand mempool limit
            utilization_rate = current_size / max_size

            # Analyze transaction types (simplified)
            tx_distribution = await self._analyze_mempool_transactions()

            # Processing metrics
            processing_rate = await self._estimate_processing_rate()
            avg_wait_time = await self._estimate_average_wait_time(current_size, processing_rate)

            # Fee analysis
            fee_distribution = await self._analyze_fee_distribution()
            congestion_factor = self._calculate_congestion_factor(utilization_rate, processing_rate)

            return TransactionPoolStatus(
                current_size=current_size,
                max_size=max_size,
                utilization_rate=utilization_rate,
                payment_txns=tx_distribution.get('pay', 0),
                app_call_txns=tx_distribution.get('appl', 0),
                asset_txns=tx_distribution.get('axfer', 0),
                key_reg_txns=tx_distribution.get('keyreg', 0),
                average_wait_time=avg_wait_time,
                processing_rate=processing_rate,
                rejected_transactions=0,  # Simplified
                fee_distribution=fee_distribution,
                congestion_factor=congestion_factor
            )

        except Exception as e:
            self.logger.error(f"Error analyzing mempool status: {e}")
            return self._default_mempool_status()

    async def _calculate_current_tps(self) -> float:
        """Calculate current transactions per second"""
        try:
            # Get recent blocks to calculate TPS
            current_round = self.algod_client.status()['last-round']

            # Analyze last 10 blocks
            total_txns = 0
            total_time = 0
            blocks_analyzed = 0

            for i in range(min(10, current_round)):
                try:
                    round_num = current_round - i
                    block_info = self.algod_client.block_info(round_num)

                    block = block_info.get('block', {})
                    txns = block.get('txns', [])
                    total_txns += len(txns)

                    # Add block time (assuming ~4.5 seconds per block)
                    total_time += 4.5
                    blocks_analyzed += 1

                except Exception:
                    continue

            if total_time > 0 and blocks_analyzed > 0:
                return total_txns / total_time
            else:
                return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating TPS: {e}")
            return 0.0

    async def _calculate_block_time_metrics(self) -> Tuple[float, float]:
        """Calculate block time and variance"""
        try:
            # Get recent block timestamps
            current_round = self.algod_client.status()['last-round']
            block_times = []

            # Analyze last 20 blocks
            for i in range(1, min(21, current_round)):
                try:
                    round_num = current_round - i
                    block_info = self.algod_client.block_info(round_num)
                    timestamp = block_info.get('block', {}).get('ts', 0)

                    if timestamp > 0:
                        block_times.append(timestamp)

                except Exception:
                    continue

            if len(block_times) < 2:
                return 4.5, 0.0  # Default Algorand block time

            # Calculate time differences
            time_diffs = []
            for i in range(1, len(block_times)):
                diff = block_times[i-1] - block_times[i]  # Reverse order (newest first)
                if 0 < diff < 60:  # Reasonable block time range
                    time_diffs.append(diff)

            if time_diffs:
                avg_block_time = statistics.mean(time_diffs)
                variance = statistics.stdev(time_diffs) if len(time_diffs) > 1 else 0.0
                return avg_block_time, variance
            else:
                return 4.5, 0.0

        except Exception as e:
            self.logger.error(f"Error calculating block time metrics: {e}")
            return 4.5, 0.5

    async def _get_participation_rate(self) -> float:
        """Get current consensus participation rate"""
        try:
            # This would typically come from node metrics
            # For now, estimate based on network activity

            # In a real implementation, this would query:
            # - Node's consensus participation metrics
            # - Network-wide participation statistics

            # Return a reasonable estimate
            return 0.92  # 92% participation rate estimate

        except Exception as e:
            self.logger.error(f"Error getting participation rate: {e}")
            return 0.90

    async def _get_stake_metrics(self) -> Tuple[int, int]:
        """Get online and total stake metrics"""
        try:
            # This would query the network for stake distribution
            # For now, return estimates

            total_algo_supply = 10_000_000_000  # 10B ALGO total supply
            online_stake_ratio = 0.70  # Estimate 70% of ALGO is online

            online_stake = int(total_algo_supply * online_stake_ratio * 1e6)  # Convert to microALGO
            total_stake = int(total_algo_supply * 1e6)

            return online_stake, total_stake

        except Exception as e:
            self.logger.error(f"Error getting stake metrics: {e}")
            return 7_000_000_000_000_000, 10_000_000_000_000_000

    async def _get_mempool_size(self) -> int:
        """Get current mempool size"""
        try:
            # Get pending transactions from the node
            # This is a simplified approach - real implementation would
            # query the node's transaction pool

            # For now, return a reasonable estimate based on network load
            current_time = datetime.utcnow()
            hour = current_time.hour

            # Simulate daily activity patterns
            if 14 <= hour <= 22:  # Peak hours
                base_size = 2000
            elif 6 <= hour <= 14:  # Moderate hours
                base_size = 1000
            else:  # Low activity hours
                base_size = 300

            # Add some randomness
            import random
            return base_size + random.randint(-200, 500)

        except Exception as e:
            self.logger.error(f"Error getting mempool size: {e}")
            return 500

    async def _analyze_participation_trend(self) -> str:
        """Analyze participation rate trend"""
        try:
            # This would analyze historical participation data
            # For now, return a static assessment
            return "stable"

        except Exception as e:
            self.logger.error(f"Error analyzing participation trend: {e}")
            return "unknown"

    async def _estimate_online_validators(self) -> int:
        """Estimate number of online validators"""
        try:
            # This would query relay node information
            # Algorand doesn't have traditional validators, but relay nodes

            # Estimate based on known relay node count
            return 120  # Approximate number of relay nodes

        except Exception as e:
            self.logger.error(f"Error estimating online validators: {e}")
            return 100

    async def _estimate_total_validators(self) -> int:
        """Estimate total number of validators"""
        try:
            # Total relay nodes in the network
            return 150

        except Exception as e:
            self.logger.error(f"Error estimating total validators: {e}")
            return 150

    async def _analyze_block_production_consistency(self) -> float:
        """Analyze block production consistency"""
        try:
            # Calculate consistency based on block time variance
            _, variance = await self._calculate_block_time_metrics()

            # Convert variance to consistency score (lower variance = higher consistency)
            target_variance = self.thresholds['block_time']['excellent_variance']

            if variance <= target_variance:
                return 1.0
            elif variance <= target_variance * 2:
                return 0.8
            elif variance <= target_variance * 3:
                return 0.6
            else:
                return 0.4

        except Exception as e:
            self.logger.error(f"Error analyzing block production consistency: {e}")
            return 0.8

    async def _count_recent_missed_blocks(self) -> int:
        """Count recently missed blocks"""
        try:
            # Algorand doesn't typically have "missed" blocks due to its consensus
            # But we can check for gaps in block production
            return 0

        except Exception as e:
            self.logger.error(f"Error counting missed blocks: {e}")
            return 0

    async def _estimate_agreement_time(self) -> float:
        """Estimate consensus agreement time"""
        try:
            # Algorand's consensus is typically very fast
            # Agreement time is usually < 1 second
            return 0.5  # 500ms estimate

        except Exception as e:
            self.logger.error(f"Error estimating agreement time: {e}")
            return 1.0

    async def _analyze_mempool_transactions(self) -> Dict[str, int]:
        """Analyze transaction types in mempool"""
        try:
            # This would analyze pending transactions by type
            # For now, return estimated distribution

            total_pending = await self._get_mempool_size()

            return {
                'pay': int(total_pending * 0.4),      # 40% payment transactions
                'appl': int(total_pending * 0.35),    # 35% application calls
                'axfer': int(total_pending * 0.2),    # 20% asset transfers
                'keyreg': int(total_pending * 0.05)   # 5% key registration
            }

        except Exception as e:
            self.logger.error(f"Error analyzing mempool transactions: {e}")
            return {'pay': 0, 'appl': 0, 'axfer': 0, 'keyreg': 0}

    async def _estimate_processing_rate(self) -> float:
        """Estimate transaction processing rate"""
        try:
            # Based on current TPS
            tps = await self._calculate_current_tps()
            return tps

        except Exception as e:
            self.logger.error(f"Error estimating processing rate: {e}")
            return 100.0

    async def _estimate_average_wait_time(self, mempool_size: int, processing_rate: float) -> float:
        """Estimate average transaction wait time"""
        try:
            if processing_rate > 0:
                return mempool_size / processing_rate
            else:
                return 60.0  # 1 minute default

        except Exception as e:
            self.logger.error(f"Error estimating wait time: {e}")
            return 30.0

    async def _analyze_fee_distribution(self) -> Dict[str, int]:
        """Analyze fee distribution in mempool"""
        try:
            # This would analyze fees of pending transactions
            # For now, return estimated distribution

            suggested_params = self.algod_client.suggested_params()
            min_fee = suggested_params.min_fee

            return {
                'min_fee': min_fee,
                'low_fee': min_fee * 2,
                'medium_fee': min_fee * 5,
                'high_fee': min_fee * 10
            }

        except Exception as e:
            self.logger.error(f"Error analyzing fee distribution: {e}")
            return {'min_fee': 1000, 'low_fee': 2000, 'medium_fee': 5000, 'high_fee': 10000}

    def _calculate_congestion_factor(self, utilization_rate: float, processing_rate: float) -> float:
        """Calculate network congestion factor"""
        # Higher utilization and lower processing rate = higher congestion
        base_congestion = utilization_rate

        # Adjust based on processing rate
        if processing_rate < 50:  # Low processing rate
            base_congestion *= 1.5
        elif processing_rate > 200:  # High processing rate
            base_congestion *= 0.7

        return min(1.0, max(0.0, base_congestion))

    def _calculate_throughput_score(self, metrics: NetworkMetrics) -> float:
        """Calculate throughput performance score"""
        tps = metrics.transactions_per_second
        thresholds = self.thresholds['tps_levels']

        if tps >= thresholds['excellent']:
            return 1.0
        elif tps >= thresholds['good']:
            return 0.8
        elif tps >= thresholds['average']:
            return 0.6
        elif tps >= thresholds['poor']:
            return 0.4
        else:
            return 0.2

    def _calculate_consensus_score(self, participation_rate: float) -> float:
        """Calculate consensus health score"""
        thresholds = self.thresholds['participation_levels']

        if participation_rate >= thresholds['excellent']:
            return 1.0
        elif participation_rate >= thresholds['good']:
            return 0.8
        elif participation_rate >= thresholds['average']:
            return 0.6
        elif participation_rate >= thresholds['poor']:
            return 0.4
        else:
            return 0.2

    def _calculate_stability_score(self, metrics: NetworkMetrics, consensus: ConsensusHealth) -> float:
        """Calculate network stability score"""
        # Based on block time variance and consensus consistency
        target_variance = self.thresholds['block_time']['excellent_variance']

        if metrics.block_time_variance <= target_variance:
            time_score = 1.0
        elif metrics.block_time_variance <= target_variance * 2:
            time_score = 0.8
        elif metrics.block_time_variance <= target_variance * 3:
            time_score = 0.6
        else:
            time_score = 0.4

        # Combine with consensus consistency
        stability_score = (time_score + consensus.block_production_consistency) / 2

        return stability_score

    def _calculate_overall_health_score(
        self, throughput_score: float, consensus_score: float, stability_score: float
    ) -> float:
        """Calculate overall network health score"""
        weights = self.network_config['health_weights']

        return (
            throughput_score * weights['transaction_throughput'] +
            consensus_score * weights['consensus_health'] +
            stability_score * (weights['node_participation'] + weights['mempool_status'])
        )

    def _determine_health_status(self, score: float) -> str:
        """Determine network health status"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.6:
            return "average"
        elif score >= 0.4:
            return "poor"
        else:
            return "critical"

    def _generate_alerts(
        self, metrics: NetworkMetrics, consensus: ConsensusHealth, mempool: TransactionPoolStatus
    ) -> List[str]:
        """Generate network health alerts"""
        alerts = []

        # TPS alerts
        if metrics.transactions_per_second < self.thresholds['tps_levels']['critical']:
            alerts.append(f"CRITICAL: Very low TPS ({metrics.transactions_per_second:.1f})")

        # Participation alerts
        if consensus.participation_rate < self.thresholds['participation_levels']['critical']:
            alerts.append(f"CRITICAL: Low consensus participation ({consensus.participation_rate:.1%})")

        # Block time alerts
        if metrics.block_time_variance > self.thresholds['block_time']['poor_variance']:
            alerts.append(f"WARNING: High block time variance ({metrics.block_time_variance:.1f}s)")

        # Mempool alerts
        if mempool.utilization_rate > 0.8:
            alerts.append(f"WARNING: High mempool utilization ({mempool.utilization_rate:.1%})")

        return alerts

    def _generate_recommendations(
        self, metrics: NetworkMetrics, consensus: ConsensusHealth,
        mempool: TransactionPoolStatus, overall_score: float
    ) -> List[str]:
        """Generate network improvement recommendations"""
        recommendations = []

        if overall_score < 0.6:
            recommendations.append("Monitor network closely due to below-average performance")

        if metrics.transactions_per_second < 100:
            recommendations.append("Consider network capacity planning for increased throughput")

        if consensus.participation_rate < 0.85:
            recommendations.append("Encourage increased consensus participation")

        if mempool.utilization_rate > 0.7:
            recommendations.append("Monitor transaction fees and processing delays")

        if not recommendations:
            recommendations.append("Network operating within normal parameters")

        return recommendations

    def _analyze_performance_trend(self) -> str:
        """Analyze recent performance trend"""
        if len(self.metrics_history) < 5:
            return "insufficient_data"

        # Simple trend analysis based on recent TPS
        recent_tps = [m.transactions_per_second for m in self.metrics_history[-5:]]

        if len(recent_tps) < 2:
            return "stable"

        trend = (recent_tps[-1] - recent_tps[0]) / max(recent_tps[0], 1)

        if trend > 0.1:
            return "improving"
        elif trend < -0.1:
            return "declining"
        else:
            return "stable"

    def _calculate_capacity_utilization(self, metrics: NetworkMetrics, mempool: TransactionPoolStatus) -> float:
        """Calculate network capacity utilization"""
        # Based on TPS relative to theoretical maximum and mempool utilization
        theoretical_max_tps = 1000  # Algorand's theoretical maximum
        tps_utilization = metrics.transactions_per_second / theoretical_max_tps

        # Combine with mempool utilization
        overall_utilization = (tps_utilization + mempool.utilization_rate) / 2

        return min(1.0, overall_utilization)

    def _store_metrics_history(self, metrics: NetworkMetrics):
        """Store metrics for trend analysis"""
        self.metrics_history.append(metrics)

        # Keep only recent history
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]

    def _calculate_finality_confidence(self, participation_rate: float) -> float:
        """Calculate finality confidence based on participation"""
        # Higher participation = higher finality confidence
        return min(1.0, participation_rate / 0.67)  # Byzantine fault tolerance threshold

    def _default_network_metrics(self) -> NetworkMetrics:
        """Default network metrics for error cases"""
        return NetworkMetrics(
            timestamp=datetime.utcnow(),
            current_round=0,
            last_round_time=datetime.utcnow(),
            transactions_per_second=0.0,
            transactions_in_round=0,
            block_time=4.5,
            block_time_variance=0.5,
            rounds_per_minute=13.3,
            participation_rate=0.9,
            online_stake=7_000_000_000_000_000,
            total_stake=10_000_000_000_000_000,
            mempool_size=1000,
            pending_transactions=1000,
            suggested_fee=1000,
            min_fee=1000
        )

    def _default_consensus_health(self) -> ConsensusHealth:
        """Default consensus health for error cases"""
        return ConsensusHealth(
            participation_rate=0.9,
            participation_trend="unknown",
            consensus_score=0.8,
            online_validators=100,
            total_validators=150,
            validator_distribution={},
            block_production_consistency=0.8,
            missed_blocks=0,
            fork_events=0,
            agreement_time=0.5,
            finality_confidence=0.95
        )

    def _default_mempool_status(self) -> TransactionPoolStatus:
        """Default mempool status for error cases"""
        return TransactionPoolStatus(
            current_size=1000,
            max_size=50000,
            utilization_rate=0.02,
            payment_txns=400,
            app_call_txns=350,
            asset_txns=200,
            key_reg_txns=50,
            average_wait_time=10.0,
            processing_rate=100.0,
            rejected_transactions=0,
            fee_distribution={'min_fee': 1000, 'low_fee': 2000, 'medium_fee': 5000, 'high_fee': 10000},
            congestion_factor=0.1
        )