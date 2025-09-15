"""
Algorand A2A Lending Core
Pure lending business logic - vendorable package
NO production config, NO environment variables
"""

from .lending_engine import LendingEngine
from .models import (
    LoanRequest,
    LoanResult,
    LoanStatus,
    CollateralType,
    LoanTerms,
    AgentResult,
    AccountBalance,
    MCPServiceConfig
)
from .agents import (
    NegotiationAgent,
    LiquidityAgent,
    ExecutionAgent,
    AgentOrchestrator
)
from .api_models import (
    LoanRequestAPI,
    LoanStatusResponse,
    LoanAcceptanceAPI,
    HealthResponse,
    ErrorResponse
)
from .blockchain import BlockchainTransactionBuilder
from .error_handling import (
    LendingError,
    ErrorSeverity,
    ErrorCategory,
    ErrorHandler
)
from .workflow import LendingWorkflow
from .integrated_workflow import IntegratedLendingWorkflow

__version__ = "1.0.0"
__author__ = "Agent 2 - Lending API Team"

__all__ = [
    # Core Components
    "LendingEngine",
    "LendingWorkflow",
    "IntegratedLendingWorkflow",
    "BlockchainTransactionBuilder",
    # Models
    "LoanRequest",
    "LoanResult",
    "LoanStatus",
    "CollateralType",
    "LoanTerms",
    "AgentResult",
    "AccountBalance",
    "MCPServiceConfig",
    # Agents
    "NegotiationAgent",
    "LiquidityAgent",
    "ExecutionAgent",
    "AgentOrchestrator",
    # API Models
    "LoanRequestAPI",
    "LoanStatusResponse",
    "LoanAcceptanceAPI",
    "HealthResponse",
    "ErrorResponse",
    # Error Handling
    "LendingError",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorHandler"
]