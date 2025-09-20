"""
Setup configuration for Holistic Decision Orchestrator

Complete package with all 6 engine CLI entry points for Algorand lending ecosystem.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="algorand-holistic-decision-orchestrator",
    version="1.0.0",
    description="Holistic loan approval decision orchestrator for Algorand ecosystem",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Algorand Lending Team",
    author_email="lending@algorand.com",
    url="https://github.com/algorand/lending-ecosystem",
    license="MIT",

    packages=find_packages(),
    python_requires=">=3.9",

    install_requires=read_requirements("requirements.txt"),

    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'pre-commit>=3.0.0'
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-mock>=3.10.0',
            'httpx>=0.24.0',
            'respx>=0.20.0'
        ],
        'monitoring': [
            'prometheus-client>=0.16.0',
            'grafana-api>=1.0.3',
            'datadog>=0.44.0'
        ]
    },

    entry_points={
        'console_scripts': [
            # Master holistic loan approver
            'holistic-loan-approver=cli.holistic_loan_approver:cli',

            # Individual engine CLIs
            'ecosystem-analyzer=cli.ecosystem_analyzer:cli',
            'defi-behavior-checker=cli.defi_behavior_checker:cli',
            'collateral-intelligence=cli.collateral_intelligence:cli',
            'governance-reputation=cli.governance_reputation:cli',
            'network-risk-monitor=cli.network_risk_monitor:cli',

            # Utility tools
            'holistic-decision-stats=cli.holistic_loan_approver:stats',
            'holistic-decision-monitor=cli.holistic_loan_approver:monitor',
        ]
    },

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Framework :: AsyncIO",
    ],

    keywords=[
        "algorand", "blockchain", "defi", "lending", "loan-approval",
        "risk-assessment", "governance", "collateral", "ecosystem",
        "holistic-analysis", "decision-engine", "fintech"
    ],

    project_urls={
        "Documentation": "https://algorand-lending-docs.readthedocs.io/",
        "Source": "https://github.com/algorand/lending-ecosystem",
        "Tracker": "https://github.com/algorand/lending-ecosystem/issues",
        "Funding": "https://github.com/sponsors/algorand",
    },

    package_data={
        'holistic_decision_orchestrator': [
            'config/*.yaml',
            'config/*.json',
            'examples/*.py',
            'examples/*.json',
            'examples/*.yaml',
        ]
    },

    include_package_data=True,
    zip_safe=False,

    # Test configuration
    test_suite='integration_tests',

    # Metadata for PyPI
    platforms=['any'],

    # Entry points for plugins (if needed in future)
    # entry_points={
    #     'algorand_lending.engines': [
    #         'holistic = holistic_decision_orchestrator.core:HolisticDecisionOrchestrator',
    #     ],
    # }
)