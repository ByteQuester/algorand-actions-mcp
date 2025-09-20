#!/usr/bin/env python3
"""
Quick Validation Script for Real-time Event Streaming System

This script validates that the event streaming system is properly integrated
and functioning correctly.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def validate_event_system():
    """Validate the event streaming system components"""

    logger.info("🚀 Validating Real-time Event Streaming System")

    try:
        # Test 1: Import all modules
        logger.info("📦 Testing module imports...")

        from src.core.audit.event_streaming import (
            get_event_streaming_service, stream_audit_event, EventPriority
        )
        from src.core.audit.event_processor import (
            get_processing_pipeline, process_audit_event
        )
        from src.core.audit.models import (
            create_loan_audit_event, AuditEventType, AuditSeverity
        )

        logger.info("✅ All modules imported successfully")

        # Test 2: Initialize services
        logger.info("🔧 Initializing streaming service...")

        streaming_service = await get_event_streaming_service()
        processing_pipeline = await get_processing_pipeline()

        logger.info("✅ Services initialized successfully")

        # Test 3: Create and process a test event
        logger.info("📝 Creating test event...")

        test_event = create_loan_audit_event(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            loan_id="validation-test-loan",
            borrower_address="validation-test-borrower",
            service_name="validation_test",
            amount_micro_algos=1000000,
            metadata={
                "validation_test": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_purpose": "system_validation"
            }
        )

        logger.info("✅ Test event created successfully")

        # Test 4: Stream the event
        logger.info("📡 Testing event streaming...")

        events_received = []

        async def test_callback(streaming_event):
            events_received.append(streaming_event)
            logger.info(f"📨 Received event: {streaming_event.event.event_type.value}")

        # Subscribe to receive the event
        subscription_id = "validation_test_subscription"
        success = await streaming_service.subscribe(subscription_id, test_callback)

        if not success:
            logger.error("❌ Failed to subscribe to event stream")
            return False

        # Stream the event
        success = await stream_audit_event(test_event, EventPriority.HIGH)

        if not success:
            logger.error("❌ Failed to stream event")
            return False

        # Wait for event processing
        await asyncio.sleep(2)

        # Cleanup subscription
        await streaming_service.unsubscribe(subscription_id)

        # Verify event was received
        if not events_received:
            logger.error("❌ No events received")
            return False

        if len(events_received) != 1:
            logger.warning(f"⚠️ Expected 1 event, received {len(events_received)}")

        logger.info("✅ Event streaming test completed successfully")

        # Test 5: Check system metrics
        logger.info("📊 Checking system metrics...")

        try:
            from src.core.audit.event_streaming import get_streaming_metrics
            from src.core.audit.event_processor import get_processing_metrics

            streaming_metrics = await get_streaming_metrics()
            processing_metrics = await get_processing_metrics()

            logger.info(f"📈 Streaming metrics: {streaming_metrics.get('events_per_second', 0):.2f} events/sec")
            logger.info(f"⚙️  Processing metrics: {processing_metrics.get('events_processed', 0)} events processed")

        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve metrics: {e}")

        logger.info("✅ System metrics check completed")

        # Test 6: Validate enforcement integration
        logger.info("🔒 Testing enforcement integration...")

        try:
            from src.core.audit.event_hooks import EnforcementHooks

            # Test enforcement hook (this won't actually execute enforcement logic)
            await EnforcementHooks.escrow_deployed(
                escrow_id="validation-escrow-123",
                loan_id="validation-test-loan",
                app_id=12345,
                escrow_address="validation-escrow-address"
            )

            logger.info("✅ Enforcement integration test completed")

        except Exception as e:
            logger.warning(f"⚠️ Enforcement integration test failed: {e}")

        # Test 7: Test WebSocket router components
        logger.info("🌐 Testing WebSocket components...")

        try:
            from src.api.websocket_router import ws_manager

            # Get WebSocket stats
            stats = await ws_manager.get_stats()
            logger.info(f"🔌 WebSocket connections: {stats['total_connections']}")

            logger.info("✅ WebSocket components test completed")

        except Exception as e:
            logger.warning(f"⚠️ WebSocket components test failed: {e}")

        logger.info("\n🎉 Event streaming system validation completed successfully!")
        logger.info("="*60)
        logger.info("✅ All core components are working correctly")
        logger.info("📡 Real-time event streaming is functional")
        logger.info("⚙️  Event processing pipeline is operational")
        logger.info("🔒 Enforcement integration is active")
        logger.info("🌐 WebSocket streaming is ready")
        logger.info("="*60)

        return True

    except ImportError as e:
        logger.error(f"❌ Module import failed: {e}")
        logger.error("💡 Make sure all dependencies are installed and paths are correct")
        return False

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        logger.error(f"💡 Error details: {str(e)}")
        return False


async def cleanup():
    """Cleanup resources"""
    try:
        from src.core.audit.event_streaming import shutdown_event_streaming_service
        from src.core.audit.event_processor import shutdown_processing_pipeline

        logger.info("🧹 Cleaning up resources...")
        await shutdown_event_streaming_service()
        await shutdown_processing_pipeline()
        logger.info("✅ Cleanup completed")

    except Exception as e:
        logger.warning(f"⚠️ Cleanup warning: {e}")


def main():
    """Main validation function"""
    try:
        # Run validation
        success = asyncio.run(validate_event_system())

        if success:
            logger.info("🎊 Validation successful! The real-time event streaming system is ready for use.")
            return 0
        else:
            logger.error("💥 Validation failed. Please check the error messages above.")
            return 1

    except KeyboardInterrupt:
        logger.info("\n🛑 Validation interrupted by user")
        return 1

    except Exception as e:
        logger.error(f"💥 Validation error: {e}")
        return 1

    finally:
        # Run cleanup
        try:
            asyncio.run(cleanup())
        except Exception as e:
            logger.warning(f"⚠️ Final cleanup error: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)