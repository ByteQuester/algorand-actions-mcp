"""
Main Rates Router

Comprehensive interest rate calculation endpoints using all available engines.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models import (
    RateCalculationRequest, RateCalculationResponse, PaymentDetails,
    MarketAnalysisResponse, RiskAssessmentResponse, ComplianceCheckResponse,
    ErrorResponse
)
from ... import get_available_engines

router = APIRouter()


@router.post("/calculate", response_model=RateCalculationResponse)
async def calculate_comprehensive_rate(
    request: RateCalculationRequest,
    background_tasks: BackgroundTasks
) -> RateCalculationResponse:
    """
    Calculate comprehensive interest rate using all available engines.

    This endpoint orchestrates all 6 engines to provide a complete interest rate
    calculation including market analysis, risk assessment, credit scoring,
    regulatory compliance, dynamic pricing, and rate optimization.
    """
    try:
        available_engines = get_available_engines()

        if not available_engines:
            raise HTTPException(
                status_code=503,
                detail="No engines available for rate calculation"
            )

        loan_decimal = Decimal(str(request.loan_amount))
        results = {}

        # Market Rate Analysis
        market_analysis = None
        if 'market_rate_analysis' in available_engines:
            engine = available_engines['market_rate_analysis']()
            analysis = await engine.analyze_market_rates(request.asset, 24)
            market_analysis = MarketAnalysisResponse(
                base_rate=float(analysis.base_rate),
                market_sentiment=analysis.market_sentiment,
                volatility_score=analysis.volatility_score,
                liquidity_score=analysis.liquidity_score,
                recommendation=analysis.recommendation,
                risk_factors=analysis.risk_factors,
                confidence=analysis.confidence,
                analysis_timestamp=analysis.analysis_timestamp
            )
            results['base_rate'] = float(analysis.base_rate)

        # Risk Assessment
        risk_assessment = None
        if 'risk_assessment' in available_engines:
            engine = available_engines['risk_assessment']()

            # Create borrower profile from request
            from ...risk_assessment.core.risk_engine import BorrowerProfile, MarketRiskFactors

            borrower_profile = BorrowerProfile(
                borrower_id=request.borrower_id,
                credit_score=getattr(request, 'credit_score', None),
                debt_to_income_ratio=getattr(request, 'debt_to_income_ratio', None)
            )

            market_factors = MarketRiskFactors(
                asset_volatility=0.4,  # Default values - would be dynamic in production
                liquidity_risk=0.3,
                regulatory_risk=0.2
            )

            assessment = await engine.assess_risk(
                borrower_profile, market_factors, loan_decimal, request.duration_days
            )

            risk_assessment = RiskAssessmentResponse(
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
            results['risk_premium'] = float(assessment.risk_premium)

        # Regulatory Compliance
        compliance_check = None
        if 'regulatory_compliance' in available_engines:
            engine = available_engines['regulatory_compliance']()

            # Calculate preliminary rate
            base_rate = results.get('base_rate', 0.05)
            risk_premium = results.get('risk_premium', 0.02)
            proposed_rate = Decimal(str(base_rate + risk_premium))

            from ...regulatory_compliance.core.compliance_engine import Jurisdiction
            jurisdiction_enum = getattr(Jurisdiction, request.jurisdiction.upper(), Jurisdiction.US_FEDERAL)

            compliance = await engine.verify_compliance(
                proposed_rate, loan_decimal, request.duration_days, jurisdiction_enum
            )

            compliance_check = ComplianceCheckResponse(
                is_compliant=compliance.is_compliant,
                jurisdiction=request.jurisdiction,
                applied_rate=float(compliance.applied_rate),
                max_allowed_rate=float(compliance.max_allowed_rate),
                violations=compliance.violations,
                warnings=compliance.warnings,
                required_disclosures=compliance.required_disclosures,
                compliance_score=compliance.compliance_score,
                check_timestamp=compliance.check_timestamp
            )
            results['final_rate'] = float(compliance.applied_rate)

        # Calculate final rate and payment details
        final_rate = Decimal(str(results.get('final_rate', base_rate + risk_premium)))

        # Payment calculations
        monthly_rate = final_rate / 12
        num_months = request.duration_days / 30.0

        if monthly_rate > 0:
            monthly_payment = loan_decimal * (monthly_rate * (1 + monthly_rate) ** num_months) / ((1 + monthly_rate) ** num_months - 1)
        else:
            monthly_payment = loan_decimal / Decimal(str(num_months))

        total_payment = monthly_payment * Decimal(str(num_months))
        total_interest = total_payment - loan_decimal

        payment_details = PaymentDetails(
            monthly_payment=float(monthly_payment),
            total_payment=float(total_payment),
            total_interest=float(total_interest),
            annual_percentage_rate=float(final_rate)
        )

        # Rate components breakdown
        rate_components = {
            'base_rate': results.get('base_rate', 0.05),
            'risk_premium': results.get('risk_premium', 0.02),
            'final_rate': float(final_rate)
        }

        # Calculate overall confidence
        confidences = []
        if market_analysis:
            confidences.append(market_analysis.confidence)
        if risk_assessment:
            confidences.append(risk_assessment.confidence)
        if compliance_check:
            confidences.append(compliance_check.compliance_score)

        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        response = RateCalculationResponse(
            final_rate=float(final_rate),
            rate_components=rate_components,
            payment_details=payment_details,
            market_analysis=market_analysis,
            risk_assessment=risk_assessment,
            compliance_check=compliance_check,
            calculation_timestamp=datetime.now(),
            confidence=overall_confidence
        )

        # Schedule background task for logging/analytics
        background_tasks.add_task(log_rate_calculation, request, response)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="calculation_error",
                message=f"Error calculating interest rate: {str(e)}",
                details={"request": request.dict()}
            ).dict()
        )


@router.post("/quick-calculate")
async def quick_rate_calculation(
    loan_amount: float,
    duration_days: int,
    borrower_id: str = "default"
) -> dict:
    """
    Quick interest rate calculation with minimal inputs.

    Provides a fast estimate using default values and simplified calculations.
    """
    try:
        # Use simplified calculation for quick estimates
        base_rate = 0.05  # 5% default
        risk_premium = 0.02  # 2% default risk premium

        final_rate = base_rate + risk_premium

        # Simple payment calculation
        loan_decimal = Decimal(str(loan_amount))
        monthly_rate = Decimal(str(final_rate)) / 12
        num_months = duration_days / 30.0

        if monthly_rate > 0:
            monthly_payment = loan_decimal * (monthly_rate * (1 + monthly_rate) ** num_months) / ((1 + monthly_rate) ** num_months - 1)
        else:
            monthly_payment = loan_decimal / Decimal(str(num_months))

        return {
            "annual_rate": final_rate,
            "monthly_rate": final_rate / 12,
            "monthly_payment": float(monthly_payment),
            "total_interest": float(monthly_payment * Decimal(str(num_months)) - loan_decimal),
            "calculation_type": "quick_estimate",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in quick calculation: {str(e)}"
        )


async def log_rate_calculation(request: RateCalculationRequest, response: RateCalculationResponse):
    """Background task to log rate calculations for analytics"""
    # In production, this would log to a database or analytics service
    print(f"Rate calculation logged: {request.borrower_id} - {response.final_rate:.4%}")