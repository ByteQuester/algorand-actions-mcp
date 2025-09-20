import { z } from "zod";
import { ExtendedEnv } from "@algorand-showcase/types";
import { ResponseProcessor, OpenAPIGenerator } from "@algorand-showcase/mcp-core";
import { PriceProviderFactory } from "./providers/price-providers.js";
import { OracleProviderFactory } from "./providers/oracle-providers.js";

// Validation schemas for external data endpoints
const PriceFeedSchema = z.object({
  pair: z.string(),
  source: z.enum(['coinbase', 'coingecko', 'chainlink']).optional(),
  interval: z.enum(['1m', '5m', '15m', '1h', '1d']).optional(),
});

const OracleDataSchema = z.object({
  oracle: z.enum(['chainlink', 'pyth', 'band']),
  feed_id: z.string(),
  network: z.enum(['mainnet', 'testnet']).optional(),
});

const MarketDataSchema = z.object({
  symbol: z.string(),
  metrics: z.array(z.enum(['price', 'volume', 'market_cap', 'price_change'])).optional(),
});

const HistoricalPricesSchema = z.object({
  pair: z.string(),
  from: z.string(),
  to: z.string(),
  interval: z.enum(['1h', '4h', '1d', '1w']).optional(),
});

const DeFiDataSchema = z.object({
  protocol: z.string(),
  metrics: z.array(z.enum(['tvl', 'apy', 'volume', 'users'])).optional(),
});

export interface HttpAdapter {
  handleRequest(request: Request, env: ExtendedEnv): Promise<Response>;
}

