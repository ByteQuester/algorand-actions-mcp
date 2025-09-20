"""
Configuration Management for Collateral Requirements Engine
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MCPServiceConfig:
    algorand_reader_url: str = "http://localhost:8002"
    market_data_url: str = "http://localhost:8003"


@dataclass
class CollateralRatioConfig:
    algo_native: float = 1.50
    stablecoin: float = 1.10
    asa_token: float = 2.00
    governance_token: float = 2.50
    lp_token: float = 3.00
    liquid_staking: float = 1.75


@dataclass
class VolatilityAdjustmentConfig:
    low: float = 1.0
    medium: float = 1.15
    high: float = 1.30
    extreme: float = 1.50


@dataclass
class LiquidityAdjustmentConfig:
    high: float = 1.0
    medium: float = 1.10
    low: float = 1.25


@dataclass
class MarketConditionsConfig:
    bull: float = 0.9
    normal: float = 1.0
    bear: float = 1.15
    volatile: float = 1.25


@dataclass
class LiquidationConfig:
    price_drops: list = field(default_factory=lambda: [0.1, 0.2, 0.3, 0.5])
    scenario_names: list = field(default_factory=lambda: ["Minor Correction", "Market Dip", "Bear Market", "Black Swan"])
    base_slippage: float = 0.05
    gas_costs_usd: float = 50


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.8
    data_quality_score: float = 0.85
    safety_buffer: float = 0.1
    max_position_concentration: float = 0.7
    diversification_bonus_factor: float = 0.1
    cache_expiry_minutes: int = 5


@dataclass
class RiskThresholdConfig:
    low_volatility: float = 0.3
    high_diversification: float = 0.5
    adequate_collateral_ratio: float = 0.8
    marginal_collateral_ratio: float = 0.6


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/collateral_analysis.db"
    max_history_limit: int = 100


@dataclass
class CollateralEngineConfig:
    """Complete configuration for the Collateral Requirements Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    base_collateral_ratios: CollateralRatioConfig = field(default_factory=CollateralRatioConfig)
    volatility_adjustments: VolatilityAdjustmentConfig = field(default_factory=VolatilityAdjustmentConfig)
    liquidity_adjustments: LiquidityAdjustmentConfig = field(default_factory=LiquidityAdjustmentConfig)
    market_conditions_adjustments: MarketConditionsConfig = field(default_factory=MarketConditionsConfig)
    liquidation_scenarios: LiquidationConfig = field(default_factory=LiquidationConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    risk_thresholds: RiskThresholdConfig = field(default_factory=RiskThresholdConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Asset data
    fallback_prices: Dict[str, float] = field(default_factory=lambda: {
        'USDC': 1.00,
        'USDT': 1.00,
        'goBTC': 45000.0,
        'goETH': 3000.0,
        'ALGO': 0.25
    })

    volatility_estimates: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'ALGO': {
            'volatility_30d': 0.45,
            'volatility_7d': 0.35,
            'max_drawdown_30d': 0.25,
            'value_at_risk_95': 0.15
        },
        'USDC': {
            'volatility_30d': 0.02,
            'volatility_7d': 0.01,
            'max_drawdown_30d': 0.01,
            'value_at_risk_95': 0.005
        },
        'default': {
            'volatility_30d': 0.60,
            'volatility_7d': 0.50,
            'max_drawdown_30d': 0.40,
            'value_at_risk_95': 0.25
        }
    })

    liquidity_estimates: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'ALGO': {
            'daily_volume_usd': 50_000_000,
            'market_cap_usd': 2_000_000_000,
            'liquidity_tier': 'high'
        },
        'USDC': {
            'daily_volume_usd': 5_000_000,
            'market_cap_usd': 500_000_000,
            'liquidity_tier': 'high'
        },
        'default': {
            'daily_volume_usd': 100_000,
            'market_cap_usd': 10_000_000,
            'liquidity_tier': 'medium'
        }
    })

    asset_classification: Dict[str, list] = field(default_factory=lambda: {
        'stablecoins': ['USDC', 'USDT', 'STBL'],
        'lp_patterns': ['LP', 'POOL'],
        'governance_patterns': ['VOTE', 'GOV', 'DAO'],
        'liquid_staking_patterns': ['STAKE', 'LIQUID']
    })


