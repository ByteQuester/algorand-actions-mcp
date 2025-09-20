"""
Database Migration Utilities for Audit Trail System

Comprehensive migration system supporting:
- Schema creation and updates
- Partition management
- Index optimization
- Data retention policies
- Performance monitoring
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json

try:
    import asyncpg
    from asyncpg import Connection, Pool
    ASYNCPG_AVAILABLE = True
except ImportError:
    asyncpg = None
    Connection = None
    Pool = None
    ASYNCPG_AVAILABLE = False

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class MigrationStatus(BaseModel):
    """Status of a database migration"""
    migration_id: str
    name: str
    applied_at: datetime
    checksum: str
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str
    username: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60

    @property
    def connection_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class AuditDatabaseMigrator:
    """
    High-performance migration system for audit database
    Handles schema creation, updates, partitioning, and maintenance
    """

    def __init__(self, config: DatabaseConfig):
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is required for database operations. Install with: pip install asyncpg")

        self.config = config
        self.pool: Optional[Pool] = None
        self._migrations_dir = Path(__file__).parent
        self._schema_file = self._migrations_dir / "schema.sql"

    async def initialize(self) -> None:
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.config.connection_url,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def create_migration_table(self) -> None:
        """Create migrations tracking table if it doesn't exist"""
        query = """
        CREATE TABLE IF NOT EXISTS audit_migrations (
            migration_id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            checksum VARCHAR(64) NOT NULL,
            execution_time_ms INTEGER NOT NULL,
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_audit_migrations_applied_at
        ON audit_migrations(applied_at DESC);
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query)
            logger.info("Migration tracking table created/verified")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file content"""
        if not file_path.exists():
            return ""

        content = file_path.read_text(encoding='utf-8')
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def get_applied_migrations(self) -> List[MigrationStatus]:
        """Get list of applied migrations"""
        query = """
        SELECT migration_id, name, applied_at, checksum,
               execution_time_ms, success, error_message
        FROM audit_migrations
        ORDER BY applied_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [
                MigrationStatus(
                    migration_id=row['migration_id'],
                    name=row['name'],
                    applied_at=row['applied_at'],
                    checksum=row['checksum'],
                    execution_time_ms=row['execution_time_ms'],
                    success=row['success'],
                    error_message=row['error_message']
                )
                for row in rows
            ]

    async def is_migration_applied(self, migration_id: str) -> bool:
        """Check if a specific migration has been applied"""
        query = "SELECT EXISTS(SELECT 1 FROM audit_migrations WHERE migration_id = $1 AND success = TRUE)"

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, migration_id)

    async def apply_schema_migration(self) -> bool:
        """Apply the main schema migration"""
        migration_id = "001_initial_schema"
        migration_name = "Initial Audit Database Schema"

        # Check if already applied
        if await self.is_migration_applied(migration_id):
            logger.info(f"Migration {migration_id} already applied")
            return True

        if not self._schema_file.exists():
            logger.error(f"Schema file not found: {self._schema_file}")
            return False

        schema_content = self._schema_file.read_text(encoding='utf-8')
        checksum = self._calculate_file_checksum(self._schema_file)

        start_time = datetime.now(timezone.utc)
        success = False
        error_message = None

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Execute schema creation
                    await conn.execute(schema_content)
                    success = True
                    logger.info(f"Successfully applied migration {migration_id}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to apply migration {migration_id}: {e}")
            success = False

        # Record migration status
        end_time = datetime.now(timezone.utc)
        execution_time = int((end_time - start_time).total_seconds() * 1000)

        await self._record_migration(
            migration_id=migration_id,
            name=migration_name,
            checksum=checksum,
            execution_time_ms=execution_time,
            success=success,
            error_message=error_message
        )

        return success

    async def _record_migration(
        self,
        migration_id: str,
        name: str,
        checksum: str,
        execution_time_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Record migration execution in tracking table"""
        query = """
        INSERT INTO audit_migrations
        (migration_id, name, checksum, execution_time_ms, success, error_message)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (migration_id) DO UPDATE SET
            applied_at = NOW(),
            checksum = EXCLUDED.checksum,
            execution_time_ms = EXCLUDED.execution_time_ms,
            success = EXCLUDED.success,
            error_message = EXCLUDED.error_message
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query, migration_id, name, checksum,
                execution_time_ms, success, error_message
            )

    async def create_monthly_partition(self, target_date: datetime) -> bool:
        """Create a monthly partition for the specified date"""
        try:
            async with self.pool.acquire() as conn:
                partition_name = await conn.fetchval(
                    "SELECT create_monthly_audit_partition($1)",
                    target_date.date()
                )
                logger.info(f"Created partition: {partition_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create partition for {target_date}: {e}")
            return False

    async def ensure_future_partitions(self, months_ahead: int = 6) -> int:
        """Ensure partitions exist for the next N months"""
        created_count = 0
        current_date = datetime.now(timezone.utc).replace(day=1)

        for i in range(months_ahead):
            target_date = current_date + timedelta(days=32 * i)
            target_date = target_date.replace(day=1)  # First day of month

            if await self.create_monthly_partition(target_date):
                created_count += 1

        logger.info(f"Ensured {created_count} future partitions exist")
        return created_count

    async def cleanup_old_partitions(self) -> int:
        """Clean up expired audit trails based on retention policies"""
        try:
            async with self.pool.acquire() as conn:
                deleted_count = await conn.fetchval("SELECT cleanup_expired_audit_trails()")
                logger.info(f"Cleaned up {deleted_count} expired partitions")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old partitions: {e}")
            return 0

    async def optimize_indexes(self) -> bool:
        """Reindex and optimize database indexes for better performance"""
        optimization_queries = [
            "REINDEX INDEX CONCURRENTLY idx_audit_trails_event_type;",
            "REINDEX INDEX CONCURRENTLY idx_audit_trails_event_data_gin;",
            "REINDEX INDEX CONCURRENTLY idx_decision_points_loan_id;",
            "REINDEX INDEX CONCURRENTLY idx_compliance_events_regulation;",
            "ANALYZE audit_trails;",
            "ANALYZE decision_points;",
            "ANALYZE compliance_events;",
            "ANALYZE audit_sessions;"
        ]

        try:
            async with self.pool.acquire() as conn:
                for query in optimization_queries:
                    try:
                        await conn.execute(query)
                        logger.debug(f"Executed optimization: {query}")
                    except Exception as e:
                        logger.warning(f"Optimization failed for '{query}': {e}")

                logger.info("Database optimization completed")
                return True

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats_queries = {
            "total_audit_events": "SELECT COUNT(*) FROM audit_trails",
            "events_last_24h": "SELECT COUNT(*) FROM audit_trails WHERE timestamp >= NOW() - INTERVAL '24 hours'",
            "total_decisions": "SELECT COUNT(*) FROM decision_points",
            "total_compliance_events": "SELECT COUNT(*) FROM compliance_events",
            "active_sessions": "SELECT COUNT(*) FROM audit_sessions WHERE is_active = TRUE",
            "database_size": "SELECT pg_size_pretty(pg_database_size(current_database()))",
            "audit_trails_size": "SELECT pg_size_pretty(pg_total_relation_size('audit_trails'))",
            "avg_events_per_day": """
                SELECT ROUND(COUNT(*)::numeric / GREATEST(EXTRACT(days FROM (MAX(timestamp) - MIN(timestamp))), 1), 2)
                FROM audit_trails
                WHERE timestamp >= NOW() - INTERVAL '30 days'
            """,
            "partition_count": """
                SELECT COUNT(*)
                FROM pg_tables
                WHERE tablename LIKE 'audit_trails_%'
            """,
            "top_event_types": """
                SELECT event_type, COUNT(*) as count
                FROM audit_trails
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 5
            """
        }

        stats = {}
        try:
            async with self.pool.acquire() as conn:
                for stat_name, query in stats_queries.items():
                    try:
                        if stat_name == "top_event_types":
                            rows = await conn.fetch(query)
                            stats[stat_name] = [dict(row) for row in rows]
                        else:
                            stats[stat_name] = await conn.fetchval(query)
                    except Exception as e:
                        logger.warning(f"Failed to get stat '{stat_name}': {e}")
                        stats[stat_name] = None

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

        return stats

    async def validate_database_integrity(self) -> Dict[str, bool]:
        """Validate database integrity and constraints"""
        validation_checks = {
            "foreign_key_constraints": """
                SELECT COUNT(*) = 0 FROM (
                    SELECT 1 FROM decision_points dp
                    LEFT JOIN audit_trails at ON dp.audit_event_id = at.id
                    WHERE at.id IS NULL
                    UNION ALL
                    SELECT 1 FROM compliance_events ce
                    LEFT JOIN audit_trails at ON ce.audit_event_id = at.id
                    WHERE at.id IS NULL
                ) violations
            """,
            "session_references": """
                SELECT COUNT(*) = 0 FROM (
                    SELECT 1 FROM audit_trails at
                    LEFT JOIN audit_sessions ases ON at.session_id = ases.session_id
                    WHERE at.session_id IS NOT NULL AND ases.session_id IS NULL
                ) violations
            """,
            "timestamp_consistency": """
                SELECT COUNT(*) = 0 FROM audit_trails
                WHERE timestamp > NOW() + INTERVAL '1 hour'
            """,
            "json_validity": """
                SELECT COUNT(*) = 0 FROM audit_trails
                WHERE NOT (event_data::jsonb IS NOT NULL)
            """,
            "partition_coverage": """
                SELECT COUNT(*) > 0 FROM pg_tables
                WHERE tablename LIKE 'audit_trails_' || TO_CHAR(NOW(), 'YYYY_MM')
            """
        }

        results = {}
        try:
            async with self.pool.acquire() as conn:
                for check_name, query in validation_checks.items():
                    try:
                        results[check_name] = await conn.fetchval(query)
                    except Exception as e:
                        logger.error(f"Integrity check '{check_name}' failed: {e}")
                        results[check_name] = False

        except Exception as e:
            logger.error(f"Failed to validate database integrity: {e}")
            return {}

        return results

    async def backup_audit_data(
        self,
        start_date: datetime,
        end_date: datetime,
        output_path: Path
    ) -> bool:
        """Export audit data for backup or archival"""
        export_query = """
        SELECT
            at.id,
            at.event_type,
            at.severity,
            at.timestamp,
            at.event_data,
            at.classification,
            at.correlation_id,
            at.service_name,
            at.service_version,
            dp.decision_type,
            dp.decision_outcome,
            ce.regulation_type,
            ce.compliance_status
        FROM audit_trails at
        LEFT JOIN decision_points dp ON at.id = dp.audit_event_id
        LEFT JOIN compliance_events ce ON at.id = ce.audit_event_id
        WHERE at.timestamp >= $1 AND at.timestamp <= $2
        ORDER BY at.timestamp
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(export_query, start_date, end_date)

                # Convert to JSON for export
                export_data = {
                    "export_metadata": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "export_timestamp": datetime.now(timezone.utc).isoformat(),
                        "record_count": len(rows)
                    },
                    "audit_records": [dict(row) for row in rows]
                }

                # Write to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)

                logger.info(f"Exported {len(rows)} audit records to {output_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to backup audit data: {e}")
            return False


