#!/usr/bin/env python3
"""
Test file for Liquidity Pool Integration Engine

Tests the Tinyman, Algofi DEX, and pool yield calculator functionality.
"""

import asyncio
import sys
import os
import pytest
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.tinyman_pools import TinymanPoolsAnalyzer
from core.algofi_pools import AlgofiPoolsAnalyzer
from core.pool_yield_calculator import PoolYieldCalculator

async def test_tinyman_pools_analyzer():
    """Test the Tinyman pools analyzer functionality"""
    print("=== Testing Tinyman Pools Analyzer ===")

    try:
        analyzer = TinymanPoolsAnalyzer()

        # Test fetch pools
        print("\n1. Testing Tinyman pools fetch...")
        pools = await analyzer.fetch_tinyman_pools()
        print(f"   Found {len(pools)} pools")

        assert len(pools) >= 0, "Should return pool list (could be empty)"

        if pools:
            pool = pools[0]
            print(f"   Sample pool: {pool.asset_1_name}/{pool.asset_2_name}")
            print(f"   Total APY: {pool.total_apy:.2%}")
            print(f"   Fee APY: {pool.apy_fees:.2%}")
            print(f"   Rewards APY: {pool.apy_rewards:.2%}")
            print(f"   Liquidity: ${pool.liquidity_usd:,.0f}")

            assert 0.0 <= pool.total_apy <= 10.0, "Total APY should be reasonable"
            assert pool.liquidity_usd >= 0, "Liquidity should be non-negative"

        # Test yield analysis
        print("\n2. Testing Tinyman yield analysis...")
        yield_data = await analyzer.analyze_tinyman_yields()
        print(f"   Weighted Average APY: {yield_data.weighted_average_apy:.2%}")
        print(f"   Total TVL: ${yield_data.total_tvl:,.0f}")
        print(f"   Total 24h Volume: ${yield_data.total_volume_24h:,.0f}")
        print(f"   Average Fee APY: {yield_data.average_fee_apy:.2%}")
        print(f"   Average Rewards APY: {yield_data.average_rewards_apy:.2%}")
        print(f"   Confidence Score: {yield_data.confidence_score:.2f}")

        assert 0.0 <= yield_data.weighted_average_apy <= 10.0, "APY should be reasonable"
        assert yield_data.total_tvl >= 0, "TVL should be non-negative"
        assert 0.0 <= yield_data.confidence_score <= 1.0, "Confidence should be valid"

        # Test specific pool lookup
        print("\n3. Testing specific pool lookup...")
        algo_usdc_pool = await analyzer.get_pool_by_pair('ALGO', 'USDC')
        if algo_usdc_pool:
            print(f"   ALGO/USDC pool found: {algo_usdc_pool.total_apy:.2%} total APY")
            print(f"   Liquidity: ${algo_usdc_pool.liquidity_usd:,.0f}")
            assert 'ALGO' in [algo_usdc_pool.asset_1_name, algo_usdc_pool.asset_2_name], "Should find ALGO/USDC pool"

        # Test impermanent loss analysis
        if algo_usdc_pool:
            print("\n4. Testing impermanent loss analysis...")
            il_analysis = await analyzer.analyze_impermanent_loss(algo_usdc_pool.pool_id)
            print(f"   Risk Category: {il_analysis.risk_category}")
            print(f"   Break-even Days: {il_analysis.break_even_days:.0f}")
            print(f"   Net APY after IL Risk: {il_analysis.net_apy_after_il_risk:.2%}")

            assert il_analysis.risk_category in ['Low', 'Medium', 'High', 'Extreme'], "Risk category should be valid"
            assert il_analysis.break_even_days >= 0, "Break-even days should be non-negative"

        # Test top yield opportunities
        print("\n5. Testing top yield opportunities...")
        opportunities = await analyzer.get_top_yield_opportunities(50000)
        print(f"   Found {len(opportunities)} opportunities")

        if opportunities:
            top_opp = opportunities[0]
            print(f"   Top opportunity: {top_opp['pair']}")
            print(f"   Total APY: {top_opp['total_apy']:.2%}")
            print(f"   IL Risk: {top_opp['il_risk_category']}")

            assert top_opp['total_apy'] >= 0, "APY should be non-negative"
            assert top_opp['liquidity_usd'] >= 50000, "Should meet minimum liquidity"

        print("✅ Tinyman Pools Analyzer tests passed!")
        return True

    except Exception as e:
        print(f"❌ Tinyman Pools Analyzer test failed: {e}")
        return False

