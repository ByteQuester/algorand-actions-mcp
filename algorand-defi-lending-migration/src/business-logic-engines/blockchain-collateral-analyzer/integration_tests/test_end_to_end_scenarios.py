"""
End-to-End Lending Scenarios Integration Tests

Tests complete lending scenarios from application to liquidation, covering multiple
borrower profiles, asset types, and market conditions to validate real-world usage.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
import random
from dataclasses import dataclass

from conftest import (
    TestConfig, create_test_loan_request, PerformanceMonitor,
    TestDataGenerator
)


@dataclass
class BorrowerProfile:
    """Borrower profile for testing scenarios"""
    borrower_id: str
    credit_score: int
    risk_level: str  # "low", "medium", "high"
    collateral_preference: List[str]  # Asset IDs
    loan_history: Dict[str, Any]
    max_loan_amount: float
    preferred_ltv: float


@dataclass
class LendingScenario:
    """Complete lending scenario definition"""
    scenario_id: str
    scenario_name: str
    borrower_profile: BorrowerProfile
    loan_amount: float
    collateral_assets: List[Dict[str, Any]]
    market_conditions: str  # "bull", "bear", "sideways", "volatile"
    expected_outcome: str  # "approved", "rejected", "conditional"
    stress_factors: List[str]
    timeline_days: int


class TestCompleteLendingScenarios:
    """Test complete lending scenarios from start to finish"""

    @pytest.fixture
    def borrower_profiles(self):
        """Generate test borrower profiles"""
        return {
            "conservative_investor": BorrowerProfile(
                borrower_id="borrower_001",
                credit_score=850,
                risk_level="low",
                collateral_preference=["0", "31566704"],  # ALGO, USDC
                loan_history={"total_loans": 5, "defaults": 0, "avg_ltv": 0.6},
                max_loan_amount=500000.0,
                preferred_ltv=0.65
            ),
            "growth_trader": BorrowerProfile(
                borrower_id="borrower_002",
                credit_score=720,
                risk_level="medium",
                collateral_preference=["0", "312769", "27165954"],  # ALGO, USDT, GOBTC
                loan_history={"total_loans": 12, "defaults": 1, "avg_ltv": 0.75},
                max_loan_amount=250000.0,
                preferred_ltv=0.80
            ),
            "high_risk_borrower": BorrowerProfile(
                borrower_id="borrower_003",
                credit_score=650,
                risk_level="high",
                collateral_preference=["0"],  # Only ALGO
                loan_history={"total_loans": 20, "defaults": 3, "avg_ltv": 0.85},
                max_loan_amount=100000.0,
                preferred_ltv=0.85
            ),
            "institutional_client": BorrowerProfile(
                borrower_id="borrower_004",
                credit_score=900,
                risk_level="low",
                collateral_preference=["0", "31566704", "312769"],
                loan_history={"total_loans": 100, "defaults": 0, "avg_ltv": 0.70},
                max_loan_amount=10000000.0,
                preferred_ltv=0.75
            ),
            "defi_native": BorrowerProfile(
                borrower_id="borrower_005",
                credit_score=750,
                risk_level="medium",
                collateral_preference=["0", "386192725"],  # ALGO, GOETH
                loan_history={"total_loans": 30, "defaults": 2, "avg_ltv": 0.78},
                max_loan_amount=750000.0,
                preferred_ltv=0.82
            )
        }

    @pytest.fixture
    def lending_scenarios(self, borrower_profiles):
        """Generate comprehensive lending scenarios"""
        return [
            LendingScenario(
                scenario_id="scenario_001",
                scenario_name="Conservative High-Value Loan",
                borrower_profile=borrower_profiles["conservative_investor"],
                loan_amount=300000.0,
                collateral_assets=[
                    {"asset_id": "0", "quantity": 1500000.0, "price": 0.25},  # $375k ALGO
                    {"asset_id": "31566704", "quantity": 100000.0, "price": 1.00}  # $100k USDC
                ],
                market_conditions="stable",
                expected_outcome="approved",
                stress_factors=[],
                timeline_days=30
            ),
            LendingScenario(
                scenario_id="scenario_002",
                scenario_name="Growth Trader Leveraged Position",
                borrower_profile=borrower_profiles["growth_trader"],
                loan_amount=150000.0,
                collateral_assets=[
                    {"asset_id": "0", "quantity": 800000.0, "price": 0.25},  # $200k ALGO
                ],
                market_conditions="bull",
                expected_outcome="approved",
                stress_factors=["high_volatility"],
                timeline_days=14
            ),
            LendingScenario(
                scenario_id="scenario_003",
                scenario_name="High-Risk Borrower Edge Case",
                borrower_profile=borrower_profiles["high_risk_borrower"],
                loan_amount=75000.0,
                collateral_assets=[
                    {"asset_id": "0", "quantity": 400000.0, "price": 0.25},  # $100k ALGO
                ],
                market_conditions="volatile",
                expected_outcome="conditional",
                stress_factors=["credit_history", "single_asset", "high_volatility"],
                timeline_days=7
            ),
            LendingScenario(
                scenario_id="scenario_004",
                scenario_name="Institutional Large Loan",
                borrower_profile=borrower_profiles["institutional_client"],
                loan_amount=5000000.0,
                collateral_assets=[
                    {"asset_id": "0", "quantity": 20000000.0, "price": 0.25},  # $5M ALGO
                    {"asset_id": "31566704", "quantity": 2000000.0, "price": 1.00},  # $2M USDC
                    {"asset_id": "312769", "quantity": 500000.0, "price": 1.00}  # $500k USDT
                ],
                market_conditions="stable",
                expected_outcome="approved",
                stress_factors=["large_amount"],
                timeline_days=45
            ),
            LendingScenario(
                scenario_id="scenario_005",
                scenario_name="DeFi Native Bear Market",
                borrower_profile=borrower_profiles["defi_native"],
                loan_amount=200000.0,
                collateral_assets=[
                    {"asset_id": "0", "quantity": 1200000.0, "price": 0.20},  # $240k ALGO (bear price)
                    {"asset_id": "386192725", "quantity": 50.0, "price": 2000.0}  # $100k GOETH
                ],
                market_conditions="bear",
                expected_outcome="conditional",
                stress_factors=["bear_market", "price_decline", "mixed_assets"],
                timeline_days=21
            )
        ]

    @pytest.mark.asyncio
    async def test_conservative_high_value_loan_scenario(self, all_engines, lending_scenarios):
        """Test conservative borrower with high-value loan scenario"""

        scenario = next(s for s in lending_scenarios if s.scenario_id == "scenario_001")

        # Step 1: Initial loan application
        loan_application = {
            "borrower_id": scenario.borrower_profile.borrower_id,
            "loan_amount": scenario.loan_amount,
            "requested_term_days": scenario.timeline_days,
            "collateral_assets": scenario.collateral_assets,
            "borrower_profile": {
                "credit_score": scenario.borrower_profile.credit_score,
                "risk_level": scenario.borrower_profile.risk_level,
                "loan_history": scenario.borrower_profile.loan_history
            }
        }

        # Step 2: Asset valuation
        valuation_engine = all_engines["valuation"]
        asset_valuations = await valuation_engine.value_portfolio({
            "assets": scenario.collateral_assets,
            "valuation_method": "comprehensive",
            "include_volatility": True
        })

        assert asset_valuations is not None
        assert "total_value" in asset_valuations
        assert asset_valuations["total_value"] > scenario.loan_amount  # Basic sanity check

        # Step 3: Portfolio diversification analysis
        portfolio_engine = all_engines["portfolio"]
        diversification_analysis = await portfolio_engine.analyze_diversification({
            "positions": scenario.collateral_assets,
            "target_diversification": 0.7,  # Conservative target
            "borrower_profile": scenario.borrower_profile.risk_level
        })

        assert diversification_analysis is not None
        assert "diversification_score" in diversification_analysis

        # Step 4: Risk assessment
        collateral_engine = all_engines["collateral"]
        risk_assessment = await collateral_engine.comprehensive_risk_analysis({
            "loan_application": loan_application,
            "asset_valuations": asset_valuations,
            "diversification_analysis": diversification_analysis,
            "market_conditions": scenario.market_conditions
        })

        assert risk_assessment is not None
        assert "overall_risk_level" in risk_assessment
        assert "recommended_ltv" in risk_assessment

        # Step 5: Lending decision
        lending_decision = await collateral_engine.make_lending_decision({
            "loan_application": loan_application,
            "risk_assessment": risk_assessment,
            "institutional_limits": {"max_single_loan": 1000000.0}
        })

        assert lending_decision is not None
        assert "decision" in lending_decision

        # Verify expected outcome for conservative scenario
        assert lending_decision["decision"] == "approved", \
            f"Conservative scenario should be approved, got: {lending_decision['decision']}"

        # Step 6: Liquidation planning
        liquidation_engine = all_engines["liquidation"]
        liquidation_plan = await liquidation_engine.create_comprehensive_plan({
            "loan_details": loan_application,
            "approved_terms": lending_decision,
            "monitoring_frequency": "daily"
        })

        assert liquidation_plan is not None
        assert "liquidation_triggers" in liquidation_plan
        assert len(liquidation_plan["liquidation_triggers"]) > 0

        # Verify conservative liquidation thresholds
        primary_trigger = liquidation_plan["liquidation_triggers"][0]
        assert primary_trigger["ltv_threshold"] < 0.85  # Conservative threshold

    @pytest.mark.asyncio
    async def test_high_risk_edge_case_scenario(self, all_engines, lending_scenarios):
        """Test high-risk borrower edge case scenario"""

        scenario = next(s for s in lending_scenarios if s.scenario_id == "scenario_003")

        # Enhanced risk assessment for high-risk borrower
        loan_application = {
            "borrower_id": scenario.borrower_profile.borrower_id,
            "loan_amount": scenario.loan_amount,
            "collateral_assets": scenario.collateral_assets,
            "borrower_profile": {
                "credit_score": scenario.borrower_profile.credit_score,
                "risk_level": scenario.borrower_profile.risk_level,
                "loan_history": scenario.borrower_profile.loan_history,
                "stress_factors": scenario.stress_factors
            }
        }

        # Enhanced volatility assessment due to single asset concentration
        volatility_engine = all_engines["volatility"]
        volatility_assessment = await volatility_engine.assess_concentration_risk({
            "assets": scenario.collateral_assets,
            "concentration_threshold": 0.8,  # 80% in single asset
            "market_conditions": scenario.market_conditions
        })

        assert volatility_assessment is not None
        assert "concentration_risk" in volatility_assessment

        # Risk assessment with stress factors
        collateral_engine = all_engines["collateral"]
        enhanced_risk_assessment = await collateral_engine.stress_test_analysis({
            "loan_application": loan_application,
            "volatility_assessment": volatility_assessment,
            "stress_scenarios": ["30_percent_drop", "liquidity_crisis", "correlation_spike"]
        })

        assert enhanced_risk_assessment is not None
        assert "stress_test_results" in enhanced_risk_assessment

        # Lending decision should be conditional or rejected
        lending_decision = await collateral_engine.make_lending_decision({
            "loan_application": loan_application,
            "risk_assessment": enhanced_risk_assessment,
            "risk_tolerance": "conservative"
        })

        assert lending_decision is not None
        assert lending_decision["decision"] in ["conditional", "rejected"], \
            f"High-risk scenario should be conditional/rejected, got: {lending_decision['decision']}"

        # If conditional, verify additional requirements
        if lending_decision["decision"] == "conditional":
            assert "additional_requirements" in lending_decision
            assert len(lending_decision["additional_requirements"]) > 0

    @pytest.mark.asyncio
    async def test_institutional_large_loan_scenario(self, all_engines, lending_scenarios):
        """Test institutional client large loan scenario"""

        scenario = next(s for s in lending_scenarios if s.scenario_id == "scenario_004")

        # Institutional-grade analysis
        loan_application = {
            "borrower_id": scenario.borrower_profile.borrower_id,
            "loan_amount": scenario.loan_amount,
            "collateral_assets": scenario.collateral_assets,
            "borrower_type": "institutional",
            "regulatory_requirements": ["aml_check", "kyc_enhanced", "large_exposure_reporting"]
        }

        # Enhanced due diligence for large amounts
        portfolio_engine = all_engines["portfolio"]
        institutional_analysis = await portfolio_engine.institutional_portfolio_analysis({
            "portfolio": scenario.collateral_assets,
            "size_category": "large",
            "diversification_requirements": "institutional_grade",
            "liquidity_requirements": "high"
        })

        assert institutional_analysis is not None
        assert "institutional_grade" in institutional_analysis

        # Large exposure risk assessment
        collateral_engine = all_engines["collateral"]
        large_exposure_assessment = await collateral_engine.large_exposure_analysis({
            "loan_application": loan_application,
            "portfolio_analysis": institutional_analysis,
            "regulatory_limits": {"max_single_exposure": 10000000.0},
            "capital_adequacy_check": True
        })

        assert large_exposure_assessment is not None
        assert "exposure_within_limits" in large_exposure_assessment

        # Decision should account for institutional status
        institutional_decision = await collateral_engine.institutional_lending_decision({
            "loan_application": loan_application,
            "large_exposure_assessment": large_exposure_assessment,
            "board_approval_required": scenario.loan_amount > 1000000.0
        })

        assert institutional_decision is not None
        # Institutional client should generally be approved due to low risk
        assert institutional_decision["decision"] == "approved"

        # Verify institutional-specific terms
        assert "institutional_terms" in institutional_decision
        assert "reporting_requirements" in institutional_decision

    @pytest.mark.asyncio
    async def test_bear_market_stress_scenario(self, all_engines, lending_scenarios, mock_market_conditions):
        """Test lending scenario during bear market conditions"""

        scenario = next(s for s in lending_scenarios if s.scenario_id == "scenario_005")
        bear_market_conditions = mock_market_conditions["bear_market"]

        # Simulate bear market pricing
        adjusted_collateral = []
        for asset in scenario.collateral_assets:
            adjusted_price = asset["price"] * bear_market_conditions["volatility_multiplier"]
            adjusted_collateral.append({
                **asset,
                "current_price": adjusted_price,
                "market_conditions": "bear"
            })

        loan_application = {
            "borrower_id": scenario.borrower_profile.borrower_id,
            "loan_amount": scenario.loan_amount,
            "collateral_assets": adjusted_collateral,
            "market_environment": "bear_market"
        }

        # Enhanced volatility assessment for bear market
        volatility_engine = all_engines["volatility"]
        bear_market_volatility = await volatility_engine.bear_market_analysis({
            "assets": adjusted_collateral,
            "market_stress": "high",
            "correlation_adjustment": "increased",
            "liquidity_adjustment": bear_market_conditions["liquidity_multiplier"]
        })

        assert bear_market_volatility is not None
        assert "adjusted_volatility" in bear_market_volatility

        # Stress-adjusted risk assessment
        collateral_engine = all_engines["collateral"]
        bear_market_risk = await collateral_engine.bear_market_risk_assessment({
            "loan_application": loan_application,
            "volatility_assessment": bear_market_volatility,
            "market_stress_level": "severe",
            "additional_margin": 0.2  # 20% additional margin for bear market
        })

        assert bear_market_risk is not None
        assert "stress_adjusted_risk" in bear_market_risk

        # Decision should be more conservative in bear market
        bear_market_decision = await collateral_engine.make_lending_decision({
            "loan_application": loan_application,
            "risk_assessment": bear_market_risk,
            "market_conditions": "bear",
            "conservative_bias": True
        })

        assert bear_market_decision is not None
        # Bear market scenario should be conditional due to elevated risk
        assert bear_market_decision["decision"] in ["conditional", "approved"]

        # If approved, should have conservative terms
        if bear_market_decision["decision"] == "approved":
            assert bear_market_decision.get("required_ltv", 1.0) < 0.75  # Conservative LTV


class TestScenarioStressTesting:
    """Test lending scenarios under various stress conditions"""

    @pytest.mark.asyncio
    async def test_market_crash_scenario(self, all_engines, borrower_profiles, mock_market_conditions):
        """Test lending system behavior during market crash"""

        crash_conditions = mock_market_conditions["crash_scenario"]
        borrower = borrower_profiles["growth_trader"]

        # Simulate market crash - 50% price drop
        crashed_collateral = [
            {
                "asset_id": "0",
                "quantity": 1000000.0,
                "original_price": 0.25,
                "crashed_price": 0.125,  # 50% drop
                "market_condition": "crash"
            }
        ]

        loan_application = {
            "borrower_id": borrower.borrower_id,
            "loan_amount": 100000.0,
            "collateral_assets": crashed_collateral,
            "market_environment": "crash"
        }

        # Emergency risk assessment
        collateral_engine = all_engines["collateral"]
        crash_risk_assessment = await collateral_engine.emergency_risk_assessment({
            "loan_application": loan_application,
            "market_crash_severity": "severe",
            "immediate_liquidation_risk": True
        })

        assert crash_risk_assessment is not None
        assert "emergency_measures" in crash_risk_assessment

        # Liquidation engine should trigger immediate response
        liquidation_engine = all_engines["liquidation"]
        emergency_liquidation = await liquidation_engine.emergency_liquidation_assessment({
            "loan_details": loan_application,
            "crash_assessment": crash_risk_assessment,
            "immediate_action_required": True
        })

        assert emergency_liquidation is not None
        assert "immediate_liquidation_required" in emergency_liquidation

        # Verify appropriate emergency response
        if emergency_liquidation["immediate_liquidation_required"]:
            assert "liquidation_strategy" in emergency_liquidation
            assert "priority_level" in emergency_liquidation

    @pytest.mark.asyncio
    async def test_liquidity_crisis_scenario(self, all_engines, lending_scenarios):
        """Test scenario during liquidity crisis"""

        scenario = lending_scenarios[1]  # Growth trader scenario

        # Simulate liquidity crisis
        liquidity_stressed_assets = []
        for asset in scenario.collateral_assets:
            liquidity_stressed_assets.append({
                **asset,
                "liquidity_score": 0.3,  # Very low liquidity
                "bid_ask_spread": 0.05,  # 5% spread
                "market_depth": 10000.0,  # Very shallow
                "liquidity_crisis": True
            })

        # Portfolio analysis under liquidity stress
        portfolio_engine = all_engines["portfolio"]
        liquidity_analysis = await portfolio_engine.liquidity_stress_analysis({
            "assets": liquidity_stressed_assets,
            "stress_level": "severe",
            "time_to_liquidate": "immediate"
        })

        assert liquidity_analysis is not None
        assert "liquidity_stress_impact" in liquidity_analysis

        # Adjusted lending decision
        collateral_engine = all_engines["collateral"]
        liquidity_adjusted_decision = await collateral_engine.liquidity_adjusted_decision({
            "loan_application": {
                "loan_amount": scenario.loan_amount,
                "collateral_assets": liquidity_stressed_assets
            },
            "liquidity_analysis": liquidity_analysis,
            "stress_scenario": "liquidity_crisis"
        })

        assert liquidity_adjusted_decision is not None
        # Should be rejected or require significantly higher collateral
        assert liquidity_adjusted_decision["decision"] in ["rejected", "conditional"]

    @pytest.mark.asyncio
    async def test_correlation_spike_scenario(self, all_engines):
        """Test scenario where asset correlations spike during stress"""

        # Multi-asset portfolio that normally has low correlation
        diversified_portfolio = [
            {"asset_id": "0", "quantity": 400000.0, "price": 0.25},      # ALGO
            {"asset_id": "31566704", "quantity": 50000.0, "price": 1.00}, # USDC
            {"asset_id": "312769", "quantity": 25000.0, "price": 1.00}    # USDT
        ]

        # Simulate correlation spike (all assets move together)
        correlation_matrix = {
            ("0", "31566704"): 0.85,     # Usually low, now high
            ("0", "312769"): 0.80,       # Usually low, now high
            ("31566704", "312769"): 0.95 # Usually high, remains high
        }

        # Portfolio analysis with correlation spike
        portfolio_engine = all_engines["portfolio"]
        correlation_analysis = await portfolio_engine.correlation_stress_analysis({
            "portfolio": diversified_portfolio,
            "stress_correlations": correlation_matrix,
            "stress_scenario": "correlation_spike"
        })

        assert correlation_analysis is not None
        assert "effective_diversification" in correlation_analysis

        # Verify diversification benefit is reduced
        assert correlation_analysis["effective_diversification"] < 0.5

        # Risk assessment should account for reduced diversification
        collateral_engine = all_engines["collateral"]
        correlation_adjusted_risk = await collateral_engine.correlation_adjusted_assessment({
            "portfolio": diversified_portfolio,
            "correlation_analysis": correlation_analysis,
            "loan_amount": 100000.0
        })

        assert correlation_adjusted_risk is not None
        assert "correlation_adjusted_risk_level" in correlation_adjusted_risk


class TestScenarioMonitoring:
    """Test ongoing monitoring of lending scenarios"""

    @pytest.mark.asyncio
    async def test_ongoing_loan_monitoring(self, all_engines, lending_scenarios):
        """Test continuous monitoring of an active loan"""

        scenario = lending_scenarios[0]  # Conservative scenario

        # Simulate approved loan
        active_loan = {
            "loan_id": f"loan_{scenario.scenario_id}_{int(time.time())}",
            "borrower_id": scenario.borrower_profile.borrower_id,
            "original_loan_amount": scenario.loan_amount,
            "current_balance": scenario.loan_amount * 0.8,  # 80% remaining
            "collateral_assets": scenario.collateral_assets,
            "start_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "maturity_date": (datetime.now() + timedelta(days=20)).isoformat()
        }

        # Daily monitoring check
        monitoring_results = {}

        # Oracle price updates
        oracle_engine = all_engines["oracle"]
        current_prices = await oracle_engine.get_current_prices([
            asset["asset_id"] for asset in scenario.collateral_assets
        ])

        monitoring_results["price_update"] = current_prices

        # Portfolio value monitoring
        portfolio_engine = all_engines["portfolio"]
        current_portfolio_value = await portfolio_engine.calculate_current_value({
            "positions": scenario.collateral_assets,
            "current_prices": current_prices
        })

        monitoring_results["portfolio_value"] = current_portfolio_value

        # Risk level monitoring
        collateral_engine = all_engines["collateral"]
        current_risk_assessment = await collateral_engine.monitor_loan_risk({
            "active_loan": active_loan,
            "current_portfolio_value": current_portfolio_value,
            "market_conditions": "stable"
        })

        monitoring_results["risk_assessment"] = current_risk_assessment

        # Liquidation trigger check
        liquidation_engine = all_engines["liquidation"]
        liquidation_check = await liquidation_engine.check_liquidation_triggers({
            "active_loan": active_loan,
            "current_risk": current_risk_assessment,
            "monitoring_frequency": "daily"
        })

        monitoring_results["liquidation_check"] = liquidation_check

        # Verify monitoring results
        assert all(result is not None for result in monitoring_results.values())
        assert "current_ltv" in current_risk_assessment
        assert "liquidation_required" in liquidation_check

    @pytest.mark.asyncio
    async def test_early_warning_system(self, all_engines):
        """Test early warning system for deteriorating loans"""

        # Simulate loan approaching danger zone
        deteriorating_loan = {
            "loan_id": "loan_deteriorating_001",
            "current_ltv": 0.78,  # Approaching 80% threshold
            "trend": "increasing",
            "collateral_assets": [
                {"asset_id": "0", "quantity": 300000.0, "price": 0.22}  # Price declining
            ]
        }

        # Early warning analysis
        collateral_engine = all_engines["collateral"]
        early_warning = await collateral_engine.early_warning_analysis({
            "loan": deteriorating_loan,
            "warning_thresholds": {
                "ltv_warning": 0.75,
                "ltv_critical": 0.85,
                "price_decline_warning": 0.15
            }
        })

        assert early_warning is not None
        assert "warning_level" in early_warning
        assert early_warning["warning_level"] in ["yellow", "orange", "red"]

        # Verify appropriate warnings are triggered
        if early_warning["warning_level"] in ["orange", "red"]:
            assert "recommended_actions" in early_warning
            assert len(early_warning["recommended_actions"]) > 0

    @pytest.mark.asyncio
    async def test_scenario_performance_tracking(self, all_engines, lending_scenarios, performance_monitor):
        """Test performance tracking across multiple scenarios"""

        performance_monitor.start()

        scenario_performances = {}

        for scenario in lending_scenarios[:3]:  # Test first 3 scenarios
            scenario_start_time = time.time()

            try:
                # Run abbreviated scenario
                loan_request = {
                    "borrower_id": scenario.borrower_profile.borrower_id,
                    "loan_amount": scenario.loan_amount,
                    "collateral_assets": scenario.collateral_assets
                }

                # Quick risk assessment
                collateral_engine = all_engines["collateral"]
                risk_result = await collateral_engine.quick_risk_assessment(loan_request)

                scenario_end_time = time.time()
                scenario_duration = scenario_end_time - scenario_start_time

                scenario_performances[scenario.scenario_id] = {
                    "duration": scenario_duration,
                    "success": True,
                    "risk_level": risk_result.get("risk_level", "unknown")
                }

            except Exception as e:
                scenario_end_time = time.time()
                scenario_duration = scenario_end_time - scenario_start_time

                scenario_performances[scenario.scenario_id] = {
                    "duration": scenario_duration,
                    "success": False,
                    "error": str(e)
                }

        performance_monitor.stop()

        # Verify performance across scenarios
        total_duration = performance_monitor.get_duration()
        assert total_duration < 30.0  # All scenarios should complete within 30 seconds

        # Verify individual scenario performance
        for scenario_id, performance in scenario_performances.items():
            assert performance["duration"] < 10.0, \
                f"Scenario {scenario_id} took too long: {performance['duration']:.2f}s"

        # Verify success rate
        successful_scenarios = sum(1 for p in scenario_performances.values() if p["success"])
        success_rate = successful_scenarios / len(scenario_performances)
        assert success_rate >= 0.8, f"Scenario success rate too low: {success_rate:.2%}"