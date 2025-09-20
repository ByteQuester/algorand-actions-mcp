from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List
from datetime import datetime
from enum import Enum

class NetworkHealth(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    CONGESTED = "congested"
    CRITICAL = "critical"

@dataclass
class NetworkMetrics:
    tps_current: Decimal
    tps_average: Decimal
    block_time: Decimal
    pending_transactions: int
    network_health: NetworkHealth
    congestion_score: Decimal
    fee_multiplier: Decimal
    timestamp: datetime

@dataclass
class CongestionData:
    avg_fee: Decimal
    fee_volatility: Decimal
    queue_length: int
    processing_delay: Decimal
    timestamp: datetime

@dataclass
class UsagePattern:
    peak_hours: List[int]
    daily_volume: Decimal
    application_calls: int
    payment_ratio: Decimal
    timestamp: datetime