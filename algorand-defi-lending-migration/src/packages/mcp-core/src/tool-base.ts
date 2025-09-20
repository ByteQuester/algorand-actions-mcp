/**
 * Base classes for MCP tools
 */
import { z } from 'zod';
import type { MCPToolResult } from '@algorand-showcase/types';
import { ResponseProcessor } from './response-processor.js';

/**
 * Base configuration for MCP tools
 */
export interface MCPToolConfig {
  name: string;
  description: string;
  schema: z.ZodSchema<any>;
}

/**
 * Abstract base class for MCP tools
 */
export abstract class MCPTool<TParams = any, TResult = any> {
  public readonly name: string;
  public readonly description: string;
  public readonly schema: z.ZodSchema<TParams>;

  constructor(config: MCPToolConfig) {
    this.name = config.name;
    this.description = config.description;
    this.schema = config.schema;
  }

  /**
   * Validate input parameters
   */
  protected validateParams(params: unknown): TParams {
    const result = this.schema.safeParse(params);
    if (!result.success) {
      throw new Error(`Invalid parameters: ${result.error.message}`);
    }
    return result.data;
  }

  /**
   * Execute the tool with validated parameters
   */
  abstract execute(params: TParams): Promise<TResult>;

  /**
   * Handle tool execution with validation and error handling
   */
  async handle(params: unknown): Promise<MCPToolResult> {
    try {
      const validatedParams = this.validateParams(params);
      const result = await this.execute(validatedParams);
      return ResponseProcessor.createSuccessResponse(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      return ResponseProcessor.createErrorResponse(message);
    }
  }
}

/**
 * Simple tool class for basic operations
 */
export class SimpleMCPTool<TParams = any> extends MCPTool<TParams, any> {
  private handler: (params: TParams) => Promise<any>;

  constructor(
    config: MCPToolConfig,
    handler: (params: TParams) => Promise<any>
  ) {
    super(config);
    this.handler = handler;
  }

  async execute(params: TParams): Promise<any> {
    return this.handler(params);
  }
}

/**
 * Tool factory for creating simple tools
 */
export class MCPToolFactory {
  /**
   * Create a simple tool with automatic validation
   */
  static createTool<TParams = any>(
    name: string,
    description: string,
    schema: z.ZodSchema<TParams>,
    handler: (params: TParams) => Promise<any>
  ): SimpleMCPTool<TParams> {
    return new SimpleMCPTool(
      { name, description, schema },
      handler
    );
  }

  /**
   * Create a read-only stub tool
   */
  static createReadOnlyStub(
    name: string,
    description: string,
    schema: z.ZodSchema<any>,
    message: string = 'unavailable in read-only mode'
  ): SimpleMCPTool {
    return new SimpleMCPTool(
      { name, description: `${description} (disabled in READ_ONLY mode)`, schema },
      async () => {
        throw new Error(message);
      }
    );
  }
}