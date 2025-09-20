"""
Integration Test Configuration and Fixtures

This module provides shared test fixtures, mock services, and test data generators
for the blockchain collateral analyzer integration testing suite.
"""

import pytest
import asyncio
import aiohttp
import json
import sqlite3
import tempfile
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator
from unittest.mock import Mock, AsyncMock, MagicMock
from dataclasses import dataclass
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import all engines
from collateral_requirements.core import CollateralRequirementsEngine
from digital_asset_valuation.core.engine import DigitalAssetValuationEngine
from oracle_price_integration.core.oracle_engine import OraclePriceEngine
from portfolio_diversification.core.portfolio_engine import PortfolioEngine
from volatility_assessment.core.volatility_engine import VolatilityEngine
from liquidation_scenarios.core.liquidation_scenarios_engine import LiquidationScenariosEngine

# Import shared models
from common.models.blockchain_collateral_models import (
    DigitalAsset, CollateralPosition, CollateralPortfolio,
    LiquidationScenario, CollateralAnalysisResult,
    DigitalCollateralType, VolatilityMetrics, LiquidityMetrics, PriceOracle
)


@dataclass
class TestConfig:
    """Test configuration constants"""
    MCP_READER_URL = "http://localhost:8002"
    MCP_WRITER_URL = "http://localhost:8003"
    TEST_DATABASE_PATH = ":memory:"
    DEFAULT_TIMEOUT = 30.0
    PERFORMANCE_TIMEOUT = 60.0

    # Test asset IDs
    ALGO_ASSET_ID = "0"
    USDC_ASSET_ID = "31566704"
    USDT_ASSET_ID = "312769"

    # Test amounts
    DEFAULT_LOAN_AMOUNT = 50000.0
    LARGE_LOAN_AMOUNT = 500000.0
    SMALL_LOAN_AMOUNT = 5000.0


@dataclass
class MockAssetData:
    """Mock asset data for testing"""
    asset_id: str
    symbol: str
    name: str
    price_usd: float
    market_cap: float
    volume_24h: float
    volatility_30d: float
    liquidity_score: float


class MockMCPService:
    """Mock MCP service for testing without external dependencies"""

    def __init__(self, port: int):
        self.port = port
        self.is_running = False
        self.mock_data = {}

    def start(self):
        """Start mock MCP service"""
        self.is_running = True

    def stop(self):
        """Stop mock MCP service"""
        self.is_running = False

    def add_mock_data(self, endpoint: str, data: Dict[str, Any]):
        """Add mock data for specific endpoint"""
        self.mock_data[endpoint] = data

    async def get_asset_info(self, asset_id: str) -> Dict[str, Any]:
        """Get mock asset information"""
        return self.mock_data.get(f"asset/{asset_id}", {
            "asset_id": asset_id,
            "name": f"Asset {asset_id}",
            "unit_name": f"AST{asset_id[:3]}",
            "total": 1000000000,
            "decimals": 6,
            "creator": "mock_creator",
            "frozen": False
        })

    async def get_asset_price(self, asset_id: str) -> Dict[str, Any]:
        """Get mock asset price"""
        mock_prices = {
            "0": {"price": 0.25, "symbol": "ALGO"},
            "31566704": {"price": 1.00, "symbol": "USDC"},
            "312769": {"price": 1.00, "symbol": "USDT"}
        }
        return mock_prices.get(asset_id, {"price": 1.0, "symbol": "UNKNOWN"})


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TestConfig()


@pytest.fixture(scope="session")
def mock_asset_data():
    """Provide mock asset data for testing"""
    return {
        "0": MockAssetData(
            asset_id="0",
            symbol="ALGO",
            name="Algorand",
            price_usd=0.25,
            market_cap=1800000000,
            volume_24h=50000000,
            volatility_30d=0.25,
            liquidity_score=0.85
        ),
        "31566704": MockAssetData(
            asset_id="31566704",
            symbol="USDC",
            name="USD Coin",
            price_usd=1.00,
            market_cap=25000000000,
            volume_24h=2000000000,
            volatility_30d=0.02,
            liquidity_score=0.98
        ),
        "312769": MockAssetData(
            asset_id="312769",
            symbol="USDT",
            name="Tether USD",
            price_usd=1.00,
            market_cap=83000000000,
            volume_24h=30000000000,
            volatility_30d=0.01,
            liquidity_score=0.99
        )
    }


@pytest.fixture(scope="session")
async def mock_mcp_services(test_config):
    """Start mock MCP services for testing"""
    reader_service = MockMCPService(8002)
    writer_service = MockMCPService(8003)

    # Add mock data
    reader_service.add_mock_data("health", {"status": "healthy", "timestamp": datetime.now().isoformat()})
    writer_service.add_mock_data("health", {"status": "healthy", "timestamp": datetime.now().isoformat()})

    reader_service.start()
    writer_service.start()

    yield {
        "reader": reader_service,
        "writer": writer_service
    }

    reader_service.stop()
    writer_service.stop()


