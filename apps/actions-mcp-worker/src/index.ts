import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { Buffer } from "buffer";
import { BaseEnv } from "@algorand-showcase/types";
import { isTrue, parseNetwork } from "@algorand-showcase/config";
import { AlgodClientWrapper } from "@algorand-showcase/algorand-clients";
import {
  createHealthResponse,
  createCapabilitiesResponse,
  shouldAllowMainnet,
  createMainnetGateResponse,
} from "@algorand-showcase/mcp-core";

type State = Record<string, unknown>;
type Props = Record<string, unknown>;

export class AlgorandActionsMCP extends McpAgent<BaseEnv, State, Props> {
  server = new McpServer({ name: "Algorand Actions MCP", version: "0.1.0" });
  initialState: State = {};

  async init() {
    const readOnlyFlag = isTrue(this.env.READ_ONLY);
    if (readOnlyFlag) {
      // In this Actions worker, READ_ONLY simply disables all tools
      this.registerReadOnlyStubs();
      return;
    }

    this.registerPaymentTools();
  }

  private registerReadOnlyStubs() {
    const unavailable = async () => ({ content: [{ type: "text", text: "unavailable in read-only mode" }] });
    this.server.tool("build_payment_tx", "Build unsigned payment txn (disabled)", { fromAddress: z.string(), toAddress: z.string(), microAlgos: z.number(), note: z.string().optional() }, unavailable);
    this.server.tool("simulate_raw_tx", "Simulate raw txn (disabled)", { unsignedTxnBase64: z.string() }, unavailable);
    this.server.tool("submit_signed_tx", "Submit signed txn (disabled)", { signedTxnBase64: z.string() }, unavailable);
  }

  private registerPaymentTools() {
    const algodUrl = this.env.ALGORAND_ALGOD || (parseNetwork(this.env.ALGORAND_NETWORK) === "testnet" ? "https://testnet-api.algonode.cloud" : "https://mainnet-api.algonode.cloud");
    const algodClient = new AlgodClientWrapper({ algodUrl, network: parseNetwork(this.env.ALGORAND_NETWORK) });

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
        const result = await algodClient.buildPaymentTransaction({
          from: fromAddress,
          to: toAddress,
          amount: microAlgos,
          note,
        });
        if (result.success) {
          return { content: [{ type: "text", text: JSON.stringify({ unsignedTxnBase64: result.data }) }] };
        } else {
          return { content: [{ type: "text", text: `error: ${result.error.message}` }] };
        }
      }
    );

    // simulate_raw_tx
    this.server.tool(
      "simulate_raw_tx",
      "Simulate an unsigned raw transaction",
      { unsignedTxnBase64: z.string() },
      async ({ unsignedTxnBase64 }) => {
        const result = await algodClient.simulateTransaction(unsignedTxnBase64);
        if (result.success) {
          return { content: [{ type: "text", text: JSON.stringify({ ok: true, raw: result.data }) }] };
        } else {
          return { content: [{ type: "text", text: JSON.stringify({ ok: false, message: result.error.message }) }] };
        }
      }
    );

    // submit_signed_tx (broadcast only)
    this.server.tool(
      "submit_signed_tx",
      "Broadcast a signed transaction",
      { signedTxnBase64: z.string() },
      async ({ signedTxnBase64 }) => {
        const result = await algodClient.submitTransaction(signedTxnBase64);
        if (result.success) {
          return { content: [{ type: "text", text: JSON.stringify(result.data) }] };
        } else {
          return { content: [{ type: "text", text: JSON.stringify({ error: result.error.message }) }] };
        }
      }
    );
  }
}

export default {
  fetch(request: Request, env: BaseEnv, ctx: ExecutionContext) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return new Response(JSON.stringify(createHealthResponse(env, isTrue(env.READ_ONLY) ? "READ-only" : "actions")), { status: 200, headers: { "content-type": "application/json" } });
    }

    if (url.pathname === "/capabilities") {
      const tools = ["build_payment_tx", "simulate_raw_tx", "submit_signed_tx"];
      return new Response(JSON.stringify(createCapabilitiesResponse(tools, parseNetwork(env.ALGORAND_NETWORK))), { status: 200, headers: { "content-type": "application/json" } });
    }

    if (url.pathname === "/sse" || url.pathname === "/sse/message" || url.pathname === "/mcp") {
      if (!shouldAllowMainnet(env)) {
        return createMainnetGateResponse();
      }
      // Use SSE transport to ensure streaming behavior
      return AlgorandActionsMCP.serveSSE("/sse", { binding: "AlgorandActionsMCP" }).fetch(request, env as any, ctx);
    }

    return new Response("Not found", { status: 404 });
  },
};


