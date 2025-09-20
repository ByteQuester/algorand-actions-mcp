"""
Base Rate Calculation Engine

This engine aggregates Federal Reserve rates, Algorand DeFi protocol rates,
and Algorand staking rewards to calculate risk-free base rates for lending.
"""

import requests
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
import json
import time
from pathlib import Path

from .config import BaseRateCalculationConfig, load_config


@dataclass
class RateDataPoint:
    """Individual rate data point"""
    source: str
    rate_type: str
    value: float
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BaseRateResult:
    """Result from base rate calculation"""
    base_rate: float
    risk_free_rate: float
    term_structure: Dict[str, float]
    confidence_score: float
    component_rates: Dict[str, float]
    data_sources: List[str]
    calculation_timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FederalReserveClient:
    """Client for Federal Reserve Economic Data (FRED) API"""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.stlouisfed.org/fred"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()

    def get_series_data(self, series_id: str, limit: int = 1) -> Optional[RateDataPoint]:
        """Get latest data point for a FRED series"""
        if not self.api_key:
            # Return fallback data if no API key
            return None

        try:
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'limit': limit,
                'sort_order': 'desc'
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            observations = data.get('observations', [])

            if observations:
                latest = observations[0]
                value = float(latest['value']) / 100.0  # Convert percentage to decimal
                date = datetime.strptime(latest['date'], '%Y-%m-%d')

                return RateDataPoint(
                    source='federal_reserve',
                    rate_type=series_id,
                    value=value,
                    timestamp=date,
                    confidence=0.95,
                    metadata={'series_id': series_id, 'fred_date': latest['date']}
                )

        except Exception as e:
            logging.warning(f"Failed to fetch FRED data for {series_id}: {e}")

        return None


class AlgorandDataClient:
    """Client for Algorand blockchain and DeFi data"""

    def __init__(self, algorand_reader_url: str, market_data_url: str):
        self.algorand_reader_url = algorand_reader_url
        self.market_data_url = market_data_url
        self.session = requests.Session()

    def get_staking_rewards(self) -> Optional[RateDataPoint]:
        """Get current Algorand staking rewards rate"""
        try:
            # In practice, this would query the Algorand network for current participation rewards
            # For now, we'll return a simulated rate based on known Algorand parameters
            base_participation = 0.055  # 5.5% base participation rewards
            governance_rewards = 0.02   # 2% governance rewards
            total_apy = base_participation + governance_rewards

            return RateDataPoint(
                source='algorand_consensus',
                rate_type='staking_rewards',
                value=total_apy,
                timestamp=datetime.now(),
                confidence=0.9,
                metadata={
                    'base_participation': base_participation,
                    'governance_rewards': governance_rewards,
                    'method': 'calculated'
                }
            )

        except Exception as e:
            logging.warning(f"Failed to get Algorand staking rewards: {e}")

        return None

    def get_defi_protocol_rates(self, protocol: str) -> List[RateDataPoint]:
        """Get rates from DeFi protocols"""
        rates = []

        try:
            if protocol == 'folks_finance':
                # In practice, this would call the Folks Finance API
                # For now, we'll return simulated rates
                assets_rates = {
                    'ALGO': 0.06,
                    'USDC': 0.04,
                    'USDT': 0.04,
                    'goBTC': 0.03,
                    'goETH': 0.035
                }

                for asset, rate in assets_rates.items():
                    rates.append(RateDataPoint(
                        source='folks_finance',
                        rate_type=f'{asset}_lending',
                        value=rate,
                        timestamp=datetime.now(),
                        confidence=0.85,
                        metadata={'asset': asset, 'protocol': 'folks_finance'}
                    ))

            elif protocol == 'tinyman':
                # Tinyman LP rates
                lp_rates = {
                    'ALGO_USDC': 0.08,
                    'ALGO_USDT': 0.075,
                    'USDC_USDT': 0.03
                }

                for pair, rate in lp_rates.items():
                    rates.append(RateDataPoint(
                        source='tinyman',
                        rate_type=f'{pair}_lp',
                        value=rate,
                        timestamp=datetime.now(),
                        confidence=0.8,
                        metadata={'pair': pair, 'protocol': 'tinyman'}
                    ))

        except Exception as e:
            logging.warning(f"Failed to get DeFi rates for {protocol}: {e}")

        return rates


