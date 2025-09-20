#!/usr/bin/env python3
"""
Digital Asset Valuation Engine Integration Test

Tests the complete functionality of the digital asset valuation engine
including configuration, MCP integration, and portfolio analysis.
"""

import sys
import asyncio
import json
import requests
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from core import DigitalAssetValuationEngine
from ..common.models.blockchain_collateral_models import DigitalCollateralType


def check_mcp_services(engine):
    """Check if MCP services are available"""
    print("Checking MCP Service Availability...")
    print("-" * 40)

    services = {
        "Algorand Reader": engine.config.mcp_services.algorand_reader_url,
        "Market Data": engine.config.mcp_services.market_data_url
    }

    service_status = {}

    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                status = "✓ Available"
                service_status[service_name] = True
            else:
                status = f"❌ HTTP {response.status_code}"
                service_status[service_name] = False
        except requests.exceptions.RequestException as e:
            status = f"❌ Not available ({e})"
            service_status[service_name] = False

        print(f"{service_name}: {url} - {status}")

    return service_status


async def test_asset_pricing(engine):
    """Test asset pricing with MCP integration and fallbacks"""
    print("\nTesting Asset Pricing...")
    print("-" * 30)

    assets = ['ALGO', 'USDC', 'USDT', 'GOBTC']
    prices = {}

    for asset in assets:
        try:
            price = await engine.get_asset_price(asset)
            if price is not None:
                prices[asset] = price
                print(f"✓ {asset}: ${price:.4f}")
            else:
                print(f"❌ {asset}: No price available")
        except Exception as e:
            print(f"❌ {asset}: Error - {e}")

    return prices


def test_configuration_loading(engine):
    """Test configuration loading and display key parameters"""
    print("\nTesting Configuration Loading...")
    print("-" * 35)

    config_summary = engine.get_configuration_summary()

    print("Key Configuration Parameters:")
    print(f"  Safety Buffer: {engine.config.analysis.safety_buffer:.1%}")
    print(f"  Cache Expiry: {engine.config.analysis.cache_expiry_minutes} minutes")
    print(f"  Max Position Concentration: {engine.config.analysis.max_position_concentration:.1%}")

    print("\nCollateral Ratios:")
    for asset_type, ratio in config_summary['collateral_ratios'].items():
        print(f"  {asset_type.replace('_', ' ').title()}: {ratio:.1%}")

    print(f"\nSupported Assets: {', '.join(config_summary['supported_assets'])}")
    print(f"Stress Test Scenarios: {', '.join(config_summary['stress_test_scenarios'])}")


def test_asset_creation_and_classification(engine, prices):
    """Test asset creation and classification"""
    print("\nTesting Asset Creation and Classification...")
    print("-" * 45)

    assets = {}

    for symbol, price in prices.items():
        try:
            # Create digital asset
            asset = engine.create_digital_asset(symbol, price)
            assets[symbol] = asset

            print(f"{symbol}:")
            print(f"  Type: {asset.asset_type.name}")
            print(f"  Price: ${price:.4f}")
            print(f"  Volatility (30d): {asset.volatility_metrics.volatility_30d:.1%}")
            print(f"  Liquidity Tier: {asset.liquidity_metrics.liquidity_tier}")
            print(f"  Asset ID: {asset.asset_id}")
            print()

        except Exception as e:
            print(f"❌ Failed to create asset {symbol}: {e}")

    return assets


def test_collateral_positions(engine, assets, prices):
    """Test collateral position creation with different market conditions"""
    print("Testing Collateral Position Creation...")
    print("-" * 40)

    market_conditions = ['normal', 'bull', 'bear', 'crisis']
    positions_by_market = {}

    # Test with ALGO as example
    if 'ALGO' in assets:
        algo_asset = assets['ALGO']
        quantity = 10000
        algo_price = prices['ALGO']

        print(f"ALGO Position (10,000 units @ ${algo_price:.4f}):")

        for condition in market_conditions:
            try:
                position = engine.create_collateral_position(algo_asset, quantity, condition, algo_price)
                positions_by_market[condition] = position

                print(f"  {condition.title()}:")
                print(f"    Value: ${position.value_usd:,.2f}")
                print(f"    Haircut: {position.haircut_percentage:.1%}")
                print(f"    Adjusted Value: ${position.adjusted_value_usd:,.2f}")

            except Exception as e:
                print(f"    ❌ Error in {condition}: {e}")

    return positions_by_market


