#!/usr/bin/env python3
"""
Lending Platform API Server
Clean FastAPI server for lending operations
"""

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Import from the local lending core
from ...core.lending.src import (
    LendingWorkflow,
    LoanRequestAPI,
    LoanStatusResponse,
    LoanAcceptanceAPI,
    HealthResponse,
    ErrorResponse,
    LendingError,
    ErrorHandler
)
from ...core.lending.src.api_models import convert_api_to_internal_request

from .auth import AuthHandler, get_current_user
from .storage import LoanStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Lending Platform API",
    description="Clean lending API for Algorand-based lending operations",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Configure CORS from environment
import os
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:8081").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize components
auth_handler = AuthHandler()
loan_storage = LoanStorage()
lending_workflow = LendingWorkflow()

# Security
security = HTTPBearer()


@app.exception_handler(LendingError)
async def lending_error_handler(request, exc: LendingError):
    """Handle lending platform errors"""
    error_handler = ErrorHandler()
    error_info = error_handler.handle_error(exc)
    return JSONResponse(
        status_code=400,
        content=error_info
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Service health check"""
    try:
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat(),
            services={
                "lending_workflow": "operational",
                "loan_storage": "operational",
                "auth_service": "operational"
            },
            active_loans=await loan_storage.count_active_loans()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )


@app.post("/api/v1/loans/request", response_model=LoanStatusResponse)
async def submit_loan_request(
    loan_request: LoanRequestAPI,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit a new loan application"""
    try:
        logger.info(f"Processing loan request from user {user.get('email')}")

        # Generate unique loan ID
        loan_id = str(uuid.uuid4())

        # Convert API model to internal format
        internal_request = convert_api_to_internal_request(
            loan_request,
            user.get("algorand_address")
        )

        # Validate borrower address
        if not internal_request["borrower"]:
            raise HTTPException(
                status_code=400,
                detail="Borrower address required - please provide in request or link Algorand wallet to profile"
            )

        # Store loan request
        await loan_storage.store_loan(loan_id, {
            "id": loan_id,
            "user_id": user.get("user_id"),
            "status": "requested",
            "request_data": internal_request,
            "created_at": datetime.utcnow().isoformat(),
            "workflow_id": None
        })

        # Start async workflow processing
        asyncio.create_task(process_loan_workflow(loan_id, internal_request))

        # Return immediate response
        return LoanStatusResponse(
            loan_id=loan_id,
            status="requested",
            created_at=datetime.utcnow().isoformat(),
            amount_micro_algos=loan_request.amount_micro_algos,
            duration_days=loan_request.duration_days,
            collateral_type=loan_request.collateral_type,
            next_actions=["Processing loan request", "Analyzing liquidity", "Generating terms"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit loan request: {e}")
        raise HTTPException(status_code=500, detail="Failed to process loan request")


@app.get("/api/v1/loans/{loan_id}", response_model=LoanStatusResponse)
async def get_loan_status(
    loan_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get loan status"""
    try:
        loan = await loan_storage.get_loan(loan_id)
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # Check user ownership
        if loan.get("user_id") != user.get("user_id"):
            raise HTTPException(status_code=403, detail="Not authorized to access this loan")

        # Get workflow status if available
        workflow_status = None
        if loan.get("workflow_id"):
            try:
                workflow_status = await lending_workflow.get_workflow_status(loan["workflow_id"])
            except Exception as e:
                logger.warning(f"Failed to get workflow status: {e}")

        return LoanStatusResponse(
            loan_id=loan_id,
            status=loan.get("status", "unknown"),
            created_at=loan.get("created_at"),
            amount_micro_algos=loan["request_data"]["amount"],
            duration_days=loan["request_data"]["duration"],
            collateral_type=loan["request_data"]["collateral_type"],
            terms=loan.get("terms"),
            transaction_id=loan.get("transaction_id"),
            workflow_status=workflow_status,
            next_actions=loan.get("next_actions", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get loan status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve loan status")


@app.post("/api/v1/loans/{loan_id}/accept", response_model=LoanStatusResponse)
async def accept_loan_terms(
    loan_id: str,
    acceptance: LoanAcceptanceAPI,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Accept or reject loan terms"""
    try:
        loan = await loan_storage.get_loan(loan_id)
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # Check user ownership
        if loan.get("user_id") != user.get("user_id"):
            raise HTTPException(status_code=403, detail="Not authorized to access this loan")

        # Update loan status
        if acceptance.accepted:
            loan["status"] = "accepted"
            loan["acceptance_timestamp"] = datetime.utcnow().isoformat()
            loan["collateral_transaction_id"] = acceptance.collateral_transaction_id
            loan["acceptance_notes"] = acceptance.notes
        else:
            loan["status"] = "rejected"
            loan["rejection_timestamp"] = datetime.utcnow().isoformat()
            loan["rejection_notes"] = acceptance.notes

        await loan_storage.update_loan(loan_id, loan)

        return LoanStatusResponse(
            loan_id=loan_id,
            status=loan["status"],
            created_at=loan.get("created_at"),
            amount_micro_algos=loan["request_data"]["amount"],
            duration_days=loan["request_data"]["duration"],
            collateral_type=loan["request_data"]["collateral_type"],
            terms=loan.get("terms"),
            transaction_id=loan.get("transaction_id"),
            next_actions=["Loan terms processed"] if acceptance.accepted else ["Loan rejected"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process loan acceptance: {e}")
        raise HTTPException(status_code=500, detail="Failed to process loan acceptance")


@app.get("/api/v1/loans", response_model=List[LoanStatusResponse])
async def list_user_loans(user: Dict[str, Any] = Depends(get_current_user)):
    """List all loans for the current user"""
    try:
        loans = await loan_storage.get_user_loans(user.get("user_id"))

        loan_responses = []
        for loan in loans:
            loan_responses.append(LoanStatusResponse(
                loan_id=loan["id"],
                status=loan.get("status", "unknown"),
                created_at=loan.get("created_at"),
                amount_micro_algos=loan["request_data"]["amount"],
                duration_days=loan["request_data"]["duration"],
                collateral_type=loan["request_data"]["collateral_type"],
                terms=loan.get("terms"),
                transaction_id=loan.get("transaction_id"),
                next_actions=loan.get("next_actions", [])
            ))

        return loan_responses

    except Exception as e:
        logger.error(f"Failed to list user loans: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve loans")


async def process_loan_workflow(loan_id: str, request_data: Dict[str, Any]):
    """Process loan workflow asynchronously"""
    try:
        logger.info(f"Starting workflow processing for loan {loan_id}")

        # Process the lending request
        workflow_result = await lending_workflow.process_lending_request(request_data)

        # Update loan with workflow results
        loan_update = {
            "workflow_id": workflow_result.get("workflow_id"),
            "status": workflow_result.get("status", "failed"),
            "workflow_completed_at": datetime.utcnow().isoformat()
        }

        if workflow_result.get("status") == "ready_for_execution":
            loan_update["terms"] = workflow_result.get("recommended_terms")
            loan_update["next_actions"] = workflow_result.get("next_steps", [])
        elif workflow_result.get("status") == "failed":
            loan_update["error_message"] = workflow_result.get("error")
            loan_update["recovery_suggestions"] = workflow_result.get("recovery_suggestions", [])

        await loan_storage.update_loan(loan_id, loan_update)

        logger.info(f"Workflow processing completed for loan {loan_id}: {workflow_result.get('status')}")

    except Exception as e:
        logger.error(f"Workflow processing failed for loan {loan_id}: {e}")

        # Update loan with error status
        await loan_storage.update_loan(loan_id, {
            "status": "failed",
            "error_message": f"Workflow processing failed: {str(e)}",
            "workflow_failed_at": datetime.utcnow().isoformat()
        })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Lending Platform API server on {host}:{port}")

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )