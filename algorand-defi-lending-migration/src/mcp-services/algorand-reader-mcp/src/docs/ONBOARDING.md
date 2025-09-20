### Algorand Remote MCP — Onboarding (From Zero to First Tool Call)

This guide walks a newcomer from “what is this?” to successfully calling tools from the deployed Algorand Remote MCP Worker.

The deployed Worker URL you provided:

- SSE endpoint: `https://algorand-remote-mcp.mehrdad-touraji.workers.dev/sse`

Notes:
- The server runs in READ_ONLY mode (no wallet custody, signing, or transaction submission). Agents can use read-safe tools (algod/indexer/NFD utilities, knowledge, etc.).
- In the current production setup, `/health` may not respond with JSON; use the SSE check to validate availability.

---

### TL;DR Quick Start

1) Verify SSE is up:
```bash
curl -s -m 3 -o /dev/null -w "%{http_code} %{content_type}\n" \
  https://algorand-remote-mcp.mehrdad-touraji.workers.dev/sse
# Expect: 200 text/event-stream
```

2) Connect a client (Cursor/Claude) via MCP servers config:
```json
{
  "mcpServers": {
    "algorand-remote-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://algorand-remote-mcp.mehrdad-touraji.workers.dev/sse"
      ]
    }
  }
}
```

3) Ask your agent (in the IDE/app): “List Algorand MCP tools” and then call a read tool like `api_indexer_lookup_account_by_id`.

---

### What is Algorand Remote MCP?

- A Model Context Protocol (MCP) server that exposes Algorand read APIs and utilities via tools an AI agent can call.
- Deployed on Cloudflare Workers and accessed via SSE (`/sse`).
- READ_ONLY mode means: wallet/sign/submit endpoints are stubbed and return a clear “unavailable in read-only mode” message.

---

### Prerequisites (Local Testing Optional)

- Node.js v18+ (v16+ often works, but v18+ recommended)
- `npx` available (bundled with Node.js)

You do NOT need keys, Vault, or OAuth to use read-only tools.

---

### Environment and Mode (for reference)

Current production env (as shared):
- `ALGORAND_NETWORK=mainnet`
- `ALGORAND_ALGOD=https://mainnet-api.algonode.cloud`
- `ALGORAND_INDEXER=https://mainnet-idx.algonode.cloud`
- `READ_ONLY=true`

Implications:
- Agents can call read-only tools safely (no secrets required).
- Wallet/sign/submit tools are present only as disabled stubs.

Switching to TestNet (optional): set `ALGORAND_NETWORK=testnet`, `ALGORAND_ALGOD=https://testnet-api.algonode.cloud`, `ALGORAND_INDEXER=https://testnet-idx.algonode.cloud` in Cloudflare Worker variables; redeploy.

---

### Validate Availability

- SSE check (authoritative):
```bash
curl -s -m 3 -o /dev/null -w "%{http_code} %{content_type}\n" \
  https://algorand-remote-mcp.mehrdad-touraji.workers.dev/sse
# Expect: 200 text/event-stream
```

- Health (optional): In this production config, `/health` may return 404; that is OK for agents because they connect via SSE.

---

### Connect From an Agent (Cursor/Claude/etc.)

Add this to your agent’s configuration (e.g., `settings.json` or equivalent):
```json
{
  "mcpServers": {
    "algorand-remote-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://algorand-remote-mcp.mehrdad-touraji.workers.dev/sse"
      ]
    }
  }
}
```

Then restart the agent or the IDE. Prompt the agent to “list Algorand MCP tools” or ask it to run a specific tool call.

What to expect on first connect:
- A 404 on POST with fallback to SSE is normal (client auto-switches transport and then streams).
- The SSE endpoint appears "blank" in a browser; that’s expected for a streaming connection.

---

### Example Tool Calls (Read-Only)

Ask your agent to invoke these tools:

- Validate an address:
```json
{
  "tool": "validate_address",
  "args": { "address": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ" }
}
```

- Look up an account via Indexer:
```json
{
  "tool": "api_indexer_lookup_account_by_id",
  "args": { "address": "<REPLACE_WITH_AN_ACCOUNT_ADDRESS>" }
}
```

- Get account info via algod:
```json
{
  "tool": "api_algod_get_account_info",
  "args": { "address": "<REPLACE_WITH_AN_ACCOUNT_ADDRESS>" }
}
```

- Fetch an NFD record:
```json
{
  "tool": "api_nfd_get_nfd",
  "args": { "name": "emg110.algo", "view": "brief" }
}
```

READ_ONLY stubs (expected responses):
- `sign_transaction`, `submit_transaction`, wallet-related tools → return “unavailable in read-only mode”.

---

### Local Development (Optional)

If you want to run a local dev Worker (read-only):
```bash
npm install
npx wrangler dev --port 8787
```

Then point your MCP client to `http://localhost:8787/sse` instead of the production URL.

---

### Troubleshooting

- SSE shows 200 but tools don’t appear in your agent:
  - Ensure your agent restarted after adding the `mcpServers` config.
  - Confirm the SSE URL is exactly `.../sse` (not the root URL).

- Browser shows a blank page at `/sse`:
  - That’s normal; it’s a streaming endpoint. Use the curl check above.

- `/health` is 404:
  - Expected in this production mode. Agents don’t rely on `/health`; they use SSE.

- First connect shows a POST 404 in logs:
  - Normal fallback behavior (HTTP-first → SSE-only).

- Rate limits or upstream errors:
  - Retry after a short backoff; public Algonode endpoints can throttle during bursts.

---

### Security & Limits (READ_ONLY)

- No secrets required; public Algonode endpoints are used for reads.
- No custody of keys; signing/submission are disabled in this mode.
- Keep requests small; avoid high-rate bursts to public endpoints.

---

### Metrics & Ops

- Review Cloudflare Worker metrics from the dashboard (production environment). Use your Worker’s metrics page for request rates, errors, and latency.

---

### When You Need Writes Later (Optional Next Step)

- Stand up a separate “Actions” Worker on TestNet to support:
  - Build unsigned transactions
  - Simulate
  - Submit signed (client-signed) transactions
- Keep READ_ONLY Worker as-is for public-safe reads.

---

### FAQ

- Q: Can I point multiple agents to the same SSE endpoint?
  - A: Yes. Each agent maintains its own streaming session.

- Q: Do I need an API token for Algonode?
  - A: Not for public endpoints used here. If you adopt a provider requiring tokens, add them as Worker vars.

- Q: How do I switch to TestNet?
  - A: Update the three env vars (`ALGORAND_NETWORK`, `ALGORAND_ALGOD`, `ALGORAND_INDEXER`) and redeploy.
