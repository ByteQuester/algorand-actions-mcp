# MCP API Reference for Algorand Lending Demo

This document provides comprehensive documentation for the Algorand MCP services used in the lending demo infrastructure.

## Services Overview

### Remote MCP Service (Read Operations)
- **URL**: `http://localhost:8002`
- **Purpose**: Query blockchain state, account information, transactions
- **Documentation**: http://localhost:8002/docs

### Actions MCP Service (Write Operations)
- **URL**: `http://localhost:3001`
- **Purpose**: Build, sign, and submit transactions
- **Documentation**: http://localhost:3001/docs

## Remote MCP Service Endpoints (Port 8002)

### Health Check
```http
GET /health
```
Returns service health status.

### Account Information
```http
POST /tools/get-account-info
Content-Type: application/json

{
  "address": "ALGORAND_ADDRESS"
}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "address": "MYZFY5XANQ3HN2YCS2XNOQIWL5PANXL35EV3YKBN5R5A6Y4TT43ZU3WZYM",
    "amount": 10000000,
    "assets": [],
    "round": 12345,
    "status": "Online"
  }
}
```

**Usage for Lending:**
- Check borrower creditworthiness (account balance, assets)
- Verify lender has sufficient funds
- Monitor collateral accounts

### Asset Information
```http
POST /tools/get-asset-info
Content-Type: application/json

{
  "asset_id": "123456"
}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "index": 123456,
    "name": "Test Token",
    "unit-name": "TST",
    "decimals": 6,
    "total": 1000000000000,
    "creator": "CREATOR_ADDRESS"
  }
}
```

**Usage for Lending:**
- Validate collateral assets
- Check asset supply and liquidity
- Verify asset creator and metadata

### Transaction Search
```http
POST /tools/search-transactions
Content-Type: application/json

{
  "address": "ALGORAND_ADDRESS",
  "limit": 10,
  "txn-type": "pay"
}
```

**Usage for Lending:**
- Audit loan payment history
- Verify collateral movements
- Track liquidation events

### Block Information
```http
POST /tools/get-block
Content-Type: application/json

{
  "round": 12345
}
```

**Usage for Lending:**
- Timestamp verification for loans
- Block-based interest calculations
- System synchronization

## Actions MCP Service Endpoints (Port 3001)

### Health Check
```http
GET /health
```
Returns service health status.

### Build Payment Transaction
```http
POST /tools/build-payment-tx
Content-Type: application/json

{
  "fromAddress": "SENDER_ADDRESS",
  "toAddress": "RECEIVER_ADDRESS",
  "microAlgos": 1000000,
  "note": "Optional transaction note"
}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "unsignedTxnBase64": "BASE64_ENCODED_TRANSACTION",
    "txnId": "TRANSACTION_ID_WHEN_SIGNED"
  }
}
```

**Usage for Lending:**
- Create loan disbursement transactions
- Build repayment transactions
- Generate collateral transfer transactions

### Simulate Transaction
```http
POST /tools/simulate-raw-tx
Content-Type: application/json

{
  "unsignedTxnBase64": "BASE64_ENCODED_UNSIGNED_TRANSACTION"
}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "would-succeed": true,
    "cost": 1000,
    "logs": []
  }
}
```

**Usage for Lending:**
- Test loan transactions before signing
- Validate smart contract interactions
- Estimate transaction costs

### Submit Signed Transaction
```http
POST /tools/submit-signed-tx
Content-Type: application/json

{
  "signedTxnBase64": "BASE64_ENCODED_SIGNED_TRANSACTION"
}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "txId": "TRANSACTION_ID"
  }
}
```

**Usage for Lending:**
- Submit loan disbursements
- Execute repayments
- Process liquidations

## Lending Demo Integration Patterns

### 1. Loan Origination Flow
```python
# 1. Check borrower account
borrower_info = await remote_client.call_tool(
    "get-account-info",
    {"address": borrower_address}
)

# 2. Build loan disbursement transaction
loan_txn = await actions_client.call_tool(
    "build-payment-tx",
    {
        "fromAddress": lender_address,
        "toAddress": borrower_address,
        "microAlgos": loan_amount,
        "note": f"Loan #{loan_id}"
    }
)

# 3. Sign and submit
# (signing handled by client-side wallet)
result = await actions_client.call_tool(
    "submit-signed-tx",
    {"signedTxnBase64": signed_transaction}
)
```

