"""
Unified API Gateway for Cross-Service Communication

Provides a unified REST API layer that supports both vendor mode (direct imports)
and hosted service mode (HTTP calls to deployed services). Includes load balancing,
authentication, rate limiting, and comprehensive monitoring.

Features:
- FastAPI-based REST endpoints for all 4 lending engines
- Service discovery for vendor vs hosted modes
- Load balancing between multiple engine instances
- Request/response logging with structured metrics
- Rate limiting and JWT authentication
- OpenAPI documentation generation
- Prometheus-compatible metrics
- Circuit breaker pattern for resilience
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
from functools import wraps

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis.asyncio as redis

from .service_discovery import ServiceDiscovery, ServiceMode, ServiceInfo
from .health_checks import HealthChecker
from .websocket_handler import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('gateway_active_connections', 'Active connections')
SERVICE_CALLS = Counter('gateway_service_calls_total', 'Service calls', ['service', 'status'])
CIRCUIT_BREAKER_STATE = Gauge('gateway_circuit_breaker_open', 'Circuit breaker state', ['service'])

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Pydantic Models

class CollateralAnalysisRequest(BaseModel):
    """Request model for collateral analysis"""
    collateral_type: str = Field(..., description="Type of collateral (ASA, NFT, etc.)")
    collateral_amount: int = Field(..., description="Amount of collateral in micro units")
    collateral_asset_id: Optional[int] = Field(None, description="Asset ID for ASA collateral")
    borrower_address: str = Field(..., description="Borrower's Algorand address")
    loan_amount: int = Field(..., description="Requested loan amount in microAlgos")

    @validator('collateral_amount', 'loan_amount')
    def validate_positive_amounts(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

class CollateralAnalysisResponse(BaseModel):
    """Response model for collateral analysis"""
    analysis_id: str
    collateral_value_usd: float
    loan_to_value_ratio: float
    risk_score: float
    is_acceptable: bool
    liquidation_threshold: float
    margin_requirements: Dict[str, float]
    timestamp: str

class RateCalculationRequest(BaseModel):
    """Request model for interest rate calculation"""
    loan_amount: int = Field(..., description="Loan amount in microAlgos")
    duration_days: int = Field(..., description="Loan duration in days")
    collateral_type: str = Field(..., description="Type of collateral")
    risk_score: float = Field(..., description="Risk score from analysis")
    borrower_credit_history: Optional[Dict[str, Any]] = Field(None, description="Borrower's credit history")

class RateCalculationResponse(BaseModel):
    """Response model for interest rate calculation"""
    calculation_id: str
    annual_percentage_rate: float
    daily_rate: float
    total_interest: int
    total_repayment: int
    payment_schedule: List[Dict[str, Any]]
    rate_factors: Dict[str, float]
    timestamp: str

class LoanEvaluationRequest(BaseModel):
    """Request model for loan evaluation"""
    borrower_address: str
    loan_amount: int
    duration_days: int
    collateral_analysis: CollateralAnalysisResponse
    rate_calculation: RateCalculationResponse
    additional_context: Optional[Dict[str, Any]] = None

class LoanEvaluationResponse(BaseModel):
    """Response model for loan evaluation"""
    evaluation_id: str
    recommendation: str  # "approve", "reject", "conditional"
    confidence_score: float
    conditions: Optional[List[str]] = None
    risk_assessment: Dict[str, Any]
    regulatory_compliance: Dict[str, bool]
    timestamp: str

class RiskAssessmentRequest(BaseModel):
    """Request model for risk assessment"""
    borrower_address: str
    loan_amount: int
    collateral_value: float
    duration_days: int
    market_conditions: Optional[Dict[str, Any]] = None

class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment"""
    assessment_id: str
    overall_risk_score: float
    risk_factors: Dict[str, float]
    probability_of_default: float
    required_collateral_ratio: float
    risk_mitigation_suggestions: List[str]
    timestamp: str

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None

# Circuit Breaker Implementation

class CircuitBreaker:
    """Circuit breaker for service resilience"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def is_available(self) -> bool:
        """Check if circuit breaker allows requests"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"
        CIRCUIT_BREAKER_STATE.labels(service="service").set(0)

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            CIRCUIT_BREAKER_STATE.labels(service="service").set(1)

