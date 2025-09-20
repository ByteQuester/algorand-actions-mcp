"""
Digital Asset Constants and Configuration (Configuration-driven Version)

This module provides a configuration-driven approach to digital asset constants,
replacing hardcoded values with configurable parameters.
"""

from typing import Dict, Any
from pathlib import Path
import sys

# Import from common shared modules
from ...common.models.blockchain_collateral_models import DigitalCollateralType
from .config import load_config, DigitalAssetValuationConfig


class ConfigurableDigitalAssetConstants:
    """
    Configuration-driven digital asset constants
    """

    def __init__(self, config_path: Path = None):
        """Initialize with configuration"""
        self.config = load_config(config_path)

    @property
    def default_collateral_ratios(self) -> Dict[DigitalCollateralType, float]:
        """Get collateral ratios mapped to enum types"""
        return {
            DigitalCollateralType.ALGO_NATIVE: self.config.default_collateral_ratios.algo_native,
            DigitalCollateralType.STABLECOIN: self.config.default_collateral_ratios.stablecoin,
            DigitalCollateralType.ASA_TOKEN: self.config.default_collateral_ratios.asa_token,
            DigitalCollateralType.GOVERNANCE_TOKEN: self.config.default_collateral_ratios.governance_token,
            DigitalCollateralType.LP_TOKEN: self.config.default_collateral_ratios.lp_token,
            DigitalCollateralType.LIQUID_STAKING: self.config.default_collateral_ratios.liquid_staking,
        }

    @property
    def maintenance_ratios(self) -> Dict[DigitalCollateralType, float]:
        """Get maintenance ratios mapped to enum types"""
        return {
            DigitalCollateralType.ALGO_NATIVE: self.config.maintenance_ratios.algo_native,
            DigitalCollateralType.STABLECOIN: self.config.maintenance_ratios.stablecoin,
            DigitalCollateralType.ASA_TOKEN: self.config.maintenance_ratios.asa_token,
            DigitalCollateralType.GOVERNANCE_TOKEN: self.config.maintenance_ratios.governance_token,
            DigitalCollateralType.LP_TOKEN: self.config.maintenance_ratios.lp_token,
            DigitalCollateralType.LIQUID_STAKING: self.config.maintenance_ratios.liquid_staking,
        }

    @property
    def liquidation_penalties(self) -> Dict[DigitalCollateralType, float]:
        """Get liquidation penalties mapped to enum types"""
        return {
            DigitalCollateralType.ALGO_NATIVE: self.config.liquidation_penalties.algo_native,
            DigitalCollateralType.STABLECOIN: self.config.liquidation_penalties.stablecoin,
            DigitalCollateralType.ASA_TOKEN: self.config.liquidation_penalties.asa_token,
            DigitalCollateralType.GOVERNANCE_TOKEN: self.config.liquidation_penalties.governance_token,
            DigitalCollateralType.LP_TOKEN: self.config.liquidation_penalties.lp_token,
            DigitalCollateralType.LIQUID_STAKING: self.config.liquidation_penalties.liquid_staking,
        }

    @property
    def default_haircuts(self) -> Dict[DigitalCollateralType, float]:
        """Get default haircuts mapped to enum types"""
        return {
            DigitalCollateralType.ALGO_NATIVE: self.config.default_haircuts.algo_native,
            DigitalCollateralType.STABLECOIN: self.config.default_haircuts.stablecoin,
            DigitalCollateralType.ASA_TOKEN: self.config.default_haircuts.asa_token,
            DigitalCollateralType.GOVERNANCE_TOKEN: self.config.default_haircuts.governance_token,
            DigitalCollateralType.LP_TOKEN: self.config.default_haircuts.lp_token,
            DigitalCollateralType.LIQUID_STAKING: self.config.default_haircuts.liquid_staking,
        }

    @property
    def risk_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get risk parameters"""
        result = {}
        for risk_level, params in self.config.risk_parameters.items():
            result[risk_level] = {
                "max_volatility_30d": params.max_volatility_30d,
                "min_liquidity_tier": params.min_liquidity_tier,
                "max_correlation": params.max_correlation,
                "min_market_cap": params.min_market_cap,
            }
        return result

    @property
    def liquidation_thresholds(self) -> Dict[str, Any]:
        """Get liquidation thresholds"""
        return {
            "warning_threshold": self.config.liquidation_thresholds.warning_threshold,
            "urgent_threshold": self.config.liquidation_thresholds.urgent_threshold,
            "auto_liquidation": self.config.liquidation_thresholds.auto_liquidation,
            "max_liquidation_time": self.config.liquidation_thresholds.max_liquidation_time,
            "preferred_liquidation_time": self.config.liquidation_thresholds.preferred_liquidation_time,
        }

    @property
    def default_oracle_config(self) -> Dict[str, Any]:
        """Get oracle configuration"""
        return {
            "primary_oracle": self.config.oracle_config.primary_oracle,
            "backup_oracles": self.config.oracle_config.backup_oracles,
            "update_frequency": self.config.oracle_config.update_frequency,
            "reliability_threshold": self.config.oracle_config.reliability_threshold,
            "max_price_deviation": self.config.oracle_config.max_price_deviation,
            "fallback_strategy": self.config.oracle_config.fallback_strategy,
        }

    @property
    def algorand_assets(self) -> Dict[str, Dict[str, Any]]:
        """Get Algorand assets configuration"""
        return self.config.algorand_assets

    @property
    def stress_test_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Get stress test scenarios"""
        return self.config.stress_test_scenarios

    @property
    def diversification_targets(self) -> Dict[str, Any]:
        """Get diversification targets"""
        return {
            "single_asset_max": self.config.diversification_targets.single_asset_max,
            "asset_type_max": self.config.diversification_targets.asset_type_max,
            "min_asset_count": self.config.diversification_targets.min_asset_count,
            "correlation_limit": self.config.diversification_targets.correlation_limit,
            "liquidity_reserve": self.config.diversification_targets.liquidity_reserve,
        }

    @property
    def market_condition_multipliers(self) -> Dict[str, Dict[str, float]]:
        """Get market condition multipliers"""
        result = {}
        for condition, multiplier in self.config.market_condition_multipliers.items():
            result[condition] = {
                "collateral_ratio_adjustment": multiplier.collateral_ratio_adjustment,
                "liquidation_buffer": multiplier.liquidation_buffer,
            }
        return result

    def get_mcp_service_url(self, service_name: str) -> str:
        """Get MCP service URL"""
        if service_name == "algorand_reader":
            return self.config.mcp_services.algorand_reader_url
        elif service_name == "market_data":
            return self.config.mcp_services.market_data_url
        else:
            raise ValueError(f"Unknown MCP service: {service_name}")

    def get_fallback_price(self, asset_symbol: str) -> float:
        """Get fallback price for an asset"""
        return self.config.fallback_prices.get(asset_symbol, 0.0)

    def get_volatility_estimate(self, asset_symbol: str) -> Dict[str, float]:
        """Get volatility estimates for an asset"""
        return self.config.volatility_estimates.get(
            asset_symbol,
            self.config.volatility_estimates['default']
        )

    def get_liquidity_estimate(self, asset_symbol: str) -> Dict[str, Any]:
        """Get liquidity estimates for an asset"""
        return self.config.liquidity_estimates.get(
            asset_symbol,
            self.config.liquidity_estimates['default']
        )


# Create a global instance for backward compatibility
_default_constants = None

def get_default_constants() -> ConfigurableDigitalAssetConstants:
    """Get the default constants instance"""
    global _default_constants
    if _default_constants is None:
        _default_constants = ConfigurableDigitalAssetConstants()
    return _default_constants

# Expose the constants for backward compatibility
def get_default_collateral_ratios():
    return get_default_constants().default_collateral_ratios

def get_maintenance_ratios():
    return get_default_constants().maintenance_ratios

def get_liquidation_penalties():
    return get_default_constants().liquidation_penalties

def get_default_haircuts():
    return get_default_constants().default_haircuts

def get_risk_parameters():
    return get_default_constants().risk_parameters

def get_liquidation_thresholds():
    return get_default_constants().liquidation_thresholds

def get_default_oracle_config():
    return get_default_constants().default_oracle_config

def get_algorand_assets():
    return get_default_constants().algorand_assets

def get_stress_test_scenarios():
    return get_default_constants().stress_test_scenarios

def get_diversification_targets():
    return get_default_constants().diversification_targets

def get_market_condition_multipliers():
    return get_default_constants().market_condition_multipliers