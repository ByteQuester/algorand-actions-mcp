"""
Configuration Management for Oracle Price Integration Engine
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
class OracleProviderConfig:
    enabled: bool = True
    api_url: str = ""
    api_key: Optional[str] = None
    variance: float = 0.001
    latency_seconds: int = 30
    reliability_score: float = 0.95
    timeout_seconds: int = 10
    retry_attempts: int = 3


@dataclass
class RefreshIntervalConfig:
    high_frequency_seconds: int = 5
    medium_frequency_seconds: int = 30
    low_frequency_seconds: int = 300
    emergency_frequency_seconds: int = 1


@dataclass
class ValidationConfig:
    max_price_deviation_percent: float = 10.0
    min_oracle_agreement_threshold: float = 0.8
    outlier_detection_method: str = "z_score"
    outlier_threshold: float = 2.5
    min_data_points: int = 2
    confidence_threshold: float = 0.8


@dataclass
class AggregationConfig:
    method: str = "weighted_median"
    weight_factors: Dict[str, float] = field(default_factory=lambda: {
        'reliability_weight': 0.4,
        'confidence_weight': 0.3,
        'freshness_weight': 0.2,
        'volume_weight': 0.1
    })
    outlier_removal: bool = True


@dataclass
class ReputationConfig:
    tracking_window_hours: int = 168
    accuracy_weight: float = 0.5
    uptime_weight: float = 0.3
    response_time_weight: float = 0.2
    min_historical_data_points: int = 100
    reputation_decay_factor: float = 0.95


@dataclass
class FallbackConfig:
    enabled: bool = True
    max_staleness_minutes: int = 60
    emergency_prices: Dict[str, float] = field(default_factory=lambda: {
        'ALGO': 0.25,
        'USDC': 1.00,
        'USDT': 1.00,
        'BTC': 45000.0,
        'ETH': 3000.0,
        'goBTC': 45000.0,
        'goETH': 3000.0
    })
    fallback_sources: List[str] = field(default_factory=lambda: [
        "cached_prices",
        "emergency_prices",
        "external_api_backup"
    ])


@dataclass
class StalenessConfig:
    excellent_threshold_seconds: int = 30
    good_threshold_seconds: int = 300
    acceptable_threshold_seconds: int = 900
    poor_threshold_seconds: int = 3600
    unacceptable_threshold_seconds: int = 7200


@dataclass
class ManipulationDetectionConfig:
    enabled: bool = True
    lookback_minutes: int = 60
    volatility_threshold: float = 0.1
    price_range_threshold: float = 0.2
    consensus_threshold: float = 0.8
    min_oracle_coverage: int = 2
    risk_weights: Dict[str, float] = field(default_factory=lambda: {
        'high_volatility': 0.3,
        'large_price_swings': 0.4,
        'poor_consensus': 0.3,
        'insufficient_coverage': 0.2
    })


@dataclass
class CircuitBreakerConfig:
    enabled: bool = True
    max_failures_per_minute: int = 5
    failure_window_minutes: int = 5
    recovery_time_minutes: int = 10
    escalation_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'warning': 0.3,
        'critical': 0.6,
        'emergency': 0.8
    })


@dataclass
class AssetConfig:
    priority: str = "medium"
    refresh_interval_override: Optional[int] = None
    confidence_threshold_override: Optional[float] = None
    max_staleness_override: Optional[int] = None


@dataclass
class CachingConfig:
    enabled: bool = True
    default_ttl_seconds: int = 30
    max_cache_size: int = 1000
    cleanup_interval_minutes: int = 10


@dataclass
class MonitoringConfig:
    health_check_interval_seconds: int = 60
    log_level: str = "INFO"
    metrics_enabled: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'oracle_failure_rate': 0.2,
        'consensus_failure_rate': 0.1,
        'average_latency_ms': 5000
    })


@dataclass
class DatabaseConfig:
    price_history_retention_days: int = 30
    oracle_performance_retention_days: int = 90
    cleanup_interval_hours: int = 24


@dataclass
class OracleEngineConfig:
    """Complete configuration for the Oracle Price Integration Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    oracle_providers: Dict[str, OracleProviderConfig] = field(default_factory=lambda: {
        'chainlink': OracleProviderConfig(
            api_url="https://api.chain.link",
            variance=0.001,
            latency_seconds=30,
            reliability_score=0.95
        ),
        'pyth': OracleProviderConfig(
            api_url="https://hermes.pyth.network",
            variance=0.002,
            latency_seconds=5,
            reliability_score=0.92
        ),
        'algorand_native': OracleProviderConfig(
            api_url="https://mainnet-api.algonode.cloud",
            variance=0.0005,
            latency_seconds=1,
            reliability_score=0.98
        ),
        'dia': OracleProviderConfig(
            api_url="https://api.diadata.org",
            variance=0.003,
            latency_seconds=60,
            reliability_score=0.85
        )
    })

    refresh_intervals: RefreshIntervalConfig = field(default_factory=RefreshIntervalConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    reputation: ReputationConfig = field(default_factory=ReputationConfig)
    fallback: FallbackConfig = field(default_factory=FallbackConfig)
    staleness: StalenessConfig = field(default_factory=StalenessConfig)
    manipulation_detection: ManipulationDetectionConfig = field(default_factory=ManipulationDetectionConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Asset-specific configurations
    asset_configurations: Dict[str, AssetConfig] = field(default_factory=lambda: {
        'ALGO': AssetConfig(
            priority="high",
            refresh_interval_override=5,
            confidence_threshold_override=0.9,
            max_staleness_override=30
        ),
        'USDC': AssetConfig(
            priority="high",
            refresh_interval_override=30,
            confidence_threshold_override=0.85,
            max_staleness_override=300
        ),
        'BTC': AssetConfig(
            priority="medium",
            refresh_interval_override=10,
            confidence_threshold_override=0.85,
            max_staleness_override=60
        )
    })


class ConfigLoader:
    """Loads and manages configuration for the Oracle Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> OracleEngineConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            OracleEngineConfig instance
        """
        # Default config
        config = OracleEngineConfig()

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
    def _merge_config(base_config: OracleEngineConfig, yaml_data: Dict[str, Any]) -> OracleEngineConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Oracle providers
        if 'oracle_providers' in yaml_data:
            providers_data = yaml_data['oracle_providers']
            for provider_name, provider_data in providers_data.items():
                base_config.oracle_providers[provider_name] = OracleProviderConfig(
                    enabled=provider_data.get('enabled', True),
                    api_url=provider_data.get('api_url', ''),
                    api_key=provider_data.get('api_key'),
                    variance=provider_data.get('variance', 0.001),
                    latency_seconds=provider_data.get('latency_seconds', 30),
                    reliability_score=provider_data.get('reliability_score', 0.95),
                    timeout_seconds=provider_data.get('timeout_seconds', 10),
                    retry_attempts=provider_data.get('retry_attempts', 3)
                )

        # Refresh intervals
        if 'refresh_intervals' in yaml_data:
            refresh_data = yaml_data['refresh_intervals']
            base_config.refresh_intervals = RefreshIntervalConfig(
                high_frequency_seconds=refresh_data.get('high_frequency_seconds', 5),
                medium_frequency_seconds=refresh_data.get('medium_frequency_seconds', 30),
                low_frequency_seconds=refresh_data.get('low_frequency_seconds', 300),
                emergency_frequency_seconds=refresh_data.get('emergency_frequency_seconds', 1)
            )

        # Validation
        if 'validation' in yaml_data:
            val_data = yaml_data['validation']
            base_config.validation = ValidationConfig(
                max_price_deviation_percent=val_data.get('max_price_deviation_percent', 10.0),
                min_oracle_agreement_threshold=val_data.get('min_oracle_agreement_threshold', 0.8),
                outlier_detection_method=val_data.get('outlier_detection_method', 'z_score'),
                outlier_threshold=val_data.get('outlier_threshold', 2.5),
                min_data_points=val_data.get('min_data_points', 2),
                confidence_threshold=val_data.get('confidence_threshold', 0.8)
            )

        # Aggregation
        if 'aggregation' in yaml_data:
            agg_data = yaml_data['aggregation']
            base_config.aggregation = AggregationConfig(
                method=agg_data.get('method', 'weighted_median'),
                weight_factors=agg_data.get('weight_factors', base_config.aggregation.weight_factors),
                outlier_removal=agg_data.get('outlier_removal', True)
            )

        # Reputation
        if 'reputation' in yaml_data:
            rep_data = yaml_data['reputation']
            base_config.reputation = ReputationConfig(
                tracking_window_hours=rep_data.get('tracking_window_hours', 168),
                accuracy_weight=rep_data.get('accuracy_weight', 0.5),
                uptime_weight=rep_data.get('uptime_weight', 0.3),
                response_time_weight=rep_data.get('response_time_weight', 0.2),
                min_historical_data_points=rep_data.get('min_historical_data_points', 100),
                reputation_decay_factor=rep_data.get('reputation_decay_factor', 0.95)
            )

        # Fallback
        if 'fallback' in yaml_data:
            fall_data = yaml_data['fallback']
            base_config.fallback = FallbackConfig(
                enabled=fall_data.get('enabled', True),
                max_staleness_minutes=fall_data.get('max_staleness_minutes', 60),
                emergency_prices=fall_data.get('emergency_prices', base_config.fallback.emergency_prices),
                fallback_sources=fall_data.get('fallback_sources', base_config.fallback.fallback_sources)
            )

        # Staleness
        if 'staleness' in yaml_data:
            stale_data = yaml_data['staleness']
            base_config.staleness = StalenessConfig(
                excellent_threshold_seconds=stale_data.get('excellent_threshold_seconds', 30),
                good_threshold_seconds=stale_data.get('good_threshold_seconds', 300),
                acceptable_threshold_seconds=stale_data.get('acceptable_threshold_seconds', 900),
                poor_threshold_seconds=stale_data.get('poor_threshold_seconds', 3600),
                unacceptable_threshold_seconds=stale_data.get('unacceptable_threshold_seconds', 7200)
            )

        # Manipulation detection
        if 'manipulation_detection' in yaml_data:
            manip_data = yaml_data['manipulation_detection']
            base_config.manipulation_detection = ManipulationDetectionConfig(
                enabled=manip_data.get('enabled', True),
                lookback_minutes=manip_data.get('lookback_minutes', 60),
                volatility_threshold=manip_data.get('volatility_threshold', 0.1),
                price_range_threshold=manip_data.get('price_range_threshold', 0.2),
                consensus_threshold=manip_data.get('consensus_threshold', 0.8),
                min_oracle_coverage=manip_data.get('min_oracle_coverage', 2),
                risk_weights=manip_data.get('risk_weights', base_config.manipulation_detection.risk_weights)
            )

        # Circuit breaker
        if 'circuit_breaker' in yaml_data:
            circuit_data = yaml_data['circuit_breaker']
            base_config.circuit_breaker = CircuitBreakerConfig(
                enabled=circuit_data.get('enabled', True),
                max_failures_per_minute=circuit_data.get('max_failures_per_minute', 5),
                failure_window_minutes=circuit_data.get('failure_window_minutes', 5),
                recovery_time_minutes=circuit_data.get('recovery_time_minutes', 10),
                escalation_thresholds=circuit_data.get('escalation_thresholds', base_config.circuit_breaker.escalation_thresholds)
            )

        # Caching
        if 'caching' in yaml_data:
            cache_data = yaml_data['caching']
            base_config.caching = CachingConfig(
                enabled=cache_data.get('enabled', True),
                default_ttl_seconds=cache_data.get('default_ttl_seconds', 30),
                max_cache_size=cache_data.get('max_cache_size', 1000),
                cleanup_interval_minutes=cache_data.get('cleanup_interval_minutes', 10)
            )

        # Monitoring
        if 'monitoring' in yaml_data:
            monitor_data = yaml_data['monitoring']
            base_config.monitoring = MonitoringConfig(
                health_check_interval_seconds=monitor_data.get('health_check_interval_seconds', 60),
                log_level=monitor_data.get('log_level', 'INFO'),
                metrics_enabled=monitor_data.get('metrics_enabled', True),
                alert_thresholds=monitor_data.get('alert_thresholds', base_config.monitoring.alert_thresholds)
            )

        # Database
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                price_history_retention_days=db_data.get('price_history_retention_days', 30),
                oracle_performance_retention_days=db_data.get('oracle_performance_retention_days', 90),
                cleanup_interval_hours=db_data.get('cleanup_interval_hours', 24)
            )

        # Asset configurations
        if 'asset_configurations' in yaml_data:
            asset_data = yaml_data['asset_configurations']
            for asset_symbol, asset_config in asset_data.items():
                base_config.asset_configurations[asset_symbol] = AssetConfig(
                    priority=asset_config.get('priority', 'medium'),
                    refresh_interval_override=asset_config.get('refresh_interval_override'),
                    confidence_threshold_override=asset_config.get('confidence_threshold_override'),
                    max_staleness_override=asset_config.get('max_staleness_override')
                )

        return base_config

    @staticmethod
    def _apply_env_overrides(config: OracleEngineConfig) -> OracleEngineConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'ORACLE_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['ORACLE_MCP_READER_URL']

        if 'ORACLE_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['ORACLE_MCP_MARKET_URL']

        # Oracle API keys
        for provider_name in config.oracle_providers.keys():
            env_key = f'ORACLE_{provider_name.upper()}_API_KEY'
            if env_key in os.environ:
                config.oracle_providers[provider_name].api_key = os.environ[env_key]

        # Monitoring log level
        if 'ORACLE_LOG_LEVEL' in os.environ:
            config.monitoring.log_level = os.environ['ORACLE_LOG_LEVEL']

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> OracleEngineConfig:
    """Load configuration - convenience function"""
    return ConfigLoader.load_config(config_path)