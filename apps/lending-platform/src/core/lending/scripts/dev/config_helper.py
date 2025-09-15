"""
Development configuration helper for lending-core package
Provides utilities for testing different configuration scenarios
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LendingConfig:
    """Configuration for lending operations"""
    reader_endpoint: str
    writer_endpoint: str
    network: str = "testnet"
    enable_debug: bool = False


class ConfigPresets:
    """Predefined configuration presets for different environments"""

    @staticmethod
    def local_development() -> LendingConfig:
        """Local development configuration"""
        return LendingConfig(
            reader_endpoint="http://localhost:8002",
            writer_endpoint="http://localhost:3001",
            network="testnet",
            enable_debug=True
        )

    @staticmethod
    def staging() -> LendingConfig:
        """Staging environment configuration"""
        return LendingConfig(
            reader_endpoint="https://staging-reader.algorand-showcase.com",
            writer_endpoint="https://staging-writer.algorand-showcase.com",
            network="testnet",
            enable_debug=True
        )

    @staticmethod
    def production() -> LendingConfig:
        """Production environment configuration"""
        return LendingConfig(
            reader_endpoint="https://reader.algorand-showcase.com",
            writer_endpoint="https://writer.algorand-showcase.com",
            network="mainnet",
            enable_debug=False
        )

    @staticmethod
    def testing() -> LendingConfig:
        """Testing configuration with mock endpoints"""
        return LendingConfig(
            reader_endpoint="http://localhost:8888",  # Mock server port
            writer_endpoint="http://localhost:8889",  # Mock server port
            network="testnet",
            enable_debug=True
        )


def get_config_from_env() -> LendingConfig:
    """Load configuration from environment variables"""
    return LendingConfig(
        reader_endpoint=os.getenv("LENDING_READER_ENDPOINT", "http://localhost:8002"),
        writer_endpoint=os.getenv("LENDING_WRITER_ENDPOINT", "http://localhost:3001"),
        network=os.getenv("ALGORAND_NETWORK", "testnet"),
        enable_debug=os.getenv("LENDING_DEBUG", "false").lower() == "true"
    )


def create_env_template(config: LendingConfig) -> Dict[str, str]:
    """Create environment variable template from config"""
    return {
        "LENDING_READER_ENDPOINT": config.reader_endpoint,
        "LENDING_WRITER_ENDPOINT": config.writer_endpoint,
        "ALGORAND_NETWORK": config.network,
        "LENDING_DEBUG": str(config.enable_debug).lower()
    }


def display_config(config: LendingConfig, name: str = "Current") -> None:
    """Display configuration in a readable format"""
    print(f"\n{name} Configuration:")
    print(f"  Reader Endpoint: {config.reader_endpoint}")
    print(f"  Writer Endpoint: {config.writer_endpoint}")
    print(f"  Network: {config.network}")
    print(f"  Debug Enabled: {config.enable_debug}")


def test_all_presets() -> None:
    """Test all configuration presets"""
    print("=== Lending Core Configuration Presets ===")

    presets = [
        ("Local Development", ConfigPresets.local_development()),
        ("Staging", ConfigPresets.staging()),
        ("Production", ConfigPresets.production()),
        ("Testing", ConfigPresets.testing()),
        ("From Environment", get_config_from_env())
    ]

    for name, config in presets:
        display_config(config, name)

        # Generate .env format
        env_vars = create_env_template(config)
        print(f"\n  Environment Variables for {name}:")
        for key, value in env_vars.items():
            print(f"    {key}={value}")
        print()


def generate_env_file(preset_name: str = "local_development", output_path: str = ".env.example") -> None:
    """Generate .env file for a specific preset"""
    preset_map = {
        "local_development": ConfigPresets.local_development(),
        "staging": ConfigPresets.staging(),
        "production": ConfigPresets.production(),
        "testing": ConfigPresets.testing()
    }

    if preset_name not in preset_map:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(preset_map.keys())}")

    config = preset_map[preset_name]
    env_vars = create_env_template(config)

    with open(output_path, 'w') as f:
        f.write(f"# Environment configuration for {preset_name}\n")
        f.write("# Copy this to .env and customize as needed\n\n")

        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

        f.write("\n# Additional configuration options:\n")
        f.write("# LOAN_AMOUNT_LIMIT=1000000  # Maximum loan amount in microAlgos\n")
        f.write("# COLLATERAL_RATIO=150       # Required collateral percentage\n")
        f.write("# INTEREST_RATE=5.0          # Annual interest rate\n")

    print(f"Generated {output_path} for {preset_name} preset")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            test_all_presets()
        elif command == "generate-env":
            preset = sys.argv[2] if len(sys.argv) > 2 else "local_development"
            output = sys.argv[3] if len(sys.argv) > 3 else ".env.example"
            generate_env_file(preset, output)
        else:
            print("Usage: python config_helper.py [test|generate-env [preset] [output_file]]")
    else:
        test_all_presets()