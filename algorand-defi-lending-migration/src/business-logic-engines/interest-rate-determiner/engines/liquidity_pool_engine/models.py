from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List
from datetime import datetime
from enum import Enum

class PoolHealth(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class LiquidityMetrics:
    total_tvl: Decimal
    avg_utilization: Decimal
    pool_count: int
    top_pool_concentration: Decimal
    health_score: Decimal
    timestamp: datetime

@dataclass
class DEXMetrics:
    dex_name: str
    tvl: Decimal
    volume_24h: Decimal
    pool_count: int
    avg_apy: Decimal
    timestamp: datetime