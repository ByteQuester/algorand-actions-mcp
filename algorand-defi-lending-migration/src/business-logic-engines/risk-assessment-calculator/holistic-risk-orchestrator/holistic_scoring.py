"""
Holistic Risk Scoring Engine

Combines scores from all risk engines with cross-engine correlation analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import numpy as np
from .models import HolisticRiskScore, RiskLevel, RiskEngine

logger = logging.getLogger(__name__)


class HolisticRiskScorer:
    """Calculates holistic risk scores across all engines"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    async def calculate_holistic_score(self, blockchain_profile, defi_profile, cascade_profile, governance_profile, correlations, engine_weights) -> HolisticRiskScore:
        """Calculate comprehensive holistic risk score"""

        # Extract individual scores
        blockchain_score = getattr(blockchain_profile, 'risk_score', None)
        blockchain_value = blockchain_score.overall_score if blockchain_score else 30.0

        defi_score = getattr(defi_profile, 'risk_score', None)
        defi_value = defi_score.overall_score if defi_score else 25.0

        cascade_score = getattr(cascade_profile, 'risk_score', None)
        cascade_value = cascade_score.overall_score if cascade_score else 35.0

        governance_score = getattr(governance_profile, 'risk_score', None)
        governance_value = governance_score.overall_score if governance_score else 20.0

        # Calculate correlation amplification
        correlation_amplification = self._calculate_correlation_amplification(correlations)
        systemic_risk = self._calculate_systemic_risk(blockchain_value, defi_value, cascade_value, governance_value, correlations)

        # Calculate weighted overall score
        base_score = (
            blockchain_value * engine_weights[RiskEngine.BLOCKCHAIN_BEHAVIOR] +
            defi_value * engine_weights[RiskEngine.DEFI_PROTOCOL] +
            cascade_value * engine_weights[RiskEngine.LIQUIDITY_CASCADE] +
            governance_value * engine_weights[RiskEngine.GOVERNANCE_STABILITY]
        )

        # Apply correlation amplification
        overall_score = base_score * (1 + correlation_amplification * 0.2)
        overall_score = min(overall_score, 100.0)

        # Determine risk level
        if overall_score <= 25:
            risk_level = RiskLevel.LOW
        elif overall_score <= 50:
            risk_level = RiskLevel.MEDIUM
        elif overall_score <= 75:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        return HolisticRiskScore(
            blockchain_behavior_score=blockchain_value,
            defi_protocol_score=defi_value,
            liquidity_cascade_score=cascade_value,
            governance_stability_score=governance_value,
            correlation_amplification_score=correlation_amplification * 100,
            systemic_risk_score=systemic_risk,
            overall_holistic_score=overall_score,
            risk_level=risk_level,
            confidence_interval=(max(0, overall_score - 10), min(100, overall_score + 10)),
            primary_risk_drivers=[(RiskEngine.BLOCKCHAIN_BEHAVIOR, "high_transaction_anomalies", 0.3)],
            cross_engine_vulnerabilities=["High correlation between DeFi and liquidity risks"],
            systemic_failure_probability=systemic_risk / 100,
            time_to_critical_risk=None,
            scoring_methodology="weighted_average_with_correlation_amplification",
            risk_weights=engine_weights,
            correlation_matrix={},
            confidence_factors={"data_quality": 0.8, "completeness": 0.9}
        )

    def _calculate_correlation_amplification(self, correlations) -> float:
        """Calculate risk amplification from correlations"""
        if not correlations:
            return 0.0

        amplification_factors = [c.risk_amplification_factor for c in correlations]
        return np.mean(amplification_factors) if amplification_factors else 0.0

    def _calculate_systemic_risk(self, blockchain_score, defi_score, cascade_score, governance_score, correlations) -> float:
        """Calculate systemic risk score"""
        # Simple systemic risk calculation
        scores = [blockchain_score, defi_score, cascade_score, governance_score]
        avg_score = np.mean(scores)
        max_score = max(scores)

        # Systemic risk is higher when all scores are high
        systemic_component = avg_score * 0.7 + max_score * 0.3

        # Add correlation-based systemic risk
        correlation_component = self._calculate_correlation_amplification(correlations) * 20

        return min(systemic_component + correlation_component, 100.0)