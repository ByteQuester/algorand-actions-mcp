"""
Simple interest rate calculation engine.
Ultra-minimal implementation for vendorable package.
"""

from decimal import Decimal
from typing import Dict, Optional
from .models import CollateralType, LoanRequest, Borrower


class SimpleRatesEngine:
    """
    Basic interest rate calculation based on risk factors.
    No external dependencies, simple rule-based pricing.
    """

    def __init__(self):
        """Initialize with base rates and risk premiums"""
        # Base interest rates by collateral type (annual %)
        self.base_rates = {
            CollateralType.ALGO: Decimal('8.0'),   # 8% base for ALGO
            CollateralType.USDC: Decimal('5.0'),   # 5% base for USDC
            CollateralType.USDT: Decimal('5.0'),   # 5% base for USDT
            CollateralType.OTHER: Decimal('12.0')  # 12% base for others
        }

        # Risk premiums based on LTV ratio
        self.ltv_premiums = [
            (Decimal('0.50'), Decimal('0.0')),   # 0-50% LTV: no premium
            (Decimal('0.65'), Decimal('1.0')),   # 50-65% LTV: +1%
            (Decimal('0.75'), Decimal('2.0')),   # 65-75% LTV: +2%
            (Decimal('0.85'), Decimal('3.5')),   # 75-85% LTV: +3.5%
            (Decimal('1.00'), Decimal('5.0'))    # 85-100% LTV: +5%
        ]

        # Credit score premiums (if available)
        self.credit_score_adjustments = [
            (800, Decimal('-1.0')),  # Excellent: -1%
            (750, Decimal('-0.5')),  # Good: -0.5%
            (700, Decimal('0.0')),   # Fair: no adjustment
            (650, Decimal('0.5')),   # Poor: +0.5%
            (600, Decimal('1.0')),   # Bad: +1%
            (0, Decimal('2.0'))      # Very bad: +2%
        ]

        # Duration premiums (longer loans = higher rates)
        self.duration_premiums = [
            (30, Decimal('0.0')),    # 0-30 days: no premium
            (90, Decimal('0.25')),   # 30-90 days: +0.25%
            (180, Decimal('0.5')),   # 90-180 days: +0.5%
            (365, Decimal('1.0')),   # 180-365 days: +1%
            (999999, Decimal('2.0')) # 365+ days: +2%
        ]

        # Loan amount premiums (smaller loans = higher rates due to fixed costs)
        self.amount_premiums = [
            (Decimal('10000'), Decimal('1.5')),  # <$10k: +1.5%
            (Decimal('50000'), Decimal('0.5')),  # $10k-$50k: +0.5%
            (Decimal('999999'), Decimal('0.0'))  # $50k+: no premium
        ]

    def get_base_rate(self, collateral_type: CollateralType) -> Decimal:
        """Get base interest rate for collateral type"""
        return self.base_rates.get(collateral_type, Decimal('10.0'))

    def calculate_ltv_premium(self, ltv_ratio: Decimal) -> Decimal:
        """Calculate premium based on LTV ratio"""
        for max_ltv, premium in self.ltv_premiums:
            if ltv_ratio <= max_ltv:
                return premium
        return self.ltv_premiums[-1][1]  # Return highest premium if LTV is very high

    def calculate_credit_premium(self, credit_score: Optional[int]) -> Decimal:
        """Calculate premium based on credit score"""
        if credit_score is None:
            return Decimal('1.0')  # Default premium for unknown credit

        for min_score, adjustment in self.credit_score_adjustments:
            if credit_score >= min_score:
                return adjustment
        return self.credit_score_adjustments[-1][1]  # Return worst adjustment

    def calculate_duration_premium(self, duration_days: int) -> Decimal:
        """Calculate premium based on loan duration"""
        for max_days, premium in self.duration_premiums:
            if duration_days <= max_days:
                return premium
        return self.duration_premiums[-1][1]  # Return highest premium

    def calculate_amount_premium(self, loan_amount: Decimal) -> Decimal:
        """Calculate premium based on loan amount"""
        for max_amount, premium in self.amount_premiums:
            if loan_amount <= max_amount:
                return premium
        return self.amount_premiums[-1][1]  # Return lowest premium for large amounts

    def calculate_interest_rate(self, loan_request: LoanRequest, ltv_ratio: Decimal) -> Decimal:
        """Calculate total interest rate for loan request"""
        # Start with base rate
        base_rate = self.get_base_rate(loan_request.collateral.asset_type)

        # Add risk premiums
        ltv_premium = self.calculate_ltv_premium(ltv_ratio)
        credit_premium = self.calculate_credit_premium(loan_request.borrower.credit_score)
        duration_premium = self.calculate_duration_premium(loan_request.duration_days)
        amount_premium = self.calculate_amount_premium(loan_request.requested_amount)

        # Calculate total rate
        total_rate = base_rate + ltv_premium + credit_premium + duration_premium + amount_premium

        # Apply minimum and maximum bounds
        total_rate = max(total_rate, Decimal('3.0'))   # Minimum 3%
        total_rate = min(total_rate, Decimal('25.0'))  # Maximum 25%

        return total_rate

    def get_rate_breakdown(self, loan_request: LoanRequest, ltv_ratio: Decimal) -> Dict[str, Decimal]:
        """Get detailed breakdown of interest rate components"""
        base_rate = self.get_base_rate(loan_request.collateral.asset_type)
        ltv_premium = self.calculate_ltv_premium(ltv_ratio)
        credit_premium = self.calculate_credit_premium(loan_request.borrower.credit_score)
        duration_premium = self.calculate_duration_premium(loan_request.duration_days)
        amount_premium = self.calculate_amount_premium(loan_request.requested_amount)

        subtotal = base_rate + ltv_premium + credit_premium + duration_premium + amount_premium
        total_rate = max(min(subtotal, Decimal('25.0')), Decimal('3.0'))

        return {
            'base_rate': base_rate,
            'ltv_premium': ltv_premium,
            'credit_premium': credit_premium,
            'duration_premium': duration_premium,
            'amount_premium': amount_premium,
            'subtotal': subtotal,
            'total_rate': total_rate,
            'capped': subtotal != total_rate
        }

    def calculate_interest_amount(self, principal: Decimal, annual_rate: Decimal, duration_days: int) -> Decimal:
        """Calculate total interest amount for loan"""
        daily_rate = annual_rate / Decimal('365') / Decimal('100')
        return principal * daily_rate * Decimal(str(duration_days))

    def calculate_total_repayment(self, principal: Decimal, annual_rate: Decimal, duration_days: int) -> Decimal:
        """Calculate total amount to be repaid"""
        interest = self.calculate_interest_amount(principal, annual_rate, duration_days)
        return principal + interest

    def get_payment_schedule(self, principal: Decimal, annual_rate: Decimal, duration_days: int) -> Dict[str, Decimal]:
        """Get simple payment schedule (interest-only during term, principal at end)"""
        interest_amount = self.calculate_interest_amount(principal, annual_rate, duration_days)
        total_repayment = principal + interest_amount

        # Simple schedule: pay interest at end, principal at end
        return {
            'principal': principal,
            'interest_amount': interest_amount,
            'total_repayment': total_repayment,
            'daily_interest': interest_amount / Decimal(str(duration_days)),
            'effective_rate': (interest_amount / principal) * Decimal('100')
        }

    def update_base_rate(self, collateral_type: CollateralType, new_rate: Decimal):
        """Update base rate for testing or market conditions"""
        self.base_rates[collateral_type] = new_rate

    def simulate_rate_scenarios(self, loan_request: LoanRequest, ltv_ratio: Decimal) -> Dict[str, Dict[str, Decimal]]:
        """Simulate different rate scenarios"""
        scenarios = {}

        # Current rate
        scenarios['current'] = self.get_rate_breakdown(loan_request, ltv_ratio)

        # Lower LTV scenario
        lower_ltv = ltv_ratio * Decimal('0.8')  # 20% lower LTV
        scenarios['lower_ltv'] = self.get_rate_breakdown(loan_request, lower_ltv)

        # Better credit scenario
        if loan_request.borrower.credit_score:
            better_credit_request = LoanRequest(
                borrower=Borrower(
                    address=loan_request.borrower.address,
                    credit_score=min(loan_request.borrower.credit_score + 50, 850)
                ),
                requested_amount=loan_request.requested_amount,
                collateral=loan_request.collateral,
                duration_days=loan_request.duration_days
            )
            scenarios['better_credit'] = self.get_rate_breakdown(better_credit_request, ltv_ratio)

        return scenarios