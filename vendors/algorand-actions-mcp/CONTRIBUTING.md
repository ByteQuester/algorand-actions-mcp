# Contributing

Thanks for your interest in contributing! Please follow these guidelines:

## Getting Started
- Node >= 18, npm >= 9
- Install deps: `npm i`
- Local dev: `npx wrangler dev --config wrangler.jsonc --port 8788`

## Development
- This Worker exposes `/sse`, `/health`, and `/capabilities`.
- Tools (JSON-RPC via SSE): `build_payment_tx`, `simulate_raw_tx`, `submit_signed_tx`.
- Simulation uses `algosdk.encodeUnsignedSimulateTransaction` + `simulateRawTransactions`.

## Pull Requests
- Open an issue first for significant changes
- Keep PRs focused and small; add tests where reasonable
- Ensure docs are updated (`README.md`, `docs/`)

## Reporting Issues
- Include reproduction steps (SSE payloads), expected/actual behavior, and logs

## License
- By contributing, you agree that your contributions will be licensed under the MIT License.
