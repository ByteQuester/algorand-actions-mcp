"""
Data Pipeline Package - Comprehensive real-time data pipeline for Algorand lending platform

This package provides:
- MCP service connectivity and management
- Real-time data aggregation from multiple sources
- Intelligent caching with multiple backends
- Performance optimization and monitoring
- Unified data interface for lending engines

Usage:
    from src.data_pipeline import get_mcp_connector, get_data_aggregator, get_cache_manager

    # Initialize pipeline
    connector = await get_mcp_connector()
    aggregator = await get_data_aggregator()
    cache = await get_cache_manager()

    # Use services
    account_data = await aggregator.get_account_data("ALGORAND_ADDRESS")
    market_data = await aggregator.get_market_data([0, 31566704])
"""

from .mcp_connector import (
    MCPConnector,
    MCPServiceType,
    MCPServiceConfig,
    MCPRequest,
    MCPResponse,
    ServiceHealthStatus,
    get_mcp_connector,
    close_mcp_connector
)

from .data_aggregator import (
    DataAggregator,
    DataType,
    AggregationStrategy,
    DataPoint,
    AggregatedData,
    SubscriptionConfig,
    get_data_aggregator,
    close_data_aggregator
)

from .cache_manager import (
    CacheManager,
    CacheBackend,
    EvictionPolicy,
    CacheEntry,
    CacheStats,
    MemoryCache,
    FileCache,
    get_cache_manager,
    close_cache_manager
)

__version__ = "1.0.0"
__author__ = "Algorand Showcase"
__description__ = "Real-time data pipeline for Algorand lending platform"

__all__ = [
    # MCP Connector
    "MCPConnector",
    "MCPServiceType",
    "MCPServiceConfig",
    "MCPRequest",
    "MCPResponse",
    "ServiceHealthStatus",
    "get_mcp_connector",
    "close_mcp_connector",

    # Data Aggregator
    "DataAggregator",
    "DataType",
    "AggregationStrategy",
    "DataPoint",
    "AggregatedData",
    "SubscriptionConfig",
    "get_data_aggregator",
    "close_data_aggregator",

    # Cache Manager
    "CacheManager",
    "CacheBackend",
    "EvictionPolicy",
    "CacheEntry",
    "CacheStats",
    "MemoryCache",
    "FileCache",
    "get_cache_manager",
    "close_cache_manager"
]