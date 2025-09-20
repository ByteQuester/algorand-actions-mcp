#!/usr/bin/env python3
"""
Test Engine Functionality for Liquidation Scenarios Engine

This script tests the main engine functionality using configuration.
"""

import sys
import os
from pathlib import Path
from typing import List
from dataclasses import dataclass

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from liquidation_scenarios.core.liquidation_scenarios_engine import (
    LiquidationScenariosEngine,
    create_liquidation_engine
)
from liquidation_scenarios.core.config import load_config


# Mock data classes for testing
@dataclass
class MockVolatilityMetrics:
    volatility_30d: float = 0.45
    volatility_7d: float = 0.35
    max_drawdown_30d: float = 0.25
    value_at_risk_95: float = 0.15


@dataclass
class MockLiquidityMetrics:
    liquidity_tier: str = "high"
    daily_volume_usd: float = 50_000_000
    market_cap_usd: float = 2_000_000_000
    depth_1_percent: float = 1_000_000


@dataclass
class MockDigitalAsset:
    symbol: str = "ALGO"
    price_usd: float = 0.25
    volatility_metrics: MockVolatilityMetrics = None
    liquidity_metrics: MockLiquidityMetrics = None

    def __post_init__(self):
        if self.volatility_metrics is None:
            self.volatility_metrics = MockVolatilityMetrics()
        if self.liquidity_metrics is None:
            self.liquidity_metrics = MockLiquidityMetrics()


@dataclass
class MockCollateralPosition:
    asset: MockDigitalAsset
    amount: float
    adjusted_value_usd: float

    def __init__(self, symbol: str = "ALGO", amount: float = 1000, price: float = 0.25):
        self.asset = MockDigitalAsset(symbol=symbol, price_usd=price)
        self.amount = amount
        self.adjusted_value_usd = amount * price


def test_engine_initialization():
    """Test that the engine initializes correctly"""
    print("Testing engine initialization...")

    # Test with default config
    engine = LiquidationScenariosEngine()
    assert engine.config is not None
    assert engine.algorand_reader_url == "http://localhost:8002"
    assert engine.market_data_url == "http://localhost:8003"

    # Test with custom config
    config = load_config()
    engine2 = LiquidationScenariosEngine(config)
    assert engine2.config == config

    # Test convenience function
    engine3 = create_liquidation_engine()
    assert engine3.config is not None

    print("✓ Engine initialization test passed")


def test_slippage_calculation():
    """Test slippage calculation with configuration"""
    print("Testing slippage calculation...")

    engine = LiquidationScenariosEngine()

    # Test normal liquidation
    slippage = engine.calculate_slippage(
        position_size_usd=100_000,
        daily_volume_usd=50_000_000,
        market_depth_1pct=1_000_000,
        liquidation_speed_factor=1.0
    )
    assert 0.0 <= slippage <= engine.config.slippage_calculation.max_slippage_cap

    # Test urgent liquidation (higher slippage)
    urgent_slippage = engine.calculate_slippage(
        position_size_usd=100_000,
        daily_volume_usd=50_000_000,
        market_depth_1pct=1_000_000,
        liquidation_speed_factor=2.0
    )
    assert urgent_slippage >= slippage

    # Test large position (should have higher slippage)
    large_slippage = engine.calculate_slippage(
        position_size_usd=10_000_000,
        daily_volume_usd=50_000_000,
        market_depth_1pct=1_000_000,
        liquidation_speed_factor=1.0
    )
    assert large_slippage >= slippage

    print("✓ Slippage calculation test passed")


def test_execution_time_estimation():
    """Test execution time estimation"""
    print("Testing execution time estimation...")

    engine = LiquidationScenariosEngine()

    # Test small position
    time_small = engine.estimate_execution_time(
        position_size_usd=50_000,      # 0.1% of daily volume
        daily_volume_usd=50_000_000,
        liquidity_tier="high",
        urgency_level="normal"
    )
    assert engine.config.liquidation_timing.time_constraints['min_hours'] <= time_small <= engine.config.liquidation_timing.time_constraints['max_hours']

    # Test large position (should take longer)
    time_large = engine.estimate_execution_time(
        position_size_usd=5_000_000,   # 10% of daily volume
        daily_volume_usd=50_000_000,
        liquidity_tier="high",
        urgency_level="normal"
    )
    assert time_large >= time_small

    # Test urgent liquidation (should be faster)
    time_urgent = engine.estimate_execution_time(
        position_size_usd=5_000_000,
        daily_volume_usd=50_000_000,
        liquidity_tier="high",
        urgency_level="immediate"
    )
    assert time_urgent <= time_large

    # Test low liquidity (should take longer)
    time_low_liq = engine.estimate_execution_time(
        position_size_usd=5_000_000,
        daily_volume_usd=50_000_000,
        liquidity_tier="low",
        urgency_level="normal"
    )
    assert time_low_liq >= time_large

    print("✓ Execution time estimation test passed")


