"""
Network Risk Monitoring Engine

Real-time ecosystem risk assessment and monitoring for the Algorand network,
enabling dynamic risk adjustment in loan decisions.
"""

from .core.risk_engine import NetworkRiskEngine

__version__ = "1.0.0"
__all__ = ["NetworkRiskEngine"]