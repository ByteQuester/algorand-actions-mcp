import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { ExtendedEnv, State, Props } from "@algorand-showcase/types";
import { ResponseProcessor } from "@algorand-showcase/mcp-core";
import OAuthProvider from "./oauth-provider";
import { OauthHandler } from "./oauth-handler";

// Define our MCP agent with tools
export class AlgorandRemoteMCP extends McpAgent<ExtendedEnv, State, Props> {
	server = new McpServer({
		name: "Algorand Remote MCP",
		version: "1.2.0",
	});

	// Initialize state with default values
	initialState: State = {
		items_per_page: 10

	};

	// Initialization function that sets up tools and resources
	async init() {
		// Configure ResponseProcessor with pagination settings
		console.log("Initializing Algorand Remote MCP...");
		const itemsPerPage = this.state?.items_per_page || 10;
		ResponseProcessor.setItemsPerPage(itemsPerPage);

		// Determine READ_ONLY mode: explicit flag or missing required secrets
		const explicitReadOnly = this.env && (this.env.READ_ONLY === true || this.env.READ_ONLY === 'true' || (this.env as any).READ_ONLY === '1');
		const secretsMissing = !(this.env as any)?.HCV_WORKER || !(this.env as any)?.HCV_WORKER_URL || !(this.env as any)?.VAULT_ENTITIES || !(this.env as any)?.VAULT_OIDC_ACCESSOR || !(this.env as any)?.GOOGLE_CLIENT_ID || !(this.env as any)?.GOOGLE_CLIENT_SECRET || !(this.env as any)?.COOKIE_ENCRYPTION_KEY;
		const isReadOnly = !!explicitReadOnly || !!secretsMissing;

		if (isReadOnly) {
			console.log('MCP running in READ_ONLY mode');
			// Provide public, read-only defaults
			if (!this.env.ALGORAND_ALGOD) this.env.ALGORAND_ALGOD = 'https://mainnet-api.algonode.cloud';
			if (!this.env.ALGORAND_INDEXER) this.env.ALGORAND_INDEXER = 'https://mainnet-idx.algonode.cloud';
			if (!(this.env as any).ALGORAND_TOKEN) (this.env as any).ALGORAND_TOKEN = '';
			this.registerReadOnlyStubs();
			return;
		}
	}

	/**
	 * Register stubs for wallet/sign tools in READ_ONLY mode
	 */
	private registerReadOnlyStubs() {
		const unavailableResponse = (message?: string) => {
			return ResponseProcessor.processResponse({ error: message || 'unavailable in read-only mode' });
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
	fetch(request: Request, env: ExtendedEnv, ctx: ExecutionContext) {
		const explicitReadOnly = env && (env.READ_ONLY === true || env.READ_ONLY === 'true' || (env as any).READ_ONLY === '1');
		const secretsMissing = !(env as any)?.HCV_WORKER || !(env as any)?.HCV_WORKER_URL || !(env as any)?.VAULT_ENTITIES || !(env as any)?.VAULT_OIDC_ACCESSOR || !(env as any)?.GOOGLE_CLIENT_ID || !(env as any)?.GOOGLE_CLIENT_SECRET || !(env as any)?.COOKIE_ENCRYPTION_KEY;
		const isReadOnly = !!explicitReadOnly || !!secretsMissing;
		if (isReadOnly) {
			console.log('MCP running in READ_ONLY mode');
			if (!env.ALGORAND_ALGOD) (env as any).ALGORAND_ALGOD = 'https://mainnet-api.algonode.cloud';
			if (!env.ALGORAND_INDEXER) (env as any).ALGORAND_INDEXER = 'https://mainnet-idx.algonode.cloud';
			if (!(env as any).ALGORAND_TOKEN) (env as any).ALGORAND_TOKEN = '';
			const url = new URL(request.url);
			if (url.pathname === "/health") {
				return new Response(JSON.stringify({ status: "ok", mode: "READ_ONLY" }), { status: 200, headers: { 'content-type': 'application/json' } });
			}
			if (url.pathname === "/sse" || url.pathname === "/sse/message") {
				return AlgorandRemoteMCP.serveSSE("/sse", {
					binding: "AlgorandRemoteMCP",
				}).fetch(request, env, ctx);
			}
			if (url.pathname === "/mcp") {
				return AlgorandRemoteMCP.serve("/mcp", {
					binding: "AlgorandRemoteMCP",
				}).fetch(request, env, ctx);
			}
			return new Response("Not found", { status: 404 });
		}

		const provider = new OAuthProvider({
			apiHandler: AlgorandRemoteMCP.mount("/sse", {
				binding: "AlgorandRemoteMCP"
			}) as any,
			apiRoute: "/sse",
			authorizeEndpoint: "/authorize",
			clientRegistrationEndpoint: "/register",
			defaultHandler: OauthHandler as any,
			tokenEndpoint: "/token",
		});
		return provider.fetch(request, env as any, ctx);
	},
};