### 2. Repayment Tracking
```python
# Monitor repayments
transactions = await remote_client.call_tool(
    "search-transactions",
    {
        "address": borrower_address,
        "txn-type": "pay",
        "limit": 50
    }
)

# Filter for loan repayments
repayments = filter_loan_transactions(transactions, loan_id)
```

### 3. Collateral Verification
```python
# Check collateral assets
account_info = await remote_client.call_tool(
    "get-account-info",
    {"address": collateral_address}
)

collateral_assets = account_info["data"]["assets"]
for asset in collateral_assets:
    asset_info = await remote_client.call_tool(
        "get-asset-info",
        {"asset_id": asset["asset-id"]}
    )
    # Validate asset value and liquidity
```

## Error Handling

Both services return consistent error responses:

```json
{
  "success": false,
  "error": "Error message",
  "details": ["Additional error details"]
}
```

Common error scenarios:
- **400 Bad Request**: Invalid parameters or malformed addresses
- **500 Internal Server Error**: Network issues or node problems
- **Timeout**: Slow network or heavy blockchain load

## Security Considerations

### Private Key Management
- **Never** send private keys to MCP services
- Sign transactions client-side using algosdk
- Use environment variables for test private keys
- Implement proper key rotation in production

### Transaction Validation
- Always simulate transactions before submitting
- Verify transaction parameters match expectations
- Check account balances before attempting transfers
- Validate asset IDs and amounts

### Network Configuration
- Services are configured for Algorand testnet
- Testnet ALGOs have no monetary value
- Use appropriate endpoints for mainnet deployment

## Test Wallets

Generated test wallets for demo:

```json
{
  "lender": {
    "name": "Lender Wallet",
    "address": "MYZFY5XANQ3HN2YCS2XNOQIWL5PANXL35EV3YKBN5R5A6Y4TT43ZU3WZYM"
  },
  "borrower": {
    "name": "Borrower Wallet",
    "address": "CRMMBMPQ7VZISVJCHBCR2T4OUZ5634FXP6BX3BLOBVXB6ZK44IF6CGMLPI"
  },
  "liquidity_provider": {
    "name": "Liquidity Provider Wallet",
    "address": "DCZRXVVPPAKVGNFHUGMTQWJHCIROOVQPHHIRM562I2WYPWXVNKISCK2DK4"
  }
}
```

**Funding Instructions:**
1. Go to https://bank.testnet.algorand.network/
2. Complete recaptcha verification
3. Fund each address with at least 10 ALGO
4. Run integration tests to verify setup

## Quick Start Testing

1. **Run Integration Tests:**
   ```bash
   cd /home/mpo/algorand-showcase
   source venv-adk/bin/activate
   python test-integration.py
   ```

2. **Check Service Health:**
   ```bash
   curl http://localhost:8002/health
   curl http://localhost:3001/health
   ```

3. **Query Test Wallet:**
   ```bash
   curl -X POST http://localhost:8002/tools/get-account-info \
     -H "Content-Type: application/json" \
     -d '{"address": "MYZFY5XANQ3HN2YCS2XNOQIWL5PANXL35EV3YKBN5R5A6Y4TT43ZU3WZYM"}'
   ```

## Troubleshooting

### Service Not Responding
- Check if services are running: `netstat -tlnp | grep -E ":(8002|3001)"`
- Restart services: `./start-testnet-services.sh`
- Check logs for error messages

### Transaction Failures
- Verify account has sufficient balance (min 0.1 ALGO for fees)
- Check transaction parameters (addresses, amounts)
- Ensure proper transaction signing
- Validate network connectivity to Algorand testnet

### Wallet Issues
- Confirm addresses are valid Algorand addresses
- Verify private keys match addresses
- Check testnet faucet funding status
- Re-run wallet generation if needed

## Production Considerations

When deploying to production:

1. **Use Mainnet Endpoints**: Update service configuration for mainnet
2. **Implement Authentication**: Add proper API authentication
3. **Rate Limiting**: Implement request rate limiting
4. **Monitoring**: Add comprehensive logging and monitoring
5. **Key Management**: Use proper key management solutions (HSM, KMS)
6. **Backup and Recovery**: Implement wallet backup and recovery procedures

---

**Generated for Algorand Lending Demo Testing Infrastructure**
*Last Updated: September 14, 2025*