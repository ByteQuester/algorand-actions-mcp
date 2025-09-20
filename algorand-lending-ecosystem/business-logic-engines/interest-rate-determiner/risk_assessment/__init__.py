"""
Risk Assessment Module

Evaluates borrower and market risks to determine appropriate risk premiums for interest rates.
This module analyzes multiple risk factors including credit risk, market risk, and operational risk.
"""

from .core.risk_engine import RiskAssessmentEngine

__version__ = "1.0.0"
__author__ = "Algorand Lending Ecosystem"

__all__ = ["RiskAssessmentEngine"]