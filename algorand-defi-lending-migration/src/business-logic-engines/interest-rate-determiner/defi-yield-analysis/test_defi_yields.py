#!/usr/bin/env python3
"""
Test file for DeFi Yield Analysis Engine

Tests the Algofi, Folks Finance, and yield aggregator functionality.
"""

import asyncio
import sys
import os
import pytest
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.algofi_yields import AlgofiYieldsAnalyzer
from core.folks_finance_yields import FolksFinanceYieldsAnalyzer
from core.yield_aggregator import YieldAggregator

async def test_algofi_yields_analyzer():
    """Test the Algofi yields analyzer functionality"""
    print("=== Testing Algofi Yields Analyzer ===")

    try:
        analyzer = AlgofiYieldsAnalyzer()

        # Test fetch markets
        print("\n1. Testing Algofi markets fetch...")
        markets = await analyzer.fetch_algofi_markets()
        print(f"   Found {len(markets)} markets")

        assert len(markets) >= 0, "Should return market list (could be empty)"

        if markets:
            market = markets[0]
            print(f"   Sample market: {market.asset_name}")
            print(f"   Supply APY: {market.supply_apy:.2%}")
            print(f"   Borrow APY: {market.borrow_apy:.2%}")
            print(f"   Total Supply: {market.total_supply:,.0f}")

            assert 0.0 <= market.supply_apy <= 5.0, "Supply APY should be reasonable"
            assert market.borrow_apy >= market.supply_apy, "Borrow APY should be >= Supply APY"

        # Test yield analysis
        print("\n2. Testing Algofi yield analysis...")
        yield_data = await analyzer.analyze_algofi_yields()
        print(f"   Weighted Supply APY: {yield_data.weighted_average_supply_apy:.2%}")
        print(f"   Weighted Borrow APY: {yield_data.weighted_average_borrow_apy:.2%}")
        print(f"   Total TVL: ${yield_data.total_value_locked:,.0f}")
        print(f"   Protocol Utilization: {yield_data.protocol_utilization:.2%}")
        print(f"   Confidence Score: {yield_data.confidence_score:.2f}")

        assert 0.0 <= yield_data.weighted_average_supply_apy <= 5.0, "Supply APY should be reasonable"
        assert yield_data.total_value_locked >= 0, "TVL should be non-negative"
        assert 0.0 <= yield_data.confidence_score <= 1.0, "Confidence should be valid"

        # Test specific market lookup
        print("\n3. Testing specific market lookup...")
        algo_market = await analyzer.get_market_by_asset('ALGO')
        if algo_market:
            print(f"   ALGO market found: {algo_market.supply_apy:.2%} supply APY")
            assert algo_market.asset_name.upper() == 'ALGO', "Should find ALGO market"

        # Test yield history
        print("\n4. Testing yield history...")
        history = await analyzer.get_yield_history('ALGO', 7)
        if "error" not in history:
            print(f"   ALGO average yield (7d): {history['average_yield']:.2%}")
            print(f"   Volatility: {history['volatility']:.2%}")
            print(f"   Trend: {history['trend']}")

            assert history['data_points'] > 0, "Should have data points"

        # Test spreads comparison
        print("\n5. Testing spreads comparison...")
        spreads = await analyzer.compare_supply_borrow_spreads()
        if "error" not in spreads:
            print(f"   Average spread: {spreads['average_spread']:.2%}")
            print(f"   Total markets: {spreads['total_markets']}")

            assert spreads['total_markets'] >= 0, "Should report market count"

        print("✅ Algofi Yields Analyzer tests passed!")
        return True

    except Exception as e:
        print(f"❌ Algofi Yields Analyzer test failed: {e}")
        return False

