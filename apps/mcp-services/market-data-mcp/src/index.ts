import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { ExtendedEnv } from "@algorand-showcase/types";
import { ResponseProcessor } from "@algorand-showcase/mcp-core";
import { MarketDataHttpAdapter } from "./http-adapter.js";
import { PriceProviderFactory } from "./providers/price-providers.js";
import { OracleProviderFactory } from "./providers/oracle-providers.js";

// ExecutionContext type for Cloudflare Workers
interface ExecutionContext {
  waitUntil(promise: Promise<any>): void;
  passThroughOnException(): void;
}

// Define our Market Data MCP service with tools
export class MarketDataMCP {
	server = new McpServer({
		name: "Market Data MCP",
		version: "1.0.0",
	});

	private env: ExtendedEnv;
	private state: Record<string, unknown> = {
		items_per_page: 10
	};

	constructor(env: ExtendedEnv) {
		this.env = env;
	}

	// Initialization function that sets up tools and resources
	async init() {
		console.log("Initializing Market Data MCP...");
		const itemsPerPage = (this.state?.items_per_page as number) || 10;
		ResponseProcessor.setItemsPerPage(itemsPerPage);

		// Register market data tools
		this.registerMarketDataTools();
	}

	/**
	 * Register tools for market data sources (price feeds, oracles)
	 */
	private registerMarketDataTools() {
		// Price feed tool
		this.server.tool(
			'get_price_feed',
			'Get real-time price data for cryptocurrency pairs (e.g., ALGO/USDC)',
			{
				pair: z.string().describe('Trading pair (e.g., "ALGO/USDC", "BTC/USD")'),
				source: z.enum(['coinbase', 'coingecko', 'chainlink']).optional().describe('Price data source'),
				interval: z.enum(['1m', '5m', '15m', '1h', '1d']).optional().describe('Price interval')
			},
			async (args) => {
				try {
					const apiKey = (this.env as any).COINGECKO_API_KEY;
					const provider = PriceProviderFactory.createProvider(args.source || 'coingecko', apiKey);
					const priceData = await provider.getPrice(args.pair);

					return {
						content: [{
							type: "text" as const,
							text: JSON.stringify({
								success: true,
								data: {
									...priceData,
									interval: args.interval || '1h'
								}
							}, null, 2)
						}]
					};
				} catch (error) {
					return {
						content: [{
							type: "text" as const,
							text: JSON.stringify({
								success: false,
								error: String(error)
							}, null, 2)
						}]
					};
				}
			}
		);

		// Oracle data tool
		this.server.tool(
			'get_oracle_data',
			'Get oracle data from various providers (Chainlink, Pyth, etc.)',
			{
				oracle: z.enum(['chainlink', 'pyth', 'band']).describe('Oracle provider'),
				feed_id: z.string().describe('Oracle feed identifier'),
				network: z.enum(['mainnet', 'testnet']).optional().describe('Network to query')
			},
			async (args) => {
				try {
					const apiKey = (this.env as any).CHAINLINK_API_KEY;
					const provider = OracleProviderFactory.createProvider(args.oracle, apiKey);
					const oracleData = await provider.getData(args.feed_id, args.network);

					return {
						content: [{
							type: "text" as const,
							text: JSON.stringify({
								success: true,
								data: oracleData
							}, null, 2)
						}]
					};
				} catch (error) {
					return {
						content: [{
							type: "text" as const,
							text: JSON.stringify({
								success: false,
								error: String(error)
							}, null, 2)
						}]
					};
				}
			}
		);

		// Market data tool
		this.server.tool(
			'get_market_data',
			'Get comprehensive market data including volume, market cap, etc.',
			{
				symbol: z.string().describe('Cryptocurrency symbol (e.g., "ALGO", "BTC")'),
				metrics: z.array(z.enum(['price', 'volume', 'market_cap', 'price_change'])).optional().describe('Specific metrics to retrieve')
			},
			async (args) => {
				return {
					content: [{
						type: "text" as const,
						text: `Market data for ${args.symbol}`
					}]
				};
			}
		);

		// Historical price data tool
		this.server.tool(
			'get_historical_prices',
			'Get historical price data for analysis',
			{
				pair: z.string().describe('Trading pair (e.g., "ALGO/USDC")'),
				from: z.string().describe('Start date (ISO 8601 format)'),
				to: z.string().describe('End date (ISO 8601 format)'),
				interval: z.enum(['1h', '4h', '1d', '1w']).optional().describe('Data interval')
			},
			async (args) => {
				return {
					content: [{
						type: "text" as const,
						text: `Historical prices for ${args.pair} from ${args.from} to ${args.to}`
					}]
				};
			}
		);

		// DeFi protocol data tool
		this.server.tool(
			'get_defi_data',
			'Get DeFi protocol data (TVL, APY, etc.)',
			{
				protocol: z.string().describe('DeFi protocol name'),
				metrics: z.array(z.enum(['tvl', 'apy', 'volume', 'users'])).optional().describe('Metrics to retrieve')
			},
			async (args) => {
				return {
					content: [{
						type: "text" as const,
						text: `DeFi data for ${args.protocol}`
					}]
				};
			}
		);
	}
}

export default {
	async fetch(request: Request, env: ExtendedEnv, ctx: ExecutionContext) {
		const url = new URL(request.url);

		// HTTP REST API endpoints
		if (url.pathname.startsWith("/api/") || url.pathname === "/tools/list" || url.pathname === "/metrics" || url.pathname === "/openapi.json" || url.pathname === "/docs" || url.pathname === "/swagger") {
			const httpAdapter = new MarketDataHttpAdapter(env);
			return httpAdapter.handleRequest(request, env);
		}

		if (url.pathname === "/health") {
			return new Response(JSON.stringify({
				status: "ok",
				service: "market-data-mcp",
				version: "1.0.0"
			}), {
				status: 200,
				headers: { 'content-type': 'application/json' }
			});
		}

		if (url.pathname === "/sse" || url.pathname === "/sse/message") {
			// Create and initialize MCP server instance
			const mcpInstance = new MarketDataMCP(env);
			await mcpInstance.init();
			// For now, return a placeholder - we need to implement proper MCP transport
			return new Response(JSON.stringify({ message: "Market Data MCP SSE endpoint - transport implementation needed" }), {
				status: 501,
				headers: { "content-type": "application/json" }
			});
		}

		if (url.pathname === "/mcp") {
			// Create and initialize MCP server instance
			const mcpInstance = new MarketDataMCP(env);
			await mcpInstance.init();
			// For now, return a placeholder - we need to implement proper MCP transport
			return new Response(JSON.stringify({ message: "Market Data MCP endpoint - transport implementation needed" }), {
				status: 501,
				headers: { "content-type": "application/json" }
			});
		}

		return new Response("Not found", { status: 404 });
	},
};