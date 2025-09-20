"""
Correlation Analyzer - Advanced cross-asset correlation and contagion risk analysis

This module analyzes correlations between assets in the Algorand ecosystem during different
market regimes and stress conditions to assess cascade risk and contagion effects.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime classifications"""
    NORMAL = "normal"
    STRESSED = "stressed"
    CRISIS = "crisis"
    RECOVERY = "recovery"

class CorrelationType(Enum):
    """Types of correlation analysis"""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    DYNAMIC = "dynamic"
    CONDITIONAL = "conditional"

@dataclass
class CorrelationMatrix:
    """Correlation matrix with metadata"""
    matrix: pd.DataFrame
    correlation_type: CorrelationType
    time_period: str
    market_regime: MarketRegime
    significance_levels: pd.DataFrame
    confidence_intervals: Dict[str, Tuple[float, float]]

@dataclass
class AssetGroup:
    """Group of related assets"""
    name: str
    assets: List[str]
    group_type: str  # major_tokens, defi_tokens, stablecoins, etc.
    risk_weight: float

@dataclass
class RegimeChangeEvent:
    """Market regime change detection"""
    timestamp: datetime
    previous_regime: MarketRegime
    new_regime: MarketRegime
    trigger_assets: List[str]
    confidence_score: float
    correlation_shift: Dict[str, float]

@dataclass
class ContagionSignal:
    """Contagion risk signal"""
    timestamp: datetime
    source_asset: str
    affected_assets: List[str]
    contagion_strength: float
    propagation_speed: float
    risk_level: str

