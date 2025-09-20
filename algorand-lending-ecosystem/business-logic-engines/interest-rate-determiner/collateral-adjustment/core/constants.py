"""
Constants for Collateral Adjustment Engine

Defines standard constants for collateral-based interest rate adjustments.
"""

from enum import Enum
from typing import Dict, Any
from pathlib import Path
import json


class CollateralTier(Enum):
    """Collateral quality tiers"""
    PREMIUM = "premium"        # Blue chip assets like ALGO, established stablecoins
    STANDARD = "standard"      # Verified ASAs, established tokens
    SPECULATIVE = "speculative"  # New or volatile assets
    HIGH_RISK = "high_risk"    # Experimental or extremely volatile assets


class RiskAdjustmentType(Enum):
    """Types of risk adjustments"""
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    CONCENTRATION = "concentration"
    CORRELATION = "correlation"
    COUNTERPARTY = "counterparty"


class CollateralAdjustmentConstants:
    """
    Configurable constants for collateral-based rate adjustments
    """

    def __init__(self, config_path: Path = None):
        """Initialize with optional config file override"""
        self.config_path = config_path
        self._load_constants()

    def _load_constants(self):
        """Load constants from config file or use defaults"""
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                constants = config.get('constants', {})
        else:
            constants = {}

        # Base collateral discount factors by tier
        self.COLLATERAL_DISCOUNT_FACTORS = constants.get('collateral_discount_factors', {
            CollateralTier.PREMIUM.value: 0.85,      # 15% discount
            CollateralTier.STANDARD.value: 0.75,     # 25% discount
            CollateralTier.SPECULATIVE.value: 0.60,  # 40% discount
            CollateralTier.HIGH_RISK.value: 0.45     # 55% discount
        })

        # Interest rate adjustments based on LTV ratio
        self.LTV_RATE_ADJUSTMENTS = constants.get('ltv_rate_adjustments', {
            0.0: -0.002,   # Very low LTV gets rate discount
            0.3: 0.0,      # Baseline
            0.5: 0.003,    # Moderate increase
            0.7: 0.008,    # Higher increase
            0.8: 0.015,    # Significant increase
            0.9: 0.025     # Maximum rate adjustment
        })

        # Asset-specific risk premiums (basis points)
        self.ASSET_RISK_PREMIUMS = constants.get('asset_risk_premiums', {
            'ALGO': 0.001,      # 10 basis points
            'USDC': 0.0005,     # 5 basis points
            'USDT': 0.0008,     # 8 basis points
            'ASA_VERIFIED': 0.002,    # 20 basis points
            'ASA_UNVERIFIED': 0.005,  # 50 basis points
            'GOVERNANCE_TOKEN': 0.003 # 30 basis points
        })

        # Liquidation premiums by asset type
        self.LIQUIDATION_PREMIUMS = constants.get('liquidation_premiums', {
            CollateralTier.PREMIUM.value: 0.05,      # 5% premium
            CollateralTier.STANDARD.value: 0.08,     # 8% premium
            CollateralTier.SPECULATIVE.value: 0.12,  # 12% premium
            CollateralTier.HIGH_RISK.value: 0.20     # 20% premium
        })

        # Diversification discounts (max discount for well-diversified portfolio)
        self.DIVERSIFICATION_DISCOUNTS = constants.get('diversification_discounts', {
            'single_asset': 0.0,       # No discount
            'two_assets': -0.0005,     # 0.5 basis points
            'three_plus_assets': -0.001, # 1 basis point
            'cross_category': -0.0015   # 1.5 basis points
        })

        # Volatility thresholds and adjustments
        self.VOLATILITY_ADJUSTMENTS = constants.get('volatility_adjustments', {
            0.1: 0.0,      # Low volatility
            0.2: 0.001,    # Moderate volatility
            0.3: 0.002,    # High volatility
            0.5: 0.004,    # Very high volatility
            1.0: 0.008     # Extreme volatility
        })

        # Liquidity impact factors
        self.LIQUIDITY_ADJUSTMENTS = constants.get('liquidity_adjustments', {
            'high_liquidity': -0.0005,   # Discount for liquid assets
            'medium_liquidity': 0.0,     # Neutral
            'low_liquidity': 0.002,      # Premium for illiquid assets
            'very_low_liquidity': 0.005  # High premium
        })

        # Correlation risk adjustments
        self.CORRELATION_ADJUSTMENTS = constants.get('correlation_adjustments', {
            'low_correlation': -0.0005,    # Discount for uncorrelated assets
            'medium_correlation': 0.0,     # Neutral
            'high_correlation': 0.001,     # Premium for correlated assets
            'perfect_correlation': 0.003   # High premium
        })

        # Time-based adjustments (loan duration impact)
        self.DURATION_ADJUSTMENTS = constants.get('duration_adjustments', {
            30: 0.0,       # 30 days - baseline
            90: 0.0005,    # 90 days
            180: 0.001,    # 6 months
            365: 0.002,    # 1 year
            730: 0.004     # 2 years
        })

        # DeFi protocol integration factors
        self.DEFI_INTEGRATION_FACTORS = constants.get('defi_integration_factors', {
            'isolated_lending': 0.0,       # Baseline
            'cross_protocol': 0.001,       # Cross-protocol risk
            'yield_farming': 0.002,        # Additional yield farming risk
            'leverage_protocol': 0.003,    # Leverage protocol risk
            'experimental_defi': 0.005     # Experimental protocol risk
        })

        # Smart contract security ratings impact
        self.SECURITY_RATING_ADJUSTMENTS = constants.get('security_rating_adjustments', {
            'AAA': -0.0005,  # Premium security rating discount
            'AA': 0.0,       # High security rating baseline
            'A': 0.0005,     # Good security rating
            'BBB': 0.001,    # Average security rating
            'BB': 0.002,     # Below average security
            'B': 0.004,      # Poor security rating
            'UNRATED': 0.006 # Unrated contracts
        })

        # Minimum and maximum rate adjustments
        self.MIN_RATE_ADJUSTMENT = constants.get('min_rate_adjustment', -0.005)  # -50 basis points max discount
        self.MAX_RATE_ADJUSTMENT = constants.get('max_rate_adjustment', 0.050)   # +500 basis points max premium

        # Emergency adjustment factors
        self.EMERGENCY_FACTORS = constants.get('emergency_factors', {
            'market_stress': 0.010,      # Market stress premium
            'liquidity_crisis': 0.020,   # Liquidity crisis premium
            'protocol_exploit': 0.030,   # Protocol exploit premium
            'regulatory_uncertainty': 0.005  # Regulatory uncertainty premium
        })

        # Collateral monitoring thresholds
        self.MONITORING_THRESHOLDS = constants.get('monitoring_thresholds', {
            'ltv_warning': 0.80,         # Warning threshold
            'ltv_critical': 0.85,        # Critical threshold
            'ltv_liquidation': 0.90,     # Liquidation threshold
            'price_change_alert': 0.10,  # 10% price change alert
            'volatility_spike': 0.50     # 50% volatility spike
        })

    def get_collateral_tier(self, asset_symbol: str, asset_metadata: Dict[str, Any]) -> CollateralTier:
        """Determine collateral tier for an asset"""
        # Premium tier assets
        premium_assets = {'ALGO', 'USDC', 'USDT'}
        if asset_symbol in premium_assets:
            return CollateralTier.PREMIUM

        # Check if it's a verified ASA
        if asset_metadata.get('verified', False):
            market_cap = asset_metadata.get('market_cap', 0)
            if market_cap > 10_000_000:  # $10M market cap threshold
                return CollateralTier.STANDARD
            else:
                return CollateralTier.SPECULATIVE

        return CollateralTier.HIGH_RISK

    def get_liquidity_category(self, daily_volume: float, market_cap: float) -> str:
        """Categorize asset liquidity"""
        if market_cap == 0:
            return 'very_low_liquidity'

        volume_ratio = daily_volume / market_cap

        if volume_ratio > 0.1:
            return 'high_liquidity'
        elif volume_ratio > 0.05:
            return 'medium_liquidity'
        elif volume_ratio > 0.01:
            return 'low_liquidity'
        else:
            return 'very_low_liquidity'