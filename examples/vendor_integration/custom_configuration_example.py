#!/usr/bin/env python3
"""
Custom Configuration Integration Example

This demonstrates advanced configuration patterns for the algorand-lending-business-logic
package, showing how to customize engines for different use cases and environments.

Features:
- Environment-specific configurations
- Custom engine parameters
- Configuration validation and testing
- Multi-tenant configuration management
- Dynamic configuration updates
- Configuration file management

Usage:
    python custom_configuration_example.py
"""

import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Add the vendor package to Python path (if not installed)
vendor_path = Path(__file__).parent / "algorand_lending_bl"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path.parent))

# Import lending business logic
from algorand_lending_bl import (
    create_lending_service,
    AlgorandLendingConfig,
    NetworkConfig,
    CollateralConfig,
    InterestRateConfig,
    LoanApprovalConfig,
    RiskAssessmentConfig,
    ServiceConfig,
    DEFAULT_CONFIG,
    create_testnet_config,
    create_mainnet_config,
    create_config_from_env,
    validate_config,
    LoanRequest,
    AlgorandAddress,
    ASAToken,
    VENDOR_INFO
)

# ============================================================================
# CUSTOM CONFIGURATION CLASSES
# ============================================================================

@dataclass
class TenantConfig:
    """Configuration for a specific tenant/client."""
    tenant_id: str
    name: str
    risk_tolerance: str  # conservative, moderate, aggressive
    max_loan_amount: int
    supported_assets: list
    custom_rates: Dict[str, float]
    special_rules: Dict[str, Any]

@dataclass
class EnvironmentConfig:
    """Environment-specific configuration."""
    environment: str  # development, staging, production
    debug_mode: bool
    rate_limits: Dict[str, int]
    feature_flags: Dict[str, bool]
    monitoring: Dict[str, str]

