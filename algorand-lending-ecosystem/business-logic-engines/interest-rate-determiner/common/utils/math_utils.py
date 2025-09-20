"""
Mathematical utilities for interest rate calculations.
"""

import math
from typing import List, Tuple, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
import statistics
import numpy as np
from scipy import stats


def calculate_monthly_payment(
    principal: Decimal,
    annual_rate: Decimal,
    num_payments: int
) -> Decimal:
    """
    Calculate monthly payment for a loan using standard amortization formula.

    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        num_payments: Total number of payments

    Returns:
        Monthly payment amount
    """
    if annual_rate == 0:
        return principal / Decimal(str(num_payments))

    monthly_rate = annual_rate / Decimal('12')

    # Calculate payment using: P * [r(1+r)^n] / [(1+r)^n - 1]
    factor = (1 + monthly_rate) ** num_payments
    monthly_payment = principal * (monthly_rate * factor) / (factor - 1)

    return monthly_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_effective_annual_rate(
    nominal_rate: Decimal,
    compounding_periods: int
) -> Decimal:
    """
    Calculate effective annual rate from nominal rate and compounding frequency.

    Args:
        nominal_rate: Nominal annual interest rate
        compounding_periods: Number of compounding periods per year

    Returns:
        Effective annual rate
    """
    rate_per_period = nominal_rate / Decimal(str(compounding_periods))
    effective_rate = (1 + rate_per_period) ** compounding_periods - 1

    return effective_rate.quantize(Decimal('0.000001'))


def calculate_compound_interest(
    principal: Decimal,
    rate: Decimal,
    time_periods: int,
    compounding_frequency: int = 1
) -> Decimal:
    """
    Calculate compound interest.

    Args:
        principal: Initial principal amount
        rate: Annual interest rate
        time_periods: Number of time periods (usually years)
        compounding_frequency: Compounding frequency per year

    Returns:
        Final amount after compound interest
    """
    rate_per_period = rate / Decimal(str(compounding_frequency))
    total_periods = time_periods * compounding_frequency

    final_amount = principal * (1 + rate_per_period) ** total_periods

    return final_amount.quantize(Decimal('0.01'))


def calculate_present_value(
    future_value: Decimal,
    discount_rate: Decimal,
    periods: int
) -> Decimal:
    """
    Calculate present value of future cash flow.

    Args:
        future_value: Future value amount
        discount_rate: Discount rate per period
        periods: Number of periods

    Returns:
        Present value
    """
    present_value = future_value / (1 + discount_rate) ** periods
    return present_value.quantize(Decimal('0.01'))


def calculate_future_value(
    present_value: Decimal,
    interest_rate: Decimal,
    periods: int
) -> Decimal:
    """
    Calculate future value of present cash flow.

    Args:
        present_value: Present value amount
        interest_rate: Interest rate per period
        periods: Number of periods

    Returns:
        Future value
    """
    future_value = present_value * (1 + interest_rate) ** periods
    return future_value.quantize(Decimal('0.01'))


def calculate_risk_adjusted_return(
    expected_return: float,
    risk_free_rate: float,
    beta: float,
    market_risk_premium: float
) -> float:
    """
    Calculate risk-adjusted return using CAPM model.

    Args:
        expected_return: Expected return of the asset
        risk_free_rate: Risk-free rate
        beta: Beta coefficient
        market_risk_premium: Market risk premium

    Returns:
        Risk-adjusted return
    """
    capm_return = risk_free_rate + beta * market_risk_premium
    risk_adjusted = expected_return - capm_return

    return risk_adjusted


def calculate_sharpe_ratio(
    portfolio_return: float,
    risk_free_rate: float,
    portfolio_volatility: float
) -> float:
    """
    Calculate Sharpe ratio for risk-adjusted performance.

    Args:
        portfolio_return: Portfolio return
        risk_free_rate: Risk-free rate
        portfolio_volatility: Portfolio volatility (standard deviation)

    Returns:
        Sharpe ratio
    """
    if portfolio_volatility == 0:
        return 0.0

    excess_return = portfolio_return - risk_free_rate
    sharpe_ratio = excess_return / portfolio_volatility

    return sharpe_ratio


