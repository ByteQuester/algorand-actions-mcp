### Local Read-Only Development

Goal: run without secrets, wallet, or OAuth/Vault. Only read APIs and utilities.

Environment variables (already set in `wrangler.jsonc`):
- `ALGORAND_NETWORK=mainnet`
- `ALGORAND_ALGOD=https://mainnet-api.algonode.cloud`
- `ALGORAND_INDEXER=https://mainnet-idx.algonode.cloud`
- `NFD_API_URL=https://api.nf.domains`
- `READ_ONLY=true`

Steps:
1) Install dependencies
   - `npm install`
2) Run local dev server
   - `npx wrangler dev --port 8787`
3) Connect an MCP client
   - `npx mcp-remote http://localhost:8787/sse`
4) Sanity checks
   - `/sse` responds
   - Tools list contains api_* and utility/knowledge
   - Wallet/transaction/signing tools are NOT listed

Notes:
- READ_ONLY mode bypasses OAuth/Vault paths and skips wallet/transaction tool registration.
- Knowledge tools will degrade gracefully if R2 `PLAUSIBLE_AI` is not bound in dev.


### Production Read-Only Deployment (workers.dev)

- Deployed URL: replace with your workers.dev URL, e.g.: `https://algorand-remote-mcp.mehrdad-touraji.workers.dev`
- Health endpoint (browser-friendly): `/health` returns `{"status":"ok","mode":"READ_ONLY"}`
- SSE endpoint (for MCP clients): `/sse` (blank in browser by design; it streams)

Deploy (no KV/DO extras):
```bash
npm i
npx wrangler deploy --minify --config wrangler.readonly.jsonc
```

If deploy fails with “KV namespace not found”, use the read-only config above, or remove KV bindings. If it fails with “workers.dev subdomain” error, open Cloudflare Dashboard → Workers once.

### Quick Usage via MCP Client

Connect:
```bash
npx -y mcp-remote https://algorand-remote-mcp.<your-subdomain>.workers.dev/sse
```
Then at the prompt:
```text
tools
call api_nfd_get_nfd {"name":"emg110.algo","view":"brief"}
call api_indexer_lookup_account_by_id {"address":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"}
call api_algod_get_account_info {"address":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"}
```

Expected behavior:
- First connect may show a 404 on POST and then auto-fallback to SSE; that is normal.
- `/sse` is a streaming endpoint; in a browser it appears blank and loading. Use `/health` for a browser check.

### Findings and Gotchas
- Opening `/sse` in a browser looks “blank” by design (SSE stream). Use `/health` instead.
- If Wrangler dev fails locally due to glibc, use `wrangler.readonly.jsonc` in CI or deploy from another host.
- READ_ONLY gating hides wallet/signing tools and registers only read APIs (algod, indexer, NFD), utilities, and knowledge.




