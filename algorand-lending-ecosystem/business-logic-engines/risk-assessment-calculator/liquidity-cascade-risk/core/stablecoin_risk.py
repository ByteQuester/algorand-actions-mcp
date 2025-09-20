"""
Stablecoin Risk Analyzer - Advanced stablecoin depeg risk and stability analysis

This module provides comprehensive analysis of stablecoin stability mechanisms,
depeg risk detection, and cross-stablecoin contagion effects in the Algorand ecosystem.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path
import math
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StablecoinType(Enum):
    """Types of stablecoin backing mechanisms"""
    FIAT_BACKED = "fiat_backed"
    CRYPTO_BACKED = "crypto_backed"
    ALGORITHMIC = "algorithmic"
    HYBRID = "hybrid"

class DepegSeverity(Enum):
    """Severity levels of depegging events"""
    MINOR = "minor"      # <1% depeg
    MODERATE = "moderate"  # 1-3% depeg
    SEVERE = "severe"    # 3-5% depeg
    CRITICAL = "critical"  # >5% depeg

class StabilityMechanism(Enum):
    """Stability mechanisms used by stablecoins"""
    RESERVES = "reserves"
    ARBITRAGE = "arbitrage"
    ALGORITHMIC = "algorithmic"
    GOVERNANCE = "governance"
    ELASTIC_SUPPLY = "elastic_supply"

@dataclass
class StablecoinProfile:
    """Profile of a stablecoin's characteristics"""
    symbol: str
    name: str
    stablecoin_type: StablecoinType
    target_peg: float
    tolerance: float
    backing_assets: List[str]
    reserve_ratio: float
    stability_mechanisms: List[StabilityMechanism]
    total_supply: float
    market_cap: float
    daily_volume: float
    redemption_fee: float
    minting_fee: float

@dataclass
class DepegEvent:
    """Depegging event data"""
    stablecoin: str
    timestamp: datetime
    price: float
    target_peg: float
    depeg_magnitude: float
    depeg_percentage: float
    severity: DepegSeverity
    duration_minutes: float
    trigger_events: List[str]
    market_conditions: Dict[str, float]

@dataclass
class StabilityAnalysis:
    """Stability analysis result"""
    stablecoin: str
    current_price: float
    target_peg: float
    current_depeg: float
    stability_score: float  # 0-1, 1 = most stable
    risk_level: str
    time_to_recovery: float  # hours
    stress_test_results: Dict[str, float]
    arbitrage_efficiency: float
    reserve_adequacy: float

@dataclass
class ContagionRisk:
    """Stablecoin contagion risk assessment"""
    source_stablecoin: str
    affected_stablecoins: List[str]
    contagion_probability: float
    spillover_magnitude: Dict[str, float]
    recovery_correlation: float

