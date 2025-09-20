"""
Voting Concentration and Power Distribution Analysis
Monitors voting power concentration, whale dominance, and distribution inequality
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import statistics
from collections import defaultdict

class ConcentrationRiskLevel(Enum):
    """Concentration risk levels"""
    EXTREME = "extreme"
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

@dataclass
class VotingPowerMetrics:
    """Voting power distribution metrics"""
    total_voting_power: float
    total_holders: int
    active_voters: int
    participation_rate: float

    # Concentration metrics
    top_1_percentage: float
    top_5_percentage: float
    top_10_percentage: float
    top_50_percentage: float
    top_100_percentage: float

    # Distribution metrics
    gini_coefficient: float
    herfindahl_index: float
    shannon_entropy: float
    median_holding: float
    mean_holding: float

    # Whale analysis
    whale_count: int
    whale_total_power: float
    mega_whale_count: int
    mega_whale_power: float

    # Delegation metrics
    delegation_concentration: Dict[str, float]
    delegate_power_distribution: List[float]

@dataclass
class ConcentrationAlert:
    """Concentration-based alert"""
    alert_type: str
    risk_level: ConcentrationRiskLevel
    threshold_breached: float
    current_value: float
    affected_metrics: List[str]
    recommendations: List[str]
    timestamp: datetime

@dataclass
class ConcentrationTrend:
    """Concentration trend analysis"""
    metric_name: str
    current_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    change_rate: float
    significance: float
    projection_7d: float
    projection_30d: float

class VotingConcentrationAnalyzer:
    """Analyzes voting power concentration and distribution"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the voting concentration analyzer"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.historical_metrics = []
        self.concentration_thresholds = self._load_concentration_thresholds()

    def _load_concentration_thresholds(self) -> Dict[str, float]:
        """Load concentration risk thresholds from config"""
        return {
            'critical_whale_threshold': self.config.get('governance_risk', {})
                .get('voting_concentration', {}).get('critical_whale_threshold', 0.20),
            'high_risk_threshold': self.config.get('governance_risk', {})
                .get('voting_concentration', {}).get('high_risk_threshold', 0.15),
            'moderate_risk_threshold': self.config.get('governance_risk', {})
                .get('voting_concentration', {}).get('moderate_risk_threshold', 0.10),
            'top_10_dominance_threshold': self.config.get('governance_risk', {})
                .get('voting_concentration', {}).get('top_10_dominance_threshold', 0.60),
            'top_50_dominance_threshold': self.config.get('governance_risk', {})
                .get('voting_concentration', {}).get('top_50_dominance_threshold', 0.80),
            'gini_coefficient_threshold': self.config.get('governance_risk', {})
                .get('voting_concentration', {}).get('gini_coefficient_threshold', 0.85)
        }

    async def analyze_voting_concentration(self,
                                         voting_data: Dict[str, Any]) -> Tuple[VotingPowerMetrics, List[ConcentrationAlert]]:
        """
        Perform comprehensive voting concentration analysis

        Args:
            voting_data: Raw voting power and holder data

        Returns:
            Tuple of voting power metrics and concentration alerts
        """
        try:
            self.logger.info("Starting voting concentration analysis")

            # Extract and process voting power data
            metrics = await self._calculate_voting_metrics(voting_data)

            # Analyze concentration risks
            alerts = await self._analyze_concentration_risks(metrics)

            # Store historical data
            self._store_historical_metrics(metrics)

            self.logger.info(f"Voting concentration analysis completed. "
                           f"Gini coefficient: {metrics.gini_coefficient:.3f}, "
                           f"Top 1% control: {metrics.top_1_percentage:.1%}")

            return metrics, alerts

        except Exception as e:
            self.logger.error(f"Voting concentration analysis failed: {e}")
            raise

    async def _calculate_voting_metrics(self, voting_data: Dict[str, Any]) -> VotingPowerMetrics:
        """Calculate comprehensive voting power metrics"""
        try:
            # Extract basic data
            holder_balances = voting_data.get('holder_balances', {})
            total_voting_power = sum(holder_balances.values())
            total_holders = len(holder_balances)

            # Active voters (holders who have voted recently)
            active_voters = voting_data.get('active_voters', 0)
            participation_rate = active_voters / total_holders if total_holders > 0 else 0

            # Sort balances for concentration calculations
            sorted_balances = sorted(holder_balances.values(), reverse=True)

            # Calculate concentration percentages
            top_percentages = self._calculate_top_percentages(sorted_balances, total_voting_power)

            # Calculate distribution metrics
            gini_coefficient = self._calculate_gini_coefficient(sorted_balances)
            herfindahl_index = self._calculate_herfindahl_index(sorted_balances, total_voting_power)
            shannon_entropy = self._calculate_shannon_entropy(sorted_balances, total_voting_power)

            # Calculate statistics
            median_holding = statistics.median(sorted_balances) if sorted_balances else 0
            mean_holding = statistics.mean(sorted_balances) if sorted_balances else 0

            # Whale analysis
            whale_metrics = self._analyze_whale_concentration(sorted_balances, total_voting_power)

            # Delegation analysis
            delegation_data = voting_data.get('delegation_data', {})
            delegation_metrics = self._analyze_delegation_concentration(delegation_data)

            return VotingPowerMetrics(
                total_voting_power=total_voting_power,
                total_holders=total_holders,
                active_voters=active_voters,
                participation_rate=participation_rate,
                top_1_percentage=top_percentages['top_1'],
                top_5_percentage=top_percentages['top_5'],
                top_10_percentage=top_percentages['top_10'],
                top_50_percentage=top_percentages['top_50'],
                top_100_percentage=top_percentages['top_100'],
                gini_coefficient=gini_coefficient,
                herfindahl_index=herfindahl_index,
                shannon_entropy=shannon_entropy,
                median_holding=median_holding,
                mean_holding=mean_holding,
                whale_count=whale_metrics['whale_count'],
                whale_total_power=whale_metrics['whale_total_power'],
                mega_whale_count=whale_metrics['mega_whale_count'],
                mega_whale_power=whale_metrics['mega_whale_power'],
                delegation_concentration=delegation_metrics['concentration'],
                delegate_power_distribution=delegation_metrics['distribution']
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate voting metrics: {e}")
            raise

    def _calculate_top_percentages(self, sorted_balances: List[float], total_power: float) -> Dict[str, float]:
        """Calculate top N percentage concentrations"""
        if not sorted_balances or total_power == 0:
            return {key: 0.0 for key in ['top_1', 'top_5', 'top_10', 'top_50', 'top_100']}

        percentages = {}
        total_holders = len(sorted_balances)

        # Calculate top N percentages
        for pct_name, holder_count in [('top_1', max(1, total_holders // 100)),
                                      ('top_5', max(1, total_holders // 20)),
                                      ('top_10', max(1, total_holders // 10)),
                                      ('top_50', max(1, total_holders // 2)),
                                      ('top_100', min(100, total_holders))]:
            top_n_power = sum(sorted_balances[:holder_count])
            percentages[pct_name] = top_n_power / total_power

        return percentages

    def _calculate_gini_coefficient(self, sorted_balances: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        if not sorted_balances:
            return 0.0

        n = len(sorted_balances)
        if n == 1:
            return 0.0

        # Sort in ascending order for Gini calculation
        sorted_asc = sorted(sorted_balances)
        cumsum = np.cumsum(sorted_asc)

        # Gini coefficient formula
        gini = (2 * sum((i + 1) * value for i, value in enumerate(sorted_asc))) / (n * sum(sorted_asc)) - (n + 1) / n

        return max(0.0, min(1.0, gini))

    def _calculate_herfindahl_index(self, sorted_balances: List[float], total_power: float) -> float:
        """Calculate Herfindahl-Hirschman Index for market concentration"""
        if not sorted_balances or total_power == 0:
            return 0.0

        # Calculate market shares squared
        hhi = sum((balance / total_power) ** 2 for balance in sorted_balances)
        return hhi

    def _calculate_shannon_entropy(self, sorted_balances: List[float], total_power: float) -> float:
        """Calculate Shannon entropy for distribution diversity"""
        if not sorted_balances or total_power == 0:
            return 0.0

        # Calculate Shannon entropy
        entropy = 0.0
        for balance in sorted_balances:
            if balance > 0:
                proportion = balance / total_power
                entropy -= proportion * np.log2(proportion)

        return entropy

    def _analyze_whale_concentration(self, sorted_balances: List[float], total_power: float) -> Dict[str, Any]:
        """Analyze whale (large holder) concentration"""
        whale_threshold = total_power * 0.01  # 1% of total power
        mega_whale_threshold = total_power * 0.05  # 5% of total power

        whales = [balance for balance in sorted_balances if balance >= whale_threshold]
        mega_whales = [balance for balance in sorted_balances if balance >= mega_whale_threshold]

        return {
            'whale_count': len(whales),
            'whale_total_power': sum(whales) / total_power if total_power > 0 else 0,
            'mega_whale_count': len(mega_whales),
            'mega_whale_power': sum(mega_whales) / total_power if total_power > 0 else 0
        }

    def _analyze_delegation_concentration(self, delegation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze delegation power concentration"""
        delegate_powers = delegation_data.get('delegate_powers', {})

        if not delegate_powers:
            return {
                'concentration': {},
                'distribution': []
            }

        # Sort delegate powers
        sorted_powers = sorted(delegate_powers.values(), reverse=True)
        total_delegated = sum(sorted_powers)

        # Calculate concentration metrics
        concentration = {}
        if total_delegated > 0:
            concentration['top_delegate'] = sorted_powers[0] / total_delegated if sorted_powers else 0
            concentration['top_3_delegates'] = sum(sorted_powers[:3]) / total_delegated
            concentration['top_5_delegates'] = sum(sorted_powers[:5]) / total_delegated
            concentration['top_10_delegates'] = sum(sorted_powers[:10]) / total_delegated

        return {
            'concentration': concentration,
            'distribution': [power / total_delegated for power in sorted_powers] if total_delegated > 0 else []
        }

    async def _analyze_concentration_risks(self, metrics: VotingPowerMetrics) -> List[ConcentrationAlert]:
        """Analyze concentration risks and generate alerts"""
        alerts = []

        try:
            # Check critical whale threshold
            if metrics.top_1_percentage > self.concentration_thresholds['critical_whale_threshold']:
                alerts.append(ConcentrationAlert(
                    alert_type="CRITICAL_WHALE_CONCENTRATION",
                    risk_level=ConcentrationRiskLevel.CRITICAL,
                    threshold_breached=self.concentration_thresholds['critical_whale_threshold'],
                    current_value=metrics.top_1_percentage,
                    affected_metrics=["top_1_percentage", "governance_security"],
                    recommendations=[
                        "Implement emergency governance measures",
                        "Encourage token distribution initiatives",
                        "Consider governance power caps"
                    ],
                    timestamp=datetime.utcnow()
                ))

            # Check high risk whale threshold
            elif metrics.top_1_percentage > self.concentration_thresholds['high_risk_threshold']:
                alerts.append(ConcentrationAlert(
                    alert_type="HIGH_WHALE_CONCENTRATION",
                    risk_level=ConcentrationRiskLevel.HIGH,
                    threshold_breached=self.concentration_thresholds['high_risk_threshold'],
                    current_value=metrics.top_1_percentage,
                    affected_metrics=["top_1_percentage"],
                    recommendations=[
                        "Monitor whale activities closely",
                        "Implement voting power distribution mechanisms"
                    ],
                    timestamp=datetime.utcnow()
                ))

            # Check top 10 dominance
            if metrics.top_10_percentage > self.concentration_thresholds['top_10_dominance_threshold']:
                alerts.append(ConcentrationAlert(
                    alert_type="TOP_10_DOMINANCE",
                    risk_level=ConcentrationRiskLevel.HIGH,
                    threshold_breached=self.concentration_thresholds['top_10_dominance_threshold'],
                    current_value=metrics.top_10_percentage,
                    affected_metrics=["top_10_percentage", "decentralization"],
                    recommendations=[
                        "Promote broader token distribution",
                        "Implement anti-concentration mechanisms"
                    ],
                    timestamp=datetime.utcnow()
                ))

            # Check Gini coefficient (inequality)
            if metrics.gini_coefficient > self.concentration_thresholds['gini_coefficient_threshold']:
                alerts.append(ConcentrationAlert(
                    alert_type="HIGH_INEQUALITY",
                    risk_level=ConcentrationRiskLevel.HIGH,
                    threshold_breached=self.concentration_thresholds['gini_coefficient_threshold'],
                    current_value=metrics.gini_coefficient,
                    affected_metrics=["gini_coefficient", "distribution_equality"],
                    recommendations=[
                        "Launch token distribution campaigns",
                        "Implement progressive governance mechanisms"
                    ],
                    timestamp=datetime.utcnow()
                ))

            # Check delegation concentration
            if metrics.delegation_concentration:
                top_delegate = metrics.delegation_concentration.get('top_delegate', 0)
                delegation_limit = self.config.get('governance_risk', {}).get('token_risks', {}).get('delegation_concentration_limit', 0.25)

                if top_delegate > delegation_limit:
                    alerts.append(ConcentrationAlert(
                        alert_type="DELEGATION_CONCENTRATION",
                        risk_level=ConcentrationRiskLevel.MODERATE,
                        threshold_breached=delegation_limit,
                        current_value=top_delegate,
                        affected_metrics=["delegation_concentration"],
                        recommendations=[
                            "Implement delegation caps",
                            "Encourage delegation diversification"
                        ],
                        timestamp=datetime.utcnow()
                    ))

            # Check Herfindahl Index (market concentration)
            if metrics.herfindahl_index > 0.15:  # High concentration threshold
                risk_level = ConcentrationRiskLevel.HIGH if metrics.herfindahl_index > 0.25 else ConcentrationRiskLevel.MODERATE
                alerts.append(ConcentrationAlert(
                    alert_type="MARKET_CONCENTRATION",
                    risk_level=risk_level,
                    threshold_breached=0.15,
                    current_value=metrics.herfindahl_index,
                    affected_metrics=["herfindahl_index", "market_concentration"],
                    recommendations=[
                        "Implement anti-monopoly governance measures",
                        "Encourage competitive token distribution"
                    ],
                    timestamp=datetime.utcnow()
                ))

            # Check participation rate
            if metrics.participation_rate < 0.20:  # Very low participation
                alerts.append(ConcentrationAlert(
                    alert_type="LOW_PARTICIPATION",
                    risk_level=ConcentrationRiskLevel.HIGH,
                    threshold_breached=0.20,
                    current_value=metrics.participation_rate,
                    affected_metrics=["participation_rate", "governance_legitimacy"],
                    recommendations=[
                        "Launch participation incentive programs",
                        "Improve governance accessibility",
                        "Implement participation rewards"
                    ],
                    timestamp=datetime.utcnow()
                ))

            return alerts

        except Exception as e:
            self.logger.error(f"Risk analysis failed: {e}")
            return []

    def _store_historical_metrics(self, metrics: VotingPowerMetrics):
        """Store historical metrics for trend analysis"""
        self.historical_metrics.append({
            'timestamp': datetime.utcnow(),
            'top_1_percentage': metrics.top_1_percentage,
            'top_10_percentage': metrics.top_10_percentage,
            'gini_coefficient': metrics.gini_coefficient,
            'herfindahl_index': metrics.herfindahl_index,
            'participation_rate': metrics.participation_rate,
            'whale_count': metrics.whale_count,
            'whale_total_power': metrics.whale_total_power
        })

        # Keep only last 90 days of data
        cutoff_time = datetime.utcnow() - timedelta(days=90)
        self.historical_metrics = [
            entry for entry in self.historical_metrics
            if entry['timestamp'] > cutoff_time
        ]

    async def analyze_concentration_trends(self) -> List[ConcentrationTrend]:
        """Analyze concentration trends over time"""
        if len(self.historical_metrics) < 2:
            return []

        trends = []

        try:
            # Analyze each metric
            for metric_name in ['top_1_percentage', 'top_10_percentage', 'gini_coefficient',
                              'herfindahl_index', 'participation_rate', 'whale_total_power']:

                values = [entry[metric_name] for entry in self.historical_metrics]
                timestamps = [entry['timestamp'] for entry in self.historical_metrics]

                if len(values) >= 7:  # Need at least a week of data
                    trend = self._calculate_trend(metric_name, values, timestamps)
                    trends.append(trend)

            return trends

        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return []

    def _calculate_trend(self, metric_name: str, values: List[float], timestamps: List[datetime]) -> ConcentrationTrend:
        """Calculate trend for a specific metric"""
        current_value = values[-1]

        # Calculate simple linear trend
        if len(values) >= 7:
            recent_values = values[-7:]  # Last week
            trend_slope = (recent_values[-1] - recent_values[0]) / 7

            # Determine trend direction
            if abs(trend_slope) < current_value * 0.01:  # Less than 1% change
                direction = "stable"
            elif trend_slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"

            # Calculate significance (how much change relative to current value)
            significance = abs(trend_slope) / current_value if current_value > 0 else 0

            # Project future values
            projection_7d = current_value + (trend_slope * 7)
            projection_30d = current_value + (trend_slope * 30)

        else:
            trend_slope = 0
            direction = "stable"
            significance = 0
            projection_7d = current_value
            projection_30d = current_value

        return ConcentrationTrend(
            metric_name=metric_name,
            current_value=current_value,
            trend_direction=direction,
            change_rate=trend_slope,
            significance=significance,
            projection_7d=max(0, projection_7d),
            projection_30d=max(0, projection_30d)
        )

    async def get_concentration_summary(self) -> Dict[str, Any]:
        """Get a summary of current concentration status"""
        try:
            if not self.historical_metrics:
                return {"status": "No data available"}

            latest_metrics = self.historical_metrics[-1]

            # Determine overall concentration status
            top_1_pct = latest_metrics['top_1_percentage']
            gini_coeff = latest_metrics['gini_coefficient']

            if top_1_pct > 0.20 or gini_coeff > 0.85:
                status = "CRITICAL"
            elif top_1_pct > 0.15 or gini_coeff > 0.75:
                status = "HIGH"
            elif top_1_pct > 0.10 or gini_coeff > 0.65:
                status = "MODERATE"
            else:
                status = "LOW"

            return {
                "status": status,
                "top_1_control": latest_metrics['top_1_percentage'],
                "top_10_control": latest_metrics['top_10_percentage'],
                "gini_coefficient": latest_metrics['gini_coefficient'],
                "whale_count": latest_metrics['whale_count'],
                "participation_rate": latest_metrics['participation_rate'],
                "last_updated": latest_metrics['timestamp']
            }

        except Exception as e:
            self.logger.error(f"Failed to get concentration summary: {e}")
            return {"status": "ERROR", "message": str(e)}

    def get_whale_analysis(self, voting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed whale analysis"""
        try:
            holder_balances = voting_data.get('holder_balances', {})
            total_power = sum(holder_balances.values())

            # Define whale categories
            whale_categories = {
                'mega_whales': total_power * 0.05,  # 5%+ of total
                'large_whales': total_power * 0.01,  # 1-5% of total
                'medium_whales': total_power * 0.005,  # 0.5-1% of total
                'small_whales': total_power * 0.001   # 0.1-0.5% of total
            }

            whale_analysis = {}

            for category, threshold in whale_categories.items():
                whales_in_category = [
                    balance for balance in holder_balances.values()
                    if balance >= threshold
                ]

                if category == 'large_whales':
                    # Exclude mega whales from large whales
                    whales_in_category = [
                        balance for balance in whales_in_category
                        if balance < whale_categories['mega_whales']
                    ]
                elif category == 'medium_whales':
                    # Exclude large and mega whales
                    whales_in_category = [
                        balance for balance in whales_in_category
                        if balance < whale_categories['large_whales']
                    ]
                elif category == 'small_whales':
                    # Exclude all larger whales
                    whales_in_category = [
                        balance for balance in whales_in_category
                        if balance < whale_categories['medium_whales']
                    ]

                whale_analysis[category] = {
                    'count': len(whales_in_category),
                    'total_power': sum(whales_in_category),
                    'percentage_of_total': sum(whales_in_category) / total_power if total_power > 0 else 0,
                    'average_holding': sum(whales_in_category) / len(whales_in_category) if whales_in_category else 0
                }

            return whale_analysis

        except Exception as e:
            self.logger.error(f"Whale analysis failed: {e}")
            return {}

# Export main classes
__all__ = ['VotingConcentrationAnalyzer', 'VotingPowerMetrics', 'ConcentrationAlert', 'ConcentrationTrend', 'ConcentrationRiskLevel']