"""
Database Connection Factory

Provides centralized connection management with pooling, retries, and error handling.
"""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    max_connections: int = 20
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    backup_on_startup: bool = True


class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass


class ConnectionFactory:
    """Factory for creating and managing database connections"""

    def __init__(self, db_path: Path, config: Optional[DatabaseConfig] = None):
        self.db_path = Path(db_path)
        self.config = config or DatabaseConfig()
        self._ensure_database_directory()

    def _ensure_database_directory(self) -> None:
        """Ensure the database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        for attempt in range(self.config.retry_attempts):
            try:
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=self.config.connection_timeout
                )
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                yield conn
                return
            except sqlite3.Error as e:
                if conn:
                    conn.close()
                if attempt == self.config.retry_attempts - 1:
                    raise DatabaseConnectionError(f"Failed to connect to database after {self.config.retry_attempts} attempts: {e}")
                time.sleep(self.config.retry_delay * (attempt + 1))
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query with connection management"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def execute_many(self, query: str, params_list) -> None:
        """Execute multiple queries in a transaction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dictionary"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> list[Dict[str, Any]]:
        """Fetch all rows as a list of dictionaries"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def backup_database(self, backup_path: Path) -> None:
        """Create a backup of the database"""
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as source:
            with sqlite3.connect(str(backup_path)) as backup:
                source.backup(backup)