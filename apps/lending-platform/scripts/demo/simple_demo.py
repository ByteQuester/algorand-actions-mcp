#!/usr/bin/env python3
"""
Simple ADK Demo
Demonstrates ADK lending patterns without requiring google-adk package
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Import tool functions directly
import sys
import os
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/adk-agents')

from negotiation.tools import (
    calculate_interest_rate,
    assess_loan_risk,
    calculate_collateral_requirement,
    generate_counter_proposal
)
from liquidity.tools import (
    find_available_lenders,
    assess_borrower_creditworthiness,
    match_liquidity_requirements,
    calculate_liquidity_costs
)
from execution.tools import (
    prepare_transaction_group,
    validate_execution_requirements,
    estimate_transaction_costs,
    create_lending_contract
)
from coordination.tools import (
    check_mcp_service_health,
    get_borrower_data,
    get_lender_data,
    coordinate_lending_workflow
)


def demo_negotiation_tools():
    """Demo negotiation agent tools"""
    print("🤝 Negotiation Agent Tools Demo")
    print("=" * 50)

    # Test interest rate calculation
    print("1. Calculating interest rate...")
    rate_result = calculate_interest_rate(
        loan_amount_algos=100.0,
        duration_days=30,
        borrower_risk_score=75,
        market_base_rate=7.5,
        collateral_ratio=1.3
    )
    print(f"   ✅ Suggested rate: {rate_result['suggested_interest_rate']}%")
    print(f"   📊 Risk adjustment: {rate_result['adjustments']['risk']}%")

    # Test risk assessment
    print("\n2. Assessing loan risk...")
    risk_result = assess_loan_risk(
        borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        loan_amount_algos=100.0,
        borrower_balance_algos=150.0,
        transaction_history={"transaction_count": 50, "average_transaction_size": 5.0},
        requested_duration_days=30
    )
    print(f"   ✅ Risk category: {risk_result['risk_category']}")
    print(f"   📈 Risk score: {risk_result['risk_score']}/100")
    print(f"   🎯 Recommendation: {risk_result['recommendation']}")

    # Test collateral calculation
    print("\n3. Calculating collateral requirement...")
    collateral_result = calculate_collateral_requirement(
        loan_amount_algos=100.0,
        borrower_risk_score=75,
        collateral_type="ALGO"
    )
    print(f"   ✅ Required collateral: {collateral_result['required_collateral_algos']} ALGO")
    print(f"   📊 Collateral ratio: {collateral_result['collateral_ratio']}x")


def demo_liquidity_tools():
    """Demo liquidity agent tools"""
    print("\n💰 Liquidity Agent Tools Demo")
    print("=" * 50)

    # Test lender discovery
    print("1. Finding available lenders...")
    lenders_result = find_available_lenders(
        loan_amount_algos=100.0,
        target_interest_rate=8.0,
        duration_days=30,
        borrower_risk_category="MEDIUM"
    )
    print(f"   ✅ Lenders found: {lenders_result['total_lenders_found']}")
    print(f"   📊 Rate range: {lenders_result['rate_range']['lowest']}-{lenders_result['rate_range']['highest']}%")
    if lenders_result['available_lenders']:
        best_lender = lenders_result['available_lenders'][0]
        print(f"   🏆 Best option: {best_lender['name']} at {best_lender['offered_interest_rate']}%")

    # Test creditworthiness assessment
    print("\n2. Assessing borrower creditworthiness...")
    credit_result = assess_borrower_creditworthiness(
        borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        current_balance_algos=150.0,
        transaction_history={
            "total_transactions": 50,
            "average_amount": 5.0,
            "monthly_frequency": 10,
            "activity_span_days": 180
        },
        loan_amount_algos=100.0
    )
    print(f"   ✅ Credit tier: {credit_result['credit_tier']}")
    print(f"   📈 Credit score: {credit_result['credit_score']}/100")
    print(f"   🎯 Risk category: {credit_result['risk_category']}")

    # Test liquidity matching
    print("\n3. Matching liquidity requirements...")
    match_result = match_liquidity_requirements(
        loan_request={"amount_algos": 100.0, "max_interest_rate": 8.0, "duration_days": 30},
        available_lenders=lenders_result['available_lenders'],
        borrower_assessment=credit_result
    )
    print(f"   ✅ Matches found: {match_result['total_matches']}")
    print(f"   📊 Matching quality: {match_result['matching_quality']}")
    if match_result['best_match']:
        print(f"   🏆 Best match: {match_result['best_match']['name']} (Score: {match_result['best_match']['match_score']})")


def demo_execution_tools():
    """Demo execution agent tools"""
    print("\n⚡ Execution Agent Tools Demo")
    print("=" * 50)

    # Test transaction preparation
    print("1. Preparing transaction group...")
    tx_result = prepare_transaction_group(
        borrower_address="BORROWER_ADDRESS_TEST_DEMO_1234567890ABCDEFGHIJ",
        lender_address="LENDER_ADDRESS_TEST_DEMO_1234567890ABCDEFGHIJK",
        loan_amount_algos=100.0,
        collateral_amount_algos=130.0,
        interest_rate_percent=7.5,
        duration_days=30
    )
    print(f"   ✅ Transactions prepared: {len(tx_result['transaction_group']['transactions'])}")
    print(f"   🆔 Group ID: {tx_result['transaction_group']['group_id']}")
    print(f"   ⏱️  Estimated time: {tx_result['transaction_group']['timeline']['execution_time']}")

    # Test execution validation
    print("\n2. Validating execution requirements...")
    validation_result = validate_execution_requirements(
        borrower_address="BORROWER_ADDRESS_TEST_DEMO_1234567890ABCDEFGHIJ",
        lender_address="LENDER_ADDRESS_TEST_DEMO_1234567890ABCDEFGHIJK",
        loan_amount_algos=100.0,
        collateral_amount_algos=130.0,
        borrower_balance_algos=160.0,
        lender_balance_algos=120.0
    )
    print(f"   ✅ Execution readiness: {validation_result['execution_readiness']}")
    print(f"   📋 Requirements met: {len(validation_result['validation_results']['requirements_met'])}")
    if validation_result['validation_results']['can_execute']:
        print("   🟢 Ready for execution!")
    else:
        print("   🔴 Issues to resolve first")

    # Test cost estimation
    print("\n3. Estimating transaction costs...")
    cost_result = estimate_transaction_costs(
        transaction_group=tx_result['transaction_group'],
        network_congestion="low",
        priority_level="standard"
    )
    print(f"   ✅ Total cost: {cost_result['cost_summary']['total_cost_algos']} ALGO")
    print(f"   💰 Borrower pays: {cost_result['cost_summary']['borrower_portion_algos']} ALGO")
    print(f"   💰 Lender pays: {cost_result['cost_summary']['lender_portion_algos']} ALGO")


def demo_coordination_tools():
    """Demo coordination agent tools"""
    print("\n🎯 Coordination Agent Tools Demo")
    print("=" * 50)

    # Test MCP service health
    print("1. Checking MCP service health...")
    health_result = check_mcp_service_health()
    print(f"   ✅ Overall status: {health_result['overall_status']}")
    print(f"   🔗 Can proceed with lending: {health_result['can_proceed_with_lending']}")

    # Test borrower data retrieval
    print("\n2. Getting borrower data...")
    borrower_data = get_borrower_data(
        "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        include_transactions=True
    )
    if not borrower_data.get('error'):
        print(f"   ✅ Balance: {borrower_data['balance_data']['algo_balance']} ALGO")
        print(f"   📊 Transactions: {borrower_data['transaction_data']['total_transactions']}")
        print(f"   🎯 Risk level: {borrower_data['risk_indicators']['overall_risk']}")
    else:
        print(f"   ⚠️  Error: {borrower_data['error']}")

    # Test workflow coordination
    print("\n3. Coordinating complete workflow...")
    workflow_result = coordinate_lending_workflow(
        loan_request={
            "borrower_address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
            "amount_algos": 50.0,
            "duration_days": 30,
            "max_interest_rate": 8.5,
            "collateral_amount_algos": 65.0
        },
        borrower_data=borrower_data
    )

    if workflow_result.get('success'):
        coordination = workflow_result['workflow_coordination']
        print(f"   ✅ Workflow status: {coordination['status']}")
        print(f"   📋 Steps completed: {len(coordination['steps_completed'])}")
        if workflow_result.get('final_results'):
            final = workflow_result['final_results']
            print(f"   🎯 Loan approved: {final['loan_approved']}")
            if final['loan_approved']:
                print(f"   💰 Final rate: {final['final_terms']['interest_rate']}%")
    else:
        print(f"   ❌ Workflow failed: {workflow_result.get('error')}")


def main():
    """Main demo function"""
    print("🎯 ADK Lending Agents - Tool Functions Demo")
    print("Demonstrating ADK pattern implementation without requiring google-adk package")
    print("=" * 80)

    try:
        # Run all demos
        demo_negotiation_tools()
        demo_liquidity_tools()
        demo_execution_tools()
        demo_coordination_tools()

        print("\n" + "=" * 80)
        print("🎉 ADK Tools Demo Complete!")

        print("\n📊 Summary of Capabilities:")
        print("✅ Negotiation: Risk assessment, rate calculation, term optimization")
        print("✅ Liquidity: Lender discovery, creditworthiness, optimal matching")
        print("✅ Execution: Transaction preparation, validation, cost estimation")
        print("✅ Coordination: Workflow orchestration, MCP integration, data aggregation")

        print("\n🏗️  ADK Architecture Benefits:")
        print("• AI-native agent design with Gemini integration")
        print("• Modular tool-based approach for extensibility")
        print("• Sub-agent coordination for complex workflows")
        print("• Built-in error handling and validation")
        print("• Standardized patterns across all agents")

        print("\n🚀 Next Steps for Production:")
        print("1. Install google-adk package")
        print("2. Configure Gemini API credentials")
        print("3. Deploy MCP services (ports 8002, 3001)")
        print("4. Test with real Algorand network")
        print("5. Set up monitoring and observability")

        return 0

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)