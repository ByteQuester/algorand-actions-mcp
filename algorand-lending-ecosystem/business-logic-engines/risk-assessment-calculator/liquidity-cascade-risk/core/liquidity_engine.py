"""
Liquidity Cascade Risk Engine - Master orchestrator for comprehensive liquidity risk assessment

This module serves as the central coordinator for all liquidity cascade risk analysis components,
providing a unified interface for holistic risk assessment across the Algorand DeFi ecosystem.
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
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Import all the specialized risk analysis components
from .cascade_modeler import LiquidationCascadeModeler, LiquidationEvent, CascadeResult
from .market_depth import MarketDepthAnalyzer, AggregatedDepth
from .slippage_calculator import SlippageCalculator, SlippageResult
from .correlation_analyzer import CorrelationAnalyzer, CorrelationMatrix, ContagionSignal
from .stablecoin_risk import StablecoinRiskAnalyzer, StabilityAnalysis, ContagionRisk
from .stress_tester import AdvancedStressTester, StressResult, MonteCarloSimulation
from .contagion_detector import ContagionDetector, ContagionEvent, ContagionSimulation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Overall risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SYSTEMIC = "systemic"

class AlertType(Enum):
    """Types of risk alerts"""
    LIQUIDITY_WARNING = "liquidity_warning"
    CASCADE_RISK = "cascade_risk"
    CONTAGION_ALERT = "contagion_alert"
    STABLECOIN_DEPEG = "stablecoin_depeg"
    CORRELATION_SPIKE = "correlation_spike"
    MARKET_STRESS = "market_stress"
    SYSTEMIC_RISK = "systemic_risk"

@dataclass
class RiskAlert:
    """Risk alert notification"""
    alert_id: str
    timestamp: datetime
    alert_type: AlertType
    severity: RiskLevel
    source_component: str
    affected_assets: List[str]
    affected_protocols: List[str]
    message: str
    metrics: Dict[str, float]
    recommendations: List[str]

@dataclass
class ComprehensiveRiskAssessment:
    """Comprehensive risk assessment result"""
    assessment_id: str
    timestamp: datetime
    overall_risk_level: RiskLevel
    component_results: Dict[str, Any]
    risk_factors: Dict[str, float]
    systemic_indicators: Dict[str, float]
    alerts: List[RiskAlert]
    recommendations: List[str]
    scenario_analysis: Dict[str, Any]
    confidence_score: float

@dataclass
class RealTimeMonitoring:
    """Real-time monitoring state"""
    monitoring_active: bool
    last_update: datetime
    update_interval_seconds: int
    monitored_assets: List[str]
    monitored_protocols: List[str]
    alert_thresholds: Dict[str, float]
    historical_assessments: List[ComprehensiveRiskAssessment]

class LiquidityCascadeRiskEngine:
    """
    Master liquidity cascade risk assessment engine that orchestrates all specialized
    risk analysis components to provide comprehensive, real-time risk monitoring
    and assessment for the Algorand DeFi ecosystem.
    """

    def __init__(self, config_path: str = None):
        """Initialize the liquidity cascade risk engine"""
        self.config = self._load_config(config_path)

        # Initialize all specialized components
        self.cascade_modeler = LiquidationCascadeModeler(config_path)
        self.market_depth_analyzer = MarketDepthAnalyzer(config_path)
        self.slippage_calculator = SlippageCalculator(config_path)
        self.correlation_analyzer = CorrelationAnalyzer(config_path)
        self.stablecoin_analyzer = StablecoinRiskAnalyzer(config_path)
        self.stress_tester = AdvancedStressTester(config_path)
        self.contagion_detector = ContagionDetector(config_path)

        # Risk monitoring state
        self.monitoring_state = RealTimeMonitoring(
            monitoring_active=False,
            last_update=datetime.now(),
            update_interval_seconds=self.config.get('monitoring', {}).get('update_interval', 300),
            monitored_assets=self._get_monitored_assets(),
            monitored_protocols=self._get_monitored_protocols(),
            alert_thresholds=self._get_alert_thresholds(),
            historical_assessments=[]
        )

        # Component weights for overall risk calculation
        self.component_weights = {
            'cascade_risk': 0.25,
            'market_depth': 0.15,
            'slippage_risk': 0.15,
            'correlation_risk': 0.15,
            'stablecoin_risk': 0.10,
            'stress_test_risk': 0.10,
            'contagion_risk': 0.10
        }

        # Alert management
        self.active_alerts: List[RiskAlert] = []
        self.alert_history: List[RiskAlert] = []

        logger.info("Liquidity Cascade Risk Engine initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _get_monitored_assets(self) -> List[str]:
        """Get list of assets to monitor"""
        return ['ALGO', 'USDC', 'USDT', 'GARD', 'BANK', 'OPUL', 'GOBTC', 'GOETH']

    def _get_monitored_protocols(self) -> List[str]:
        """Get list of protocols to monitor"""
        return ['algofi', 'folks_finance', 'tinyman', 'pact', 'gard', 'algodex']

    def _get_alert_thresholds(self) -> Dict[str, float]:
        """Get alert thresholds from configuration"""
        alerts_config = self.config.get('alerts', {})

        return {
            'cascade_probability': alerts_config.get('rules', {}).get('cascade_risk_high', {}).get('threshold', 0.7),
            'liquidity_crisis': alerts_config.get('rules', {}).get('liquidity_crisis', {}).get('threshold', 0.3),
            'stablecoin_depeg': alerts_config.get('rules', {}).get('stablecoin_depeg', {}).get('threshold', 0.02),
            'contagion_probability': alerts_config.get('rules', {}).get('contagion_detected', {}).get('threshold', 0.8),
            'correlation_spike': 0.3,
            'market_stress': 0.8,
            'systemic_risk': 0.8
        }

    async def run_comprehensive_assessment(
        self,
        portfolio: Dict[str, float] = None,
        scenario_analysis: bool = True,
        stress_testing: bool = True
    ) -> ComprehensiveRiskAssessment:
        """
        Run comprehensive liquidity cascade risk assessment

        Args:
            portfolio: Portfolio composition for analysis
            scenario_analysis: Whether to include scenario analysis
            stress_testing: Whether to include stress testing

        Returns:
            Comprehensive risk assessment results
        """
        logger.info("Running comprehensive liquidity cascade risk assessment")

        assessment_id = f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if portfolio is None:
            portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        # Run all component analyses in parallel
        component_tasks = {
            'cascade_analysis': self._run_cascade_analysis(),
            'market_depth_analysis': self._run_market_depth_analysis(),
            'slippage_analysis': self._run_slippage_analysis(portfolio),
            'correlation_analysis': self._run_correlation_analysis(),
            'stablecoin_analysis': self._run_stablecoin_analysis(),
            'contagion_analysis': self._run_contagion_analysis()
        }

        # Add stress testing if requested
        if stress_testing:
            component_tasks['stress_testing'] = self._run_stress_testing(portfolio)

        # Execute all analyses concurrently
        component_results = {}

        with ThreadPoolExecutor(max_workers=len(component_tasks)) as executor:
            # Submit all tasks
            future_to_component = {
                executor.submit(asyncio.run, task): component
                for component, task in component_tasks.items()
            }

            # Collect results
            for future in as_completed(future_to_component):
                component = future_to_component[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per component
                    component_results[component] = result
                except Exception as e:
                    logger.error(f"Component {component} failed: {e}")
                    component_results[component] = {'error': str(e)}

        # Calculate overall risk assessment
        overall_risk_level = self._calculate_overall_risk_level(component_results)
        risk_factors = self._extract_risk_factors(component_results)
        systemic_indicators = self._calculate_systemic_indicators(component_results)

        # Generate alerts
        alerts = self._generate_alerts(component_results, risk_factors)

        # Generate recommendations
        recommendations = self._generate_recommendations(component_results, alerts)

        # Run scenario analysis if requested
        scenario_results = {}
        if scenario_analysis:
            scenario_results = await self._run_scenario_analysis(portfolio, component_results)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(component_results)

        assessment = ComprehensiveRiskAssessment(
            assessment_id=assessment_id,
            timestamp=datetime.now(),
            overall_risk_level=overall_risk_level,
            component_results=component_results,
            risk_factors=risk_factors,
            systemic_indicators=systemic_indicators,
            alerts=alerts,
            recommendations=recommendations,
            scenario_analysis=scenario_results,
            confidence_score=confidence_score
        )

        # Store assessment
        self.monitoring_state.historical_assessments.append(assessment)

        # Update active alerts
        self._update_active_alerts(alerts)

        logger.info(f"Comprehensive assessment complete: {overall_risk_level.value} risk level")

        return assessment

    async def _run_cascade_analysis(self) -> Dict[str, Any]:
        """Run liquidation cascade analysis"""
        try:
            # Test multiple liquidation scenarios
            test_liquidations = [
                LiquidationEvent(
                    protocol="algofi",
                    asset="ALGO",
                    amount_usd=2_000_000,
                    collateral_asset="ALGO",
                    collateral_amount=4_000_000,
                    liquidation_price=0.5,
                    timestamp=datetime.now()
                ),
                LiquidationEvent(
                    protocol="folks_finance",
                    asset="GARD",
                    amount_usd=1_000_000,
                    collateral_asset="ALGO",
                    collateral_amount=2_000_000,
                    liquidation_price=0.5,
                    timestamp=datetime.now()
                )
            ]

            results = []
            for liquidation in test_liquidations:
                result = await self.cascade_modeler.model_liquidation_cascade(liquidation)
                results.append(result)

            # Real-time cascade monitoring
            real_time_risks = await self.cascade_modeler.real_time_cascade_monitoring()

            return {
                'cascade_scenarios': [result.__dict__ for result in results],
                'real_time_risks': real_time_risks,
                'statistics': self.cascade_modeler.get_cascade_statistics()
            }

        except Exception as e:
            logger.error(f"Cascade analysis failed: {e}")
            return {'error': str(e)}

    async def _run_market_depth_analysis(self) -> Dict[str, Any]:
        """Run market depth analysis"""
        try:
            async with self.market_depth_analyzer as analyzer:
                # Analyze major trading pairs
                depth_analysis = await analyzer.analyze_market_depth(
                    ['ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO', 'BANK/ALGO']
                )

                # Test liquidation impacts
                liquidation_impacts = {}
                for pair in ['ALGO/USDC', 'GARD/ALGO']:
                    impact = await analyzer.analyze_liquidation_impact(pair, 1_000_000, 'sell')
                    liquidation_impacts[pair] = impact

                # Real-time depth metrics
                real_time_metrics = await analyzer.get_real_time_depth_metrics()

                return {
                    'depth_analysis': {k: v.__dict__ for k, v in depth_analysis.items()},
                    'liquidation_impacts': liquidation_impacts,
                    'real_time_metrics': real_time_metrics
                }

        except Exception as e:
            logger.error(f"Market depth analysis failed: {e}")
            return {'error': str(e)}

    async def _run_slippage_analysis(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """Run slippage analysis"""
        try:
            # Test slippage for various order sizes
            test_orders = [
                {'pair': 'ALGO/USDC', 'amount': 100_000, 'side': 'sell'},
                {'pair': 'ALGO/USDC', 'amount': 1_000_000, 'side': 'sell'},
                {'pair': 'GARD/ALGO', 'amount': 500_000, 'side': 'sell'},
            ]

            slippage_results = {}
            for order in test_orders:
                result = await self.slippage_calculator.calculate_slippage(
                    order['pair'], order['amount'], order['side']
                )
                slippage_results[f"{order['pair']}_{order['amount']}"] = result.__dict__

            # Cascade slippage analysis
            cascade_liquidations = [
                {'asset_pair': 'ALGO/USDC', 'amount_usd': 2_000_000},
                {'asset_pair': 'GARD/ALGO', 'amount_usd': 500_000}
            ]

            cascade_slippage = await self.slippage_calculator.calculate_cascade_slippage(
                cascade_liquidations
            )

            # Execution optimization
            optimization = await self.slippage_calculator.optimize_execution_strategy(
                'ALGO/USDC', 5_000_000, 100  # $5M order, max 100 bps slippage
            )

            return {
                'slippage_tests': slippage_results,
                'cascade_slippage': cascade_slippage,
                'execution_optimization': optimization,
                'statistics': self.slippage_calculator.get_slippage_statistics()
            }

        except Exception as e:
            logger.error(f"Slippage analysis failed: {e}")
            return {'error': str(e)}

    async def _run_correlation_analysis(self) -> Dict[str, Any]:
        """Run correlation analysis"""
        try:
            # Analyze correlations across timeframes
            correlation_results = {}

            for lookback in [24, 168, 720]:  # 1 day, 1 week, 1 month
                correlation_matrix = await self.correlation_analyzer.analyze_correlations(
                    lookback_hours=lookback
                )
                correlation_results[f"{lookback}h"] = correlation_matrix.__dict__

            # Test contagion scenarios
            shock_events = [
                {'asset': 'ALGO', 'magnitude': 0.2},
                {'asset': 'GARD', 'magnitude': 0.1}
            ]

            contagion_signals = await self.correlation_analyzer.detect_contagion_risk(shock_events)

            # Portfolio correlation analysis
            portfolio_risk = await self.correlation_analyzer.analyze_portfolio_correlation_risk(
                {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}
            )

            return {
                'correlation_analysis': correlation_results,
                'contagion_signals': [signal.__dict__ for signal in contagion_signals],
                'portfolio_risk': portfolio_risk,
                'statistics': self.correlation_analyzer.get_correlation_statistics()
            }

        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            return {'error': str(e)}

    async def _run_stablecoin_analysis(self) -> Dict[str, Any]:
        """Run stablecoin risk analysis"""
        try:
            # Analyze all major stablecoins
            stablecoin_analyses = {}
            stablecoins = ['USDC', 'USDT', 'GARD']

            for stablecoin in stablecoins:
                try:
                    analysis = await self.stablecoin_analyzer.analyze_stablecoin_stability(stablecoin)
                    stablecoin_analyses[stablecoin] = analysis.__dict__
                except Exception as e:
                    logger.warning(f"Stablecoin analysis failed for {stablecoin}: {e}")
                    stablecoin_analyses[stablecoin] = {'error': str(e)}

            # Detect depeg events
            depeg_events = await self.stablecoin_analyzer.detect_depeg_events(stablecoins)

            # Test contagion between stablecoins
            contagion_analysis = {}
            for stablecoin in stablecoins:
                try:
                    contagion = await self.stablecoin_analyzer.analyze_contagion_risk(stablecoin, 0.03)
                    contagion_analysis[stablecoin] = contagion.__dict__
                except Exception as e:
                    logger.warning(f"Contagion analysis failed for {stablecoin}: {e}")

            # Ecosystem stability monitoring
            ecosystem_stability = await self.stablecoin_analyzer.monitor_ecosystem_stability()

            return {
                'stablecoin_analyses': stablecoin_analyses,
                'depeg_events': [event.__dict__ for event in depeg_events],
                'contagion_analysis': contagion_analysis,
                'ecosystem_stability': ecosystem_stability,
                'statistics': self.stablecoin_analyzer.get_stability_statistics()
            }

        except Exception as e:
            logger.error(f"Stablecoin analysis failed: {e}")
            return {'error': str(e)}

    async def _run_stress_testing(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """Run stress testing"""
        try:
            # Run comprehensive stress testing suite
            stress_results = await self.stress_tester.run_comprehensive_stress_suite(portfolio)

            # Additional Monte Carlo analysis
            monte_carlo = await self.stress_tester.run_monte_carlo_simulation(
                num_simulations=5000,
                time_horizon_days=30,
                portfolio=portfolio
            )

            return {
                'comprehensive_stress_results': stress_results,
                'monte_carlo_analysis': monte_carlo,
                'statistics': self.stress_tester.get_stress_test_statistics()
            }

        except Exception as e:
            logger.error(f"Stress testing failed: {e}")
            return {'error': str(e)}

    async def _run_contagion_analysis(self) -> Dict[str, Any]:
        """Run contagion analysis"""
        try:
            # Test contagion scenarios
            trigger_events = [
                {'protocol': 'algofi', 'magnitude': 0.3, 'type': 'liquidity_crisis'},
                {'protocol': 'tinyman', 'magnitude': 0.2, 'type': 'smart_contract_exploit'}
            ]

            contagion_events = await self.contagion_detector.detect_contagion_risk(trigger_events)

            # Run contagion simulations
            simulation_results = []
            test_shocks = [
                {'algofi': 0.4},
                {'tinyman': 0.3, 'pact': 0.2},
                {'gard': 0.5}
            ]

            for shock in test_shocks:
                simulation = await self.contagion_detector.simulate_contagion_propagation(shock)
                simulation_results.append(simulation.__dict__)

            # Network vulnerability analysis
            vulnerability_analysis = await self.contagion_detector.analyze_network_vulnerabilities()

            return {
                'contagion_events': [event.__dict__ for event in contagion_events],
                'simulation_results': simulation_results,
                'network_vulnerabilities': vulnerability_analysis,
                'statistics': self.contagion_detector.get_contagion_statistics()
            }

        except Exception as e:
            logger.error(f"Contagion analysis failed: {e}")
            return {'error': str(e)}

    def _calculate_overall_risk_level(self, component_results: Dict[str, Any]) -> RiskLevel:
        """Calculate overall risk level from component results"""
        risk_scores = {}

        # Extract risk scores from each component
        try:
            # Cascade risk
            if 'cascade_analysis' in component_results and 'real_time_risks' in component_results['cascade_analysis']:
                system_risk = component_results['cascade_analysis']['real_time_risks'].get('system_wide_risk', {})
                risk_scores['cascade_risk'] = system_risk.get('risk_level', 0.0)

            # Market depth risk
            if 'market_depth_analysis' in component_results:
                depth_metrics = component_results['market_depth_analysis'].get('real_time_metrics', {})
                # Calculate risk from liquidity concentration
                concentration = depth_metrics.get('max_concentration_risk', 0.0)
                risk_scores['market_depth'] = concentration

            # Slippage risk
            if 'slippage_analysis' in component_results:
                cascade_slippage = component_results['slippage_analysis'].get('cascade_slippage', {})
                systemic_risk = cascade_slippage.get('systemic_risk_level', 'LOW')
                risk_mapping = {'LOW': 0.2, 'MEDIUM': 0.4, 'HIGH': 0.7, 'CRITICAL': 0.9}
                risk_scores['slippage_risk'] = risk_mapping.get(systemic_risk, 0.2)

            # Correlation risk
            if 'correlation_analysis' in component_results:
                portfolio_risk = component_results['correlation_analysis'].get('portfolio_risk', {})
                risk_assessment = portfolio_risk.get('risk_assessment', 'LOW')
                risk_mapping = {'LOW': 0.2, 'MEDIUM': 0.4, 'HIGH': 0.7, 'CRITICAL': 0.9}
                risk_scores['correlation_risk'] = risk_mapping.get(risk_assessment, 0.2)

            # Stablecoin risk
            if 'stablecoin_analysis' in component_results:
                ecosystem = component_results['stablecoin_analysis'].get('ecosystem_stability', {})
                ecosystem_metrics = ecosystem.get('ecosystem_metrics', {})
                weighted_stability = ecosystem_metrics.get('weighted_stability_score', 0.8)
                risk_scores['stablecoin_risk'] = 1.0 - weighted_stability  # Invert stability to risk

            # Stress test risk
            if 'stress_testing' in component_results:
                stress_results = component_results['stress_testing'].get('comprehensive_stress_results', {})
                aggregate = stress_results.get('aggregate_analysis', {})
                worst_case = aggregate.get('worst_case_analysis', {})
                worst_risk = worst_case.get('worst_systemic_risk', 0.0)
                risk_scores['stress_test_risk'] = worst_risk

            # Contagion risk
            if 'contagion_analysis' in component_results:
                vulnerabilities = component_results['contagion_analysis'].get('network_vulnerabilities', {})
                vulnerability_assessment = vulnerabilities.get('vulnerability_assessment', {})
                overall_vulnerability = vulnerability_assessment.get('overall_vulnerability', 0.0)
                risk_scores['contagion_risk'] = overall_vulnerability

        except Exception as e:
            logger.warning(f"Error calculating risk scores: {e}")

        # Calculate weighted average risk
        total_weighted_risk = 0.0
        total_weight = 0.0

        for component, weight in self.component_weights.items():
            if component in risk_scores:
                total_weighted_risk += risk_scores[component] * weight
                total_weight += weight

        overall_risk = total_weighted_risk / total_weight if total_weight > 0 else 0.0

        # Map to risk levels
        if overall_risk < 0.2:
            return RiskLevel.LOW
        elif overall_risk < 0.4:
            return RiskLevel.MEDIUM
        elif overall_risk < 0.6:
            return RiskLevel.HIGH
        elif overall_risk < 0.8:
            return RiskLevel.CRITICAL
        else:
            return RiskLevel.SYSTEMIC

    def _extract_risk_factors(self, component_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract key risk factors from component results"""
        risk_factors = {}

        try:
            # Liquidity risk factors
            if 'market_depth_analysis' in component_results:
                depth_metrics = component_results['market_depth_analysis'].get('real_time_metrics', {})
                risk_factors['total_ecosystem_liquidity'] = depth_metrics.get('total_ecosystem_liquidity', 0)
                risk_factors['average_spread_bps'] = depth_metrics.get('average_spread_bps', 0)

            # Cascade risk factors
            if 'cascade_analysis' in component_results:
                real_time = component_results['cascade_analysis'].get('real_time_risks', {})
                system_risk = real_time.get('system_wide_risk', {})
                risk_factors['cascade_probability'] = system_risk.get('risk_level', 0.0)

            # Correlation risk factors
            if 'correlation_analysis' in component_results:
                latest_correlation = None
                for timeframe, data in component_results['correlation_analysis'].get('correlation_analysis', {}).items():
                    if 'correlation_shift' in data:
                        risk_factors['correlation_shift'] = data['correlation_shift']
                        break

            # Stablecoin risk factors
            if 'stablecoin_analysis' in component_results:
                for coin, analysis in component_results['stablecoin_analysis'].get('stablecoin_analyses', {}).items():
                    if 'current_depeg' in analysis:
                        risk_factors[f'{coin}_depeg'] = analysis['current_depeg']

            # Contagion risk factors
            if 'contagion_analysis' in component_results:
                network_vuln = component_results['contagion_analysis'].get('network_vulnerabilities', {})
                systemic_indicators = network_vuln.get('systemic_risk_indicators', {})
                risk_factors['network_concentration'] = systemic_indicators.get('network_concentration_hhi', 0)
                risk_factors['contagion_potential'] = systemic_indicators.get('contagion_potential', 0)

        except Exception as e:
            logger.warning(f"Error extracting risk factors: {e}")

        return risk_factors

    def _calculate_systemic_indicators(self, component_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate systemic risk indicators"""
        indicators = {}

        try:
            # System-wide liquidity indicator
            if 'market_depth_analysis' in component_results:
                depth_metrics = component_results['market_depth_analysis'].get('real_time_metrics', {})
                total_liquidity = depth_metrics.get('total_ecosystem_liquidity', 0)
                indicators['liquidity_adequacy'] = min(1.0, total_liquidity / 100_000_000)  # Normalize to $100M

            # Systemic cascade risk
            if 'cascade_analysis' in component_results:
                stats = component_results['cascade_analysis'].get('statistics', {})
                indicators['systemic_cascade_events'] = stats.get('systemic_events', 0)

            # Network resilience
            if 'contagion_analysis' in component_results:
                stats = component_results['contagion_analysis'].get('statistics', {})
                network_health = stats.get('network_health', {})
                indicators['network_resilience'] = network_health.get('network_resilience_score', 0.5)

            # Stablecoin stability
            if 'stablecoin_analysis' in component_results:
                ecosystem = component_results['stablecoin_analysis'].get('ecosystem_stability', {})
                ecosystem_metrics = ecosystem.get('ecosystem_metrics', {})
                indicators['stablecoin_stability'] = ecosystem_metrics.get('weighted_stability_score', 0.8)

            # Stress test resilience
            if 'stress_testing' in component_results:
                monte_carlo = component_results['stress_testing'].get('monte_carlo_analysis', {})
                risk_stats = monte_carlo.get('risk_statistics', {})
                indicators['tail_risk_exposure'] = risk_stats.get('probability_extreme_loss', 0.0)

        except Exception as e:
            logger.warning(f"Error calculating systemic indicators: {e}")

        return indicators

    def _generate_alerts(
        self,
        component_results: Dict[str, Any],
        risk_factors: Dict[str, float]
    ) -> List[RiskAlert]:
        """Generate risk alerts based on analysis results"""
        alerts = []
        thresholds = self.monitoring_state.alert_thresholds

        try:
            # Cascade risk alerts
            cascade_prob = risk_factors.get('cascade_probability', 0.0)
            if cascade_prob > thresholds['cascade_probability']:
                alerts.append(RiskAlert(
                    alert_id=f"cascade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    timestamp=datetime.now(),
                    alert_type=AlertType.CASCADE_RISK,
                    severity=RiskLevel.HIGH if cascade_prob > 0.8 else RiskLevel.MEDIUM,
                    source_component="cascade_modeler",
                    affected_assets=self.monitoring_state.monitored_assets,
                    affected_protocols=self.monitoring_state.monitored_protocols,
                    message=f"High cascade probability detected: {cascade_prob:.2%}",
                    metrics={'cascade_probability': cascade_prob},
                    recommendations=["Monitor liquidation positions closely", "Consider reducing leverage"]
                ))

            # Liquidity crisis alerts
            total_liquidity = risk_factors.get('total_ecosystem_liquidity', float('inf'))
            if total_liquidity < thresholds['liquidity_crisis'] * 100_000_000:  # $30M threshold
                alerts.append(RiskAlert(
                    alert_id=f"liquidity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    timestamp=datetime.now(),
                    alert_type=AlertType.LIQUIDITY_WARNING,
                    severity=RiskLevel.HIGH,
                    source_component="market_depth_analyzer",
                    affected_assets=self.monitoring_state.monitored_assets,
                    affected_protocols=self.monitoring_state.monitored_protocols,
                    message=f"Low ecosystem liquidity: ${total_liquidity:,.0f}",
                    metrics={'total_liquidity': total_liquidity},
                    recommendations=["Avoid large trades", "Monitor market depth before transactions"]
                ))

            # Stablecoin depeg alerts
            for coin in ['USDC', 'USDT', 'GARD']:
                depeg_key = f'{coin}_depeg'
                if depeg_key in risk_factors:
                    depeg_magnitude = risk_factors[depeg_key]
                    if depeg_magnitude > thresholds['stablecoin_depeg']:
                        alerts.append(RiskAlert(
                            alert_id=f"depeg_{coin}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            timestamp=datetime.now(),
                            alert_type=AlertType.STABLECOIN_DEPEG,
                            severity=RiskLevel.CRITICAL if depeg_magnitude > 0.05 else RiskLevel.HIGH,
                            source_component="stablecoin_analyzer",
                            affected_assets=[coin],
                            affected_protocols=self.monitoring_state.monitored_protocols,
                            message=f"{coin} depegging detected: {depeg_magnitude:.3f} from peg",
                            metrics={f'{coin}_depeg': depeg_magnitude},
                            recommendations=[f"Monitor {coin} stability", "Consider alternative stablecoins"]
                        ))

            # Contagion alerts
            contagion_potential = risk_factors.get('contagion_potential', 0.0)
            if contagion_potential > thresholds['contagion_probability']:
                alerts.append(RiskAlert(
                    alert_id=f"contagion_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    timestamp=datetime.now(),
                    alert_type=AlertType.CONTAGION_ALERT,
                    severity=RiskLevel.HIGH,
                    source_component="contagion_detector",
                    affected_assets=self.monitoring_state.monitored_assets,
                    affected_protocols=self.monitoring_state.monitored_protocols,
                    message=f"High contagion risk detected: {contagion_potential:.2%}",
                    metrics={'contagion_potential': contagion_potential},
                    recommendations=["Diversify protocol exposure", "Monitor cross-protocol dependencies"]
                ))

        except Exception as e:
            logger.warning(f"Error generating alerts: {e}")

        return alerts

    def _generate_recommendations(
        self,
        component_results: Dict[str, Any],
        alerts: List[RiskAlert]
    ) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        try:
            # General recommendations based on alerts
            if any(alert.alert_type == AlertType.CASCADE_RISK for alert in alerts):
                recommendations.extend([
                    "Reduce leverage and maintain higher collateral ratios",
                    "Monitor liquidation thresholds across all positions",
                    "Consider implementing circuit breakers for large positions"
                ])

            if any(alert.alert_type == AlertType.LIQUIDITY_WARNING for alert in alerts):
                recommendations.extend([
                    "Avoid large market orders during low liquidity periods",
                    "Use limit orders and break large trades into smaller chunks",
                    "Monitor market depth before executing significant transactions"
                ])

            if any(alert.alert_type == AlertType.STABLECOIN_DEPEG for alert in alerts):
                recommendations.extend([
                    "Diversify stablecoin holdings across different mechanisms",
                    "Monitor stablecoin stability mechanisms and reserve ratios",
                    "Consider temporarily reducing stablecoin exposure"
                ])

            if any(alert.alert_type == AlertType.CONTAGION_ALERT for alert in alerts):
                recommendations.extend([
                    "Diversify across multiple protocols and avoid concentration",
                    "Monitor cross-protocol dependencies and shared infrastructure",
                    "Implement position limits per protocol"
                ])

            # Component-specific recommendations
            if 'stress_testing' in component_results:
                stress_results = component_results['stress_testing']
                if 'recommendations' in stress_results.get('comprehensive_stress_results', {}):
                    recommendations.extend(stress_results['comprehensive_stress_results']['recommendations'])

            # Remove duplicates while preserving order
            unique_recommendations = []
            for rec in recommendations:
                if rec not in unique_recommendations:
                    unique_recommendations.append(rec)

            return unique_recommendations[:10]  # Limit to top 10 recommendations

        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            return ["Monitor market conditions closely", "Maintain conservative risk parameters"]

    async def _run_scenario_analysis(
        self,
        portfolio: Dict[str, float],
        component_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run scenario analysis based on component results"""
        scenarios = {}

        try:
            # Best case scenario
            scenarios['best_case'] = {
                'description': 'Optimal market conditions with high liquidity and low correlation',
                'expected_return': 0.15,
                'max_drawdown': 0.05,
                'probability': 0.2
            }

            # Base case scenario
            scenarios['base_case'] = {
                'description': 'Normal market conditions',
                'expected_return': 0.08,
                'max_drawdown': 0.15,
                'probability': 0.6
            }

            # Stress scenario
            stress_results = component_results.get('stress_testing', {})
            if 'comprehensive_stress_results' in stress_results:
                worst_case = stress_results['comprehensive_stress_results'].get('aggregate_analysis', {})
                worst_risk = worst_case.get('worst_case_analysis', {})

                scenarios['stress_case'] = {
                    'description': 'Market stress with elevated correlation and reduced liquidity',
                    'expected_return': -0.25,
                    'max_drawdown': 0.4,
                    'probability': 0.15,
                    'worst_scenario': worst_risk.get('worst_scenario', 'unknown'),
                    'recovery_time': worst_risk.get('worst_recovery_time', 72)
                }

            # Black swan scenario
            scenarios['black_swan'] = {
                'description': 'Extreme tail event with systemic contagion',
                'expected_return': -0.5,
                'max_drawdown': 0.8,
                'probability': 0.05,
                'systemic_impact': True
            }

        except Exception as e:
            logger.warning(f"Error in scenario analysis: {e}")

        return scenarios

    def _calculate_confidence_score(self, component_results: Dict[str, Any]) -> float:
        """Calculate confidence score in the assessment"""
        confidence_factors = []

        try:
            # Data quality factors
            successful_components = sum(1 for result in component_results.values() if 'error' not in result)
            total_components = len(component_results)
            data_quality = successful_components / total_components if total_components > 0 else 0

            confidence_factors.append(data_quality)

            # Component-specific confidence
            if 'stress_testing' in component_results and 'error' not in component_results['stress_testing']:
                # Monte Carlo simulations provide high confidence
                confidence_factors.append(0.9)

            if 'correlation_analysis' in component_results and 'error' not in component_results['correlation_analysis']:
                # Correlation analysis based on historical data
                confidence_factors.append(0.8)

            # Market conditions factor
            market_volatility = 0.3  # Would get from real market data
            volatility_confidence = max(0.3, 1.0 - market_volatility)
            confidence_factors.append(volatility_confidence)

            # Calculate weighted average
            overall_confidence = np.mean(confidence_factors) if confidence_factors else 0.5

            return min(max(overall_confidence, 0.1), 0.95)  # Clamp between 10% and 95%

        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
            return 0.5

    def _update_active_alerts(self, new_alerts: List[RiskAlert]):
        """Update active alerts list"""
        # Remove expired alerts (older than 24 hours)
        current_time = datetime.now()
        self.active_alerts = [
            alert for alert in self.active_alerts
            if (current_time - alert.timestamp).total_seconds() < 86400
        ]

        # Add new alerts
        for alert in new_alerts:
            # Check if similar alert already exists
            similar_exists = any(
                existing.alert_type == alert.alert_type and
                existing.source_component == alert.source_component
                for existing in self.active_alerts
            )

            if not similar_exists:
                self.active_alerts.append(alert)

        # Move old alerts to history
        for alert in new_alerts:
            self.alert_history.append(alert)

    async def start_real_time_monitoring(
        self,
        update_interval_seconds: int = None
    ) -> None:
        """Start real-time risk monitoring"""
        if update_interval_seconds:
            self.monitoring_state.update_interval_seconds = update_interval_seconds

        self.monitoring_state.monitoring_active = True

        logger.info(f"Starting real-time monitoring with {self.monitoring_state.update_interval_seconds}s intervals")

        while self.monitoring_state.monitoring_active:
            try:
                # Run abbreviated assessment
                assessment = await self.run_comprehensive_assessment(
                    scenario_analysis=False,
                    stress_testing=False  # Skip stress testing in real-time mode
                )

                self.monitoring_state.last_update = datetime.now()

                # Log current status
                logger.info(f"Real-time update: {assessment.overall_risk_level.value} risk, "
                           f"{len(assessment.alerts)} active alerts")

                # Wait for next update
                await asyncio.sleep(self.monitoring_state.update_interval_seconds)

            except Exception as e:
                logger.error(f"Real-time monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    def stop_real_time_monitoring(self):
        """Stop real-time risk monitoring"""
        self.monitoring_state.monitoring_active = False
        logger.info("Real-time monitoring stopped")

    def get_current_risk_status(self) -> Dict[str, Any]:
        """Get current risk status summary"""
        if not self.monitoring_state.historical_assessments:
            return {'error': 'No assessments available'}

        latest_assessment = self.monitoring_state.historical_assessments[-1]

        return {
            'timestamp': latest_assessment.timestamp.isoformat(),
            'overall_risk_level': latest_assessment.overall_risk_level.value,
            'active_alerts': len(self.active_alerts),
            'confidence_score': latest_assessment.confidence_score,
            'key_risk_factors': latest_assessment.risk_factors,
            'systemic_indicators': latest_assessment.systemic_indicators,
            'monitoring_active': self.monitoring_state.monitoring_active,
            'last_update': self.monitoring_state.last_update.isoformat()
        }

    def get_risk_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get risk assessment history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_assessments = [
            assessment for assessment in self.monitoring_state.historical_assessments
            if assessment.timestamp >= cutoff_time
        ]

        return [
            {
                'timestamp': assessment.timestamp.isoformat(),
                'risk_level': assessment.overall_risk_level.value,
                'confidence_score': assessment.confidence_score,
                'alert_count': len(assessment.alerts)
            }
            for assessment in recent_assessments
        ]

    def export_assessment_report(
        self,
        assessment: ComprehensiveRiskAssessment,
        format_type: str = 'json'
    ) -> str:
        """Export assessment report in specified format"""
        report_data = {
            'assessment_id': assessment.assessment_id,
            'timestamp': assessment.timestamp.isoformat(),
            'overall_risk_level': assessment.overall_risk_level.value,
            'confidence_score': assessment.confidence_score,
            'risk_factors': assessment.risk_factors,
            'systemic_indicators': assessment.systemic_indicators,
            'alerts': [
                {
                    'type': alert.alert_type.value,
                    'severity': alert.severity.value,
                    'message': alert.message,
                    'affected_assets': alert.affected_assets,
                    'affected_protocols': alert.affected_protocols
                }
                for alert in assessment.alerts
            ],
            'recommendations': assessment.recommendations,
            'scenario_analysis': assessment.scenario_analysis
        }

        if format_type.lower() == 'json':
            return json.dumps(report_data, indent=2)
        else:
            # Could add other formats like CSV, PDF, etc.
            return json.dumps(report_data, indent=2)


# Example usage and testing
async def main():
    """Example usage of the liquidity cascade risk engine"""
    engine = LiquidityCascadeRiskEngine()

    # Run comprehensive assessment
    portfolio = {'ALGO': 0.5, 'USDC': 0.3, 'GARD': 0.15, 'BANK': 0.05}

    assessment = await engine.run_comprehensive_assessment(
        portfolio=portfolio,
        scenario_analysis=True,
        stress_testing=True
    )

    print("Comprehensive Risk Assessment Results:")
    print(f"Overall Risk Level: {assessment.overall_risk_level.value}")
    print(f"Confidence Score: {assessment.confidence_score:.2%}")
    print(f"Active Alerts: {len(assessment.alerts)}")

    # Display key risk factors
    print("\nKey Risk Factors:")
    for factor, value in assessment.risk_factors.items():
        print(f"  {factor}: {value}")

    # Display alerts
    if assessment.alerts:
        print("\nActive Alerts:")
        for alert in assessment.alerts:
            print(f"  {alert.alert_type.value}: {alert.message}")

    # Display recommendations
    print("\nRecommendations:")
    for rec in assessment.recommendations[:5]:  # Show top 5
        print(f"  - {rec}")

    # Get current risk status
    status = engine.get_current_risk_status()
    print(f"\nCurrent Status:")
    print(f"Risk Level: {status.get('overall_risk_level', 'unknown')}")
    print(f"Monitoring Active: {status.get('monitoring_active', False)}")

    # Export report
    report = engine.export_assessment_report(assessment)
    print(f"\nReport exported: {len(report)} characters")

if __name__ == "__main__":
    asyncio.run(main())