"""
Connection Factory for Audit Event Storage

Reuses the connection factory from database-schema-manager.
"""

from pathlib import Path

# Import from parent module
import sys
sys.path.append(str(Path(__file__).parent.parent / "database-schema-manager"))

from connection_factory import ConnectionFactory as BaseConnectionFactory, DatabaseConfig, DatabaseConnectionError

__all__ = ['ConnectionFactory', 'DatabaseConfig', 'DatabaseConnectionError']

# Re-export the connection factory for use in this module
ConnectionFactory = BaseConnectionFactory