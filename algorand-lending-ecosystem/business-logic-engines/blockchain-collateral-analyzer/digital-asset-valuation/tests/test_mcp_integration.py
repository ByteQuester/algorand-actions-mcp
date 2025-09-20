#!/usr/bin/env python3
"""
Test MCP Integration for Digital Asset Valuation Engine
"""

import sys
from pathlib import Path
import asyncio
import json
import requests
from unittest.mock import patch, Mock

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.engine import DigitalAssetValuationEngine
from ...common.models.blockchain_collateral_models import DigitalCollateralType


def test_mcp_service_urls():
    """Test MCP service URL configuration"""
    print("Testing MCP service URL configuration...")

    engine = DigitalAssetValuationEngine()

    # Test configured URLs
    assert engine.config.mcp_services.algorand_reader_url == "http://localhost:8002"
    assert engine.config.mcp_services.market_data_url == "http://localhost:8003"

    print("✓ MCP service URLs configured correctly")


async def test_price_fetching_with_mock():
    """Test price fetching with mocked HTTP responses"""
    print("Testing price fetching with mock responses...")

    engine = DigitalAssetValuationEngine()

    # Mock successful price response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'price': 0.28, 'symbol': 'ALGO'}

    with patch('requests.get', return_value=mock_response) as mock_get:
        price = await engine.get_asset_price('ALGO')

        # Verify the request was made to the correct URL
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert called_url == "http://localhost:8003/price/ALGO"

        # Verify price was returned correctly
        assert price == 0.28

    print("✓ Price fetching with successful response works correctly")


async def test_price_fallback():
    """Test price fallback when MCP service fails"""
    print("Testing price fallback mechanism...")

    engine = DigitalAssetValuationEngine()

    # Mock failed HTTP response
    with patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error")):
        price = await engine.get_asset_price('ALGO')

        # Should fall back to configured fallback price
        assert price == 0.25  # From config fallback_prices

    print("✓ Price fallback mechanism works correctly")


async def test_unknown_asset_fallback():
    """Test handling of unknown assets"""
    print("Testing unknown asset handling...")

    engine = DigitalAssetValuationEngine()

    # Mock failed HTTP response for unknown asset
    with patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error")):
        price = await engine.get_asset_price('UNKNOWN_ASSET')

        # Should return None for unknown assets with no fallback
        assert price is None

    print("✓ Unknown asset handling works correctly")


