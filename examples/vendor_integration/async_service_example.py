#!/usr/bin/env python3
"""
Async Service Integration Example

This demonstrates how to integrate the algorand-lending-business-logic package
into an asynchronous background service for high-performance, non-blocking operations.

Features:
- AsyncIO-based loan processing
- Non-blocking queue management
- Concurrent analysis of multiple requests
- WebSocket real-time updates
- Background task scheduling
- Graceful shutdown handling

Usage:
    pip install aiohttp websockets
    python async_service_example.py

WebSocket endpoints:
    ws://localhost:8080/ws - Real-time loan analysis updates

HTTP endpoints:
    POST /submit - Submit loan request for async processing
    GET /status/{request_id} - Check processing status
    GET /health - Service health check
"""

import sys
import json
import asyncio
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Add the vendor package to Python path (if not installed)
vendor_path = Path(__file__).parent / "algorand_lending_bl"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path.parent))

try:
    import aiohttp
    from aiohttp import web, WSMsgType
    import websockets
except ImportError:
    print("❌ Required packages not installed. Please run:")
    print("   pip install aiohttp websockets")
    sys.exit(1)

# Import lending business logic
from algorand_lending_bl import (
    create_lending_service,
    LoanRequest,
    AlgorandAddress,
    ASAToken,
    VENDOR_INFO
)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class AsyncLoanRequest:
    """Async loan request with tracking information."""
    request_id: str
    borrower: str
    requested_amount: int
    collateral_assets: List[Dict[str, Any]]
    loan_duration_days: int
    submitted_at: datetime
    status: str = "pending"  # pending, processing, completed, failed
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class ProcessingUpdate:
    """Update message for processing progress."""
    request_id: str
    status: str
    progress: float
    stage: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None

# ============================================================================
# ASYNC LENDING SERVICE
# ============================================================================

