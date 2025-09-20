"""
Credit Scoring Module

Advanced credit scoring system for DeFi lending using traditional and blockchain-based metrics.
Integrates multiple data sources to provide comprehensive creditworthiness assessment.
"""

from .core.credit_engine import CreditScoringEngine

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = ["CreditScoringEngine"]