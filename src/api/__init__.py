"""
Unified API Gateway for Algorand Lending Platform

This package provides a comprehensive API gateway that supports both vendor mode
(direct imports) and hosted service mode (HTTP calls) for the Algorand lending
platform. It includes service discovery, health monitoring, WebSocket support,
and comprehensive observability features.

Key Components:
- gateway.py: Main API gateway with unified REST endpoints
- websocket_handler.py: Real-time WebSocket communication
- service_discovery.py: Service registry and discovery mechanism
- health_checks.py: Health monitoring and system metrics

Usage:
    # Vendor mode (direct imports)
    export LENDING_MODE=vendor
    python -m src.api.gateway

    # Hosted service mode (HTTP calls)
    export LENDING_MODE=hosted
    export COLLATERAL_ANALYZER_URL=http://localhost:8001
    export RATE_CALCULATOR_URL=http://localhost:8002
    export LOAN_EVALUATOR_URL=http://localhost:8003
    export RISK_ASSESSOR_URL=http://localhost:8004
    python -m src.api.gateway
"""

from .gateway import app, APIGateway
from .service_discovery import ServiceDiscovery, ServiceMode, ServiceInfo
from .health_checks import HealthChecker, HealthStatus
from .websocket_handler import WebSocketManager, MessageType

__version__ = "1.0.0"
__author__ = "Algorand Lending Platform Team"

__all__ = [
    "app",
    "APIGateway",
    "ServiceDiscovery",
    "ServiceMode",
    "ServiceInfo",
    "HealthChecker",
    "HealthStatus",
    "WebSocketManager",
    "MessageType"
]