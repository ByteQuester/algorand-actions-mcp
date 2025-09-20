#!/usr/bin/env python3
"""
Vendoring Simulation Test for Algorand Lending Business Logic package.
Tests that the package can be vendored and used in external environments.
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
import traceback

class VendoringTest:
    """Test suite for vendoring simulation."""

    def __init__(self):
        self.test_results = {}
        self.original_dir = os.getcwd()
        self.temp_dir = None

    def setup_test_environment(self) -> bool:
        """Set up temporary test environment."""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="algorand_lending_vendor_test_")
            print(f"✅ Created test environment: {self.temp_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to create test environment: {e}")
            return False

    def simulate_package_copy(self) -> bool:
        """Simulate copying the package to a vendor directory."""
        try:
            # Create vendor structure
            vendor_dir = Path(self.temp_dir) / "vendor" / "algorand-lending-bl"
            vendor_dir.mkdir(parents=True, exist_ok=True)

            # Copy package files
            source_package = Path(self.original_dir) / "algorand_lending_bl"
            target_package = vendor_dir / "algorand_lending_bl"

            if source_package.exists():
                shutil.copytree(source_package, target_package)
                print(f"✅ Package copied to vendor directory")
            else:
                print(f"❌ Source package not found: {source_package}")
                return False

            # Copy essential files
            essential_files = [
                "requirements.txt",
                "setup.py",
                "pyproject.toml",
                "README.md"
            ]

            for file_name in essential_files:
                source_file = Path(self.original_dir) / file_name
                if source_file.exists():
                    target_file = vendor_dir / file_name
                    shutil.copy2(source_file, target_file)
                    print(f"  ✅ Copied {file_name}")
                else:
                    print(f"  ⚠️ Optional file not found: {file_name}")

            return True

        except Exception as e:
            print(f"❌ Failed to copy package: {e}")
            return False

    def test_minimal_import(self) -> bool:
        """Test minimal import from vendored location."""
        try:
            vendor_dir = Path(self.temp_dir) / "vendor" / "algorand-lending-bl"

            # Create minimal test script
            test_script = vendor_dir / "test_minimal_import.py"
            test_script.write_text("""
import sys
import os

# Add vendor package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test basic imports
    from algorand_lending_bl import CollateralAnalyzer, InterestRateEngine
    print("✅ Basic imports successful")

    # Test instantiation
    analyzer = CollateralAnalyzer()
    engine = InterestRateEngine()
    print("✅ Engine instantiation successful")

    # Test basic functionality
    from algorand_lending_bl import create_lending_engines
    ca, ire = create_lending_engines()
    print("✅ Convenience function works")

    print("SUCCESS: Minimal vendoring test passed")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
""")

            # Run the test script
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(vendor_dir),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Minimal import test passed")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print("❌ Minimal import test failed")
                print(f"  Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Minimal import test failed: {e}")
            return False

    def test_functionality_from_vendor(self) -> bool:
        """Test actual functionality from vendored package."""
        try:
            vendor_dir = Path(self.temp_dir) / "vendor" / "algorand-lending-bl"

            # Create functional test script
            test_script = vendor_dir / "test_vendor_functionality.py"
            test_script.write_text("""
import sys
import os
import asyncio
from decimal import Decimal

# Add vendor package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_functionality():
    try:
        from algorand_lending_bl import (
            CollateralAnalyzer,
            InterestRateEngine,
            ASAToken,
            AlgorandAddress,
            create_lending_engines
        )

        print("✅ All imports successful")

        # Create test data
        algo_token = ASAToken(
            asset_id="0",
            symbol="ALGO",
            name="Algorand",
            decimals=6,
            total_supply=Decimal("10000000000"),
            circulating_supply=Decimal("8000000000"),
            creator_address="ALGORAND"
        )

        borrower = AlgorandAddress(
            address="VENDOR_TEST_BORROWER_123456789012345678901234567890123456789",
            is_valid=True
        )

        print("✅ Test data created")

        # Test engines
        analyzer, engine = create_lending_engines()

        # Test collateral analysis
        analysis = await analyzer.analyze_collateral(
            assets=[algo_token],
            quantities=[Decimal("10000")],
            loan_amount_usd=Decimal("2000")
        )

        assert analysis.total_collateral_value > 0
        print(f"✅ Collateral analysis: ${analysis.total_collateral_value:.2f}")

        # Test rate calculation
        rate_calc = await engine.calculate_rate(
            borrower=borrower,
            loan_amount_usd=Decimal("2000"),
            loan_duration_days=90,
            collateral_assets=["ALGO"],
            collateral_value_usd=analysis.total_adjusted_value
        )

        assert rate_calc.final_interest_rate > 0
        print(f"✅ Rate calculation: {rate_calc.final_interest_rate:.4f}")

        print("SUCCESS: Vendor functionality test passed")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_functionality())
    sys.exit(0 if result else 1)
""")

            # Run the test script
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(vendor_dir),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✅ Vendor functionality test passed")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print("❌ Vendor functionality test failed")
                print(f"  Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Vendor functionality test failed: {e}")
            return False

    def test_isolation(self) -> bool:
        """Test that vendored package is isolated from original."""
        try:
            vendor_dir = Path(self.temp_dir) / "vendor" / "algorand-lending-bl"

            # Create isolation test script
            test_script = vendor_dir / "test_isolation.py"
            test_script.write_text("""
import sys
import os

# Only add vendor package to path, not original
vendor_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, vendor_path)

# Remove any references to original package location
original_paths_to_remove = []
for path in sys.path:
    if 'algorand-lending-ecosystem' in path and path != vendor_path:
        original_paths_to_remove.append(path)

