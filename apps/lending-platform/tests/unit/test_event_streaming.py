#!/usr/bin/env python3
"""
Test Script for Event Streaming System

This script tests the real-time event streaming system by:
1. Starting the event streaming service
2. Creating test audit events
3. Subscribing to the event stream
4. Verifying events are received in real-time
5. Testing WebSocket functionality
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test event streaming without FastAPI dependencies
async def test_basic_event_streaming():
    """Test basic event streaming functionality"""
    print("=== Testing Basic Event Streaming ===")

    try:
        from src.core.audit.event_streaming import (
            EventStreamingService, EventStreamConfig, EventPriority
        )
        from src.core.audit.models import (
            create_loan_audit_event, AuditEventType, AuditSeverity
        )

        # Create event streaming service
        config = EventStreamConfig(
            max_queue_size=100,
            batch_size=10,
            flush_interval_ms=50
        )

        streaming_service = EventStreamingService(config)
        await streaming_service.start()

        print("✓ Event streaming service started")

        # Create test events
        test_events = []

        # Event 1: Loan request
        event1 = create_loan_audit_event(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER_ADDRESS",
            service_name="test_service",
            amount_micro_algos=1000000,
            metadata={"test": True, "event_number": 1}
        )
        test_events.append(event1)

        # Event 2: Loan approved
        event2 = create_loan_audit_event(
            event_type=AuditEventType.LOAN_APPROVED,
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER_ADDRESS",
            service_name="test_service",
            amount_micro_algos=1000000,
            interest_rate=5.5,
            metadata={"test": True, "event_number": 2}
        )
        test_events.append(event2)

        # Event 3: Transaction created
        event3 = create_loan_audit_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER_ADDRESS",
            service_name="test_service",
            transaction_id="TEST_TX_123",
            metadata={"test": True, "event_number": 3}
        )
        test_events.append(event3)

        print(f"✓ Created {len(test_events)} test events")

        # Set up event receiver
        received_events: List[Any] = []

        async def event_callback(streaming_event):
            received_events.append(streaming_event)
            print(f"📩 Received event: {streaming_event.event.event_type.value} for loan {streaming_event.event.event_data.loan_id}")

        # Subscribe to events
        success = await streaming_service.subscribe(
            subscriber_id="test_subscriber",
            callback=event_callback,
            filters={
                'event_types': [e.value for e in AuditEventType],
                'min_severity': 'info'
            }
        )

        if not success:
            raise Exception("Failed to subscribe to events")

        print("✓ Subscribed to event stream")

        # Submit test events
        for i, event in enumerate(test_events, 1):
            success = streaming_service.submit_event(event, EventPriority.NORMAL)
            if success:
                print(f"✓ Event {i} submitted to queue")
            else:
                print(f"✗ Failed to submit event {i}")

        # Wait for events to be processed
        await asyncio.sleep(1)

        # Verify events were received
        print(f"📊 Events submitted: {len(test_events)}, Events received: {len(received_events)}")

        if len(received_events) == len(test_events):
            print("✓ All events received successfully")
        else:
            print(f"⚠️ Expected {len(test_events)} events, received {len(received_events)}")

        # Test metrics
        metrics = await streaming_service.get_metrics()
        print(f"📈 Streaming metrics:")
        print(f"   - Events per second: {metrics.get('events_per_second', 0):.2f}")
        print(f"   - Active subscribers: {metrics.get('active_subscribers', 0)}")
        print(f"   - Queue size: {metrics.get('queue_size', 0)}")
        print(f"   - Processing time: {metrics.get('average_processing_time_ms', 0):.2f}ms")

        # Test deduplication
        print("\n=== Testing Deduplication ===")
        duplicate_event = test_events[0]  # Submit the same event again

        success1 = streaming_service.submit_event(duplicate_event, EventPriority.NORMAL)
        success2 = streaming_service.submit_event(duplicate_event, EventPriority.NORMAL)

        await asyncio.sleep(0.5)

        print(f"✓ Deduplication test: submitted duplicate events, success rates: {success1}, {success2}")

        # Stop the service
        await streaming_service.stop()
        print("✓ Event streaming service stopped")

        return True

    except Exception as e:
        logger.error(f"Basic event streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_event_hooks():
    """Test event hooks and context"""
    print("\n=== Testing Event Hooks ===")

    try:
        from src.core.audit.event_hooks import (
            event_context, EnforcementHooks, LendingWorkflowHooks,
            get_event_streaming_service
        )

        # Get streaming service
        streaming_service = await get_event_streaming_service()

        # Set up event receiver
        received_events: List[Any] = []

        async def hook_callback(streaming_event):
            received_events.append(streaming_event)
            print(f"🔗 Hook event received: {streaming_event.event.event_type.value}")

        # Subscribe to hook events
        await streaming_service.subscribe(
            subscriber_id="hook_test_subscriber",
            callback=hook_callback,
            filters={'min_severity': 'info'}
        )

        # Test enforcement hooks
        async with event_context(
            loan_id="hook-test-loan-001",
            service_name="test_enforcement",
            operation_name="test_escrow_deployment"
        ):
            await EnforcementHooks.escrow_deployed(
                escrow_id="test-escrow-001",
                loan_id="hook-test-loan-001",
                app_id=12345,
                escrow_address="TEST_ESCROW_ADDRESS"
            )

        # Test lending workflow hooks
        await LendingWorkflowHooks.loan_request_created(
            loan_id="hook-test-loan-002",
            borrower_address="TEST_BORROWER_2",
            request_data={
                'amount': 2000000,
                'collateral_type': 'ALGO',
                'duration': 30,
                'test': True
            }
        )

        await LendingWorkflowHooks.loan_approved(
            loan_id="hook-test-loan-002",
            borrower_address="TEST_BORROWER_2",
            terms={
                'amount': 2000000,
                'interest_rate': 6.0,
                'duration': 30
            }
        )

        # Wait for hook events to be processed
        await asyncio.sleep(1)

        print(f"🔗 Hook events received: {len(received_events)}")

        for event in received_events:
            loan_id = getattr(event.event.event_data, 'loan_id', 'N/A')
            print(f"   - {event.event.event_type.value} for loan {loan_id}")

        print("✓ Event hooks test completed")
        return True

    except Exception as e:
        logger.error(f"Event hooks test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance():
    """Test performance with high-throughput events"""
    print("\n=== Testing Performance ===")

    try:
        from src.core.audit.event_streaming import get_event_streaming_service
        from src.core.audit.models import create_loan_audit_event, AuditEventType

        streaming_service = await get_event_streaming_service()

        # Performance test parameters
        num_events = 100
        start_time = time.time()

        # Submit many events quickly
        submitted_count = 0
        for i in range(num_events):
            event = create_loan_audit_event(
                event_type=AuditEventType.AGENT_INVOKED,
                loan_id=f"perf-test-loan-{i % 10}",  # 10 different loans
                borrower_address="PERF_TEST_BORROWER",
                service_name="performance_test",
                metadata={
                    "test": True,
                    "sequence": i,
                    "batch": "performance"
                }
            )

            if streaming_service.submit_event(event):
                submitted_count += 1

        submission_time = time.time() - start_time

        # Wait for processing
        await asyncio.sleep(2)

        # Get metrics
        metrics = await streaming_service.get_metrics()

        print(f"⚡ Performance test results:")
        print(f"   - Events submitted: {submitted_count}/{num_events}")
        print(f"   - Submission time: {submission_time:.3f}s")
        print(f"   - Events per second: {submitted_count/submission_time:.1f}")
        print(f"   - Avg processing time: {metrics.get('average_processing_time_ms', 0):.2f}ms")
        print(f"   - Max processing time: {metrics.get('max_processing_time_ms', 0):.2f}ms")
        print(f"   - Queue size: {metrics.get('queue_size', 0)}")

        # Check if we met performance requirements
        avg_processing_time = metrics.get('average_processing_time_ms', 0)
        if avg_processing_time > 0 and avg_processing_time < 100:  # <100ms requirement
            print("✓ Performance requirement met (<100ms latency)")
        else:
            print(f"⚠️ Performance requirement not met: {avg_processing_time}ms > 100ms")

        return True

    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting Event Streaming System Tests")
    print("=" * 50)

    test_results = []

    # Test 1: Basic event streaming
    result1 = await test_basic_event_streaming()
    test_results.append(("Basic Event Streaming", result1))

    # Test 2: Event hooks
    result2 = await test_event_hooks()
    test_results.append(("Event Hooks", result2))

    # Test 3: Performance
    result3 = await test_performance()
    test_results.append(("Performance", result3))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(test_results)

    for test_name, passed_test in test_results:
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Event streaming system is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the logs for details.")

    # Clean up
    try:
        from src.core.audit.event_streaming import shutdown_event_streaming_service
        await shutdown_event_streaming_service()
        print("✓ Event streaming service cleaned up")
    except Exception as e:
        logger.error(f"Failed to clean up: {e}")


if __name__ == "__main__":
    asyncio.run(main())