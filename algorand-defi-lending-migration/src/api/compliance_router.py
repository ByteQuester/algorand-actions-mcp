"""
Compliance API Router for Regulatory Reporting and Analysis

Provides RESTful endpoints for compliance reporting, bias detection, and regulatory analysis.
Supports real-time compliance monitoring and automated report generation.

Endpoints:
- POST /api/v1/audit/export/regulatory - Generate compliance reports
- GET /api/v1/audit/compliance/metrics - Real-time compliance metrics
- POST /api/v1/audit/compliance/validate/{loan_id} - Validate specific loan
- GET /api/v1/audit/compliance/bias-analysis - Bias detection results
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path as PathParam
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from ..core.audit.compliance_service import (
    ComplianceService, ComplianceMetrics, InterestRateJustification,
    BiasType, RegulatoryFramework, BiasAnalysisResult
)
from ..core.audit.bias_detection import (
    BiasDetector, FairnessResult, BiasTestConfig, FairnessMetric, ProtectedAttribute
)
from ..core.audit.report_generator import (
    ComplianceReportGenerator, ReportConfiguration, ReportMetadata
)
from ..core.audit.models import AuditTrail, DecisionPoint, ComplianceEvent

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# API Models

class ComplianceMetricsRequest(BaseModel):
    """Request model for compliance metrics"""
    start_date: datetime = Field(..., description="Start date for analysis period")
    end_date: datetime = Field(..., description="End date for analysis period")
    frameworks: Optional[List[RegulatoryFramework]] = Field(
        default=[RegulatoryFramework.ECOA, RegulatoryFramework.FAIR_LENDING_ACT],
        description="Regulatory frameworks to analyze"
    )
    include_demographics: bool = Field(default=True, description="Include demographic analysis")
    include_bias_analysis: bool = Field(default=True, description="Include bias detection")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('start_date', 'end_date')
    def validate_dates_not_future(cls, v):
        if v > datetime.now(timezone.utc):
            raise ValueError('Dates cannot be in the future')
        return v


class BiasAnalysisRequest(BaseModel):
    """Request model for bias analysis"""
    start_date: datetime = Field(..., description="Start date for analysis period")
    end_date: datetime = Field(..., description="End date for analysis period")
    protected_attributes: Optional[List[ProtectedAttribute]] = Field(
        default=[ProtectedAttribute.RACE, ProtectedAttribute.GENDER, ProtectedAttribute.AGE],
        description="Protected attributes to analyze"
    )
    fairness_metrics: Optional[List[FairnessMetric]] = Field(
        default=[FairnessMetric.STATISTICAL_PARITY, FairnessMetric.EQUALIZED_ODDS],
        description="Fairness metrics to calculate"
    )
    bias_types: Optional[List[BiasType]] = Field(
        default=[BiasType.APPROVAL_RATE_BIAS, BiasType.INTEREST_RATE_BIAS],
        description="Types of bias to detect"
    )
    significance_level: float = Field(default=0.05, ge=0.001, le=0.1, description="Statistical significance level")
    minimum_sample_size: int = Field(default=30, ge=10, le=1000, description="Minimum sample size for analysis")


class ReportGenerationRequest(BaseModel):
    """Request model for report generation"""
    report_type: str = Field(..., regex="^(compliance|bias_analysis|regulatory_filing)$")
    start_date: datetime = Field(..., description="Start date for report period")
    end_date: datetime = Field(..., description="End date for report period")
    output_format: str = Field(default="PDF", regex="^(PDF|CSV|JSON|XLSX)$")
    template_name: str = Field(default="standard", regex="^(standard|executive|regulatory|technical)$")
    include_charts: bool = Field(default=True, description="Include charts and visualizations")
    include_recommendations: bool = Field(default=True, description="Include recommendations")
    regulatory_framework: str = Field(default="ECOA", description="Primary regulatory framework")
    confidentiality_level: str = Field(default="CONFIDENTIAL", regex="^(PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED)$")


class LoanValidationRequest(BaseModel):
    """Request model for loan validation"""
    loan_id: str = Field(..., description="Loan ID to validate")
    validation_types: List[str] = Field(
        default=["compliance", "bias", "interest_rate"],
        description="Types of validation to perform"
    )
    include_similar_loans: bool = Field(default=True, description="Include analysis of similar loans")
    similarity_threshold: float = Field(default=0.8, ge=0.5, le=1.0, description="Similarity threshold")


class ComplianceMetricsResponse(BaseModel):
    """Response model for compliance metrics"""
    metrics: Dict[str, Any]
    period: Dict[str, datetime]
    bias_analysis: List[Dict[str, Any]]
    regulatory_status: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime


class BiasAnalysisResponse(BaseModel):
    """Response model for bias analysis"""
    analysis_period: Dict[str, datetime]
    total_records_analyzed: int
    fairness_results: List[Dict[str, Any]]
    bias_flags: List[Dict[str, Any]]
    summary: Dict[str, Any]
    recommendations: List[str]
    regulatory_notes: List[str]
    generated_at: datetime


class ReportResponse(BaseModel):
    """Response model for report generation"""
    report_id: str
    file_path: str
    download_url: str
    metadata: Dict[str, Any]
    generation_status: str
    estimated_completion: Optional[datetime] = None


class LoanValidationResponse(BaseModel):
    """Response model for loan validation"""
    loan_id: str
    validation_results: Dict[str, Any]
    compliance_status: str
    bias_indicators: List[Dict[str, Any]]
    interest_rate_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    validated_at: datetime


# Router setup
router = APIRouter(prefix="/api/v1/audit/compliance", tags=["compliance"])

# Global service instances (would be dependency injected in production)
compliance_service: Optional[ComplianceService] = None
bias_detector: Optional[BiasDetector] = None
report_generator: Optional[ComplianceReportGenerator] = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current authenticated user"""
    # Placeholder - implement actual authentication
    return "system_user"


