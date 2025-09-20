#!/usr/bin/env python3
"""
Simple demo script to verify governance reputation and network risk monitoring engines
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def demo_governance_reputation():
    """Demo the governance reputation engine"""
    print("🏛️ Governance Reputation Engine Demo")
    print("=" * 50)

    try:
        # Import reputation engine
        sys.path.append(str(Path(__file__).parent / "governance-reputation"))
        from core.reputation_engine import ReputationEngine

        # Initialize engine
        reputation_engine = ReputationEngine()

        # Test address
        test_address = "ALGORAND_TEST_ADDRESS_123456789"

        print(f"📊 Analyzing reputation for: {test_address}")

        # Perform analysis
        reputation_analysis = await reputation_engine.analyze_comprehensive_reputation(test_address)

        # Display results
        print(f"✅ Overall Reputation Score: {reputation_analysis.overall_reputation_score:.1f}")
        print(f"🏆 Reputation Tier: {reputation_analysis.reputation_tier.value.upper()}")
        print(f"📈 Component Scores:")
        print(f"  • Governance: {reputation_analysis.governance_score:.1f}")
        print(f"  • Community: {reputation_analysis.community_engagement_score:.1f}")
        print(f"  • Consensus: {reputation_analysis.consensus_participation_score:.1f}")
        print(f"  • Commitment: {reputation_analysis.ecosystem_commitment_score:.1f}")

        print(f"🎯 Loan Impact:")
        impact = reputation_analysis.loan_decision_impact
        print(f"  • LTV Adjustment: {impact.ltv_adjustment:+.1%}")
        print(f"  • Rate Adjustment: {impact.rate_adjustment:+.3f}%")
        print(f"  • Auto Reject: {'Yes' if impact.auto_reject else 'No'}")

        print("✅ Governance reputation engine working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error in governance reputation demo: {e}")
        return False

async def demo_network_risk():
    """Demo the network risk monitoring engine"""
    print("\n🌐 Network Risk Monitoring Engine Demo")
    print("=" * 50)

    try:
        # Import risk engine
        sys.path.append(str(Path(__file__).parent / "network-risk-monitoring"))
        from core.risk_engine import NetworkRiskEngine

        # Initialize engine
        risk_engine = NetworkRiskEngine()

        print("📊 Performing comprehensive risk assessment...")

        # Perform assessment
        risk_assessment = await risk_engine.assess_comprehensive_risk()

        # Display results
        print(f"✅ Overall Risk Score: {risk_assessment.overall_risk_score:.1f}")
        print(f"🚨 Risk Level: {risk_assessment.risk_level.value.upper()}")
        print(f"📈 Component Scores:")
        for component, score in list(risk_assessment.component_scores.items())[:4]:
            print(f"  • {component.replace('_', ' ').title()}: {score:.1f}")

        print(f"⚙️ Risk Adjustments:")
        adj = risk_assessment.risk_adjustments
        print(f"  • LTV Adjustment: {adj.ltv_adjustment:+.1%}")
        print(f"  • Rate Adjustment: {adj.interest_rate_adjustment:+.3f}%")
        print(f"  • Manual Review: {'Yes' if adj.manual_review_required else 'No'}")

        print("✅ Network risk monitoring engine working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error in network risk demo: {e}")
        return False

async def main():
    """Main demo function"""
    print("🚀 Algorand Governance & Risk Engines Demo")
    print("=" * 60)

    # Test both engines
    governance_success = await demo_governance_reputation()
    risk_success = await demo_network_risk()

    print("\n" + "=" * 60)
    if governance_success and risk_success:
        print("🎉 All engines working successfully!")
        print("✅ Ready for holistic loan approval decisions")
    else:
        print("⚠️ Some engines encountered issues")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())