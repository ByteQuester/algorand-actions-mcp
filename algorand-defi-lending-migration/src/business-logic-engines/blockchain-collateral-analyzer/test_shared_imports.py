#!/usr/bin/env python3
"""
Test Shared Imports
Quick test to verify that all engines can import from the new common modules.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_common_imports():
    """Test that common modules can be imported"""
    print("Testing common module imports...")

    try:
        # Test models import
        from common.models.blockchain_collateral_models import (
            DigitalCollateralType, DigitalAsset, CollateralPosition,
            CollateralPortfolio, LiquidationScenario, CollateralAnalysisResult
        )
        print("✓ Models import successful")

        # Test utils import
        from common.utils.calculations import (
            calculate_asset_haircut, calculate_portfolio_diversification,
            calculate_portfolio_var
        )
        from common.utils.validation import (
            validate_positive_number, validate_percentage, ValidationError
        )
        print("✓ Utils import successful")

        # Test database import
        from common.database.storage import (
            CollateralDatabase, CacheManager, DatabaseError
        )
        print("✓ Database import successful")

        # Test MCP import
        from common.mcp.client import (
            MCPClient, MCPServiceManager, MCPError
        )
        print("✓ MCP client import successful")

        # Test common module root import
        from common import (
            DigitalCollateralType, calculate_asset_haircut,
            CollateralDatabase, MCPClient
        )
        print("✓ Common root import successful")

        return True

    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_engine_imports():
    """Test that engines can import from common modules"""
    print("\nTesting engine imports...")

    try:
        # Test liquidation scenarios engine
        from liquidation_scenarios.core.liquidation_scenarios_engine import LiquidationScenariosEngine
        print("✓ Liquidation scenarios engine import successful")

        # Test digital asset valuation engine
        from digital_asset_valuation.core.engine import DigitalAssetValuationEngine
        print("✓ Digital asset valuation engine import successful")

        # Test collateral requirements engine
        from collateral_requirements.core.collateral_engine import CollateralRequirementsEngine
        print("✓ Collateral requirements engine import successful")

        return True

    except Exception as e:
        print(f"✗ Engine import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_functionality():
    """Test basic functionality with shared modules"""
    print("\nTesting basic functionality...")

    try:
        from common.models.blockchain_collateral_models import (
            DigitalCollateralType, VolatilityMetrics, LiquidityMetrics,
            PriceOracle, DigitalAsset
        )
        from common.utils.calculations import calculate_asset_haircut
        from common.utils.validation import validate_positive_number

        # Create test data
        volatility_metrics = VolatilityMetrics(
            volatility_30d=0.15,
            volatility_7d=0.20,
            max_drawdown_30d=0.25,
            value_at_risk_95=0.10,
            correlation_with_algo=0.8,
            stress_test_scenarios={"severe": 0.35, "extreme": 0.50}
        )

        liquidity_metrics = LiquidityMetrics(
            daily_volume_usd=1000000.0,
            market_cap_usd=50000000.0,
            depth_1_percent=100000.0,
            largest_liquidation_size=500000.0,
            average_spread_bps=10.0,
            liquidity_tier="high"
        )

        price_oracle = PriceOracle(
            primary_oracle="coinbase",
            backup_oracles=["binance", "kraken"],
            update_frequency=30,
            reliability_score=0.95,
            price_deviation_threshold=0.02,
            fallback_mechanism="median_price"
        )

        # Create test asset
        test_asset = DigitalAsset(
            asset_id="algo_001",
            symbol="ALGO",
            name="Algorand",
            asset_type=DigitalCollateralType.ALGO_NATIVE,
            volatility_metrics=volatility_metrics,
            liquidity_metrics=liquidity_metrics,
            price_oracle=price_oracle,
            base_collateral_ratio=1.5,
            maintenance_ratio=1.3,
            liquidation_penalty=0.05
        )

        # Test calculations
        haircut = calculate_asset_haircut(test_asset, "normal")
        print(f"✓ Calculated asset haircut: {haircut:.3f}")

        # Test validation
        validate_positive_number(100.0, "test_value")
        print("✓ Validation successful")

        return True

    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("BLOCKCHAIN COLLATERAL ANALYZER - SHARED IMPORTS TEST")
    print("=" * 60)

    # Run tests
    common_success = test_common_imports()
    engine_success = test_engine_imports()
    functionality_success = test_basic_functionality()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Common imports: {'✓ PASS' if common_success else '✗ FAIL'}")
    print(f"Engine imports: {'✓ PASS' if engine_success else '✗ FAIL'}")
    print(f"Basic functionality: {'✓ PASS' if functionality_success else '✗ FAIL'}")

    overall_success = common_success and engine_success and functionality_success
    print(f"\nOverall result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")

    if overall_success:
        print("\n🎉 Shared module structure is working correctly!")
        print("All engines can now use common models, utilities, database, and MCP clients.")
    else:
        print("\n❌ There are issues with the shared module structure.")
        print("Please check the errors above and fix the import issues.")

    sys.exit(0 if overall_success else 1)