class AsyncLendingService:
    """Asynchronous lending service with queue management."""

    def __init__(self, max_concurrent: int = 10, queue_size: int = 1000):
        """
        Initialize async lending service.

        Args:
            max_concurrent: Maximum concurrent processing tasks
            queue_size: Maximum queue size
        """
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size

        # Service components
        self.lending_service = None
        self.request_queue = asyncio.Queue(maxsize=queue_size)
        self.active_requests: Dict[str, AsyncLoanRequest] = {}
        self.completed_requests: Dict[str, AsyncLoanRequest] = {}
        self.processing_tasks: List[asyncio.Task] = []

        # WebSocket connections
        self.websocket_connections: List[websockets.WebSocketServerProtocol] = []

        # Statistics
        self.stats = {
            'total_submitted': 0,
            'total_completed': 0,
            'total_failed': 0,
            'start_time': time.time(),
            'avg_processing_time': 0.0
        }

        # Shutdown event
        self.shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize the lending service."""
        print("🚀 Initializing async lending service...")

        # Initialize lending service in thread pool since it's CPU-bound
        loop = asyncio.get_event_loop()
        self.lending_service = await loop.run_in_executor(
            None, create_lending_service
        )

        print(f"✓ Lending service ready with {len(self.lending_service)} engines")

        # Start processing workers
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._processing_worker(f"worker-{i}"))
            self.processing_tasks.append(task)

        print(f"✓ Started {self.max_concurrent} processing workers")

    async def submit_loan_request(self, request_data: Dict[str, Any]) -> str:
        """
        Submit a loan request for async processing.

        Args:
            request_data: Loan request data

        Returns:
            Request ID for tracking
        """
        request_id = str(uuid.uuid4())

        async_request = AsyncLoanRequest(
            request_id=request_id,
            borrower=request_data['borrower'],
            requested_amount=request_data['requested_amount'],
            collateral_assets=request_data.get('collateral_assets', []),
            loan_duration_days=request_data.get('loan_duration_days', 30),
            submitted_at=datetime.utcnow()
        )

        # Add to queue
        try:
            await self.request_queue.put(async_request)
            self.active_requests[request_id] = async_request
            self.stats['total_submitted'] += 1

            # Notify WebSocket clients
            await self._broadcast_update(ProcessingUpdate(
                request_id=request_id,
                status="queued",
                progress=0.0,
                stage="submitted",
                timestamp=datetime.utcnow()
            ))

            print(f"📝 Submitted request {request_id} to queue")
            return request_id

        except asyncio.QueueFull:
            raise Exception("Service queue is full, please try again later")

    async def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a loan request."""

        # Check active requests
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            return {
                'request_id': request_id,
                'status': request.status,
                'progress': request.progress,
                'submitted_at': request.submitted_at.isoformat(),
                'result': request.result,
                'error': request.error
            }

        # Check completed requests
        if request_id in self.completed_requests:
            request = self.completed_requests[request_id]
            return {
                'request_id': request_id,
                'status': request.status,
                'progress': 100.0,
                'submitted_at': request.submitted_at.isoformat(),
                'result': request.result,
                'error': request.error
            }

        return None

    async def _processing_worker(self, worker_id: str):
        """Worker coroutine for processing loan requests."""
        print(f"🔧 Worker {worker_id} started")

        while not self.shutdown_event.is_set():
            try:
                # Get request from queue with timeout
                request = await asyncio.wait_for(
                    self.request_queue.get(),
                    timeout=1.0
                )

                print(f"🔍 Worker {worker_id} processing {request.request_id}")
                await self._process_loan_request(request, worker_id)

            except asyncio.TimeoutError:
                # No requests in queue, continue
                continue
            except Exception as e:
                print(f"❌ Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        print(f"🛑 Worker {worker_id} stopped")

    async def _process_loan_request(self, request: AsyncLoanRequest, worker_id: str):
        """Process a single loan request asynchronously."""
        start_time = time.time()

        try:
            # Update status to processing
            request.status = "processing"
            request.progress = 10.0

            await self._broadcast_update(ProcessingUpdate(
                request_id=request.request_id,
                status="processing",
                progress=10.0,
                stage="parsing_request",
                timestamp=datetime.utcnow()
            ))

            # Parse loan request
            borrower = AlgorandAddress(request.borrower)
            collateral_assets = []

            for asset_data in request.collateral_assets:
                asset = ASAToken(
                    asset_id=asset_data['asset_id'],
                    amount=asset_data['amount']
                )
                collateral_assets.append(asset)

            loan_request = LoanRequest(
                borrower=borrower,
                requested_amount=request.requested_amount,
                collateral_assets=collateral_assets,
                loan_duration_days=request.loan_duration_days
            )

            # Progress: 25%
            request.progress = 25.0
            await self._broadcast_update(ProcessingUpdate(
                request_id=request.request_id,
                status="processing",
                progress=25.0,
                stage="collateral_analysis",
                timestamp=datetime.utcnow()
            ))

            # Run collateral analysis in thread pool
            loop = asyncio.get_event_loop()
            collateral_analysis = await loop.run_in_executor(
                None,
                self.lending_service["collateral"].analyze_collateral,
                collateral_assets,
                borrower
            )

            # Progress: 50%
            request.progress = 50.0
            await self._broadcast_update(ProcessingUpdate(
                request_id=request.request_id,
                status="processing",
                progress=50.0,
                stage="interest_rate_calculation",
                timestamp=datetime.utcnow()
            ))

            # Calculate interest rate
            rate_calculation = await loop.run_in_executor(
                None,
                self.lending_service["interest_rates"].calculate_interest_rate,
                loan_request
            )

            # Progress: 75%
            request.progress = 75.0
            await self._broadcast_update(ProcessingUpdate(
                request_id=request.request_id,
                status="processing",
                progress=75.0,
                stage="loan_evaluation",
                timestamp=datetime.utcnow()
            ))

            # Evaluate loan and assess risk concurrently
            loan_decision_task = loop.run_in_executor(
                None,
                self.lending_service["loan_approval"].evaluate_loan,
                loan_request
            )

            risk_assessment_task = loop.run_in_executor(
                None,
                self.lending_service["risk_assessment"].assess_risk,
                loan_request
            )

            loan_decision, risk_assessment = await asyncio.gather(
                loan_decision_task,
                risk_assessment_task
            )

            # Complete processing
            processing_time = time.time() - start_time

            # Prepare result
            result = {
                'collateral_analysis': {
                    'total_value': collateral_analysis.total_value,
                    'liquidity_tier': collateral_analysis.liquidity_tier.value,
                    'portfolio_risk': collateral_analysis.portfolio_risk.value
                },
                'interest_rate': {
                    'base_rate': rate_calculation.base_rate,
                    'final_rate': rate_calculation.final_rate,
                    'risk_premium': rate_calculation.risk_premium
                },
                'loan_decision': {
                    'decision': loan_decision.decision.value,
                    'confidence': loan_decision.confidence.value,
                    'approved_amount': loan_decision.approved_amount
                },
                'risk_assessment': {
                    'overall_score': risk_assessment.overall_score,
                    'risk_level': risk_assessment.risk_level.value,
                    'borrower_risk': risk_assessment.borrower_risk,
                    'collateral_risk': risk_assessment.collateral_risk
                },
                'processing_metadata': {
                    'worker_id': worker_id,
                    'processing_time_seconds': round(processing_time, 3),
                    'completed_at': datetime.utcnow().isoformat()
                }
            }

            # Update request
            request.status = "completed"
            request.progress = 100.0
            request.result = result

            # Move to completed requests
            self.completed_requests[request.request_id] = request
            del self.active_requests[request.request_id]

            # Update statistics
            self.stats['total_completed'] += 1
            total_time = sum(
                r.result['processing_metadata']['processing_time_seconds']
                for r in self.completed_requests.values()
                if r.result
            )
            self.stats['avg_processing_time'] = total_time / self.stats['total_completed']

            # Final update
            await self._broadcast_update(ProcessingUpdate(
                request_id=request.request_id,
                status="completed",
                progress=100.0,
                stage="finished",
                timestamp=datetime.utcnow(),
                data=result
            ))

            print(f"✅ Completed {request.request_id} in {processing_time:.2f}s")

        except Exception as e:
            # Handle processing error
            request.status = "failed"
            request.error = str(e)

            self.completed_requests[request.request_id] = request
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]

            self.stats['total_failed'] += 1

            await self._broadcast_update(ProcessingUpdate(
                request_id=request.request_id,
                status="failed",
                progress=0.0,
                stage="error",
                timestamp=datetime.utcnow(),
                data={'error': str(e)}
            ))

            print(f"❌ Failed {request.request_id}: {e}")

    async def _broadcast_update(self, update: ProcessingUpdate):
        """Broadcast update to all WebSocket connections."""
        if not self.websocket_connections:
            return

        message = json.dumps(asdict(update), default=str)

        # Remove closed connections
        active_connections = []
        for ws in self.websocket_connections:
            try:
                await ws.send(message)
                active_connections.append(ws)
            except websockets.exceptions.ConnectionClosed:
                continue
            except Exception as e:
                print(f"WebSocket broadcast error: {e}")

        self.websocket_connections = active_connections

    async def add_websocket_connection(self, websocket):
        """Add a WebSocket connection for updates."""
        self.websocket_connections.append(websocket)
        print(f"📡 WebSocket client connected ({len(self.websocket_connections)} total)")

    async def remove_websocket_connection(self, websocket):
        """Remove a WebSocket connection."""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        print(f"📡 WebSocket client disconnected ({len(self.websocket_connections)} total)")

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        uptime = time.time() - self.stats['start_time']

        return {
            'service_info': {
                'package': VENDOR_INFO['name'],
                'version': VENDOR_INFO['version'],
                'uptime_seconds': round(uptime, 2)
            },
            'queue_info': {
                'queue_size': self.request_queue.qsize(),
                'max_queue_size': self.queue_size,
                'active_requests': len(self.active_requests),
                'completed_requests': len(self.completed_requests)
            },
            'processing_stats': self.stats,
            'workers': {
                'max_concurrent': self.max_concurrent,
                'active_workers': len([t for t in self.processing_tasks if not t.done()])
            },
            'websocket_connections': len(self.websocket_connections)
        }

    async def shutdown(self):
        """Graceful shutdown of the service."""
        print("🛑 Shutting down async lending service...")

        # Signal shutdown
        self.shutdown_event.set()

        # Wait for workers to finish
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)

        # Close WebSocket connections
        for ws in self.websocket_connections:
            try:
                await ws.close()
            except:
                pass

        print("✓ Async lending service shutdown complete")

