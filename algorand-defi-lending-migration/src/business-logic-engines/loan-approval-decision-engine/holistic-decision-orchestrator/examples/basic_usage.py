#!/usr/bin/env python3
"""
Basic Usage Example for Holistic Decision Orchestrator

This example demonstrates the basic functionality of the holistic loan approval system.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from holistic_decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanApplication,
    LoanDecision,
    DecisionConfidence
)


async def basic_loan_application_example():
    """
    Basic example of processing a loan application.
    """
    print("🏦 Holistic Decision Orchestrator - Basic Usage Example")
    print("=" * 60)

    # Initialize the orchestrator
    orchestrator = HolisticDecisionOrchestrator()

    # Create a loan application
    application = LoanApplication(
        application_id="EXAMPLE_001",
        borrower_address="EXAMPLE_ALGORAND_ADDRESS_123",
        loan_amount=50000.0,
        requested_term=180,  # 6 months
        collateral_assets=[
            {'asset': 'ALGO', 'amount': 40000, 'value': 40000},
            {'asset': 'USDC', 'amount': 20000, 'value': 20000}
        ],
        purpose="DeFi strategy expansion",
        timestamp=datetime.now(),
        market_conditions={'volatility': 0.15},
        network_health={'health_score': 0.95}
    )

    print(f"📋 Processing loan application: {application.application_id}")
    print(f"💰 Requested amount: {application.loan_amount:,.0f} ALGO")
    print(f"📅 Requested term: {application.requested_term} days")
    print(f"🏠 Collateral value: {sum(asset['value'] for asset in application.collateral_assets):,.0f} ALGO")
    print()

    # Process the application
    print("🔄 Processing through holistic analysis...")
    decision = await orchestrator.process_loan_application(application)

    # Display results
    print("✅ Analysis Complete!")
    print()
    print_decision_summary(decision)


def print_decision_summary(decision):
    """Print a formatted summary of the loan decision."""

    print("📊 DECISION SUMMARY")
    print("-" * 40)
    print(f"Decision: {decision.decision.value.upper()}")
    print(f"Confidence: {decision.confidence.value.upper()}")
    print(f"Overall Score: {decision.overall_score:.3f}")
    print(f"Processing Time: {decision.processing_time:.2f} seconds")
    print()

    print("🎯 ENGINE SCORES")
    print("-" * 40)
    print(f"Ecosystem Analysis:     {decision.ecosystem_score:.3f}")
    print(f"DeFi Behavior:          {decision.defi_score:.3f}")
    print(f"Collateral Intelligence: {decision.collateral_score:.3f}")
    print(f"Governance Reputation:   {decision.governance_score:.3f}")
    print(f"Risk Assessment:         {decision.risk_score:.3f}")
    print()

    if decision.decision in [LoanDecision.APPROVED, LoanDecision.CONDITIONALLY_APPROVED]:
        print("💳 LOAN TERMS")
        print("-" * 40)
        print(f"Approved Amount: {decision.approved_amount:,.0f} ALGO")
        print(f"Interest Rate: {decision.interest_rate:.2%}")
        print(f"Loan Term: {decision.loan_term} days")
        print(f"LTV Ratio: {decision.ltv_ratio:.1%}")
        print()

        if decision.conditions:
            print("📋 CONDITIONS")
            print("-" * 40)
            for i, condition in enumerate(decision.conditions, 1):
                print(f"{i}. {condition}")
            print()

        print("📈 MONITORING")
        print("-" * 40)
        print(f"Frequency: {decision.monitoring_frequency}")
        print(f"Parameters: {', '.join(decision.monitoring_parameters[:3])}...")
        print()

    print("🎯 DECISION RATIONALE")
    print("-" * 40)
    print("Primary Factors:")
    for factor in decision.primary_factors:
        print(f"  • {factor}")

    if decision.risk_factors:
        print("\nRisk Factors:")
        for factor in decision.risk_factors:
            print(f"  ⚠ {factor}")

    if decision.positive_factors:
        print("\nPositive Factors:")
        for factor in decision.positive_factors:
            print(f"  ✓ {factor}")

    if decision.alternatives:
        print("\n🔄 ALTERNATIVES AVAILABLE")
        print("-" * 40)
        for i, alt in enumerate(decision.alternatives, 1):
            print(f"{i}. {alt['title']}")
            print(f"   {alt['description']}")
        print()


async def borrower_profile_example():
    """
    Example of generating a detailed borrower profile.
    """
    print("\n" + "=" * 60)
    print("👤 BORROWER PROFILE EXAMPLE")
    print("=" * 60)

    orchestrator = HolisticDecisionOrchestrator()

    # Generate borrower profile
    address = "EXAMPLE_BORROWER_ADDRESS_456"
    print(f"📊 Generating profile for: {address}")

    profile = await orchestrator._build_borrower_profile(address)

    print("\n📋 PROFILE SUMMARY")
    print("-" * 40)
    print(f"Address: {profile.address}")
    print(f"Data Completeness: {profile.data_completeness:.1%}")
    print(f"Profile Generated: {profile.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("🎯 DETAILED SCORES")
    print("-" * 40)
    print(f"Ecosystem Analysis:      {profile.ecosystem_score:.3f} (confidence: {profile.ecosystem_confidence:.2f})")
    print(f"DeFi Behavior:           {profile.defi_score:.3f} (confidence: {profile.defi_confidence:.2f})")
    print(f"Collateral Intelligence: {profile.collateral_score:.3f} (confidence: {profile.collateral_confidence:.2f})")
    print(f"Governance Reputation:   {profile.governance_score:.3f} (confidence: {profile.governance_confidence:.2f})")
    print(f"Risk Assessment:         {profile.risk_score:.3f} (confidence: {profile.risk_confidence:.2f})")
    print()

    # Sample data insights
    print("💡 KEY INSIGHTS")
    print("-" * 40)
    if profile.ecosystem_score >= 0.7:
        print("✓ Strong ecosystem participation")
    if profile.defi_score >= 0.6:
        print("✓ Good DeFi experience and risk management")
    if profile.collateral_score >= 0.8:
        print("✓ High-quality collateral portfolio")
    if profile.governance_score >= 0.5:
        print("✓ Active in governance participation")
    if profile.risk_score <= 0.3:
        print("✓ Low risk profile")

    if profile.data_completeness < 0.7:
        print("⚠ Limited data available - may affect decision confidence")


async def multiple_scenarios_example():
    """
    Example showing different borrower scenarios and their outcomes.
    """
    print("\n" + "=" * 60)
    print("🎭 MULTIPLE SCENARIOS EXAMPLE")
    print("=" * 60)

    orchestrator = HolisticDecisionOrchestrator()

    scenarios = [
        {
            'name': 'DeFi Power User',
            'address': 'DEFI_POWER_USER_ADDRESS',
            'amount': 75000,
            'collateral': [
                {'asset': 'ALGO', 'amount': 60000, 'value': 60000},
                {'asset': 'USDC', 'amount': 40000, 'value': 40000}
            ],
            'purpose': 'Advanced DeFi strategies'
        },
        {
            'name': 'Governance Leader',
            'address': 'GOVERNANCE_LEADER_ADDRESS',
            'amount': 100000,
            'collateral': [
                {'asset': 'ALGO', 'amount': 120000, 'value': 120000}
            ],
            'purpose': 'Community development'
        },
        {
            'name': 'New User',
            'address': 'NEW_USER_ADDRESS',
            'amount': 15000,
            'collateral': [
                {'asset': 'ALGO', 'amount': 20000, 'value': 20000}
            ],
            'purpose': 'First DeFi experience'
        },
        {
            'name': 'High Risk User',
            'address': 'HIGH_RISK_ADDRESS',
            'amount': 50000,
            'collateral': [
                {'asset': 'OPUL', 'amount': 25000, 'value': 5000}  # Low quality
            ],
            'purpose': 'Speculative trading'
        }
    ]

    for scenario in scenarios:
        print(f"\n🎯 Scenario: {scenario['name']}")
        print("-" * 30)

        application = LoanApplication(
            application_id=f"SCENARIO_{scenario['name'].upper().replace(' ', '_')}",
            borrower_address=scenario['address'],
            loan_amount=scenario['amount'],
            requested_term=180,
            collateral_assets=scenario['collateral'],
            purpose=scenario['purpose'],
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        decision = await orchestrator.process_loan_application(application)

        print(f"Decision: {decision.decision.value}")
        print(f"Score: {decision.overall_score:.3f}")
        if decision.approved_amount:
            print(f"Amount: {decision.approved_amount:,.0f} ALGO")
            print(f"Rate: {decision.interest_rate:.2%}")


async def configuration_example():
    """
    Example of using custom configuration.
    """
    print("\n" + "=" * 60)
    print("⚙️ CUSTOM CONFIGURATION EXAMPLE")
    print("=" * 60)

    # Custom configuration emphasizing governance
    custom_config = {
        'engine_weights': {
            'ecosystem_analysis': 0.25,      # Reduced
            'defi_behavior': 0.20,          # Reduced
            'collateral_intelligence': 0.20, # Same
            'governance_reputation': 0.25,   # Increased
            'network_risk_monitoring': 0.10  # Same
        },
        'approval_thresholds': {
            'excellent': 0.90,  # More conservative
            'good': 0.75,
            'fair': 0.60,
            'poor': 0.45,
            'reject': 0.44
        }
    }

    print("📋 Custom Configuration:")
    print("- Increased governance weight to 25%")
    print("- More conservative approval thresholds")
    print("- Emphasis on community participation")
    print()

    # Initialize with custom config
    orchestrator = HolisticDecisionOrchestrator()

    # Test with governance-focused application
    application = LoanApplication(
        application_id="GOVERNANCE_FOCUSED_001",
        borrower_address="GOVERNANCE_FOCUSED_ADDRESS",
        loan_amount=50000.0,
        requested_term=365,
        collateral_assets=[
            {'asset': 'ALGO', 'amount': 75000, 'value': 75000}
        ],
        purpose="Governance participation and community building",
        timestamp=datetime.now(),
        market_conditions={'volatility': 0.12},
        network_health={'health_score': 0.96}
    )

    decision = await orchestrator.process_loan_application(application)

    print("📊 Results with Governance-Focused Configuration:")
    print(f"Decision: {decision.decision.value}")
    print(f"Overall Score: {decision.overall_score:.3f}")
    print(f"Governance Score: {decision.governance_score:.3f}")

    if decision.decision == LoanDecision.APPROVED:
        print("✅ Governance participation rewarded with approval!")


async def main():
    """
    Run all examples.
    """
    print("🚀 Starting Holistic Decision Orchestrator Examples")
    print()

    try:
        await basic_loan_application_example()
        await borrower_profile_example()
        await multiple_scenarios_example()
        await configuration_example()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("📚 Check the documentation for more advanced usage patterns.")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("💡 This is normal in a demo environment without real Algorand data.")


if __name__ == "__main__":
    asyncio.run(main())