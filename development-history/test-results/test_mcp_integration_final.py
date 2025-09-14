#!/usr/bin/env python3
"""
Final MCP Integration Test - Agent 10 Completion
Tests the corrected MCP protocol integration with real blockchain connectivity
"""

import asyncio
import json
import sys
import os

# Add the adk-agents directory to Python path
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/adk-agents')

from real_mcp_integration_v2 import test_full_mcp_integration, MCPServiceConfig


async def main():
    """Run comprehensive MCP integration test"""
    print("🚀 Starting Final MCP Integration Test - Agent 10")
    print("=" * 60)

    # Test with testnet configuration
    config = MCPServiceConfig(
        reader_endpoint="http://localhost:8002",
        writer_endpoint="http://localhost:3001",
        timeout=15
    )

    try:
        results = await test_full_mcp_integration(config)

        print(f"\n📊 TEST RESULTS")
        print(f"Overall Status: {results['overall_status']}")
        print(f"MCP Integration Complete: {results['mcp_integration_complete']}")
        print(f"Fallback Mechanisms Needed: {results['fallback_mechanisms_needed']}")

        print(f"\n🧪 Individual Tests:")
        for test_name, test_result in results['tests'].items():
            status_emoji = "✅" if test_result['status'] == 'PASS' else "❌"
            print(f"  {status_emoji} {test_name}: {test_result['status']}")

            if test_name == 'account_info' and test_result.get('success'):
                print(f"    - Lender Balance: {test_result.get('lender_balance_algos', 0)} ALGO")
                print(f"    - Borrower Balance: {test_result.get('borrower_balance_algos', 0)} ALGO")

            elif test_name == 'transaction_history' and test_result.get('success'):
                print(f"    - Found {test_result.get('transaction_count', 0)} transactions")

            elif test_name == 'transaction_building' and test_result.get('success'):
                print(f"    - Built transaction of {test_result.get('txn_length', 0)} bytes")

        print(f"\n🎯 Test Wallet Addresses:")
        for role, addr in results['test_addresses'].items():
            print(f"  {role}: {addr}")

        # Final assessment
        if results['mcp_integration_complete']:
            print(f"\n🎉 SUCCESS: MCP Protocol Integration COMPLETE!")
            print(f"   ✅ Real blockchain connectivity established")
            print(f"   ✅ All services working without fallbacks")
            print(f"   ✅ Ready for production lending operations")
        else:
            print(f"\n⚠️  PARTIAL: Some services need attention")
            failed_tests = [name for name, result in results['tests'].items()
                          if result['status'] == 'FAIL']
            print(f"   Failed tests: {', '.join(failed_tests)}")

        # Save detailed results
        with open('/home/mpo/algorand-showcase/mcp_integration_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: mcp_integration_results.json")

        return results['mcp_integration_complete']

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)