# Algorand Blockchain Reader MCP

A Model Context Protocol (MCP) service providing **READ ONLY** access to Algorand blockchain data via indexer and algod APIs.

## Overview

The Algorand Reader MCP is a professional service that provides comprehensive read access to Algorand blockchain data. It supports OAuth authentication, pagination, and connects to both testnet and mainnet networks.

## Features

- **Read-Only Operations**: Safe access to blockchain data without any write capabilities
- **Comprehensive Data Access**: Accounts, transactions, assets, applications, and blocks
- **OAuth2 Authentication**: Secure access with proper authentication
- **Pagination Support**: Handle large datasets efficiently
- **Network Support**: Both testnet and mainnet compatibility
- **Health Monitoring**: Built-in health checks

## Available Tools

### Account Operations
- `search_accounts` - Search for accounts by various criteria
- `get_account` - Get detailed account information

### Transaction Operations
- `search_transactions` - Search transactions by address, asset, type, etc.
- `get_transaction` - Get detailed transaction information

### Asset Operations
- `search_assets` - Search Algorand Standard Assets (ASAs)
- `get_asset` - Get detailed asset information

### Application Operations
- `search_applications` - Search for Algorand applications
- `get_application` - Get detailed application information

### Blockchain Operations
- `get_block` - Get block information for a specific round

### System Operations
- `get_health` - Check service health status

## API Endpoints

- `GET /health` - Service health check
- `GET /accounts/{address}` - Account information
- `GET /accounts` - Search accounts
- `GET /transactions/{txid}` - Transaction details
- `GET /transactions` - Search transactions
- `GET /assets/{asset_id}` - Asset information
- `GET /assets` - Search assets
- `GET /applications/{app_id}` - Application information
- `GET /applications` - Search applications
- `GET /blocks/{round}` - Block information

## Configuration

### Environment Variables

- `ALGORAND_SERVER` - Algod server URL
- `ALGORAND_TOKEN` - Algod API token
- `INDEXER_SERVER` - Indexer server URL
- `INDEXER_TOKEN` - Indexer API token
- `READ_ONLY` - Force read-only mode (default: true)
- `OAUTH_*` - OAuth configuration variables

### Network Configuration

```json
{
  "default": "testnet",
  "supported": ["testnet", "mainnet"]
}
```

## Development

### Local Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The service will run on port 8002 by default.

### Docker

```bash
# Build Docker image
docker build -t algorand-reader-mcp .

# Run container
docker run -p 8002:8002 algorand-reader-mcp
```

## Usage Examples

### Get Account Information

```bash
curl -X GET "http://localhost:8002/accounts/ACCOUNT_ADDRESS" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search Transactions

```bash
curl -X GET "http://localhost:8002/transactions?address=ACCOUNT_ADDRESS&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Asset Information

```bash
curl -X GET "http://localhost:8002/assets/ASSET_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Security

- **Read-Only**: This service cannot perform any write operations
- **OAuth2**: Secure authentication required
- **Rate Limiting**: Built-in protection against abuse
- **Input Validation**: All inputs are validated and sanitized

## Production Deployment

The service is designed for production deployment with:
- Health checks for load balancers
- Proper error handling and logging
- OAuth2 authentication
- Rate limiting and security controls
- Support for both testnet and mainnet

## Support

For issues and questions:
- Check the manifest.json for complete API specification
- Review the health endpoint for service status
- Ensure proper OAuth configuration

## Version

Current version: 1.2.0

## License

See LICENSE file for details.