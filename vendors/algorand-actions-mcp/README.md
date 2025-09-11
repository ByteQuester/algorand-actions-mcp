### Algorand Actions MCP (Non‑custodial)

Purpose: expose a minimal, safe toolset for agents to build, simulate, and submit Algorand transactions with client‑side signing. Defaults to TestNet; mainnet is disabled by default.

#### Tools
- `build_payment_tx` → { unsignedTxnBase64, txnIdPreview, network }
- `simulate_raw_tx` → { ok, fee?, suggestedParams?, message? }
- `submit_signed_tx` → { txId, explorerUrl, network }

#### Endpoints
- `/sse`: MCP streaming endpoint
- `/health`: { status, mode, network }

#### Defaults (wrangler.jsonc)
```
ALGORAND_NETWORK=testnet
ALGORAND_ALGOD=https://testnet-api.algonode.cloud
ALGORAND_INDEXER=https://testnet-idx.algonode.cloud
READ_ONLY=false
ALLOW_MAINNET=false
```

#### Run (local)
```bash
npm i
npx wrangler dev --config wrangler.jsonc --port 8788
# SSE: http://localhost:8788/sse
```

#### Connect from an agent
```json
{
  "mcpServers": {
    "algorand-actions-mcp": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8788/sse"]
    }
  }
}
```

#### Example flow
1) Build unsigned payment:
```json
{ "tool": "build_payment_tx", "args": { "fromAddress": "<FROM>", "toAddress": "<TO>", "microAlgos": 100000, "note": "hello" } }
```
2) Simulate:
```json
{ "tool": "simulate_raw_tx", "args": { "unsignedTxnBase64": "<from step 1>" } }
```
3) Sign client‑side (wallet) and submit:
```json
{ "tool": "submit_signed_tx", "args": { "signedTxnBase64": "<signed bytes base64>" } }
```

#### SSE quick test
- Open SSE and copy the session endpoint:
```bash
curl -sN https://algorand-actions-mcp.mehrdad-touraji.workers.dev/sse
```
- POST to the session endpoint returned above with JSON-RPC 2.0 messages for steps 1 and 2.

#### Simulation implementation notes
- The worker now uses `algosdk.encodeUnsignedSimulateTransaction(txn)` and calls `algod.simulateRawTransactions(bytes)`.
- For HTTP JSON simulate, it uses `txn-groups` and embeds a decoded SignedTxn object (not base64 strings).
- `stxns` request shape is not used (not supported by Algonode).
- If simulation fails, responses include `used.shape/impl` and provider body for diagnostics.

Notes:
- No key custody. We only build, simulate, and broadcast.
- Mainnet requires toggling `ALLOW_MAINNET=true` and `ALGORAND_NETWORK=mainnet` plus an explicit client confirmation.

#### Debugging log
- See `DEBUGGING.md` for a detailed, chronological log of issues, payloads, and fixes while bringing up simulation.


