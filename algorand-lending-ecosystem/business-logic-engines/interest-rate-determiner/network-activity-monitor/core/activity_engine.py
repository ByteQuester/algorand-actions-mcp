"""
Network Activity Engine
Main engine that combines network health, DApp activity, and ecosystem monitoring for interest rate adjustments.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import yaml

from .network_health import NetworkHealthMonitor, NetworkHealthReport
from .dapp_activity import DAppActivityMonitor, DAppActivityReport
from .ecosystem_monitor import EcosystemMonitor, EcosystemReport


@dataclass
class ActivityComponents:
    """Individual activity component reports"""
    network_health: NetworkHealthReport
    dapp_activity: DAppActivityReport
    ecosystem_health: EcosystemReport
    combined_activity_score: float
    utilization_category: str
    rate_adjustment: float


@dataclass
class NetworkActivityReport:
    """Comprehensive network activity analysis report"""
    timestamp: datetime

    # Component reports
    components: ActivityComponents

    # Aggregate scores
    network_performance_score: float
    ecosystem_vitality_score: float
    overall_activity_score: float

    # Rate impact
    utilization_category: str
    recommended_rate_adjustment: float
    adjustment_confidence: float

    # Insights
    key_metrics: Dict[str, float]
    activity_trends: List[str]
    performance_indicators: List[str]
    risk_warnings: List[str]
    recommendations: List[str]

    # Future projections
    projected_activity: Dict[str, float]
    capacity_outlook: str


@dataclass
class ActivityTrendAnalysis:
    """Network activity trend analysis"""
    short_term_trend: str      # 24 hours
    medium_term_trend: str     # 7 days
    long_term_trend: str       # 30 days

    momentum_indicators: Dict[str, float]
    seasonal_adjustments: Dict[str, float]
    growth_projections: Dict[str, float]


class NetworkActivityEngine:
    """Main engine for network activity monitoring and rate adjustment recommendations"""

    def __init__(self, config_path: str = None, config_dict: Dict = None):
        """Initialize with configuration file or dictionary"""
        if config_dict:
            self.config = config_dict
        else:
            config_path = config_path or "/home/mpo/algorand-showcase/algorand-lending-ecosystem/business-logic-engines/interest-rate-determiner/network-activity-monitor/config/config.yaml"
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)

        self.logger = logging.getLogger(__name__)

        # Initialize component monitors
        self.network_monitor = NetworkHealthMonitor(self.config)
        self.dapp_monitor = DAppActivityMonitor(self.config)
        self.ecosystem_monitor = EcosystemMonitor(self.config)

        # Utilization categories from config
        self.utilization_categories = self.config['utilization_categories']

        # Historical data for trend analysis
        self.activity_history = []
        self.max_history_size = 720  # 30 days of hourly data

    async def analyze_network_activity(self) -> NetworkActivityReport:
        """Perform comprehensive network activity analysis"""
        try:
            self.logger.info("Starting comprehensive network activity analysis")

            # Run parallel monitoring
            network_report, dapp_report, ecosystem_report = await asyncio.gather(
                self.network_monitor.get_network_health_report(),
                self.dapp_monitor.get_dapp_activity_report(),
                self.ecosystem_monitor.generate_ecosystem_report(),
                return_exceptions=True
            )

            # Handle monitoring errors
            if isinstance(network_report, Exception):
                self.logger.error(f"Network monitoring failed: {network_report}")
                network_report = self._create_default_network_report()

            if isinstance(dapp_report, Exception):
                self.logger.error(f"DApp monitoring failed: {dapp_report}")
                dapp_report = self._create_default_dapp_report()

            if isinstance(ecosystem_report, Exception):
                self.logger.error(f"Ecosystem monitoring failed: {ecosystem_report}")
                ecosystem_report = self._create_default_ecosystem_report()

            # Calculate combined activity score
            combined_score = self._calculate_combined_activity_score(
                network_report, dapp_report, ecosystem_report
            )

            # Determine utilization category and rate adjustment
            utilization_category, rate_adjustment = self._determine_rate_adjustment(
                combined_score, network_report, dapp_report
            )

            # Create activity components
            components = ActivityComponents(
                network_health=network_report,
                dapp_activity=dapp_report,
                ecosystem_health=ecosystem_report,
                combined_activity_score=combined_score,
                utilization_category=utilization_category,
                rate_adjustment=rate_adjustment
            )

            # Calculate aggregate scores
            network_performance_score = self._calculate_network_performance_score(network_report)
            ecosystem_vitality_score = self._calculate_ecosystem_vitality_score(ecosystem_report)
            overall_activity_score = self._calculate_overall_activity_score(
                network_performance_score, dapp_report.overall_activity_score, ecosystem_vitality_score
            )

            # Calculate adjustment confidence
            adjustment_confidence = self._calculate_adjustment_confidence(
                network_report, dapp_report, ecosystem_report
            )

            # Generate insights
            key_metrics = self._extract_key_metrics(network_report, dapp_report, ecosystem_report)
            activity_trends = self._analyze_activity_trends()
            performance_indicators = self._generate_performance_indicators(
                network_report, dapp_report, ecosystem_report
            )
            risk_warnings = self._generate_risk_warnings(network_report, dapp_report, ecosystem_report)
            recommendations = self._generate_activity_recommendations(
                network_report, dapp_report, ecosystem_report, overall_activity_score
            )

            # Future projections
            projected_activity = self._project_future_activity(components)
            capacity_outlook = self._assess_capacity_outlook(network_report, projected_activity)

            # Store for trend analysis
            self._store_activity_data(components)

            return NetworkActivityReport(
                timestamp=datetime.utcnow(),
                components=components,
                network_performance_score=network_performance_score,
                ecosystem_vitality_score=ecosystem_vitality_score,
                overall_activity_score=overall_activity_score,
                utilization_category=utilization_category,
                recommended_rate_adjustment=rate_adjustment,
                adjustment_confidence=adjustment_confidence,
                key_metrics=key_metrics,
                activity_trends=activity_trends,
                performance_indicators=performance_indicators,
                risk_warnings=risk_warnings,
                recommendations=recommendations,
                projected_activity=projected_activity,
                capacity_outlook=capacity_outlook
            )

        except Exception as e:
            self.logger.error(f"Error in network activity analysis: {e}")
            raise

    async def get_real_time_activity_score(self) -> Dict[str, float]:
        """Get real-time activity score for immediate rate adjustments"""
        try:
            # Quick network metrics
            network_tps = await self._get_quick_tps()
            mempool_utilization = await self._get_quick_mempool_utilization()

            # Quick activity score
            network_score = min(1.0, network_tps / 500)  # Normalize to 500 TPS
            utilization_score = 1.0 - mempool_utilization  # Higher utilization = lower score

            quick_score = (network_score + utilization_score) / 2

            # Determine quick rate adjustment
            _, rate_adjustment = self._determine_rate_adjustment_from_score(quick_score)

            return {
                'activity_score': quick_score,
                'network_tps': network_tps,
                'mempool_utilization': mempool_utilization,
                'rate_adjustment': rate_adjustment,
                'timestamp': datetime.utcnow().timestamp()
            }

        except Exception as e:
            self.logger.error(f"Error getting real-time activity score: {e}")
            return {
                'activity_score': 0.5,
                'rate_adjustment': 0.0,
                'error': str(e),
                'timestamp': datetime.utcnow().timestamp()
            }

    def _calculate_combined_activity_score(
        self, network_report: NetworkHealthReport,
        dapp_report: DAppActivityReport,
        ecosystem_report: EcosystemReport
    ) -> float:
        """Calculate combined network activity score"""
        weights = self.config['network_monitoring']['health_weights']

        # Network health contribution
        network_contribution = (
            network_report.overall_health_score * weights['transaction_throughput'] +
            network_report.consensus_health.consensus_score * weights['consensus_health']
        )

        # DApp activity contribution
        dapp_weights = self.config['network_monitoring']['dapp_weights']
        dapp_contribution = (
            dapp_report.defi_activity_score * dapp_weights['defi_protocol_usage'] +
            dapp_report.nft_activity_score * dapp_weights['nft_marketplace_activity'] +
            dapp_report.governance_activity_score * dapp_weights['governance_activity'] +
            (dapp_report.smart_contract_metrics.daily_app_calls / 50_000) * dapp_weights['smart_contract_activity']
        )

        # Ecosystem health contribution (10% weight)
        ecosystem_contribution = ecosystem_report.overall_ecosystem_score * 0.1

        # Combined score
        combined_score = (
            network_contribution * 0.4 +
            dapp_contribution * 0.5 +
            ecosystem_contribution * 0.1
        )

        return min(1.0, max(0.0, combined_score))

    def _determine_rate_adjustment(
        self, combined_score: float, network_report: NetworkHealthReport, dapp_report: DAppActivityReport
    ) -> Tuple[str, float]:
        """Determine rate adjustment based on activity levels"""
        # Primary scoring based on TPS and DApp activity
        network_tps = network_report.network_metrics.transactions_per_second
        dapp_activity_level = dapp_report.overall_activity_score

        # Weighted activity score for rate determination
        rate_score = (network_tps / 1000) * 0.6 + dapp_activity_level * 0.4

        # Map to utilization categories
        for category, config in self.utilization_categories.items():
            if rate_score * 1000 >= config['min_tps']:  # Convert back to TPS scale
                return category, config['rate_impact']

        # Default to lowest category
        lowest_category = list(self.utilization_categories.keys())[-1]
        return lowest_category, self.utilization_categories[lowest_category]['rate_impact']

    def _determine_rate_adjustment_from_score(self, score: float) -> Tuple[str, float]:
        """Determine rate adjustment from a simple score"""
        # Convert score to equivalent TPS for categorization
        equivalent_tps = score * 1000

        for category, config in self.utilization_categories.items():
            if equivalent_tps >= config['min_tps']:
                return category, config['rate_impact']

        # Default to lowest category
        lowest_category = list(self.utilization_categories.keys())[-1]
        return lowest_category, self.utilization_categories[lowest_category]['rate_impact']

    def _calculate_network_performance_score(self, network_report: NetworkHealthReport) -> float:
        """Calculate network performance score"""
        return (
            network_report.throughput_score * 0.4 +
            network_report.consensus_score * 0.3 +
            network_report.stability_score * 0.3
        )

    def _calculate_ecosystem_vitality_score(self, ecosystem_report: EcosystemReport) -> float:
        """Calculate ecosystem vitality score"""
        return (
            ecosystem_report.growth_score * 0.3 +
            ecosystem_report.adoption_score * 0.3 +
            ecosystem_report.health_score * 0.2 +
            ecosystem_report.innovation_score * 0.2
        )

    def _calculate_overall_activity_score(
        self, network_score: float, dapp_score: float, ecosystem_score: float
    ) -> float:
        """Calculate overall activity score"""
        return (
            network_score * 0.4 +
            dapp_score * 0.4 +
            ecosystem_score * 0.2
        )

    def _calculate_adjustment_confidence(
        self, network_report: NetworkHealthReport,
        dapp_report: DAppActivityReport,
        ecosystem_report: EcosystemReport
    ) -> float:
        """Calculate confidence in rate adjustment recommendation"""
        # Higher confidence when all metrics agree
        scores = [
            network_report.overall_health_score,
            dapp_report.overall_activity_score,
            ecosystem_report.overall_ecosystem_score
        ]

        # Calculate variance - lower variance = higher confidence
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Convert variance to confidence (0-1)
        confidence = max(0.5, 1.0 - variance * 4)  # Scale variance appropriately

        # Boost confidence for strong signals
        if all(s > 0.8 for s in scores) or all(s < 0.3 for s in scores):
            confidence = min(1.0, confidence + 0.2)

        return confidence

    def _extract_key_metrics(
        self, network_report: NetworkHealthReport,
        dapp_report: DAppActivityReport,
        ecosystem_report: EcosystemReport
    ) -> Dict[str, float]:
        """Extract key metrics for summary"""
        return {
            'network_tps': network_report.network_metrics.transactions_per_second,
            'block_time': network_report.network_metrics.block_time,
            'participation_rate': network_report.consensus_health.participation_rate,
            'mempool_utilization': network_report.mempool_status.utilization_rate,
            'dapp_activity_score': dapp_report.overall_activity_score,
            'defi_volume_24h': dapp_report.defi_metrics.dex_volume_24h,
            'ecosystem_growth_score': ecosystem_report.growth_score,
            'developer_count': ecosystem_report.adoption_metrics.developer_count,
            'total_tvl': dapp_report.defi_metrics.total_tvl_usd
        }

    def _analyze_activity_trends(self) -> List[str]:
        """Analyze activity trends from historical data"""
        if len(self.activity_history) < 5:
            return ["Insufficient data for trend analysis"]

        trends = []

        # Recent activity levels
        recent_scores = [data.combined_activity_score for data in self.activity_history[-5:]]
        if len(recent_scores) >= 2:
            recent_trend = (recent_scores[-1] - recent_scores[0]) / max(recent_scores[0], 0.01)

            if recent_trend > 0.1:
                trends.append("Strong upward activity trend")
            elif recent_trend > 0.05:
                trends.append("Moderate upward activity trend")
            elif recent_trend < -0.1:
                trends.append("Declining activity trend")
            elif recent_trend < -0.05:
                trends.append("Moderate downward trend")
            else:
                trends.append("Stable activity levels")

        # TPS trends
        if hasattr(self.activity_history[-1], 'network_health'):
            current_tps = self.activity_history[-1].network_health.network_metrics.transactions_per_second
            if current_tps > 500:
                trends.append("High network throughput")
            elif current_tps < 50:
                trends.append("Low network activity")

        return trends

    def _generate_performance_indicators(
        self, network_report: NetworkHealthReport,
        dapp_report: DAppActivityReport,
        ecosystem_report: EcosystemReport
    ) -> List[str]:
        """Generate performance indicators"""
        indicators = []

        # Network performance
        if network_report.network_metrics.transactions_per_second > 300:
            indicators.append("High network throughput performance")

        if network_report.consensus_health.participation_rate > 0.9:
            indicators.append("Strong consensus participation")

        # DApp activity
        if dapp_report.defi_metrics.total_tvl_usd > 100_000_000:
            indicators.append("Strong DeFi ecosystem ($100M+ TVL)")

        if dapp_report.smart_contract_metrics.daily_app_calls > 25_000:
            indicators.append("High smart contract usage")

        # Ecosystem health
        if ecosystem_report.growth_score > 0.8:
            indicators.append("Excellent ecosystem growth")

        if ecosystem_report.adoption_metrics.developer_count > 4_000:
            indicators.append("Robust developer ecosystem")

        return indicators

    def _generate_risk_warnings(
        self, network_report: NetworkHealthReport,
        dapp_report: DAppActivityReport,
        ecosystem_report: EcosystemReport
    ) -> List[str]:
        """Generate risk warnings"""
        warnings = []

        # Network risks
        if network_report.network_metrics.transactions_per_second < 20:
            warnings.append("Very low network activity may indicate issues")

        if network_report.mempool_status.utilization_rate > 0.8:
            warnings.append("High mempool utilization may cause delays")

        # DApp risks
        if dapp_report.overall_activity_score < 0.3:
            warnings.append("Low DApp activity levels")

        # Ecosystem risks
        if ecosystem_report.health_score < 0.6:
            warnings.append("Ecosystem health concerns")

        return warnings

    def _generate_activity_recommendations(
        self, network_report: NetworkHealthReport,
        dapp_report: DAppActivityReport,
        ecosystem_report: EcosystemReport,
        overall_score: float
    ) -> List[str]:
        """Generate activity-based recommendations"""
        recommendations = []

        if overall_score > 0.8:
            recommendations.append("Network showing excellent activity - maintain current policies")

        elif overall_score > 0.6:
            recommendations.append("Good network activity - minor optimizations may help")

        elif overall_score > 0.4:
            recommendations.append("Moderate activity - consider incentives to boost usage")

        else:
            recommendations.append("Low activity - implement growth initiatives")

        # Specific recommendations
        if network_report.network_metrics.transactions_per_second < 100:
            recommendations.append("Consider marketing campaigns to increase transaction volume")

        if dapp_report.defi_metrics.total_tvl_usd < 50_000_000:
            recommendations.append("Focus on DeFi ecosystem development")

        return recommendations

    def _project_future_activity(self, components: ActivityComponents) -> Dict[str, float]:
        """Project future activity levels"""
        current_score = components.combined_activity_score

        # Simple projection based on trends
        projections = {
            '24h': current_score * 1.02,  # Slight growth expected
            '7d': current_score * 1.05,   # Weekly growth
            '30d': current_score * 1.15   # Monthly growth
        }

        # Cap projections at 1.0
        return {k: min(1.0, v) for k, v in projections.items()}

    def _assess_capacity_outlook(
        self, network_report: NetworkHealthReport, projected_activity: Dict[str, float]
    ) -> str:
        """Assess network capacity outlook"""
        current_utilization = network_report.capacity_utilization
        projected_30d_activity = projected_activity.get('30d', 0.5)

        if projected_30d_activity > 0.9:
            return "approaching_capacity"
        elif projected_30d_activity > 0.7:
            return "moderate_growth_expected"
        elif projected_30d_activity > 0.5:
            return "stable_capacity"
        else:
            return "excess_capacity"

    def _store_activity_data(self, components: ActivityComponents):
        """Store activity data for trend analysis"""
        self.activity_history.append(components)

        # Keep only recent history
        if len(self.activity_history) > self.max_history_size:
            self.activity_history = self.activity_history[-self.max_history_size:]

    async def _get_quick_tps(self) -> float:
        """Get quick TPS estimate"""
        try:
            status = self.network_monitor.algod_client.status()
            # Simple TPS estimate - would be more sophisticated in practice
            return 150.0  # Placeholder
        except:
            return 100.0

    async def _get_quick_mempool_utilization(self) -> float:
        """Get quick mempool utilization estimate"""
        try:
            # Would query actual mempool size
            return 0.3  # 30% utilization placeholder
        except:
            return 0.5

    # Default report generators for error cases
    def _create_default_network_report(self) -> NetworkHealthReport:
        """Create default network report"""
        from .network_health import (
            NetworkHealthReport, NetworkMetrics, ConsensusHealth, TransactionPoolStatus
        )

        default_metrics = NetworkMetrics(
            timestamp=datetime.utcnow(),
            current_round=0,
            last_round_time=datetime.utcnow(),
            transactions_per_second=100.0,
            transactions_in_round=500,
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

        default_consensus = ConsensusHealth(
            participation_rate=0.9,
            participation_trend="stable",
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

        default_mempool = TransactionPoolStatus(
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
            fee_distribution={'min_fee': 1000},
            congestion_factor=0.1
        )

        return NetworkHealthReport(
            timestamp=datetime.utcnow(),
            network_metrics=default_metrics,
            consensus_health=default_consensus,
            mempool_status=default_mempool,
            throughput_score=0.6,
            consensus_score=0.8,
            stability_score=0.8,
            overall_health_score=0.7,
            health_status="average",
            alerts=[],
            recommendations=["Default report - monitoring failed"],
            performance_trend="unknown",
            capacity_utilization=0.5
        )

    def _create_default_dapp_report(self) -> DAppActivityReport:
        """Create default DApp report"""
        from .dapp_activity import (
            DAppActivityReport, SmartContractMetrics, DeFiMetrics,
            NFTActivity, GovernanceActivity
        )

        default_sc = SmartContractMetrics(
            total_app_calls=10000,
            daily_app_calls=10000,
            unique_apps_used=500,
            top_apps_by_calls=[],
            top_apps_by_users=[],
            new_applications=50,
            app_call_growth=0.1,
            user_adoption_rate=0.1
        )

        default_defi = DeFiMetrics(
            dex_volume_24h=1_000_000.0,
            dex_trades_count=1000,
            swap_protocols=[],
            lending_volume_24h=500_000.0,
            borrows_count=100,
            supplies_count=150,
            lending_protocols=[],
            total_liquidity_pools=200,
            total_tvl_usd=50_000_000.0,
            liquidity_growth=0.05,
            farming_protocols=5,
            staking_volume=10_000_000.0,
            average_apr=0.08
        )

        default_nft = NFTActivity(
            total_marketplaces=3,
            daily_sales_count=50,
            daily_sales_volume=10_000.0,
            new_collections=5,
            new_nfts_minted=200,
            creator_count=50,
            floor_price_changes={},
            volume_by_marketplace={}
        )

        default_gov = GovernanceActivity(
            total_participants=50_000,
            participation_rate=0.05,
            algo_committed=1_000_000_000.0,
            active_proposals=2,
            votes_cast=30_000,
            voting_participation=0.6,
            delegated_stake=200_000_000.0,
            delegation_rate=0.2
        )

        return DAppActivityReport(
            timestamp=datetime.utcnow(),
            smart_contract_metrics=default_sc,
            defi_metrics=default_defi,
            nft_activity=default_nft,
            governance_activity=default_gov,
            defi_activity_score=0.5,
            nft_activity_score=0.3,
            governance_activity_score=0.4,
            overall_activity_score=0.45,
            ecosystem_status="moderate",
            activity_trend="stable",
            growth_indicators=["Default data"],
            recommendations=["Default report - monitoring failed"]
        )

    def _create_default_ecosystem_report(self) -> EcosystemReport:
        """Create default ecosystem report"""
        from .ecosystem_monitor import (
            EcosystemReport, EcosystemGrowth, AdoptionMetrics,
            EcosystemHealth, LongTermTrends
        )

        # Use the default methods from EcosystemMonitor
        monitor = EcosystemMonitor(self.config)

        return EcosystemReport(
            timestamp=datetime.utcnow(),
            ecosystem_growth=monitor._default_growth(),
            adoption_metrics=monitor._default_adoption(),
            ecosystem_health=monitor._default_health(),
            long_term_trends=monitor._default_trends(),
            growth_score=0.6,
            adoption_score=0.5,
            health_score=0.7,
            innovation_score=0.4,
            overall_ecosystem_score=0.55,
            ecosystem_status="developing",
            key_insights=["Default report - monitoring failed"],
            risk_factors=[],
            opportunities=[],
            recommendations=["Restore monitoring functionality"]
        )

    async def get_activity_summary(self) -> Dict:
        """Get high-level activity summary"""
        try:
            report = await self.analyze_network_activity()

            return {
                'timestamp': report.timestamp.isoformat(),
                'overall_activity_score': report.overall_activity_score,
                'utilization_category': report.utilization_category,
                'recommended_rate_adjustment': report.recommended_rate_adjustment,
                'adjustment_confidence': report.adjustment_confidence,
                'network_tps': report.key_metrics.get('network_tps', 0),
                'defi_volume_24h': report.key_metrics.get('defi_volume_24h', 0),
                'ecosystem_status': report.components.ecosystem_health.ecosystem_status,
                'capacity_outlook': report.capacity_outlook,
                'risk_warnings_count': len(report.risk_warnings),
                'performance_indicators_count': len(report.performance_indicators)
            }

        except Exception as e:
            self.logger.error(f"Error generating activity summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'overall_activity_score': 0.5,
                'recommended_rate_adjustment': 0.0
            }

    def export_activity_report(self, report: NetworkActivityReport, format: str = 'json') -> str:
        """Export activity report in specified format"""
        if format == 'json':
            return json.dumps({
                'timestamp': report.timestamp.isoformat(),
                'overall_activity_score': report.overall_activity_score,
                'utilization_category': report.utilization_category,
                'recommended_rate_adjustment': report.recommended_rate_adjustment,
                'adjustment_confidence': report.adjustment_confidence,
                'key_metrics': report.key_metrics,
                'activity_trends': report.activity_trends,
                'performance_indicators': report.performance_indicators,
                'risk_warnings': report.risk_warnings,
                'recommendations': report.recommendations,
                'capacity_outlook': report.capacity_outlook
            }, indent=2)

        elif format == 'yaml':
            return yaml.dump({
                'timestamp': report.timestamp.isoformat(),
                'activity_score': float(report.overall_activity_score),
                'utilization_category': report.utilization_category,
                'rate_adjustment': float(report.recommended_rate_adjustment),
                'confidence': float(report.adjustment_confidence),
                'key_metrics': {k: float(v) for k, v in report.key_metrics.items()},
                'trends': report.activity_trends,
                'recommendations': report.recommendations
            })

        else:
            raise ValueError(f"Unsupported format: {format}")