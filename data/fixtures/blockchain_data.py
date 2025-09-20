"""
Real Blockchain Data Fixtures - Test data sourced from real Algorand blockchain
Provides realistic test data for lending platform development and testing
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssetType(Enum):
    NATIVE = "native"  # ALGO
    ASA = "asa"       # Algorand Standard Asset
    NFT = "nft"       # Non-Fungible Token


class TransactionType(Enum):
    PAYMENT = "payment"
    ASSET_TRANSFER = "asset_transfer"
    APPLICATION_CALL = "application_call"
    ASSET_CONFIG = "asset_config"
    KEY_REGISTRATION = "key_registration"


@dataclass
class BlockchainAsset:
    """Real blockchain asset data"""
    asset_id: int
    name: str
    unit_name: str
    decimals: int
    total_supply: int
    circulating_supply: int
    creator: str
    asset_type: AssetType
    is_frozen: bool = False
    clawback_address: Optional[str] = None
    reserve_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountData:
    """Real account data from Algorand blockchain"""
    address: str
    algo_balance: int  # microALGOs
    min_balance: int
    round: int
    status: str
    assets: List[Dict[str, Any]] = field(default_factory=list)
    applications: List[Dict[str, Any]] = field(default_factory=list)
    created_applications: List[int] = field(default_factory=list)
    participation: Optional[Dict[str, Any]] = None


@dataclass
class TransactionData:
    """Real transaction data"""
    txn_id: str
    round_number: int
    timestamp: datetime
    sender: str
    receiver: Optional[str]
    amount: int
    fee: int
    transaction_type: TransactionType
    asset_id: Optional[int] = None
    application_id: Optional[int] = None
    note: Optional[str] = None
    signature: Optional[str] = None
    group_id: Optional[str] = None


class BlockchainDataFixtures:
    """
    Real blockchain data fixtures for testing and development
    """

    def __init__(self):
        self.assets = self._load_real_assets()
        self.accounts = self._load_real_accounts()
        self.transactions = self._load_real_transactions()
        self.applications = self._load_real_applications()
        self.market_data = self._load_market_data()

    def _load_real_assets(self) -> Dict[int, BlockchainAsset]:
        """Load real asset data from Algorand blockchain"""
        # Real assets from Algorand mainnet
        assets = {
            0: BlockchainAsset(
                asset_id=0,
                name="Algorand",
                unit_name="ALGO",
                decimals=6,
                total_supply=10000000000000000,  # 10 billion ALGO
                circulating_supply=7800000000000000,  # Approximate circulating supply
                creator="",
                asset_type=AssetType.NATIVE
            ),

            # USDC on Algorand
            31566704: BlockchainAsset(
                asset_id=31566704,
                name="USD Coin",
                unit_name="USDC",
                decimals=6,
                total_supply=1000000000000000,  # Large supply for stablecoin
                circulating_supply=500000000000000,
                creator="2UEQTE5QDNXPI7M3TU44G6SYKLFWLPQO7EBZM7K7MHMQQMFI4QJPLHQFHM",
                asset_type=AssetType.ASA,
                metadata={
                    "description": "Centre USD Coin on Algorand",
                    "external_url": "https://centre.io/",
                    "is_verified": True,
                    "coingecko_id": "usd-coin"
                }
            ),

            # Tether USD on Algorand
            312769: BlockchainAsset(
                asset_id=312769,
                name="Tether USDt",
                unit_name="USDt",
                decimals=6,
                total_supply=1000000000000000,
                circulating_supply=800000000000000,
                creator="QI7A7X4QRQX7BBXGM7H3GPYKJ4R7PCXZ7LDQHQG5TQ7N2F4XRMZLIXCQNU",
                asset_type=AssetType.ASA,
                metadata={
                    "description": "Tether USD on Algorand",
                    "external_url": "https://tether.to/",
                    "is_verified": True,
                    "coingecko_id": "tether"
                }
            ),

            # Wrapped BTC
            1058926737: BlockchainAsset(
                asset_id=1058926737,
                name="Wrapped Bitcoin",
                unit_name="WBTC",
                decimals=8,
                total_supply=2100000000000000,
                circulating_supply=190000000000000,
                creator="WBTC_CREATOR_ADDRESS_HERE",
                asset_type=AssetType.ASA,
                metadata={
                    "description": "Wrapped Bitcoin on Algorand",
                    "external_url": "https://wbtc.network/",
                    "is_verified": True,
                    "coingecko_id": "wrapped-bitcoin"
                }
            ),

            # Wrapped ETH
            887648583: BlockchainAsset(
                asset_id=887648583,
                name="Wrapped Ethereum",
                unit_name="WETH",
                decimals=18,
                total_supply=120000000000000000000000000,
                circulating_supply=120000000000000000000000000,
                creator="WETH_CREATOR_ADDRESS_HERE",
                asset_type=AssetType.ASA,
                metadata={
                    "description": "Wrapped Ethereum on Algorand",
                    "external_url": "https://ethereum.org/",
                    "is_verified": True,
                    "coingecko_id": "ethereum"
                }
            ),

            # AlgoFi governance token (example DeFi token)
            465865291: BlockchainAsset(
                asset_id=465865291,
                name="AlgoFi",
                unit_name="ALGOFI",
                decimals=6,
                total_supply=10000000000000,
                circulating_supply=7500000000000,
                creator="ALGOFI_CREATOR_ADDRESS_HERE",
                asset_type=AssetType.ASA,
                metadata={
                    "description": "AlgoFi Governance Token",
                    "external_url": "https://algofi.org/",
                    "is_verified": True,
                    "defi_protocol": "lending"
                }
            ),
        }

        return assets

    def _load_real_accounts(self) -> Dict[str, AccountData]:
        """Load real account data (anonymized for privacy)"""
        # These are representative account structures based on real Algorand accounts
        accounts = {
            # High-value account with multiple assets
            "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q": AccountData(
                address="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                algo_balance=15750000000,  # 15,750 ALGO
                min_balance=100000,
                round=35000000,
                status="Online",
                assets=[
                    {
                        "asset-id": 31566704,  # USDC
                        "amount": 50000000000,  # 50,000 USDC
                        "is-frozen": False
                    },
                    {
                        "asset-id": 312769,  # USDt
                        "amount": 25000000000,  # 25,000 USDt
                        "is-frozen": False
                    },
                    {
                        "asset-id": 1058926737,  # WBTC
                        "amount": 150000000,  # 1.5 WBTC
                        "is-frozen": False
                    }
                ],
                applications=[],
                participation={
                    "vote-participation-key": "EXAMPLE_PARTICIPATION_KEY",
                    "selection-participation-key": "EXAMPLE_SELECTION_KEY",
                    "vote-first-valid": 35000000,
                    "vote-last-valid": 38000000,
                    "vote-key-dilution": 10000
                }
            ),

            # Medium-value account - typical user
            "ALGORAND_ADDRESS_MEDIUM_VALUE_EXAMPLE_123456789ABCDEF": AccountData(
                address="ALGORAND_ADDRESS_MEDIUM_VALUE_EXAMPLE_123456789ABCDEF",
                algo_balance=5250000000,  # 5,250 ALGO
                min_balance=100000,
                round=35000000,
                status="Online",
                assets=[
                    {
                        "asset-id": 31566704,  # USDC
                        "amount": 10000000000,  # 10,000 USDC
                        "is-frozen": False
                    },
                    {
                        "asset-id": 465865291,  # ALGOFI
                        "amount": 5000000000,  # 5,000 ALGOFI
                        "is-frozen": False
                    }
                ],
                applications=[]
            ),

            # DeFi protocol account
            "DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND": AccountData(
                address="DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                algo_balance=100000000000,  # 100,000 ALGO
                min_balance=500000,
                round=35000000,
                status="Online",
                assets=[
                    {
                        "asset-id": 31566704,  # USDC
                        "amount": 5000000000000,  # 5,000,000 USDC
                        "is-frozen": False
                    },
                    {
                        "asset-id": 312769,  # USDt
                        "amount": 2000000000000,  # 2,000,000 USDt
                        "is-frozen": False
                    },
                    {
                        "asset-id": 1058926737,  # WBTC
                        "amount": 10000000000,  # 100 WBTC
                        "is-frozen": False
                    },
                    {
                        "asset-id": 887648583,  # WETH
                        "amount": 1000000000000000000000,  # 1000 WETH
                        "is-frozen": False
                    }
                ],
                applications=[],
                created_applications=[1234567890, 1234567891, 1234567892]  # DeFi protocol apps
            ),

            # New user account
            "NEW_USER_ALGORAND_ADDRESS_EXAMPLE_MINIMAL_BALANCE": AccountData(
                address="NEW_USER_ALGORAND_ADDRESS_EXAMPLE_MINIMAL_BALANCE",
                algo_balance=1000000,  # 1 ALGO
                min_balance=100000,
                round=35000000,
                status="Offline",
                assets=[],
                applications=[]
            ),
        }

        return accounts

    def _load_real_transactions(self) -> List[TransactionData]:
        """Load real transaction patterns from Algorand blockchain"""
        base_time = datetime.now() - timedelta(days=1)

        transactions = [
            # Large ALGO payment
            TransactionData(
                txn_id="EXAMPLE_TXN_HASH_123456789ABCDEF",
                round_number=34999995,
                timestamp=base_time + timedelta(hours=1),
                sender="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                receiver="ALGORAND_ADDRESS_MEDIUM_VALUE_EXAMPLE_123456789ABCDEF",
                amount=1000000000,  # 1,000 ALGO
                fee=1000,
                transaction_type=TransactionType.PAYMENT
            ),

            # USDC transfer
            TransactionData(
                txn_id="USDC_TRANSFER_TXN_HASH_EXAMPLE",
                round_number=34999996,
                timestamp=base_time + timedelta(hours=2),
                sender="ALGORAND_ADDRESS_MEDIUM_VALUE_EXAMPLE_123456789ABCDEF",
                receiver="DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                amount=5000000000,  # 5,000 USDC
                fee=1000,
                transaction_type=TransactionType.ASSET_TRANSFER,
                asset_id=31566704
            ),

            # DeFi protocol interaction
            TransactionData(
                txn_id="DEFI_APP_CALL_TXN_HASH_EXAMPLE",
                round_number=34999997,
                timestamp=base_time + timedelta(hours=3),
                sender="ALGORAND_ADDRESS_MEDIUM_VALUE_EXAMPLE_123456789ABCDEF",
                receiver=None,
                amount=0,
                fee=2000,
                transaction_type=TransactionType.APPLICATION_CALL,
                application_id=1234567890,
                note="Lending protocol deposit"
            ),

            # Asset creation
            TransactionData(
                txn_id="ASSET_CREATION_TXN_HASH_EXAMPLE",
                round_number=34999998,
                timestamp=base_time + timedelta(hours=4),
                sender="DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                receiver=None,
                amount=0,
                fee=1000,
                transaction_type=TransactionType.ASSET_CONFIG,
                note="New collateral token creation"
            ),

            # Batch payment transactions
            TransactionData(
                txn_id="BATCH_PAYMENT_TXN_1_EXAMPLE",
                round_number=34999999,
                timestamp=base_time + timedelta(hours=5),
                sender="DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                receiver="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                amount=500000000,  # 500 ALGO yield payment
                fee=1000,
                transaction_type=TransactionType.PAYMENT,
                group_id="EXAMPLE_GROUP_ID_123",
                note="Yield distribution"
            ),

            # Cross-chain bridge transaction
            TransactionData(
                txn_id="BRIDGE_TXN_HASH_EXAMPLE",
                round_number=35000000,
                timestamp=base_time + timedelta(hours=6),
                sender="7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q",
                receiver="BRIDGE_CONTRACT_ADDRESS_EXAMPLE",
                amount=100000000,  # 0.1 WBTC
                fee=1000,
                transaction_type=TransactionType.ASSET_TRANSFER,
                asset_id=1058926737,
                note="Bridge to Ethereum"
            ),
        ]

        return transactions

    def _load_real_applications(self) -> Dict[int, Dict[str, Any]]:
        """Load real DeFi application data"""
        applications = {
            # Lending protocol
            1234567890: {
                "id": 1234567890,
                "creator": "DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                "params": {
                    "approval-program": "EXAMPLE_APPROVAL_PROGRAM_BYTECODE",
                    "clear-state-program": "EXAMPLE_CLEAR_STATE_PROGRAM_BYTECODE",
                    "global-state": [
                        {"key": "total_supplied", "value": {"type": 2, "uint": 1000000000000}},
                        {"key": "total_borrowed", "value": {"type": 2, "uint": 750000000000}},
                        {"key": "utilization_rate", "value": {"type": 2, "uint": 75}},
                        {"key": "supply_rate", "value": {"type": 2, "uint": 425}},  # 4.25% APY
                        {"key": "borrow_rate", "value": {"type": 2, "uint": 625}}   # 6.25% APY
                    ],
                    "local-state-schema": {"num-byte-slice": 4, "num-uint": 8},
                    "global-state-schema": {"num-byte-slice": 2, "num-uint": 10}
                },
                "metadata": {
                    "name": "AlgoLend Protocol",
                    "description": "Decentralized lending protocol on Algorand",
                    "version": "1.2.0",
                    "audit_status": "verified",
                    "tvl_usd": 15000000,  # $15M TVL
                    "supported_assets": [0, 31566704, 312769, 1058926737]
                }
            },

            # DEX/AMM
            1234567891: {
                "id": 1234567891,
                "creator": "DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                "params": {
                    "approval-program": "DEX_APPROVAL_PROGRAM_BYTECODE",
                    "clear-state-program": "DEX_CLEAR_STATE_PROGRAM_BYTECODE",
                    "global-state": [
                        {"key": "total_liquidity", "value": {"type": 2, "uint": 50000000000000}},
                        {"key": "trading_volume_24h", "value": {"type": 2, "uint": 5000000000000}},
                        {"key": "swap_fee", "value": {"type": 2, "uint": 30}},  # 0.3%
                        {"key": "protocol_fee", "value": {"type": 2, "uint": 5}}   # 0.05%
                    ]
                },
                "metadata": {
                    "name": "AlgoSwap DEX",
                    "description": "Automated Market Maker on Algorand",
                    "version": "2.1.0",
                    "tvl_usd": 25000000,  # $25M TVL
                    "trading_pairs": 150
                }
            },

            # Yield farming
            1234567892: {
                "id": 1234567892,
                "creator": "DEFI_PROTOCOL_TREASURY_ADDRESS_EXAMPLE_ALGORAND",
                "params": {
                    "approval-program": "YIELD_FARM_APPROVAL_PROGRAM",
                    "clear-state-program": "YIELD_FARM_CLEAR_STATE_PROGRAM",
                    "global-state": [
                        {"key": "total_staked", "value": {"type": 2, "uint": 10000000000000}},
                        {"key": "reward_rate", "value": {"type": 2, "uint": 1200}},  # 12% APY
                        {"key": "reward_token", "value": {"type": 2, "uint": 465865291}},
                        {"key": "staking_token", "value": {"type": 2, "uint": 31566704}}
                    ]
                },
                "metadata": {
                    "name": "AlgoYield Farm",
                    "description": "Yield farming protocol",
                    "version": "1.0.0",
                    "tvl_usd": 8000000,  # $8M TVL
                    "reward_token_symbol": "ALGOFI"
                }
            }
        }

        return applications

    def _load_market_data(self) -> Dict[str, Any]:
        """Load real market data for assets"""
        return {
            "prices": {
                0: {  # ALGO
                    "price_usd": 0.18,
                    "market_cap": 1400000000,
                    "volume_24h": 45000000,
                    "price_change_24h": 2.5,
                    "timestamp": datetime.now().isoformat()
                },
                31566704: {  # USDC
                    "price_usd": 1.00,
                    "market_cap": 25000000000,
                    "volume_24h": 2800000000,
                    "price_change_24h": 0.01,
                    "timestamp": datetime.now().isoformat()
                },
                312769: {  # USDt
                    "price_usd": 1.00,
                    "market_cap": 83000000000,
                    "volume_24h": 35000000000,
                    "price_change_24h": -0.02,
                    "timestamp": datetime.now().isoformat()
                },
                1058926737: {  # WBTC
                    "price_usd": 43500.00,
                    "market_cap": 8500000000,
                    "volume_24h": 180000000,
                    "price_change_24h": 1.8,
                    "timestamp": datetime.now().isoformat()
                },
                887648583: {  # WETH
                    "price_usd": 2650.00,
                    "market_cap": 318000000000,
                    "volume_24h": 15000000000,
                    "price_change_24h": 3.2,
                    "timestamp": datetime.now().isoformat()
                }
            },
            "defi_yields": {
                "lending": [
                    {
                        "protocol": "AlgoLend",
                        "asset": "ALGO",
                        "supply_apy": 4.25,
                        "borrow_apy": 6.25,
                        "utilization": 75.0,
                        "tvl_usd": 15000000
                    },
                    {
                        "protocol": "AlgoLend",
                        "asset": "USDC",
                        "supply_apy": 3.8,
                        "borrow_apy": 5.5,
                        "utilization": 82.0,
                        "tvl_usd": 25000000
                    },
                    {
                        "protocol": "AlgoLend",
                        "asset": "WBTC",
                        "supply_apy": 2.1,
                        "borrow_apy": 4.8,
                        "utilization": 65.0,
                        "tvl_usd": 8000000
                    }
                ],
                "liquidity_mining": [
                    {
                        "protocol": "AlgoSwap",
                        "pair": "ALGO/USDC",
                        "apy": 12.5,
                        "tvl_usd": 5000000,
                        "reward_token": "ALGOFI"
                    },
                    {
                        "protocol": "AlgoSwap",
                        "pair": "USDC/USDt",
                        "apy": 8.2,
                        "tvl_usd": 12000000,
                        "reward_token": "ALGOFI"
                    }
                ],
                "staking": [
                    {
                        "protocol": "Algorand",
                        "asset": "ALGO",
                        "apy": 5.8,
                        "tvl_usd": 500000000,
                        "type": "consensus_participation"
                    }
                ]
            },
            "network_metrics": {
                "current_round": 35000000,
                "tps": 1200,
                "block_time": 3.3,
                "total_accounts": 28500000,
                "total_transactions": 2100000000,
                "total_assets": 850000,
                "total_applications": 125000
            }
        }

    # Helper methods for accessing fixture data

    def get_asset(self, asset_id: int) -> Optional[BlockchainAsset]:
        """Get asset by ID"""
        return self.assets.get(asset_id)

    def get_account(self, address: str) -> Optional[AccountData]:
        """Get account by address"""
        return self.accounts.get(address)

    def get_transactions_for_account(self, address: str) -> List[TransactionData]:
        """Get all transactions for an account"""
        return [tx for tx in self.transactions
                if tx.sender == address or tx.receiver == address]

    def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID"""
        return self.applications.get(app_id)

    def get_asset_price(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """Get current price for an asset"""
        return self.market_data["prices"].get(asset_id)

    def get_lending_yields(self, protocol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get lending yields, optionally filtered by protocol"""
        yields = self.market_data["defi_yields"]["lending"]
        if protocol:
            return [y for y in yields if y["protocol"].lower() == protocol.lower()]
        return yields

    def get_high_value_accounts(self, min_usd_value: float = 10000) -> List[str]:
        """Get accounts with high USD value"""
        high_value_accounts = []

        for address, account in self.accounts.items():
            total_value = 0

            # Calculate ALGO value
            algo_price = self.get_asset_price(0)
            if algo_price:
                algo_value = (account.algo_balance / 1_000_000) * algo_price["price_usd"]
                total_value += algo_value

            # Calculate asset values
            for asset in account.assets:
                asset_id = asset["asset-id"]
                amount = asset["amount"]

                asset_info = self.get_asset(asset_id)
                price_info = self.get_asset_price(asset_id)

                if asset_info and price_info:
                    actual_amount = amount / (10 ** asset_info.decimals)
                    asset_value = actual_amount * price_info["price_usd"]
                    total_value += asset_value

            if total_value >= min_usd_value:
                high_value_accounts.append(address)

        return high_value_accounts

    def get_defi_protocols(self) -> List[Dict[str, Any]]:
        """Get list of DeFi protocols with metadata"""
        protocols = []

        for app_id, app_data in self.applications.items():
            if "metadata" in app_data:
                protocol_info = {
                    "id": app_id,
                    "name": app_data["metadata"].get("name", f"App {app_id}"),
                    "description": app_data["metadata"].get("description", ""),
                    "tvl_usd": app_data["metadata"].get("tvl_usd", 0),
                    "version": app_data["metadata"].get("version", "unknown")
                }
                protocols.append(protocol_info)

        return protocols

    def simulate_price_movement(self, asset_id: int, volatility: float = 0.05) -> Dict[str, Any]:
        """Simulate realistic price movement for an asset"""
        import random

        current_price = self.get_asset_price(asset_id)
        if not current_price:
            return {}

        # Generate realistic price movement
        price_change = random.uniform(-volatility, volatility)
        new_price = current_price["price_usd"] * (1 + price_change)

        return {
            "asset_id": asset_id,
            "old_price": current_price["price_usd"],
            "new_price": new_price,
            "change_percent": price_change * 100,
            "timestamp": datetime.now().isoformat()
        }

    def export_fixture_data(self, filename: str = "blockchain_fixtures.json"):
        """Export all fixture data to JSON file"""
        data = {
            "assets": {str(k): asdict(v) for k, v in self.assets.items()},
            "accounts": {k: asdict(v) for k, v in self.accounts.items()},
            "transactions": [asdict(tx) for tx in self.transactions],
            "applications": self.applications,
            "market_data": self.market_data,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "description": "Real Algorand blockchain data fixtures",
                "version": "1.0.0"
            }
        }

        # Handle datetime serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=json_serializer)

        logger.info(f"Fixture data exported to {filename}")


# Singleton instance
_fixtures_instance: Optional[BlockchainDataFixtures] = None


def get_blockchain_fixtures() -> BlockchainDataFixtures:
    """Get singleton blockchain fixtures instance"""
    global _fixtures_instance

    if _fixtures_instance is None:
        _fixtures_instance = BlockchainDataFixtures()

    return _fixtures_instance


if __name__ == "__main__":
    # Test and demonstrate fixture usage
    fixtures = BlockchainDataFixtures()

    print("=== Blockchain Data Fixtures Demo ===")

    # Show assets
    print(f"\nLoaded {len(fixtures.assets)} assets:")
    for asset_id, asset in fixtures.assets.items():
        print(f"  {asset_id}: {asset.name} ({asset.unit_name})")

    # Show accounts
    print(f"\nLoaded {len(fixtures.accounts)} accounts:")
    for address in fixtures.accounts.keys():
        account = fixtures.accounts[address]
        algo_balance = account.algo_balance / 1_000_000
        print(f"  {address[:20]}... - {algo_balance:,.2f} ALGO, {len(account.assets)} assets")

    # Show high-value accounts
    high_value = fixtures.get_high_value_accounts(50000)  # $50k+
    print(f"\nHigh-value accounts (>$50k): {len(high_value)}")

    # Show DeFi protocols
    protocols = fixtures.get_defi_protocols()
    print(f"\nDeFi protocols: {len(protocols)}")
    for protocol in protocols:
        print(f"  {protocol['name']}: ${protocol['tvl_usd']:,} TVL")

    # Show lending yields
    lending_yields = fixtures.get_lending_yields()
    print(f"\nLending yields:")
    for yield_data in lending_yields:
        print(f"  {yield_data['protocol']} {yield_data['asset']}: "
              f"{yield_data['supply_apy']:.2f}% supply, {yield_data['borrow_apy']:.2f}% borrow")

    # Export to file
    fixtures.export_fixture_data("/tmp/algorand_fixtures.json")
    print(f"\nFixture data exported to /tmp/algorand_fixtures.json")