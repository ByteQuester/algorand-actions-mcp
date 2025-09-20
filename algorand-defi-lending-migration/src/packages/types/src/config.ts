/**
 * Configuration types for Algorand Workers
 */
import { AlgorandNetwork, EnvValue } from './common';

/**
 * Network configuration for Algorand clients
 */
export interface NetworkConfig {
  network: AlgorandNetwork;
  algodUrl: string;
  indexerUrl: string;
  apiKey?: string;
  token?: string;
}

/**
 * Base environment interface for Cloudflare Workers
 */
export interface BaseEnv {
  // Algorand network configuration
  ALGORAND_NETWORK?: string;
  ALGORAND_ALGOD?: string;
  ALGORAND_INDEXER?: string;
  ALGORAND_TOKEN?: string;
  
  // Mode configuration
  READ_ONLY?: EnvValue;
  ALLOW_MAINNET?: EnvValue;
  
  // Pagination
  ITEMS_PER_PAGE?: string;
}

/**
 * Extended environment for Remote MCP with additional services
 */
export interface ExtendedEnv extends BaseEnv {
  // Hashicorp Vault integration
  HCV_WORKER?: any;
  HCV_WORKER_URL?: string;
  VAULT_ENTITIES?: any;
  VAULT_OIDC_ACCESSOR?: string;
  
  // OAuth configuration
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  COOKIE_ENCRYPTION_KEY?: string;
  OAUTH_KV?: KVNamespace;
  
  // R2 storage bindings
  KNOWLEDGE_BUCKET?: R2Bucket;
  PLAUSIBLE_AI?: R2Bucket;
  
  // Cache bindings
  PUBLIC_KEY_CACHE?: any;
  
  // External API URLs
  NFD_API_URL?: string;
  PERA_WALLET_API_URL?: string;
  PERA_EXPLORER_URL?: string;
  
  // Durable Object namespace
  AlgorandRemoteMCP?: DurableObjectNamespace;
}

/**
 * MCP server configuration
 */
export interface MCPConfig {
  name: string;
  version: string;
  network: AlgorandNetwork;
  readOnly: boolean;
  itemsPerPage: number;
}

/**
 * App configuration aggregating all settings
 */
export interface AppConfig {
  mcp: MCPConfig;
  network: NetworkConfig;
  features: {
    oauth: boolean;
    vault: boolean;
    storage: boolean;
  };
}