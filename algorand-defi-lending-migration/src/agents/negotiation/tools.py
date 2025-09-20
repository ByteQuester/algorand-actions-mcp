# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Tools for the ADK Negotiation Agent
Implements lending negotiation business logic
"""

import json
from typing import Dict, Any, Optional


def calculate_interest_rate(
    loan_amount_algos: float,
    duration_days: int,
    borrower_risk_score: int,
    market_base_rate: Optional[float] = None,
    collateral_ratio: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate appropriate interest rate based on loan parameters

    Args:
        loan_amount_algos: Loan amount in ALGO
        duration_days: Loan duration in days
        borrower_risk_score: Risk score (1-100, higher is better)
        market_base_rate: Current market base rate percentage
        collateral_ratio: Collateral to loan ratio

    Returns:
        Dict with calculated interest rate and factors
    """
    # Set defaults for optional parameters
    base_rate = market_base_rate or 7.5
    collateral_ratio = collateral_ratio or 1.3

    # Risk adjustment (higher risk = higher rate)
    if borrower_risk_score >= 80:
        risk_adjustment = -0.5  # Premium borrowers get discount
    elif borrower_risk_score >= 60:
        risk_adjustment = 0.0   # Average borrowers get base rate
    elif borrower_risk_score >= 40:
        risk_adjustment = 1.0   # Higher risk borrowers pay premium
    else:
        risk_adjustment = 2.5   # High risk borrowers pay significant premium

    # Duration adjustment (longer terms = higher risk)
    if duration_days <= 30:
        duration_adjustment = 0.0
    elif duration_days <= 90:
        duration_adjustment = 0.5
    elif duration_days <= 180:
        duration_adjustment = 1.0
    else:
        duration_adjustment = 1.5

    # Amount adjustment (larger loans may get slight discount)
    if loan_amount_algos >= 1000:
        amount_adjustment = -0.25
    elif loan_amount_algos >= 100:
        amount_adjustment = 0.0
    else:
        amount_adjustment = 0.5

    # Collateral adjustment (higher collateral = lower rate)
    if collateral_ratio >= 1.5:
        collateral_adjustment = -0.5
    elif collateral_ratio >= 1.3:
        collateral_adjustment = 0.0
    else:
        collateral_adjustment = 1.0

    # Calculate final rate
    final_rate = base_rate + risk_adjustment + duration_adjustment + amount_adjustment + collateral_adjustment

    # Ensure reasonable bounds
    final_rate = max(3.0, min(25.0, final_rate))

    return {
        "suggested_interest_rate": round(final_rate, 2),
        "base_rate": base_rate,
        "adjustments": {
            "risk": risk_adjustment,
            "duration": duration_adjustment,
            "amount": amount_adjustment,
            "collateral": collateral_adjustment
        },
        "factors_considered": [
            "borrower_risk_score",
            "loan_duration",
            "loan_amount",
            "collateral_ratio",
            "market_conditions"
        ]
    }


