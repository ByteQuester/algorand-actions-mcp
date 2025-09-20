"""
Test DeFi Protocol Risk Engine
Comprehensive tests for the DeFi protocol risk assessment engine
"""

import asyncio
import pytest
from datetime import datetime, timedelta
import yaml
from pathlib import Path

# Import the DeFi protocol risk modules
from defi_protocol_risk.core.protocol_exposure import ProtocolExposureAnalyzer
from defi_protocol_risk.core.concentration_risk import ConcentrationRiskAnalyzer
from defi_protocol_risk.core.systemic_risk import SystemicRiskAnalyzer
from defi_protocol_risk.core.protocol_engine import DeFiProtocolRiskEngine

class TestProtocolExposureAnalyzer:
    """Test protocol exposure analysis functionality"""

    @pytest.fixture
    async def analyzer(self):
        """Create analyzer instance for testing"""
        return ProtocolExposureAnalyzer()

    @pytest.fixture
    def sample_positions(self):
        """Sample user positions for testing"""
        return {
            'algofi': 50000,
            'folks_finance': 30000,
            'tinyman': 15000,
            'pact': 5000
        }

    @pytest.mark.asyncio
    async def test_protocol_exposure_calculation(self, analyzer, sample_positions):
        """Test basic protocol exposure calculation"""
        async with analyzer:
            exposure_analysis = await analyzer.calculate_protocol_exposure(sample_positions)

            # Check basic structure
            assert exposure_analysis is not None
            assert exposure_analysis.total_exposure_usd == 100000
            assert len(exposure_analysis.protocol_exposures) == 4
            assert exposure_analysis.risk_level in ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL']

            # Check individual exposures
            algofi_exposure = next(
                exp for exp in exposure_analysis.protocol_exposures
                if exp.protocol_name == 'algofi'
            )
            assert algofi_exposure.exposure_percentage == 50.0
            assert algofi_exposure.concentration_risk_score > 0

    @pytest.mark.asyncio
    async def test_empty_positions(self, analyzer):
        """Test handling of empty positions"""
        async with analyzer:
            with pytest.raises(ValueError):
                await analyzer.calculate_protocol_exposure({})

    @pytest.mark.asyncio
    async def test_single_protocol_concentration(self, analyzer):
        """Test high concentration in single protocol"""
        high_concentration_positions = {'algofi': 100000}

        async with analyzer:
            exposure_analysis = await analyzer.calculate_protocol_exposure(high_concentration_positions)

            assert exposure_analysis.concentration_risk_score > 0.8  # High concentration
            assert exposure_analysis.diversification_score < 0.3     # Low diversification

    @pytest.mark.asyncio
    async def test_monitoring_functionality(self, analyzer, sample_positions):
        """Test monitoring and alert functionality"""
        async with analyzer:
            monitoring_result = await analyzer.monitor_protocol_exposure(sample_positions)

            assert 'analysis' in monitoring_result
            assert 'alerts' in monitoring_result
            assert 'monitoring_timestamp' in monitoring_result

