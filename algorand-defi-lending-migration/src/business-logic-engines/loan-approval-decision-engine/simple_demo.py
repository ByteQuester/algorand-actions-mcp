#!/usr/bin/env python3
"""
Simple demonstration of the governance reputation and network risk engines
"""

import asyncio
from datetime import datetime
from enum import Enum


class ReputationTier(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


def simulate_governance_reputation_analysis(address: str):
    """Simulate governance reputation analysis"""
    print(f"🏛️ Governance Reputation Analysis for {address[:20]}...")

    # Simulate reputation analysis results
    reputation_data = {
        'overall_score': 78.5,
        'tier': ReputationTier.GOOD,
        'governance_score': 82.0,
        'community_score': 75.0,
        'consensus_score': 68.0,
        'commitment_score': 89.0,
        'positive_indicators': [
            "Active governance participation (75% voting rate)",
            "Strong community engagement (20+ forum posts)",
            "Long-term ALGO holding (500+ days)",
            "DeFi protocol usage across 4+ platforms"
        ],
        'loan_impact': {
            'ltv_adjustment': 0.05,  # +5% LTV bonus
            'rate_adjustment': -0.002,  # -0.2% rate discount
            'approval_bias': 0.08,  # +8% approval likelihood
            'auto_reject': False
        }
    }

    print(f"  ✅ Overall Score: {reputation_data['overall_score']:.1f}")
    print(f"  🏆 Tier: {reputation_data['tier'].value.upper()}")
    print(f"  📊 Components: Gov({reputation_data['governance_score']:.0f}) "
          f"Com({reputation_data['community_score']:.0f}) "
          f"Con({reputation_data['consensus_score']:.0f}) "
          f"Eco({reputation_data['commitment_score']:.0f})")

    print("  💡 Key Indicators:")
    for indicator in reputation_data['positive_indicators'][:3]:
        print(f"    • {indicator}")

    return reputation_data


def simulate_network_risk_analysis():
    """Simulate network risk analysis"""
    print("\n🌐 Network Risk Assessment...")

    # Simulate risk analysis results
    risk_data = {
        'overall_score': 35.0,
        'risk_level': RiskLevel.LOW,
        'component_scores': {
            'ecosystem_health': 25.0,  # Lower = better (inverted from health score)
            'protocol_risk': 30.0,
            'market_conditions': 45.0,
            'congestion_impact': 20.0,
            'correlation_risk': 40.0,
            'systemic_risk': 25.0
        },
        'risk_factors': [
            "Moderate market volatility detected",
            "Some correlation between major protocols",
            "Overall ecosystem health is strong"
        ],
        'risk_adjustments': {
            'ltv_adjustment': 0.02,  # +2% LTV (low risk bonus)
            'rate_adjustment': -0.001,  # -0.1% rate discount
            'approval_threshold_adjustment': -0.02,  # Easier approval
            'manual_review_required': False,
            'additional_collateral': 0.0
        }
    }

    print(f"  ✅ Overall Risk Score: {risk_data['overall_score']:.1f}")
    print(f"  🚨 Risk Level: {risk_data['risk_level'].value.upper()}")
    print("  📈 Component Scores:")
    for component, score in list(risk_data['component_scores'].items())[:4]:
        risk_emoji = "🔴" if score > 60 else "🟡" if score > 40 else "🟢"
        print(f"    • {component.replace('_', ' ').title()}: {score:.0f} {risk_emoji}")

    return risk_data


def simulate_holistic_loan_decision(borrower_name: str, loan_amount: float,
                                  reputation_data: dict, risk_data: dict):
    """Simulate holistic loan decision making"""
    print(f"\n💰 Holistic Loan Decision for {borrower_name}")
    print("=" * 60)

    # Base loan parameters
    base_ltv = 0.75
    base_rate = 0.08
    base_approval_threshold = 0.60

    # Apply reputation adjustments
    rep_impact = reputation_data['loan_impact']
    adjusted_ltv = base_ltv + rep_impact['ltv_adjustment']
    adjusted_rate = base_rate + rep_impact['rate_adjustment']
    approval_boost = rep_impact['approval_bias']

    # Apply risk adjustments
    risk_adj = risk_data['risk_adjustments']
    final_ltv = adjusted_ltv + risk_adj['ltv_adjustment']
    final_rate = adjusted_rate + risk_adj['rate_adjustment']
    final_threshold = base_approval_threshold + risk_adj['approval_threshold_adjustment'] - approval_boost

    # Calculate required collateral
    required_collateral = loan_amount / final_ltv

    # Make decision
    combined_score = (reputation_data['overall_score'] - risk_data['overall_score']) / 2

    if combined_score > 70:
        decision = "APPROVED"
        decision_emoji = "✅"
    elif combined_score > 40:
        decision = "NEEDS_REVIEW"
        decision_emoji = "🔍"
    else:
        decision = "REJECTED"
        decision_emoji = "❌"

    # Display results
    print(f"📊 Loan Amount: ${loan_amount:,.0f}")
    print(f"🏛️ Reputation Score: {reputation_data['overall_score']:.1f} ({reputation_data['tier'].value})")
    print(f"🌐 Network Risk Score: {risk_data['overall_score']:.1f} ({risk_data['risk_level'].value})")
    print(f"🎯 Combined Score: {combined_score:.1f}")
    print()
    print("⚙️ Applied Adjustments:")
    print(f"  • LTV: {base_ltv:.1%} → {final_ltv:.1%} "
          f"({rep_impact['ltv_adjustment']:+.1%} rep + {risk_adj['ltv_adjustment']:+.1%} risk)")
    print(f"  • Rate: {base_rate:.2%} → {final_rate:.2%} "
          f"({rep_impact['rate_adjustment']:+.3f}% rep + {risk_adj['rate_adjustment']:+.3f}% risk)")
    print(f"  • Approval Boost: {approval_boost:+.1%} (reputation)")
    print()
    print(f"💰 Required Collateral: ${required_collateral:,.0f}")
    print(f"{decision_emoji} FINAL DECISION: {decision}")

    return {
        'decision': decision,
        'loan_amount': loan_amount,
        'required_collateral': required_collateral,
        'final_ltv': final_ltv,
        'final_rate': final_rate,
        'combined_score': combined_score
    }


async def main():
    """Main demonstration function"""
    print("🌟 Algorand Holistic Loan Decision Engine Demo")
    print("=" * 80)
    print("Demonstrating governance reputation and network risk integration")
    print("for comprehensive, ecosystem-focused loan approval decisions.")
    print("=" * 80)

    # Test scenarios
    scenarios = [
        {
            'name': 'Alice - Ecosystem Contributor',
            'address': 'ALICE_GOVERNANCE_LEADER_ADDRESS_123',
            'loan_amount': 50000.0
        },
        {
            'name': 'Bob - Average User',
            'address': 'BOB_REGULAR_USER_ADDRESS_456',
            'loan_amount': 25000.0
        },
        {
            'name': 'Charlie - New User',
            'address': 'CHARLIE_NEW_USER_ADDRESS_789',
            'loan_amount': 75000.0
        }
    ]

    results = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔍 Scenario {i}: {scenario['name']}")
        print("=" * 60)

        # Analyze governance reputation
        reputation_data = simulate_governance_reputation_analysis(scenario['address'])

        # Analyze network risk
        risk_data = simulate_network_risk_analysis()

        # Make holistic decision
        decision_result = simulate_holistic_loan_decision(
            scenario['name'],
            scenario['loan_amount'],
            reputation_data,
            risk_data
        )

        results.append({
            'name': scenario['name'],
            'reputation_score': reputation_data['overall_score'],
            'risk_score': risk_data['overall_score'],
            'decision': decision_result['decision'],
            'loan_amount': decision_result['loan_amount'],
            'final_ltv': decision_result['final_ltv'],
            'final_rate': decision_result['final_rate']
        })

        print("-" * 60)

    # Summary
    print(f"\n📋 SUMMARY RESULTS")
    print("=" * 80)

    approved = len([r for r in results if r['decision'] == 'APPROVED'])
    needs_review = len([r for r in results if r['decision'] == 'NEEDS_REVIEW'])
    rejected = len([r for r in results if r['decision'] == 'REJECTED'])

    print(f"📊 Decision Distribution:")
    print(f"  • Approved: {approved}/{len(results)}")
    print(f"  • Needs Review: {needs_review}/{len(results)}")
    print(f"  • Rejected: {rejected}/{len(results)}")

    print(f"\n💡 Key Benefits Demonstrated:")
    print("  • Long-term ecosystem commitment evaluation")
    print("  • Real-time network risk consideration")
    print("  • Dynamic parameter adjustment based on conditions")
    print("  • Community-focused lending approach")
    print("  • Holistic decision making beyond traditional metrics")

    print(f"\n🎯 Engine Capabilities:")
    print("  • Governance participation analysis")
    print("  • Community engagement scoring")
    print("  • Consensus participation tracking")
    print("  • Ecosystem commitment assessment")
    print("  • Real-time network risk monitoring")
    print("  • Dynamic risk adjustments")

    print("\n✅ DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())