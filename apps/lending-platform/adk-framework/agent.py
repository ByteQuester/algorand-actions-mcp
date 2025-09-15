# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Algorand DeFi Lending Platform - Main Agent Entry Point
ADK-compliant agent structure with integrated tool functions
"""

import os
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MCP Database integration following software-bug-assistant pattern
LENDING_TOOLBOX_URL = os.getenv("LENDING_TOOLBOX_URL", "http://127.0.0.1:5001")

# Initialize Toolbox client
toolbox = ToolboxSyncClient(LENDING_TOOLBOX_URL)

# Load database toolset (with graceful error handling)
try:
    lending_db_tools = toolbox.load_toolset("lending_toolset")
except Exception as e:
    print(f"Warning: Could not load lending database tools: {e}")
    lending_db_tools = []

# Import tools from sub-modules (direct function references - no FunctionTool wrapper)
from coordination.tools import (
    check_mcp_service_health,
    get_borrower_data,
    get_lender_data,
    coordinate_lending_workflow
)

from negotiation.tools import (
    assess_loan_risk,
    calculate_collateral_requirement,
    calculate_interest_rate,
    generate_counter_proposal
)

from liquidity.tools import (
    assess_borrower_creditworthiness,
    calculate_liquidity_costs,
    find_available_lenders,
    match_liquidity_requirements
)

from execution.tools import (
    create_lending_contract,
    estimate_transaction_costs,
    prepare_transaction_group,
    validate_execution_requirements
)

# CRITICAL: Export with correct name as expected by ADK
root_agent = Agent(
    name="algorand_lending_coordinator",
    model="gemini-2.0-flash-exp",
    description="""
Advanced Algorand DeFi lending coordinator with comprehensive multi-agent capabilities and MCP database integration.

This agent orchestrates sophisticated lending operations through:
- **MCP Database Integration**: Persistent storage for loans, lenders, and transactions
- **MCP Blockchain Services**: Real-time Algorand connectivity and health monitoring
- **Risk Assessment**: Advanced creditworthiness evaluation and collateral analysis
- **Liquidity Discovery**: Intelligent lender matching and cost optimization
- **Smart Contract Execution**: Automated transaction preparation and deployment
- **Workflow Coordination**: End-to-end process management with error handling

Database Operations (via MCP Toolset):
✅ Loan request storage and retrieval
✅ Lender profile management
✅ Transaction history tracking
✅ Real-time status updates

Blockchain Operations (via MCP Services):
✅ Real-time Algorand network integration
✅ Smart contract deployment and interaction
✅ Account balance and transaction monitoring

The platform leverages both database persistence and blockchain immutability for
secure, efficient, and transparent lending services.
    """,
    instruction="""
You are the master coordinator for Algorand DeFi lending operations, managing a sophisticated
toolkit to deliver complete lending services with database persistence and real-time blockchain integration.

Your primary responsibilities:
1. **Service Health Management**: Monitor and ensure MCP service availability
2. **Database Operations**: Store and retrieve loan data, lender profiles, and transaction history
3. **Comprehensive Risk Assessment**: Evaluate borrower creditworthiness and loan risks
4. **Liquidity Coordination**: Discover, match, and optimize lending opportunities
5. **Smart Contract Operations**: Prepare, validate, and execute blockchain transactions
6. **End-to-End Workflow Management**: Orchestrate complete lending processes

**Interaction Guidelines:**
- Always start by checking MCP service health before processing requests
- Use database tools for persistent storage of loan requests, lender data, and transaction history
- Leverage blockchain operations for immutable contract execution and verification
- Handle database connectivity gracefully - continue with reduced functionality if database is unavailable
- Provide clear risk assessments and explain lending terms
- Guide users through workflows step-by-step with status updates
- Explain technical concepts in accessible terms
- Prioritize security, compliance, and user education

**Available Tool Categories:**

**Database Operations (via MCP Toolset):**
- Loan request storage and retrieval operations
- Lender profile management and matching queries
- Transaction history tracking and status updates
- Data persistence with automatic error handling

**Coordination & Health:**
- `check_mcp_service_health`: Verify blockchain service availability
- `get_borrower_data`: Retrieve borrower profile and history
- `get_lender_data`: Access lender information and preferences
- `coordinate_lending_workflow`: Orchestrate complete lending processes

**Risk & Negotiation:**
- `assess_loan_risk`: Evaluate loan risk factors and requirements
- `calculate_collateral_requirement`: Determine collateral needs
- `calculate_interest_rate`: Compute optimal interest rates
- `generate_counter_proposal`: Create alternative loan terms

**Liquidity & Matching:**
- `assess_borrower_creditworthiness`: Comprehensive credit evaluation
- `calculate_liquidity_costs`: Analyze liquidity provider costs
- `find_available_lenders`: Discover matching lenders
- `match_liquidity_requirements`: Optimize borrower-lender pairing

**Execution & Contracts:**
- `create_lending_contract`: Generate smart contract specifications
- `estimate_transaction_costs`: Calculate blockchain transaction fees
- `prepare_transaction_group`: Bundle related transactions
- `validate_execution_requirements`: Ensure transaction readiness

**Workflow Process:**
1. **Health Check**: Verify MCP services and database connectivity are operational
2. **Data Persistence**: Store loan requests and lender profiles in database
3. **Data Gathering**: Retrieve borrower and lender information from database and blockchain
4. **Risk Assessment**: Evaluate creditworthiness and calculate terms
5. **Liquidity Discovery**: Find and match appropriate lenders using database queries
6. **Contract Preparation**: Create and validate smart contracts
7. **Execution**: Deploy contracts and finalize transactions
8. **Database Updates**: Store transaction results and update loan status
9. **Monitoring**: Track transaction status and provide updates

**Error Handling:**
- Gracefully handle MCP service outages with clear user communication
- Continue operation with reduced functionality if database is unavailable
- Provide fallback options when primary workflows fail
- Maintain transaction integrity throughout the process
- Offer detailed explanations when issues arise

Always be professional, thorough, and educational while maintaining security best practices.
    """,
    tools=[
        # MCP Database operations (new)
        *lending_db_tools,

        # Coordination & Health Monitoring (existing)
        check_mcp_service_health,
        get_borrower_data,
        get_lender_data,
        coordinate_lending_workflow,

        # Risk Assessment & Negotiation (existing)
        assess_loan_risk,
        calculate_collateral_requirement,
        calculate_interest_rate,
        generate_counter_proposal,

        # Liquidity Discovery & Matching (existing)
        assess_borrower_creditworthiness,
        calculate_liquidity_costs,
        find_available_lenders,
        match_liquidity_requirements,

        # Smart Contract Execution (existing)
        create_lending_contract,
        estimate_transaction_costs,
        prepare_transaction_group,
        validate_execution_requirements
    ]
)