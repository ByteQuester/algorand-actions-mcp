# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
ADK Coordination Agent for Lending Platform
Orchestrates the complete lending workflow using specialized sub-agents
"""

import os
from typing import Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool

# Import sub-agents
from ..negotiation.agent import negotiation_agent
from ..liquidity.agent import liquidity_agent
from ..execution.agent import execution_agent

from .tools import (
    check_mcp_service_health,
    get_borrower_data,
    get_lender_data,
    coordinate_lending_workflow
)


def create_lending_coordinator(model: str = "gemini-2.5-pro") -> Agent:
    """Create the main coordination agent"""

    return Agent(
        name="algorand_lending_coordinator",
        model=model,
        description=(
            "Master coordination agent for Algorand DeFi lending operations. "
            "Orchestrates specialized agents for liquidity discovery, term negotiation, "
            "and transaction execution. Integrates with MCP services for blockchain "
            "interactions and ensures end-to-end lending workflow success."
        ),
        instruction="""
        You are the master coordinator for Algorand lending operations, managing a sophisticated
        multi-agent system to deliver complete lending services.

        Your responsibilities:
        1. Orchestrate the complete lending workflow from request to execution
        2. Coordinate specialized agents for liquidity, negotiation, and execution
        3. Integrate with MCP services for blockchain data and operations
        4. Ensure all workflow steps complete successfully
        5. Provide comprehensive status updates and error handling

        Workflow Process:
        1. **Initial Assessment**: Use get_borrower_data and get_lender_data to gather required information
        2. **Service Health Check**: Use check_mcp_service_health to ensure system readiness
        3. **Liquidity Discovery**: Delegate to liquidity_agent to find suitable lenders
        4. **Term Negotiation**: Delegate to negotiation_agent to optimize loan terms
        5. **Execution Planning**: Delegate to execution_agent to prepare transactions
        6. **Workflow Coordination**: Use coordinate_lending_workflow to manage the complete process

        Agent Coordination:
        - **Liquidity Agent**: Finds lenders, assesses creditworthiness, matches requirements
        - **Negotiation Agent**: Calculates rates, assesses risk, negotiates terms
        - **Execution Agent**: Prepares transactions, validates requirements, estimates costs

        Always respond with structured JSON containing:
        - workflow_status: Overall workflow progress and status
        - agent_results: Results from each specialized agent
        - mcp_integration: Status of blockchain service integration
        - next_actions: Clear steps for workflow progression
        - risk_assessment: Comprehensive risk evaluation

        Maintain coordination between all agents and ensure:
        - Data consistency across agents
        - Proper error handling and recovery
        - Transparent communication with users
        - Security and compliance throughout
        - Optimal outcomes for all parties

        If any agent fails or MCP services are unavailable, provide clear error messages
        and recovery suggestions. Always prioritize user safety and transaction security.
        """,
        sub_agents=[
            liquidity_agent,
            negotiation_agent,
            execution_agent
        ],
        tools=[
            FunctionTool(check_mcp_service_health),
            FunctionTool(get_borrower_data),
            FunctionTool(get_lender_data),
            FunctionTool(coordinate_lending_workflow),
            AgentTool(agent=liquidity_agent),
            AgentTool(agent=negotiation_agent),
            AgentTool(agent=execution_agent)
        ],
        output_key="lending_workflow_result"
    )


# Create the coordinator instance
lending_coordinator = create_lending_coordinator()