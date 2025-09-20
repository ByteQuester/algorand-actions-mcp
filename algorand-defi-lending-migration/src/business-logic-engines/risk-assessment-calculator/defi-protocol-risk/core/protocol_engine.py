"""
DeFi Protocol Risk Engine
Master engine for comprehensive DeFi protocol risk assessment
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import yaml
import json
from pathlib import Path

from .protocol_exposure import ProtocolExposureAnalyzer, CrossProtocolExposure
from .concentration_risk import ConcentrationRiskAnalyzer, ConcentrationRiskAssessment
from .systemic_risk import SystemicRiskAnalyzer, SystemicRiskAssessment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProtocolRiskScore:
    """Individual protocol risk score"""
    protocol_name: str
    category: str
    exposure_risk: float
    concentration_risk: float
    systemic_risk: float
    liquidity_risk: float
    governance_risk: float
    overall_risk_score: float
    risk_tier: str
    confidence_level: float

@dataclass
class PortfolioRiskMetrics:
    """Portfolio-level risk metrics"""
    total_exposure_usd: float
    protocol_count: int
    category_count: int
    effective_diversification: float
    concentration_ratio: float
    systemic_vulnerability: float
    liquidity_coverage_ratio: float
    stress_test_score: float

@dataclass
class RiskAlert:
    """Risk alert information"""
    alert_type: str
    severity: str
    protocol: Optional[str]
    category: Optional[str]
    message: str
    threshold_exceeded: float
    current_value: float
    recommended_action: str
    urgency_score: float

@dataclass
class ComprehensiveRiskAssessment:
    """Complete DeFi protocol risk assessment"""
    portfolio_metrics: PortfolioRiskMetrics
    protocol_scores: List[ProtocolRiskScore]
    exposure_analysis: CrossProtocolExposure
    concentration_assessment: ConcentrationRiskAssessment
    systemic_assessment: SystemicRiskAssessment
    risk_alerts: List[RiskAlert]
    overall_portfolio_score: float
    risk_level: str
    confidence_score: float
    recommendations: List[str]
    next_review_date: datetime
    timestamp: datetime

class DeFiProtocolRiskEngine:
    """Master engine for comprehensive DeFi protocol risk assessment"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the DeFi protocol risk engine"""
        self.config = self._load_config(config_path)
        self.exposure_analyzer = ProtocolExposureAnalyzer(config_path)
        self.concentration_analyzer = ConcentrationRiskAnalyzer(config_path)
        self.systemic_analyzer = SystemicRiskAnalyzer(config_path)

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def assess_portfolio_risk(self, user_positions: Dict[str, float],
                                  include_stress_tests: bool = True,
                                  include_scenario_analysis: bool = True) -> ComprehensiveRiskAssessment:
        """Perform comprehensive portfolio risk assessment"""
        logger.info("Starting comprehensive DeFi protocol risk assessment...")

        if not user_positions:
            raise ValueError("No user positions provided for risk assessment")

        # Get protocol data for systemic analysis
        protocol_data = await self._fetch_protocol_data(list(user_positions.keys()))

        # Run all risk analyses in parallel
        exposure_task = self.exposure_analyzer.calculate_protocol_exposure(user_positions)
        concentration_task = self.concentration_analyzer.analyze_concentration_risk(user_positions)
        systemic_task = self.systemic_analyzer.analyze_systemic_risk(protocol_data)

        # Wait for all analyses to complete
        exposure_analysis, concentration_assessment, systemic_assessment = await asyncio.gather(
            exposure_task, concentration_task, systemic_task
        )

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(
            user_positions, exposure_analysis, concentration_assessment, systemic_assessment
        )

        # Calculate individual protocol risk scores
        protocol_scores = await self._calculate_protocol_risk_scores(
            user_positions, exposure_analysis, concentration_assessment, systemic_assessment
        )

        # Generate risk alerts
        risk_alerts = self._generate_risk_alerts(
            portfolio_metrics, protocol_scores, exposure_analysis, concentration_assessment, systemic_assessment
        )

        # Calculate overall portfolio score
        overall_portfolio_score = self._calculate_overall_portfolio_score(
            portfolio_metrics, protocol_scores, concentration_assessment, systemic_assessment
        )

        # Determine risk level
        risk_level = self._determine_portfolio_risk_level(overall_portfolio_score, risk_alerts)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            exposure_analysis, concentration_assessment, systemic_assessment
        )

        # Generate comprehensive recommendations
        recommendations = self._generate_comprehensive_recommendations(
            portfolio_metrics, protocol_scores, risk_alerts, overall_portfolio_score
        )

        # Determine next review date
        next_review_date = self._determine_next_review_date(risk_level, risk_alerts)

        return ComprehensiveRiskAssessment(
            portfolio_metrics=portfolio_metrics,
            protocol_scores=protocol_scores,
            exposure_analysis=exposure_analysis,
            concentration_assessment=concentration_assessment,
            systemic_assessment=systemic_assessment,
            risk_alerts=risk_alerts,
            overall_portfolio_score=overall_portfolio_score,
            risk_level=risk_level,
            confidence_score=confidence_score,
            recommendations=recommendations,
            next_review_date=next_review_date,
            timestamp=datetime.now()
        )

    async def _fetch_protocol_data(self, protocols: List[str]) -> Dict[str, Dict]:
        """Fetch protocol data for systemic analysis"""
        protocol_data = {}

        # Mock protocol data - in production, fetch from actual APIs
        mock_data = {
            'algofi': {
                'tvl_usd': 45000000,
                'total_borrowed': 25000000,
                'total_supplied': 55000000,
                'active_users': 2500,
                'governance_token_price': 0.15,
                'governance_market_cap': 15000000,
                'pools': ['ALGO', 'USDC', 'USDT', 'goBTC', 'goETH']
            },
            'folks_finance': {
                'tvl_usd': 32000000,
                'total_borrowed': 18000000,
                'total_supplied': 40000000,
                'active_users': 1800,
                'governance_token_price': 0.08,
                'governance_market_cap': 8000000,
                'pools': ['ALGO', 'USDC', 'USDT', 'gALGO']
            },
            'tinyman': {
                'tvl_usd': 25000000,
                'total_volume_24h': 2000000,
                'active_users': 3000,
                'governance_token_price': 0.12,
                'governance_market_cap': 12000000,
                'pools': ['ALGO/USDC', 'ALGO/USDT', 'USDC/USDT']
            },
            'pact': {
                'tvl_usd': 12000000,
                'total_volume_24h': 800000,
                'active_users': 1200,
                'governance_token_price': 0.05,
                'governance_market_cap': 5000000,
                'pools': ['ALGO/USDC', 'ALGO/PACT']
            },
            'humble_defi': {
                'tvl_usd': 6000000,
                'total_staked': 8000000,
                'active_users': 800,
                'governance_token_price': 0.03,
                'governance_market_cap': 3000000,
                'pools': ['ALGO', 'HMBL']
            },
            'algomint': {
                'tvl_usd': 4000000,
                'total_bridged': 5000000,
                'active_users': 600,
                'pools': ['goBTC', 'goETH']
            },
            'yieldly': {
                'tvl_usd': 2000000,
                'total_staked': 3000000,
                'active_users': 400,
                'governance_token_price': 0.01,
                'governance_market_cap': 1000000,
                'pools': ['ALGO', 'YLDY']
            }
        }

        for protocol in protocols:
            if protocol in mock_data:
                protocol_data[protocol] = mock_data[protocol]

        return protocol_data

    def _calculate_portfolio_metrics(self, positions: Dict[str, float],
                                   exposure_analysis: CrossProtocolExposure,
                                   concentration_assessment: ConcentrationRiskAssessment,
                                   systemic_assessment: SystemicRiskAssessment) -> PortfolioRiskMetrics:
        """Calculate comprehensive portfolio metrics"""
        total_exposure = sum(positions.values())
        protocol_count = len([p for p, v in positions.items() if v > 0])

        # Category count
        protocols_config = self.config.get('algorand_protocols', {})
        categories = set()
        for protocol in positions.keys():
            if positions[protocol] > 0:
                category = protocols_config.get(protocol, {}).get('category', 'unknown')
                categories.add(category)
        category_count = len(categories)

        # Effective diversification (from concentration analysis)
        effective_diversification = concentration_assessment.diversification_analysis.diversification_score

        # Concentration ratio (HHI from concentration analysis)
        concentration_ratio = concentration_assessment.concentration_metrics.herfindahl_index

        # Systemic vulnerability
        systemic_vulnerability = systemic_assessment.systemic_risk_score

        # Liquidity coverage ratio (simplified)
        liquidity_coverage_ratio = self._calculate_liquidity_coverage_ratio(positions)

        # Stress test score
        stress_test_score = self._calculate_stress_test_score(concentration_assessment.stress_test_results)

        return PortfolioRiskMetrics(
            total_exposure_usd=total_exposure,
            protocol_count=protocol_count,
            category_count=category_count,
            effective_diversification=effective_diversification,
            concentration_ratio=concentration_ratio,
            systemic_vulnerability=systemic_vulnerability,
            liquidity_coverage_ratio=liquidity_coverage_ratio,
            stress_test_score=stress_test_score
        )

    def _calculate_liquidity_coverage_ratio(self, positions: Dict[str, float]) -> float:
        """Calculate liquidity coverage ratio"""
        protocols_config = self.config.get('algorand_protocols', {})
        total_value = sum(positions.values())
        high_liquidity_value = 0

        for protocol, value in positions.items():
            if value <= 0:
                continue

            protocol_config = protocols_config.get(protocol, {})
            tvl_weight = protocol_config.get('tvl_weight', 0)

            # Consider protocols with high TVL weight as high liquidity
            if tvl_weight >= 0.15:  # 15% of DeFi TVL threshold
                high_liquidity_value += value

        return high_liquidity_value / total_value if total_value > 0 else 0

    def _calculate_stress_test_score(self, stress_test_results: Dict[str, float]) -> float:
        """Calculate overall stress test score"""
        if not stress_test_results:
            return 0.5  # Neutral score if no stress tests

        # Lower impact = better score
        max_impact = max(stress_test_results.values())
        stress_test_score = 1.0 - min(max_impact, 1.0)

        return stress_test_score

    async def _calculate_protocol_risk_scores(self, positions: Dict[str, float],
                                            exposure_analysis: CrossProtocolExposure,
                                            concentration_assessment: ConcentrationRiskAssessment,
                                            systemic_assessment: SystemicRiskAssessment) -> List[ProtocolRiskScore]:
        """Calculate individual protocol risk scores"""
        protocol_scores = []
        protocols_config = self.config.get('algorand_protocols', {})

        for protocol, value in positions.items():
            if value <= 0:
                continue

            protocol_config = protocols_config.get(protocol, {})

            # Find protocol in exposure analysis
            exposure_data = next(
                (exp for exp in exposure_analysis.protocol_exposures if exp.protocol_name == protocol),
                None
            )

            # Find protocol in systemic analysis
            systemic_node = next(
                (node for node in systemic_assessment.network_nodes if node.protocol_name == protocol),
                None
            )

            # Calculate individual risk components
            exposure_risk = exposure_data.concentration_risk_score if exposure_data else 0.5
            concentration_risk = self._calculate_individual_concentration_risk(protocol, positions)
            systemic_risk = systemic_node.failure_probability if systemic_node else 0.3
            liquidity_risk = exposure_data.liquidity_risk_score if exposure_data else 0.5
            governance_risk = self._calculate_governance_risk(protocol_config)

            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_protocol_risk(
                exposure_risk, concentration_risk, systemic_risk, liquidity_risk, governance_risk
            )

            # Determine risk tier
            risk_tier = self._determine_protocol_risk_tier(overall_risk_score)

            # Calculate confidence level
            confidence_level = self._calculate_protocol_confidence(protocol_config, exposure_data is not None)

            protocol_score = ProtocolRiskScore(
                protocol_name=protocol,
                category=protocol_config.get('category', 'unknown'),
                exposure_risk=exposure_risk,
                concentration_risk=concentration_risk,
                systemic_risk=systemic_risk,
                liquidity_risk=liquidity_risk,
                governance_risk=governance_risk,
                overall_risk_score=overall_risk_score,
                risk_tier=risk_tier,
                confidence_level=confidence_level
            )

            protocol_scores.append(protocol_score)

        return protocol_scores

    def _calculate_individual_concentration_risk(self, protocol: str, positions: Dict[str, float]) -> float:
        """Calculate concentration risk for individual protocol"""
        total_value = sum(positions.values())
        protocol_value = positions.get(protocol, 0)

        if total_value == 0:
            return 0

        concentration_percentage = protocol_value / total_value
        concentration_threshold = self.config.get('concentration_thresholds', {}).get('single_protocol_max', 0.4)

        # Risk increases exponentially above threshold
        if concentration_percentage <= concentration_threshold:
            return concentration_percentage / concentration_threshold * 0.5
        else:
            excess = concentration_percentage - concentration_threshold
            return 0.5 + (excess / (1 - concentration_threshold)) * 0.5

    def _calculate_governance_risk(self, protocol_config: Dict) -> float:
        """Calculate governance risk for protocol"""
        governance_concentration = protocol_config.get('governance_concentration', 0.5)
        audit_status = protocol_config.get('audit_status', 'none')

        # Base risk from governance concentration
        base_risk = governance_concentration

        # Adjust for audit status
        audit_adjustments = {
            'audited': 0.8,      # 20% risk reduction
            'partial': 1.1,      # 10% risk increase
            'outdated': 1.3,     # 30% risk increase
            'none': 1.5          # 50% risk increase
        }
        audit_multiplier = audit_adjustments.get(audit_status, 1.5)

        governance_risk = base_risk * audit_multiplier

        return min(governance_risk, 1.0)

    def _calculate_overall_protocol_risk(self, exposure_risk: float, concentration_risk: float,
                                       systemic_risk: float, liquidity_risk: float,
                                       governance_risk: float) -> float:
        """Calculate overall protocol risk score"""
        weights = self.config.get('protocol_risk_weights', {
            'exposure_weight': 0.25,
            'concentration_weight': 0.2,
            'systemic_weight': 0.25,
            'liquidity_weight': 0.15,
            'governance_weight': 0.15
        })

        overall_risk = (
            exposure_risk * weights.get('exposure_weight', 0.25) +
            concentration_risk * weights.get('concentration_weight', 0.2) +
            systemic_risk * weights.get('systemic_weight', 0.25) +
            liquidity_risk * weights.get('liquidity_weight', 0.15) +
            governance_risk * weights.get('governance_weight', 0.15)
        )

        return min(overall_risk, 1.0)

    def _determine_protocol_risk_tier(self, risk_score: float) -> str:
        """Determine protocol risk tier"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MODERATE"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    def _calculate_protocol_confidence(self, protocol_config: Dict, has_exposure_data: bool) -> float:
        """Calculate confidence level for protocol risk assessment"""
        base_confidence = 0.7

        # Adjust for data availability
        if has_exposure_data:
            data_adjustment = 1.0
        else:
            data_adjustment = 0.8

        # Adjust for audit status
        audit_status = protocol_config.get('audit_status', 'none')
        audit_confidence = {
            'audited': 1.0,
            'partial': 0.9,
            'outdated': 0.8,
            'none': 0.6
        }.get(audit_status, 0.6)

        # Adjust for risk tier
        risk_tier = protocol_config.get('risk_tier', 'tier_3')
        tier_confidence = {
            'tier_1': 1.0,
            'tier_2': 0.9,
            'tier_3': 0.7
        }.get(risk_tier, 0.7)

        confidence = base_confidence * data_adjustment * audit_confidence * tier_confidence

        return min(confidence, 1.0)

    def _generate_risk_alerts(self, portfolio_metrics: PortfolioRiskMetrics,
                            protocol_scores: List[ProtocolRiskScore],
                            exposure_analysis: CrossProtocolExposure,
                            concentration_assessment: ConcentrationRiskAssessment,
                            systemic_assessment: SystemicRiskAssessment) -> List[RiskAlert]:
        """Generate comprehensive risk alerts"""
        alerts = []
        thresholds = self.config.get('alert_thresholds', {})

        # Portfolio-level alerts
        if portfolio_metrics.concentration_ratio > thresholds.get('high_concentration_warning', 0.35):
            alerts.append(RiskAlert(
                alert_type='concentration',
                severity='HIGH',
                protocol=None,
                category=None,
                message=f"High portfolio concentration detected (HHI: {portfolio_metrics.concentration_ratio:.2f})",
                threshold_exceeded=thresholds.get('high_concentration_warning', 0.35),
                current_value=portfolio_metrics.concentration_ratio,
                recommended_action="Diversify across more protocols and categories",
                urgency_score=0.8
            ))

        if portfolio_metrics.systemic_vulnerability > thresholds.get('systemic_risk_warning', 0.6):
            alerts.append(RiskAlert(
                alert_type='systemic',
                severity='HIGH',
                protocol=None,
                category=None,
                message=f"High systemic vulnerability detected ({portfolio_metrics.systemic_vulnerability:.2f})",
                threshold_exceeded=thresholds.get('systemic_risk_warning', 0.6),
                current_value=portfolio_metrics.systemic_vulnerability,
                recommended_action="Reduce exposure to highly correlated protocols",
                urgency_score=0.9
            ))

        # Protocol-level alerts
        for score in protocol_scores:
            if score.overall_risk_score > 0.7:
                alerts.append(RiskAlert(
                    alert_type='protocol_risk',
                    severity='HIGH' if score.overall_risk_score > 0.8 else 'MEDIUM',
                    protocol=score.protocol_name,
                    category=score.category,
                    message=f"High risk detected in {score.protocol_name} (risk score: {score.overall_risk_score:.2f})",
                    threshold_exceeded=0.7,
                    current_value=score.overall_risk_score,
                    recommended_action=f"Consider reducing exposure to {score.protocol_name}",
                    urgency_score=score.overall_risk_score
                ))

        # Liquidity alerts
        if portfolio_metrics.liquidity_coverage_ratio < 0.5:
            alerts.append(RiskAlert(
                alert_type='liquidity',
                severity='MEDIUM',
                protocol=None,
                category=None,
                message=f"Low liquidity coverage ratio ({portfolio_metrics.liquidity_coverage_ratio:.2f})",
                threshold_exceeded=0.5,
                current_value=portfolio_metrics.liquidity_coverage_ratio,
                recommended_action="Increase exposure to high-liquidity protocols",
                urgency_score=0.6
            ))

        # Diversification alerts
        if portfolio_metrics.category_count < 3:
            alerts.append(RiskAlert(
                alert_type='diversification',
                severity='MEDIUM',
                protocol=None,
                category=None,
                message=f"Limited category diversification ({portfolio_metrics.category_count} categories)",
                threshold_exceeded=3,
                current_value=portfolio_metrics.category_count,
                recommended_action="Add exposure to different protocol categories",
                urgency_score=0.5
            ))

        # Sort alerts by urgency
        alerts.sort(key=lambda x: x.urgency_score, reverse=True)

        return alerts

    def _calculate_overall_portfolio_score(self, portfolio_metrics: PortfolioRiskMetrics,
                                         protocol_scores: List[ProtocolRiskScore],
                                         concentration_assessment: ConcentrationRiskAssessment,
                                         systemic_assessment: SystemicRiskAssessment) -> float:
        """Calculate overall portfolio risk score"""
        # Portfolio structure score (lower concentration = better)
        structure_score = 1.0 - portfolio_metrics.concentration_ratio

        # Diversification score
        diversification_score = portfolio_metrics.effective_diversification

        # Systemic risk score (inverted - lower systemic risk = better)
        systemic_score = 1.0 - portfolio_metrics.systemic_vulnerability

        # Protocol quality score (average of individual protocol scores, inverted)
        if protocol_scores:
            avg_protocol_risk = sum(score.overall_risk_score for score in protocol_scores) / len(protocol_scores)
            protocol_quality_score = 1.0 - avg_protocol_risk
        else:
            protocol_quality_score = 0.5

        # Liquidity score
        liquidity_score = portfolio_metrics.liquidity_coverage_ratio

        # Stress test score
        stress_score = portfolio_metrics.stress_test_score

        # Weighted combination
        weights = {
            'structure': 0.2,
            'diversification': 0.2,
            'systemic': 0.25,
            'protocol_quality': 0.2,
            'liquidity': 0.1,
            'stress': 0.05
        }

        overall_score = (
            structure_score * weights['structure'] +
            diversification_score * weights['diversification'] +
            systemic_score * weights['systemic'] +
            protocol_quality_score * weights['protocol_quality'] +
            liquidity_score * weights['liquidity'] +
            stress_score * weights['stress']
        )

        return min(overall_score, 1.0)

    def _determine_portfolio_risk_level(self, portfolio_score: float, alerts: List[RiskAlert]) -> str:
        """Determine overall portfolio risk level"""
        # Base level from portfolio score
        if portfolio_score >= 0.8:
            base_level = "EXCELLENT"
        elif portfolio_score >= 0.65:
            base_level = "GOOD"
        elif portfolio_score >= 0.5:
            base_level = "MODERATE"
        elif portfolio_score >= 0.3:
            base_level = "POOR"
        else:
            base_level = "CRITICAL"

        # Adjust for high-severity alerts
        high_severity_alerts = [alert for alert in alerts if alert.severity == 'HIGH']
        if len(high_severity_alerts) >= 2:
            if base_level in ["EXCELLENT", "GOOD"]:
                return "MODERATE"
            elif base_level == "MODERATE":
                return "POOR"
            else:
                return "CRITICAL"

        return base_level

    def _calculate_confidence_score(self, exposure_analysis: CrossProtocolExposure,
                                  concentration_assessment: ConcentrationRiskAssessment,
                                  systemic_assessment: SystemicRiskAssessment) -> float:
        """Calculate confidence score for the overall assessment"""
        # Base confidence from data availability
        base_confidence = 0.75

        # Adjust for number of protocols analyzed
        protocol_count = len(exposure_analysis.protocol_exposures)
        if protocol_count >= 3:
            protocol_confidence = 1.0
        elif protocol_count >= 2:
            protocol_confidence = 0.9
        else:
            protocol_confidence = 0.7

        # Adjust for systemic analysis completeness
        systemic_confidence = 1.0 if len(systemic_assessment.network_nodes) >= 3 else 0.8

        # Adjust for market condition volatility (simplified)
        market_confidence = 0.9  # Assume normal market conditions

        confidence = base_confidence * protocol_confidence * systemic_confidence * market_confidence

        return min(confidence, 1.0)

    def _generate_comprehensive_recommendations(self, portfolio_metrics: PortfolioRiskMetrics,
                                              protocol_scores: List[ProtocolRiskScore],
                                              alerts: List[RiskAlert],
                                              portfolio_score: float) -> List[str]:
        """Generate comprehensive risk management recommendations"""
        recommendations = []

        # High-priority recommendations from alerts
        high_priority_alerts = [alert for alert in alerts if alert.urgency_score > 0.7]
        for alert in high_priority_alerts[:3]:  # Top 3 urgent alerts
            recommendations.append(f"URGENT: {alert.recommended_action}")

        # Portfolio structure recommendations
        if portfolio_metrics.concentration_ratio > 0.4:
            recommendations.append("Reduce concentration: No single protocol should exceed 30% of portfolio")

        if portfolio_metrics.category_count < 3:
            missing_categories = {'lending', 'dex', 'staking'} - {score.category for score in protocol_scores}
            if missing_categories:
                recommendations.append(f"Add exposure to {', '.join(missing_categories)} protocols for better diversification")

        # Protocol-specific recommendations
        high_risk_protocols = [score for score in protocol_scores if score.overall_risk_score > 0.6]
        for score in high_risk_protocols[:2]:  # Top 2 riskiest protocols
            if score.governance_risk > 0.7:
                recommendations.append(f"Monitor {score.protocol_name} governance developments closely")
            if score.liquidity_risk > 0.7:
                recommendations.append(f"Consider reducing {score.protocol_name} exposure due to liquidity concerns")

        # Systemic risk recommendations
        if portfolio_metrics.systemic_vulnerability > 0.6:
            recommendations.append("Implement portfolio hedging strategies to reduce systemic risk exposure")

        # Positive reinforcement for good practices
        if portfolio_score > 0.7 and not high_priority_alerts:
            recommendations.append("Well-diversified portfolio! Continue monitoring and periodic rebalancing")

        # Liquidity recommendations
        if portfolio_metrics.liquidity_coverage_ratio < 0.6:
            recommendations.append("Increase exposure to tier-1 protocols with high liquidity")

        return recommendations[:6]  # Limit to top 6 recommendations

    def _determine_next_review_date(self, risk_level: str, alerts: List[RiskAlert]) -> datetime:
        """Determine when the next risk review should occur"""
        base_days = {
            "CRITICAL": 1,
            "POOR": 3,
            "MODERATE": 7,
            "GOOD": 14,
            "EXCELLENT": 30
        }

        days = base_days.get(risk_level, 7)

        # Adjust for high-severity alerts
        high_severity_count = len([alert for alert in alerts if alert.severity == 'HIGH'])
        if high_severity_count > 0:
            days = max(1, days // 2)

        return datetime.now() + timedelta(days=days)

    async def export_assessment_report(self, assessment: ComprehensiveRiskAssessment,
                                     output_path: Optional[str] = None) -> str:
        """Export comprehensive assessment report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"defi_risk_assessment_{timestamp}.json"

        # Convert assessment to dict for JSON serialization
        report_data = {
            'assessment_metadata': {
                'timestamp': assessment.timestamp.isoformat(),
                'overall_score': assessment.overall_portfolio_score,
                'risk_level': assessment.risk_level,
                'confidence_score': assessment.confidence_score,
                'next_review_date': assessment.next_review_date.isoformat()
            },
            'portfolio_metrics': asdict(assessment.portfolio_metrics),
            'protocol_scores': [asdict(score) for score in assessment.protocol_scores],
            'risk_alerts': [asdict(alert) for alert in assessment.risk_alerts],
            'recommendations': assessment.recommendations,
            'exposure_summary': {
                'total_exposure_usd': assessment.exposure_analysis.total_exposure_usd,
                'protocol_count': len(assessment.exposure_analysis.protocol_exposures),
                'concentration_risk_score': assessment.exposure_analysis.concentration_risk_score,
                'diversification_score': assessment.exposure_analysis.diversification_score,
                'systemic_risk_score': assessment.exposure_analysis.systemic_risk_score
            },
            'concentration_summary': {
                'herfindahl_index': assessment.concentration_assessment.concentration_metrics.herfindahl_index,
                'max_exposure_percentage': assessment.concentration_assessment.concentration_metrics.max_exposure_percentage,
                'effective_protocols': assessment.concentration_assessment.concentration_metrics.effective_protocols,
                'diversification_score': assessment.concentration_assessment.diversification_analysis.diversification_score
            },
            'systemic_summary': {
                'systemic_risk_score': assessment.systemic_assessment.systemic_risk_score,
                'network_stability_score': assessment.systemic_assessment.network_stability_score,
                'interconnectedness_index': assessment.systemic_assessment.interconnectedness_index,
                'ecosystem_health': assessment.systemic_assessment.overall_ecosystem_health,
                'cascade_scenario_count': len(assessment.systemic_assessment.cascade_scenarios)
            }
        }

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Risk assessment report exported to: {output_path}")
        return output_path

