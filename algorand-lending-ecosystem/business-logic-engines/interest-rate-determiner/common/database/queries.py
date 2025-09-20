"""
Query builder and common queries for DeFi database operations.

Provides type-safe query builders and optimized queries for common operations.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


class QueryBuilder:
    """SQL query builder for DeFi database operations"""

    @staticmethod
    def select(table: str, columns: List[str] = None) -> 'SelectQuery':
        """Start building a SELECT query"""
        return SelectQuery(table, columns or ["*"])

    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> str:
        """Build INSERT query"""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        columns_str = ", ".join(columns)

        return f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

    @staticmethod
    def update(table: str, data: Dict[str, Any], where_clause: str) -> str:
        """Build UPDATE query"""
        set_clauses = [f"{col} = %s" for col in data.keys()]
        set_str = ", ".join(set_clauses)

        return f"UPDATE {table} SET {set_str} WHERE {where_clause}"

    @staticmethod
    def delete(table: str, where_clause: str) -> str:
        """Build DELETE query"""
        return f"DELETE FROM {table} WHERE {where_clause}"


@dataclass
class SelectQuery:
    """SELECT query builder"""
    table: str
    columns: List[str]
    where_conditions: List[str] = None
    joins: List[str] = None
    order_by: List[str] = None
    group_by: List[str] = None
    having: List[str] = None
    limit_count: Optional[int] = None
    offset_count: Optional[int] = None

    def __post_init__(self):
        if self.where_conditions is None:
            self.where_conditions = []
        if self.joins is None:
            self.joins = []
        if self.order_by is None:
            self.order_by = []
        if self.group_by is None:
            self.group_by = []
        if self.having is None:
            self.having = []

    def where(self, condition: str) -> 'SelectQuery':
        """Add WHERE condition"""
        self.where_conditions.append(condition)
        return self

    def join(self, join_clause: str) -> 'SelectQuery':
        """Add JOIN clause"""
        self.joins.append(join_clause)
        return self

    def order(self, column: str, direction: str = "ASC") -> 'SelectQuery':
        """Add ORDER BY clause"""
        self.order_by.append(f"{column} {direction}")
        return self

    def group(self, column: str) -> 'SelectQuery':
        """Add GROUP BY clause"""
        self.group_by.append(column)
        return self

    def limit(self, count: int) -> 'SelectQuery':
        """Add LIMIT clause"""
        self.limit_count = count
        return self

    def offset(self, count: int) -> 'SelectQuery':
        """Add OFFSET clause"""
        self.offset_count = count
        return self

    def build(self) -> str:
        """Build the SQL query"""
        query_parts = []

        # SELECT clause
        columns_str = ", ".join(self.columns)
        query_parts.append(f"SELECT {columns_str}")

        # FROM clause
        query_parts.append(f"FROM {self.table}")

        # JOIN clauses
        for join in self.joins:
            query_parts.append(join)

        # WHERE clause
        if self.where_conditions:
            where_str = " AND ".join(self.where_conditions)
            query_parts.append(f"WHERE {where_str}")

        # GROUP BY clause
        if self.group_by:
            group_str = ", ".join(self.group_by)
            query_parts.append(f"GROUP BY {group_str}")

        # HAVING clause
        if self.having:
            having_str = " AND ".join(self.having)
            query_parts.append(f"HAVING {having_str}")

        # ORDER BY clause
        if self.order_by:
            order_str = ", ".join(self.order_by)
            query_parts.append(f"ORDER BY {order_str}")

        # LIMIT clause
        if self.limit_count:
            query_parts.append(f"LIMIT {self.limit_count}")

        # OFFSET clause
        if self.offset_count:
            query_parts.append(f"OFFSET {self.offset_count}")

        return " ".join(query_parts)


class AsaQueries:
    """Common queries for ASA price data"""

    @staticmethod
    def get_latest_price(asset_id: int) -> str:
        """Get latest price for an ASA"""
        return (QueryBuilder
                .select("asa_price_history")
                .where(f"asset_id = {asset_id}")
                .order("timestamp", "DESC")
                .limit(1)
                .build())

    @staticmethod
    def get_price_history(asset_id: int, days: int = 30) -> str:
        """Get price history for specified period"""
        return (QueryBuilder
                .select("asa_price_history")
                .where(f"asset_id = {asset_id}")
                .where(f"timestamp >= NOW() - INTERVAL '{days} days'")
                .order("timestamp", "ASC")
                .build())

    @staticmethod
    def get_volatility_data(asset_id: int, days: int = 30) -> str:
        """Get volatility data for analysis"""
        return (QueryBuilder
                .select("asa_price_history", [
                    "timestamp",
                    "price_algo",
                    "price_usd",
                    "volatility_24h",
                    "price_change_24h"
                ])
                .where(f"asset_id = {asset_id}")
                .where(f"timestamp >= NOW() - INTERVAL '{days} days'")
                .where("volatility_24h IS NOT NULL")
                .order("timestamp", "ASC")
                .build())


class DeFiQueries:
    """Common queries for DeFi protocol data"""

    @staticmethod
    def get_latest_yields(protocol_name: str) -> str:
        """Get latest yields for a protocol"""
        return (QueryBuilder
                .select("defi_protocol_yields")
                .where(f"protocol_name = '{protocol_name}'")
                .where("timestamp = (SELECT MAX(timestamp) FROM defi_protocol_yields WHERE protocol_name = '%s')")
                .build())

    @staticmethod
    def get_yield_history(protocol_name: str, asset_id: int, days: int = 30) -> str:
        """Get yield history for protocol and asset"""
        return (QueryBuilder
                .select("defi_protocol_yields")
                .where(f"protocol_name = '{protocol_name}'")
                .where(f"asset_id = {asset_id}")
                .where(f"timestamp >= NOW() - INTERVAL '{days} days'")
                .order("timestamp", "ASC")
                .build())

    @staticmethod
    def get_best_yields_for_asset(asset_id: int) -> str:
        """Get best current yields across all protocols for an asset"""
        return """
        WITH latest_yields AS (
            SELECT DISTINCT ON (protocol_name)
                protocol_name, asset_id, supply_apy, borrow_apy, total_apy, timestamp
            FROM defi_protocol_yields
            WHERE asset_id = %s
            ORDER BY protocol_name, timestamp DESC
        )
        SELECT * FROM latest_yields
        ORDER BY total_apy DESC NULLS LAST
        """


class ReputationQueries:
    """Common queries for reputation data"""

    @staticmethod
    def get_latest_reputation(address: str) -> str:
        """Get latest reputation score for address"""
        return (QueryBuilder
                .select("reputation_score_history")
                .where(f"address = '{address}'")
                .order("timestamp", "DESC")
                .limit(1)
                .build())

    @staticmethod
    def get_reputation_trend(address: str, days: int = 90) -> str:
        """Get reputation trend over time"""
        return (QueryBuilder
                .select("reputation_score_history", [
                    "timestamp",
                    "overall_score",
                    "reputation_tier",
                    "confidence_level"
                ])
                .where(f"address = '{address}'")
                .where(f"timestamp >= NOW() - INTERVAL '{days} days'")
                .order("timestamp", "ASC")
                .build())

    @staticmethod
    def get_reputation_distribution() -> str:
        """Get distribution of reputation scores"""
        return """
        SELECT
            reputation_tier,
            COUNT(*) as count,
            AVG(overall_score) as avg_score,
            MIN(overall_score) as min_score,
            MAX(overall_score) as max_score
        FROM (
            SELECT DISTINCT ON (address)
                address, overall_score, reputation_tier
            FROM reputation_score_history
            ORDER BY address, timestamp DESC
        ) latest_scores
        GROUP BY reputation_tier
        ORDER BY
            CASE reputation_tier
                WHEN 'diamond' THEN 1
                WHEN 'platinum' THEN 2
                WHEN 'gold' THEN 3
                WHEN 'silver' THEN 4
                WHEN 'bronze' THEN 5
                ELSE 6
            END
        """


class NetworkQueries:
    """Common queries for network activity data"""

    @staticmethod
    def get_latest_network_stats() -> str:
        """Get latest network activity statistics"""
        return (QueryBuilder
                .select("network_activity_history")
                .order("timestamp", "DESC")
                .limit(1)
                .build())

    @staticmethod
    def get_network_trends(days: int = 7) -> str:
        """Get network activity trends"""
        return (QueryBuilder
                .select("network_activity_history", [
                    "timestamp",
                    "total_transactions",
                    "transactions_per_second",
                    "average_block_utilization",
                    "defi_transaction_ratio",
                    "network_health_score"
                ])
                .where(f"timestamp >= NOW() - INTERVAL '{days} days'")
                .order("timestamp", "ASC")
                .build())

    @staticmethod
    def get_capacity_utilization() -> str:
        """Get network capacity utilization over time"""
        return """
        SELECT
            DATE_TRUNC('hour', timestamp) as hour,
            AVG(average_block_utilization) as avg_utilization,
            MAX(peak_tps) as max_tps,
            AVG(transactions_per_second) as avg_tps
        FROM network_activity_history
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', timestamp)
        ORDER BY hour
        """