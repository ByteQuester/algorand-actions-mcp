"""
Lending Platform API - Bridge Module
This module imports from the shared lending-api package
"""

# Import everything from the shared package
import sys
import os

# Add packages directory to path if needed
packages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../packages'))
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

# Import from the shared lending-api package
from algorand_lending_api import *

# Re-export for backward compatibility
__all__ = [
    # API Factory
    "APIFactory",
    # Server
    "LendingAPIServer",
    # Authentication
    "AuthMiddleware",
    "JWTAuth",
    "APIKeyAuth",
    # Storage
    "StorageBackend",
    "InMemoryStorage",
    "FileStorage"
]