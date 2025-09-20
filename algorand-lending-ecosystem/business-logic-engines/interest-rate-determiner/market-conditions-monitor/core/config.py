"""
Configuration Management for Market Conditions Monitor Engine
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
class VolatilityThresholdsConfig:
    low_volatility: float = 0.15
    normal_volatility: float = 0.30
    high_volatility: float = 0.50
    extreme_volatility: float = 0.75


@dataclass
class TimeWindowsConfig:
    intraday: int = 24      # hours
    short_term: int = 168   # hours (1 week)
    medium_term: int = 720  # hours (30 days)
    long_term: int = 2160   # hours (90 days)


@dataclass
class VolatilityMonitoringConfig:
    calculation_methods: List[str] = field(default_factory=lambda: [
        "realized_volatility", "garch_volatility", "exponential_smoothing", "parkinson_estimator"
    ])
    time_windows: TimeWindowsConfig = field(default_factory=TimeWindowsConfig)
    thresholds: VolatilityThresholdsConfig = field(default_factory=VolatilityThresholdsConfig)
    monitored_assets: Dict[str, List[str]] = field(default_factory=lambda: {
        "algorand_native": ["ALGO"],
        "crypto_majors": ["BTC", "ETH"],
        "stablecoins": ["USDC", "USDT", "DAI"],
        "algorand_ecosystem": ["goBTC", "goETH", "PLANET", "OPUL"]
    })


@dataclass
class NetworkMetricConfig:
    enabled: bool = True
    threshold_low: Optional[int] = None
    threshold_high: Optional[int] = None
    update_frequency_minutes: int = 5
    target_block_time: Optional[float] = None
    acceptable_deviation: Optional[float] = None
    alert_threshold: Optional[float] = None
    target_finality: Optional[float] = None
    minimum_participation: Optional[float] = None
    healthy_participation: Optional[float] = None


@dataclass
class DeFiProtocolConfig:
    enabled: bool = True
    health_endpoints: List[str] = field(default_factory=list)
    key_metrics: List[str] = field(default_factory=list)
    alert_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class AlgorandEcosystemConfig:
    network_metrics: Dict[str, NetworkMetricConfig] = field(default_factory=lambda: {
        "transaction_throughput": NetworkMetricConfig(threshold_low=1000, threshold_high=5000),
        "block_time_consistency": NetworkMetricConfig(
            target_block_time=3.3, acceptable_deviation=0.5, alert_threshold=1.0
        ),
        "finality_time": NetworkMetricConfig(target_finality=4.5, alert_threshold=10.0),
        "network_participation": NetworkMetricConfig(
            minimum_participation=0.70, healthy_participation=0.85
        )
    })
    defi_protocols: Dict[str, DeFiProtocolConfig] = field(default_factory=lambda: {
        "folks_finance": DeFiProtocolConfig(
            health_endpoints=["https://api.folks.finance/health"],
            key_metrics=["total_value_locked", "lending_utilization", "borrowing_demand"],
            alert_thresholds={"tvl_drop_percent": 0.20, "utilization_high": 0.90, "utilization_low": 0.10}
        ),
        "tinyman": DeFiProtocolConfig(
            health_endpoints=["https://api.tinyman.org/v1/status"],
            key_metrics=["total_liquidity", "trading_volume_24h", "active_pools"],
            alert_thresholds={"liquidity_drop_percent": 0.25, "volume_drop_percent": 0.40}
        ),
        "pact": DeFiProtocolConfig(
            key_metrics=["trading_pairs", "liquidity_depth"],
            alert_thresholds={"liquidity_drop_percent": 0.30}
        )
    })


@dataclass
class MarketIndexConfig:
    symbol: str
    name: str
    weight: float


@dataclass
class CorrelationCalculationConfig:
    correlation_windows: Dict[str, int] = field(default_factory=lambda: {
        "short_term": 30, "medium_term": 90, "long_term": 252
    })
    significance_threshold: float = 0.05
    high_correlation_threshold: float = 0.7
    low_correlation_threshold: float = 0.3
    update_frequency_hours: int = 6


@dataclass
class CorrelationAnalysisConfig:
    traditional_indices: Dict[str, List[MarketIndexConfig]] = field(default_factory=lambda: {
        "us_equity": [
            MarketIndexConfig("SPY", "S&P 500 ETF", 0.4),
            MarketIndexConfig("QQQ", "NASDAQ ETF", 0.3),
            MarketIndexConfig("IWM", "Russell 2000 ETF", 0.3)
        ],
        "bonds": [
            MarketIndexConfig("TLT", "Long Treasury ETF", 0.6),
            MarketIndexConfig("HYG", "High Yield ETF", 0.4)
        ],
        "commodities": [
            MarketIndexConfig("GLD", "Gold ETF", 0.5),
            MarketIndexConfig("DBC", "Commodities ETF", 0.5)
        ]
    })
    crypto_indices: Dict[str, List[MarketIndexConfig]] = field(default_factory=lambda: {
        "major_crypto": [
            MarketIndexConfig("BTC", "Bitcoin", 0.6),
            MarketIndexConfig("ETH", "Ethereum", 0.4)
        ],
        "defi_tokens": [
            MarketIndexConfig("UNI", "Uniswap", 0.25),
            MarketIndexConfig("AAVE", "Aave", 0.25),
            MarketIndexConfig("COMP", "Compound", 0.25),
            MarketIndexConfig("MKR", "Maker", 0.25)
        ]
    })
    calculation_parameters: CorrelationCalculationConfig = field(default_factory=CorrelationCalculationConfig)


@dataclass
class VolatilityIndexConfig:
    symbol: str
    thresholds: Dict[str, float]
    weight: float


@dataclass
class CreditIndicatorConfig:
    symbol: str
    treasury_benchmark: str
    thresholds: Dict[str, float]
    weight: float


@dataclass
class LiquidityIndicatorConfig:
    enabled: bool = True
    assets_to_monitor: List[str] = field(default_factory=lambda: ["ALGO", "BTC", "ETH", "USDC"])
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "normal_spread_bps": 10, "elevated_spread_bps": 50, "wide_spread_bps": 100
    })
    lookback_days: Optional[int] = None
    volume_drop_threshold: Optional[float] = None
    volume_spike_threshold: Optional[float] = None


@dataclass
class StressIndicatorsConfig:
    volatility_indices: Dict[str, VolatilityIndexConfig] = field(default_factory=lambda: {
        "vix": VolatilityIndexConfig(
            symbol="VIX",
            thresholds={"low_fear": 15, "normal": 25, "elevated": 35, "panic": 50},
            weight=0.4
        ),
        "crypto_fear_greed": VolatilityIndexConfig(
            symbol="FNG",
            thresholds={"extreme_greed": 75, "greed": 55, "neutral": 45, "fear": 25, "extreme_fear": 10},
            weight=0.3
        )
    })
    credit_indicators: Dict[str, CreditIndicatorConfig] = field(default_factory=lambda: {
        "investment_grade_spreads": CreditIndicatorConfig(
            symbol="LQD", treasury_benchmark="TLT",
            thresholds={"tight": 100, "normal": 200, "wide": 300, "stressed": 500},
            weight=0.2
        ),
        "high_yield_spreads": CreditIndicatorConfig(
            symbol="HYG", treasury_benchmark="TLT",
            thresholds={"tight": 300, "normal": 500, "wide": 800, "distressed": 1200},
            weight=0.3
        )
    })
    liquidity_indicators: Dict[str, LiquidityIndicatorConfig] = field(default_factory=lambda: {
        "bid_ask_spreads": LiquidityIndicatorConfig(),
        "trading_volume": LiquidityIndicatorConfig(
            lookback_days=30, volume_drop_threshold=0.30, volume_spike_threshold=2.0
        )
    })


@dataclass
class TrendBasedConfig:
    enabled: bool = True
    lookback_periods: Dict[str, int] = field(default_factory=lambda: {
        "short_term": 30, "medium_term": 90, "long_term": 252
    })
    trend_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "bull_market": 0.15, "bear_market": -0.15, "sideways_threshold": 0.05
    })
    weight: float = 0.4


@dataclass
class VolatilityBasedConfig:
    enabled: bool = True
    regime_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "low_vol_regime": 0.15, "normal_vol_regime": 0.30, "high_vol_regime": 0.50
    })
    weight: float = 0.3


@dataclass
class MomentumBasedConfig:
    enabled: bool = True
    momentum_periods: List[int] = field(default_factory=lambda: [20, 50, 200])
    momentum_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "strong_momentum": 0.10, "weak_momentum": 0.02
    })
    weight: float = 0.3


@dataclass
class CrisisDetectionConfig:
    enabled: bool = True
    crisis_indicators: Dict[str, float] = field(default_factory=lambda: {
        "price_drop_threshold": 0.20, "volatility_spike_threshold": 2.0,
        "correlation_spike_threshold": 0.8, "volume_spike_threshold": 3.0
    })
    crisis_duration_hours: int = 72
    recovery_threshold: float = 0.10


@dataclass
class RegimeSmoothingConfig:
    enabled: bool = True
    minimum_regime_duration_days: int = 5
    regime_change_threshold: float = 0.7


@dataclass
class RegimeDetectionConfig:
    classification_methods: Dict[str, Any] = field(default_factory=lambda: {
        "trend_based": TrendBasedConfig(),
        "volatility_based": VolatilityBasedConfig(),
        "momentum_based": MomentumBasedConfig()
    })
    crisis_detection: CrisisDetectionConfig = field(default_factory=CrisisDetectionConfig)
    regime_smoothing: RegimeSmoothingConfig = field(default_factory=RegimeSmoothingConfig)


@dataclass
class AlertLevelsConfig:
    info: Dict[str, float] = field(default_factory=lambda: {
        "volatility_change": 0.05, "correlation_change": 0.10, "regime_probability_change": 0.15
    })
    warning: Dict[str, float] = field(default_factory=lambda: {
        "volatility_change": 0.10, "correlation_change": 0.20, "price_change_1h": 0.05, "volume_spike": 2.0
    })
    critical: Dict[str, Any] = field(default_factory=lambda: {
        "volatility_change": 0.20, "price_change_1h": 0.10, "regime_change": True,
        "crisis_detected": True, "network_issue": True
    })


@dataclass
class DeliveryMethodsConfig:
    database_log: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "retention_days": 90})
    webhook: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False, "url": "https://hooks.slack.com/webhook-url"
    })
    email: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False, "smtp_server": "smtp.gmail.com",
        "recipients": ["alerts@lending-platform.com"]
    })


@dataclass
class RateLimitingConfig:
    max_alerts_per_hour: int = 10
    duplicate_alert_cooldown_minutes: int = 15
    critical_alert_bypass: bool = True


@dataclass
class AlertSystemConfig:
    alert_levels: AlertLevelsConfig = field(default_factory=AlertLevelsConfig)
    delivery_methods: DeliveryMethodsConfig = field(default_factory=DeliveryMethodsConfig)
    rate_limiting: RateLimitingConfig = field(default_factory=RateLimitingConfig)


@dataclass
class DataSourceConfig:
    enabled: bool = True
    api_endpoint: str = ""
    rate_limit_per_hour: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_second: Optional[int] = None
    symbols: List[str] = field(default_factory=list)


@dataclass
class DataSourcesConfig:
    primary_sources: Dict[str, DataSourceConfig] = field(default_factory=lambda: {
        "yahoo_finance": DataSourceConfig(
            api_endpoint="https://query1.finance.yahoo.com/v8/finance/chart",
            rate_limit_per_hour=1000,
            symbols=["SPY", "QQQ", "VIX", "TLT", "GLD"]
        ),
        "alpha_vantage": DataSourceConfig(
            enabled=False, api_endpoint="https://www.alphavantage.co/query",
            rate_limit_per_minute=5
        ),
        "binance": DataSourceConfig(
            api_endpoint="https://api.binance.com/api/v3",
            rate_limit_per_minute=1200,
            symbols=["BTCUSDT", "ETHUSDT", "ALGOUSDT"]
        ),
        "coinbase": DataSourceConfig(
            api_endpoint="https://api.exchange.coinbase.com",
            rate_limit_per_second=10,
            symbols=["BTC-USD", "ETH-USD", "ALGO-USD"]
        )
    })
    fallback_sources: Dict[str, DataSourceConfig] = field(default_factory=lambda: {
        "coingecko": DataSourceConfig(
            api_endpoint="https://api.coingecko.com/api/v3",
            rate_limit_per_minute=100
        ),
        "cached_data": DataSourceConfig(enabled=True)
    })


@dataclass
class UpdateFrequenciesConfig:
    price_data_seconds: int = 60
    volatility_calculation_minutes: int = 5
    correlation_update_hours: int = 1
    regime_detection_hours: int = 6
    stress_indicators_minutes: int = 15


@dataclass
class DataValidationConfig:
    max_price_change_percent: float = 0.50
    min_trading_volume: int = 1000
    stale_data_threshold_minutes: int = 10
    outlier_detection_enabled: bool = True
    outlier_threshold_std_devs: int = 3


@dataclass
class CircuitBreakersConfig:
    enabled: bool = True
    extreme_volatility_threshold: float = 1.0
    flash_crash_threshold: float = 0.20
    circuit_breaker_duration_minutes: int = 15


@dataclass
class RealTimeMonitoringConfig:
    update_frequencies: UpdateFrequenciesConfig = field(default_factory=UpdateFrequenciesConfig)
    data_validation: DataValidationConfig = field(default_factory=DataValidationConfig)
    circuit_breakers: CircuitBreakersConfig = field(default_factory=CircuitBreakersConfig)


@dataclass
class DataRetentionConfig:
    raw_data_days: int = 30
    calculated_metrics_days: int = 90
    regime_history_days: int = 365
    alert_history_days: int = 180


@dataclass
class TrendAnalysisConfig:
    enabled: bool = True
    trend_periods: List[int] = field(default_factory=lambda: [7, 30, 90, 252])
    trend_significance_threshold: float = 0.05


@dataclass
class SeasonalAnalysisConfig:
    enabled: bool = True
    seasonal_periods: List[str] = field(default_factory=lambda: ["day_of_week", "month_of_year", "quarter"])


@dataclass
class BacktestingConfig:
    enabled: bool = True
    backtest_periods: List[int] = field(default_factory=lambda: [30, 90, 252])
    regime_accuracy_threshold: float = 0.70


@dataclass
class HistoricalAnalysisConfig:
    data_retention: DataRetentionConfig = field(default_factory=DataRetentionConfig)
    trend_analysis: TrendAnalysisConfig = field(default_factory=TrendAnalysisConfig)
    seasonal_analysis: SeasonalAnalysisConfig = field(default_factory=SeasonalAnalysisConfig)
    backtesting: BacktestingConfig = field(default_factory=BacktestingConfig)


@dataclass
class PerformanceMetricsConfig:
    max_calculation_time_seconds: int = 30
    memory_usage_limit_mb: int = 500
    error_rate_threshold: float = 0.05


@dataclass
class HealthChecksConfig:
    data_freshness_minutes: int = 10
    calculation_success_rate: float = 0.95
    api_response_time_seconds: int = 5


@dataclass
class PerformanceMonitoringConfig:
    performance_metrics: PerformanceMetricsConfig = field(default_factory=PerformanceMetricsConfig)
    health_checks: HealthChecksConfig = field(default_factory=HealthChecksConfig)


@dataclass
class DatabaseTableConfig:
    partition_by: Optional[str] = None
    index_columns: List[str] = field(default_factory=list)


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/market_conditions_monitor.db"
    backup_enabled: bool = True
    backup_frequency_hours: int = 6
    max_history_limit: int = 50000
    tables: Dict[str, DatabaseTableConfig] = field(default_factory=lambda: {
        "market_data": DatabaseTableConfig(
            partition_by="date", index_columns=["timestamp", "symbol"]
        ),
        "volatility_calculations": DatabaseTableConfig(
            partition_by="date", index_columns=["timestamp", "asset", "window"]
        ),
        "regime_classifications": DatabaseTableConfig(
            index_columns=["timestamp", "regime_type"]
        ),
        "alerts": DatabaseTableConfig(
            index_columns=["timestamp", "alert_level", "alert_type"]
        )
    })


@dataclass
class DevelopmentConfig:
    mock_data_enabled: bool = False
    mock_data_path: str = "test_data/"
    log_level: str = "INFO"
    log_calculations: bool = True
    log_api_calls: bool = False
    log_alerts: bool = True
    test_scenarios: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "normal_market": {
            "vix_level": 20, "btc_volatility": 0.40, "algo_correlation_btc": 0.60, "expected_regime": "normal"
        },
        "stressed_market": {
            "vix_level": 40, "btc_volatility": 0.80, "algo_correlation_btc": 0.85, "expected_regime": "crisis"
        },
        "bull_market": {
            "trend_30d": 0.20, "volatility_level": 0.25, "fear_greed_index": 80, "expected_regime": "bull"
        },
        "bear_market": {
            "trend_30d": -0.25, "volatility_level": 0.45, "fear_greed_index": 20, "expected_regime": "bear"
        }
    })


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.80
    regime_confidence_threshold: float = 0.70
    alert_confidence_threshold: float = 0.75
    cache_expiry_minutes: int = 10


@dataclass
class BaseRateEngineConfig:
    enabled: bool = True
    volatility_adjustment_factor: float = 0.5
    regime_adjustment_factors: Dict[str, float] = field(default_factory=lambda: {
        "bull": -0.005, "normal": 0.000, "bear": 0.010, "crisis": 0.020
    })


@dataclass
class WebhookConfig:
    enabled: bool = False
    url: str = ""
    timeout_seconds: int = 5


@dataclass
class IntegrationConfig:
    base_rate_engine: BaseRateEngineConfig = field(default_factory=BaseRateEngineConfig)
    webhooks: Dict[str, WebhookConfig] = field(default_factory=lambda: {
        "lending_platform": WebhookConfig(url="http://localhost:8080/market-conditions"),
        "risk_management": WebhookConfig(url="http://localhost:8081/risk-alerts", timeout_seconds=3)
    })


@dataclass
class MarketConditionsMonitorConfig:
    """Complete configuration for the Market Conditions Monitor Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    volatility_monitoring: VolatilityMonitoringConfig = field(default_factory=VolatilityMonitoringConfig)
    algorand_ecosystem: AlgorandEcosystemConfig = field(default_factory=AlgorandEcosystemConfig)
    correlation_analysis: CorrelationAnalysisConfig = field(default_factory=CorrelationAnalysisConfig)
    stress_indicators: StressIndicatorsConfig = field(default_factory=StressIndicatorsConfig)
    regime_detection: RegimeDetectionConfig = field(default_factory=RegimeDetectionConfig)
    alert_system: AlertSystemConfig = field(default_factory=AlertSystemConfig)
    data_sources: DataSourcesConfig = field(default_factory=DataSourcesConfig)
    real_time_monitoring: RealTimeMonitoringConfig = field(default_factory=RealTimeMonitoringConfig)
    historical_analysis: HistoricalAnalysisConfig = field(default_factory=HistoricalAnalysisConfig)
    performance_monitoring: PerformanceMonitoringConfig = field(default_factory=PerformanceMonitoringConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)


