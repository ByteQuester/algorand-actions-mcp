#!/usr/bin/env python3
"""
Comprehensive Test Runner for MCP Integration Framework

Executes all test suites with performance benchmarking and detailed reporting:
1. Framework connectivity and health checks
2. Data pipeline integration tests
3. End-to-end lending workflow tests
4. Performance benchmarking under load
5. Error handling and recovery testing

Features:
- Parallel test execution where safe
- Detailed performance metrics collection
- Comprehensive error reporting
- Service health monitoring throughout testing
- Automated test result aggregation
- Export to multiple formats (JSON, HTML, CSV)
"""

import asyncio
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Import all test frameworks
from test_framework import LendingEngineTestFramework, ServiceConfig, TestMode
from test_data_pipeline import DataPipelineTestFramework, PipelineTestConfig
from test_end_to_end import EndToEndTestFramework


class ComprehensiveTestRunner:
    """Runs all MCP integration tests with performance benchmarking"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.overall_metrics = []

        # Setup logging
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Test configurations
        self.service_config = ServiceConfig(
            reader_url=self.config.get("reader_url", "http://localhost:8002"),
            writer_url=self.config.get("writer_url", "http://localhost:3001"),
            market_data_url=self.config.get("market_data_url", "http://localhost:8789"),
            timeout=self.config.get("timeout", 30),
            retry_attempts=self.config.get("retry_attempts", 3)
        )

        self.pipeline_config = PipelineTestConfig(
            use_real_data=self.config.get("use_real_data", True),
            performance_mode=self.config.get("performance_mode", True),
            concurrent_requests=self.config.get("concurrent_requests", 5),
            data_consistency_checks=self.config.get("data_consistency_checks", True)
        )

    async def check_prerequisites(self) -> Dict[str, Any]:
        """Check if all services are available before running tests"""
        self.logger.info("Checking test prerequisites...")

        prereq_results = {
            "all_services_available": False,
            "service_status": {},
            "lending_engines_available": False,
            "errors": []
        }

        try:
            # Check MCP services
            framework = LendingEngineTestFramework(self.service_config, TestMode.REAL_DATA)
            await framework.initialize()

            try:
                connectivity_result = await framework.test_service_connectivity()
                prereq_results["service_status"] = connectivity_result.get("service_status", {})
                prereq_results["all_services_available"] = connectivity_result.get("all_services_healthy", False)

                # Check lending engines
                if framework.lending_engines:
                    prereq_results["lending_engines_available"] = True
                else:
                    prereq_results["errors"].append("Lending engines not available")

            finally:
                await framework.cleanup()

        except Exception as e:
            prereq_results["errors"].append(f"Failed to check prerequisites: {e}")

        return prereq_results

    async def run_framework_tests(self) -> Dict[str, Any]:
        """Run main framework connectivity and health tests"""
        self.logger.info("Running framework tests...")

        try:
            framework = LendingEngineTestFramework(self.service_config, TestMode.HYBRID)
            suite = await framework.run_comprehensive_test_suite()

            return {
                "success": True,
                "suite": {
                    "total_tests": suite.total_tests,
                    "passed_tests": suite.passed_tests,
                    "failed_tests": suite.failed_tests,
                    "success_rate": suite.passed_tests / suite.total_tests if suite.total_tests > 0 else 0,
                    "duration": suite.total_duration,
                    "performance_summary": suite.performance_summary
                },
                "detailed_results": [
                    {
                        "test_name": result.test_name,
                        "success": result.success,
                        "duration": result.duration,
                        "error": result.error
                    }
                    for result in suite.results
                ]
            }

        except Exception as e:
            self.logger.error(f"Framework tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": 0
            }

    async def run_pipeline_tests(self) -> Dict[str, Any]:
        """Run data pipeline integration tests"""
        self.logger.info("Running data pipeline tests...")

        try:
            framework = DataPipelineTestFramework(self.pipeline_config, self.service_config)
            results = await framework.run_comprehensive_pipeline_tests()

            # Extract summary metrics
            summary = results.get("summary", {})
            return {
                "success": True,
                "summary": summary,
                "reader_mcp": {
                    "account_tests": len(results.get("reader_mcp", {}).get("account_tests", [])),
                    "asset_tests": len(results.get("reader_mcp", {}).get("asset_tests", [])),
                    "success_rate": self._calculate_success_rate(results.get("reader_mcp", {}))
                },
                "market_data_mcp": {
                    "price_tests": len(results.get("market_data_mcp", {}).get("price_tests", [])),
                    "success_rate": self._calculate_success_rate(results.get("market_data_mcp", {}))
                },
                "cross_service": {
                    "correlation_tests": len(results.get("cross_service", {}).get("correlation_tests", [])),
                    "integration_health": results.get("cross_service", {}).get("integration_health", {})
                },
                "duration": summary.get("test_completion_time", datetime.now().isoformat())
            }

        except Exception as e:
            self.logger.error(f"Pipeline tests failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end lending workflow tests"""
        self.logger.info("Running end-to-end tests...")

        try:
            framework = EndToEndTestFramework(self.service_config, self.pipeline_config)
            results = await framework.run_comprehensive_e2e_tests()

            # Extract key metrics
            summary = results.get("summary", {})
            loan_scenarios = summary.get("loan_scenarios", {})
            stress_tests = summary.get("stress_tests", {})
            performance = summary.get("performance", {})

            return {
                "success": True,
                "loan_scenarios": {
                    "total_scenarios": loan_scenarios.get("total_scenarios", 0),
                    "success_rate": loan_scenarios.get("success_rate", 0),
                    "prediction_accuracy": loan_scenarios.get("average_prediction_accuracy", 0),
                    "performance_score": loan_scenarios.get("average_performance_score", 0)
                },
                "stress_tests": {
                    "concurrency_efficiency": stress_tests.get("concurrency_efficiency", 0),
                    "concurrent_scenarios": stress_tests.get("concurrent_scenarios_tested", 0)
                },
                "performance": {
                    "total_operations": performance.get("total_operations", 0),
                    "services_tested": performance.get("services_tested", 0),
                    "average_success_rate": performance.get("average_success_rate", 0)
                },
                "detailed_scenarios": results.get("loan_scenarios", {}).get("scenario_results", [])
            }

        except Exception as e:
            self.logger.error(f"End-to-end tests failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run dedicated performance benchmarking tests"""
        self.logger.info("Running performance benchmarks...")

        benchmarks = {
            "service_response_times": {},
            "concurrent_load_test": {},
            "engine_performance": {},
            "memory_usage": {}
        }

        try:
            # Service response time benchmarks
            framework = LendingEngineTestFramework(self.service_config, TestMode.PERFORMANCE)
            await framework.initialize()

            try:
                # Test service response times under load
                start_time = time.time()
                connectivity_results = []

                for i in range(10):  # 10 iterations
                    result = await framework.test_service_connectivity()
                    connectivity_results.append(result)
                    await asyncio.sleep(0.1)  # Small delay between tests

                total_time = time.time() - start_time

                benchmarks["service_response_times"] = {
                    "iterations": len(connectivity_results),
                    "total_duration": total_time,
                    "average_per_iteration": total_time / len(connectivity_results),
                    "all_successful": all(r.get("all_services_healthy", False) for r in connectivity_results)
                }

                # Engine performance benchmarks
                engine_start = time.time()
                engine_result = await framework.test_lending_engine_performance()
                engine_duration = time.time() - engine_start

                benchmarks["engine_performance"] = {
                    "duration": engine_duration,
                    "all_engines_operational": engine_result.get("all_engines_operational", False),
                    "average_engine_duration": engine_result.get("average_duration", 0),
                    "engine_results": engine_result.get("engine_results", {})
                }

            finally:
                await framework.cleanup()

            # Concurrent load test
            if self.config.get("run_load_tests", True):
                concurrent_start = time.time()

                # Run multiple frameworks concurrently
                concurrent_tasks = []
                for i in range(3):  # 3 concurrent instances
                    task_framework = LendingEngineTestFramework(self.service_config, TestMode.PERFORMANCE)
                    concurrent_tasks.append(task_framework.test_service_connectivity())

                concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
                concurrent_duration = time.time() - concurrent_start

                successful_concurrent = sum(1 for r in concurrent_results
                                          if not isinstance(r, Exception) and r.get("all_services_healthy", False))

                benchmarks["concurrent_load_test"] = {
                    "concurrent_instances": len(concurrent_tasks),
                    "successful_instances": successful_concurrent,
                    "total_duration": concurrent_duration,
                    "success_rate": successful_concurrent / len(concurrent_tasks),
                    "throughput": len(concurrent_tasks) / concurrent_duration
                }

            return {
                "success": True,
                "benchmarks": benchmarks
            }

        except Exception as e:
            self.logger.error(f"Performance benchmarks failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "partial_benchmarks": benchmarks
            }

    def _calculate_success_rate(self, test_category: Dict) -> float:
        """Calculate success rate for a test category"""
        if isinstance(test_category, dict):
            for key in ["account_tests", "asset_tests", "price_tests", "correlation_tests"]:
                if key in test_category:
                    tests = test_category[key]
                    if isinstance(tests, list) and tests:
                        successful = sum(1 for test in tests if test.get("success", False))
                        return successful / len(tests)
        return 0.0

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite with all components"""
        self.start_time = datetime.now()
        self.logger.info("Starting comprehensive MCP integration test suite")

        # Final results structure
        final_results = {
            "execution_info": {
                "start_time": self.start_time.isoformat(),
                "test_configuration": {
                    "service_urls": {
                        "reader": self.service_config.reader_url,
                        "writer": self.service_config.writer_url,
                        "market_data": self.service_config.market_data_url
                    },
                    "performance_mode": self.pipeline_config.performance_mode,
                    "concurrent_requests": self.pipeline_config.concurrent_requests,
                    "use_real_data": self.pipeline_config.use_real_data
                }
            },
            "test_results": {},
            "summary": {},
            "errors": []
        }

        try:
            # 1. Prerequisites check
            self.logger.info("Step 1: Checking prerequisites...")
            prereq_results = await self.check_prerequisites()
            final_results["test_results"]["prerequisites"] = prereq_results

            if not prereq_results["all_services_available"]:
                self.logger.warning("Some services unavailable, continuing with available tests...")

            # 2. Framework tests
            self.logger.info("Step 2: Running framework tests...")
            framework_results = await self.run_framework_tests()
            final_results["test_results"]["framework"] = framework_results

            # 3. Pipeline tests
            self.logger.info("Step 3: Running pipeline tests...")
            pipeline_results = await self.run_pipeline_tests()
            final_results["test_results"]["pipeline"] = pipeline_results

            # 4. End-to-end tests
            self.logger.info("Step 4: Running end-to-end tests...")
            e2e_results = await self.run_e2e_tests()
            final_results["test_results"]["end_to_end"] = e2e_results

            # 5. Performance benchmarks
            if self.config.get("run_performance_tests", True):
                self.logger.info("Step 5: Running performance benchmarks...")
                perf_results = await self.run_performance_benchmarks()
                final_results["test_results"]["performance"] = perf_results

        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            final_results["errors"].append(str(e))

        finally:
            self.end_time = datetime.now()
            final_results["execution_info"]["end_time"] = self.end_time.isoformat()
            final_results["execution_info"]["total_duration"] = (self.end_time - self.start_time).total_seconds()

        # Generate summary
        final_results["summary"] = self._generate_final_summary(final_results)

        return final_results

    def _generate_final_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final comprehensive summary"""
        test_results = results.get("test_results", {})

        summary = {
            "overall_success": True,
            "test_categories_completed": 0,
            "test_categories_failed": 0,
            "total_duration": results.get("execution_info", {}).get("total_duration", 0),
            "service_health": {},
            "performance_metrics": {},
            "recommendations": []
        }

        # Analyze each test category
        for category, result in test_results.items():
            if result.get("success", False):
                summary["test_categories_completed"] += 1
            else:
                summary["test_categories_failed"] += 1
                summary["overall_success"] = False

        # Service health summary
        if "prerequisites" in test_results:
            prereq = test_results["prerequisites"]
            summary["service_health"] = {
                "all_services_available": prereq.get("all_services_available", False),
                "service_status": prereq.get("service_status", {}),
                "lending_engines_available": prereq.get("lending_engines_available", False)
            }

        # Performance summary
        if "performance" in test_results:
            perf = test_results["performance"]
            if perf.get("success"):
                benchmarks = perf.get("benchmarks", {})
                summary["performance_metrics"] = {
                    "service_response_time": benchmarks.get("service_response_times", {}).get("average_per_iteration", 0),
                    "concurrent_success_rate": benchmarks.get("concurrent_load_test", {}).get("success_rate", 0),
                    "engine_performance": benchmarks.get("engine_performance", {}).get("all_engines_operational", False)
                }

        # Generate recommendations
        if not summary["service_health"].get("all_services_available", False):
            summary["recommendations"].append("Some MCP services are unavailable - check service status")

        if summary["performance_metrics"].get("service_response_time", 0) > 5.0:
            summary["recommendations"].append("Service response times are high - consider performance optimization")

        if summary["performance_metrics"].get("concurrent_success_rate", 1.0) < 0.8:
            summary["recommendations"].append("Concurrent load test success rate is low - investigate resource constraints")

        if not summary["performance_metrics"].get("engine_performance", True):
            summary["recommendations"].append("Some lending engines are not performing optimally")

        return summary

    def save_results(self, results: Dict[str, Any], output_dir: str = None) -> List[str]:
        """Save test results in multiple formats"""
        if output_dir is None:
            output_dir = "/home/mpo/algorand-showcase/tests/mcp_integration"

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []

        # Save JSON results
        json_file = output_dir / f"comprehensive_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        saved_files.append(str(json_file))

        # Save summary report
        summary_file = output_dir / f"test_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(self._generate_text_report(results))
        saved_files.append(str(summary_file))

        return saved_files

    def _generate_text_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable text report"""
        report = []
        report.append("="*80)
        report.append("COMPREHENSIVE MCP INTEGRATION TEST REPORT")
        report.append("="*80)

        exec_info = results.get("execution_info", {})
        report.append(f"\nExecution Time: {exec_info.get('start_time', 'Unknown')} - {exec_info.get('end_time', 'Unknown')}")
        report.append(f"Total Duration: {exec_info.get('total_duration', 0):.2f} seconds")

        summary = results.get("summary", {})
        report.append(f"\nOVERALL RESULT: {'PASS' if summary.get('overall_success') else 'FAIL'}")
        report.append(f"Categories Completed: {summary.get('test_categories_completed', 0)}")
        report.append(f"Categories Failed: {summary.get('test_categories_failed', 0)}")

        # Service Health
        service_health = summary.get("service_health", {})
        report.append(f"\nSERVICE HEALTH:")
        report.append(f"  All Services Available: {service_health.get('all_services_available', False)}")
        report.append(f"  Lending Engines Available: {service_health.get('lending_engines_available', False)}")

        service_status = service_health.get("service_status", {})
        for service, status in service_status.items():
            report.append(f"  {service.title()}: {status}")

        # Performance Metrics
        perf_metrics = summary.get("performance_metrics", {})
        if perf_metrics:
            report.append(f"\nPERFORMANCE METRICS:")
            report.append(f"  Average Service Response: {perf_metrics.get('service_response_time', 0):.3f}s")
            report.append(f"  Concurrent Success Rate: {perf_metrics.get('concurrent_success_rate', 0)*100:.1f}%")
            report.append(f"  Engine Performance: {'OK' if perf_metrics.get('engine_performance') else 'ISSUES'}")

        # Recommendations
        recommendations = summary.get("recommendations", [])
        if recommendations:
            report.append(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"  {i}. {rec}")

        # Detailed Results
        test_results = results.get("test_results", {})
        report.append(f"\nDETAILED RESULTS:")
        report.append("-" * 50)

        for category, result in test_results.items():
            status = "PASS" if result.get("success", False) else "FAIL"
            report.append(f"{category.upper():<20} {status}")

            if category == "framework" and "suite" in result:
                suite = result["suite"]
                report.append(f"  Tests: {suite['passed_tests']}/{suite['total_tests']} passed ({suite['success_rate']*100:.1f}%)")

            elif category == "pipeline" and "summary" in result:
                summary = result["summary"]
                report.append(f"  Operations: {summary.get('total_operations', 0)}, Success: {summary.get('successful_operations', 0)}")

            elif category == "end_to_end" and "loan_scenarios" in result:
                scenarios = result["loan_scenarios"]
                report.append(f"  Scenarios: {scenarios['total_scenarios']}, Success: {scenarios['success_rate']*100:.1f}%")
                report.append(f"  Prediction Accuracy: {scenarios['prediction_accuracy']*100:.1f}%")

        report.append("\n" + "="*80)
        return "\n".join(report)

    def print_final_summary(self, results: Dict[str, Any]):
        """Print final test summary to console"""
        print(self._generate_text_report(results))


async def main():
    """Main function for running comprehensive tests"""
    parser = argparse.ArgumentParser(description="Comprehensive MCP Integration Test Runner")
    parser.add_argument("--reader-url", default="http://localhost:8002", help="Reader MCP URL")
    parser.add_argument("--writer-url", default="http://localhost:3001", help="Writer MCP URL")
    parser.add_argument("--market-data-url", default="http://localhost:8789", help="Market Data MCP URL")
    parser.add_argument("--performance-mode", action="store_true", help="Enable performance testing")
    parser.add_argument("--concurrent-requests", type=int, default=5, help="Number of concurrent requests")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--output-dir", help="Output directory for results")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    # Configuration from arguments
    config = {
        "reader_url": args.reader_url,
        "writer_url": args.writer_url,
        "market_data_url": args.market_data_url,
        "performance_mode": args.performance_mode,
        "concurrent_requests": args.concurrent_requests,
        "timeout": args.timeout,
        "log_level": args.log_level,
        "use_real_data": True,
        "run_performance_tests": True,
        "run_load_tests": True,
        "data_consistency_checks": True
    }

    print("Starting Comprehensive MCP Integration Test Runner")
    print(f"Configuration: {config}")

    runner = ComprehensiveTestRunner(config)

    try:
        # Run all tests
        results = await runner.run_all_tests()

        # Print summary
        runner.print_final_summary(results)

        # Save results
        saved_files = runner.save_results(results, args.output_dir)
        print(f"\nResults saved to:")
        for file_path in saved_files:
            print(f"  {file_path}")

        # Return success code
        overall_success = results.get("summary", {}).get("overall_success", False)
        return 0 if overall_success else 1

    except Exception as e:
        print(f"Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)