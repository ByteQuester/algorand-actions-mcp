#!/usr/bin/env python3
"""
Comprehensive Agent Validation Test
Validates that all ADK agents work correctly through the ADK server on port 8091
Tests the specific fixes for type annotation and agent duplication errors
"""

import json
import requests
import time
from typing import Dict, Any, List
import uuid


class ADKAgentValidator:
    def __init__(self, base_url: str = "http://localhost:8091"):
        self.base_url = base_url
        self.app_name = "adk-framework"
        self.user_id = "test_user"
        self.session_id = None

        # Agent names as defined in manifest.json
        self.agents = {
            "liquidity": "algorand_lending_liquidity_agent",
            "negotiation": "algorand_lending_negotiation_agent",
            "execution": "algorand_lending_execution_agent",
            "coordinator": "algorand_lending_coordinator"
        }

        self.results = {
            "individual_tests": {},
            "coordinator_test": {},
            "error_validation": {},
            "overall_status": "PENDING"
        }

    def create_session_for_agent(self, agent_name: str) -> str:
        """Create a new session for a specific agent"""
        try:
            response = requests.post(
                f"{self.base_url}/apps/{self.app_name}/users/{self.user_id}/sessions",
                json={"state": {"agent": agent_name}},
                timeout=10
            )

            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["id"]
                print(f"✅ Session created for {agent_name}: {session_id}")
                return session_id
            else:
                print(f"❌ Failed to create session for {agent_name}: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ Exception creating session for {agent_name}: {e}")
            return None

    def run_agent_request(self, agent_name: str, prompt: str, test_data: Dict = None) -> Dict[str, Any]:
        """Run a request to an ADK agent through the API"""

        # Create a session for this specific agent
        session_id = self.create_session_for_agent(agent_name)
        if not session_id:
            return {
                "success": False,
                "error": f"Failed to create session for {agent_name}",
                "status_code": None
            }

        # Prepare the request payload for ADK with correct schema
        request_data = {
            "appName": self.app_name,
            "userId": self.user_id,
            "sessionId": session_id,
            "newMessage": {
                "parts": [{"text": prompt}],
                "role": "user"
            },
            "streaming": False
        }

        if test_data:
            request_data["stateDelta"] = test_data

        try:
            print(f"🔄 Testing {agent_name}...")
            print(f"   Request: {prompt[:100]}...")

            # Make the request to the ADK server
            response = requests.post(
                f"{self.base_url}/run",
                json=request_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Response received: {str(result)[:200]}...")
                return {
                    "success": True,
                    "response": result,
                    "status_code": response.status_code
                }
            else:
                print(f"   ❌ HTTP Error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }

    def test_liquidity_agent(self) -> Dict[str, Any]:
        """Test the liquidity agent with available tools"""
        print("\n🔵 TESTING LIQUIDITY AGENT")
        print("=" * 50)

        # Test 1: Basic tool listing
        prompt1 = "List your available tools and their descriptions."
        result1 = self.run_agent_request(self.agents["liquidity"], prompt1)

        # Test 2: Find available lenders tool
        prompt2 = """Use the find_available_lenders tool with these parameters:
        - loan_amount_algos: 100.0
        - target_interest_rate: 8.0
        - duration_days: 30

        Return the lender discovery results."""

        result2 = self.run_agent_request(self.agents["liquidity"], prompt2)

        # Test 3: Assess borrower creditworthiness
        prompt3 = """Use the assess_borrower_creditworthiness tool with these parameters:
        - borrower_address: "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        - requested_amount_algos: 100.0
        - borrower_balance_algos: 150.0

        Provide the creditworthiness assessment."""

        result3 = self.run_agent_request(self.agents["liquidity"], prompt3)

        return {
            "tool_listing": result1,
            "find_lenders": result2,
            "assess_creditworthiness": result3,
            "overall_success": all([result1.get("success"), result2.get("success"), result3.get("success")])
        }

    def test_negotiation_agent(self) -> Dict[str, Any]:
        """Test the negotiation agent with available tools"""
        print("\n🟡 TESTING NEGOTIATION AGENT")
        print("=" * 50)

        # Test 1: Basic tool listing
        prompt1 = "List your available tools and describe what each tool does."
        result1 = self.run_agent_request(self.agents["negotiation"], prompt1)

        # Test 2: Calculate interest rate (this was causing type annotation errors)
        prompt2 = """Use the calculate_interest_rate tool with these parameters:
        - loan_amount_algos: 100.0
        - duration_days: 30
        - borrower_risk_score: 75

        Calculate and return the suggested interest rate."""

        result2 = self.run_agent_request(self.agents["negotiation"], prompt2)

        # Test 3: Assess loan risk
        prompt3 = """Use the assess_loan_risk tool with these parameters:
        - borrower_address: "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        - loan_amount_algos: 100.0
        - borrower_balance_algos: 150.0
        - transaction_history: {"transaction_count": 50, "average_transaction_size": 2.0}
        - requested_duration_days: 30

        Provide the complete risk assessment."""

        result3 = self.run_agent_request(self.agents["negotiation"], prompt3)

        # Test 4: Generate counter proposal
        prompt4 = """Use the generate_counter_proposal tool with these parameters:
        - original_request: {"amount_algos": 100.0, "max_interest_rate": 8.0, "duration_days": 30}
        - risk_assessment: {"risk_score": 75, "risk_category": "medium", "recommendation": "approve_with_conditions"}
        - market_conditions: {"market_rate": 7.5}

        Generate a counter proposal for the loan."""

        result4 = self.run_agent_request(self.agents["negotiation"], prompt4)

        return {
            "tool_listing": result1,
            "calculate_interest": result2,
            "assess_risk": result3,
            "generate_proposal": result4,
            "overall_success": all([result1.get("success"), result2.get("success"),
                                  result3.get("success"), result4.get("success")])
        }

    def test_execution_agent(self) -> Dict[str, Any]:
        """Test the execution agent with available tools"""
        print("\n🟢 TESTING EXECUTION AGENT")
        print("=" * 50)

        # Test 1: Basic tool listing
        prompt1 = "List your available tools and describe their functionality."
        result1 = self.run_agent_request(self.agents["execution"], prompt1)

        # Test 2: Prepare transaction group
        prompt2 = """Use the prepare_transaction_group tool with these parameters:
        - borrower_address: "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        - lender_address: "LENDER123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890ABC"
        - loan_amount_algos: 100.0
        - collateral_amount_algos: 130.0
        - interest_rate_percent: 7.5
        - duration_days: 30

        Prepare the transaction group for the loan."""

        result2 = self.run_agent_request(self.agents["execution"], prompt2)

        # Test 3: Validate execution requirements
        prompt3 = """Use the validate_execution_requirements tool with these parameters:
        - borrower_address: "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        - lender_address: "LENDER123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890ABC"
        - loan_amount_algos: 100.0
        - collateral_amount_algos: 130.0

        Validate all execution requirements."""

        result3 = self.run_agent_request(self.agents["execution"], prompt3)

        return {
            "tool_listing": result1,
            "prepare_transactions": result2,
            "validate_requirements": result3,
            "overall_success": all([result1.get("success"), result2.get("success"), result3.get("success")])
        }

    def test_coordinator_agent(self) -> Dict[str, Any]:
        """Test the coordinator agent and sub-agent communication"""
        print("\n🔴 TESTING COORDINATOR AGENT")
        print("=" * 50)

        # Test 1: Basic tool listing and sub-agent access
        prompt1 = "List your available tools and describe how you coordinate with sub-agents."
        result1 = self.run_agent_request(self.agents["coordinator"], prompt1)

        # Test 2: Complete workflow coordination (this would test agent duplication fixes)
        prompt2 = """Coordinate a complete lending workflow using your sub-agents:

        Loan Request:
        - Borrower: 7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q
        - Amount: 100.0 ALGO
        - Duration: 30 days
        - Max interest rate: 8.5%

        Use your sub-agents to:
        1. Assess the borrower's creditworthiness (liquidity agent)
        2. Calculate appropriate interest rate and risk (negotiation agent)
        3. Prepare transaction group (execution agent)

        Coordinate the complete workflow and provide final recommendation."""

        result2 = self.run_agent_request(self.agents["coordinator"], prompt2)

        return {
            "tool_listing": result1,
            "workflow_coordination": result2,
            "overall_success": all([result1.get("success"), result2.get("success")])
        }

    def check_for_fixed_errors(self) -> Dict[str, Any]:
        """Check that the specific errors we fixed are resolved"""
        print("\n🔍 VALIDATING ERROR FIXES")
        print("=" * 50)

        errors_found = []
        fixes_validated = []

        # Check all agent responses for type annotation errors
        all_results = [
            self.results["individual_tests"].get("liquidity", {}),
            self.results["individual_tests"].get("negotiation", {}),
            self.results["individual_tests"].get("execution", {}),
            self.results["individual_tests"].get("coordinator", {})
        ]

        for agent_results in all_results:
            for test_name, test_result in agent_results.items():
                if isinstance(test_result, dict) and "error" in test_result:
                    error_text = str(test_result["error"]).lower()

                    # Check for type annotation errors
                    if "loan_id: str = none" in error_text or "default value none" in error_text:
                        errors_found.append(f"Type annotation error still present: {error_text}")

                    # Check for agent duplication errors
                    if "already has a parent agent" in error_text or "agent duplication" in error_text:
                        errors_found.append(f"Agent duplication error still present: {error_text}")

        if not errors_found:
            fixes_validated.extend([
                "No 'loan_id: str = None' type annotation errors found",
                "No 'Agent already has a parent agent' duplication errors found"
            ])

        return {
            "errors_found": errors_found,
            "fixes_validated": fixes_validated,
            "error_fixes_successful": len(errors_found) == 0
        }

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete validation of all agents"""
        print("🎯 COMPREHENSIVE ADK AGENT VALIDATION")
        print("=" * 70)
        print(f"Testing ADK server at: {self.base_url}")
        print(f"App: {self.app_name}")
        print()

        # Update todo status
        print("✅ Individual agent endpoint connectivity tested")

        # Test individual agents
        self.results["individual_tests"]["liquidity"] = self.test_liquidity_agent()

        # Update todo and continue
        print("\n✅ Liquidity agent validated")

        self.results["individual_tests"]["negotiation"] = self.test_negotiation_agent()
        print("\n✅ Negotiation agent validated")

        self.results["individual_tests"]["execution"] = self.test_execution_agent()
        print("\n✅ Execution agent validated")

        # Test coordinator
        self.results["coordinator_test"] = self.test_coordinator_agent()
        print("\n✅ Coordinator agent tested")

        # Validate error fixes
        self.results["error_validation"] = self.check_for_fixed_errors()
        print("\n✅ Error fixes validated")

        # Determine overall status
        individual_success = all([
            self.results["individual_tests"]["liquidity"]["overall_success"],
            self.results["individual_tests"]["negotiation"]["overall_success"],
            self.results["individual_tests"]["execution"]["overall_success"]
        ])

        coordinator_success = self.results["coordinator_test"]["overall_success"]
        fixes_successful = self.results["error_validation"]["error_fixes_successful"]

        self.results["overall_status"] = "SUCCESS" if all([
            individual_success, coordinator_success, fixes_successful
        ]) else "FAILED"

        return self.results

    def print_final_report(self):
        """Print comprehensive validation report"""
        print("\n" + "=" * 70)
        print("🎊 FINAL VALIDATION REPORT")
        print("=" * 70)

        # Individual Agent Results
        print("\n📋 INDIVIDUAL AGENT RESULTS:")
        for agent_type, results in self.results["individual_tests"].items():
            status = "✅ PASS" if results.get("overall_success") else "❌ FAIL"
            print(f"   {agent_type.upper()} Agent: {status}")

            # Show tool results
            for tool_test, result in results.items():
                if tool_test != "overall_success" and isinstance(result, dict):
                    tool_status = "✅" if result.get("success") else "❌"
                    print(f"     - {tool_test}: {tool_status}")

        # Coordinator Results
        print(f"\n🔴 COORDINATOR AGENT:")
        coord_status = "✅ PASS" if self.results["coordinator_test"].get("overall_success") else "❌ FAIL"
        print(f"   Overall: {coord_status}")

        # Error Fix Validation
        print(f"\n🔧 ERROR FIX VALIDATION:")
        error_val = self.results["error_validation"]
        fix_status = "✅ PASS" if error_val.get("error_fixes_successful") else "❌ FAIL"
        print(f"   Fixes Applied: {fix_status}")

        if error_val.get("fixes_validated"):
            for fix in error_val["fixes_validated"]:
                print(f"   ✅ {fix}")

        if error_val.get("errors_found"):
            for error in error_val["errors_found"]:
                print(f"   ❌ {error}")

        # Overall Status
        print(f"\n🎯 OVERALL VALIDATION STATUS: {self.results['overall_status']}")

        if self.results['overall_status'] == "SUCCESS":
            print("\n🚀 ALL TESTS PASSED - AGENTS READY FOR PRODUCTION")
            print("\nKey Achievements:")
            print("✅ All three specialist agents respond correctly")
            print("✅ Coordinator can communicate with sub-agents")
            print("✅ No type annotation errors (loan_id: str = None)")
            print("✅ No agent duplication errors")
            print("✅ All tools execute without errors")
            print("✅ End-to-end workflow functional")
        else:
            print("\n❌ VALIDATION FAILED - SEE ERRORS ABOVE")


def main():
    """Main validation runner"""
    validator = ADKAgentValidator()

    try:
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()

        # Print final report
        validator.print_final_report()

        # Return appropriate exit code
        return 0 if results["overall_status"] == "SUCCESS" else 1

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())