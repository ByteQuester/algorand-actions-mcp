"""
Cross-Chain Bridge Risk Assessment

Analyzes cross-chain bridge activities and associated risks
for Algorand DeFi protocols and users.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics

from ..models.blockchain_risk import RiskLevel, RiskAlert


class BridgeType(Enum):
    """Types of cross-chain bridges"""
    LOCK_AND_MINT = "lock_and_mint"
    BURN_AND_MINT = "burn_and_mint"
    LIQUIDITY_POOL = "liquidity_pool"
    ATOMIC_SWAP = "atomic_swap"
    WRAPPED_ASSET = "wrapped_asset"


class BridgeRiskCategory(Enum):
    """Categories of bridge risks"""
    TECHNICAL = "technical"
    ECONOMIC = "economic"
    GOVERNANCE = "governance"
    OPERATIONAL = "operational"
    REGULATORY = "regulatory"


@dataclass
class BridgeActivity:
    """Bridge activity data"""
    bridge_name: str
    bridge_type: BridgeType
    source_chain: str
    destination_chain: str
    asset_symbol: str
    amount: float
    timestamp: datetime
    transaction_hash: str
    user_address: str
    bridge_fee: float
    confirmation_time: timedelta


@dataclass
class BridgeRiskMetrics:
    """Risk metrics for a specific bridge"""
    bridge_name: str
    tvl: float
    daily_volume: float
    monthly_volume: float
    user_count: int
    transaction_count: int
    avg_transaction_size: float
    largest_transaction: float
    fee_volatility: float
    uptime_percentage: float
    failure_rate: float
    avg_confirmation_time: timedelta
    security_incidents: int
    audit_score: float
    insurance_coverage: float


@dataclass
class BridgeLiquidityAnalysis:
    """Bridge liquidity analysis"""
    bridge_name: str
    total_liquidity: float
    utilization_rate: float
    liquidity_depth: Dict[str, float]  # Asset -> liquidity depth
    slippage_impact: Dict[float, float]  # Amount -> slippage
    rebalancing_frequency: int
    liquidity_providers: int
    concentration_risk: float


class BridgeRiskAssessment:
    """Comprehensive bridge risk assessment system"""

    def __init__(self):
        self.bridge_metrics = {}
        self.risk_thresholds = {
            'high_volume_ratio': 0.1,  # 10% of daily volume in single transaction
            'liquidity_utilization': 0.8,  # 80% utilization
            'failure_rate': 0.05,  # 5% failure rate
            'concentration_risk': 0.5  # 50% concentration
        }

    async def assess_bridge_risk(
        self,
        bridge_name: str,
        activities: List[BridgeActivity],
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """
        Assess comprehensive risk for a specific bridge

        Args:
            bridge_name: Name of the bridge to assess
            activities: List of bridge activities
            time_window: Time window for analysis

        Returns:
            Comprehensive risk assessment
        """
        # Calculate bridge metrics
        metrics = await self._calculate_bridge_metrics(bridge_name, activities, time_window)

        # Analyze liquidity risks
        liquidity_analysis = await self._analyze_liquidity_risks(bridge_name, activities)

        # Assess technical risks
        technical_risks = await self._assess_technical_risks(metrics)

        # Assess economic risks
        economic_risks = await self._assess_economic_risks(metrics, liquidity_analysis)

        # Assess operational risks
        operational_risks = await self._assess_operational_risks(metrics)

        # Calculate overall risk score
        overall_risk = self._calculate_overall_bridge_risk(
            technical_risks, economic_risks, operational_risks
        )

        return {
            'bridge_name': bridge_name,
            'overall_risk_score': overall_risk['score'],
            'risk_level': overall_risk['level'],
            'metrics': metrics,
            'liquidity_analysis': liquidity_analysis,
            'risk_breakdown': {
                'technical': technical_risks,
                'economic': economic_risks,
                'operational': operational_risks
            },
            'recommendations': self._generate_recommendations(overall_risk, metrics),
            'assessment_timestamp': datetime.utcnow()
        }

    async def analyze_user_bridge_behavior(
        self,
        user_address: str,
        activities: List[BridgeActivity],
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """
        Analyze user's bridge usage patterns for risk assessment

        Args:
            user_address: User's wallet address
            activities: User's bridge activities
            time_window: Analysis time window

        Returns:
            User bridge behavior analysis
        """
        user_activities = [
            activity for activity in activities
            if activity.user_address == user_address
        ]

        if not user_activities:
            return {
                'user_address': user_address,
                'risk_score': 0.0,
                'patterns': [],
                'anomalies': []
            }

        # Analyze patterns
        patterns = await self._analyze_bridge_patterns(user_activities)

        # Detect anomalies
        anomalies = await self._detect_bridge_anomalies(user_activities)

        # Calculate user risk score
        risk_score = self._calculate_user_bridge_risk(patterns, anomalies)

        return {
            'user_address': user_address,
            'risk_score': risk_score,
            'activity_count': len(user_activities),
            'total_volume': sum(activity.amount for activity in user_activities),
            'bridges_used': list(set(activity.bridge_name for activity in user_activities)),
            'patterns': patterns,
            'anomalies': anomalies,
            'assessment_timestamp': datetime.utcnow()
        }

    async def _calculate_bridge_metrics(
        self,
        bridge_name: str,
        activities: List[BridgeActivity],
        time_window: timedelta
    ) -> BridgeRiskMetrics:
        """Calculate comprehensive bridge metrics"""
        bridge_activities = [
            activity for activity in activities
            if activity.bridge_name == bridge_name
        ]

        if not bridge_activities:
            return BridgeRiskMetrics(
                bridge_name=bridge_name,
                tvl=0, daily_volume=0, monthly_volume=0,
                user_count=0, transaction_count=0,
                avg_transaction_size=0, largest_transaction=0,
                fee_volatility=0, uptime_percentage=1.0,
                failure_rate=0, avg_confirmation_time=timedelta(0),
                security_incidents=0, audit_score=0.5,
                insurance_coverage=0
            )

        # Basic volume metrics
        total_volume = sum(activity.amount for activity in bridge_activities)
        transaction_count = len(bridge_activities)
        unique_users = len(set(activity.user_address for activity in bridge_activities))

        # Time-based metrics
        daily_activities = [
            activity for activity in bridge_activities
            if activity.timestamp >= datetime.utcnow() - timedelta(days=1)
        ]
        daily_volume = sum(activity.amount for activity in daily_activities)

        monthly_activities = [
            activity for activity in bridge_activities
            if activity.timestamp >= datetime.utcnow() - timedelta(days=30)
        ]
        monthly_volume = sum(activity.amount for activity in monthly_activities)

        # Transaction size analysis
        amounts = [activity.amount for activity in bridge_activities]
        avg_transaction_size = statistics.mean(amounts) if amounts else 0
        largest_transaction = max(amounts) if amounts else 0

        # Fee analysis
        fees = [activity.bridge_fee for activity in bridge_activities]
        fee_volatility = statistics.stdev(fees) if len(fees) > 1 else 0

        # Confirmation time analysis
        confirmation_times = [
            activity.confirmation_time.total_seconds()
            for activity in bridge_activities
            if activity.confirmation_time
        ]
        avg_confirmation_seconds = statistics.mean(confirmation_times) if confirmation_times else 0
        avg_confirmation_time = timedelta(seconds=avg_confirmation_seconds)

        # Placeholder for complex metrics (would require external data)
        uptime_percentage = 0.99  # Would be calculated from monitoring data
        failure_rate = 0.01  # Would be calculated from failed transactions
        security_incidents = 0  # Would be tracked from security reports
        audit_score = 0.8  # Would be based on audit reports
        insurance_coverage = total_volume * 0.5  # Placeholder

        return BridgeRiskMetrics(
            bridge_name=bridge_name,
            tvl=total_volume,  # Simplified TVL calculation
            daily_volume=daily_volume,
            monthly_volume=monthly_volume,
            user_count=unique_users,
            transaction_count=transaction_count,
            avg_transaction_size=avg_transaction_size,
            largest_transaction=largest_transaction,
            fee_volatility=fee_volatility,
            uptime_percentage=uptime_percentage,
            failure_rate=failure_rate,
            avg_confirmation_time=avg_confirmation_time,
            security_incidents=security_incidents,
            audit_score=audit_score,
            insurance_coverage=insurance_coverage
        )

    async def _analyze_liquidity_risks(
        self,
        bridge_name: str,
        activities: List[BridgeActivity]
    ) -> BridgeLiquidityAnalysis:
        """Analyze bridge liquidity risks"""
        bridge_activities = [
            activity for activity in activities
            if activity.bridge_name == bridge_name
        ]

        if not bridge_activities:
            return BridgeLiquidityAnalysis(
                bridge_name=bridge_name,
                total_liquidity=0,
                utilization_rate=0,
                liquidity_depth={},
                slippage_impact={},
                rebalancing_frequency=0,
                liquidity_providers=0,
                concentration_risk=0
            )

        # Group by assets
        asset_volumes = {}
        for activity in bridge_activities:
            asset = activity.asset_symbol
            if asset not in asset_volumes:
                asset_volumes[asset] = []
            asset_volumes[asset].append(activity.amount)

        # Calculate liquidity depth per asset
        liquidity_depth = {}
        for asset, volumes in asset_volumes.items():
            total_volume = sum(volumes)
            liquidity_depth[asset] = total_volume

        total_liquidity = sum(liquidity_depth.values())

        # Calculate utilization rate (simplified)
        recent_volume = sum(
            activity.amount for activity in bridge_activities
            if activity.timestamp >= datetime.utcnow() - timedelta(days=1)
        )
        utilization_rate = recent_volume / max(total_liquidity, 1)

        # Estimate slippage impact
        slippage_impact = {}
        for amount in [1000, 10000, 100000, 1000000]:
            # Simplified slippage calculation
            impact = min(amount / max(total_liquidity, 1) * 0.1, 0.5)
            slippage_impact[amount] = impact

        # Calculate concentration risk
        if asset_volumes:
            sorted_volumes = sorted(liquidity_depth.values(), reverse=True)
            top_asset_volume = sorted_volumes[0] if sorted_volumes else 0
            concentration_risk = top_asset_volume / max(total_liquidity, 1)
        else:
            concentration_risk = 0

        return BridgeLiquidityAnalysis(
            bridge_name=bridge_name,
            total_liquidity=total_liquidity,
            utilization_rate=utilization_rate,
            liquidity_depth=liquidity_depth,
            slippage_impact=slippage_impact,
            rebalancing_frequency=30,  # Placeholder
            liquidity_providers=50,  # Placeholder
            concentration_risk=concentration_risk
        )

    async def _assess_technical_risks(self, metrics: BridgeRiskMetrics) -> Dict[str, float]:
        """Assess technical risks of the bridge"""
        risks = {}

        # Uptime risk
        risks['uptime_risk'] = 1.0 - metrics.uptime_percentage

        # Failure rate risk
        risks['failure_rate_risk'] = min(metrics.failure_rate / self.risk_thresholds['failure_rate'], 1.0)

        # Confirmation time risk
        confirmation_minutes = metrics.avg_confirmation_time.total_seconds() / 60
        risks['confirmation_delay_risk'] = min(confirmation_minutes / 60, 1.0)  # Risk increases after 1 hour

        # Security audit risk
        risks['audit_risk'] = 1.0 - metrics.audit_score

        # Security incidents risk
        risks['security_incident_risk'] = min(metrics.security_incidents / 5, 1.0)

        return risks

    async def _assess_economic_risks(
        self,
        metrics: BridgeRiskMetrics,
        liquidity: BridgeLiquidityAnalysis
    ) -> Dict[str, float]:
        """Assess economic risks of the bridge"""
        risks = {}

        # Liquidity utilization risk
        risks['liquidity_utilization_risk'] = min(
            liquidity.utilization_rate / self.risk_thresholds['liquidity_utilization'], 1.0
        )

        # Concentration risk
        risks['concentration_risk'] = min(
            liquidity.concentration_risk / self.risk_thresholds['concentration_risk'], 1.0
        )

        # Volume volatility risk
        if metrics.daily_volume > 0:
            volume_ratio = metrics.largest_transaction / metrics.daily_volume
            risks['volume_volatility_risk'] = min(
                volume_ratio / self.risk_thresholds['high_volume_ratio'], 1.0
            )
        else:
            risks['volume_volatility_risk'] = 0

        # Fee volatility risk
        if metrics.avg_transaction_size > 0:
            fee_ratio = metrics.fee_volatility / metrics.avg_transaction_size
            risks['fee_volatility_risk'] = min(fee_ratio, 1.0)
        else:
            risks['fee_volatility_risk'] = 0

        # Insurance coverage risk
        coverage_ratio = metrics.insurance_coverage / max(metrics.tvl, 1)
        risks['insurance_coverage_risk'] = 1.0 - min(coverage_ratio, 1.0)

        return risks

    async def _assess_operational_risks(self, metrics: BridgeRiskMetrics) -> Dict[str, float]:
        """Assess operational risks of the bridge"""
        risks = {}

        # Scale risk (too much volume relative to capacity)
        if metrics.tvl > 0:
            volume_to_tvl = metrics.daily_volume / metrics.tvl
            risks['scale_risk'] = min(volume_to_tvl, 1.0)
        else:
            risks['scale_risk'] = 0

        # Dependency risk (based on user concentration)
        if metrics.transaction_count > 0:
            avg_txns_per_user = metrics.transaction_count / max(metrics.user_count, 1)
            risks['user_dependency_risk'] = min(avg_txns_per_user / 100, 1.0)
        else:
            risks['user_dependency_risk'] = 0

        # Operational complexity risk (simplified)
        risks['operational_complexity_risk'] = 0.3  # Placeholder based on bridge type

        return risks

    def _calculate_overall_bridge_risk(
        self,
        technical_risks: Dict[str, float],
        economic_risks: Dict[str, float],
        operational_risks: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate overall bridge risk score"""
        # Weight categories
        weights = {
            'technical': 0.4,
            'economic': 0.35,
            'operational': 0.25
        }

        # Calculate category scores
        technical_score = sum(technical_risks.values()) / len(technical_risks) if technical_risks else 0
        economic_score = sum(economic_risks.values()) / len(economic_risks) if economic_risks else 0
        operational_score = sum(operational_risks.values()) / len(operational_risks) if operational_risks else 0

        # Overall weighted score
        overall_score = (
            technical_score * weights['technical'] +
            economic_score * weights['economic'] +
            operational_score * weights['operational']
        )

        # Determine risk level
        if overall_score <= 0.2:
            risk_level = RiskLevel.LOW
        elif overall_score <= 0.4:
            risk_level = RiskLevel.MODERATE
        elif overall_score <= 0.7:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        return {
            'score': overall_score,
            'level': risk_level,
            'category_scores': {
                'technical': technical_score,
                'economic': economic_score,
                'operational': operational_score
            }
        }

    async def _analyze_bridge_patterns(self, activities: List[BridgeActivity]) -> List[str]:
        """Analyze user bridge usage patterns"""
        patterns = []

        if len(activities) < 2:
            return patterns

        # Analyze timing patterns
        timestamps = [activity.timestamp for activity in activities]
        timestamps.sort()

        time_gaps = []
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            time_gaps.append(gap.total_seconds())

        if time_gaps:
            avg_gap = statistics.mean(time_gaps)
            if avg_gap < 3600:  # Less than 1 hour
                patterns.append("Rapid sequential bridging")
            elif avg_gap > 7 * 24 * 3600:  # More than 1 week
                patterns.append("Infrequent bridge usage")

        # Analyze amount patterns
        amounts = [activity.amount for activity in activities]
        if len(set(amounts)) == 1:
            patterns.append("Identical bridge amounts")

        # Analyze bridge usage diversity
        bridges_used = set(activity.bridge_name for activity in activities)
        if len(bridges_used) == 1:
            patterns.append("Single bridge preference")
        elif len(bridges_used) >= 5:
            patterns.append("High bridge diversity")

        # Analyze chain patterns
        chains = set()
        for activity in activities:
            chains.add(activity.source_chain)
            chains.add(activity.destination_chain)

        if len(chains) <= 2:
            patterns.append("Limited chain interaction")

        return patterns

    async def _detect_bridge_anomalies(self, activities: List[BridgeActivity]) -> List[str]:
        """Detect anomalous bridge behavior"""
        anomalies = []

        if len(activities) < 3:
            return anomalies

        # Amount anomalies
        amounts = [activity.amount for activity in activities]
        if len(amounts) > 2:
            mean_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts)

            for amount in amounts:
                if std_amount > 0:
                    z_score = abs((amount - mean_amount) / std_amount)
                    if z_score > 3:
                        anomalies.append(f"Unusual transaction size: {amount}")

        # Time anomalies
        timestamps = [activity.timestamp for activity in activities]
        timestamps.sort()

        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            if gap < timedelta(minutes=5):
                anomalies.append("Extremely rapid bridge transactions")

        # Fee anomalies
        fees = [activity.bridge_fee for activity in activities]
        if len(fees) > 2:
            mean_fee = statistics.mean(fees)
            for fee in fees:
                if fee > mean_fee * 10:
                    anomalies.append(f"Unusually high bridge fee: {fee}")

        return anomalies

    def _calculate_user_bridge_risk(self, patterns: List[str], anomalies: List[str]) -> float:
        """Calculate user bridge risk score"""
        risk_score = 0.0

        # Pattern-based risk
        pattern_risks = {
            "Rapid sequential bridging": 0.3,
            "Identical bridge amounts": 0.4,
            "High bridge diversity": 0.2,
            "Limited chain interaction": 0.1
        }

        for pattern in patterns:
            risk_score += pattern_risks.get(pattern, 0.1)

        # Anomaly-based risk
        risk_score += len(anomalies) * 0.2

        return min(risk_score, 1.0)

    def _generate_recommendations(
        self,
        overall_risk: Dict[str, Any],
        metrics: BridgeRiskMetrics
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if overall_risk['level'] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Implement enhanced monitoring for this bridge")
            recommendations.append("Consider transaction limits for high-risk periods")

        if overall_risk['category_scores']['technical'] > 0.5:
            recommendations.append("Increase technical monitoring and alerts")
            recommendations.append("Require additional confirmations for large transactions")

        if overall_risk['category_scores']['economic'] > 0.5:
            recommendations.append("Monitor liquidity levels more closely")
            recommendations.append("Implement dynamic fee adjustments")

        if metrics.failure_rate > self.risk_thresholds['failure_rate']:
            recommendations.append("Investigate and address high failure rate")

        return recommendations

    def create_bridge_risk_alert(
        self,
        bridge_name: str,
        risk_assessment: Dict[str, Any]
    ) -> RiskAlert:
        """Create a bridge risk alert"""
        severity = risk_assessment['risk_level']

        return RiskAlert(
            alert_id=f"bridge_risk_{bridge_name}_{datetime.utcnow().timestamp()}",
            alert_type="BRIDGE_RISK",
            severity=severity,
            title=f"Bridge Risk Alert: {bridge_name}",
            description=f"Bridge {bridge_name} shows {severity.value} risk level "
                       f"with score {risk_assessment['overall_risk_score']:.2f}",
            affected_addresses=[],
            affected_protocols=[bridge_name],
            risk_score=risk_assessment['overall_risk_score'],
            confidence=0.8,
            detection_method="Bridge Risk Assessment",
            evidence={
                'metrics': risk_assessment['metrics'].__dict__,
                'risk_breakdown': risk_assessment['risk_breakdown']
            },
            recommendations=risk_assessment['recommendations']
        )