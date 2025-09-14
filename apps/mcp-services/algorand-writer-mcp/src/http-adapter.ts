import { z } from "zod";
import { BaseEnv } from "@algorand-showcase/types";
import { parseNetwork } from "@algorand-showcase/config";
import { AlgodClientWrapper } from "@algorand-showcase/algorand-clients";
import { OpenAPIGenerator } from "@algorand-showcase/mcp-core";

const PaymentTxSchema = z.object({
  fromAddress: z.string(),
  toAddress: z.string(),
  microAlgos: z.number().min(1000).max(50_000_000),
  note: z.string().optional(),
});

const SimulateTxSchema = z.object({
  unsignedTxnBase64: z.string(),
});

const SubmitTxSchema = z.object({
  signedTxnBase64: z.string(),
});

export interface HttpAdapter {
  handleRequest(request: Request, env: BaseEnv): Promise<Response>;
}

export class ActionsHttpAdapter implements HttpAdapter {
  private algodClient: AlgodClientWrapper;
  
  constructor(private env: BaseEnv) {
    const algodUrl = env.ALGORAND_ALGOD || 
      (parseNetwork(env.ALGORAND_NETWORK) === "testnet" 
        ? "https://testnet-api.algonode.cloud" 
        : "https://mainnet-api.algonode.cloud");
    
    this.algodClient = new AlgodClientWrapper({ 
      algodUrl, 
      network: parseNetwork(env.ALGORAND_NETWORK) 
    });
  }

  async handleRequest(request: Request, env: BaseEnv): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Handle CORS
    if (request.method === "OPTIONS") {
      return this.corsResponse(new Response(null, { status: 204 }));
    }

    // Route requests
    switch (path) {
      case "/tools/list":
        return this.handleToolsList();
      case "/tools/build_payment":
        return this.handleBuildPayment(request);
      case "/tools/simulate":
        return this.handleSimulate(request);
      case "/tools/submit":
        return this.handleSubmit(request);
      case "/health":
        return this.handleHealth();
      case "/metrics":
        return this.handleMetrics();
      case "/openapi.json":
        return this.handleOpenAPISpec();
      case "/docs":
      case "/swagger":
        return this.handleSwaggerUI();
      default:
        return new Response(JSON.stringify({ error: "Not found" }), { status: 404 });
    }
  }

  private async handleToolsList(): Promise<Response> {
    const tools = [
      {
        name: "build_payment_tx",
        description: "Build an unsigned payment transaction",
        inputSchema: PaymentTxSchema.shape,
      },
      {
        name: "simulate_raw_tx",
        description: "Simulate an unsigned raw transaction",
        inputSchema: SimulateTxSchema.shape,
      },
      {
        name: "submit_signed_tx",
        description: "Broadcast a signed transaction",
        inputSchema: SubmitTxSchema.shape,
      },
    ];

    return this.jsonResponse({ tools });
  }

  private async handleBuildPayment(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = PaymentTxSchema.parse(body);

      const result = await this.algodClient.buildPaymentTransaction({
        from: parsed.fromAddress,
        to: parsed.toAddress,
        amount: parsed.microAlgos,
        note: parsed.note,
      });

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          unsignedTxnBase64: result.data 
        });
      } else {
        return this.jsonResponse(
          { success: false, error: result.error.message },
          400
        );
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        return this.jsonResponse(
          { success: false, error: "Invalid input", details: error.errors },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleSimulate(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = SimulateTxSchema.parse(body);

      const result = await this.algodClient.simulateTransaction(parsed.unsignedTxnBase64);

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          simulation: result.data 
        });
      } else {
        return this.jsonResponse(
          { success: false, error: result.error.message },
          400
        );
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        return this.jsonResponse(
          { success: false, error: "Invalid input", details: error.errors },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleSubmit(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = SubmitTxSchema.parse(body);

      const result = await this.algodClient.submitTransaction(parsed.signedTxnBase64);

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          txId: result.data 
        });
      } else {
        return this.jsonResponse(
          { success: false, error: result.error.message },
          400
        );
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        return this.jsonResponse(
          { success: false, error: "Invalid input", details: error.errors },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private handleHealth(): Response {
    return this.jsonResponse({
      status: "healthy",
      timestamp: new Date().toISOString(),
      network: parseNetwork(this.env.ALGORAND_NETWORK),
      readOnly: this.env.READ_ONLY === "true",
    });
  }

  private handleMetrics(): Response {
    // Basic Prometheus-style metrics
    const metrics = `
# HELP actions_mcp_up Actions MCP Worker is up
# TYPE actions_mcp_up gauge
actions_mcp_up 1

# HELP actions_mcp_info Actions MCP Worker info
# TYPE actions_mcp_info gauge
actions_mcp_info{network="${parseNetwork(this.env.ALGORAND_NETWORK)}",readonly="${this.env.READ_ONLY === "true"}"} 1
`.trim();

    return new Response(metrics, {
      headers: {
        "Content-Type": "text/plain; version=0.0.4",
      },
    });
  }

  private handleOpenAPISpec(): Response {
    const tools = [
      {
        name: "build_payment_tx",
        description: "Build an unsigned payment transaction",
        inputSchema: PaymentTxSchema.shape,
      },
      {
        name: "simulate_raw_tx", 
        description: "Simulate an unsigned raw transaction",
        inputSchema: SimulateTxSchema.shape,
      },
      {
        name: "submit_signed_tx",
        description: "Broadcast a signed transaction",
        inputSchema: SubmitTxSchema.shape,
      },
    ];

    const spec = OpenAPIGenerator.generateSpec(
      "Algorand Actions MCP Worker",
      "HTTP REST API for Algorand transaction building, simulation, and submission",
      "0.1.0",
      new URL("", new URL("", "https://example.com").href).href,
      tools
    );

    return this.jsonResponse(spec);
  }

  private handleSwaggerUI(): Response {
    const tools = [
      {
        name: "build_payment_tx",
        description: "Build an unsigned payment transaction",
        inputSchema: PaymentTxSchema.shape,
      },
      {
        name: "simulate_raw_tx",
        description: "Simulate an unsigned raw transaction", 
        inputSchema: SimulateTxSchema.shape,
      },
      {
        name: "submit_signed_tx",
        description: "Broadcast a signed transaction",
        inputSchema: SubmitTxSchema.shape,
      },
    ];

    const spec = OpenAPIGenerator.generateSpec(
      "Algorand Actions MCP Worker",
      "HTTP REST API for Algorand transaction building, simulation, and submission",
      "0.1.0",
      new URL("", new URL("", "https://example.com").href).href,
      tools
    );

    const html = OpenAPIGenerator.generateSwaggerHTML(spec);
    
    return new Response(html, {
      headers: {
        "Content-Type": "text/html",
      },
    });
  }

  private jsonResponse(data: any, status = 200): Response {
    return this.corsResponse(
      new Response(JSON.stringify(data), {
        status,
        headers: {
          "Content-Type": "application/json",
        },
      })
    );
  }

  private corsResponse(response: Response): Response {
    response.headers.set("Access-Control-Allow-Origin", "*");
    response.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    response.headers.set("Access-Control-Allow-Headers", "Content-Type");
    return response;
  }
}