async def initialize_services():
    """Initialize compliance services"""
    global compliance_service, bias_detector, report_generator

    if compliance_service is None:
        # In production, get from dependency injection or config
        database_url = "postgresql://localhost:5432/lending_platform"
        compliance_service = ComplianceService(database_url)
        await compliance_service.initialize()

    if bias_detector is None:
        bias_detector = BiasDetector(BiasTestConfig())

    if report_generator is None:
        report_generator = ComplianceReportGenerator()


@router.on_event("startup")
async def startup_event():
    """Initialize services on router startup"""
    await initialize_services()


@router.get("/metrics", response_model=ComplianceMetricsResponse)
async def get_compliance_metrics(
    start_date: datetime = Query(..., description="Start date for metrics"),
    end_date: datetime = Query(..., description="End date for metrics"),
    frameworks: Optional[str] = Query(None, description="Comma-separated regulatory frameworks"),
    include_bias: bool = Query(True, description="Include bias analysis"),
    current_user: str = Depends(get_current_user)
):
    """
    Get real-time compliance metrics for a specified period

    Returns comprehensive compliance metrics including approval rates,
    bias analysis, and regulatory status indicators.
    """

    try:
        await initialize_services()

        # Parse frameworks
        framework_list = []
        if frameworks:
            for fw in frameworks.split(','):
                try:
                    framework_list.append(RegulatoryFramework(fw.strip().lower()))
                except ValueError:
                    logger.warning(f"Invalid framework: {fw}")

        if not framework_list:
            framework_list = [RegulatoryFramework.ECOA, RegulatoryFramework.FAIR_LENDING_ACT]

        # Generate compliance metrics
        compliance_metrics = await compliance_service.generate_compliance_metrics(
            start_date=start_date,
            end_date=end_date,
            frameworks=framework_list
        )

        # Prepare response
        bias_analysis_data = []
        if include_bias:
            for bias_result in compliance_metrics.bias_flags:
                bias_analysis_data.append({
                    "bias_type": bias_result.bias_type.value,
                    "detected": bias_result.detected,
                    "severity": bias_result.severity_score,
                    "p_value": bias_result.p_value,
                    "affected_groups": bias_result.affected_groups,
                    "recommendations": bias_result.recommendations[:3]  # Limit for API response
                })

        regulatory_status = {
            "compliance_score": compliance_metrics.compliance_score,
            "violations_count": len(compliance_metrics.regulatory_violations),
            "violations": compliance_metrics.regulatory_violations,
            "status": "COMPLIANT" if compliance_metrics.compliance_score > 0.8 else "NON_COMPLIANT"
        }

        # Generate recommendations
        recommendations = []
        for bias_result in compliance_metrics.bias_flags:
            if bias_result.detected:
                recommendations.extend(bias_result.recommendations[:2])

        return ComplianceMetricsResponse(
            metrics={
                "total_loans": compliance_metrics.total_loans,
                "approval_rate": compliance_metrics.approval_rate,
                "average_interest_rate": compliance_metrics.average_interest_rate,
                "demographic_breakdown": compliance_metrics.demographic_breakdown,
                "geographic_distribution": compliance_metrics.geographic_distribution,
                "risk_score_distribution": compliance_metrics.risk_score_distribution
            },
            period={"start": start_date, "end": end_date},
            bias_analysis=bias_analysis_data,
            regulatory_status=regulatory_status,
            recommendations=list(set(recommendations))[:10],  # Unique and limited
            generated_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Error generating compliance metrics: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating compliance metrics: {str(e)}"
        )


