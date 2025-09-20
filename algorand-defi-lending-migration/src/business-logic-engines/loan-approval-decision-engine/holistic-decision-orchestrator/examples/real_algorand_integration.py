#!/usr/bin/env python3
"""
Real Algorand Integration Example

This example demonstrates integration with real Algorand addresses and data.
It shows how to analyze actual ecosystem participation and make decisions
based on real blockchain activity.

NOTE: This example requires real Algorand addresses and network connectivity.
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any

from holistic_decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanApplication
)


# Real Algorand addresses for demonstration
# These would be replaced with actual addresses in production
EXAMPLE_ADDRESSES = {
    'ecosystem_active': 'ALGORAND_FOUNDATION_ADDRESS',  # Well-known active address
    'governance_participant': 'GOVERNANCE_ADDRESS',     # Address with governance history
    'defi_user': 'DEFI_USER_ADDRESS',                  # Address with DeFi activity
    'new_user': 'NEW_USER_ADDRESS',                    # Recently created address
    'whale': 'WHALE_ADDRESS'                           # High-balance address
}


async def analyze_real_algorand_address(address: str, name: str = None):
    """
    Analyze a real Algorand address and generate comprehensive profile.
    """
    if not name:
        name = address[:12] + "..."

    print(f"\n🔍 Analyzing Real Address: {name}")
    print(f"Address: {address}")
    print("-" * 60)

    try:
        orchestrator = HolisticDecisionOrchestrator()

        # Generate real borrower profile
        print("📊 Building borrower profile from blockchain data...")
        profile = await orchestrator._build_borrower_profile(address)

        print("\n📋 REAL PROFILE ANALYSIS")
        print("-" * 40)
        print(f"Data Completeness: {profile.data_completeness:.1%}")
        print(f"Profile Timestamp: {profile.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        print("🎯 ENGINE SCORES (Real Data)")
        print("-" * 40)
        print(f"Ecosystem Analysis:      {profile.ecosystem_score:.3f} (conf: {profile.ecosystem_confidence:.2f})")
        print(f"DeFi Behavior:           {profile.defi_score:.3f} (conf: {profile.defi_confidence:.2f})")
        print(f"Collateral Intelligence: {profile.collateral_score:.3f} (conf: {profile.collateral_confidence:.2f})")
        print(f"Governance Reputation:   {profile.governance_score:.3f} (conf: {profile.governance_confidence:.2f})")
        print(f"Risk Assessment:         {profile.risk_score:.3f} (conf: {profile.risk_confidence:.2f})")

        # Generate insights based on real data
        generate_real_insights(profile)

        return profile

    except Exception as e:
        print(f"❌ Error analyzing address: {e}")
        print("💡 This may occur if the address is invalid or network is unavailable")
        return None


def generate_real_insights(profile):
    """Generate insights based on real profile data."""
    print("\n💡 REAL DATA INSIGHTS")
    print("-" * 40)

    insights = []

    # Ecosystem analysis insights
    if profile.ecosystem_score >= 0.8:
        insights.append("✅ Exceptional ecosystem participation")
    elif profile.ecosystem_score >= 0.6:
        insights.append("✅ Strong ecosystem engagement")
    elif profile.ecosystem_score >= 0.4:
        insights.append("⚠️ Moderate ecosystem activity")
    else:
        insights.append("❌ Limited ecosystem participation")

    # DeFi behavior insights
    if profile.defi_score >= 0.7:
        insights.append("✅ Experienced DeFi user with good risk management")
    elif profile.defi_score >= 0.5:
        insights.append("✅ Active DeFi participant")
    elif profile.defi_score >= 0.3:
        insights.append("⚠️ Limited DeFi experience")
    else:
        insights.append("❌ Minimal or no DeFi activity")

    # Collateral quality insights
    if profile.collateral_score >= 0.8:
        insights.append("✅ High-quality, well-diversified collateral")
    elif profile.collateral_score >= 0.6:
        insights.append("✅ Good collateral quality")
    elif profile.collateral_score >= 0.4:
        insights.append("⚠️ Moderate collateral quality")
    else:
        insights.append("❌ Poor or insufficient collateral")

    # Governance insights
    if profile.governance_score >= 0.7:
        insights.append("✅ Active governance participant and community leader")
    elif profile.governance_score >= 0.5:
        insights.append("✅ Regular governance participation")
    elif profile.governance_score >= 0.3:
        insights.append("⚠️ Occasional governance participation")
    else:
        insights.append("❌ No governance participation")

    # Risk insights
    if profile.risk_score <= 0.2:
        insights.append("✅ Very low risk profile")
    elif profile.risk_score <= 0.4:
        insights.append("✅ Low risk profile")
    elif profile.risk_score <= 0.6:
        insights.append("⚠️ Moderate risk profile")
    else:
        insights.append("❌ High risk profile")

    # Data completeness insights
    if profile.data_completeness >= 0.9:
        insights.append("✅ Comprehensive data available")
    elif profile.data_completeness >= 0.7:
        insights.append("✅ Good data coverage")
    elif profile.data_completeness >= 0.5:
        insights.append("⚠️ Moderate data availability")
    else:
        insights.append("❌ Limited data available")

    for insight in insights:
        print(f"  {insight}")


async def process_real_loan_application(address: str, loan_amount: float, name: str = None):
    """
    Process a real loan application using actual Algorand address data.
    """
    if not name:
        name = address[:12] + "..."

    print(f"\n💰 Processing Real Loan Application")
    print(f"Borrower: {name}")
    print(f"Address: {address}")
    print(f"Amount: {loan_amount:,.0f} ALGO")
    print("-" * 60)

    try:
        orchestrator = HolisticDecisionOrchestrator()

        # Create loan application with real address
        application = LoanApplication(
            application_id=f"REAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            borrower_address=address,
            loan_amount=loan_amount,
            requested_term=180,  # 6 months
            collateral_assets=[],  # Will be populated from real data
            purpose="Real Algorand ecosystem loan",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.15},
            network_health={'health_score': 0.95}
        )

        print("🔄 Processing through holistic analysis with real data...")
        decision = await orchestrator.process_loan_application(application)

        print("\n📊 REAL LOAN DECISION")
        print("-" * 40)
        print(f"Decision: {decision.decision.value.upper()}")
        print(f"Confidence: {decision.confidence.value.upper()}")
        print(f"Overall Score: {decision.overall_score:.3f}")
        print(f"Processing Time: {decision.processing_time:.2f} seconds")

        if decision.approved_amount:
            print(f"\n💳 APPROVED TERMS")
            print("-" * 40)
            print(f"Approved Amount: {decision.approved_amount:,.0f} ALGO")
            print(f"Interest Rate: {decision.interest_rate:.2%}")
            print(f"LTV Ratio: {decision.ltv_ratio:.1%}")

        print(f"\n🎯 DECISION RATIONALE")
        print("-" * 40)
        for factor in decision.primary_factors:
            print(f"  • {factor}")

        return decision

    except Exception as e:
        print(f"❌ Error processing loan application: {e}")
        return None


async def compare_multiple_real_addresses():
    """
    Compare loan decisions for multiple real Algorand addresses.
    """
    print("\n" + "=" * 80)
    print("🔄 COMPARATIVE ANALYSIS OF REAL ADDRESSES")
    print("=" * 80)

    results = []

    for address_type, address in EXAMPLE_ADDRESSES.items():
        print(f"\n📊 Analyzing: {address_type.replace('_', ' ').title()}")

        try:
            profile = await analyze_real_algorand_address(address, address_type)
            if profile:
                # Test with standard loan amount
                decision = await process_real_loan_application(address, 50000.0, address_type)

                results.append({
                    'type': address_type,
                    'address': address,
                    'profile': profile,
                    'decision': decision
                })

        except Exception as e:
            print(f"❌ Failed to analyze {address_type}: {e}")
            continue

    # Generate comparison report
    if results:
        print("\n" + "=" * 80)
        print("📈 COMPARATIVE RESULTS")
        print("=" * 80)

        print(f"{'Address Type':<20} {'Overall Score':<15} {'Decision':<20} {'Rate':<10}")
        print("-" * 80)

        for result in results:
            if result['decision']:
                score = result['profile'].ecosystem_score if result['profile'] else 0
                decision_str = result['decision'].decision.value
                rate = f"{result['decision'].interest_rate:.2%}" if result['decision'].interest_rate else "N/A"
            else:
                score = 0
                decision_str = "ERROR"
                rate = "N/A"

            print(f"{result['type']:<20} {score:<15.3f} {decision_str:<20} {rate:<10}")


async def test_mcp_services_integration():
    """
    Test integration with MCP services running on ports 8002/8003.
    """
    print("\n" + "=" * 80)
    print("🔌 MCP SERVICES INTEGRATION TEST")
    print("=" * 80)

    try:
        import httpx

        # Test MCP Reader Service (port 8002)
        print("🔍 Testing MCP Reader Service (port 8002)...")
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get("http://localhost:8002/health")
                if response.status_code == 200:
                    print("✅ MCP Reader Service is available")

                    # Test account data retrieval
                    test_address = list(EXAMPLE_ADDRESSES.values())[0]
                    account_response = await client.get(f"http://localhost:8002/account/{test_address}")

                    if account_response.status_code == 200:
                        print("✅ Account data retrieval working")
                    else:
                        print(f"⚠️ Account data retrieval returned: {account_response.status_code}")

                else:
                    print(f"❌ MCP Reader Service health check failed: {response.status_code}")

            except httpx.ConnectError:
                print("❌ MCP Reader Service not available (connection refused)")

        # Test MCP Writer Service (port 8003)
        print("\n🔍 Testing MCP Writer Service (port 8003)...")
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get("http://localhost:8003/health")
                if response.status_code == 200:
                    print("✅ MCP Writer Service is available")

                    # Test decision storage
                    test_decision = {
                        'application_id': 'MCP_TEST_001',
                        'decision': 'approved',
                        'timestamp': datetime.now().isoformat()
                    }

                    store_response = await client.post(
                        "http://localhost:8003/decisions",
                        json=test_decision
                    )

                    if store_response.status_code in [200, 201]:
                        print("✅ Decision storage working")
                    else:
                        print(f"⚠️ Decision storage returned: {store_response.status_code}")

                else:
                    print(f"❌ MCP Writer Service health check failed: {response.status_code}")

            except httpx.ConnectError:
                print("❌ MCP Writer Service not available (connection refused)")

    except ImportError:
        print("❌ httpx not available for MCP testing")


async def test_governance_api_integration():
    """
    Test integration with Algorand governance API.
    """
    print("\n" + "=" * 80)
    print("🏛️ GOVERNANCE API INTEGRATION TEST")
    print("=" * 80)

    try:
        import httpx

        governance_url = "https://governance.algorand.foundation/api"

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Test governance API availability
                response = await client.get(f"{governance_url}/status")

                if response.status_code == 200:
                    print("✅ Governance API is available")

                    # Test current period data
                    period_response = await client.get(f"{governance_url}/periods/current")

                    if period_response.status_code == 200:
                        period_data = period_response.json()
                        print(f"✅ Current governance period: {period_data.get('period_id', 'Unknown')}")
                        print(f"   Status: {period_data.get('status', 'Unknown')}")
                    else:
                        print(f"⚠️ Current period data: {period_response.status_code}")

                    # Test participant data for sample address
                    test_address = EXAMPLE_ADDRESSES.get('governance_participant', 'TEST_ADDRESS')
                    participant_response = await client.get(
                        f"{governance_url}/accounts/{test_address}/participation"
                    )

                    if participant_response.status_code == 200:
                        print("✅ Participant data retrieval working")
                    elif participant_response.status_code == 404:
                        print("⚠️ Test address not found in governance data (expected)")
                    else:
                        print(f"⚠️ Participant data returned: {participant_response.status_code}")

                else:
                    print(f"❌ Governance API not available: {response.status_code}")

            except httpx.ConnectError:
                print("❌ Governance API not reachable")

    except ImportError:
        print("❌ httpx not available for governance API testing")


async def main():
    """
    Run real Algorand integration examples.
    """
    print("🚀 REAL ALGORAND INTEGRATION EXAMPLES")
    print("=" * 80)
    print("⚠️  Note: These examples require real Algorand network connectivity")
    print("🔗 Some features require MCP services running on ports 8002/8003")
    print()

    # Check if we should run network tests
    run_network_tests = os.getenv('RUN_NETWORK_TESTS', 'false').lower() == 'true'

    if not run_network_tests:
        print("💡 Set RUN_NETWORK_TESTS=true to run tests with real network data")
        print("🎭 Running with mock data for demonstration...")

        # Run basic examples with mock data
        await basic_mock_examples()
    else:
        print("🌐 Running with real network connectivity...")

        try:
            # Test MCP services
            await test_mcp_services_integration()

            # Test governance API
            await test_governance_api_integration()

            # Analyze real addresses
            await compare_multiple_real_addresses()

        except Exception as e:
            print(f"❌ Error running network tests: {e}")
            print("💡 Falling back to mock examples...")
            await basic_mock_examples()

    print("\n" + "=" * 80)
    print("✅ Real Algorand integration examples completed!")
    print("📚 Check logs for any connection issues or data limitations.")


async def basic_mock_examples():
    """
    Run basic examples with mock data when network isn't available.
    """
    print("\n🎭 Running mock examples (no network required)...")

    # This would use the existing orchestrator with mock data
    orchestrator = HolisticDecisionOrchestrator()

    mock_address = "MOCK_EXAMPLE_ADDRESS_123"

    # Generate mock profile
    profile = await orchestrator._build_borrower_profile(mock_address)

    print(f"\n📊 Mock Profile Generated:")
    print(f"Address: {mock_address}")
    print(f"Ecosystem Score: {profile.ecosystem_score:.3f}")
    print(f"DeFi Score: {profile.defi_score:.3f}")
    print(f"Collateral Score: {profile.collateral_score:.3f}")
    print(f"Governance Score: {profile.governance_score:.3f}")
    print(f"Risk Score: {profile.risk_score:.3f}")

    # Process mock loan application
    application = LoanApplication(
        application_id="MOCK_REAL_001",
        borrower_address=mock_address,
        loan_amount=50000.0,
        requested_term=180,
        collateral_assets=[
            {'asset': 'ALGO', 'amount': 60000, 'value': 60000}
        ],
        purpose="Mock real integration test",
        timestamp=datetime.now(),
        market_conditions={'volatility': 0.15},
        network_health={'health_score': 0.95}
    )

    decision = await orchestrator.process_loan_application(application)

    print(f"\n💰 Mock Decision:")
    print(f"Decision: {decision.decision.value}")
    print(f"Score: {decision.overall_score:.3f}")
    if decision.approved_amount:
        print(f"Amount: {decision.approved_amount:,.0f} ALGO")


if __name__ == "__main__":
    asyncio.run(main())