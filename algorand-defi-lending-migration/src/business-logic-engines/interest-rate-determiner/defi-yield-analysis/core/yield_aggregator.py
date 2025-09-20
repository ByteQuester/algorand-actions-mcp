"""
Yield Aggregator

Combines yield data from multiple DeFi protocols to provide comprehensive
interest rate analysis for Algorand-based lending platforms.
"""

import asyncio
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
import statistics
import math

# Import individual protocol analyzers
from .algofi_yields import AlgofiYieldsAnalyzer, AlgofiYieldData
from .folks_finance_yields import FolksFinanceYieldsAnalyzer, FolksYieldData

@dataclass
class ProtocolYield:
    """Represents yield data from a single protocol"""
    protocol_name: str
    supply_apy: float
    borrow_apy: float
    additional_rewards: float
    total_tvl: float
    utilization_rate: float
    confidence_score: float
    weight: float
    timestamp: datetime
    supported_assets: List[str]

@dataclass
class AggregatedYield:
    """Aggregated yield data across all protocols"""
    weighted_supply_apy: float
    weighted_borrow_apy: float
    total_rewards_apy: float
    market_size_weighted_apy: float
    protocol_count: int
    total_market_tvl: float
    average_confidence: float
    yield_spread: float
    volatility_estimate: float
    timestamp: datetime
    protocol_breakdown: List[ProtocolYield]
    metadata: Dict[str, Any]

@dataclass
class AssetSpecificYield:
    """Yield data for a specific asset across protocols"""
    asset_name: str
    protocol_yields: Dict[str, float]
    weighted_average_yield: float
    best_yield_protocol: str
    worst_yield_protocol: str
    yield_range: float
    liquidity_weighted_yield: float
    confidence_score: float
    timestamp: datetime

