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
import { ActionsHttpAdapter } from "./http-adapter.js";

export class AlgorandActionsMCP {
  server = new McpServer({ name: "Algorand Actions MCP", version: "0.1.0" });
  private env: BaseEnv;

  constructor(env: BaseEnv) {
    this.env = env;
  }

  async init() {
    const readOnlyFlag = isTrue(this.env?.READ_ONLY);
    if (readOnlyFlag) {
      // In this Actions worker, READ_ONLY simply disables all tools
      this.registerReadOnlyStubs();
      return;
    }

    this.registerPaymentTools();
  }

  private registerReadOnlyStubs() {
    const unavailable = async () => ({ 
      content: [{ 
        type: "text" as const, 
        text: "unavailable in read-only mode" 
      }] 
    });
    this.server.tool(
      "build_payment_tx", 
      "Build unsigned payment txn (disabled)", 
      { 
        fromAddress: z.string(), 
        toAddress: z.string(), 
        microAlgos: z.number(), 
        note: z.string().optional() 
      }, 
      unavailable
    );
    this.server.tool(
      "simulate_raw_tx", 
      "Simulate raw txn (disabled)", 
      { unsignedTxnBase64: z.string() }, 
      unavailable
    );
    this.server.tool(
      "submit_signed_tx", 
      "Submit signed txn (disabled)", 
      { signedTxnBase64: z.string() }, 
      unavailable
    );
  }

  private registerPaymentTools() {
    const env = this.env;
    const algodUrl = env?.ALGORAND_ALGOD || (parseNetwork(env?.ALGORAND_NETWORK) === "testnet" ? "https://testnet-api.algonode.cloud" : "https://mainnet-api.algonode.cloud");
    const algodClient = new AlgodClientWrapper({ algodUrl, network: parseNetwork(env?.ALGORAND_NETWORK) });

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
          return { content: [{ type: "text" as const, text: JSON.stringify({ unsignedTxnBase64: result.data }) }] };
        } else {
          return { content: [{ type: "text" as const, text: `error: ${result.error.message}` }] };
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
          return { content: [{ type: "text" as const, text: JSON.stringify({ ok: true, raw: result.data }) }] };
        } else {
          return { content: [{ type: "text" as const, text: JSON.stringify({ ok: false, message: result.error.message }) }] };
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
          return { content: [{ type: "text" as const, text: JSON.stringify(result.data) }] };
        } else {
          return { content: [{ type: "text" as const, text: JSON.stringify({ error: result.error.message }) }] };
        }
      }
    );
  }
}

export default {
  async fetch(request: Request, env: BaseEnv, ctx: any) {
    const url = new URL(request.url);

    // Legacy health endpoint (kept for backward compatibility)
    if (url.pathname === "/health") {
      return new Response(JSON.stringify(createHealthResponse(env, isTrue(env.READ_ONLY) ? "READ-only" : "actions")), { status: 200, headers: { "content-type": "application/json" } });
    }

    if (url.pathname === "/capabilities") {
      const tools = ["build_payment_tx", "simulate_raw_tx", "submit_signed_tx"];
      return new Response(JSON.stringify(createCapabilitiesResponse(tools, parseNetwork(env.ALGORAND_NETWORK))), { status: 200, headers: { "content-type": "application/json" } });
    }

    // SSE/MCP endpoints for existing clients
    if (url.pathname === "/sse" || url.pathname === "/sse/message" || url.pathname === "/mcp") {
      if (!shouldAllowMainnet(env)) {
        return createMainnetGateResponse();
      }
      // Create and initialize MCP server instance
      const mcpInstance = new AlgorandActionsMCP(env);
      await mcpInstance.init();
      // For now, return a placeholder - we need to implement proper MCP transport
      return new Response(JSON.stringify({ message: "MCP endpoint - transport implementation needed" }), {
        status: 501,
        headers: { "content-type": "application/json" }
      });
    }

    // HTTP REST API endpoints
    if (url.pathname.startsWith("/tools/") || url.pathname === "/metrics" || url.pathname === "/openapi.json" || url.pathname === "/docs" || url.pathname === "/swagger") {
      if (isTrue(env.READ_ONLY) && url.pathname !== "/tools/list" && url.pathname !== "/metrics") {
        return new Response(JSON.stringify({ error: "Service is in read-only mode" }), { 
          status: 503, 
          headers: { "content-type": "application/json" } 
        });
      }
      
      if (!shouldAllowMainnet(env) && url.pathname !== "/tools/list" && url.pathname !== "/metrics") {
        return new Response(JSON.stringify({ error: "Mainnet access not allowed" }), { 
          status: 403, 
          headers: { "content-type": "application/json" } 
        });
      }

      const httpAdapter = new ActionsHttpAdapter(env);
      return httpAdapter.handleRequest(request, env);
    }

    return new Response("Not found", { status: 404 });
  },
};