for path in original_paths_to_remove:
    sys.path.remove(path)

try:
    from algorand_lending_bl import __version__, VENDOR_INFO

    print(f"✅ Package version: {__version__}")
    print(f"✅ Vendor info accessible: {VENDOR_INFO['name']}")

    # Verify we're importing from vendor location
    import algorand_lending_bl
    package_path = os.path.dirname(algorand_lending_bl.__file__)

    if vendor_path in package_path:
        print(f"✅ Importing from vendor location: {package_path}")
        print("SUCCESS: Isolation test passed")
    else:
        print(f"❌ Not importing from vendor location: {package_path}")
        print("FAILED: Isolation test failed")
        sys.exit(1)

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
""")

            # Run the test script
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(vendor_dir),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Isolation test passed")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print("❌ Isolation test failed")
                print(f"  Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Isolation test failed: {e}")
            return False

    def test_configuration_override(self) -> bool:
        """Test that configuration can be overridden in vendored environment."""
        try:
            vendor_dir = Path(self.temp_dir) / "vendor" / "algorand-lending-bl"

            # Create configuration override test
            test_script = vendor_dir / "test_config_override.py"
            test_script.write_text("""
import sys
import os

# Add vendor package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from algorand_lending_bl import CollateralConfig, InterestRateConfig

    # Test default config
    default_collateral_config = CollateralConfig.from_env()
    default_rate_config = InterestRateConfig.from_env()

    print("✅ Default configs created")

    # Test custom config creation
    custom_collateral_config = CollateralConfig(
        min_collateral_ratio=1.5,
        liquidation_threshold=1.2,
        safety_margin=0.1
    )

    custom_rate_config = InterestRateConfig(
        base_rate=0.05,
        risk_premium_multiplier=2.0,
        max_rate=0.30
    )

    print("✅ Custom configs created")
    print(f"  Custom collateral ratio: {custom_collateral_config.min_collateral_ratio}")
    print(f"  Custom base rate: {custom_rate_config.base_rate}")

    # Test that configs can be used with engines
    from algorand_lending_bl import CollateralAnalyzer, InterestRateEngine

    analyzer = CollateralAnalyzer(custom_collateral_config)
    engine = InterestRateEngine(custom_rate_config)

    print("✅ Engines created with custom configs")
    print("SUCCESS: Configuration override test passed")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
""")

            # Run the test script
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(vendor_dir),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Configuration override test passed")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print("❌ Configuration override test failed")
                print(f"  Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Configuration override test failed: {e}")
            return False

    def test_dependency_handling(self) -> bool:
        """Test dependency handling in vendored environment."""
        try:
            vendor_dir = Path(self.temp_dir) / "vendor" / "algorand-lending-bl"

            # Create dependency test script
            test_script = vendor_dir / "test_dependencies.py"
            test_script.write_text("""
import sys
import os

# Add vendor package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test that all required dependencies are available
    import decimal
    import asyncio
    import typing
    import datetime
    import enum
    print("✅ Standard library dependencies available")

    # Test optional dependencies
    optional_deps = []

    try:
        import yaml
        optional_deps.append("yaml")
    except ImportError:
        print("ℹ️ yaml not available (optional)")

    try:
        import httpx
        optional_deps.append("httpx")
    except ImportError:
        print("ℹ️ httpx not available (optional)")

    if optional_deps:
        print(f"✅ Optional dependencies available: {', '.join(optional_deps)}")

    # Test package imports with minimal dependencies
    from algorand_lending_bl import CollateralAnalyzer, InterestRateEngine
    print("✅ Package imports work with available dependencies")

    print("SUCCESS: Dependency handling test passed")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
""")

            # Run the test script
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=str(vendor_dir),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print("✅ Dependency handling test passed")
                print(f"  Output: {result.stdout.strip()}")
                return True
            else:
                print("❌ Dependency handling test failed")
                print(f"  Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Dependency handling test failed: {e}")
            return False

    def cleanup(self) -> bool:
        """Clean up test environment."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"✅ Cleaned up test environment")
            return True
        except Exception as e:
            print(f"⚠️ Failed to clean up test environment: {e}")
            return False

    def run_vendoring_tests(self) -> bool:
        """Run all vendoring tests."""
        print("📦 Starting Algorand Lending Business Logic Vendoring Tests")
        print("=" * 65)

        # Setup
        if not self.setup_test_environment():
            return False

        # Run tests
        test_functions = [
            ("Package Copy Simulation", self.simulate_package_copy),
            ("Minimal Import Test", self.test_minimal_import),
            ("Functionality from Vendor", self.test_functionality_from_vendor),
            ("Isolation Test", self.test_isolation),
            ("Configuration Override", self.test_configuration_override),
            ("Dependency Handling", self.test_dependency_handling)
        ]

        results = {}

        for test_name, test_func in test_functions:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 40)

            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"  {status}")
            except Exception as e:
                results[test_name] = False
                print(f"  ❌ FAILED with exception: {e}")
                print(f"  Traceback: {traceback.format_exc()}")

        # Cleanup
        self.cleanup()

        # Results
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)

        print("\n" + "=" * 65)
        print("VENDORING TEST RESULTS")
        print("=" * 65)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")

        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("\n🎉 ALL VENDORING TESTS PASSED!")
            print("✅ Package can be successfully vendored")
            print("✅ Works in isolated environments")
            print("✅ Configuration can be customized")
            print("✅ Dependencies are properly handled")
            print("✅ Ready for external distribution")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed")
            print("❌ Vendoring issues need to be resolved")
            return False

def main():
    """Run vendoring tests."""
    test_runner = VendoringTest()
    return test_runner.run_vendoring_tests()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)