class MarketConditionsConfigLoader:
    """Loads and manages configuration for the Market Conditions Monitor Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> MarketConditionsMonitorConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            MarketConditionsMonitorConfig instance
        """
        # Default config
        config = MarketConditionsMonitorConfig()

        # Try to load from file
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                config = MarketConditionsConfigLoader._merge_config(config, yaml_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        # Override with environment variables
        config = MarketConditionsConfigLoader._apply_env_overrides(config)

        return config

    @staticmethod
    def _merge_config(base_config: MarketConditionsMonitorConfig, yaml_data: Dict[str, Any]) -> MarketConditionsMonitorConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Volatility monitoring
        if 'volatility_monitoring' in yaml_data:
            vol_data = yaml_data['volatility_monitoring']
            vol_config = VolatilityMonitoringConfig()

            if 'calculation_methods' in vol_data:
                vol_config.calculation_methods = vol_data['calculation_methods']

            if 'time_windows' in vol_data:
                tw_data = vol_data['time_windows']
                vol_config.time_windows = TimeWindowsConfig(
                    intraday=tw_data.get('intraday', 24),
                    short_term=tw_data.get('short_term', 168),
                    medium_term=tw_data.get('medium_term', 720),
                    long_term=tw_data.get('long_term', 2160)
                )

            if 'thresholds' in vol_data:
                thresh_data = vol_data['thresholds']
                vol_config.thresholds = VolatilityThresholdsConfig(
                    low_volatility=thresh_data.get('low_volatility', 0.15),
                    normal_volatility=thresh_data.get('normal_volatility', 0.30),
                    high_volatility=thresh_data.get('high_volatility', 0.50),
                    extreme_volatility=thresh_data.get('extreme_volatility', 0.75)
                )

            if 'monitored_assets' in vol_data:
                vol_config.monitored_assets = vol_data['monitored_assets']

            base_config.volatility_monitoring = vol_config

        # Database config
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                default_path=db_data.get('default_path', 'notebooks/market_conditions_monitor.db'),
                backup_enabled=db_data.get('backup_enabled', True),
                backup_frequency_hours=db_data.get('backup_frequency_hours', 6),
                max_history_limit=db_data.get('max_history_limit', 50000)
            )

            if 'tables' in db_data:
                table_configs = {}
                for table_name, table_data in db_data['tables'].items():
                    table_configs[table_name] = DatabaseTableConfig(
                        partition_by=table_data.get('partition_by'),
                        index_columns=table_data.get('index_columns', [])
                    )
                base_config.database.tables = table_configs

        # Analysis config
        if 'analysis' in yaml_data:
            analysis_data = yaml_data['analysis']
            base_config.analysis = AnalysisConfig(
                default_confidence_score=analysis_data.get('default_confidence_score', 0.80),
                regime_confidence_threshold=analysis_data.get('regime_confidence_threshold', 0.70),
                alert_confidence_threshold=analysis_data.get('alert_confidence_threshold', 0.75),
                cache_expiry_minutes=analysis_data.get('cache_expiry_minutes', 10)
            )

        # Real-time monitoring
        if 'real_time_monitoring' in yaml_data:
            rtm_data = yaml_data['real_time_monitoring']

            if 'update_frequencies' in rtm_data:
                freq_data = rtm_data['update_frequencies']
                update_freq = UpdateFrequenciesConfig(
                    price_data_seconds=freq_data.get('price_data_seconds', 60),
                    volatility_calculation_minutes=freq_data.get('volatility_calculation_minutes', 5),
                    correlation_update_hours=freq_data.get('correlation_update_hours', 1),
                    regime_detection_hours=freq_data.get('regime_detection_hours', 6),
                    stress_indicators_minutes=freq_data.get('stress_indicators_minutes', 15)
                )
                base_config.real_time_monitoring.update_frequencies = update_freq

        # Development config
        if 'development' in yaml_data:
            dev_data = yaml_data['development']
            base_config.development = DevelopmentConfig(
                mock_data_enabled=dev_data.get('mock_data_enabled', False),
                mock_data_path=dev_data.get('mock_data_path', 'test_data/'),
                log_level=dev_data.get('log_level', 'INFO'),
                log_calculations=dev_data.get('log_calculations', True),
                log_api_calls=dev_data.get('log_api_calls', False),
                log_alerts=dev_data.get('log_alerts', True),
                test_scenarios=dev_data.get('test_scenarios', {})
            )

        # Integration config
        if 'integration' in yaml_data:
            int_data = yaml_data['integration']

            if 'base_rate_engine' in int_data:
                bre_data = int_data['base_rate_engine']
                base_config.integration.base_rate_engine = BaseRateEngineConfig(
                    enabled=bre_data.get('enabled', True),
                    volatility_adjustment_factor=bre_data.get('volatility_adjustment_factor', 0.5),
                    regime_adjustment_factors=bre_data.get('regime_adjustment_factors', {})
                )

        return base_config

    @staticmethod
    def _apply_env_overrides(config: MarketConditionsMonitorConfig) -> MarketConditionsMonitorConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'MARKET_CONDITIONS_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['MARKET_CONDITIONS_MCP_READER_URL']

        if 'MARKET_CONDITIONS_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['MARKET_CONDITIONS_MCP_MARKET_URL']

        # Database path
        if 'MARKET_CONDITIONS_DB_PATH' in os.environ:
            config.database.default_path = os.environ['MARKET_CONDITIONS_DB_PATH']

        # API keys
        if 'ALPHA_VANTAGE_API_KEY' in os.environ:
            api_key = os.environ['ALPHA_VANTAGE_API_KEY']
            config.data_sources.primary_sources['alpha_vantage'].enabled = True

        if 'YAHOO_FINANCE_API_KEY' in os.environ:
            # Yahoo Finance doesn't require API key but can use one for higher limits
            pass

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> MarketConditionsMonitorConfig:
    """Load configuration - convenience function"""
    return MarketConditionsConfigLoader.load_config(config_path)