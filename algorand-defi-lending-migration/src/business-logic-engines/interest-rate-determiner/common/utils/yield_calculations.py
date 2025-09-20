"""
DeFi yield calculation utilities for Algorand ecosystem.

Provides comprehensive yield mathematics including:
- APY/APR conversions and compounding
- Impermanent loss calculations
- Time-weighted returns
- Risk-adjusted yield metrics
"""

import math
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from enum import Enum


class CompoundingFrequency(Enum):
    """Compounding frequency options"""
    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


@dataclass
class YieldMetrics:
    """Comprehensive yield metrics"""
    nominal_apy: Decimal
    effective_apy: Decimal
    compounding_frequency: CompoundingFrequency
    risk_adjusted_yield: Decimal
    sharpe_ratio: Optional[Decimal] = None
    sortino_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None


class YieldCalculator:
    """
    Comprehensive yield calculator for DeFi protocols.

    Provides accurate calculations for various yield scenarios
    including compounding effects and risk adjustments.
    """

    @staticmethod
    def calculate_apy(
        apr: Decimal,
        compounding_frequency: CompoundingFrequency
    ) -> Decimal:
        """
        Convert APR to APY based on compounding frequency.

        Args:
            apr: Annual Percentage Rate (as decimal, e.g., 0.05 for 5%)
            compounding_frequency: How often interest compounds

        Returns:
            APY as decimal
        """
        if compounding_frequency == CompoundingFrequency.CONTINUOUS:
            # APY = e^(APR) - 1
            return Decimal(str(math.exp(float(apr)) - 1))

        # Discrete compounding: APY = (1 + APR/n)^n - 1
        n_values = {
            CompoundingFrequency.DAILY: 365,
            CompoundingFrequency.WEEKLY: 52,
            CompoundingFrequency.MONTHLY: 12,
            CompoundingFrequency.QUARTERLY: 4,
            CompoundingFrequency.ANNUALLY: 1
        }

        n = Decimal(str(n_values[compounding_frequency]))
        apy = (1 + apr / n) ** n - 1
        return apy

    @staticmethod
    def calculate_apr_from_apy(
        apy: Decimal,
        compounding_frequency: CompoundingFrequency
    ) -> Decimal:
        """Convert APY back to APR"""
        if compounding_frequency == CompoundingFrequency.CONTINUOUS:
            # APR = ln(1 + APY)
            return Decimal(str(math.log(float(apy + 1))))

        n_values = {
            CompoundingFrequency.DAILY: 365,
            CompoundingFrequency.WEEKLY: 52,
            CompoundingFrequency.MONTHLY: 12,
            CompoundingFrequency.QUARTERLY: 4,
            CompoundingFrequency.ANNUALLY: 1
        }

        n = Decimal(str(n_values[compounding_frequency]))
        apr = ((apy + 1) ** (1 / n) - 1) * n
        return apr

    @staticmethod
    def calculate_future_value(
        principal: Decimal,
        rate: Decimal,
        time_periods: Decimal,
        compounding_frequency: CompoundingFrequency
    ) -> Decimal:
        """
        Calculate future value with compounding.

        Args:
            principal: Initial investment
            rate: Annual rate (as decimal)
            time_periods: Time in years
            compounding_frequency: Compounding frequency

        Returns:
            Future value
        """
        if compounding_frequency == CompoundingFrequency.CONTINUOUS:
            # FV = P * e^(rt)
            return principal * Decimal(str(math.exp(float(rate * time_periods))))

        n_values = {
            CompoundingFrequency.DAILY: 365,
            CompoundingFrequency.WEEKLY: 52,
            CompoundingFrequency.MONTHLY: 12,
            CompoundingFrequency.QUARTERLY: 4,
            CompoundingFrequency.ANNUALLY: 1
        }

        n = Decimal(str(n_values[compounding_frequency]))
        fv = principal * (1 + rate / n) ** (n * time_periods)
        return fv

    @staticmethod
    def calculate_time_weighted_return(
        values: List[Decimal],
        timestamps: List[datetime]
    ) -> Decimal:
        """
        Calculate time-weighted return for a series of values.

        This eliminates the impact of cash flows and shows
        the actual performance of the investment strategy.
        """
        if len(values) != len(timestamps) or len(values) < 2:
            return Decimal('0')

        # Calculate period returns
        period_returns = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                period_return = (values[i] - values[i-1]) / values[i-1]
                period_returns.append(1 + period_return)

        if not period_returns:
            return Decimal('0')

        # Calculate cumulative return
        cumulative_return = Decimal('1')
        for return_factor in period_returns:
            cumulative_return *= return_factor

        # Annualize the return
        total_days = (timestamps[-1] - timestamps[0]).days
        if total_days == 0:
            return Decimal('0')

        years = Decimal(str(total_days / 365.25))
        annualized_return = cumulative_return ** (1 / years) - 1

        return annualized_return

    @staticmethod
    def calculate_risk_adjusted_yield(
        yield_rate: Decimal,
        volatility: Decimal,
        risk_free_rate: Decimal = Decimal('0.02')  # 2% default risk-free rate
    ) -> Decimal:
        """
        Calculate risk-adjusted yield using Sharpe ratio concept.

        Args:
            yield_rate: Expected yield (APY)
            volatility: Yield volatility (standard deviation)
            risk_free_rate: Risk-free rate for comparison

        Returns:
            Risk-adjusted yield
        """
        if volatility == 0:
            return yield_rate

        excess_return = yield_rate - risk_free_rate
        sharpe_ratio = excess_return / volatility

        # Adjust yield based on Sharpe ratio
        # Higher Sharpe = less adjustment needed
        adjustment_factor = 1 - (1 / (1 + sharpe_ratio))
        risk_adjusted = yield_rate * adjustment_factor

        return max(Decimal('0'), risk_adjusted)


