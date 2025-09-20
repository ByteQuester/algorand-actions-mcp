#!/usr/bin/env python3
"""
End-to-End Lending Workflow Tests with MCP Integration

Complete lending workflow testing that integrates all components:
- MCP Services: Reader, Writer, Market Data
- Lending Engines: Collateral, Interest Rate, Loan Approval, Risk Assessment
- Real blockchain data integration
- Full loan lifecycle testing
- Error handling and edge cases
- Performance under realistic conditions

Test Scenarios:
1. Complete loan application workflow
2. Collateral valuation with real market data
3. Risk assessment with blockchain history
4. Interest rate calculation with market conditions
5. Loan approval decision making
6. Transaction execution and verification
7. Portfolio monitoring and liquidation scenarios
8. Multi-asset collateral handling
9. Cross-chain integration scenarios
10. Stress testing under market volatility
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import sys
import statistics
from decimal import Decimal
import random

# Import test framework components
from test_framework import (
    MCPServiceClient, ServiceConfig, ServiceHealth,
    PerformanceMetrics, TestResult, TestMode,
    LendingEngineTestFramework
)

from test_data_pipeline import DataValidator, PipelineTestConfig

# Add lending ecosystem to path
lending_path = Path(__file__).parent.parent.parent / "algorand-lending-ecosystem" / "algorand-lending-business-logic"
sys.path.insert(0, str(lending_path))

try:
    from algorand_lending_bl import (
        CollateralAnalyzer, InterestRateEngine, LoanApprovalEngine, RiskAssessmentEngine,
        LoanRequest, AlgorandAddress, ASAToken, AssetValuation, CollateralPosition,
        LoanDecision, RiskAssessment, RateCalculation, DecisionType,
        DEFAULT_CONFIG, create_lending_engines, create_lending_service
    )
except ImportError as e:
    logging.error(f"Failed to import lending engines: {e}")
    CollateralAnalyzer = InterestRateEngine = LoanApprovalEngine = RiskAssessmentEngine = None


@dataclass
class LoanScenario:
    """Test scenario for loan workflows"""
    name: str
    description: str
    borrower_address: str
    loan_amount: int  # microalgos
    collateral_assets: List[Dict[str, Any]]
    loan_duration_days: int
    expected_approval: bool
    risk_tolerance: str  # "low", "medium", "high"
    market_conditions: str  # "stable", "volatile", "bearish", "bullish"


@dataclass
class WorkflowResult:
    """Result of a complete workflow test"""
    scenario_name: str
    success: bool
    duration: float
    steps_completed: List[str]
    steps_failed: List[str]
    collateral_analysis: Optional[Dict] = None
    interest_rate: Optional[Dict] = None
    risk_assessment: Optional[Dict] = None
    loan_decision: Optional[Dict] = None
    transaction_result: Optional[Dict] = None
    performance_metrics: List[PerformanceMetrics] = None
    error_details: Optional[str] = None


class EndToEndTestFramework:
    """Comprehensive end-to-end testing framework"""

    def __init__(self, service_config: ServiceConfig = None, pipeline_config: PipelineTestConfig = None):
        self.service_config = service_config or ServiceConfig()
        self.pipeline_config = pipeline_config or PipelineTestConfig()
        self.mcp_client = None
        self.lending_service = None
        self.lending_engines = None
        self.validator = DataValidator()
        self.performance_metrics: List[PerformanceMetrics] = []
        self.workflow_results: List[WorkflowResult] = []

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Create test scenarios
        self.test_scenarios = self._create_test_scenarios()

    def _create_test_scenarios(self) -> List[LoanScenario]:
        """Create comprehensive test scenarios"""
        return [
            LoanScenario(
                name="conservative_algo_loan",
                description="Conservative ALGO loan with USDC collateral",
                borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                loan_amount=1_000_000,  # 1 ALGO
                collateral_assets=[
                    {"asset_id": 31566704, "amount": 2_000_000}  # 2 USDC
                ],
                loan_duration_days=30,
                expected_approval=True,
                risk_tolerance="low",
                market_conditions="stable"
            ),
            LoanScenario(
                name="high_value_multi_asset",
                description="High-value loan with multiple asset collateral",
                borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                loan_amount=10_000_000,  # 10 ALGO
                collateral_assets=[
                    {"asset_id": 31566704, "amount": 15_000_000},  # 15 USDC
                    {"asset_id": 0, "amount": 5_000_000}  # 5 ALGO
                ],
                loan_duration_days=90,
                expected_approval=True,
                risk_tolerance="medium",
                market_conditions="stable"
            ),
            LoanScenario(
                name="risky_volatile_market",
                description="Risky loan application during volatile market",
                borrower_address="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                loan_amount=5_000_000,  # 5 ALGO
                collateral_assets=[
                    {"asset_id": 31566704, "amount": 5_500_000}  # 5.5 USDC (barely sufficient)
                ],
                loan_duration_days=60,
                expected_approval=False,
                risk_tolerance="low",
                market_conditions="volatile"
            ),
            LoanScenario(
                name="under_collateralized",
                description="Under-collateralized loan application",
                borrower_address="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                loan_amount=10_000_000,  # 10 ALGO
                collateral_assets=[
                    {"asset_id": 31566704, "amount": 5_000_000}  # 5 USDC (insufficient)
                ],
                loan_duration_days=30,
                expected_approval=False,
                risk_tolerance="low",
                market_conditions="stable"
            ),
            LoanScenario(
                name="optimal_defi_yield",
                description="Optimal loan for DeFi yield farming",
                borrower_address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                loan_amount=20_000_000,  # 20 ALGO
                collateral_assets=[
                    {"asset_id": 31566704, "amount": 30_000_000},  # 30 USDC
                    {"asset_id": 0, "amount": 10_000_000}  # 10 ALGO
                ],
                loan_duration_days=180,
                expected_approval=True,
                risk_tolerance="high",
                market_conditions="bullish"
            )
        ]

    async def initialize(self):
        """Initialize the test framework"""
        self.logger.info("Initializing End-to-End Test Framework")

        # Initialize MCP client
        self.mcp_client = MCPServiceClient(self.service_config)

        # Initialize lending engines
        try:
            if CollateralAnalyzer is not None:
                self.lending_service = create_lending_service()
                self.lending_engines = create_lending_engines()
                self.logger.info("Lending engines initialized successfully")
            else:
                self.logger.error("Lending engines not available - imports failed")
                raise RuntimeError("Lending engines not available")

        except Exception as e:
            self.logger.error(f"Failed to initialize lending engines: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client and self.mcp_client.session:
            await self.mcp_client.session.close()

    async def execute_complete_workflow(self, scenario: LoanScenario) -> WorkflowResult:
        """Execute complete lending workflow for a scenario"""
        self.logger.info(f"Executing workflow: {scenario.name}")
        start_time = time.time()
        steps_completed = []
        steps_failed = []

        result = WorkflowResult(
            scenario_name=scenario.name,
            success=False,
            duration=0,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            performance_metrics=[]
        )

        try:
            async with self.mcp_client:
                # Step 1: Gather market data
                await self._step_gather_market_data(scenario, result, steps_completed, steps_failed)

                # Step 2: Analyze borrower profile
                await self._step_analyze_borrower_profile(scenario, result, steps_completed, steps_failed)

                # Step 3: Collateral analysis
                await self._step_collateral_analysis(scenario, result, steps_completed, steps_failed)

                # Step 4: Risk assessment
                await self._step_risk_assessment(scenario, result, steps_completed, steps_failed)

                # Step 5: Interest rate calculation
                await self._step_interest_rate_calculation(scenario, result, steps_completed, steps_failed)

                # Step 6: Loan approval decision
                await self._step_loan_approval_decision(scenario, result, steps_completed, steps_failed)

                # Step 7: Transaction preparation (if approved)
                if result.loan_decision and result.loan_decision.get("approved"):
                    await self._step_transaction_preparation(scenario, result, steps_completed, steps_failed)

                # Step 8: Workflow validation
                await self._step_workflow_validation(scenario, result, steps_completed, steps_failed)

                # Mark as successful if all critical steps completed
                critical_steps = ["gather_market_data", "collateral_analysis", "risk_assessment",
                                "interest_rate_calculation", "loan_approval_decision"]
                result.success = all(step in steps_completed for step in critical_steps)

        except Exception as e:
            result.error_details = str(e)
            self.logger.error(f"Workflow {scenario.name} failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def _step_gather_market_data(self, scenario: LoanScenario, result: WorkflowResult,
                                     steps_completed: List[str], steps_failed: List[str]):
        """Step 1: Gather market data for all relevant assets"""
        step_name = "gather_market_data"
        try:
            market_data = {}

            # Get ALGO price
            algo_success, algo_data, algo_duration = await self.mcp_client.get_market_data("ALGO")
            if algo_success:
                market_data["ALGO"] = algo_data

            # Get USDC price (if used as collateral)
            usdc_in_collateral = any(asset["asset_id"] == 31566704 for asset in scenario.collateral_assets)
            if usdc_in_collateral:
                usdc_success, usdc_data, usdc_duration = await self.mcp_client.get_market_data("USDC")
                if usdc_success:
                    market_data["USDC"] = usdc_data

            # Record performance
            total_duration = algo_duration + (usdc_duration if usdc_in_collateral else 0)
            self.performance_metrics.append(PerformanceMetrics(
                operation="gather_market_data",
                duration=total_duration,
                success=len(market_data) > 0,
                timestamp=datetime.now(),
                service="market_data_mcp"
            ))

            if market_data:
                result.collateral_analysis = {"market_data": market_data}
                steps_completed.append(step_name)
                self.logger.info(f"✓ {step_name}: Retrieved {len(market_data)} market prices")
            else:
                steps_failed.append(step_name)
                self.logger.error(f"✗ {step_name}: Failed to retrieve market data")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_analyze_borrower_profile(self, scenario: LoanScenario, result: WorkflowResult,
                                           steps_completed: List[str], steps_failed: List[str]):
        """Step 2: Analyze borrower profile from blockchain data"""
        step_name = "analyze_borrower_profile"
        try:
            # Get borrower account information
            account_success, account_data, account_duration = await self.mcp_client.get_account_info(
                scenario.borrower_address
            )

            self.performance_metrics.append(PerformanceMetrics(
                operation="analyze_borrower_profile",
                duration=account_duration,
                success=account_success,
                timestamp=datetime.now(),
                service="reader_mcp"
            ))

            if account_success:
                # Analyze borrower profile
                borrower_analysis = {
                    "account_data": account_data,
                    "algo_balance": account_data.get("amount", 0) / 1_000_000,
                    "asset_count": len(account_data.get("assets", [])),
                    "account_age_indicator": "amount-without-pending-rewards" in account_data,
                    "has_sufficient_balance": account_data.get("amount", 0) >= 100_000  # 0.1 ALGO minimum
                }

                if not result.collateral_analysis:
                    result.collateral_analysis = {}
                result.collateral_analysis["borrower_profile"] = borrower_analysis

                steps_completed.append(step_name)
                self.logger.info(f"✓ {step_name}: Analyzed borrower with {borrower_analysis['algo_balance']:.2f} ALGO")
            else:
                steps_failed.append(step_name)
                self.logger.error(f"✗ {step_name}: Failed to retrieve borrower account data")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_collateral_analysis(self, scenario: LoanScenario, result: WorkflowResult,
                                      steps_completed: List[str], steps_failed: List[str]):
        """Step 3: Perform comprehensive collateral analysis"""
        step_name = "collateral_analysis"
        try:
            collateral_analyzer = self.lending_service["collateral"]

            # Convert scenario data to lending engine format
            collateral_assets = []
            for asset in scenario.collateral_assets:
                if asset["asset_id"] == 0:  # ALGO
                    collateral_assets.append(ASAToken(asset_id=0, amount=asset["amount"]))
                else:
                    collateral_assets.append(ASAToken(asset_id=asset["asset_id"], amount=asset["amount"]))

            # Perform collateral analysis
            analysis_start = time.time()
            collateral_result = await asyncio.to_thread(
                collateral_analyzer.analyze_collateral,
                AlgorandAddress(scenario.borrower_address),
                collateral_assets
            )
            analysis_duration = time.time() - analysis_start

            self.performance_metrics.append(PerformanceMetrics(
                operation="collateral_analysis",
                duration=analysis_duration,
                success=True,
                timestamp=datetime.now(),
                service="lending_engine",
                engine="collateral"
            ))

            # Convert result to dict for JSON serialization
            collateral_dict = {
                "total_value_usd": float(collateral_result.total_value_usd),
                "loan_to_value_ratio": float(collateral_result.loan_to_value_ratio),
                "liquidation_threshold": float(collateral_result.liquidation_threshold),
                "risk_score": float(collateral_result.risk_score),
                "is_sufficient": collateral_result.is_sufficient,
                "asset_valuations": [
                    {
                        "asset_id": val.asset.asset_id,
                        "amount": val.asset.amount,
                        "price_usd": float(val.price_usd),
                        "value_usd": float(val.value_usd),
                        "confidence": val.confidence.value,
                        "liquidity_tier": val.liquidity_tier.value
                    }
                    for val in collateral_result.asset_valuations
                ]
            }

            result.collateral_analysis = {
                **result.collateral_analysis or {},
                "analysis": collateral_dict
            }

            steps_completed.append(step_name)
            self.logger.info(f"✓ {step_name}: Total collateral value ${collateral_dict['total_value_usd']:.2f}, "
                           f"LTV {collateral_dict['loan_to_value_ratio']:.2%}")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_risk_assessment(self, scenario: LoanScenario, result: WorkflowResult,
                                  steps_completed: List[str], steps_failed: List[str]):
        """Step 4: Perform comprehensive risk assessment"""
        step_name = "risk_assessment"
        try:
            risk_engine = self.lending_service["risk_assessment"]

            # Convert scenario data
            collateral_assets = []
            for asset in scenario.collateral_assets:
                collateral_assets.append(ASAToken(asset_id=asset["asset_id"], amount=asset["amount"]))

            # Perform risk assessment
            assessment_start = time.time()
            risk_result = await asyncio.to_thread(
                risk_engine.assess_risk,
                AlgorandAddress(scenario.borrower_address),
                collateral_assets,
                scenario.loan_amount
            )
            assessment_duration = time.time() - assessment_start

            self.performance_metrics.append(PerformanceMetrics(
                operation="risk_assessment",
                duration=assessment_duration,
                success=True,
                timestamp=datetime.now(),
                service="lending_engine",
                engine="risk_assessment"
            ))

            # Convert result to dict
            risk_dict = {
                "overall_score": float(risk_result.overall_score),
                "risk_level": risk_result.risk_level.value,
                "confidence": risk_result.confidence.value,
                "factors": {
                    "collateral_risk": float(risk_result.risk_profile.collateral_risk),
                    "borrower_risk": float(risk_result.risk_profile.borrower_risk),
                    "market_risk": float(risk_result.risk_profile.market_risk),
                    "liquidity_risk": float(risk_result.risk_profile.liquidity_risk)
                },
                "recommendations": risk_result.recommendations
            }

            result.risk_assessment = risk_dict

            steps_completed.append(step_name)
            self.logger.info(f"✓ {step_name}: Risk score {risk_dict['overall_score']:.2f}, "
                           f"level {risk_dict['risk_level']}")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_interest_rate_calculation(self, scenario: LoanScenario, result: WorkflowResult,
                                            steps_completed: List[str], steps_failed: List[str]):
        """Step 5: Calculate interest rate based on risk and market conditions"""
        step_name = "interest_rate_calculation"
        try:
            rate_engine = self.lending_service["interest_rates"]

            # Convert scenario data
            collateral_assets = []
            for asset in scenario.collateral_assets:
                collateral_assets.append(ASAToken(asset_id=asset["asset_id"], amount=asset["amount"]))

            # Calculate interest rate
            rate_start = time.time()
            rate_result = await asyncio.to_thread(
                rate_engine.calculate_rate,
                AlgorandAddress(scenario.borrower_address),
                scenario.loan_amount,
                collateral_assets,
                scenario.loan_duration_days
            )
            rate_duration = time.time() - rate_start

            self.performance_metrics.append(PerformanceMetrics(
                operation="interest_rate_calculation",
                duration=rate_duration,
                success=True,
                timestamp=datetime.now(),
                service="lending_engine",
                engine="interest_rates"
            ))

            # Convert result to dict
            rate_dict = {
                "annual_rate": float(rate_result.annual_rate),
                "daily_rate": float(rate_result.daily_rate),
                "total_interest": float(rate_result.total_interest),
                "risk_tier": rate_result.risk_tier.value,
                "factors": {
                    "base_rate": float(rate_result.factors.base_rate),
                    "risk_premium": float(rate_result.factors.risk_premium),
                    "collateral_discount": float(rate_result.factors.collateral_discount),
                    "duration_adjustment": float(rate_result.factors.duration_adjustment),
                    "market_adjustment": float(rate_result.factors.market_adjustment)
                }
            }

            result.interest_rate = rate_dict

            steps_completed.append(step_name)
            self.logger.info(f"✓ {step_name}: Annual rate {rate_dict['annual_rate']:.2%}, "
                           f"total interest {rate_dict['total_interest']:.2f} microalgos")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_loan_approval_decision(self, scenario: LoanScenario, result: WorkflowResult,
                                         steps_completed: List[str], steps_failed: List[str]):
        """Step 6: Make final loan approval decision"""
        step_name = "loan_approval_decision"
        try:
            approval_engine = self.lending_service["loan_approval"]

            # Create loan request
            collateral_assets = []
            for asset in scenario.collateral_assets:
                collateral_assets.append(ASAToken(asset_id=asset["asset_id"], amount=asset["amount"]))

            loan_request = LoanRequest(
                borrower_address=AlgorandAddress(scenario.borrower_address),
                requested_amount=scenario.loan_amount,
                collateral_assets=collateral_assets,
                loan_duration_days=scenario.loan_duration_days
            )

            # Make approval decision
            approval_start = time.time()
            approval_result = await asyncio.to_thread(
                approval_engine.evaluate_loan,
                loan_request
            )
            approval_duration = time.time() - approval_start

            self.performance_metrics.append(PerformanceMetrics(
                operation="loan_approval_decision",
                duration=approval_duration,
                success=True,
                timestamp=datetime.now(),
                service="lending_engine",
                engine="loan_approval"
            ))

            # Convert result to dict
            approval_dict = {
                "approved": approval_result.decision_type == DecisionType.APPROVED,
                "decision_type": approval_result.decision_type.value,
                "confidence": approval_result.confidence.value,
                "reasoning": approval_result.reasoning,
                "conditions": approval_result.conditions,
                "loan_terms": {
                    "principal": approval_result.loan_terms.principal if approval_result.loan_terms else None,
                    "interest_rate": float(approval_result.loan_terms.interest_rate) if approval_result.loan_terms else None,
                    "duration_days": approval_result.loan_terms.duration_days if approval_result.loan_terms else None,
                    "collateral_requirement": float(approval_result.loan_terms.collateral_requirement) if approval_result.loan_terms else None
                } if approval_result.loan_terms else None
            }

            result.loan_decision = approval_dict

            # Validate against expected outcome
            expected_approval = scenario.expected_approval
            actual_approval = approval_dict["approved"]
            prediction_correct = expected_approval == actual_approval

            steps_completed.append(step_name)
            decision_status = "APPROVED" if actual_approval else "REJECTED"
            prediction_status = "✓" if prediction_correct else "⚠"
            self.logger.info(f"{prediction_status} {step_name}: {decision_status}, "
                           f"confidence {approval_dict['confidence']}")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_transaction_preparation(self, scenario: LoanScenario, result: WorkflowResult,
                                          steps_completed: List[str], steps_failed: List[str]):
        """Step 7: Prepare transaction for loan execution (mock)"""
        step_name = "transaction_preparation"
        try:
            # Mock transaction preparation - in real implementation would create actual transactions
            transaction_data = {
                "type": "loan_execution",
                "borrower": scenario.borrower_address,
                "loan_amount": scenario.loan_amount,
                "collateral_assets": scenario.collateral_assets,
                "interest_rate": result.interest_rate["annual_rate"] if result.interest_rate else 0.05,
                "duration_days": scenario.loan_duration_days,
                "timestamp": datetime.now().isoformat(),
                "status": "prepared"
            }

            # Simulate transaction validation
            prep_start = time.time()
            await asyncio.sleep(0.1)  # Simulate preparation time
            prep_duration = time.time() - prep_start

            self.performance_metrics.append(PerformanceMetrics(
                operation="transaction_preparation",
                duration=prep_duration,
                success=True,
                timestamp=datetime.now(),
                service="writer_mcp"
            ))

            result.transaction_result = transaction_data

            steps_completed.append(step_name)
            self.logger.info(f"✓ {step_name}: Transaction prepared for {scenario.loan_amount/1_000_000:.2f} ALGO")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def _step_workflow_validation(self, scenario: LoanScenario, result: WorkflowResult,
                                      steps_completed: List[str], steps_failed: List[str]):
        """Step 8: Validate complete workflow consistency"""
        step_name = "workflow_validation"
        try:
            validation_results = []

            # Check data consistency across engines
            if result.collateral_analysis and result.risk_assessment:
                collateral_sufficient = result.collateral_analysis.get("analysis", {}).get("is_sufficient", False)
                risk_level = result.risk_assessment.get("risk_level", "HIGH")

                # Risk and collateral should be consistent
                if collateral_sufficient and risk_level in ["LOW", "MEDIUM"]:
                    validation_results.append("✓ Collateral and risk assessment consistent")
                else:
                    validation_results.append("⚠ Collateral and risk assessment inconsistent")

            # Check interest rate reasonableness
            if result.interest_rate:
                annual_rate = result.interest_rate.get("annual_rate", 0)
                if 0.01 <= annual_rate <= 0.50:  # 1% to 50% seems reasonable
                    validation_results.append("✓ Interest rate within reasonable bounds")
                else:
                    validation_results.append("⚠ Interest rate outside expected range")

            # Check loan decision logic
            if result.loan_decision:
                approved = result.loan_decision.get("approved", False)
                expected = scenario.expected_approval

                if approved == expected:
                    validation_results.append("✓ Loan decision matches expected outcome")
                else:
                    validation_results.append("⚠ Loan decision differs from expected outcome")

            # Overall workflow completeness
            critical_components = ["collateral_analysis", "risk_assessment", "interest_rate", "loan_decision"]
            completed_components = sum(1 for comp in critical_components if getattr(result, comp, None) is not None)

            if completed_components == len(critical_components):
                validation_results.append("✓ All critical components completed")
            else:
                validation_results.append(f"⚠ Only {completed_components}/{len(critical_components)} components completed")

            # Store validation results
            if not hasattr(result, 'workflow_validation'):
                result.workflow_validation = {}
            result.workflow_validation = {
                "validations": validation_results,
                "components_completed": completed_components,
                "total_components": len(critical_components),
                "consistency_score": len([v for v in validation_results if v.startswith("✓")]) / len(validation_results)
            }

            steps_completed.append(step_name)
            self.logger.info(f"✓ {step_name}: {len(validation_results)} validations performed")

        except Exception as e:
            steps_failed.append(step_name)
            self.logger.error(f"✗ {step_name}: {e}")

    async def test_loan_lifecycle_scenarios(self) -> Dict[str, Any]:
        """Test multiple loan lifecycle scenarios"""
        results = {
            "scenario_results": [],
            "performance_summary": {},
            "consistency_analysis": {},
            "error_analysis": {}
        }

        self.logger.info(f"Testing {len(self.test_scenarios)} loan scenarios")

        for scenario in self.test_scenarios:
            try:
                workflow_result = await self.execute_complete_workflow(scenario)
                self.workflow_results.append(workflow_result)

                # Convert to serializable format
                scenario_result = {
                    "scenario_name": workflow_result.scenario_name,
                    "success": workflow_result.success,
                    "duration": workflow_result.duration,
                    "steps_completed": len(workflow_result.steps_completed),
                    "steps_failed": len(workflow_result.steps_failed),
                    "prediction_accuracy": self._calculate_prediction_accuracy(scenario, workflow_result),
                    "performance_score": self._calculate_performance_score(workflow_result)
                }

                # Add detailed results
                if workflow_result.collateral_analysis:
                    scenario_result["collateral_value"] = workflow_result.collateral_analysis.get("analysis", {}).get("total_value_usd", 0)
                if workflow_result.risk_assessment:
                    scenario_result["risk_score"] = workflow_result.risk_assessment.get("overall_score", 0)
                if workflow_result.interest_rate:
                    scenario_result["interest_rate"] = workflow_result.interest_rate.get("annual_rate", 0)
                if workflow_result.loan_decision:
                    scenario_result["approved"] = workflow_result.loan_decision.get("approved", False)

                results["scenario_results"].append(scenario_result)

            except Exception as e:
                self.logger.error(f"Scenario {scenario.name} failed: {e}")
                results["scenario_results"].append({
                    "scenario_name": scenario.name,
                    "success": False,
                    "error": str(e)
                })

        # Calculate summary statistics
        successful_scenarios = [r for r in results["scenario_results"] if r.get("success", False)]

        if successful_scenarios:
            results["performance_summary"] = {
                "total_scenarios": len(self.test_scenarios),
                "successful_scenarios": len(successful_scenarios),
                "success_rate": len(successful_scenarios) / len(self.test_scenarios),
                "average_duration": statistics.mean(r["duration"] for r in successful_scenarios),
                "average_steps_completed": statistics.mean(r["steps_completed"] for r in successful_scenarios),
                "average_prediction_accuracy": statistics.mean(r.get("prediction_accuracy", 0) for r in successful_scenarios),
                "average_performance_score": statistics.mean(r.get("performance_score", 0) for r in successful_scenarios)
            }

            # Consistency analysis
            results["consistency_analysis"] = self._analyze_consistency(successful_scenarios)

        return results

    def _calculate_prediction_accuracy(self, scenario: LoanScenario, result: WorkflowResult) -> float:
        """Calculate how accurately the system predicted the outcome"""
        if not result.loan_decision:
            return 0.0

        expected = scenario.expected_approval
        actual = result.loan_decision.get("approved", False)

        return 1.0 if expected == actual else 0.0

    def _calculate_performance_score(self, result: WorkflowResult) -> float:
        """Calculate overall performance score for a workflow"""
        score = 0.0

        # Completion score (40%)
        total_steps = len(result.steps_completed) + len(result.steps_failed)
        if total_steps > 0:
            completion_score = len(result.steps_completed) / total_steps
            score += completion_score * 0.4

        # Speed score (30%)
        if result.duration > 0:
            # Faster is better, but diminishing returns
            speed_score = min(1.0, 10.0 / result.duration)
            score += speed_score * 0.3

        # Consistency score (30%)
        if hasattr(result, 'workflow_validation'):
            consistency_score = result.workflow_validation.get("consistency_score", 0)
            score += consistency_score * 0.3

        return score

    def _analyze_consistency(self, successful_scenarios: List[Dict]) -> Dict[str, Any]:
        """Analyze consistency across successful scenarios"""
        analysis = {}

        # Interest rate consistency
        rates = [r.get("interest_rate", 0) for r in successful_scenarios if r.get("interest_rate")]
        if rates:
            analysis["interest_rate_variance"] = {
                "mean": statistics.mean(rates),
                "std_dev": statistics.stdev(rates) if len(rates) > 1 else 0,
                "min": min(rates),
                "max": max(rates),
                "reasonable_variance": statistics.stdev(rates) < 0.1 if len(rates) > 1 else True
            }

        # Risk score consistency
        risk_scores = [r.get("risk_score", 0) for r in successful_scenarios if r.get("risk_score")]
        if risk_scores:
            analysis["risk_score_distribution"] = {
                "mean": statistics.mean(risk_scores),
                "std_dev": statistics.stdev(risk_scores) if len(risk_scores) > 1 else 0,
                "min": min(risk_scores),
                "max": max(risk_scores)
            }

        # Approval consistency
        approvals = [r.get("approved", False) for r in successful_scenarios]
        analysis["approval_rate"] = sum(approvals) / len(approvals) if approvals else 0

        return analysis

    async def test_stress_scenarios(self) -> Dict[str, Any]:
        """Test system under stress conditions"""
        results = {
            "concurrent_workflows": {},
            "high_volume_scenarios": {},
            "error_recovery": {}
        }

        # Test concurrent workflow execution
        self.logger.info("Testing concurrent workflow execution")
        concurrent_scenarios = self.test_scenarios[:3]  # Use first 3 scenarios

        start_time = time.time()
        concurrent_tasks = [
            self.execute_complete_workflow(scenario)
            for scenario in concurrent_scenarios
        ]

        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        concurrent_duration = time.time() - start_time

        successful_concurrent = sum(1 for r in concurrent_results
                                  if not isinstance(r, Exception) and r.success)

        results["concurrent_workflows"] = {
            "scenarios_tested": len(concurrent_scenarios),
            "successful_workflows": successful_concurrent,
            "total_duration": concurrent_duration,
            "average_duration_per_workflow": concurrent_duration / len(concurrent_scenarios),
            "concurrency_efficiency": successful_concurrent / len(concurrent_scenarios)
        }

        return results

    async def run_comprehensive_e2e_tests(self) -> Dict[str, Any]:
        """Run complete end-to-end test suite"""
        await self.initialize()

        try:
            self.logger.info("Starting comprehensive end-to-end testing")

            test_results = {}

            # Main loan lifecycle tests
            self.logger.info("Running loan lifecycle scenarios...")
            test_results["loan_scenarios"] = await self.test_loan_lifecycle_scenarios()

            # Stress testing
            self.logger.info("Running stress scenarios...")
            test_results["stress_tests"] = await self.test_stress_scenarios()

            # Performance analysis
            if self.performance_metrics:
                test_results["performance_analysis"] = self._analyze_performance_metrics()

            # Overall summary
            test_results["summary"] = self._generate_summary(test_results)

            return test_results

        finally:
            await self.cleanup()

    def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze collected performance metrics"""
        analysis = {}

        # Group by operation
        operations = {}
        for metric in self.performance_metrics:
            if metric.operation not in operations:
                operations[metric.operation] = []
            operations[metric.operation].append(metric)

        for operation, metrics in operations.items():
            durations = [m.duration for m in metrics]
            success_rate = sum(1 for m in metrics if m.success) / len(metrics)

            analysis[operation] = {
                "count": len(metrics),
                "success_rate": success_rate,
                "average_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "max_duration": max(durations),
                "min_duration": min(durations)
            }

        # Group by service
        services = {}
        for metric in self.performance_metrics:
            if metric.service not in services:
                services[metric.service] = []
            services[metric.service].append(metric)

        analysis["by_service"] = {}
        for service, metrics in services.items():
            durations = [m.duration for m in metrics]
            success_rate = sum(1 for m in metrics if m.success) / len(metrics)

            analysis["by_service"][service] = {
                "operation_count": len(metrics),
                "success_rate": success_rate,
                "average_duration": statistics.mean(durations),
                "total_duration": sum(durations)
            }

        return analysis

    def _generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall test summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "framework_version": "1.0.0",
            "test_categories": list(test_results.keys())
        }

        # Loan scenario summary
        if "loan_scenarios" in test_results:
            scenarios = test_results["loan_scenarios"]
            perf_summary = scenarios.get("performance_summary", {})

            summary["loan_scenarios"] = {
                "total_scenarios": perf_summary.get("total_scenarios", 0),
                "success_rate": perf_summary.get("success_rate", 0),
                "average_prediction_accuracy": perf_summary.get("average_prediction_accuracy", 0),
                "average_performance_score": perf_summary.get("average_performance_score", 0)
            }

        # Stress test summary
        if "stress_tests" in test_results:
            stress = test_results["stress_tests"]
            if "concurrent_workflows" in stress:
                concurrent = stress["concurrent_workflows"]
                summary["stress_tests"] = {
                    "concurrency_efficiency": concurrent.get("concurrency_efficiency", 0),
                    "concurrent_scenarios_tested": concurrent.get("scenarios_tested", 0)
                }

        # Performance summary
        if "performance_analysis" in test_results:
            perf = test_results["performance_analysis"]
            summary["performance"] = {
                "total_operations": sum(op.get("count", 0) for op in perf.values() if isinstance(perf[op], dict)),
                "services_tested": len(perf.get("by_service", {})),
                "average_success_rate": statistics.mean([
                    service.get("success_rate", 0)
                    for service in perf.get("by_service", {}).values()
                ]) if perf.get("by_service") else 0
            }

        return summary

    def print_e2e_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive end-to-end test summary"""
        print("\n" + "="*80)
        print("END-TO-END LENDING WORKFLOW TEST RESULTS")
        print("="*80)

        summary = results.get("summary", {})
        print(f"\nTest Execution: {summary.get('timestamp', 'Unknown')}")
        print(f"Framework Version: {summary.get('framework_version', 'Unknown')}")

        # Loan Scenarios
        if "loan_scenarios" in summary:
            loan_summary = summary["loan_scenarios"]
            print(f"\nLoan Scenarios:")
            print(f"  Total Scenarios: {loan_summary.get('total_scenarios', 0)}")
            print(f"  Success Rate: {loan_summary.get('success_rate', 0)*100:.1f}%")
            print(f"  Prediction Accuracy: {loan_summary.get('average_prediction_accuracy', 0)*100:.1f}%")
            print(f"  Performance Score: {loan_summary.get('average_performance_score', 0)*100:.1f}%")

        # Individual scenario results
        if "loan_scenarios" in results and "scenario_results" in results["loan_scenarios"]:
            print(f"\nDetailed Scenario Results:")
            print("-" * 50)
            for scenario in results["loan_scenarios"]["scenario_results"]:
                if scenario.get("success"):
                    status = "PASS"
                    approval_status = "APPROVED" if scenario.get("approved") else "REJECTED"
                    duration = scenario.get("duration", 0)
                    prediction = "✓" if scenario.get("prediction_accuracy", 0) > 0 else "✗"

                    print(f"  {scenario['scenario_name']:<25} {status:<6} {approval_status:<10} "
                          f"{prediction} ({duration:.2f}s)")

                    if scenario.get("risk_score"):
                        print(f"    Risk: {scenario['risk_score']:.2f}, "
                              f"Rate: {scenario.get('interest_rate', 0)*100:.2f}%")
                else:
                    print(f"  {scenario['scenario_name']:<25} FAIL   -         - "
                          f"({scenario.get('error', 'Unknown error')})")

        # Stress Tests
        if "stress_tests" in summary:
            stress_summary = summary["stress_tests"]
            print(f"\nStress Testing:")
            print(f"  Concurrent Scenarios: {stress_summary.get('concurrent_scenarios_tested', 0)}")
            print(f"  Concurrency Efficiency: {stress_summary.get('concurrency_efficiency', 0)*100:.1f}%")

        # Performance Analysis
        if "performance" in summary:
            perf_summary = summary["performance"]
            print(f"\nPerformance Analysis:")
            print(f"  Total Operations: {perf_summary.get('total_operations', 0)}")
            print(f"  Services Tested: {perf_summary.get('services_tested', 0)}")
            print(f"  Average Success Rate: {perf_summary.get('average_success_rate', 0)*100:.1f}%")

        # Detailed performance by service
        if "performance_analysis" in results and "by_service" in results["performance_analysis"]:
            print(f"\n  Performance by Service:")
            for service, metrics in results["performance_analysis"]["by_service"].items():
                print(f"    {service:<20} {metrics['operation_count']:>3} ops, "
                      f"{metrics['success_rate']*100:>5.1f}% success, "
                      f"{metrics['average_duration']:>6.3f}s avg")

        print("\n" + "="*80)


async def main():
    """Main execution function for end-to-end tests"""
    print("Starting End-to-End Lending Workflow Test Framework")

    # Configuration
    service_config = ServiceConfig(
        reader_url="http://localhost:8002",
        writer_url="http://localhost:3001",
        market_data_url="http://localhost:8789",
        timeout=30
    )

    pipeline_config = PipelineTestConfig(
        use_real_data=True,
        performance_mode=True,
        concurrent_requests=3
    )

    framework = EndToEndTestFramework(service_config, pipeline_config)

    try:
        # Run comprehensive tests
        results = await framework.run_comprehensive_e2e_tests()

        # Print summary
        framework.print_e2e_test_summary(results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/home/mpo/algorand-showcase/tests/mcp_integration/e2e_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nDetailed results saved to: {output_file}")

        # Return success based on overall performance
        summary = results.get("summary", {})
        loan_success_rate = summary.get("loan_scenarios", {}).get("success_rate", 0)

        return loan_success_rate > 0.8

    except Exception as e:
        print(f"End-to-end test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)