class TermStructureCalculator:
    """Calculate term structure and yield curves"""

    def __init__(self, config: BaseRateCalculationConfig):
        self.config = config

    def calculate_term_structure(self, base_rate: float) -> Dict[str, float]:
        """Calculate term structure based on base rate and configured premiums"""
        term_structure = {}

        term_premiums = self.config.term_structure.term_premiums

        for term, premium in term_premiums.items():
            term_rate = base_rate + premium
            term_structure[term] = max(term_rate, self.config.calculation_parameters.bounds.minimum_rate)

        return term_structure

    def interpolate_curve(self, known_points: Dict[float, float]) -> Dict[str, float]:
        """Interpolate yield curve for missing points"""
        interpolation_points = self.config.term_structure.interpolation_points

        if len(known_points) < 2:
            # Not enough points for interpolation
            return {}

        # Convert to numpy arrays for interpolation
        x_known = np.array(list(known_points.keys()))
        y_known = np.array(list(known_points.values()))

        # Interpolate at desired points
        interpolated = np.interp(interpolation_points, x_known, y_known)

        # Convert back to dictionary with term labels
        result = {}
        term_labels = ['overnight', '1_week', '1_month', '3_months', '6_months', '1_year', '2_years', '5_years', '10_years']

        for i, point in enumerate(interpolation_points):
            if i < len(term_labels):
                result[term_labels[i]] = interpolated[i]

        return result


