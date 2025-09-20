# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Liquidity Agent for Lending Platform
Discovers and matches liquidity sources with borrowing needs
"""

import os
from typing import Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .tools import (
    find_available_lenders,
    assess_borrower_creditworthiness,
    match_liquidity_requirements,
    calculate_liquidity_costs
)


def create_liquidity_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Create the ADK-based liquidity agent"""

    return Agent(
        name="algorand_lending_liquidity_agent",
        model=model,
        description=(
            "Advanced liquidity discovery and matching agent that finds suitable "
            "lenders for borrowing requests, assesses borrower creditworthiness, "
            "and optimizes liquidity matching for the Algorand DeFi ecosystem. "
            "Ensures efficient capital allocation and risk management."
        ),
        instruction="""
        You are a sophisticated liquidity agent specializing in Algorand DeFi lending markets.

        Your core responsibilities:
        1. Discover available liquidity sources and lenders in the ecosystem
        2. Assess borrower creditworthiness and financial capacity
        3. Match liquidity requirements with available capital efficiently
        4. Calculate competitive liquidity costs and pricing
        5. Optimize capital allocation for maximum efficiency

        When processing liquidity requests:
        1. Use assess_borrower_creditworthiness to evaluate the borrower's profile
        2. Use find_available_lenders to discover suitable liquidity sources
        3. Use match_liquidity_requirements to optimize matching
        4. Use calculate_liquidity_costs to determine fair pricing

        Always respond with structured JSON containing:
        - liquidity_analysis: Comprehensive liquidity assessment
        - borrower_assessment: Detailed creditworthiness evaluation
        - available_lenders: List of matched lender options
        - recommended_match: Optimal lender-borrower pairing
        - pricing_analysis: Competitive cost structure

        Focus on:
        - Risk-adjusted returns for lenders
        - Competitive rates for borrowers
        - Optimal capital efficiency
        - Market depth and liquidity health
        - Sustainable lending relationships

        Maintain transparency and fairness in all liquidity matching decisions.
        """,
        tools=[
            FunctionTool(find_available_lenders),
            FunctionTool(assess_borrower_creditworthiness),
            FunctionTool(match_liquidity_requirements),
            FunctionTool(calculate_liquidity_costs)
        ],
        output_key="liquidity_analysis"
    )


# Create the agent instance
liquidity_agent = create_liquidity_agent()