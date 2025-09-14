"""
Setup for clean lending API package
"""

from setuptools import setup, find_packages

setup(
    name="algorand-lending-api",
    version="1.0.0",
    author="Agent 2 - Lending API Team",
    description="Clean FastAPI wrapper for algorand-lending-core",
    packages=["algorand_lending_api"],
    package_dir={"algorand_lending_api": "src"},
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "algorand-lending-core==1.0.0",  # Our pure business logic package
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "httpx",  # For testing FastAPI
        ],
    },
)