### Deploy Notes — Algorand Actions MCP (Non‑custodial)

Goal: provide build/simulate/submit tools on TestNet with no key custody; safe for public use.

#### Env (wrangler.jsonc)
- `ALGORAND_NETWORK=testnet`
- `ALGORAND_ALGOD=https://testnet-api.algonode.cloud`
- `ALGORAND_INDEXER=https://testnet-idx.algonode.cloud`
- `READ_ONLY=false`
- `ALLOW_MAINNET=false`

#### Deploy
```bash
npm i
npx wrangler deploy --config wrangler.jsonc --minify
```

#### Verify
```bash
curl -s https://<your-workers-subdomain>.workers.dev/health | jq
curl -sI https://<your-workers-subdomain>.workers.dev/sse | grep -i content-type
```

#### Example MCP calls (agent)
1) Build unsigned payment tx (100k µAlgos):
```json
{ "tool": "build_payment_tx", "args": { "fromAddress": "<FROM>", "toAddress": "<TO>", "microAlgos": 100000, "note": "hello" } }
```
2) Simulate unsigned tx:
```json
{ "tool": "simulate_raw_tx", "args": { "unsignedTxnBase64": "<from step 1>" } }
```
3) Sign in wallet → submit signed bytes:
```json
{ "tool": "submit_signed_tx", "args": { "signedTxnBase64": "<signed bytes base64>" } }
```

#### Mainnet toggle (optional, not recommended for public endpoints)
Set `ALGORAND_NETWORK=mainnet` and `ALLOW_MAINNET=true`. The Worker will still enforce a warning contract at the tool level (clients should require explicit confirmation).


