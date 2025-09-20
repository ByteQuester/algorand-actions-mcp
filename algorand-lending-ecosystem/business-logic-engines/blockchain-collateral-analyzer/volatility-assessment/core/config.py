"""
Configuration Management for Volatility Assessment Engine
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
class PriceStalenessConfig:
    scoring_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'fresh': 30,
        'good': 300,
        'acceptable': 900,
        'stale': 3600,
        'very_stale': 7200
    })

    scoring_values: Dict[str, float] = field(default_factory=lambda: {
        'fresh': 1.0,
        'good': 0.9,
        'acceptable': 0.7,
        'stale': 0.5,
        'decline_rate': 0.000069444
    })


@dataclass
class VolatilityCalculationConfig:
    lookback_periods: Dict[str, int] = field(default_factory=lambda: {
        'short_term_minutes': 60,
        'medium_term_hours': 24,
        'long_term_days': 7
    })

    windows: Dict[str, int] = field(default_factory=lambda: {
        'manipulation_detection': 60,
        'volatility_7d': 7,
        'volatility_30d': 30
    })

    minimum_data_points: int = 5


@dataclass
class ManipulationDetectionConfig:
    risk_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'volatility_high': 0.10,
        'price_range_suspicious': 0.20,
        'consensus_poor': 0.80,
        'insufficient_oracles': 2
    })

    risk_scoring: Dict[str, float] = field(default_factory=lambda: {
        'volatility_weight': 0.3,
        'price_range_weight': 0.4,
        'consensus_weight': 0.3,
        'oracle_coverage_weight': 0.2
    })

    risk_levels: Dict[str, float] = field(default_factory=lambda: {
        'minimal_threshold': 0.2,
        'low_threshold': 0.4,
        'medium_threshold': 0.7,
        'high_threshold': 0.7
    })


@dataclass
class OracleConfidenceConfig:
    minimum_confidence: float = 0.8
    confidence_penalty_single: float = 0.8
    consensus_strength_single: float = 0.5

    reliability_weights: Dict[str, float] = field(default_factory=lambda: {
        'consensus_weight': 0.4,
        'staleness_weight': 0.3,
        'reliability_weight': 0.3
    })

    outlier_detection: Dict[str, any] = field(default_factory=lambda: {
        'max_deviation_multiplier': 10,
        'weighted_median_enabled': True
    })


@dataclass
class MarketAnalysisConfig:
    asset_categories: Dict[str, List[str]] = field(default_factory=lambda: {
        'highly_liquid': ["ALGO", "USDC", "USDT", "BTC", "ETH"],
        'liquid': ["AVAX", "SOL", "MATIC"],
        'illiquid': ["GARD", "STBL"]
    })

    volume_analysis: Dict[str, int] = field(default_factory=lambda: {
        'high': 1000000,
        'medium': 100000,
        'low': 10000
    })

    correlation_analysis: Dict[str, any] = field(default_factory=lambda: {
        'correlation_window_days': 30,
        'correlation_threshold': 0.8
    })


@dataclass
class MonitoringConfig:
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'volatility_spike': 2.0,
        'price_deviation': 0.15,
        'oracle_failure_count': 2,
        'staleness_critical': 7200
    })

    escalation_levels: Dict[str, float] = field(default_factory=lambda: {
        'warning': 0.3,
        'critical': 0.6,
        'emergency': 0.8
    })


@dataclass
class PerformanceConfig:
    cache_settings: Dict[str, int] = field(default_factory=lambda: {
        'price_cache_seconds': 30,
        'volatility_cache_minutes': 5,
        'oracle_status_cache_seconds': 60
    })

    rate_limiting: Dict[str, int] = field(default_factory=lambda: {
        'max_requests_per_second': 10,
        'timeout_seconds': 30
    })

    batch_processing: Dict[str, int] = field(default_factory=lambda: {
        'max_batch_size': 50,
        'parallel_requests': 5
    })


@dataclass
class StorageConfig:
    price_history: Dict[str, int] = field(default_factory=lambda: {
        'retention_days': 30,
        'cleanup_interval_hours': 24,
        'max_records_per_asset': 10000
    })

    volatility_metrics: Dict[str, int] = field(default_factory=lambda: {
        'retention_days': 90,
        'calculation_interval_minutes': 15
    })


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.8
    data_quality_score: float = 0.85
    simulation_iterations: int = 1000
    stress_test_scenarios: int = 5
    cache_expiry_minutes: int = 3


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/volatility_analysis.db"
    max_history_limit: int = 1000
    backup_enabled: bool = True
    backup_interval_hours: int = 6


@dataclass
class VolatilityEngineConfig:
    """Complete configuration for the Volatility Assessment Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    price_staleness: PriceStalenessConfig = field(default_factory=PriceStalenessConfig)
    volatility_calculation: VolatilityCalculationConfig = field(default_factory=VolatilityCalculationConfig)
    manipulation_detection: ManipulationDetectionConfig = field(default_factory=ManipulationDetectionConfig)
    oracle_confidence: OracleConfidenceConfig = field(default_factory=OracleConfidenceConfig)
    market_analysis: MarketAnalysisConfig = field(default_factory=MarketAnalysisConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)