class YieldAggregator:
    """
    Aggregates yield data from multiple DeFi protocols to provide
    comprehensive interest rate analysis for lending platforms.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the yield aggregator"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()

        # Initialize protocol analyzers
        self.analyzers = {
            'algofi': AlgofiYieldsAnalyzer(config_path),
            'folks_finance': FolksFinanceYieldsAnalyzer(config_path)
        }

        self.cache = {}
        self.aggregation_history = []

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            # Fallback configuration
            return {
                'defi_protocols': {
                    'algofi': {'weight': 0.4, 'enabled': True},
                    'folks_finance': {'weight': 0.35, 'enabled': True}
                },
                'aggregation_methodology': {
                    'primary_method': 'liquidity_weighted',
                    'outlier_removal': True
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the aggregator"""
        logger = logging.getLogger('yield_aggregator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def aggregate_yields(self) -> AggregatedYield:
        """
        Aggregate yields from all enabled protocols

        Returns:
            AggregatedYield: Comprehensive yield analysis
        """
        try:
            # Check cache first
            if self._is_cache_valid('aggregated_yields'):
                return self.cache['aggregated_yields']

            # Fetch data from all protocols
            protocol_data = await self._fetch_all_protocol_data()

            if not protocol_data:
                return self._get_fallback_aggregated_yield()

            # Convert to ProtocolYield objects
            protocol_yields = self._convert_to_protocol_yields(protocol_data)

            # Remove outliers if enabled
            if self.config['aggregation_methodology']['outlier_removal']:
                protocol_yields = self._remove_outliers(protocol_yields)

            # Calculate aggregated metrics
            aggregated = self._calculate_aggregated_metrics(protocol_yields)

            # Cache the result
            self.cache['aggregated_yields'] = aggregated
            self.cache['aggregated_yields_timestamp'] = datetime.now()

            # Store in history
            self.aggregation_history.append(aggregated)
            if len(self.aggregation_history) > 100:  # Keep last 100 records
                self.aggregation_history.pop(0)

            return aggregated

        except Exception as e:
            self.logger.error(f"Error aggregating yields: {e}")
            return self._get_fallback_aggregated_yield()

    async def _fetch_all_protocol_data(self) -> Dict[str, Union[AlgofiYieldData, FolksYieldData]]:
        """Fetch yield data from all enabled protocols"""
        protocol_data = {}
        enabled_protocols = {
            name: config for name, config in self.config['defi_protocols'].items()
            if config.get('enabled', True) and name in self.analyzers
        }

        # Fetch data from all protocols concurrently
        tasks = []
        for protocol_name in enabled_protocols.keys():
            if protocol_name == 'algofi':
                tasks.append(('algofi', self.analyzers['algofi'].analyze_algofi_yields()))
            elif protocol_name == 'folks_finance':
                tasks.append(('folks_finance', self.analyzers['folks_finance'].analyze_folks_yields()))

        # Wait for all tasks to complete
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

        # Process results
        for i, (protocol_name, _) in enumerate(tasks):
            result = results[i]
            if not isinstance(result, Exception):
                protocol_data[protocol_name] = result
            else:
                self.logger.error(f"Error fetching data from {protocol_name}: {result}")

        return protocol_data

    def _convert_to_protocol_yields(self, protocol_data: Dict) -> List[ProtocolYield]:
        """Convert protocol-specific data to standardized ProtocolYield objects"""
        protocol_yields = []

        for protocol_name, data in protocol_data.items():
            try:
                config = self.config['defi_protocols'].get(protocol_name, {})
                weight = config.get('weight', 0.1)

                if isinstance(data, AlgofiYieldData):
                    yield_obj = ProtocolYield(
                        protocol_name='Algofi',
                        supply_apy=data.weighted_average_supply_apy,
                        borrow_apy=data.weighted_average_borrow_apy,
                        additional_rewards=0.0,  # Algofi doesn't have separate rewards
                        total_tvl=data.total_value_locked,
                        utilization_rate=data.protocol_utilization,
                        confidence_score=data.confidence_score,
                        weight=weight,
                        timestamp=data.timestamp,
                        supported_assets=[m.asset_name for m in data.markets]
                    )

                elif isinstance(data, FolksYieldData):
                    yield_obj = ProtocolYield(
                        protocol_name='Folks Finance',
                        supply_apy=data.weighted_supply_apy,
                        borrow_apy=data.weighted_borrow_apy,
                        additional_rewards=data.total_rewards_apy,
                        total_tvl=data.protocol_tvl,
                        utilization_rate=data.average_utilization,
                        confidence_score=data.confidence_score,
                        weight=weight,
                        timestamp=data.timestamp,
                        supported_assets=[p.asset_name for p in data.pools]
                    )

                else:
                    self.logger.warning(f"Unknown data type for protocol {protocol_name}")
                    continue

                protocol_yields.append(yield_obj)

            except Exception as e:
                self.logger.error(f"Error converting data for {protocol_name}: {e}")

        return protocol_yields

    def _remove_outliers(self, protocol_yields: List[ProtocolYield]) -> List[ProtocolYield]:
        """Remove statistical outliers from protocol yields"""
        if len(protocol_yields) < 3:
            return protocol_yields  # Need at least 3 data points

        # Remove outliers based on supply APY
        supply_apys = [p.supply_apy for p in protocol_yields]
        mean_apy = statistics.mean(supply_apys)
        std_apy = statistics.stdev(supply_apys) if len(supply_apys) > 1 else 0

        threshold = self.config['aggregation_methodology'].get('outlier_threshold_std', 2.0)

        filtered_yields = []
        for yield_obj in protocol_yields:
            # Check if yield is within acceptable range
            if std_apy == 0 or abs(yield_obj.supply_apy - mean_apy) <= threshold * std_apy:
                filtered_yields.append(yield_obj)
            else:
                self.logger.warning(
                    f"Removing outlier: {yield_obj.protocol_name} with {yield_obj.supply_apy:.2%} APY"
                )

        return filtered_yields if filtered_yields else protocol_yields

    def _calculate_aggregated_metrics(self, protocol_yields: List[ProtocolYield]) -> AggregatedYield:
        """Calculate aggregated metrics from protocol yields"""
        if not protocol_yields:
            return self._get_fallback_aggregated_yield()

        # Normalize weights
        total_weight = sum(p.weight for p in protocol_yields)
        if total_weight > 0:
            for p in protocol_yields:
                p.weight = p.weight / total_weight
        else:
            equal_weight = 1.0 / len(protocol_yields)
            for p in protocol_yields:
                p.weight = equal_weight

        # Calculate weighted averages
        method = self.config['aggregation_methodology']['primary_method']

        if method == 'liquidity_weighted':
            weighted_supply_apy = self._calculate_liquidity_weighted_apy(protocol_yields, 'supply')
            weighted_borrow_apy = self._calculate_liquidity_weighted_apy(protocol_yields, 'borrow')
        else:
            # Fallback to simple weighted average
            weighted_supply_apy = sum(p.supply_apy * p.weight for p in protocol_yields)
            weighted_borrow_apy = sum(p.borrow_apy * p.weight for p in protocol_yields)

        # Calculate additional metrics
        total_rewards_apy = sum(p.additional_rewards * p.weight for p in protocol_yields)
        market_size_weighted_apy = self._calculate_market_size_weighted_apy(protocol_yields)
        total_market_tvl = sum(p.total_tvl for p in protocol_yields)
        average_confidence = statistics.mean([p.confidence_score for p in protocol_yields])

        # Calculate yield spread and volatility
        supply_apys = [p.supply_apy for p in protocol_yields]
        yield_spread = max(supply_apys) - min(supply_apys) if len(supply_apys) > 1 else 0.0
        volatility_estimate = statistics.stdev(supply_apys) if len(supply_apys) > 1 else 0.0

        return AggregatedYield(
            weighted_supply_apy=weighted_supply_apy,
            weighted_borrow_apy=weighted_borrow_apy,
            total_rewards_apy=total_rewards_apy,
            market_size_weighted_apy=market_size_weighted_apy,
            protocol_count=len(protocol_yields),
            total_market_tvl=total_market_tvl,
            average_confidence=average_confidence,
            yield_spread=yield_spread,
            volatility_estimate=volatility_estimate,
            timestamp=datetime.now(),
            protocol_breakdown=protocol_yields,
            metadata={
                'aggregation_method': method,
                'outliers_removed': self.config['aggregation_methodology']['outlier_removal'],
                'data_sources': [p.protocol_name for p in protocol_yields]
            }
        )

    def _calculate_liquidity_weighted_apy(self, protocol_yields: List[ProtocolYield],
                                        yield_type: str) -> float:
        """Calculate liquidity-weighted APY"""
        total_weighted_apy = 0.0
        total_weight = 0.0

        for p in protocol_yields:
            # Use TVL as liquidity weight
            tvl_weight = p.total_tvl

            if yield_type == 'supply':
                apy = p.supply_apy
            elif yield_type == 'borrow':
                apy = p.borrow_apy
            else:
                apy = p.supply_apy

            total_weighted_apy += apy * tvl_weight
            total_weight += tvl_weight

        if total_weight > 0:
            return total_weighted_apy / total_weight
        else:
            # Fallback to simple average
            if yield_type == 'supply':
                return statistics.mean([p.supply_apy for p in protocol_yields])
            elif yield_type == 'borrow':
                return statistics.mean([p.borrow_apy for p in protocol_yields])
            else:
                return 0.0

    def _calculate_market_size_weighted_apy(self, protocol_yields: List[ProtocolYield]) -> float:
        """Calculate market size weighted APY (by TVL)"""
        return self._calculate_liquidity_weighted_apy(protocol_yields, 'supply')

    async def get_asset_specific_yields(self, asset_name: str) -> AssetSpecificYield:
        """
        Get yield analysis for a specific asset across protocols

        Args:
            asset_name: Name of the asset (e.g., 'ALGO', 'USDC')

        Returns:
            AssetSpecificYield: Asset-specific yield analysis
        """
        try:
            protocol_yields = {}
            tvl_weights = {}

            # Fetch asset-specific data from each protocol
            for protocol_name, analyzer in self.analyzers.items():
                try:
                    if protocol_name == 'algofi':
                        market = await analyzer.get_market_by_asset(asset_name)
                        if market:
                            protocol_yields[protocol_name] = market.supply_apy
                            tvl_weights[protocol_name] = market.total_supply * 0.25  # Approximate USD value

                    elif protocol_name == 'folks_finance':
                        pool = await analyzer.get_pool_by_asset(asset_name)
                        if pool:
                            total_yield = pool.supply_apy + pool.pool_rewards_apy
                            protocol_yields[protocol_name] = total_yield
                            tvl_weights[protocol_name] = pool.total_deposited * pool.oracle_price

                except Exception as e:
                    self.logger.warning(f"Error fetching {asset_name} from {protocol_name}: {e}")

            if not protocol_yields:
                return self._get_fallback_asset_yield(asset_name)

            # Calculate metrics
            weighted_average = self._calculate_weighted_average(protocol_yields, tvl_weights)
            best_protocol = max(protocol_yields, key=protocol_yields.get)
            worst_protocol = min(protocol_yields, key=protocol_yields.get)
            yield_range = max(protocol_yields.values()) - min(protocol_yields.values())

            # Calculate confidence based on data availability and consistency
            confidence = self._calculate_asset_confidence(protocol_yields, tvl_weights)

            return AssetSpecificYield(
                asset_name=asset_name,
                protocol_yields=protocol_yields,
                weighted_average_yield=weighted_average,
                best_yield_protocol=best_protocol,
                worst_yield_protocol=worst_protocol,
                yield_range=yield_range,
                liquidity_weighted_yield=weighted_average,  # Same as weighted average here
                confidence_score=confidence,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error getting asset-specific yields for {asset_name}: {e}")
            return self._get_fallback_asset_yield(asset_name)

    def _calculate_weighted_average(self, yields: Dict[str, float],
                                  weights: Dict[str, float]) -> float:
        """Calculate weighted average yield"""
        total_weighted_yield = 0.0
        total_weight = 0.0

        for protocol, yield_value in yields.items():
            weight = weights.get(protocol, 1.0)
            total_weighted_yield += yield_value * weight
            total_weight += weight

        if total_weight > 0:
            return total_weighted_yield / total_weight
        else:
            return statistics.mean(yields.values()) if yields else 0.0

    def _calculate_asset_confidence(self, yields: Dict[str, float],
                                  weights: Dict[str, float]) -> float:
        """Calculate confidence score for asset-specific analysis"""
        confidence = 1.0

        # Reduce confidence for fewer protocols
        if len(yields) < 2:
            confidence *= 0.7

        # Reduce confidence for high yield variance
        if len(yields) > 1:
            yield_values = list(yields.values())
            if statistics.stdev(yield_values) > 0.02:  # > 2% standard deviation
                confidence *= 0.8

        # Reduce confidence for low liquidity
        total_weight = sum(weights.values())
        if total_weight < 1000000:  # < $1M total liquidity
            confidence *= 0.6

        return max(confidence, 0.1)

    async def get_yield_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze yield trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Dict containing trend analysis
        """
        try:
            # Use historical data if available, otherwise simulate
            if len(self.aggregation_history) >= days:
                historical_data = self.aggregation_history[-days:]
            else:
                # Simulate historical data for demo purposes
                current_yield = await self.aggregate_yields()
                historical_data = self._simulate_historical_yields(current_yield, days)

            # Calculate trends
            supply_apys = [data.weighted_supply_apy for data in historical_data]
            borrow_apys = [data.weighted_borrow_apy for data in historical_data]

            supply_trend = "increasing" if supply_apys[-1] > supply_apys[0] else "decreasing"
            borrow_trend = "increasing" if borrow_apys[-1] > borrow_apys[0] else "decreasing"

            return {
                "period_days": days,
                "supply_apy_trend": {
                    "direction": supply_trend,
                    "start_apy": supply_apys[0],
                    "end_apy": supply_apys[-1],
                    "change": supply_apys[-1] - supply_apys[0],
                    "volatility": statistics.stdev(supply_apys) if len(supply_apys) > 1 else 0,
                    "average": statistics.mean(supply_apys)
                },
                "borrow_apy_trend": {
                    "direction": borrow_trend,
                    "start_apy": borrow_apys[0],
                    "end_apy": borrow_apys[-1],
                    "change": borrow_apys[-1] - borrow_apys[0],
                    "volatility": statistics.stdev(borrow_apys) if len(borrow_apys) > 1 else 0,
                    "average": statistics.mean(borrow_apys)
                },
                "market_metrics": {
                    "average_tvl": statistics.mean([data.total_market_tvl for data in historical_data]),
                    "tvl_trend": "increasing" if historical_data[-1].total_market_tvl > historical_data[0].total_market_tvl else "decreasing"
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing yield trends: {e}")
            return {"error": str(e)}

    def _simulate_historical_yields(self, current_yield: AggregatedYield, days: int) -> List[AggregatedYield]:
        """Simulate historical yield data for trend analysis"""
        historical_data = []
        base_supply_apy = current_yield.weighted_supply_apy
        base_borrow_apy = current_yield.weighted_borrow_apy

        for i in range(days):
            # Add realistic daily variations
            supply_variation = math.sin(i * 0.2) * 0.003  # ±0.3% variation
            borrow_variation = math.sin(i * 0.15) * 0.004  # ±0.4% variation

            # Create historical data point
            historical_point = AggregatedYield(
                weighted_supply_apy=base_supply_apy + supply_variation,
                weighted_borrow_apy=base_borrow_apy + borrow_variation,
                total_rewards_apy=current_yield.total_rewards_apy,
                market_size_weighted_apy=current_yield.market_size_weighted_apy + supply_variation,
                protocol_count=current_yield.protocol_count,
                total_market_tvl=current_yield.total_market_tvl * (1 + i * 0.01),  # Growing TVL
                average_confidence=current_yield.average_confidence,
                yield_spread=current_yield.yield_spread,
                volatility_estimate=current_yield.volatility_estimate,
                timestamp=datetime.now() - timedelta(days=days-i),
                protocol_breakdown=current_yield.protocol_breakdown,
                metadata=current_yield.metadata
            )
            historical_data.append(historical_point)

        return historical_data

    def _get_fallback_aggregated_yield(self) -> AggregatedYield:
        """Return fallback aggregated yield when analysis fails"""
        fallback_protocol = ProtocolYield(
            protocol_name='Fallback',
            supply_apy=0.04,
            borrow_apy=0.06,
            additional_rewards=0.01,
            total_tvl=20000000,
            utilization_rate=0.7,
            confidence_score=0.5,
            weight=1.0,
            timestamp=datetime.now(),
            supported_assets=['ALGO', 'USDC']
        )

        return AggregatedYield(
            weighted_supply_apy=0.04,
            weighted_borrow_apy=0.06,
            total_rewards_apy=0.01,
            market_size_weighted_apy=0.04,
            protocol_count=1,
            total_market_tvl=20000000,
            average_confidence=0.5,
            yield_spread=0.0,
            volatility_estimate=0.005,
            timestamp=datetime.now(),
            protocol_breakdown=[fallback_protocol],
            metadata={'fallback': True}
        )

    def _get_fallback_asset_yield(self, asset_name: str) -> AssetSpecificYield:
        """Return fallback asset-specific yield"""
        fallback_yield = 0.04 if asset_name.upper() == 'ALGO' else 0.03

        return AssetSpecificYield(
            asset_name=asset_name,
            protocol_yields={'fallback': fallback_yield},
            weighted_average_yield=fallback_yield,
            best_yield_protocol='fallback',
            worst_yield_protocol='fallback',
            yield_range=0.0,
            liquidity_weighted_yield=fallback_yield,
            confidence_score=0.3,
            timestamp=datetime.now()
        )

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False

        timestamp_key = f"{key}_timestamp"
        if timestamp_key not in self.cache:
            return False

        cache_expiry = self.config.get('historical_data', {}).get('cache_expiry_minutes', 5)
        expiry_time = self.cache[timestamp_key] + timedelta(minutes=cache_expiry)

        return datetime.now() < expiry_time

# Example usage and testing
async def main():
    """Example usage of the YieldAggregator"""
    aggregator = YieldAggregator()

    print("=== DeFi Yield Aggregator Demo ===")

    # Aggregate yields from all protocols
    print("\n1. Aggregated Yield Analysis:")
    aggregated = await aggregator.aggregate_yields()
    print(f"   Weighted Supply APY: {aggregated.weighted_supply_apy:.2%}")
    print(f"   Weighted Borrow APY: {aggregated.weighted_borrow_apy:.2%}")
    print(f"   Total Rewards APY: {aggregated.total_rewards_apy:.2%}")
    print(f"   Market Size Weighted APY: {aggregated.market_size_weighted_apy:.2%}")
    print(f"   Protocol Count: {aggregated.protocol_count}")
    print(f"   Total Market TVL: ${aggregated.total_market_tvl:,.0f}")
    print(f"   Yield Spread: {aggregated.yield_spread:.2%}")
    print(f"   Average Confidence: {aggregated.average_confidence:.2f}")

    # Show protocol breakdown
    print(f"\n2. Protocol Breakdown ({len(aggregated.protocol_breakdown)} protocols):")
    for protocol in aggregated.protocol_breakdown:
        print(f"   {protocol.protocol_name}:")
        print(f"     Supply APY: {protocol.supply_apy:.2%}")
        print(f"     Borrow APY: {protocol.borrow_apy:.2%}")
        print(f"     Additional Rewards: {protocol.additional_rewards:.2%}")
        print(f"     TVL: ${protocol.total_tvl:,.0f}")
        print(f"     Weight: {protocol.weight:.1%}")
        print(f"     Confidence: {protocol.confidence_score:.2f}")

    # Asset-specific analysis
    print("\n3. Asset-Specific Analysis:")
    for asset in ['ALGO', 'USDC']:
        asset_yield = await aggregator.get_asset_specific_yields(asset)
        print(f"   {asset}:")
        print(f"     Weighted Average Yield: {asset_yield.weighted_average_yield:.2%}")
        print(f"     Best Protocol: {asset_yield.best_yield_protocol}")
        print(f"     Yield Range: {asset_yield.yield_range:.2%}")
        print(f"     Protocol Yields:")
        for protocol, yield_value in asset_yield.protocol_yields.items():
            print(f"       {protocol}: {yield_value:.2%}")

    # Yield trends
    print("\n4. Yield Trends (7 days):")
    trends = await aggregator.get_yield_trends(7)
    if "error" not in trends:
        supply_trend = trends['supply_apy_trend']
        print(f"   Supply APY Trend: {supply_trend['direction']}")
        print(f"   Change: {supply_trend['change']:+.2%}")
        print(f"   Volatility: {supply_trend['volatility']:.2%}")
        print(f"   Average: {supply_trend['average']:.2%}")

if __name__ == "__main__":
    asyncio.run(main())