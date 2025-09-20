# Simple helper functions for MCP notebooks
import aiohttp
import json
from config import USE_MOCK_MODE, USE_MOCK_READER, USE_MOCK_WRITER, USE_MOCK_MARKET, READER_URL, WRITER_URL, MARKET_URL

def get_mock_data(url, data=None):
    """Return mock data for testing when services aren't available"""
    if "/health" in url:
        return {"status": "ok", "message": "Mock service healthy"}

    if "/tools/list" in url:
        return {
            "tools": [
                {"name": "get_account_info", "description": "Get account information"},
                {"name": "get_asset_info", "description": "Get asset information"},
                {"name": "build_payment_transaction", "description": "Build payment transaction"}
            ]
        }

    if "/tools/get_account_info" in url:
        return {
            "success": True,
            "account": {
                "address": data.get("address", "ALICE_ADDRESS") if data else "ALICE_ADDRESS",
                "amount": 5000000,  # 5 ALGO
                "status": "Online",
                "round": 12345,
                "assets": []
            }
        }

    if "/tools/build_payment_transaction" in url:
        return {
            "success": True,
            "transaction": "mock_transaction_data",
            "txId": "MOCK_TX_ID_123"
        }

    if "/tools/get_price_feed" in url:
        return {
            "success": True,
            "price": 0.1234,
            "pair": data.get("pair", "ALGO-USDC") if data else "ALGO-USDC",
            "timestamp": "2024-01-01T00:00:00Z"
        }

    return {"success": False, "error": "Mock endpoint not implemented"}

def should_use_mock(url):
    """Determine if we should use mock data for a specific service"""
    if USE_MOCK_MODE:
        return True
    if READER_URL in url and USE_MOCK_READER:
        return True
    if WRITER_URL in url and USE_MOCK_WRITER:
        return True
    if MARKET_URL in url and USE_MOCK_MARKET:
        return True
    return False

async def call_api(url, data=None):
    """API call helper with error handling and mock mode support"""
    if should_use_mock(url):
        service_name = "Reader" if READER_URL in url else "Writer" if WRITER_URL in url else "Market"
        print(f"🧪 Using mock data for {service_name} MCP: {url.split('/')[-1]}")
        return get_mock_data(url, data)

    # Convert /tools/ endpoints to /api/ endpoints for compatibility
    original_url = url
    if "/tools/" in url:
        # Map tool endpoints to API endpoints
        tool_mappings = {
            "/tools/get_account_info": "/api/account",
            "/tools/get_transaction": "/api/transaction",
            "/tools/get_asset_info": "/api/asset",
            "/tools/get_block_info": "/api/block",
            "/tools/search_transactions": "/api/search/transactions"
        }

        for tool_path, api_path in tool_mappings.items():
            if url.endswith(tool_path):
                url = url.replace(tool_path, api_path)
                break

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) if data else session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {"success": False, "error": f"Unexpected content type: {content_type}"}
                else:
                    text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {text}"}
    except aiohttp.ClientConnectorError as e:
        print(f"❌ Cannot connect to service: {original_url}")
        print(f"💡 Run './setup.sh' to start MCP services")
        print(f"💡 Or set USE_MOCK_MODE=True in config.py for testing")
        return {"success": False, "error": "Service not running", "mock_available": True}
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return {"success": False, "error": str(e)}

async def check_health(service_url):
    """Check if service is healthy"""
    try:
        result = await call_api(f"{service_url}/health")
        return result.get("status") == "ok"
    except:
        return False

def format_algo(microalgos):
    """Convert microAlgos to ALGO"""
    return microalgos / 1_000_000

def format_asset(micro_amount, decimals=6):
    """Convert micro units to regular units"""
    return micro_amount / (10 ** decimals)

def short_address(address):
    """Shorten address for display"""
    return f"{address[:8]}...{address[-8:]}"