#!/usr/bin/env python3
"""
Example usage of Algorand Lending Business Logic.
Demonstrates basic integration and usage patterns.
"""

import json
from algorand_lending_bl import AlgorandLendingService

def main():
    """Demonstrate basic lending service usage."""

    # Initialize the service
    print("Initializing Algorand Lending Service...")
    service = AlgorandLendingService()

    # Show service info
    info = service.get_service_info()
    print(f"Service: {info['service_name']} v{info['version']}")
    print(f"Capabilities: {', '.join(info['capabilities'])}")
    print()

    # Example 1: Simple loan evaluation
    print("=== Example 1: Basic Loan Evaluation ===")
    loan_request = {
        "borrower_address": "ALGORAND_ADDRESS_EXAMPLE_12345678901234567890123456789012345678",
        "loan_amount": 50000,  # $50,000 USD
        "collateral_assets": [
            {"asset_id": "0", "amount": 100000},      # 100k ALGO
            {"asset_id": "31566704", "amount": 25000} # 25k USDC
        ]
    }

    result = service.evaluate_loan(
        borrower_address=loan_request["borrower_address"],
        loan_amount=loan_request["loan_amount"],
        collateral_assets=loan_request["collateral_assets"]
    )

    print(f"Loan Decision: {'APPROVED' if result['decision'] else 'REJECTED'}")
    if result['decision']:
        print(f"Approved Amount: ${result['approved_amount']:,.2f}")
        print(f"Interest Rate: {result['interest_rate']:.2%}")
        if result.get('conditions'):
            print(f"Conditions: {', '.join(result['conditions'])}")
    else:
        print(f"Rejection Reason: {result.get('error', 'Unknown')}")
    print()

    # Example 2: Collateral analysis
    print("=== Example 2: Collateral Analysis ===")
    collateral_assets = [
        {"asset_id": "0", "amount": 75000},       # 75k ALGO
        {"asset_id": "31566704", "amount": 50000} # 50k USDC
    ]

    collateral_analysis = service.analyze_collateral(collateral_assets)
    print(f"Total Collateral Value: ${collateral_analysis['total_value_usd']:,.2f}")
    print(f"Loan-to-Value Ratio: {collateral_analysis['loan_to_value']:.1%}")
    print(f"Risk Level: {collateral_analysis['risk_level'].upper()}")
    print(f"Assets analyzed: {len(collateral_analysis['assets'])}")
    print()

    # Example 3: Interest rate calculation
    print("=== Example 3: Interest Rate Calculation ===")
    borrower = "ALGORAND_ADDRESS_EXAMPLE_12345678901234567890123456789012345678"
    loan_terms = {
        "loan_amount": 100000,
        "term_days": 365
    }

    interest_rate = service.calculate_interest_rate(borrower, loan_terms)
    print(f"Calculated Interest Rate: {interest_rate:.2%}")
    print(f"For loan: ${loan_terms['loan_amount']:,} over {loan_terms['term_days']} days")
    print()

    # Example 4: Risk assessment
    print("=== Example 4: Risk Assessment ===")
    risk_assessment = service.assess_risk(borrower)
    print(f"Overall Risk: {risk_assessment['overall_risk'].upper()}")
    print(f"Risk Score: {risk_assessment['risk_score']:.2f}")
    print(f"Key Risk Factors:")
    for factor in risk_assessment['risk_factors'][:3]:  # Show first 3
        print(f"  - {factor}")
    print()

    # Example 5: Full loan process simulation
    print("=== Example 5: Complete Loan Process ===")
    complete_request = {
        "borrower_address": "ALGORAND_ADDRESS_COMPLETE_EXAMPLE_123456789012345678901234567890",
        "loan_amount": 25000,
        "collateral_assets": [
            {"asset_id": "0", "amount": 50000},       # 50k ALGO
            {"asset_id": "386192725", "amount": 10000} # 10k USDT
        ]
    }

    print("Processing complete loan application...")
    final_result = service.evaluate_loan(**complete_request)

    print("\n--- FINAL LOAN DECISION ---")
    print(json.dumps({
        "approved": final_result['decision'],
        "amount": final_result.get('approved_amount'),
        "rate": f"{final_result['interest_rate']:.2%}" if 'interest_rate' in final_result else None,
        "collateral_value": f"${final_result['collateral_analysis']['total_value_usd']:,.2f}",
        "risk_level": final_result['risk_assessment']['overall_risk']
    }, indent=2))

if __name__ == "__main__":
    main()