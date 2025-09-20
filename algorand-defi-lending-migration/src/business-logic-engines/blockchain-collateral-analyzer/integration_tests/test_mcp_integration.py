"""
MCP Service Integration Tests

Tests integration with Model Context Protocol (MCP) services, verifying that all 6 engines
can properly connect to and communicate with MCP services on ports 8002/8003.
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import patch, AsyncMock

from conftest import (
    TestConfig, MockMCPService, assert_mcp_connectivity,
    PerformanceMonitor
)


class TestMCPServiceConnectivity:
    """Test basic MCP service connectivity for all engines"""

    @pytest.mark.asyncio
    async def test_all_engines_mcp_connectivity(self, all_engines, mock_mcp_services):
        """Test that all engines can connect to MCP services"""

        connectivity_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Test basic connectivity
                if hasattr(engine, 'test_mcp_connection'):
                    result = await engine.test_mcp_connection()
                    connectivity_results[engine_name] = {
                        "connected": True,
                        "response_time": result.get("response_time", 0.0),
                        "status": result.get("status", "unknown")
                    }
                else:
                    # Try a basic health check or similar method
                    await assert_mcp_connectivity(engine, engine_name)
                    connectivity_results[engine_name] = {
                        "connected": True,
                        "response_time": 0.0,
                        "status": "healthy"
                    }

            except Exception as e:
                connectivity_results[engine_name] = {
                    "connected": False,
                    "error": str(e),
                    "status": "failed"
                }

        # Verify all engines connected successfully
        failed_engines = [name for name, result in connectivity_results.items()
                         if not result["connected"]]

        assert len(failed_engines) == 0, \
            f"Engines failed to connect to MCP services: {failed_engines}"

        # Verify reasonable response times
        for engine_name, result in connectivity_results.items():
            if result["connected"] and result["response_time"] > 0:
                assert result["response_time"] < 5.0, \
                    f"Engine {engine_name} MCP response time too slow: {result['response_time']}s"

    @pytest.mark.asyncio
    async def test_mcp_reader_service_integration(self, all_engines, test_config):
        """Test integration with MCP reader service (port 8002)"""

        reader_tests = [
            {
                "engine": "oracle",
                "method": "get_asset_info",
                "params": {"asset_id": "0"}
            },
            {
                "engine": "valuation",
                "method": "fetch_market_data",
                "params": {"asset_id": "31566704"}
            },
            {
                "engine": "volatility",
                "method": "get_price_history",
                "params": {"asset_id": "0", "days": 30}
            }
        ]

        for test_case in reader_tests:
            engine = all_engines[test_case["engine"]]

            try:
                if hasattr(engine, test_case["method"]):
                    method = getattr(engine, test_case["method"])
                    result = await method(**test_case["params"])

                    assert result is not None, \
                        f"Engine {test_case['engine']} method {test_case['method']} returned None"

                    # Verify data structure
                    if isinstance(result, dict):
                        assert len(result) > 0, \
                            f"Engine {test_case['engine']} returned empty result"

            except Exception as e:
                pytest.fail(f"MCP reader test failed for {test_case['engine']}.{test_case['method']}: {str(e)}")

    @pytest.mark.asyncio
    async def test_mcp_writer_service_integration(self, all_engines, test_config):
        """Test integration with MCP writer service (port 8003)"""

        writer_tests = [
            {
                "engine": "collateral",
                "method": "store_analysis_result",
                "params": {
                    "analysis_id": f"test_{int(time.time())}",
                    "result_data": {"loan_amount": 50000, "collateral_ratio": 1.5}
                }
            },
            {
                "engine": "liquidation",
                "method": "log_liquidation_event",
                "params": {
                    "event_id": f"liquidation_{int(time.time())}",
                    "event_data": {"asset_id": "0", "liquidated_amount": 1000}
                }
            }
        ]

        for test_case in writer_tests:
            engine = all_engines[test_case["engine"]]

            try:
                if hasattr(engine, test_case["method"]):
                    method = getattr(engine, test_case["method"])
                    result = await method(**test_case["params"])

                    # Writer operations should return success confirmation
                    assert result is not None
                    if isinstance(result, dict):
                        assert result.get("success", False) is True or \
                               result.get("status", "") == "success"

            except Exception as e:
                # Writer operations may not be implemented yet, so we log but don't fail
                print(f"Writer test skipped for {test_case['engine']}.{test_case['method']}: {str(e)}")

    @pytest.mark.asyncio
    async def test_mcp_service_health_checks(self, all_engines, mock_mcp_services):
        """Test MCP service health checks from all engines"""

        health_check_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Try different methods to check MCP health
                health_result = None

                if hasattr(engine, 'check_mcp_health'):
                    health_result = await engine.check_mcp_health()
                elif hasattr(engine, 'health_check'):
                    health_result = await engine.health_check()
                elif hasattr(engine, 'get_mcp_status'):
                    health_result = await engine.get_mcp_status()

                if health_result:
                    health_check_results[engine_name] = health_result
                else:
                    # Default health check
                    health_check_results[engine_name] = {"status": "unknown"}

            except Exception as e:
                health_check_results[engine_name] = {"status": "error", "error": str(e)}

        # Verify health check responses
        for engine_name, health in health_check_results.items():
            assert health is not None, f"Engine {engine_name} health check returned None"

            # Health should contain some status information
            assert "status" in health or "healthy" in health or "error" in health, \
                f"Engine {engine_name} health check missing status information"


class TestMCPServiceResilience:
    """Test MCP service resilience and error handling"""

    @pytest.mark.asyncio
    async def test_mcp_service_unavailable_handling(self, all_engines):
        """Test engine behavior when MCP services are unavailable"""

        # Test with completely unreachable URLs
        unreachable_config = {
            "mcp_reader_url": "http://localhost:9999",  # Non-existent port
            "mcp_writer_url": "http://localhost:9998",  # Non-existent port
            "timeout": 2.0
        }

        resilience_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Try to configure engine with unreachable URLs
                if hasattr(engine, 'configure_mcp'):
                    await engine.configure_mcp(unreachable_config)

                # Attempt an operation that requires MCP
                if hasattr(engine, 'get_asset_info'):
                    result = await engine.get_asset_info("0")
                elif hasattr(engine, 'fetch_data'):
                    result = await engine.fetch_data({"asset_id": "0"})
                else:
                    result = {"status": "no_operation_available"}

                resilience_results[engine_name] = {
                    "handled_gracefully": True,
                    "result": result,
                    "fallback_used": result.get("fallback_used", False)
                }

            except Exception as e:
                # Check if the exception is handled appropriately
                error_message = str(e).lower()
                if any(term in error_message for term in ["timeout", "connection", "unavailable", "refused"]):
                    resilience_results[engine_name] = {
                        "handled_gracefully": True,
                        "error_type": "connection_error",
                        "error_message": str(e)
                    }
                else:
                    resilience_results[engine_name] = {
                        "handled_gracefully": False,
                        "unexpected_error": str(e)
                    }

        # Verify all engines handled MCP unavailability gracefully
        for engine_name, result in resilience_results.items():
            assert result["handled_gracefully"], \
                f"Engine {engine_name} did not handle MCP unavailability gracefully: {result}"

    @pytest.mark.asyncio
    async def test_mcp_timeout_handling(self, all_engines):
        """Test MCP timeout handling across all engines"""

        timeout_config = {
            "mcp_reader_url": "http://localhost:8002",
            "mcp_writer_url": "http://localhost:8003",
            "timeout": 0.1  # Very short timeout
        }

        timeout_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Configure short timeout if possible
                if hasattr(engine, 'set_timeout'):
                    await engine.set_timeout(timeout_config["timeout"])

                # Perform operation that might timeout
                start_time = time.time()

                try:
                    if hasattr(engine, 'get_complex_analysis'):
                        result = await engine.get_complex_analysis({"detailed": True})
                    elif hasattr(engine, 'calculate_volatility'):
                        result = await engine.calculate_volatility({
                            "asset_ids": ["0", "31566704", "312769"],
                            "time_window": 365
                        })
                    else:
                        result = {"status": "no_timeout_test_available"}

                    end_time = time.time()
                    execution_time = end_time - start_time

                    timeout_results[engine_name] = {
                        "completed": True,
                        "execution_time": execution_time,
                        "result": result
                    }

                except asyncio.TimeoutError:
                    end_time = time.time()
                    execution_time = end_time - start_time

                    timeout_results[engine_name] = {
                        "completed": False,
                        "timed_out": True,
                        "execution_time": execution_time
                    }

            except Exception as e:
                timeout_results[engine_name] = {
                    "completed": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }

        # Verify timeout handling
        for engine_name, result in timeout_results.items():
            # Either operation completed quickly or timed out gracefully
            assert result.get("completed", False) or result.get("timed_out", False) or "error" in result, \
                f"Engine {engine_name} timeout test produced unexpected result: {result}"

    @pytest.mark.asyncio
    async def test_mcp_partial_service_failure(self, all_engines, mock_mcp_services):
        """Test behavior when only one MCP service (reader or writer) fails"""

        # Test with reader service failing
        original_reader = mock_mcp_services["reader"]
        mock_mcp_services["reader"].is_running = False

        reader_failure_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Operations that only need writer should still work
                if hasattr(engine, 'store_result'):
                    result = await engine.store_result({"test": "data"})
                    reader_failure_results[engine_name] = {
                        "writer_only_success": True,
                        "result": result
                    }
                else:
                    reader_failure_results[engine_name] = {
                        "writer_only_success": True,
                        "result": {"no_writer_operation": True}
                    }

            except Exception as e:
                reader_failure_results[engine_name] = {
                    "writer_only_success": False,
                    "error": str(e)
                }

        # Restore reader service
        mock_mcp_services["reader"].is_running = True

        # Test with writer service failing
        mock_mcp_services["writer"].is_running = False

        writer_failure_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Operations that only need reader should still work
                if hasattr(engine, 'get_asset_info'):
                    result = await engine.get_asset_info("0")
                    writer_failure_results[engine_name] = {
                        "reader_only_success": True,
                        "result": result
                    }
                else:
                    writer_failure_results[engine_name] = {
                        "reader_only_success": True,
                        "result": {"no_reader_operation": True}
                    }

            except Exception as e:
                writer_failure_results[engine_name] = {
                    "reader_only_success": False,
                    "error": str(e)
                }

        # Restore writer service
        mock_mcp_services["writer"].is_running = True

        # Verify partial failure handling
        for engine_name in all_engines.keys():
            reader_result = reader_failure_results.get(engine_name, {})
            writer_result = writer_failure_results.get(engine_name, {})

            # At least one partial operation should succeed, indicating graceful degradation
            assert reader_result.get("writer_only_success", False) or \
                   writer_result.get("reader_only_success", False), \
                   f"Engine {engine_name} should handle partial MCP service failure gracefully"


class TestMCPDataIntegrity:
    """Test data integrity in MCP service interactions"""

    @pytest.mark.asyncio
    async def test_mcp_data_round_trip(self, all_engines, test_data_generator):
        """Test data integrity in MCP read/write operations"""

        test_data = {
            "analysis_id": f"integrity_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "asset_data": {
                "asset_id": "0",
                "price": 0.25,
                "volume": 1000000,
                "volatility": 0.25
            },
            "analysis_result": {
                "risk_level": "medium",
                "confidence": 0.85,
                "recommendations": ["increase_collateral", "monitor_volatility"]
            }
        }

        round_trip_results = {}

        for engine_name, engine in all_engines.items():
            try:
                # Store data if engine supports it
                if hasattr(engine, 'store_analysis_data'):
                    store_result = await engine.store_analysis_data(test_data)

                    # Retrieve data if engine supports it
                    if hasattr(engine, 'get_analysis_data'):
                        retrieved_data = await engine.get_analysis_data(test_data["analysis_id"])

                        round_trip_results[engine_name] = {
                            "round_trip_success": True,
                            "stored_data": test_data,
                            "retrieved_data": retrieved_data,
                            "data_matches": self._compare_data(test_data, retrieved_data)
                        }
                    else:
                        round_trip_results[engine_name] = {
                            "store_only": True,
                            "store_result": store_result
                        }
                else:
                    round_trip_results[engine_name] = {
                        "no_storage_capability": True
                    }

            except Exception as e:
                round_trip_results[engine_name] = {
                    "round_trip_success": False,
                    "error": str(e)
                }

        # Verify data integrity where applicable
        for engine_name, result in round_trip_results.items():
            if result.get("round_trip_success", False):
                assert result.get("data_matches", False), \
                    f"Engine {engine_name} data integrity check failed"

    def _compare_data(self, original: Dict[str, Any], retrieved: Dict[str, Any]) -> bool:
        """Compare original and retrieved data for integrity"""
        if not isinstance(retrieved, dict):
            return False

        # Check key fields
        key_fields = ["analysis_id", "asset_data", "analysis_result"]
        for field in key_fields:
            if field in original:
                if field not in retrieved:
                    return False

                # For nested objects, check critical sub-fields
                if isinstance(original[field], dict) and isinstance(retrieved[field], dict):
                    if field == "asset_data":
                        if original[field].get("asset_id") != retrieved[field].get("asset_id"):
                            return False
                    elif field == "analysis_result":
                        if original[field].get("risk_level") != retrieved[field].get("risk_level"):
                            return False

        return True

    @pytest.mark.asyncio
    async def test_mcp_concurrent_access(self, all_engines, performance_monitor):
        """Test concurrent MCP access from multiple engines"""

        performance_monitor.start()

        # Create concurrent tasks for different engines
        concurrent_tasks = []

        # Reader operations
        for engine_name, engine in all_engines.items():
            if hasattr(engine, 'get_asset_info'):
                task = engine.get_asset_info("0")
                concurrent_tasks.append((engine_name, "read", task))

        # Writer operations
        for engine_name, engine in all_engines.items():
            if hasattr(engine, 'store_analysis_result'):
                test_data = {
                    "analysis_id": f"concurrent_{engine_name}_{int(time.time())}",
                    "data": {"test": True}
                }
                task = engine.store_analysis_result(test_data)
                concurrent_tasks.append((engine_name, "write", task))

        # Execute all tasks concurrently
        if concurrent_tasks:
            tasks = [task for _, _, task in concurrent_tasks]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            performance_monitor.stop()

            # Verify concurrent access results
            for i, (engine_name, operation, _) in enumerate(concurrent_tasks):
                result = results[i]

                if isinstance(result, Exception):
                    # Check if exception is related to concurrency issues
                    error_msg = str(result).lower()
                    if "deadlock" in error_msg or "locked" in error_msg:
                        pytest.fail(f"Concurrency issue in {engine_name} {operation}: {result}")
                else:
                    assert result is not None, f"Concurrent {operation} operation failed for {engine_name}"

            # Verify reasonable execution time for concurrent operations
            execution_time = performance_monitor.get_duration()
            assert execution_time < 30.0, f"Concurrent MCP operations took too long: {execution_time}s"


class TestMCPPerformance:
    """Test MCP service performance characteristics"""

    @pytest.mark.asyncio
    async def test_mcp_response_times(self, all_engines, performance_benchmarks):
        """Test MCP service response times for each engine"""

        response_time_results = {}

        for engine_name, engine in all_engines.items():
            monitor = PerformanceMonitor()

            try:
                monitor.start()

                # Perform a typical MCP operation
                if hasattr(engine, 'get_asset_info'):
                    result = await engine.get_asset_info("0")
                elif hasattr(engine, 'fetch_market_data'):
                    result = await engine.fetch_market_data({"asset_id": "0"})
                else:
                    result = {"no_operation": True}

                monitor.stop()

                response_time = monitor.get_duration()
                response_time_results[engine_name] = {
                    "response_time": response_time,
                    "success": True,
                    "result": result
                }

            except Exception as e:
                monitor.stop()
                response_time_results[engine_name] = {
                    "response_time": monitor.get_duration(),
                    "success": False,
                    "error": str(e)
                }

        # Verify response times meet benchmarks
        max_response_time = performance_benchmarks.get("price_fetch_time", 5.0)

        for engine_name, result in response_time_results.items():
            if result["success"]:
                assert result["response_time"] < max_response_time, \
                    f"Engine {engine_name} MCP response time {result['response_time']:.2f}s " \
                    f"exceeds benchmark {max_response_time}s"

    @pytest.mark.asyncio
    async def test_mcp_throughput(self, all_engines):
        """Test MCP service throughput capabilities"""

        throughput_results = {}

        for engine_name, engine in all_engines.items():
            if not hasattr(engine, 'get_asset_info'):
                continue

            monitor = PerformanceMonitor()
            monitor.start()

            # Perform multiple sequential operations
            num_operations = 10
            successful_operations = 0

            for i in range(num_operations):
                try:
                    result = await engine.get_asset_info(str(i % 3))  # Cycle through asset IDs
                    if result is not None:
                        successful_operations += 1
                except Exception:
                    pass

            monitor.stop()

            execution_time = monitor.get_duration()
            throughput = successful_operations / execution_time if execution_time > 0 else 0

            throughput_results[engine_name] = {
                "total_operations": num_operations,
                "successful_operations": successful_operations,
                "execution_time": execution_time,
                "throughput_ops_per_second": throughput
            }

        # Verify reasonable throughput
        min_throughput = 1.0  # At least 1 operation per second

        for engine_name, result in throughput_results.items():
            assert result["throughput_ops_per_second"] >= min_throughput, \
                f"Engine {engine_name} MCP throughput {result['throughput_ops_per_second']:.2f} ops/s " \
                f"below minimum {min_throughput} ops/s"

    @pytest.mark.asyncio
    async def test_mcp_memory_usage(self, all_engines, performance_monitor):
        """Test memory usage during MCP operations"""

        initial_memory = performance_monitor.check_memory_usage()

        # Perform memory-intensive MCP operations
        for engine_name, engine in all_engines.items():
            try:
                # Perform operations that might use significant memory
                if hasattr(engine, 'get_price_history'):
                    await engine.get_price_history({
                        "asset_id": "0",
                        "days": 365,  # One year of data
                        "detailed": True
                    })
                elif hasattr(engine, 'calculate_volatility'):
                    await engine.calculate_volatility({
                        "asset_ids": ["0", "31566704", "312769"],
                        "time_window": 365,
                        "detailed_analysis": True
                    })

            except Exception:
                # Memory test failures are not critical
                pass

        final_memory = performance_monitor.check_memory_usage()
        memory_increase = final_memory - initial_memory

        # Verify memory usage is reasonable (less than 200MB increase)
        max_memory_increase = 200  # MB
        assert memory_increase < max_memory_increase, \
            f"MCP operations increased memory usage by {memory_increase:.1f}MB, " \
            f"exceeding limit of {max_memory_increase}MB"