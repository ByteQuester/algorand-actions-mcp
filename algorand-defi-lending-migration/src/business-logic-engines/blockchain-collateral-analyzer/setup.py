#!/usr/bin/env python3
"""
Setup script for blockchain-collateral-analyzer package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read version from __init__.py
init_path = Path(__file__).parent / "__init__.py"
version = "1.0.0"
if init_path.exists():
    with open(init_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break

setup(
    name="blockchain-collateral-analyzer",
    version=version,
    description="Comprehensive digital collateral analysis for DeFi lending on Algorand",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Algorand Lending Ecosystem",
    author_email="info@algorand-lending.dev",
    url="https://github.com/algorand-lending-ecosystem/blockchain-collateral-analyzer",
    license="MIT",

    # Package configuration
    packages=find_packages(exclude=["tests", "tests.*", "notebooks", "learning-path"]),
    include_package_data=True,
    zip_safe=False,

    # Python version requirement
    python_requires=">=3.8",

    # Dependencies
    install_requires=[
        "pyyaml>=6.0",
        "httpx>=0.24.0",
        "aiohttp>=3.8.0",
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scipy>=1.9.0",
        "asyncio-mqtt>=0.11.0",
        "websockets>=10.0",
        "python-dateutil>=2.8.0",
        "typing-extensions>=4.0.0",
        "dataclasses-json>=0.5.7",
        "pydantic>=1.10.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
    ],

    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
            "jupyter>=1.0.0",
            "notebook>=6.5.0",
            "ipykernel>=6.15.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "notebook>=6.5.0",
            "ipykernel>=6.15.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "plotly>=5.10.0",
        ],
        "oracle": [
            "chainlink-feeds>=1.0.0",
            "pycoingecko>=3.1.0",
        ],
        "mcp": [
            "mcp>=1.0.0",
            "sse-starlette>=1.6.0",
        ]
    },

    # Entry points for CLI commands
    entry_points={
        "console_scripts": [
            "collateral-analyzer=cli.main:main",
            "asset-valuation=cli.asset_valuation:main",
            "volatility-assessment=cli.volatility_assessment:main",
            "liquidation-scenarios=cli.liquidation_scenarios:main",
            "oracle-integration=cli.oracle_integration:main",
            "portfolio-analysis=cli.portfolio_analysis:main",
            "collateral-requirements=cli.collateral_requirements:main",
        ],
    },

    # Package classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],

    # Keywords for package discovery
    keywords=[
        "algorand", "defi", "collateral", "blockchain", "cryptocurrency",
        "lending", "risk-assessment", "valuation", "liquidation", "oracle",
        "portfolio", "volatility", "financial-analysis"
    ],

    # Project URLs
    project_urls={
        "Documentation": "https://algorand-lending-ecosystem.readthedocs.io/",
        "Source": "https://github.com/algorand-lending-ecosystem/blockchain-collateral-analyzer",
        "Bug Reports": "https://github.com/algorand-lending-ecosystem/blockchain-collateral-analyzer/issues",
        "Funding": "https://github.com/sponsors/algorand-lending-ecosystem",
    },
)