### Actions MCP — Debugging Log (Simulation Path)

This document records the exact steps, payloads, server edits, and outcomes while bringing up the non‑custodial Actions MCP.

#### Endpoints
- Base: `https://algorand-actions-mcp.<subdomain>.workers.dev`
- `/health` → `{ status:"ok", mode:"ACTIONS", network:"testnet" }`
- `/capabilities` → `{ tools:["build_payment_tx","simulate_raw_tx","submit_signed_tx"], network }`
- `/sse` (GET, streaming) → first event `data: /sse/message?sessionId=...`
- `/sse/message?sessionId=...` (POST) → accepts JSON-RPC 2.0 requests; responses stream back on `/sse`

#### JSON-RPC payloads
- List tools
```json
{ "jsonrpc":"2.0", "id":"1", "method":"tools/list", "params":{} }
```
- Build unsigned payment
```json
{
  "jsonrpc":"2.0","id":"2","method":"tools/call",
  "params":{ "name":"build_payment_tx", "arguments":{
    "fromAddress":"<FROM>", "toAddress":"<TO>", "microAlgos":100000, "note":"hello"
  }}
}
```
- Simulate unsigned tx
```json
{
  "jsonrpc":"2.0","id":"3","method":"tools/call",
  "params":{ "name":"simulate_raw_tx", "arguments":{
    "unsignedTxnBase64":"<paste-from-build>"
  }}
}
```
- Submit signed tx
```json
{
  "jsonrpc":"2.0","id":"4","method":"tools/call",
  "params":{ "name":"submit_signed_tx", "arguments":{
    "signedTxnBase64":"<signed-bytes-base64>"
  }}
}
```

#### Interaction flow (terminal)
1) Open SSE and keep it open:
```bash
curl -sN https://algorand-actions-mcp.<subdomain>.workers.dev/sse
# Copy: data: /sse/message?sessionId=...
```
2) POST JSON-RPC to the session path:
```bash
curl -s -X POST -H 'Content-Type: application/json' \
  "https://algorand-actions-mcp.<subdomain>.workers.dev/sse/message?sessionId=<ID>" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'
```
3) Build → Simulate → (Sign) → Submit

---

### Issues Encountered and Fix Attempts

1) SSE basics / capabilities
   - Fixed SSE to use `serveSSE`, added `/capabilities`. Verified headers `text/event-stream`.

2) Initial simulation attempts
   - Error: `r.get_obj_for_encoding is not a function`
   - Cause: Using SDK transaction instance methods in Workers runtime created brittle paths.

3) Wrap unsigned as SignedTransaction (msgpack)
   - Attempted `{ txn: <decoded-unsigned-obj> }` and with empty `sig`.
   - Error persisted.

4) Reconstruct Transaction and encode signed
   - Used `Transaction.from_obj_for_encoding` → `encodeSignedTransaction(txn, emptySig)`.
   - Still failed downstream after posting to simulate.

5) Direct fetch to Algonode simulate endpoint (JSON)
   - POST `txn-groups: [{ txns: [{ txn: <base64> }] }]`, `allow-empty-signatures:true`.
   - Response: `400 failed to decode object: json decode error [pos 32]: only encoded map or array can be decoded into a struct`.

#### Current Hypothesis
- The simulate endpoint expects a specific signed-transaction msgpack layout and/or field name shape.
- Our `txn` base64 likely does not match the exact SignedTxn structure expected (either signature handling, or envelope field mismatch).
- Alternatively, the provider expects `stxns` (array of fully signed msgpack blobs) instead of `txn-groups` JSON; needs verification against the node version.

#### Next Investigation Tasks (for assigned agent)
- Confirm current node’s simulate API contract: required fields and accepted shapes.
- Produce a known-good control by signing a trivial testnet txn with a disposable key and posting to `/v2/transactions/simulate` (outside the Worker). Capture exact JSON and base64 payload.
- Compare decoded structures (msgpack decode both our payload and the control) to identify structural differences.
- Adjust Worker to send the precise accepted shape (e.g., `stxns:[<base64>]` or correct group wrapper).

#### Known Good Checkpoints
- `/health` returns testnet ACTIONS mode.
- `/capabilities` lists tools.
- `/sse` emits `endpoint` and streams responses.

#### Notes
- All tool calls are JSON-RPC 2.0 via `tools/call`.
- Keep SSE session open; POSTs return 202 and stream results on SSE.


