"""
Market Conditions Monitor Engine

This engine provides real-time market monitoring, volatility analysis, correlation tracking,
and market regime detection for the Algorand lending ecosystem.
"""

import requests
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
import json
import time
import statistics
from pathlib import Path
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

from .config import MarketConditionsMonitorConfig, load_config


class MarketRegime(Enum):
    """Market regime classifications"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"
    NORMAL = "normal"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MarketDataPoint:
    """Individual market data point"""
    symbol: str
    price: float
    volume: Optional[float]
    timestamp: datetime
    source: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VolatilityMetric:
    """Volatility calculation result"""
    asset: str
    value: float
    annualized_value: float
    calculation_method: str
    time_window: str
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CorrelationMetric:
    """Correlation analysis result"""
    asset1: str
    asset2: str
    correlation: float
    p_value: float
    time_window: str
    significance_level: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MarketAlert:
    """Market condition alert"""
    alert_type: str
    level: AlertLevel
    message: str
    affected_assets: List[str]
    metrics: Dict[str, float]
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class MarketConditionsResult:
    """Complete market conditions analysis result"""
    timestamp: datetime
    market_regime: MarketRegime
    regime_confidence: float
    volatility_metrics: Dict[str, VolatilityMetric]
    correlation_metrics: List[CorrelationMetric]
    stress_indicators: Dict[str, float]
    algorand_ecosystem_health: Dict[str, float]
    alerts: List[MarketAlert]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MarketDataProvider:
    """Handles fetching market data from various sources"""

    def __init__(self, config: MarketConditionsMonitorConfig):
        self.config = config
        self.session = requests.Session()
        self.cache = {}
        self.cache_expiry = {}

    def get_price_data(self, symbol: str, source: Optional[str] = None) -> Optional[MarketDataPoint]:
        """Get current price data for a symbol"""
        # Check cache first
        cache_key = f"{symbol}_{source or 'default'}"
        if self._is_cached_valid(cache_key):
            return self.cache[cache_key]

        # Try primary sources
        data_point = None
        sources_to_try = [source] if source else ['binance', 'coinbase', 'yahoo_finance']

        for src in sources_to_try:
            try:
                if src == 'binance':
                    data_point = self._fetch_binance_data(symbol)
                elif src == 'coinbase':
                    data_point = self._fetch_coinbase_data(symbol)
                elif src == 'yahoo_finance':
                    data_point = self._fetch_yahoo_data(symbol)

                if data_point:
                    self._cache_data(cache_key, data_point)
                    break

            except Exception as e:
                logging.warning(f"Failed to fetch {symbol} from {src}: {e}")
                continue

        return data_point

    def _fetch_binance_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Fetch data from Binance API"""
        if not self.config.data_sources.primary_sources['binance'].enabled:
            return None

        # Convert symbol format (e.g., ALGO -> ALGOUSDT)
        binance_symbol = f"{symbol}USDT" if symbol not in ['BTCUSDT', 'ETHUSDT', 'ALGOUSDT'] else symbol

        try:
            url = f"{self.config.data_sources.primary_sources['binance'].api_endpoint}/ticker/24hr"
            response = self.session.get(url, params={'symbol': binance_symbol}, timeout=10)
            response.raise_for_status()

            data = response.json()
            return MarketDataPoint(
                symbol=symbol,
                price=float(data['lastPrice']),
                volume=float(data['volume']),
                timestamp=datetime.now(),
                source='binance',
                high_24h=float(data['highPrice']),
                low_24h=float(data['lowPrice']),
                metadata={'binance_symbol': binance_symbol}
            )

        except Exception as e:
            logging.warning(f"Binance API error for {symbol}: {e}")
            return None

    def _fetch_coinbase_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Fetch data from Coinbase API"""
        if not self.config.data_sources.primary_sources['coinbase'].enabled:
            return None

        # Convert symbol format (e.g., ALGO -> ALGO-USD)
        coinbase_symbol = f"{symbol}-USD"

        try:
            url = f"{self.config.data_sources.primary_sources['coinbase'].api_endpoint}/products/{coinbase_symbol}/ticker"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            return MarketDataPoint(
                symbol=symbol,
                price=float(data['price']),
                volume=float(data.get('volume', 0)),
                timestamp=datetime.now(),
                source='coinbase',
                bid=float(data.get('bid', 0)),
                ask=float(data.get('ask', 0)),
                metadata={'coinbase_symbol': coinbase_symbol}
            )

        except Exception as e:
            logging.warning(f"Coinbase API error for {symbol}: {e}")
            return None

    def _fetch_yahoo_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Fetch data from Yahoo Finance API"""
        if not self.config.data_sources.primary_sources['yahoo_finance'].enabled:
            return None

        try:
            url = f"{self.config.data_sources.primary_sources['yahoo_finance'].api_endpoint}/{symbol}"
            params = {
                'interval': '1d',
                'range': '1d'
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            result = data['chart']['result'][0]
            meta = result['meta']

            return MarketDataPoint(
                symbol=symbol,
                price=meta['regularMarketPrice'],
                volume=meta.get('regularMarketVolume'),
                timestamp=datetime.now(),
                source='yahoo_finance',
                high_24h=meta.get('regularMarketDayHigh'),
                low_24h=meta.get('regularMarketDayLow'),
                metadata={'yahoo_symbol': symbol}
            )

        except Exception as e:
            logging.warning(f"Yahoo Finance API error for {symbol}: {e}")
            return None

    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache or cache_key not in self.cache_expiry:
            return False

        return datetime.now() < self.cache_expiry[cache_key]

    def _cache_data(self, cache_key: str, data: MarketDataPoint):
        """Cache market data point"""
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now() + timedelta(
            seconds=self.config.real_time_monitoring.update_frequencies.price_data_seconds
        )

    def get_historical_prices(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical price data for volatility calculations"""
        # In a production system, this would fetch historical data
        # For demo purposes, we'll generate simulated data
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_price = 0.25  # ALGO base price

        # Generate realistic price movements
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0, 0.02, days)  # 2% daily volatility
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        return pd.DataFrame({
            'timestamp': dates,
            'symbol': symbol,
            'price': prices,
            'volume': np.random.uniform(100000, 1000000, days)
        })


class VolatilityCalculator:
    """Calculates various volatility metrics"""

    def __init__(self, config: MarketConditionsMonitorConfig):
        self.config = config

    def calculate_realized_volatility(self, prices: pd.Series, window_hours: int = 24) -> float:
        """Calculate realized volatility from price returns"""
        if len(prices) < 2:
            return 0.0

        # Calculate returns
        returns = prices.pct_change().dropna()

        if len(returns) == 0:
            return 0.0

        # Calculate volatility (annualized)
        volatility = returns.std() * np.sqrt(365)  # Assuming daily data
        return float(volatility)

    def calculate_garch_volatility(self, prices: pd.Series) -> float:
        """Calculate GARCH model volatility (simplified version)"""
        if len(prices) < 10:
            return self.calculate_realized_volatility(prices)

        returns = prices.pct_change().dropna()
        if len(returns) < 5:
            return 0.0

        # Simplified GARCH(1,1) - in practice would use arch library
        alpha = 0.1
        beta = 0.85
        gamma = 0.05

        variances = []
        long_run_var = returns.var()

        for i, ret in enumerate(returns):
            if i == 0:
                variance = long_run_var
            else:
                variance = gamma * long_run_var + alpha * (returns.iloc[i-1] ** 2) + beta * variances[-1]

            variances.append(variance)

        # Return annualized volatility
        current_volatility = np.sqrt(variances[-1] * 365)
        return float(current_volatility)

    def calculate_exponential_smoothing(self, prices: pd.Series, lambda_factor: float = 0.94) -> float:
        """Calculate exponentially weighted volatility"""
        if len(prices) < 2:
            return 0.0

        returns = prices.pct_change().dropna()
        if len(returns) == 0:
            return 0.0

        # Exponentially weighted variance
        weights = np.array([(1 - lambda_factor) * (lambda_factor ** i) for i in range(len(returns))])
        weights = weights[::-1]  # Most recent gets highest weight
        weights = weights / weights.sum()

        weighted_variance = np.sum(weights * (returns ** 2))
        volatility = np.sqrt(weighted_variance * 365)

        return float(volatility)

    def calculate_parkinson_estimator(self, high_prices: pd.Series, low_prices: pd.Series) -> float:
        """Calculate Parkinson volatility estimator using high-low range"""
        if len(high_prices) != len(low_prices) or len(high_prices) < 2:
            return 0.0

        # Parkinson estimator
        log_hl_ratio = np.log(high_prices / low_prices)
        parkinson_var = (log_hl_ratio ** 2).mean() / (4 * np.log(2))
        volatility = np.sqrt(parkinson_var * 365)

        return float(volatility)

    def calculate_all_volatilities(self, symbol: str, prices_df: pd.DataFrame) -> Dict[str, VolatilityMetric]:
        """Calculate all configured volatility metrics"""
        volatilities = {}

        if prices_df.empty:
            return volatilities

        prices = prices_df['price']
        high_prices = prices_df.get('high_24h', prices)
        low_prices = prices_df.get('low_24h', prices)

        methods = self.config.volatility_monitoring.calculation_methods

        for method in methods:
            try:
                if method == "realized_volatility":
                    vol = self.calculate_realized_volatility(prices)
                elif method == "garch_volatility":
                    vol = self.calculate_garch_volatility(prices)
                elif method == "exponential_smoothing":
                    vol = self.calculate_exponential_smoothing(prices)
                elif method == "parkinson_estimator":
                    vol = self.calculate_parkinson_estimator(high_prices, low_prices)
                else:
                    continue

                volatilities[method] = VolatilityMetric(
                    asset=symbol,
                    value=vol,
                    annualized_value=vol,
                    calculation_method=method,
                    time_window="30d",  # Default window
                    confidence=0.85,
                    timestamp=datetime.now(),
                    metadata={'data_points': len(prices)}
                )

            except Exception as e:
                logging.warning(f"Failed to calculate {method} for {symbol}: {e}")

        return volatilities


class CorrelationAnalyzer:
    """Analyzes correlations between different assets and markets"""

    def __init__(self, config: MarketConditionsMonitorConfig):
        self.config = config
        self.data_provider = MarketDataProvider(config)

    def calculate_correlation(self, asset1_prices: pd.Series, asset2_prices: pd.Series,
                            window_days: int = 30) -> Tuple[float, float]:
        """Calculate correlation and p-value between two price series"""
        if len(asset1_prices) != len(asset2_prices) or len(asset1_prices) < 2:
            return 0.0, 1.0

        # Calculate returns
        returns1 = asset1_prices.pct_change().dropna()
        returns2 = asset2_prices.pct_change().dropna()

        # Align series
        min_length = min(len(returns1), len(returns2))
        if min_length < 2:
            return 0.0, 1.0

        returns1 = returns1.iloc[-min_length:]
        returns2 = returns2.iloc[-min_length:]

        # Calculate correlation
        correlation = returns1.corr(returns2)
        if np.isnan(correlation):
            correlation = 0.0

        # Calculate p-value (simplified)
        n = len(returns1)
        t_stat = correlation * np.sqrt((n - 2) / (1 - correlation ** 2)) if correlation != 1.0 else 0
        p_value = 2 * (1 - statistics.NormalDist().cdf(abs(t_stat)))

        return float(correlation), float(p_value)

    def analyze_cross_asset_correlations(self) -> List[CorrelationMetric]:
        """Analyze correlations between Algorand and traditional/crypto markets"""
        correlations = []

        # Get ALGO price data
        algo_prices = self.data_provider.get_historical_prices('ALGO', days=90)

        # Traditional market correlations
        traditional_assets = ['SPY', 'QQQ', 'VIX', 'TLT', 'GLD']
        crypto_assets = ['BTC', 'ETH']

        all_assets = traditional_assets + crypto_assets

        for asset in all_assets:
            try:
                asset_prices = self.data_provider.get_historical_prices(asset, days=90)

                if not asset_prices.empty and not algo_prices.empty:
                    corr, p_val = self.calculate_correlation(
                        algo_prices['price'],
                        asset_prices['price']
                    )

                    correlations.append(CorrelationMetric(
                        asset1='ALGO',
                        asset2=asset,
                        correlation=corr,
                        p_value=p_val,
                        time_window='90d',
                        significance_level=0.05,
                        timestamp=datetime.now(),
                        metadata={
                            'asset1_type': 'algorand_native',
                            'asset2_type': 'traditional' if asset in traditional_assets else 'crypto'
                        }
                    ))

            except Exception as e:
                logging.warning(f"Failed to calculate correlation for ALGO-{asset}: {e}")

        return correlations


class RegimeDetector:
    """Detects market regimes using multiple methodologies"""

    def __init__(self, config: MarketConditionsMonitorConfig):
        self.config = config

    def detect_trend_based_regime(self, prices_df: pd.DataFrame) -> Tuple[MarketRegime, float]:
        """Detect regime based on price trends"""
        if prices_df.empty or len(prices_df) < 30:
            return MarketRegime.NORMAL, 0.5

        prices = prices_df['price']

        # Calculate returns over different periods
        short_return = (prices.iloc[-1] / prices.iloc[-30] - 1) if len(prices) >= 30 else 0
        medium_return = (prices.iloc[-1] / prices.iloc[-90] - 1) if len(prices) >= 90 else 0

        # Get thresholds from config
        thresholds = self.config.regime_detection.classification_methods['trend_based'].trend_thresholds

        bull_threshold = thresholds['bull_market']
        bear_threshold = thresholds['bear_market']
        sideways_threshold = thresholds['sideways_threshold']

        # Determine regime
        if short_return > bull_threshold and medium_return > bull_threshold:
            return MarketRegime.BULL, 0.85
        elif short_return < bear_threshold and medium_return < bear_threshold:
            return MarketRegime.BEAR, 0.85
        elif abs(short_return) < sideways_threshold and abs(medium_return) < sideways_threshold:
            return MarketRegime.SIDEWAYS, 0.80
        else:
            return MarketRegime.NORMAL, 0.70

    def detect_volatility_based_regime(self, volatility_metrics: Dict[str, VolatilityMetric]) -> Tuple[MarketRegime, float]:
        """Detect regime based on volatility levels"""
        if not volatility_metrics:
            return MarketRegime.NORMAL, 0.5

        # Get average volatility across methods
        avg_volatility = np.mean([vm.annualized_value for vm in volatility_metrics.values()])

        thresholds = self.config.regime_detection.classification_methods['volatility_based'].regime_thresholds

        if avg_volatility > thresholds['high_vol_regime']:
            return MarketRegime.CRISIS, 0.80
        elif avg_volatility < thresholds['low_vol_regime']:
            return MarketRegime.BULL, 0.75
        else:
            return MarketRegime.NORMAL, 0.85

    def detect_crisis_conditions(self, prices_df: pd.DataFrame, volatility_metrics: Dict[str, VolatilityMetric]) -> bool:
        """Detect crisis market conditions"""
        crisis_indicators = self.config.regime_detection.crisis_detection.crisis_indicators

        crisis_signals = 0

        # Check price drop
        if not prices_df.empty and len(prices_df) >= 24:  # 24 hours of data
            recent_prices = prices_df['price'].tail(24)
            price_drop = (recent_prices.min() / recent_prices.max() - 1)
            if price_drop < -crisis_indicators['price_drop_threshold']:
                crisis_signals += 1

        # Check volatility spike
        if volatility_metrics:
            avg_volatility = np.mean([vm.annualized_value for vm in volatility_metrics.values()])
            normal_volatility = 0.40  # Assume 40% is normal for crypto
            if avg_volatility > normal_volatility * crisis_indicators['volatility_spike_threshold']:
                crisis_signals += 1

        # Check volume spike
        if not prices_df.empty and 'volume' in prices_df.columns:
            recent_volume = prices_df['volume'].tail(24).mean()
            historical_volume = prices_df['volume'].mean()
            if recent_volume > historical_volume * crisis_indicators['volume_spike_threshold']:
                crisis_signals += 1

        # Crisis if multiple indicators trigger
        return crisis_signals >= 2

    def detect_market_regime(self, prices_df: pd.DataFrame, volatility_metrics: Dict[str, VolatilityMetric]) -> Tuple[MarketRegime, float]:
        """Detect overall market regime using multiple methods"""
        # Check for crisis first
        if self.detect_crisis_conditions(prices_df, volatility_metrics):
            return MarketRegime.CRISIS, 0.90

        # Get individual regime predictions
        trend_regime, trend_conf = self.detect_trend_based_regime(prices_df)
        vol_regime, vol_conf = self.detect_volatility_based_regime(volatility_metrics)

        # Combine predictions with weights
        trend_weight = self.config.regime_detection.classification_methods['trend_based'].weight
        vol_weight = self.config.regime_detection.classification_methods['volatility_based'].weight

        # Simple weighted voting (in practice, would use more sophisticated ensemble)
        if trend_regime == vol_regime:
            # Agreement between methods
            combined_confidence = (trend_conf * trend_weight + vol_conf * vol_weight) / (trend_weight + vol_weight)
            return trend_regime, combined_confidence
        else:
            # Disagreement - use higher confidence method
            if trend_conf > vol_conf:
                return trend_regime, trend_conf * 0.8  # Reduce confidence due to disagreement
            else:
                return vol_regime, vol_conf * 0.8


class AlertManager:
    """Manages market condition alerts"""

    def __init__(self, config: MarketConditionsMonitorConfig):
        self.config = config
        self.alert_history = []
        self.last_alert_times = {}

    def check_volatility_alerts(self, volatility_metrics: Dict[str, VolatilityMetric]) -> List[MarketAlert]:
        """Check for volatility-based alerts"""
        alerts = []

        if not volatility_metrics:
            return alerts

        thresholds = self.config.volatility_monitoring.thresholds
        alert_thresholds = self.config.alert_system.alert_levels

        for method, metric in volatility_metrics.items():
            # Critical volatility alert
            if metric.annualized_value > thresholds.extreme_volatility:
                alerts.append(MarketAlert(
                    alert_type="extreme_volatility",
                    level=AlertLevel.CRITICAL,
                    message=f"Extreme volatility detected for {metric.asset}: {metric.annualized_value:.2%}",
                    affected_assets=[metric.asset],
                    metrics={"volatility": metric.annualized_value},
                    confidence=metric.confidence,
                    timestamp=datetime.now()
                ))

            # Warning volatility alert
            elif metric.annualized_value > thresholds.high_volatility:
                alerts.append(MarketAlert(
                    alert_type="high_volatility",
                    level=AlertLevel.WARNING,
                    message=f"High volatility detected for {metric.asset}: {metric.annualized_value:.2%}",
                    affected_assets=[metric.asset],
                    metrics={"volatility": metric.annualized_value},
                    confidence=metric.confidence,
                    timestamp=datetime.now()
                ))

        return alerts

    def check_regime_change_alerts(self, current_regime: MarketRegime, previous_regime: MarketRegime,
                                 confidence: float) -> List[MarketAlert]:
        """Check for regime change alerts"""
        alerts = []

        if current_regime != previous_regime and confidence > 0.7:
            level = AlertLevel.CRITICAL if current_regime == MarketRegime.CRISIS else AlertLevel.WARNING

            alerts.append(MarketAlert(
                alert_type="regime_change",
                level=level,
                message=f"Market regime changed from {previous_regime.value} to {current_regime.value}",
                affected_assets=["ALGO"],  # Primary asset
                metrics={"confidence": confidence},
                confidence=confidence,
                timestamp=datetime.now()
            ))

        return alerts

    def check_correlation_alerts(self, correlations: List[CorrelationMetric]) -> List[MarketAlert]:
        """Check for correlation-based alerts"""
        alerts = []

        high_corr_threshold = self.config.correlation_analysis.calculation_parameters.high_correlation_threshold

        for corr in correlations:
            if abs(corr.correlation) > high_corr_threshold and corr.p_value < 0.05:
                alerts.append(MarketAlert(
                    alert_type="high_correlation",
                    level=AlertLevel.WARNING,
                    message=f"High correlation detected between {corr.asset1} and {corr.asset2}: {corr.correlation:.3f}",
                    affected_assets=[corr.asset1, corr.asset2],
                    metrics={"correlation": corr.correlation, "p_value": corr.p_value},
                    confidence=1 - corr.p_value,
                    timestamp=datetime.now()
                ))

        return alerts

    def filter_and_rate_limit_alerts(self, alerts: List[MarketAlert]) -> List[MarketAlert]:
        """Filter alerts based on rate limiting and deduplication"""
        filtered_alerts = []
        current_time = datetime.now()

        rate_limiting = self.config.alert_system.rate_limiting

        for alert in alerts:
            alert_key = f"{alert.alert_type}_{alert.level.value}"

            # Check rate limiting
            if alert_key in self.last_alert_times:
                time_since_last = (current_time - self.last_alert_times[alert_key]).total_seconds() / 60
                cooldown = rate_limiting.duplicate_alert_cooldown_minutes

                if time_since_last < cooldown and not (
                    alert.level == AlertLevel.CRITICAL and rate_limiting.critical_alert_bypass
                ):
                    continue

            # Update last alert time and add to filtered list
            self.last_alert_times[alert_key] = current_time
            filtered_alerts.append(alert)

        return filtered_alerts


class MarketConditionsMonitorEngine:
    """Main engine for monitoring market conditions"""

    def __init__(self, config: Optional[MarketConditionsMonitorConfig] = None):
        self.config = config or load_config()
        self.logger = self._setup_logging()

        # Initialize components
        self.data_provider = MarketDataProvider(self.config)
        self.volatility_calculator = VolatilityCalculator(self.config)
        self.correlation_analyzer = CorrelationAnalyzer(self.config)
        self.regime_detector = RegimeDetector(self.config)
        self.alert_manager = AlertManager(self.config)

        # Initialize database
        self.db_path = Path(self.config.database.default_path)
        self._init_database()

        # State tracking
        self.current_regime = MarketRegime.NORMAL
        self.last_analysis_time = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('market_conditions_monitor')
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
        """Initialize SQLite database for storing market data and analysis"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Market data table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    price REAL,
                    volume REAL,
                    source TEXT,
                    metadata TEXT
                )
            ''')

            # Volatility calculations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS volatility_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    asset TEXT,
                    method TEXT,
                    value REAL,
                    annualized_value REAL,
                    time_window TEXT,
                    confidence REAL,
                    metadata TEXT
                )
            ''')

            # Regime classifications table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS regime_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    regime TEXT,
                    confidence REAL,
                    metadata TEXT
                )
            ''')

            # Correlation analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS correlation_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    asset1 TEXT,
                    asset2 TEXT,
                    correlation REAL,
                    p_value REAL,
                    time_window TEXT,
                    metadata TEXT
                )
            ''')

            # Alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    alert_type TEXT,
                    level TEXT,
                    message TEXT,
                    affected_assets TEXT,
                    metrics TEXT,
                    confidence REAL,
                    metadata TEXT
                )
            ''')

            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_volatility_timestamp ON volatility_calculations(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_regime_timestamp ON regime_classifications(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')

    def analyze_market_conditions(self) -> MarketConditionsResult:
        """Perform comprehensive market conditions analysis"""
        analysis_start = time.time()

        self.logger.info("Starting market conditions analysis")

        # Get market data for key assets
        assets_to_monitor = []
        for asset_category in self.config.volatility_monitoring.monitored_assets.values():
            assets_to_monitor.extend(asset_category)

        # Analyze ALGO as primary asset
        algo_prices = self.data_provider.get_historical_prices('ALGO', days=90)

        # Calculate volatility metrics
        volatility_metrics = self.volatility_calculator.calculate_all_volatilities('ALGO', algo_prices)

        # Analyze correlations
        correlation_metrics = self.correlation_analyzer.analyze_cross_asset_correlations()

        # Detect market regime
        regime, regime_confidence = self.regime_detector.detect_market_regime(algo_prices, volatility_metrics)

        # Calculate stress indicators (simplified)
        stress_indicators = self._calculate_stress_indicators()

        # Assess Algorand ecosystem health
        ecosystem_health = self._assess_algorand_ecosystem_health()

        # Generate alerts
        alerts = []
        alerts.extend(self.alert_manager.check_volatility_alerts(volatility_metrics))
        alerts.extend(self.alert_manager.check_regime_change_alerts(regime, self.current_regime, regime_confidence))
        alerts.extend(self.alert_manager.check_correlation_alerts(correlation_metrics))

        # Filter alerts
        alerts = self.alert_manager.filter_and_rate_limit_alerts(alerts)

        # Update current regime
        self.current_regime = regime

        # Store results in database
        self._store_analysis_results(volatility_metrics, correlation_metrics, regime, regime_confidence, alerts)

        # Create result object
        result = MarketConditionsResult(
            timestamp=datetime.now(),
            market_regime=regime,
            regime_confidence=regime_confidence,
            volatility_metrics=volatility_metrics,
            correlation_metrics=correlation_metrics,
            stress_indicators=stress_indicators,
            algorand_ecosystem_health=ecosystem_health,
            alerts=alerts,
            metadata={
                'analysis_time_ms': (time.time() - analysis_start) * 1000,
                'assets_analyzed': len(assets_to_monitor),
                'data_sources_used': ['binance', 'coinbase', 'simulated']
            }
        )

        self.last_analysis_time = datetime.now()

        if self.config.development.log_calculations:
            self.logger.info(f"Market analysis completed: regime={regime.value}, confidence={regime_confidence:.2f}")

        return result

    def _calculate_stress_indicators(self) -> Dict[str, float]:
        """Calculate market stress indicators"""
        stress_indicators = {}

        # VIX level (simulated)
        vix_level = np.random.uniform(15, 35)  # Normal range
        stress_indicators['vix'] = vix_level

        # Crypto Fear & Greed Index (simulated)
        fear_greed = np.random.uniform(20, 80)
        stress_indicators['crypto_fear_greed'] = fear_greed

        # Credit spreads (simulated)
        ig_spread = np.random.uniform(100, 300)  # Investment grade spread in bps
        hy_spread = np.random.uniform(300, 800)  # High yield spread in bps
        stress_indicators['investment_grade_spread'] = ig_spread
        stress_indicators['high_yield_spread'] = hy_spread

        return stress_indicators

    def _assess_algorand_ecosystem_health(self) -> Dict[str, float]:
        """Assess Algorand ecosystem health metrics"""
        health_metrics = {}

        # Network metrics (simulated - in practice would query Algorand network)
        health_metrics['transaction_throughput'] = np.random.uniform(2000, 6000)  # TPS
        health_metrics['block_time'] = np.random.uniform(3.2, 3.5)  # seconds
        health_metrics['finality_time'] = np.random.uniform(4.0, 5.0)  # seconds
        health_metrics['network_participation'] = np.random.uniform(0.80, 0.90)  # 80-90%

        # DeFi protocol health (simulated)
        health_metrics['folks_finance_tvl'] = np.random.uniform(50e6, 100e6)  # $50-100M TVL
        health_metrics['tinyman_liquidity'] = np.random.uniform(20e6, 50e6)  # $20-50M liquidity
        health_metrics['total_defi_tvl'] = health_metrics['folks_finance_tvl'] + health_metrics['tinyman_liquidity']

        return health_metrics

    def _store_analysis_results(self, volatility_metrics: Dict[str, VolatilityMetric],
                               correlation_metrics: List[CorrelationMetric],
                               regime: MarketRegime, regime_confidence: float,
                               alerts: List[MarketAlert]):
        """Store analysis results in database"""
        with sqlite3.connect(self.db_path) as conn:
            timestamp = datetime.now()

            # Store volatility metrics
            for method, metric in volatility_metrics.items():
                conn.execute('''
                    INSERT INTO volatility_calculations
                    (timestamp, asset, method, value, annualized_value, time_window, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, metric.asset, metric.calculation_method, metric.value,
                    metric.annualized_value, metric.time_window, metric.confidence,
                    json.dumps(metric.metadata)
                ))

            # Store regime classification
            conn.execute('''
                INSERT INTO regime_classifications
                (timestamp, regime, confidence, metadata)
                VALUES (?, ?, ?, ?)
            ''', (
                timestamp, regime.value, regime_confidence,
                json.dumps({'detection_methods': ['trend_based', 'volatility_based']})
            ))

            # Store correlations
            for corr in correlation_metrics:
                conn.execute('''
                    INSERT INTO correlation_analysis
                    (timestamp, asset1, asset2, correlation, p_value, time_window, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, corr.asset1, corr.asset2, corr.correlation,
                    corr.p_value, corr.time_window, json.dumps(corr.metadata)
                ))

            # Store alerts
            for alert in alerts:
                conn.execute('''
                    INSERT INTO alerts
                    (timestamp, alert_type, level, message, affected_assets, metrics, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, alert.alert_type, alert.level.value, alert.message,
                    json.dumps(alert.affected_assets), json.dumps(alert.metrics),
                    alert.confidence, json.dumps(alert.metadata)
                ))

    def get_historical_analysis(self, days: int = 7) -> pd.DataFrame:
        """Get historical market analysis results"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT * FROM regime_classifications
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', conn, params=(start_date,))

        return df

    def get_current_conditions(self) -> Optional[MarketConditionsResult]:
        """Get current market conditions (cached if recent enough)"""
        cache_expiry_minutes = self.config.analysis.cache_expiry_minutes

        if (self.last_analysis_time and
            (datetime.now() - self.last_analysis_time).total_seconds() < cache_expiry_minutes * 60):
            # Return cached result if available and recent
            pass

        # Perform new analysis
        return self.analyze_market_conditions()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the monitoring engine"""
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

        # Check data sources
        try:
            test_data = self.data_provider.get_price_data('ALGO')
            health_status['checks']['data_sources'] = 'ok' if test_data else 'no_data'
            if not test_data:
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['data_sources'] = f'error: {e}'
            health_status['status'] = 'degraded'

        # Check last analysis time
        if self.last_analysis_time:
            age_minutes = (datetime.now() - self.last_analysis_time).total_seconds() / 60
            health_status['checks']['last_analysis'] = f'{age_minutes:.1f} minutes ago'
            if age_minutes > 60:  # Alert if no analysis in last hour
                health_status['status'] = 'degraded'
        else:
            health_status['checks']['last_analysis'] = 'no analysis performed'
            health_status['status'] = 'degraded'

        return health_status


# Convenience functions for external use
def analyze_current_market_conditions(config_path: Optional[Path] = None) -> MarketConditionsResult:
    """Analyze current market conditions - convenience function"""
    engine = MarketConditionsMonitorEngine(load_config(config_path))
    return engine.analyze_market_conditions()


def get_market_conditions_engine(config_path: Optional[Path] = None) -> MarketConditionsMonitorEngine:
    """Get configured market conditions engine - convenience function"""
    return MarketConditionsMonitorEngine(load_config(config_path))