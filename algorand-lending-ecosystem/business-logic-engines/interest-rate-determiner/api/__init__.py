"""
API Module for Interest Rate Determiner

FastAPI-based REST API and WebSocket endpoints for all interest rate engines.
Provides HTTP access to comprehensive interest rate determination functionality.
"""

from .main import app
from .models import *
from .routers import *

__version__ = "1.0.0"

__all__ = ["app"]