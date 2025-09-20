"""
Configuration Management for Base Rate Calculation Engine
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
class FederalReserveRateConfig:
    enabled: bool = True
    weight: float = 0.4
    api_endpoint: str = "https://api.stlouisfed.org/fred/series/observations"
    series_id: str = "FEDFUNDS"
    update_frequency_hours: int = 24
    fallback_rate: float = 0.05


@dataclass
class FederalReserveRatesConfig:
    fed_funds_rate: FederalReserveRateConfig = field(default_factory=FederalReserveRateConfig)
    treasury_10y: FederalReserveRateConfig = field(default_factory=lambda: FederalReserveRateConfig(
        weight=0.3, series_id="GS10", fallback_rate=0.04
    ))
    treasury_3m: FederalReserveRateConfig = field(default_factory=lambda: FederalReserveRateConfig(
        weight=0.2, series_id="GS3M", fallback_rate=0.045
    ))
    sofr_rate: FederalReserveRateConfig = field(default_factory=lambda: FederalReserveRateConfig(
        weight=0.1, series_id="SOFR", fallback_rate=0.048
    ))


@dataclass
class DeFiProtocolConfig:
    enabled: bool = True
    weight: float = 0.35
    protocol_name: str = "Folks Finance"
    api_endpoint: str = "https://api.folks.finance/rates"
    supported_assets: List[str] = field(default_factory=lambda: ["ALGO", "USDC", "USDT", "goBTC", "goETH"])
    rate_types: Dict[str, float] = field(default_factory=lambda: {"lending": 0.8, "borrowing": 0.2})
    fallback_rates: Dict[str, float] = field(default_factory=lambda: {
        "ALGO": 0.06, "USDC": 0.04, "USDT": 0.04, "goBTC": 0.03, "goETH": 0.035
    })


@dataclass
class AlgorandStakingConfig:
    enabled: bool = True
    weight: float = 0.25
    protocol_name: str = "Algorand Consensus"
    base_participation_rewards: float = 0.055
    governance_rewards: float = 0.02
    total_staking_apy: float = 0.075
    minimum_stake_algo: float = 1.0


@dataclass
class AlgorandDeFiRatesConfig:
    folks_finance: DeFiProtocolConfig = field(default_factory=DeFiProtocolConfig)
    algofi: DeFiProtocolConfig = field(default_factory=lambda: DeFiProtocolConfig(
        enabled=False, weight=0.15, protocol_name="Algofi",
        api_endpoint="", fallback_rates={"ALGO": 0.05, "USDC": 0.035, "USDT": 0.035}
    ))
    tinyman: DeFiProtocolConfig = field(default_factory=lambda: DeFiProtocolConfig(
        weight=0.25, protocol_name="Tinyman", api_endpoint="https://api.tinyman.org/v1/pools",
        rate_types={"lp_rewards": 0.6, "farming_rewards": 0.4},
        fallback_rates={"ALGO_USDC": 0.08, "ALGO_USDT": 0.075, "USDC_USDT": 0.03}
    ))
    algorand_staking: AlgorandStakingConfig = field(default_factory=AlgorandStakingConfig)


@dataclass
class RiskFreeRateConfig:
    calculation_method: str = "weighted_average"  # weighted_average, median, min, max
    source_weights: Dict[str, float] = field(default_factory=lambda: {
        "federal_reserve": 0.6, "algorand_staking": 0.3, "defi_protocols": 0.1
    })
    adjustments: Dict[str, float] = field(default_factory=lambda: {
        "liquidity_premium": 0.005, "credit_risk_margin": 0.01,
        "operational_margin": 0.005, "volatility_adjustment": 0.002
    })


@dataclass
class TermStructureConfig:
    curve_model: str = "nelson_siegel"  # nelson_siegel, cubic_spline, linear
    term_premiums: Dict[str, float] = field(default_factory=lambda: {
        "1_day": 0.0, "1_week": 0.001, "1_month": 0.005, "3_months": 0.01,
        "6_months": 0.015, "1_year": 0.02, "2_years": 0.025, "5_years": 0.03
    })
    interpolation_points: List[float] = field(default_factory=lambda: [0.003, 0.019, 0.083, 0.25, 0.5, 1, 2, 5, 10])
    adjustments: Dict[str, float] = field(default_factory=lambda: {
        "inverted_curve_penalty": 0.005, "steep_curve_bonus": -0.002
    })


@dataclass
class DataSourceConfig:
    enabled: bool = True
    reliability_score: float = 0.95
    max_staleness_hours: int = 48
    retry_attempts: int = 3
    timeout_seconds: int = 30


@dataclass
class RateSourcesConfig:
    primary_sources: Dict[str, DataSourceConfig] = field(default_factory=lambda: {
        "federal_reserve_api": DataSourceConfig(),
        "algorand_rpc": DataSourceConfig(reliability_score=0.9, max_staleness_hours=1, retry_attempts=5, timeout_seconds=10),
        "defi_protocol_apis": DataSourceConfig(reliability_score=0.85, max_staleness_hours=6, timeout_seconds=15)
    })
    fallback_sources: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "static_rates": {
            "enabled": True, "use_when": "all_primary_failed",
            "rates": {"base_rate": 0.05, "risk_premium": 0.015}
        },
        "cached_rates": {
            "enabled": True, "max_cache_age_hours": 24, "use_when": "api_unavailable"
        }
    })


@dataclass
class VolatilityAdjustmentConfig:
    rate_adjustment: float
    confidence_boost: float = 0.0


@dataclass
class MarketConditionsConfig:
    volatility_adjustments: Dict[str, VolatilityAdjustmentConfig] = field(default_factory=lambda: {
        "low_volatility": VolatilityAdjustmentConfig(-0.005, 0.1),
        "normal_volatility": VolatilityAdjustmentConfig(0.0, 0.0),
        "high_volatility": VolatilityAdjustmentConfig(0.01, -0.1)
    })
    credit_spread_adjustments: Dict[str, float] = field(default_factory=lambda: {
        "tight_spreads": -0.003, "normal_spreads": 0.0, "wide_spreads": 0.008
    })


@dataclass
class SmoothingConfig:
    enabled: bool = True
    method: str = "exponential_moving_average"  # ema, sma, none
    alpha: float = 0.3
    window: int = 12


@dataclass
class RateBoundsConfig:
    minimum_rate: float = 0.001
    maximum_rate: float = 0.50
    max_daily_change: float = 0.02
    max_hourly_change: float = 0.005


@dataclass
class ConfidenceScoringConfig:
    data_freshness_weight: float = 0.3
    source_reliability_weight: float = 0.4
    rate_stability_weight: float = 0.3
    minimum_confidence: float = 0.7


@dataclass
class CalculationParametersConfig:
    update_frequency_minutes: int = 15
    smoothing: SmoothingConfig = field(default_factory=SmoothingConfig)
    bounds: RateBoundsConfig = field(default_factory=RateBoundsConfig)
    confidence_scoring: ConfidenceScoringConfig = field(default_factory=ConfidenceScoringConfig)


@dataclass
class TrendAnalysisConfig:
    enabled: bool = True
    lookback_days: int = 30
    trend_weight: float = 0.1


@dataclass
class SeasonalAdjustmentsConfig:
    enabled: bool = True
    year_end_premium: float = 0.002
    quarter_end_premium: float = 0.001


@dataclass
class HistoricalAnalysisConfig:
    retention_days: int = 365
    trend_analysis: TrendAnalysisConfig = field(default_factory=TrendAnalysisConfig)
    seasonal_adjustments: SeasonalAdjustmentsConfig = field(default_factory=SeasonalAdjustmentsConfig)


@dataclass
class AlertsConfig:
    rate_change_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "minor_change": 0.005, "major_change": 0.02, "critical_change": 0.05
    })
    data_quality_thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "stale_data_hours": 6, "low_confidence": 0.6, "source_failure_count": 3
    })


@dataclass
class CacheConfig:
    redis_enabled: bool = False
    memory_cache_size_mb: int = 50
    cache_ttl_minutes: int = 30


@dataclass
class APISettingsConfig:
    rate_limits: Dict[str, int] = field(default_factory=lambda: {
        "federal_reserve_api": 120, "defi_apis": 1000, "algorand_rpc": 10000
    })
    cache_settings: CacheConfig = field(default_factory=CacheConfig)


@dataclass
class DevelopmentConfig:
    mock_data_enabled: bool = False
    log_level: str = "INFO"
    log_rate_calculations: bool = True
    log_api_calls: bool = False
    test_scenarios: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "normal_market": {
            "fed_funds_rate": 0.05, "treasury_10y": 0.045, "algo_staking_rate": 0.075,
            "expected_base_rate_range": [0.045, 0.055]
        },
        "crisis_market": {
            "fed_funds_rate": 0.0, "treasury_10y": 0.02, "algo_staking_rate": 0.075,
            "expected_base_rate_range": [0.02, 0.04]
        },
        "high_rate_environment": {
            "fed_funds_rate": 0.08, "treasury_10y": 0.085, "algo_staking_rate": 0.075,
            "expected_base_rate_range": [0.075, 0.09]
        }
    })


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/base_rate_calculation.db"
    max_history_limit: int = 10000
    backup_enabled: bool = True
    backup_frequency_hours: int = 24


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.85
    data_quality_score: float = 0.9
    safety_buffer: float = 0.005
    cache_expiry_minutes: int = 15


@dataclass
class BaseRateCalculationConfig:
    """Complete configuration for the Base Rate Calculation Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    federal_reserve_rates: FederalReserveRatesConfig = field(default_factory=FederalReserveRatesConfig)
    algorand_defi_rates: AlgorandDeFiRatesConfig = field(default_factory=AlgorandDeFiRatesConfig)
    risk_free_rate: RiskFreeRateConfig = field(default_factory=RiskFreeRateConfig)
    term_structure: TermStructureConfig = field(default_factory=TermStructureConfig)
    rate_sources: RateSourcesConfig = field(default_factory=RateSourcesConfig)
    market_conditions: MarketConditionsConfig = field(default_factory=MarketConditionsConfig)
    calculation_parameters: CalculationParametersConfig = field(default_factory=CalculationParametersConfig)
    historical_analysis: HistoricalAnalysisConfig = field(default_factory=HistoricalAnalysisConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    api_settings: APISettingsConfig = field(default_factory=APISettingsConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)


class BaseRateConfigLoader:
    """Loads and manages configuration for the Base Rate Calculation Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> BaseRateCalculationConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            BaseRateCalculationConfig instance
        """
        # Default config
        config = BaseRateCalculationConfig()

        # Try to load from file
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                config = BaseRateConfigLoader._merge_config(config, yaml_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        # Override with environment variables
        config = BaseRateConfigLoader._apply_env_overrides(config)

        return config

    @staticmethod
    def _merge_config(base_config: BaseRateCalculationConfig, yaml_data: Dict[str, Any]) -> BaseRateCalculationConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Federal Reserve rates
        if 'federal_reserve_rates' in yaml_data:
            fed_data = yaml_data['federal_reserve_rates']
            fr_config = FederalReserveRatesConfig()

            for rate_name, rate_config in fed_data.items():
                if hasattr(fr_config, rate_name) and isinstance(rate_config, dict):
                    setattr(fr_config, rate_name, FederalReserveRateConfig(
                        enabled=rate_config.get('enabled', True),
                        weight=rate_config.get('weight', 0.25),
                        api_endpoint=rate_config.get('api_endpoint', ''),
                        series_id=rate_config.get('series_id', ''),
                        update_frequency_hours=rate_config.get('update_frequency_hours', 24),
                        fallback_rate=rate_config.get('fallback_rate', 0.05)
                    ))
            base_config.federal_reserve_rates = fr_config

        # Algorand DeFi rates
        if 'algorand_defi_rates' in yaml_data:
            defi_data = yaml_data['algorand_defi_rates']
            defi_config = AlgorandDeFiRatesConfig()

            for protocol_name, protocol_config in defi_data.items():
                if hasattr(defi_config, protocol_name) and isinstance(protocol_config, dict):
                    if protocol_name == 'algorand_staking':
                        setattr(defi_config, protocol_name, AlgorandStakingConfig(
                            enabled=protocol_config.get('enabled', True),
                            weight=protocol_config.get('weight', 0.25),
                            protocol_name=protocol_config.get('protocol_name', 'Algorand Consensus'),
                            base_participation_rewards=protocol_config.get('base_participation_rewards', 0.055),
                            governance_rewards=protocol_config.get('governance_rewards', 0.02),
                            total_staking_apy=protocol_config.get('total_staking_apy', 0.075),
                            minimum_stake_algo=protocol_config.get('minimum_stake_algo', 1.0)
                        ))
                    else:
                        setattr(defi_config, protocol_name, DeFiProtocolConfig(
                            enabled=protocol_config.get('enabled', True),
                            weight=protocol_config.get('weight', 0.25),
                            protocol_name=protocol_config.get('protocol_name', ''),
                            api_endpoint=protocol_config.get('api_endpoint', ''),
                            supported_assets=protocol_config.get('supported_assets', []),
                            rate_types=protocol_config.get('rate_types', {}),
                            fallback_rates=protocol_config.get('fallback_rates', {})
                        ))
            base_config.algorand_defi_rates = defi_config

        # Risk-free rate configuration
        if 'risk_free_rate' in yaml_data:
            rfr_data = yaml_data['risk_free_rate']
            base_config.risk_free_rate = RiskFreeRateConfig(
                calculation_method=rfr_data.get('calculation_method', 'weighted_average'),
                source_weights=rfr_data.get('source_weights', {}),
                adjustments=rfr_data.get('adjustments', {})
            )

        # Term structure
        if 'term_structure' in yaml_data:
            ts_data = yaml_data['term_structure']
            base_config.term_structure = TermStructureConfig(
                curve_model=ts_data.get('curve_model', 'nelson_siegel'),
                term_premiums=ts_data.get('term_premiums', {}),
                interpolation_points=ts_data.get('interpolation_points', []),
                adjustments=ts_data.get('adjustments', {})
            )

        # Calculation parameters
        if 'calculation_parameters' in yaml_data:
            calc_data = yaml_data['calculation_parameters']
            smoothing_config = SmoothingConfig()
            bounds_config = RateBoundsConfig()
            confidence_config = ConfidenceScoringConfig()

            if 'smoothing' in calc_data:
                smoothing_data = calc_data['smoothing']
                smoothing_config = SmoothingConfig(
                    enabled=smoothing_data.get('enabled', True),
                    method=smoothing_data.get('method', 'exponential_moving_average'),
                    alpha=smoothing_data.get('alpha', 0.3),
                    window=smoothing_data.get('window', 12)
                )

            if 'bounds' in calc_data:
                bounds_data = calc_data['bounds']
                bounds_config = RateBoundsConfig(
                    minimum_rate=bounds_data.get('minimum_rate', 0.001),
                    maximum_rate=bounds_data.get('maximum_rate', 0.50),
                    max_daily_change=bounds_data.get('max_daily_change', 0.02),
                    max_hourly_change=bounds_data.get('max_hourly_change', 0.005)
                )

            if 'confidence_scoring' in calc_data:
                conf_data = calc_data['confidence_scoring']
                confidence_config = ConfidenceScoringConfig(
                    data_freshness_weight=conf_data.get('data_freshness_weight', 0.3),
                    source_reliability_weight=conf_data.get('source_reliability_weight', 0.4),
                    rate_stability_weight=conf_data.get('rate_stability_weight', 0.3),
                    minimum_confidence=conf_data.get('minimum_confidence', 0.7)
                )

            base_config.calculation_parameters = CalculationParametersConfig(
                update_frequency_minutes=calc_data.get('update_frequency_minutes', 15),
                smoothing=smoothing_config,
                bounds=bounds_config,
                confidence_scoring=confidence_config
            )

        # Database config
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                default_path=db_data.get('default_path', 'notebooks/base_rate_calculation.db'),
                max_history_limit=db_data.get('max_history_limit', 10000),
                backup_enabled=db_data.get('backup_enabled', True),
                backup_frequency_hours=db_data.get('backup_frequency_hours', 24)
            )

        # Analysis config
        if 'analysis' in yaml_data:
            analysis_data = yaml_data['analysis']
            base_config.analysis = AnalysisConfig(
                default_confidence_score=analysis_data.get('default_confidence_score', 0.85),
                data_quality_score=analysis_data.get('data_quality_score', 0.9),
                safety_buffer=analysis_data.get('safety_buffer', 0.005),
                cache_expiry_minutes=analysis_data.get('cache_expiry_minutes', 15)
            )

        return base_config

    @staticmethod
    def _apply_env_overrides(config: BaseRateCalculationConfig) -> BaseRateCalculationConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'BASE_RATE_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['BASE_RATE_MCP_READER_URL']

        if 'BASE_RATE_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['BASE_RATE_MCP_MARKET_URL']

        # Database path
        if 'BASE_RATE_DB_PATH' in os.environ:
            config.database.default_path = os.environ['BASE_RATE_DB_PATH']

        # Federal Reserve API key
        if 'FRED_API_KEY' in os.environ:
            api_key = os.environ['FRED_API_KEY']
            # Update all Fed endpoints with API key
            for rate_config in [config.federal_reserve_rates.fed_funds_rate,
                              config.federal_reserve_rates.treasury_10y,
                              config.federal_reserve_rates.treasury_3m,
                              config.federal_reserve_rates.sofr_rate]:
                if rate_config.api_endpoint:
                    rate_config.api_endpoint += f"&api_key={api_key}"

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> BaseRateCalculationConfig:
    """Load configuration - convenience function"""
    return BaseRateConfigLoader.load_config(config_path)