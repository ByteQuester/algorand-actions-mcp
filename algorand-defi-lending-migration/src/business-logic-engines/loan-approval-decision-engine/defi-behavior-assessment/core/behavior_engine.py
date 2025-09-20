"""
Combined Behavioral Risk Assessment Engine

Master engine that integrates all DeFi behavior analysis components for
comprehensive behavioral risk assessment in loan approval decisions.
"""

import asyncio
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
import json

from .protocol_analyzer import ProtocolAnalyzer, CrossProtocolAnalysis
from .behavior_patterns import BehaviorPatternAnalyzer, BehaviorPatternAnalysis
from .liquidity_behavior import LiquidityBehaviorAnalyzer, LiquidityBehaviorAnalysis

@dataclass
class BehavioralRiskAssessment:
    """Comprehensive behavioral risk assessment"""
    address: str
    analysis_timestamp: datetime

    # Core analyses
    protocol_analysis: CrossProtocolAnalysis
    behavior_pattern_analysis: BehaviorPatternAnalysis
    liquidity_behavior_analysis: LiquidityBehaviorAnalysis

    # Integrated scores
    overall_behavior_score: float
    sophistication_score: float
    risk_management_score: float
    defi_experience_score: float

    # Decision factors
    behavioral_risk_level: str  # low, medium, high, very_high
    loan_recommendation: str    # approve, conditional, monitor, reject
    interest_rate_adjustment: float  # basis points adjustment

    # Behavioral insights
    strengths: List[str]
    weaknesses: List[str]
    red_flags: List[str]
    growth_indicators: List[str]

    # Recommendations
    risk_mitigation_recommendations: List[str]
    monitoring_requirements: List[str]

    # Confidence metrics
    analysis_confidence: float
    data_quality_score: float

