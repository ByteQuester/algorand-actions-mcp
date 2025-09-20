#!/usr/bin/env python3
"""
Fixed API Server - Integrates with Working Lending System
No import errors, uses proven business logic
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import sqlite3
import uvicorn

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the working lending system
from working_lending_system import WorkingLendingPlatform

# ============= Data Models =============

class LoanApplication(BaseModel):
    """Loan application request model"""
    borrower_name: str = Field(..., min_length=1, max_length=100)
    borrower_address: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=1000000)
    duration_days: int = Field(..., ge=30, le=365)
    purpose: str = Field(default="general")
    credit_score: Optional[int] = Field(None, ge=300, le=850)
    debt_to_income: Optional[float] = Field(None, ge=0, le=1)
    payment_history: Optional[int] = Field(None, ge=0, le=100)
    collateral_offered: Optional[float] = Field(None, ge=0)


class LoanResponse(BaseModel):
    """Loan processing response model"""
    loan_id: str
    status: str
    risk_score: int
    risk_level: str
    interest_rate: float
    collateral_required: float
    decision_reason: str
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    database_status: str
    total_loans: int
    approved_loans: int
    rejected_loans: int
    approval_rate: str
    uptime_seconds: float


# ============= API Application =============

app = FastAPI(
    title="Algorand Lending Platform API",
    description="Fixed API server integrating with working lending system",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global platform instance
lending_platform = WorkingLendingPlatform()
start_time = datetime.now()


# ============= API Endpoints =============

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Algorand Lending Platform API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint with system statistics"""

    try:
        # Get database statistics
        conn = sqlite3.connect(lending_platform.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM loans")
        total_loans = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'approved'")
        approved = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'rejected'")
        rejected = cursor.fetchone()[0]

        conn.close()

        approval_rate = f"{(approved/total_loans*100 if total_loans > 0 else 0):.1f}%"
        uptime = (datetime.now() - start_time).total_seconds()

        return HealthResponse(
            status="healthy",
            database_status="connected",
            total_loans=total_loans,
            approved_loans=approved,
            rejected_loans=rejected,
            approval_rate=approval_rate,
            uptime_seconds=uptime
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            database_status=f"error: {str(e)}",
            total_loans=0,
            approved_loans=0,
            rejected_loans=0,
            approval_rate="0.0%",
            uptime_seconds=0
        )


@app.post("/api/v1/loans/apply", response_model=LoanResponse, tags=["Loans"])
async def apply_for_loan(application: LoanApplication):
    """Process a new loan application"""

    try:
        # Convert Pydantic model to dict for processing
        app_data = application.dict()

        # Process the loan application
        result = lending_platform.process_loan_application(app_data)

        # Return formatted response
        return LoanResponse(
            loan_id=result["loan_id"],
            status=result["status"],
            risk_score=result["risk_assessment"]["final_risk_score"],
            risk_level=result["risk_assessment"]["risk_level"],
            interest_rate=result["terms"]["interest_rate"],
            collateral_required=result["terms"]["collateral_required"],
            decision_reason=result["decision_reason"],
            timestamp=result["timestamp"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process loan application: {str(e)}"
        )


@app.get("/api/v1/loans/{loan_id}", tags=["Loans"])
async def get_loan_details(loan_id: str):
    """Get details of a specific loan"""

    loan = lending_platform.get_loan_status(loan_id)

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan {loan_id} not found"
        )

    return loan


@app.get("/api/v1/audit/{loan_id}", tags=["Audit"])
async def get_audit_trail(loan_id: str):
    """Get complete audit trail for a loan"""

    audit_trail = lending_platform.get_audit_trail(loan_id)

    if not audit_trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit trail found for loan {loan_id}"
        )

    return {
        "loan_id": loan_id,
        "events_count": len(audit_trail),
        "events": audit_trail,
        "complete": True
    }


@app.get("/api/v1/loans", tags=["Loans"])
async def list_loans(limit: int = 10, offset: int = 0):
    """List all loans with pagination"""

    try:
        conn = sqlite3.connect(lending_platform.db_path)
        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM loans")
        total = cursor.fetchone()[0]

        # Get paginated results
        cursor.execute("""
            SELECT loan_id, borrower_name, amount, status,
                   risk_score, interest_rate, created_at
            FROM loans
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        loans = []
        for row in rows:
            loans.append({
                "loan_id": row[0],
                "borrower_name": row[1],
                "amount": row[2],
                "status": row[3],
                "risk_score": row[4],
                "interest_rate": row[5],
                "created_at": row[6]
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "loans": loans
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve loans: {str(e)}"
        )


@app.get("/api/v1/statistics", tags=["Analytics"])
async def get_statistics():
    """Get platform statistics and analytics"""

    report = lending_platform.generate_report()

    return {
        "summary": report["summary"],
        "recent_loans": report["recent_loans"],
        "database_info": {
            "location": str(report["database_location"]),
            "audit_log": str(report["audit_log_location"])
        },
        "generated_at": report["report_generated"]
    }


@app.post("/api/v1/loans/{loan_id}/update-status", tags=["Loans"])
async def update_loan_status(loan_id: str, new_status: str):
    """Update the status of a loan (for testing/admin)"""

    if new_status not in ["pending", "approved", "rejected", "funded", "repaid", "defaulted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {new_status}"
        )

    try:
        conn = sqlite3.connect(lending_platform.db_path)
        cursor = conn.cursor()

        # Check if loan exists
        cursor.execute("SELECT loan_id FROM loans WHERE loan_id = ?", (loan_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Loan {loan_id} not found"
            )

        # Update status
        cursor.execute("""
            UPDATE loans
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE loan_id = ?
        """, (new_status, loan_id))

        conn.commit()
        conn.close()

        # Log audit event
        lending_platform._log_audit_event(
            loan_id=loan_id,
            event_type="STATUS_UPDATED",
            event_data={"new_status": new_status, "updated_via": "API"}
        )

        return {
            "loan_id": loan_id,
            "new_status": new_status,
            "updated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update loan status: {str(e)}"
        )


# ============= Exception Handlers =============

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Resource not found",
        "detail": str(exc.detail) if hasattr(exc, 'detail') else "The requested resource was not found",
        "status_code": 404
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Internal server error",
        "detail": "An unexpected error occurred",
        "status_code": 500
    }


# ============= Startup/Shutdown Events =============

@app.on_event("startup")
async def startup_event():
    """Initialize the platform on startup"""
    print("🚀 Starting Algorand Lending Platform API...")
    print(f"📁 Database: {lending_platform.db_path}")
    print(f"📝 Audit Log: {lending_platform.audit_log_path}")
    print("✅ API Ready at http://localhost:8003")
    print("📚 API Docs at http://localhost:8003/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Algorand Lending Platform API...")


# ============= Main Entry Point =============

if __name__ == "__main__":
    print("=" * 60)
    print("🏦 ALGORAND LENDING PLATFORM - FIXED API SERVER")
    print("=" * 60)
    print()

    # Run the server
    uvicorn.run(
        "fixed_server:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )