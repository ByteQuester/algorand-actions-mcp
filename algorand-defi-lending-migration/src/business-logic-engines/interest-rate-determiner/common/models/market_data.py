"""
Market data models for interest rate calculation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum


class MarketDataSource(Enum):
    """Sources of market data"""
    FEDERAL_RESERVE = "FEDERAL_RESERVE"
    ALGORAND_DEX = "ALGORAND_DEX"
    TINYMAN = "TINYMAN"
    PACT = "PACT"
    ALGOFI = "ALGOFI"
    FOLKS_FINANCE = "FOLKS_FINANCE"
    EXTERNAL_API = "EXTERNAL_API"
    MANUAL = "MANUAL"


class RateType(Enum):
    """Types of interest rates"""
    FEDERAL_FUNDS_RATE = "FEDERAL_FUNDS_RATE"
    TREASURY_RATE = "TREASURY_RATE"
    PRIME_RATE = "PRIME_RATE"
    LIBOR = "LIBOR"
    SOFR = "SOFR"
    DEFI_LENDING_RATE = "DEFI_LENDING_RATE"
    DEFI_BORROWING_RATE = "DEFI_BORROWING_RATE"
    LP_YIELD_RATE = "LP_YIELD_RATE"
    STAKING_RATE = "STAKING_RATE"


@dataclass
class RateDataPoint:
    """Individual rate data point"""
    rate_type: RateType
    value: Decimal
    timestamp: datetime
    source: MarketDataSource
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FederalRates:
    """Federal Reserve and traditional banking rates"""
    federal_funds_rate: Decimal
    treasury_1y: Decimal
    treasury_5y: Decimal
    treasury_10y: Decimal
    prime_rate: Decimal
    sofr: Decimal

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: MarketDataSource = MarketDataSource.FEDERAL_RESERVE
    data_quality: float = 1.0


@dataclass
class DeFiProtocolRates:
    """Rates from a specific DeFi protocol"""
    protocol_name: str
    lending_rates: Dict[str, Decimal] = field(default_factory=dict)  # Asset symbol -> rate
    borrowing_rates: Dict[str, Decimal] = field(default_factory=dict)  # Asset symbol -> rate
    lp_yields: Dict[str, Decimal] = field(default_factory=dict)  # Pool -> yield
    total_value_locked: Decimal = Decimal('0')

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: MarketDataSource = MarketDataSource.ALGORAND_DEX
    data_quality: float = 1.0


@dataclass
class DeFiRates:
    """Comprehensive DeFi rates across Algorand ecosystem"""

    # Protocol-specific rates
    algofi_rates: Optional[DeFiProtocolRates] = None
    folks_finance_rates: Optional[DeFiProtocolRates] = None
    tinyman_yields: Dict[str, Decimal] = field(default_factory=dict)  # Pool -> yield
    pact_yields: Dict[str, Decimal] = field(default_factory=dict)  # Pool -> yield

    # Aggregated rates
    average_lending_rate_algo: Decimal = Decimal('0')
    average_lending_rate_usdc: Decimal = Decimal('0')
    average_borrowing_rate_algo: Decimal = Decimal('0')
    average_borrowing_rate_usdc: Decimal = Decimal('0')

    # Market dynamics
    lending_utilization_rates: Dict[str, float] = field(default_factory=dict)
    liquidity_depth: Dict[str, Decimal] = field(default_factory=dict)
    yield_volatility: Dict[str, float] = field(default_factory=dict)

    # Staking and governance
    algorand_staking_rate: Decimal = Decimal('0')
    governance_participation_rate: float = 0.0

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_sources: List[MarketDataSource] = field(default_factory=list)
    overall_data_quality: float = 1.0


@dataclass
class AlgorandMarketData:
    """Algorand-specific market data"""

    # Algorand price and volume
    algo_price_usd: Decimal
    algo_24h_volume: Decimal
    algo_market_cap: Decimal
    algo_price_volatility: float

    # Network metrics
    total_accounts: int
    active_accounts_24h: int
    transactions_per_second: float
    network_utilization: float

    # ASA metrics
    total_asa_count: int
    active_asa_24h: int
    top_asa_by_volume: Dict[int, Decimal] = field(default_factory=dict)  # ASA ID -> volume

    # DeFi ecosystem
    total_defi_tvl: Decimal
    defi_protocol_count: int
    defi_growth_rate: float

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: MarketDataSource = MarketDataSource.ALGORAND_DEX
    data_quality: float = 1.0


@dataclass
class MarketData:
    """Comprehensive market data for interest rate calculation"""

    # Traditional financial markets
    federal_rates: FederalRates

    # DeFi and Algorand markets
    defi_rates: DeFiRates
    algorand_market: AlgorandMarketData

    # Cross-market analytics
    rate_correlations: Dict[str, float] = field(default_factory=dict)
    market_sentiment: float = 0.5  # 0 = bearish, 1 = bullish
    volatility_index: float = 0.0
    liquidity_score: float = 1.0

    # Risk indicators
    credit_spread: Decimal = Decimal('0')
    term_structure_slope: float = 0.0
    default_risk_premium: Decimal = Decimal('0')

    # Metadata
    snapshot_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_sources: List[MarketDataSource] = field(default_factory=list)
    overall_confidence: float = 1.0
    refresh_needed: bool = False

    def get_benchmark_rate(self, duration_days: int) -> Decimal:
        """Get appropriate benchmark rate based on loan duration"""
        if duration_days <= 365:  # 1 year or less
            return self.federal_rates.treasury_1y
        elif duration_days <= 365 * 5:  # 5 years or less
            return self.federal_rates.treasury_5y
        else:
            return self.federal_rates.treasury_10y

    def get_defi_benchmark(self, asset: str = "ALGO") -> Decimal:
        """Get DeFi lending benchmark for specific asset"""
        if asset.upper() == "ALGO":
            return self.defi_rates.average_lending_rate_algo
        elif asset.upper() in ["USDC", "USD"]:
            return self.defi_rates.average_lending_rate_usdc
        else:
            # Default to ALGO rate
            return self.defi_rates.average_lending_rate_algo

    def get_risk_free_rate(self) -> Decimal:
        """Get risk-free rate (typically federal funds rate)"""
        return self.federal_rates.federal_funds_rate

    def calculate_defi_premium(self) -> Decimal:
        """Calculate premium of DeFi rates over traditional rates"""
        defi_rate = self.defi_rates.average_lending_rate_algo
        traditional_rate = self.federal_rates.prime_rate
        return max(defi_rate - traditional_rate, Decimal('0'))

    def is_data_fresh(self, max_age_minutes: int = 60) -> bool:
        """Check if market data is fresh enough for calculations"""
        now = datetime.now(timezone.utc)
        age = (now - self.snapshot_timestamp).total_seconds() / 60
        return age <= max_age_minutes

    def get_market_stress_indicator(self) -> float:
        """Calculate overall market stress indicator (0 = calm, 1 = stressed)"""
        # Combine volatility, sentiment, and spread indicators
        volatility_stress = min(self.volatility_index / 50.0, 1.0)  # Normalize to 0-1
        sentiment_stress = 1.0 - self.market_sentiment  # Invert sentiment
        spread_stress = min(float(self.credit_spread) / 0.05, 1.0)  # Normalize to 5% max

        return (volatility_stress + sentiment_stress + spread_stress) / 3.0