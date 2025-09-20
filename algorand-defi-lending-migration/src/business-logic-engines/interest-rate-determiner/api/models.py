"""
API Models for Interest Rate Determiner

Pydantic models for request/response validation and API documentation.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class JurisdictionEnum(str, Enum):
    """Supported regulatory jurisdictions"""
    US_FEDERAL = "us_federal"
    US_STATE = "us_state"
    EU = "eu"
    UK = "uk"
    SINGAPORE = "singapore"
    SWITZERLAND = "switzerland"
    GLOBAL = "global"


class RiskLevelEnum(str, Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Request Models
class RateCalculationRequest(BaseModel):
    """Request for comprehensive interest rate calculation"""
    loan_amount: float = Field(..., gt=0, description="Loan amount in USD")
    duration_days: int = Field(..., gt=0, le=365*10, description="Loan duration in days")
    borrower_id: str = Field(..., description="Unique borrower identifier")
    jurisdiction: JurisdictionEnum = Field(JurisdictionEnum.US_FEDERAL, description="Regulatory jurisdiction")
    asset: str = Field("ALGO", description="Collateral asset type")

    @validator('loan_amount')
    def validate_loan_amount(cls, v):
        if v <= 0:
            raise ValueError('Loan amount must be positive')
        if v > 100_000_000:  # 100M limit
            raise ValueError('Loan amount exceeds maximum limit')
        return v


class MarketAnalysisRequest(BaseModel):
    """Request for market rate analysis"""
    asset: str = Field("ALGO", description="Asset to analyze")
    analysis_period_hours: int = Field(24, ge=1, le=8760, description="Analysis period in hours")


class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment"""
    borrower_id: str = Field(..., description="Borrower identifier")
    loan_amount: float = Field(..., gt=0, description="Loan amount")
    duration_days: int = Field(..., gt=0, description="Loan duration in days")
    credit_score: Optional[int] = Field(None, ge=300, le=850, description="Traditional credit score")
    debt_to_income_ratio: Optional[float] = Field(None, ge=0, le=2, description="Debt to income ratio")
    employment_status: Optional[str] = Field(None, description="Employment status")


class CreditScoringRequest(BaseModel):
    """Request for credit scoring"""
    wallet_address: str = Field(..., description="Blockchain wallet address")
    traditional_credit_score: Optional[int] = Field(None, ge=300, le=850)
    wallet_age_days: Optional[int] = Field(None, ge=0)
    transaction_count: Optional[int] = Field(None, ge=0)
    average_balance: Optional[float] = Field(None, ge=0)


class ComplianceCheckRequest(BaseModel):
    """Request for regulatory compliance check"""
    proposed_rate: float = Field(..., ge=0, le=1, description="Proposed annual interest rate (decimal)")
    loan_amount: float = Field(..., gt=0, description="Loan amount")
    duration_days: int = Field(..., gt=0, description="Loan duration")
    jurisdiction: JurisdictionEnum = Field(..., description="Regulatory jurisdiction")
    borrower_type: str = Field("individual", description="Borrower type: individual or institutional")


# Response Models
class MarketAnalysisResponse(BaseModel):
    """Market analysis response"""
    base_rate: float = Field(..., description="Calculated base interest rate")
    market_sentiment: str = Field(..., description="Market sentiment: bullish, bearish, neutral")
    volatility_score: float = Field(..., ge=0, le=1, description="Volatility score")
    liquidity_score: float = Field(..., ge=0, le=1, description="Liquidity score")
    recommendation: str = Field(..., description="Rate recommendation")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    confidence: float = Field(..., ge=0, le=1, description="Analysis confidence")
    analysis_timestamp: datetime = Field(..., description="Analysis timestamp")


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response"""
    overall_risk_level: RiskLevelEnum = Field(..., description="Overall risk level")
    risk_premium: float = Field(..., description="Calculated risk premium")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    credit_risk_score: float = Field(..., description="Credit risk component")
    market_risk_score: float = Field(..., description="Market risk component")
    operational_risk_score: float = Field(..., description="Operational risk component")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    mitigation_recommendations: List[str] = Field(..., description="Risk mitigation recommendations")
    confidence: float = Field(..., ge=0, le=1, description="Assessment confidence")
    assessment_timestamp: datetime = Field(..., description="Assessment timestamp")


class CreditScoreResponse(BaseModel):
    """Credit scoring response"""
    overall_score: int = Field(..., ge=300, le=850, description="Overall credit score")
    traditional_score: Optional[int] = Field(None, description="Traditional credit score component")
    blockchain_score: int = Field(..., description="Blockchain-based score component")
    behavioral_score: int = Field(..., description="Behavioral score component")
    confidence_level: float = Field(..., ge=0, le=1, description="Score confidence")
    positive_factors: List[str] = Field(..., description="Positive credit factors")
    negative_factors: List[str] = Field(..., description="Negative credit factors")
    recommendations: List[str] = Field(..., description="Credit improvement recommendations")
    risk_level: str = Field(..., description="Credit risk level")
    score_timestamp: datetime = Field(..., description="Score calculation timestamp")


class ComplianceCheckResponse(BaseModel):
    """Compliance check response"""
    is_compliant: bool = Field(..., description="Whether the rate is compliant")
    jurisdiction: JurisdictionEnum = Field(..., description="Checked jurisdiction")
    applied_rate: float = Field(..., description="Rate after compliance adjustments")
    max_allowed_rate: float = Field(..., description="Maximum allowed rate")
    violations: List[str] = Field(..., description="Compliance violations")
    warnings: List[str] = Field(..., description="Compliance warnings")
    required_disclosures: List[str] = Field(..., description="Required disclosures")
    compliance_score: float = Field(..., ge=0, le=1, description="Compliance score")
    check_timestamp: datetime = Field(..., description="Check timestamp")


class PaymentDetails(BaseModel):
    """Loan payment details"""
    monthly_payment: float = Field(..., description="Monthly payment amount")
    total_payment: float = Field(..., description="Total payment over loan term")
    total_interest: float = Field(..., description="Total interest paid")
    annual_percentage_rate: float = Field(..., description="APR including all costs")


class RateCalculationResponse(BaseModel):
    """Comprehensive rate calculation response"""
    final_rate: float = Field(..., description="Final calculated annual interest rate")
    rate_components: Dict[str, float] = Field(..., description="Breakdown of rate components")
    payment_details: PaymentDetails = Field(..., description="Payment calculation details")
    market_analysis: Optional[MarketAnalysisResponse] = Field(None, description="Market analysis results")
    risk_assessment: Optional[RiskAssessmentResponse] = Field(None, description="Risk assessment results")
    credit_score: Optional[CreditScoreResponse] = Field(None, description="Credit scoring results")
    compliance_check: Optional[ComplianceCheckResponse] = Field(None, description="Compliance check results")
    calculation_timestamp: datetime = Field(..., description="Calculation timestamp")
    confidence: float = Field(..., ge=0, le=1, description="Overall calculation confidence")


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class RateUpdateMessage(BaseModel):
    """Real-time rate update message"""
    asset: str = Field(..., description="Asset symbol")
    base_rate: float = Field(..., description="Updated base rate")
    market_sentiment: str = Field(..., description="Current market sentiment")
    volatility_score: float = Field(..., description="Current volatility")
    update_timestamp: datetime = Field(..., description="Update timestamp")


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = Field("validation_error", description="Error type")
    message: str = Field(..., description="Validation error message")
    field_errors: List[Dict[str, str]] = Field(..., description="Field-specific errors")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")