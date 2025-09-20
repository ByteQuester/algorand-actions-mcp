"""
Main FastAPI Application for Interest Rate Determiner

Comprehensive REST API with WebSocket support for all interest rate engines.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from .routers import rates, market, risk, credit, compliance, monitoring
from .models import ErrorResponse
from .. import get_available_engines, check_engine_availability

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Interest Rate Determiner API")

    # Check engine availability
    available_engines = get_available_engines()
    logger.info(f"Available engines: {len(available_engines)}/6")

    yield

    # Shutdown
    logger.info("Shutting down Interest Rate Determiner API")


# Create FastAPI application
app = FastAPI(
    title="Interest Rate Determiner API",
    description="""
    Comprehensive Interest Rate Determination System for Algorand DeFi Lending

    This API provides access to 6 specialized engines for calculating appropriate
    interest rates based on market conditions, risk assessment, credit scoring,
    regulatory compliance, dynamic pricing, and rate optimization.

    ## Features

    * **Market Rate Analysis**: Real-time market condition analysis
    * **Risk Assessment**: Comprehensive borrower and market risk evaluation
    * **Credit Scoring**: Traditional and blockchain-based credit scoring
    * **Regulatory Compliance**: Multi-jurisdiction compliance verification
    * **Dynamic Pricing**: Real-time rate adjustments
    * **Rate Optimization**: Profit and competitiveness optimization
    * **WebSocket Support**: Real-time rate updates

    ## Engine Integration

    All engines integrate with the blockchain-collateral-analyzer package and
    support Algorand-specific features including ASA tokens, governance
    participation, and staking rewards.
    """,
    version="1.0.0",
    contact={
        "name": "Algorand Lending Ecosystem",
        "email": "dev@algorand-lending.io",
        "url": "https://algorand-lending.io"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(rates.router, prefix="/api/v1/rates", tags=["rates"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(credit.router, prefix="/api/v1/credit", tags=["credit"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation and status page"""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Interest Rate Determiner API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #2c3e50; }
                .status { background: #f8f9fa; padding: 20px; border-radius: 5px; }
                .endpoint { margin: 10px 0; }
                .ws-test { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1 class="header">Interest Rate Determiner API</h1>
            <div class="status">
                <h2>Status</h2>
                <p>API is running and ready to process requests.</p>
                <p><strong>Version:</strong> 1.0.0</p>
                <p><strong>Documentation:</strong> <a href="/docs">/docs</a></p>
                <p><strong>OpenAPI Schema:</strong> <a href="/openapi.json">/openapi.json</a></p>
            </div>

            <h2>Available Endpoints</h2>
            <div class="endpoint"><strong>POST</strong> /api/v1/rates/calculate - Calculate comprehensive interest rate</div>
            <div class="endpoint"><strong>POST</strong> /api/v1/market/analyze - Market rate analysis</div>
            <div class="endpoint"><strong>POST</strong> /api/v1/risk/assess - Risk assessment</div>
            <div class="endpoint"><strong>POST</strong> /api/v1/credit/score - Credit scoring</div>
            <div class="endpoint"><strong>POST</strong> /api/v1/compliance/check - Compliance verification</div>
            <div class="endpoint"><strong>GET</strong> /api/v1/monitoring/health - Health check</div>
            <div class="endpoint"><strong>WebSocket</strong> /ws/{client_id} - Real-time updates</div>

            <div class="ws-test">
                <h3>WebSocket Test</h3>
                <p>Connect to WebSocket at: <code>ws://localhost:8000/ws/test</code></p>
                <p>You'll receive real-time rate updates and market data.</p>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    available_engines = get_available_engines()
    return {
        "status": "healthy",
        "engines_available": len(available_engines),
        "engines_total": 6,
        "engines": list(available_engines.keys())
    }


@app.get("/engines")
async def engine_status():
    """Get detailed engine status"""
    available_engines = get_available_engines()

    engine_status = {
        "market_rate_analysis": "market_rate_analysis" in available_engines,
        "risk_assessment": "risk_assessment" in available_engines,
        "credit_scoring": "credit_scoring" in available_engines,
        "regulatory_compliance": "regulatory_compliance" in available_engines,
        "dynamic_pricing": "dynamic_pricing" in available_engines,
        "rate_optimization": "rate_optimization" in available_engines,
    }

    return {
        "total_engines": 6,
        "available_engines": len(available_engines),
        "engine_status": engine_status,
        "available_engine_classes": {
            name: engine.__name__ for name, engine in available_engines.items()
        }
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "message": f"Connected as {client_id}",
            "timestamp": "2024-01-01T00:00:00Z"
        }, client_id)

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()

            # Echo back the message (in production, this would handle specific commands)
            await manager.send_personal_message({
                "type": "echo",
                "message": f"Received: {data}",
                "timestamp": "2024-01-01T00:00:00Z"
            }, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail=ErrorResponse(
            error="internal_server_error",
            message="An internal server error occurred",
            details={"exception": str(exc)}
        ).dict()
    )


# Background task for broadcasting rate updates
async def rate_update_broadcaster():
    """Background task to broadcast rate updates"""
    while True:
        try:
            # Simulate rate updates (in production, this would get real data)
            update_message = {
                "type": "rate_update",
                "data": {
                    "asset": "ALGO",
                    "base_rate": 0.05,
                    "market_sentiment": "neutral",
                    "volatility_score": 0.4,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }

            await manager.broadcast(update_message)
            await asyncio.sleep(60)  # Update every minute

        except Exception as e:
            logger.error(f"Error in rate update broadcaster: {e}")
            await asyncio.sleep(60)


# Start background task
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(rate_update_broadcaster())


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )