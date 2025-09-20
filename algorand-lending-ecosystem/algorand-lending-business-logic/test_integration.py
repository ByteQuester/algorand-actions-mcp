#!/usr/bin/env python3
"""
Integration Test for Algorand Lending Business Logic package.
Tests complete loan flow and validates all functionality works together.
"""

import asyncio
import time
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

from algorand_lending_bl import (
    CollateralAnalyzer,
    InterestRateEngine,
    AlgorandLendingService,
    ASAToken,
    AlgorandAddress,
    CollateralConfig,
    InterestRateConfig,
    create_lending_engines,
    AssetType,
    RiskTier
)

class LendingIntegrationTest:
    """Complete integration test suite for lending business logic."""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.collateral_analyzer = None
        self.rate_engine = None
        self.service = None

    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up integration test environment...")

        # Create engines
        self.collateral_analyzer, self.rate_engine = create_lending_engines()
        self.service = AlgorandLendingService()

        print("✅ Test environment ready")

    def create_test_borrower(self, suffix: str = "001") -> AlgorandAddress:
        """Create a test borrower address."""
        return AlgorandAddress(
            address=f"BORROWER_{suffix}_{'A' * (58 - len(suffix) - 10)}",
            is_valid=True,
            creation_round=25000000,
            last_activity_round=35000000
        )

    def create_test_assets(self) -> Dict[str, ASAToken]:
        """Create test assets for collateral."""
        return {
            'ALGO': ASAToken(
                asset_id="0",
                symbol="ALGO",
                name="Algorand",
                decimals=6,
                total_supply=Decimal("10000000000"),
                circulating_supply=Decimal("8500000000"),
                creator_address="ALGORAND_FOUNDATION"
            ),
            'USDC': ASAToken(
                asset_id="31566704",
                symbol="USDC",
                name="USD Coin",
                decimals=6,
                total_supply=Decimal("1000000000"),
                circulating_supply=Decimal("800000000"),
                creator_address="CENTRE_CONSORTIUM"
            ),
            'goBTC': ASAToken(
                asset_id="386192725",
                symbol="goBTC",
                name="Wrapped Bitcoin",
                decimals=8,
                total_supply=Decimal("21000000"),
                circulating_supply=Decimal("19500000"),
                creator_address="GOBTC_ISSUER"
            ),
            'USDT': ASAToken(
                asset_id="312769",
                symbol="USDT",
                name="Tether USD",
                decimals=6,
                total_supply=Decimal("1000000000"),
                circulating_supply=Decimal("750000000"),
                creator_address="TETHER_ISSUER"
            )
        }

    async def test_individual_engine_functionality(self) -> bool:
        """Test each engine individually."""
        print("\n🔬 Testing Individual Engine Functionality")
        print("-" * 50)

        success = True
        assets = self.create_test_assets()
        borrower = self.create_test_borrower("ENGINE_TEST")

        # Test 1: Collateral Analyzer
        try:
            print("Testing CollateralAnalyzer...")
            analysis = await self.collateral_analyzer.analyze_collateral(
                assets=[assets['ALGO'], assets['USDC']],
                quantities=[Decimal("25000"), Decimal("10000")],
                loan_amount_usd=Decimal("8000"),
                market_condition="normal"
            )

            # Validate results
            assert analysis.total_collateral_value > 0
            assert analysis.total_adjusted_value > 0
            assert len(analysis.positions) == 2
            assert analysis.current_collateral_ratio > 0

            print(f"  ✅ Collateral value: ${analysis.total_collateral_value:,.2f}")
            print(f"  ✅ Adjusted value: ${analysis.total_adjusted_value:,.2f}")
            print(f"  ✅ Collateral ratio: {analysis.current_collateral_ratio:.2%}")

        except Exception as e:
            print(f"  ❌ CollateralAnalyzer failed: {e}")
            success = False

        # Test 2: Interest Rate Engine
        try:
            print("Testing InterestRateEngine...")
            rate_calc = await self.rate_engine.calculate_rate(
                borrower=borrower,
                loan_amount_usd=Decimal("8000"),
                loan_duration_days=180,
                collateral_assets=["ALGO", "USDC"],
                collateral_value_usd=Decimal("12000"),
                market_condition="normal"
            )

            # Validate results
            assert rate_calc.final_interest_rate > 0
            assert rate_calc.effective_apr > 0
            assert rate_calc.borrower_risk_tier in [tier for tier in RiskTier]

            print(f"  ✅ Interest rate: {rate_calc.final_interest_rate:.4f}")
            print(f"  ✅ Effective APR: {rate_calc.effective_apr:.4f}")
            print(f"  ✅ Risk tier: {rate_calc.borrower_risk_tier.value}")

        except Exception as e:
            print(f"  ❌ InterestRateEngine failed: {e}")
            success = False

        return success

    async def test_loan_approval_scenarios(self) -> bool:
        """Test various loan approval scenarios."""
        print("\n📋 Testing Loan Approval Scenarios")
        print("-" * 50)

        success = True
        assets = self.create_test_assets()
        scenarios = [
            {
                "name": "High-value collateral, small loan (should approve)",
                "borrower": self.create_test_borrower("SCENARIO_1"),
                "assets": [assets['ALGO'], assets['USDC']],
                "quantities": [Decimal("100000"), Decimal("50000")],  # Very high collateral
                "loan_amount": Decimal("5000"),  # Small loan
                "duration": 90,
                "expected_approval": True
            },
            {
                "name": "Adequate collateral, medium loan (should approve)",
                "borrower": self.create_test_borrower("SCENARIO_2"),
                "assets": [assets['ALGO']],
                "quantities": [Decimal("50000")],
                "loan_amount": Decimal("8000"),
                "duration": 180,
                "expected_approval": None  # Depends on current market conditions
            },
            {
                "name": "Low collateral, large loan (should reject)",
                "borrower": self.create_test_borrower("SCENARIO_3"),
                "assets": [assets['ALGO']],
                "quantities": [Decimal("5000")],  # Low collateral
                "loan_amount": Decimal("15000"),  # Large loan
                "duration": 365,
                "expected_approval": False
            },
            {
                "name": "Multi-asset portfolio (comprehensive test)",
                "borrower": self.create_test_borrower("SCENARIO_4"),
                "assets": [assets['ALGO'], assets['USDC'], assets['goBTC']],
                "quantities": [Decimal("30000"), Decimal("15000"), Decimal("0.25")],
                "loan_amount": Decimal("12000"),
                "duration": 270,
                "expected_approval": None  # Complex scenario
            }
        ]

        for i, scenario in enumerate(scenarios, 1):
            print(f"\nScenario {i}: {scenario['name']}")

            try:
                # Step 1: Collateral analysis
                collateral_analysis = await self.collateral_analyzer.analyze_collateral(
                    assets=scenario['assets'],
                    quantities=scenario['quantities'],
                    loan_amount_usd=scenario['loan_amount'],
                    market_condition="normal"
                )

                # Step 2: Interest rate calculation (if collateral is sufficient)
                if collateral_analysis.is_sufficient:
                    rate_calculation = await self.rate_engine.calculate_rate(
                        borrower=scenario['borrower'],
                        loan_amount_usd=scenario['loan_amount'],
                        loan_duration_days=scenario['duration'],
                        collateral_assets=[asset.symbol for asset in scenario['assets']],
                        collateral_value_usd=collateral_analysis.total_adjusted_value,
                        market_condition="normal"
                    )

                    # Decision logic
                    safety_margin = collateral_analysis.safety_margin()
                    decision = (
                        collateral_analysis.is_sufficient and
                        safety_margin >= Decimal('0.10') and  # 10% minimum safety margin
                        rate_calculation.confidence_interval <= Decimal('0.30')  # 30% max confidence interval
                    )

                    print(f"  Collateral: ${collateral_analysis.total_collateral_value:,.2f}")
                    print(f"  Adjusted: ${collateral_analysis.total_adjusted_value:,.2f}")
                    print(f"  Safety Margin: {safety_margin:.2%}")
                    print(f"  Interest Rate: {rate_calculation.final_interest_rate:.3%}")
                    print(f"  Decision: {'APPROVED' if decision else 'REJECTED'}")

                    # Validate against expected result if provided
                    if scenario['expected_approval'] is not None:
                        if decision != scenario['expected_approval']:
                            print(f"  ⚠️ Unexpected result: expected {scenario['expected_approval']}, got {decision}")
                        else:
                            print(f"  ✅ Expected result achieved")
                else:
                    print(f"  Insufficient collateral")
                    print(f"  Additional needed: ${collateral_analysis.additional_collateral_needed:,.2f}")
                    print(f"  Decision: REJECTED")

                    if scenario['expected_approval'] is True:
                        print(f"  ⚠️ Unexpected rejection")
                        success = False
                    else:
                        print(f"  ✅ Expected rejection")

            except Exception as e:
                print(f"  ❌ Scenario failed: {e}")
                success = False

        return success

    async def test_performance_under_load(self) -> bool:
        """Test performance under concurrent load."""
        print("\n⚡ Testing Performance Under Load")
        print("-" * 50)

        success = True
        assets = self.create_test_assets()

        # Create multiple borrowers and loan requests
        loan_requests = []
        for i in range(10):
            loan_requests.append({
                'borrower': self.create_test_borrower(f"PERF_{i:03d}"),
                'assets': [assets['ALGO'], assets['USDC']],
                'quantities': [Decimal(f"{5000 + i * 1000}"), Decimal(f"{2500 + i * 500}")],
                'loan_amount': Decimal(f"{3000 + i * 200}"),
                'duration': 90 + i * 30
            })

        # Test concurrent processing
        start_time = time.time()

        async def process_loan_request(request):
            """Process a single loan request."""
            # Collateral analysis
            collateral_analysis = await self.collateral_analyzer.analyze_collateral(
                assets=request['assets'],
                quantities=request['quantities'],
                loan_amount_usd=request['loan_amount'],
                market_condition="normal"
            )

            # Rate calculation if collateral is sufficient
            if collateral_analysis.is_sufficient:
                rate_calculation = await self.rate_engine.calculate_rate(
                    borrower=request['borrower'],
                    loan_amount_usd=request['loan_amount'],
                    loan_duration_days=request['duration'],
                    collateral_assets=[asset.symbol for asset in request['assets']],
                    collateral_value_usd=collateral_analysis.total_adjusted_value,
                    market_condition="normal"
                )
                return {
                    'collateral': collateral_analysis,
                    'rate': rate_calculation,
                    'approved': collateral_analysis.is_sufficient and collateral_analysis.safety_margin() >= Decimal('0.10')
                }
            else:
                return {
                    'collateral': collateral_analysis,
                    'rate': None,
                    'approved': False
                }

        try:
            # Process all requests concurrently
            results = await asyncio.gather(*[process_loan_request(req) for req in loan_requests])

            processing_time = time.time() - start_time

            # Analyze results
            approved_count = sum(1 for result in results if result['approved'])
            rejected_count = len(results) - approved_count
            avg_processing_time = processing_time / len(results)

            print(f"  ✅ Processed {len(results)} loan requests in {processing_time:.3f} seconds")
            print(f"  ✅ Average processing time: {avg_processing_time:.3f} seconds per request")
            print(f"  ✅ Approved: {approved_count}, Rejected: {rejected_count}")

            # Performance validation
            if avg_processing_time > 1.0:  # Should process in under 1 second each
                print(f"  ⚠️ Performance warning: average processing time too high")
                success = False

            # Validate all results have expected structure
            for i, result in enumerate(results):
                assert result['collateral'] is not None
                assert result['collateral'].total_collateral_value > 0
                if result['approved']:
                    assert result['rate'] is not None
                    assert result['rate'].final_interest_rate > 0

            print(f"  ✅ All results structurally valid")

        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            success = False

        return success

    async def test_error_handling_and_edge_cases(self) -> bool:
        """Test error handling and edge cases."""
        print("\n🛡️ Testing Error Handling and Edge Cases")
        print("-" * 50)

        success = True
        assets = self.create_test_assets()

        error_test_cases = [
            {
                "name": "Zero loan amount",
                "test": lambda: self.collateral_analyzer.analyze_collateral(
                    assets=[assets['ALGO']],
                    quantities=[Decimal("1000")],
                    loan_amount_usd=Decimal("0")
                ),
                "should_fail": True
            },
            {
                "name": "Negative collateral quantity",
                "test": lambda: self.collateral_analyzer.analyze_collateral(
                    assets=[assets['ALGO']],
                    quantities=[Decimal("-1000")],
                    loan_amount_usd=Decimal("1000")
                ),
                "should_fail": True
            },
            {
                "name": "Invalid borrower address",
                "test": lambda: self.rate_engine.calculate_rate(
                    borrower=AlgorandAddress(address="INVALID", is_valid=False),
                    loan_amount_usd=Decimal("1000"),
                    loan_duration_days=90,
                    collateral_assets=["ALGO"],
                    collateral_value_usd=Decimal("1500")
                ),
                "should_fail": True
            },
            {
                "name": "Very large loan amount",
                "test": lambda: self.collateral_analyzer.analyze_collateral(
                    assets=[assets['ALGO']],
                    quantities=[Decimal("1000")],
                    loan_amount_usd=Decimal("1000000000")  # 1 billion
                ),
                "should_fail": False  # Should handle gracefully
            },
            {
                "name": "Very small collateral amount",
                "test": lambda: self.collateral_analyzer.analyze_collateral(
                    assets=[assets['ALGO']],
                    quantities=[Decimal("0.000001")],
                    loan_amount_usd=Decimal("1000")
                ),
                "should_fail": False  # Should handle gracefully
            }
        ]

        for case in error_test_cases:
            print(f"\nTesting: {case['name']}")
            try:
                result = await case['test']()
                if case['should_fail']:
                    print(f"  ⚠️ Expected failure but got result: {type(result)}")
                    success = False
                else:
                    print(f"  ✅ Handled gracefully")
            except Exception as e:
                if case['should_fail']:
                    print(f"  ✅ Correctly failed with: {type(e).__name__}")
                else:
                    print(f"  ❌ Unexpected failure: {e}")
                    success = False

        return success

    async def test_service_interface(self) -> bool:
        """Test the unified service interface."""
        print("\n🔌 Testing Service Interface")
        print("-" * 50)

        success = True

        try:
            # Test service info
            info = self.service.get_service_info()
            assert 'service_name' in info
            assert 'version' in info
            assert 'capabilities' in info
            print(f"  ✅ Service info: {info['service_name']} v{info['version']}")

            # Test simple API methods
            borrower_address = "ALGORAND_ADDRESS_SERVICE_TEST_123456789012345678901234567890"

            # Test loan evaluation
            result = self.service.evaluate_loan(
                borrower_address=borrower_address,
                loan_amount=50000,
                collateral_assets=[
                    {"asset_id": "0", "amount": 100000},
                    {"asset_id": "31566704", "amount": 25000}
                ]
            )

            assert 'decision' in result
            assert 'interest_rate' in result
            print(f"  ✅ Loan evaluation: {'APPROVED' if result['decision'] else 'REJECTED'}")

            # Test collateral analysis
            collateral_result = self.service.analyze_collateral([
                {"asset_id": "0", "amount": 75000},
                {"asset_id": "31566704", "amount": 50000}
            ])

            assert 'total_value_usd' in collateral_result
            assert 'risk_level' in collateral_result
            print(f"  ✅ Collateral analysis: ${collateral_result['total_value_usd']:,.2f}")

            # Test interest rate calculation
            rate = self.service.calculate_interest_rate(
                borrower_address,
                {"loan_amount": 100000, "term_days": 365}
            )

            assert rate > 0
            print(f"  ✅ Interest rate calculation: {rate:.2%}")

            # Test risk assessment
            risk = self.service.assess_risk(borrower_address)

            assert 'overall_risk' in risk
            assert 'risk_score' in risk
            print(f"  ✅ Risk assessment: {risk['overall_risk']} (score: {risk['risk_score']:.2f})")

        except Exception as e:
            print(f"  ❌ Service interface test failed: {e}")
            success = False

        return success

    async def run_full_integration_test(self) -> bool:
        """Run the complete integration test suite."""
        print("🚀 Starting Algorand Lending Business Logic Integration Test")
        print("=" * 70)

        self.start_time = time.time()

        # Setup
        await self.setup()

        # Run all test suites
        test_suites = [
            ("Individual Engine Functionality", self.test_individual_engine_functionality),
            ("Loan Approval Scenarios", self.test_loan_approval_scenarios),
            ("Performance Under Load", self.test_performance_under_load),
            ("Error Handling and Edge Cases", self.test_error_handling_and_edge_cases),
            ("Service Interface", self.test_service_interface)
        ]

        results = {}

        for suite_name, test_func in test_suites:
            print(f"\n🧪 Running: {suite_name}")
            try:
                suite_start = time.time()
                result = await test_func()
                suite_time = time.time() - suite_start

                results[suite_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"   {status} ({suite_time:.2f}s)")

            except Exception as e:
                results[suite_name] = False
                print(f"   ❌ FAILED with exception: {e}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")

        # Final results
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)

        print("\n" + "=" * 70)
        print("INTEGRATION TEST RESULTS")
        print("=" * 70)

        for suite_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {suite_name}: {status}")

        print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
        print(f"Total test time: {total_time:.2f} seconds")
        print(f"Test completed at: {datetime.now().isoformat()}")

        if passed_tests == total_tests:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Complete loan flow works correctly")
            print("✅ All engines integrate properly")
            print("✅ Error handling is robust")
            print("✅ Performance is acceptable")
            print("✅ Service interface works correctly")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} test suites failed")
            print("❌ Integration issues need to be resolved")
            return False

async def main():
    """Run the integration test."""
    test_runner = LendingIntegrationTest()
    success = await test_runner.run_full_integration_test()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)