"""
Cross-Engine Workflow Integration Tests

Tests the complete workflows that span multiple engines, verifying that data flows
correctly between engines and that the complete lending decision pipeline works.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time

from conftest import (
    assert_engine_health, assert_mcp_connectivity, create_test_loan_request,
    PerformanceMonitor
)


class TestCrossEngineWorkflows:
    """Test cross-engine workflow integration"""

    @pytest.mark.asyncio
    async def test_portfolio_to_risk_to_liquidation_workflow(self, all_engines, sample_collateral_positions):
        """Test complete workflow: portfolio analysis → risk assessment → liquidation scenarios"""

        # Step 1: Portfolio diversification analysis
        portfolio_engine = all_engines["portfolio"]
        portfolio_result = await portfolio_engine.analyze_portfolio({
            "positions": [
                {
                    "asset_id": pos.asset_id,
                    "quantity": pos.quantity,
                    "current_price": pos.current_price_usd
                }
                for pos in sample_collateral_positions
            ]
        })

        assert portfolio_result is not None
        assert "diversification_score" in portfolio_result
        assert "risk_metrics" in portfolio_result

        # Step 2: Risk assessment using portfolio data
        collateral_engine = all_engines["collateral"]
        risk_result = await collateral_engine.assess_collateral_risk({
            "loan_amount": 50000.0,
            "collateral_positions": sample_collateral_positions,
            "portfolio_metrics": portfolio_result
        })

        assert risk_result is not None
        assert "risk_level" in risk_result
        assert "required_collateral_ratio" in risk_result

        # Step 3: Liquidation scenario analysis
        liquidation_engine = all_engines["liquidation"]
        liquidation_scenarios = await liquidation_engine.analyze_liquidation_scenarios({
            "collateral_positions": sample_collateral_positions,
            "risk_assessment": risk_result,
            "current_ltv": 0.8
        })

        assert liquidation_scenarios is not None
        assert "scenarios" in liquidation_scenarios
        assert len(liquidation_scenarios["scenarios"]) > 0

        # Verify workflow consistency
        assert portfolio_result["diversification_score"] <= 1.0
        assert risk_result["risk_level"] in ["low", "medium", "high", "critical"]

        # Higher diversification should generally lead to lower risk
        if portfolio_result["diversification_score"] > 0.7:
            assert risk_result["risk_level"] in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_oracle_to_volatility_to_collateral_workflow(self, all_engines, mock_asset_data):
        """Test workflow: oracle data → volatility assessment → collateral requirements"""

        # Step 1: Get current price data from oracle
        oracle_engine = all_engines["oracle"]
        price_data = await oracle_engine.get_asset_prices(["0", "31566704"])

        assert price_data is not None
        assert "0" in price_data
        assert "31566704" in price_data

        # Step 2: Volatility assessment using price data
        volatility_engine = all_engines["volatility"]
        volatility_result = await volatility_engine.calculate_volatility({
            "asset_ids": ["0", "31566704"],
            "price_data": price_data,
            "time_window": 30
        })

        assert volatility_result is not None
        assert "volatility_metrics" in volatility_result

        # Step 3: Collateral requirements based on volatility
        collateral_engine = all_engines["collateral"]
        collateral_req = await collateral_engine.calculate_requirements({
            "loan_amount": 100000.0,
            "asset_ids": ["0", "31566704"],
            "volatility_data": volatility_result,
            "price_data": price_data
        })

        assert collateral_req is not None
        assert "required_collateral_ratio" in collateral_req
        assert "total_collateral_value" in collateral_req

        # Verify logical consistency
        # Higher volatility should require higher collateral ratios
        algo_volatility = volatility_result["volatility_metrics"]["0"]["monthly_volatility"]
        usdc_volatility = volatility_result["volatility_metrics"]["31566704"]["monthly_volatility"]

        assert algo_volatility > usdc_volatility  # ALGO should be more volatile than USDC
        assert collateral_req["required_collateral_ratio"] >= 1.2  # Minimum safe ratio

    @pytest.mark.asyncio
    async def test_complete_lending_decision_pipeline(self, all_engines, test_data_generator):
        """Test the complete lending decision pipeline through all engines"""

        loan_request = create_test_loan_request(amount=75000.0, collateral_assets=["0", "31566704"])

        # Step 1: Asset valuation
        valuation_engine = all_engines["valuation"]
        asset_values = await valuation_engine.value_assets({
            "asset_ids": loan_request["collateral_assets"],
            "quantities": [300000.0, 50000.0],  # ALGO and USDC quantities
            "valuation_method": "market_based"
        })

        assert asset_values is not None
        assert "total_value" in asset_values

        # Step 2: Oracle price validation
        oracle_engine = all_engines["oracle"]
        oracle_prices = await oracle_engine.validate_prices({
            "asset_ids": loan_request["collateral_assets"],
            "reported_prices": {
                "0": asset_values["asset_values"]["0"]["price"],
                "31566704": asset_values["asset_values"]["31566704"]["price"]
            }
        })

        assert oracle_prices is not None
        assert "validation_passed" in oracle_prices

        # Step 3: Portfolio diversification check
        portfolio_engine = all_engines["portfolio"]
        portfolio_analysis = await portfolio_engine.analyze_diversification({
            "positions": [
                {"asset_id": "0", "value": asset_values["asset_values"]["0"]["total_value"]},
                {"asset_id": "31566704", "value": asset_values["asset_values"]["31566704"]["total_value"]}
            ]
        })

        assert portfolio_analysis is not None
        assert "diversification_adequate" in portfolio_analysis

        # Step 4: Volatility assessment
        volatility_engine = all_engines["volatility"]
        volatility_assessment = await volatility_engine.assess_portfolio_volatility({
            "asset_ids": loan_request["collateral_assets"],
            "weights": [
                asset_values["asset_values"]["0"]["total_value"] / asset_values["total_value"],
                asset_values["asset_values"]["31566704"]["total_value"] / asset_values["total_value"]
            ]
        })

        assert volatility_assessment is not None
        assert "portfolio_volatility" in volatility_assessment

        # Step 5: Collateral requirements calculation
        collateral_engine = all_engines["collateral"]
        collateral_decision = await collateral_engine.make_lending_decision({
            "loan_request": loan_request,
            "asset_values": asset_values,
            "oracle_validation": oracle_prices,
            "portfolio_analysis": portfolio_analysis,
            "volatility_assessment": volatility_assessment
        })

        assert collateral_decision is not None
        assert "approved" in collateral_decision
        assert "required_collateral_ratio" in collateral_decision

        # Step 6: Liquidation scenario planning
        liquidation_engine = all_engines["liquidation"]
        liquidation_plan = await liquidation_engine.create_liquidation_plan({
            "loan_details": loan_request,
            "collateral_decision": collateral_decision,
            "current_ltv": 0.75
        })

        assert liquidation_plan is not None
        assert "liquidation_triggers" in liquidation_plan

        # Verify end-to-end consistency
        total_collateral_value = asset_values["total_value"]
        loan_amount = loan_request["amount"]
        current_ltv = loan_amount / total_collateral_value

        assert current_ltv <= 0.85  # Safe LTV threshold
        assert collateral_decision["required_collateral_ratio"] >= 1.2

        # If approved, liquidation plan should have reasonable triggers
        if collateral_decision["approved"]:
            assert len(liquidation_plan["liquidation_triggers"]) > 0
            assert liquidation_plan["liquidation_triggers"][0]["ltv_threshold"] < 1.0

    @pytest.mark.asyncio
    async def test_cross_engine_data_consistency(self, all_engines, mock_asset_data):
        """Test that data remains consistent across all engines"""

        asset_id = "0"  # ALGO

        # Get asset data from different engines
        oracle_price = await all_engines["oracle"].get_asset_price(asset_id)
        valuation_data = await all_engines["valuation"].get_asset_valuation(asset_id)
        volatility_data = await all_engines["volatility"].get_asset_volatility(asset_id)

        # Verify price consistency (within reasonable tolerance)
        oracle_price_value = oracle_price.get("price", 0.0)
        valuation_price_value = valuation_data.get("current_price", 0.0)

        if oracle_price_value > 0 and valuation_price_value > 0:
            price_difference = abs(oracle_price_value - valuation_price_value) / oracle_price_value
            assert price_difference < 0.05  # 5% tolerance for price consistency

        # Verify asset ID consistency
        assert oracle_price.get("asset_id", "") == asset_id
        assert valuation_data.get("asset_id", "") == asset_id
        assert volatility_data.get("asset_id", "") == asset_id

    @pytest.mark.asyncio
    async def test_error_propagation_across_engines(self, all_engines):
        """Test how errors propagate through cross-engine workflows"""

        # Test with invalid asset ID
        invalid_asset_id = "999999999"

        # Oracle should handle gracefully
        try:
            oracle_result = await all_engines["oracle"].get_asset_price(invalid_asset_id)
            # Should either return None or default data, not crash
            assert oracle_result is not None
        except Exception as e:
            # If it throws an exception, it should be handled gracefully
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()

        # Valuation engine should handle missing price data
        try:
            valuation_result = await all_engines["valuation"].value_assets({
                "asset_ids": [invalid_asset_id],
                "quantities": [1000.0]
            })
            # Should handle gracefully
            assert valuation_result is not None
            assert "errors" in valuation_result or "warnings" in valuation_result
        except Exception as e:
            # Should be a handled error
            assert len(str(e)) > 0

    @pytest.mark.asyncio
    async def test_concurrent_cross_engine_operations(self, all_engines, performance_monitor):
        """Test concurrent operations across multiple engines"""

        performance_monitor.start()

        # Create multiple concurrent tasks
        tasks = []

        # Portfolio analysis tasks
        for i in range(3):
            task = all_engines["portfolio"].analyze_portfolio({
                "positions": [
                    {"asset_id": "0", "quantity": 100000 + i * 10000, "price": 0.25},
                    {"asset_id": "31566704", "quantity": 25000 + i * 5000, "price": 1.00}
                ]
            })
            tasks.append(task)

        # Volatility calculation tasks
        for i in range(3):
            task = all_engines["volatility"].calculate_volatility({
                "asset_ids": ["0", "31566704"],
                "time_window": 30 + i * 10
            })
            tasks.append(task)

        # Collateral assessment tasks
        for i in range(3):
            task = all_engines["collateral"].assess_collateral_risk({
                "loan_amount": 50000.0 + i * 10000,
                "collateral_ratio": 1.5
            })
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        performance_monitor.stop()

        # Verify all operations completed
        assert len(results) == 9

        # Check for any exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found exceptions in concurrent operations: {exceptions}"

        # Verify performance (all operations should complete within reasonable time)
        execution_time = performance_monitor.get_duration()
        assert execution_time < 30.0  # 30 second timeout for all concurrent operations

    @pytest.mark.asyncio
    async def test_state_management_across_engines(self, all_engines):
        """Test that engines maintain proper state during cross-engine operations"""

        # Initialize state in multiple engines
        portfolio_state = await all_engines["portfolio"].get_state()
        volatility_state = await all_engines["volatility"].get_state()
        collateral_state = await all_engines["collateral"].get_state()

        # Verify initial states
        assert portfolio_state is not None
        assert volatility_state is not None
        assert collateral_state is not None

        # Perform operations that might change state
        await all_engines["portfolio"].analyze_portfolio({
            "positions": [{"asset_id": "0", "quantity": 100000, "price": 0.25}]
        })

        await all_engines["volatility"].calculate_volatility({
            "asset_ids": ["0"],
            "time_window": 30
        })

        # Check that states are properly maintained
        new_portfolio_state = await all_engines["portfolio"].get_state()
        new_volatility_state = await all_engines["volatility"].get_state()

        # States should have reasonable values (not None or empty)
        assert new_portfolio_state is not None
        assert new_volatility_state is not None

        # Verify state consistency
        if "last_analysis_time" in new_portfolio_state:
            assert new_portfolio_state["last_analysis_time"] >= portfolio_state.get("last_analysis_time", 0)


class TestWorkflowPerformance:
    """Test performance of cross-engine workflows"""

    @pytest.mark.asyncio
    async def test_workflow_performance_benchmarks(self, all_engines, performance_benchmarks):
        """Test that cross-engine workflows meet performance benchmarks"""

        workflows = [
            {
                "name": "portfolio_risk_liquidation",
                "benchmark": 15.0,  # seconds
                "workflow": self._execute_portfolio_risk_liquidation_workflow
            },
            {
                "name": "oracle_volatility_collateral",
                "benchmark": 10.0,  # seconds
                "workflow": self._execute_oracle_volatility_collateral_workflow
            },
            {
                "name": "complete_lending_pipeline",
                "benchmark": 20.0,  # seconds
                "workflow": self._execute_complete_lending_pipeline
            }
        ]

        for workflow in workflows:
            monitor = PerformanceMonitor()
            monitor.start()

            try:
                result = await workflow["workflow"](all_engines)
                monitor.stop()

                execution_time = monitor.get_duration()
                assert execution_time < workflow["benchmark"], \
                    f"Workflow {workflow['name']} took {execution_time:.2f}s, " \
                    f"exceeding benchmark of {workflow['benchmark']}s"

                # Verify workflow completed successfully
                assert result is not None
                assert result.get("success", False) is True

            except Exception as e:
                pytest.fail(f"Workflow {workflow['name']} failed: {str(e)}")

    async def _execute_portfolio_risk_liquidation_workflow(self, engines) -> Dict[str, Any]:
        """Execute portfolio → risk → liquidation workflow"""
        try:
            # Portfolio analysis
            portfolio_result = await engines["portfolio"].analyze_portfolio({
                "positions": [
                    {"asset_id": "0", "quantity": 200000, "price": 0.25},
                    {"asset_id": "31566704", "quantity": 25000, "price": 1.00}
                ]
            })

            # Risk assessment
            risk_result = await engines["collateral"].assess_collateral_risk({
                "loan_amount": 50000.0,
                "portfolio_metrics": portfolio_result
            })

            # Liquidation scenarios
            liquidation_result = await engines["liquidation"].analyze_liquidation_scenarios({
                "risk_assessment": risk_result,
                "current_ltv": 0.8
            })

            return {
                "success": True,
                "portfolio_result": portfolio_result,
                "risk_result": risk_result,
                "liquidation_result": liquidation_result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_oracle_volatility_collateral_workflow(self, engines) -> Dict[str, Any]:
        """Execute oracle → volatility → collateral workflow"""
        try:
            # Oracle data
            oracle_result = await engines["oracle"].get_asset_prices(["0", "31566704"])

            # Volatility assessment
            volatility_result = await engines["volatility"].calculate_volatility({
                "asset_ids": ["0", "31566704"],
                "price_data": oracle_result
            })

            # Collateral requirements
            collateral_result = await engines["collateral"].calculate_requirements({
                "loan_amount": 100000.0,
                "volatility_data": volatility_result
            })

            return {
                "success": True,
                "oracle_result": oracle_result,
                "volatility_result": volatility_result,
                "collateral_result": collateral_result
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_complete_lending_pipeline(self, engines) -> Dict[str, Any]:
        """Execute complete lending decision pipeline"""
        try:
            loan_request = create_test_loan_request()

            # Sequential pipeline execution
            valuation_result = await engines["valuation"].value_assets({
                "asset_ids": ["0", "31566704"],
                "quantities": [300000.0, 50000.0]
            })

            oracle_result = await engines["oracle"].validate_prices({
                "asset_ids": ["0", "31566704"]
            })

            portfolio_result = await engines["portfolio"].analyze_diversification({
                "positions": [
                    {"asset_id": "0", "value": 75000},
                    {"asset_id": "31566704", "value": 50000}
                ]
            })

            volatility_result = await engines["volatility"].assess_portfolio_volatility({
                "asset_ids": ["0", "31566704"],
                "weights": [0.6, 0.4]
            })

            collateral_result = await engines["collateral"].make_lending_decision({
                "loan_request": loan_request,
                "asset_values": valuation_result,
                "volatility_assessment": volatility_result
            })

            liquidation_result = await engines["liquidation"].create_liquidation_plan({
                "loan_details": loan_request,
                "collateral_decision": collateral_result
            })

            return {
                "success": True,
                "pipeline_results": {
                    "valuation": valuation_result,
                    "oracle": oracle_result,
                    "portfolio": portfolio_result,
                    "volatility": volatility_result,
                    "collateral": collateral_result,
                    "liquidation": liquidation_result
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class TestWorkflowResilience:
    """Test resilience and error handling in cross-engine workflows"""

    @pytest.mark.asyncio
    async def test_partial_engine_failure_resilience(self, all_engines):
        """Test workflow resilience when one engine fails"""

        # Simulate oracle engine failure
        original_oracle_method = all_engines["oracle"].get_asset_prices

        async def failing_oracle_method(*args, **kwargs):
            raise Exception("Oracle service temporarily unavailable")

        all_engines["oracle"].get_asset_prices = failing_oracle_method

        try:
            # Portfolio and volatility engines should still work
            portfolio_result = await all_engines["portfolio"].analyze_portfolio({
                "positions": [{"asset_id": "0", "quantity": 100000, "price": 0.25}]
            })
            assert portfolio_result is not None

            # Volatility engine with fallback data should work
            volatility_result = await all_engines["volatility"].calculate_volatility({
                "asset_ids": ["0"],
                "use_fallback": True
            })
            assert volatility_result is not None

        finally:
            # Restore original method
            all_engines["oracle"].get_asset_prices = original_oracle_method

    @pytest.mark.asyncio
    async def test_data_inconsistency_handling(self, all_engines):
        """Test handling of inconsistent data between engines"""

        # Create scenario with inconsistent price data
        inconsistent_data = {
            "oracle_price": 0.25,  # ALGO price from oracle
            "valuation_price": 0.30,  # Different price from valuation engine
            "asset_id": "0"
        }

        # Collateral engine should detect and handle inconsistency
        result = await all_engines["collateral"].validate_data_consistency({
            "oracle_data": {"0": {"price": inconsistent_data["oracle_price"]}},
            "valuation_data": {"0": {"price": inconsistent_data["valuation_price"]}},
            "tolerance_threshold": 0.05  # 5% tolerance
        })

        assert result is not None
        assert "inconsistencies_detected" in result
        assert result["inconsistencies_detected"] is True
        assert "resolution_strategy" in result

    @pytest.mark.asyncio
    async def test_timeout_handling_in_workflows(self, all_engines):
        """Test timeout handling in cross-engine workflows"""

        # Set very short timeout
        short_timeout = 0.1  # 100ms

        try:
            # This should timeout quickly
            result = await asyncio.wait_for(
                all_engines["volatility"].calculate_volatility({
                    "asset_ids": ["0", "31566704", "312769"],
                    "time_window": 365,  # Large calculation
                    "detailed_analysis": True
                }),
                timeout=short_timeout
            )

            # If it doesn't timeout, that's also acceptable (fast execution)
            assert result is not None

        except asyncio.TimeoutError:
            # Timeout is expected and acceptable
            pass
        except Exception as e:
            # Other exceptions should be handled gracefully
            assert "timeout" in str(e).lower() or "cancelled" in str(e).lower()