async def test_folks_finance_analyzer():
    """Test the Folks Finance yields analyzer functionality"""
    print("\n=== Testing Folks Finance Yields Analyzer ===")

    try:
        analyzer = FolksFinanceYieldsAnalyzer()

        # Test fetch pools
        print("\n1. Testing Folks Finance pools fetch...")
        pools = await analyzer.fetch_folks_pools()
        print(f"   Found {len(pools)} pools")

        assert len(pools) >= 0, "Should return pool list (could be empty)"

        if pools:
            pool = pools[0]
            print(f"   Sample pool: {pool.asset_name}")
            print(f"   Supply APY: {pool.supply_apy:.2%}")
            print(f"   Pool Rewards APY: {pool.pool_rewards_apy:.2%}")
            print(f"   Total Deposited: {pool.total_deposited:,.0f}")

            assert 0.0 <= pool.supply_apy <= 5.0, "Supply APY should be reasonable"
            assert 0.0 <= pool.pool_rewards_apy <= 2.0, "Pool rewards should be reasonable"

        # Test yield analysis
        print("\n2. Testing Folks Finance yield analysis...")
        yield_data = await analyzer.analyze_folks_yields()
        print(f"   Weighted Supply APY: {yield_data.weighted_supply_apy:.2%}")
        print(f"   Weighted Borrow APY: {yield_data.weighted_borrow_apy:.2%}")
        print(f"   Total Rewards APY: {yield_data.total_rewards_apy:.2%}")
        print(f"   Protocol TVL: ${yield_data.protocol_tvl:,.0f}")
        print(f"   Average Utilization: {yield_data.average_utilization:.2%}")
        print(f"   Confidence Score: {yield_data.confidence_score:.2f}")

        assert 0.0 <= yield_data.weighted_supply_apy <= 5.0, "Supply APY should be reasonable"
        assert yield_data.protocol_tvl >= 0, "TVL should be non-negative"
        assert 0.0 <= yield_data.confidence_score <= 1.0, "Confidence should be valid"

        # Test specific pool lookup
        print("\n3. Testing specific pool lookup...")
        algo_pool = await analyzer.get_pool_by_asset('ALGO')
        if algo_pool:
            print(f"   ALGO pool found: {algo_pool.supply_apy:.2%} supply APY")
            print(f"   Pool rewards: {algo_pool.pool_rewards_apy:.2%}")
            assert algo_pool.asset_name.upper() == 'ALGO', "Should find ALGO pool"

        # Test utilization analysis
        print("\n4. Testing utilization analysis...")
        utilization = await analyzer.get_optimal_utilization_analysis()
        if "error" not in utilization:
            print(f"   Average utilization: {utilization['average_utilization']:.2%}")
            print(f"   Protocol TVL: ${utilization['protocol_tvl']:,.0f}")

            assert 'pools' in utilization, "Should include pool analysis"

        # Test competitive comparison
        print("\n5. Testing competitive comparison...")
        competition = await analyzer.compare_with_competitors()
        if "error" not in competition:
            print(f"   Total market TVL: ${competition['total_market_tvl']:,.0f}")
            print(f"   Market leader: {competition['market_leader_supply'][0]}")

            assert 'protocols' in competition, "Should include protocol comparison"

        print("✅ Folks Finance Yields Analyzer tests passed!")
        return True

    except Exception as e:
        print(f"❌ Folks Finance Yields Analyzer test failed: {e}")
        return False