class ConfigLoader:
    """Loads and manages configuration for the Collateral Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> CollateralEngineConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            CollateralEngineConfig instance
        """
        # Default config
        config = CollateralEngineConfig()

        # Try to load from file
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                config = ConfigLoader._merge_config(config, yaml_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        # Override with environment variables
        config = ConfigLoader._apply_env_overrides(config)

        return config

    @staticmethod
    def _merge_config(base_config: CollateralEngineConfig, yaml_data: Dict[str, Any]) -> CollateralEngineConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Base collateral ratios
        if 'base_collateral_ratios' in yaml_data:
            ratios_data = yaml_data['base_collateral_ratios']
            base_config.base_collateral_ratios = CollateralRatioConfig(
                algo_native=ratios_data.get('algo_native', base_config.base_collateral_ratios.algo_native),
                stablecoin=ratios_data.get('stablecoin', base_config.base_collateral_ratios.stablecoin),
                asa_token=ratios_data.get('asa_token', base_config.base_collateral_ratios.asa_token),
                governance_token=ratios_data.get('governance_token', base_config.base_collateral_ratios.governance_token),
                lp_token=ratios_data.get('lp_token', base_config.base_collateral_ratios.lp_token),
                liquid_staking=ratios_data.get('liquid_staking', base_config.base_collateral_ratios.liquid_staking)
            )

        # Volatility adjustments
        if 'volatility_adjustments' in yaml_data:
            vol_data = yaml_data['volatility_adjustments']
            base_config.volatility_adjustments = VolatilityAdjustmentConfig(
                low=vol_data.get('low', base_config.volatility_adjustments.low),
                medium=vol_data.get('medium', base_config.volatility_adjustments.medium),
                high=vol_data.get('high', base_config.volatility_adjustments.high),
                extreme=vol_data.get('extreme', base_config.volatility_adjustments.extreme)
            )

        # Liquidity adjustments
        if 'liquidity_adjustments' in yaml_data:
            liq_data = yaml_data['liquidity_adjustments']
            base_config.liquidity_adjustments = LiquidityAdjustmentConfig(
                high=liq_data.get('high', base_config.liquidity_adjustments.high),
                medium=liq_data.get('medium', base_config.liquidity_adjustments.medium),
                low=liq_data.get('low', base_config.liquidity_adjustments.low)
            )

        # Market conditions
        if 'market_conditions_adjustments' in yaml_data:
            market_data = yaml_data['market_conditions_adjustments']
            base_config.market_conditions_adjustments = MarketConditionsConfig(
                bull=market_data.get('bull', base_config.market_conditions_adjustments.bull),
                normal=market_data.get('normal', base_config.market_conditions_adjustments.normal),
                bear=market_data.get('bear', base_config.market_conditions_adjustments.bear),
                volatile=market_data.get('volatile', base_config.market_conditions_adjustments.volatile)
            )

        # Liquidation scenarios
        if 'liquidation_scenarios' in yaml_data:
            liq_data = yaml_data['liquidation_scenarios']
            base_config.liquidation_scenarios = LiquidationConfig(
                price_drops=liq_data.get('price_drops', base_config.liquidation_scenarios.price_drops),
                scenario_names=liq_data.get('scenario_names', base_config.liquidation_scenarios.scenario_names),
                base_slippage=liq_data.get('base_slippage', base_config.liquidation_scenarios.base_slippage),
                gas_costs_usd=liq_data.get('gas_costs_usd', base_config.liquidation_scenarios.gas_costs_usd)
            )

        # Analysis parameters
        if 'analysis' in yaml_data:
            analysis_data = yaml_data['analysis']
            base_config.analysis = AnalysisConfig(
                default_confidence_score=analysis_data.get('default_confidence_score', base_config.analysis.default_confidence_score),
                data_quality_score=analysis_data.get('data_quality_score', base_config.analysis.data_quality_score),
                safety_buffer=analysis_data.get('safety_buffer', base_config.analysis.safety_buffer),
                max_position_concentration=analysis_data.get('max_position_concentration', base_config.analysis.max_position_concentration),
                diversification_bonus_factor=analysis_data.get('diversification_bonus_factor', base_config.analysis.diversification_bonus_factor),
                cache_expiry_minutes=analysis_data.get('cache_expiry_minutes', base_config.analysis.cache_expiry_minutes)
            )

        # Risk thresholds
        if 'risk_thresholds' in yaml_data:
            risk_data = yaml_data['risk_thresholds']
            base_config.risk_thresholds = RiskThresholdConfig(
                low_volatility=risk_data.get('low_volatility', base_config.risk_thresholds.low_volatility),
                high_diversification=risk_data.get('high_diversification', base_config.risk_thresholds.high_diversification),
                adequate_collateral_ratio=risk_data.get('adequate_collateral_ratio', base_config.risk_thresholds.adequate_collateral_ratio),
                marginal_collateral_ratio=risk_data.get('marginal_collateral_ratio', base_config.risk_thresholds.marginal_collateral_ratio)
            )

        # Database config
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                default_path=db_data.get('default_path', base_config.database.default_path),
                max_history_limit=db_data.get('max_history_limit', base_config.database.max_history_limit)
            )

        # Direct data mappings
        for key in ['fallback_prices', 'volatility_estimates', 'liquidity_estimates', 'asset_classification']:
            if key in yaml_data:
                setattr(base_config, key, yaml_data[key])

        return base_config

    @staticmethod
    def _apply_env_overrides(config: CollateralEngineConfig) -> CollateralEngineConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'COLLATERAL_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['COLLATERAL_MCP_READER_URL']

        if 'COLLATERAL_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['COLLATERAL_MCP_MARKET_URL']

        # Database path
        if 'COLLATERAL_DB_PATH' in os.environ:
            config.database.default_path = os.environ['COLLATERAL_DB_PATH']

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> CollateralEngineConfig:
    """Load configuration - convenience function"""
    return ConfigLoader.load_config(config_path)