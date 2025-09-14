"""
Setup configuration for lending-core package
Pure vendorable Python package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="algorand-lending-core",
    version="1.0.0",
    author="Agent 2 - Lending API Team",
    author_email="agent2@algorand-showcase.com",
    description="Pure business logic for Algorand A2A lending",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/lending-core",
    packages=["algorand_lending_core"],
    package_dir={"algorand_lending_core": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # NO production dependencies!
        # External dependencies injected by consumer
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "black",
            "isort",
            "mypy",
        ],
        "algorand": [
            # Optional - consumer can choose their Algorand SDK version
            "py-algorand-sdk>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # No CLI scripts - pure library
        ],
    },
)