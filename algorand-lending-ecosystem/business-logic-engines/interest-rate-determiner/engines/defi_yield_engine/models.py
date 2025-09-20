"""
Data models for DeFi yield analysis
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class ProtocolType(Enum):
    """Types of DeFi protocols"""
    DEX = "dex"
    LENDING = "lending"
    YIELD_FARMING = "yield_farming"
    LIQUIDITY_MINING = "liquidity_mining"
    STAKING = "staking"

@dataclass
class DeFiProtocolData:
    """Data for a specific DeFi protocol"""
    protocol_name: str
    protocol_type: ProtocolType
    tvl_usd: Decimal
    apy: Decimal
    volume_24h: Decimal
    fees_24h: Decimal
    token_address: Optional[str]
    pool_count: int
    active_users: int
    risk_score: Decimal  # 0-1, where 1 is highest risk
    timestamp: datetime

    def risk_adjusted_apy(self) -> Decimal:
        """Calculate risk-adjusted APY"""
        risk_penalty = self.risk_score * Decimal('0.2')  # Up to 20% penalty
        return max(self.apy * (Decimal('1') - risk_penalty), Decimal('0'))

@dataclass
class YieldMetrics:
    """Aggregated yield metrics across protocols"""
    weighted_avg_apy: Decimal
    median_apy: Decimal
    top_quartile_apy: Decimal
    total_tvl: Decimal
    protocol_count: int
    risk_adjusted_apy: Decimal
    volatility_score: Decimal
    timestamp: datetime

@dataclass
class PoolData:
    """Liquidity pool specific data"""
    pool_id: str
    protocol_name: str
    token_pair: str
    tvl_usd: Decimal
    apy: Decimal
    volume_24h: Decimal
    fees_apy: Decimal
    farming_apy: Decimal
    impermanent_loss_risk: Decimal
    utilization_rate: Decimal
    timestamp: datetime

    def total_apy(self) -> Decimal:
        """Calculate total APY including fees and farming rewards"""
        return self.fees_apy + self.farming_apy

    def risk_score(self) -> Decimal:
        """Calculate risk score for the pool"""
        # Factors: impermanent loss, utilization, volatility
        il_risk = self.impermanent_loss_risk
        util_risk = abs(self.utilization_rate - Decimal('0.8')) / Decimal('0.8')  # Optimal ~80%

        return (il_risk + util_risk) / Decimal('2')

@dataclass
class DeFiMarketData:
    """Overall DeFi market data"""
    total_market_cap: Decimal
    total_tvl: Decimal
    algo_price_usd: Decimal
    market_volatility: Decimal
    fear_greed_index: Decimal
    defi_dominance: Decimal
    timestamp: datetime