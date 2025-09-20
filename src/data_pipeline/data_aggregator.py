"""
Real-time Data Aggregator - Aggregates data from all MCP services for lending engines
Provides unified data interface with real-time updates and intelligent caching
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import hashlib

from .mcp_connector import MCPConnector, MCPServiceType, get_mcp_connector
from .cache_manager import CacheManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataType(Enum):
    ACCOUNT_INFO = "account_info"
    TRANSACTION_HISTORY = "transaction_history"
    ASSET_PRICE = "asset_price"
    MARKET_DATA = "market_data"
    DEFI_YIELD = "defi_yield"
    NETWORK_STATUS = "network_status"
    COLLATERAL_VALUE = "collateral_value"
    LOAN_METRICS = "loan_metrics"


class AggregationStrategy(Enum):
    LATEST = "latest"
    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    MEDIAN = "median"
    MAX = "max"
    MIN = "min"


@dataclass
class DataPoint:
    """Individual data point with metadata"""
    data_type: DataType
    value: Any
    timestamp: datetime
    source: MCPServiceType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedData:
    """Aggregated data result"""
    data_type: DataType
    value: Any
    timestamp: datetime
    sources: List[MCPServiceType]
    strategy: AggregationStrategy
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriptionConfig:
    """Configuration for data subscription"""
    data_type: DataType
    parameters: Dict[str, Any]
    update_interval: float
    aggregation_strategy: AggregationStrategy = AggregationStrategy.LATEST
    callback: Optional[Callable] = None
    max_age: Optional[float] = None  # Maximum age of data in seconds


class DataAggregator:
    """
    Real-time data aggregator that combines data from multiple MCP services
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.mcp_connector: Optional[MCPConnector] = None
        self.cache_manager = cache_manager

        # Data storage
        self.data_points: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.aggregated_data: Dict[str, AggregatedData] = {}

        # Subscriptions
        self.subscriptions: Dict[str, SubscriptionConfig] = {}
        self.subscription_tasks: Dict[str, asyncio.Task] = {}

        # Real-time feeds
        self.price_feed_active = False
        self.price_callbacks: Dict[int, List[Callable]] = defaultdict(list)

        # Performance metrics
        self.metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "aggregation_time": deque(maxlen=100),
            "data_freshness": deque(maxlen=100)
        }

    async def initialize(self):
        """Initialize the data aggregator"""
        self.mcp_connector = await get_mcp_connector()

        if not self.cache_manager:
            from .cache_manager import CacheManager
            self.cache_manager = CacheManager()
            await self.cache_manager.initialize()

        logger.info("Data Aggregator initialized successfully")

    async def shutdown(self):
        """Shutdown the data aggregator"""
        # Cancel all subscription tasks
        for task in self.subscription_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.subscription_tasks:
            await asyncio.gather(*self.subscription_tasks.values(), return_exceptions=True)

        if self.cache_manager:
            await self.cache_manager.shutdown()

        logger.info("Data Aggregator shutdown complete")

    def _generate_key(self, data_type: DataType, **params) -> str:
        """Generate unique key for data identification"""
        param_str = json.dumps(params, sort_keys=True)
        key_data = f"{data_type.value}:{param_str}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_account_data(self, address: str, include_history: bool = True) -> Dict[str, Any]:
        """Get comprehensive account data"""
        cache_key = self._generate_key(DataType.ACCOUNT_INFO, address=address, history=include_history)

        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            self.metrics["cache_hits"] += 1
            return cached_data

        self.metrics["cache_misses"] += 1
        start_time = time.time()

        try:
            # Get account info from Reader MCP
            account_response = await self.mcp_connector.get_account_info(address)
            if not account_response.success:
                raise Exception(f"Failed to get account info: {account_response.error}")

            result = {
                "address": address,
                "account_info": account_response.data,
                "timestamp": datetime.now().isoformat()
            }

            # Get transaction history if requested
            if include_history:
                tx_response = await self.mcp_connector.get_account_transactions(address, limit=100)
                if tx_response.success:
                    result["transaction_history"] = tx_response.data

            # Get asset values for account holdings
            if account_response.data and "assets" in account_response.data:
                asset_values = await self._get_asset_values(account_response.data["assets"])
                result["asset_values"] = asset_values
                result["total_value_usd"] = sum(asset_values.values())

            # Cache the result
            await self.cache_manager.set(cache_key, result, ttl=60)  # 1 minute TTL

            # Record metrics
            self.metrics["requests_total"] += 1
            self.metrics["aggregation_time"].append(time.time() - start_time)

            return result

        except Exception as e:
            self.metrics["requests_failed"] += 1
            logger.error(f"Failed to get account data for {address}: {e}")
            raise

    async def _get_asset_values(self, assets: List[Dict]) -> Dict[str, float]:
        """Get USD values for a list of assets"""
        asset_values = {}

        for asset in assets:
            asset_id = asset.get("asset-id", 0)
            amount = asset.get("amount", 0)

            try:
                # Get asset price
                price_response = await self.mcp_connector.get_asset_price(asset_id)
                if price_response.success and price_response.data:
                    price_usd = price_response.data.get("price_usd", 0)

                    # Convert amount to proper decimal based on asset decimals
                    decimals = asset.get("decimals", 6)
                    actual_amount = amount / (10 ** decimals)

                    asset_values[str(asset_id)] = actual_amount * price_usd
                else:
                    asset_values[str(asset_id)] = 0

            except Exception as e:
                logger.warning(f"Failed to get price for asset {asset_id}: {e}")
                asset_values[str(asset_id)] = 0

        return asset_values

    async def get_market_data(self, asset_ids: List[int], include_history: bool = False) -> Dict[str, Any]:
        """Get comprehensive market data"""
        cache_key = self._generate_key(DataType.MARKET_DATA, assets=asset_ids, history=include_history)

        # Check cache
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            self.metrics["cache_hits"] += 1
            return cached_data

        self.metrics["cache_misses"] += 1
        start_time = time.time()

        try:
            # Get current market data
            market_response = await self.mcp_connector.get_market_data(asset_ids)
            if not market_response.success:
                raise Exception(f"Failed to get market data: {market_response.error}")

            result = {
                "asset_ids": asset_ids,
                "market_data": market_response.data,
                "timestamp": datetime.now().isoformat()
            }

            # Get price history if requested
            if include_history:
                history_data = {}
                for asset_id in asset_ids:
                    try:
                        history_response = await self.mcp_connector.get_price_history(asset_id, "24h")
                        if history_response.success:
                            history_data[str(asset_id)] = history_response.data
                    except Exception as e:
                        logger.warning(f"Failed to get history for asset {asset_id}: {e}")

                result["price_history"] = history_data

            # Get DeFi yields
            yield_response = await self.mcp_connector.get_defi_yields()
            if yield_response.success:
                result["defi_yields"] = yield_response.data

            # Cache the result
            await self.cache_manager.set(cache_key, result, ttl=30)  # 30 second TTL

            # Record metrics
            self.metrics["requests_total"] += 1
            self.metrics["aggregation_time"].append(time.time() - start_time)

            return result

        except Exception as e:
            self.metrics["requests_failed"] += 1
            logger.error(f"Failed to get market data: {e}")
            raise

    async def calculate_collateral_value(self, address: str) -> Dict[str, Any]:
        """Calculate collateral value for an address"""
        cache_key = self._generate_key(DataType.COLLATERAL_VALUE, address=address)

        # Check cache
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            self.metrics["cache_hits"] += 1
            return cached_data

        self.metrics["cache_misses"] += 1

        try:
            # Get account data
            account_data = await self.get_account_data(address, include_history=False)

            if "asset_values" not in account_data:
                return {"total_collateral_usd": 0, "assets": [], "timestamp": datetime.now().isoformat()}

            # Calculate collateral with risk factors
            collateral_assets = []
            total_collateral = 0

            for asset_id, value_usd in account_data["asset_values"].items():
                # Apply collateral factor based on asset type
                collateral_factor = await self._get_collateral_factor(int(asset_id))
                collateral_value = value_usd * collateral_factor

                collateral_assets.append({
                    "asset_id": int(asset_id),
                    "value_usd": value_usd,
                    "collateral_factor": collateral_factor,
                    "collateral_value": collateral_value
                })

                total_collateral += collateral_value

            result = {
                "address": address,
                "total_collateral_usd": total_collateral,
                "assets": collateral_assets,
                "timestamp": datetime.now().isoformat()
            }

            # Cache for 2 minutes
            await self.cache_manager.set(cache_key, result, ttl=120)

            return result

        except Exception as e:
            logger.error(f"Failed to calculate collateral value for {address}: {e}")
            raise

    async def _get_collateral_factor(self, asset_id: int) -> float:
        """Get collateral factor for an asset"""
        # Default collateral factors - in production, this would come from configuration
        collateral_factors = {
            0: 0.8,    # ALGO - 80%
            1: 0.75,   # Other major assets - 75%
            # Add more asset-specific factors
        }

        return collateral_factors.get(asset_id, 0.5)  # Default 50% for unknown assets

    async def get_lending_metrics(self, protocol: Optional[str] = None) -> Dict[str, Any]:
        """Get lending protocol metrics"""
        cache_key = self._generate_key(DataType.LOAN_METRICS, protocol=protocol)

        # Check cache
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            self.metrics["cache_hits"] += 1
            return cached_data

        self.metrics["cache_misses"] += 1

        try:
            # Get DeFi yields
            yield_response = await self.mcp_connector.get_defi_yields(protocol)
            if not yield_response.success:
                raise Exception(f"Failed to get DeFi yields: {yield_response.error}")

            # Calculate lending metrics
            yields_data = yield_response.data

            result = {
                "protocol": protocol,
                "yields": yields_data,
                "metrics": {
                    "avg_lending_rate": self._calculate_average_rate(yields_data, "lending"),
                    "avg_borrowing_rate": self._calculate_average_rate(yields_data, "borrowing"),
                    "total_tvl": self._calculate_total_tvl(yields_data),
                    "utilization_rates": self._calculate_utilization_rates(yields_data)
                },
                "timestamp": datetime.now().isoformat()
            }

            # Cache for 5 minutes
            await self.cache_manager.set(cache_key, result, ttl=300)

            return result

        except Exception as e:
            logger.error(f"Failed to get lending metrics: {e}")
            raise

    def _calculate_average_rate(self, yields_data: Dict, rate_type: str) -> float:
        """Calculate average rate from yields data"""
        if not yields_data or rate_type not in yields_data:
            return 0.0

        rates = []
        for protocol_data in yields_data[rate_type]:
            if isinstance(protocol_data, dict) and "rate" in protocol_data:
                rates.append(protocol_data["rate"])

        return statistics.mean(rates) if rates else 0.0

    def _calculate_total_tvl(self, yields_data: Dict) -> float:
        """Calculate total TVL from yields data"""
        if not yields_data or "tvl" not in yields_data:
            return 0.0

        total_tvl = 0.0
        for protocol_data in yields_data["tvl"]:
            if isinstance(protocol_data, dict) and "amount" in protocol_data:
                total_tvl += protocol_data["amount"]

        return total_tvl

    def _calculate_utilization_rates(self, yields_data: Dict) -> Dict[str, float]:
        """Calculate utilization rates from yields data"""
        utilization = {}

        if yields_data and "utilization" in yields_data:
            for protocol_data in yields_data["utilization"]:
                if isinstance(protocol_data, dict):
                    protocol = protocol_data.get("protocol", "unknown")
                    rate = protocol_data.get("rate", 0.0)
                    utilization[protocol] = rate

        return utilization

    async def subscribe_to_real_time_data(self, config: SubscriptionConfig) -> str:
        """Subscribe to real-time data updates"""
        subscription_id = self._generate_key(
            config.data_type,
            **config.parameters,
            interval=config.update_interval
        )

        self.subscriptions[subscription_id] = config

        # Start subscription task
        task = asyncio.create_task(self._subscription_loop(subscription_id, config))
        self.subscription_tasks[subscription_id] = task

        logger.info(f"Started subscription {subscription_id} for {config.data_type.value}")
        return subscription_id

    async def _subscription_loop(self, subscription_id: str, config: SubscriptionConfig):
        """Main loop for a data subscription"""
        while subscription_id in self.subscriptions:
            try:
                start_time = time.time()

                # Get fresh data based on data type
                if config.data_type == DataType.MARKET_DATA:
                    data = await self.get_market_data(
                        config.parameters.get("asset_ids", []),
                        include_history=config.parameters.get("include_history", False)
                    )
                elif config.data_type == DataType.ACCOUNT_INFO:
                    data = await self.get_account_data(
                        config.parameters["address"],
                        include_history=config.parameters.get("include_history", True)
                    )
                elif config.data_type == DataType.COLLATERAL_VALUE:
                    data = await self.calculate_collateral_value(config.parameters["address"])
                elif config.data_type == DataType.LOAN_METRICS:
                    data = await self.get_lending_metrics(config.parameters.get("protocol"))
                else:
                    logger.warning(f"Unknown data type in subscription: {config.data_type}")
                    continue

                # Call callback if provided
                if config.callback:
                    try:
                        await config.callback(data)
                    except Exception as e:
                        logger.error(f"Subscription callback error: {e}")

                # Record data freshness
                self.metrics["data_freshness"].append(time.time() - start_time)

                # Wait for next update
                await asyncio.sleep(config.update_interval)

            except asyncio.CancelledError:
                logger.info(f"Subscription {subscription_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Subscription error for {subscription_id}: {e}")
                await asyncio.sleep(config.update_interval)

    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from real-time data"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]

        if subscription_id in self.subscription_tasks:
            task = self.subscription_tasks[subscription_id]
            task.cancel()
            del self.subscription_tasks[subscription_id]

            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info(f"Unsubscribed from {subscription_id}")

    async def start_price_feed(self, asset_ids: List[int]):
        """Start real-time price feed"""
        if self.price_feed_active:
            logger.warning("Price feed already active")
            return

        self.price_feed_active = True

        try:
            await self.mcp_connector.subscribe_to_price_feed(
                asset_ids,
                self._handle_price_update
            )
        except Exception as e:
            logger.error(f"Failed to start price feed: {e}")
            self.price_feed_active = False
            raise

    async def _handle_price_update(self, price_data: Dict[str, Any]):
        """Handle incoming price updates"""
        try:
            asset_id = price_data.get("asset_id")
            price = price_data.get("price")
            timestamp = datetime.now()

            if asset_id is not None and price is not None:
                # Store data point
                key = self._generate_key(DataType.ASSET_PRICE, asset_id=asset_id)
                data_point = DataPoint(
                    data_type=DataType.ASSET_PRICE,
                    value=price,
                    timestamp=timestamp,
                    source=MCPServiceType.MARKET_DATA,
                    metadata=price_data
                )

                self.data_points[key].append(data_point)

                # Update cache
                await self.cache_manager.set(
                    f"price:{asset_id}",
                    {"price": price, "timestamp": timestamp.isoformat()},
                    ttl=10  # 10 second TTL for real-time prices
                )

                # Call registered callbacks
                for callback in self.price_callbacks[asset_id]:
                    try:
                        await callback(price_data)
                    except Exception as e:
                        logger.error(f"Price callback error: {e}")

        except Exception as e:
            logger.error(f"Error handling price update: {e}")

    def register_price_callback(self, asset_id: int, callback: Callable):
        """Register callback for price updates"""
        self.price_callbacks[asset_id].append(callback)

    def unregister_price_callback(self, asset_id: int, callback: Callable):
        """Unregister price callback"""
        if asset_id in self.price_callbacks:
            try:
                self.price_callbacks[asset_id].remove(callback)
            except ValueError:
                pass

    async def simulate_transaction_impact(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate transaction impact on account and market"""
        try:
            # Use Writer MCP to simulate transaction
            sim_response = await self.mcp_connector.simulate_transaction(transaction_data)
            if not sim_response.success:
                raise Exception(f"Transaction simulation failed: {sim_response.error}")

            # Get fee estimate
            fee_response = await self.mcp_connector.estimate_fee(transaction_data)

            result = {
                "simulation": sim_response.data,
                "estimated_fee": fee_response.data if fee_response.success else None,
                "timestamp": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Failed to simulate transaction impact: {e}")
            raise

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get aggregator performance metrics"""
        return {
            "requests_total": self.metrics["requests_total"],
            "requests_failed": self.metrics["requests_failed"],
            "success_rate": (
                (self.metrics["requests_total"] - self.metrics["requests_failed"])
                / max(self.metrics["requests_total"], 1)
            ),
            "cache_hit_rate": (
                self.metrics["cache_hits"]
                / max(self.metrics["cache_hits"] + self.metrics["cache_misses"], 1)
            ),
            "avg_aggregation_time": (
                statistics.mean(self.metrics["aggregation_time"])
                if self.metrics["aggregation_time"] else 0
            ),
            "avg_data_freshness": (
                statistics.mean(self.metrics["data_freshness"])
                if self.metrics["data_freshness"] else 0
            ),
            "active_subscriptions": len(self.subscriptions),
            "price_feed_active": self.price_feed_active
        }


# Singleton instance
_data_aggregator_instance: Optional[DataAggregator] = None


async def get_data_aggregator() -> DataAggregator:
    """Get singleton data aggregator instance"""
    global _data_aggregator_instance

    if _data_aggregator_instance is None:
        _data_aggregator_instance = DataAggregator()
        await _data_aggregator_instance.initialize()

    return _data_aggregator_instance


async def close_data_aggregator():
    """Close singleton data aggregator instance"""
    global _data_aggregator_instance

    if _data_aggregator_instance:
        await _data_aggregator_instance.shutdown()
        _data_aggregator_instance = None


if __name__ == "__main__":
    async def test_aggregator():
        """Test data aggregator functionality"""
        aggregator = DataAggregator()
        await aggregator.initialize()

        try:
            # Test account data
            account_data = await aggregator.get_account_data("TEST_ADDRESS")
            print(f"Account data: {account_data.keys()}")

            # Test market data
            market_data = await aggregator.get_market_data([0, 1])  # ALGO and another asset
            print(f"Market data: {market_data.keys()}")

            # Test performance metrics
            metrics = aggregator.get_performance_metrics()
            print(f"Performance metrics: {metrics}")

        finally:
            await aggregator.shutdown()

    asyncio.run(test_aggregator())