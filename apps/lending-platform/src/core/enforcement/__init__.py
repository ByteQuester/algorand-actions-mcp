"""
Backend Enforcement Module for Collateral Management
Provides programmatic enforcement via smart contracts
"""

from .models import (
    EscrowContract,
    EscrowStatus,
    EscrowDeploymentRequest,
    EscrowDeploymentResponse,
    EscrowStatusResponse,
    LiquidationRequest,
    LiquidationResponse,
    ReleaseRequest,
    ReleaseResponse,
    EscrowEvent,
    EscrowMonitoringConfig,
    TriggerStatus,
    LiquidationTrigger
)

from .smart_contracts import (
    EscrowContractTemplate,
    EscrowContractFactory
)

from .mcp_integration import (
    MCPBlockchainClient,
    MCPConfig,
    MCPTransactionBuilder
)

from .escrow_service import EscrowService
from .liquidation_monitor import LiquidationMonitor, MonitoringResult

__all__ = [
    # Models
    "EscrowContract",
    "EscrowStatus",
    "EscrowDeploymentRequest",
    "EscrowDeploymentResponse",
    "EscrowStatusResponse",
    "LiquidationRequest",
    "LiquidationResponse",
    "ReleaseRequest",
    "ReleaseResponse",
    "EscrowEvent",
    "EscrowMonitoringConfig",
    "TriggerStatus",
    "LiquidationTrigger",

    # Smart Contracts
    "EscrowContractTemplate",
    "EscrowContractFactory",

    # MCP Integration
    "MCPBlockchainClient",
    "MCPConfig",
    "MCPTransactionBuilder",

    # Services
    "EscrowService",
    "LiquidationMonitor",
    "MonitoringResult"
]