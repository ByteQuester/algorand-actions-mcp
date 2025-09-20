"""
Configuration management for Collateral Adjustment Engine
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CollateralMonitoringConfig:
    """Configuration for collateral monitoring"""
    price_update_interval: int = 30  # seconds
    volatility_window: int = 24  # hours
    liquidity_check_interval: int = 300  # seconds
    correlation_analysis_window: int = 7  # days
    emergency_check_interval: int = 10  # seconds during stress

    # Alert thresholds
    price_deviation_threshold: float = 0.05  # 5%
    volatility_spike_threshold: float = 0.3   # 30%
    liquidity_drop_threshold: float = 0.5     # 50%


@dataclass
class RiskAssessmentConfig:
    """Configuration for risk assessment"""
    volatility_lookback_days: int = 30
    correlation_lookback_days: int = 90
    liquidity_measurement_window: int = 7  # days

    # Risk model parameters
    use_monte_carlo_simulation: bool = True
    simulation_iterations: int = 10000
    confidence_level: float = 0.95

    # Asset classification thresholds
    high_cap_threshold: int = 100_000_000  # $100M
    mid_cap_threshold: int = 10_000_000    # $10M
    min_volume_threshold: int = 100_000    # $100K daily


@dataclass
class RateCalculationConfig:
    """Configuration for rate calculation algorithms"""
    base_rate_source: str = "fed_funds_rate"  # or "libor", "sofr"
    base_rate_premium: float = 0.02  # 200 basis points

    # Adjustment calculation methods
    ltv_adjustment_method: str = "linear"  # or "exponential", "step"
    volatility_adjustment_method: str = "log_normal"
    liquidity_adjustment_method: str = "inverse_linear"

    # Rate bounds
    minimum_interest_rate: float = 0.001  # 0.1%
    maximum_interest_rate: float = 0.50   # 50%

    # Update frequencies
    rate_recalculation_interval: int = 3600  # seconds (1 hour)
    emergency_recalculation_interval: int = 300  # seconds (5 minutes)


@dataclass
class IntegrationConfig:
    """Configuration for external integrations"""
    # Blockchain collateral analyzer integration
    collateral_analyzer_enabled: bool = True
    collateral_analyzer_endpoint: str = "http://localhost:8001"
    collateral_analyzer_timeout: int = 30

    # MCP services integration
    mcp_services_enabled: bool = True
    price_oracle_mcp_endpoint: str = "http://localhost:8002"
    market_data_mcp_endpoint: str = "http://localhost:8003"

    # External data sources
    coingecko_api_key: Optional[str] = None
    coinmarketcap_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    # Cache settings
    price_cache_ttl: int = 300  # seconds
    analysis_cache_ttl: int = 1800  # seconds

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    exponential_backoff: bool = True


@dataclass
class CollateralAdjustmentConfig:
    """Main configuration class for collateral adjustment engine"""
    monitoring: CollateralMonitoringConfig
    risk_assessment: RiskAssessmentConfig
    rate_calculation: RateCalculationConfig
    integration: IntegrationConfig

    # Engine settings
    engine_name: str = "collateral_adjustment_engine"
    version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"

    # Performance settings
    max_concurrent_calculations: int = 100
    calculation_timeout: int = 60  # seconds
    memory_limit_mb: int = 512

    # Storage settings
    data_retention_days: int = 90
    backup_enabled: bool = True
    backup_interval_hours: int = 24

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollateralAdjustmentConfig':
        """Create config from dictionary"""
        return cls(
            monitoring=CollateralMonitoringConfig(**data.get('monitoring', {})),
            risk_assessment=RiskAssessmentConfig(**data.get('risk_assessment', {})),
            rate_calculation=RateCalculationConfig(**data.get('rate_calculation', {})),
            integration=IntegrationConfig(**data.get('integration', {})),
            **{k: v for k, v in data.items() if k not in ['monitoring', 'risk_assessment', 'rate_calculation', 'integration']}
        )


def load_config(config_path: Optional[Path] = None) -> CollateralAdjustmentConfig:
    """
    Load configuration from file or return default configuration

    Args:
        config_path: Path to configuration file

    Returns:
        CollateralAdjustmentConfig: Loaded or default configuration
    """
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return CollateralAdjustmentConfig.from_dict(config_data)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            print("Using default configuration")

    # Return default configuration
    return CollateralAdjustmentConfig(
        monitoring=CollateralMonitoringConfig(),
        risk_assessment=RiskAssessmentConfig(),
        rate_calculation=RateCalculationConfig(),
        integration=IntegrationConfig()
    )


def save_config(config: CollateralAdjustmentConfig, config_path: Path) -> None:
    """
    Save configuration to file

    Args:
        config: Configuration to save
        config_path: Path where to save configuration
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)


def create_default_config_file(config_path: Path) -> None:
    """
    Create a default configuration file

    Args:
        config_path: Path where to create the configuration file
    """
    default_config = load_config()
    save_config(default_config, config_path)