"""
API Models for Lending Platform
Clean API contract definitions with validation
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from .models import CollateralType


class LoanRequestAPI(BaseModel):
    """Loan request model for API"""
    amount_micro_algos: int = Field(
        ...,
        ge=1000000,  # Minimum 1 ALGO
        le=100000000000,  # Maximum 100,000 ALGO
        description="Loan amount in microAlgos (1 ALGO = 1,000,000 microAlgos)"
    )
    duration_days: int = Field(
        ...,
        ge=1,
        le=365,
        description="Loan duration in days (1-365)"
    )
    max_interest_rate: float = Field(
        ...,
        ge=0.0,
        le=50.0,
        description="Maximum acceptable interest rate (annual %)"
    )
    collateral_type: str = Field(
        ...,
        description="Type of collateral (ALGO, USDC, ASA)"
    )
    collateral_amount: int = Field(
        ...,
        ge=0,
        description="Collateral amount in base units"
    )
    borrower_address: Optional[str] = Field(
        None,
        min_length=58,
        max_length=58,
        description="Algorand address of borrower"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the loan request"
    )

    @validator('collateral_type')
    def validate_collateral_type(cls, v):
        try:
            CollateralType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid collateral type. Must be one of: {[e.value for e in CollateralType]}")

    @validator('borrower_address')
    def validate_algorand_address(cls, v):
        if v is None:
            return v
        if len(v) != 58:
            raise ValueError("Algorand address must be exactly 58 characters")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Invalid Algorand address format")
        return v

    class Config:
        schema_extra = {
            "example": {
                "amount_micro_algos": 10000000,  # 10 ALGO
                "duration_days": 30,
                "max_interest_rate": 8.5,
                "collateral_type": "ALGO",
                "collateral_amount": 13000000,  # 13 ALGO (130% collateralization)
                "borrower_address": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                "metadata": {
                    "purpose": "Working capital",
                    "business_type": "DeFi protocol"
                }
            }
        }


class LoanStatusResponse(BaseModel):
    """Loan status response model"""
    loan_id: str
    status: str
    created_at: str
    amount_micro_algos: int
    duration_days: int
    collateral_type: str
    terms: Optional[Dict[str, Any]] = None
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    workflow_status: Optional[Dict[str, Any]] = None
    next_actions: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "loan_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "negotiating",
                "created_at": "2025-01-15T10:30:00Z",
                "amount_micro_algos": 10000000,
                "duration_days": 30,
                "collateral_type": "ALGO",
                "terms": {
                    "lender": "AJNNFQN7DSR7QEY766Q7JXW5JWF6WC4BFHSEWH7JDQFV5DXHGHH2KN7N7A",
                    "interest_rate": 7.5,
                    "collateral_ratio": 1.3
                },
                "next_actions": ["Review proposed terms", "Accept or reject terms"]
            }
        }


class LoanAcceptanceAPI(BaseModel):
    """Loan term acceptance model"""
    accepted: bool = Field(
        ...,
        description="Whether the borrower accepts the negotiated terms"
    )
    collateral_transaction_id: Optional[str] = Field(
        None,
        description="Transaction ID for collateral deposit"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional notes from borrower"
    )

    class Config:
        schema_extra = {
            "example": {
                "accepted": True,
                "collateral_transaction_id": "ABCD1234567890ABCD1234567890ABCD1234567890ABCD1234567890ABCD",
                "notes": "Terms acceptable, proceeding with loan"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Response timestamp")
    services: Optional[Dict[str, str]] = Field(
        None,
        description="Status of dependent services"
    )
    active_loans: Optional[int] = Field(
        None,
        description="Number of active loans"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if unhealthy"
    )


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Error timestamp"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracking"
    )


def convert_api_to_internal_request(api_request: LoanRequestAPI, user_address: str = None) -> Dict[str, Any]:
    """Convert API request to internal lending request format"""
    return {
        "borrower": api_request.borrower_address or user_address,
        "amount": api_request.amount_micro_algos,
        "duration": api_request.duration_days,
        "max_interest_rate": api_request.max_interest_rate,
        "collateral_type": api_request.collateral_type,
        "collateral_amount": api_request.collateral_amount,
        "metadata": api_request.metadata or {}
    }