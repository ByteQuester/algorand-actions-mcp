#!/usr/bin/env python3
"""
Test script to verify the blockchain-collateral-analyzer package structure.

This script tests the package installation and CLI functionality.
"""

import os
import sys
import subprocess
import tempfile
import json

def test_package_structure():
    """Test that all required files are in place."""
    print("Testing package structure...")

    required_files = [
        "setup.py",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "MANIFEST.in",
        "__init__.py",
        "scripts/install.sh",
    ]

    required_dirs = [
        "cli",
        "bin",
        "scripts",
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (missing)")

    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"  ✓ {dir}/")
        else:
            print(f"  ✗ {dir}/ (missing)")

def test_cli_commands():
    """Test that CLI commands are working."""
    print("\nTesting CLI commands...")

    commands = [
        ("bin/collateral-analyzer", "--help"),
        ("bin/asset-valuation", "--help"),
        ("bin/volatility-assessment", "--help"),
        ("bin/liquidation-scenarios", "--help"),
        ("bin/oracle-integration", "--help"),
        ("bin/portfolio-analysis", "--help"),
        ("bin/collateral-requirements", "--help"),
    ]

    for cmd, arg in commands:
        try:
            result = subprocess.run([sys.executable, cmd, arg],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✓ {cmd} {arg}")
            else:
                print(f"  ✗ {cmd} {arg} (exit code: {result.returncode})")
        except Exception as e:
            print(f"  ✗ {cmd} {arg} (error: {e})")

def test_engine_availability():
    """Test engine availability check."""
    print("\nTesting engine availability...")

    try:
        result = subprocess.run([sys.executable, "bin/collateral-analyzer", "--check-engines"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  ✓ Engine availability check executed")
            # Parse output to count available engines
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "Available engines:" in line:
                    print(f"    {line.strip()}")
                elif line.strip().startswith("✓") or line.strip().startswith("✗"):
                    print(f"    {line.strip()}")
        else:
            print(f"  ✗ Engine availability check failed (exit code: {result.returncode})")
    except Exception as e:
        print(f"  ✗ Engine availability check error: {e}")

def test_package_metadata():
    """Test package metadata."""
    print("\nTesting package metadata...")

    try:
        # Test Python import
        sys.path.insert(0, '.')
        import __init__ as analyzer

        print(f"  ✓ Package version: {analyzer.__version__}")
        print(f"  ✓ Package author: {analyzer.__author__}")

        # Test available functions
        functions = ['get_available_engines', 'check_engine_availability']
        for func in functions:
            if hasattr(analyzer, func):
                print(f"  ✓ Function available: {func}")
            else:
                print(f"  ✗ Function missing: {func}")

    except Exception as e:
        print(f"  ✗ Package import error: {e}")

def test_config_files():
    """Test configuration file formats."""
    print("\nTesting configuration files...")

    config_files = [
        ("pyproject.toml", "TOML"),
        ("requirements.txt", "plain text"),
        ("requirements-dev.txt", "plain text"),
    ]

    for file, format_type in config_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
                if content.strip():
                    print(f"  ✓ {file} ({format_type}) - {len(content)} characters")
                else:
                    print(f"  ✗ {file} is empty")
        except Exception as e:
            print(f"  ✗ {file} error: {e}")

def main():
    """Run all tests."""
    print("Blockchain Collateral Analyzer Package Test")
    print("=" * 50)

    # Change to package directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    test_package_structure()
    test_cli_commands()
    test_engine_availability()
    test_package_metadata()
    test_config_files()

    print("\n" + "=" * 50)
    print("Package test completed!")
    print("\nTo install the package:")
    print("  ./scripts/install.sh")
    print("\nTo install in development mode:")
    print("  ./scripts/install.sh --dev --venv")

if __name__ == "__main__":
    main()