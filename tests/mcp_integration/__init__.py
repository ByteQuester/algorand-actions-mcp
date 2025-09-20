"""
MCP Integration Test Framework

Automated testing framework for integrating MCP services with lending engines.
Provides comprehensive testing of:
- Reader MCP (blockchain data)
- Writer MCP (transaction execution)
- Market Data MCP (price feeds)
- All 4 lending engines (collateral, interest rate, loan approval, risk assessment)

Key Features:
- Async test execution with performance benchmarking
- Real blockchain data validation
- Mock/real data switching capability
- Service health monitoring
- Cross-engine integration testing
- Error handling and fallback mechanisms
- Comprehensive test result reporting

Usage:
    from tests.mcp_integration import LendingEngineTestFramework

    framework = LendingEngineTestFramework()
    results = await framework.run_comprehensive_test_suite()
"""

__version__ = "1.0.0"
__author__ = "Algorand Lending Platform Team"

from .test_framework import (
    LendingEngineTestFramework,
    MCPServiceClient,
    ServiceConfig,
    ServiceHealth,
    PerformanceMetrics,
    TestResult,
    TestSuite,
    TestMode
)

from .test_data_pipeline import (
    DataPipelineTestFramework,
    DataValidator,
    DataFixture,
    PipelineTestConfig
)

from .test_end_to_end import (
    EndToEndTestFramework,
    LoanScenario,
    WorkflowResult
)

__all__ = [
    # Main frameworks
    "LendingEngineTestFramework",
    "DataPipelineTestFramework",
    "EndToEndTestFramework",

    # Client and configuration
    "MCPServiceClient",
    "ServiceConfig",
    "PipelineTestConfig",

    # Data structures
    "ServiceHealth",
    "PerformanceMetrics",
    "TestResult",
    "TestSuite",
    "TestMode",
    "DataValidator",
    "DataFixture",
    "LoanScenario",
    "WorkflowResult"
]