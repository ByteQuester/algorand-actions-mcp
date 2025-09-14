# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Tools for the ADK Liquidity Agent
Implements liquidity discovery and matching logic
"""

import json
import random
from typing import Dict, Any, List, Optional


def find_available_lenders(
    loan_amount_algos: float,
    target_interest_rate: float,
    duration_days: int,
    borrower_risk_category: str = "MEDIUM"
) -> Dict[str, Any]:
    """
    Find available lenders who can provide the requested liquidity

    Args:
        loan_amount_algos: Amount of ALGO needed
        target_interest_rate: Target interest rate
        duration_days: Loan duration in days
        borrower_risk_category: Risk category of borrower

    Returns:
        Dict with available lenders and their terms
    """

    # Simulate lender discovery based on market conditions
    # In production, this would query actual lender pools/platforms

    available_lenders = []

    # Generate realistic lender profiles based on market segments
    lender_profiles = [
        {
            "id": "INSTITUTIONAL_POOL_1",
            "name": "Algorand DeFi Fund",
            "type": "institutional",
            "max_capacity_algos": 50000,
            "min_loan_algos": 100,
            "preferred_duration_days": [30, 60, 90],
            "risk_tolerance": ["LOW", "MEDIUM"],
            "rate_premium": -0.5,  # Discount for institutional rates
            "reputation_score": 95,
            "active_loans": 42
        },
        {
            "id": "PRIVATE_LENDER_1",
            "name": "AlgoCapital Partners",
            "type": "private",
            "max_capacity_algos": 20000,
            "min_loan_algos": 50,
            "preferred_duration_days": [14, 30, 45],
            "risk_tolerance": ["LOW", "MEDIUM", "HIGH"],
            "rate_premium": 0.0,  # Market rates
            "reputation_score": 88,
            "active_loans": 18
        },
        {
            "id": "COMMUNITY_POOL_1",
            "name": "Algorand Community Lending",
            "type": "community",
            "max_capacity_algos": 10000,
            "min_loan_algos": 10,
            "preferred_duration_days": [7, 14, 30],
            "risk_tolerance": ["MEDIUM", "HIGH"],
            "rate_premium": 0.5,  # Slight premium for community
            "reputation_score": 82,
            "active_loans": 156
        },
        {
            "id": "YIELD_OPTIMIZER_1",
            "name": "AlgoYield Protocol",
            "type": "protocol",
            "max_capacity_algos": 30000,
            "min_loan_algos": 25,
            "preferred_duration_days": [30, 60, 90, 180],
            "risk_tolerance": ["LOW", "MEDIUM"],
            "rate_premium": -0.25,  # Competitive rates
            "reputation_score": 91,
            "active_loans": 73
        }
    ]

    for lender in lender_profiles:
        # Check if lender can accommodate the request
        can_lend = (
            loan_amount_algos >= lender["min_loan_algos"] and
            loan_amount_algos <= lender["max_capacity_algos"] and
            borrower_risk_category in lender["risk_tolerance"] and
            any(abs(duration_days - pref) <= 15 for pref in lender["preferred_duration_days"])
        )

        if can_lend:
            # Calculate offered rate
            base_rate = target_interest_rate
            offered_rate = base_rate + lender["rate_premium"]

            # Add some market variance
            market_adjustment = random.uniform(-0.3, 0.3)
            offered_rate += market_adjustment

            # Ensure reasonable bounds
            offered_rate = max(2.0, min(20.0, offered_rate))

            available_lenders.append({
                "lender_id": lender["id"],
                "name": lender["name"],
                "type": lender["type"],
                "available_capacity_algos": min(lender["max_capacity_algos"], loan_amount_algos * 2),
                "offered_interest_rate": round(offered_rate, 2),
                "max_duration_days": max(lender["preferred_duration_days"]),
                "reputation_score": lender["reputation_score"],
                "active_loans": lender["active_loans"],
                "estimated_approval_time": "2-4 hours" if lender["type"] == "institutional"
                                          else "1-2 hours" if lender["type"] == "protocol"
                                          else "4-8 hours",
                "special_terms": {
                    "early_repayment": True,
                    "rate_negotiable": lender["type"] in ["private", "community"],
                    "collateral_flexibility": lender["type"] == "community"
                }
            })

    # Sort by best terms (lowest rate, highest reputation)
    available_lenders.sort(key=lambda x: (x["offered_interest_rate"], -x["reputation_score"]))

    return {
        "total_lenders_found": len(available_lenders),
        "available_lenders": available_lenders,
        "total_available_capacity": sum(l["available_capacity_algos"] for l in available_lenders),
        "rate_range": {
            "lowest": min((l["offered_interest_rate"] for l in available_lenders), default=0),
            "highest": max((l["offered_interest_rate"] for l in available_lenders), default=0),
            "average": sum(l["offered_interest_rate"] for l in available_lenders) / len(available_lenders) if available_lenders else 0
        },
        "market_depth": "DEEP" if len(available_lenders) >= 3 else "MODERATE" if len(available_lenders) >= 2 else "SHALLOW"
    }


def assess_borrower_creditworthiness(
    borrower_address: str,
    current_balance_algos: float,
    transaction_history: Dict[str, Any],
    previous_loans: Dict[str, Any] = None,
    loan_amount_algos: float = 0
) -> Dict[str, Any]:
    """
    Assess borrower's creditworthiness for lending decisions

    Args:
        borrower_address: Borrower's Algorand address
        current_balance_algos: Current ALGO balance
        transaction_history: Historical transaction data
        previous_loans: Previous lending history if available
        loan_amount_algos: Requested loan amount

    Returns:
        Dict with creditworthiness assessment
    """

    credit_score = 60  # Start with neutral score
    credit_factors = []

    # Balance assessment
    if loan_amount_algos > 0:
        balance_ratio = current_balance_algos / loan_amount_algos

        if balance_ratio >= 3.0:
            credit_score += 20
            credit_factors.append("Excellent balance cushion (3x+ loan amount)")
        elif balance_ratio >= 2.0:
            credit_score += 15
            credit_factors.append("Strong balance cushion (2x+ loan amount)")
        elif balance_ratio >= 1.0:
            credit_score += 10
            credit_factors.append("Adequate balance cushion")
        elif balance_ratio >= 0.5:
            credit_score += 0
            credit_factors.append("Minimal balance relative to loan")
        else:
            credit_score -= 15
            credit_factors.append("Insufficient balance raises risk concerns")

    # Transaction history analysis
    tx_count = transaction_history.get("total_transactions", 0)
    avg_tx_amount = transaction_history.get("average_amount", 0)
    tx_frequency = transaction_history.get("monthly_frequency", 0)

    # Transaction volume assessment
    if tx_count >= 100:
        credit_score += 15
        credit_factors.append("Extensive transaction history shows active usage")
    elif tx_count >= 50:
        credit_score += 10
        credit_factors.append("Good transaction history")
    elif tx_count >= 20:
        credit_score += 5
        credit_factors.append("Moderate transaction activity")
    else:
        credit_score -= 5
        credit_factors.append("Limited transaction history")

    # Transaction patterns
    if avg_tx_amount > 10.0 and tx_frequency > 5:
        credit_score += 10
        credit_factors.append("Consistent high-value transaction pattern")
    elif avg_tx_amount > 1.0:
        credit_score += 5
        credit_factors.append("Regular transaction activity")

    # Previous loan history (if available)
    if previous_loans:
        total_loans = previous_loans.get("total_loans", 0)
        successful_repayments = previous_loans.get("successful_repayments", 0)
        defaults = previous_loans.get("defaults", 0)

        if total_loans > 0:
            repayment_rate = successful_repayments / total_loans

            if repayment_rate >= 0.95 and defaults == 0:
                credit_score += 25
                credit_factors.append("Excellent repayment history (95%+ success rate)")
            elif repayment_rate >= 0.90:
                credit_score += 15
                credit_factors.append("Strong repayment history")
            elif repayment_rate >= 0.75:
                credit_score += 5
                credit_factors.append("Acceptable repayment history")
            else:
                credit_score -= 20
                credit_factors.append("Poor repayment history raises significant concerns")
    else:
        credit_factors.append("No previous lending history available")

    # Account age estimation (based on transaction spread)
    tx_span_days = transaction_history.get("activity_span_days", 0)
    if tx_span_days >= 365:
        credit_score += 8
        credit_factors.append("Long-term account activity (1+ years)")
    elif tx_span_days >= 90:
        credit_score += 5
        credit_factors.append("Established account activity")
    elif tx_span_days >= 30:
        credit_score += 2
        credit_factors.append("Recent account activity")

    # Ensure score bounds
    credit_score = max(0, min(100, credit_score))

    # Determine credit tier
    if credit_score >= 80:
        credit_tier = "PRIME"
        risk_category = "LOW"
    elif credit_score >= 65:
        credit_tier = "NEAR_PRIME"
        risk_category = "MEDIUM"
    elif credit_score >= 50:
        credit_tier = "SUBPRIME"
        risk_category = "HIGH"
    else:
        credit_tier = "HIGH_RISK"
        risk_category = "VERY_HIGH"

    return {
        "credit_score": credit_score,
        "credit_tier": credit_tier,
        "risk_category": risk_category,
        "credit_factors": credit_factors,
        "borrower_profile": {
            "balance_strength": "STRONG" if current_balance_algos >= loan_amount_algos * 2 else
                               "ADEQUATE" if current_balance_algos >= loan_amount_algos else "WEAK",
            "transaction_activity": "HIGH" if tx_count >= 50 else "MEDIUM" if tx_count >= 20 else "LOW",
            "account_maturity": "MATURE" if tx_span_days >= 365 else "DEVELOPING" if tx_span_days >= 90 else "NEW"
        },
        "lending_recommendations": {
            "max_loan_ratio": 0.7 if credit_score >= 80 else 0.5 if credit_score >= 65 else 0.3,
            "rate_adjustment": -0.5 if credit_score >= 80 else 0 if credit_score >= 65 else 1.5,
            "collateral_requirement": 1.2 if credit_score >= 80 else 1.3 if credit_score >= 65 else 1.5
        }
    }


def match_liquidity_requirements(
    loan_request: Dict[str, Any],
    available_lenders: List[Dict[str, Any]],
    borrower_assessment: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Match borrower requirements with available lenders optimally

    Args:
        loan_request: Borrower's loan requirements
        available_lenders: List of available lenders
        borrower_assessment: Borrower creditworthiness assessment

    Returns:
        Dict with optimal matches and recommendations
    """

    requested_amount = loan_request.get("amount_algos", 0)
    max_rate = loan_request.get("max_interest_rate", 15.0)
    duration_days = loan_request.get("duration_days", 30)
    borrower_risk = borrower_assessment.get("risk_category", "MEDIUM")

    matched_lenders = []

    for lender in available_lenders:
        # Check if lender can meet requirements
        rate_acceptable = lender["offered_interest_rate"] <= max_rate
        capacity_sufficient = lender["available_capacity_algos"] >= requested_amount
        duration_compatible = lender["max_duration_days"] >= duration_days

        if rate_acceptable and capacity_sufficient and duration_compatible:
            # Calculate match score
            match_score = 0

            # Rate competitiveness (30% weight)
            rate_score = max(0, 30 - (lender["offered_interest_rate"] - 3.0) * 5)
            match_score += rate_score * 0.3

            # Reputation (25% weight)
            reputation_score = lender["reputation_score"]
            match_score += reputation_score * 0.25

            # Capacity buffer (20% weight)
            capacity_ratio = lender["available_capacity_algos"] / requested_amount
            capacity_score = min(100, 50 + capacity_ratio * 15)
            match_score += capacity_score * 0.2

            # Approval speed (15% weight)
            speed_score = {
                "1-2 hours": 100,
                "2-4 hours": 80,
                "4-8 hours": 60
            }.get(lender.get("estimated_approval_time", "4-8 hours"), 40)
            match_score += speed_score * 0.15

            # Special terms compatibility (10% weight)
            special_score = 70  # Base score
            if lender.get("special_terms", {}).get("rate_negotiable", False):
                special_score += 15
            if lender.get("special_terms", {}).get("early_repayment", False):
                special_score += 10
            if lender.get("special_terms", {}).get("collateral_flexibility", False):
                special_score += 5

            match_score += special_score * 0.1

            matched_lenders.append({
                **lender,
                "match_score": round(match_score, 1),
                "match_reasons": [
                    f"Rate within budget ({lender['offered_interest_rate']}% ≤ {max_rate}%)",
                    f"Sufficient capacity ({lender['available_capacity_algos']:,.0f} ALGO available)",
                    f"Duration compatible ({lender['max_duration_days']} days ≥ {duration_days} days)",
                    f"High reputation ({lender['reputation_score']}/100)"
                ]
            })

    # Sort by match score (highest first)
    matched_lenders.sort(key=lambda x: x["match_score"], reverse=True)

    # Determine best match
    best_match = matched_lenders[0] if matched_lenders else None

    # Calculate overall matching success
    matching_quality = "EXCELLENT" if best_match and best_match["match_score"] >= 80 else \
                      "GOOD" if best_match and best_match["match_score"] >= 65 else \
                      "FAIR" if best_match and best_match["match_score"] >= 50 else \
                      "POOR"

    return {
        "matching_success": len(matched_lenders) > 0,
        "total_matches": len(matched_lenders),
        "matching_quality": matching_quality,
        "best_match": best_match,
        "all_matches": matched_lenders[:5],  # Top 5 matches
        "recommendations": {
            "primary_choice": best_match["name"] if best_match else None,
            "backup_options": len(matched_lenders) - 1 if len(matched_lenders) > 1 else 0,
            "rate_savings": max_rate - best_match["offered_interest_rate"] if best_match else 0,
            "estimated_total_cost": requested_amount * (1 + best_match["offered_interest_rate"]/100 * duration_days/365) if best_match else 0
        }
    }