async def test_algofi_pools_analyzer():
    """Test the Algofi pools analyzer functionality"""
    print("\n=== Testing Algofi Pools Analyzer ===")

    try:
        analyzer = AlgofiPoolsAnalyzer()

        # Test fetch pools
        print("\n1. Testing Algofi pools fetch...")
        pools = await analyzer.fetch_algofi_pools()
        print(f"   Found {len(pools)} pools")

        assert len(pools) >= 0, "Should return pool list (could be empty)"

        if pools:
            pool = pools[0]
            print(f"   Sample pool: {pool.asset_1_name}/{pool.asset_2_name}")
            print(f"   Total APY: {pool.total_apy:.2%}")
            print(f"   Trading Fees APY: {pool.apy_trading_fees:.2%}")
            print(f"   ALFI Rewards APY: {pool.apy_alfi_rewards:.2%}")
            print(f"   Multiplier Boost: {pool.multiplier_boost:.1f}x")

            assert 0.0 <= pool.total_apy <= 10.0, "Total APY should be reasonable"
            assert pool.multiplier_boost >= 1.0, "Multiplier should be at least 1.0"

        # Test pool analysis
        print("\n2. Testing Algofi pool analysis...")
        pool_data = await analyzer.analyze_algofi_pools()
        print(f"   Weighted Average APY: {pool_data.weighted_average_apy:.2%}")
        print(f"   Total TVL: ${pool_data.total_tvl:,.0f}")
        print(f"   Average Trading APY: {pool_data.average_trading_apy:.2%}")
        print(f"   Average ALFI Rewards: {pool_data.average_alfi_rewards:.2%}")
        print(f"   Total ALFI Emissions: {pool_data.total_alfi_emissions:,.0f} ALFI/day")
        print(f"   Confidence Score: {pool_data.confidence_score:.2f}")

        assert 0.0 <= pool_data.weighted_average_apy <= 10.0, "APY should be reasonable"
        assert pool_data.total_tvl >= 0, "TVL should be non-negative"
        assert 0.0 <= pool_data.confidence_score <= 1.0, "Confidence should be valid"

        # Test specific pool lookup
        print("\n3. Testing specific pool lookup...")
        algo_usdc_pool = await analyzer.get_pool_by_pair('ALGO', 'USDC')
        if algo_usdc_pool:
            print(f"   ALGO/USDC pool found: {algo_usdc_pool.total_apy:.2%} total APY")
            print(f"   Fee tier: {algo_usdc_pool.fee_tier:.2%}")
            assert 'ALGO' in [algo_usdc_pool.asset_1_name, algo_usdc_pool.asset_2_name], "Should find ALGO/USDC pool"

        # Test liquidity mining details
        if algo_usdc_pool:
            print("\n4. Testing liquidity mining details...")
            mining_data = await analyzer.get_liquidity_mining_details(algo_usdc_pool.pool_id)
            print(f"   ALFI Emission Rate: {mining_data.alfi_emission_rate:,.0f} ALFI/day")
            print(f"   ALFI Price: ${mining_data.alfi_price_usd:.3f}")
            print(f"   Effective APY: {mining_data.effective_apy:.2%}")
            print(f"   Risk-Adjusted APY: {mining_data.risk_adjusted_apy:.2%}")

            assert mining_data.alfi_emission_rate >= 0, "Emission rate should be non-negative"
            assert mining_data.alfi_price_usd > 0, "ALFI price should be positive"

        # Test ALFI emissions analysis
        print("\n5. Testing ALFI emissions analysis...")
        emissions_analysis = await analyzer.analyze_alfi_emissions_impact()
        if "error" not in emissions_analysis:
            print(f"   Total Daily ALFI: {emissions_analysis['total_daily_alfi_emissions']:,.0f}")
            print(f"   USD Value: ${emissions_analysis['total_daily_usd_value']:,.0f}")
            print(f"   Sustainability Score: {emissions_analysis['sustainability_score']:.2f}")

            assert emissions_analysis['total_daily_alfi_emissions'] >= 0, "Emissions should be non-negative"
            assert 0.0 <= emissions_analysis['sustainability_score'] <= 1.0, "Sustainability should be valid"

        # Test pool efficiency comparison
        print("\n6. Testing pool efficiency comparison...")
        efficiency = await analyzer.compare_pool_efficiency()
        if "error" not in efficiency:
            print(f"   Most efficient: {efficiency['most_efficient_pool']['pair'] if efficiency['most_efficient_pool'] else 'None'}")
            print(f"   Average efficiency: {efficiency['average_efficiency']:.2f}")

            assert 'pools' in efficiency, "Should include pool analysis"

        print("✅ Algofi Pools Analyzer tests passed!")
        return True

    except Exception as e:
        print(f"❌ Algofi Pools Analyzer test failed: {e}")
        return False

