"""
Portfolio Diversification Engine

A configurable engine for analyzing portfolio diversification using YAML configuration.
"""

from .config import (
    PortfolioDiversificationConfig,
    ConfigLoader,
    load_config
)

from .portfolio_engine import (
    PortfolioDiversificationEngine,
    AssetPosition,
    Portfolio,
    DiversificationAnalysis,
    create_sample_portfolio
)

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = [
    "PortfolioDiversificationConfig",
    "ConfigLoader",
    "load_config",
    "PortfolioDiversificationEngine",
    "AssetPosition",
    "Portfolio",
    "DiversificationAnalysis",
    "create_sample_portfolio"
]