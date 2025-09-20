"""Credit Scoring Router"""

from fastapi import APIRouter, HTTPException
from ..models import CreditScoringRequest, CreditScoreResponse
from ... import get_available_engines

router = APIRouter()

@router.post("/score", response_model=CreditScoreResponse)
async def calculate_credit_score(request: CreditScoringRequest) -> CreditScoreResponse:
    """Calculate credit score using traditional and blockchain data."""
    try:
        available_engines = get_available_engines()

        if 'credit_scoring' not in available_engines:
            raise HTTPException(status_code=503, detail="Credit scoring engine not available")

        engine = available_engines['credit_scoring']()

        from ...credit_scoring.core.credit_engine import TraditionalCreditData, BlockchainCreditData

        traditional_data = TraditionalCreditData(
            credit_score=request.traditional_credit_score
        ) if request.traditional_credit_score else None

        blockchain_data = BlockchainCreditData(
            wallet_address=request.wallet_address,
            wallet_age_days=request.wallet_age_days,
            transaction_count=request.transaction_count,
            average_balance=request.average_balance
        )

        score = await engine.calculate_credit_score(traditional_data, blockchain_data, None)

        return CreditScoreResponse(
            overall_score=score.overall_score,
            traditional_score=score.traditional_score,
            blockchain_score=score.blockchain_score,
            behavioral_score=score.behavioral_score,
            confidence_level=score.confidence_level,
            positive_factors=score.positive_factors,
            negative_factors=score.negative_factors,
            recommendations=score.recommendations,
            risk_level=score.risk_level,
            score_timestamp=score.score_timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))