@pytest.fixture
def temp_database():
    """Create temporary database for testing"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    # Initialize database
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collateral_analysis (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            loan_amount REAL,
            collateral_value REAL,
            risk_level TEXT,
            analysis_data TEXT
        )
    """)
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def collateral_engine(temp_database, mock_mcp_services):
    """Create CollateralRequirementsEngine instance"""
    config = {
        "database_path": temp_database,
        "mcp_reader_url": "http://localhost:8002",
        "mcp_writer_url": "http://localhost:8003",
        "default_timeout": 30.0
    }

    engine = CollateralRequirementsEngine(config)
    await engine.initialize()

    yield engine

    await engine.cleanup()


@pytest.fixture
async def valuation_engine(mock_mcp_services):
    """Create DigitalAssetValuationEngine instance"""
    config = {
        "mcp_reader_url": "http://localhost:8002",
        "mcp_writer_url": "http://localhost:8003",
        "cache_ttl": 300,
        "timeout": 30.0
    }

    engine = DigitalAssetValuationEngine(config)
    await engine.initialize()

    yield engine

    await engine.cleanup()


@pytest.fixture
async def oracle_engine(mock_mcp_services):
    """Create OraclePriceEngine instance"""
    config = {
        "mcp_reader_url": "http://localhost:8002",
        "price_sources": ["mcp", "fallback"],
        "update_interval": 60,
        "timeout": 30.0
    }

    engine = OraclePriceEngine(config)
    await engine.initialize()

    yield engine

    await engine.cleanup()


@pytest.fixture
async def portfolio_engine(mock_mcp_services):
    """Create PortfolioEngine instance"""
    config = {
        "mcp_reader_url": "http://localhost:8002",
        "mcp_writer_url": "http://localhost:8003",
        "diversification_threshold": 0.3,
        "timeout": 30.0
    }

    engine = PortfolioEngine(config)
    await engine.initialize()

    yield engine

    await engine.cleanup()


@pytest.fixture
async def volatility_engine(mock_mcp_services):
    """Create VolatilityEngine instance"""
    config = {
        "mcp_reader_url": "http://localhost:8002",
        "volatility_window": 30,
        "update_frequency": 3600,
        "timeout": 30.0
    }

    engine = VolatilityEngine(config)
    await engine.initialize()

    yield engine

    await engine.cleanup()


@pytest.fixture
async def liquidation_engine(mock_mcp_services):
    """Create LiquidationScenariosEngine instance"""
    config = {
        "mcp_reader_url": "http://localhost:8002",
        "mcp_writer_url": "http://localhost:8003",
        "liquidation_threshold": 1.2,
        "timeout": 30.0
    }

    engine = LiquidationScenariosEngine(config)
    await engine.initialize()

    yield engine

    await engine.cleanup()


@pytest.fixture
async def all_engines(collateral_engine, valuation_engine, oracle_engine,
                     portfolio_engine, volatility_engine, liquidation_engine):
    """Provide all engines for cross-engine testing"""
    return {
        "collateral": collateral_engine,
        "valuation": valuation_engine,
        "oracle": oracle_engine,
        "portfolio": portfolio_engine,
        "volatility": volatility_engine,
        "liquidation": liquidation_engine
    }


@pytest.fixture
def sample_collateral_positions(mock_asset_data):
    """Generate sample collateral positions for testing"""
    return [
        CollateralPosition(
            asset_id="0",
            asset_type=DigitalCollateralType.NATIVE_TOKEN,
            quantity=200000.0,
            current_price_usd=0.25,
            volatility_metrics=VolatilityMetrics(
                daily_volatility=0.03,
                weekly_volatility=0.08,
                monthly_volatility=0.25
            ),
            liquidity_metrics=LiquidityMetrics(
                bid_ask_spread=0.001,
                market_depth=1000000.0,
                daily_volume=50000000.0
            )
        ),
        CollateralPosition(
            asset_id="31566704",
            asset_type=DigitalCollateralType.STABLECOIN,
            quantity=25000.0,
            current_price_usd=1.00,
            volatility_metrics=VolatilityMetrics(
                daily_volatility=0.001,
                weekly_volatility=0.002,
                monthly_volatility=0.02
            ),
            liquidity_metrics=LiquidityMetrics(
                bid_ask_spread=0.0001,
                market_depth=10000000.0,
                daily_volume=2000000000.0
            )
        )
    ]


@pytest.fixture
def sample_lending_scenarios():
    """Generate sample lending scenarios for testing"""
    return [
        {
            "scenario_name": "conservative_lending",
            "loan_amount": 25000.0,
            "collateral_ratio": 1.5,
            "borrower_profile": "low_risk",
            "market_conditions": "stable"
        },
        {
            "scenario_name": "aggressive_lending",
            "loan_amount": 100000.0,
            "collateral_ratio": 1.2,
            "borrower_profile": "high_risk",
            "market_conditions": "volatile"
        },
        {
            "scenario_name": "institutional_lending",
            "loan_amount": 1000000.0,
            "collateral_ratio": 1.3,
            "borrower_profile": "institutional",
            "market_conditions": "stable"
        }
    ]


