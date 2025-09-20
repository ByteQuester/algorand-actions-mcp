"""
Test script for Governance Reputation Engine

Tests comprehensive governance and reputation analysis functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from governance_reputation.core.reputation_engine import ReputationEngine


async def test_governance_reputation_engine():
    """Test the governance reputation engine"""
    print("🚀 Testing Governance Reputation Engine")
    print("=" * 60)

    # Initialize the reputation engine
    reputation_engine = ReputationEngine()

    # Test address (mock Algorand address)
    test_address = "ALGORANDTESTADDRESS123456789ABCDEFGHIJKLMNOP"

    try:
        print(f"📊 Analyzing comprehensive reputation for: {test_address}")
        print("-" * 60)

        # Perform comprehensive reputation analysis
        reputation_analysis = await reputation_engine.analyze_comprehensive_reputation(test_address)

        # Display results
        print(f"✅ Overall Reputation Score: {reputation_analysis.overall_reputation_score:.1f}")
        print(f"🏆 Reputation Tier: {reputation_analysis.reputation_tier.value.upper()}")
        print()

        print("📈 Component Scores:")
        print(f"  • Governance Participation: {reputation_analysis.governance_score:.1f}")
        print(f"  • Community Engagement: {reputation_analysis.community_engagement_score:.1f}")
        print(f"  • Consensus Participation: {reputation_analysis.consensus_participation_score:.1f}")
        print(f"  • Ecosystem Commitment: {reputation_analysis.ecosystem_commitment_score:.1f}")
        print()

        print("💡 Applied Bonuses:")
        for bonus in reputation_analysis.applied_bonuses:
            if bonus.applicable:
                print(f"  • {bonus.bonus_type}: {bonus.multiplier:.2f}x - {bonus.description}")
        print()

        print("🔍 Positive Indicators:")
        for indicator in reputation_analysis.positive_indicators[:5]:  # Show top 5
            print(f"  • {indicator}")
        print()

        print("⚠️ Risk Factors:")
        for risk in reputation_analysis.reputation_risks[:3]:  # Show top 3
            print(f"  • {risk}")
        print()

        print("🎯 Loan Decision Impact:")
        impact = reputation_analysis.loan_decision_impact
        print(f"  • LTV Adjustment: {impact.ltv_adjustment:+.1%}")
        print(f"  • Rate Adjustment: {impact.rate_adjustment:+.3f}%")
        print(f"  • Approval Bias: {impact.approval_bias:+.1%}")
        print(f"  • Manual Review Required: {'Yes' if impact.manual_review_required else 'No'}")
        print(f"  • Auto Reject: {'Yes' if impact.auto_reject else 'No'}")
        print()

        print("📋 Improvement Recommendations:")
        for rec in reputation_analysis.improvement_recommendations[:3]:  # Show top 3
            print(f"  • {rec}")
        print()

        print("📊 Reputation Trends:")
        for trend, value in reputation_analysis.reputation_trends.items():
            trend_arrow = "📈" if value > 0.02 else "📉" if value < -0.02 else "➡️"
            print(f"  • {trend}: {value:+.1%} {trend_arrow}")
        print()

        print(f"🎯 Confidence Score: {reputation_analysis.confidence_score:.1%}")
        print(f"⏰ Analysis Timestamp: {reputation_analysis.analysis_timestamp}")

        print("\n✅ Governance Reputation Engine test completed successfully!")

        return reputation_analysis

    except Exception as e:
        print(f"❌ Error testing governance reputation engine: {e}")
        raise


async def test_individual_components():
    """Test individual reputation components"""
    print("\n🔧 Testing Individual Components")
    print("=" * 60)

    reputation_engine = ReputationEngine()
    test_address = "ALGORANDTESTADDRESS123456789ABCDEFGHIJKLMNOP"

    try:
        print("1️⃣ Testing Governance Analyzer...")
        governance_analysis = await reputation_engine.governance_analyzer.analyze_governance_participation(test_address)
        print(f"   Governance Score: {governance_analysis.overall_score:.1f}")
        print(f"   Governance Periods: {governance_analysis.governance_periods}")
        print(f"   Achievements: {len(governance_analysis.governance_achievements)}")

        print("\n2️⃣ Testing Voting Pattern Analyzer...")
        voting_patterns = await reputation_engine.voting_analyzer.analyze_voting_patterns(test_address)
        print(f"   Voting Consistency: {voting_patterns.consistency_score:.1f}")
        print(f"   Total Votes: {voting_patterns.total_votes}")
        print(f"   Participation Rate: {voting_patterns.participation_rate:.1%}")

        print("\n3️⃣ Testing Community Engagement Analyzer...")
        community_profile = await reputation_engine.community_analyzer.analyze_community_engagement(test_address)
        print(f"   Overall Engagement: {community_profile.overall_engagement_score:.1f}")
        print(f"   Total Activities: {community_profile.total_activities}")
        print(f"   Leadership Indicators: {len(community_profile.leadership_indicators)}")

        print("\n4️⃣ Testing Consensus Participation Analyzer...")
        async with reputation_engine.consensus_analyzer:
            consensus_profile = await reputation_engine.consensus_analyzer.analyze_consensus_participation(test_address)
            print(f"   Consensus Score: {consensus_profile.overall_consensus_score:.1f}")
            print(f"   Total Nodes: {consensus_profile.total_nodes_operated}")
            print(f"   Average Uptime: {consensus_profile.average_uptime:.1f}%")

        print("\n5️⃣ Testing Ecosystem Commitment Analyzer...")
        commitment_profile = await reputation_engine.commitment_analyzer.analyze_ecosystem_commitment(test_address)
        print(f"   Commitment Score: {commitment_profile.overall_commitment_score:.1f}")
        print(f"   Portfolio Value: ${commitment_profile.total_portfolio_value:,.0f}")
        print(f"   ALGO Percentage: {commitment_profile.algo_holding_percentage:.1%}")

        print("\n✅ All individual components tested successfully!")

    except Exception as e:
        print(f"❌ Error testing individual components: {e}")
        raise


if __name__ == "__main__":
    async def main():
        print("🏛️ Algorand Governance Reputation Engine Test Suite")
        print("=" * 80)

        # Test main engine
        reputation_analysis = await test_governance_reputation_engine()

        # Test individual components
        await test_individual_components()

        print("\n🎉 All tests completed successfully!")
        print("=" * 80)

    # Run the async main function
    asyncio.run(main())