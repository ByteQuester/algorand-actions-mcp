"""
Volatility Assessment Engine - Configurable Implementation

This module provides volatility assessment functionality using configuration
instead of hardcoded parameters. It extracts and refactors the logic from
oracle_integration.py to make it configurable and modular.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math
import random

from .config import VolatilityEngineConfig, load_config


class OracleStatus(Enum):
    """Oracle operational status"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class PriceFeed:
    """Individual price feed from an oracle"""
    oracle_name: str
    asset_symbol: str
    price_usd: float
    timestamp: datetime
    confidence: float
    volume_24h: Optional[float] = None
    source_count: Optional[int] = None


@dataclass
class AggregatedPrice:
    """Aggregated price from multiple oracles"""
    asset_symbol: str
    consensus_price: float
    price_confidence: float
    price_deviation: float
    oracle_count: int
    timestamp: datetime
    oracle_prices: List[PriceFeed]
    staleness_score: float
    reliability_score: float
    consensus_strength: float


@dataclass
class VolatilityMetrics:
    """Volatility assessment metrics"""
    asset_symbol: str
    volatility_7d: float
    volatility_30d: float
    price_range_24h: float
    price_stability_score: float
    manipulation_risk_level: str
    manipulation_risk_score: float
    confidence: float
    timestamp: datetime

    # Additional metrics
    oracle_consensus: float
    data_freshness: float
    risk_factors: List[str]
    recommendation: str


class PriceOracle:
    """Mock price oracle for demonstration"""
    def __init__(self, name: str, reliability_score: float = 0.95):
        self.primary_oracle = name
        self.reliability_score = reliability_score


