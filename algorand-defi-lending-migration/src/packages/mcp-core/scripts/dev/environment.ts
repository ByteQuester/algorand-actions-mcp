/**
 * Development environment configuration utilities
 * These utilities help configure packages for development vs production
 */

export interface DevEnvironmentConfig {
  enableDebugLogging: boolean;
  paginationPageSize?: number;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
}

/**
 * Default development configuration
 */
export const defaultDevConfig: DevEnvironmentConfig = {
  enableDebugLogging: true,
  paginationPageSize: 5, // Smaller for testing
  logLevel: 'debug'
};

/**
 * Production configuration (no debug features)
 */
export const productionConfig: DevEnvironmentConfig = {
  enableDebugLogging: false,
  logLevel: 'error'
};

/**
 * Get configuration based on NODE_ENV
 */
export function getEnvironmentConfig(): DevEnvironmentConfig {
  const env = process.env.NODE_ENV || 'development';

  switch (env) {
    case 'production':
      return productionConfig;
    case 'test':
      return {
        ...defaultDevConfig,
        paginationPageSize: 2, // Very small for predictable testing
        logLevel: 'warn'
      };
    default:
      return defaultDevConfig;
  }
}

/**
 * Apply environment configuration to MCP Core components
 */
export function applyEnvironmentConfig(config: DevEnvironmentConfig = getEnvironmentConfig()) {
  // Import here to avoid circular dependencies
  const { ResponseProcessor } = require('../../src/response-processor.js');

  if (config.enableDebugLogging) {
    // Import debug utilities
    const { responseProcessorLogger } = require('./debug-utils.js');
    ResponseProcessor.setLogger(responseProcessorLogger);
  } else {
    ResponseProcessor.resetLogger();
  }

  if (config.paginationPageSize) {
    ResponseProcessor.setItemsPerPage(config.paginationPageSize);
  }
}