class ConfigurationManager:
    """Advanced configuration management system."""

    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # Configuration cache
        self._config_cache: Dict[str, AlgorandLendingConfig] = {}

        # Tenant configurations
        self._tenant_configs: Dict[str, TenantConfig] = {}

        # Environment configuration
        self._env_config: Optional[EnvironmentConfig] = None

    def create_conservative_config(self) -> AlgorandLendingConfig:
        """Create configuration for conservative lending."""
        return AlgorandLendingConfig(
            network=NetworkConfig(
                algod_token=os.getenv("ALGOD_TOKEN", ""),
                algod_server=os.getenv("ALGOD_SERVER", "https://testnet-api.algonode.cloud"),
                network_name="testnet"
            ),
            collateral=CollateralConfig(
                min_collateral_ratio=2.0,  # 200% collateralization
                liquidation_threshold=1.5,  # 150% liquidation
                max_ltv_ratio=0.5,  # 50% max LTV
                supported_assets=[0],  # ALGO only
                price_deviation_threshold=0.05,  # 5% price deviation
                enable_cross_collateral=False
            ),
            interest_rates=InterestRateConfig(
                base_rate=0.08,  # 8% base rate
                min_rate=0.05,  # 5% minimum
                max_rate=0.20,  # 20% maximum
                risk_multiplier=1.5,  # Conservative risk multiplier
                reputation_weight=0.3,
                collateral_weight=0.4,
                market_weight=0.3
            ),
            loan_approval=LoanApprovalConfig(
                min_loan_amount=100000,  # 0.1 ALGO minimum
                max_loan_amount=10000000,  # 10 ALGO maximum
                max_duration_days=30,  # 30 days max
                min_credit_score=0.7,  # High credit score required
                require_kyc=True,
                enable_automatic_approval=False
            ),
            risk_assessment=RiskAssessmentConfig(
                max_risk_score=0.6,  # Low risk tolerance
                enable_stress_testing=True,
                correlation_threshold=0.8,
                volatility_lookback_days=30,
                enable_portfolio_risk=True
            )
        )

    def create_aggressive_config(self) -> AlgorandLendingConfig:
        """Create configuration for aggressive lending."""
        return AlgorandLendingConfig(
            network=NetworkConfig(
                algod_token=os.getenv("ALGOD_TOKEN", ""),
                algod_server=os.getenv("ALGOD_SERVER", "https://testnet-api.algonode.cloud"),
                network_name="testnet"
            ),
            collateral=CollateralConfig(
                min_collateral_ratio=1.2,  # 120% collateralization
                liquidation_threshold=1.1,  # 110% liquidation
                max_ltv_ratio=0.8,  # 80% max LTV
                supported_assets=[0, 31566704, 386192725],  # ALGO, USDC, goBTC
                price_deviation_threshold=0.15,  # 15% price deviation
                enable_cross_collateral=True
            ),
            interest_rates=InterestRateConfig(
                base_rate=0.12,  # 12% base rate
                min_rate=0.08,  # 8% minimum
                max_rate=0.35,  # 35% maximum
                risk_multiplier=2.5,  # Aggressive risk multiplier
                reputation_weight=0.2,
                collateral_weight=0.3,
                market_weight=0.5
            ),
            loan_approval=LoanApprovalConfig(
                min_loan_amount=10000,  # 0.01 ALGO minimum
                max_loan_amount=100000000,  # 100 ALGO maximum
                max_duration_days=365,  # 1 year max
                min_credit_score=0.3,  # Lower credit score accepted
                require_kyc=False,
                enable_automatic_approval=True
            ),
            risk_assessment=RiskAssessmentConfig(
                max_risk_score=0.9,  # High risk tolerance
                enable_stress_testing=False,
                correlation_threshold=0.9,
                volatility_lookback_days=7,
                enable_portfolio_risk=False
            )
        )

    def create_defi_protocol_config(self) -> AlgorandLendingConfig:
        """Create configuration optimized for DeFi protocols."""
        return AlgorandLendingConfig(
            network=NetworkConfig(
                algod_token=os.getenv("ALGOD_TOKEN", ""),
                algod_server=os.getenv("ALGOD_SERVER", "https://mainnet-api.algonode.cloud"),
                network_name="mainnet"
            ),
            collateral=CollateralConfig(
                min_collateral_ratio=1.5,  # 150% collateralization
                liquidation_threshold=1.3,  # 130% liquidation
                max_ltv_ratio=0.75,  # 75% max LTV
                supported_assets=[0, 31566704, 386192725, 386195940],  # Major tokens
                price_deviation_threshold=0.10,  # 10% price deviation
                enable_cross_collateral=True,
                liquidation_penalty=0.05  # 5% liquidation penalty
            ),
            interest_rates=InterestRateConfig(
                base_rate=0.06,  # 6% base rate (competitive)
                min_rate=0.03,  # 3% minimum
                max_rate=0.25,  # 25% maximum
                risk_multiplier=2.0,
                reputation_weight=0.25,
                collateral_weight=0.35,
                market_weight=0.4,
                utilization_weight=0.3  # Factor in utilization
            ),
            loan_approval=LoanApprovalConfig(
                min_loan_amount=1000,  # 0.001 ALGO minimum
                max_loan_amount=1000000000,  # 1000 ALGO maximum
                max_duration_days=90,  # 3 months max
                min_credit_score=0.4,
                require_kyc=False,  # DeFi typically doesn't require KYC
                enable_automatic_approval=True,
                enable_flash_loans=True
            ),
            risk_assessment=RiskAssessmentConfig(
                max_risk_score=0.8,
                enable_stress_testing=True,
                correlation_threshold=0.85,
                volatility_lookback_days=14,
                enable_portfolio_risk=True,
                liquidity_risk_weight=0.4
            )
        )

    def create_institutional_config(self) -> AlgorandLendingConfig:
        """Create configuration for institutional clients."""
        return AlgorandLendingConfig(
            network=NetworkConfig(
                algod_token=os.getenv("ALGOD_TOKEN", ""),
                algod_server=os.getenv("ALGOD_SERVER", "https://mainnet-api.algonode.cloud"),
                network_name="mainnet"
            ),
            collateral=CollateralConfig(
                min_collateral_ratio=1.3,  # 130% collateralization
                liquidation_threshold=1.2,  # 120% liquidation
                max_ltv_ratio=0.8,  # 80% max LTV
                supported_assets=[0, 31566704],  # ALGO and USDC only
                price_deviation_threshold=0.08,  # 8% price deviation
                enable_cross_collateral=True,
                institutional_discount=0.02  # 2% institutional discount
            ),
            interest_rates=InterestRateConfig(
                base_rate=0.04,  # 4% base rate (institutional rate)
                min_rate=0.02,  # 2% minimum
                max_rate=0.15,  # 15% maximum
                risk_multiplier=1.2,  # Lower risk multiplier
                reputation_weight=0.4,  # Higher weight on reputation
                collateral_weight=0.3,
                market_weight=0.3,
                volume_discount=0.01  # Volume discount
            ),
            loan_approval=LoanApprovalConfig(
                min_loan_amount=10000000,  # 10 ALGO minimum
                max_loan_amount=10000000000,  # 10,000 ALGO maximum
                max_duration_days=180,  # 6 months max
                min_credit_score=0.8,  # High credit score required
                require_kyc=True,
                enable_automatic_approval=False,  # Manual review for large amounts
                require_compliance_check=True
            ),
            risk_assessment=RiskAssessmentConfig(
                max_risk_score=0.5,  # Very low risk tolerance
                enable_stress_testing=True,
                correlation_threshold=0.7,
                volatility_lookback_days=60,  # Longer lookback
                enable_portfolio_risk=True,
                regulatory_compliance=True
            )
        )

    def create_tenant_config(self, tenant_id: str, tenant_data: TenantConfig) -> AlgorandLendingConfig:
        """Create configuration for a specific tenant."""
        self._tenant_configs[tenant_id] = tenant_data

        # Base configuration based on risk tolerance
        if tenant_data.risk_tolerance == "conservative":
            base_config = self.create_conservative_config()
        elif tenant_data.risk_tolerance == "aggressive":
            base_config = self.create_aggressive_config()
        else:  # moderate
            base_config = DEFAULT_CONFIG

        # Apply tenant-specific customizations
        base_config.loan_approval.max_loan_amount = tenant_data.max_loan_amount
        base_config.collateral.supported_assets = tenant_data.supported_assets

        # Apply custom rates
        if "base_rate" in tenant_data.custom_rates:
            base_config.interest_rates.base_rate = tenant_data.custom_rates["base_rate"]
        if "min_rate" in tenant_data.custom_rates:
            base_config.interest_rates.min_rate = tenant_data.custom_rates["min_rate"]
        if "max_rate" in tenant_data.custom_rates:
            base_config.interest_rates.max_rate = tenant_data.custom_rates["max_rate"]

        # Apply special rules
        for rule_name, rule_value in tenant_data.special_rules.items():
            if hasattr(base_config.loan_approval, rule_name):
                setattr(base_config.loan_approval, rule_name, rule_value)

        # Cache configuration
        self._config_cache[tenant_id] = base_config

        return base_config

    def save_config_to_file(self, config: AlgorandLendingConfig, filename: str):
        """Save configuration to YAML file."""
        config_file = self.config_dir / f"{filename}.yaml"

        # Convert config to dict (simplified for YAML serialization)
        config_dict = {
            "network": {
                "network_name": config.network.network_name,
                "algod_server": config.network.algod_server
            },
            "collateral": {
                "min_collateral_ratio": config.collateral.min_collateral_ratio,
                "liquidation_threshold": config.collateral.liquidation_threshold,
                "max_ltv_ratio": config.collateral.max_ltv_ratio,
                "supported_assets": config.collateral.supported_assets
            },
            "interest_rates": {
                "base_rate": config.interest_rates.base_rate,
                "min_rate": config.interest_rates.min_rate,
                "max_rate": config.interest_rates.max_rate,
                "risk_multiplier": config.interest_rates.risk_multiplier
            },
            "loan_approval": {
                "min_loan_amount": config.loan_approval.min_loan_amount,
                "max_loan_amount": config.loan_approval.max_loan_amount,
                "max_duration_days": config.loan_approval.max_duration_days,
                "min_credit_score": config.loan_approval.min_credit_score
            },
            "risk_assessment": {
                "max_risk_score": config.risk_assessment.max_risk_score,
                "enable_stress_testing": config.risk_assessment.enable_stress_testing
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        print(f"✓ Configuration saved to {config_file}")

    def load_config_from_file(self, filename: str) -> AlgorandLendingConfig:
        """Load configuration from YAML file."""
        config_file = self.config_dir / f"{filename}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)

        # Convert dict back to config objects
        network_config = NetworkConfig(
            network_name=config_dict["network"]["network_name"],
            algod_server=config_dict["network"]["algod_server"],
            algod_token=os.getenv("ALGOD_TOKEN", "")
        )

        collateral_config = CollateralConfig(
            min_collateral_ratio=config_dict["collateral"]["min_collateral_ratio"],
            liquidation_threshold=config_dict["collateral"]["liquidation_threshold"],
            max_ltv_ratio=config_dict["collateral"]["max_ltv_ratio"],
            supported_assets=config_dict["collateral"]["supported_assets"]
        )

        interest_config = InterestRateConfig(
            base_rate=config_dict["interest_rates"]["base_rate"],
            min_rate=config_dict["interest_rates"]["min_rate"],
            max_rate=config_dict["interest_rates"]["max_rate"],
            risk_multiplier=config_dict["interest_rates"]["risk_multiplier"]
        )

        loan_config = LoanApprovalConfig(
            min_loan_amount=config_dict["loan_approval"]["min_loan_amount"],
            max_loan_amount=config_dict["loan_approval"]["max_loan_amount"],
            max_duration_days=config_dict["loan_approval"]["max_duration_days"],
            min_credit_score=config_dict["loan_approval"]["min_credit_score"]
        )

        risk_config = RiskAssessmentConfig(
            max_risk_score=config_dict["risk_assessment"]["max_risk_score"],
            enable_stress_testing=config_dict["risk_assessment"]["enable_stress_testing"]
        )

        config = AlgorandLendingConfig(
            network=network_config,
            collateral=collateral_config,
            interest_rates=interest_config,
            loan_approval=loan_config,
            risk_assessment=risk_config
        )

        print(f"✓ Configuration loaded from {config_file}")
        return config

    def validate_and_test_config(self, config: AlgorandLendingConfig) -> Dict[str, Any]:
        """Validate and test a configuration."""
        results = {
            "validation": {"passed": True, "errors": []},
            "service_creation": {"passed": False, "error": None},
            "engine_tests": {"passed": 0, "failed": 0, "details": {}},
            "recommendations": []
        }

        # 1. Validate configuration
        try:
            validate_config(config)
        except Exception as e:
            results["validation"]["passed"] = False
            results["validation"]["errors"].append(str(e))

        # 2. Test service creation
        try:
            test_service = create_lending_service(config)
            results["service_creation"]["passed"] = True
            results["service_creation"]["engines"] = len(test_service)
        except Exception as e:
            results["service_creation"]["error"] = str(e)
            return results  # Can't continue without service

        # 3. Test engines with sample data
        sample_address = AlgorandAddress("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        sample_collateral = [ASAToken(asset_id=0, amount=2000000)]
        sample_loan = LoanRequest(
            borrower=sample_address,
            requested_amount=1000000,
            collateral_assets=sample_collateral,
            loan_duration_days=30
        )

        engines_to_test = [
            ("collateral", lambda: test_service["collateral"].analyze_collateral(sample_collateral, sample_address)),
            ("interest_rates", lambda: test_service["interest_rates"].calculate_interest_rate(sample_loan)),
            ("loan_approval", lambda: test_service["loan_approval"].evaluate_loan(sample_loan)),
            ("risk_assessment", lambda: test_service["risk_assessment"].assess_risk(sample_loan))
        ]

        for engine_name, test_func in engines_to_test:
            try:
                result = test_func()
                results["engine_tests"]["passed"] += 1
                results["engine_tests"]["details"][engine_name] = "✓ Passed"
            except Exception as e:
                results["engine_tests"]["failed"] += 1
                results["engine_tests"]["details"][engine_name] = f"✗ Failed: {e}"

        # 4. Generate recommendations
        if config.interest_rates.base_rate > 0.20:
            results["recommendations"].append("Base rate is very high (>20%) - consider reducing")

        if config.collateral.min_collateral_ratio < 1.1:
            results["recommendations"].append("Collateral ratio is very low (<110%) - high liquidation risk")

        if config.loan_approval.max_loan_amount > 1000000000:
            results["recommendations"].append("Maximum loan amount is very high - consider risk limits")

        return results

# ============================================================================
# CONFIGURATION EXAMPLES
# ============================================================================

def demonstrate_basic_configurations():
    """Demonstrate basic configuration patterns."""
    print("\n🔧 Basic Configuration Patterns")
    print("=" * 50)

    manager = ConfigurationManager()

    # 1. Default configuration
    print("\n1. Default Configuration:")
    default_service = create_lending_service(DEFAULT_CONFIG)
    print(f"   ✓ Service created with {len(default_service)} engines")
    print(f"   Network: {DEFAULT_CONFIG.network.network_name}")
    print(f"   Base rate: {DEFAULT_CONFIG.interest_rates.base_rate:.2%}")

    # 2. TestNet configuration
    print("\n2. TestNet Configuration:")
    testnet_config = create_testnet_config()
    testnet_service = create_lending_service(testnet_config)
    print(f"   ✓ Service created for {testnet_config.network.network_name}")
    print(f"   Server: {testnet_config.network.algod_server}")

    # 3. Environment-based configuration
    print("\n3. Environment Configuration:")
    try:
        env_config = create_config_from_env()
        env_service = create_lending_service(env_config)
        print(f"   ✓ Loaded configuration from environment")
    except Exception as e:
        print(f"   ℹ️  Environment config not available: {e}")

def demonstrate_custom_configurations():
    """Demonstrate custom configuration creation."""
    print("\n⚙️  Custom Configuration Examples")
    print("=" * 50)

    manager = ConfigurationManager()

    # Test different risk profiles
    configs = {
        "conservative": manager.create_conservative_config(),
        "aggressive": manager.create_aggressive_config(),
        "defi_protocol": manager.create_defi_protocol_config(),
        "institutional": manager.create_institutional_config()
    }

    for config_name, config in configs.items():
        print(f"\n{config_name.upper()} Configuration:")
        print(f"   Collateral ratio: {config.collateral.min_collateral_ratio:.1f}x")
        print(f"   Base rate: {config.interest_rates.base_rate:.2%}")
        print(f"   Max loan: {config.loan_approval.max_loan_amount / 1_000_000:.1f} ALGO")
        print(f"   Risk tolerance: {config.risk_assessment.max_risk_score:.1f}")

        # Save to file
        manager.save_config_to_file(config, config_name)

def demonstrate_tenant_configurations():
    """Demonstrate multi-tenant configuration."""
    print("\n🏢 Multi-Tenant Configuration")
    print("=" * 50)

    manager = ConfigurationManager()

    # Define tenants
    tenants = [
        TenantConfig(
            tenant_id="startup_lender",
            name="Startup Lending Co",
            risk_tolerance="aggressive",
            max_loan_amount=5000000,  # 5 ALGO max
            supported_assets=[0],  # ALGO only
            custom_rates={"base_rate": 0.15},
            special_rules={"require_kyc": False}
        ),
        TenantConfig(
            tenant_id="traditional_bank",
            name="Traditional Bank Corp",
            risk_tolerance="conservative",
            max_loan_amount=100000000,  # 100 ALGO max
            supported_assets=[0, 31566704],  # ALGO and USDC
            custom_rates={"base_rate": 0.06, "max_rate": 0.18},
            special_rules={"require_kyc": True, "require_compliance_check": True}
        ),
        TenantConfig(
            tenant_id="defi_protocol",
            name="DeFi Protocol Alpha",
            risk_tolerance="moderate",
            max_loan_amount=50000000,  # 50 ALGO max
            supported_assets=[0, 31566704, 386192725],  # Multiple assets
            custom_rates={"base_rate": 0.08},
            special_rules={"enable_flash_loans": True, "enable_automatic_approval": True}
        )
    ]

    # Create configurations for each tenant
    tenant_services = {}
    for tenant in tenants:
        print(f"\n{tenant.name} ({tenant.tenant_id}):")
        config = manager.create_tenant_config(tenant.tenant_id, tenant)
        service = create_lending_service(config)
        tenant_services[tenant.tenant_id] = service

        print(f"   Risk tolerance: {tenant.risk_tolerance}")
        print(f"   Max loan: {tenant.max_loan_amount / 1_000_000:.1f} ALGO")
        print(f"   Supported assets: {len(tenant.supported_assets)}")
        print(f"   Base rate: {config.interest_rates.base_rate:.2%}")

        # Save tenant configuration
        manager.save_config_to_file(config, f"tenant_{tenant.tenant_id}")

def demonstrate_configuration_validation():
    """Demonstrate configuration validation and testing."""
    print("\n🔍 Configuration Validation & Testing")
    print("=" * 50)

    manager = ConfigurationManager()

    # Test different configurations
    test_configs = {
        "default": DEFAULT_CONFIG,
        "conservative": manager.create_conservative_config(),
        "aggressive": manager.create_aggressive_config()
    }

    for config_name, config in test_configs.items():
        print(f"\n{config_name.upper()} Configuration Validation:")

        # Validate and test
        validation_results = manager.validate_and_test_config(config)

        # Print results
        if validation_results["validation"]["passed"]:
            print("   ✓ Validation: PASSED")
        else:
            print("   ✗ Validation: FAILED")
            for error in validation_results["validation"]["errors"]:
                print(f"     - {error}")

        if validation_results["service_creation"]["passed"]:
            print(f"   ✓ Service creation: PASSED ({validation_results['service_creation']['engines']} engines)")
        else:
            print(f"   ✗ Service creation: FAILED - {validation_results['service_creation']['error']}")

        print(f"   Engine tests: {validation_results['engine_tests']['passed']} passed, {validation_results['engine_tests']['failed']} failed")

        for engine, result in validation_results["engine_tests"]["details"].items():
            print(f"     {engine}: {result}")

        if validation_results["recommendations"]:
            print("   Recommendations:")
            for rec in validation_results["recommendations"]:
                print(f"     - {rec}")

def demonstrate_dynamic_configuration():
    """Demonstrate dynamic configuration updates."""
    print("\n🔄 Dynamic Configuration Updates")
    print("=" * 50)

    # Start with default configuration
    current_config = DEFAULT_CONFIG
    service = create_lending_service(current_config)

    print(f"Initial configuration:")
    print(f"   Base rate: {current_config.interest_rates.base_rate:.2%}")
    print(f"   Collateral ratio: {current_config.collateral.min_collateral_ratio:.1f}x")

    # Simulate market conditions requiring rate adjustment
    print(f"\n📈 Market conditions changed - updating rates...")

    # Create updated configuration
    updated_config = AlgorandLendingConfig(
        network=current_config.network,
        collateral=current_config.collateral,
        interest_rates=InterestRateConfig(
            base_rate=current_config.interest_rates.base_rate + 0.02,  # +2%
            min_rate=current_config.interest_rates.min_rate,
            max_rate=current_config.interest_rates.max_rate + 0.05,  # +5%
            risk_multiplier=current_config.interest_rates.risk_multiplier * 1.1  # +10%
        ),
        loan_approval=current_config.loan_approval,
        risk_assessment=current_config.risk_assessment
    )

    # Create new service with updated configuration
    updated_service = create_lending_service(updated_config)

    print(f"Updated configuration:")
    print(f"   Base rate: {updated_config.interest_rates.base_rate:.2%} (+2%)")
    print(f"   Max rate: {updated_config.interest_rates.max_rate:.2%} (+5%)")
    print(f"   Risk multiplier: {updated_config.interest_rates.risk_multiplier:.1f}x (+10%)")

    # Test rate calculation with both configurations
    sample_loan = LoanRequest(
        borrower=AlgorandAddress("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
        requested_amount=1000000,
        collateral_assets=[ASAToken(asset_id=0, amount=2000000)],
        loan_duration_days=30
    )

    original_rate = service["interest_rates"].calculate_interest_rate(sample_loan)
    updated_rate = updated_service["interest_rates"].calculate_interest_rate(sample_loan)

    print(f"\nRate calculation comparison:")
    print(f"   Original final rate: {original_rate.final_rate:.2%}")
    print(f"   Updated final rate: {updated_rate.final_rate:.2%}")
    print(f"   Rate difference: {(updated_rate.final_rate - original_rate.final_rate):.2%}")

def main():
    """Main demonstration function."""
    print("🏦 Algorand Lending Custom Configuration Examples")
    print("=" * 60)
    print(f"📦 Package: {VENDOR_INFO['name']} v{VENDOR_INFO['version']}")

    try:
        # Run demonstrations
        demonstrate_basic_configurations()
        demonstrate_custom_configurations()
        demonstrate_tenant_configurations()
        demonstrate_configuration_validation()
        demonstrate_dynamic_configuration()

        print(f"\n🎉 Configuration Examples Completed!")
        print(f"\nGenerated configuration files:")

        # List generated config files
        config_dir = Path("configs")
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                print(f"   - {config_file}")

        print(f"\n📚 Key Configuration Patterns Demonstrated:")
        print(f"   ✓ Risk-based configurations (conservative, aggressive)")
        print(f"   ✓ Use-case specific configs (DeFi, institutional)")
        print(f"   ✓ Multi-tenant configuration management")
        print(f"   ✓ Configuration validation and testing")
        print(f"   ✓ Dynamic configuration updates")
        print(f"   ✓ File-based configuration persistence")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()