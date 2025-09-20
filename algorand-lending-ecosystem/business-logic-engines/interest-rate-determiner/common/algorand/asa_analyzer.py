"""
ASA (Algorand Standard Asset) analyzer for risk assessment and valuation.

Provides comprehensive analysis of ASA tokens including:
- Risk assessment and classification
- Market data integration
- Liquidity analysis
- Portfolio valuation
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging

from ..models.algorand_models import ASAToken, AssetType, AssetRiskLevel

logger = logging.getLogger(__name__)


@dataclass
class TokenMetrics:
    """Comprehensive token metrics for ASA analysis"""
    asset_id: int
    current_price_algo: Decimal
    current_price_usd: Decimal

    # Market metrics
    market_cap_usd: Decimal = Decimal('0')
    volume_24h_usd: Decimal = Decimal('0')
    volume_7d_usd: Decimal = Decimal('0')
    price_change_24h: Decimal = Decimal('0')
    price_change_7d: Decimal = Decimal('0')

    # Liquidity metrics
    liquidity_score: float = 0.0  # 0-1, higher = more liquid
    bid_ask_spread: Decimal = Decimal('0')
    order_book_depth: Decimal = Decimal('0')

    # Volatility metrics
    volatility_24h: Decimal = Decimal('0')
    volatility_7d: Decimal = Decimal('0')
    volatility_30d: Decimal = Decimal('0')

    # Trading metrics
    trade_count_24h: int = 0
    unique_traders_24h: int = 0
    average_trade_size: Decimal = Decimal('0')

    # Risk metrics
    risk_level: AssetRiskLevel = AssetRiskLevel.UNKNOWN
    correlation_with_algo: float = 0.0
    beta_vs_algo: float = 1.0

    # Quality indicators
    is_verified: bool = False
    audit_score: float = 0.0
    community_score: float = 0.0

    @property
    def is_liquid(self) -> bool:
        """Check if asset has sufficient liquidity"""
        return self.liquidity_score > 0.3 and self.volume_24h_usd > Decimal('1000')

    @property
    def is_stable(self) -> bool:
        """Check if asset shows stable price behavior"""
        return self.volatility_24h < Decimal('0.05')  # Less than 5% daily volatility


@dataclass
class ASAValuation:
    """Valuation result for an ASA position"""
    asset_id: int
    balance: Decimal
    decimals: int

    # Valuation
    value_algo: Decimal
    value_usd: Decimal
    unit_price_algo: Decimal
    unit_price_usd: Decimal

    # Risk assessment
    position_risk_score: float = 0.0
    confidence_level: float = 1.0

    # Market data timestamp
    valuation_timestamp: datetime = field(default_factory=datetime.now)

    @property
    def value_in_base_units(self) -> Decimal:
        """Get value in smallest unit of the asset"""
        return self.balance * (Decimal('10') ** self.decimals)


class ASAAnalyzer:
    """
    Comprehensive ASA analyzer for DeFi risk assessment.

    Provides risk classification, valuation, and portfolio analysis
    for Algorand Standard Assets.
    """

    def __init__(self, algorand_client=None, price_oracle=None):
        self.algorand_client = algorand_client
        self.price_oracle = price_oracle
        self._asset_cache: Dict[int, ASAToken] = {}
        self._metrics_cache: Dict[int, TokenMetrics] = {}
        self._price_cache: Dict[int, Tuple[Decimal, Decimal, datetime]] = {}  # ALGO, USD, timestamp

    async def analyze_asset(self, asset_id: int) -> TokenMetrics:
        """
        Perform comprehensive analysis of an ASA.

        Returns detailed metrics including risk assessment,
        liquidity analysis, and market data.
        """
        if asset_id in self._metrics_cache:
            return self._metrics_cache[asset_id]

        try:
            # Get basic asset information
            asset_info = await self._get_asset_info(asset_id)
            if not asset_info:
                raise ValueError(f"Asset {asset_id} not found")

            # Get market data
            price_data = await self._get_price_data(asset_id)
            volume_data = await self._get_volume_data(asset_id)
            liquidity_data = await self._get_liquidity_data(asset_id)

            # Calculate risk metrics
            risk_assessment = await self._assess_risk(asset_id, asset_info)

            # Build comprehensive metrics
            metrics = TokenMetrics(
                asset_id=asset_id,
                current_price_algo=price_data.get('price_algo', Decimal('0')),
                current_price_usd=price_data.get('price_usd', Decimal('0')),
                market_cap_usd=price_data.get('market_cap', Decimal('0')),
                volume_24h_usd=volume_data.get('volume_24h', Decimal('0')),
                volume_7d_usd=volume_data.get('volume_7d', Decimal('0')),
                price_change_24h=price_data.get('change_24h', Decimal('0')),
                price_change_7d=price_data.get('change_7d', Decimal('0')),
                liquidity_score=liquidity_data.get('liquidity_score', 0.0),
                bid_ask_spread=liquidity_data.get('spread', Decimal('0')),
                volatility_24h=await self._calculate_volatility(asset_id, days=1),
                volatility_7d=await self._calculate_volatility(asset_id, days=7),
                volatility_30d=await self._calculate_volatility(asset_id, days=30),
                risk_level=risk_assessment['risk_level'],
                is_verified=risk_assessment['is_verified'],
                audit_score=risk_assessment['audit_score']
            )

            self._metrics_cache[asset_id] = metrics
            return metrics

        except Exception as e:
            logger.error(f"Error analyzing asset {asset_id}: {e}")
            raise

    async def value_asa_position(
        self,
        asset_id: int,
        balance: Decimal,
        decimals: int
    ) -> ASAValuation:
        """
        Value an ASA position in ALGO and USD.

        Args:
            asset_id: The ASA ID
            balance: Balance in base units
            decimals: Number of decimal places for the asset
        """
        try:
            # Get current prices
            prices = await self._get_current_prices(asset_id)
            price_algo = prices['price_algo']
            price_usd = prices['price_usd']

            # Calculate position value
            position_balance = balance / (Decimal('10') ** decimals)
            value_algo = position_balance * price_algo
            value_usd = position_balance * price_usd

            # Get risk assessment
            metrics = await self.analyze_asset(asset_id)
            risk_score = self._calculate_position_risk(metrics, value_usd)
            confidence = self._calculate_valuation_confidence(metrics)

            return ASAValuation(
                asset_id=asset_id,
                balance=position_balance,
                decimals=decimals,
                value_algo=value_algo,
                value_usd=value_usd,
                unit_price_algo=price_algo,
                unit_price_usd=price_usd,
                position_risk_score=risk_score,
                confidence_level=confidence
            )

        except Exception as e:
            logger.error(f"Error valuing position for asset {asset_id}: {e}")
            raise

    async def analyze_portfolio(
        self,
        asset_positions: List[Tuple[int, Decimal, int]]  # (asset_id, balance, decimals)
    ) -> Dict[str, Any]:
        """
        Analyze a complete ASA portfolio for risk and diversification.

        Returns portfolio-level metrics including:
        - Total value and composition
        - Risk distribution
        - Diversification metrics
        - Concentration analysis
        """
        try:
            portfolio_analysis = {
                'total_value_algo': Decimal('0'),
                'total_value_usd': Decimal('0'),
                'position_count': len(asset_positions),
                'positions': [],
                'risk_distribution': {
                    'very_low': Decimal('0'),
                    'low': Decimal('0'),
                    'medium': Decimal('0'),
                    'high': Decimal('0'),
                    'very_high': Decimal('0'),
                    'unknown': Decimal('0')
                },
                'quality_metrics': {
                    'verified_percentage': 0.0,
                    'liquid_percentage': 0.0,
                    'stable_percentage': 0.0
                },
                'concentration_risk': {
                    'largest_position_pct': 0.0,
                    'top_3_concentration': 0.0,
                    'top_5_concentration': 0.0,
                    'herfindahl_index': 0.0
                },
                'overall_risk_score': 0.0,
                'diversification_score': 0.0
            }

            # Analyze each position
            valuations = []
            for asset_id, balance, decimals in asset_positions:
                valuation = await self.value_asa_position(asset_id, balance, decimals)
                metrics = await self.analyze_asset(asset_id)

                position_data = {
                    'asset_id': asset_id,
                    'valuation': valuation,
                    'metrics': metrics
                }
                valuations.append(position_data)
                portfolio_analysis['positions'].append(position_data)

                # Add to totals
                portfolio_analysis['total_value_algo'] += valuation.value_algo
                portfolio_analysis['total_value_usd'] += valuation.value_usd

            # Calculate portfolio metrics
            if portfolio_analysis['total_value_usd'] > 0:
                await self._calculate_portfolio_metrics(portfolio_analysis, valuations)

            return portfolio_analysis

        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            raise

    async def _get_asset_info(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """Get basic asset information from Algorand"""
        if self.algorand_client:
            return await self.algorand_client.get_asset_info(asset_id)

        # Mock implementation
        return {
            'index': asset_id,
            'params': {
                'creator': 'MOCK_CREATOR',
                'total': 1000000000,
                'decimals': 6,
                'name': f'Mock Asset {asset_id}',
                'unit-name': 'MOCK'
            }
        }

    async def _get_price_data(self, asset_id: int) -> Dict[str, Decimal]:
        """Get current price data for asset"""
        # Check cache first
        if asset_id in self._price_cache:
            price_algo, price_usd, timestamp = self._price_cache[asset_id]
            if datetime.now() - timestamp < timedelta(minutes=5):  # 5-minute cache
                return {
                    'price_algo': price_algo,
                    'price_usd': price_usd,
                    'market_cap': price_usd * Decimal('1000000'),  # Mock market cap
                    'change_24h': Decimal('0.05'),  # Mock 5% change
                    'change_7d': Decimal('0.12')   # Mock 12% change
                }

        # Mock implementation
        price_algo = Decimal('0.1')  # Mock price in ALGO
        price_usd = Decimal('0.015')  # Mock price in USD

        self._price_cache[asset_id] = (price_algo, price_usd, datetime.now())

        return {
            'price_algo': price_algo,
            'price_usd': price_usd,
            'market_cap': price_usd * Decimal('1000000'),
            'change_24h': Decimal('0.05'),
            'change_7d': Decimal('0.12')
        }

    async def _get_volume_data(self, asset_id: int) -> Dict[str, Decimal]:
        """Get trading volume data"""
        # Mock implementation
        return {
            'volume_24h': Decimal('10000'),
            'volume_7d': Decimal('70000'),
            'trade_count_24h': 150,
            'unique_traders_24h': 45
        }

    async def _get_liquidity_data(self, asset_id: int) -> Dict[str, Any]:
        """Get liquidity metrics for asset"""
        # Mock implementation
        return {
            'liquidity_score': 0.6,
            'spread': Decimal('0.005'),  # 0.5% spread
            'order_book_depth': Decimal('50000')
        }

    async def _assess_risk(self, asset_id: int, asset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk level for an asset"""
        # Mock risk assessment logic
        risk_factors = {
            'age_score': 0.8,  # How long has it existed
            'volume_score': 0.6,  # Trading volume
            'liquidity_score': 0.7,  # Market liquidity
            'audit_score': 0.5,  # Security audits
            'community_score': 0.6  # Community adoption
        }

        overall_score = sum(risk_factors.values()) / len(risk_factors)

        if overall_score > 0.8:
            risk_level = AssetRiskLevel.VERY_LOW
        elif overall_score > 0.6:
            risk_level = AssetRiskLevel.LOW
        elif overall_score > 0.4:
            risk_level = AssetRiskLevel.MEDIUM
        elif overall_score > 0.2:
            risk_level = AssetRiskLevel.HIGH
        else:
            risk_level = AssetRiskLevel.VERY_HIGH

        return {
            'risk_level': risk_level,
            'is_verified': overall_score > 0.7,
            'audit_score': risk_factors['audit_score']
        }

    async def _calculate_volatility(self, asset_id: int, days: int) -> Decimal:
        """Calculate price volatility over specified period"""
        # Mock implementation - would fetch historical prices and calculate standard deviation
        if days == 1:
            return Decimal('0.08')  # 8% daily volatility
        elif days == 7:
            return Decimal('0.15')  # 15% weekly volatility
        else:
            return Decimal('0.25')  # 25% monthly volatility

    async def _get_current_prices(self, asset_id: int) -> Dict[str, Decimal]:
        """Get current ALGO and USD prices for asset"""
        price_data = await self._get_price_data(asset_id)
        return {
            'price_algo': price_data['price_algo'],
            'price_usd': price_data['price_usd']
        }

    def _calculate_position_risk(self, metrics: TokenMetrics, position_value_usd: Decimal) -> float:
        """Calculate risk score for a specific position"""
        # Base risk from asset risk level
        risk_level_scores = {
            AssetRiskLevel.VERY_LOW: 0.1,
            AssetRiskLevel.LOW: 0.3,
            AssetRiskLevel.MEDIUM: 0.5,
            AssetRiskLevel.HIGH: 0.7,
            AssetRiskLevel.VERY_HIGH: 0.9,
            AssetRiskLevel.UNKNOWN: 0.8
        }

        base_risk = risk_level_scores.get(metrics.risk_level, 0.8)

        # Adjust for position size (larger positions = higher risk)
        if position_value_usd > Decimal('100000'):  # >$100k
            size_adjustment = 0.2
        elif position_value_usd > Decimal('10000'):  # >$10k
            size_adjustment = 0.1
        else:
            size_adjustment = 0.0

        # Adjust for liquidity (illiquid = higher risk)
        liquidity_adjustment = (1 - metrics.liquidity_score) * 0.3

        return min(1.0, base_risk + size_adjustment + liquidity_adjustment)

    def _calculate_valuation_confidence(self, metrics: TokenMetrics) -> float:
        """Calculate confidence level in valuation"""
        confidence = 1.0

        # Reduce confidence for low liquidity
        if metrics.liquidity_score < 0.3:
            confidence -= 0.3

        # Reduce confidence for high volatility
        if metrics.volatility_24h > Decimal('0.2'):  # >20% daily volatility
            confidence -= 0.2

        # Reduce confidence for unverified assets
        if not metrics.is_verified:
            confidence -= 0.1

        return max(0.1, confidence)  # Minimum 10% confidence

    async def _calculate_portfolio_metrics(
        self,
        portfolio: Dict[str, Any],
        valuations: List[Dict[str, Any]]
    ):
        """Calculate portfolio-level risk and diversification metrics"""
        total_value = portfolio['total_value_usd']

        # Risk distribution
        for position in valuations:
            risk_level = position['metrics'].risk_level.value
            position_pct = position['valuation'].value_usd / total_value
            portfolio['risk_distribution'][risk_level] += position_pct

        # Quality metrics
        verified_value = sum(
            pos['valuation'].value_usd for pos in valuations
            if pos['metrics'].is_verified
        )
        liquid_value = sum(
            pos['valuation'].value_usd for pos in valuations
            if pos['metrics'].is_liquid
        )
        stable_value = sum(
            pos['valuation'].value_usd for pos in valuations
            if pos['metrics'].is_stable
        )

        portfolio['quality_metrics']['verified_percentage'] = float(verified_value / total_value)
        portfolio['quality_metrics']['liquid_percentage'] = float(liquid_value / total_value)
        portfolio['quality_metrics']['stable_percentage'] = float(stable_value / total_value)

        # Concentration analysis
        position_percentages = [
            float(pos['valuation'].value_usd / total_value) for pos in valuations
        ]
        position_percentages.sort(reverse=True)

        if position_percentages:
            portfolio['concentration_risk']['largest_position_pct'] = position_percentages[0]
            portfolio['concentration_risk']['top_3_concentration'] = sum(position_percentages[:3])
            portfolio['concentration_risk']['top_5_concentration'] = sum(position_percentages[:5])

            # Herfindahl Index (concentration measure)
            hhi = sum(pct ** 2 for pct in position_percentages)
            portfolio['concentration_risk']['herfindahl_index'] = hhi

        # Overall risk score (weighted average)
        risk_scores = [pos['valuation'].position_risk_score for pos in valuations]
        weights = [float(pos['valuation'].value_usd / total_value) for pos in valuations]
        portfolio['overall_risk_score'] = sum(score * weight for score, weight in zip(risk_scores, weights))

        # Diversification score (inverse of concentration)
        portfolio['diversification_score'] = max(0.0, 1.0 - portfolio['concentration_risk']['herfindahl_index'])