#!/usr/bin/env python3
"""
Setup script for Algorand Lending Business Logic package.
Simple vendoring package for easy integration.
"""

from setuptools import setup, find_packages

def get_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="algorand-lending-business-logic",
    version="1.0.0",
    description="Algorand lending engines",
    author="Algorand Team",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=get_requirements(),
    include_package_data=True,
    zip_safe=False,
)