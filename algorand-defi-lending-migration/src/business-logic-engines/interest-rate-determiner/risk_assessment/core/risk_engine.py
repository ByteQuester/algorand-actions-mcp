"""
Risk Assessment Engine

Evaluates various risk factors and calculates appropriate risk premiums for interest rates.
Analyzes credit risk, market risk, operational risk, and Algorand-specific risks.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class BorrowerProfile:
    """Borrower risk profile data"""
    borrower_id: str
    credit_score: Optional[int] = None
    debt_to_income_ratio: Optional[float] = None
    employment_status: Optional[str] = None
    annual_income: Optional[Decimal] = None
    payment_history: Optional[List[Dict[str, Any]]] = None
    collateral_portfolio: Optional[Dict[str, Decimal]] = None
    algorand_wallet_age: Optional[int] = None  # days
    defi_experience_score: Optional[float] = None
    governance_participation: Optional[bool] = None


@dataclass
class MarketRiskFactors:
    """Market-related risk factors"""
    asset_volatility: float
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    liquidity_risk: float = 0.5
    regulatory_risk: float = 0.3
    technology_risk: float = 0.2
    smart_contract_risk: float = 0.1


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    overall_risk_level: RiskLevel
    risk_premium: Decimal
    risk_score: float  # 0-100 scale
    credit_risk_score: float
    market_risk_score: float
    operational_risk_score: float
    risk_factors: List[str]
    mitigation_recommendations: List[str]
    confidence: float
    assessment_timestamp: datetime
    risk_breakdown: Dict[str, float]


class RiskAssessmentEngine:
    """
    Engine for comprehensive risk assessment and premium calculation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.risk_weights = self.config.get('risk_weights', {
            'credit_risk': 0.4,
            'market_risk': 0.35,
            'operational_risk': 0.25
        })
        self.premium_multipliers = {
            RiskLevel.VERY_LOW: Decimal('0.5'),
            RiskLevel.LOW: Decimal('1.0'),
            RiskLevel.MEDIUM: Decimal('1.5'),
            RiskLevel.HIGH: Decimal('2.5'),
            RiskLevel.VERY_HIGH: Decimal('4.0')
        }
        self.base_premium = Decimal('0.02')  # 2% base risk premium

    async def assess_risk(self, borrower_profile: BorrowerProfile,
                         market_factors: MarketRiskFactors,
                         loan_amount: Decimal,
                         loan_duration_days: int) -> RiskAssessment:
        """
        Perform comprehensive risk assessment

        Args:
            borrower_profile: Borrower's risk profile
            market_factors: Current market risk factors
            loan_amount: Requested loan amount
            loan_duration_days: Loan duration in days

        Returns:
            RiskAssessment with calculated premium
        """
        try:
            logger.info(f"Starting risk assessment for borrower {borrower_profile.borrower_id}")

            # Assess individual risk components
            credit_risk = await self._assess_credit_risk(borrower_profile, loan_amount)
            market_risk = await self._assess_market_risk(market_factors, loan_amount, loan_duration_days)
            operational_risk = await self._assess_operational_risk(borrower_profile, market_factors)

            # Calculate overall risk score
            overall_score = self._calculate_overall_risk_score(credit_risk, market_risk, operational_risk)

            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)

            # Calculate risk premium
            risk_premium = self._calculate_risk_premium(risk_level, overall_score, loan_amount, loan_duration_days)

            # Identify risk factors and recommendations
            risk_factors = self._identify_risk_factors(borrower_profile, market_factors, overall_score)
            recommendations = self._generate_mitigation_recommendations(risk_factors, risk_level)

            # Calculate confidence
            confidence = self._calculate_confidence(borrower_profile, market_factors)

            # Create risk breakdown
            risk_breakdown = {
                'credit_risk': credit_risk,
                'market_risk': market_risk,
                'operational_risk': operational_risk,
                'overall_score': overall_score
            }

            assessment = RiskAssessment(
                overall_risk_level=risk_level,
                risk_premium=risk_premium,
                risk_score=overall_score,
                credit_risk_score=credit_risk,
                market_risk_score=market_risk,
                operational_risk_score=operational_risk,
                risk_factors=risk_factors,
                mitigation_recommendations=recommendations,
                confidence=confidence,
                assessment_timestamp=datetime.now(),
                risk_breakdown=risk_breakdown
            )

            logger.info(f"Risk assessment completed. Risk level: {risk_level.value}, Premium: {risk_premium:.4%}")
            return assessment

        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            raise

    async def _assess_credit_risk(self, borrower_profile: BorrowerProfile, loan_amount: Decimal) -> float:
        """Assess credit-related risks (0-100 scale)"""
        credit_score = 50.0  # Default moderate risk

        # Credit score impact
        if borrower_profile.credit_score is not None:
            if borrower_profile.credit_score >= 750:
                credit_score -= 20
            elif borrower_profile.credit_score >= 700:
                credit_score -= 10
            elif borrower_profile.credit_score >= 650:
                credit_score -= 5
            elif borrower_profile.credit_score < 600:
                credit_score += 25
            elif borrower_profile.credit_score < 550:
                credit_score += 40

        # Debt-to-income ratio impact
        if borrower_profile.debt_to_income_ratio is not None:
            if borrower_profile.debt_to_income_ratio > 0.5:
                credit_score += 15
            elif borrower_profile.debt_to_income_ratio > 0.3:
                credit_score += 5
            elif borrower_profile.debt_to_income_ratio < 0.2:
                credit_score -= 5

        # Employment status impact
        if borrower_profile.employment_status:
            if borrower_profile.employment_status.lower() in ['employed', 'self-employed']:
                credit_score -= 5
            elif borrower_profile.employment_status.lower() == 'unemployed':
                credit_score += 20

        # Payment history impact
        if borrower_profile.payment_history:
            late_payments = sum(1 for payment in borrower_profile.payment_history
                              if payment.get('status') == 'late')
            total_payments = len(borrower_profile.payment_history)
            if total_payments > 0:
                late_ratio = late_payments / total_payments
                credit_score += late_ratio * 30

        # DeFi experience impact
        if borrower_profile.defi_experience_score is not None:
            if borrower_profile.defi_experience_score > 0.8:
                credit_score -= 10
            elif borrower_profile.defi_experience_score < 0.3:
                credit_score += 10

        # Algorand wallet age impact
        if borrower_profile.algorand_wallet_age is not None:
            if borrower_profile.algorand_wallet_age > 365:  # > 1 year
                credit_score -= 5
            elif borrower_profile.algorand_wallet_age < 30:  # < 1 month
                credit_score += 10

        return max(0, min(100, credit_score))

    async def _assess_market_risk(self, market_factors: MarketRiskFactors,
                                loan_amount: Decimal, loan_duration_days: int) -> float:
        """Assess market-related risks (0-100 scale)"""
        market_score = 30.0  # Default low-moderate risk

        # Asset volatility impact
        volatility_impact = market_factors.asset_volatility * 50
        market_score += volatility_impact

        # Liquidity risk impact
        liquidity_impact = market_factors.liquidity_risk * 20
        market_score += liquidity_impact

        # Regulatory risk impact
        regulatory_impact = market_factors.regulatory_risk * 15
        market_score += regulatory_impact

        # Technology risk impact
        tech_impact = market_factors.technology_risk * 10
        market_score += tech_impact

        # Smart contract risk impact
        contract_impact = market_factors.smart_contract_risk * 25
        market_score += contract_impact

        # Duration impact (longer loans = higher market risk)
        if loan_duration_days > 365 * 3:  # > 3 years
            market_score += 15
        elif loan_duration_days > 365:  # > 1 year
            market_score += 10
        elif loan_duration_days > 180:  # > 6 months
            market_score += 5

        # Loan size impact (larger loans = higher market risk)
        if loan_amount > Decimal('1000000'):  # > 1M
            market_score += 10
        elif loan_amount > Decimal('100000'):  # > 100K
            market_score += 5

        return max(0, min(100, market_score))

    async def _assess_operational_risk(self, borrower_profile: BorrowerProfile,
                                     market_factors: MarketRiskFactors) -> float:
        """Assess operational risks (0-100 scale)"""
        operational_score = 25.0  # Default low risk

        # Smart contract risk
        operational_score += market_factors.smart_contract_risk * 30

        # Technology risk
        operational_score += market_factors.technology_risk * 20

        # Governance participation (positive factor)
        if borrower_profile.governance_participation:
            operational_score -= 5

        # DeFi experience (reduces operational risk)
        if borrower_profile.defi_experience_score is not None:
            experience_reduction = borrower_profile.defi_experience_score * 10
            operational_score -= experience_reduction

        # Wallet age (older wallets = lower operational risk)
        if borrower_profile.algorand_wallet_age is not None:
            if borrower_profile.algorand_wallet_age > 365:
                operational_score -= 5
            elif borrower_profile.algorand_wallet_age > 180:
                operational_score -= 2

        return max(0, min(100, operational_score))

    def _calculate_overall_risk_score(self, credit_risk: float, market_risk: float,
                                    operational_risk: float) -> float:
        """Calculate weighted overall risk score"""
        overall_score = (
            credit_risk * self.risk_weights['credit_risk'] +
            market_risk * self.risk_weights['market_risk'] +
            operational_risk * self.risk_weights['operational_risk']
        )
        return max(0, min(100, overall_score))

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from risk score"""
        if risk_score <= 20:
            return RiskLevel.VERY_LOW
        elif risk_score <= 40:
            return RiskLevel.LOW
        elif risk_score <= 60:
            return RiskLevel.MEDIUM
        elif risk_score <= 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    def _calculate_risk_premium(self, risk_level: RiskLevel, risk_score: float,
                              loan_amount: Decimal, loan_duration_days: int) -> Decimal:
        """Calculate risk premium based on assessment"""

        # Base premium from risk level
        base_premium = self.base_premium * self.premium_multipliers[risk_level]

        # Fine-tune based on exact risk score
        score_adjustment = Decimal(str(risk_score / 100)) * Decimal('0.01')
        premium = base_premium + score_adjustment

        # Duration adjustment
        duration_years = loan_duration_days / 365
        if duration_years > 3:
            premium *= Decimal('1.2')
        elif duration_years > 1:
            premium *= Decimal('1.1')

        # Loan size adjustment
        if loan_amount > Decimal('1000000'):
            premium *= Decimal('1.15')
        elif loan_amount > Decimal('100000'):
            premium *= Decimal('1.05')

        return premium.quantize(Decimal('0.0001'))

    def _identify_risk_factors(self, borrower_profile: BorrowerProfile,
                             market_factors: MarketRiskFactors, risk_score: float) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []

        # Credit-related factors
        if borrower_profile.credit_score and borrower_profile.credit_score < 650:
            risk_factors.append("Low credit score")

        if borrower_profile.debt_to_income_ratio and borrower_profile.debt_to_income_ratio > 0.4:
            risk_factors.append("High debt-to-income ratio")

        if borrower_profile.employment_status == 'unemployed':
            risk_factors.append("Unemployment")

        # Market-related factors
        if market_factors.asset_volatility > 0.7:
            risk_factors.append("High asset volatility")

        if market_factors.liquidity_risk > 0.6:
            risk_factors.append("Limited liquidity")

        if market_factors.regulatory_risk > 0.5:
            risk_factors.append("Regulatory uncertainty")

        # Operational factors
        if market_factors.smart_contract_risk > 0.3:
            risk_factors.append("Smart contract risk")

        if borrower_profile.defi_experience_score and borrower_profile.defi_experience_score < 0.4:
            risk_factors.append("Limited DeFi experience")

        if borrower_profile.algorand_wallet_age and borrower_profile.algorand_wallet_age < 90:
            risk_factors.append("New Algorand wallet")

        # Overall risk
        if risk_score > 70:
            risk_factors.append("High overall risk profile")

        return risk_factors

    def _generate_mitigation_recommendations(self, risk_factors: List[str],
                                           risk_level: RiskLevel) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if "Low credit score" in risk_factors:
            recommendations.append("Consider additional collateral or co-signer")

        if "High debt-to-income ratio" in risk_factors:
            recommendations.append("Reduce loan amount or extend repayment term")

        if "High asset volatility" in risk_factors:
            recommendations.append("Implement dynamic interest rate adjustments")

        if "Limited liquidity" in risk_factors:
            recommendations.append("Add liquidity premium and monitoring")

        if "Smart contract risk" in risk_factors:
            recommendations.append("Use audited smart contracts and insurance")

        if "Limited DeFi experience" in risk_factors:
            recommendations.append("Provide DeFi education and lower initial limits")

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            recommendations.extend([
                "Require comprehensive due diligence",
                "Implement enhanced monitoring",
                "Consider risk-based pricing tiers"
            ])

        return recommendations

    def _calculate_confidence(self, borrower_profile: BorrowerProfile,
                            market_factors: MarketRiskFactors) -> float:
        """Calculate confidence in risk assessment"""
        confidence = 0.5  # Base confidence

        # Data completeness factors
        if borrower_profile.credit_score is not None:
            confidence += 0.15

        if borrower_profile.debt_to_income_ratio is not None:
            confidence += 0.1

        if borrower_profile.payment_history:
            confidence += 0.1

        if borrower_profile.employment_status:
            confidence += 0.05

        if borrower_profile.defi_experience_score is not None:
            confidence += 0.05

        if borrower_profile.algorand_wallet_age is not None:
            confidence += 0.05

        # Market data quality
        if hasattr(market_factors, 'data_quality_score'):
            confidence += getattr(market_factors, 'data_quality_score', 0) * 0.1

        return min(confidence, 1.0)

    def validate_risk_inputs(self, borrower_profile: BorrowerProfile,
                           market_factors: MarketRiskFactors) -> Tuple[bool, List[str]]:
        """Validate input data for risk assessment"""
        errors = []

        # Validate borrower profile
        if not borrower_profile.borrower_id:
            errors.append("Borrower ID is required")

        if borrower_profile.credit_score is not None:
            if not (300 <= borrower_profile.credit_score <= 850):
                errors.append("Credit score must be between 300 and 850")

        if borrower_profile.debt_to_income_ratio is not None:
            if not (0 <= borrower_profile.debt_to_income_ratio <= 2):
                errors.append("Debt-to-income ratio must be between 0 and 2")

        # Validate market factors
        if not (0 <= market_factors.asset_volatility <= 2):
            errors.append("Asset volatility must be between 0 and 2")

        if not (0 <= market_factors.liquidity_risk <= 1):
            errors.append("Liquidity risk must be between 0 and 1")

        return len(errors) == 0, errors