class BehaviorEngine:
    """Master behavioral risk assessment engine"""

    def __init__(self, config_path: str = None):
        """Initialize the behavior engine"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize component analyzers
        self.protocol_analyzer = ProtocolAnalyzer(config_path)
        self.behavior_pattern_analyzer = BehaviorPatternAnalyzer(config_path)
        self.liquidity_behavior_analyzer = LiquidityBehaviorAnalyzer(config_path)

        # Load risk assessment parameters
        self.risk_thresholds = self.config['risk_thresholds']
        self.scoring_algorithms = self.config['scoring_algorithms']

        self.logger.info("Behavior Engine initialized successfully")

    async def assess_behavioral_risk(self,
                                   address: str,
                                   analysis_period_days: int = 365,
                                   loan_request: Dict[str, Any] = None) -> BehavioralRiskAssessment:
        """
        Comprehensive behavioral risk assessment

        Args:
            address: Algorand address to analyze
            analysis_period_days: Period for historical analysis
            loan_request: Details of loan request

        Returns:
            BehavioralRiskAssessment with comprehensive evaluation
        """
        try:
            self.logger.info(f"Starting behavioral risk assessment for {address}")

            # Run parallel analyses
            protocol_analysis_task = self.protocol_analyzer.analyze_cross_protocol_activity(
                address, analysis_period_days
            )

            # For behavior pattern analysis, we need protocol activities first
            protocol_analysis = await protocol_analysis_task

            # Now run remaining analyses in parallel
            behavior_analysis_task = self.behavior_pattern_analyzer.analyze_behavior_patterns(
                {address: protocol_analysis},
                {},  # market_data placeholder
                analysis_period_days
            )

            liquidity_analysis_task = self.liquidity_behavior_analyzer.analyze_liquidity_behavior(
                {address: protocol_analysis},
                {},  # market_data placeholder
                analysis_period_days
            )

            behavior_analysis, liquidity_analysis = await asyncio.gather(
                behavior_analysis_task,
                liquidity_analysis_task
            )

            # Generate comprehensive assessment
            assessment = await self._generate_behavioral_assessment(
                protocol_analysis,
                behavior_analysis,
                liquidity_analysis,
                loan_request
            )

            self.logger.info(f"Behavioral risk assessment completed for {address}")
            return assessment

        except Exception as e:
            self.logger.error(f"Error in behavioral risk assessment: {str(e)}")
            raise

    async def _generate_behavioral_assessment(self,
                                            protocol_analysis: CrossProtocolAnalysis,
                                            behavior_analysis: BehaviorPatternAnalysis,
                                            liquidity_analysis: LiquidityBehaviorAnalysis,
                                            loan_request: Dict[str, Any]) -> BehavioralRiskAssessment:
        """Generate integrated behavioral assessment"""

        # Calculate integrated scores
        overall_behavior_score = self._calculate_overall_behavior_score(
            protocol_analysis, behavior_analysis, liquidity_analysis
        )

        sophistication_score = self._calculate_sophistication_score(
            protocol_analysis, behavior_analysis, liquidity_analysis
        )

        risk_management_score = self._calculate_risk_management_score(
            behavior_analysis, liquidity_analysis
        )

        defi_experience_score = self._calculate_defi_experience_score(
            protocol_analysis, behavior_analysis
        )

        # Determine behavioral risk level
        behavioral_risk_level = self._determine_behavioral_risk_level(
            overall_behavior_score, risk_management_score, behavior_analysis
        )

        # Generate loan recommendation
        loan_recommendation = self._generate_loan_recommendation(
            behavioral_risk_level, overall_behavior_score, loan_request
        )

        # Calculate interest rate adjustment
        interest_rate_adjustment = self._calculate_interest_rate_adjustment(
            behavioral_risk_level, sophistication_score, risk_management_score
        )

        # Extract behavioral insights
        strengths = self._extract_behavioral_strengths(
            behavior_analysis, liquidity_analysis, protocol_analysis
        )

        weaknesses = self._extract_behavioral_weaknesses(
            behavior_analysis, liquidity_analysis, protocol_analysis
        )

        red_flags = self._extract_red_flags(
            behavior_analysis, liquidity_analysis, protocol_analysis
        )

        growth_indicators = self._extract_growth_indicators(
            protocol_analysis, behavior_analysis
        )

        # Generate recommendations
        risk_mitigation_recommendations = self._generate_risk_mitigation_recommendations(
            behavioral_risk_level, weaknesses, red_flags
        )

        monitoring_requirements = self._generate_monitoring_requirements(
            behavioral_risk_level, red_flags, loan_request
        )

        # Calculate confidence metrics
        analysis_confidence = self._calculate_analysis_confidence(
            protocol_analysis, behavior_analysis, liquidity_analysis
        )

        data_quality_score = self._calculate_data_quality_score(
            protocol_analysis, behavior_analysis, liquidity_analysis
        )

        return BehavioralRiskAssessment(
            address=protocol_analysis.address,
            analysis_timestamp=datetime.now(),
            protocol_analysis=protocol_analysis,
            behavior_pattern_analysis=behavior_analysis,
            liquidity_behavior_analysis=liquidity_analysis,
            overall_behavior_score=overall_behavior_score,
            sophistication_score=sophistication_score,
            risk_management_score=risk_management_score,
            defi_experience_score=defi_experience_score,
            behavioral_risk_level=behavioral_risk_level,
            loan_recommendation=loan_recommendation,
            interest_rate_adjustment=interest_rate_adjustment,
            strengths=strengths,
            weaknesses=weaknesses,
            red_flags=red_flags,
            growth_indicators=growth_indicators,
            risk_mitigation_recommendations=risk_mitigation_recommendations,
            monitoring_requirements=monitoring_requirements,
            analysis_confidence=analysis_confidence,
            data_quality_score=data_quality_score
        )

    def _calculate_overall_behavior_score(self,
                                        protocol_analysis: CrossProtocolAnalysis,
                                        behavior_analysis: BehaviorPatternAnalysis,
                                        liquidity_analysis: LiquidityBehaviorAnalysis) -> float:
        """Calculate overall behavioral score"""

        # Component weights
        weights = {
            'sophistication': 0.25,
            'risk_management': 0.25,
            'consistency': 0.20,
            'diversification': 0.15,
            'liquidity_behavior': 0.15
        }

        # Extract component scores
        sophistication = protocol_analysis.sophistication_score
        risk_management = behavior_analysis.behavior_metrics.loss_management_score
        consistency = behavior_analysis.behavior_metrics.consistency_score
        diversification = protocol_analysis.diversification_score
        liquidity_behavior = liquidity_analysis.overall_liquidity_score

        # Weighted combination
        overall_score = (
            sophistication * weights['sophistication'] +
            risk_management * weights['risk_management'] +
            consistency * weights['consistency'] +
            diversification * weights['diversification'] +
            liquidity_behavior * weights['liquidity_behavior']
        )

        return round(overall_score, 3)

    def _calculate_sophistication_score(self,
                                      protocol_analysis: CrossProtocolAnalysis,
                                      behavior_analysis: BehaviorPatternAnalysis,
                                      liquidity_analysis: LiquidityBehaviorAnalysis) -> float:
        """Calculate DeFi sophistication score"""

        sophistication_factors = []

        # Protocol sophistication
        sophistication_factors.append(protocol_analysis.sophistication_score)

        # Yield strategy sophistication
        sophistication_factors.append(
            behavior_analysis.behavior_metrics.yield_strategy_sophistication
        )

        # Liquidity provision sophistication
        sophistication_factors.append(
            liquidity_analysis.liquidity_sophistication_score
        )

        # Strategy complexity (from cross-protocol strategies)
        strategy_complexity = len(protocol_analysis.cross_protocol_strategies) / 5  # Max 5 strategies
        sophistication_factors.append(min(strategy_complexity, 1.0))

        return round(sum(sophistication_factors) / len(sophistication_factors), 3)

    def _calculate_risk_management_score(self,
                                       behavior_analysis: BehaviorPatternAnalysis,
                                       liquidity_analysis: LiquidityBehaviorAnalysis) -> float:
        """Calculate risk management capability score"""

        risk_factors = []

        # Loss management
        risk_factors.append(behavior_analysis.behavior_metrics.loss_management_score)

        # Diversification discipline
        risk_factors.append(behavior_analysis.behavior_metrics.diversification_discipline)

        # Market cycle adaptation
        risk_factors.append(behavior_analysis.market_cycle_behavior.cycle_adaptation_score)

        # Liquidity risk management
        risk_factors.append(liquidity_analysis.risk_management_score)

        # Panic resistance
        panic_resistance = behavior_analysis.market_cycle_behavior.bear_market_behavior.get(
            'panic_selling_resistance', 0.5
        )
        risk_factors.append(panic_resistance)

        return round(sum(risk_factors) / len(risk_factors), 3)

    def _calculate_defi_experience_score(self,
                                       protocol_analysis: CrossProtocolAnalysis,
                                       behavior_analysis: BehaviorPatternAnalysis) -> float:
        """Calculate DeFi experience and maturity score"""

        experience_factors = []

        # Protocol diversity and usage
        protocol_diversity = min(len(protocol_analysis.protocol_activities) / 4, 1.0)
        experience_factors.append(protocol_diversity)

        # Engagement level
        engagement_mapping = {
            'Highly Engaged': 1.0,
            'Moderately Engaged': 0.7,
            'Casually Engaged': 0.4,
            'Minimally Engaged': 0.2
        }
        engagement_score = engagement_mapping.get(protocol_analysis.engagement_level, 0.3)
        experience_factors.append(engagement_score)

        # Behavioral maturity progression
        maturity_progression = behavior_analysis.risk_profile_evolution.get('maturity_progression', 0.5)
        experience_factors.append(maturity_progression)

        # Time in DeFi (based on first activity across protocols)
        if protocol_analysis.protocol_activities:
            first_activities = [
                activity.first_activity for activity in protocol_analysis.protocol_activities.values()
            ]
            earliest_activity = min(first_activities)
            days_in_defi = (datetime.now() - earliest_activity).days
            time_score = min(days_in_defi / 365, 1.0)  # 1 year = max score
            experience_factors.append(time_score)

        return round(sum(experience_factors) / len(experience_factors), 3)

    def _determine_behavioral_risk_level(self,
                                       overall_score: float,
                                       risk_management_score: float,
                                       behavior_analysis: BehaviorPatternAnalysis) -> str:
        """Determine behavioral risk level"""

        # Check for critical red flags
        critical_red_flags = [
            flag for flag in behavior_analysis.behavioral_red_flags
            if any(keyword in flag.lower() for keyword in ['critical', 'panic', 'inadequate'])
        ]

        if critical_red_flags:
            return 'very_high'

        # Risk level determination based on scores
        if overall_score >= 0.8 and risk_management_score >= 0.7:
            return 'low'
        elif overall_score >= 0.6 and risk_management_score >= 0.5:
            return 'medium'
        elif overall_score >= 0.4:
            return 'high'
        else:
            return 'very_high'

    def _generate_loan_recommendation(self,
                                    risk_level: str,
                                    overall_score: float,
                                    loan_request: Dict[str, Any]) -> str:
        """Generate loan approval recommendation based on behavioral assessment"""

        # Risk level mapping to recommendations
        if risk_level == 'low':
            return 'approve'
        elif risk_level == 'medium':
            if overall_score >= 0.65:
                return 'approve'
            else:
                return 'conditional'
        elif risk_level == 'high':
            return 'monitor'
        else:  # very_high
            return 'reject'

    def _calculate_interest_rate_adjustment(self,
                                          risk_level: str,
                                          sophistication_score: float,
                                          risk_management_score: float) -> float:
        """Calculate interest rate adjustment in basis points"""

        base_adjustments = {
            'low': -25,      # 25 bps discount
            'medium': 0,     # No adjustment
            'high': 50,      # 50 bps premium
            'very_high': 150 # 150 bps premium
        }

        base_adjustment = base_adjustments.get(risk_level, 0)

        # Sophistication bonus (up to -15 bps)
        sophistication_bonus = (sophistication_score - 0.5) * 30

        # Risk management bonus (up to -10 bps)
        risk_management_bonus = (risk_management_score - 0.5) * 20

        total_adjustment = base_adjustment + sophistication_bonus + risk_management_bonus

        # Cap adjustments
        return round(max(-50, min(total_adjustment, 200)), 0)

    def _extract_behavioral_strengths(self,
                                    behavior_analysis: BehaviorPatternAnalysis,
                                    liquidity_analysis: LiquidityBehaviorAnalysis,
                                    protocol_analysis: CrossProtocolAnalysis) -> List[str]:
        """Extract behavioral strengths"""

        strengths = []

        # From behavior analysis
        strengths.extend(behavior_analysis.behavioral_strengths)

        # From protocol analysis
        if protocol_analysis.sophistication_score > 0.7:
            strengths.append("High DeFi protocol sophistication")

        if protocol_analysis.diversification_score > 0.7:
            strengths.append("Excellent protocol diversification")

        if len(protocol_analysis.cross_protocol_strategies) >= 3:
            strengths.append("Advanced cross-protocol strategies")

        # From liquidity analysis
        if liquidity_analysis.liquidity_sophistication_score > 0.7:
            strengths.append("Sophisticated liquidity provision strategies")

        if liquidity_analysis.risk_management_score > 0.7:
            strengths.append("Strong liquidity risk management")

        return strengths

    def _extract_behavioral_weaknesses(self,
                                     behavior_analysis: BehaviorPatternAnalysis,
                                     liquidity_analysis: LiquidityBehaviorAnalysis,
                                     protocol_analysis: CrossProtocolAnalysis) -> List[str]:
        """Extract behavioral weaknesses"""

        weaknesses = []

        # Low scores indicate weaknesses
        if behavior_analysis.behavior_metrics.risk_tolerance_score > 0.8 and \
           behavior_analysis.behavior_metrics.yield_strategy_sophistication < 0.4:
            weaknesses.append("High risk appetite without adequate sophistication")

        if behavior_analysis.behavior_metrics.consistency_score < 0.4:
            weaknesses.append("Inconsistent behavioral patterns")

        if protocol_analysis.diversification_score < 0.4:
            weaknesses.append("Poor protocol diversification")

        if liquidity_analysis.risk_management_score < 0.4:
            weaknesses.append("Inadequate liquidity risk management")

        if behavior_analysis.behavior_metrics.market_timing_ability < 0.3:
            weaknesses.append("Poor market timing skills")

        return weaknesses

    def _extract_red_flags(self,
                         behavior_analysis: BehaviorPatternAnalysis,
                         liquidity_analysis: LiquidityBehaviorAnalysis,
                         protocol_analysis: CrossProtocolAnalysis) -> List[str]:
        """Extract behavioral red flags"""

        red_flags = []

        # From behavior analysis
        red_flags.extend(behavior_analysis.behavioral_red_flags)

        # Additional red flags
        if protocol_analysis.engagement_level == 'Minimally Engaged':
            red_flags.append("Very limited DeFi engagement history")

        if len(protocol_analysis.protocol_activities) == 1:
            red_flags.append("Single protocol concentration risk")

        # Liquidity-specific red flags
        if liquidity_analysis.total_positions > 0 and \
           liquidity_analysis.il_metrics.total_il_experienced > \
           liquidity_analysis.total_liquidity_provided_usd * 0.2:
            red_flags.append("Excessive impermanent loss exposure")

        return red_flags

    def _extract_growth_indicators(self,
                                 protocol_analysis: CrossProtocolAnalysis,
                                 behavior_analysis: BehaviorPatternAnalysis) -> List[str]:
        """Extract positive growth and learning indicators"""

        growth_indicators = []

        # Risk profile evolution
        risk_trend = behavior_analysis.risk_profile_evolution.get('risk_trend', 'stable')
        if risk_trend == 'decreasing':
            growth_indicators.append("Improving risk management over time")

        # Learning indicators
        learning_indicators = behavior_analysis.risk_profile_evolution.get('learning_indicators', [])
        growth_indicators.extend(learning_indicators)

        # Protocol adoption growth
        if len(protocol_analysis.cross_protocol_strategies) > 2:
            growth_indicators.append("Developing sophisticated cross-protocol strategies")

        # Engagement growth
        if protocol_analysis.engagement_level in ['Highly Engaged', 'Moderately Engaged']:
            growth_indicators.append("Strong and growing DeFi ecosystem engagement")

        return growth_indicators

    def _generate_risk_mitigation_recommendations(self,
                                                risk_level: str,
                                                weaknesses: List[str],
                                                red_flags: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""

        recommendations = []

        if risk_level in ['high', 'very_high']:
            recommendations.append("Implement enhanced monitoring and early warning systems")

        if any('diversification' in weakness.lower() for weakness in weaknesses):
            recommendations.append("Encourage portfolio diversification across protocols")

        if any('sophistication' in weakness.lower() for weakness in weaknesses):
            recommendations.append("Provide DeFi education and risk awareness training")

        if any('panic' in flag.lower() for flag in red_flags):
            recommendations.append("Implement automatic stop-loss and risk management tools")

        if any('timing' in weakness.lower() for weakness in weaknesses):
            recommendations.append("Suggest dollar-cost averaging strategies")

        return recommendations

    def _generate_monitoring_requirements(self,
                                        risk_level: str,
                                        red_flags: List[str],
                                        loan_request: Dict[str, Any]) -> List[str]:
        """Generate monitoring requirements based on risk assessment"""

        requirements = []

        # Base monitoring by risk level
        if risk_level == 'low':
            requirements.append("Monthly behavioral assessment review")
        elif risk_level == 'medium':
            requirements.append("Bi-weekly behavioral pattern monitoring")
        elif risk_level == 'high':
            requirements.append("Weekly high-risk behavior detection")
        else:  # very_high
            requirements.append("Daily critical risk behavior monitoring")

        # Specific monitoring for red flags
        if any('panic' in flag.lower() for flag in red_flags):
            requirements.append("Real-time market stress response monitoring")

        if any('concentration' in flag.lower() for flag in red_flags):
            requirements.append("Protocol concentration risk alerts")

        if any('liquidation' in flag.lower() for flag in red_flags):
            requirements.append("Enhanced liquidation risk monitoring")

        return requirements

    def _calculate_analysis_confidence(self,
                                     protocol_analysis: CrossProtocolAnalysis,
                                     behavior_analysis: BehaviorPatternAnalysis,
                                     liquidity_analysis: LiquidityBehaviorAnalysis) -> float:
        """Calculate overall confidence in the behavioral analysis"""

        confidence_factors = []

        # Individual analysis confidence levels
        confidence_factors.append(behavior_analysis.confidence_level)
        confidence_factors.append(liquidity_analysis.confidence_level)

        # Data quantity factor
        total_transactions = sum(
            activity.total_transactions
            for activity in protocol_analysis.protocol_activities.values()
        )
        data_quantity_score = min(total_transactions / 100, 1.0)  # 100 tx = full confidence
        confidence_factors.append(data_quantity_score)

        # Protocol diversity factor
        protocol_diversity_score = min(len(protocol_analysis.protocol_activities) / 4, 1.0)
        confidence_factors.append(protocol_diversity_score)

        return round(sum(confidence_factors) / len(confidence_factors), 3)

    def _calculate_data_quality_score(self,
                                    protocol_analysis: CrossProtocolAnalysis,
                                    behavior_analysis: BehaviorPatternAnalysis,
                                    liquidity_analysis: LiquidityBehaviorAnalysis) -> float:
        """Calculate data quality score"""

        quality_factors = []

        # Completeness of protocol data
        complete_protocols = len([
            activity for activity in protocol_analysis.protocol_activities.values()
            if activity.total_transactions > 0 and activity.total_volume_usd > 0
        ])
        completeness_score = complete_protocols / max(len(protocol_analysis.protocol_activities), 1)
        quality_factors.append(completeness_score)

        # Behavioral data consistency
        consistency_score = behavior_analysis.behavior_metrics.consistency_score
        quality_factors.append(consistency_score)

        # Liquidity data completeness
        if liquidity_analysis.total_positions > 0:
            quality_factors.append(0.9)  # Good quality if we have LP data
        else:
            quality_factors.append(0.6)  # Lower quality without LP data

        return round(sum(quality_factors) / len(quality_factors), 3)

    def export_assessment(self, assessment: BehavioralRiskAssessment, format: str = 'json') -> str:
        """Export behavioral assessment in specified format"""
        try:
            if format.lower() == 'json':
                return json.dumps(asdict(assessment), indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Error exporting assessment: {str(e)}")
            return "{}"