"""
Configuration Management for Portfolio Diversification Engine
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
class HHICalculationConfig:
    min_hhi: float = 0.2
    max_hhi: float = 1.0
    perfect_diversification_types: int = 5


@dataclass
class AssetTypeCategoryConfig:
    base_weight: float
    volatility_multiplier: float
    liquidity_factor: float


@dataclass
class AssetTypeCategoriesConfig:
    cryptocurrency: AssetTypeCategoryConfig = field(default_factory=lambda: AssetTypeCategoryConfig(
        base_weight=1.0, volatility_multiplier=1.2, liquidity_factor=0.8
    ))
    stablecoin: AssetTypeCategoryConfig = field(default_factory=lambda: AssetTypeCategoryConfig(
        base_weight=0.8, volatility_multiplier=0.3, liquidity_factor=1.0
    ))
    defi_token: AssetTypeCategoryConfig = field(default_factory=lambda: AssetTypeCategoryConfig(
        base_weight=1.1, volatility_multiplier=1.5, liquidity_factor=0.6
    ))
    nft: AssetTypeCategoryConfig = field(default_factory=lambda: AssetTypeCategoryConfig(
        base_weight=1.3, volatility_multiplier=2.0, liquidity_factor=0.3
    ))
    governance_token: AssetTypeCategoryConfig = field(default_factory=lambda: AssetTypeCategoryConfig(
        base_weight=1.0, volatility_multiplier=1.3, liquidity_factor=0.7
    ))


@dataclass
class ConcentrationLimitsConfig:
    single_asset_max: float = 0.40
    single_type_max: float = 0.60
    correlated_assets_max: float = 0.50
    low_liquidity_max: float = 0.30


@dataclass
class PositionThresholdsConfig:
    minimum_position_usd: float = 100.0
    minimum_portfolio_usd: float = 1000.0
    dust_threshold_usd: float = 10.0
    rebalancing_threshold: float = 0.05


@dataclass
class DiversificationScoringConfig:
    excellent_threshold: float = 0.8
    good_threshold: float = 0.6
    adequate_threshold: float = 0.4
    poor_threshold: float = 0.2


@dataclass
class RiskAdjustmentConfig:
    collateral_ratio_reduction: Optional[float] = None
    collateral_ratio_increase: Optional[float] = None
    confidence_bonus: Optional[float] = None
    confidence_penalty: Optional[float] = None


@dataclass
class RiskAdjustmentsConfig:
    excellent_diversification: RiskAdjustmentConfig = field(default_factory=lambda: RiskAdjustmentConfig(
        collateral_ratio_reduction=0.10, confidence_bonus=0.15
    ))
    good_diversification: RiskAdjustmentConfig = field(default_factory=lambda: RiskAdjustmentConfig(
        collateral_ratio_reduction=0.05, confidence_bonus=0.10
    ))
    adequate_diversification: RiskAdjustmentConfig = field(default_factory=lambda: RiskAdjustmentConfig(
        collateral_ratio_reduction=0.00, confidence_bonus=0.00
    ))
    poor_diversification: RiskAdjustmentConfig = field(default_factory=lambda: RiskAdjustmentConfig(
        collateral_ratio_increase=0.10, confidence_penalty=0.15
    ))
    very_poor_diversification: RiskAdjustmentConfig = field(default_factory=lambda: RiskAdjustmentConfig(
        collateral_ratio_increase=0.20, confidence_penalty=0.25
    ))


@dataclass
class CorrelationAnalysisConfig:
    high_correlation_threshold: float = 0.70
    medium_correlation_threshold: float = 0.40
    correlation_lookback_days: int = 90
    min_data_points: int = 30


@dataclass
class LiquidityTierConfig:
    daily_volume_threshold: float
    bid_ask_spread_max: float
    market_depth_min: float


@dataclass
class LiquidityTiersConfig:
    high: LiquidityTierConfig = field(default_factory=lambda: LiquidityTierConfig(
        daily_volume_threshold=10_000_000, bid_ask_spread_max=0.005, market_depth_min=1_000_000
    ))
    medium: LiquidityTierConfig = field(default_factory=lambda: LiquidityTierConfig(
        daily_volume_threshold=1_000_000, bid_ask_spread_max=0.02, market_depth_min=100_000
    ))
    low: LiquidityTierConfig = field(default_factory=lambda: LiquidityTierConfig(
        daily_volume_threshold=100_000, bid_ask_spread_max=0.05, market_depth_min=10_000
    ))


@dataclass
class RebalancingConfig:
    frequency_days: int = 30
    threshold_deviation: float = 0.10
    min_trade_size: float = 1000.0


@dataclass
class DiversificationTargetsConfig:
    target_asset_types: int = 5
    max_single_asset: float = 0.25
    min_stablecoin_allocation: float = 0.15


@dataclass
class RiskManagementConfig:
    volatility_budget: float = 0.40
    correlation_limit: float = 0.60
    liquidity_requirement: float = 0.20


@dataclass
class OptimizationRecommendationsConfig:
    rebalancing: RebalancingConfig = field(default_factory=RebalancingConfig)
    diversification_targets: DiversificationTargetsConfig = field(default_factory=DiversificationTargetsConfig)
    risk_management: RiskManagementConfig = field(default_factory=RiskManagementConfig)


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.75
    data_quality_threshold: float = 0.80
    monte_carlo_simulations: int = 1000
    stress_test_scenarios: int = 10
    cache_expiry_minutes: int = 5
    historical_lookback_days: int = 365


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/portfolio_diversification.db"
    max_history_records: int = 1000
    backup_enabled: bool = True
    backup_interval_hours: int = 12


@dataclass
class APIIntegrationConfig:
    rate_limit_requests_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1


@dataclass
class AlertingConfig:
    concentration_alert_threshold: float = 0.35
    correlation_spike_threshold: float = 0.80
    liquidity_drop_threshold: float = 0.50
    diversification_warning_threshold: float = 0.30


@dataclass
class MarketCrashConfig:
    volatility_spike_threshold: float = 0.50
    correlation_increase_threshold: float = 0.90
    emergency_rebalancing: bool = True


@dataclass
class LiquidityCrisisConfig:
    liquidity_drop_threshold: float = 0.70
    high_liquidity_requirement: float = 0.50
    restrict_low_liquidity: bool = True


@dataclass
class BlackSwanConfig:
    disable_normal_rules: bool = True
    emergency_exit_strategy: bool = True
    minimum_stablecoin_allocation: float = 0.30


@dataclass
class EmergencyScenariosConfig:
    market_crash: MarketCrashConfig = field(default_factory=MarketCrashConfig)
    liquidity_crisis: LiquidityCrisisConfig = field(default_factory=LiquidityCrisisConfig)
    black_swan: BlackSwanConfig = field(default_factory=BlackSwanConfig)


@dataclass
class PortfolioDiversificationConfig:
    """Complete configuration for the Portfolio Diversification Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    hhi_calculation: HHICalculationConfig = field(default_factory=HHICalculationConfig)
    asset_type_categories: AssetTypeCategoriesConfig = field(default_factory=AssetTypeCategoriesConfig)
    concentration_limits: ConcentrationLimitsConfig = field(default_factory=ConcentrationLimitsConfig)
    position_thresholds: PositionThresholdsConfig = field(default_factory=PositionThresholdsConfig)
    diversification_scoring: DiversificationScoringConfig = field(default_factory=DiversificationScoringConfig)
    risk_adjustments: RiskAdjustmentsConfig = field(default_factory=RiskAdjustmentsConfig)
    correlation_analysis: CorrelationAnalysisConfig = field(default_factory=CorrelationAnalysisConfig)
    asset_type_correlations: Dict[str, Dict[str, float]] = field(default_factory=dict)
    liquidity_tiers: LiquidityTiersConfig = field(default_factory=LiquidityTiersConfig)
    optimization_recommendations: OptimizationRecommendationsConfig = field(default_factory=OptimizationRecommendationsConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api_integration: APIIntegrationConfig = field(default_factory=APIIntegrationConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    emergency_scenarios: EmergencyScenariosConfig = field(default_factory=EmergencyScenariosConfig)


class ConfigLoader:
    """Loads and manages configuration for the Portfolio Diversification Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> PortfolioDiversificationConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            PortfolioDiversificationConfig instance
        """
        # Default config
        config = PortfolioDiversificationConfig()

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
    def _merge_config(base_config: PortfolioDiversificationConfig, yaml_data: Dict[str, Any]) -> PortfolioDiversificationConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # HHI calculation
        if 'hhi_calculation' in yaml_data:
            hhi_data = yaml_data['hhi_calculation']
            base_config.hhi_calculation = HHICalculationConfig(
                min_hhi=hhi_data.get('min_hhi', base_config.hhi_calculation.min_hhi),
                max_hhi=hhi_data.get('max_hhi', base_config.hhi_calculation.max_hhi),
                perfect_diversification_types=hhi_data.get('perfect_diversification_types', base_config.hhi_calculation.perfect_diversification_types)
            )

        # Asset type categories
        if 'asset_type_categories' in yaml_data:
            categories_data = yaml_data['asset_type_categories']

            def create_category_config(category_data: Dict[str, Any]) -> AssetTypeCategoryConfig:
                return AssetTypeCategoryConfig(
                    base_weight=category_data.get('base_weight', 1.0),
                    volatility_multiplier=category_data.get('volatility_multiplier', 1.0),
                    liquidity_factor=category_data.get('liquidity_factor', 1.0)
                )

            base_config.asset_type_categories = AssetTypeCategoriesConfig(
                cryptocurrency=create_category_config(categories_data.get('cryptocurrency', {})),
                stablecoin=create_category_config(categories_data.get('stablecoin', {})),
                defi_token=create_category_config(categories_data.get('defi_token', {})),
                nft=create_category_config(categories_data.get('nft', {})),
                governance_token=create_category_config(categories_data.get('governance_token', {}))
            )

        # Concentration limits
        if 'concentration_limits' in yaml_data:
            conc_data = yaml_data['concentration_limits']
            base_config.concentration_limits = ConcentrationLimitsConfig(
                single_asset_max=conc_data.get('single_asset_max', base_config.concentration_limits.single_asset_max),
                single_type_max=conc_data.get('single_type_max', base_config.concentration_limits.single_type_max),
                correlated_assets_max=conc_data.get('correlated_assets_max', base_config.concentration_limits.correlated_assets_max),
                low_liquidity_max=conc_data.get('low_liquidity_max', base_config.concentration_limits.low_liquidity_max)
            )

        # Position thresholds
        if 'position_thresholds' in yaml_data:
            pos_data = yaml_data['position_thresholds']
            base_config.position_thresholds = PositionThresholdsConfig(
                minimum_position_usd=pos_data.get('minimum_position_usd', base_config.position_thresholds.minimum_position_usd),
                minimum_portfolio_usd=pos_data.get('minimum_portfolio_usd', base_config.position_thresholds.minimum_portfolio_usd),
                dust_threshold_usd=pos_data.get('dust_threshold_usd', base_config.position_thresholds.dust_threshold_usd),
                rebalancing_threshold=pos_data.get('rebalancing_threshold', base_config.position_thresholds.rebalancing_threshold)
            )

        # Diversification scoring
        if 'diversification_scoring' in yaml_data:
            div_data = yaml_data['diversification_scoring']
            base_config.diversification_scoring = DiversificationScoringConfig(
                excellent_threshold=div_data.get('excellent_threshold', base_config.diversification_scoring.excellent_threshold),
                good_threshold=div_data.get('good_threshold', base_config.diversification_scoring.good_threshold),
                adequate_threshold=div_data.get('adequate_threshold', base_config.diversification_scoring.adequate_threshold),
                poor_threshold=div_data.get('poor_threshold', base_config.diversification_scoring.poor_threshold)
            )

        # Risk adjustments
        if 'risk_adjustments' in yaml_data:
            risk_data = yaml_data['risk_adjustments']

            def create_risk_adjustment(adj_data: Dict[str, Any]) -> RiskAdjustmentConfig:
                return RiskAdjustmentConfig(
                    collateral_ratio_reduction=adj_data.get('collateral_ratio_reduction'),
                    collateral_ratio_increase=adj_data.get('collateral_ratio_increase'),
                    confidence_bonus=adj_data.get('confidence_bonus'),
                    confidence_penalty=adj_data.get('confidence_penalty')
                )

            base_config.risk_adjustments = RiskAdjustmentsConfig(
                excellent_diversification=create_risk_adjustment(risk_data.get('excellent_diversification', {})),
                good_diversification=create_risk_adjustment(risk_data.get('good_diversification', {})),
                adequate_diversification=create_risk_adjustment(risk_data.get('adequate_diversification', {})),
                poor_diversification=create_risk_adjustment(risk_data.get('poor_diversification', {})),
                very_poor_diversification=create_risk_adjustment(risk_data.get('very_poor_diversification', {}))
            )

        # Correlation analysis
        if 'correlation_analysis' in yaml_data:
            corr_data = yaml_data['correlation_analysis']
            base_config.correlation_analysis = CorrelationAnalysisConfig(
                high_correlation_threshold=corr_data.get('high_correlation_threshold', base_config.correlation_analysis.high_correlation_threshold),
                medium_correlation_threshold=corr_data.get('medium_correlation_threshold', base_config.correlation_analysis.medium_correlation_threshold),
                correlation_lookback_days=corr_data.get('correlation_lookback_days', base_config.correlation_analysis.correlation_lookback_days),
                min_data_points=corr_data.get('min_data_points', base_config.correlation_analysis.min_data_points)
            )

        # Asset type correlations
        if 'asset_type_correlations' in yaml_data:
            base_config.asset_type_correlations = yaml_data['asset_type_correlations']

        # Liquidity tiers
        if 'liquidity_tiers' in yaml_data:
            liq_data = yaml_data['liquidity_tiers']

            def create_liquidity_tier(tier_data: Dict[str, Any]) -> LiquidityTierConfig:
                return LiquidityTierConfig(
                    daily_volume_threshold=tier_data.get('daily_volume_threshold', 0),
                    bid_ask_spread_max=tier_data.get('bid_ask_spread_max', 1.0),
                    market_depth_min=tier_data.get('market_depth_min', 0)
                )

            base_config.liquidity_tiers = LiquidityTiersConfig(
                high=create_liquidity_tier(liq_data.get('high', {})),
                medium=create_liquidity_tier(liq_data.get('medium', {})),
                low=create_liquidity_tier(liq_data.get('low', {}))
            )

        # Database config
        if 'database' in yaml_data:
            db_data = yaml_data['database']
            base_config.database = DatabaseConfig(
                default_path=db_data.get('default_path', base_config.database.default_path),
                max_history_records=db_data.get('max_history_records', base_config.database.max_history_records),
                backup_enabled=db_data.get('backup_enabled', base_config.database.backup_enabled),
                backup_interval_hours=db_data.get('backup_interval_hours', base_config.database.backup_interval_hours)
            )

        # Analysis config
        if 'analysis' in yaml_data:
            analysis_data = yaml_data['analysis']
            base_config.analysis = AnalysisConfig(
                default_confidence_score=analysis_data.get('default_confidence_score', base_config.analysis.default_confidence_score),
                data_quality_threshold=analysis_data.get('data_quality_threshold', base_config.analysis.data_quality_threshold),
                monte_carlo_simulations=analysis_data.get('monte_carlo_simulations', base_config.analysis.monte_carlo_simulations),
                stress_test_scenarios=analysis_data.get('stress_test_scenarios', base_config.analysis.stress_test_scenarios),
                cache_expiry_minutes=analysis_data.get('cache_expiry_minutes', base_config.analysis.cache_expiry_minutes),
                historical_lookback_days=analysis_data.get('historical_lookback_days', base_config.analysis.historical_lookback_days)
            )

        return base_config

    @staticmethod
    def _apply_env_overrides(config: PortfolioDiversificationConfig) -> PortfolioDiversificationConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'PORTFOLIO_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['PORTFOLIO_MCP_READER_URL']

        if 'PORTFOLIO_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['PORTFOLIO_MCP_MARKET_URL']

        # Database path
        if 'PORTFOLIO_DB_PATH' in os.environ:
            config.database.default_path = os.environ['PORTFOLIO_DB_PATH']

        # HHI parameters
        if 'PORTFOLIO_MIN_HHI' in os.environ:
            try:
                config.hhi_calculation.min_hhi = float(os.environ['PORTFOLIO_MIN_HHI'])
            except ValueError:
                pass

        if 'PORTFOLIO_MAX_HHI' in os.environ:
            try:
                config.hhi_calculation.max_hhi = float(os.environ['PORTFOLIO_MAX_HHI'])
            except ValueError:
                pass

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> PortfolioDiversificationConfig:
    """Load configuration - convenience function"""
    return ConfigLoader.load_config(config_path)