class BaseRateCalculationEngine:
    """Main engine for calculating base interest rates"""

    def __init__(self, config: Optional[BaseRateCalculationConfig] = None):
        self.config = config or load_config()
        self.logger = self._setup_logging()

        # Initialize clients
        self.fed_client = FederalReserveClient()
        self.algorand_client = AlgorandDataClient(
            self.config.mcp_services.algorand_reader_url,
            self.config.mcp_services.market_data_url
        )
        self.term_calculator = TermStructureCalculator(self.config)

        # Initialize database
        self.db_path = Path(self.config.database.default_path)
        self._init_database()

        # Rate cache
        self.rate_cache = {}
        self.last_update = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('base_rate_calculation')
        logger.setLevel(getattr(logging, self.config.development.log_level))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _init_database(self):
        """Initialize SQLite database for storing rate history"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    source TEXT,
                    rate_type TEXT,
                    value REAL,
                    confidence REAL,
                    metadata TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS base_rate_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    base_rate REAL,
                    risk_free_rate REAL,
                    confidence_score REAL,
                    component_rates TEXT,
                    term_structure TEXT,
                    metadata TEXT
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_rate_history_timestamp
                ON rate_history(timestamp)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_base_rate_timestamp
                ON base_rate_calculations(timestamp)
            ''')

    def fetch_federal_reserve_rates(self) -> List[RateDataPoint]:
        """Fetch rates from Federal Reserve FRED API"""
        rates = []

        fed_config = self.config.federal_reserve_rates

        # Fed funds rate
        if fed_config.fed_funds_rate.enabled:
            rate = self.fed_client.get_series_data('FEDFUNDS')
            if rate:
                rates.append(rate)
            else:
                # Use fallback rate
                rates.append(RateDataPoint(
                    source='federal_reserve_fallback',
                    rate_type='FEDFUNDS',
                    value=fed_config.fed_funds_rate.fallback_rate,
                    timestamp=datetime.now(),
                    confidence=0.5
                ))

        # Treasury rates
        for rate_name, rate_config in [
            ('treasury_10y', fed_config.treasury_10y),
            ('treasury_3m', fed_config.treasury_3m),
            ('sofr_rate', fed_config.sofr_rate)
        ]:
            if rate_config.enabled:
                rate = self.fed_client.get_series_data(rate_config.series_id)
                if rate:
                    rates.append(rate)
                else:
                    rates.append(RateDataPoint(
                        source='federal_reserve_fallback',
                        rate_type=rate_config.series_id,
                        value=rate_config.fallback_rate,
                        timestamp=datetime.now(),
                        confidence=0.5
                    ))

        return rates

    def fetch_algorand_rates(self) -> List[RateDataPoint]:
        """Fetch rates from Algorand ecosystem"""
        rates = []

        # Algorand staking rewards
        staking_rate = self.algorand_client.get_staking_rewards()
        if staking_rate:
            rates.append(staking_rate)

        # DeFi protocol rates
        defi_config = self.config.algorand_defi_rates

        if defi_config.folks_finance.enabled:
            folks_rates = self.algorand_client.get_defi_protocol_rates('folks_finance')
            rates.extend(folks_rates)

        if defi_config.tinyman.enabled:
            tinyman_rates = self.algorand_client.get_defi_protocol_rates('tinyman')
            rates.extend(tinyman_rates)

        return rates

    def calculate_weighted_average(self, rates: List[RateDataPoint], weights: Dict[str, float]) -> float:
        """Calculate weighted average of rates"""
        if not rates:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for rate in rates:
            weight = weights.get(rate.source, weights.get('default', 0.1))
            weighted_sum += rate.value * weight * rate.confidence
            total_weight += weight * rate.confidence

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def calculate_confidence_score(self, rates: List[RateDataPoint]) -> float:
        """Calculate overall confidence score for the calculation"""
        if not rates:
            return 0.0

        confidence_config = self.config.calculation_parameters.confidence_scoring

        # Data freshness score
        now = datetime.now()
        freshness_scores = []
        for rate in rates:
            age_hours = (now - rate.timestamp).total_seconds() / 3600
            max_age = 48  # 48 hours max age
            freshness = max(0, 1 - (age_hours / max_age))
            freshness_scores.append(freshness)

        avg_freshness = np.mean(freshness_scores) if freshness_scores else 0

        # Source reliability score
        reliability_scores = [rate.confidence for rate in rates]
        avg_reliability = np.mean(reliability_scores) if reliability_scores else 0

        # Rate stability score (simplified - in practice would look at historical volatility)
        stability_score = 0.8  # Default stability assumption

        # Weighted final score
        final_score = (
            avg_freshness * confidence_config.data_freshness_weight +
            avg_reliability * confidence_config.source_reliability_weight +
            stability_score * confidence_config.rate_stability_weight
        )

        return min(1.0, max(0.0, final_score))

    def calculate_base_rate(self) -> BaseRateResult:
        """Calculate the base interest rate"""
        calculation_start = time.time()

        # Fetch all rate data
        fed_rates = self.fetch_federal_reserve_rates()
        algo_rates = self.fetch_algorand_rates()

        all_rates = fed_rates + algo_rates

        if not all_rates:
            # Emergency fallback
            fallback_rate = 0.05  # 5%
            return BaseRateResult(
                base_rate=fallback_rate,
                risk_free_rate=fallback_rate,
                term_structure={'1_year': fallback_rate},
                confidence_score=0.1,
                component_rates={'fallback': fallback_rate},
                data_sources=['emergency_fallback'],
                calculation_timestamp=datetime.now(),
                metadata={'calculation_time_ms': (time.time() - calculation_start) * 1000}
            )

        # Store rate data in database
        self._store_rate_data(all_rates)

        # Calculate component rates
        component_rates = {}
        source_weights = self.config.risk_free_rate.source_weights

        # Federal Reserve component
        fed_component = self.calculate_weighted_average(fed_rates, {
            'federal_reserve': 1.0,
            'federal_reserve_fallback': 0.5
        })
        component_rates['federal_reserve'] = fed_component

        # Algorand staking component
        algo_staking = [r for r in algo_rates if r.rate_type == 'staking_rewards']
        algo_component = self.calculate_weighted_average(algo_staking, {'algorand_consensus': 1.0})
        component_rates['algorand_staking'] = algo_component

        # DeFi protocols component
        defi_rates = [r for r in algo_rates if r.source in ['folks_finance', 'tinyman']]
        defi_component = self.calculate_weighted_average(defi_rates, {
            'folks_finance': 0.7,
            'tinyman': 0.3
        })
        component_rates['defi_protocols'] = defi_component

        # Calculate risk-free rate
        risk_free_rate = (
            fed_component * source_weights.get('federal_reserve', 0.6) +
            algo_component * source_weights.get('algorand_staking', 0.3) +
            defi_component * source_weights.get('defi_protocols', 0.1)
        )

        # Apply adjustments
        adjustments = self.config.risk_free_rate.adjustments
        for adjustment_name, adjustment_value in adjustments.items():
            risk_free_rate += adjustment_value
            component_rates[f'adjustment_{adjustment_name}'] = adjustment_value

        # Calculate base rate (risk-free rate plus safety buffer)
        base_rate = risk_free_rate + self.config.analysis.safety_buffer

        # Apply bounds
        bounds = self.config.calculation_parameters.bounds
        base_rate = max(bounds.minimum_rate, min(bounds.maximum_rate, base_rate))
        risk_free_rate = max(bounds.minimum_rate, min(bounds.maximum_rate, risk_free_rate))

        # Calculate term structure
        term_structure = self.term_calculator.calculate_term_structure(base_rate)

        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(all_rates)

        # Create result
        result = BaseRateResult(
            base_rate=base_rate,
            risk_free_rate=risk_free_rate,
            term_structure=term_structure,
            confidence_score=confidence_score,
            component_rates=component_rates,
            data_sources=[rate.source for rate in all_rates],
            calculation_timestamp=datetime.now(),
            metadata={
                'calculation_time_ms': (time.time() - calculation_start) * 1000,
                'num_data_points': len(all_rates),
                'calculation_method': self.config.risk_free_rate.calculation_method
            }
        )

        # Store calculation result
        self._store_calculation_result(result)

        # Log result if enabled
        if self.config.development.log_rate_calculations:
            self.logger.info(f"Base rate calculated: {base_rate:.4f} (confidence: {confidence_score:.2f})")

        return result

    def _store_rate_data(self, rates: List[RateDataPoint]):
        """Store rate data in database"""
        with sqlite3.connect(self.db_path) as conn:
            for rate in rates:
                conn.execute('''
                    INSERT INTO rate_history
                    (timestamp, source, rate_type, value, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    rate.timestamp,
                    rate.source,
                    rate.rate_type,
                    rate.value,
                    rate.confidence,
                    json.dumps(rate.metadata)
                ))

    def _store_calculation_result(self, result: BaseRateResult):
        """Store calculation result in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO base_rate_calculations
                (timestamp, base_rate, risk_free_rate, confidence_score,
                 component_rates, term_structure, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.calculation_timestamp,
                result.base_rate,
                result.risk_free_rate,
                result.confidence_score,
                json.dumps(result.component_rates),
                json.dumps(result.term_structure),
                json.dumps(result.metadata)
            ))

    def get_historical_rates(self, days: int = 30) -> pd.DataFrame:
        """Get historical rate data"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT * FROM base_rate_calculations
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', conn, params=(start_date,))

        return df

    def get_current_rate(self, max_age_minutes: int = 15) -> Optional[BaseRateResult]:
        """Get current rate if recent enough, otherwise calculate new one"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM base_rate_calculations
                WHERE timestamp >= ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (cutoff_time,))

            row = cursor.fetchone()

            if row:
                # Convert database row to BaseRateResult
                return BaseRateResult(
                    base_rate=row[2],
                    risk_free_rate=row[3],
                    term_structure=json.loads(row[6]),
                    confidence_score=row[4],
                    component_rates=json.loads(row[5]),
                    data_sources=[],  # Not stored in this table
                    calculation_timestamp=datetime.fromisoformat(row[1]),
                    metadata=json.loads(row[7]) if row[7] else {}
                )

        # No recent rate found, calculate new one
        return self.calculate_base_rate()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the engine"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        # Check database connectivity
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('SELECT 1')
            health_status['checks']['database'] = 'ok'
        except Exception as e:
            health_status['checks']['database'] = f'error: {e}'
            health_status['status'] = 'degraded'

        # Check data freshness
        try:
            latest_calc = self.get_current_rate(max_age_minutes=60)
            if latest_calc:
                age_minutes = (datetime.now() - latest_calc.calculation_timestamp).total_seconds() / 60
                health_status['checks']['data_freshness'] = f'latest calculation: {age_minutes:.1f} minutes ago'
                if age_minutes > 30:
                    health_status['status'] = 'degraded'
            else:
                health_status['checks']['data_freshness'] = 'no recent calculations'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['data_freshness'] = f'error: {e}'
            health_status['status'] = 'degraded'

        # Check configuration
        try:
            config_check = {
                'federal_reserve_enabled': self.config.federal_reserve_rates.fed_funds_rate.enabled,
                'algorand_staking_enabled': self.config.algorand_defi_rates.algorand_staking.enabled,
                'update_frequency': self.config.calculation_parameters.update_frequency_minutes
            }
            health_status['checks']['configuration'] = config_check
        except Exception as e:
            health_status['checks']['configuration'] = f'error: {e}'
            health_status['status'] = 'degraded'

        return health_status


# Convenience functions for external use
def calculate_current_base_rate(config_path: Optional[Path] = None) -> BaseRateResult:
    """Calculate current base rate - convenience function"""
    engine = BaseRateCalculationEngine(load_config(config_path))
    return engine.calculate_base_rate()


def get_base_rate_engine(config_path: Optional[Path] = None) -> BaseRateCalculationEngine:
    """Get configured base rate engine - convenience function"""
    return BaseRateCalculationEngine(load_config(config_path))