# ============================================================================
# HTTP SERVER
# ============================================================================

class AsyncLendingServer:
    """HTTP server for the async lending service."""

    def __init__(self, lending_service: AsyncLendingService):
        self.lending_service = lending_service
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_post('/submit', self.submit_loan_request)
        self.app.router.add_get('/status/{request_id}', self.get_request_status)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/stats', self.get_stats)
        self.app.router.add_get('/ws', self.websocket_handler)

    async def submit_loan_request(self, request):
        """Submit loan request endpoint."""
        try:
            data = await request.json()

            # Validate required fields
            required_fields = ['borrower', 'requested_amount', 'collateral_assets']
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {'error': f'Missing required field: {field}'},
                        status=400
                    )

            # Submit request
            request_id = await self.lending_service.submit_loan_request(data)

            return web.json_response({
                'request_id': request_id,
                'status': 'submitted',
                'message': 'Loan request submitted for processing'
            })

        except Exception as e:
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def get_request_status(self, request):
        """Get request status endpoint."""
        request_id = request.match_info['request_id']

        status = await self.lending_service.get_request_status(request_id)

        if status is None:
            return web.json_response(
                {'error': 'Request not found'},
                status=404
            )

        return web.json_response(status)

    async def health_check(self, request):
        """Health check endpoint."""
        stats = await self.lending_service.get_service_stats()

        return web.json_response({
            'status': 'healthy',
            'service': 'async-lending-service',
            'stats': stats
        })

    async def get_stats(self, request):
        """Get service statistics."""
        stats = await self.lending_service.get_service_stats()
        return web.json_response(stats)

    async def websocket_handler(self, request):
        """WebSocket handler for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        await self.lending_service.add_websocket_connection(ws)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Handle client messages if needed
                    pass
                elif msg.type == WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')

        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await self.lending_service.remove_websocket_connection(ws)

        return ws

# ============================================================================
# MAIN APPLICATION
# ============================================================================

async def create_sample_requests():
    """Create sample requests for testing."""
    return [
        {
            'borrower': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'requested_amount': 1000000,  # 1 ALGO
            'collateral_assets': [
                {'asset_id': 0, 'amount': 2000000}  # 2 ALGO
            ],
            'loan_duration_days': 30
        },
        {
            'borrower': 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
            'requested_amount': 5000000,  # 5 ALGO
            'collateral_assets': [
                {'asset_id': 0, 'amount': 10000000}  # 10 ALGO
            ],
            'loan_duration_days': 60
        },
        {
            'borrower': 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC',
            'requested_amount': 500000,  # 0.5 ALGO
            'collateral_assets': [
                {'asset_id': 0, 'amount': 1500000}  # 1.5 ALGO
            ],
            'loan_duration_days': 14
        }
    ]

async def demo_async_processing():
    """Demonstrate async loan processing."""
    print("\n🚀 Starting async loan processing demo...")

    # Initialize service
    lending_service = AsyncLendingService(max_concurrent=3, queue_size=100)
    await lending_service.initialize()

    # Create sample requests
    sample_requests = await create_sample_requests()

    # Submit requests
    request_ids = []
    for i, request_data in enumerate(sample_requests):
        request_id = await lending_service.submit_loan_request(request_data)
        request_ids.append(request_id)
        print(f"📝 Submitted request {i+1}: {request_id}")

    # Monitor progress
    print("\n📊 Monitoring processing progress...")
    completed_count = 0

    while completed_count < len(request_ids):
        await asyncio.sleep(2)  # Check every 2 seconds

        for request_id in request_ids:
            status = await lending_service.get_request_status(request_id)
            if status and status['status'] == 'completed':
                if request_id not in [r for r in request_ids[:completed_count]]:
                    print(f"✅ Request {request_id} completed")
                    completed_count += 1

    print(f"\n🎉 All {len(request_ids)} requests completed!")

    # Show final statistics
    stats = await lending_service.get_service_stats()
    print(f"\n📈 Final Statistics:")
    print(f"   Total completed: {stats['processing_stats']['total_completed']}")
    print(f"   Average processing time: {stats['processing_stats']['avg_processing_time']:.2f}s")

    # Shutdown service
    await lending_service.shutdown()

async def start_server():
    """Start the HTTP server."""
    print("🌐 Starting async lending HTTP server...")

    # Initialize service
    lending_service = AsyncLendingService(max_concurrent=5, queue_size=1000)
    await lending_service.initialize()

    # Create server
    server = AsyncLendingServer(lending_service)

    # Start server
    runner = web.AppRunner(server.app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    print("✓ Server started at http://localhost:8080")
    print("\nAvailable endpoints:")
    print("  POST /submit - Submit loan request")
    print("  GET /status/{request_id} - Check status")
    print("  GET /health - Health check")
    print("  GET /stats - Service statistics")
    print("  WS /ws - WebSocket for real-time updates")

    print("\nSample request:")
    sample_request = (await create_sample_requests())[0]
    print(json.dumps(sample_request, indent=2))

    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        await lending_service.shutdown()
        await runner.cleanup()

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Async lending service example")
    parser.add_argument("--demo", action="store_true", help="Run processing demo")
    parser.add_argument("--server", action="store_true", help="Start HTTP server")

    args = parser.parse_args()

    print("🏦 Algorand Lending Async Service")
    print("=" * 50)
    print(f"📦 Package: {VENDOR_INFO['name']} v{VENDOR_INFO['version']}")

    if args.demo:
        asyncio.run(demo_async_processing())
    elif args.server:
        asyncio.run(start_server())
    else:
        print("\nChoose mode:")
        print("  --demo   Run async processing demonstration")
        print("  --server Start HTTP server with WebSocket support")

if __name__ == "__main__":
    main()