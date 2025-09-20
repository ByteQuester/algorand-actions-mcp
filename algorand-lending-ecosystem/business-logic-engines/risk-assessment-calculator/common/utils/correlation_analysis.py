"""
Correlation Analysis for Risk Assessment

Analyzes correlations between assets, protocols, and risk factors
to identify systemic risks and concentration exposures.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import statistics
from collections import defaultdict
from enum import Enum


class CorrelationType(Enum):
    """Types of correlations to analyze"""
    PRICE = "price"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    RISK_FACTOR = "risk_factor"
    BEHAVIORAL = "behavioral"


@dataclass
class CorrelationPair:
    """Correlation between two entities"""
    entity_a: str
    entity_b: str
    correlation_type: CorrelationType
    correlation_coefficient: float
    confidence_interval: Tuple[float, float]
    p_value: float
    sample_size: int
    time_period: timedelta
    last_updated: datetime


@dataclass
class CorrelationMatrix:
    """Correlation matrix for a set of entities"""
    entities: List[str]
    correlation_type: CorrelationType
    matrix: List[List[float]]
    metadata: Dict[str, Any]
    creation_timestamp: datetime


@dataclass
class RiskConcentration:
    """Risk concentration analysis"""
    risk_factor: str
    affected_entities: List[str]
    concentration_score: float
    systemic_risk_potential: float
    correlation_strength: float
    evidence: Dict[str, Any]


class CorrelationAnalyzer:
    """Advanced correlation analysis for blockchain risk assessment"""

    def __init__(self):
        self.correlation_cache = {}
        self.correlation_thresholds = {
            'high_correlation': 0.7,
            'moderate_correlation': 0.4,
            'low_correlation': 0.2
        }
        self.min_sample_size = 30
        self.max_cache_age = timedelta(hours=1)

    async def analyze_asset_correlations(
        self,
        asset_data: Dict[str, List[Dict[str, Any]]],
        correlation_types: List[CorrelationType],
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[CorrelationType, CorrelationMatrix]:
        """
        Analyze correlations between assets

        Args:
            asset_data: Dictionary mapping asset IDs to time series data
            correlation_types: Types of correlations to analyze
            time_window: Time window for analysis

        Returns:
            Dictionary mapping correlation types to correlation matrices
        """
        correlation_matrices = {}

        for corr_type in correlation_types:
            matrix = await self._calculate_correlation_matrix(
                asset_data, corr_type, time_window
            )
            correlation_matrices[corr_type] = matrix

        return correlation_matrices

    async def detect_risk_concentrations(
        self,
        portfolio_data: Dict[str, Any],
        correlation_matrices: Dict[CorrelationType, CorrelationMatrix]
    ) -> List[RiskConcentration]:
        """
        Detect risk concentrations in portfolio

        Args:
            portfolio_data: Portfolio composition and risk data
            correlation_matrices: Correlation matrices for analysis

        Returns:
            List of detected risk concentrations
        """
        concentrations = []

        # Analyze price correlation concentrations
        if CorrelationType.PRICE in correlation_matrices:
            price_concentrations = await self._analyze_price_concentrations(
                portfolio_data, correlation_matrices[CorrelationType.PRICE]
            )
            concentrations.extend(price_concentrations)

        # Analyze liquidity correlation concentrations
        if CorrelationType.LIQUIDITY in correlation_matrices:
            liquidity_concentrations = await self._analyze_liquidity_concentrations(
                portfolio_data, correlation_matrices[CorrelationType.LIQUIDITY]
            )
            concentrations.extend(liquidity_concentrations)

        # Analyze behavioral correlation concentrations
        if CorrelationType.BEHAVIORAL in correlation_matrices:
            behavioral_concentrations = await self._analyze_behavioral_concentrations(
                portfolio_data, correlation_matrices[CorrelationType.BEHAVIORAL]
            )
            concentrations.extend(behavioral_concentrations)

        return concentrations

    async def calculate_portfolio_correlation_risk(
        self,
        portfolio_positions: List[Dict[str, Any]],
        correlation_matrices: Dict[CorrelationType, CorrelationMatrix]
    ) -> Dict[str, float]:
        """
        Calculate portfolio-level correlation risks

        Args:
            portfolio_positions: List of portfolio positions
            correlation_matrices: Correlation matrices

        Returns:
            Dictionary of correlation risk metrics
        """
        risk_metrics = {}

        # Extract asset weights
        total_value = sum(pos.get('value', 0) for pos in portfolio_positions)
        if total_value == 0:
            return risk_metrics

        weights = [pos.get('value', 0) / total_value for pos in portfolio_positions]
        assets = [pos.get('asset', '') for pos in portfolio_positions]

        # Calculate correlation-adjusted risk
        for corr_type, matrix in correlation_matrices.items():
            if corr_type == CorrelationType.PRICE:
                risk_metrics['price_correlation_risk'] = await self._calculate_correlation_adjusted_risk(
                    weights, assets, matrix
                )
            elif corr_type == CorrelationType.VOLUME:
                risk_metrics['volume_correlation_risk'] = await self._calculate_volume_correlation_risk(
                    weights, assets, matrix
                )
            elif corr_type == CorrelationType.LIQUIDITY:
                risk_metrics['liquidity_correlation_risk'] = await self._calculate_liquidity_correlation_risk(
                    weights, assets, matrix
                )

        # Calculate overall correlation risk
        risk_metrics['overall_correlation_risk'] = await self._calculate_overall_correlation_risk(
            risk_metrics
        )

        return risk_metrics

    async def _calculate_correlation_matrix(
        self,
        asset_data: Dict[str, List[Dict[str, Any]]],
        correlation_type: CorrelationType,
        time_window: timedelta
    ) -> CorrelationMatrix:
        """Calculate correlation matrix for given type"""
        assets = list(asset_data.keys())
        n_assets = len(assets)

        # Initialize correlation matrix
        correlation_matrix = [[0.0 for _ in range(n_assets)] for _ in range(n_assets)]

        # Extract time series for each asset
        asset_series = {}
        for asset, data in asset_data.items():
            series = await self._extract_time_series(data, correlation_type, time_window)
            asset_series[asset] = series

        # Calculate pairwise correlations
        for i, asset_a in enumerate(assets):
            for j, asset_b in enumerate(assets):
                if i == j:
                    correlation_matrix[i][j] = 1.0
                elif i < j:  # Calculate only upper triangle
                    correlation = await self._calculate_pairwise_correlation(
                        asset_series[asset_a], asset_series[asset_b]
                    )
                    correlation_matrix[i][j] = correlation
                    correlation_matrix[j][i] = correlation  # Symmetric matrix

        return CorrelationMatrix(
            entities=assets,
            correlation_type=correlation_type,
            matrix=correlation_matrix,
            metadata={
                'time_window_days': time_window.days,
                'sample_sizes': {asset: len(series) for asset, series in asset_series.items()}
            },
            creation_timestamp=datetime.utcnow()
        )

    async def _extract_time_series(
        self,
        data: List[Dict[str, Any]],
        correlation_type: CorrelationType,
        time_window: timedelta
    ) -> List[float]:
        """Extract time series based on correlation type"""
        cutoff_time = datetime.utcnow() - time_window

        filtered_data = [
            item for item in data
            if datetime.fromisoformat(item.get('timestamp', '1970-01-01')) >= cutoff_time
        ]

        if correlation_type == CorrelationType.PRICE:
            return [float(item.get('price', 0)) for item in filtered_data]
        elif correlation_type == CorrelationType.VOLUME:
            return [float(item.get('volume', 0)) for item in filtered_data]
        elif correlation_type == CorrelationType.VOLATILITY:
            prices = [float(item.get('price', 0)) for item in filtered_data]
            return self._calculate_rolling_volatility(prices)
        elif correlation_type == CorrelationType.LIQUIDITY:
            return [float(item.get('liquidity', 0)) for item in filtered_data]
        else:
            return [float(item.get('value', 0)) for item in filtered_data]

    def _calculate_rolling_volatility(
        self,
        prices: List[float],
        window: int = 24
    ) -> List[float]:
        """Calculate rolling volatility from price series"""
        if len(prices) < window + 1:
            return []

        volatilities = []
        for i in range(window, len(prices)):
            window_prices = prices[i-window:i]
            returns = []
            for j in range(1, len(window_prices)):
                if window_prices[j-1] != 0:
                    ret = (window_prices[j] - window_prices[j-1]) / window_prices[j-1]
                    returns.append(ret)

            if returns:
                volatility = statistics.stdev(returns) if len(returns) > 1 else 0
                volatilities.append(volatility)

        return volatilities

    async def _calculate_pairwise_correlation(
        self,
        series_a: List[float],
        series_b: List[float]
    ) -> float:
        """Calculate Pearson correlation between two time series"""
        if len(series_a) != len(series_b) or len(series_a) < 2:
            return 0.0

        # Remove None/NaN values
        valid_pairs = [(a, b) for a, b in zip(series_a, series_b) if a is not None and b is not None]

        if len(valid_pairs) < self.min_sample_size:
            return 0.0

        series_a_clean = [pair[0] for pair in valid_pairs]
        series_b_clean = [pair[1] for pair in valid_pairs]

        # Calculate Pearson correlation coefficient
        try:
            correlation = np.corrcoef(series_a_clean, series_b_clean)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except:
            return 0.0

    async def _analyze_price_concentrations(
        self,
        portfolio_data: Dict[str, Any],
        correlation_matrix: CorrelationMatrix
    ) -> List[RiskConcentration]:
        """Analyze price correlation concentrations"""
        concentrations = []

        # Find clusters of highly correlated assets
        clusters = await self._find_correlation_clusters(
            correlation_matrix, self.correlation_thresholds['high_correlation']
        )

        for cluster in clusters:
            if len(cluster) >= 3:  # At least 3 assets in cluster
                # Calculate portfolio exposure to this cluster
                cluster_exposure = self._calculate_cluster_exposure(
                    cluster, portfolio_data
                )

                if cluster_exposure > 0.3:  # >30% exposure to cluster
                    concentration = RiskConcentration(
                        risk_factor="price_correlation",
                        affected_entities=cluster,
                        concentration_score=cluster_exposure,
                        systemic_risk_potential=min(cluster_exposure * len(cluster) / 10, 1.0),
                        correlation_strength=self._calculate_average_correlation(
                            cluster, correlation_matrix
                        ),
                        evidence={
                            'cluster_size': len(cluster),
                            'portfolio_exposure': cluster_exposure,
                            'correlation_type': 'price'
                        }
                    )
                    concentrations.append(concentration)

        return concentrations

    async def _analyze_liquidity_concentrations(
        self,
        portfolio_data: Dict[str, Any],
        correlation_matrix: CorrelationMatrix
    ) -> List[RiskConcentration]:
        """Analyze liquidity correlation concentrations"""
        concentrations = []

        # Find assets with correlated liquidity patterns
        clusters = await self._find_correlation_clusters(
            correlation_matrix, self.correlation_thresholds['moderate_correlation']
        )

        for cluster in clusters:
            if len(cluster) >= 2:
                cluster_exposure = self._calculate_cluster_exposure(
                    cluster, portfolio_data
                )

                # Liquidity concentrations are riskier than price concentrations
                if cluster_exposure > 0.2:  # >20% exposure
                    concentration = RiskConcentration(
                        risk_factor="liquidity_correlation",
                        affected_entities=cluster,
                        concentration_score=cluster_exposure,
                        systemic_risk_potential=min(cluster_exposure * 1.5, 1.0),
                        correlation_strength=self._calculate_average_correlation(
                            cluster, correlation_matrix
                        ),
                        evidence={
                            'cluster_size': len(cluster),
                            'portfolio_exposure': cluster_exposure,
                            'correlation_type': 'liquidity'
                        }
                    )
                    concentrations.append(concentration)

        return concentrations

    async def _analyze_behavioral_concentrations(
        self,
        portfolio_data: Dict[str, Any],
        correlation_matrix: CorrelationMatrix
    ) -> List[RiskConcentration]:
        """Analyze behavioral correlation concentrations"""
        concentrations = []

        # Behavioral correlations indicate potential market manipulation or coordinated behavior
        clusters = await self._find_correlation_clusters(
            correlation_matrix, self.correlation_thresholds['moderate_correlation']
        )

        for cluster in clusters:
            if len(cluster) >= 2:
                cluster_exposure = self._calculate_cluster_exposure(
                    cluster, portfolio_data
                )

                # Any significant behavioral correlation is concerning
                if cluster_exposure > 0.1:  # >10% exposure
                    concentration = RiskConcentration(
                        risk_factor="behavioral_correlation",
                        affected_entities=cluster,
                        concentration_score=cluster_exposure,
                        systemic_risk_potential=min(cluster_exposure * 2.0, 1.0),
                        correlation_strength=self._calculate_average_correlation(
                            cluster, correlation_matrix
                        ),
                        evidence={
                            'cluster_size': len(cluster),
                            'portfolio_exposure': cluster_exposure,
                            'correlation_type': 'behavioral',
                            'risk_indicator': 'potential_manipulation'
                        }
                    )
                    concentrations.append(concentration)

        return concentrations

    async def _find_correlation_clusters(
        self,
        correlation_matrix: CorrelationMatrix,
        threshold: float
    ) -> List[List[str]]:
        """Find clusters of correlated entities"""
        entities = correlation_matrix.entities
        matrix = correlation_matrix.matrix
        n = len(entities)

        # Use simple clustering based on correlation threshold
        visited = [False] * n
        clusters = []

        for i in range(n):
            if visited[i]:
                continue

            # Start new cluster
            cluster = [entities[i]]
            visited[i] = True

            # Find all entities correlated with this one
            for j in range(i + 1, n):
                if not visited[j] and abs(matrix[i][j]) >= threshold:
                    cluster.append(entities[j])
                    visited[j] = True

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    def _calculate_cluster_exposure(
        self,
        cluster: List[str],
        portfolio_data: Dict[str, Any]
    ) -> float:
        """Calculate portfolio exposure to a cluster of assets"""
        positions = portfolio_data.get('positions', [])
        total_value = sum(pos.get('value', 0) for pos in positions)

        if total_value == 0:
            return 0.0

        cluster_value = 0.0
        for position in positions:
            if position.get('asset', '') in cluster:
                cluster_value += position.get('value', 0)

        return cluster_value / total_value

    def _calculate_average_correlation(
        self,
        cluster: List[str],
        correlation_matrix: CorrelationMatrix
    ) -> float:
        """Calculate average correlation within a cluster"""
        entities = correlation_matrix.entities
        matrix = correlation_matrix.matrix

        correlations = []
        for i, entity_a in enumerate(cluster):
            for j, entity_b in enumerate(cluster):
                if i < j:  # Avoid double counting
                    idx_a = entities.index(entity_a) if entity_a in entities else -1
                    idx_b = entities.index(entity_b) if entity_b in entities else -1

                    if idx_a >= 0 and idx_b >= 0:
                        correlations.append(abs(matrix[idx_a][idx_b]))

        return statistics.mean(correlations) if correlations else 0.0

    async def _calculate_correlation_adjusted_risk(
        self,
        weights: List[float],
        assets: List[str],
        correlation_matrix: CorrelationMatrix
    ) -> float:
        """Calculate correlation-adjusted portfolio risk"""
        if len(weights) != len(assets):
            return 0.0

        entities = correlation_matrix.entities
        matrix = correlation_matrix.matrix

        # Build weight vector aligned with correlation matrix
        aligned_weights = []
        for entity in entities:
            if entity in assets:
                idx = assets.index(entity)
                aligned_weights.append(weights[idx])
            else:
                aligned_weights.append(0.0)

        # Calculate portfolio variance using correlation matrix
        portfolio_variance = 0.0
        n = len(aligned_weights)

        for i in range(n):
            for j in range(n):
                # Assume unit variance for simplicity (would use actual variances in practice)
                correlation = matrix[i][j] if i < len(matrix) and j < len(matrix[i]) else 0.0
                portfolio_variance += aligned_weights[i] * aligned_weights[j] * correlation

        return min(abs(portfolio_variance), 1.0)

    async def _calculate_volume_correlation_risk(
        self,
        weights: List[float],
        assets: List[str],
        correlation_matrix: CorrelationMatrix
    ) -> float:
        """Calculate volume correlation risk"""
        # Volume correlation risk is generally lower than price correlation risk
        base_risk = await self._calculate_correlation_adjusted_risk(
            weights, assets, correlation_matrix
        )
        return base_risk * 0.6

    async def _calculate_liquidity_correlation_risk(
        self,
        weights: List[float],
        assets: List[str],
        correlation_matrix: CorrelationMatrix
    ) -> float:
        """Calculate liquidity correlation risk"""
        # Liquidity correlation risk is higher than price correlation risk
        base_risk = await self._calculate_correlation_adjusted_risk(
            weights, assets, correlation_matrix
        )
        return min(base_risk * 1.5, 1.0)

    async def _calculate_overall_correlation_risk(
        self,
        risk_metrics: Dict[str, float]
    ) -> float:
        """Calculate overall correlation risk from component risks"""
        weights = {
            'price_correlation_risk': 0.4,
            'volume_correlation_risk': 0.2,
            'liquidity_correlation_risk': 0.4
        }

        overall_risk = 0.0
        total_weight = 0.0

        for risk_type, weight in weights.items():
            if risk_type in risk_metrics:
                overall_risk += risk_metrics[risk_type] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return overall_risk / total_weight

    async def calculate_correlation_stability(
        self,
        correlation_history: List[CorrelationMatrix],
        lookback_periods: int = 5
    ) -> Dict[str, float]:
        """Calculate stability of correlations over time"""
        if len(correlation_history) < 2:
            return {}

        stability_metrics = {}

        # Take last N correlation matrices
        recent_matrices = correlation_history[-lookback_periods:]

        if len(recent_matrices) < 2:
            return stability_metrics

        # Calculate correlation stability for each pair
        entities = recent_matrices[0].entities
        n = len(entities)

        total_stability = 0.0
        pair_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                correlations_over_time = []

                for matrix in recent_matrices:
                    if (i < len(matrix.matrix) and
                        j < len(matrix.matrix[i])):
                        correlations_over_time.append(matrix.matrix[i][j])

                if len(correlations_over_time) >= 2:
                    # Calculate stability as inverse of standard deviation
                    std_dev = statistics.stdev(correlations_over_time)
                    stability = 1.0 / (1.0 + std_dev)  # Higher std = lower stability
                    total_stability += stability
                    pair_count += 1

        stability_metrics['average_correlation_stability'] = (
            total_stability / pair_count if pair_count > 0 else 0.0
        )

        # Calculate regime change risk (instability risk)
        stability_metrics['regime_change_risk'] = 1.0 - stability_metrics['average_correlation_stability']

        return stability_metrics

    def detect_correlation_breakdowns(
        self,
        current_matrix: CorrelationMatrix,
        historical_matrix: CorrelationMatrix,
        breakdown_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Detect significant correlation breakdowns"""
        breakdowns = []

        if (current_matrix.entities != historical_matrix.entities or
            len(current_matrix.matrix) != len(historical_matrix.matrix)):
            return breakdowns

        entities = current_matrix.entities
        n = len(entities)

        for i in range(n):
            for j in range(i + 1, n):
                current_corr = current_matrix.matrix[i][j]
                historical_corr = historical_matrix.matrix[i][j]

                correlation_change = abs(current_corr - historical_corr)

                if correlation_change > breakdown_threshold:
                    breakdown = {
                        'entity_a': entities[i],
                        'entity_b': entities[j],
                        'current_correlation': current_corr,
                        'historical_correlation': historical_corr,
                        'change_magnitude': correlation_change,
                        'breakdown_type': 'increase' if current_corr > historical_corr else 'decrease'
                    }
                    breakdowns.append(breakdown)

        return sorted(breakdowns, key=lambda x: x['change_magnitude'], reverse=True)