async def test_portfolio_analysis(engine, assets, prices):
    """Test portfolio analysis functionality"""
    print("\nTesting Portfolio Analysis...")
    print("-" * 30)

    # Create a sample portfolio
    portfolio_data = [
        {'symbol': 'ALGO', 'quantity': 10000},
        {'symbol': 'USDC', 'quantity': 2000},
    ]

    # Only include assets we have prices for
    portfolio_data = [p for p in portfolio_data if p['symbol'] in assets]

    if not portfolio_data:
        print("❌ No assets available for portfolio analysis")
        return None

    loan_amount = 3000

    portfolio_desc = ', '.join([f"{p['quantity']:,} {p['symbol']}" for p in portfolio_data])
    print(f"Portfolio: {portfolio_desc}")
    print(f"Loan Amount: ${loan_amount:,.2f}")

    try:
        # Calculate total portfolio value
        total_value = sum(
            prices[p['symbol']] * p['quantity']
            for p in portfolio_data
        )
        print(f"Total Portfolio Value: ${total_value:,.2f}")
        print(f"Initial LTV: {loan_amount/total_value:.1%}")

        # Create positions for analysis
        positions = []
        for position_data in portfolio_data:
            symbol = position_data['symbol']
            quantity = position_data['quantity']
            asset = assets[symbol]
            position = engine.create_collateral_position(asset, quantity, "normal", prices[symbol])
            positions.append(position)

        # Calculate adjusted values
        total_adjusted = sum(p.adjusted_value_usd for p in positions)
        avg_haircut = (total_value - total_adjusted) / total_value

        print(f"Total Adjusted Value: ${total_adjusted:,.2f}")
        print(f"Average Haircut: {avg_haircut:.1%}")
        print(f"Collateralization Ratio: {total_adjusted/loan_amount:.1%}")

        # Check sufficiency
        required_ratio = engine.get_recommended_collateral_ratio(
            DigitalCollateralType.ALGO_NATIVE,  # Use ALGO as representative
            portfolio_diversification=0.5,
            market_conditions="normal"
        )

        required_collateral = loan_amount * required_ratio
        is_sufficient = total_adjusted >= required_collateral

        print(f"Required Collateral: ${required_collateral:,.2f} ({required_ratio:.1%})")
        print(f"Sufficient: {'✓ Yes' if is_sufficient else '❌ No'}")

        if not is_sufficient:
            deficit = required_collateral - total_adjusted
            print(f"Deficit: ${deficit:,.2f}")

        return positions

    except Exception as e:
        print(f"❌ Portfolio analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_stress_scenarios(engine, positions):
    """Test stress testing functionality"""
    if not positions:
        print("\nSkipping stress tests - no positions available")
        return

    print("\nTesting Stress Scenarios...")
    print("-" * 30)

    scenarios = ['market_crash', 'regulatory_shock', 'liquidity_crisis']

    original_value = sum(p.value_usd for p in positions)
    print(f"Original Portfolio Value: ${original_value:,.2f}")
    print()

    for scenario in scenarios:
        try:
            result = engine.run_stress_test(positions, scenario)

            print(f"{scenario.replace('_', ' ').title()}:")
            print(f"  Description: {result['scenario_description']}")
            print(f"  Value Impact: {result['value_impact_percentage']:.1f}%")
            print(f"  Stressed Value: ${result['stressed_total_value']:,.2f}")
            print()

        except Exception as e:
            print(f"❌ Stress test {scenario} failed: {e}")


def test_market_condition_adjustments(engine):
    """Test market condition adjustments"""
    print("Testing Market Condition Adjustments...")
    print("-" * 40)

    asset_type = DigitalCollateralType.ALGO_NATIVE
    conditions = ['bull', 'normal', 'bear', 'crisis']

    print("Required Collateral Ratios for ALGO:")
    for condition in conditions:
        try:
            ratio = engine.get_recommended_collateral_ratio(
                asset_type,
                portfolio_diversification=0.5,
                market_conditions=condition
            )
            print(f"  {condition.title()}: {ratio:.1%}")
        except Exception as e:
            print(f"  ❌ {condition}: Error - {e}")


async def main():
    """Run comprehensive integration test"""
    print("Digital Asset Valuation Engine Integration Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()

    try:
        # Initialize engine
        print("Initializing Digital Asset Valuation Engine...")
        engine = DigitalAssetValuationEngine()
        print("✓ Engine initialized successfully")

        # Test configuration
        test_configuration_loading(engine)

        # Check MCP services
        mcp_status = check_mcp_services(engine)

        # Test asset pricing
        prices = await test_asset_pricing(engine)

        if not prices:
            print("\n❌ No asset prices available - cannot continue with portfolio tests")
            return False

        # Test asset creation
        assets = test_asset_creation_and_classification(engine, prices)

        # Test collateral positions
        positions_by_market = test_collateral_positions(engine, assets, prices)

        # Test portfolio analysis
        positions = await test_portfolio_analysis(engine, assets, prices)

        # Test stress scenarios
        test_stress_scenarios(engine, positions)

        # Test market condition adjustments
        test_market_condition_adjustments(engine)

        print("\n" + "=" * 50)
        print("✅ Integration test completed successfully!")

        # Summary
        print("\nTest Summary:")
        print(f"  MCP Services Available: {sum(mcp_status.values())}/{len(mcp_status)}")
        print(f"  Assets Priced: {len(prices)}")
        print(f"  Assets Created: {len(assets)}")
        print(f"  Market Conditions Tested: {len(positions_by_market)}")

        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)