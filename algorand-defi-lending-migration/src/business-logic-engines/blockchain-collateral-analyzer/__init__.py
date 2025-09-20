"""
Blockchain Collateral Analyzer Module

This module provides comprehensive analysis of digital collateral for DeFi lending on Algorand.
It evaluates cryptocurrency assets, calculates risk-adjusted valuations, and determines
appropriate collateralization ratios for secure lending operations.

Key Components:
- Digital asset valuation with real-time pricing
- Volatility assessment and VaR calculations
- Liquidation scenario modeling
- Portfolio diversification analysis
- Oracle price feed integration
- Final collateral requirement determination

The module supports various digital asset types including:
- ALGO (native Algorand cryptocurrency)
- ASA tokens (Algorand Standard Assets)
- Stablecoins (USDC, USDT on Algorand)
- Governance tokens
- Liquidity pool tokens
- Liquid staking derivatives
"""

# Import from individual engine modules with proper error handling
import sys
import logging
from typing import Optional, Type, Any

logger = logging.getLogger(__name__)

# Engine imports with graceful fallbacks
DigitalAssetValuationEngine: Optional[Type[Any]] = None
VolatilityAssessmentEngine: Optional[Type[Any]] = None
LiquidationEngine: Optional[Type[Any]] = None
OraclePriceIntegrationEngine: Optional[Type[Any]] = None
PortfolioEngine: Optional[Type[Any]] = None
CollateralRequirementsEngine: Optional[Type[Any]] = None

# Try different import methods depending on how the module is being loaded
def _try_import_engine(module_path, class_name, engine_name):
    """Try to import an engine class with multiple fallback methods."""
    try:
        # Try relative import first (for package installation)
        if '__name__' in globals() and '.' in globals().get('__name__', ''):
            module = __import__(f".{module_path}", fromlist=[class_name], level=1)
            return getattr(module, class_name)
    except (ImportError, ValueError, KeyError):
        pass

    try:
        # Try absolute import with current directory in path
        import importlib.util
        import os

        # Convert module path to file path
        module_file_path = module_path.replace('.', os.sep) + '.py'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, module_file_path)

        if os.path.exists(full_path):
            spec = importlib.util.spec_from_file_location(f"{engine_name}_engine", full_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return getattr(module, class_name, None)
    except Exception:
        pass

    try:
        # Try direct import (last resort)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except Exception:
        logger.warning(f"Failed to import {class_name} from {engine_name} engine")
        return None

# Import engines with fallback handling
DigitalAssetValuationEngine = _try_import_engine(
    "digital_asset_valuation.core.engine",
    "DigitalAssetValuationEngine",
    "digital_asset_valuation"
)

VolatilityAssessmentEngine = _try_import_engine(
    "volatility_assessment.core.volatility_engine",
    "VolatilityAssessmentEngine",
    "volatility_assessment"
)

LiquidationEngine = _try_import_engine(
    "liquidation_scenarios.core.liquidation_engine",
    "LiquidationEngine",
    "liquidation_scenarios"
)

OraclePriceIntegrationEngine = _try_import_engine(
    "oracle_price_integration.core.oracle_engine",
    "OraclePriceIntegrationEngine",
    "oracle_price_integration"
)

PortfolioEngine = _try_import_engine(
    "portfolio_diversification.core.portfolio_engine",
    "PortfolioEngine",
    "portfolio_diversification"
)

CollateralRequirementsEngine = _try_import_engine(
    "collateral_requirements.core.collateral_engine",
    "CollateralRequirementsEngine",
    "collateral_requirements"
)

# Convenience function to get available engines
def get_available_engines():
    """Return a dictionary of available engine classes."""
    engines = {}
    if DigitalAssetValuationEngine:
        engines['digital_asset_valuation'] = DigitalAssetValuationEngine
    if VolatilityAssessmentEngine:
        engines['volatility_assessment'] = VolatilityAssessmentEngine
    if LiquidationEngine:
        engines['liquidation_scenarios'] = LiquidationEngine
    if OraclePriceIntegrationEngine:
        engines['oracle_price_integration'] = OraclePriceIntegrationEngine
    if PortfolioEngine:
        engines['portfolio_diversification'] = PortfolioEngine
    if CollateralRequirementsEngine:
        engines['collateral_requirements'] = CollateralRequirementsEngine
    return engines

def check_engine_availability():
    """Check which engines are available for use."""
    available = get_available_engines()
    total_engines = 6
    available_count = len(available)

    print(f"Blockchain Collateral Analyzer v{__version__}")
    print(f"Available engines: {available_count}/{total_engines}")

    for engine_name, engine_class in available.items():
        print(f"  ✓ {engine_name}: {engine_class.__name__}")

    missing_engines = set([
        'digital_asset_valuation', 'volatility_assessment', 'liquidation_scenarios',
        'oracle_price_integration', 'portfolio_diversification', 'collateral_requirements'
    ]) - set(available.keys())

    if missing_engines:
        print("Missing engines:")
        for engine_name in missing_engines:
            print(f"  ✗ {engine_name}")

    return available

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = [
    # Engine modules
    "DigitalAssetValuationEngine",
    "VolatilityAssessmentEngine",
    "LiquidationEngine",
    "OraclePriceIntegrationEngine",
    "PortfolioEngine",
    "CollateralRequirementsEngine",
    # Utility functions
    "get_available_engines",
    "check_engine_availability",
    # Metadata
    "__version__",
    "__author__"
]