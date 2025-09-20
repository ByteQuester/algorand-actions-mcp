#!/usr/bin/env python3
"""
Test Configuration System for Digital Asset Valuation Engine
"""

import sys
from pathlib import Path
import tempfile
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.config import (
    DigitalAssetValuationConfig,
    DigitalAssetConfigLoader,
    load_config
)
from core.constants import ConfigurableDigitalAssetConstants
from core.calculator import ConfigurableDigitalCollateralCalculator
from core.engine import DigitalAssetValuationEngine
from ...common.models.blockchain_collateral_models import DigitalCollateralType


def test_default_config():
    """Test loading default configuration"""
    print("Testing default configuration loading...")

    config = DigitalAssetValuationConfig()

    # Test basic configuration values
    assert config.mcp_services.algorand_reader_url == "http://localhost:8002"
    assert config.mcp_services.market_data_url == "http://localhost:8003"
    assert config.default_collateral_ratios.algo_native == 1.5
    assert config.default_collateral_ratios.stablecoin == 1.1

    print("✓ Default configuration loaded successfully")


def test_yaml_config_loading():
    """Test loading configuration from YAML file"""
    print("Testing YAML configuration loading...")

    # Create a temporary config file
    test_config = {
        'mcp_services': {
            'algorand_reader_url': 'http://test:8002',
            'market_data_url': 'http://test:8003'
        },
        'default_collateral_ratios': {
            'algo_native': 1.8,
            'stablecoin': 1.2
        },
        'analysis': {
            'safety_buffer': 0.15,
            'cache_expiry_minutes': 10
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        temp_config_path = Path(f.name)

    try:
        # Load config from file
        config = load_config(temp_config_path)

        # Test overridden values
        assert config.mcp_services.algorand_reader_url == 'http://test:8002'
        assert config.mcp_services.market_data_url == 'http://test:8003'
        assert config.default_collateral_ratios.algo_native == 1.8
        assert config.default_collateral_ratios.stablecoin == 1.2
        assert config.analysis.safety_buffer == 0.15
        assert config.analysis.cache_expiry_minutes == 10

        # Test that non-overridden values remain default
        assert config.default_collateral_ratios.asa_token == 2.0  # Should be default

        print("✓ YAML configuration loaded and merged successfully")

    finally:
        # Clean up
        temp_config_path.unlink()


def test_constants_class():
    """Test the configurable constants class"""
    print("Testing configurable constants class...")

    constants = ConfigurableDigitalAssetConstants()

    # Test property access
    collateral_ratios = constants.default_collateral_ratios
    assert DigitalCollateralType.ALGO_NATIVE in collateral_ratios
    assert collateral_ratios[DigitalCollateralType.ALGO_NATIVE] == 1.5

    # Test fallback prices
    algo_price = constants.get_fallback_price('ALGO')
    assert algo_price == 0.25

    # Test volatility estimates
    algo_volatility = constants.get_volatility_estimate('ALGO')
    assert 'volatility_30d' in algo_volatility
    assert algo_volatility['volatility_30d'] == 0.45

    # Test default volatility for unknown asset
    unknown_volatility = constants.get_volatility_estimate('UNKNOWN')
    assert unknown_volatility['volatility_30d'] == 0.60  # Should be default

    print("✓ Configurable constants class working correctly")


def test_calculator_with_config():
    """Test the configurable calculator"""
    print("Testing configurable calculator...")

    calculator = ConfigurableDigitalCollateralCalculator()

    # Test that calculator uses configuration
    # This is more of a smoke test to ensure it initializes properly
    assert calculator.config is not None
    assert calculator.constants is not None

    # Test basic calculation methods exist
    assert hasattr(calculator, 'calculate_asset_haircut')
    assert hasattr(calculator, 'assess_liquidation_urgency')
    assert hasattr(calculator, 'calculate_portfolio_diversification')

    print("✓ Configurable calculator initialized correctly")


def test_engine_initialization():
    """Test the valuation engine initialization"""
    print("Testing valuation engine initialization...")

    engine = DigitalAssetValuationEngine()

    # Test that engine components are properly initialized
    assert engine.config is not None
    assert engine.constants is not None
    assert engine.calculator is not None

    # Test configuration summary
    summary = engine.get_configuration_summary()
    assert 'mcp_services' in summary
    assert 'collateral_ratios' in summary
    assert 'analysis_parameters' in summary
    assert 'supported_assets' in summary

    # Test MCP URLs are correct
    assert summary['mcp_services']['algorand_reader_url'] == 'http://localhost:8002'
    assert summary['mcp_services']['market_data_url'] == 'http://localhost:8003'

    print("✓ Valuation engine initialized correctly")


def test_asset_classification():
    """Test asset classification logic"""
    print("Testing asset classification...")

    engine = DigitalAssetValuationEngine()

    # Test known assets
    algo_type = engine.get_asset_classification('ALGO')
    assert algo_type == DigitalCollateralType.ALGO_NATIVE

    usdc_type = engine.get_asset_classification('USDC')
    assert usdc_type == DigitalCollateralType.STABLECOIN

    # Test unknown asset (should default to ASA_TOKEN)
    unknown_type = engine.get_asset_classification('UNKNOWN')
    assert unknown_type == DigitalCollateralType.ASA_TOKEN

    print("✓ Asset classification working correctly")


def test_recommended_ratios():
    """Test recommended collateral ratio calculations"""
    print("Testing recommended collateral ratios...")

    engine = DigitalAssetValuationEngine()

    # Test different scenarios
    algo_ratio_normal = engine.get_recommended_collateral_ratio(
        DigitalCollateralType.ALGO_NATIVE,
        portfolio_diversification=0.5,
        market_conditions="normal"
    )

    algo_ratio_bear = engine.get_recommended_collateral_ratio(
        DigitalCollateralType.ALGO_NATIVE,
        portfolio_diversification=0.5,
        market_conditions="bear"
    )

    # Bear market should require higher ratio
    assert algo_ratio_bear > algo_ratio_normal

    # Test diversification impact
    algo_ratio_diversified = engine.get_recommended_collateral_ratio(
        DigitalCollateralType.ALGO_NATIVE,
        portfolio_diversification=0.8,  # High diversification
        market_conditions="normal"
    )

    algo_ratio_concentrated = engine.get_recommended_collateral_ratio(
        DigitalCollateralType.ALGO_NATIVE,
        portfolio_diversification=0.2,  # Low diversification
        market_conditions="normal"
    )

    # High diversification should allow lower ratio
    assert algo_ratio_diversified < algo_ratio_concentrated

    print("✓ Recommended collateral ratios calculated correctly")


def run_all_tests():
    """Run all configuration tests"""
    print("Running Digital Asset Valuation Engine Configuration Tests")
    print("=" * 60)

    try:
        test_default_config()
        test_yaml_config_loading()
        test_constants_class()
        test_calculator_with_config()
        test_engine_initialization()
        test_asset_classification()
        test_recommended_ratios()

        print("\n" + "=" * 60)
        print("✅ All tests passed! Configuration system is working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)