async def test_pool_yield_calculator():
    """Test the pool yield calculator functionality"""
    print("\n=== Testing Pool Yield Calculator ===")

    try:
        calculator = PoolYieldCalculator()

        # Test calculate all pool yields
        print("\n1. Testing pool yield calculation...")
        aggregated = await calculator.calculate_all_pool_yields()
        print(f"   Overall Weighted Yield: {aggregated.overall_weighted_yield:.2%}")
        print(f"   Total TVL Across DEXes: ${aggregated.total_tvl_across_dexes:,.0f}")
        print(f"   Total 24h Volume: ${aggregated.total_volume_24h:,.0f}")
        print(f"   Average IL Risk: {aggregated.average_il_risk:.2%}")
        print(f"   Sustainability Score: {aggregated.sustainability_score:.2f}")

        assert 0.0 <= aggregated.overall_weighted_yield <= 10.0, "Yield should be reasonable"
        assert aggregated.total_tvl_across_dexes >= 0, "TVL should be non-negative"
        assert 0.0 <= aggregated.sustainability_score <= 1.0, "Sustainability should be valid"

        # Test DEX market shares
        print(f"\n2. Testing DEX market shares...")
        for dex, share in aggregated.dex_market_shares.items():
            print(f"   {dex}: {share:.1%}")
            assert 0.0 <= share <= 1.0, "Market share should be valid percentage"

        # Test pool summaries
        print(f"\n3. Testing pool summaries ({len(aggregated.pool_summaries)} pairs)...")
        for summary in aggregated.pool_summaries[:2]:  # Test first 2
            print(f"   {summary.asset_pair}:")
            print(f"     Weighted Average Yield: {summary.weighted_average_yield:.2%}")
            print(f"     Best Yield: {summary.best_yield_dex}")
            print(f"     Yield Spread: {summary.yield_spread:.2%}")

            assert summary.weighted_average_yield >= 0, "Yield should be non-negative"
            assert summary.yield_spread >= 0, "Spread should be non-negative"

        # Test top opportunities
        print(f"\n4. Testing top opportunities...")
        for i, opp in enumerate(aggregated.top_yield_opportunities[:3], 1):
            print(f"   {i}. {opp['pair']} on {opp['dex']}: {opp['total_apy']:.2%}")
            assert opp['total_apy'] >= 0, "APY should be non-negative"
            assert opp['liquidity_usd'] >= 0, "Liquidity should be non-negative"

        # Test optimal allocation
        print(f"\n5. Testing optimal LP allocation...")
        allocation = await calculator.get_optimal_lp_allocation(0.08, "medium")
        if "error" not in allocation:
            print(f"   Expected APY: {allocation['expected_apy']:.2%}")
            print(f"   Expected IL Risk: {allocation['expected_il_risk']:.2f}")
            print(f"   Diversification Score: {allocation['diversification_score']:.2f}")

            assert allocation['expected_apy'] >= 0, "Expected APY should be non-negative"
            assert 0.0 <= allocation['diversification_score'] <= 1.0, "Diversification should be valid"

            print(f"   Top allocations:")
            for alloc in allocation['allocations'][:2]:
                print(f"     {alloc['pair']} on {alloc['dex']}: {alloc['weight']:.1%}")
                assert 0.0 <= alloc['weight'] <= 1.0, "Weight should be valid percentage"

        # Test yield projections
        print(f"\n6. Testing yield projections...")
        projections = await calculator.project_yields(30)
        print(f"   Generated {len(projections)} projections")

        if projections:
            proj = projections[0]
            print(f"   Sample: {proj.pool_pair} on {proj.dex_name}")
            print(f"   30-day Projected: {proj.projected_30d_yield:.2%}")
            print(f"   Net After IL: {proj.net_yield_after_il:.2%}")
            print(f"   Risk Factors: {len(proj.risk_factors)}")

            assert proj.projected_30d_yield >= 0, "Projected yield should be non-negative"
            assert proj.net_yield_after_il >= 0, "Net yield should be non-negative"

        print("✅ Pool Yield Calculator tests passed!")
        return True

    except Exception as e:
        print(f"❌ Pool Yield Calculator test failed: {e}")
        return False

