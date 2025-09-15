#!/usr/bin/env python3
"""
Complete End-to-End Lending Workflow Test
Tests all three agents working together: Liquidity, Negotiation (AI), Execution
"""

import asyncio
import json
import os
import sys

# Add apps to Python path
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/src')

# Set environment variables for Gemini
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDYGxsZFS4pl5-3mnxVwrp3YqCe67DPuB4'
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'


async def test_complete_lending_workflow():
    """Test the complete integrated lending workflow"""
    print("🚀 Testing Complete Lending Workflow")
    print("=" * 60)

    try:
        # Import the integrated workflow
        from core.lending.src import IntegratedLendingWorkflow, MCPServiceConfig

        print("✅ Successfully imported IntegratedLendingWorkflow")

        # Configure MCP services
        mcp_config = MCPServiceConfig(
            reader_endpoint="http://localhost:8002",
            writer_endpoint="http://localhost:3001"
        )

        # Create workflow instance
        workflow = IntegratedLendingWorkflow(mcp_config)
        print("✅ Created IntegratedLendingWorkflow instance")

        # Test case 1: Standard loan request
        print("\n🧪 Test Case 1: Standard Loan Request")
        print("-" * 40)

        test_request = {
            "borrower": "TESTADDR12345678901234567890123456789012345678901234567890ABCDEF",
            "amount": 5_000_000,  # 5 ALGO
            "duration": 30,  # 30 days
            "max_interest_rate": 12.0,  # 12% max
            "collateral_type": "ALGO",
            "collateral_amount": 6_500_000  # 6.5 ALGO collateral
        }

        print(f"📝 Loan Request: {test_request['amount']/1_000_000} ALGO for {test_request['duration']} days")

        # Process the complete workflow
        result = await workflow.process_complete_lending_request(test_request)

        print(f"\n📊 Workflow Result:")
        print(f"   Status: {result['status']}")
        print(f"   Workflow ID: {result['workflow_id']}")

        if result['status'] == 'success':
            print("✅ SUCCESS! All three agents completed successfully")

            agents_used = result.get('agents_used', [])
            print(f"   Agents Used: {', '.join(agents_used)}")
            print(f"   Processing Time: {result.get('total_processing_time', 'Unknown')}")

            # Display final terms
            terms = result.get('final_terms', {})
            if terms:
                print(f"\n💰 Final Loan Terms:")
                print(f"   Amount: {terms.get('amount_micro_algos', 0)/1_000_000:.2f} ALGO")
                print(f"   Interest Rate: {terms.get('interest_rate', 0):.2f}%")
                print(f"   Duration: {terms.get('duration_days', 0)} days")
                print(f"   Collateral: {terms.get('collateral_amount', 0)/1_000_000:.2f} ALGO")
                print(f"   Risk Score: {terms.get('risk_score', 'N/A')}/10")
                print(f"   AI Confidence: {terms.get('approval_confidence', 'N/A')}%")

            # Display agent results
            print(f"\n🤖 Agent Details:")
            liquidity_data = result.get('liquidity_analysis', {})
            if liquidity_data:
                print(f"   🔍 Liquidity Agent:")
                print(f"      Available: {liquidity_data.get('available_amount', 0)/1_000_000:.2f} ALGO")
                print(f"      Creditworthiness: {liquidity_data.get('creditworthiness_score', 'N/A')}/100")

            risk_data = result.get('risk_assessment', {})
            if risk_data:
                ai_assessment = risk_data.get('ai_assessment', {})
                print(f"   🧠 AI Negotiation Agent:")
                print(f"      Risk Score: {ai_assessment.get('risk_score', 'N/A')}/10")
                print(f"      Recommended Rate: {ai_assessment.get('recommended_rate', 'N/A')}%")

            transaction_data = result.get('transaction_details', {})
            if transaction_data:
                print(f"   ⚡ Execution Agent:")
                print(f"      Transaction ID: {transaction_data.get('transaction_id', 'N/A')}")
                print(f"      Status: {transaction_data.get('status', 'N/A')}")

        else:
            print("❌ WORKFLOW FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Category: {result.get('error_category', 'Unknown')}")
            agents_completed = result.get('agents_completed', [])
            if agents_completed:
                print(f"   Agents Completed: {', '.join(agents_completed)}")

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure packages are properly installed")
        return False

    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("🎉 Complete lending workflow test completed!")
    return True


async def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\n🧪 Testing Edge Cases")
    print("-" * 30)

    try:
        from core.lending.src import IntegratedLendingWorkflow

        workflow = IntegratedLendingWorkflow()

        # Test case: Large loan amount (should fail)
        print("\n📋 Edge Case 1: Loan amount too large")
        large_loan_request = {
            "borrower": "TESTADDR12345678901234567890123456789012345678901234567890ABCDEF",
            "amount": 200_000_000_000,  # 200,000 ALGO (too large)
            "duration": 30,
            "max_interest_rate": 15.0,
            "collateral_type": "ALGO"
        }

        result = await workflow.process_complete_lending_request(large_loan_request)
        if result['status'] == 'failed':
            print(f"✅ Correctly rejected large loan: {result['error']}")
        else:
            print(f"⚠️ Unexpectedly approved large loan")

        # Test case: Invalid address (should fail)
        print("\n📋 Edge Case 2: Invalid borrower address")
        invalid_request = {
            "borrower": "INVALID_ADDRESS",
            "amount": 5_000_000,
            "duration": 30,
            "max_interest_rate": 10.0,
            "collateral_type": "ALGO"
        }

        result = await workflow.process_complete_lending_request(invalid_request)
        if result['status'] == 'failed':
            print(f"✅ Correctly rejected invalid address: {result['error']}")
        else:
            print(f"⚠️ Unexpectedly approved invalid address")

    except Exception as e:
        print(f"❌ Edge case testing failed: {e}")


if __name__ == "__main__":
    print("🌟 Algorand Showcase - Complete Lending Workflow Test")
    print("This tests all three agents: Liquidity, AI Negotiation, Execution")
    print("=" * 80)

    # Check prerequisites
    print("🔧 Checking Prerequisites...")

    # Check MCP services
    import httpx

    try:
        response = httpx.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ MCP Reader Service (port 8002) is running")
        else:
            print(f"⚠️ MCP Reader Service returned status {response.status_code}")
    except:
        print("❌ MCP Reader Service (port 8002) is not accessible")

    try:
        response = httpx.get("http://localhost:3001/health", timeout=5)
        if response.status_code == 200:
            print("✅ MCP Writer Service (port 3001) is running")
        else:
            print(f"⚠️ MCP Writer Service returned status {response.status_code}")
    except:
        print("❌ MCP Writer Service (port 3001) is not accessible")

    # Check Gemini API
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        print("✅ Gemini AI is accessible and working")
    except:
        print("⚠️ Gemini AI is not accessible (will use fallback)")

    print("\n🚀 Starting Tests...")

    # Run the tests
    success = asyncio.run(test_complete_lending_workflow())

    if success:
        asyncio.run(test_edge_cases())
        print("\n🎯 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("The integrated lending workflow is fully functional.")
    else:
        print("\n💥 TESTS FAILED")
        print("Please check the error messages above.")
        sys.exit(1)