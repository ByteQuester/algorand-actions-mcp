"""Risk Assessment Router"""

from decimal import Decimal
from fastapi import APIRouter, HTTPException
from ..models import RiskAssessmentRequest, RiskAssessmentResponse
from ... import get_available_engines

router = APIRouter()

@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_risk(request: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """Assess risk for borrower and loan parameters."""
    try:
        available_engines = get_available_engines()

        if 'risk_assessment' not in available_engines:
            raise HTTPException(status_code=503, detail="Risk assessment engine not available")

        engine = available_engines['risk_assessment']()

        from ...risk_assessment.core.risk_engine import BorrowerProfile, MarketRiskFactors

        borrower_profile = BorrowerProfile(
            borrower_id=request.borrower_id,
            credit_score=request.credit_score,
            debt_to_income_ratio=request.debt_to_income_ratio,
            employment_status=request.employment_status
        )

        market_factors = MarketRiskFactors(
            asset_volatility=0.4,
            liquidity_risk=0.3,
            regulatory_risk=0.2
        )

        assessment = await engine.assess_risk(
            borrower_profile, market_factors, Decimal(str(request.loan_amount)), request.duration_days
        )

        return RiskAssessmentResponse(
            overall_risk_level=assessment.overall_risk_level,
            risk_premium=float(assessment.risk_premium),
            risk_score=assessment.risk_score,
            credit_risk_score=assessment.credit_risk_score,
            market_risk_score=assessment.market_risk_score,
            operational_risk_score=assessment.operational_risk_score,
            risk_factors=assessment.risk_factors,
            mitigation_recommendations=assessment.mitigation_recommendations,
            confidence=assessment.confidence,
            assessment_timestamp=assessment.assessment_timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))