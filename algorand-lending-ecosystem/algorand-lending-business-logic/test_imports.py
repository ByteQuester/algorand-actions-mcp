#!/usr/bin/env python3
"""
Import Validation Test for Algorand Lending Business Logic package.
Verifies that all modules import correctly and classes can be instantiated.
"""

import sys
import traceback
from typing import List, Tuple, Any

def test_basic_imports() -> Tuple[bool, List[str]]:
    """Test basic package imports."""
    results = []
    success = True

    try:
        # Test main package import
        import algorand_lending_bl
        results.append("✅ algorand_lending_bl package imported successfully")

        # Test version
        version = getattr(algorand_lending_bl, '__version__', None)
        if version:
            results.append(f"✅ Package version: {version}")
        else:
            results.append("⚠️ Package version not found")

    except Exception as e:
        results.append(f"❌ Failed to import algorand_lending_bl: {e}")
        success = False

    return success, results

def test_core_engines() -> Tuple[bool, List[str]]:
    """Test core engine imports."""
    results = []
    success = True

    try:
        from algorand_lending_bl import CollateralAnalyzer, InterestRateEngine
        results.append("✅ Core engines (CollateralAnalyzer, InterestRateEngine) imported")

        # Test instantiation
        collateral_analyzer = CollateralAnalyzer()
        results.append("✅ CollateralAnalyzer instantiated")

        interest_rate_engine = InterestRateEngine()
        results.append("✅ InterestRateEngine instantiated")

    except Exception as e:
        results.append(f"❌ Failed to import/instantiate core engines: {e}")
        success = False

    return success, results

def test_model_imports() -> Tuple[bool, List[str]]:
    """Test model imports."""
    results = []
    success = True

    # Collateral models
    try:
        from algorand_lending_bl import (
            CollateralAnalysis,
            AssetValuation,
            LiquidationScenario,
            PortfolioRisk,
            ASAToken,
            AssetType,
            LiquidityTier,
            CollateralRiskLevel,
            CollateralPosition
        )
        results.append("✅ Collateral models imported successfully")

        # Test enum access
        asset_type = AssetType.ALGO_NATIVE
        liquidity_tier = LiquidityTier.HIGH
        risk_level = CollateralRiskLevel.LOW
        results.append(f"✅ Enum values accessible: {asset_type.value}, {liquidity_tier.value}, {risk_level.value}")

    except Exception as e:
        results.append(f"❌ Failed to import collateral models: {e}")
        success = False

    # Interest rate models
    try:
        from algorand_lending_bl import (
            RateCalculation,
            RateFactors,
            StakingMetrics,
            DeFiYieldData,
            ReputationScore,
            ASARiskMetrics,
            NetworkMetrics,
            LiquidityMetrics,
            AlgorandAddress,
            RiskTier
        )
        results.append("✅ Interest rate models imported successfully")

        # Test enum access with correct value
        risk_tier = RiskTier.STANDARD
        results.append(f"✅ RiskTier enum accessible: {risk_tier.value}")

    except Exception as e:
        results.append(f"❌ Failed to import interest rate models: {e}")
        success = False

    return success, results

def test_config_imports() -> Tuple[bool, List[str]]:
    """Test configuration imports."""
    results = []
    success = True

    try:
        from algorand_lending_bl import CollateralConfig, InterestRateConfig
        results.append("✅ Configuration classes imported")

        # Test config creation
        collateral_config = CollateralConfig.from_env()
        interest_rate_config = InterestRateConfig.from_env()
        results.append("✅ Configuration objects created from environment")

    except Exception as e:
        results.append(f"❌ Failed to import/create configurations: {e}")
        success = False

    return success, results

def test_service_import() -> Tuple[bool, List[str]]:
    """Test service layer imports."""
    results = []
    success = True

    try:
        from algorand_lending_bl import AlgorandLendingService
        results.append("✅ AlgorandLendingService imported successfully")

        # Test service instantiation
        service = AlgorandLendingService()
        results.append("✅ AlgorandLendingService instantiated")

    except Exception as e:
        results.append(f"❌ Failed to import/instantiate service: {e}")
        success = False

    return success, results

def test_convenience_functions() -> Tuple[bool, List[str]]:
    """Test convenience functions."""
    results = []
    success = True

    try:
        from algorand_lending_bl import create_lending_engines
        results.append("✅ create_lending_engines function imported")

        # Test function call
        collateral_analyzer, interest_rate_engine = create_lending_engines()
        results.append("✅ create_lending_engines executed successfully")

        # Verify types
        from algorand_lending_bl import CollateralAnalyzer, InterestRateEngine
        assert isinstance(collateral_analyzer, CollateralAnalyzer)
        assert isinstance(interest_rate_engine, InterestRateEngine)
        results.append("✅ Returned objects are correct types")

    except Exception as e:
        results.append(f"❌ Failed to test convenience functions: {e}")
        success = False

    return success, results

def test_model_instantiation() -> Tuple[bool, List[str]]:
    """Test that models can be instantiated with valid data."""
    results = []
    success = True

    try:
        from decimal import Decimal
        from algorand_lending_bl import ASAToken, AlgorandAddress

        # Test ASAToken creation
        algo_token = ASAToken(
            asset_id="0",
            symbol="ALGO",
            name="Algorand",
            decimals=6,
            total_supply=Decimal("10000000000"),
            circulating_supply=Decimal("8000000000"),
            creator_address="ALGORAND_FOUNDATION"
        )
        results.append("✅ ASAToken instantiated successfully")

        # Test AlgorandAddress creation
        address = AlgorandAddress(
            address="TEST_ADDRESS_123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            is_valid=True
        )
        results.append("✅ AlgorandAddress instantiated successfully")

        # Test accessing attributes
        assert algo_token.symbol == "ALGO"
        assert address.is_valid == True
        results.append("✅ Model attributes accessible")

    except Exception as e:
        results.append(f"❌ Failed to instantiate models: {e}")
        results.append(f"   Traceback: {traceback.format_exc()}")
        success = False

    return success, results

def main():
    """Run all import tests."""
    print("Algorand Lending Business Logic - Import Validation Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print("=" * 60)

    test_functions = [
        ("Basic Imports", test_basic_imports),
        ("Core Engines", test_core_engines),
        ("Model Imports", test_model_imports),
        ("Configuration", test_config_imports),
        ("Service Layer", test_service_import),
        ("Convenience Functions", test_convenience_functions),
        ("Model Instantiation", test_model_instantiation),
    ]

    all_results = []
    total_tests = len(test_functions)
    passed_tests = 0

    for test_name, test_func in test_functions:
        print(f"\n{'-' * 40}")
        print(f"Testing: {test_name}")
        print(f"{'-' * 40}")

        try:
            success, results = test_func()
            if success:
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")

            for result in results:
                print(f"  {result}")

            all_results.extend(results)

        except Exception as e:
            print(f"❌ {test_name}: FAILED with exception: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

    # Summary
    print("\n" + "=" * 60)
    print("IMPORT TEST SUMMARY")
    print("=" * 60)
    print(f"Tests: {passed_tests}/{total_tests} passed")

    if passed_tests == total_tests:
        print("🎉 ALL IMPORT TESTS PASSED!")
        print("✅ Package is properly structured and all imports work")
        print("✅ Ready for usage and vendoring")
    else:
        print(f"⚠️ {total_tests - passed_tests} tests failed")
        print("❌ Package has import issues that need to be resolved")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)