"""
Lending Platform Core - Bridge Module
This module imports from the shared lending-core package
"""

# Import everything from the shared package
import sys
import os

# Add packages directory to path if needed
packages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../packages'))
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

# Import from the shared lending-core package
from algorand_lending_core import *

# Re-export for backward compatibility
__all__ = [
    # Core Components
    "LendingEngine",
    "LendingWorkflow",
    "BlockchainInterface",
    # Models
    "LoanRequest",
    "LoanResult",
    "LoanStatus",
    "CollateralType",
    "LoanTerms",
    "AgentResult",
    "AccountBalance",
    # Agents
    "NegotiationAgent",
    "LiquidityAgent",
    "ExecutionAgent",
    "AgentOrchestrator",
    # API Models
    "LoanRequestAPI",
    "LoanResponseAPI",
    "LoanStatusAPI",
    "ValidationErrorAPI",
    # Error Handling
    "LendingError",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorHandler"
]