export class MarketDataHttpAdapter implements HttpAdapter {
  constructor(private env: ExtendedEnv) {}

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
      case "/tools/get_price_feed":
      case "/api/price-feed":
        return this.handlePriceFeed(request);
      case "/tools/get_oracle_data":
      case "/api/oracle-data":
        return this.handleOracleData(request);
      case "/tools/get_market_data":
      case "/api/market-data":
        return this.handleMarketData(request);
      case "/tools/get_historical_prices":
      case "/api/historical-prices":
        return this.handleHistoricalPrices(request);
      case "/tools/get_defi_data":
      case "/api/defi-data":
        return this.handleDeFiData(request);
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
        name: "get_price_feed",
        description: "Get real-time price data for cryptocurrency pairs",
        inputSchema: PriceFeedSchema.shape,
      },
      {
        name: "get_oracle_data",
        description: "Get oracle data from various providers",
        inputSchema: OracleDataSchema.shape,
      },
      {
        name: "get_market_data",
        description: "Get comprehensive market data",
        inputSchema: MarketDataSchema.shape,
      },
      {
        name: "get_historical_prices",
        description: "Get historical price data for analysis",
        inputSchema: HistoricalPricesSchema.shape,
      },
      {
        name: "get_defi_data",
        description: "Get DeFi protocol data",
        inputSchema: DeFiDataSchema.shape,
      },
    ];

    return this.jsonResponse({ tools });
  }

  private async handlePriceFeed(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = PriceFeedSchema.parse(body);

      // Get API key from environment if available
      const apiKey = (this.env as any).COINGECKO_API_KEY;

      // Create price provider
      const provider = PriceProviderFactory.createProvider(parsed.source || 'coingecko', apiKey);

      // Get price data from the provider
      const priceData = await provider.getPrice(parsed.pair);

      return this.jsonResponse({
        success: true,
        data: {
          ...priceData,
          interval: parsed.interval || '1h'
        }
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  private async handleOracleData(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = OracleDataSchema.parse(body);

      // Get API key from environment if available
      const apiKey = (this.env as any).CHAINLINK_API_KEY;

      // Create oracle provider
      const provider = OracleProviderFactory.createProvider(parsed.oracle, apiKey);

      // Get oracle data from the provider
      const oracleData = await provider.getData(parsed.feed_id, parsed.network);

      return this.jsonResponse({
        success: true,
        data: oracleData
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  private async handleMarketData(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = MarketDataSchema.parse(body);

      // Mock implementation
      const mockData = {
        symbol: parsed.symbol,
        price: 0.25,
        volume_24h: 50000000,
        market_cap: 2500000000,
        price_change_24h: 2.5,
        price_change_percentage_24h: 1.02,
        circulating_supply: 10000000000,
        total_supply: 10000000000,
        rank: 50,
        timestamp: new Date().toISOString()
      };

      // Filter based on requested metrics
      if (parsed.metrics) {
        const filteredData = {};
        parsed.metrics.forEach(metric => {
          if (metric in mockData) {
            (filteredData as any)[metric] = (mockData as any)[metric];
          }
        });
        (filteredData as any).symbol = mockData.symbol;
        (filteredData as any).timestamp = mockData.timestamp;

        return this.jsonResponse({
          success: true,
          data: filteredData
        });
      }

      return this.jsonResponse({
        success: true,
        data: mockData
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  private async handleHistoricalPrices(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = HistoricalPricesSchema.parse(body);

      // Mock implementation - generate sample historical data
      const mockData = {
        pair: parsed.pair,
        from: parsed.from,
        to: parsed.to,
        interval: parsed.interval || '1d',
        prices: [
          { timestamp: "2025-01-01T00:00:00Z", open: 0.24, high: 0.26, low: 0.23, close: 0.25, volume: 1000000 },
          { timestamp: "2025-01-02T00:00:00Z", open: 0.25, high: 0.27, low: 0.24, close: 0.26, volume: 1200000 },
          { timestamp: "2025-01-03T00:00:00Z", open: 0.26, high: 0.28, low: 0.25, close: 0.27, volume: 1100000 }
        ]
      };

      return this.jsonResponse({
        success: true,
        data: mockData
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  private async handleDeFiData(request: Request): Promise<Response> {
    try {
      const body = await request.json();
      const parsed = DeFiDataSchema.parse(body);

      // Mock implementation
      const mockData = {
        protocol: parsed.protocol,
        tvl: 125000000, // Total Value Locked
        apy: 8.5, // Annual Percentage Yield
        volume_24h: 5000000,
        users_24h: 1250,
        fees_24h: 25000,
        timestamp: new Date().toISOString()
      };

      // Filter based on requested metrics
      if (parsed.metrics) {
        const filteredData = {};
        parsed.metrics.forEach(metric => {
          if (metric === 'tvl' && 'tvl' in mockData) (filteredData as any).tvl = mockData.tvl;
          if (metric === 'apy' && 'apy' in mockData) (filteredData as any).apy = mockData.apy;
          if (metric === 'volume' && 'volume_24h' in mockData) (filteredData as any).volume_24h = mockData.volume_24h;
          if (metric === 'users' && 'users_24h' in mockData) (filteredData as any).users_24h = mockData.users_24h;
        });
        (filteredData as any).protocol = mockData.protocol;
        (filteredData as any).timestamp = mockData.timestamp;

        return this.jsonResponse({
          success: true,
          data: filteredData
        });
      }

      return this.jsonResponse({
        success: true,
        data: mockData
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  private async handleStatus(): Promise<Response> {
    return this.jsonResponse({
      success: true,
      service: "market-data-mcp",
      version: "1.0.0",
      status: "operational",
      data_sources: {
        price_feeds: ["coinbase", "coingecko", "chainlink"],
        oracles: ["chainlink", "pyth", "band"],
        defi_protocols: ["supported"]
      }
    });
  }

  private handleHealth(): Response {
    return this.jsonResponse({
      status: "healthy",
      service: "market-data-mcp",
      version: "1.0.0",
      timestamp: new Date().toISOString(),
      data_sources_available: true,
    });
  }

  private handleMetrics(): Response {
    // Basic Prometheus-style metrics
    const metrics = `
# HELP market_data_mcp_up Market Data MCP Worker is up
# TYPE market_data_mcp_up gauge
market_data_mcp_up 1

# HELP market_data_mcp_info Market Data MCP Worker info
# TYPE market_data_mcp_info gauge
market_data_mcp_info{version="1.0.0"} 1

# HELP market_data_sources_available Number of data sources available
# TYPE market_data_sources_available gauge
market_data_sources_available 8
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
        name: "get_price_feed",
        description: "Get real-time price data for cryptocurrency pairs",
        inputSchema: PriceFeedSchema.shape,
      },
      {
        name: "get_oracle_data",
        description: "Get oracle data from various providers",
        inputSchema: OracleDataSchema.shape,
      },
      {
        name: "get_market_data",
        description: "Get comprehensive market data",
        inputSchema: MarketDataSchema.shape,
      },
      {
        name: "get_historical_prices",
        description: "Get historical price data for analysis",
        inputSchema: HistoricalPricesSchema.shape,
      },
      {
        name: "get_defi_data",
        description: "Get DeFi protocol data",
        inputSchema: DeFiDataSchema.shape,
      },
    ];

    const spec = OpenAPIGenerator.generateSpec(
      "Market Data MCP Worker",
      "HTTP REST API for market data sources (price feeds, oracles)",
      "1.0.0",
      new URL("", new URL("", "https://example.com").href).href,
      tools
    );

    return this.jsonResponse(spec);
  }

  private handleSwaggerUI(): Response {
    const tools = [
      {
        name: "get_price_feed",
        description: "Get real-time price data for cryptocurrency pairs",
        inputSchema: PriceFeedSchema.shape,
      },
      {
        name: "get_oracle_data",
        description: "Get oracle data from various providers",
        inputSchema: OracleDataSchema.shape,
      },
      {
        name: "get_market_data",
        description: "Get comprehensive market data",
        inputSchema: MarketDataSchema.shape,
      },
      {
        name: "get_historical_prices",
        description: "Get historical price data for analysis",
        inputSchema: HistoricalPricesSchema.shape,
      },
      {
        name: "get_defi_data",
        description: "Get DeFi protocol data",
        inputSchema: DeFiDataSchema.shape,
      },
    ];

    const spec = OpenAPIGenerator.generateSpec(
      "Market Data MCP Worker",
      "HTTP REST API for market data sources (price feeds, oracles)",
      "1.0.0",
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

  private handleError(error: any): Response {
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