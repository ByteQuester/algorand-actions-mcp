"""
Collateral Rate Calculator

Sophisticated calculator for determining interest rate adjustments based on
collateral characteristics, risk metrics, and market conditions.
"""

import asyncio
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .config import CollateralAdjustmentConfig
from .constants import CollateralAdjustmentConstants, CollateralTier, RiskAdjustmentType


@dataclass
class CollateralAsset:
    """Represents a collateral asset with its properties"""
    symbol: str
    amount: float
    current_price: float
    market_cap: float
    daily_volume: float
    volatility_24h: float
    volatility_30d: float
    liquidity_score: float
    security_rating: str
    asset_tier: CollateralTier
    metadata: Dict[str, Any]


@dataclass
class CollateralPortfolio:
    """Represents a portfolio of collateral assets"""
    assets: List[CollateralAsset]
    total_value_usd: float
    loan_amount_usd: float
    current_ltv: float
    diversification_score: float
    correlation_matrix: Optional[np.ndarray] = None


@dataclass
class RateAdjustmentResult:
    """Result of rate adjustment calculation"""
    base_rate: float
    total_adjustment: float
    final_rate: float
    adjustment_breakdown: Dict[str, float]
    risk_factors: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float


class CollateralRateCalculator:
    """
    Advanced calculator for collateral-based interest rate adjustments
    """

    def __init__(self, config: CollateralAdjustmentConfig):
        """Initialize the calculator with configuration"""
        self.config = config
        self.constants = CollateralAdjustmentConstants()
        self._risk_cache = {}
        self._correlation_cache = {}

    async def calculate_adjusted_rate(
        self,
        base_rate: float,
        portfolio: CollateralPortfolio,
        loan_duration_days: int = 30,
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> RateAdjustmentResult:
        """
        Calculate the adjusted interest rate based on collateral

        Args:
            base_rate: Base interest rate before adjustments
            portfolio: Collateral portfolio
            loan_duration_days: Duration of the loan
            market_conditions: Current market conditions

        Returns:
            RateAdjustmentResult: Detailed adjustment result
        """
        adjustments = {}
        risk_factors = {}
        recommendations = []

        # 1. LTV-based adjustment
        ltv_adjustment = self._calculate_ltv_adjustment(portfolio.current_ltv)
        adjustments['ltv_adjustment'] = ltv_adjustment

        # 2. Asset quality adjustment
        quality_adjustment = self._calculate_asset_quality_adjustment(portfolio.assets)
        adjustments['quality_adjustment'] = quality_adjustment

        # 3. Volatility adjustment
        volatility_adjustment = self._calculate_volatility_adjustment(portfolio.assets)
        adjustments['volatility_adjustment'] = volatility_adjustment

        # 4. Liquidity adjustment
        liquidity_adjustment = self._calculate_liquidity_adjustment(portfolio.assets)
        adjustments['liquidity_adjustment'] = liquidity_adjustment

        # 5. Diversification adjustment
        diversification_adjustment = self._calculate_diversification_adjustment(portfolio)
        adjustments['diversification_adjustment'] = diversification_adjustment

        # 6. Correlation adjustment
        correlation_adjustment = await self._calculate_correlation_adjustment(portfolio)
        adjustments['correlation_adjustment'] = correlation_adjustment

        # 7. Duration adjustment
        duration_adjustment = self._calculate_duration_adjustment(loan_duration_days)
        adjustments['duration_adjustment'] = duration_adjustment

        # 8. Market stress adjustment
        market_adjustment = self._calculate_market_stress_adjustment(market_conditions)
        adjustments['market_stress_adjustment'] = market_adjustment

        # 9. Security rating adjustment
        security_adjustment = self._calculate_security_adjustment(portfolio.assets)
        adjustments['security_adjustment'] = security_adjustment

        # Calculate total adjustment
        total_adjustment = sum(adjustments.values())

        # Apply bounds
        total_adjustment = max(
            self.constants.MIN_RATE_ADJUSTMENT,
            min(self.constants.MAX_RATE_ADJUSTMENT, total_adjustment)
        )

        final_rate = max(
            self.config.rate_calculation.minimum_interest_rate,
            min(self.config.rate_calculation.maximum_interest_rate, base_rate + total_adjustment)
        )

        # Generate risk factors and recommendations
        risk_factors = self._analyze_risk_factors(portfolio, adjustments)
        recommendations = self._generate_recommendations(portfolio, adjustments, risk_factors)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(portfolio, adjustments)

        return RateAdjustmentResult(
            base_rate=base_rate,
            total_adjustment=total_adjustment,
            final_rate=final_rate,
            adjustment_breakdown=adjustments,
            risk_factors=risk_factors,
            recommendations=recommendations,
            confidence_score=confidence_score
        )

    def _calculate_ltv_adjustment(self, ltv: float) -> float:
        """Calculate adjustment based on loan-to-value ratio"""
        ltv_thresholds = sorted(self.constants.LTV_RATE_ADJUSTMENTS.keys())

        for i, threshold in enumerate(ltv_thresholds):
            if ltv <= threshold:
                return self.constants.LTV_RATE_ADJUSTMENTS[threshold]

        # If LTV exceeds all thresholds, use the highest adjustment
        return self.constants.LTV_RATE_ADJUSTMENTS[ltv_thresholds[-1]]

    def _calculate_asset_quality_adjustment(self, assets: List[CollateralAsset]) -> float:
        """Calculate adjustment based on asset quality"""
        total_value = sum(asset.amount * asset.current_price for asset in assets)
        weighted_adjustment = 0.0

        for asset in assets:
            asset_value = asset.amount * asset.current_price
            weight = asset_value / total_value

            # Get risk premium for this asset
            risk_premium = self._get_asset_risk_premium(asset)
            weighted_adjustment += weight * risk_premium

        return weighted_adjustment

    def _get_asset_risk_premium(self, asset: CollateralAsset) -> float:
        """Get risk premium for a specific asset"""
        # Check for exact symbol match first
        if asset.symbol in self.constants.ASSET_RISK_PREMIUMS:
            return self.constants.ASSET_RISK_PREMIUMS[asset.symbol]

        # Fallback to category-based premium
        if asset.symbol == 'ALGO':
            return self.constants.ASSET_RISK_PREMIUMS['ALGO']
        elif asset.symbol in ['USDC', 'USDT']:
            return self.constants.ASSET_RISK_PREMIUMS.get(asset.symbol, 0.0005)
        elif asset.metadata.get('verified', False):
            return self.constants.ASSET_RISK_PREMIUMS['ASA_VERIFIED']
        else:
            return self.constants.ASSET_RISK_PREMIUMS['ASA_UNVERIFIED']

    def _calculate_volatility_adjustment(self, assets: List[CollateralAsset]) -> float:
        """Calculate adjustment based on portfolio volatility"""
        total_value = sum(asset.amount * asset.current_price for asset in assets)
        weighted_volatility = 0.0

        for asset in assets:
            asset_value = asset.amount * asset.current_price
            weight = asset_value / total_value
            weighted_volatility += weight * asset.volatility_30d

        # Find appropriate volatility adjustment
        vol_thresholds = sorted(self.constants.VOLATILITY_ADJUSTMENTS.keys())
        for threshold in vol_thresholds:
            if weighted_volatility <= threshold:
                return self.constants.VOLATILITY_ADJUSTMENTS[threshold]

        # If volatility exceeds all thresholds, use the highest adjustment
        return self.constants.VOLATILITY_ADJUSTMENTS[vol_thresholds[-1]]

    def _calculate_liquidity_adjustment(self, assets: List[CollateralAsset]) -> float:
        """Calculate adjustment based on portfolio liquidity"""
        total_value = sum(asset.amount * asset.current_price for asset in assets)
        weighted_adjustment = 0.0

        for asset in assets:
            asset_value = asset.amount * asset.current_price
            weight = asset_value / total_value

            # Determine liquidity category
            liquidity_category = self.constants.get_liquidity_category(
                asset.daily_volume, asset.market_cap
            )

            adjustment = self.constants.LIQUIDITY_ADJUSTMENTS[liquidity_category]
            weighted_adjustment += weight * adjustment

        return weighted_adjustment

    def _calculate_diversification_adjustment(self, portfolio: CollateralPortfolio) -> float:
        """Calculate adjustment based on portfolio diversification"""
        num_assets = len(portfolio.assets)

        if num_assets == 1:
            return self.constants.DIVERSIFICATION_DISCOUNTS['single_asset']
        elif num_assets == 2:
            return self.constants.DIVERSIFICATION_DISCOUNTS['two_assets']
        else:
            # Check for cross-category diversification
            categories = set()
            for asset in portfolio.assets:
                if asset.symbol == 'ALGO':
                    categories.add('native')
                elif asset.symbol in ['USDC', 'USDT']:
                    categories.add('stablecoin')
                elif asset.metadata.get('verified', False):
                    categories.add('verified_asa')
                else:
                    categories.add('unverified_asa')

            if len(categories) >= 3:
                return self.constants.DIVERSIFICATION_DISCOUNTS['cross_category']
            else:
                return self.constants.DIVERSIFICATION_DISCOUNTS['three_plus_assets']

    async def _calculate_correlation_adjustment(self, portfolio: CollateralPortfolio) -> float:
        """Calculate adjustment based on asset correlations"""
        if len(portfolio.assets) < 2:
            return 0.0

        # Calculate average correlation
        correlations = []
        for i, asset1 in enumerate(portfolio.assets):
            for asset2 in portfolio.assets[i+1:]:
                correlation = await self._get_asset_correlation(asset1.symbol, asset2.symbol)
                correlations.append(abs(correlation))

        if not correlations:
            return 0.0

        avg_correlation = sum(correlations) / len(correlations)

        # Determine correlation category
        if avg_correlation < 0.3:
            category = 'low_correlation'
        elif avg_correlation < 0.6:
            category = 'medium_correlation'
        elif avg_correlation < 0.9:
            category = 'high_correlation'
        else:
            category = 'perfect_correlation'

        return self.constants.CORRELATION_ADJUSTMENTS[category]

    async def _get_asset_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two assets (cached)"""
        cache_key = tuple(sorted([symbol1, symbol2]))

        if cache_key in self._correlation_cache:
            cached_data = self._correlation_cache[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < 3600:  # 1 hour cache
                return cached_data['correlation']

        # Calculate correlation (simplified - in practice would use historical price data)
        correlation = self._calculate_asset_correlation(symbol1, symbol2)

        self._correlation_cache[cache_key] = {
            'correlation': correlation,
            'timestamp': datetime.now()
        }

        return correlation

    def _calculate_asset_correlation(self, symbol1: str, symbol2: str) -> float:
        """Calculate correlation between assets (simplified implementation)"""
        # This is a simplified implementation
        # In practice, this would use historical price data

        if symbol1 == symbol2:
            return 1.0

        # Default correlations based on asset types
        asset_types = {}
        for symbol in [symbol1, symbol2]:
            if symbol == 'ALGO':
                asset_types[symbol] = 'native'
            elif symbol in ['USDC', 'USDT']:
                asset_types[symbol] = 'stablecoin'
            else:
                asset_types[symbol] = 'asa'

        # Stablecoins are highly correlated
        if asset_types[symbol1] == 'stablecoin' and asset_types[symbol2] == 'stablecoin':
            return 0.95

        # Different types have lower correlation
        if asset_types[symbol1] != asset_types[symbol2]:
            return 0.3

        # Same type (ASAs) have medium correlation
        return 0.6

    def _calculate_duration_adjustment(self, duration_days: int) -> float:
        """Calculate adjustment based on loan duration"""
        duration_thresholds = sorted(self.constants.DURATION_ADJUSTMENTS.keys())

        for threshold in duration_thresholds:
            if duration_days <= threshold:
                return self.constants.DURATION_ADJUSTMENTS[threshold]

        # If duration exceeds all thresholds, use the highest adjustment
        return self.constants.DURATION_ADJUSTMENTS[duration_thresholds[-1]]

    def _calculate_market_stress_adjustment(self, market_conditions: Optional[Dict[str, Any]]) -> float:
        """Calculate adjustment based on market stress conditions"""
        if not market_conditions:
            return 0.0

        adjustment = 0.0

        # Check for various stress indicators
        if market_conditions.get('market_stress', False):
            adjustment += self.constants.EMERGENCY_FACTORS['market_stress']

        if market_conditions.get('liquidity_crisis', False):
            adjustment += self.constants.EMERGENCY_FACTORS['liquidity_crisis']

        if market_conditions.get('protocol_exploit', False):
            adjustment += self.constants.EMERGENCY_FACTORS['protocol_exploit']

        if market_conditions.get('regulatory_uncertainty', False):
            adjustment += self.constants.EMERGENCY_FACTORS['regulatory_uncertainty']

        return adjustment

    def _calculate_security_adjustment(self, assets: List[CollateralAsset]) -> float:
        """Calculate adjustment based on smart contract security ratings"""
        total_value = sum(asset.amount * asset.current_price for asset in assets)
        weighted_adjustment = 0.0

        for asset in assets:
            asset_value = asset.amount * asset.current_price
            weight = asset_value / total_value

            security_rating = asset.security_rating or 'UNRATED'
            adjustment = self.constants.SECURITY_RATING_ADJUSTMENTS.get(security_rating, 0.006)
            weighted_adjustment += weight * adjustment

        return weighted_adjustment

    def _analyze_risk_factors(
        self,
        portfolio: CollateralPortfolio,
        adjustments: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze and categorize risk factors"""
        risk_factors = {}

        # LTV risk
        if portfolio.current_ltv > self.constants.MONITORING_THRESHOLDS['ltv_warning']:
            risk_factors['high_ltv'] = {
                'level': 'high' if portfolio.current_ltv > self.constants.MONITORING_THRESHOLDS['ltv_critical'] else 'medium',
                'value': portfolio.current_ltv,
                'threshold': self.constants.MONITORING_THRESHOLDS['ltv_warning']
            }

        # Concentration risk
        if len(portfolio.assets) < 3:
            risk_factors['concentration_risk'] = {
                'level': 'high' if len(portfolio.assets) == 1 else 'medium',
                'asset_count': len(portfolio.assets)
            }

        # Volatility risk
        avg_volatility = sum(asset.volatility_30d for asset in portfolio.assets) / len(portfolio.assets)
        if avg_volatility > 0.3:
            risk_factors['high_volatility'] = {
                'level': 'high' if avg_volatility > 0.5 else 'medium',
                'value': avg_volatility
            }

        # Liquidity risk
        low_liquidity_assets = [
            asset for asset in portfolio.assets
            if self.constants.get_liquidity_category(asset.daily_volume, asset.market_cap) in ['low_liquidity', 'very_low_liquidity']
        ]
        if low_liquidity_assets:
            risk_factors['liquidity_risk'] = {
                'level': 'high' if len(low_liquidity_assets) > len(portfolio.assets) / 2 else 'medium',
                'affected_assets': [asset.symbol for asset in low_liquidity_assets]
            }

        return risk_factors

    def _generate_recommendations(
        self,
        portfolio: CollateralPortfolio,
        adjustments: Dict[str, float],
        risk_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # LTV recommendations
        if 'high_ltv' in risk_factors:
            recommendations.append(
                f"Consider reducing LTV from {portfolio.current_ltv:.1%} to below "
                f"{self.constants.MONITORING_THRESHOLDS['ltv_warning']:.1%} to reduce rate adjustments"
            )

        # Diversification recommendations
        if 'concentration_risk' in risk_factors:
            recommendations.append(
                "Add more diverse collateral assets to reduce concentration risk and qualify for diversification discounts"
            )

        # Volatility recommendations
        if 'high_volatility' in risk_factors:
            recommendations.append(
                "Consider adding stable assets (USDC, USDT) to reduce portfolio volatility"
            )

        # Liquidity recommendations
        if 'liquidity_risk' in risk_factors:
            recommendations.append(
                "Replace low-liquidity assets with more liquid alternatives to reduce liquidity premiums"
            )

        # Security recommendations
        unrated_assets = [asset for asset in portfolio.assets if asset.security_rating == 'UNRATED']
        if unrated_assets:
            recommendations.append(
                f"Security audit recommended for: {', '.join(asset.symbol for asset in unrated_assets)}"
            )

        return recommendations

    def _calculate_confidence_score(
        self,
        portfolio: CollateralPortfolio,
        adjustments: Dict[str, float]
    ) -> float:
        """Calculate confidence score for the rate adjustment"""
        confidence_factors = []

        # Data quality factors
        for asset in portfolio.assets:
            if asset.market_cap > 0 and asset.daily_volume > 0:
                confidence_factors.append(0.2)
            else:
                confidence_factors.append(0.1)

        # Portfolio diversity factor
        if len(portfolio.assets) >= 3:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)

        # Volatility data quality
        valid_volatility = sum(1 for asset in portfolio.assets if asset.volatility_30d > 0)
        if valid_volatility == len(portfolio.assets):
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)

        # Security rating availability
        rated_assets = sum(1 for asset in portfolio.assets if asset.security_rating != 'UNRATED')
        if rated_assets >= len(portfolio.assets) * 0.8:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)

        # Adjustment magnitude reasonableness
        total_adjustment = sum(adjustments.values())
        if abs(total_adjustment) < 0.02:  # Less than 200 basis points
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)

        return min(1.0, sum(confidence_factors))