"""Regulatory Compliance Router"""

from decimal import Decimal
from fastapi import APIRouter, HTTPException
from ..models import ComplianceCheckRequest, ComplianceCheckResponse
from ... import get_available_engines

router = APIRouter()

@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(request: ComplianceCheckRequest) -> ComplianceCheckResponse:
    """Check regulatory compliance for proposed interest rate."""
    try:
        available_engines = get_available_engines()

        if 'regulatory_compliance' not in available_engines:
            raise HTTPException(status_code=503, detail="Compliance engine not available")

        engine = available_engines['regulatory_compliance']()

        from ...regulatory_compliance.core.compliance_engine import Jurisdiction
        jurisdiction_enum = getattr(Jurisdiction, request.jurisdiction.upper(), Jurisdiction.US_FEDERAL)

        compliance = await engine.verify_compliance(
            Decimal(str(request.proposed_rate)),
            Decimal(str(request.loan_amount)),
            request.duration_days,
            jurisdiction_enum,
            request.borrower_type
        )

        return ComplianceCheckResponse(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))