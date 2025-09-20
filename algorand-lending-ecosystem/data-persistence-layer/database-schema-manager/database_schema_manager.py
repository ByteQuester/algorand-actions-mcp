"""
Database Schema Manager

Manages database schema creation, versioning, and migrations for the lending platform.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from .connection_factory import ConnectionFactory, DatabaseConfig


class DatabaseSchemaManager:
    """Manages database schema creation, migrations, and versioning"""

    def __init__(self, db_path: Path, config: Optional[DatabaseConfig] = None):
        self.db_path = Path(db_path)
        self.connection_factory = ConnectionFactory(db_path, config)

    def create_initial_schema(self) -> None:
        """Create initial database schema with all required tables"""
        schema_queries = [
            self._create_schema_versions_table(),
            self._create_loans_table(),
            self._create_audit_trail_table(),
            self._create_risk_assessments_table(),
            self._create_performance_indexes()
        ]

        for query in schema_queries:
            self.connection_factory.execute_query(query)

        # Record the initial schema version
        self._record_schema_version(1, "Initial schema creation")

    def get_schema_version(self) -> int:
        """Get current schema version"""
        try:
            result = self.connection_factory.fetch_one(
                "SELECT MAX(version) as version FROM schema_versions"
            )
            return result['version'] if result and result['version'] else 0
        except Exception:
            # Schema versions table doesn't exist yet
            return 0

    def _create_schema_versions_table(self) -> str:
        """Create schema versions tracking table"""
        return """
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT NOT NULL
            )
        """

    def _create_loans_table(self) -> str:
        """Create loans table with optimized schema"""
        return """
            CREATE TABLE IF NOT EXISTS loans (
                loan_id TEXT PRIMARY KEY,
                borrower_name TEXT NOT NULL,
                borrower_address TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                duration_days INTEGER NOT NULL CHECK (duration_days > 0),
                purpose TEXT,
                risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
                interest_rate REAL CHECK (interest_rate >= 0),
                collateral_required REAL CHECK (collateral_required >= 0),
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'active', 'completed', 'defaulted')),
                decision_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """

    def _create_audit_trail_table(self) -> str:
        """Create audit trail table"""
        return """
            CREATE TABLE IF NOT EXISTS audit_trail (
                event_id TEXT PRIMARY KEY,
                loan_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (loan_id) REFERENCES loans (loan_id) ON DELETE CASCADE
            )
        """

    def _create_risk_assessments_table(self) -> str:
        """Create risk assessments table"""
        return """
            CREATE TABLE IF NOT EXISTS risk_assessments (
                assessment_id TEXT PRIMARY KEY,
                loan_id TEXT NOT NULL,
                credit_score INTEGER CHECK (credit_score >= 300 AND credit_score <= 850),
                debt_to_income REAL CHECK (debt_to_income >= 0 AND debt_to_income <= 1),
                payment_history_score INTEGER CHECK (payment_history_score >= 0 AND payment_history_score <= 100),
                collateral_value REAL CHECK (collateral_value >= 0),
                final_risk_score INTEGER CHECK (final_risk_score >= 0 AND final_risk_score <= 100),
                risk_level TEXT CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'VERY HIGH')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (loan_id) REFERENCES loans (loan_id) ON DELETE CASCADE
            )
        """

    def _create_performance_indexes(self) -> str:
        """Create performance indexes"""
        return """
            CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
            CREATE INDEX IF NOT EXISTS idx_loans_created_at ON loans(created_at);
            CREATE INDEX IF NOT EXISTS idx_loans_risk_score ON loans(risk_score);
            CREATE INDEX IF NOT EXISTS idx_audit_trail_loan_id ON audit_trail(loan_id);
            CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type ON audit_trail(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail(timestamp);
            CREATE INDEX IF NOT EXISTS idx_risk_assessments_loan_id ON risk_assessments(loan_id);
            CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_level ON risk_assessments(risk_level);
        """

    def _record_schema_version(self, version: int, description: str) -> None:
        """Record a schema version"""
        self.connection_factory.execute_query(
            "INSERT OR REPLACE INTO schema_versions (version, description) VALUES (?, ?)",
            (version, description)
        )

    def validate_schema_integrity(self) -> dict:
        """Validate database schema integrity"""
        checks = {}

        # Check table existence
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = [row['name'] for row in self.connection_factory.fetch_all(tables_query)]
        required_tables = ['loans', 'audit_trail', 'risk_assessments', 'schema_versions']
        checks['tables_exist'] = all(table in tables for table in required_tables)

        # Check foreign key constraints
        fk_check = self.connection_factory.fetch_all("PRAGMA foreign_key_check")
        checks['foreign_keys_valid'] = len(fk_check) == 0

        # Check index existence
        indexes_query = "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        indexes = [row['name'] for row in self.connection_factory.fetch_all(indexes_query)]
        checks['indexes_exist'] = len(indexes) >= 8  # We create 8 indexes

        return checks

    def get_database_statistics(self) -> dict:
        """Get database statistics"""
        stats = {}

        # Table counts
        stats['loans_count'] = self.connection_factory.fetch_one("SELECT COUNT(*) as count FROM loans")['count']
        stats['audit_events_count'] = self.connection_factory.fetch_one("SELECT COUNT(*) as count FROM audit_trail")['count']
        stats['risk_assessments_count'] = self.connection_factory.fetch_one("SELECT COUNT(*) as count FROM risk_assessments")['count']

        # Database size
        stats['database_size_kb'] = self.db_path.stat().st_size / 1024 if self.db_path.exists() else 0

        # Schema version
        stats['schema_version'] = self.get_schema_version()

        return stats