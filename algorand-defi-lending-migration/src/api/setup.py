"""
Setup for lending platform API module
Part of the lending-platform application
"""

from setuptools import setup, find_packages

setup(
    name="lending-platform-api",
    version="1.0.0",
    author="Algorand Lending Platform Team",
    description="API module for the lending platform application",
    packages=["lending_platform_api"],
    package_dir={"lending_platform_api": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Dependencies managed at application level
    ],
)