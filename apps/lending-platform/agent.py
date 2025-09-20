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

# Add the src/agents directory to Python path to import existing agents
agents_path = os.path.join(os.path.dirname(__file__), 'src', 'agents')
sys.path.insert(0, agents_path)

try:
    from coordination.agent import lending_coordinator

    # ADK expects a 'root_agent' variable for web interface discovery
    root_agent = lending_coordinator

except ImportError as e:
    print(f"Error importing agent: {e}")
    # Fallback: Create a simple agent if import fails
    try:
        from google.adk.agents import Agent

        root_agent = Agent(
            name="lending_platform",
            description="Algorand DeFi Lending Platform",
            instruction="I help manage DeFi lending on Algorand blockchain.",
            tools=[]
        )
    except ImportError:
        # If even google.adk is not available, create a mock
        class MockAgent:
            def __init__(self):
                self.name = "lending_platform"
                self.description = "Algorand DeFi Lending Platform (Mock)"

        root_agent = MockAgent()

# Export the agent for ADK discovery
__all__ = ['root_agent']