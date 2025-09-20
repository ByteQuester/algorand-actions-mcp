"""
Database model classes for DeFi data storage.

Provides ORM-style models for interacting with DeFi database tables.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass
class AsaPriceHistory:
    """ASA price history database model"""
    id: Optional[int] = None
    asset_id: int = 0
    timestamp: datetime = datetime.now()
    price_algo: Decimal = Decimal('0')
    price_usd: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None
    volatility_24h: Optional[Decimal] = None
    source: str = ""
    created_at: datetime = datetime.now()


@dataclass
class DeFiProtocolYields:
    """DeFi protocol yields database model"""
    id: Optional[int] = None
    protocol_name: str = ""
    asset_id: int = 0
    timestamp: datetime = datetime.now()
    supply_apy: Optional[Decimal] = None
    borrow_apy: Optional[Decimal] = None
    reward_apy: Optional[Decimal] = None
    total_apy: Optional[Decimal] = None
    utilization_rate: Optional[Decimal] = None
    total_supplied: Optional[Decimal] = None
    total_borrowed: Optional[Decimal] = None
    available_liquidity: Optional[Decimal] = None
    protocol_tvl: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now()


@dataclass
class ReputationScoreHistory:
    """Reputation score history database model"""
    id: Optional[int] = None
    address: str = ""
    timestamp: datetime = datetime.now()
    overall_score: Decimal = Decimal('0')
    activity_score: Decimal = Decimal('0')
    consistency_score: Decimal = Decimal('0')
    defi_engagement_score: Decimal = Decimal('0')
    governance_score: Decimal = Decimal('0')
    liquidity_provision_score: Decimal = Decimal('0')
    risk_behavior_score: Decimal = Decimal('0')
    reputation_tier: str = ""
    confidence_level: Decimal = Decimal('0')
    analysis_period_days: int = 0
    data_quality_score: Optional[Decimal] = None
    created_at: datetime = datetime.now()


@dataclass
class GovernanceParticipationHistory:
    """Governance participation history database model"""
    id: Optional[int] = None
    address: str = ""
    period: int = 0
    committed_algo: Decimal = Decimal('0')
    status: str = ""
    votes_cast: int = 0
    total_votes_available: int = 0
    voting_power_used: Decimal = Decimal('0')
    rewards_earned: Optional[Decimal] = None
    penalties_applied: Optional[Decimal] = None
    commitment_round: Optional[int] = None
    commitment_timestamp: Optional[datetime] = None
    created_at: datetime = datetime.now()


@dataclass
class NetworkActivityHistory:
    """Network activity history database model"""
    id: Optional[int] = None
    timestamp: datetime = datetime.now()
    measurement_period_hours: int = 24
    total_transactions: int = 0
    payment_transactions: int = 0
    app_call_transactions: int = 0
    asset_transfer_transactions: int = 0
    transactions_per_second: Decimal = Decimal('0')
    peak_tps: Decimal = Decimal('0')
    average_block_utilization: Decimal = Decimal('0')
    total_fees_paid: Decimal = Decimal('0')
    total_value_transferred: Decimal = Decimal('0')
    unique_active_accounts: int = 0
    defi_transaction_ratio: Decimal = Decimal('0')
    total_defi_volume: Decimal = Decimal('0')
    network_health_score: Optional[Decimal] = None
    created_at: datetime = datetime.now()


@dataclass
class LiquidityPoolHistory:
    """Liquidity pool history database model"""
    id: Optional[int] = None
    pool_id: str = ""
    protocol: str = ""
    asset_a: int = 0
    asset_b: int = 0
    timestamp: datetime = datetime.now()
    reserve_a: Decimal = Decimal('0')
    reserve_b: Decimal = Decimal('0')
    total_liquidity_usd: Decimal = Decimal('0')
    volume_24h_usd: Decimal = Decimal('0')
    fee_revenue_24h: Decimal = Decimal('0')
    base_apy: Decimal = Decimal('0')
    reward_apy: Optional[Decimal] = None
    total_apy: Decimal = Decimal('0')
    impermanent_loss_1d: Optional[Decimal] = None
    price_impact_1pct: Optional[Decimal] = None
    trades_24h: int = 0
    is_active: bool = True
    created_at: datetime = datetime.now()