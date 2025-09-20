"""
DeFi protocol-specific data models for Algorand ecosystem.

Models for liquidity pools, yield farming, protocol rates,
and cross-protocol yield aggregation.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum


class DeFiProtocolType(Enum):
    """Types of DeFi protocols on Algorand"""
    DEX = "dex"  # Decentralized Exchange
    LENDING = "lending"  # Lending/Borrowing
    YIELD_FARMING = "yield_farming"  # Yield farming
    LIQUIDITY_MINING = "liquidity_mining"  # Liquidity mining
    STAKING = "staking"  # Staking protocols
    DERIVATIVES = "derivatives"  # Derivatives
    INSURANCE = "insurance"  # Insurance protocols


class PoolType(Enum):
    """Types of liquidity pools"""
    CONSTANT_PRODUCT = "constant_product"  # x*y=k (Uniswap-style)
    STABLE_SWAP = "stable_swap"  # StableSwap (Curve-style)
    WEIGHTED = "weighted"  # Weighted pools (Balancer-style)
    CONCENTRATED = "concentrated"  # Concentrated liquidity
    SINGLE_ASSET = "single_asset"  # Single asset pools


@dataclass
class DeFiProtocol:
    """DeFi protocol information and metadata"""
    protocol_id: str
    name: str
    protocol_type: DeFiProtocolType
    app_id: int  # Main application ID

    # Protocol characteristics
    tvl_algo: Decimal = Decimal('0')
    tvl_usd: Decimal = Decimal('0')
    daily_volume_algo: Decimal = Decimal('0')
    daily_volume_usd: Decimal = Decimal('0')

    # Risk metrics
    security_score: float = 0.0  # 0-100 security assessment
    audit_status: str = "unaudited"  # "audited", "partially_audited", "unaudited"
    time_weighted_return: Optional[Decimal] = None

    # Protocol metadata
    website: Optional[str] = None
    documentation: Optional[str] = None
    github: Optional[str] = None
    launched_date: Optional[datetime] = None

    # Supported assets
    supported_assets: List[int] = field(default_factory=list)  # ASA IDs
    base_fee_rate: Decimal = Decimal('0.003')  # 0.3% default

    @property
    def is_established(self) -> bool:
        """Check if protocol is established (>6 months, >$1M TVL)"""
        if not self.launched_date:
            return False

        days_active = (datetime.now() - self.launched_date).days
        return days_active > 180 and self.tvl_usd > Decimal('1000000')


@dataclass
class LiquidityPool:
    """Liquidity pool information and metrics"""
    pool_id: str
    protocol: str  # Protocol name
    app_id: int  # Pool application ID
    pool_type: PoolType

    # Pool composition
    asset_a: int  # ASA ID of first asset
    asset_b: int  # ASA ID of second asset
    reserve_a: Decimal  # Reserve of asset A
    reserve_b: Decimal  # Reserve of asset B

    # Pool metrics
    total_liquidity_algo: Decimal = Decimal('0')
    total_liquidity_usd: Decimal = Decimal('0')
    lp_token_supply: Decimal = Decimal('0')

    # Trading metrics
    volume_24h_algo: Decimal = Decimal('0')
    volume_24h_usd: Decimal = Decimal('0')
    trades_24h: int = 0
    fee_revenue_24h: Decimal = Decimal('0')

    # Yield metrics
    base_apy: Decimal = Decimal('0')  # From trading fees
    reward_apy: Decimal = Decimal('0')  # From incentive programs
    total_apy: Decimal = Decimal('0')  # Combined APY

    # Risk metrics
    impermanent_loss_1d: Decimal = Decimal('0')
    price_impact_1pct: Decimal = Decimal('0')  # Price impact for 1% of liquidity

    # Pool state
    is_active: bool = True
    last_trade_timestamp: Optional[datetime] = None
    created_timestamp: Optional[datetime] = None

    @property
    def utilization_rate(self) -> float:
        """Calculate pool utilization rate"""
        if self.total_liquidity_usd == 0:
            return 0.0
        return float(self.volume_24h_usd / self.total_liquidity_usd)

    @property
    def price_ratio(self) -> Decimal:
        """Calculate current price ratio (asset_a / asset_b)"""
        if self.reserve_b == 0:
            return Decimal('0')
        return self.reserve_a / self.reserve_b


@dataclass
class DeFiYield:
    """DeFi yield opportunity information"""
    protocol: str
    strategy_name: str
    asset_id: int  # Primary asset for yield farming

    # Yield metrics
    current_apy: Decimal
    historical_apy_7d: Decimal = Decimal('0')
    historical_apy_30d: Decimal = Decimal('0')
    max_apy_observed: Decimal = Decimal('0')
    min_apy_observed: Decimal = Decimal('0')

    # Risk assessment
    strategy_risk_level: str = "medium"  # "low", "medium", "high", "very_high"
    smart_contract_risk: float = 0.5  # 0-1 risk score
    liquidity_risk: float = 0.5  # 0-1 risk score

    # Capital requirements
    min_deposit_amount: Decimal = Decimal('0')
    max_deposit_amount: Optional[Decimal] = None
    lock_period_days: int = 0  # 0 = no lock

    # Reward structure
    reward_tokens: List[int] = field(default_factory=list)  # Reward token ASA IDs
    compounding_frequency: str = "daily"  # "continuous", "daily", "weekly"
    auto_compound: bool = False

    # Performance tracking
    total_value_locked: Decimal = Decimal('0')
    participants_count: int = 0

    @property
    def risk_adjusted_yield(self) -> Decimal:
        """Calculate risk-adjusted yield"""
        risk_factor = 1 - ((self.smart_contract_risk + self.liquidity_risk) / 2)
        return self.current_apy * Decimal(str(risk_factor))


@dataclass
class ProtocolRates:
    """Current interest rates for a DeFi protocol"""
    protocol: str
    timestamp: datetime

    # Lending rates (what lenders earn)
    lending_rates: Dict[int, Decimal] = field(default_factory=dict)  # asset_id -> APY

    # Borrowing rates (what borrowers pay)
    borrowing_rates: Dict[int, Decimal] = field(default_factory=dict)  # asset_id -> APY

    # Utilization rates
    utilization_rates: Dict[int, Decimal] = field(default_factory=dict)  # asset_id -> utilization

    # Available liquidity
    available_liquidity: Dict[int, Decimal] = field(default_factory=dict)  # asset_id -> amount

    # Protocol-specific metrics
    governance_token_rewards: Optional[Decimal] = None
    protocol_revenue_share: Optional[Decimal] = None

    def get_lending_rate(self, asset_id: int) -> Decimal:
        """Get lending rate for specific asset"""
        return self.lending_rates.get(asset_id, Decimal('0'))

    def get_borrowing_rate(self, asset_id: int) -> Decimal:
        """Get borrowing rate for specific asset"""
        return self.borrowing_rates.get(asset_id, Decimal('0'))

    def get_spread(self, asset_id: int) -> Decimal:
        """Calculate spread between borrowing and lending rates"""
        return self.get_borrowing_rate(asset_id) - self.get_lending_rate(asset_id)


@dataclass
class YieldHistory:
    """Historical yield data for analysis"""
    protocol: str
    asset_id: int
    strategy: str

    # Time series data
    timestamps: List[datetime] = field(default_factory=list)
    apy_values: List[Decimal] = field(default_factory=list)
    tvl_values: List[Decimal] = field(default_factory=list)

    # Statistical metrics
    mean_apy: Decimal = Decimal('0')
    std_deviation: Decimal = Decimal('0')
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal = Decimal('0')

    # Volatility metrics
    daily_volatility: Decimal = Decimal('0')
    annualized_volatility: Decimal = Decimal('0')

    def add_data_point(self, timestamp: datetime, apy: Decimal, tvl: Decimal):
        """Add new data point to history"""
        self.timestamps.append(timestamp)
        self.apy_values.append(apy)
        self.tvl_values.append(tvl)

        # Recalculate statistics
        self._calculate_statistics()

    def _calculate_statistics(self):
        """Calculate statistical metrics from historical data"""
        if len(self.apy_values) < 2:
            return

        # Calculate mean
        self.mean_apy = sum(self.apy_values) / len(self.apy_values)

        # Calculate standard deviation
        variance = sum((x - self.mean_apy) ** 2 for x in self.apy_values) / len(self.apy_values)
        self.std_deviation = variance ** Decimal('0.5')

        # Calculate volatility (assuming daily data)
        if len(self.apy_values) > 1:
            returns = []
            for i in range(1, len(self.apy_values)):
                if self.apy_values[i-1] != 0:
                    daily_return = (self.apy_values[i] - self.apy_values[i-1]) / self.apy_values[i-1]
                    returns.append(daily_return)

            if returns:
                daily_vol = (sum(r**2 for r in returns) / len(returns)) ** Decimal('0.5')
                self.daily_volatility = daily_vol
                self.annualized_volatility = daily_vol * (Decimal('365') ** Decimal('0.5'))


@dataclass
class ProtocolComparison:
    """Comparison metrics across multiple DeFi protocols"""
    asset_id: int
    comparison_timestamp: datetime

    # Protocol data
    protocols: List[str] = field(default_factory=list)
    lending_rates: List[Decimal] = field(default_factory=list)
    borrowing_rates: List[Decimal] = field(default_factory=list)
    risk_scores: List[float] = field(default_factory=list)
    tvl_amounts: List[Decimal] = field(default_factory=list)

    @property
    def best_lending_rate(self) -> tuple[str, Decimal]:
        """Get protocol with highest lending rate"""
        if not self.lending_rates:
            return ("", Decimal('0'))

        max_idx = max(range(len(self.lending_rates)), key=lambda i: self.lending_rates[i])
        return (self.protocols[max_idx], self.lending_rates[max_idx])

    @property
    def lowest_borrowing_rate(self) -> tuple[str, Decimal]:
        """Get protocol with lowest borrowing rate"""
        if not self.borrowing_rates:
            return ("", Decimal('0'))

        min_idx = min(range(len(self.borrowing_rates)), key=lambda i: self.borrowing_rates[i])
        return (self.protocols[min_idx], self.borrowing_rates[min_idx])

    def get_risk_adjusted_ranking(self) -> List[tuple[str, float]]:
        """Get protocols ranked by risk-adjusted returns"""
        if len(self.protocols) != len(self.lending_rates) or len(self.protocols) != len(self.risk_scores):
            return []

        risk_adjusted = []
        for i in range(len(self.protocols)):
            risk_factor = 1 - self.risk_scores[i]  # Higher risk score = lower factor
            adjusted_return = float(self.lending_rates[i]) * risk_factor
            risk_adjusted.append((self.protocols[i], adjusted_return))

        return sorted(risk_adjusted, key=lambda x: x[1], reverse=True)