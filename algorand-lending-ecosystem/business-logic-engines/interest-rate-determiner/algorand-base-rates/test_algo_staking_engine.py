#!/usr/bin/env python3
"""
Test file for Algorand Base Rates Engine

Tests the ALGO staking engine and consensus rewards analyzer functionality.
"""

import asyncio
import sys
import os
import pytest
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.algo_staking_engine import AlgoStakingEngine
from core.consensus_rewards import ConsensusRewardsAnalyzer

async def test_algo_staking_engine():
    """Test the ALGO staking engine functionality"""
    print("=== Testing ALGO Staking Engine ===")

    try:
        engine = AlgoStakingEngine()

        # Test current staking metrics
        print("\n1. Testing current staking metrics...")
        metrics = await engine.get_current_staking_metrics()
        print(f"   Current APY: {metrics.current_apy:.2%}")
        print(f"   Participation Rate: {metrics.participation_rate:.2%}")
        print(f"   Confidence Score: {metrics.confidence_score:.2f}")

        assert 0.0 <= metrics.current_apy <= 1.0, "APY should be between 0% and 100%"
        assert 0.0 <= metrics.participation_rate <= 1.0, "Participation rate should be between 0% and 100%"
        assert 0.0 <= metrics.confidence_score <= 1.0, "Confidence score should be between 0 and 1"

        # Test base rate calculation
        print("\n2. Testing base rate calculation...")
        result = await engine.calculate_base_rate()
        print(f"   Base Rate: {result.base_rate:.2%}")
        print(f"   Staking Component: {result.staking_component:.2%}")
        print(f"   Participation Component: {result.participation_component:.2%}")
        print(f"   Governance Component: {result.governance_component:.2%}")
        print(f"   Security Component: {result.network_security_component:.2%}")

        assert 0.0 <= result.base_rate <= 1.0, "Base rate should be reasonable"
        assert result.base_rate > 0, "Base rate should be positive"

        # Test historical analysis
        print("\n3. Testing historical analysis...")
        analysis = await engine.get_historical_analysis(30)
        if "error" not in analysis:
            print(f"   Average Rate (30d): {analysis['average_rate']:.2%}")
            print(f"   Volatility: {analysis['volatility']:.2%}")
            print(f"   Trend: {analysis['trend']}")

            assert analysis['data_points'] > 0, "Should have data points"
            assert 'average_rate' in analysis, "Should include average rate"

        print("✅ ALGO Staking Engine tests passed!")
        return True

    except Exception as e:
        print(f"❌ ALGO Staking Engine test failed: {e}")
        return False

async def test_consensus_rewards_analyzer():
    """Test the consensus rewards analyzer functionality"""
    print("\n=== Testing Consensus Rewards Analyzer ===")

    try:
        analyzer = ConsensusRewardsAnalyzer()

        # Test consensus metrics
        print("\n1. Testing consensus metrics...")
        metrics = await analyzer.get_consensus_metrics()
        print(f"   Online Stake: {metrics.online_stake_percentage:.2%}")
        print(f"   Participation APY: {metrics.participation_rewards_apy:.2%}")
        print(f"   Governance APY: {metrics.governance_rewards_apy:.2%}")
        print(f"   Validator Count: {metrics.validator_count:,}")
        print(f"   Average Uptime: {metrics.average_uptime:.2%}")
        print(f"   Consensus Efficiency: {metrics.consensus_efficiency:.2%}")

        assert 0.0 <= metrics.online_stake_percentage <= 1.0, "Online stake should be valid percentage"
        assert metrics.validator_count >= 0, "Validator count should be non-negative"
        assert 0.0 <= metrics.average_uptime <= 1.0, "Uptime should be valid percentage"

        # Test reward analysis
        print("\n2. Testing reward component analysis...")
        analysis = await analyzer.analyze_reward_components()
        print(f"   Total Reward Rate: {analysis.total_reward_rate:.2%}")
        print(f"   Consensus Component: {analysis.consensus_component:.2%}")
        print(f"   Governance Component: {analysis.governance_component:.2%}")
        print(f"   Security Premium: {analysis.security_premium:.2%}")
        print(f"   Participation Bonus: {analysis.participation_bonus:.2%}")

        assert analysis.total_reward_rate >= 0, "Total reward rate should be non-negative"
        assert analysis.consensus_component >= 0, "Consensus component should be non-negative"

        # Test governance summary
        print("\n3. Testing governance summary...")
        governance = await analyzer.get_governance_summary()
        print(f"   Current Period: {governance.current_period}")
        print(f"   Total Governors: {governance.total_governors:,}")
        print(f"   Committed ALGO: {governance.committed_algo / 1_000_000:,.0f}M")
        print(f"   Governance APY: {governance.governance_apy:.2%}")

        assert governance.current_period >= 0, "Governance period should be non-negative"
        assert governance.total_governors >= 0, "Governor count should be non-negative"

        # Test participation trend
        print("\n4. Testing participation trend...")
        trend = await analyzer.get_participation_trend(30)
        if "error" not in trend:
            print(f"   Average Participation: {trend['average_participation']:.2%}")
            print(f"   Target Achievement: {trend['target_achievement_rate']:.2%}")
            print(f"   Trend: {trend['trend']}")

            assert 'average_participation' in trend, "Should include average participation"
            assert 0.0 <= trend['average_participation'] <= 1.0, "Participation should be valid percentage"

        print("✅ Consensus Rewards Analyzer tests passed!")
        return True

    except Exception as e:
        print(f"❌ Consensus Rewards Analyzer test failed: {e}")
        return False

async def test_integration():
    """Test integration between staking engine and consensus analyzer"""
    print("\n=== Testing Integration ===")

    try:
        engine = AlgoStakingEngine()
        analyzer = ConsensusRewardsAnalyzer()

        # Get data from both engines
        staking_result = await engine.calculate_base_rate()
        consensus_analysis = await analyzer.analyze_reward_components()

        # Verify they can work together
        combined_rate = staking_result.base_rate + consensus_analysis.total_reward_rate
        print(f"   Combined Base Rate: {combined_rate:.2%}")
        print(f"   Staking Contribution: {staking_result.base_rate / combined_rate:.1%}")
        print(f"   Consensus Contribution: {consensus_analysis.total_reward_rate / combined_rate:.1%}")

        assert combined_rate > 0, "Combined rate should be positive"
        assert combined_rate < 1.0, "Combined rate should be reasonable"

        print("✅ Integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests for the algorand-base-rates engine"""
    print("Starting Algorand Base Rates Engine Tests...")

    test_results = []

    # Run individual tests
    test_results.append(await test_algo_staking_engine())
    test_results.append(await test_consensus_rewards_analyzer())
    test_results.append(await test_integration())

    # Summary
    passed = sum(test_results)
    total = len(test_results)

    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All Algorand Base Rates Engine tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)