"""
Performance Benchmarking Integration Tests

Tests performance characteristics of all engines including response times,
memory usage, concurrent request handling, and throughput under load.
"""

import pytest
import asyncio
import time
import psutil
import gc
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json

from conftest import (
    TestConfig, PerformanceMonitor, create_test_loan_request,
    TestDataGenerator
)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark definition"""
    operation_name: str
    target_response_time: float  # seconds
    target_throughput: float  # operations per second
    max_memory_usage: float  # MB
    max_concurrent_requests: int
    error_rate_threshold: float  # percentage


@dataclass
class PerformanceResult:
    """Performance test result"""
    operation_name: str
    response_time: float
    throughput: float
    memory_usage: float
    error_rate: float
    concurrent_requests_handled: int
    success: bool
    details: Dict[str, Any]


class TestEnginePerformance:
    """Test individual engine performance characteristics"""

    @pytest.fixture
    def performance_benchmarks(self):
        """Define performance benchmarks for each engine operation"""
        return {
            "collateral_analysis": PerformanceBenchmark(
                operation_name="collateral_analysis",
                target_response_time=3.0,
                target_throughput=5.0,
                max_memory_usage=100.0,
                max_concurrent_requests=10,
                error_rate_threshold=5.0
            ),
            "asset_valuation": PerformanceBenchmark(
                operation_name="asset_valuation",
                target_response_time=2.0,
                target_throughput=8.0,
                max_memory_usage=75.0,
                max_concurrent_requests=15,
                error_rate_threshold=3.0
            ),
            "oracle_price_fetch": PerformanceBenchmark(
                operation_name="oracle_price_fetch",
                target_response_time=1.0,
                target_throughput=20.0,
                max_memory_usage=50.0,
                max_concurrent_requests=25,
                error_rate_threshold=2.0
            ),
            "portfolio_analysis": PerformanceBenchmark(
                operation_name="portfolio_analysis",
                target_response_time=4.0,
                target_throughput=4.0,
                max_memory_usage=120.0,
                max_concurrent_requests=8,
                error_rate_threshold=5.0
            ),
            "volatility_calculation": PerformanceBenchmark(
                operation_name="volatility_calculation",
                target_response_time=3.5,
                target_throughput=6.0,
                max_memory_usage=90.0,
                max_concurrent_requests=12,
                error_rate_threshold=4.0
            ),
            "liquidation_analysis": PerformanceBenchmark(
                operation_name="liquidation_analysis",
                target_response_time=5.0,
                target_throughput=3.0,
                max_memory_usage=150.0,
                max_concurrent_requests=6,
                error_rate_threshold=8.0
            )
        }

    @pytest.mark.asyncio
    async def test_collateral_engine_performance(self, all_engines, performance_benchmarks):
        """Test collateral engine performance"""

        engine = all_engines["collateral"]
        benchmark = performance_benchmarks["collateral_analysis"]

        # Test response time
        response_times = []
        memory_usage_samples = []

        for i in range(10):
            monitor = PerformanceMonitor()
            monitor.start()

            initial_memory = monitor.check_memory_usage()

            try:
                result = await engine.assess_collateral_risk({
                    "loan_amount": 50000.0 + i * 5000,
                    "collateral_positions": [
                        {
                            "asset_id": "0",
                            "quantity": 200000.0 + i * 10000,
                            "current_price": 0.25
                        }
                    ]
                })

                monitor.stop()
                response_time = monitor.get_duration()
                final_memory = monitor.check_memory_usage()

                response_times.append(response_time)
                memory_usage_samples.append(final_memory - initial_memory)

                assert result is not None

            except Exception as e:
                pytest.fail(f"Collateral engine performance test failed: {str(e)}")

        # Analyze performance
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        avg_memory_usage = statistics.mean(memory_usage_samples)

        # Verify benchmarks
        assert avg_response_time < benchmark.target_response_time, \
            f"Average response time {avg_response_time:.2f}s exceeds benchmark {benchmark.target_response_time}s"

        assert max_response_time < benchmark.target_response_time * 2, \
            f"Max response time {max_response_time:.2f}s exceeds 2x benchmark"

        assert avg_memory_usage < benchmark.max_memory_usage, \
            f"Average memory usage {avg_memory_usage:.1f}MB exceeds benchmark {benchmark.max_memory_usage}MB"

    @pytest.mark.asyncio
    async def test_valuation_engine_performance(self, all_engines, performance_benchmarks):
        """Test asset valuation engine performance"""

        engine = all_engines["valuation"]
        benchmark = performance_benchmarks["asset_valuation"]

        # Test throughput with batch operations
        num_operations = 20
        start_time = time.time()
        successful_operations = 0

        for i in range(num_operations):
            try:
                result = await engine.value_assets({
                    "asset_ids": ["0", "31566704"],
                    "quantities": [100000.0 + i * 1000, 25000.0 + i * 500]
                })

                if result is not None:
                    successful_operations += 1

            except Exception:
                pass

        end_time = time.time()
        total_time = end_time - start_time
        throughput = successful_operations / total_time

        # Verify throughput benchmark
        assert throughput >= benchmark.target_throughput, \
            f"Throughput {throughput:.2f} ops/s below benchmark {benchmark.target_throughput} ops/s"

        # Verify success rate
        success_rate = (successful_operations / num_operations) * 100
        assert success_rate >= (100 - benchmark.error_rate_threshold), \
            f"Error rate {100 - success_rate:.1f}% exceeds threshold {benchmark.error_rate_threshold}%"

    @pytest.mark.asyncio
    async def test_oracle_engine_performance(self, all_engines, performance_benchmarks):
        """Test oracle engine performance"""

        engine = all_engines["oracle"]
        benchmark = performance_benchmarks["oracle_price_fetch"]

        # Test rapid price fetching
        asset_ids = ["0", "31566704", "312769"]
        response_times = []

        for asset_id in asset_ids * 5:  # 15 total requests
            monitor = PerformanceMonitor()
            monitor.start()

            try:
                result = await engine.get_asset_price(asset_id)
                monitor.stop()

                response_time = monitor.get_duration()
                response_times.append(response_time)

                assert result is not None

            except Exception as e:
                # Oracle failures are acceptable for performance testing
                monitor.stop()
                response_times.append(monitor.get_duration())

        # Analyze response time distribution
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        assert avg_response_time < benchmark.target_response_time, \
            f"Average response time {avg_response_time:.3f}s exceeds benchmark {benchmark.target_response_time}s"

        assert p95_response_time < benchmark.target_response_time * 2, \
            f"95th percentile response time {p95_response_time:.3f}s too high"

    @pytest.mark.asyncio
    async def test_portfolio_engine_performance(self, all_engines, performance_benchmarks):
        """Test portfolio engine performance with complex portfolios"""

        engine = all_engines["portfolio"]
        benchmark = performance_benchmarks["portfolio_analysis"]

        # Test with increasingly complex portfolios
        portfolio_sizes = [3, 5, 10, 15, 20]
        performance_results = []

        for size in portfolio_sizes:
            # Generate complex portfolio
            portfolio_positions = []
            for i in range(size):
                portfolio_positions.append({
                    "asset_id": str(i % 5),  # Cycle through asset IDs
                    "quantity": 10000.0 + i * 1000,
                    "price": 0.25 + (i * 0.01),
                    "weight": 1.0 / size
                })

            monitor = PerformanceMonitor()
            monitor.start()

            try:
                result = await engine.analyze_portfolio({
                    "positions": portfolio_positions,
                    "detailed_analysis": True,
                    "risk_metrics": True
                })

                monitor.stop()
                response_time = monitor.get_duration()

                performance_results.append({
                    "portfolio_size": size,
                    "response_time": response_time,
                    "success": result is not None
                })

            except Exception as e:
                monitor.stop()
                performance_results.append({
                    "portfolio_size": size,
                    "response_time": monitor.get_duration(),
                    "success": False,
                    "error": str(e)
                })

        # Verify performance scales reasonably
        for result in performance_results:
            if result["success"]:
                assert result["response_time"] < benchmark.target_response_time * (result["portfolio_size"] / 5), \
                    f"Portfolio analysis for {result['portfolio_size']} assets took {result['response_time']:.2f}s"

    @pytest.mark.asyncio
    async def test_volatility_engine_performance(self, all_engines, performance_benchmarks):
        """Test volatility engine performance with various time windows"""

        engine = all_engines["volatility"]
        benchmark = performance_benchmarks["volatility_calculation"]

        # Test different volatility calculation complexities
        test_cases = [
            {"asset_ids": ["0"], "time_window": 7, "complexity": "low"},
            {"asset_ids": ["0", "31566704"], "time_window": 30, "complexity": "medium"},
            {"asset_ids": ["0", "31566704", "312769"], "time_window": 90, "complexity": "high"}
        ]

        for test_case in test_cases:
            monitor = PerformanceMonitor()
            monitor.start()

            try:
                result = await engine.calculate_volatility({
                    "asset_ids": test_case["asset_ids"],
                    "time_window": test_case["time_window"],
                    "detailed_metrics": True
                })

                monitor.stop()
                response_time = monitor.get_duration()

                # Verify reasonable response time based on complexity
                complexity_multiplier = {"low": 1.0, "medium": 1.5, "high": 2.0}
                max_time = benchmark.target_response_time * complexity_multiplier[test_case["complexity"]]

                assert response_time < max_time, \
                    f"Volatility calculation ({test_case['complexity']}) took {response_time:.2f}s, " \
                    f"exceeding {max_time:.2f}s"

                assert result is not None

            except Exception as e:
                pytest.fail(f"Volatility engine performance test failed for {test_case}: {str(e)}")

    @pytest.mark.asyncio
    async def test_liquidation_engine_performance(self, all_engines, performance_benchmarks):
        """Test liquidation engine performance with complex scenarios"""

        engine = all_engines["liquidation"]
        benchmark = performance_benchmarks["liquidation_analysis"]

        # Test liquidation scenario complexity
        scenario_complexities = [
            {
                "name": "simple",
                "positions": 1,
                "scenarios": 3,
                "multiplier": 1.0
            },
            {
                "name": "moderate",
                "positions": 3,
                "scenarios": 5,
                "multiplier": 1.5
            },
            {
                "name": "complex",
                "positions": 5,
                "scenarios": 10,
                "multiplier": 2.0
            }
        ]

        for complexity in scenario_complexities:
            # Generate test data
            positions = []
            for i in range(complexity["positions"]):
                positions.append({
                    "asset_id": str(i),
                    "quantity": 100000.0,
                    "current_price": 0.25,
                    "liquidation_priority": i + 1
                })

            monitor = PerformanceMonitor()
            monitor.start()

            try:
                result = await engine.analyze_liquidation_scenarios({
                    "collateral_positions": positions,
                    "num_scenarios": complexity["scenarios"],
                    "detailed_analysis": True
                })

                monitor.stop()
                response_time = monitor.get_duration()

                max_time = benchmark.target_response_time * complexity["multiplier"]
                assert response_time < max_time, \
                    f"Liquidation analysis ({complexity['name']}) took {response_time:.2f}s, " \
                    f"exceeding {max_time:.2f}s"

                assert result is not None

            except Exception as e:
                pytest.fail(f"Liquidation engine performance test failed for {complexity['name']}: {str(e)}")


class TestConcurrentPerformance:
    """Test concurrent request handling performance"""

    @pytest.mark.asyncio
    async def test_concurrent_collateral_analysis(self, all_engines, performance_benchmarks):
        """Test concurrent collateral analysis requests"""

        engine = all_engines["collateral"]
        benchmark = performance_benchmarks["collateral_analysis"]

        # Create concurrent requests
        num_concurrent = benchmark.max_concurrent_requests
        tasks = []

        for i in range(num_concurrent):
            task = engine.assess_collateral_risk({
                "loan_amount": 50000.0 + i * 1000,
                "collateral_positions": [
                    {
                        "asset_id": "0",
                        "quantity": 200000.0 + i * 5000,
                        "current_price": 0.25
                    }
                ]
            })
            tasks.append(task)

        # Execute concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_results) / len(results) * 100
        total_time = end_time - start_time

        # Verify concurrent performance
        assert success_rate >= (100 - benchmark.error_rate_threshold), \
            f"Concurrent success rate {success_rate:.1f}% below threshold"

        assert total_time < benchmark.target_response_time * 2, \
            f"Concurrent execution time {total_time:.2f}s too slow"

        # Verify no resource contention issues
        for failed_result in failed_results:
            error_msg = str(failed_result).lower()
            assert "deadlock" not in error_msg and "timeout" not in error_msg, \
                f"Resource contention detected: {failed_result}"

    @pytest.mark.asyncio
    async def test_mixed_engine_concurrent_load(self, all_engines):
        """Test concurrent load across multiple engines"""

        # Create mixed workload
        tasks = []

        # Collateral analysis tasks
        for i in range(5):
            task = all_engines["collateral"].assess_collateral_risk({
                "loan_amount": 50000.0 + i * 5000,
                "collateral_ratio": 1.5
            })
            tasks.append(("collateral", task))

        # Valuation tasks
        for i in range(8):
            task = all_engines["valuation"].value_assets({
                "asset_ids": ["0", "31566704"],
                "quantities": [100000.0 + i * 1000, 25000.0]
            })
            tasks.append(("valuation", task))

        # Oracle tasks
        for i in range(12):
            task = all_engines["oracle"].get_asset_price(str(i % 3))
            tasks.append(("oracle", task))

        # Portfolio tasks
        for i in range(3):
            task = all_engines["portfolio"].analyze_portfolio({
                "positions": [
                    {"asset_id": "0", "quantity": 100000, "price": 0.25},
                    {"asset_id": "31566704", "quantity": 25000, "price": 1.00}
                ]
            })
            tasks.append(("portfolio", task))

        # Execute all tasks concurrently
        start_time = time.time()
        task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        end_time = time.time()

        # Analyze mixed workload performance
        total_time = end_time - start_time
        successful_tasks = sum(1 for result in task_results if not isinstance(result, Exception))
        success_rate = successful_tasks / len(task_results) * 100

        # Verify mixed workload performance
        assert total_time < 15.0, f"Mixed workload took {total_time:.2f}s, too slow"
        assert success_rate >= 85.0, f"Mixed workload success rate {success_rate:.1f}% too low"

        # Analyze per-engine performance
        engine_results = {}
        for i, (engine_name, _) in enumerate(tasks):
            if engine_name not in engine_results:
                engine_results[engine_name] = {"success": 0, "total": 0}

            engine_results[engine_name]["total"] += 1
            if not isinstance(task_results[i], Exception):
                engine_results[engine_name]["success"] += 1

        # Verify each engine handled concurrent load well
        for engine_name, stats in engine_results.items():
            engine_success_rate = stats["success"] / stats["total"] * 100
            assert engine_success_rate >= 80.0, \
                f"Engine {engine_name} success rate {engine_success_rate:.1f}% too low under concurrent load"

    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, all_engines):
        """Test performance under sustained load"""

        # Run sustained load for 30 seconds
        test_duration = 30.0  # seconds
        start_time = time.time()
        operation_count = 0
        error_count = 0

        while (time.time() - start_time) < test_duration:
            try:
                # Rotate through different engines
                engine_choice = operation_count % 6

                if engine_choice == 0:
                    result = await all_engines["collateral"].quick_risk_assessment({
                        "loan_amount": 50000.0,
                        "collateral_ratio": 1.5
                    })
                elif engine_choice == 1:
                    result = await all_engines["valuation"].quick_valuation({
                        "asset_id": "0",
                        "quantity": 100000.0
                    })
                elif engine_choice == 2:
                    result = await all_engines["oracle"].get_asset_price("0")
                elif engine_choice == 3:
                    result = await all_engines["portfolio"].quick_diversification_check({
                        "assets": ["0", "31566704"]
                    })
                elif engine_choice == 4:
                    result = await all_engines["volatility"].quick_volatility_check({
                        "asset_id": "0"
                    })
                else:
                    result = await all_engines["liquidation"].quick_liquidation_check({
                        "current_ltv": 0.75
                    })

                operation_count += 1

                # Brief pause to simulate realistic load
                await asyncio.sleep(0.1)

            except Exception:
                error_count += 1
                operation_count += 1

        end_time = time.time()
        actual_duration = end_time - start_time

        # Analyze sustained load performance
        operations_per_second = operation_count / actual_duration
        error_rate = (error_count / operation_count) * 100 if operation_count > 0 else 100

        # Verify sustained performance
        assert operations_per_second >= 5.0, \
            f"Sustained load throughput {operations_per_second:.2f} ops/s too low"

        assert error_rate <= 10.0, \
            f"Sustained load error rate {error_rate:.1f}% too high"


class TestMemoryPerformance:
    """Test memory usage and management"""

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, all_engines):
        """Test memory usage under various load conditions"""

        # Get baseline memory usage
        gc.collect()  # Force garbage collection
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Run memory-intensive operations
        memory_samples = []

        for i in range(20):
            # Perform operations that might consume memory
            tasks = [
                all_engines["portfolio"].analyze_portfolio({
                    "positions": [
                        {"asset_id": str(j), "quantity": 100000 + j * 1000, "price": 0.25 + j * 0.01}
                        for j in range(10)  # 10 asset portfolio
                    ],
                    "detailed_analysis": True
                }),
                all_engines["volatility"].calculate_volatility({
                    "asset_ids": ["0", "31566704", "312769"],
                    "time_window": 90,
                    "detailed_metrics": True
                }),
                all_engines["liquidation"].analyze_liquidation_scenarios({
                    "collateral_positions": [
                        {"asset_id": "0", "quantity": 100000, "price": 0.25}
                    ],
                    "num_scenarios": 5,
                    "detailed_analysis": True
                })
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            # Sample memory usage
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)

            # Force garbage collection periodically
            if i % 5 == 0:
                gc.collect()

        # Analyze memory usage
        max_memory = max(memory_samples)
        final_memory = memory_samples[-1]
        memory_increase = max_memory - initial_memory

        # Verify memory usage is reasonable
        assert memory_increase < 500.0, \
            f"Memory increase {memory_increase:.1f}MB too high"

        # Verify no significant memory leaks
        gc.collect()
        post_gc_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_leak = post_gc_memory - initial_memory

        assert memory_leak < 100.0, \
            f"Potential memory leak detected: {memory_leak:.1f}MB increase after GC"

    @pytest.mark.asyncio
    async def test_memory_cleanup_after_errors(self, all_engines):
        """Test memory cleanup after error conditions"""

        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Intentionally cause errors to test cleanup
        error_operations = [
            lambda: all_engines["collateral"].assess_collateral_risk({
                "invalid_parameter": "should_cause_error"
            }),
            lambda: all_engines["valuation"].value_assets({
                "asset_ids": ["invalid_asset_id"],
                "quantities": [-1000]  # Invalid quantity
            }),
            lambda: all_engines["oracle"].get_asset_price("invalid_asset"),
            lambda: all_engines["portfolio"].analyze_portfolio({
                "positions": []  # Empty portfolio might cause issues
            })
        ]

        # Execute error-prone operations
        for i in range(10):
            for operation in error_operations:
                try:
                    await operation()
                except Exception:
                    pass  # Expected errors

        # Force cleanup
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_after_errors = final_memory - initial_memory

        # Verify memory was properly cleaned up after errors
        assert memory_after_errors < 50.0, \
            f"Memory not properly cleaned after errors: {memory_after_errors:.1f}MB increase"


class TestScalabilityPerformance:
    """Test scalability characteristics"""

    @pytest.mark.asyncio
    async def test_scaling_with_portfolio_size(self, all_engines):
        """Test how performance scales with portfolio size"""

        portfolio_sizes = [1, 5, 10, 20, 50]
        performance_results = []

        for size in portfolio_sizes:
            # Generate portfolio of specified size
            positions = []
            for i in range(size):
                positions.append({
                    "asset_id": str(i % 10),  # Cycle through 10 different assets
                    "quantity": 10000.0 + i * 100,
                    "price": 0.25 + (i * 0.001)
                })

            # Measure performance
            start_time = time.time()

            try:
                result = await all_engines["portfolio"].analyze_portfolio({
                    "positions": positions,
                    "detailed_analysis": True
                })

                end_time = time.time()
                response_time = end_time - start_time

                performance_results.append({
                    "size": size,
                    "response_time": response_time,
                    "success": result is not None
                })

            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time

                performance_results.append({
                    "size": size,
                    "response_time": response_time,
                    "success": False,
                    "error": str(e)
                })

        # Analyze scaling characteristics
        successful_results = [r for r in performance_results if r["success"]]

        if len(successful_results) >= 3:
            # Check if scaling is reasonable (should be roughly linear or sub-linear)
            size_1_time = next(r["response_time"] for r in successful_results if r["size"] == 1)
            size_10_time = next((r["response_time"] for r in successful_results if r["size"] == 10), None)

            if size_10_time:
                scaling_factor = size_10_time / size_1_time
                # 10x size should not take more than 20x time (allowing for some overhead)
                assert scaling_factor < 20.0, \
                    f"Poor scaling: 10x portfolio size took {scaling_factor:.1f}x time"

        # Verify all reasonable sizes complete successfully
        for result in performance_results:
            if result["size"] <= 20:  # Reasonable portfolio sizes should work
                assert result["success"], \
                    f"Portfolio size {result['size']} failed: {result.get('error', 'Unknown error')}"

    @pytest.mark.asyncio
    async def test_throughput_scaling(self, all_engines):
        """Test throughput scaling with concurrent requests"""

        concurrency_levels = [1, 2, 5, 10, 15]
        throughput_results = []

        for concurrency in concurrency_levels:
            # Create concurrent tasks
            tasks = []
            for i in range(concurrency):
                task = all_engines["oracle"].get_asset_price(str(i % 3))
                tasks.append(task)

            # Measure throughput
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            total_time = end_time - start_time
            throughput = successful_requests / total_time

            throughput_results.append({
                "concurrency": concurrency,
                "throughput": throughput,
                "success_rate": successful_requests / len(results) * 100
            })

        # Analyze throughput scaling
        single_thread_throughput = throughput_results[0]["throughput"]

        for result in throughput_results[1:]:
            # Throughput should generally increase with concurrency (up to a point)
            if result["concurrency"] <= 10:
                efficiency = result["throughput"] / (single_thread_throughput * result["concurrency"])
                assert efficiency > 0.3, \
                    f"Poor concurrency efficiency at {result['concurrency']} threads: {efficiency:.2%}"

            # Success rate should remain high
            assert result["success_rate"] >= 80.0, \
                f"Success rate {result['success_rate']:.1f}% too low at concurrency {result['concurrency']}"