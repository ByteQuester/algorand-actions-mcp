"""
Setup configuration for lending platform core module
Part of the lending-platform application
"""

from setuptools import setup, find_packages

setup(
    name="lending-platform-core",
    version="1.0.0",
    author="Algorand Lending Platform Team",
    description="Core business logic for the lending platform application",
    packages=["lending_platform_core"],
    package_dir={"lending_platform_core": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Dependencies managed at application level
    ],
)