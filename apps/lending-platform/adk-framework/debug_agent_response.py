#!/usr/bin/env python3
"""
Debug script to see what the agent is actually responding with
"""

import requests
import json

# Configuration
ADK_WEB_URL = "http://localhost:8091"
TEST_USER = "debug_test"
APP_NAME = "lending_platform"

def debug_agent_response():
    """Debug what the agent is actually returning"""

    # Create session
    session_response = requests.post(
        f"{ADK_WEB_URL}/apps/{APP_NAME}/users/{TEST_USER}/sessions",
        json={}
    )
    session_id = session_response.json()['id']
    print(f"Session ID: {session_id}")

    # Test message
    message = {
        "app_name": APP_NAME,
        "user_id": TEST_USER,
        "session_id": session_id,
        "new_message": {
            "parts": [{"text": "Please use your calculate_interest_rate function to calculate the interest rate for a 100 ALGO loan for 30 days with borrower risk score 75."}]
        },
        "streaming": False
    }

    response = requests.post(f"{ADK_WEB_URL}/run", json=message)
    events = response.json()

    print(f"Response status: {response.status_code}")
    print(f"Number of events: {len(events)}")
    print("\nFull response:")
    print(json.dumps(events, indent=2))

if __name__ == "__main__":
    debug_agent_response()