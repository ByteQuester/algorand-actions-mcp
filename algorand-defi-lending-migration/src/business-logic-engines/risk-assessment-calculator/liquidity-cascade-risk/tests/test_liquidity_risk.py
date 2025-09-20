"""
Comprehensive test suite for the Liquidity Cascade Risk Engine

This test suite validates all components of the liquidity cascade risk assessment system,
including individual modules and their integration.
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liquidity_engine import LiquidityCascadeRiskEngine, RiskLevel, AlertType
from core.cascade_modeler import LiquidationCascadeModeler, LiquidationEvent, CascadeLevel
from core.market_depth import MarketDepthAnalyzer
from core.slippage_calculator import SlippageCalculator, SlippageModel, OrderType
from core.correlation_analyzer import CorrelationAnalyzer, CorrelationType, MarketRegime
from core.stablecoin_risk import StablecoinRiskAnalyzer, DepegSeverity
from core.stress_tester import AdvancedStressTester, StressScenario, RiskMetric
from core.contagion_detector import ContagionDetector, ContagionType, ContagionSeverity

class TestLiquidationCascadeModeler:
    """Test suite for the liquidation cascade modeler"""

    @pytest.fixture
    def cascade_modeler(self):
        return LiquidationCascadeModeler()

    @pytest.mark.asyncio
    async def test_liquidation_event_creation(self, cascade_modeler):
        """Test creation of liquidation events"""
        event = LiquidationEvent(
            protocol="algofi",
            asset="ALGO",
            amount_usd=1_000_000,
            collateral_asset="ALGO",
            collateral_amount=2_000_000,
            liquidation_price=0.5,
            timestamp=datetime.now()
        )

        assert event.protocol == "algofi"
        assert event.amount_usd == 1_000_000
        assert event.cascade_level == CascadeLevel.PRIMARY

    @pytest.mark.asyncio
    async def test_cascade_modeling(self, cascade_modeler):
        """Test cascade modeling functionality"""
        liquidation_event = LiquidationEvent(
            protocol="algofi",
            asset="ALGO",
            amount_usd=2_000_000,
            collateral_asset="ALGO",
            collateral_amount=4_000_000,
            liquidation_price=0.5,
            timestamp=datetime.now()
        )

        result = await cascade_modeler.model_liquidation_cascade(liquidation_event)

        assert result.initial_event == liquidation_event
        assert result.total_impact_usd >= liquidation_event.amount_usd
        assert isinstance(result.affected_protocols, list)
        assert result.systemic_risk_score >= 0.0
        assert result.systemic_risk_score <= 1.0

    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, cascade_modeler):
        """Test real-time cascade monitoring"""
        monitoring_result = await cascade_modeler.real_time_cascade_monitoring()

        assert 'protocol_risks' in monitoring_result
        assert 'system_wide_risk' in monitoring_result
        assert 'timestamp' in monitoring_result

        # Validate protocol risk structure
        for protocol, risk_data in monitoring_result['protocol_risks'].items():
            assert 'cascade_probability' in risk_data
            assert 'alert_level' in risk_data
            assert risk_data['cascade_probability'] >= 0.0
            assert risk_data['cascade_probability'] <= 1.0

    @pytest.mark.asyncio
    async def test_scenario_analysis(self, cascade_modeler):
        """Test multiple cascade scenarios"""
        scenarios = [
            {
                'protocol': 'algofi',
                'asset': 'ALGO',
                'amount_usd': 1_000_000,
                'collateral_asset': 'ALGO',
                'collateral_amount': 2_000_000,
                'liquidation_price': 0.5
            },
            {
                'protocol': 'folks_finance',
                'asset': 'GARD',
                'amount_usd': 500_000,
                'collateral_asset': 'ALGO',
                'collateral_amount': 1_000_000,
                'liquidation_price': 0.5
            }
        ]

        results = await cascade_modeler.analyze_cascade_scenarios(scenarios)

        assert len(results) == len(scenarios)
        for result in results:
            assert result.total_impact_usd > 0
            assert isinstance(result.affected_protocols, list)

class TestMarketDepthAnalyzer:
    """Test suite for the market depth analyzer"""

    @pytest.mark.asyncio
    async def test_market_depth_analysis(self):
        """Test market depth analysis"""
        async with MarketDepthAnalyzer() as analyzer:
            asset_pairs = ['ALGO/USDC', 'GARD/ALGO']
            depth_analysis = await analyzer.analyze_market_depth(asset_pairs)

            assert len(depth_analysis) == len(asset_pairs)

            for pair, depth in depth_analysis.items():
                assert depth.total_liquidity > 0
                assert depth.aggregated_spread_bps >= 0
                assert 0 <= depth.concentration_risk <= 1
                assert isinstance(depth.dex_breakdown, dict)

    @pytest.mark.asyncio
    async def test_liquidation_impact_analysis(self):
        """Test liquidation impact analysis"""
        async with MarketDepthAnalyzer() as analyzer:
            impact = await analyzer.analyze_liquidation_impact(
                'ALGO/USDC', 1_000_000, 'sell'
            )

            assert impact['liquidation_amount_usd'] == 1_000_000
            assert impact['side'] == 'sell'
            assert impact['price_impact_pct'] >= 0
            assert impact['slippage_bps'] >= 0
            assert 0 <= impact['fill_ratio'] <= 1

    @pytest.mark.asyncio
    async def test_real_time_metrics(self):
        """Test real-time depth metrics"""
        async with MarketDepthAnalyzer() as analyzer:
            metrics = await analyzer.get_real_time_depth_metrics()

            assert 'total_ecosystem_liquidity' in metrics
            assert 'average_spread_bps' in metrics
            assert 'dex_market_shares' in metrics
            assert metrics['total_ecosystem_liquidity'] > 0

class TestSlippageCalculator:
    """Test suite for the slippage calculator"""

    @pytest.fixture
    def slippage_calculator(self):
        return SlippageCalculator()

    @pytest.mark.asyncio
    async def test_slippage_calculation(self, slippage_calculator):
        """Test basic slippage calculation"""
        result = await slippage_calculator.calculate_slippage(
            asset_pair='ALGO/USDC',
            order_amount_usd=100_000,
            side='sell',
            order_type=OrderType.MARKET,
            model=SlippageModel.ADAPTIVE
        )

        assert result.order_amount_usd == 100_000
        assert result.side == 'sell'
        assert result.slippage_pct >= 0
        assert result.price_impact_pct >= 0
        assert result.model_used == SlippageModel.ADAPTIVE
        assert len(result.confidence_interval) == 2

    @pytest.mark.asyncio
    async def test_cascade_slippage(self, slippage_calculator):
        """Test cascade slippage calculation"""
        liquidation_events = [
            {'asset_pair': 'ALGO/USDC', 'amount_usd': 1_000_000},
            {'asset_pair': 'GARD/ALGO', 'amount_usd': 500_000}
        ]

        result = await slippage_calculator.calculate_cascade_slippage(liquidation_events)

        assert result['total_events'] == len(liquidation_events)
        assert result['total_volume_usd'] == 1_500_000
        assert result['weighted_avg_slippage_pct'] >= 0
        assert 'systemic_risk_level' in result

    @pytest.mark.asyncio
    async def test_execution_optimization(self, slippage_calculator):
        """Test execution strategy optimization"""
        optimization = await slippage_calculator.optimize_execution_strategy(
            asset_pair='ALGO/USDC',
            total_amount_usd=5_000_000,
            max_slippage_bps=100,
            time_horizon_minutes=60
        )

        assert optimization['total_amount_usd'] == 5_000_000
        assert optimization['max_slippage_bps'] == 100
        assert 'optimal_strategy' in optimization
        assert 'all_strategies' in optimization

        optimal = optimization['optimal_strategy']
        assert 'chunks' in optimal
        assert 'total_slippage_bps' in optimal

class TestCorrelationAnalyzer:
    """Test suite for the correlation analyzer"""

    @pytest.fixture
    def correlation_analyzer(self):
        return CorrelationAnalyzer()

    @pytest.mark.asyncio
    async def test_correlation_analysis(self, correlation_analyzer):
        """Test correlation analysis"""
        assets = ['ALGO', 'USDC', 'GARD', 'BANK']
        result = await correlation_analyzer.analyze_correlations(
            assets=assets,
            lookback_hours=168,
            correlation_type=CorrelationType.PEARSON
        )

        assert result.correlation_type == CorrelationType.PEARSON
        assert result.matrix.shape == (len(assets), len(assets))
        assert isinstance(result.market_regime, MarketRegime)
        assert len(result.confidence_intervals) > 0

    @pytest.mark.asyncio
    async def test_contagion_detection(self, correlation_analyzer):
        """Test contagion risk detection"""
        source_events = [
            {'asset': 'ALGO', 'magnitude': 0.2}
        ]

        contagion_signals = await correlation_analyzer.detect_contagion_risk(source_events)

        for signal in contagion_signals:
            assert signal.source_asset == 'ALGO'
            assert isinstance(signal.affected_assets, list)
            assert 0 <= signal.contagion_strength <= 1
            assert signal.propagation_speed >= 0

    @pytest.mark.asyncio
    async def test_portfolio_correlation_risk(self, correlation_analyzer):
        """Test portfolio correlation risk analysis"""
        portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        risk_analysis = await correlation_analyzer.analyze_portfolio_correlation_risk(portfolio)

        assert risk_analysis['portfolio_assets'] == list(portfolio.keys())
        assert 'diversification_ratio' in risk_analysis
        assert 'concentration_risk' in risk_analysis
        assert 'contagion_vulnerability' in risk_analysis
        assert risk_analysis['risk_assessment'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

class TestStablecoinRiskAnalyzer:
    """Test suite for the stablecoin risk analyzer"""

    @pytest.fixture
    def stablecoin_analyzer(self):
        return StablecoinRiskAnalyzer()

    @pytest.mark.asyncio
    async def test_stability_analysis(self, stablecoin_analyzer):
        """Test stablecoin stability analysis"""
        for stablecoin in ['USDC', 'GARD']:
            analysis = await stablecoin_analyzer.analyze_stablecoin_stability(stablecoin)

            assert analysis.stablecoin == stablecoin
            assert analysis.current_price > 0
            assert 0 <= analysis.stability_score <= 1
            assert analysis.risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            assert analysis.time_to_recovery >= 0
            assert isinstance(analysis.stress_test_results, dict)

    @pytest.mark.asyncio
    async def test_depeg_detection(self, stablecoin_analyzer):
        """Test depeg event detection"""
        stablecoins = ['USDC', 'GARD']
        depeg_events = await stablecoin_analyzer.detect_depeg_events(stablecoins)

        for event in depeg_events:
            assert event.stablecoin in stablecoins
            assert isinstance(event.severity, DepegSeverity)
            assert event.depeg_magnitude >= 0
            assert event.duration_minutes >= 0

    @pytest.mark.asyncio
    async def test_contagion_analysis(self, stablecoin_analyzer):
        """Test stablecoin contagion analysis"""
        contagion_risk = await stablecoin_analyzer.analyze_contagion_risk('GARD', 0.05)

        assert contagion_risk.source_stablecoin == 'GARD'
        assert isinstance(contagion_risk.affected_stablecoins, list)
        assert 0 <= contagion_risk.contagion_probability <= 1
        assert isinstance(contagion_risk.spillover_magnitude, dict)

    @pytest.mark.asyncio
    async def test_ecosystem_monitoring(self, stablecoin_analyzer):
        """Test ecosystem stability monitoring"""
        ecosystem_status = await stablecoin_analyzer.monitor_ecosystem_stability()

        assert 'individual_analyses' in ecosystem_status
        assert 'ecosystem_metrics' in ecosystem_status
        assert 'alerts' in ecosystem_status

        metrics = ecosystem_status['ecosystem_metrics']
        assert 'weighted_stability_score' in metrics
        assert 'risk_distribution' in metrics

class TestAdvancedStressTester:
    """Test suite for the advanced stress tester"""

    @pytest.fixture
    def stress_tester(self):
        return AdvancedStressTester()

    @pytest.mark.asyncio
    async def test_stress_testing(self, stress_tester):
        """Test stress testing functionality"""
        portfolio = {'ALGO': 0.5, 'USDC': 0.3, 'GARD': 0.2}

        result = await stress_tester.run_stress_test(
            StressScenario.MARKET_CRASH,
            portfolio
        )

        assert result.scenario == StressScenario.MARKET_CRASH
        assert isinstance(result.risk_metrics, dict)
        assert RiskMetric.VAR_99 in result.risk_metrics
        assert 0 <= result.systemic_risk_score <= 1
        assert result.recovery_time_hours >= 0

    @pytest.mark.asyncio
    async def test_monte_carlo_simulation(self, stress_tester):
        """Test Monte Carlo simulation"""
        portfolio = {'ALGO': 0.5, 'USDC': 0.3, 'GARD': 0.2}

        result = await stress_tester.run_monte_carlo_simulation(
            num_simulations=1000,
            time_horizon_days=30,
            portfolio=portfolio
        )

        assert 'simulation_summary' in result
        assert 'return_statistics' in result
        assert 'risk_statistics' in result
        assert 'var_estimates' in result

        # Validate return statistics
        returns = result['return_statistics']
        assert 'mean' in returns
        assert 'std' in returns
        assert 'percentiles' in returns

    @pytest.mark.asyncio
    async def test_comprehensive_stress_suite(self, stress_tester):
        """Test comprehensive stress testing suite"""
        portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        results = await stress_tester.run_comprehensive_stress_suite(portfolio)

        assert 'stress_test_results' in results
        assert 'monte_carlo_results' in results
        assert 'aggregate_analysis' in results
        assert 'recommendations' in results

        # Validate aggregate analysis
        aggregate = results['aggregate_analysis']
        assert 'worst_case_analysis' in aggregate
        assert 'risk_distribution' in aggregate

class TestContagionDetector:
    """Test suite for the contagion detector"""

    @pytest.fixture
    def contagion_detector(self):
        return ContagionDetector()

    @pytest.mark.asyncio
    async def test_contagion_detection(self, contagion_detector):
        """Test contagion detection"""
        trigger_events = [
            {'protocol': 'algofi', 'magnitude': 0.3, 'type': 'liquidity_crisis'}
        ]

        contagion_events = await contagion_detector.detect_contagion_risk(trigger_events)

        for event in contagion_events:
            assert event.source_protocol == 'algofi'
            assert isinstance(event.affected_protocols, list)
            assert isinstance(event.contagion_type, ContagionType)
            assert isinstance(event.severity, ContagionSeverity)

    @pytest.mark.asyncio
    async def test_contagion_simulation(self, contagion_detector):
        """Test contagion propagation simulation"""
        initial_shock = {'algofi': 0.4, 'tinyman': 0.2}

        simulation = await contagion_detector.simulate_contagion_propagation(initial_shock)

        assert simulation.initial_shock == initial_shock
        assert isinstance(simulation.propagation_timeline, list)
        assert isinstance(simulation.final_impacts, dict)
        assert 0 <= simulation.total_system_impact <= 1
        assert simulation.cascade_depth >= 0

    @pytest.mark.asyncio
    async def test_network_vulnerabilities(self, contagion_detector):
        """Test network vulnerability analysis"""
        analysis = await contagion_detector.analyze_network_vulnerabilities()

        assert 'network_metrics' in analysis
        assert 'critical_nodes' in analysis
        assert 'pathway_vulnerabilities' in analysis
        assert 'vulnerability_assessment' in analysis

        # Validate vulnerability assessment
        vuln_assessment = analysis['vulnerability_assessment']
        assert 'overall_vulnerability' in vuln_assessment
        assert 'risk_level' in vuln_assessment
        assert vuln_assessment['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

class TestLiquidityCascadeRiskEngine:
    """Test suite for the main liquidity cascade risk engine"""

    @pytest.fixture
    def risk_engine(self):
        return LiquidityCascadeRiskEngine()

    @pytest.mark.asyncio
    async def test_comprehensive_assessment(self, risk_engine):
        """Test comprehensive risk assessment"""
        portfolio = {'ALGO': 0.4, 'USDC': 0.3, 'GARD': 0.2, 'BANK': 0.1}

        assessment = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=True,
            stress_testing=False  # Skip stress testing for faster tests
        )

        # Validate assessment structure
        assert isinstance(assessment.overall_risk_level, RiskLevel)
        assert isinstance(assessment.component_results, dict)
        assert isinstance(assessment.risk_factors, dict)
        assert isinstance(assessment.alerts, list)
        assert isinstance(assessment.recommendations, list)
        assert 0 <= assessment.confidence_score <= 1

        # Validate component results
        expected_components = [
            'cascade_analysis', 'market_depth_analysis', 'slippage_analysis',
            'correlation_analysis', 'stablecoin_analysis', 'contagion_analysis'
        ]

        for component in expected_components:
            assert component in assessment.component_results

    @pytest.mark.asyncio
    async def test_alert_generation(self, risk_engine):
        """Test alert generation functionality"""
        # First run assessment to generate some data
        portfolio = {'ALGO': 0.6, 'GARD': 0.4}  # High concentration to trigger alerts

        assessment = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=False,
            stress_testing=False
        )

        # Validate alerts
        for alert in assessment.alerts:
            assert isinstance(alert.alert_type, AlertType)
            assert isinstance(alert.severity, RiskLevel)
            assert alert.message is not None
            assert isinstance(alert.affected_assets, list)
            assert isinstance(alert.recommendations, list)

    def test_risk_status(self, risk_engine):
        """Test risk status functionality"""
        # Initially should have no data
        status = risk_engine.get_current_risk_status()
        assert 'error' in status or status['overall_risk_level'] is not None

        # Test risk history (should be empty initially)
        history = risk_engine.get_risk_history(24)
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_report_export(self, risk_engine):
        """Test assessment report export"""
        portfolio = {'ALGO': 0.5, 'USDC': 0.5}

        assessment = await risk_engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=False,
            stress_testing=False
        )

        # Export report
        report = risk_engine.export_assessment_report(assessment, 'json')

        assert isinstance(report, str)
        assert len(report) > 0

        # Should be valid JSON
        import json
        parsed_report = json.loads(report)
        assert 'assessment_id' in parsed_report
        assert 'overall_risk_level' in parsed_report

class TestIntegration:
    """Integration tests for the entire system"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        engine = LiquidityCascadeRiskEngine()

        # Define test portfolio
        portfolio = {
            'ALGO': 0.4,
            'USDC': 0.3,
            'GARD': 0.2,
            'BANK': 0.1
        }

        # Run comprehensive assessment
        assessment = await engine.run_comprehensive_assessment(
            portfolio=portfolio,
            scenario_analysis=True,
            stress_testing=False  # Skip for faster testing
        )

        # Validate the assessment was successful
        assert assessment is not None
        assert isinstance(assessment.overall_risk_level, RiskLevel)

        # Test that we can get current status
        status = engine.get_current_risk_status()
        assert 'overall_risk_level' in status

        # Test report export
        report = engine.export_assessment_report(assessment)
        assert len(report) > 100  # Should be substantial report

        print(f"Integration test completed successfully:")
        print(f"- Risk Level: {assessment.overall_risk_level.value}")
        print(f"- Confidence: {assessment.confidence_score:.2%}")
        print(f"- Alerts: {len(assessment.alerts)}")
        print(f"- Recommendations: {len(assessment.recommendations)}")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling and resilience"""
        engine = LiquidityCascadeRiskEngine()

        # Test with empty portfolio
        assessment = await engine.run_comprehensive_assessment(
            portfolio={},
            scenario_analysis=False,
            stress_testing=False
        )

        # Should handle gracefully
        assert assessment is not None

        # Test with invalid portfolio
        assessment = await engine.run_comprehensive_assessment(
            portfolio={'INVALID': 1.0},
            scenario_analysis=False,
            stress_testing=False
        )

        # Should handle gracefully
        assert assessment is not None

# Run the tests
if __name__ == "__main__":
    # Run a simple integration test
    async def simple_test():
        print("Running simple integration test...")
        engine = LiquidityCascadeRiskEngine()

        portfolio = {'ALGO': 0.5, 'USDC': 0.5}

        try:
            assessment = await engine.run_comprehensive_assessment(
                portfolio=portfolio,
                scenario_analysis=False,
                stress_testing=False
            )

            print(f"✓ Assessment completed successfully")
            print(f"  Risk Level: {assessment.overall_risk_level.value}")
            print(f"  Confidence: {assessment.confidence_score:.2%}")
            print(f"  Components: {len(assessment.component_results)}")
            print(f"  Alerts: {len(assessment.alerts)}")

        except Exception as e:
            print(f"✗ Test failed: {e}")
            raise

    asyncio.run(simple_test())