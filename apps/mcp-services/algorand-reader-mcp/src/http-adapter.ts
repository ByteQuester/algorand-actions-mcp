import { z } from "zod";
import { ExtendedEnv } from "@algorand-showcase/types";
import { AlgodClientWrapper, IndexerClientWrapper } from "@algorand-showcase/algorand-clients";
import { ResponseProcessor, OpenAPIGenerator } from "@algorand-showcase/mcp-core";

const AccountInfoSchema = z.object({
  address: z.string(),
});

const TransactionSchema = z.object({
  txId: z.string(),
});

const AssetSchema = z.object({
  assetId: z.number(),
});

const BlockSchema = z.object({
  round: z.number(),
});

const SearchTransactionsSchema = z.object({
  address: z.string().optional(),
  assetId: z.number().optional(),
  limit: z.number().min(1).max(100).default(10),
  next: z.string().optional(),
});

export interface HttpAdapter {
  handleRequest(request: Request, env: ExtendedEnv): Promise<Response>;
}

export class RemoteHttpAdapter implements HttpAdapter {
  private algodClient: AlgodClientWrapper;
  private indexerClient: IndexerClientWrapper;
  
  constructor(private env: ExtendedEnv) {
    const algodUrl = env.ALGORAND_ALGOD || "https://mainnet-api.algonode.cloud";
    const indexerUrl = env.ALGORAND_INDEXER || "https://mainnet-idx.algonode.cloud";
    const token = (env as any).ALGORAND_TOKEN || "";
    
    this.algodClient = new AlgodClientWrapper({ 
      algodUrl, 
      network: "mainnet",
      token 
    });
    
    this.indexerClient = new IndexerClientWrapper({
      network: "mainnet",
      algodUrl,
      indexerUrl,
      token
    });
  }

  async handleRequest(request: Request, env: ExtendedEnv): Promise<Response> {
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
      case "/api/account":
        return this.handleAccountInfo(request);
      case "/api/transaction":
        return this.handleTransaction(request);
      case "/api/asset":
        return this.handleAsset(request);
      case "/api/block":
        return this.handleBlock(request);
      case "/api/search/transactions":
        return this.handleSearchTransactions(request);
      case "/api/status":
        return this.handleStatus();
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
        name: "get_account_info",
        description: "Get account information including balance and assets",
        inputSchema: AccountInfoSchema.shape,
      },
      {
        name: "get_transaction",
        description: "Get transaction details by ID",
        inputSchema: TransactionSchema.shape,
      },
      {
        name: "get_asset_info",
        description: "Get asset information",
        inputSchema: AssetSchema.shape,
      },
      {
        name: "get_block",
        description: "Get block information by round",
        inputSchema: BlockSchema.shape,
      },
      {
        name: "search_transactions",
        description: "Search transactions with filters",
        inputSchema: SearchTransactionsSchema.shape,
      },
    ];

    return this.jsonResponse({ tools });
  }

  private async handleAccountInfo(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = AccountInfoSchema.parse(body);

      const result = await this.indexerClient.getAccountInfo(parsed.address);

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          account: result.data 
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
          { success: false, error: "Invalid input", details: error.issues },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleTransaction(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = TransactionSchema.parse(body);

      const result = await this.indexerClient.lookupTransaction(parsed.txId);

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          transaction: result.data 
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
          { success: false, error: "Invalid input", details: error.issues },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleAsset(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = AssetSchema.parse(body);

      const result = await this.indexerClient.lookupAsset(parsed.assetId);

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          asset: result.data 
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
          { success: false, error: "Invalid input", details: error.issues },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleBlock(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = BlockSchema.parse(body);

      const result = await this.algodClient.getBlock(parsed.round);

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          block: result.data 
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
          { success: false, error: "Invalid input", details: error.issues },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleSearchTransactions(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = SearchTransactionsSchema.parse(body);

      const result = await this.indexerClient.searchTransactions({
        address: parsed.address,
        assetId: parsed.assetId,
        limit: parsed.limit,
        nextToken: parsed.next,
      });

      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          transactions: result.data.transactions,
          nextToken: result.data.nextToken 
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
          { success: false, error: "Invalid input", details: error.issues },
          400
        );
      }
      return this.jsonResponse(
        { success: false, error: String(error) },
        500
      );
    }
  }

  private async handleStatus(): Promise<Response> {
    try {
      const result = await this.algodClient.getStatus();
      
      if (result.success) {
        return this.jsonResponse({ 
          success: true, 
          status: result.data 
        });
      } else {
        return this.jsonResponse(
          { success: false, error: result.error.message },
          500
        );
      }
    } catch (error) {
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
      algodUrl: this.env.ALGORAND_ALGOD || "https://mainnet-api.algonode.cloud",
      indexerUrl: this.env.ALGORAND_INDEXER || "https://mainnet-idx.algonode.cloud",
      readOnly: true,
    });
  }

  private handleMetrics(): Response {
    // Basic Prometheus-style metrics
    const metrics = `
# HELP remote_mcp_up Remote MCP Worker is up
# TYPE remote_mcp_up gauge
remote_mcp_up 1

# HELP remote_mcp_info Remote MCP Worker info
# TYPE remote_mcp_info gauge
remote_mcp_info{readonly="true"} 1
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
        name: "get_account_info",
        description: "Get account information including balance and assets",
        inputSchema: AccountInfoSchema.shape,
      },
      {
        name: "get_transaction",
        description: "Get transaction details by ID", 
        inputSchema: TransactionSchema.shape,
      },
      {
        name: "get_asset_info",
        description: "Get asset information",
        inputSchema: AssetSchema.shape,
      },
      {
        name: "get_block",
        description: "Get block information by round",
        inputSchema: BlockSchema.shape,
      },
      {
        name: "search_transactions",
        description: "Search transactions with filters",
        inputSchema: SearchTransactionsSchema.shape,
      },
    ];

    const spec = OpenAPIGenerator.generateSpec(
      "Algorand Remote MCP Worker",
      "HTTP REST API for Algorand blockchain data access",
      "1.2.0",
      new URL("", new URL("", "https://example.com").href).href,
      tools
    );

    return this.jsonResponse(spec);
  }

  private handleSwaggerUI(): Response {
    const tools = [
      {
        name: "get_account_info",
        description: "Get account information including balance and assets",
        inputSchema: AccountInfoSchema.shape,
      },
      {
        name: "get_transaction", 
        description: "Get transaction details by ID",
        inputSchema: TransactionSchema.shape,
      },
      {
        name: "get_asset_info",
        description: "Get asset information", 
        inputSchema: AssetSchema.shape,
      },
      {
        name: "get_block",
        description: "Get block information by round",
        inputSchema: BlockSchema.shape,
      },
      {
        name: "search_transactions",
        description: "Search transactions with filters",
        inputSchema: SearchTransactionsSchema.shape,
      },
    ];

    const spec = OpenAPIGenerator.generateSpec(
      "Algorand Remote MCP Worker", 
      "HTTP REST API for Algorand blockchain data access",
      "1.2.0",
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
    response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
    return response;
  }
}