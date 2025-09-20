"""
Setup configuration for Algorand Risk Assessment Calculator
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="algorand-risk-assessment-calculator",
    version="1.0.0",
    author="Algorand Risk Assessment Team",
    author_email="risk@algorand.com",
    description="Comprehensive holistic risk assessment system for Algorand ecosystem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/risk-assessment-calculator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.20",
            "pytest-cov>=3.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "sphinx-autodoc-typehints>=1.12",
        ],
        "monitoring": [
            "prometheus-client>=0.14",
            "grafana-api>=1.0",
            "alertmanager-webhook>=0.3",
        ]
    },
    entry_points={
        "console_scripts": [
            "holistic-risk-assessor=cli.holistic_assessor:main",
            "blockchain-behavior-monitor=cli.blockchain_monitor:main",
            "defi-protocol-monitor=cli.defi_monitor:main",
            "smart-contract-analyzer=cli.contract_analyzer:main",
            "liquidity-cascade-monitor=cli.cascade_monitor:main",
            "governance-stability-tracker=cli.governance_tracker:main",
            "risk-alert-manager=cli.alert_manager:main",
            "risk-monitoring-dashboard=cli.monitoring_dashboard:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.md"],
        "config": ["*.yaml", "*.json"],
        "docs": ["*.md", "*.rst"],
    },
    zip_safe=False,
    keywords=[
        "algorand", "blockchain", "risk-assessment", "defi", "cryptocurrency",
        "financial-analysis", "risk-management", "smart-contracts", "governance"
    ],
    project_urls={
        "Bug Reports": "https://github.com/algorand/risk-assessment-calculator/issues",
        "Source": "https://github.com/algorand/risk-assessment-calculator",
        "Documentation": "https://algorand-risk-docs.readthedocs.io/",
    },
)