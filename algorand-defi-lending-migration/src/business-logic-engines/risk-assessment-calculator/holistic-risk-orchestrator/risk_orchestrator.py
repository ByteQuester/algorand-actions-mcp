"""
Holistic Risk Orchestrator

Master orchestrator that combines all risk engines and provides comprehensive
Algorand-native risk assessment with cross-engine correlation analysis.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from .models import (
    HolisticRiskProfile, HolisticRiskScore, RiskLevel, RiskEngine,
    CrossEngineCorrelation, RiskAlert, MitigationStrategy,
    MonitoringConfiguration, ScenarioAnalysis, RiskTrend
)
from .holistic_scoring import HolisticRiskScorer
from .risk_correlation import RiskCorrelationAnalyzer
from .alert_manager import RiskAlertManager
from .mitigation_engine import RiskMitigationEngine
from .monitoring_scheduler import RiskMonitoringScheduler

# Import risk engines
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain_behavior_engine.behavior_analyzer import BlockchainBehaviorAnalyzer
from defi_protocol_engine.protocol_analyzer import DeFiProtocolAnalyzer
from liquidity_cascade_engine.cascade_analyzer import LiquidityCascadeAnalyzer
from governance_stability_engine.governance_analyzer import GovernanceStabilityAnalyzer

logger = logging.getLogger(__name__)


class HolisticRiskOrchestrator:
    """
    Master orchestrator for comprehensive Algorand risk assessment
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

        # Initialize individual risk engines
        self.blockchain_analyzer = BlockchainBehaviorAnalyzer(self.config.get('blockchain_behavior', {}))
        self.defi_analyzer = DeFiProtocolAnalyzer(self.config.get('defi_protocol', {}))
        self.cascade_analyzer = LiquidityCascadeAnalyzer(self.config.get('liquidity_cascade', {}))
        self.governance_analyzer = GovernanceStabilityAnalyzer(self.config.get('governance_stability', {}))

        # Initialize orchestration components
        self.holistic_scorer = HolisticRiskScorer(self.config.get('holistic_scoring', {}))
        self.correlation_analyzer = RiskCorrelationAnalyzer(self.config.get('correlation_analysis', {}))
        self.alert_manager = RiskAlertManager(self.config.get('alert_management', {}))
        self.mitigation_engine = RiskMitigationEngine(self.config.get('mitigation', {}))
        self.monitoring_scheduler = RiskMonitoringScheduler(self.config.get('monitoring', {}))

        # Risk engine weights for holistic scoring
        self.engine_weights = self.config.get('engine_weights', {
            RiskEngine.BLOCKCHAIN_BEHAVIOR: 0.25,
            RiskEngine.DEFI_PROTOCOL: 0.25,
            RiskEngine.LIQUIDITY_CASCADE: 0.25,
            RiskEngine.GOVERNANCE_STABILITY: 0.25
        })

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for holistic risk orchestration"""
        return {
            'enable_real_time_monitoring': True,
            'enable_cross_engine_correlation': True,
            'enable_automated_alerts': True,
            'enable_mitigation_recommendations': True,
            'analysis_depth': 'comprehensive',
            'correlation_threshold': 0.5,
            'alert_thresholds': {
                RiskLevel.LOW: 25,
                RiskLevel.MEDIUM: 50,
                RiskLevel.HIGH: 75,
                RiskLevel.CRITICAL: 90
            },
            'scenario_analysis_enabled': True,
            'trend_analysis_window_days': 30,
            'max_concurrent_analyses': 10,
            'data_sources': ['on_chain', 'defi_protocols', 'governance', 'market_data']
        }

    async def assess_holistic_risk(
        self,
        address: str,
        include_scenario_analysis: bool = True,
        include_trend_analysis: bool = True,
        enable_real_time_monitoring: bool = True
    ) -> HolisticRiskProfile:
        """
        Perform comprehensive holistic risk assessment

        Args:
            address: Algorand address to assess
            include_scenario_analysis: Whether to include scenario analysis
            include_trend_analysis: Whether to include trend analysis
            enable_real_time_monitoring: Whether to enable ongoing monitoring

        Returns:
            Complete holistic risk profile
        """
        try:
            logger.info(f"Starting holistic risk assessment for address: {address}")

            # Run all risk engines in parallel
            engine_tasks = [
                self._run_blockchain_behavior_analysis(address),
                self._run_defi_protocol_analysis(address),
                self._run_liquidity_cascade_analysis(address),
                self._run_governance_stability_analysis(address)
            ]

            engine_results = await asyncio.gather(*engine_tasks, return_exceptions=True)

            # Parse individual engine results
            blockchain_profile = engine_results[0] if not isinstance(engine_results[0], Exception) else None
            defi_profile = engine_results[1] if not isinstance(engine_results[1], Exception) else None
            cascade_profile = engine_results[2] if not isinstance(engine_results[2], Exception) else None
            governance_profile = engine_results[3] if not isinstance(engine_results[3], Exception) else None

            # Perform cross-engine correlation analysis
            correlations = await self.correlation_analyzer.analyze_cross_engine_correlations(
                blockchain_profile, defi_profile, cascade_profile, governance_profile
            )

            # Calculate holistic risk score
            holistic_score = await self.holistic_scorer.calculate_holistic_score(
                blockchain_profile, defi_profile, cascade_profile, governance_profile,
                correlations, self.engine_weights
            )

            # Generate and process alerts
            alerts = await self.alert_manager.generate_alerts(
                address, holistic_score, blockchain_profile, defi_profile,
                cascade_profile, governance_profile, correlations
            )

            # Generate mitigation recommendations
            mitigations = await self.mitigation_engine.generate_mitigation_strategies(
                address, holistic_score, correlations, alerts
            )

            # Optional advanced analysis
            scenario_analyses = []
            risk_trends = []

            if include_scenario_analysis:
                scenario_analyses = await self._perform_scenario_analysis(
                    address, blockchain_profile, defi_profile, cascade_profile, governance_profile
                )

            if include_trend_analysis:
                risk_trends = await self._perform_trend_analysis(
                    address, self.config['trend_analysis_window_days']
                )

            # Set up real-time monitoring if enabled
            monitoring_config = None
            if enable_real_time_monitoring:
                monitoring_config = await self._setup_monitoring(address, holistic_score)

            # Calculate portfolio context
            portfolio_context = await self._analyze_portfolio_context(
                address, blockchain_profile, defi_profile, cascade_profile
            )

            # Assess market environment
            market_regime = await self._assess_market_environment()

            # Create comprehensive holistic profile
            profile = HolisticRiskProfile(
                address=address,
                assessment_timestamp=datetime.utcnow(),
                blockchain_behavior_profile=blockchain_profile,
                defi_protocol_profile=defi_profile,
                liquidity_cascade_profile=cascade_profile,
                governance_stability_profile=governance_profile,
                cross_engine_correlations=correlations,
                systemic_risk_factors=await self._identify_systemic_risk_factors(correlations),
                risk_amplification_chains=await self._identify_risk_amplification_chains(correlations),
                holistic_risk_score=holistic_score,
                active_alerts=alerts,
                monitoring_configuration=monitoring_config,
                recommended_mitigations=mitigations,
                implemented_mitigations=[],  # Would track actual implementations
                scenario_analyses=scenario_analyses,
                risk_trends=risk_trends,
                portfolio_value_at_risk=portfolio_context.get('var', 0.0),
                position_concentration_risk=portfolio_context.get('concentration', {}),
                diversification_effectiveness=portfolio_context.get('diversification', 0.0),
                hedging_effectiveness=portfolio_context.get('hedging', 0.0),
                market_regime=market_regime,
                regulatory_environment=await self._assess_regulatory_environment(),
                competitive_landscape=await self._assess_competitive_landscape(),
                data_quality_score=await self._calculate_data_quality_score(
                    blockchain_profile, defi_profile, cascade_profile, governance_profile
                ),
                analysis_completeness=await self._calculate_analysis_completeness(
                    blockchain_profile, defi_profile, cascade_profile, governance_profile
                ),
                limitations=self._get_analysis_limitations(),
                data_sources=self.config['data_sources'],
                analysis_version="1.0.0"
            )

            # Start monitoring if enabled
            if enable_real_time_monitoring and monitoring_config:
                await self.monitoring_scheduler.start_monitoring(address, profile)

            logger.info(f"Holistic risk assessment completed. Overall risk: {holistic_score.risk_level.value}")
            return profile

        except Exception as e:
            logger.error(f"Error in holistic risk assessment for {address}: {e}")
            raise

    async def _run_blockchain_behavior_analysis(self, address: str):
        """Run blockchain behavior risk analysis"""
        try:
            return await self.blockchain_analyzer.analyze_address_behavior(address)
        except Exception as e:
            logger.error(f"Blockchain behavior analysis failed: {e}")
            return None

    async def _run_defi_protocol_analysis(self, address: str):
        """Run DeFi protocol risk analysis"""
        try:
            # For DeFi analysis, we need to identify protocols the address interacts with
            protocols = await self._identify_defi_protocols(address)
            if protocols:
                # Analyze the primary protocol
                return await self.defi_analyzer.analyze_protocol_risk(protocols[0])
            return None
        except Exception as e:
            logger.error(f"DeFi protocol analysis failed: {e}")
            return None

    async def _run_liquidity_cascade_analysis(self, address: str):
        """Run liquidity cascade risk analysis"""
        try:
            return await self.cascade_analyzer.analyze_cascade_risk(address)
        except Exception as e:
            logger.error(f"Liquidity cascade analysis failed: {e}")
            return None

    async def _run_governance_stability_analysis(self, address: str):
        """Run governance stability risk analysis"""
        try:
            # For governance analysis, we analyze the Algorand network as a whole
            return await self.governance_analyzer.analyze_governance_risk("algorand_mainnet")
        except Exception as e:
            logger.error(f"Governance stability analysis failed: {e}")
            return None

    async def _perform_scenario_analysis(self, address: str, *profiles) -> List[ScenarioAnalysis]:
        """Perform scenario analysis across all risk engines"""
        try:
            scenarios = []

            # Define key scenarios for Algorand ecosystem
            scenario_definitions = [
                {
                    'name': 'Algorand Network Stress',
                    'type': 'stress_test',
                    'description': 'High transaction load with validator performance degradation',
                    'probability': 0.15,
                    'market_conditions': {'tps_load': 2.0, 'validator_performance': 0.7},
                    'external_shocks': {'network_latency': 1.5, 'consensus_delays': 1.8}
                },
                {
                    'name': 'DeFi Cascade Event',
                    'type': 'historical',
                    'description': 'Major DeFi protocol failure causing cascade liquidations',
                    'probability': 0.08,
                    'market_conditions': {'defi_tvl_shock': -0.40, 'liquidity_crisis': True},
                    'external_shocks': {'stablecoin_depeg': -0.05, 'oracle_manipulation': True}
                },
                {
                    'name': 'Governance Attack',
                    'type': 'synthetic',
                    'description': 'Coordinated governance token accumulation and malicious proposals',
                    'probability': 0.05,
                    'market_conditions': {'governance_concentration': 0.8},
                    'external_shocks': {'proposal_spam': True, 'validator_coordination': True}
                },
                {
                    'name': 'Regulatory Crackdown',
                    'type': 'stress_test',
                    'description': 'Major jurisdiction implements restrictive crypto regulations',
                    'probability': 0.20,
                    'market_conditions': {'regulatory_pressure': 1.0, 'compliance_costs': 2.0},
                    'external_shocks': {'exchange_restrictions': True, 'institutional_withdrawal': True}
                },
                {
                    'name': 'Black Swan Market Event',
                    'type': 'black_swan',
                    'description': 'Unprecedented market crash with correlation breakdown',
                    'probability': 0.02,
                    'market_conditions': {'market_crash': -0.70, 'correlation_breakdown': True},
                    'external_shocks': {'liquidity_evaporation': True, 'system_failures': True}
                }
            ]

            for scenario_def in scenario_definitions:
                analysis = await self._analyze_scenario_impact(address, scenario_def, *profiles)
                if analysis:
                    scenarios.append(analysis)

            return scenarios

        except Exception as e:
            logger.error(f"Scenario analysis failed: {e}")
            return []

    async def _perform_trend_analysis(self, address: str, window_days: int) -> List[RiskTrend]:
        """Perform trend analysis for each risk engine"""
        try:
            trends = []

            for engine in RiskEngine:
                trend = await self._analyze_engine_trend(address, engine, window_days)
                if trend:
                    trends.append(trend)

            return trends

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return []

    async def _setup_monitoring(self, address: str, risk_score: HolisticRiskScore) -> MonitoringConfiguration:
        """Set up real-time monitoring configuration"""
        from .models import MonitoringConfiguration, AlertSeverity

        # Determine monitoring frequency based on risk level
        if risk_score.risk_level == RiskLevel.CRITICAL:
            frequency = 60  # Every minute
        elif risk_score.risk_level == RiskLevel.HIGH:
            frequency = 300  # Every 5 minutes
        elif risk_score.risk_level == RiskLevel.MEDIUM:
            frequency = 900  # Every 15 minutes
        else:
            frequency = 3600  # Every hour

        return MonitoringConfiguration(
            monitoring_frequency_seconds=frequency,
            risk_threshold_levels=self.config['alert_thresholds'],
            alert_escalation_rules={
                AlertSeverity.WARNING: {'notify_team': True, 'auto_acknowledge': False},
                AlertSeverity.HIGH: {'notify_team': True, 'escalate_after_minutes': 30},
                AlertSeverity.CRITICAL: {'notify_team': True, 'escalate_after_minutes': 10, 'auto_mitigation': True},
                AlertSeverity.EMERGENCY: {'notify_team': True, 'immediate_escalation': True, 'auto_mitigation': True}
            },
            correlation_monitoring_enabled=True,
            real_time_data_sources=['algorand_indexer', 'defi_protocols', 'governance_api'],
            historical_analysis_window_days=7,
            anomaly_detection_sensitivity=0.8,
            automated_response_enabled=risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            notification_channels=['email', 'slack', 'webhook'],
            monitoring_scope={engine: True for engine in RiskEngine}
        )

    async def _analyze_portfolio_context(self, address: str, *profiles) -> Dict[str, Any]:
        """Analyze portfolio context for risk assessment"""
        try:
            # Extract portfolio information from profiles
            portfolio_data = {}

            # From blockchain behavior profile
            if profiles[0]:  # blockchain_profile
                portfolio_data['transaction_patterns'] = getattr(profiles[0], 'transaction_patterns', [])

            # From DeFi protocol profile
            if profiles[1]:  # defi_profile
                portfolio_data['defi_exposures'] = getattr(profiles[1], 'cross_protocol_exposures', [])

            # From liquidity cascade profile
            if profiles[2]:  # cascade_profile
                portfolio_data['position_concentration'] = getattr(profiles[2], 'position_concentration', {})
                portfolio_data['leverage_metrics'] = getattr(profiles[2], 'leverage_metrics', {})

            # Calculate portfolio metrics
            var = await self._calculate_value_at_risk(portfolio_data)
            concentration = await self._calculate_concentration_risk(portfolio_data)
            diversification = await self._calculate_diversification_effectiveness(portfolio_data)
            hedging = await self._calculate_hedging_effectiveness(portfolio_data)

            return {
                'var': var,
                'concentration': concentration,
                'diversification': diversification,
                'hedging': hedging
            }

        except Exception as e:
            logger.error(f"Portfolio context analysis failed: {e}")
            return {}

    async def _assess_market_environment(self) -> Dict[str, str]:
        """Assess current market environment across different dimensions"""
        return {
            'volatility': 'medium',
            'liquidity': 'normal',
            'correlation': 'normal',
            'sentiment': 'neutral',
            'macro_environment': 'stable'
        }

    async def _assess_regulatory_environment(self) -> str:
        """Assess current regulatory environment"""
        return 'evolving'  # Could be 'favorable', 'neutral', 'restrictive', 'evolving'

    async def _assess_competitive_landscape(self) -> str:
        """Assess competitive landscape"""
        return 'competitive'  # Could be 'monopolistic', 'competitive', 'fragmented'

    async def _calculate_data_quality_score(self, *profiles) -> float:
        """Calculate overall data quality score"""
        quality_scores = []

        for profile in profiles:
            if profile and hasattr(profile, 'data_sources'):
                # Simple quality scoring based on data source diversity
                quality_scores.append(min(len(profile.data_sources) / 4, 1.0))

        return np.mean(quality_scores) if quality_scores else 0.7

    async def _calculate_analysis_completeness(self, *profiles) -> float:
        """Calculate analysis completeness score"""
        completed_engines = sum(1 for profile in profiles if profile is not None)
        return completed_engines / len(RiskEngine)

    def _get_analysis_limitations(self) -> List[str]:
        """Get current analysis limitations"""
        return [
            "Cross-engine correlation analysis based on current market conditions",
            "Scenario analysis limited to predefined scenarios",
            "Real-time monitoring subject to data source availability",
            "Mitigation recommendations require manual implementation validation"
        ]

    # Helper methods with placeholder implementations
    async def _identify_defi_protocols(self, address: str) -> List[str]:
        """Identify DeFi protocols the address interacts with"""
        # Placeholder - would analyze transaction history to identify protocol interactions
        return ["tinyman", "algofi", "yieldly"]

    async def _identify_systemic_risk_factors(self, correlations: List[CrossEngineCorrelation]) -> List[str]:
        """Identify systemic risk factors from correlations"""
        factors = []

        high_correlation_pairs = [
            c for c in correlations
            if c.correlation_strength in ["strong", "very_strong"]
        ]

        if high_correlation_pairs:
            factors.append("High cross-engine risk correlation")

        amplification_risks = [
            c for c in correlations
            if c.risk_amplification_factor > 1.5
        ]

        if amplification_risks:
            factors.append("Risk amplification effects present")

        return factors

    async def _identify_risk_amplification_chains(self, correlations: List[CrossEngineCorrelation]) -> List[List[RiskEngine]]:
        """Identify risk amplification chains"""
        # Placeholder for complex network analysis
        chains = []

        # Simple example: if we have strong correlations, create basic chains
        strong_correlations = [
            c for c in correlations
            if c.correlation_strength == "very_strong"
        ]

        for correlation in strong_correlations:
            chains.append([correlation.engine_1, correlation.engine_2])

        return chains

    async def _analyze_scenario_impact(self, address: str, scenario_def: Dict, *profiles) -> Optional[ScenarioAnalysis]:
        """Analyze impact of a specific scenario"""
        from .models import ScenarioAnalysis

        # Placeholder implementation
        return ScenarioAnalysis(
            scenario_name=scenario_def['name'],
            scenario_type=scenario_def['type'],
            scenario_description=scenario_def['description'],
            probability_estimate=scenario_def['probability'],
            market_conditions=scenario_def['market_conditions'],
            external_shocks=scenario_def['external_shocks'],
            behavioral_assumptions={},
            impact_by_engine={
                RiskEngine.BLOCKCHAIN_BEHAVIOR: 0.3,
                RiskEngine.DEFI_PROTOCOL: 0.5,
                RiskEngine.LIQUIDITY_CASCADE: 0.7,
                RiskEngine.GOVERNANCE_STABILITY: 0.2
            },
            overall_impact_score=0.4,
            cascading_effects=["Liquidity reduction", "Increased correlation"],
            recovery_time_estimate_hours=24.0,
            current_resilience_score=0.6,
            recommended_preparations=["Increase cash reserves", "Reduce leverage"],
            early_warning_indicators=["Unusual transaction patterns", "Governance proposal activity"]
        )

    async def _analyze_engine_trend(self, address: str, engine: RiskEngine, window_days: int) -> Optional[RiskTrend]:
        """Analyze trend for a specific risk engine"""
        from .models import RiskTrend

        # Placeholder implementation
        base_time = datetime.utcnow() - timedelta(days=window_days)
        history = [
            (base_time + timedelta(days=i), 30 + i * 0.5 + np.random.normal(0, 5))
            for i in range(window_days)
        ]

        return RiskTrend(
            engine=engine,
            time_period_days=window_days,
            trend_direction="increasing",
            trend_strength=0.3,
            risk_score_history=history,
            volatility=5.0,
            momentum=0.1,
            seasonal_patterns={},
            anomalies_detected=[],
            forecast_next_30_days=[]
        )

    # Portfolio analysis placeholders
    async def _calculate_value_at_risk(self, portfolio_data: Dict) -> float:
        """Calculate portfolio Value at Risk"""
        return 50000.0  # Placeholder

    async def _calculate_concentration_risk(self, portfolio_data: Dict) -> Dict[str, float]:
        """Calculate position concentration risks"""
        return {'max_position': 0.4, 'top_5_positions': 0.7}  # Placeholder

    async def _calculate_diversification_effectiveness(self, portfolio_data: Dict) -> float:
        """Calculate diversification effectiveness"""
        return 0.6  # Placeholder

    async def _calculate_hedging_effectiveness(self, portfolio_data: Dict) -> float:
        """Calculate hedging effectiveness"""
        return 0.3  # Placeholder