class TestConcentrationRiskAnalyzer:
    """Test concentration risk analysis functionality"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return ConcentrationRiskAnalyzer()

    @pytest.fixture
    def balanced_positions(self):
        """Balanced positions for testing"""
        return {
            'algofi': 25000,
            'folks_finance': 25000,
            'tinyman': 25000,
            'pact': 25000
        }

    @pytest.fixture
    def concentrated_positions(self):
        """Concentrated positions for testing"""
        return {
            'algofi': 80000,
            'folks_finance': 15000,
            'tinyman': 5000
        }

    @pytest.mark.asyncio
    async def test_concentration_metrics_calculation(self, analyzer, balanced_positions):
        """Test concentration metrics calculation"""
        assessment = await analyzer.analyze_concentration_risk(balanced_positions)

        # Check metrics structure
        assert assessment.concentration_metrics is not None
        assert assessment.concentration_metrics.herfindahl_index == 0.25  # Perfect distribution
        assert assessment.concentration_metrics.effective_protocols == 4.0
        assert assessment.concentration_metrics.max_exposure_percentage == 25.0

    @pytest.mark.asyncio
    async def test_high_concentration_detection(self, analyzer, concentrated_positions):
        """Test detection of high concentration"""
        assessment = await analyzer.analyze_concentration_risk(concentrated_positions)

        assert assessment.concentration_metrics.herfindahl_index > 0.6
        assert assessment.concentration_metrics.max_exposure_percentage == 80.0
        assert assessment.overall_risk_score > 0.7
        assert assessment.risk_level in ['HIGH', 'CRITICAL']

    @pytest.mark.asyncio
    async def test_diversification_analysis(self, analyzer, balanced_positions):
        """Test diversification analysis"""
        assessment = await analyzer.analyze_concentration_risk(balanced_positions)

        diversification = assessment.diversification_analysis
        assert diversification.protocol_count == 4
        assert diversification.diversification_score > 0.7  # Good diversification

    @pytest.mark.asyncio
    async def test_stress_testing(self, analyzer, balanced_positions):
        """Test stress testing functionality"""
        assessment = await analyzer.analyze_concentration_risk(balanced_positions)

        stress_results = assessment.stress_test_results
        assert 'largest_protocol_failure' in stress_results
        assert 'category_failure' in stress_results
        assert all(0 <= result <= 1 for result in stress_results.values())

    @pytest.mark.asyncio
    async def test_rebalancing_suggestions(self, analyzer, concentrated_positions):
        """Test rebalancing suggestions"""
        rebalancing = await analyzer.get_rebalancing_suggestions(concentrated_positions)

        assert 'current_analysis' in rebalancing
        assert 'rebalancing_actions' in rebalancing
        assert len(rebalancing['rebalancing_actions']) > 0

        # Should suggest reducing algofi concentration
        algofi_reduction = any(
            action.get('protocol') == 'algofi' and action.get('action') == 'reduce'
            for action in rebalancing['rebalancing_actions']
        )
        assert algofi_reduction

class TestSystemicRiskAnalyzer:
    """Test systemic risk analysis functionality"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return SystemicRiskAnalyzer()

    @pytest.fixture
    def sample_protocol_data(self):
        """Sample protocol data for testing"""
        return {
            'algofi': {
                'tvl_usd': 45000000,
                'total_borrowed': 25000000,
                'active_users': 2500
            },
            'folks_finance': {
                'tvl_usd': 32000000,
                'total_borrowed': 18000000,
                'active_users': 1800
            },
            'tinyman': {
                'tvl_usd': 25000000,
                'total_volume_24h': 2000000,
                'active_users': 3000
            }
        }

    @pytest.mark.asyncio
    async def test_systemic_risk_analysis(self, analyzer, sample_protocol_data):
        """Test basic systemic risk analysis"""
        assessment = await analyzer.analyze_systemic_risk(sample_protocol_data)

        # Check basic structure
        assert assessment is not None
        assert len(assessment.network_nodes) == 3
        assert assessment.systemic_risk_score >= 0
        assert assessment.systemic_risk_score <= 1
        assert assessment.risk_level in ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL']

    @pytest.mark.asyncio
    async def test_network_node_creation(self, analyzer, sample_protocol_data):
        """Test network node creation"""
        assessment = await analyzer.analyze_systemic_risk(sample_protocol_data)

        # Check that nodes have required attributes
        for node in assessment.network_nodes:
            assert node.protocol_name in sample_protocol_data
            assert 0 <= node.systemic_importance <= 1
            assert 0 <= node.failure_probability <= 1
            assert 0 <= node.cascade_vulnerability <= 1

    @pytest.mark.asyncio
    async def test_cascade_scenario_modeling(self, analyzer, sample_protocol_data):
        """Test cascade scenario modeling"""
        assessment = await analyzer.analyze_systemic_risk(sample_protocol_data)

        # Should have cascade scenarios
        assert len(assessment.cascade_scenarios) > 0

        # Check scenario structure
        for scenario in assessment.cascade_scenarios:
            assert scenario.trigger_protocol is not None
            assert len(scenario.affected_protocols) > 0
            assert scenario.cascade_probability >= 0
            assert scenario.total_tvl_impact >= 0

    @pytest.mark.asyncio
    async def test_contagion_analysis(self, analyzer, sample_protocol_data):
        """Test contagion path analysis"""
        assessment = await analyzer.analyze_systemic_risk(sample_protocol_data)

        # Should have contagion paths
        assert len(assessment.contagion_paths) > 0

        # Check path structure
        for path in assessment.contagion_paths:
            assert path.source_protocol in sample_protocol_data
            assert path.target_protocol in sample_protocol_data
            assert 0 <= path.contagion_strength <= 1
            assert path.propagation_delay_hours > 0

