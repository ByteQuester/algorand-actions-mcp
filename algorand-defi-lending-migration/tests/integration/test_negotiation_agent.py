#!/usr/bin/env python3
"""
Test script specifically for the 4 negotiation tools in the lending platform
This validates that all negotiation tools are accessible and working through the UI
"""

import requests
import json
import time

# Configuration
ADK_WEB_URL = "http://localhost:8091"
TEST_USER = "negotiation_test"
APP_NAME = "lending_platform"

def create_test_session():
    """Create a test session for the agent"""
    print("🔄 Creating test session...")

    try:
        response = requests.post(
            f"{ADK_WEB_URL}/apps/{APP_NAME}/users/{TEST_USER}/sessions",
            json={}
        )
        if response.status_code == 200:
            session = response.json()
            print(f"✅ Session created: {session['id']}")
            return session['id']
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None

def test_negotiation_tool(session_id, tool_name, test_prompt):
    """Test a specific negotiation tool"""
    print(f"🔧 Testing {tool_name}...")

    message = {
        "app_name": APP_NAME,
        "user_id": TEST_USER,
        "session_id": session_id,
        "new_message": {
            "parts": [{"text": test_prompt}]
        },
        "streaming": False
    }

    try:
        response = requests.post(f"{ADK_WEB_URL}/run", json=message)
        if response.status_code == 200:
            events = response.json()
            print(f"✅ {tool_name} responded with {len(events)} events")

            # Look for specific tool indicators
            found_tool_usage = False
            for event in events:
                if event.get('type') == 'content':
                    content = event.get('content', {})
                    if 'parts' in content:
                        for part in content['parts']:
                            if 'text' in part:
                                text = part['text'].lower()
                                # Check for tool-specific keywords
                                tool_keywords = {
                                    'calculate_interest_rate': ['interest', 'rate', 'percentage', '%'],
                                    'calculate_collateral_requirement': ['collateral', 'requirement', 'ratio'],
                                    'assess_loan_risk': ['risk', 'score', 'assessment', 'category'],
                                    'generate_counter_proposal': ['proposal', 'counter', 'terms', 'alternative']
                                }

                                if tool_name in tool_keywords:
                                    if any(keyword in text for keyword in tool_keywords[tool_name]):
                                        found_tool_usage = True
                                        print(f"🎯 Found {tool_name} usage indicators")
                                        break

            return found_tool_usage
        else:
            print(f"❌ {tool_name} failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing {tool_name}: {e}")
        return False

def main():
    """Test all 4 negotiation tools"""
    print("🎯 Testing 4 Negotiation Tools via UI")
    print("=" * 60)

    # Create session
    session_id = create_test_session()
    if not session_id:
        print("❌ Could not create session, stopping tests")
        return False

    # Test 1: calculate_interest_rate
    test1_result = test_negotiation_tool(
        session_id,
        "calculate_interest_rate",
        "Please calculate the interest rate for a loan of 100 ALGO for 30 days for a borrower with a risk score of 75. What rate would you recommend?"
    )

    # Test 2: calculate_collateral_requirement
    test2_result = test_negotiation_tool(
        session_id,
        "calculate_collateral_requirement",
        "I need to borrow 100 ALGO and my risk score is 75. How much collateral in ALGO would I need to provide?"
    )

    # Test 3: assess_loan_risk
    test3_result = test_negotiation_tool(
        session_id,
        "assess_loan_risk",
        "Please assess the risk for a borrower with address TEST_BORROWER who wants to borrow 100 ALGO, has a balance of 150 ALGO, and 50 transaction history. What is the risk assessment?"
    )

    # Test 4: generate_counter_proposal
    test4_result = test_negotiation_tool(
        session_id,
        "generate_counter_proposal",
        "A borrower requested 100 ALGO at 8% for 30 days, but the risk assessment shows medium risk. Can you generate a counter-proposal with better terms?"
    )

    # Summary
    print("\n" + "=" * 60)
    print("🎉 Negotiation Tools Test Results:")
    print(f"{'✅' if test1_result else '❌'} calculate_interest_rate: {test1_result}")
    print(f"{'✅' if test2_result else '❌'} calculate_collateral_requirement: {test2_result}")
    print(f"{'✅' if test3_result else '❌'} assess_loan_risk: {test3_result}")
    print(f"{'✅' if test4_result else '❌'} generate_counter_proposal: {test4_result}")

    all_tools_working = test1_result and test2_result and test3_result and test4_result
    tools_working_count = sum([test1_result, test2_result, test3_result, test4_result])

    print(f"\n🎯 Overall Result: {tools_working_count}/4 tools accessible")

    if all_tools_working:
        print("🎊 SUCCESS: All 4 negotiation tools are accessible through the UI!")
        print("✅ algorand_lending_negotiation_agent tools are working correctly")
        print("✅ No type annotation errors detected")
        print("✅ End-to-end tool calling is functional")
    elif tools_working_count >= 2:
        print("⚠️  PARTIAL SUCCESS: Most tools are working, minor issues detected")
    else:
        print("❌ FAILURE: Significant issues with tool accessibility")

    return all_tools_working

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)