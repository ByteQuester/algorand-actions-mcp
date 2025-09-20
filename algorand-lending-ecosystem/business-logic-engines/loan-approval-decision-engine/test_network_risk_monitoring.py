"""
Test script for Network Risk Monitoring Engine

Tests comprehensive network risk assessment and real-time monitoring functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from network_risk_monitoring.core.risk_engine import NetworkRiskEngine


async def test_network_risk_engine():
    """Test the network risk monitoring engine"""
    print("🚀 Testing Network Risk Monitoring Engine")
    print("=" * 60)

    # Initialize the risk engine
    risk_engine = NetworkRiskEngine()

    try:
        print("📊 Performing comprehensive network risk assessment...")
        print("-" * 60)

        # Perform comprehensive risk assessment
        risk_assessment = await risk_engine.assess_comprehensive_risk()

        # Display results
        print(f"✅ Overall Risk Score: {risk_assessment.overall_risk_score:.1f}")
        print(f"🚨 Risk Level: {risk_assessment.risk_level.value.upper()}")
        print()

        print("📈 Component Risk Scores:")
        for component, score in risk_assessment.component_scores.items():
            risk_emoji = "🔴" if score > 70 else "🟡" if score > 40 else "🟢"
            print(f"  • {component.replace('_', ' ').title()}: {score:.1f} {risk_emoji}")
        print()

        print("⚙️ Risk Adjustments for Loan Decisions:")
        adj = risk_assessment.risk_adjustments
        print(f"  • LTV Adjustment: {adj.ltv_adjustment:+.1%}")
        print(f"  • Interest Rate Adjustment: {adj.interest_rate_adjustment:+.3f}%")
        print(f"  • Approval Threshold Adjustment: {adj.approval_threshold_adjustment:+.1%}")
        print(f"  • Manual Review Required: {'Yes' if adj.manual_review_required else 'No'}")
        print(f"  • Additional Collateral Required: {adj.additional_collateral_required:.1%}")
        print()

        print("🚨 Active Alerts:")
        if risk_assessment.active_alerts:
            for alert in risk_assessment.active_alerts[:3]:  # Show top 3
                severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "emergency": "🆘"}.get(alert.severity.value, "❓")
                print(f"  • {severity_emoji} {alert.title}")
                print(f"    {alert.message}")
        else:
            print("  • No active alerts 🟢")
        print()

        print("⚠️ Risk Factors:")
        for risk in risk_assessment.risk_factors[:5]:  # Show top 5
            print(f"  • {risk}")
        print()

        print("📊 Risk Trends:")
        for component, trend in risk_assessment.risk_trends.items():
            trend_arrow = "📈" if trend > 0.02 else "📉" if trend < -0.02 else "➡️"
            print(f"  • {component.replace('_', ' ').title()}: {trend:+.1%} {trend_arrow}")
        print()

        print("💡 Recommendations:")
        for rec in risk_assessment.recommendations[:3]:  # Show top 3
            print(f"  • {rec}")
        print()

        print(f"🎯 Confidence Score: {risk_assessment.confidence_score:.1%}")
        print(f"⏰ Assessment Timestamp: {risk_assessment.assessment_timestamp}")
        print(f"⏱️ Next Assessment: {risk_assessment.next_assessment_time}")

        print("\n✅ Network Risk Monitoring Engine test completed successfully!")

        return risk_assessment

    except Exception as e:
        print(f"❌ Error testing network risk engine: {e}")
        raise


async def test_individual_risk_components():
    """Test individual risk monitoring components"""
    print("\n🔧 Testing Individual Risk Components")
    print("=" * 60)

    risk_engine = NetworkRiskEngine()

    try:
        print("1️⃣ Testing Ecosystem Health Monitor...")
        async with risk_engine.ecosystem_monitor:
            health_report = await risk_engine.ecosystem_monitor.assess_ecosystem_health()
            print(f"   Health Score: {health_report.overall_health_score:.1f}")
            print(f"   Health Status: {health_report.health_status.value}")
            print(f"   Total TVL: ${health_report.ecosystem_metrics.total_tvl_usd:,.0f}")
            print(f"   Active Protocols: {health_report.ecosystem_metrics.total_active_protocols}")

        print("\n2️⃣ Testing Protocol Risk Analyzer...")
        protocol_report = await risk_engine.protocol_analyzer.assess_protocol_risks()
        print(f"   Overall Protocol Risk: {protocol_report.overall_risk_score:.1f}")
        print(f"   Protocol Risks: {len(protocol_report.protocol_risks)} protocols analyzed")

        print("\n3️⃣ Testing Market Condition Analyzer...")
        market_report = await risk_engine.market_analyzer.analyze_market_conditions()
        print(f"   Market Risk Score: {market_report.overall_risk_score:.1f}")
        print(f"   Market Condition: {market_report.market_condition}")
        print(f"   Volatility Score: {market_report.volatility_score:.1f}")

        print("\n4️⃣ Testing Congestion Monitor...")
        congestion_report = await risk_engine.congestion_monitor.monitor_network_congestion()
        print(f"   Congestion Risk: {congestion_report.congestion_risk_score:.1f}")
        print(f"   Current TPS: {congestion_report.current_tps:.1f}")
        print(f"   Confirmation Time: {congestion_report.average_confirmation_time:.1f}s")

        print("\n5️⃣ Testing Correlation Analyzer...")
        correlation_report = await risk_engine.correlation_analyzer.analyze_correlations()
        print(f"   Correlation Risk: {correlation_report.overall_correlation_risk:.1f}")
        print(f"   Systemic Correlation: {correlation_report.systemic_correlation:.2f}")

        print("\n6️⃣ Testing Systemic Risk Assessor...")
        systemic_report = await risk_engine.systemic_assessor.assess_systemic_risks()
        print(f"   Systemic Risk: {systemic_report.overall_systemic_risk:.1f}")
        print(f"   Early Warning Level: {systemic_report.early_warning_level}")

        print("\n✅ All individual risk components tested successfully!")

    except Exception as e:
        print(f"❌ Error testing individual risk components: {e}")
        raise


async def test_risk_adjustments():
    """Test dynamic risk adjustments for different risk levels"""
    print("\n🎛️ Testing Dynamic Risk Adjustments")
    print("=" * 60)

    risk_engine = NetworkRiskEngine()

    try:
        # Get current risk level and adjustments
        current_risk_level = await risk_engine.get_current_risk_level()
        risk_adjustments = await risk_engine.get_risk_adjustments()

        print(f"📊 Current Risk Level: {current_risk_level.value.upper()}")
        print("\n⚙️ Dynamic Adjustments Applied:")
        print(f"  • LTV Adjustment: {risk_adjustments.ltv_adjustment:+.1%}")
        print(f"  • Interest Rate Adjustment: {risk_adjustments.interest_rate_adjustment:+.3f}%")
        print(f"  • Approval Threshold Adjustment: {risk_adjustments.approval_threshold_adjustment:+.1%}")
        print(f"  • Manual Review Required: {'Yes' if risk_adjustments.manual_review_required else 'No'}")
        print(f"  • Additional Collateral: {risk_adjustments.additional_collateral_required:.1%}")

        # Simulate loan decision impact
        print("\n💰 Example Loan Impact:")
        base_ltv = 0.75
        base_rate = 0.08
        adjusted_ltv = base_ltv + risk_adjustments.ltv_adjustment
        adjusted_rate = base_rate + risk_adjustments.interest_rate_adjustment

        print(f"  • Base LTV: {base_ltv:.1%} → Adjusted LTV: {adjusted_ltv:.1%}")
        print(f"  • Base Rate: {base_rate:.2%} → Adjusted Rate: {adjusted_rate:.2%}")

        print("\n✅ Risk adjustment testing completed successfully!")

    except Exception as e:
        print(f"❌ Error testing risk adjustments: {e}")
        raise


if __name__ == "__main__":
    async def main():
        print("🌐 Algorand Network Risk Monitoring Engine Test Suite")
        print("=" * 80)

        # Test main engine
        risk_assessment = await test_network_risk_engine()

        # Test individual components
        await test_individual_risk_components()

        # Test risk adjustments
        await test_risk_adjustments()

        print("\n🎉 All tests completed successfully!")
        print("=" * 80)

    # Run the async main function
    asyncio.run(main())