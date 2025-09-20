/**
 * Development helper for network configuration
 * Provides utilities for switching between networks and testing configurations
 */

import { AlgorandNetwork } from '@algorand-showcase/types';
import { loadNetworkConfig, validateNetworkConfig, getNetworkUrls } from '../../src/index.js';

export interface NetworkPreset {
  name: string;
  description: string;
  network: AlgorandNetwork;
  algodUrl?: string;
  indexerUrl?: string;
  allowMainnet?: boolean;
}

/**
 * Common network presets for development and testing
 */
export const networkPresets: NetworkPreset[] = [
  {
    name: 'testnet-algonode',
    description: 'Testnet using AlgoNode public endpoints',
    network: 'testnet'
  },
  {
    name: 'mainnet-algonode',
    description: 'Mainnet using AlgoNode public endpoints (requires ALLOW_MAINNET=true)',
    network: 'mainnet',
    allowMainnet: true
  },
  {
    name: 'local-development',
    description: 'Local development network (requires running local nodes)',
    network: 'testnet',
    algodUrl: 'http://localhost:4001',
    indexerUrl: 'http://localhost:8980'
  },
  {
    name: 'betanet-algonode',
    description: 'Betanet using AlgoNode public endpoints',
    network: 'betanet'
  }
];

/**
 * Generate environment variables for a network preset
 */
export function generateEnvForPreset(preset: NetworkPreset): Record<string, string> {
  const env: Record<string, string> = {
    ALGORAND_NETWORK: preset.network
  };

  if (preset.allowMainnet) {
    env.ALLOW_MAINNET = 'true';
  }

  if (preset.algodUrl) {
    env.CUSTOM_ALGOD_URL = preset.algodUrl;
  }

  if (preset.indexerUrl) {
    env.CUSTOM_INDEXER_URL = preset.indexerUrl;
  }

  return env;
}

/**
 * Test a network configuration
 */
export async function testNetworkConfig(preset: NetworkPreset): Promise<{
  success: boolean;
  config?: any;
  error?: string;
}> {
  try {
    // Generate environment variables
    const envVars = generateEnvForPreset(preset);

    // Create mock environment
    const mockEnv = {
      ...process.env,
      ...envVars
    };

    // Validate configuration
    const config = validateNetworkConfig(mockEnv);
    const urls = getNetworkUrls(config.network);

    return {
      success: true,
      config: {
        network: config.network,
        algodUrl: envVars.CUSTOM_ALGOD_URL || urls.algod,
        indexerUrl: envVars.CUSTOM_INDEXER_URL || urls.indexer,
        allowMainnet: config.allowMainnet
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Display all available network presets
 */
export function displayNetworkPresets(): void {
  console.log('Available Network Presets:\n');

  networkPresets.forEach((preset, index) => {
    console.log(`${index + 1}. ${preset.name}`);
    console.log(`   Description: ${preset.description}`);
    console.log(`   Network: ${preset.network}`);

    if (preset.algodUrl) {
      console.log(`   Algod URL: ${preset.algodUrl}`);
    }
    if (preset.indexerUrl) {
      console.log(`   Indexer URL: ${preset.indexerUrl}`);
    }
    if (preset.allowMainnet) {
      console.log(`   Requires: ALLOW_MAINNET=true`);
    }

    const envVars = generateEnvForPreset(preset);
    console.log(`   Environment variables:`);
    Object.entries(envVars).forEach(([key, value]) => {
      console.log(`     ${key}=${value}`);
    });

    console.log('');
  });
}

/**
 * Interactive network configuration tester
 */
export async function runInteractiveTest(): Promise<void> {
  console.log('=== Network Configuration Tester ===\n');

  displayNetworkPresets();

  console.log('Testing all presets:\n');

  for (const preset of networkPresets) {
    console.log(`Testing ${preset.name}...`);
    const result = await testNetworkConfig(preset);

    if (result.success) {
      console.log(`✅ Success:`, result.config);
    } else {
      console.log(`❌ Failed:`, result.error);
    }
    console.log('');
  }
}

// Run interactive test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runInteractiveTest().catch(console.error);
}