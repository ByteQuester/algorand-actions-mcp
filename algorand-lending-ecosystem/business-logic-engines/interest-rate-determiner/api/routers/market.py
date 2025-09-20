"""Market Analysis Router"""

from fastapi import APIRouter, HTTPException
from ..models import MarketAnalysisRequest, MarketAnalysisResponse, ErrorResponse
from ... import get_available_engines

router = APIRouter()

@router.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market_rates(request: MarketAnalysisRequest) -> MarketAnalysisResponse:
    """Analyze market rates for specified asset."""
    try:
        available_engines = get_available_engines()

        if 'market_rate_analysis' not in available_engines:
            raise HTTPException(status_code=503, detail="Market analysis engine not available")

        engine = available_engines['market_rate_analysis']()
        analysis = await engine.analyze_market_rates(request.asset, request.analysis_period_hours)

        return MarketAnalysisResponse(
            base_rate=float(analysis.base_rate),
            market_sentiment=analysis.market_sentiment,
            volatility_score=analysis.volatility_score,
            liquidity_score=analysis.liquidity_score,
            recommendation=analysis.recommendation,
            risk_factors=analysis.risk_factors,
            confidence=analysis.confidence,
            analysis_timestamp=analysis.analysis_timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))