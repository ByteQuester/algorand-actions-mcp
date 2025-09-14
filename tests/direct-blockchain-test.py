#!/usr/bin/env python3
"""
Direct Blockchain Infrastructure Test
Tests core Algorand testnet connectivity bypassing MCP issues
"""

import asyncio
import json
import requests
from algosdk import account, transaction, encoding
import base64

# Load wallet configuration
WALLETS_FILE = "/home/mpo/algorand-showcase/test-wallets.json"
ENV_FILE = "/home/mpo/algorand-showcase/.env.testnet"
TESTNET_ALGOD = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER = "https://testnet-idx.algonode.cloud"

def load_private_keys():
    """Load private keys from .env.testnet"""
    keys = {}
    try:
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#') and 'PRIVATE_KEY' in line:
                    key, value = line.strip().split('=', 1)
                    # Clean up the value - remove quotes and whitespace
                    clean_value = value.strip().strip('"').strip("'")
                    keys[key] = clean_value
    except Exception as e:
        print(f"Error loading private keys: {e}")
        return {}
    return keys

def load_wallets():
    """Load wallet addresses"""
    try:
        with open(WALLETS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading wallets: {e}")
        return {}

def test_wallet_balance(address):
    """Test wallet balance using direct Algorand API"""
    try:
        url = f"{TESTNET_INDEXER}/v2/accounts/{address}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            account_info = data.get('account', {})
            balance_micro_algos = account_info.get('amount', 0)
            balance_algos = balance_micro_algos / 1000000

            return {
                'success': True,
                'balance_algos': balance_algos,
                'balance_micro_algos': balance_micro_algos,
                'address': address
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}",
                'address': address
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'address': address
        }

