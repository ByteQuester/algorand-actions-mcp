"""
Common MCP Client Module for Blockchain Collateral Analyzer

This module provides shared MCP client utilities used across all blockchain collateral analysis engines.
"""

from .client import (
    MCPClient,
    MCPClientPool,
    MCPServiceManager,
    MCPError,
    ConnectionError,
    TimeoutError,
    create_mcp_client,
    create_service_manager,
    health_check_services,
)

__all__ = [
    "MCPClient",
    "MCPClientPool",
    "MCPServiceManager",
    "MCPError",
    "ConnectionError",
    "TimeoutError",
    "create_mcp_client",
    "create_service_manager",
    "health_check_services",
]