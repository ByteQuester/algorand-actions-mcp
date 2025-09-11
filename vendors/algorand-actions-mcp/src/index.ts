import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import algosdk from "algosdk";
import * as msgpack from "algo-msgpack-with-bigint";
import { z } from "zod";

type Env = {
  ALGORAND_NETWORK?: string;
  ALGORAND_ALGOD?: string;
  ALGORAND_INDEXER?: string;
  READ_ONLY?: string | boolean;
  ALLOW_MAINNET?: string | boolean;
};

type State = Record<string, unknown>;
type Props = Record<string, unknown>;

function isTrue(v: any): boolean {
  return v === true || v === "true" || v === "1";
}

function getNetwork(env: Env): "testnet" | "mainnet" {
  const n = (env.ALGORAND_NETWORK || "testnet").toLowerCase();
  return n === "mainnet" ? "mainnet" : "testnet";
}

async function fetchSuggestedParams(algodUrl: string): Promise<algosdk.SuggestedParams> {
  const client = new algosdk.Algodv2("", algodUrl, "");
  return await client.getTransactionParams().do();
}

export class AlgorandActionsMCP extends McpAgent<Env, State, Props> {
  server = new McpServer({ name: "Algorand Actions MCP", version: "0.1.0" });
  initialState: State = {};

  async init() {
    const network = getNetwork(this.env);
    const readOnlyFlag = isTrue(this.env.READ_ONLY);
    if (readOnlyFlag) {
      // In this Actions worker, READ_ONLY simply disables all tools
      this.registerReadOnlyStubs();
      return;
    }

    this.registerHealthEndpoints();
    this.registerPaymentTools(network);
  }

  private registerReadOnlyStubs() {
    const unavailable = async () => ({ content: [{ type: "text", text: "unavailable in read-only mode" }] });
    this.server.tool("build_payment_tx", "Build unsigned payment txn (disabled)", { fromAddress: z.string(), toAddress: z.string(), microAlgos: z.number(), note: z.string().optional() }, unavailable);
    this.server.tool("simulate_raw_tx", "Simulate raw txn (disabled)", { unsignedTxnBase64: z.string() }, unavailable);
    this.server.tool("submit_signed_tx", "Submit signed txn (disabled)", { signedTxnBase64: z.string() }, unavailable);
  }

  private registerHealthEndpoints() {
    // no-op: route handled in default export fetch
  }