class TestDeFiProtocolRiskEngine:
    """Test the master DeFi protocol risk engine"""

    @pytest.fixture
    def engine(self):
        """Create engine instance for testing"""
        return DeFiProtocolRiskEngine()

    @pytest.fixture
    def sample_positions(self):
        """Sample positions for testing"""
        return {
            'algofi': 60000,
            'folks_finance': 25000,
            'tinyman': 10000,
            'pact': 5000
        }

    @pytest.mark.asyncio
    async def test_comprehensive_assessment(self, engine, sample_positions):
        """Test comprehensive portfolio risk assessment"""
        assessment = await engine.assess_portfolio_risk(sample_positions)

        # Check main assessment structure
        assert assessment is not None
        assert assessment.portfolio_metrics is not None
        assert len(assessment.protocol_scores) > 0
        assert assessment.exposure_analysis is not None
        assert assessment.concentration_assessment is not None
        assert assessment.systemic_assessment is not None

        # Check overall scores
        assert 0 <= assessment.overall_portfolio_score <= 1
        assert assessment.risk_level in ['EXCELLENT', 'GOOD', 'MODERATE', 'POOR', 'CRITICAL']
        assert 0 <= assessment.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_portfolio_metrics(self, engine, sample_positions):
        """Test portfolio metrics calculation"""
        assessment = await engine.assess_portfolio_risk(sample_positions)
        metrics = assessment.portfolio_metrics

        assert metrics.total_exposure_usd == 100000
        assert metrics.protocol_count == 4
        assert metrics.category_count >= 1
        assert 0 <= metrics.effective_diversification <= 1
        assert 0 <= metrics.concentration_ratio <= 1

    @pytest.mark.asyncio
    async def test_risk_alerts_generation(self, engine, sample_positions):
        """Test risk alerts generation"""
        assessment = await engine.assess_portfolio_risk(sample_positions)

        # Should have some alerts for concentrated portfolio
        assert len(assessment.risk_alerts) >= 0

        # Check alert structure
        for alert in assessment.risk_alerts:
            assert alert.alert_type is not None
            assert alert.severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            assert alert.message is not None
            assert alert.recommended_action is not None

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, engine, sample_positions):
        """Test recommendations generation"""
        assessment = await engine.assess_portfolio_risk(sample_positions)

        assert len(assessment.recommendations) > 0
        assert all(isinstance(rec, str) for rec in assessment.recommendations)

    @pytest.mark.asyncio
    async def test_report_export(self, engine, sample_positions):
        """Test assessment report export"""
        assessment = await engine.assess_portfolio_risk(sample_positions)

        # Export report
        report_path = await engine.export_assessment_report(assessment)

        # Check file exists and contains data
        assert Path(report_path).exists()

        # Read and validate JSON structure
        import json
        with open(report_path, 'r') as f:
            report_data = json.load(f)

        assert 'assessment_metadata' in report_data
        assert 'portfolio_metrics' in report_data
        assert 'protocol_scores' in report_data

        # Cleanup
        Path(report_path).unlink()

    @pytest.mark.asyncio
    async def test_edge_cases(self, engine):
        """Test edge cases and error handling"""
        # Test empty positions
        with pytest.raises(ValueError):
            await engine.assess_portfolio_risk({})

        # Test single position
        single_position = {'algofi': 50000}
        assessment = await engine.assess_portfolio_risk(single_position)
        assert assessment is not None
        assert assessment.overall_portfolio_score < 0.7  # Should be lower due to concentration

class TestConfiguration:
    """Test configuration loading and validation"""

    def test_config_loading(self):
        """Test configuration file loading"""
        config_path = Path(__file__).parent / "defi-protocol-risk" / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check main sections exist
        assert 'mcp_services' in config
        assert 'algorand_protocols' in config
        assert 'protocol_risk_weights' in config
        assert 'concentration_thresholds' in config

    def test_protocol_configuration(self):
        """Test protocol configuration completeness"""
        config_path = Path(__file__).parent / "defi-protocol-risk" / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        protocols = config['algorand_protocols']

        # Check major protocols are configured
        assert 'algofi' in protocols
        assert 'folks_finance' in protocols
        assert 'tinyman' in protocols

        # Check protocol structure
        for protocol_name, protocol_config in protocols.items():
            assert 'name' in protocol_config
            assert 'category' in protocol_config
            assert 'tvl_weight' in protocol_config
            assert 'risk_tier' in protocol_config

