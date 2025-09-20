"""
Volatility and risk analysis utilities for ASA tokens and DeFi protocols.

Provides comprehensive risk metrics including:
- Price volatility calculations
- Value at Risk (VaR) estimation
- Correlation analysis
- Portfolio risk assessment
"""

import math
import statistics
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum


class VolatilityMethod(Enum):
    """Methods for calculating volatility"""
    SIMPLE = "simple"
    EXPONENTIAL_WEIGHTED = "exponential_weighted"
    GARCH = "garch"
    ROLLING_WINDOW = "rolling_window"


class VaRMethod(Enum):
    """Methods for calculating Value at Risk"""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for an asset"""
    asset_id: int
    calculation_timestamp: datetime

    # Volatility metrics
    daily_volatility: Decimal = Decimal('0')
    weekly_volatility: Decimal = Decimal('0')
    monthly_volatility: Decimal = Decimal('0')
    annualized_volatility: Decimal = Decimal('0')

    # Risk metrics
    var_1d_95: Decimal = Decimal('0')  # 1-day 95% VaR
    var_1d_99: Decimal = Decimal('0')  # 1-day 99% VaR
    expected_shortfall_95: Decimal = Decimal('0')  # Conditional VaR
    max_drawdown: Decimal = Decimal('0')

    # Distribution metrics
    skewness: float = 0.0
    kurtosis: float = 0.0
    is_normal_distribution: bool = False

    # Market metrics
    beta_vs_algo: float = 1.0
    correlation_with_market: float = 0.0
    sharpe_ratio: Optional[Decimal] = None

    @property
    def risk_level(self) -> str:
        """Categorize risk level based on volatility"""
        if self.annualized_volatility <= Decimal('0.15'):  # ≤15%
            return "very_low"
        elif self.annualized_volatility <= Decimal('0.30'):  # ≤30%
            return "low"
        elif self.annualized_volatility <= Decimal('0.60'):  # ≤60%
            return "medium"
        elif self.annualized_volatility <= Decimal('1.0'):   # ≤100%
            return "high"
        else:
            return "very_high"


class VolatilityAnalyzer:
    """
    Comprehensive volatility analyzer for Algorand assets.

    Provides various volatility calculation methods and
    risk assessment tools for DeFi protocols.
    """

    @staticmethod
    def calculate_historical_volatility(
        prices: List[Decimal],
        method: VolatilityMethod = VolatilityMethod.SIMPLE,
        window_size: int = 30,
        lambda_decay: float = 0.94
    ) -> Decimal:
        """
        Calculate historical volatility using various methods.

        Args:
            prices: Historical price series
            method: Volatility calculation method
            window_size: Window size for rolling calculations
            lambda_decay: Decay factor for exponential weighting

        Returns:
            Volatility as decimal (e.g., 0.05 = 5%)
        """
        if len(prices) < 2:
            return Decimal('0')

        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(float(ret))

        if not returns:
            return Decimal('0')

        if method == VolatilityMethod.SIMPLE:
            return VolatilityAnalyzer._simple_volatility(returns)
        elif method == VolatilityMethod.EXPONENTIAL_WEIGHTED:
            return VolatilityAnalyzer._exponential_weighted_volatility(returns, lambda_decay)
        elif method == VolatilityMethod.ROLLING_WINDOW:
            return VolatilityAnalyzer._rolling_window_volatility(returns, window_size)
        else:
            return VolatilityAnalyzer._simple_volatility(returns)

    @staticmethod
    def _simple_volatility(returns: List[float]) -> Decimal:
        """Calculate simple historical volatility"""
        if len(returns) < 2:
            return Decimal('0')

        std_dev = statistics.stdev(returns)
        return Decimal(str(std_dev))

    @staticmethod
    def _exponential_weighted_volatility(returns: List[float], lambda_decay: float) -> Decimal:
        """Calculate exponentially weighted volatility"""
        if len(returns) < 2:
            return Decimal('0')

        # Calculate exponentially weighted variance
        mean_return = sum(returns) / len(returns)
        variance = 0.0
        weight_sum = 0.0

        for i, ret in enumerate(reversed(returns)):
            weight = lambda_decay ** i
            variance += weight * (ret - mean_return) ** 2
            weight_sum += weight

        if weight_sum == 0:
            return Decimal('0')

        variance /= weight_sum
        volatility = math.sqrt(variance)
        return Decimal(str(volatility))

    @staticmethod
    def _rolling_window_volatility(returns: List[float], window_size: int) -> Decimal:
        """Calculate rolling window volatility (most recent window)"""
        if len(returns) < window_size:
            window_size = len(returns)

        if window_size < 2:
            return Decimal('0')

        recent_returns = returns[-window_size:]
        std_dev = statistics.stdev(recent_returns)
        return Decimal(str(std_dev))

    @staticmethod
    def annualize_volatility(
        daily_volatility: Decimal,
        trading_days_per_year: int = 365
    ) -> Decimal:
        """Convert daily volatility to annualized volatility"""
        return daily_volatility * Decimal(str(math.sqrt(trading_days_per_year)))

    @staticmethod
    def calculate_realized_volatility(
        prices: List[Decimal],
        timestamps: List[datetime]
    ) -> Dict[str, Decimal]:
        """
        Calculate realized volatility over different time periods.

        Returns volatility for 1d, 7d, 30d periods.
        """
        if len(prices) != len(timestamps) or len(prices) < 2:
            return {"1d": Decimal('0'), "7d": Decimal('0'), "30d": Decimal('0')}

        # Calculate returns with timestamps
        returns_with_time = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns_with_time.append((timestamps[i], float(ret)))

        now = datetime.now()
        volatilities = {}

        # Calculate for different periods
        periods = [1, 7, 30]
        for days in periods:
            cutoff_date = now - timedelta(days=days)
            period_returns = [ret for ts, ret in returns_with_time if ts >= cutoff_date]

            if len(period_returns) >= 2:
                volatility = statistics.stdev(period_returns)
                # Annualize the volatility
                annualized = volatility * math.sqrt(365 / days)
                volatilities[f"{days}d"] = Decimal(str(annualized))
            else:
                volatilities[f"{days}d"] = Decimal('0')

        return volatilities


class VaRCalculator:
    """
    Value at Risk calculator for portfolio risk assessment.

    Provides multiple VaR calculation methods for different
    risk management scenarios.
    """

    @staticmethod
    def calculate_historical_var(
        returns: List[float],
        confidence_level: float = 0.95,
        holding_period: int = 1
    ) -> Dict[str, float]:
        """
        Calculate Historical VaR using empirical return distribution.

        Args:
            returns: Historical returns
            confidence_level: Confidence level (0.95 = 95%)
            holding_period: Holding period in days

        Returns:
            VaR metrics including VaR and Expected Shortfall
        """
        if len(returns) < 10:
            return {"var": 0.0, "expected_shortfall": 0.0}

        # Sort returns (worst to best)
        sorted_returns = sorted(returns)

        # Calculate percentile for VaR
        percentile = (1 - confidence_level) * 100
        var_index = int(len(sorted_returns) * (1 - confidence_level))
        var_index = max(0, min(var_index, len(sorted_returns) - 1))

        var = -sorted_returns[var_index]  # Negative because we want loss

        # Calculate Expected Shortfall (average of returns worse than VaR)
        tail_returns = sorted_returns[:var_index + 1]
        expected_shortfall = -sum(tail_returns) / len(tail_returns) if tail_returns else 0.0

        # Adjust for holding period
        holding_period_adjustment = math.sqrt(holding_period)
        var *= holding_period_adjustment
        expected_shortfall *= holding_period_adjustment

        return {
            "var": var,
            "expected_shortfall": expected_shortfall,
            "confidence_level": confidence_level,
            "holding_period": holding_period
        }

    @staticmethod
    def calculate_parametric_var(
        returns: List[float],
        confidence_level: float = 0.95,
        holding_period: int = 1
    ) -> Dict[str, float]:
        """
        Calculate Parametric VaR assuming normal distribution.

        Args:
            returns: Historical returns
            confidence_level: Confidence level
            holding_period: Holding period in days

        Returns:
            VaR metrics
        """
        if len(returns) < 2:
            return {"var": 0.0, "expected_shortfall": 0.0}

        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)

        # Z-score for given confidence level
        z_scores = {
            0.90: 1.282,
            0.95: 1.645,
            0.99: 2.326
        }
        z_score = z_scores.get(confidence_level, 1.645)

        # Calculate VaR
        var = -(mean_return - z_score * std_return)

        # Expected Shortfall for normal distribution
        # ES = μ - σ * φ(z) / α where φ is PDF, α is tail probability
        alpha = 1 - confidence_level
        phi_z = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * z_score ** 2)
        expected_shortfall = -(mean_return - std_return * phi_z / alpha)

        # Adjust for holding period
        holding_period_adjustment = math.sqrt(holding_period)
        var *= holding_period_adjustment
        expected_shortfall *= holding_period_adjustment

        return {
            "var": var,
            "expected_shortfall": expected_shortfall,
            "confidence_level": confidence_level,
            "holding_period": holding_period,
            "mean_return": mean_return,
            "volatility": std_return
        }

    @staticmethod
    def calculate_portfolio_var(
        asset_returns: Dict[str, List[float]],
        weights: Dict[str, float],
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate portfolio VaR considering correlations.

        Args:
            asset_returns: Returns for each asset
            weights: Portfolio weights for each asset
            confidence_level: Confidence level

        Returns:
            Portfolio VaR metrics
        """
        assets = list(asset_returns.keys())
        if len(assets) < 2:
            # Single asset portfolio
            if assets:
                single_returns = asset_returns[assets[0]]
                return VaRCalculator.calculate_historical_var(single_returns, confidence_level)
            return {"var": 0.0, "expected_shortfall": 0.0}

        # Calculate portfolio returns
        min_length = min(len(returns) for returns in asset_returns.values())
        portfolio_returns = []

        for i in range(min_length):
            portfolio_return = sum(
                weights.get(asset, 0) * asset_returns[asset][i]
                for asset in assets
            )
            portfolio_returns.append(portfolio_return)

        return VaRCalculator.calculate_historical_var(portfolio_returns, confidence_level)