def calculate_liquidity_costs(
    loan_amount_algos: float,
    interest_rate_percent: float,
    duration_days: int,
    platform_fee_percent: float = 0.5,
    origination_fee_algos: float = 0.1
) -> Dict[str, Any]:
    """
    Calculate comprehensive costs for accessing liquidity

    Args:
        loan_amount_algos: Loan amount in ALGO
        interest_rate_percent: Annual interest rate
        duration_days: Loan duration in days
        platform_fee_percent: Platform fee as percentage of loan
        origination_fee_algos: Fixed origination fee in ALGO

    Returns:
        Dict with detailed cost breakdown
    """

    # Calculate interest cost
    daily_rate = interest_rate_percent / 100 / 365
    interest_cost = loan_amount_algos * daily_rate * duration_days

    # Calculate platform fees
    platform_fee = loan_amount_algos * platform_fee_percent / 100

    # Calculate total costs
    total_fees = platform_fee + origination_fee_algos
    total_cost = interest_cost + total_fees
    total_repayment = loan_amount_algos + total_cost

    # Calculate effective rates
    effective_annual_rate = (total_cost / loan_amount_algos) * (365 / duration_days) * 100

    # Calculate cost per day
    daily_cost = total_cost / duration_days

    return {
        "cost_breakdown": {
            "principal_amount": round(loan_amount_algos, 6),
            "interest_cost": round(interest_cost, 6),
            "platform_fee": round(platform_fee, 6),
            "origination_fee": round(origination_fee_algos, 6),
            "total_fees": round(total_fees, 6),
            "total_interest_and_fees": round(total_cost, 6),
            "total_repayment": round(total_repayment, 6)
        },
        "rate_analysis": {
            "nominal_annual_rate": interest_rate_percent,
            "effective_annual_rate": round(effective_annual_rate, 2),
            "daily_cost_rate": round(daily_cost / loan_amount_algos * 100, 4),
            "total_cost_percentage": round(total_cost / loan_amount_algos * 100, 2)
        },
        "payment_schedule": {
            "loan_duration_days": duration_days,
            "daily_cost": round(daily_cost, 6),
            "final_payment": round(total_repayment, 6),
            "cost_per_algo_borrowed": round(total_cost / loan_amount_algos, 6)
        },
        "comparison_metrics": {
            "cost_vs_market": "Competitive" if effective_annual_rate <= 10 else "Above Market" if effective_annual_rate <= 15 else "Expensive",
            "fee_ratio": round(total_fees / total_cost * 100, 1),
            "interest_ratio": round(interest_cost / total_cost * 100, 1)
        }
    }