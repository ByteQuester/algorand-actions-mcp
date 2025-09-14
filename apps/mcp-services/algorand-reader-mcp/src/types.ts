/**
 * Type definitions for OAuth handler and remote MCP worker
 */

/**
 * OAuth Props stored with user authentication data
 */
export interface Props {
  accessToken: string;
  email: string;
  name: string;
  provider: string;
  id: string;
  clientId: string;
}

/**
 * Environment variables for the remote MCP worker
 */
export interface Env {
  // OAuth configuration
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  TWITTER_CLIENT_ID?: string;
  TWITTER_CLIENT_SECRET?: string;
  LINKEDIN_CLIENT_ID?: string;
  LINKEDIN_CLIENT_SECRET?: string;
  COOKIE_ENCRYPTION_KEY?: string;
  HOSTED_DOMAIN?: string;

  // KV Namespaces
  OAUTH_KV?: KVNamespace;
  CODE_VERIFIER_KV?: KVNamespace;

  // Algorand configuration
  ALGORAND_NETWORK?: string;
  ALGORAND_ALGOD?: string;
  ALGORAND_INDEXER?: string;
  ALGORAND_TOKEN?: string;

  // Mode configuration
  READ_ONLY?: boolean | string;
  ALLOW_MAINNET?: boolean | string;
}