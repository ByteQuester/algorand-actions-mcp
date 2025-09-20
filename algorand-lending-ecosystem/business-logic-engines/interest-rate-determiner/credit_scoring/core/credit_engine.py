"""
Credit Scoring Engine

Advanced credit scoring system that combines traditional credit metrics with
blockchain-based behavioral data and DeFi participation patterns.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class TraditionalCreditData:
    """Traditional credit data"""
    credit_score: Optional[int] = None
    credit_history_length_months: Optional[int] = None
    open_accounts: Optional[int] = None
    credit_utilization: Optional[float] = None
    payment_history_score: Optional[float] = None
    debt_to_income_ratio: Optional[float] = None
    bankruptcies: Optional[int] = None
    foreclosures: Optional[int] = None


@dataclass
class BlockchainCreditData:
    """Blockchain-based credit data"""
    wallet_address: str
    wallet_age_days: Optional[int] = None
    transaction_count: Optional[int] = None
    average_balance: Optional[Decimal] = None
    staking_participation: Optional[bool] = None
    governance_participation: Optional[bool] = None
    defi_protocol_count: Optional[int] = None
    lending_history: Optional[List[Dict[str, Any]]] = None
    liquidation_events: Optional[int] = None
    smart_contract_interactions: Optional[int] = None


@dataclass
class BehavioralCreditData:
    """Behavioral credit patterns"""
    transaction_regularity: Optional[float] = None
    average_transaction_size: Optional[Decimal] = None
    volatility_comfort: Optional[float] = None
    long_term_holding_pattern: Optional[bool] = None
    diversification_score: Optional[float] = None
    risk_taking_behavior: Optional[str] = None
    social_reputation_score: Optional[float] = None


@dataclass
class CreditScore:
    """Complete credit score result"""
    overall_score: int  # 300-850 scale
    traditional_score: Optional[int]
    blockchain_score: int
    behavioral_score: int
    confidence_level: float
    score_factors: Dict[str, float]
    positive_factors: List[str]
    negative_factors: List[str]
    recommendations: List[str]
    risk_level: str
    score_timestamp: datetime


class CreditScoringEngine:
    """
    Advanced credit scoring engine combining traditional and blockchain metrics
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.scoring_weights = self.config.get('scoring_weights', {
            'traditional': 0.4,
            'blockchain': 0.35,
            'behavioral': 0.25
        })

        # Score ranges for different components
        self.score_ranges = {
            'excellent': (750, 850),
            'good': (700, 749),
            'fair': (650, 699),
            'poor': (550, 649),
            'bad': (300, 549)
        }

    async def calculate_credit_score(self, traditional_data: Optional[TraditionalCreditData],
                                   blockchain_data: BlockchainCreditData,
                                   behavioral_data: Optional[BehavioralCreditData]) -> CreditScore:
        """
        Calculate comprehensive credit score

        Args:
            traditional_data: Traditional credit bureau data
            blockchain_data: Blockchain transaction and participation data
            behavioral_data: Behavioral patterns and preferences

        Returns:
            CreditScore with detailed breakdown
        """
        try:
            logger.info(f"Calculating credit score for wallet {blockchain_data.wallet_address}")

            # Calculate individual score components
            traditional_score = await self._calculate_traditional_score(traditional_data)
            blockchain_score = await self._calculate_blockchain_score(blockchain_data)
            behavioral_score = await self._calculate_behavioral_score(behavioral_data)

            # Calculate weighted overall score
            overall_score = self._calculate_overall_score(traditional_score, blockchain_score, behavioral_score)

            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)

            # Calculate confidence level
            confidence = self._calculate_confidence(traditional_data, blockchain_data, behavioral_data)

            # Identify score factors
            score_factors = self._analyze_score_factors(traditional_data, blockchain_data, behavioral_data)
            positive_factors = self._identify_positive_factors(traditional_data, blockchain_data, behavioral_data)
            negative_factors = self._identify_negative_factors(traditional_data, blockchain_data, behavioral_data)

            # Generate recommendations
            recommendations = self._generate_recommendations(overall_score, negative_factors)

            credit_score = CreditScore(
                overall_score=overall_score,
                traditional_score=traditional_score,
                blockchain_score=blockchain_score,
                behavioral_score=behavioral_score,
                confidence_level=confidence,
                score_factors=score_factors,
                positive_factors=positive_factors,
                negative_factors=negative_factors,
                recommendations=recommendations,
                risk_level=risk_level,
                score_timestamp=datetime.now()
            )

            logger.info(f"Credit score calculated: {overall_score} ({risk_level})")
            return credit_score

        except Exception as e:
            logger.error(f"Error calculating credit score: {e}")
            raise

    async def _calculate_traditional_score(self, data: Optional[TraditionalCreditData]) -> Optional[int]:
        """Calculate traditional credit score component"""
        if not data:
            return None

        # Start with base score
        score = 500

        # Credit score factor (most important)
        if data.credit_score is not None:
            return data.credit_score  # Use existing credit score if available

        # Payment history (35% of traditional score)
        if data.payment_history_score is not None:
            score += int((data.payment_history_score - 0.5) * 200)

        # Credit utilization (30% of traditional score)
        if data.credit_utilization is not None:
            if data.credit_utilization < 0.1:  # <10% utilization
                score += 50
            elif data.credit_utilization < 0.3:  # <30% utilization
                score += 20
            elif data.credit_utilization > 0.7:  # >70% utilization
                score -= 100

        # Credit history length (15% of traditional score)
        if data.credit_history_length_months is not None:
            if data.credit_history_length_months > 120:  # >10 years
                score += 40
            elif data.credit_history_length_months > 60:  # >5 years
                score += 20
            elif data.credit_history_length_months < 12:  # <1 year
                score -= 30

        # Types of credit (10% of traditional score)
        if data.open_accounts is not None:
            if 3 <= data.open_accounts <= 10:
                score += 20
            elif data.open_accounts > 15:
                score -= 20

        # New credit (10% of traditional score)
        # This would typically look at recent inquiries, but we'll approximate

        # Negative factors
        if data.bankruptcies and data.bankruptcies > 0:
            score -= 150 * data.bankruptcies

        if data.foreclosures and data.foreclosures > 0:
            score -= 100 * data.foreclosures

        # Debt to income ratio
        if data.debt_to_income_ratio is not None:
            if data.debt_to_income_ratio > 0.5:
                score -= 50
            elif data.debt_to_income_ratio < 0.2:
                score += 25

        return max(300, min(850, score))

    async def _calculate_blockchain_score(self, data: BlockchainCreditData) -> int:
        """Calculate blockchain-based credit score component"""
        score = 500  # Start with neutral score

        # Wallet age factor
        if data.wallet_age_days is not None:
            if data.wallet_age_days > 730:  # >2 years
                score += 50
            elif data.wallet_age_days > 365:  # >1 year
                score += 30
            elif data.wallet_age_days > 180:  # >6 months
                score += 15
            elif data.wallet_age_days < 30:  # <1 month
                score -= 30

        # Transaction history
        if data.transaction_count is not None:
            if data.transaction_count > 1000:
                score += 40
            elif data.transaction_count > 500:
                score += 25
            elif data.transaction_count > 100:
                score += 15
            elif data.transaction_count < 10:
                score -= 20

        # Average balance (financial stability)
        if data.average_balance is not None:
            if data.average_balance > Decimal('100000'):
                score += 60
            elif data.average_balance > Decimal('10000'):
                score += 40
            elif data.average_balance > Decimal('1000'):
                score += 20
            elif data.average_balance < Decimal('100'):
                score -= 25

        # Staking participation (long-term commitment)
        if data.staking_participation:
            score += 25

        # Governance participation (community involvement)
        if data.governance_participation:
            score += 20

        # DeFi experience
        if data.defi_protocol_count is not None:
            if data.defi_protocol_count > 10:
                score += 30
            elif data.defi_protocol_count > 5:
                score += 20
            elif data.defi_protocol_count > 2:
                score += 10

        # Lending history analysis
        if data.lending_history:
            successful_loans = sum(1 for loan in data.lending_history if loan.get('status') == 'completed')
            total_loans = len(data.lending_history)
            if total_loans > 0:
                success_rate = successful_loans / total_loans
                if success_rate > 0.9:
                    score += 40
                elif success_rate > 0.8:
                    score += 25
                elif success_rate < 0.7:
                    score -= 30

        # Liquidation events (negative factor)
        if data.liquidation_events is not None and data.liquidation_events > 0:
            score -= 50 * data.liquidation_events

        # Smart contract interactions (technical sophistication)
        if data.smart_contract_interactions is not None:
            if data.smart_contract_interactions > 100:
                score += 20
            elif data.smart_contract_interactions > 50:
                score += 10

        return max(300, min(850, score))

    async def _calculate_behavioral_score(self, data: Optional[BehavioralCreditData]) -> int:
        """Calculate behavioral credit score component"""
        if not data:
            return 500  # Neutral score if no behavioral data

        score = 500

        # Transaction regularity (consistent behavior)
        if data.transaction_regularity is not None:
            if data.transaction_regularity > 0.8:
                score += 30
            elif data.transaction_regularity > 0.6:
                score += 15
            elif data.transaction_regularity < 0.3:
                score -= 20

        # Risk taking behavior
        if data.risk_taking_behavior:
            risk_behavior = data.risk_taking_behavior.lower()
            if risk_behavior == 'conservative':
                score += 25
            elif risk_behavior == 'moderate':
                score += 10
            elif risk_behavior == 'aggressive':
                score -= 15
            elif risk_behavior == 'reckless':
                score -= 40

        # Long-term holding pattern (stability)
        if data.long_term_holding_pattern:
            score += 20

        # Diversification score (risk management)
        if data.diversification_score is not None:
            if data.diversification_score > 0.7:
                score += 25
            elif data.diversification_score < 0.3:
                score -= 15

        # Volatility comfort (market understanding)
        if data.volatility_comfort is not None:
            if 0.4 <= data.volatility_comfort <= 0.7:  # Balanced comfort
                score += 15
            elif data.volatility_comfort > 0.9:  # Too risk-seeking
                score -= 20
            elif data.volatility_comfort < 0.2:  # Too risk-averse
                score -= 10

        # Social reputation score
        if data.social_reputation_score is not None:
            if data.social_reputation_score > 0.8:
                score += 20
            elif data.social_reputation_score < 0.4:
                score -= 15

        # Average transaction size (spending patterns)
        if data.average_transaction_size is not None:
            if Decimal('100') <= data.average_transaction_size <= Decimal('10000'):
                score += 10  # Reasonable transaction sizes

        return max(300, min(850, score))

    def _calculate_overall_score(self, traditional_score: Optional[int],
                               blockchain_score: int, behavioral_score: int) -> int:
        """Calculate weighted overall credit score"""
        scores = []
        weights = []

        if traditional_score is not None:
            scores.append(traditional_score)
            weights.append(self.scoring_weights['traditional'])

        scores.append(blockchain_score)
        weights.append(self.scoring_weights['blockchain'])

        scores.append(behavioral_score)
        weights.append(self.scoring_weights['behavioral'])

        # Normalize weights if traditional score is missing
        if traditional_score is None:
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

        # Calculate weighted average
        overall_score = sum(score * weight for score, weight in zip(scores, weights))

        return int(max(300, min(850, overall_score)))

    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level from credit score"""
        for level, (min_score, max_score) in self.score_ranges.items():
            if min_score <= score <= max_score:
                return level
        return 'unknown'

    def _calculate_confidence(self, traditional_data: Optional[TraditionalCreditData],
                            blockchain_data: BlockchainCreditData,
                            behavioral_data: Optional[BehavioralCreditData]) -> float:
        """Calculate confidence in credit score"""
        confidence = 0.3  # Base confidence

        # Traditional data availability
        if traditional_data:
            if traditional_data.credit_score is not None:
                confidence += 0.3
            if traditional_data.payment_history_score is not None:
                confidence += 0.1
            if traditional_data.credit_utilization is not None:
                confidence += 0.1

        # Blockchain data quality
        if blockchain_data.wallet_age_days and blockchain_data.wallet_age_days > 90:
            confidence += 0.1
        if blockchain_data.transaction_count and blockchain_data.transaction_count > 50:
            confidence += 0.1
        if blockchain_data.lending_history:
            confidence += 0.1

        # Behavioral data availability
        if behavioral_data:
            confidence += 0.1

        return min(confidence, 1.0)

    def _analyze_score_factors(self, traditional_data: Optional[TraditionalCreditData],
                             blockchain_data: BlockchainCreditData,
                             behavioral_data: Optional[BehavioralCreditData]) -> Dict[str, float]:
        """Analyze factors contributing to credit score"""
        factors = {}

        if traditional_data:
            factors['traditional_credit'] = 0.4 if traditional_data.credit_score else 0.3

        factors['blockchain_history'] = 0.35
        factors['behavioral_patterns'] = 0.25

        # Specific sub-factors
        if blockchain_data.wallet_age_days and blockchain_data.wallet_age_days > 365:
            factors['wallet_maturity'] = 0.1

        if blockchain_data.staking_participation:
            factors['staking_commitment'] = 0.05

        if behavioral_data and behavioral_data.risk_taking_behavior == 'conservative':
            factors['risk_management'] = 0.08

        return factors

    def _identify_positive_factors(self, traditional_data: Optional[TraditionalCreditData],
                                 blockchain_data: BlockchainCreditData,
                                 behavioral_data: Optional[BehavioralCreditData]) -> List[str]:
        """Identify positive credit factors"""
        positive_factors = []

        if traditional_data:
            if traditional_data.credit_score and traditional_data.credit_score > 700:
                positive_factors.append("Excellent traditional credit score")
            if traditional_data.credit_utilization and traditional_data.credit_utilization < 0.3:
                positive_factors.append("Low credit utilization")

        if blockchain_data.wallet_age_days and blockchain_data.wallet_age_days > 365:
            positive_factors.append("Mature wallet with long history")

        if blockchain_data.staking_participation:
            positive_factors.append("Active staking participation")

        if blockchain_data.governance_participation:
            positive_factors.append("Governance participation")

        if blockchain_data.lending_history:
            successful_loans = sum(1 for loan in blockchain_data.lending_history if loan.get('status') == 'completed')
            if successful_loans > 0:
                positive_factors.append("Successful lending history")

        if behavioral_data:
            if behavioral_data.diversification_score and behavioral_data.diversification_score > 0.7:
                positive_factors.append("Well-diversified portfolio")
            if behavioral_data.long_term_holding_pattern:
                positive_factors.append("Long-term investment approach")

        return positive_factors

    def _identify_negative_factors(self, traditional_data: Optional[TraditionalCreditData],
                                 blockchain_data: BlockchainCreditData,
                                 behavioral_data: Optional[BehavioralCreditData]) -> List[str]:
        """Identify negative credit factors"""
        negative_factors = []

        if traditional_data:
            if traditional_data.credit_score and traditional_data.credit_score < 650:
                negative_factors.append("Low traditional credit score")
            if traditional_data.bankruptcies and traditional_data.bankruptcies > 0:
                negative_factors.append("Previous bankruptcy")
            if traditional_data.debt_to_income_ratio and traditional_data.debt_to_income_ratio > 0.5:
                negative_factors.append("High debt-to-income ratio")

        if blockchain_data.wallet_age_days and blockchain_data.wallet_age_days < 90:
            negative_factors.append("New wallet with limited history")

        if blockchain_data.liquidation_events and blockchain_data.liquidation_events > 0:
            negative_factors.append("Previous liquidation events")

        if blockchain_data.transaction_count and blockchain_data.transaction_count < 20:
            negative_factors.append("Limited transaction history")

        if behavioral_data:
            if behavioral_data.risk_taking_behavior == 'reckless':
                negative_factors.append("Reckless risk-taking behavior")
            if behavioral_data.diversification_score and behavioral_data.diversification_score < 0.3:
                negative_factors.append("Poor portfolio diversification")

        return negative_factors

    def _generate_recommendations(self, score: int, negative_factors: List[str]) -> List[str]:
        """Generate recommendations for credit improvement"""
        recommendations = []

        if score < 650:
            recommendations.append("Focus on building consistent payment history")
            recommendations.append("Consider starting with smaller loan amounts")

        if "Limited transaction history" in negative_factors:
            recommendations.append("Increase blockchain transaction activity")

        if "New wallet with limited history" in negative_factors:
            recommendations.append("Build wallet history through regular transactions")
            recommendations.append("Consider participating in governance and staking")

        if "Poor portfolio diversification" in negative_factors:
            recommendations.append("Diversify digital asset holdings")

        if "Reckless risk-taking behavior" in negative_factors:
            recommendations.append("Demonstrate more conservative investment patterns")

        if score > 750:
            recommendations.append("Excellent credit profile - eligible for premium rates")

        return recommendations