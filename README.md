# Algorand NFD + Account Explorer (MCP Showcase)


A lightweight and secure Model Context Protocol (MCP) designed to surface Algorand account data and NFD (Algorand Name Service) information. This MCP is scaffolded for integration with the Algorand Remote MCP server and serves as a complementary counterpart to the read-only [Algorand Remote MCP](https://github.com/ByteQuester/algorand-remote-mcp.git). While the read-only MCP is restricted to exposing on-chain data, this implementation adds scoped write and interaction capabilities, though limited to a curated set of tools for safety and simplicity. Used together, the two protocols provide a secure, extensible, and more complete framework for interacting with the Algorand ecosystem.


This repo emphasizes clarity over complexity: a few small scripts, a simple environment file, and ready-to-use commands that work with a local node or public endpoints. It pairs well with the remote MCP server to expose rich tools for AI agents.

## Features

- NFD lookup script for quick name-to-address and profile lookups
- Account summary script (against local algod or a public Indexer)
- One-command node status check (catchup progress, rounds)
- Ready to integrate with remote MCP for expanded capabilities
- Static web UI (no build tools): index.html + vanilla JS wired to public endpoints

## Requirements

- bash, curl
- Optional: a local Algorand node (mainnet) at 127.0.0.1:8080; token at `/var/lib/algorand/algod.token`

## Quickstart

1. Clone and configure env
   ```bash
   cd ~/algorand-showcase
   cp .env.example .env
   # adjust values in .env as needed
   ```

2. Node status (local node)
   ```bash
   ./scripts/status.sh
   ```

3. NFD lookup
   ```bash
   ./scripts/nfd_lookup.sh "nfd-name.algo"   # e.g. foundation.algo
   ```

4. Account summary
5. Open the static UI
   ```bash
   # Option A: serve locally with Python
   cd web && python3 -m http.server 8088
   # then open http://localhost:8088/

   # Option B: open file directly (may be restricted by browser CORS)
   # open web/index.html
   ```
   - Override endpoints via query params:
     - `?indexer=https://mainnet-idx.algonode.cloud&nfd=https://api.nf.domains`
   ```bash
   ./scripts/account_summary.sh "ADDRESS_OR_NFD"
   # Uses INDEXER_URL if set; otherwise falls back to local algod
   ```

## Remote MCP (optional)

This scaffold includes the Algorand Remote MCP server as a git submodule under `vendors/algorand-remote-mcp`. It exposes a comprehensive toolset (Indexer/algod/NFD/TEAL/tx ops). See the project for details:

- Algorand Remote MCP: [algorand-remote-mcp](https://github.com/ByteQuester/algorand-remote-mcp)

You can deploy the Worker later (e.g., with Wrangler). For a quick portfolio demo, the included scripts are sufficient.

## Deploying the static UI

- Any static host works (GitHub Pages, Cloudflare Pages, Netlify, S3+CloudFront).
- Publish the `web/` directory as-is. No build step required.

## Environment

See `.env.example` for defaults. Common settings:

- `ALGOD_ADDR` (default `http://127.0.0.1:8080`)
- `ALGOD_TOKEN_FILE` (default `/var/lib/algorand/algod.token`)
- `INDEXER_URL` (e.g. `https://mainnet-idx.algonode.cloud`)
- `NFD_API_URL` (default `https://api.nf.domains`)

## License

MIT


