# MCP Notebooks Configuration
# This setup gives you real Algorand blockchain data

USE_MOCK_MODE = False
USE_MOCK_READER = False    # Real Algorand testnet data
USE_MOCK_WRITER = False    # LIVE WRITER SERVICE ACTIVE!
USE_MOCK_MARKET = True     # Mock data (consistent prices)

# To enable REAL Writer and Market services:
# 1. Set USE_MOCK_WRITER = False (enables real transaction building)
# 2. Set USE_MOCK_MARKET = False (enables real price feeds)
# 3. Run the start-real-services.sh script to launch them
# WARNING: Real Writer service can create actual testnet transactions!

# Service URLs
READER_URL = "http://localhost:3500"
WRITER_URL = "http://localhost:8788"
MARKET_URL = "http://localhost:8789"

# Algorand testnet addresses for examples
ALICE_ADDRESS = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
BOB_ADDRESS = "GD64YIY3TWGDMCNPP553DZPPR6LDUSFQOIJVFDPPXWEG3FVOJCCDBBHU5A"
ESCROW_ADDRESS = "2UBZKFR6RCZL7R24ZG327VKPTPJUPFM6WTG7PJG2ZJLU234KIIRUXPLWW4"

# Assets and amounts
USDC_ASSET_ID = 10458941
USDT_ASSET_ID = 312769
ALGO_ASSET_ID = 0
ONE_ALGO = 1_000_000
HALF_ALGO = 500_000
TEN_USDC = 10_000_000

# Network
TESTNET_ALGOD = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER = "https://testnet-idx.algonode.cloud"