"""
MCP Service Connector - Unified interface for all 3 MCP services
Handles connections to Reader, Writer, and Market Data MCP services
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import websockets
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServiceType(Enum):
    READER = "reader"
    WRITER = "writer"
    MARKET_DATA = "market_data"


@dataclass
class MCPServiceConfig:
    """Configuration for an MCP service"""
    service_type: MCPServiceType
    base_url: str
    websocket_url: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class ServiceHealthStatus:
    """Health status of an MCP service"""
    service_type: MCPServiceType
    is_healthy: bool
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None


@dataclass
class MCPRequest:
    """MCP request structure"""
    method: str
    params: Dict[str, Any]
    service_type: MCPServiceType
    timeout: Optional[int] = None


@dataclass
class MCPResponse:
    """MCP response structure"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    service_type: Optional[MCPServiceType] = None
    response_time: float = 0.0


class MCPConnector:
    """
    Unified connector for all MCP services with failover and health monitoring
    """

    def __init__(self):
        self.services: Dict[MCPServiceType, MCPServiceConfig] = {}
        self.health_status: Dict[MCPServiceType, ServiceHealthStatus] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket_connections: Dict[MCPServiceType, websockets.WebSocketServerProtocol] = {}

        # Default service configurations
        self._setup_default_services()

        # Circuit breaker states
        self.circuit_breakers: Dict[MCPServiceType, Dict] = {}
        self._initialize_circuit_breakers()

    def _setup_default_services(self):
        """Setup default MCP service configurations"""
        self.services = {
            MCPServiceType.READER: MCPServiceConfig(
                service_type=MCPServiceType.READER,
                base_url="http://localhost:8002",
                websocket_url="ws://localhost:8002/ws",
                timeout=30
            ),
            MCPServiceType.WRITER: MCPServiceConfig(
                service_type=MCPServiceType.WRITER,
                base_url="http://localhost:3001",
                websocket_url="ws://localhost:3001/ws",
                timeout=30
            ),
            MCPServiceType.MARKET_DATA: MCPServiceConfig(
                service_type=MCPServiceType.MARKET_DATA,
                base_url="http://localhost:8789",
                websocket_url="ws://localhost:8789/ws",
                timeout=30
            )
        }

    def _initialize_circuit_breakers(self):
        """Initialize circuit breaker states for each service"""
        for service_type in MCPServiceType:
            self.circuit_breakers[service_type] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": None,
                "timeout": 60,  # seconds before trying again
                "failure_threshold": 5
            }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Establish connections to all MCP services"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )

        # Check health of all services
        await self.check_all_services_health()

        logger.info("MCP Connector initialized successfully")

    async def disconnect(self):
        """Close all connections"""
        if self.session:
            await self.session.close()

        # Close websocket connections
        for ws in self.websocket_connections.values():
            if ws and not ws.closed:
                await ws.close()

        self.websocket_connections.clear()
        logger.info("MCP Connector disconnected")

    def add_service(self, config: MCPServiceConfig):
        """Add or update a service configuration"""
        self.services[config.service_type] = config
        self._initialize_circuit_breaker(config.service_type)
        logger.info(f"Added MCP service: {config.service_type.value} at {config.base_url}")

    def _initialize_circuit_breaker(self, service_type: MCPServiceType):
        """Initialize circuit breaker for a specific service"""
        if service_type not in self.circuit_breakers:
            self.circuit_breakers[service_type] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "timeout": 60,
                "failure_threshold": 5
            }

    def _check_circuit_breaker(self, service_type: MCPServiceType) -> bool:
        """Check if circuit breaker allows requests"""
        breaker = self.circuit_breakers[service_type]

        if breaker["state"] == "closed":
            return True
        elif breaker["state"] == "open":
            # Check if timeout has passed
            if (breaker["last_failure_time"] and
                time.time() - breaker["last_failure_time"] > breaker["timeout"]):
                breaker["state"] = "half_open"
                return True
            return False
        elif breaker["state"] == "half_open":
            return True

        return False

    def _record_success(self, service_type: MCPServiceType):
        """Record successful request for circuit breaker"""
        breaker = self.circuit_breakers[service_type]
        breaker["failure_count"] = 0
        breaker["state"] = "closed"
        breaker["last_failure_time"] = None

    def _record_failure(self, service_type: MCPServiceType):
        """Record failed request for circuit breaker"""
        breaker = self.circuit_breakers[service_type]
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()

        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for {service_type.value}")

    async def check_service_health(self, service_type: MCPServiceType) -> ServiceHealthStatus:
        """Check health of a specific MCP service"""
        if service_type not in self.services:
            return ServiceHealthStatus(
                service_type=service_type,
                is_healthy=False,
                last_check=datetime.now(),
                response_time=0.0,
                error_message="Service not configured"
            )

        config = self.services[service_type]
        start_time = time.time()

        try:
            health_url = urljoin(config.base_url, "/health")
            async with self.session.get(health_url, timeout=5) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    status = ServiceHealthStatus(
                        service_type=service_type,
                        is_healthy=True,
                        last_check=datetime.now(),
                        response_time=response_time
                    )
                    self._record_success(service_type)
                else:
                    status = ServiceHealthStatus(
                        service_type=service_type,
                        is_healthy=False,
                        last_check=datetime.now(),
                        response_time=response_time,
                        error_message=f"HTTP {response.status}"
                    )
                    self._record_failure(service_type)

                self.health_status[service_type] = status
                return status

        except Exception as e:
            response_time = time.time() - start_time
            status = ServiceHealthStatus(
                service_type=service_type,
                is_healthy=False,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=str(e)
            )
            self.health_status[service_type] = status
            self._record_failure(service_type)
            return status

    async def check_all_services_health(self) -> Dict[MCPServiceType, ServiceHealthStatus]:
        """Check health of all configured services"""
        tasks = []
        for service_type in self.services:
            tasks.append(self.check_service_health(service_type))

        statuses = await asyncio.gather(*tasks, return_exceptions=True)

        result = {}
        for i, service_type in enumerate(self.services):
            if isinstance(statuses[i], Exception):
                result[service_type] = ServiceHealthStatus(
                    service_type=service_type,
                    is_healthy=False,
                    last_check=datetime.now(),
                    response_time=0.0,
                    error_message=str(statuses[i])
                )
            else:
                result[service_type] = statuses[i]

        return result

    async def make_request(self, request: MCPRequest) -> MCPResponse:
        """Make a request to an MCP service with retry and fallback"""
        if request.service_type not in self.services:
            return MCPResponse(
                success=False,
                error=f"Service {request.service_type.value} not configured",
                service_type=request.service_type
            )

        # Check circuit breaker
        if not self._check_circuit_breaker(request.service_type):
            return MCPResponse(
                success=False,
                error=f"Circuit breaker open for {request.service_type.value}",
                service_type=request.service_type
            )

        config = self.services[request.service_type]

        for attempt in range(config.retry_attempts):
            try:
                start_time = time.time()
                response = await self._execute_request(config, request)
                response_time = time.time() - start_time

                if response.success:
                    self._record_success(request.service_type)
                    response.response_time = response_time
                    response.service_type = request.service_type
                    return response
                else:
                    self._record_failure(request.service_type)
                    if attempt == config.retry_attempts - 1:
                        response.response_time = response_time
                        response.service_type = request.service_type
                        return response

            except Exception as e:
                self._record_failure(request.service_type)
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")

                if attempt == config.retry_attempts - 1:
                    return MCPResponse(
                        success=False,
                        error=str(e),
                        service_type=request.service_type,
                        response_time=time.time() - start_time
                    )

                await asyncio.sleep(config.retry_delay * (2 ** attempt))

        return MCPResponse(
            success=False,
            error="Max retry attempts exceeded",
            service_type=request.service_type
        )

    async def _execute_request(self, config: MCPServiceConfig, request: MCPRequest) -> MCPResponse:
        """Execute the actual HTTP request"""
        url = urljoin(config.base_url, f"/mcp/{request.method}")
        timeout = request.timeout or config.timeout

        payload = {
            "method": request.method,
            "params": request.params
        }

        async with self.session.post(
            url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        ) as response:

            if response.status == 200:
                data = await response.json()
                return MCPResponse(success=True, data=data)
            else:
                error_text = await response.text()
                return MCPResponse(
                    success=False,
                    error=f"HTTP {response.status}: {error_text}"
                )

    # Reader MCP specific methods
    async def get_account_info(self, address: str) -> MCPResponse:
        """Get account information from Reader MCP"""
        return await self.make_request(MCPRequest(
            method="get_account_info",
            params={"address": address},
            service_type=MCPServiceType.READER
        ))

    async def get_account_transactions(self, address: str, limit: int = 100) -> MCPResponse:
        """Get account transactions from Reader MCP"""
        return await self.make_request(MCPRequest(
            method="get_account_transactions",
            params={"address": address, "limit": limit},
            service_type=MCPServiceType.READER
        ))

    async def get_asset_info(self, asset_id: int) -> MCPResponse:
        """Get asset information from Reader MCP"""
        return await self.make_request(MCPRequest(
            method="get_asset_info",
            params={"asset_id": asset_id},
            service_type=MCPServiceType.READER
        ))

    async def get_application_info(self, app_id: int) -> MCPResponse:
        """Get application information from Reader MCP"""
        return await self.make_request(MCPRequest(
            method="get_application_info",
            params={"app_id": app_id},
            service_type=MCPServiceType.READER
        ))

    # Writer MCP specific methods
    async def build_payment_transaction(self, sender: str, receiver: str, amount: int) -> MCPResponse:
        """Build payment transaction using Writer MCP"""
        return await self.make_request(MCPRequest(
            method="build_payment_transaction",
            params={
                "sender": sender,
                "receiver": receiver,
                "amount": amount
            },
            service_type=MCPServiceType.WRITER
        ))

    async def simulate_transaction(self, txn_data: Dict[str, Any]) -> MCPResponse:
        """Simulate transaction using Writer MCP"""
        return await self.make_request(MCPRequest(
            method="simulate_transaction",
            params={"transaction": txn_data},
            service_type=MCPServiceType.WRITER
        ))

    async def estimate_fee(self, txn_data: Dict[str, Any]) -> MCPResponse:
        """Estimate transaction fee using Writer MCP"""
        return await self.make_request(MCPRequest(
            method="estimate_fee",
            params={"transaction": txn_data},
            service_type=MCPServiceType.WRITER
        ))

    # Market Data MCP specific methods
    async def get_asset_price(self, asset_id: int, currency: str = "USD") -> MCPResponse:
        """Get asset price from Market Data MCP"""
        return await self.make_request(MCPRequest(
            method="get_asset_price",
            params={"asset_id": asset_id, "currency": currency},
            service_type=MCPServiceType.MARKET_DATA
        ))

    async def get_defi_yields(self, protocol: Optional[str] = None) -> MCPResponse:
        """Get DeFi yields from Market Data MCP"""
        params = {}
        if protocol:
            params["protocol"] = protocol

        return await self.make_request(MCPRequest(
            method="get_defi_yields",
            params=params,
            service_type=MCPServiceType.MARKET_DATA
        ))

    async def get_market_data(self, asset_ids: List[int]) -> MCPResponse:
        """Get market data for multiple assets"""
        return await self.make_request(MCPRequest(
            method="get_market_data",
            params={"asset_ids": asset_ids},
            service_type=MCPServiceType.MARKET_DATA
        ))

    async def get_price_history(self, asset_id: int, period: str = "24h") -> MCPResponse:
        """Get price history for an asset"""
        return await self.make_request(MCPRequest(
            method="get_price_history",
            params={"asset_id": asset_id, "period": period},
            service_type=MCPServiceType.MARKET_DATA
        ))

    # WebSocket methods for real-time data
    async def subscribe_to_price_feed(self, asset_ids: List[int], callback):
        """Subscribe to real-time price feeds"""
        if MCPServiceType.MARKET_DATA not in self.services:
            raise ValueError("Market Data MCP service not configured")

        config = self.services[MCPServiceType.MARKET_DATA]
        if not config.websocket_url:
            raise ValueError("WebSocket URL not configured for Market Data MCP")

        try:
            ws = await websockets.connect(config.websocket_url)
            self.websocket_connections[MCPServiceType.MARKET_DATA] = ws

            # Subscribe to asset prices
            subscribe_msg = {
                "type": "subscribe",
                "channel": "prices",
                "asset_ids": asset_ids
            }
            await ws.send(json.dumps(subscribe_msg))

            # Listen for updates
            async for message in ws:
                try:
                    data = json.loads(message)
                    await callback(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error processing price feed: {e}")

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    # Utility methods
    def get_healthy_services(self) -> List[MCPServiceType]:
        """Get list of currently healthy services"""
        healthy = []
        for service_type, status in self.health_status.items():
            if status.is_healthy:
                healthy.append(service_type)
        return healthy

    def get_service_status(self, service_type: MCPServiceType) -> Optional[ServiceHealthStatus]:
        """Get status of a specific service"""
        return self.health_status.get(service_type)

    def is_service_healthy(self, service_type: MCPServiceType) -> bool:
        """Check if a specific service is healthy"""
        status = self.health_status.get(service_type)
        return status is not None and status.is_healthy

    async def wait_for_service(self, service_type: MCPServiceType, timeout: int = 60) -> bool:
        """Wait for a service to become healthy"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self.check_service_health(service_type)
            if status.is_healthy:
                return True
            await asyncio.sleep(1)

        return False


# Singleton instance
_mcp_connector_instance: Optional[MCPConnector] = None


async def get_mcp_connector() -> MCPConnector:
    """Get singleton MCP connector instance"""
    global _mcp_connector_instance

    if _mcp_connector_instance is None:
        _mcp_connector_instance = MCPConnector()
        await _mcp_connector_instance.connect()

    return _mcp_connector_instance


async def close_mcp_connector():
    """Close singleton MCP connector instance"""
    global _mcp_connector_instance

    if _mcp_connector_instance:
        await _mcp_connector_instance.disconnect()
        _mcp_connector_instance = None


if __name__ == "__main__":
    async def test_connector():
        """Test MCP connector functionality"""
        async with MCPConnector() as connector:
            # Check service health
            health_status = await connector.check_all_services_health()

            for service_type, status in health_status.items():
                print(f"{service_type.value}: {'✓' if status.is_healthy else '✗'} "
                      f"({status.response_time:.2f}s)")
                if not status.is_healthy:
                    print(f"  Error: {status.error_message}")

            # Test some requests if services are available
            if connector.is_service_healthy(MCPServiceType.READER):
                # Test account info
                response = await connector.get_account_info(
                    "ALGORAND_ADDRESS_HERE"  # Replace with actual address
                )
                print(f"Account info: {response.success}")

            if connector.is_service_healthy(MCPServiceType.MARKET_DATA):
                # Test asset price
                response = await connector.get_asset_price(1)  # ALGO
                print(f"Asset price: {response.success}")

    asyncio.run(test_connector())