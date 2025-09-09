# Algorand NFD + Account Explorer (MCP Showcase)

A lightweight, portfolio-friendly showcase that surfaces Algorand account and NFD (Algorand Name Service) data, and is scaffolded to integrate with the Algorand Remote MCP server.

This repo emphasizes clarity over complexity: a few small scripts, a simple environment file, and ready-to-use commands that work with a local node or public endpoints. It pairs well with the remote MCP server to expose rich tools for AI agents.

## Features

- NFD lookup script for quick name-to-address and profile lookups
- Account summary script (against local algod or a public Indexer)
- One-command node status check (catchup progress, rounds)
- Ready to integrate with remote MCP for expanded capabilities

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
   ```bash
   ./scripts/account_summary.sh "ADDRESS_OR_NFD"
   # Uses INDEXER_URL if set; otherwise falls back to local algod
   ```

## Remote MCP (optional)

This scaffold includes the Algorand Remote MCP server as a git submodule under `vendors/algorand-remote-mcp`. It exposes a comprehensive toolset (Indexer/algod/NFD/TEAL/tx ops). See the project for details:

- Algorand Remote MCP: [algorand-remote-mcp](https://github.com/ByteQuester/algorand-remote-mcp)

You can deploy the Worker later (e.g., with Wrangler). For a quick portfolio demo, the included scripts are sufficient.

## Environment

See `.env.example` for defaults. Common settings:

- `ALGOD_ADDR` (default `http://127.0.0.1:8080`)
- `ALGOD_TOKEN_FILE` (default `/var/lib/algorand/algod.token`)
- `INDEXER_URL` (e.g. `https://mainnet-idx.algonode.cloud`)
- `NFD_API_URL` (default `https://api.nf.domains`)

## License

MIT


