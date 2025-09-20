#!/usr/bin/env python3
"""
Direct Test for Event Streaming Components

Tests event streaming by importing components directly to avoid dependency issues.
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime, timezone

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_model_creation():
    """Test that we can create audit models"""
    print("=== Testing Model Creation ===")

    try:
        # Import models directly
        from core.audit.models import (
            AuditTrail, AuditEventType, AuditSeverity, AuditEventData
        )

        # Create event data
        event_data = AuditEventData(
            loan_id="test-loan-001",
            borrower_address="TEST_BORROWER",
            amount_micro_algos=1000000,
            metadata={"test": True}
        )

        # Create audit trail
        audit_event = AuditTrail(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            event_data=event_data,
            service_name="test_service",
            service_version="1.0.0",
            severity=AuditSeverity.INFO
        )

        print(f"✅ Created audit event: {audit_event.event_type.value}")
        print(f"   - Loan ID: {audit_event.event_data.loan_id}")
        print(f"   - Timestamp: {audit_event.timestamp}")
        print(f"   - Service: {audit_event.service_name}")

        # Test JSON serialization
        json_data = audit_event.to_json()
        print(f"✅ JSON serialization successful ({len(json_data)} chars)")

        # Test deserialization
        recovered_event = AuditTrail.from_json(json_data)
        print(f"✅ JSON deserialization successful")
        print(f"   - Event type matches: {recovered_event.event_type == audit_event.event_type}")
        print(f"   - Loan ID matches: {recovered_event.event_data.loan_id == audit_event.event_data.loan_id}")

        return True

    except Exception as e:
        logger.error(f"Model creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_event_streaming_standalone():
    """Test event streaming components in isolation"""
    print("\n=== Testing Event Streaming (Standalone) ===")

    try:
        # Import streaming components directly
        from core.audit.event_streaming import (
            EventStreamingService, EventStreamConfig, EventPriority,
            EventDeduplicator, EventMetrics, StreamingEvent
        )
        from core.audit.models import AuditTrail, AuditEventType, AuditEventData, AuditSeverity

        print("✅ Successfully imported event streaming components")

        # Test deduplicator
        print("\n--- Testing Deduplicator ---")
        deduplicator = EventDeduplicator(window_seconds=60, cache_size=1000)

        # Create test event
        event_data = AuditEventData(
            loan_id="dedup-test-001",
            borrower_address="TEST_BORROWER",
            metadata={"test": "deduplication"}
        )

        audit_event = AuditTrail(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            event_data=event_data,
            service_name="dedup_test",
            service_version="1.0.0"
        )

        streaming_event = StreamingEvent(
            id="test-001",
            event=audit_event,
            priority=EventPriority.NORMAL
        )

        # Test deduplication
        is_dup1 = deduplicator.is_duplicate(streaming_event)
        is_dup2 = deduplicator.is_duplicate(streaming_event)

        print(f"   - First check (should be False): {is_dup1}")
        print(f"   - Second check (should be True): {is_dup2}")
        print(f"   - Deduplication working: {'✅' if not is_dup1 and is_dup2 else '❌'}")

        # Test metrics
        print("\n--- Testing Metrics ---")
        metrics = EventMetrics(window_seconds=300)

        # Record some test metrics
        metrics.record_event_processed(50.0)
        metrics.record_event_processed(75.0)
        metrics.record_event_processed(25.0)
        metrics.record_event_dropped("test_reason")

        metrics_data = metrics.get_metrics()
        print(f"   - Events per second: {metrics_data['events_per_second']:.2f}")
        print(f"   - Average processing time: {metrics_data['average_processing_time_ms']:.2f}ms")
        print(f"   - Max processing time: {metrics_data['max_processing_time_ms']:.2f}ms")

        # Test event streaming service
        print("\n--- Testing Event Streaming Service ---")

        config = EventStreamConfig(
            max_queue_size=100,
            batch_size=10,
            flush_interval_ms=100
        )

        service = EventStreamingService(config)
        await service.start()
        print("✅ Event streaming service started")

        # Set up subscriber
        received_events = []

        async def test_callback(streaming_event):
            received_events.append(streaming_event)
            loan_id = getattr(streaming_event.event.event_data, 'loan_id', 'N/A')
            print(f"   📩 Received: {streaming_event.event.event_type.value} for loan {loan_id}")

        # Subscribe
        subscribe_success = await service.subscribe(
            subscriber_id="test_subscriber",
            callback=test_callback,
            filters={'min_severity': 'info'}
        )

        print(f"   - Subscription successful: {'✅' if subscribe_success else '❌'}")

        # Submit test events
        test_events = []

        for i in range(5):
            event_data = AuditEventData(
                loan_id=f"stream-test-{i:03d}",
                borrower_address="STREAM_TEST_BORROWER",
                amount_micro_algos=1000000 + (i * 100000),
                metadata={"test": True, "sequence": i}
            )

            event = AuditTrail(
                event_type=AuditEventType.AGENT_INVOKED,
                event_data=event_data,
                service_name="stream_test",
                service_version="1.0.0"
            )

            test_events.append(event)

        # Submit events
        submitted = 0
        for event in test_events:
            if service.submit_event(event, EventPriority.NORMAL):
                submitted += 1

        print(f"   - Events submitted: {submitted}/{len(test_events)}")

        # Wait for processing
        await asyncio.sleep(1.5)

        print(f"   - Events received: {len(received_events)}")
        print(f"   - All events processed: {'✅' if len(received_events) == submitted else '❌'}")

        # Test high priority event
        priority_event = AuditTrail(
            event_type=AuditEventType.SYSTEM_ERROR,
            event_data=AuditEventData(
                error_message="Test priority event",
                metadata={"priority": True}
            ),
            service_name="priority_test",
            service_version="1.0.0",
            severity=AuditSeverity.CRITICAL
        )

        pre_count = len(received_events)
        service.submit_event(priority_event, EventPriority.CRITICAL)
        await asyncio.sleep(0.5)
        post_count = len(received_events)

        print(f"   - Priority event received: {'✅' if post_count > pre_count else '❌'}")

        # Get metrics
        final_metrics = await service.get_metrics()
        print(f"   - Final metrics:")
        print(f"     * Events/sec: {final_metrics.get('events_per_second', 0):.2f}")
        print(f"     * Avg processing: {final_metrics.get('average_processing_time_ms', 0):.2f}ms")
        print(f"     * Queue size: {final_metrics.get('queue_size', 0)}")
        print(f"     * Active subscribers: {final_metrics.get('active_subscribers', 0)}")

        # Stop service
        await service.stop()
        print("✅ Event streaming service stopped")

        return len(received_events) > 0

    except Exception as e:
        logger.error(f"Event streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_scenario():
    """Test a complete integration scenario"""
    print("\n=== Testing Integration Scenario ===")

    try:
        from core.audit.event_streaming import EventStreamingService, EventStreamConfig
        from core.audit.models import AuditTrail, AuditEventType, AuditEventData, AuditSeverity

        # Simulate a loan application workflow
        service = EventStreamingService(EventStreamConfig())
        await service.start()

        workflow_events = []

        async def workflow_callback(streaming_event):
            workflow_events.append(streaming_event)
            event_type = streaming_event.event.event_type.value
            loan_id = getattr(streaming_event.event.event_data, 'loan_id', 'N/A')
            print(f"   🔄 Workflow event: {event_type} for loan {loan_id}")

        await service.subscribe("workflow_subscriber", workflow_callback)

        loan_id = "workflow-test-loan-001"
        borrower = "WORKFLOW_TEST_BORROWER"

        # Step 1: Loan request created
        request_event = AuditTrail(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            event_data=AuditEventData(
                loan_id=loan_id,
                borrower_address=borrower,
                amount_micro_algos=2000000,
                metadata={"step": "request_created"}
            ),
            service_name="lending_workflow",
            service_version="1.0.0"
        )

        # Step 2: Loan approved
        approval_event = AuditTrail(
            event_type=AuditEventType.LOAN_APPROVED,
            event_data=AuditEventData(
                loan_id=loan_id,
                borrower_address=borrower,
                amount_micro_algos=2000000,
                interest_rate=6.5,
                metadata={"step": "approved", "terms": "standard"}
            ),
            service_name="lending_workflow",
            service_version="1.0.0",
            severity=AuditSeverity.INFO
        )

        # Step 3: Transaction created
        transaction_event = AuditTrail(
            event_type=AuditEventType.TRANSACTION_CREATED,
            event_data=AuditEventData(
                loan_id=loan_id,
                borrower_address=borrower,
                transaction_id="workflow-tx-123",
                metadata={"step": "transaction_created", "type": "funding"}
            ),
            service_name="blockchain_service",
            service_version="1.0.0"
        )

        # Step 4: Transaction confirmed
        confirmation_event = AuditTrail(
            event_type=AuditEventType.TRANSACTION_CONFIRMED,
            event_data=AuditEventData(
                loan_id=loan_id,
                transaction_id="workflow-tx-123",
                metadata={"step": "confirmed", "block_height": 12345}
            ),
            service_name="blockchain_service",
            service_version="1.0.0"
        )

        # Submit workflow events with timing
        workflow_steps = [
            ("Request Created", request_event),
            ("Loan Approved", approval_event),
            ("Transaction Created", transaction_event),
            ("Transaction Confirmed", confirmation_event)
        ]

        print(f"   🚀 Starting workflow for loan {loan_id}")

        for step_name, event in workflow_steps:
            service.submit_event(event)
            print(f"   📝 {step_name}")
            await asyncio.sleep(0.2)  # Simulate processing time

        # Wait for all events to be processed
        await asyncio.sleep(1)

        print(f"   📊 Workflow completed:")
        print(f"     * Expected events: {len(workflow_steps)}")
        print(f"     * Received events: {len(workflow_events)}")
        print(f"     * Workflow successful: {'✅' if len(workflow_events) == len(workflow_steps) else '❌'}")

        await service.stop()

        return len(workflow_events) == len(workflow_steps)

    except Exception as e:
        logger.error(f"Integration scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all direct tests"""
    print("🚀 Starting Direct Event Streaming Component Tests")
    print("=" * 70)

    test_results = []

    # Test 1: Model creation
    print("Test 1: Model Creation and Serialization")
    result1 = test_model_creation()
    test_results.append(("Model Creation", result1))

    # Test 2: Event streaming
    print("\nTest 2: Event Streaming Service")
    result2 = await test_event_streaming_standalone()
    test_results.append(("Event Streaming", result2))

    # Test 3: Integration scenario
    print("\nTest 3: Integration Scenario")
    result3 = await test_integration_scenario()
    test_results.append(("Integration Scenario", result3))

    # Summary
    print("\n" + "=" * 70)
    print("📊 DIRECT TEST SUMMARY")
    print("=" * 70)

    passed = 0
    total = len(test_results)

    for test_name, passed_test in test_results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All direct tests passed!")
        print("✨ Event streaming system core functionality is working correctly")
        print("🔗 System is ready for integration with ADK and MCP services")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())

    if success:
        print("\n🚀 NEXT STEPS:")
        print("   1. Start the FastAPI server with: python src/api/server.py")
        print("   2. Connect to WebSocket endpoint: ws://localhost:8003/api/v1/events/stream/your-connection-id")
        print("   3. Use audit hooks in your application code")
        print("   4. Monitor real-time events through the streaming system")

    exit(0 if success else 1)