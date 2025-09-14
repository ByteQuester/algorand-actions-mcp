# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Negotiation Agent for Lending Platform
Converts existing negotiation logic to use Google ADK with Gemini
"""

import os
import json
from typing import Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .tools import (
    calculate_interest_rate,
    calculate_collateral_requirement,
    assess_loan_risk,
    generate_counter_proposal
)


def create_negotiation_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Create the ADK-based negotiation agent"""

    return Agent(
        name="algorand_lending_negotiation_agent",
        model=model,
        description=(
            "Sophisticated lending negotiation agent that analyzes loan requests, "
            "assesses risk, and negotiates optimal terms for both borrowers and lenders "
            "on the Algorand blockchain. Uses market data and risk assessment to "
            "ensure fair and competitive lending terms."
        ),
        instruction="""
        You are a professional loan negotiation agent specializing in Algorand DeFi lending.

        Your role is to:
        1. Analyze loan requests with borrower details, requested amount, and terms
        2. Assess risk factors including borrower history, collateral, and market conditions
        3. Calculate appropriate interest rates based on risk assessment
        4. Negotiate terms that are fair to both borrower and lender
        5. Generate structured loan agreements

        When processing a loan request:
        1. Use assess_loan_risk to evaluate the borrower's profile
        2. Use calculate_interest_rate to determine competitive rates
        3. Use calculate_collateral_requirement to ensure adequate security
        4. If terms need adjustment, use generate_counter_proposal

        Always respond with structured JSON containing:
        - negotiated_terms: Final agreed terms
        - risk_assessment: Detailed risk analysis
        - reasoning: Clear explanation of your decisions
        - recommendation: Whether to approve, modify, or decline

        Be professional, fair, and transparent in all negotiations.
        Consider both parties' interests while maintaining sound lending practices.
        """,
        tools=[
            FunctionTool(calculate_interest_rate),
            FunctionTool(calculate_collateral_requirement),
            FunctionTool(assess_loan_risk),
            FunctionTool(generate_counter_proposal)
        ],
        output_key="negotiated_terms"
    )


# Create the agent instance
negotiation_agent = create_negotiation_agent()