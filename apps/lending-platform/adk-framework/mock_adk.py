# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Mock ADK Implementation
Simulates Google ADK functionality for testing without requiring the actual package
"""

from typing import Dict, Any, List, Callable, Optional
import json


class MockAgent:
    """Mock implementation of Google ADK Agent"""

    def __init__(
        self,
        name: str,
        model: str = "gemini-2.5-flash",
        description: str = "",
        instruction: str = "",
        tools: List = None,
        sub_agents: List = None,
        output_key: str = "result"
    ):
        self.name = name
        self.model = model
        self.description = description
        self.instruction = instruction
        self.tools = tools or []
        self.sub_agents = sub_agents or []
        self.output_key = output_key

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock agent processing - simulates ADK agent execution
        In a real ADK agent, this would use Gemini to process the input
        """
        result = {
            "agent_name": self.name,
            "model_used": self.model,
            "input_received": input_data,
            "processing_status": "completed",
            "tools_available": len(self.tools),
            "sub_agents_available": len(self.sub_agents)
        }

        # Simulate agent-specific processing based on name
        if "negotiation" in self.name.lower():
            result.update(self._simulate_negotiation_processing(input_data))
        elif "liquidity" in self.name.lower():
            result.update(self._simulate_liquidity_processing(input_data))
        elif "execution" in self.name.lower():
            result.update(self._simulate_execution_processing(input_data))
        elif "coordinator" in self.name.lower():
            result.update(self._simulate_coordination_processing(input_data))

        return {self.output_key: result}

    def _simulate_negotiation_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate negotiation agent processing"""
        return {
            "negotiated_terms": {
                "interest_rate": 7.2,
                "collateral_ratio": 1.3,
                "duration_days": 30,
                "risk_assessment": "MEDIUM"
            },
            "risk_analysis": {
                "risk_score": 75,
                "risk_category": "MEDIUM",
                "factors": ["balance_adequate", "transaction_history_good"]
            },
            "recommendation": "APPROVE_WITH_CONDITIONS"
        }

    def _simulate_liquidity_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate liquidity agent processing"""
        return {
            "liquidity_analysis": {
                "lenders_found": 3,
                "total_capacity": 500.0,
                "best_match": "AlgoCapital Partners",
                "average_rate": 7.5
            },
            "borrower_assessment": {
                "credit_score": 78,
                "credit_tier": "NEAR_PRIME",
                "risk_category": "MEDIUM"
            },
            "recommended_match": {
                "lender": "AlgoCapital Partners",
                "offered_rate": 7.2,
                "capacity": 200.0
            }
        }

    def _simulate_execution_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate execution agent processing"""
        return {
            "execution_plan": {
                "transactions_prepared": 3,
                "atomic_group_ready": True,
                "estimated_cost": 0.0285,
                "estimated_time": "2-5 minutes"
            },
            "validation_results": {
                "can_execute": True,
                "requirements_met": True,
                "blocking_issues": []
            },
            "transaction_group": {
                "group_id": "TXG_MOCK_123",
                "transactions": [
                    {"type": "collateral_deposit", "amount": 130000000},
                    {"type": "loan_disbursement", "amount": 100000000},
                    {"type": "contract_creation", "fee": 28500}
                ]
            }
        }

    def _simulate_coordination_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate coordination agent processing"""
        return {
            "workflow_status": "completed",
            "steps_completed": ["liquidity", "negotiation", "execution"],
            "agent_results": {
                "liquidity": "success",
                "negotiation": "success",
                "execution": "ready"
            },
            "final_recommendation": {
                "loan_approved": True,
                "terms": {
                    "amount": 100.0,
                    "rate": 7.2,
                    "duration": 30
                }
            }
        }


class MockFunctionTool:
    """Mock implementation of Google ADK FunctionTool"""

    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
        self.description = func.__doc__ or f"Tool for {func.__name__}"

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class MockAgentTool:
    """Mock implementation of Google ADK AgentTool"""

    def __init__(self, agent: MockAgent):
        self.agent = agent
        self.name = f"agent_tool_{agent.name}"

    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.agent.process(input_data)


# Mock modules structure to replace actual ADK imports
class MockADKAgents:
    Agent = MockAgent


class MockADKTools:
    FunctionTool = MockFunctionTool

    class agent_tool:
        AgentTool = MockAgentTool


# Create mock google.adk structure
class MockGoogleADK:
    agents = MockADKAgents()
    tools = MockADKTools()


# For testing, we'll monkey patch the imports
def patch_adk_imports():
    """Patch ADK imports for testing without the actual package"""
    import sys

    # Create mock modules
    mock_google = type(sys)("google")
    mock_adk = MockGoogleADK()
    mock_google.adk = mock_adk

    sys.modules["google"] = mock_google
    sys.modules["google.adk"] = mock_adk
    sys.modules["google.adk.agents"] = mock_adk.agents
    sys.modules["google.adk.tools"] = mock_adk.tools
    sys.modules["google.adk.tools.agent_tool"] = mock_adk.tools.agent_tool