"""
Configuration Management for Digital Asset Valuation Engine
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class MCPServiceConfig:
    algorand_reader_url: str = "http://localhost:8002"
    market_data_url: str = "http://localhost:8003"


@dataclass
class CollateralRatioConfig:
    algo_native: float = 1.5
    stablecoin: float = 1.1
    asa_token: float = 2.0
    governance_token: float = 2.5
    lp_token: float = 3.0
    liquid_staking: float = 1.8


@dataclass
class MaintenanceRatioConfig:
    algo_native: float = 1.25
    stablecoin: float = 1.05
    asa_token: float = 1.5
    governance_token: float = 1.8
    lp_token: float = 2.0
    liquid_staking: float = 1.4


@dataclass
class LiquidationPenaltyConfig:
    algo_native: float = 0.05
    stablecoin: float = 0.02
    asa_token: float = 0.08
    governance_token: float = 0.12
    lp_token: float = 0.15
    liquid_staking: float = 0.06


@dataclass
class HaircutConfig:
    algo_native: float = 0.05
    stablecoin: float = 0.01
    asa_token: float = 0.15
    governance_token: float = 0.25
    lp_token: float = 0.30
    liquid_staking: float = 0.08


@dataclass
class RiskParameterConfig:
    max_volatility_30d: float
    min_liquidity_tier: str
    max_correlation: float
    min_market_cap: int


@dataclass
class LiquidationThresholdConfig:
    warning_threshold: float = 1.1
    urgent_threshold: float = 1.05
    auto_liquidation: float = 1.02
    max_liquidation_time: int = 24
    preferred_liquidation_time: int = 4


@dataclass
class OracleConfig:
    primary_oracle: str = "algorand_native"
    backup_oracles: List[str] = field(default_factory=lambda: ["chainlink", "pyth", "dia"])
    update_frequency: int = 60
    reliability_threshold: float = 0.95
    max_price_deviation: float = 0.05
    fallback_strategy: str = "median_of_three"


@dataclass
class DiversificationTargetConfig:
    single_asset_max: float = 0.4
    asset_type_max: float = 0.6
    min_asset_count: int = 3
    correlation_limit: float = 0.7
    liquidity_reserve: float = 0.1


@dataclass
class MarketConditionMultiplierConfig:
    collateral_ratio_adjustment: float
    liquidation_buffer: float


@dataclass
class LiquidityTierAdjustmentConfig:
    high: float = 0.0
    medium: float = 0.02
    low: float = 0.05


@dataclass
class MarketConditionAdjustmentConfig:
    bull: float = -0.02
    normal: float = 0.0
    bear: float = 0.05
    crisis: float = 0.15


@dataclass
class VolatilityParameterConfig:
    max_volatility_adjustment: float = 0.2
    volatility_multiplier: float = 0.5


@dataclass
class ValuationMethodConfig:
    oracle_weight: float = 0.7
    market_weight: float = 0.2
    fallback_weight: float = 0.1


@dataclass
class PriceFeedConfig:
    update_interval_seconds: int = 30
    max_staleness_seconds: int = 300
    price_deviation_threshold: float = 0.1


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.8
    data_quality_score: float = 0.85
    safety_buffer: float = 0.1
    max_position_concentration: float = 0.6
    diversification_bonus_factor: float = 0.05
    cache_expiry_minutes: int = 5


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/digital_asset_valuation.db"
    max_history_limit: int = 1000


@dataclass
class DigitalAssetValuationConfig:
    """Complete configuration for the Digital Asset Valuation Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    default_collateral_ratios: CollateralRatioConfig = field(default_factory=CollateralRatioConfig)
    maintenance_ratios: MaintenanceRatioConfig = field(default_factory=MaintenanceRatioConfig)
    liquidation_penalties: LiquidationPenaltyConfig = field(default_factory=LiquidationPenaltyConfig)
    default_haircuts: HaircutConfig = field(default_factory=HaircutConfig)
    liquidation_thresholds: LiquidationThresholdConfig = field(default_factory=LiquidationThresholdConfig)
    oracle_config: OracleConfig = field(default_factory=OracleConfig)
    diversification_targets: DiversificationTargetConfig = field(default_factory=DiversificationTargetConfig)
    liquidity_tier_adjustments: LiquidityTierAdjustmentConfig = field(default_factory=LiquidityTierAdjustmentConfig)
    market_condition_adjustments: MarketConditionAdjustmentConfig = field(default_factory=MarketConditionAdjustmentConfig)
    volatility_parameters: VolatilityParameterConfig = field(default_factory=VolatilityParameterConfig)
    valuation_methods: ValuationMethodConfig = field(default_factory=ValuationMethodConfig)
    price_feeds: PriceFeedConfig = field(default_factory=PriceFeedConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Complex configuration objects
    risk_parameters: Dict[str, RiskParameterConfig] = field(default_factory=lambda: {
        'conservative': RiskParameterConfig(0.3, 'medium', 0.7, 100_000_000),
        'moderate': RiskParameterConfig(0.5, 'low', 0.8, 50_000_000),
        'aggressive': RiskParameterConfig(0.8, 'low', 0.9, 10_000_000)
    })

    market_condition_multipliers: Dict[str, MarketConditionMultiplierConfig] = field(default_factory=lambda: {
        'bull_market': MarketConditionMultiplierConfig(-0.1, 0.02),
        'bear_market': MarketConditionMultiplierConfig(0.2, 0.05),
        'high_volatility': MarketConditionMultiplierConfig(0.15, 0.03),
        'low_volatility': MarketConditionMultiplierConfig(-0.05, 0.01)
    })

    # Asset data
    algorand_assets: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'ALGO': {
            'name': 'Algorand',
            'type': 'algo_native',
            'asset_id': '0',
            'decimals': 6,
            'is_native': True,
            'typical_volatility': 0.4,
            'liquidity_tier': 'high'
        },
        'USDC': {
            'name': 'USD Coin',
            'type': 'stablecoin',
            'asset_id': '31566704',
            'decimals': 6,
            'is_native': False,
            'typical_volatility': 0.02,
            'liquidity_tier': 'high'
        },
        'USDT': {
            'name': 'Tether USD',
            'type': 'stablecoin',
            'asset_id': '312769',
            'decimals': 6,
            'is_native': False,
            'typical_volatility': 0.02,
            'liquidity_tier': 'high'
        },
        'GOBTC': {
            'name': 'GoETH Bitcoin',
            'type': 'asa_token',
            'asset_id': '386192725',
            'decimals': 8,
            'is_native': False,
            'typical_volatility': 0.6,
            'liquidity_tier': 'medium'
        }
    })

    stress_test_scenarios: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'market_crash': {
            'description': 'Market-wide 50% drop',
            'algo_impact': -0.5,
            'correlation_increase': 0.3,
            'liquidity_reduction': 0.5
        },
        'regulatory_shock': {
            'description': 'Regulatory crackdown',
            'algo_impact': -0.3,
            'correlation_increase': 0.2,
            'liquidity_reduction': 0.7
        },
        'technical_failure': {
            'description': 'Network or protocol failure',
            'algo_impact': -0.4,
            'correlation_increase': 0.4,
            'liquidity_reduction': 0.8
        },
        'liquidity_crisis': {
            'description': 'Market liquidity dries up',
            'algo_impact': -0.2,
            'correlation_increase': 0.1,
            'liquidity_reduction': 0.9
        }
    })

    fallback_prices: Dict[str, float] = field(default_factory=lambda: {
        'USDC': 1.00,
        'USDT': 1.00,
        'ALGO': 0.25,
        'goBTC': 45000.0,
        'goETH': 3000.0
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


class DigitalAssetConfigLoader:
    """Loads and manages configuration for the Digital Asset Valuation Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> DigitalAssetValuationConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            DigitalAssetValuationConfig instance
        """
        # Default config
        config = DigitalAssetValuationConfig()

        # Try to load from file
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                config = DigitalAssetConfigLoader._merge_config(config, yaml_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        # Override with environment variables
        config = DigitalAssetConfigLoader._apply_env_overrides(config)

        return config

    @staticmethod
    def _merge_config(base_config: DigitalAssetValuationConfig, yaml_data: Dict[str, Any]) -> DigitalAssetValuationConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Default collateral ratios
        if 'default_collateral_ratios' in yaml_data:
            ratios_data = yaml_data['default_collateral_ratios']
            base_config.default_collateral_ratios = CollateralRatioConfig(
                algo_native=ratios_data.get('algo_native', base_config.default_collateral_ratios.algo_native),
                stablecoin=ratios_data.get('stablecoin', base_config.default_collateral_ratios.stablecoin),
                asa_token=ratios_data.get('asa_token', base_config.default_collateral_ratios.asa_token),
                governance_token=ratios_data.get('governance_token', base_config.default_collateral_ratios.governance_token),
                lp_token=ratios_data.get('lp_token', base_config.default_collateral_ratios.lp_token),
                liquid_staking=ratios_data.get('liquid_staking', base_config.default_collateral_ratios.liquid_staking)
            )

        # Maintenance ratios
        if 'maintenance_ratios' in yaml_data:
            maint_data = yaml_data['maintenance_ratios']
            base_config.maintenance_ratios = MaintenanceRatioConfig(
                algo_native=maint_data.get('algo_native', base_config.maintenance_ratios.algo_native),
                stablecoin=maint_data.get('stablecoin', base_config.maintenance_ratios.stablecoin),
                asa_token=maint_data.get('asa_token', base_config.maintenance_ratios.asa_token),
                governance_token=maint_data.get('governance_token', base_config.maintenance_ratios.governance_token),
                lp_token=maint_data.get('lp_token', base_config.maintenance_ratios.lp_token),
                liquid_staking=maint_data.get('liquid_staking', base_config.maintenance_ratios.liquid_staking)
            )

        # Liquidation penalties
        if 'liquidation_penalties' in yaml_data:
            liq_data = yaml_data['liquidation_penalties']
            base_config.liquidation_penalties = LiquidationPenaltyConfig(
                algo_native=liq_data.get('algo_native', base_config.liquidation_penalties.algo_native),
                stablecoin=liq_data.get('stablecoin', base_config.liquidation_penalties.stablecoin),
                asa_token=liq_data.get('asa_token', base_config.liquidation_penalties.asa_token),
                governance_token=liq_data.get('governance_token', base_config.liquidation_penalties.governance_token),
                lp_token=liq_data.get('lp_token', base_config.liquidation_penalties.lp_token),
                liquid_staking=liq_data.get('liquid_staking', base_config.liquidation_penalties.liquid_staking)
            )

        # Default haircuts
        if 'default_haircuts' in yaml_data:
            haircut_data = yaml_data['default_haircuts']
            base_config.default_haircuts = HaircutConfig(
                algo_native=haircut_data.get('algo_native', base_config.default_haircuts.algo_native),
                stablecoin=haircut_data.get('stablecoin', base_config.default_haircuts.stablecoin),
                asa_token=haircut_data.get('asa_token', base_config.default_haircuts.asa_token),
                governance_token=haircut_data.get('governance_token', base_config.default_haircuts.governance_token),
                lp_token=haircut_data.get('lp_token', base_config.default_haircuts.lp_token),
                liquid_staking=haircut_data.get('liquid_staking', base_config.default_haircuts.liquid_staking)
            )

        # Risk parameters
        if 'risk_parameters' in yaml_data:
            risk_data = yaml_data['risk_parameters']
            for risk_level, params in risk_data.items():
                base_config.risk_parameters[risk_level] = RiskParameterConfig(
                    max_volatility_30d=params.get('max_volatility_30d', 0.5),
                    min_liquidity_tier=params.get('min_liquidity_tier', 'medium'),
                    max_correlation=params.get('max_correlation', 0.8),
                    min_market_cap=params.get('min_market_cap', 50_000_000)
                )

        # Liquidation thresholds
        if 'liquidation_thresholds' in yaml_data:
            liq_thresh_data = yaml_data['liquidation_thresholds']
            base_config.liquidation_thresholds = LiquidationThresholdConfig(
                warning_threshold=liq_thresh_data.get('warning_threshold', base_config.liquidation_thresholds.warning_threshold),
                urgent_threshold=liq_thresh_data.get('urgent_threshold', base_config.liquidation_thresholds.urgent_threshold),
                auto_liquidation=liq_thresh_data.get('auto_liquidation', base_config.liquidation_thresholds.auto_liquidation),
                max_liquidation_time=liq_thresh_data.get('max_liquidation_time', base_config.liquidation_thresholds.max_liquidation_time),
                preferred_liquidation_time=liq_thresh_data.get('preferred_liquidation_time', base_config.liquidation_thresholds.preferred_liquidation_time)
            )

        # Oracle config
        if 'oracle_config' in yaml_data:
            oracle_data = yaml_data['oracle_config']
            base_config.oracle_config = OracleConfig(
                primary_oracle=oracle_data.get('primary_oracle', base_config.oracle_config.primary_oracle),
                backup_oracles=oracle_data.get('backup_oracles', base_config.oracle_config.backup_oracles),
                update_frequency=oracle_data.get('update_frequency', base_config.oracle_config.update_frequency),
                reliability_threshold=oracle_data.get('reliability_threshold', base_config.oracle_config.reliability_threshold),
                max_price_deviation=oracle_data.get('max_price_deviation', base_config.oracle_config.max_price_deviation),
                fallback_strategy=oracle_data.get('fallback_strategy', base_config.oracle_config.fallback_strategy)
            )

        # Market condition multipliers
        if 'market_condition_multipliers' in yaml_data:
            mult_data = yaml_data['market_condition_multipliers']
            for condition, multiplier in mult_data.items():
                base_config.market_condition_multipliers[condition] = MarketConditionMultiplierConfig(
                    collateral_ratio_adjustment=multiplier.get('collateral_ratio_adjustment', 0.0),
                    liquidation_buffer=multiplier.get('liquidation_buffer', 0.0)
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

        # Database config
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                default_path=db_data.get('default_path', base_config.database.default_path),
                max_history_limit=db_data.get('max_history_limit', base_config.database.max_history_limit)
            )

        # Direct data mappings
        for key in ['algorand_assets', 'stress_test_scenarios', 'fallback_prices',
                   'volatility_estimates', 'liquidity_estimates']:
            if key in yaml_data:
                setattr(base_config, key, yaml_data[key])

        return base_config

    @staticmethod
    def _apply_env_overrides(config: DigitalAssetValuationConfig) -> DigitalAssetValuationConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'DIGITAL_ASSET_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['DIGITAL_ASSET_MCP_READER_URL']

        if 'DIGITAL_ASSET_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['DIGITAL_ASSET_MCP_MARKET_URL']

        # Database path
        if 'DIGITAL_ASSET_DB_PATH' in os.environ:
            config.database.default_path = os.environ['DIGITAL_ASSET_DB_PATH']

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> DigitalAssetValuationConfig:
    """Load configuration - convenience function"""
    return DigitalAssetConfigLoader.load_config(config_path)