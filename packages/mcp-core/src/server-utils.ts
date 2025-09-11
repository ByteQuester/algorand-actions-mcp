/**
 * MCP server utilities and common patterns
 */
import { z } from 'zod';
import type { BaseEnv, HealthResponse } from '@algorand-showcase/types';
import { parseNetwork, isTrue } from '@algorand-showcase/config';

/**
 * Create a health check response
 */
export function createHealthResponse(
  env: BaseEnv,
  mode?: 'READ-only' | 'full' | 'actions',
  version?: string
): HealthResponse {
  const network = parseNetwork(env.ALGORAND_NETWORK);
  const readOnly = isTrue(env.READ_ONLY);
  
  return {
    status: 'ok',
    mode: mode || (readOnly ? 'READ-only' : 'full'),
    network,
    timestamp: new Date().toISOString(),
    ...(version && { version })
  };
}

/**
 * Create a capabilities response
 */
export function createCapabilitiesResponse(
  tools: string[],
  network?: string,
  features?: Record<string, boolean>
): any {
  return {
    tools,
    ...(network && { network }),
    ...(features && { features })
  };
}

/**
 * Common tool schemas
 */
export const CommonSchemas = {
  address: z.string().describe('Algorand address'),
  amount: z.number().min(0).describe('Amount in microAlgos'),
  assetId: z.number().min(0).describe('Asset ID'),
  appId: z.number().min(0).describe('Application ID'),
  note: z.string().optional().describe('Optional note'),
  pageToken: z.string().optional().describe('Pagination token for next page'),
  limit: z.number().min(1).max(100).optional().describe('Maximum number of items to return'),
} as const;

/**
 * Validate environment requirements
 */
export function validateEnvironment(
  env: BaseEnv,
  requiredVars: (keyof BaseEnv)[]
): { valid: boolean; missing: string[] } {
  const missing = requiredVars.filter(varName => !env[varName]);
  
  return {
    valid: missing.length === 0,
    missing
  };
}

/**
 * Check if mainnet operations should be allowed
 */
export function shouldAllowMainnet(env: BaseEnv): boolean {
  const network = parseNetwork(env.ALGORAND_NETWORK);
  if (network !== 'mainnet') return true;
  
  return isTrue(env.ALLOW_MAINNET);
}

/**
 * Create a mainnet gate response
 */
export function createMainnetGateResponse(): Response {
  return new Response(
    JSON.stringify({ error: 'mainnet operations disabled' }), 
    { 
      status: 403, 
      headers: { 'content-type': 'application/json' } 
    }
  );
}

/**
 * Standard error responses
 */
export const ErrorResponses = {
  notFound: () => new Response('Not found', { status: 404 }),
  
  badRequest: (message?: string) => new Response(
    JSON.stringify({ error: message || 'Bad request' }), 
    { 
      status: 400, 
      headers: { 'content-type': 'application/json' } 
    }
  ),
  
  unauthorized: (message?: string) => new Response(
    JSON.stringify({ error: message || 'Unauthorized' }), 
    { 
      status: 401, 
      headers: { 'content-type': 'application/json' } 
    }
  ),
  
  forbidden: (message?: string) => new Response(
    JSON.stringify({ error: message || 'Forbidden' }), 
    { 
      status: 403, 
      headers: { 'content-type': 'application/json' } 
    }
  ),
  
  internalError: (message?: string) => new Response(
    JSON.stringify({ error: message || 'Internal server error' }), 
    { 
      status: 500, 
      headers: { 'content-type': 'application/json' } 
    }
  ),
} as const;

/**
 * CORS headers for Cloudflare Workers
 */
export const CORSHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '3600',
} as const;

/**
 * Create a response with CORS headers
 */
export function createCORSResponse(
  body: string | null,
  init?: ResponseInit
): Response {
  return new Response(body, {
    ...init,
    headers: {
      ...CORSHeaders,
      ...init?.headers
    }
  });
}