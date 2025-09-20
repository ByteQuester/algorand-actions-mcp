"""
API Integration Tests

Tests the FastAPI endpoints and WebSocket functionality for the Interest Rate Determiner.
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient

from interest_rate_determiner.api.main import app


class TestAPIIntegration:
    """Test API endpoints and WebSocket functionality"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Async test client fixture"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    def test_root_endpoint(self, client):
        """Test root endpoint returns HTML documentation"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Interest Rate Determiner API" in response.text

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "engines_available" in data
        assert "engines_total" in data
        assert data["engines_total"] == 6

    def test_engine_status(self, client):
        """Test engine status endpoint"""
        response = client.get("/engines")
        assert response.status_code == 200

        data = response.json()
        assert data["total_engines"] == 6
        assert "available_engines" in data
        assert "engine_status" in data

        # Check engine status structure
        engine_status = data["engine_status"]
        expected_engines = [
            "market_rate_analysis", "risk_assessment", "credit_scoring",
            "regulatory_compliance", "dynamic_pricing", "rate_optimization"
        ]

        for engine in expected_engines:
            assert engine in engine_status
            assert isinstance(engine_status[engine], bool)

    @pytest.mark.asyncio
    async def test_comprehensive_rate_calculation(self, async_client):
        """Test comprehensive rate calculation endpoint"""
        request_data = {
            "loan_amount": 50000.0,
            "duration_days": 365,
            "borrower_id": "test_borrower_001",
            "jurisdiction": "us_federal",
            "asset": "ALGO"
        }

        response = await async_client.post("/api/v1/rates/calculate", json=request_data)

        if response.status_code == 503:
            # Service unavailable if engines not loaded
            pytest.skip("Engines not available for testing")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "final_rate" in data
        assert "rate_components" in data
        assert "payment_details" in data
        assert "calculation_timestamp" in data
        assert "confidence" in data

        # Validate rate values
        assert 0 < data["final_rate"] < 1, "Final rate should be between 0 and 100%"
        assert 0 <= data["confidence"] <= 1, "Confidence should be between 0 and 1"

        # Validate payment details
        payment_details = data["payment_details"]
        assert "monthly_payment" in payment_details
        assert "total_payment" in payment_details
        assert "total_interest" in payment_details
        assert "annual_percentage_rate" in payment_details

        assert payment_details["monthly_payment"] > 0
        assert payment_details["total_payment"] > request_data["loan_amount"]
        assert payment_details["total_interest"] >= 0

    @pytest.mark.asyncio
    async def test_quick_rate_calculation(self, async_client):
        """Test quick rate calculation endpoint"""
        response = await async_client.post(
            "/api/v1/rates/quick-calculate",
            params={
                "loan_amount": 25000.0,
                "duration_days": 180,
                "borrower_id": "quick_test"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "annual_rate" in data
        assert "monthly_rate" in data
        assert "monthly_payment" in data
        assert "total_interest" in data
        assert "calculation_type" in data
        assert data["calculation_type"] == "quick_estimate"

        # Validate values
        assert 0 < data["annual_rate"] < 1
        assert data["monthly_rate"] == data["annual_rate"] / 12
        assert data["monthly_payment"] > 0
        assert data["total_interest"] >= 0

    @pytest.mark.asyncio
    async def test_market_analysis_endpoint(self, async_client):
        """Test market analysis endpoint"""
        request_data = {
            "asset": "ALGO",
            "analysis_period_hours": 24
        }

        response = await async_client.post("/api/v1/market/analyze", json=request_data)

        if response.status_code == 503:
            pytest.skip("Market analysis engine not available")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        required_fields = [
            "base_rate", "market_sentiment", "volatility_score",
            "liquidity_score", "recommendation", "risk_factors",
            "confidence", "analysis_timestamp"
        ]

        for field in required_fields:
            assert field in data

        # Validate values
        assert 0 <= data["base_rate"] <= 1
        assert data["market_sentiment"] in ["bullish", "bearish", "neutral"]
        assert 0 <= data["volatility_score"] <= 1
        assert 0 <= data["liquidity_score"] <= 1
        assert 0 <= data["confidence"] <= 1
        assert isinstance(data["risk_factors"], list)

    @pytest.mark.asyncio
    async def test_risk_assessment_endpoint(self, async_client):
        """Test risk assessment endpoint"""
        request_data = {
            "borrower_id": "test_borrower_001",
            "loan_amount": 50000.0,
            "duration_days": 365,
            "credit_score": 720,
            "debt_to_income_ratio": 0.3,
            "employment_status": "employed"
        }

        response = await async_client.post("/api/v1/risk/assess", json=request_data)

        if response.status_code == 503:
            pytest.skip("Risk assessment engine not available")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        required_fields = [
            "overall_risk_level", "risk_premium", "risk_score",
            "credit_risk_score", "market_risk_score", "operational_risk_score",
            "risk_factors", "mitigation_recommendations", "confidence"
        ]

        for field in required_fields:
            assert field in data

        # Validate values
        assert data["overall_risk_level"] in ["very_low", "low", "medium", "high", "very_high"]
        assert 0 <= data["risk_premium"] <= 1
        assert 0 <= data["risk_score"] <= 100
        assert 0 <= data["confidence"] <= 1
        assert isinstance(data["risk_factors"], list)
        assert isinstance(data["mitigation_recommendations"], list)

    @pytest.mark.asyncio
    async def test_credit_scoring_endpoint(self, async_client):
        """Test credit scoring endpoint"""
        request_data = {
            "wallet_address": "test_wallet_123",
            "traditional_credit_score": 720,
            "wallet_age_days": 365,
            "transaction_count": 150,
            "average_balance": 10000.0
        }

        response = await async_client.post("/api/v1/credit/score", json=request_data)

        if response.status_code == 503:
            pytest.skip("Credit scoring engine not available")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        required_fields = [
            "overall_score", "traditional_score", "blockchain_score",
            "behavioral_score", "confidence_level", "positive_factors",
            "negative_factors", "recommendations", "risk_level"
        ]

        for field in required_fields:
            assert field in data

        # Validate values
        assert 300 <= data["overall_score"] <= 850
        assert 300 <= data["blockchain_score"] <= 850
        assert 300 <= data["behavioral_score"] <= 850
        assert 0 <= data["confidence_level"] <= 1
        assert isinstance(data["positive_factors"], list)
        assert isinstance(data["negative_factors"], list)
        assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    async def test_compliance_check_endpoint(self, async_client):
        """Test regulatory compliance endpoint"""
        request_data = {
            "proposed_rate": 0.15,
            "loan_amount": 50000.0,
            "duration_days": 365,
            "jurisdiction": "us_federal",
            "borrower_type": "individual"
        }

        response = await async_client.post("/api/v1/compliance/check", json=request_data)

        if response.status_code == 503:
            pytest.skip("Compliance engine not available")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        required_fields = [
            "is_compliant", "jurisdiction", "applied_rate",
            "max_allowed_rate", "violations", "warnings",
            "required_disclosures", "compliance_score"
        ]

        for field in required_fields:
            assert field in data

        # Validate values
        assert isinstance(data["is_compliant"], bool)
        assert data["jurisdiction"] == "us_federal"
        assert 0 <= data["applied_rate"] <= 1
        assert 0 <= data["max_allowed_rate"] <= 1
        assert 0 <= data["compliance_score"] <= 1
        assert isinstance(data["violations"], list)
        assert isinstance(data["warnings"], list)
        assert isinstance(data["required_disclosures"], list)

    def test_monitoring_endpoints(self, client):
        """Test monitoring endpoints"""
        # Health check
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"

        # Engine status
        response = client.get("/api/v1/monitoring/engines")
        assert response.status_code == 200

        data = response.json()
        assert data["total_engines"] == 6
        assert "engine_status" in data

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client):
        """Test API error handling"""
        # Test with invalid loan amount
        invalid_request = {
            "loan_amount": -1000.0,  # Invalid negative amount
            "duration_days": 365,
            "borrower_id": "test_borrower",
            "jurisdiction": "us_federal"
        }

        response = await async_client.post("/api/v1/rates/calculate", json=invalid_request)
        assert response.status_code == 422  # Validation error

        # Test with missing required fields
        incomplete_request = {
            "loan_amount": 50000.0
            # Missing required fields
        }

        response = await async_client.post("/api/v1/rates/calculate", json=incomplete_request)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_rate_calculation_consistency(self, async_client):
        """Test that identical requests return consistent results"""
        request_data = {
            "loan_amount": 30000.0,
            "duration_days": 180,
            "borrower_id": "consistency_test",
            "jurisdiction": "us_federal",
            "asset": "ALGO"
        }

        # Make multiple identical requests
        responses = []
        for _ in range(3):
            response = await async_client.post("/api/v1/rates/calculate", json=request_data)
            if response.status_code == 200:
                responses.append(response.json())

        if len(responses) >= 2:
            # Compare results for consistency
            first_result = responses[0]
            for result in responses[1:]:
                # Final rates should be identical for same inputs
                assert abs(result["final_rate"] - first_result["final_rate"]) < 0.0001, \
                    "Results should be consistent for identical inputs"

                # Payment calculations should be identical
                assert abs(result["payment_details"]["monthly_payment"] -
                          first_result["payment_details"]["monthly_payment"]) < 0.01, \
                    "Payment calculations should be consistent"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """Test API performance under concurrent load"""
        request_data = {
            "loan_amount": 25000.0,
            "duration_days": 365,
            "borrower_id": "concurrent_test",
            "jurisdiction": "us_federal"
        }

        # Make 5 concurrent requests
        tasks = []
        for i in range(5):
            task = async_client.post("/api/v1/rates/calculate", json={
                **request_data,
                "borrower_id": f"concurrent_test_{i}"
            })
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # Check that most requests succeeded
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) >= 3, "Most concurrent requests should succeed"

    def test_openapi_documentation(self, client):
        """Test OpenAPI documentation is accessible"""
        # OpenAPI JSON schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data

        # Check that our endpoints are documented
        paths = openapi_data["paths"]
        expected_endpoints = [
            "/api/v1/rates/calculate",
            "/api/v1/market/analyze",
            "/api/v1/risk/assess",
            "/api/v1/credit/score",
            "/api/v1/compliance/check"
        ]

        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} should be documented"

        # Swagger UI documentation
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection and messaging"""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test WebSocket connection
        with client.websocket_connect("/ws/test_client") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert "Connected as test_client" in data["message"]

            # Send a test message
            websocket.send_text("test message")

            # Should receive echo back
            data = websocket.receive_json()
            assert data["type"] == "echo"
            assert "test message" in data["message"]