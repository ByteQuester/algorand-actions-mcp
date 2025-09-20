"""
Database connection management for interest rate determiner.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: DatabaseType
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sqlite_path: Optional[str] = None
    connection_pool_size: int = 10
    connection_timeout: int = 30


class DatabaseConnection:
    """Database connection manager"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
        self._connection_pool = []

    def connect(self):
        """Establish database connection"""
        try:
            if self.config.db_type == DatabaseType.SQLITE:
                self._connection = self._connect_sqlite()
            elif self.config.db_type == DatabaseType.POSTGRESQL:
                self._connection = self._connect_postgresql()
            else:
                raise ValueError(f"Unsupported database type: {self.config.db_type}")

            logger.info(f"Connected to {self.config.db_type.value} database")
            return self._connection

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _connect_sqlite(self):
        """Connect to SQLite database"""
        if not self.config.sqlite_path:
            # Default to local file in current directory
            self.config.sqlite_path = "interest_rate_determiner.db"

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.config.sqlite_path)), exist_ok=True)

        connection = sqlite3.connect(
            self.config.sqlite_path,
            timeout=self.config.connection_timeout,
            check_same_thread=False
        )

        # Enable foreign key support
        connection.execute("PRAGMA foreign_keys = ON")

        # Set row factory for dict-like access
        connection.row_factory = sqlite3.Row

        return connection

    def _connect_postgresql(self):
        """Connect to PostgreSQL database"""
        connection_params = {
            'host': self.config.host or 'localhost',
            'port': self.config.port or 5432,
            'database': self.config.database or 'interest_rate_db',
            'user': self.config.username or 'postgres',
            'password': self.config.password or '',
            'connect_timeout': self.config.connection_timeout
        }

        connection = psycopg2.connect(**connection_params)
        connection.autocommit = False

        return connection

    def disconnect(self):
        """Close database connection"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._connection = None

    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """Get database cursor with automatic cleanup"""
        if not self._connection:
            self.connect()

        cursor = None
        try:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                cursor = self._connection.cursor(cursor_factory=cursor_factory or RealDictCursor)
            else:
                cursor = self._connection.cursor()

            yield cursor

        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            if self._connection:
                self._connection.rollback()
            raise

        finally:
            if cursor:
                cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """Execute SELECT query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            self._connection.commit()
            return affected_rows

    def execute_batch(self, query: str, params_list: list) -> int:
        """Execute batch INSERT/UPDATE operations"""
        with self.get_cursor() as cursor:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                from psycopg2.extras import execute_batch
                execute_batch(cursor, query, params_list)
            else:
                cursor.executemany(query, params_list)

            affected_rows = cursor.rowcount
            self._connection.commit()
            return affected_rows

    def begin_transaction(self):
        """Begin database transaction"""
        if not self._connection:
            self.connect()

        if self.config.db_type == DatabaseType.SQLITE:
            self._connection.execute("BEGIN")
        else:
            self._connection.autocommit = False

    def commit_transaction(self):
        """Commit database transaction"""
        if self._connection:
            self._connection.commit()

    def rollback_transaction(self):
        """Rollback database transaction"""
        if self._connection:
            self._connection.rollback()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        self.begin_transaction()
        try:
            yield
            self.commit_transaction()
        except Exception as e:
            self.rollback_transaction()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    def get_table_info(self, table_name: str) -> list:
        """Get table schema information"""
        if self.config.db_type == DatabaseType.SQLITE:
            query = f"PRAGMA table_info({table_name})"
        else:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """

        return self.execute_query(query, (table_name,) if self.config.db_type == DatabaseType.POSTGRESQL else ())

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        if self.config.db_type == DatabaseType.SQLITE:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            params = (table_name,)
        else:
            query = "SELECT table_name FROM information_schema.tables WHERE table_name = %s"
            params = (table_name,)

        result = self.execute_query(query, params)
        return len(result) > 0

    def get_database_size(self) -> Dict[str, Any]:
        """Get database size information"""
        if self.config.db_type == DatabaseType.SQLITE:
            # Get file size
            if os.path.exists(self.config.sqlite_path):
                size_bytes = os.path.getsize(self.config.sqlite_path)
                return {
                    'total_size_bytes': size_bytes,
                    'total_size_mb': size_bytes / (1024 * 1024)
                }
            return {'total_size_bytes': 0, 'total_size_mb': 0}

        else:
            # PostgreSQL database size
            query = """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size_pretty,
                       pg_database_size(current_database()) as size_bytes
            """
            result = self.execute_query(query)
            if result:
                return {
                    'total_size_bytes': result[0]['size_bytes'],
                    'total_size_mb': result[0]['size_bytes'] / (1024 * 1024),
                    'size_pretty': result[0]['size_pretty']
                }
            return {'total_size_bytes': 0, 'total_size_mb': 0}


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_database_connection() -> DatabaseConnection:
    """Get global database connection instance"""
    global _db_connection

    if _db_connection is None:
        # Load configuration from environment
        config = _load_database_config()
        _db_connection = DatabaseConnection(config)

    return _db_connection


def _load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables"""
    db_type_str = os.getenv('DATABASE_TYPE', 'sqlite').lower()

    if db_type_str == 'postgresql':
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=int(os.getenv('DATABASE_PORT', '5432')),
            database=os.getenv('DATABASE_NAME', 'interest_rate_db'),
            username=os.getenv('DATABASE_USER', 'postgres'),
            password=os.getenv('DATABASE_PASSWORD', ''),
            connection_pool_size=int(os.getenv('DATABASE_POOL_SIZE', '10')),
            connection_timeout=int(os.getenv('DATABASE_TIMEOUT', '30'))
        )
    else:
        # Default to SQLite
        sqlite_path = os.getenv('DATABASE_PATH', 'data/interest_rate_determiner.db')
        return DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            sqlite_path=sqlite_path,
            connection_timeout=int(os.getenv('DATABASE_TIMEOUT', '30'))
        )


def initialize_database() -> bool:
    """Initialize database with required tables"""
    try:
        db = get_database_connection()
        db.connect()

        # Import and create tables
        from .schema import create_tables
        create_tables(db)

        logger.info("Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def close_database_connection():
    """Close global database connection"""
    global _db_connection

    if _db_connection:
        _db_connection.disconnect()
        _db_connection = None