class AuditDatabaseManager:
    """
    High-level manager for audit database operations
    Provides convenient interface for common operations
    """

    def __init__(self, config: DatabaseConfig):
        self.migrator = AuditDatabaseMigrator(config)

    async def __aenter__(self):
        await self.migrator.initialize()
        await self.migrator.create_migration_table()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.migrator.close()

    async def setup_database(self) -> bool:
        """Complete database setup including schema and initial partitions"""
        logger.info("Starting audit database setup...")

        # Apply schema migration
        if not await self.migrator.apply_schema_migration():
            logger.error("Failed to apply schema migration")
            return False

        # Create future partitions
        await self.migrator.ensure_future_partitions(12)  # 1 year ahead

        # Validate setup
        integrity_results = await self.migrator.validate_database_integrity()
        all_valid = all(integrity_results.values())

        if all_valid:
            logger.info("Database setup completed successfully")
        else:
            logger.warning(f"Database setup completed with integrity issues: {integrity_results}")

        return all_valid

    async def maintenance_cycle(self) -> Dict[str, Any]:
        """Run routine maintenance tasks"""
        logger.info("Starting maintenance cycle...")

        results = {
            "partitions_created": await self.migrator.ensure_future_partitions(6),
            "partitions_cleaned": await self.migrator.cleanup_old_partitions(),
            "optimization_success": await self.migrator.optimize_indexes(),
            "integrity_checks": await self.migrator.validate_database_integrity(),
            "database_stats": await self.migrator.get_database_stats()
        }

        logger.info("Maintenance cycle completed")
        return results

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of audit database"""
        return {
            "applied_migrations": await self.migrator.get_applied_migrations(),
            "database_stats": await self.migrator.get_database_stats(),
            "integrity_status": await self.migrator.validate_database_integrity()
        }


# Convenience functions for common operations

async def setup_audit_database(config: DatabaseConfig) -> bool:
    """Setup audit database with schema and partitions"""
    async with AuditDatabaseManager(config) as manager:
        return await manager.setup_database()

async def run_maintenance(config: DatabaseConfig) -> Dict[str, Any]:
    """Run routine maintenance on audit database"""
    async with AuditDatabaseManager(config) as manager:
        return await manager.maintenance_cycle()

async def backup_audit_data(
    config: DatabaseConfig,
    start_date: datetime,
    end_date: datetime,
    output_path: Path
) -> bool:
    """Backup audit data to file"""
    async with AuditDatabaseManager(config) as manager:
        return await manager.migrator.backup_audit_data(start_date, end_date, output_path)


# CLI support for migration operations

if __name__ == "__main__":
    import argparse
    import os
    from dotenv import load_dotenv

    load_dotenv()

    def get_db_config() -> DatabaseConfig:
        """Get database configuration from environment"""
        return DatabaseConfig(
            host=os.getenv("AUDIT_DB_HOST", "localhost"),
            port=int(os.getenv("AUDIT_DB_PORT", "5432")),
            database=os.getenv("AUDIT_DB_NAME", "audit_db"),
            username=os.getenv("AUDIT_DB_USER", "audit_user"),
            password=os.getenv("AUDIT_DB_PASSWORD", ""),
        )

    async def main():
        parser = argparse.ArgumentParser(description="Audit Database Migration Utility")
        parser.add_argument("command", choices=["setup", "maintenance", "stats", "backup"])
        parser.add_argument("--start-date", help="Start date for backup (YYYY-MM-DD)")
        parser.add_argument("--end-date", help="End date for backup (YYYY-MM-DD)")
        parser.add_argument("--output", help="Output path for backup")

        args = parser.parse_args()
        config = get_db_config()

        if args.command == "setup":
            success = await setup_audit_database(config)
            print(f"Setup {'completed' if success else 'failed'}")

        elif args.command == "maintenance":
            results = await run_maintenance(config)
            print(f"Maintenance results: {json.dumps(results, indent=2, default=str)}")

        elif args.command == "stats":
            async with AuditDatabaseManager(config) as manager:
                stats = await manager.get_health_status()
                print(f"Health status: {json.dumps(stats, indent=2, default=str)}")

        elif args.command == "backup":
            if not all([args.start_date, args.end_date, args.output]):
                print("Backup requires --start-date, --end-date, and --output")
                return

            start_date = datetime.fromisoformat(args.start_date).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)
            output_path = Path(args.output)

            success = await backup_audit_data(config, start_date, end_date, output_path)
            print(f"Backup {'completed' if success else 'failed'}")

    # Run the CLI
    asyncio.run(main())