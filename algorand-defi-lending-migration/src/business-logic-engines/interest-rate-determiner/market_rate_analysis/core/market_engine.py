"""
Market Rate Analysis Engine

Analyzes market conditions and determines base interest rates for lending operations.
Integrates with multiple data sources including DeFi protocols, traditional finance,
and Algorand-specific market conditions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data point for analysis"""
    timestamp: datetime
    source: str
    rate_type: str  # 'lending', 'borrowing', 'treasury', 'defi'
    rate_value: Decimal
    volume: Optional[Decimal] = None
    asset_pair: Optional[str] = None
    protocol: Optional[str] = None
    confidence: float = 1.0


@dataclass
class MarketAnalysis:
    """Result of market rate analysis"""
    base_rate: Decimal
    market_sentiment: str  # 'bullish', 'bearish', 'neutral'
    volatility_score: float
    liquidity_score: float
    recommendation: str
    risk_factors: List[str]
    supporting_data: Dict[str, Any]
    confidence: float
    analysis_timestamp: datetime


class MarketRateAnalysisEngine:
    """
    Engine for analyzing market conditions and determining appropriate base rates
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_sources = self.config.get('data_sources', [
            'algorand_dex',
            'traditional_rates',
            'defi_protocols',
            'treasury_rates'
        ])
        self.rate_cache = {}
        self.cache_ttl = self.config.get('cache_ttl_seconds', 300)  # 5 minutes

    async def analyze_market_rates(self, asset: str = 'ALGO', analysis_period_hours: int = 24) -> MarketAnalysis:
        """
        Analyze current market conditions and determine appropriate base rate

        Args:
            asset: The asset to analyze (default: ALGO)
            analysis_period_hours: Period for analysis in hours

        Returns:
            MarketAnalysis with rate recommendation
        """
        try:
            logger.info(f"Starting market rate analysis for {asset}")

            # Gather market data from multiple sources
            market_data = await self._gather_market_data(asset, analysis_period_hours)

            # Analyze traditional finance rates
            traditional_rates = await self._analyze_traditional_rates()

            # Analyze DeFi protocol rates
            defi_rates = await self._analyze_defi_rates(asset)

            # Analyze Algorand-specific conditions
            algorand_conditions = await self._analyze_algorand_conditions(asset)

            # Calculate base rate recommendation
            base_rate = self._calculate_base_rate(
                market_data, traditional_rates, defi_rates, algorand_conditions
            )

            # Assess market sentiment and conditions
            sentiment = self._assess_market_sentiment(market_data)
            volatility = self._calculate_volatility_score(market_data)
            liquidity = self._assess_liquidity_score(market_data)

            # Generate recommendations and risk factors
            recommendation = self._generate_recommendation(base_rate, sentiment, volatility, liquidity)
            risk_factors = self._identify_risk_factors(market_data, sentiment, volatility)

            # Calculate confidence score
            confidence = self._calculate_confidence_score(market_data, sentiment)

            # Compile supporting data
            supporting_data = {
                'market_data_points': len(market_data),
                'traditional_rates': traditional_rates,
                'defi_rates': defi_rates,
                'algorand_conditions': algorand_conditions,
                'analysis_period_hours': analysis_period_hours
            }

            analysis = MarketAnalysis(
                base_rate=base_rate,
                market_sentiment=sentiment,
                volatility_score=volatility,
                liquidity_score=liquidity,
                recommendation=recommendation,
                risk_factors=risk_factors,
                supporting_data=supporting_data,
                confidence=confidence,
                analysis_timestamp=datetime.now()
            )

            logger.info(f"Market analysis completed. Base rate: {base_rate:.4%}")
            return analysis

        except Exception as e:
            logger.error(f"Error in market rate analysis: {e}")
            raise

    async def _gather_market_data(self, asset: str, hours: int) -> List[MarketData]:
        """Gather market data from configured sources"""
        market_data = []

        # Simulated data gathering (in production, this would call real APIs)
        for source in self.data_sources:
            try:
                data_points = await self._fetch_from_source(source, asset, hours)
                market_data.extend(data_points)
            except Exception as e:
                logger.warning(f"Failed to fetch data from {source}: {e}")

        return market_data

    async def _fetch_from_source(self, source: str, asset: str, hours: int) -> List[MarketData]:
        """Fetch data from a specific source"""
        # Simulated data for demonstration
        now = datetime.now()
        data_points = []

        if source == 'algorand_dex':
            # Simulate Algorand DEX rates
            for i in range(min(hours, 24)):
                timestamp = now - timedelta(hours=i)
                rate = Decimal('0.045') + Decimal(str(i * 0.001))  # Simulated rate
                data_points.append(MarketData(
                    timestamp=timestamp,
                    source=source,
                    rate_type='lending',
                    rate_value=rate,
                    volume=Decimal('1000000'),
                    asset_pair=f'{asset}/USDC',
                    protocol='Algorand DEX',
                    confidence=0.9
                ))

        elif source == 'traditional_rates':
            # Simulate traditional finance rates
            data_points.append(MarketData(
                timestamp=now,
                source=source,
                rate_type='treasury',
                rate_value=Decimal('0.05'),  # 5% treasury rate
                confidence=0.95
            ))

        elif source == 'defi_protocols':
            # Simulate other DeFi protocol rates
            protocols = ['Aave', 'Compound', 'MakerDAO']
            for protocol in protocols:
                rate = Decimal('0.06') + Decimal(str(len(protocol) * 0.002))
                data_points.append(MarketData(
                    timestamp=now,
                    source=source,
                    rate_type='lending',
                    rate_value=rate,
                    protocol=protocol,
                    confidence=0.85
                ))

        return data_points

    async def _analyze_traditional_rates(self) -> Dict[str, Decimal]:
        """Analyze traditional finance rates"""
        return {
            'federal_funds_rate': Decimal('0.05'),
            'treasury_10y': Decimal('0.045'),
            'corporate_bond_rate': Decimal('0.065'),
            'bank_prime_rate': Decimal('0.08')
        }

    async def _analyze_defi_rates(self, asset: str) -> Dict[str, Decimal]:
        """Analyze DeFi protocol rates"""
        return {
            'average_lending_rate': Decimal('0.06'),
            'average_borrowing_rate': Decimal('0.08'),
            'volatility_premium': Decimal('0.02'),
            'liquidity_premium': Decimal('0.01')
        }

    async def _analyze_algorand_conditions(self, asset: str) -> Dict[str, Any]:
        """Analyze Algorand-specific market conditions"""
        return {
            'network_utilization': 0.75,
            'governance_participation': 0.68,
            'total_value_locked': Decimal('500000000'),
            'validator_rewards': Decimal('0.05'),
            'network_security_score': 0.92
        }

    def _calculate_base_rate(self, market_data: List[MarketData],
                           traditional_rates: Dict[str, Decimal],
                           defi_rates: Dict[str, Decimal],
                           algorand_conditions: Dict[str, Any]) -> Decimal:
        """Calculate the recommended base rate"""

        # Weight different rate sources
        weights = {
            'traditional': Decimal('0.3'),
            'defi': Decimal('0.4'),
            'algorand': Decimal('0.3')
        }

        # Traditional finance baseline
        traditional_base = traditional_rates.get('treasury_10y', Decimal('0.05'))

        # DeFi market rate
        defi_base = defi_rates.get('average_lending_rate', Decimal('0.06'))

        # Algorand-specific adjustments
        algo_adjustment = Decimal('0.01')  # Premium for Algorand ecosystem

        # Calculate weighted average
        base_rate = (
            traditional_base * weights['traditional'] +
            defi_base * weights['defi'] +
            (traditional_base + algo_adjustment) * weights['algorand']
        )

        # Apply market data influence
        if market_data:
            recent_rates = [d.rate_value for d in market_data[-10:]]  # Last 10 data points
            if recent_rates:
                market_avg = sum(recent_rates) / len(recent_rates)
                base_rate = (base_rate + market_avg) / Decimal('2')

        return base_rate.quantize(Decimal('0.0001'))

    def _assess_market_sentiment(self, market_data: List[MarketData]) -> str:
        """Assess overall market sentiment"""
        if not market_data:
            return 'neutral'

        # Analyze rate trends
        recent_data = sorted(market_data, key=lambda x: x.timestamp)[-24:]  # Last 24 hours
        if len(recent_data) < 2:
            return 'neutral'

        rates = [d.rate_value for d in recent_data]
        trend = (rates[-1] - rates[0]) / rates[0] if rates[0] > 0 else 0

        if trend > 0.02:  # 2% increase
            return 'bullish'
        elif trend < -0.02:  # 2% decrease
            return 'bearish'
        else:
            return 'neutral'

    def _calculate_volatility_score(self, market_data: List[MarketData]) -> float:
        """Calculate volatility score (0-1, higher = more volatile)"""
        if len(market_data) < 2:
            return 0.5  # Default moderate volatility

        rates = [float(d.rate_value) for d in market_data]
        mean_rate = sum(rates) / len(rates)
        variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        volatility = (variance ** 0.5) / mean_rate if mean_rate > 0 else 0

        # Normalize to 0-1 scale
        return min(volatility * 10, 1.0)

    def _assess_liquidity_score(self, market_data: List[MarketData]) -> float:
        """Assess market liquidity score (0-1, higher = more liquid)"""
        volume_data = [d for d in market_data if d.volume is not None]

        if not volume_data:
            return 0.5  # Default moderate liquidity

        total_volume = sum(float(d.volume) for d in volume_data)
        data_points = len(volume_data)

        # Simple liquidity score based on volume and data availability
        avg_volume = total_volume / data_points if data_points > 0 else 0
        liquidity_score = min(avg_volume / 10000000, 1.0)  # Normalize against 10M baseline

        return liquidity_score

    def _generate_recommendation(self, base_rate: Decimal, sentiment: str,
                               volatility: float, liquidity: float) -> str:
        """Generate rate recommendation based on analysis"""
        recommendations = []

        if sentiment == 'bullish':
            recommendations.append("Consider slightly higher rates due to bullish sentiment")
        elif sentiment == 'bearish':
            recommendations.append("Consider lower rates to attract borrowers in bearish market")

        if volatility > 0.7:
            recommendations.append("Add volatility premium due to high market volatility")
        elif volatility < 0.3:
            recommendations.append("Stable market conditions allow for competitive rates")

        if liquidity < 0.4:
            recommendations.append("Add liquidity premium due to limited market liquidity")
        elif liquidity > 0.8:
            recommendations.append("High liquidity supports lower rate premiums")

        return "; ".join(recommendations) if recommendations else "Standard rate recommended"

    def _identify_risk_factors(self, market_data: List[MarketData],
                             sentiment: str, volatility: float) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []

        if volatility > 0.8:
            risk_factors.append("High market volatility")

        if sentiment == 'bearish':
            risk_factors.append("Bearish market sentiment")

        if len(market_data) < 10:
            risk_factors.append("Limited market data availability")

        # Check for data source diversity
        sources = set(d.source for d in market_data)
        if len(sources) < 2:
            risk_factors.append("Limited data source diversity")

        return risk_factors

    def _calculate_confidence_score(self, market_data: List[MarketData], sentiment: str) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence

        # More data points increase confidence
        data_factor = min(len(market_data) / 50, 0.3)
        confidence += data_factor

        # Data source diversity increases confidence
        sources = set(d.source for d in market_data)
        source_factor = min(len(sources) / 4, 0.2)
        confidence += source_factor

        # Recent data increases confidence
        recent_data = [d for d in market_data if (datetime.now() - d.timestamp).hours < 6]
        recency_factor = min(len(recent_data) / 20, 0.1)
        confidence += recency_factor

        # Clear sentiment increases confidence
        if sentiment != 'neutral':
            confidence += 0.05

        return min(confidence, 1.0)

    def get_cached_analysis(self, asset: str) -> Optional[MarketAnalysis]:
        """Get cached analysis if available and not expired"""
        cache_key = f"market_analysis_{asset}"
        if cache_key in self.rate_cache:
            cached_data, timestamp = self.rate_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return cached_data
        return None

    def cache_analysis(self, asset: str, analysis: MarketAnalysis):
        """Cache analysis result"""
        cache_key = f"market_analysis_{asset}"
        self.rate_cache[cache_key] = (analysis, datetime.now())