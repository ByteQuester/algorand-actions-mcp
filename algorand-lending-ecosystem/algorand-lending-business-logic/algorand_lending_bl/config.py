"""
Simplified Configuration for Algorand Lending Business Logic

Single configuration file with essential parameters only.
Replaced complex YAML schema validation with simple dataclasses.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional, List
import os


@dataclass
class NetworkConfig:
    """Algorand network configuration"""
    # Algorand node endpoints
    algod_address: str = "https://testnet-api.algonode.cloud"
    algod_token: str = ""
    indexer_address: str = "https://testnet-idx.algonode.cloud"
    indexer_token: str = ""

    # Network parameters
    network: str = "testnet"  # mainnet, testnet, betanet
    request_timeout: int = 30
    retry_attempts: int = 3


@dataclass
class CollateralConfig:
    """Collateral analysis configuration"""
    # Risk parameters
    min_collateral_ratio: Decimal = Decimal('1.5')  # 150% minimum
    liquidation_threshold: Decimal = Decimal('1.25')  # 125% liquidation
    max_asset_concentration: Decimal = Decimal('0.4')  # 40% max single asset

    # Haircut percentages by asset type
    algo_haircut: Decimal = Decimal('0.1')  # 10% haircut for ALGO
    stablecoin_haircut: Decimal = Decimal('0.05')  # 5% haircut for stablecoins
    asa_haircut: Decimal = Decimal('0.2')  # 20% haircut for other ASAs
    lp_token_haircut: Decimal = Decimal('0.3')  # 30% haircut for LP tokens

    # Pricing and data sources
    price_staleness_threshold: int = 300  # 5 minutes
    min_liquidity_usd: Decimal = Decimal('100000')  # $100k minimum liquidity
    volatility_lookback_days: int = 30

    # Cache settings
    price_cache_ttl: int = 60  # 1 minute
    analysis_cache_ttl: int = 300  # 5 minutes


@dataclass
class InterestRateConfig:
    """Interest rate calculation configuration"""
    # Base rate parameters
    base_spread: Decimal = Decimal('0.02')  # 2% spread over staking yield
    min_rate: Decimal = Decimal('0.05')  # 5% minimum rate
    max_rate: Decimal = Decimal('0.25')  # 25% maximum rate

    # Duration premiums (per year)
    duration_premium_per_year: Decimal = Decimal('0.01')  # 1% per year

    # Risk adjustments
    max_reputation_adjustment: Decimal = Decimal('0.1')  # +/- 10%
    max_collateral_adjustment: Decimal = Decimal('0.05')  # +/- 5%
    max_network_adjustment: Decimal = Decimal('0.02')  # +/- 2%

    # Data freshness requirements
    max_data_age_hours: int = 6
    min_data_confidence: Decimal = Decimal('0.7')  # 70% minimum confidence

    # Cache settings
    rate_cache_ttl: int = 300  # 5 minutes
    market_data_cache_ttl: int = 60  # 1 minute


@dataclass
class LoanApprovalConfig:
    """Loan approval engine configuration"""
    # Approval thresholds
    min_approval_score: Decimal = Decimal('0.6')  # 60% minimum score
    min_confidence_level: Decimal = Decimal('0.7')  # 70% minimum confidence

    # Loan limits
    max_loan_amount_usd: Decimal = Decimal('1000000')  # $1M maximum
    min_loan_amount_usd: Decimal = Decimal('1000')  # $1K minimum
    max_loan_term_days: int = 730  # 2 years maximum
    min_loan_term_days: int = 1  # 1 day minimum

    # Borrower requirements
    min_account_age_days: int = 30
    min_transaction_count: int = 10
    min_total_volume_algo: Decimal = Decimal('100')  # 100 ALGO minimum volume

    # Decision caching
    decision_cache_ttl: int = 3600  # 1 hour


@dataclass
class RiskAssessmentConfig:
    """Risk assessment configuration"""
    # Risk score thresholds
    low_risk_threshold: Decimal = Decimal('30')
    medium_risk_threshold: Decimal = Decimal('60')
    high_risk_threshold: Decimal = Decimal('80')

    # Alert thresholds
    risk_alert_threshold: Decimal = Decimal('70')
    critical_alert_threshold: Decimal = Decimal('90')

    # Analysis parameters
    lookback_days: int = 90
    min_data_points: int = 10
    correlation_threshold: Decimal = Decimal('0.6')

    # Cache settings
    risk_cache_ttl: int = 1800  # 30 minutes


@dataclass
class ServiceConfig:
    """Service-level configuration"""
    # External service URLs
    algorand_reader_url: str = "http://localhost:8000"
    market_data_url: str = "http://localhost:8001"

    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30

    # Logging
    log_level: str = "INFO"
    enable_performance_logging: bool = True

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090


@dataclass
class AlgorandLendingConfig:
    """Main configuration combining all sub-configurations"""
    network: NetworkConfig = field(default_factory=NetworkConfig)
    collateral: CollateralConfig = field(default_factory=CollateralConfig)
    interest_rates: InterestRateConfig = field(default_factory=InterestRateConfig)
    loan_approval: LoanApprovalConfig = field(default_factory=LoanApprovalConfig)
    risk_assessment: RiskAssessmentConfig = field(default_factory=RiskAssessmentConfig)
    service: ServiceConfig = field(default_factory=ServiceConfig)

    # Environment-based overrides
    def __post_init__(self):
        """Apply environment variable overrides"""
        # Network overrides
        if os.getenv("ALGOD_ADDRESS"):
            self.network.algod_address = os.getenv("ALGOD_ADDRESS")
        if os.getenv("ALGOD_TOKEN"):
            self.network.algod_token = os.getenv("ALGOD_TOKEN")
        if os.getenv("INDEXER_ADDRESS"):
            self.network.indexer_address = os.getenv("INDEXER_ADDRESS")
        if os.getenv("INDEXER_TOKEN"):
            self.network.indexer_token = os.getenv("INDEXER_TOKEN")
        if os.getenv("ALGORAND_NETWORK"):
            self.network.network = os.getenv("ALGORAND_NETWORK")

        # Service overrides
        if os.getenv("ALGORAND_READER_URL"):
            self.service.algorand_reader_url = os.getenv("ALGORAND_READER_URL")
        if os.getenv("MARKET_DATA_URL"):
            self.service.market_data_url = os.getenv("MARKET_DATA_URL")
        if os.getenv("LOG_LEVEL"):
            self.service.log_level = os.getenv("LOG_LEVEL")


# Default configuration instances for convenience
DEFAULT_CONFIG = AlgorandLendingConfig()
DEFAULT_NETWORK_CONFIG = NetworkConfig()
DEFAULT_COLLATERAL_CONFIG = CollateralConfig()
DEFAULT_INTEREST_RATE_CONFIG = InterestRateConfig()
DEFAULT_LOAN_APPROVAL_CONFIG = LoanApprovalConfig()
DEFAULT_RISK_ASSESSMENT_CONFIG = RiskAssessmentConfig()
DEFAULT_SERVICE_CONFIG = ServiceConfig()


def create_config_from_env() -> AlgorandLendingConfig:
    """Create configuration with environment variable overrides applied"""
    return AlgorandLendingConfig()


def create_testnet_config() -> AlgorandLendingConfig:
    """Create configuration optimized for testnet development"""
    config = AlgorandLendingConfig()

    # Testnet-specific overrides
    config.network.network = "testnet"
    config.network.algod_address = "https://testnet-api.algonode.cloud"
    config.network.indexer_address = "https://testnet-idx.algonode.cloud"

    # More lenient settings for testing
    config.collateral.min_collateral_ratio = Decimal('1.2')  # 120% for testing
    config.loan_approval.min_account_age_days = 1  # 1 day for testing
    config.loan_approval.min_transaction_count = 1  # 1 transaction for testing
    config.loan_approval.min_total_volume_algo = Decimal('1')  # 1 ALGO for testing

    return config


def create_mainnet_config() -> AlgorandLendingConfig:
    """Create configuration optimized for mainnet production"""
    config = AlgorandLendingConfig()

    # Mainnet-specific overrides
    config.network.network = "mainnet"
    config.network.algod_address = "https://mainnet-api.algonode.cloud"
    config.network.indexer_address = "https://mainnet-idx.algonode.cloud"

    # More conservative settings for production
    config.collateral.min_collateral_ratio = Decimal('1.8')  # 180% for mainnet
    config.interest_rates.min_rate = Decimal('0.08')  # 8% minimum for mainnet
    config.loan_approval.min_account_age_days = 90  # 90 days for mainnet
    config.loan_approval.min_transaction_count = 50  # 50 transactions for mainnet
    config.loan_approval.min_total_volume_algo = Decimal('1000')  # 1000 ALGO for mainnet

    return config


def validate_config(config: AlgorandLendingConfig) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []

    # Validate network config
    if not config.network.algod_address:
        issues.append("Algod address is required")
    if not config.network.indexer_address:
        issues.append("Indexer address is required")
    if config.network.network not in ["mainnet", "testnet", "betanet"]:
        issues.append("Network must be mainnet, testnet, or betanet")

    # Validate collateral config
    if config.collateral.min_collateral_ratio <= 1:
        issues.append("Minimum collateral ratio must be greater than 100%")
    if config.collateral.liquidation_threshold >= config.collateral.min_collateral_ratio:
        issues.append("Liquidation threshold must be less than minimum collateral ratio")

    # Validate interest rate config
    if config.interest_rates.min_rate >= config.interest_rates.max_rate:
        issues.append("Minimum rate must be less than maximum rate")
    if config.interest_rates.max_rate > Decimal('1.0'):
        issues.append("Maximum rate should not exceed 100%")

    # Validate loan approval config
    if config.loan_approval.min_loan_amount_usd >= config.loan_approval.max_loan_amount_usd:
        issues.append("Minimum loan amount must be less than maximum")
    if config.loan_approval.min_loan_term_days >= config.loan_approval.max_loan_term_days:
        issues.append("Minimum loan term must be less than maximum")

    return issues


# Export configuration classes and factory functions
__all__ = [
    "NetworkConfig",
    "CollateralConfig",
    "InterestRateConfig",
    "LoanApprovalConfig",
    "RiskAssessmentConfig",
    "ServiceConfig",
    "AlgorandLendingConfig",
    "DEFAULT_CONFIG",
    "create_config_from_env",
    "create_testnet_config",
    "create_mainnet_config",
    "validate_config"
]