/**
 * Model Context Protocol (MCP) related types
 */

/**
 * Standard MCP request structure
 */
export interface MCPRequest {
  method: string;
  params: Record<string, unknown>;
  id: string;
}

/**
 * Standard MCP response structure
 */
export interface MCPResponse {
  result?: unknown;
  error?: MCPError;
  id: string;
}

/**
 * MCP error structure
 */
export interface MCPError {
  code: number;
  message: string;
  data?: unknown;
}

/**
 * MCP tool result content
 */
export interface MCPToolContent {
  type: 'text' | 'image' | 'resource';
  text?: string;
  data?: string;
  mimeType?: string;
}

/**
 * MCP tool result structure
 */
export interface MCPToolResult {
  content: MCPToolContent[];
  isError?: boolean;
}

/**
 * MCP tool definition
 */
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

/**
 * MCP server configuration
 */
export interface MCPServerConfig {
  name: string;
  version: string;
  capabilities?: {
    tools?: boolean;
    resources?: boolean;
    prompts?: boolean;
  };
}

/**
 * Pagination metadata for MCP responses
 */
export interface MCPPaginationMetadata {
  totalItems: number;
  itemsPerPage: number;
  currentPage: number;
  totalPages: number;
  hasNextPage: boolean;
  pageToken?: string;
}

/**
 * Paginated MCP response structure
 */
export interface MCPPaginatedResponse<T = unknown> {
  data: T;
  metadata: MCPPaginationMetadata & {
    arrayField?: string;
  };
}

/**
 * Standard processed response for MCP tools
 */
export interface MCPProcessedResponse {
  [key: string]: any;
  content?: MCPToolContent[];
  metadata?: MCPPaginationMetadata & {
    arrayField?: string;
  };
}