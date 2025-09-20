#!/usr/bin/env python3
"""
End-to-End Lending Test with Real MCP Integration
Tests the full lending workflow with true blockchain connectivity
"""

import asyncio
import json
import sys
import os

# Add necessary directories to Python path
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/adk-agents')
sys.path.insert(0, '/home/mpo/algorand-showcase/packages/lending-core')

from real_mcp_integration_v2 import get_real_account_info, get_real_account_transactions, MCPServiceConfig


async def test_lending_workflow_with_real_mcp():
    """Test a complete lending workflow using real MCP blockchain data"""
    print("🏦 Testing Lending Workflow with Real MCP Integration")
    print("=" * 60)

    # Test wallet addresses (from test-wallets.json)
    lender_address = "MYZFY5XANQ3HN2YCS2XNOQIWL5PANXL35EV3YKBN5R5A6Y4TT43ZU3WZYM"
    borrower_address = "CRMMBMPQ7VZISVJCHBCR2T4OUZ5634FXP6BX3BLOBVXB6ZK44IF6CGMLPI"
    liquidity_address = "DCZRXVVPPAKVGNFHUGMTQWJHCIROOVQPHHIRM562I2WYPWXVNKISCK2DK4"

    config = MCPServiceConfig(
        reader_endpoint="http://localhost:8002",
        writer_endpoint="http://localhost:3001",
        timeout=15
    )

    results = {
        "workflow_start": "2025-09-14T21:52:17Z",
        "participants": {
            "lender": lender_address,
            "borrower": borrower_address,
            "liquidity_provider": liquidity_address
        },
        "steps": {}
    }

    try:
        # Step 1: Get Real Account Information for Risk Assessment
        print("📊 Step 1: Gathering Real Account Information...")

        lender_info = await get_real_account_info(lender_address, config)
        borrower_info = await get_real_account_info(borrower_address, config)
        liquidity_info = await get_real_account_info(liquidity_address, config)

        results["steps"]["account_verification"] = {
            "lender_balance_algo": lender_info.get("balance_algos", 0),
            "borrower_balance_algo": borrower_info.get("balance_algos", 0),
            "liquidity_balance_algo": liquidity_info.get("balance_algos", 0),
            "real_data_used": all([
                info.get("real_blockchain_data", False)
                for info in [lender_info, borrower_info, liquidity_info]
            ]),
            "status": "SUCCESS"
        }

        print(f"  ✅ Lender Balance: {lender_info.get('balance_algos', 0)} ALGO")
        print(f"  ✅ Borrower Balance: {borrower_info.get('balance_algos', 0)} ALGO")
        print(f"  ✅ Liquidity Provider Balance: {liquidity_info.get('balance_algos', 0)} ALGO")

        # Step 2: Transaction History Analysis for Credit Assessment
        print("📈 Step 2: Analyzing Real Transaction History...")

        lender_txns = await get_real_account_transactions(lender_address, limit=5, config=config)
        borrower_txns = await get_real_account_transactions(borrower_address, limit=5, config=config)

        results["steps"]["credit_analysis"] = {
            "lender_transaction_count": lender_txns.get("count", 0),
            "borrower_transaction_count": borrower_txns.get("count", 0),
            "real_data_used": all([
                txns.get("real_blockchain_data", False)
                for txns in [lender_txns, borrower_txns]
            ]),
            "credit_score_factors": {
                "lender_activity": lender_txns.get("count", 0) > 0,
                "borrower_activity": borrower_txns.get("count", 0) > 0,
                "sufficient_balances": all([
                    info.get("balance_algos", 0) >= 5.0
                    for info in [lender_info, borrower_info]
                ])
            },
            "status": "SUCCESS"
        }

        print(f"  ✅ Lender Transaction History: {lender_txns.get('count', 0)} transactions")
        print(f"  ✅ Borrower Transaction History: {borrower_txns.get('count', 0)} transactions")

        # Step 3: AI-Powered Risk Assessment with Real Data
        print("🤖 Step 3: AI Risk Assessment with Real Blockchain Data...")

        total_liquidity = sum([
            lender_info.get("balance_algos", 0),
            liquidity_info.get("balance_algos", 0)
        ])

        loan_amount_algo = 5.0  # 5 ALGO loan request
        collateral_ratio = borrower_info.get("balance_algos", 0) / loan_amount_algo if loan_amount_algo > 0 else 0

        # Simulate AI risk assessment based on real data
        risk_factors = {
            "collateral_ratio": collateral_ratio,
            "borrower_balance_sufficient": borrower_info.get("balance_algos", 0) >= 5.0,
            "lender_liquidity_available": lender_info.get("balance_algos", 0) >= loan_amount_algo,
            "transaction_history_positive": all([
                txns.get("count", 0) > 0 for txns in [lender_txns, borrower_txns]
            ])
        }

        risk_score = sum([
            0.3 if risk_factors["collateral_ratio"] >= 2.0 else 0.1,
            0.2 if risk_factors["borrower_balance_sufficient"] else 0.0,
            0.3 if risk_factors["lender_liquidity_available"] else 0.0,
            0.2 if risk_factors["transaction_history_positive"] else 0.1
        ]) * 10  # Scale to 0-10

        loan_approved = risk_score >= 7.0
        interest_rate = max(5.0, 15.0 - risk_score)

        results["steps"]["ai_risk_assessment"] = {
            "risk_score": round(risk_score, 2),
            "risk_factors": risk_factors,
            "loan_approved": loan_approved,
            "recommended_interest_rate": round(interest_rate, 2),
            "loan_amount_algo": loan_amount_algo,
            "collateral_ratio": round(collateral_ratio, 2),
            "real_data_based": True,
            "status": "SUCCESS"
        }

        print(f"  🎯 Risk Score: {risk_score:.1f}/10.0")
        print(f"  {'✅' if loan_approved else '❌'} Loan Decision: {'APPROVED' if loan_approved else 'REJECTED'}")
        print(f"  💰 Recommended Rate: {interest_rate:.1f}%")
        print(f"  🔒 Collateral Ratio: {collateral_ratio:.1f}x")

        # Final Assessment
        all_real_data = all([
            results["steps"]["account_verification"]["real_data_used"],
            results["steps"]["credit_analysis"]["real_data_used"],
            results["steps"]["ai_risk_assessment"]["real_data_based"]
        ])

        results["workflow_success"] = loan_approved and all_real_data
        results["real_blockchain_integration"] = all_real_data
        results["fallback_mechanisms_used"] = not all_real_data

        print(f"\n🎉 LENDING WORKFLOW RESULTS:")
        print(f"   Workflow Success: {'✅' if results['workflow_success'] else '❌'}")
        print(f"   Real Blockchain Data: {'✅' if all_real_data else '❌'}")
        print(f"   Fallback Mechanisms: {'❌ None Used' if not results['fallback_mechanisms_used'] else '⚠️ Some Used'}")
        print(f"   MCP Integration: {'🟢 COMPLETE' if all_real_data else '🟡 PARTIAL'}")

        # Save results
        with open('/home/mpo/algorand-showcase/lending_workflow_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: lending_workflow_results.json")

        return results["workflow_success"] and all_real_data

    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED: {str(e)}")
        results["error"] = str(e)
        results["workflow_success"] = False
        return False


if __name__ == "__main__":
    success = asyncio.run(test_lending_workflow_with_real_mcp())
    print(f"\n{'🎊 MISSION ACCOMPLISHED' if success else '⚠️ NEEDS ATTENTION'}")
    sys.exit(0 if success else 1)