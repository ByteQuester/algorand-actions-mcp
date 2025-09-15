#!/usr/bin/env python3
"""
Debug Agent Errors
Simple debug script to identify the specific errors causing HTTP 500s
"""

import json
import requests
import time


def test_simple_agent_call(agent_name: str) -> dict:
    """Test a simple agent call and capture detailed error info"""
    print(f"\n🔍 Testing {agent_name}")
    print("=" * 50)

    # Create session
    try:
        session_response = requests.post(
            "http://localhost:8091/apps/lending_platform/users/debug_user/sessions",
            json={"state": {"agent": agent_name}},
            timeout=10
        )

        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return {"status": "session_failed", "error": session_response.text}

        session_data = session_response.json()
        session_id = session_data["id"]
        print(f"✅ Session created: {session_id}")

        # Try a very simple request
        simple_prompt = "Hello, what can you help me with?"

        request_data = {
            "appName": "lending_platform",
            "userId": "debug_user",
            "sessionId": session_id,
            "newMessage": {
                "parts": [{"text": simple_prompt}],
                "role": "user"
            },
            "streaming": False
        }

        print(f"📤 Sending simple request: {simple_prompt}")

        # Make the agent request
        agent_response = requests.post(
            "http://localhost:8091/run",
            json=request_data,
            timeout=30
        )

        print(f"📥 Response status: {agent_response.status_code}")

        if agent_response.status_code == 200:
            result = agent_response.json()
            print(f"✅ Success! Response length: {len(str(result))}")

            # Look for any error messages in the response
            result_str = str(result).lower()
            error_indicators = [
                "loan_id: str = none",
                "already has a parent agent",
                "type annotation",
                "error",
                "exception",
                "traceback"
            ]

            found_errors = []
            for indicator in error_indicators:
                if indicator in result_str:
                    found_errors.append(indicator)

            if found_errors:
                print(f"⚠️  Error indicators found: {found_errors}")
                return {"status": "success_with_errors", "errors": found_errors, "response": result}
            else:
                print("✅ No error indicators found in response")
                return {"status": "success", "response": result}

        else:
            print(f"❌ HTTP Error: {agent_response.status_code}")
            error_text = agent_response.text
            print(f"Error details: {error_text[:500]}...")

            # Check for our specific errors in the 500 error
            if "loan_id: str = none" in error_text.lower():
                print("🎯 FOUND: Type annotation error (loan_id: str = None)")
            if "already has a parent agent" in error_text.lower():
                print("🎯 FOUND: Agent duplication error")

            return {
                "status": "http_error",
                "status_code": agent_response.status_code,
                "error": error_text
            }

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "exception", "error": str(e)}


def main():
    """Main debug function"""
    print("🔍 ADK AGENT ERROR DEBUG SESSION")
    print("=" * 60)

    agents_to_test = [
        "algorand_lending_liquidity_agent",
        "algorand_lending_negotiation_agent",
        "algorand_lending_execution_agent",
        "algorand_lending_coordinator"
    ]

    results = {}

    for agent_name in agents_to_test:
        results[agent_name] = test_simple_agent_call(agent_name)
        time.sleep(1)  # Small delay between tests

    # Summary
    print(f"\n{'='*60}")
    print("🎯 DEBUG SUMMARY")
    print(f"{'='*60}")

    success_count = 0
    error_count = 0
    specific_errors_found = []

    for agent_name, result in results.items():
        status = result["status"]

        if status == "success":
            print(f"✅ {agent_name}: SUCCESS")
            success_count += 1
        elif status == "success_with_errors":
            print(f"⚠️  {agent_name}: SUCCESS (with error indicators)")
            if "errors" in result:
                specific_errors_found.extend(result["errors"])
        else:
            print(f"❌ {agent_name}: FAILED ({status})")
            error_count += 1

            # Check for specific errors we're tracking
            if "error" in result:
                error_text = str(result["error"]).lower()
                if "loan_id: str = none" in error_text:
                    specific_errors_found.append("loan_id type annotation error")
                if "already has a parent agent" in error_text:
                    specific_errors_found.append("agent duplication error")

    print(f"\n📊 RESULTS:")
    print(f"   Success: {success_count}/{len(agents_to_test)}")
    print(f"   Failed: {error_count}/{len(agents_to_test)}")

    if specific_errors_found:
        print(f"\n🎯 SPECIFIC ERRORS DETECTED:")
        for error in set(specific_errors_found):
            print(f"   • {error}")

        if "loan_id type annotation error" in specific_errors_found:
            print("\n❌ TYPE ANNOTATION ERRORS NOT FIXED")
        if "agent duplication error" in specific_errors_found:
            print("\n❌ AGENT DUPLICATION ERRORS NOT FIXED")
    else:
        print(f"\n✅ NO SPECIFIC TARGET ERRORS DETECTED")
        print("   (loan_id type annotation and agent duplication errors appear to be fixed)")

    print(f"\n🔧 NEXT STEPS:")
    if error_count > 0:
        print("   1. Investigate the HTTP 500 errors in agent implementation")
        print("   2. Check agent initialization and tool loading")
        print("   3. Verify agent dependencies and imports")
    if success_count > 0:
        print("   4. Test successful agents with more complex requests")
        print("   5. Validate tool functionality on working agents")

    return error_count == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)