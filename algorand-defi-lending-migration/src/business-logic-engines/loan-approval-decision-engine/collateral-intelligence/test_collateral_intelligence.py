"""
Test suite for Collateral Intelligence Engine

Tests the comprehensive collateral intelligence functionality including
smart collateral analysis, liquidation prediction, and integrated intelligence.
"""

import asyncio
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import numpy as np

# Add the core module to the path
sys.path.append(str(Path(__file__).parent / "core"))

from core.intelligence_engine import CollateralIntelligenceEngine, CollateralIntelligenceReport
from core.smart_collateral import SmartCollateralAnalyzer, SmartCollateralAnalysis
from core.liquidation_predictor import LiquidationPredictor, LiquidationPredictionAnalysis

class TestCollateralIntelligenceEngine:
    """Test suite for the main collateral intelligence engine"""

    @pytest.fixture
    def intelligence_engine(self):
        """Create a collateral intelligence engine instance"""
        return CollateralIntelligenceEngine()

    @pytest.fixture
    def sample_collateral_portfolio(self):
        """Sample collateral portfolio for testing"""
        return {
            'address': 'ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456',
            'assets': {
                'ALGO': {
                    'amount': 10000,
                    'current_price': 0.25,
                    'market_cap': 2000000000,
                    'daily_volume': 50000000,
                    'volatility_30d': 0.45
                },
                'USDC': {
                    'amount': 5000,
                    'current_price': 1.00,
                    'market_cap': 50000000000,
                    'daily_volume': 5000000000,
                    'volatility_30d': 0.02
                },
                'goBTC': {
                    'amount': 0.1,
                    'current_price': 45000,
                    'market_cap': 800000000000,
                    'daily_volume': 20000000000,
                    'volatility_30d': 0.60
                }
            },
            'market_conditions': {
                'sentiment': 0.6,
                'volatility_index': 0.35,
                'market_trend': 'bullish'
            }
        }

    @pytest.fixture
    def sample_borrower_profile(self):
        """Sample borrower profile for testing"""
        return {
            'address': 'ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456',
            'overall_behavior_score': 0.75,
            'sophistication_score': 0.8,
            'risk_management_score': 0.7,
            'defi_experience_score': 0.65
        }

    @pytest.fixture
    def sample_loan_request(self):
        """Sample loan request for testing"""
        return {
            'amount': 5000,
            'currency': 'USDC',
            'duration_days': 30,
            'purpose': 'trading'
        }

    @pytest.mark.asyncio
    async def test_comprehensive_collateral_analysis(self, intelligence_engine, sample_collateral_portfolio):
        """Test comprehensive collateral intelligence analysis"""

        # Run analysis
        report = await intelligence_engine.analyze_collateral_portfolio(
            collateral_portfolio=sample_collateral_portfolio
        )

        # Verify report structure
        assert isinstance(report, CollateralIntelligenceReport)
        assert report.address == sample_collateral_portfolio['address']
        assert isinstance(report.analysis_timestamp, datetime)

        # Verify integrated scores
        assert 0 <= report.overall_collateral_score <= 1
        assert report.risk_adjusted_value >= 0
        assert report.liquidation_adjusted_value >= 0
        assert 0 <= report.recommended_loan_to_value <= 1

        # Verify decision components
        valid_recommendations = ['approve', 'conditional_approve', 'reject']
        assert report.approval_recommendation in valid_recommendations

        print(f"✅ Comprehensive analysis completed")
        print(f"   Total Collateral Value: ${report.smart_collateral_analysis.total_collateral_value:,.2f}")
        print(f"   Overall Score: {report.overall_collateral_score:.3f}")
        print(f"   Risk Adjusted Value: ${report.risk_adjusted_value:,.2f}")
        print(f"   Recommended LTV: {report.recommended_loan_to_value:.1%}")
        print(f"   Approval Recommendation: {report.approval_recommendation}")

    @pytest.mark.asyncio
    async def test_analysis_with_borrower_profile(self, intelligence_engine, sample_collateral_portfolio, sample_borrower_profile):
        """Test analysis with borrower behavioral profile"""

        report = await intelligence_engine.analyze_collateral_portfolio(
            collateral_portfolio=sample_collateral_portfolio,
            borrower_profile=sample_borrower_profile
        )

        # Verify borrower profile is considered
        assert report.recommended_loan_to_value > 0

        # With good borrower profile, LTV should be reasonable
        if sample_borrower_profile['overall_behavior_score'] > 0.7:
            assert report.recommended_loan_to_value >= 0.5

        print(f"✅ Analysis with borrower profile completed")
        print(f"   Borrower Score Impact: LTV = {report.recommended_loan_to_value:.1%}")

    @pytest.mark.asyncio
    async def test_analysis_with_loan_context(self, intelligence_engine, sample_collateral_portfolio, sample_loan_request):
        """Test analysis with loan request context"""

        report = await intelligence_engine.analyze_collateral_portfolio(
            collateral_portfolio=sample_collateral_portfolio,
            loan_request=sample_loan_request
        )

        # Verify loan context influences decision
        assert isinstance(report.required_conditions, list)
        assert isinstance(report.monitoring_requirements, list)

        print(f"✅ Analysis with loan context completed")
        print(f"   Required Conditions: {len(report.required_conditions)}")
        print(f"   Monitoring Requirements: {len(report.monitoring_requirements)}")

    @pytest.mark.asyncio
    async def test_integrated_risk_assessment(self, intelligence_engine, sample_collateral_portfolio):
        """Test integrated risk assessment"""

        report = await intelligence_engine.analyze_collateral_portfolio(
            collateral_portfolio=sample_collateral_portfolio
        )

        # Verify risk assessment components
        assert 0 <= report.integrated_risk_score <= 1
        assert 0 <= report.confidence_level <= 1

        # Verify liquidation analysis
        liquidation_analysis = report.liquidation_prediction_analysis
        assert 0 <= liquidation_analysis.portfolio_risk.overall_liquidation_probability <= 1

        print(f"✅ Integrated risk assessment completed")
        print(f"   Integrated Risk Score: {report.integrated_risk_score:.3f}")
        print(f"   Liquidation Probability: {liquidation_analysis.portfolio_risk.overall_liquidation_probability:.1%}")
        print(f"   Confidence Level: {report.confidence_level:.3f}")

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, intelligence_engine, sample_collateral_portfolio):
        """Test optimization recommendations generation"""

        report = await intelligence_engine.analyze_collateral_portfolio(
            collateral_portfolio=sample_collateral_portfolio
        )

        # Verify recommendations are provided
        assert isinstance(report.optimization_recommendations, list)
        assert isinstance(report.risk_mitigation_strategies, list)

        print(f"✅ Optimization recommendations generated")
        print(f"   Optimization Recommendations: {len(report.optimization_recommendations)}")
        print(f"   Risk Mitigation Strategies: {len(report.risk_mitigation_strategies)}")

        if report.optimization_recommendations:
            print(f"   Sample Recommendation: {report.optimization_recommendations[0]}")

    def test_report_export(self, intelligence_engine):
        """Test report export functionality"""

        # Create a minimal mock report for testing
        from core.smart_collateral import SmartCollateralAnalysis, CollateralAsset, CollateralQualityMetrics, RealTimeAnalysis
        from core.liquidation_predictor import LiquidationPredictionAnalysis, PortfolioLiquidationRisk

        mock_asset = CollateralAsset(
            asset_id="ALGO",
            symbol="ALGO",
            name="Algorand",
            current_price=0.25,
            market_cap=2000000000,
            daily_volume=50000000,
            volatility_30d=0.45,
            liquidity_tier="tier_1",
            quality_score=0.75,
            risk_score=0.35,
            correlation_btc=0.6,
            correlation_algo=1.0
        )

        mock_quality_metrics = CollateralQualityMetrics(
            liquidity_score=0.8,
            volatility_score=0.6,
            market_cap_score=0.9,
            governance_score=0.7,
            technical_score=0.7,
            correlation_score=0.5,
            regulatory_score=0.8,
            overall_quality_score=0.75
        )

        mock_real_time = RealTimeAnalysis(
            timestamp=datetime.now(),
            price_trend="neutral",
            volume_trend="stable",
            volatility_spike=False,
            liquidity_stress=False,
            correlation_warning=False,
            quality_change=0.0,
            alerts=[]
        )

        mock_smart_analysis = SmartCollateralAnalysis(
            address="test_address",
            analysis_timestamp=datetime.now(),
            total_collateral_value=10000,
            collateral_assets=[mock_asset],
            quality_metrics=mock_quality_metrics,
            real_time_analysis=mock_real_time,
            predictive_insights={},
            optimization_recommendations=["Test recommendation"],
            risk_warnings=[],
            confidence_level=0.8
        )

        mock_portfolio_risk = PortfolioLiquidationRisk(
            overall_liquidation_probability=0.2,
            worst_case_scenario_probability=0.3,
            expected_liquidation_value=500,
            time_to_liquidation_estimate=30,
            cascade_risk_probability=0.1,
            stress_test_results={}
        )

        mock_liquidation_analysis = LiquidationPredictionAnalysis(
            address="test_address",
            analysis_timestamp=datetime.now(),
            asset_predictions=[],
            portfolio_risk=mock_portfolio_risk,
            prediction_model_performance={},
            feature_importance={},
            risk_mitigation_strategies=[],
            early_warning_indicators=[],
            confidence_level=0.8
        )

        mock_report = CollateralIntelligenceReport(
            address="test_address",
            analysis_timestamp=datetime.now(),
            smart_collateral_analysis=mock_smart_analysis,
            liquidation_prediction_analysis=mock_liquidation_analysis,
            overall_collateral_score=0.75,
            risk_adjusted_value=9000,
            liquidation_adjusted_value=8500,
            recommended_loan_to_value=0.7,
            approval_recommendation="approve",
            required_conditions=[],
            monitoring_requirements=[],
            integrated_risk_score=0.3,
            confidence_level=0.8,
            optimization_recommendations=[],
            risk_mitigation_strategies=[]
        )

        # Test export
        exported = intelligence_engine.export_report(mock_report, 'json')
        assert isinstance(exported, str)

        # Verify it's valid JSON
        parsed = json.loads(exported)
        assert parsed['overall_collateral_score'] == 0.75

        print("✅ Report export functionality working")