class VolatilityAssessmentEngine:
    """
    Configurable Volatility Assessment Engine

    Refactored from oracle_integration.py to use YAML configuration
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the engine with configuration"""
        self.config = load_config(config_path)
        self.oracles: Dict[str, PriceOracle] = {}
        self.oracle_status: Dict[str, OracleStatus] = {}
        self.price_history: Dict[str, List[PriceFeed]] = {}
        self.reliability_scores: Dict[str, float] = {}

    def register_oracle(self, oracle: PriceOracle) -> None:
        """Register a new price oracle"""
        self.oracles[oracle.primary_oracle] = oracle
        self.oracle_status[oracle.primary_oracle] = OracleStatus.ACTIVE
        self.reliability_scores[oracle.primary_oracle] = oracle.reliability_score

    def get_price_feeds(self, asset_symbol: str) -> List[PriceFeed]:
        """Get price feeds from all active oracles for an asset"""
        feeds = []

        for oracle_name, oracle in self.oracles.items():
            if self.oracle_status[oracle_name] != OracleStatus.ACTIVE:
                continue

            try:
                price_data = self._fetch_price_from_oracle(oracle_name, asset_symbol)

                if price_data:
                    feed = PriceFeed(
                        oracle_name=oracle_name,
                        asset_symbol=asset_symbol,
                        price_usd=price_data["price"],
                        timestamp=price_data["timestamp"],
                        confidence=price_data.get("confidence", 1.0),
                        volume_24h=price_data.get("volume_24h"),
                        source_count=price_data.get("source_count")
                    )
                    feeds.append(feed)

            except Exception as e:
                # Mark oracle as degraded if it fails
                self.oracle_status[oracle_name] = OracleStatus.DEGRADED
                print(f"Oracle {oracle_name} failed: {e}")

        return feeds

    def _fetch_price_from_oracle(self, oracle_name: str, asset_symbol: str) -> Optional[Dict]:
        """
        Simulate fetching price from an oracle
        In practice, this would make actual API calls to MCP services
        """

        # Simulated price data for demonstration
        base_prices = {
            "ALGO": 0.50,
            "USDC": 1.00,
            "USDT": 0.999,
            "BTC": 35000.0,
            "ETH": 2500.0,
            "AVAX": 45.0,
            "SOL": 120.0,
            "MATIC": 1.20,
            "GARD": 0.95,
            "STBL": 1.01
        }

        if asset_symbol not in base_prices:
            return None

        # Simulate different oracle behaviors using config
        oracle_variations = {
            "chainlink": {"variance": 0.001, "latency": 30},
            "pyth": {"variance": 0.002, "latency": 5},
            "algorand_native": {"variance": 0.0005, "latency": 1},
            "dia": {"variance": 0.003, "latency": 60}
        }

        variation = oracle_variations.get(oracle_name, {"variance": 0.005, "latency": 120})

        # Add some random variation to simulate real oracle differences
        price_multiplier = 1.0 + random.uniform(-variation["variance"], variation["variance"])
        simulated_price = base_prices[asset_symbol] * price_multiplier

        return {
            "price": simulated_price,
            "timestamp": datetime.now() - timedelta(seconds=variation["latency"]),
            "confidence": 0.95 + random.uniform(-0.05, 0.05),
            "volume_24h": random.randint(100000, 50000000),
            "source_count": random.randint(3, 15)
        }

    def calculate_staleness_score(self, feeds: List[PriceFeed]) -> float:
        """
        Calculate how fresh the price data is (0-1, higher is fresher)
        Uses configuration parameters instead of hardcoded values
        """
        now = datetime.now()
        staleness_scores = []

        thresholds = self.config.price_staleness.scoring_thresholds
        values = self.config.price_staleness.scoring_values

        for feed in feeds:
            age_seconds = (now - feed.timestamp).total_seconds()

            # Configurable scoring based on YAML parameters
            if age_seconds <= thresholds['fresh']:
                score = values['fresh']
            elif age_seconds <= thresholds['good']:
                score = values['good']
            elif age_seconds <= thresholds['acceptable']:
                score = values['acceptable']
            elif age_seconds <= thresholds['stale']:
                score = values['stale']
            else:
                # Decline to 0 over the next period using configured decline rate
                excess_time = age_seconds - thresholds['stale']
                score = max(0.0, values['stale'] - (excess_time * values['decline_rate']))

            staleness_scores.append(score)

        return statistics.mean(staleness_scores)

    def aggregate_prices(self, feeds: List[PriceFeed]) -> AggregatedPrice:
        """Aggregate prices from multiple oracles into consensus price"""

        if not feeds:
            raise ValueError("No price feeds available for aggregation")

        if len(feeds) == 1:
            # Single oracle - use its price but mark lower confidence per config
            feed = feeds[0]
            confidence_penalty = self.config.oracle_confidence.confidence_penalty_single
            consensus_strength = self.config.oracle_confidence.consensus_strength_single

            return AggregatedPrice(
                asset_symbol=feed.asset_symbol,
                consensus_price=feed.price_usd,
                price_confidence=feed.confidence * confidence_penalty,
                price_deviation=0.0,
                oracle_count=1,
                timestamp=feed.timestamp,
                oracle_prices=feeds,
                staleness_score=self.calculate_staleness_score([feed]),
                reliability_score=self.reliability_scores.get(feed.oracle_name, 0.5),
                consensus_strength=consensus_strength
            )

        # Multiple oracles - calculate consensus
        prices = [feed.price_usd for feed in feeds]
        weights = [feed.confidence * self.reliability_scores.get(feed.oracle_name, 0.5)
                  for feed in feeds]

        # Weighted median for robustness against outliers (configurable)
        if self.config.oracle_confidence.outlier_detection['weighted_median_enabled']:
            consensus_price = self._weighted_median(prices, weights)
        else:
            consensus_price = statistics.median(prices)

        # Calculate price deviation
        price_deviation = statistics.stdev(prices) if len(prices) > 1 else 0.0
        relative_deviation = price_deviation / consensus_price if consensus_price > 0 else 0.0

        # Calculate confidence based on agreement (using config parameters)
        max_deviation = max(abs(p - consensus_price) / consensus_price for p in prices)
        deviation_multiplier = self.config.oracle_confidence.outlier_detection['max_deviation_multiplier']
        consensus_strength = max(0.0, 1.0 - max_deviation * deviation_multiplier)

        # Overall confidence considering multiple factors (using config weights)
        staleness_score = self.calculate_staleness_score(feeds)
        avg_reliability = statistics.mean(self.reliability_scores.get(f.oracle_name, 0.5) for f in feeds)

        weights = self.config.oracle_confidence.reliability_weights
        price_confidence = min(1.0, (
            consensus_strength * weights['consensus_weight'] +
            staleness_score * weights['staleness_weight'] +
            avg_reliability * weights['reliability_weight']
        ))

        return AggregatedPrice(
            asset_symbol=feeds[0].asset_symbol,
            consensus_price=consensus_price,
            price_confidence=price_confidence,
            price_deviation=relative_deviation,
            oracle_count=len(feeds),
            timestamp=max(feed.timestamp for feed in feeds),
            oracle_prices=feeds,
            staleness_score=staleness_score,
            reliability_score=avg_reliability,
            consensus_strength=consensus_strength
        )

    def _weighted_median(self, values: List[float], weights: List[float]) -> float:
        """Calculate weighted median of values"""
        if len(values) != len(weights):
            return statistics.median(values)

        # Sort by value
        sorted_pairs = sorted(zip(values, weights))

        total_weight = sum(weights)
        cumulative_weight = 0.0

        for value, weight in sorted_pairs:
            cumulative_weight += weight
            if cumulative_weight >= total_weight / 2:
                return value

        return sorted_pairs[-1][0]  # Fallback

    def get_reliable_price(self, asset_symbol: str, min_confidence: Optional[float] = None) -> Optional[AggregatedPrice]:
        """Get a reliable price with minimum confidence threshold"""

        if min_confidence is None:
            min_confidence = self.config.oracle_confidence.minimum_confidence

        feeds = self.get_price_feeds(asset_symbol)

        if not feeds:
            return None

        # Filter feeds by minimum individual confidence
        reliable_feeds = [f for f in feeds if f.confidence >= min_confidence * 0.8]

        if not reliable_feeds:
            # If no feeds meet the high standard, use all but mark lower confidence
            reliable_feeds = feeds

        aggregated = self.aggregate_prices(reliable_feeds)

        # Check if aggregated price meets confidence threshold
        if aggregated.price_confidence < min_confidence:
            print(f"Warning: Price confidence {aggregated.price_confidence:.2f} below threshold {min_confidence}")

        return aggregated

    def detect_price_manipulation(self, asset_symbol: str, lookback_minutes: Optional[int] = None) -> Dict[str, any]:
        """
        Detect potential price manipulation or anomalies
        Uses configuration parameters instead of hardcoded thresholds
        """

        if lookback_minutes is None:
            lookback_minutes = self.config.volatility_calculation.windows['manipulation_detection']

        # Get recent price history
        recent_feeds = []
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)

        if asset_symbol in self.price_history:
            recent_feeds = [
                f for f in self.price_history[asset_symbol]
                if f.timestamp >= cutoff_time
            ]

        min_data_points = self.config.volatility_calculation.minimum_data_points
        if len(recent_feeds) < min_data_points:
            return {"manipulation_risk": "unknown", "confidence": 0.0}

        # Get current price
        current_price = self.get_reliable_price(asset_symbol)
        if not current_price:
            return {"manipulation_risk": "unknown", "confidence": 0.0}

        # Calculate price volatility over the period
        prices = [f.price_usd for f in recent_feeds]
        price_volatility = statistics.stdev(prices) / statistics.mean(prices)

        # Check for sudden price jumps
        max_price = max(prices)
        min_price = min(prices)
        price_range = (max_price - min_price) / statistics.mean(prices)

        # Analyze oracle consensus
        consensus_scores = []
        for i in range(len(recent_feeds) - 2):
            window_feeds = recent_feeds[i:i+3]
            if len(set(f.oracle_name for f in window_feeds)) >= 2:
                window_prices = [f.price_usd for f in window_feeds]
                if statistics.mean(window_prices) > 0:
                    consensus = 1.0 - (statistics.stdev(window_prices) / statistics.mean(window_prices))
                    consensus_scores.append(max(0.0, consensus))

        avg_consensus = statistics.mean(consensus_scores) if consensus_scores else 1.0

        # Risk assessment using configuration parameters
        risk_factors = []
        risk_score = 0.0

        config = self.config.manipulation_detection
        thresholds = config.risk_thresholds
        weights = config.risk_scoring

        if price_volatility > thresholds['volatility_high']:
            risk_factors.append("high_volatility")
            risk_score += weights['volatility_weight']

        if price_range > thresholds['price_range_suspicious']:
            risk_factors.append("large_price_swings")
            risk_score += weights['price_range_weight']

        if avg_consensus < thresholds['consensus_poor']:
            risk_factors.append("poor_oracle_consensus")
            risk_score += weights['consensus_weight']

        if current_price.oracle_count < thresholds['insufficient_oracles']:
            risk_factors.append("insufficient_oracle_coverage")
            risk_score += weights['oracle_coverage_weight']

        # Determine risk level using configuration thresholds
        levels = config.risk_levels
        if risk_score >= levels['high_threshold']:
            risk_level = "high"
        elif risk_score >= levels['medium_threshold']:
            risk_level = "medium"
        elif risk_score >= levels['low_threshold']:
            risk_level = "low"
        else:
            risk_level = "minimal"

        # Recommendation based on monitoring configuration
        monitoring_config = self.config.monitoring.escalation_levels
        if risk_score > monitoring_config['critical']:
            recommendation = "emergency_halt"
        elif risk_score > monitoring_config['warning']:
            recommendation = "increase_monitoring"
        else:
            recommendation = "normal_operation"

        return {
            "manipulation_risk": risk_level,
            "confidence": min(1.0, avg_consensus),
            "risk_factors": risk_factors,
            "price_volatility": price_volatility,
            "price_range": price_range,
            "oracle_consensus": avg_consensus,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "lookback_minutes": lookback_minutes,
            "data_points": len(recent_feeds)
        }

    def assess_volatility(self, asset_symbol: str) -> VolatilityMetrics:
        """
        Comprehensive volatility assessment for an asset
        """
        current_time = datetime.now()

        # Get current reliable price
        current_price = self.get_reliable_price(asset_symbol)
        if not current_price:
            raise ValueError(f"Unable to get reliable price for {asset_symbol}")

        # Get manipulation detection results
        manipulation_results = self.detect_price_manipulation(asset_symbol)

        # Calculate volatility over different periods (simplified for demo)
        # In a real implementation, this would use historical price data
        volatility_7d = self._calculate_historical_volatility(asset_symbol, days=7)
        volatility_30d = self._calculate_historical_volatility(asset_symbol, days=30)

        # Calculate 24h price range
        price_range_24h = self._calculate_price_range_24h(asset_symbol)

        # Calculate price stability score
        price_stability_score = self._calculate_stability_score(
            volatility_7d, price_range_24h, current_price.consensus_strength
        )

        return VolatilityMetrics(
            asset_symbol=asset_symbol,
            volatility_7d=volatility_7d,
            volatility_30d=volatility_30d,
            price_range_24h=price_range_24h,
            price_stability_score=price_stability_score,
            manipulation_risk_level=manipulation_results["manipulation_risk"],
            manipulation_risk_score=manipulation_results["risk_score"],
            confidence=current_price.price_confidence,
            timestamp=current_time,
            oracle_consensus=manipulation_results["oracle_consensus"],
            data_freshness=current_price.staleness_score,
            risk_factors=manipulation_results["risk_factors"],
            recommendation=manipulation_results["recommendation"]
        )

    def _calculate_historical_volatility(self, asset_symbol: str, days: int) -> float:
        """Calculate historical volatility (simplified simulation)"""
        # In a real implementation, this would query historical price data
        # For demo purposes, we'll simulate based on asset category

        categories = self.config.market_analysis.asset_categories

        if asset_symbol in categories['highly_liquid']:
            base_volatility = 0.02  # 2% daily volatility for stable assets
        elif asset_symbol in categories['liquid']:
            base_volatility = 0.05  # 5% daily volatility
        else:
            base_volatility = 0.10  # 10% daily volatility for illiquid assets

        # Add some randomness
        return base_volatility * (1 + random.uniform(-0.3, 0.3))

    def _calculate_price_range_24h(self, asset_symbol: str) -> float:
        """Calculate 24h price range (simplified simulation)"""
        # Simulate 24h price range based on asset type
        return random.uniform(0.01, 0.15)  # 1-15% range

    def _calculate_stability_score(self, volatility_7d: float, price_range_24h: float, consensus_strength: float) -> float:
        """Calculate overall price stability score"""
        # Higher volatility and price range reduce stability
        volatility_component = max(0, 1 - volatility_7d * 5)  # Penalize high volatility
        range_component = max(0, 1 - price_range_24h * 3)     # Penalize large ranges
        consensus_component = consensus_strength               # Good consensus improves stability

        return (volatility_component + range_component + consensus_component) / 3

    def setup_demo_oracles(self):
        """Setup demo oracles for testing"""
        demo_oracles = [
            PriceOracle("chainlink", 0.95),
            PriceOracle("pyth", 0.92),
            PriceOracle("algorand_native", 0.98),
            PriceOracle("dia", 0.88)
        ]

        for oracle in demo_oracles:
            self.register_oracle(oracle)

    def simulate_price_history(self, asset_symbol: str, hours: int = 24):
        """Simulate price history for demonstration"""
        if asset_symbol not in self.price_history:
            self.price_history[asset_symbol] = []

        current_time = datetime.now()

        for i in range(hours * 4):  # 4 data points per hour
            timestamp = current_time - timedelta(minutes=15 * i)

            for oracle_name in self.oracles.keys():
                if random.random() > 0.1:  # 90% chance oracle reports
                    price_data = self._fetch_price_from_oracle(oracle_name, asset_symbol)
                    if price_data:
                        price_data["timestamp"] = timestamp
                        feed = PriceFeed(
                            oracle_name=oracle_name,
                            asset_symbol=asset_symbol,
                            price_usd=price_data["price"],
                            timestamp=price_data["timestamp"],
                            confidence=price_data["confidence"],
                            volume_24h=price_data.get("volume_24h"),
                            source_count=price_data.get("source_count")
                        )
                        self.price_history[asset_symbol].append(feed)

        # Sort by timestamp
        self.price_history[asset_symbol].sort(key=lambda x: x.timestamp, reverse=True)