async def test_portfolio_analysis_with_mock():
    """Test full portfolio analysis with mocked prices"""
    print("Testing portfolio analysis with mocked prices...")

    engine = DigitalAssetValuationEngine()

    # Mock price responses for different assets
    def mock_get(url, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200

        if "ALGO" in url:
            mock_response.json.return_value = {'price': 0.28, 'symbol': 'ALGO'}
        elif "USDC" in url:
            mock_response.json.return_value = {'price': 1.00, 'symbol': 'USDC'}
        else:
            mock_response.status_code = 404

        return mock_response

    portfolio_data = [
        {'symbol': 'ALGO', 'quantity': 10000},
        {'symbol': 'USDC', 'quantity': 1000}
    ]

    with patch('requests.get', side_effect=mock_get):
        result = await engine.analyze_portfolio_collateral(
            portfolio_data=portfolio_data,
            loan_amount_usd=2000,
            market_conditions="normal"
        )

        # Verify analysis result structure
        assert result.loan_amount_usd == 2000
        assert result.collateral_portfolio is not None
        assert len(result.collateral_portfolio.positions) == 2
        assert result.is_sufficient is not None
        assert result.risk_level in ["low", "medium", "high", "critical"]

        # Verify positions were created correctly
        algo_position = next(p for p in result.collateral_portfolio.positions if p.asset.symbol == 'ALGO')
        usdc_position = next(p for p in result.collateral_portfolio.positions if p.asset.symbol == 'USDC')

        assert algo_position.quantity == 10000
        assert usdc_position.quantity == 1000
        assert algo_position.value_usd == 2800  # 10000 * 0.28
        assert usdc_position.value_usd == 1000  # 1000 * 1.00

    print("✓ Portfolio analysis with mocked prices works correctly")


def test_asset_creation():
    """Test digital asset creation with configuration"""
    print("Testing digital asset creation...")

    engine = DigitalAssetValuationEngine()

    # Test creating ALGO asset
    algo_asset = engine.create_digital_asset('ALGO', 0.28)

    assert algo_asset.symbol == 'ALGO'
    assert algo_asset.name == 'Algorand'
    assert algo_asset.asset_type == DigitalCollateralType.ALGO_NATIVE
    assert algo_asset.current_price_usd == 0.28
    assert algo_asset.is_native_algo == True
    assert algo_asset.volatility_metrics.volatility_30d == 0.45  # From config

    # Test creating USDC asset
    usdc_asset = engine.create_digital_asset('USDC', 1.00)

    assert usdc_asset.symbol == 'USDC'
    assert usdc_asset.name == 'USD Coin'
    assert usdc_asset.asset_type == DigitalCollateralType.STABLECOIN
    assert usdc_asset.current_price_usd == 1.00
    assert usdc_asset.is_native_algo == False
    assert usdc_asset.volatility_metrics.volatility_30d == 0.02  # From config

    print("✓ Digital asset creation works correctly")


def test_collateral_position_creation():
    """Test collateral position creation with risk adjustments"""
    print("Testing collateral position creation...")

    engine = DigitalAssetValuationEngine()

    # Create an asset
    algo_asset = engine.create_digital_asset('ALGO', 0.25)

    # Create a position
    position = engine.create_collateral_position(algo_asset, 1000, "normal")

    assert position.asset.symbol == 'ALGO'
    assert position.quantity == 1000
    assert position.value_usd == 250  # 1000 * 0.25

    # Adjusted value should be less due to haircut
    assert position.adjusted_value_usd < position.value_usd
    assert position.haircut_percentage > 0

    # Test different market conditions
    bear_position = engine.create_collateral_position(algo_asset, 1000, "bear")

    # Bear market should have higher haircut
    assert bear_position.haircut_percentage > position.haircut_percentage
    assert bear_position.adjusted_value_usd < position.adjusted_value_usd

    print("✓ Collateral position creation works correctly")


def test_stress_testing():
    """Test stress testing functionality"""
    print("Testing stress testing functionality...")

    engine = DigitalAssetValuationEngine()

    # Create some positions
    algo_asset = engine.create_digital_asset('ALGO', 0.25)
    usdc_asset = engine.create_digital_asset('USDC', 1.00)

    positions = [
        engine.create_collateral_position(algo_asset, 1000, "normal"),
        engine.create_collateral_position(usdc_asset, 500, "normal")
    ]

    # Run market crash stress test
    stress_result = engine.run_stress_test(positions, "market_crash")

    assert stress_result['scenario_name'] == 'market_crash'
    assert 'scenario_description' in stress_result
    assert 'original_total_value' in stress_result
    assert 'stressed_total_value' in stress_result
    assert 'value_impact_percentage' in stress_result

    # Market crash should reduce portfolio value
    assert stress_result['stressed_total_value'] < stress_result['original_total_value']
    assert stress_result['value_impact_percentage'] < 0

    print("✓ Stress testing functionality works correctly")


async def run_all_tests():
    """Run all MCP integration tests"""
    print("Running Digital Asset Valuation Engine MCP Integration Tests")
    print("=" * 70)

    try:
        test_mcp_service_urls()
        await test_price_fetching_with_mock()
        await test_price_fallback()
        await test_unknown_asset_fallback()
        await test_portfolio_analysis_with_mock()
        test_asset_creation()
        test_collateral_position_creation()
        test_stress_testing()

        print("\n" + "=" * 70)
        print("✅ All MCP integration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)