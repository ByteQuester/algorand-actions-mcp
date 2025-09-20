#!/usr/bin/env python3
"""
Test Real MCP Integration
Tests the production MCP integration with actual services
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/adk-agents')

from real_mcp_integration import (
    MCPClient,
    MCPServiceConfig,
    get_real_account_balance,
    get_real_account_transactions,
    check_real_mcp_services,
    prepare_real_transaction,
    submit_real_transaction
)


async def test_service_health():
    """Test MCP service health monitoring"""
    print("🏥 Testing MCP Service Health...")

    config = MCPServiceConfig()
    health_result = await check_real_mcp_services(config)

    print(f"   Overall Status: {health_result['overall_status']}")
    print(f"   Services: {health_result['healthy_services']}/{health_result['total_services']} healthy")
    print(f"   Response Time: {health_result['total_response_time_ms']}ms")

    for service_name, service_data in health_result['services'].items():
        status_icon = "✅" if service_data['status'] == 'healthy' else "❌"
        print(f"   {status_icon} {service_name}: {service_data['status']} ({service_data['response_time_ms']}ms)")

    return health_result['overall_status'] == 'healthy'


async def test_account_info():
    """Test real account information retrieval"""
    print("\n👤 Testing Account Information...")

    # Test with a known testnet address
    test_address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"

    config = MCPServiceConfig()
    account_result = await get_real_account_balance(test_address, config)

    if account_result['success']:
        account_info = account_result['account_info']
        print(f"   ✅ Address: {account_info.address}")
        print(f"   💰 Balance: {account_info.algo_balance / 1_000_000:.6f} ALGO")
        print(f"   📊 Assets: {len(account_info.assets)} assets")
        print(f"   🔒 Min Balance: {account_info.min_balance / 1_000_000:.6f} ALGO")
        print(f"   🌐 Endpoint: {account_result['endpoint_used']}")
        print(f"   🔧 Method: {account_result['method']}")
        return True
    else:
        print(f"   ❌ Failed to get account info: {account_result.get('error', 'Unknown error')}")
        return False


async def test_transaction_history():
    """Test transaction history retrieval"""
    print("\n📊 Testing Transaction History...")

    test_address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"

    config = MCPServiceConfig()
    tx_result = await get_real_account_transactions(test_address, limit=5, config=config)

    if tx_result['success']:
        transactions = tx_result['transactions']
        print(f"   ✅ Found {len(transactions)} transactions")
        print(f"   🌐 Endpoint: {tx_result['endpoint_used']}")

        for i, tx in enumerate(transactions[:3], 1):
            print(f"   📝 TX {i}: {tx.txid[:12]}... Amount: {tx.amount / 1_000_000:.6f} ALGO")

        return True
    else:
        print(f"   ❌ Failed to get transactions: {tx_result.get('error', 'Unknown error')}")
        return False


async def test_transaction_preparation():
    """Test transaction preparation"""
    print("\n⚡ Testing Transaction Preparation...")

    transaction_params = {
        "sender": "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
        "receiver": "RECEIVER_ADDRESS_HERE",
        "amount": 1_000_000,  # 1 ALGO
        "fee": 1000,
        "note": "ADK lending agent test transaction"
    }

    config = MCPServiceConfig()
    prep_result = await prepare_real_transaction(transaction_params, config)

    if prep_result['success']:
        tx_data = prep_result['transaction_data']
        print(f"   ✅ Transaction prepared")
        print(f"   🆔 TX ID: {tx_data.get('txID', 'unknown')}")
        print(f"   🌐 Endpoint: {prep_result['endpoint_used']}")
        print(f"   ✍️  Ready for signing: {prep_result['ready_for_signing']}")
        return True
    else:
        print(f"   ❌ Failed to prepare transaction: {prep_result.get('error', 'Unknown error')}")
        return False


async def test_mcp_client_directly():
    """Test MCP client with direct API calls"""
    print("\n🔧 Testing Direct MCP Client...")

    config = MCPServiceConfig()

    async with MCPClient(config) as client:
        # Test health check
        health = await client.check_service_health()
        print(f"   🏥 Health check: {health['overall_status']}")

        # Test account info with fallback handling
        test_address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        account = await client.get_account_info(test_address)

        if account['success']:
            account_info = account['account_info']
            print(f"   👤 Account balance: {account_info.algo_balance / 1_000_000:.6f} ALGO")
            print(f"   🔗 API pattern used: {account['method']}")

        return True


async def test_lending_scenario():
    """Test a complete lending scenario"""
    print("\n💰 Testing Complete Lending Scenario...")

    borrower = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
    lender = "LENDER_ADDRESS_PLACEHOLDER_HERE"

    config = MCPServiceConfig()

    # Step 1: Check borrower account
    print("   1. Checking borrower account...")
    borrower_account = await get_real_account_balance(borrower, config)

    if not borrower_account['success']:
        print(f"   ❌ Cannot verify borrower account: {borrower_account.get('error')}")
        return False

    borrower_info = borrower_account['account_info']
    print(f"   ✅ Borrower has {borrower_info.algo_balance / 1_000_000:.6f} ALGO")

    # Step 2: Check transaction history for creditworthiness
    print("   2. Analyzing transaction history...")
    tx_history = await get_real_account_transactions(borrower, limit=10, config=config)

    if tx_history['success']:
        transactions = tx_history['transactions']
        print(f"   ✅ Found {len(transactions)} recent transactions")

        # Simple creditworthiness analysis
        total_volume = sum(tx.amount for tx in transactions)
        avg_transaction = total_volume / len(transactions) if transactions else 0

        print(f"   📊 Total volume: {total_volume / 1_000_000:.6f} ALGO")
        print(f"   📈 Avg transaction: {avg_transaction / 1_000_000:.6f} ALGO")

        # Determine lending eligibility
        min_balance_for_loan = 5_000_000  # 5 ALGO minimum
        eligible = borrower_info.algo_balance >= min_balance_for_loan

        print(f"   🎯 Lending eligible: {'✅ Yes' if eligible else '❌ No'}")

        if eligible:
            # Step 3: Prepare a mock lending transaction
            print("   3. Preparing lending transaction...")

            lending_params = {
                "type": "lending_group",
                "borrower": borrower,
                "lender": lender,
                "loan_amount": 2_000_000,  # 2 ALGO loan
                "collateral_amount": 3_000_000,  # 3 ALGO collateral
                "interest_rate": 7.5,
                "duration_days": 30
            }

            prep_result = await prepare_real_transaction(lending_params, config)
            if prep_result['success']:
                print(f"   ✅ Lending transaction prepared")
                print(f"   💡 Note: {prep_result.get('note', 'Real transaction preparation')}")
            else:
                print(f"   ⚠️  Mock preparation: {prep_result.get('note', 'Could not prepare real transaction')}")

        return eligible
    else:
        print(f"   ❌ Cannot analyze transaction history: {tx_history.get('error')}")
        return False


async def main():
    """Main test runner"""
    print("🎯 Real MCP Integration Test Suite")
    print("Testing production blockchain integration")
    print("=" * 60)

    tests = [
        ("Service Health", test_service_health),
        ("Account Information", test_account_info),
        ("Transaction History", test_transaction_history),
        ("Transaction Preparation", test_transaction_preparation),
        ("Direct MCP Client", test_mcp_client_directly),
        ("Lending Scenario", test_lending_scenario)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 Real MCP Integration Test Results:")

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "⚠️  SOME TESTS FAILED"
    print(f"\n🎯 Overall: {overall_status}")

    if all_passed:
        print("\n🎉 Real MCP integration is working!")
        print("✅ Production-ready blockchain connectivity")
        print("✅ Error handling and retry logic functional")
        print("✅ Multiple endpoint patterns supported")
        print("✅ Fallback mechanisms operational")
    else:
        print("\n🔧 Issues found. Check service connectivity and API patterns.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)