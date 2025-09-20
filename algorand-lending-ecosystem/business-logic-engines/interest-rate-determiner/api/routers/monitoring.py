"""Monitoring and Health Check Router"""

from fastapi import APIRouter
from ... import get_available_engines, check_engine_availability

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    available_engines = get_available_engines()
    return {
        "status": "healthy",
        "engines_available": len(available_engines),
        "engines_total": 6,
        "engines": list(available_engines.keys())
    }

@router.get("/engines")
async def engine_status():
    """Detailed engine status."""
    available_engines = get_available_engines()
    
    engine_status = {
        "market_rate_analysis": "market_rate_analysis" in available_engines,
        "risk_assessment": "risk_assessment" in available_engines,
        "credit_scoring": "credit_scoring" in available_engines,
        "regulatory_compliance": "regulatory_compliance" in available_engines,
        "dynamic_pricing": "dynamic_pricing" in available_engines,
        "rate_optimization": "rate_optimization" in available_engines,
    }
    
    return {
        "total_engines": 6,
        "available_engines": len(available_engines),
        "engine_status": engine_status,
        "available_engine_classes": {
            name: engine.__name__ for name, engine in available_engines.items()
        }
    }