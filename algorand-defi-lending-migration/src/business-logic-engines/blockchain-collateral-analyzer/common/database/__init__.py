"""
Common Database Module for Blockchain Collateral Analyzer

This module provides shared database utilities used across all blockchain collateral analysis engines.
"""

from .storage import (
    CollateralDatabase,
    CacheManager,
    BackupManager,
    DatabaseError,
    create_database,
    get_database_stats,
    cleanup_old_data,
)

__all__ = [
    "CollateralDatabase",
    "CacheManager",
    "BackupManager",
    "DatabaseError",
    "create_database",
    "get_database_stats",
    "cleanup_old_data",
]