class StablecoinRiskAnalyzer:
    """
    Advanced stablecoin risk analyzer that monitors stability, detects depeg events,
    and assesses contagion risks across the Algorand stablecoin ecosystem.
    """

    def __init__(self, config_path: str = None):
        """Initialize the stablecoin risk analyzer"""
        self.config = self._load_config(config_path)
        self.stablecoin_config = self.config['stablecoin']

        # Initialize stablecoin profiles
        self.stablecoin_profiles: Dict[str, StablecoinProfile] = {}
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.depeg_history: List[DepegEvent] = []
        self.stability_history: List[StabilityAnalysis] = []

        # Risk parameters
        self.depeg_warning = self.stablecoin_config['depeg_warning']
        self.depeg_critical = self.stablecoin_config['depeg_critical']
        self.depeg_severe = self.stablecoin_config['depeg_severe']

        self._initialize_stablecoin_profiles()

        logger.info("Stablecoin Risk Analyzer initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_stablecoin_profiles(self):
        """Initialize profiles for major Algorand stablecoins"""
        stablecoins = {
            'USDC': StablecoinProfile(
                symbol='USDC',
                name='USD Coin',
                stablecoin_type=StablecoinType.FIAT_BACKED,
                target_peg=1.0,
                tolerance=0.002,
                backing_assets=['USD'],
                reserve_ratio=1.0,
                stability_mechanisms=[StabilityMechanism.RESERVES, StabilityMechanism.ARBITRAGE],
                total_supply=100_000_000,
                market_cap=100_000_000,
                daily_volume=5_000_000,
                redemption_fee=0.0,
                minting_fee=0.0
            ),
            'USDT': StablecoinProfile(
                symbol='USDT',
                name='Tether',
                stablecoin_type=StablecoinType.FIAT_BACKED,
                target_peg=1.0,
                tolerance=0.003,
                backing_assets=['USD', 'Treasuries', 'Commercial Paper'],
                reserve_ratio=0.95,
                stability_mechanisms=[StabilityMechanism.RESERVES, StabilityMechanism.ARBITRAGE],
                total_supply=50_000_000,
                market_cap=50_000_000,
                daily_volume=2_000_000,
                redemption_fee=0.001,
                minting_fee=0.001
            ),
            'GARD': StablecoinProfile(
                symbol='GARD',
                name='Gard Stablecoin',
                stablecoin_type=StablecoinType.ALGORITHMIC,
                target_peg=1.0,
                tolerance=0.005,
                backing_assets=['ALGO', 'USDC'],
                reserve_ratio=1.5,
                stability_mechanisms=[
                    StabilityMechanism.ALGORITHMIC,
                    StabilityMechanism.ARBITRAGE,
                    StabilityMechanism.ELASTIC_SUPPLY
                ],
                total_supply=10_000_000,
                market_cap=10_000_000,
                daily_volume=500_000,
                redemption_fee=0.002,
                minting_fee=0.002
            ),
            'STBL': StablecoinProfile(
                symbol='STBL',
                name='Stable Asset',
                stablecoin_type=StablecoinType.CRYPTO_BACKED,
                target_peg=1.0,
                tolerance=0.004,
                backing_assets=['ALGO', 'GOBTC', 'GOETH'],
                reserve_ratio=1.2,
                stability_mechanisms=[
                    StabilityMechanism.RESERVES,
                    StabilityMechanism.ARBITRAGE,
                    StabilityMechanism.GOVERNANCE
                ],
                total_supply=5_000_000,
                market_cap=5_000_000,
                daily_volume=200_000,
                redemption_fee=0.003,
                minting_fee=0.003
            )
        }

        self.stablecoin_profiles = stablecoins

        # Initialize configuration data
        for symbol, config_data in self.stablecoin_config['coins'].items():
            if symbol.upper() in self.stablecoin_profiles:
                profile = self.stablecoin_profiles[symbol.upper()]
                profile.target_peg = config_data['target_peg']
                profile.tolerance = config_data['tolerance']
                profile.reserve_ratio = config_data['reserve_ratio']

    async def analyze_stablecoin_stability(
        self,
        stablecoin: str,
        lookback_hours: int = 24
    ) -> StabilityAnalysis:
        """
        Analyze the stability of a specific stablecoin

        Args:
            stablecoin: Stablecoin symbol (e.g., 'USDC', 'GARD')
            lookback_hours: Hours of historical data to analyze

        Returns:
            Comprehensive stability analysis
        """
        logger.info(f"Analyzing stability for {stablecoin}")

        if stablecoin not in self.stablecoin_profiles:
            raise ValueError(f"No profile available for {stablecoin}")

        profile = self.stablecoin_profiles[stablecoin]

        # Get price data
        price_data = await self._get_price_data(stablecoin, lookback_hours)

        if price_data.empty:
            raise ValueError(f"No price data available for {stablecoin}")

        current_price = price_data['price'].iloc[-1]
        current_depeg = abs(current_price - profile.target_peg)

        # Calculate stability metrics
        stability_score = self._calculate_stability_score(price_data, profile)
        risk_level = self._assess_risk_level(current_depeg, profile)
        time_to_recovery = self._estimate_recovery_time(price_data, profile)
        arbitrage_efficiency = self._calculate_arbitrage_efficiency(price_data, profile)
        reserve_adequacy = self._assess_reserve_adequacy(profile)

        # Run stress tests
        stress_test_results = await self._run_stability_stress_tests(stablecoin, profile)

        analysis = StabilityAnalysis(
            stablecoin=stablecoin,
            current_price=current_price,
            target_peg=profile.target_peg,
            current_depeg=current_depeg,
            stability_score=stability_score,
            risk_level=risk_level,
            time_to_recovery=time_to_recovery,
            stress_test_results=stress_test_results,
            arbitrage_efficiency=arbitrage_efficiency,
            reserve_adequacy=reserve_adequacy
        )

        self.stability_history.append(analysis)

        return analysis

    async def _get_price_data(self, stablecoin: str, lookback_hours: int) -> pd.DataFrame:
        """Get or generate price data for stablecoin"""
        # In production, this would fetch real price data
        # For now, generate realistic mock data

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)

        # Generate hourly timestamps
        timestamps = pd.date_range(start=start_time, end=end_time, freq='H')

        # Get profile
        profile = self.stablecoin_profiles[stablecoin]

        # Generate realistic price series around the peg
        np.random.seed(42 + hash(stablecoin) % 100)

        prices = []
        current_price = profile.target_peg

        for _ in timestamps:
            # Mean reversion to peg with some noise
            mean_reversion = (profile.target_peg - current_price) * 0.1
            noise = np.random.normal(0, profile.tolerance * 0.3)

            # Occasional larger deviations for algorithmic stablecoins
            if profile.stablecoin_type == StablecoinType.ALGORITHMIC:
                if np.random.random() < 0.02:  # 2% chance of larger deviation
                    noise += np.random.normal(0, profile.tolerance * 2)

            price_change = mean_reversion + noise
            current_price += price_change

            # Ensure price stays positive
            current_price = max(current_price, 0.001)

            prices.append(current_price)

        return pd.DataFrame({
            'timestamp': timestamps,
            'price': prices
        }).set_index('timestamp')

    def _calculate_stability_score(
        self,
        price_data: pd.DataFrame,
        profile: StablecoinProfile
    ) -> float:
        """Calculate stability score (0-1, higher = more stable)"""
        prices = price_data['price']

        # Calculate various stability metrics
        # 1. Price volatility
        returns = prices.pct_change().dropna()
        volatility = returns.std()

        # 2. Deviation from peg
        deviations = abs(prices - profile.target_peg)
        avg_deviation = deviations.mean()
        max_deviation = deviations.max()

        # 3. Time above/below tolerance
        tolerance_breaches = (deviations > profile.tolerance).sum() / len(deviations)

        # 4. Mean reversion speed
        mean_reversion_speed = self._calculate_mean_reversion_speed(prices, profile.target_peg)

        # Combine metrics into stability score
        volatility_score = max(0, 1 - volatility / (profile.tolerance * 5))
        deviation_score = max(0, 1 - avg_deviation / (profile.tolerance * 2))
        tolerance_score = max(0, 1 - tolerance_breaches * 2)
        reversion_score = min(1, mean_reversion_speed)

        stability_score = (
            volatility_score * 0.3 +
            deviation_score * 0.3 +
            tolerance_score * 0.2 +
            reversion_score * 0.2
        )

        return stability_score

    def _calculate_mean_reversion_speed(self, prices: pd.Series, target: float) -> float:
        """Calculate how quickly price reverts to peg"""
        deviations = prices - target
        # Calculate autocorrelation to measure mean reversion
        if len(deviations) > 1:
            autocorr = deviations.autocorr(lag=1)
            # Mean reversion speed is 1 - autocorrelation
            return max(0, 1 - autocorr) if not np.isnan(autocorr) else 0.5
        return 0.5

    def _assess_risk_level(self, current_depeg: float, profile: StablecoinProfile) -> str:
        """Assess current risk level based on depeg magnitude"""
        depeg_pct = current_depeg / profile.target_peg

        if depeg_pct <= profile.tolerance:
            return "LOW"
        elif depeg_pct <= self.depeg_warning:
            return "MEDIUM"
        elif depeg_pct <= self.depeg_critical:
            return "HIGH"
        else:
            return "CRITICAL"

    def _estimate_recovery_time(
        self,
        price_data: pd.DataFrame,
        profile: StablecoinProfile
    ) -> float:
        """Estimate time to recover to peg (in hours)"""
        current_price = price_data['price'].iloc[-1]
        depeg_magnitude = abs(current_price - profile.target_peg)

        if depeg_magnitude <= profile.tolerance:
            return 0.0  # Already within tolerance

        # Base recovery time from config
        base_recovery = self.stablecoin_config['recovery_half_life'] / 3600  # Convert to hours

        # Adjust based on stablecoin type
        type_multipliers = {
            StablecoinType.FIAT_BACKED: 0.5,
            StablecoinType.CRYPTO_BACKED: 1.0,
            StablecoinType.ALGORITHMIC: 2.0,
            StablecoinType.HYBRID: 1.5
        }

        type_multiplier = type_multipliers.get(profile.stablecoin_type, 1.0)

        # Adjust based on depeg magnitude
        magnitude_multiplier = 1 + (depeg_magnitude / profile.tolerance)

        # Adjust based on arbitrage efficiency
        arbitrage_efficiency = self.stablecoin_config['arbitrage_efficiency']
        arbitrage_multiplier = 2 - arbitrage_efficiency  # Higher efficiency = faster recovery

        recovery_time = base_recovery * type_multiplier * magnitude_multiplier * arbitrage_multiplier

        return min(recovery_time, self.stablecoin_config['max_recovery_time'] / 3600)

    def _calculate_arbitrage_efficiency(
        self,
        price_data: pd.DataFrame,
        profile: StablecoinProfile
    ) -> float:
        """Calculate arbitrage efficiency (0-1, higher = more efficient)"""
        prices = price_data['price']

        # Calculate how quickly price movements are corrected
        deviations = abs(prices - profile.target_peg)
        price_changes = prices.diff().abs()

        # Efficiency is inversely related to persistent deviations
        if len(deviations) > 1:
            # Calculate correlation between deviations and subsequent price changes
            if deviations.std() > 0:
                correction_correlation = deviations[:-1].corr(price_changes[1:])
                efficiency = max(0, correction_correlation) if not np.isnan(correction_correlation) else 0.5
            else:
                efficiency = 1.0  # Perfect stability
        else:
            efficiency = 0.5

        # Adjust for fees (higher fees reduce efficiency)
        fee_impact = 1 - (profile.redemption_fee + profile.minting_fee)

        return efficiency * fee_impact

    def _assess_reserve_adequacy(self, profile: StablecoinProfile) -> float:
        """Assess reserve adequacy (0-1, higher = more adequate)"""
        if profile.stablecoin_type == StablecoinType.FIAT_BACKED:
            # For fiat-backed, reserve ratio should be close to 1.0
            adequacy = min(1.0, profile.reserve_ratio)
        elif profile.stablecoin_type == StablecoinType.CRYPTO_BACKED:
            # For crypto-backed, higher ratios are better due to volatility
            adequacy = min(1.0, (profile.reserve_ratio - 1.0) / 0.5)  # Normalize to 1.5 = 100%
        elif profile.stablecoin_type == StablecoinType.ALGORITHMIC:
            # For algorithmic, assess based on backing mechanism strength
            adequacy = min(1.0, profile.reserve_ratio / 2.0)  # Normalize to 2.0 = 100%
        else:
            adequacy = 0.5  # Default for unknown types

        return max(0, adequacy)

    async def _run_stability_stress_tests(
        self,
        stablecoin: str,
        profile: StablecoinProfile
    ) -> Dict[str, float]:
        """Run stress tests on stablecoin stability"""
        stress_scenarios = {
            'market_crash': {'market_shock': -0.3, 'volume_spike': 5.0},
            'liquidity_crisis': {'liquidity_reduction': 0.8, 'spread_increase': 10.0},
            'backing_asset_crash': {'backing_shock': -0.5},
            'bank_run': {'redemption_pressure': 0.3},
            'arbitrage_failure': {'arbitrage_efficiency': 0.1}
        }

        stress_results = {}

        for scenario_name, scenario_params in stress_scenarios.items():
            depeg_magnitude = self._simulate_stress_scenario(profile, scenario_params)
            stress_results[scenario_name] = depeg_magnitude

        return stress_results

    def _simulate_stress_scenario(
        self,
        profile: StablecoinProfile,
        scenario_params: Dict[str, float]
    ) -> float:
        """Simulate stress scenario and return expected depeg magnitude"""
        base_depeg = 0.01  # 1% base depeg under stress

        # Adjust based on stablecoin type
        if profile.stablecoin_type == StablecoinType.FIAT_BACKED:
            type_resilience = 0.5  # More resilient
        elif profile.stablecoin_type == StablecoinType.CRYPTO_BACKED:
            type_resilience = 1.0  # Moderate resilience
        elif profile.stablecoin_type == StablecoinType.ALGORITHMIC:
            type_resilience = 2.0  # Less resilient
        else:
            type_resilience = 1.5

        # Apply scenario-specific stress factors
        stress_factor = 1.0

        if 'market_shock' in scenario_params:
            stress_factor *= abs(scenario_params['market_shock']) * 2

        if 'liquidity_reduction' in scenario_params:
            stress_factor *= scenario_params['liquidity_reduction'] * 1.5

        if 'backing_shock' in scenario_params:
            stress_factor *= abs(scenario_params['backing_shock']) * 1.5

        if 'redemption_pressure' in scenario_params:
            stress_factor *= scenario_params['redemption_pressure'] * 3

        if 'arbitrage_efficiency' in scenario_params:
            stress_factor *= (1 - scenario_params['arbitrage_efficiency']) * 2

        # Adjust for reserve adequacy
        reserve_buffer = max(0.1, profile.reserve_ratio - 1.0)
        reserve_protection = 1 / (1 + reserve_buffer)

        expected_depeg = base_depeg * type_resilience * stress_factor * reserve_protection

        return min(expected_depeg, 0.2)  # Cap at 20% depeg

    async def detect_depeg_events(
        self,
        stablecoins: List[str] = None,
        monitoring_hours: int = 24
    ) -> List[DepegEvent]:
        """
        Detect depegging events across stablecoins

        Args:
            stablecoins: List of stablecoins to monitor
            monitoring_hours: Hours to monitor for events

        Returns:
            List of detected depeg events
        """
        if stablecoins is None:
            stablecoins = list(self.stablecoin_profiles.keys())

        logger.info(f"Detecting depeg events for {len(stablecoins)} stablecoins")

        depeg_events = []

        for stablecoin in stablecoins:
            profile = self.stablecoin_profiles[stablecoin]
            price_data = await self._get_price_data(stablecoin, monitoring_hours)

            # Detect depeg events in price series
            events = self._identify_depeg_events(price_data, profile)
            depeg_events.extend(events)

        self.depeg_history.extend(depeg_events)

        return depeg_events

    def _identify_depeg_events(
        self,
        price_data: pd.DataFrame,
        profile: StablecoinProfile
    ) -> List[DepegEvent]:
        """Identify depeg events in price data"""
        events = []
        prices = price_data['price']

        # Calculate deviations from peg
        deviations = abs(prices - profile.target_peg)
        depeg_threshold = profile.tolerance

        # Find periods where price is outside tolerance
        outside_tolerance = deviations > depeg_threshold

        if not outside_tolerance.any():
            return events

        # Group consecutive depeg periods
        depeg_periods = self._find_consecutive_periods(outside_tolerance)

        for start_idx, end_idx in depeg_periods:
            start_time = prices.index[start_idx]
            end_time = prices.index[end_idx]
            duration = (end_time - start_time).total_seconds() / 60  # minutes

            # Get maximum depeg during this period
            period_deviations = deviations.iloc[start_idx:end_idx+1]
            max_depeg = period_deviations.max()
            max_depeg_idx = period_deviations.idxmax()
            max_depeg_price = prices.loc[max_depeg_idx]

            # Determine severity
            depeg_pct = max_depeg / profile.target_peg
            severity = self._classify_depeg_severity(depeg_pct)

            # Identify potential triggers
            trigger_events = self._identify_trigger_events(
                price_data, start_idx, profile
            )

            # Get market conditions during event
            market_conditions = self._get_market_conditions_during_event(
                start_time, end_time
            )

            event = DepegEvent(
                stablecoin=profile.symbol,
                timestamp=start_time,
                price=max_depeg_price,
                target_peg=profile.target_peg,
                depeg_magnitude=max_depeg,
                depeg_percentage=depeg_pct,
                severity=severity,
                duration_minutes=duration,
                trigger_events=trigger_events,
                market_conditions=market_conditions
            )

            events.append(event)

        return events

    def _find_consecutive_periods(self, boolean_series: pd.Series) -> List[Tuple[int, int]]:
        """Find consecutive True periods in boolean series"""
        periods = []
        start_idx = None

        for i, value in enumerate(boolean_series):
            if value and start_idx is None:
                start_idx = i
            elif not value and start_idx is not None:
                periods.append((start_idx, i - 1))
                start_idx = None

        # Handle case where series ends with True
        if start_idx is not None:
            periods.append((start_idx, len(boolean_series) - 1))

        return periods

    def _classify_depeg_severity(self, depeg_pct: float) -> DepegSeverity:
        """Classify depeg severity"""
        if depeg_pct < 0.01:
            return DepegSeverity.MINOR
        elif depeg_pct < 0.03:
            return DepegSeverity.MODERATE
        elif depeg_pct < 0.05:
            return DepegSeverity.SEVERE
        else:
            return DepegSeverity.CRITICAL

    def _identify_trigger_events(
        self,
        price_data: pd.DataFrame,
        event_start_idx: int,
        profile: StablecoinProfile
    ) -> List[str]:
        """Identify potential trigger events for depeg"""
        triggers = []

        # Look at price action before event
        lookback = min(6, event_start_idx)  # 6 hours or less
        if lookback > 0:
            pre_event_prices = price_data['price'].iloc[event_start_idx-lookback:event_start_idx]

            # Check for sudden price movements
            price_changes = pre_event_prices.pct_change().abs()
            if price_changes.max() > 0.02:  # >2% sudden change
                triggers.append("sudden_price_movement")

            # Check for volume spikes (would need volume data in practice)
            # For now, simulate based on price volatility
            volatility = price_changes.std()
            if volatility > profile.tolerance:
                triggers.append("volume_spike")

        # Check for specific patterns based on stablecoin type
        if profile.stablecoin_type == StablecoinType.ALGORITHMIC:
            triggers.append("algorithmic_rebalancing")
        elif profile.stablecoin_type == StablecoinType.CRYPTO_BACKED:
            triggers.append("collateral_volatility")

        return triggers if triggers else ["unknown"]

    def _get_market_conditions_during_event(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get market conditions during depeg event"""
        # In practice, this would fetch real market data
        # For now, simulate realistic conditions
        return {
            'market_volatility': np.random.uniform(0.2, 0.6),
            'trading_volume_ratio': np.random.uniform(0.5, 3.0),
            'spread_increase': np.random.uniform(1.0, 5.0),
            'correlation_spike': np.random.uniform(0.1, 0.4)
        }

    async def analyze_contagion_risk(
        self,
        source_stablecoin: str,
        depeg_magnitude: float
    ) -> ContagionRisk:
        """
        Analyze contagion risk from one stablecoin to others

        Args:
            source_stablecoin: Stablecoin experiencing depeg
            depeg_magnitude: Magnitude of the depeg

        Returns:
            Contagion risk assessment
        """
        logger.info(f"Analyzing contagion risk from {source_stablecoin} depeg")

        if source_stablecoin not in self.stablecoin_profiles:
            raise ValueError(f"Unknown stablecoin: {source_stablecoin}")

        source_profile = self.stablecoin_profiles[source_stablecoin]
        affected_stablecoins = []
        spillover_magnitudes = {}

        # Analyze potential spillover to each other stablecoin
        for target_coin, target_profile in self.stablecoin_profiles.items():
            if target_coin == source_stablecoin:
                continue

            # Calculate contagion probability and spillover magnitude
            contagion_prob = self._calculate_contagion_probability(
                source_profile, target_profile, depeg_magnitude
            )

            spillover_magnitude = self._calculate_spillover_magnitude(
                source_profile, target_profile, depeg_magnitude, contagion_prob
            )

            if contagion_prob > 0.2:  # 20% threshold
                affected_stablecoins.append(target_coin)
                spillover_magnitudes[target_coin] = spillover_magnitude

        # Calculate overall contagion probability
        overall_contagion_prob = self._calculate_overall_contagion_probability(
            source_profile, affected_stablecoins, depeg_magnitude
        )

        # Estimate recovery correlation
        recovery_correlation = self._estimate_recovery_correlation(
            source_profile, affected_stablecoins
        )

        return ContagionRisk(
            source_stablecoin=source_stablecoin,
            affected_stablecoins=affected_stablecoins,
            contagion_probability=overall_contagion_prob,
            spillover_magnitude=spillover_magnitudes,
            recovery_correlation=recovery_correlation
        )

    def _calculate_contagion_probability(
        self,
        source_profile: StablecoinProfile,
        target_profile: StablecoinProfile,
        depeg_magnitude: float
    ) -> float:
        """Calculate probability of contagion between stablecoins"""

        # Base contagion probability depends on depeg magnitude
        base_prob = min(depeg_magnitude * 2, 0.8)  # Cap at 80%

        # Similarity factors increase contagion risk
        similarity_factors = []

        # Same backing type
        if source_profile.stablecoin_type == target_profile.stablecoin_type:
            similarity_factors.append(0.3)

        # Shared backing assets
        source_assets = set(source_profile.backing_assets)
        target_assets = set(target_profile.backing_assets)
        shared_ratio = len(source_assets & target_assets) / len(source_assets | target_assets)
        similarity_factors.append(shared_ratio * 0.2)

        # Similar stability mechanisms
        source_mechanisms = set(source_profile.stability_mechanisms)
        target_mechanisms = set(target_profile.stability_mechanisms)
        mechanism_similarity = len(source_mechanisms & target_mechanisms) / len(source_mechanisms | target_mechanisms)
        similarity_factors.append(mechanism_similarity * 0.1)

        # Size factor (larger stablecoins can affect smaller ones more)
        size_factor = min(source_profile.market_cap / target_profile.market_cap, 2.0) * 0.1

        # Calculate final probability
        total_similarity = sum(similarity_factors) + size_factor
        contagion_prob = base_prob * (1 + total_similarity)

        return min(contagion_prob, 0.95)  # Cap at 95%

    def _calculate_spillover_magnitude(
        self,
        source_profile: StablecoinProfile,
        target_profile: StablecoinProfile,
        depeg_magnitude: float,
        contagion_prob: float
    ) -> float:
        """Calculate expected spillover magnitude"""

        # Base spillover is a fraction of original depeg
        base_spillover = depeg_magnitude * contagion_prob * 0.5

        # Adjust based on target stablecoin's resilience
        resilience_factors = {
            StablecoinType.FIAT_BACKED: 0.3,
            StablecoinType.CRYPTO_BACKED: 0.6,
            StablecoinType.ALGORITHMIC: 1.0,
            StablecoinType.HYBRID: 0.8
        }

        target_resilience = resilience_factors.get(target_profile.stablecoin_type, 1.0)
        adjusted_spillover = base_spillover * target_resilience

        # Adjust for reserve adequacy
        reserve_protection = min(1.0, target_profile.reserve_ratio)
        final_spillover = adjusted_spillover / reserve_protection

        return min(final_spillover, depeg_magnitude * 0.8)  # Cap at 80% of original

    def _calculate_overall_contagion_probability(
        self,
        source_profile: StablecoinProfile,
        affected_stablecoins: List[str],
        depeg_magnitude: float
    ) -> float:
        """Calculate overall contagion probability"""
        if not affected_stablecoins:
            return 0.0

        # Base probability from number of affected coins
        breadth_factor = len(affected_stablecoins) / len(self.stablecoin_profiles)

        # Magnitude factor
        magnitude_factor = min(depeg_magnitude * 3, 1.0)

        # Source importance factor
        source_importance = source_profile.market_cap / sum(
            p.market_cap for p in self.stablecoin_profiles.values()
        )

        overall_prob = (breadth_factor + magnitude_factor + source_importance) / 3

        return min(overall_prob, 0.9)

    def _estimate_recovery_correlation(
        self,
        source_profile: StablecoinProfile,
        affected_stablecoins: List[str]
    ) -> float:
        """Estimate correlation in recovery times"""
        if not affected_stablecoins:
            return 0.0

        # Recovery correlation depends on shared mechanisms and backing
        correlations = []

        for affected_coin in affected_stablecoins:
            affected_profile = self.stablecoin_profiles[affected_coin]

            # Mechanism correlation
            source_mechanisms = set(source_profile.stability_mechanisms)
            affected_mechanisms = set(affected_profile.stability_mechanisms)
            mechanism_corr = len(source_mechanisms & affected_mechanisms) / len(source_mechanisms | affected_mechanisms)

            # Backing correlation
            source_assets = set(source_profile.backing_assets)
            affected_assets = set(affected_profile.backing_assets)
            backing_corr = len(source_assets & affected_assets) / len(source_assets | affected_assets)

            # Type correlation
            type_corr = 1.0 if source_profile.stablecoin_type == affected_profile.stablecoin_type else 0.3

            coin_correlation = (mechanism_corr + backing_corr + type_corr) / 3
            correlations.append(coin_correlation)

        return np.mean(correlations) if correlations else 0.0

    async def monitor_ecosystem_stability(self) -> Dict[str, Any]:
        """Monitor overall stablecoin ecosystem stability"""
        logger.info("Monitoring ecosystem-wide stablecoin stability")

        ecosystem_analysis = {}
        individual_analyses = {}

        # Analyze each stablecoin
        for stablecoin in self.stablecoin_profiles.keys():
            analysis = await self.analyze_stablecoin_stability(stablecoin)
            individual_analyses[stablecoin] = analysis

        # Calculate ecosystem-wide metrics
        total_market_cap = sum(p.market_cap for p in self.stablecoin_profiles.values())

        weighted_stability = sum(
            analysis.stability_score * self.stablecoin_profiles[stablecoin].market_cap
            for stablecoin, analysis in individual_analyses.items()
        ) / total_market_cap

        # Count coins at various risk levels
        risk_distribution = {}
        for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            count = sum(1 for analysis in individual_analyses.values() if analysis.risk_level == level)
            risk_distribution[level] = count

        # Detect systemic risks
        systemic_risks = self._detect_systemic_risks(individual_analyses)

        # Calculate contagion vulnerability
        contagion_vulnerability = await self._assess_ecosystem_contagion_vulnerability(
            individual_analyses
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'individual_analyses': {k: v.__dict__ for k, v in individual_analyses.items()},
            'ecosystem_metrics': {
                'total_market_cap': total_market_cap,
                'weighted_stability_score': weighted_stability,
                'risk_distribution': risk_distribution,
                'systemic_risks': systemic_risks,
                'contagion_vulnerability': contagion_vulnerability
            },
            'alerts': self._generate_stability_alerts(individual_analyses, systemic_risks)
        }

    def _detect_systemic_risks(self, individual_analyses: Dict[str, StabilityAnalysis]) -> List[str]:
        """Detect ecosystem-wide systemic risks"""
        risks = []

        # Check for multiple high-risk stablecoins
        high_risk_count = sum(
            1 for analysis in individual_analyses.values()
            if analysis.risk_level in ["HIGH", "CRITICAL"]
        )

        if high_risk_count >= 2:
            risks.append("multiple_high_risk_stablecoins")

        # Check for concentration in single backing type
        type_distribution = {}
        for stablecoin, analysis in individual_analyses.items():
            profile = self.stablecoin_profiles[stablecoin]
            coin_type = profile.stablecoin_type.value

            market_cap = profile.market_cap
            if coin_type not in type_distribution:
                type_distribution[coin_type] = 0
            type_distribution[coin_type] += market_cap

        total_cap = sum(type_distribution.values())
        for coin_type, cap in type_distribution.items():
            if cap / total_cap > 0.7:  # >70% concentration
                risks.append(f"concentration_in_{coin_type}")

        # Check for correlated stress test failures
        failed_stress_tests = {}
        for stablecoin, analysis in individual_analyses.items():
            for scenario, depeg in analysis.stress_test_results.items():
                if depeg > 0.05:  # >5% depeg in stress test
                    if scenario not in failed_stress_tests:
                        failed_stress_tests[scenario] = 0
                    failed_stress_tests[scenario] += 1

        for scenario, failures in failed_stress_tests.items():
            if failures >= len(individual_analyses) / 2:  # >50% failure rate
                risks.append(f"widespread_{scenario}_vulnerability")

        return risks

    async def _assess_ecosystem_contagion_vulnerability(
        self,
        individual_analyses: Dict[str, StabilityAnalysis]
    ) -> Dict[str, float]:
        """Assess ecosystem vulnerability to contagion"""

        # Test contagion from each stablecoin
        contagion_scenarios = {}

        for source_coin in self.stablecoin_profiles.keys():
            # Simulate moderate depeg (3%)
            contagion_risk = await self.analyze_contagion_risk(source_coin, 0.03)

            affected_market_cap = sum(
                self.stablecoin_profiles[coin].market_cap
                for coin in contagion_risk.affected_stablecoins
            )

            total_market_cap = sum(p.market_cap for p in self.stablecoin_profiles.values())

            contagion_scenarios[source_coin] = {
                'affected_coins': len(contagion_risk.affected_stablecoins),
                'affected_market_cap_pct': affected_market_cap / total_market_cap,
                'contagion_probability': contagion_risk.contagion_probability
            }

        # Calculate overall vulnerability metrics
        max_affected_pct = max(
            scenario['affected_market_cap_pct'] for scenario in contagion_scenarios.values()
        )

        avg_contagion_prob = np.mean([
            scenario['contagion_probability'] for scenario in contagion_scenarios.values()
        ])

        return {
            'contagion_scenarios': contagion_scenarios,
            'max_affected_market_cap_pct': max_affected_pct,
            'avg_contagion_probability': avg_contagion_prob,
            'vulnerability_score': (max_affected_pct + avg_contagion_prob) / 2
        }

    def _generate_stability_alerts(
        self,
        individual_analyses: Dict[str, StabilityAnalysis],
        systemic_risks: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate stability alerts"""
        alerts = []

        # Individual stablecoin alerts
        for stablecoin, analysis in individual_analyses.items():
            if analysis.risk_level == "CRITICAL":
                alerts.append({
                    'type': 'critical_depeg_risk',
                    'stablecoin': stablecoin,
                    'current_depeg': analysis.current_depeg,
                    'message': f"{stablecoin} at critical depeg risk: {analysis.current_depeg:.3f} from peg"
                })
            elif analysis.risk_level == "HIGH":
                alerts.append({
                    'type': 'high_depeg_risk',
                    'stablecoin': stablecoin,
                    'current_depeg': analysis.current_depeg,
                    'message': f"{stablecoin} at high depeg risk: {analysis.current_depeg:.3f} from peg"
                })

        # Systemic risk alerts
        for risk in systemic_risks:
            alerts.append({
                'type': 'systemic_risk',
                'risk': risk,
                'message': f"Systemic risk detected: {risk.replace('_', ' ')}"
            })

        return alerts

    def get_stability_statistics(self) -> Dict[str, Any]:
        """Get historical stability statistics"""
        if not self.stability_history:
            return {"error": "No stability history available"}

        return {
            'total_analyses': len(self.stability_history),
            'depeg_events': len(self.depeg_history),
            'avg_stability_score': np.mean([s.stability_score for s in self.stability_history]),
            'stability_by_coin': self._calculate_stability_by_coin(),
            'depeg_frequency': self._calculate_depeg_frequency(),
            'severity_distribution': self._calculate_severity_distribution(),
            'recovery_time_stats': self._calculate_recovery_time_stats()
        }

    def _calculate_stability_by_coin(self) -> Dict[str, Dict[str, float]]:
        """Calculate stability statistics by stablecoin"""
        coin_stats = {}

        for coin in self.stablecoin_profiles.keys():
            coin_analyses = [s for s in self.stability_history if s.stablecoin == coin]
            coin_depegs = [d for d in self.depeg_history if d.stablecoin == coin]

            if coin_analyses:
                coin_stats[coin] = {
                    'avg_stability_score': np.mean([s.stability_score for s in coin_analyses]),
                    'depeg_events': len(coin_depegs),
                    'avg_recovery_time': np.mean([s.time_to_recovery for s in coin_analyses]),
                    'worst_depeg': max([d.depeg_percentage for d in coin_depegs]) if coin_depegs else 0
                }

        return coin_stats

    def _calculate_depeg_frequency(self) -> Dict[str, int]:
        """Calculate depeg event frequency by severity"""
        frequency = {}

        for severity in DepegSeverity:
            count = sum(1 for event in self.depeg_history if event.severity == severity)
            frequency[severity.value] = count

        return frequency

    def _calculate_severity_distribution(self) -> Dict[str, float]:
        """Calculate distribution of depeg severities"""
        if not self.depeg_history:
            return {}

        total_events = len(self.depeg_history)
        distribution = {}

        for severity in DepegSeverity:
            count = sum(1 for event in self.depeg_history if event.severity == severity)
            distribution[severity.value] = count / total_events

        return distribution

    def _calculate_recovery_time_stats(self) -> Dict[str, float]:
        """Calculate recovery time statistics"""
        if not self.depeg_history:
            return {}

        durations = [event.duration_minutes for event in self.depeg_history]

        return {
            'avg_duration_minutes': np.mean(durations),
            'median_duration_minutes': np.median(durations),
            'max_duration_minutes': max(durations),
            'min_duration_minutes': min(durations)
        }


# Example usage and testing
async def main():
    """Example usage of the stablecoin risk analyzer"""
    analyzer = StablecoinRiskAnalyzer()

    # Analyze stability of GARD (algorithmic stablecoin)
    gard_analysis = await analyzer.analyze_stablecoin_stability('GARD')

    print("GARD Stability Analysis:")
    print(f"Current Price: ${gard_analysis.current_price:.4f}")
    print(f"Depeg: ${gard_analysis.current_depeg:.4f}")
    print(f"Stability Score: {gard_analysis.stability_score:.3f}")
    print(f"Risk Level: {gard_analysis.risk_level}")
    print(f"Recovery Time: {gard_analysis.time_to_recovery:.1f} hours")

    # Test contagion analysis
    contagion_risk = await analyzer.analyze_contagion_risk('GARD', 0.05)

    print(f"\nContagion Risk Analysis:")
    print(f"Source: {contagion_risk.source_stablecoin}")
    print(f"Affected: {contagion_risk.affected_stablecoins}")
    print(f"Contagion Probability: {contagion_risk.contagion_probability:.3f}")

    # Monitor ecosystem stability
    ecosystem_status = await analyzer.monitor_ecosystem_stability()

    print(f"\nEcosystem Stability:")
    print(f"Weighted Stability: {ecosystem_status['ecosystem_metrics']['weighted_stability_score']:.3f}")
    print(f"Risk Distribution: {ecosystem_status['ecosystem_metrics']['risk_distribution']}")

    if ecosystem_status['alerts']:
        print(f"Alerts: {len(ecosystem_status['alerts'])} active")

if __name__ == "__main__":
    asyncio.run(main())