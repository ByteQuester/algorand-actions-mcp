"""
Regulatory Compliance Module

Ensures interest rate calculations comply with relevant financial regulations,
including usury laws, consumer protection, and DeFi regulatory requirements.
"""

from .core.compliance_engine import RegulatoryComplianceEngine

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = ["RegulatoryComplianceEngine"]