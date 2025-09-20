# Algorand Blockchain Writer MCP

A Model Context Protocol (MCP) service providing **WRITE operations** to the Algorand blockchain - build, simulate, and submit transactions with proper security controls.

## Overview

The Algorand Writer MCP is a professional service that enables secure transaction operations on the Algorand blockchain. It provides tools to build unsigned transactions, simulate their effects, and submit signed transactions to the network. The service includes mainnet protection and can operate in read-only mode for testing.

## Features

- **Transaction Building**: Create unsigned transactions for various operations
- **Simulation Engine**: Test transaction effects before submission
- **Secure Submission**: Submit signed transactions with proper validation
- **Mainnet Protection**: Built-in safeguards against accidental mainnet operations
- **Read-Only Mode**: Can be disabled for testing and development
- **Network Support**: Both testnet and mainnet compatibility
- **Health Monitoring**: Built-in health checks and status reporting

## Available Tools

### Transaction Building
- `build_payment_tx` - Build unsigned payment transactions

### Transaction Simulation
- `simulate_raw_tx` - Simulate transaction effects and estimate costs

### Transaction Submission
- `submit_signed_tx` - Submit signed transactions to the network

### System Operations
- `get_health` - Check service health and network status

## API Endpoints

- `POST /transactions/build` - Build unsigned transaction
- `POST /transactions/simulate` - Simulate transaction effects
- `POST /transactions/submit` - Submit signed transaction
- `GET /health` - Service health check

## Configuration

### Environment Variables

- `ALGORAND_NETWORK` - Network to use (testnet/mainnet, default: testnet)
- `ALGORAND_ALGOD` - Algod server URL
- `ALGORAND_TOKEN` - Algod API token
- `ALGORAND_INDEXER` - Indexer server URL (optional)
- `READ_ONLY` - Enable read-only mode (default: false)
- `ALLOW_MAINNET` - Allow mainnet operations (default: false)

### Network Configuration

```json
{
  "default": "testnet",
  "supported": ["testnet", "mainnet"],
  "mainnet_warning": "Mainnet operations require explicit confirmation"
}
```

### Security Settings

- **Mainnet Gate**: Prevents accidental mainnet operations
- **Read-Only Mode**: Disables all write operations when enabled
- **Input Validation**: All transaction parameters are validated

## Development

### Local Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The service will run on port 3001 by default.

### Docker

```bash
# Build Docker image
docker build -t algorand-writer-mcp .

# Run container
docker run -p 3001:3001 algorand-writer-mcp
```

## Usage Examples

### Build Payment Transaction

```bash
curl -X POST "http://localhost:3001/transactions/build" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAddress": "SENDER_ADDRESS",
    "toAddress": "RECIPIENT_ADDRESS",
    "microAlgos": 100000,
    "note": "Payment memo"
  }'
```

### Simulate Transaction

```bash
curl -X POST "http://localhost:3001/transactions/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "unsignedTxnBase64": "BASE64_ENCODED_UNSIGNED_TRANSACTION"
  }'
```

### Submit Signed Transaction

```bash
curl -X POST "http://localhost:3001/transactions/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "signedTxnBase64": "BASE64_ENCODED_SIGNED_TRANSACTION"
  }'
```

## Transaction Flow

### Standard Transaction Process

1. **Build Transaction**: Use `build_payment_tx` to create unsigned transaction
2. **Simulate (Optional)**: Use `simulate_raw_tx` to test effects
3. **Sign Client-Side**: Sign the transaction with your wallet
4. **Submit**: Use `submit_signed_tx` to broadcast to network

### Example Flow

```javascript
// 1. Build unsigned transaction
const buildResponse = await fetch('/transactions/build', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    fromAddress: 'SENDER_ADDRESS',
    toAddress: 'RECIPIENT_ADDRESS',
    microAlgos: 100000,
    note: 'Test payment'
  })
});

// 2. Simulate transaction (optional)
const simResponse = await fetch('/transactions/simulate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    unsignedTxnBase64: buildResponse.unsignedTxn
  })
});

// 3. Sign transaction client-side (with your wallet)
// const signedTxn = await wallet.signTransaction(unsignedTxn);

// 4. Submit signed transaction
const submitResponse = await fetch('/transactions/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    signedTxnBase64: signedTxnBase64
  })
});
```

## Security

- **No Private Keys**: Service never handles or stores private keys
- **Client-Side Signing**: All signing happens on the client side
- **Mainnet Protection**: Explicit confirmation required for mainnet
- **Input Validation**: All parameters are validated before processing
- **Rate Limiting**: Protection against abuse
- **Read-Only Mode**: Can disable all write operations

## Supported Transaction Types

- **Payment**: Basic Algo transfers between accounts
- **Asset Transfer**: Transfer of Algorand Standard Assets (ASAs)
- **Asset Configuration**: Create and configure ASAs
- **Application Calls**: Smart contract interactions

## Production Deployment

The service is designed for production use with:
- Comprehensive health checks
- Proper error handling and logging
- Security controls and validation
- Support for both testnet and mainnet
- Mainnet protection mechanisms

## Monitoring

### Health Check Response

```json
{
  "status": "healthy",
  "network": "testnet",
  "mode": "write",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Support

For issues and questions:
- Check the manifest.json for complete API specification
- Review the health endpoint for service status
- Ensure proper network configuration
- Verify mainnet settings if using mainnet

## Version

Current version: 0.1.1

## License

See LICENSE file for details.