def test_transaction_build(from_address, to_address, amount_micro_algos, private_key_b64):
    """Test transaction building and signing"""
    try:
        # Get network parameters
        params_response = requests.get(f"{TESTNET_ALGOD}/v2/transactions/params")
        if params_response.status_code != 200:
            return {'success': False, 'error': 'Failed to get network parameters'}

        params = params_response.json()
        print(f"    Debug: Genesis hash: {params.get('genesis-hash')}")
        print(f"    Debug: Genesis hash length: {len(params.get('genesis-hash', ''))}")

        # Build suggested params more carefully
        suggested_params = transaction.SuggestedParams(
            fee=params.get('min-fee', 1000),
            first=params.get('last-round') - 1000,
            last=params.get('last-round') + 1000,
            gh=params.get('genesis-hash'),
            gen=params.get('genesis-id', 'testnet-v1.0'),
            flat_fee=True
        )

        # Build transaction
        txn = transaction.PaymentTxn(
            sender=from_address,
            sp=suggested_params,
            receiver=to_address,
            amt=amount_micro_algos
        )

        # Sign transaction
        private_key = base64.b64decode(private_key_b64)
        signed_txn = txn.sign(private_key)

        return {
            'success': True,
            'transaction_id': txn.get_txid(),
            'signed': True,
            'from_address': from_address,
            'to_address': to_address,
            'amount_algos': amount_micro_algos / 1000000
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Run comprehensive infrastructure tests"""
    print("🧪 Direct Blockchain Infrastructure Test")
    print("=" * 50)

    # Load configuration
    wallets = load_wallets()
    private_keys = load_private_keys()

    if not wallets:
        print("❌ Failed to load wallets")
        return False

    if not private_keys:
        print("❌ Failed to load private keys")
        return False

    print(f"📋 Loaded {len(wallets)} wallets")

    # Test Results
    results = {
        'wallet_tests': [],
        'transaction_test': None,
        'services_status': {
            'testnet_algod': None,
            'testnet_indexer': None
        },
        'summary': {
            'wallets_funded': 0,
            'total_balance_algos': 0,
            'transaction_build_success': False
        }
    }

    # Test Algorand services connectivity
    print("\n🔍 Testing Algorand Testnet Services...")
    try:
        algod_response = requests.get(f"{TESTNET_ALGOD}/health", timeout=5)
        results['services_status']['testnet_algod'] = algod_response.status_code == 200
        print(f"  Algod API: {'✅' if results['services_status']['testnet_algod'] else '❌'}")
    except:
        results['services_status']['testnet_algod'] = False
        print(f"  Algod API: ❌")

    try:
        indexer_response = requests.get(f"{TESTNET_INDEXER}/health", timeout=5)
        results['services_status']['testnet_indexer'] = indexer_response.status_code == 200
        print(f"  Indexer API: {'✅' if results['services_status']['testnet_indexer'] else '❌'}")
    except:
        results['services_status']['testnet_indexer'] = False
        print(f"  Indexer API: ❌")

    # Test wallet balances
    print("\n💰 Testing Wallet Balances...")
    for role, wallet in wallets.items():
        print(f"  Testing {wallet['name']}...")
        balance_result = test_wallet_balance(wallet['address'])
        results['wallet_tests'].append(balance_result)

        if balance_result['success']:
            balance = balance_result['balance_algos']
            print(f"    ✅ Balance: {balance:.6f} ALGO")
            if balance > 0:
                results['summary']['wallets_funded'] += 1
                results['summary']['total_balance_algos'] += balance
        else:
            print(f"    ❌ Error: {balance_result['error']}")

    # Test transaction building
    print("\n🔨 Testing Transaction Building...")
    if results['summary']['wallets_funded'] >= 2:
        # Find funded wallets for test transaction
        funded_wallets = [(role, wallet) for role, wallet in wallets.items()
                         if any(test['address'] == wallet['address'] and test['success'] and test['balance_algos'] > 0
                               for test in results['wallet_tests'])]

        if len(funded_wallets) >= 2:
            from_role, from_wallet = funded_wallets[0]
            to_role, to_wallet = funded_wallets[1]
            from_private_key = private_keys.get(f"{from_role.upper()}_PRIVATE_KEY")

            if from_private_key:
                print(f"  Building test transaction: {from_wallet['name']} -> {to_wallet['name']}")
                print(f"  Debug: Private key length: {len(from_private_key)} characters")
                print(f"  Debug: Private key ends with: ...{from_private_key[-10:]}")
                tx_result = test_transaction_build(
                    from_wallet['address'],
                    to_wallet['address'],
                    100000,  # 0.1 ALGO in micro-ALGOs
                    from_private_key
                )
                results['transaction_test'] = tx_result

                if tx_result['success']:
                    print(f"    ✅ Transaction built successfully")
                    print(f"    📝 Transaction ID: {tx_result['transaction_id']}")
                    results['summary']['transaction_build_success'] = True
                else:
                    print(f"    ❌ Transaction build failed: {tx_result['error']}")
            else:
                print(f"    ❌ Missing private key for {from_role}")
        else:
            print(f"    ⚠️  Not enough funded wallets for transaction test")
    else:
        print(f"    ⚠️  No funded wallets available for transaction test")

    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"Testnet Algod API: {'✅' if results['services_status']['testnet_algod'] else '❌'}")
    print(f"Testnet Indexer API: {'✅' if results['services_status']['testnet_indexer'] else '❌'}")
    print(f"Funded Wallets: {results['summary']['wallets_funded']}/{len(wallets)}")
    print(f"Total Balance: {results['summary']['total_balance_algos']:.6f} ALGO")
    print(f"Transaction Build: {'✅' if results['summary']['transaction_build_success'] else '❌'}")

    # Wallet details
    print("\n📋 WALLET DETAILS")
    for role, wallet in wallets.items():
        test_result = next((test for test in results['wallet_tests'] if test['address'] == wallet['address']), None)
        if test_result and test_result['success']:
            status = '✅ FUNDED' if test_result['balance_algos'] > 0 else '⚠️ EMPTY'
            print(f"  {wallet['name']}: {status} ({test_result['balance_algos']:.6f} ALGO)")
            print(f"    Address: {wallet['address']}")
        else:
            print(f"  {wallet['name']}: ❌ ERROR")
            print(f"    Address: {wallet['address']}")

    # Overall status
    overall_success = (
        results['services_status']['testnet_algod'] and
        results['services_status']['testnet_indexer'] and
        results['summary']['wallets_funded'] >= len(wallets) and
        results['summary']['transaction_build_success']
    )

    print(f"\n🎯 OVERALL STATUS: {'✅ READY' if overall_success else '⚠️ NEEDS ATTENTION'}")

    # Save detailed results
    with open('/home/mpo/algorand-showcase/direct-test-results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📁 Detailed results saved to: direct-test-results.json")

    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)