"""
Common Database Storage Utilities for Blockchain Collateral Analysis

Shared database operations and utilities used across all analysis engines.
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict, is_dataclass
import logging

from ..models.blockchain_collateral_models import (
    CollateralAnalysisResult,
    CollateralPortfolio,
    CollateralPosition,
    DigitalAsset,
)
from ..utils.validation import (
    validate_positive_number,
    validate_database_path,
    ValidationError,
)

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass


class CollateralDatabase:
    """
    Shared database manager for collateral analysis data across all engines.

    This class provides a unified interface for storing and retrieving
    analysis results, market data, and other shared information.
    """

    def __init__(self, db_path: Optional[Path] = None, engine_name: str = "shared"):
        """
        Initialize database connection.

        Args:
            db_path: Path to database file (None for default)
            engine_name: Name of the engine using this database
        """
        if db_path is None:
            # Default path in common directory
            db_path = Path(__file__).parent / f"collateral_analysis_{engine_name}.db"

        validate_database_path(str(db_path))

        self.db_path = Path(db_path)
        self.engine_name = engine_name
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Main analysis table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS collateral_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        engine_name TEXT NOT NULL,
                        loan_id TEXT,
                        analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        loan_amount_usd REAL NOT NULL,
                        borrower_address TEXT,
                        analysis_input TEXT,  -- JSON of input parameters
                        analysis_output TEXT, -- JSON of analysis results
                        confidence_score REAL,
                        risk_level TEXT,
                        required_collateral_ratio REAL,
                        total_collateral_value_usd REAL,
                        total_adjusted_value_usd REAL,
                        market_conditions TEXT,
                        oracle_data_timestamp TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Asset valuations table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS asset_valuations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id INTEGER,
                        asset_id TEXT NOT NULL,
                        asset_symbol TEXT NOT NULL,
                        asset_type TEXT NOT NULL,
                        current_price_usd REAL NOT NULL,
                        position_size REAL NOT NULL,
                        position_value_usd REAL NOT NULL,
                        volatility_30d REAL,
                        volatility_7d REAL,
                        max_drawdown_30d REAL,
                        value_at_risk_95 REAL,
                        correlation_with_algo REAL,
                        liquidity_tier TEXT,
                        daily_volume_usd REAL,
                        market_cap_usd REAL,
                        collateral_haircut REAL,
                        adjusted_collateral_value REAL,
                        oracle_source TEXT,
                        oracle_confidence REAL,
                        liquidation_urgency TEXT,
                        time_to_liquidate_hours REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (analysis_id) REFERENCES collateral_analyses (id)
                    )
                """)

                # Market data cache table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_data_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asset_id TEXT NOT NULL,
                        asset_symbol TEXT NOT NULL,
                        price_usd REAL NOT NULL,
                        volume_24h_usd REAL,
                        market_cap_usd REAL,
                        volatility_30d REAL,
                        volatility_7d REAL,
                        max_drawdown_30d REAL,
                        value_at_risk_95 REAL,
                        correlation_with_algo REAL,
                        liquidity_tier TEXT,
                        oracle_source TEXT,
                        confidence_score REAL,
                        staleness_score REAL,
                        data_timestamp TIMESTAMP NOT NULL,
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(asset_id, data_timestamp)
                    )
                """)

                # Liquidation scenarios table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS liquidation_scenarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id INTEGER,
                        scenario_name TEXT NOT NULL,
                        trigger_condition TEXT,
                        price_drop_percentage REAL NOT NULL,
                        estimated_liquidation_value REAL,
                        liquidation_time_hours REAL,
                        expected_slippage REAL,
                        recovery_percentage REAL,
                        market_impact TEXT,
                        gas_costs_usd REAL,
                        scenario_probability REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (analysis_id) REFERENCES collateral_analyses (id)
                    )
                """)

                # Engine-specific data table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS engine_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id INTEGER,
                        engine_name TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        data_key TEXT NOT NULL,
                        data_value TEXT,  -- JSON serialized data
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (analysis_id) REFERENCES collateral_analyses (id)
                    )
                """)

                # Performance indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_engine ON collateral_analyses(engine_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_loan_id ON collateral_analyses(loan_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON collateral_analyses(analysis_timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_valuations_analysis ON asset_valuations(analysis_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_valuations_symbol ON asset_valuations(asset_symbol)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_market_data_asset ON market_data_cache(asset_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data_cache(data_timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_engine_data_analysis ON engine_data(analysis_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_engine_data_engine ON engine_data(engine_name)")

                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}")

    def _serialize_dataclass(self, obj: Any) -> str:
        """Serialize dataclass objects to JSON string"""
        if is_dataclass(obj):
            return json.dumps(asdict(obj), default=str)
        elif isinstance(obj, dict):
            return json.dumps(obj, default=str)
        else:
            return json.dumps(obj, default=str)

    def store_analysis_result(self, result: CollateralAnalysisResult,
                            loan_id: Optional[str] = None,
                            borrower_address: Optional[str] = None) -> int:
        """
        Store a complete collateral analysis result.

        Args:
            result: Analysis result to store
            loan_id: Optional loan identifier
            borrower_address: Optional borrower address

        Returns:
            Analysis ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Store main analysis
                cursor.execute("""
                    INSERT INTO collateral_analyses (
                        engine_name, loan_id, loan_amount_usd, borrower_address,
                        analysis_input, analysis_output, confidence_score, risk_level,
                        required_collateral_ratio, total_collateral_value_usd,
                        total_adjusted_value_usd, market_conditions, oracle_data_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.engine_name,
                    loan_id,
                    result.loan_amount_usd,
                    borrower_address,
                    self._serialize_dataclass({}),  # input parameters
                    self._serialize_dataclass(result),  # full result
                    result.confidence_score,
                    result.risk_level,
                    result.required_collateral_ratio,
                    result.collateral_portfolio.total_value_usd,
                    result.collateral_portfolio.total_adjusted_value_usd,
                    result.market_conditions,
                    result.oracle_prices_timestamp
                ))

                analysis_id = cursor.lastrowid

                # Store asset valuations
                for position in result.collateral_portfolio.positions:
                    cursor.execute("""
                        INSERT INTO asset_valuations (
                            analysis_id, asset_id, asset_symbol, asset_type,
                            current_price_usd, position_size, position_value_usd,
                            volatility_30d, volatility_7d, max_drawdown_30d,
                            value_at_risk_95, correlation_with_algo, liquidity_tier,
                            daily_volume_usd, market_cap_usd, collateral_haircut,
                            adjusted_collateral_value, oracle_source, oracle_confidence,
                            liquidation_urgency, time_to_liquidate_hours
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id,
                        position.asset.asset_id,
                        position.asset.symbol,
                        position.asset.asset_type.value,
                        position.current_price_usd,
                        position.quantity,
                        position.value_usd,
                        position.asset.volatility_metrics.volatility_30d,
                        position.asset.volatility_metrics.volatility_7d,
                        position.asset.volatility_metrics.max_drawdown_30d,
                        position.asset.volatility_metrics.value_at_risk_95,
                        position.asset.volatility_metrics.correlation_with_algo,
                        position.asset.liquidity_metrics.liquidity_tier,
                        position.asset.liquidity_metrics.daily_volume_usd,
                        position.asset.liquidity_metrics.market_cap_usd,
                        position.haircut_percentage,
                        position.adjusted_value_usd,
                        position.asset.price_oracle.primary_oracle,
                        position.price_confidence,
                        position.liquidation_urgency,
                        position.time_to_liquidate_hours
                    ))

                # Store liquidation scenarios
                for scenario in result.liquidation_scenarios:
                    cursor.execute("""
                        INSERT INTO liquidation_scenarios (
                            analysis_id, scenario_name, trigger_condition,
                            estimated_liquidation_value, liquidation_time_hours,
                            expected_slippage, recovery_percentage, market_impact
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id,
                        scenario.scenario_name,
                        scenario.trigger_condition,
                        0.0,  # estimated_liquidation_value - would need calculation
                        scenario.estimated_time_hours,
                        scenario.expected_slippage,
                        scenario.recovery_percentage,
                        scenario.market_impact
                    ))

                conn.commit()
                return analysis_id

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to store analysis result: {e}")

    def get_analysis_result(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a complete analysis result by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get main analysis
                cursor.execute("SELECT * FROM collateral_analyses WHERE id = ?", (analysis_id,))
                analysis = cursor.fetchone()

                if not analysis:
                    return None

                result = dict(analysis)

                # Parse JSON fields
                result['analysis_input'] = json.loads(analysis['analysis_input'] or '{}')
                result['analysis_output'] = json.loads(analysis['analysis_output'] or '{}')

                # Get asset valuations
                cursor.execute("SELECT * FROM asset_valuations WHERE analysis_id = ?", (analysis_id,))
                result['asset_valuations'] = [dict(row) for row in cursor.fetchall()]

                # Get liquidation scenarios
                cursor.execute("SELECT * FROM liquidation_scenarios WHERE analysis_id = ?", (analysis_id,))
                result['liquidation_scenarios'] = [dict(row) for row in cursor.fetchall()]

                # Get engine-specific data
                cursor.execute("SELECT * FROM engine_data WHERE analysis_id = ?", (analysis_id,))
                engine_data = {}
                for row in cursor.fetchall():
                    key = f"{row['data_type']}.{row['data_key']}"
                    engine_data[key] = json.loads(row['data_value'] or '{}')
                result['engine_data'] = engine_data

                return result

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve analysis result: {e}")

    def store_engine_data(self, analysis_id: int, data_type: str,
                         data_key: str, data_value: Any):
        """Store engine-specific data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO engine_data (analysis_id, engine_name, data_type, data_key, data_value)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    self.engine_name,
                    data_type,
                    data_key,
                    self._serialize_dataclass(data_value)
                ))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to store engine data: {e}")


