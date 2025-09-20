"""
Algorand blockchain-specific data models for DeFi interest rate determination.

Core models for Algorand account data, ASA tokens, transactions,
governance participation, and network activity analysis.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum


class AssetType(Enum):
    """Types of Algorand assets"""
    ALGO = "ALGO"
    ASA = "ASA"
    NFT = "NFT"
    LP_TOKEN = "LP_TOKEN"
    GOVERNANCE_TOKEN = "GOVERNANCE_TOKEN"
    STABLECOIN = "STABLECOIN"
    UTILITY_TOKEN = "UTILITY_TOKEN"


class AssetRiskLevel(Enum):
    """Risk levels for ASAs"""
    VERY_LOW = "VERY_LOW"      # USDC, USDT, major stablecoins
    LOW = "LOW"                # Established projects, high liquidity
    MEDIUM = "MEDIUM"          # Mid-cap projects, moderate liquidity
    HIGH = "HIGH"              # Small projects, low liquidity
    VERY_HIGH = "VERY_HIGH"    # New/experimental projects
    UNKNOWN = "UNKNOWN"        # No sufficient data


class DeFiProtocol(Enum):
    """Supported DeFi protocols on Algorand"""
    ALGOFI = "ALGOFI"
    FOLKS_FINANCE = "FOLKS_FINANCE"
    TINYMAN = "TINYMAN"
    PACT = "PACT"
    ALGODEX = "ALGODEX"
    YIELDLY = "YIELDLY"
    HUMBLE = "HUMBLE"
    C3 = "C3"


@dataclass
class ASAMetadata:
    """Metadata for an Algorand Standard Asset"""
    asset_id: int
    name: str
    unit_name: str
    total_supply: Decimal
    decimals: int
    creator_address: str

    # Market data
    current_price_algo: Decimal = Decimal('0')
    current_price_usd: Decimal = Decimal('0')
    market_cap_usd: Decimal = Decimal('0')
    daily_volume_usd: Decimal = Decimal('0')

    # Risk assessment
    risk_level: AssetRiskLevel = AssetRiskLevel.UNKNOWN
    asset_type: AssetType = AssetType.ASA
    liquidity_score: float = 0.0  # 0 = illiquid, 1 = very liquid

    # Verification status
    is_verified: bool = False
    verification_tier: Optional[str] = None
    audit_status: Optional[str] = None

    # Additional metadata
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None

    # Metadata timestamps
    created_date: Optional[datetime] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ASAPosition:
    """Position in an Algorand Standard Asset"""
    asset_id: int
    asset_metadata: ASAMetadata

    # Position details
    balance: Decimal
    balance_in_algo: Decimal
    balance_in_usd: Decimal

    # Cost basis and performance
    average_cost_algo: Decimal = Decimal('0')
    average_cost_usd: Decimal = Decimal('0')
    unrealized_pnl_algo: Decimal = Decimal('0')
    unrealized_pnl_usd: Decimal = Decimal('0')

    # Position metrics
    position_size_pct: float = 0.0  # Percentage of total portfolio
    days_held: int = 0

    # Risk metrics
    value_at_risk_1d: Decimal = Decimal('0')  # 1-day VaR
    position_risk_score: float = 0.0

    # Timestamps
    first_acquired: Optional[datetime] = None
    last_transaction: Optional[datetime] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ASAValuation:
    """Comprehensive valuation of ASA holdings"""

    # Portfolio summary
    total_asa_count: int
    total_value_algo: Decimal
    total_value_usd: Decimal

    # Individual positions
    positions: List[ASAPosition] = field(default_factory=list)

    # Portfolio composition
    largest_position_pct: float = 0.0
    top_5_concentration: float = 0.0
    diversity_score: float = 0.0  # Shannon diversity index

    # Risk metrics
    portfolio_var_1d: Decimal = Decimal('0')  # Portfolio Value at Risk
    portfolio_risk_score: float = 0.0
    correlation_risk: float = 0.0

    # Quality metrics
    verified_assets_pct: float = 0.0
    liquid_assets_pct: float = 0.0
    stablecoin_pct: float = 0.0

    # Valuation methodology
    valuation_confidence: float = 1.0
    pricing_sources: List[str] = field(default_factory=list)
    last_valuation: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_position_by_asset_id(self, asset_id: int) -> Optional[ASAPosition]:
        """Get position for specific asset ID"""
        return next((pos for pos in self.positions if pos.asset_id == asset_id), None)

    def get_high_risk_exposure(self) -> float:
        """Calculate exposure to high-risk assets"""
        high_risk_value = sum(
            float(pos.balance_in_usd)
            for pos in self.positions
            if pos.asset_metadata.risk_level in [AssetRiskLevel.HIGH, AssetRiskLevel.VERY_HIGH]
        )
        return high_risk_value / max(float(self.total_value_usd), 1.0)

    def get_liquidity_score(self) -> float:
        """Calculate weighted average liquidity score"""
        if not self.positions or self.total_value_usd == 0:
            return 0.0

        weighted_liquidity = sum(
            pos.asset_metadata.liquidity_score * float(pos.balance_in_usd)
            for pos in self.positions
        )
        return weighted_liquidity / float(self.total_value_usd)


@dataclass
class DeFiPosition:
    """Position in a DeFi protocol"""
    protocol: DeFiProtocol
    position_type: str  # "lending", "borrowing", "LP", "staking"

    # Position details
    asset_supplied: Optional[int] = None  # Asset ID
    asset_borrowed: Optional[int] = None  # Asset ID
    supplied_amount: Decimal = Decimal('0')
    borrowed_amount: Decimal = Decimal('0')

    # LP positions
    lp_token_balance: Decimal = Decimal('0')
    lp_token_value_usd: Decimal = Decimal('0')

    # Yield and performance
    current_supply_apy: float = 0.0
    current_borrow_apy: float = 0.0
    accumulated_interest: Decimal = Decimal('0')
    accumulated_rewards: Decimal = Decimal('0')

    # Risk metrics
    health_factor: Optional[float] = None  # For borrowing positions
    liquidation_threshold: Optional[float] = None
    utilization_rate: float = 0.0

    # Timestamps
    position_opened: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SmartContractInteraction:
    """Record of smart contract interaction"""
    app_id: int
    interaction_type: str  # "call", "opt_in", "close_out", "clear_state"
    transaction_id: str

    # Interaction details
    method_called: Optional[str] = None
    args_provided: List[Any] = field(default_factory=list)
    assets_involved: List[int] = field(default_factory=list)

    # Financial impact
    algo_spent: Decimal = Decimal('0')
    assets_transferred: Dict[int, Decimal] = field(default_factory=dict)

    # Protocol identification
    protocol_name: Optional[str] = None
    protocol_category: Optional[str] = None

    # Risk assessment
    interaction_risk_score: float = 0.0
    success: bool = True

    # Metadata
    block_number: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AlgorandWallet:
    """Comprehensive Algorand wallet analysis"""

    # Basic wallet info
    address: str

    # Balances
    algo_balance: Decimal
    min_balance_requirement: Decimal
    available_balance: Decimal

    # ASA holdings
    asa_valuation: ASAValuation

    # DeFi positions
    defi_positions: List[DeFiPosition] = field(default_factory=list)

    # Smart contract interactions
    smart_contract_interactions: List[SmartContractInteraction] = field(default_factory=list)

    # Wallet characteristics
    wallet_age_days: int = 0
    total_transactions: int = 0
    unique_counterparties: int = 0

    # Activity patterns
    average_monthly_transactions: float = 0.0
    largest_transaction_algo: Decimal = Decimal('0')
    most_active_protocol: Optional[DeFiProtocol] = None

    # Risk assessment
    overall_risk_score: float = 0.0
    kyc_level: Optional[str] = None

    # Governance and staking
    governance_participation: bool = False
    consensus_participation: bool = False

    # Metadata
    last_analysis: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_confidence: float = 1.0

    def get_total_portfolio_value_usd(self) -> Decimal:
        """Calculate total portfolio value in USD"""
        algo_value = self.algo_balance * self._get_algo_price_usd()
        asa_value = self.asa_valuation.total_value_usd
        defi_value = sum(pos.lp_token_value_usd for pos in self.defi_positions)
        return algo_value + asa_value + defi_value

    def get_net_defi_position(self) -> Decimal:
        """Calculate net DeFi position (supplied - borrowed)"""
        total_supplied = sum(pos.supplied_amount for pos in self.defi_positions)
        total_borrowed = sum(pos.borrowed_amount for pos in self.defi_positions)
        return total_supplied - total_borrowed

    def get_defi_health_factor(self) -> Optional[float]:
        """Get the lowest health factor across all DeFi positions"""
        health_factors = [
            pos.health_factor for pos in self.defi_positions
            if pos.health_factor is not None
        ]
        return min(health_factors) if health_factors else None

    def is_defi_active(self) -> bool:
        """Check if wallet is actively using DeFi protocols"""
        return len(self.defi_positions) > 0

    def get_protocol_interaction_count(self, protocol: DeFiProtocol) -> int:
        """Count interactions with specific protocol"""
        return len([
            interaction for interaction in self.smart_contract_interactions
            if interaction.protocol_name == protocol.value
        ])

    def calculate_liquidity_score(self) -> float:
        """Calculate overall wallet liquidity score"""
        # Base ALGO liquidity (always liquid)
        algo_ratio = float(self.algo_balance / self.get_total_portfolio_value_usd())
        algo_contribution = algo_ratio * 1.0

        # ASA liquidity (weighted by individual asset liquidity)
        asa_ratio = float(self.asa_valuation.total_value_usd / self.get_total_portfolio_value_usd())
        asa_contribution = asa_ratio * self.asa_valuation.get_liquidity_score()

        # DeFi positions (less liquid)
        defi_value = sum(pos.lp_token_value_usd for pos in self.defi_positions)
        defi_ratio = float(defi_value / self.get_total_portfolio_value_usd())
        defi_contribution = defi_ratio * 0.5  # Assume 50% liquidity for DeFi

        return algo_contribution + asa_contribution + defi_contribution

    def _get_algo_price_usd(self) -> Decimal:
        """Get current ALGO price in USD (placeholder)"""
        # This would be fetched from market data service
        return Decimal('0.15')  # Placeholder price

    def get_collateral_quality_assessment(self) -> Dict[str, Any]:
        """Assess quality of holdings as collateral"""
        total_value = self.get_total_portfolio_value_usd()

        # ALGO assessment (highest quality)
        algo_value = self.algo_balance * self._get_algo_price_usd()
        algo_ratio = float(algo_value / total_value) if total_value > 0 else 0

        # Stablecoin assessment (high quality)
        stablecoin_ratio = self.asa_valuation.stablecoin_pct

        # Verified assets assessment (medium-high quality)
        verified_ratio = self.asa_valuation.verified_assets_pct

        # Liquid assets assessment
        liquid_ratio = self.asa_valuation.liquid_assets_pct

        # Overall quality score
        quality_score = (
            algo_ratio * 1.0 +
            stablecoin_ratio * 0.9 +
            verified_ratio * 0.7 +
            liquid_ratio * 0.5
        ) / 4.0

        return {
            'overall_quality_score': quality_score,
            'algo_percentage': algo_ratio,
            'stablecoin_percentage': stablecoin_ratio,
            'verified_assets_percentage': verified_ratio,
            'liquid_assets_percentage': liquid_ratio,
            'acceptable_as_collateral': quality_score > 0.6,
            'recommended_ltv': min(0.8 * quality_score, 0.75)  # Max 75% LTV
        }


class TransactionType(Enum):
    """Types of Algorand transactions"""
    PAYMENT = "pay"
    ASSET_TRANSFER = "axfer"
    ASSET_CONFIG = "acfg"
    ASSET_FREEZE = "afrz"
    APPLICATION_CALL = "appl"
    KEY_REGISTRATION = "keyreg"
    STATE_PROOF = "stpf"


class GovernanceStatus(Enum):
    """Algorand governance participation status"""
    ELIGIBLE = "eligible"
    COMMITTED = "committed"
    VOTING = "voting"
    REWARDED = "rewarded"
    INELIGIBLE = "ineligible"


@dataclass
class AlgorandAccount:
    """Algorand account information and metrics"""
    address: str
    algo_balance: Decimal
    min_balance: Decimal
    total_assets_opted_in: int
    total_apps_opted_in: int
    total_created_assets: int
    total_created_apps: int
    auth_addr: Optional[str] = None
    created_at_round: Optional[int] = None
    deleted: bool = False
    rewards: Decimal = Decimal('0')
    pending_rewards: Decimal = Decimal('0')
    reward_base: Optional[int] = None
    status: str = "Online"
    sig_type: Optional[str] = None

    @property
    def available_balance(self) -> Decimal:
        """Calculate available ALGO balance after min balance"""
        return max(Decimal('0'), self.algo_balance - self.min_balance)

    @property
    def total_balance_with_rewards(self) -> Decimal:
        """Total balance including pending rewards"""
        return self.algo_balance + self.pending_rewards


@dataclass
class ASAToken:
    """Algorand Standard Asset (ASA) information"""
    asset_id: int
    name: str
    unit_name: str
    total: Decimal
    decimals: int
    default_frozen: bool = False
    manager: Optional[str] = None
    reserve: Optional[str] = None
    freeze: Optional[str] = None
    clawback: Optional[str] = None
    creator: Optional[str] = None
    url: Optional[str] = None
    metadata_hash: Optional[str] = None
    created_at_round: Optional[int] = None
    deleted: bool = False

    # Market data
    current_price_algo: Optional[Decimal] = None
    current_price_usd: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None

    @property
    def is_pure_asa(self) -> bool:
        """Check if ASA is a pure token (not NFT)"""
        return self.total > 1 and self.decimals > 0

    @property
    def is_nft(self) -> bool:
        """Check if ASA is an NFT"""
        return self.total == 1 and self.decimals == 0


@dataclass
class OnChainTransaction:
    """Algorand transaction data"""
    txn_id: str
    sender: str
    receiver: Optional[str]
    amount: Decimal
    fee: Decimal
    round_number: int
    block_time: datetime
    txn_type: TransactionType
    asset_id: Optional[int] = None
    application_id: Optional[int] = None
    note: Optional[str] = None
    group: Optional[str] = None
    inner_txns: List['OnChainTransaction'] = field(default_factory=list)

    # Application call specific
    app_args: List[str] = field(default_factory=list)
    accounts: List[str] = field(default_factory=list)
    foreign_apps: List[int] = field(default_factory=list)
    foreign_assets: List[int] = field(default_factory=list)

    @property
    def is_defi_transaction(self) -> bool:
        """Check if transaction is DeFi protocol related"""
        defi_patterns = ['swap', 'pool', 'stake', 'farm', 'lend', 'borrow']
        if self.note:
            return any(pattern in self.note.lower() for pattern in defi_patterns)
        return self.txn_type == TransactionType.APPLICATION_CALL


@dataclass
class GovernanceData:
    """Algorand governance participation data"""
    period: int
    address: str
    committed_algo: Decimal
    status: GovernanceStatus
    votes_cast: int
    total_votes_available: int
    commitment_round: Optional[int] = None
    commitment_timestamp: Optional[datetime] = None
    rewards_earned: Decimal = Decimal('0')
    penalties_applied: Decimal = Decimal('0')

    @property
    def participation_rate(self) -> float:
        """Calculate governance participation rate"""
        if self.total_votes_available == 0:
            return 0.0
        return self.votes_cast / self.total_votes_available

    @property
    def is_eligible_for_rewards(self) -> bool:
        """Check if eligible for governance rewards"""
        return (
            self.status in [GovernanceStatus.COMMITTED, GovernanceStatus.VOTING, GovernanceStatus.REWARDED] and
            self.participation_rate >= 0.9  # 90% voting requirement
        )


@dataclass
class StakingReward:
    """Algorand staking and participation rewards"""
    address: str
    round_number: int
    timestamp: datetime
    reward_amount: Decimal
    reward_type: str  # 'participation', 'governance', 'consensus'
    period: Optional[int] = None  # For governance rewards

    # Staking metrics
    staked_amount: Optional[Decimal] = None
    apy: Optional[Decimal] = None
    duration_days: Optional[int] = None


@dataclass
class NetworkActivity:
    """Algorand network activity metrics"""
    address: str
    measurement_period: str  # '24h', '7d', '30d', '90d'

    # Transaction metrics
    total_transactions: int
    transaction_volume_algo: Decimal
    transaction_volume_usd: Optional[Decimal] = None
    avg_transaction_size: Decimal = Decimal('0')
    unique_counterparties: int = 0

    # DeFi activity
    defi_transactions: int = 0
    defi_volume_algo: Decimal = Decimal('0')
    protocols_used: List[str] = field(default_factory=list)

    # Asset activity
    asset_transfers: int = 0
    unique_assets_traded: int = 0

    # Application activity
    app_calls: int = 0
    unique_apps_used: int = 0

    # Time-based metrics
    active_days: int = 0
    longest_inactive_period_days: int = 0

    @property
    def activity_score(self) -> float:
        """Calculate normalized activity score (0-100)"""
        # Weight different types of activity
        weights = {
            'transactions': 0.3,
            'defi': 0.4,
            'consistency': 0.3
        }

        # Normalize transaction activity (log scale)
        import math
        txn_score = min(100, math.log10(max(1, self.total_transactions)) * 25)

        # DeFi activity score
        defi_score = min(100, (self.defi_transactions / max(1, self.total_transactions)) * 100)

        # Consistency score based on active days
        period_days = {'24h': 1, '7d': 7, '30d': 30, '90d': 90}.get(self.measurement_period, 30)
        consistency_score = min(100, (self.active_days / period_days) * 100)

        return (
            weights['transactions'] * txn_score +
            weights['defi'] * defi_score +
            weights['consistency'] * consistency_score
        )