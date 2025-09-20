"""
Volatility Assessment Engine - Core Module

This module provides configurable volatility assessment functionality for
blockchain collateral analysis. It extracts parameters from oracle_integration.py
and makes them configurable via YAML files.

Key Features:
- YAML-based configuration management
- Configurable price staleness scoring
- Configurable volatility calculation parameters
- Configurable manipulation detection thresholds
- Oracle confidence scoring with configurable weights
- MCP service integration

Main Components:
- config.py: Configuration loading and management
- volatility_engine.py: Main volatility assessment engine
"""

from .config import VolatilityEngineConfig, ConfigLoader, load_config
from .volatility_engine import (
    VolatilityAssessmentEngine,
    PriceFeed,
    AggregatedPrice,
    VolatilityMetrics,
    OracleStatus,
    PriceOracle
)

__all__ = [
    'VolatilityEngineConfig',
    'ConfigLoader',
    'load_config',
    'VolatilityAssessmentEngine',
    'PriceFeed',
    'AggregatedPrice',
    'VolatilityMetrics',
    'OracleStatus',
    'PriceOracle'
]