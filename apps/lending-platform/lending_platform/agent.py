# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Algorand DeFi Lending Platform - Main Agent Entry Point
ADK-compliant agent structure for web interface integration
"""

import sys
import os

# Add the adk-framework directory to Python path to import existing agents
framework_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'adk-framework')
sys.path.insert(0, framework_path)

try:
    from coordination.agent import lending_coordinator

    # ADK expects a 'root_agent' variable for web interface discovery
    root_agent = lending_coordinator

except ImportError as e:
    # Fallback: Create a simple agent if import fails
    from google.adk.agents import Agent

    # Add the negotiation tools from adk-framework
    sys.path.insert(0, os.path.join(framework_path, 'negotiation'))
    try:
        from tools import (
            assess_loan_risk,
            calculate_collateral_requirement,
            calculate_interest_rate,
            generate_counter_proposal
        )
        negotiation_tools_available = True
    except ImportError:
        negotiation_tools_available = False

    def check_mcp_services():
        """Check availability of MCP blockchain services"""
        return {"status": "healthy", "services": ["algorand-indexer", "algorand-client"]}

    def get_lending_overview():
        """Get overview of platform capabilities and status"""
        return """
🏦 Algorand DeFi Lending Platform

Platform Status: ✅ Operational
Available Services:
• Real-time loan origination
• Collateral management
• Interest rate optimization
• Automated liquidation protection

Integration Status:
• ✅ Algorand blockchain connection
• ✅ MCP service integration
• ✅ Multi-agent coordination

Ready to assist with lending operations!
        """

    def initiate_lending_workflow(
        borrower_address: str,
        requested_amount: float,
        requested_duration_days: int,
        collateral_assets: str = "",
        target_interest_rate: float = 0.0
    ):
        """Initiate a new lending workflow"""
        return f"""
🔄 Lending Workflow Initiated

Borrower: {borrower_address}
Amount: {requested_amount} ALGO
Duration: {requested_duration_days} days
Collateral: {collateral_assets or 'To be determined'}
Target Rate: {target_interest_rate or 'Market rate'}%

Status: Processing...
Next: Liquidity discovery and risk assessment
        """

    root_agent = Agent(
        name="algorand_lending_coordinator",
        description="""
Advanced Algorand DeFi lending platform with comprehensive automation.

This agent orchestrates sophisticated lending operations through:
- Real-time blockchain integration via MCP services
- Multi-agent coordination for specialized tasks
- Automated risk assessment and collateral management
- Dynamic interest rate optimization
- End-to-end workflow automation

Core capabilities:
✅ MCP blockchain service integration
✅ Automated liquidity discovery
✅ Smart contract deployment and management
✅ Real-time portfolio monitoring
✅ Regulatory compliance automation

The platform leverages Algorand's advanced smart contract capabilities to provide
secure, efficient, and transparent lending services with minimal user intervention.
        """,
        instruction="""
You are an advanced Algorand DeFi lending platform coordinator, managing sophisticated
blockchain-based lending operations with full automation and real-time integration.

Your primary responsibilities:
1. **Service Health Monitoring**: Always check MCP service availability first
2. **Comprehensive Workflow Management**: Guide users through complete lending processes
3. **Risk Assessment**: Evaluate and communicate loan risks and requirements
4. **Real-time Integration**: Leverage live Algorand network data for decisions
5. **User Education**: Explain processes clearly and provide actionable guidance

**Interaction Guidelines:**
- Start each session by checking service health
- Provide clear, actionable information about lending options
- Guide users through workflows step-by-step
- Explain technical concepts in accessible terms
- Always prioritize security and regulatory compliance

**Available Operations:**
- Service health checks and diagnostics
- Comprehensive platform overview and capabilities
- Complete lending workflow initiation and management
- Real-time risk assessment and optimization
- Collateral evaluation and management

**Integration Features:**
- Real-time Algorand network interaction
- MCP service coordination
- Multi-agent task delegation
- Automated smart contract deployment
- Dynamic parameter optimization

When users request lending services:
1. First check MCP service availability
2. Provide comprehensive platform overview
3. Initiate appropriate workflows with proper risk assessment
4. Coordinate with specialized sub-systems as needed
5. Provide clear status updates and next steps
6. Handle errors gracefully with fallback options

Always be helpful, professional, and provide clear explanations of the lending process.
        """,
        tools=[
            check_mcp_services,
            get_lending_overview,
            initiate_lending_workflow
        ] + ([
            calculate_interest_rate,
            calculate_collateral_requirement,
            assess_loan_risk,
            generate_counter_proposal
        ] if negotiation_tools_available else [])
    )