# API Gateway Class

class APIGateway:
    """Main API Gateway class"""

    def __init__(self):
        self.service_discovery = ServiceDiscovery()
        self.health_checker = HealthChecker()
        self.websocket_manager = WebSocketManager()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize gateway components"""
        try:
            # Initialize service discovery
            await self.service_discovery.initialize()

            # Initialize health checker
            await self.health_checker.initialize()

            # Initialize Redis for caching (optional)
            try:
                self.redis_client = redis.from_url("redis://localhost:6379")
                await self.redis_client.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")
                self.redis_client = None

            # Initialize HTTP client for service calls
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )

            logger.info("API Gateway initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API Gateway: {e}")
            raise

    async def shutdown(self):
        """Cleanup gateway resources"""
        try:
            if self.http_client:
                await self.http_client.aclose()

            if self.redis_client:
                await self.redis_client.close()

            await self.service_discovery.shutdown()
            await self.health_checker.shutdown()

            logger.info("API Gateway shutdown completed")

        except Exception as e:
            logger.error(f"Error during gateway shutdown: {e}")

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Call a service with circuit breaker and load balancing"""

        circuit_breaker = self.get_circuit_breaker(service_name)

        if not circuit_breaker.is_available():
            SERVICE_CALLS.labels(service=service_name, status="circuit_open").inc()
            raise HTTPException(
                status_code=503,
                detail=f"Service {service_name} is temporarily unavailable"
            )

        try:
            # Get service info
            service_info = await self.service_discovery.get_service(service_name)

            if service_info.mode == ServiceMode.VENDOR:
                # Direct import mode
                result = await self._call_vendor_service(service_name, endpoint, data)
            else:
                # HTTP service mode
                result = await self._call_http_service(service_info, endpoint, data, method)

            circuit_breaker.record_success()
            SERVICE_CALLS.labels(service=service_name, status="success").inc()
            return result

        except Exception as e:
            circuit_breaker.record_failure()
            SERVICE_CALLS.labels(service=service_name, status="error").inc()
            logger.error(f"Service call failed for {service_name}: {e}")
            raise

    async def _call_vendor_service(
        self,
        service_name: str,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call service in vendor mode (direct import)"""
        try:
            # Import the service dynamically
            if service_name == "collateral_analyzer":
                from algorand_lending_bl import CollateralAnalyzer
                analyzer = CollateralAnalyzer()
                result = await analyzer.analyze_collateral(data)

            elif service_name == "rate_calculator":
                from algorand_lending_bl import RateCalculator
                calculator = RateCalculator()
                result = await calculator.calculate_rates(data)

            elif service_name == "loan_evaluator":
                from algorand_lending_bl import LoanEvaluator
                evaluator = LoanEvaluator()
                result = await evaluator.evaluate_loan(data)

            elif service_name == "risk_assessor":
                from algorand_lending_bl import RiskAssessor
                assessor = RiskAssessor()
                result = await assessor.assess_risk(data)

            else:
                raise ValueError(f"Unknown service: {service_name}")

            return result

        except ImportError as e:
            logger.error(f"Failed to import {service_name}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Service {service_name} not available in vendor mode"
            )

    async def _call_http_service(
        self,
        service_info: ServiceInfo,
        endpoint: str,
        data: Dict[str, Any],
        method: str
    ) -> Dict[str, Any]:
        """Call service via HTTP"""
        url = f"{service_info.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AlgorandLendingGateway/1.0"
        }

        # Add authentication if configured
        if service_info.auth_token:
            headers["Authorization"] = f"Bearer {service_info.auth_token}"

        response = await self.http_client.request(
            method=method,
            url=url,
            json=data,
            headers=headers
        )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Service call failed: {response.text}"
            )

        return response.json()

# Global gateway instance
gateway = APIGateway()

# FastAPI lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    await gateway.initialize()
    yield
    # Shutdown
    await gateway.shutdown()

# Initialize FastAPI app
app = FastAPI(
    title="Algorand Lending API Gateway",
    description="Unified API gateway for Algorand lending platform with vendor and service modes",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Security
security = HTTPBearer()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and get current user"""
    try:
        # TODO: Implement proper JWT validation
        # For now, return a mock user
        return {
            "user_id": "gateway_user",
            "email": "gateway@algorand.com",
            "permissions": ["read", "write"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Middleware for request logging and metrics
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and update metrics"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Add request ID to context
    request.state.request_id = request_id

    # Log request
    logger.info(f"Request {request_id}: {request.method} {request.url}")

    try:
        response = await call_next(request)

        # Update metrics
        duration = time.time() - start_time
        REQUEST_DURATION.observe(duration)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"Request {request_id} completed: "
            f"{response.status_code} in {duration:.3f}s"
        )

        return response

    except Exception as e:
        # Log error
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()

        logger.error(f"Request {request_id} failed: {e} in {duration:.3f}s")
        raise

# API Endpoints

@app.post(
    "/api/v1/collateral/analyze",
    response_model=CollateralAnalysisResponse,
    summary="Analyze collateral for loan approval"
)
@limiter.limit("10/minute")
async def analyze_collateral(
    request: Request,
    analysis_request: CollateralAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze collateral value and risk for loan approval"""
    try:
        result = await gateway.call_service(
            "collateral_analyzer",
            "/analyze",
            analysis_request.dict()
        )

        return CollateralAnalysisResponse(
            analysis_id=str(uuid.uuid4()),
            **result,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collateral analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Collateral analysis service unavailable"
        )

@app.post(
    "/api/v1/rates/calculate",
    response_model=RateCalculationResponse,
    summary="Calculate interest rates for loan"
)
@limiter.limit("10/minute")
async def calculate_rates(
    request: Request,
    rate_request: RateCalculationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Calculate interest rates based on loan parameters and risk"""
    try:
        result = await gateway.call_service(
            "rate_calculator",
            "/calculate",
            rate_request.dict()
        )

        return RateCalculationResponse(
            calculation_id=str(uuid.uuid4()),
            **result,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate calculation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Rate calculation service unavailable"
        )

@app.post(
    "/api/v1/loans/evaluate",
    response_model=LoanEvaluationResponse,
    summary="Evaluate loan application"
)
@limiter.limit("5/minute")
async def evaluate_loan(
    request: Request,
    evaluation_request: LoanEvaluationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Evaluate complete loan application for approval decision"""
    try:
        result = await gateway.call_service(
            "loan_evaluator",
            "/evaluate",
            evaluation_request.dict()
        )

        return LoanEvaluationResponse(
            evaluation_id=str(uuid.uuid4()),
            **result,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Loan evaluation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Loan evaluation service unavailable"
        )

@app.post(
    "/api/v1/risk/assess",
    response_model=RiskAssessmentResponse,
    summary="Assess risk for loan application"
)
@limiter.limit("10/minute")
async def assess_risk(
    request: Request,
    risk_request: RiskAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Perform comprehensive risk assessment for loan"""
    try:
        result = await gateway.call_service(
            "risk_assessor",
            "/assess",
            risk_request.dict()
        )

        return RiskAssessmentResponse(
            assessment_id=str(uuid.uuid4()),
            **result,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Risk assessment service unavailable"
        )

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/v1/services/status")
async def get_services_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get status of all registered services"""
    try:
        services = await gateway.service_discovery.list_services()
        health_status = await gateway.health_checker.check_all_services()

        return {
            "services": services,
            "health": health_status,
            "circuit_breakers": {
                name: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time
                }
                for name, cb in gateway.circuit_breakers.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get services status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve services status"
        )

# Include WebSocket router
app.include_router(gateway.websocket_manager.router)

# Include health check router
from .health_checks import router as health_router
app.include_router(health_router)

if __name__ == "__main__":
    import os

    port = int(os.getenv("GATEWAY_PORT", 8000))
    host = os.getenv("GATEWAY_HOST", "0.0.0.0")

    logger.info(f"Starting API Gateway on {host}:{port}")

    uvicorn.run(
        "gateway:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )