"""
Database schema definitions for DeFi interest rate determination.

Provides comprehensive schemas for storing Algorand DeFi data including
ASA pricing, protocol yields, reputation scores, and network metrics.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class DataType(Enum):
    """Database data types"""
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    DECIMAL = "DECIMAL"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    TIMESTAMP = "TIMESTAMP"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    BYTEA = "BYTEA"


class IndexType(Enum):
    """Database index types"""
    BTREE = "BTREE"
    HASH = "HASH"
    GIN = "GIN"
    GIST = "GIST"


@dataclass
class ColumnDefinition:
    """Database column definition"""
    name: str
    data_type: DataType
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: Optional[str] = None
    check_constraint: Optional[str] = None
    foreign_key: Optional[str] = None
    size: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None

    def to_sql(self) -> str:
        """Convert column definition to SQL"""
        sql_parts = [self.name]

        # Data type with size/precision
        if self.data_type in [DataType.VARCHAR, DataType.DECIMAL]:
            if self.data_type == DataType.VARCHAR:
                size = self.size or 255
                sql_parts.append(f"VARCHAR({size})")
            elif self.data_type == DataType.DECIMAL:
                precision = self.precision or 18
                scale = self.scale or 6
                sql_parts.append(f"DECIMAL({precision},{scale})")
        else:
            sql_parts.append(self.data_type.value)

        # Constraints
        if self.primary_key:
            sql_parts.append("PRIMARY KEY")
        if not self.nullable and not self.primary_key:
            sql_parts.append("NOT NULL")
        if self.unique:
            sql_parts.append("UNIQUE")
        if self.default:
            sql_parts.append(f"DEFAULT {self.default}")
        if self.check_constraint:
            sql_parts.append(f"CHECK ({self.check_constraint})")

        return " ".join(sql_parts)


@dataclass
class IndexDefinition:
    """Database index definition"""
    name: str
    table_name: str
    columns: List[str]
    index_type: IndexType = IndexType.BTREE
    unique: bool = False
    partial_condition: Optional[str] = None

    def to_sql(self) -> str:
        """Convert index definition to SQL"""
        unique_clause = "UNIQUE " if self.unique else ""
        columns_clause = ", ".join(self.columns)
        using_clause = f" USING {self.index_type.value}" if self.index_type != IndexType.BTREE else ""
        where_clause = f" WHERE {self.partial_condition}" if self.partial_condition else ""

        return (f"CREATE {unique_clause}INDEX {self.name} "
                f"ON {self.table_name}{using_clause} ({columns_clause}){where_clause}")


@dataclass
class TableDefinition:
    """Database table definition"""
    name: str
    columns: List[ColumnDefinition]
    indexes: List[IndexDefinition] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    def to_sql(self) -> str:
        """Convert table definition to SQL CREATE TABLE statement"""
        column_sql = [col.to_sql() for col in self.columns]

        # Add table constraints
        if self.constraints:
            column_sql.extend(self.constraints)

        columns_clause = ",\n    ".join(column_sql)
        return f"CREATE TABLE {self.name} (\n    {columns_clause}\n)"

    def get_index_sql(self) -> List[str]:
        """Get SQL statements for creating indexes"""
        return [index.to_sql() for index in self.indexes]


class DatabaseSchema:
    """
    Complete database schema for DeFi interest rate determination.

    Defines all tables, indexes, and constraints needed for storing
    Algorand DeFi data for rate calculation.
    """

    def __init__(self):
        self.tables = self._define_tables()

    def _define_tables(self) -> Dict[str, TableDefinition]:
        """Define all database tables"""
        tables = {}

        # ASA Price History Table
        tables["asa_price_history"] = TableDefinition(
            name="asa_price_history",
            columns=[
                ColumnDefinition("id", DataType.BIGINT, nullable=False, primary_key=True),
                ColumnDefinition("asset_id", DataType.BIGINT, nullable=False),
                ColumnDefinition("timestamp", DataType.TIMESTAMP, nullable=False),
                ColumnDefinition("price_algo", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("price_usd", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("volume_24h", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("market_cap", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("price_change_24h", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("volatility_24h", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("source", DataType.VARCHAR, nullable=False, size=50),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_asa_price_asset_timestamp", "asa_price_history",
                               ["asset_id", "timestamp"]),
                IndexDefinition("idx_asa_price_timestamp", "asa_price_history", ["timestamp"]),
                IndexDefinition("idx_asa_price_asset", "asa_price_history", ["asset_id"])
            ]
        )

        # DeFi Protocol Yields Table
        tables["defi_protocol_yields"] = TableDefinition(
            name="defi_protocol_yields",
            columns=[
                ColumnDefinition("id", DataType.BIGINT, nullable=False, primary_key=True),
                ColumnDefinition("protocol_name", DataType.VARCHAR, nullable=False, size=100),
                ColumnDefinition("asset_id", DataType.BIGINT, nullable=False),
                ColumnDefinition("timestamp", DataType.TIMESTAMP, nullable=False),
                ColumnDefinition("supply_apy", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("borrow_apy", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("reward_apy", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("total_apy", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("utilization_rate", DataType.DECIMAL, nullable=True, precision=6, scale=4),
                ColumnDefinition("total_supplied", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("total_borrowed", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("available_liquidity", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("protocol_tvl", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("metadata", DataType.JSON, nullable=True),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_defi_protocol_timestamp", "defi_protocol_yields",
                               ["protocol_name", "asset_id", "timestamp"]),
                IndexDefinition("idx_defi_timestamp", "defi_protocol_yields", ["timestamp"]),
                IndexDefinition("idx_defi_protocol", "defi_protocol_yields", ["protocol_name"])
            ]
        )

        # Reputation Score History Table
        tables["reputation_score_history"] = TableDefinition(
            name="reputation_score_history",
            columns=[
                ColumnDefinition("id", DataType.BIGINT, nullable=False, primary_key=True),
                ColumnDefinition("address", DataType.VARCHAR, nullable=False, size=58),
                ColumnDefinition("timestamp", DataType.TIMESTAMP, nullable=False),
                ColumnDefinition("overall_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("activity_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("consistency_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("defi_engagement_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("governance_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("liquidity_provision_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("risk_behavior_score", DataType.DECIMAL, nullable=False, precision=5, scale=2),
                ColumnDefinition("reputation_tier", DataType.VARCHAR, nullable=False, size=20),
                ColumnDefinition("confidence_level", DataType.DECIMAL, nullable=False, precision=4, scale=3),
                ColumnDefinition("analysis_period_days", DataType.INTEGER, nullable=False),
                ColumnDefinition("data_quality_score", DataType.DECIMAL, nullable=True, precision=4, scale=3),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_reputation_address_timestamp", "reputation_score_history",
                               ["address", "timestamp"]),
                IndexDefinition("idx_reputation_timestamp", "reputation_score_history", ["timestamp"]),
                IndexDefinition("idx_reputation_tier", "reputation_score_history", ["reputation_tier"]),
                IndexDefinition("idx_reputation_score", "reputation_score_history", ["overall_score"])
            ]
        )

        # Governance Participation History Table
        tables["governance_participation_history"] = TableDefinition(
            name="governance_participation_history",
            columns=[
                ColumnDefinition("id", DataType.BIGINT, nullable=False, primary_key=True),
                ColumnDefinition("address", DataType.VARCHAR, nullable=False, size=58),
                ColumnDefinition("period", DataType.INTEGER, nullable=False),
                ColumnDefinition("committed_algo", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("status", DataType.VARCHAR, nullable=False, size=20),
                ColumnDefinition("votes_cast", DataType.INTEGER, nullable=False, default="0"),
                ColumnDefinition("total_votes_available", DataType.INTEGER, nullable=False),
                ColumnDefinition("voting_power_used", DataType.DECIMAL, nullable=False, precision=4, scale=3),
                ColumnDefinition("rewards_earned", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("penalties_applied", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("commitment_round", DataType.BIGINT, nullable=True),
                ColumnDefinition("commitment_timestamp", DataType.TIMESTAMP, nullable=True),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_governance_address_period", "governance_participation_history",
                               ["address", "period"], unique=True),
                IndexDefinition("idx_governance_period", "governance_participation_history", ["period"]),
                IndexDefinition("idx_governance_address", "governance_participation_history", ["address"])
            ]
        )

        # Network Activity History Table
        tables["network_activity_history"] = TableDefinition(
            name="network_activity_history",
            columns=[
                ColumnDefinition("id", DataType.BIGINT, nullable=False, primary_key=True),
                ColumnDefinition("timestamp", DataType.TIMESTAMP, nullable=False),
                ColumnDefinition("measurement_period_hours", DataType.INTEGER, nullable=False, default="24"),
                ColumnDefinition("total_transactions", DataType.BIGINT, nullable=False),
                ColumnDefinition("payment_transactions", DataType.BIGINT, nullable=False),
                ColumnDefinition("app_call_transactions", DataType.BIGINT, nullable=False),
                ColumnDefinition("asset_transfer_transactions", DataType.BIGINT, nullable=False),
                ColumnDefinition("transactions_per_second", DataType.DECIMAL, nullable=False, precision=8, scale=3),
                ColumnDefinition("peak_tps", DataType.DECIMAL, nullable=False, precision=8, scale=3),
                ColumnDefinition("average_block_utilization", DataType.DECIMAL, nullable=False, precision=4, scale=3),
                ColumnDefinition("total_fees_paid", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("total_value_transferred", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("unique_active_accounts", DataType.BIGINT, nullable=False),
                ColumnDefinition("defi_transaction_ratio", DataType.DECIMAL, nullable=False, precision=4, scale=3),
                ColumnDefinition("total_defi_volume", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("network_health_score", DataType.DECIMAL, nullable=True, precision=5, scale=2),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_network_timestamp", "network_activity_history", ["timestamp"]),
                IndexDefinition("idx_network_period", "network_activity_history", ["measurement_period_hours"])
            ]
        )

        # Liquidity Pool History Table
        tables["liquidity_pool_history"] = TableDefinition(
            name="liquidity_pool_history",
            columns=[
                ColumnDefinition("id", DataType.BIGINT, nullable=False, primary_key=True),
                ColumnDefinition("pool_id", DataType.VARCHAR, nullable=False, size=100),
                ColumnDefinition("protocol", DataType.VARCHAR, nullable=False, size=50),
                ColumnDefinition("asset_a", DataType.BIGINT, nullable=False),
                ColumnDefinition("asset_b", DataType.BIGINT, nullable=False),
                ColumnDefinition("timestamp", DataType.TIMESTAMP, nullable=False),
                ColumnDefinition("reserve_a", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("reserve_b", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("total_liquidity_usd", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("volume_24h_usd", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("fee_revenue_24h", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("base_apy", DataType.DECIMAL, nullable=False, precision=8, scale=4),
                ColumnDefinition("reward_apy", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("total_apy", DataType.DECIMAL, nullable=False, precision=8, scale=4),
                ColumnDefinition("impermanent_loss_1d", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("price_impact_1pct", DataType.DECIMAL, nullable=True, precision=8, scale=4),
                ColumnDefinition("trades_24h", DataType.INTEGER, nullable=False, default="0"),
                ColumnDefinition("is_active", DataType.BOOLEAN, nullable=False, default="TRUE"),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_pool_id_timestamp", "liquidity_pool_history",
                               ["pool_id", "timestamp"]),
                IndexDefinition("idx_pool_protocol", "liquidity_pool_history", ["protocol"]),
                IndexDefinition("idx_pool_assets", "liquidity_pool_history", ["asset_a", "asset_b"]),
                IndexDefinition("idx_pool_timestamp", "liquidity_pool_history", ["timestamp"])
            ]
        )

        # Address Activity Cache Table
        tables["address_activity_cache"] = TableDefinition(
            name="address_activity_cache",
            columns=[
                ColumnDefinition("address", DataType.VARCHAR, nullable=False, primary_key=True, size=58),
                ColumnDefinition("last_updated", DataType.TIMESTAMP, nullable=False),
                ColumnDefinition("analysis_period_days", DataType.INTEGER, nullable=False),
                ColumnDefinition("total_transactions", DataType.INTEGER, nullable=False),
                ColumnDefinition("total_volume_algo", DataType.DECIMAL, nullable=False, precision=18, scale=6),
                ColumnDefinition("total_volume_usd", DataType.DECIMAL, nullable=True, precision=18, scale=6),
                ColumnDefinition("unique_protocols_used", DataType.INTEGER, nullable=False),
                ColumnDefinition("defi_transactions", DataType.INTEGER, nullable=False),
                ColumnDefinition("governance_votes_cast", DataType.INTEGER, nullable=False),
                ColumnDefinition("activity_data", DataType.JSON, nullable=True),
                ColumnDefinition("created_at", DataType.TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP")
            ],
            indexes=[
                IndexDefinition("idx_address_cache_updated", "address_activity_cache", ["last_updated"]),
                IndexDefinition("idx_address_cache_volume", "address_activity_cache", ["total_volume_usd"])
            ]
        )

        return tables

    def get_create_table_sql(self) -> List[str]:
        """Get SQL statements for creating all tables"""
        sql_statements = []

        for table in self.tables.values():
            sql_statements.append(table.to_sql())

        return sql_statements

    def get_create_index_sql(self) -> List[str]:
        """Get SQL statements for creating all indexes"""
        sql_statements = []

        for table in self.tables.values():
            sql_statements.extend(table.get_index_sql())

        return sql_statements

    def get_drop_table_sql(self) -> List[str]:
        """Get SQL statements for dropping all tables"""
        # Drop in reverse order to handle dependencies
        table_names = list(self.tables.keys())
        return [f"DROP TABLE IF EXISTS {name} CASCADE" for name in reversed(table_names)]

    def validate_schema(self) -> List[str]:
        """Validate schema definitions and return any issues"""
        issues = []

        for table_name, table in self.tables.items():
            # Check for primary key
            primary_keys = [col for col in table.columns if col.primary_key]
            if not primary_keys:
                issues.append(f"Table {table_name} has no primary key")

            # Check for duplicate column names
            column_names = [col.name for col in table.columns]
            if len(column_names) != len(set(column_names)):
                issues.append(f"Table {table_name} has duplicate column names")

            # Validate index references
            for index in table.indexes:
                for col_name in index.columns:
                    if col_name not in column_names:
                        issues.append(f"Index {index.name} references non-existent column {col_name}")

        return issues


class SchemaValidator:
    """Utility for validating database schema consistency"""

    @staticmethod
    def validate_foreign_keys(schema: DatabaseSchema) -> List[str]:
        """Validate foreign key references"""
        issues = []
        all_tables = schema.tables

        for table_name, table in all_tables.items():
            for column in table.columns:
                if column.foreign_key:
                    # Parse foreign key reference (format: "table.column")
                    if "." in column.foreign_key:
                        ref_table, ref_column = column.foreign_key.split(".", 1)

                        if ref_table not in all_tables:
                            issues.append(f"Foreign key {column.foreign_key} references non-existent table {ref_table}")
                        else:
                            ref_table_obj = all_tables[ref_table]
                            ref_columns = [col.name for col in ref_table_obj.columns]
                            if ref_column not in ref_columns:
                                issues.append(f"Foreign key {column.foreign_key} references non-existent column {ref_column}")

        return issues

    @staticmethod
    def check_naming_conventions(schema: DatabaseSchema) -> List[str]:
        """Check adherence to naming conventions"""
        issues = []

        for table_name, table in schema.tables.items():
            # Table names should be lowercase with underscores
            if not table_name.islower() or " " in table_name:
                issues.append(f"Table name '{table_name}' doesn't follow naming convention")

            for column in table.columns:
                # Column names should be lowercase with underscores
                if not column.name.islower() or " " in column.name:
                    issues.append(f"Column '{column.name}' in table '{table_name}' doesn't follow naming convention")

            for index in table.indexes:
                # Index names should follow pattern
                if not index.name.startswith("idx_"):
                    issues.append(f"Index '{index.name}' doesn't follow naming convention (should start with 'idx_')")

        return issues