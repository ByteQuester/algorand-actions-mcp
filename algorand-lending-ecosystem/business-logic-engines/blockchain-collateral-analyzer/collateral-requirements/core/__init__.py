"""
Collateral Requirements Core Module

Core functionality for calculating digital asset collateral requirements.
"""

from .collateral_engine import (
    CollateralRequirementsEngine,
    CollateralPosition,
    CollateralRequirement
)
from .database import CollateralDatabase

__all__ = [
    'CollateralRequirementsEngine',
    'CollateralPosition',
    'CollateralRequirement',
    'CollateralDatabase'
]