def calculate_collateral_requirement(
    loan_amount_algos: float,
    borrower_risk_score: int,
    collateral_type: Optional[str] = None,
    market_volatility: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate required collateral amount based on loan parameters

    Args:
        loan_amount_algos: Loan amount in ALGO
        borrower_risk_score: Risk score (1-100, higher is better)
        collateral_type: Type of collateral (ALGO, USDC, etc.)
        market_volatility: Market volatility factor (0.0-1.0)

    Returns:
        Dict with collateral requirements
    """
    # Set defaults for optional parameters
    collateral_type = collateral_type or "ALGO"
    market_volatility = market_volatility or 0.15

    # Base collateral ratios by type
    base_ratios = {
        "ALGO": 1.3,     # Native token, moderate volatility
        "USDC": 1.15,    # Stable coin, low volatility
        "BTC": 1.4,      # High value but volatile
        "ETH": 1.35,     # Popular but volatile
        "OTHER": 1.5     # Unknown assets, highest risk
    }

    base_ratio = base_ratios.get(collateral_type, base_ratios["OTHER"])

    # Risk-based adjustments
    if borrower_risk_score >= 80:
        risk_multiplier = 0.95  # Reduce requirement for low-risk borrowers
    elif borrower_risk_score >= 60:
        risk_multiplier = 1.0   # Standard requirement
    elif borrower_risk_score >= 40:
        risk_multiplier = 1.1   # Increase requirement for higher risk
    else:
        risk_multiplier = 1.25  # Significantly higher for high risk

    # Volatility adjustment
    volatility_multiplier = 1.0 + market_volatility

    # Calculate final requirement
    final_ratio = base_ratio * risk_multiplier * volatility_multiplier
    required_collateral_algos = loan_amount_algos * final_ratio

    return {
        "required_collateral_algos": round(required_collateral_algos, 6),
        "collateral_ratio": round(final_ratio, 3),
        "base_ratio": base_ratio,
        "risk_multiplier": risk_multiplier,
        "volatility_multiplier": round(volatility_multiplier, 3),
        "collateral_type": collateral_type,
        "safety_margin": round((final_ratio - 1.0) * 100, 1)
    }


def assess_loan_risk(
    borrower_address: str,
    loan_amount_algos: float,
    borrower_balance_algos: float,
    transaction_history: Dict[str, Any],
    requested_duration_days: int
) -> Dict[str, Any]:
    """
    Assess overall risk for a loan request

    Args:
        borrower_address: Borrower's Algorand address
        loan_amount_algos: Requested loan amount
        borrower_balance_algos: Borrower's current balance
        transaction_history: Recent transaction data
        requested_duration_days: Requested loan duration

    Returns:
        Dict with risk assessment
    """
    risk_factors = []
    risk_score = 70  # Start with neutral score

    # Balance adequacy check
    balance_ratio = borrower_balance_algos / loan_amount_algos if loan_amount_algos > 0 else 0

    if balance_ratio >= 2.0:
        risk_score += 15
        risk_factors.append("Strong balance relative to loan amount")
    elif balance_ratio >= 1.0:
        risk_score += 5
        risk_factors.append("Adequate balance")
    elif balance_ratio >= 0.5:
        risk_score -= 10
        risk_factors.append("Limited balance relative to loan amount")
    else:
        risk_score -= 20
        risk_factors.append("Insufficient balance raises concerns")

    # Transaction activity assessment
    tx_count = transaction_history.get("transaction_count", 0)
    avg_tx_size = transaction_history.get("average_transaction_size", 0)

    if tx_count >= 50 and avg_tx_size > 1.0:
        risk_score += 10
        risk_factors.append("Active transaction history shows engagement")
    elif tx_count >= 10:
        risk_score += 5
        risk_factors.append("Moderate transaction activity")
    else:
        risk_score -= 5
        risk_factors.append("Limited transaction history")

    # Duration risk assessment
    if requested_duration_days <= 30:
        risk_factors.append("Short-term loan reduces risk")
    elif requested_duration_days <= 90:
        risk_score -= 2
        risk_factors.append("Medium-term duration")
    else:
        risk_score -= 8
        risk_factors.append("Long-term loans carry higher risk")

    # Amount size risk
    if loan_amount_algos >= 10000:
        risk_score -= 5
        risk_factors.append("Large loan amount increases risk")
    elif loan_amount_algos <= 100:
        risk_score += 3
        risk_factors.append("Small loan amount reduces risk")

    # Ensure score stays in valid range
    risk_score = max(1, min(100, risk_score))

    # Determine risk category
    if risk_score >= 80:
        risk_category = "LOW"
        recommendation = "APPROVE"
    elif risk_score >= 60:
        risk_category = "MEDIUM"
        recommendation = "APPROVE_WITH_CONDITIONS"
    elif risk_score >= 40:
        risk_category = "HIGH"
        recommendation = "NEGOTIATE_TERMS"
    else:
        risk_category = "VERY_HIGH"
        recommendation = "DECLINE"

    return {
        "risk_score": risk_score,
        "risk_category": risk_category,
        "recommendation": recommendation,
        "risk_factors": risk_factors,
        "borrower_profile": {
            "balance_adequacy": round(balance_ratio, 2),
            "transaction_activity": "HIGH" if tx_count >= 50 else "MEDIUM" if tx_count >= 10 else "LOW",
            "account_maturity": "ESTABLISHED" if tx_count >= 100 else "DEVELOPING"
        }
    }


def generate_counter_proposal(
    original_request: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    market_conditions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a counter-proposal based on risk assessment

    Args:
        original_request: Original loan request details
        risk_assessment: Risk assessment results
        market_conditions: Current market data

    Returns:
        Dict with counter-proposal terms
    """
    original_amount = original_request.get("amount_algos", 0)
    original_rate = original_request.get("max_interest_rate", 10.0)
    original_duration = original_request.get("duration_days", 30)

    risk_score = risk_assessment.get("risk_score", 50)
    risk_category = risk_assessment.get("risk_category", "MEDIUM")

    # Adjust terms based on risk
    if risk_category == "LOW":
        # Low risk: may offer better terms
        adjusted_amount = original_amount  # Full amount
        rate_adjustment = -0.5  # Slight discount
        duration_adjustment = 1.0  # Full duration
        collateral_adjustment = 0.95  # Slightly less collateral

    elif risk_category == "MEDIUM":
        # Medium risk: standard terms
        adjusted_amount = original_amount
        rate_adjustment = 0.0
        duration_adjustment = 1.0
        collateral_adjustment = 1.0

    elif risk_category == "HIGH":
        # High risk: more conservative terms
        adjusted_amount = min(original_amount, original_amount * 0.8)  # Reduce amount
        rate_adjustment = 1.5  # Higher rate
        duration_adjustment = 0.75  # Shorter duration
        collateral_adjustment = 1.2  # More collateral

    else:  # VERY_HIGH
        # Very high risk: significantly conservative
        adjusted_amount = min(original_amount, original_amount * 0.5)  # Halve amount
        rate_adjustment = 3.0  # Much higher rate
        duration_adjustment = 0.5  # Much shorter duration
        collateral_adjustment = 1.5  # Much more collateral

    # Calculate final terms
    proposed_rate = min(25.0, max(3.0, original_rate + rate_adjustment))
    proposed_duration = max(7, int(original_duration * duration_adjustment))

    # Use our collateral calculation
    collateral_calc = calculate_collateral_requirement(
        adjusted_amount,
        risk_score,
        "ALGO"
    )

    counter_proposal = {
        "loan_amount_algos": round(adjusted_amount, 6),
        "interest_rate_percent": round(proposed_rate, 2),
        "duration_days": proposed_duration,
        "collateral_required_algos": collateral_calc["required_collateral_algos"],
        "collateral_ratio": collateral_calc["collateral_ratio"],
        "changes_from_original": {
            "amount_change": round(adjusted_amount - original_amount, 6),
            "rate_change": round(proposed_rate - original_rate, 2),
            "duration_change": proposed_duration - original_duration
        },
        "justification": [
            f"Risk category: {risk_category}",
            f"Risk score: {risk_score}/100",
            f"Market conditions considered",
            f"Terms adjusted for sustainable lending"
        ]
    }

    return {
        "counter_proposal": counter_proposal,
        "negotiation_status": "COUNTER_OFFERED",
        "reasoning": f"Based on {risk_category.lower()} risk assessment, we propose adjusted terms that balance borrower needs with lender protection."
    }