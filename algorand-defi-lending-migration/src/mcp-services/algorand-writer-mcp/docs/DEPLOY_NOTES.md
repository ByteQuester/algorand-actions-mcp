# Deploy Notes

Goal: provide build/simulate/submit tools on TestNet with no key custody; safe for public use.
## Prerequisites
- Cloudflare account with Workers enabled
- Wrangler CLI logged in: `npx wrangler login`

## Environment
Default values are in `wrangler.jsonc`:
```
ALGORAND_NETWORK=testnet
ALGORAND_ALGOD=https://testnet-api.algonode.cloud
ALGORAND_INDEXER=https://testnet-idx.algonode.cloud
READ_ONLY=false
ALLOW_MAINNET=false
```

## Deploy
```bash
npm run deploy
# Outputs the public URL, e.g. https://algorand-actions-mcp.<subdomain>.workers.dev
```

## Smoke Test
- Health:
```bash
curl -s https://<host>/health
```
- SSE:
```bash
curl -sN https://<host>/sse
```
- Use returned session to POST JSON-RPC requests for tools.

## Notes
- Simulation uses Algonode testnet by default.
- Mainnet is disabled unless `ALLOW_MAINNET=true` and `ALGORAND_NETWORK=mainnet`.


