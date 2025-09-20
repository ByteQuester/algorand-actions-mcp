"""
Test suite for DeFi Behavior Assessment Engine

Tests the comprehensive DeFi behavior analysis functionality including
protocol analysis, behavior patterns, and liquidity behavior assessment.
"""

import asyncio
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add the core module to the path
sys.path.append(str(Path(__file__).parent / "core"))

from core.behavior_engine import BehaviorEngine, BehavioralRiskAssessment
from core.protocol_analyzer import ProtocolAnalyzer, CrossProtocolAnalysis, ProtocolActivity
from core.behavior_patterns import BehaviorPatternAnalyzer, BehaviorPatternAnalysis
from core.liquidity_behavior import LiquidityBehaviorAnalyzer, LiquidityBehaviorAnalysis

class TestBehaviorEngine:
    """Test suite for the main behavior engine"""

    @pytest.fixture
    def behavior_engine(self):
        """Create a behavior engine instance"""
        return BehaviorEngine()

    @pytest.fixture
    def sample_address(self):
        """Sample Algorand address for testing"""
        return "ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456"

    @pytest.fixture
    def sample_loan_request(self):
        """Sample loan request for testing"""
        return {
            'amount': 50000,
            'currency': 'USDC',
            'duration_days': 90,
            'purpose': 'yield_farming'
        }

    @pytest.mark.asyncio
    async def test_basic_behavioral_assessment(self, behavior_engine, sample_address):
        """Test basic behavioral risk assessment"""

        # Run assessment
        assessment = await behavior_engine.assess_behavioral_risk(
            address=sample_address,
            analysis_period_days=180
        )

        # Verify assessment structure
        assert isinstance(assessment, BehavioralRiskAssessment)
        assert assessment.address == sample_address
        assert isinstance(assessment.analysis_timestamp, datetime)

        # Verify scores are in valid range
        assert 0 <= assessment.overall_behavior_score <= 1
        assert 0 <= assessment.sophistication_score <= 1
        assert 0 <= assessment.risk_management_score <= 1
        assert 0 <= assessment.defi_experience_score <= 1

        # Verify risk level is valid
        valid_risk_levels = ['low', 'medium', 'high', 'very_high']
        assert assessment.behavioral_risk_level in valid_risk_levels

        # Verify recommendation is valid
        valid_recommendations = ['approve', 'conditional', 'monitor', 'reject']
        assert assessment.loan_recommendation in valid_recommendations

        print(f"✅ Basic assessment completed for {sample_address}")
        print(f"   Overall Score: {assessment.overall_behavior_score}")
        print(f"   Risk Level: {assessment.behavioral_risk_level}")
        print(f"   Recommendation: {assessment.loan_recommendation}")

    @pytest.mark.asyncio
    async def test_assessment_with_loan_request(self, behavior_engine, sample_address, sample_loan_request):
        """Test assessment with loan request context"""

        assessment = await behavior_engine.assess_behavioral_risk(
            address=sample_address,
            analysis_period_days=365,
            loan_request=sample_loan_request
        )

        # Verify loan-specific factors are considered
        assert assessment.interest_rate_adjustment is not None
        assert isinstance(assessment.interest_rate_adjustment, (int, float))

        # Interest rate adjustment should be reasonable (-50 to +200 bps)
        assert -50 <= assessment.interest_rate_adjustment <= 200

        print(f"✅ Assessment with loan request completed")
        print(f"   Interest Rate Adjustment: {assessment.interest_rate_adjustment} bps")

    @pytest.mark.asyncio
    async def test_behavioral_insights_extraction(self, behavior_engine, sample_address):
        """Test extraction of behavioral insights"""

        assessment = await behavior_engine.assess_behavioral_risk(
            address=sample_address,
            analysis_period_days=365
        )

        # Verify insights are extracted
        assert isinstance(assessment.strengths, list)
        assert isinstance(assessment.weaknesses, list)
        assert isinstance(assessment.red_flags, list)
        assert isinstance(assessment.growth_indicators, list)

        # Verify recommendations are provided
        assert isinstance(assessment.risk_mitigation_recommendations, list)
        assert isinstance(assessment.monitoring_requirements, list)

        print(f"✅ Behavioral insights extracted")
        print(f"   Strengths: {len(assessment.strengths)}")
        print(f"   Weaknesses: {len(assessment.weaknesses)}")
        print(f"   Red Flags: {len(assessment.red_flags)}")

    @pytest.mark.asyncio
    async def test_confidence_metrics(self, behavior_engine, sample_address):
        """Test confidence and data quality metrics"""

        assessment = await behavior_engine.assess_behavioral_risk(
            address=sample_address,
            analysis_period_days=90
        )

        # Verify confidence metrics
        assert 0 <= assessment.analysis_confidence <= 1
        assert 0 <= assessment.data_quality_score <= 1

        print(f"✅ Confidence metrics calculated")
        print(f"   Analysis Confidence: {assessment.analysis_confidence}")
        print(f"   Data Quality Score: {assessment.data_quality_score}")

    def test_assessment_export(self, behavior_engine):
        """Test assessment export functionality"""

        # Create a mock assessment
        mock_assessment = BehavioralRiskAssessment(
            address="test_address",
            analysis_timestamp=datetime.now(),
            protocol_analysis=None,
            behavior_pattern_analysis=None,
            liquidity_behavior_analysis=None,
            overall_behavior_score=0.75,
            sophistication_score=0.8,
            risk_management_score=0.7,
            defi_experience_score=0.6,
            behavioral_risk_level="medium",
            loan_recommendation="approve",
            interest_rate_adjustment=0,
            strengths=["Strong risk management"],
            weaknesses=["Limited diversification"],
            red_flags=[],
            growth_indicators=["Improving strategies"],
            risk_mitigation_recommendations=["Monitor volatility"],
            monitoring_requirements=["Monthly review"],
            analysis_confidence=0.8,
            data_quality_score=0.75
        )

        # Test JSON export
        json_export = behavior_engine.export_assessment(mock_assessment, 'json')
        assert isinstance(json_export, str)

        # Verify it's valid JSON
        parsed = json.loads(json_export)
        assert parsed['overall_behavior_score'] == 0.75

        print("✅ Assessment export functionality working")