@router.get("/bias-analysis", response_model=BiasAnalysisResponse)
async def get_bias_analysis(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    protected_attributes: Optional[str] = Query(None, description="Comma-separated protected attributes"),
    significance_level: float = Query(0.05, ge=0.001, le=0.1, description="Statistical significance level"),
    current_user: str = Depends(get_current_user)
):
    """
    Perform comprehensive bias detection analysis

    Analyzes lending decisions for potential bias across protected classes
    and returns statistical analysis results with recommendations.
    """

    try:
        await initialize_services()

        # Parse protected attributes
        attr_list = []
        if protected_attributes:
            for attr in protected_attributes.split(','):
                try:
                    attr_list.append(ProtectedAttribute(attr.strip().lower()))
                except ValueError:
                    logger.warning(f"Invalid protected attribute: {attr}")

        # Configure bias detector
        config = BiasTestConfig(significance_level=significance_level)
        bias_detector_instance = BiasDetector(config)

        # Get loan data for the period
        async with compliance_service.connection_pool.acquire() as conn:
            loan_data = await compliance_service._get_loan_data(conn, start_date, end_date)

        if not loan_data:
            return BiasAnalysisResponse(
                analysis_period={"start": start_date, "end": end_date},
                total_records_analyzed=0,
                fairness_results=[],
                bias_flags=[],
                summary={"status": "insufficient_data"},
                recommendations=["Increase sample size for meaningful analysis"],
                regulatory_notes=[],
                generated_at=datetime.now(timezone.utc)
            )

        # Perform bias analysis
        fairness_results = bias_detector_instance.detect_all_bias_types(loan_data)

        # Format fairness results
        fairness_data = []
        bias_flags = []

        for result in fairness_results:
            fairness_dict = {
                "metric_type": result.metric_type.value,
                "protected_attribute": result.protected_attribute,
                "reference_group": result.reference_group,
                "comparison_groups": result.comparison_groups,
                "metric_values": result.metric_values,
                "disparity_ratios": result.disparity_ratios,
                "bias_detected": result.bias_detected,
                "severity_level": result.severity_level,
                "statistical_significance": result.statistical_significance,
                "sample_sizes": result.sample_sizes
            }
            fairness_data.append(fairness_dict)

            if result.bias_detected:
                bias_flags.append({
                    "type": result.metric_type.value,
                    "attribute": result.protected_attribute,
                    "severity": result.severity_level,
                    "summary": f"Bias detected in {result.protected_attribute} for {result.metric_type.value}"
                })

        # Generate summary
        total_bias_flags = len(bias_flags)
        critical_issues = len([f for f in bias_flags if f["severity"] == "CRITICAL"])

        summary = {
            "total_bias_flags": total_bias_flags,
            "critical_issues": critical_issues,
            "status": "CRITICAL" if critical_issues > 0 else "WARNING" if total_bias_flags > 0 else "COMPLIANT",
            "analysis_completeness": "COMPLETE" if len(loan_data) >= 100 else "LIMITED"
        }

        # Collect recommendations
        all_recommendations = set()
        regulatory_notes = set()

        for result in fairness_results:
            if result.bias_detected:
                all_recommendations.update(result.recommendations[:3])
                all_recommendations.update(result.regulatory_notes[:2])

        return BiasAnalysisResponse(
            analysis_period={"start": start_date, "end": end_date},
            total_records_analyzed=len(loan_data),
            fairness_results=fairness_data,
            bias_flags=bias_flags,
            summary=summary,
            recommendations=list(all_recommendations)[:15],  # Limit response size
            regulatory_notes=list(regulatory_notes)[:10],
            generated_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"Error performing bias analysis: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing bias analysis: {str(e)}"
        )


