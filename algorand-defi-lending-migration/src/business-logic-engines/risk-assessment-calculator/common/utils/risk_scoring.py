"""
Blockchain Risk Scoring Algorithms

Advanced risk scoring algorithms specifically designed for
blockchain-native risk assessment in DeFi protocols.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math
import statistics
from collections import defaultdict

from ..models.blockchain_risk import (
    RiskLevel, TransactionPattern, BehaviorPattern,
    HolisticRiskProfile, ASARisk, ProtocolRisk, LiquidityRisk
)


class RiskComponent(Enum):
    """Components of blockchain risk"""
    TRANSACTION_BEHAVIOR = "transaction_behavior"
    WALLET_CLUSTERING = "wallet_clustering"
    DEFI_EXPOSURE = "defi_exposure"
    LIQUIDITY_RISK = "liquidity_risk"
    SMART_CONTRACT_RISK = "smart_contract_risk"
    GOVERNANCE_RISK = "governance_risk"
    SYSTEMIC_RISK = "systemic_risk"
    MEV_EXPOSURE = "mev_exposure"
    BRIDGE_RISK = "bridge_risk"
    ASA_RISK = "asa_risk"


@dataclass
class RiskWeight:
    """Risk component weight configuration"""
    component: RiskComponent
    base_weight: float
    context_multipliers: Dict[str, float]
    decay_factor: float = 0.95  # Time decay factor


@dataclass
class ScoringContext:
    """Context for risk scoring"""
    entity_type: str  # wallet, protocol, asset
    time_horizon: timedelta
    market_conditions: str  # bull, bear, sideways
    regulatory_environment: str
    protocol_maturity: str
    analysis_purpose: str  # lending, trading, governance


class BlockchainRiskScorer:
    """Advanced blockchain-native risk scoring system"""

    def __init__(self):
        self.default_weights = self._initialize_default_weights()
        self.scoring_models = {}
        self.context_adjustments = {}
        self.temporal_decay_factors = {}

    def _initialize_default_weights(self) -> Dict[RiskComponent, RiskWeight]:
        """Initialize default risk component weights"""
        return {
            RiskComponent.TRANSACTION_BEHAVIOR: RiskWeight(
                component=RiskComponent.TRANSACTION_BEHAVIOR,
                base_weight=0.20,
                context_multipliers={
                    'high_velocity': 1.5,
                    'dormant_activation': 2.0,
                    'wash_trading': 2.5
                }
            ),
            RiskComponent.WALLET_CLUSTERING: RiskWeight(
                component=RiskComponent.WALLET_CLUSTERING,
                base_weight=0.15,
                context_multipliers={
                    'sybil_detected': 3.0,
                    'coordinated_behavior': 2.0
                }
            ),
            RiskComponent.DEFI_EXPOSURE: RiskWeight(
                component=RiskComponent.DEFI_EXPOSURE,
                base_weight=0.15,
                context_multipliers={
                    'high_concentration': 1.8,
                    'experimental_protocols': 2.0
                }
            ),
            RiskComponent.LIQUIDITY_RISK: RiskWeight(
                component=RiskComponent.LIQUIDITY_RISK,
                base_weight=0.12,
                context_multipliers={
                    'low_liquidity': 2.0,
                    'high_slippage': 1.5
                }
            ),
            RiskComponent.SMART_CONTRACT_RISK: RiskWeight(
                component=RiskComponent.SMART_CONTRACT_RISK,
                base_weight=0.12,
                context_multipliers={
                    'unaudited': 2.5,
                    'high_complexity': 1.5
                }
            ),
            RiskComponent.MEV_EXPOSURE: RiskWeight(
                component=RiskComponent.MEV_EXPOSURE,
                base_weight=0.10,
                context_multipliers={
                    'frequent_mev': 2.0,
                    'sandwich_victim': 1.8
                }
            ),
            RiskComponent.BRIDGE_RISK: RiskWeight(
                component=RiskComponent.BRIDGE_RISK,
                base_weight=0.08,
                context_multipliers={
                    'high_bridge_usage': 1.5,
                    'risky_bridges': 2.0
                }
            ),
            RiskComponent.GOVERNANCE_RISK: RiskWeight(
                component=RiskComponent.GOVERNANCE_RISK,
                base_weight=0.05,
                context_multipliers={
                    'centralized_governance': 1.8
                }
            ),
            RiskComponent.ASA_RISK: RiskWeight(
                component=RiskComponent.ASA_RISK,
                base_weight=0.03,
                context_multipliers={
                    'experimental_assets': 2.0
                }
            )
        }

    async def calculate_comprehensive_risk_score(
        self,
        risk_profile: HolisticRiskProfile,
        scoring_context: ScoringContext
    ) -> Tuple[float, RiskLevel, Dict[str, float]]:
        """
        Calculate comprehensive risk score using blockchain-native factors

        Args:
            risk_profile: Holistic risk profile data
            scoring_context: Context for scoring

        Returns:
            Tuple of (overall_score, risk_level, component_scores)
        """
        # Calculate individual component scores
        component_scores = await self._calculate_component_scores(risk_profile, scoring_context)

        # Apply context-based weight adjustments
        adjusted_weights = self._adjust_weights_for_context(scoring_context)

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(component_scores, adjusted_weights)

        # Apply temporal decay
        time_adjusted_score = self._apply_temporal_decay(overall_score, risk_profile, scoring_context)

        # Apply market condition adjustments
        market_adjusted_score = self._apply_market_adjustments(time_adjusted_score, scoring_context)

        # Determine risk level
        risk_level = self._determine_risk_level(market_adjusted_score)

        return market_adjusted_score, risk_level, component_scores

    async def _calculate_component_scores(
        self,
        risk_profile: HolisticRiskProfile,
        context: ScoringContext
    ) -> Dict[str, float]:
        """Calculate scores for individual risk components"""
        scores = {}

        # Transaction behavior score
        scores['transaction_behavior'] = await self._score_transaction_behavior(
            risk_profile.transaction_patterns, context
        )

        # Wallet clustering score
        scores['wallet_clustering'] = await self._score_wallet_clustering(
            risk_profile, context
        )

        # DeFi exposure score
        scores['defi_exposure'] = await self._score_defi_exposure(
            risk_profile.defi_exposures, context
        )

        # Liquidity risk score
        scores['liquidity_risk'] = await self._score_liquidity_risk(
            risk_profile.liquidity_risks, context
        )

        # Smart contract risk score
        scores['smart_contract_risk'] = await self._score_smart_contract_risk(
            risk_profile.smart_contract_risks, context
        )

        # MEV exposure score
        scores['mev_exposure'] = await self._score_mev_exposure(
            risk_profile.transaction_patterns, context
        )

        # Bridge risk score
        scores['bridge_risk'] = await self._score_bridge_risk(
            risk_profile, context
        )

        # Governance risk score
        scores['governance_risk'] = await self._score_governance_risk(
            risk_profile.governance_risks, context
        )

        # ASA risk score
        scores['asa_risk'] = await self._score_asa_risk(
            risk_profile.asa_risks, context
        )

        return scores

    async def _score_transaction_behavior(
        self,
        patterns: List[TransactionPattern],
        context: ScoringContext
    ) -> float:
        """Score transaction behavior patterns"""
        if not patterns:
            return 0.0

        pattern_scores = []

        for pattern in patterns:
            base_score = pattern.confidence_score

            # Pattern-specific scoring
            if pattern.pattern_type == BehaviorPattern.VELOCITY_SPIKE:
                score = base_score * 0.6  # Moderate risk
            elif pattern.pattern_type == BehaviorPattern.DORMANT_ACTIVATION:
                score = base_score * 0.8  # Higher risk
            elif pattern.pattern_type == BehaviorPattern.WASH_TRADING:
                score = base_score * 0.9  # High risk
            elif pattern.pattern_type == BehaviorPattern.SYBIL_CLUSTER:
                score = base_score * 0.95  # Very high risk
            elif pattern.pattern_type == BehaviorPattern.MEV_EXPLOITATION:
                score = base_score * 0.7  # Moderate-high risk
            else:
                score = base_score * 0.5

            # Apply risk factor multipliers
            for factor, value in pattern.risk_factors.items():
                if factor == 'volume_concentration' and value > 0.8:
                    score *= 1.3
                elif factor == 'velocity_anomaly' and value > 0.9:
                    score *= 1.4

            pattern_scores.append(score)

        # Use weighted average with emphasis on highest risks
        pattern_scores.sort(reverse=True)
        if len(pattern_scores) == 1:
            return min(pattern_scores[0], 1.0)
        else:
            # Weight top patterns more heavily
            weighted_sum = 0.0
            weight_sum = 0.0
            for i, score in enumerate(pattern_scores[:5]):  # Top 5 patterns
                weight = 1.0 / (i + 1)  # Decreasing weights
                weighted_sum += score * weight
                weight_sum += weight

            return min(weighted_sum / weight_sum, 1.0)

    async def _score_wallet_clustering(
        self,
        risk_profile: HolisticRiskProfile,
        context: ScoringContext
    ) -> float:
        """Score wallet clustering risk"""
        # Look for clustering-related alerts
        clustering_alerts = [
            alert for alert in risk_profile.active_alerts
            if 'sybil' in alert.alert_type.lower() or 'cluster' in alert.alert_type.lower()
        ]

        if not clustering_alerts:
            return 0.0

        # Calculate score based on clustering evidence
        max_clustering_score = 0.0
        for alert in clustering_alerts:
            score = alert.risk_score * alert.confidence
            max_clustering_score = max(max_clustering_score, score)

        return min(max_clustering_score, 1.0)

    async def _score_defi_exposure(
        self,
        exposures: List,  # Would be DeFiExposure objects
        context: ScoringContext
    ) -> float:
        """Score DeFi exposure risk"""
        if not exposures:
            return 0.0

        total_exposure_risk = 0.0
        total_weight = 0.0

        for exposure in exposures:
            # Calculate individual exposure risk
            exposure_risk = exposure.calculate_overall_exposure_risk()

            # Weight by exposure size
            weight = exposure.position_size
            total_exposure_risk += exposure_risk * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return min(total_exposure_risk / total_weight, 1.0)

    async def _score_liquidity_risk(
        self,
        liquidity_risks: List[LiquidityRisk],
        context: ScoringContext
    ) -> float:
        """Score liquidity risk"""
        if not liquidity_risks:
            return 0.0

        risk_scores = []
        for liquidity_risk in liquidity_risks:
            score = liquidity_risk.calculate_liquidity_risk_score()
            risk_scores.append(score)

        # Use maximum risk approach
        return max(risk_scores) if risk_scores else 0.0

    async def _score_smart_contract_risk(
        self,
        contract_risks: List,  # Would be SmartContractRisk objects
        context: ScoringContext
    ) -> float:
        """Score smart contract risk"""
        if not contract_risks:
            return 0.0

        risk_scores = []
        for contract_risk in contract_risks:
            score = contract_risk.calculate_contract_risk_score()
            risk_scores.append(score)

        # Use weighted average based on interaction frequency
        if not risk_scores:
            return 0.0

        total_risk = 0.0
        total_weight = 0.0

        for i, contract_risk in enumerate(contract_risks):
            weight = contract_risk.interaction_frequency
            total_risk += risk_scores[i] * weight
            total_weight += weight

        if total_weight == 0:
            return statistics.mean(risk_scores)

        return min(total_risk / total_weight, 1.0)

    async def _score_mev_exposure(
        self,
        patterns: List[TransactionPattern],
        context: ScoringContext
    ) -> float:
        """Score MEV exposure risk"""
        mev_patterns = [
            pattern for pattern in patterns
            if pattern.pattern_type in [
                BehaviorPattern.MEV_EXPLOITATION,
                BehaviorPattern.FLASH_LOAN_ARBITRAGE
            ]
        ]

        if not mev_patterns:
            return 0.0

        # Calculate MEV activity score
        mev_score = 0.0
        for pattern in mev_patterns:
            if pattern.pattern_type == BehaviorPattern.MEV_EXPLOITATION:
                mev_score += pattern.confidence_score * 0.8
            elif pattern.pattern_type == BehaviorPattern.FLASH_LOAN_ARBITRAGE:
                mev_score += pattern.confidence_score * 0.6

        return min(mev_score, 1.0)

    async def _score_bridge_risk(
        self,
        risk_profile: HolisticRiskProfile,
        context: ScoringContext
    ) -> float:
        """Score cross-chain bridge risk"""
        # Look for bridge-related patterns
        bridge_patterns = [
            pattern for pattern in risk_profile.transaction_patterns
            if pattern.pattern_type == BehaviorPattern.BRIDGE_FARMING
        ]

        if not bridge_patterns:
            return 0.0

        bridge_score = 0.0
        for pattern in bridge_patterns:
            bridge_score += pattern.confidence_score * 0.5

        return min(bridge_score, 1.0)

    async def _score_governance_risk(
        self,
        governance_risks: List,  # Would be GovernanceRisk objects
        context: ScoringContext
    ) -> float:
        """Score governance risk"""
        if not governance_risks:
            return 0.0

        risk_scores = []
        for governance_risk in governance_risks:
            score = governance_risk.calculate_governance_risk_score()
            risk_scores.append(score)

        return max(risk_scores) if risk_scores else 0.0

    async def _score_asa_risk(
        self,
        asa_risks: List[ASARisk],
        context: ScoringContext
    ) -> float:
        """Score Algorand Standard Asset risk"""
        if not asa_risks:
            return 0.0

        risk_scores = []
        for asa_risk in asa_risks:
            score = asa_risk.calculate_asa_risk_score()
            risk_scores.append(score)

        return max(risk_scores) if risk_scores else 0.0

    def _adjust_weights_for_context(
        self,
        context: ScoringContext
    ) -> Dict[RiskComponent, float]:
        """Adjust component weights based on context"""
        adjusted_weights = {}

        for component, weight_config in self.default_weights.items():
            base_weight = weight_config.base_weight

            # Apply context multipliers
            multiplier = 1.0

            # Entity type adjustments
            if context.entity_type == 'wallet':
                if component == RiskComponent.TRANSACTION_BEHAVIOR:
                    multiplier *= 1.2
            elif context.entity_type == 'protocol':
                if component == RiskComponent.SMART_CONTRACT_RISK:
                    multiplier *= 1.3

            # Market condition adjustments
            if context.market_conditions == 'bear':
                if component == RiskComponent.LIQUIDITY_RISK:
                    multiplier *= 1.4
            elif context.market_conditions == 'bull':
                if component == RiskComponent.MEV_EXPOSURE:
                    multiplier *= 1.2

            # Time horizon adjustments
            if context.time_horizon > timedelta(days=90):
                if component == RiskComponent.GOVERNANCE_RISK:
                    multiplier *= 1.3

            adjusted_weights[component] = base_weight * multiplier

        # Normalize weights to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        for component in adjusted_weights:
            adjusted_weights[component] /= total_weight

        return adjusted_weights

    def _calculate_weighted_score(
        self,
        component_scores: Dict[str, float],
        weights: Dict[RiskComponent, float]
    ) -> float:
        """Calculate weighted overall risk score"""
        total_score = 0.0
        total_weight = 0.0

        for component, weight in weights.items():
            component_name = component.value
            if component_name in component_scores:
                score = component_scores[component_name]
                total_score += score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def _apply_temporal_decay(
        self,
        score: float,
        risk_profile: HolisticRiskProfile,
        context: ScoringContext
    ) -> float:
        """Apply temporal decay to risk scores"""
        # Calculate time since last significant activity
        time_since_assessment = datetime.utcnow() - risk_profile.assessment_timestamp
        decay_days = time_since_assessment.days

        # Apply exponential decay
        decay_factor = 0.98 ** decay_days  # 2% decay per day

        return score * decay_factor

    def _apply_market_adjustments(
        self,
        score: float,
        context: ScoringContext
    ) -> float:
        """Apply market condition adjustments"""
        multiplier = 1.0

        if context.market_conditions == 'bear':
            multiplier *= 1.15  # Increase risk in bear markets
        elif context.market_conditions == 'bull':
            multiplier *= 0.95  # Slightly decrease risk in bull markets

        # Regulatory environment adjustments
        if context.regulatory_environment == 'strict':
            multiplier *= 1.1
        elif context.regulatory_environment == 'permissive':
            multiplier *= 0.95

        return min(score * multiplier, 1.0)

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from numerical score"""
        if score <= 0.15:
            return RiskLevel.MINIMAL
        elif score <= 0.35:
            return RiskLevel.LOW
        elif score <= 0.60:
            return RiskLevel.MODERATE
        elif score <= 0.80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    async def calculate_portfolio_risk_score(
        self,
        portfolio_positions: List[Dict[str, Any]],
        context: ScoringContext
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate portfolio-level risk score"""
        if not portfolio_positions:
            return 0.0, {}

        position_risks = []
        total_value = 0.0

        # Calculate risk for each position
        for position in portfolio_positions:
            position_value = position.get('value', 0)
            position_risk = position.get('risk_score', 0)

            position_risks.append({
                'value': position_value,
                'risk': position_risk,
                'asset': position.get('asset', 'unknown')
            })
            total_value += position_value

        if total_value == 0:
            return 0.0, {}

        # Calculate value-weighted risk
        weighted_risk = 0.0
        for pos_risk in position_risks:
            weight = pos_risk['value'] / total_value
            weighted_risk += pos_risk['risk'] * weight

        # Calculate concentration risk
        concentration_risk = self._calculate_concentration_risk(position_risks, total_value)

        # Calculate correlation risk
        correlation_risk = await self._calculate_correlation_risk(position_risks)

        # Combine risks
        portfolio_risk = min(
            weighted_risk * 0.6 +
            concentration_risk * 0.25 +
            correlation_risk * 0.15,
            1.0
        )

        risk_breakdown = {
            'weighted_position_risk': weighted_risk,
            'concentration_risk': concentration_risk,
            'correlation_risk': correlation_risk,
            'portfolio_risk': portfolio_risk
        }

        return portfolio_risk, risk_breakdown

    def _calculate_concentration_risk(
        self,
        position_risks: List[Dict[str, Any]],
        total_value: float
    ) -> float:
        """Calculate portfolio concentration risk"""
        if total_value == 0:
            return 0.0

        # Calculate Herfindahl index for concentration
        hhi = 0.0
        for pos_risk in position_risks:
            weight = pos_risk['value'] / total_value
            hhi += weight ** 2

        # Convert HHI to risk score (0-1)
        # HHI ranges from 1/n (perfect diversification) to 1 (complete concentration)
        n_positions = len(position_risks)
        min_hhi = 1.0 / n_positions if n_positions > 0 else 1.0
        max_hhi = 1.0

        concentration_risk = (hhi - min_hhi) / (max_hhi - min_hhi)
        return min(concentration_risk, 1.0)

    async def _calculate_correlation_risk(
        self,
        position_risks: List[Dict[str, Any]]
    ) -> float:
        """Calculate portfolio correlation risk"""
        # Simplified correlation risk calculation
        # In practice, this would use historical correlation data

        unique_assets = set(pos['asset'] for pos in position_risks)

        # Assume higher correlation in crypto markets
        if len(unique_assets) <= 2:
            return 0.8  # High correlation risk
        elif len(unique_assets) <= 5:
            return 0.5  # Medium correlation risk
        else:
            return 0.2  # Lower correlation risk

    def create_risk_score_explanation(
        self,
        overall_score: float,
        risk_level: RiskLevel,
        component_scores: Dict[str, float],
        context: ScoringContext
    ) -> Dict[str, Any]:
        """Create detailed explanation of risk score"""
        # Identify top risk contributors
        sorted_components = sorted(
            component_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_risks = sorted_components[:3]

        explanations = []
        for component, score in top_risks:
            if score > 0.3:
                explanations.append(
                    f"{component.replace('_', ' ').title()}: {score:.2f}"
                )

        return {
            'overall_score': overall_score,
            'risk_level': risk_level.value,
            'top_risk_contributors': top_risks,
            'explanations': explanations,
            'component_breakdown': component_scores,
            'context_applied': {
                'entity_type': context.entity_type,
                'market_conditions': context.market_conditions,
                'time_horizon_days': context.time_horizon.days
            },
            'recommendations': self._generate_risk_recommendations(
                risk_level, component_scores
            )
        }

    def _generate_risk_recommendations(
        self,
        risk_level: RiskLevel,
        component_scores: Dict[str, float]
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Implement immediate risk monitoring and alerts")
            recommendations.append("Consider position size limitations")

        # Component-specific recommendations
        if component_scores.get('transaction_behavior', 0) > 0.6:
            recommendations.append("Enhanced transaction pattern monitoring required")

        if component_scores.get('liquidity_risk', 0) > 0.6:
            recommendations.append("Diversify across multiple liquidity sources")

        if component_scores.get('smart_contract_risk', 0) > 0.7:
            recommendations.append("Require additional smart contract audits")

        if component_scores.get('defi_exposure', 0) > 0.5:
            recommendations.append("Reduce protocol concentration risk")

        return recommendations