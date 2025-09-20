"""
Common Module for Blockchain Collateral Analyzer

This module provides shared components used across all blockchain collateral analysis engines:
- Data models for collateral analysis
- Utility functions for calculations and validation
- Database storage and management
- MCP service client utilities

By centralizing these common components, we eliminate code duplication and ensure
consistency across all analysis engines.
"""

# Import all common modules for easy access
from . import models
from . import utils
from . import database
from . import mcp

# Re-export commonly used items for convenience
from .models import (
    DigitalCollateralType,
    DigitalAsset,
    CollateralPosition,
    CollateralPortfolio,
    CollateralAnalysisResult,
    LiquidationScenario,
    VolatilityMetrics,
    LiquidityMetrics,
    PriceOracle,
)

from .utils import (
    calculate_asset_haircut,
    calculate_portfolio_diversification,
    calculate_portfolio_var,
    validate_positive_number,
    validate_percentage,
    ValidationError,
)

from .database import (
    CollateralDatabase,
    CacheManager,
    DatabaseError,
)

from .mcp import (
    MCPClient,
    MCPServiceManager,
    MCPError,
    create_mcp_client,
    create_service_manager,
)

__version__ = "1.0.0"

__all__ = [
    # Modules
    "models",
    "utils",
    "database",
    "mcp",

    # Data Models
    "DigitalCollateralType",
    "DigitalAsset",
    "CollateralPosition",
    "CollateralPortfolio",
    "CollateralAnalysisResult",
    "LiquidationScenario",
    "VolatilityMetrics",
    "LiquidityMetrics",
    "PriceOracle",

    # Utilities
    "calculate_asset_haircut",
    "calculate_portfolio_diversification",
    "calculate_portfolio_var",
    "validate_positive_number",
    "validate_percentage",
    "ValidationError",

    # Database
    "CollateralDatabase",
    "CacheManager",
    "DatabaseError",

    # MCP Clients
    "MCPClient",
    "MCPServiceManager",
    "MCPError",
    "create_mcp_client",
    "create_service_manager",
]