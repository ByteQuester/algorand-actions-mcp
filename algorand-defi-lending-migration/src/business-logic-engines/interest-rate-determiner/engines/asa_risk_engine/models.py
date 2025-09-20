"""
Data models for ASA risk analysis
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(Enum):
    """Risk levels for ASAs"""
    VERY_LOW = "very_low"      # Blue chip ASAs
    LOW = "low"                # Established ASAs
    MEDIUM = "medium"          # Growing ASAs
    HIGH = "high"              # Volatile ASAs
    VERY_HIGH = "very_high"    # Highly speculative ASAs

@dataclass
class VolatilityData:
    """Volatility metrics for an ASA"""
    asset_id: int
    daily_volatility: Decimal
    weekly_volatility: Decimal
    monthly_volatility: Decimal
    annual_volatility: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    timestamp: datetime

    def volatility_score(self) -> Decimal:
        """Calculate volatility score (0-1, higher = more volatile)"""
        # Normalize annual volatility to 0-1 scale
        # Assume 200% annual volatility = score of 1
        return min(self.annual_volatility / Decimal('2.0'), Decimal('1.0'))

@dataclass
class ASAProfile:
    """Complete profile for an ASA"""
    asset_id: int
    name: str
    unit_name: str
    total_supply: Decimal
    decimals: int
    creator: str
    manager: Optional[str]
    reserve: Optional[str]
    freeze: Optional[str]
    clawback: Optional[str]
    url: Optional[str]
    metadata_hash: Optional[str]
    is_frozen: bool
    creation_round: int
    timestamp: datetime

    def governance_score(self) -> Decimal:
        """Calculate governance score based on address configuration"""
        score = Decimal('0')

        # No manager = immutable (good)
        if not self.manager:
            score += Decimal('0.3')

        # No freeze = cannot be frozen (good)
        if not self.freeze:
            score += Decimal('0.3')

        # No clawback = cannot be clawed back (good)
        if not self.clawback:
            score += Decimal('0.3')

        # Has metadata (good)
        if self.url or self.metadata_hash:
            score += Decimal('0.1')

        return score

@dataclass
class LiquidityMetrics:
    """Liquidity metrics for an ASA"""
    asset_id: int
    trading_volume_24h: Decimal
    trading_volume_7d: Decimal
    market_cap: Decimal
    circulating_supply: Decimal
    number_of_holders: int
    number_of_dexes: int
    largest_pool_tvl: Decimal
    bid_ask_spread: Decimal
    timestamp: datetime

    def liquidity_score(self) -> Decimal:
        """Calculate liquidity score (0-1, higher = more liquid)"""
        scores = []

        # Volume relative to market cap
        if self.market_cap > 0:
            volume_ratio = self.trading_volume_24h / self.market_cap
            volume_score = min(volume_ratio * Decimal('10'), Decimal('1'))  # 10% daily volume = full score
            scores.append(volume_score * Decimal('0.4'))

        # Number of holders
        holder_score = min(Decimal(self.number_of_holders) / Decimal('1000'), Decimal('1'))
        scores.append(holder_score * Decimal('0.3'))

        # DEX availability
        dex_score = min(Decimal(self.number_of_dexes) / Decimal('3'), Decimal('1'))
        scores.append(dex_score * Decimal('0.2'))

        # Bid-ask spread (lower is better)
        spread_score = max(Decimal('1') - self.bid_ask_spread, Decimal('0'))
        scores.append(spread_score * Decimal('0.1'))

        return sum(scores) if scores else Decimal('0')

@dataclass
class ASARiskMetrics:
    """Complete risk assessment for an ASA"""
    asset_id: int
    name: str
    risk_level: RiskLevel
    overall_risk_score: Decimal  # 0-1, higher = riskier
    volatility_score: Decimal
    liquidity_score: Decimal
    governance_score: Decimal
    adoption_score: Decimal
    technical_score: Decimal
    collateral_factor: Decimal  # Recommended LTV ratio
    interest_rate_premium: Decimal  # Additional premium for this asset
    confidence_level: Decimal
    risk_factors: List[str]
    strengths: List[str]
    timestamp: datetime

    def recommended_ltv(self) -> Decimal:
        """Calculate recommended loan-to-value ratio"""
        base_ltv = Decimal('0.8')  # 80% for safest assets

        # Reduce LTV based on risk factors
        volatility_penalty = self.volatility_score * Decimal('0.3')
        liquidity_penalty = (Decimal('1') - self.liquidity_score) * Decimal('0.2')
        governance_penalty = (Decimal('1') - self.governance_score) * Decimal('0.1')

        total_penalty = volatility_penalty + liquidity_penalty + governance_penalty
        return max(base_ltv - total_penalty, Decimal('0.3'))  # Minimum 30% LTV

    def rate_adjustment(self) -> Decimal:
        """Calculate interest rate adjustment for this ASA"""
        if self.risk_level == RiskLevel.VERY_LOW:
            return Decimal('0')  # No premium
        elif self.risk_level == RiskLevel.LOW:
            return Decimal('0.005')  # 0.5% premium
        elif self.risk_level == RiskLevel.MEDIUM:
            return Decimal('0.01')  # 1% premium
        elif self.risk_level == RiskLevel.HIGH:
            return Decimal('0.02')  # 2% premium
        else:  # VERY_HIGH
            return Decimal('0.04')  # 4% premium

@dataclass
class MarketData:
    """Market data for ASA analysis"""
    asset_id: int
    current_price: Decimal
    price_24h_ago: Decimal
    price_7d_ago: Decimal
    price_30d_ago: Decimal
    all_time_high: Decimal
    all_time_low: Decimal
    market_cap: Decimal
    trading_volume_24h: Decimal
    timestamp: datetime

    def price_change_24h(self) -> Decimal:
        """Calculate 24h price change percentage"""
        if self.price_24h_ago > 0:
            return (self.current_price - self.price_24h_ago) / self.price_24h_ago
        return Decimal('0')

    def distance_from_ath(self) -> Decimal:
        """Calculate distance from all-time high"""
        if self.all_time_high > 0:
            return (self.all_time_high - self.current_price) / self.all_time_high
        return Decimal('0')