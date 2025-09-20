"""
Database schemas and utilities for DeFi interest rate determination.

Provides database models and utilities for storing:
- ASA price and volatility history
- DeFi protocol yields and metrics
- On-chain reputation scores
- Governance participation data
- Network activity metrics
"""

from .schema import (
    DatabaseSchema,
    TableDefinition,
    IndexDefinition,
    SchemaValidator
)

from .models import (
    AsaPriceHistory,
    DeFiProtocolYields,
    ReputationScoreHistory,
    GovernanceParticipationHistory,
    NetworkActivityHistory,
    LiquidityPoolHistory
)

from .migrations import (
    MigrationManager,
    Migration,
    SchemaVersion
)

from .queries import (
    QueryBuilder,
    AsaQueries,
    DeFiQueries,
    ReputationQueries,
    NetworkQueries
)

__all__ = [
    # Schema management
    "DatabaseSchema",
    "TableDefinition",
    "IndexDefinition",
    "SchemaValidator",

    # Data models
    "AsaPriceHistory",
    "DeFiProtocolYields",
    "ReputationScoreHistory",
    "GovernanceParticipationHistory",
    "NetworkActivityHistory",
    "LiquidityPoolHistory",

    # Migration management
    "MigrationManager",
    "Migration",
    "SchemaVersion",

    # Query utilities
    "QueryBuilder",
    "AsaQueries",
    "DeFiQueries",
    "ReputationQueries",
    "NetworkQueries"
]