/**
 * Configuration validation utilities
 */
import type { Result, AlgorandNetwork, BaseEnv } from '@algorand-showcase/types';

/**
 * Check if a value is truthy (true, "true", "1")
 */
export function isTrue(value: any): boolean {
  return value === true || value === "true" || value === "1";
}

/**
 * Parse network from environment variable
 */
export function parseNetwork(networkValue?: string): AlgorandNetwork {
  const network = (networkValue || "testnet").toLowerCase();
  return network === "mainnet" || network === "betanet" ? network : "testnet";
}

/**
 * Validate network configuration
 */
export function validateNetworkConfig(
  network: AlgorandNetwork,
  algodUrl?: string,
  indexerUrl?: string
): Result<{ algodUrl: string; indexerUrl: string }> {
  const defaultUrls = getDefaultUrls(network);
  
  const finalAlgodUrl = algodUrl || defaultUrls.algod;
  const finalIndexerUrl = indexerUrl || defaultUrls.indexer;

  try {
    new URL(finalAlgodUrl);
    new URL(finalIndexerUrl);
    
    return {
      success: true,
      data: {
        algodUrl: finalAlgodUrl,
        indexerUrl: finalIndexerUrl
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error : new Error('Invalid URL configuration')
    };
  }
}

/**
 * Get default URLs for a network
 */
export function getDefaultUrls(network: AlgorandNetwork): { algod: string; indexer: string } {
  switch (network) {
    case 'mainnet':
      return {
        algod: 'https://mainnet-api.algonode.cloud',
        indexer: 'https://mainnet-idx.algonode.cloud'
      };
    case 'betanet':
      return {
        algod: 'https://betanet-api.algonode.cloud',
        indexer: 'https://betanet-idx.algonode.cloud'
      };
    case 'testnet':
    default:
      return {
        algod: 'https://testnet-api.algonode.cloud',
        indexer: 'https://testnet-idx.algonode.cloud'
      };
  }
}

/**
 * Check if read-only mode should be enabled
 */
export function shouldEnableReadOnlyMode(env: BaseEnv, requiredSecrets: string[] = []): boolean {
  // Explicit read-only flag
  const explicitReadOnly = isTrue(env.READ_ONLY);
  if (explicitReadOnly) return true;

  // Check for missing required secrets
  if (requiredSecrets.length > 0) {
    const missingSecrets = requiredSecrets.some(secret => !env[secret as keyof BaseEnv]);
    if (missingSecrets) return true;
  }

  return false;
}

/**
 * Parse items per page from environment
 */
export function parseItemsPerPage(value?: string, defaultValue: number = 10): number {
  if (!value) return defaultValue;
  
  const parsed = parseInt(value, 10);
  if (isNaN(parsed) || parsed < 1 || parsed > 100) {
    return defaultValue;
  }
  
  return parsed;
}