class TestProtocolAnalyzer:
    """Test suite for protocol analyzer"""

    @pytest.fixture
    def protocol_analyzer(self):
        """Create a protocol analyzer instance"""
        return ProtocolAnalyzer()

    @pytest.fixture
    def sample_address(self):
        """Sample address for testing"""
        return "ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456"

    @pytest.mark.asyncio
    async def test_cross_protocol_analysis(self, protocol_analyzer, sample_address):
        """Test cross-protocol activity analysis"""

        analysis = await protocol_analyzer.analyze_cross_protocol_activity(
            address=sample_address,
            analysis_period_days=365
        )

        # Verify analysis structure
        assert isinstance(analysis, CrossProtocolAnalysis)
        assert analysis.address == sample_address
        assert isinstance(analysis.analysis_timestamp, datetime)

        # Verify scores
        assert 0 <= analysis.diversification_score <= 1
        assert 0 <= analysis.sophistication_score <= 1

        # Verify protocol activities
        assert isinstance(analysis.protocol_activities, dict)
        assert isinstance(analysis.loyalty_scores, dict)
        assert isinstance(analysis.cross_protocol_strategies, list)

        print(f"✅ Cross-protocol analysis completed")
        print(f"   Protocols analyzed: {len(analysis.protocol_activities)}")
        print(f"   Diversification score: {analysis.diversification_score}")
        print(f"   Sophistication score: {analysis.sophistication_score}")

class TestBehaviorPatternAnalyzer:
    """Test suite for behavior pattern analyzer"""

    @pytest.fixture
    def pattern_analyzer(self):
        """Create a behavior pattern analyzer instance"""
        return BehaviorPatternAnalyzer()

    @pytest.mark.asyncio
    async def test_behavior_pattern_analysis(self, pattern_analyzer):
        """Test behavior pattern analysis"""

        # Mock protocol activities
        mock_protocol_activities = {
            'address': 'test_address',
            'algofi': type('MockActivity', (), {
                'protocol_specific_metrics': {'transactions': []},
                'total_transactions': 10,
                'activity_frequency': 1.0
            })()
        }

        mock_market_data = {
            'sentiment': 0.5,
            'volatility_index': 0.3
        }

        analysis = await pattern_analyzer.analyze_behavior_patterns(
            protocol_activities=mock_protocol_activities,
            market_data=mock_market_data,
            historical_period_days=365
        )

        # Verify analysis structure
        assert isinstance(analysis, BehaviorPatternAnalysis)
        assert hasattr(analysis, 'behavior_metrics')
        assert hasattr(analysis, 'market_cycle_behavior')

        print("✅ Behavior pattern analysis completed")

