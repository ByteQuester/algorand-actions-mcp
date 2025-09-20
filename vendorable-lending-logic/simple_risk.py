"""
Simple risk assessment engine.
Ultra-minimal implementation for vendorable package.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from .models import LoanRequest, Borrower, CollateralType, RiskAssessment


class SimpleRiskEngine:
    """
    Basic risk assessment using simple heuristics.
    No ML models, no external data sources - just simple rules.
    """

    def __init__(self):
        """Initialize risk scoring parameters"""
        # Risk weights for different factors (sum to 100)
        self.risk_weights = {
            'collateral_type': 25,    # 25% weight
            'ltv_ratio': 30,          # 30% weight
            'credit_score': 20,       # 20% weight
            'loan_amount': 10,        # 10% weight
            'duration': 10,           # 10% weight
            'borrower_history': 5     # 5% weight
        }

        # Collateral type risk scores (0-100, higher is better)
        self.collateral_scores = {
            CollateralType.USDC: 95,   # Stablecoin - very low risk
            CollateralType.USDT: 90,   # Stablecoin - very low risk
            CollateralType.ALGO: 70,   # Volatile but established
            CollateralType.OTHER: 30   # Unknown asset - high risk
        }

        # LTV risk scoring (higher LTV = higher risk = lower score)
        self.ltv_score_bands = [
            (Decimal('0.30'), 100),  # 0-30% LTV: excellent
            (Decimal('0.50'), 90),   # 30-50% LTV: very good
            (Decimal('0.65'), 75),   # 50-65% LTV: good
            (Decimal('0.75'), 60),   # 65-75% LTV: fair
            (Decimal('0.85'), 40),   # 75-85% LTV: poor
            (Decimal('1.00'), 20)    # 85-100% LTV: very poor
        ]

        # Credit score bands
        self.credit_score_bands = [
            (800, 100),  # Excellent
            (750, 85),   # Very good
            (700, 70),   # Good
            (650, 50),   # Fair
            (600, 30),   # Poor
            (0, 10)      # Very poor
        ]

        # Loan amount risk (very small and very large loans are riskier)
        self.amount_score_bands = [
            (Decimal('1000'), 60),    # <$1k: small loan risk
            (Decimal('10000'), 90),   # $1k-$10k: optimal
            (Decimal('100000'), 80),  # $10k-$100k: good
            (Decimal('500000'), 60),  # $100k-$500k: large loan risk
            (Decimal('999999999'), 40) # $500k+: very large loan risk
        ]

        # Duration risk (longer loans are riskier)
        self.duration_score_bands = [
            (30, 95),    # 0-30 days: very low risk
            (90, 85),    # 30-90 days: low risk
            (180, 70),   # 90-180 days: moderate risk
            (365, 50),   # 180-365 days: higher risk
            (999999, 30) # 365+ days: high risk
        ]

    def score_collateral_type(self, collateral_type: CollateralType) -> int:
        """Score collateral type risk (0-100, higher is better)"""
        return self.collateral_scores.get(collateral_type, 30)

    def score_ltv_ratio(self, ltv_ratio: Decimal) -> int:
        """Score LTV ratio risk (0-100, higher is better)"""
        for max_ltv, score in self.ltv_score_bands:
            if ltv_ratio <= max_ltv:
                return score
        return 10  # Very high LTV

    def score_credit_score(self, credit_score: Optional[int]) -> int:
        """Score credit score (0-100, higher is better)"""
        if credit_score is None:
            return 40  # Unknown credit - moderate risk

        for min_score, risk_score in self.credit_score_bands:
            if credit_score >= min_score:
                return risk_score
        return 10  # Very poor credit

    def score_loan_amount(self, amount: Decimal) -> int:
        """Score loan amount risk (0-100, higher is better)"""
        for max_amount, score in self.amount_score_bands:
            if amount <= max_amount:
                return score
        return 40  # Very large amount

    def score_duration(self, duration_days: int) -> int:
        """Score loan duration risk (0-100, higher is better)"""
        for max_days, score in self.duration_score_bands:
            if duration_days <= max_days:
                return score
        return 30  # Very long duration

    def score_borrower_history(self, borrower: Borrower) -> int:
        """Score borrower's loan history (0-100, higher is better)"""
        if not borrower.loan_history:
            return 50  # No history - neutral

        # Simple heuristic: more loans = more experience = better score
        # In reality, you'd check for defaults, late payments, etc.
        num_loans = len(borrower.loan_history)

        if num_loans == 0:
            return 50   # No history
        elif num_loans <= 2:
            return 60   # Limited history
        elif num_loans <= 5:
            return 75   # Some history
        elif num_loans <= 10:
            return 85   # Good history
        else:
            return 90   # Extensive history

    def calculate_composite_score(self, loan_request: LoanRequest, ltv_ratio: Decimal) -> Dict[str, Any]:
        """Calculate composite risk score and component breakdown"""
        # Calculate individual scores
        collateral_score = self.score_collateral_type(loan_request.collateral.asset_type)
        ltv_score = self.score_ltv_ratio(ltv_ratio)
        credit_score = self.score_credit_score(loan_request.borrower.credit_score)
        amount_score = self.score_loan_amount(loan_request.requested_amount)
        duration_score = self.score_duration(loan_request.duration_days)
        history_score = self.score_borrower_history(loan_request.borrower)

        # Calculate weighted composite score
        composite_score = (
            collateral_score * self.risk_weights['collateral_type'] +
            ltv_score * self.risk_weights['ltv_ratio'] +
            credit_score * self.risk_weights['credit_score'] +
            amount_score * self.risk_weights['loan_amount'] +
            duration_score * self.risk_weights['duration'] +
            history_score * self.risk_weights['borrower_history']
        ) / 100

        return {
            'composite_score': int(composite_score),
            'components': {
                'collateral_type': collateral_score,
                'ltv_ratio': ltv_score,
                'credit_score': credit_score,
                'loan_amount': amount_score,
                'duration': duration_score,
                'borrower_history': history_score
            },
            'weights': self.risk_weights.copy()
        }

    def assess_risk(self, loan_request: LoanRequest, ltv_ratio: Decimal) -> RiskAssessment:
        """Perform complete risk assessment"""
        score_data = self.calculate_composite_score(loan_request, ltv_ratio)
        composite_score = score_data['composite_score']

        # Determine risk level and recommendation
        if composite_score >= 80:
            recommendation = "APPROVE - Low risk, excellent borrower profile"
        elif composite_score >= 65:
            recommendation = "APPROVE - Moderate risk, good borrower profile"
        elif composite_score >= 50:
            recommendation = "CONDITIONAL - Higher risk, consider with conditions"
        elif composite_score >= 35:
            recommendation = "CAUTION - High risk, require additional guarantees"
        else:
            recommendation = "REJECT - Very high risk, not suitable for lending"

        # Add specific risk factors
        risk_factors = self._identify_risk_factors(loan_request, ltv_ratio, score_data)

        return RiskAssessment(
            score=composite_score,
            factors=risk_factors,
            recommendation=recommendation
        )

    def _identify_risk_factors(self, loan_request: LoanRequest, ltv_ratio: Decimal, score_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify specific risk factors"""
        factors = {
            'ltv_ratio': float(ltv_ratio),
            'collateral_type': loan_request.collateral.asset_type.value,
            'loan_amount': float(loan_request.requested_amount),
            'duration_days': loan_request.duration_days,
            'credit_score': loan_request.borrower.credit_score,
            'component_scores': score_data['components'],
            'risk_flags': []
        }

        # Identify risk flags
        if ltv_ratio > Decimal('0.80'):
            factors['risk_flags'].append("High LTV ratio")

        if loan_request.collateral.asset_type == CollateralType.OTHER:
            factors['risk_flags'].append("Unknown collateral type")

        if loan_request.borrower.credit_score and loan_request.borrower.credit_score < 650:
            factors['risk_flags'].append("Poor credit score")

        if loan_request.requested_amount > Decimal('100000'):
            factors['risk_flags'].append("Large loan amount")

        if loan_request.duration_days > 180:
            factors['risk_flags'].append("Long loan duration")

        if not loan_request.borrower.loan_history:
            factors['risk_flags'].append("No borrowing history")

        return factors

    def get_risk_recommendations(self, risk_assessment: RiskAssessment) -> List[str]:
        """Get specific recommendations based on risk assessment"""
        recommendations = []

        if risk_assessment.score < 50:
            recommendations.append("Consider rejecting this loan application")

        if 'High LTV ratio' in risk_assessment.factors.get('risk_flags', []):
            recommendations.append("Require additional collateral or lower loan amount")

        if 'Poor credit score' in risk_assessment.factors.get('risk_flags', []):
            recommendations.append("Increase interest rate or require co-signer")

        if 'Large loan amount' in risk_assessment.factors.get('risk_flags', []):
            recommendations.append("Implement staged disbursement")

        if 'Long loan duration' in risk_assessment.factors.get('risk_flags', []):
            recommendations.append("Consider shorter loan term")

        if 'No borrowing history' in risk_assessment.factors.get('risk_flags', []):
            recommendations.append("Start with smaller loan amount")

        if not recommendations:
            recommendations.append("Loan appears suitable for approval")

        return recommendations

    def simulate_risk_scenarios(self, loan_request: LoanRequest, ltv_ratio: Decimal) -> Dict[str, RiskAssessment]:
        """Simulate different risk scenarios"""
        scenarios = {}

        # Current scenario
        scenarios['current'] = self.assess_risk(loan_request, ltv_ratio)

        # Lower LTV scenario
        lower_ltv = ltv_ratio * Decimal('0.8')
        scenarios['lower_ltv'] = self.assess_risk(loan_request, lower_ltv)

        # Higher LTV scenario
        higher_ltv = min(ltv_ratio * Decimal('1.2'), Decimal('0.95'))
        scenarios['higher_ltv'] = self.assess_risk(loan_request, higher_ltv)

        return scenarios