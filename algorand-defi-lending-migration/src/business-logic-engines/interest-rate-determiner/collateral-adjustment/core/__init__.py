"""
Collateral Adjustment Engine for Interest Rate Determination

This module provides sophisticated collateral-based interest rate adjustments
for Algorand lending platforms, integrating with blockchain collateral analysis.
"""

from .engine import CollateralAdjustmentEngine
from .calculator import CollateralRateCalculator
from .monitor import CollateralMonitor
from .config import CollateralAdjustmentConfig, load_config
from .constants import CollateralAdjustmentConstants

__all__ = [
    'CollateralAdjustmentEngine',
    'CollateralRateCalculator',
    'CollateralMonitor',
    'CollateralAdjustmentConfig',
    'load_config',
    'CollateralAdjustmentConstants'
]

__version__ = "1.0.0"