# Example usage
async def main():
    """Example usage of the DeFi protocol risk engine"""
    engine = DeFiProtocolRiskEngine()

    # Example portfolio with various risk profiles
    user_positions = {
        'algofi': 60000,        # Large position in tier-1 protocol
        'folks_finance': 25000,  # Medium position in tier-1 protocol
        'tinyman': 10000,       # Small position in DEX
        'pact': 5000            # Small position in smaller DEX
    }

    # Perform comprehensive risk assessment
    assessment = await engine.assess_portfolio_risk(user_positions)

    print(f"\n=== DeFi Protocol Risk Assessment ===")
    print(f"Overall Portfolio Score: {assessment.overall_portfolio_score:.2f}")
    print(f"Risk Level: {assessment.risk_level}")
    print(f"Confidence Score: {assessment.confidence_score:.2f}")
    print(f"Next Review Date: {assessment.next_review_date.strftime('%Y-%m-%d')}")

    print(f"\n=== Portfolio Metrics ===")
    metrics = assessment.portfolio_metrics
    print(f"Total Exposure: ${metrics.total_exposure_usd:,.2f}")
    print(f"Protocol Count: {metrics.protocol_count}")
    print(f"Category Count: {metrics.category_count}")
    print(f"Effective Diversification: {metrics.effective_diversification:.2f}")
    print(f"Concentration Ratio: {metrics.concentration_ratio:.2f}")
    print(f"Systemic Vulnerability: {metrics.systemic_vulnerability:.2f}")
    print(f"Liquidity Coverage: {metrics.liquidity_coverage_ratio:.2f}")

    print(f"\n=== Protocol Risk Scores ===")
    for score in assessment.protocol_scores:
        print(f"{score.protocol_name} ({score.category}):")
        print(f"  Overall Risk: {score.overall_risk_score:.2f} ({score.risk_tier})")
        print(f"  Exposure Risk: {score.exposure_risk:.2f}")
        print(f"  Concentration Risk: {score.concentration_risk:.2f}")
        print(f"  Systemic Risk: {score.systemic_risk:.2f}")
        print(f"  Liquidity Risk: {score.liquidity_risk:.2f}")
        print(f"  Governance Risk: {score.governance_risk:.2f}")

    print(f"\n=== Risk Alerts ===")
    for alert in assessment.risk_alerts:
        severity_emoji = "🚨" if alert.severity == "HIGH" else "⚠️"
        print(f"{severity_emoji} {alert.severity}: {alert.message}")
        print(f"   Action: {alert.recommended_action}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(assessment.recommendations, 1):
        print(f"{i}. {rec}")

    # Export report
    report_path = await engine.export_assessment_report(assessment)
    print(f"\n=== Report Exported ===")
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())