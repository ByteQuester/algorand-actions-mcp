"""
Dynamic Pricing Engine

Real-time interest rate adjustments based on market conditions, supply/demand,
and liquidity factors for responsive pricing in DeFi lending.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketConditions:
    """Current market conditions for dynamic pricing"""
    supply_utilization: float  # 0-1
    demand_pressure: float  # 0-1
    liquidity_index: float  # 0-1
    volatility_index: float  # 0-1
    competitor_rates: Dict[str, Decimal]


@dataclass
class PricingAdjustment:
    """Dynamic pricing adjustment result"""
    base_rate: Decimal
    adjusted_rate: Decimal
    adjustment_factor: Decimal
    reasoning: List[str]
    confidence: float
    adjustment_timestamp: datetime


class DynamicPricingEngine:
    """Engine for real-time interest rate adjustments"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    async def calculate_dynamic_rate(self, base_rate: Decimal,
                                   market_conditions: MarketConditions) -> PricingAdjustment:
        """Calculate dynamically adjusted interest rate"""
        adjustment_factor = Decimal('1.0')
        reasoning = []

        # Supply/demand adjustments
        if market_conditions.supply_utilization > 0.8:
            adjustment_factor *= Decimal('1.1')
            reasoning.append("High supply utilization (+10%)")

        if market_conditions.demand_pressure > 0.7:
            adjustment_factor *= Decimal('1.05')
            reasoning.append("High demand pressure (+5%)")

        adjusted_rate = base_rate * adjustment_factor

        return PricingAdjustment(
            base_rate=base_rate,
            adjusted_rate=adjusted_rate,
            adjustment_factor=adjustment_factor,
            reasoning=reasoning,
            confidence=0.8,
            adjustment_timestamp=datetime.now()
        )