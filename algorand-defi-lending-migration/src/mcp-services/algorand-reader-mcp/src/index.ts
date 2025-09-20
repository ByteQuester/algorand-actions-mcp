import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { ExtendedEnv } from "@algorand-showcase/types";
import { ResponseProcessor } from "@algorand-showcase/mcp-core";
import OAuthProvider from "./oauth-provider.js";
import { OauthHandler } from "./oauth-handler.js";
import { RemoteHttpAdapter } from "./http-adapter.js";

// ExecutionContext type for Cloudflare Workers
interface ExecutionContext {
  waitUntil(promise: Promise<any>): void;
  passThroughOnException(): void;
}

// Define our MCP agent with tools
export class AlgorandRemoteMCP {
	server = new McpServer({
		name: "Algorand Remote MCP",
		version: "1.2.0",
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
		// Configure ResponseProcessor with pagination settings
		console.log("Initializing Algorand Remote MCP...");
		const itemsPerPage = (this.state?.items_per_page as number) || 10;
		ResponseProcessor.setItemsPerPage(itemsPerPage);

		// Set to read-only mode for now
		const isReadOnly = true;

		if (isReadOnly) {
			console.log('MCP running in READ_ONLY mode');
			this.registerReadOnlyStubs();
			return;
		}
	}

	/**
	 * Register stubs for wallet/sign tools in READ_ONLY mode
	 */
	private registerReadOnlyStubs() {
		const unavailableResponse = (message?: string) => {
			return { content: [{ type: "text" as const, text: message || 'unavailable in read-only mode' }] };
		};

		// Signing and submission
		this.server.tool(
			'sign_transaction',
			'Sign an Algorand transaction (disabled in READ_ONLY mode)',
			{ encodedTxn: z.string().describe('Base64 encoded transaction') },
			async (_args) => unavailableResponse()
		);
		this.server.tool(
			'submit_transaction',
			'Submit a signed transaction (disabled in READ_ONLY mode)',
			{ signedTxn: z.string().describe('Base64 encoded signed transaction') },
			async (_args) => unavailableResponse()
		);

		// Wallet-related
		this.server.tool('reset_wallet_account', 'Reset wallet account (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
		this.server.tool('get_wallet_publickey', 'Get wallet public key (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
		this.server.tool('get_wallet_address', 'Get wallet address (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
		this.server.tool('get_wallet_role', 'Get wallet role (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
		this.server.tool('get_wallet_info', 'Get wallet info (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
		this.server.tool('get_wallet_assets', 'Get wallet assets (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
		this.server.tool('logout', 'Logout (disabled in READ_ONLY mode)', {}, async (_args) => unavailableResponse());
	}
}

export default {
	async fetch(request: Request, env: ExtendedEnv, ctx: ExecutionContext) {
		const url = new URL(request.url);
		const explicitReadOnly = env && (env.READ_ONLY === true || env.READ_ONLY === 'true' || (env as any).READ_ONLY === '1');
		const secretsMissing = !(env as any)?.HCV_WORKER || !(env as any)?.HCV_WORKER_URL || !(env as any)?.VAULT_ENTITIES || !(env as any)?.VAULT_OIDC_ACCESSOR || !(env as any)?.GOOGLE_CLIENT_ID || !(env as any)?.GOOGLE_CLIENT_SECRET || !(env as any)?.COOKIE_ENCRYPTION_KEY;
		const isReadOnly = !!explicitReadOnly || !!secretsMissing;
		
		// HTTP REST API endpoints (available in both modes)
		if (url.pathname.startsWith("/api/") || url.pathname === "/tools/list" || url.pathname === "/metrics" || url.pathname === "/openapi.json" || url.pathname === "/docs" || url.pathname === "/swagger") {
			const httpAdapter = new RemoteHttpAdapter(env);
			return httpAdapter.handleRequest(request, env);
		}
		
		if (isReadOnly) {
			console.log('MCP running in READ_ONLY mode');
			if (!env.ALGORAND_ALGOD) (env as any).ALGORAND_ALGOD = 'https://mainnet-api.algonode.cloud';
			if (!env.ALGORAND_INDEXER) (env as any).ALGORAND_INDEXER = 'https://mainnet-idx.algonode.cloud';
			if (!(env as any).ALGORAND_TOKEN) (env as any).ALGORAND_TOKEN = '';
			
			if (url.pathname === "/health") {
				return new Response(JSON.stringify({ status: "ok", mode: "READ_ONLY" }), { status: 200, headers: { 'content-type': 'application/json' } });
			}
			if (url.pathname === "/sse" || url.pathname === "/sse/message") {
				// Create and initialize MCP server instance
				const mcpInstance = new AlgorandRemoteMCP(env);
				await mcpInstance.init();
				// For now, return a placeholder - we need to implement proper MCP transport
				return new Response(JSON.stringify({ message: "MCP SSE endpoint - transport implementation needed" }), {
					status: 501,
					headers: { "content-type": "application/json" }
				});
			}
			if (url.pathname === "/mcp") {
				// Create and initialize MCP server instance
				const mcpInstance = new AlgorandRemoteMCP(env);
				await mcpInstance.init();
				// For now, return a placeholder - we need to implement proper MCP transport
				return new Response(JSON.stringify({ message: "MCP endpoint - transport implementation needed" }), {
					status: 501,
					headers: { "content-type": "application/json" }
				});
			}
			return new Response("Not found", { status: 404 });
		}

		// OAuth mode with full functionality
		// For now, disable OAuth mode until proper transport is implemented
		return new Response(JSON.stringify({ message: "OAuth mode temporarily disabled - transport implementation needed" }), {
			status: 501,
			headers: { "content-type": "application/json" }
		});

		/* TODO: Implement proper OAuth mode
		const provider = new OAuthProvider({
			apiHandler: "placeholder", // Need to implement proper handler
			apiRoute: "/sse",
			authorizeEndpoint: "/authorize",
			clientRegistrationEndpoint: "/register",
			defaultHandler: OauthHandler as any,
			tokenEndpoint: "/token",
		});
		return provider.fetch(request, env as any, ctx);
		*/
	},
};