  private registerPaymentTools(network: "testnet" | "mainnet") {
    const algodUrl = this.env.ALGORAND_ALGOD || (network === "testnet" ? "https://testnet-api.algonode.cloud" : "https://mainnet-api.algonode.cloud");

    // build_payment_tx
    this.server.tool(
      "build_payment_tx",
      "Build an unsigned payment transaction",
      {
        fromAddress: z.string(),
        toAddress: z.string(),
        microAlgos: z.number().min(1000).max(50_000_000),
        note: z.string().optional(),
      },
      async ({ fromAddress, toAddress, microAlgos, note }) => {
        if (!algosdk.isValidAddress(fromAddress) || !algosdk.isValidAddress(toAddress)) {
          return { content: [{ type: "text", text: "invalid address" }] };
        }
        try {
          const params = await fetchSuggestedParams(algodUrl);
          const noteBytes = note ? new TextEncoder().encode(note.slice(0, 256)) : undefined;
          const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
            from: fromAddress,
            to: toAddress,
            amount: microAlgos,
            note: noteBytes,
            suggestedParams: params,
          });
          const unsignedTxnBase64 = Buffer.from(algosdk.encodeUnsignedTransaction(txn)).toString("base64");
          return {
            content: [{
              type: "text",
              text: JSON.stringify({ unsignedTxnBase64, txnIdPreview: txn.txID().slice(0, 16), network })
            }]
          };
        } catch (e: any) {
          return { content: [{ type: "text", text: `error: ${e?.message || "unknown"}` }] };
        }
      }
    );

    // simulate_raw_tx
    this.server.tool(
      "simulate_raw_tx",
      "Simulate an unsigned raw transaction",
      { unsignedTxnBase64: z.string() },
      async ({ unsignedTxnBase64 }) => {
        try {
          const client = new algosdk.Algodv2("", algodUrl, "");
          const unsignedBytes = Buffer.from(unsignedTxnBase64, "base64");

          // Decode msgpack object directly and wrap into a SignedTransaction structure { txn: <obj> }
          // This avoids relying on Transaction#get_obj_for_encoding and works in Workers runtime
          let stxnBase64: string;
          try {
            const unsignedObj = msgpack.decode(unsignedBytes) as any;
            const emptySig = new Uint8Array(64); // empty Ed25519 signature
            const stxnBytes = msgpack.encode({ sig: emptySig, txn: unsignedObj });
            stxnBase64 = Buffer.from(stxnBytes).toString("base64");
          } catch (_e) {
            // If decodeObj fails, assume caller already provided an stxn blob
            stxnBase64 = unsignedTxnBase64;
          }

          // Build SimulateRequest JSON (Algod expects JSON, not msgpack here)
          const req = {
            "txn-groups": [
              {
                txns: [
                  {
                    txn: stxnBase64,
                  },
                ],
              },
            ],
            "allow-empty-signatures": true,
            "allow-more-hash-failures": true,
          } as any;

          const endpoint = (algodUrl.endsWith('/') ? algodUrl.slice(0, -1) : algodUrl) + '/v2/transactions/simulate';
          const resp = await fetch(endpoint, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify(req)
          });
          if (!resp.ok) {
            const text = await resp.text();
            return { content: [{ type: 'text', text: JSON.stringify({ ok: false, status: resp.status, message: text }) }] };
          }
          const sim = await resp.json();
          const fee = sim?.txnGroups?.[0]?.txnResults?.[0]?.txnResult?.txn?.fee;
          return { content: [{ type: "text", text: JSON.stringify({ ok: true, fee, suggestedParams: undefined, raw: sim }) }] };
        } catch (e: any) {
          return { content: [{ type: "text", text: JSON.stringify({ ok: false, message: e?.message || "simulation failed" }) }] };
        }
      }
    );

    // submit_signed_tx (broadcast only)
    this.server.tool(
      "submit_signed_tx",
      "Broadcast a signed transaction",
      { signedTxnBase64: z.string() },
      async ({ signedTxnBase64 }) => {
        try {
          const client = new algosdk.Algodv2("", algodUrl, "");
          const bytes = new Uint8Array(Buffer.from(signedTxnBase64, "base64"));
          const res = await client.sendRawTransaction(bytes).do();
          const txId = res?.txId || res?.txid;
          const explorerBase = network === "testnet" ? "https://testnet.explorer.perawallet.app/tx/" : "https://explorer.perawallet.app/tx/";
          return { content: [{ type: "text", text: JSON.stringify({ txId, explorerUrl: `${explorerBase}${txId}`, network }) }] };
        } catch (e: any) {
          return { content: [{ type: "text", text: JSON.stringify({ error: e?.message || "broadcast failed" }) }] };
        }
      }
    );
  }
}

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);
    const network = getNetwork(env);
    const allowMainnet = isTrue(env.ALLOW_MAINNET);
    const explicitReadOnly = isTrue(env.READ_ONLY);

    if (url.pathname === "/health") {
      const mode = explicitReadOnly ? "READ_ONLY" : "ACTIONS";
      return new Response(JSON.stringify({ status: "ok", mode, network }), { status: 200, headers: { "content-type": "application/json" } });
    }

    if (url.pathname === "/capabilities") {
      const tools = ["build_payment_tx", "simulate_raw_tx", "submit_signed_tx"];
      return new Response(JSON.stringify({ tools, network }), { status: 200, headers: { "content-type": "application/json" } });
    }

    if (url.pathname === "/sse" || url.pathname === "/sse/message" || url.pathname === "/mcp") {
      // Gate mainnet usage
      if (network === "mainnet" && !allowMainnet) {
        return new Response(JSON.stringify({ error: "mainnet disabled" }), { status: 403, headers: { "content-type": "application/json" } });
      }
      // Use SSE transport to ensure streaming behavior
      return AlgorandActionsMCP.serveSSE("/sse", { binding: "AlgorandActionsMCP" }).fetch(request, env as any, ctx);
    }

    return new Response("Not found", { status: 404 });
  },
};


