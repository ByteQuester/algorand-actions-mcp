#!/usr/bin/env python3
"""
Test script for Audit Trail API

Basic functionality test to verify the audit API endpoints work correctly.
"""

import asyncio
import httpx
from src.api.auth import create_demo_token

async def test_audit_api():
    """Test audit API endpoints"""

    # Generate test tokens
    admin_token = create_demo_token("admin")
    auditor_token = create_demo_token("auditor")

    print("Generated test tokens:")
    print(f"Admin token: {admin_token[:50]}...")
    print(f"Auditor token: {auditor_token[:50]}...")

    base_url = "http://localhost:8003"
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with httpx.AsyncClient() as client:

        # Test 1: Health Check
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{base_url}/api/v1/audit/health")
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"Service status: {health_data.get('status', 'unknown')}")
        except Exception as e:
            print(f"Health check failed: {e}")

        # Test 2: Metrics (Admin only)
        print("\n2. Testing metrics endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/audit/metrics", headers=headers)
            print(f"Metrics status: {response.status_code}")
            if response.status_code == 200:
                metrics_data = response.json()
                print(f"Metrics retrieved successfully")
        except Exception as e:
            print(f"Metrics test failed: {e}")

        # Test 3: Session Timeline (will fail without real data but should show proper error handling)
        print("\n3. Testing session timeline endpoint...")
        try:
            test_loan_id = "test-loan-123"
            response = await client.get(f"{base_url}/api/v1/audit/session/{test_loan_id}", headers=headers)
            print(f"Session timeline status: {response.status_code}")
            if response.status_code != 200:
                error_data = response.json()
                print(f"Expected error (no data): {error_data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"Session timeline test failed: {e}")

        # Test 4: Decision Breakdown
        print("\n4. Testing decision breakdown endpoint...")
        try:
            test_loan_id = "test-loan-123"
            response = await client.get(f"{base_url}/api/v1/audit/decisions/{test_loan_id}", headers=headers)
            print(f"Decision breakdown status: {response.status_code}")
            if response.status_code != 200:
                error_data = response.json()
                print(f"Expected error (no data): {error_data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"Decision breakdown test failed: {e}")

        # Test 5: Tool Usage Analysis
        print("\n5. Testing tool usage analysis endpoint...")
        try:
            test_loan_id = "test-loan-123"
            response = await client.get(f"{base_url}/api/v1/audit/tools/{test_loan_id}", headers=headers)
            print(f"Tool usage analysis status: {response.status_code}")
            if response.status_code != 200:
                error_data = response.json()
                print(f"Expected error (no data): {error_data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"Tool usage analysis test failed: {e}")

        # Test 6: Search Functionality
        print("\n6. Testing search endpoint...")
        try:
            params = {"query": "test search", "limit": 10}
            response = await client.get(f"{base_url}/api/v1/audit/search", headers=headers, params=params)
            print(f"Search status: {response.status_code}")
            if response.status_code == 200:
                search_data = response.json()
                print(f"Search completed: {search_data.get('total_results', 0)} results")
        except Exception as e:
            print(f"Search test failed: {e}")

        # Test 7: Authorization Test (using auditor token)
        print("\n7. Testing authorization with auditor token...")
        try:
            auditor_headers = {"Authorization": f"Bearer {auditor_token}"}
            response = await client.get(f"{base_url}/api/v1/audit/metrics", headers=auditor_headers)
            print(f"Auditor metrics access status: {response.status_code}")
            if response.status_code == 200:
                print("Auditor has access to metrics")
            else:
                print("Auditor properly denied access to admin-only metrics")
        except Exception as e:
            print(f"Authorization test failed: {e}")

def main():
    """Run audit API tests"""
    print("=== Audit Trail API Test Suite ===")
    print("Note: This test expects the API server to be running on localhost:8003")
    print("Start the server with: python -m uvicorn src.api.server:app --reload --port 8003")
    print()

    try:
        asyncio.run(test_audit_api())
        print("\n=== Test Suite Complete ===")
        print("Check the output above for any failures.")
        print("Some failures are expected if the database is not properly initialized.")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest suite failed with error: {e}")

if __name__ == "__main__":
    main()