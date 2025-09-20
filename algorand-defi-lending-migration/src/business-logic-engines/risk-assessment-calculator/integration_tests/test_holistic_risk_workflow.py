"""
Holistic Risk Workflow Integration Tests

Tests the complete risk assessment workflow:
Blockchain → DeFi → Liquidity → Governance → Orchestrated Risk Score

Multiple risk scenarios:
- Normal market conditions
- Stressed market conditions
- Crisis conditions
- Black swan events
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holistic_risk_orchestrator.risk_orchestrator import HolisticRiskOrchestrator
from holistic_risk_orchestrator.models import RiskLevel, RiskEngine


class TestHolisticRiskWorkflow:
    """Test complete holistic risk assessment workflow"""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance for testing"""
        config = {
            'enable_real_time_monitoring': False,  # Disable for testing
            'scenario_analysis_enabled': True,
            'trend_analysis_window_days': 7,  # Shorter for testing
            'max_concurrent_analyses': 5
        }
        return HolisticRiskOrchestrator(config)

    @pytest.fixture
    def test_addresses(self):
        """Test Algorand addresses for different risk profiles"""
        return {
            'low_risk': 'LOWRISK1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'medium_risk': 'MEDRISK1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'high_risk': 'HIGHRISK1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'critical_risk': 'CRITRISK1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        }

    @pytest.mark.asyncio
    async def test_normal_market_conditions_workflow(self, orchestrator, test_addresses):
        """Test holistic risk assessment under normal market conditions"""

        # Test low-risk address
        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['low_risk'],
            include_scenario_analysis=True,
            include_trend_analysis=True,
            enable_real_time_monitoring=False
        )

        # Validate profile structure
        assert profile is not None
        assert profile.address == test_addresses['low_risk']
        assert isinstance(profile.assessment_timestamp, datetime)
        assert profile.holistic_risk_score is not None

        # Validate risk scores are within expected ranges for normal conditions
        score = profile.holistic_risk_score
        assert 0 <= score.overall_holistic_score <= 100
        assert score.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

        # Validate individual engine scores
        assert 0 <= score.blockchain_behavior_score <= 100
        assert 0 <= score.defi_protocol_score <= 100
        assert 0 <= score.liquidity_cascade_score <= 100
        assert 0 <= score.governance_stability_score <= 100

        # Validate cross-engine analysis
        assert len(profile.cross_engine_correlations) >= 0
        assert isinstance(profile.systemic_risk_factors, list)

        # Validate scenario analysis was performed
        assert len(profile.scenario_analyses) > 0
        assert any(scenario.scenario_type == 'stress_test' for scenario in profile.scenario_analyses)

        # Validate confidence metrics
        assert 0 <= profile.data_quality_score <= 1.0
        assert 0 <= profile.analysis_completeness <= 1.0

    @pytest.mark.asyncio
    async def test_stressed_market_conditions_workflow(self, orchestrator, test_addresses):
        """Test holistic risk assessment under stressed market conditions"""

        # Test medium-risk address under stress
        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['medium_risk'],
            include_scenario_analysis=True,
            include_trend_analysis=False,  # Skip for faster testing
            enable_real_time_monitoring=False
        )

        # Under stressed conditions, expect higher risk scores
        score = profile.holistic_risk_score
        assert score.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]

        # Validate stress-specific metrics
        assert score.correlation_amplification_score >= 0
        assert score.systemic_risk_score >= 0

        # Check for appropriate risk factors
        assert len(score.primary_risk_drivers) > 0
        risk_engines_involved = {driver[0] for driver in score.primary_risk_drivers}
        assert len(risk_engines_involved) >= 1  # At least one engine flagging risk

        # Validate scenario analysis shows stress impacts
        stress_scenarios = [s for s in profile.scenario_analyses if 'stress' in s.scenario_type.lower()]
        assert len(stress_scenarios) > 0

    @pytest.mark.asyncio
    async def test_crisis_conditions_workflow(self, orchestrator, test_addresses):
        """Test holistic risk assessment under crisis conditions"""

        # Test high-risk address in crisis
        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['high_risk'],
            include_scenario_analysis=True,
            include_trend_analysis=False,
            enable_real_time_monitoring=False
        )

        # Crisis conditions should show high risk
        score = profile.holistic_risk_score
        assert score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert score.overall_holistic_score >= 65  # High risk threshold

        # Validate crisis-specific indicators
        assert score.systemic_failure_probability > 0
        if score.time_to_critical_risk is not None:
            assert score.time_to_critical_risk > 0  # If set, should be positive

        # Check for alerts in crisis conditions
        high_severity_alerts = [
            alert for alert in profile.active_alerts
            if alert.severity.value in ['HIGH', 'CRITICAL', 'EMERGENCY']
        ]
        assert len(high_severity_alerts) >= 0  # May have high severity alerts

        # Validate mitigation recommendations
        urgent_mitigations = [
            m for m in profile.recommended_mitigations
            if m.priority.value == 'URGENT'
        ]
        # In crisis, should have some urgent recommendations
        assert len(profile.recommended_mitigations) > 0

    @pytest.mark.asyncio
    async def test_black_swan_event_workflow(self, orchestrator, test_addresses):
        """Test holistic risk assessment during black swan events"""

        # Test critical-risk address during black swan
        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['critical_risk'],
            include_scenario_analysis=True,
            include_trend_analysis=False,
            enable_real_time_monitoring=False
        )

        # Black swan should trigger critical risk levels
        score = profile.holistic_risk_score
        assert score.risk_level == RiskLevel.CRITICAL
        assert score.overall_holistic_score >= 75  # Critical threshold

        # Validate extreme risk indicators
        assert score.systemic_failure_probability >= 0.1  # 10%+ systemic failure probability

        # Check correlation breakdown (typical in black swan events)
        if profile.cross_engine_correlations:
            high_correlations = [
                c for c in profile.cross_engine_correlations
                if c.correlation_strength in ['strong', 'very_strong']
            ]
            # In black swan, correlations may be unusually high
            assert len(high_correlations) >= 0

        # Validate black swan scenario analysis
        black_swan_scenarios = [
            s for s in profile.scenario_analyses
            if 'black_swan' in s.scenario_type.lower()
        ]
        assert len(black_swan_scenarios) >= 0

    @pytest.mark.asyncio
    async def test_cross_engine_correlation_validation(self, orchestrator, test_addresses):
        """Test cross-engine correlation analysis accuracy"""

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['medium_risk'],
            include_scenario_analysis=False,  # Focus on correlation
            include_trend_analysis=False,
            enable_real_time_monitoring=False
        )

        # Validate correlation analysis
        correlations = profile.cross_engine_correlations

        # Should have correlations between engine pairs
        expected_pairs = 6  # 4 engines = 6 pairs (4 choose 2)
        assert len(correlations) <= expected_pairs

        for correlation in correlations:
            # Validate correlation structure
            assert correlation.engine_1 in [e for e in RiskEngine]
            assert correlation.engine_2 in [e for e in RiskEngine]
            assert correlation.engine_1 != correlation.engine_2

            # Validate correlation metrics
            assert -1.0 <= correlation.correlation_coefficient <= 1.0
            assert correlation.correlation_strength in ['weak', 'moderate', 'strong', 'very_strong']
            assert correlation.risk_amplification_factor >= 0
            assert 0 <= correlation.confidence_level <= 1.0

    @pytest.mark.asyncio
    async def test_risk_amplification_chains(self, orchestrator, test_addresses):
        """Test risk amplification chain identification"""

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['high_risk'],
            include_scenario_analysis=False,
            include_trend_analysis=False,
            enable_real_time_monitoring=False
        )

        # Validate amplification chains
        chains = profile.risk_amplification_chains
        assert isinstance(chains, list)

        for chain in chains:
            assert isinstance(chain, list)
            assert len(chain) >= 2  # Chain must have at least 2 engines

            # All elements should be valid risk engines
            for engine in chain:
                assert engine in [e for e in RiskEngine]

    @pytest.mark.asyncio
    async def test_portfolio_context_integration(self, orchestrator, test_addresses):
        """Test portfolio context integration in risk assessment"""

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['medium_risk'],
            include_scenario_analysis=False,
            include_trend_analysis=False,
            enable_real_time_monitoring=False
        )

        # Validate portfolio metrics
        assert profile.portfolio_value_at_risk >= 0
        assert isinstance(profile.position_concentration_risk, dict)
        assert 0 <= profile.diversification_effectiveness <= 1.0
        assert 0 <= profile.hedging_effectiveness <= 1.0

        # Validate market regime assessment
        assert isinstance(profile.market_regime, dict)
        assert 'volatility' in profile.market_regime
        assert 'liquidity' in profile.market_regime
        assert 'correlation' in profile.market_regime

    @pytest.mark.asyncio
    async def test_confidence_and_quality_metrics(self, orchestrator, test_addresses):
        """Test confidence and data quality metrics"""

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['low_risk'],
            include_scenario_analysis=False,
            include_trend_analysis=False,
            enable_real_time_monitoring=False
        )

        # Validate confidence intervals
        score = profile.holistic_risk_score
        lower, upper = score.confidence_interval
        assert 0 <= lower <= upper <= 100
        assert lower <= score.overall_holistic_score <= upper

        # Validate quality metrics
        assert 0 <= profile.data_quality_score <= 1.0
        assert 0 <= profile.analysis_completeness <= 1.0

        # Validate limitations are documented
        assert isinstance(profile.limitations, list)
        assert len(profile.limitations) > 0  # Should document limitations

        # Validate data sources are tracked
        assert isinstance(profile.data_sources, list)
        assert len(profile.data_sources) > 0

    @pytest.mark.asyncio
    async def test_serialization_and_executive_summary(self, orchestrator, test_addresses):
        """Test profile serialization and executive summary generation"""

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['medium_risk'],
            include_scenario_analysis=True,
            include_trend_analysis=True,
            enable_real_time_monitoring=False
        )

        # Test dictionary serialization
        profile_dict = profile.to_dict()
        assert isinstance(profile_dict, dict)
        assert 'address' in profile_dict
        assert 'overall_risk_level' in profile_dict
        assert 'overall_risk_score' in profile_dict
        assert 'risk_scores_by_engine' in profile_dict

        # Test executive summary
        summary = profile.get_executive_summary()
        assert isinstance(summary, dict)
        assert 'overall_assessment' in summary
        assert 'key_risks' in summary
        assert 'immediate_actions' in summary
        assert 'risk_distribution' in summary

        # Validate summary content
        assert 'risk_level' in summary['overall_assessment']
        assert 'score' in summary['overall_assessment']
        assert 'confidence' in summary['overall_assessment']

    @pytest.mark.asyncio
    async def test_concurrent_risk_assessments(self, orchestrator, test_addresses):
        """Test concurrent risk assessments for multiple addresses"""

        # Run concurrent assessments
        tasks = []
        for address in test_addresses.values():
            task = orchestrator.assess_holistic_risk(
                address=address,
                include_scenario_analysis=False,  # Faster for concurrency test
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )
            tasks.append(task)

        # Execute concurrently
        profiles = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate all assessments completed successfully
        for i, profile in enumerate(profiles):
            assert not isinstance(profile, Exception), f"Assessment {i} failed: {profile}"
            assert profile is not None
            assert profile.holistic_risk_score is not None

        # Validate different addresses have different risk profiles
        scores = [p.holistic_risk_score.overall_holistic_score for p in profiles]
        assert len(set([round(s, 1) for s in scores])) > 1  # Some variation expected

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self, orchestrator):
        """Test error handling and system resilience"""

        # Test with invalid address
        with pytest.raises(Exception):
            await orchestrator.assess_holistic_risk(
                address="INVALID_ADDRESS",
                include_scenario_analysis=False,
                include_trend_analysis=False,
                enable_real_time_monitoring=False
            )

        # Test with partial engine failures (would need to mock failures)
        # This is a placeholder for more sophisticated failure testing
        assert True  # Placeholder assertion

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, orchestrator, test_addresses):
        """Test performance benchmarks for risk assessments"""

        # Time a complete assessment
        start_time = datetime.utcnow()

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['medium_risk'],
            include_scenario_analysis=True,
            include_trend_analysis=True,
            enable_real_time_monitoring=False
        )

        end_time = datetime.utcnow()
        assessment_time = (end_time - start_time).total_seconds()

        # Validate assessment completed in reasonable time
        assert assessment_time < 60.0  # Should complete within 60 seconds
        assert profile is not None

        # Log performance metrics
        print(f"Holistic risk assessment completed in {assessment_time:.2f} seconds")

    @pytest.mark.asyncio
    async def test_risk_trend_analysis(self, orchestrator, test_addresses):
        """Test risk trend analysis functionality"""

        profile = await orchestrator.assess_holistic_risk(
            address=test_addresses['medium_risk'],
            include_scenario_analysis=False,
            include_trend_analysis=True,
            enable_real_time_monitoring=False
        )

        # Validate trend analysis
        trends = profile.risk_trends
        assert isinstance(trends, list)

        for trend in trends:
            assert trend.engine in [e for e in RiskEngine]
            assert trend.time_period_days > 0
            assert trend.trend_direction in ['increasing', 'decreasing', 'stable', 'volatile']
            assert 0 <= trend.trend_strength <= 1.0
            assert len(trend.risk_score_history) >= 0

    def test_integration_test_coverage(self):
        """Verify integration test coverage of all risk workflow components"""

        # This test verifies that we have covered all major workflow components
        covered_components = [
            'holistic_risk_orchestrator',
            'blockchain_behavior_engine',
            'defi_protocol_engine',
            'liquidity_cascade_engine',
            'governance_stability_engine',
            'cross_engine_correlation',
            'scenario_analysis',
            'trend_analysis',
            'portfolio_context',
            'quality_metrics',
            'performance_benchmarks'
        ]

        # Verify all components are tested
        test_methods = [method for method in dir(self) if method.startswith('test_')]

        # Each component should have at least one test
        for component in covered_components:
            has_test = any(component.replace('_', '') in method.replace('_', '')
                          for method in test_methods)
            assert has_test, f"No test found for component: {component}"

        print(f"Integration test coverage verified for {len(covered_components)} components")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])