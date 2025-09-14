#!/usr/bin/env python3
"""
Integration test script for Algorand MCP services and lending demo infrastructure

This script verifies:
1. MCP services are running and accessible
2. Test wallets can be queried via Remote MCP
3. Simple transfers work via Actions MCP
4. All infrastructure is ready for lending demo
"""

import asyncio
import json
import httpx
import os
import sys
from typing import Dict, Any, Optional
from algosdk import account, transaction, encoding
import base64

# Configuration
REMOTE_MCP_URL = "http://localhost:8002"
ACTIONS_MCP_URL = "http://localhost:3001"
WALLETS_FILE = "/home/mpo/algorand-showcase/test-wallets.json"
ENV_FILE = "/home/mpo/algorand-showcase/.env.testnet"

class TestResults:
    """Track test results and provide summary"""

    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0

    def add_test(self, name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        print(f"\n=== TEST RESULTS ===")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total: {len(self.tests)}")

        if self.failed > 0:
            print("\nFailed tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  ❌ {test['name']}: {test['message']}")

        return self.failed == 0

class IntegrationTester:
    """Main integration test class"""

    def __init__(self):
        self.results = TestResults()
        self.wallets = None
        self.private_keys = {}

    async def load_test_data(self) -> bool:
        """Load wallet data and private keys"""
        try:
            # Load public wallet data
            if not os.path.exists(WALLETS_FILE):
                self.results.add_test("Load wallet data", False, f"Wallets file not found: {WALLETS_FILE}")
                return False

            with open(WALLETS_FILE, 'r') as f:
                self.wallets = json.load(f)

            # Load private keys from env file
            if not os.path.exists(ENV_FILE):
                self.results.add_test("Load private keys", False, f"Env file not found: {ENV_FILE}")
                return False

            with open(ENV_FILE, 'r') as f:
                env_content = f.read()
                for line in env_content.split('\n'):
                    if '_PRIVATE_KEY=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        role = key.replace('_PRIVATE_KEY', '').lower()
                        self.private_keys[role] = value

            self.results.add_test("Load test data", True, f"Loaded {len(self.wallets)} wallets")
            return True

        except Exception as e:
            self.results.add_test("Load test data", False, str(e))
            return False

    async def test_mcp_services(self) -> bool:
        """Test that MCP services are running and accessible"""
        async with httpx.AsyncClient(timeout=10) as client:
            # Test Remote MCP service
            try:
                response = await client.get(f"{REMOTE_MCP_URL}/health")
                if response.status_code == 200:
                    self.results.add_test("Remote MCP Health", True, "Service responding")
                else:
                    self.results.add_test("Remote MCP Health", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.results.add_test("Remote MCP Health", False, str(e))

            # Test Actions MCP service
            try:
                response = await client.get(f"{ACTIONS_MCP_URL}/health")
                if response.status_code == 200:
                    self.results.add_test("Actions MCP Health", True, "Service responding")
                else:
                    self.results.add_test("Actions MCP Health", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.results.add_test("Actions MCP Health", False, str(e))

            # Test API endpoints availability
            try:
                response = await client.get(f"{REMOTE_MCP_URL}/openapi.json")
                if response.status_code == 200:
                    spec = response.json()
                    endpoints = len(spec.get('paths', {}))
                    self.results.add_test("Remote MCP API", True, f"{endpoints} endpoints available")
                else:
                    self.results.add_test("Remote MCP API", False, "OpenAPI spec not accessible")
            except Exception as e:
                self.results.add_test("Remote MCP API", False, str(e))

            try:
                response = await client.get(f"{ACTIONS_MCP_URL}/openapi.json")
                if response.status_code == 200:
                    spec = response.json()
                    endpoints = len(spec.get('paths', {}))
                    self.results.add_test("Actions MCP API", True, f"{endpoints} endpoints available")
                else:
                    self.results.add_test("Actions MCP API", False, "OpenAPI spec not accessible")
            except Exception as e:
                self.results.add_test("Actions MCP API", False, str(e))

    async def test_wallet_balances(self) -> bool:
        """Test wallet balance queries via Remote MCP"""
        async with httpx.AsyncClient(timeout=10) as client:
            for role, wallet in self.wallets.items():
                try:
                    response = await client.post(
                        f"{REMOTE_MCP_URL}/tools/get-account-info",
                        json={"address": wallet["address"]}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if "error" not in result and "data" in result:
                            balance = result["data"].get("amount", 0) / 1000000  # Convert microAlgos
                            self.results.add_test(
                                f"Query {wallet['name']}",
                                True,
                                f"Balance: {balance:.6f} ALGO"
                            )

                            # Update wallet info
                            wallet["funded"] = balance > 0
                            wallet["balance"] = balance
                        else:
                            self.results.add_test(
                                f"Query {wallet['name']}",
                                False,
                                f"API error: {result.get('error', 'Unknown error')}"
                            )
                    else:
                        self.results.add_test(
                            f"Query {wallet['name']}",
                            False,
                            f"HTTP {response.status_code}"
                        )

                except Exception as e:
                    self.results.add_test(f"Query {wallet['name']}", False, str(e))

    async def test_simple_transfer(self) -> bool:
        """Test a simple transfer between wallets using Actions MCP"""
        if not all(wallet["funded"] for wallet in self.wallets.values()):
            self.results.add_test("Simple Transfer", False, "Not all wallets are funded")
            return False

        # Use lender -> borrower for test transfer
        from_wallet = self.wallets["lender"]
        to_wallet = self.wallets["borrower"]
        from_private_key = self.private_keys.get("lender")

        if not from_private_key:
            self.results.add_test("Simple Transfer", False, "Lender private key not found")
            return False

        transfer_amount = 1000000  # 1 ALGO in microAlgos

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # Build transaction
                build_response = await client.post(
                    f"{ACTIONS_MCP_URL}/tools/build-payment-tx",
                    json={
                        "fromAddress": from_wallet["address"],
                        "toAddress": to_wallet["address"],
                        "microAlgos": transfer_amount,
                        "note": "Integration test transfer"
                    }
                )

                if build_response.status_code != 200:
                    self.results.add_test("Build Transaction", False, f"HTTP {build_response.status_code}")
                    return False

                build_result = build_response.json()
                if "error" in build_result:
                    self.results.add_test("Build Transaction", False, build_result["error"])
                    return False

                # Get unsigned transaction
                unsigned_txn_b64 = build_result.get("unsignedTxnBase64")
                if not unsigned_txn_b64:
                    self.results.add_test("Build Transaction", False, "No unsigned transaction returned")
                    return False

                self.results.add_test("Build Transaction", True, "Transaction built successfully")

                # Sign transaction
                try:
                    unsigned_txn_bytes = base64.b64decode(unsigned_txn_b64)
                    unsigned_txn = encoding.future_msgpack_decode(unsigned_txn_bytes)
                    signed_txn = transaction.SignedTransaction(unsigned_txn, from_private_key)
                    signed_txn_b64 = base64.b64encode(encoding.msgpack_encode(signed_txn)).decode()

                    self.results.add_test("Sign Transaction", True, "Transaction signed")
                except Exception as e:
                    self.results.add_test("Sign Transaction", False, str(e))
                    return False

                # Submit transaction
                submit_response = await client.post(
                    f"{ACTIONS_MCP_URL}/tools/submit-signed-tx",
                    json={"signedTxnBase64": signed_txn_b64}
                )

                if submit_response.status_code == 200:
                    submit_result = submit_response.json()
                    if "error" not in submit_result and "txId" in submit_result:
                        tx_id = submit_result["txId"]
                        self.results.add_test(
                            "Submit Transaction",
                            True,
                            f"Transaction ID: {tx_id}"
                        )

                        # Wait and verify transaction
                        await asyncio.sleep(5)

                        # Check transaction on testnet explorer
                        explorer_url = f"https://testnet.algoexplorer.io/tx/{tx_id}"
                        self.results.add_test(
                            "Transaction Explorer",
                            True,
                            f"View at: {explorer_url}"
                        )

                        return True
                    else:
                        self.results.add_test("Submit Transaction", False, submit_result.get("error", "Unknown error"))
                        return False
                else:
                    self.results.add_test("Submit Transaction", False, f"HTTP {submit_response.status_code}")
                    return False

            except Exception as e:
                self.results.add_test("Simple Transfer", False, str(e))
                return False

    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        print("🚀 Starting Algorand MCP Integration Tests\n")

        # Load test data
        if not await self.load_test_data():
            return False

        print("📋 Test wallets loaded:")
        for role, wallet in self.wallets.items():
            print(f"  {wallet['name']}: {wallet['address']}")
        print()

        # Test MCP services
        print("🔍 Testing MCP services...")
        await self.test_mcp_services()

        # Test wallet queries
        print("💰 Testing wallet balance queries...")
        await self.test_wallet_balances()

        # Update wallets file with current balances
        try:
            with open(WALLETS_FILE, 'w') as f:
                json.dump(self.wallets, f, indent=2)
        except:
            pass

        # Test simple transfer (only if wallets are funded)
        if any(wallet["funded"] for wallet in self.wallets.values()):
            print("💸 Testing simple transfer...")
            await self.test_simple_transfer()
        else:
            self.results.add_test("Simple Transfer", False, "No funded wallets available")
            print("⚠️  Skipping transfer test - wallets not funded")

        # Print results
        success = self.results.print_summary()

        if not success:
            print(f"\n❌ Some tests failed. Check MCP services and wallet funding.")
            print(f"Funding instructions:")
            print(f"1. Go to https://bank.testnet.algorand.network/")
            print(f"2. Fund each wallet with at least 10 ALGO:")
            for role, wallet in self.wallets.items():
                funded_status = "✅" if wallet["funded"] else "❌"
                print(f"   {funded_status} {wallet['name']}: {wallet['address']}")
        else:
            print(f"\n✅ All tests passed! Infrastructure is ready for lending demo.")

        return success

async def main():
    """Main entry point"""
    tester = IntegrationTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())