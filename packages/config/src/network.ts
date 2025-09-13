/**
 * Network configuration management
 */
import type { NetworkConfig, AlgorandNetwork, BaseEnv, Result } from '@algorand-showcase/types';
import { parseNetwork, validateNetworkConfig, getDefaultUrls } from './validation.js';

/**
 * Create network configuration from environment
 */
export function createNetworkConfig(env: BaseEnv): Result<NetworkConfig> {
  const network = parseNetwork(env.ALGORAND_NETWORK);
  
  const validation = validateNetworkConfig(
    network,
    env.ALGORAND_ALGOD,
    env.ALGORAND_INDEXER
  );

  if (!validation.success) {
    return validation;
  }

  return {
    success: true,
    data: {
      network,
      algodUrl: validation.data.algodUrl,
      indexerUrl: validation.data.indexerUrl,
      token: env.ALGORAND_TOKEN,
    }
  };
}

/**
 * Get network configuration for a specific network
 */
export function getNetworkConfig(network: AlgorandNetwork, token?: string): NetworkConfig {
  const urls = getDefaultUrls(network);
  
  return {
    network,
    algodUrl: urls.algod,
    indexerUrl: urls.indexer,
    token,
  };
}

/**
 * Check if mainnet is allowed
 */
export function isMainnetAllowed(network: AlgorandNetwork, allowMainnet?: boolean | string): boolean {
  if (network !== 'mainnet') return true;
  
  return allowMainnet === true || allowMainnet === 'true' || allowMainnet === '1';
}

/**
 * Get explorer URL for a network
 */
export function getExplorerUrl(network: AlgorandNetwork, type: 'tx' | 'account' | 'asset' | 'app' = 'tx'): string {
  const baseUrl = network === 'testnet' 
    ? 'https://testnet.explorer.perawallet.app'
    : 'https://explorer.perawallet.app';
  
  return `${baseUrl}/${type}/`;
}