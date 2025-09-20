#!/usr/bin/env python3
"""
Setup script for Interest Rate Determiner package.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Interest Rate Determiner for Algorand DeFi Lending"

# Read requirements
def read_requirements(filename):
    req_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="interest-rate-determiner",
    version="1.0.0",
    author="Algorand Lending Ecosystem",
    author_email="dev@algorand-lending.io",
    description="Comprehensive interest rate determination system for DeFi lending on Algorand",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/algorand-lending-ecosystem/interest-rate-determiner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': read_requirements('requirements-dev.txt'),
        'testing': read_requirements('requirements-test.txt'),
        'docs': read_requirements('requirements-docs.txt'),
    },
    entry_points={
        'console_scripts': [
            'algo-rate-calculator=interest_rate_determiner.cli.algo_rate_calculator:main',
            'staking-yields=interest_rate_determiner.cli.staking_yields:main',
            'defi-yields=interest_rate_determiner.cli.defi_yields:main',
            'reputation-checker=interest_rate_determiner.cli.reputation_checker:main',
            'asa-analyzer=interest_rate_determiner.cli.asa_analyzer:main',
            'network-monitor=interest_rate_determiner.cli.network_monitor:main',
        ],
    },
    include_package_data=True,
    package_data={
        'interest_rate_determiner': [
            'data/*.json',
            'data/*.csv',
            'config/*.yaml',
            'config/*.json',
        ],
    },
    zip_safe=False,
    keywords=[
        'algorand', 'defi', 'lending', 'interest-rates', 'blockchain',
        'cryptocurrency', 'financial-services', 'credit-scoring',
        'risk-assessment', 'regulatory-compliance'
    ],
    project_urls={
        'Bug Reports': 'https://github.com/algorand-lending-ecosystem/interest-rate-determiner/issues',
        'Source': 'https://github.com/algorand-lending-ecosystem/interest-rate-determiner',
        'Documentation': 'https://docs.algorand-lending.io/interest-rate-determiner',
    },
)