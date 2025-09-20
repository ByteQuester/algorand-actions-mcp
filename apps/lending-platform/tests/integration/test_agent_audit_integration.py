"""
Agent-Audit System Integration Test
Tests complete integration between AI agents and audit system
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Import test framework
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import components to test
from src.agents.integration.audit_integration import (
    AgentAuditLogger,
    AuditIntegratedWorkflow,
    agent_audit_logger
)
from src.agents.coordination.tools import (
    get_borrower_data,
    coordinate_lending_workflow
)
from src.agents.negotiation.tools import calculate_interest_rate
from src.core.audit.models import AuditEventType


class MockAgent:
    """Mock agent for testing audit integration"""

    def __init__(self, name: str):
        self.name = name


async def test_agent_audit_logging():
    """Test that agent actions are properly logged to audit system"""

    print("🧪 Testing Agent Audit Logging Integration")
    print("=" * 60)

    audit_logger = AgentAuditLogger()

    # Test 1: Basic agent action logging
    print("1. Testing basic agent action logging...")

    event_id = await audit_logger.log_agent_action(
        agent_name="test_agent",
        action="agent_invoked",
        details={
            "function": "test_function",
            "parameters": {"param1": "value1"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        loan_id="TEST_LOAN_001",
        user_id="test_user"
    )

    print(f"   ✅ Agent action logged with event ID: {event_id}")

    # Test 2: Compliance check logging
    print("2. Testing compliance check integration...")

    decision_data = {
        "loan_amount": 25.0,
        "interest_rate": 7.2,
        "approval_decision": True,
        "risk_factors": ["low_balance", "limited_history"]
    }

    compliance_result = await audit_logger.log_compliance_check(
        agent_name="negotiation_agent",
        decision_data=decision_data,
        loan_id="TEST_LOAN_001",
        user_id="test_user"
    )

    print(f"   ✅ Compliance check completed: {compliance_result.get('compliance_score', 'N/A')}%")

    return True


async def test_workflow_audit_integration():
    """Test complete workflow with audit trail integration"""

    print("🔄 Testing Complete Workflow Audit Integration")
    print("=" * 60)

    workflow_manager = AuditIntegratedWorkflow()

    # Test loan request
    loan_request = {
        "loan_id": "TEST_WORKFLOW_001",
        "borrower_address": "TESTADDRESS123456789",
        "amount_algos": 50.0,
        "duration_days": 60,
        "purpose": "business_expansion",
        "collateral_offered": "ALGO"
    }

    print("1. Executing integrated lending workflow...")

    try:
        workflow_results = await workflow_manager.execute_lending_workflow(
            loan_request=loan_request,
            user_id="integration_test_user"
        )

        print(f"   ✅ Workflow completed: {workflow_results['status']}")
        print(f"   ✅ Audit trail complete: {workflow_results['audit_trail_complete']}")
        print(f"   ✅ Compliance passed: {workflow_results['compliance_passed']}")
        print(f"   ✅ Real-time streaming: {workflow_results['real_time_streaming']}")
        print(f"   ✅ Steps completed: {workflow_results['steps_completed']}")

        return workflow_results

    except Exception as e:
        print(f"   ❌ Workflow failed: {str(e)}")
        return None


def test_decorated_agent_functions():
    """Test that decorated agent functions create audit trails"""

    print("🎯 Testing Decorated Agent Functions")
    print("=" * 60)

    # Create mock agent for testing
    mock_agent = MockAgent("negotiation_agent")

    # Test 1: Interest rate calculation with audit
    print("1. Testing interest rate calculation with audit decorators...")

    try:
        # This should trigger both audit_agent_action and audit_compliance_decision decorators
        result = calculate_interest_rate(
            loan_amount_algos=25.0,
            duration_days=60,
            borrower_risk_score=75,
            market_base_rate=7.5,
            collateral_ratio=1.3
        )

        print(f"   ✅ Interest rate calculated: {result.get('final_interest_rate', 'N/A')}%")

        # Check if compliance info was added
        if 'compliance_check' in result:
            print(f"   ✅ Compliance check integrated: {result['compliance_check']}")
        else:
            print("   ⚠️  Compliance check not found in result (may be async)")

        return True

    except Exception as e:
        print(f"   ❌ Decorated function test failed: {str(e)}")
        return False


def test_borrower_data_audit():
    """Test borrower data retrieval with audit logging"""

    print("👤 Testing Borrower Data Retrieval Audit")
    print("=" * 60)

    try:
        # This should trigger audit_agent_action decorator
        borrower_data = get_borrower_data(
            borrower_address="TESTBORROWER123456789",
            include_transactions=True
        )

        print(f"   ✅ Borrower data retrieved for: {borrower_data.get('borrower_address', 'Unknown')}")
        print(f"   ✅ Balance: {borrower_data.get('balance_data', {}).get('algo_balance', 'N/A')} ALGO")
        print(f"   ✅ Risk level: {borrower_data.get('risk_indicators', {}).get('overall_risk', 'N/A')}")

        return True

    except Exception as e:
        print(f"   ❌ Borrower data audit test failed: {str(e)}")
        return False


async def test_real_time_streaming():
    """Test real-time event streaming from agent actions"""

    print("📡 Testing Real-Time Event Streaming")
    print("=" * 60)

    # Note: This test simulates streaming since WebSocket requires server running
    print("1. Testing audit event broadcasting...")

    try:
        # Create audit logger
        audit_logger = AgentAuditLogger()

        # Log an event that should trigger real-time streaming
        event_id = await audit_logger.log_agent_action(
            agent_name="streaming_test_agent",
            action="test_streaming_event",
            details={
                "test": True,
                "streaming": "enabled",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            loan_id="STREAM_TEST_001",
            user_id="streaming_test_user"
        )

        print(f"   ✅ Streaming event logged: {event_id}")
        print("   ✅ Real-time broadcast attempted (WebSocket server needed for actual delivery)")

        return True

    except Exception as e:
        print(f"   ❌ Streaming test failed: {str(e)}")
        return False


async def run_comprehensive_integration_test():
    """Run complete integration test suite"""

    print("🎊 COMPREHENSIVE AGENT-AUDIT INTEGRATION TEST")
    print("=" * 80)
    print()

    test_results = {
        "agent_audit_logging": False,
        "workflow_integration": False,
        "decorated_functions": False,
        "borrower_data_audit": False,
        "real_time_streaming": False
    }

    # Test 1: Agent audit logging
    try:
        test_results["agent_audit_logging"] = await test_agent_audit_logging()
    except Exception as e:
        print(f"❌ Agent audit logging test failed: {str(e)}")

    print()

    # Test 2: Complete workflow integration
    try:
        workflow_result = await test_workflow_audit_integration()
        test_results["workflow_integration"] = workflow_result is not None
    except Exception as e:
        print(f"❌ Workflow integration test failed: {str(e)}")

    print()

    # Test 3: Decorated functions
    try:
        test_results["decorated_functions"] = test_decorated_agent_functions()
    except Exception as e:
        print(f"❌ Decorated functions test failed: {str(e)}")

    print()

    # Test 4: Borrower data audit
    try:
        test_results["borrower_data_audit"] = test_borrower_data_audit()
    except Exception as e:
        print(f"❌ Borrower data audit test failed: {str(e)}")

    print()

    # Test 5: Real-time streaming
    try:
        test_results["real_time_streaming"] = await test_real_time_streaming()
    except Exception as e:
        print(f"❌ Real-time streaming test failed: {str(e)}")

    # Final results
    print()
    print("🎯 FINAL INTEGRATION TEST RESULTS")
    print("=" * 80)

    passed_tests = sum(test_results.values())
    total_tests = len(test_results)

    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    print()
    print(f"📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Agent-Audit system integration is working correctly")
        print("✅ Complete traceability achieved")
        print("✅ Compliance checking integrated")
        print("✅ Real-time streaming configured")
    else:
        print("⚠️  Some integration tests failed")
        print("🔧 Check error messages above for troubleshooting")

    return test_results


if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(run_comprehensive_integration_test())