"""
Master Collateral Intelligence System

Integrates all collateral intelligence components into a unified system for
comprehensive collateral assessment and decision support.
"""

import asyncio
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
import json

from .smart_collateral import SmartCollateralAnalyzer, SmartCollateralAnalysis
from .liquidation_predictor import LiquidationPredictor, LiquidationPredictionAnalysis

@dataclass
class CollateralIntelligenceReport:
    """Comprehensive collateral intelligence report"""
    address: str
    analysis_timestamp: datetime

    # Core analyses
    smart_collateral_analysis: SmartCollateralAnalysis
    liquidation_prediction_analysis: LiquidationPredictionAnalysis

    # Integrated insights
    overall_collateral_score: float
    risk_adjusted_value: float
    liquidation_adjusted_value: float
    recommended_loan_to_value: float

    # Decision support
    approval_recommendation: str  # approve, conditional_approve, reject
    required_conditions: List[str]
    monitoring_requirements: List[str]

    # Risk assessment
    integrated_risk_score: float
    confidence_level: float

    # Recommendations
    optimization_recommendations: List[str]
    risk_mitigation_strategies: List[str]

class CollateralIntelligenceEngine:
    """Master collateral intelligence system"""

    def __init__(self, config_path: str = None):
        """Initialize the collateral intelligence engine"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize component analyzers
        self.smart_collateral_analyzer = SmartCollateralAnalyzer(config_path)
        self.liquidation_predictor = LiquidationPredictor(config_path)

        # Load decision thresholds
        self.decision_thresholds = self._load_decision_thresholds()

        self.logger.info("Collateral Intelligence Engine initialized successfully")

    def _load_decision_thresholds(self) -> Dict[str, float]:
        """Load decision-making thresholds"""
        return {
            'min_collateral_score': 0.6,
            'max_liquidation_risk': 0.3,
            'min_confidence_level': 0.7,
            'conservative_ltv': 0.6,
            'standard_ltv': 0.75,
            'aggressive_ltv': 0.85,
            'min_risk_adjusted_value': 0.8
        }

    async def analyze_collateral_portfolio(self,
                                         collateral_portfolio: Dict[str, Any],
                                         borrower_profile: Dict[str, Any] = None,
                                         loan_request: Dict[str, Any] = None) -> CollateralIntelligenceReport:
        """
        Comprehensive collateral intelligence analysis

        Args:
            collateral_portfolio: Portfolio of collateral assets
            borrower_profile: Borrower behavior and risk profile
            loan_request: Details of the loan request

        Returns:
            CollateralIntelligenceReport with comprehensive assessment
        """
        try:
            self.logger.info("Starting comprehensive collateral intelligence analysis")

            # Run parallel analyses
            smart_analysis_task = self.smart_collateral_analyzer.analyze_smart_collateral(
                collateral_portfolio, borrower_profile
            )

            liquidation_analysis_task = self.liquidation_predictor.predict_liquidation_risk(
                collateral_portfolio.get('assets', []),
                borrower_profile,
                collateral_portfolio.get('market_conditions', {})
            )

            # Wait for both analyses to complete
            smart_analysis, liquidation_analysis = await asyncio.gather(
                smart_analysis_task,
                liquidation_analysis_task
            )

            # Integrate analyses and generate comprehensive report
            intelligence_report = await self._generate_intelligence_report(
                smart_analysis,
                liquidation_analysis,
                borrower_profile,
                loan_request
            )

            self.logger.info("Collateral intelligence analysis completed successfully")
            return intelligence_report

        except Exception as e:
            self.logger.error(f"Error in collateral intelligence analysis: {str(e)}")
            raise

    async def _generate_intelligence_report(self,
                                          smart_analysis: SmartCollateralAnalysis,
                                          liquidation_analysis: LiquidationPredictionAnalysis,
                                          borrower_profile: Dict[str, Any],
                                          loan_request: Dict[str, Any]) -> CollateralIntelligenceReport:
        """Generate integrated intelligence report"""

        # Calculate integrated scores
        overall_collateral_score = self._calculate_overall_collateral_score(
            smart_analysis, liquidation_analysis
        )

        # Calculate risk-adjusted values
        risk_adjusted_value = self._calculate_risk_adjusted_value(
            smart_analysis, liquidation_analysis
        )

        liquidation_adjusted_value = self._calculate_liquidation_adjusted_value(
            smart_analysis, liquidation_analysis
        )

        # Determine recommended LTV
        recommended_ltv = self._calculate_recommended_ltv(
            smart_analysis, liquidation_analysis, borrower_profile
        )

        # Generate approval recommendation
        approval_recommendation, required_conditions = self._generate_approval_recommendation(
            overall_collateral_score,
            liquidation_analysis.portfolio_risk.overall_liquidation_probability,
            smart_analysis.confidence_level,
            loan_request
        )

        # Generate monitoring requirements
        monitoring_requirements = self._generate_monitoring_requirements(
            smart_analysis, liquidation_analysis
        )

        # Calculate integrated risk score
        integrated_risk_score = self._calculate_integrated_risk_score(
            smart_analysis, liquidation_analysis
        )

        # Calculate overall confidence
        confidence_level = self._calculate_overall_confidence(
            smart_analysis, liquidation_analysis
        )

        # Combine optimization recommendations
        optimization_recommendations = self._combine_optimization_recommendations(
            smart_analysis, liquidation_analysis
        )

        # Combine risk mitigation strategies
        risk_mitigation_strategies = self._combine_risk_mitigation_strategies(
            smart_analysis, liquidation_analysis
        )

        return CollateralIntelligenceReport(
            address=smart_analysis.address,
            analysis_timestamp=datetime.now(),
            smart_collateral_analysis=smart_analysis,
            liquidation_prediction_analysis=liquidation_analysis,
            overall_collateral_score=overall_collateral_score,
            risk_adjusted_value=risk_adjusted_value,
            liquidation_adjusted_value=liquidation_adjusted_value,
            recommended_loan_to_value=recommended_ltv,
            approval_recommendation=approval_recommendation,
            required_conditions=required_conditions,
            monitoring_requirements=monitoring_requirements,
            integrated_risk_score=integrated_risk_score,
            confidence_level=confidence_level,
            optimization_recommendations=optimization_recommendations,
            risk_mitigation_strategies=risk_mitigation_strategies
        )

    def _calculate_overall_collateral_score(self,
                                          smart_analysis: SmartCollateralAnalysis,
                                          liquidation_analysis: LiquidationPredictionAnalysis) -> float:
        """Calculate overall collateral score integrating all factors"""

        # Weight different components
        weights = {
            'quality': 0.4,
            'liquidation_risk': 0.3,
            'diversification': 0.2,
            'liquidity': 0.1
        }

        # Quality score from smart analysis
        quality_score = smart_analysis.quality_metrics.overall_quality_score

        # Liquidation risk score (inverted - lower risk = higher score)
        liquidation_risk_score = 1 - liquidation_analysis.portfolio_risk.overall_liquidation_probability

        # Diversification score (based on number of assets and correlations)
        diversification_score = self._calculate_diversification_score(smart_analysis)

        # Liquidity score
        liquidity_score = smart_analysis.quality_metrics.liquidity_score

        # Weighted combination
        overall_score = (
            quality_score * weights['quality'] +
            liquidation_risk_score * weights['liquidation_risk'] +
            diversification_score * weights['diversification'] +
            liquidity_score * weights['liquidity']
        )

        return round(overall_score, 3)

    def _calculate_diversification_score(self, smart_analysis: SmartCollateralAnalysis) -> float:
        """Calculate portfolio diversification score"""
        assets = smart_analysis.collateral_assets

        if len(assets) <= 1:
            return 0.2  # Poor diversification

        # Number of assets factor
        asset_count_score = min(len(assets) / 5, 1.0)  # 5 assets = max score

        # Correlation factor
        correlations = [abs(asset.correlation_btc) for asset in assets]
        avg_correlation = sum(correlations) / len(correlations) if correlations else 0.5
        correlation_score = 1 - avg_correlation  # Lower correlation = better

        # Asset type diversity (simplified)
        asset_types = set()
        for asset in assets:
            if asset.symbol in ['USDC', 'USDT', 'STBL']:
                asset_types.add('stablecoin')
            elif asset.symbol in ['BTC', 'ETH', 'ALGO']:
                asset_types.add('major')
            else:
                asset_types.add('alt')

        type_diversity_score = min(len(asset_types) / 3, 1.0)

        # Combined diversification score
        diversification_score = (
            asset_count_score * 0.4 +
            correlation_score * 0.4 +
            type_diversity_score * 0.2
        )

        return round(diversification_score, 3)

    def _calculate_risk_adjusted_value(self,
                                     smart_analysis: SmartCollateralAnalysis,
                                     liquidation_analysis: LiquidationPredictionAnalysis) -> float:
        """Calculate risk-adjusted collateral value"""

        total_value = smart_analysis.total_collateral_value
        if total_value == 0:
            return 0.0

        # Apply quality adjustment
        quality_adjustment = smart_analysis.quality_metrics.overall_quality_score

        # Apply liquidation risk adjustment
        liquidation_adjustment = 1 - (liquidation_analysis.portfolio_risk.overall_liquidation_probability * 0.5)

        # Apply volatility adjustment
        volatility_adjustment = smart_analysis.quality_metrics.volatility_score

        # Combined adjustment
        total_adjustment = (
            quality_adjustment * 0.4 +
            liquidation_adjustment * 0.4 +
            volatility_adjustment * 0.2
        )

        risk_adjusted_value = total_value * total_adjustment

        return round(risk_adjusted_value, 2)

    def _calculate_liquidation_adjusted_value(self,
                                            smart_analysis: SmartCollateralAnalysis,
                                            liquidation_analysis: LiquidationPredictionAnalysis) -> float:
        """Calculate liquidation-adjusted collateral value"""

        total_value = smart_analysis.total_collateral_value
        if total_value == 0:
            return 0.0

        # Expected liquidation value from prediction
        expected_liquidation_value = liquidation_analysis.portfolio_risk.expected_liquidation_value

        # Worst-case liquidation scenario
        worst_case_adjustment = 1 - liquidation_analysis.portfolio_risk.worst_case_scenario_probability

        # Market impact adjustment for liquidation
        market_impact_adjustment = self._calculate_market_impact_adjustment(smart_analysis)

        # Conservative liquidation value estimate
        liquidation_adjusted_value = min(
            total_value * worst_case_adjustment * market_impact_adjustment,
            total_value - expected_liquidation_value
        )

        return round(max(liquidation_adjusted_value, 0), 2)

    def _calculate_market_impact_adjustment(self, smart_analysis: SmartCollateralAnalysis) -> float:
        """Calculate market impact adjustment for liquidation scenarios"""

        # Based on liquidity tiers of assets
        adjustments = {
            'tier_1': 0.95,  # 5% impact for highly liquid assets
            'tier_2': 0.90,  # 10% impact for medium liquid assets
            'tier_3': 0.80,  # 20% impact for low liquid assets
            'tier_4': 0.65   # 35% impact for illiquid assets
        }

        if not smart_analysis.collateral_assets:
            return 0.8  # Conservative default

        # Weighted average based on asset values
        total_value = sum(asset.current_price for asset in smart_analysis.collateral_assets)
        if total_value == 0:
            return 0.8

        weighted_adjustment = sum(
            adjustments.get(asset.liquidity_tier, 0.7) * (asset.current_price / total_value)
            for asset in smart_analysis.collateral_assets
        )

        return round(weighted_adjustment, 3)

    def _calculate_recommended_ltv(self,
                                 smart_analysis: SmartCollateralAnalysis,
                                 liquidation_analysis: LiquidationPredictionAnalysis,
                                 borrower_profile: Dict[str, Any]) -> float:
        """Calculate recommended loan-to-value ratio"""

        base_ltv = self.decision_thresholds['standard_ltv']

        # Quality adjustment
        quality_score = smart_analysis.quality_metrics.overall_quality_score
        quality_adjustment = (quality_score - 0.5) * 0.2  # ±10% adjustment

        # Liquidation risk adjustment
        liquidation_risk = liquidation_analysis.portfolio_risk.overall_liquidation_probability
        risk_adjustment = -liquidation_risk * 0.3  # Up to -30% for high risk

        # Borrower profile adjustment (if available)
        borrower_adjustment = 0.0
        if borrower_profile:
            behavior_score = borrower_profile.get('overall_behavior_score', 0.5)
            sophistication_score = borrower_profile.get('sophistication_score', 0.5)
            borrower_adjustment = (behavior_score + sophistication_score - 1.0) * 0.1

        # Confidence adjustment
        confidence_penalty = (1 - smart_analysis.confidence_level) * 0.1

        # Calculate final LTV
        recommended_ltv = base_ltv + quality_adjustment + risk_adjustment + borrower_adjustment - confidence_penalty

        # Apply bounds
        recommended_ltv = max(0.3, min(recommended_ltv, 0.9))

        return round(recommended_ltv, 3)

    def _generate_approval_recommendation(self,
                                        collateral_score: float,
                                        liquidation_probability: float,
                                        confidence_level: float,
                                        loan_request: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Generate loan approval recommendation"""

        conditions = []

        # Check minimum thresholds
        if collateral_score < self.decision_thresholds['min_collateral_score']:
            return "reject", ["Collateral quality below minimum threshold"]

        if liquidation_probability > self.decision_thresholds['max_liquidation_risk']:
            return "reject", ["Liquidation risk exceeds maximum acceptable level"]

        if confidence_level < self.decision_thresholds['min_confidence_level']:
            conditions.append("Low analysis confidence - additional verification required")

        # Determine approval level
        if (collateral_score >= 0.8 and
            liquidation_probability <= 0.15 and
            confidence_level >= 0.8):
            return "approve", conditions

        elif (collateral_score >= 0.6 and
              liquidation_probability <= 0.3 and
              confidence_level >= 0.7):

            # Add conditions for conditional approval
            if liquidation_probability > 0.2:
                conditions.append("Enhanced monitoring of liquidation risk required")

            if collateral_score < 0.7:
                conditions.append("Periodic collateral quality review required")

            if confidence_level < 0.8:
                conditions.append("Additional data verification recommended")

            return "conditional_approve", conditions

        else:
            return "reject", ["Collateral does not meet minimum risk criteria"]

    def _generate_monitoring_requirements(self,
                                        smart_analysis: SmartCollateralAnalysis,
                                        liquidation_analysis: LiquidationPredictionAnalysis) -> List[str]:
        """Generate monitoring requirements for approved loans"""

        requirements = []

        # High liquidation risk monitoring
        if liquidation_analysis.portfolio_risk.overall_liquidation_probability > 0.2:
            requirements.append("Daily liquidation risk monitoring")
        else:
            requirements.append("Weekly liquidation risk monitoring")

        # Quality degradation monitoring
        if smart_analysis.quality_metrics.overall_quality_score < 0.7:
            requirements.append("Daily collateral quality assessment")

        # Liquidity monitoring
        low_liquidity_assets = [
            asset for asset in smart_analysis.collateral_assets
            if asset.liquidity_tier in ['tier_3', 'tier_4']
        ]
        if low_liquidity_assets:
            requirements.append("Enhanced liquidity monitoring for low-tier assets")

        # Volatility monitoring
        if smart_analysis.quality_metrics.volatility_score < 0.6:
            requirements.append("Real-time volatility spike detection")

        # Correlation monitoring
        if smart_analysis.quality_metrics.correlation_score < 0.5:
            requirements.append("Systemic risk and correlation monitoring")

        # Early warning system
        if liquidation_analysis.portfolio_risk.time_to_liquidation_estimate and \
           liquidation_analysis.portfolio_risk.time_to_liquidation_estimate < 30:
            requirements.append("Immediate alert system for liquidation triggers")

        return requirements

    def _calculate_integrated_risk_score(self,
                                       smart_analysis: SmartCollateralAnalysis,
                                       liquidation_analysis: LiquidationPredictionAnalysis) -> float:
        """Calculate integrated risk score across all factors"""

        risk_components = []

        # Quality risk (inverted)
        quality_risk = 1 - smart_analysis.quality_metrics.overall_quality_score
        risk_components.append(quality_risk * 0.3)

        # Liquidation risk
        liquidation_risk = liquidation_analysis.portfolio_risk.overall_liquidation_probability
        risk_components.append(liquidation_risk * 0.4)

        # Concentration risk
        concentration_risk = 1 - self._calculate_diversification_score(smart_analysis)
        risk_components.append(concentration_risk * 0.2)

        # Liquidity risk
        liquidity_risk = 1 - smart_analysis.quality_metrics.liquidity_score
        risk_components.append(liquidity_risk * 0.1)

        integrated_risk = sum(risk_components)
        return round(integrated_risk, 3)

    def _calculate_overall_confidence(self,
                                    smart_analysis: SmartCollateralAnalysis,
                                    liquidation_analysis: LiquidationPredictionAnalysis) -> float:
        """Calculate overall confidence in the analysis"""

        confidence_factors = [
            smart_analysis.confidence_level,
            liquidation_analysis.confidence_level
        ]

        # Data completeness factor
        data_completeness = len([
            asset for asset in smart_analysis.collateral_assets
            if asset.market_cap > 0 and asset.daily_volume > 0
        ]) / max(len(smart_analysis.collateral_assets), 1)

        confidence_factors.append(data_completeness)

        return round(sum(confidence_factors) / len(confidence_factors), 3)

    def _combine_optimization_recommendations(self,
                                            smart_analysis: SmartCollateralAnalysis,
                                            liquidation_analysis: LiquidationPredictionAnalysis) -> List[str]:
        """Combine optimization recommendations from both analyses"""

        recommendations = []

        # Add smart collateral recommendations
        recommendations.extend(smart_analysis.optimization_recommendations)

        # Add liquidation prediction recommendations
        recommendations.extend(liquidation_analysis.risk_mitigation_strategies)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        # Add integrated recommendations
        if (smart_analysis.quality_metrics.overall_quality_score < 0.6 and
            liquidation_analysis.portfolio_risk.overall_liquidation_probability > 0.3):
            unique_recommendations.append(
                "PRIORITY: Comprehensive portfolio restructuring recommended"
            )

        return unique_recommendations

    def _combine_risk_mitigation_strategies(self,
                                          smart_analysis: SmartCollateralAnalysis,
                                          liquidation_analysis: LiquidationPredictionAnalysis) -> List[str]:
        """Combine risk mitigation strategies from both analyses"""

        strategies = []

        # Add risk warnings as mitigation strategies
        for warning in smart_analysis.risk_warnings:
            if "CRITICAL" in warning or "HIGH RISK" in warning:
                strategies.append(f"URGENT MITIGATION: {warning}")

        # Add liquidation mitigation strategies
        strategies.extend(liquidation_analysis.risk_mitigation_strategies)

        # Add integrated strategies
        if (liquidation_analysis.portfolio_risk.cascade_risk_probability > 0.4):
            strategies.append("Implement cascade liquidation protection mechanisms")

        if (smart_analysis.quality_metrics.liquidity_score < 0.4 and
            liquidation_analysis.portfolio_risk.overall_liquidation_probability > 0.2):
            strategies.append("Emergency liquidity buffer recommended")

        return strategies

    async def get_historical_performance(self, address: str, days: int = 30) -> Dict[str, Any]:
        """Get historical performance of collateral intelligence predictions"""
        try:
            # This would query historical data and compare predictions with actual outcomes
            # For now, return placeholder data

            return {
                'prediction_accuracy': 0.85,
                'false_positive_rate': 0.12,
                'false_negative_rate': 0.08,
                'avg_confidence_level': 0.78,
                'total_predictions': 45,
                'successful_predictions': 38
            }

        except Exception as e:
            self.logger.error(f"Error retrieving historical performance: {str(e)}")
            return {}

    def export_report(self, report: CollateralIntelligenceReport, format: str = 'json') -> str:
        """Export intelligence report in specified format"""
        try:
            if format.lower() == 'json':
                return json.dumps(asdict(report), indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            return "{}"