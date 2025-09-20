"""
Main Liquidity Cascade Risk Analyzer

Orchestrates comprehensive liquidation cascade risk assessment including:
- Liquidation modeling and simulation
- Market depth analysis
- Stablecoin stability evaluation
- Correlation and contagion analysis
- Stress testing under various scenarios
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from .models import (
    CascadeRiskProfile, CascadeRiskScore, RiskLevel,
    LiquidationEvent, MarketDepthRisk, StablecoinRisk,
    CorrelationRisk, CascadeSimulationResult, StressTestScenario
)
from .liquidation_modeler import LiquidationModeler
from .market_depth_analyzer import MarketDepthAnalyzer
from .stablecoin_stability import StablecoinStabilityAnalyzer

logger = logging.getLogger(__name__)


class LiquidityCascadeAnalyzer:
    """
    Main analyzer for liquidity cascade risk assessment
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

        # Initialize component analyzers
        self.liquidation_modeler = LiquidationModeler(self.config.get('liquidation_modeling', {}))
        self.market_depth_analyzer = MarketDepthAnalyzer(self.config.get('market_depth', {}))
        self.stablecoin_analyzer = StablecoinStabilityAnalyzer(self.config.get('stablecoin', {}))

        # Risk scoring weights
        self.risk_weights = self.config.get('risk_weights', {
            'liquidation_modeling': 0.25,
            'market_depth': 0.20,
            'stablecoin_stability': 0.20,
            'correlation_amplification': 0.20,
            'systemic_contagion': 0.15
        })

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for cascade risk analysis"""
        return {
            'analysis_window_days': 30,
            'simulation_scenarios': 10,
            'stress_test_confidence': 0.95,
            'cascade_depth_limit': 5,
            'risk_thresholds': {
                'low': 25,
                'medium': 50,
                'high': 75
            },
            'position_size_threshold': 1000000,  # $1M
            'enable_monte_carlo': True,
            'monte_carlo_iterations': 1000
        }

    async def analyze_cascade_risk(
        self,
        address: str,
        include_portfolio_analysis: bool = True,
        stress_test_scenarios: Optional[List[str]] = None
    ) -> CascadeRiskProfile:
        """
        Perform comprehensive liquidity cascade risk analysis

        Args:
            address: Address to analyze for cascade risk
            include_portfolio_analysis: Whether to include detailed portfolio analysis
            stress_test_scenarios: List of stress test scenarios to run

        Returns:
            Complete cascade risk profile
        """
        try:
            logger.info(f"Starting cascade risk analysis for address: {address}")

            # Get base position and portfolio information
            portfolio_info = await self._get_portfolio_info(address)

            # Run parallel risk analysis components
            analysis_tasks = [
                self._analyze_liquidation_risk(address, portfolio_info),
                self._analyze_market_depth_risks(address, portfolio_info),
                self._analyze_stablecoin_risks(address, portfolio_info),
                self._analyze_correlation_risks(address, portfolio_info),
                self._run_cascade_simulations(address, portfolio_info),
                self._run_stress_tests(address, portfolio_info, stress_test_scenarios or [])
            ]

            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # Parse results
            liquidation_events = results[0] if not isinstance(results[0], Exception) else []
            market_depth_risks = results[1] if not isinstance(results[1], Exception) else []
            stablecoin_risks = results[2] if not isinstance(results[2], Exception) else []
            correlation_risks = results[3] if not isinstance(results[3], Exception) else None
            cascade_simulations = results[4] if not isinstance(results[4], Exception) else []
            stress_test_scenarios = results[5] if not isinstance(results[5], Exception) else []

            # Calculate comprehensive risk score
            risk_score = self._calculate_cascade_risk_score(
                liquidation_events, market_depth_risks, stablecoin_risks,
                correlation_risks, cascade_simulations, stress_test_scenarios,
                portfolio_info
            )

            # Analyze market environment
            market_environment = await self._analyze_market_environment()

            # Create comprehensive profile
            profile = CascadeRiskProfile(
                address=address,
                assessment_timestamp=datetime.utcnow(),
                liquidation_events=liquidation_events,
                market_depth_risks=market_depth_risks,
                stablecoin_risks=stablecoin_risks,
                correlation_risks=correlation_risks,
                cascade_simulations=cascade_simulations,
                stress_test_scenarios=stress_test_scenarios,
                risk_score=risk_score,
                position_concentration=portfolio_info.get('position_concentration', {}),
                leverage_metrics=portfolio_info.get('leverage_metrics', {}),
                collateral_diversity=portfolio_info.get('collateral_diversity', 0.0),
                liquidation_thresholds=portfolio_info.get('liquidation_thresholds', {}),
                health_factor_history=portfolio_info.get('health_factor_history', []),
                market_volatility_regime=market_environment.get('volatility_regime', 'normal'),
                liquidity_environment=market_environment.get('liquidity_environment', 'normal'),
                correlation_regime=market_environment.get('correlation_regime', 'normal'),
                data_sources=self.config.get('data_sources', ['on_chain', 'market_data']),
                analysis_version="1.0.0",
                limitations=self._get_analysis_limitations()
            )

            logger.info(f"Cascade risk analysis completed. Risk level: {risk_score.risk_level.value}")
            return profile

        except Exception as e:
            logger.error(f"Error in cascade risk analysis for {address}: {e}")
            raise

    async def _analyze_liquidation_risk(
        self,
        address: str,
        portfolio_info: Dict[str, Any]
    ) -> List[LiquidationEvent]:
        """Analyze liquidation risk and historical events"""
        try:
            return await self.liquidation_modeler.model_liquidation_risk(address, portfolio_info)
        except Exception as e:
            logger.error(f"Liquidation risk analysis failed: {e}")
            return []

    async def _analyze_market_depth_risks(
        self,
        address: str,
        portfolio_info: Dict[str, Any]
    ) -> List[MarketDepthRisk]:
        """Analyze market depth and liquidity risks"""
        try:
            assets = list(portfolio_info.get('position_concentration', {}).keys())
            return await self.market_depth_analyzer.analyze_market_depth_risks(assets)
        except Exception as e:
            logger.error(f"Market depth risk analysis failed: {e}")
            return []

    async def _analyze_stablecoin_risks(
        self,
        address: str,
        portfolio_info: Dict[str, Any]
    ) -> List[StablecoinRisk]:
        """Analyze stablecoin stability risks"""
        try:
            # Identify stablecoins in portfolio
            stablecoins = await self._identify_stablecoins_in_portfolio(portfolio_info)
            return await self.stablecoin_analyzer.analyze_stablecoin_risks(stablecoins)
        except Exception as e:
            logger.error(f"Stablecoin risk analysis failed: {e}")
            return []

    async def _analyze_correlation_risks(
        self,
        address: str,
        portfolio_info: Dict[str, Any]
    ) -> Optional[CorrelationRisk]:
        """Analyze correlation and systemic risks"""
        try:
            assets = list(portfolio_info.get('position_concentration', {}).keys())
            if len(assets) < 2:
                return None

            correlation_matrix = await self._calculate_asset_correlations(assets)
            liquidation_correlations = await self._calculate_liquidation_correlations(assets)

            # Calculate systemic risk factors
            systemic_factors = await self._identify_systemic_risk_factors(assets)
            contagion_paths = await self._identify_contagion_pathways(assets, correlation_matrix)

            from .models import CorrelationRisk
            return CorrelationRisk(
                asset_correlation_matrix=correlation_matrix,
                liquidation_correlation=liquidation_correlations,
                market_beta=await self._calculate_market_betas(assets),
                systemic_risk_factors=systemic_factors,
                contagion_pathways=contagion_paths,
                diversification_effectiveness=await self._calculate_diversification_effectiveness(portfolio_info),
                tail_risk_correlation=await self._calculate_tail_risk_correlation(assets),
                volatility_clustering=await self._calculate_volatility_clustering(assets),
                jump_risk_correlation=await self._calculate_jump_risk_correlation(assets)
            )

        except Exception as e:
            logger.error(f"Correlation risk analysis failed: {e}")
            return None

    async def _run_cascade_simulations(
        self,
        address: str,
        portfolio_info: Dict[str, Any]
    ) -> List[CascadeSimulationResult]:
        """Run liquidation cascade simulations"""
        try:
            simulations = []

            # Define simulation scenarios
            scenarios = [
                {'name': 'market_crash_20', 'price_shock': -0.20},
                {'name': 'market_crash_40', 'price_shock': -0.40},
                {'name': 'flash_crash', 'price_shock': -0.60, 'duration_minutes': 15},
                {'name': 'liquidity_crisis', 'liquidity_shock': -0.70},
                {'name': 'stablecoin_depeg', 'stablecoin_shock': -0.10}
            ]

            # Run each simulation
            for scenario in scenarios:
                simulation_result = await self._simulate_cascade_scenario(address, portfolio_info, scenario)
                if simulation_result:
                    simulations.append(simulation_result)

            return simulations

        except Exception as e:
            logger.error(f"Cascade simulation failed: {e}")
            return []

    async def _run_stress_tests(
        self,
        address: str,
        portfolio_info: Dict[str, Any],
        scenario_names: List[str]
    ) -> List[StressTestScenario]:
        """Run stress testing scenarios"""
        try:
            stress_tests = []

            # Default stress test scenarios if none specified
            if not scenario_names:
                scenario_names = ['market_crash', 'liquidity_crisis', 'correlation_breakdown']

            for scenario_name in scenario_names:
                stress_test = await self._execute_stress_test(address, portfolio_info, scenario_name)
                if stress_test:
                    stress_tests.append(stress_test)

            return stress_tests

        except Exception as e:
            logger.error(f"Stress testing failed: {e}")
            return []

    def _calculate_cascade_risk_score(
        self,
        liquidation_events: List[LiquidationEvent],
        market_depth_risks: List[MarketDepthRisk],
        stablecoin_risks: List[StablecoinRisk],
        correlation_risks: Optional[CorrelationRisk],
        cascade_simulations: List[CascadeSimulationResult],
        stress_tests: List[StressTestScenario],
        portfolio_info: Dict[str, Any]
    ) -> CascadeRiskScore:
        """Calculate comprehensive cascade risk score"""

        # Calculate component scores (0-100)
        liquidation_score = self._score_liquidation_risk(liquidation_events, portfolio_info)
        market_depth_score = self._score_market_depth_risk(market_depth_risks)
        stablecoin_score = self._score_stablecoin_risk(stablecoin_risks)
        correlation_score = self._score_correlation_risk(correlation_risks)
        systemic_score = self._score_systemic_risk(cascade_simulations, stress_tests)

        # Calculate weighted overall score
        overall_score = (
            liquidation_score * self.risk_weights['liquidation_modeling'] +
            market_depth_score * self.risk_weights['market_depth'] +
            stablecoin_score * self.risk_weights['stablecoin_stability'] +
            correlation_score * self.risk_weights['correlation_amplification'] +
            systemic_score * self.risk_weights['systemic_contagion']
        )

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(overall_score, portfolio_info)

        # Generate risk analysis
        vulnerability_sources = self._identify_vulnerability_sources(
            liquidation_score, market_depth_score, stablecoin_score, correlation_score, systemic_score
        )

        cascade_triggers = self._calculate_cascade_trigger_probabilities(cascade_simulations)
        worst_case_impact = self._calculate_worst_case_impact(cascade_simulations, stress_tests)
        mitigation_effectiveness = self._assess_mitigation_effectiveness(portfolio_info)
        monitoring_priorities = self._generate_monitoring_priorities(vulnerability_sources)

        return CascadeRiskScore(
            liquidation_modeling_risk=liquidation_score,
            market_depth_risk=market_depth_score,
            stablecoin_stability_risk=stablecoin_score,
            correlation_amplification_risk=correlation_score,
            systemic_contagion_risk=systemic_score,
            overall_score=overall_score,
            risk_level=risk_level,
            confidence_interval=confidence_interval,
            primary_vulnerability_sources=vulnerability_sources,
            cascade_trigger_probabilities=cascade_triggers,
            worst_case_scenario_impact=worst_case_impact,
            mitigation_effectiveness=mitigation_effectiveness,
            monitoring_priorities=monitoring_priorities
        )

    def _score_liquidation_risk(self, events: List[LiquidationEvent], portfolio_info: Dict) -> float:
        """Score liquidation risk based on events and portfolio"""
        if not events:
            # Score based on current portfolio health
            health_factor = portfolio_info.get('current_health_factor', 2.0)
            if health_factor < 1.1:
                return 90.0
            elif health_factor < 1.3:
                return 70.0
            elif health_factor < 1.5:
                return 40.0
            else:
                return 15.0

        # Score based on historical liquidation events
        recent_events = [e for e in events if (datetime.utcnow() - e.timestamp).days <= 30]
        cascade_events = [e for e in events if e.cascade_depth > 0]

        base_score = min(len(recent_events) * 20, 60)
        cascade_penalty = min(len(cascade_events) * 15, 40)

        return min(base_score + cascade_penalty, 100.0)

    def _score_market_depth_risk(self, risks: List[MarketDepthRisk]) -> float:
        """Score market depth risk"""
        if not risks:
            return 20.0

        avg_liquidity_concentration = np.mean([r.liquidity_concentration for r in risks])
        avg_price_impact = np.mean([max(r.price_impact_analysis.values()) for r in risks if r.price_impact_analysis])
        avg_withdrawal_risk = np.mean([r.liquidity_withdrawal_risk for r in risks])

        score = (avg_liquidity_concentration * 40 + avg_price_impact * 30 + avg_withdrawal_risk * 30)
        return min(score, 100.0)

    def _score_stablecoin_risk(self, risks: List[StablecoinRisk]) -> float:
        """Score stablecoin stability risk"""
        if not risks:
            return 0.0

        max_depeg = max([r.current_peg_deviation for r in risks])
        avg_depeg_frequency = np.mean([r.depeg_frequency for r in risks])
        min_collateral_ratio = min([r.collateralization_ratio for r in risks])

        score = (abs(max_depeg) * 500 + avg_depeg_frequency * 10 + max(0, 1.5 - min_collateral_ratio) * 40)
        return min(score, 100.0)

    def _score_correlation_risk(self, correlation_risk: Optional[CorrelationRisk]) -> float:
        """Score correlation and systemic risk"""
        if not correlation_risk:
            return 30.0  # Medium baseline for unknown correlations

        tail_risk = correlation_risk.tail_risk_correlation * 50
        contagion_risk = len(correlation_risk.contagion_pathways) * 10
        diversification_risk = (1 - correlation_risk.diversification_effectiveness) * 40

        return min(tail_risk + contagion_risk + diversification_risk, 100.0)

    def _score_systemic_risk(self, simulations: List[CascadeSimulationResult], stress_tests: List[StressTestScenario]) -> float:
        """Score systemic contagion risk"""
        if not simulations and not stress_tests:
            return 25.0

        systemic_materializations = sum(1 for sim in simulations if sim.systemic_risk_materialized)
        max_cascade_depth = max([sim.max_cascade_depth for sim in simulations], default=0)
        worst_liquidated_value = max([sim.total_liquidated_value for sim in simulations], default=0)

        base_score = min(systemic_materializations * 25, 50)
        depth_penalty = min(max_cascade_depth * 10, 30)
        value_penalty = min(worst_liquidated_value / 1_000_000, 20)  # Per million liquidated

        return min(base_score + depth_penalty + value_penalty, 100.0)

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from numerical score"""
        thresholds = self.config['risk_thresholds']

        if score <= thresholds['low']:
            return RiskLevel.LOW
        elif score <= thresholds['medium']:
            return RiskLevel.MEDIUM
        elif score <= thresholds['high']:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _calculate_confidence_interval(self, score: float, portfolio_info: Dict) -> tuple:
        """Calculate confidence interval for risk score"""
        # Confidence depends on data quality and portfolio complexity
        base_margin = score * 0.12  # 12% base margin

        # Adjust based on portfolio complexity
        complexity = portfolio_info.get('complexity_score', 0.5)
        margin = base_margin * (1 + complexity)

        return (max(0, score - margin), min(100, score + margin))

    def _identify_vulnerability_sources(self, *scores) -> List[str]:
        """Identify primary vulnerability sources"""
        sources = []
        score_names = [
            'liquidation_modeling', 'market_depth', 'stablecoin_stability',
            'correlation_amplification', 'systemic_contagion'
        ]

        for score, name in zip(scores, score_names):
            if score > 60:
                sources.append(f"High {name.replace('_', ' ')} vulnerability")

        return sources

    def _calculate_cascade_trigger_probabilities(self, simulations: List[CascadeSimulationResult]) -> Dict[str, float]:
        """Calculate probabilities of different cascade triggers"""
        triggers = {}

        for sim in simulations:
            trigger_type = sim.initial_trigger.get('type', 'unknown')
            if trigger_type not in triggers:
                triggers[trigger_type] = 0
            triggers[trigger_type] += 1

        # Convert to probabilities
        total = len(simulations) if simulations else 1
        return {k: v / total for k, v in triggers.items()}

    def _calculate_worst_case_impact(self, simulations: List[CascadeSimulationResult], stress_tests: List[StressTestScenario]) -> float:
        """Calculate worst-case scenario impact"""
        worst_impact = 0.0

        for sim in simulations:
            impact = sim.total_liquidated_value / 1_000_000  # In millions
            worst_impact = max(worst_impact, impact)

        return worst_impact

    def _assess_mitigation_effectiveness(self, portfolio_info: Dict) -> Dict[str, float]:
        """Assess effectiveness of risk mitigation measures"""
        return {
            'diversification': portfolio_info.get('collateral_diversity', 0.5),
            'hedging': portfolio_info.get('hedging_ratio', 0.0),
            'position_sizing': 1.0 - max(portfolio_info.get('position_concentration', {}).values(), default=0),
            'monitoring': 0.7  # Placeholder for monitoring effectiveness
        }

    def _generate_monitoring_priorities(self, vulnerability_sources: List[str]) -> List[str]:
        """Generate monitoring priorities based on vulnerabilities"""
        priorities = []

        if vulnerability_sources:
            priorities.append("Health factor continuous monitoring")
            priorities.append("Market depth tracking for major positions")
            priorities.append("Correlation regime change detection")

        return priorities

    def _get_analysis_limitations(self) -> List[str]:
        """Get current analysis limitations"""
        return [
            "Cascade modeling based on historical patterns",
            "Market depth analysis limited to major DEXs",
            "Correlation analysis assumes normal market conditions",
            "Stress testing scenarios may not cover all possibilities"
        ]

    # Placeholder methods for data gathering and calculations
    async def _get_portfolio_info(self, address: str) -> Dict[str, Any]:
        """Get portfolio and position information"""
        # Placeholder implementation
        return {
            'position_concentration': {123: 0.4, 456: 0.3, 789: 0.3},
            'leverage_metrics': {'total_leverage': 2.5, 'max_leverage': 5.0},
            'collateral_diversity': 0.7,
            'liquidation_thresholds': {123: 150.0, 456: 200.0, 789: 180.0},
            'health_factor_history': [(datetime.utcnow(), 1.8)],
            'current_health_factor': 1.8,
            'complexity_score': 0.6
        }

    async def _analyze_market_environment(self) -> Dict[str, str]:
        """Analyze current market environment"""
        return {
            'volatility_regime': 'medium',
            'liquidity_environment': 'normal',
            'correlation_regime': 'normal'
        }

    async def _identify_stablecoins_in_portfolio(self, portfolio_info: Dict) -> List[int]:
        """Identify stablecoins in portfolio"""
        return []  # Placeholder

    async def _calculate_asset_correlations(self, assets: List[int]) -> Dict[int, Dict[int, float]]:
        """Calculate asset correlation matrix"""
        return {}  # Placeholder

    async def _calculate_liquidation_correlations(self, assets: List[int]) -> Dict[int, float]:
        """Calculate liquidation correlation factors"""
        return {}  # Placeholder

    async def _calculate_market_betas(self, assets: List[int]) -> Dict[int, float]:
        """Calculate market beta for assets"""
        return {}  # Placeholder

    async def _identify_systemic_risk_factors(self, assets: List[int]) -> List[str]:
        """Identify systemic risk factors"""
        return ["market_correlation", "liquidity_concentration"]

    async def _identify_contagion_pathways(self, assets: List[int], correlation_matrix: Dict) -> List[List[int]]:
        """Identify contagion pathways"""
        return []  # Placeholder

    async def _calculate_diversification_effectiveness(self, portfolio_info: Dict) -> float:
        """Calculate diversification effectiveness"""
        return portfolio_info.get('collateral_diversity', 0.5)

    async def _calculate_tail_risk_correlation(self, assets: List[int]) -> float:
        """Calculate tail risk correlation"""
        return 0.6  # Placeholder

    async def _calculate_volatility_clustering(self, assets: List[int]) -> float:
        """Calculate volatility clustering tendency"""
        return 0.4  # Placeholder

    async def _calculate_jump_risk_correlation(self, assets: List[int]) -> float:
        """Calculate jump risk correlation"""
        return 0.5  # Placeholder

    async def _simulate_cascade_scenario(self, address: str, portfolio_info: Dict, scenario: Dict) -> Optional[CascadeSimulationResult]:
        """Simulate a specific cascade scenario"""
        # Placeholder implementation
        from .models import CascadeSimulationResult
        return CascadeSimulationResult(
            scenario_name=scenario['name'],
            initial_trigger=scenario,
            total_liquidated_value=1_000_000,
            liquidation_events=[],
            max_cascade_depth=2,
            time_to_resolution_hours=4.0,
            worst_price_impact={123: 0.15, 456: 0.10},
            systemic_risk_materialized=False,
            recovery_time_estimate_hours=12.0,
            residual_risk_factors=["market_volatility"]
        )

    async def _execute_stress_test(self, address: str, portfolio_info: Dict, scenario_name: str) -> Optional[StressTestScenario]:
        """Execute a stress test scenario"""
        # Placeholder implementation
        return None