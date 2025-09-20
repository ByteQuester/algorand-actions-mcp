/**
 * Configuration validation schemas using Zod
 */
import { z } from 'zod';
import type { NetworkConfig, MCPConfig, AppConfig } from '@algorand-showcase/types';

/**
 * Algorand network schema
 */
export const AlgorandNetworkSchema = z.enum(['mainnet', 'testnet', 'betanet']);

/**
 * Network configuration schema
 */
export const NetworkConfigSchema = z.object({
  network: AlgorandNetworkSchema,
  algodUrl: z.string().url(),
  indexerUrl: z.string().url(),
  apiKey: z.string().optional(),
  token: z.string().optional(),
}) satisfies z.ZodSchema<NetworkConfig>;

/**
 * MCP server configuration schema
 */
export const MCPConfigSchema = z.object({
  name: z.string().min(1),
  version: z.string().regex(/^\d+\.\d+\.\d+/),
  network: AlgorandNetworkSchema,
  readOnly: z.boolean(),
  itemsPerPage: z.number().min(1).max(100),
}) satisfies z.ZodSchema<MCPConfig>;

/**
 * App configuration schema
 */
export const AppConfigSchema = z.object({
  mcp: MCPConfigSchema,
  network: NetworkConfigSchema,
  features: z.object({
    oauth: z.boolean(),
    vault: z.boolean(),
    storage: z.boolean(),
  }),
}) satisfies z.ZodSchema<AppConfig>;

/**
 * Base environment schema
 */
export const BaseEnvSchema = z.object({
  // Algorand network configuration
  ALGORAND_NETWORK: z.string().optional(),
  ALGORAND_ALGOD: z.string().optional(),
  ALGORAND_INDEXER: z.string().optional(),
  ALGORAND_TOKEN: z.string().optional(),
  
  // Mode configuration
  READ_ONLY: z.union([z.string(), z.boolean()]).optional(),
  ALLOW_MAINNET: z.union([z.string(), z.boolean()]).optional(),
  
  // Pagination
  ITEMS_PER_PAGE: z.string().optional(),
});

/**
 * Extended environment schema for Remote MCP
 */
export const ExtendedEnvSchema = BaseEnvSchema.extend({
  // Hashicorp Vault integration
  HCV_WORKER_URL: z.string().optional(),
  VAULT_OIDC_ACCESSOR: z.string().optional(),
  
  // OAuth configuration
  GOOGLE_CLIENT_ID: z.string().optional(),
  GOOGLE_CLIENT_SECRET: z.string().optional(),
  COOKIE_ENCRYPTION_KEY: z.string().optional(),
  
  // External API URLs
  NFD_API_URL: z.string().optional(),
  PERA_WALLET_API_URL: z.string().optional(),
  PERA_EXPLORER_URL: z.string().optional(),
});