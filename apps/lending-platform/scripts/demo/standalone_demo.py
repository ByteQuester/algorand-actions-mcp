#!/usr/bin/env python3
"""
Standalone ADK Demo
Tests tool functions directly without agent imports
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/adk-agents')

def test_negotiation_tools():
    """Test negotiation tools directly"""
    print("🤝 Testing Negotiation Tools...")

    # Import tools directly from the module
    from negotiation.tools import (
        calculate_interest_rate,
        assess_loan_risk,
        calculate_collateral_requirement,
        generate_counter_proposal
    )

    print("1. Interest Rate Calculation:")
    rate_result = calculate_interest_rate(
        loan_amount_algos=100.0,
        duration_days=30,
        borrower_risk_score=75,
        market_base_rate=7.5
    )
    print(f"   ✅ Suggested rate: {rate_result['suggested_interest_rate']}%")

    print("2. Risk Assessment:")
    risk_result = assess_loan_risk(
        borrower_address="TEST_ADDRESS",
        loan_amount_algos=100.0,
        borrower_balance_algos=150.0,
        transaction_history={"transaction_count": 50, "average_transaction_size": 5.0},
        requested_duration_days=30
    )
    print(f"   ✅ Risk: {risk_result['risk_category']} ({risk_result['risk_score']}/100)")

    print("3. Collateral Calculation:")
    collateral_result = calculate_collateral_requirement(
        loan_amount_algos=100.0,
        borrower_risk_score=75
    )
    print(f"   ✅ Collateral needed: {collateral_result['required_collateral_algos']} ALGO")


def test_liquidity_tools():
    """Test liquidity tools directly"""
    print("\n💰 Testing Liquidity Tools...")

    from liquidity.tools import (
        find_available_lenders,
        assess_borrower_creditworthiness,
        match_liquidity_requirements
    )

    print("1. Lender Discovery:")
    lenders = find_available_lenders(
        loan_amount_algos=100.0,
        target_interest_rate=8.0,
        duration_days=30
    )
    print(f"   ✅ Found {lenders['total_lenders_found']} lenders")

    print("2. Creditworthiness Assessment:")
    credit = assess_borrower_creditworthiness(
        borrower_address="TEST_ADDRESS",
        current_balance_algos=150.0,
        transaction_history={
            "total_transactions": 50,
            "average_amount": 5.0,
            "monthly_frequency": 10,
            "activity_span_days": 180
        }
    )
    print(f"   ✅ Credit tier: {credit['credit_tier']}")


def test_execution_tools():
    """Test execution tools directly"""
    print("\n⚡ Testing Execution Tools...")

    from execution.tools import (
        prepare_transaction_group,
        validate_execution_requirements,
        estimate_transaction_costs
    )

    print("1. Transaction Preparation:")
    tx_group = prepare_transaction_group(
        borrower_address="BORROWER_TEST_12345678901234567890123456789012345678",
        lender_address="LENDER_TEST_123456789012345678901234567890123456789",
        loan_amount_algos=100.0,
        collateral_amount_algos=130.0,
        interest_rate_percent=7.5,
        duration_days=30
    )
    print(f"   ✅ {len(tx_group['transaction_group']['transactions'])} transactions prepared")

    print("2. Execution Validation:")
    validation = validate_execution_requirements(
        borrower_address="BORROWER_TEST_12345678901234567890123456789012345678",
        lender_address="LENDER_TEST_123456789012345678901234567890123456789",
        loan_amount_algos=100.0,
        collateral_amount_algos=130.0,
        borrower_balance_algos=160.0,
        lender_balance_algos=120.0
    )
    print(f"   ✅ Execution readiness: {validation['execution_readiness']}")


def test_coordination_tools():
    """Test coordination tools directly"""
    print("\n🎯 Testing Coordination Tools...")

    from coordination.tools import (
        check_mcp_service_health,
        get_borrower_data,
        coordinate_lending_workflow
    )

    print("1. MCP Service Health:")
    health = check_mcp_service_health()
    print(f"   ✅ Status: {health['overall_status']}")

    print("2. Borrower Data:")
    borrower_data = get_borrower_data("TEST_ADDRESS")
    print(f"   ✅ Balance: {borrower_data['balance_data']['algo_balance']} ALGO")

    print("3. Workflow Coordination:")
    workflow = coordinate_lending_workflow(
        loan_request={
            "borrower_address": "TEST_ADDRESS",
            "amount_algos": 50.0,
            "duration_days": 30
        },
        borrower_data=borrower_data
    )
    print(f"   ✅ Workflow: {workflow['workflow_coordination']['status']}")


def main():
    """Main test function"""
    print("🎯 ADK Lending Tools - Standalone Demo")
    print("Testing tool functions without ADK agent framework")
    print("=" * 60)

    try:
        test_negotiation_tools()
        test_liquidity_tools()
        test_execution_tools()
        test_coordination_tools()

        print("\n" + "=" * 60)
        print("🎉 All ADK tools working successfully!")
        print("\n✅ Key Features Demonstrated:")
        print("• Risk-based interest rate calculation")
        print("• Comprehensive loan risk assessment")
        print("• Intelligent lender discovery and matching")
        print("• Atomic transaction group preparation")
        print("• Complete workflow coordination")
        print("• MCP service integration")

        print("\n🏗️ ADK Architecture Ready:")
        print("• Tool functions implemented and tested")
        print("• Agent patterns designed for Google ADK")
        print("• MCP integration for blockchain operations")
        print("• Parallel implementation to existing system")

        print("\n🚀 Next Steps:")
        print("1. pip install google-adk")
        print("2. Set GOOGLE_API_KEY environment variable")
        print("3. Start MCP services on ports 8002 and 3001")
        print("4. Test with actual Gemini integration")

        return 0

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())