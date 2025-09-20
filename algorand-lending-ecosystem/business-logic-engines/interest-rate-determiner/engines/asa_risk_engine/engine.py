"""
ASA Risk Engine

Analyzes ASA volatility, liquidity, and governance to determine
risk-adjusted interest rates for collateralized lending.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from algosdk.v2client import algod, indexer

from .models import (
    ASARiskMetrics,
    VolatilityData,
    ASAProfile,
    LiquidityMetrics,
    MarketData,
    RiskLevel
)

logger = logging.getLogger(__name__)

class ASARiskEngine:
    """
    Engine for analyzing ASA risk and determining appropriate
    interest rate adjustments and collateral factors.
    """

    def __init__(
        self,
        algod_client: algod.AlgodClient,
        indexer_client: indexer.IndexerClient,
        price_apis: Dict[str, str],
        cache_ttl: int = 300  # 5 minutes
    ):
        self.algod_client = algod_client
        self.indexer_client = indexer_client
        self.price_apis = price_apis
        self.cache_ttl = cache_ttl
        self._cache: Dict = {}
        self._cache_timestamps: Dict = {}

    async def analyze_asa_risk(
        self,
        asset_id: int,
        analysis_period_days: int = 90
    ) -> ASARiskMetrics:
        """
        Perform comprehensive risk analysis for an ASA
        """
        try:
            # Get ASA profile
            profile = await self._get_asa_profile(asset_id)

            # Get volatility data
            volatility = await self._calculate_volatility(asset_id, analysis_period_days)

            # Get liquidity metrics
            liquidity = await self._analyze_liquidity(asset_id)

            # Get market data
            market_data = await self._get_market_data(asset_id)

            # Calculate component scores
            volatility_score = volatility.volatility_score()
            liquidity_score = liquidity.liquidity_score()
            governance_score = profile.governance_score()
            adoption_score = await self._calculate_adoption_score(asset_id, liquidity)
            technical_score = await self._calculate_technical_score(profile, market_data)

            # Calculate overall risk score
            weights = {
                'volatility': Decimal('0.3'),
                'liquidity': Decimal('0.25'),
                'governance': Decimal('0.2'),
                'adoption': Decimal('0.15'),
                'technical': Decimal('0.1')
            }

            # Risk score (higher = riskier)
            overall_risk = (
                volatility_score * weights['volatility'] +
                (Decimal('1') - liquidity_score) * weights['liquidity'] +
                (Decimal('1') - governance_score) * weights['governance'] +
                (Decimal('1') - adoption_score) * weights['adoption'] +
                (Decimal('1') - technical_score) * weights['technical']
            )

            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk)

            # Calculate collateral factor
            collateral_factor = self._calculate_collateral_factor(overall_risk, volatility_score)

            # Calculate rate premium
            rate_premium = self._calculate_rate_premium(risk_level, overall_risk)

            # Identify risk factors and strengths
            risk_factors = await self._identify_risk_factors(profile, volatility, liquidity, market_data)
            strengths = await self._identify_strengths(profile, volatility, liquidity, market_data)

            # Calculate confidence
            confidence = await self._calculate_confidence(profile, liquidity, market_data)

            return ASARiskMetrics(
                asset_id=asset_id,
                name=profile.name,
                risk_level=risk_level,
                overall_risk_score=overall_risk,
                volatility_score=volatility_score,
                liquidity_score=liquidity_score,
                governance_score=governance_score,
                adoption_score=adoption_score,
                technical_score=technical_score,
                collateral_factor=collateral_factor,
                interest_rate_premium=rate_premium,
                confidence_level=confidence,
                risk_factors=risk_factors,
                strengths=strengths,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error analyzing ASA risk for {asset_id}: {e}")
            raise

    async def _get_asa_profile(self, asset_id: int) -> ASAProfile:
        """Get ASA profile information"""
        cache_key = f"asa_profile_{asset_id}"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            asset_info = self.algod_client.asset_info(asset_id)
            params = asset_info.get('params', {})

            profile = ASAProfile(
                asset_id=asset_id,
                name=params.get('name', f'ASA-{asset_id}'),
                unit_name=params.get('unit-name', ''),
                total_supply=Decimal(str(params.get('total', 0))),
                decimals=params.get('decimals', 0),
                creator=params.get('creator', ''),
                manager=params.get('manager'),
                reserve=params.get('reserve'),
                freeze=params.get('freeze'),
                clawback=params.get('clawback'),
                url=params.get('url'),
                metadata_hash=params.get('metadata-hash'),
                is_frozen=params.get('default-frozen', False),
                creation_round=asset_info.get('created-at-round', 0),
                timestamp=datetime.utcnow()
            )

            self._cache[cache_key] = profile
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return profile

        except Exception as e:
            logger.error(f"Error getting ASA profile for {asset_id}: {e}")
            raise

    async def _calculate_volatility(self, asset_id: int, days: int) -> VolatilityData:
        """Calculate volatility metrics for an ASA"""
        cache_key = f"volatility_{asset_id}_{days}"

        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            # Get price history (mock data for now)
            price_history = await self._get_price_history(asset_id, days)

            if len(price_history) < 7:
                # Not enough data, return default high volatility
                return VolatilityData(
                    asset_id=asset_id,
                    daily_volatility=Decimal('0.15'),
                    weekly_volatility=Decimal('0.35'),
                    monthly_volatility=Decimal('0.60'),
                    annual_volatility=Decimal('1.50'),
                    max_drawdown=Decimal('0.40'),
                    sharpe_ratio=Decimal('0.5'),
                    sortino_ratio=Decimal('0.6'),
                    timestamp=datetime.utcnow()
                )

            # Calculate returns
            prices = [p['price'] for p in price_history]
            returns = [
                (prices[i] - prices[i-1]) / prices[i-1]
                for i in range(1, len(prices))
            ]

            # Calculate volatilities
            daily_vol = Decimal(str(statistics.stdev(returns))) if len(returns) > 1 else Decimal('0.1')
            weekly_vol = daily_vol * Decimal('7').sqrt()
            monthly_vol = daily_vol * Decimal('30').sqrt()
            annual_vol = daily_vol * Decimal('365').sqrt()

            # Calculate max drawdown
            max_price = max(prices)
            min_price_after_max = min(prices[prices.index(max_price):])
            max_drawdown = (max_price - min_price_after_max) / max_price

            # Calculate Sharpe ratio (simplified)
            avg_return = sum(returns) / len(returns) if returns else 0
            sharpe = Decimal(str(avg_return)) / daily_vol if daily_vol > 0 else Decimal('0')

            # Sortino ratio (simplified - using downside deviation)
            negative_returns = [r for r in returns if r < 0]
            downside_vol = Decimal(str(statistics.stdev(negative_returns))) if len(negative_returns) > 1 else daily_vol
            sortino = Decimal(str(avg_return)) / downside_vol if downside_vol > 0 else Decimal('0')

            volatility_data = VolatilityData(
                asset_id=asset_id,
                daily_volatility=daily_vol,
                weekly_volatility=weekly_vol,
                monthly_volatility=monthly_vol,
                annual_volatility=annual_vol,
                max_drawdown=Decimal(str(max_drawdown)),
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                timestamp=datetime.utcnow()
            )

            self._cache[cache_key] = volatility_data
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return volatility_data

        except Exception as e:
            logger.error(f"Error calculating volatility for {asset_id}: {e}")
            # Return high volatility as default
            return VolatilityData(
                asset_id=asset_id,
                daily_volatility=Decimal('0.12'),
                weekly_volatility=Decimal('0.32'),
                monthly_volatility=Decimal('0.55'),
                annual_volatility=Decimal('1.2'),
                max_drawdown=Decimal('0.35'),
                sharpe_ratio=Decimal('0.3'),
                sortino_ratio=Decimal('0.4'),
                timestamp=datetime.utcnow()
            )

    async def _analyze_liquidity(self, asset_id: int) -> LiquidityMetrics:
        """Analyze liquidity metrics for an ASA"""
        try:
            # Get asset holder count
            holders = await self._count_asset_holders(asset_id)

            # Mock liquidity data (would integrate with DEX APIs)
            return LiquidityMetrics(
                asset_id=asset_id,
                trading_volume_24h=Decimal('100000'),
                trading_volume_7d=Decimal('600000'),
                market_cap=Decimal('5000000'),
                circulating_supply=Decimal('1000000'),
                number_of_holders=holders,
                number_of_dexes=2,
                largest_pool_tvl=Decimal('500000'),
                bid_ask_spread=Decimal('0.01'),
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error analyzing liquidity for {asset_id}: {e}")
            return LiquidityMetrics(
                asset_id=asset_id,
                trading_volume_24h=Decimal('10000'),
                trading_volume_7d=Decimal('60000'),
                market_cap=Decimal('500000'),
                circulating_supply=Decimal('100000'),
                number_of_holders=100,
                number_of_dexes=1,
                largest_pool_tvl=Decimal('50000'),
                bid_ask_spread=Decimal('0.05'),
                timestamp=datetime.utcnow()
            )

    async def _get_market_data(self, asset_id: int) -> MarketData:
        """Get current market data for an ASA"""
        # Mock market data
        return MarketData(
            asset_id=asset_id,
            current_price=Decimal('1.0'),
            price_24h_ago=Decimal('0.95'),
            price_7d_ago=Decimal('0.88'),
            price_30d_ago=Decimal('0.75'),
            all_time_high=Decimal('2.5'),
            all_time_low=Decimal('0.10'),
            market_cap=Decimal('1000000'),
            trading_volume_24h=Decimal('50000'),
            timestamp=datetime.utcnow()
        )

    def _determine_risk_level(self, risk_score: Decimal) -> RiskLevel:
        """Determine risk level based on overall risk score"""
        if risk_score <= Decimal('0.2'):
            return RiskLevel.VERY_LOW
        elif risk_score <= Decimal('0.4'):
            return RiskLevel.LOW
        elif risk_score <= Decimal('0.6'):
            return RiskLevel.MEDIUM
        elif risk_score <= Decimal('0.8'):
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    def _calculate_collateral_factor(self, risk_score: Decimal, volatility_score: Decimal) -> Decimal:
        """Calculate appropriate collateral factor"""
        base_factor = Decimal('0.8')  # 80% for lowest risk
        risk_penalty = risk_score * Decimal('0.4')  # Up to 40% penalty
        volatility_penalty = volatility_score * Decimal('0.2')  # Up to 20% penalty

        return max(base_factor - risk_penalty - volatility_penalty, Decimal('0.3'))

    def _calculate_rate_premium(self, risk_level: RiskLevel, risk_score: Decimal) -> Decimal:
        """Calculate interest rate premium based on risk"""
        base_premiums = {
            RiskLevel.VERY_LOW: Decimal('0'),
            RiskLevel.LOW: Decimal('0.005'),
            RiskLevel.MEDIUM: Decimal('0.015'),
            RiskLevel.HIGH: Decimal('0.03'),
            RiskLevel.VERY_HIGH: Decimal('0.05')
        }

        base_premium = base_premiums[risk_level]
        # Add additional premium based on exact risk score
        additional_premium = risk_score * Decimal('0.02')

        return base_premium + additional_premium

    # Simplified helper methods
    async def _get_price_history(self, asset_id: int, days: int) -> List[Dict]:
        """Get price history for an asset"""
        # Mock price data with some volatility
        import random
        prices = []
        base_price = 1.0

        for i in range(days):
            # Simulate price movement
            change = random.uniform(-0.1, 0.1)  # ±10% daily change
            base_price *= (1 + change)
            prices.append({
                'date': datetime.utcnow() - timedelta(days=days-i),
                'price': Decimal(str(max(base_price, 0.01)))
            })

        return prices

    async def _count_asset_holders(self, asset_id: int) -> int:
        """Count number of asset holders"""
        try:
            # This would query the indexer for asset balances
            # For now, return a mock count
            return 500
        except:
            return 100

    async def _calculate_adoption_score(self, asset_id: int, liquidity: LiquidityMetrics) -> Decimal:
        """Calculate adoption score based on usage metrics"""
        holder_score = min(Decimal(liquidity.number_of_holders) / Decimal('1000'), Decimal('1'))
        volume_score = min(liquidity.trading_volume_24h / Decimal('1000000'), Decimal('1'))
        dex_score = min(Decimal(liquidity.number_of_dexes) / Decimal('5'), Decimal('1'))

        return (holder_score + volume_score + dex_score) / Decimal('3')

    async def _calculate_technical_score(self, profile: ASAProfile, market: MarketData) -> Decimal:
        """Calculate technical score based on tokenomics"""
        scores = []

        # Supply distribution
        if profile.total_supply > 0:
            supply_score = Decimal('1') if profile.total_supply < Decimal('1000000000') else Decimal('0.7')
            scores.append(supply_score * Decimal('0.3'))

        # Price stability (distance from ATH)
        ath_distance = market.distance_from_ath()
        stability_score = Decimal('1') - min(ath_distance, Decimal('0.8'))
        scores.append(stability_score * Decimal('0.4'))

        # Age factor
        age_score = Decimal('1')  # Assume mature for now
        scores.append(age_score * Decimal('0.3'))

        return sum(scores) if scores else Decimal('0.5')

    async def _identify_risk_factors(self, profile, volatility, liquidity, market) -> List[str]:
        """Identify risk factors"""
        factors = []

        if volatility.annual_volatility > Decimal('1.0'):
            factors.append("High volatility (>100% annually)")

        if liquidity.number_of_holders < 100:
            factors.append("Low number of holders")

        if profile.manager:
            factors.append("Mutable asset (has manager)")

        if profile.freeze:
            factors.append("Can be frozen")

        if liquidity.trading_volume_24h < Decimal('10000'):
            factors.append("Low trading volume")

        return factors

    async def _identify_strengths(self, profile, volatility, liquidity, market) -> List[str]:
        """Identify strengths"""
        strengths = []

        if not profile.manager:
            strengths.append("Immutable asset")

        if not profile.freeze and not profile.clawback:
            strengths.append("No freeze/clawback capability")

        if liquidity.number_of_holders > 1000:
            strengths.append("Wide distribution")

        if volatility.sharpe_ratio > Decimal('1'):
            strengths.append("Good risk-adjusted returns")

        if liquidity.number_of_dexes >= 3:
            strengths.append("Multi-DEX availability")

        return strengths

    async def _calculate_confidence(self, profile, liquidity, market) -> Decimal:
        """Calculate confidence in the risk assessment"""
        factors = []

        # More holders = more confidence
        holder_confidence = min(Decimal(liquidity.number_of_holders) / Decimal('1000'), Decimal('1'))
        factors.append(holder_confidence * Decimal('0.4'))

        # More volume = more confidence
        volume_confidence = min(liquidity.trading_volume_24h / Decimal('100000'), Decimal('1'))
        factors.append(volume_confidence * Decimal('0.3'))

        # More DEXes = more confidence
        dex_confidence = min(Decimal(liquidity.number_of_dexes) / Decimal('3'), Decimal('1'))
        factors.append(dex_confidence * Decimal('0.3'))

        return sum(factors)

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self._cache:
            return False

        cache_time = self._cache_timestamps.get(key)
        if not cache_time:
            return False

        return (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl