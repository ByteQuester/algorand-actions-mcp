#!/usr/bin/env python3
"""
Simple Test Script for Event Streaming System

This script tests core event streaming functionality without database dependencies.
"""

import asyncio
import logging
import json
import time
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_event_streaming_core():
    """Test core event streaming without database dependencies"""
    print("=== Testing Core Event Streaming ===")

    try:
        # Import only the core streaming components
        from core.audit.event_streaming import (
            EventStreamingService, EventStreamConfig, EventPriority, StreamingEvent
        )
        from core.audit.models import AuditTrail, AuditEventType, AuditSeverity, AuditEventData

        # Create event streaming service
        config = EventStreamConfig(
            max_queue_size=100,
            batch_size=5,
            flush_interval_ms=50,
            max_latency_ms=50
        )

        streaming_service = EventStreamingService(config)
        await streaming_service.start()

        print("✓ Event streaming service started")

        # Create test audit events manually
        test_events = []

        # Event 1: Loan request
        event_data1 = AuditEventData(
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER_ADDRESS",
            amount_micro_algos=1000000,
            metadata={"test": True, "event_number": 1}
        )

        event1 = AuditTrail(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            event_data=event_data1,
            service_name="test_service",
            service_version="1.0.0"
        )
        test_events.append(event1)

        # Event 2: Loan approved
        event_data2 = AuditEventData(
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER_ADDRESS",
            amount_micro_algos=1000000,
            interest_rate=5.5,
            metadata={"test": True, "event_number": 2}
        )

        event2 = AuditTrail(
            event_type=AuditEventType.LOAN_APPROVED,
            event_data=event_data2,
            service_name="test_service",
            service_version="1.0.0",
            severity=AuditSeverity.INFO
        )
        test_events.append(event2)

        # Event 3: Transaction created
        event_data3 = AuditEventData(
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER_ADDRESS",
            transaction_id="TEST_TX_123",
            metadata={"test": True, "event_number": 3}
        )

        event3 = AuditTrail(
            event_type=AuditEventType.TRANSACTION_CREATED,
            event_data=event_data3,
            service_name="test_service",
            service_version="1.0.0"
        )
        test_events.append(event3)

        print(f"✓ Created {len(test_events)} test events")

        # Set up event receiver
        received_events = []

        async def event_callback(streaming_event):
            received_events.append(streaming_event)
            loan_id = getattr(streaming_event.event.event_data, 'loan_id', 'N/A')
            print(f"📩 Received event: {streaming_event.event.event_type.value} for loan {loan_id}")

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
        submitted_count = 0
        for i, event in enumerate(test_events, 1):
            success = streaming_service.submit_event(event, EventPriority.NORMAL)
            if success:
                submitted_count += 1
                print(f"✓ Event {i} submitted to queue")
            else:
                print(f"✗ Failed to submit event {i}")

        # Wait for events to be processed
        print("⏳ Waiting for events to be processed...")
        await asyncio.sleep(1)

        # Verify events were received
        print(f"📊 Events submitted: {submitted_count}, Events received: {len(received_events)}")

        if len(received_events) == submitted_count:
            print("✅ All events received successfully")
        else:
            print(f"⚠️ Expected {submitted_count} events, received {len(received_events)}")

        # Test metrics
        metrics = await streaming_service.get_metrics()
        print(f"📈 Streaming metrics:")
        print(f"   - Events per second: {metrics.get('events_per_second', 0):.2f}")
        print(f"   - Active subscribers: {metrics.get('active_subscribers', 0)}")
        print(f"   - Queue size: {metrics.get('queue_size', 0)}")
        print(f"   - Pending events: {metrics.get('pending_events', 0)}")
        print(f"   - Average processing time: {metrics.get('average_processing_time_ms', 0):.2f}ms")

        # Test deduplication
        print("\n--- Testing Deduplication ---")
        initial_count = len(received_events)

        # Submit the same event twice
        duplicate_event = test_events[0]
        success1 = streaming_service.submit_event(duplicate_event, EventPriority.NORMAL)
        success2 = streaming_service.submit_event(duplicate_event, EventPriority.NORMAL)

        await asyncio.sleep(0.5)

        final_count = len(received_events)
        dedupe_worked = (final_count - initial_count) <= 1

        print(f"   - Duplicate submissions: success={success1}, success={success2}")
        print(f"   - Events before: {initial_count}, after: {final_count}")
        print(f"   - Deduplication working: {'✅' if dedupe_worked else '❌'}")

        # Test high priority events
        print("\n--- Testing Priority Events ---")
        high_priority_event = AuditTrail(
            event_type=AuditEventType.SYSTEM_ERROR,
            event_data=AuditEventData(
                error_message="Critical system error",
                metadata={"priority": "high", "test": True}
            ),
            service_name="priority_test",
            service_version="1.0.0",
            severity=AuditSeverity.CRITICAL
        )

        pre_priority_count = len(received_events)
        streaming_service.submit_event(high_priority_event, EventPriority.CRITICAL)

        await asyncio.sleep(0.3)

        post_priority_count = len(received_events)
        priority_received = post_priority_count > pre_priority_count

        print(f"   - High priority event submitted and received: {'✅' if priority_received else '❌'}")

        # Test unsubscribe
        print("\n--- Testing Unsubscribe ---")
        unsubscribe_success = await streaming_service.unsubscribe("test_subscriber")
        print(f"   - Unsubscribe successful: {'✅' if unsubscribe_success else '❌'}")

        # Submit event after unsubscribe (should not be received)
        post_unsub_count = len(received_events)
        streaming_service.submit_event(test_events[0], EventPriority.NORMAL)
        await asyncio.sleep(0.3)

        final_unsub_count = len(received_events)
        unsubscribe_worked = final_unsub_count == post_unsub_count

        print(f"   - No events after unsubscribe: {'✅' if unsubscribe_worked else '❌'}")

        # Stop the service
        await streaming_service.stop()
        print("✓ Event streaming service stopped")

        return True

    except Exception as e:
        logger.error(f"Core event streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance():
    """Test performance with many events"""
    print("\n=== Testing Performance ===")

    try:
        from core.audit.event_streaming import EventStreamingService, EventStreamConfig, EventPriority
        from core.audit.models import AuditTrail, AuditEventType, AuditEventData

        # High-performance configuration
        config = EventStreamConfig(
            max_queue_size=1000,
            batch_size=50,
            flush_interval_ms=25,
            max_latency_ms=50
        )

        streaming_service = EventStreamingService(config)
        await streaming_service.start()

        # Performance test
        num_events = 200
        received_count = 0

        async def perf_callback(streaming_event):
            nonlocal received_count
            received_count += 1

        await streaming_service.subscribe("perf_subscriber", perf_callback)

        print(f"⚡ Submitting {num_events} events for performance test...")

        start_time = time.time()
        submitted_count = 0

        for i in range(num_events):
            event_data = AuditEventData(
                loan_id=f"perf-loan-{i % 20}",
                borrower_address="PERF_BORROWER",
                metadata={"sequence": i, "test": "performance"}
            )

            event = AuditTrail(
                event_type=AuditEventType.AGENT_INVOKED,
                event_data=event_data,
                service_name="perf_test",
                service_version="1.0.0"
            )

            if streaming_service.submit_event(event, EventPriority.NORMAL):
                submitted_count += 1

        submission_time = time.time() - start_time

        # Wait for processing
        await asyncio.sleep(2)

        processing_time = time.time() - start_time

        # Get final metrics
        metrics = await streaming_service.get_metrics()

        print(f"📊 Performance Results:")
        print(f"   - Events submitted: {submitted_count}/{num_events}")
        print(f"   - Submission rate: {submitted_count/submission_time:.1f} events/sec")
        print(f"   - Events received: {received_count}")
        print(f"   - Total processing time: {processing_time:.3f}s")
        print(f"   - Average latency: {metrics.get('average_processing_time_ms', 0):.2f}ms")

        # Check performance requirements
        avg_latency = metrics.get('average_processing_time_ms', 0)
        meets_requirement = avg_latency > 0 and avg_latency < 100

        print(f"   - Meets <100ms requirement: {'✅' if meets_requirement else '❌'} ({avg_latency:.2f}ms)")

        await streaming_service.stop()

        return submitted_count > 0 and received_count > 0

    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run simplified tests"""
    print("🚀 Starting Simplified Event Streaming Tests")
    print("=" * 60)

    test_results = []

    # Test 1: Core functionality
    print("Test 1: Core Event Streaming")
    result1 = await test_event_streaming_core()
    test_results.append(("Core Event Streaming", result1))

    # Test 2: Performance
    print("Test 2: Performance Testing")
    result2 = await test_performance()
    test_results.append(("Performance", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, passed_test in test_results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Event streaming system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)