class CompoundingCalculator:
    """
    Advanced compounding calculations for DeFi strategies.

    Handles complex compounding scenarios including
    variable rates and reinvestment strategies.
    """

    @staticmethod
    def calculate_compound_yield_with_variable_rates(
        principal: Decimal,
        rate_periods: List[Tuple[Decimal, int]],  # (rate, days)
        compounding_frequency: CompoundingFrequency
    ) -> Decimal:
        """
        Calculate compound yield with variable rates over different periods.

        Args:
            principal: Initial amount
            rate_periods: List of (annual_rate, days) tuples
            compounding_frequency: How often to compound

        Returns:
            Final value after all periods
        """
        current_value = principal

        for rate, days in rate_periods:
            # Convert days to years
            years = Decimal(str(days / 365.25))

            # Calculate value for this period
            period_value = YieldCalculator.calculate_future_value(
                current_value, rate, years, compounding_frequency
            )

            current_value = period_value

        return current_value

    @staticmethod
    def calculate_dollar_cost_averaging_yield(
        periodic_investment: Decimal,
        investment_periods: int,
        periodic_rate: Decimal,
        compounding_frequency: CompoundingFrequency
    ) -> Decimal:
        """
        Calculate yield for dollar-cost averaging strategy.

        Args:
            periodic_investment: Amount invested each period
            investment_periods: Number of investment periods
            periodic_rate: Rate per period
            compounding_frequency: Compounding frequency

        Returns:
            Total value after all investments and compounding
        """
        total_value = Decimal('0')

        for period in range(investment_periods):
            # Remaining periods for this investment to compound
            remaining_periods = investment_periods - period

            # Calculate future value of this investment
            if compounding_frequency == CompoundingFrequency.CONTINUOUS:
                period_value = periodic_investment * Decimal(str(
                    math.exp(float(periodic_rate * remaining_periods))
                ))
            else:
                period_value = periodic_investment * (1 + periodic_rate) ** remaining_periods

            total_value += period_value

        return total_value

    @staticmethod
    def calculate_auto_compound_advantage(
        principal: Decimal,
        base_apy: Decimal,
        manual_compound_frequency: CompoundingFrequency,
        auto_compound_frequency: CompoundingFrequency,
        time_years: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate the advantage of auto-compounding vs manual compounding.

        Returns comparison of final values and the advantage percentage.
        """
        manual_value = YieldCalculator.calculate_future_value(
            principal, base_apy, time_years, manual_compound_frequency
        )

        auto_value = YieldCalculator.calculate_future_value(
            principal, base_apy, time_years, auto_compound_frequency
        )

        advantage = (auto_value - manual_value) / manual_value * 100

        return {
            'manual_value': manual_value,
            'auto_value': auto_value,
            'advantage_percentage': advantage,
            'additional_yield': auto_value - manual_value
        }


class APYConverter:
    """
    Utility for converting between different yield representations.

    Handles conversions between APY, APR, daily rates, and
    protocol-specific yield formats.
    """

    @staticmethod
    def daily_rate_to_apy(daily_rate: Decimal) -> Decimal:
        """Convert daily rate to APY"""
        return (1 + daily_rate) ** 365 - 1

    @staticmethod
    def apy_to_daily_rate(apy: Decimal) -> Decimal:
        """Convert APY to daily rate"""
        return (1 + apy) ** (Decimal('1') / 365) - 1

    @staticmethod
    def protocol_rate_to_apy(
        protocol_rate: Decimal,
        rate_frequency: str  # "daily", "weekly", "monthly", etc.
    ) -> Decimal:
        """
        Convert protocol-specific rate to APY.

        Args:
            protocol_rate: Rate as provided by protocol
            rate_frequency: How often this rate is applied

        Returns:
            Equivalent APY
        """
        frequency_map = {
            "daily": 365,
            "weekly": 52,
            "monthly": 12,
            "quarterly": 4,
            "annually": 1
        }

        periods_per_year = frequency_map.get(rate_frequency, 365)
        apy = (1 + protocol_rate) ** periods_per_year - 1

        return apy

    @staticmethod
    def normalize_yield_for_comparison(
        yield_rate: Decimal,
        source_frequency: CompoundingFrequency,
        target_frequency: CompoundingFrequency = CompoundingFrequency.ANNUALLY
    ) -> Decimal:
        """
        Normalize yields from different sources for fair comparison.

        Converts all yields to the same compounding frequency
        for accurate comparison.
        """
        # First convert to APR
        apr = YieldCalculator.calculate_apr_from_apy(yield_rate, source_frequency)

        # Then convert to target frequency
        normalized_yield = YieldCalculator.calculate_apy(apr, target_frequency)

        return normalized_yield


class ImpermanentLossCalculator:
    """
    Calculator for impermanent loss in liquidity pools.

    Provides accurate calculations for IL across different
    pool types and price scenarios.
    """

    @staticmethod
    def calculate_constant_product_il(
        price_change_ratio: Decimal
    ) -> Decimal:
        """
        Calculate impermanent loss for constant product pools (x*y=k).

        Args:
            price_change_ratio: Price change ratio (new_price / initial_price)

        Returns:
            Impermanent loss as percentage (negative value)
        """
        # IL formula: 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
        sqrt_ratio = price_change_ratio ** Decimal('0.5')
        il = 2 * sqrt_ratio / (1 + price_change_ratio) - 1

        return il * 100  # Convert to percentage

    @staticmethod
    def calculate_stable_swap_il(
        price_changes: List[Decimal],
        amplification_factor: Decimal = Decimal('100')
    ) -> Decimal:
        """
        Calculate impermanent loss for stable swap pools.

        Args:
            price_changes: List of price change ratios for each asset
            amplification_factor: Pool's amplification parameter

        Returns:
            Impermanent loss percentage
        """
        # Simplified stable swap IL calculation
        # In practice, this would use the full StableSwap invariant

        max_deviation = max([abs(1 - change) for change in price_changes])

        # Stable pools have much lower IL due to amplification
        il_reduction_factor = 1 / (1 + amplification_factor / 100)
        il = max_deviation * il_reduction_factor * 100

        return -il  # Return as negative (loss)

    @staticmethod
    def calculate_il_breakeven_fees(
        price_change_ratio: Decimal,
        pool_fee_rate: Decimal,
        time_period_days: int
    ) -> Dict[str, Decimal]:
        """
        Calculate how much trading fees are needed to offset impermanent loss.

        Args:
            price_change_ratio: Asset price change ratio
            pool_fee_rate: Pool's trading fee rate (e.g., 0.003 for 0.3%)
            time_period_days: Time period in days

        Returns:
            Dictionary with IL, required volume, and breakeven analysis
        """
        il_percentage = ImpermanentLossCalculator.calculate_constant_product_il(price_change_ratio)

        # Calculate required daily volume to offset IL
        daily_fees_needed = abs(il_percentage) / 100 / time_period_days
        required_daily_volume_ratio = daily_fees_needed / pool_fee_rate

        return {
            'impermanent_loss_pct': il_percentage,
            'daily_fees_needed_pct': daily_fees_needed * 100,
            'required_daily_volume_ratio': required_daily_volume_ratio,
            'is_profitable': il_percentage > -abs(il_percentage),  # Net positive after fees
            'breakeven_volume_multiplier': required_daily_volume_ratio
        }

    @staticmethod
    def calculate_il_with_yield_farming(
        price_change_ratio: Decimal,
        trading_fee_apy: Decimal,
        reward_token_apy: Decimal,
        time_period_days: int
    ) -> Dict[str, Decimal]:
        """
        Calculate net yield considering IL, trading fees, and farming rewards.

        Args:
            price_change_ratio: Asset price change ratio
            trading_fee_apy: APY from trading fees
            reward_token_apy: APY from reward tokens
            time_period_days: Time period in days

        Returns:
            Comprehensive yield analysis including IL
        """
        il_percentage = ImpermanentLossCalculator.calculate_constant_product_il(price_change_ratio)

        # Calculate yields for the time period
        time_fraction = Decimal(str(time_period_days / 365))
        trading_yield = trading_fee_apy * time_fraction
        reward_yield = reward_token_apy * time_fraction

        total_yield = trading_yield + reward_yield
        net_yield = total_yield + (il_percentage / 100)  # IL is already negative

        return {
            'impermanent_loss_pct': il_percentage,
            'trading_fee_yield_pct': trading_yield * 100,
            'reward_token_yield_pct': reward_yield * 100,
            'total_positive_yield_pct': total_yield * 100,
            'net_yield_pct': net_yield * 100,
            'is_profitable': net_yield > 0,
            'yield_to_il_ratio': abs(total_yield * 100 / il_percentage) if il_percentage != 0 else float('inf')
        }

    @staticmethod
    def simulate_il_scenarios(
        initial_prices: Tuple[Decimal, Decimal],
        price_scenarios: List[Tuple[Decimal, Decimal]],
        pool_fee_rate: Decimal
    ) -> List[Dict[str, Decimal]]:
        """
        Simulate IL across multiple price scenarios.

        Args:
            initial_prices: (price_a, price_b) initial prices
            price_scenarios: List of (price_a, price_b) scenarios
            pool_fee_rate: Pool trading fee rate

        Returns:
            List of IL calculations for each scenario
        """
        results = []

        for price_a, price_b in price_scenarios:
            # Calculate price change ratios
            ratio_a = price_a / initial_prices[0]
            ratio_b = price_b / initial_prices[1]

            # For constant product pools, we need the relative price change
            relative_change = ratio_a / ratio_b

            il = ImpermanentLossCalculator.calculate_constant_product_il(relative_change)

            results.append({
                'price_a': price_a,
                'price_b': price_b,
                'price_ratio_a': ratio_a,
                'price_ratio_b': ratio_b,
                'relative_price_change': relative_change,
                'impermanent_loss_pct': il
            })

        return results