/**
 * Configuration loading utilities
 */
import type { NetworkConfig, MCPConfig, AppConfig, BaseEnv, AlgorandNetwork } from '@algorand-showcase/types';
import { createNetworkConfig } from './network';
import { parseItemsPerPage, shouldEnableReadOnlyMode, isTrue } from './validation';
import { NetworkConfigSchema, MCPConfigSchema, AppConfigSchema } from './schemas';

/**
 * Load and validate network configuration
 */
export function loadNetworkConfig(env: BaseEnv): NetworkConfig {
  const result = createNetworkConfig(env);
  if (!result.success) {
    throw new Error(`Invalid network configuration: ${result.error.message}`);
  }
  return result.data;
}

/**
 * Load MCP configuration
 */
export function loadMCPConfig(
  name: string,
  version: string,
  env: BaseEnv,
  requiredSecrets: string[] = []
): MCPConfig {
  const networkConfig = loadNetworkConfig(env);
  const readOnly = shouldEnableReadOnlyMode(env, requiredSecrets);
  const itemsPerPage = parseItemsPerPage(env.ITEMS_PER_PAGE);

  const config: MCPConfig = {
    name,
    version,
    network: networkConfig.network,
    readOnly,
    itemsPerPage,
  };

  // Validate the configuration
  const validated = MCPConfigSchema.safeParse(config);
  if (!validated.success) {
    throw new Error(`Invalid MCP configuration: ${validated.error.message}`);
  }

  return config;
}

/**
 * Load complete application configuration
 */
export function loadAppConfig(
  name: string,
  version: string,
  env: BaseEnv,
  requiredSecrets: string[] = []
): AppConfig {
  const networkConfig = loadNetworkConfig(env);
  const mcpConfig = loadMCPConfig(name, version, env, requiredSecrets);

  // Determine feature availability
  const hasOAuth = !!(env as any).GOOGLE_CLIENT_ID && !!(env as any).GOOGLE_CLIENT_SECRET;
  const hasVault = !!(env as any).HCV_WORKER && !!(env as any).HCV_WORKER_URL;
  const hasStorage = !!(env as any).KNOWLEDGE_BUCKET;

  const config: AppConfig = {
    mcp: mcpConfig,
    network: networkConfig,
    features: {
      oauth: hasOAuth && !mcpConfig.readOnly,
      vault: hasVault && !mcpConfig.readOnly,
      storage: hasStorage,
    },
  };

  // Validate the complete configuration
  const validated = AppConfigSchema.safeParse(config);
  if (!validated.success) {
    throw new Error(`Invalid app configuration: ${validated.error.message}`);
  }

  return config;
}

/**
 * Validate configuration against schema
 */
export function validateConfig<T>(config: unknown, schema: any): T {
  const result = schema.safeParse(config);
  if (!result.success) {
    throw new Error(`Configuration validation failed: ${result.error.message}`);
  }
  return result.data;
}