@router.post("/export/regulatory", response_model=ReportResponse)
async def generate_regulatory_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    Generate regulatory compliance reports

    Creates comprehensive compliance reports in specified format (PDF/CSV/JSON)
    with bias analysis, metrics, and recommendations for regulatory filing.
    """

    try:
        await initialize_services()

        # Generate report ID
        report_id = f"reg_{request.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Validate request
        if request.end_date <= request.start_date:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        # Create report configuration
        report_config = ReportConfiguration(
            template_name=request.template_name,
            include_charts=request.include_charts,
            include_recommendations=request.include_recommendations,
            regulatory_framework=request.regulatory_framework,
            output_format=request.output_format,
            confidentiality_level=request.confidentiality_level
        )

        # For long-running reports, use background tasks
        if request.output_format == "PDF" and request.include_charts:
            background_tasks.add_task(
                generate_report_background,
                request, report_config, report_id, current_user
            )

            return ReportResponse(
                report_id=report_id,
                file_path="",
                download_url=f"/api/v1/audit/compliance/reports/{report_id}/download",
                metadata={"status": "generating"},
                generation_status="IN_PROGRESS",
                estimated_completion=datetime.now(timezone.utc) + timedelta(minutes=5)
            )

        # Generate report synchronously for simple formats
        file_path, metadata = await generate_compliance_report_sync(
            request, report_config, report_id
        )

        return ReportResponse(
            report_id=report_id,
            file_path=file_path,
            download_url=f"/api/v1/audit/compliance/reports/{report_id}/download",
            metadata={
                "file_size": metadata.file_size_bytes,
                "checksum": metadata.checksum,
                "total_records": metadata.total_records
            },
            generation_status="COMPLETED"
        )

    except Exception as e:
        logger.error(f"Error generating regulatory report: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.post("/validate/{loan_id}", response_model=LoanValidationResponse)
async def validate_loan_compliance(
    loan_id: str = PathParam(..., description="Loan ID to validate"),
    request: LoanValidationRequest = None,
    current_user: str = Depends(get_current_user)
):
    """
    Validate specific loan for compliance and bias

    Performs detailed compliance validation for a specific loan including
    bias detection, interest rate justification, and regulatory compliance checks.
    """

    try:
        await initialize_services()

        # If no request body, use defaults
        if request is None:
            request = LoanValidationRequest(loan_id=loan_id)

        # Get loan data
        async with compliance_service.connection_pool.acquire() as conn:
            loan_query = """
            SELECT dp.*, at.event_data
            FROM decision_points dp
            JOIN audit_trails at ON at.id = dp.audit_event_id
            WHERE dp.loan_id = $1
            ORDER BY dp.decision_timestamp DESC
            LIMIT 1
            """

            loan_record = await conn.fetchrow(loan_query, loan_id)

            if not loan_record:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Loan {loan_id} not found"
                )

            # Parse loan data
            event_data = json.loads(loan_record['event_data']) if loan_record['event_data'] else {}
            loan_data = {
                'loan_id': loan_id,
                'borrower_address': loan_record['borrower_address'],
                'approved': loan_record['decision_outcome'].lower() == 'approved',
                'interest_rate': event_data.get('interest_rate'),
                'loan_amount': event_data.get('loan_amount'),
                'risk_score': loan_record['risk_score'],
                **event_data
            }

        validation_results = {}

        # Compliance validation
        if "compliance" in request.validation_types:
            compliance_result = await validate_loan_compliance_rules(loan_data)
            validation_results["compliance"] = compliance_result

        # Bias validation
        bias_indicators = []
        if "bias" in request.validation_types and request.include_similar_loans:
            # Find similar loans for comparison
            similar_loans = await find_similar_loans(
                conn, loan_data, request.similarity_threshold
            )

            if similar_loans:
                bias_result = bias_detector.detect_individual_bias(
                    loan_data, similar_loans, ["race", "gender", "age"]
                )

                if bias_result["bias_detected"]:
                    bias_indicators.append({
                        "type": "individual_bias",
                        "confidence": bias_result["confidence"],
                        "explanation": bias_result["explanation"],
                        "similar_cases": bias_result["similar_cases_analyzed"]
                    })

        # Interest rate validation
        interest_rate_analysis = None
        if "interest_rate" in request.validation_types and loan_data.get('interest_rate'):
            rate_justification = await compliance_service.justify_interest_rate(
                loan_id, loan_data, loan_data['interest_rate']
            )

            interest_rate_analysis = {
                "assigned_rate": rate_justification.assigned_rate,
                "market_benchmark": rate_justification.market_benchmark,
                "risk_premium": rate_justification.risk_premium,
                "justified": rate_justification.justified,
                "regulatory_compliant": rate_justification.regulatory_compliance,
                "explanation": rate_justification.explanation,
                "factors": rate_justification.justification_factors
            }

        # Overall compliance status
        compliance_issues = len([v for v in validation_results.values() if v.get("status") == "NON_COMPLIANT"])
        bias_issues = len(bias_indicators)
        rate_issues = 1 if interest_rate_analysis and not interest_rate_analysis["justified"] else 0

        total_issues = compliance_issues + bias_issues + rate_issues

        if total_issues == 0:
            compliance_status = "COMPLIANT"
        elif total_issues <= 2:
            compliance_status = "WARNING"
        else:
            compliance_status = "NON_COMPLIANT"

        # Generate recommendations
        recommendations = []
        if compliance_issues > 0:
            recommendations.append("Review loan against compliance policies")
        if bias_issues > 0:
            recommendations.append("Manual review for potential bias")
        if rate_issues > 0:
            recommendations.append("Justify interest rate assignment")

        return LoanValidationResponse(
            loan_id=loan_id,
            validation_results=validation_results,
            compliance_status=compliance_status,
            bias_indicators=bias_indicators,
            interest_rate_analysis=interest_rate_analysis,
            recommendations=recommendations,
            validated_at=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating loan {loan_id}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating loan: {str(e)}"
        )


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str = PathParam(..., description="Report ID to download"),
    current_user: str = Depends(get_current_user)
):
    """
    Download generated compliance report

    Returns the generated compliance report file for download.
    Supports PDF, CSV, and JSON formats.
    """

    try:
        # Find report file
        report_files = list(Path("/tmp/compliance_reports").glob(f"{report_id}.*"))

        if not report_files:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )

        report_file = report_files[0]

        # Determine media type
        if report_file.suffix == '.pdf':
            media_type = 'application/pdf'
        elif report_file.suffix == '.csv':
            media_type = 'text/csv'
        elif report_file.suffix == '.json':
            media_type = 'application/json'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            path=str(report_file),
            filename=report_file.name,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading report: {str(e)}"
        )


# Helper functions

async def generate_report_background(
    request: ReportGenerationRequest,
    config: ReportConfiguration,
    report_id: str,
    user: str
):
    """Generate report in background task"""
    try:
        await generate_compliance_report_sync(request, config, report_id)
        logger.info(f"Background report generation completed: {report_id}")
    except Exception as e:
        logger.error(f"Background report generation failed: {e}")


async def generate_compliance_report_sync(
    request: ReportGenerationRequest,
    config: ReportConfiguration,
    report_id: str
) -> Tuple[str, ReportMetadata]:
    """Generate compliance report synchronously"""

    # Generate compliance metrics
    compliance_metrics = await compliance_service.generate_compliance_metrics(
        start_date=request.start_date,
        end_date=request.end_date,
        frameworks=[RegulatoryFramework(request.regulatory_framework.lower())]
    )

    # Generate report
    if request.report_type == "compliance":
        file_path, metadata = await report_generator.generate_compliance_report(
            compliance_metrics, compliance_metrics.bias_flags, config
        )
    elif request.report_type == "regulatory_filing":
        file_path, metadata = await report_generator.generate_regulatory_filing(
            compliance_metrics, request.regulatory_framework
        )
    else:
        raise ValueError(f"Unsupported report type: {request.report_type}")

    return file_path, metadata


async def validate_loan_compliance_rules(loan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate loan against compliance rules"""

    validation_result = {
        "status": "COMPLIANT",
        "checks": [],
        "violations": []
    }

    # Check interest rate limits
    interest_rate = loan_data.get('interest_rate', 0)
    if interest_rate > 0.25:  # 25% cap
        validation_result["status"] = "NON_COMPLIANT"
        validation_result["violations"].append("Interest rate exceeds regulatory limit")

    # Check loan amount limits
    loan_amount = loan_data.get('loan_amount', 0)
    if loan_amount > 1000000:  # $1M limit
        validation_result["status"] = "NON_COMPLIANT"
        validation_result["violations"].append("Loan amount exceeds regulatory limit")

    validation_result["checks"] = [
        {"rule": "interest_rate_limit", "passed": interest_rate <= 0.25},
        {"rule": "loan_amount_limit", "passed": loan_amount <= 1000000}
    ]

    return validation_result


async def find_similar_loans(
    conn,
    loan_data: Dict[str, Any],
    similarity_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """Find loans similar to the given loan for comparison"""

    # Simplified implementation - would use more sophisticated similarity matching
    query = """
    SELECT dp.*, at.event_data
    FROM decision_points dp
    JOIN audit_trails at ON at.id = dp.audit_event_id
    WHERE dp.loan_id != $1
    AND dp.decision_type = 'credit_approval'
    AND ABS(dp.risk_score - $2) < 10
    LIMIT 10
    """

    rows = await conn.fetch(query, loan_data['loan_id'], loan_data.get('risk_score', 50))

    similar_loans = []
    for row in rows:
        event_data = json.loads(row['event_data']) if row['event_data'] else {}
        similar_loan = {
            'loan_id': row['loan_id'],
            'approved': row['decision_outcome'].lower() == 'approved',
            'risk_score': row['risk_score'],
            **event_data
        }
        similar_loans.append(similar_loan)

    return similar_loans