class CacheManager:
    """Manages market data and price caching across engines"""

    def __init__(self, database: CollateralDatabase):
        self.db = database

    def cache_market_data(self, asset_id: str, asset_symbol: str,
                         market_data: Dict[str, Any]):
        """Cache market data for an asset"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO market_data_cache (
                        asset_id, asset_symbol, price_usd, volume_24h_usd,
                        market_cap_usd, volatility_30d, volatility_7d,
                        max_drawdown_30d, value_at_risk_95, correlation_with_algo,
                        liquidity_tier, oracle_source, confidence_score,
                        staleness_score, data_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset_id,
                    asset_symbol,
                    market_data['price_usd'],
                    market_data.get('volume_24h_usd'),
                    market_data.get('market_cap_usd'),
                    market_data.get('volatility_30d'),
                    market_data.get('volatility_7d'),
                    market_data.get('max_drawdown_30d'),
                    market_data.get('value_at_risk_95'),
                    market_data.get('correlation_with_algo'),
                    market_data.get('liquidity_tier'),
                    market_data.get('oracle_source'),
                    market_data.get('confidence_score'),
                    market_data.get('staleness_score'),
                    market_data.get('data_timestamp', datetime.now())
                ))
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to cache market data: {e}")

    def get_cached_market_data(self, asset_id: str,
                              max_age_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """Get cached market data if fresh enough"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM market_data_cache
                    WHERE asset_id = ?
                    AND cached_at > datetime('now', '-{} minutes')
                    ORDER BY cached_at DESC
                    LIMIT 1
                """.format(max_age_minutes), (asset_id,))

                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get cached market data: {e}")


class BackupManager:
    """Manages database backups"""

    def __init__(self, database: CollateralDatabase):
        self.db = database

    def create_backup(self, backup_path: Optional[Path] = None) -> Path:
        """Create a backup of the database"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db.db_path.parent / f"backup_{timestamp}_{self.db.db_path.name}"

        try:
            shutil.copy2(self.db.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            raise DatabaseError(f"Failed to create backup: {e}")

    def restore_backup(self, backup_path: Path):
        """Restore database from backup"""
        try:
            if not backup_path.exists():
                raise DatabaseError(f"Backup file does not exist: {backup_path}")

            shutil.copy2(backup_path, self.db.db_path)
            logger.info(f"Database restored from backup: {backup_path}")
        except Exception as e:
            raise DatabaseError(f"Failed to restore backup: {e}")


# Utility functions

def create_database(db_path: Path, engine_name: str = "shared") -> CollateralDatabase:
    """Create a new database instance"""
    return CollateralDatabase(db_path, engine_name)


def get_database_stats(database: CollateralDatabase) -> Dict[str, Any]:
    """Get comprehensive database statistics"""
    try:
        with sqlite3.connect(database.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            stats = {}

            # Total analyses by engine
            cursor.execute("""
                SELECT engine_name, COUNT(*) as count
                FROM collateral_analyses
                GROUP BY engine_name
            """)
            stats['analyses_by_engine'] = {row['engine_name']: row['count'] for row in cursor.fetchall()}

            # Risk level distribution
            cursor.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM collateral_analyses
                WHERE risk_level IS NOT NULL
                GROUP BY risk_level
            """)
            stats['risk_level_distribution'] = {row['risk_level']: row['count'] for row in cursor.fetchall()}

            # Average metrics
            cursor.execute("""
                SELECT
                    AVG(required_collateral_ratio) as avg_collateral_ratio,
                    AVG(confidence_score) as avg_confidence,
                    AVG(total_collateral_value_usd) as avg_collateral_value
                FROM collateral_analyses
            """)
            row = cursor.fetchone()
            stats['averages'] = dict(row) if row else {}

            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM collateral_analyses
                WHERE analysis_timestamp > datetime('now', '-24 hours')
            """)
            stats['analyses_last_24h'] = cursor.fetchone()['count']

            # Cache statistics
            cursor.execute("SELECT COUNT(*) as count FROM market_data_cache")
            stats['cached_market_data_entries'] = cursor.fetchone()['count']

            return stats

    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get database statistics: {e}")


def cleanup_old_data(database: CollateralDatabase, days_to_keep: int = 30):
    """Clean up old data from database"""
    try:
        with sqlite3.connect(database.db_path) as conn:
            # Clean old analyses
            conn.execute("""
                DELETE FROM collateral_analyses
                WHERE analysis_timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            # Clean old cache entries
            conn.execute("""
                DELETE FROM market_data_cache
                WHERE cached_at < datetime('now', '-{} days')
            """.format(min(days_to_keep, 7)))  # Keep cache for max 7 days

            conn.commit()
            logger.info(f"Cleaned up data older than {days_to_keep} days")

    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to cleanup old data: {e}")