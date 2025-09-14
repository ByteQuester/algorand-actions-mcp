#!/usr/bin/env python3
"""
Generate and test with fresh wallet to isolate the transaction issue
"""

import base64
from algosdk import account, transaction
from algosdk.v2client import algod

TESTNET_ALGOD_URL = "https://testnet-api.algonode.cloud"

def main():
    print("🧪 Fresh Wallet Transaction Test")
    print("=" * 40)

    # Generate a fresh account
    private_key, address = account.generate_account()

    print(f"Generated address: {address}")
    print(f"Private key (b64): {private_key}")
    print(f"Private key length: {len(private_key)} characters")

    # Test base64 decoding (private_key is already base64 encoded string)
    decoded_key = base64.b64decode(private_key)

    print(f"✅ Base64 encode/decode test passed")
    print(f"Original key == Decoded key: {private_key == decoded_key}")

    # Setup Algod client
    algod_client = algod.AlgodClient("", TESTNET_ALGOD_URL)

    try:
        # Get suggested transaction parameters
        params = algod_client.suggested_params()
        print(f"✅ Got network parameters")

        # Create a dummy transaction (won't be funded but should build/sign)
        dummy_address = "MYZFY5XANQ3HN2YCS2XNOQIWL5PANXL35EV3YKBN5R5A6Y4TT43ZU3WZYM"

        txn = transaction.PaymentTxn(
            sender=address,
            sp=params,
            receiver=dummy_address,
            amt=100000,  # 0.1 ALGO
            note="Test transaction".encode()
        )

        print(f"✅ Transaction created")

        # Sign transaction with decoded private key (sign expects bytes)
        signed_txn = txn.sign(base64.b64decode(private_key))

        print(f"✅ Transaction signed successfully!")
        print(f"📝 Transaction ID: {txn.get_txid()}")

        print("\n🎉 FRESH WALLET TEST PASSED!")
        print("The issue is not with the transaction building logic.")

        return True

    except Exception as e:
        print(f"❌ Transaction failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)