async def test_yield_aggregator():
    """Test the yield aggregator functionality"""
    print("\n=== Testing Yield Aggregator ===")

    try:
        aggregator = YieldAggregator()

        # Test yield aggregation
        print("\n1. Testing yield aggregation...")
        aggregated = await aggregator.aggregate_yields()
        print(f"   Weighted Supply APY: {aggregated.weighted_supply_apy:.2%}")
        print(f"   Weighted Borrow APY: {aggregated.weighted_borrow_apy:.2%}")
        print(f"   Total Rewards APY: {aggregated.total_rewards_apy:.2%}")
        print(f"   Protocol Count: {aggregated.protocol_count}")
        print(f"   Total Market TVL: ${aggregated.total_market_tvl:,.0f}")
        print(f"   Yield Spread: {aggregated.yield_spread:.2%}")
        print(f"   Average Confidence: {aggregated.average_confidence:.2f}")

        assert 0.0 <= aggregated.weighted_supply_apy <= 5.0, "Supply APY should be reasonable"
        assert aggregated.protocol_count >= 0, "Protocol count should be non-negative"
        assert aggregated.total_market_tvl >= 0, "TVL should be non-negative"
        assert 0.0 <= aggregated.average_confidence <= 1.0, "Confidence should be valid"

        # Test protocol breakdown
        print(f"\n2. Testing protocol breakdown ({len(aggregated.protocol_breakdown)} protocols)...")
        for protocol in aggregated.protocol_breakdown:
            print(f"   {protocol.protocol_name}:")
            print(f"     Supply APY: {protocol.supply_apy:.2%}")
            print(f"     Additional Rewards: {protocol.additional_rewards:.2%}")
            print(f"     TVL: ${protocol.total_tvl:,.0f}")
            print(f"     Weight: {protocol.weight:.1%}")

            assert 0.0 <= protocol.supply_apy <= 5.0, "Protocol APY should be reasonable"
            assert protocol.total_tvl >= 0, "Protocol TVL should be non-negative"

        # Test asset-specific yields
        print("\n3. Testing asset-specific yields...")
        for asset in ['ALGO', 'USDC']:
            asset_yield = await aggregator.get_asset_specific_yields(asset)
            print(f"   {asset}:")
            print(f"     Weighted Average Yield: {asset_yield.weighted_average_yield:.2%}")
            print(f"     Best Protocol: {asset_yield.best_yield_protocol}")
            print(f"     Yield Range: {asset_yield.yield_range:.2%}")
            print(f"     Confidence: {asset_yield.confidence_score:.2f}")

            assert asset_yield.weighted_average_yield >= 0, "Yield should be non-negative"
            assert 0.0 <= asset_yield.confidence_score <= 1.0, "Confidence should be valid"

        # Test yield trends
        print("\n4. Testing yield trends...")
        trends = await aggregator.get_yield_trends(7)
        if "error" not in trends:
            supply_trend = trends['supply_apy_trend']
            print(f"   Supply APY trend: {supply_trend['direction']}")
            print(f"   Change: {supply_trend['change']:+.2%}")
            print(f"   Volatility: {supply_trend['volatility']:.2%}")

            assert 'direction' in supply_trend, "Should include trend direction"
            assert 'change' in supply_trend, "Should include change calculation"

        print("✅ Yield Aggregator tests passed!")
        return True

    except Exception as e:
        print(f"❌ Yield Aggregator test failed: {e}")
        return False

async def test_integration():
    """Test integration between all DeFi yield components"""
    print("\n=== Testing DeFi Yield Integration ===")

    try:
        # Initialize all analyzers
        algofi_analyzer = AlgofiYieldsAnalyzer()
        folks_analyzer = FolksFinanceYieldsAnalyzer()
        aggregator = YieldAggregator()

        # Get data from individual analyzers
        algofi_data = await algofi_analyzer.analyze_algofi_yields()
        folks_data = await folks_analyzer.analyze_folks_yields()

        # Verify aggregator can combine them
        aggregated_data = await aggregator.aggregate_yields()

        # Compare individual vs aggregated results
        print(f"   Algofi Supply APY: {algofi_data.weighted_average_supply_apy:.2%}")
        print(f"   Folks Supply APY: {folks_data.weighted_supply_apy:.2%}")
        print(f"   Aggregated Supply APY: {aggregated_data.weighted_supply_apy:.2%}")

        # Verify aggregated is reasonable combination
        individual_apys = [algofi_data.weighted_average_supply_apy, folks_data.weighted_supply_apy]
        min_apy = min(individual_apys)
        max_apy = max(individual_apys)

        assert min_apy <= aggregated_data.weighted_supply_apy <= max_apy, "Aggregated APY should be in reasonable range"

        print("✅ DeFi Yield Integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ DeFi Yield Integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests for the defi-yield-analysis engine"""
    print("Starting DeFi Yield Analysis Engine Tests...")

    test_results = []

    # Run individual tests
    test_results.append(await test_algofi_yields_analyzer())
    test_results.append(await test_folks_finance_analyzer())
    test_results.append(await test_yield_aggregator())
    test_results.append(await test_integration())

    # Summary
    passed = sum(test_results)
    total = len(test_results)

    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All DeFi Yield Analysis Engine tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)