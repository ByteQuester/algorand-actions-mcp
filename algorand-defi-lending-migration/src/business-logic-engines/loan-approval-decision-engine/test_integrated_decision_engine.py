"""
Test script for Integrated Loan Decision Engine

Tests the integration of governance reputation and network risk monitoring
with the existing loan approval decision engine for holistic loan decisions.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from decision_engine import LoanDecisionEngine, LoanApplication, DecisionType
from governance_reputation.core.reputation_engine import ReputationEngine
from network_risk_monitoring.core.risk_engine import NetworkRiskEngine


class HolisticLoanDecisionEngine:
    """
    Enhanced loan decision engine that integrates governance reputation
    and network risk monitoring for comprehensive loan approval decisions.
    """

    def __init__(self):
        self.base_engine = LoanDecisionEngine()
        self.reputation_engine = ReputationEngine()
        self.risk_engine = NetworkRiskEngine()

    async def evaluate_holistic_application(self, application: LoanApplication, borrower_address: str):
        """
        Evaluate loan application with comprehensive governance reputation
        and network risk assessment.
        """
        try:
            print(f"🔍 Evaluating holistic loan application for {application.borrower_name}")
            print("=" * 70)

            # 1. Get base loan decision
            print("1️⃣ Base Financial Assessment...")
            base_decision = self.base_engine.evaluate_application(application)
            print(f"   Base Decision: {base_decision.decision.value.upper()}")
            print(f"   Base Risk Score: {base_decision.risk_score}")
            print(f"   Base Confidence: {base_decision.confidence_score:.1%}")

            # 2. Analyze governance reputation
            print("\n2️⃣ Governance Reputation Analysis...")
            reputation_analysis = await self.reputation_engine.analyze_comprehensive_reputation(borrower_address)
            print(f"   Reputation Score: {reputation_analysis.overall_reputation_score:.1f}")
            print(f"   Reputation Tier: {reputation_analysis.reputation_tier.value.upper()}")

            # 3. Assess network risk
            print("\n3️⃣ Network Risk Assessment...")
            risk_assessment = await self.risk_engine.assess_comprehensive_risk()
            print(f"   Network Risk Score: {risk_assessment.overall_risk_score:.1f}")
            print(f"   Risk Level: {risk_assessment.risk_level.value.upper()}")

            # 4. Apply holistic adjustments
            print("\n4️⃣ Applying Holistic Adjustments...")
            final_decision = self._integrate_assessments(
                base_decision, reputation_analysis, risk_assessment, application
            )

            return final_decision

        except Exception as e:
            print(f"❌ Error in holistic evaluation: {e}")
            raise

    def _integrate_assessments(self, base_decision, reputation_analysis, risk_assessment, application):
        """Integrate all assessments into final loan decision"""
        try:
            # Start with base decision
            final_risk_score = base_decision.risk_score
            final_confidence = base_decision.confidence_score
            final_amount = base_decision.suggested_amount
            final_collateral = base_decision.required_collateral
            final_conditions = list(base_decision.conditions)
            final_reasons = list(base_decision.reasons)

            # Apply reputation adjustments
            reputation_impact = reputation_analysis.loan_decision_impact

            if reputation_impact.auto_reject:
                final_decision = DecisionType.REJECTED
                final_reasons.append("Unacceptable governance reputation")
            else:
                # Adjust based on reputation
                if reputation_analysis.reputation_tier.value in ['excellent', 'good']:
                    final_risk_score = max(0, final_risk_score - 15)  # Reduce risk
                    final_confidence = min(1.0, final_confidence + 0.1)  # Increase confidence
                    final_reasons.append(f"Good governance reputation ({reputation_analysis.reputation_tier.value})")
                elif reputation_analysis.reputation_tier.value in ['poor', 'unacceptable']:
                    final_risk_score = min(100, final_risk_score + 20)  # Increase risk
                    final_confidence = max(0.3, final_confidence - 0.15)  # Decrease confidence
                    final_reasons.append(f"Poor governance reputation ({reputation_analysis.reputation_tier.value})")

                # Apply reputation-based LTV adjustment
                ltv_adjustment = reputation_impact.ltv_adjustment
                if ltv_adjustment != 0:
                    adjusted_collateral = final_collateral * (1 - ltv_adjustment)
                    final_collateral = max(final_collateral, adjusted_collateral)

                # Apply reputation-based conditions
                if reputation_impact.manual_review_required:
                    final_conditions.append("Manual review required due to reputation factors")

            # Apply network risk adjustments
            risk_adjustments = risk_assessment.risk_adjustments

            # Adjust based on network risk
            if risk_assessment.risk_level.value in ['high', 'very_high']:
                final_risk_score = min(100, final_risk_score + 10)  # Increase risk
                final_reasons.append(f"High network risk ({risk_assessment.risk_level.value})")

                # Apply risk-based LTV adjustment
                ltv_risk_adjustment = risk_adjustments.ltv_adjustment
                if ltv_risk_adjustment < 0:  # Negative adjustment means more collateral
                    risk_collateral = final_collateral * (1 - ltv_risk_adjustment)
                    final_collateral = max(final_collateral, risk_collateral)

                # Apply additional collateral requirement
                if risk_adjustments.additional_collateral_required > 0:
                    additional_collateral = application.amount * risk_adjustments.additional_collateral_required
                    final_collateral += additional_collateral
                    final_conditions.append(f"Additional {risk_adjustments.additional_collateral_required:.1%} collateral due to network risk")

            # Apply network risk conditions
            if risk_adjustments.manual_review_required:
                final_conditions.append("Manual review required due to network risk factors")

            # Make final decision
            if base_decision.decision == DecisionType.REJECTED:
                final_decision = DecisionType.REJECTED
            elif final_risk_score > 70:
                final_decision = DecisionType.REJECTED
                final_reasons.append("High combined risk score")
            elif final_risk_score > 50 or len([c for c in final_conditions if "manual review" in c.lower()]) > 0:
                final_decision = DecisionType.NEEDS_REVIEW
            else:
                final_decision = DecisionType.APPROVED

            # Create enhanced decision result
            from decision_engine import DecisionResult

            final_result = DecisionResult(
                decision=final_decision,
                confidence_score=final_confidence,
                risk_score=final_risk_score,
                required_collateral=final_collateral,
                suggested_amount=final_amount,
                reasons=final_reasons,
                conditions=final_conditions
            )

            # Add holistic context
            final_result.reputation_score = reputation_analysis.overall_reputation_score
            final_result.reputation_tier = reputation_analysis.reputation_tier.value
            final_result.network_risk_score = risk_assessment.overall_risk_score
            final_result.network_risk_level = risk_assessment.risk_level.value

            return final_result

        except Exception as e:
            print(f"❌ Error integrating assessments: {e}")
            raise


async def test_holistic_loan_decisions():
    """Test holistic loan decisions with different scenarios"""
    print("🏛️ Testing Holistic Loan Decision Engine")
    print("=" * 80)

    engine = HolisticLoanDecisionEngine()

    # Test scenarios
    scenarios = [
        {
            "name": "High-Quality Borrower",
            "application": LoanApplication(
                loan_id="LOAN_001",
                borrower_name="Alice Ecosystem Contributor",
                borrower_address="ALICE_ALGO_ADDRESS_123456789",
                amount=50000.0,
                duration_days=365,
                purpose="DeFi liquidity provision",
                credit_score=750,
                annual_income=120000.0,
                debt_to_income=0.25,
                collateral_value=75000.0,
                employment_years=5,
                previous_defaults=0
            )
        },
        {
            "name": "Average Borrower",
            "application": LoanApplication(
                loan_id="LOAN_002",
                borrower_name="Bob Average User",
                borrower_address="BOB_ALGO_ADDRESS_987654321",
                amount=25000.0,
                duration_days=180,
                purpose="Personal investment",
                credit_score=680,
                annual_income=75000.0,
                debt_to_income=0.35,
                collateral_value=30000.0,
                employment_years=3,
                previous_defaults=0
            )
        },
        {
            "name": "High-Risk Borrower",
            "application": LoanApplication(
                loan_id="LOAN_003",
                borrower_name="Charlie High Risk",
                borrower_address="CHARLIE_ALGO_ADDRESS_555555555",
                amount=100000.0,
                duration_days=730,
                purpose="Speculative trading",
                credit_score=580,
                annual_income=60000.0,
                debt_to_income=0.45,
                collateral_value=80000.0,
                employment_years=1,
                previous_defaults=2
            )
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📊 Scenario {i}: {scenario['name']}")
        print("=" * 60)

        try:
            decision = await engine.evaluate_holistic_application(
                scenario['application'],
                scenario['application'].borrower_address
            )

            # Display comprehensive results
            print(f"\n🎯 FINAL DECISION: {decision.decision.value.upper()}")
            print(f"📊 Combined Risk Score: {decision.risk_score}")
            print(f"🎯 Decision Confidence: {decision.confidence_score:.1%}")
            print(f"💰 Suggested Amount: ${decision.suggested_amount:,.0f}")
            print(f"🔒 Required Collateral: ${decision.required_collateral:,.0f}")

            if hasattr(decision, 'reputation_score'):
                print(f"🏛️ Governance Reputation: {decision.reputation_score:.1f} ({decision.reputation_tier})")
            if hasattr(decision, 'network_risk_score'):
                print(f"🌐 Network Risk: {decision.network_risk_score:.1f} ({decision.network_risk_level})")

            print("\n💡 Decision Factors:")
            for reason in decision.reasons:
                print(f"  • {reason}")

            if decision.conditions:
                print("\n📋 Approval Conditions:")
                for condition in decision.conditions:
                    print(f"  • {condition}")

            print("\n" + "="*60)

        except Exception as e:
            print(f"❌ Error in scenario {i}: {e}")

    print("\n✅ Holistic loan decision testing completed!")


if __name__ == "__main__":
    async def main():
        print("🌟 Algorand Holistic Loan Decision Engine Test Suite")
        print("=" * 80)
        print("Integrating governance reputation and network risk monitoring")
        print("for comprehensive, long-term focused loan approval decisions.")
        print("=" * 80)

        await test_holistic_loan_decisions()

        print("\n🎉 All holistic testing completed successfully!")
        print("=" * 80)

    # Run the async main function
    asyncio.run(main())