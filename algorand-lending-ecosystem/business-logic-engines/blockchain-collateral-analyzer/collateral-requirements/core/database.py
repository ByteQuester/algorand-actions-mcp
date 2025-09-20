"""
Collateral Requirements Database

SQLite database for storing collateral analysis inputs, outputs, and historical data.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Database path within the collateral-requirements module
DB_PATH = Path(__file__).parent / "collateral_analysis.db"


class CollateralDatabase:
    """Database manager for collateral analysis data"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collateral_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    market_conditions TEXT,
                    oracle_data_timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

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
                    liquidity_tier TEXT,
                    collateral_haircut REAL,
                    adjusted_collateral_value REAL,
                    oracle_source TEXT,
                    oracle_confidence REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES collateral_analyses (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    asset_symbol TEXT NOT NULL,
                    price_usd REAL NOT NULL,
                    volume_24h_usd REAL,
                    market_cap_usd REAL,
                    volatility_30d REAL,
                    oracle_source TEXT,
                    confidence_score REAL,
                    data_timestamp TIMESTAMP NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(asset_id, data_timestamp)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS liquidation_scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    scenario_name TEXT NOT NULL,
                    price_drop_percentage REAL NOT NULL,
                    estimated_liquidation_value REAL,
                    liquidation_time_hours REAL,
                    slippage_percentage REAL,
                    gas_costs_usd REAL,
                    net_recovery_percentage REAL,
                    scenario_probability REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES collateral_analyses (id)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collateral_loan_id ON collateral_analyses(loan_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collateral_timestamp ON collateral_analyses(analysis_timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_asset_valuations_analysis ON asset_valuations(analysis_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_market_data_asset ON market_data_cache(asset_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data_cache(data_timestamp)")

            conn.commit()

    def store_collateral_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """Store a complete collateral analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Store main analysis
            cursor.execute("""
                INSERT INTO collateral_analyses (
                    loan_id, loan_amount_usd, borrower_address, analysis_input,
                    analysis_output, confidence_score, risk_level,
                    required_collateral_ratio, total_collateral_value_usd,
                    market_conditions, oracle_data_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_data.get('loan_id'),
                analysis_data['loan_amount_usd'],
                analysis_data.get('borrower_address'),
                json.dumps(analysis_data.get('input_parameters', {})),
                json.dumps(analysis_data.get('analysis_results', {})),
                analysis_data.get('confidence_score'),
                analysis_data.get('risk_level'),
                analysis_data.get('required_collateral_ratio'),
                analysis_data.get('total_collateral_value_usd'),
                analysis_data.get('market_conditions', 'normal'),
                analysis_data.get('oracle_data_timestamp')
            ))

            analysis_id = cursor.lastrowid

            # Store asset valuations
            if 'asset_valuations' in analysis_data:
                for asset in analysis_data['asset_valuations']:
                    cursor.execute("""
                        INSERT INTO asset_valuations (
                            analysis_id, asset_id, asset_symbol, asset_type,
                            current_price_usd, position_size, position_value_usd,
                            volatility_30d, volatility_7d, liquidity_tier,
                            collateral_haircut, adjusted_collateral_value,
                            oracle_source, oracle_confidence
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id,
                        asset['asset_id'],
                        asset['asset_symbol'],
                        asset['asset_type'],
                        asset['current_price_usd'],
                        asset['position_size'],
                        asset['position_value_usd'],
                        asset.get('volatility_30d'),
                        asset.get('volatility_7d'),
                        asset.get('liquidity_tier'),
                        asset.get('collateral_haircut'),
                        asset.get('adjusted_collateral_value'),
                        asset.get('oracle_source'),
                        asset.get('oracle_confidence')
                    ))

            # Store liquidation scenarios
            if 'liquidation_scenarios' in analysis_data:
                for scenario in analysis_data['liquidation_scenarios']:
                    cursor.execute("""
                        INSERT INTO liquidation_scenarios (
                            analysis_id, scenario_name, price_drop_percentage,
                            estimated_liquidation_value, liquidation_time_hours,
                            slippage_percentage, gas_costs_usd,
                            net_recovery_percentage, scenario_probability
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id,
                        scenario['scenario_name'],
                        scenario['price_drop_percentage'],
                        scenario['estimated_liquidation_value'],
                        scenario.get('liquidation_time_hours'),
                        scenario.get('slippage_percentage'),
                        scenario.get('gas_costs_usd'),
                        scenario.get('net_recovery_percentage'),
                        scenario.get('scenario_probability')
                    ))

            conn.commit()
            return analysis_id

    def get_collateral_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a collateral analysis by ID"""
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

            return result

    def get_recent_analyses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent collateral analyses"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM collateral_analyses
                ORDER BY analysis_timestamp DESC
                LIMIT ?
            """, (limit,))

            analyses = []
            for row in cursor.fetchall():
                analysis = dict(row)
                analysis['analysis_input'] = json.loads(analysis['analysis_input'] or '{}')
                analysis['analysis_output'] = json.loads(analysis['analysis_output'] or '{}')
                analyses.append(analysis)

            return analyses

    def cache_market_data(self, asset_id: str, asset_symbol: str, market_data: Dict[str, Any]):
        """Cache market data for an asset"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO market_data_cache (
                    asset_id, asset_symbol, price_usd, volume_24h_usd,
                    market_cap_usd, volatility_30d, oracle_source,
                    confidence_score, data_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id,
                asset_symbol,
                market_data['price_usd'],
                market_data.get('volume_24h_usd'),
                market_data.get('market_cap_usd'),
                market_data.get('volatility_30d'),
                market_data.get('oracle_source'),
                market_data.get('confidence_score'),
                market_data.get('data_timestamp', datetime.now())
            ))
            conn.commit()

    def get_cached_market_data(self, asset_id: str, max_age_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """Get cached market data if fresh enough"""
        with sqlite3.connect(self.db_path) as conn:
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

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored analyses"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            stats = {}

            # Total analyses
            cursor.execute("SELECT COUNT(*) as count FROM collateral_analyses")
            stats['total_analyses'] = cursor.fetchone()['count']

            # Analyses by risk level
            cursor.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM collateral_analyses
                WHERE risk_level IS NOT NULL
                GROUP BY risk_level
            """)
            stats['risk_level_distribution'] = {row['risk_level']: row['count'] for row in cursor.fetchall()}

            # Average collateral ratios
            cursor.execute("""
                SELECT AVG(required_collateral_ratio) as avg_ratio
                FROM collateral_analyses
                WHERE required_collateral_ratio IS NOT NULL
            """)
            avg_ratio = cursor.fetchone()['avg_ratio']
            stats['average_collateral_ratio'] = round(avg_ratio, 3) if avg_ratio else None

            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM collateral_analyses
                WHERE analysis_timestamp > datetime('now', '-24 hours')
            """)
            stats['analyses_last_24h'] = cursor.fetchone()['count']

            return stats