@pytest.fixture
def performance_benchmarks():
    """Define performance benchmarks for testing"""
    return {
        "collateral_analysis_time": 5.0,  # seconds
        "price_fetch_time": 2.0,
        "risk_assessment_time": 3.0,
        "portfolio_analysis_time": 4.0,
        "volatility_calculation_time": 3.0,
        "liquidation_scenario_time": 6.0,
        "memory_usage_mb": 500,  # MB
        "concurrent_requests": 10
    }


@pytest.fixture
def mock_market_conditions():
    """Generate mock market conditions for stress testing"""
    return {
        "bull_market": {
            "price_trend": "up",
            "volatility_multiplier": 0.8,
            "liquidity_multiplier": 1.2
        },
        "bear_market": {
            "price_trend": "down",
            "volatility_multiplier": 1.5,
            "liquidity_multiplier": 0.7
        },
        "sideways_market": {
            "price_trend": "flat",
            "volatility_multiplier": 1.0,
            "liquidity_multiplier": 1.0
        },
        "crash_scenario": {
            "price_trend": "crash",
            "volatility_multiplier": 3.0,
            "liquidity_multiplier": 0.3
        }
    }


class TestDataGenerator:
    """Utility class for generating test data"""

    @staticmethod
    def generate_price_history(asset_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Generate mock price history data"""
        base_price = 0.25 if asset_id == "0" else 1.00
        prices = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            # Add some random variation
            import random
            variation = random.uniform(-0.1, 0.1)
            price = base_price * (1 + variation)

            prices.append({
                "timestamp": date.isoformat(),
                "price": price,
                "volume": random.uniform(1000000, 10000000)
            })

        return prices

    @staticmethod
    def generate_portfolio_data(num_assets: int = 5) -> Dict[str, Any]:
        """Generate mock portfolio data"""
        import random

        assets = ["0", "31566704", "312769", "27165954", "386192725"][:num_assets]
        portfolio = {
            "total_value": 0.0,
            "positions": []
        }

        for asset_id in assets:
            quantity = random.uniform(1000, 100000)
            price = 0.25 if asset_id == "0" else 1.00
            value = quantity * price

            portfolio["positions"].append({
                "asset_id": asset_id,
                "quantity": quantity,
                "price": price,
                "value": value,
                "weight": 0.0  # Will be calculated
            })
            portfolio["total_value"] += value

        # Calculate weights
        for position in portfolio["positions"]:
            position["weight"] = position["value"] / portfolio["total_value"]

        return portfolio


@pytest.fixture
def test_data_generator():
    """Provide test data generator instance"""
    return TestDataGenerator()


# Async context manager for temporary MCP service simulation
class MockMCPContext:
    """Context manager for mock MCP services"""

    def __init__(self, reader_port: int = 8002, writer_port: int = 8003):
        self.reader_port = reader_port
        self.writer_port = writer_port
        self.reader_service = None
        self.writer_service = None

    async def __aenter__(self):
        self.reader_service = MockMCPService(self.reader_port)
        self.writer_service = MockMCPService(self.writer_port)

        self.reader_service.start()
        self.writer_service.start()

        return {
            "reader": self.reader_service,
            "writer": self.writer_service
        }

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.reader_service:
            self.reader_service.stop()
        if self.writer_service:
            self.writer_service.stop()


@pytest.fixture
async def mcp_context():
    """Provide MCP context manager"""
    return MockMCPContext()


# Helper functions for integration tests
def assert_engine_health(engine, engine_name: str):
    """Assert that an engine is healthy and properly initialized"""
    assert engine is not None, f"{engine_name} engine should not be None"
    assert hasattr(engine, "is_initialized"), f"{engine_name} should have is_initialized attribute"
    # Note: We'll check this in the actual test since it might be async


async def assert_mcp_connectivity(engine, engine_name: str):
    """Assert that an engine can connect to MCP services"""
    try:
        # Most engines should have a health check method
        if hasattr(engine, "health_check"):
            health = await engine.health_check()
            assert health["status"] == "healthy", f"{engine_name} health check failed"
    except Exception as e:
        pytest.fail(f"{engine_name} MCP connectivity check failed: {str(e)}")


def create_test_loan_request(amount: float = 50000.0, collateral_assets: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a test loan request"""
    if collateral_assets is None:
        collateral_assets = ["0", "31566704"]

    return {
        "loan_id": f"test_loan_{int(time.time())}",
        "amount": amount,
        "currency": "USD",
        "collateral_assets": collateral_assets,
        "borrower_id": "test_borrower",
        "term_days": 30,
        "timestamp": datetime.now().isoformat()
    }


# Performance monitoring utilities
class PerformanceMonitor:
    """Utility for monitoring test performance"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = {}

    def start(self):
        """Start performance monitoring"""
        self.start_time = time.time()

    def stop(self):
        """Stop performance monitoring"""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Get execution duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def check_memory_usage(self):
        """Check current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0  # psutil not available


@pytest.fixture
def performance_monitor():
    """Provide performance monitor instance"""
    return PerformanceMonitor()