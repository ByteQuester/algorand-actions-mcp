#!/usr/bin/env python3
"""
Simple Algorand Transaction Test - Execute actual testnet transaction
"""

import json
import requests
import base64
from algosdk import account, transaction
from algosdk.v2client import algod

# Configuration
ENV_FILE = "/home/mpo/algorand-showcase/.env.testnet"
WALLETS_FILE = "/home/mpo/algorand-showcase/test-wallets.json"
TESTNET_ALGOD_URL = "https://testnet-api.algonode.cloud"

def load_env_vars():
    """Load environment variables from .env.testnet"""
    env_vars = {}
    with open(ENV_FILE, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value.strip('"')
    return env_vars

def load_wallets():
    """Load wallet info from JSON"""
    with open(WALLETS_FILE, 'r') as f:
        return json.load(f)

def main():
    print("🧪 Simple Algorand Transaction Test")
    print("=" * 40)

    # Load configuration
    env_vars = load_env_vars()
    wallets = load_wallets()

    # Setup Algod client
    algod_client = algod.AlgodClient("", TESTNET_ALGOD_URL)

    # Get lender wallet info
    lender_address = env_vars.get('LENDER_ADDRESS')
    lender_private_key_b64 = env_vars.get('LENDER_PRIVATE_KEY')
    borrower_address = env_vars.get('BORROWER_ADDRESS')

    print(f"From: {lender_address[:10]}...{lender_address[-10:]}")
    print(f"To: {borrower_address[:10]}...{borrower_address[-10:]}")

    try:
        # Get suggested transaction parameters
        params = algod_client.suggested_params()
        print(f"✅ Got network parameters")

        # Create payment transaction for 0.1 ALGO
        amount = 100000  # 0.1 ALGO in microAlgos

        txn = transaction.PaymentTxn(
            sender=lender_address,
            sp=params,
            receiver=borrower_address,
            amt=amount,
            note="Test transaction from infrastructure test".encode()
        )

        print(f"✅ Transaction created")

        # Sign transaction
        private_key = base64.b64decode(lender_private_key_b64)
        signed_txn = txn.sign(private_key)

        print(f"✅ Transaction signed")
        print(f"📝 Transaction ID: {txn.get_txid()}")

        # Submit transaction
        tx_id = algod_client.send_transaction(signed_txn)
        print(f"✅ Transaction submitted: {tx_id}")

        # Wait for confirmation
        print("⏳ Waiting for confirmation...")
        confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)

        print(f"✅ Transaction confirmed in round {confirmed_txn.get('confirmed-round')}")

        # Check balances after transaction
        print("\n💰 Updated Balances:")
        lender_info = algod_client.account_info(lender_address)
        borrower_info = algod_client.account_info(borrower_address)

        print(f"  Lender: {lender_info['amount'] / 1000000:.6f} ALGO")
        print(f"  Borrower: {borrower_info['amount'] / 1000000:.6f} ALGO")

        print("\n🎉 TRANSACTION SUCCESS!")
        print(f"🔗 View on AlgoExplorer: https://testnet.explorer.perawallet.app/tx/{tx_id}")

        return True

    except Exception as e:
        print(f"❌ Transaction failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)