"""
Stress Tester - Advanced black swan event and extreme scenario modeling

This module provides comprehensive stress testing capabilities for the Algorand DeFi ecosystem,
modeling extreme market events, black swan scenarios, and their cascading effects across protocols.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StressScenario(Enum):
    """Types of stress test scenarios"""
    MARKET_CRASH = "market_crash"
    FLASH_CRASH = "flash_crash"
    STABLECOIN_DEPEG = "stablecoin_depeg"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    PROTOCOL_HACK = "protocol_hack"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    CONTAGION_CASCADE = "contagion_cascade"
    BLACK_SWAN = "black_swan"
    TAIL_RISK = "tail_risk"

class RiskMetric(Enum):
    """Risk metrics to calculate during stress tests"""
    VAR_95 = "var_95"           # Value at Risk 95%
    VAR_99 = "var_99"           # Value at Risk 99%
    VAR_999 = "var_999"         # Value at Risk 99.9%
    EXPECTED_SHORTFALL = "expected_shortfall"
    MAX_DRAWDOWN = "max_drawdown"
    LIQUIDATION_RATIO = "liquidation_ratio"
    CORRELATION_SHIFT = "correlation_shift"
    LIQUIDITY_IMPACT = "liquidity_impact"

@dataclass
class StressParameters:
    """Parameters for a stress test scenario"""
    scenario: StressScenario
    severity: float  # 0-1, 1 = most severe
    duration_hours: float
    affected_assets: List[str]
    shock_magnitudes: Dict[str, float]  # Asset -> shock percentage
    correlation_changes: Dict[str, float]  # Asset pair -> correlation change
    liquidity_impacts: Dict[str, float]  # Protocol -> liquidity reduction
    volume_multipliers: Dict[str, float]  # Asset -> volume multiplier
    volatility_multipliers: Dict[str, float]  # Asset -> volatility multiplier

@dataclass
class StressResult:
    """Result of a stress test"""
    scenario: StressScenario
    parameters: StressParameters
    risk_metrics: Dict[RiskMetric, float]
    portfolio_impact: Dict[str, float]  # Asset -> impact
    protocol_impacts: Dict[str, Dict[str, float]]  # Protocol -> metrics
    liquidation_events: List[Dict[str, Any]]
    recovery_time_hours: float
    systemic_risk_score: float
    confidence_level: float

@dataclass
class MonteCarloSimulation:
    """Monte Carlo simulation configuration"""
    num_simulations: int
    random_seed: Optional[int]
    correlation_matrix: pd.DataFrame
    return_distributions: Dict[str, Dict[str, float]]  # Asset -> {mean, std, skew, kurtosis}
    time_horizon_days: int

@dataclass
class TailRiskAnalysis:
    """Tail risk analysis results"""
    extreme_events: List[Dict[str, Any]]
    tail_index: float
    expected_tail_loss: float
    conditional_var: Dict[str, float]  # Confidence level -> CVaR
    extreme_value_params: Dict[str, float]

class AdvancedStressTester:
    """
    Advanced stress testing engine for comprehensive risk assessment across
    the Algorand DeFi ecosystem including black swan events and extreme scenarios.
    """

    def __init__(self, config_path: str = None):
        """Initialize the stress tester"""
        self.config = self._load_config(config_path)
        self.stress_config = self.config['stress_testing']
        self.monte_carlo_config = self.stress_config['monte_carlo']

        # Initialize scenario definitions
        self.scenarios = self._initialize_scenarios()
        self.risk_metrics = self._initialize_risk_metrics()

        # Historical data and results
        self.stress_results: List[StressResult] = []
        self.monte_carlo_results: Dict[str, Any] = {}
        self.tail_risk_analysis: Optional[TailRiskAnalysis] = None

        # Execution configuration
        self.max_workers = self.stress_config['execution']['max_workers']
        self.timeout_per_scenario = self.stress_config['execution']['timeout_per_scenario']

        logger.info("Advanced Stress Tester initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_scenarios(self) -> Dict[StressScenario, StressParameters]:
        """Initialize predefined stress test scenarios"""
        scenarios = {}

        # Market crash scenario
        scenarios[StressScenario.MARKET_CRASH] = StressParameters(
            scenario=StressScenario.MARKET_CRASH,
            severity=0.8,
            duration_hours=24,
            affected_assets=['ALGO', 'GARD', 'BANK', 'OPUL', 'GOBTC', 'GOETH'],
            shock_magnitudes={
                'ALGO': -0.5, 'GARD': -0.1, 'BANK': -0.6, 'OPUL': -0.7,
                'GOBTC': -0.4, 'GOETH': -0.45, 'USDC': 0.02, 'USDT': 0.02
            },
            correlation_changes={'all_pairs': 0.3},  # Increased correlation
            liquidity_impacts={'all_protocols': 0.6},  # 60% liquidity reduction
            volume_multipliers={'all_assets': 3.0},
            volatility_multipliers={'all_assets': 2.5}
        )

        # Flash crash scenario
        scenarios[StressScenario.FLASH_CRASH] = StressParameters(
            scenario=StressScenario.FLASH_CRASH,
            severity=0.6,
            duration_hours=1,
            affected_assets=['ALGO', 'GARD', 'BANK'],
            shock_magnitudes={'ALGO': -0.2, 'GARD': -0.05, 'BANK': -0.3},
            correlation_changes={'ALGO-GARD': 0.4, 'ALGO-BANK': 0.5},
            liquidity_impacts={'tinyman': 0.8, 'pact': 0.7},
            volume_multipliers={'ALGO': 10.0, 'GARD': 5.0, 'BANK': 8.0},
            volatility_multipliers={'ALGO': 5.0, 'GARD': 3.0, 'BANK': 6.0}
        )

        # Stablecoin depeg scenario
        scenarios[StressScenario.STABLECOIN_DEPEG] = StressParameters(
            scenario=StressScenario.STABLECOIN_DEPEG,
            severity=0.7,
            duration_hours=12,
            affected_assets=['USDC', 'GARD', 'USDT'],
            shock_magnitudes={'USDC': -0.1, 'GARD': -0.15, 'USDT': -0.05},
            correlation_changes={'USDC-GARD': 0.6, 'USDC-USDT': 0.4},
            liquidity_impacts={'all_protocols': 0.4},
            volume_multipliers={'USDC': 8.0, 'GARD': 12.0, 'USDT': 6.0},
            volatility_multipliers={'USDC': 20.0, 'GARD': 15.0, 'USDT': 10.0}
        )

        # Liquidity crisis scenario
        scenarios[StressScenario.LIQUIDITY_CRISIS] = StressParameters(
            scenario=StressScenario.LIQUIDITY_CRISIS,
            severity=0.9,
            duration_hours=6,
            affected_assets=['ALGO', 'USDC', 'GARD', 'BANK', 'OPUL'],
            shock_magnitudes={'all_assets': -0.1},  # Moderate price impact
            correlation_changes={'all_pairs': 0.5},  # High correlation increase
            liquidity_impacts={'all_protocols': 0.8},  # Severe liquidity reduction
            volume_multipliers={'all_assets': 0.2},  # Volume dries up
            volatility_multipliers={'all_assets': 4.0}
        )

        # Protocol hack scenario
        scenarios[StressScenario.PROTOCOL_HACK] = StressParameters(
            scenario=StressScenario.PROTOCOL_HACK,
            severity=0.8,
            duration_hours=72,
            affected_assets=['ALGO', 'USDC', 'GARD'],
            shock_magnitudes={'ALGO': -0.3, 'USDC': 0.01, 'GARD': -0.2},
            correlation_changes={'all_pairs': 0.4},
            liquidity_impacts={'algofi': 0.9, 'folks_finance': 0.3, 'tinyman': 0.2},
            volume_multipliers={'ALGO': 5.0, 'GARD': 8.0},
            volatility_multipliers={'ALGO': 3.0, 'GARD': 4.0}
        )

        # Add more scenarios from config
        for scenario_name, scenario_data in self.stress_config['scenarios'].items():
            if scenario_name not in [s.value for s in scenarios.keys()]:
                scenarios[StressScenario(scenario_name)] = self._create_scenario_from_config(
                    scenario_name, scenario_data
                )

        return scenarios

    def _create_scenario_from_config(self, scenario_name: str, scenario_data: Dict) -> StressParameters:
        """Create stress parameters from configuration"""
        return StressParameters(
            scenario=StressScenario(scenario_name),
            severity=0.8,  # Default severity
            duration_hours=scenario_data.get('duration_hours', 24),
            affected_assets=['ALGO', 'USDC', 'GARD'],  # Default assets
            shock_magnitudes={'ALGO': scenario_data.get('price_shock', -0.2)},
            correlation_changes={'all_pairs': scenario_data.get('correlation_increase', 0.3)},
            liquidity_impacts={'all_protocols': 0.5},
            volume_multipliers={'all_assets': scenario_data.get('volume_spike', 2.0)},
            volatility_multipliers={'all_assets': 2.0}
        )

    def _initialize_risk_metrics(self) -> Dict[RiskMetric, Callable]:
        """Initialize risk metric calculation functions"""
        return {
            RiskMetric.VAR_95: lambda returns: np.percentile(returns, 5),
            RiskMetric.VAR_99: lambda returns: np.percentile(returns, 1),
            RiskMetric.VAR_999: lambda returns: np.percentile(returns, 0.1),
            RiskMetric.EXPECTED_SHORTFALL: self._calculate_expected_shortfall,
            RiskMetric.MAX_DRAWDOWN: self._calculate_max_drawdown,
            RiskMetric.LIQUIDATION_RATIO: self._calculate_liquidation_ratio,
            RiskMetric.CORRELATION_SHIFT: self._calculate_correlation_shift,
            RiskMetric.LIQUIDITY_IMPACT: self._calculate_liquidity_impact
        }

    async def run_stress_test(
        self,
        scenario: StressScenario,
        portfolio: Dict[str, float] = None,
        custom_parameters: StressParameters = None
    ) -> StressResult:
        """
        Run a comprehensive stress test for a specific scenario

        Args:
            scenario: Stress test scenario to run
            portfolio: Portfolio composition (asset -> weight)
            custom_parameters: Custom scenario parameters

        Returns:
            Comprehensive stress test results
        """
        logger.info(f"Running stress test: {scenario.value}")

        # Get scenario parameters
        if custom_parameters:
            params = custom_parameters
        else:
            params = self.scenarios.get(scenario)
            if not params:
                raise ValueError(f"Unknown scenario: {scenario}")

        # Default portfolio if none provided
        if portfolio is None:
            portfolio = {
                'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1
            }

        # Generate stressed returns
        stressed_returns = await self._generate_stressed_returns(params, portfolio)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(stressed_returns, params)

        # Calculate portfolio impact
        portfolio_impact = self._calculate_portfolio_impact(stressed_returns, portfolio)

        # Simulate protocol impacts
        protocol_impacts = await self._simulate_protocol_impacts(params)

        # Generate liquidation events
        liquidation_events = await self._generate_liquidation_events(params, portfolio_impact)

        # Estimate recovery time
        recovery_time = self._estimate_recovery_time(params, risk_metrics)

        # Calculate systemic risk score
        systemic_risk_score = self._calculate_systemic_risk_score(
            risk_metrics, protocol_impacts, liquidation_events
        )

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(params, stressed_returns)

        result = StressResult(
            scenario=scenario,
            parameters=params,
            risk_metrics=risk_metrics,
            portfolio_impact=portfolio_impact,
            protocol_impacts=protocol_impacts,
            liquidation_events=liquidation_events,
            recovery_time_hours=recovery_time,
            systemic_risk_score=systemic_risk_score,
            confidence_level=confidence_level
        )

        self.stress_results.append(result)

        return result

    async def _generate_stressed_returns(
        self,
        params: StressParameters,
        portfolio: Dict[str, float]
    ) -> pd.DataFrame:
        """Generate stressed return series based on scenario parameters"""

        # Time series setup
        hours = int(params.duration_hours)
        timestamps = pd.date_range(
            start=datetime.now(),
            periods=hours,
            freq='H'
        )

        returns_data = {}

        for asset in portfolio.keys():
            # Get base shock magnitude
            shock = params.shock_magnitudes.get(asset,
                    params.shock_magnitudes.get('all_assets', 0.0))

            # Get volatility multiplier
            vol_mult = params.volatility_multipliers.get(asset,
                      params.volatility_multipliers.get('all_assets', 1.0))

            # Generate base return series
            base_volatility = self._get_base_volatility(asset)
            stressed_volatility = base_volatility * vol_mult

            # Generate return series with initial shock
            returns = np.random.normal(0, stressed_volatility / np.sqrt(24), hours)

            # Apply initial shock in first period
            returns[0] = shock

            # Add mean reversion after initial shock
            for i in range(1, len(returns)):
                mean_reversion = -returns[i-1] * 0.1  # 10% mean reversion
                returns[i] += mean_reversion

            returns_data[asset] = returns

        # Apply correlation changes
        returns_df = pd.DataFrame(returns_data, index=timestamps)

        if 'all_pairs' in params.correlation_changes:
            # Increase correlation across all assets
            corr_increase = params.correlation_changes['all_pairs']
            returns_df = self._apply_correlation_stress(returns_df, corr_increase)

        return returns_df

    def _get_base_volatility(self, asset: str) -> float:
        """Get base volatility for an asset"""
        base_volatilities = {
            'ALGO': 0.6,     # 60% annual volatility
            'USDC': 0.05,    # 5% for stablecoin
            'USDT': 0.05,
            'GARD': 0.3,     # 30% for algorithmic stablecoin
            'BANK': 0.8,     # 80% for DeFi token
            'OPUL': 0.9,     # 90% for smaller token
            'GOBTC': 0.7,    # 70% for wrapped BTC
            'GOETH': 0.8     # 80% for wrapped ETH
        }
        return base_volatilities.get(asset, 0.7)  # Default 70%

    def _apply_correlation_stress(
        self,
        returns_df: pd.DataFrame,
        correlation_increase: float
    ) -> pd.DataFrame:
        """Apply correlation stress to returns"""

        # Calculate current correlation matrix
        current_corr = returns_df.corr()

        # Create stressed correlation matrix
        stressed_corr = current_corr + correlation_increase

        # Ensure diagonal remains 1 and values stay in [-1, 1]
        np.fill_diagonal(stressed_corr.values, 1.0)
        stressed_corr = stressed_corr.clip(-1.0, 1.0)

        # Apply Cholesky decomposition to generate correlated returns
        try:
            L = np.linalg.cholesky(stressed_corr.values)

            # Generate uncorrelated random returns
            uncorr_returns = np.random.normal(0, 1, returns_df.shape)

            # Apply correlation structure
            corr_returns = uncorr_returns @ L.T

            # Scale by original volatilities
            for i, asset in enumerate(returns_df.columns):
                corr_returns[:, i] *= returns_df[asset].std()

            return pd.DataFrame(corr_returns,
                              index=returns_df.index,
                              columns=returns_df.columns)

        except np.linalg.LinAlgError:
            # If Cholesky fails, return original with warning
            logger.warning("Cholesky decomposition failed, using original returns")
            return returns_df

    def _calculate_risk_metrics(
        self,
        returns: pd.DataFrame,
        params: StressParameters
    ) -> Dict[RiskMetric, float]:
        """Calculate various risk metrics from stressed returns"""

        # Portfolio returns (equally weighted for simplicity)
        portfolio_returns = returns.mean(axis=1)

        risk_metrics = {}

        # VaR calculations
        risk_metrics[RiskMetric.VAR_95] = np.percentile(portfolio_returns, 5)
        risk_metrics[RiskMetric.VAR_99] = np.percentile(portfolio_returns, 1)
        risk_metrics[RiskMetric.VAR_999] = np.percentile(portfolio_returns, 0.1)

        # Expected Shortfall (Conditional VaR)
        var_95 = risk_metrics[RiskMetric.VAR_95]
        tail_losses = portfolio_returns[portfolio_returns <= var_95]
        risk_metrics[RiskMetric.EXPECTED_SHORTFALL] = tail_losses.mean() if len(tail_losses) > 0 else var_95

        # Maximum Drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        risk_metrics[RiskMetric.MAX_DRAWDOWN] = drawdown.min()

        # Liquidation ratio (simplified)
        severe_losses = (portfolio_returns < -0.1).sum() / len(portfolio_returns)
        risk_metrics[RiskMetric.LIQUIDATION_RATIO] = severe_losses

        # Correlation shift
        if len(returns.columns) > 1:
            current_corr = returns.corr()
            avg_corr = current_corr.values[np.triu_indices_from(current_corr.values, k=1)].mean()
            risk_metrics[RiskMetric.CORRELATION_SHIFT] = avg_corr
        else:
            risk_metrics[RiskMetric.CORRELATION_SHIFT] = 0.0

        # Liquidity impact (based on volume multipliers)
        avg_volume_impact = np.mean(list(params.volume_multipliers.values()))
        risk_metrics[RiskMetric.LIQUIDITY_IMPACT] = 1.0 / avg_volume_impact if avg_volume_impact > 0 else 1.0

        return risk_metrics

    def _calculate_expected_shortfall(self, returns: np.ndarray, confidence: float = 0.05) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        var = np.percentile(returns, confidence * 100)
        tail_losses = returns[returns <= var]
        return tail_losses.mean() if len(tail_losses) > 0 else var

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def _calculate_liquidation_ratio(self, returns: np.ndarray) -> float:
        """Calculate ratio of periods with severe losses"""
        return (returns < -0.1).sum() / len(returns)

    def _calculate_correlation_shift(self, returns: pd.DataFrame) -> float:
        """Calculate average correlation shift"""
        if len(returns.columns) < 2:
            return 0.0
        corr_matrix = returns.corr()
        upper_triangle = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
        return np.mean(upper_triangle)

    def _calculate_liquidity_impact(self, returns: pd.DataFrame) -> float:
        """Calculate liquidity impact metric"""
        volatility = returns.std().mean()
        return min(volatility * 10, 1.0)  # Normalize to 0-1

    def _calculate_portfolio_impact(
        self,
        returns: pd.DataFrame,
        portfolio: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate impact on each asset in portfolio"""
        impact = {}

        for asset, weight in portfolio.items():
            if asset in returns.columns:
                asset_returns = returns[asset]

                # Calculate various impact metrics
                total_return = (1 + asset_returns).prod() - 1
                max_single_loss = asset_returns.min()
                volatility = asset_returns.std()

                # Combined impact score
                impact_score = abs(total_return) + abs(max_single_loss) + volatility
                impact[asset] = impact_score * weight

        return impact

    async def _simulate_protocol_impacts(self, params: StressParameters) -> Dict[str, Dict[str, float]]:
        """Simulate impacts on DeFi protocols"""
        protocols = ['algofi', 'folks_finance', 'tinyman', 'pact', 'gard']

        protocol_impacts = {}

        for protocol in protocols:
            # Get liquidity impact for this protocol
            liquidity_impact = params.liquidity_impacts.get(protocol,
                             params.liquidity_impacts.get('all_protocols', 0.0))

            # Simulate various protocol metrics
            impacts = {
                'liquidity_reduction': liquidity_impact,
                'tvl_impact': liquidity_impact * 0.8,  # TVL reduces less than liquidity
                'utilization_increase': liquidity_impact * 0.5,  # Utilization increases
                'borrowing_rate_increase': liquidity_impact * 2.0,  # Rates increase more
                'liquidation_increase': liquidity_impact * 1.5,  # More liquidations
                'protocol_revenue_impact': -liquidity_impact * 0.3  # Revenue decreases
            }

            # Add protocol-specific factors
            if protocol in ['algofi', 'folks_finance']:  # Lending protocols
                impacts['bad_debt_ratio'] = liquidity_impact * 0.1
                impacts['collateral_ratio_stress'] = liquidity_impact * 0.6
            elif protocol in ['tinyman', 'pact']:  # DEXs
                impacts['slippage_increase'] = liquidity_impact * 3.0
                impacts['lp_impermanent_loss'] = liquidity_impact * 0.4
            elif protocol == 'gard':  # Stablecoin
                impacts['depeg_magnitude'] = liquidity_impact * 0.05
                impacts['redemption_pressure'] = liquidity_impact * 0.8

            protocol_impacts[protocol] = impacts

        return protocol_impacts

    async def _generate_liquidation_events(
        self,
        params: StressParameters,
        portfolio_impact: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate simulated liquidation events during stress"""

        liquidation_events = []

        # Base liquidation probability from scenario severity
        base_prob = params.severity * 0.3  # Up to 30% liquidation probability

        for asset, impact in portfolio_impact.items():
            # Liquidation probability increases with impact
            liquidation_prob = base_prob * (1 + impact)

            if np.random.random() < liquidation_prob:
                # Generate liquidation event
                liquidation_amount = np.random.uniform(10000, 1000000)  # $10k to $1M

                event = {
                    'timestamp': datetime.now().isoformat(),
                    'asset': asset,
                    'liquidation_amount_usd': liquidation_amount,
                    'price_impact': impact * 0.1,  # Price impact from liquidation
                    'trigger': params.scenario.value,
                    'severity': 'high' if impact > 0.5 else 'medium' if impact > 0.2 else 'low'
                }

                liquidation_events.append(event)

        return liquidation_events

    def _estimate_recovery_time(
        self,
        params: StressParameters,
        risk_metrics: Dict[RiskMetric, float]
    ) -> float:
        """Estimate recovery time from stress event"""

        # Base recovery time
        base_recovery = params.duration_hours * 2  # Usually 2x the stress duration

        # Adjust for severity
        severity_multiplier = 1 + params.severity

        # Adjust for max drawdown
        drawdown_multiplier = 1 + abs(risk_metrics.get(RiskMetric.MAX_DRAWDOWN, 0)) * 5

        # Adjust for scenario type
        scenario_multipliers = {
            StressScenario.FLASH_CRASH: 0.5,      # Recovers quickly
            StressScenario.MARKET_CRASH: 2.0,     # Takes longer
            StressScenario.LIQUIDITY_CRISIS: 3.0, # Very slow recovery
            StressScenario.PROTOCOL_HACK: 4.0,    # Longest recovery
            StressScenario.STABLECOIN_DEPEG: 1.5  # Moderate recovery
        }

        scenario_multiplier = scenario_multipliers.get(params.scenario, 1.0)

        recovery_time = base_recovery * severity_multiplier * drawdown_multiplier * scenario_multiplier

        return min(recovery_time, 720)  # Cap at 30 days

    def _calculate_systemic_risk_score(
        self,
        risk_metrics: Dict[RiskMetric, float],
        protocol_impacts: Dict[str, Dict[str, float]],
        liquidation_events: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall systemic risk score (0-1)"""

        # Risk from portfolio metrics
        var_99 = abs(risk_metrics.get(RiskMetric.VAR_99, 0))
        max_drawdown = abs(risk_metrics.get(RiskMetric.MAX_DRAWDOWN, 0))
        liquidation_ratio = risk_metrics.get(RiskMetric.LIQUIDATION_RATIO, 0)

        portfolio_risk = (var_99 + max_drawdown + liquidation_ratio) / 3

        # Risk from protocol impacts
        total_protocol_impact = 0
        for protocol, impacts in protocol_impacts.items():
            protocol_impact = np.mean(list(impacts.values()))
            total_protocol_impact += abs(protocol_impact)

        avg_protocol_impact = total_protocol_impact / len(protocol_impacts) if protocol_impacts else 0

        # Risk from liquidation events
        liquidation_risk = min(len(liquidation_events) / 10, 1.0)  # Normalize to max 10 events

        # Weighted systemic risk score
        systemic_risk = (
            portfolio_risk * 0.4 +
            avg_protocol_impact * 0.4 +
            liquidation_risk * 0.2
        )

        return min(systemic_risk, 1.0)

    def _calculate_confidence_level(
        self,
        params: StressParameters,
        returns: pd.DataFrame
    ) -> float:
        """Calculate confidence level in stress test results"""

        # Confidence based on data quality and scenario realism
        base_confidence = 0.8

        # Adjust for scenario severity (extreme scenarios less confident)
        severity_adjustment = -params.severity * 0.2

        # Adjust for return series quality
        returns_quality = 1.0 - returns.isnull().sum().sum() / (returns.shape[0] * returns.shape[1])
        quality_adjustment = (returns_quality - 0.8) * 0.25

        # Adjust for scenario type (some scenarios more predictable)
        scenario_confidence = {
            StressScenario.MARKET_CRASH: 0.9,
            StressScenario.FLASH_CRASH: 0.8,
            StressScenario.LIQUIDITY_CRISIS: 0.7,
            StressScenario.PROTOCOL_HACK: 0.6,
            StressScenario.BLACK_SWAN: 0.3
        }

        scenario_adjustment = scenario_confidence.get(params.scenario, 0.7) - 0.7

        confidence = base_confidence + severity_adjustment + quality_adjustment + scenario_adjustment

        return max(0.1, min(confidence, 0.95))

    async def run_monte_carlo_simulation(
        self,
        num_simulations: int = None,
        time_horizon_days: int = 30,
        portfolio: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for comprehensive risk assessment

        Args:
            num_simulations: Number of simulation runs
            time_horizon_days: Time horizon for simulation
            portfolio: Portfolio composition

        Returns:
            Monte Carlo simulation results
        """
        if num_simulations is None:
            num_simulations = self.monte_carlo_config['num_simulations']

        if portfolio is None:
            portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        logger.info(f"Running Monte Carlo simulation with {num_simulations} iterations")

        # Set random seed for reproducibility
        if self.monte_carlo_config.get('random_seed'):
            np.random.seed(self.monte_carlo_config['random_seed'])

        simulation_results = []

        # Run simulations in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for i in range(num_simulations):
                future = executor.submit(
                    self._run_single_monte_carlo,
                    i, time_horizon_days, portfolio
                )
                futures.append(future)

            # Collect results
            for future in futures:
                try:
                    result = future.result(timeout=60)  # 60 second timeout per simulation
                    simulation_results.append(result)
                except Exception as e:
                    logger.warning(f"Simulation failed: {e}")

        if not simulation_results:
            raise RuntimeError("All Monte Carlo simulations failed")

        # Analyze simulation results
        analysis = self._analyze_monte_carlo_results(simulation_results, portfolio)

        self.monte_carlo_results = analysis

        return analysis

    def _run_single_monte_carlo(
        self,
        simulation_id: int,
        time_horizon_days: int,
        portfolio: Dict[str, float]
    ) -> Dict[str, Any]:
        """Run a single Monte Carlo simulation"""

        # Generate random returns for each asset
        daily_returns = {}

        for asset in portfolio.keys():
            # Get asset parameters
            mean_return = self._get_expected_return(asset)
            volatility = self._get_base_volatility(asset)

            # Generate correlated random returns
            returns = np.random.normal(
                mean_return / 365,  # Daily mean
                volatility / np.sqrt(365),  # Daily volatility
                time_horizon_days
            )

            daily_returns[asset] = returns

        # Calculate portfolio returns
        portfolio_returns = np.zeros(time_horizon_days)

        for asset, weight in portfolio.items():
            portfolio_returns += daily_returns[asset] * weight

        # Calculate metrics for this simulation
        total_return = (1 + portfolio_returns).prod() - 1
        max_drawdown = self._calculate_max_drawdown(portfolio_returns)
        volatility = np.std(portfolio_returns)
        var_95 = np.percentile(portfolio_returns, 5)
        var_99 = np.percentile(portfolio_returns, 1)

        # Count extreme events
        extreme_events = (portfolio_returns < -0.05).sum()  # Days with >5% loss

        return {
            'simulation_id': simulation_id,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'var_95': var_95,
            'var_99': var_99,
            'extreme_events': extreme_events,
            'final_portfolio_value': 1 + total_return,
            'daily_returns': portfolio_returns.tolist()
        }

    def _get_expected_return(self, asset: str) -> float:
        """Get expected annual return for asset"""
        expected_returns = {
            'ALGO': 0.15,    # 15% expected return
            'USDC': 0.02,    # 2% for stablecoin
            'USDT': 0.02,
            'GARD': 0.05,    # 5% for algorithmic stablecoin
            'BANK': 0.25,    # 25% for DeFi token (higher risk/reward)
            'OPUL': 0.30,    # 30% for smaller token
            'GOBTC': 0.20,   # 20% for wrapped BTC
            'GOETH': 0.22    # 22% for wrapped ETH
        }
        return expected_returns.get(asset, 0.10)  # Default 10%

    def _analyze_monte_carlo_results(
        self,
        results: List[Dict[str, Any]],
        portfolio: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze Monte Carlo simulation results"""

        # Extract metrics
        total_returns = [r['total_return'] for r in results]
        max_drawdowns = [r['max_drawdown'] for r in results]
        volatilities = [r['volatility'] for r in results]
        var_95s = [r['var_95'] for r in results]
        var_99s = [r['var_99'] for r in results]
        extreme_events = [r['extreme_events'] for r in results]
        final_values = [r['final_portfolio_value'] for r in results]

        # Calculate percentiles
        confidence_levels = self.monte_carlo_config['confidence_levels']

        return_percentiles = {
            f"return_{int(conf*100)}%": np.percentile(total_returns, conf*100)
            for conf in confidence_levels
        }

        drawdown_percentiles = {
            f"drawdown_{int(conf*100)}%": np.percentile(max_drawdowns, conf*100)
            for conf in confidence_levels
        }

        # Risk metrics
        probability_of_loss = (np.array(total_returns) < 0).mean()
        probability_extreme_loss = (np.array(total_returns) < -0.2).mean()  # >20% loss

        expected_shortfall_95 = np.mean([r for r in total_returns if r <= np.percentile(total_returns, 5)])
        expected_shortfall_99 = np.mean([r for r in total_returns if r <= np.percentile(total_returns, 1)])

        return {
            'simulation_summary': {
                'num_simulations': len(results),
                'portfolio': portfolio,
                'confidence_levels': confidence_levels
            },
            'return_statistics': {
                'mean': np.mean(total_returns),
                'median': np.median(total_returns),
                'std': np.std(total_returns),
                'skewness': self._calculate_skewness(total_returns),
                'kurtosis': self._calculate_kurtosis(total_returns),
                'percentiles': return_percentiles
            },
            'risk_statistics': {
                'probability_of_loss': probability_of_loss,
                'probability_extreme_loss': probability_extreme_loss,
                'expected_shortfall_95': expected_shortfall_95,
                'expected_shortfall_99': expected_shortfall_99,
                'max_drawdown_percentiles': drawdown_percentiles,
                'avg_extreme_events': np.mean(extreme_events)
            },
            'var_estimates': {
                'var_95': np.percentile(total_returns, 5),
                'var_99': np.percentile(total_returns, 1),
                'var_999': np.percentile(total_returns, 0.1)
            },
            'tail_risk_analysis': self._analyze_tail_risk(total_returns)
        }

    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate skewness of data"""
        data = np.array(data)
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return 0

        return np.mean(((data - mean) / std) ** 3)

    def _calculate_kurtosis(self, data: List[float]) -> float:
        """Calculate kurtosis of data"""
        data = np.array(data)
        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return 0

        return np.mean(((data - mean) / std) ** 4) - 3  # Excess kurtosis

    def _analyze_tail_risk(self, returns: List[float]) -> Dict[str, Any]:
        """Analyze tail risk characteristics"""
        returns = np.array(returns)

        # Identify extreme losses (bottom 5%)
        threshold = np.percentile(returns, 5)
        extreme_losses = returns[returns <= threshold]

        if len(extreme_losses) == 0:
            return {'error': 'No extreme losses found'}

        # Estimate tail index using Hill estimator
        sorted_losses = np.sort(-extreme_losses)  # Convert to positive losses

        if len(sorted_losses) > 1:
            # Hill estimator for tail index
            k = min(len(sorted_losses) // 2, 20)  # Use up to 20 extreme values
            if k > 1:
                tail_index = 1 / np.mean(np.log(sorted_losses[:k]) - np.log(sorted_losses[k]))
            else:
                tail_index = 1.0
        else:
            tail_index = 1.0

        # Expected tail loss
        expected_tail_loss = np.mean(extreme_losses)

        # Tail probability
        tail_probability = len(extreme_losses) / len(returns)

        return {
            'tail_index': tail_index,
            'expected_tail_loss': expected_tail_loss,
            'tail_probability': tail_probability,
            'extreme_loss_threshold': threshold,
            'num_extreme_events': len(extreme_losses),
            'worst_loss': np.min(returns),
            'tail_var_ratio': abs(expected_tail_loss) / abs(threshold) if threshold != 0 else 1
        }

    async def run_comprehensive_stress_suite(
        self,
        portfolio: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive stress testing suite across all scenarios

        Args:
            portfolio: Portfolio composition

        Returns:
            Comprehensive stress testing results
        """
        logger.info("Running comprehensive stress testing suite")

        if portfolio is None:
            portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        # Run all stress scenarios
        stress_results = {}

        for scenario in StressScenario:
            if scenario in self.scenarios:
                try:
                    result = await self.run_stress_test(scenario, portfolio)
                    stress_results[scenario.value] = result
                except Exception as e:
                    logger.error(f"Failed to run stress test {scenario.value}: {e}")

        # Run Monte Carlo simulation
        try:
            monte_carlo_results = await self.run_monte_carlo_simulation(portfolio=portfolio)
        except Exception as e:
            logger.error(f"Failed to run Monte Carlo simulation: {e}")
            monte_carlo_results = {}

        # Aggregate analysis
        aggregate_analysis = self._create_aggregate_analysis(stress_results, monte_carlo_results)

        return {
            'portfolio': portfolio,
            'stress_test_results': {k: v.__dict__ if hasattr(v, '__dict__') else v
                                  for k, v in stress_results.items()},
            'monte_carlo_results': monte_carlo_results,
            'aggregate_analysis': aggregate_analysis,
            'recommendations': self._generate_risk_recommendations(
                stress_results, monte_carlo_results, portfolio
            )
        }

    def _create_aggregate_analysis(
        self,
        stress_results: Dict[str, StressResult],
        monte_carlo_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create aggregate analysis across all stress tests"""

        if not stress_results:
            return {'error': 'No stress test results available'}

        # Aggregate stress test metrics
        all_systemic_risks = [result.systemic_risk_score for result in stress_results.values()]
        all_recovery_times = [result.recovery_time_hours for result in stress_results.values()]
        all_liquidation_counts = [len(result.liquidation_events) for result in stress_results.values()]

        # Find worst-case scenarios
        worst_systemic_risk = max(all_systemic_risks)
        worst_recovery_time = max(all_recovery_times)
        worst_scenario = max(stress_results.items(), key=lambda x: x[1].systemic_risk_score)

        # Calculate risk concentration
        risk_by_scenario = {
            scenario: result.systemic_risk_score
            for scenario, result in stress_results.items()
        }

        return {
            'worst_case_analysis': {
                'worst_systemic_risk': worst_systemic_risk,
                'worst_recovery_time': worst_recovery_time,
                'worst_scenario': worst_scenario[0],
                'total_liquidation_events': sum(all_liquidation_counts)
            },
            'risk_distribution': {
                'avg_systemic_risk': np.mean(all_systemic_risks),
                'risk_concentration': max(all_systemic_risks) / np.mean(all_systemic_risks),
                'scenario_risks': risk_by_scenario
            },
            'recovery_analysis': {
                'avg_recovery_time': np.mean(all_recovery_times),
                'max_recovery_time': worst_recovery_time,
                'recovery_variance': np.var(all_recovery_times)
            },
            'monte_carlo_comparison': self._compare_stress_vs_monte_carlo(
                stress_results, monte_carlo_results
            )
        }

    def _compare_stress_vs_monte_carlo(
        self,
        stress_results: Dict[str, StressResult],
        monte_carlo_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare stress test results with Monte Carlo simulation"""

        if not monte_carlo_results or 'var_estimates' not in monte_carlo_results:
            return {'error': 'No Monte Carlo results for comparison'}

        # Get worst VaR from stress tests
        worst_stress_var = min(
            result.risk_metrics.get(RiskMetric.VAR_99, 0)
            for result in stress_results.values()
        )

        # Get Monte Carlo VaR
        mc_var_99 = monte_carlo_results['var_estimates']['var_99']

        # Compare
        stress_vs_mc_ratio = abs(worst_stress_var) / abs(mc_var_99) if mc_var_99 != 0 else 1

        return {
            'worst_stress_var_99': worst_stress_var,
            'monte_carlo_var_99': mc_var_99,
            'stress_severity_ratio': stress_vs_mc_ratio,
            'stress_more_severe': stress_vs_mc_ratio > 1.2,  # Stress tests 20% worse
            'coverage_analysis': {
                'stress_covers_tail_risk': abs(worst_stress_var) > abs(mc_var_99),
                'confidence_gap': abs(worst_stress_var) - abs(mc_var_99)
            }
        }

    def _generate_risk_recommendations(
        self,
        stress_results: Dict[str, StressResult],
        monte_carlo_results: Dict[str, Any],
        portfolio: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """Generate risk management recommendations"""

        recommendations = []

        if not stress_results:
            return [{'type': 'error', 'message': 'No stress test results available for recommendations'}]

        # Analyze worst risks
        worst_scenario = max(stress_results.items(), key=lambda x: x[1].systemic_risk_score)
        worst_risk_score = worst_scenario[1].systemic_risk_score

        # High systemic risk
        if worst_risk_score > 0.8:
            recommendations.append({
                'type': 'critical',
                'category': 'portfolio_diversification',
                'message': f'Critical systemic risk detected in {worst_scenario[0]} scenario. '
                          'Consider reducing portfolio concentration and adding uncorrelated assets.'
            })

        # Liquidation risk
        total_liquidations = sum(len(result.liquidation_events) for result in stress_results.values())
        if total_liquidations > len(stress_results) * 2:  # Avg > 2 liquidations per scenario
            recommendations.append({
                'type': 'high',
                'category': 'liquidation_risk',
                'message': 'High liquidation risk detected across multiple scenarios. '
                          'Consider increasing collateral ratios and monitoring liquidation thresholds.'
            })

        # Recovery time risk
        max_recovery = max(result.recovery_time_hours for result in stress_results.values())
        if max_recovery > 168:  # > 1 week
            recommendations.append({
                'type': 'medium',
                'category': 'recovery_planning',
                'message': f'Extended recovery time of {max_recovery:.0f} hours detected. '
                          'Develop contingency plans for prolonged market stress periods.'
            })

        # Monte Carlo tail risk
        if monte_carlo_results and 'tail_risk_analysis' in monte_carlo_results:
            tail_risk = monte_carlo_results['tail_risk_analysis']
            if tail_risk.get('tail_index', 1) < 2:  # Heavy tails
                recommendations.append({
                    'type': 'medium',
                    'category': 'tail_risk',
                    'message': 'Heavy tail risk detected in return distribution. '
                              'Consider tail risk hedging strategies and position sizing limits.'
                })

        # Portfolio concentration
        max_weight = max(portfolio.values())
        if max_weight > 0.5:  # > 50% in single asset
            recommendations.append({
                'type': 'medium',
                'category': 'concentration',
                'message': f'High concentration risk: {max_weight:.1%} in single asset. '
                          'Consider rebalancing to reduce concentration risk.'
            })

        # Stablecoin risk
        stablecoin_exposure = sum(weight for asset, weight in portfolio.items()
                                 if asset in ['USDC', 'USDT', 'GARD'])
        if stablecoin_exposure > 0.7:  # > 70% stablecoins
            recommendations.append({
                'type': 'low',
                'category': 'stablecoin_risk',
                'message': 'High stablecoin exposure detected. Monitor depeg risks and consider '
                          'diversifying across different stablecoin mechanisms.'
            })

        return recommendations

    def get_stress_test_statistics(self) -> Dict[str, Any]:
        """Get comprehensive stress testing statistics"""

        if not self.stress_results:
            return {'error': 'No stress test history available'}

        return {
            'total_stress_tests': len(self.stress_results),
            'scenarios_tested': list(set(result.scenario.value for result in self.stress_results)),
            'risk_metric_statistics': self._calculate_risk_metric_statistics(),
            'scenario_impact_ranking': self._rank_scenarios_by_impact(),
            'recovery_time_analysis': self._analyze_recovery_times(),
            'liquidation_frequency': self._analyze_liquidation_frequency(),
            'confidence_analysis': self._analyze_confidence_levels()
        }

    def _calculate_risk_metric_statistics(self) -> Dict[str, Dict[str, float]]:
        """Calculate statistics for each risk metric across all tests"""

        metric_stats = {}

        for metric in RiskMetric:
            values = [
                result.risk_metrics.get(metric, 0)
                for result in self.stress_results
            ]

            if values:
                metric_stats[metric.value] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }

        return metric_stats

    def _rank_scenarios_by_impact(self) -> List[Dict[str, Any]]:
        """Rank scenarios by their average impact"""

        scenario_impacts = {}

        for result in self.stress_results:
            scenario = result.scenario.value

            if scenario not in scenario_impacts:
                scenario_impacts[scenario] = []

            scenario_impacts[scenario].append(result.systemic_risk_score)

        # Calculate average impact per scenario
        scenario_rankings = []
        for scenario, impacts in scenario_impacts.items():
            scenario_rankings.append({
                'scenario': scenario,
                'avg_impact': np.mean(impacts),
                'max_impact': np.max(impacts),
                'num_tests': len(impacts)
            })

        # Sort by average impact
        scenario_rankings.sort(key=lambda x: x['avg_impact'], reverse=True)

        return scenario_rankings

    def _analyze_recovery_times(self) -> Dict[str, float]:
        """Analyze recovery time patterns"""

        recovery_times = [result.recovery_time_hours for result in self.stress_results]

        return {
            'avg_recovery_hours': np.mean(recovery_times),
            'median_recovery_hours': np.median(recovery_times),
            'max_recovery_hours': np.max(recovery_times),
            'recovery_time_variance': np.var(recovery_times),
            'long_recovery_probability': (np.array(recovery_times) > 168).mean()  # > 1 week
        }

    def _analyze_liquidation_frequency(self) -> Dict[str, float]:
        """Analyze liquidation event frequency"""

        liquidation_counts = [len(result.liquidation_events) for result in self.stress_results]

        return {
            'avg_liquidations_per_test': np.mean(liquidation_counts),
            'max_liquidations': np.max(liquidation_counts),
            'zero_liquidation_probability': (np.array(liquidation_counts) == 0).mean(),
            'high_liquidation_probability': (np.array(liquidation_counts) > 5).mean()
        }

    def _analyze_confidence_levels(self) -> Dict[str, float]:
        """Analyze confidence levels in stress test results"""

        confidence_levels = [result.confidence_level for result in self.stress_results]

        return {
            'avg_confidence': np.mean(confidence_levels),
            'min_confidence': np.min(confidence_levels),
            'high_confidence_tests': (np.array(confidence_levels) > 0.8).mean(),
            'low_confidence_tests': (np.array(confidence_levels) < 0.5).mean()
        }


# Example usage and testing
async def main():
    """Example usage of the advanced stress tester"""
    tester = AdvancedStressTester()

    # Run a single stress test
    market_crash_result = await tester.run_stress_test(
        StressScenario.MARKET_CRASH,
        portfolio={'ALGO': 0.5, 'USDC': 0.3, 'GARD': 0.2}
    )

    print("Market Crash Stress Test Results:")
    print(f"Systemic Risk Score: {market_crash_result.systemic_risk_score:.3f}")
    print(f"Recovery Time: {market_crash_result.recovery_time_hours:.1f} hours")
    print(f"VaR 99%: {market_crash_result.risk_metrics.get(RiskMetric.VAR_99, 0):.3f}")
    print(f"Liquidation Events: {len(market_crash_result.liquidation_events)}")

    # Run Monte Carlo simulation
    mc_results = await tester.run_monte_carlo_simulation(
        num_simulations=1000,
        time_horizon_days=30,
        portfolio={'ALGO': 0.5, 'USDC': 0.3, 'GARD': 0.2}
    )

    print(f"\nMonte Carlo Results:")
    print(f"VaR 95%: {mc_results['var_estimates']['var_95']:.3f}")
    print(f"VaR 99%: {mc_results['var_estimates']['var_99']:.3f}")
    print(f"Expected Return: {mc_results['return_statistics']['mean']:.3f}")
    print(f"Probability of Loss: {mc_results['risk_statistics']['probability_of_loss']:.3f}")

    # Run comprehensive stress suite
    comprehensive_results = await tester.run_comprehensive_stress_suite(
        portfolio={'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}
    )

    print(f"\nComprehensive Stress Testing:")
    print(f"Worst Scenario: {comprehensive_results['aggregate_analysis']['worst_case_analysis']['worst_scenario']}")
    print(f"Worst Systemic Risk: {comprehensive_results['aggregate_analysis']['worst_case_analysis']['worst_systemic_risk']:.3f}")

    recommendations = comprehensive_results['recommendations']
    print(f"\nRecommendations ({len(recommendations)}):")
    for rec in recommendations[:3]:  # Show first 3
        print(f"- {rec['category']}: {rec['message']}")

if __name__ == "__main__":
    asyncio.run(main())