class ConfigLoader:
    """Loads and manages configuration for the Volatility Assessment Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> VolatilityEngineConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            VolatilityEngineConfig instance
        """
        # Default config
        config = VolatilityEngineConfig()

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
    def _merge_config(base_config: VolatilityEngineConfig, yaml_data: Dict[str, Any]) -> VolatilityEngineConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Price staleness
        if 'price_staleness' in yaml_data:
            staleness_data = yaml_data['price_staleness']
            base_config.price_staleness = PriceStalenessConfig(
                scoring_thresholds=staleness_data.get('scoring_thresholds', base_config.price_staleness.scoring_thresholds),
                scoring_values=staleness_data.get('scoring_values', base_config.price_staleness.scoring_values)
            )

        # Volatility calculation
        if 'volatility_calculation' in yaml_data:
            vol_data = yaml_data['volatility_calculation']
            base_config.volatility_calculation = VolatilityCalculationConfig(
                lookback_periods=vol_data.get('lookback_periods', base_config.volatility_calculation.lookback_periods),
                windows=vol_data.get('windows', base_config.volatility_calculation.windows),
                minimum_data_points=vol_data.get('minimum_data_points', base_config.volatility_calculation.minimum_data_points)
            )

        # Manipulation detection
        if 'manipulation_detection' in yaml_data:
            manip_data = yaml_data['manipulation_detection']
            base_config.manipulation_detection = ManipulationDetectionConfig(
                risk_thresholds=manip_data.get('risk_thresholds', base_config.manipulation_detection.risk_thresholds),
                risk_scoring=manip_data.get('risk_scoring', base_config.manipulation_detection.risk_scoring),
                risk_levels=manip_data.get('risk_levels', base_config.manipulation_detection.risk_levels)
            )

        # Oracle confidence
        if 'oracle_confidence' in yaml_data:
            oracle_data = yaml_data['oracle_confidence']
            base_config.oracle_confidence = OracleConfidenceConfig(
                minimum_confidence=oracle_data.get('minimum_confidence', base_config.oracle_confidence.minimum_confidence),
                confidence_penalty_single=oracle_data.get('confidence_penalty_single', base_config.oracle_confidence.confidence_penalty_single),
                consensus_strength_single=oracle_data.get('consensus_strength_single', base_config.oracle_confidence.consensus_strength_single),
                reliability_weights=oracle_data.get('reliability_weights', base_config.oracle_confidence.reliability_weights),
                outlier_detection=oracle_data.get('outlier_detection', base_config.oracle_confidence.outlier_detection)
            )

        # Market analysis
        if 'market_analysis' in yaml_data:
            market_data = yaml_data['market_analysis']
            base_config.market_analysis = MarketAnalysisConfig(
                asset_categories=market_data.get('asset_categories', base_config.market_analysis.asset_categories),
                volume_analysis=market_data.get('volume_analysis', base_config.market_analysis.volume_analysis),
                correlation_analysis=market_data.get('correlation_analysis', base_config.market_analysis.correlation_analysis)
            )

        # Monitoring
        if 'monitoring' in yaml_data:
            monitoring_data = yaml_data['monitoring']
            base_config.monitoring = MonitoringConfig(
                alert_thresholds=monitoring_data.get('alert_thresholds', base_config.monitoring.alert_thresholds),
                escalation_levels=monitoring_data.get('escalation_levels', base_config.monitoring.escalation_levels)
            )

        # Performance
        if 'performance' in yaml_data:
            perf_data = yaml_data['performance']
            base_config.performance = PerformanceConfig(
                cache_settings=perf_data.get('cache_settings', base_config.performance.cache_settings),
                rate_limiting=perf_data.get('rate_limiting', base_config.performance.rate_limiting),
                batch_processing=perf_data.get('batch_processing', base_config.performance.batch_processing)
            )

        # Storage
        if 'storage' in yaml_data:
            storage_data = yaml_data['storage']
            base_config.storage = StorageConfig(
                price_history=storage_data.get('price_history', base_config.storage.price_history),
                volatility_metrics=storage_data.get('volatility_metrics', base_config.storage.volatility_metrics)
            )

        # Analysis config
        if 'analysis' in yaml_data:
            analysis_data = yaml_data['analysis']
            base_config.analysis = AnalysisConfig(
                default_confidence_score=analysis_data.get('default_confidence_score', base_config.analysis.default_confidence_score),
                data_quality_score=analysis_data.get('data_quality_score', base_config.analysis.data_quality_score),
                simulation_iterations=analysis_data.get('simulation_iterations', base_config.analysis.simulation_iterations),
                stress_test_scenarios=analysis_data.get('stress_test_scenarios', base_config.analysis.stress_test_scenarios),
                cache_expiry_minutes=analysis_data.get('cache_expiry_minutes', base_config.analysis.cache_expiry_minutes)
            )

        # Database config
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                default_path=db_data.get('default_path', base_config.database.default_path),
                max_history_limit=db_data.get('max_history_limit', base_config.database.max_history_limit),
                backup_enabled=db_data.get('backup_enabled', base_config.database.backup_enabled),
                backup_interval_hours=db_data.get('backup_interval_hours', base_config.database.backup_interval_hours)
            )

        return base_config

    @staticmethod
    def _apply_env_overrides(config: VolatilityEngineConfig) -> VolatilityEngineConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'VOLATILITY_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['VOLATILITY_MCP_READER_URL']

        if 'VOLATILITY_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['VOLATILITY_MCP_MARKET_URL']

        # Database path
        if 'VOLATILITY_DB_PATH' in os.environ:
            config.database.default_path = os.environ['VOLATILITY_DB_PATH']

        # Minimum confidence threshold
        if 'VOLATILITY_MIN_CONFIDENCE' in os.environ:
            try:
                config.oracle_confidence.minimum_confidence = float(os.environ['VOLATILITY_MIN_CONFIDENCE'])
            except ValueError:
                print(f"Warning: Invalid VOLATILITY_MIN_CONFIDENCE value: {os.environ['VOLATILITY_MIN_CONFIDENCE']}")

        # Cache settings
        if 'VOLATILITY_CACHE_SECONDS' in os.environ:
            try:
                config.performance.cache_settings['price_cache_seconds'] = int(os.environ['VOLATILITY_CACHE_SECONDS'])
            except ValueError:
                print(f"Warning: Invalid VOLATILITY_CACHE_SECONDS value: {os.environ['VOLATILITY_CACHE_SECONDS']}")

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> VolatilityEngineConfig:
    """Load configuration - convenience function"""
    return ConfigLoader.load_config(config_path)