class CorrelationAnalyzer:
    """
    Correlation analysis for portfolio diversification assessment.

    Helps identify correlation patterns and diversification benefits
    across different Algorand assets and DeFi protocols.
    """

    @staticmethod
    def calculate_correlation_matrix(
        asset_returns: Dict[str, List[float]]
    ) -> Dict[Tuple[str, str], float]:
        """
        Calculate correlation matrix for multiple assets.

        Args:
            asset_returns: Returns for each asset

        Returns:
            Correlation matrix as dictionary of asset pairs
        """
        assets = list(asset_returns.keys())
        correlations = {}

        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                if i <= j:  # Calculate upper triangle and diagonal
                    corr = CorrelationAnalyzer.calculate_correlation(
                        asset_returns[asset1],
                        asset_returns[asset2]
                    )
                    correlations[(asset1, asset2)] = corr
                    if i != j:  # Add symmetric entry
                        correlations[(asset2, asset1)] = corr

        return correlations

    @staticmethod
    def calculate_correlation(
        returns1: List[float],
        returns2: List[float]
    ) -> float:
        """Calculate Pearson correlation coefficient between two return series"""
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return 0.0

        n = len(returns1)
        mean1 = sum(returns1) / n
        mean2 = sum(returns2) / n

        numerator = sum((returns1[i] - mean1) * (returns2[i] - mean2) for i in range(n))

        sum_sq1 = sum((returns1[i] - mean1) ** 2 for i in range(n))
        sum_sq2 = sum((returns2[i] - mean2) ** 2 for i in range(n))

        denominator = math.sqrt(sum_sq1 * sum_sq2)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def analyze_diversification_benefit(
        asset_returns: Dict[str, List[float]],
        equal_weights: bool = True
    ) -> Dict[str, float]:
        """
        Analyze diversification benefit of a portfolio.

        Compares portfolio volatility to weighted average of individual volatilities.
        """
        assets = list(asset_returns.keys())
        n_assets = len(assets)

        if n_assets < 2:
            return {"diversification_ratio": 1.0, "risk_reduction": 0.0}

        # Calculate individual volatilities
        individual_vols = {}
        for asset in assets:
            if len(asset_returns[asset]) >= 2:
                vol = statistics.stdev(asset_returns[asset])
                individual_vols[asset] = vol
            else:
                individual_vols[asset] = 0.0

        # Calculate weights
        if equal_weights:
            weights = {asset: 1.0 / n_assets for asset in assets}
        else:
            # Use inverse volatility weighting
            total_inv_vol = sum(1 / max(vol, 0.001) for vol in individual_vols.values())
            weights = {
                asset: (1 / max(individual_vols[asset], 0.001)) / total_inv_vol
                for asset in assets
            }

        # Calculate weighted average volatility
        weighted_avg_vol = sum(weights[asset] * individual_vols[asset] for asset in assets)

        # Calculate portfolio volatility
        portfolio_var = VaRCalculator.calculate_portfolio_var(
            asset_returns, weights, confidence_level=0.68  # 1 std dev
        )
        portfolio_vol = portfolio_var.get("volatility", weighted_avg_vol)

        # Diversification ratio
        if portfolio_vol > 0:
            diversification_ratio = weighted_avg_vol / portfolio_vol
            risk_reduction = (1 - 1 / diversification_ratio) * 100
        else:
            diversification_ratio = 1.0
            risk_reduction = 0.0

        return {
            "diversification_ratio": diversification_ratio,
            "risk_reduction": risk_reduction,
            "portfolio_volatility": portfolio_vol,
            "weighted_average_volatility": weighted_avg_vol
        }

    @staticmethod
    def identify_risk_clusters(
        correlations: Dict[Tuple[str, str], float],
        correlation_threshold: float = 0.7
    ) -> List[List[str]]:
        """
        Identify clusters of highly correlated assets.

        Args:
            correlations: Correlation matrix
            correlation_threshold: Threshold for high correlation

        Returns:
            List of asset clusters
        """
        # Build adjacency list for highly correlated assets
        adjacency = {}
        assets = set()

        for (asset1, asset2), corr in correlations.items():
            if asset1 != asset2 and abs(corr) >= correlation_threshold:
                assets.add(asset1)
                assets.add(asset2)

                if asset1 not in adjacency:
                    adjacency[asset1] = set()
                if asset2 not in adjacency:
                    adjacency[asset2] = set()

                adjacency[asset1].add(asset2)
                adjacency[asset2].add(asset1)

        # Find connected components (clusters)
        visited = set()
        clusters = []

        def dfs(asset, current_cluster):
            if asset in visited:
                return
            visited.add(asset)
            current_cluster.append(asset)

            for neighbor in adjacency.get(asset, []):
                dfs(neighbor, current_cluster)

        for asset in assets:
            if asset not in visited:
                cluster = []
                dfs(asset, cluster)
                if cluster:
                    clusters.append(cluster)

        return clusters