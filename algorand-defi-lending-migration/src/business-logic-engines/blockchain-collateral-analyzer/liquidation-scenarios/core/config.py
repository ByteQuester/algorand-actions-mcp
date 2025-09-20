"""
Configuration Management for Liquidation Scenarios Engine
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
class SlippageCalculationConfig:
    max_slippage_cap: float = 0.50
    volume_ratio_power: float = 0.7
    base_slippage_factor: float = 0.1
    depth_penalty_factor: float = 0.02
    max_depth_penalty: float = 0.20
    speed_power_factor: float = 0.5


@dataclass
class LiquidationTimingConfig:
    volume_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'very_small': 0.01,
        'small': 0.05,
        'medium': 0.10,
        'large': 0.25
    })

    base_liquidation_times: Dict[str, float] = field(default_factory=lambda: {
        'very_small': 0.5,
        'small': 2.0,
        'medium': 8.0,
        'large': 24.0,
        'very_large': 48.0
    })

    time_constraints: Dict[str, float] = field(default_factory=lambda: {
        'min_hours': 0.1,
        'max_hours': 168.0
    })


@dataclass
class LiquidityAdjustmentConfig:
    high: float = 0.5
    medium: float = 1.0
    low: float = 2.0


@dataclass
class UrgencyAdjustmentConfig:
    immediate: float = 0.25
    urgent: float = 0.5
    normal: float = 1.0
    patient: float = 2.0


@dataclass
class MarketImpactConfig:
    low: float = 0.01
    medium: float = 0.05
    high: float = 0.05


@dataclass
class LiquidationStrategyConfig:
    max_slippage_tolerance: float
    target_completion_time: float
    min_recovery_rate: float
    market_impact_limit: float
    gas_cost_consideration: bool = True


@dataclass
class LiquidationStrategiesConfig:
    immediate: LiquidationStrategyConfig = field(default_factory=lambda: LiquidationStrategyConfig(
        max_slippage_tolerance=0.15,
        target_completion_time=1.0,
        min_recovery_rate=0.80,
        market_impact_limit=0.10
    ))

    gradual: LiquidationStrategyConfig = field(default_factory=lambda: LiquidationStrategyConfig(
        max_slippage_tolerance=0.05,
        target_completion_time=24.0,
        min_recovery_rate=0.90,
        market_impact_limit=0.03
    ))

    selective: LiquidationStrategyConfig = field(default_factory=lambda: LiquidationStrategyConfig(
        max_slippage_tolerance=0.08,
        target_completion_time=2.0,
        min_recovery_rate=0.85,
        market_impact_limit=0.05
    ))


@dataclass
class ExecutionParametersConfig:
    default_gas_cost_usd: float = 50.0
    tranche_delay_hours: float = 0.5
    depth_safety_factor: float = 0.5
    max_tranches: int = 10


@dataclass
class FeasibilityAssessmentConfig:
    volume_impact_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'very_high': 0.01,
        'high': 0.05,
        'medium': 0.15,
        'low': 0.30,
        'very_low': 0.30
    })

    confidence_scores: Dict[str, float] = field(default_factory=lambda: {
        'very_high': 0.95,
        'high': 0.85,
        'medium': 0.70,
        'low': 0.50,
        'very_low': 0.25
    })


@dataclass
class FlashLoanConfig:
    enabled: bool = True
    max_flash_loan_amount: float = 10_000_000
    flash_loan_fee_rate: float = 0.0009
    flash_loan_gas_multiplier: float = 2.0
    supported_protocols: List[str] = field(default_factory=lambda: ["aave", "dydx", "balancer"])


@dataclass
class EmergencyScenarioConfig:
    fallback_discount: float
    max_liquidation_delay: float
    confidence_penalty: float
    volatility_threshold: Optional[float] = None
    slippage_multiplier: Optional[float] = None
    urgency_override: Optional[str] = None
    market_crash_threshold: Optional[float] = None
    emergency_slippage_tolerance: Optional[float] = None
    override_recovery_requirements: Optional[bool] = None
    priority_liquidation_only: Optional[bool] = None


@dataclass
class EmergencyScenariosConfig:
    oracle_failure: EmergencyScenarioConfig = field(default_factory=lambda: EmergencyScenarioConfig(
        fallback_discount=0.20,
        max_liquidation_delay=2.0,
        confidence_penalty=0.30
    ))

    volatility_spike: EmergencyScenarioConfig = field(default_factory=lambda: EmergencyScenarioConfig(
        fallback_discount=0.0,
        max_liquidation_delay=0.0,
        confidence_penalty=0.0,
        volatility_threshold=0.50,
        slippage_multiplier=1.5,
        urgency_override="immediate"
    ))

    black_swan: EmergencyScenarioConfig = field(default_factory=lambda: EmergencyScenarioConfig(
        fallback_discount=0.0,
        max_liquidation_delay=0.0,
        confidence_penalty=0.0,
        market_crash_threshold=0.30,
        emergency_slippage_tolerance=0.25,
        override_recovery_requirements=True,
        priority_liquidation_only=True
    ))


@dataclass
class DutchAuctionConfig:
    enabled: bool = True
    starting_discount: float = 0.05
    discount_increment: float = 0.01
    time_interval_minutes: int = 15
    max_discount: float = 0.20


@dataclass
class SealedBidAuctionConfig:
    enabled: bool = False
    minimum_bid_increment: float = 0.005
    auction_duration_hours: float = 4
    reserve_price_discount: float = 0.10


@dataclass
class AuctionParametersConfig:
    dutch_auction: DutchAuctionConfig = field(default_factory=DutchAuctionConfig)
    sealed_bid_auction: SealedBidAuctionConfig = field(default_factory=SealedBidAuctionConfig)


@dataclass
class RecoveryRatesConfig:
    asset_type_adjustments: Dict[str, float] = field(default_factory=lambda: {
        'highly_liquid': 0.95,
        'liquid': 0.90,
        'illiquid': 0.75
    })

    market_condition_adjustments: Dict[str, float] = field(default_factory=lambda: {
        'bull_market': 1.05,
        'normal_market': 1.00,
        'bear_market': 0.90,
        'crisis_market': 0.70
    })


@dataclass
class LiquidationPenaltiesConfig:
    borrower_penalty_rate: float = 0.05
    liquidator_bonus_rate: float = 0.03
    protocol_fee_rate: float = 0.02
    insurance_fund_rate: float = 0.01


@dataclass
class RiskMonitoringConfig:
    position_concentration_limit: float = 0.30
    portfolio_correlation_limit: float = 0.70
    volatility_spike_threshold: float = 2.0
    liquidity_drop_threshold: float = 0.50


@dataclass
class AnalysisConfig:
    default_confidence_score: float = 0.8
    data_quality_score: float = 0.85
    simulation_iterations: int = 1000
    stress_test_scenarios: int = 5
    cache_expiry_minutes: int = 3


@dataclass
class DatabaseConfig:
    default_path: str = "notebooks/liquidation_analysis.db"
    max_history_limit: int = 500
    backup_enabled: bool = True
    backup_interval_hours: int = 6


@dataclass
class LiquidationEngineConfig:
    """Complete configuration for the Liquidation Scenarios Engine"""

    mcp_services: MCPServiceConfig = field(default_factory=MCPServiceConfig)
    slippage_calculation: SlippageCalculationConfig = field(default_factory=SlippageCalculationConfig)
    liquidation_timing: LiquidationTimingConfig = field(default_factory=LiquidationTimingConfig)
    liquidity_adjustments: LiquidityAdjustmentConfig = field(default_factory=LiquidityAdjustmentConfig)
    urgency_adjustments: UrgencyAdjustmentConfig = field(default_factory=UrgencyAdjustmentConfig)
    market_impact_thresholds: MarketImpactConfig = field(default_factory=MarketImpactConfig)
    liquidation_strategies: LiquidationStrategiesConfig = field(default_factory=LiquidationStrategiesConfig)
    execution_parameters: ExecutionParametersConfig = field(default_factory=ExecutionParametersConfig)
    feasibility_assessment: FeasibilityAssessmentConfig = field(default_factory=FeasibilityAssessmentConfig)
    flash_loan_integration: FlashLoanConfig = field(default_factory=FlashLoanConfig)
    emergency_scenarios: EmergencyScenariosConfig = field(default_factory=EmergencyScenariosConfig)
    auction_parameters: AuctionParametersConfig = field(default_factory=AuctionParametersConfig)
    recovery_rates: RecoveryRatesConfig = field(default_factory=RecoveryRatesConfig)
    liquidation_penalties: LiquidationPenaltiesConfig = field(default_factory=LiquidationPenaltiesConfig)
    risk_monitoring: RiskMonitoringConfig = field(default_factory=RiskMonitoringConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)


class ConfigLoader:
    """Loads and manages configuration for the Liquidation Engine"""

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> LiquidationEngineConfig:
        """
        Load configuration from YAML file or environment variables

        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory

        Returns:
            LiquidationEngineConfig instance
        """
        # Default config
        config = LiquidationEngineConfig()

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
    def _merge_config(base_config: LiquidationEngineConfig, yaml_data: Dict[str, Any]) -> LiquidationEngineConfig:
        """Merge YAML configuration with base config"""

        # MCP Services
        if 'mcp_services' in yaml_data:
            mcp_data = yaml_data['mcp_services']
            base_config.mcp_services = MCPServiceConfig(
                algorand_reader_url=mcp_data.get('algorand_reader_url', base_config.mcp_services.algorand_reader_url),
                market_data_url=mcp_data.get('market_data_url', base_config.mcp_services.market_data_url)
            )

        # Slippage calculation
        if 'slippage_calculation' in yaml_data:
            slip_data = yaml_data['slippage_calculation']
            base_config.slippage_calculation = SlippageCalculationConfig(
                max_slippage_cap=slip_data.get('max_slippage_cap', base_config.slippage_calculation.max_slippage_cap),
                volume_ratio_power=slip_data.get('volume_ratio_power', base_config.slippage_calculation.volume_ratio_power),
                base_slippage_factor=slip_data.get('base_slippage_factor', base_config.slippage_calculation.base_slippage_factor),
                depth_penalty_factor=slip_data.get('depth_penalty_factor', base_config.slippage_calculation.depth_penalty_factor),
                max_depth_penalty=slip_data.get('max_depth_penalty', base_config.slippage_calculation.max_depth_penalty),
                speed_power_factor=slip_data.get('speed_power_factor', base_config.slippage_calculation.speed_power_factor)
            )

        # Liquidation timing
        if 'liquidation_timing' in yaml_data:
            timing_data = yaml_data['liquidation_timing']
            base_config.liquidation_timing = LiquidationTimingConfig(
                volume_thresholds=timing_data.get('volume_thresholds', base_config.liquidation_timing.volume_thresholds),
                base_liquidation_times=timing_data.get('base_liquidation_times', base_config.liquidation_timing.base_liquidation_times),
                time_constraints=timing_data.get('time_constraints', base_config.liquidation_timing.time_constraints)
            )

        # Liquidity adjustments
        if 'liquidity_adjustments' in yaml_data:
            liq_data = yaml_data['liquidity_adjustments']
            base_config.liquidity_adjustments = LiquidityAdjustmentConfig(
                high=liq_data.get('high', base_config.liquidity_adjustments.high),
                medium=liq_data.get('medium', base_config.liquidity_adjustments.medium),
                low=liq_data.get('low', base_config.liquidity_adjustments.low)
            )

        # Urgency adjustments
        if 'urgency_adjustments' in yaml_data:
            urg_data = yaml_data['urgency_adjustments']
            base_config.urgency_adjustments = UrgencyAdjustmentConfig(
                immediate=urg_data.get('immediate', base_config.urgency_adjustments.immediate),
                urgent=urg_data.get('urgent', base_config.urgency_adjustments.urgent),
                normal=urg_data.get('normal', base_config.urgency_adjustments.normal),
                patient=urg_data.get('patient', base_config.urgency_adjustments.patient)
            )

        # Market impact thresholds
        if 'market_impact_thresholds' in yaml_data:
            impact_data = yaml_data['market_impact_thresholds']
            base_config.market_impact_thresholds = MarketImpactConfig(
                low=impact_data.get('low', base_config.market_impact_thresholds.low),
                medium=impact_data.get('medium', base_config.market_impact_thresholds.medium),
                high=impact_data.get('high', base_config.market_impact_thresholds.high)
            )

        # Liquidation strategies
        if 'liquidation_strategies' in yaml_data:
            strategies_data = yaml_data['liquidation_strategies']

            immediate = strategies_data.get('immediate', {})
            gradual = strategies_data.get('gradual', {})
            selective = strategies_data.get('selective', {})

            base_config.liquidation_strategies = LiquidationStrategiesConfig(
                immediate=LiquidationStrategyConfig(
                    max_slippage_tolerance=immediate.get('max_slippage_tolerance', 0.15),
                    target_completion_time=immediate.get('target_completion_time', 1.0),
                    min_recovery_rate=immediate.get('min_recovery_rate', 0.80),
                    market_impact_limit=immediate.get('market_impact_limit', 0.10),
                    gas_cost_consideration=immediate.get('gas_cost_consideration', True)
                ),
                gradual=LiquidationStrategyConfig(
                    max_slippage_tolerance=gradual.get('max_slippage_tolerance', 0.05),
                    target_completion_time=gradual.get('target_completion_time', 24.0),
                    min_recovery_rate=gradual.get('min_recovery_rate', 0.90),
                    market_impact_limit=gradual.get('market_impact_limit', 0.03),
                    gas_cost_consideration=gradual.get('gas_cost_consideration', True)
                ),
                selective=LiquidationStrategyConfig(
                    max_slippage_tolerance=selective.get('max_slippage_tolerance', 0.08),
                    target_completion_time=selective.get('target_completion_time', 2.0),
                    min_recovery_rate=selective.get('min_recovery_rate', 0.85),
                    market_impact_limit=selective.get('market_impact_limit', 0.05),
                    gas_cost_consideration=selective.get('gas_cost_consideration', True)
                )
            )

        # Execution parameters
        if 'execution_parameters' in yaml_data:
            exec_data = yaml_data['execution_parameters']
            base_config.execution_parameters = ExecutionParametersConfig(
                default_gas_cost_usd=exec_data.get('default_gas_cost_usd', base_config.execution_parameters.default_gas_cost_usd),
                tranche_delay_hours=exec_data.get('tranche_delay_hours', base_config.execution_parameters.tranche_delay_hours),
                depth_safety_factor=exec_data.get('depth_safety_factor', base_config.execution_parameters.depth_safety_factor),
                max_tranches=exec_data.get('max_tranches', base_config.execution_parameters.max_tranches)
            )

        # Feasibility assessment
        if 'feasibility_assessment' in yaml_data:
            feas_data = yaml_data['feasibility_assessment']
            base_config.feasibility_assessment = FeasibilityAssessmentConfig(
                volume_impact_thresholds=feas_data.get('volume_impact_thresholds', base_config.feasibility_assessment.volume_impact_thresholds),
                confidence_scores=feas_data.get('confidence_scores', base_config.feasibility_assessment.confidence_scores)
            )

        # Flash loan integration
        if 'flash_loan_integration' in yaml_data:
            flash_data = yaml_data['flash_loan_integration']
            base_config.flash_loan_integration = FlashLoanConfig(
                enabled=flash_data.get('enabled', base_config.flash_loan_integration.enabled),
                max_flash_loan_amount=flash_data.get('max_flash_loan_amount', base_config.flash_loan_integration.max_flash_loan_amount),
                flash_loan_fee_rate=flash_data.get('flash_loan_fee_rate', base_config.flash_loan_integration.flash_loan_fee_rate),
                flash_loan_gas_multiplier=flash_data.get('flash_loan_gas_multiplier', base_config.flash_loan_integration.flash_loan_gas_multiplier),
                supported_protocols=flash_data.get('supported_protocols', base_config.flash_loan_integration.supported_protocols)
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

        return base_config

    @staticmethod
    def _apply_env_overrides(config: LiquidationEngineConfig) -> LiquidationEngineConfig:
        """Apply environment variable overrides"""

        # MCP service URLs
        if 'LIQUIDATION_MCP_READER_URL' in os.environ:
            config.mcp_services.algorand_reader_url = os.environ['LIQUIDATION_MCP_READER_URL']

        if 'LIQUIDATION_MCP_MARKET_URL' in os.environ:
            config.mcp_services.market_data_url = os.environ['LIQUIDATION_MCP_MARKET_URL']

        # Database path
        if 'LIQUIDATION_DB_PATH' in os.environ:
            config.database.default_path = os.environ['LIQUIDATION_DB_PATH']

        # Flash loan settings
        if 'LIQUIDATION_FLASH_LOAN_ENABLED' in os.environ:
            config.flash_loan_integration.enabled = os.environ['LIQUIDATION_FLASH_LOAN_ENABLED'].lower() == 'true'

        return config


# Convenience function for loading config
def load_config(config_path: Optional[Path] = None) -> LiquidationEngineConfig:
    """Load configuration - convenience function"""
    return ConfigLoader.load_config(config_path)