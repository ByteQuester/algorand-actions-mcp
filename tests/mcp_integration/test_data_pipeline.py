#!/usr/bin/env python3
"""
Data Pipeline Tests for MCP Services Integration

Comprehensive testing of data flow between MCP services and lending engines:
- Reader MCP: Account data, asset information, transaction history
- Writer MCP: Transaction broadcasting, state updates
- Market Data MCP: Real-time pricing, market conditions
- Data validation, transformation, and error handling

Features:
- Real blockchain data validation
- Data consistency checks across services
- Pipeline performance monitoring
- Error recovery and fallback testing
- Data fixtures management
- Cross-service data correlation
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import sys
import statistics
from decimal import Decimal

# Import test framework
from test_framework import (
    MCPServiceClient, ServiceConfig, ServiceHealth,
    PerformanceMetrics, TestResult, TestMode
)

# Add lending ecosystem to path
lending_path = Path(__file__).parent.parent.parent / "algorand-lending-ecosystem" / "algorand-lending-business-logic"
sys.path.insert(0, str(lending_path))

try:
    from algorand_lending_bl import (
        AlgorandAddress, ASAToken, AssetValuation,
        CollateralPosition, DEFAULT_CONFIG
    )
except ImportError as e:
    logging.error(f"Failed to import lending models: {e}")


@dataclass
class DataFixture:
    """Test data fixture"""
    name: str
    data_type: str
    description: str
    data: Dict[str, Any]
    expected_validation: bool = True
    performance_threshold: float = 5.0  # seconds


@dataclass
class PipelineTestConfig:
    """Configuration for data pipeline tests"""
    use_real_data: bool = True
    performance_mode: bool = False
    concurrent_requests: int = 5
    data_consistency_checks: bool = True
    error_injection: bool = False
    timeout_multiplier: float = 1.0


class DataValidator:
    """Validates data from MCP services"""

    @staticmethod
    def validate_account_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate account data structure"""
        errors = []

        if not isinstance(data, dict):
            errors.append("Data is not a dictionary")
            return False, errors

        required_fields = ["address", "amount", "amount-without-pending-rewards"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "address" in data:
            if not isinstance(data["address"], str) or len(data["address"]) != 58:
                errors.append("Invalid address format")

        if "amount" in data:
            if not isinstance(data["amount"], (int, float)) or data["amount"] < 0:
                errors.append("Invalid amount value")

        if "assets" in data:
            if not isinstance(data["assets"], list):
                errors.append("Assets should be a list")
            else:
                for i, asset in enumerate(data["assets"]):
                    if not isinstance(asset, dict):
                        errors.append(f"Asset {i} is not a dictionary")
                    elif "asset-id" not in asset or "amount" not in asset:
                        errors.append(f"Asset {i} missing required fields")

        return len(errors) == 0, errors

    @staticmethod
    def validate_asset_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate asset data structure"""
        errors = []

        if not isinstance(data, dict):
            errors.append("Data is not a dictionary")
            return False, errors

        required_fields = ["index", "params"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "params" in data and isinstance(data["params"], dict):
            param_fields = ["total", "decimals", "name"]
            for field in param_fields:
                if field not in data["params"]:
                    errors.append(f"Missing asset param: {field}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_market_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate market data structure"""
        errors = []

        if not isinstance(data, dict):
            errors.append("Data is not a dictionary")
            return False, errors

        required_fields = ["symbol", "price", "timestamp"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "price" in data:
            if not isinstance(data["price"], (int, float, str)) or float(data["price"]) <= 0:
                errors.append("Invalid price value")

        if "timestamp" in data:
            try:
                datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                errors.append("Invalid timestamp format")

        return len(errors) == 0, errors

    @staticmethod
    def validate_transaction_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate transaction data structure"""
        errors = []

        if not isinstance(data, dict):
            errors.append("Data is not a dictionary")
            return False, errors

        if "txn" in data:
            txn = data["txn"]
            required_txn_fields = ["type", "snd", "fee"]
            for field in required_txn_fields:
                if field not in txn:
                    errors.append(f"Missing transaction field: {field}")

        return len(errors) == 0, errors


class DataPipelineTestFramework:
    """Comprehensive data pipeline testing framework"""

    def __init__(self, config: PipelineTestConfig = None, service_config: ServiceConfig = None):
        self.config = config or PipelineTestConfig()
        self.service_config = service_config or ServiceConfig()
        self.mcp_client = None
        self.validator = DataValidator()
        self.performance_metrics: List[PerformanceMetrics] = []
        self.test_results: List[TestResult] = []

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Load test fixtures
        self.fixtures = self._create_test_fixtures()

    def _create_test_fixtures(self) -> List[DataFixture]:
        """Create test data fixtures"""
        return [
            DataFixture(
                name="valid_account",
                data_type="account",
                description="Valid Algorand account with assets",
                data={
                    "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                    "expected_fields": ["address", "amount", "amount-without-pending-rewards"]
                }
            ),
            DataFixture(
                name="usdc_asset",
                data_type="asset",
                description="USDC asset information",
                data={
                    "asset_id": 31566704,
                    "expected_fields": ["index", "params"]
                }
            ),
            DataFixture(
                name="algo_price",
                data_type="market_data",
                description="ALGO price data",
                data={
                    "symbol": "ALGO",
                    "expected_fields": ["symbol", "price", "timestamp"]
                }
            ),
            DataFixture(
                name="usdc_price",
                data_type="market_data",
                description="USDC price data",
                data={
                    "symbol": "USDC",
                    "expected_fields": ["symbol", "price", "timestamp"]
                }
            ),
            DataFixture(
                name="high_value_account",
                data_type="account",
                description="Account with significant assets",
                data={
                    "address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                    "expected_fields": ["address", "amount", "assets"]
                }
            )
        ]

    async def initialize(self):
        """Initialize the test framework"""
        self.mcp_client = MCPServiceClient(self.service_config)

    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client and self.mcp_client.session:
            await self.mcp_client.session.close()

    async def test_reader_mcp_data_quality(self) -> Dict[str, Any]:
        """Test Reader MCP data quality and consistency"""
        results = {
            "account_tests": [],
            "asset_tests": [],
            "data_consistency": {},
            "performance_metrics": []
        }

        async with self.mcp_client:
            # Test account data quality
            for fixture in self.fixtures:
                if fixture.data_type == "account":
                    try:
                        start_time = time.time()
                        success, data, duration = await self.mcp_client.get_account_info(
                            fixture.data["address"]
                        )

                        if success:
                            is_valid, errors = self.validator.validate_account_data(data)

                            # Check if expected fields are present
                            expected_fields = fixture.data.get("expected_fields", [])
                            field_coverage = sum(1 for field in expected_fields if field in data)
                            coverage_ratio = field_coverage / len(expected_fields) if expected_fields else 1.0

                            results["account_tests"].append({
                                "fixture": fixture.name,
                                "success": success,
                                "valid": is_valid,
                                "errors": errors,
                                "duration": duration,
                                "field_coverage": coverage_ratio,
                                "data_size": len(str(data))
                            })
                        else:
                            results["account_tests"].append({
                                "fixture": fixture.name,
                                "success": False,
                                "error": data.get("error", "Unknown error"),
                                "duration": duration
                            })

                        # Record performance metric
                        self.performance_metrics.append(PerformanceMetrics(
                            operation="get_account_info",
                            duration=duration,
                            success=success,
                            timestamp=datetime.now(),
                            service="reader_mcp",
                            data_size=len(str(data)) if success else 0
                        ))

                    except Exception as e:
                        results["account_tests"].append({
                            "fixture": fixture.name,
                            "success": False,
                            "error": str(e),
                            "duration": 0
                        })

            # Test asset data quality
            for fixture in self.fixtures:
                if fixture.data_type == "asset":
                    try:
                        start_time = time.time()
                        success, data, duration = await self.mcp_client.get_asset_info(
                            fixture.data["asset_id"]
                        )

                        if success:
                            is_valid, errors = self.validator.validate_asset_data(data)

                            results["asset_tests"].append({
                                "fixture": fixture.name,
                                "asset_id": fixture.data["asset_id"],
                                "success": success,
                                "valid": is_valid,
                                "errors": errors,
                                "duration": duration,
                                "data_size": len(str(data))
                            })
                        else:
                            results["asset_tests"].append({
                                "fixture": fixture.name,
                                "asset_id": fixture.data["asset_id"],
                                "success": False,
                                "error": data.get("error", "Unknown error"),
                                "duration": duration
                            })

                        # Record performance metric
                        self.performance_metrics.append(PerformanceMetrics(
                            operation="get_asset_info",
                            duration=duration,
                            success=success,
                            timestamp=datetime.now(),
                            service="reader_mcp",
                            data_size=len(str(data)) if success else 0
                        ))

                    except Exception as e:
                        results["asset_tests"].append({
                            "fixture": fixture.name,
                            "asset_id": fixture.data["asset_id"],
                            "success": False,
                            "error": str(e),
                            "duration": 0
                        })

            # Data consistency checks
            if self.config.data_consistency_checks:
                results["data_consistency"] = await self._test_data_consistency()

        return results

    async def test_market_data_mcp_quality(self) -> Dict[str, Any]:
        """Test Market Data MCP data quality and real-time accuracy"""
        results = {
            "price_tests": [],
            "real_time_accuracy": {},
            "performance_metrics": []
        }

        async with self.mcp_client:
            # Test price data quality
            for fixture in self.fixtures:
                if fixture.data_type == "market_data":
                    try:
                        start_time = time.time()
                        success, data, duration = await self.mcp_client.get_market_data(
                            fixture.data["symbol"]
                        )

                        if success:
                            is_valid, errors = self.validator.validate_market_data(data)

                            # Check price reasonableness
                            price_reasonable = True
                            if "price" in data:
                                price = float(data["price"])
                                symbol = fixture.data["symbol"]

                                # Basic price sanity checks
                                if symbol == "ALGO" and (price < 0.01 or price > 100):
                                    price_reasonable = False
                                elif symbol == "USDC" and (price < 0.95 or price > 1.05):
                                    price_reasonable = False

                            # Check timestamp freshness
                            timestamp_fresh = True
                            if "timestamp" in data:
                                try:
                                    ts = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                                    age = (datetime.now(ts.tzinfo) - ts).total_seconds()
                                    if age > 300:  # More than 5 minutes old
                                        timestamp_fresh = False
                                except:
                                    timestamp_fresh = False

                            results["price_tests"].append({
                                "fixture": fixture.name,
                                "symbol": fixture.data["symbol"],
                                "success": success,
                                "valid": is_valid,
                                "errors": errors,
                                "duration": duration,
                                "price_reasonable": price_reasonable,
                                "timestamp_fresh": timestamp_fresh,
                                "price": data.get("price"),
                                "timestamp": data.get("timestamp")
                            })
                        else:
                            results["price_tests"].append({
                                "fixture": fixture.name,
                                "symbol": fixture.data["symbol"],
                                "success": False,
                                "error": data.get("error", "Unknown error"),
                                "duration": duration
                            })

                        # Record performance metric
                        self.performance_metrics.append(PerformanceMetrics(
                            operation="get_market_data",
                            duration=duration,
                            success=success,
                            timestamp=datetime.now(),
                            service="market_data_mcp"
                        ))

                    except Exception as e:
                        results["price_tests"].append({
                            "fixture": fixture.name,
                            "symbol": fixture.data["symbol"],
                            "success": False,
                            "error": str(e),
                            "duration": 0
                        })

            # Test real-time accuracy with multiple requests
            if self.config.performance_mode:
                results["real_time_accuracy"] = await self._test_real_time_accuracy()

        return results

    async def test_writer_mcp_functionality(self) -> Dict[str, Any]:
        """Test Writer MCP transaction capabilities (mock mode)"""
        results = {
            "transaction_validation": [],
            "error_handling": [],
            "performance_metrics": []
        }

        async with self.mcp_client:
            # Test transaction validation with mock data
            mock_transactions = [
                {
                    "name": "valid_payment",
                    "data": {
                        "type": "pay",
                        "sender": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                        "receiver": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                        "amount": 1000000,
                        "fee": 1000
                    },
                    "should_validate": True
                },
                {
                    "name": "invalid_sender",
                    "data": {
                        "type": "pay",
                        "sender": "INVALID",
                        "receiver": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                        "amount": 1000000,
                        "fee": 1000
                    },
                    "should_validate": False
                },
                {
                    "name": "zero_amount",
                    "data": {
                        "type": "pay",
                        "sender": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                        "receiver": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                        "amount": 0,
                        "fee": 1000
                    },
                    "should_validate": False
                }
            ]

            for mock_txn in mock_transactions:
                try:
                    start_time = time.time()

                    # Note: In a real test, we would send to a testnet or use dry-run mode
                    # For safety, we'll just validate the transaction structure
                    is_valid, errors = self.validator.validate_transaction_data({"txn": mock_txn["data"]})
                    duration = time.time() - start_time

                    results["transaction_validation"].append({
                        "transaction": mock_txn["name"],
                        "expected_valid": mock_txn["should_validate"],
                        "actual_valid": is_valid,
                        "errors": errors,
                        "duration": duration,
                        "test_passed": is_valid == mock_txn["should_validate"]
                    })

                    # Record performance metric
                    self.performance_metrics.append(PerformanceMetrics(
                        operation="validate_transaction",
                        duration=duration,
                        success=True,
                        timestamp=datetime.now(),
                        service="writer_mcp"
                    ))

                except Exception as e:
                    results["transaction_validation"].append({
                        "transaction": mock_txn["name"],
                        "error": str(e),
                        "test_passed": False
                    })

        return results

    async def test_cross_service_data_correlation(self) -> Dict[str, Any]:
        """Test data correlation between all MCP services"""
        results = {
            "correlation_tests": [],
            "data_consistency": {},
            "integration_health": {}
        }

        async with self.mcp_client:
            # Test correlation between account data and market prices
            test_address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"

            try:
                # Get account data
                account_success, account_data, account_duration = await self.mcp_client.get_account_info(test_address)

                # Get ALGO price
                algo_success, algo_price_data, algo_duration = await self.mcp_client.get_market_data("ALGO")

                # Get USDC asset info and price
                usdc_success, usdc_asset_data, usdc_asset_duration = await self.mcp_client.get_asset_info(31566704)
                usdc_price_success, usdc_price_data, usdc_price_duration = await self.mcp_client.get_market_data("USDC")

                if all([account_success, algo_success, usdc_success, usdc_price_success]):
                    # Calculate portfolio value if possible
                    portfolio_value = 0

                    # ALGO balance
                    if "amount" in account_data and "price" in algo_price_data:
                        algo_balance = account_data["amount"] / 1_000_000  # Convert microalgos
                        algo_price = float(algo_price_data["price"])
                        portfolio_value += algo_balance * algo_price

                    # Asset balances
                    asset_values = []
                    if "assets" in account_data:
                        for asset in account_data["assets"]:
                            if asset.get("asset-id") == 31566704:  # USDC
                                if "amount" in asset and "price" in usdc_price_data:
                                    usdc_balance = asset["amount"] / 1_000_000  # Assuming 6 decimals
                                    usdc_price = float(usdc_price_data["price"])
                                    usdc_value = usdc_balance * usdc_price
                                    portfolio_value += usdc_value
                                    asset_values.append({"asset": "USDC", "value": usdc_value})

                    results["correlation_tests"].append({
                        "test": "portfolio_valuation",
                        "success": True,
                        "portfolio_value": portfolio_value,
                        "asset_breakdown": asset_values,
                        "data_sources_used": 4,
                        "total_duration": account_duration + algo_duration + usdc_asset_duration + usdc_price_duration
                    })

                    # Data freshness correlation
                    timestamps = []
                    if "timestamp" in algo_price_data:
                        timestamps.append(algo_price_data["timestamp"])
                    if "timestamp" in usdc_price_data:
                        timestamps.append(usdc_price_data["timestamp"])

                    timestamp_consistency = len(set(timestamps)) <= 1  # All timestamps should be similar

                    results["data_consistency"] = {
                        "timestamp_consistency": timestamp_consistency,
                        "price_data_aligned": len(timestamps) > 0,
                        "account_data_complete": "assets" in account_data
                    }

                else:
                    results["correlation_tests"].append({
                        "test": "portfolio_valuation",
                        "success": False,
                        "errors": {
                            "account_success": account_success,
                            "algo_price_success": algo_success,
                            "usdc_asset_success": usdc_success,
                            "usdc_price_success": usdc_price_success
                        }
                    })

            except Exception as e:
                results["correlation_tests"].append({
                    "test": "portfolio_valuation",
                    "success": False,
                    "error": str(e)
                })

            # Integration health assessment
            service_health = await self.mcp_client.check_all_services_health()
            results["integration_health"] = {
                "all_services_operational": all(status == ServiceHealth.HEALTHY for status in service_health.values()),
                "service_status": {name: status.value for name, status in service_health.items()},
                "degraded_services": [name for name, status in service_health.items() if status != ServiceHealth.HEALTHY]
            }

        return results

    async def test_performance_under_load(self) -> Dict[str, Any]:
        """Test pipeline performance under concurrent load"""
        results = {
            "concurrent_tests": [],
            "throughput_metrics": {},
            "bottlenecks": []
        }

        if not self.config.performance_mode:
            return {"skipped": "Performance mode not enabled"}

        async with self.mcp_client:
            # Concurrent account requests
            account_addresses = [
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
            ] * self.config.concurrent_requests

            start_time = time.time()
            tasks = [
                self.mcp_client.get_account_info(addr)
                for addr in account_addresses
            ]

            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            total_duration = time.time() - start_time

            successful_requests = sum(1 for r in results_list if not isinstance(r, Exception) and r[0])
            total_requests = len(tasks)

            results["concurrent_tests"].append({
                "test": "concurrent_account_requests",
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": successful_requests / total_requests,
                "total_duration": total_duration,
                "requests_per_second": total_requests / total_duration,
                "average_response_time": total_duration / total_requests
            })

            # Throughput analysis
            durations = [r[2] for r in results_list if not isinstance(r, Exception)]
            if durations:
                results["throughput_metrics"] = {
                    "average_response_time": statistics.mean(durations),
                    "median_response_time": statistics.median(durations),
                    "max_response_time": max(durations),
                    "min_response_time": min(durations),
                    "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0
                }

                # Identify bottlenecks
                slow_threshold = statistics.mean(durations) + statistics.stdev(durations) if len(durations) > 1 else 5.0
                slow_requests = [d for d in durations if d > slow_threshold]

                if slow_requests:
                    results["bottlenecks"].append({
                        "type": "slow_responses",
                        "count": len(slow_requests),
                        "threshold": slow_threshold,
                        "average_slow_time": statistics.mean(slow_requests)
                    })

        return results

    async def _test_data_consistency(self) -> Dict[str, Any]:
        """Test data consistency across services"""
        consistency_results = {}

        # Test asset data consistency between Reader and Market Data
        try:
            asset_success, asset_data, _ = await self.mcp_client.get_asset_info(31566704)  # USDC
            price_success, price_data, _ = await self.mcp_client.get_market_data("USDC")

            if asset_success and price_success:
                # Check if asset name matches expected symbol
                asset_name = asset_data.get("params", {}).get("name", "").upper()
                price_symbol = price_data.get("symbol", "").upper()

                consistency_results["asset_symbol_consistency"] = {
                    "consistent": "USDC" in asset_name and price_symbol == "USDC",
                    "asset_name": asset_name,
                    "price_symbol": price_symbol
                }

        except Exception as e:
            consistency_results["asset_symbol_consistency"] = {"error": str(e)}

        return consistency_results

    async def _test_real_time_accuracy(self) -> Dict[str, Any]:
        """Test real-time accuracy of market data"""
        accuracy_results = {}

        try:
            # Get ALGO price multiple times with small intervals
            prices = []
            timestamps = []

            for i in range(3):
                success, data, duration = await self.mcp_client.get_market_data("ALGO")
                if success:
                    prices.append(float(data.get("price", 0)))
                    timestamps.append(data.get("timestamp", ""))

                if i < 2:  # Don't wait after the last request
                    await asyncio.sleep(1)

            if len(prices) >= 2:
                price_variance = max(prices) - min(prices)
                relative_variance = price_variance / statistics.mean(prices) if statistics.mean(prices) > 0 else 0

                accuracy_results["price_stability"] = {
                    "price_variance": price_variance,
                    "relative_variance": relative_variance,
                    "stable": relative_variance < 0.01,  # Less than 1% variance
                    "samples": len(prices)
                }

                # Check timestamp progression
                timestamp_progression = all(
                    timestamps[i] <= timestamps[i+1]
                    for i in range(len(timestamps)-1)
                    if timestamps[i] and timestamps[i+1]
                )

                accuracy_results["timestamp_progression"] = {
                    "progressive": timestamp_progression,
                    "timestamps": timestamps
                }

        except Exception as e:
            accuracy_results["error"] = str(e)

        return accuracy_results

    async def run_comprehensive_pipeline_tests(self) -> Dict[str, Any]:
        """Run complete data pipeline test suite"""
        await self.initialize()

        try:
            self.logger.info("Starting comprehensive data pipeline tests")

            # Run all test categories
            test_results = {}

            # Reader MCP tests
            self.logger.info("Testing Reader MCP data quality...")
            test_results["reader_mcp"] = await self.test_reader_mcp_data_quality()

            # Market Data MCP tests
            self.logger.info("Testing Market Data MCP quality...")
            test_results["market_data_mcp"] = await self.test_market_data_mcp_quality()

            # Writer MCP tests
            self.logger.info("Testing Writer MCP functionality...")
            test_results["writer_mcp"] = await self.test_writer_mcp_functionality()

            # Cross-service correlation tests
            self.logger.info("Testing cross-service data correlation...")
            test_results["cross_service"] = await self.test_cross_service_data_correlation()

            # Performance tests
            if self.config.performance_mode:
                self.logger.info("Testing performance under load...")
                test_results["performance"] = await self.test_performance_under_load()

            # Calculate overall metrics
            total_operations = len(self.performance_metrics)
            successful_operations = sum(1 for m in self.performance_metrics if m.success)

            test_results["summary"] = {
                "total_test_categories": len(test_results) - 1,  # Exclude summary
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
                "average_operation_duration": statistics.mean([m.duration for m in self.performance_metrics]) if self.performance_metrics else 0,
                "test_completion_time": datetime.now().isoformat()
            }

            return test_results

        finally:
            await self.cleanup()

    def print_pipeline_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive pipeline test summary"""
        print("\n" + "="*80)
        print("DATA PIPELINE TEST FRAMEWORK - RESULTS SUMMARY")
        print("="*80)

        summary = results.get("summary", {})
        print(f"\nOverall Results:")
        print(f"  Test Categories: {summary.get('total_test_categories', 0)}")
        print(f"  Total Operations: {summary.get('total_operations', 0)}")
        print(f"  Success Rate: {summary.get('success_rate', 0)*100:.1f}%")
        print(f"  Average Duration: {summary.get('average_operation_duration', 0):.3f}s")

        # Reader MCP Results
        if "reader_mcp" in results:
            reader = results["reader_mcp"]
            print(f"\nReader MCP:")
            print(f"  Account Tests: {len(reader.get('account_tests', []))}")
            print(f"  Asset Tests: {len(reader.get('asset_tests', []))}")

            account_success = sum(1 for t in reader.get('account_tests', []) if t.get('success'))
            asset_success = sum(1 for t in reader.get('asset_tests', []) if t.get('success'))
            print(f"  Account Success Rate: {account_success}/{len(reader.get('account_tests', []))}")
            print(f"  Asset Success Rate: {asset_success}/{len(reader.get('asset_tests', []))}")

        # Market Data MCP Results
        if "market_data_mcp" in results:
            market = results["market_data_mcp"]
            print(f"\nMarket Data MCP:")
            print(f"  Price Tests: {len(market.get('price_tests', []))}")

            price_success = sum(1 for t in market.get('price_tests', []) if t.get('success'))
            print(f"  Price Success Rate: {price_success}/{len(market.get('price_tests', []))}")

            reasonable_prices = sum(1 for t in market.get('price_tests', []) if t.get('price_reasonable'))
            fresh_timestamps = sum(1 for t in market.get('price_tests', []) if t.get('timestamp_fresh'))
            print(f"  Price Reasonableness: {reasonable_prices}/{len(market.get('price_tests', []))}")
            print(f"  Timestamp Freshness: {fresh_timestamps}/{len(market.get('price_tests', []))}")

        # Cross-service Results
        if "cross_service" in results:
            cross = results["cross_service"]
            print(f"\nCross-Service Integration:")
            correlation_success = sum(1 for t in cross.get('correlation_tests', []) if t.get('success'))
            print(f"  Correlation Tests: {correlation_success}/{len(cross.get('correlation_tests', []))}")

            if "integration_health" in cross:
                health = cross["integration_health"]
                print(f"  All Services Operational: {health.get('all_services_operational', False)}")
                degraded = len(health.get('degraded_services', []))
                if degraded > 0:
                    print(f"  Degraded Services: {degraded}")

        # Performance Results
        if "performance" in results:
            perf = results["performance"]
            if "concurrent_tests" in perf:
                for test in perf["concurrent_tests"]:
                    print(f"\nPerformance ({test['test']}):")
                    print(f"  Requests/Second: {test.get('requests_per_second', 0):.2f}")
                    print(f"  Success Rate: {test.get('success_rate', 0)*100:.1f}%")
                    print(f"  Avg Response Time: {test.get('average_response_time', 0):.3f}s")

        print("\n" + "="*80)


async def main():
    """Main execution function for data pipeline tests"""
    print("Starting Data Pipeline Test Framework")

    # Configuration
    pipeline_config = PipelineTestConfig(
        use_real_data=True,
        performance_mode=True,
        concurrent_requests=5,
        data_consistency_checks=True
    )

    service_config = ServiceConfig(
        reader_url="http://localhost:8002",
        writer_url="http://localhost:3001",
        market_data_url="http://localhost:8789"
    )

    framework = DataPipelineTestFramework(pipeline_config, service_config)

    try:
        # Run comprehensive tests
        results = await framework.run_comprehensive_pipeline_tests()

        # Print summary
        framework.print_pipeline_test_summary(results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/home/mpo/algorand-showcase/tests/mcp_integration/pipeline_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nDetailed results saved to: {output_file}")

        # Return success if summary indicates good results
        summary = results.get("summary", {})
        return summary.get("success_rate", 0) > 0.8

    except Exception as e:
        print(f"Pipeline test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)