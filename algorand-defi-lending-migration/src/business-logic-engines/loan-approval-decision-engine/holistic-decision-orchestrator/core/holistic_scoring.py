"""
Holistic Scoring Engine for Algorand-Native Loan Decisions

Combines weighted scores from all 5 engines to produce comprehensive
assessment of borrower creditworthiness based on ecosystem participation.
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

from .decision_orchestrator import BorrowerProfile, LoanApplication


@dataclass
class EngineScore:
    """Individual engine score with metadata"""
    score: float
    confidence: float
    weight: float
    normalized_score: float
    contribution: float


@dataclass
class HolisticScores:
    """Complete holistic scoring results"""
    overall_score: float
    confidence_weighted_score: float

    # Individual engine scores
    ecosystem_score: float
    defi_score: float
    collateral_score: float
    governance_score: float
    risk_score: float

    # Score components
    engine_scores: Dict[str, EngineScore]

    # Quality metrics
    data_completeness: float
    score_variance: float
    confidence_level: float

    # Contextual adjustments
    market_adjustment: float
    network_adjustment: float
    temporal_adjustment: float


class HolisticScorer:
    """
    Sophisticated scoring engine that combines multiple data sources
    into unified creditworthiness assessment.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.engine_weights = config.get('engine_weights', {})
        self.logger = logging.getLogger("holistic_scorer")

        # Scoring parameters
        self.confidence_boost = 0.1  # Boost for high confidence scores
        self.consistency_bonus = 0.05  # Bonus for consistent scores across engines
        self.diversity_bonus = 0.03  # Bonus for diverse data sources

    async def calculate_holistic_scores(
        self,
        profile: BorrowerProfile,
        application: LoanApplication
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive holistic scores combining all engines.

        Returns weighted and adjusted scores based on:
        - Individual engine performance
        - Data quality and confidence
        - Market and network conditions
        - Temporal factors
        """

        self.logger.info(f"Calculating holistic scores for {profile.address}")

        # Step 1: Normalize individual engine scores
        engine_scores = self._normalize_engine_scores(profile)

        # Step 2: Apply confidence weighting
        confidence_weighted = self._apply_confidence_weighting(engine_scores, profile)

        # Step 3: Calculate base holistic score
        base_score = self._calculate_weighted_score(confidence_weighted)

        # Step 4: Apply contextual adjustments
        contextual_adjustments = self._calculate_contextual_adjustments(
            profile, application
        )

        # Step 5: Apply quality bonuses
        quality_bonuses = self._calculate_quality_bonuses(profile, engine_scores)

        # Step 6: Calculate final adjusted score
        final_score = self._calculate_final_score(
            base_score, contextual_adjustments, quality_bonuses
        )

        # Step 7: Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(profile, engine_scores)

        return {
            'overall_score': final_score,
            'confidence_weighted_score': base_score,

            'ecosystem_score': profile.ecosystem_score,
            'defi_score': profile.defi_score,
            'collateral_score': profile.collateral_score,
            'governance_score': profile.governance_score,
            'risk_score': profile.risk_score,

            'engine_scores': {
                name: {
                    'score': score.score,
                    'confidence': score.confidence,
                    'weight': score.weight,
                    'contribution': score.contribution
                }
                for name, score in engine_scores.items()
            },

            'data_completeness': profile.data_completeness,
            'score_variance': self._calculate_score_variance(engine_scores),
            'confidence_level': overall_confidence,

            'market_adjustment': contextual_adjustments['market'],
            'network_adjustment': contextual_adjustments['network'],
            'temporal_adjustment': contextual_adjustments['temporal'],

            'quality_bonuses': quality_bonuses,

            'scoring_metadata': {
                'calculation_timestamp': datetime.now(),
                'profile_timestamp': profile.timestamp,
                'engines_available': len([s for s in engine_scores.values() if s.confidence > 0]),
                'total_engines': len(engine_scores)
            }
        }

    def _normalize_engine_scores(self, profile: BorrowerProfile) -> Dict[str, EngineScore]:
        """
        Normalize scores from different engines to consistent 0-1 scale.

        Each engine may have different scoring methodologies, so we normalize
        them for fair comparison and combination.
        """

        # Raw scores from engines
        raw_scores = {
            'ecosystem_analysis': {
                'score': profile.ecosystem_score,
                'confidence': profile.ecosystem_confidence,
                'weight': self.engine_weights.get('ecosystem_analysis', 0.30)
            },
            'defi_behavior': {
                'score': profile.defi_score,
                'confidence': profile.defi_confidence,
                'weight': self.engine_weights.get('defi_behavior', 0.25)
            },
            'collateral_intelligence': {
                'score': profile.collateral_score,
                'confidence': profile.collateral_confidence,
                'weight': self.engine_weights.get('collateral_intelligence', 0.20)
            },
            'governance_reputation': {
                'score': profile.governance_score,
                'confidence': profile.governance_confidence,
                'weight': self.engine_weights.get('governance_reputation', 0.15)
            },
            'network_risk_monitoring': {
                'score': 1.0 - profile.risk_score,  # Invert risk score (lower risk = higher score)
                'confidence': profile.risk_confidence,
                'weight': self.engine_weights.get('network_risk_monitoring', 0.10)
            }
        }

        # Normalize and create EngineScore objects
        normalized_scores = {}
        for engine_name, data in raw_scores.items():
            # Ensure score is in 0-1 range
            normalized_score = max(0.0, min(1.0, data['score']))

            # Calculate contribution based on weight and confidence
            contribution = normalized_score * data['weight'] * data['confidence']

            normalized_scores[engine_name] = EngineScore(
                score=data['score'],
                confidence=data['confidence'],
                weight=data['weight'],
                normalized_score=normalized_score,
                contribution=contribution
            )

        return normalized_scores

    def _apply_confidence_weighting(
        self,
        engine_scores: Dict[str, EngineScore],
        profile: BorrowerProfile
    ) -> Dict[str, EngineScore]:
        """
        Adjust engine weights based on confidence levels.

        Higher confidence engines get more weight in final decision.
        """

        # Calculate total confidence-weighted weight
        total_confidence_weight = sum(
            score.weight * score.confidence
            for score in engine_scores.values()
        )

        # Avoid division by zero
        if total_confidence_weight == 0:
            return engine_scores

        # Redistribute weights based on confidence
        adjusted_scores = {}
        for engine_name, score in engine_scores.items():
            confidence_adjusted_weight = (
                score.weight * score.confidence / total_confidence_weight
            ) * sum(self.engine_weights.values())  # Maintain total weight

            adjusted_scores[engine_name] = EngineScore(
                score=score.score,
                confidence=score.confidence,
                weight=confidence_adjusted_weight,
                normalized_score=score.normalized_score,
                contribution=score.normalized_score * confidence_adjusted_weight
            )

        return adjusted_scores

    def _calculate_weighted_score(self, engine_scores: Dict[str, EngineScore]) -> float:
        """Calculate base weighted score from all engines"""

        total_contribution = sum(score.contribution for score in engine_scores.values())
        total_weight = sum(score.weight for score in engine_scores.values())

        if total_weight == 0:
            return 0.5  # Default score if no engines available

        return total_contribution / total_weight

    def _calculate_contextual_adjustments(
        self,
        profile: BorrowerProfile,
        application: LoanApplication
    ) -> Dict[str, float]:
        """
        Calculate adjustments based on market and network conditions.

        These adjustments account for external factors that affect loan risk.
        """

        # Market condition adjustment
        market_adjustment = 0.0
        if hasattr(application, 'market_conditions'):
            volatility = application.market_conditions.get('volatility', 0.2)
            # Higher volatility = more conservative scoring
            market_adjustment = -0.05 * max(0, volatility - 0.2)

        # Network health adjustment
        network_adjustment = 0.0
        if hasattr(application, 'network_health'):
            health_score = application.network_health.get('health_score', 0.9)
            # Better network health = slight positive adjustment
            network_adjustment = 0.02 * max(0, health_score - 0.8)

        # Temporal adjustment (account age, recent activity)
        temporal_adjustment = 0.0
        ecosystem_data = profile.ecosystem_data
        if 'wallet_age_days' in ecosystem_data:
            wallet_age_days = ecosystem_data['wallet_age_days']
            # Bonus for mature wallets
            if wallet_age_days > 365:
                temporal_adjustment += 0.03
            elif wallet_age_days > 180:
                temporal_adjustment += 0.01

        return {
            'market': market_adjustment,
            'network': network_adjustment,
            'temporal': temporal_adjustment
        }

    def _calculate_quality_bonuses(
        self,
        profile: BorrowerProfile,
        engine_scores: Dict[str, EngineScore]
    ) -> Dict[str, float]:
        """
        Calculate bonuses for high-quality data and consistent scoring.
        """

        bonuses = {}

        # Data completeness bonus
        if profile.data_completeness > 0.9:
            bonuses['completeness'] = 0.02
        elif profile.data_completeness > 0.8:
            bonuses['completeness'] = 0.01
        else:
            bonuses['completeness'] = 0.0

        # Confidence consistency bonus
        confidences = [score.confidence for score in engine_scores.values()]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)

            # Low variance in confidence = more reliable
            if confidence_variance < 0.01 and avg_confidence > 0.8:
                bonuses['consistency'] = 0.02
            else:
                bonuses['consistency'] = 0.0

        # Score consistency bonus
        scores = [score.normalized_score for score in engine_scores.values()]
        if scores:
            score_variance = self._calculate_variance(scores)
            if score_variance < 0.05:  # Consistent scores across engines
                bonuses['score_consistency'] = 0.01
            else:
                bonuses['score_consistency'] = 0.0

        # Data diversity bonus (multiple strong data sources)
        strong_engines = len([s for s in engine_scores.values() if s.confidence > 0.8])
        if strong_engines >= 4:
            bonuses['diversity'] = 0.02
        elif strong_engines >= 3:
            bonuses['diversity'] = 0.01
        else:
            bonuses['diversity'] = 0.0

        return bonuses

    def _calculate_final_score(
        self,
        base_score: float,
        adjustments: Dict[str, float],
        bonuses: Dict[str, float]
    ) -> float:
        """
        Calculate final score with all adjustments and bonuses applied.
        """

        # Start with base score
        final_score = base_score

        # Apply contextual adjustments
        for adjustment in adjustments.values():
            final_score += adjustment

        # Apply quality bonuses
        for bonus in bonuses.values():
            final_score += bonus

        # Ensure score stays in valid range
        return max(0.0, min(1.0, final_score))

    def _calculate_overall_confidence(
        self,
        profile: BorrowerProfile,
        engine_scores: Dict[str, EngineScore]
    ) -> float:
        """
        Calculate overall confidence in the holistic score.
        """

        # Weight confidence by engine importance
        weighted_confidences = []
        total_weight = 0

        for score in engine_scores.values():
            weighted_confidences.append(score.confidence * score.weight)
            total_weight += score.weight

        if total_weight == 0:
            return 0.0

        base_confidence = sum(weighted_confidences) / total_weight

        # Adjust for data completeness
        completeness_factor = profile.data_completeness

        # Adjust for score consistency
        scores = [s.normalized_score for s in engine_scores.values()]
        variance = self._calculate_variance(scores) if scores else 1.0
        consistency_factor = max(0.5, 1.0 - variance)

        # Calculate final confidence
        final_confidence = base_confidence * completeness_factor * consistency_factor

        return max(0.0, min(1.0, final_confidence))

    def _calculate_score_variance(self, engine_scores: Dict[str, EngineScore]) -> float:
        """Calculate variance in normalized scores across engines"""
        scores = [score.normalized_score for score in engine_scores.values()]
        return self._calculate_variance(scores)

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def get_score_explanation(self, scores: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate human-readable explanation of scoring decisions.
        """

        explanations = {}

        # Overall score explanation
        overall = scores['overall_score']
        if overall >= 0.85:
            explanations['overall'] = "Excellent borrower profile with strong ecosystem participation"
        elif overall >= 0.70:
            explanations['overall'] = "Good borrower profile with solid Algorand engagement"
        elif overall >= 0.55:
            explanations['overall'] = "Fair borrower profile with moderate ecosystem activity"
        elif overall >= 0.40:
            explanations['overall'] = "Poor borrower profile with limited ecosystem engagement"
        else:
            explanations['overall'] = "High-risk borrower with minimal or concerning activity"

        # Engine-specific explanations
        engine_explanations = {}
        for engine_name, engine_data in scores['engine_scores'].items():
            score = engine_data['score']
            confidence = engine_data['confidence']

            if confidence < 0.5:
                engine_explanations[engine_name] = f"Limited data available (confidence: {confidence:.2f})"
            elif score >= 0.8:
                engine_explanations[engine_name] = f"Strong performance (score: {score:.2f})"
            elif score >= 0.6:
                engine_explanations[engine_name] = f"Good performance (score: {score:.2f})"
            elif score >= 0.4:
                engine_explanations[engine_name] = f"Fair performance (score: {score:.2f})"
            else:
                engine_explanations[engine_name] = f"Poor performance (score: {score:.2f})"

        explanations['engines'] = engine_explanations

        return explanations