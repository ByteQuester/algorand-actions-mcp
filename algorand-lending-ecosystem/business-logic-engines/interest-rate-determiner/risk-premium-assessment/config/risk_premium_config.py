"""
Risk Premium Assessment Configuration

Defines scoring weights, thresholds, and parameters for comprehensive risk assessment
including traditional credit scoring and Algorand-specific on-chain behavior analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import json
import os


@dataclass
class CreditScoringWeights:
    """Traditional credit scoring factor weights."""
    payment_history: float = 0.35
    credit_utilization: float = 0.30
    credit_age: float = 0.15
    credit_mix: float = 0.10
    new_credit: float = 0.10


@dataclass
class OnChainBehaviorWeights:
    """Algorand on-chain behavior scoring weights."""
    wallet_age: float = 0.20
    transaction_volume: float = 0.25
    defi_participation: float = 0.20
    governance_voting: float = 0.15
    staking_history: float = 0.10
    smart_contract_interactions: float = 0.10


@dataclass
class RiskThresholds:
    """Risk assessment thresholds and boundaries."""
    excellent_credit_score: int = 750
    good_credit_score: int = 670
    fair_credit_score: int = 580
    poor_credit_score: int = 500

    min_wallet_age_days: int = 90
    min_transaction_count: int = 10
    min_defi_participation_score: float = 0.3

    high_risk_threshold: float = 0.7
    medium_risk_threshold: float = 0.4
    low_risk_threshold: float = 0.2


@dataclass
class MarketConditionFactors:
    """Dynamic risk adjustment factors based on market conditions."""
    volatility_multiplier: float = 1.5
    liquidity_adjustment: float = 1.2
    correlation_penalty: float = 1.3
    market_stress_multiplier: float = 2.0


@dataclass
class AlgorandSpecificParams:
    """Algorand-specific scoring parameters."""
    governance_period_bonus: float = 0.15
    consensus_participation_bonus: float = 0.10
    asa_creation_bonus: float = 0.05
    smart_contract_deployment_bonus: float = 0.10

    min_governance_commitment_algo: int = 1000
    min_staking_period_days: int = 30
    defi_protocol_whitelist: List[str] = field(default_factory=lambda: [
        'tinyman', 'algofi', 'folks_finance', 'pact', 'humble_swap'
    ])


@dataclass
class RiskPremiumRates:
    """Base risk premium rates for different risk categories."""
    base_rate: Decimal = Decimal('0.02')  # 2% base rate

    # Risk category premiums (annual percentage points)
    excellent_premium: Decimal = Decimal('0.005')  # 0.5%
    good_premium: Decimal = Decimal('0.015')       # 1.5%
    fair_premium: Decimal = Decimal('0.035')       # 3.5%
    poor_premium: Decimal = Decimal('0.070')       # 7.0%
    high_risk_premium: Decimal = Decimal('0.120')  # 12.0%

    # On-chain behavior adjustments
    excellent_onchain_discount: Decimal = Decimal('0.005')  # -0.5%
    good_onchain_discount: Decimal = Decimal('0.002')       # -0.2%
    poor_onchain_penalty: Decimal = Decimal('0.015')        # +1.5%


@dataclass
class CrossChainScoringConfig:
    """Configuration for cross-chain credit analysis."""
    enabled_chains: List[str] = field(default_factory=lambda: [
        'ethereum', 'polygon', 'avalanche', 'fantom'
    ])

    chain_weights: Dict[str, float] = field(default_factory=lambda: {
        'ethereum': 0.4,
        'polygon': 0.2,
        'avalanche': 0.2,
        'fantom': 0.2
    })

    cross_chain_bonus: float = 0.05
    min_cross_chain_activity: int = 5


@dataclass
class RiskPremiumConfig:
    """Main configuration class for risk premium assessment."""
    credit_scoring_weights: CreditScoringWeights = field(default_factory=CreditScoringWeights)
    onchain_behavior_weights: OnChainBehaviorWeights = field(default_factory=OnChainBehaviorWeights)
    risk_thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    market_condition_factors: MarketConditionFactors = field(default_factory=MarketConditionFactors)
    algorand_specific_params: AlgorandSpecificParams = field(default_factory=AlgorandSpecificParams)
    risk_premium_rates: RiskPremiumRates = field(default_factory=RiskPremiumRates)
    cross_chain_scoring: CrossChainScoringConfig = field(default_factory=CrossChainScoringConfig)

    # API and data source configurations
    credit_bureau_api_key: Optional[str] = None
    algorand_indexer_url: str = "https://mainnet-idx.algonode.cloud"
    algorand_algod_url: str = "https://mainnet-api.algonode.cloud"

    # Caching and performance
    cache_duration_hours: int = 24
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30

    # Logging and monitoring
    enable_detailed_logging: bool = True
    log_sensitive_data: bool = False
    alert_on_high_risk: bool = True

    @classmethod
    def from_file(cls, config_path: str) -> 'RiskPremiumConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        # Create nested dataclass instances
        config = cls()

        if 'credit_scoring_weights' in config_data:
            config.credit_scoring_weights = CreditScoringWeights(**config_data['credit_scoring_weights'])

        if 'onchain_behavior_weights' in config_data:
            config.onchain_behavior_weights = OnChainBehaviorWeights(**config_data['onchain_behavior_weights'])

        if 'risk_thresholds' in config_data:
            config.risk_thresholds = RiskThresholds(**config_data['risk_thresholds'])

        if 'market_condition_factors' in config_data:
            config.market_condition_factors = MarketConditionFactors(**config_data['market_condition_factors'])

        if 'algorand_specific_params' in config_data:
            config.algorand_specific_params = AlgorandSpecificParams(**config_data['algorand_specific_params'])

        if 'risk_premium_rates' in config_data:
            rates_data = config_data['risk_premium_rates']
            # Convert string values to Decimal
            for key, value in rates_data.items():
                if isinstance(value, (str, float, int)):
                    rates_data[key] = Decimal(str(value))
            config.risk_premium_rates = RiskPremiumRates(**rates_data)

        if 'cross_chain_scoring' in config_data:
            config.cross_chain_scoring = CrossChainScoringConfig(**config_data['cross_chain_scoring'])

        # Set simple attributes
        for attr in ['credit_bureau_api_key', 'algorand_indexer_url', 'algorand_algod_url',
                    'cache_duration_hours', 'max_concurrent_requests', 'request_timeout_seconds',
                    'enable_detailed_logging', 'log_sensitive_data', 'alert_on_high_risk']:
            if attr in config_data:
                setattr(config, attr, config_data[attr])

        return config

    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        config_dict = self.to_dict()

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'credit_scoring_weights': {
                'payment_history': self.credit_scoring_weights.payment_history,
                'credit_utilization': self.credit_scoring_weights.credit_utilization,
                'credit_age': self.credit_scoring_weights.credit_age,
                'credit_mix': self.credit_scoring_weights.credit_mix,
                'new_credit': self.credit_scoring_weights.new_credit
            },
            'onchain_behavior_weights': {
                'wallet_age': self.onchain_behavior_weights.wallet_age,
                'transaction_volume': self.onchain_behavior_weights.transaction_volume,
                'defi_participation': self.onchain_behavior_weights.defi_participation,
                'governance_voting': self.onchain_behavior_weights.governance_voting,
                'staking_history': self.onchain_behavior_weights.staking_history,
                'smart_contract_interactions': self.onchain_behavior_weights.smart_contract_interactions
            },
            'risk_thresholds': {
                'excellent_credit_score': self.risk_thresholds.excellent_credit_score,
                'good_credit_score': self.risk_thresholds.good_credit_score,
                'fair_credit_score': self.risk_thresholds.fair_credit_score,
                'poor_credit_score': self.risk_thresholds.poor_credit_score,
                'min_wallet_age_days': self.risk_thresholds.min_wallet_age_days,
                'min_transaction_count': self.risk_thresholds.min_transaction_count,
                'min_defi_participation_score': self.risk_thresholds.min_defi_participation_score,
                'high_risk_threshold': self.risk_thresholds.high_risk_threshold,
                'medium_risk_threshold': self.risk_thresholds.medium_risk_threshold,
                'low_risk_threshold': self.risk_thresholds.low_risk_threshold
            },
            'market_condition_factors': {
                'volatility_multiplier': self.market_condition_factors.volatility_multiplier,
                'liquidity_adjustment': self.market_condition_factors.liquidity_adjustment,
                'correlation_penalty': self.market_condition_factors.correlation_penalty,
                'market_stress_multiplier': self.market_condition_factors.market_stress_multiplier
            },
            'algorand_specific_params': {
                'governance_period_bonus': self.algorand_specific_params.governance_period_bonus,
                'consensus_participation_bonus': self.algorand_specific_params.consensus_participation_bonus,
                'asa_creation_bonus': self.algorand_specific_params.asa_creation_bonus,
                'smart_contract_deployment_bonus': self.algorand_specific_params.smart_contract_deployment_bonus,
                'min_governance_commitment_algo': self.algorand_specific_params.min_governance_commitment_algo,
                'min_staking_period_days': self.algorand_specific_params.min_staking_period_days,
                'defi_protocol_whitelist': self.algorand_specific_params.defi_protocol_whitelist
            },
            'risk_premium_rates': {
                'base_rate': str(self.risk_premium_rates.base_rate),
                'excellent_premium': str(self.risk_premium_rates.excellent_premium),
                'good_premium': str(self.risk_premium_rates.good_premium),
                'fair_premium': str(self.risk_premium_rates.fair_premium),
                'poor_premium': str(self.risk_premium_rates.poor_premium),
                'high_risk_premium': str(self.risk_premium_rates.high_risk_premium),
                'excellent_onchain_discount': str(self.risk_premium_rates.excellent_onchain_discount),
                'good_onchain_discount': str(self.risk_premium_rates.good_onchain_discount),
                'poor_onchain_penalty': str(self.risk_premium_rates.poor_onchain_penalty)
            },
            'cross_chain_scoring': {
                'enabled_chains': self.cross_chain_scoring.enabled_chains,
                'chain_weights': self.cross_chain_scoring.chain_weights,
                'cross_chain_bonus': self.cross_chain_scoring.cross_chain_bonus,
                'min_cross_chain_activity': self.cross_chain_scoring.min_cross_chain_activity
            },
            'credit_bureau_api_key': self.credit_bureau_api_key,
            'algorand_indexer_url': self.algorand_indexer_url,
            'algorand_algod_url': self.algorand_algod_url,
            'cache_duration_hours': self.cache_duration_hours,
            'max_concurrent_requests': self.max_concurrent_requests,
            'request_timeout_seconds': self.request_timeout_seconds,
            'enable_detailed_logging': self.enable_detailed_logging,
            'log_sensitive_data': self.log_sensitive_data,
            'alert_on_high_risk': self.alert_on_high_risk
        }


# Default configuration instance
DEFAULT_CONFIG = RiskPremiumConfig()