async def test_integration():
    """Test integration between all liquidity pool components"""
    print("\n=== Testing Liquidity Pool Integration ===")

    try:
        # Initialize all analyzers
        tinyman_analyzer = TinymanPoolsAnalyzer()
        algofi_analyzer = AlgofiPoolsAnalyzer()
        calculator = PoolYieldCalculator()

        # Get data from individual analyzers
        tinyman_data = await tinyman_analyzer.analyze_tinyman_yields()
        algofi_data = await algofi_analyzer.analyze_algofi_pools()

        # Verify calculator can combine them
        aggregated_data = await calculator.calculate_all_pool_yields()

        # Compare individual vs aggregated results
        print(f"   Tinyman APY: {tinyman_data.weighted_average_apy:.2%}")
        print(f"   Algofi APY: {algofi_data.weighted_average_apy:.2%}")
        print(f"   Aggregated APY: {aggregated_data.overall_weighted_yield:.2%}")

        print(f"   Tinyman TVL: ${tinyman_data.total_tvl:,.0f}")
        print(f"   Algofi TVL: ${algofi_data.total_tvl:,.0f}")
        print(f"   Combined TVL: ${aggregated_data.total_tvl_across_dexes:,.0f}")

        # Verify TVL aggregation is reasonable
        individual_tvl = tinyman_data.total_tvl + algofi_data.total_tvl
        assert abs(aggregated_data.total_tvl_across_dexes - individual_tvl) / max(individual_tvl, 1) < 0.1, "TVL aggregation should be consistent"

        # Verify yield is in reasonable range
        individual_yields = [tinyman_data.weighted_average_apy, algofi_data.weighted_average_apy]
        min_yield = min(individual_yields) if individual_yields else 0
        max_yield = max(individual_yields) if individual_yields else 0

        if min_yield > 0 and max_yield > 0:
            assert min_yield * 0.5 <= aggregated_data.overall_weighted_yield <= max_yield * 1.5, "Aggregated yield should be in reasonable range"

        print("✅ Liquidity Pool Integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Liquidity Pool Integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests for the liquidity-pool-integration engine"""
    print("Starting Liquidity Pool Integration Engine Tests...")

    test_results = []

    # Run individual tests
    test_results.append(await test_tinyman_pools_analyzer())
    test_results.append(await test_algofi_pools_analyzer())
    test_results.append(await test_pool_yield_calculator())
    test_results.append(await test_integration())

    # Summary
    passed = sum(test_results)
    total = len(test_results)

    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All Liquidity Pool Integration Engine tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)