def test_liquidation_plan_creation():
    """Test liquidation plan creation"""
    print("Testing liquidation plan creation...")

    engine = LiquidationScenariosEngine()

    # Create mock positions
    positions = [
        MockCollateralPosition("ALGO", 1000, 0.25),   # $250
        MockCollateralPosition("USDC", 500, 1.0),     # $500
        MockCollateralPosition("TEST", 100, 5.0)      # $500
    ]

    # Test immediate strategy
    immediate_plan = engine.create_liquidation_plan(
        positions,
        liquidation_target_usd=1000,
        strategy="immediate"
    )
    assert len(immediate_plan) > 0
    assert all(plan.asset_symbol in ["ALGO", "USDC", "TEST"] for plan in immediate_plan)

    # Test gradual strategy
    gradual_plan = engine.create_liquidation_plan(
        positions,
        liquidation_target_usd=1000,
        strategy="gradual"
    )
    assert len(gradual_plan) > 0

    # Test selective strategy
    selective_plan = engine.create_liquidation_plan(
        positions,
        liquidation_target_usd=1000,
        strategy="selective"
    )
    assert len(selective_plan) > 0

    print("✓ Liquidation plan creation test passed")


def test_feasibility_assessment():
    """Test liquidation feasibility assessment"""
    print("Testing feasibility assessment...")

    engine = LiquidationScenariosEngine()

    # Create a high-liquidity position
    position = MockCollateralPosition("ALGO", 1000, 0.25)

    # Test small liquidation (should be very feasible)
    small_assessment = engine.assess_feasibility(
        position,
        required_liquidation_usd=10_000,  # Small relative to daily volume
        time_constraint_hours=24.0
    )
    assert small_assessment['feasibility_level'] in ['very_high', 'high']
    assert small_assessment['time_feasible'] == True
    assert 0.0 <= small_assessment['confidence_score'] <= 1.0

    # Test large liquidation (should be less feasible)
    large_assessment = engine.assess_feasibility(
        position,
        required_liquidation_usd=20_000_000,  # Large relative to daily volume
        time_constraint_hours=24.0
    )
    assert small_assessment['confidence_score'] >= large_assessment['confidence_score']

    print("✓ Feasibility assessment test passed")


def test_emergency_scenarios():
    """Test emergency scenario parameters"""
    print("Testing emergency scenarios...")

    engine = LiquidationScenariosEngine()

    # Test oracle failure scenario
    oracle_params = engine.get_emergency_parameters('oracle_failure')
    assert 'fallback_discount' in oracle_params
    assert 'max_liquidation_delay' in oracle_params
    assert 'confidence_penalty' in oracle_params

    # Test volatility spike scenario
    volatility_params = engine.get_emergency_parameters('volatility_spike')
    assert 'volatility_threshold' in volatility_params
    assert 'slippage_multiplier' in volatility_params
    assert 'urgency_override' in volatility_params

    # Test black swan scenario
    black_swan_params = engine.get_emergency_parameters('black_swan')
    assert 'market_crash_threshold' in black_swan_params
    assert 'emergency_slippage_tolerance' in black_swan_params

    # Test invalid scenario
    try:
        engine.get_emergency_parameters('invalid_scenario')
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("✓ Emergency scenarios test passed")


