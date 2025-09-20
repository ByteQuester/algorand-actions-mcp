#!/usr/bin/env python3
"""
Simple Integration Example - 3-Line Pattern

This demonstrates the absolute simplest way to integrate the algorand-lending-business-logic
package into any project. Just 3 lines and you're ready to analyze loans!

Usage:
    python simple_integration.py
"""

import sys
from pathlib import Path

# Add the vendor package to Python path (if not installed)
vendor_path = Path(__file__).parent / "algorand_lending_bl"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path.parent))

# ============================================================================
# THE 3-LINE INTEGRATION PATTERN
# ============================================================================

# Line 1: Import the service factory
from algorand_lending_bl import create_lending_service

# Line 2: Create the service (works out of the box with defaults)
lending_service = create_lending_service()

# Line 3: Use the service (all engines ready to use)
print("✓ Lending service ready with engines:", list(lending_service.keys()))

# ============================================================================
# SIMPLE USAGE EXAMPLE
# ============================================================================

def simple_loan_analysis():
    """Demonstrate basic loan analysis with minimal code."""

    # Import required models
    from algorand_lending_bl import LoanRequest, AlgorandAddress, ASAToken

    print("\n🏦 Simple Loan Analysis Example")
    print("=" * 50)

    # Create a sample loan request
    borrower = AlgorandAddress("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    collateral = [
        ASAToken(asset_id=0, amount=2000000),        # 2 ALGO
        ASAToken(asset_id=31566704, amount=10000000) # 10 USDC
    ]

    loan_request = LoanRequest(
        borrower=borrower,
        requested_amount=1000000,  # 1 ALGO
        collateral_assets=collateral,
        loan_duration_days=30
    )

    print(f"📋 Loan Request:")
    print(f"   Borrower: {borrower}")
    print(f"   Amount: {loan_request.requested_amount / 1_000_000:.2f} ALGO")
    print(f"   Collateral: {len(collateral)} assets")
    print(f"   Duration: {loan_request.loan_duration_days} days")

    # 1. Analyze collateral
    print(f"\n🔍 Analyzing collateral...")
    collateral_analysis = lending_service["collateral"].analyze_collateral(
        collateral, borrower
    )
    print(f"   Total value: ${collateral_analysis.total_value:.2f}")
    print(f"   Liquidity tier: {collateral_analysis.liquidity_tier}")

    # 2. Calculate interest rate
    print(f"\n📊 Calculating interest rate...")
    rate_calculation = lending_service["interest_rates"].calculate_interest_rate(loan_request)
    print(f"   Base rate: {rate_calculation.base_rate:.2%}")
    print(f"   Final rate: {rate_calculation.final_rate:.2%}")

    # 3. Evaluate loan approval
    print(f"\n✅ Evaluating loan approval...")
    loan_decision = lending_service["loan_approval"].evaluate_loan(loan_request)
    print(f"   Decision: {loan_decision.decision}")
    print(f"   Confidence: {loan_decision.confidence}")
    print(f"   Approved amount: {loan_decision.approved_amount / 1_000_000:.2f} ALGO")

    # 4. Assess risk
    print(f"\n⚠️  Assessing risk...")
    risk_assessment = lending_service["risk_assessment"].assess_risk(loan_request)
    print(f"   Overall risk score: {risk_assessment.overall_score:.2f}")
    print(f"   Risk level: {risk_assessment.risk_level}")

    return {
        "collateral": collateral_analysis,
        "interest_rate": rate_calculation,
        "approval": loan_decision,
        "risk": risk_assessment
    }


def demonstrate_engine_access():
    """Show different ways to access the engines."""

    print("\n🔧 Engine Access Patterns")
    print("=" * 50)

    # Method 1: Via service dictionary
    collateral_engine = lending_service["collateral"]
    print(f"✓ Collateral engine: {type(collateral_engine).__name__}")

    # Method 2: Direct import and creation
    from algorand_lending_bl import CollateralAnalyzer, DEFAULT_CONFIG
    direct_engine = CollateralAnalyzer(DEFAULT_CONFIG.collateral)
    print(f"✓ Direct engine: {type(direct_engine).__name__}")

    # Method 3: Individual engine creation helper
    from algorand_lending_bl import create_lending_engines
    engines = create_lending_engines()
    print(f"✓ Created {len(engines)} engines directly")


def demonstrate_configuration():
    """Show configuration options."""

    print("\n⚙️  Configuration Options")
    print("=" * 50)

    # Default configuration
    from algorand_lending_bl import DEFAULT_CONFIG
    print(f"✓ Default config network: {DEFAULT_CONFIG.network.network_name}")

    # TestNet configuration
    from algorand_lending_bl import create_testnet_config
    testnet_config = create_testnet_config()
    testnet_service = create_lending_service(testnet_config)
    print(f"✓ TestNet service created")

    # Environment-based configuration
    from algorand_lending_bl import create_config_from_env
    try:
        env_config = create_config_from_env()
        print(f"✓ Environment config loaded")
    except Exception as e:
        print(f"ℹ️  Environment config not available: {e}")


def main():
    """Main demonstration function."""

    print("🚀 Algorand Lending Business Logic - Simple Integration")
    print("=" * 60)

    # Show that the service is ready
    print(f"✓ Service initialized with {len(lending_service)} engines")
    print(f"✓ Available engines: {', '.join(lending_service.keys())}")

    # Run demonstrations
    try:
        # Basic loan analysis
        results = simple_loan_analysis()

        # Engine access patterns
        demonstrate_engine_access()

        # Configuration options
        demonstrate_configuration()

        print(f"\n🎉 Integration Success!")
        print(f"   The algorand-lending-business-logic package is working perfectly!")
        print(f"   You can now build your lending application with minimal effort.")

        # Show package info
        from algorand_lending_bl import VENDOR_INFO
        print(f"\n📦 Package Info:")
        print(f"   Name: {VENDOR_INFO['name']}")
        print(f"   Version: {VENDOR_INFO['version']}")
        print(f"   Dependencies: {', '.join(VENDOR_INFO['dependencies'])}")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print(f"   Please check that the package is properly vendored.")
        sys.exit(1)


if __name__ == "__main__":
    main()