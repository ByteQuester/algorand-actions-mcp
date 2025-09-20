#!/usr/bin/env python3
"""
Microservice Integration Example

This demonstrates how to integrate the algorand-lending-business-logic package
into a REST API microservice using Flask.

Features:
- RESTful API endpoints for all lending engines
- JSON request/response handling
- Error handling and validation
- OpenAPI documentation
- Health checks

Usage:
    pip install flask
    python microservice_example.py

API Endpoints:
    POST /api/v1/loans/analyze - Full loan analysis
    POST /api/v1/collateral/analyze - Collateral analysis only
    POST /api/v1/interest-rates/calculate - Interest rate calculation
    POST /api/v1/loans/evaluate - Loan approval evaluation
    POST /api/v1/risk/assess - Risk assessment
    GET /health - Health check
    GET /api/v1/info - Service information
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add the vendor package to Python path (if not installed)
vendor_path = Path(__file__).parent / "algorand_lending_bl"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path.parent))

try:
    from flask import Flask, request, jsonify, Response
    from flask.logging import default_handler
except ImportError:
    print("❌ Flask not installed. Please run: pip install flask")
    sys.exit(1)

# Import lending business logic
from algorand_lending_bl import (
    create_lending_service,
    LoanRequest,
    AlgorandAddress,
    ASAToken,
    VENDOR_INFO,
    DEFAULT_CONFIG
)

# ============================================================================
# MICROSERVICE SETUP
# ============================================================================

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Initialize lending service once at startup
print("🚀 Initializing Algorand Lending Service...")
lending_service = create_lending_service()
print(f"✓ Service ready with {len(lending_service)} engines")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_algorand_address(address_str: str) -> bool:
    """Validate Algorand address format."""
    try:
        AlgorandAddress(address_str)
        return True
    except:
        return False

def parse_loan_request(data: dict) -> LoanRequest:
    """Parse JSON data into LoanRequest object."""
    try:
        borrower = AlgorandAddress(data['borrower'])

        collateral_assets = []
        for asset_data in data.get('collateral_assets', []):
            asset = ASAToken(
                asset_id=asset_data['asset_id'],
                amount=asset_data['amount']
            )
            collateral_assets.append(asset)

        return LoanRequest(
            borrower=borrower,
            requested_amount=data['requested_amount'],
            collateral_assets=collateral_assets,
            loan_duration_days=data.get('loan_duration_days', 30)
        )
    except KeyError as e:
        raise ValueError(f"Missing required field: {e}")
    except Exception as e:
        raise ValueError(f"Invalid request data: {e}")

def create_error_response(message: str, code: int = 400) -> Response:
    """Create standardized error response."""
    return jsonify({
        "error": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "code": code
    }), code

def create_success_response(data: dict, message: str = "Success") -> dict:
    """Create standardized success response."""
    return {
        "error": False,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test that all engines are accessible
        engines_status = {}
        for engine_name in lending_service.keys():
            if engine_name != 'config':
                engines_status[engine_name] = "healthy"

        return jsonify({
            "status": "healthy",
            "service": "algorand-lending-microservice",
            "version": VENDOR_INFO['version'],
            "engines": engines_status,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return create_error_response(f"Health check failed: {e}", 503)

@app.route('/api/v1/info', methods=['GET'])
def service_info():
    """Get service information."""
    return jsonify(create_success_response({
        "service": "Algorand Lending Business Logic Microservice",
        "vendor_info": VENDOR_INFO,
        "available_engines": list(lending_service.keys()),
        "endpoints": [
            "POST /api/v1/loans/analyze",
            "POST /api/v1/collateral/analyze",
            "POST /api/v1/interest-rates/calculate",
            "POST /api/v1/loans/evaluate",
            "POST /api/v1/risk/assess"
        ]
    }))

@app.route('/api/v1/loans/analyze', methods=['POST'])
def analyze_loan():
    """Complete loan analysis using all engines."""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("JSON body required")

        # Parse loan request
        loan_request = parse_loan_request(data)

        # Run all analyses
        print(f"🔍 Analyzing loan for {loan_request.borrower}")

        collateral_analysis = lending_service["collateral"].analyze_collateral(
            loan_request.collateral_assets,
            loan_request.borrower
        )

        rate_calculation = lending_service["interest_rates"].calculate_interest_rate(loan_request)
        loan_decision = lending_service["loan_approval"].evaluate_loan(loan_request)
        risk_assessment = lending_service["risk_assessment"].assess_risk(loan_request)

        # Prepare response
        analysis_data = {
            "loan_request": {
                "borrower": str(loan_request.borrower),
                "requested_amount": loan_request.requested_amount,
                "collateral_count": len(loan_request.collateral_assets),
                "duration_days": loan_request.loan_duration_days
            },
            "collateral_analysis": {
                "total_value": collateral_analysis.total_value,
                "liquidity_tier": collateral_analysis.liquidity_tier.value,
                "portfolio_risk": collateral_analysis.portfolio_risk.value,
                "liquidation_scenarios": len(collateral_analysis.liquidation_scenarios)
            },
            "interest_rate": {
                "base_rate": rate_calculation.base_rate,
                "final_rate": rate_calculation.final_rate,
                "risk_premium": rate_calculation.risk_premium,
                "rate_factors": {
                    "borrower_reputation": rate_calculation.rate_factors.borrower_reputation,
                    "collateral_quality": rate_calculation.rate_factors.collateral_quality,
                    "market_conditions": rate_calculation.rate_factors.market_conditions
                }
            },
            "loan_decision": {
                "decision": loan_decision.decision.value,
                "confidence": loan_decision.confidence.value,
                "approved_amount": loan_decision.approved_amount,
                "terms": {
                    "interest_rate": loan_decision.terms.interest_rate if loan_decision.terms else None,
                    "duration_days": loan_decision.terms.duration_days if loan_decision.terms else None
                } if loan_decision.terms else None
            },
            "risk_assessment": {
                "overall_score": risk_assessment.overall_score,
                "risk_level": risk_assessment.risk_level.value,
                "borrower_risk": risk_assessment.borrower_risk,
                "collateral_risk": risk_assessment.collateral_risk,
                "market_risk": risk_assessment.market_risk
            }
        }

        return jsonify(create_success_response(
            analysis_data,
            "Complete loan analysis completed successfully"
        ))

    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        print(f"❌ Error in loan analysis: {e}")
        return create_error_response(f"Analysis failed: {e}", 500)

@app.route('/api/v1/collateral/analyze', methods=['POST'])
def analyze_collateral():
    """Analyze collateral assets."""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("JSON body required")

        # Validate required fields
        if 'borrower' not in data or 'collateral_assets' not in data:
            return create_error_response("borrower and collateral_assets required")

        borrower = AlgorandAddress(data['borrower'])
        collateral_assets = []

        for asset_data in data['collateral_assets']:
            asset = ASAToken(
                asset_id=asset_data['asset_id'],
                amount=asset_data['amount']
            )
            collateral_assets.append(asset)

        # Analyze collateral
        analysis = lending_service["collateral"].analyze_collateral(collateral_assets, borrower)

        response_data = {
            "total_value": analysis.total_value,
            "liquidity_tier": analysis.liquidity_tier.value,
            "portfolio_risk": analysis.portfolio_risk.value,
            "asset_valuations": [
                {
                    "asset_id": val.asset.asset_id,
                    "current_price": val.current_price,
                    "total_value": val.total_value,
                    "liquidity_score": val.liquidity_score
                }
                for val in analysis.asset_valuations
            ],
            "liquidation_scenarios": len(analysis.liquidation_scenarios)
        }

        return jsonify(create_success_response(
            response_data,
            "Collateral analysis completed successfully"
        ))

    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        return create_error_response(f"Collateral analysis failed: {e}", 500)

@app.route('/api/v1/interest-rates/calculate', methods=['POST'])
def calculate_interest_rate():
    """Calculate interest rate for a loan."""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("JSON body required")

        loan_request = parse_loan_request(data)
        rate_calculation = lending_service["interest_rates"].calculate_interest_rate(loan_request)

        response_data = {
            "base_rate": rate_calculation.base_rate,
            "final_rate": rate_calculation.final_rate,
            "risk_premium": rate_calculation.risk_premium,
            "rate_factors": {
                "borrower_reputation": rate_calculation.rate_factors.borrower_reputation,
                "collateral_quality": rate_calculation.rate_factors.collateral_quality,
                "market_conditions": rate_calculation.rate_factors.market_conditions,
                "network_health": rate_calculation.rate_factors.network_health.value
            }
        }

        return jsonify(create_success_response(
            response_data,
            "Interest rate calculated successfully"
        ))

    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        return create_error_response(f"Interest rate calculation failed: {e}", 500)

@app.route('/api/v1/loans/evaluate', methods=['POST'])
def evaluate_loan():
    """Evaluate loan application for approval."""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("JSON body required")

        loan_request = parse_loan_request(data)
        decision = lending_service["loan_approval"].evaluate_loan(loan_request)

        response_data = {
            "decision": decision.decision.value,
            "confidence": decision.confidence.value,
            "approved_amount": decision.approved_amount,
            "reasoning": decision.reasoning,
            "terms": {
                "interest_rate": decision.terms.interest_rate,
                "duration_days": decision.terms.duration_days,
                "collateral_requirements": decision.terms.collateral_requirements
            } if decision.terms else None
        }

        return jsonify(create_success_response(
            response_data,
            "Loan evaluation completed successfully"
        ))

    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        return create_error_response(f"Loan evaluation failed: {e}", 500)

@app.route('/api/v1/risk/assess', methods=['POST'])
def assess_risk():
    """Assess risk for a loan request."""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("JSON body required")

        loan_request = parse_loan_request(data)
        risk_assessment = lending_service["risk_assessment"].assess_risk(loan_request)

        response_data = {
            "overall_score": risk_assessment.overall_score,
            "risk_level": risk_assessment.risk_level.value,
            "borrower_risk": risk_assessment.borrower_risk,
            "collateral_risk": risk_assessment.collateral_risk,
            "market_risk": risk_assessment.market_risk,
            "risk_profile": {
                "borrower_profile": risk_assessment.risk_profile.borrower_profile.value,
                "collateral_profile": risk_assessment.risk_profile.collateral_profile.value,
                "market_profile": risk_assessment.risk_profile.market_profile.value
            },
            "risk_factors": risk_assessment.risk_factors
        }

        return jsonify(create_success_response(
            response_data,
            "Risk assessment completed successfully"
        ))

    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        return create_error_response(f"Risk assessment failed: {e}", 500)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return create_error_response("Endpoint not found", 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return create_error_response("Method not allowed", 405)

@app.errorhandler(500)
def internal_error(error):
    return create_error_response("Internal server error", 500)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def print_api_documentation():
    """Print API documentation."""
    print("\n📚 API Documentation")
    print("=" * 50)
    print("Health Check:")
    print("  GET /health")
    print()
    print("Service Info:")
    print("  GET /api/v1/info")
    print()
    print("Loan Analysis:")
    print("  POST /api/v1/loans/analyze")
    print("  Body: {")
    print("    'borrower': 'ALGORAND_ADDRESS',")
    print("    'requested_amount': 1000000,")
    print("    'collateral_assets': [")
    print("      {'asset_id': 0, 'amount': 2000000}")
    print("    ],")
    print("    'loan_duration_days': 30")
    print("  }")
    print()
    print("Individual Engine Endpoints:")
    print("  POST /api/v1/collateral/analyze")
    print("  POST /api/v1/interest-rates/calculate")
    print("  POST /api/v1/loans/evaluate")
    print("  POST /api/v1/risk/assess")
    print()

def create_sample_request():
    """Create a sample request for testing."""
    return {
        "borrower": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "requested_amount": 1000000,
        "collateral_assets": [
            {"asset_id": 0, "amount": 2000000}
        ],
        "loan_duration_days": 30
    }

def main():
    """Main application entry point."""
    print("🏦 Algorand Lending Business Logic Microservice")
    print("=" * 60)
    print(f"✓ Package: {VENDOR_INFO['name']} v{VENDOR_INFO['version']}")
    print(f"✓ Engines: {', '.join([k for k in lending_service.keys() if k != 'config'])}")
    print(f"✓ Configuration: {DEFAULT_CONFIG.network.network_name}")

    print_api_documentation()

    print("🚀 Starting Flask development server...")
    print("   Access the API at: http://localhost:5000")
    print("   Health check: http://localhost:5000/health")
    print("   Service info: http://localhost:5000/api/v1/info")

    # Start the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()