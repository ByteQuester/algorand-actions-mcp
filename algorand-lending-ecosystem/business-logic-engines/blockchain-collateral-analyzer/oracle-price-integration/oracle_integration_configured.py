"""
Oracle Price Integration Module (Configuration-Enabled)

Handles integration with multiple price oracles for reliable asset pricing.
Implements fallback mechanisms and price confidence scoring with configuration support.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math
import random
from pathlib import Path

from core.config import load_config, OracleEngineConfig


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
    confidence: float                    # Confidence score 0-1
    volume_24h: Optional[float] = None   # 24h trading volume
    source_count: Optional[int] = None   # Number of sources aggregated


@dataclass
class AggregatedPrice:
    """Aggregated price from multiple oracles"""
    asset_symbol: str
    consensus_price: float               # Final consensus price
    price_confidence: float              # Overall confidence 0-1
    price_deviation: float               # Standard deviation of prices
    oracle_count: int                    # Number of oracles used
    timestamp: datetime

    # Individual oracle prices for transparency
    oracle_prices: List[PriceFeed]

    # Quality metrics
    staleness_score: float               # How fresh the data is
    reliability_score: float             # Historical reliability
    consensus_strength: float            # Agreement between oracles


class ConfigurableOracleManager:
    """Manages multiple price oracles with configuration-driven failover and aggregation"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.oracle_status: Dict[str, OracleStatus] = {}
        self.price_history: Dict[str, List[PriceFeed]] = {}
        self.reliability_scores: Dict[str, float] = {}

        # Initialize oracles from configuration
        self._initialize_oracles()

    def _initialize_oracles(self) -> None:
        """Initialize oracles from configuration"""
        for oracle_name, oracle_config in self.config.oracle_providers.items():
            if oracle_config.enabled:
                self.oracle_status[oracle_name] = OracleStatus.ACTIVE
                self.reliability_scores[oracle_name] = oracle_config.reliability_score

    def register_oracle(self, oracle_name: str) -> None:
        """Register a new price oracle (legacy compatibility)"""
        if oracle_name in self.config.oracle_providers:
            oracle_config = self.config.oracle_providers[oracle_name]
            self.oracle_status[oracle_name] = OracleStatus.ACTIVE
            self.reliability_scores[oracle_name] = oracle_config.reliability_score

    def get_price_feeds(self, asset_symbol: str) -> List[PriceFeed]:
        """Get price feeds from all active oracles for an asset"""
        feeds = []

        for oracle_name, oracle_config in self.config.oracle_providers.items():
            if not oracle_config.enabled or self.oracle_status.get(oracle_name) != OracleStatus.ACTIVE:
                continue

            try:
                # Simulate getting price from oracle using configuration
                price_data = self._fetch_price_from_oracle(oracle_name, asset_symbol, oracle_config)

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

    def _fetch_price_from_oracle(self, oracle_name: str, asset_symbol: str, oracle_config) -> Optional[Dict]:
        """
        Simulate fetching price from an oracle using configuration parameters
        In practice, this would make actual API calls
        """

        # Use fallback prices from config
        if asset_symbol not in self.config.fallback.emergency_prices:
            return None

        base_price = self.config.fallback.emergency_prices[asset_symbol]

        # Apply oracle-specific variation from configuration
        price_multiplier = 1.0 + random.uniform(-oracle_config.variance, oracle_config.variance)
        simulated_price = base_price * price_multiplier

        return {
            "price": simulated_price,
            "timestamp": datetime.now() - timedelta(seconds=oracle_config.latency_seconds),
            "confidence": oracle_config.reliability_score + random.uniform(-0.05, 0.05),
            "volume_24h": random.randint(1000000, 50000000),
            "source_count": random.randint(3, 15)
        }

    def aggregate_prices(self, feeds: List[PriceFeed]) -> AggregatedPrice:
        """Aggregate prices from multiple oracles into consensus price using configuration"""

        if not feeds:
            raise ValueError("No price feeds available for aggregation")

        if len(feeds) == 1:
            # Single oracle - use its price but mark lower confidence
            feed = feeds[0]
            return AggregatedPrice(
                asset_symbol=feed.asset_symbol,
                consensus_price=feed.price_usd,
                price_confidence=feed.confidence * 0.8,  # Reduce confidence for single source
                price_deviation=0.0,
                oracle_count=1,
                timestamp=feed.timestamp,
                oracle_prices=feeds,
                staleness_score=self._calculate_staleness_score([feed]),
                reliability_score=self.reliability_scores.get(feed.oracle_name, 0.5),
                consensus_strength=0.5  # Lower consensus with single oracle
            )

        # Multiple oracles - calculate consensus using configuration
        prices = [feed.price_usd for feed in feeds]

        # Use configured aggregation weights
        weight_factors = self.config.aggregation.weight_factors
        weights = [
            feed.confidence * weight_factors['confidence_weight'] +
            self.reliability_scores.get(feed.oracle_name, 0.5) * weight_factors['reliability_weight']
            for feed in feeds
        ]

        # Apply configured aggregation method
        if self.config.aggregation.method == "weighted_median":
            consensus_price = self._weighted_median(prices, weights)
        elif self.config.aggregation.method == "weighted_mean":
            consensus_price = self._weighted_mean(prices, weights)
        elif self.config.aggregation.method == "median":
            consensus_price = statistics.median(prices)
        else:  # default to mean
            consensus_price = statistics.mean(prices)

        # Calculate price deviation
        price_deviation = statistics.stdev(prices) if len(prices) > 1 else 0.0
        relative_deviation = price_deviation / consensus_price if consensus_price > 0 else 0.0

        # Calculate confidence based on agreement using configuration
        max_deviation = max(abs(p - consensus_price) / consensus_price for p in prices)
        max_allowed_deviation = self.config.validation.max_price_deviation_percent / 100
        consensus_strength = max(0.0, 1.0 - max_deviation / max_allowed_deviation)

        # Overall confidence considering multiple factors
        staleness_score = self._calculate_staleness_score(feeds)
        avg_reliability = statistics.mean(self.reliability_scores.get(f.oracle_name, 0.5) for f in feeds)

        price_confidence = min(1.0, (
            consensus_strength * 0.4 +
            staleness_score * 0.3 +
            avg_reliability * 0.3
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

    def _weighted_mean(self, values: List[float], weights: List[float]) -> float:
        """Calculate weighted mean of values"""
        if len(values) != len(weights):
            return statistics.mean(values)

        return sum(v * w for v, w in zip(values, weights)) / sum(weights)

    def _calculate_staleness_score(self, feeds: List[PriceFeed]) -> float:
        """Calculate how fresh the price data is using configuration thresholds"""
        now = datetime.now()
        staleness_config = self.config.staleness

        staleness_scores = []
        for feed in feeds:
            age_seconds = (now - feed.timestamp).total_seconds()

            # Use configuration thresholds for scoring
            if age_seconds <= staleness_config.excellent_threshold_seconds:
                score = 1.0
            elif age_seconds <= staleness_config.good_threshold_seconds:
                score = 0.9
            elif age_seconds <= staleness_config.acceptable_threshold_seconds:
                score = 0.7
            elif age_seconds <= staleness_config.poor_threshold_seconds:
                score = 0.5
            else:
                max_age = staleness_config.unacceptable_threshold_seconds
                score = max(0.0, 0.5 - (age_seconds - staleness_config.poor_threshold_seconds) / (max_age - staleness_config.poor_threshold_seconds))

            staleness_scores.append(score)

        return statistics.mean(staleness_scores)

    def get_reliable_price(self, asset_symbol: str, min_confidence: Optional[float] = None) -> Optional[AggregatedPrice]:
        """Get a reliable price with minimum confidence threshold from configuration"""

        if min_confidence is None:
            min_confidence = self.config.validation.confidence_threshold

        feeds = self.get_price_feeds(asset_symbol)

        if not feeds:
            return self._get_fallback_price(asset_symbol)

        # Filter feeds by minimum individual confidence
        reliable_feeds = [f for f in feeds if f.confidence >= min_confidence * 0.8]

        if not reliable_feeds:
            # If no feeds meet the high standard, use all but mark lower confidence
            reliable_feeds = feeds

        # Check minimum data points from configuration
        if len(reliable_feeds) < self.config.validation.min_data_points:
            return self._get_fallback_price(asset_symbol)

        aggregated = self.aggregate_prices(reliable_feeds)

        # Check if aggregated price meets confidence threshold
        if aggregated.price_confidence < min_confidence:
            print(f"Warning: Price confidence {aggregated.price_confidence:.2f} below threshold {min_confidence}")

        return aggregated

    def _get_fallback_price(self, asset_symbol: str) -> Optional[AggregatedPrice]:
        """Get fallback price when oracles fail using configuration"""
        if not self.config.fallback.enabled:
            return None

        if asset_symbol not in self.config.fallback.emergency_prices:
            return None

        emergency_price = self.config.fallback.emergency_prices[asset_symbol]

        # Create a fallback price feed
        fallback_feed = PriceFeed(
            oracle_name="emergency_fallback",
            asset_symbol=asset_symbol,
            price_usd=emergency_price,
            timestamp=datetime.now(),
            confidence=0.5  # Low confidence for emergency prices
        )

        return AggregatedPrice(
            asset_symbol=asset_symbol,
            consensus_price=emergency_price,
            price_confidence=0.5,
            price_deviation=0.0,
            oracle_count=1,
            timestamp=datetime.now(),
            oracle_prices=[fallback_feed],
            staleness_score=1.0,  # Fresh fallback
            reliability_score=0.5,
            consensus_strength=0.5
        )

    def detect_price_manipulation(self, asset_symbol: str, lookback_minutes: Optional[int] = None) -> Dict[str, any]:
        """Detect potential price manipulation or anomalies using configuration parameters"""

        if not self.config.manipulation_detection.enabled:
            return {"manipulation_risk": "disabled", "confidence": 0.0}

        if lookback_minutes is None:
            lookback_minutes = self.config.manipulation_detection.lookback_minutes

        # Get recent price history
        recent_feeds = []
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)

        if asset_symbol in self.price_history:
            recent_feeds = [
                f for f in self.price_history[asset_symbol]
                if f.timestamp >= cutoff_time
            ]

        if len(recent_feeds) < 5:
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
                consensus = 1.0 - (statistics.stdev(window_prices) / statistics.mean(window_prices))
                consensus_scores.append(max(0.0, consensus))

        avg_consensus = statistics.mean(consensus_scores) if consensus_scores else 1.0

        # Risk assessment using configuration parameters
        risk_factors = []
        risk_score = 0.0
        config = self.config.manipulation_detection

        if price_volatility > config.volatility_threshold:
            risk_factors.append("high_volatility")
            risk_score += config.risk_weights['high_volatility']

        if price_range > config.price_range_threshold:
            risk_factors.append("large_price_swings")
            risk_score += config.risk_weights['large_price_swings']

        if avg_consensus < config.consensus_threshold:
            risk_factors.append("poor_oracle_consensus")
            risk_score += config.risk_weights['poor_consensus']

        if current_price.oracle_count < config.min_oracle_coverage:
            risk_factors.append("insufficient_oracle_coverage")
            risk_score += config.risk_weights['insufficient_coverage']

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        elif risk_score >= 0.2:
            risk_level = "low"
        else:
            risk_level = "minimal"

        return {
            "manipulation_risk": risk_level,
            "confidence": min(1.0, avg_consensus),
            "risk_factors": risk_factors,
            "price_volatility": price_volatility,
            "oracle_consensus": avg_consensus,
            "recommendation": "increase_monitoring" if risk_score > 0.5 else "normal_operation"
        }

    def get_config_summary(self) -> Dict[str, any]:
        """Get summary of current configuration"""
        return {
            "oracle_providers": {
                name: {
                    "enabled": config.enabled,
                    "reliability_score": config.reliability_score,
                    "api_url": config.api_url,
                    "variance": config.variance,
                    "latency_seconds": config.latency_seconds
                }
                for name, config in self.config.oracle_providers.items()
            },
            "validation": {
                "confidence_threshold": self.config.validation.confidence_threshold,
                "min_data_points": self.config.validation.min_data_points,
                "max_price_deviation_percent": self.config.validation.max_price_deviation_percent
            },
            "aggregation_method": self.config.aggregation.method,
            "fallback_enabled": self.config.fallback.enabled,
            "manipulation_detection_enabled": self.config.manipulation_detection.enabled
        }

    def health_check(self) -> Dict[str, any]:
        """Perform health check on all oracles"""
        results = {
            "overall_status": "healthy",
            "oracle_status": {},
            "active_oracles": 0,
            "total_oracles": len(self.config.oracle_providers),
            "timestamp": datetime.now().isoformat()
        }

        for oracle_name, oracle_config in self.config.oracle_providers.items():
            if oracle_config.enabled:
                status = self.oracle_status.get(oracle_name, OracleStatus.FAILED)
                results["oracle_status"][oracle_name] = {
                    "status": status.value,
                    "reliability": self.reliability_scores.get(oracle_name, 0.0),
                    "url": oracle_config.api_url
                }

                if status == OracleStatus.ACTIVE:
                    results["active_oracles"] += 1

        # Determine overall status based on circuit breaker config
        failure_rate = 1.0 - (results["active_oracles"] / results["total_oracles"])

        if failure_rate >= self.config.circuit_breaker.escalation_thresholds["emergency"]:
            results["overall_status"] = "emergency"
        elif failure_rate >= self.config.circuit_breaker.escalation_thresholds["critical"]:
            results["overall_status"] = "critical"
        elif failure_rate >= self.config.circuit_breaker.escalation_thresholds["warning"]:
            results["overall_status"] = "warning"

        return results