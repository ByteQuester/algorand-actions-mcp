"""
Connection Factory for Loan Repository

Reuses the connection factory from database-schema-manager with repository-specific
configuration and error handling.
"""

from pathlib import Path
from typing import Optional

# Import from parent module
import sys
sys.path.append(str(Path(__file__).parent.parent / "database-schema-manager"))

from connection_factory import ConnectionFactory as BaseConnectionFactory, DatabaseConfig, DatabaseConnectionError

__all__ = ['ConnectionFactory', 'DatabaseConfig', 'DatabaseConnectionError']

# Re-export the connection factory for use in this module
ConnectionFactory = BaseConnectionFactory