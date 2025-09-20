#!/usr/bin/env python3
"""
Basic Collateral Analysis Example

Demonstrates how to use the collateral requirements engine with real Algorand data.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from core import CollateralRequirementsEngine


async def demo_algo_collateral_analysis():
    """Demo analyzing ALGO as collateral for a USD loan"""
    print("🔍 Algorand Collateral Analysis Demo")
    print("=" * 50)

    # Initialize the engine
    engine = CollateralRequirementsEngine()

    # Define a loan scenario
    loan_amount_usd = 50000  # $50k loan
    loan_id = "DEMO-LOAN-001"
    borrower_address = "DEMO-BORROWER-ABC123"

    # Define collateral positions
    collateral_positions = [
        {
            'asset_id': '0',         # ALGO native token
            'asset_symbol': 'ALGO',
            'amount': 300000         # 300k ALGO tokens
        }
    ]

    print(f"📊 Loan Details:")
    print(f"   Amount: ${loan_amount_usd:,}")
    print(f"   Loan ID: {loan_id}")
    print(f"   Borrower: {borrower_address}")
    print()

    print(f"💰 Collateral Offered:")
    for pos in collateral_positions:
        print(f"   {pos['amount']:,} {pos['asset_symbol']} (Asset ID: {pos['asset_id']})")
    print()

    # Run the analysis
    print("⚡ Running collateral analysis...")
    try:
        result = await engine.analyze_collateral_requirement(
            loan_amount_usd=loan_amount_usd,
            collateral_positions=collateral_positions,
            loan_id=loan_id,
            borrower_address=borrower_address,
            market_conditions="normal"
        )

        # Display results
        print("\n🎯 Analysis Results:")
        print("=" * 50)
        print(f"Required Collateral Ratio: {result.required_collateral_ratio:.2f}x")
        print(f"Current Collateral Value: ${result.total_collateral_value_usd:,.2f}")
        print(f"Required Collateral Value: ${loan_amount_usd * result.required_collateral_ratio:,.2f}")
        print(f"Risk Level: {result.risk_level.upper()}")
        print(f"Confidence Score: {result.confidence_score:.1%}")
        print()

        # Show collateral breakdown
        print("📋 Collateral Breakdown:")
        for pos in result.collateral_positions:
            print(f"   {pos.asset_symbol}: {pos.position_size:,.0f} @ ${pos.current_price_usd:.4f} = ${pos.position_value_usd:,.2f}")
            if pos.volatility_metrics:
                print(f"     Volatility (30d): {pos.volatility_metrics.volatility_30d:.1%}")
            if pos.liquidity_metrics:
                print(f"     Liquidity Tier: {pos.liquidity_metrics.liquidity_tier}")
        print()

        # Show liquidation scenarios
        print("⚠️  Liquidation Scenarios:")
        for scenario in result.liquidation_scenarios:
            print(f"   {scenario['scenario_name']}: {scenario['price_drop_percentage']:.1%} drop → "
                  f"${scenario['estimated_liquidation_value']:,.0f} recovery "
                  f"({scenario['scenario_probability']:.1%} probability)")
        print()

        # Show recommendations
        print("💡 Recommendations:")
        for rec in result.recommendations:
            print(f"   • {rec}")
        print()

        # Show database stats
        stats = engine.db.get_analysis_statistics()
        print("📈 Database Statistics:")
        print(f"   Total Analyses: {stats['total_analyses']}")
        print(f"   Analyses Last 24h: {stats['analyses_last_24h']}")
        if stats['average_collateral_ratio']:
            print(f"   Average Collateral Ratio: {stats['average_collateral_ratio']:.2f}x")
        print()

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


async def demo_mixed_collateral_analysis():
    """Demo analyzing mixed collateral portfolio"""
    print("\n🔍 Mixed Collateral Portfolio Analysis")
    print("=" * 50)

    engine = CollateralRequirementsEngine()

    # Mixed collateral scenario
    loan_amount_usd = 100000  # $100k loan

    collateral_positions = [
        {
            'asset_id': '0',
            'asset_symbol': 'ALGO',
            'amount': 200000  # 200k ALGO
        },
        {
            'asset_id': '31566704',  # USDC on Algorand
            'asset_symbol': 'USDC',
            'amount': 50000  # 50k USDC
        },
        {
            'asset_id': '312769',  # Example ASA token
            'asset_symbol': 'CUSTOM',
            'amount': 10000  # 10k custom tokens
        }
    ]

    print(f"📊 Loan Amount: ${loan_amount_usd:,}")
    print(f"💰 Mixed Collateral Portfolio:")
    for pos in collateral_positions:
        print(f"   {pos['amount']:,} {pos['asset_symbol']}")
    print()

    try:
        result = await engine.analyze_collateral_requirement(
            loan_amount_usd=loan_amount_usd,
            collateral_positions=collateral_positions,
            market_conditions="volatile"  # Stress test with volatile conditions
        )

        print("🎯 Analysis Results:")
        print(f"Required Ratio: {result.required_collateral_ratio:.2f}x")
        print(f"Current Value: ${result.total_collateral_value_usd:,.2f}")
        print(f"Risk Level: {result.risk_level.upper()}")
        print()

        shortage = (loan_amount_usd * result.required_collateral_ratio) - result.total_collateral_value_usd
        if shortage > 0:
            print(f"⚠️  Collateral Shortage: ${shortage:,.2f}")
        else:
            print(f"✅ Collateral Sufficient (${-shortage:,.2f} excess)")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all demos"""
    await demo_algo_collateral_analysis()
    await demo_mixed_collateral_analysis()


if __name__ == "__main__":
    asyncio.run(main())