"""
Duration Risk Modeling Configuration

Defines parameters for term structure analysis, prepayment risk modeling,
and duration-based risk assessment for crypto-backed loans.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import json
import os


@dataclass
class TermStructureParams:
    """Term structure modeling parameters."""
    # Standard loan terms (in days)
    standard_terms: List[int] = field(default_factory=lambda: [30, 90, 180, 365, 730, 1095])

    # Yield curve construction
    interpolation_method: str = "cubic_spline"  # cubic_spline, linear, nelson_siegel
    smoothing_factor: float = 0.1
    extrapolation_method: str = "flat"  # flat, linear, exponential

    # Term structure risk factors
    short_term_weight: float = 0.3  # Weight for terms < 90 days
    medium_term_weight: float = 0.5  # Weight for 90-365 days
    long_term_weight: float = 0.2   # Weight for terms > 365 days

    # Base term structure spreads (annualized)
    term_spreads: Dict[int, Decimal] = field(default_factory=lambda: {
        30: Decimal('0.005'),   # 0.5% for 30 days
        90: Decimal('0.010'),   # 1.0% for 90 days
        180: Decimal('0.020'),  # 2.0% for 180 days
        365: Decimal('0.035'),  # 3.5% for 1 year
        730: Decimal('0.050'),  # 5.0% for 2 years
        1095: Decimal('0.065')  # 6.5% for 3 years
    })


@dataclass
class PrepaymentRiskParams:
    """Prepayment risk modeling parameters."""
    # Base prepayment probabilities by term
    base_prepayment_rates: Dict[int, float] = field(default_factory=lambda: {
        30: 0.15,   # 15% chance for 30-day loans
        90: 0.25,   # 25% chance for 90-day loans
        180: 0.35,  # 35% chance for 180-day loans
        365: 0.45,  # 45% chance for 1-year loans
        730: 0.55,  # 55% chance for 2-year loans
        1095: 0.65  # 65% chance for 3-year loans
    })

    # Factors affecting prepayment probability
    ltv_prepayment_factor: float = 1.5    # Higher LTV increases prepayment risk
    volatility_prepayment_factor: float = 2.0  # Higher volatility increases prepayment
    rate_differential_factor: float = 1.8     # Rate spread affects prepayment

    # Penalty structure for early prepayment
    prepayment_penalty_rates: Dict[str, Decimal] = field(default_factory=lambda: {
        "early_exit": Decimal('0.02'),     # 2% penalty for early exit
        "partial_prepay": Decimal('0.01'), # 1% penalty for partial prepayment
        "refinancing": Decimal('0.015')    # 1.5% penalty for refinancing
    })

    # Minimum prepayment amounts
    min_prepayment_percentage: float = 0.1  # 10% minimum prepayment
    max_prepayment_frequency: int = 4       # Max 4 prepayments per year


@dataclass
class DurationRiskParams:
    """Duration and interest rate sensitivity parameters."""
    # Duration calculation methods
    duration_method: str = "modified_duration"  # modified_duration, macaulay_duration, effective_duration

    # Interest rate sensitivity factors
    parallel_shift_sensitivity: float = 1.0    # Sensitivity to parallel yield curve shifts
    slope_change_sensitivity: float = 0.7      # Sensitivity to yield curve slope changes
    curvature_sensitivity: float = 0.4         # Sensitivity to yield curve curvature changes

    # Duration risk buckets and multipliers
    duration_buckets: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "very_short": (0.0, 0.25),    # 0-3 months
        "short": (0.25, 1.0),         # 3-12 months
        "medium": (1.0, 3.0),         # 1-3 years
        "long": (3.0, 7.0),           # 3-7 years
        "very_long": (7.0, 20.0)      # 7+ years
    })

    duration_risk_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "very_short": 1.0,
        "short": 1.2,
        "medium": 1.5,
        "long": 2.0,
        "very_long": 3.0
    })


@dataclass
class AssetLiabilityParams:
    """Asset-liability management parameters."""
    # Target duration matching tolerance
    duration_matching_tolerance: float = 0.5  # Years

    # Asset-liability buckets for matching
    al_buckets: List[str] = field(default_factory=lambda: [
        "overnight", "1_week", "1_month", "3_months",
        "6_months", "1_year", "2_years", "5_years"
    ])

    # Mismatch penalties
    duration_mismatch_penalty: Decimal = Decimal('0.005')  # 0.5% penalty per year of mismatch
    concentration_penalty: Decimal = Decimal('0.002')      # 0.2% penalty for concentration

    # Hedging parameters
    enable_duration_hedging: bool = True
    hedge_ratio_target: float = 0.8
    hedge_rebalance_threshold: float = 0.1


@dataclass
class CryptoSpecificParams:
    """Cryptocurrency-specific duration risk parameters."""
    # Crypto volatility adjustments
    algo_volatility_adjustment: float = 1.5
    btc_correlation_factor: float = 0.8
    eth_correlation_factor: float = 0.7

    # Staking and governance impact on duration
    staking_duration_bonus: float = 0.9    # Staked collateral has lower duration risk
    governance_lock_penalty: float = 1.3   # Governance locks increase duration risk

    # Defi protocol risk adjustments
    defi_duration_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "lending_protocols": 1.2,
        "dex_liquidity": 1.4,
        "yield_farming": 1.6,
        "governance_tokens": 1.8
    })

    # On-chain activity impact
    high_activity_duration_discount: float = 0.95
    dormant_wallet_duration_penalty: float = 1.15


@dataclass
class MarketRiskParams:
    """Market risk parameters affecting duration risk."""
    # Volatility regime adjustments
    low_volatility_multiplier: float = 0.9
    normal_volatility_multiplier: float = 1.0
    high_volatility_multiplier: float = 1.4
    extreme_volatility_multiplier: float = 2.0

    # Correlation adjustments
    low_correlation_discount: float = 0.95
    high_correlation_penalty: float = 1.25

    # Liquidity risk adjustments
    liquid_market_discount: float = 0.98
    illiquid_market_penalty: float = 1.3


@dataclass
class DurationRiskConfig:
    """Main configuration class for duration risk modeling."""
    term_structure: TermStructureParams = field(default_factory=TermStructureParams)
    prepayment_risk: PrepaymentRiskParams = field(default_factory=PrepaymentRiskParams)
    duration_risk: DurationRiskParams = field(default_factory=DurationRiskParams)
    asset_liability: AssetLiabilityParams = field(default_factory=AssetLiabilityParams)
    crypto_specific: CryptoSpecificParams = field(default_factory=CryptoSpecificParams)
    market_risk: MarketRiskParams = field(default_factory=MarketRiskParams)

    # Data sources and APIs
    yield_curve_source: str = "federal_reserve"  # federal_reserve, bloomberg, custom
    crypto_rate_source: str = "coingecko"        # coingecko, coinbase, binance

    # Model calibration
    historical_lookback_days: int = 365
    stress_test_scenarios: List[str] = field(default_factory=lambda: [
        "rate_shock_up_200bp", "rate_shock_down_100bp",
        "volatility_spike", "liquidity_crisis"
    ])

    # Computational parameters
    monte_carlo_simulations: int = 10000
    confidence_intervals: List[float] = field(default_factory=lambda: [0.95, 0.99])

    # Performance and caching
    cache_duration_hours: int = 4
    parallel_processing: bool = True
    max_worker_threads: int = 4

    @classmethod
    def from_file(cls, config_path: str) -> 'DurationRiskConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        config = cls()

        # Load nested configurations
        if 'term_structure' in config_data:
            ts_data = config_data['term_structure']
            if 'term_spreads' in ts_data:
                # Convert to Decimal
                ts_data['term_spreads'] = {
                    int(k): Decimal(str(v)) for k, v in ts_data['term_spreads'].items()
                }
            config.term_structure = TermStructureParams(**ts_data)

        if 'prepayment_risk' in config_data:
            pr_data = config_data['prepayment_risk']
            if 'prepayment_penalty_rates' in pr_data:
                # Convert to Decimal
                pr_data['prepayment_penalty_rates'] = {
                    k: Decimal(str(v)) for k, v in pr_data['prepayment_penalty_rates'].items()
                }
            config.prepayment_risk = PrepaymentRiskParams(**pr_data)

        if 'duration_risk' in config_data:
            config.duration_risk = DurationRiskParams(**config_data['duration_risk'])

        if 'asset_liability' in config_data:
            al_data = config_data['asset_liability']
            if 'duration_mismatch_penalty' in al_data:
                al_data['duration_mismatch_penalty'] = Decimal(str(al_data['duration_mismatch_penalty']))
            if 'concentration_penalty' in al_data:
                al_data['concentration_penalty'] = Decimal(str(al_data['concentration_penalty']))
            config.asset_liability = AssetLiabilityParams(**al_data)

        if 'crypto_specific' in config_data:
            config.crypto_specific = CryptoSpecificParams(**config_data['crypto_specific'])

        if 'market_risk' in config_data:
            config.market_risk = MarketRiskParams(**config_data['market_risk'])

        # Set simple attributes
        for attr in ['yield_curve_source', 'crypto_rate_source', 'historical_lookback_days',
                    'stress_test_scenarios', 'monte_carlo_simulations', 'confidence_intervals',
                    'cache_duration_hours', 'parallel_processing', 'max_worker_threads']:
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
            'term_structure': {
                'standard_terms': self.term_structure.standard_terms,
                'interpolation_method': self.term_structure.interpolation_method,
                'smoothing_factor': self.term_structure.smoothing_factor,
                'extrapolation_method': self.term_structure.extrapolation_method,
                'short_term_weight': self.term_structure.short_term_weight,
                'medium_term_weight': self.term_structure.medium_term_weight,
                'long_term_weight': self.term_structure.long_term_weight,
                'term_spreads': {k: str(v) for k, v in self.term_structure.term_spreads.items()}
            },
            'prepayment_risk': {
                'base_prepayment_rates': self.prepayment_risk.base_prepayment_rates,
                'ltv_prepayment_factor': self.prepayment_risk.ltv_prepayment_factor,
                'volatility_prepayment_factor': self.prepayment_risk.volatility_prepayment_factor,
                'rate_differential_factor': self.prepayment_risk.rate_differential_factor,
                'prepayment_penalty_rates': {k: str(v) for k, v in self.prepayment_risk.prepayment_penalty_rates.items()},
                'min_prepayment_percentage': self.prepayment_risk.min_prepayment_percentage,
                'max_prepayment_frequency': self.prepayment_risk.max_prepayment_frequency
            },
            'duration_risk': {
                'duration_method': self.duration_risk.duration_method,
                'parallel_shift_sensitivity': self.duration_risk.parallel_shift_sensitivity,
                'slope_change_sensitivity': self.duration_risk.slope_change_sensitivity,
                'curvature_sensitivity': self.duration_risk.curvature_sensitivity,
                'duration_buckets': self.duration_risk.duration_buckets,
                'duration_risk_multipliers': self.duration_risk.duration_risk_multipliers
            },
            'asset_liability': {
                'duration_matching_tolerance': self.asset_liability.duration_matching_tolerance,
                'al_buckets': self.asset_liability.al_buckets,
                'duration_mismatch_penalty': str(self.asset_liability.duration_mismatch_penalty),
                'concentration_penalty': str(self.asset_liability.concentration_penalty),
                'enable_duration_hedging': self.asset_liability.enable_duration_hedging,
                'hedge_ratio_target': self.asset_liability.hedge_ratio_target,
                'hedge_rebalance_threshold': self.asset_liability.hedge_rebalance_threshold
            },
            'crypto_specific': {
                'algo_volatility_adjustment': self.crypto_specific.algo_volatility_adjustment,
                'btc_correlation_factor': self.crypto_specific.btc_correlation_factor,
                'eth_correlation_factor': self.crypto_specific.eth_correlation_factor,
                'staking_duration_bonus': self.crypto_specific.staking_duration_bonus,
                'governance_lock_penalty': self.crypto_specific.governance_lock_penalty,
                'defi_duration_multipliers': self.crypto_specific.defi_duration_multipliers,
                'high_activity_duration_discount': self.crypto_specific.high_activity_duration_discount,
                'dormant_wallet_duration_penalty': self.crypto_specific.dormant_wallet_duration_penalty
            },
            'market_risk': {
                'low_volatility_multiplier': self.market_risk.low_volatility_multiplier,
                'normal_volatility_multiplier': self.market_risk.normal_volatility_multiplier,
                'high_volatility_multiplier': self.market_risk.high_volatility_multiplier,
                'extreme_volatility_multiplier': self.market_risk.extreme_volatility_multiplier,
                'low_correlation_discount': self.market_risk.low_correlation_discount,
                'high_correlation_penalty': self.market_risk.high_correlation_penalty,
                'liquid_market_discount': self.market_risk.liquid_market_discount,
                'illiquid_market_penalty': self.market_risk.illiquid_market_penalty
            },
            'yield_curve_source': self.yield_curve_source,
            'crypto_rate_source': self.crypto_rate_source,
            'historical_lookback_days': self.historical_lookback_days,
            'stress_test_scenarios': self.stress_test_scenarios,
            'monte_carlo_simulations': self.monte_carlo_simulations,
            'confidence_intervals': self.confidence_intervals,
            'cache_duration_hours': self.cache_duration_hours,
            'parallel_processing': self.parallel_processing,
            'max_worker_threads': self.max_worker_threads
        }


# Default configuration instance
DEFAULT_DURATION_CONFIG = DurationRiskConfig()