def calculate_value_at_risk(
    returns: List[float],
    confidence_level: float = 0.95,
    time_horizon: int = 1
) -> float:
    """
    Calculate Value at Risk (VaR) using historical simulation.

    Args:
        returns: Historical returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        time_horizon: Time horizon in periods

    Returns:
        Value at Risk
    """
    if not returns:
        return 0.0

    # Sort returns in ascending order
    sorted_returns = sorted(returns)

    # Calculate percentile
    percentile = (1 - confidence_level) * 100
    var_index = int(len(sorted_returns) * (1 - confidence_level))

    if var_index >= len(sorted_returns):
        var_index = len(sorted_returns) - 1

    var = abs(sorted_returns[var_index]) * math.sqrt(time_horizon)

    return var


def calculate_correlation_coefficient(
    x_values: List[float],
    y_values: List[float]
) -> float:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x_values: First variable values
        y_values: Second variable values

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0

    try:
        correlation = statistics.correlation(x_values, y_values)
        return correlation
    except statistics.StatisticsError:
        return 0.0


def calculate_portfolio_variance(
    weights: List[float],
    variances: List[float],
    correlations: List[List[float]]
) -> float:
    """
    Calculate portfolio variance given weights, individual variances, and correlations.

    Args:
        weights: Portfolio weights
        variances: Individual asset variances
        correlations: Correlation matrix

    Returns:
        Portfolio variance
    """
    n = len(weights)
    portfolio_variance = 0.0

    for i in range(n):
        for j in range(n):
            if i == j:
                # Variance term
                portfolio_variance += weights[i] ** 2 * variances[i]
            else:
                # Covariance term
                covariance = correlations[i][j] * math.sqrt(variances[i] * variances[j])
                portfolio_variance += 2 * weights[i] * weights[j] * covariance

    return max(portfolio_variance, 0.0)


def normalize_score(
    value: float,
    min_value: float,
    max_value: float,
    target_min: float = 0.0,
    target_max: float = 1.0
) -> float:
    """
    Normalize a value to a target range.

    Args:
        value: Value to normalize
        min_value: Minimum value in the original range
        max_value: Maximum value in the original range
        target_min: Target minimum value
        target_max: Target maximum value

    Returns:
        Normalized value
    """
    if max_value == min_value:
        return target_min

    normalized = ((value - min_value) / (max_value - min_value)) * (target_max - target_min) + target_min

    # Clamp to target range
    return max(target_min, min(target_max, normalized))


def weighted_average(
    values: List[float],
    weights: List[float]
) -> float:
    """
    Calculate weighted average.

    Args:
        values: Values to average
        weights: Corresponding weights

    Returns:
        Weighted average
    """
    if len(values) != len(weights) or not values:
        return 0.0

    total_weight = sum(weights)
    if total_weight == 0:
        return statistics.mean(values)

    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight


def exponential_moving_average(
    values: List[float],
    alpha: float = 0.1
) -> List[float]:
    """
    Calculate exponential moving average.

    Args:
        values: Time series values
        alpha: Smoothing factor (0 < alpha <= 1)

    Returns:
        Exponential moving average series
    """
    if not values:
        return []

    ema = [values[0]]

    for i in range(1, len(values)):
        ema_value = alpha * values[i] + (1 - alpha) * ema[i-1]
        ema.append(ema_value)

    return ema


def calculate_z_score(
    value: float,
    mean: float,
    std_dev: float
) -> float:
    """
    Calculate z-score (standard score).

    Args:
        value: Value to standardize
        mean: Population mean
        std_dev: Population standard deviation

    Returns:
        Z-score
    """
    if std_dev == 0:
        return 0.0

    return (value - mean) / std_dev


def calculate_percentile_rank(
    value: float,
    dataset: List[float]
) -> float:
    """
    Calculate percentile rank of a value in a dataset.

    Args:
        value: Value to find percentile rank for
        dataset: Reference dataset

    Returns:
        Percentile rank (0-100)
    """
    if not dataset:
        return 50.0

    sorted_data = sorted(dataset)

    # Count values less than the target value
    count_less = sum(1 for x in sorted_data if x < value)

    # Count values equal to the target value
    count_equal = sum(1 for x in sorted_data if x == value)

    # Calculate percentile rank
    percentile_rank = (count_less + 0.5 * count_equal) / len(sorted_data) * 100

    return percentile_rank


