#!/usr/bin/env python3
"""
Generate Algorand testnet wallets for lending demo testing
"""

import json
import os
from algosdk import account, mnemonic
from typing import Dict, Any

def generate_wallet(name: str) -> Dict[str, Any]:
    """Generate a new Algorand wallet"""
    private_key, public_address = account.generate_account()
    wallet_mnemonic = mnemonic.from_private_key(private_key)

    return {
        "name": name,
        "address": public_address,
        "private_key": private_key,
        "mnemonic": wallet_mnemonic
    }

def main():
    """Generate test wallets for the lending demo"""
    print("Generating Algorand testnet wallets for lending demo...")

    # Generate the three required wallets
    wallets = {
        "lender": generate_wallet("Lender Wallet"),
        "borrower": generate_wallet("Borrower Wallet"),
        "liquidity_provider": generate_wallet("Liquidity Provider Wallet")
    }

    # Create .env file with private keys (NEVER commit this!)
    env_content = "# TESTNET WALLETS - DO NOT COMMIT TO GIT!\n"
    env_content += "# Generated for lending demo testing\n\n"

    for role, wallet in wallets.items():
        env_content += f"# {wallet['name']}\n"
        env_content += f"{role.upper()}_ADDRESS={wallet['address']}\n"
        env_content += f"{role.upper()}_PRIVATE_KEY={wallet['private_key']}\n"
        env_content += f"{role.upper()}_MNEMONIC=\"{wallet['mnemonic']}\"\n\n"

    # Write private keys to .env.testnet (secure)
    with open('/home/mpo/algorand-showcase/.env.testnet', 'w') as f:
        f.write(env_content)

    # Create public wallet info file (safe to commit)
    public_wallets = {}
    for role, wallet in wallets.items():
        public_wallets[role] = {
            "name": wallet["name"],
            "address": wallet["address"],
            "funded": False,
            "balance": 0
        }

    with open('/home/mpo/algorand-showcase/test-wallets.json', 'w') as f:
        json.dump(public_wallets, f, indent=2)

    print("\n=== TESTNET WALLETS GENERATED ===")
    print("Private keys stored in: .env.testnet (DO NOT COMMIT)")
    print("Public addresses stored in: test-wallets.json\n")

    print("Wallet Addresses:")
    for role, wallet in wallets.items():
        print(f"  {wallet['name']}: {wallet['address']}")

    print("\nFunding Instructions:")
    print("1. Go to https://bank.testnet.algorand.network/")
    print("2. Fund each address with at least 10 ALGO")
    print("3. Run the integration test to verify setup")

    print("\nNext Steps:")
    print("- Fund wallets using testnet faucet")
    print("- Run integration tests with: python test-integration.py")
    print("- Check MCP API documentation at localhost:8002/docs and localhost:3001/docs")

if __name__ == "__main__":
    main()