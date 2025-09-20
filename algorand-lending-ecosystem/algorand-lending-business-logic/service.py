"""
Simple service wrapper for Algorand Lending Business Logic.
This provides the easiest entry point for vendoring.
"""

from algorand_lending_bl import create_lending_service

# Re-export the main service for convenience
__all__ = ['create_service']

# Simple factory function
def create_service(config=None):
    """Create a configured lending service with all engines."""
    return create_lending_service(config)