class CorrelationAnalyzer:
    """
    Advanced correlation analyzer for the Algorand ecosystem that tracks
    asset correlations across market regimes and detects contagion risks.
    """

    def __init__(self, config_path: str = None):
        """Initialize the correlation analyzer"""
        self.config = self._load_config(config_path)
        self.correlation_config = self.config['correlation']
        self.asset_groups = self._initialize_asset_groups()

        # Historical data storage
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.correlation_history: List[CorrelationMatrix] = []
        self.regime_history: List[RegimeChangeEvent] = []
        self.contagion_signals: List[ContagionSignal] = []

        # Analysis parameters
        self.lookback_periods = self.correlation_config['lookback_periods']
        self.correlation_threshold = self.correlation_config['correlation_threshold']
        self.regime_change_threshold = self.correlation_config['regime_change_threshold']

        # Current state
        self.current_regime = MarketRegime.NORMAL
        self.current_correlations: Optional[CorrelationMatrix] = None

        logger.info("Correlation Analyzer initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_asset_groups(self) -> Dict[str, AssetGroup]:
        """Initialize asset groups from configuration"""
        groups = {}

        for group_name, assets in self.correlation_config['asset_groups'].items():
            risk_weights = {
                'major_tokens': 1.0,
                'defi_tokens': 1.2,
                'stablecoins': 0.8,
                'governance': 1.5
            }

            groups[group_name] = AssetGroup(
                name=group_name,
                assets=assets,
                group_type=group_name,
                risk_weight=risk_weights.get(group_name, 1.0)
            )

        return groups

    async def analyze_correlations(
        self,
        assets: List[str] = None,
        lookback_hours: int = 168,  # 1 week default
        correlation_type: CorrelationType = CorrelationType.PEARSON
    ) -> CorrelationMatrix:
        """
        Analyze correlations between assets

        Args:
            assets: List of assets to analyze (defaults to major tokens)
            lookback_hours: Hours of historical data to use
            correlation_type: Type of correlation analysis

        Returns:
            Correlation matrix with metadata
        """
        if assets is None:
            assets = self.asset_groups['major_tokens'].assets

        logger.info(f"Analyzing {correlation_type.value} correlations for {len(assets)} assets")

        # Get or generate price data
        price_data = await self._get_price_data(assets, lookback_hours)

        if price_data.empty:
            raise ValueError("No price data available for correlation analysis")

        # Calculate returns
        returns = price_data.pct_change().dropna()

        # Detect current market regime
        current_regime = self._detect_market_regime(returns)

        # Calculate correlation matrix
        if correlation_type == CorrelationType.PEARSON:
            corr_matrix = returns.corr(method='pearson')
        elif correlation_type == CorrelationType.SPEARMAN:
            corr_matrix = returns.corr(method='spearman')
        elif correlation_type == CorrelationType.KENDALL:
            corr_matrix = returns.corr(method='kendall')
        elif correlation_type == CorrelationType.DYNAMIC:
            corr_matrix = self._calculate_dynamic_correlation(returns)
        elif correlation_type == CorrelationType.CONDITIONAL:
            corr_matrix = self._calculate_conditional_correlation(returns, current_regime)
        else:
            raise ValueError(f"Unknown correlation type: {correlation_type}")

        # Calculate significance levels
        significance_levels = self._calculate_significance_levels(returns, corr_matrix)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(returns, corr_matrix)

        correlation_result = CorrelationMatrix(
            matrix=corr_matrix,
            correlation_type=correlation_type,
            time_period=f"{lookback_hours}h",
            market_regime=current_regime,
            significance_levels=significance_levels,
            confidence_intervals=confidence_intervals
        )

        self.current_correlations = correlation_result
        self.correlation_history.append(correlation_result)

        return correlation_result

    async def _get_price_data(self, assets: List[str], lookback_hours: int) -> pd.DataFrame:
        """Get or generate price data for assets"""
        # In a real implementation, this would fetch from data sources
        # For now, we'll generate realistic mock data

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)

        # Generate hourly timestamps
        timestamps = pd.date_range(start=start_time, end=end_time, freq='H')

        price_data = pd.DataFrame(index=timestamps)

        # Generate correlated price series for each asset
        np.random.seed(42)  # For reproducible results

        # Base price movements (market factor)
        market_returns = np.random.normal(0, 0.02, len(timestamps))

        for i, asset in enumerate(assets):
            # Asset-specific parameters
            if asset == 'ALGO':
                base_price = 0.5
                volatility = 0.25
                market_beta = 1.0
            elif asset in ['USDC', 'USDT']:
                base_price = 1.0
                volatility = 0.05  # Low volatility for stablecoins
                market_beta = 0.1
            elif asset == 'GARD':
                base_price = 1.0
                volatility = 0.15
                market_beta = 0.6
            else:
                base_price = np.random.uniform(0.1, 5.0)
                volatility = np.random.uniform(0.3, 0.6)
                market_beta = np.random.uniform(0.5, 1.5)

            # Generate asset-specific noise
            asset_noise = np.random.normal(0, volatility * 0.7, len(timestamps))

            # Combine market factor and asset-specific noise
            returns = market_beta * market_returns + asset_noise

            # Generate price series
            prices = [base_price]
            for ret in returns[1:]:
                new_price = prices[-1] * (1 + ret)
                prices.append(max(new_price, 0.001))  # Prevent negative prices

            price_data[asset] = prices

        return price_data

    def _detect_market_regime(self, returns: pd.DataFrame) -> MarketRegime:
        """Detect current market regime based on return characteristics"""
        # Calculate market stress indicators
        volatility = returns.std().mean()
        avg_correlation = self._calculate_average_correlation(returns)
        max_drawdown = self._calculate_max_drawdown(returns)

        # Regime classification rules
        if volatility > 0.4 and avg_correlation > 0.8:
            regime = MarketRegime.CRISIS
        elif volatility > 0.3 or avg_correlation > 0.7:
            regime = MarketRegime.STRESSED
        elif max_drawdown < -0.2:  # Recovery after significant drawdown
            regime = MarketRegime.RECOVERY
        else:
            regime = MarketRegime.NORMAL

        # Check for regime change
        if regime != self.current_regime:
            self._record_regime_change(self.current_regime, regime, returns)

        return regime

    def _calculate_average_correlation(self, returns: pd.DataFrame) -> float:
        """Calculate average pairwise correlation"""
        corr_matrix = returns.corr()
        # Get upper triangle excluding diagonal
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        correlations = corr_matrix.where(mask).values.flatten()
        correlations = correlations[~np.isnan(correlations)]

        return np.mean(correlations) if len(correlations) > 0 else 0.0

    def _calculate_max_drawdown(self, returns: pd.DataFrame) -> float:
        """Calculate maximum drawdown across all assets"""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max

        return drawdown.min().min()

    def _record_regime_change(
        self,
        previous_regime: MarketRegime,
        new_regime: MarketRegime,
        returns: pd.DataFrame
    ):
        """Record a market regime change event"""
        # Identify assets that triggered the regime change
        trigger_assets = self._identify_regime_triggers(returns)

        # Calculate correlation shift
        correlation_shift = self._calculate_correlation_shift(returns)

        # Calculate confidence score
        confidence_score = self._calculate_regime_confidence(returns, new_regime)

        regime_event = RegimeChangeEvent(
            timestamp=datetime.now(),
            previous_regime=previous_regime,
            new_regime=new_regime,
            trigger_assets=trigger_assets,
            confidence_score=confidence_score,
            correlation_shift=correlation_shift
        )

        self.regime_history.append(regime_event)
        self.current_regime = new_regime

        logger.info(f"Regime change detected: {previous_regime.value} -> {new_regime.value}")

    def _identify_regime_triggers(self, returns: pd.DataFrame) -> List[str]:
        """Identify assets that likely triggered regime change"""
        # Assets with highest recent volatility or extreme returns
        recent_returns = returns.tail(24)  # Last 24 hours
        volatility = recent_returns.std()
        extreme_returns = recent_returns.abs().max()

        # Combine volatility and extreme return scores
        trigger_scores = volatility + extreme_returns
        trigger_threshold = trigger_scores.quantile(0.8)  # Top 20%

        return trigger_scores[trigger_scores > trigger_threshold].index.tolist()

    def _calculate_correlation_shift(self, returns: pd.DataFrame) -> Dict[str, float]:
        """Calculate how correlations have shifted"""
        if len(self.correlation_history) < 2:
            return {}

        current_corr = returns.corr()
        previous_corr = self.correlation_history[-1].matrix

        # Calculate average shift for each asset
        shifts = {}
        for asset in current_corr.columns:
            if asset in previous_corr.columns:
                asset_shifts = abs(current_corr[asset] - previous_corr[asset])
                shifts[asset] = asset_shifts.mean()

        return shifts

    def _calculate_regime_confidence(self, returns: pd.DataFrame, regime: MarketRegime) -> float:
        """Calculate confidence in regime classification"""
        # Simple confidence based on how well indicators align with regime
        volatility = returns.std().mean()
        avg_correlation = self._calculate_average_correlation(returns)

        if regime == MarketRegime.CRISIS:
            vol_score = min(1.0, volatility / 0.4)
            corr_score = min(1.0, avg_correlation / 0.8)
        elif regime == MarketRegime.STRESSED:
            vol_score = min(1.0, volatility / 0.3)
            corr_score = min(1.0, avg_correlation / 0.7)
        elif regime == MarketRegime.NORMAL:
            vol_score = max(0.0, 1.0 - volatility / 0.2)
            corr_score = max(0.0, 1.0 - avg_correlation / 0.5)
        else:  # RECOVERY
            vol_score = 0.5  # Neutral
            corr_score = 0.5

        return (vol_score + corr_score) / 2

    def _calculate_dynamic_correlation(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate dynamic correlation using rolling windows"""
        window_size = min(48, len(returns) // 4)  # 48 hours or 1/4 of data
        dynamic_corr = returns.rolling(window=window_size).corr().iloc[-len(returns.columns):]

        return dynamic_corr

    def _calculate_conditional_correlation(
        self,
        returns: pd.DataFrame,
        regime: MarketRegime
    ) -> pd.DataFrame:
        """Calculate correlation conditional on market regime"""
        # Adjust correlation based on regime
        base_corr = returns.corr()

        regime_multipliers = {
            MarketRegime.NORMAL: 1.0,
            MarketRegime.STRESSED: 1.3,
            MarketRegime.CRISIS: 1.8,
            MarketRegime.RECOVERY: 0.9
        }

        multiplier = regime_multipliers[regime]

        # Apply multiplier while keeping diagonal as 1.0
        conditional_corr = base_corr * multiplier
        np.fill_diagonal(conditional_corr.values, 1.0)

        # Ensure correlations stay within [-1, 1]
        conditional_corr = conditional_corr.clip(-1.0, 1.0)

        return conditional_corr

    def _calculate_significance_levels(
        self,
        returns: pd.DataFrame,
        corr_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate statistical significance of correlations"""
        n = len(returns)
        significance_matrix = pd.DataFrame(
            index=corr_matrix.index,
            columns=corr_matrix.columns,
            dtype=float
        )

        for i, asset1 in enumerate(corr_matrix.columns):
            for j, asset2 in enumerate(corr_matrix.columns):
                if i != j:
                    r = corr_matrix.loc[asset1, asset2]
                    # Calculate t-statistic for correlation
                    t_stat = r * np.sqrt((n - 2) / (1 - r**2))
                    # Calculate p-value (two-tailed test)
                    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
                    significance_matrix.loc[asset1, asset2] = p_value
                else:
                    significance_matrix.loc[asset1, asset2] = 0.0

        return significance_matrix

    def _calculate_confidence_intervals(
        self,
        returns: pd.DataFrame,
        corr_matrix: pd.DataFrame
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for correlations"""
        n = len(returns)
        confidence_intervals = {}

        for i, asset1 in enumerate(corr_matrix.columns):
            for j, asset2 in enumerate(corr_matrix.columns):
                if i < j:  # Only calculate for unique pairs
                    r = corr_matrix.loc[asset1, asset2]

                    # Fisher transformation for confidence interval
                    z = 0.5 * np.log((1 + r) / (1 - r))
                    se = 1 / np.sqrt(n - 3)

                    # 95% confidence interval
                    z_lower = z - 1.96 * se
                    z_upper = z + 1.96 * se

                    # Transform back to correlation scale
                    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
                    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

                    confidence_intervals[f"{asset1}-{asset2}"] = (r_lower, r_upper)

        return confidence_intervals

    async def detect_contagion_risk(
        self,
        source_events: List[Dict[str, Any]],
        monitoring_window_hours: int = 24
    ) -> List[ContagionSignal]:
        """
        Detect contagion risk from source events

        Args:
            source_events: List of initial shock events
            monitoring_window_hours: Time window to monitor for contagion

        Returns:
            List of detected contagion signals
        """
        logger.info(f"Detecting contagion risk from {len(source_events)} source events")

        contagion_signals = []

        for event in source_events:
            source_asset = event['asset']
            shock_magnitude = event.get('magnitude', 0.1)

            # Get correlations for source asset
            if self.current_correlations is None:
                await self.analyze_correlations()

            correlations = self.current_correlations.matrix[source_asset]

            # Identify potentially affected assets
            high_corr_assets = correlations[
                (correlations.abs() > self.correlation_threshold) &
                (correlations.index != source_asset)
            ]

            if len(high_corr_assets) > 0:
                # Calculate contagion strength
                contagion_strength = self._calculate_contagion_strength(
                    shock_magnitude, high_corr_assets, self.current_correlations.market_regime
                )

                # Estimate propagation speed
                propagation_speed = self._estimate_propagation_speed(
                    source_asset, high_corr_assets, self.current_correlations.market_regime
                )

                # Assess risk level
                risk_level = self._assess_contagion_risk_level(
                    contagion_strength, len(high_corr_assets), propagation_speed
                )

                signal = ContagionSignal(
                    timestamp=datetime.now(),
                    source_asset=source_asset,
                    affected_assets=high_corr_assets.index.tolist(),
                    contagion_strength=contagion_strength,
                    propagation_speed=propagation_speed,
                    risk_level=risk_level
                )

                contagion_signals.append(signal)
                self.contagion_signals.append(signal)

        return contagion_signals

    def _calculate_contagion_strength(
        self,
        shock_magnitude: float,
        correlations: pd.Series,
        regime: MarketRegime
    ) -> float:
        """Calculate expected contagion strength"""
        # Base contagion from correlation strength
        avg_correlation = correlations.abs().mean()
        base_strength = shock_magnitude * avg_correlation

        # Adjust for market regime
        regime_multipliers = self.correlation_config['stress_multipliers']
        regime_key = regime.value if regime.value in regime_multipliers else 'normal'
        regime_multiplier = regime_multipliers[regime_key]

        # Apply regime adjustment
        contagion_strength = base_strength * regime_multiplier

        return min(contagion_strength, 1.0)  # Cap at 100%

    def _estimate_propagation_speed(
        self,
        source_asset: str,
        correlations: pd.Series,
        regime: MarketRegime
    ) -> float:
        """Estimate contagion propagation speed (events per hour)"""
        # Base speed depends on correlation strength
        avg_correlation = correlations.abs().mean()
        base_speed = avg_correlation * 2.0  # Up to 2 events per hour

        # Adjust for market regime (stress increases speed)
        if regime == MarketRegime.CRISIS:
            speed_multiplier = 3.0
        elif regime == MarketRegime.STRESSED:
            speed_multiplier = 2.0
        elif regime == MarketRegime.RECOVERY:
            speed_multiplier = 0.5
        else:
            speed_multiplier = 1.0

        return base_speed * speed_multiplier

    def _assess_contagion_risk_level(
        self,
        strength: float,
        num_affected: int,
        speed: float
    ) -> str:
        """Assess overall contagion risk level"""
        # Calculate composite risk score
        strength_score = strength  # 0-1
        breadth_score = min(1.0, num_affected / 10)  # Normalize to max 10 assets
        speed_score = min(1.0, speed / 5)  # Normalize to max 5 events/hour

        composite_score = (
            strength_score * 0.4 +
            breadth_score * 0.3 +
            speed_score * 0.3
        )

        if composite_score < 0.3:
            return "LOW"
        elif composite_score < 0.6:
            return "MEDIUM"
        elif composite_score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"

    async def analyze_portfolio_correlation_risk(
        self,
        portfolio: Dict[str, float]  # asset -> weight
    ) -> Dict[str, Any]:
        """
        Analyze correlation risk for a portfolio

        Args:
            portfolio: Dictionary of asset weights

        Returns:
            Portfolio correlation risk analysis
        """
        logger.info(f"Analyzing portfolio correlation risk for {len(portfolio)} assets")

        # Get current correlations for portfolio assets
        portfolio_assets = list(portfolio.keys())
        correlation_matrix = await self.analyze_correlations(portfolio_assets)

        # Calculate portfolio correlation metrics
        weights = np.array([portfolio[asset] for asset in portfolio_assets])
        corr_matrix = correlation_matrix.matrix.values

        # Portfolio variance due to correlations
        portfolio_variance = np.dot(weights, np.dot(corr_matrix, weights))

        # Diversification ratio
        individual_variances = np.sum(weights**2)
        diversification_ratio = individual_variances / portfolio_variance

        # Concentration risk
        concentration_risk = self._calculate_portfolio_concentration_risk(
            portfolio, correlation_matrix
        )

        # Regime sensitivity
        regime_sensitivity = self._calculate_regime_sensitivity(
            portfolio, correlation_matrix
        )

        # Contagion vulnerability
        contagion_vulnerability = await self._calculate_contagion_vulnerability(
            portfolio, correlation_matrix
        )

        return {
            'portfolio_assets': portfolio_assets,
            'portfolio_weights': portfolio,
            'correlation_matrix': correlation_matrix.matrix.to_dict(),
            'portfolio_variance': portfolio_variance,
            'diversification_ratio': diversification_ratio,
            'concentration_risk': concentration_risk,
            'regime_sensitivity': regime_sensitivity,
            'contagion_vulnerability': contagion_vulnerability,
            'current_regime': correlation_matrix.market_regime.value,
            'risk_assessment': self._assess_portfolio_correlation_risk(
                diversification_ratio, concentration_risk, contagion_vulnerability
            )
        }

    def _calculate_portfolio_concentration_risk(
        self,
        portfolio: Dict[str, float],
        correlation_matrix: CorrelationMatrix
    ) -> Dict[str, float]:
        """Calculate portfolio concentration risk metrics"""
        corr_matrix = correlation_matrix.matrix

        # Calculate effective number of independent assets
        weights = np.array(list(portfolio.values()))
        avg_correlation = self._calculate_portfolio_avg_correlation(portfolio, corr_matrix)

        effective_assets = 1 + (len(portfolio) - 1) * (1 - avg_correlation)

        # Herfindahl-Hirschman Index for concentration
        hhi = sum(weight**2 for weight in portfolio.values())

        return {
            'average_correlation': avg_correlation,
            'effective_independent_assets': effective_assets,
            'herfindahl_hirschman_index': hhi,
            'concentration_score': 1 - (effective_assets / len(portfolio))
        }

    def _calculate_portfolio_avg_correlation(
        self,
        portfolio: Dict[str, float],
        corr_matrix: pd.DataFrame
    ) -> float:
        """Calculate portfolio-weighted average correlation"""
        total_weighted_corr = 0
        total_weight_pairs = 0

        assets = list(portfolio.keys())

        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                if i < j:  # Avoid double counting
                    weight1 = portfolio[asset1]
                    weight2 = portfolio[asset2]
                    correlation = corr_matrix.loc[asset1, asset2]

                    weighted_corr = weight1 * weight2 * correlation
                    total_weighted_corr += weighted_corr
                    total_weight_pairs += weight1 * weight2

        return total_weighted_corr / total_weight_pairs if total_weight_pairs > 0 else 0

    def _calculate_regime_sensitivity(
        self,
        portfolio: Dict[str, float],
        correlation_matrix: CorrelationMatrix
    ) -> Dict[str, float]:
        """Calculate portfolio sensitivity to regime changes"""
        current_regime = correlation_matrix.market_regime

        # Estimate correlation changes under different regimes
        regime_sensitivities = {}

        for regime in MarketRegime:
            if regime != current_regime:
                # Estimate correlation change
                regime_multipliers = self.correlation_config['stress_multipliers']
                regime_key = regime.value if regime.value in regime_multipliers else 'normal'
                current_key = current_regime.value if current_regime.value in regime_multipliers else 'normal'

                multiplier_change = regime_multipliers[regime_key] / regime_multipliers[current_key]

                # Calculate portfolio variance under new regime
                adjusted_corr = correlation_matrix.matrix * multiplier_change
                np.fill_diagonal(adjusted_corr.values, 1.0)
                adjusted_corr = adjusted_corr.clip(-1.0, 1.0)

                weights = np.array([portfolio[asset] for asset in portfolio.keys()])
                new_variance = np.dot(weights, np.dot(adjusted_corr.values, weights))

                # Sensitivity is the relative change in variance
                current_variance = np.dot(weights, np.dot(correlation_matrix.matrix.values, weights))
                sensitivity = (new_variance - current_variance) / current_variance

                regime_sensitivities[regime.value] = sensitivity

        return regime_sensitivities

    async def _calculate_contagion_vulnerability(
        self,
        portfolio: Dict[str, float],
        correlation_matrix: CorrelationMatrix
    ) -> Dict[str, float]:
        """Calculate portfolio vulnerability to contagion events"""
        vulnerabilities = {}

        for asset in portfolio.keys():
            # Simulate shock to this asset
            shock_events = [{'asset': asset, 'magnitude': 0.2}]  # 20% shock

            # Detect potential contagion
            contagion_signals = await self.detect_contagion_risk(shock_events)

            if contagion_signals:
                signal = contagion_signals[0]
                # Calculate portfolio exposure to affected assets
                affected_exposure = sum(
                    portfolio.get(affected_asset, 0)
                    for affected_asset in signal.affected_assets
                )

                vulnerability = signal.contagion_strength * affected_exposure
            else:
                vulnerability = 0.0

            vulnerabilities[asset] = vulnerability

        return vulnerabilities

    def _assess_portfolio_correlation_risk(
        self,
        diversification_ratio: float,
        concentration_risk: Dict[str, float],
        contagion_vulnerability: Dict[str, float]
    ) -> str:
        """Assess overall portfolio correlation risk"""
        # Risk factors
        div_score = max(0, 1 - diversification_ratio / 2)  # Lower diversification = higher risk
        conc_score = concentration_risk['concentration_score']
        cont_score = max(contagion_vulnerability.values()) if contagion_vulnerability else 0

        # Weighted risk score
        risk_score = (
            div_score * 0.4 +
            conc_score * 0.3 +
            cont_score * 0.3
        )

        if risk_score < 0.3:
            return "LOW"
        elif risk_score < 0.6:
            return "MEDIUM"
        elif risk_score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"

    def get_correlation_statistics(self) -> Dict[str, Any]:
        """Get statistics from correlation analysis history"""
        if not self.correlation_history:
            return {"error": "No correlation history available"}

        history = self.correlation_history

        return {
            'total_analyses': len(history),
            'regime_distribution': {
                regime.value: sum(1 for h in history if h.market_regime == regime)
                for regime in MarketRegime
            },
            'regime_changes': len(self.regime_history),
            'contagion_events': len(self.contagion_signals),
            'avg_correlation_by_regime': self._calculate_avg_correlation_by_regime(),
            'most_correlated_pairs': self._identify_most_correlated_pairs(),
            'regime_persistence': self._calculate_regime_persistence()
        }

    def _calculate_avg_correlation_by_regime(self) -> Dict[str, float]:
        """Calculate average correlation by market regime"""
        regime_correlations = {}

        for regime in MarketRegime:
            regime_matrices = [h.matrix for h in self.correlation_history if h.market_regime == regime]

            if regime_matrices:
                # Calculate average correlation across all matrices
                combined_matrix = pd.concat(regime_matrices).groupby(level=0).mean()
                mask = np.triu(np.ones_like(combined_matrix, dtype=bool), k=1)
                correlations = combined_matrix.where(mask).values.flatten()
                correlations = correlations[~np.isnan(correlations)]

                regime_correlations[regime.value] = np.mean(correlations) if len(correlations) > 0 else 0.0

        return regime_correlations

    def _identify_most_correlated_pairs(self) -> List[Dict[str, Any]]:
        """Identify most consistently correlated asset pairs"""
        if not self.correlation_history:
            return []

        # Get latest correlation matrix
        latest_matrix = self.correlation_history[-1].matrix

        # Find pairs with highest correlations
        correlations = []
        for i, asset1 in enumerate(latest_matrix.columns):
            for j, asset2 in enumerate(latest_matrix.columns):
                if i < j:
                    corr_value = latest_matrix.loc[asset1, asset2]
                    correlations.append({
                        'asset1': asset1,
                        'asset2': asset2,
                        'correlation': corr_value,
                        'abs_correlation': abs(corr_value)
                    })

        # Sort by absolute correlation
        correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)

        return correlations[:10]  # Top 10 pairs

    def _calculate_regime_persistence(self) -> Dict[str, float]:
        """Calculate how long each regime typically persists"""
        if len(self.regime_history) < 2:
            return {}

        regime_durations = {regime.value: [] for regime in MarketRegime}

        for i in range(1, len(self.regime_history)):
            prev_event = self.regime_history[i-1]
            curr_event = self.regime_history[i]

            duration = (curr_event.timestamp - prev_event.timestamp).total_seconds() / 3600  # Hours
            regime_durations[prev_event.new_regime.value].append(duration)

        # Calculate average duration for each regime
        avg_durations = {}
        for regime, durations in regime_durations.items():
            if durations:
                avg_durations[regime] = np.mean(durations)

        return avg_durations


# Example usage and testing
async def main():
    """Example usage of the correlation analyzer"""
    analyzer = CorrelationAnalyzer()

    # Analyze correlations for major tokens
    correlation_result = await analyzer.analyze_correlations(
        assets=['ALGO', 'USDC', 'GARD', 'BANK', 'OPUL'],
        lookback_hours=168,
        correlation_type=CorrelationType.ADAPTIVE
    )

    print("Correlation Analysis Results:")
    print(f"Market Regime: {correlation_result.market_regime.value}")
    print(f"Correlation Matrix:")
    print(correlation_result.matrix.round(3))

    # Test contagion detection
    shock_events = [
        {'asset': 'ALGO', 'magnitude': 0.15}  # 15% ALGO shock
    ]

    contagion_signals = await analyzer.detect_contagion_risk(shock_events)

    print(f"\nContagion Analysis:")
    for signal in contagion_signals:
        print(f"Source: {signal.source_asset}")
        print(f"Affected: {signal.affected_assets}")
        print(f"Strength: {signal.contagion_strength:.3f}")
        print(f"Risk Level: {signal.risk_level}")

    # Analyze portfolio correlation risk
    portfolio = {
        'ALGO': 0.4,
        'USDC': 0.3,
        'GARD': 0.2,
        'BANK': 0.1
    }

    portfolio_risk = await analyzer.analyze_portfolio_correlation_risk(portfolio)

    print(f"\nPortfolio Correlation Risk:")
    print(f"Diversification Ratio: {portfolio_risk['diversification_ratio']:.3f}")
    print(f"Concentration Risk: {portfolio_risk['concentration_risk']['concentration_score']:.3f}")
    print(f"Risk Assessment: {portfolio_risk['risk_assessment']}")

if __name__ == "__main__":
    asyncio.run(main())