def calculate_loan_to_value_ratio(
    loan_amount: Decimal,
    collateral_value: Decimal
) -> float:
    """
    Calculate loan-to-value ratio.

    Args:
        loan_amount: Loan amount
        collateral_value: Collateral value

    Returns:
        LTV ratio (0-1)
    """
    if collateral_value == 0:
        return float('inf')

    return float(loan_amount / collateral_value)


def calculate_debt_service_coverage_ratio(
    net_operating_income: Decimal,
    debt_service: Decimal
) -> float:
    """
    Calculate debt service coverage ratio.

    Args:
        net_operating_income: Net operating income
        debt_service: Total debt service payments

    Returns:
        DSCR ratio
    """
    if debt_service == 0:
        return float('inf')

    return float(net_operating_income / debt_service)


def calculate_annual_percentage_rate(
    loan_amount: Decimal,
    total_payments: Decimal,
    loan_term_months: int
) -> Decimal:
    """
    Calculate Annual Percentage Rate (APR) using iterative method.

    Args:
        loan_amount: Principal loan amount
        total_payments: Total of all payments
        loan_term_months: Loan term in months

    Returns:
        Annual Percentage Rate
    """
    if loan_term_months == 0:
        return Decimal('0')

    monthly_payment = total_payments / Decimal(str(loan_term_months))

    # Use Newton-Raphson method to solve for APR
    apr_guess = Decimal('0.10')  # Start with 10% guess
    tolerance = Decimal('0.000001')
    max_iterations = 100

    for _ in range(max_iterations):
        monthly_rate = apr_guess / Decimal('12')

        # Calculate present value of payments
        pv = Decimal('0')
        for month in range(1, loan_term_months + 1):
            pv += monthly_payment / (1 + monthly_rate) ** month

        # Calculate derivative for Newton-Raphson
        derivative = Decimal('0')
        for month in range(1, loan_term_months + 1):
            derivative -= (monthly_payment * month) / (Decimal('12') * (1 + monthly_rate) ** (month + 1))

        # Newton-Raphson update
        error = pv - loan_amount
        if abs(error) < tolerance:
            break

        if derivative != 0:
            apr_guess = apr_guess - error / derivative
        else:
            break

    return max(apr_guess, Decimal('0')).quantize(Decimal('0.000001'))


def calculate_duration_risk_premium(
    base_rate: Decimal,
    duration_years: float,
    term_structure_slope: float = 0.002
) -> Decimal:
    """
    Calculate duration-based risk premium.

    Args:
        base_rate: Base interest rate
        duration_years: Loan duration in years
        term_structure_slope: Term structure slope (default 0.2% per year)

    Returns:
        Duration risk premium
    """
    # Non-linear duration premium calculation
    if duration_years <= 1:
        premium_factor = 0.0
    elif duration_years <= 5:
        # Linear increase for short to medium term
        premium_factor = (duration_years - 1) * term_structure_slope
    else:
        # Diminishing returns for long term
        base_premium = 4 * term_structure_slope  # 5-year premium
        additional_years = duration_years - 5
        additional_premium = additional_years * term_structure_slope * 0.5  # Half rate
        premium_factor = base_premium + additional_premium

    return Decimal(str(premium_factor)).quantize(Decimal('0.000001'))


def calculate_confidence_interval(
    sample_mean: float,
    sample_std: float,
    sample_size: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for a sample mean.

    Args:
        sample_mean: Sample mean
        sample_std: Sample standard deviation
        sample_size: Sample size
        confidence_level: Confidence level (default 95%)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if sample_size <= 1:
        return (sample_mean, sample_mean)

    # Use t-distribution for small samples, normal for large samples
    if sample_size < 30:
        # t-distribution
        t_value = stats.t.ppf((1 + confidence_level) / 2, sample_size - 1)
        margin_error = t_value * (sample_std / math.sqrt(sample_size))
    else:
        # Normal distribution
        z_value = stats.norm.ppf((1 + confidence_level) / 2)
        margin_error = z_value * (sample_std / math.sqrt(sample_size))

    lower_bound = sample_mean - margin_error
    upper_bound = sample_mean + margin_error

    return (lower_bound, upper_bound)