/**
 * Debug utilities for MCP Core development
 * These utilities are only used during development and testing
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface DebugConfig {
  enabled: boolean;
  level: LogLevel;
  prefix?: string;
}

export class DebugLogger {
  private config: DebugConfig;

  constructor(config: DebugConfig = { enabled: false, level: 'debug' }) {
    this.config = config;
  }

  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled;
  }

  setLevel(level: LogLevel): void {
    this.config.level = level;
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;

    const levels = ['debug', 'info', 'warn', 'error'];
    const configLevelIndex = levels.indexOf(this.config.level);
    const logLevelIndex = levels.indexOf(level);

    return logLevelIndex >= configLevelIndex;
  }

  private formatMessage(level: LogLevel, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    const prefix = this.config.prefix ? `[${this.config.prefix}] ` : '';
    const baseMessage = `${timestamp} ${prefix}[${level.toUpperCase()}] ${message}`;

    if (data) {
      return `${baseMessage} ${JSON.stringify(data, null, 2)}`;
    }

    return baseMessage;
  }

  debug(message: string, data?: any): void {
    if (this.shouldLog('debug')) {
      console.log(this.formatMessage('debug', message, data));
    }
  }

  info(message: string, data?: any): void {
    if (this.shouldLog('info')) {
      console.log(this.formatMessage('info', message, data));
    }
  }

  warn(message: string, data?: any): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message, data));
    }
  }

  error(message: string, data?: any): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message, data));
    }
  }
}

// Development-only logging utilities
export const responseProcessorLogger = new DebugLogger({
  enabled: process.env.NODE_ENV === 'development',
  level: 'debug',
  prefix: 'ResponseProcessor'
});

export const paginationLogger = new DebugLogger({
  enabled: process.env.NODE_ENV === 'development',
  level: 'debug',
  prefix: 'Pagination'
});

// Export development utilities for testing
export const devUtils = {
  enableDebugLogging: () => {
    responseProcessorLogger.setEnabled(true);
    paginationLogger.setEnabled(true);
  },
  disableDebugLogging: () => {
    responseProcessorLogger.setEnabled(false);
    paginationLogger.setEnabled(false);
  }
};