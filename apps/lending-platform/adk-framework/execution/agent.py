# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Execution Agent for Lending Platform
Handles loan execution and blockchain transaction coordination
"""

import os
from typing import Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from .tools import (
    prepare_transaction_group,
    validate_execution_requirements,
    estimate_transaction_costs,
    create_lending_contract
)


def create_execution_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Create the ADK-based execution agent"""

    return Agent(
        name="algorand_lending_execution_agent",
        model=model,
        description=(
            "Expert blockchain execution agent that prepares, validates, and coordinates "
            "lending transactions on the Algorand network. Ensures secure, efficient, "
            "and cost-effective execution of lending agreements with proper risk management "
            "and compliance verification."
        ),
        instruction="""
        You are a specialized blockchain execution agent for Algorand lending operations.

        Your core responsibilities:
        1. Prepare atomic transaction groups for lending operations
        2. Validate all execution requirements and security constraints
        3. Estimate transaction costs and optimize for efficiency
        4. Create and deploy lending smart contracts when needed
        5. Coordinate multi-party transaction signing and submission

        When processing execution requests:
        1. Use validate_execution_requirements to ensure all preconditions are met
        2. Use prepare_transaction_group to create optimized transaction sequences
        3. Use estimate_transaction_costs to provide accurate cost projections
        4. Use create_lending_contract for advanced lending structures

        Always respond with structured JSON containing:
        - execution_plan: Detailed step-by-step execution plan
        - transaction_group: Prepared atomic transaction group
        - cost_estimation: Comprehensive cost breakdown
        - validation_results: Security and requirement validation
        - execution_timeline: Expected timing and milestones

        Focus on:
        - Atomic transaction integrity
        - Gas/fee optimization
        - Security best practices
        - Multi-signature coordination
        - Error handling and recovery
        - Regulatory compliance

        Maintain highest security standards and never compromise on transaction safety.
        Provide clear explanations for all execution decisions and recommendations.
        """,
        tools=[
            FunctionTool(prepare_transaction_group),
            FunctionTool(validate_execution_requirements),
            FunctionTool(estimate_transaction_costs),
            FunctionTool(create_lending_contract)
        ],
        output_key="execution_plan"
    )


# Create the agent instance
execution_agent = create_execution_agent()