#!/usr/bin/env python3
"""
Demo ADK Lending Agents
Demonstrates ADK pattern implementation with mock ADK functionality
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Set up environment
os.environ.setdefault("GOOGLE_API_KEY", "AIzaSyDYGxsZFS4pl5-3mnxVwrp3YqCe67DPuB4")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

# Add paths for imports
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/adk-agents')

# Import mock ADK
from mock_adk import MockAgent, MockFunctionTool, MockAgentTool

# Import our actual tool functions
from negotiation.tools import calculate_interest_rate, assess_loan_risk
from liquidity.tools import find_available_lenders, assess_borrower_creditworthiness
from execution.tools import prepare_transaction_group, validate_execution_requirements
from coordination.tools import check_mcp_service_health, coordinate_lending_workflow


def create_demo_negotiation_agent() -> MockAgent:
    """Create demo negotiation agent using mock ADK"""
    return MockAgent(
        name="demo_negotiation_agent",
        model="gemini-2.5-flash",
        description="Demo negotiation agent for lending terms",
        instruction="You are a lending negotiation agent that assesses risk and calculates optimal loan terms.",
        tools=[
            MockFunctionTool(calculate_interest_rate),
            MockFunctionTool(assess_loan_risk)
        ],
        output_key="negotiated_terms"
    )


def create_demo_liquidity_agent() -> MockAgent:
    """Create demo liquidity agent using mock ADK"""
    return MockAgent(
        name="demo_liquidity_agent",
        model="gemini-2.5-flash",
        description="Demo liquidity agent for lender discovery",
        instruction="You are a liquidity agent that finds lenders and assesses creditworthiness.",
        tools=[
            MockFunctionTool(find_available_lenders),
            MockFunctionTool(assess_borrower_creditworthiness)
        ],
        output_key="liquidity_analysis"
    )


def create_demo_execution_agent() -> MockAgent:
    """Create demo execution agent using mock ADK"""
    return MockAgent(
        name="demo_execution_agent",
        model="gemini-2.5-flash",
        description="Demo execution agent for transaction preparation",
        instruction="You are an execution agent that prepares and validates blockchain transactions.",
        tools=[
            MockFunctionTool(prepare_transaction_group),
            MockFunctionTool(validate_execution_requirements)
        ],
        output_key="execution_plan"
    )


def create_demo_coordinator() -> MockAgent:
    """Create demo coordination agent using mock ADK"""
    # Create sub-agents
    negotiation_agent = create_demo_negotiation_agent()
    liquidity_agent = create_demo_liquidity_agent()
    execution_agent = create_demo_execution_agent()

    return MockAgent(
        name="demo_lending_coordinator",
        model="gemini-2.5-pro",
        description="Demo master coordinator for lending operations",
        instruction="You are the master coordinator that orchestrates the complete lending workflow.",
        sub_agents=[negotiation_agent, liquidity_agent, execution_agent],
        tools=[
            MockFunctionTool(check_mcp_service_health),
            MockFunctionTool(coordinate_lending_workflow),
            MockAgentTool(negotiation_agent),
            MockAgentTool(liquidity_agent),
            MockAgentTool(execution_agent)
        ],
        output_key="lending_workflow_result"
    )


async def demo_individual_agents():
    """Demonstrate individual agent capabilities"""
    print("🤖 Demonstrating Individual Agent Capabilities...")
    print("=" * 60)

    # Test negotiation agent
    print("Testing Negotiation Agent...")
    negotiation_agent = create_demo_negotiation_agent()

    negotiation_input = {
        "loan_request": {
            "borrower_address": "TEST_BORROWER",
            "amount_algos": 100.0,
            "duration_days": 30,
            "max_interest_rate": 9.0
        },
        "borrower_data": {
            "balance": 150.0,
            "transaction_history": {"total_transactions": 50}
        }
    }

    negotiation_result = await negotiation_agent.process(negotiation_input)
    print(f"✅ Negotiation result: {negotiation_result['negotiated_terms']['recommendation']}")

    # Test liquidity agent
    print("\nTesting Liquidity Agent...")
    liquidity_agent = create_demo_liquidity_agent()

    liquidity_input = {
        "loan_request": {
            "amount_algos": 100.0,
            "target_rate": 8.0
        },
        "borrower_profile": {
            "address": "TEST_BORROWER",
            "balance": 150.0
        }
    }

    liquidity_result = await liquidity_agent.process(liquidity_input)
    print(f"✅ Liquidity result: Found {liquidity_result['liquidity_analysis']['lenders_found']} lenders")

    # Test execution agent
    print("\nTesting Execution Agent...")
    execution_agent = create_demo_execution_agent()

    execution_input = {
        "loan_terms": {
            "borrower": "TEST_BORROWER",
            "lender": "TEST_LENDER",
            "amount": 100.0,
            "collateral": 130.0
        }
    }

    execution_result = await execution_agent.process(execution_input)
    print(f"✅ Execution result: {execution_result['execution_plan']['transactions_prepared']} transactions prepared")


async def demo_coordination_workflow():
    """Demonstrate complete workflow coordination"""
    print("\n🚀 Demonstrating Complete Workflow Coordination...")
    print("=" * 60)

    # Create coordinator
    coordinator = create_demo_coordinator()

    # Prepare loan request
    loan_request = {
        "borrower_address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        "amount_algos": 50.0,
        "duration_days": 30,
        "max_interest_rate": 8.5,
        "collateral_amount_algos": 65.0,
        "collateral_type": "ALGO"
    }

    print(f"Processing loan request for {loan_request['amount_algos']} ALGO...")

    # Process through coordinator
    workflow_result = await coordinator.process({"loan_request": loan_request})

    # Display results
    result_data = workflow_result["lending_workflow_result"]
    print(f"✅ Workflow Status: {result_data['workflow_status']}")
    print(f"📋 Steps Completed: {', '.join(result_data['steps_completed'])}")
    print(f"🎯 Loan Approved: {result_data['final_recommendation']['loan_approved']}")

    if result_data['final_recommendation']['loan_approved']:
        terms = result_data['final_recommendation']['terms']
        print(f"💰 Final Terms: {terms['amount']} ALGO at {terms['rate']}% for {terms['duration']} days")


def demo_tool_functions():
    """Demonstrate individual tool functions"""
    print("\n⚙️  Demonstrating Tool Functions...")
    print("=" * 60)

    # Test interest rate calculation
    print("Testing interest rate calculation...")
    rate_result = calculate_interest_rate(
        loan_amount_algos=100.0,
        duration_days=30,
        borrower_risk_score=75
    )
    print(f"✅ Calculated rate: {rate_result['suggested_interest_rate']}%")

    # Test lender discovery
    print("\nTesting lender discovery...")
    lenders_result = find_available_lenders(
        loan_amount_algos=100.0,
        target_interest_rate=8.0,
        duration_days=30
    )
    print(f"✅ Found {lenders_result['total_lenders_found']} lenders")

    # Test transaction preparation
    print("\nTesting transaction preparation...")
    tx_result = prepare_transaction_group(
        borrower_address="BORROWER_TEST",
        lender_address="LENDER_TEST",
        loan_amount_algos=100.0,
        collateral_amount_algos=130.0,
        interest_rate_percent=7.5,
        duration_days=30
    )
    print(f"✅ Prepared {len(tx_result['transaction_group']['transactions'])} transactions")

    # Test MCP health check
    print("\nTesting MCP service health...")
    health_result = check_mcp_service_health()
    print(f"✅ MCP services: {health_result['overall_status']}")


async def demo_adk_patterns():
    """Demonstrate ADK patterns and capabilities"""
    print("\n🎯 Demonstrating ADK Patterns...")
    print("=" * 60)

    coordinator = create_demo_coordinator()

    print(f"Agent Architecture:")
    print(f"  - Name: {coordinator.name}")
    print(f"  - Model: {coordinator.model}")
    print(f"  - Tools Available: {len(coordinator.tools)}")
    print(f"  - Sub-Agents: {len(coordinator.sub_agents)}")

    print(f"\nSub-Agent Details:")
    for sub_agent in coordinator.sub_agents:
        print(f"  - {sub_agent.name}: {len(sub_agent.tools)} tools")

    print(f"\nTool Integration:")
    for i, tool in enumerate(coordinator.tools[:3]):  # Show first 3 tools
        tool_name = getattr(tool, 'name', str(type(tool).__name__))
        print(f"  - Tool {i+1}: {tool_name}")


async def main():
    """Main demo runner"""
    print("🎯 ADK Lending Agents Demo")
    print("Demonstrating Google ADK patterns for Algorand lending")
    print("=" * 60)

    try:
        # Run demos
        await demo_individual_agents()
        await demo_coordination_workflow()
        demo_tool_functions()
        await demo_adk_patterns()

        print("\n" + "=" * 60)
        print("🎉 ADK Demo Complete!")
        print("\nKey Achievements:")
        print("✅ Created ADK agents with Google ADK patterns")
        print("✅ Integrated with existing MCP services")
        print("✅ Demonstrated multi-agent coordination")
        print("✅ Showed tool function integration")
        print("✅ Built alongside existing system (parallel approach)")

        print("\nNext Steps for Production:")
        print("📦 Install actual google-adk package")
        print("🔑 Configure Gemini API credentials")
        print("🚀 Deploy MCP services on ports 8002, 3001")
        print("🧪 Test with real Algorand addresses")
        print("📊 Set up monitoring and observability")

        return 0

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))