"""
Simple collateral valuation and LTV calculation engine.
Ultra-minimal implementation for vendorable package.
"""

from decimal import Decimal
from typing import Dict, Optional
from .models import Collateral, CollateralType, LoanRequest


class SimpleCollateralEngine:
    """
    Basic collateral valuation and LTV calculation.
    No external dependencies, simple price feeds.
    """

    def __init__(self):
        """Initialize with basic price feeds and LTV limits"""
        # Simple price feeds - in production, these would come from oracles
        self.price_feeds = {
            CollateralType.ALGO: Decimal('0.15'),  # $0.15 per ALGO
            CollateralType.USDC: Decimal('1.00'),  # $1.00 per USDC
            CollateralType.USDT: Decimal('1.00'),  # $1.00 per USDT
            CollateralType.OTHER: Decimal('0.01')  # Very low default
        }

        # Maximum LTV ratios by collateral type
        self.max_ltv_ratios = {
            CollateralType.ALGO: Decimal('0.70'),  # 70% max LTV for ALGO
            CollateralType.USDC: Decimal('0.90'),  # 90% max LTV for USDC
            CollateralType.USDT: Decimal('0.90'),  # 90% max LTV for USDT
            CollateralType.OTHER: Decimal('0.50')  # 50% max LTV for others
        }

        # Liquidation thresholds (when to liquidate)
        self.liquidation_thresholds = {
            CollateralType.ALGO: Decimal('0.85'),  # Liquidate at 85% LTV
            CollateralType.USDC: Decimal('0.95'),  # Liquidate at 95% LTV
            CollateralType.USDT: Decimal('0.95'),  # Liquidate at 95% LTV
            CollateralType.OTHER: Decimal('0.70')  # Liquidate at 70% LTV
        }

    def get_asset_price(self, asset_type: CollateralType) -> Decimal:
        """Get current price for asset type"""
        return self.price_feeds.get(asset_type, Decimal('0'))

    def update_price(self, asset_type: CollateralType, new_price: Decimal):
        """Update price feed (for testing or manual price updates)"""
        self.price_feeds[asset_type] = new_price

    def calculate_collateral_value(self, collateral: Collateral) -> Decimal:
        """Calculate USD value of collateral"""
        price = self.get_asset_price(collateral.asset_type)
        return collateral.amount * price

    def calculate_ltv(self, loan_amount: Decimal, collateral: Collateral) -> Decimal:
        """Calculate loan-to-value ratio"""
        collateral_value = self.calculate_collateral_value(collateral)
        if collateral_value == 0:
            return Decimal('999')  # Effectively infinite LTV
        return loan_amount / collateral_value

    def get_max_ltv(self, collateral_type: CollateralType) -> Decimal:
        """Get maximum allowed LTV for collateral type"""
        return self.max_ltv_ratios.get(collateral_type, Decimal('0.50'))

    def get_liquidation_threshold(self, collateral_type: CollateralType) -> Decimal:
        """Get liquidation threshold for collateral type"""
        return self.liquidation_thresholds.get(collateral_type, Decimal('0.70'))

    def is_ltv_acceptable(self, loan_request: LoanRequest) -> bool:
        """Check if requested LTV is acceptable"""
        requested_ltv = self.calculate_ltv(
            loan_request.requested_amount,
            loan_request.collateral
        )
        max_ltv = self.get_max_ltv(loan_request.collateral.asset_type)
        return requested_ltv <= max_ltv

    def calculate_max_loan_amount(self, collateral: Collateral) -> Decimal:
        """Calculate maximum loan amount for given collateral"""
        collateral_value = self.calculate_collateral_value(collateral)
        max_ltv = self.get_max_ltv(collateral.asset_type)
        return collateral_value * max_ltv

    def needs_liquidation(self, current_loan_amount: Decimal, collateral: Collateral) -> bool:
        """Check if position needs liquidation"""
        current_ltv = self.calculate_ltv(current_loan_amount, collateral)
        threshold = self.get_liquidation_threshold(collateral.asset_type)
        return current_ltv >= threshold

    def calculate_health_factor(self, current_loan_amount: Decimal, collateral: Collateral) -> Decimal:
        """
        Calculate health factor (>1 is healthy, <1 needs liquidation)
        Health Factor = (Collateral Value * Liquidation Threshold) / Loan Amount
        """
        collateral_value = self.calculate_collateral_value(collateral)
        threshold = self.get_liquidation_threshold(collateral.asset_type)

        if current_loan_amount == 0:
            return Decimal('999')  # Effectively infinite (very healthy)

        return (collateral_value * threshold) / current_loan_amount

    def get_collateral_requirements(self, loan_amount: Decimal, asset_type: CollateralType) -> Dict[str, Decimal]:
        """Get collateral requirements for a loan amount"""
        max_ltv = self.get_max_ltv(asset_type)
        asset_price = self.get_asset_price(asset_type)

        # Minimum collateral value needed
        min_collateral_value = loan_amount / max_ltv

        # Minimum collateral amount needed
        min_collateral_amount = min_collateral_value / asset_price if asset_price > 0 else Decimal('0')

        return {
            'min_collateral_value_usd': min_collateral_value,
            'min_collateral_amount': min_collateral_amount,
            'max_ltv': max_ltv,
            'asset_price': asset_price
        }

    def simulate_price_impact(self, collateral: Collateral, price_change_percent: Decimal) -> Dict[str, Decimal]:
        """Simulate impact of price changes on collateral"""
        current_price = self.get_asset_price(collateral.asset_type)
        new_price = current_price * (Decimal('1') + price_change_percent / Decimal('100'))

        current_value = self.calculate_collateral_value(collateral)
        new_value = collateral.amount * new_price

        return {
            'current_price': current_price,
            'new_price': new_price,
            'current_value': current_value,
            'new_value': new_value,
            'value_change': new_value - current_value,
            'value_change_percent': ((new_value - current_value) / current_value * Decimal('100')) if current_value > 0 else Decimal('0')
        }