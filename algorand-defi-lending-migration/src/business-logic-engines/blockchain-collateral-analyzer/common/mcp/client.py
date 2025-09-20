"""
Common MCP Client Utilities for Blockchain Collateral Analysis

Shared MCP service client implementations used across all analysis engines.
Provides unified access to MCP services on ports 8002 (Algorand Reader) and 8003 (Market Data).
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager

from ..utils.validation import (
    validate_url,
    validate_port,
    validate_positive_number,
    ValidationError,
)

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass


class ConnectionError(MCPError):
    """Exception for MCP connection errors."""
    pass


class TimeoutError(MCPError):
    """Exception for MCP timeout errors."""
    pass


@dataclass
class MCPServiceConfig:
    """Configuration for MCP services"""
    algorand_reader_url: str = "http://localhost:8002"
    market_data_url: str = "http://localhost:8003"
    default_timeout: float = 10.0
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_pool_size: int = 10
    rate_limit_requests_per_minute: int = 60


class MCPClient:
    """
    Unified MCP client for communicating with MCP services.

    Provides robust error handling, retry logic, and connection pooling.
    """

    def __init__(self, base_url: str, timeout: float = 10.0,
                 max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of the MCP service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        validate_url(base_url)
        validate_positive_number(timeout, "timeout")

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session: Optional[aiohttp.ClientSession] = None
        self._closed = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            self._closed = False

    async def close(self):
        """Close the client session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self._closed = True

    async def _make_request(self, method: str, endpoint: str,
                           params: Optional[Dict] = None,
                           data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            Response data or None if failed
        """
        if self._closed:
            raise MCPError("Client is closed")

        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.request(
                    method, url, params=params, json=data
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Resource not found: {url}")
                        return None
                    elif response.status >= 500 and attempt < self.max_retries:
                        # Server error, retry
                        logger.warning(f"Server error {response.status}, retrying in {self.retry_delay}s")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        logger.error(f"Request failed with status {response.status}: {url}")
                        return None

            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    logger.warning(f"Request timeout, retrying in {self.retry_delay}s")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise TimeoutError(f"Request timed out after {self.max_retries} retries: {url}")

            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    logger.warning(f"Connection error, retrying in {self.retry_delay}s: {e}")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise ConnectionError(f"Connection failed after {self.max_retries} retries: {e}")

        return None

    async def health_check(self) -> bool:
        """Check if MCP service is healthy"""
        try:
            result = await self._make_request("GET", "/health")
            return result is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.base_url}: {e}")
            return False

    async def get_asset_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get asset data from MCP service"""
        if not symbol:
            raise ValidationError("Asset symbol cannot be empty")

        try:
            return await self._make_request("GET", f"/asset/{symbol.upper()}")
        except Exception as e:
            logger.error(f"Failed to get asset data for {symbol}: {e}")
            return None

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data from MCP service"""
        if not symbol:
            raise ValidationError("Asset symbol cannot be empty")

        try:
            return await self._make_request("GET", f"/market/{symbol.upper()}")
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None

    async def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price data from MCP service"""
        if not symbol:
            raise ValidationError("Asset symbol cannot be empty")

        try:
            return await self._make_request("GET", f"/price/{symbol.upper()}")
        except Exception as e:
            logger.error(f"Failed to get price data for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get historical data from MCP service"""
        if not symbol:
            raise ValidationError("Asset symbol cannot be empty")
        validate_positive_number(days, "days")

        try:
            return await self._make_request("GET", f"/historical/{symbol.upper()}",
                                          params={"days": days})
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None

    async def get_portfolio_data(self, addresses: List[str]) -> Optional[Dict[str, Any]]:
        """Get portfolio data for multiple addresses"""
        if not addresses:
            raise ValidationError("Addresses list cannot be empty")

        try:
            return await self._make_request("POST", "/portfolio",
                                          data={"addresses": addresses})
        except Exception as e:
            logger.error(f"Failed to get portfolio data: {e}")
            return None


class MCPClientPool:
    """Pool of MCP clients for managing multiple connections"""

    def __init__(self, config: MCPServiceConfig):
        self.config = config
        self.algorand_client: Optional[MCPClient] = None
        self.market_client: Optional[MCPClient] = None
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize client pool"""
        if self._initialized:
            return

        self.algorand_client = MCPClient(
            self.config.algorand_reader_url,
            timeout=self.config.default_timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay
        )

        self.market_client = MCPClient(
            self.config.market_data_url,
            timeout=self.config.default_timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay
        )

        await self.algorand_client._ensure_session()
        await self.market_client._ensure_session()
        self._initialized = True

    async def close(self):
        """Close all clients"""
        if self.algorand_client:
            await self.algorand_client.close()
        if self.market_client:
            await self.market_client.close()
        self._initialized = False

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services"""
        if not self._initialized:
            await self.initialize()

        results = {}
        if self.algorand_client:
            results["algorand_reader"] = await self.algorand_client.health_check()
        if self.market_client:
            results["market_data"] = await self.market_client.health_check()

        return results

    async def get_comprehensive_asset_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive asset data from both services"""
        if not self._initialized:
            await self.initialize()

        # Gather data from both services concurrently
        algorand_task = self.algorand_client.get_asset_data(symbol)
        market_task = self.market_client.get_market_data(symbol)

        algorand_data, market_data = await asyncio.gather(
            algorand_task, market_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(algorand_data, Exception):
            logger.error(f"Algorand service error for {symbol}: {algorand_data}")
            algorand_data = None

        if isinstance(market_data, Exception):
            logger.error(f"Market service error for {symbol}: {market_data}")
            market_data = None

        # Combine data
        combined_data = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "algorand_data": algorand_data,
            "market_data": market_data,
            "data_sources": {
                "algorand_available": algorand_data is not None,
                "market_available": market_data is not None
            }
        }

        return combined_data


class MCPServiceManager:
    """High-level manager for MCP services with caching and rate limiting"""

    def __init__(self, config: MCPServiceConfig):
        self.config = config
        self.client_pool: Optional[MCPClientPool] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._request_timestamps: List[datetime] = []
        self.cache_ttl = timedelta(minutes=5)  # 5-minute cache TTL

    async def __aenter__(self):
        """Async context manager entry"""
        self.client_pool = MCPClientPool(self.config)
        await self.client_pool.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client_pool:
            await self.client_pool.__aexit__(exc_type, exc_val, exc_tb)

    def _is_rate_limited(self) -> bool:
        """Check if we're hitting rate limits"""
        now = datetime.now()
        # Remove requests older than 1 minute
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < timedelta(minutes=1)
        ]
        return len(self._request_timestamps) >= self.config.rate_limit_requests_per_minute

    def _add_request_timestamp(self):
        """Add timestamp for rate limiting"""
        self._request_timestamps.append(datetime.now())

    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if still valid"""
        if cache_key not in self._cache:
            return None

        timestamp = self._cache_timestamps.get(cache_key)
        if timestamp and datetime.now() - timestamp < self.cache_ttl:
            return self._cache[cache_key]

        # Cache expired
        del self._cache[cache_key]
        del self._cache_timestamps[cache_key]
        return None

    def _cache_data(self, cache_key: str, data: Dict[str, Any]):
        """Cache data with timestamp"""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()

    async def get_asset_data_with_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get asset data with caching and rate limiting"""
        cache_key = f"asset_{symbol.upper()}"

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        # Check rate limits
        if self._is_rate_limited():
            logger.warning("Rate limit reached, using cached data if available")
            return self._cache.get(cache_key)

        # Fetch fresh data
        self._add_request_timestamp()
        data = await self.client_pool.get_comprehensive_asset_data(symbol)

        if data:
            self._cache_data(cache_key, data)

        return data

    async def health_check_services(self) -> Dict[str, Any]:
        """Comprehensive health check of all services"""
        if not self.client_pool:
            return {"error": "Client pool not initialized"}

        health_results = await self.client_pool.health_check_all()

        return {
            "timestamp": datetime.now().isoformat(),
            "services": health_results,
            "all_healthy": all(health_results.values()),
            "cache_size": len(self._cache),
            "recent_requests": len(self._request_timestamps)
        }


# Utility functions

def create_mcp_client(base_url: str, **kwargs) -> MCPClient:
    """Create a new MCP client instance"""
    return MCPClient(base_url, **kwargs)


def create_service_manager(algorand_url: str = "http://localhost:8002",
                         market_url: str = "http://localhost:8003",
                         **kwargs) -> MCPServiceManager:
    """Create a new MCP service manager"""
    config = MCPServiceConfig(
        algorand_reader_url=algorand_url,
        market_data_url=market_url,
        **kwargs
    )
    return MCPServiceManager(config)


async def health_check_services(algorand_url: str = "http://localhost:8002",
                               market_url: str = "http://localhost:8003") -> Dict[str, Any]:
    """Quick health check of MCP services"""
    async with create_service_manager(algorand_url, market_url) as manager:
        return await manager.health_check_services()


@asynccontextmanager
async def mcp_client_session(base_url: str, **kwargs):
    """Context manager for MCP client sessions"""
    client = MCPClient(base_url, **kwargs)
    try:
        async with client:
            yield client
    finally:
        await client.close()