"""
Escrow API Router
Implements REST endpoints for collateral enforcement
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..core.enforcement.models import (
    EscrowDeploymentRequest, EscrowDeploymentResponse,
    EscrowStatusResponse, LiquidationRequest, LiquidationResponse,
    ReleaseRequest, ReleaseResponse
)
from ..core.enforcement.escrow_service import EscrowService
from ..core.enforcement.mcp_integration import MCPConfig

from .auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/escrow",
    tags=["escrow"],
    responses={404: {"description": "Not found"}}
)

# Initialize escrow service
mcp_config = MCPConfig(
    writer_endpoint="http://localhost:3001",
    reader_endpoint="http://localhost:8002"
)
escrow_service = EscrowService(mcp_config)


@router.post("/deploy", response_model=EscrowDeploymentResponse)
async def deploy_escrow(
    request: EscrowDeploymentRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deploy a new escrow smart contract for loan collateral

    This endpoint creates and deploys a smart contract that will:
    - Hold collateral from the borrower
    - Enforce multi-signature requirements
    - Enable automatic liquidation on default
    - Release collateral upon loan repayment

    Args:
        request: Escrow deployment parameters including:
            - loan_id: Associated loan identifier
            - borrower: Borrower's Algorand address
            - lender: Lender's Algorand address
            - amount: Loan amount in microAlgos
            - collateral: Collateral amount in microAlgos
            - duration: Loan duration in days

    Returns:
        EscrowDeploymentResponse with:
            - escrow_id: Unique escrow identifier
            - escrow_address: On-chain escrow address
            - app_id: Smart contract application ID
            - transaction_id: Deployment transaction ID
    """
    try:
        logger.info(f"Deploying escrow for loan {request.loan_id} by user {user.get('email')}")

        # Validate user authorization
        if request.borrower != user.get("algorand_address") and \
           request.lender != user.get("algorand_address"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be either borrower or lender"
            )

        # Deploy escrow contract
        result = await escrow_service.deploy_escrow(request)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or "Escrow deployment failed"
            )

        logger.info(f"Successfully deployed escrow {result.escrow_id} at {result.escrow_address}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Escrow deployment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy escrow contract"
        )


@router.get("/{escrow_id}/status", response_model=EscrowStatusResponse)
async def get_escrow_status(
    escrow_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current status of an escrow contract

    Provides real-time information about:
    - Current balance held in escrow
    - Lock duration and expiry
    - Liquidation trigger status
    - Available actions (liquidate/release)

    Args:
        escrow_id: Unique escrow identifier

    Returns:
        EscrowStatusResponse with complete escrow state
    """
    try:
        logger.info(f"Getting status for escrow {escrow_id}")

        result = await escrow_service.get_escrow_status(escrow_id)

        # Verify user has access to this escrow
        user_address = user.get("algorand_address")
        if user_address not in [result.parties.get("borrower"),
                                result.parties.get("lender"),
                                result.parties.get("platform")]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this escrow"
            )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get escrow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve escrow status"
        )


@router.post("/{escrow_id}/liquidate", response_model=LiquidationResponse)
async def liquidate_escrow(
    escrow_id: str,
    request: LiquidationRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Execute liquidation of escrow collateral

    Triggers automatic transfer of collateral to lender when:
    - Loan payment is overdue beyond grace period
    - Collateral value falls below threshold
    - Manual liquidation with valid evidence

    Args:
        escrow_id: Unique escrow identifier
        request: Liquidation request with:
            - reason: Liquidation reason/trigger
            - evidence: Supporting evidence/data
            - force: Override automatic checks (platform only)

    Returns:
        LiquidationResponse with:
            - transaction_id: Liquidation transaction ID
            - distribution: Collateral distribution details
            - status: Updated escrow status
    """
    try:
        logger.info(f"Processing liquidation for escrow {escrow_id}")

        # Set requestor
        request.escrow_id = escrow_id
        request.requestor = user.get("email")

        # Get escrow status to verify authorization
        escrow_status = await escrow_service.get_escrow_status(escrow_id)

        user_address = user.get("algorand_address")
        is_platform = user.get("role") == "platform_admin"

        # Only lender or platform can initiate liquidation
        if user_address != escrow_status.parties.get("lender") and not is_platform:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only lender or platform can initiate liquidation"
            )

        # Only platform can force liquidation
        if request.force and not is_platform:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only platform administrators can force liquidation"
            )

        result = await escrow_service.liquidate_escrow(request)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or "Liquidation failed"
            )

        logger.info(f"Successfully liquidated escrow {escrow_id}: {result.transaction_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liquidation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute liquidation"
        )


@router.post("/{escrow_id}/release", response_model=ReleaseResponse)
async def release_collateral(
    escrow_id: str,
    request: ReleaseRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Release collateral back to borrower after loan repayment

    Executes collateral release when:
    - Loan has been fully repaid
    - Required signatures are provided
    - Release conditions are met

    Args:
        escrow_id: Unique escrow identifier
        request: Release request with:
            - authorization: Multi-sig authorization data
            - proof_of_payment: Transaction ID of loan repayment

    Returns:
        ReleaseResponse with:
            - transaction_id: Release transaction ID
            - released_amount: Amount returned to borrower
            - recipient: Borrower's address
    """
    try:
        logger.info(f"Processing collateral release for escrow {escrow_id}")

        # Set requestor
        request.escrow_id = escrow_id
        request.requestor = user.get("email")

        # Get escrow status
        escrow_status = await escrow_service.get_escrow_status(escrow_id)

        user_address = user.get("algorand_address")
        is_platform = user.get("role") == "platform_admin"

        # Platform or lender can authorize release
        if user_address not in [escrow_status.parties.get("lender"),
                                escrow_status.parties.get("platform")] and not is_platform:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to release collateral"
            )

        result = await escrow_service.release_collateral(request)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or "Release failed"
            )

        logger.info(f"Successfully released collateral from escrow {escrow_id}: {result.transaction_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Release error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to release collateral"
        )


@router.get("/loan/{loan_id}/escrows")
async def get_loan_escrows(
    loan_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all escrow contracts associated with a loan

    Args:
        loan_id: Loan identifier

    Returns:
        List of escrow contracts for the loan
    """
    try:
        # This would typically query a database
        # For now, return from in-memory storage
        escrows = [
            escrow for escrow in escrow_service.escrow_storage.values()
            if escrow.loan_id == loan_id
        ]

        # Verify user has access
        if escrows:
            sample_escrow = escrows[0]
            user_address = user.get("algorand_address")
            if user_address not in [sample_escrow.borrower, sample_escrow.lender]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view these escrows"
                )

        return {
            "loan_id": loan_id,
            "escrows": [
                {
                    "escrow_id": e.escrow_id,
                    "status": e.status.value,
                    "collateral_amount": e.collateral_amount,
                    "created_at": e.created_at.isoformat()
                }
                for e in escrows
            ],
            "count": len(escrows)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get loan escrows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve loan escrows"
        )