class TestSmartCollateralAnalyzer:
    """Test suite for smart collateral analyzer"""

    @pytest.fixture
    def smart_analyzer(self):
        """Create a smart collateral analyzer instance"""
        return SmartCollateralAnalyzer()

    @pytest.mark.asyncio
    async def test_smart_collateral_analysis(self, smart_analyzer):
        """Test smart collateral analysis"""

        mock_portfolio = {
            'address': 'test_address',
            'assets': {
                'ALGO': {
                    'amount': 1000,
                    'current_price': 0.25,
                    'market_cap': 2000000000,
                    'daily_volume': 50000000
                }
            }
        }

        analysis = await smart_analyzer.analyze_smart_collateral(
            collateral_portfolio=mock_portfolio
        )

        # Verify analysis structure
        assert isinstance(analysis, SmartCollateralAnalysis)
        assert analysis.total_collateral_value >= 0
        assert 0 <= analysis.quality_metrics.overall_quality_score <= 1

        print("✅ Smart collateral analysis completed")

class TestLiquidationPredictor:
    """Test suite for liquidation predictor"""

    @pytest.fixture
    def liquidation_predictor(self):
        """Create a liquidation predictor instance"""
        return LiquidationPredictor()

    @pytest.mark.asyncio
    async def test_liquidation_prediction(self, liquidation_predictor):
        """Test liquidation risk prediction"""

        mock_assets = [
            {
                'symbol': 'ALGO',
                'current_price': 0.25,
                'market_cap': 2000000000,
                'daily_volume': 50000000,
                'volatility_30d': 0.45
            }
        ]

        analysis = await liquidation_predictor.predict_liquidation_risk(
            collateral_assets=mock_assets
        )

        # Verify analysis structure
        assert isinstance(analysis, LiquidationPredictionAnalysis)
        assert 0 <= analysis.portfolio_risk.overall_liquidation_probability <= 1

        print("✅ Liquidation prediction completed")

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 Starting Collateral Intelligence Engine Tests")
    print("=" * 60)

    # Create test instance
    engine = CollateralIntelligenceEngine()

    # Sample test data
    test_portfolio = {
        'address': 'ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456',
        'assets': {
            'ALGO': {
                'amount': 20000,
                'current_price': 0.25,
                'market_cap': 2000000000,
                'daily_volume': 50000000,
                'volatility_30d': 0.45
            },
            'USDC': {
                'amount': 10000,
                'current_price': 1.00,
                'market_cap': 50000000000,
                'daily_volume': 5000000000,
                'volatility_30d': 0.02
            },
            'goBTC': {
                'amount': 0.2,
                'current_price': 45000,
                'market_cap': 800000000000,
                'daily_volume': 20000000000,
                'volatility_30d': 0.60
            }
        },
        'market_conditions': {
            'sentiment': 0.6,
            'volatility_index': 0.35
        }
    }

    test_borrower = {
        'address': test_portfolio['address'],
        'overall_behavior_score': 0.75,
        'sophistication_score': 0.8,
        'risk_management_score': 0.7
    }

    test_loan = {
        'amount': 8000,
        'currency': 'USDC',
        'duration_days': 60
    }

    async def run_full_test():
        try:
            # Test comprehensive analysis
            print("\n🔍 Running comprehensive collateral intelligence analysis...")
            report = await engine.analyze_collateral_portfolio(
                collateral_portfolio=test_portfolio,
                borrower_profile=test_borrower,
                loan_request=test_loan
            )

            print(f"\n📊 Collateral Intelligence Report:")
            print(f"   Address: {report.address}")
            print(f"   Total Collateral Value: ${report.smart_collateral_analysis.total_collateral_value:,.2f}")
            print(f"   Overall Collateral Score: {report.overall_collateral_score:.3f}")
            print(f"   Risk Adjusted Value: ${report.risk_adjusted_value:,.2f}")
            print(f"   Liquidation Adjusted Value: ${report.liquidation_adjusted_value:,.2f}")
            print(f"   Recommended LTV: {report.recommended_loan_to_value:.1%}")
            print(f"   Integrated Risk Score: {report.integrated_risk_score:.3f}")
            print(f"   Confidence Level: {report.confidence_level:.3f}")

            print(f"\n🎯 Decision Support:")
            print(f"   Approval Recommendation: {report.approval_recommendation}")
            print(f"   Required Conditions: {len(report.required_conditions)}")
            print(f"   Monitoring Requirements: {len(report.monitoring_requirements)}")

            print(f"\n💡 Smart Collateral Analysis:")
            print(f"   Quality Score: {report.smart_collateral_analysis.quality_metrics.overall_quality_score:.3f}")
            print(f"   Liquidity Score: {report.smart_collateral_analysis.quality_metrics.liquidity_score:.3f}")
            print(f"   Volatility Score: {report.smart_collateral_analysis.quality_metrics.volatility_score:.3f}")
            print(f"   Assets Analyzed: {len(report.smart_collateral_analysis.collateral_assets)}")

            print(f"\n⚠️  Liquidation Risk Analysis:")
            liquidation_risk = report.liquidation_prediction_analysis.portfolio_risk
            print(f"   Overall Liquidation Probability: {liquidation_risk.overall_liquidation_probability:.1%}")
            print(f"   Worst Case Scenario: {liquidation_risk.worst_case_scenario_probability:.1%}")
            print(f"   Expected Liquidation Value: ${liquidation_risk.expected_liquidation_value:,.2f}")
            print(f"   Cascade Risk Probability: {liquidation_risk.cascade_risk_probability:.1%}")

            if report.optimization_recommendations:
                print(f"\n🔧 Optimization Recommendations ({len(report.optimization_recommendations)}):")
                for i, rec in enumerate(report.optimization_recommendations[:3], 1):
                    print(f"   {i}. {rec}")

            if report.risk_mitigation_strategies:
                print(f"\n🛡️  Risk Mitigation Strategies ({len(report.risk_mitigation_strategies)}):")
                for i, strategy in enumerate(report.risk_mitigation_strategies[:3], 1):
                    print(f"   {i}. {strategy}")

            # Test historical performance
            print(f"\n📈 Testing historical performance retrieval...")
            historical = await engine.get_historical_performance(test_portfolio['address'])
            if historical:
                print(f"   Prediction Accuracy: {historical.get('prediction_accuracy', 0):.1%}")
                print(f"   Total Predictions: {historical.get('total_predictions', 0)}")

            # Test export functionality
            print(f"\n📄 Testing export functionality...")
            exported = engine.export_report(report, 'json')
            print(f"   Export size: {len(exported):,} characters")

            print("\n✅ All tests completed successfully!")
            print("🎉 Collateral Intelligence Engine is ready for production!")

        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

    # Run the async test
    asyncio.run(run_full_test())

if __name__ == "__main__":
    run_comprehensive_test()