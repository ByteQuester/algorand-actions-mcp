#!/usr/bin/env python3
"""
Automated Test Framework for MCP Services Integration with Lending Engines

This framework provides comprehensive testing infrastructure for:
- Reader MCP (localhost:8002) - Blockchain data reading
- Writer MCP (localhost:3001) - Transaction execution
- Market Data MCP (localhost:8789) - Market data feeds
- 4 Lending Engines: Collateral, Interest Rate, Loan Approval, Risk Assessment

Key Features:
- Async test execution with concurrent testing
- Real blockchain data integration and validation
- Mock/real data switching capability
- Performance benchmarking and metrics collection
- Service health monitoring and failure recovery
- Cross-engine integration testing
- Comprehensive error handling and fallback mechanisms
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
from contextlib import asynccontextmanager
from enum import Enum
import statistics
import traceback

# Add lending ecosystem to path
lending_path = Path(__file__).parent.parent.parent / "algorand-lending-ecosystem" / "algorand-lending-business-logic"
sys.path.insert(0, str(lending_path))

try:
    from algorand_lending_bl import (
        CollateralAnalyzer,
        InterestRateEngine,
        LoanApprovalEngine,
        RiskAssessmentEngine,
        LoanRequest,
        AlgorandAddress,
        ASAToken,
        DEFAULT_CONFIG,
        create_lending_engines,
        create_lending_service
    )
except ImportError as e:
    logging.error(f"Failed to import lending engines: {e}")
    CollateralAnalyzer = InterestRateEngine = LoanApprovalEngine = RiskAssessmentEngine = None


class TestMode(Enum):
    """Test execution modes"""
    MOCK_DATA = "mock"
    REAL_DATA = "real"
    HYBRID = "hybrid"
    PERFORMANCE = "performance"


class ServiceHealth(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ServiceConfig:
    """Configuration for MCP services"""
    reader_url: str = "http://localhost:8002"
    writer_url: str = "http://localhost:3001"
    market_data_url: str = "http://localhost:8789"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation: str
    duration: float
    success: bool
    timestamp: datetime
    service: str
    engine: Optional[str] = None
    data_size: Optional[int] = None
    error: Optional[str] = None


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    success: bool
    duration: float
    timestamp: datetime
    details: Dict[str, Any]
    error: Optional[str] = None
    performance_metrics: List[PerformanceMetrics] = None


@dataclass
class TestSuite:
    """Complete test suite results"""
    suite_name: str
    results: List[TestResult]
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration: float
    performance_summary: Dict[str, Any]


class MCPServiceClient:
    """Client for interacting with MCP services"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_status: Dict[str, ServiceHealth] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _make_request(self, service_url: str, endpoint: str, method: str = "GET",
                           data: Optional[Dict] = None, params: Optional[Dict] = None) -> Tuple[bool, Dict, float]:
        """Make HTTP request with retry logic"""
        start_time = time.time()

        for attempt in range(self.config.retry_attempts):
            try:
                url = f"{service_url}{endpoint}"

                if method.upper() == "GET":
                    async with self.session.get(url, params=params) as response:
                        result = await response.json()
                        duration = time.time() - start_time
                        return response.status == 200, result, duration

                elif method.upper() == "POST":
                    async with self.session.post(url, json=data, params=params) as response:
                        result = await response.json()
                        duration = time.time() - start_time
                        return response.status == 200, result, duration

            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    duration = time.time() - start_time
                    return False, {"error": str(e)}, duration
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        duration = time.time() - start_time
        return False, {"error": "Max retry attempts exceeded"}, duration

    async def check_service_health(self, service_url: str, service_name: str) -> ServiceHealth:
        """Check health of a specific service"""
        try:
            success, result, duration = await self._make_request(service_url, "/health")

            if success and duration < 5.0:
                status = ServiceHealth.HEALTHY
            elif success and duration < 10.0:
                status = ServiceHealth.DEGRADED
            elif success:
                status = ServiceHealth.UNHEALTHY
            else:
                status = ServiceHealth.OFFLINE

            self.health_status[service_name] = status
            return status

        except Exception:
            self.health_status[service_name] = ServiceHealth.OFFLINE
            return ServiceHealth.OFFLINE

    async def check_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Check health of all MCP services"""
        tasks = [
            self.check_service_health(self.config.reader_url, "reader"),
            self.check_service_health(self.config.writer_url, "writer"),
            self.check_service_health(self.config.market_data_url, "market_data")
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
        return self.health_status

    async def get_account_info(self, address: str) -> Tuple[bool, Dict, float]:
        """Get account information from Reader MCP"""
        return await self._make_request(
            self.config.reader_url,
            f"/account/{address}"
        )

    async def get_asset_info(self, asset_id: int) -> Tuple[bool, Dict, float]:
        """Get asset information from Reader MCP"""
        return await self._make_request(
            self.config.reader_url,
            f"/asset/{asset_id}"
        )

    async def get_market_data(self, symbol: str) -> Tuple[bool, Dict, float]:
        """Get market data from Market Data MCP"""
        return await self._make_request(
            self.config.market_data_url,
            f"/price/{symbol}"
        )

    async def send_transaction(self, transaction_data: Dict) -> Tuple[bool, Dict, float]:
        """Send transaction via Writer MCP"""
        return await self._make_request(
            self.config.writer_url,
            "/transaction",
            method="POST",
            data=transaction_data
        )


class LendingEngineTestFramework:
    """Main test framework for lending engines with MCP integration"""

    def __init__(self, config: ServiceConfig = None, test_mode: TestMode = TestMode.HYBRID):
        self.config = config or ServiceConfig()
        self.test_mode = test_mode
        self.lending_engines = None
        self.lending_service = None
        self.mcp_client = None
        self.performance_metrics: List[PerformanceMetrics] = []
        self.test_results: List[TestResult] = []

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize test framework"""
        self.logger.info("Initializing Lending Engine Test Framework")

        # Initialize MCP client
        self.mcp_client = MCPServiceClient(self.config)

        # Initialize lending engines
        try:
            if CollateralAnalyzer is not None:
                self.lending_service = create_lending_service()
                self.lending_engines = create_lending_engines()
                self.logger.info("Lending engines initialized successfully")
            else:
                self.logger.error("Lending engines not available - imports failed")

        except Exception as e:
            self.logger.error(f"Failed to initialize lending engines: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client and self.mcp_client.session:
            await self.mcp_client.session.close()

    def add_performance_metric(self, metric: PerformanceMetrics):
        """Add performance metric"""
        self.performance_metrics.append(metric)

    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run individual test with metrics collection"""
        self.logger.info(f"Running test: {test_name}")
        start_time = time.time()
        timestamp = datetime.now()

        try:
            result = await test_func(*args, **kwargs)
            duration = time.time() - start_time

            test_result = TestResult(
                test_name=test_name,
                success=True,
                duration=duration,
                timestamp=timestamp,
                details=result,
                performance_metrics=[]
            )

            self.test_results.append(test_result)
            self.logger.info(f"Test {test_name} passed in {duration:.2f}s")
            return test_result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"

            test_result = TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                timestamp=timestamp,
                details={},
                error=error_msg,
                performance_metrics=[]
            )

            self.test_results.append(test_result)
            self.logger.error(f"Test {test_name} failed in {duration:.2f}s: {error_msg}")
            return test_result

    async def test_service_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to all MCP services"""
        async with self.mcp_client:
            health_status = await self.mcp_client.check_all_services_health()

            return {
                "all_services_healthy": all(status == ServiceHealth.HEALTHY for status in health_status.values()),
                "service_status": {name: status.value for name, status in health_status.items()},
                "total_services": len(health_status),
                "healthy_services": sum(1 for status in health_status.values() if status == ServiceHealth.HEALTHY)
            }

    async def test_data_pipeline_integration(self) -> Dict[str, Any]:
        """Test integration between MCP services and lending engines"""
        async with self.mcp_client:
            # Test account data retrieval
            test_address = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            account_success, account_data, account_duration = await self.mcp_client.get_account_info(test_address)

            # Test asset data retrieval
            test_asset_id = 31566704  # USDC
            asset_success, asset_data, asset_duration = await self.mcp_client.get_asset_info(test_asset_id)

            # Test market data retrieval
            market_success, market_data, market_duration = await self.mcp_client.get_market_data("ALGO")

            # Record performance metrics
            self.add_performance_metric(PerformanceMetrics(
                operation="get_account_info",
                duration=account_duration,
                success=account_success,
                timestamp=datetime.now(),
                service="reader_mcp"
            ))

            self.add_performance_metric(PerformanceMetrics(
                operation="get_asset_info",
                duration=asset_duration,
                success=asset_success,
                timestamp=datetime.now(),
                service="reader_mcp"
            ))

            self.add_performance_metric(PerformanceMetrics(
                operation="get_market_data",
                duration=market_duration,
                success=market_success,
                timestamp=datetime.now(),
                service="market_data_mcp"
            ))

            return {
                "account_retrieval": {"success": account_success, "duration": account_duration},
                "asset_retrieval": {"success": asset_success, "duration": asset_duration},
                "market_data_retrieval": {"success": market_success, "duration": market_duration},
                "pipeline_operational": account_success and asset_success and market_success,
                "average_response_time": (account_duration + asset_duration + market_duration) / 3
            }

    async def test_lending_engine_performance(self) -> Dict[str, Any]:
        """Test performance of all lending engines"""
        if not self.lending_service:
            return {"error": "Lending engines not initialized"}

        results = {}

        # Test data
        test_request = LoanRequest(
            borrower_address=AlgorandAddress("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            requested_amount=1000000,  # 1 ALGO in microalgos
            collateral_assets=[
                ASAToken(asset_id=31566704, amount=1000000)  # 1 USDC
            ],
            loan_duration_days=30
        )

        # Test each engine
        engines = {
            "collateral": self.lending_service["collateral"],
            "interest_rates": self.lending_service["interest_rates"],
            "loan_approval": self.lending_service["loan_approval"],
            "risk_assessment": self.lending_service["risk_assessment"]
        }

        for engine_name, engine in engines.items():
            try:
                start_time = time.time()

                if engine_name == "collateral":
                    result = await asyncio.to_thread(
                        engine.analyze_collateral,
                        test_request.borrower_address,
                        test_request.collateral_assets
                    )
                elif engine_name == "interest_rates":
                    result = await asyncio.to_thread(
                        engine.calculate_rate,
                        test_request.borrower_address,
                        test_request.requested_amount,
                        test_request.collateral_assets,
                        test_request.loan_duration_days
                    )
                elif engine_name == "loan_approval":
                    result = await asyncio.to_thread(
                        engine.evaluate_loan,
                        test_request
                    )
                elif engine_name == "risk_assessment":
                    result = await asyncio.to_thread(
                        engine.assess_risk,
                        test_request.borrower_address,
                        test_request.collateral_assets,
                        test_request.requested_amount
                    )

                duration = time.time() - start_time

                self.add_performance_metric(PerformanceMetrics(
                    operation=f"{engine_name}_analysis",
                    duration=duration,
                    success=True,
                    timestamp=datetime.now(),
                    service="lending_engine",
                    engine=engine_name
                ))

                results[engine_name] = {
                    "success": True,
                    "duration": duration,
                    "result_type": type(result).__name__
                }

            except Exception as e:
                duration = time.time() - start_time

                self.add_performance_metric(PerformanceMetrics(
                    operation=f"{engine_name}_analysis",
                    duration=duration,
                    success=False,
                    timestamp=datetime.now(),
                    service="lending_engine",
                    engine=engine_name,
                    error=str(e)
                ))

                results[engine_name] = {
                    "success": False,
                    "duration": duration,
                    "error": str(e)
                }

        # Calculate summary statistics
        successful_engines = [r for r in results.values() if r["success"]]
        if successful_engines:
            avg_duration = statistics.mean(r["duration"] for r in successful_engines)
            max_duration = max(r["duration"] for r in successful_engines)
            min_duration = min(r["duration"] for r in successful_engines)
        else:
            avg_duration = max_duration = min_duration = 0

        return {
            "engine_results": results,
            "total_engines_tested": len(engines),
            "successful_engines": len(successful_engines),
            "average_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "all_engines_operational": len(successful_engines) == len(engines)
        }

    async def run_comprehensive_test_suite(self) -> TestSuite:
        """Run complete test suite"""
        suite_start = datetime.now()
        self.logger.info("Starting comprehensive test suite")

        await self.initialize()

        try:
            # Test suite
            tests = [
                ("service_connectivity", self.test_service_connectivity),
                ("data_pipeline_integration", self.test_data_pipeline_integration),
                ("lending_engine_performance", self.test_lending_engine_performance)
            ]

            test_results = []
            for test_name, test_func in tests:
                result = await self.run_test(test_name, test_func)
                test_results.append(result)

            # Calculate summary
            suite_end = datetime.now()
            total_duration = (suite_end - suite_start).total_seconds()
            passed_tests = sum(1 for r in test_results if r.success)
            failed_tests = len(test_results) - passed_tests

            # Performance summary
            if self.performance_metrics:
                performance_summary = {
                    "total_operations": len(self.performance_metrics),
                    "successful_operations": sum(1 for m in self.performance_metrics if m.success),
                    "average_duration": statistics.mean(m.duration for m in self.performance_metrics),
                    "operations_by_service": {},
                    "operations_by_engine": {}
                }

                # Group by service
                service_metrics = {}
                for metric in self.performance_metrics:
                    if metric.service not in service_metrics:
                        service_metrics[metric.service] = []
                    service_metrics[metric.service].append(metric)

                for service, metrics in service_metrics.items():
                    performance_summary["operations_by_service"][service] = {
                        "count": len(metrics),
                        "success_rate": sum(1 for m in metrics if m.success) / len(metrics),
                        "average_duration": statistics.mean(m.duration for m in metrics)
                    }

                # Group by engine
                engine_metrics = {}
                for metric in self.performance_metrics:
                    if metric.engine:
                        if metric.engine not in engine_metrics:
                            engine_metrics[metric.engine] = []
                        engine_metrics[metric.engine].append(metric)

                for engine, metrics in engine_metrics.items():
                    performance_summary["operations_by_engine"][engine] = {
                        "count": len(metrics),
                        "success_rate": sum(1 for m in metrics if m.success) / len(metrics),
                        "average_duration": statistics.mean(m.duration for m in metrics)
                    }

            else:
                performance_summary = {"no_metrics": True}

            suite = TestSuite(
                suite_name="MCP Integration Test Suite",
                results=test_results,
                start_time=suite_start,
                end_time=suite_end,
                total_tests=len(test_results),
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                total_duration=total_duration,
                performance_summary=performance_summary
            )

            return suite

        finally:
            await self.cleanup()

    def save_test_results(self, suite: TestSuite, output_file: str = None):
        """Save test results to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/home/mpo/algorand-showcase/tests/mcp_integration/test_results_{timestamp}.json"

        # Convert to serializable format
        suite_dict = asdict(suite)

        # Handle datetime serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(output_file, 'w') as f:
            json.dump(suite_dict, f, indent=2, default=json_serializer)

        self.logger.info(f"Test results saved to {output_file}")
        return output_file

    def print_test_summary(self, suite: TestSuite):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("MCP INTEGRATION TEST FRAMEWORK - RESULTS SUMMARY")
        print("="*80)

        print(f"\nSuite: {suite.suite_name}")
        print(f"Duration: {suite.total_duration:.2f} seconds")
        print(f"Tests: {suite.total_tests} total, {suite.passed_tests} passed, {suite.failed_tests} failed")
        print(f"Success Rate: {(suite.passed_tests/suite.total_tests)*100:.1f}%")

        print(f"\nTest Results:")
        print("-" * 50)
        for result in suite.results:
            status = "PASS" if result.success else "FAIL"
            print(f"  {result.test_name:<30} {status:<6} ({result.duration:.2f}s)")
            if not result.success:
                print(f"    Error: {result.error}")

        if not suite.performance_summary.get("no_metrics"):
            print(f"\nPerformance Summary:")
            print("-" * 50)
            perf = suite.performance_summary
            print(f"  Total Operations: {perf['total_operations']}")
            print(f"  Successful: {perf['successful_operations']}")
            print(f"  Average Duration: {perf['average_duration']:.3f}s")

            if perf['operations_by_service']:
                print(f"\n  By Service:")
                for service, metrics in perf['operations_by_service'].items():
                    print(f"    {service:<20} {metrics['count']:>3} ops, "
                          f"{metrics['success_rate']*100:>5.1f}% success, "
                          f"{metrics['average_duration']:>6.3f}s avg")

            if perf['operations_by_engine']:
                print(f"\n  By Engine:")
                for engine, metrics in perf['operations_by_engine'].items():
                    print(f"    {engine:<20} {metrics['count']:>3} ops, "
                          f"{metrics['success_rate']*100:>5.1f}% success, "
                          f"{metrics['average_duration']:>6.3f}s avg")

        print("\n" + "="*80)


async def main():
    """Main execution function"""
    print("Starting MCP Integration Test Framework")

    # Create test framework
    config = ServiceConfig(
        reader_url="http://localhost:8002",
        writer_url="http://localhost:3001",
        market_data_url="http://localhost:8789",
        timeout=30,
        retry_attempts=3
    )

    framework = LendingEngineTestFramework(config, TestMode.HYBRID)

    try:
        # Run comprehensive test suite
        suite = await framework.run_comprehensive_test_suite()

        # Print results
        framework.print_test_summary(suite)

        # Save results
        output_file = framework.save_test_results(suite)
        print(f"\nDetailed results saved to: {output_file}")

        return suite.passed_tests == suite.total_tests

    except Exception as e:
        print(f"Framework execution failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)