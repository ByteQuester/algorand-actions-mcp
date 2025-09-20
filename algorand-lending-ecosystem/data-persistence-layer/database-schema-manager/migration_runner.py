"""
Migration Runner

Handles database schema migrations with rollback capabilities.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .connection_factory import ConnectionFactory, DatabaseConfig


class MigrationError(Exception):
    """Raised when migration fails"""
    pass


class Migration:
    """Represents a single database migration"""

    def __init__(self, version: int, description: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql

    @classmethod
    def from_file(cls, migration_file: Path) -> 'Migration':
        """Create migration from SQL file"""
        content = migration_file.read_text()

        # Extract version from filename (e.g., 001_initial_schema.sql)
        version_match = re.match(r'(\d+)_.*\.sql$', migration_file.name)
        if not version_match:
            raise MigrationError(f"Invalid migration filename: {migration_file.name}")

        version = int(version_match.group(1))

        # Split content into up and down migrations
        if '-- DOWN' in content:
            parts = content.split('-- DOWN', 1)
            up_sql = parts[0].replace('-- UP', '').strip()
            down_sql = parts[1].strip()
        else:
            up_sql = content.replace('-- UP', '').strip()
            down_sql = ""

        # Extract description from comment or filename
        description_match = re.search(r'-- Description: (.+)', content)
        if description_match:
            description = description_match.group(1).strip()
        else:
            description = migration_file.stem.replace(f'{version:03d}_', '').replace('_', ' ')

        return cls(version, description, up_sql, down_sql)


class MigrationRunner:
    """Runs database migrations"""

    def __init__(self, db_path: Path, migrations_dir: Path, config: Optional[DatabaseConfig] = None):
        self.db_path = Path(db_path)
        self.migrations_dir = Path(migrations_dir)
        self.connection_factory = ConnectionFactory(db_path, config)

    def get_available_migrations(self) -> List[Migration]:
        """Get all available migrations from migrations directory"""
        migrations = []

        if not self.migrations_dir.exists():
            return migrations

        for migration_file in sorted(self.migrations_dir.glob('*.sql')):
            try:
                migration = Migration.from_file(migration_file)
                migrations.append(migration)
            except MigrationError as e:
                print(f"Warning: Skipping invalid migration file {migration_file}: {e}")

        return sorted(migrations, key=lambda m: m.version)

    def get_applied_migrations(self) -> List[int]:
        """Get list of applied migration versions"""
        try:
            results = self.connection_factory.fetch_all(
                "SELECT version FROM schema_versions ORDER BY version"
            )
            return [row['version'] for row in results]
        except Exception:
            # Schema versions table doesn't exist yet
            return []

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied yet"""
        available = self.get_available_migrations()
        applied = set(self.get_applied_migrations())

        return [m for m in available if m.version not in applied]

    def migrate_up(self, target_version: Optional[int] = None) -> List[Migration]:
        """Run migrations up to target version (or all if None)"""
        pending = self.get_pending_migrations()

        if target_version:
            pending = [m for m in pending if m.version <= target_version]

        applied_migrations = []

        for migration in pending:
            try:
                self._apply_migration(migration)
                applied_migrations.append(migration)
                print(f"Applied migration {migration.version}: {migration.description}")
            except Exception as e:
                raise MigrationError(f"Failed to apply migration {migration.version}: {e}")

        return applied_migrations

    def migrate_down(self, target_version: int) -> List[Migration]:
        """Roll back migrations to target version"""
        applied = self.get_applied_migrations()
        to_rollback = [v for v in applied if v > target_version]
        to_rollback.sort(reverse=True)  # Rollback in reverse order

        available_migrations = {m.version: m for m in self.get_available_migrations()}
        rolled_back = []

        for version in to_rollback:
            if version not in available_migrations:
                raise MigrationError(f"Cannot rollback migration {version}: migration file not found")

            migration = available_migrations[version]
            if not migration.down_sql:
                raise MigrationError(f"Cannot rollback migration {version}: no down migration defined")

            try:
                self._rollback_migration(migration)
                rolled_back.append(migration)
                print(f"Rolled back migration {migration.version}: {migration.description}")
            except Exception as e:
                raise MigrationError(f"Failed to rollback migration {migration.version}: {e}")

        return rolled_back

    def _apply_migration(self, migration: Migration) -> None:
        """Apply a single migration"""
        # Execute the migration SQL
        statements = self._split_sql_statements(migration.up_sql)

        with self.connection_factory.get_connection() as conn:
            cursor = conn.cursor()
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)

            # Record the migration
            cursor.execute(
                "INSERT INTO schema_versions (version, description) VALUES (?, ?)",
                (migration.version, migration.description)
            )
            conn.commit()

    def _rollback_migration(self, migration: Migration) -> None:
        """Rollback a single migration"""
        statements = self._split_sql_statements(migration.down_sql)

        with self.connection_factory.get_connection() as conn:
            cursor = conn.cursor()
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)

            # Remove the migration record
            cursor.execute(
                "DELETE FROM schema_versions WHERE version = ?",
                (migration.version,)
            )
            conn.commit()

    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL content into individual statements"""
        # Simple statement splitting - this could be enhanced for complex SQL
        statements = []
        current_statement = ""

        for line in sql.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                current_statement += line + '\n'
                if line.endswith(';'):
                    statements.append(current_statement.strip())
                    current_statement = ""

        if current_statement.strip():
            statements.append(current_statement.strip())

        return statements

    def create_migration_file(self, description: str, up_sql: str, down_sql: str = "") -> Path:
        """Create a new migration file"""
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

        # Get next version number
        existing_migrations = self.get_available_migrations()
        next_version = max([m.version for m in existing_migrations], default=0) + 1

        # Create filename
        safe_description = re.sub(r'[^a-zA-Z0-9_]', '_', description.lower())
        filename = f"{next_version:03d}_{safe_description}.sql"
        migration_file = self.migrations_dir / filename

        # Create migration content
        content = f"-- Description: {description}\n-- UP\n{up_sql}\n"
        if down_sql:
            content += f"\n-- DOWN\n{down_sql}\n"

        migration_file.write_text(content)
        return migration_file