class TestLiquidityBehaviorAnalyzer:
    """Test suite for liquidity behavior analyzer"""

    @pytest.fixture
    def liquidity_analyzer(self):
        """Create a liquidity behavior analyzer instance"""
        return LiquidityBehaviorAnalyzer()

    @pytest.mark.asyncio
    async def test_liquidity_behavior_analysis(self, liquidity_analyzer):
        """Test liquidity behavior analysis"""

        # Mock protocol activities
        mock_protocol_activities = {
            'address': 'test_address',
            'tinyman': type('MockActivity', (), {
                'protocol_specific_metrics': {'transactions': []},
                'total_transactions': 5,
                'activity_frequency': 0.5
            })()
        }

        mock_market_data = {
            'price_data': {},
            'volume_data': {}
        }

        analysis = await liquidity_analyzer.analyze_liquidity_behavior(
            protocol_activities=mock_protocol_activities,
            market_data=mock_market_data,
            analysis_period_days=365
        )

        # Verify analysis structure
        assert isinstance(analysis, LiquidityBehaviorAnalysis)
        assert hasattr(analysis, 'liquidity_sophistication_score')
        assert hasattr(analysis, 'risk_management_score')

        print("✅ Liquidity behavior analysis completed")

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 Starting DeFi Behavior Assessment Engine Tests")
    print("=" * 60)

    # Create test instance
    engine = BehaviorEngine()
    test_address = "ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456"

    async def run_full_test():
        try:
            # Test full assessment
            print("\n📊 Running comprehensive behavioral assessment...")
            assessment = await engine.assess_behavioral_risk(
                address=test_address,
                analysis_period_days=365
            )

            print(f"\n📈 Assessment Results for {test_address}:")
            print(f"   Overall Behavior Score: {assessment.overall_behavior_score:.3f}")
            print(f"   Sophistication Score: {assessment.sophistication_score:.3f}")
            print(f"   Risk Management Score: {assessment.risk_management_score:.3f}")
            print(f"   DeFi Experience Score: {assessment.defi_experience_score:.3f}")
            print(f"   Behavioral Risk Level: {assessment.behavioral_risk_level}")
            print(f"   Loan Recommendation: {assessment.loan_recommendation}")
            print(f"   Interest Rate Adjustment: {assessment.interest_rate_adjustment} bps")
            print(f"   Analysis Confidence: {assessment.analysis_confidence:.3f}")
            print(f"   Data Quality Score: {assessment.data_quality_score:.3f}")

            if assessment.strengths:
                print(f"\n💪 Behavioral Strengths ({len(assessment.strengths)}):")
                for strength in assessment.strengths[:3]:  # Show first 3
                    print(f"   • {strength}")

            if assessment.red_flags:
                print(f"\n⚠️  Red Flags ({len(assessment.red_flags)}):")
                for flag in assessment.red_flags[:3]:  # Show first 3
                    print(f"   • {flag}")

            if assessment.risk_mitigation_recommendations:
                print(f"\n🛡️  Risk Mitigation Recommendations ({len(assessment.risk_mitigation_recommendations)}):")
                for rec in assessment.risk_mitigation_recommendations[:3]:  # Show first 3
                    print(f"   • {rec}")

            # Test export functionality
            print("\n📄 Testing export functionality...")
            exported = engine.export_assessment(assessment, 'json')
            print(f"   Export size: {len(exported)} characters")

            print("\n✅ All tests completed successfully!")
            print("🎉 DeFi Behavior Assessment Engine is ready for production!")

        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

    # Run the async test
    asyncio.run(run_full_test())

if __name__ == "__main__":
    run_comprehensive_test()