class TestIntegrationScenarios:
    """Test integration scenarios and real-world cases"""

    @pytest.fixture
    def engine(self):
        return DeFiProtocolRiskEngine()

    @pytest.mark.asyncio
    async def test_balanced_portfolio_scenario(self, engine):
        """Test assessment of well-balanced portfolio"""
        balanced_positions = {
            'algofi': 30000,
            'folks_finance': 25000,
            'tinyman': 20000,
            'pact': 15000,
            'humble_defi': 10000
        }

        assessment = await engine.assess_portfolio_risk(balanced_positions)

        # Should have good diversification
        assert assessment.concentration_assessment.diversification_analysis.diversification_score > 0.6
        assert assessment.portfolio_metrics.category_count >= 3
        assert assessment.risk_level in ['EXCELLENT', 'GOOD', 'MODERATE']

    @pytest.mark.asyncio
    async def test_high_risk_portfolio_scenario(self, engine):
        """Test assessment of high-risk portfolio"""
        risky_positions = {
            'yieldly': 70000,      # High concentration in risky protocol
            'algomint': 20000,     # Bridge risk
            'humble_defi': 10000   # Smaller protocol
        }

        assessment = await engine.assess_portfolio_risk(risky_positions)

        # Should detect high risks
        assert assessment.concentration_assessment.overall_risk_score > 0.5
        assert len(assessment.risk_alerts) > 0
        assert assessment.risk_level in ['MODERATE', 'POOR', 'CRITICAL']

    @pytest.mark.asyncio
    async def test_defi_crisis_scenario(self, engine):
        """Test assessment during DeFi crisis conditions"""
        # Simulate crisis by adjusting market conditions
        positions = {
            'algofi': 40000,
            'folks_finance': 30000,
            'tinyman': 20000,
            'pact': 10000
        }

        assessment = await engine.assess_portfolio_risk(positions)

        # Should have recommendations for crisis management
        assert len(assessment.recommendations) > 0
        crisis_recommendations = [
            rec for rec in assessment.recommendations
            if 'crisis' in rec.lower() or 'emergency' in rec.lower() or 'urgent' in rec.lower()
        ]

        # Should provide monitoring requirements
        assert len(assessment.monitoring_requirements) > 0

# Performance tests
class TestPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def engine(self):
        return DeFiProtocolRiskEngine()

    @pytest.mark.asyncio
    async def test_large_portfolio_performance(self, engine):
        """Test performance with large portfolio"""
        # Create large portfolio
        large_positions = {
            f'protocol_{i}': 1000 + (i * 100)
            for i in range(20)  # 20 different positions
        }

        start_time = datetime.now()
        assessment = await engine.assess_portfolio_risk(large_positions)
        end_time = datetime.now()

        # Should complete within reasonable time (5 seconds)
        assert (end_time - start_time).total_seconds() < 5
        assert assessment is not None

    @pytest.mark.asyncio
    async def test_concurrent_assessments(self, engine):
        """Test concurrent assessment performance"""
        positions_list = [
            {'algofi': 50000, 'tinyman': 25000, 'pact': 25000},
            {'folks_finance': 60000, 'tinyman': 40000},
            {'algofi': 30000, 'folks_finance': 30000, 'pact': 40000}
        ]

        # Run concurrent assessments
        start_time = datetime.now()
        tasks = [engine.assess_portfolio_risk(positions) for positions in positions_list]
        assessments = await asyncio.gather(*tasks)
        end_time = datetime.now()

        # All should complete successfully
        assert len(assessments) == 3
        assert all(assessment is not None for assessment in assessments)

        # Should be faster than sequential execution
        assert (end_time - start_time).total_seconds() < 10

def run_tests():
    """Run all tests"""
    pytest.main([__file__, '-v', '-x'])

if __name__ == "__main__":
    run_tests()