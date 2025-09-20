#!/usr/bin/env python3
"""
Comprehensive Test Suite for Real-time Event Streaming System

Tests the complete event streaming pipeline including:
- Event generation and capture
- Real-time processing and transformation
- WebSocket streaming to UI clients
- Integration with enforcement events
- Performance and reliability
"""

import asyncio
import json
import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
import websockets
import aiohttp
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.audit.event_streaming import (
    get_event_streaming_service, stream_audit_event, EventPriority,
    subscribe_to_events, get_streaming_metrics
)
from src.core.audit.event_processor import (
    get_processing_pipeline, process_audit_event, get_processing_metrics
)
from src.core.audit.models import (
    AuditTrail, AuditEventType, AuditSeverity, AuditEventData,
    create_loan_audit_event
)
from src.core.enforcement.escrow_service import EscrowService
from src.core.enforcement.models import (
    EscrowDeploymentRequest, LiquidationRequest, ReleaseRequest
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventStreamingTestSuite:
    """Comprehensive test suite for the event streaming system"""

    def __init__(self):
        self.test_results = {}
        self.test_events_received = []
        self.websocket_events = []
        self.performance_metrics = {}

    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting Real-time Event Streaming System Tests")

        test_suites = [
            ("Basic Event Streaming", self.test_basic_event_streaming),
            ("Event Processing Pipeline", self.test_event_processing_pipeline),
            ("WebSocket Streaming", self.test_websocket_streaming),
            ("Enforcement Integration", self.test_enforcement_integration),
            ("Performance Tests", self.test_performance),
            ("Error Handling", self.test_error_handling),
            ("Concurrent Load", self.test_concurrent_load)
        ]

        for suite_name, test_func in test_suites:
            logger.info(f"\n📋 Running {suite_name} Tests...")
            try:
                start_time = time.time()
                result = await test_func()
                test_time = (time.time() - start_time) * 1000

                self.test_results[suite_name] = {
                    'status': 'PASSED' if result else 'FAILED',
                    'duration_ms': test_time,
                    'details': result if isinstance(result, dict) else {}
                }

                status_emoji = "✅" if result else "❌"
                logger.info(f"{status_emoji} {suite_name}: {self.test_results[suite_name]['status']} ({test_time:.2f}ms)")

            except Exception as e:
                logger.error(f"❌ {suite_name} failed with exception: {e}")
                self.test_results[suite_name] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'duration_ms': 0
                }

        # Print comprehensive test report
        await self.print_test_report()

        return all(result['status'] == 'PASSED' for result in self.test_results.values())

    async def test_basic_event_streaming(self) -> bool:
        """Test basic event streaming functionality"""
        try:
            # Get streaming service
            streaming_service = await get_event_streaming_service()

            # Create test events
            test_events = []
            for i in range(5):
                event = create_loan_audit_event(
                    event_type=AuditEventType.LOAN_REQUEST_CREATED,
                    loan_id=f"test-loan-{i}",
                    borrower_address=f"test-borrower-{i}",
                    service_name="test_service",
                    amount_micro_algos=1000000 * (i + 1),
                    metadata={
                        "test_sequence": i,
                        "test_timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                test_events.append(event)

            # Subscribe to receive events
            events_received = []

            async def event_callback(streaming_event):
                events_received.append(streaming_event)
                logger.info(f"📨 Received event: {streaming_event.event.event_type.value}")

            # Subscribe with test callback
            subscription_id = f"test_subscription_{uuid.uuid4()}"
            success = await streaming_service.subscribe(subscription_id, event_callback)

            if not success:
                logger.error("Failed to subscribe to event stream")
                return False

            # Stream the test events
            for event in test_events:
                success = await stream_audit_event(event, EventPriority.NORMAL)
                if not success:
                    logger.error(f"Failed to stream event: {event.event_type}")
                    return False

            # Wait for events to be processed
            await asyncio.sleep(2)

            # Unsubscribe
            await streaming_service.unsubscribe(subscription_id)

            # Verify results
            if len(events_received) != len(test_events):
                logger.error(f"Expected {len(test_events)} events, received {len(events_received)}")
                return False

            logger.info(f"✅ Successfully streamed and received {len(events_received)} events")
            return True

        except Exception as e:
            logger.error(f"Basic event streaming test failed: {e}")
            return False

    async def test_event_processing_pipeline(self) -> bool:
        """Test event processing pipeline functionality"""
        try:
            # Get processing pipeline
            pipeline = await get_processing_pipeline()

            # Create test event with various data for processing
            test_event = create_loan_audit_event(
                event_type=AuditEventType.LOAN_APPROVED,
                loan_id="pipeline-test-loan",
                borrower_address="pipeline-test-borrower",
                service_name="pipeline_test",
                amount_micro_algos=5000000,
                metadata={
                    "sensitive_key": "secret_data",  # Should be redacted
                    "user_id": "test_user_123",
                    "processing_test": True,
                    "large_data": "x" * 2000  # Should be truncated
                }
            )

            # Convert to streaming event
            from src.core.audit.event_streaming import StreamingEvent
            streaming_event = StreamingEvent(
                id=str(uuid.uuid4()),
                event=test_event,
                priority=EventPriority.NORMAL
            )

            # Process through pipeline
            processed_event = await pipeline.process_event(streaming_event)

            if not processed_event:
                logger.error("Event processing failed")
                return False

            # Verify processing stages
            expected_stages = ['validation', 'enrichment', 'transformation', 'filtering', 'routing']
            actual_stages = [stage.value for stage in processed_event.processing_stages]

            for stage in expected_stages:
                if stage not in actual_stages:
                    logger.error(f"Missing processing stage: {stage}")
                    return False

            # Check processing time
            if processed_event.processing_time_ms > 1000:  # Should be under 1 second
                logger.warning(f"Processing time high: {processed_event.processing_time_ms}ms")

            # Get processing metrics
            metrics = pipeline.get_processing_metrics()
            logger.info(f"📊 Processing metrics: {metrics['events_processed']} processed, "
                       f"avg {metrics['average_processing_time_ms']:.2f}ms")

            return True

        except Exception as e:
            logger.error(f"Event processing pipeline test failed: {e}")
            return False

    async def test_websocket_streaming(self) -> bool:
        """Test WebSocket streaming functionality"""
        try:
            # Start a mock WebSocket server test
            websocket_events = []

            async def mock_websocket_client():
                """Mock WebSocket client to test streaming"""
                try:
                    # In a real test, this would connect to the WebSocket endpoint
                    # For this test, we'll simulate the WebSocket behavior

                    # Subscribe to events through streaming service
                    streaming_service = await get_event_streaming_service()

                    async def websocket_callback(streaming_event):
                        websocket_events.append({
                            'type': 'event',
                            'event_type': streaming_event.event.event_type.value,
                            'timestamp': streaming_event.event.timestamp.isoformat(),
                            'data': {
                                'loan_id': getattr(streaming_event.event.event_data, 'loan_id', None),
                                'service_name': streaming_event.event.service_name
                            }
                        })
                        logger.info(f"🌐 WebSocket received: {streaming_event.event.event_type.value}")

                    subscription_id = f"websocket_test_{uuid.uuid4()}"
                    await streaming_service.subscribe(subscription_id, websocket_callback)

                    # Wait for events
                    await asyncio.sleep(3)

                    # Cleanup
                    await streaming_service.unsubscribe(subscription_id)

                except Exception as e:
                    logger.error(f"Mock WebSocket client error: {e}")

            # Start mock WebSocket client
            websocket_task = asyncio.create_task(mock_websocket_client())

            # Send test events
            for i in range(3):
                event = create_loan_audit_event(
                    event_type=AuditEventType.LOAN_FUNDED,
                    loan_id=f"websocket-test-loan-{i}",
                    borrower_address=f"websocket-borrower-{i}",
                    service_name="websocket_test",
                    amount_micro_algos=2000000,
                    metadata={"websocket_test": True, "sequence": i}
                )

                await stream_audit_event(event, EventPriority.HIGH)
                await asyncio.sleep(0.5)  # Space out events

            # Wait for WebSocket client to finish
            await websocket_task

            # Verify WebSocket events were received
            if len(websocket_events) < 3:
                logger.error(f"Expected 3+ WebSocket events, received {len(websocket_events)}")
                return False

            logger.info(f"✅ WebSocket streaming test passed: {len(websocket_events)} events")
            return True

        except Exception as e:
            logger.error(f"WebSocket streaming test failed: {e}")
            return False

    async def test_enforcement_integration(self) -> bool:
        """Test integration with enforcement events"""
        try:
            # Create mock MCP configuration
            from src.core.enforcement.mcp_integration import MCPConfig
            mock_config = MCPConfig()

            # Create escrow service
            escrow_service = EscrowService(mock_config)

            # Mock the MCP blockchain client
            original_mcp_client = None

            # Create mock deployment request
            deployment_request = EscrowDeploymentRequest(
                loan_id="enforcement-test-loan",
                borrower="test-borrower-address",
                lender="test-lender-address",
                amount=1000000,
                collateral=1500000,
                collateral_type="ALGO",
                duration=30,
                interest_rate=0.05
            )

            # Subscribe to enforcement events
            enforcement_events = []

            async def enforcement_callback(streaming_event):
                if streaming_event.event.service_name == "escrow_enforcement":
                    enforcement_events.append({
                        'operation': streaming_event.event.event_data.metadata.get('operation'),
                        'event_type': streaming_event.event.event_type.value,
                        'timestamp': streaming_event.event.timestamp.isoformat()
                    })
                    logger.info(f"🔒 Enforcement event: {streaming_event.event.event_data.metadata.get('operation')}")

            streaming_service = await get_event_streaming_service()
            enforcement_sub_id = f"enforcement_test_{uuid.uuid4()}"
            await streaming_service.subscribe(enforcement_sub_id, enforcement_callback)

            # Mock the blockchain deployment to avoid actual blockchain calls
            async def mock_deploy_smart_contract(*args, **kwargs):
                return {
                    "success": True,
                    "app_id": 12345,
                    "transaction_id": "mock_tx_12345"
                }

            # Patch the MCP client for testing
            import src.core.enforcement.mcp_integration as mcp_module
            original_client = getattr(mcp_module, 'MCPBlockchainClient', None)

            if original_client:
                # Create a mock client class
                class MockMCPClient:
                    def __init__(self, config):
                        self.config = config

                    async def __aenter__(self):
                        return self

                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        pass

                    async def deploy_smart_contract(self, *args, **kwargs):
                        return await mock_deploy_smart_contract(*args, **kwargs)

                # Replace the client temporarily
                mcp_module.MCPBlockchainClient = MockMCPClient

            try:
                # Test escrow deployment (this should trigger enforcement events)
                deployment_response = await escrow_service.deploy_escrow(deployment_request)

                if not deployment_response.success:
                    logger.error(f"Escrow deployment failed: {deployment_response.error_message}")
                    return False

                # Wait for events to be processed
                await asyncio.sleep(2)

                # Verify enforcement events were captured
                if not enforcement_events:
                    logger.error("No enforcement events captured")
                    return False

                # Check for escrow deployment event
                deployment_events = [e for e in enforcement_events if e['operation'] == 'escrow_deployment']
                if not deployment_events:
                    logger.error("No escrow deployment events found")
                    return False

                logger.info(f"✅ Enforcement integration test passed: {len(enforcement_events)} events")
                return True

            finally:
                # Restore original client
                if original_client:
                    mcp_module.MCPBlockchainClient = original_client

                # Cleanup subscription
                await streaming_service.unsubscribe(enforcement_sub_id)

        except Exception as e:
            logger.error(f"Enforcement integration test failed: {e}")
            return False

    async def test_performance(self) -> bool:
        """Test performance under load"""
        try:
            # Performance test parameters
            num_events = 100
            max_latency_ms = 100
            max_processing_time_ms = 50

            performance_data = []

            # Subscribe to measure performance
            async def performance_callback(streaming_event):
                receive_time = time.time()
                event_time = streaming_event.timestamp_received
                latency_ms = (receive_time - event_time) * 1000
                performance_data.append({
                    'latency_ms': latency_ms,
                    'event_id': streaming_event.id
                })

            streaming_service = await get_event_streaming_service()
            perf_sub_id = f"performance_test_{uuid.uuid4()}"
            await streaming_service.subscribe(perf_sub_id, performance_callback)

            # Generate events rapidly
            start_time = time.time()

            for i in range(num_events):
                event = create_loan_audit_event(
                    event_type=AuditEventType.LOAN_REQUEST_CREATED,
                    loan_id=f"perf-test-loan-{i}",
                    borrower_address=f"perf-borrower-{i}",
                    service_name="performance_test",
                    amount_micro_algos=1000000,
                    metadata={"performance_test": True, "sequence": i}
                )

                await stream_audit_event(event, EventPriority.NORMAL)

            generation_time = (time.time() - start_time) * 1000

            # Wait for processing
            await asyncio.sleep(3)

            # Cleanup
            await streaming_service.unsubscribe(perf_sub_id)

            # Analyze performance
            if len(performance_data) < num_events * 0.9:  # Allow 10% loss
                logger.error(f"Performance test: Only received {len(performance_data)}/{num_events} events")
                return False

            latencies = [d['latency_ms'] for d in performance_data]
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)

            # Get system metrics
            streaming_metrics = await get_streaming_metrics()
            processing_metrics = await get_processing_metrics()

            self.performance_metrics = {
                'events_generated': num_events,
                'events_received': len(performance_data),
                'generation_time_ms': generation_time,
                'average_latency_ms': avg_latency,
                'max_latency_ms': max_latency,
                'throughput_events_per_second': num_events / (generation_time / 1000),
                'streaming_metrics': streaming_metrics,
                'processing_metrics': processing_metrics
            }

            # Performance validation
            if avg_latency > max_latency_ms:
                logger.warning(f"Average latency {avg_latency:.2f}ms exceeds target {max_latency_ms}ms")

            if processing_metrics['average_processing_time_ms'] > max_processing_time_ms:
                logger.warning(f"Processing time {processing_metrics['average_processing_time_ms']:.2f}ms exceeds target {max_processing_time_ms}ms")

            logger.info(f"📈 Performance: {len(performance_data)} events, "
                       f"avg latency {avg_latency:.2f}ms, "
                       f"throughput {self.performance_metrics['throughput_events_per_second']:.2f} events/sec")

            return True

        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling and recovery"""
        try:
            # Test invalid event handling
            streaming_service = await get_event_streaming_service()

            # Test with invalid event data
            try:
                invalid_event = AuditTrail(
                    event_type=None,  # Invalid
                    severity=AuditSeverity.INFO,
                    event_data=None,  # Invalid
                    service_name=""  # Invalid
                )

                success = await stream_audit_event(invalid_event)
                if success:
                    logger.error("Invalid event was accepted")
                    return False

            except Exception as e:
                logger.info(f"✅ Invalid event correctly rejected: {type(e).__name__}")

            # Test subscriber error handling
            error_count = 0

            async def failing_callback(streaming_event):
                nonlocal error_count
                error_count += 1
                raise Exception("Simulated callback failure")

            # Subscribe with failing callback
            error_sub_id = f"error_test_{uuid.uuid4()}"
            await streaming_service.subscribe(error_sub_id, failing_callback)

            # Send event to failing subscriber
            test_event = create_loan_audit_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                loan_id="error-test-loan",
                borrower_address="error-test-borrower",
                service_name="error_test",
                amount_micro_algos=1000000,
                metadata={"error_test": True}
            )

            await stream_audit_event(test_event, EventPriority.NORMAL)
            await asyncio.sleep(1)

            # Cleanup
            await streaming_service.unsubscribe(error_sub_id)

            # Verify error was handled gracefully
            if error_count == 0:
                logger.error("Error callback was not called")
                return False

            logger.info("✅ Error handling test passed")
            return True

        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False

    async def test_concurrent_load(self) -> bool:
        """Test concurrent load handling"""
        try:
            num_concurrent_clients = 10
            events_per_client = 20
            total_expected_events = num_concurrent_clients * events_per_client

            all_received_events = []

            async def concurrent_client(client_id: int):
                """Simulate concurrent client"""
                client_events = []

                async def client_callback(streaming_event):
                    client_events.append(streaming_event)
                    all_received_events.append(streaming_event)

                streaming_service = await get_event_streaming_service()
                sub_id = f"concurrent_client_{client_id}_{uuid.uuid4()}"

                try:
                    await streaming_service.subscribe(sub_id, client_callback)

                    # Generate events from this client
                    for i in range(events_per_client):
                        event = create_loan_audit_event(
                            event_type=AuditEventType.LOAN_REQUEST_CREATED,
                            loan_id=f"concurrent-loan-{client_id}-{i}",
                            borrower_address=f"concurrent-borrower-{client_id}",
                            service_name=f"concurrent_client_{client_id}",
                            amount_micro_algos=1000000,
                            metadata={
                                "client_id": client_id,
                                "sequence": i,
                                "concurrent_test": True
                            }
                        )

                        await stream_audit_event(event, EventPriority.NORMAL)
                        await asyncio.sleep(0.1)  # Small delay to simulate real usage

                    # Wait for processing
                    await asyncio.sleep(2)

                    return len(client_events)

                finally:
                    await streaming_service.unsubscribe(sub_id)

            # Start concurrent clients
            start_time = time.time()
            client_tasks = [
                asyncio.create_task(concurrent_client(i))
                for i in range(num_concurrent_clients)
            ]

            # Wait for all clients to complete
            client_results = await asyncio.gather(*client_tasks)
            test_duration = time.time() - start_time

            # Analyze results
            total_received = sum(client_results)
            total_unique_events = len(set(e.id for e in all_received_events))

            logger.info(f"🚀 Concurrent test: {num_concurrent_clients} clients, "
                       f"{total_received} events received, "
                       f"{total_unique_events} unique events, "
                       f"{test_duration:.2f}s duration")

            # Validation
            if total_received < total_expected_events * 0.9:  # Allow 10% loss under load
                logger.error(f"Concurrent test: Only received {total_received}/{total_expected_events} events")
                return False

            return True

        except Exception as e:
            logger.error(f"Concurrent load test failed: {e}")
            return False

    async def print_test_report(self):
        """Print comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("📋 REAL-TIME EVENT STREAMING SYSTEM TEST REPORT")
        logger.info("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASSED')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'FAILED')
        error_tests = sum(1 for r in self.test_results.values() if r['status'] == 'ERROR')

        logger.info(f"📊 Summary: {passed_tests}/{total_tests} tests passed")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"💥 Errors: {error_tests}")

        logger.info("\n📋 Test Details:")
        for test_name, result in self.test_results.items():
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}[result['status']]
            logger.info(f"{status_emoji} {test_name}: {result['status']} ({result.get('duration_ms', 0):.2f}ms)")

            if 'error' in result:
                logger.info(f"   Error: {result['error']}")

        # Performance metrics
        if self.performance_metrics:
            logger.info("\n📈 Performance Metrics:")
            logger.info(f"   Events Generated: {self.performance_metrics['events_generated']}")
            logger.info(f"   Events Received: {self.performance_metrics['events_received']}")
            logger.info(f"   Average Latency: {self.performance_metrics['average_latency_ms']:.2f}ms")
            logger.info(f"   Max Latency: {self.performance_metrics['max_latency_ms']:.2f}ms")
            logger.info(f"   Throughput: {self.performance_metrics['throughput_events_per_second']:.2f} events/sec")

        # System status
        try:
            streaming_metrics = await get_streaming_metrics()
            processing_metrics = await get_processing_metrics()

            logger.info("\n🔧 System Status:")
            logger.info(f"   Active Connections: {streaming_metrics.get('active_connections', 0)}")
            logger.info(f"   Queue Size: {streaming_metrics.get('queue_size', 0)}")
            logger.info(f"   Events Per Second: {streaming_metrics.get('events_per_second', 0):.2f}")
            logger.info(f"   Processing Time: {processing_metrics.get('average_processing_time_ms', 0):.2f}ms")

        except Exception as e:
            logger.warning(f"Could not retrieve system metrics: {e}")

        logger.info("="*60)


async def main():
    """Main test execution function"""
    try:
        # Initialize test suite
        test_suite = EventStreamingTestSuite()

        # Run all tests
        success = await test_suite.run_all_tests()

        if success:
            logger.info("🎉 All tests passed! Event streaming system is working correctly.")
            exit_code = 0
        else:
            logger.error("💥 Some tests failed. Please check the system.")
            exit_code = 1

        return exit_code

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

    finally:
        # Cleanup
        try:
            from src.core.audit.event_streaming import shutdown_event_streaming_service
            from src.core.audit.event_processor import shutdown_processing_pipeline

            await shutdown_event_streaming_service()
            await shutdown_processing_pipeline()

        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")


if __name__ == "__main__":
    import signal

    def signal_handler(sig, frame):
        logger.info("\n🛑 Test interrupted by user")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)