def test_flash_loan_parameters():
    """Test flash loan parameter calculation"""
    print("Testing flash loan parameters...")

    engine = LiquidationScenariosEngine()

    if engine.config.flash_loan_integration.enabled:
        # Test valid flash loan
        flash_params = engine.calculate_flash_loan_parameters(
            liquidation_amount=1_000_000,
            protocol="aave"
        )
        assert 'loan_amount' in flash_params
        assert 'fee_amount' in flash_params
        assert 'estimated_gas_cost' in flash_params
        assert 'total_cost' in flash_params
        assert flash_params['loan_amount'] == 1_000_000

        # Test exceeding max amount
        try:
            engine.calculate_flash_loan_parameters(
                liquidation_amount=20_000_000,  # Exceeds max
                protocol="aave"
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        # Test unsupported protocol
        try:
            engine.calculate_flash_loan_parameters(
                liquidation_amount=1_000_000,
                protocol="unsupported"
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    print("✓ Flash loan parameters test passed")


def test_auction_parameters():
    """Test auction parameter retrieval"""
    print("Testing auction parameters...")

    engine = LiquidationScenariosEngine()

    # Test dutch auction
    if engine.config.auction_parameters.dutch_auction.enabled:
        dutch_params = engine.get_auction_parameters("dutch")
        assert dutch_params['type'] == 'dutch'
        assert 'starting_discount' in dutch_params
        assert 'discount_increment' in dutch_params
        assert 'time_interval_minutes' in dutch_params
        assert 'max_discount' in dutch_params

    # Test sealed bid auction
    try:
        sealed_params = engine.get_auction_parameters("sealed_bid")
        if engine.config.auction_parameters.sealed_bid_auction.enabled:
            assert sealed_params['type'] == 'sealed_bid'
            assert 'minimum_bid_increment' in sealed_params
    except ValueError:
        # Expected if sealed bid auction is disabled
        pass

    # Test invalid auction type
    try:
        engine.get_auction_parameters("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("✓ Auction parameters test passed")


def test_recovery_rate_calculation():
    """Test recovery rate calculation"""
    print("Testing recovery rate calculation...")

    engine = LiquidationScenariosEngine()

    # Test different asset types
    highly_liquid_rate = engine.calculate_recovery_rate("highly_liquid", "normal_market")
    liquid_rate = engine.calculate_recovery_rate("liquid", "normal_market")
    illiquid_rate = engine.calculate_recovery_rate("illiquid", "normal_market")

    assert highly_liquid_rate >= liquid_rate >= illiquid_rate
    assert all(0.0 <= rate <= 1.0 for rate in [highly_liquid_rate, liquid_rate, illiquid_rate])

    # Test different market conditions
    bull_rate = engine.calculate_recovery_rate("liquid", "bull_market")
    normal_rate = engine.calculate_recovery_rate("liquid", "normal_market")
    bear_rate = engine.calculate_recovery_rate("liquid", "bear_market")
    crisis_rate = engine.calculate_recovery_rate("liquid", "crisis_market")

    assert bull_rate >= normal_rate >= bear_rate >= crisis_rate

    print("✓ Recovery rate calculation test passed")


def test_penalty_structure():
    """Test penalty structure retrieval"""
    print("Testing penalty structure...")

    engine = LiquidationScenariosEngine()

    penalties = engine.get_penalty_structure()

    expected_keys = [
        'borrower_penalty_rate',
        'liquidator_bonus_rate',
        'protocol_fee_rate',
        'insurance_fund_rate'
    ]

    for key in expected_keys:
        assert key in penalties
        assert 0.0 <= penalties[key] <= 1.0

    print("✓ Penalty structure test passed")


def test_risk_threshold_checking():
    """Test risk threshold checking"""
    print("Testing risk threshold checking...")

    engine = LiquidationScenariosEngine()

    # Test normal conditions (no breaches)
    normal_checks = engine.check_risk_thresholds(
        position_concentration=0.20,  # Below limit
        portfolio_correlation=0.50,   # Below limit
        volatility_multiplier=1.5,    # Below threshold
        liquidity_ratio=0.8           # Above threshold
    )

    assert normal_checks['concentration_breach'] == False
    assert normal_checks['correlation_breach'] == False
    assert normal_checks['volatility_spike'] == False
    assert normal_checks['liquidity_drop'] == False

    # Test breach conditions
    breach_checks = engine.check_risk_thresholds(
        position_concentration=0.80,  # Above limit
        portfolio_correlation=0.90,   # Above limit
        volatility_multiplier=3.0,    # Above threshold
        liquidity_ratio=0.3           # Below threshold
    )

    assert breach_checks['concentration_breach'] == True
    assert breach_checks['correlation_breach'] == True
    assert breach_checks['volatility_spike'] == True
    assert breach_checks['liquidity_drop'] == True

    print("✓ Risk threshold checking test passed")


def test_config_reloading():
    """Test configuration reloading"""
    print("Testing configuration reloading...")

    engine = LiquidationScenariosEngine()
    original_url = engine.algorand_reader_url

    # Reload should not fail
    engine.reload_config()
    assert engine.algorand_reader_url == original_url

    print("✓ Configuration reloading test passed")


def run_all_tests():
    """Run all engine functionality tests"""
    print("=" * 60)
    print("LIQUIDATION SCENARIOS ENGINE - FUNCTIONALITY TESTS")
    print("=" * 60)

    tests = [
        test_engine_initialization,
        test_slippage_calculation,
        test_execution_time_estimation,
        test_liquidation_plan_creation,
        test_feasibility_assessment,
        test_emergency_scenarios,
        test_flash_loan_parameters,
        test_auction_parameters,
        test_recovery_rate_calculation,
        test_penalty_structure,
        test_risk_threshold_checking,
        test_config_reloading
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)